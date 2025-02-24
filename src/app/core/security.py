from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status
from .config import settings


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# Verify a plain password against its hash
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False
    

def create_token(data: Dict[str, Any], token_type: str, expires_delta: Optional[timedelta] = None) -> str:
    """
    Base function to create JWT tokens
    Args:
        data: The data to encode in the token
        token_type: Type of token ("access" or "refresh")
        expires_delta: Optional expiration time
    Returns:
        str: The encoded JWT token
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES if token_type == "access"
            else settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60
        )
    
    # Add claims to token
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(),
        "type": token_type
    })
    
    try:
        # Create the JWT token
        encoded_jwt = jwt.encode(
            to_encode,
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM
        )
        return encoded_jwt
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Could not create token: {str(e)}"
        )

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create an access token
    Args:
        data: The data to encode in the token
        expires_delta: Optional custom expiration time
    Returns:
        str: The encoded access token
    """
    return create_token(data, "access", expires_delta)


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a refresh token
    Args:
        data: The data to encode in the token
    Returns:
        str: The encoded refresh token
    """
    # Refresh tokens always use the default expiration time
    return create_token(data, "refresh", None)


def verify_token(token: str, token_type: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token
    Args:
        token: The token to verify
        token_type: Expected token type ("access" or "refresh")
    Returns:
        dict: The decoded token payload
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        
        # Verify token type
        if payload.get("type") != token_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {token_type} token."
            )
            
        return payload
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )


def get_user_id_from_token(token: str, token_type: str = "access") -> int:
    """
    Extract user ID from a token
    Args:
        token: The token to decode
        token_type: Type of token to expect
    Returns:
        int: The user ID from the token
    """
    payload = verify_token(token, token_type)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token contains no user ID"
        )
    return int(user_id)