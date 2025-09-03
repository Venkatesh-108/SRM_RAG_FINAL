# SRM RAG System

A comprehensive RAG (Retrieval-Augmented Generation) system for Dell SRM guides with advanced chunking, hybrid retrieval, and Ollama integration. The system provides both a command-line interface and a web API for querying SRM documentation.

## Features

- **Advanced Document Processing**: Intelligent chunking with procedure-aware and table-aware document parsing
- **Hybrid Retrieval System**: Combines BM25 (sparse) and FAISS (dense) search with cross-encoder reranking
- **Multi-Query Generation**: Automatic query expansion for better retrieval coverage
- **Ollama Integration**: Local LLM support using llama3.2:3b model for answer generation
- **Smart Context Selection**: Diversity-aware chunk selection to avoid redundancy
- **Auto-Indexing**: Automatic document indexing on startup
- **Web Interface**: HTML interface for easy testing and interaction
- **Rich CLI**: Beautiful command-line interface with Typer and Rich
- **FastAPI Backend**: Modern, fast web API with automatic documentation

## Architecture

The system uses a multi-stage approach:
1. **Document Processing**: PDF and Markdown parsing with unstructured
2. **Intelligent Chunking**: Context-aware chunking with overlap for continuity
3. **Hybrid Search**: BM25 + FAISS with query expansion
4. **Advanced Reranking**: Cross-encoder based reranking with metadata scoring
5. **Answer Generation**: Multi-stage LLM generation with validation
6. **Quality Assessment**: Confidence scoring and answer validation

## Setup

### Prerequisites

- Python 3.8+
- Ollama installed and running locally
- Dell SRM guide documents (PDF or Markdown format)

### Installation

1. **Clone or download the project:**
   ```bash
   cd SRM_RAG
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   ```bash
   # Windows
   venv\Scripts\activate.bat
   
   # Linux/Mac
   source venv/bin/activate
   ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Place your Dell SRM guide documents into the `docs` directory**

6. **Ensure Ollama is running with the required model:**
   ```bash
   ollama pull llama3.2:3b
   ```

## Configuration

The system uses `config.yaml` for configuration. Key settings include:

- **Embedding Model**: Sentence transformer model for dense search
- **Reranker Model**: Cross-encoder model for reranking
- **Ollama Model**: Local LLM model for answer generation
- **Search Parameters**: Top-k values for different search stages
- **Context Lengths**: Dynamic context selection based on query complexity

## Usage

### Web Server Mode (Recommended)

Start the web server with auto-reload for development:

```bash
python app.py --host 127.0.0.1 --port 8000 --reload
```

This will:
- Start the FastAPI server on the specified host and port
- Enable auto-reload for development
- Automatically index documents if needed
- Provide a web interface at `http://127.0.0.1:8000`

### Command Line Interface

1. **Index the documents:**
   ```bash
   python app.py index
   ```

2. **Ask a question:**
   ```bash
   python app.py ask "Your question about the SRM guides"
   ```

### API Endpoints

The system provides several REST API endpoints:

- **GET /** - HTML interface for testing
- **POST /ask** - Query endpoint for asking questions
- **POST /reindex** - Force reindexing of documents

#### Example API Usage

```bash
# Ask a question via API
curl -X POST "http://127.0.0.1:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"query": "How do I upgrade SRM?"}'

# Force reindexing
curl -X POST "http://127.0.0.1:8000/reindex"
```

## Document Processing

### Supported Formats
- **PDF**: Full PDF parsing with text extraction
- **Markdown**: Markdown file processing

### Chunking Strategy
- **Procedure-Aware**: Detects and preserves step-by-step procedures
- **Contextual Overlap**: Creates overlapping chunks for better continuity
- **Metadata Enrichment**: Adds section titles, page numbers, and chunk types
- **Smart Classification**: Automatically categorizes chunks (procedure, troubleshooting, requirements, etc.)

## Search and Retrieval

### Hybrid Search
- **BM25 (Sparse)**: Keyword-based search for exact term matching
- **FAISS (Dense)**: Semantic search using sentence embeddings
- **Query Expansion**: Generates multiple query variations for better coverage

### Reranking
- **Cross-Encoder**: Uses advanced reranking models for relevance scoring
- **Metadata Scoring**: Incorporates chunk type and quality metrics
- **Diversity Selection**: Ensures diverse context selection

## Answer Generation

### Multi-Stage Generation
1. **Initial Generation**: Creates first answer based on context
2. **Refinement**: Improves and validates the initial answer
3. **Validation**: Checks consistency and completeness

### Quality Features
- **Confidence Scoring**: Provides confidence metrics for answers
- **Source Citations**: Links answers to specific document sections
- **Validation Metrics**: Context alignment, fact consistency, and procedure completeness

## Development

### Project Structure
```
SRM_RAG/
├── app.py              # Main application (CLI + Web API)
├── config.yaml         # Configuration file
├── requirements.txt    # Python dependencies
├── docs/              # Document directory
├── index/             # Generated indices
└── venv/              # Virtual environment
```

### Key Components
- **Document Loader**: Handles PDF and Markdown parsing
- **Chunker**: Intelligent document chunking
- **Index Manager**: Manages BM25 and FAISS indices
- **Search Engine**: Hybrid search and reranking
- **Answer Generator**: LLM-based answer generation
- **Web Server**: FastAPI-based web interface

### Adding New Features
- **New Document Types**: Extend the `load_documents()` function
- **Custom Chunking**: Modify the `chunk_elements()` function
- **Additional Models**: Update configuration and model loading
- **New API Endpoints**: Add to the FastAPI app

## Troubleshooting

### Common Issues

1. **Module Not Found Errors**: Ensure virtual environment is activated and dependencies are installed
2. **Ollama Connection Issues**: Verify Ollama is running and the model is available
3. **Index Not Found**: Run the indexing command or use the web server mode for auto-indexing
4. **Memory Issues**: Large documents may require more RAM; consider reducing chunk sizes

### Performance Optimization

- **Chunk Size**: Adjust chunk sizes in configuration for optimal performance
- **Model Selection**: Choose appropriate embedding and reranking models
- **Index Management**: Regular reindexing for updated documents

## Contributing

When contributing to this project:

1. Follow the existing code structure and patterns
2. Add appropriate error handling and logging
3. Update documentation for new features
4. Test with various document types and sizes

## License

This project is designed for internal use with Dell SRM documentation.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the configuration settings
3. Ensure all dependencies are properly installed
4. Verify Ollama is running with the correct model
