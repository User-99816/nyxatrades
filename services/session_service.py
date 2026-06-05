from datetime import datetime, timedelta

from config.supabase_client import supabase
from config.settings import TRIAL_DURATION_HOURS


# ==========================================
# CREATE SESSION (TRIAL START)
# ==========================================

def create_session(user_email: str):

    now = datetime.utcnow()

    expires_at = now + timedelta(
        hours=TRIAL_DURATION_HOURS
    )

    payload = {
        "user_email": user_email,
        "started_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "active": True
    }

    # Insert session
    (
        supabase
        .table("sessions")
        .insert(payload)
        .execute()
    )

    return payload


# ==========================================
# GET ACTIVE SESSION
# ==========================================

def get_active_session(user_email: str):

    response = (
        supabase
        .table("sessions")
        .select("*")
        .eq("user_email", user_email)
        .eq("active", True)
        .order("started_at", desc=True)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


# ==========================================
# CHECK IF SESSION IS VALID
# ==========================================

def is_session_active(user_email: str):

    session = get_active_session(user_email)

    if not session:
        return {
            "active": False,
            "reason": "NO_SESSION"
        }

    now = datetime.utcnow()

    expires_at = datetime.fromisoformat(
        session["expires_at"]
    )

    if now > expires_at:

        # auto deactivate
        deactivate_session(user_email)

        return {
            "active": False,
            "reason": "TRIAL_EXPIRED"
        }

    return {
        "active": True,
        "session": session
    }


# ==========================================
# DEACTIVATE SESSION
# ==========================================

def deactivate_session(user_email: str):

    return (
        supabase
        .table("sessions")
        .update({
            "active": False
        })
        .eq("user_email", user_email)
        .execute()
    )


# ==========================================
# EXTEND SESSION (FOR PAID USERS)
# ==========================================

def extend_session(user_email: str, hours: int):

    session = get_active_session(user_email)

    if not session:
        return None

    current_expiry = datetime.fromisoformat(
        session["expires_at"]
    )

    new_expiry = current_expiry + timedelta(
        hours=hours
    )

    return (
        supabase
        .table("sessions")
        .update({
            "expires_at": new_expiry.isoformat()
        })
        .eq("user_email", user_email)
        .execute()
    )


# ==========================================
# RESET SESSION (NEW TRIAL)
# ==========================================

def reset_trial_session(user_email: str):

    # deactivate old sessions
    (
        supabase
        .table("sessions")
        .update({
            "active": False
        })
        .eq("user_email", user_email)
        .execute()
    )

    # create new session
    return create_session(user_email)