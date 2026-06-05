from core.events.event_bus import event_bus


async def dispatch_event(event):
    await event_bus.publish(event)