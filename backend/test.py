import modal
import numpy as np
from PIL import Image

image = (
    modal.Image.debian_slim()
    .apt_install("libzbar0", "libzbar-dev")
    .pip_install(
        "torch", "torchvision", "Pillow", "cryptography", 
        "qrcode", "pyzbar", "matplotlib", "scikit-image", 
        "lpips", "transformers"
    )
    # Add the ignore list so we only upload your code and model.pt
    .add_local_dir(
        ".", 
        remote_path="/app", 
        ignore=["venv", ".venv", "__pycache__", ".git"]
    )
)

app = modal.App("metaseal-test")

@app.function(
    image=image, 
    gpu="T4", 
    secrets=[modal.Secret.from_name("metaseal-secrets")]
)
def run_pipeline_test():
    import sys
    sys.path.insert(0, "/app")
    import urllib.request
    
    from pipeline import watermark_image, verify_image
    
    # Download a real image to test on (gives the network actual texture to work with)
    print("Downloading test image...")
    urllib.request.urlretrieve("https://picsum.photos/256", "test_image.jpg")
    real_image = Image.open("test_image.jpg").convert('RGB')

    print("--- Starting Watermark Test ---")
    watermarked, priv, pub, sig, img_id = watermark_image(real_image, "Test Caption")
    print("Watermarking successful!")

    print("\n--- Starting Verification Test ---")
    result = verify_image(watermarked, real_image)
    print("Verification result:", result)
    
    assert result["vsr"] is True, "VSR failed!"
    assert result["qr_recovery"] is True, "QR Recovery failed!"
    print("\nAll pipeline tests passed on Modal GPU! ✓")

@app.local_entrypoint()
def main():
    run_pipeline_test.remote()