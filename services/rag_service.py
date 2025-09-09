from pathlib import Path
from typing import List, Dict, Any
from pdf_processing import PDFProcessor, PDFSearcher
from loguru import logger

class RAGService:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = Path(config.get("output_dir", "extracted_docs"))
        self.index_dir = Path(config.get("index_path", "index"))
        self.docs_path = Path(config.get("docs_path", "docs"))

        self.pdf_processor = PDFProcessor(
            output_dir=str(self.output_dir),
            index_dir=str(self.index_dir)
        )
        self.pdf_searcher = None
        self._load_searcher()

    def _load_searcher(self):
        if self.index_dir.exists() and any(self.index_dir.iterdir()):
            try:
                self.pdf_searcher = PDFSearcher(
                    index_dir=str(self.index_dir),
                    extracted_docs_dir=str(self.output_dir)
                )
                logger.info("PDFSearcher loaded successfully.")
            except Exception as e:
                logger.warning(f"Could not load PDFSearcher, indexes might be missing: {e}")
        else:
            logger.warning("Index directory is empty. PDFSearcher not loaded.")

    def index_documents(self):
        logger.info(f"Starting batch processing of PDFs in {self.docs_path}")
        results = self.pdf_processor.process_batch(str(self.docs_path))
        logger.info(f"Batch processing completed. Results: {results}")
        # After indexing, reload the searcher to include the new indexes
        self._load_searcher()
        return results

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        if not self.pdf_searcher:
            logger.error("PDFSearcher is not available. Make sure to index documents first.")
            return []
        
        logger.info(f"Searching for query: '{query}'")
        
        # Use configuration-based top_k values for better retrieval
        config_top_k = self.config.get("top_k_faiss", top_k)
        actual_top_k = max(config_top_k, top_k)
        
        search_results = self.pdf_searcher.search(query, top_k=actual_top_k)
        
        # Format results to be consistent with the rest of the application
        formatted_results = []
        for res in search_results:
            formatted_results.append({
                "text": res.get("content", ""),
                "metadata": {
                    "filename": res.get("document_id", "Unknown"),
                    "page_number": res.get("page", 1),
                    "section_title": res.get("title", "Unknown Section"),
                    "relevance_score": res.get("final_score", 0.0),
                    "search_type": res.get("search_type", "unknown"),
                    "match_type": res.get("match_type", "unknown"),
                    "is_heading_result": res.get("is_heading_result", False),
                    "font_size": res.get("font_size", 0),
                    "is_bold": res.get("is_bold", False)
                }
            })
        return formatted_results[:top_k]

    def get_available_documents(self):
        if not self.pdf_searcher:
            return []
        return self.pdf_searcher.list_documents()
