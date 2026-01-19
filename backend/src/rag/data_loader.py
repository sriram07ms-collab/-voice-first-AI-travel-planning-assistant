"""
Data loader for Wikivoyage content into vector store.
"""

import logging
from typing import List, Optional

# Use try/except for imports
try:
    from ..data_sources.wikivoyage import scrape_city_page, chunk_text, get_city_url
    from .vector_store import add_documents, delete_by_city, initialize_store
    from ..utils.config import settings
except ImportError:
    from src.data_sources.wikivoyage import scrape_city_page, chunk_text, get_city_url
    from src.rag.vector_store import add_documents, delete_by_city, initialize_store
    from src.utils.config import settings

logger = logging.getLogger(__name__)

# Note: ChromaDB uses its default embedding function
# For production, you can configure custom embeddings (OpenAI, local models, etc.)
# ChromaDB's default embedding function works well for most use cases


def load_wikivoyage_data(cities: List[str], refresh: bool = False) -> None:
    """
    Load Wikivoyage data for cities into vector store.
    
    Args:
        cities: List of city names
        refresh: If True, delete existing data before loading
    """
    # Initialize vector store
    initialize_store()
    
    for city in cities:
        try:
            logger.info(f"Loading Wikivoyage data for {city}")
            
            # Delete existing data if refreshing
            if refresh:
                delete_by_city(city)
            
            # Scrape city page
            sections = scrape_city_page(city)
            
            if not sections:
                logger.warning(f"No sections found for {city}")
                continue
            
            # Prepare documents and metadata
            documents = []
            metadatas = []
            city_url = get_city_url(city)
            
            for section_name, content in sections.items():
                # Chunk the content
                chunks = chunk_text(content, max_tokens=500, overlap=50)
                
                for i, chunk in enumerate(chunks):
                    documents.append(chunk)
                    metadatas.append({
                        "city": city,
                        "section": section_name,
                        "source_url": city_url,
                        "page_title": city,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    })
            
            # Add to vector store
            if documents:
                add_documents(
                    documents=documents,
                    metadatas=metadatas,
                    collection_name="wikivoyage"
                )
                logger.info(f"Loaded {len(documents)} chunks for {city}")
            else:
                logger.warning(f"No documents to load for {city}")
        
        except Exception as e:
            logger.error(f"Error loading data for {city}: {e}", exc_info=True)
            continue


def preload_common_cities(cities: Optional[List[str]] = None) -> None:
    """
    Preload data for common cities.
    
    Args:
        cities: List of cities to preload (defaults to common Indian cities)
    """
    if cities is None:
        cities = [
            "Jaipur",
            "Mumbai",
            "Delhi",
            "Bangalore",
            "Goa",
            "Kolkata",
            "Chennai",
            "Hyderabad",
            "Pune",
            "Udaipur"
        ]
    
    logger.info(f"Preloading data for {len(cities)} cities")
    load_wikivoyage_data(cities, refresh=False)
