import ollama
from typing import List, Dict, Any, Tuple
from loguru import logger

def generate_answer_with_ollama(query: str, context_chunks: List[Dict[str, Any]], config: Dict[str, Any] = None) -> Tuple[str, float, Dict[str, Any]]:
    """
    Enhanced answer generation with multi-stage approach and validation.
    """
    # Get the model name from config
    ollama_model = config.get("ollama_model", "phi3:3.8b") if config else "phi3:3.8b"
    
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
    initial_answer = generate_ollama_response(initial_prompt, model=ollama_model)

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
            refined_answer = generate_ollama_response(complete_prompt, model=ollama_model)
    
    # Stage 3: Validate answer consistency and check for hallucination
    validation_result = validate_answer_consistency(query, refined_answer, context_chunks)
    
    # Check for hallucinated content if strict mode is enabled
    if config and config.get("strict_mode", False):
        hallucination_check = detect_hallucination(refined_answer, context_text)
        if hallucination_check["has_hallucination"]:
            logger.warning(f"Hallucination detected in non-title match mode: {hallucination_check['issues']}")
            logger.warning(f"Severity: {hallucination_check.get('severity', 'unknown')}")

            # For non-title matches, be very strict about PDF-only responses
            if hallucination_check.get("severity") in ["high", "medium"]:
                logger.info("Strict mode: Replacing LLM response with PDF-only content")
                refined_answer = extract_safe_answer_from_context(query, context_text)
            else:
                # For low severity issues, try to generate a cleaner response
                logger.info("Strict mode: Regenerating response with stricter instructions")
                strict_prompt = create_strict_pdf_only_prompt(query, context_text)
                refined_answer = generate_ollama_response(strict_prompt, model=ollama_model)
    
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

def create_strict_pdf_only_prompt(query: str, context: str) -> str:
    """Create stricter prompt for PDF-focused responses when hallucination is detected."""
    return f"""
    You are a HCL SRM technical documentation assistant. Your previous response included some details not found in the documentation.
    Please provide a more accurate answer using the provided documentation.

    STRICT REQUIREMENTS:
    1. Base your answer ONLY on information in the context below
    2. Do NOT add specific UI element names, button labels, or navigation paths not in the context
    3. Do NOT fabricate procedural steps
    4. If the context doesn't fully answer the question, acknowledge what IS available and what is NOT
    5. Present information clearly and helpfully, but stay grounded in the documentation

    Question: {query}

    PDF Documentation Context:
    {context}

    Accurate Answer (based on documentation):
    """

def create_enhanced_prompt(query: str, context: str, stage: str, previous_answer: str = "") -> str:
    """Create enhanced prompts for different generation stages."""

    if stage == "initial":
        return f"""
        You are a HCL SRM technical documentation assistant. Answer questions based on the provided documentation.

        RESPONSE GUIDELINES:
        1. Prioritize information explicitly stated in the provided context
        2. Present information in a clear, helpful manner
        3. If the context contains procedural steps, present them clearly
        4. Use natural, instructional language when explaining procedures
        5. If specific details are missing from the context, acknowledge this limitation
        6. Quote directly from the context when it adds clarity
        7. Organize information logically (steps, lists, paragraphs as appropriate)

        IMPORTANT RESTRICTIONS:
        - Do NOT fabricate specific UI element names that aren't in the context (e.g., specific button names, menu paths)
        - Do NOT create detailed multi-level navigation paths unless they're in the context
        - Do NOT add troubleshooting steps not mentioned in the documentation
        - If the context doesn't fully answer the question, clearly state what information IS available

        HELPFUL PRACTICES:
        - Use clear, procedural language for step-by-step instructions
        - Organize information with proper formatting (numbered lists, sections, etc.)
        - Provide context and explanations where helpful
        - Be direct and concise while remaining thorough

        Question: {query}

        Context from HCL SRM Documentation:
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

def generate_ollama_response(prompt: str, model: str = 'phi3:3.8b') -> str:
    """Generate response using Ollama.
    
    Args:
        prompt: The prompt to send to the model
        model: The model name to use (from config.yaml)
    """
    try:
        response = ollama.chat(
            model=model,
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

def detect_hallucination(answer: str, context: str) -> Dict[str, Any]:
    """
    Balanced hallucination detection for PDF-based responses.
    Focuses on catching truly fabricated content while allowing reasonable instructional language.
    """
    # CRITICAL hallucination indicators - specific UI elements and paths that must be in context
    critical_hallucination_indicators = [
        # Very specific UI navigation that must be exact
        "System Resources > Frontend Servers",
        "Advanced Settings section",
        "Enable Frontend Server Tasks checkbox",
        "Send Frontend Server Data option",
        "log in to the HCL SRM console using a valid username and password",
    ]

    # Specific button/field names that must be in context
    specific_ui_elements = [
        "Edit button", "Save button", "Apply button", "Cancel button", "OK button",
        "Uncheck the boxes", "Click Save to apply", "Click Apply", "Click OK"
    ]

    # Pattern-based hallucination detection (only very specific patterns)
    critical_navigation_patterns = [
        r"navigate to.*>.*>.*>.*",  # Very specific multi-level navigation
        r"right-click.*and select",
        r"double-click.*to open"
    ]

    issues = []
    has_hallucination = False

    answer_lower = answer.lower()
    context_lower = context.lower()

    # Check for CRITICAL hallucination indicators (specific paths/elements)
    for indicator in critical_hallucination_indicators:
        if indicator.lower() in answer_lower and indicator.lower() not in context_lower:
            issues.append(f"Contains specific UI path not in context: {indicator}")
            has_hallucination = True

    # Check for specific UI elements only if they're very explicit
    for element in specific_ui_elements:
        if element.lower() in answer_lower and element.lower() not in context_lower:
            # Only flag if it's a very specific instruction, not general language
            if "click" in element.lower() or "button" in element.lower():
                issues.append(f"Contains specific UI element not in context: {element}")
                has_hallucination = True

    # Check for critical navigation patterns
    import re
    for pattern in critical_navigation_patterns:
        if re.search(pattern, answer_lower) and not re.search(pattern, context_lower):
            issues.append(f"Contains specific navigation not in context: {pattern}")
            has_hallucination = True

    # Check for fabricated technical details (very specific terms)
    answer_words = set(answer_lower.split())
    context_words = set(context_lower.split())

    # Only flag truly technical UI terms that are fabricated
    critical_technical_terms = {
        "checkbox", "dropdown", "textbox", "textarea", "radiobutton"
    }

    for term in critical_technical_terms:
        if term in answer_words and term not in context_words:
            issues.append(f"Contains specific UI control not in context: {term}")
            has_hallucination = True

    # Only flag severity as "high" if there are multiple critical issues
    # For basic helpful language (like "navigate to" or "recommended"), don't flag as hallucination
    return {
        "has_hallucination": has_hallucination,
        "issues": issues,
        "severity": "high" if len(issues) >= 3 else "medium" if len(issues) == 2 else "low",
        "confidence": 0.2 if len(issues) >= 3 else 0.5 if has_hallucination else 0.9
    }

def extract_safe_answer_from_context(query: str, context: str) -> str:
    """
    Extract exact content directly from context without any AI modification.
    This ensures complete accuracy when hallucination is detected.
    """
    query_lower = query.lower().strip()

    # For substantial context, try to find relevant content
    if len(context) > 200:
        # Look for key terms from the query in the context
        query_words = [word for word in query_lower.split() if len(word) > 3]
        context_lower = context.lower()

        # If we find most query terms in context, return relevant excerpts
        matching_words = sum(1 for word in query_words if word in context_lower)
        if matching_words >= len(query_words) * 0.6:  # 60% of query words found

            # Try to find the most relevant paragraph
            paragraphs = context.split('\n\n')
            best_paragraph = ""
            best_score = 0

            for paragraph in paragraphs:
                if len(paragraph.strip()) > 50:  # Substantial paragraph
                    para_lower = paragraph.lower()
                    score = sum(1 for word in query_words if word in para_lower)
                    if score > best_score:
                        best_score = score
                        best_paragraph = paragraph.strip()

            if best_paragraph and best_score > 0:
                return f"According to the available documentation:\n\n{best_paragraph}"

        # If context is substantial but doesn't match well, return acknowledgment with limited info
        if len(context.strip()) > 100:
            # Return first substantial sentence that might be relevant
            sentences = context.replace('\n', ' ').split('.')
            for sentence in sentences[:3]:  # Check first 3 sentences
                sentence = sentence.strip()
                if len(sentence) > 30 and any(word in sentence.lower() for word in query_words):
                    return f"The available documentation mentions: {sentence}.\n\nHowever, specific details for your question are not fully covered in the provided documentation sections."

    # Fallback for cases where context doesn't sufficiently match the query
    return "The available documentation does not contain sufficient information to answer this question fully. Please refer to the complete HCL SRM documentation or contact support for detailed guidance on this topic."
