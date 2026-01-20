"""
Geocoding service to convert city names to coordinates.
Uses Nominatim API (OpenStreetMap) - free, no API key required.
"""

import requests
import time
from typing import Dict, Optional, Tuple
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

# Nominatim API endpoint
NOMINATIM_API_URL = "https://nominatim.openstreetmap.org/search"

# Rate limiting: Nominatim requires max 1 request per second
_last_request_time = 0
_request_interval = 1.1  # 1.1 seconds to be safe


def _rate_limit():
    """Ensure we don't exceed Nominatim's rate limit of 1 request/second."""
    global _last_request_time
    current_time = time.time()
    time_since_last = current_time - _last_request_time
    
    if time_since_last < _request_interval:
        sleep_time = _request_interval - time_since_last
        time.sleep(sleep_time)
    
    _last_request_time = time.time()


def get_city_coordinates(
    city: str, 
    country: Optional[str] = None,
    state: Optional[str] = None
) -> Dict[str, float]:
    """
    Get latitude and longitude coordinates for a city.
    
    Args:
        city: City name (e.g., "Jaipur")
        country: Optional country name (e.g., "India")
        state: Optional state/province name (e.g., "Rajasthan")
    
    Returns:
        Dictionary with 'lat' and 'lon' keys
        
    Raises:
        ValueError: If city not found
        requests.RequestException: If API request fails
    """
    # Normalize city name (handle common variations)
    city_normalized = city.strip()
    
    # Special handling for Indian cities with common variations
    indian_city_fixes = {
        "chennai": "Chennai, Tamil Nadu, India",
        "mumbai": "Mumbai, Maharashtra, India",
        "delhi": "Delhi, India",
        "bangalore": "Bangalore, Karnataka, India",
        "hyderabad": "Hyderabad, Telangana, India",
        "kolkata": "Kolkata, West Bengal, India",
        "pune": "Pune, Maharashtra, India",
        "jaipur": "Jaipur, Rajasthan, India"
    }
    
    # Build query string with fallback strategies
    query_parts = [city_normalized]
    if state:
        query_parts.append(state)
    if country:
        query_parts.append(country)
    
    query = ", ".join(query_parts)
    
    # Rate limit
    _rate_limit()
    
    # Make request to Nominatim API
    params = {
        "q": query,
        "format": "json",
        "limit": 5,  # Get more results for better matching
        "addressdetails": 1
    }
    
    headers = {
        "User-Agent": "Voice-First-Travel-Assistant/1.0"  # Required by Nominatim
    }
    
    try:
        logger.info(f"Geocoding request: {query}")
        response = requests.get(NOMINATIM_API_URL, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            # Try fallback with normalized city name
            city_lower = city_normalized.lower()
            if city_lower in indian_city_fixes:
                logger.info(f"Trying fallback query for {city_normalized}: {indian_city_fixes[city_lower]}")
                _rate_limit()  # Rate limit before retry
                params["q"] = indian_city_fixes[city_lower]
                response = requests.get(NOMINATIM_API_URL, params=params, headers=headers, timeout=15)
                response.raise_for_status()
                data = response.json()
            
            if not data:
                raise ValueError(f"City '{city}' not found. Try specifying country or state.")
        
        # Find best match (prefer exact city match)
        best_result = None
        for result in data:
            address = result.get("address", {})
            result_city = address.get("city") or address.get("town") or address.get("village")
            if result_city and city_normalized.lower() in result_city.lower():
                best_result = result
                break
        
        # If no exact match, use first result
        if not best_result:
            best_result = data[0]
        
        lat = float(best_result["lat"])
        lon = float(best_result["lon"])
        
        logger.info(f"Found coordinates for {query}: ({lat}, {lon})")
        
        return {
            "lat": lat,
            "lon": lon,
            "display_name": best_result.get("display_name", query),
            "place_id": best_result.get("place_id")
        }
    
    except requests.RequestException as e:
        logger.error(f"Geocoding API request failed for '{city}': {e}")
        # Try fallback for Indian cities
        city_lower = city_normalized.lower()
        if city_lower in indian_city_fixes and not country:
            try:
                logger.info(f"Retrying geocoding with fallback: {indian_city_fixes[city_lower]}")
                _rate_limit()
                params["q"] = indian_city_fixes[city_lower]
                response = requests.get(NOMINATIM_API_URL, params=params, headers=headers, timeout=15)
                response.raise_for_status()
                data = response.json()
                if data:
                    result = data[0]
                    return {
                        "lat": float(result["lat"]),
                        "lon": float(result["lon"]),
                        "display_name": result.get("display_name", query),
                        "place_id": result.get("place_id")
                    }
            except Exception as fallback_error:
                logger.error(f"Fallback geocoding also failed: {fallback_error}")
        
        raise requests.RequestException(f"Failed to geocode city '{city}': {e}")
    except (KeyError, ValueError, IndexError) as e:
        logger.error(f"Failed to parse geocoding response: {e}")
        raise ValueError(f"Could not extract coordinates for '{city}': Invalid response format")


@lru_cache(maxsize=100)
def get_city_coordinates_cached(
    city: str, 
    country: Optional[str] = None,
    state: Optional[str] = None
) -> Tuple[float, float]:
    """
    Cached version of get_city_coordinates.
    Returns only (lat, lon) tuple for use in other functions.
    
    Note: LRU cache requires hashable arguments, so None values are converted to empty strings.
    """
    country_str = country or ""
    state_str = state or ""
    
    result = get_city_coordinates(city, country_str if country_str else None, state_str if state_str else None)
    return (result["lat"], result["lon"])


def search_city(query: str, limit: int = 5) -> list:
    """
    Search for cities matching the query.
    Useful for autocomplete or city suggestions.
    
    Args:
        query: Search query (city name or partial name)
        limit: Maximum number of results to return
    
    Returns:
        List of city suggestions with details
    """
    _rate_limit()
    
    params = {
        "q": query,
        "format": "json",
        "limit": limit,
        "addressdetails": 1,
        "featuretype": "city"
    }
    
    headers = {
        "User-Agent": "Voice-First-Travel-Assistant/1.0"
    }
    
    try:
        logger.info(f"City search request: {query}")
        response = requests.get(NOMINATIM_API_URL, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        
        results = response.json()
        
        formatted_results = []
        for result in results:
            formatted_results.append({
                "city": result.get("address", {}).get("city") or result.get("name"),
                "state": result.get("address", {}).get("state"),
                "country": result.get("address", {}).get("country"),
                "lat": float(result["lat"]),
                "lon": float(result["lon"]),
                "display_name": result.get("display_name")
            })
        
        return formatted_results
    
    except requests.RequestException as e:
        logger.error(f"City search API request failed: {e}")
        return []
