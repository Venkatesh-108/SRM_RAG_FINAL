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
        
        # Greeting patterns for casual conversation detection
        self.greeting_patterns = [
            r'^(hi|hello|hey|hiya|howdy)\s*!?$',
            r'^(hi|hello|hey|hiya|howdy)\s+(there|you)\s*!?$',
            r'^(good\s+(morning|afternoon|evening|day))\s*!?$',
            r'^(how\s+are\s+you|how\s+are\s+you\s+doing|how\s+do\s+you\s+do)\s*!?$',
            r'^(what\'s\s+up|whats\s+up|sup)\s*!?$',
            r'^(nice\s+to\s+meet\s+you|pleased\s+to\s+meet\s+you)\s*!?$',
            r'^(thanks|thank\s+you)\s*!?$',
            r'^(bye|goodbye|see\s+you|farewell)\s*!?$',
        ]
        
        # Default responses for greetings
        self.default_responses = {
            'greeting': "Hi! I'm AI Doc Assist, your intelligent assistant for HCL SRM. How can I help you today?",
            'how_are_you': "I'm doing great, thank you for asking! I'm here and ready to help you with any questions about HCL SRM. What would you like to know?",
            'good_morning': "Good morning! I'm AI Doc Assist, ready to help you with HCL SRM. How can I assist you today?",
            'good_afternoon': "Good afternoon! I'm AI Doc Assist, your guide to HCL SRM. What can I help you with?",
            'good_evening': "Good evening! I'm AI Doc Assist, here to help with HCL SRM. How may I assist you?",
            'whats_up': "Hello! I'm AI Doc Assist, your HCL SRM assistant. I'm here to help you find information and answer questions. What do you need to know?",
            'thanks': "You're very welcome! I'm here whenever you need help with HCL SRM. Feel free to ask me anything!",
            'goodbye': "Goodbye! It was great helping you with HCL SRM. Feel free to come back anytime you have questions!"
        }
    
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
    
    def _detect_greeting(self, message: str) -> Optional[str]:
        """Detect if the message is a casual greeting and return appropriate response type"""
        message_clean = message.strip().lower()
        
        # Check each greeting pattern
        for i, pattern in enumerate(self.greeting_patterns):
            if re.match(pattern, message_clean, re.IGNORECASE):
                # Map pattern index to response type
                if i == 0 or i == 1:  # Basic greetings
                    return 'greeting'
                elif i == 2:  # Time-based greetings
                    if 'morning' in message_clean:
                        return 'good_morning'
                    elif 'afternoon' in message_clean:
                        return 'good_afternoon'
                    elif 'evening' in message_clean:
                        return 'good_evening'
                    else:
                        return 'greeting'
                elif i == 3:  # How are you
                    return 'how_are_you'
                elif i == 4:  # What's up
                    return 'whats_up'
                elif i == 5:  # Nice to meet you
                    return 'greeting'
                elif i == 6:  # Thanks
                    return 'thanks'
                elif i == 7:  # Goodbye
                    return 'goodbye'
        
        return None
    
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
        
        # Check if this is a casual greeting first
        greeting_type = self._detect_greeting(user_message)
        if greeting_type:
            logger.info(f"Detected greeting type: {greeting_type} for message: '{user_message}'")
            
            # Return default greeting response
            greeting_response = self.default_responses.get(greeting_type, self.default_responses['greeting'])
            
            ai_message = ChatMessage(
                role=MessageRole.ASSISTANT,
                content=greeting_response,
                sources=[],
                metadata={
                    "response_type": "greeting",
                    "greeting_type": greeting_type,
                    "confidence_score": 1.0
                }
            )
            
            session.add_message(ai_message)
            self.storage.save_session(session)
            
            processing_time = time.time() - start_time
            
            return ChatResponse(
                message=ai_message,
                session=session,
                sources=[],
                confidence_score=1.0,
                processing_time=processing_time
            )
        
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
                    
                    # CRITICAL FIX: For exact title matches, prioritize the most relevant match
                    # instead of combining all matches which can include unrelated sections
                    
                    # Find the best match by title similarity to the query
                    best_match = None
                    best_score = 0
                    
                    for match in exact_matches:
                        title = match.get('metadata', {}).get('title', '').lower()
                        query_lower = query.lower()
                        
                        # Calculate similarity score
                        if title == query_lower:
                            score = 1.0  # Perfect match
                        elif query_lower in title:
                            score = 0.8  # Query is contained in title
                        elif title in query_lower:
                            score = 0.6  # Title is contained in query
                        else:
                            # Calculate word overlap
                            query_words = set(query_lower.split())
                            title_words = set(title.split())
                            if query_words and title_words:
                                overlap = len(query_words & title_words) / len(query_words | title_words)
                                score = overlap * 0.5
                            else:
                                score = 0.0
                        
                        if score > best_score:
                            best_score = score
                            best_match = match
                    
                    if best_match and best_score > 0.3:  # Only use if reasonably relevant
                        content = best_match.get('text', '')
                        # Clean up content to remove unrelated sections
                        content = self._clean_section_content(content)
                        logger.info(f"Selected best match: '{best_match.get('metadata', {}).get('title', '')}' with score {best_score:.2f}")
                    else:
                        # Fall back to first match if no good match found
                        content = exact_matches[0].get('text', '')
                        content = self._clean_section_content(content)
                        logger.info(f"No good match found, using first match: '{exact_matches[0].get('metadata', {}).get('title', '')}'")
                    
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
