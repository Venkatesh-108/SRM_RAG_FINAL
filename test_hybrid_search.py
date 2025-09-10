#!/usr/bin/env python3
"""
Test script for the hybrid search functionality
"""

import yaml
import logging
from pathlib import Path
from services.hybrid_search import HybridSearchEngine
from services.rag_service import RAGService

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration"""
    config_path = Path("config.yaml")
    if not config_path.exists():
        logger.error("config.yaml not found!")
        return None
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    current_mode = config.get("current_mode", "medium")
    mode_settings = config.get("modes", {}).get(current_mode, {})
    
    return {**config, **mode_settings}

def test_hybrid_search_direct():
    """Test hybrid search engine directly"""
    logger.info("=== Testing Hybrid Search Engine Directly ===")
    
    config = load_config()
    if not config:
        return False
    
    try:
        # Initialize hybrid search engine
        hybrid_engine = HybridSearchEngine(
            config=config,
            index_dir="index",
            extracted_docs_dir="extracted_docs"
        )
        
        # Test search
        test_queries = [
            "upgrade SRM",
            "install preconfigured alerts",
            "configure frontend server"
        ]
        
        for query in test_queries:
            logger.info(f"\n--- Testing query: '{query}' ---")
            results = hybrid_engine.hybrid_search(query, top_k=3)
            
            logger.info(f"Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                logger.info(f"{i}. Score: {result.get('final_score', 0):.3f}")
                logger.info(f"   Title: {result.get('title', 'N/A')}")
                logger.info(f"   Search types: {result.get('search_types', [])}")
                logger.info(f"   BM25: {result.get('bm25_score', 0):.3f}, "
                          f"FAISS: {result.get('faiss_score', 0):.3f}, "
                          f"Rerank: {result.get('rerank_score', 0):.3f}")
                logger.info(f"   Content: {result.get('content', '')[:100]}...")
                logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"Hybrid search test failed: {e}")
        return False

def test_rag_service_integration():
    """Test RAG service with hybrid search integration"""
    logger.info("=== Testing RAG Service Integration ===")
    
    config = load_config()
    if not config:
        return False
    
    try:
        # Initialize RAG service
        rag_service = RAGService(config)
        
        # Test search through RAG service
        test_queries = [
            "upgrade SRM",
            "install alerts"
        ]
        
        for query in test_queries:
            logger.info(f"\n--- Testing RAG service query: '{query}' ---")
            results = rag_service.search(query, top_k=3)
            
            logger.info(f"Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                metadata = result.get('metadata', {})
                logger.info(f"{i}. Score: {metadata.get('relevance_score', 0):.3f}")
                logger.info(f"   Title: {metadata.get('section_title', 'N/A')}")
                logger.info(f"   Search type: {metadata.get('search_type', 'N/A')}")
                logger.info(f"   Text: {result.get('text', '')[:100]}...")
                logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"RAG service test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("Starting hybrid search tests...")
    
    # Check if indexes exist
    index_dir = Path("index")
    if not index_dir.exists() or not any(index_dir.glob("*.faiss")):
        logger.warning("No FAISS indexes found. Please run indexing first:")
        logger.warning("python app.py index")
        return
    
    # Run tests
    success = True
    
    # Test 1: Direct hybrid search engine
    if not test_hybrid_search_direct():
        success = False
    
    # Test 2: RAG service integration
    if not test_rag_service_integration():
        success = False
    
    if success:
        logger.info("✅ All tests passed! Hybrid search is working correctly.")
    else:
        logger.error("❌ Some tests failed. Check the logs above.")

if __name__ == "__main__":
    main()