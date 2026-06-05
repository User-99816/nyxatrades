from core.events.event_bus import event_bus


async def publish_signal_created(signal_data: dict):
    await event_bus.emit(
        "SIGNAL_CREATED",
        signal_data
    )


async def publish_trade_opened(trade_data: dict):
    await event_bus.emit(
        "TRADE_OPENED",
        trade_data
    )


async def publish_trade_updated(trade_data: dict):
    await event_bus.emit(
        "TRADE_UPDATED",
        trade_data
    )


async def publish_trade_closed(trade_data: dict):
    await event_bus.emit(
        "TRADE_CLOSED",
        trade_data
    )