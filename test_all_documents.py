#!/usr/bin/env python3
"""
Test exact title matching across all reindexed documents
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

async def test_exact_title_matching_all_docs():
    print("=== Testing Exact Title Matching Across All Documents ===\n")
    
    config = load_config()
    rag_service = RAGService(config)
    chat_service = ChatService(rag_service)
    session = chat_service.create_session("Cross-Document Test")
    
    # Test queries from different documents
    test_queries = [
        # From SRM Deploying Additional Frontend Servers
        "Additional frontend server tasks",
        "Adding MySQL grants to the databases",
        
        # From SRM Installation and Configuration Guide  
        "Installing and configuring the Frontend host",
        "Verifying that the services are running",
        "Configure SSL",
        
        # From SRM Upgrade Guide
        "Upgrade Prerequisites",
        "Database backup and restoration",
        "Post-upgrade validation"
    ]
    
    for query in test_queries:
        print(f"Query: '{query}'")
        print("-" * 60)
        
        try:
            response = await chat_service.send_message(session.session_id, query)
            
            content_length = len(response.message.content)
            confidence = response.confidence_score
            sources = len(response.sources)
            
            # Check if it looks like exact match behavior
            is_exact_match = confidence == 1.0 and content_length > 200
            
            print(f"  Length: {content_length} chars")
            print(f"  Confidence: {confidence}")
            print(f"  Sources: {sources}")
            print(f"  Exact Match: {'YES' if is_exact_match else 'NO'}")
            
            if is_exact_match:
                # Show first source document
                if response.sources:
                    source = response.sources[0]
                    print(f"  Document: {source.filename}")
                    print(f"  Page: {source.page_number}")
                
                # Show content preview
                preview = response.message.content[:150].replace('\n', ' ')
                print(f"  Preview: {preview}...")
            
        except Exception as e:
            print(f"  ERROR: {e}")
        
        print()

if __name__ == "__main__":
    asyncio.run(test_exact_title_matching_all_docs())