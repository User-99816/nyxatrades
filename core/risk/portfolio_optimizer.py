from config.supabase_client import supabase


# ==========================================
# GET CURRENT PORTFOLIO EXPOSURE
# ==========================================

def get_portfolio_exposure(user_email: str):

    trades = supabase.table("open_trades") \
        .select("*") \
        .eq("user_email", user_email) \
        .eq("status", "OPEN") \
        .execute()

    exposure = {}

    for trade in trades.data:

        symbol = trade["symbol"]
        direction = trade["direction"]
        risk = float(trade.get("risk_amount", 0))

        if symbol not in exposure:
            exposure[symbol] = {"BUY": 0, "SELL": 0}

        exposure[symbol][direction] += risk

    return exposure


# ==========================================
# CHECK IF NEW TRADE IS SAFE
# ==========================================

def check_portfolio_risk(user_email: str, new_trade: dict):

    exposure = get_portfolio_exposure(user_email)

    symbol = new_trade["symbol"]
    direction = new_trade["direction"]
    risk = float(new_trade.get("risk_amount", 1))

    symbol_exposure = exposure.get(symbol, {"BUY": 0, "SELL": 0})

    total_symbol_risk = symbol_exposure["BUY"] + symbol_exposure["SELL"]

    # ==========================================
    # HARD LIMITS
    # ==========================================

    if total_symbol_risk + risk > 5:
        return {
            "allowed": False,
            "reason": "SYMBOL_EXPOSURE_LIMIT"
        }

    # Opposite position conflict check
    opposite = "SELL" if direction == "BUY" else "BUY"

    if symbol_exposure[opposite] > 3:
        return {
            "allowed": False,
            "reason": "HEDGE_CONFLICT_RISK"
        }

    return {
        "allowed": True,
        "exposure": symbol_exposure
    }