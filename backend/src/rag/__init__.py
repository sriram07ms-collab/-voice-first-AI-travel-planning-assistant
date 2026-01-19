"""
RAG (Retrieval-Augmented Generation) module.
"""

from .vector_store import (
    initialize_store,
    get_collection,
    add_documents,
    search_similar,
    get_by_city,
    delete_by_city
)
from .retriever import (
    retrieve_city_tips,
    retrieve_safety_info,
    retrieve_indoor_alternatives,
    format_for_context,
    format_with_citations
)
from .data_loader import (
    load_wikivoyage_data,
    preload_common_cities
)

__all__ = [
    "initialize_store",
    "get_collection",
    "add_documents",
    "search_similar",
    "get_by_city",
    "delete_by_city",
    "retrieve_city_tips",
    "retrieve_safety_info",
    "retrieve_indoor_alternatives",
    "format_for_context",
    "format_with_citations",
    "load_wikivoyage_data",
    "preload_common_cities"
]
