import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization

def get_fernet() -> Fernet:
    """Initialize Fernet with the secret key injected by Modal."""
    secret = os.environ.get("FERNET_SECRET_KEY")
    if not secret:
        raise ValueError("FERNET_SECRET_KEY environment variable is missing")
    return Fernet(secret.encode())

def generate_ecdsa_keypair():
    """Generates an ECDSA keypair and returns (private_pem, public_pem)."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem, public_pem

def encrypt_private_key(private_pem: bytes) -> str:
    """Encrypts the private key for database rest storage."""
    f = get_fernet()
    return f.encrypt(private_pem).decode()

def sign_caption(caption: str, private_pem: bytes) -> str:
    """Signs the semantic caption using the private key and returns a base64 signature."""
    private_key = serialization.load_pem_private_key(private_pem, password=None)
    signature = private_key.sign(
        caption.encode('utf-8'),
        ec.ECDSA(hashes.SHA256())
    )
    return base64.b64encode(signature).decode('utf-8')



def verify_signature(caption: str, signature_b64: str, public_pem: str) -> bool:
    import base64
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.exceptions import InvalidSignature

    try:
        # 1. Load the public key from the PEM string stored in Supabase
        public_key = serialization.load_pem_public_key(public_pem.encode('utf-8'))
        
        # 2. Decode the base64 signature stored in Supabase
        signature_bytes = base64.b64decode(signature_b64)
        
        # 3. Verify it against the caption (or an empty string if there's no caption)
        message = caption.encode('utf-8') if caption else b""
        
        public_key.verify(
            signature_bytes,
            message,
            ec.ECDSA(hashes.SHA256())
        )
        return True
        
    except InvalidSignature:
        print("Signature verification error: Invalid Signature (Tampered!)")
        return False
    except Exception as e:
        print(f"Signature verification error: {type(e).__name__} - {str(e)}")
        return False