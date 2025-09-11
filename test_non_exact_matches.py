#!/usr/bin/env python3
"""
Test what happens when titles don't exactly match
"""

import asyncio
import yaml
from services.rag_service import RAGService
from services.chat_service import ChatService

def load_config():
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    current_mode = config.get("current_mode", "medium")
    mode_settings = config.get("modes", {}).get(current_mode, {})
    return {**config, **mode_settings}

async def test_non_exact_matches():
    print("=== Testing Non-Exact Title Matches ===\n")
    
    config = load_config()
    rag_service = RAGService(config)
    chat_service = ChatService(rag_service)
    session = chat_service.create_session("Non-Exact Test")
    
    # Test cases with variations of exact titles
    test_cases = [
        # Exact match for comparison
        {"query": "Additional frontend server tasks", "type": "EXACT"},
        
        # Partial matches
        {"query": "frontend server tasks", "type": "PARTIAL"},
        {"query": "additional frontend tasks", "type": "PARTIAL"},
        {"query": "server tasks", "type": "PARTIAL"},
        
        # Similar but not exact
        {"query": "frontend server task", "type": "SIMILAR (singular)"},
        {"query": "Additional frontend servers tasks", "type": "SIMILAR (extra s)"},
        
        # Questions about the topic
        {"query": "What are the additional frontend server tasks?", "type": "QUESTION"},
        {"query": "How to configure frontend server tasks?", "type": "QUESTION"},
        
        # Completely different
        {"query": "Database configuration", "type": "DIFFERENT TOPIC"},
    ]
    
    for test_case in test_cases:
        query = test_case["query"]
        query_type = test_case["type"]
        
        print(f"Query ({query_type}): '{query}'")
        print("-" * 60)
        
        try:
            response = await chat_service.send_message(session.session_id, query)
            
            content_length = len(response.message.content)
            confidence = response.confidence_score
            sources = len(response.sources)
            
            # Determine behavior type
            is_exact_match = confidence == 1.0
            is_high_confidence = confidence > 0.8
            is_llm_generated = confidence < 1.0 and content_length > 100
            
            behavior = "UNKNOWN"
            if is_exact_match:
                behavior = "EXACT MATCH (Direct Content)"
            elif is_high_confidence:
                behavior = "HIGH CONFIDENCE (LLM + Context)"
            elif is_llm_generated:
                behavior = "STANDARD RAG (LLM + Context)"
            else:
                behavior = "LOW CONFIDENCE"
            
            print(f"  Behavior: {behavior}")
            print(f"  Confidence: {confidence:.3f}")
            print(f"  Length: {content_length} chars")
            print(f"  Sources: {sources}")
            
            # Show content preview
            preview = response.message.content[:150].replace('\n', ' ').strip()
            print(f"  Preview: {preview}...")
            
        except Exception as e:
            print(f"  ERROR: {e}")
        
        print()

if __name__ == "__main__":
    asyncio.run(test_non_exact_matches())