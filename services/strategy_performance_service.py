from datetime import datetime
from config.supabase_client import supabase


# ==========================================
# GET STRATEGY
# ==========================================

def get_strategy(strategy: str):

    result = (
        supabase
        .table("strategy_performance")
        .select("*")
        .eq("strategy", strategy)
        .limit(1)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


# ==========================================
# CREATE STRATEGY RECORD
# ==========================================

def create_strategy(strategy: str):

    payload = {
        "strategy": strategy,
        "total_trades": 0,
        "wins": 0,
        "losses": 0,
        "total_pnl": 0,
        "gross_profit": 0,
        "gross_loss": 0,
        "win_rate": 0,
        "profit_factor": 0,
        "avg_pnl": 0,
        "best_trade": 0,
        "worst_trade": 0,
        "updated_at": datetime.utcnow().isoformat()
    }

    (
        supabase
        .table("strategy_performance")
        .insert(payload)
        .execute()
    )

    return payload


# ==========================================
# UPDATE STRATEGY PERFORMANCE
# ==========================================

def update_strategy_stats(
    strategy: str,
    pnl: float
):

    record = get_strategy(strategy)

    if not record:
        record = create_strategy(strategy)

    total_trades = int(record.get("total_trades", 0))
    wins = int(record.get("wins", 0))
    losses = int(record.get("losses", 0))

    total_pnl = float(record.get("total_pnl", 0))

    gross_profit = float(record.get("gross_profit", 0))
    gross_loss = float(record.get("gross_loss", 0))

    best_trade = float(record.get("best_trade", 0))
    worst_trade = float(record.get("worst_trade", 0))

    total_trades += 1
    total_pnl += pnl

    if pnl > 0:
        wins += 1
        gross_profit += pnl

        if pnl > best_trade:
            best_trade = pnl

    elif pnl < 0:
        losses += 1
        gross_loss += abs(pnl)

        if worst_trade == 0:
            worst_trade = pnl
        else:
            worst_trade = min(worst_trade, pnl)

    win_rate = 0

    if total_trades > 0:
        win_rate = round(
            (wins / total_trades) * 100,
            2
        )

    avg_pnl = 0

    if total_trades > 0:
        avg_pnl = round(
            total_pnl / total_trades,
            2
        )

    if gross_loss == 0:
        profit_factor = gross_profit
    else:
        profit_factor = round(
            gross_profit / gross_loss,
            2
        )

    payload = {
        "total_trades": total_trades,
        "wins": wins,
        "losses": losses,

        "total_pnl": round(total_pnl, 2),

        "gross_profit": round(gross_profit, 2),
        "gross_loss": round(gross_loss, 2),

        "win_rate": win_rate,
        "profit_factor": profit_factor,

        "avg_pnl": avg_pnl,

        "best_trade": round(best_trade, 2),
        "worst_trade": round(worst_trade, 2),

        "updated_at": datetime.utcnow().isoformat()
    }

    (
        supabase
        .table("strategy_performance")
        .update(payload)
        .eq("strategy", strategy)
        .execute()
    )

    return {
        "strategy": strategy,
        **payload
    }


# ==========================================
# GET ALL STRATEGIES
# ==========================================

def get_all_strategies():

    result = (
        supabase
        .table("strategy_performance")
        .select("*")
        .order("total_pnl", desc=True)
        .execute()
    )

    return result.data or []


# ==========================================
# GET BEST STRATEGY
# ==========================================

def get_best_strategy():

    result = (
        supabase
        .table("strategy_performance")
        .select("*")
        .order("total_pnl", desc=True)
        .limit(1)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


# ==========================================
# GET WORST STRATEGY
# ==========================================

def get_worst_strategy():

    result = (
        supabase
        .table("strategy_performance")
        .select("*")
        .order("total_pnl")
        .limit(1)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


# ==========================================
# GET TOP N STRATEGIES
# ==========================================

def get_top_strategies(limit: int = 5):

    result = (
        supabase
        .table("strategy_performance")
        .select("*")
        .order("total_pnl", desc=True)
        .limit(limit)
        .execute()
    )

    return result.data or []


# ==========================================
# GET STRATEGY RANKINGS
# ==========================================

def get_strategy_rankings():

    strategies = get_all_strategies()

    rankings = []

    for rank, strategy in enumerate(
        strategies,
        start=1
    ):
        rankings.append({
            "rank": rank,
            **strategy
        })

    return rankings


# ==========================================
# RESET STRATEGY
# ==========================================

def reset_strategy(strategy: str):

    return (
        supabase
        .table("strategy_performance")
        .update({
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "total_pnl": 0,
            "gross_profit": 0,
            "gross_loss": 0,
            "win_rate": 0,
            "profit_factor": 0,
            "avg_pnl": 0,
            "best_trade": 0,
            "worst_trade": 0,
            "updated_at": datetime.utcnow().isoformat()
        })
        .eq("strategy", strategy)
        .execute()
    )