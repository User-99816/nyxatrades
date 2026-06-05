from config.supabase_client import supabase
from collections import defaultdict
from datetime import datetime


class PortfolioAllocatorV2:

    # ==========================================
    # MAIN ENTRY POINT
    # ==========================================

    def allocate(self, user_email: str, total_equity: float):

        strategies = self._get_strategy_decisions()

        if not strategies:
            return {"status": "NO_STRATEGIES"}

        portfolio = self._build_allocation(strategies, total_equity)

        self._store_allocation(user_email, portfolio)

        return {
            "status": "ALLOCATED",
            "user_email": user_email,
            "total_equity": total_equity,
            "allocations": portfolio
        }

    # ==========================================
    # FETCH STRATEGY INTELLIGENCE
    # ==========================================

    def _get_strategy_decisions(self):

        response = (
            supabase.table("strategy_decisions")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )

        if not response.data:
            return []

        # keep latest per strategy
        latest = {}

        for row in response.data:
            strategy = row["strategy"]

            if strategy not in latest:
                latest[strategy] = row

        return list(latest.values())

    # ==========================================
    # CORE ALLOCATION ENGINE
    # ==========================================

    def _build_allocation(self, strategies, total_equity):

        allocations = {}

        # Step 1: calculate raw weights
        raw_weights = {}

        for s in strategies:

            win_rate = float(s.get("win_rate", 0))
            avg_pnl = float(s.get("avg_pnl", 0))
            risk_multiplier = float(s.get("risk_multiplier", 1.0))

            # performance score (simple ML heuristic model)
            score = (
                (win_rate * 0.7) +
                (avg_pnl * 0.3)
            ) * risk_multiplier

            # ignore dead strategies
            if s["action"] == "DISABLE":
                continue

            raw_weights[s["strategy"]] = max(score, 0.01)

        # Step 2: normalize weights
        total_weight = sum(raw_weights.values())

        if total_weight <= 0:
            return {}

        for strategy, weight in raw_weights.items():

            normalized = weight / total_weight

            # Step 3: exposure caps (risk control layer)
            max_cap = self._get_max_cap(strategy)

            allocation = min(normalized * total_equity, max_cap)

            allocations[strategy] = {
                "equity_allocated": allocation,
                "weight": normalized,
                "max_cap": max_cap,
                "timestamp": datetime.utcnow().isoformat()
            }

        return allocations

    # ==========================================
    # RISK LIMIT PER STRATEGY
    # ==========================================

    def _get_max_cap(self, strategy: str):

        # hard risk guardrails (can later be ML-driven)

        if "scalping" in strategy.lower():
            return 1000

        if "swing" in strategy.lower():
            return 3000

        if "trend" in strategy.lower():
            return 5000

        # default cap
        return 2000

    # ==========================================
    # STORE ALLOCATION STATE
    # ==========================================

    def _store_allocation(self, user_email, portfolio):

        rows = []

        for strategy, data in portfolio.items():

            rows.append({
                "user_email": user_email,
                "strategy": strategy,
                "equity_allocated": data["equity_allocated"],
                "weight": data["weight"],
                "created_at": data["timestamp"]
            })

        supabase.table("portfolio_allocations").insert(rows).execute()


# GLOBAL INSTANCE
portfolio_allocator_v2 = PortfolioAllocatorV2()