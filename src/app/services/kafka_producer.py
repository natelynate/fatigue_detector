from aiokafka import AIOKafkaProducer
import json
import uuid
from datetime import datetime


class KafkaService:
    def __init__(self):
        self.producer = None
        self.session_topic = "session_events"
        self.frame_topic = "frame_data"
        self.blink_topic = "blink_event"
    
    async def start(self, server='localhost', port=9092):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=f'{server}:{port}',
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda v: str(v).encode('utf-8')
        )
        await self.producer.start()

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    async def send_session_event(self, user_id: str, status: str, session_id: int = None):
        if not session_id:
            session_id = int(uuid.uuid4().int & (1<<31)-1)  # Generate 31-bit integer
            
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "start_time": datetime.now().isoformat(),
            "end_time": None,
            "status": status
        }
        
        await self.producer.send(
            topic=self.session_topic,
            key=user_id,  # Using user_id as key for session ordering
            value=session_data
        )
        return session_id

    async def send_frame_data(self, session_id: int, timestamp: float, ear_value: float):
        frame_data = {
            "session_id": session_id,
            "timestamp": timestamp,
            "ear_value": ear_value
        }
        
        await self.producer.send(
            topic=self.frame_topic,
            key=str(session_id),  # Using session_id as key to keep frames ordered
            value=frame_data
        )

    async def send_blink_data(self, session_id:int, start_timestamp:float, end_timestamp:float):
        blink_data = {
            "session_id":session_id,
            "start_timestamp":start_timestamp,
            "end_timestamp":end_timestamp
        }
        await self.producer.send(
            topic=self.blink_topic,
            key=str(session_id),  # Using session_id as key to keep frames ordered
            value=blink_data
        )
