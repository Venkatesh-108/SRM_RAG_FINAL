#!/usr/bin/env python3
"""
Test script to analyze page-aware chunking opportunities
"""

import json
import re
from pathlib import Path
from collections import defaultdict

def analyze_font_patterns():
    """Analyze font patterns across all documents"""
    
    docs = [
        "SRM_Installation_and_Configuration_Guide",
        "SRM_Upgrade_Guide", 
        "SRM_Deploying_Additional_Frontend_Servers"
    ]
    
    print("=== FONT SIZE ANALYSIS ===\n")
    
    for doc in docs:
        font_file = Path(f"extracted_docs/{doc}/font_analysis.json")
        
        if font_file.exists():
            with open(font_file, 'r') as f:
                font_data = json.load(f)
            
            print(f"## {doc}")
            print(f"Body size: {font_data['body_size']}")
            print(f"Heading sizes: {font_data['heading_sizes']}")
            print(f"Total headings detected: {len(font_data['heading_map'])}")
            
            # Analyze heading levels by size
            size_levels = defaultdict(list)
            for heading, info in font_data['heading_map'].items():
                size = info['size']
                page = info['page']
                size_levels[size].append((heading[:50] + "..." if len(heading) > 50 else heading, page))
            
            print("Heading hierarchy by font size:")
            for size in sorted(size_levels.keys(), reverse=True):
                print(f"  {size}pt: {len(size_levels[size])} headings")
                for heading, page in size_levels[size][:3]:  # Show first 3
                    print(f"    - '{heading}' (page {page})")
            print()

def analyze_page_breaks():
    """Analyze how current chunks handle page breaks"""
    
    docs = [
        "SRM_Installation_and_Configuration_Guide",
        "SRM_Upgrade_Guide"
    ]
    
    print("=== PAGE BREAK ANALYSIS ===\n")
    
    for doc in docs:
        chunks_file = Path(f"extracted_docs/{doc}/enhanced_chunks.json")
        
        if chunks_file.exists():
            with open(chunks_file, 'r', encoding='utf-8') as f:
                chunks = json.load(f)
            
            print(f"## {doc}")
            print(f"Total chunks: {len(chunks)}")
            
            # Analyze page spans
            page_spans = []
            long_chunks = []
            
            for chunk in chunks:
                pages = chunk.get('pages', [chunk.get('page', 1)])
                if len(pages) > 1:
                    page_spans.append((chunk['title'], pages, len(chunk['content'])))
                
                if len(chunk['content']) > 8000:  # Large chunks
                    long_chunks.append((
                        chunk['title'], 
                        len(chunk['content']), 
                        chunk.get('page', 1),
                        chunk.get('chunk_type', 'unknown')
                    ))
            
            print(f"Chunks spanning multiple pages: {len(page_spans)}")
            for title, pages, content_len in page_spans[:3]:
                print(f"  - '{title}' spans pages {pages[0]}-{pages[-1]} ({content_len} chars)")
            
            print(f"Large chunks (>8000 chars): {len(long_chunks)}")
            for title, content_len, page, chunk_type in long_chunks[:3]:
                print(f"  - '{title}' ({content_len} chars, page {page}, {chunk_type})")
            print()

def suggest_page_aware_improvements():
    """Suggest improvements for page-aware chunking"""
    
    print("=== SUGGESTED IMPROVEMENTS ===\n")
    
    print("## Font Size Based Chunking:")
    print("- Main headings: 20-28pt (Chapter level)")
    print("- Sub headings: 16pt (Section level)")  
    print("- Minor headings: 11.5-14pt (Sub-section level)")
    print("- Body text: 9pt")
    print()
    
    print("## Page-Aware Chunking Strategy:")
    print("1. Use font size hierarchy as primary chunk boundaries")
    print("2. Avoid breaking procedures/steps across chunks")
    print("3. Consider page boundaries for very long sections")
    print("4. Preserve tables and figures within chunks")
    print("5. Add page range metadata to chunks")
    print()
    
    print("## Recommended Chunk Types:")
    print("- chapter_complete: Full chapter (20-28pt headings)")
    print("- section_complete: Major sections (16-20pt headings)")
    print("- subsection: Minor sections (11.5-16pt headings)")
    print("- procedure: Step-by-step procedures")
    print("- table: Tables and structured data")
    print()

if __name__ == "__main__":
    analyze_font_patterns()
    analyze_page_breaks()
    suggest_page_aware_improvements()