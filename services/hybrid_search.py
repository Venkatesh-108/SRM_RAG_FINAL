#!/usr/bin/env python3
"""
Hybrid Search Service
Combines BM25 (sparse) and FAISS (dense) search with cross-encoder reranking
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

class HybridSearchEngine:
    """Enhanced hybrid search combining BM25, FAISS, and cross-encoder reranking"""
    
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
        
        # Load document data
        self.documents = self._discover_documents()
        self.bm25_indexes = {}
        self.faiss_indexes = {}
        self.document_chunks = {}
        
        # Initialize indexes
        self._load_all_indexes()
        logger.info(f"Hybrid search initialized with {len(self.documents)} documents")
    
    def _discover_documents(self) -> Dict[str, Dict[str, Any]]:
        """Discover all processed documents"""
        documents = {}
        
        if not self.index_dir.exists():
            logger.warning(f"Index directory not found: {self.index_dir}")
            return documents
        
        # Find all FAISS index files
        faiss_files = list(self.index_dir.glob("*.faiss"))
        
        for faiss_file in faiss_files:
            doc_id = faiss_file.stem
            metadata_file = self.index_dir / f"{doc_id}_metadata.json"
            
            if metadata_file.exists():
                documents[doc_id] = {
                    'doc_id': doc_id,
                    'faiss_file': faiss_file,
                    'metadata_file': metadata_file,
                }
                logger.info(f"Found document: {doc_id}")
        
        return documents
    
    def _load_all_indexes(self):
        """Load BM25 and FAISS indexes for all documents"""
        for doc_id, doc_info in self.documents.items():
            try:
                # Load FAISS index and metadata
                faiss_index = faiss.read_index(str(doc_info['faiss_file']))
                
                with open(doc_info['metadata_file'], 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                
                chunks = metadata.get('chunks', [])
                chunk_metadata = metadata.get('metadata', [])
                
                # Store FAISS data
                self.faiss_indexes[doc_id] = {
                    'index': faiss_index,
                    'metadata': chunk_metadata,
                    'chunks': chunks
                }
                
                # Create BM25 index from chunks
                tokenized_chunks = [self._tokenize(chunk) for chunk in chunks]
                bm25_index = BM25Okapi(tokenized_chunks)
                
                self.bm25_indexes[doc_id] = bm25_index
                self.document_chunks[doc_id] = {
                    'chunks': chunks,
                    'metadata': chunk_metadata,
                    'tokenized': tokenized_chunks
                }
                
                logger.info(f"Loaded indexes for {doc_id}: {len(chunks)} chunks")
                
            except Exception as e:
                logger.error(f"Failed to load indexes for {doc_id}: {e}")
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for BM25"""
        # Convert to lowercase and split on non-alphanumeric characters
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
    
    def generate_multi_queries(self, query: str, num_queries: int = 3) -> List[str]:
        """Generate multiple query variations for better retrieval coverage"""
        if not self.config.get("enable_multi_query_generation", False):
            return [query]
        
        queries = [query]
        
        # Add variations based on common patterns
        # 1. Add question form
        if not query.endswith('?'):
            queries.append(f"How to {query.lower()}?")
            queries.append(f"What is {query.lower()}?")
        
        # 2. Add procedural form
        if "install" in query.lower():
            queries.append(query.replace("install", "setup"))
            queries.append(query.replace("install", "configure"))
        
        # 3. Add specific terms
        query_words = query.lower().split()
        if "upgrade" in query_words:
            queries.append(query.replace("upgrade", "update"))
        
        if "configure" in query_words:
            queries.append(query.replace("configure", "setup"))
        
        return queries[:num_queries]
    
    def search_bm25(self, query: str, doc_id: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """BM25 sparse retrieval for a document"""
        if doc_id not in self.bm25_indexes:
            return []
        
        bm25_index = self.bm25_indexes[doc_id]
        tokenized_query = self._tokenize(query)
        
        # Get BM25 scores
        scores = bm25_index.get_scores(tokenized_query)
        
        # Get top-k results
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        results = []
        for idx in top_indices:
            if scores[idx] > 0:  # Only include positive scores
                chunk_data = self.document_chunks[doc_id]
                results.append({
                    'doc_id': doc_id,
                    'chunk_idx': idx,
                    'content': chunk_data['chunks'][idx],
                    'metadata': chunk_data['metadata'][idx],
                    'bm25_score': float(scores[idx]),
                    'search_type': 'bm25'
                })
        
        return results
    
    def search_faiss(self, query: str, doc_id: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """FAISS dense retrieval for a document"""
        if doc_id not in self.faiss_indexes:
            return []
        
        faiss_data = self.faiss_indexes[doc_id]
        faiss_index = faiss_data['index']
        
        # Generate query embedding
        query_embedding = self.embedding_model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = faiss_index.search(
            query_embedding.astype('float32'),
            min(top_k, faiss_index.ntotal)
        )
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1 and score > 0:
                results.append({
                    'doc_id': doc_id,
                    'chunk_idx': idx,
                    'content': faiss_data['chunks'][idx],
                    'metadata': faiss_data['metadata'][idx],
                    'faiss_score': float(score),
                    'search_type': 'faiss'
                })
        
        return results
    
    def combine_results(self, bm25_results: List[Dict], faiss_results: List[Dict], 
                       alpha: float = 0.5) -> List[Dict[str, Any]]:
        """Combine BM25 and FAISS results with score normalization"""
        # Normalize BM25 scores
        if bm25_results:
            max_bm25 = max(r['bm25_score'] for r in bm25_results)
            if max_bm25 > 0:
                for r in bm25_results:
                    r['bm25_score_norm'] = r['bm25_score'] / max_bm25
            else:
                for r in bm25_results:
                    r['bm25_score_norm'] = 0.0
        
        # Normalize FAISS scores (already normalized by L2)
        for r in faiss_results:
            r['faiss_score_norm'] = r['faiss_score']
        
        # Combine results by chunk index
        combined = {}
        
        # Add BM25 results
        for result in bm25_results:
            key = f"{result['doc_id']}_{result['chunk_idx']}"
            combined[key] = result
            combined[key]['combined_score'] = alpha * result['bm25_score_norm']
            combined[key]['search_types'] = ['bm25']
        
        # Add FAISS results
        for result in faiss_results:
            key = f"{result['doc_id']}_{result['chunk_idx']}"
            if key in combined:
                # Combine scores
                combined[key]['faiss_score'] = result['faiss_score']
                combined[key]['faiss_score_norm'] = result['faiss_score_norm']
                combined[key]['combined_score'] += (1 - alpha) * result['faiss_score_norm']
                combined[key]['search_types'].append('faiss')
            else:
                # New result from FAISS only
                combined[key] = result
                combined[key]['combined_score'] = (1 - alpha) * result['faiss_score_norm']
                combined[key]['search_types'] = ['faiss']
        
        # Convert to list and sort by combined score
        results = list(combined.values())
        results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        return results
    
    def rerank_results(self, query: str, results: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """Rerank results using cross-encoder"""
        if not self.reranker or not results:
            return results[:top_k]
        
        # Prepare query-document pairs for reranking
        pairs = []
        for result in results:
            pairs.append([query, result['content']])
        
        # Get reranking scores
        rerank_scores = self.reranker.predict(pairs)
        
        # Update results with rerank scores
        for result, score in zip(results, rerank_scores):
            result['rerank_score'] = float(score)
            # Combine with original score
            result['final_score'] = 0.7 * result['combined_score'] + 0.3 * float(score)
        
        # Sort by final score
        results.sort(key=lambda x: x['final_score'], reverse=True)
        
        return results[:top_k]
    
    def diversity_selection(self, results: List[Dict[str, Any]], top_k: int = 5, 
                           similarity_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """Select diverse results to avoid redundancy"""
        if not self.config.get("enable_diversity_selection", False) or len(results) <= top_k:
            return results[:top_k]
        
        selected = []
        selected_embeddings = []
        
        for result in results:
            if len(selected) >= top_k:
                break
            
            # Get embedding for this result
            content_embedding = self.embedding_model.encode([result['content']])
            
            # Check similarity with already selected results
            is_diverse = True
            for selected_embedding in selected_embeddings:
                similarity = np.dot(content_embedding[0], selected_embedding) / (
                    np.linalg.norm(content_embedding[0]) * np.linalg.norm(selected_embedding)
                )
                if similarity > similarity_threshold:
                    is_diverse = False
                    break
            
            if is_diverse:
                selected.append(result)
                selected_embeddings.append(content_embedding[0])
        
        return selected
    
    def hybrid_search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Main hybrid search function"""
        logger.info(f"Hybrid search for: '{query}'")
        
        # Generate multiple queries if enabled
        queries = self.generate_multi_queries(query)
        
        all_results = []
        
        # Search across all documents
        for doc_id in self.documents:
            for q in queries:
                # BM25 search
                bm25_results = self.search_bm25(
                    q, doc_id, 
                    top_k=self.config.get("top_k_bm25", 10)
                )
                
                # FAISS search  
                faiss_results = self.search_faiss(
                    q, doc_id, 
                    top_k=self.config.get("top_k_faiss", 10)
                )
                
                # Combine results
                combined = self.combine_results(bm25_results, faiss_results)
                all_results.extend(combined)
        
        # Remove duplicates and sort by combined score
        seen = set()
        unique_results = []
        for result in all_results:
            key = f"{result['doc_id']}_{result['chunk_idx']}"
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        unique_results.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Take top candidates for reranking
        top_candidates = unique_results[:self.config.get("top_k_reranked", 15)]
        
        # Rerank if enabled
        if self.config.get("enable_reranking", False):
            reranked = self.rerank_results(query, top_candidates, top_k * 2)
        else:
            reranked = top_candidates[:top_k * 2]
        
        # Diversity selection
        final_results = self.diversity_selection(reranked, top_k)
        
        # Format results for compatibility
        formatted_results = []
        for result in final_results:
            formatted_results.append({
                'content': result['content'],
                'document_id': result['doc_id'],
                'chunk_index': result['chunk_idx'],
                'title': result['metadata'].get('title', 'Unknown Section'),
                'page': result['metadata'].get('primary_page', 1),
                'final_score': result.get('final_score', result['combined_score']),
                'bm25_score': result.get('bm25_score', 0.0),
                'faiss_score': result.get('faiss_score', 0.0),
                'rerank_score': result.get('rerank_score', 0.0),
                'search_types': result.get('search_types', []),
                'match_type': 'hybrid_search',
                'search_type': 'hybrid',
                'is_heading_result': result['metadata'].get('is_heading_chunk', False),
                'font_size': result['metadata'].get('font_size', 0),
                'is_bold': result['metadata'].get('is_bold', False),
                'hierarchy_level': result['metadata'].get('hierarchy_level', 'unknown'),
                'extraction_method': result['metadata'].get('extraction_method', 'unknown')
            })
        
        logger.info(f"Hybrid search returned {len(formatted_results)} results")
        return formatted_results