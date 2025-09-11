import time
from typing import List, Dict, Any, Optional, Tuple
from loguru import logger
from pathlib import Path
import re

from models.chat import ChatSession, ChatMessage, MessageRole, Source, ChatResponse
from storage.chat_storage import ChatStorage
from services.rag_service import RAGService
from services.ollama_service import generate_answer_with_ollama

class ChatService:
    """Service for managing chat functionality with RAG integration"""
    
    def __init__(self, rag_service: RAGService):
        self.storage = ChatStorage()
        self.rag_service = rag_service
    
    def create_session(self, title: Optional[str] = None, initial_message: Optional[str] = None) -> ChatSession:
        """Create a new chat session"""
        return self.storage.create_session(title, initial_message)
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get a chat session by ID"""
        return self.storage.get_session(session_id)
    
    def get_all_sessions(self) -> List[ChatSession]:
        """Get all chat sessions, sorted by recent activity."""
        all_sessions = self.storage.get_all_sessions()
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
        
        session = self.storage.get_session(session_id)
        if not session:
            raise ValueError(f"Session {session_id} not found")
        
        user_msg = ChatMessage(
            role=MessageRole.USER,
            content=user_message
        )
        session.add_message(user_msg)
        
        if self.rag_service:
            try:
                # Check if direct results mode is enabled
                use_direct = self.rag_service.config.get("use_direct_results", False)
                answer, confidence_score, context_chunks = await self._get_rag_response(user_message, use_direct_results=use_direct)
                
                sources = self._extract_sources_from_chunks(context_chunks)
                
                ai_message = ChatMessage(
                    role=MessageRole.ASSISTANT,
                    content=answer,
                    sources=sources,
                    metadata={
                        "confidence_score": confidence_score,
                        "context_chunks_count": len(context_chunks)
                    }
                )
                
                session.add_message(ai_message)
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
    
    def _normalize(self, text: str) -> str:
        if not text:
            return ""
        t = text.strip().lower()
        t = re.sub(r"\s+", " ", t)
        t = re.sub(r"[`:*_]+", "", t)
        t = t.replace("—", "-")
        return t
    
    def _extract_section_from_markdown(self, markdown_content: str, section_title: str) -> Optional[str]:
        """Dynamically extracts content for a section from full markdown."""
        lines = markdown_content.split('\n')
        
        target_heading_level = -1
        start_index = -1
        
        normalized_title_to_find = self._normalize(section_title)
        
        for i, line in enumerate(lines):
            line_strip = line.strip()
            match = re.match(r'^(#+)\s+(.*)', line_strip)
            if match:
                level = len(match.group(1))
                heading_text = match.group(2).strip()
                
                if self._normalize(heading_text) == normalized_title_to_find:
                    target_heading_level = level
                    start_index = i
                    break

        if start_index == -1:
            logger.warning(f"Could not find section '{section_title}' in markdown content for dynamic extraction.")
            return None

        content_lines = [lines[start_index]]
        for i in range(start_index + 1, len(lines)):
            line = lines[i]
            line_strip = line.strip()
            
            match = re.match(r'^(#+)\s+', line_strip)
            if match:
                current_level = len(match.group(1))
                if current_level <= target_heading_level:
                    break
            
            content_lines.append(line)

        return '\n'.join(content_lines).strip()

    async def _get_rag_response(self, query: str, use_direct_results: bool = False) -> Tuple[str, float, List[Dict[str, Any]]]:
        """Get response from RAG system"""
        try:
            retrieved_chunks = self.rag_service.search(query)
            
            if use_direct_results:
                # Return direct results without LLM processing
                direct_response = self._format_direct_results(query, retrieved_chunks)
                return direct_response, 1.0, retrieved_chunks
            
            # Check if we got complete content from exact title match
            if retrieved_chunks:
                exact_matches = [chunk for chunk in retrieved_chunks if chunk.get('metadata', {}).get('match_type') == 'exact_title_match']
                if exact_matches:
                    # For exact title matches, return the section content directly without LLM processing
                    logger.info(f"Found {len(exact_matches)} exact title match(es) for query: '{query}' - returning section content directly")
                    
                    if len(exact_matches) == 1:
                        # Single match - return content directly
                        content = exact_matches[0].get('text', '')
                        # Clean up content to remove unrelated sections
                        content = self._clean_section_content(content)
                    else:
                        # Multiple matches - combine with separators
                        combined_content = ""
                        for i, chunk in enumerate(exact_matches):
                            if i > 0:
                                combined_content += "\n\n---\n\n"  # Separator between sections
                            chunk_content = chunk.get('text', '')
                            # Clean each chunk
                            chunk_content = self._clean_section_content(chunk_content)
                            combined_content += chunk_content
                        content = combined_content
                    
                    return content.strip(), 1.0, exact_matches
            
            # Standard RAG response generation
            answer, confidence_score, validation_result = generate_answer_with_ollama(query, retrieved_chunks, self.rag_service.config)
            return answer, confidence_score, retrieved_chunks
            
        except Exception as e:
            logger.error(f"Error in RAG response generation: {e}")
            return f"I encountered an error while processing your request: {str(e)}", 0.0, []
    
    def _clean_section_content(self, content: str) -> str:
        """Clean section content by removing unrelated sections and metadata, and improve formatting"""
        if not content:
            return content
        
        lines = content.split('\n')
        cleaned_lines = []
        is_first_header = True
        
        for line in lines:
            # Stop at common document boundaries that are not part of the main section
            if line.strip().startswith('## Documentation Feedback'):
                break
            if line.strip().startswith('## Appendix'):
                break
            if line.strip().startswith('# Chapter') and 'Chapter' not in line[:20]:  # Don't break on chapter references in metadata
                break
            
            # Skip chapter and page metadata lines
            line_strip = line.strip()
            if (line_strip.startswith('*Chapter:') and line_strip.endswith('*')) or \
               (line_strip.startswith('*Page:') and line_strip.endswith('*')):
                continue
            
            # Improve header formatting
            if line_strip.startswith('##'):
                if is_first_header:
                    # Main title: Remove ## and make it larger (use # for larger font)
                    title_text = line_strip.replace('##', '').strip()
                    cleaned_lines.append(f"# {title_text}")
                    is_first_header = False
                else:
                    # Sub-titles: Keep as ## but could be styled smaller
                    cleaned_lines.append(line)
            else:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines).strip()
    
    def _extract_sources_from_chunks(self, chunks: List[Dict[str, Any]]) -> List[Source]:
        """Extract source information from RAG context chunks"""
        sources = []
        
        for chunk in chunks:
            metadata = chunk.get('metadata', {})
            doc_id = metadata.get('filename', 'Unknown')
            
            # Convert internal document ID to actual filename using RAGService
            filename = self.rag_service.get_pdf_filename_from_document_id(doc_id)
            
            page_number = metadata.get('page_number')
            section_title = metadata.get('section_title', 'Unknown Section')
            relevance_score = metadata.get('relevance_score', 0.0)
            
            source = Source(
                filename=filename,
                page_number=page_number,
                chunk_id=str(metadata.get('chunk_id', section_title)),
                relevance_score=float(relevance_score),
                content_preview=chunk.get('text', '')[:150] + "..." if len(chunk.get('text', '')) > 150 else chunk.get('text', '')
            )
            sources.append(source)
        
        return sources
    
    def _format_direct_results(self, query: str, chunks: List[Dict[str, Any]]) -> str:
        """Format direct search results without LLM processing"""
        if not chunks:
            return f"No relevant information found for: '{query}'"
        
        response = f"**Direct Search Results for: '{query}'**\n\n"
        
        for i, chunk in enumerate(chunks, 1):
            metadata = chunk['metadata']
            response += f"**Result {i}:**\n"
            response += f"- **Title:** {metadata['section_title']}\n"
            response += f"- **Document:** {metadata['filename']}\n"
            response += f"- **Page:** {metadata['page_number']}\n"
            response += f"- **Relevance Score:** {metadata['relevance_score']:.3f}\n"
            response += f"- **Search Type:** {metadata.get('search_type', 'N/A')}\n"
            response += f"- **Content:**\n{chunk['text']}\n\n"
            response += "---\n\n"
        
        return response
    
    def search_sessions(self, query: str) -> List[ChatSession]:
        """Search sessions by content"""
        return self.storage.search_sessions(query)
    
    def get_session_count(self) -> int:
        """Get total number of chat sessions"""
        return self.storage.get_session_count()
    
    def get_recent_sessions(self, limit: int = 10) -> List[ChatSession]:
        """Get recent chat sessions"""
        all_sessions = self.storage.get_all_sessions()
        sorted_sessions = sorted(all_sessions, key=lambda x: x.updated_at, reverse=True)
        return sorted_sessions[:limit]
