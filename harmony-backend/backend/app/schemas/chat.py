"""Chat schemas — 对应前端 ChatMessage。"""
from typing import List, Literal, Optional, Any
from pydantic import BaseModel


class Attachment(BaseModel):
    type: Literal["table", "chart", "order"]
    data: Any


class ChatMessage(BaseModel):
    id: Optional[str] = None
    role: Literal["user", "assistant"]
    content: str
    timestamp: Optional[str] = None
    attachments: Optional[List[Attachment]] = None


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    stream: bool = False


class ChatResponse(BaseModel):
    content: str
