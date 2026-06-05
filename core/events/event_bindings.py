from core.events.event_bus import event_bus
from core.events.event_types import EventTypes

from services.ai_orchestrator_service import orchestrator
from core.realtime.ws_manager import manager


# ==========================================
# AI ORCHESTRATOR BINDINGS
# ==========================================

def register_ai_event_handlers():

    event_bus.subscribe(
        EventTypes.TRADE_CLOSED,
        orchestrator.process_event
    )

    event_bus.subscribe(
        EventTypes.NEW_SIGNAL,
        orchestrator.process_event
    )

    event_bus.subscribe(
        EventTypes.EXECUTION_UPDATE,
        orchestrator.process_event
    )


# ==========================================
# WEBSOCKET DASHBOARD BINDINGS
# ==========================================

def register_dashboard_handlers():

    async def ws_broadcast(event):

        try:
            await manager.broadcast({
                "type": event["type"],
                "data": event["data"]
            })
        except:
            pass

    event_bus.subscribe(EventTypes.NEW_SIGNAL, ws_broadcast)
    event_bus.subscribe(EventTypes.TRADE_CLOSED, ws_broadcast)
    event_bus.subscribe(EventTypes.EXECUTION_UPDATE, ws_broadcast)


# ==========================================
# INITIALIZER
# ==========================================

def init_event_system():

    register_ai_event_handlers()
    register_dashboard_handlers()

    print("✅ Event system initialized")