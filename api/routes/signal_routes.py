from fastapi import APIRouter, HTTPException

from core.data.ohlc_parser import parse_ohlc
from core.data.multi_timeframe import build_timeframe_data, timeframe_confluence

from core.risk.institutional_risk_engine import evaluate_institutional_risk
from core.risk.kill_switch import is_kill_switch_active

from services.license_service import validate_license
from services.session_service import is_session_active
from services.risk_service import get_risk_metrics, update_risk_metrics

# 🔥 REAL-TIME UPGRADE
from core.realtime.ws_manager import manager

# 🔥 PORTFOLIO EXPOSURE ENGINE (NEW UPGRADE)
from services.portfolio_exposure_service import can_open_trade

# 🔥 EXECUTION QUALITY ENGINE (NEW UPGRADE)
from services.execution_quality_service import evaluate_execution_quality

# 🔥 EVENT STREAM (NEW UPGRADE - FUTURE CORE ENGINE)
from core.events.event_bus import publish_event

import uuid
from datetime import datetime


router = APIRouter(prefix="/signal", tags=["Signals"])


# ==========================================
# MAIN SIGNAL ENDPOINT (EA ENTRY POINT)
# ==========================================

@router.post("/")
async def get_signal(payload: dict):

    api_key = payload.get("api_key")

    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    # ==========================================
    # EVENT: SIGNAL_REQUEST_RECEIVED
    # ==========================================

    try:
        await publish_event("SIGNAL_REQUEST_RECEIVED", {
            "api_key": api_key,
            "symbol": payload.get("symbol"),
            "timestamp": datetime.utcnow().isoformat()
        })
    except:
        pass

    # ==========================================
    # KILL SWITCH CHECK
    # ==========================================

    kill_status = is_kill_switch_active()

    if kill_status["active"]:

        await publish_event("SIGNAL_BLOCKED_KILL_SWITCH", {
            "reason": kill_status["reason"],
            "timestamp": datetime.utcnow().isoformat()
        })

        return {
            "status": "BLOCKED",
            "trade_allowed": False,
            "reason": kill_status["reason"],
            "kill_switch": True
        }

    # ==========================================
    # LICENSE VALIDATION
    # ==========================================

    license_data = validate_license(api_key)

    if not license_data or license_data["status"] != "active":

        await publish_event("SIGNAL_BLOCKED_LICENSE", {
            "api_key": api_key,
            "reason": "INVALID_LICENSE"
        })

        return {
            "status": "BLOCKED",
            "trade_allowed": False,
            "reason": "INVALID_LICENSE"
        }

    user_email = license_data["user_email"]

    # ==========================================
    # SESSION VALIDATION
    # ==========================================

    session = is_session_active(user_email)

    if not session.get("active"):

        await publish_event("SIGNAL_BLOCKED_SESSION", {
            "user_email": user_email,
            "reason": "SESSION_INACTIVE"
        })

        return {
            "status": "BLOCKED",
            "trade_allowed": False,
            "reason": "SESSION_INACTIVE"
        }

    # ==========================================
    # MULTI-TIMEFRAME PARSING
    # ==========================================

    try:
        tf_data = build_timeframe_data(payload)

        confluence_direction, confluence_score = timeframe_confluence(tf_data)

    except Exception as e:
        return {
            "status": "BLOCKED",
            "trade_allowed": False,
            "reason": f"INVALID_MTF_DATA: {str(e)}"
        }

    # ==========================================
    # BASE SIGNAL OBJECT
    # ==========================================

    optimized_signal = {
        "direction": confluence_direction,
        "confidence": confluence_score / 5.0,
        "entry_price": tf_data["M1"]["entry_price"],
        "stop_loss": 0,
        "take_profit": 0,
        "strategy": "MTF_LIQUIDITY_ENGINE",
        "symbol": payload.get("symbol", "UNKNOWN"),
        "atr": tf_data["M1"]["atr"]
    }

    # ==========================================
    # PORTFOLIO EXPOSURE CHECK
    # ==========================================

    exposure_check = can_open_trade(
        user_email=user_email,
        symbol=optimized_signal["symbol"],
        exposure_percent=optimized_signal["confidence"]
    )

    if not exposure_check["allowed"]:
        return {
            "status": "BLOCKED",
            "trade_allowed": False,
            "reason": exposure_check["reason"]
        }

    # ==========================================
    # EXECUTION QUALITY CHECK
    # ==========================================

    execution_check = evaluate_execution_quality(
        symbol=optimized_signal["symbol"],
        spread=payload.get("spread", 0),
        slippage=payload.get("slippage", 0),
        volatility=payload.get("volatility", 0),
        liquidity_score=payload.get("liquidity_score", 100)
    )

    if execution_check["decision"] == "REJECTED":

        await publish_event("SIGNAL_REJECTED_EXECUTION", {
            "symbol": optimized_signal["symbol"],
            "reason": "POOR_EXECUTION_CONDITIONS"
        })

        return {
            "status": "BLOCKED",
            "trade_allowed": False,
            "reason": "POOR_EXECUTION_CONDITIONS",
            "execution_quality": execution_check
        }

    # ==========================================
    # RISK METRICS
    # ==========================================

    risk_metrics = get_risk_metrics(user_email)

    # ==========================================
    # INSTITUTIONAL RISK ENGINE
    # ==========================================

    risk_check = evaluate_institutional_risk(
        user_email=user_email,
        metrics=risk_metrics,
        signal=optimized_signal
    )

    if not risk_check["allowed"]:

        await publish_event("SIGNAL_BLOCKED_RISK", {
            "user_email": user_email,
            "reason": risk_check["reason"]
        })

        return {
            "status": "BLOCKED",
            "trade_allowed": False,
            "reason": risk_check["reason"],
            "kill_switch": risk_check.get("kill_switch", False)
        }

    # ==========================================
    # APPLY SAFE MODE
    # ==========================================

    risk_mult = risk_check.get("risk_reduction", 1.0)

    atr = optimized_signal["atr"]

    if atr is None or atr <= 0:
        return {
            "status": "BLOCKED",
            "trade_allowed": False,
            "reason": "INVALID_ATR_DATA"
        }

    if optimized_signal["direction"] == "BUY":
        optimized_signal["stop_loss"] = optimized_signal["entry_price"] - (atr * 1.5 * risk_mult)
        optimized_signal["take_profit"] = optimized_signal["entry_price"] + (atr * 3 * risk_mult)

    elif optimized_signal["direction"] == "SELL":
        optimized_signal["stop_loss"] = optimized_signal["entry_price"] + (atr * 1.5 * risk_mult)
        optimized_signal["take_profit"] = optimized_signal["entry_price"] - (atr * 3 * risk_mult)

    else:
        return {
            "status": "BLOCKED",
            "trade_allowed": False,
            "reason": "NO_VALID_DIRECTION"
        }

    # ==========================================
    # SIGNAL ID
    # ==========================================

    signal_id = f"NX-{uuid.uuid4().hex[:10].upper()}"

    # ==========================================
    # RESPONSE (EA FORMAT)
    # ==========================================

    response = {
        "status": "OK",
        "trade_allowed": True,
        "signal_id": signal_id,

        "symbol": optimized_signal["symbol"],
        "direction": optimized_signal["direction"],

        "entry_price": optimized_signal["entry_price"],
        "stop_loss": optimized_signal["stop_loss"],
        "take_profit": optimized_signal["take_profit"],

        "confidence": optimized_signal["confidence"],

        "strategy": optimized_signal["strategy"],

        "execution": {
            "valid_for_seconds": 60,
            "max_slippage": 2
        },

        "kill_switch": False,
        "timestamp": datetime.utcnow().isoformat()
    }

    # ==========================================
    # REAL-TIME BROADCAST (ADMIN DASHBOARD)
    # ==========================================

    try:
        await manager.broadcast({
            "type": "NEW_SIGNAL",
            "data": {
                "signal_id": signal_id,
                "user_email": user_email,
                "symbol": optimized_signal["symbol"],
                "direction": optimized_signal["direction"],
                "confidence": optimized_signal["confidence"],
                "entry_price": optimized_signal["entry_price"],
                "timestamp": response["timestamp"]
            }
        })
    except:
        pass

    # ==========================================
    # EVENT: SIGNAL_APPROVED
    # ==========================================

    try:
        await publish_event("SIGNAL_APPROVED", {
            "signal_id": signal_id,
            "user_email": user_email,
            "symbol": optimized_signal["symbol"],
            "direction": optimized_signal["direction"],
            "confidence": optimized_signal["confidence"]
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