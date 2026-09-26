from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING
from datetime import datetime

from langchain_core.tools import tool

from .base import BaseAgent
from ..data_sources.noaa_ocean import NOAAOceanClient, CoralReefWatchClient, OpenMeteoMarineClient

if TYPE_CHECKING:
    from ..memory import MemoryManager

noaa_client = NOAAOceanClient()
coral_client = CoralReefWatchClient()
marine_client = OpenMeteoMarineClient()


@tool
def get_sea_level_trend(station_id: str = "8518750") -> str:
    """Get sea level trend at a NOAA tide station. Default is NYC Battery. 
    Common stations: 8518750 (NYC), 9414290 (San Francisco), 8723214 (Key West)."""
    try:
        data = noaa_client.get_sea_level_trend(station_id)
        if "error" in data:
            return f"Error: {data['error']}"
        
        if isinstance(data, dict) and "sltrends" in data:
            trend = data["sltrends"]
            rate = trend.get("linearTrend", "N/A")
            station = trend.get("station", station_id)
            return f"Sea Level Trend at Station {station}: {rate} mm/year"
        return f"Data retrieved: {data}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_water_level(station_id: str) -> str:
    """Get current water level observations at a NOAA tide station."""
    try:
        data = noaa_client.get_water_level(station_id, hours=6)
        if "error" in data:
            return f"Error: {data['error']}"
        
        observations = data.get("data", [])
        if observations:
            latest = observations[-1]
            value = latest.get("v", "N/A")
            time = latest.get("t", "N/A")
            return f"Water Level at {station_id}: {value}m (MLLW) at {time}"
        return "No observations available"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_coral_bleaching_status(region: str) -> str:
    """Get coral bleaching risk for a region.
    Regions: great_barrier_reef, caribbean, hawaii, florida_keys, red_sea.
    You MUST specify a region."""
    try:
        status = coral_client.get_bleaching_status()
        region_info = coral_client.get_region_status(region)
        
        if "error" in region_info:
            return f"Error: {region_info['error']}"
        
        return f"""Coral Bleaching Status for {region_info.get('region', region)}:
Location: {region_info.get('coordinates', {})}
Alert Levels: {status.get('alert_levels', {})}
Data source: NOAA Coral Reef Watch
Monitoring URL: {status.get('data_url', 'N/A')}"""
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_ocean_conditions(latitude: float, longitude: float) -> str:
    """Get ocean conditions (SST, waves, currents) at a location."""
    try:
        data = marine_client.get_ocean_conditions(latitude, longitude)
        if "error" in data:
            return f"Error: {data['error']}"
        
        hourly = data.get("hourly", {})
        sst = hourly.get("sea_surface_temperature", [])
        waves = hourly.get("wave_height", [])
        currents = hourly.get("ocean_current_velocity", [])
        
        current_sst = sst[0] if sst else "N/A"
        current_wave = waves[0] if waves else "N/A"
        current_velocity = currents[0] if currents else "N/A"
        max_wave_7d = max(waves) if waves else "N/A"
        
        return f"""Ocean Conditions at ({latitude}, {longitude}):
Sea Surface Temperature: {current_sst}°C
Wave Height: {current_wave}m (Max 7-day: {max_wave_7d}m)
Current Velocity: {current_velocity}m/s"""
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_sea_surface_temperature(latitude: float, longitude: float) -> str:
    """Get sea surface temperature forecast for a location."""
    try:
        data = marine_client.get_sea_surface_temperature(latitude, longitude)
        if "error" in data:
            return f"Error: {data['error']}"
        
        hourly = data.get("hourly", {})
        sst = hourly.get("sea_surface_temperature", [])[:24]
        
        if sst:
            min_sst = min(sst)
            max_sst = max(sst)
            avg_sst = sum(sst) / len(sst)
            return f"SST at ({latitude}, {longitude}): Current {sst[0]}°C, 24h range {min_sst}-{max_sst}°C, Avg {avg_sst:.1f}°C"
        return "SST data unavailable for this location"
    except Exception as e:
        return f"Error: {str(e)}"


class OceanAgent(BaseAgent):
    
    def __init__(self, google_api_key: Optional[str] = None, memory_manager: Optional['MemoryManager'] = None):
        super().__init__("OceanAgent", google_api_key, memory_manager=memory_manager)
    
    def get_tools(self) -> List[Callable]:
        return [get_sea_level_trend, get_water_level, get_coral_bleaching_status, 
                get_ocean_conditions, get_sea_surface_temperature]
    
    def get_system_prompt(self) -> str:
        return """You are an Ocean and Marine monitoring agent. Help users understand ocean conditions and marine health.

- get_sea_surface_temperature: Get SST forecast at coordinates

STRATEGY:
1. If user gives coordinates:
   - Call `get_ocean_conditions` IMMEDIATELY.
   - If the tool returns "Error" or "N/A" (likely inland), REPORT THAT. Do NOT make up data about the Great Barrier Reef.
   - Only call `get_coral_bleaching_status` if the user explicitly asks for a specific reef region (e.g., Red Sea).
2. For specific regions (Red Sea, Caribbean), use `get_coral_bleaching_status(region="name")`.
3. Be direct: "No marine data available for this land-locked location" is a valid and helpful response.

Key insights to provide:
- Sea level rise impacts on coastal communities
- Coral bleaching risks from elevated SST (>1°C above normal = stress)
- Wave height safety for maritime activities
- Ocean current patterns for shipping and fishing"""
    
    def get_alerts(self, locations: List[tuple] = None) -> List[Dict]:
        """Check for ocean alerts at given locations."""
        locations = locations or [(25.0, -80.0)]  # Default: Florida Keys
        alerts = []
        
        for lat, lon in locations:
            try:
                data = marine_client.get_ocean_conditions(lat, lon)
                hourly = data.get("hourly", {})
                sst = hourly.get("sea_surface_temperature", [])
                waves = hourly.get("wave_height", [])
                
                if sst and max(sst[:24]) > 30:
                    alerts.append({
                        "type": "high_sst",
                        "location": {"lat": lat, "lon": lon},
                        "max_sst": max(sst[:24]),
                        "risk": "Coral bleaching risk",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                if waves and max(waves[:24]) > 4:
                    alerts.append({
                        "type": "high_waves",
                        "location": {"lat": lat, "lon": lon},
                        "max_wave": max(waves[:24]),
                        "risk": "Maritime safety warning",
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except:
                pass
        
        return alerts
