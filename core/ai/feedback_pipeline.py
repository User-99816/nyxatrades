from config.supabase_client import supabase

from core.ai.trade_learning_engine import (
    calculate_trade_score,
    update_strategy_memory
)

from datetime import datetime


# ==========================================
# PROCESS CLOSED TRADE (MAIN ENTRY POINT)
# ==========================================

def process_closed_trade(trade_id: str):

    """
    Called by:
    /trade/close endpoint when EA closes a trade.

    This triggers:
    - scoring
    - strategy learning
    - history storage
    """

    # ==========================================
    # FETCH TRADE FROM SUPABASE
    # ==========================================

    trade_res = supabase.table("open_trades") \
        .select("*") \
        .eq("trade_id", trade_id) \
        .execute()

    if not trade_res.data:
        return {
            "status": "ERROR",
            "reason": "TRADE_NOT_FOUND"
        }

    trade = trade_res.data[0]

    pnl = float(trade.get("pnl", 0))
    win = pnl > 0

    strategy = trade.get("strategy", "UNKNOWN")

    # ==========================================
    # CALCULATE LEARNING SCORE
    # ==========================================

    score = calculate_trade_score(trade)

    # ==========================================
    # UPDATE STRATEGY MEMORY (AI LEARNING)
    # ==========================================

    update_strategy_memory(
        strategy_name=strategy,
        score=score,
        win=win
    )

    # ==========================================
    # STORE TRADE IN HISTORY TABLE
    # ==========================================

    supabase.table("trade_history").insert({
        "trade_id": trade_id,
        "user_email": trade.get("user_email"),
        "symbol": trade.get("symbol"),
        "strategy": strategy,
        "direction": trade.get("direction"),

        "entry_price": trade.get("entry_price"),
        "exit_price": trade.get("exit_price"),

        "pnl": pnl,
        "risk_amount": trade.get("risk_amount"),

        "score": score,
        "win": win,

        "max_drawdown": trade.get("max_drawdown", 0),
        "holding_time_minutes": trade.get("holding_time_minutes", 0),

        "closed_at": datetime.utcnow().isoformat()
    }).execute()

    # ==========================================
    # OPTIONAL: UPDATE RISK PROFILE (FUTURE USE)
    # ==========================================

    supabase.table("risk_metrics") \
        .update({
            "last_trade_score": score,
            "last_trade_pnl": pnl,
            "updated_at": datetime.utcnow().isoformat()
        }) \
        .eq("user_email", trade.get("user_email")) \
        .execute()

    # ==========================================
    # RETURN LEARNING RESULT
    # ==========================================

    return {
        "status": "LEARNED",
        "trade_id": trade_id,
        "strategy": strategy,
        "score": score,
        "win": win,
        "pnl": pnl
    }