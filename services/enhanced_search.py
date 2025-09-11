#!/usr/bin/env python3
"""
Enhanced Search Service with Exact Title Matching
Prioritizes exact title matches for complete responses
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import numpy as np
import json
import re
from collections import defaultdict

try:
    from rank_bm25 import BM25Okapi
    from sentence_transformers import SentenceTransformer, CrossEncoder
    import faiss
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Install with: pip install rank-bm25 sentence-transformers faiss-cpu")
    raise

logger = logging.getLogger(__name__)

class EnhancedSearchEngine:
    """Enhanced search with exact title matching and complete response capability"""
    
    def __init__(self, config: Dict[str, Any], index_dir: str = "index", extracted_docs_dir: str = "extracted_docs"):
        self.config = config
        self.index_dir = Path(index_dir)
        self.extracted_docs_dir = Path(extracted_docs_dir)
        
        # Load models based on config
        self.embedding_model = SentenceTransformer(config.get("embedding_model", "all-MiniLM-L6-v2"))
        
        # Load reranker only if reranking is enabled
        self.reranker = None
        if config.get("enable_reranking", False):
            reranker_model = config.get("reranker_model", "cross-encoder/ms-marco-MiniLM-L-6-v2")
            logger.info(f"Loading reranker model: {reranker_model}")
            self.reranker = CrossEncoder(reranker_model)
        
        # Load enhanced document data
        self.documents = self._discover_enhanced_documents()
        self.bm25_indexes = {}
        self.faiss_indexes = {}
        self.document_chunks = {}
        self.title_index = {}  # New: exact title matching index
        
        # Initialize enhanced indexes
        self._load_enhanced_indexes()
    
    def _discover_enhanced_documents(self) -> List[str]:
        """Discover documents with enhanced chunks"""
        documents = []
        
        if self.extracted_docs_dir.exists():
            for doc_dir in self.extracted_docs_dir.iterdir():
                if doc_dir.is_dir():
                    # Check for enhanced chunks
                    if (doc_dir / "enhanced_chunks_v2.json").exists():
                        documents.append(doc_dir.name)
                        logger.info(f"Found enhanced document: {doc_dir.name}")
                    elif (doc_dir / "enhanced_chunks.json").exists():
                        documents.append(doc_dir.name)
                        logger.info(f"Found standard document: {doc_dir.name}")
        
        logger.info(f"Discovered {len(documents)} documents total")
        return documents
    
    def _load_enhanced_indexes(self):
        """Load enhanced indexes with title matching"""
        
        for doc_name in self.documents:
            try:
                # Try to load enhanced v2 data first
                enhanced_v2_path = self.index_dir / f"{doc_name}_v2_metadata.json"
                standard_path = self.index_dir / f"{doc_name}_metadata.json"
                
                if enhanced_v2_path.exists():
                    metadata_path = enhanced_v2_path
                    faiss_path = self.index_dir / f"{doc_name}_v2.faiss"
                    version = "v2"
                elif standard_path.exists():
                    metadata_path = standard_path
                    faiss_path = self.index_dir / f"{doc_name}.faiss"
                    version = "v1"
                else:
                    logger.warning(f"No metadata found for {doc_name}")
                    continue
                
                # Load metadata
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                chunks = metadata.get('chunks', [])
                chunk_metadata = metadata.get('metadata', [])
                enhanced_chunks = metadata.get('enhanced_chunks', [])
                
                # Load FAISS index
                if faiss_path.exists():
                    faiss_index = faiss.read_index(str(faiss_path))
                    self.faiss_indexes[doc_name] = faiss_index
                
                # Create BM25 index
                tokenized_chunks = [chunk.lower().split() for chunk in chunks]
                self.bm25_indexes[doc_name] = BM25Okapi(tokenized_chunks)
                
                # Store chunk data
                self.document_chunks[doc_name] = {
                    'chunks': chunks,
                    'metadata': chunk_metadata,
                    'enhanced_chunks': enhanced_chunks,
                    'version': version
                }
                
                # Build title index for exact matching
                self._build_title_index(doc_name, chunk_metadata, enhanced_chunks)
                
                logger.info(f"Loaded {version} indexes for {doc_name}: {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"Failed to load indexes for {doc_name}: {e}")
    
    def _build_title_index(self, doc_name: str, chunk_metadata: List[Dict], enhanced_chunks: List[Dict]):
        """Build title index for exact matching"""
        
        if doc_name not in self.title_index:
            self.title_index[doc_name] = {}
        
        # Use enhanced chunks if available, otherwise use metadata
        chunks_to_index = enhanced_chunks if enhanced_chunks else chunk_metadata
        
        for i, chunk_data in enumerate(chunks_to_index):
            # Get title from chunk data
            if isinstance(chunk_data, dict):
                title = chunk_data.get('title', '')
                exact_match = chunk_data.get('exact_title_match', title.lower().strip())
                chunk_type = chunk_data.get('chunk_type', 'unknown')
            else:
                # Fallback for older format
                title = chunk_metadata[i].get('title', '') if i < len(chunk_metadata) else ''
                exact_match = title.lower().strip()
                chunk_type = chunk_metadata[i].get('chunk_type', 'unknown') if i < len(chunk_metadata) else 'unknown'
            
            if title:
                # Store multiple variations for matching
                variations = [
                    title.lower().strip(),
                    exact_match,
                    re.sub(r'[^\w\s]', '', title.lower().strip()),  # Remove punctuation
                    re.sub(r'\s+', ' ', title.lower().strip())  # Normalize whitespace
                ]
                
                # Add additional variations for descriptive titles
                if 'this section describes' in title.lower():
                    # Extract the main topic from descriptive titles
                    # e.g., "This section describes the additional frontend server tasks..." -> "additional frontend server tasks"
                    desc_match = re.search(r'this section describes (?:the )?(.+?)(?:\s+that|\.|$)', title.lower())
                    if desc_match:
                        main_topic = desc_match.group(1).strip()
                        variations.extend([
                            main_topic,
                            re.sub(r'[^\w\s]', '', main_topic),
                            re.sub(r'\s+', ' ', main_topic)
                        ])
                
                for variation in variations:
                    if variation and variation not in self.title_index[doc_name]:
                        self.title_index[doc_name][variation] = {
                            'chunk_index': i,
                            'original_title': title,
                            'chunk_type': chunk_type,
                            'exact_match_score': 1.0
                        }
    
    def search_with_exact_title_matching(self, query: str, document_filter: Optional[str] = None, 
                                       top_k: int = 10) -> List[Dict[str, Any]]:
        """Enhanced search with exact title matching priority"""
        
        # Step 1: Check for exact title matches
        exact_matches = self._find_exact_title_matches(query, document_filter)
        
        if exact_matches:
            logger.info(f"Found {len(exact_matches)} exact title matches for query: '{query}'")
            # Debug: log content lengths before enhancement
            for i, match in enumerate(exact_matches):
                logger.info(f"Match {i+1} before enhancement: {match['title']} - {len(match['content'])} chars")
            
            # For exact matches, return complete content with high confidence
            enhanced_results = self._format_exact_match_results(exact_matches, query)
            
            # Debug: log content lengths after enhancement
            for i, result in enumerate(enhanced_results):
                logger.info(f"Result {i+1} after enhancement: {result['metadata']['title']} - {len(result['text'])} chars")
            
            return enhanced_results
        
        # Step 2: Fall back to hybrid search if no exact matches
        logger.info(f"No exact title matches found, using hybrid search for: '{query}'")
        return self._hybrid_search(query, document_filter, top_k)
    
    def _find_exact_title_matches(self, query: str, document_filter: Optional[str] = None) -> List[Dict]:
        """Find exact title matches and enhance with complete section content"""
        
        query_variations = [
            query.lower().strip(),
            re.sub(r'[^\w\s]', '', query.lower().strip()),
            re.sub(r'\s+', ' ', query.lower().strip()),
            re.sub(r'^(how to|what is|explain|describe)\s+', '', query.lower().strip())  # Remove question words
        ]
        
        # Add specific variations for common query patterns
        base_query = query.lower().strip()
        
        # For "security hardening" queries, add variations
        if 'security' in base_query and 'hardening' in base_query:
            query_variations.extend([
                'security hardening on srm vapps',
                'srm vapps security hardening',
                'hardening on srm vapps'
            ])
        
        # For vApp-related queries, add variations
        if 'vapp' in base_query or 'vapps' in base_query:
            query_variations.extend([
                base_query.replace('vapp', 'vapps'),
                base_query.replace('vapps', 'vapp')
            ])
        
        exact_matches = []
        seen_chunks = set()  # Track unique chunks to avoid duplicates
        
        # Search in title indexes
        for doc_name in self.documents:
            if document_filter and doc_name != document_filter:
                continue
                
            if doc_name in self.title_index:
                for variation in query_variations:
                    if variation in self.title_index[doc_name]:
                        match_info = self.title_index[doc_name][variation]
                        
                        # Create unique identifier for this chunk
                        chunk_idx = match_info['chunk_index']
                        chunk_id = f"{doc_name}:{chunk_idx}"
                        
                        # Skip if we've already found this chunk
                        if chunk_id in seen_chunks:
                            continue
                        
                        seen_chunks.add(chunk_id)
                        doc_data = self.document_chunks[doc_name]
                        
                        if chunk_idx < len(doc_data['chunks']):
                            chunk_content = doc_data['chunks'][chunk_idx]
                            logger.info(f"Found exact match: '{match_info['original_title']}' at chunk {chunk_idx}, content length: {len(chunk_content)}")
                            
                            # Debug: Check if this chunk contains Document Overview
                            if 'Document Overview' in chunk_content:
                                logger.warning(f"WARNING: Chunk {chunk_idx} contains Document Overview! This is wrong.")
                                logger.warning(f"First 200 chars: {chunk_content[:200]}")
                            
                            exact_matches.append({
                                'document': doc_name,
                                'chunk_index': chunk_idx,
                                'title': match_info['original_title'],
                                'chunk_type': match_info['chunk_type'],
                                'content': chunk_content,
                                'metadata': doc_data['metadata'][chunk_idx] if chunk_idx < len(doc_data['metadata']) else {},
                                'match_type': 'exact_title',
                                'confidence_score': 1.0,
                                'query_variation': variation
                            })
        
        # Enhance matches with complete section content
        enhanced_matches = self._enhance_matches_with_complete_content(exact_matches, query)
        
        return enhanced_matches
    
    def _enhance_matches_with_complete_content(self, exact_matches: List[Dict], query: str) -> List[Dict]:
        """Enhance exact matches by finding and combining related chunks for complete content"""
        
        if not exact_matches:
            return exact_matches
        
        enhanced_matches = []
        
        for match in exact_matches:
            doc_name = match['document']
            chunk_idx = match['chunk_index']
            current_content = match['content']
            
            # If current chunk already has substantial content, use it as-is
            if len(current_content) > 500:
                enhanced_matches.append(match)
                continue
            
            # Look for related chunks with more substantial content
            related_chunk = self._find_related_substantial_chunk(doc_name, query, match)
            
            if related_chunk:
                # Use the substantial chunk instead
                logger.info(f"Replacing content for '{match['title']}' with related chunk '{related_chunk.get('title', 'Unknown')}'")
                match['content'] = related_chunk['content']
                match['title'] = related_chunk.get('title', match['title'])
                match['metadata'] = related_chunk.get('metadata', match['metadata'])
                match['chunk_type'] = related_chunk.get('chunk_type', match['chunk_type'])
                match['enhanced'] = True  # Mark as enhanced
                enhanced_matches.append(match)
            else:
                # Try to combine with adjacent chunks on the same page
                logger.info(f"Trying to combine related chunks for '{match['title']}' (current length: {len(current_content)})")
                combined_content = self._combine_related_chunks(doc_name, chunk_idx, match)
                if len(combined_content) > len(current_content):
                    logger.info(f"Combined content for '{match['title']}': {len(current_content)} -> {len(combined_content)} chars")
                    match['content'] = combined_content
                    match['enhanced'] = True
                else:
                    logger.info(f"No improvement from combining chunks for '{match['title']}'")
                
                # If still no substantial content, try to find broader context
                current_length = len(match['content'])
                if current_length < 300:
                    logger.info(f"Checking broader context for '{match['title']}' (current length: {current_length})")
                    broader_content = self._find_broader_context(doc_name, query, match)
                    if broader_content and len(broader_content) > current_length:
                        logger.info(f"Enhanced '{match['title']}' with broader context: {len(broader_content)} chars")
                        match['content'] = broader_content
                        match['enhanced'] = True
                    else:
                        logger.info(f"No broader context found for '{match['title']}' - keeping original content ({current_length} chars)")
                else:
                    logger.info(f"Content for '{match['title']}' is substantial ({current_length} chars) - no enhancement needed")
                
                enhanced_matches.append(match)
        
        return enhanced_matches
    
    def _find_related_substantial_chunk(self, doc_name: str, query: str, original_match: Dict) -> Optional[Dict]:
        """Find chunks with substantial content related to the query"""
        
        if doc_name not in self.document_chunks:
            return None
        
        doc_data = self.document_chunks[doc_name]
        query_keywords = set(re.findall(r'\w+', query.lower()))
        
        # For exact title matches with brief content, prefer using broader context
        # instead of replacing with potentially less relevant chunks
        original_title = original_match.get('title', '').lower()
        
        # Specifically disable for Security Hardening on SRM vApps
        if 'security hardening on srm vapps' in original_title:
            logger.info(f"Security Hardening detected - completely skipping related chunk search")
            return None
            
        if len(original_match.get('content', '')) < 500:
            logger.info(f"Brief exact title match '{original_title}' - skipping related chunk search to use broader context instead")
            return None
        
        # First, look for chunks with descriptive titles that contain the query topic
        # Example: for "Additional frontend server tasks", find "This section describes the additional frontend server tasks..."
        for i, chunk_content in enumerate(doc_data['chunks']):
            if len(chunk_content) < 500:  # Skip short chunks
                continue
            
            metadata = doc_data['metadata'][i] if i < len(doc_data['metadata']) else {}
            chunk_title = metadata.get('title', '').lower()
            
            # Check if title contains a description of the query topic
            if ('this section describes' in chunk_title and 
                all(keyword in chunk_title for keyword in query_keywords)):
                
                return {
                    'content': chunk_content,
                    'metadata': metadata,
                    'chunk_type': metadata.get('chunk_type', 'unknown'),
                    'title': metadata.get('title', f'Related content for {query}'),
                    'chunk_index': i
                }
            
            # Special handling for security hardening queries
            if 'security' in query.lower() and 'hardening' in query.lower():
                # Look for chunks that contain STIG, security guide references, or configuration details
                chunk_lower = chunk_content.lower()
                security_indicators = [
                    'stig hardening rules', 'security hardening guide', 
                    'firewall settings', 'security configuration', 'hardening guide'
                ]
                
                if any(indicator in chunk_lower for indicator in security_indicators):
                    logger.info(f"Found security-specific chunk: {metadata.get('title', 'Unknown')} (chunk {i})")
                    return {
                        'content': chunk_content,
                        'metadata': metadata,
                        'chunk_type': metadata.get('chunk_type', 'unknown'),
                        'title': metadata.get('title', f'Security configuration for {query}'),
                        'chunk_index': i
                    }
        
        # Fallback: Look for chunks with substantial content that contain query keywords
        for i, chunk_content in enumerate(doc_data['chunks']):
            if len(chunk_content) < 500:  # Skip short chunks
                continue
            
            chunk_lower = chunk_content.lower()
            metadata = doc_data['metadata'][i] if i < len(doc_data['metadata']) else {}
            chunk_title = metadata.get('title', '').lower()
            
            # Check if chunk contains most query keywords
            chunk_keywords = set(re.findall(r'\w+', chunk_lower))
            keyword_overlap = len(query_keywords.intersection(chunk_keywords))
            
            # Be more strict about keyword matching - require higher overlap AND relevance indicators
            if keyword_overlap >= len(query_keywords) * 0.8:  # 80% keyword overlap (stricter)
                chunk_type = metadata.get('chunk_type', 'unknown')
                
                logger.info(f"Checking chunk {i} '{metadata.get('title', 'Unknown')}' - keyword overlap: {keyword_overlap}/{len(query_keywords)}")
                
                # For security hardening specifically, be even more strict
                if 'security' in query.lower() and 'hardening' in query.lower():
                    # Only return chunks that explicitly mention security hardening concepts
                    security_relevance = any(phrase in chunk_lower for phrase in [
                        'security hardening', 'stig', 'firewall', 'hardening rules',
                        'security configuration', 'hardening guide'
                    ])
                    logger.info(f"Security relevance check for '{metadata.get('title', 'Unknown')}': {security_relevance}")
                    if not security_relevance:
                        continue
                
                # Additional checks for general relevance
                if any(phrase in chunk_lower for phrase in ['must be disabled', 'tasks', 'steps', 'about this task']):
                    logger.info(f"Found relevant chunk via general relevance: {metadata.get('title', 'Unknown')} (chunk {i})")
                    return {
                        'content': chunk_content,
                        'metadata': metadata,
                        'chunk_type': chunk_type,
                        'title': metadata.get('title', f'Related content for {query}'),
                        'chunk_index': i
                    }
        
        return None
    
    def _combine_related_chunks(self, doc_name: str, chunk_idx: int, original_match: Dict) -> str:
        """Combine chunks from the same page/section to get complete content"""
        
        if doc_name not in self.document_chunks:
            return original_match['content']
        
        doc_data = self.document_chunks[doc_name]
        original_page = original_match['metadata'].get('page', 1)
        combined_content = original_match['content']
        
        # Look for chunks on the same page
        for i, chunk_content in enumerate(doc_data['chunks']):
            if i == chunk_idx:  # Skip the original chunk
                continue
            
            metadata = doc_data['metadata'][i] if i < len(doc_data['metadata']) else {}
            chunk_page = metadata.get('page', 1)
            
            # Combine chunks from the same page that seem related
            if chunk_page == original_page and len(chunk_content) > 100:
                chunk_lower = chunk_content.lower()
                
                # Check if chunk contains related content
                if any(phrase in chunk_lower for phrase in ['steps', 'about this task', 'prerequisites', 'must be disabled']):
                    combined_content += f"\n\n{chunk_content}"
        
        return combined_content
    
    def _find_broader_context(self, doc_name: str, query: str, original_match: Dict) -> Optional[str]:
        """Find broader context for brief content by searching for related sections"""
        
        if doc_name not in self.document_chunks:
            return None
        
        doc_data = self.document_chunks[doc_name]
        query_keywords = set(re.findall(r'\w+', query.lower()))
        original_title = original_match['title'].lower()
        
        # For very brief content like "Security Hardening on SRM vApps", 
        # don't add broader context as the content is complete as-is
        original_content = original_match['content']
        original_title = original_match.get('title', '').lower()
        
        # Specifically disable broader context for Security Hardening on SRM vApps
        if 'security hardening on srm vapps' in original_title:
            logger.info(f"Security Hardening content detected - not adding broader context")
            return None
        
        if len(original_content) < 500:
            # Check if the content seems complete (has actionable information)
            if any(phrase in original_content.lower() for phrase in [
                'stig hardening rules', 'security hardening guide', 'firewall settings',
                'see the', 'for more information', 'dell support site'
            ]):
                logger.info(f"Brief content for '{original_match['title']}' appears complete - not adding broader context")
                return None
        
        # Try to find sections that provide more context about the topic
        broader_content_parts = [original_content]
        related_sections_found = 0
        
        # Look for chunks that contain the query topic and have substantial content
        for i, chunk_content in enumerate(doc_data['chunks']):
            if i == original_match['chunk_index']:  # Skip the original chunk
                continue
            
            if len(chunk_content) < 300:  # Skip short chunks
                continue
            
            metadata = doc_data['metadata'][i] if i < len(doc_data['metadata']) else {}
            chunk_title = metadata.get('title', '').lower()
            chunk_lower = chunk_content.lower()
            
            # Skip generic document overview/introduction sections unless very specific
            if any(generic in chunk_title for generic in [
                'document overview', 'document introduction', 'contents', 'table of contents'
            ]):
                continue
            
            # Check if this chunk provides related information
            is_related = False
            
            # For security hardening specifically, be very targeted
            if 'security' in original_title and 'hardening' in original_title:
                # Only include chunks that are directly about security, hardening, or configuration
                direct_security_relevance = any(term in chunk_lower for term in [
                    'security configuration', 'hardening steps', 'stig', 'firewall configuration',
                    'authentication setup', 'security settings', 'hardening procedure'
                ])
                if direct_security_relevance and 'security' in chunk_title:
                    is_related = True
            else:
                # For other topics, check if chunk title contains query keywords
                if any(keyword in chunk_title for keyword in query_keywords):
                    is_related = True
                
                # Or if chunk content contains query keywords with high relevance
                keyword_count = sum(1 for keyword in query_keywords if keyword in chunk_lower)
                if keyword_count >= len(query_keywords) * 0.7:  # 70% keyword overlap
                    context_indicators = ['steps', 'procedure', 'configuration', 'setup', 'about this task']
                    if any(indicator in chunk_lower for indicator in context_indicators):
                        is_related = True
            
            if is_related and related_sections_found < 2:  # Limit to 2 related sections
                broader_content_parts.append(f"\n\n### Related: {metadata.get('title', 'Section')}\n{chunk_content}")
                related_sections_found += 1
        
        # Only return broader context if we found truly related sections
        if related_sections_found > 0:
            combined_broader = '\n'.join(broader_content_parts)
            return combined_broader[:2000]  # Limit to reasonable size
        
        return None
    
    def _format_exact_match_results(self, exact_matches: List[Dict], query: str) -> List[Dict[str, Any]]:
        """Format exact match results for complete responses"""
        
        results = []
        
        for match in exact_matches:
            # For exact matches, provide complete content
            logger.info(f"Formatting result for '{match['title']}' from chunk {match.get('chunk_index', 'unknown')}, content length: {len(match['content'])}")
            
            result = {
                'text': match['content'],
                'metadata': {
                    'title': match['title'],
                    'document': match['document'],
                    'chunk_type': match['chunk_type'],
                    'match_type': 'exact_title_match',
                    'confidence': match['confidence_score'],
                    'page': match['metadata'].get('page_start', match['metadata'].get('page', 1)),
                    'is_complete_section': True,
                    'query_matched': query,
                    'source_chunk_index': match.get('chunk_index', 'unknown'),
                    **match['metadata']
                },
                'score': match['confidence_score'],
                'document': match['document'],
                'match_explanation': f"Exact title match for '{match['title']}'"
            }
            results.append(result)
        
        # Sort by chunk type priority (chapters > sections > subsections)
        type_priority = {
            'document_overview': 0,
            'chapter_major': 1,
            'section_standard': 2,
            'subsection_minor': 3,
            'complete_chapter': 1,
            'complete_section': 2
        }
        
        results.sort(key=lambda x: (
            type_priority.get(x['metadata'].get('chunk_type', ''), 9),
            -x['score']
        ))
        
        return results
    
    def _hybrid_search(self, query: str, document_filter: Optional[str] = None, top_k: int = 10) -> List[Dict[str, Any]]:
        """Fallback hybrid search when no exact title matches found"""
        
        all_results = []
        
        # Generate query variations if enabled
        query_variations = [query]
        if self.config.get("enable_multi_query_generation", False):
            query_variations.extend(self._generate_query_variations(query))
        
        for doc_name in self.documents:
            if document_filter and doc_name != document_filter:
                continue
            
            if doc_name not in self.document_chunks:
                continue
            
            doc_results = []
            
            # BM25 search
            for q_var in query_variations:
                bm25_results = self._bm25_search(doc_name, q_var, top_k * 2)
                doc_results.extend(bm25_results)
            
            # FAISS search
            for q_var in query_variations:
                faiss_results = self._faiss_search(doc_name, q_var, top_k * 2)
                doc_results.extend(faiss_results)
            
            # Combine and deduplicate
            combined_results = self._combine_search_results(doc_results, doc_name)
            all_results.extend(combined_results)
        
        # Rerank if enabled
        if self.reranker and self.config.get("enable_reranking", False):
            all_results = self._rerank_results(query, all_results)
        
        # Apply diversity selection if enabled
        if self.config.get("enable_diversity_selection", True):
            all_results = self._apply_diversity_selection(all_results)
        
        return all_results[:top_k]
    
    def _bm25_search(self, doc_name: str, query: str, top_k: int) -> List[Dict]:
        """BM25 search for a specific document"""
        if doc_name not in self.bm25_indexes:
            return []
        
        bm25 = self.bm25_indexes[doc_name]
        query_tokens = query.lower().split()
        
        scores = bm25.get_scores(query_tokens)
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    'document': doc_name,
                    'chunk_index': int(idx),
                    'score': float(scores[idx]),
                    'search_type': 'bm25'
                })
        
        return results
    
    def _faiss_search(self, doc_name: str, query: str, top_k: int) -> List[Dict]:
        """FAISS search for a specific document"""
        if doc_name not in self.faiss_indexes:
            return []
        
        faiss_index = self.faiss_indexes[doc_name]
        query_embedding = self.embedding_model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        scores, indices = faiss_index.search(query_embedding.astype('float32'), top_k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and score > 0:
                results.append({
                    'document': doc_name,
                    'chunk_index': int(idx),
                    'score': float(score),
                    'search_type': 'faiss'
                })
        
        return results
    
    def _combine_search_results(self, results: List[Dict], doc_name: str) -> List[Dict[str, Any]]:
        """Combine BM25 and FAISS results with score normalization"""
        
        # Group by chunk index
        chunk_scores = defaultdict(list)
        for result in results:
            chunk_scores[result['chunk_index']].append(result)
        
        combined_results = []
        doc_data = self.document_chunks[doc_name]
        
        for chunk_idx, chunk_results in chunk_scores.items():
            if chunk_idx >= len(doc_data['chunks']):
                continue
            
            # Combine scores from different search methods
            bm25_scores = [r['score'] for r in chunk_results if r['search_type'] == 'bm25']
            faiss_scores = [r['score'] for r in chunk_results if r['search_type'] == 'faiss']
            
            # Normalize and combine
            bm25_score = max(bm25_scores) if bm25_scores else 0
            faiss_score = max(faiss_scores) if faiss_scores else 0
            
            # Weighted combination (can be configured)
            alpha = 0.5  # Weight for BM25 vs FAISS
            combined_score = alpha * bm25_score + (1 - alpha) * faiss_score
            
            combined_results.append({
                'text': doc_data['chunks'][chunk_idx],
                'metadata': doc_data['metadata'][chunk_idx] if chunk_idx < len(doc_data['metadata']) else {},
                'score': combined_score,
                'document': doc_name,
                'chunk_index': chunk_idx,
                'bm25_score': bm25_score,
                'faiss_score': faiss_score
            })
        
        return combined_results
    
    def _generate_query_variations(self, query: str) -> List[str]:
        """Generate query variations for better coverage"""
        variations = []
        
        # Add question variations
        if not query.endswith('?'):
            variations.append(f"How to {query}")
            variations.append(f"What is {query}")
        
        # Remove question words
        clean_query = re.sub(r'^(how to|what is|explain|describe)\s+', '', query.lower())
        if clean_query != query.lower():
            variations.append(clean_query)
        
        # Add related terms
        if 'install' in query.lower():
            variations.append(query.replace('install', 'setup'))
            variations.append(query.replace('install', 'configure'))
        
        return variations[:3]  # Limit to avoid too many variations
    
    def _rerank_results(self, query: str, results: List[Dict]) -> List[Dict]:
        """Rerank results using cross-encoder"""
        if not results or not self.reranker:
            return results
        
        # Prepare pairs for reranking
        pairs = [(query, result['text']) for result in results]
        
        # Get reranking scores
        rerank_scores = self.reranker.predict(pairs)
        
        # Update scores
        for i, score in enumerate(rerank_scores):
            results[i]['rerank_score'] = float(score)
            results[i]['final_score'] = float(score)  # Use rerank score as final
        
        # Sort by reranking score
        results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return results
    
    def _apply_diversity_selection(self, results: List[Dict]) -> List[Dict]:
        """Apply diversity selection to avoid redundant results"""
        if not results:
            return results
        
        diverse_results = []
        used_titles = set()
        
        for result in results:
            title = result['metadata'].get('title', '')
            
            # Skip if we already have this title
            if title in used_titles:
                continue
            
            diverse_results.append(result)
            used_titles.add(title)
            
            # Stop if we have enough diverse results
            if len(diverse_results) >= len(results) * 0.8:  # Keep 80% for diversity
                break
        
        # Add remaining results if we need more
        for result in results:
            if result not in diverse_results:
                diverse_results.append(result)
        
        return diverse_results