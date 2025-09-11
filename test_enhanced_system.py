#!/usr/bin/env python3
"""
Test script for enhanced page-aware chunking and exact title matching
"""

import yaml
import logging
from pathlib import Path
from pdf_processing.enhanced_processor import EnhancedPDFProcessor
from services.enhanced_search import EnhancedSearchEngine

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_config():
    """Load configuration"""
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    current_mode = config.get("current_mode", "medium")
    mode_settings = config.get("modes", {}).get(current_mode, {})
    
    return {**config, **mode_settings}

def test_enhanced_processing():
    """Test enhanced PDF processing"""
    print("=== Testing Enhanced PDF Processing ===\n")
    
    config = load_config()
    processor = EnhancedPDFProcessor(
        output_dir="extracted_docs",
        index_dir="index",
        max_chunk_size=config.get('max_chunk_size', 8000)
    )
    
    # Test with one document
    test_doc = "docs/SRM Installation and Configuration Guide.pdf"
    doc_id = "SRM_Installation_and_Configuration_Guide"
    
    if Path(test_doc).exists():
        print(f"Processing: {test_doc}")
        result = processor.process_document(test_doc, doc_id)
        
        print("Processing Results:")
        print(f"- Total chunks: {result['total_chunks']}")
        print(f"- Chunk types: {result['chunk_types']}")
        print(f"- Content length: {result['content_length']}")
        print(f"- Extraction method: {result['extraction_method']}")
        print()
        
        return True
    else:
        print(f"Test document not found: {test_doc}")
        return False

def test_exact_title_matching():
    """Test exact title matching functionality"""
    print("=== Testing Exact Title Matching ===\n")
    
    config = load_config()
    search_engine = EnhancedSearchEngine(
        config=config,
        index_dir="index",
        extracted_docs_dir="extracted_docs"
    )
    
    # Test queries for exact title matches
    test_queries = [
        "Installing and configuring the Frontend host",
        "Dell SRM virtual appliance installation overview",
        "Customizing vApp Configuration",
        "Using the Discovery Wizard",
        "Verifying that the services are running",
        "how to install frontend host",  # Variation test
        "configuration guide"  # Partial match test
    ]
    
    for query in test_queries:
        print(f"Query: '{query}'")
        
        try:
            results = search_engine.search_with_exact_title_matching(
                query=query,
                top_k=3
            )
            
            if results:
                print(f"Found {len(results)} results:")
                for i, result in enumerate(results, 1):
                    metadata = result.get('metadata', {})
                    print(f"  {i}. Title: {metadata.get('title', 'N/A')}")
                    print(f"     Type: {metadata.get('chunk_type', 'N/A')}")
                    print(f"     Match: {metadata.get('match_type', 'N/A')}")
                    print(f"     Score: {result.get('score', 0):.3f}")
                    print(f"     Content length: {len(result.get('text', ''))}")
                    if metadata.get('match_explanation'):
                        print(f"     Explanation: {metadata['match_explanation']}")
                    print()
            else:
                print("  No results found")
                print()
                
        except Exception as e:
            print(f"  Error: {e}")
            print()

def test_chunk_analysis():
    """Analyze the enhanced chunks"""
    print("=== Analyzing Enhanced Chunks ===\n")
    
    doc_dir = Path("extracted_docs/SRM_Installation_and_Configuration_Guide")
    
    # Check for enhanced chunks
    enhanced_chunks_path = doc_dir / "enhanced_chunks_v2.json"
    analysis_path = doc_dir / "chunk_analysis.json"
    
    if enhanced_chunks_path.exists():
        import json
        
        with open(enhanced_chunks_path, 'r', encoding='utf-8') as f:
            chunks = json.load(f)
        
        print(f"Enhanced chunks found: {len(chunks)}")
        
        # Analyze chunk types
        chunk_types = {}
        for chunk in chunks:
            chunk_type = chunk.get('chunk_type', 'unknown')
            chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1
        
        print("Chunk type distribution:")
        for chunk_type, count in sorted(chunk_types.items()):
            print(f"  {chunk_type}: {count}")
        print()
        
        # Show some example exact title matches
        print("Sample exact title matches:")
        for chunk in chunks[:5]:
            title = chunk.get('title', 'N/A')
            exact_match = chunk.get('exact_title_match', 'N/A')
            chunk_type = chunk.get('chunk_type', 'N/A')
            print(f"  '{title}' -> '{exact_match}' ({chunk_type})")
        print()
        
        # Show chunk analysis if available
        if analysis_path.exists():
            with open(analysis_path, 'r', encoding='utf-8') as f:
                analysis = json.load(f)
            
            print("Chunk Analysis Summary:")
            print(f"- Total chunks: {analysis.get('total_chunks', 0)}")
            print(f"- Size distribution: {analysis.get('size_distribution', {})}")
            print(f"- Page distribution: {analysis.get('page_distribution', {})}")
            print(f"- Procedure chunks: {analysis.get('procedure_chunks', 0)}")
            print()
    else:
        print("No enhanced chunks found. Run processing first.")

def test_comparison():
    """Compare old vs new chunking"""
    print("=== Comparing Old vs New Chunking ===\n")
    
    doc_dir = Path("extracted_docs/SRM_Installation_and_Configuration_Guide")
    
    old_chunks_path = doc_dir / "enhanced_chunks.json"
    new_chunks_path = doc_dir / "enhanced_chunks_v2.json"
    
    if old_chunks_path.exists() and new_chunks_path.exists():
        import json
        
        with open(old_chunks_path, 'r', encoding='utf-8') as f:
            old_chunks = json.load(f)
        
        with open(new_chunks_path, 'r', encoding='utf-8') as f:
            new_chunks = json.load(f)
        
        print(f"Old system: {len(old_chunks)} chunks")
        print(f"New system: {len(new_chunks)} chunks")
        
        # Compare chunk types
        old_types = {}
        new_types = {}
        
        for chunk in old_chunks:
            chunk_type = chunk.get('chunk_type', 'unknown')
            old_types[chunk_type] = old_types.get(chunk_type, 0) + 1
        
        for chunk in new_chunks:
            chunk_type = chunk.get('chunk_type', 'unknown')
            new_types[chunk_type] = new_types.get(chunk_type, 0) + 1
        
        print("\nChunk type comparison:")
        print("Old system:")
        for chunk_type, count in sorted(old_types.items()):
            print(f"  {chunk_type}: {count}")
        
        print("New system:")
        for chunk_type, count in sorted(new_types.items()):
            print(f"  {chunk_type}: {count}")
        print()
    else:
        print("Cannot compare - missing chunk files")

if __name__ == "__main__":
    print("Enhanced Chunking and Search Test Suite")
    print("=" * 50)
    print()
    
    # Test 1: Enhanced Processing
    try:
        if test_enhanced_processing():
            print("[SUCCESS] Enhanced processing completed successfully\n")
        else:
            print("[FAILED] Enhanced processing failed\n")
    except Exception as e:
        print(f"[ERROR] Enhanced processing error: {e}\n")
    
    # Test 2: Chunk Analysis
    try:
        test_chunk_analysis()
        print("[SUCCESS] Chunk analysis completed\n")
    except Exception as e:
        print(f"[ERROR] Chunk analysis error: {e}\n")
    
    # Test 3: Exact Title Matching
    try:
        test_exact_title_matching()
        print("[SUCCESS] Exact title matching test completed\n")
    except Exception as e:
        print(f"[ERROR] Exact title matching error: {e}\n")
    
    # Test 4: Comparison
    try:
        test_comparison()
        print("[SUCCESS] Comparison completed\n")
    except Exception as e:
        print(f"[ERROR] Comparison error: {e}\n")
    
    print("Test suite completed!")