from config.supabase_client import supabase


# ==========================================
# GET STRATEGY PERFORMANCE
# ==========================================

def get_strategy_confidence(strategy_name: str):

    res = supabase.table("strategy_performance") \
        .select("*") \
        .eq("strategy", strategy_name) \
        .execute()

    if not res.data:
        return 0.5

    return float(res.data[0].get("confidence_weight", 0.5))


# ==========================================
# AUTO TUNE PARAMETERS
# ==========================================

def auto_tune_parameters(base_signal: dict, strategy_name: str):

    confidence = get_strategy_confidence(strategy_name)

    signal = base_signal.copy()

    # ==========================================
    # ADJUST RISK BASED ON PERFORMANCE
    # ==========================================

    signal["confidence"] *= confidence

    # If strategy is weak → reduce TP aggressiveness
    if confidence < 0.4:
        signal["take_profit_multiplier"] = 0.8
        signal["risk_multiplier"] = 0.7

    # If strong → allow full aggression
    elif confidence > 0.75:
        signal["take_profit_multiplier"] = 1.2
        signal["risk_multiplier"] = 1.1

    else:
        signal["take_profit_multiplier"] = 1.0
        signal["risk_multiplier"] = 1.0

    return signal