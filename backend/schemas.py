from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

class AgentBase(BaseModel):
    name: str
    avatar_emoji: str = "🤖"
    role: str
    soul: str
    system_prompt: str
    provider: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 1024
    is_active: bool = True
    order: int = 0

class AgentCreate(AgentBase):
    api_key: str

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    avatar_emoji: Optional[str] = None
    role: Optional[str] = None
    soul: Optional[str] = None
    system_prompt: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    is_active: Optional[bool] = None
    order: Optional[int] = None

class AgentResponse(AgentBase):
    id: str
    model_config = ConfigDict(from_attributes=True)

class MessageResponse(BaseModel):
    id: str
    session_id: str
    role: str
    agent_id: Optional[str] = None
    content: str
    timestamp: datetime
    model_config = ConfigDict(from_attributes=True)

class SessionResponse(BaseModel):
    id: str
    title: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class SessionDetailResponse(SessionResponse):
    messages: List[MessageResponse] = []
    model_config = ConfigDict(from_attributes=True)
