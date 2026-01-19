"""
Open-Meteo API integration for weather forecasts.
Provides weather forecast data for itinerary planning.
"""

import requests
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging

# Use try/except for imports to handle both relative and absolute
try:
    from .geocoding import get_city_coordinates
    from ..utils.config import settings
except ImportError:
    from src.data_sources.geocoding import get_city_coordinates
    from src.utils.config import settings

logger = logging.getLogger(__name__)

# Open-Meteo API base URL (from settings)
OPEN_METEO_API_URL = getattr(settings, 'open_meteo_api_url', 'https://api.open-meteo.com/v1')


def _parse_weather_code(weather_code: int) -> Dict[str, Any]:
    """
    Parse WMO weather code to human-readable description.
    Based on WMO Weather interpretation codes (WW).
    
    Args:
        weather_code: WMO weather code (0-99)
    
    Returns:
        Dictionary with description and icon info
    """
    # WMO Weather interpretation codes (simplified)
    code_map = {
        # Clear
        0: {"description": "Clear sky", "icon": "☀️", "condition": "clear", "indoor_needed": False},
        1: {"description": "Mainly clear", "icon": "🌤️", "condition": "mostly_clear", "indoor_needed": False},
        
        # Partly cloudy
        2: {"description": "Partly cloudy", "icon": "⛅", "condition": "partly_cloudy", "indoor_needed": False},
        3: {"description": "Overcast", "icon": "☁️", "condition": "overcast", "indoor_needed": False},
        
        # Fog
        45: {"description": "Foggy", "icon": "🌫️", "condition": "fog", "indoor_needed": False},
        48: {"description": "Depositing rime fog", "icon": "🌫️", "condition": "fog", "indoor_needed": False},
        
        # Drizzle
        51: {"description": "Light drizzle", "icon": "🌦️", "condition": "drizzle", "indoor_needed": True},
        53: {"description": "Moderate drizzle", "icon": "🌦️", "condition": "drizzle", "indoor_needed": True},
        55: {"description": "Dense drizzle", "icon": "🌦️", "condition": "drizzle", "indoor_needed": True},
        
        # Freezing drizzle
        56: {"description": "Light freezing drizzle", "icon": "🌨️", "condition": "freezing_rain", "indoor_needed": True},
        57: {"description": "Dense freezing drizzle", "icon": "🌨️", "condition": "freezing_rain", "indoor_needed": True},
        
        # Rain
        61: {"description": "Slight rain", "icon": "🌧️", "condition": "rain", "indoor_needed": True},
        63: {"description": "Moderate rain", "icon": "🌧️", "condition": "rain", "indoor_needed": True},
        65: {"description": "Heavy rain", "icon": "🌧️", "condition": "rain", "indoor_needed": True},
        
        # Freezing rain
        66: {"description": "Light freezing rain", "icon": "🌨️", "condition": "freezing_rain", "indoor_needed": True},
        67: {"description": "Heavy freezing rain", "icon": "🌨️", "condition": "freezing_rain", "indoor_needed": True},
        
        # Snow
        71: {"description": "Slight snow", "icon": "🌨️", "condition": "snow", "indoor_needed": True},
        73: {"description": "Moderate snow", "icon": "🌨️", "condition": "snow", "indoor_needed": True},
        75: {"description": "Heavy snow", "icon": "🌨️", "condition": "snow", "indoor_needed": True},
        
        # Snow grains
        77: {"description": "Snow grains", "icon": "🌨️", "condition": "snow", "indoor_needed": True},
        
        # Rain showers
        80: {"description": "Slight rain showers", "icon": "🌦️", "condition": "rain_showers", "indoor_needed": True},
        81: {"description": "Moderate rain showers", "icon": "🌦️", "condition": "rain_showers", "indoor_needed": True},
        82: {"description": "Violent rain showers", "icon": "🌧️", "condition": "rain_showers", "indoor_needed": True},
        
        # Snow showers
        85: {"description": "Slight snow showers", "icon": "🌨️", "condition": "snow_showers", "indoor_needed": True},
        86: {"description": "Heavy snow showers", "icon": "🌨️", "condition": "snow_showers", "indoor_needed": True},
        
        # Thunderstorm
        95: {"description": "Thunderstorm", "icon": "⛈️", "condition": "thunderstorm", "indoor_needed": True},
        96: {"description": "Thunderstorm with slight hail", "icon": "⛈️", "condition": "thunderstorm", "indoor_needed": True},
        99: {"description": "Thunderstorm with heavy hail", "icon": "⛈️", "condition": "thunderstorm", "indoor_needed": True},
    }
    
    return code_map.get(weather_code, {
        "description": "Unknown weather",
        "icon": "❓",
        "condition": "unknown",
        "indoor_needed": False
    })


def get_weather_forecast(
    lat: float,
    lon: float,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    forecast_days: int = 7
) -> Dict[str, Any]:
    """
    Get weather forecast for a location using Open-Meteo API.
    
    Args:
        lat: Latitude
        lon: Longitude
        start_date: Start date in YYYY-MM-DD format (optional, defaults to today)
        end_date: End date in YYYY-MM-DD format (optional)
        forecast_days: Number of forecast days (default: 7, max: 16)
    
    Returns:
        Dictionary with weather forecast data
    """
    try:
        # Build API URL
        url = f"{OPEN_METEO_API_URL}/forecast"
        
        # Prepare parameters
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "temperature_2m,precipitation_probability,weather_code",
            "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_probability_max,precipitation_sum",
            "timezone": "auto",
            "forecast_days": min(forecast_days, 16)  # Max 16 days for free tier
        }
        
        # Add date range if specified
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date
        
        logger.info(f"Fetching weather forecast for ({lat}, {lon}), forecast_days={params['forecast_days']}")
        
        # Make request
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Parse daily forecasts
        daily_forecasts = []
        if "daily" in data:
            daily_data = data["daily"]
            times = daily_data.get("time", [])
            weathercodes = daily_data.get("weathercode", [])
            temp_max = daily_data.get("temperature_2m_max", [])
            temp_min = daily_data.get("temperature_2m_min", [])
            precip_prob = daily_data.get("precipitation_probability_max", [])
            precip_sum = daily_data.get("precipitation_sum", [])
            
            for i in range(len(times)):
                weather_code = weathercodes[i] if i < len(weathercodes) else 0
                weather_info = _parse_weather_code(weather_code)
                
                daily_forecasts.append({
                    "date": times[i],
                    "weather_code": weather_code,
                    "condition": weather_info["condition"],
                    "description": weather_info["description"],
                    "icon": weather_info["icon"],
                    "temperature_max": temp_max[i] if i < len(temp_max) else None,
                    "temperature_min": temp_min[i] if i < len(temp_min) else None,
                    "precipitation_probability": precip_prob[i] if i < len(precip_prob) else 0,
                    "precipitation_sum": precip_sum[i] if i < len(precip_sum) else 0,
                    "indoor_needed": weather_info["indoor_needed"]
                })
        
        result = {
            "latitude": data.get("latitude", lat),
            "longitude": data.get("longitude", lon),
            "timezone": data.get("timezone", "auto"),
            "daily": daily_forecasts,
            "source": "open-meteo"
        }
        
        logger.info(f"Successfully fetched weather forecast: {len(daily_forecasts)} days")
        return result
        
    except requests.RequestException as e:
        logger.error(f"Open-Meteo API request failed: {e}")
        return {
            "error": f"Failed to fetch weather forecast: {str(e)}",
            "latitude": lat,
            "longitude": lon,
            "daily": [],
            "source": "error"
        }
    except Exception as e:
        logger.error(f"Error parsing weather forecast: {e}", exc_info=True)
        return {
            "error": f"Error parsing weather forecast: {str(e)}",
            "latitude": lat,
            "longitude": lon,
            "daily": [],
            "source": "error"
        }


def get_weather_for_city(
    city: str,
    country: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    forecast_days: int = 7
) -> Dict[str, Any]:
    """
    Get weather forecast for a city by name.
    
    Args:
        city: City name
        country: Optional country name for better geocoding
        start_date: Start date in YYYY-MM-DD format (optional)
        end_date: End date in YYYY-MM-DD format (optional)
        forecast_days: Number of forecast days (default: 7)
    
    Returns:
        Dictionary with weather forecast data
    """
    try:
        # Get city coordinates
        coords = get_city_coordinates(city, country=country)
        lat = coords["lat"]
        lon = coords["lon"]
        
        # Get weather forecast
        return get_weather_forecast(
            lat=lat,
            lon=lon,
            start_date=start_date,
            end_date=end_date,
            forecast_days=forecast_days
        )
        
    except Exception as e:
        logger.error(f"Failed to get weather for city '{city}': {e}")
        return {
            "error": f"Failed to get weather for city '{city}': {str(e)}",
            "city": city,
            "daily": [],
            "source": "error"
        }


def get_weather_for_dates(
    city: str,
    travel_dates: List[str],
    country: Optional[str] = None
) -> Dict[str, Dict[str, Any]]:
    """
    Get weather forecast for specific travel dates.
    
    Args:
        city: City name
        travel_dates: List of dates in YYYY-MM-DD format
        country: Optional country name
    
    Returns:
        Dictionary mapping date to weather data: {date: weather_info}
    """
    if not travel_dates:
        return {}
    
    try:
        # Get city coordinates
        coords = get_city_coordinates(city, country=country)
        lat = coords["lat"]
        lon = coords["lon"]
        
        # Get start and end dates
        start_date = travel_dates[0]
        end_date = travel_dates[-1]
        
        # Get weather forecast for the date range
        forecast = get_weather_forecast(
            lat=lat,
            lon=lon,
            start_date=start_date,
            end_date=end_date,
            forecast_days=len(travel_dates)
        )
        
        # Map dates to weather data
        weather_by_date = {}
        if "daily" in forecast:
            for daily_data in forecast["daily"]:
                date = daily_data.get("date")
                if date in travel_dates:
                    weather_by_date[date] = daily_data
        
        return weather_by_date
        
    except Exception as e:
        logger.error(f"Failed to get weather for dates: {e}")
        return {}


def get_weather_summary_for_day(weather_data: Optional[Dict[str, Any]]) -> str:
    """
    Get a human-readable weather summary for a single day.
    
    Args:
        weather_data: Weather data dictionary for a day (from daily forecast)
    
    Returns:
        Summary string (e.g., "☀️ Clear sky, 75°F / 60°F, 10% chance of rain")
    """
    if not weather_data or "error" in weather_data:
        return "Weather information unavailable"
    
    icon = weather_data.get("icon", "☁️")
    description = weather_data.get("description", "Unknown")
    temp_max = weather_data.get("temperature_max")
    temp_min = weather_data.get("temperature_min")
    precip_prob = weather_data.get("precipitation_probability", 0)
    
    parts = [f"{icon} {description}"]
    
    if temp_max is not None and temp_min is not None:
        # Convert Celsius to Fahrenheit for display (Open-Meteo returns Celsius)
        temp_max_f = (temp_max * 9/5) + 32
        temp_min_f = (temp_min * 9/5) + 32
        parts.append(f"{temp_max_f:.0f}°F / {temp_min_f:.0f}°F")
    
    if precip_prob and precip_prob > 0:
        parts.append(f"{precip_prob}% chance of rain")
    
    return ", ".join(parts)
