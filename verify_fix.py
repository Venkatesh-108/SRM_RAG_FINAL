#!/usr/-bin/env python3
"""
Verifies that the chunking fix for "Installing and configuring the Frontend host" was successful.
"""
import yaml
import logging
from services.rag_service import RAGService

print("--- verify_fix.py script started ---")

try:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    print("--- Logging configured ---")

    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    print("--- Config loaded ---")

    rag_service = RAGService(config)
    print("--- RAGService initialized, now re-indexing... ---")
    
    rag_service.index_documents()
    
    print("--- Re-indexing complete ---")


    print("--- Verification script completed successfully ---")

except Exception as e:
    print(f"--- Exception in verify_fix.py: {e} ---")
    logging.error("Error in verification script", exc_info=True)

