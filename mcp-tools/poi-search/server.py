"""
POI Search MCP Tool Server
Implements the search_pois MCP tool for finding Points of Interest.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add backend to path
backend_dir = Path(__file__).parent.parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

try:
    from src.data_sources.poi_search import search_pois
    from src.models.itinerary_models import POI, Location
except ImportError:
    # Fallback for direct imports
    sys.path.insert(0, str(backend_dir / "src"))
    from data_sources.poi_search import search_pois
    from models.itinerary_models import POI, Location

logger = logging.getLogger(__name__)


def search_pois_mcp(
    city: str,
    interests: List[str],
    constraints: Optional[Dict[str, Any]] = None,
    country: Optional[str] = None,
    limit: int = 50
) -> Dict[str, Any]:
    """
    MCP Tool: Search for Points of Interest in a city.
    
    This is the MCP-compliant wrapper around the OpenStreetMap POI search.
    
    Args:
        city: City name (e.g., "Jaipur")
        interests: List of interests (e.g., ["food", "culture"])
        constraints: Optional constraints dict with:
            - budget: "low" | "moderate" | "high" | None
            - accessibility: bool | None
            - time_of_day: "morning" | "afternoon" | "evening" | None
        country: Optional country name for better geocoding (e.g., "India")
        limit: Maximum number of POIs to return (default: 50)
    
    Returns:
        Dictionary with MCP-compliant structure:
        {
            "pois": [
                {
                    "name": str,
                    "category": str,
                    "location": {"lat": float, "lon": float},
                    "duration_minutes": int,
                    "data_source": "openstreetmap",
                    "source_id": str,
                    "rating": float | None,
                    "description": str | None
                }
            ]
        }
    """
    try:
        logger.info(f"MCP POI Search: city={city}, country={country}, interests={interests}, constraints={constraints}")
        
        # Call the unified POI search (Google Places first, Overpass fallback)
        pois = search_pois(
            city=city,
            interests=interests,
            constraints=constraints or {},
            country=country,
            limit=limit
        )
        
        # Convert POI models to dictionaries
        pois_list = []
        for poi in pois:
            poi_dict = {
                "name": poi.name,
                "category": poi.category,
                "location": {
                    "lat": poi.location.lat,
                    "lon": poi.location.lon
                },
                "duration_minutes": poi.duration_minutes,
                "data_source": poi.data_source,  # Critical: preserve data_source for source attribution
                "source_id": poi.source_id,
                "rating": poi.rating,
                "description": poi.description,
                "opening_hours": getattr(poi, 'opening_hours', None)
            }
            # Log data_source for debugging
            if poi.data_source == "google_places":
                logger.debug(f"POI '{poi.name}' has data_source='google_places'")
            pois_list.append(poi_dict)
        
        logger.info(f"MCP POI Search: Found {len(pois_list)} POIs")
        
        return {
            "pois": pois_list,
            "count": len(pois_list),
            "city": city,
            "interests": interests
        }
    
    except Exception as e:
        logger.error(f"MCP POI Search error: {e}", exc_info=True)
        return {
            "pois": [],
            "count": 0,
            "error": str(e),
            "city": city,
            "interests": interests
        }


# For direct testing
if __name__ == "__main__":
    # Test the MCP tool
    result = search_pois_mcp(
        city="Jaipur",
        interests=["culture", "food"],
        constraints={"budget": "moderate"},
        limit=5
    )
    print(f"Found {result['count']} POIs")
    for poi in result["pois"][:3]:
        print(f"  - {poi['name']} ({poi['category']})")
