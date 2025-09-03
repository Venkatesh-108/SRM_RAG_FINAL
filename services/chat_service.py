import time
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger

from models.chat import ChatSession, ChatMessage, MessageRole, Source, ChatResponse
from storage.chat_storage import ChatStorage

class ChatService:
    """Service for managing chat functionality with RAG integration"""
    
    def __init__(self, rag_service=None):
        self.storage = ChatStorage()
        self.rag_service = rag_service  # Will be injected from main app
    
    def create_session(self, title: Optional[str] = None, initial_message: Optional[str] = None) -> ChatSession:
        """Create a new chat session"""
        return self.storage.create_session(title, initial_message)
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID"""
        return self.storage.get_session(session_id)
    
    def get_all_sessions(self) -> List[ChatSession]:
        """Get all chat sessions"""
        return self.storage.get_all_sessions()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a chat session"""
        return self.storage.delete_session(session_id)
    
    def clear_all_sessions(self) -> bool:
        """Clear all chat sessions"""
        return self.storage.clear_all_sessions()
    
    async def send_message(self, session_id: str, user_message: str) -> ChatResponse:
        """Send a message and get AI response"""
        start_time = time.time()
        
        # Get or create session
        session = self.storage.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        # Add user message
        user_msg = ChatMessage(
            role=MessageRole.USER,
            content=user_message
        )
        session.add_message(user_msg)
        
        # Generate AI response using RAG
        if self.rag_service:
            try:
                # Get answer from RAG system
                answer, confidence_score, context_chunks = await self._get_rag_response(user_message)
                
                # Extract sources from context chunks
                sources = self._extract_sources_from_chunks(context_chunks)
                
                # Create AI message
                ai_message = ChatMessage(
                    role=MessageRole.ASSISTANT,
                    content=answer,
                    sources=sources,
                    metadata={
                        "confidence_score": confidence_score,
                        "context_chunks_count": len(context_chunks)
                    }
                )
                
                # Add AI message to session
                session.add_message(ai_message)
                
                # Save session
                self.storage.save_session(session)
                
                processing_time = time.time() - start_time
                
                return ChatResponse(
                    message=ai_message,
                    session=session,
                    sources=sources,
                    confidence_score=confidence_score,
                    processing_time=processing_time
                )
                
            except Exception as e:
                logger.error(f"Failed to generate RAG response: {e}")
                # Fallback response
                fallback_message = ChatMessage(
                    role=MessageRole.ASSISTANT,
                    content="I apologize, but I encountered an error while processing your request. Please try again.",
                    metadata={"error": str(e)}
                )
                session.add_message(fallback_message)
                self.storage.save_session(session)
                
                processing_time = time.time() - start_time
                
                return ChatResponse(
                    message=fallback_message,
                    session=session,
                    sources=[],
                    confidence_score=0.0,
                    processing_time=processing_time
                )
        else:
            # No RAG service available
            fallback_message = ChatMessage(
                role=MessageRole.ASSISTANT,
                content="I'm sorry, but the RAG system is not available at the moment. Please try again later.",
                metadata={"error": "RAG service not available"}
            )
            session.add_message(fallback_message)
            self.storage.save_session(session)
            
            processing_time = time.time() - start_time
            
            return ChatResponse(
                message=fallback_message,
                session=session,
                sources=[],
                confidence_score=0.0,
                processing_time=processing_time
            )
    
    async def _get_rag_response(self, query: str) -> Tuple[str, float, List[Dict[str, Any]]]:
        """Get response from RAG system"""
        if not self.rag_service:
            raise ValueError("RAG service not available")
        
        # This will be implemented when we integrate with the existing RAG system
        # For now, return a placeholder
        return "This is a placeholder response from the RAG system.", 0.8, []
    
    def _extract_sources_from_chunks(self, chunks: List[Dict[str, Any]]) -> List[Source]:
        """Extract source information from RAG context chunks"""
        sources = []
        
        for chunk in chunks:
            source = Source(
                filename=chunk.get('metadata', {}).get('filename', 'Unknown'),
                page_number=chunk.get('metadata', {}).get('page_number'),
                chunk_id=chunk.get('id'),
                relevance_score=chunk.get('score', 0.0),
                content_preview=chunk.get('text', '')[:100] + "..." if len(chunk.get('text', '')) > 100 else chunk.get('text', '')
            )
            sources.append(source)
        
        return sources
    
    def search_sessions(self, query: str) -> List[ChatSession]:
        """Search sessions by content"""
        return self.storage.search_sessions(query)
    
    def get_session_count(self) -> int:
        """Get total number of chat sessions"""
        return self.storage.get_session_count()
    
    def get_recent_sessions(self, limit: int = 10) -> List[ChatSession]:
        """Get recent chat sessions"""
        all_sessions = self.storage.get_all_sessions()
        # Sort by updated_at descending and return limited results
        sorted_sessions = sorted(all_sessions, key=lambda x: x.updated_at, reverse=True)
        return sorted_sessions[:limit]
