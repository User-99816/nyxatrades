from datetime import datetime

from core.events.event_store_service import event_store_service
from core.events.event_pipeline import event_pipeline

from services.strategy_ml_optimizer_v2 import strategy_ml_optimizer_v2
from services.portfolio_allocator_v2 import portfolio_allocator_v2

from services.strategy_performance_service import update_strategy_stats


class AIFeedbackConnector:

    # ==========================================
    # MAIN ENTRY POINT (CALLED ON TRADE CLOSE)
    # ==========================================

    async def process_trade_result(self, trade_id: str):

        # ==========================================
        # 1. REPLAY FULL TRADE LIFECYCLE
        # ==========================================

        events = event_store_service.get_trade_replay(trade_id)

        if not events:
            return {
                "status": "NO_DATA",
                "trade_id": trade_id
            }

        # ==========================================
        # 2. EXTRACT CORE METRICS
        # ==========================================

        trade_open = None
        trade_close = None

        for e in events:

            if e["event_type"] in ["TRADE_OPENED", "SIGNAL_APPROVED"]:
                trade_open = e

            if e["event_type"] in ["TRADE_CLOSED"]:
                trade_close = e

        if not trade_close:
            return {
                "status": "INCOMPLETE_TRADE",
                "trade_id": trade_id
            }

        open_data = trade_open["payload"] if trade_open else {}
        close_data = trade_close["payload"]

        pnl = close_data.get("pnl", 0)
        strategy = open_data.get("strategy", "UNKNOWN")
        user_email = open_data.get("user_email")

        # ==========================================
        # 3. CLASSIFY RESULT (WIN / LOSS / FLAT)
        # ==========================================

        if pnl > 0:
            outcome = "WIN"
        elif pnl < 0:
            outcome = "LOSS"
        else:
            outcome = "BREAKEVEN"

        # ==========================================
        # 4. UPDATE STRATEGY PERFORMANCE DB
        # ==========================================

        try:
            strategy_stats = update_strategy_stats(
                strategy=strategy,
                pnl=pnl
            )
        except Exception as e:
            strategy_stats = {"error": str(e)}

        # ==========================================
        # 5. ML OPTIMIZER FEEDBACK UPDATE
        # ==========================================

        try:
            strategy_ml_optimizer_v2.learn(
                strategy=strategy,
                outcome=outcome,
                pnl=pnl,
                context=open_data
            )
        except Exception as e:
            print(f"[ML FEEDBACK ERROR] {str(e)}")

        # ==========================================
        # 6. PORTFOLIO REBALANCE SIGNAL
        # ==========================================

        try:
            portfolio_allocator_v2.rebalance_from_trade(
                user_email=user_email,
                strategy=strategy,
                pnl=pnl,
                outcome=outcome
            )
        except Exception as e:
            print(f"[PORTFOLIO FEEDBACK ERROR] {str(e)}")

        # ==========================================
        # 7. EMIT AI LEARNING EVENT
        # ==========================================

        await event_pipeline.emit("AI_FEEDBACK_PROCESSED", {
            "trade_id": trade_id,
            "strategy": strategy,
            "pnl": pnl,
            "outcome": outcome,
            "timestamp": datetime.utcnow().isoformat()
        })

        # ==========================================
        # 8. RETURN LEARNING SUMMARY
        # ==========================================

        return {
            "status": "PROCESSED",
            "trade_id": trade_id,
            "strategy": strategy,
            "outcome": outcome,
            "pnl": pnl,
            "strategy_stats": strategy_stats
        }


# ==========================================
# SINGLETON
# ==========================================

ai_feedback_connector = AIFeedbackConnector()