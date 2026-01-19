"""
Weather MCP Tool
Provides weather forecast functionality via Model Context Protocol.
"""

from .server import (
    get_weather_forecast_mcp,
    get_weather_for_city_mcp,
    get_weather_for_dates_mcp
)

__all__ = [
    "get_weather_forecast_mcp",
    "get_weather_for_city_mcp",
    "get_weather_for_dates_mcp"
]
