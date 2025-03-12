from base_consumer import BaseKafkaConsumer
import logging
import statistics
from datetime import datetime

logger = logging.getLogger(__name__)

class BlinkEventConsumer(BaseKafkaConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_blink_timestamps = {}

    async def process_message(self, message):
        try:
            blink_data = message.value
            session_id = blink_data.get('session_id')
            start_timestamp = blink_data.get('start_timestamp')
            end_timestamp = blink_data.get('end_timestamp')

            if start_timestamp is None or end_timestamp is None:
                logger.error(f"Missing timestamp data: start={start_timestamp}, end={end_timestamp}")
                return

            if isinstance(start_timestamp, str):
                start_timestamp = datetime.fromisoformat(start_timestamp)
            elif isinstance(start_timestamp, (int, float)):
                start_timestamp = datetime.fromtimestamp(start_timestamp)
                
            if isinstance(end_timestamp, str):
                end_timestamp = datetime.fromisoformat(end_timestamp)
            elif isinstance(end_timestamp, (int, float)):
                end_timestamp = datetime.fromtimestamp(end_timestamp)

            duration = (end_timestamp - start_timestamp).total_seconds()
            
            interval = None
            if session_id in self.last_blink_timestamps:
                # Calculate time from last blink's end to this blink's start
                interval = (start_timestamp - self.last_blink_timestamps[session_id]).total_seconds()
            self.last_blink_timestamps[session_id] = end_timestamp # Update last blink timestamp
            logger.info(f"Blink: session_id={session_id}, start={start_timestamp}, end={end_timestamp}, duration={duration}, interval={interval}")
            with self.db_conn.cursor() as cursor:
                cursor.execute(
                    """  
                    INSERT INTO operation.blink_events
                    (session_id, start_time, end_time, duration, interval)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (session_id, start_timestamp, end_timestamp, duration, interval)
                )
            logger.debug(f"Processed blink event for session {session_id}")
        except Exception as e:
            logger.error(f"Error at BlinkEventConsumer's self.process_message: {e}")