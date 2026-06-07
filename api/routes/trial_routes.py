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
# START FREE TRIAL
# ==========================================

@router.post("/start")
def start_trial():

    try:

        # ==========================================
        # GENERATE REAL LICENSE
        # ==========================================

        license_key = (
            "NYXA-" +
            secrets.token_hex(4).upper()
        )

        api_key = (
            "NYXA-API-" +
            secrets.token_hex(8).upper()
        )

        # Trial placeholder email
        # Replace later with authenticated user email
        email = (
            f"trial_{secrets.token_hex(4)}@nyxa.local"
        )

        expires_at = (
            datetime.utcnow() +
            timedelta(hours=1)
        )

        # ==========================================
        # SAVE LICENSE TO SUPABASE
        # ==========================================

        insert_result = (
            supabase.table("licenses")
            .insert({
                "user_email": email,
                "license_key": license_key,
                "api_key": api_key,
                "status": "active",
                "plan": "trial",
                "expires_at": expires_at.isoformat()
            })
            .execute()
        )

        if not insert_result.data:

            return {
                "success": False,
                "message": "LICENSE_CREATION_FAILED"
            }

        # ==========================================
        # CREATE DOWNLOAD TOKEN
        # ==========================================

        download_token = create_download_token(
            license_key=api_key,
            email=email
        )

        # ==========================================
        # RESPONSE
        # ==========================================

        return {
            "success": True,
            "message": "Trial Created",
            "email": email,
            "license_key": license_key,
            "api_key": api_key,
            "download_token": download_token,
            "expires_at": expires_at.isoformat(),
            "download_url": (
                f"/download/ea?token={download_token}"
            )
        }

    except Exception as e:

        print(f"[TRIAL ERROR] {str(e)}")

        return {
            "success": False,
            "message": "TRIAL_CREATION_FAILED",
            "error": str(e)
        }