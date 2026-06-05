from fastapi import APIRouter
from config.supabase_client import supabase

from core.trade.smart_trade_manager import update_trade_management
from core.ai.feedback_pipeline import process_closed_trade

from core.events.event_bus import publish_event
from datetime import datetime

# 🔥 REAL-TIME UPGRADE
from core.realtime.ws_manager import manager

# 🔥 STRATEGY PERFORMANCE ENGINE
from services.strategy_performance_service import update_strategy_stats


router = APIRouter(prefix="/trade", tags=["Trade Management"])


# ==========================================
# UPDATE LIVE TRADE (EA → BACKEND)
# ==========================================

@router.post("/update")
async def update_trade(payload: dict):

    trade_id = payload.get("trade_id")
    current_price = payload.get("current_price")

    if not trade_id:
        return {"error": "missing trade_id"}

    if current_price is None:
        return {"error": "missing current_price"}

    # ==========================================
    # EVENT: TRADE UPDATE RECEIVED
    # ==========================================

    try:
        await publish_event(
            "TRADE_UPDATE_RECEIVED",
            {
                "trade_id": trade_id,
                "current_price": current_price,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except:
        pass

    # ==========================================
    # SMART TRADE ENGINE
    # ==========================================

    updated_trade = update_trade_management(trade_id, current_price)

    # ==========================================
    # DATABASE SYNC
    # ==========================================

    try:
        supabase.table("open_trades") \
            .update({
                "current_price": current_price,
                "pnl": updated_trade.get("pnl"),
                "holding_time_minutes": updated_trade.get("holding_time_minutes"),
                "max_drawdown": updated_trade.get("max_drawdown"),
                "partial_taken": updated_trade.get("partial_taken"),
                "break_even_moved": updated_trade.get("break_even_moved"),
                "trailing_active": updated_trade.get("trailing_active")
            }) \
            .eq("trade_id", trade_id) \
            .execute()

    except Exception as e:
        return {
            "status": "UPDATED_BUT_DB_SYNC_FAILED",
            "error": str(e),
            "trade": updated_trade
        }

    # ==========================================
    # EVENT: TRADE UPDATED
    # ==========================================

    try:
        await publish_event(
            "TRADE_UPDATED",
            {
                "trade_id": trade_id,
                "current_price": current_price,
                "pnl": updated_trade.get("pnl")
            }
        )
    except:
        pass

    # ==========================================
    # REAL-TIME BROADCAST
    # ==========================================

    try:
        await manager.broadcast({
            "type": "TRADE_UPDATE",
            "data": {
                "trade_id": trade_id,
                "current_price": current_price,
                "pnl": updated_trade.get("pnl"),
                "trailing_active": updated_trade.get("trailing_active"),
                "break_even_moved": updated_trade.get("break_even_moved")
            }
        })
    except:
        pass

    return {
        "status": "UPDATED",
        "trade": updated_trade
    }


# ==========================================
# CLOSE TRADE (EA → BACKEND)
# ==========================================

@router.post("/close")
async def close_trade(payload: dict):

    trade_id = payload.get("trade_id")

    if not trade_id:
        return {"error": "missing trade_id"}

    # ==========================================
    # EVENT: CLOSE REQUEST
    # ==========================================

    try:
        await publish_event(
            "TRADE_CLOSE_REQUESTED",
            {
                "trade_id": trade_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
    except:
        pass

    # ==========================================
    # FETCH TRADE
    # ==========================================

    trade = supabase.table("open_trades") \
        .select("*") \
        .eq("trade_id", trade_id) \
        .execute()

    if not trade.data:
        return {"error": "trade not found"}

    trade_data = trade.data[0]

    # ==========================================
    # CLOSE TRADE
    # ==========================================

    supabase.table("open_trades") \
        .update({
            "status": "CLOSED",
            "closed_at": "now()"
        }) \
        .eq("trade_id", trade_id) \
        .execute()

    # ==========================================
    # MOVE TO HISTORY
    # ==========================================

    try:
        supabase.table("trade_history").insert({
            "trade_id": trade_data["trade_id"],
            "user_email": trade_data["user_email"],
            "symbol": trade_data["symbol"],
            "direction": trade_data["direction"],
            "strategy": trade_data.get("strategy"),
            "entry_price": trade_data.get("entry_price"),
            "exit_price": trade_data.get("current_price"),
            "pnl": trade_data.get("pnl"),
            "risk_amount": trade_data.get("risk_amount"),
            "max_drawdown": trade_data.get("max_drawdown"),
            "holding_time_minutes": trade_data.get("holding_time_minutes"),
            "closed_at": "now()"
        }).execute()
    except:
        pass

    # ==========================================
    # STRATEGY PERFORMANCE UPDATE
    # ==========================================

    try:
        strategy_name = trade_data.get("strategy", "UNKNOWN_STRATEGY")
        pnl = float(trade_data.get("pnl", 0))

        strategy_stats = update_strategy_stats(
            strategy=strategy_name,
            pnl=pnl
        )

    except Exception as e:
        strategy_stats = {"error": str(e)}

    # ==========================================
    # EVENT: TRADE CLOSED
    # ==========================================

    try:
        await publish_event(
            "TRADE_CLOSED",
            {
                "trade_id": trade_id,
                "symbol": trade_data.get("symbol"),
                "direction": trade_data.get("direction"),
                "strategy": trade_data.get("strategy"),
                "pnl": trade_data.get("pnl")
            }
        )
    except:
        pass

    # ==========================================
    # REAL-TIME BROADCAST
    # ==========================================

    try:
        await manager.broadcast({
            "type": "TRADE_CLOSED",
            "data": {
                "trade_id": trade_id,
                "symbol": trade_data.get("symbol"),
                "direction": trade_data.get("direction"),
                "pnl": trade_data.get("pnl"),
                "status": "CLOSED"
            }
        })
    except:
        pass

    # ==========================================
    # EVENT: STRATEGY UPDATED
    # ==========================================

    try:
        await publish_event(
            "STRATEGY_UPDATED",
            strategy_stats
        )
    except:
        pass

    # ==========================================
    # AI LEARNING PIPELINE
    # ==========================================

    learning_result = process_closed_trade(trade_id)

    # ==========================================
    # EVENT: AI LEARNING COMPLETE
    # ==========================================

    try:
        await publish_event(
            "TRADE_LEARNING_COMPLETED",
            {
                "trade_id": trade_id,
                "learning": learning_result
            }
        )
    except:
        pass

    return {
        "status": "CLOSED",
        "trade_id": trade_id,
        "strategy": strategy_stats,
        "learning": learning_result
    }