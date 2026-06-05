from config.supabase_client import supabase
from datetime import datetime


# ==========================================
# TRADE SCORING ENGINE (REINFORCEMENT SIGNAL)
# ==========================================

def calculate_trade_score(trade: dict):

    """
    Converts trade outcome into reinforcement learning signal.
    Used to improve future strategy selection.
    """

    pnl = float(trade.get("pnl", 0))
    risk = float(trade.get("risk_amount", 1))
    max_dd = float(trade.get("max_drawdown", 0))
    holding_time = float(trade.get("holding_time_minutes", 0))

    rr = pnl / risk if risk != 0 else 0

    score = 0

    # ==========================================
    # PROFIT QUALITY SCORING
    # ==========================================

    if rr >= 3:
        score += 5
    elif rr >= 2:
        score += 3
    elif rr >= 1:
        score += 2
    elif rr > 0:
        score += 1
    else:
        score -= 3

    # ==========================================
    # LOSS CONTROL PENALTY
    # ==========================================

    if rr < 0:
        score -= 2

    # ==========================================
    # EFFICIENCY BONUS (FAST PROFITS GOOD)
    # ==========================================

    if holding_time < 60 and rr > 1:
        score += 1

    # ==========================================
    # DRAWDOWN PENALTY (VERY IMPORTANT FOR FUNDS)
    # ==========================================

    if max_dd >= 0.03:
        score -= 3
    elif max_dd >= 0.02:
        score -= 2

    # ==========================================
    # FINAL NORMALIZATION
    # ==========================================

    return round(score, 4)


# ==========================================
# UPDATE STRATEGY MEMORY (LEARNING STORAGE)
# ==========================================

def update_strategy_memory(strategy_name: str, score: float, win: bool):

    """
    Updates long-term strategy performance in Supabase.
    """

    record = supabase.table("strategy_performance") \
        .select("*") \
        .eq("strategy", strategy_name) \
        .execute()

    if not record.data:

        supabase.table("strategy_performance").insert({
            "strategy": strategy_name,
            "wins": 1 if win else 0,
            "losses": 0 if win else 1,
            "avg_score": score,
            "confidence_weight": 0.5,
            "updated_at": datetime.utcnow().isoformat()
        }).execute()

        return

    data = record.data[0]

    wins = data["wins"] + (1 if win else 0)
    losses = data["losses"] + (0 if win else 1)

    total = wins + losses

    prev_avg = float(data["avg_score"])

    new_avg = ((prev_avg * (total - 1)) + score) / total

    # ==========================================
    # WIN RATE BASED CONFIDENCE
    # ==========================================

    win_rate = wins / total if total > 0 else 0

    confidence_weight = min(0.95, max(0.25, win_rate))

    # ==========================================
    # UPDATE SUPABASE
    # ==========================================

    supabase.table("strategy_performance") \
        .update({
            "wins": wins,
            "losses": losses,
            "avg_score": round(new_avg, 4),
            "confidence_weight": round(confidence_weight, 4),
            "updated_at": datetime.utcnow().isoformat()
        }) \
        .eq("strategy", strategy_name) \
        .execute()


# ==========================================
# MAIN FEEDBACK PIPELINE (CALLED ON TRADE CLOSE)
# ==========================================

def process_closed_trade(trade_id: str):

    """
    Called when EA closes a trade.
    Triggers learning update.
    """

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

    # ==========================================
    # SCORE TRADE
    # ==========================================

    score = calculate_trade_score(trade)

    # ==========================================
    # UPDATE STRATEGY MEMORY
    # ==========================================

    update_strategy_memory(
        strategy_name=trade.get("strategy", "UNKNOWN"),
        score=score,
        win=win
    )

    # ==========================================
    # STORE IN HISTORY TABLE
    # ==========================================

    supabase.table("trade_history").insert({
        "trade_id": trade_id,
        "user_email": trade.get("user_email"),
        "symbol": trade.get("symbol"),
        "strategy": trade.get("strategy"),
        "pnl": pnl,
        "score": score,
        "win": win,
        "closed_at": datetime.utcnow().isoformat()
    }).execute()

    # ==========================================
    # RETURN LEARNING RESULT
    # ==========================================

    return {
        "status": "LEARNED",
        "trade_id": trade_id,
        "score": score,
        "win": win,
        "strategy": trade.get("strategy"),
        "pnl": pnl
    }