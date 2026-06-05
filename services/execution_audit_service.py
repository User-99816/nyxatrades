from datetime import datetime
from config.supabase_client import supabase


# ==========================================
# CREATE INITIAL SIGNAL AUDIT
# ==========================================

def log_signal_created(
    signal_id: str,
    user_email: str,
    symbol: str,
    direction: str,
    entry_price: float,
    strategy: str = None
):

    payload = {
        "signal_id": signal_id,
        "user_email": user_email,
        "symbol": symbol,
        "direction": direction,
        "entry_price": entry_price,
        "strategy": strategy,
        "execution_status": "SIGNAL_CREATED",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }

    return supabase.table("executions").insert(payload).execute()


# ==========================================
# MARK SIGNAL SENT TO EA
# ==========================================

def log_signal_sent(
    signal_id: str
):

    return supabase.table("executions") \
        .update({
            "execution_status": "SIGNAL_SENT",
            "updated_at": datetime.utcnow().isoformat()
        }) \
        .eq("signal_id", signal_id) \
        .execute()


# ==========================================
# LOG EXECUTION CONFIRMATION (FROM MT5 EA)
# ==========================================

def log_execution_confirmed(
    signal_id: str,
    trade_id: str,
    broker_ticket: str,
    entry_price: float = None
):

    update_data = {
        "execution_status": "EXECUTION_CONFIRMED",
        "trade_id": trade_id,
        "broker_ticket": broker_ticket,
        "updated_at": datetime.utcnow().isoformat()
    }

    if entry_price is not None:
        update_data["entry_price"] = entry_price

    return supabase.table("executions") \
        .update(update_data) \
        .eq("signal_id", signal_id) \
        .execute()


# ==========================================
# LOG TRADE UPDATE (OPTIONAL REAL-TIME)
# ==========================================

def log_trade_update(
    trade_id: str,
    current_price: float,
    pnl: float = None
):

    update_data = {
        "updated_at": datetime.utcnow().isoformat()
    }

    if current_price is not None:
        update_data["entry_price"] = current_price

    if pnl is not None:
        update_data["pnl"] = pnl

    return supabase.table("executions") \
        .update(update_data) \
        .eq("trade_id", trade_id) \
        .execute()


# ==========================================
# LOG TRADE CLOSED (FINAL STATE)
# ==========================================

def log_trade_closed(
    trade_id: str,
    exit_price: float,
    pnl: float
):

    return supabase.table("executions") \
        .update({
            "execution_status": "POSITION_CLOSED",
            "exit_price": exit_price,
            "pnl": pnl,
            "updated_at": datetime.utcnow().isoformat()
        }) \
        .eq("trade_id", trade_id) \
        .execute()


# ==========================================
# MARK FAILURE (IMPORTANT FOR DEBUGGING)
# ==========================================

def log_execution_failed(
    signal_id: str,
    reason: str
):

    return supabase.table("executions") \
        .update({
            "execution_status": "FAILED",
            "failure_reason": reason,
            "updated_at": datetime.utcnow().isoformat()
        }) \
        .eq("signal_id", signal_id) \
        .execute()