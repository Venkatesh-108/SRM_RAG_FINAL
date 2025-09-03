from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class Source(BaseModel):
    """Source information for a message"""
    filename: str
    page_number: Optional[int] = None
    chunk_id: Optional[str] = None
    relevance_score: Optional[float] = None
    content_preview: Optional[str] = None

class ChatMessage(BaseModel):
    """Individual chat message"""
    id: str = Field(default_factory=lambda: f"msg_{datetime.now().timestamp()}")
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    sources: List[Source] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ChatSession(BaseModel):
    """Chat session containing multiple messages"""
    session_id: str = Field(default_factory=lambda: f"session_{datetime.now().timestamp()}")
    title: Optional[str] = None
    messages: List[ChatMessage] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    def add_message(self, message: ChatMessage):
        """Add a message to the session"""
        self.messages.append(message)
        self.updated_at = datetime.now()
        
        # Auto-generate title from first user message if not set
        if not self.title and message.role == MessageRole.USER:
            self.title = message.content[:50] + "..." if len(message.content) > 50 else message.content

class CreateSessionRequest(BaseModel):
    """Request to create a new chat session"""
    title: Optional[str] = None
    initial_message: Optional[str] = None

class SendMessageRequest(BaseModel):
    """Request to send a message in a chat session"""
    content: str
    session_id: str

class ChatResponse(BaseModel):
    """Response from chat API"""
    message: ChatMessage
    session: ChatSession
    sources: List[Source]
    confidence_score: float
    processing_time: float

class SessionListResponse(BaseModel):
    """Response for listing chat sessions"""
    sessions: List[ChatSession]
    total_count: int
