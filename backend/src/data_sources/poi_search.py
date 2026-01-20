"""
Unified POI search that uses Google Places API first, falls back to OpenStreetMap.
This is the main entry point for POI searches.
"""

from typing import List, Optional, Dict, Any
import logging

try:
    from .google_places import search_pois_google_places
    from .openstreetmap import search_pois_overpass
    from ..models.itinerary_models import POI
except ImportError:
    from src.data_sources.google_places import search_pois_google_places
    from src.data_sources.openstreetmap import search_pois_overpass
    from src.models.itinerary_models import POI

logger = logging.getLogger(__name__)


def search_pois(
    city: str,
    interests: List[str],
    constraints: Optional[Dict[str, Any]] = None,
    country: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 50
) -> List[POI]:
    """
    Search for Points of Interest in a city.
    Tries Google Places API first, falls back to OpenStreetMap/Overpass API.
    
    Priority: Google Places API → OpenStreetMap/Overpass API
    
    Args:
        city: City name
        interests: List of interests (e.g., ['food', 'culture'])
        constraints: Optional constraints (budget, accessibility, time_of_day)
        country: Optional country name
        state: Optional state/province name
        limit: Maximum number of POIs to return
    
    Returns:
        List of POI objects
    """
    # Try Google Places API first (if configured)
    logger.info(f"🔍 Searching POIs for {city} - PRIORITY: Google Places API first")
    
    # Check if Google Maps API key is configured
    try:
        from ..utils.config import get_settings
        settings = get_settings()
        google_api_configured = bool(settings.google_maps_api_key)
    except Exception:
        google_api_configured = False
    
    if not google_api_configured:
        logger.warning(f"⚠️ Google Maps API key not configured. Set GOOGLE_MAPS_API_KEY environment variable to use Google Places API. Falling back to OpenStreetMap.")
    else:
        logger.info(f"✅ Google Maps API key is configured, using Google Places API for {city}")
    
    google_pois = []
    google_api_used = False
    google_api_error = None
    
    if google_api_configured:
        try:
            google_pois = search_pois_google_places(
                city=city,
                interests=interests,
                constraints=constraints,
                country=country,
                state=state,
                limit=limit
            )
            google_api_used = True
            
            if google_pois:
                # Verify data_source is set correctly
                google_count = len([p for p in google_pois if p.data_source == "google_places"])
                logger.info(f"✅ Google Places API returned {len(google_pois)} POIs for {city} ({google_count} with google_places data_source)")
                if google_count < len(google_pois):
                    logger.warning(f"⚠️ Some POIs missing google_places data_source: {len(google_pois) - google_count}")
                
                # Log sample POIs to verify data
                if google_pois:
                    sample_poi = google_pois[0]
                    logger.info(f"📊 Sample POI: {sample_poi.name} (data_source: {sample_poi.data_source}, duration: {sample_poi.duration_minutes}min, rating: {sample_poi.rating})")
                
                return google_pois
            else:
                logger.warning(f"⚠️ Google Places API returned no results for {city} with interests {interests}")
        except Exception as e:
            google_api_error = str(e)
            logger.error(f"❌ Google Places API failed for {city}: {e}", exc_info=True)
    
    # Fallback to OpenStreetMap/Overpass API
    if google_api_used:
        logger.warning(f"⚠️ Google Places API returned no results, falling back to OpenStreetMap/Overpass API")
    else:
        logger.info(f"⚠️ Using OpenStreetMap/Overpass API (Google Places API {'not configured' if not google_api_configured else 'failed'})")
    
    try:
        overpass_pois = search_pois_overpass(
            city=city,
            interests=interests,
            constraints=constraints,
            country=country,
            state=state,
            limit=limit
        )
        
        if overpass_pois:
            logger.info(f"✅ OpenStreetMap/Overpass API returned {len(overpass_pois)} POIs for {city}")
            return overpass_pois
        else:
            logger.warning(f"⚠️ Both Google Places and OpenStreetMap returned no POIs for {city}")
            return []
            
    except Exception as e:
        logger.error(f"OpenStreetMap/Overpass API fallback failed: {e}", exc_info=True)
        return []
