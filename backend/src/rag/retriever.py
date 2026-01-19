"""
RAG retriever for semantic search and citation.
"""

import logging
from typing import List, Dict, Optional

# Use try/except for imports
try:
    from .vector_store import search_similar, get_by_city
    from ..models.itinerary_models import Source
except ImportError:
    from src.rag.vector_store import search_similar, get_by_city
    from src.models.itinerary_models import Source

logger = logging.getLogger(__name__)


def retrieve_city_tips(
    city: str,
    query: str,
    top_k: int = 5
) -> List[Dict]:
    """
    Retrieve city tips based on query.
    
    Args:
        city: City name
        query: Search query
        top_k: Number of results
    
    Returns:
        List of result dictionaries with text, metadata, and citations
    """
    try:
        results = search_similar(query, city=city, top_k=top_k)
        
        # Add citation information
        for result in results:
            metadata = result.get("metadata", {})
            result["citation"] = {
                "type": "wikivoyage",
                "url": metadata.get("source_url", ""),
                "section": metadata.get("section", ""),
                "city": metadata.get("city", city)
            }
        
        logger.info(f"Retrieved {len(results)} tips for {city}: {query}")
        return results
    
    except Exception as e:
        logger.error(f"Error retrieving city tips: {e}", exc_info=True)
        return []


def retrieve_safety_info(city: str) -> List[Dict]:
    """
    Retrieve safety information for a city.
    
    Args:
        city: City name
    
    Returns:
        List of safety-related documents
    """
    queries = [
        "safety tips",
        "stay safe",
        "safety precautions",
        "crime",
        "scams"
    ]
    
    all_results = []
    for query in queries:
        results = retrieve_city_tips(city, query, top_k=2)
        all_results.extend(results)
    
    # Remove duplicates (by text content)
    seen = set()
    unique_results = []
    for result in all_results:
        text_hash = hash(result.get("text", ""))
        if text_hash not in seen:
            seen.add(text_hash)
            unique_results.append(result)
    
    return unique_results[:5]  # Return top 5 unique results


def retrieve_indoor_alternatives(city: str) -> List[Dict]:
    """
    Retrieve indoor activity alternatives for a city.
    
    Args:
        city: City name
    
    Returns:
        List of indoor activity documents
    """
    queries = [
        "indoor activities",
        "museums",
        "shopping malls",
        "covered markets",
        "indoor attractions"
    ]
    
    all_results = []
    for query in queries:
        results = retrieve_city_tips(city, query, top_k=2)
        all_results.extend(results)
    
    # Remove duplicates
    seen = set()
    unique_results = []
    for result in all_results:
        text_hash = hash(result.get("text", ""))
        if text_hash not in seen:
            seen.add(text_hash)
            unique_results.append(result)
    
    return unique_results[:5]


def format_for_context(results: List[Dict]) -> str:
    """
    Format retrieval results for LLM context.
    
    Args:
        results: List of retrieval result dictionaries
    
    Returns:
        Formatted context string
    """
    if not results:
        return ""
    
    context_parts = []
    for i, result in enumerate(results, 1):
        text = result.get("text", "")
        metadata = result.get("metadata", {})
        section = metadata.get("section", "general")
        city = metadata.get("city", "unknown")
        
        context_parts.append(
            f"[{i}] Section: {section}\n"
            f"City: {city}\n"
            f"Content: {text}\n"
        )
    
    return "\n---\n".join(context_parts)


def format_with_citations(results: List[Dict]) -> tuple[str, List[Source]]:
    """
    Format results with citations for response.
    
    Args:
        results: List of retrieval result dictionaries
    
    Returns:
        Tuple of (formatted_text, list_of_sources)
    """
    if not results:
        return "", []
    
    context_parts = []
    sources = []
    
    for i, result in enumerate(results, 1):
        text = result.get("text", "")
        citation = result.get("citation", {})
        
        context_parts.append(f"[{i}] {text}")
        
        # Create Source object
        source = Source(
            type=citation.get("type", "wikivoyage"),
            url=citation.get("url"),
            section=citation.get("section"),
            topic=citation.get("city")
        )
        sources.append(source)
    
    formatted_text = "\n\n".join(context_parts)
    return formatted_text, sources
