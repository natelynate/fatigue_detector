from base_consumer import BaseKafkaConsumer
import logging
import statistics
from datetime import datetime

logger = logging.getLogger(__name__)

class SessionEventConsumer(BaseKafkaConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Cache of active sessions
        self.active_sessions = {}
    
    async def process_message(self, message):
        try:
            session_data = message.value
            session_id = session_data.get('session_id')
            user_id = session_data.get('user_id')
            status = session_data.get('status')
            
            # Convert timestamps if present
            start_time = None
            if 'start_time' in session_data:
                start_time = datetime.fromisoformat(session_data['start_time'])
            
            end_time = None
            if 'end_time' in session_data and session_data['end_time']:
                end_time = datetime.fromisoformat(session_data['end_time'])
            
            # If this is a new session, store it in the active sessions
            if status == 'active':
                self.active_sessions[session_id] = {
                    'user_id': user_id,
                    'start_time': start_time,
                    'status': status
                }
                
                # Store in database
                with self.db_conn.cursor() as cursor:
                    cursor.execute(
                        """
                        INSERT INTO operation.sessions 
                        (session_id, user_id, start_time, status)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (session_id) 
                        DO UPDATE SET 
                            user_id = EXCLUDED.user_id,
                            start_time = EXCLUDED.start_time,
                            status = EXCLUDED.status
                        """,
                        (session_id, user_id, start_time, status)
                    )
                
                logger.info(f"Started new session {session_id} for user {user_id}")
            
            # If session is complete or interrupted
            elif status in ('complete', 'interrupted'):
                # Update session in database
                with self.db_conn.cursor() as cursor:
                    cursor.execute(
                        """
                        UPDATE operation.sessions 
                        SET end_time = %s, status = %s
                        WHERE session_id = %s
                        """,
                        (end_time or datetime.now(), status, session_id)
                    )
                
                # Calculate session statistics # To be implemented
                # await self._calculate_session_metrics(session_id)
                
                # Remove from active sessions
                if session_id in self.active_sessions:
                    del self.active_sessions[session_id]
                
                logger.info(f"Completed session {session_id} with status {status}")
        
        except Exception as e:
            logger.error(f"Error processing session event: {e}")
    
    
    # async def _calculate_session_metrics(self, session_id):
    #     """Calculate and store session metrics"""
    #     try:
    #         # Fetch all blink events for this session
    #         with self.db_conn.cursor() as cursor:
    #             cursor.execute(
    #                 """
    #                 SELECT duration, interval 
    #                 FROM blink_events 
    #                 WHERE session_id = %s 
    #                 AND duration IS NOT NULL
    #                 ORDER BY start_time
    #                 """,
    #                 (session_id,)
    #             )
    #             blink_data = cursor.fetchall()
            
    #         # Return if no blink data
    #         if not blink_data:
    #             logger.warning(f"No blink data found for session {session_id}")
    #             return
                
    #         # Extract durations and intervals
    #         durations = [row[0] for row in blink_data if row[0] is not None]
    #         intervals = [row[1] for row in blink_data if row[1] is not None]
            
    #         # Calculate metrics
    #         metrics = {}
    #         metrics['total_blinks'] = len(durations)
            
    #         if durations:
    #             metrics['avg_duration'] = sum(durations) / len(durations)
    #             metrics['max_duration'] = max(durations)
    #             metrics['min_duration'] = min(durations)
    #             metrics['duration_variance'] = statistics.variance(durations) if len(durations) > 1 else 0
            
    #         if intervals:
    #             metrics['avg_interval'] = sum(intervals) / len(intervals)
    #             metrics['max_interval'] = max(intervals)
    #             metrics['min_interval'] = min(intervals)
    #             metrics['interval_variance'] = statistics.variance(intervals) if len(intervals) > 1 else 0
            
    #         # Calculate blink rate (blinks per minute)
    #         with self.db_conn.cursor() as cursor:
    #             cursor.execute(
    #                 """
    #                 SELECT EXTRACT(EPOCH FROM (end_time - start_time))/60 as session_minutes
    #                 FROM sessions
    #                 WHERE session_id = %s
    #                 """,
    #                 (session_id,)
    #             )
    #             result = cursor.fetchone()
                
    #             if result and result[0]:
    #                 session_minutes = result[0]
    #                 metrics['blink_rate'] = metrics['total_blinks'] / session_minutes
            
    #         # Calculate fatigue score (a simple example)
    #         # Low values indicate more fatigue
    #         if 'interval_variance' in metrics and 'duration_variance' in metrics:
    #             # Higher variance in both metrics often indicates fatigue
    #             # This is a simplified model - you'd want to refine this
    #             metrics['fatigue_score'] = 100 - (
    #                 (metrics['interval_variance'] * 20) + 
    #                 (metrics['duration_variance'] * 50)
    #             )
    #             # Clamp to 0-100 range
    #             metrics['fatigue_score'] = max(0, min(100, metrics['fatigue_score']))
            
    #         # Store metrics in database
    #         placeholders = ", ".join([f"{k} = %s" for k in metrics.keys()])
    #         values = list(metrics.values())
            
    #         with self.db_conn.cursor() as cursor:
    #             cursor.execute(
    #                 f"""
    #                 INSERT INTO session_metrics 
    #                 (session_id, {', '.join(metrics.keys())})
    #                 VALUES (%s, {', '.join(['%s' for _ in metrics])})
    #                 ON CONFLICT (session_id) 
    #                 DO UPDATE SET {placeholders}
    #                 """,
    #                 [session_id] + values
    #             )
            
    #         logger.info(f"Calculated metrics for session {session_id}")
        
    #     except Exception as e:
    #         logger.error(f"Error calculating session metrics: {e}")