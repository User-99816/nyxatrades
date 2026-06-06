from dotenv import load_dotenv
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# ==========================================
# LOAD ENVIRONMENT VARIABLES
# ==========================================

load_dotenv()

# ==========================================
# ROUTES
# ==========================================

from api.routes.signal_routes import router as signal_router
from api.routes.trade_routes import router as trade_router
from api.routes.execution_routes import router as execution_router
from api.routes.download_routes import router as download_router

# ==========================================
# REAL-TIME SYSTEM
# ==========================================

from core.realtime.ws_manager import manager

# ==========================================
# EVENT SYSTEM
# ==========================================

from core.events.event_bus import event_bus

# ==========================================
# AI CORE ORCHESTRATION LAYER
# ==========================================

from services.ai_orchestrator_v2 import ai_orchestrator_v2
from services.execution_router_v2 import execution_router_v2


# ==========================================
# PLAN SYSTEM (NEW ADDITION)
# ==========================================

from config.supabase_client import supabase


def get_user_plan(email: str):
    """
    Fetch user plan from Supabase license table
    """
    try:
        res = (
            supabase.table("licenses")
            .select("plan, status, expires_at")
            .eq("user_email", email)
            .execute()
        )

        if not res.data:
            return "trial"

        license = res.data[0]

        if license["status"] != "active":
            return "trial"

        return license.get("plan", "trial")

    except Exception:
        return "trial"


# ==========================================
# APP INITIALIZATION
# ==========================================

app = FastAPI(
    title="NYXA Trading OS",
    description="AI-driven institutional trading backend",
    version="2.0.0"
)

# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# ROUTE REGISTRATION
# ==========================================

app.include_router(signal_router)
app.include_router(trade_router)
app.include_router(execution_router)
app.include_router(download_router)

# ==========================================
# PLAN-AWARE SYSTEM STATUS (UPGRADED)
# ==========================================

@app.get("/system/status")
def system_status():

    return {
        "status": "ONLINE",
        "event_bus_active": True,
        "websocket_connections": len(manager.active_connections),
        "event_buffer_size": len(manager.event_buffer),
        "event_history_size": len(event_bus.get_history()),
        "ai_orchestrator": "ACTIVE",
        "execution_router": "ACTIVE",
        "secure_downloads": "ACTIVE",
        "plans": ["trial", "lite", "pro"]
    }

# ==========================================
# TEST SIGNAL (PLAN AWARE)
# ==========================================

@app.post("/system/test-signal")
async def test_signal(payload: dict):

    user_email = payload.get("user_email", "test@system.com")

    # ==========================================
    # GET USER PLAN (NEW)
    # ==========================================

    plan = get_user_plan(user_email)

    # Attach plan to payload for AI engine
    payload["plan"] = plan

    # ==========================================
    # AI DECISION
    # ==========================================

    decision = await ai_orchestrator_v2.evaluate_signal(
        payload,
        user_email
    )

    if decision.get("decision") == "REJECTED":
        return decision

    # ==========================================
    # EXECUTION
    # ==========================================

    execution = await execution_router_v2.execute_trade(
        decision,
        user_email
    )

    # ==========================================
    # BROADCAST
    # ==========================================

    await manager.broadcast({
        "type": "SYSTEM_TEST_PIPELINE",
        "data": {
            "plan": plan,
            "decision": decision,
            "execution": execution
        }
    })

    return {
        "status": "PIPELINE_EXECUTED",
        "plan": plan,
        "decision": decision,
        "execution": execution
    }


# ==========================================
# EVENT STREAM ACCESS
# ==========================================

@app.get("/system/events")
def get_events(limit: int = 100):

    return {
        "events": event_bus.get_history(limit=limit)
    }


# ==========================================
# EVENT HISTORY
# ==========================================

@app.get("/system/event-history")
def event_history(limit: int = 100):

    history = event_bus.get_history()

    return {
        "total_events": len(history),
        "events": history[-limit:]
    }


# ==========================================
# STARTUP
# ==========================================

@app.on_event("startup")
async def startup_event():

    print("🚀 NYXA TRADING OS STARTING...")

    await event_bus.emit(
        "SYSTEM_STARTED",
        {
            "message": "Trading OS online",
            "version": "2.0.0",
            "plans_enabled": True
        }
    )


# ==========================================
# SHUTDOWN
# ==========================================

@app.on_event("shutdown")
async def shutdown_event():

    await event_bus.emit(
        "SYSTEM_SHUTDOWN",
        {
            "message": "Trading OS shutting down"
        }
    )


# ==========================================
# RUN SERVER
# ==========================================

port = int(os.getenv("PORT", 8000))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port
    )