from fastapi import APIRouter
from core.risk.kill_switch import (
    activate_kill_switch,
    deactivate_kill_switch,
    is_kill_switch_active
)

router = APIRouter(prefix="/admin/control", tags=["Admin Control"])


# ==========================================
# GET STATUS
# ==========================================

@router.get("/status")
def get_status():
    return is_kill_switch_active()


# ==========================================
# ACTIVATE KILL SWITCH
# ==========================================

@router.post("/kill")
def kill_system(payload: dict):

    reason = payload.get("reason", "ADMIN_TRIGGERED")

    activate_kill_switch(reason)

    return {
        "status": "KILLED",
        "reason": reason
    }


# ==========================================
# RESTART SYSTEM
# ==========================================

@router.post("/restart")
def restart_system():

    deactivate_kill_switch()

    return {
        "status": "ACTIVE",
        "message": "System restarted successfully"
    }