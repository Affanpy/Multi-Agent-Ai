import os
import json
import asyncio
import re
from typing import List, Dict
from datetime import datetime
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, UploadFile, File as FastAPIFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from database import init_db, get_db
from models import Agent, Session, Message
from schemas import AgentCreate, AgentUpdate, AgentResponse, SessionResponse, SessionDetailResponse
from security import encrypt_api_key
from orchestrator import determine_speaking_order, generate_summary
from agent_runner import run_agent_stream
from file_handler import process_uploaded_file, model_supports_vision, SUPPORTED_IMAGE_TYPES, SUPPORTED_DOC_TYPES

app = FastAPI(title="AgentRoom API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", 20))

# In-memory cache untuk file yang diupload (per session)
uploaded_files_cache: Dict[str, dict] = {}

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

@app.put("/api/agents/reorder")
async def reorder_agents(payload: dict, db: AsyncSession = Depends(get_db)):
    ordered_ids = payload.get("ordered_ids", [])
    for idx, agent_id in enumerate(ordered_ids):
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        db_agent = result.scalars().first()
        if db_agent:
            db_agent.order = idx
    await db.commit()
    return {"message": "Agents reordered successfully"}

@app.patch("/api/agents/{agent_id}/toggle")
async def toggle_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    db_agent = result.scalars().first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    db_agent.is_active = not db_agent.is_active
    await db.commit()
    await db.refresh(db_agent)
    return db_agent

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

@app.post("/api/upload")
async def upload_file(file: UploadFile = FastAPIFile(...)):
    content_type = file.content_type or ""
    
    if content_type not in SUPPORTED_IMAGE_TYPES and content_type not in SUPPORTED_DOC_TYPES:
        raise HTTPException(status_code=400, detail=f"Tipe file tidak didukung: {content_type}. Gunakan gambar (PNG/JPG/WebP) atau dokumen (PDF/DOCX/TXT).")
    
    file_bytes = await file.read()
    
    # Max 10MB
    if len(file_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Ukuran file maksimal 10MB")
    
    file_data = process_uploaded_file(file.filename, content_type, file_bytes)
    
    # Simpan ke cache dengan unique ID
    file_id = f"file-{id(file_bytes)}-{file.filename}"
    uploaded_files_cache[file_id] = file_data
    
    return {
        "file_id": file_id,
        "filename": file_data["filename"],
        "content_type": content_type,
        "is_image": file_data["is_image"],
        "is_document": file_data["is_document"],
        "has_extracted_text": bool(file_data["extracted_text"]),
        "text_preview": (file_data["extracted_text"][:200] + "...") if file_data["extracted_text"] and len(file_data["extracted_text"]) > 200 else file_data.get("extracted_text"),
        "base64_preview": file_data["base64_data"][:100] + "..." if file_data["base64_data"] else None
    }

@app.get("/api/providers")
async def get_providers():
    return {
        "providers": [
             {"id": "openai", "name": "OpenAI"},
             {"id": "anthropic", "name": "Anthropic"},
             {"id": "gemini", "name": "Google Gemini"}
        ]
    }

@app.post("/api/sessions/{session_id}/summary")
async def summarize_session(session_id: str, db: AsyncSession = Depends(get_db)):
    # Ambil semua pesan publik di sesi ini
    result = await db.execute(
        select(Message).where(
            Message.session_id == session_id,
            Message.is_private == False
        ).order_by(Message.timestamp.asc())
    )
    messages = list(result.scalars().all())
    
    if len(messages) < 2:
        raise HTTPException(status_code=400, detail="Diskusi terlalu pendek untuk dirangkum")
    
    # Ambil semua agen untuk resolve nama
    agent_res = await db.execute(select(Agent))
    agents_map = {a.id: a.name for a in agent_res.scalars().all()}
    
    # Format riwayat chat
    chat_history = []
    for m in messages:
        if m.role == "user":
            chat_history.append({"role": "user", "content": m.content})
        elif m.role == "agent":
            agent_name = agents_map.get(m.agent_id, "Agent")
            chat_history.append({"role": "agent", "name": agent_name, "content": m.content})
    
    summary_text = await generate_summary(chat_history)
    return {"summary": summary_text}

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
                    
                is_private = data.get("is_private", False)
                target_agent_id = data.get("target_agent_id")
                moderator_enabled = data.get("moderator_enabled", True)
                reply_to_agent_id = data.get("reply_to_agent_id")
                file_id = data.get("file_id")
                
                # Resolve file data dari cache
                file_data = uploaded_files_cache.pop(file_id, None) if file_id else None
                user_msg = Message(
                    session_id=session_id, 
                    role="user", 
                    content=user_msg_content, 
                    is_private=is_private, 
                    target_agent_id=target_agent_id
                )
                db.add(user_msg)
                
                res_session = await db.execute(select(Session).where(Session.id == session_id))
                sess = res_session.scalars().first()
                if sess and sess.title == "New Session":
                     sess.title = user_msg_content[:30] + ("..." if len(user_msg_content) > 30 else "")
                
                await db.commit()
                
                # Resolve reply agent name untuk broadcast
                _reply_agent_name = None
                if reply_to_agent_id:
                    # Kita perlu agents_dict tapi belum di-build, jadi query langsung
                    _reply_res = await db.execute(select(Agent).where(Agent.id == reply_to_agent_id))
                    _reply_agent = _reply_res.scalars().first()
                    if _reply_agent:
                        _reply_agent_name = _reply_agent.name

                await manager.broadcast(session_id, {
                    "type": "user_message",
                    "content": user_msg_content,
                    "timestamp": user_msg.timestamp.isoformat(),
                    "is_private": is_private,
                    "target_agent_id": target_agent_id,
                    "reply_to_agent_name": _reply_agent_name,
                    "file_info": {
                        "filename": file_data["filename"],
                        "is_image": file_data["is_image"],
                        "is_document": file_data["is_document"],
                        "base64_data": file_data.get("base64_data") if file_data.get("is_image") else None,
                        "content_type": file_data.get("content_type")
                    } if file_data else None
                })
                
                agent_res = await db.execute(select(Agent).where(Agent.is_active == True).order_by(Agent.order.asc()))
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
                    # Filter cerdas memori privat
                    if m.is_private:
                        if not is_private or str(m.target_agent_id) != str(target_agent_id):
                            continue
                            
                    if m.role == "user":
                        raw_history.append({"role": "user", "name": "User", "content": m.content})
                    elif m.role == "agent":
                        agent_name = agents_dict[m.agent_id]["name"] if m.agent_id in agents_dict else "Agent"
                        raw_history.append({"role": "agent", "agent_id": str(m.agent_id), "name": agent_name, "content": m.content})
                
                if is_private:
                     speaking_order = [target_agent_id] if target_agent_id in agents_dict else []
                     context_hints = {target_agent_id: "PERINGATAN KRITIS: Kamu ditarik ke obrolan 1-on-1 private. Jawab langsung secara spesifik pesannya, ini rahasia, ABAIKAN jalannya grup."}
                elif reply_to_agent_id and reply_to_agent_id in agents_dict:
                     # Reply langsung: bypass moderator, hanya agen target yang menjawab
                     speaking_order = [reply_to_agent_id]
                     reply_agent_name = agents_dict[reply_to_agent_id]["name"]
                     context_hints = {reply_to_agent_id: f"User secara khusus membalas pesanmu dan mengarahkan pertanyaan ini langsung padamu. Jawab secara langsung dan fokus."}
                     # Update broadcast agar frontend tahu ini reply
                     await manager.broadcast(session_id, {
                          "type": "moderator_decision",
                          "speaking_order": speaking_order,
                          "reasoning": f"User membalas langsung ke {reply_agent_name}"
                     })
                elif not moderator_enabled:
                     # Mode Sequential: Semua agen menjawab berurutan tanpa moderator
                     speaking_order = [a.id for a in active_agents]
                     context_hints = {}
                     await manager.broadcast(session_id, {
                          "type": "moderator_decision",
                          "speaking_order": speaking_order,
                          "reasoning": "Moderator dinonaktifkan — semua agen menjawab berurutan."
                     })
                else:
                     mod_decision = await determine_speaking_order(
                          active_agents=[agents_dict[aid] for aid in agents_dict],
                          user_message=user_msg_content,
                          recent_history=raw_history[-10:]
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
                         async for token in run_agent_stream(agent_info, raw_history, hint, file_data=file_data):
                              collected_tokens.append(token)
                              await manager.broadcast(session_id, {
                                   "type": "agent_stream",
                                   "agent_id": aid,
                                   "token": token,
                                   "is_private": is_private,
                                   "target_agent_id": target_agent_id
                              })
                              await asyncio.sleep(0.01)
                     except Exception as e:
                         # Fix #5: Error Handling Graceful Fallback
                         error_msg = f"\n[System: {agent_info['name']} mengalami gangguan koneksi API. Berlanjut ke agen berikutnya...]"
                         collected_tokens.append(error_msg)
                         await manager.broadcast(session_id, {
                             "type": "agent_stream",
                             "agent_id": aid,
                             "token": error_msg,
                             "is_private": is_private,
                             "target_agent_id": target_agent_id
                         })
                     
                     full_message = "".join(collected_tokens)
                     
                     # Fix #2: Post-Processing Regex Filter untuk membuang Prefix Halusinasi
                     all_names = [a.name for a in active_agents]
                     for name in all_names:
                         # Hapus pola seperti [Nama]: atau Nama: atau **Nama**: di awal baris baru
                         pattern = rf'(?m)^\s*\[?{re.escape(name)}\]?\s*[::]\s*|^\s*\*{{1,2}}{re.escape(name)}\*{{1,2}}\s*[::]\s*'
                         full_message = re.sub(pattern, '', full_message, flags=re.IGNORECASE).strip()
                         
                     # Bersihkan format pemisah seperti '---' di awal pesan yang sering terbawa
                     full_message = re.sub(r'^(?:---\s*|\n)+', '', full_message).strip()
                     
                     agent_msg = Message(
                         session_id=session_id, 
                         role="agent", 
                         agent_id=aid, 
                         content=full_message,
                         is_private=is_private,
                         target_agent_id=target_agent_id
                     )
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
                          "timestamp": agent_msg.timestamp.isoformat(),
                          "is_private": is_private,
                          "target_agent_id": target_agent_id
                     })
                     
                await manager.broadcast(session_id, {"type": "round_complete"})
                
    except WebSocketDisconnect:
        manager.disconnect(websocket, session_id)
