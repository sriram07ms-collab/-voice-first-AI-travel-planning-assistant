"""
Google Places API integration for Points of Interest (POI) search.
Uses Places API (New) - Text Search and Nearby Search.
Falls back to OpenStreetMap if Google Places API fails.
"""

import requests
import time
from typing import List, Dict, Optional, Any, Tuple
import logging
from collections import OrderedDict

# Use try/except for imports to handle both relative and absolute
try:
    from .geocoding import get_city_coordinates
    from ..models.itinerary_models import POI, Location
    from ..utils.config import get_settings
except ImportError:
    from src.data_sources.geocoding import get_city_coordinates
    from src.models.itinerary_models import POI, Location
    from src.utils.config import get_settings

logger = logging.getLogger(__name__)

# Google Places API (New) endpoints
GOOGLE_PLACES_TEXT_SEARCH_URL = "https://places.googleapis.com/v1/places:searchText"
GOOGLE_PLACES_NEARBY_SEARCH_URL = "https://places.googleapis.com/v1/places:searchNearby"

# Rate limiting: Google Places API has quotas
_last_request_time = 0
_request_interval = 0.1  # 100ms between requests (10 requests/second max)

# Cache for POI search results (TTL: 24 hours)
_poi_search_cache: Dict[str, Tuple[List[POI], float]] = OrderedDict()
_cache_max_size = 500
_cache_ttl = 86400  # 24 hours in seconds


def _rate_limit():
    """Ensure we don't exceed Google Places API rate limits."""
    global _last_request_time
    current_time = time.time()
    time_since_last = current_time - _last_request_time
    
    if time_since_last < _request_interval:
        sleep_time = _request_interval - time_since_last
        time.sleep(sleep_time)
    
    _last_request_time = time.time()


def _get_poi_cache_key(city: str, interests: List[str], country: Optional[str] = None, state: Optional[str] = None) -> str:
    """Generate cache key for POI search request."""
    interests_str = ",".join(sorted(interests))
    location_str = f"{city}"
    if country:
        location_str += f",{country}"
    if state:
        location_str += f",{state}"
    return f"{location_str}|{interests_str}"


def _get_cached_pois(cache_key: str) -> Optional[List[POI]]:
    """Get cached POI search results if available and not expired."""
    if cache_key not in _poi_search_cache:
        return None
    
    results, timestamp = _poi_search_cache[cache_key]
    current_time = time.time()
    
    # Check if cache entry is expired
    if current_time - timestamp > _cache_ttl:
        del _poi_search_cache[cache_key]
        return None
    
    # Move to end (LRU)
    _poi_search_cache.move_to_end(cache_key)
    logger.debug(f"Cache hit for POI search: {cache_key}")
    return results


def _set_cached_pois(cache_key: str, results: List[POI]):
    """Cache POI search results."""
    # Remove oldest entries if cache is full
    while len(_poi_search_cache) >= _cache_max_size:
        _poi_search_cache.popitem(last=False)
    
    _poi_search_cache[cache_key] = (results, time.time())
    logger.debug(f"Cached POI search results: {cache_key} ({len(results)} POIs)")


def _map_interests_to_place_types(interests: List[str]) -> List[str]:
    """
    Map user interests to Google Places API place types.
    
    Args:
        interests: List of interests (e.g., ['food', 'culture'])
    
    Returns:
        List of Google Places API place types
    """
    interest_mapping = {
        "food": [
            "restaurant",
            "cafe",
            "meal_takeaway",
            "bakery",
            "food",
            "meal_delivery"
        ],
        "culture": [
            "museum",
            "art_gallery",
            "tourist_attraction",
            "church",
            "hindu_temple",
            "mosque",
            "synagogue",
            "place_of_worship"
        ],
        "shopping": [
            "shopping_mall",
            "store",
            "clothing_store",
            "jewelry_store",
            "supermarket"
        ],
        "nightlife": [
            "bar",
            "night_club",
            "casino"
        ],
        "nature": [
            "park",
            "zoo",
            "aquarium"
        ],
        "beaches": [
            "beach"
        ],
        "religion": [
            "place_of_worship",
            "church",
            "hindu_temple",
            "mosque",
            "synagogue"
        ],
        "historical": [
            "tourist_attraction",
            "museum",
            "art_gallery"
        ]
    }
    
    place_types = []
    for interest in interests:
        interest_lower = interest.lower()
        if interest_lower in interest_mapping:
            place_types.extend(interest_mapping[interest_lower])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_types = []
    for ptype in place_types:
        if ptype not in seen:
            seen.add(ptype)
            unique_types.append(ptype)
    
    return unique_types


def _map_place_type_to_category(place_type: str) -> str:
    """
    Map Google Places API place type to our internal category.
    
    Args:
        place_type: Google Places API place type
    
    Returns:
        Internal category string
    """
    category_mapping = {
        "restaurant": "restaurant",
        "cafe": "restaurant",
        "meal_takeaway": "restaurant",
        "bakery": "restaurant",
        "food": "restaurant",
        "meal_delivery": "restaurant",
        "museum": "museum",
        "art_gallery": "museum",
        "tourist_attraction": "attraction",
        "shopping_mall": "shopping",
        "store": "shopping",
        "clothing_store": "shopping",
        "jewelry_store": "shopping",
        "supermarket": "shopping",
        "park": "park",
        "zoo": "park",
        "aquarium": "park",
        "bar": "nightlife",
        "night_club": "nightlife",
        "casino": "nightlife",
        "church": "historical",
        "hindu_temple": "historical",
        "mosque": "historical",
        "synagogue": "historical",
        "place_of_worship": "historical",
        "beach": "nature"
    }
    
    return category_mapping.get(place_type, "attraction")


def _estimate_duration_from_category(category: str, rating: Optional[float] = None, user_rating_count: Optional[int] = None) -> int:
    """
    Estimate duration in minutes based on REAL Google Places data (category, rating, user count).
    Uses actual Google Places API data to make intelligent estimates.
    
    NOTE: Google Places API doesn't provide visit duration, so we estimate based on:
    - Category (from Google Places types)
    - Rating (from Google Places rating)
    - User rating count (from Google Places userRatingCount)
    
    Args:
        category: POI category (derived from Google Places types)
        rating: Google Places rating (0-5) - REAL data from Google Places API
        user_rating_count: Number of user ratings - REAL data from Google Places API
    
    Returns:
        Estimated duration in minutes (based on real Google Places data)
    """
    # Base duration by category (based on typical visit times)
    base_duration_map = {
        "restaurant": 60,      # Typical meal time
        "museum": 120,         # Museums typically need 1-2 hours
        "attraction": 90,      # Tourist attractions: 1-1.5 hours
        "shopping": 60,        # Shopping: ~1 hour
        "park": 60,            # Parks: ~1 hour
        "nightlife": 120,      # Nightlife venues: 2+ hours
        "historical": 90,      # Historical sites: 1-1.5 hours
        "nature": 60           # Nature spots: ~1 hour
    }
    base_duration = base_duration_map.get(category, 90)
    
    # Adjust based on REAL Google Places rating and popularity data
    if rating is not None and user_rating_count is not None:
        # Use actual Google Places data to refine estimate
        if rating >= 4.5 and user_rating_count >= 100:
            # Highly-rated, popular place (from Google Places) - visitors spend more time
            adjustment = int(base_duration * 0.25)
            base_duration += adjustment
            logger.debug(f"Duration adjusted +{adjustment} min for highly-rated popular place (rating: {rating}, reviews: {user_rating_count})")
        elif rating >= 4.0 and user_rating_count >= 50:
            # Well-rated place (from Google Places) - add some time
            adjustment = int(base_duration * 0.15)
            base_duration += adjustment
            logger.debug(f"Duration adjusted +{adjustment} min for well-rated place (rating: {rating}, reviews: {user_rating_count})")
        elif rating < 3.5:
            # Lower-rated place (from Google Places) - visitors spend less time
            adjustment = int(base_duration * 0.1)
            base_duration = max(base_duration - adjustment, int(base_duration * 0.7))
            logger.debug(f"Duration adjusted -{adjustment} min for lower-rated place (rating: {rating}, reviews: {user_rating_count})")
    
    return base_duration


def search_railway_station(
    city: str,
    country: Optional[str] = None,
    state: Optional[str] = None
) -> Optional[Dict[str, float]]:
    """
    Search for central railway station in a city using Google Places API.
    
    Args:
        city: City name
        country: Optional country name
        state: Optional state/province name
    
    Returns:
        Dictionary with 'lat' and 'lon' keys, or None if not found
    """
    settings = get_settings()
    
    if not settings.google_maps_api_key:
        logger.debug("Google Maps API key not configured, cannot search for railway station")
        return None
    
    try:
        # Get city coordinates
        coords = get_city_coordinates(city, country, state)
        lat = coords["lat"]
        lon = coords["lon"]
        
        # Rate limit
        _rate_limit()
        
        # Search for railway station
        text_query = f"central railway station {city}"
        if country:
            text_query += f", {country}"
        
        request_body = {
            "textQuery": text_query,
            "maxResultCount": 5,
            "locationBias": {
                "circle": {
                    "center": {
                        "latitude": lat,
                        "longitude": lon
                    },
                    "radius": 20000.0  # 20km radius
                }
            },
            "includedType": "train_station",  # Single string, not array
            "languageCode": "en"
        }
        
        field_mask = "places.id,places.displayName,places.location"
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": settings.google_maps_api_key,
            "X-Goog-FieldMask": field_mask
        }
        
        logger.info(f"Searching for railway station in {city} using Google Places API")
        
        response = requests.post(
            GOOGLE_PLACES_TEXT_SEARCH_URL,
            json=request_body,
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            logger.warning(f"Google Places API returned status {response.status_code} for railway station search")
            return None
        
        data = response.json()
        
        if "error" in data:
            logger.warning(f"Google Places API error for railway station: {data['error'].get('message', 'Unknown error')}")
            return None
        
        places = data.get("places", [])
        if not places:
            logger.warning(f"No railway station found for {city}")
            return None
        
        # Use first result (most relevant)
        place = places[0]
        location = place.get("location", {})
        lat_station = location.get("latitude")
        lon_station = location.get("longitude")
        station_name = place.get("displayName", {}).get("text", "Railway Station")
        
        if lat_station and lon_station:
            logger.info(f"Found railway station: {station_name} at ({lat_station}, {lon_station})")
            return {
                "lat": lat_station,
                "lon": lon_station,
                "name": station_name
            }
        
        return None
    
    except Exception as e:
        logger.error(f"Failed to search for railway station: {e}", exc_info=True)
        return None


def search_pois_google_places(
    city: str,
    interests: List[str],
    constraints: Optional[Dict[str, Any]] = None,
    country: Optional[str] = None,
    state: Optional[str] = None,
    limit: int = 50
) -> List[POI]:
    """
    Search for Points of Interest using Google Places API (New).
    
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
    settings = get_settings()
    
    # Check if API key is configured
    if not settings.google_maps_api_key:
        logger.warning("⚠️ Google Maps API key not configured! Set GOOGLE_MAPS_API_KEY environment variable. Skipping Google Places API.")
        return []
    
    # Log API key status (without exposing the key)
    api_key_preview = f"{settings.google_maps_api_key[:10]}..." if len(settings.google_maps_api_key) > 10 else "***"
    logger.info(f"✅ Google Maps API key is configured ({api_key_preview}), proceeding with Google Places API search for {city}")
    
    # Check cache first (only if no constraints that would affect results)
    if not constraints or (not constraints.get("budget") and not constraints.get("time_of_day")):
        cache_key = _get_poi_cache_key(city, interests, country, state)
        cached_pois = _get_cached_pois(cache_key)
        if cached_pois is not None:
            logger.info(f"Returning {len(cached_pois)} cached POIs for {city} (from Google Places API)")
            return cached_pois[:limit] if limit else cached_pois
            return cached_pois[:limit] if limit else cached_pois
    
    try:
        # Get city coordinates
        logger.info(f"Searching POIs for {city} using Google Places API")
        coords = get_city_coordinates(city, country, state)
        lat = coords["lat"]
        lon = coords["lon"]
        
        # Map interests to place types
        place_types = _map_interests_to_place_types(interests)
        
        if not place_types:
            logger.warning(f"No valid place types found for interests: {interests}")
            return []
        
        logger.info(f"Mapped interests {interests} to Google Places types: {place_types}")
        
        # Rate limit
        _rate_limit()
        
        # Use Text Search (New) for better flexibility
        # Build text query from place types and city
        type_names = {
            "restaurant": "restaurants",
            "cafe": "cafes",
            "museum": "museums",
            "tourist_attraction": "attractions",
            "shopping_mall": "shopping malls",
            "park": "parks",
            "art_gallery": "art galleries",
            "hindu_temple": "temples",
            "place_of_worship": "places of worship"
        }
        
        # Build text query using place types - improved for Indian cities
        if place_types:
            query_parts = [type_names.get(ptype, ptype.replace("_", " ")) for ptype in place_types[:3] if ptype in type_names]
            if query_parts:
                # For Indian cities, include state/country in query for better results
                if country and country.lower() == "india":
                    # Try to include state if available (e.g., "Chennai, Tamil Nadu")
                    if state:
                        text_query = f"{', '.join(query_parts)} in {city}, {state}, {country}"
                    else:
                        # Map major Indian cities to their states
                        city_state_map = {
                            "chennai": "Tamil Nadu",
                            "mumbai": "Maharashtra",
                            "delhi": "Delhi",
                            "new delhi": "Delhi",
                            "bangalore": "Karnataka",
                            "hyderabad": "Telangana",
                            "kolkata": "West Bengal",
                            "pune": "Maharashtra",
                            "jaipur": "Rajasthan",
                            "ahmedabad": "Gujarat"
                        }
                        city_lower = city.lower()
                        if city_lower in city_state_map:
                            text_query = f"{', '.join(query_parts)} in {city}, {city_state_map[city_lower]}, {country}"
                        else:
                            text_query = f"{', '.join(query_parts)} in {city}, {country}"
                else:
                    text_query = f"{', '.join(query_parts)} in {city}"
                    if country:
                        text_query += f", {country}"
            else:
                # Fallback to generic query
                if country and country.lower() == "india":
                    if state:
                        text_query = f"places in {city}, {state}, {country}"
                    else:
                        city_state_map = {
                            "chennai": "Tamil Nadu",
                            "mumbai": "Maharashtra",
                            "delhi": "Delhi",
                            "new delhi": "Delhi",
                            "bangalore": "Karnataka",
                            "hyderabad": "Telangana",
                            "kolkata": "West Bengal",
                            "pune": "Maharashtra",
                            "jaipur": "Rajasthan",
                            "ahmedabad": "Gujarat"
                        }
                        city_lower = city.lower()
                        if city_lower in city_state_map:
                            text_query = f"places in {city}, {city_state_map[city_lower]}, {country}"
                        else:
                            text_query = f"places in {city}, {country}"
                else:
                    text_query = f"places in {city}"
                    if country:
                        text_query += f", {country}"
        else:
            # No place types - use city with location context
            if country and country.lower() == "india":
                if state:
                    text_query = f"places in {city}, {state}, {country}"
                else:
                    city_state_map = {
                        "chennai": "Tamil Nadu",
                        "mumbai": "Maharashtra",
                        "delhi": "Delhi",
                        "new delhi": "Delhi",
                        "bangalore": "Karnataka",
                        "hyderabad": "Telangana",
                        "kolkata": "West Bengal",
                        "pune": "Maharashtra",
                        "jaipur": "Rajasthan",
                        "ahmedabad": "Gujarat"
                    }
                    city_lower = city.lower()
                    if city_lower in city_state_map:
                        text_query = f"places in {city}, {city_state_map[city_lower]}, {country}"
                    else:
                        text_query = f"places in {city}, {country}"
            else:
                text_query = f"places in {city}"
                if country:
                    text_query += f", {country}"
        
        # Build request body for Text Search (New)
        request_body = {
            "textQuery": text_query,
            "maxResultCount": min(limit, 20),  # Google limits to 20 per request
            "locationBias": {
                "circle": {
                    "center": {
                        "latitude": lat,
                        "longitude": lon
                    },
                    "radius": 10000.0  # 10km radius
                }
            },
            "languageCode": "en"
        }
        
        # Add type filter if we have specific types
        # NOTE: Google Places API (New) only accepts a SINGLE includedType (not an array)
        # If we have multiple types, we'll use the first one and rely on textQuery for others
        if place_types:
            # Use the first place type as includedType (must be single string, not array)
            request_body["includedType"] = place_types[0]
            logger.debug(f"Using includedType: {place_types[0]} (from {len(place_types)} total types)")
        
        # Add optional filters
        if constraints:
            # Google Places API (New) uses priceLevels as an array, not priceRange
            if constraints.get("budget") == "low":
                request_body["priceLevels"] = ["PRICE_LEVEL_INEXPENSIVE"]
            elif constraints.get("budget") == "high":
                request_body["priceLevels"] = ["PRICE_LEVEL_EXPENSIVE"]
            elif constraints.get("budget") == "moderate":
                request_body["priceLevels"] = ["PRICE_LEVEL_MODERATE"]
            
            if constraints.get("time_of_day") in ["morning", "afternoon"]:
                # Add openNow filter for morning/afternoon
                request_body["openNow"] = True
        
        # Field mask - only request fields we need
        field_mask = "places.id,places.displayName,places.location,places.types,places.rating,places.userRatingCount,places.formattedAddress,places.currentOpeningHours,places.priceLevel"
        
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": settings.google_maps_api_key,
            "X-Goog-FieldMask": field_mask
        }
        
        logger.debug(f"Google Places Text Search request: {text_query}")
        
        # Make request
        response = requests.post(
            GOOGLE_PLACES_TEXT_SEARCH_URL,
            json=request_body,
            headers=headers,
            timeout=10
        )
        
        if response.status_code != 200:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get("error", {}).get("message", f"HTTP {response.status_code}")
            logger.warning(f"Google Places API returned status {response.status_code}: {error_msg}")
            return []
        
        data = response.json()
        
        # Check for errors
        if "error" in data:
            error_msg = data["error"].get("message", "Unknown error")
            logger.warning(f"Google Places API error: {error_msg}")
            return []
        
        # Parse results
        places = data.get("places", [])
        logger.info(f"Google Places API returned {len(places)} places")
        
        pois = []
        for place in places:
            try:
                # Extract place data
                place_id = place.get("id", "")
                display_name = place.get("displayName", {}).get("text", "Unknown Place")
                location = place.get("location", {})
                lat_poi = location.get("latitude")
                lon_poi = location.get("longitude")
                types = place.get("types", [])
                rating = place.get("rating")
                user_rating_count = place.get("userRatingCount", 0)
                address = place.get("formattedAddress", "")
                opening_hours = place.get("currentOpeningHours", {})
                price_level = place.get("priceLevel")
                
                if not lat_poi or not lon_poi:
                    logger.debug(f"Skipping place '{display_name}': no coordinates")
                    continue
                
                # Determine category from types
                category = "attraction"  # default
                for ptype in types:
                    mapped_category = _map_place_type_to_category(ptype)
                    if mapped_category != "attraction":
                        category = mapped_category
                        break
                
                # Format opening hours
                opening_hours_str = None
                if opening_hours:
                    weekday_text = opening_hours.get("weekdayText", [])
                    if weekday_text:
                        opening_hours_str = "; ".join(weekday_text[:3])  # Limit to 3 days
                
                # Estimate duration using category, rating, and user count
                duration_minutes = _estimate_duration_from_category(
                    category=category,
                    rating=rating,
                    user_rating_count=user_rating_count
                )
                
                poi = POI(
                    name=display_name,
                    category=category,
                    location=Location(lat=lat_poi, lon=lon_poi),
                    duration_minutes=duration_minutes,
                    data_source="google_places",  # Explicitly set to google_places
                    source_id=f"place_id:{place_id}",
                    rating=rating,
                    description=address,
                    opening_hours=opening_hours_str
                )
                
                logger.debug(f"Created POI: {display_name} (category: {category}, duration: {duration_minutes}min, rating: {rating}, data_source: google_places)")
                
                pois.append(poi)
                
            except Exception as e:
                logger.warning(f"Failed to parse place: {e}")
                continue
        
        logger.info(f"Parsed {len(pois)} POIs from Google Places API")
        
        # Cache results (only if no constraints that would affect results)
        if not constraints or (not constraints.get("budget") and not constraints.get("time_of_day")):
            cache_key = _get_poi_cache_key(city, interests, country, state)
            _set_cached_pois(cache_key, pois)
        
        return pois[:limit]  # Limit results
        
    except requests.RequestException as e:
        logger.warning(f"Google Places API request failed: {e}")
        return []
    except Exception as e:
        logger.error(f"Google Places API search failed: {e}", exc_info=True)
        return []
