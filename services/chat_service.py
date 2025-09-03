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
        """Get all chat sessions, sorted by recent activity."""
        all_sessions = self.storage.get_all_sessions()
        # Sort by updated_at descending
        return sorted(all_sessions, key=lambda x: x.updated_at, reverse=True)
    
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
        if self.rag_service and self.rag_service != "not_available":
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
        try:
            # Import the RAG functions from the main app
            from app import load_indices_and_chunks, search_and_rerank, generate_answer_with_ollama
            
            # Load indices
            chunks, bm25, faiss_index, embedding_model = load_indices_and_chunks()
            if chunks is None:
                raise ValueError("Index not found. Please ensure documents are indexed.")
            
            # Search and rerank
            retrieved_chunks = search_and_rerank(query, chunks, bm25, faiss_index, embedding_model)
            
            # Generate answer
            answer, confidence_score, validation_result = generate_answer_with_ollama(query, retrieved_chunks)
            
            return answer, confidence_score, retrieved_chunks
            
        except Exception as e:
            logger.error(f"Error in RAG response generation: {e}")
            # Return a helpful error message
            return f"I encountered an error while processing your request: {str(e)}", 0.0, []
    
    def _extract_sources_from_chunks(self, chunks: List[Dict[str, Any]]) -> List[Source]:
        """Extract source information from RAG context chunks"""
        sources = []
        
        for chunk in chunks:
            # Handle both old and new chunk formats
            metadata = chunk.get('metadata', {})
            if isinstance(metadata, dict):
                filename = metadata.get('filename', 'Unknown')
                page_number = metadata.get('page_number')
            else:
                # Handle case where metadata might be a string or other format
                filename = str(metadata) if metadata else 'Unknown'
                page_number = None
            
            source = Source(
                filename=filename,
                page_number=page_number,
                chunk_id=str(chunk.get('id', '')),
                relevance_score=float(chunk.get('score', 0.0)),
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
