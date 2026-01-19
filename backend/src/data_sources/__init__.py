"""
Data sources module for external APIs and data providers.
"""

from .poi_search import search_pois
from .openstreetmap import (
    search_pois_overpass,
    get_poi_details,
    filter_by_category
)
from .google_places import search_pois_google_places, search_railway_station
from .geocoding import (
    get_city_coordinates,
    get_city_coordinates_cached,
    search_city
)
from .travel_time import (
    calculate_travel_time,
    estimate_travel_time_batch,
    calculate_distance
)
from .wikivoyage import (
    scrape_city_page,
    chunk_text,
    extract_sections,
    get_city_url
)
from .weather import (
    get_weather_forecast,
    get_weather_for_city,
    get_weather_for_dates,
    get_weather_summary_for_day
)

__all__ = [
    "search_pois",  # Main entry point - uses Google Places first, Overpass fallback
    "search_pois_google_places",  # Google Places API search
    "search_railway_station",  # Search for railway station using Google Places
    "search_pois_overpass",  # OpenStreetMap/Overpass API search (fallback)
    "get_poi_details",
    "filter_by_category",
    "get_city_coordinates",
    "get_city_coordinates_cached",
    "search_city",
    "calculate_travel_time",
    "estimate_travel_time_batch",
    "calculate_distance",
    "scrape_city_page",
    "chunk_text",
    "extract_sections",
    "get_city_url",
    "get_weather_forecast",
    "get_weather_for_city",
    "get_weather_for_dates",
    "get_weather_summary_for_day"
]
