import json
from config.supabase_client import supabase
from datetime import datetime

from core.events.event_bus import EventBus


# ==========================================
# PERSISTENT EVENT BUS
# ==========================================

class PersistentEventBus(EventBus):

    async def emit(self, event_type: str, data: dict):

        event = await super().emit(event_type, data)

        # ==========================================
        # SAVE TO DATABASE (EVENT JOURNAL)
        # ==========================================

        try:
            supabase.table("event_stream").insert({
                "event_type": event_type,
                "payload": json.dumps(data),
                "timestamp": datetime.utcnow().isoformat()
            }).execute()

        except Exception as e:
            print(f"[DB EVENT FAIL] {str(e)}")

        return event


# ==========================================
# GLOBAL INSTANCE (USE THIS IN PRODUCTION)
# ==========================================

persistent_event_bus = PersistentEventBus()