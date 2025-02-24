from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings, static, templates    
from .core.database import Base, engine                 
from .models.users import User
from .routers import home, monitoring
from contextlib import asynccontextmanager
from .services.kafka_producer import KafkaService

@asynccontextmanager
async def lifespan(app: FastAPI):
    kafka_service = KafkaService() # Initialize Kafka service  
    await kafka_service.start(settings.KAFKA_SERVER, settings.KAFKA_PORT)
    app.state.kafka_service = kafka_service
    print(f"Kafka service Producer = {kafka_service.producer}")
    yield
    await kafka_service.stop()

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specify your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(home.router)
app.include_router(monitoring.router)

# Mount static directory
app.mount("/static", static)