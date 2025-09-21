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

def clean_frontend_formatting(content: str) -> str:
    """Generic text cleaning for frontend display - merges content that belongs to same numbered step"""
    if not content:
        return content

    import re
    lines = content.split('\n')
    grouped_lines = []
    i = 0

    while i < len(lines):
        line = lines[i].rstrip()

        # Skip completely empty lines
        if not line.strip():
            i += 1
            continue

        # Remove standalone punctuation on separate lines (., :, etc.)
        if re.match(r'^\s*[.,:;]+\s*$', line):
            i += 1
            continue

        # Check if this is a numbered step
        numbered_match = re.match(r'^(\s*)(\d+)[\.\)]\s*(.+)', line)
        if numbered_match:
            indent, number, initial_content = numbered_match.groups()

            # Start collecting all content for this step
            step_content = [initial_content.strip()]
            j = i + 1

            # Look ahead to collect all content that belongs to this step
            while j < len(lines):
                next_line = lines[j].strip()

                # Stop if we hit another numbered step
                if re.match(r'^\d+[\.\)]\s', next_line):
                    break

                # Stop if we hit a heading
                if re.match(r'^#{1,6}\s', next_line):
                    break

                # Stop if we hit a lettered sub-item (but these should be included)
                # Actually, include lettered items as part of the step
                if re.match(r'^[a-z][\.\)]\s', next_line):
                    step_content.append(next_line)
                    j += 1
                    continue

                # Skip empty lines but don't stop
                if not next_line:
                    j += 1
                    continue

                # Special handling for NOTEs - keep them separate but as part of the step
                if re.match(r'^(NOTE|IMPORTANT|WARNING|CAUTION):', next_line, re.IGNORECASE):
                    step_content.append('\n' + next_line)  # Add line break before NOTE
                    j += 1
                    continue

                # Add this line as continuation of the step
                step_content.append(next_line)
                j += 1

            # Clean and format the collected content
            cleaned_content = []
            for content in step_content:
                if content.startswith('\n'):  # This is a NOTE
                    cleaned_content.append(content)  # Keep the line break
                else:
                    # Clean HTML entities and extra punctuation
                    content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                    content = re.sub(r'\s*[\.,]+\s*$', '', content)
                    content = re.sub(r'\s+', ' ', content)
                    if content:  # Only add non-empty content
                        cleaned_content.append(content)

            # Join the content appropriately
            final_content = []
            for content in cleaned_content:
                if content.startswith('\n'):  # This is a NOTE
                    final_content.append(content)
                else:
                    if final_content and not final_content[-1].startswith('\n'):
                        # Join with previous content with a space
                        final_content[-1] = final_content[-1] + ' ' + content
                    else:
                        final_content.append(content)

            # Create the final step line
            main_content = final_content[0] if final_content else ''
            step_line = f"{indent}{number}. {main_content}"
            grouped_lines.append(step_line)

            # Add any NOTEs as separate lines
            for content in final_content[1:]:
                if content.startswith('\n'):
                    grouped_lines.append(content[1:])  # Remove the \n prefix

            i = j  # Skip all the lines we processed

        else:
            # This is not a numbered step - handle other content types

            # Clean lettered sub-items
            letter_match = re.match(r'^(\s*)([a-z])[\.\)]\s*(.+)', line)
            if letter_match:
                indent, letter, content = letter_match.groups()
                content = content.strip()
                content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                content = re.sub(r'\s*[\.,]+\s*$', '', content)
                content = re.sub(r'\s+', ' ', content)
                line = f"{indent}- {letter}. {content}"

            # Clean bullet points
            elif re.match(r'^(\s*)[-*+•]\s*(.+)', line):
                bullet_match = re.match(r'^(\s*)[-*+•]\s*(.+)', line)
                indent, content = bullet_match.groups()
                content = content.strip()
                content = content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                content = re.sub(r'\s+', ' ', content)
                line = f"{indent}- {content}"

            # Clean headings
            elif re.match(r'^(\s*)(#{1,6})\s*(.+)', line):
                heading_match = re.match(r'^(\s*)(#{1,6})\s*(.+)', line)
                indent, hashes, title = heading_match.groups()
                title = title.strip()
                title = re.sub(r'[\.,;:]+$', '', title)
                title = re.sub(r'\s+', ' ', title)
                line = f"{indent}{hashes} {title}"

            # Regular content - clean up spacing
            else:
                line = re.sub(r'\s+', ' ', line)
                if ':' in line and not line.strip().endswith(':'):
                    line = re.sub(r'\s*:\s*', ': ', line)

            grouped_lines.append(line)
            i += 1

    # Final cleanup - no empty lines between steps
    result_lines = []
    for line in grouped_lines:
        if line.strip():  # Only add non-empty lines
            result_lines.append(line)

    return '\n'.join(result_lines)

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
    console.print("Built with Llama - Llama 3.2 Community License", style="bold blue")
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
    title="AI Doc Assist API - Built with Llama", 
    description="RAG system for document guides powered by Llama 3.2 Community License", 
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
    """Modern HTML interface for AI Doc Assist"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/ask", response_model=QueryResponse)
async def ask_endpoint(request: QueryRequest):
    """API endpoint for asking questions"""
    try:
        # Check for casual greetings first
        greeting_response = chat_service._detect_greeting(request.query)
        if greeting_response:
            greeting_text = chat_service.default_responses.get(greeting_response, chat_service.default_responses['greeting'])
            return QueryResponse(
                answer=greeting_text,
                context=[],
                sources=[],
                confidence_score=1.0,
                answer_validation={"response_type": "greeting", "greeting_type": greeting_response}
            )
        
        retrieved_chunks = rag_service.search(request.query)
        
        answer, confidence_score, validation_result = generate_answer_with_ollama(request.query, retrieved_chunks)

        # Clean the answer for frontend display
        answer = clean_frontend_formatting(answer)
        
        sources = []
        seen_sources = set()  # Track (filename, page_number) combinations
        duplicate_count = 0  # Track how many duplicates were removed

        for chunk in retrieved_chunks:
            source_info = chunk['metadata']
            # Convert document ID to actual PDF filename
            document_id = source_info.get('filename', 'Unknown')
            actual_pdf_filename = rag_service.get_pdf_filename_from_document_id(document_id)

            page_number = source_info.get('page_number')
            section_title = source_info.get('section_title')
            relevance_score = source_info.get('relevance_score', 0.0)

            # Create unique identifier for this source
            source_key = (actual_pdf_filename, page_number)

            # Skip if we've already seen this source
            if source_key not in seen_sources:
                seen_sources.add(source_key)

                source_text = f"{actual_pdf_filename} (Page {page_number or 'N/A'})"
                if section_title:
                    source_text += f" → Section: {section_title}"

                sources.append({
                    'text': source_text,
                    'filename': actual_pdf_filename,
                    'page_number': page_number,
                    'section_title': section_title,
                    'relevance_score': relevance_score
                })
            else:
                duplicate_count += 1
                # If duplicate, update the relevance score to the highest one
                for existing_source in sources:
                    if (existing_source['filename'] == actual_pdf_filename and
                        existing_source['page_number'] == page_number):
                        existing_source['relevance_score'] = max(
                            existing_source['relevance_score'] or 0.0,
                            relevance_score or 0.0
                        )
                        break

        # Log deduplication info
        if duplicate_count > 0:
            logger.info(f"Deduplicated {duplicate_count} duplicate sources from {len(retrieved_chunks)} total chunks")
        
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
    console.print("Built with Llama - Llama 3.2 Community License", style="bold blue")
    console.print("Starting the indexing process...", style="bold green")
    results = rag_service.index_documents()
    console.print(f"Successfully indexed. Results: {results}", style="bold green")

@cli_app.command()
def ask(query: str):
    """Ask a question to the indexed documents."""
    console.print("Built with Llama - Llama 3.2 Community License", style="bold blue")
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
        parser = argparse.ArgumentParser(description="AI Doc Assist Web Server")
        parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
        parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
        parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
        
        args = parser.parse_args()
        
        console.print(f"Starting AI Doc Assist web server on {args.host}:{args.port}", style="bold green")
        
        uvicorn.run(
            "app:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info"
        )
    else:
        cli_app()
