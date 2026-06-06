from fastapi import APIRouter, HTTPException

from core.data.ohlc_parser import parse_ohlc
from core.data.multi_timeframe import build_timeframe_data, timeframe_confluence

from core.risk.institutional_risk_engine import evaluate_institutional_risk
from core.risk.kill_switch import is_kill_switch_active

from services.license_service import validate_license
from services.session_service import is_session_active
from services.risk_service import get_risk_metrics, update_risk_metrics

from core.realtime.ws_manager import manager
from services.portfolio_exposure_service import can_open_trade
from services.execution_quality_service import evaluate_execution_quality
from core.events.event_bus import publish_event

from config.supabase_client import supabase

import uuid
from datetime import datetime

router = APIRouter(prefix="/signal", tags=["Signals"])


# ==========================================
# PLAN ENGINE (NEW CORE UPGRADE)
# ==========================================

def get_plan_rules(plan: str):

    if plan == "trial":
        return {
            "confidence_min": 0.60,
            "risk_multiplier": 0.8,
            "symbols": ["EURUSD", "GBPUSD"],
            "execution_delay": 120
        }

    elif plan == "lite":
        return {
            "confidence_min": 0.65,
            "risk_multiplier": 1.0,
            "symbols": ["EURUSD", "GBPUSD", "USDJPY"],
            "execution_delay": 60
        }

    elif plan == "pro":
        return {
            "confidence_min": 0.75,
            "risk_multiplier": 1.5,
            "symbols": ["EURUSD", "GBPUSD", "USDJPY", "XAUUSD"],
            "execution_delay": 10
        }

    return get_plan_rules("trial")


# ==========================================
# MAIN SIGNAL ENDPOINT
# ==========================================

@router.post("/")
async def get_signal(payload: dict):

    api_key = payload.get("api_key")

    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    # ==========================================
    # LICENSE VALIDATION
    # ==========================================

    license_data = validate_license(api_key)

    if not license_data or license_data["status"] != "active":
        return {
            "status": "BLOCKED",
            "trade_allowed": False,
            "reason": "INVALID_LICENSE"
        }

    user_email = license_data["user_email"]

    # ==========================================
    # PLAN DETECTION (NEW)
    # ==========================================

    plan = license_data.get("plan", "trial")
    rules = get_plan_rules(plan)

    # ==========================================
    # KILL SWITCH CHECK
    # ==========================================

    kill_status = is_kill_switch_active()

    if kill_status["active"]:
        return {
            "status": "BLOCKED",
            "trade_allowed": False,
            "reason": kill_status["reason"],
            "kill_switch": True
        }

    # ==========================================
    # SESSION VALIDATION
    # ==========================================

    session = is_session_active(user_email)

    if not session.get("active"):
        return {
            "status": "BLOCKED",
            "trade_allowed": False,
            "reason": "SESSION_INACTIVE"
        }

    # ==========================================
    # TIMEFRAME ENGINE
    # ==========================================

    try:
        tf_data = build_timeframe_data(payload)
        direction, score = timeframe_confluence(tf_data)

    except Exception as e:
        return {
            "status": "BLOCKED",
            "reason": f"INVALID_MTF_DATA: {str(e)}"
        }

    # ==========================================
    # SYMBOL FILTER (PLAN BASED)
    # ==========================================

    symbol = payload.get("symbol", "UNKNOWN")

    if symbol not in rules["symbols"]:
        return {
            "status": "BLOCKED",
            "reason": f"SYMBOL_NOT_ALLOWED_FOR_{plan.upper()}"
        }

    # ==========================================
    # BASE SIGNAL
    # ==========================================

    confidence = score / 5.0

    if confidence < rules["confidence_min"]:
        return {
            "status": "BLOCKED",
            "reason": "LOW_CONFIDENCE"
        }

    signal = {
        "direction": direction,
        "confidence": confidence,
        "entry_price": tf_data["M1"]["entry_price"],
        "atr": tf_data["M1"]["atr"],
        "symbol": symbol,
        "strategy": "MTF_LIQUIDITY_ENGINE"
    }

    # ==========================================
    # EXECUTION QUALITY
    # ==========================================

    execution_check = evaluate_execution_quality(
        symbol=symbol,
        spread=payload.get("spread", 0),
        slippage=payload.get("slippage", 0),
        volatility=payload.get("volatility", 0),
        liquidity_score=payload.get("liquidity_score", 100)
    )

    if execution_check["decision"] == "REJECTED":
        return {
            "status": "BLOCKED",
            "reason": "POOR_EXECUTION_CONDITIONS"
        }

    # ==========================================
    # RISK ENGINE
    # ==========================================

    risk_metrics = get_risk_metrics(user_email)

    risk_check = evaluate_institutional_risk(
        user_email=user_email,
        metrics=risk_metrics,
        signal=signal
    )

    if not risk_check["allowed"]:
        return {
            "status": "BLOCKED",
            "reason": risk_check["reason"]
        }

    # ==========================================
    # APPLY PLAN-BASED RISK MULTIPLIER
    # ==========================================

    risk_mult = rules["risk_multiplier"]
    atr = signal["atr"]

    if not atr or atr <= 0:
        return {
            "status": "BLOCKED",
            "reason": "INVALID_ATR"
        }

    if direction == "BUY":
        signal["stop_loss"] = signal["entry_price"] - (atr * 1.5 * risk_mult)
        signal["take_profit"] = signal["entry_price"] + (atr * 3 * risk_mult)

    elif direction == "SELL":
        signal["stop_loss"] = signal["entry_price"] + (atr * 1.5 * risk_mult)
        signal["take_profit"] = signal["entry_price"] - (atr * 3 * risk_mult)

    else:
        return {
            "status": "BLOCKED",
            "reason": "NO_DIRECTION"
        }

    # ==========================================
    # SIGNAL ID
    # ==========================================

    signal_id = f"NX-{uuid.uuid4().hex[:10].upper()}"

    response = {
        "status": "OK",
        "trade_allowed": True,
        "signal_id": signal_id,

        "plan": plan,

        "symbol": symbol,
        "direction": direction,

        "entry_price": signal["entry_price"],
        "stop_loss": signal["stop_loss"],
        "take_profit": signal["take_profit"],

        "confidence": signal["confidence"],
        "strategy": signal["strategy"],

        "execution": {
            "valid_for_seconds": rules["execution_delay"],
            "max_slippage": 2
        },

        "timestamp": datetime.utcnow().isoformat()
    }

    # ==========================================
    # REAL-TIME BROADCAST
    # ==========================================

    try:
        await manager.broadcast({
            "type": "NEW_SIGNAL",
            "data": response
        })
    except:
        pass

    # ==========================================
    # UPDATE RISK TRACKING
    # ==========================================

    update_risk_metrics(
        user_email=user_email,
        trades_today=risk_metrics["trades_today"] + 1,
        daily_loss_percent=risk_metrics["daily_loss_percent"],
        current_drawdown_percent=risk_metrics["current_drawdown_percent"],
        account_balance=risk_metrics["account_balance"],
        account_equity=risk_metrics["account_equity"]
    )

    return response