#!/usr/bin/env python3
"""
Test exact title matching - should return raw section content without LLM processing
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

async def test_exact_title_responses():
    print("=== Testing Exact Title Match Responses ===\n")
    
    config = load_config()
    rag_service = RAGService(config)
    chat_service = ChatService(rag_service)
    session = chat_service.create_session("Exact Title Test")
    
    # Test cases - exact titles
    test_cases = [
        "Installing and configuring the Frontend host",
        "Verifying that the services are running"
    ]
    
    for query in test_cases:
        print(f"\n" + "="*60)
        print(f"Query: '{query}'")
        print("="*60)
        
        try:
            response = await chat_service.send_message(session.session_id, query)
            
            print(f"Response Length: {len(response.message.content)} characters")
            print(f"Confidence Score: {response.confidence_score}")
            print(f"Number of Sources: {len(response.sources)}")
            
            # Check if it's returning raw content (starts with ##)
            content = response.message.content
            if content.startswith("##") or "## " in content[:50]:
                print("SUCCESS: LOOKS LIKE RAW SECTION CONTENT")
            else:
                print("WARNING: LOOKS LIKE LLM-PROCESSED RESPONSE")
            
            print("\nFirst 400 characters of response:")
            print("-" * 50)
            print(content[:400] + "..." if len(content) > 400 else content)
            print("-" * 50)
            
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_exact_title_responses())