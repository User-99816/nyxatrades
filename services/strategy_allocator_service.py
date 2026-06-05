from datetime import datetime

from services.strategy_performance_service import (
    get_all_strategies
)

# ==========================================
# CONFIGURATION
# ==========================================

MIN_WEIGHT = 0.25
BASE_WEIGHT = 1.00
MAX_WEIGHT = 1.50

MIN_TRADES_REQUIRED = 20

DISABLE_BELOW_WIN_RATE = 40.0
DISABLE_BELOW_PROFIT_FACTOR = 0.90


# ==========================================
# CALCULATE STRATEGY ALLOCATION
# ==========================================

def calculate_strategy_weight(strategy: dict):

    total_trades = int(strategy.get("total_trades", 0))
    win_rate = float(strategy.get("win_rate", 0))
    profit_factor = float(strategy.get("profit_factor", 0))

    if total_trades < MIN_TRADES_REQUIRED:
        return {
            "strategy": strategy["strategy"],
            "enabled": True,
            "weight": BASE_WEIGHT,
            "reason": "INSUFFICIENT_DATA"
        }

    if (
        win_rate < DISABLE_BELOW_WIN_RATE
        and profit_factor < DISABLE_BELOW_PROFIT_FACTOR
    ):
        return {
            "strategy": strategy["strategy"],
            "enabled": False,
            "weight": 0,
            "reason": "UNDERPERFORMING"
        }

    score = (
        (win_rate / 100.0) * 0.6
        + min(profit_factor / 3.0, 1.0) * 0.4
    )

    weight = MIN_WEIGHT + (
        score * (MAX_WEIGHT - MIN_WEIGHT)
    )

    weight = round(
        max(MIN_WEIGHT, min(weight, MAX_WEIGHT)),
        2
    )

    return {
        "strategy": strategy["strategy"],
        "enabled": True,
        "weight": weight,
        "reason": "ACTIVE"
    }


# ==========================================
# GET ALL ALLOCATIONS
# ==========================================

def get_strategy_allocations():

    strategies = get_all_strategies()

    allocations = []

    for strategy in strategies:
        allocations.append(
            calculate_strategy_weight(strategy)
        )

    allocations.sort(
        key=lambda x: x["weight"],
        reverse=True
    )

    return allocations


# ==========================================
# GET BEST ALLOCATION
# ==========================================

def get_best_allocation():

    allocations = get_strategy_allocations()

    if not allocations:
        return None

    return allocations[0]


# ==========================================
# CHECK IF STRATEGY CAN TRADE
# ==========================================

def strategy_is_enabled(
    strategy_name: str
):

    allocations = get_strategy_allocations()

    for allocation in allocations:

        if allocation["strategy"] == strategy_name:

            return allocation["enabled"]

    return True


# ==========================================
# GET RISK MULTIPLIER
# ==========================================

def get_strategy_risk_multiplier(
    strategy_name: str
):

    allocations = get_strategy_allocations()

    for allocation in allocations:

        if allocation["strategy"] == strategy_name:

            if not allocation["enabled"]:
                return 0

            return allocation["weight"]

    return BASE_WEIGHT


# ==========================================
# STRATEGY PORTFOLIO SUMMARY
# ==========================================

def get_portfolio_summary():

    allocations = get_strategy_allocations()

    enabled = len([
        a for a in allocations
        if a["enabled"]
    ])

    disabled = len([
        a for a in allocations
        if not a["enabled"]
    ])

    return {
        "generated_at": datetime.utcnow().isoformat(),
        "total_strategies": len(allocations),
        "enabled": enabled,
        "disabled": disabled,
        "allocations": allocations
    }