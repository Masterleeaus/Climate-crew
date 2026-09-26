from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING
from datetime import datetime

from langchain_core.tools import tool

from .base import BaseAgent
from ..data_sources.open_meteo import OpenMeteoClient

if TYPE_CHECKING:
    from ..memory import MemoryManager

meteo_client = OpenMeteoClient()


@tool
def get_flood_forecast(latitude: float, longitude: float) -> str:
    """Get flood forecast with river discharge data at coordinates."""
    try:
        data = meteo_client.get_flood_forecast(latitude, longitude)
        daily = data.get("daily", {})
        discharge = daily.get("river_discharge", [])
        
        if not discharge:
            return f"No flood data available for ({latitude}, {longitude})"
        
        max_d = max(discharge)
        min_d = min(discharge)
        risk = "High" if max_d > 1000 else "Moderate" if max_d > 500 else "Low"
        
        return f"Flood Forecast at ({latitude}, {longitude}): River discharge {min_d:.0f}-{max_d:.0f} m3/s, Flood Risk: {risk}"
    except Exception as e:
        return f"Flood data unavailable: {str(e)}"


@tool
def get_precipitation_forecast(latitude: float, longitude: float) -> str:
    """Get precipitation forecast for next 72 hours."""
    try:
        data = meteo_client.get_weather(latitude, longitude)
        hourly = data.get("hourly", {})
        precip = hourly.get("precipitation", [])[:72]
        
        total_24h = sum(precip[:24])
        total_72h = sum(precip)
        max_hourly = max(precip) if precip else 0
        
        risk = "High" if total_24h > 50 or max_hourly > 20 else "Moderate" if total_24h > 20 else "Low"
        
        return f"Precipitation at ({latitude}, {longitude}): 24h total {total_24h:.1f}mm, 72h total {total_72h:.1f}mm, Max hourly {max_hourly:.1f}mm, Flood Risk: {risk}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_marine_conditions(latitude: float, longitude: float) -> str:
    """Get marine/wave conditions for coastal locations."""
    try:
        data = meteo_client.get_marine_forecast(latitude, longitude)
        hourly = data.get("hourly", {})
        waves = hourly.get("wave_height", [])[:24]
        
        if not waves:
            return "Marine data unavailable for this location (may be inland)"
        
        max_wave = max(waves)
        avg_wave = sum(waves) / len(waves)
        
        return f"Marine Conditions at ({latitude}, {longitude}): Max wave height {max_wave:.1f}m, Avg wave height {avg_wave:.1f}m"
    except Exception as e:
        return f"Marine data unavailable: {str(e)}"


class FloodAgent(BaseAgent):
    
    def __init__(self, google_api_key: Optional[str] = None, memory_manager: Optional['MemoryManager'] = None):
        super().__init__("FloodAgent", google_api_key, memory_manager=memory_manager)
    
    def get_tools(self) -> List[Callable]:
        return [get_flood_forecast, get_precipitation_forecast, get_marine_conditions]
    
    def get_system_prompt(self) -> str:
        return """You are a Flood monitoring agent. Help users understand flood risks and precipitation.

You have these tools:
- get_flood_forecast: Get river discharge and flood risk at coordinates
- get_precipitation_forecast: Get 72-hour precipitation forecast
- get_marine_conditions: Get wave heights for coastal areas

- get_marine_conditions: Get wave heights for coastal areas

STRATEGY:
1. If user gives coordinates:
   - Call `get_flood_forecast` AND `get_precipitation_forecast` concurrently.
   - Do NOT ask for permission. JUST CHECK THE DATA.
2. Report the risk levels.

Flood risk factors:
- Heavy rain (>50mm/24h) = High flood risk
- High river discharge (>1000 m3/s) = Major flooding possible
- Coastal storms with high waves = Storm surge risk

Provide evacuation recommendations for high-risk situations."""
    
    def get_alerts(self, locations: List[tuple] = None, threshold: float = 50) -> List[Dict]:
        locations = locations or [(28.6139, 77.2090)]
        alerts = []
        for lat, lon in locations:
            try:
                data = meteo_client.get_weather(lat, lon)
                precip = data.get("hourly", {}).get("precipitation", [])[:24]
                total = sum(precip)
                if total > threshold:
                    alerts.append({
                        "type": "flood_risk",
                        "location": {"lat": lat, "lon": lon},
                        "precipitation_24h": round(total, 1),
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except:
                pass
        return alerts
