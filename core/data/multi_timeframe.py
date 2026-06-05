from core.data.ohlc_parser import parse_ohlc


# ==========================================
# BUILD TIMEFRAME STRUCTURE
# ==========================================

def build_timeframe_data(payload):

    """
    payload format:
    {
        "M1": [...],
        "M5": [...],
        "H1": [...]
    }
    """

    if "M1" not in payload or "M5" not in payload or "H1" not in payload:
        raise ValueError("Missing timeframe data")

    m1 = parse_ohlc({"ohlc": payload["M1"]})
    m5 = parse_ohlc({"ohlc": payload["M5"]})
    h1 = parse_ohlc({"ohlc": payload["H1"]})

    return {
        "M1": m1,
        "M5": m5,
        "H1": h1
    }


# ==========================================
# CONFLUENCE ENGINE
# ==========================================

def timeframe_confluence(tf_data):

    m1 = tf_data["M1"]
    m5 = tf_data["M5"]
    h1 = tf_data["H1"]

    score_buy = 0
    score_sell = 0

    # -------------------------
    # H1 = TREND BIAS
    # -------------------------

    if h1["ema_fast"] > h1["ema_slow"]:
        score_buy += 2
    else:
        score_sell += 2

    # -------------------------
    # M5 = STRUCTURE
    # -------------------------

    if m5["structure"] == "HH_HL":
        score_buy += 2
    elif m5["structure"] == "LH_LL":
        score_sell += 2

    # -------------------------
    # M1 = ENTRY MOMENTUM
    # -------------------------

    if m1["rsi"] > 55:
        score_buy += 1
    elif m1["rsi"] < 45:
        score_sell += 1

    # -------------------------
    # FINAL DECISION
    # -------------------------

    if score_buy >= 4 and score_buy > score_sell:
        return "BUY", score_buy

    if score_sell >= 4 and score_sell > score_buy:
        return "SELL", score_sell

    return "NO_TRADE", max(score_buy, score_sell)