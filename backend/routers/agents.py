from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db
from models import Agent
from schemas import AgentCreate, AgentUpdate, AgentResponse
from security import encrypt_api_key
from agent_runner import run_agent_stream

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("", response_model=List[AgentResponse])
async def list_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).order_by(Agent.order.asc()))
    agents = result.scalars().all()
    return agents


@router.post("", response_model=AgentResponse)
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


@router.put("/{agent_id}", response_model=AgentResponse)
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


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    db_agent = result.scalars().first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    await db.delete(db_agent)
    await db.commit()
    return {"message": "Agent deleted successfully"}


@router.put("/reorder")
async def reorder_agents(payload: dict, db: AsyncSession = Depends(get_db)):
    ordered_ids = payload.get("ordered_ids", [])
    for idx, agent_id in enumerate(ordered_ids):
        result = await db.execute(select(Agent).where(Agent.id == agent_id))
        db_agent = result.scalars().first()
        if db_agent:
            db_agent.order = idx
    await db.commit()
    return {"message": "Agents reordered successfully"}


@router.patch("/{agent_id}/toggle")
async def toggle_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    db_agent = result.scalars().first()
    if not db_agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    db_agent.is_active = not db_agent.is_active
    await db.commit()
    await db.refresh(db_agent)
    return db_agent


@router.post("/{agent_id}/test")
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
