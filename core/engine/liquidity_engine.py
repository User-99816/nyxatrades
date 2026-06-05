def detect_order_blocks(ohlc):

    """
    Order Block:
    last bullish candle before strong bearish move
    """

    blocks = []

    for i in range(2, len(ohlc)):

        prev = ohlc[i - 2]
        curr = ohlc[i - 1]
        next_c = ohlc[i]

        bullish_to_bearish = (
            prev["c"] > prev["o"] and
            next_c["c"] < next_c["o"]
        )

        bearish_to_bullish = (
            prev["c"] < prev["o"] and
            next_c["c"] > next_c["o"]
        )

        if bullish_to_bearish or bearish_to_bullish:
            blocks.append(prev)

    return blocks


# ==========================================
# FAIR VALUE GAP (FVG)
# ==========================================

def detect_fvg(ohlc):

    fvgs = []

    for i in range(2, len(ohlc)):

        prev = ohlc[i - 2]
        curr = ohlc[i - 1]
        next_c = ohlc[i]

        # bullish FVG
        if next_c["low"] > prev["high"]:
            fvgs.append({
                "type": "BULLISH_FVG",
                "zone": (prev["high"], next_c["low"])
            })

        # bearish FVG
        if next_c["high"] < prev["low"]:
            fvgs.append({
                "type": "BEARISH_FVG",
                "zone": (next_c["high"], prev["low"])
            })

    return fvgs


# ==========================================
# LIQUIDITY SCORE
# ==========================================

def liquidity_bias(ohlc):

    order_blocks = detect_order_blocks(ohlc)
    fvgs = detect_fvg(ohlc)

    score = 0

    if len(order_blocks) > 2:
        score += 1

    if len(fvgs) > 2:
        score += 1

    return {
        "score": score,
        "order_blocks": order_blocks,
        "fvgs": fvgs
    }