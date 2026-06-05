from datetime import datetime
from config.supabase_client import supabase


def update_heartbeat(
    user_email,
    api_key_hash,
    mt5_account,
    broker_server,
    terminal_id
):

    payload = {
        "user_email": user_email,
        "api_key_hash": api_key_hash,
        "mt5_account": mt5_account,
        "broker_server": broker_server,
        "terminal_id": terminal_id,
        "last_seen": datetime.utcnow().isoformat()
    }

    return (
        supabase
        .table("ea_connections")
        .upsert(payload)
        .execute()
    )