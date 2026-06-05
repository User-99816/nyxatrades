from datetime import datetime

from config.settings import (
    MIN_CONFIDENCE,
    MAX_DAILY_LOSS_PERCENT,
    MAX_DRAWDOWN_PERCENT,
    MAX_DAILY_TRADES_TRIAL,
    MAX_DAILY_TRADES_PRO,
    TRIAL_RISK_PER_TRADE,
    PRO_RISK_PER_TRADE,
    ALLOWED_SESSIONS,
    MIN_ATR,
    MAX_ATR
)


# ==========================================
# SESSION CHECK
# ==========================================

def is_session_allowed(session_name: str) -> bool:
    return session_name in ALLOWED_SESSIONS


# ==========================================
# CONFIDENCE CHECK
# ==========================================

def confidence_check(confidence: float):

    if confidence < MIN_CONFIDENCE:
        return {
            "allowed": False,
            "reason": "LOW_CONFIDENCE"
        }

    return {
        "allowed": True
    }


# ==========================================
# DAILY TRADE LIMIT
# ==========================================

def daily_trade_check(
    user_plan: str,
    trades_today: int
):

    limit = (
        MAX_DAILY_TRADES_TRIAL
        if user_plan == "trial"
        else MAX_DAILY_TRADES_PRO
    )

    if trades_today >= limit:
        return {
            "allowed": False,
            "reason": "DAILY_TRADE_LIMIT_REACHED"
        }

    return {
        "allowed": True
    }


# ==========================================
# DAILY LOSS CHECK
# ==========================================

def daily_loss_check(
    daily_loss_percent: float
):

    if daily_loss_percent >= MAX_DAILY_LOSS_PERCENT:
        return {
            "allowed": False,
            "reason": "DAILY_LOSS_LIMIT_REACHED"
        }

    return {
        "allowed": True
    }


# ==========================================
# DRAWDOWN CHECK
# ==========================================

def drawdown_check(
    current_drawdown_percent: float
):

    if current_drawdown_percent >= MAX_DRAWDOWN_PERCENT:
        return {
            "allowed": False,
            "reason": "KILL_SWITCH_ACTIVE"
        }

    return {
        "allowed": True
    }


# ==========================================
# NEWS FILTER
# ==========================================

def news_filter(
    major_news_nearby: bool
):

    if major_news_nearby:
        return {
            "allowed": False,
            "reason": "MAJOR_NEWS_EVENT"
        }

    return {
        "allowed": True
    }


# ==========================================
# VOLATILITY FILTER
# ==========================================

def volatility_filter(
    atr_value: float
):

    if atr_value < MIN_ATR:
        return {
            "allowed": False,
            "reason": "LOW_VOLATILITY"
        }

    if atr_value > MAX_ATR:
        return {
            "allowed": False,
            "reason": "EXTREME_VOLATILITY"
        }

    return {
        "allowed": True
    }


# ==========================================
# MAIN RISK ENGINE
# ==========================================

def evaluate_risk(
    user_plan: str,
    signal: dict,
    session_name: str = "LONDON",
    trades_today: int = 0,
    daily_loss_percent: float = 0.0,
    current_drawdown_percent: float = 0.0,
    major_news_nearby: bool = False,
    atr_value: float = 0.0010
):

    confidence = signal.get(
        "confidence",
        0
    )

    if not is_session_allowed(
        session_name
    ):
        return {
            "allowed": False,
            "reason": "SESSION_BLOCKED"
        }

    result = confidence_check(
        confidence
    )

    if not result["allowed"]:
        return result

    result = daily_trade_check(
        user_plan,
        trades_today
    )

    if not result["allowed"]:
        return result

    result = daily_loss_check(
        daily_loss_percent
    )

    if not result["allowed"]:
        return result

    result = drawdown_check(
        current_drawdown_percent
    )

    if not result["allowed"]:
        return result

    result = news_filter(
        major_news_nearby
    )

    if not result["allowed"]:
        return result

    result = volatility_filter(
        atr_value
    )

    if not result["allowed"]:
        return result

    risk_per_trade = (
        TRIAL_RISK_PER_TRADE
        if user_plan == "trial"
        else PRO_RISK_PER_TRADE
    )

    return {
        "allowed": True,
        "risk_per_trade_percent": risk_per_trade,
        "confidence": confidence,
        "timestamp": datetime.utcnow().isoformat()
    }