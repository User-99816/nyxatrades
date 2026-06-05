from datetime import datetime


# ==========================================
# INSTITUTIONAL RISK ENGINE
# ==========================================

def evaluate_institutional_risk(user_email: str, metrics: dict, signal: dict):

    """
    metrics from Supabase:
    - equity
    - balance
    - peak_equity
    - daily_start_equity
    - trades_today
    - daily_loss_percent
    - current_drawdown_percent
    """

    equity = float(metrics.get("equity", 0))
    peak_equity = float(metrics.get("peak_equity", equity))
    daily_start = float(metrics.get("daily_start_equity", equity))

    daily_loss_percent = float(metrics.get("daily_loss_percent", 0))
    drawdown_percent = float(metrics.get("current_drawdown_percent", 0))

    trades_today = int(metrics.get("trades_today", 0))

    # ==========================================
    # 1. EQUITY CURVE PROTECTION
    # ==========================================

    if equity < peak_equity * 0.95:
        return {
            "allowed": False,
            "reason": "EQUITY_CURVE_BREACH",
            "kill_switch": True
        }

    # ==========================================
    # 2. DAILY LOSS LIMIT
    # ==========================================

    if daily_loss_percent >= 3.0:
        return {
            "allowed": False,
            "reason": "DAILY_LOSS_LIMIT_REACHED",
            "kill_switch": True
        }

    # ==========================================
    # 3. DRAWDOWN PROTECTION
    # ==========================================

    if drawdown_percent >= 5.0:
        return {
            "allowed": False,
            "reason": "MAX_DRAWDOWN_EXCEEDED",
            "kill_switch": True
        }

    # ==========================================
    # 4. TRADE FREQUENCY CONTROL
    # ==========================================

    if trades_today >= 10:
        return {
            "allowed": False,
            "reason": "TOO_MANY_TRADES_TODAY",
            "kill_switch": False
        }

    # ==========================================
    # 5. SIGNAL QUALITY FILTER
    # ==========================================

    confidence = signal.get("confidence", 0)

    if confidence < 0.65:
        return {
            "allowed": False,
            "reason": "LOW_SIGNAL_CONFIDENCE",
            "kill_switch": False
        }

    # ==========================================
    # 6. SAFE MODE TRIGGER
    # ==========================================

    if daily_loss_percent >= 2.0 or drawdown_percent >= 3.5:
        return {
            "allowed": True,
            "safe_mode": True,
            "risk_reduction": 0.5,
            "reason": "SAFE_MODE_ACTIVE"
        }

    # ==========================================
    # 7. NORMAL MODE
    # ==========================================

    return {
        "allowed": True,
        "safe_mode": False,
        "risk_reduction": 1.0,
        "reason": "OK"
    }