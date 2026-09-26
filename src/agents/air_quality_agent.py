from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING
from datetime import datetime

from langchain_core.tools import tool

from .base import BaseAgent
from ..data_sources.openaq import WAQIClient
from ..data_sources.open_meteo import OpenMeteoClient

if TYPE_CHECKING:
    from ..memory import MemoryManager

waqi_client = WAQIClient()
meteo_client = OpenMeteoClient()


@tool
def get_city_aqi(city: str) -> str:
    """Get the current AQI (Air Quality Index) for a city by name."""
    try:
        data = waqi_client.get_city_feed(city.strip())
        if data.get("status") == "ok":
            aqi = data["data"].get("aqi", "N/A")
            name = data["data"].get("city", {}).get("name", city)
            dom = data["data"].get("dominentpol", "unknown")
            
            if aqi <= 50: level = "Good"
            elif aqi <= 100: level = "Moderate"
            elif aqi <= 150: level = "Unhealthy for Sensitive Groups"
            elif aqi <= 200: level = "Unhealthy"
            elif aqi <= 300: level = "Very Unhealthy"
            else: level = "Hazardous"
            
            return f"City: {name}, AQI: {aqi}, Level: {level}, Dominant Pollutant: {dom}"
        return f"Could not fetch data for {city}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_location_aqi(latitude: float, longitude: float) -> str:
    """Get the current AQI at specific latitude/longitude coordinates."""
    try:
        data = waqi_client.get_by_coordinates(latitude, longitude)
        if data.get("status") == "ok":
            aqi = data["data"].get("aqi", "N/A")
            name = data["data"].get("city", {}).get("name", f"{latitude},{longitude}")
            return f"Location: {name}, AQI: {aqi}"
        return "Could not fetch data"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def search_air_quality_stations(keyword: str) -> str:
    """Search for air quality monitoring stations by keyword."""
    try:
        stations = waqi_client.search_stations(keyword.strip())
        if stations:
            result = f"Found {len(stations)} stations:\n"
            for s in stations[:5]:
                name = s.get("station", {}).get("name", "Unknown")
                aqi = s.get("aqi", "N/A")
                result += f"- {name}: AQI {aqi}\n"
            return result
        return "No stations found"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_air_quality_forecast(latitude: float, longitude: float) -> str:
    """Get 24-hour air quality forecast for a location including PM2.5 and PM10 levels."""
    try:
        data = meteo_client.get_air_quality(latitude, longitude)
        hourly = data.get("hourly", {})
        pm25 = hourly.get("pm2_5", [])[:24]
        pm10 = hourly.get("pm10", [])[:24]
        if pm25:
            return f"24h Forecast: PM2.5 range {min(pm25):.1f}-{max(pm25):.1f}, PM10 range {min(pm10):.1f}-{max(pm10):.1f}"
        return "Forecast unavailable"
    except Exception as e:
        return f"Error: {str(e)}"


class AirQualityAgent(BaseAgent):
    
    def __init__(self, google_api_key: Optional[str] = None, memory_manager: Optional['MemoryManager'] = None):
        super().__init__("AirQualityAgent", google_api_key, memory_manager=memory_manager)
    
    def get_tools(self) -> List[Callable]:
        return [get_city_aqi, get_location_aqi, search_air_quality_stations, get_air_quality_forecast]
    
    def get_system_prompt(self) -> str:
        return """You are an Air Quality monitoring agent. Help users understand air pollution levels.

You have these tools:
- get_city_aqi: Get current AQI for a city name
- get_location_aqi: Get AQI at specific lat/lon coordinates
- search_air_quality_stations: Search for monitoring stations
- get_air_quality_forecast: Get 24h air quality forecast

STRATEGY:
1. If user gives coordinates:
   - Call `get_location_aqi` IMMEDIATELY.
   - Call `get_air_quality_forecast` for that location.
   - Do NOT ask "Would you like to check the AQI?". JUST CHECK IT.
2. Provide health recommendations based on the findings.

Always use tools to get real data. Provide health recommendations based on AQI levels:
- 0-50: Good - Air quality is satisfactory
- 51-100: Moderate - Acceptable, but sensitive individuals may experience issues
- 101-150: Unhealthy for Sensitive Groups - Limit outdoor activity if sensitive
- 151-200: Unhealthy - Everyone may experience health effects
- 201-300: Very Unhealthy - Avoid outdoor activities
- 300+: Hazardous - Stay indoors"""
    
    def get_alerts(self, cities: List[str] = None, threshold: int = 150) -> List[Dict]:
        cities = cities or ["Delhi", "Mumbai", "Bangalore"]
        alerts = []
        for city in cities:
            try:
                data = waqi_client.get_city_feed(city)
                if data.get("status") == "ok":
                    aqi = data["data"].get("aqi", 0)
                    if isinstance(aqi, int) and aqi > threshold:
                        alerts.append({
                            "type": "air_quality",
                            "city": city,
                            "aqi": aqi,
                            "timestamp": datetime.utcnow().isoformat()
                        })
            except:
                pass
        return alerts
