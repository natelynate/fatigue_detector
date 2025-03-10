from base_consumer import BaseKafkaConsumer
import logging
import statistics
from datetime import datetime


class BlinkEventConsumer(BaseKafkaConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cache of active sessions
        self.active_sessions = {}