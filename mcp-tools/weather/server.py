"""
Weather MCP Tool Server
Implements weather forecast MCP tools using Open-Meteo API.
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
    from src.data_sources.weather import (
        get_weather_forecast as backend_get_weather_forecast,
        get_weather_for_city as backend_get_weather_for_city,
        get_weather_for_dates as backend_get_weather_for_dates
    )
except ImportError:
    # Fallback for direct imports
    sys.path.insert(0, str(backend_dir / "src"))
    from data_sources.weather import (
        get_weather_forecast as backend_get_weather_forecast,
        get_weather_for_city as backend_get_weather_for_city,
        get_weather_for_dates as backend_get_weather_for_dates
    )

logger = logging.getLogger(__name__)


def get_weather_forecast_mcp(
    lat: float,
    lon: float,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    forecast_days: int = 7
) -> Dict[str, Any]:
    """
    MCP Tool: Get weather forecast for a location using coordinates.
    
    This is the MCP-compliant wrapper around the Open-Meteo weather forecast API.
    
    Args:
        lat: Latitude (e.g., 26.9124)
        lon: Longitude (e.g., 75.7873)
        start_date: Start date in YYYY-MM-DD format (optional, defaults to today)
        end_date: End date in YYYY-MM-DD format (optional)
        forecast_days: Number of forecast days (default: 7, max: 16)
    
    Returns:
        Dictionary with MCP-compliant structure:
        {
            "latitude": float,
            "longitude": float,
            "timezone": str,
            "daily": [
                {
                    "date": str,
                    "weather_code": int,
                    "condition": str,
                    "description": str,
                    "icon": str,
                    "temperature_max": float,
                    "temperature_min": float,
                    "precipitation_probability": int,
                    "precipitation_sum": float,
                    "indoor_needed": bool
                }
            ],
            "source": "open-meteo"
        }
    """
    try:
        logger.info(f"MCP Weather Forecast: lat={lat}, lon={lon}, forecast_days={forecast_days}")
        
        # Call the underlying weather forecast function
        result = backend_get_weather_forecast(
            lat=lat,
            lon=lon,
            start_date=start_date,
            end_date=end_date,
            forecast_days=forecast_days
        )
        
        # Check for errors
        if "error" in result:
            logger.error(f"MCP Weather Forecast error: {result.get('error')}")
            return result
        
        logger.info(f"MCP Weather Forecast: Retrieved {len(result.get('daily', []))} days of forecast")
        return result
    
    except Exception as e:
        logger.error(f"MCP Weather Forecast error: {e}", exc_info=True)
        return {
            "error": str(e),
            "latitude": lat,
            "longitude": lon,
            "daily": [],
            "source": "error"
        }


def get_weather_for_city_mcp(
    city: str,
    country: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    forecast_days: int = 7
) -> Dict[str, Any]:
    """
    MCP Tool: Get weather forecast for a city by name.
    
    This is the MCP-compliant wrapper around the Open-Meteo weather forecast API.
    Automatically resolves city name to coordinates using geocoding.
    
    Args:
        city: City name (e.g., "Jaipur")
        country: Optional country name for better geocoding (e.g., "India")
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
        forecast_days: Number of forecast days (default: 7, max: 16)
    
    Returns:
        Dictionary with MCP-compliant structure (same as get_weather_forecast_mcp)
    """
    try:
        logger.info(f"MCP Weather for City: city={city}, country={country}, forecast_days={forecast_days}")
        
        # Call the underlying weather for city function
        result = backend_get_weather_for_city(
            city=city,
            country=country,
            start_date=start_date,
            end_date=end_date,
            forecast_days=forecast_days
        )
        
        # Check for errors
        if "error" in result:
            logger.error(f"MCP Weather for City error: {result.get('error')}")
            return result
        
        logger.info(f"MCP Weather for City: Retrieved {len(result.get('daily', []))} days of forecast for {city}")
        return result
    
    except Exception as e:
        logger.error(f"MCP Weather for City error: {e}", exc_info=True)
        return {
            "error": str(e),
            "city": city,
            "daily": [],
            "source": "error"
        }


def get_weather_for_dates_mcp(
    city: str,
    travel_dates: List[str],
    country: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    MCP Tool: Get weather forecast for specific travel dates.
    
    This is the MCP-compliant wrapper that returns weather data mapped to specific dates.
    
    Args:
        city: City name (e.g., "Jaipur")
        travel_dates: List of dates in YYYY-MM-DD format (e.g., ["2024-01-15", "2024-01-16"])
        country: Optional country name for better geocoding
    
    Returns:
        Dictionary mapping date to weather data:
        {
            "2024-01-15": {
                "date": str,
                "weather_code": int,
                "condition": str,
                "description": str,
                "icon": str,
                "temperature_max": float,
                "temperature_min": float,
                "precipitation_probability": int,
                "precipitation_sum": float,
                "indoor_needed": bool
            },
            ...
        }
    """
    try:
        logger.info(f"MCP Weather for Dates: city={city}, dates={travel_dates}")
        
        # Call the underlying weather for dates function
        result = backend_get_weather_for_dates(
            city=city,
            travel_dates=travel_dates,
            country=country
        )
        
        logger.info(f"MCP Weather for Dates: Retrieved weather for {len(result)} dates")
        return result
    
    except Exception as e:
        logger.error(f"MCP Weather for Dates error: {e}", exc_info=True)
        return {}


# For direct testing
if __name__ == "__main__":
    # Test the MCP tool
    print("Testing Weather MCP Tool...")
    
    # Test 1: Get weather for coordinates
    print("\n1. Testing get_weather_forecast_mcp:")
    result = get_weather_forecast_mcp(
        lat=26.9124,
        lon=75.7873,
        forecast_days=3
    )
    if "error" not in result:
        print(f"   Retrieved {len(result.get('daily', []))} days of forecast")
        if result.get('daily'):
            first_day = result['daily'][0]
            print(f"   First day: {first_day.get('date')} - {first_day.get('description')}, "
                  f"Temp: {first_day.get('temperature_min')}°C - {first_day.get('temperature_max')}°C")
    else:
        print(f"   Error: {result.get('error')}")
    
    # Test 2: Get weather for city
    print("\n2. Testing get_weather_for_city_mcp:")
    result = get_weather_for_city_mcp(
        city="Jaipur",
        country="India",
        forecast_days=3
    )
    if "error" not in result:
        print(f"   Retrieved {len(result.get('daily', []))} days of forecast for Jaipur")
    else:
        print(f"   Error: {result.get('error')}")
    
    # Test 3: Get weather for specific dates
    print("\n3. Testing get_weather_for_dates_mcp:")
    from datetime import datetime, timedelta
    today = datetime.now()
    test_dates = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(3)]
    result = get_weather_for_dates_mcp(
        city="Jaipur",
        travel_dates=test_dates
    )
    print(f"   Retrieved weather for {len(result)} dates")
    for date, weather in result.items():
        print(f"   {date}: {weather.get('description')}, "
              f"Temp: {weather.get('temperature_min')}°C - {weather.get('temperature_max')}°C")
