#!/usr/bin/env python3
"""
Quick test of exact title matching across documents
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

async def test_exact_titles():
    print("=== Quick Test: Exact Title Matching Results ===\n")
    
    config = load_config()
    rag_service = RAGService(config)
    chat_service = ChatService(rag_service)
    session = chat_service.create_session("Quick Test")
    
    # Test a few key exact titles
    test_queries = [
        "Additional frontend server tasks",
        "Installing and configuring the Frontend host", 
        "Verifying that the services are running",
        "Adding MySQL grants to the databases"
    ]
    
    for query in test_queries:
        response = await chat_service.send_message(session.session_id, query)
        
        is_exact = response.confidence_score == 1.0
        print(f"'{query}':")
        print(f"  Exact Match: {'YES' if is_exact else 'NO'}")
        print(f"  Confidence: {response.confidence_score}")
        print(f"  Content Length: {len(response.message.content)} chars")
        if response.sources:
            print(f"  Document: {response.sources[0].filename}")
        print()

if __name__ == "__main__":
    asyncio.run(test_exact_titles())