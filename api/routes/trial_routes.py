from fastapi import APIRouter
from datetime import datetime, timedelta
import secrets

from config.supabase_client import supabase
from services.secure_download_service import create_download_token

router = APIRouter(
    prefix="/trial",
    tags=["Trial"]
)

# ==========================================
# START FREE TRIAL (1 HOUR)
# ==========================================
@router.post("/start")
def start_trial():

    try:
        print("[TRIAL] Starting new trial...")

        # ==========================================
        # GENERATE CREDENTIALS
        # ==========================================
        license_key = "NYXA-" + secrets.token_hex(4).upper()
        api_key = "NYXA-API-" + secrets.token_hex(8).upper()

        email = f"trial_{secrets.token_hex(4)}@nyxa.local"

        expires_at = datetime.utcnow() + timedelta(hours=1)

        # ==========================================
        # SAVE TO SUPABASE
        # ==========================================
        insert_result = supabase.table("licenses").insert({
            "user_email": email,
            "license_key": license_key,
            "api_key": api_key,
            "status": "active",
            "plan": "trial",
            "expires_at": expires_at.isoformat(),
            "mt5_account": None   # 🔐 DEVICE LOCK READY FIELD
        }).execute()

        if not insert_result.data:
            print("[TRIAL ERROR] Insert failed")
            return {
                "success": False,
                "message": "LICENSE_CREATION_FAILED"
            }

        print("[TRIAL] License stored successfully")

        # ==========================================
        # CREATE DOWNLOAD TOKEN
        # ==========================================
        download_token = create_download_token(
            license_key=license_key,
            email=email
        )

        if not download_token:
            print("[TRIAL ERROR] Token generation failed")
            return {
                "success": False,
                "message": "TOKEN_CREATION_FAILED"
            }

        print("[TRIAL] Download token created")

        return {
            "success": True,
            "message": "Trial Created Successfully",
            "email": email,
            "license_key": license_key,
            "api_key": api_key,
            "download_token": download_token,
            "expires_at": expires_at.isoformat(),
            "download_url": f"/download/ea?token={download_token}"
        }

    except Exception as e:
        print("[TRIAL FATAL ERROR]", str(e))
        return {
            "success": False,
            "message": "TRIAL_CREATION_FAILED",
            "error": str(e)
        }


# ==========================================
# CREATE PAID LICENSE (30 DAYS)
# ==========================================
@router.post("/create-paid")
def create_paid_license():

    try:
        print("[PAID] Creating paid license...")

        # ==========================================
        # GENERATE CREDENTIALS
        # ==========================================
        license_key = "NYXA-" + secrets.token_hex(4).upper()
        api_key = "NYXA-API-" + secrets.token_hex(8).upper()

        email = f"paid_{secrets.token_hex(4)}@nyxa.local"

        expires_at = datetime.utcnow() + timedelta(days=30)

        # ==========================================
        # SAVE TO SUPABASE
        # ==========================================
        insert_result = supabase.table("licenses").insert({
            "user_email": email,
            "license_key": license_key,
            "api_key": api_key,
            "status": "active",
            "plan": "paid",
            "expires_at": expires_at.isoformat(),
            "mt5_account": None   # 🔐 DEVICE LOCK READY FIELD
        }).execute()

        if not insert_result.data:
            print("[PAID ERROR] Insert failed")
            return {
                "success": False,
                "message": "LICENSE_CREATION_FAILED"
            }

        print("[PAID] License stored successfully")

        # ==========================================
        # CREATE DOWNLOAD TOKEN
        # ==========================================
        download_token = create_download_token(
            license_key=license_key,
            email=email
        )

        if not download_token:
            print("[PAID ERROR] Token generation failed")
            return {
                "success": False,
                "message": "TOKEN_CREATION_FAILED"
            }

        print("[PAID] Download token created")

        return {
            "success": True,
            "message": "Paid License Created Successfully",
            "email": email,
            "license_key": license_key,
            "api_key": api_key,
            "download_token": download_token,
            "expires_at": expires_at.isoformat(),
            "download_url": f"/download/ea?token={download_token}"
        }

    except Exception as e:
        print("[PAID FATAL ERROR]", str(e))
        return {
            "success": False,
            "message": "PAID_LICENSE_FAILED",
            "error": str(e)
        }


# ==========================================
# 🔐 DEVICE LOCKING ENDPOINT (NEW)
# ==========================================
@router.post("/validate-device")
def validate_device(payload: dict):

    try:
        api_key = payload.get("api_key")
        mt5_account = payload.get("mt5_account")

        print("[DEVICE CHECK] API:", api_key)
        print("[DEVICE CHECK] MT5:", mt5_account)

        # ==========================================
        # GET LICENSE
        # ==========================================
        result = supabase.table("licenses") \
            .select("*") \
            .eq("api_key", api_key) \
            .execute()

        if not result.data:
            return {
                "valid": False,
                "reason": "LICENSE_NOT_FOUND"
            }

        license = result.data[0]

        # ==========================================
        # EXPIRY CHECK
        # ==========================================
        if datetime.utcnow() > datetime.fromisoformat(license["expires_at"]):
            return {
                "valid": False,
                "reason": "EXPIRED"
            }

        # ==========================================
        # DEVICE LOCK LOGIC
        # ==========================================
        stored_account = license.get("mt5_account")

        # FIRST TIME USE → bind device
        if stored_account is None:
            supabase.table("licenses") \
                .update({"mt5_account": mt5_account}) \
                .eq("api_key", api_key) \
                .execute()

            return {
                "valid": True,
                "bound": True,
                "message": "Device bound successfully"
            }

        # SAME DEVICE → allow
        if stored_account == mt5_account:
            return {
                "valid": True,
                "bound": True,
                "message": "Device verified"
            }

        # DIFFERENT DEVICE → BLOCK
        return {
            "valid": False,
            "reason": "DEVICE_MISMATCH",
            "message": "License already used on another MT5 account"
        }

    except Exception as e:
        return {
            "valid": False,
            "reason": "SERVER_ERROR",
            "error": str(e)
        }