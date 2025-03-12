from base_consumer import BaseKafkaConsumer
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FrameEventConsumer(BaseKafkaConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cache of active sessions
        self.active_sessions = {}

    async def process_message(self, message):
        try:
            frame_data = message.value
            
            # Extract and validate session_id
            try:
                session_id = int(frame_data.get('session_id'))
            except (TypeError, ValueError):
                logger.error(f"Invalid session_id: {frame_data.get('session_id')}")
                return
            
            # Extract and handle timestamp
            timestamp = frame_data.get('timeframe')
            if timestamp is None:
                logger.error(f"Missing timestamp in frame data for session {session_id}")
                return
                
            # Convert timestamp based on its type
            if isinstance(timestamp, str):
                try:
                    timestamp = datetime.fromisoformat(timestamp)
                except ValueError:
                    # Try parsing as timestamp if isoformat fails
                    timestamp = datetime.fromtimestamp(float(timestamp))
            elif isinstance(timestamp, (int, float)):
                timestamp = datetime.fromtimestamp(timestamp)
            
            # Extract and validate ear_value
            try:
                ear_value = float(frame_data.get("ear_value"))
                if ear_value is None:
                    logger.warning(f"Missing ear_value in frame data for session {session_id}")
                    return
            except (TypeError, ValueError):
                logger.error(f"Invalid ear_value: {frame_data.get('ear_value')}")
                return
            
            # Insert into database using parameterized query
            with self.db_conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO operation.raw_frame_data
                    (session_id, timestamp, ear)
                    VALUES (%s, %s, %s)
                    """,
                    (session_id, timestamp, ear_value)
                )
                
            logger.debug(f"Stored frame data for session {session_id}: timestamp={timestamp}, ear={ear_value}")
            
        except Exception as e:
            logger.error(f"Error at FrameEventConsumer on self.process_message: {e}", exc_info=True)