import json
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import pickle
from loguru import logger

from models.chat import ChatSession, ChatMessage, MessageRole

class ChatStorage:
    """Chat session storage with file-based persistence"""
    
    def __init__(self, storage_dir: str = "storage/chat_sessions"):
        self.storage_dir = Path(storage_dir)
        # Ensure the storage directory exists
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.sessions: Dict[str, ChatSession] = {}
        self.load_sessions()
    
    def load_sessions(self):
        """Load all chat sessions from storage"""
        try:
            for session_file in self.storage_dir.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                        # Convert timestamp strings back to datetime objects
                        session_data['created_at'] = datetime.fromisoformat(session_data['created_at'])
                        session_data['updated_at'] = datetime.fromisoformat(session_data['updated_at'])
                        
                        # Convert message timestamps
                        for msg in session_data.get('messages', []):
                            msg['timestamp'] = datetime.fromisoformat(msg['timestamp'])
                        
                        session = ChatSession(**session_data)
                        self.sessions[session.session_id] = session
                except Exception as e:
                    logger.error(f"Failed to load session from {session_file}: {e}")
            
            logger.info(f"Loaded {len(self.sessions)} chat sessions from storage")
        except Exception as e:
            logger.error(f"Failed to load chat sessions: {e}")
    
    def save_session(self, session: ChatSession):
        """Save a chat session to storage"""
        try:
            session_file = self.storage_dir / f"{session.session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(session.model_dump(), f, default=str, indent=2, ensure_ascii=False)
            self.sessions[session.session_id] = session
            logger.debug(f"Saved session {session.session_id}")
        except Exception as e:
            logger.error(f"Failed to save session {session.session_id}: {e}")
    
    def create_session(self, title: Optional[str] = None, initial_message: Optional[str] = None) -> ChatSession:
        """Create a new chat session"""
        session = ChatSession(title=title)
        
        if initial_message:
            message = ChatMessage(
                role=MessageRole.USER,
                content=initial_message
            )
            session.add_message(message)
        
        self.save_session(session)
        logger.info(f"Created new chat session: {session.session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID"""
        return self.sessions.get(session_id)
    
    def get_all_sessions(self) -> List[ChatSession]:
        """Get all chat sessions"""
        return list(self.sessions.values())
    
    def add_message(self, session_id: str, message: ChatMessage) -> Optional[ChatSession]:
        """Add a message to a chat session"""
        session = self.get_session(session_id)
        if not session:
            return None
        
        session.add_message(message)
        self.save_session(session)
        logger.debug(f"Added message to session {session_id}")
        return session
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session"""
        try:
            session = self.get_session(session_id)
            if not session:
                return False
            
            # Remove from memory
            del self.sessions[session_id]
            
            # Remove from storage
            session_file = self.storage_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
            
            logger.info(f"Deleted chat session: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False
    
    def clear_all_sessions(self) -> bool:
        """Clear all chat sessions"""
        try:
            # Clear memory
            self.sessions.clear()
            
            # Clear storage files
            for session_file in self.storage_dir.glob("*.json"):
                session_file.unlink()
            
            logger.info("Cleared all chat sessions")
            return True
        except Exception as e:
            logger.error(f"Failed to clear all sessions: {e}")
            return False
    
    def get_session_count(self) -> int:
        """Get total number of chat sessions"""
        return len(self.sessions)
    
    def search_sessions(self, query: str) -> List[ChatSession]:
        """Search sessions by content"""
        query_lower = query.lower()
        results = []
        
        for session in self.sessions.values():
            # Search in title
            if session.title and query_lower in session.title.lower():
                results.append(session)
                continue
            
            # Search in messages
            for message in session.messages:
                if query_lower in message.content.lower():
                    results.append(session)
                    break
        
        return results
