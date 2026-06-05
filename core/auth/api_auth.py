from config.supabase_client import supabase
from fastapi import HTTPException
from datetime import datetime

# 🔥 NEW SECURITY UPGRADE
from utils.security import hash_api_key


def validate_api_key(
    api_key: str,
    mt5_account: str = None,
    broker_server: str = None,
    terminal_id: str = None
):

    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="Missing API key"
        )

    # ==========================================
    # HASH API KEY
    # ==========================================

    api_key_hash = hash_api_key(api_key)

    # ==========================================
    # LOOKUP LICENSE
    # ==========================================

    result = supabase.table("licenses") \
        .select("*") \
        .eq("api_key_hash", api_key_hash) \
        .eq("activated", True) \
        .execute()

    if not result.data:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )

    license_data = result.data[0]

    # ==========================================
    # EXPIRY CHECK
    # ==========================================

    expires_at = license_data.get("expires_at")

    if expires_at:

        try:
            expiry_date = datetime.fromisoformat(
                expires_at.replace("Z", "+00:00")
            )

            if datetime.utcnow() > expiry_date.replace(tzinfo=None):
                raise HTTPException(
                    status_code=403,
                    detail="License expired"
                )

        except Exception:
            raise HTTPException(
                status_code=403,
                detail="Invalid license expiry"
            )

    # ==========================================
    # DEVICE BINDING VALIDATION
    # ==========================================

    stored_account = license_data.get("mt5_account")
    stored_server = license_data.get("broker_server")
    stored_terminal = license_data.get("terminal_id")

    if (
        mt5_account is not None and
        stored_account and
        mt5_account != stored_account
    ):
        raise HTTPException(
            status_code=403,
            detail="MT5 account mismatch"
        )

    if (
        broker_server is not None and
        stored_server and
        broker_server != stored_server
    ):
        raise HTTPException(
            status_code=403,
            detail="Broker server mismatch"
        )

    if (
        terminal_id is not None and
        stored_terminal and
        terminal_id != stored_terminal
    ):
        raise HTTPException(
            status_code=403,
            detail="Terminal ID mismatch"
        )

    # ==========================================
    # LICENSE STATUS CHECK
    # ==========================================

    if license_data.get("status") not in [None, "active", "ACTIVE"]:
        raise HTTPException(
            status_code=403,
            detail="License inactive"
        )

    return license_data