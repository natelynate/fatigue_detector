from typing import Annotated
from fastapi import Header, HTTPException


async def get_token_header(x_token: str = Header(default=None)):
    pass # Temporary pass all requests

