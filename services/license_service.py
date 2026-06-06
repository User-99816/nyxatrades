from config.supabase_client import supabase
from config.settings import LICENSE_PREFIX
import secrets
from datetime import datetime, timedelta

from utils.security import hash_api_key


# ==========================================
# PLAN CONFIG (NEW CORE UPGRADE)
# ==========================================

PLAN_RULES = {
    "trial": {
        "days": 3,
        "status": "active"
    },
    "lite": {
        "days": 30,
        "status": "active"
    },
    "pro": {
        "days": 3650,
        "status": "active"
    }
}


# ==========================================
# VALIDATE LICENSE (UPGRADED)
# ==========================================

def validate_license(api_key: str):

    if not api_key:
        return None

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

    if license_data.get("status") not in ["active", "ACTIVE"]:
        return None

    # ==========================================
    # EXPIRY CHECK (IMPROVED)
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
# CREATE LICENSE (PLAN-BASED EXPIRY ADDED)
# ==========================================

def create_license(user_email: str, plan: str = "trial"):

    if plan not in PLAN_RULES:
        plan = "trial"

    api_key = (
        f"{LICENSE_PREFIX}-"
        f"{secrets.token_hex(8).upper()}"
    )

    api_key_hash = hash_api_key(api_key)

    expiry_date = datetime.utcnow() + timedelta(
        days=PLAN_RULES[plan]["days"]
    )

    payload = {
        "user_email": user_email,

        # PUBLIC KEY (shown once)
        "api_key": api_key,

        # SECURE HASH (used internally)
        "api_key_hash": api_key_hash,

        "status": "active",
        "plan": plan,

        "expires_at": expiry_date.isoformat(),

        # DEVICE BINDING PLACEHOLDER
        "mt5_account": None,
        "broker_server": None,
        "terminal_id": None,

        # TRACKING
        "created_at": datetime.utcnow().isoformat()
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

def deactivate_license(api_key: str):

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

def activate_license(api_key: str):

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
# DEVICE BINDING (IMPROVED)
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

    # First-time binding (auto bind)
    updates = {}

    if not license_data.get("mt5_account"):
        updates["mt5_account"] = mt5_account

    if not license_data.get("broker_server"):
        updates["broker_server"] = broker_server

    if not license_data.get("terminal_id"):
        updates["terminal_id"] = terminal_id

    # Save binding if first time
    if updates:
        (
            supabase
            .table("licenses")
            .update(updates)
            .eq("api_key_hash", hash_api_key(api_key))
            .execute()
        )
        return True

    # Strict validation
    if license_data.get("mt5_account") != mt5_account:
        return False

    if license_data.get("broker_server") != broker_server:
        return False

    if license_data.get("terminal_id") != terminal_id:
        return False

    return True