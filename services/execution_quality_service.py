from datetime import datetime


# ==========================================
# CONFIGURATION (ADJUST PER BROKER)
# ==========================================

MAX_SPREAD_PIPS = 2.5
MAX_SLIPPAGE_PIPS = 2.0
MIN_EXECUTION_SCORE = 70


# ==========================================
# EXECUTION QUALITY ANALYZER
# ==========================================

def evaluate_execution_quality(
    symbol: str,
    spread: float,
    slippage: float,
    volatility: float = 0,
    liquidity_score: float = 100
):

    """
    Returns execution quality assessment before trade entry.
    """

    reasons = []
    score = 100

    # ==========================================
    # SPREAD CHECK
    # ==========================================

    if spread > MAX_SPREAD_PIPS:
        reasons.append("HIGH_SPREAD")
        score -= 30

    # ==========================================
    # SLIPPAGE CHECK
    # ==========================================

    if slippage > MAX_SLIPPAGE_PIPS:
        reasons.append("HIGH_SLIPPAGE")
        score -= 25

    # ==========================================
    # VOLATILITY CHECK
    # ==========================================

    if volatility > 2.0:
        reasons.append("HIGH_VOLATILITY")
        score -= 20

    # ==========================================
    # LIQUIDITY CHECK
    # ==========================================

    if liquidity_score < 60:
        reasons.append("LOW_LIQUIDITY")
        score -= 25

    # ==========================================
    # FINAL SCORE NORMALIZATION
    # ==========================================

    if score < 0:
        score = 0

    decision = "APPROVED" if score >= MIN_EXECUTION_SCORE else "REJECTED"

    return {
        "symbol": symbol,
        "score": score,
        "decision": decision,
        "spread": spread,
        "slippage": slippage,
        "volatility": volatility,
        "liquidity_score": liquidity_score,
        "reasons": reasons,
        "timestamp": datetime.utcnow().isoformat()
    }