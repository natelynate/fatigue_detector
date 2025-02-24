from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # JWT Settings
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    
    # Database Settings
    DATABASE_HOST: str
    DATABASE_PORT: int = 5432  # PostgreSQL default port
    DATABASE_USER: str
    DATABASE_PASSWORD: str
    DATABASE_NAME: str
    
    # SSH Tunnel Settings
    SSH_HOST: str
    SSH_USER: str = 'ubuntu'
    SSH_KEY_PATH: str
    SSH_PORT: int = 22
    SSH_KEY_PATH: str
    SSH_KEY_PW: str
    
    # Application Settings
    STATIC_DIR: Path = BASE_DIR / "static"
    TEMPLATES_DIR: Path = BASE_DIR / "templates"    

    # Kafka Settings
    KAFKA_SERVER:str
    KAFKA_PORT:int
    
    class Config:
        env_file = BASE_DIR / "core" / ".env"
        env_file_encoding = 'utf-8'


settings = Settings()

# Initialize static files and templates
static = StaticFiles(directory=str(settings.STATIC_DIR))
templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))