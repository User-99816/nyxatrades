from config.supabase_client import supabase
from config.settings import (
    LICENSE_PREFIX
)

import secrets
from datetime import datetime

# 🔥 SECURITY UPGRADE
from utils.security import hash_api_key


# ==========================================
# VALIDATE LICENSE
# ==========================================

def validate_license(
    api_key: str
):

    if not api_key:
        return None

    # ==========================================
    # HASH API KEY
    # ==========================================

    api_key_hash = hash_api_key(api_key)

    response = (
        supabase
        .table("licenses")
        .select("*")
        .eq("api_key_hash", api_key_hash)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    license_data = response.data[0]

    # ==========================================
    # STATUS CHECK
    # ==========================================

    status = license_data.get("status")

    if status not in ["active", "ACTIVE"]:
        return None

    # ==========================================
    # EXPIRY CHECK
    # ==========================================

    expires_at = license_data.get("expires_at")

    if expires_at:

        try:
            expiry = datetime.fromisoformat(
                expires_at.replace("Z", "+00:00")
            )

            if datetime.utcnow() > expiry.replace(tzinfo=None):
                return None

        except Exception:
            return None

    return license_data


# ==========================================
# CREATE LICENSE
# ==========================================

def create_license(
    user_email: str,
    plan: str
):

    # Raw API key shown to customer
    api_key = (
        f"{LICENSE_PREFIX}-"
        f"{secrets.token_hex(8).upper()}"
    )

    # Store only hash for authentication
    api_key_hash = hash_api_key(api_key)

    payload = {
        "user_email": user_email,

        # Legacy support
        "api_key": api_key,

        # 🔥 New authentication method
        "api_key_hash": api_key_hash,

        "status": "active",
        "plan": plan,

        # Device binding placeholders
        "mt5_account": None,
        "broker_server": None,
        "terminal_id": None
    }

    (
        supabase
        .table("licenses")
        .insert(payload)
        .execute()
    )

    return payload


# ==========================================
# DEACTIVATE LICENSE
# ==========================================

def deactivate_license(
    api_key: str
):

    api_key_hash = hash_api_key(api_key)

    return (
        supabase
        .table("licenses")
        .update({
            "status": "inactive"
        })
        .eq("api_key_hash", api_key_hash)
        .execute()
    )


# ==========================================
# ACTIVATE LICENSE
# ==========================================

def activate_license(
    api_key: str
):

    api_key_hash = hash_api_key(api_key)

    return (
        supabase
        .table("licenses")
        .update({
            "status": "active"
        })
        .eq("api_key_hash", api_key_hash)
        .execute()
    )


# ==========================================
# VALIDATE DEVICE BINDING
# ==========================================

def validate_device_binding(
    api_key: str,
    mt5_account: str,
    broker_server: str,
    terminal_id: str
):

    license_data = validate_license(api_key)

    if not license_data:
        return False

    stored_account = license_data.get("mt5_account")
    stored_server = license_data.get("broker_server")
    stored_terminal = license_data.get("terminal_id")

    if stored_account and stored_account != mt5_account:
        return False

    if stored_server and stored_server != broker_server:
        return False

    if stored_terminal and stored_terminal != terminal_id:
        return False

    return True