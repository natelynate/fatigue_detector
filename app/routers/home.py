from fastapi import APIRouter, Request, Depends, Form, HTTPException, Response, status
from fastapi.responses import JSONResponse
from . import templates
from ..dependencies import get_token_header
from ..core.database import get_db
from ..core.config import settings
from ..core.security import verify_password, create_access_token, create_refresh_token
from ..models.users import User
from datetime import datetime, timedelta

router = APIRouter(
    prefix="",
    tags=["home"],
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
async def login(
    response: Response, 
    username: str = Form(), 
    password: str = Form(), 
    db=Depends(get_db)
):
    print(f"Login attempt with email:{username}, pw:{password}")
    user = db.query(User).filter(User.email == username).first()
    
    if not user or not verify_password(password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )

    # If a successful login 
    user.last_login = datetime.now()
    db.commit()

    # Create access and refresh tokens
    access_token = create_access_token(
        data={"sub": str(user.user_id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    print(f"Created access token: {access_token}") 

    refresh_token = create_refresh_token(
        data={"sub": str(user.user_id)}
    )
    print(f"Created refresh token: {refresh_token}") 

    # Create a JSONResponse that will include both the JSON body and cookies
    login_response = JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "success": True,
            "message": "Login successful",
            "user": {
                "email": user.email,
                "id": user.user_id
            }
        }
    )

    # Set cookies on the response
    login_response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=False,  # Set True for HTTPS in production
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/"
    )
    login_response.set_cookie(
        key="refresh_token",
        value=f"Bearer {refresh_token}",
        httponly=True,
        secure=False,  # Set True for HTTPS in production
        samesite="strict",
        max_age=60 * 60 * 24 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
        path="/"
    )

    return login_response

@router.post("/logout")
async def logout(response: Response):
    # Clear the cookies
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    
    return JSONResponse({
        "success": True,
        "message": "Logout successful"
    })