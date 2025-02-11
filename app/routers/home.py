from fastapi import APIRouter, Request, Depends, Form, WebSocket
from fastapi.websockets import WebSocketDisconnect
from fastapi.responses import JSONResponse
from . import templates
from ..dependencies import get_token_header


router = APIRouter(
    prefix="",
    tags=["home"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {"request": request, 
         "message": "Eye Fatigue Monitor"}
    )

@router.post("/login")
async def login(username: str = Form(), password: str = Form()):
    # For now, accept any credentials
    print(f"Login attempt with id:{username}, pw:{password}")
    return JSONResponse({
        "success": True,
        "message": "Login successful"
    })

