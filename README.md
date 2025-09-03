# SRM RAG CLI

This is a command-line interface for querying Dell SRM guides using a RAG architecture with advanced chunking, hybrid retrieval, and Ollama integration.

## Setup

1.  Create a virtual environment:
    ```bash
    python -m venv venv
    ```

2.  Activate the virtual environment:
    ```bash
    # Windows
    venv\Scripts\activate.bat
    
    # Linux/Mac
    source venv/bin/activate
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

4.  Place your Dell SRM guide documents (in PDF or Markdown format) into the `docs` directory.

## Usage

1.  **Index the documents:**
    ```bash
    python app.py index
    ```

2.  **Ask a question:**
    ```bash
    python app.py ask "Your question about the SRM guides"
    ```

## Features

- **Advanced Chunking**: Procedure-aware and table-aware document processing
- **Hybrid Retrieval**: BM25 (sparse) + FAISS (dense) search with cross-encoder reranking
- **Ollama Integration**: Local LLM support for answer generation
- **Rich CLI**: Beautiful command-line interface with Typer and Rich
