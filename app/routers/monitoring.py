from fastapi import APIRouter, Request
from . import templates

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/")
async def monitoring_page(request: Request):
    return templates.TemplateResponse(
        "monitoring.html",
        {"request": request}
    )

