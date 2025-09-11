#!/usr/bin/env python3
"""
Simple test to see what happens when title matches
"""

import yaml
import asyncio
from services.rag_service import RAGService
from services.chat_service import ChatService
from services.ollama_service import generate_answer_with_ollama

def load_config():
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    current_mode = config.get("current_mode", "medium")
    mode_settings = config.get("modes", {}).get(current_mode, {})
    return {**config, **mode_settings}

async def test_title_match():
    print("=== Testing Title Match Response ===\n")
    
    config = load_config()
    rag_service = RAGService(config)
    chat_service = ChatService(rag_service)
    
    # Test exact title match
    query = "Installing and configuring the Frontend host"
    print(f"Query: '{query}'\n")
    
    # Step 1: Test direct search
    print("1. Direct search results:")
    search_results = rag_service.search(query)
    print(f"Found {len(search_results)} chunks")
    
    for i, chunk in enumerate(search_results[:2], 1):  # Show first 2 chunks
        metadata = chunk.get('metadata', {})
        print(f"  Chunk {i}:")
        print(f"    Title: {metadata.get('title', 'N/A')}")
        print(f"    Search type: {metadata.get('search_type', 'N/A')}")
        print(f"    Match type: {metadata.get('match_type', 'N/A')}")
        print(f"    Is complete section: {metadata.get('is_complete_section', 'N/A')}")
        print(f"    Content length: {len(chunk.get('text', ''))}")
        print(f"    Content preview: {chunk.get('text', '')[:200]}...")
        print()
    
    # Step 2: Test answer generation
    print("2. Answer generation:")
    answer, confidence, validation = generate_answer_with_ollama(query, search_results, config)
    print(f"Answer length: {len(answer)}")
    print(f"Confidence: {confidence}")
    print(f"Answer preview: {answer[:300]}...")
    print()
    
    # Step 3: Test via chat service
    print("3. Via chat service:")
    session = chat_service.create_session("Test Session")
    response = await chat_service.send_message(session.session_id, query)
    
    print(f"Response length: {len(response.message.content)}")
    print(f"Confidence: {response.confidence_score}")
    print(f"Sources: {len(response.sources)}")
    print(f"Response preview: {response.message.content[:300]}...")

if __name__ == "__main__":
    asyncio.run(test_title_match())