from fastapi import APIRouter, Request, WebSocket
from fastapi.websockets import WebSocketDisconnect
from . import templates
from ..dependencies import BlinkDetector
from fastapi.responses import JSONResponse
import numpy as np
import time
import cv2
import json

router = APIRouter(prefix="/monitoring", tags=["monitoring"])

@router.get("/")
async def monitoring_page(request: Request):
    return templates.TemplateResponse(
        "monitoring.html",
        {"request": request}
    )


@router.websocket("/websocket_process")
async def websocket_process(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket accepted") # log
    detector = BlinkDetector(annotate=True)
    try:
        while True:
            try:
                # Receive data packet and 
                data = await websocket.receive_bytes()
                metadata_str, frame_bytes = data.split(b'\n', 1)
                metadata = json.loads(metadata_str)
                timestamp = metadata['timestamp']
                nparr = np.frombuffer(frame_bytes, np.uint8)       
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                # Process
                annotated_frame, ear_value = detector.process_frame(frame)
                
                # Convert annotated frame back to bytes for backchanneling
                _, buffer = cv2.imencode('.jpg', annotated_frame)
                frame_bytes = buffer.tobytes()
                
                # Send back results
                await websocket.send_bytes(frame_bytes)  # Send annotated frame first
                await websocket.send_json({
                    "timestamp": timestamp,
                    "processed_data": -0.1 if ear_value is None else float(ear_value)
                    })
            except Exception as e:
                print(f"Error processing frame: {e}")
                break
    except WebSocketDisconnect:
        print("Client disconnected")