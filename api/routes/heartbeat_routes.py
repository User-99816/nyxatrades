from fastapi import APIRouter, HTTPException

from core.auth.api_auth import validate_api_key
from services.heartbeat_service import update_heartbeat
from utils.security import hash_api_key

router = APIRouter(
    prefix="/heartbeat",
    tags=["Heartbeat"]
)


@router.post("/")
async def heartbeat(payload: dict):

    api_key = payload.get("api_key")

    mt5_account = payload.get("mt5_account")
    broker_server = payload.get("broker_server")
    terminal_id = payload.get("terminal_id")

    license_data = validate_api_key(
        api_key,
        mt5_account,
        broker_server,
        terminal_id
    )

    update_heartbeat(
        user_email=license_data["user_email"],
        api_key_hash=hash_api_key(api_key),
        mt5_account=mt5_account,
        broker_server=broker_server,
        terminal_id=terminal_id
    )

    return {
        "status": "ONLINE",
        "timestamp": license_data.get("activated_at")
    }