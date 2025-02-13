from fastapi import APIRouter, Request, WebSocket, Depends, status
from fastapi.websockets import WebSocketDisconnect
from fastapi.responses import HTMLResponse
from . import templates
from jose import JWTError
from ..dependencies import get_token_header
from ..core.security import verify_token


router = APIRouter(prefix="/monitoring", 
                   tags=["monitoring"])

@router.get("/", response_class=HTMLResponse)
async def monitoring_page(request: Request, token: str = Depends(get_token_header)):
    return templates.TemplateResponse(
        "monitoring.html",
        {"request": request}
    )


@router.websocket("/websocket_process")
async def websocket_process(websocket: WebSocket):
    try:
        token = websocket.cookies.get("access_token")
        if token and token.startswith("Bearer "):
            token = token.split("Bearer ")[1]
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        # Verify token
        try:
            payload = verify_token(token, "access")
            user_id = payload.get("sub")
            if not user_id:
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
        except JWTError:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
         # Accept the connection after verification
        await websocket.accept()
        print(f"WebSocket accepted for user {user_id}")

        try:
            while True:
                try:
                    # Receive JSON data from client
                    data = await websocket.receive_json()
                    
                    # Store the received data
                    timestamp = data.get('timestamp')
                    ear_value = data.get('ear_value')
                    
                    # You can process or store the data here
                    print(f"Received EAR value: {ear_value} at timestamp: {timestamp}")
                    
                    # Send acknowledgment back to client
                    await websocket.send_json({
                        "status": "received",
                        "timestamp": timestamp
                    })
                except Exception as e:
                    print(f"Error processing data: {e}")
                    break
                    
        except WebSocketDisconnect:
            print("Client disconnected")

    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
