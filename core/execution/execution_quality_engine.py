import random


# ==========================================
# SIMULATED EXECUTION CONDITIONS (REALISTIC MODEL)
# ==========================================

def get_market_conditions(symbol: str):

    return {
        "spread": random.uniform(0.1, 2.5),
        "slippage_risk": random.uniform(0, 1),
        "liquidity_score": random.uniform(0, 1)
    }


# ==========================================
# CHECK EXECUTION QUALITY
# ==========================================

def check_execution_quality(symbol: str):

    conditions = get_market_conditions(symbol)

    spread = conditions["spread"]
    slippage = conditions["slippage_risk"]
    liquidity = conditions["liquidity_score"]

    # ==========================================
    # HARD FILTERS
    # ==========================================

    if spread > 2.0:
        return {
            "allowed": False,
            "reason": "HIGH_SPREAD"
        }

    if slippage > 0.8:
        return {
            "allowed": False,
            "reason": "HIGH_SLIPPAGE_RISK"
        }

    if liquidity < 0.3:
        return {
            "allowed": False,
            "reason": "LOW_LIQUIDITY"
        }

    return {
        "allowed": True,
        "spread": spread,
        "slippage": slippage,
        "liquidity": liquidity
    }