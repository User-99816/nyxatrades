from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from services.secure_download_service import (
    create_download_token,
    verify_download_token,
    validate_download_license,
    log_download,
    mark_token_used
)

router = APIRouter(
    prefix="/download",
    tags=["Downloads"]
)


# ==========================================
# GENERATE SECURE DOWNLOAD LINK
# ==========================================

@router.post("/generate")
def generate_download(payload: dict):

    email = payload.get("email")
    license_key = payload.get("license_key")

    if not email or not license_key:

        return {
            "allowed": False,
            "message": "Missing Credentials"
        }

    validation = validate_download_license(
        email=email,
        license_key=license_key
    )

    if not validation["valid"]:

        return {
            "allowed": False,
            "message": validation["reason"]
        }

    token = create_download_token(
        license_key=license_key,
        email=email
    )

    return {
        "allowed": True,
        "message": "Download Approved",
        "token": token,
        "download_url": f"/download/ea?token={token}"
    }


# ==========================================
# DOWNLOAD EA (ONE-TIME SECURE ACCESS)
# ==========================================

@router.get("/ea")
async def download_ea(
    request: Request,
    token: str
):

    # ==========================================
    # VERIFY TOKEN
    # ==========================================

    verification = verify_download_token(token)

    if not verification["valid"]:

        return {
            "allowed": False,
            "message": verification["error"]
        }

    data = verification["data"]

    license_key = data["license_key"]
    email = data["email"]

    # ==========================================
    # MARK TOKEN AS USED (ANTI-SHARING LOCK)
    # ==========================================

    mark_token_used(token)

    # ==========================================
    # LOG DOWNLOAD
    # ==========================================

    log_download(
        license_key=license_key,
        email=email,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent", "unknown")
    )

    # ==========================================
    # EA FILE LOCATION
    # ==========================================

    ea_file = Path(
        "downloads/nyxatrades_ea.ex5"
    )

    if not ea_file.exists():

        return {
            "allowed": False,
            "message": "EA File Not Found"
        }

    return FileResponse(
        path=str(ea_file),
        filename="NyxaTradesEA.ex5",
        media_type="application/octet-stream"
    )