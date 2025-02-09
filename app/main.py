from fastapi import FastAPI, Depends
from .core.config import templates, static
from .dependencies import get_token_header
from .routers import users, home, monitoring

# Include routers
app = FastAPI(dependencies=[Depends(get_token_header)])
app.include_router(users.router)
app.include_router(home.router)
app.include_router(monitoring.router)

# Mount static directory
app.mount("/static", static)
