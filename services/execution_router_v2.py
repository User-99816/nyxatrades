from datetime import datetime
import uuid
import asyncio

from core.events.event_bus import event_bus
from services.execution_quality_service import evaluate_execution_quality


class ExecutionRouterV2:

    # ==========================================
    # MAIN EXECUTION ENTRY POINT
    # ==========================================

    async def execute_trade(self, signal: dict, user_email: str):

        execution_id = f"EX-{uuid.uuid4().hex[:10].upper()}"

        # ==========================================
        # 1. PRE-EXECUTION QUALITY CHECK
        # ==========================================

        quality = evaluate_execution_quality(
            symbol=signal["symbol"],
            spread=signal.get("spread", 0),
            slippage=signal.get("slippage", 0),
            volatility=signal.get("volatility", 0),
            liquidity_score=signal.get("liquidity_score", 100)
        )

        if quality["decision"] == "REJECTED":
            return self._fail(execution_id, "POOR_EXECUTION_CONDITIONS", quality)

        # ==========================================
        # 2. BUILD ORDER PACKET
        # ==========================================

        order = self._build_order(signal, user_email, execution_id)

        # ==========================================
        # 3. ROUTE ORDER (SIMULATED BROKER LAYER)
        # ==========================================

        execution_result = await self._route_to_broker(order)

        # ==========================================
        # 4. VERIFY EXECUTION
        # ==========================================

        if not execution_result["filled"]:
            return self._retry_or_fail(order, execution_result)

        # ==========================================
        # 5. EMIT EXECUTION EVENT
        # ==========================================

        await event_bus.emit(
            "TRADE_EXECUTED",
            {
                "execution_id": execution_id,
                "user_email": user_email,
                "order": order,
                "execution": execution_result,
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        return {
            "status": "EXECUTED",
            "execution_id": execution_id,
            "order": order,
            "execution": execution_result
        }

    # ==========================================
    # ORDER BUILDER
    # ==========================================

    def _build_order(self, signal, user_email, execution_id):

        return {
            "execution_id": execution_id,
            "user_email": user_email,

            "symbol": signal["symbol"],
            "direction": signal["direction"],
            "volume": self._calculate_lot_size(signal),

            "entry_price": signal["entry_price"],
            "stop_loss": signal["stop_loss"],
            "take_profit": signal["take_profit"],

            "strategy": signal.get("strategy", "UNKNOWN"),
            "timestamp": datetime.utcnow().isoformat()
        }

    # ==========================================
    # LOT SIZE CALCULATOR (RISK-BASED)
    # ==========================================

    def _calculate_lot_size(self, signal):

        confidence = float(signal.get("confidence", 0.5))

        base_lot = 0.01

        # scale by confidence
        lot = base_lot * (1 + confidence)

        # cap risk exposure
        return round(min(lot, 1.0), 2)

    # ==========================================
    # BROKER ROUTER (SIMULATION LAYER)
    # ==========================================

    async def _route_to_broker(self, order):

        # simulate network latency / broker response
        await asyncio.sleep(0.2)

        # simulated fill logic (replace with MT5 / broker API later)
        return {
            "filled": True,
            "fill_price": order["entry_price"],
            "slippage": 0.1,
            "latency_ms": 180,
            "broker": "SIMULATED_BROKER_V2"
        }

    # ==========================================
    # RETRY LOGIC (INSTITUTIONAL STYLE)
    # ==========================================

    async def _retry_or_fail(self, order, execution_result):

        retries = 2

        for i in range(retries):

            await asyncio.sleep(0.5)

            retry_result = await self._route_to_broker(order)

            if retry_result["filled"]:
                return {
                    "status": "EXECUTED_AFTER_RETRY",
                    "order": order,
                    "execution": retry_result
                }

        return self._fail(order["execution_id"], "BROKER_REJECTED", execution_result)

    # ==========================================
    # FAILURE HANDLER
    # ==========================================

    def _fail(self, execution_id, reason, context):

        return {
            "status": "FAILED",
            "execution_id": execution_id,
            "reason": reason,
            "context": context,
            "timestamp": datetime.utcnow().isoformat()
        }


# GLOBAL INSTANCE
execution_router_v2 = ExecutionRouterV2()