#!/usr/bin/env python3
"""
Test to specifically target the chunk with complete content
"""

import yaml
from services.enhanced_search import EnhancedSearchEngine

def load_config():
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    current_mode = config.get("current_mode", "medium")
    mode_settings = config.get("modes", {}).get(current_mode, {})
    return {**config, **mode_settings}

def test_specific_chunk():
    print("=== Testing Specific Chunk Search ===\n")
    
    config = load_config()
    search_engine = EnhancedSearchEngine(
        config=config,
        index_dir="index",
        extracted_docs_dir="extracted_docs"
    )
    
    # Test the descriptive title directly
    queries = [
        "Additional frontend server tasks",
        "This section describes the additional frontend server tasks that must be disabled",
        "frontend server tasks that must be disabled"
    ]
    
    for query in queries:
        print(f"Query: '{query}'")
        results = search_engine.search_with_exact_title_matching(query, top_k=1)
        
        if results:
            result = results[0]
            content = result.get('text', '')
            title = result.get('metadata', {}).get('title', 'N/A')
            
            print(f"  Found: \"{title}\"")
            print(f"  Content length: {len(content)}")
            
            if len(content) > 1000:
                print("  ✅ SUCCESS: Found substantial content")
                print(f"  Content preview: {content[:300]}...")
            else:
                print("  ❌ WARNING: Short content")
                print(f"  Content: {content}")
        else:
            print("  No results found")
        
        print()

if __name__ == "__main__":
    test_specific_chunk()