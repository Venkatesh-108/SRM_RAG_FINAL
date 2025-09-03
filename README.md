# SRM RAG CLI

This is a command-line interface for querying Dell SRM guides using a RAG architecture as described in the project documentation.

## Setup

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Place your Dell SRM guide documents (in PDF or Markdown format) into a `docs` directory.

## Usage

1.  **Index the documents:**
    ```bash
    python -m srm_rag.cli index
    ```

2.  **Ask a question:**
    ```bash
    python -m srm_rag.cli ask "Your question about the SRM guides"
    ```
