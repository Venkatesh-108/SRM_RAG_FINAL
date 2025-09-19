#!/usr/bin/env python3
"""
Test script to investigate duplicate search results
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.rag_service import RAGService
from pathlib import Path
import yaml
import json

def main():
    print("Testing search for 'Installing on Windows Server'...")
    
    # Load configuration
    config_path = Path("config.yaml")
    if not config_path.is_file():
        print(f"Configuration file not found at: {config_path}")
        return
    
    print("Loading configuration...")
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    print("Initializing RAG service...")
    try:
        rag_service = RAGService(config)
        print("RAG service initialized successfully")
    except Exception as e:
        print(f"Error initializing RAG service: {e}")
        return
    
    # Test search
    query = "Installing on Windows Server"
    print(f"Searching for: '{query}'")
    
    results = rag_service.search(query, top_k=10)
    
    print(f"Found {len(results)} results:")
    for i, result in enumerate(results):
        content = result.get("text", "")
        metadata = result.get("metadata", {})
        title = metadata.get("section_title", "Unknown")
        filename = metadata.get("filename", "Unknown")
        
        print(f"\n--- Result {i+1} ---")
        print(f"Title: {title}")
        print(f"Filename: {filename}")
        print(f"Content length: {len(content)}")
        print(f"Content preview: {content[:200]}...")
    
    # Check if there are duplicates
    seen_titles = set()
    duplicates = []
    for result in results:
        title = result.get("metadata", {}).get("section_title", "").lower().strip()
        if title in seen_titles:
            duplicates.append(title)
        seen_titles.add(title)
    
    if duplicates:
        print(f"\n⚠️  Found duplicate titles: {duplicates}")
    else:
        print("\n✅ No duplicate titles found")

if __name__ == "__main__":
    main()
