import asyncio
import os
import logging
from frame_consumer import FrameEventConsumer
from blink_consumer import BlinkEventConsumer
from session_consumer import SessionEventConsumer

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    # Get configuration from environment variables
    kafka_server = os.environ.get('KAFKA_SERVER', 'localhost') 
    kafka_port = os.environ.get('KAFKA_PORT', '9092')
    
    db_config = {
        'host': os.environ.get('DATABASE_HOST'),
        'port': os.environ.get('DATABASE_PORT', '5432'),
        'user': os.environ.get('DATABASE_USER'),
        'password': os.environ.get('DATABASE_PASSWORD', ''),
        'dbname': os.environ.get('DATABASE_NAME'),
    }
    
    ssh_config = None
    if os.environ.get('SSH_HOST'):
        ssh_config = {
            'host': os.environ.get('SSH_HOST'),
            'port': os.environ.get('SSH_PORT', '22'),
            'user': os.environ.get('SSH_USER'),
            'key_path': os.environ.get('SSH_KEY_PATH'),
            'key_pw': os.environ.get('SSH_KEY_PW', '')
        }
    
    # Determine which consumer to run based on environment variable
    consumer_type = os.environ.get('CONSUMER_TYPE', 'frame')
    
    if consumer_type == 'frame':
        consumer = FrameEventConsumer(
            kafka_server, kafka_port, 'frame_data', 
            'frame-consumer-group', db_config, ssh_config
        )
    elif consumer_type == 'blink':
        consumer = BlinkEventConsumer(
            kafka_server, kafka_port, 'blink_event', 
            'blink-consumer-group', db_config, ssh_config
        )
    elif consumer_type == 'session':
        consumer = SessionEventConsumer(
            kafka_server, kafka_port, 'session_events', 
            'session-consumer-group', db_config, ssh_config
        )
    else:
        logger.error(f"Unknown consumer type: {consumer_type}")
        return
    
    logger.info(f"Starting {consumer_type} consumer at {kafka_server} on port {kafka_port}")
    await consumer.start()

if __name__ == "__main__":
    asyncio.run(main())