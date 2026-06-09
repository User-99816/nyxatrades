import os
from datetime import datetime, timedelta

from jose import jwt, JWTError
from config.supabase_client import supabase

# ==========================================
# CONFIG
# ==========================================

SECRET_KEY = os.getenv("DOWNLOAD_SECRET_KEY")

if not SECRET_KEY:
    raise RuntimeError("DOWNLOAD_SECRET_KEY environment variable is missing")

ALGORITHM = "HS256"

DOWNLOAD_EXPIRY_MINUTES = int(
    os.getenv("DOWNLOAD_EXPIRY_MINUTES", "10")
)

# ==========================================
# CREATE DOWNLOAD TOKEN (SECURE)
# ==========================================
def create_download_token(license_key: str, email: str):

    payload = {
        "license_key": license_key,
        "email": email,
        "type": "ea_download",
        "exp": datetime.utcnow() + timedelta(minutes=DOWNLOAD_EXPIRY_MINUTES)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    try:
        supabase.table("download_tokens").insert({
            "token": token,
            "email": email,
            "license_key": license_key,
            "used": False,
            "created_at": datetime.utcnow().isoformat()
        }).execute()

    except Exception as e:
        print(f"[TOKEN STORE ERROR] {e}")

    return token

# ==========================================
# VERIFY TOKEN (STRICT MODE)
# ==========================================
def verify_download_token(token: str):

    if not token:
        return {"valid": False, "error": "MISSING_TOKEN"}

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        result = supabase.table("download_tokens") \
            .select("*") \
            .eq("token", token) \
            .limit(1) \
            .execute()

        if not result.data:
            return {"valid": False, "error": "TOKEN_NOT_FOUND"}

        record = result.data[0]

        # ==========================================
        # BLOCK REPLAY ATTACKS
        # ==========================================
        if record.get("used"):
            return {"valid": False, "error": "TOKEN_ALREADY_USED"}

        # ==========================================
        # TOKEN EXPIRED (DB LEVEL CHECK)
        # ==========================================
        if record.get("created_at"):
            created = datetime.fromisoformat(record["created_at"])
            if datetime.utcnow() > created + timedelta(minutes=DOWNLOAD_EXPIRY_MINUTES):
                return {"valid": False, "error": "TOKEN_EXPIRED"}

        return {
            "valid": True,
            "data": payload,
            "record": record
        }

    except JWTError as e:
        return {
            "valid": False,
            "error": f"JWT_INVALID: {str(e)}"
        }

    except Exception as e:
        return {
            "valid": False,
            "error": f"TOKEN_VERIFICATION_FAILED: {str(e)}"
        }

# ==========================================
# MARK TOKEN AS USED
# ==========================================
def mark_token_used(token: str):

    try:
        supabase.table("download_tokens").update({
            "used": True,
            "used_at": datetime.utcnow().isoformat()
        }).eq("token", token).execute()

    except Exception as e:
        print(f"[TOKEN UPDATE ERROR] {e}")

# ==========================================
# LOG DOWNLOAD ACTIVITY
# ==========================================
def log_download(license_key: str, email: str, ip_address: str, user_agent: str):

    try:
        supabase.table("download_logs").insert({
            "license_key": license_key,
            "email": email,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "downloaded_at": datetime.utcnow().isoformat()
        }).execute()

    except Exception as e:
        print(f"[DOWNLOAD LOG ERROR] {e}")

# ==========================================
# LICENSE VALIDATION (PRODUCTION SAFE)
# ==========================================
def validate_download_license(email: str, license_key: str):

    try:
        result = supabase.table("licenses") \
            .select("*") \
            .eq("user_email", email) \
            .eq("api_key", license_key) \
            .eq("status", "active") \
            .limit(1) \
            .execute()

        if not result.data:
            return {
                "valid": False,
                "reason": "LICENSE_NOT_FOUND"
            }

        license_data = result.data[0]

        # ==========================================
        # EXPIRY CHECK (STRICT)
        # ==========================================
        expires_at = license_data.get("expires_at")

        if expires_at:
            try:
                expiry = datetime.fromisoformat(
                    expires_at.replace("Z", "+00:00")
                )

                if expiry < datetime.utcnow().astimezone():
                    return {
                        "valid": False,
                        "reason": "LICENSE_EXPIRED"
                    }

            except Exception as e:
                return {
                    "valid": False,
                    "reason": "INVALID_EXPIRY"
                }

        return {
            "valid": True,
            "license": license_data
        }

    except Exception as e:
        print("[LICENSE ERROR]", str(e))
        return {
            "valid": False,
            "reason": "LICENSE_VALIDATION_ERROR"
        }