from pathlib import Path
from unstructured.partition.auto import partition
from unstructured.documents.elements import Element
from typing import List
from loguru import logger

from config import config

def load_documents() -> List[Element]:
    docs_path = Path(config["docs_path"])
    if not docs_path.is_dir():
        logger.warning(f"Docs directory not found at: {docs_path}")
        return []

    supported_formats = [".pdf", ".md"]
    doc_files = [f for f in docs_path.glob("**/*") if f.is_file() and f.suffix in supported_formats]

    elements = []
    for doc_file in doc_files:
        logger.info(f"Processing file: {doc_file}")
        try:
            file_elements = partition(filename=str(doc_file))
            elements.extend(file_elements)
        except Exception as e:
            logger.error(f"Failed to process {doc_file}: {e}")
    
    return elements

if __name__ == '__main__':
    # Create a dummy doc for testing
    docs_dir = Path(config["docs_path"])
    docs_dir.mkdir(exist_ok=True)
    dummy_file = docs_dir / "dummy_doc.md"
    dummy_file.write_text("# Test Document\n\nThis is a test paragraph.\n\n- Item 1\n- Item 2")

    loaded_elements = load_documents()
    print(f"Loaded {len(loaded_elements)} elements.")
    for el in loaded_elements:
        print(f"- Type: {type(el).__name__}, Content: '{el.text[:50]}...'")
    
    # Clean up
    dummy_file.unlink()
    docs_dir.rmdir()
