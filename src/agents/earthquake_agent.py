from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING
from datetime import datetime, timedelta

from langchain_core.tools import tool

from .base import BaseAgent
from ..data_sources.usgs_earthquake import USGSEarthquakeClient

if TYPE_CHECKING:
    from ..memory import MemoryManager

usgs_client = USGSEarthquakeClient()


@tool
def get_recent_earthquakes(min_magnitude: float = 4.5) -> str:
    """Get recent earthquakes from the past week. Specify minimum magnitude."""
    try:
        data = usgs_client.get_real_time_feed(timeframe="week", magnitude=str(min_magnitude))
        features = data.get("features", [])[:10]
        
        result = f"Recent M{min_magnitude}+ earthquakes (past week):\n"
        for eq in features:
            props = eq["properties"]
            result += f"- M{props.get('mag')} at {props.get('place')}\n"
        result += f"\nTotal: {len(data.get('features', []))} earthquakes"
        return result
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_significant_earthquakes() -> str:
    """Get significant earthquakes from the past 30 days."""
    try:
        data = usgs_client.get_significant_earthquakes(days=30)
        features = data.get("features", [])
        
        result = f"Significant earthquakes (past 30 days):\n"
        for eq in features[:10]:
            props = eq["properties"]
            time_str = datetime.fromtimestamp(props.get("time", 0) / 1000).strftime("%Y-%m-%d")
            result += f"- M{props.get('mag')} at {props.get('place')} on {time_str}\n"
        result += f"\nTotal significant: {len(features)}"
        return result
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_earthquakes_near_location(latitude: float, longitude: float, radius_km: float = 100) -> str:
    """Get earthquakes near a specific location within radius."""
    try:
        data = usgs_client.get_earthquakes_near_location(latitude, longitude, radius_km, days=30)
        features = data.get("features", [])
        
        result = f"Earthquakes within {radius_km}km of ({latitude}, {longitude}):\n"
        for eq in features[:10]:
            props = eq["properties"]
            result += f"- M{props.get('mag')} at {props.get('place')}\n"
        result += f"\nTotal: {len(features)}"
        return result
    except Exception as e:
        return f"Error: {str(e)}"


@tool  
def get_realtime_earthquake_feed(timeframe: str = "day") -> str:
    """Get real-time earthquake feed. Timeframe: hour, day, week, or month."""
    try:
        data = usgs_client.get_real_time_feed(timeframe=timeframe, magnitude="4.5")
        features = data.get("features", [])[:10]
        
        result = f"Real-time earthquakes (past {timeframe}):\n"
        for eq in features:
            props = eq["properties"]
            result += f"- M{props.get('mag')} at {props.get('place')}\n"
        return result
    except Exception as e:
        return f"Error: {str(e)}"


class EarthquakeAgent(BaseAgent):
    
    def __init__(self, google_api_key: Optional[str] = None, memory_manager: Optional['MemoryManager'] = None):
        super().__init__("EarthquakeAgent", google_api_key, memory_manager=memory_manager)
    
    def get_tools(self) -> List[Callable]:
        return [get_recent_earthquakes, get_significant_earthquakes, get_earthquakes_near_location, get_realtime_earthquake_feed]
    
    def get_system_prompt(self) -> str:
        return """You are an Earthquake monitoring agent. Help users understand seismic activity.

You have these tools:
- get_recent_earthquakes: Get earthquakes from past week with min magnitude
- get_significant_earthquakes: Get major earthquakes from past 30 days
- get_earthquakes_near_location: Get earthquakes near specific coordinates (Default radius: 500km)
- get_realtime_earthquake_feed: Get real-time feed (hour/day/week/month)

STRATEGY:
1. If the user provides coordinates:
   - Call `get_earthquakes_near_location` with a DEFAULT radius of 500km (earthquakes are rare).
   - Do NOT ask "What radius would you like?". JUST CHECK 500km.
2. Report any findings immediately.
3. If no earthquakes are found, say so clearly.

Context magnitudes:
- M3-3.9: Minor - Often felt, rarely causes damage
- M4-4.9: Light - Noticeable shaking, minor damage possible
- M5-5.9: Moderate - Can cause damage to weak structures
- M6-6.9: Strong - Destructive in populated areas
- M7+: Major/Great - Causes serious damage over large areas"""
    
    def get_alerts(self, min_magnitude: float = 6.0) -> List[Dict]:
        alerts = []
        try:
            data = usgs_client.get_real_time_feed(timeframe="day", magnitude="4.5")
            for eq in data.get("features", []):
                props = eq["properties"]
                if props.get("mag", 0) >= min_magnitude:
                    alerts.append({
                        "type": "earthquake",
                        "magnitude": props.get("mag"),
                        "place": props.get("place"),
                        "timestamp": datetime.fromtimestamp(props.get("time", 0) / 1000).isoformat()
                    })
        except:
            pass
        return alerts


