#!/usr/bin/env python3
"""
Test the specific "Additional frontend server tasks" exact match
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

async def test_additional_frontend_tasks():
    print("=== Testing 'Additional frontend server tasks' ===\n")
    
    config = load_config()
    rag_service = RAGService(config)
    chat_service = ChatService(rag_service)
    session = chat_service.create_session("Frontend Tasks Test")
    
    query = "Additional frontend server tasks"
    print(f"Query: '{query}'\n")
    
    try:
        response = await chat_service.send_message(session.session_id, query)
        
        print(f"Response Length: {len(response.message.content)} characters")
        print(f"Confidence Score: {response.confidence_score}")
        print(f"Number of Sources: {len(response.sources)}")
        
        content = response.message.content
        print(f"Content starts with markdown header: {content.startswith('##') or '## ' in content[:50]}")
        
        print(f"\nFull Response:")
        print("="*80)
        print(content)
        print("="*80)
        
        print(f"\nSources:")
        for i, source in enumerate(response.sources, 1):
            print(f"{i}. {source.filename} (Page {source.page_number})")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_additional_frontend_tasks())