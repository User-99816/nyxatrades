from core.events.event_store import event_store
from datetime import datetime


# ==========================================
# EVENT REPLAY ENGINE
# ==========================================

class EventReplayEngine:

    # ==========================================
    # REPLAY BY TIME RANGE
    # ==========================================

    def replay_by_time(
        self,
        start_time: str,
        end_time: str
    ):

        events = event_store.get_events(
            start_time=start_time,
            end_time=end_time
        )

        return self._simulate(events)

    # ==========================================
    # REPLAY BY TRADE
    # ==========================================

    def replay_trade(self, trade_id: str):

        events = event_store.get_trade_events(trade_id)

        return self._simulate(events)

    # ==========================================
    # CORE SIMULATION ENGINE
    # ==========================================

    def _simulate(self, events: list):

        state = {
            "trades": {},
            "signals": {},
            "pnl_curve": [],
            "risk_events": 0
        }

        timeline = []

        for event in events:

            event_type = event.get("event_type")
            data = event.get("data")

            # ==========================
            # SIGNAL EVENTS
            # ==========================
            if event_type == "NEW_SIGNAL":
                timeline.append(("signal", data))
                state["signals"][data.get("signal_id")] = data

            # ==========================
            # TRADE OPENED
            # ==========================
            elif event_type == "TRADE_OPENED":
                trade_id = data.get("trade_id")
                state["trades"][trade_id] = data
                timeline.append(("open", data))

            # ==========================
            # TRADE UPDATE
            # ==========================
            elif event_type == "TRADE_UPDATE":
                trade_id = data.get("trade_id")

                if trade_id in state["trades"]:
                    state["trades"][trade_id].update(data)

                timeline.append(("update", data))

            # ==========================
            # TRADE CLOSED
            # ==========================
            elif event_type == "TRADE_CLOSED":
                trade_id = data.get("trade_id")

                if trade_id in state["trades"]:
                    state["trades"][trade_id]["status"] = "CLOSED"

                timeline.append(("close", data))

            # ==========================
            # RISK EVENT
            # ==========================
            elif "RISK" in event_type:
                state["risk_events"] += 1
                timeline.append(("risk", data))

            # ==========================
            # PnL TRACKING (OPTIONAL)
            # ==========================
            pnl = data.get("pnl")
            if pnl is not None:
                state["pnl_curve"].append(pnl)

        return {
            "summary": state,
            "timeline": timeline,
            "total_events": len(events)
        }


# GLOBAL INSTANCE
replay_engine = EventReplayEngine()