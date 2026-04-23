from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from connection_manager import manager
from debate_manager import start_debate_task, stop_debate_task
from services.chat_service import process_chat_message

router = APIRouter()


@router.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue
                
            if data.get("type") == "start_debate":
                start_debate_task(session_id, data, manager)
                continue
                
            if data.get("type") == "stop_debate":
                stop_debate_task(session_id)
                continue
                
            if data.get("type") == "chat":
                await process_chat_message(session_id, data, manager)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
