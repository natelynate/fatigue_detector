from fastapi import HTTPException, Request, status
from jose import JWTError, jwt
from .core.config import settings


async def get_token_header(request: Request) -> str:
    token = request.cookies.get("access_token") #   Get token from HTTP-only cookie
    print(f"All cookies: {request.cookies}")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    # Remove 'Bearer ' prefix if present and validate the token
    if token.startswith("Bearer "): 
        token = token.split("Bearer ")[1]
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        print(f"Token payload: {payload}")  # Debug print
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        # Returns the access token
        return token 
    except JWTError as e:
        print(f"JWT Error: {e}")  # Debug print
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
