#!/usr/bin/env python3
"""
Re-processes all PDF documents to apply the updated chunking logic.
"""
import yaml
import logging
from services.rag_service import RAGService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def reindex_documents():
    """
    Clears existing indexes and re-processes all documents in the 'docs' folder.
    """
    print("🚀 Starting document re-processing...")
    print("="*50)
    
    try:
        # Load configuration
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        logging.info("✅ Configuration loaded.")
        
        # Initialize RAG Service, which will handle the processing
        rag_service = RAGService(config)
        
        # The index_documents method will find all PDFs in the configured 'docs_path',
        # process them with the updated logic, and save the new indexes.
        logging.info(f"Scanning for documents in '{config.get('docs_path', 'docs')}'...")
        results = rag_service.index_documents()
        
        print("\n📊 Re-processing complete. Summary:")
        print("-" * 30)
        for result in results:
            if result.get('status') == 'failed':
                print(f"❌ Document: {result['document_id']}")
                print(f"   Error: {result['error']}")
            else:
                print(f"✅ Document: {result['document_id']}")
                print(f"   Chunks created: {result['total_chunks']}")
                print(f"   Content length: {result['content_length']} chars")
        
        print("\n🏁 All documents have been re-processed successfully!")
        
    except FileNotFoundError:
        logging.error("❌ config.yaml not found. Please ensure the configuration file exists.")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}", exc_info=True)

if __name__ == "__main__":
    reindex_documents()

