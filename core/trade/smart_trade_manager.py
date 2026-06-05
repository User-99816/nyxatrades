from config.supabase_client import supabase


# ==========================================
# BREAK EVEN LOGIC
# ==========================================

def apply_break_even(trade, current_price):

    entry = trade["entry_price"]
    sl = trade["sl"]
    direction = trade["direction"]

    move_threshold = abs(entry - sl) * 1.0  # 1R

    if trade["break_even_moved"]:
        return trade

    # BUY
    if direction == "BUY":
        if current_price >= entry + move_threshold:
            trade["sl"] = entry
            trade["break_even_moved"] = True

    # SELL
    if direction == "SELL":
        if current_price <= entry - move_threshold:
            trade["sl"] = entry
            trade["break_even_moved"] = True

    return trade


# ==========================================
# PARTIAL TAKE PROFIT (50%)
# ==========================================

def apply_partial_tp(trade, current_price):

    entry = trade["entry_price"]
    tp = trade["tp"]
    direction = trade["direction"]

    if trade["partial_taken"]:
        return trade

    partial_level = entry + (tp - entry) * 0.5 if direction == "BUY" else entry - (entry - tp) * 0.5

    if direction == "BUY" and current_price >= partial_level:
        trade["partial_taken"] = True
        trade["partial_level"] = partial_level

    if direction == "SELL" and current_price <= partial_level:
        trade["partial_taken"] = True
        trade["partial_level"] = partial_level

    return trade


# ==========================================
# TRAILING STOP SYSTEM
# ==========================================

def apply_trailing_stop(trade, current_price):

    if not trade["partial_taken"]:
        return trade

    entry = trade["entry_price"]
    direction = trade["direction"]

    trail_distance = abs(entry - trade["sl"]) * 0.8

    if direction == "BUY":
        new_sl = current_price - trail_distance
        if new_sl > trade["sl"]:
            trade["sl"] = new_sl
            trade["trailing_active"] = True

    if direction == "SELL":
        new_sl = current_price + trail_distance
        if new_sl < trade["sl"]:
            trade["sl"] = new_sl
            trade["trailing_active"] = True

    return trade


# ==========================================
# MASTER UPDATE FUNCTION
# ==========================================

def update_trade_management(trade_id: str, current_price: float):

    trade = supabase.table("open_trades") \
        .select("*") \
        .eq("trade_id", trade_id) \
        .execute()

    if not trade.data:
        return

    trade = trade.data[0]

    # APPLY MANAGEMENT LAYERS
    trade = apply_partial_tp(trade, current_price)
    trade = apply_break_even(trade, current_price)
    trade = apply_trailing_stop(trade, current_price)

    # UPDATE SUPABASE
    supabase.table("open_trades").update({
        "sl": trade["sl"],
        "partial_taken": trade["partial_taken"],
        "break_even_moved": trade["break_even_moved"],
        "trailing_active": trade["trailing_active"]
    }).eq("trade_id", trade_id).execute()

    return trade