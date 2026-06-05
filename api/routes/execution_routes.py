from fastapi import APIRouter, HTTPException
from config.supabase_client import supabase

# 🔥 SECURITY UPGRADE (HMAC AUTH)
from core.auth.hmac_auth import verify_signature
import json
from datetime import datetime

router = APIRouter(
    prefix="/execution",
    tags=["Execution"]
)


# ==========================================
# CREATE EXECUTION (SIGNAL → QUEUE)
# ==========================================

@router.post("/create")
def create_execution(payload: dict):

    # ==========================================
    # BASIC VALIDATION
    # ==========================================

    required_fields = [
        "user_email",
        "signal_id",
        "symbol",
        "direction",
        "entry_price",
        "stop_loss",
        "take_profit"
    ]

    for field in required_fields:
        if field not in payload:
            return {"error": f"missing {field}"}

    execution = {
        "user_email": payload["user_email"],
        "signal_id": payload["signal_id"],
        "symbol": payload["symbol"],
        "direction": payload["direction"],
        "entry_price": payload["entry_price"],
        "stop_loss": payload["stop_loss"],
        "take_profit": payload["take_profit"],

        # ==========================================
        # ENHANCED EXECUTION STATE
        # ==========================================
        "status": "PENDING",
        "retries": 0,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    supabase.table("execution_queue").insert(
        execution
    ).execute()

    return {
        "status": "QUEUED",
        "signal_id": payload["signal_id"]
    }


# ==========================================
# GET NEXT PENDING EXECUTION (MT5 POLLING)
# ==========================================

@router.post("/pending")
def get_pending_execution(payload: dict):

    user_email = payload.get("user_email")
    api_key = payload.get("api_key")
    timestamp = payload.get("timestamp")
    signature = payload.get("signature")

    if not user_email:
        raise HTTPException(status_code=400, detail="Missing user_email")

    # ==========================================
    # FETCH LICENSE FOR HMAC SECRET
    # ==========================================

    license_data = supabase.table("licenses") \
        .select("*") \
        .eq("api_key", api_key) \
        .limit(1) \
        .execute()

    if not license_data.data:
        raise HTTPException(status_code=403, detail="Invalid API key")

    license_row = license_data.data[0]

    user_secret = license_row.get("hmac_secret", api_key)

    # ==========================================
    # HMAC AUTH VALIDATION
    # ==========================================

    payload_copy = payload.copy()
    payload_copy.pop("signature", None)

    payload_string = json.dumps(payload_copy, sort_keys=True)

    if signature:
        valid = verify_signature(
            payload_string,
            timestamp,
            signature,
            user_secret
        )

        if not valid:
            raise HTTPException(status_code=403, detail="HMAC verification failed")

    # ==========================================
    # FETCH PENDING EXECUTION
    # ==========================================

    result = (
        supabase.table("execution_queue")
        .select("*")
        .eq("user_email", user_email)
        .eq("status", "PENDING")
        .order("created_at", desc=False)
        .limit(1)
        .execute()
    )

    if not result.data:
        return {
            "status": "NO_SIGNAL"
        }

    execution = result.data[0]

    # ==========================================
    # LOCK EXECUTION (PREVENT DOUBLE EXECUTION)
    # ==========================================

    supabase.table("execution_queue") \
        .update({
            "status": "SENT",
            "updated_at": datetime.utcnow().isoformat()
        }) \
        .eq("id", execution["id"]) \
        .execute()

    return {
        "status": "OK",
        "execution": execution
    }