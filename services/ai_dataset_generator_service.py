from core.events.event_store import event_store
from config.supabase_client import supabase
from datetime import datetime
import json


# ==========================================
# AI DATASET GENERATOR SERVICE
# ==========================================

class AIDatasetGeneratorService:

    TABLE_NAME = "ai_training_dataset"

    # ==========================================
    # MAIN PIPELINE: GENERATE DATASET
    # ==========================================

    def generate_dataset(
        self,
        start_time: str = None,
        end_time: str = None,
        symbol: str = None
    ):

        # STEP 1: FETCH EVENTS
        events = event_store.get_events(
            start_time=start_time,
            end_time=end_time
        )

        dataset = []

        trade_states = {}

        # STEP 2: REBUILD TRADE STATE FROM EVENTS
        for event in events:

            event_type = event.get("event_type")
            data = event.get("data")

            # ==========================
            # SIGNAL EVENT
            # ==========================
            if event_type == "NEW_SIGNAL":

                signal_id = data.get("signal_id")

                trade_states[signal_id] = {
                    "signal": data,
                    "entry_price": data.get("entry_price"),
                    "direction": data.get("direction"),
                    "start_time": event.get("timestamp"),
                    "updates": [],
                    "exit": None,
                    "pnl": None
                }

            # ==========================
            # TRADE UPDATE
            # ==========================
            elif event_type == "TRADE_UPDATE":

                trade_id = data.get("trade_id")

                if trade_id in trade_states:
                    trade_states[trade_id]["updates"].append(data)

            # ==========================
            # TRADE CLOSED → LABEL POINT
            # ==========================
            elif event_type == "TRADE_CLOSED":

                trade_id = data.get("trade_id")

                if trade_id in trade_states:

                    trade_states[trade_id]["exit"] = data
                    trade_states[trade_id]["pnl"] = data.get("pnl")

        # STEP 3: BUILD ML DATASET
        for trade_id, trade in trade_states.items():

            signal = trade.get("signal")

            if not signal:
                continue

            pnl = trade.get("pnl", 0)

            # ==========================================
            # LABELING LOGIC (CORE AI TRAINING SIGNAL)
            # ==========================================

            if pnl > 0:
                label = "WIN"
            elif pnl < 0:
                label = "LOSS"
            else:
                label = "BREAKEVEN"

            # ==========================================
            # FEATURE ENGINEERING
            # ==========================================

            entry_price = trade.get("entry_price", 0)

            updates = trade.get("updates", [])

            max_favorable = 0
            max_adverse = 0

            for u in updates:
                u_pnl = u.get("pnl", 0)

                if u_pnl > max_favorable:
                    max_favorable = u_pnl

                if u_pnl < max_adverse:
                    max_adverse = u_pnl

            feature = {
                "signal_id": signal.get("signal_id"),
                "symbol": signal.get("symbol"),
                "direction": signal.get("direction"),

                "confidence": signal.get("confidence"),
                "entry_price": entry_price,

                "atr": signal.get("atr", 0),

                "max_favorable_pnl": max_favorable,
                "max_adverse_pnl": max_adverse,

                "holding_updates": len(updates),

                # LABEL
                "label": label,
                "final_pnl": pnl,

                "created_at": datetime.utcnow().isoformat()
            }

            dataset.append(feature)

        # STEP 4: STORE DATASET IN SUPABASE
        if dataset:

            supabase.table(self.TABLE_NAME).insert(dataset).execute()

        return {
            "status": "SUCCESS",
            "samples_generated": len(dataset),
            "dataset": dataset
        }

    # ==========================================
    # GET TRAINING DATA
    # ==========================================

    def get_training_data(self, limit: int = 1000):

        result = (
            supabase.table(self.TABLE_NAME)
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        return result.data or []


# GLOBAL INSTANCE
ai_dataset_generator = AIDatasetGeneratorService()