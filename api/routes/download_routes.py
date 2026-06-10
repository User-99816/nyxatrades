from pathlib import Path
from fastapi import APIRouter, Request, Query
from fastapi.responses import FileResponse

from services.secure_download_service import (
    create_download_token,
    verify_download_token,
    validate_download_license,
    log_download,
    mark_token_used
)

from config.supabase_client import supabase
from datetime import datetime

router = APIRouter(
    prefix="/download",
    tags=["Downloads"]
)

# ==========================================
# CONFIG
# ==========================================

EA_FILE = Path("downloads/nyxatrades_ea.ex5")


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
            "message": "MISSING_CREDENTIALS"
        }

    # ==========================================
    # LICENSE VALIDATION (STRICT)
    # ==========================================
    validation = validate_download_license(
        email=email,
        license_key=license_key
    )

    if not validation["valid"]:
        return {
            "allowed": False,
            "message": validation["reason"]
        }

    # ==========================================
    # CREATE DOWNLOAD TOKEN
    # ==========================================
    token = create_download_token(
        license_key=license_key,
        email=email
    )

    return {
        "allowed": True,
        "message": "DOWNLOAD_APPROVED",
        "token": token,
        "download_url": f"/download/ea?token={token}"
    }


# ==========================================
# DOWNLOAD EA (SAAS-GRADE SECURITY)
# ==========================================

@router.get("/ea")
async def download_ea(
    request: Request,
    token: str = Query(None)
):

    # ==========================================
    # 1. FILE CHECK FIRST (FAIL FAST)
    # ==========================================
    if not EA_FILE.exists():
        return {
            "allowed": False,
            "message": "EA_FILE_MISSING"
        }

    # ==========================================
    # 2. IF NO TOKEN → BLOCK (SAAS SECURITY FIX)
    # ==========================================
    if not token:
        return {
            "allowed": False,
            "message": "MISSING_TOKEN"
        }

    # ==========================================
    # 3. VERIFY TOKEN
    # ==========================================
    verification = verify_download_token(token)

    if not verification.get("valid"):
        return {
            "allowed": False,
            "message": verification.get("error", "INVALID_TOKEN")
        }

    data = verification["data"]
    record = verification["record"]

    license_key = data["license_key"]
    email = data["email"]

    # ==========================================
    # 4. LICENSE DOUBLE CHECK (ANTI BYPASS)
    # ==========================================
    license_check = (
        supabase.table("licenses")
        .select("status, expires_at")
        .eq("license_key", license_key)
        .limit(1)
        .execute()
    )

    if not license_check.data:
        return {"allowed": False, "message": "LICENSE_NOT_FOUND"}

    license_data = license_check.data[0]

    if license_data.get("status") != "active":
        return {"allowed": False, "message": "LICENSE_INACTIVE"}

    expires_at = license_data.get("expires_at")

    if expires_at:
        try:
            expiry = datetime.fromisoformat(
                expires_at.replace("Z", "+00:00")
            )

            if expiry < datetime.utcnow().astimezone():
                return {"allowed": False, "message": "LICENSE_EXPIRED"}

        except Exception:
            pass

    # ==========================================
    # 5. MARK TOKEN USED (ANTI-SHARING)
    # ==========================================
    try:
        mark_token_used(token)
    except Exception as e:
        print("[TOKEN ERROR]", str(e))

    # ==========================================
    # 6. LOG DOWNLOAD (AUDIT TRAIL)
    # ==========================================
    try:
        log_download(
            license_key=license_key,
            email=email,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent", "unknown")
        )
    except Exception as e:
        print("[LOG ERROR]", str(e))

    # ==========================================
    # 7. FORCE DOWNLOAD EA FILE
    # ==========================================
    return FileResponse(
        path=str(EA_FILE),
        filename="NyxaTradesEA.ex5",
        media_type="application/octet-stream"
    )