import pandas as pd


# ==========================================
# CONVERT RAW EA OHLC → STRUCTURED DATA
# ==========================================

def parse_ohlc(payload: dict):
    """
    Expected input:
    payload["ohlc"] = [
        {"o":..., "h":..., "l":..., "c":...},
        ...
    ]
    """

    ohlc = payload.get("ohlc", [])

    if not ohlc or len(ohlc) < 20:
        raise ValueError("Insufficient OHLC data")

    df = pd.DataFrame(ohlc)

    df.columns = ["open", "high", "low", "close"]

    # ==========================================
    # BASIC SERIES
    # ==========================================

    close = df["close"]

    high = df["high"]
    low = df["low"]

    # ==========================================
    # EMA CALCULATION
    # ==========================================

    ema_fast = close.ewm(span=9).mean().iloc[-1]
    ema_slow = close.ewm(span=21).mean().iloc[-1]

    # ==========================================
    # RSI CALCULATION
    # ==========================================

    delta = close.diff()

    gain = (delta.where(delta > 0, 0)).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()

    rs = gain / (loss + 1e-10)
    rsi = 100 - (100 / (1 + rs))

    rsi_value = rsi.iloc[-1]

    # ==========================================
    # STRUCTURE DETECTION
    # ==========================================

    recent_highs = high.tail(10)
    recent_lows = low.tail(10)

    higher_high = recent_highs.iloc[-1] > recent_highs.iloc[:-1].max()
    higher_low = recent_lows.iloc[-1] > recent_lows.iloc[:-1].min()

    lower_high = recent_highs.iloc[-1] < recent_highs.iloc[:-1].max()
    lower_low = recent_lows.iloc[-1] < recent_lows.iloc[:-1].min()

    if higher_high and higher_low:
        structure = "HH_HL"
    elif lower_high and lower_low:
        structure = "LH_LL"
    else:
        structure = "RANGE"

    # ==========================================
    # LIQUIDITY DETECTION (SIMPLIFIED)
    # ==========================================

    equal_highs = abs(high.iloc[-1] - high.iloc[-2]) < 0.0002
    equal_lows = abs(low.iloc[-1] - low.iloc[-2]) < 0.0002

    liquidity_sweep = (
        high.iloc[-1] > high.iloc[-2] and close.iloc[-1] < high.iloc[-2]
    ) or (
        low.iloc[-1] < low.iloc[-2] and close.iloc[-1] > low.iloc[-2]
    )

    return {
        "ema_fast": float(ema_fast),
        "ema_slow": float(ema_slow),
        "rsi": float(rsi_value),

        "structure": structure,

        "liquidity_sweep": liquidity_sweep,
        "equal_highs": equal_highs,
        "equal_lows": equal_lows,

        "entry_price": float(close.iloc[-1]),
        "atr": float(high.tail(14).max() - low.tail(14).min())
    }