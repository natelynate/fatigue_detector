from fastapi import APIRouter, Request, WebSocket
from fastapi.websockets import WebSocketDisconnect
from . import templates
from ..dependencies import BlinkDetector
from fastapi.responses import JSONResponse
import numpy as np
import time
import cv2

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
                # Decode and convert to np array from websocket
                frame_data = await websocket.receive_bytes()
                nparr = np.frombuffer(frame_data, np.uint8)       
                frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                
                annotated_frame, ear_value = detector.process_frame(frame)
                print(f"Processed frame. EAR: {ear_value}", time.time())
                # Convert annotated frame back to bytes for backchanneling
                _, buffer = cv2.imencode('.jpg', annotated_frame)
                frame_bytes = buffer.tobytes()
                
                # Send back results
                await websocket.send_bytes(frame_bytes)  # Send annotated frame first
                await websocket.send_json({
                    "timestamp": time.time(),
                    "processed_data": -0.1 if ear_value is None else float(ear_value)
                    })
            except Exception as e:
                print(f"Error processing frame: {e}")
                break
    except WebSocketDisconnect:
        print("Client disconnected")