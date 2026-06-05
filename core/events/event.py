from datetime import datetime
import uuid


class Event:
    def __init__(self, event_type, data: dict):
        self.id = f"EV-{uuid.uuid4().hex[:10].upper()}"
        self.type = event_type
        self.data = data
        self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self):
        return {
            "event_id": self.id,
            "type": self.type,
            "data": self.data,
            "timestamp": self.timestamp
        }