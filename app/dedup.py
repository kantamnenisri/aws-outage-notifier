from datetime import datetime, timedelta
from typing import Dict

class AlertState:
    def __init__(self):
        # Stores {service_region: last_alerted_datetime}
        self.last_alerted: Dict[str, datetime] = {}
        self.silenced_until: datetime = datetime.min
        self.history = []

    def should_alert(self, key: str) -> bool:
        now = datetime.now()
        
        # Check global silence
        if now < self.silenced_until:
            return False
            
        # Check deduplication (60 minutes)
        last_time = self.last_alerted.get(key)
        if last_time and (now - last_time) < timedelta(minutes=60):
            return False
            
        return True

    def mark_alerted(self, key: str, details: dict):
        self.last_alerted[key] = datetime.now()
        # Keep last 50 alerts in history
        self.history.insert(0, details)
        if len(self.history) > 50:
            self.history.pop()

    def silence(self, hours: int):
        self.silenced_until = datetime.now() + timedelta(hours=hours)

# Global singleton
state = AlertState()
