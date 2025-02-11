from fastapi import APIRouter, Request, WebSocket
from fastapi.websockets import WebSocketDisconnect
from fastapi.responses import HTMLResponse
from . import templates
import numpy as np
import time
import cv2
import json

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/", response_class=HTMLResponse)
async def monitoring_page(request: Request):
    return templates.TemplateResponse(
        "monitoring.html",
        {"request": request}
    )


@router.websocket("/websocket_process")
async def websocket_process(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket accepted") 
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