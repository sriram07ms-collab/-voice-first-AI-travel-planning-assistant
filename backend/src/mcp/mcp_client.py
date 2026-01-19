"""
MCP Client Wrapper
Provides a unified interface to call MCP tools.
"""

import sys
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Add project root to path for MCP tools
project_root = Path(__file__).parent.parent.parent.parent
mcp_tools_dir = project_root / "mcp-tools"

# Use importlib for reliable imports
import importlib.util

# Import POI Search MCP
poi_search_path = mcp_tools_dir / "poi-search" / "server.py"
if poi_search_path.exists():
    spec = importlib.util.spec_from_file_location("poi_search_server", poi_search_path)
    poi_search_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(poi_search_module)
    search_pois_mcp = poi_search_module.search_pois_mcp
else:
    search_pois_mcp = None
    logger.warning(f"POI Search MCP not found at {poi_search_path}")

# Import Itinerary Builder MCP
itinerary_builder_path = mcp_tools_dir / "itinerary-builder" / "server.py"
if itinerary_builder_path.exists():
    spec = importlib.util.spec_from_file_location("itinerary_builder_server", itinerary_builder_path)
    itinerary_builder_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(itinerary_builder_module)
    build_itinerary_mcp = itinerary_builder_module.build_itinerary_mcp
else:
    build_itinerary_mcp = None
    logger.warning(f"Itinerary Builder MCP not found at {itinerary_builder_path}")

# Import Weather MCP
weather_path = mcp_tools_dir / "weather" / "server.py"
if weather_path.exists():
    spec = importlib.util.spec_from_file_location("weather_server", weather_path)
    weather_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(weather_module)
    get_weather_forecast_mcp = weather_module.get_weather_forecast_mcp
    get_weather_for_city_mcp = weather_module.get_weather_for_city_mcp
    get_weather_for_dates_mcp = weather_module.get_weather_for_dates_mcp
else:
    get_weather_forecast_mcp = None
    get_weather_for_city_mcp = None
    get_weather_for_dates_mcp = None
    logger.warning(f"Weather MCP not found at {weather_path}")

try:
    from src.data_sources.travel_time import calculate_travel_time
except ImportError:
    from data_sources.travel_time import calculate_travel_time

logger = logging.getLogger(__name__)


class MCPClient:
    """
    Client for interacting with MCP tools.
    Provides wrapper functions for each MCP tool with error handling and retries.
    """
    
    def __init__(self):
        """Initialize MCP client."""
        self.connected = False
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to MCP tools."""
        try:
            # Test if MCP tools are importable (weather is optional)
            if search_pois_mcp is not None and build_itinerary_mcp is not None:
                self.connected = True
                available_tools = ["POI Search", "Itinerary Builder"]
                if get_weather_forecast_mcp is not None:
                    available_tools.append("Weather")
                logger.info(f"MCP tools connected successfully: {', '.join(available_tools)}")
            else:
                logger.warning("MCP tools not fully available")
                self.connected = False
        except Exception as e:
            logger.warning(f"MCP tools connection test failed: {e}")
            self.connected = False
    
    def search_pois(
        self,
        city: str,
        interests: List[str],
        constraints: Optional[Dict[str, Any]] = None,
        country: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search for Points of Interest using POI Search MCP tool.
        
        Args:
            city: City name
            interests: List of interests
            constraints: Optional constraints (budget, accessibility, time_of_day)
            country: Optional country name for better geocoding
            limit: Maximum number of POIs
        
        Returns:
            List of POI dictionaries
        """
        if search_pois_mcp is None:
            logger.error("POI Search MCP tool not available")
            return []
        
        try:
            logger.info(f"MCP Client: Searching POIs for city='{city}', country={country}, interests={interests}, limit={limit}")
            result = search_pois_mcp(
                city=city,
                interests=interests,
                constraints=constraints,
                country=country,
                limit=limit
            )
            
            # Check for errors in the result
            if "error" in result:
                error_msg = result.get("error", "Unknown error")
                logger.error(f"POI Search MCP error for city '{city}': {error_msg}")
                return []
            
            pois = result.get("pois", [])
            logger.info(f"MCP Client: POI search returned {len(pois)} POIs for '{city}'")
            
            if not pois:
                logger.warning(f"No POIs found for city '{city}' with interests {interests}. Result keys: {list(result.keys())}")
            
            return pois
        
        except Exception as e:
            logger.error(f"MCP Client POI search failed for city '{city}': {e}", exc_info=True)
            return []
    
    def build_itinerary(
        self,
        pois: List[Dict[str, Any]],
        daily_time_windows: List[Dict[str, Any]],
        pace: str = "moderate",
        preferences: Optional[Dict[str, Any]] = None,
        starting_point_location: Optional[Dict[str, float]] = None,
        travel_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build itinerary using Itinerary Builder MCP tool.
        
        Args:
            pois: List of POI dictionaries
            daily_time_windows: List of time windows per day
            pace: Pace preference ("relaxed", "moderate", "fast")
            preferences: Optional preferences
            starting_point_location: Optional starting point coordinates (lat/lon) for travel calculations
            travel_mode: Optional travel mode ("road", "airplane", "railway") for calculating travel times
        
        Returns:
            Dictionary with itinerary structure
        """
        if build_itinerary_mcp is None:
            logger.error("Itinerary Builder MCP tool not available")
            return {
                "itinerary": {},
                "total_travel_time": 0,
                "explanation": "Itinerary Builder MCP tool not available"
            }
        
        try:
            logger.info(f"MCP Client: Building itinerary for {len(daily_time_windows)} days")
            if starting_point_location:
                logger.info(f"Using starting point location: {starting_point_location}")
            result = build_itinerary_mcp(
                pois=pois,
                daily_time_windows=daily_time_windows,
                pace=pace,
                preferences=preferences,
                starting_point_location=starting_point_location,
                travel_mode=travel_mode
            )
            
            if "error" in result:
                logger.error(f"Itinerary Builder MCP error: {result['error']}")
                return {
                    "itinerary": {},
                    "total_travel_time": 0,
                    "explanation": f"Error: {result['error']}"
                }
            
            return result
        
        except Exception as e:
            logger.error(f"MCP Client itinerary build failed: {e}", exc_info=True)
            return {
                "itinerary": {},
                "total_travel_time": 0,
                "explanation": f"Error building itinerary: {str(e)}"
            }
    
    def estimate_travel_time(
        self,
        origin: Dict[str, float],
        destination: Dict[str, float],
        mode: str = "walking"
    ) -> Dict[str, Any]:
        """
        Estimate travel time between two locations.
        
        Args:
            origin: Origin location with 'lat' and 'lon'
            destination: Destination location with 'lat' and 'lon'
            mode: Travel mode ("walking", "driving", "public_transit")
        
        Returns:
            Dictionary with travel time information
        """
        try:
            return calculate_travel_time(
                origin=origin,
                destination=destination,
                mode=mode
            )
        except Exception as e:
            logger.error(f"Travel time estimation failed: {e}")
            return {
                "duration_minutes": 0,
                "distance_km": 0,
                "mode": mode,
                "source": "error"
            }
    
    def get_weather_forecast(
        self,
        lat: float,
        lon: float,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        forecast_days: int = 7
    ) -> Dict[str, Any]:
        """
        Get weather forecast using Weather MCP tool.
        
        Args:
            lat: Latitude
            lon: Longitude
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            forecast_days: Number of forecast days (default: 7, max: 16)
        
        Returns:
            Dictionary with weather forecast data
        """
        if get_weather_forecast_mcp is None:
            logger.error("Weather MCP tool not available")
            return {
                "error": "Weather MCP tool not available",
                "latitude": lat,
                "longitude": lon,
                "daily": [],
                "source": "error"
            }
        
        try:
            logger.info(f"MCP Client: Getting weather forecast for ({lat}, {lon}), forecast_days={forecast_days}")
            result = get_weather_forecast_mcp(
                lat=lat,
                lon=lon,
                start_date=start_date,
                end_date=end_date,
                forecast_days=forecast_days
            )
            
            if "error" in result:
                logger.error(f"Weather MCP error: {result.get('error')}")
            
            return result
        
        except Exception as e:
            logger.error(f"MCP Client weather forecast failed: {e}", exc_info=True)
            return {
                "error": str(e),
                "latitude": lat,
                "longitude": lon,
                "daily": [],
                "source": "error"
            }
    
    def get_weather_for_city(
        self,
        city: str,
        country: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        forecast_days: int = 7
    ) -> Dict[str, Any]:
        """
        Get weather forecast for a city using Weather MCP tool.
        
        Args:
            city: City name
            country: Optional country name for better geocoding
            start_date: Start date in YYYY-MM-DD format (optional)
            end_date: End date in YYYY-MM-DD format (optional)
            forecast_days: Number of forecast days (default: 7, max: 16)
        
        Returns:
            Dictionary with weather forecast data
        """
        if get_weather_for_city_mcp is None:
            logger.error("Weather MCP tool not available")
            return {
                "error": "Weather MCP tool not available",
                "city": city,
                "daily": [],
                "source": "error"
            }
        
        try:
            logger.info(f"MCP Client: Getting weather for city='{city}', country={country}, forecast_days={forecast_days}")
            result = get_weather_for_city_mcp(
                city=city,
                country=country,
                start_date=start_date,
                end_date=end_date,
                forecast_days=forecast_days
            )
            
            if "error" in result:
                logger.error(f"Weather MCP error for city '{city}': {result.get('error')}")
            
            return result
        
        except Exception as e:
            logger.error(f"MCP Client weather for city failed: {e}", exc_info=True)
            return {
                "error": str(e),
                "city": city,
                "daily": [],
                "source": "error"
            }
    
    def get_weather_for_dates(
        self,
        city: str,
        travel_dates: List[str],
        country: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get weather forecast for specific travel dates using Weather MCP tool.
        
        Args:
            city: City name
            travel_dates: List of dates in YYYY-MM-DD format
            country: Optional country name for better geocoding
        
        Returns:
            Dictionary mapping date to weather data
        """
        if get_weather_for_dates_mcp is None:
            logger.error("Weather MCP tool not available")
            return {}
        
        try:
            logger.info(f"MCP Client: Getting weather for city='{city}', dates={travel_dates}")
            result = get_weather_for_dates_mcp(
                city=city,
                travel_dates=travel_dates,
                country=country
            )
            
            logger.info(f"MCP Client: Retrieved weather for {len(result)} dates")
            return result
        
        except Exception as e:
            logger.error(f"MCP Client weather for dates failed: {e}", exc_info=True)
            return {}


# Global MCP client instance
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """
    Get or create global MCP client instance.
    
    Returns:
        MCPClient instance
    """
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client


def connect_to_mcp_servers() -> bool:
    """
    Connect to MCP servers (for compatibility).
    
    Returns:
        True if connected successfully
    """
    client = get_mcp_client()
    return client.connected
