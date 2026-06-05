from fastapi import APIRouter, HTTPException

from services.user_service import get_dashboard_data
from services.session_service import is_session_active
from services.license_service import validate_license
from services.risk_service import get_risk_metrics

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)


# ==========================================
# MAIN DASHBOARD DATA ENDPOINT
# ==========================================

@router.get("/")
async def get_dashboard(email: str):

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required"
        )

    # --------------------------------------
    # SESSION CHECK (TRIAL / PAID ACCESS)
    # --------------------------------------

    session_status = is_session_active(email)

    if not session_status.get("active", False):
        return {
            "access": False,
            "reason": session_status.get(
                "reason",
                "SESSION_INACTIVE"
            ),
            "message": "Access denied. Session expired or inactive."
        }

    # --------------------------------------
    # USER + LICENSE DATA
    # --------------------------------------

    dashboard_data = get_dashboard_data(email)

    if not dashboard_data:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # --------------------------------------
    # RISK METRICS (LIVE STATE)
    # --------------------------------------

    risk = get_risk_metrics(email)

    # --------------------------------------
    # BUILD DASHBOARD RESPONSE
    # --------------------------------------

    return {
        "access": True,

        "user": dashboard_data["user"],

        "license": dashboard_data["license"],

        "session": session_status.get("session"),

        "risk": risk,

        "status": {
            "plan": dashboard_data["user"]["plan"],
            "trading_enabled": True,
            "session_active": True
        }
    }