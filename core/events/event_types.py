# ==========================================
# CENTRAL EVENT REGISTRY
# ==========================================

class EventTypes:

    # Market events
    NEW_SIGNAL = "NEW_SIGNAL"
    SIGNAL_REJECTED = "SIGNAL_REJECTED"

    # Trade lifecycle
    TRADE_OPENED = "TRADE_OPENED"
    TRADE_UPDATED = "TRADE_UPDATED"
    TRADE_CLOSED = "TRADE_CLOSED"

    # Execution
    EXECUTION_UPDATE = "EXECUTION_UPDATE"
    EXECUTION_FAILED = "EXECUTION_FAILED"

    # Risk
    RISK_LIMIT_HIT = "RISK_LIMIT_HIT"
    KILL_SWITCH_ACTIVATED = "KILL_SWITCH_ACTIVATED"

    # AI system
    AI_LEARNING_UPDATE = "AI_LEARNING_UPDATE"
    STRATEGY_UPDATED = "STRATEGY_UPDATED"

    # System
    SYSTEM_HEALTH = "SYSTEM_HEALTH"