import base64
import hmac
import os
from pathlib import Path

KEY_DIR = Path(__file__).resolve().parent / "keys"
SECRET_KEY_PATH = KEY_DIR / "organism_hmac.key"


def load_or_create_secret() -> bytes:
    KEY_DIR.mkdir(parents=True, exist_ok=True)
    if SECRET_KEY_PATH.exists():
        return SECRET_KEY_PATH.read_bytes()

    secret = os.urandom(32)
    SECRET_KEY_PATH.write_bytes(secret)
    return secret


def sign(payload: bytes) -> str:
    secret = load_or_create_secret()
    signature = hmac.new(secret, payload, digestmod="sha3_256").digest()
    return base64.b64encode(signature).decode("ascii")


def verify(payload: bytes, signature_b64: str) -> bool:
    expected = sign(payload)
    return hmac.compare_digest(expected, signature_b64)
