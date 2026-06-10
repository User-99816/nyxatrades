from fastapi import APIRouter
from config.supabase_client import supabase
from datetime import datetime, timedelta
import secrets

from services.secure_download_service import create_download_token

router = APIRouter(
    prefix="/license",
    tags=["License"]
)

# ==========================================
# CREATE PAID LICENSE (WHATSAPP FLOW)
# ==========================================
@router.post("/create-paid")
def create_paid_license(payload: dict = None):

    try:
        print("[PAID] Creating license from WhatsApp payment...")

        email_input = None
        if payload:
            email_input = payload.get("email")

        license_key = "NYXA-" + secrets.token_hex(4).upper()
        api_key = "NYXA-API-" + secrets.token_hex(8).upper()

        email = email_input or f"paid_{secrets.token_hex(4)}@nyxa.local"

        expires_at = datetime.utcnow() + timedelta(days=30)

        # ==========================
        # SAVE LICENSE
        # ==========================
        insert_result = supabase.table("licenses").insert({
            "user_email": email,
            "license_key": license_key,
            "api_key": api_key,
            "status": "active",
            "plan": "paid",
            "max_devices": 1,
            "expires_at": expires_at.isoformat()
        }).execute()

        if not insert_result.data:
            return {
                "success": False,
                "message": "LICENSE_CREATION_FAILED"
            }

        # ==========================
        # CREATE DOWNLOAD TOKEN
        # ==========================
        download_token = create_download_token(
            license_key=license_key,
            email=email
        )

        if not download_token:
            return {
                "success": False,
                "message": "TOKEN_CREATION_FAILED"
            }

        print("[PAID] License created successfully")

        return {
            "success": True,
            "message": "Paid License Created",

            "email": email,
            "license_key": license_key,
            "api_key": api_key,

            "download_token": download_token,
            "download_url": f"https://nyxatrades-2.onrender.com/download/ea?token={download_token}",

            "expires_at": expires_at.isoformat()
        }

    except Exception as e:
        print("[PAID ERROR]", str(e))
        return {
            "success": False,
            "message": "PAID_LICENSE_FAILED",
            "error": str(e)
        }


# ==========================================
# VERIFY DOWNLOAD ACCESS (SECURE)
# ==========================================
@router.post("/verify-download")
def verify_download(payload: dict):

    email = payload.get("email")
    license_key = payload.get("license_key")

    if not email or not license_key:
        return {
            "allowed": False,
            "message": "Missing Credentials"
        }

    result = supabase.table("licenses") \
        .select("*") \
        .eq("user_email", email) \
        .eq("license_key", license_key) \
        .eq("status", "active") \
        .execute()

    if not result.data:
        return {
            "allowed": False,
            "message": "Invalid License"
        }

    license_data = result.data[0]

    # ==========================
    # EXPIRY CHECK
    # ==========================
    expires_at = license_data.get("expires_at")

    if expires_at:
        try:
            expiry_date = datetime.fromisoformat(
                expires_at.replace("Z", "+00:00")
            )

            if expiry_date < datetime.utcnow().astimezone():
                return {
                    "allowed": False,
                    "message": "License Expired"
                }

        except Exception:
            return {
                "allowed": False,
                "message": "Invalid expiry format"
            }

    # ==========================
    # DEVICE COUNT
    # ==========================
    device_result = supabase.table("license_devices") \
        .select("*") \
        .eq("license_key", license_key) \
        .execute()

    devices_data = device_result.data or []

    return {
        "allowed": True,
        "message": "License Valid",

        "license_key": license_key,
        "plan": license_data.get("plan"),
        "status": license_data.get("status"),

        "devices_used": len(devices_data),
        "max_devices": license_data.get("max_devices", 1),

        "download_url": "/ea/nyxatrades_ea.ex5"
    }


# ==========================================
# VALIDATE LICENSE + DEVICE BINDING (CORE EA SECURITY)
# ==========================================
@router.post("/validate")
def validate_license(payload: dict):

    license_key = payload.get("license_key")
    device_id = payload.get("device_id")

    if not license_key:
        return {"valid": False, "reason": "MISSING_LICENSE"}

    if not device_id:
        return {"valid": False, "reason": "MISSING_DEVICE"}

    # ==========================
    # GET LICENSE
    # ==========================
    license_result = supabase.table("licenses") \
        .select("*") \
        .eq("license_key", license_key) \
        .eq("status", "active") \
        .execute()

    if not license_result.data:
        return {"valid": False, "reason": "INVALID_LICENSE"}

    license_data = license_result.data[0]

    # ==========================
    # EXPIRY CHECK
    # ==========================
    expires_at = license_data.get("expires_at")

    if expires_at:
        try:
            expiry_date = datetime.fromisoformat(
                expires_at.replace("Z", "+00:00")
            )

            if expiry_date < datetime.utcnow().astimezone():
                return {"valid": False, "reason": "EXPIRED"}

        except Exception:
            return {"valid": False, "reason": "INVALID_EXPIRY"}

    # ==========================
    # DEVICE CHECK
    # ==========================
    devices = supabase.table("license_devices") \
        .select("*") \
        .eq("license_key", license_key) \
        .execute()

    devices_data = devices.data or []

    existing_device = next(
        (d for d in devices_data if d.get("device_id") == device_id),
        None
    )

    # ==========================
    # UPDATE DEVICE
    # ==========================
    if existing_device:

        supabase.table("license_devices") \
            .update({
                "last_seen_at": datetime.utcnow().isoformat()
            }) \
            .eq("license_key", license_key) \
            .eq("device_id", device_id) \
            .execute()

        return {
            "valid": True,
            "bound": True,
            "message": "Device Verified"
        }

    # ==========================
    # DEVICE LIMIT CHECK
    # ==========================
    max_devices = license_data.get("max_devices", 1)

    if len(devices_data) >= max_devices:
        return {
            "valid": False,
            "reason": "DEVICE_LIMIT_REACHED"
        }

    # ==========================
    # BIND NEW DEVICE
    # ==========================
    supabase.table("license_devices").insert({
        "license_key": license_key,
        "device_id": device_id,
        "activated_at": datetime.utcnow().isoformat(),
        "last_seen_at": datetime.utcnow().isoformat()
    }).execute()

    return {
        "valid": True,
        "bound": True,
        "message": "Device Activated"
    }