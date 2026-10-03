import hashlib
import hmac
import json
import base64
import os
import time

SECRET_KEY = os.getenv("SECRET_KEY", "testtrace_super_secret_dev_key_2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies password using SHA-256 with salt or fallback."""
    try:
        if hashed_password.startswith("pbkdf2:"):
            _, salt_hex, hash_hex = hashed_password.split(":")
            calc = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), bytes.fromhex(salt_hex), 100000)
            return hmac.compare_digest(calc.hex(), hash_hex)
        elif ":" in hashed_password:
            salt_hex, hash_hex = hashed_password.split(":")
            calc = hashlib.sha256((salt_hex + plain_password).encode("utf-8")).hexdigest()
            return hmac.compare_digest(calc, hash_hex)
        else:
            # Simple hex hash fallback
            calc = hashlib.sha256(plain_password.encode("utf-8")).hexdigest()
            return hmac.compare_digest(calc, hashed_password)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Creates a secure salted PBKDF2-SHA256 password hash."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return f"pbkdf2:{salt.hex()}:{key.hex()}"


def create_access_token(data: dict, expires_in_seconds: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60) -> str:
    """Creates a lightweight JWT token using standard HMAC-SHA256."""
    payload = data.copy()
    now = int(time.time())
    payload["iat"] = now
    payload["exp"] = now + expires_in_seconds

    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")

    signing_input = f"{header_b64}.{payload_b64}"
    signature = hmac.new(SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")

    return f"{signing_input}.{sig_b64}"


def decode_access_token(token: str) -> dict | None:
    """Decodes and validates HMAC-SHA256 JWT signature and expiry."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts

        signing_input = f"{header_b64}.{payload_b64}"
        expected_sig = hmac.new(SECRET_KEY.encode(), signing_input.encode(), hashlib.sha256).digest()
        expected_sig_b64 = base64.urlsafe_b64encode(expected_sig).decode().rstrip("=")

        if not hmac.compare_digest(sig_b64, expected_sig_b64):
            return None

        # Decode payload with padding
        padding = 4 - (len(payload_b64) % 4)
        if padding != 4:
            payload_b64 += "=" * padding

        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())

        # Check expiration
        if "exp" in payload and int(time.time()) > payload["exp"]:
            return None

        return payload
    except Exception:
        return None
