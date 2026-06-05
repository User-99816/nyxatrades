from datetime import datetime
from config.supabase_client import supabase

# ==========================================
# GLOBAL KILL SWITCH STATE (MEMORY CACHE)
# ==========================================

KILL_SWITCH_STATE = {
    "GLOBAL": False,
    "reason": None,
    "activated_at": None
}


# ==========================================
# LOAD STATE FROM DATABASE
# ==========================================

def _sync_from_database():

    try:

        result = (
            supabase
            .table("system_control")
            .select("*")
            .limit(1)
            .execute()
        )

        if not result.data:
            return

        row = result.data[0]

        KILL_SWITCH_STATE["GLOBAL"] = row.get(
            "kill_switch",
            False
        )

        KILL_SWITCH_STATE["reason"] = row.get(
            "reason"
        )

        KILL_SWITCH_STATE["activated_at"] = row.get(
            "activated_at"
        )

    except Exception:
        pass


# ==========================================
# ACTIVATE KILL SWITCH
# ==========================================

def activate_kill_switch(reason: str):

    timestamp = datetime.utcnow().isoformat()

    # --------------------------------------
    # MEMORY CACHE
    # --------------------------------------

    KILL_SWITCH_STATE["GLOBAL"] = True
    KILL_SWITCH_STATE["reason"] = reason
    KILL_SWITCH_STATE["activated_at"] = timestamp

    # --------------------------------------
    # DATABASE PERSISTENCE
    # --------------------------------------

    try:

        (
            supabase
            .table("system_control")
            .upsert({
                "id": 1,
                "kill_switch": True,
                "reason": reason,
                "activated_at": timestamp,
                "updated_at": timestamp
            })
            .execute()
        )

    except Exception:
        pass


# ==========================================
# DEACTIVATE KILL SWITCH
# ==========================================

def deactivate_kill_switch():

    # --------------------------------------
    # MEMORY CACHE
    # --------------------------------------

    KILL_SWITCH_STATE["GLOBAL"] = False
    KILL_SWITCH_STATE["reason"] = None
    KILL_SWITCH_STATE["activated_at"] = None

    # --------------------------------------
    # DATABASE PERSISTENCE
    # --------------------------------------

    try:

        (
            supabase
            .table("system_control")
            .upsert({
                "id": 1,
                "kill_switch": False,
                "reason": "SYSTEM_OK",
                "activated_at": None,
                "updated_at": datetime.utcnow().isoformat()
            })
            .execute()
        )

    except Exception:
        pass


# ==========================================
# CHECK STATUS
# ==========================================

def is_kill_switch_active():

    # --------------------------------------
    # ALWAYS SYNC FROM DATABASE
    # Allows multi-server consistency
    # --------------------------------------

    _sync_from_database()

    return {
        "active": KILL_SWITCH_STATE["GLOBAL"],
        "reason": KILL_SWITCH_STATE["reason"],
        "activated_at": KILL_SWITCH_STATE["activated_at"]
    }