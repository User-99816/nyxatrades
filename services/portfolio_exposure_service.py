from datetime import datetime

from config.supabase_client import supabase


# ==========================================
# CONFIGURATION
# ==========================================

MAX_TOTAL_EXPOSURE_PERCENT = 10.0
MAX_SYMBOL_EXPOSURE_PERCENT = 3.0
MAX_CURRENCY_EXPOSURE_PERCENT = 5.0


# ==========================================
# FOREX CURRENCY PARSER
# ==========================================

def extract_currencies(symbol: str):

    symbol = (symbol or "").upper()

    if len(symbol) >= 6:
        return symbol[:3], symbol[3:6]

    return None, None


# ==========================================
# GET OPEN EXPOSURES
# ==========================================

def get_open_exposures(user_email: str):

    result = (
        supabase
        .table("portfolio_exposure")
        .select("*")
        .eq("user_email", user_email)
        .execute()
    )

    return result.data or []


# ==========================================
# TOTAL PORTFOLIO EXPOSURE
# ==========================================

def calculate_total_exposure(user_email: str):

    exposures = get_open_exposures(user_email)

    total = sum(
        float(row.get("exposure_percent", 0))
        for row in exposures
    )

    return round(total, 2)


# ==========================================
# SYMBOL EXPOSURE
# ==========================================

def calculate_symbol_exposure(
    user_email: str,
    symbol: str
):

    exposures = get_open_exposures(user_email)

    total = sum(
        float(row.get("exposure_percent", 0))
        for row in exposures
        if row.get("symbol") == symbol
    )

    return round(total, 2)


# ==========================================
# CURRENCY EXPOSURE
# ==========================================

def calculate_currency_exposure(
    user_email: str,
    currency: str
):

    exposures = get_open_exposures(user_email)

    total = 0

    for row in exposures:

        base, quote = extract_currencies(
            row.get("symbol")
        )

        if currency in [base, quote]:
            total += float(
                row.get("exposure_percent", 0)
            )

    return round(total, 2)


# ==========================================
# REGISTER OPEN TRADE
# ==========================================

def register_exposure(
    user_email: str,
    trade_id: str,
    symbol: str,
    direction: str,
    risk_amount: float,
    lot_size: float,
    exposure_percent: float
):

    payload = {
        "user_email": user_email,
        "trade_id": trade_id,
        "symbol": symbol,
        "direction": direction,
        "risk_amount": risk_amount,
        "lot_size": lot_size,
        "exposure_percent": exposure_percent,
        "created_at": datetime.utcnow().isoformat()
    }

    (
        supabase
        .table("portfolio_exposure")
        .insert(payload)
        .execute()
    )

    return payload


# ==========================================
# REMOVE CLOSED TRADE
# ==========================================

def remove_exposure(trade_id: str):

    return (
        supabase
        .table("portfolio_exposure")
        .delete()
        .eq("trade_id", trade_id)
        .execute()
    )


# ==========================================
# PORTFOLIO APPROVAL ENGINE
# ==========================================

def can_open_trade(
    user_email: str,
    symbol: str,
    exposure_percent: float
):

    # -----------------------------
    # TOTAL EXPOSURE
    # -----------------------------

    total_exposure = (
        calculate_total_exposure(user_email)
        + exposure_percent
    )

    if total_exposure > MAX_TOTAL_EXPOSURE_PERCENT:

        return {
            "allowed": False,
            "reason": "MAX_TOTAL_EXPOSURE_EXCEEDED",
            "current": total_exposure,
            "limit": MAX_TOTAL_EXPOSURE_PERCENT
        }

    # -----------------------------
    # SYMBOL EXPOSURE
    # -----------------------------

    symbol_exposure = (
        calculate_symbol_exposure(
            user_email,
            symbol
        )
        + exposure_percent
    )

    if symbol_exposure > MAX_SYMBOL_EXPOSURE_PERCENT:

        return {
            "allowed": False,
            "reason": "MAX_SYMBOL_EXPOSURE_EXCEEDED",
            "current": symbol_exposure,
            "limit": MAX_SYMBOL_EXPOSURE_PERCENT
        }

    # -----------------------------
    # CURRENCY EXPOSURE
    # -----------------------------

    base, quote = extract_currencies(symbol)

    if base:

        base_exposure = (
            calculate_currency_exposure(
                user_email,
                base
            )
            + exposure_percent
        )

        if base_exposure > MAX_CURRENCY_EXPOSURE_PERCENT:

            return {
                "allowed": False,
                "reason": f"{base}_EXPOSURE_LIMIT_EXCEEDED",
                "current": base_exposure,
                "limit": MAX_CURRENCY_EXPOSURE_PERCENT
            }

    if quote:

        quote_exposure = (
            calculate_currency_exposure(
                user_email,
                quote
            )
            + exposure_percent
        )

        if quote_exposure > MAX_CURRENCY_EXPOSURE_PERCENT:

            return {
                "allowed": False,
                "reason": f"{quote}_EXPOSURE_LIMIT_EXCEEDED",
                "current": quote_exposure,
                "limit": MAX_CURRENCY_EXPOSURE_PERCENT
            }

    return {
        "allowed": True,
        "reason": "APPROVED"
    }


# ==========================================
# PORTFOLIO SUMMARY
# ==========================================

def get_portfolio_summary(user_email: str):

    exposures = get_open_exposures(
        user_email
    )

    symbols = {}

    for row in exposures:

        symbol = row.get("symbol")

        symbols.setdefault(symbol, 0)

        symbols[symbol] += float(
            row.get("exposure_percent", 0)
        )

    return {
        "user_email": user_email,
        "total_exposure": calculate_total_exposure(
            user_email
        ),
        "symbols": symbols,
        "open_positions": len(exposures)
    }


# ==========================================
# TOP EXPOSURES
# ==========================================

def get_top_exposures(user_email: str):

    summary = get_portfolio_summary(
        user_email
    )

    ranked = sorted(
        summary["symbols"].items(),
        key=lambda x: x[1],
        reverse=True
    )

    return [
        {
            "symbol": symbol,
            "exposure_percent": exposure
        }
        for symbol, exposure in ranked
    ]