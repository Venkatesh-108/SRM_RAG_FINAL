import typer
from rich.console import Console
from typing import List, Dict, Any, Tuple
from loguru import logger
from pathlib import Path
import ollama
import yaml
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from pydantic import BaseModel
import re
import json
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

def generate_answer_with_ollama(query: str, context_chunks: List[Dict[str, Any]]) -> Tuple[str, float, Dict[str, Any]]:
    """
    Enhanced answer generation with multi-stage approach and validation.
    """
    # Dynamic context length based on query complexity and mode
    query_complexity = analyze_query_complexity(query)
    
    if config.get("current_mode") == "low":
        max_context_length = config.get("max_context_length", 4000)
    else:
        if query_complexity == "simple":
            max_context_length = config.get("max_context_length_simple", 6000)
        elif query_complexity == "medium":
            max_context_length = config.get("max_context_length_medium", 8000)
        else:  # complex
            max_context_length = config.get("max_context_length_complex", 12000)
    
    context_text = ""
    total_length = 0
    
    for chunk in context_chunks:
        chunk_text = chunk['text']
        if total_length + len(chunk_text) <= max_context_length:
            context_text += chunk_text + "\n\n"
            total_length += len(chunk_text)
        else:
            if not context_text:
                context_text = chunk_text[:max_context_length] + "..."
            break
    
    # Stage 1: Generate initial answer
    initial_prompt = create_enhanced_prompt(query, context_text, "initial")
    initial_answer = generate_ollama_response(initial_prompt)

    # Stage 2: Refine and validate answer (Conditional)
    if not config.get("enable_multi_stage_generation", False):
        logger.info("Multi-stage generation is disabled. Using initial answer.")
        # When disabled, use the initial answer and proceed to validation
        refined_answer = initial_answer
    else:
        refinement_prompt = create_enhanced_prompt(query, context_text, "refinement", initial_answer)
        refined_answer = generate_ollama_response(refinement_prompt)
    
    # Ensure answer is not truncated and is complete
    if len(refined_answer) < 100 or "..." in refined_answer:
        if len(initial_answer) > len(refined_answer) and "..." not in initial_answer:
            refined_answer = initial_answer
        else:
            # Try to get a more complete answer
            complete_prompt = f"""
            The previous answer was incomplete. Please provide a complete answer to this question:
            {query}
            
            Context:
            {context_text}
            
            Provide a complete answer without truncation:
            """
            refined_answer = generate_ollama_response(complete_prompt)
    
    # Stage 3: Validate answer consistency
    validation_result = validate_answer_consistency(query, refined_answer, context_chunks)
    
    # Calculate confidence score
    confidence_score = calculate_confidence_score(refined_answer, validation_result, context_chunks)
    
    return refined_answer, confidence_score, validation_result

def analyze_query_complexity(query: str) -> str:
    """Analyze query complexity for dynamic context selection."""
    query_lower = query.lower()
    
    # Simple queries
    if any(word in query_lower for word in ['what is', 'which', 'where', 'when']):
        return "simple"
    
    # Medium complexity
    if any(word in query_lower for word in ['how to', 'configure', 'setup']):
        return "medium"
    
    # Complex queries
    if any(word in query_lower for word in ['troubleshoot', 'optimize', 'best practices', 'maintenance', 'issue', 'error', 'loading', 'failed']):
        return "complex"
    
    return "medium"

def create_enhanced_prompt(query: str, context: str, stage: str, previous_answer: str = "") -> str:
    """Create enhanced prompts for different generation stages."""
    
    if stage == "initial":
        return f"""
        Based on the following context from the Dell SRM guides, provide a focused and accurate answer.
        
        CRITICAL INSTRUCTIONS:
        1. ONLY use information that is explicitly stated in the provided context
        2. If the context contains procedure steps, PRESERVE THEM EXACTLY as written
        3. Do NOT invent, assume, or add information not present in the context
        4. Include ALL steps in the correct order with exact numbering when available
        5. Cite specific section titles and page numbers when available
        6. If context is incomplete, clearly state "The context does not contain sufficient information to answer this question completely"
        7. Keep answers concise and focused on what the context actually contains
        8. Do NOT reference external resources or make general statements
        9. IMPORTANT: If a step mentions a command but doesn't show the full command, state "Command details not provided in context"
        10. Ensure the answer is complete and not cut off
        
        FORMATTING REQUIREMENTS:
        - Use **bold** for section headers and important terms
        - Use numbered lists (1. 2. 3.) for procedure steps
        - Use bullet points (-) for lists of items
        - Use `code formatting` for commands, file paths, and technical terms
        - Use _italics_ for emphasis on key points
        - Structure the response with clear sections and proper spacing
        
        Context:
        ---
        {context}
        ---

        Question: {query}
        
        Answer (based ONLY on the context above):
        """
    
    elif stage == "refinement":
        return f"""
        Refine the following answer to be more accurate and focused. CRITICAL RULES:
        1. ONLY include information that is explicitly stated in the context
        2. Remove any invented or assumed information
        3. Ensure all procedure steps are exactly as written in the context
        4. Improve citations to reference specific sections and pages from the context
        5. Make the answer more concise and focused
        6. If the context is insufficient, clearly state this
        
        FORMATTING REQUIREMENTS:
        - Use **bold** for section headers and important terms
        - Use numbered lists (1. 2. 3.) for procedure steps
        - Use bullet points (-) for lists of items
        - Use `code formatting` for commands, file paths, and technical terms
        - Use _italics_ for emphasis on key points
        - Structure the response with clear sections and proper spacing
        
        Original Answer:
        {previous_answer}
        
        Context:
        ---
        {context}
        ---

        Question: {query}
        
        Refined Answer (based ONLY on the context above):
        """
    
    return ""

def generate_ollama_response(prompt: str) -> str:
    """Generate response using Ollama with error handling."""
    try:
        response = ollama.chat(
            model=config["ollama_model"],
            messages=[{'role': 'user', 'content': prompt}]
        )
        return response['message']['content']
    except Exception as e:
        logger.error(f"Error communicating with Ollama: {e}")
        return "Error: Could not generate an answer from the LLM."

def validate_answer_consistency(query: str, answer: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate answer consistency with context and generate validation metrics."""
    validation_metrics = {
        "context_alignment": 0.0,
        "fact_consistency": 0.0,
        "procedure_completeness": 0.0,
        "source_citation_quality": 0.0,
        "overall_validation_score": 0.0
    }
    
    # Context alignment check - more lenient for focused answers
    context_text = " ".join([chunk['text'] for chunk in context_chunks]).lower()
    answer_lower = answer.lower()
    
    # Check if answer terms are present in context
    answer_terms = set(re.findall(r'\b\w+\b', answer_lower))
    context_terms = set(re.findall(r'\b\w+\b', context_text))
    common_terms = answer_terms.intersection(context_terms)
    
    if answer_terms:
        # More lenient scoring - focus on key terms rather than all terms
        key_terms = [term for term in answer_terms if len(term) > 3]  # Focus on longer, more meaningful terms
        if key_terms:
            key_common_terms = [term for term in key_terms if term in context_terms]
            validation_metrics["context_alignment"] = len(key_common_terms) / len(key_terms)
        else:
            validation_metrics["context_alignment"] = len(common_terms) / len(answer_terms)
    
    # Fact consistency check
    fact_indicators = ['error', 'failed', 'success', 'complete', 'minimum', 'required']
    fact_consistency = 0
    for indicator in fact_indicators:
        if indicator in answer_lower and indicator in context_text:
            fact_consistency += 1
    
    validation_metrics["fact_consistency"] = min(fact_consistency / len(fact_indicators), 1.0)
    
    # Procedure completeness check
    if any(word in query.lower() for word in ['how', 'step', 'procedure']):
        step_count = len(re.findall(r'\d+\.', answer))
        validation_metrics["procedure_completeness"] = min(step_count / 5, 1.0)  # Normalize to 0-1
    
    # Source citation quality - more lenient
    citation_patterns = [r'page \d+', r'section [^,]+', r'chapter [^,]+']
    citations_found = sum(1 for pattern in citation_patterns if re.search(pattern, answer_lower))
    validation_metrics["source_citation_quality"] = min(citations_found / 2, 1.0)  # Reduced threshold
    
    # Calculate overall validation score with adjusted weights
    weights = {
        "context_alignment": 0.25,  # Reduced weight
        "fact_consistency": 0.3,    # Increased weight
        "procedure_completeness": 0.3,  # Increased weight
        "source_citation_quality": 0.15  # Reduced weight
    }
    
    overall_score = sum(validation_metrics[key] * weights[key] for key in weights.keys())
    validation_metrics["overall_validation_score"] = round(overall_score, 2)
    
    return validation_metrics

def calculate_confidence_score(answer: str, validation_result: Dict[str, Any], context_chunks: List[Dict[str, Any]]) -> float:
    """Calculate overall confidence score for the answer."""
    # Base confidence from validation
    base_confidence = validation_result.get("overall_validation_score", 0.0)
    
    # Context coverage confidence
    context_coverage = len(context_chunks) / config["top_k_reranked"]
    context_confidence = min(context_coverage, 1.0)
    
    # Answer length confidence (optimized for focused answers)
    answer_length = len(answer)
    if 100 <= answer_length <= 1500:  # More reasonable range for focused answers
        length_confidence = 1.0
    elif 50 <= answer_length < 100:
        length_confidence = 0.7
    elif 1500 < answer_length <= 2500:
        length_confidence = 0.8
    else:
        length_confidence = 0.4
    
    # Source diversity confidence
    unique_sources = len(set([chunk['metadata'].get('filename', '') for chunk in context_chunks]))
    source_confidence = min(unique_sources / 2, 1.0)  # Normalize to 0-1
    
    # Additional confidence from answer quality indicators
    answer_quality_confidence = 0.0
    if "the context does not contain sufficient information" in answer.lower():
        answer_quality_confidence = 0.8  # High confidence when honestly stating limitations
    elif any(word in answer.lower() for word in ['step', 'procedure', '1.', '2.', '3.']):
        answer_quality_confidence = 0.7  # Good confidence for procedural answers
    
    # Calculate weighted confidence
    confidence_weights = {
        "base_confidence": 0.35,
        "context_confidence": 0.2,
        "length_confidence": 0.15,
        "source_confidence": 0.15,
        "answer_quality": 0.15
    }
    
    final_confidence = (
        base_confidence * confidence_weights["base_confidence"] +
        context_confidence * confidence_weights["context_confidence"] +
        length_confidence * confidence_weights["length_confidence"] +
        source_confidence * confidence_weights["source_confidence"] +
        answer_quality_confidence * confidence_weights["answer_quality"]
    )
    
    return round(final_confidence, 2)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Check and auto-index on startup"""
    console.print("Checking for existing indexes...", style="bold yellow")
    if not rag_service.pdf_searcher:
        console.print("No indexes found. Auto-indexing documents...", style="bold yellow")
        rag_service.index_documents()
    else:
        console.print("Indexes found. Ready to serve queries.", style="bold green")
    yield

app = FastAPI(title="SRM RAG API", description="RAG system for Dell SRM guides", lifespan=lifespan)

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
            source_text = f"{source_info.get('filename', 'Unknown')} (Page {source_info.get('page_number', 'N/A')})"
            if source_info.get('section_title'):
                source_text += f" → Section: {source_info.get('section_title')}"
            
            sources.append({
                'text': source_text,
                'filename': source_info.get('filename'),
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
async def reindex_endpoint():
    """Force reindexing of documents"""
    try:
        results = rag_service.index_documents()
        return {"message": f"Successfully reindexed. Results: {results}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

cli_app = typer.Typer()

@cli_app.command()
def index():
    """Index the source documents."""
    console.print("Starting the indexing process...", style="bold green")
    results = rag_service.index_documents()
    console.print(f"Successfully indexed. Results: {results}", style="bold green")

@cli_app.command()
def ask(query: str):
    """Ask a question to the indexed documents."""
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
