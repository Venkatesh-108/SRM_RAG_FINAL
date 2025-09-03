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

from data_loader import load_documents
from config import config

app = typer.Typer()
console = Console()

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
            # For now, el.metadata.text_as_html is a good source for structure
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


@app.command()
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

@app.command()
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
    app()
