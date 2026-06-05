from fastapi import APIRouter, HTTPException

from services.session_service import (
    create_session,
    get_active_session,
    is_session_active,
    deactivate_session,
    reset_trial_session,
    extend_session
)

router = APIRouter(
    prefix="/session",
    tags=["Session"]
)


# ==========================================
# START TRIAL SESSION
# ==========================================

@router.post("/start")
async def start_session(payload: dict):

    email = payload.get("email")

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required"
        )

    session = create_session(email)

    return {
        "success": True,
        "message": "Trial started",
        "session": session
    }


# ==========================================
# GET ACTIVE SESSION
# ==========================================

@router.get("/active")
async def active_session(email: str):

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required"
        )

    session = get_active_session(email)

    if not session:
        return {
            "active": False,
            "reason": "NO_SESSION"
        }

    return {
        "active": True,
        "session": session
    }


# ==========================================
# CHECK SESSION STATUS (TRIAL GUARD)
# ==========================================

@router.get("/status")
async def session_status(email: str):

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required"
        )

    return is_session_active(email)


# ==========================================
# DEACTIVATE SESSION
# ==========================================

@router.post("/deactivate")
async def stop_session(payload: dict):

    email = payload.get("email")

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required"
        )

    deactivate_session(email)

    return {
        "success": True,
        "message": "Session deactivated"
    }


# ==========================================
# RESET TRIAL
# ==========================================

@router.post("/reset-trial")
async def reset_trial(payload: dict):

    email = payload.get("email")

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required"
        )

    session = reset_trial_session(email)

    return {
        "success": True,
        "message": "Trial reset",
        "session": session
    }


# ==========================================
# EXTEND SESSION (PAID USERS)
# ==========================================

@router.post("/extend")
async def extend(payload: dict):

    email = payload.get("email")
    hours = payload.get("hours", 24)

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email is required"
        )

    result = extend_session(email, hours)

    if not result:
        raise HTTPException(
            status_code=404,
            detail="Session not found"
        )

    return {
        "success": True,
        "message": "Session extended",
        "hours_added": hours
    }