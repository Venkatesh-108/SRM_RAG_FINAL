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
- Provide a web interface at `http://127.0.0.1:5000`

### Command Line Interface

1. **Index the documents:**
   ```bash
   python app.py index
   ```
