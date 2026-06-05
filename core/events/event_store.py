from config.supabase_client import supabase
from datetime import datetime
import json


# ==========================================
# EVENT STORE (PERSISTENCE LAYER)
# ==========================================

class EventStore:

    TABLE_NAME = "event_stream"

    # ==========================================
    # WRITE EVENT
    # ==========================================

    def write_event(
        self,
        event_type: str,
        data: dict,
        user_email: str = None,
        signal_id: str = None,
        trade_id: str = None
    ):

        event = {
            "event_type": event_type,
            "data": json.dumps(data),
            "user_email": user_email,
            "signal_id": signal_id,
            "trade_id": trade_id,
            "timestamp": datetime.utcnow().isoformat()
        }

        try:
            supabase.table(self.TABLE_NAME).insert(event).execute()
        except Exception as e:
            print(f"[EVENT STORE ERROR] {str(e)}")

        return event

    # ==========================================
    # GET EVENTS (TIME RANGE)
    # ==========================================

    def get_events(
        self,
        start_time: str = None,
        end_time: str = None,
        event_type: str = None,
        limit: int = 1000
    ):

        query = supabase.table(self.TABLE_NAME).select("*")

        if event_type:
            query = query.eq("event_type", event_type)

        if start_time:
            query = query.gte("timestamp", start_time)

        if end_time:
            query = query.lte("timestamp", end_time)

        result = query.order("timestamp", desc=False).limit(limit).execute()

        return result.data or []

    # ==========================================
    # GET TRADE HISTORY (AI FEATURE)
    # ==========================================

    def get_trade_events(self, trade_id: str):

        result = (
            supabase.table(self.TABLE_NAME)
            .select("*")
            .eq("trade_id", trade_id)
            .order("timestamp", desc=False)
            .execute()
        )

        return result.data or []


# GLOBAL INSTANCE
event_store = EventStore()