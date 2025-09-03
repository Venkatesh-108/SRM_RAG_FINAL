import typer
from rich.console import Console
from typing import List, Dict, Any
from unstructured.documents.elements import Element, Title, NarrativeText, ListItem, Table
from loguru import logger
import pickle
from pathlib import Path
import numpy as np
import faiss
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer, CrossEncoder
import ollama
import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import uvicorn
from pydantic import BaseModel

# Configuration
CONFIG_PATH = Path("config.yaml")

def load_config():
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(f"Configuration file not found at: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    return config

config = load_config()

# FastAPI app
app = FastAPI(title="SRM RAG API", description="RAG system for Dell SRM guides")
console = Console()

# Pydantic models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    context: List[Dict[str, Any]]
    sources: List[str]

def check_and_auto_index():
    """
    Check if indices exist, if not, automatically index the documents.
    """
    index_path = Path(config["index_path"])
    if not index_path.is_dir() or not (index_path / "chunks.pkl").exists():
        console.print("No indices found. Auto-indexing documents...", style="bold yellow")
        try:
            # Load documents
            elements = load_documents()
            if not elements:
                console.print("No documents found to index.", style="bold red")
                return False
                
            # Chunk elements
            chunks = chunk_elements(elements)
            
            # Create and save indices
            create_and_save_index(chunks)
            
            console.print(f"Auto-indexing completed: {len(chunks)} chunks indexed.", style="bold green")
            return True
        except Exception as e:
            console.print(f"Auto-indexing failed: {e}", style="bold red")
            return False
    else:
        console.print("Indices found. Ready to serve queries.", style="bold green")
        return True

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
            from unstructured.partition.auto import partition
            file_elements = partition(filename=str(doc_file))
            elements.extend(file_elements)
        except Exception as e:
            logger.error(f"Failed to process {doc_file}: {e}")
    
    return elements

def chunk_elements(elements: List[Element]) -> List[Dict[str, Any]]:
    """
    Chunks elements based on their type, grouping related items.
    - Combines Title with following NarrativeText.
    - Groups consecutive ListItem elements as procedures.
    - Treats Tables as distinct chunks with special metadata.
    """
    chunks = []
    i = 0
    while i < len(elements):
        el = elements[i]
        
        if isinstance(el, Title):
            # Combine title with the following paragraph
            chunk_text = el.text
            metadata = el.metadata.to_dict()
            metadata["type"] = "title_and_text"
            
            if i + 1 < len(elements) and isinstance(elements[i+1], NarrativeText):
                chunk_text += "\n" + elements[i+1].text
                i += 1 # Move past the narrative text
            
            chunks.append({"text": chunk_text, "metadata": metadata})

        elif isinstance(el, ListItem):
            # Group consecutive list items as a procedure
            procedure_steps = [el.text]
            metadata = el.metadata.to_dict()
            metadata["type"] = "procedure"

            while i + 1 < len(elements) and isinstance(elements[i+1], ListItem):
                i += 1
                procedure_steps.append(elements[i].text)
            
            chunk_text = "\n".join(procedure_steps)
            metadata["step_count"] = len(procedure_steps)
            chunks.append({"text": chunk_text, "metadata": metadata})

        elif isinstance(el, Table):
            # Handle tables
            metadata = el.metadata.to_dict()
            metadata["type"] = "table"
            
            # Flattened text representation
            chunk_text = el.text
            
            # Optional: Add structured data if available
            if hasattr(el.metadata, "text_as_html"):
                metadata["html"] = el.metadata.text_as_html

            chunks.append({"text": chunk_text, "metadata": metadata})
            
        elif isinstance(el, NarrativeText):
            # Handle standalone paragraphs
            metadata = el.metadata.to_dict()
            metadata["type"] = "text"
            chunks.append({"text": el.text, "metadata": metadata})

        else:
            # Generic fallback for other element types
            metadata = el.metadata.to_dict()
            metadata["type"] = type(el).__name__
            chunks.append({"text": el.text, "metadata": metadata})

        i += 1
        
    logger.info(f"Chunked {len(elements)} elements into {len(chunks)} chunks.")
    return chunks

def create_and_save_index(chunks: List[Dict[str, Any]]):
    """
    Creates and saves BM25 and FAISS indices from the given chunks.
    """
    index_path = Path(config["index_path"])
    index_path.mkdir(exist_ok=True)

    # Store the raw chunks
    with open(index_path / "chunks.pkl", "wb") as f:
        pickle.dump(chunks, f)

    # --- BM25 Index ---
    tokenized_corpus = [chunk["text"].split(" ") for chunk in chunks]
    bm25 = BM25Okapi(tokenized_corpus)
    with open(index_path / "bm25.pkl", "wb") as f:
        pickle.dump(bm25, f)
    logger.info("BM25 index created and saved.")

    # --- FAISS Index ---
    embedding_model = SentenceTransformer(config["embedding_model"])
    embeddings = embedding_model.encode([chunk["text"] for chunk in chunks], show_progress_bar=True)
    
    d = embeddings.shape[1]  # dimension of vectors
    faiss_index = faiss.IndexFlatL2(d)
    faiss_index.add(np.array(embeddings, dtype='f4'))
    faiss.write_index(faiss_index, str(index_path / "faiss.index"))
    logger.info("FAISS index created and saved.")

def load_indices_and_chunks():
    """
    Loads the saved indices and chunk data from the index directory.
    """
    index_path = Path(config["index_path"])
    if not index_path.is_dir():
        return None, None, None, None

    with open(index_path / "chunks.pkl", "rb") as f:
        chunks = pickle.load(f)
    with open(index_path / "bm25.pkl", "rb") as f:
        bm25 = pickle.load(f)
    
    faiss_index = faiss.read_index(str(index_path / "faiss.index"))
    embedding_model = SentenceTransformer(config["embedding_model"])

    return chunks, bm25, faiss_index, embedding_model

def search_and_rerank(query: str, chunks, bm25, faiss_index, embedding_model):
    """
    Performs hybrid search (BM25 + FAISS) and then reranks the results.
    """
    # --- Stage 1 & 2: Hybrid Search ---
    # BM25 search
    tokenized_query = query.split(" ")
    bm25_scores = bm25.get_scores(tokenized_query)
    top_k_bm25_indices = np.argsort(bm25_scores)[::-1][:config["top_k_bm25"]]
    
    # FAISS search
    query_embedding = embedding_model.encode([query])
    _, top_k_faiss_indices = faiss_index.search(np.array(query_embedding, dtype='f4'), config["top_k_faiss"])
    top_k_faiss_indices = top_k_faiss_indices[0]

    # Merge and dedupe results
    combined_indices = list(set(top_k_bm25_indices) | set(top_k_faiss_indices))

    # --- Stage 3: Reranking ---
    cross_encoder = CrossEncoder(config["reranker_model"])
    pairs = [[query, chunks[i]["text"]] for i in combined_indices]
    scores = cross_encoder.predict(pairs)
    
    reranked_indices = np.argsort(scores)[::-1]
    
    # Get top results after reranking
    top_k_final_indices = [combined_indices[i] for i in reranked_indices[:config["top_k_reranked"]]]
    
    retrieved_chunks = [chunks[i] for i in top_k_final_indices]
    return retrieved_chunks

def generate_answer_with_ollama(query: str, context_chunks: List[Dict[str, Any]]):
    """
    Generates an answer using Ollama, based on the provided query and context.
    """
    context_text = "\n\n".join([chunk['text'] for chunk in context_chunks])
    
    prompt = f"""
    Based on the following context from the Dell SRM guides, answer the question.
    Provide the answer and cite the source document and page number from the metadata if available.

    Context:
    ---
    {context_text}
    ---

    Question: {query}
    
    Answer:
    """
    
    try:
        response = ollama.chat(
            model=config["ollama_model"],
            messages=[{'role': 'user', 'content': prompt}]
        )
        return response['message']['content']
    except Exception as e:
        logger.error(f"Error communicating with Ollama: {e}")
        return "Error: Could not generate an answer from the LLM."

# FastAPI endpoints
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Check and auto-index on startup"""
    check_and_auto_index()
    yield

app = FastAPI(title="SRM RAG API", description="RAG system for Dell SRM guides", lifespan=lifespan)

@app.get("/", response_class=HTMLResponse)
async def root():
    """Simple HTML interface for testing"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>SRM RAG System</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            input[type="text"] { width: 70%; padding: 10px; margin: 10px 0; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; cursor: pointer; }
            button:hover { background: #0056b3; }
            .result { margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>SRM RAG System</h1>
            <p>Ask questions about Dell SRM guides:</p>
            <input type="text" id="query" placeholder="Enter your question here..." />
            <button onclick="askQuestion()">Ask Question</button>
            <div id="result" class="result" style="display:none;"></div>
        </div>
        <script>
            async function askQuestion() {
                const query = document.getElementById('query').value;
                if (!query) return;
                
                const resultDiv = document.getElementById('result');
                resultDiv.style.display = 'block';
                resultDiv.innerHTML = 'Processing...';
                
                try {
                    const response = await fetch('/ask', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({query: query})
                    });
                    const data = await response.json();
                    
                    let html = '<h3>Answer:</h3><p>' + data.answer + '</p>';
                    if (data.sources && data.sources.length > 0) {
                        html += '<h4>Sources:</h4><ul>';
                        data.sources.forEach(source => html += '<li>' + source + '</li>');
                        html += '</ul>';
                    }
                    resultDiv.innerHTML = html;
                } catch (error) {
                    resultDiv.innerHTML = 'Error: ' + error.message;
                }
            }
        </script>
    </body>
    </html>
    """

@app.post("/ask", response_model=QueryResponse)
async def ask_endpoint(request: QueryRequest):
    """API endpoint for asking questions"""
    try:
        # Load indices
        chunks, bm25, faiss_index, embedding_model = load_indices_and_chunks()
        if chunks is None:
            raise HTTPException(status_code=500, detail="Index not found. Please ensure documents are indexed.")
        
        # Search and rerank
        retrieved_chunks = search_and_rerank(request.query, chunks, bm25, faiss_index, embedding_model)
        
        # Generate answer
        answer = generate_answer_with_ollama(request.query, retrieved_chunks)
        
        # Extract sources
        sources = []
        for chunk in retrieved_chunks:
            source = chunk['metadata'].get('filename', 'Unknown')
            page = chunk['metadata'].get('page_number', 'N/A')
            sources.append(f"{source} (Page {page})")
        
        return QueryResponse(
            answer=answer,
            context=[{"text": chunk['text'][:200] + "...", "metadata": chunk['metadata']} for chunk in retrieved_chunks],
            sources=sources
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reindex")
async def reindex_endpoint():
    """Force reindexing of documents"""
    try:
        # Load documents
        elements = load_documents()
        if not elements:
            raise HTTPException(status_code=400, detail="No documents found to index.")
            
        # Chunk elements
        chunks = chunk_elements(elements)
        
        # Create and save indices
        create_and_save_index(chunks)
        
        return {"message": f"Successfully reindexed {len(chunks)} chunks."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# CLI commands (keeping for backward compatibility)
cli_app = typer.Typer()

@cli_app.command()
def index():
    """
    Index the source documents.
    """
    console.print("Starting the indexing process...", style="bold green")
    
    # 1. Load documents
    elements = load_documents()
    if not elements:
        console.print("No documents found to index.", style="bold red")
        return
        
    # 2. Chunk elements
    chunks = chunk_elements(elements)
    
    # 3. Create and save indices
    create_and_save_index(chunks)
    
    console.print(f"Successfully indexed {len(chunks)} chunks.", style="bold green")

@cli_app.command()
def ask(query: str):
    """
    Ask a question to the indexed documents.
    """
    console.print(f"Query: '{query}'", style="bold blue")

    # 1. Load indices
    chunks, bm25, faiss_index, embedding_model = load_indices_and_chunks()
    if chunks is None:
        console.print("Index not found. Please run `index` first.", style="bold red")
        return

    # 2. Search and rerank
    retrieved_chunks = search_and_rerank(query, chunks, bm25, faiss_index, embedding_model)
    
    console.print("\n--- Retrieved Context ---", style="bold green")
    for i, chunk in enumerate(retrieved_chunks):
        source = chunk['metadata'].get('filename', 'N/A')
        page = chunk['metadata'].get('page_number', 'N/A')
        console.print(f"[{i+1}] Source: {source}, Page: {page}")
        console.print(f"   Content: {chunk['text'][:200]}...")
    
    # 3. Generate answer
    console.print("\n--- Generating Answer ---", style="bold blue")
    answer = generate_answer_with_ollama(query, retrieved_chunks)
    
    console.print("\n--- Answer ---", style="bold green")
    console.print(answer)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] in ["--host", "--port", "--help"]:
        # Web server mode
        import argparse
        parser = argparse.ArgumentParser(description="SRM RAG Web Server")
        parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
        parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
        parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
        
        args = parser.parse_args()
        
        console.print(f"Starting SRM RAG web server on {args.host}:{args.port}", style="bold green")
        console.print("Auto-indexing will be performed on startup if needed.", style="bold yellow")
        
        uvicorn.run(
            "app:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info"
        )
    else:
        # CLI mode
        cli_app()
