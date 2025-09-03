import typer
from rich.console import Console
from typing import List, Dict, Any, Tuple
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
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from pydantic import BaseModel
import re
from collections import Counter
import json

# Import new chat models and services
from models.chat import (
    ChatSession, ChatMessage, CreateSessionRequest, 
    SendMessageRequest, ChatResponse, SessionListResponse
)
from services.chat_service import ChatService

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

# Initialize chat service
chat_service = ChatService()

# Pydantic models
class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    answer: str
    context: List[Dict[str, Any]]
    sources: List[str]
    confidence_score: float
    answer_validation: Dict[str, Any]

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
    Enhanced contextual chunking with semantic awareness and overlap.
    """
    chunks = []
    current_chunk = {"text": "", "metadata": {}}
    section_title = "Introduction"
    chunk_id = 0

    for el in elements:
        metadata = el.metadata.to_dict()
        
        if isinstance(el, Title):
            # When a new title is found, save the previous chunk if it has content
            if current_chunk["text"].strip():
                current_chunk["metadata"]["section_title"] = section_title
                current_chunk["metadata"]["chunk_id"] = chunk_id
                current_chunk["metadata"]["chunk_type"] = determine_chunk_type(current_chunk["text"])
                chunks.append(current_chunk)
                chunk_id += 1

            # Start a new chunk
            section_title = el.text.strip()
            current_chunk = {"text": el.text, "metadata": metadata}

        elif isinstance(el, ListItem):
            # Add list items to the current chunk
            current_chunk["text"] += f"\n- {el.text}"
            if "procedure" not in current_chunk["metadata"].get("type", ""):
                 current_chunk["metadata"]["type"] = "procedure"

        else:
            # Append other text elements to the current chunk
            current_chunk["text"] += f"\n{el.text}"

    # Add the last processed chunk if it exists
    if current_chunk["text"].strip():
        current_chunk["metadata"]["section_title"] = section_title
        current_chunk["metadata"]["chunk_id"] = chunk_id
        current_chunk["metadata"]["chunk_type"] = determine_chunk_type(current_chunk["text"])
        chunks.append(current_chunk)
    
    # Create overlapping chunks for better context continuity
    overlapping_chunks = create_overlapping_chunks(chunks)
    
    logger.info(f"Chunked {len(elements)} elements into {len(overlapping_chunks)} contextual chunks with overlap.")
    return overlapping_chunks

def determine_chunk_type(text: str) -> str:
    """Determine the type of chunk based on content analysis."""
    text_lower = text.lower()
    
    if any(word in text_lower for word in ['step', 'procedure', 'how to', 'instructions']):
        return "procedure"
    elif any(word in text_lower for word in ['error', 'failed', 'troubleshoot', 'fix', 'issue']):
        return "troubleshooting"
    elif any(word in text_lower for word in ['requirement', 'minimum', 'specification', 'gb', 'ram', 'cpu']):
        return "requirements"
    elif any(word in text_lower for word in ['backup', 'recovery', 'restore', 'snapshot']):
        return "backup_recovery"
    else:
        return "general"

def create_overlapping_chunks(chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Create overlapping chunks for better context continuity."""
    overlapping_chunks = []
    
    for i, chunk in enumerate(chunks):
        # Add the original chunk
        overlapping_chunks.append(chunk)
        
        # Create overlapping chunk with previous context if available
        if i > 0:
            prev_chunk = chunks[i-1]
            overlap_text = f"{prev_chunk['text'][-200:]}\n\n{chunk['text']}"
            
            overlap_chunk = {
                "text": overlap_text,
                "metadata": {
                    **chunk["metadata"],
                    "chunk_id": f"{chunk['metadata']['chunk_id']}_overlap",
                    "chunk_type": "overlap",
                    "overlaps_with": [prev_chunk["metadata"]["chunk_id"], chunk["metadata"]["chunk_id"]]
                }
            }
            overlapping_chunks.append(overlap_chunk)
    
    return overlapping_chunks

def create_and_save_index(chunks: List[Dict[str, Any]]):
    """
    Creates and saves enhanced indices with metadata.
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

def generate_multiple_queries(query: str) -> List[str]:
    """
    Generate multiple search queries using query expansion and rephrasing.
    This is a key technique for improving retrieval coverage.
    """
    queries = [query]  # Original query
    
    # Query expansion based on common SRM terms
    srm_terms = {
        'upgrade': ['update', 'install', 'deploy', 'migrate'],
        'configure': ['setup', 'install', 'deploy', 'arrange'],
        'backup': ['restore', 'recovery', 'snapshot', 'copy'],
        'troubleshoot': ['fix', 'resolve', 'error', 'failed', 'issue'],
        'requirement': ['specification', 'minimum', 'needed', 'prerequisite'],
        'network': ['connection', 'connectivity', 'communication'],
        'performance': ['optimization', 'tuning', 'speed', 'efficiency'],
        'monitoring': ['alert', 'watch', 'observe', 'track'],
        'authentication': ['login', 'user', 'permission', 'access'],
        'maintenance': ['update', 'patch', 'service', 'care'],
        'issue': ['problem', 'error', 'failed', 'trouble', 'loading'],
        'loading': ['start', 'boot', 'initialize', 'launch', 'load'],
        'ui': ['interface', 'user interface', 'gui', 'web interface'],
        'apg': ['application', 'service', 'process']
    }
    
    # Generate variations
    for original_term, synonyms in srm_terms.items():
        if original_term in query.lower():
            for synonym in synonyms:
                new_query = query.lower().replace(original_term, synonym)
                if new_query != query.lower():
                    queries.append(new_query)
    
    # Add question type variations
    if query.lower().startswith('how do i'):
        queries.append(query.lower().replace('how do i', 'what are the steps to'))
        queries.append(query.lower().replace('how do i', 'procedure for'))
    
    if query.lower().startswith('what are'):
        queries.append(query.lower().replace('what are', 'how to configure'))
        queries.append(query.lower().replace('what are', 'steps for'))
    
    # Remove duplicates and limit to reasonable number
    unique_queries = list(dict.fromkeys(queries))[:5]
    
    logger.info(f"Generated {len(unique_queries)} search queries from original query")
    return unique_queries

def search_and_rerank(query: str, chunks, bm25, faiss_index, embedding_model):
    """
    Enhanced hybrid search with multi-query generation and advanced reranking.
    """
    # Generate multiple queries for better coverage
    multiple_queries = generate_multiple_queries(query)
    
    # Analyze query type for better context selection
    query_lower = query.lower()
    is_procedure_query = any(word in query_lower for word in ['how to', 'steps', 'procedure', 'process'])
    is_fact_query = any(word in query_lower for word in ['what is', 'which', 'where', 'when'])
    is_troubleshooting_query = any(word in query_lower for word in ['error', 'failed', 'troubleshoot', 'fix'])
    
    # Adjust search parameters based on query type
    if is_procedure_query:
        top_k_bm25 = min(config["top_k_bm25"] + 3, 12)
        top_k_faiss = min(config["top_k_faiss"] + 3, 12)
    elif is_troubleshooting_query:
        top_k_bm25 = config["top_k_bm25"] + 2
        top_k_faiss = config["top_k_faiss"] + 2
    else:
        top_k_bm25 = max(config["top_k_bm25"] - 1, 3)
        top_k_faiss = max(config["top_k_faiss"] - 1, 3)
    
    all_candidates = set()
    
    # Search with multiple queries
    for search_query in multiple_queries:
        # BM25 search
        tokenized_query = search_query.split(" ")
        bm25_scores = bm25.get_scores(tokenized_query)
        top_k_bm25_indices = np.argsort(bm25_scores)[::-1][:top_k_bm25]
        
        # FAISS search
        query_embedding = embedding_model.encode([search_query])
        _, top_k_faiss_indices = faiss_index.search(np.array(query_embedding, dtype='f4'), top_k_faiss)
        top_k_faiss_indices = top_k_faiss_indices[0]
        
        # Add to candidates
        all_candidates.update(top_k_bm25_indices)
        all_candidates.update(top_k_faiss_indices)
    
    # Convert to list
    combined_indices = list(all_candidates)
    
    # --- Enhanced Reranking ---
    cross_encoder = CrossEncoder(config["reranker_model"])
    
    # Create pairs for reranking
    pairs = [[query, chunks[i]["text"]] for i in combined_indices]
    scores = cross_encoder.predict(pairs)
    
    # Apply additional scoring factors
    enhanced_scores = []
    for i, (idx, score) in enumerate(zip(combined_indices, scores)):
        chunk = chunks[idx]
        
        # Content relevance scoring
        query_terms = query.lower().split()
        chunk_text = chunk['text'].lower()
        term_overlap = sum(1 for term in query_terms if term in chunk_text)
        
        # Chunk type relevance
        chunk_type = chunk['metadata'].get('chunk_type', 'general')
        type_relevance = get_chunk_type_relevance(query_lower, chunk_type)
        
        # Metadata quality scoring
        metadata_score = get_metadata_quality_score(chunk)
        
        # Combine scores with weights
        enhanced_score = (
            score * 0.5 +                    # Cross-encoder score
            term_overlap * 0.2 +             # Term overlap
            type_relevance * 0.2 +           # Chunk type relevance
            metadata_score * 0.1             # Metadata quality
        )
        
        enhanced_scores.append((idx, enhanced_score))
    
    # Sort by enhanced scores
    enhanced_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Get top results after reranking
    top_k_final_indices = [idx for idx, _ in enhanced_scores[:config["top_k_reranked"]]]
    
    # Smart context selection with diversity
    retrieved_chunks = select_diverse_chunks(chunks, top_k_final_indices, query)
    
    return retrieved_chunks

def get_chunk_type_relevance(query: str, chunk_type: str) -> float:
    """Calculate relevance score based on chunk type and query type."""
    query_lower = query.lower()
    
    if chunk_type == "procedure" and any(word in query_lower for word in ['how', 'step', 'procedure']):
        return 1.0
    elif chunk_type == "troubleshooting" and any(word in query_lower for word in ['error', 'failed', 'fix', 'issue']):
        return 1.0
    elif chunk_type == "requirements" and any(word in query_lower for word in ['requirement', 'minimum', 'specification']):
        return 1.0
    elif chunk_type == "backup_recovery" and any(word in query_lower for word in ['backup', 'recovery', 'restore']):
        return 1.0
    else:
        return 0.5

def get_metadata_quality_score(chunk: Dict[str, Any]) -> float:
    """Calculate metadata quality score."""
    score = 0.0
    
    # Check for important metadata fields
    if chunk['metadata'].get('section_title'):
        score += 0.3
    if chunk['metadata'].get('page_number'):
        score += 0.2
    if chunk['metadata'].get('filename'):
        score += 0.2
    if chunk['metadata'].get('chunk_type'):
        score += 0.3
    
    return score

def select_diverse_chunks(chunks: List[Dict[str, Any]], indices: List[int], query: str) -> List[Dict[str, Any]]:
    """Select diverse chunks to avoid redundancy while maintaining relevance."""
    selected_chunks = []
    used_sections = set()
    used_types = set()
    
    for idx in indices:
        chunk = chunks[idx]
        section = chunk['metadata'].get('section_title', '')
        chunk_type = chunk['metadata'].get('chunk_type', 'general')
        
        # Calculate diversity penalty
        diversity_penalty = 0
        if section in used_sections:
            diversity_penalty += 0.2  # Reduced penalty
        if chunk_type in used_types:
            diversity_penalty += 0.1  # Reduced penalty
        
        # Apply diversity penalty to relevance score
        relevance_score = chunk['metadata'].get('relevance_score', 0)
        adjusted_score = relevance_score * (1 - diversity_penalty)
        
        # Add to selected chunks
        selected_chunks.append({
            **chunk,
            'metadata': {
                **chunk['metadata'],
                'diversity_score': adjusted_score
            }
        })
        
        # Update used sets
        used_sections.add(section)
        used_types.add(chunk_type)
    
    # Sort by diversity-adjusted score
    selected_chunks.sort(key=lambda x: x['metadata'].get('diversity_score', 0), reverse=True)
    
    return selected_chunks

def generate_answer_with_ollama(query: str, context_chunks: List[Dict[str, Any]]) -> Tuple[str, float, Dict[str, Any]]:
    """
    Enhanced answer generation with multi-stage approach and validation.
    """
    # Dynamic context length based on query complexity
    query_complexity = analyze_query_complexity(query)
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
    
    # Stage 2: Refine and validate answer
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

# FastAPI endpoints
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Check and auto-index on startup"""
    check_and_auto_index()
    yield

app = FastAPI(title="SRM RAG API", description="RAG system for Dell SRM guides", lifespan=lifespan)

# Mount static files and templates
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="templates/static"), name="static")

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
        # Load indices
        chunks, bm25, faiss_index, embedding_model = load_indices_and_chunks()
        if chunks is None:
            raise HTTPException(status_code=500, detail="Index not found. Please ensure documents are indexed.")
        
        # Search and rerank
        retrieved_chunks = search_and_rerank(request.query, chunks, bm25, faiss_index, embedding_model)
        
        # Generate answer
        answer, confidence_score, validation_result = generate_answer_with_ollama(request.query, retrieved_chunks)
        
        # Extract sources with better metadata and relevance scoring
        sources = []
        for chunk in retrieved_chunks:
            source = chunk['metadata'].get('filename', 'Unknown')
            page = chunk['metadata'].get('page_number', 'N/A')
            section_title = chunk['metadata'].get('section_title', '')
            step_count = chunk['metadata'].get('step_count', '')
            relevance_score = chunk['metadata'].get('relevance_score', 0)
            
            # Create enhanced source citation
            if section_title:
                if step_count and step_count > 1:
                    source_text = f"{source} (Page {page}) → Section: {section_title} → {step_count} steps"
                else:
                    source_text = f"{source} (Page {page}) → Section: {section_title}"
            else:
                source_text = f"{source} (Page {page})"
            
            # Add relevance indicator for debugging
            if relevance_score > 0:
                source_text += f" [Relevance: {relevance_score}]"
            
            sources.append(source_text)
        
        return QueryResponse(
            answer=answer,
            context=[{"text": chunk['text'][:200] + "...", "metadata": chunk['metadata']} for chunk in retrieved_chunks],
            sources=sources,
            confidence_score=confidence_score,
            answer_validation=validation_result
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
    answer, confidence_score, validation_result = generate_answer_with_ollama(query, retrieved_chunks)
    
    console.print("\n--- Answer ---", style="bold green")
    console.print(answer)
    
    console.print(f"\n--- Confidence Score: {confidence_score:.2f}/1.0 ---", style="bold blue")
    console.print(f"--- Validation Score: {validation_result.get('overall_validation_score', 0):.2f}/1.0 ---", style="bold blue")

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
