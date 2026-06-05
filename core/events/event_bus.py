from collections import defaultdict, deque
from datetime import datetime
import asyncio
import logging
from typing import Callable, Any, Dict, Optional, List


# ==========================================
# EVENT BUS CORE ENGINE (PRODUCTION READY)
# ==========================================

class EventBus:

    def __init__(self):

        self.subscribers = defaultdict(list)

        # ==========================================
        # MEMORY EVENT STREAM (REPLAY ENGINE CORE)
        # ==========================================
        self.history = deque(maxlen=100000)

        # ==========================================
        # FAILED EVENTS TRACKING (DEBUG / AI LEARNING)
        # ==========================================
        self.failed_events = deque(maxlen=20000)

        # ==========================================
        # EVENT METRICS (OPTIONAL MONITORING)
        # ==========================================
        self.event_count = 0

    # ==========================================
    # SUBSCRIBE
    # ==========================================

    def subscribe(self, event_type: str, handler: Callable):

        self.subscribers[event_type].append(handler)

    # ==========================================
    # UNSUBSCRIBE
    # ==========================================

    def unsubscribe(self, event_type: str, handler: Callable):

        if handler in self.subscribers[event_type]:
            self.subscribers[event_type].remove(handler)

    # ==========================================
    # GET FULL HISTORY (REPLAY ENGINE)
    # ==========================================

    def get_history(self, event_type: Optional[str] = None):

        if not event_type:
            return list(self.history)

        return [
            e for e in self.history
            if e["type"] == event_type
        ]

    # ==========================================
    # FAILED EVENTS (AI DEBUGGING)
    # ==========================================

    def get_failed_events(self):

        return list(self.failed_events)

    # ==========================================
    # CLEAR HISTORY
    # ==========================================

    def clear_history(self):

        self.history.clear()

    # ==========================================
    # CLEAR FAILURES
    # ==========================================

    def clear_failed_events(self):

        self.failed_events.clear()

    # ==========================================
    # CORE EMIT ENGINE (ASYNC SAFE)
    # ==========================================

    async def emit(self, event_type: str, data: Dict[str, Any]):

        event = {
            "id": f"EVT-{self.event_count}",
            "type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }

        self.event_count += 1

        # ==========================================
        # STORE EVENT IN MEMORY STREAM
        # ==========================================
        self.history.append(event)

        # ==========================================
        # GET HANDLERS
        # ==========================================
        handlers = self.subscribers.get(event_type, [])

        # ==========================================
        # HANDLER EXECUTION WRAPPER
        # ==========================================
        async def run_handler(handler):

            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)

            except Exception as e:

                self.failed_events.append({
                    "event": event,
                    "error": str(e),
                    "handler": str(handler),
                    "timestamp": datetime.utcnow().isoformat()
                })

                logging.error(
                    f"[EVENT BUS ERROR] {event_type}: {str(e)}"
                )

        # ==========================================
        # PARALLEL EXECUTION (FAST STREAM PROCESSING)
        # ==========================================
        await asyncio.gather(
            *[run_handler(h) for h in handlers],
            return_exceptions=True
        )

        return event

    # ==========================================
    # BROADCAST WRAPPER (WEBSOCKET LAYER)
    # ==========================================

    async def broadcast(self, event_type: str, data: Dict[str, Any]):

        return await self.emit(event_type, data)

    # ==========================================
    # EVENT STREAM EXPORT (AI / REPLAY / TRAINING)
    # ==========================================

    def get_event_stream(self, limit: int = 1000):

        return list(self.history)[-limit:]

    # ==========================================
    # EVENT ANALYTICS (OPTIONAL AI USE)
    # ==========================================

    def get_event_stats(self):

        return {
            "total_events": self.event_count,
            "history_size": len(self.history),
            "failed_events": len(self.failed_events),
            "subscribers": {
                k: len(v) for k, v in self.subscribers.items()
            }
        }


# ==========================================
# GLOBAL SINGLETON
# ==========================================

event_bus = EventBus()


# ==========================================
# COMPATIBILITY LAYER (KEEP YOUR ROUTES CLEAN)
# ==========================================

async def publish_event(event_type: str, data: dict):

    return await event_bus.emit(event_type, data)


def subscribe(event_type: str, handler):

    event_bus.subscribe(event_type, handler)


def unsubscribe(event_type: str, handler):

    event_bus.unsubscribe(event_type, handler)