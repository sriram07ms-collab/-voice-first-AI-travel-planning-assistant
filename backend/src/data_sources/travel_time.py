"""
Travel time calculation service.
Uses Google Maps Directions API (if configured) for accurate travel time estimation.
Falls back to OSRM (Open Source Routing Machine) API, then to distance-based estimation.
"""

import requests
import math
from typing import Dict, Tuple, Optional, List
import logging
import time
from functools import lru_cache
from collections import OrderedDict

# Import settings lazily to avoid circular dependencies
_settings = None

def _get_settings():
    """Lazy import of settings to avoid circular dependencies."""
    global _settings
    if _settings is None:
        try:
            from src.utils.config import get_settings
            _settings = get_settings()
        except ImportError:
            # Fallback if import fails (e.g., during testing)
            _settings = type('Settings', (), {'google_maps_api_key': None})()
    return _settings

logger = logging.getLogger(__name__)

# API endpoints
GOOGLE_MAPS_API_URL = "https://maps.googleapis.com/maps/api/directions/json"
GOOGLE_DISTANCE_MATRIX_API_URL = "https://maps.googleapis.com/maps/api/distancematrix/json"
OSRM_API_URL = "http://router.project-osrm.org/route/v1"

# Rate limiting for Google Maps API (10 requests/second max)
_google_maps_last_request_time = 0
_google_maps_request_interval = 0.1  # 100ms between requests

# Cache for travel time results (TTL: 1 hour)
_travel_time_cache: Dict[str, Tuple[Dict, float]] = OrderedDict()
_cache_max_size = 1000
_cache_ttl = 3600  # 1 hour in seconds

def _rate_limit_google_maps():
    """Rate limit Google Maps API calls to avoid exceeding limits."""
    global _google_maps_last_request_time
    current_time = time.time()
    time_since_last = current_time - _google_maps_last_request_time
    
    if time_since_last < _google_maps_request_interval:
        sleep_time = _google_maps_request_interval - time_since_last
        time.sleep(sleep_time)
    
    _google_maps_last_request_time = time.time()

def _get_cache_key(origin: Dict[str, float], destination: Dict[str, float], mode: str) -> str:
    """Generate cache key for travel time request."""
    return f"{origin['lat']:.4f},{origin['lon']:.4f}|{destination['lat']:.4f},{destination['lon']:.4f}|{mode}"

def _get_cached_result(cache_key: str) -> Optional[Dict]:
    """Get cached travel time result if available and not expired."""
    if cache_key not in _travel_time_cache:
        return None
    
    result, timestamp = _travel_time_cache[cache_key]
    current_time = time.time()
    
    # Check if cache entry is expired
    if current_time - timestamp > _cache_ttl:
        del _travel_time_cache[cache_key]
        return None
    
    # Move to end (LRU)
    _travel_time_cache.move_to_end(cache_key)
    logger.debug(f"Cache hit for travel time: {cache_key}")
    return result

def _set_cached_result(cache_key: str, result: Dict):
    """Cache travel time result."""
    # Remove oldest entries if cache is full
    while len(_travel_time_cache) >= _cache_max_size:
        _travel_time_cache.popitem(last=False)
    
    _travel_time_cache[cache_key] = (result, time.time())
    logger.debug(f"Cached travel time result: {cache_key}")


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great-circle distance between two points using Haversine formula.
    Returns distance in kilometers.
    
    Args:
        lat1, lon1: Coordinates of first point
        lat2, lon2: Coordinates of second point
    
    Returns:
        Distance in kilometers
    """
    # Radius of Earth in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    distance = R * c
    return distance


def estimate_travel_time_distance(
    lat1: float, 
    lon1: float, 
    lat2: float, 
    lon2: float, 
    mode: str = "walking"
) -> int:
    """
    Estimate travel time based on straight-line distance.
    
    Args:
        lat1, lon1: Origin coordinates
        lat2, lon2: Destination coordinates
        mode: Travel mode ('walking', 'driving', 'public_transit')
    
    Returns:
        Estimated travel time in minutes
    """
    distance_km = calculate_distance(lat1, lon1, lat2, lon2)
    
    # Average speeds in km/h
    speeds = {
        "walking": 5.0,  # 5 km/h average walking speed
        "driving": 30.0,  # 30 km/h average city driving
        "public_transit": 25.0,  # 25 km/h average public transport
        "cycling": 15.0  # 15 km/h average cycling
    }
    
    speed = speeds.get(mode.lower(), 5.0)
    
    # Time = Distance / Speed (in hours), convert to minutes
    time_hours = distance_km / speed
    time_minutes = int(time_hours * 60)
    
    # Add buffer time for urban areas (traffic, stops, etc.)
    if mode == "walking":
        buffer = max(5, int(time_minutes * 0.2))  # 20% buffer, min 5 min
    elif mode == "driving":
        buffer = max(10, int(time_minutes * 0.3))  # 30% buffer, min 10 min
    else:
        buffer = max(10, int(time_minutes * 0.25))  # 25% buffer, min 10 min
    
    return time_minutes + buffer


def calculate_travel_time_google_maps(
    origin: Dict[str, float],
    destination: Dict[str, float],
    mode: str = "driving"
) -> Optional[Dict[str, any]]:
    """
    Calculate travel time using Google Maps Directions API.
    Uses caching and rate limiting for optimization.
    
    Args:
        origin: Dict with 'lat' and 'lon' keys
        destination: Dict with 'lat' and 'lon' keys
        mode: Travel mode ('driving', 'walking', 'bicycling', 'transit')
    
    Returns:
        Dictionary with travel time, distance, and route info, or None if API fails
    """
    settings = _get_settings()
    
    # Check if API key is configured
    if not settings.google_maps_api_key:
        logger.warning("⚠️ Google Maps API key not configured! Set GOOGLE_MAPS_API_KEY environment variable. Skipping Google Maps Directions API.")
        return None
    
    logger.debug(f"✅ Google Maps API key configured, using Google Maps Directions API (mode: {mode})")
    
    # Check cache first
    cache_key = _get_cache_key(origin, destination, mode)
    cached_result = _get_cached_result(cache_key)
    if cached_result is not None:
        return cached_result
    
    lat1 = origin["lat"]
    lon1 = origin["lon"]
    lat2 = destination["lat"]
    lon2 = destination["lon"]
    
    # Map mode to Google Maps mode
    mode_mapping = {
        "driving": "driving",
        "walking": "walking",
        "bicycling": "bicycling",
        "cycling": "bicycling",
        "public_transit": "transit",
        "transit": "transit"
    }
    
    google_mode = mode_mapping.get(mode.lower(), "driving")
    
    # Build Google Maps request URL
    origin_str = f"{lat1},{lon1}"
    destination_str = f"{lat2},{lon2}"
    
    params = {
        "origin": origin_str,
        "destination": destination_str,
        "mode": google_mode,
        "key": settings.google_maps_api_key,
        "alternatives": "false",
        "units": "metric"
    }
    
    try:
        # Apply rate limiting
        _rate_limit_google_maps()
        
        logger.debug(f"Google Maps API request: origin={origin_str}, destination={destination_str}, mode={google_mode}")
        response = requests.get(GOOGLE_MAPS_API_URL, params=params, timeout=10)
        
        if response.status_code != 200:
            logger.warning(f"Google Maps API returned status {response.status_code}")
            return None
        
        data = response.json()
        
        # Check for API errors
        status = data.get("status")
        
        if status == "OK":
            # Extract route information
            routes = data.get("routes", [])
            if not routes:
                logger.warning("Google Maps API returned OK status but no routes")
                return None
            
            route = routes[0]
            legs = route.get("legs", [])
            
            if not legs:
                logger.warning("Google Maps API returned route but no legs")
                return None
            
            leg = legs[0]
            duration_seconds = int(leg.get("duration", {}).get("value", 0))
            distance_meters = int(leg.get("distance", {}).get("value", 0))
            
            if duration_seconds == 0 or distance_meters == 0:
                logger.warning("Google Maps API returned invalid duration or distance")
                return None
            
            duration_minutes = duration_seconds // 60
            
            result = {
                "duration_minutes": duration_minutes,
                "duration_seconds": duration_seconds,
                "distance_km": round(distance_meters / 1000, 2),
                "distance_meters": distance_meters,
                "mode": mode,
                "source": "google_maps"
            }
            
            # Cache the result
            _set_cached_result(cache_key, result)
            return result
        
        elif status == "OVER_QUERY_LIMIT":
            logger.warning("Google Maps API rate limit exceeded (OVER_QUERY_LIMIT)")
            return None
        
        elif status == "REQUEST_DENIED":
            logger.warning("Google Maps API request denied (invalid API key or permissions)")
            return None
        
        elif status == "INVALID_REQUEST":
            logger.warning("Google Maps API invalid request (check parameters)")
            return None
        
        elif status == "ZERO_RESULTS":
            logger.debug("Google Maps API found no route (ZERO_RESULTS)")
            return None
        
        elif status == "UNKNOWN_ERROR":
            logger.warning("Google Maps API unknown error (temporary issue)")
            return None
        
        else:
            logger.warning(f"Google Maps API returned error status: {status}")
            return None
    
    except requests.RequestException as e:
        logger.warning(f"Google Maps API request failed: {e}")
        return None
    except (KeyError, ValueError, IndexError, TypeError) as e:
        logger.warning(f"Failed to parse Google Maps API response: {e}")
        return None


def calculate_travel_time_osrm(
    lat1: float, 
    lon1: float, 
    lat2: float, 
    lon2: float, 
    mode: str = "driving"
) -> Optional[Dict[str, any]]:
    """
    Calculate travel time using OSRM API (more accurate).
    
    Args:
        lat1, lon1: Origin coordinates
        lat2, lon2: Destination coordinates
        mode: Travel mode ('driving', 'walking', 'cycling')
    
    Returns:
        Dictionary with travel time, distance, and route info, or None if API fails
    """
    # Map mode to OSRM profile
    profiles = {
        "driving": "driving",
        "walking": "walking",
        "cycling": "cycling",
        "public_transit": "driving"  # Fallback to driving for transit
    }
    
    profile = profiles.get(mode.lower(), "driving")
    
    # Build OSRM request URL
    coordinates = f"{lon1},{lat1};{lon2},{lat2}"
    url = f"{OSRM_API_URL}/{profile}/{coordinates}"
    
    params = {
        "overview": "false",  # Don't need full route geometry
        "steps": "false",  # Don't need step-by-step directions
        "geometries": "geojson"
    }
    
    try:
        logger.debug(f"OSRM request: {url}")
        response = requests.get(url, params=params, timeout=5)
        
        if response.status_code != 200:
            logger.warning(f"OSRM API returned status {response.status_code}")
            return None
        
        data = response.json()
        
        if data.get("code") != "Ok" or not data.get("routes"):
            logger.warning(f"OSRM API returned error: {data.get('code')}")
            return None
        
        route = data["routes"][0]
        duration_seconds = int(route["duration"])
        distance_meters = int(route["distance"])
        duration_minutes = duration_seconds // 60
        
        return {
            "duration_minutes": duration_minutes,
            "duration_seconds": duration_seconds,
            "distance_km": round(distance_meters / 1000, 2),
            "distance_meters": distance_meters,
            "mode": mode,
            "source": "osrm"
        }
    
    except requests.RequestException as e:
        logger.warning(f"OSRM API request failed: {e}")
        return None
    except (KeyError, ValueError, IndexError) as e:
        logger.warning(f"Failed to parse OSRM response: {e}")
        return None


def calculate_travel_time(
    origin: Dict[str, float], 
    destination: Dict[str, float], 
    mode: str = "driving"  # Changed default from "walking" to "driving"
) -> Dict[str, any]:
    """
    Calculate travel time between two locations.
    Tries Google Maps API first (if configured), falls back to OSRM API,
    then to distance-based estimation.
    
    Priority: Google Maps → OSRM → Distance Estimation
    
    Args:
        origin: Dict with 'lat' and 'lon' keys
        destination: Dict with 'lat' and 'lon' keys
        mode: Travel mode ('walking', 'driving', 'public_transit', 'cycling')
              Defaults to 'driving' for all scenarios unless explicitly 'walking'
    
    Returns:
        Dictionary with travel time and distance information
    """
    lat1 = origin["lat"]
    lon1 = origin["lon"]
    lat2 = destination["lat"]
    lon2 = destination["lon"]
    
    # Try Google Maps API first (if configured)
    google_maps_result = calculate_travel_time_google_maps(origin, destination, mode)
    
    if google_maps_result:
        logger.info(f"✅ Using Google Maps API for travel time calculation ({mode}): {google_maps_result.get('duration_minutes')} min, {google_maps_result.get('distance_km')} km")
        return google_maps_result
    
    # Fallback to OSRM (more accurate than distance estimation)
    osrm_result = calculate_travel_time_osrm(lat1, lon1, lat2, lon2, mode)
    
    if osrm_result:
        logger.warning(f"⚠️ Google Maps API unavailable, using OSRM API for travel time calculation ({mode}): {osrm_result.get('duration_minutes')} min")
        return osrm_result
    
    # Fallback to distance-based estimation
    logger.warning(f"⚠️ Both Google Maps and OSRM unavailable, using distance-based estimation for travel time ({mode})")
    duration_minutes = estimate_travel_time_distance(lat1, lon1, lat2, lon2, mode)
    distance_km = calculate_distance(lat1, lon1, lat2, lon2)
    
    return {
        "duration_minutes": duration_minutes,
        "distance_km": round(distance_km, 2),
        "mode": mode,
        "source": "distance_estimation"
    }


def calculate_travel_time_batch_google_maps(
    origins: List[Dict[str, float]],
    destinations: List[Dict[str, float]],
    mode: str = "driving"
) -> Optional[Dict[Tuple[int, int], Dict[str, any]]]:
    """
    Calculate travel times in batch using Google Distance Matrix API.
    Supports up to 25 origins/destinations per request.
    
    Args:
        origins: List of origin dicts with 'lat' and 'lon' keys
        destinations: List of destination dicts with 'lat' and 'lon' keys
        mode: Travel mode ('driving', 'walking', 'bicycling', 'transit')
    
    Returns:
        Dictionary mapping (origin_index, destination_index) to travel time info, or None if API fails
    """
    settings = _get_settings()
    
    if not settings.google_maps_api_key:
        logger.debug("Google Maps API key not configured, skipping batch calculation")
        return None
    
    # Google Distance Matrix API limit: 25 origins/destinations per request
    max_batch_size = 25
    
    if len(origins) > max_batch_size or len(destinations) > max_batch_size:
        logger.warning(f"Batch size exceeds Google API limit ({max_batch_size}), falling back to individual calls")
        return None
    
    # Map mode to Google Maps mode
    mode_mapping = {
        "driving": "driving",
        "walking": "walking",
        "bicycling": "bicycling",
        "cycling": "bicycling",
        "public_transit": "transit",
        "transit": "transit"
    }
    
    google_mode = mode_mapping.get(mode.lower(), "driving")
    
    # Build origin and destination strings
    origins_str = "|".join([f"{o['lat']},{o['lon']}" for o in origins])
    destinations_str = "|".join([f"{d['lat']},{d['lon']}" for d in destinations])
    
    params = {
        "origins": origins_str,
        "destinations": destinations_str,
        "mode": google_mode,
        "key": settings.google_maps_api_key,
        "units": "metric"
    }
    
    try:
        # Apply rate limiting
        _rate_limit_google_maps()
        
        logger.debug(f"Google Distance Matrix API batch request: {len(origins)} origins, {len(destinations)} destinations, mode={google_mode}")
        response = requests.get(GOOGLE_DISTANCE_MATRIX_API_URL, params=params, timeout=15)
        
        if response.status_code != 200:
            logger.warning(f"Google Distance Matrix API returned status {response.status_code}")
            return None
        
        data = response.json()
        status = data.get("status")
        
        if status != "OK":
            if status == "OVER_QUERY_LIMIT":
                logger.warning("Google Distance Matrix API rate limit exceeded")
            else:
                logger.warning(f"Google Distance Matrix API returned error status: {status}")
            return None
        
        rows = data.get("rows", [])
        results = {}
        
        for i, row in enumerate(rows):
            elements = row.get("elements", [])
            for j, element in enumerate(elements):
                element_status = element.get("status")
                
                if element_status == "OK":
                    duration_seconds = int(element.get("duration", {}).get("value", 0))
                    distance_meters = int(element.get("distance", {}).get("value", 0))
                    duration_minutes = duration_seconds // 60
                    
                    results[(i, j)] = {
                        "duration_minutes": duration_minutes,
                        "duration_seconds": duration_seconds,
                        "distance_km": round(distance_meters / 1000, 2),
                        "distance_meters": distance_meters,
                        "mode": mode,
                        "source": "google_maps_distance_matrix"
                    }
                else:
                    logger.debug(f"Distance Matrix element ({i}, {j}) status: {element_status}")
                    # Return None for failed elements, will fall back to individual calls
                    results[(i, j)] = None
        
        logger.info(f"Successfully calculated {len([r for r in results.values() if r])} travel times via Distance Matrix API")
        return results
    
    except requests.RequestException as e:
        logger.warning(f"Google Distance Matrix API request failed: {e}")
        return None
    except (KeyError, ValueError, IndexError, TypeError) as e:
        logger.warning(f"Failed to parse Google Distance Matrix API response: {e}")
        return None


def estimate_travel_time_batch(pois: List[Dict], mode: str = "driving") -> Dict[Tuple[int, int], Dict[str, any]]:
    """
    Estimate travel times between multiple POIs in batch.
    Uses Google Distance Matrix API when possible, falls back to individual calls.
    Returns a dictionary mapping (origin_index, destination_index) to travel time info.
    
    Args:
        pois: List of POI dictionaries with 'location' key containing 'lat' and 'lon'
        mode: Travel mode ('driving', 'walking', 'cycling', etc.)
    
    Returns:
        Dictionary with (i, j) tuples as keys and travel time info as values
    """
    results = {}
    
    # Try Google Distance Matrix API first if we have <= 25 POIs
    if len(pois) <= 25:
        origins = [poi["location"] for poi in pois]
        destinations = origins  # All-to-all matrix
        
        batch_results = calculate_travel_time_batch_google_maps(origins, destinations, mode)
        
        if batch_results:
            # Use batch results
            for i in range(len(pois)):
                for j in range(len(pois)):
                    if i != j:
                        result = batch_results.get((i, j))
                        if result:
                            results[(i, j)] = result
                            results[(j, i)] = result  # Symmetric
            
            # Fill any missing pairs with individual calls
            for i in range(len(pois)):
                for j in range(i + 1, len(pois)):
                    if (i, j) not in results:
                        origin = pois[i]["location"]
                        destination = pois[j]["location"]
                        travel_info = calculate_travel_time(origin, destination, mode=mode)
                        results[(i, j)] = travel_info
                        results[(j, i)] = travel_info  # Symmetric
            
            return results
    
    # Fallback to individual calls for large batches
    logger.info(f"Using individual calls for batch calculation ({len(pois)} POIs)")
    for i in range(len(pois)):
        for j in range(i + 1, len(pois)):
            origin = pois[i]["location"]
            destination = pois[j]["location"]
            travel_info = calculate_travel_time(origin, destination, mode=mode)
            results[(i, j)] = travel_info
            results[(j, i)] = travel_info  # Symmetric
    
    return results
