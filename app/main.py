from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.config import settings, static, templates    
from app.core.database import Base, engine                 
from .models.users import User
from .routers import home, monitoring

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app = FastAPI()

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