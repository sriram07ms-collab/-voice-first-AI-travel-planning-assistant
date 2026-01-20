"""
OpenStreetMap integration for Points of Interest (POI) data.
Uses Overpass API to query POIs by city, category, and interests.
"""

import requests
import time
from typing import List, Dict, Optional, Any
import logging

# Use try/except for imports to handle both relative and absolute
try:
    from .geocoding import get_city_coordinates
    from ..models.itinerary_models import POI, Location
except ImportError:
    from src.data_sources.geocoding import get_city_coordinates
    from src.models.itinerary_models import POI, Location

logger = logging.getLogger(__name__)

# Overpass API endpoints (with failover)
OVERPASS_API_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
]
OVERPASS_API_URL = OVERPASS_API_ENDPOINTS[0]  # Primary endpoint

# Rate limiting: Overpass API recommends max 1 request/second
_last_request_time = 0
_request_interval = 1.2  # 1.2 seconds to be safer


def _rate_limit():
    """Ensure we don't exceed Overpass API rate limit."""
    global _last_request_time
    current_time = time.time()
    time_since_last = current_time - _last_request_time
    
    if time_since_last < _request_interval:
        sleep_time = _request_interval - time_since_last
        time.sleep(sleep_time)
    
    _last_request_time = time.time()


def _category_to_tags(interests: List[str]) -> Dict[str, List[str]]:
    """
    Map user interests to OpenStreetMap tags.
    
    Args:
        interests: List of user interests (e.g., ['food', 'culture', 'shopping'])
    
    Returns:
        Dictionary mapping tag types to tag values
    """
    interest_mapping = {
        "food": {
            "amenity": ["restaurant", "cafe", "fast_food", "food_court"],
            "tourism": ["attraction"]  # Some food places are attractions
        },
        "culture": {
            "tourism": ["museum", "gallery", "attraction", "artwork"],
            "historic": ["monument", "memorial", "castle", "palace", "temple"]
        },
        "shopping": {
            "shop": ["mall", "supermarket", "marketplace", "department_store", "clothes", "jewelry", "electronics", "bookstore"],
            "tourism": ["attraction"],  # Markets
            "amenity": ["marketplace"]  # Marketplaces
        },
        "nightlife": {
            "amenity": ["bar", "pub", "nightclub", "casino"]
        },
        "nature": {
            "leisure": ["park", "nature_reserve"],
            "natural": ["*"]
        },
        "beaches": {
            "natural": ["beach"],
            "leisure": ["beach_resort"]
        },
        "religion": {
            "amenity": ["place_of_worship"],
            "historic": ["temple", "church", "mosque"]
        }
    }
    
    tags = {}
    for interest in interests:
        interest_lower = interest.lower()
        if interest_lower in interest_mapping:
            for tag_type, tag_values in interest_mapping[interest_lower].items():
                if tag_type not in tags:
                    tags[tag_type] = []
                tags[tag_type].extend(tag_values)
    
    return tags


def _calculate_bbox(lat: float, lon: float, radius_meters: int) -> tuple:
    """
    Calculate bounding box from center point and radius.
    
    Args:
        lat: Center latitude
        lon: Center longitude
        radius_meters: Radius in meters
    
    Returns:
        Tuple of (south, west, north, east) in degrees
    """
    # Approximate conversion: 1 degree latitude ≈ 111km
    # 1 degree longitude ≈ 111km * cos(latitude)
    lat_delta = radius_meters / 111000.0
    lon_delta = radius_meters / (111000.0 * abs(__import__('math').cos(__import__('math').radians(lat))))
    
    south = lat - lat_delta
    north = lat + lat_delta
    west = lon - lon_delta
    east = lon + lon_delta
    
    return (south, west, north, east)


def _build_overpass_query(lat: float, lon: float, tags: Dict[str, List[str]], radius: int = 5000, limit: int = 100) -> str:
    """
    Build Overpass QL query for POIs using around:radius (most efficient).
    Uses nwr[...] syntax (node+way+relation combined) for maximum efficiency.
    
    Args:
        lat: Latitude
        lon: Longitude
        tags: Dictionary of tag types to tag values
        radius: Search radius in meters (default: 5000 = 5km)
        limit: Maximum number of results to return (applied in query)
    
    Returns:
        Overpass QL query string
    """
    query_lines = []
    
    # Build efficient queries using nwr[...] syntax (combines node, way, relation)
    # Use around:radius which is more efficient than bounding boxes
    for tag_type, tag_values in tags.items():
        # Filter out "*" wildcards - they create too many results
        valid_values = [v for v in tag_values if v != "*"]
        if not valid_values and "*" in tag_values:
            # For wildcard, use simple tag query (but be careful - can return many results)
            query_lines.append(f'  nwr(around:{radius},{lat:.6f},{lon:.6f})["{tag_type}"];')
            continue
        
        if not valid_values:
            continue
        
        # Use regex pattern for multiple values (much more efficient than separate queries)
        if len(valid_values) > 1:
            # Build regex pattern: "^(value1|value2|value3)$"
            # Limit to 8 values max to prevent query from being too complex
            regex_pattern = "|".join(valid_values[:8])
            query_lines.append(f'  nwr(around:{radius},{lat:.6f},{lon:.6f})["{tag_type}"~"^({regex_pattern})$"];')
        else:
            # Single value - use exact match (most efficient)
            query_lines.append(f'  nwr(around:{radius},{lat:.6f},{lon:.6f})["{tag_type}"="{valid_values[0]}"];')
    
    if not query_lines:
        logger.warning("No query parts generated from tags")
        return None
    
    # Use reasonable timeout based on radius (larger radius = more time needed)
    # maxsize: 1GB (1073741824 bytes) - reasonable for POI queries
    timeout = min(60, 30 + (radius // 1000))  # 30s base + 1s per km, max 60s
    
    # Build query - limit results in the query itself
    query = f"""[out:json][timeout:{timeout}][maxsize:1073741824];
(
{chr(10).join(query_lines)}
);
out center {limit};"""
    
    logger.debug(f"Built Overpass query with around:({lat:.6f},{lon:.6f},{radius}m), timeout={timeout}s, limit={limit}")
    logger.debug(f"Query has {len(query_lines)} tag filters")
    return query


def _parse_overpass_response(data: Dict) -> List[Dict]:
    """
    Parse Overpass API response into POI dictionaries.
    
    Args:
        data: Overpass API JSON response
    
    Returns:
        List of POI dictionaries
    """
    pois = []
    elements = data.get("elements", [])
    
    logger.debug(f"Parsing {len(elements)} elements from Overpass response")
    
    # Track statistics for diagnostics
    skipped_no_name = 0
    skipped_no_coords = 0
    
    for element in elements:
        element_type = element.get("type")
        if element_type not in ["node", "way", "relation"]:
            continue
        
        tags = element.get("tags", {})
        # Try multiple name fields (including local language names)
        name = (tags.get("name") or tags.get("name:en") or tags.get("alt_name") or 
                tags.get("name:hi") or tags.get("name:ta") or tags.get("name:kn") or 
                tags.get("name:te") or tags.get("name:ml") or tags.get("official_name") or
                tags.get("loc_name") or tags.get("short_name"))
        
        if not name:
            skipped_no_name += 1
            continue  # Skip POIs without names
        
        # Get coordinates
        if element_type == "node":
            lat = element.get("lat")
            lon = element.get("lon")
        else:
            # For ways and relations, get center point
            center = element.get("center", {})
            lat = center.get("lat")
            lon = center.get("lon")
            # Fallback: try lat/lon directly if center not available
            if not lat or not lon:
                lat = element.get("lat")
                lon = element.get("lon")
        
        if not lat or not lon:
            skipped_no_coords += 1
            logger.debug(f"Skipping {element_type} {element.get('id')}: no coordinates")
            continue
        
        # Determine category
        category = "attraction"  # default
        if tags.get("tourism") == "museum":
            category = "museum"
        elif tags.get("tourism") == "attraction":
            category = "attraction"
        elif tags.get("amenity") in ["restaurant", "cafe", "fast_food"]:
            category = "restaurant"
        elif tags.get("shop"):
            category = "shopping"
        elif tags.get("historic"):
            category = "historical"
        elif tags.get("leisure") == "park":
            category = "park"
        
        # Get source ID
        source_id = f"{element_type}:{element['id']}"
        
        # Estimate duration (rough estimates)
        duration_map = {
            "museum": 120,
            "attraction": 90,
            "restaurant": 60,
            "shopping": 60,
            "historical": 90,
            "park": 60
        }
        duration_minutes = duration_map.get(category, 60)
        
        poi = {
            "name": name,
            "category": category,
            "location": {
                "lat": lat,
                "lon": lon
            },
            "duration_minutes": duration_minutes,
            "data_source": "openstreetmap",
            "source_id": source_id,
            "rating": None,  # OSM doesn't have ratings
            "description": tags.get("description") or tags.get("tourism") or category,
            "opening_hours": tags.get("opening_hours"),
            "tags": tags  # Store all tags for reference
        }
        
        pois.append(poi)
    
    # Log diagnostic stats if many elements were filtered out
    if len(elements) > 0 and len(pois) == 0:
        logger.warning(f"Parsed 0 POIs from {len(elements)} elements: {skipped_no_name} without names, {skipped_no_coords} without coordinates")
    elif skipped_no_name > len(elements) * 0.5:  # More than 50% filtered for no name
        logger.info(f"Parsed {len(pois)} POIs from {len(elements)} elements: {skipped_no_name} skipped (no name), {skipped_no_coords} skipped (no coords)")
    
    return pois


def _try_fallback_query(lat: float, lon: float, radius: int, interests: List[str]) -> List[Dict]:
    """
    Try a broader fallback query if the specific query returns no results.
    This searches for general tourism and amenity POIs.
    Tries alternative Overpass API endpoints if the primary fails.
    
    Args:
        lat: Latitude
        lon: Longitude
        radius: Search radius in meters
        interests: Original interests list
    
    Returns:
        List of POI dictionaries
    """
    logger.info(f"Attempting fallback query with broader tourism tags at ({lat}, {lon}) with radius {radius}m")
    
    import math
    # Calculate bounding box for fallback queries too
    lat_delta = radius / 111000.0
    lon_delta = radius / (111000.0 * abs(math.cos(math.radians(lat))))
    south = lat - lat_delta
    north = lat + lat_delta
    west = lon - lon_delta
    east = lon + lon_delta
    
    # Build a broader query with common tourism tags - try multiple approaches
    fallback_queries = [
        # Query 1: Very broad tourism/amenity/historic using bbox
        f"""
[out:json][timeout:25];
(
  node["tourism"]({south},{west},{north},{east});
  way["tourism"]({south},{west},{north},{east});
  relation["tourism"]({south},{west},{north},{east});
  node["amenity"]({south},{west},{north},{east});
  way["amenity"]({south},{west},{north},{east});
  relation["amenity"]({south},{west},{north},{east});
  node["historic"]({south},{west},{north},{east});
  way["historic"]({south},{west},{north},{east});
  relation["historic"]({south},{west},{north},{east});
);
out center;
""",
        # Query 2: Even broader - any named POI with tourism or amenity
        f"""
[out:json][timeout:25];
(
  node["name"]({south},{west},{north},{east})["tourism"];
  way["name"]({south},{west},{north},{east})["tourism"];
  relation["name"]({south},{west},{north},{east})["tourism"];
  node["name"]({south},{west},{north},{east})["amenity"];
  way["name"]({south},{west},{north},{east})["amenity"];
  relation["name"]({south},{west},{north},{east})["amenity"];
);
out center;
"""
    ]
    
    # Try each fallback query with all endpoints
    for i, fallback_query in enumerate(fallback_queries, 1):
        # Try each Overpass endpoint
        for endpoint_idx, api_url in enumerate(OVERPASS_API_ENDPOINTS):
            try:
                if endpoint_idx > 0:
                    logger.info(f"Trying fallback query {i} with alternative endpoint {endpoint_idx + 1}/{len(OVERPASS_API_ENDPOINTS)}: {api_url}")
                else:
                    logger.info(f"Trying fallback query {i}...")
                
                _rate_limit()
                response = requests.post(
                    api_url,
                    data=fallback_query,
                    headers={"Content-Type": "text/plain"},
                    timeout=30
                )
                response.raise_for_status()
                
                data = response.json()
                if "remark" in data:
                    logger.warning(f"Overpass API remark (fallback {i}, endpoint {endpoint_idx + 1}): {data['remark']}")
                
                if "elements" not in data:
                    logger.warning(f"Fallback query {i} response missing 'elements' key. Keys: {list(data.keys())}")
                    continue
                
                elements_count = len(data.get('elements', []))
                logger.info(f"Fallback query {i} returned {elements_count} elements (endpoint {endpoint_idx + 1})")
                
                # Log diagnostic info if no elements
                if elements_count == 0:
                    logger.debug(f"Fallback query {i} returned 0 elements. Query was: {fallback_query[:200]}...")
                    continue
                
                pois_dict = _parse_overpass_response(data)
                logger.info(f"Fallback query {i} parsed {len(pois_dict)} POIs (from {elements_count} elements)")
                
                # Log diagnostic if elements were filtered out (no names)
                if elements_count > 0 and len(pois_dict) == 0:
                    sample_element = data["elements"][0] if data["elements"] else None
                    if sample_element:
                        tags = sample_element.get("tags", {})
                        logger.warning(f"Fallback query {i}: {elements_count} elements returned but 0 POIs parsed. Sample element tags: {list(tags.keys())[:5]}. Has name: {'name' in tags}")
                
                if pois_dict:
                    logger.info(f"Fallback query {i} succeeded with {len(pois_dict)} POIs")
                    return pois_dict
            
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 504:
                    logger.warning(f"Fallback query {i} 504 timeout on endpoint {endpoint_idx + 1}. Trying next endpoint...")
                    continue
                else:
                    logger.error(f"Fallback query {i} HTTP error on endpoint {endpoint_idx + 1}: {e}")
                    continue
            except Exception as e:
                logger.error(f"Fallback query {i} failed on endpoint {endpoint_idx + 1}: {e}")
                continue
    
    logger.warning("All fallback queries returned no results after trying all endpoints")
    return []


def _try_very_broad_query(lat: float, lon: float, radius: int) -> List[Dict]:
    """
    Very broad fallback query - searches for ANY named POI with common tags.
    This is the last resort when all other queries fail.
    
    Args:
        lat: Latitude
        lon: Longitude
        radius: Search radius in meters
    
    Returns:
        List of POI dictionaries
    """
    logger.info(f"Attempting very broad query at ({lat}, {lon}) with radius {radius}m")
    
    import math
    # Use smaller radius for very broad query to avoid timeout
    safe_radius = min(radius, 3000)  # Max 3km for very broad query
    lat_delta = safe_radius / 111000.0
    lon_delta = safe_radius / (111000.0 * abs(math.cos(math.radians(lat))))
    south = lat - lat_delta
    north = lat + lat_delta
    west = lon - lon_delta
    east = lon + lon_delta
    
    # Very broad query - any named POI with common tags
    very_broad_query = f"""
[out:json][timeout:20];
(
  node["name"]({south},{west},{north},{east})["tourism"];
  way["name"]({south},{west},{north},{east})["tourism"];
  relation["name"]({south},{west},{north},{east})["tourism"];
  node["name"]({south},{west},{north},{east})["amenity"];
  way["name"]({south},{west},{north},{east})["amenity"];
  relation["name"]({south},{west},{north},{east})["amenity"];
  node["name"]({south},{west},{north},{east})["shop"];
  way["name"]({south},{west},{north},{east})["shop"];
  relation["name"]({south},{west},{north},{east})["shop"];
  node["name"]({south},{west},{north},{east})["historic"];
  way["name"]({south},{west},{north},{east})["historic"];
  relation["name"]({south},{west},{north},{east})["historic"];
);
out center 50;
"""
    
    # Try with primary endpoint
    try:
        _rate_limit()
        response = requests.post(
            OVERPASS_API_ENDPOINTS[0],
            data=very_broad_query,
            headers={"Content-Type": "text/plain"},
            timeout=25
        )
        response.raise_for_status()
        
        data = response.json()
        if "elements" in data and len(data["elements"]) > 0:
            pois_dict = _parse_overpass_response(data)
            logger.info(f"Very broad query returned {len(pois_dict)} POIs")
            return pois_dict
    except Exception as e:
        logger.error(f"Very broad query failed: {e}")
    
    return []


def search_pois_overpass(
    city: str,
    interests: List[str],
    constraints: Optional[Dict[str, Any]] = None,
    country: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 50
) -> List[POI]:
    """
    Search for Points of Interest in a city using OpenStreetMap/Overpass API.
    This is the fallback method when Google Places API is unavailable.
    
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
    try:
        # Get city coordinates
        logger.info(f"Searching POIs for {city}")
        coords = get_city_coordinates(city, country, state)
        lat = coords["lat"]
        lon = coords["lon"]
        
        # Map interests to OSM tags
        tags = _category_to_tags(interests)
        
        if not tags:
            logger.warning(f"No valid tags found for interests: {interests}")
            return []
        
        logger.info(f"Mapped interests {interests} to OSM tags: {tags}")
        
        # Use conservative radius to prevent timeouts - start with 5km
        # For Chennai and other major Indian cities, use slightly larger radius
        city_lower = city.lower()
        if city_lower in ["chennai", "mumbai", "delhi", "bangalore", "hyderabad", "kolkata"]:
            radius = 7000  # 7km for major cities - more coverage
            logger.info(f"Using larger radius (7km) for major city: {city}")
        else:
            radius = 5000  # 5km radius - optimal for preventing timeouts while getting good coverage
        logger.info(f"Using search radius of {radius/1000}km for POI search at ({lat}, {lon})")
        
        # Build Overpass query with result limit
        query = _build_overpass_query(lat, lon, tags, radius=radius, limit=limit)
        
        if not query:
            logger.error("Failed to build Overpass query")
            return []
        
        # Rate limit
        _rate_limit()
        
        # Make request to Overpass API with retry logic for timeouts
        logger.debug(f"Overpass query: {query[:500]}...")
        
        max_retries = 3
        retry_delay = 2  # seconds
        pois_dict = []  # Initialize to avoid undefined variable errors
        
        for attempt in range(max_retries):
            # Try alternative endpoints on retries (failover)
            endpoint_index = min(attempt, len(OVERPASS_API_ENDPOINTS) - 1)
            api_url = OVERPASS_API_ENDPOINTS[endpoint_index]
            
            try:
                # Increase timeout with each retry
                request_timeout = 30 + (attempt * 10)
                
                if endpoint_index > 0:
                    logger.info(f"Trying alternative Overpass endpoint {endpoint_index + 1}/{len(OVERPASS_API_ENDPOINTS)}: {api_url}")
                
                response = requests.post(
                    api_url,
                    data=query,
                    headers={"Content-Type": "text/plain"},
                    timeout=request_timeout
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Check for errors in response
                if "remark" in data:
                    logger.warning(f"Overpass API remark: {data['remark']}")
                
                if "elements" not in data:
                    logger.warning(f"Overpass response missing 'elements' key. Keys: {list(data.keys())}")
                    data["elements"] = []
                
                # Log raw response info for debugging
                elements_count = len(data.get("elements", []))
                logger.info(f"Overpass API returned {elements_count} elements (attempt {attempt + 1})")
                
                if elements_count > 0:
                    # Log sample element for debugging
                    sample = data["elements"][0]
                    logger.debug(f"Sample element: type={sample.get('type')}, tags={list(sample.get('tags', {}).keys())[:5]}")
                
                # Parse response
                pois_dict = _parse_overpass_response(data)
                logger.info(f"Parsed {len(pois_dict)} POIs from Overpass response (from {elements_count} elements)")
                
                # Log diagnostic if elements were filtered out (no names)
                if elements_count > 0 and len(pois_dict) == 0:
                    sample_element = data["elements"][0] if data["elements"] else None
                    if sample_element:
                        tags = sample_element.get("tags", {})
                        logger.warning(f"Overpass returned {elements_count} elements but 0 POIs parsed (filtered out). Sample element tags: {list(tags.keys())[:5]}. Has name: {'name' in tags}")
                
                # If no POIs found, try a broader fallback query
                if not pois_dict:
                    logger.warning(f"No POIs found with specific tags. Trying fallback query...")
                    try:
                        pois_dict = _try_fallback_query(lat, lon, radius, interests)
                        if not pois_dict:
                            # Last resort: try even broader query with just tourism/amenity
                            logger.warning(f"Fallback query also returned no results. Trying very broad query...")
                            pois_dict = _try_very_broad_query(lat, lon, radius)
                    except Exception as fallback_error:
                        logger.error(f"Fallback query failed: {fallback_error}")
                        pois_dict = []
                
                # Success - break retry loop
                break
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 504 and attempt < max_retries - 1:
                    # Gateway timeout - retry with reduced radius
                    logger.warning(f"Overpass API 504 timeout (attempt {attempt + 1}/{max_retries}). Retrying with reduced radius...")
                    
                    # Reduce radius by 30% for retry
                    if attempt == 0:
                        radius_reduced = int(radius * 0.7)
                        logger.info(f"Retrying with reduced radius: {radius}m -> {radius_reduced}m")
                        radius = radius_reduced  # Update radius for next iteration
                        # Rebuild query with reduced radius
                        query = _build_overpass_query(lat, lon, tags, radius=radius, limit=limit)
                        if not query:
                            raise
                        time.sleep(retry_delay)
                        continue
                    elif attempt == 1:
                        # Second retry - try even smaller radius (50% of original)
                        original_radius = radius if radius > 5000 else 5000
                        radius_reduced = int(original_radius * 0.5)
                        logger.info(f"Retrying with further reduced radius: {radius}m -> {radius_reduced}m")
                        radius = radius_reduced  # Update radius for next iteration
                        query = _build_overpass_query(lat, lon, tags, radius=radius, limit=limit)
                        if not query:
                            raise
                        time.sleep(retry_delay * 2)
                        continue
                
                # Other HTTP errors or final retry attempt
                if attempt == max_retries - 1:
                    logger.error(f"Overpass API request failed after {max_retries} attempts: {e}")
                    # Try fallback query as last resort
                    logger.info("Attempting fallback query as last resort...")
                    try:
                        pois_dict = _try_fallback_query(lat, lon, radius, interests)
                        break
                    except Exception as fallback_error:
                        logger.error(f"Fallback query also failed: {fallback_error}")
                        raise
                else:
                    time.sleep(retry_delay * (attempt + 1))
                    
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    logger.error(f"Overpass API request failed after {max_retries} attempts: {e}")
                    # Try fallback query as last resort
                    logger.info("Attempting fallback query as last resort...")
                    try:
                        pois_dict = _try_fallback_query(lat, lon, radius, interests)
                        break
                    except Exception as fallback_error:
                        logger.error(f"Fallback query also failed: {fallback_error}")
                        raise
                else:
                    logger.warning(f"Overpass API request failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying...")
                    time.sleep(retry_delay * (attempt + 1))
        
        # Apply constraints if provided
        if constraints:
            pois_dict = _apply_constraints(pois_dict, constraints)
        
        # Limit results
        pois_dict = pois_dict[:limit]
        
        # Convert to Pydantic models
        pois = []
        for poi_dict in pois_dict:
            try:
                poi = POI(
                    name=poi_dict["name"],
                    category=poi_dict["category"],
                    location=Location(
                        lat=poi_dict["location"]["lat"],
                        lon=poi_dict["location"]["lon"]
                    ),
                    duration_minutes=poi_dict["duration_minutes"],
                    data_source=poi_dict["data_source"],
                    source_id=poi_dict["source_id"],
                    rating=poi_dict.get("rating"),
                    description=poi_dict.get("description"),
                    opening_hours=poi_dict.get("opening_hours")
                )
                pois.append(poi)
            except Exception as e:
                logger.warning(f"Failed to create POI model: {e}")
                continue
        
        logger.info(f"Found {len(pois)} POIs for {city}")
        return pois
    
    except ValueError as e:
        # Geocoding error - city not found
        logger.error(f"Geocoding error for {city}: {e}")
        raise ValueError(f"Could not find city '{city}'. Please check the city name spelling. For Indian cities, try including state name (e.g., 'Chennai, Tamil Nadu').")
    except requests.RequestException as e:
        # API request error
        logger.error(f"OpenStreetMap API error for {city}: {e}", exc_info=True)
        raise requests.RequestException(f"Failed to search POIs for {city}. The OpenStreetMap API may be temporarily unavailable. Please try again in a few moments.")
    except Exception as e:
        logger.error(f"Error searching POIs for {city}: {e}", exc_info=True)
        raise Exception(f"An unexpected error occurred while searching POIs for {city}: {str(e)}")


def _apply_constraints(pois: List[Dict], constraints: Dict[str, Any]) -> List[Dict]:
    """
    Apply constraints to filter POIs.
    
    Args:
        pois: List of POI dictionaries
        constraints: Constraints dictionary
    
    Returns:
        Filtered list of POIs
    """
    filtered = pois
    
    # Budget constraint (if implemented)
    budget = constraints.get("budget")
    if budget:
        # This would require additional data (price ranges)
        # For now, we'll skip this filtering
        pass
    
    # Time of day constraint
    time_of_day = constraints.get("time_of_day")
    if time_of_day:
        # Filter based on opening hours if available
        # This is a simplified version
        pass
    
    # Accessibility constraint
    accessibility = constraints.get("accessibility")
    if accessibility:
        # Filter based on wheelchair accessibility tags
        # OSM has wheelchair=yes/no tags
        pass
    
    return filtered


def get_poi_details(poi_id: str) -> Optional[Dict]:
    """
    Get detailed information about a specific POI.
    
    Args:
        poi_id: POI source ID (e.g., 'way:123456')
    
    Returns:
        POI details dictionary or None
    """
    try:
        # Parse POI ID
        parts = poi_id.split(":")
        if len(parts) != 2:
            return None
        
        element_type = parts[0]
        element_id = parts[1]
        
        # Build query to get specific element
        query = f"""
[out:json][timeout:10];
(
  {element_type}({element_id});
);
out body;
>;
out skel qt;
"""
        _rate_limit()
        
        response = requests.post(
            OVERPASS_API_URL,
            data=query,
            headers={"Content-Type": "text/plain"},
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        elements = data.get("elements", [])
        
        if not elements:
            return None
        
        element = elements[0]
        tags = element.get("tags", {})
        
        return {
            "source_id": poi_id,
            "name": tags.get("name"),
            "tags": tags,
            "type": element.get("type"),
            "id": element.get("id")
        }
    
    except Exception as e:
        logger.error(f"Error getting POI details: {e}")
        return None


def filter_by_category(pois: List[POI], category: str) -> List[POI]:
    """
    Filter POIs by category.
    
    Args:
        pois: List of POI objects
        category: Category to filter by
    
    Returns:
        Filtered list of POIs
    """
    return [poi for poi in pois if poi.category.lower() == category.lower()]
