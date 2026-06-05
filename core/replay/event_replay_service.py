from config.supabase_client import supabase
from datetime import datetime


# ==========================================
# SAVE EVENT (PERSISTENCE LAYER)
# ==========================================

def save_event(event: dict):

    try:
        payload = {
            "event_type": event.get("type"),
            "event_data": event.get("data"),
            "timestamp": event.get("timestamp", datetime.utcnow().isoformat())
        }

        supabase.table("event_stream").insert(payload).execute()

    except Exception:
        pass  # never break trading flow


# ==========================================
# FETCH EVENT HISTORY
# ==========================================

def get_event_history(
    event_type: str = None,
    limit: int = 100
):

    query = supabase.table("event_stream").select("*")

    if event_type:
        query = query.eq("event_type", event_type)

    result = (
        query
        .order("timestamp", desc=True)
        .limit(limit)
        .execute()
    )

    return result.data


# ==========================================
# REPLAY SINGLE EVENT STREAM
# ==========================================

def replay_events(
    event_type: str = None,
    limit: int = 50
):

    events = get_event_history(event_type, limit)

    replay_sequence = []

    for event in reversed(events):  # chronological order
        replay_sequence.append({
            "type": event["event_type"],
            "data": event["event_data"],
            "timestamp": event["timestamp"]
        })

    return replay_sequence