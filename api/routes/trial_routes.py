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
# START FREE TRIAL (PRODUCTION READY)
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
            "expires_at": expires_at.isoformat()
        }).execute()

        # IMPORTANT: Proper Supabase error handling
        if insert_result.error:
            print("[TRIAL ERROR] Supabase insert failed:", insert_result.error)

            return {
                "success": False,
                "message": "LICENSE_CREATION_FAILED",
                "error": str(insert_result.error)
            }

        print("[TRIAL] License stored successfully")

        # ==========================================
        # CREATE DOWNLOAD TOKEN (FIXED)
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

        # ==========================================
        # RESPONSE
        # ==========================================
        response = {
            "success": True,
            "message": "Trial Created Successfully",
            "email": email,
            "license_key": license_key,
            "api_key": api_key,
            "download_token": download_token,
            "expires_at": expires_at.isoformat(),
            "download_url": f"/download/ea?token={download_token}"
        }

        print("[TRIAL] Response ready:", response)

        return response

    except Exception as e:
        print("[TRIAL FATAL ERROR]", str(e))

        return {
            "success": False,
            "message": "TRIAL_CREATION_FAILED",
            "error": str(e)
        }