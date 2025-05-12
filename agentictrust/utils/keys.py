import os
import base64
import json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from agentictrust.config import Config

def _base64url_uint(val: int) -> str:
    b = val.to_bytes((val.bit_length() + 7) // 8, 'big')
    return base64.urlsafe_b64encode(b).rstrip(b'=') .decode('ascii')

def generate_rsa_keypair():
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )
    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    pub_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    os.makedirs(Config.KEY_DIR, exist_ok=True)
    priv_path = os.path.join(Config.KEY_DIR, Config.PRIVATE_KEY_FILENAME)
    pub_path = os.path.join(Config.KEY_DIR, Config.PUBLIC_KEY_FILENAME)
    with open(priv_path, 'wb') as f:
        f.write(priv_pem)
    with open(pub_path, 'wb') as f:
        f.write(pub_pem)

def load_or_generate_keys():
    priv_path = os.path.join(Config.KEY_DIR, Config.PRIVATE_KEY_FILENAME)
    pub_path = os.path.join(Config.KEY_DIR, Config.PUBLIC_KEY_FILENAME)
    if not os.path.exists(priv_path) or not os.path.exists(pub_path):
        generate_rsa_keypair()

def get_private_key():
    """Load or generate the RSA private key for signing ID Tokens."""
    load_or_generate_keys()
    priv_path = os.path.join(Config.KEY_DIR, Config.PRIVATE_KEY_FILENAME)
    with open(priv_path, "rb") as f:
        priv_pem = f.read()
    return serialization.load_pem_private_key(priv_pem, password=None, backend=default_backend())

def get_public_jwks():
    load_or_generate_keys()
    pub_path = os.path.join(Config.KEY_DIR, Config.PUBLIC_KEY_FILENAME)
    with open(pub_path, 'rb') as f:
        pub_pem = f.read()
    public_key = serialization.load_pem_public_key(pub_pem, backend=default_backend())
    nums = public_key.public_numbers()
    jwk = {
        "kty": "RSA",
        "kid": Config.JWKS_KID,
        "use": "sig",
        "alg": "RS256",
        "n": _base64url_uint(nums.n),
        "e": _base64url_uint(nums.e),
    }
    return {"keys": [jwk]}
