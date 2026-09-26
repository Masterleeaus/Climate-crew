from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING
from datetime import datetime

from langchain_core.tools import tool

from .base import BaseAgent
from ..data_sources.nasa_firms import NASAFIRMSClient
from ..data_sources.open_meteo import OpenMeteoClient

if TYPE_CHECKING:
    from ..memory import MemoryManager

firms_client = NASAFIRMSClient()
meteo_client = OpenMeteoClient()


@tool
def assess_fire_risk(latitude: float, longitude: float) -> str:
    """Assess wildfire risk at a location based on weather conditions."""
    try:
        weather = meteo_client.get_weather(latitude, longitude)
        hourly = weather.get("hourly", {})
        
        temps = hourly.get("temperature_2m", [])[:24]
        humidity = hourly.get("relative_humidity_2m", [])[:24]
        wind = hourly.get("wind_speed_10m", [])[:24]
        precip = hourly.get("precipitation", [])[:24]
        
        avg_temp = sum(temps) / len(temps) if temps else 0
        avg_hum = sum(humidity) / len(humidity) if humidity else 100
        max_wind = max(wind) if wind else 0
        total_precip = sum(precip) if precip else 0
        
        risk = 0
        if avg_temp > 35: risk += 30
        elif avg_temp > 30: risk += 20
        if avg_hum < 30: risk += 30
        elif avg_hum < 50: risk += 15
        if max_wind > 40: risk += 25
        elif max_wind > 20: risk += 10
        if total_precip < 1: risk += 15
        
        level = "Extreme" if risk >= 75 else "High" if risk >= 50 else "Moderate" if risk >= 25 else "Low"
        
        return f"Fire Risk at ({latitude}, {longitude}): Score {risk}/100, Level: {level}. Temp: {avg_temp:.1f}C, Humidity: {avg_hum:.0f}%, Max Wind: {max_wind:.0f}km/h, Rain 24h: {total_precip:.1f}mm"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_active_fires(country_code: str) -> str:
    """Get active fire detections for a country. Requires NASA FIRMS API key."""
    if not firms_client.api_key:
        return "NASA FIRMS API key required. Get free key at: https://firms.modaps.eosdis.nasa.gov/api/"
    try:
        fires = firms_client.get_fires_by_country(country_code.upper(), days=1)
        high_conf = [f for f in fires if f.get("confidence") in ["high", "h", "nominal", "n"]]
        return f"Active fires in {country_code}: {len(fires)} total, {len(high_conf)} high confidence"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_weather_conditions(latitude: float, longitude: float) -> str:
    """Get current weather conditions at a location."""
    try:
        data = meteo_client.get_weather(latitude, longitude)
        hourly = data.get("hourly", {})
        temps = hourly.get("temperature_2m", [])[:6]
        humidity = hourly.get("relative_humidity_2m", [])[:6]
        wind = hourly.get("wind_speed_10m", [])[:6]
        return f"Weather at ({latitude}, {longitude}): Temp {temps[0] if temps else 'N/A'}C, Humidity {humidity[0] if humidity else 'N/A'}%, Wind {wind[0] if wind else 'N/A'}km/h"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_fire_map(country_code: str) -> str:
    """Generate a visual map of active fires for a country. Returns file path of the map."""
    if not firms_client.api_key:
        return "NASA FIRMS API key required."
    try:
        # 1. Fetch data
        fires = firms_client.get_fires_by_country(country_code.upper(), days=1)
        if not fires:
            return f"No active fires found in {country_code}."
        
        # 2. Generate Map
        filename = f"fire_map_{country_code}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        output_path = f"artifacts/{filename}"
        
        firms_client.generate_fire_map(fires, output_path)
        
        return f"Map generated successfully at: {output_path} (Contains {len(fires)} fire points)"
    except Exception as e:
        return f"Error generating map: {str(e)}"

@tool
def get_fire_map_by_coordinates(latitude: float, longitude: float, radius_km: float = 50.0) -> str:
    """
    Generate a visual map of active fires for a specific location (radius in km). 
    Best for auditing specific project sites.
    Returns file path of the map.
    """
    if not firms_client.api_key:
        return "NASA FIRMS API key required."
    try:
        # 1. Fetch data
        # Note: firms_client.get_fire_data uses a slightly different signature/logic in our new file?
        # Let's check nasa_firms.py again. It has get_fires_by_bbox or just get_fires with area.
        # Wait, I see get_fire_data in my memory of writing it, but let's verify if I should use that or existing methods.
        # Existing `nasa_firms.py` has `get_fires_by_bbox`.
        
        # Calculate bbox from radius
        deg_radius = radius_km / 111.0
        west = longitude - deg_radius
        south = latitude - deg_radius
        east = longitude + deg_radius
        north = latitude + deg_radius
        
        fires = firms_client.get_fires_by_bbox(west, south, east, north, days=1)
        
        if not fires:
            return f"No active fires found within {radius_km}km of ({latitude}, {longitude})."
        
        # 2. Generate Map
        filename = f"fire_map_{latitude}_{longitude}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        output_path = f"artifacts/{filename}"
        
        firms_client.generate_fire_map(fires, output_path)
        
        return f"Map generated successfully at: {output_path} (Contains {len(fires)} fire points)"
    except Exception as e:
        return f"Error generating map: {str(e)}"


class WildfireAgent(BaseAgent):
    
    def __init__(self, firms_api_key: Optional[str] = None, google_api_key: Optional[str] = None, memory_manager: Optional['MemoryManager'] = None):
        super().__init__("WildfireAgent", google_api_key, memory_manager=memory_manager)
        if firms_api_key:
            firms_client.api_key = firms_api_key
    
    def get_tools(self) -> List[Callable]:
        return [assess_fire_risk, get_active_fires, get_weather_conditions, get_fire_map, get_fire_map_by_coordinates]
    
    def get_system_prompt(self) -> str:
        return """You are a Wildfire monitoring agent. Help users assess fire risk and track active fires.

You have these tools:
- assess_fire_risk: Assess wildfire risk at coordinates based on weather
- get_active_fires: Get active fire detections for a country (text summary)
- get_fire_map: Generate a visual MAP of active fires for a country (returns image path)
- get_fire_map_by_coordinates: Generate a visual MAP for a specific location (Default: 50km radius). BEST for project sites.
- get_weather_conditions: Get current weather at coordinates

STRATEGY:
1. If user gives coordinates:
   - Call `assess_fire_risk` to get weather/risk data.
   - AUTOMATICALLY call `get_fire_map_by_coordinates` with default 50km radius.
   - Do NOT ask for permission. JUST GENERATE THE MAP.
2. Report the risk level and map status clearly.

Fire risk factors:
- High temperature (>35C) + Low humidity (<30%) = Extreme risk
- Strong winds (>40km/h) spread fires rapidly
- No recent rain increases dry fuel load

Provide actionable safety recommendations based on risk levels.
When users ask for "visual proof" or "map", ALWAYS use get_fire_map or get_fire_map_by_coordinates."""
    
    def get_alerts(self, country: str = "USA") -> List[Dict]:
        if not firms_client.api_key:
            return []
        alerts = []
        try:
            fires = firms_client.get_fires_by_country(country, days=1)
            high_conf = [f for f in fires if f.get("confidence") in ["high", "h", "nominal"]]
            if len(high_conf) > 100:
                alerts.append({
                    "type": "wildfire",
                    "country": country,
                    "count": len(high_conf),
                    "timestamp": datetime.utcnow().isoformat()
                })
        except:
            pass
        return alerts
