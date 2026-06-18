import torch
import torch.nn as nn
from torchvision import transforms
from PIL import Image
import numpy as np
import qrcode
from pyzbar.pyzbar import decode as qr_decode
from skimage.metrics import peak_signal_noise_ratio as psnr_fn
from skimage.metrics import structural_similarity as ssim_fn
import lpips
import sys
import os
import uuid

# Import MetaSeal modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'MetaSeal')))
from scripts.model.model import Model, init_model
import modules.Unet_common as common
from crypto_utils import generate_ecdsa_keypair, sign_caption

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
to_tensor = transforms.ToTensor()
to_pil = transforms.ToPILImage()

# Global variables to hold models in memory
_net = None
_dwt = None
_iwt = None
_lpips_fn = None

def load_models():
    global _net, _dwt, _iwt, _lpips_fn
    if _net is not None:
        return

    _net = Model().to(device)
    init_model(_net)
    
    model_path = os.path.join(os.path.dirname(__file__), 'MetaSeal', 'model', 'model.pt')
    state_dicts = torch.load(model_path, map_location=device)
    network_state_dict = {k: v for k, v in state_dicts['net'].items() if 'tmp_var' not in k}
    
    _net = nn.DataParallel(_net, device_ids=[0])
    _net.load_state_dict(network_state_dict, strict=False)
    _net.eval()

    _dwt = common.DWT().to(device)
    _iwt = common.IWT().to(device)
    _lpips_fn = lpips.LPIPS(net='vgg').to(device)

def watermark_image(image_pil: Image.Image, caption: str):
    load_models()
    
    # 1. Cryptography
    private_pem, public_pem = generate_ecdsa_keypair()
    signature = sign_caption(caption, private_pem)
    
    # 2. Generate a lightweight Reference Payload (just a UUID)
    image_id = str(uuid.uuid4())
    payload = f"MetaSeal-FYP|id:{image_id}"
    
    # Low density QR code (Version 1) easily hidden by the INN
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
    qr.add_data(payload)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert('RGB').resize((256, 256), Image.NEAREST)
    
    cover_t = to_tensor(image_pil.convert('RGB').resize((256, 256), Image.BILINEAR)).unsqueeze(0).to(device)
    secret_t = to_tensor(qr_img).unsqueeze(0).to(device)
    
    with torch.no_grad():
        input_dwt = _dwt(cover_t)
        secret_dwt = _dwt(secret_t)
        input_cat = torch.cat((input_dwt, secret_dwt), dim=1)
        steg_dwt = _net(input_cat, rev=False)
        
        steg_dwt_sliced = steg_dwt.narrow(1, 0, 12) 
        steg_img = _iwt(steg_dwt_sliced)
        steg_img = torch.clamp(steg_img, 0, 1)
        
    watermarked_pil = to_pil(steg_img.squeeze(0).cpu())
    return watermarked_pil, private_pem, public_pem, signature, image_id

def verify_image(forged_pil: Image.Image, original_pil: Image.Image = None):
    load_models()
    
    img_tensor = to_tensor(forged_pil.convert('RGB').resize((256, 256), Image.BILINEAR)).unsqueeze(0).to(device)
    
    with torch.no_grad():
        backward_z = torch.randn((1, 12, 128, 128)).to(device) 
        output_rev = torch.cat((_dwt(img_tensor), backward_z), dim=1)
        backward_img = _net(output_rev, rev=True)
        
        secret_rev = backward_img.narrow(1, 12, 12)
        secret_rev = _iwt(secret_rev)
        secret_rev = torch.clamp(secret_rev, 0, 1)
        
    secret_pil = to_pil(secret_rev.squeeze(0).cpu())
    
    decoded = qr_decode(secret_pil)
    if not decoded:
        grey = secret_pil.convert('L')
        arr = np.array(grey)
        binary = Image.fromarray((arr > arr.mean()).astype(np.uint8) * 255)
        decoded = qr_decode(binary)
        
    qr_recovery = False
    vsr = False
    extracted_id = None
    
    if decoded:
        qr_recovery = True
        payload_str = decoded[0].data.decode('utf-8')
        if payload_str.startswith("MetaSeal-FYP|id:"):
            vsr = True  # The INN embedding survived! 
            extracted_id = payload_str.split("id:")[1]

    metrics = {"psnr": None, "ssim": None, "lpips": None}
    if original_pil:
        clean_arr = np.array(original_pil.convert('RGB').resize((256, 256), Image.BILINEAR))
        forged_arr = np.array(forged_pil.convert('RGB').resize((256, 256), Image.BILINEAR))
        
        metrics["psnr"] = float(psnr_fn(clean_arr, forged_arr, data_range=255))
        metrics["ssim"] = float(ssim_fn(clean_arr, forged_arr, channel_axis=2, data_range=255))
        
        t_clean = to_tensor(original_pil).unsqueeze(0).to(device) * 2 - 1
        t_forged = img_tensor * 2 - 1
        with torch.no_grad():
            metrics["lpips"] = float(_lpips_fn(t_clean, t_forged).item())

    outcome = "authentic" if vsr else "tampered" if qr_recovery else "unverifiable"
    return {"vsr": vsr, "qr_recovery": qr_recovery, "outcome": outcome, "extracted_id": extracted_id, **metrics}