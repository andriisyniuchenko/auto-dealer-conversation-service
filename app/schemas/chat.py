from datetime import datetime

from pydantic import BaseModel


class ChatSessionResponse(BaseModel):
    session_id: str
    created_at: datetime


class ChatMessageRequest(BaseModel):
    session_id: str
    message: str


class ChatMessageResponse(BaseModel):
    session_id: str
    message_id: str


class ChatHistoryItem(BaseModel):
    role: str
    content: str
    created_at: datetime


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: list[ChatHistoryItem]