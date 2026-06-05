from config.supabase_client import supabase
from collections import defaultdict
from datetime import datetime


class StrategyMLOptimizerV2:

    TABLE_STRATEGY_STATS = "strategy_stats"
    TABLE_STRATEGY_DECISIONS = "strategy_decisions"

    # ==========================================
    # MAIN ENTRY: ANALYZE ALL STRATEGIES
    # ==========================================

    def run_optimization(self):

        trades = self._fetch_closed_trades()

        if not trades:
            return {"status": "NO_DATA"}

        stats = self._aggregate_strategy_performance(trades)

        decisions = self._make_decisions(stats)

        self._store_decisions(decisions)

        return {
            "status": "OPTIMIZED",
            "strategies_analyzed": len(stats),
            "decisions": decisions
        }

    # ==========================================
    # FETCH DATA
    # ==========================================

    def _fetch_closed_trades(self):

        response = (
            supabase.table("trade_history")
            .select("*")
            .execute()
        )

        return response.data or []

    # ==========================================
    # AGGREGATE STRATEGY PERFORMANCE
    # ==========================================

    def _aggregate_strategy_performance(self, trades):

        stats = defaultdict(lambda: {
            "total_trades": 0,
            "wins": 0,
            "losses": 0,
            "total_pnl": 0.0,
            "avg_pnl": 0.0,
            "win_rate": 0.0
        })

        for t in trades:

            strategy = t.get("strategy", "UNKNOWN")
            pnl = float(t.get("pnl", 0))

            stats[strategy]["total_trades"] += 1
            stats[strategy]["total_pnl"] += pnl

            if pnl > 0:
                stats[strategy]["wins"] += 1
            else:
                stats[strategy]["losses"] += 1

        # finalize metrics
        for s in stats:

            total = stats[s]["total_trades"]
            wins = stats[s]["wins"]

            stats[s]["avg_pnl"] = stats[s]["total_pnl"] / max(total, 1)
            stats[s]["win_rate"] = wins / max(total, 1)

        return stats

    # ==========================================
    # DECISION ENGINE (CORE ML LOGIC)
    # ==========================================

    def _make_decisions(self, stats):

        decisions = {}

        for strategy, s in stats.items():

            win_rate = s["win_rate"]
            avg_pnl = s["avg_pnl"]

            # ==========================================
            # STRATEGY CLASSIFICATION
            # ==========================================

            if win_rate >= 0.60 and avg_pnl > 0:
                action = "SCALE_UP"
                risk_multiplier = 1.3

            elif win_rate >= 0.50:
                action = "KEEP"
                risk_multiplier = 1.0

            elif win_rate >= 0.40:
                action = "REDUCE_RISK"
                risk_multiplier = 0.7

            else:
                action = "DISABLE"
                risk_multiplier = 0.0

            decisions[strategy] = {
                "action": action,
                "win_rate": win_rate,
                "avg_pnl": avg_pnl,
                "risk_multiplier": risk_multiplier,
                "timestamp": datetime.utcnow().isoformat()
            }

        return decisions

    # ==========================================
    # STORE DECISIONS
    # ==========================================

    def _store_decisions(self, decisions):

        rows = []

        for strategy, d in decisions.items():

            rows.append({
                "strategy": strategy,
                "action": d["action"],
                "win_rate": d["win_rate"],
                "avg_pnl": d["avg_pnl"],
                "risk_multiplier": d["risk_multiplier"],
                "created_at": d["timestamp"]
            })

        supabase.table(self.TABLE_STRATEGY_DECISIONS).insert(rows).execute()


# GLOBAL INSTANCE
strategy_ml_optimizer_v2 = StrategyMLOptimizerV2()