#!/usr/bin/env python3
"""
PDF Searcher Module
Handles semantic search with font-based heading prioritization
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from collections import defaultdict
import re

# Import required libraries
try:
    from sentence_transformers import SentenceTransformer
    import faiss
    import numpy as np
except ImportError as e:
    print(f"Missing required library: {e}")
    print("Install with: pip install sentence-transformers faiss-cpu numpy")
    raise

logger = logging.getLogger(__name__)

class PDFSearcher:
    """Enhanced searcher with font-based heading priority"""
    
    def __init__(self, index_dir: str = "indexes", extracted_docs_dir: str = "extracted_docs",
                 model_name: str = 'all-MiniLM-L6-v2'):
        self.index_dir = Path(index_dir)
        self.extracted_docs_dir = Path(extracted_docs_dir)
        self.model_name = model_name
        
        # Load embedding model
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        # Discover available documents
        self.documents = self.discover_documents()
        logger.info(f"Found {len(self.documents)} processed documents")
        
        # Load indexes and enhanced data
        self.indexes = self.load_all_indexes()
        self.enhanced_data = self.load_enhanced_data()
    
    def discover_documents(self) -> Dict[str, Dict[str, Any]]:
        """Discover all processed documents with enhanced data"""
        documents = {}
        
        if not self.index_dir.exists():
            logger.warning(f"Index directory not found: {self.index_dir}")
            return documents
        
        # Find all FAISS index files
        faiss_files = list(self.index_dir.glob("*.faiss"))
        
        for faiss_file in faiss_files:
            doc_id = faiss_file.stem
            metadata_file = self.index_dir / f"{doc_id}_metadata.json"
            
            # Check for enhanced data
            enhanced_dir = self.extracted_docs_dir / doc_id
            enhanced_structure_file = enhanced_dir / "enhanced_structure.json"
            heading_summary_file = enhanced_dir / "heading_summary.json"
            font_analysis_file = enhanced_dir / "font_analysis.json"
            
            if (metadata_file.exists() and enhanced_structure_file.exists() 
                and heading_summary_file.exists()):
                documents[doc_id] = {
                    'doc_id': doc_id,
                    'faiss_file': faiss_file,
                    'metadata_file': metadata_file,
                    'enhanced_structure_file': enhanced_structure_file,
                    'heading_summary_file': heading_summary_file,
                    'font_analysis_file': font_analysis_file,
                    'has_enhanced_data': True
                }
                logger.info(f"✅ Found enhanced document: {doc_id}")
            elif metadata_file.exists():
                # Fallback to standard processing
                title_index_file = self.index_dir / f"{doc_id}_title_index.json"
                if title_index_file.exists():
                    documents[doc_id] = {
                        'doc_id': doc_id,
                        'faiss_file': faiss_file,
                        'metadata_file': metadata_file,
                        'title_index_file': title_index_file,
                        'has_enhanced_data': False
                    }
                    logger.info(f"⚠️ Found standard document: {doc_id}")
        
        return documents
    
    def load_all_indexes(self) -> Dict[str, Dict[str, Any]]:
        """Load all document indexes"""
        indexes = {}
        
        for doc_id, doc_info in self.documents.items():
            try:
                # Load FAISS index
                faiss_index = faiss.read_index(str(doc_info['faiss_file']))
                
                # Load metadata
                with open(doc_info['metadata_file'], 'r', encoding='utf-8') as f:
                    metadata_data = json.load(f)
                
                indexes[doc_id] = {
                    'faiss_index': faiss_index,
                    'metadata': metadata_data['metadata'],
                    'chunks': metadata_data['chunks'],
                    'embedding_model': metadata_data.get('embedding_model', 384),
                    'has_enhanced_data': doc_info['has_enhanced_data']
                }
                
                # Load title index for non-enhanced documents
                if not doc_info['has_enhanced_data'] and 'title_index_file' in doc_info:
                    with open(doc_info['title_index_file'], 'r', encoding='utf-8') as f:
                        indexes[doc_id]['title_index'] = json.load(f)
                
                logger.info(f"Loaded index for {doc_id}: {faiss_index.ntotal} vectors")
                
            except Exception as e:
                logger.error(f"Failed to load index for {doc_id}: {e}")
        
        return indexes
    
    def load_enhanced_data(self) -> Dict[str, Dict[str, Any]]:
        """Load enhanced font-based data for documents that have it"""
        enhanced_data = {}
        
        for doc_id, doc_info in self.documents.items():
            if not doc_info['has_enhanced_data']:
                continue
                
            try:
                # Load enhanced structure
                with open(doc_info['enhanced_structure_file'], 'r', encoding='utf-8') as f:
                    structure = json.load(f)
                
                # Load heading summary
                with open(doc_info['heading_summary_file'], 'r', encoding='utf-8') as f:
                    headings = json.load(f)
                
                # Load font analysis if available
                font_analysis = None
                if doc_info['font_analysis_file'].exists():
                    with open(doc_info['font_analysis_file'], 'r', encoding='utf-8') as f:
                        font_analysis = json.load(f)
                
                enhanced_data[doc_id] = {
                    'structure': structure,
                    'headings': headings,
                    'font_analysis': font_analysis,
                    'heading_index': self._build_enhanced_heading_index(headings)
                }
                
                logger.info(f"Loaded enhanced data for {doc_id}: {len(headings)} headings")
                
            except Exception as e:
                logger.error(f"Failed to load enhanced data for {doc_id}: {e}")
        
        return enhanced_data
    
    def _build_enhanced_heading_index(self, headings: List[Dict]) -> Dict[str, List[Dict]]:
        """Build optimized heading index for fast search"""
        heading_index = defaultdict(list)
        
        for i, heading in enumerate(headings):
            title = heading['title'].lower().strip()
            words = title.split()
            
            # Index full title (highest priority)
            heading_index[title].append({
                'heading': heading,
                'heading_index': i,
                'match_type': 'exact_title',
                'priority_score': self._calculate_heading_priority(heading)
            })
            
            # Index individual words
            for word in words:
                if len(word) > 2:  # Skip short words
                    heading_index[word].append({
                        'heading': heading,
                        'heading_index': i,
                        'match_type': 'title_word',
                        'priority_score': self._calculate_heading_priority(heading) * 0.8
                    })
        
        return dict(heading_index)
    
    def _calculate_heading_priority(self, heading: Dict) -> float:
        """Calculate priority score for a heading based on font characteristics"""
        priority = 0.5  # Base priority
        
        # Higher priority for larger fonts
        font_size = heading.get('font_size', 12)
        if font_size >= 18:
            priority += 0.3
        elif font_size >= 16:
            priority += 0.2
        elif font_size >= 14:
            priority += 0.1
        
        # Higher priority for bold text
        if heading.get('is_bold', False):
            priority += 0.2
        
        # Higher priority for higher heading levels (lower numbers = higher priority)
        heading_level = heading.get('heading_level', 3)
        if heading_level == 1:
            priority += 0.3
        elif heading_level == 2:
            priority += 0.2
        elif heading_level == 3:
            priority += 0.1
        
        # Higher priority for more confident classifications
        confidence = heading.get('confidence', 0.0)
        priority += confidence * 0.2
        
        return min(priority, 1.0)  # Cap at 1.0
    
    def _find_chunk_content_by_title(self, doc_id: str, title: str) -> Optional[str]:
        """Find the full content of a chunk by its title."""
        if doc_id not in self.indexes:
            return None
        
        index_data = self.indexes[doc_id]
        metadata_list = index_data.get('metadata', [])
        chunks = index_data.get('chunks', [])

        target = self._normalize_title(title)

        # 1) Exact match after normalization
        for i, metadata in enumerate(metadata_list):
            meta_title = self._normalize_title(metadata.get('title', ''))
            if meta_title == target:
                if i < len(chunks):
                    return chunks[i]

        # 2) Enhanced substring/containment match for heading-to-content mapping
        best_match_content = None
        best_match_score = 0
        
        for i, metadata in enumerate(metadata_list):
            meta_title = self._normalize_title(metadata.get('title', ''))
            chunk_content = chunks[i] if i < len(chunks) else ""
            
            # Check if target title appears in the chunk content or vice versa
            if target and len(target) > 8:
                # Score the match quality
                match_score = 0
                
                # Direct title containment
                if target in meta_title or meta_title in target:
                    match_score += 0.8
                
                # Check if the title appears in the content itself
                if target in chunk_content.lower():
                    match_score += 0.6
                
                # Check for key words matching
                target_words = set(target.split())
                meta_words = set(meta_title.split())
                content_words = set(chunk_content.lower().split())
                
                word_overlap = len(target_words.intersection(meta_words))
                content_overlap = len(target_words.intersection(content_words))
                
                if word_overlap > 0:
                    match_score += (word_overlap / len(target_words)) * 0.5
                
                if content_overlap > 0:
                    match_score += (content_overlap / len(target_words)) * 0.4
                
                # Prefer chunks with substantial content
                if len(chunk_content) > 100:
                    match_score += 0.2
                
                if match_score > best_match_score and match_score > 0.5:
                    best_match_score = match_score
                    best_match_content = chunk_content

        if best_match_content:
            return best_match_content

        return None
    
    def _find_content_by_semantic_search(self, doc_id: str, title: str) -> Optional[str]:
        """Use semantic search to find content related to a title when direct mapping fails"""
        try:
            if doc_id not in self.indexes:
                return None
            
            index_data = self.indexes[doc_id]
            faiss_index = index_data['faiss_index']
            
            # Generate embedding for the title
            title_embedding = self.model.encode([title])
            faiss.normalize_L2(title_embedding)
            
            # Search for semantically similar content
            scores, indices = faiss_index.search(
                title_embedding.astype('float32'), 
                min(5, faiss_index.ntotal)
            )
            
            # Return the best matching content that's substantial
            for score, idx in zip(scores[0], indices[0]):
                if idx != -1 and score > 0.3:  # Reasonable similarity threshold
                    content = index_data['chunks'][idx]
                    if len(content) > 100:  # Ensure substantial content
                        return content
            
            return None
            
        except Exception as e:
            logger.error(f"Semantic fallback search failed: {e}")
            return None
    
    def _find_complete_content_from_source(self, doc_id: str, title: str) -> Optional[str]:
        """Find complete content by looking directly at source markdown files for exact title matches"""
        try:
            # Check if we have enhanced data for this document
            if doc_id not in self.enhanced_data:
                return None
            
            # Look for markdown files in the extracted docs directory
            doc_dir = self.extracted_docs_dir / doc_id
            markdown_files = ['docling_content.md', 'complete_content.md']
            
            target_title = title.lower().strip()
            
            for markdown_file in markdown_files:
                markdown_path = doc_dir / markdown_file
                if not markdown_path.exists():
                    continue
                
                try:
                    with open(markdown_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Split into lines and find the section
                    lines = content.split('\n')
                    section_content = []
                    in_target_section = False
                    section_level = 0
                    
                    for line in lines:
                        # Check if this is our target heading
                        if line.strip() and ('##' in line or '#' in line):
                            clean_line = line.strip().lower()
                            clean_line = clean_line.replace('#', '').strip()
                            
                            # Normalize both strings for better matching
                            normalized_line = self._normalize_title(clean_line)
                            normalized_target = self._normalize_title(target_title)
                            
                            if normalized_line == normalized_target:
                                # Found our section
                                in_target_section = True
                                section_level = line.count('#')
                                section_content = [line]
                                continue
                            elif in_target_section:
                                # Check if this is a new section at same or higher level
                                current_level = line.count('#')
                                # Don't break on procedural sub-headings, continue including them
                                is_procedural_sub = self._is_procedural_subheading(line.strip())
                                if current_level <= section_level and not is_procedural_sub:
                                    # End of our section
                                    break
                        
                        if in_target_section:
                            section_content.append(line)
                    
                    if section_content:
                        complete_content = '\n'.join(section_content)
                        # Only return if we have substantial content (more than just the heading)
                        if len(complete_content) > len(title) + 50:
                            logger.info(f"Found complete content from source for '{title}': {len(complete_content)} chars")
                            return complete_content
                
                except Exception as e:
                    logger.error(f"Error reading {markdown_path}: {e}")
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding complete content from source: {e}")
            return None
    
    def _is_procedural_subheading(self, text: str) -> bool:
        """Detect procedural sub-headings that should remain part of the main content."""
        if not text:
            return False
        
        text_lower = text.strip().lower()
        
        # Remove markdown formatting for checking
        clean_text = text_lower.replace('#', '').strip()
        
        # Common procedural sub-headings that should not split content
        procedural_subheadings = [
            'steps', 'procedure', 'instructions', 'process', 'method',
            'prerequisites', 'requirements', 'before you begin',
            'next steps', 'what to do next', 'continue with',
            'follow these steps', 'to do this', 'implementation',
            'example', 'examples', 'note', 'notes', 'important',
            'warning', 'caution', 'tip', 'tips', 'result', 'results',
            'outcome', 'expected result', 'verification', 'verify',
            'troubleshooting', 'if this fails', 'alternative'
        ]
        
        # Check if the clean text matches any procedural sub-heading
        for subheading in procedural_subheadings:
            if clean_text == subheading or clean_text.startswith(subheading + ' '):
                return True
        
        # Also check for very short headings that are likely sub-sections
        if len(clean_text.split()) <= 2 and len(clean_text) <= 15:
            return True
            
        return False

    def _normalize_title(self, text: str) -> str:
        """Normalize titles to improve matching between heading lists and chunk metadata."""
        if not text:
            return ""
        t = text.strip().lower()
        # Remove TOC pipes and leaders
        t = t.replace('|', ' ')
        t = re.sub(r"\.{3,}", " ", t)
        # Collapse whitespace
        t = re.sub(r"\s+", " ", t)
        # Remove trailing page numbers and parentheses
        t = re.sub(r"\(page\s*\d+\)$", "", t)
        t = re.sub(r"\s\d{1,4}$", "", t)
        return t.strip()
    
    def search(self, query: str, top_k: int = 10, 
               document_ids: Optional[List[str]] = None,
               heading_boost: float = 2.0) -> List[Dict[str, Any]]:
        """Enhanced search with font-based heading priority"""
        logger.info(f"Performing enhanced search for: '{query}'")
        
        query_lower = query.lower().strip()
        query_words = set(query_lower.split())
        all_results = []
        
        # Search in each document
        search_docs = document_ids if document_ids else list(self.indexes.keys())
        
        for doc_id in search_docs:
            if doc_id not in self.indexes:
                continue
            
            doc_results = []
            
            # 1. PRIORITY: Font-based heading matches (if enhanced data available)
            if doc_id in self.enhanced_data:
                heading_matches = self._search_enhanced_headings(
                    query_lower, query_words, doc_id, heading_boost
                )
                doc_results.extend(heading_matches)
            
            # 2. Semantic search in chunks
            semantic_matches = self._search_semantic_chunks(
                query, doc_id, top_k * 2
            )
            doc_results.extend(semantic_matches)
            
            # 3. Fallback title search for non-enhanced documents
            if doc_id not in self.enhanced_data:
                title_matches = self._search_titles_fallback(
                    query_lower, doc_id, heading_boost
                )
                doc_results.extend(title_matches)
            
            all_results.extend(doc_results)
        
        # Deduplicate and rank results
        final_results = self._rank_and_deduplicate_results(all_results, query_words)
        
        return final_results[:top_k]
    
    def _search_enhanced_headings(self, query_lower: str, query_words: set, 
                                 doc_id: str, heading_boost: float) -> List[Dict]:
        """Search in font-based headings with high precision"""
        results = []
        enhanced_data = self.enhanced_data[doc_id]
        heading_index = enhanced_data['heading_index']

        # Helper to create result dict
        def create_heading_result(match, match_type, score_multiplier):
            heading_title = match['heading']['title']
            content = self._find_chunk_content_by_title(doc_id, heading_title)
            
            # For exact matches, try to get complete content from source files first
            if match_type == 'exact_heading_match' and (not content or len(content) < 200):
                complete_content = self._find_complete_content_from_source(doc_id, heading_title)
                if complete_content:
                    content = complete_content
            
            # Enhanced fallback - try to find content using semantic search if direct mapping fails
            if not content or len(content) < 50:
                content = self._find_content_by_semantic_search(doc_id, heading_title)
            
            # Final fallback with heading title
            if not content:
                content = f"# {heading_title}\n\n(Content not found - This is a heading reference)"
            
            result = {
                'document_id': doc_id,
                'title': heading_title,
                'content': content,
                'match_type': match_type,
                'match_score': match['priority_score'] * heading_boost * score_multiplier,
                'font_size': match['heading'].get('font_size', 0),
                'is_bold': match['heading'].get('is_bold', False),
                'heading_level': match['heading'].get('heading_level', 3),
                'page': match['heading'].get('page', 1),
                'confidence': match['heading'].get('confidence', 0.0),
                'search_type': 'font_based_heading',
                'is_heading_result': True
            }
            return result

        # Exact title matches (highest priority)
        if query_lower in heading_index:
            for match in heading_index[query_lower]:
                if match['match_type'] == 'exact_title':
                    results.append(create_heading_result(match, 'exact_heading_match', 1.0))
        
        # Enhanced exact matching - try variations of the query
        query_variations = [
            query_lower,
            query_lower.replace(' for all ', ' for all '),  # Handle spacing variations
            query_lower.replace(' - ', ' '),  # Handle dash variations
            query_lower.strip('# '),  # Remove markdown headers
        ]
        
        for variation in query_variations:
            variation = variation.strip()
            if variation and variation != query_lower and variation in heading_index:
                for match in heading_index[variation]:
                    if match['match_type'] == 'exact_title':
                        results.append(create_heading_result(match, 'exact_heading_match_variation', 0.95))
        
        # Partial title matches
        for title, matches in heading_index.items():
            if query_lower in title and query_lower != title:
                for match in matches:
                    if match['match_type'] == 'exact_title':
                        results.append(create_heading_result(match, 'partial_heading_match', 0.8))
        
        # Word-based matches in headings
        for word in query_words:
            if word in heading_index:
                for match in heading_index[word]:
                    if match['match_type'] == 'title_word':
                        result = create_heading_result(match, 'heading_word_match', 0.6)
                        result['matched_word'] = word
                        results.append(result)
        
        # Enhanced: Search for related procedure content when finding procedure titles
        if any(word in query_lower for word in ['upgrade', 'install', 'configure', 'procedure', 'steps']):
            related_results = self._find_related_procedure_content(query_lower, query_words, doc_id)
            results.extend(related_results)
        
        return results
    
    def _find_related_procedure_content(self, query_lower: str, query_words: set, doc_id: str) -> List[Dict]:
        """Find related procedure content when searching for procedure titles"""
        results = []
        
        # Look for procedure-related headings that might contain the actual steps
        procedure_keywords = ['if', 'install', 'upgrade', 'ese', 'steps', 'procedure', 'command']
        
        for keyword in procedure_keywords:
            if keyword in query_lower:
                # Search for headings that contain procedure steps
                for heading_title, matches in self.enhanced_data[doc_id]['heading_index'].items():
                    if (keyword in heading_title.lower() and 
                        any(proc_word in heading_title.lower() for proc_word in procedure_keywords)):
                        
                        for match in matches:
                            if match['match_type'] == 'exact_title':
                                content = self._find_chunk_content_by_title(doc_id, heading_title)
                                if content and len(content) > 200:  # Only include chunks with substantial content
                                    result = {
                                        'document_id': doc_id,
                                        'title': heading_title,
                                        'content': content,
                                        'match_type': 'related_procedure',
                                        'match_score': match['priority_score'] * 0.7,  # Lower score than exact matches
                                        'font_size': match['heading'].get('font_size', 0),
                                        'is_bold': match['heading'].get('is_bold', False),
                                        'heading_level': match['heading'].get('heading_level', 3),
                                        'page': match['heading'].get('page', 1),
                                        'confidence': match['heading'].get('confidence', 0.0),
                                        'search_type': 'related_procedure_search',
                                        'is_heading_result': True
                                    }
                                    results.append(result)
        
        return results
    
    def _search_semantic_chunks(self, query: str, doc_id: str, top_k: int) -> List[Dict]:
        """Search in vector-indexed chunks"""
        index_data = self.indexes[doc_id]
        faiss_index = index_data['faiss_index']
        
        # Generate query embedding
        query_embedding = self.model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = faiss_index.search(
            query_embedding.astype('float32'),
            min(top_k, faiss_index.ntotal)
        )
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1:
                metadata = index_data['metadata'][idx]
                chunk_text = index_data['chunks'][idx]
                
                # Check if this is a heading chunk (enhanced data)
                is_heading_chunk = metadata.get('is_heading_chunk', False)
                boost = 1.5 if is_heading_chunk else 1.0
                
                results.append({
                    'document_id': doc_id,
                    'chunk_index': idx,
                    'title': metadata['title'],
                    'content': chunk_text,
                    'match_type': 'semantic_match',
                    'match_score': float(score) * boost,
                    'hierarchy_level': metadata.get('hierarchy_level', 'unknown'),
                    'chunk_type': metadata.get('chunk_type', 'unknown'),
                    'page': metadata.get('primary_page', 1),
                    'font_size': metadata.get('font_size', 0),
                    'is_bold': metadata.get('is_bold', False),
                    'heading_level': metadata.get('heading_level', 0),
                    'search_type': 'semantic',
                    'is_heading_result': is_heading_chunk,
                    'extraction_method': metadata.get('extraction_method', 'unknown')
                })
        
        return results
    
    def _search_titles_fallback(self, query_lower: str, doc_id: str, 
                               heading_boost: float) -> List[Dict]:
        """Fallback title search for documents without enhanced data"""
        results = []
        index_data = self.indexes[doc_id]
        
        if 'title_index' not in index_data:
            return results
        
        title_index = index_data['title_index']
        metadata = index_data['metadata']
        chunks = index_data['chunks']
        
        for title, matches in title_index.items():
            if query_lower in title:
                for match in matches:
                    chunk_idx = match['chunk_index']
                    chunk_metadata = metadata[chunk_idx]
                    chunk_text = chunks[chunk_idx]
                    
                    score = heading_boost if match.get('exact_match', False) else heading_boost * 0.8
                    
                    results.append({
                        'document_id': doc_id,
                        'chunk_index': chunk_idx,
                        'title': chunk_metadata['title'],
                        'content': chunk_text,
                        'match_type': 'title_fallback_match',
                        'match_score': score,
                        'hierarchy_level': chunk_metadata.get('hierarchy_level', 'unknown'),
                        'page': chunk_metadata.get('primary_page', 1),
                        'search_type': 'title_fallback',
                        'is_heading_result': True
                    })
        
        return results
    
    def _rank_and_deduplicate_results(self, all_results: List[Dict], 
                                    query_words: set) -> List[Dict]:
        """Rank and deduplicate search results"""
        
        # Deduplicate by document + title + page
        seen = set()
        unique_results = []
        
        for result in all_results:
            # Create unique key
            key = (
                result['document_id'],
                result['title'],
                result.get('page', 1),
                result.get('chunk_index', -1)
            )
            
            if key not in seen:
                seen.add(key)
                
                # Calculate final ranking score
                base_score = result['match_score']
                
                # Boost for heading results
                if result.get('is_heading_result', False):
                    base_score *= 1.3
                
                # Boost for font-based extraction
                if result.get('extraction_method') == 'font_based':
                    base_score *= 1.2
                
                # Boost for exact matches
                if result.get('match_type') == 'exact_heading_match':
                    base_score *= 1.5
                
                # Word density boost
                content_words = set(result['content'].lower().split())
                word_matches = len(query_words.intersection(content_words))
                if word_matches > 0:
                    word_density = word_matches / len(query_words)
                    base_score *= (1.0 + word_density * 0.3)
                
                result['final_score'] = base_score
                unique_results.append(result)
        
        # Sort by final score
        unique_results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return unique_results
    
    def format_result(self, result: Dict[str, Any], show_content: bool = True) -> str:
        """Format search result"""
        lines = []
        
        # Title with font information
        title = result['title']
        if result.get('is_heading_result', False):
            font_info = []
            if result.get('font_size', 0) > 0:
                font_info.append(f"{result['font_size']:.1f}pt")
            if result.get('is_bold', False):
                font_info.append("Bold")
            if result.get('heading_level', 0) > 0:
                font_info.append(f"H{result['heading_level']}")
            
            font_str = f" [{', '.join(font_info)}]" if font_info else ""
            lines.append(f"HEADING: {title}{font_str}")
        else:
            lines.append(f"CONTENT: {title}")
        
        lines.append(f"   Document: {result['document_id']}")
        lines.append(f"   Page: {result.get('page', 'N/A')}")
        
        # Search metadata
        search_type = result.get('search_type', 'unknown')
        match_type = result.get('match_type', 'unknown')
        score = result.get('final_score', result.get('match_score', 0))
        confidence = result.get('confidence', 0)
        
        search_info = f"   Search: {search_type} | {match_type}"
        if confidence > 0:
            search_info += f" | confidence: {confidence:.2f}"
        search_info += f" | score: {score:.3f}"
        lines.append(search_info)
        
        # Content preview
        if show_content:
            content = result['content']
            if result.get('is_heading_result', False) and content.startswith("HEADING:"):
                # For heading results, show context or full heading
                lines.append(f"   MATCH: {content}")
            else:
                # For body content, show preview
                preview = content[:300] + "..." if len(content) > 300 else content
                lines.append(f"   Content: {preview}")
        
        lines.append("")
        return "\n".join(lines)
    
    def list_documents(self) -> Dict[str, Dict[str, Any]]:
        """List all available documents"""
        return self.documents
