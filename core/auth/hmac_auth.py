import hmac
import hashlib
import time


# ==========================================
# GENERATE SIGNATURE (PER USER)
# ==========================================

def generate_signature(payload: str, timestamp: str, secret: str):

    message = f"{payload}|{timestamp}"

    return hmac.new(
        secret.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()


# ==========================================
# VERIFY SIGNATURE (PER USER)
# ==========================================

def verify_signature(payload: str, timestamp: str, signature: str, secret: str):

    if abs(time.time() - float(timestamp)) > 300:
        return False

    expected = generate_signature(payload, timestamp, secret)

    return hmac.compare_digest(expected, signature)