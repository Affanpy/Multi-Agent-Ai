import os
import json
import asyncio
from typing import List, Dict
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from database import init_db, get_db
from models import Agent, Session, Message
from schemas import AgentCreate, AgentUpdate, AgentResponse, SessionResponse, SessionDetailResponse
from security import encrypt_api_key
from orchestrator import determine_speaking_order
from agent_runner import run_agent_stream

app = FastAPI(title="AgentRoom API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", 20))

@app.on_event("startup")
async def startup_event():
    await init_db()

# REST Endpoints
@app.get("/api/agents", response_model=List[AgentResponse])
async def list_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).order_by(Agent.order.asc()))
    agents = result.scalars().all()
    return agents

@app.post("/api/agents", response_model=AgentResponse)
async def create_agent(agent: AgentCreate, db: AsyncSession = Depends(get_db)):
    db_agent = Agent(
        name=agent.name,
        avatar_emoji=agent.avatar_emoji,
        role=agent.role,
        soul=agent.soul,
        system_prompt=agent.system_prompt,
        provider=agent.provider,
        model=agent.model,
        api_key_encrypted=encrypt_api_key(agent.api_key),
        temperature=agent.temperature,
        max_tokens=agent.max_tokens,
        is_active=agent.is_active,
        order=agent.order
    )
    db.add(db_agent)
    await db.commit()
    await db.refresh(db_agent)
    return db_agent

@app.put("/api/agents/{agent_id}", response_model=AgentResponse)
async def update_agent(agent_id: str, agent: AgentUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    db_agent = result.scalars().first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    for key, value in agent.model_dump(exclude_unset=True).items():
        if key == "api_key":
            if value:
                db_agent.api_key_encrypted = encrypt_api_key(value)
        else:
            setattr(db_agent, key, value)
            
    await db.commit()
    await db.refresh(db_agent)
    return db_agent

@app.delete("/api/agents/{agent_id}")
async def delete_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    db_agent = result.scalars().first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    await db.delete(db_agent)
    await db.commit()
    return {"message": "Agent deleted successfully"}

@app.post("/api/agents/{agent_id}/test")
async def test_agent(agent_id: str, payload: dict, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    db_agent = result.scalars().first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
        
    test_msg = payload.get("message", "Test message")
    
    agent_data = {
         "id": db_agent.id, "name": db_agent.name, "role": db_agent.role, "soul": db_agent.soul,
         "system_prompt": db_agent.system_prompt, "provider": db_agent.provider, "model": db_agent.model,
         "api_key_encrypted": db_agent.api_key_encrypted, "temperature": db_agent.temperature, "max_tokens": db_agent.max_tokens
    }
    
    try:
        response_chunks = []
        async for chunk in run_agent_stream(agent_data, [{"role": "user", "content": test_msg}]):
             response_chunks.append(chunk)
        return {"response": "".join(response_chunks)}
    except Exception as e:
         raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sessions", response_model=List[SessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).order_by(Session.created_at.desc()))
    return result.scalars().all()

@app.post("/api/sessions", response_model=SessionResponse)
async def create_session(db: AsyncSession = Depends(get_db)):
    db_session = Session(title="New Session", created_at=datetime.utcnow())
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session

@app.get("/api/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Session).options(selectinload(Session.messages)).where(Session.id == session_id)
    )
    db_session = result.scalars().first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return db_session

@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == session_id))
    db_session = result.scalars().first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    await db.delete(db_session)
    await db.commit()
    return {"message": "Session deleted"}

@app.get("/api/providers")
async def get_providers():
    return {
        "providers": [
             {"id": "openai", "name": "OpenAI"},
             {"id": "anthropic", "name": "Anthropic"},
             {"id": "gemini", "name": "Google Gemini"}
        ]
    }


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        if session_id not in self.active_connections:
            self.active_connections[session_id] = []
        self.active_connections[session_id].append(websocket)

    def disconnect(self, websocket: WebSocket, session_id: str):
        if session_id in self.active_connections and websocket in self.active_connections[session_id]:
            self.active_connections[session_id].remove(websocket)

    async def broadcast(self, session_id: str, message: dict):
        if session_id in self.active_connections:
            for connection in self.active_connections[session_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

manager = ConnectionManager()

@app.websocket("/ws/{session_id}")
async def websocket_chat(websocket: WebSocket, session_id: str, db: AsyncSession = Depends(get_db)):
    await manager.connect(websocket, session_id)
    
    try:
        while True:
            data = await websocket.receive_json()
            
            if data.get("type") == "ping":
                await websocket.send_json({"type": "pong"})
                continue
                
            if data.get("type") == "chat":
                user_msg_content = data.get("content", "")
                if not user_msg_content:
                    continue
                    
                user_msg = Message(session_id=session_id, role="user", content=user_msg_content)
                db.add(user_msg)
                
                res_session = await db.execute(select(Session).where(Session.id == session_id))
                sess = res_session.scalars().first()
                if sess and sess.title == "New Session":
                     sess.title = user_msg_content[:30] + ("..." if len(user_msg_content) > 30 else "")
                
                await db.commit()
                
                await manager.broadcast(session_id, {
                    "type": "user_message",
                    "content": user_msg_content,
                    "timestamp": user_msg.timestamp.isoformat()
                })
                
                agent_res = await db.execute(select(Agent).where(Agent.is_active == True))
                active_agents = list(agent_res.scalars().all())
                if not active_agents:
                    await manager.broadcast(session_id, {"type": "error", "content": "No active agents available"})
                    continue
                    
                agents_dict = {
                     a.id: {
                         "id": a.id, "name": a.name, "role": a.role, "soul": a.soul,
                         "system_prompt": a.system_prompt, "provider": a.provider,
                         "model": a.model, "api_key_encrypted": a.api_key_encrypted,
                         "temperature": a.temperature, "max_tokens": a.max_tokens,
                         "avatar_emoji": a.avatar_emoji
                     } for a in active_agents
                }
                
                history_res = await db.execute(select(Message).where(Message.session_id == session_id).order_by(Message.timestamp.desc()).limit(MAX_HISTORY_MESSAGES))
                chat_history_db = list(reversed(list(history_res.scalars().all())))
                
                raw_history = []
                for m in chat_history_db:
                    if m.role == "user":
                        raw_history.append({"role": "user", "name": "User", "content": m.content})
                    elif m.role == "agent":
                        agent_name = agents_dict[m.agent_id]["name"] if m.agent_id in agents_dict else "Agent"
                        raw_history.append({"role": "agent", "agent_id": str(m.agent_id), "name": agent_name, "content": m.content})
                
                history_for_moderator = raw_history[-10:]
                
                mod_decision = await determine_speaking_order(
                     active_agents=[agents_dict[aid] for aid in agents_dict],
                     user_message=user_msg_content,
                     recent_history=history_for_moderator
                )
                
                speaking_order = mod_decision.get("speaking_order", [])
                context_hints = mod_decision.get("context_hints", {})
                
                await manager.broadcast(session_id, {
                     "type": "moderator_decision",
                     "speaking_order": speaking_order,
                     "reasoning": mod_decision.get("reasoning", "")
                })
                
                for aid in speaking_order:
                     if aid not in agents_dict: continue
                     
                     agent_info = agents_dict[aid]
                     await manager.broadcast(session_id, {
                         "type": "agent_typing",
                         "agent_id": aid,
                         "agent_name": agent_info["name"],
                         "agent_emoji": agent_info["avatar_emoji"]
                     })
                     
                     hint = context_hints.get(aid, "")
                     collected_tokens = []
                     
                     try:
                         async for token in run_agent_stream(agent_info, raw_history, hint):
                              collected_tokens.append(token)
                              await manager.broadcast(session_id, {
                                   "type": "agent_stream",
                                   "agent_id": aid,
                                   "token": token
                              })
                              await asyncio.sleep(0.01)
                     except Exception as e:
                         collected_tokens.append(f"\n[Error generating response: {str(e)}]")
                     
                     full_message = "".join(collected_tokens)
                     
                     agent_msg = Message(session_id=session_id, role="agent", agent_id=aid, content=full_message)
                     db.add(agent_msg)
                     await db.commit()
                     
                     raw_history.append({
                         "role": "agent",
                         "agent_id": str(aid),
                         "name": agent_info["name"],
                         "content": full_message
                     })
                     
                     await manager.broadcast(session_id, {
                          "type": "agent_done",
                          "agent_id": aid,
                          "agent_name": agent_info["name"],
                          "agent_emoji": agent_info["avatar_emoji"],
                          "full_message": full_message,
                          "timestamp": agent_msg.timestamp.isoformat()
                     })
                     
                await manager.broadcast(session_id, {"type": "round_complete"})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
