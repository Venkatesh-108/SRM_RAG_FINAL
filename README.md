# AI Doc Assist 

A comprehensive RAG (Retrieval-Augmented Generation) system for document guides with advanced chunking, hybrid retrieval, and Ollama integration. The system provides both a command-line interface and a web API for querying documentation.

> **🤖 Built with Llama** - This system is powered by Llama 3.2 and operates under the Llama 3.2 Community License.

## Features

- **🎯 Enhanced Exact Title Matching**: Direct section content retrieval for exact documentation titles
- **🔍 Advanced Document Processing**: Intelligent chunking with procedure-aware and table-aware document parsing
- **🔄 Hybrid Retrieval System**: Combines BM25 (sparse) and FAISS (dense) search with cross-encoder reranking
- **📈 Multi-Query Generation**: Automatic query expansion for better retrieval coverage
- **🤖 Ollama Integration**: Local LLM support using llama3.2:3b model for answer generation
- **🎛️ Smart Context Selection**: Diversity-aware chunk selection to avoid redundancy
- **⚡ Auto-Indexing**: Automatic document indexing on startup
- **🌐 Web Interface**: HTML interface for easy testing and interaction
- **💻 Rich CLI**: Beautiful command-line interface with Typer and Rich
- **🚀 FastAPI Backend**: Modern, fast web API with automatic documentation
- **📚 Cross-Document Search**: Seamless search across multiple PDF documents
- **🧹 Clean Response Formatting**: Metadata-free, properly formatted responses

## Architecture

The system uses a multi-stage approach:
1. **Enhanced Document Processing**: Advanced PDF parsing with Docling and enhanced chunking
2. **Exact Title Indexing**: Pre-built index for instant exact title matching
3. **Intelligent Chunking**: Context-aware chunking with complete section preservation
4. **Dual Search Strategy**: Exact title matching + hybrid search fallback
5. **Smart Content Enhancement**: Automatic detection of substantial content chunks
6. **Advanced Reranking**: Cross-encoder based reranking with metadata scoring
7. **Adaptive Response**: Direct content return for exact matches, LLM synthesis for others
8. **Quality Assessment**: Confidence scoring and answer validation

### Search Flow
```
User Query → Exact Title Check → Direct Content Return (if exact match)
            ↓
         Hybrid Search → LLM Synthesis → Generated Answer (if no exact match)
```

## Setup

### Prerequisites

- Python 3.8+
- Ollama installed and running locally
- Document guides (PDF or Markdown format)

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

5. **Place your document guides into the `docs` directory**

6. **Ensure Ollama is running with the required model:**
   ```bash
   ollama pull llama3.2:3b
   ```


- **Automatic Detection**: The system automatically looks for a `models` folder
- **Local Model Usage**: Uses pre-downloaded Docling and SentenceTransformer models
- **No Internet Required**: Works completely offline once models are downloaded
- **Fallback Support**: Falls back to internet download if models not found (will fail in offline environments)

### Model Requirements

The offline deployment requires approximately **450MB** of model files:
- **Docling Models**: ~358MB (TableFormer models for PDF processing)
- **SentenceTransformer Models**: ~90MB (all-MiniLM-L6-v2 for embeddings)

### Troubleshooting Offline Deployment

**Models not found?**
```bash
# Check that models folder exists
ls -la models/

# Verify model files are present
find models/ -name "*.pt" -o -name "*.safetensors"
```

**Still getting download errors?**
- Ensure the `models` folder is in the correct location (same level as `app.py`)
- Check file permissions on the models directory
- Verify the models folder contains the required subdirectories

**Benefits of Offline Deployment:**
- ✅ **No Internet Required**: Works in restricted environments
- ✅ **Fast Startup**: Models are already downloaded
- ✅ **Reliable**: No dependency on external services
- ✅ **Portable**: Easy to deploy to multiple customer locations

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
python app.py --host 127.0.0.1 --port 5000 --reload
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
   python app.py ask "Your question about the guides"
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
     -d '{"query": "How do I upgrade the system?"}'

# Force reindexing
curl -X POST "http://127.0.0.1:8000/reindex"
```

## Enhanced Exact Title Matching

The system features an advanced exact title matching capability that provides instant, direct access to complete documentation sections.

### How It Works

1. **Exact Title Detection**: When users type exact section titles, the system bypasses LLM processing
2. **Direct Content Return**: Returns complete section content with proper formatting
3. **Instant Response**: No LLM delay - immediate response with confidence score 1.0
4. **Clean Formatting**: Metadata-free content with proper markdown hierarchy

### Example Usage

**Exact Match (Direct Content):**
```
Query: "Additional frontend server tasks"
→ Returns: Complete section with tasks, steps, and prerequisites
→ Confidence: 1.0
→ Processing: Instant (no LLM)
```

**Non-Exact Match (Standard RAG):**
```
Query: "frontend server tasks" 
→ Returns: LLM-synthesized answer from multiple sources
→ Confidence: 0.8-0.9
→ Processing: Hybrid search + LLM synthesis
```

### Supported Documents

- ✅ Installation and Configuration Guide
- ✅ Deploying Additional Frontend Servers
- ✅ Upgrade Guide

### Benefits

- **⚡ Instant Access**: No waiting for LLM processing
- **📖 Complete Content**: Full section with all details, steps, and context
- **🎯 Perfect Accuracy**: Raw documentation without AI interpretation
- **🔄 Smart Fallback**: Automatically switches to standard RAG for non-exact queries

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
├── app.py                     # Main application (CLI + Web API)
├── config.yaml               # Configuration file
├── requirements.txt          # Python dependencies
├── docs/                     # Document directory
├── index/                    # Generated indices and title indexes
├── extracted_docs/           # Enhanced processed documents
├── services/
│   ├── enhanced_search.py    # Enhanced search with exact title matching
│   ├── chat_service.py       # Chat management and response formatting
│   ├── rag_service.py        # Main RAG orchestration
│   └── ollama_service.py     # LLM integration
├── pdf_processing/
│   └── enhanced_processor.py # Advanced PDF processing with Docling
└── venv/                     # Virtual environment
```

### Key Components
- **Enhanced Search Engine**: Exact title matching + hybrid search fallback
- **Enhanced PDF Processor**: Advanced document parsing with complete section extraction
- **Chat Service**: Response formatting and metadata cleaning
- **Title Index Manager**: Pre-built indexes for instant exact matching
- **RAG Service**: Orchestrates search strategies and response types
- **Dual-Mode Processing**: Direct content return vs. LLM synthesis
- **Web Server**: FastAPI-based web interface with enhanced endpoints



### Common Issues

1. **Module Not Found Errors**: Ensure virtual environment is activated and dependencies are installed
2. **Ollama Connection Issues**: Verify Ollama is running and the model is available
3. **Index Not Found**: Run the indexing command or use the web server mode for auto-indexing
4. **Memory Issues**: Large documents may require more RAM; consider reducing chunk sizes



### Search Behaviors

| Query Type | Example | Response Time | Content Type | Confidence |
|------------|---------|---------------|--------------|-------------|
| **Exact Title** | "Installing and configuring the Frontend host" | Instant | Raw Documentation | 1.0 |
| **Partial Match** | "frontend server tasks" | ~3-5 seconds | LLM Synthesis | 0.8-0.9 |
| **Question** | "How do I configure SSL?" | ~3-5 seconds | LLM Synthesis | 0.8-0.9 |
| **Broad Topic** | "database configuration" | ~5-8 seconds | LLM Synthesis | 0.7-0.9 |

