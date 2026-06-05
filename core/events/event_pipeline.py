from datetime import datetime

from core.events.event_bus import event_bus
from core.events.event_store_service import event_store_service
from core.realtime.ws_manager import manager


class EventPipeline:

    # ==========================================
    # SINGLE ENTRY POINT (USE THIS EVERYWHERE)
    # ==========================================

    async def emit(self, event_type: str, data: dict):

        event = {
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

        # ==========================================
        # 1. STORE EVENT (HARD MEMORY - SUPABASE)
        # ==========================================

        try:
            event_store_service.store_event(event_type, data)
        except Exception as e:
            print(f"[PIPELINE STORE ERROR] {str(e)}")

        # ==========================================
        # 2. REAL-TIME EVENT BUS (IN-MEMORY AI)
        # ==========================================

        try:
            await event_bus.emit(event_type, data)
        except Exception as e:
            print(f"[PIPELINE BUS ERROR] {str(e)}")

        # ==========================================
        # 3. WEBSOCKET BROADCAST (DASHBOARD)
        # ==========================================

        try:
            await manager.broadcast({
                "type": event_type,
                "data": data,
                "timestamp": event["timestamp"]
            })
        except Exception as e:
            print(f"[PIPELINE WS ERROR] {str(e)}")

        return event

    # ==========================================
    # BATCH EVENTS (FOR EA / HIGH FREQUENCY)
    # ==========================================

    async def emit_batch(self, events: list):

        results = []

        for e in events:

            result = await self.emit(
                e.get("type"),
                e.get("data", {})
            )

            results.append(result)

        return results

    # ==========================================
    # REPLAY HOOK (FOR AI + BACKTEST)
    # ==========================================

    def replay(self, limit: int = 1000):

        return event_store_service.get_events(limit=limit)


# ==========================================
# SINGLETON
# ==========================================

event_pipeline = EventPipeline()