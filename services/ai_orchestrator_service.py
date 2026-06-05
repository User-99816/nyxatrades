from datetime import datetime

# Core AI modules
from core.ai.trade_learning_engine import analyze_trade
from core.ai.strategy_auto_tuner import tune_strategy
from core.ai.feedback_pipeline import process_closed_trade

# Execution intelligence
from core.execution.execution_quality_engine import evaluate_execution_quality


# ==========================================
# AI ORCHESTRATOR (MAIN INTELLIGENCE LAYER)
# ==========================================

class AIOrchestrator:

    def __init__(self):

        # System state memory
        self.last_decision = None
        self.last_update = None

    # ==========================================
    # MAIN ENTRY POINT (POST-TRADE OR SIGNAL FEEDBACK)
    # ==========================================

    def process_event(self, event: dict):

        event_type = event.get("type", "UNKNOWN")

        # ==========================================
        # TRADE CLOSED EVENT
        # ==========================================

        if event_type == "TRADE_CLOSED":

            return self._handle_closed_trade(event)

        # ==========================================
        # SIGNAL GENERATED EVENT
        # ==========================================

        elif event_type == "NEW_SIGNAL":

            return self._handle_new_signal(event)

        # ==========================================
        # EXECUTION UPDATE EVENT
        # ==========================================

        elif event_type == "EXECUTION_UPDATE":

            return self._handle_execution_update(event)

        return {
            "status": "IGNORED",
            "reason": "UNKNOWN_EVENT_TYPE"
        }

    # ==========================================
    # CLOSED TRADE ANALYSIS
    # ==========================================

    def _handle_closed_trade(self, event):

        trade = event.get("data", {})

        # 1. Core trade learning
        learning_result = analyze_trade(trade)

        # 2. Feedback pipeline update
        feedback_result = process_closed_trade(trade)

        # 3. Strategy tuning
        tuning_result = tune_strategy(
            strategy=trade.get("strategy"),
            pnl=trade.get("pnl"),
            win=(float(trade.get("pnl", 0)) > 0)
        )

        # ==========================================
        # FINAL AI SUMMARY
        # ==========================================

        decision = {
            "type": "TRADE_LEARNING_COMPLETE",
            "timestamp": datetime.utcnow().isoformat(),
            "strategy": trade.get("strategy"),
            "learning": learning_result,
            "feedback": feedback_result,
            "tuning": tuning_result
        }

        self.last_decision = decision
        self.last_update = datetime.utcnow()

        return decision

    # ==========================================
    # SIGNAL ANALYSIS (PRE-TRADE INTELLIGENCE)
    # ==========================================

    def _handle_new_signal(self, event):

        signal = event.get("data", {})

        # Optional: you can later plug prediction models here
        adjusted_confidence = signal.get("confidence", 0)

        return {
            "type": "SIGNAL_ANALYZED",
            "signal_id": signal.get("signal_id"),
            "adjusted_confidence": adjusted_confidence,
            "approved": adjusted_confidence > 0.5
        }

    # ==========================================
    # EXECUTION QUALITY FEEDBACK LOOP
    # ==========================================

    def _handle_execution_update(self, event):

        execution = event.get("data", {})

        execution_score = evaluate_execution_quality(execution)

        return {
            "type": "EXECUTION_ANALYSIS",
            "execution_score": execution_score,
            "symbol": execution.get("symbol"),
            "status": execution.get("status")
        }


# ==========================================
# GLOBAL INSTANCE (USED ACROSS SYSTEM)
# ==========================================

orchestrator = AIOrchestrator()