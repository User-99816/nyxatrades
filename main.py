
from dotenv import load_dotenv

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
# APP INITIALIZATION
# ==========================================

app = FastAPI(
    title="NYXA Trading OS",
    description="AI-driven institutional trading backend",
    version="2.0.0"
)

# ==========================================
# CORS (EA + Dashboard + Mobile support)
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
# HEALTH CHECK
# ==========================================

@app.get("/")
def root():

    return {
        "status": "NYXA TRADING OS ONLINE",
        "version": "2.0.0",
        "architecture": "AI_ORCHESTRATED_EVENT_DRIVEN_SYSTEM"
    }

# ==========================================
# SYSTEM STATUS
# ==========================================

@app.get("/system/status")
def system_status():

    return {
        "status": "ONLINE",
        "event_bus_active": True,
        "websocket_connections": len(
            manager.active_connections
        ),
        "event_buffer_size": len(
            manager.event_buffer
        ),
        "event_history_size": len(
            event_bus.get_history()
        ),
        "ai_orchestrator": "ACTIVE",
        "execution_router": "ACTIVE",
        "secure_downloads": "ACTIVE"
    }

# ==========================================
# MANUAL SIGNAL PIPELINE (TEST / DEBUG)
# ==========================================

@app.post("/system/test-signal")
async def test_signal(payload: dict):

    user_email = payload.get(
        "user_email",
        "test@system.com"
    )

    # STEP 1: AI DECISION

    decision = await ai_orchestrator_v2.evaluate_signal(
        payload,
        user_email
    )

    if decision.get("decision") == "REJECTED":
        return decision

    # STEP 2: EXECUTION

    execution = await execution_router_v2.execute_trade(
        decision,
        user_email
    )

    # STEP 3: DASHBOARD BROADCAST

    await manager.broadcast({
        "type": "SYSTEM_TEST_PIPELINE",
        "data": {
            "decision": decision,
            "execution": execution
        }
    })

    return {
        "status": "PIPELINE_EXECUTED",
        "decision": decision,
        "execution": execution
    }

# ==========================================
# EVENT STREAM ACCESS
# ==========================================

@app.get("/system/events")
def get_events(limit: int = 100):

    return {
        "events": manager.get_event_stream(
            limit=limit
        )
    }

# ==========================================
# EVENT BUS HISTORY ACCESS
# ==========================================

@app.get("/system/event-history")
def event_history(limit: int = 100):

    history = event_bus.get_history()

    return {
        "total_events": len(history),
        "events": history[-limit:]
    }

# ==========================================
# STARTUP HOOKS
# ==========================================

@app.on_event("startup")
async def startup_event():

    print("🚀 NYXA TRADING OS STARTING...")

    await event_bus.emit(
        "SYSTEM_STARTED",
        {
            "message": "Trading OS online",
            "version": "2.0.0",
            "architecture":
                "AI_ORCHESTRATED_EVENT_DRIVEN_SYSTEM"
        }
    )

# ==========================================
# SHUTDOWN HOOKS
# ==========================================

@app.on_event("shutdown")
async def shutdown_event():

    await event_bus.emit(
        "SYSTEM_SHUTDOWN",
        {
            "message": "Trading OS shutting down"
        }
    )

import os

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False
    )