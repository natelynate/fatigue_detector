# app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sshtunnel import SSHTunnelForwarder
from .config import settings
import paramiko
from paramiko import RSAKey

tunnel = None

def get_db_url_with_tunnel():
    """Create SSH tunnel and return database URL"""
    global tunnel
    if tunnel is None or not tunnel.is_active:
        ssh_pkey = paramiko.RSAKey.from_private_key_file(settings.SSH_KEY_PATH, settings.SSH_KEY_PW)
        tunnel = SSHTunnelForwarder(
            (settings.SSH_HOST, settings.SSH_PORT),
            ssh_username=settings.SSH_USER,
            ssh_pkey=ssh_pkey,
            remote_bind_address=(settings.DATABASE_HOST, settings.DATABASE_PORT),
            local_bind_address=('localhost', 0),  # 0 means random free port
        )
        tunnel.start()
    
    # Construct database URL using the tunnel's local port
    return f"postgresql://postgres@localhost:{tunnel.local_bind_port}/operation"

# Create engine with SSH tunnel
engine = create_engine(get_db_url_with_tunnel())

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()