from datetime import datetime


def build_signal_response(
    signal,
    license_data
):

    return {
        "timestamp": datetime.utcnow().isoformat(),

        "plan": license_data["plan"],

        "pair": signal["pair"],

        "signal": signal["signal"],

        "confidence": signal["confidence"],

        "entry": signal["entry"],

        "stop_loss": signal["sl"],

        "take_profit": signal["tp"]
    }