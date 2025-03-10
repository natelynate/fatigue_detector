from fastapi import APIRouter, Request, WebSocket, Depends, status
from fastapi.websockets import WebSocketDisconnect
from fastapi.responses import HTMLResponse
from . import templates
from ..dependencies import get_token_header
from ..core.security import verify_token, get_user_id_from_token
from ..services.kafka_producer import KafkaService
from jose import JWTError
import logging


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


async def get_kafka_service(websocket: WebSocket):
    return websocket.app.state.kafka_service


@router.get("/", response_class=HTMLResponse)
async def monitoring_page(request: Request, token: str = Depends(get_token_header)):
    return templates.TemplateResponse(
        "monitoring.html",
        {"request": request}
    )


@router.websocket("/websocket_process")
async def websocket_process(websocket:WebSocket,
                            kafka_service: KafkaService = Depends(get_kafka_service),
                            session_id=None,
                            user_id=None
                            ):
    try:
        token = websocket.cookies.get("access_token")
        if token and token.startswith("Bearer "):
            token = token.split("Bearer ")[1]
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        # Verify token
        try:
            _ = verify_token(token, "access")
            user_id = get_user_id_from_token(token, "access")
            if not user_id:
                logger.warning("No user_id in token payload")
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
                return
        except JWTError as e:
            logger.error(f"JWT verification failed: {e}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        
         # Accept the connection after verification
        await websocket.accept()
        logger.info(f"WebSocket accepted for user {user_id}")

        # Initialize session in Kafka
        try:
            session_id = await kafka_service.send_session_event(
                user_id=user_id,
                status="active"
            )
            logger.info(f"Kafka Session {session_id} started for user {user_id}")
        except Exception as e:
            logger.error(f"Failed to create Kafka session: {e}")
            await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
            return
        
        # Main Websocket loop
        last_event_onset = None
        while True:
            try:
                # Receive JSON data from client
                data = await websocket.receive_json()
            
                # Send the received data to t Kafka session
                timestamp = data.get('timestamp')
                ear_value = data.get('ear_value')
                logger.info(f"Received EAR value: {ear_value} at timestamp: {timestamp}") # debug

                # Message handling for blink events
                if data.get("event_onset"):
                    last_event_onset = timestamp
                    logger.debug(f"Blink onset detected at {timestamp}") # debug
                elif data.get("event_end"):
                    await kafka_service.send_blink_data(session_id, last_event_onset, timestamp)
                    blink_duration = timestamp - last_event_onset
                    logger.debug(f"Blink end detected at {timestamp}, duration: {blink_duration:.3f}s") # debug
                    last_event_onset = None
                
                # Message handling for frame event
                await kafka_service.send_frame_data(session_id, timestamp, ear_value)
                
                # Send acknowledgment back to client
                await websocket.send_json({
                    "status": "received",
                    "timestamp": timestamp
                })
            except WebSocketDisconnect:
                logger.info(f"Client disconnected normally for session {session_id}")
                if session_id:
                    await kafka_service.send_session_event(
                        user_id=user_id,
                        session_id=session_id,
                        status="complete"
                    )
                break
            except Exception as e:
                logger.error(f"Error in WebSocket loop: {e}")
                if session_id:
                    await kafka_service.send_session_event(
                        user_id=user_id,
                        session_id=session_id,
                        status="interrupted"
                    )
                break
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if session_id and user_id:
            try:
                await kafka_service.send_session_event(
                    user_id=user_id,
                    session_id=session_id,
                    status="interrupted"
                )
            except Exception as kafka_error:
                logger.error(f"Failed to update session status: {kafka_error}")
        
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)