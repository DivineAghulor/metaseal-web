import os
import io
import jwt
import modal
import ecdsa
from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from PIL import Image

# 1. Define the Modal Environment
image = (
    modal.Image.debian_slim()
    .apt_install("libzbar0", "libzbar-dev")
    .pip_install(
        "fastapi", "uvicorn", "python-multipart", "torch", "torchvision",
        "Pillow", "cryptography", "qrcode", "pyzbar", "matplotlib",
        "scikit-image", "lpips", "transformers", "supabase", "PyJWT", "ecdsa"
    )
    .add_local_dir(".", remote_path="/app", ignore=["venv", ".venv", "__pycache__", ".git"])
)

app = modal.App("metaseal-backend")
web_app = FastAPI(title="MetaSeal API")

web_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Lock this down to your Vercel URL later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. Helper Functions
def get_supabase() -> Client:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    return create_client(url, key)

# def verify_supabase_jwt(authorization: str = Header(...)):
#     """Validates the Supabase JWT from the frontend."""
#     if not authorization.startswith("Bearer "):
#         raise HTTPException(status_code=401, detail="Invalid token format")
#     token = authorization.split(" ")[1]
#     secret = os.environ.get("SUPABASE_JWT_SECRET")
#     try:
#         decoded = jwt.decode(token, secret, algorithms=["HS256"], audience="authenticated")
#         return decoded["sub"] # Returns the user_id
#     except jwt.ExpiredSignatureError:
#         raise HTTPException(status_code=401, detail="Token expired")
#     except jwt.InvalidTokenError:
#         raise HTTPException(status_code=401, detail="Invalid token")
#     except jwt.ExpiredSignatureError:
#         print("JWT ERROR: Token expired")
#         raise HTTPException(status_code=401, detail="Token expired")
#     except jwt.InvalidTokenError as e:
#         print(f"JWT ERROR: {e}") # <--- This will print the exact issue to Modal logs
#         raise HTTPException(status_code=401, detail=f"Invalid token: {e}")

def verify_supabase_jwt(authorization: str = Header(...)):
    print("--- Supabase Auth Verification Started ---")
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    token = authorization.split(" ")[1]
    
    try:
        # Delegate token verification entirely to the official Supabase client
        supabase = get_supabase()
        user_response = supabase.auth.get_user(token)
        
        if user_response and user_response.user:
            print(f"SUCCESS! User ID verified: {user_response.user.id}")
            return user_response.user.id
        else:
            raise HTTPException(status_code=401, detail="Invalid token session")
            
    except Exception as e:
        print(f"Supabase Auth Error: {str(e)}")
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
    

# 3. Endpoints
@web_app.get("/health")
async def health_check():
    return {"status": "healthy"}

@web_app.post("/watermark")
async def watermark_endpoint(
    image: UploadFile = File(...), 
    caption: str = Form(""),
    user_id: str = Depends(verify_supabase_jwt)
):
    import sys
    sys.path.insert(0, "/app")
    from pipeline import watermark_image
    from crypto_utils import encrypt_private_key
    
    # Process image
    img_bytes = await image.read()
    pil_image = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    
    # Run Pipeline
    watermarked_pil, priv_pem, pub_pem, signature, image_id = watermark_image(pil_image, caption)
    
    # Convert watermarked image back to bytes for storage
    out_buf = io.BytesIO()
    watermarked_pil.save(out_buf, format="PNG")
    watermarked_bytes = out_buf.getvalue()
    
    file_path = f"{user_id}/{image_id}.png"
    supabase = get_supabase()
    
    # Upload to Supabase Storage
    supabase.storage.from_("watermarked-images").upload(
        path=file_path,
        file=watermarked_bytes,
        file_options={"content-type": "image/png"}
    )
    
    public_url = supabase.storage.from_("watermarked-images").get_public_url(file_path)
    
    # Insert into Database
    supabase.table("images").insert({
        "id": image_id,
        "user_id": user_id,
        "original_storage_path": "originals/not-saved-yet", # Optional: implement original storage if needed
        "watermarked_storage_path": file_path,
        "public_key": pub_pem.decode('utf-8'),
        "signature": signature,
        "caption": caption
    }).execute()
    
    supabase.table("private_keys").insert({
        "image_id": image_id,
        "encrypted_private_key": encrypt_private_key(priv_pem)
    }).execute()
    
    return {
        "message": "Watermarking successful",
        "image_id": image_id,
        "watermarked_url": public_url,
        "public_key": pub_pem.decode('utf-8')
    }

@web_app.post("/verify")
async def verify_endpoint(image: UploadFile = File(...)):
    import sys
    sys.path.insert(0, "/app")
    from pipeline import verify_image
    from crypto_utils import verify_signature
    
    img_bytes = await image.read()
    forged_pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    
    # 1. Run Extraction Pipeline
    result = verify_image(forged_pil, original_pil=None)
    
    vsr = False
    outcome = result["outcome"]
    
    # 2. Cryptographic Validation
    if result["qr_recovery"] and result.get("extracted_id"):
        # Strip any hidden null bytes, newlines, or whitespace from the QR decoder
        clean_id = str(result["extracted_id"]).strip().replace("\x00", "")
        print(f"--- VERIFICATION STARTED FOR ID: '{clean_id}' ---")
        
        supabase = get_supabase()
        db_response = supabase.table("images").select("public_key, signature, caption").eq("id", clean_id).execute()
        
        if db_response.data:
            print("DB Lookup: SUCCESS (Record found in Supabase)")
            db_record = db_response.data[0]
            
            # Run cryptographic check
            is_valid = verify_signature(db_record["caption"], db_record["signature"], db_record["public_key"])
            print(f"Crypto Check: {'PASSED' if is_valid else 'FAILED'}")
            
            if is_valid:
                vsr = True
                outcome = "authentic"
            else:
                outcome = "tampered"
        else:
            print("DB Lookup: FAILED (ID not found in Database)")
            outcome = "tampered" # QR decoded, but ID not found in DB
            
        # Update the result with the cleaned ID
        result["extracted_id"] = clean_id
            
    # Overwrite outcome based on cryptographic check
    result["vsr"] = vsr
    result["outcome"] = outcome
    
    # Log verification attempt to database (fire and forget)
    try:
        supabase = get_supabase()
        supabase.table("verifications").insert({
            "image_id": result.get("extracted_id") if result.get("extracted_id") else None,
            "vsr": vsr,
            "qr_recovery": result["qr_recovery"],
            "outcome": outcome
        }).execute()
    except Exception as e:
        print(f"Failed to log verification: {e}")

    return result

# 4. Modal Entrypoint
# 4. Modal Entrypoint
@app.function(
    image=image, 
    gpu="T4", 
    secrets=[modal.Secret.from_name("metaseal-secrets")],
    min_containers=1 # Keeps one container alive to prevent cold starts during development
)
@modal.asgi_app()
def fastapi_app():
    return web_app