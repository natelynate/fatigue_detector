import asyncio
import json
import logging
from datetime import datetime, timedelta
from aiokafka import AIOKafkaConsumer
import psycopg2
import psycopg2.extras
from psycopg2.extensions import connection as pg_connection
from sshtunnel import SSHTunnelForwarder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseKafkaConsumer:
    def __init__(self, kafka_server, kafka_port, topic, 
                 group_id, db_config, ssh_config=None):
        self.kafka_server = kafka_server
        self.kafka_port = kafka_port
        self.topic = topic
        self.group_id = group_id
        self.db_config = db_config
        self.ssh_config = ssh_config
        self.consumer = None
        self.db_conn = None
        self.ssh_tunnel = None
        
    async def start(self):
        # Connect to Kafka
        self.consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=f'{self.kafka_server}:{self.kafka_port}',
            group_id=self.group_id,
            auto_offset_reset='earliest',
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda m: m.decode('utf-8') if m else None
        )
        
        await self.consumer.start()
        logger.info(f"Started consuming from topic: {self.topic}")
        
        # Connect to database
        try:
            self._connect_db()
            logger.info(f"Successfully conntected to Database.")
        except Exception as e:
            logger.info(f"Error connecting to Database: {self.topic}, {e}")
        
        # Start processing loop
        await self._process_messages()
    
    def _connect_db(self):
        """Connect to PostgreSQL database, optionally through SSH tunnel"""
        try:
            if self.ssh_config:
                # Create SSH tunnel
                self.ssh_tunnel = SSHTunnelForwarder(
                    (self.ssh_config['host'], int(self.ssh_config['port'])),  # SSH server address
                    ssh_username=self.ssh_config['user'],
                    ssh_pkey=self.ssh_config['key_path'],
                    ssh_password=self.ssh_config['key_pw'],
                    remote_bind_address=('localhost', int(self.db_config['port'])),  # PostgreSQL on remote server
                    local_bind_address=('127.0.0.1', 6543)  # Local forwarded port
                )
                self.ssh_tunnel.start()
                
                # Connect through tunnel
                self.db_conn = psycopg2.connect(
                    host='127.0.0.1',  # Connect to the local end of the tunnel
                    port=6543,         # The local forwarded port
                    user=self.db_config['user'],
                    password=self.db_config['password'],
                    dbname=self.db_config['dbname']
                )
            else:
                # Direct connection
                self.db_conn = psycopg2.connect(
                    host=self.db_config['host'],
                    port=self.db_config['port'],
                    user=self.db_config['user'],
                    password=self.db_config['password'],
                    dbname=self.db_config['dbname']
                )
            
            # Set autocommit for timescale
            self.db_conn.autocommit = True
            logger.info("Connected to database")
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            logger.info(f"Error connecting to Database: {e}")
    
    async def _process_messages(self):
        """Main processing loop - to be implemented by subclasses"""
        try:
            async for message in self.consumer:
                await self.process_message(message)
        finally:
            await self.stop()
    
    async def process_message(self, message):
        """Process a single message - to be implemented by subclasses"""
        raise NotImplementedError
    
    async def stop(self):
        """Stop consumer and close connections"""
        if self.consumer:
            await self.consumer.stop()
        
        if self.db_conn:
            self.db_conn.close()
        
        if self.ssh_tunnel:
            self.ssh_tunnel.close()