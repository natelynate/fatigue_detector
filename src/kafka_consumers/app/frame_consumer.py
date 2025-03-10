from base_consumer import BaseKafkaConsumer
from datetime import datetime

class FrameEventConsumer(BaseKafkaConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cache of active sessions
        self.active_sessions = {}