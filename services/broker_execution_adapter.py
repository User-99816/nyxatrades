import time
import random
from datetime import datetime


# ==========================================
# BROKER EXECUTION CONFIG
# ==========================================

MAX_RETRIES = 3
BASE_RETRY_DELAY = 0.8  # seconds


# ==========================================
# SIMULATED MT5 EXECUTION LAYER (REPLACE WITH EA BRIDGE)
# ==========================================

def send_to_mt5(order_payload: dict):

    """
    This function represents your MT5 bridge endpoint.
    Replace with real HTTP call or socket bridge to EA.
    """

    # Simulated broker behavior
    success_rate = 0.85

    if random.random() > success_rate:
        return {
            "status": "FAILED",
            "error_code": random.choice([
                "REQUOTE",
                "OFF_QUOTES",
                "BROKER_BUSY",
                "INVALID_PRICE"
            ])
        }

    return {
        "status": "FILLED",
        "execution_price": order_payload["price"] + random.uniform(-0.2, 0.2),
        "order_id": f"MT5-{int(time.time())}",
        "slippage": random.uniform(0.1, 1.5),
        "timestamp": datetime.utcnow().isoformat()
    }


# ==========================================
# LOT SIZE SAFETY ENGINE
# ==========================================

def normalize_lot_size(lot: float):

    if lot < 0.01:
        return 0.01

    if lot > 10:
        return 10

    return round(lot, 2)


# ==========================================
# EXECUTION ADAPTER CORE
# ==========================================

def execute_trade_with_adapter(
    symbol: str,
    direction: str,
    lot_size: float,
    price: float,
    stop_loss: float,
    take_profit: float
):

    lot_size = normalize_lot_size(lot_size)

    payload = {
        "symbol": symbol,
        "direction": direction,
        "lot": lot_size,
        "price": price,
        "sl": stop_loss,
        "tp": take_profit
    }

    attempt = 0
    last_error = None

    while attempt < MAX_RETRIES:

        attempt += 1

        result = send_to_mt5(payload)

        # ==========================================
        # SUCCESS CASE
        # ==========================================

        if result["status"] == "FILLED":

            return {
                "status": "SUCCESS",
                "order_id": result["order_id"],
                "execution_price": result["execution_price"],
                "slippage": result["slippage"],
                "attempts": attempt,
                "timestamp": result["timestamp"]
            }

        # ==========================================
        # FAILURE HANDLING
        # ==========================================

        last_error = result.get("error_code", "UNKNOWN_ERROR")

        # retry delay with backoff
        time.sleep(BASE_RETRY_DELAY * attempt)

    # ==========================================
    # FINAL FAILURE RESPONSE
    # ==========================================

    return {
        "status": "FAILED",
        "error": last_error,
        "attempts": attempt,
        "timestamp": datetime.utcnow().isoformat()
    }