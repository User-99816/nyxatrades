from datetime import datetime

from core.events.event_bus import event_bus

from services.portfolio_allocator_v2 import portfolio_allocator_v2
from services.strategy_ml_optimizer_v2 import strategy_ml_optimizer_v2
from services.execution_quality_service import evaluate_execution_quality
from services.portfolio_exposure_service import can_open_trade

from core.risk.kill_switch import is_kill_switch_active
from core.risk.institutional_risk_engine import evaluate_institutional_risk

from services.risk_service import get_risk_metrics


class AIOrchestratorV2:

    # ==========================================
    # MAIN DECISION ENGINE (CORE BRAIN)
    # ==========================================

    async def evaluate_signal(self, payload: dict, user_email: str):

        # ==========================================
        # 1. GLOBAL SAFETY CHECK (KILL SWITCH)
        # ==========================================

        kill = is_kill_switch_active()

        if kill["active"]:
            return self._reject("KILL_SWITCH_ACTIVE", kill)

        # ==========================================
        # 2. PORTFOLIO EXPOSURE CHECK
        # ==========================================

        exposure = can_open_trade(
            user_email=user_email,
            symbol=payload["symbol"],
            exposure_percent=payload.get("confidence", 0.5)
        )

        if not exposure["allowed"]:
            return self._reject("EXPOSURE_LIMIT", exposure)

        # ==========================================
        # 3. EXECUTION QUALITY FILTER
        # ==========================================

        execution = evaluate_execution_quality(
            symbol=payload["symbol"],
            spread=payload.get("spread", 0),
            slippage=payload.get("slippage", 0),
            volatility=payload.get("volatility", 0),
            liquidity_score=payload.get("liquidity_score", 100)
        )

        if execution["decision"] == "REJECTED":
            return self._reject("POOR_EXECUTION", execution)

        # ==========================================
        # 4. RISK ENGINE VALIDATION
        # ==========================================

        risk_metrics = get_risk_metrics(user_email)

        risk = evaluate_institutional_risk(
            user_email=user_email,
            metrics=risk_metrics,
            signal=payload
        )

        if not risk["allowed"]:
            return self._reject("RISK_BLOCKED", risk)

        # ==========================================
        # 5. STRATEGY INTELLIGENCE CHECK
        # ==========================================

        strategy_action = strategy_ml_optimizer_v2.run_optimization()

        # optional: you could hard-block DISABLED strategies here
        strategy_name = payload.get("strategy", "UNKNOWN")

        # ==========================================
        # 6. PORTFOLIO ALLOCATION (CAPITAL CONTROL)
        # ==========================================

        portfolio = portfolio_allocator_v2.allocate(
            user_email=user_email,
            total_equity=risk_metrics.get("account_equity", 1000)
        )

        allocation = portfolio.get("allocations", {}).get(strategy_name, {})

        if allocation.get("equity_allocated", 0) <= 0:
            return self._reject("NO_CAPITAL_ALLOCATION", allocation)

        # ==========================================
        # 7. FINAL DECISION ENGINE
        # ==========================================

        decision_score = self._compute_score(
            risk,
            execution,
            exposure,
            allocation
        )

        if decision_score < 0.5:
            return self._reject("LOW_CONFIDENCE", {
                "score": decision_score
            })

        # ==========================================
        # 8. APPROVED SIGNAL (ENRICHED)
        # ==========================================

        enriched = {
            **payload,
            "decision": "APPROVED",
            "decision_score": decision_score,

            "portfolio_allocation": allocation,
            "execution_quality": execution,
            "risk": risk,

            "timestamp": datetime.utcnow().isoformat()
        }

        # ==========================================
        # 9. EVENT EMISSION (FULL OBSERVABILITY)
        # ==========================================

        await event_bus.emit(
            "AI_DECISION_APPROVED",
            enriched
        )

        return enriched

    # ==========================================
    # SCORE ENGINE (WEIGHTED INTELLIGENCE)
    # ==========================================

    def _compute_score(self, risk, execution, exposure, allocation):

        score = 1.0

        # risk penalty
        if not risk.get("allowed", True):
            score -= 0.5

        # execution penalty
        if execution.get("decision") == "REJECTED":
            score -= 0.4

        # exposure penalty
        if not exposure.get("allowed", True):
            score -= 0.3

        # allocation strength bonus
        if allocation.get("equity_allocated", 0) > 1000:
            score += 0.1

        return max(0.0, min(score, 1.0))

    # ==========================================
    # REJECTION FORMAT
    # ==========================================

    def _reject(self, reason: str, context: dict):

        event = {
            "decision": "REJECTED",
            "reason": reason,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }

        return event


# GLOBAL INSTANCE
ai_orchestrator_v2 = AIOrchestratorV2()