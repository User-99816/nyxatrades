from fastapi import APIRouter
from config.supabase_client import supabase
from datetime import datetime

router = APIRouter(
    prefix="/license",
    tags=["License"]
)

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

    # ==========================================
    # EXPIRY CHECK (FIXED SAFE TIME)
    # ==========================================
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

    # ==========================================
    # DEVICE COUNT CHECK
    # ==========================================
    device_result = supabase.table("license_devices") \
        .select("*") \
        .eq("license_key", license_key) \
        .execute()

    current_devices = len(device_result.data or [])

    max_devices = license_data.get("max_devices", 1)

    return {
        "allowed": True,
        "message": "License Valid",

        "license_key": license_key,
        "plan": license_data.get("plan"),
        "status": license_data.get("status"),

        "devices_used": current_devices,
        "max_devices": max_devices,

        "download_url": "/ea/nyxatrades_ea.ex5"
    }


# ==========================================
# VALIDATE LICENSE + DEVICE BINDING (CORE SECURITY)
# ==========================================
@router.post("/validate")
def validate_license(payload: dict):

    license_key = payload.get("license_key")
    device_id = payload.get("device_id")

    if not license_key:
        return {
            "valid": False,
            "reason": "MISSING_LICENSE"
        }

    if not device_id:
        return {
            "valid": False,
            "reason": "MISSING_DEVICE"
        }

    # ==========================================
    # GET LICENSE
    # ==========================================
    license_result = supabase.table("licenses") \
        .select("*") \
        .eq("license_key", license_key) \
        .eq("status", "active") \
        .execute()

    if not license_result.data:
        return {
            "valid": False,
            "reason": "INVALID_LICENSE"
        }

    license_data = license_result.data[0]

    # ==========================================
    # EXPIRY CHECK (CRITICAL)
    # ==========================================
    expires_at = license_data.get("expires_at")

    if expires_at:
        try:
            expiry_date = datetime.fromisoformat(
                expires_at.replace("Z", "+00:00")
            )

            if expiry_date < datetime.utcnow().astimezone():
                return {
                    "valid": False,
                    "reason": "EXPIRED"
                }

        except Exception:
            return {
                "valid": False,
                "reason": "INVALID_EXPIRY"
            }

    # ==========================================
    # GET DEVICE LIST
    # ==========================================
    devices = supabase.table("license_devices") \
        .select("*") \
        .eq("license_key", license_key) \
        .execute()

    devices_data = devices.data or []

    # ==========================================
    # CHECK IF DEVICE EXISTS
    # ==========================================
    existing_device = next(
        (d for d in devices_data if d.get("device_id") == device_id),
        None
    )

    # ==========================================
    # IF DEVICE EXISTS → UPDATE LAST SEEN
    # ==========================================
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

    # ==========================================
    # DEVICE LIMIT CHECK
    # ==========================================
    max_devices = license_data.get("max_devices", 1)

    if len(devices_data) >= max_devices:
        return {
            "valid": False,
            "reason": "DEVICE_LIMIT_REACHED"
        }

    # ==========================================
    # BIND NEW DEVICE
    # ==========================================
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