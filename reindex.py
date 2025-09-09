#!/usr/bin/env python3
"""
Simple script to reindex documents
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.rag_service import RAGService
from pathlib import Path
import yaml
from loguru import logger

def load_config():
    config_path = Path("config.yaml")
    if not config_path.is_file():
        logger.error(f"Config file not found at: {config_path}")
        return {}
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"Loaded configuration for mode: '{config.get('current_mode', 'unknown')}'")
    return config

def main():
    print("Starting the indexing process...")
    
    # Load configuration
    config = load_config()
    
    # Initialize RAG service
    rag_service = RAGService(config)
    
    # Index documents
    results = rag_service.index_documents()
    
    print(f"Successfully indexed. Results: {results}")

if __name__ == "__main__":
    main()
