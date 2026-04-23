from typing import List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from database import get_db
from models import Agent, Session, Message
from schemas import SessionResponse, SessionDetailResponse
from orchestrator import generate_summary

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=List[SessionResponse])
async def list_sessions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).order_by(Session.created_at.desc()))
    return result.scalars().all()


@router.post("", response_model=SessionResponse)
async def create_session(db: AsyncSession = Depends(get_db)):
    db_session = Session(title="New Session", created_at=datetime.now(timezone.utc))
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Session).options(selectinload(Session.messages)).where(Session.id == session_id)
    )
    db_session = result.scalars().first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    return db_session


@router.delete("/{session_id}")
async def delete_session(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Session).where(Session.id == session_id))
    db_session = result.scalars().first()
    if not db_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    await db.delete(db_session)
    await db.commit()
    return {"message": "Session deleted"}


@router.post("/{session_id}/summary")
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
