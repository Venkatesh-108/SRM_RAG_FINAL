#!/usr/bin/env python3
"""
Simple test to see exact title content directly
"""

import yaml
from services.enhanced_search import EnhancedSearchEngine

def load_config():
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    current_mode = config.get("current_mode", "medium")
    mode_settings = config.get("modes", {}).get(current_mode, {})
    return {**config, **mode_settings}

def test_exact_title_content():
    print("=== Testing Direct Title Content ===\n")
    
    config = load_config()
    search_engine = EnhancedSearchEngine(
        config=config,
        index_dir="index",
        extracted_docs_dir="extracted_docs"
    )
    
    # Test exact title
    query = "Installing and configuring the Frontend host"
    print(f"Query: '{query}'\n")
    
    results = search_engine.search_with_exact_title_matching(query, top_k=1)
    
    if results:
        result = results[0]
        print(f"Match type: {result.get('metadata', {}).get('match_type', 'N/A')}")
        print(f"Is complete section: {result.get('metadata', {}).get('is_complete_section', 'N/A')}")
        print(f"Content length: {len(result.get('text', ''))}")
        print("\n=== FULL SECTION CONTENT ===")
        print(result.get('text', ''))
        print("=== END CONTENT ===\n")
        
        # Test another exact title
        query2 = "Verifying that the services are running"
        print(f"\nQuery 2: '{query2}'\n")
        results2 = search_engine.search_with_exact_title_matching(query2, top_k=1)
        
        if results2:
            result2 = results2[0]
            print(f"Match type: {result2.get('metadata', {}).get('match_type', 'N/A')}")
            print(f"Content length: {len(result2.get('text', ''))}")
            print("\n=== FULL SECTION CONTENT ===")
            print(result2.get('text', ''))
            print("=== END CONTENT ===\n")
    else:
        print("No results found")

if __name__ == "__main__":
    test_exact_title_content()