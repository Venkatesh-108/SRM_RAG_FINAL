#!/usr/bin/env python3
"""
Re-processes all PDF documents to apply the updated chunking logic.
"""
import yaml
import logging
from services.rag_service import RAGService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def reindex_documents(force=False):
    """
    Clears existing indexes and re-processes all documents in the 'docs' folder.
    """
    print("Starting document re-processing...")
    print("="*50)
    
    try:
        # Load configuration
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        logging.info("Configuration loaded.")
        
        # Initialize RAG Service, which will handle the processing
        rag_service = RAGService(config)
        
        # The index_documents method will find all PDFs in the configured 'docs_path',
        # process them with the updated logic, and save the new indexes.
        logging.info(f"Scanning for documents in '{config.get('docs_path', 'docs')}'...")
        response = rag_service.index_documents(force_reindex=force)
        
        print("\nRe-processing complete. Summary:")
        print("-" * 30)
        
        if response.get('status') == 'up_to_date':
            print("No new or modified documents to process.")
        elif response.get('results'):
            for result in response['results']:
                if result.get('status') == 'failed':
                    print(f"FAILED Document: {result.get('document_id', 'Unknown')}")
                    print(f"   Error: {result.get('error', 'No error details')}")
                else:
                    print(f"SUCCESS Document: {result.get('document_id', 'Unknown')}")
                    print(f"   Chunks created: {result.get('total_chunks', 'N/A')}")
                    print(f"   Content length: {result.get('content_length', 'N/A')} chars")
        else:
            print("No results to display.")
        
        print("\nAll documents have been re-processed successfully!")
        
    except FileNotFoundError:
        logging.error("config.yaml not found. Please ensure the configuration file exists.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Re-index all PDF documents.")
    parser.add_argument('--force', action='store_true', help='Force re-indexing even if files are not modified.')
    args = parser.parse_args()
    
    reindex_documents(force=args.force)

