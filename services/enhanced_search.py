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

        # Load models based on config with CPU optimizations
        embedding_model_name = config.get("embedding_model", "all-MiniLM-L6-v2")
        logger.info(f"Loading embedding model for CPU: {embedding_model_name}")

        # Optimize for CPU-only systems
        self.embedding_model = SentenceTransformer(embedding_model_name)
        self.embedding_model._target_device = 'cpu'  # Force CPU usage

        # Set smaller batch size for low-spec systems
        batch_size = config.get("batch_size", 32)
        if hasattr(self.embedding_model, 'encode'):
            # Store original encode method and create optimized version
            self._original_encode = self.embedding_model.encode
            self.embedding_model.encode = lambda *args, **kwargs: self._cpu_optimized_encode(*args, **kwargs, batch_size=batch_size)

        # Load reranker only if reranking is enabled
        self.reranker = None
        if config.get("enable_reranking", False):
            reranker_model = config.get("reranker_model", "cross-encoder/ms-marco-MiniLM-L-2-v2")
            logger.info(f"Loading lightweight reranker model: {reranker_model}")
            self.reranker = CrossEncoder(reranker_model)
            # Force CPU usage for reranker
            if hasattr(self.reranker.model, 'to'):
                self.reranker.model.to('cpu')
        
        # Load enhanced document data
        self.documents = self._discover_enhanced_documents()
        self.bm25_indexes = {}
        self.faiss_indexes = {}
        self.document_chunks = {}
        self.title_index = {}  # New: exact title matching index
        
        # Initialize enhanced indexes
        self._load_enhanced_indexes()

    def _cpu_optimized_encode(self, sentences, batch_size=16, **kwargs):
        """CPU-optimized encoding with smaller batches for low-spec systems"""
        import torch

        # Ensure we're using CPU
        kwargs['device'] = 'cpu'
        kwargs['batch_size'] = batch_size

        # Disable gradient computation for inference
        with torch.no_grad():
            return self._original_encode(sentences, **kwargs)
    
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
        hybrid_results = self._hybrid_search(query, document_filter, top_k)

        # Step 3: Apply precision enhancement for better ranking
        enhanced_results = self._enhance_search_precision(query, hybrid_results)

        return enhanced_results
    
    def _find_exact_title_matches(self, query: str, document_filter: Optional[str] = None) -> List[Dict]:
        """Find exact title matches and enhance with complete section content"""

        # Start with basic variations
        query_variations = [
            query.lower().strip(),
            re.sub(r'[^\w\s]', '', query.lower().strip()),
            re.sub(r'\s+', ' ', query.lower().strip())
        ]

        # Enhanced question-to-statement transformation
        base_query = query.lower().strip()

        # Transform questions to procedural titles
        question_transforms = self._generate_question_transforms(base_query)
        query_variations.extend(question_transforms)

        # Add specific variations for common query patterns
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

    def _generate_question_transforms(self, query: str) -> List[str]:
        """Transform questions into procedural title formats to match documentation"""
        transforms = []
        query_clean = query.strip()

        # Remove common question words and transform to procedural form
        basic_clean = re.sub(r'^(how to|how do i|what is|explain|describe)\s+', '', query_clean, flags=re.IGNORECASE)
        if basic_clean != query_clean:
            transforms.append(basic_clean)

        # Transform specific question patterns to procedural titles
        # Pattern: "how to [verb] [object]" -> "[verb]ing [object]"
        how_to_match = re.match(r'^how\s+to\s+(\w+)\s+(.+)', query_clean, re.IGNORECASE)
        if how_to_match:
            verb, obj = how_to_match.groups()
            verb_lower = verb.lower()

            # Common verb transformations for procedural titles
            verb_transforms = {
                'restart': ['restarting', 'restart'],
                'start': ['starting', 'start'],
                'stop': ['stopping', 'stop'],
                'configure': ['configuring', 'configure'],
                'install': ['installing', 'install'],
                'setup': ['setting up', 'setup'],
                'enable': ['enabling', 'enable'],
                'disable': ['disabling', 'disable'],
                'create': ['creating', 'create'],
                'delete': ['deleting', 'delete'],
                'update': ['updating', 'update'],
                'upgrade': ['upgrading', 'upgrade'],
                'deploy': ['deploying', 'deploy'],
                'manage': ['managing', 'manage'],
                'troubleshoot': ['troubleshooting', 'troubleshoot']
            }

            if verb_lower in verb_transforms:
                for verb_form in verb_transforms[verb_lower]:
                    transforms.append(f"{verb_form} {obj}")
                    transforms.append(f"{verb_form} the {obj}")

        # Pattern: "how do i [verb] [object]" -> same transformation as above
        how_do_match = re.match(r'^how\s+do\s+i\s+(\w+)\s+(.+)', query_clean, re.IGNORECASE)
        if how_do_match:
            verb, obj = how_do_match.groups()
            verb_lower = verb.lower()

            # Reuse the same verb_transforms dictionary
            verb_transforms = {
                'restart': ['restarting', 'restart'],
                'start': ['starting', 'start'],
                'stop': ['stopping', 'stop'],
                'configure': ['configuring', 'configure'],
                'install': ['installing', 'install'],
                'setup': ['setting up', 'setup'],
                'enable': ['enabling', 'enable'],
                'disable': ['disabling', 'disable'],
                'create': ['creating', 'create'],
                'delete': ['deleting', 'delete'],
                'update': ['updating', 'update'],
                'upgrade': ['upgrading', 'upgrade'],
                'deploy': ['deploying', 'deploy'],
                'manage': ['managing', 'manage'],
                'troubleshoot': ['troubleshooting', 'troubleshoot']
            }

            if verb_lower in verb_transforms:
                for verb_form in verb_transforms[verb_lower]:
                    transforms.append(f"{verb_form} {obj}")
                    transforms.append(f"{verb_form} the {obj}")

        # Specific transformations for common technical terms
        # SMI-S provider variations
        if 'smi-s' in query_clean.lower() or 'smis' in query_clean.lower():
            if 'restart' in query_clean.lower():
                transforms.extend([
                    'restarting the smi-s provider',
                    'restart the smi-s provider',
                    'restarting smi-s provider',
                    'restart smi-s provider',
                    'restarting the smis provider',
                    'restart the smis provider'
                ])

        # Solution Pack variations
        if 'solution' in query_clean.lower() and 'pack' in query_clean.lower():
            if 'install' in query_clean.lower():
                transforms.extend([
                    'installing solutionpacks',
                    'install solutionpacks',
                    'installing the solutionpack',
                    'install the solutionpack',
                    'solutionpack installation'
                ])

        # Frontend server variations
        if 'frontend' in query_clean.lower() and 'server' in query_clean.lower():
            if 'deploy' in query_clean.lower() or 'add' in query_clean.lower():
                transforms.extend([
                    'deploying additional frontend servers',
                    'additional frontend server deployment',
                    'adding frontend servers',
                    'frontend server configuration'
                ])

        # Database variations
        if 'database' in query_clean.lower() and ('mysql' in query_clean.lower() or 'grant' in query_clean.lower()):
            transforms.extend([
                'adding mysql grants to the databases',
                'mysql grants to databases',
                'database grants configuration'
            ])

        # Remove duplicates and return
        unique_transforms = []
        seen = set()
        for transform in transforms:
            if transform.lower() not in seen and len(transform.strip()) > 3:
                seen.add(transform.lower())
                unique_transforms.append(transform.lower())

        logger.info(f"Generated {len(unique_transforms)} question transforms for '{query}': {unique_transforms[:5]}...")
        return unique_transforms

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
        
        # For content that already appears complete (has actionable information), don't combine
        original_content = original_match['content']
        original_title = original_match.get('title', '').lower()
        
        # Check if content already seems complete
        if any(phrase in original_content.lower() for phrase in [
            'for more information', 'see the', 'dell support site', 'stig hardening rules',
            'security hardening guide', 'firewall settings'
        ]):
            logger.info(f"Content for '{original_match['title']}' appears complete - not combining with other chunks")
            return original_content
        
        # Specifically avoid combining for Security Hardening
        if 'security hardening' in original_title:
            logger.info(f"Security Hardening content - not combining chunks")
            return original_content
        
        # For exact title matches that are already substantial, don't combine with other chunks
        # This prevents mixing different sections that happen to be on the same page
        if len(original_content) > 300 and 'exact_title' in original_match.get('match_type', ''):
            logger.info(f"Exact title match with substantial content ({len(original_content)} chars) - not combining chunks to preserve precision")
            return original_content
        
        # Check if this is a self-contained section that shouldn't be combined with others
        if self._is_self_contained_section(original_match):
            logger.info(f"Self-contained section '{original_title}' - not combining chunks to preserve precision")
            return original_content
        
        doc_data = self.document_chunks[doc_name]
        original_page = original_match['metadata'].get('page', 1)
        combined_content = original_content
        
        # Look for chunks on the same page that are truly related procedural content
        for i, chunk_content in enumerate(doc_data['chunks']):
            if i == chunk_idx:  # Skip the original chunk
                continue
            
            metadata = doc_data['metadata'][i] if i < len(doc_data['metadata']) else {}
            chunk_page = metadata.get('page', 1)
            chunk_title = metadata.get('title', '').lower()
            
            # Only combine chunks from the same page that have procedural content
            if chunk_page == original_page and len(chunk_content) > 100:
                chunk_lower = chunk_content.lower()
                
                # Skip generic overview/introduction sections
                if any(generic in chunk_title for generic in [
                    'document overview', 'document introduction', 'contents'
                ]):
                    continue
                
                # Check if this chunk is unrelated to the original section
                if self._are_sections_unrelated(original_match, chunk_title, chunk_content):
                    logger.info(f"Skipping unrelated section '{chunk_title}' on same page")
                    continue
                
                # Only combine if it's truly related procedural content
                if any(phrase in chunk_lower for phrase in [
                    'steps', 'about this task', 'prerequisites', 'must be disabled',
                    'procedure', 'configuration steps'
                ]):
                    # Additional check: make sure it's not just a bullet point list
                    if len(chunk_content) > 500:  # Substantial procedural content
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
        
        # Check if this is a self-contained section that shouldn't get broader context
        if self._is_self_contained_section(original_match):
            logger.info(f"Self-contained section '{original_title}' - not adding broader context to preserve precision")
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
            
            # Check if this chunk is unrelated to the original section
            if self._are_sections_unrelated(original_match, chunk_title, chunk_content):
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
    
    def _improve_content_formatting(self, content: str) -> str:
        """Improve content formatting, especially for command outputs and tables"""
        
        import re
        
        # Find and format code blocks that contain command output
        code_block_pattern = r'```\n(.*?)\n```'
        
        def format_code_block(match):
            code_content = match.group(1)
            return "```\n" + self._format_command_block(code_content) + "\n```"
        
        # Replace code blocks with formatted versions
        formatted_content = re.sub(code_block_pattern, format_code_block, content, flags=re.DOTALL)
        
        # Format markdown tables for better display
        formatted_content = self._format_markdown_tables(formatted_content)
        
        return formatted_content
    
    def _format_command_block(self, code_content: str) -> str:
        """Format content within code blocks"""
        
        import re
        
        # If this looks like manage-modules.sh output, format it
        if 'manage-modules.sh' in code_content:
            return self._format_manage_modules_output(code_content)
        
        # For other command outputs, apply basic formatting
        return self._apply_basic_command_formatting(code_content)
    
    def _format_manage_modules_output(self, content: str) -> str:
        """Format manage-modules.sh command output"""
        
        import re
        lines = []
        
        # Split content into logical sections
        sections = content.split('lppa028:~ #')
        
        for i, section in enumerate(sections):
            section = section.strip()
            if not section:
                continue
            
            if i == 0:
                # First section might not have the prompt
                lines.append(f"lppa028:~ # {section}")
            else:
                # This section starts after a prompt
                if 'manage-modules.sh list installed' in section:
                    lines.append("lppa028:~ # manage-modules.sh list installed")
                    lines.append("")
                    lines.append("Installed Modules:")
                    lines.append("")
                    lines.append("Identifier                        Instance                     Category")
                    lines.append("--------------------              ------------                 ---------------")
                    
                    # Extract and format module entries
                    module_pattern = r'\*([a-zA-Z0-9-]+)\s+([a-zA-Z0-9.-]+)\s*:\s*([a-zA-Z-]+)'
                    modules = re.findall(module_pattern, section)
                    
                    for identifier, instance, category in modules:
                        line = f"*{identifier:<32} {instance:<24} : {category}"
                        lines.append(line)
                    
                    lines.append("")
                    
                elif 'manage-modules.sh service status all' in section:
                    lines.append("lppa028:~ # manage-modules.sh service status all")
                    lines.append("")
                    
                    # Extract and format status entries
                    status_pattern = r'\*Checking \'([^\']+)\'\.\.\.\s*\[\s*([^\]]+)\s*\]'
                    statuses = re.findall(status_pattern, section)
                    
                    for service, status in statuses:
                        lines.append(f"*Checking '{service}'... [{status.strip()}]")
                    
                    lines.append("")
                
                # Add the prompt at the end
                lines.append("lppa028:~ #")
        
        return "\n".join(lines)
    
    def _apply_basic_command_formatting(self, content: str) -> str:
        """Apply basic formatting to command output"""
        
        # Just clean up extra whitespace and ensure proper line breaks
        import re
        
        # Replace multiple spaces with single spaces
        content = re.sub(r' +', ' ', content)
        
        # Ensure proper line breaks around prompts
        content = re.sub(r'([^#]+#)\s*([^#\n]+)', r'\1 \2\n', content)
        
        return content.strip()
    
    def _format_markdown_tables(self, content: str) -> str:
        """Format markdown tables for better display"""
        
        import re
        
        # Find markdown tables (lines starting and ending with |)
        lines = content.split('\n')
        formatted_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if this line starts a markdown table
            if line.startswith('|') and line.endswith('|') and line.count('|') >= 3:
                table_lines = []
                table_start = i
                
                # Collect all consecutive table lines
                while i < len(lines) and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
                    table_lines.append(lines[i].strip())
                    i += 1
                
                # Format the table
                if len(table_lines) >= 2:  # At least header and separator
                    formatted_table = self._format_table_rows(table_lines)
                    formatted_lines.extend(formatted_table)
                else:
                    # Not a proper table, add as-is
                    formatted_lines.extend(table_lines)
            else:
                formatted_lines.append(lines[i])
                i += 1
        
        return '\n'.join(formatted_lines)
    
    def _format_table_rows(self, table_lines: List[str]) -> List[str]:
        """Format table rows for better readability"""
        
        if len(table_lines) < 2:
            return table_lines
        
        # Parse the table
        rows = []
        for line in table_lines:
            # Split by | and clean up
            cells = [cell.strip() for cell in line.split('|')[1:-1]]  # Remove empty first/last
            rows.append(cells)
        
        # Identify header and data rows
        header = rows[0] if rows else []
        
        # Check if there's a separator row (contains mostly dashes)
        separator_idx = -1
        for i, row in enumerate(rows[1:], 1):
            if all(cell.replace('-', '').replace('|', '').strip() == '' for cell in row):
                separator_idx = i
                break
        
        if separator_idx > 0:
            data_rows = rows[separator_idx + 1:]
        else:
            # No separator found, treat all rows after header as data
            data_rows = rows[1:]
        
        if not header:
            return table_lines
        
        # Calculate column widths with better spacing
        col_widths = []
        all_rows = [header] + data_rows
        
        for col_idx in range(len(header)):
            max_width = 0
            for row in all_rows:
                if col_idx < len(row):
                    max_width = max(max_width, len(row[col_idx]))
            
            # Set minimum widths based on column type
            if col_idx == 0:  # First column (Configuration Name)
                min_width = 25
            else:  # Value columns
                min_width = 40
            
            col_widths.append(max(max_width, min_width))
        
        # Format the table
        formatted_table = []
        
        # Header
        header_row = "| " + " | ".join(header[i].ljust(col_widths[i]) for i in range(len(header))) + " |"
        formatted_table.append(header_row)
        
        # Separator
        separator = "|" + "|".join("-" * (width + 2) for width in col_widths) + "|"
        formatted_table.append(separator)
        
        # Data rows
        for row in data_rows:
            if row:  # Skip empty rows
                # Handle text wrapping for very long cells
                formatted_cells = []
                for i in range(len(header)):
                    cell_content = row[i] if i < len(row) else ""
                    
                    # If cell is very long, add some intelligent breaking
                    if len(cell_content) > col_widths[i] and col_widths[i] > 50:
                        # Try to break at word boundaries
                        words = cell_content.split()
                        if len(words) > 1:
                            # For very long cells, just truncate nicely
                            if len(cell_content) > 80:
                                cell_content = cell_content[:77] + "..."
                    
                    formatted_cells.append(cell_content.ljust(col_widths[i]))
                
                formatted_row = "| " + " | ".join(formatted_cells) + " |"
                formatted_table.append(formatted_row)
        
        return formatted_table
    
    def _convert_tables_to_plain_text(self, content: str) -> str:
        """Convert markdown tables to plain text format for better UI compatibility"""
        
        import re
        lines = content.split('\n')
        converted_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if this line starts a markdown table
            if line.startswith('|') and line.endswith('|') and line.count('|') >= 3:
                table_lines = []
                
                # Collect all consecutive table lines
                while i < len(lines) and lines[i].strip().startswith('|') and lines[i].strip().endswith('|'):
                    table_lines.append(lines[i].strip())
                    i += 1
                
                # Convert table to plain text format
                if len(table_lines) >= 2:
                    plain_table = self._table_to_plain_text(table_lines)
                    converted_lines.extend(plain_table)
                else:
                    converted_lines.extend(table_lines)
                
                # Don't increment i here since the while loop already did
                continue
            else:
                converted_lines.append(lines[i])
                i += 1
        
        # Clean up excessive empty lines around tables
        result = '\n'.join(converted_lines)
        
        # Remove multiple consecutive empty lines before and after tables
        import re
        result = re.sub(r'\n\n+(<table[^>]*>)', r'\n\1', result)
        result = re.sub(r'(</table>)\n\n+', r'\1\n', result)
        
        # Also remove empty lines right before table (more aggressive cleanup)
        result = re.sub(r'\n(<table[^>]*>)', r'\1', result)
        
        return result
    
    def _table_to_plain_text(self, table_lines: List[str]) -> List[str]:
        """Convert a markdown table to HTML table format"""
        
        # Parse the table
        rows = []
        for line in table_lines:
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            # Skip separator rows (contain only dashes and spaces)
            if not all(cell.replace('-', '').replace(' ', '') == '' for cell in cells):
                rows.append(cells)
        
        if len(rows) < 2:
            return table_lines
        
        header = rows[0]
        data_rows = rows[1:]
        
        # Create HTML table as a single compact line to avoid BR tag issues
        table_html = '<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%; margin: 5px 0;">'
        
        # Header
        table_html += '<thead><tr style="background-color: #f5f5f5; font-weight: bold;">'
        for cell in header:
            table_html += f'<th style="border: 1px solid #ddd; padding: 8px; text-align: left;">{cell}</th>'
        table_html += '</tr></thead>'
        
        # Body
        table_html += '<tbody>'
        for row in data_rows:
            table_html += '<tr>'
            for cell in row:
                table_html += f'<td style="border: 1px solid #ddd; padding: 8px; vertical-align: top;">{cell}</td>'
            table_html += '</tr>'
        table_html += '</tbody>'
        
        table_html += '</table>'
        
        return [table_html]
    
    def _format_exact_match_results(self, exact_matches: List[Dict], query: str) -> List[Dict[str, Any]]:
        """Format exact match results for complete responses"""
        
        results = []
        
        for match in exact_matches:
            # For exact matches, provide complete content
            logger.info(f"Formatting result for '{match['title']}' from chunk {match.get('chunk_index', 'unknown')}, content length: {len(match['content'])}")
            
            # Post-process content to improve formatting
            formatted_content = self._improve_content_formatting(match['content'])
            
            # For tables that might not render well as markdown, convert to plain text format
            formatted_content = self._convert_tables_to_plain_text(formatted_content)
            
            result = {
                'text': formatted_content,
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

        # Generate query variations if enabled (disabled in low mode for performance)
        query_variations = [query]
        if self.config.get("enable_multi_query_generation", False):
            query_variations.extend(self._generate_query_variations(query))

        # Process documents sequentially for low-spec systems (avoid memory spikes)
        max_concurrent = self.config.get("max_concurrent_searches", 1)

        for doc_name in self.documents:
            if document_filter and doc_name != document_filter:
                continue

            if doc_name not in self.document_chunks:
                continue

            doc_results = []

            # Use reduced top_k for low-spec systems
            search_top_k = min(self.config.get("top_k_bm25", 6), self.config.get("top_k_faiss", 6))

            # BM25 search - more lightweight, prioritize this
            for q_var in query_variations:
                bm25_results = self._bm25_search(doc_name, q_var, search_top_k)
                doc_results.extend(bm25_results)

            # FAISS search - more resource intensive
            for q_var in query_variations:
                faiss_results = self._faiss_search(doc_name, q_var, search_top_k)
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
        """Apply diversity selection to avoid redundant results and ensure document diversity"""
        if not results:
            return results

        # First apply document diversity if enabled
        if self.config.get("enable_document_diversity", False):
            results = self._apply_document_diversity(results)

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

    def _apply_document_diversity(self, results: List[Dict]) -> List[Dict]:
        """Ensure results come from multiple documents when possible"""
        if len(results) <= 2:
            return results

        logger.info(f"Applying document diversity to {len(results)} results")

        # Group results by document
        by_document = defaultdict(list)
        for result in results:
            doc_name = result.get('document', result.get('metadata', {}).get('document', 'unknown'))
            by_document[doc_name].append(result)

        # Log current distribution
        for doc_name, doc_results in by_document.items():
            logger.info(f"Document '{doc_name}': {len(doc_results)} results")

        if len(by_document) == 1:
            logger.info("All results from single document - keeping as is")
            return results

        # Take top results from each document to ensure diversity
        diverse_results = []
        max_per_doc = max(2, len(results) // len(by_document))  # At least 2 per doc

        # Sort documents by their best result score
        sorted_docs = sorted(by_document.items(),
                           key=lambda x: max(r.get('score', r.get('final_score', 0)) for r in x[1]),
                           reverse=True)

        # Take results from each document in round-robin fashion
        remaining_slots = len(results)
        for doc_name, doc_results in sorted_docs:
            if remaining_slots <= 0:
                break

            # Sort results within document by score
            doc_results.sort(key=lambda x: x.get('score', x.get('final_score', 0)), reverse=True)

            # Take up to max_per_doc from this document
            to_take = min(max_per_doc, len(doc_results), remaining_slots)
            diverse_results.extend(doc_results[:to_take])
            remaining_slots -= to_take

        # If we still have slots and any unused results, fill them
        if remaining_slots > 0:
            used_indices = set()
            for result in diverse_results:
                for doc_results in by_document.values():
                    if result in doc_results:
                        used_indices.add(id(result))

            for doc_results in by_document.values():
                for result in doc_results:
                    if remaining_slots <= 0:
                        break
                    if id(result) not in used_indices:
                        diverse_results.append(result)
                        remaining_slots -= 1

        # Sort final results by score
        diverse_results.sort(key=lambda x: x.get('score', x.get('final_score', 0)), reverse=True)

        # Log final distribution
        final_by_doc = defaultdict(int)
        for result in diverse_results:
            doc_name = result.get('document', result.get('metadata', {}).get('document', 'unknown'))
            final_by_doc[doc_name] += 1

        logger.info(f"Document diversity applied - final distribution:")
        for doc_name, count in final_by_doc.items():
            logger.info(f"  {doc_name}: {count} results")

        return diverse_results

    def _enhance_search_precision(self, query: str, results: List[Dict]) -> List[Dict]:
        """Enhance search precision by re-ranking results based on query-specific rules"""

        if not results:
            return results

        query_lower = query.lower().strip()
        enhanced_results = []

        logger.info(f"Enhancing search precision for query: '{query}'")

        for result in results:
            title = result.get('metadata', {}).get('title', '').lower()
            content = result.get('text', '').lower()
            original_score = result.get('final_score', result.get('score', 0.0))

            # Start with original score
            enhanced_score = original_score
            precision_adjustments = []

            # Apply specific enhancements for chargeback preprocessor queries
            if self._is_chargeback_manual_query(query_lower):
                enhanced_score, adjustments = self._apply_chargeback_manual_precision(
                    title, content, enhanced_score, query_lower
                )
                precision_adjustments.extend(adjustments)

            # Apply general precision rules
            enhanced_score, general_adjustments = self._apply_general_precision_rules(
                title, content, enhanced_score, query_lower
            )
            precision_adjustments.extend(general_adjustments)

            # Create enhanced result
            enhanced_result = result.copy()
            enhanced_result['enhanced_score'] = enhanced_score
            enhanced_result['original_score'] = original_score
            enhanced_result['precision_adjustments'] = precision_adjustments
            enhanced_results.append(enhanced_result)

        # Sort by enhanced score
        enhanced_results.sort(key=lambda x: x.get('enhanced_score', 0), reverse=True)

        # Log precision improvements
        if enhanced_results:
            top_result = enhanced_results[0]
            if top_result['precision_adjustments']:
                logger.info(f"Top result precision adjustments: {top_result['precision_adjustments']}")

        return enhanced_results

    def _is_chargeback_manual_query(self, query_lower: str) -> bool:
        """Check if this is a chargeback manual task query"""
        chargeback_keywords = ['running', 'chargeback', 'preprocessor', 'manually']
        return all(keyword in query_lower for keyword in chargeback_keywords)

    def _apply_chargeback_manual_precision(self, title: str, content: str, score: float, query: str) -> Tuple[float, List[str]]:
        """Apply precision enhancements specific to chargeback manual queries"""

        adjustments = []

        # Exact title match for manual task gets highest priority
        if 'running the chargeback preprocessor task manually' in title:
            score += 5.0
            adjustments.append("Exact manual task title match: +5.0")

        # Boost content with specific manual task indicators
        manual_indicators = ['run now', 'scheduled tasks', 'chargeback-processor-genericchargeback']
        manual_matches = sum(1 for indicator in manual_indicators if indicator in content)
        if manual_matches > 0:
            boost = manual_matches * 1.5
            score += boost
            adjustments.append(f"Manual task indicators ({manual_matches}): +{boost:.1f}")

        # Penalty for component level metrics content (unwanted for this query)
        unwanted_phrases = [
            'component level metrics',
            'whitelist',
            'limited set of hosts',
            'cbp.usecase.whitelist'
        ]
        unwanted_matches = sum(1 for phrase in unwanted_phrases if phrase in content)
        if unwanted_matches > 0:
            penalty = unwanted_matches * 2.0
            score -= penalty
            adjustments.append(f"Unwanted content penalty ({unwanted_matches}): -{penalty:.1f}")

        # Boost for procedural content
        if 'steps' in content and ('1.' in content or '2.' in content):
            score += 1.0
            adjustments.append("Procedural steps detected: +1.0")

        return score, adjustments

    def _apply_general_precision_rules(self, title: str, content: str, score: float, query: str) -> Tuple[float, List[str]]:
        """Apply general precision enhancement rules"""

        adjustments = []

        # Title relevance boost
        query_words = query.split()
        title_matches = sum(1 for word in query_words if word in title)
        if title_matches > 0:
            title_boost = (title_matches / len(query_words)) * 1.0
            score += title_boost
            adjustments.append(f"Title relevance ({title_matches}/{len(query_words)}): +{title_boost:.1f}")

        # Content length penalty for overly long chunks (prefer focused content)
        content_length = len(content)
        if content_length > 3000:
            length_penalty = (content_length - 3000) / 1000 * 0.3
            score -= length_penalty
            adjustments.append(f"Length penalty ({content_length} chars): -{length_penalty:.1f}")

        # Boost for exact phrase matches in content
        if query in content:
            score += 2.0
            adjustments.append("Exact phrase match in content: +2.0")

        return score, adjustments

    def _is_self_contained_section(self, match: Dict) -> bool:
        """Check if a section is self-contained and shouldn't be combined with other sections"""
        
        title = match.get('title', '').lower()
        content = match.get('content', '').lower()
        
        # Check for procedural sections that are typically self-contained
        procedural_indicators = [
            'running', 'manually', 'steps', 'procedure', 'task', 'how to',
            'enable', 'disable', 'configure', 'install', 'setup'
        ]
        
        # Check for content completeness indicators
        completeness_indicators = [
            'steps', '1.', '2.', '3.', 'about this task', 'prerequisites',
            'run now', 'click', 'browse', 'select', 'configure'
        ]
        
        # If it's a procedural section with substantial content and completeness indicators
        is_procedural = any(indicator in title for indicator in procedural_indicators)
        has_substantial_content = len(match.get('content', '')) > 300
        has_completeness = any(indicator in content for indicator in completeness_indicators)
        
        # If it's an exact title match with procedural content, it's likely self-contained
        is_exact_match = 'exact_title' in match.get('match_type', '')
        
        # Additional check: if content has a clear start and end (procedural steps)
        has_clear_structure = (
            'steps' in content and 
            any(num in content for num in ['1.', '2.', '3.', '4.', '5.']) and
            len(content.split('\n')) > 5  # Multiple lines suggest structured content
        )
        
        return (is_procedural and has_substantial_content and 
                (has_completeness or has_clear_structure or is_exact_match))

    def _are_sections_unrelated(self, original_match: Dict, chunk_title: str, chunk_content: str) -> bool:
        """Check if two sections are unrelated and shouldn't be combined"""
        
        original_title = original_match.get('title', '').lower()
        original_content = original_match.get('content', '').lower()
        chunk_title_lower = chunk_title.lower()
        chunk_content_lower = chunk_content.lower()
        
        # Extract key concepts from titles
        original_concepts = self._extract_section_concepts(original_title)
        chunk_concepts = self._extract_section_concepts(chunk_title_lower)
        
        # If they share no meaningful concepts, they're likely unrelated
        shared_concepts = original_concepts.intersection(chunk_concepts)
        if len(shared_concepts) == 0 and len(original_concepts) > 0 and len(chunk_concepts) > 0:
            logger.info(f"Sections unrelated - no shared concepts. Original: {original_concepts}, Chunk: {chunk_concepts}")
            return True
        
        # Check for conflicting purposes (e.g., manual vs automatic, different systems)
        conflicting_pairs = [
            ('manually', 'automatic'), ('manual', 'scheduled'),
            ('chargeback', 'component'), ('preprocessor', 'metrics'),
            ('whitelist', 'blacklist'), ('enable', 'disable')
        ]
        
        for concept1, concept2 in conflicting_pairs:
            if (concept1 in original_title and concept2 in chunk_title_lower) or \
               (concept2 in original_title and concept1 in chunk_title_lower):
                logger.info(f"Sections have conflicting purposes: {concept1} vs {concept2}")
                return True
        
        # Check for different system components or different types of operations
        system_indicators = {
            'chargeback': ['preprocessor', 'processor', 'task', 'scheduled'],
            'metrics': ['component', 'level', 'collection', 'whitelist'],
            'security': ['hardening', 'firewall', 'authentication', 'certificate'],
            'installation': ['setup', 'configure', 'install', 'prerequisites']
        }
        
        original_system = None
        chunk_system = None
        
        for system, indicators in system_indicators.items():
            if any(indicator in original_title for indicator in indicators):
                original_system = system
            if any(indicator in chunk_title_lower for indicator in indicators):
                chunk_system = system
        
        # If they belong to different systems and don't share concepts, they're unrelated
        if (original_system and chunk_system and 
            original_system != chunk_system and 
            len(shared_concepts) < 2):
            logger.info(f"Sections belong to different systems: {original_system} vs {chunk_system}")
            return True
        
        return False

    def _extract_section_concepts(self, title: str) -> set:
        """Extract key concepts from a section title"""
        
        # Remove common words and extract meaningful concepts
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during',
            'before', 'after', 'above', 'below', 'between', 'among', 'is', 'are',
            'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
            'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he',
            'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        # Split title into words and filter out stop words and short words
        words = title.split()
        concepts = set()
        
        for word in words:
            # Remove punctuation and convert to lowercase
            clean_word = ''.join(c for c in word if c.isalnum()).lower()
            if len(clean_word) > 2 and clean_word not in stop_words:
                concepts.add(clean_word)
        
        return concepts