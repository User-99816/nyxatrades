from datetime import datetime, timedelta
from config.supabase_client import supabase

from core.events.event_bus import event_bus


class EventStoreService:

    # ==========================================
    # WRITE EVENT TO SUPABASE (SOURCE OF TRUTH)
    # ==========================================

    async def store_event(self, event_type: str, data: dict):

        event = {
            "event_type": event_type,
            "event_data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            supabase.table("event_stream").insert(event).execute()
        except Exception as e:
            print(f"[EVENT STORE ERROR] {str(e)}")

        return event

    # ==========================================
    # STORE + BROADCAST (HYBRID PIPELINE)
    # ==========================================

    async def emit(self, event_type: str, data: dict):

        # 1. store in database (durable memory)
        event = await self.store_event(event_type, data)

        # 2. send to in-memory event bus (real-time system)
        try:
            await event_bus.emit(event_type, data)
        except Exception as e:
            print(f"[EVENT BUS ERROR] {str(e)}")

        return event

    # ==========================================
    # GET FULL EVENT HISTORY (REPLAY ENGINE)
    # ==========================================

    def get_events(self, limit: int = 1000):

        try:
            response = (
                supabase.table("event_stream")
                .select("*")
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
            )

            return response.data or []

        except Exception as e:
            print(f"[EVENT FETCH ERROR] {str(e)}")
            return []

    # ==========================================
    # GET EVENTS BY TYPE (ML FILTERING)
    # ==========================================

    def get_events_by_type(self, event_type: str, limit: int = 1000):

        try:
            response = (
                supabase.table("event_stream")
                .select("*")
                .eq("event_type", event_type)
                .order("timestamp", desc=True)
                .limit(limit)
                .execute()
            )

            return response.data or []

        except Exception as e:
            print(f"[EVENT TYPE FETCH ERROR] {str(e)}")
            return []

    # ==========================================
    # TIME RANGE REPLAY (BACKTEST ENGINE CORE)
    # ==========================================

    def get_events_between(self, start_time: str, end_time: str):

        try:
            response = (
                supabase.table("event_stream")
                .select("*")
                .gte("timestamp", start_time)
                .lte("timestamp", end_time)
                .order("timestamp", asc=True)
                .execute()
            )

            return response.data or []

        except Exception as e:
            print(f"[EVENT RANGE ERROR] {str(e)}")
            return []

    # ==========================================
    # TRADE REPLAY (FULL TRADE JOURNEY)
    # ==========================================

    def replay_trade(self, trade_id: str):

        try:
            response = (
                supabase.table("event_stream")
                .select("*")
                .contains("event_data", {"trade_id": trade_id})
                .order("timestamp", asc=True)
                .execute()
            )

            return response.data or []

        except Exception as e:
            print(f"[TRADE REPLAY ERROR] {str(e)}")
            return []

    # ==========================================
    # AI DATASET EXPORT (ML TRAINING READY)
    # ==========================================

    def export_training_dataset(self, event_type: str = "TRADE_CLOSED"):

        events = self.get_events_by_type(event_type, limit=10000)

        dataset = []

        for e in events:

            dataset.append({
                "features": e.get("event_data", {}),
                "label": e.get("event_type"),
                "timestamp": e.get("timestamp")
            })

        return dataset

    # ==========================================
    # CLEANUP OLD EVENTS (PERFORMANCE CONTROL)
    # ==========================================

    def cleanup_old_events(self, days: int = 30):

        cutoff = datetime.utcnow() - timedelta(days=days)

        try:
            supabase.table("event_stream") \
                .delete() \
                .lt("timestamp", cutoff.isoformat()) \
                .execute()

        except Exception as e:
            print(f"[EVENT CLEANUP ERROR] {str(e)}")


# ==========================================
# GLOBAL INSTANCE
# ==========================================

event_store_service = EventStoreService()