from fastapi import APIRouter, HTTPException
import uuid
from datetime import datetime, timedelta

from services.user_service import (
    get_user,
    update_plan
)

from services.license_service import (
    validate_license,
    activate_license
)

from services.session_service import (
    extend_session
)

from services.risk_service import (
    reset_risk_metrics
)

from config.supabase_client import supabase

# 🔥 NEW SECURITY UPGRADE
from utils.security import hash_api_key


router = APIRouter(
    prefix="/activate",
    tags=["Activation"]
)


# ==========================================
# ACTIVATE USER (MAIN ENDPOINT)
# ==========================================

@router.post("/")
async def activate_user(payload: dict):

    email = payload.get("email")
    license_key = payload.get("license_key")
    plan = payload.get("plan", "pro")

    # 🔥 DEVICE BINDING UPGRADE
    mt5_account = payload.get("mt5_account")
    broker_server = payload.get("broker_server")
    terminal_id = payload.get("terminal_id")

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required"
        )

    if not license_key:
        raise HTTPException(
            status_code=400,
            detail="License key is required"
        )

    # --------------------------------------
    # VALIDATE USER
    # --------------------------------------

    user = get_user(email)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # --------------------------------------
    # VALIDATE LICENSE
    # --------------------------------------

    license_data = validate_license(license_key)

    if not license_data:
        raise HTTPException(
            status_code=401,
            detail="Invalid license key"
        )

    if license_data["user_email"] != email:
        raise HTTPException(
            status_code=403,
            detail="License does not belong to this user"
        )

    # --------------------------------------
    # DEVICE BINDING PROTECTION
    # --------------------------------------

    existing_account = license_data.get("mt5_account")

    if existing_account:

        if (
            existing_account != mt5_account or
            license_data.get("broker_server") != broker_server or
            license_data.get("terminal_id") != terminal_id
        ):
            raise HTTPException(
                status_code=403,
                detail="License already bound to another MT5 device"
            )

    # --------------------------------------
    # ACTIVATE LICENSE
    # --------------------------------------

    activate_license(license_key)

    # --------------------------------------
    # GENERATE MT5 API KEY (NEW UPGRADE)
    # --------------------------------------

    api_key = f"NYXA-{uuid.uuid4().hex[:12].upper()}"

    # 🔥 HASH API KEY BEFORE STORAGE
    api_key_hash = hash_api_key(api_key)

    expires_at = datetime.utcnow() + timedelta(days=30)

    # Store HASHED API KEY inside license record
    supabase.table("licenses").update({

        # 🔥 SECURITY UPGRADE
        "api_key_hash": api_key_hash,

        # optional legacy support
        "api_key": api_key,

        "activated": True,
        "activated_at": datetime.utcnow().isoformat(),
        "expires_at": expires_at.isoformat(),

        # 🔥 DEVICE BINDING STORAGE
        "mt5_account": mt5_account,
        "broker_server": broker_server,
        "terminal_id": terminal_id

    }).eq("license_key", license_key).execute()

    # --------------------------------------
    # UPGRADE USER PLAN
    # --------------------------------------

    update_plan(
        email=email,
        new_plan=plan
    )

    # --------------------------------------
    # EXTEND SESSION (UNLOCK ACCESS)
    # --------------------------------------

    extend_session(
        email=email,
        hours=24 * 30  # 30 days access
    )

    # --------------------------------------
    # RESET RISK (CLEAN START)
    # --------------------------------------

    try:
        reset_risk_metrics(email)
    except:
        pass  # optional if not implemented yet

    # --------------------------------------
    # STORE RISK INITIALIZATION (SAFETY LAYER)
    # --------------------------------------

    supabase.table("risk_metrics").upsert({
        "user_email": email,
        "trades_today": 0,
        "daily_loss_percent": 0,
        "current_drawdown_percent": 0
    }).execute()

    # --------------------------------------
    # RESPONSE
    # --------------------------------------

    return {
        "success": True,
        "message": "Account activated successfully",
        "email": email,
        "plan": plan,
        "status": "ACTIVE",

        # 🔥 THIS IS WHAT CONNECTS TO MT5 EA
        "api_key": api_key,
        "expires_at": expires_at.isoformat(),

        # 🔥 DEVICE INFO
        "mt5_account": mt5_account,
        "broker_server": broker_server
    }