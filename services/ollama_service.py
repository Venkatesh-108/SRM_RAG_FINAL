import ollama
from typing import List, Dict, Any, Tuple
from loguru import logger

def generate_answer_with_ollama(query: str, context_chunks: List[Dict[str, Any]], config: Dict[str, Any] = None) -> Tuple[str, float, Dict[str, Any]]:
    """
    Enhanced answer generation with multi-stage approach and validation.
    """
    # Dynamic context length based on query complexity and mode
    query_complexity = analyze_query_complexity(query)
    
    # Use configuration-based context length
    if config:
        if query_complexity == "simple":
            max_context_length = config.get("max_context_length_simple", 8000)
        elif query_complexity == "complex":
            max_context_length = config.get("max_context_length_complex", 14000)
        else:
            max_context_length = config.get("max_context_length_medium", 10000)
    else:
        max_context_length = 10000
    
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
    # For now, skip multi-stage generation to simplify
    refined_answer = initial_answer
    
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
        You are a Dell SRM technical expert. Answer the following question using the provided documentation context.
        
        INSTRUCTIONS:
        1. Provide direct, confident answers based on the context
        2. If the context contains procedure steps, include them exactly as written with proper numbering
        3. Include relevant section titles and page numbers when available
        4. Structure your response clearly with headings and bullet points when appropriate
        5. Be comprehensive but concise
        6. Only mention limitations if absolutely no relevant information exists
        
        Question: {query}
        
        Context from Dell SRM Documentation:
        {context}
        
        Answer:
        """
    
    elif stage == "refinement":
        return f"""
        Refine and improve the following answer based on the context. Make it more accurate, complete, and helpful.
        
        Original Question: {query}
        
        Context:
        {context}
        
        Previous Answer:
        {previous_answer}
        
        Refined Answer:
        """
    
    else:
        return f"""
        Answer the following question based on the provided context:
        
        Question: {query}
        
        Context:
        {context}
        
        Answer:
        """

def generate_ollama_response(prompt: str) -> str:
    """Generate response using Ollama."""
    try:
        response = ollama.chat(
            model='llama3.2:3b',
            messages=[
                {
                    'role': 'user',
                    'content': prompt,
                },
            ],
        )
        return response['message']['content']
    except Exception as e:
        logger.error(f"Error generating Ollama response: {e}")
        return f"I apologize, but I encountered an error while generating a response: {str(e)}"

def validate_answer_consistency(query: str, answer: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate answer consistency with context."""
    try:
        # Simple validation - check if answer contains key terms from context
        context_text = " ".join([chunk['text'] for chunk in context_chunks])
        context_terms = set(context_text.lower().split())
        answer_terms = set(answer.lower().split())
        
        # Calculate overlap
        overlap = len(context_terms.intersection(answer_terms))
        total_terms = len(answer_terms)
        
        consistency_score = overlap / total_terms if total_terms > 0 else 0
        
        return {
            "consistency_score": consistency_score,
            "overlap_terms": overlap,
            "total_terms": total_terms,
            "is_consistent": consistency_score > 0.3
        }
    except Exception as e:
        logger.error(f"Error validating answer consistency: {e}")
        return {
            "consistency_score": 0.0,
            "overlap_terms": 0,
            "total_terms": 0,
            "is_consistent": False,
            "error": str(e)
        }

def calculate_confidence_score(answer: str, validation_result: Dict[str, Any], context_chunks: List[Dict[str, Any]]) -> float:
    """Calculate confidence score for the answer."""
    try:
        base_score = 0.5
        
        # Boost based on consistency
        consistency_score = validation_result.get("consistency_score", 0.0)
        base_score += consistency_score * 0.3
        
        # Boost based on answer length (more detailed answers get higher scores)
        if len(answer) > 200:
            base_score += 0.1
        elif len(answer) > 100:
            base_score += 0.05
        
        # Boost based on number of context chunks used
        if len(context_chunks) > 3:
            base_score += 0.1
        elif len(context_chunks) > 1:
            base_score += 0.05
        
        # Cap at 1.0
        return min(base_score, 1.0)
        
    except Exception as e:
        logger.error(f"Error calculating confidence score: {e}")
        return 0.5
