import typer
from rich.console import Console
from typing import List, Dict, Any
from loguru import logger
from pathlib import Path
import yaml
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Import new chat models and services
from models.chat import (
    CreateSessionRequest, 
    SendMessageRequest, ChatResponse, SessionListResponse, ChatMessage
)
from services.chat_service import ChatService
from services.rag_service import RAGService
from services.ollama_service import generate_answer_with_ollama

# Configuration
CONFIG_PATH = Path("config.yaml")

def load_config():
    if not CONFIG_PATH.is_file():
        raise FileNotFoundError(f"Configuration file not found at: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r") as f:
        config = yaml.safe_load(f)
    
    current_mode = config.get("current_mode", "medium")
    mode_settings = config.get("modes", {}).get(current_mode, {})
    
    final_config = {**config, **mode_settings}
    logger.info(f"Loaded configuration for mode: '{current_mode}'")
    
    return final_config

config = load_config()

# Initialize services
rag_service = RAGService(config)
chat_service = ChatService(rag_service=rag_service)

console = Console()

# Pydantic models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    context: List[Dict[str, Any]]
    sources: List[Dict[str, Any]]
    confidence_score: float
    answer_validation: Dict[str, Any]

# Use imported function from services/ollama_service.py instead of duplicating code

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Check for new PDFs and auto-index on startup"""
    # Display Llama license compliance notice
    console.print("🤖 Built with Llama - Llama 3.2 Community License", style="bold blue")
    console.print("Checking for new or modified PDFs...", style="bold yellow")
    
    # Always check for new or modified PDFs, even if indexes exist
    try:
        new_or_modified = rag_service.detect_new_or_modified_pdfs()
        
        if new_or_modified:
            console.print(f"Found {len(new_or_modified)} new/modified PDFs: {new_or_modified}", style="bold yellow")
            console.print("Auto-indexing new documents...", style="bold yellow")
            results = rag_service.index_documents()
            console.print(f"Indexing completed: {results}", style="bold green")
        else:
            console.print("No new or modified PDFs found. All documents are up to date.", style="bold green")
            
        # Ensure searcher is loaded
        if not rag_service.pdf_searcher:
            console.print("No indexes found. Performing full indexing...", style="bold yellow")
            rag_service.index_documents(force_reindex=True)
            
        console.print("Ready to serve queries.", style="bold green")
        
    except Exception as e:
        console.print(f"Error during startup indexing check: {e}", style="bold red")
        logger.error(f"Startup indexing error: {e}")
    
    yield

app = FastAPI(
    title="SRM RAG API - Built with Llama", 
    description="RAG system for Dell SRM guides powered by Llama 3.2 Community License", 
    lifespan=lifespan
)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="templates/static"), name="static")

@app.post("/upload_pdf/", response_model=Dict[str, str])
async def upload_pdf(file: UploadFile = File(...)):
    """Endpoint to upload a PDF file."""
    try:
        docs_path = Path(config["docs_path"])
        docs_path.mkdir(exist_ok=True)
        file_path = docs_path / file.filename
        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())
        
        # After uploading, re-index all documents
        rag_service.index_documents()
        
        return JSONResponse(status_code=200, content={"message": f"File '{file.filename}' uploaded and indexed successfully."})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents")
async def list_documents():
    """Lists the documents available in the docs directory."""
    docs_path = Path(config["docs_path"])
    if not docs_path.is_dir():
        logger.warning(f"Docs directory not found at: {docs_path}")
        return []
    
    supported_formats = [".pdf", ".md"]
    doc_files = [f.name for f in docs_path.glob("**/*") if f.is_file() and f.suffix in supported_formats]
    return doc_files

@app.get("/documents/{filename}")
async def get_document(filename: str):
    """Serves a specific document file from the docs directory."""
    docs_path = Path(config["docs_path"])
    file_path = docs_path / filename

    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
        
    return FileResponse(file_path)

@app.post("/chat/create_session", response_model=ChatResponse)
async def create_session(request: CreateSessionRequest):
    """Create a new chat session."""
    try:
        session = chat_service.create_session(
            title=request.title,
            initial_message=request.initial_message
        )
        return ChatResponse(
            message=ChatMessage(role="assistant", content="Session created successfully. How can I help you today?"),
            session=session,
            sources=[],
            confidence_score=1.0,
            processing_time=0.0
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/send_message", response_model=ChatResponse)
async def send_message(request: SendMessageRequest):
    """Send a message in an existing chat session."""
    try:
        response = await chat_service.send_message(request.session_id, request.content)
        return response
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/sessions", response_model=SessionListResponse)
async def get_sessions():
    """List all chat sessions."""
    try:
        sessions = chat_service.get_all_sessions()
        return SessionListResponse(sessions=sessions, total_count=len(sessions))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/session/{session_id}")
async def get_session(session_id: str):
    """Get a specific chat session."""
    try:
        session = chat_service.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat/session/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session."""
    try:
        success = chat_service.delete_session(session_id)
        if not success:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"message": f"Session {session_id} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat/sessions/clear")
async def clear_all_sessions():
    """Clear all chat sessions."""
    try:
        success = chat_service.clear_all_sessions()
        if success:
            return {"message": "All chat sessions cleared successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to clear sessions")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    """Modern HTML interface for SRM AI Doc Assist"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask", response_model=QueryResponse)
async def ask_endpoint(request: QueryRequest):
    """API endpoint for asking questions"""
    try:
        retrieved_chunks = rag_service.search(request.query)
        
        answer, confidence_score, validation_result = generate_answer_with_ollama(request.query, retrieved_chunks)
        
        sources = []
        for chunk in retrieved_chunks:
            source_info = chunk['metadata']
            # Convert document ID to actual PDF filename
            document_id = source_info.get('filename', 'Unknown')
            actual_pdf_filename = rag_service.get_pdf_filename_from_document_id(document_id)
            
            source_text = f"{actual_pdf_filename} (Page {source_info.get('page_number', 'N/A')})"
            if source_info.get('section_title'):
                source_text += f" → Section: {source_info.get('section_title')}"
            
            sources.append({
                'text': source_text,
                'filename': actual_pdf_filename,
                'page_number': source_info.get('page_number'),
                'section_title': source_info.get('section_title'),
                'relevance_score': source_info.get('relevance_score')
            })
        
        return QueryResponse(
            answer=answer,
            context=[{"text": chunk['text'][:1000] + ("..." if len(chunk['text']) > 1000 else ""), "metadata": chunk['metadata']} for chunk in retrieved_chunks],
            sources=sources,
            confidence_score=confidence_score,
            answer_validation=validation_result
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/autocomplete")
async def autocomplete_endpoint(query: str = ""):
    """Get autocomplete suggestions for section titles"""
    try:
        suggestions = rag_service.get_title_suggestions(query)
        return {"suggestions": suggestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reindex")
async def reindex_endpoint(force: bool = False):
    """Reindex documents (incremental by default, force=true for full reindex)"""
    try:
        if force:
            results = rag_service.index_documents(force_reindex=True)
            return {"message": f"Force reindex completed. Results: {results}"}
        else:
            new_or_modified = rag_service.detect_new_or_modified_pdfs()
            if new_or_modified:
                results = rag_service.index_documents()
                return {
                    "message": f"Incremental reindex completed. Processed {len(new_or_modified)} files.",
                    "processed_files": new_or_modified,
                    "results": results
                }
            else:
                return {
                    "message": "No new or modified PDFs detected. All documents are up to date.",
                    "processed_files": [],
                    "results": {"status": "up_to_date", "processed_files": 0}
                }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

cli_app = typer.Typer()

@cli_app.command()
def index():
    """Index the source documents."""
    console.print("🤖 Built with Llama - Llama 3.2 Community License", style="bold blue")
    console.print("Starting the indexing process...", style="bold green")
    results = rag_service.index_documents()
    console.print(f"Successfully indexed. Results: {results}", style="bold green")

@cli_app.command()
def ask(query: str):
    """Ask a question to the indexed documents."""
    console.print("🤖 Built with Llama - Llama 3.2 Community License", style="bold blue")
    console.print(f"Query: '{query}'", style="bold blue")

    retrieved_chunks = rag_service.search(query)
    
    console.print("\n--- Retrieved Context ---", style="bold green")
    for i, chunk in enumerate(retrieved_chunks):
        source = chunk['metadata'].get('filename', 'N/A')
        page = chunk['metadata'].get('page_number', 'N/A')
        console.print(f"[{i+1}] Source: {source}, Page: {page}")
        console.print(f"   Content: {chunk['text'][:200]}...")
    
    console.print("\n--- Generating Answer ---", style="bold blue")
    answer, confidence_score, validation_result = generate_answer_with_ollama(query, retrieved_chunks)
    
    console.print("\n--- Answer ---", style="bold green")
    console.print(answer)
    
    console.print(f"\n--- Confidence Score: {confidence_score:.2f}/1.0 ---", style="bold blue")
    console.print(f"--- Validation Score: {validation_result.get('overall_validation_score', 0):.2f}/1.0 ---", style="bold blue")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] in ["--host", "--port", "--help"]:
        import argparse
        parser = argparse.ArgumentParser(description="SRM RAG Web Server")
        parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
        parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
        parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
        
        args = parser.parse_args()
        
        console.print(f"Starting SRM RAG web server on {args.host}:{args.port}", style="bold green")
        
        uvicorn.run(
            "app:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info"
        )
    else:
        cli_app()
