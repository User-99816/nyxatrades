from fastapi import APIRouter
import os

router = APIRouter(prefix="/admin-auth", tags=["AdminAuth"])

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "078G@b2023df")


@router.post("/login")
def admin_login(payload: dict):

    password = payload.get("password")

    if password != ADMIN_PASSWORD:
        return {
            "success": False,
            "message": "Invalid password"
        }

    return {
        "success": True,
        "token": "NYXA_ADMIN_SESSION"
    }