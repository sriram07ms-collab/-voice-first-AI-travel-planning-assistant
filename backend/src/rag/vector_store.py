"""
ChromaDB vector store setup for RAG.
Stores and retrieves Wikivoyage content with embeddings.
"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import logging
from pathlib import Path

# Use try/except for imports
try:
    from ..utils.config import settings
except ImportError:
    from src.utils.config import settings

logger = logging.getLogger(__name__)

# Global ChromaDB client
_chroma_client: Optional[chromadb.ClientAPI] = None
_collection: Optional[chromadb.Collection] = None


def initialize_store(persist_directory: str = None) -> chromadb.ClientAPI:
    """
    Initialize ChromaDB with persistent storage.
    
    Args:
        persist_directory: Directory to persist data (defaults to settings)
    
    Returns:
        ChromaDB client
    """
    global _chroma_client
    
    if _chroma_client is not None:
        return _chroma_client
    
    persist_dir = persist_directory or settings.chroma_persist_dir
    
    # Create directory if it doesn't exist
    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Initializing ChromaDB at {persist_dir}")
    
    _chroma_client = chromadb.PersistentClient(
        path=persist_dir,
        settings=Settings(
            anonymized_telemetry=False,
            allow_reset=True
        )
    )
    
    logger.info("ChromaDB initialized successfully")
    return _chroma_client


def get_collection(collection_name: str = "wikivoyage") -> chromadb.Collection:
    """
    Get or create ChromaDB collection.
    
    Args:
        collection_name: Name of the collection
    
    Returns:
        ChromaDB collection
    """
    global _collection
    
    if _collection is not None:
        return _collection
    
    client = initialize_store()
    
    try:
        _collection = client.get_collection(name=collection_name)
        logger.info(f"Retrieved existing collection: {collection_name}")
    except Exception:
        # Collection doesn't exist, create it
        _collection = client.create_collection(
            name=collection_name,
            metadata={"description": "Wikivoyage city guides and travel tips"}
        )
        logger.info(f"Created new collection: {collection_name}")
    
    return _collection


def add_documents(
    documents: List[str],
    metadatas: List[Dict],
    ids: Optional[List[str]] = None,
    collection_name: str = "wikivoyage"
) -> None:
    """
    Add documents to vector store.
    
    Args:
        documents: List of document texts
        metadatas: List of metadata dictionaries
        ids: Optional list of document IDs
        collection_name: Collection name
    """
    collection = get_collection(collection_name)
    
    # Generate IDs if not provided
    if ids is None:
        ids = [f"doc_{i}_{hash(doc) % 100000}" for i, doc in enumerate(documents)]
    
    # Ensure all metadata have required fields
    for metadata in metadatas:
        if "city" not in metadata:
            metadata["city"] = "unknown"
        if "source_url" not in metadata:
            metadata["source_url"] = ""
        if "section" not in metadata:
            metadata["section"] = "general"
    
    try:
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"Added {len(documents)} documents to collection")
    except Exception as e:
        logger.error(f"Error adding documents: {e}", exc_info=True)
        raise


def search_similar(
    query: str,
    city: Optional[str] = None,
    top_k: int = 5,
    collection_name: str = "wikivoyage"
) -> List[Dict]:
    """
    Search for similar documents using semantic search.
    
    Args:
        query: Search query
        city: Optional city filter
        top_k: Number of results to return
        collection_name: Collection name
    
    Returns:
        List of result dictionaries with document, metadata, and distance
    """
    collection = get_collection(collection_name)
    
    # Build where clause if city is specified
    where_clause = None
    if city:
        where_clause = {"city": city}
    
    try:
        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where_clause
        )
        
        # Format results
        formatted_results = []
        
        if results["documents"] and len(results["documents"]) > 0:
            docs = results["documents"][0]
            metadatas = results["metadatas"][0]
            distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)
            ids = results["ids"][0]
            
            for i, doc in enumerate(docs):
                formatted_results.append({
                    "text": doc,
                    "metadata": metadatas[i] if i < len(metadatas) else {},
                    "distance": distances[i] if i < len(distances) else 0.0,
                    "id": ids[i] if i < len(ids) else None
                })
        
        logger.debug(f"Found {len(formatted_results)} similar documents")
        return formatted_results
    
    except Exception as e:
        logger.error(f"Error searching vector store: {e}", exc_info=True)
        return []


def get_by_city(city: str, collection_name: str = "wikivoyage") -> List[Dict]:
    """
    Get all documents for a specific city.
    
    Args:
        city: City name
        collection_name: Collection name
    
    Returns:
        List of document dictionaries
    """
    collection = get_collection(collection_name)
    
    try:
        results = collection.get(
            where={"city": city}
        )
        
        formatted_results = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"]):
                formatted_results.append({
                    "text": doc,
                    "metadata": results["metadatas"][i] if results.get("metadatas") else {},
                    "id": results["ids"][i] if results.get("ids") else None
                })
        
        logger.info(f"Retrieved {len(formatted_results)} documents for {city}")
        return formatted_results
    
    except Exception as e:
        logger.error(f"Error getting documents by city: {e}", exc_info=True)
        return []


def delete_by_city(city: str, collection_name: str = "wikivoyage") -> None:
    """
    Delete all documents for a specific city.
    Useful for refreshing city data.
    
    Args:
        city: City name
        collection_name: Collection name
    """
    collection = get_collection(collection_name)
    
    try:
        # Get all IDs for this city
        results = collection.get(
            where={"city": city}
        )
        
        if results.get("ids"):
            collection.delete(ids=results["ids"])
            logger.info(f"Deleted {len(results['ids'])} documents for {city}")
    
    except Exception as e:
        logger.error(f"Error deleting documents by city: {e}", exc_info=True)
