from datetime import datetime
from config.supabase_client import supabase


# ==========================================
# VALIDATE LICENSE
# ==========================================

def get_license(license_key: str):

    result = (
        supabase.table("licenses")
        .select("*")
        .eq("license_key", license_key)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


# ==========================================
# CHECK LICENSE STATUS
# ==========================================

def validate_license_status(license_data: dict):

    if not license_data:
        return {
            "valid": False,
            "reason": "LICENSE_NOT_FOUND"
        }

    if license_data.get("status") != "active":
        return {
            "valid": False,
            "reason": "LICENSE_INACTIVE"
        }

    expires_at = license_data.get("expires_at")

    if expires_at:

        try:

            expiry_date = datetime.fromisoformat(
                expires_at.replace("Z", "+00:00")
            )

            if expiry_date < datetime.utcnow().astimezone():

                return {
                    "valid": False,
                    "reason": "LICENSE_EXPIRED"
                }

        except Exception:
            pass

    return {
        "valid": True
    }


# ==========================================
# GET DEVICES
# ==========================================

def get_registered_devices(license_key: str):

    result = (
        supabase.table("license_devices")
        .select("*")
        .eq("license_key", license_key)
        .execute()
    )

    return result.data or []


# ==========================================
# UPDATE LAST SEEN
# ==========================================

def update_device_last_seen(
    license_key: str,
    device_id: str
):

    try:

        supabase.table("license_devices") \
            .update({
                "last_seen_at": datetime.utcnow().isoformat()
            }) \
            .eq("license_key", license_key) \
            .eq("device_id", device_id) \
            .execute()

    except Exception:
        pass


# ==========================================
# REGISTER DEVICE
# ==========================================

def register_device(
    license_key: str,
    device_id: str
):

    supabase.table("license_devices").insert({
        "license_key": license_key,
        "device_id": device_id,
        "activated_at": datetime.utcnow().isoformat(),
        "last_seen_at": datetime.utcnow().isoformat()
    }).execute()


# ==========================================
# MAIN DEVICE VALIDATION ENGINE
# ==========================================

def validate_device(
    license_key: str,
    device_id: str
):

    license_data = get_license(
        license_key
    )

    status = validate_license_status(
        license_data
    )

    if not status["valid"]:
        return status

    devices = get_registered_devices(
        license_key
    )

    existing_device = next(
        (
            d for d in devices
            if d.get("device_id") == device_id
        ),
        None
    )

    # ==========================================
    # EXISTING DEVICE
    # ==========================================

    if existing_device:

        update_device_last_seen(
            license_key,
            device_id
        )

        return {
            "valid": True,
            "bound": True,
            "existing_device": True,
            "device_count": len(devices),
            "max_devices": license_data.get(
                "max_devices",
                1
            )
        }

    # ==========================================
    # NEW DEVICE LIMIT CHECK
    # ==========================================

    max_devices = license_data.get(
        "max_devices",
        1
    )

    if len(devices) >= max_devices:

        return {
            "valid": False,
            "reason": "DEVICE_LIMIT_REACHED",
            "device_count": len(devices),
            "max_devices": max_devices
        }

    # ==========================================
    # REGISTER NEW DEVICE
    # ==========================================

    register_device(
        license_key,
        device_id
    )

    return {
        "valid": True,
        "bound": True,
        "existing_device": False,
        "device_count": len(devices) + 1,
        "max_devices": max_devices
    }


# ==========================================
# DEVICE HEARTBEAT
# ==========================================

def heartbeat(
    license_key: str,
    device_id: str
):

    validation = validate_device(
        license_key,
        device_id
    )

    if not validation.get("valid"):
        return validation

    update_device_last_seen(
        license_key,
        device_id
    )

    return {
        "valid": True,
        "heartbeat": True,
        "timestamp": datetime.utcnow().isoformat()
    }


# ==========================================
# ADMIN DEVICE RESET
# ==========================================

def reset_devices(
    license_key: str
):

    try:

        supabase.table("license_devices") \
            .delete() \
            .eq("license_key", license_key) \
            .execute()

        return {
            "success": True
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }