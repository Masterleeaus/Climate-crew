from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING
from datetime import datetime

from langchain_core.tools import tool

from .base import BaseAgent
from ..data_sources.open_meteo import OpenMeteoClient

if TYPE_CHECKING:
    from ..memory import MemoryManager

meteo_client = OpenMeteoClient()


@tool
def detect_heat_wave(latitude: float, longitude: float) -> str:
    """Detect heat wave conditions at a location. A heat wave is 3+ days above 35°C or 5°C above normal."""
    try:
        data = meteo_client.get_weather(latitude, longitude)
        hourly = data.get("hourly", {})
        temps = hourly.get("temperature_2m", [])[:168]  # 7 days
        
        if not temps:
            return "Temperature data unavailable"
        
        # Calculate daily max temperatures
        daily_max = []
        for i in range(0, len(temps), 24):
            day_temps = temps[i:i+24]
            if day_temps:
                daily_max.append(max(day_temps))
        
        # Check for heat wave (3+ consecutive days above 35°C)
        consecutive_hot = 0
        max_consecutive = 0
        for temp in daily_max:
            if temp >= 35:
                consecutive_hot += 1
                max_consecutive = max(max_consecutive, consecutive_hot)
            else:
                consecutive_hot = 0
        
        avg_temp = sum(temps) / len(temps)
        max_temp = max(temps)
        
        if max_consecutive >= 3:
            status = "HEAT WAVE DETECTED"
            risk = "High"
        elif max_temp >= 40:
            status = "EXTREME HEAT"
            risk = "High"
        elif max_temp >= 35:
            status = "HOT CONDITIONS"
            risk = "Moderate"
        else:
            status = "Normal"
            risk = "Low"
        
        return f"""Heat Wave Analysis at ({latitude}, {longitude}):
Status: {status}
Risk Level: {risk}
Current Period Max: {max_temp:.1f}°C
Average Temperature: {avg_temp:.1f}°C
Consecutive Hot Days (≥35°C): {max_consecutive}

Advisory: {"Stay hydrated, avoid outdoor activities during peak heat" if risk == "High" else "Normal conditions"}"""
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_weather_anomalies(latitude: float, longitude: float) -> str:
    """Identify weather anomalies at a location by analyzing current conditions."""
    try:
        data = meteo_client.get_weather(latitude, longitude)
        hourly = data.get("hourly", {})
        
        temps = hourly.get("temperature_2m", [])[:72]
        humidity = hourly.get("relative_humidity_2m", [])[:72]
        precip = hourly.get("precipitation", [])[:72]
        wind = hourly.get("wind_speed_10m", [])[:72]
        
        anomalies = []
        
        # Temperature anomalies
        if temps:
            max_temp = max(temps)
            min_temp = min(temps)
            temp_range = max_temp - min_temp
            
            if max_temp >= 42:
                anomalies.append(f"EXTREME HEAT: {max_temp:.1f}°C")
            if min_temp <= -10:
                anomalies.append(f"EXTREME COLD: {min_temp:.1f}°C")
            if temp_range >= 25:
                anomalies.append(f"HIGH TEMP VARIABILITY: {temp_range:.1f}°C range")
        
        # Precipitation anomalies
        if precip:
            total_precip = sum(precip)
            max_hourly = max(precip)
            
            if total_precip >= 100:
                anomalies.append(f"HEAVY RAINFALL: {total_precip:.1f}mm in 72h")
            if max_hourly >= 30:
                anomalies.append(f"INTENSE RAINFALL: {max_hourly:.1f}mm/hour")
        
        # Humidity anomalies
        if humidity:
            avg_humidity = sum(humidity) / len(humidity)
            if avg_humidity <= 20:
                anomalies.append(f"VERY DRY: {avg_humidity:.0f}% avg humidity")
        
        # Wind anomalies
        if wind:
            max_wind = max(wind)
            if max_wind >= 60:
                anomalies.append(f"STRONG WINDS: {max_wind:.0f} km/h")
            if max_wind >= 100:
                anomalies.append(f"STORM FORCE WINDS: {max_wind:.0f} km/h")
        
        if anomalies:
            return f"Weather Anomalies at ({latitude}, {longitude}):\n" + "\n".join(f"⚠️ {a}" for a in anomalies)
        else:
            return f"No significant weather anomalies detected at ({latitude}, {longitude})"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_extreme_events(latitude: float, longitude: float) -> str:
    """Check for extreme weather events at a location."""
    try:
        data = meteo_client.get_weather(latitude, longitude)
        hourly = data.get("hourly", {})
        
        temps = hourly.get("temperature_2m", [])[:168]
        precip = hourly.get("precipitation", [])[:168]
        wind = hourly.get("wind_speed_10m", [])[:168]
        
        events = []
        
        # Drought indicator (no rain for extended period)
        if precip and sum(precip) < 1:
            events.append({
                "type": "DRY_SPELL",
                "description": "Less than 1mm precipitation in 7 days",
                "severity": "Moderate"
            })
        
        # Flash flood potential
        if precip:
            for i in range(len(precip) - 6):
                six_hour_total = sum(precip[i:i+6])
                if six_hour_total >= 50:
                    events.append({
                        "type": "FLASH_FLOOD_RISK",
                        "description": f"50mm+ rainfall in 6 hours ({six_hour_total:.1f}mm)",
                        "severity": "High"
                    })
                    break
        
        # Storm detection
        if wind and max(wind) >= 80:
            events.append({
                "type": "STORM",
                "description": f"Wind speeds up to {max(wind):.0f} km/h",
                "severity": "High" if max(wind) >= 100 else "Moderate"
            })
        
        # Cold snap
        if temps and min(temps) <= 0:
            events.append({
                "type": "COLD_SNAP",
                "description": f"Temperature dropping to {min(temps):.1f}°C",
                "severity": "Moderate"
            })
        
        if events:
            response = f"Extreme Events at ({latitude}, {longitude}):\n"
            for event in events:
                response += f"🚨 {event['type']} ({event['severity']}): {event['description']}\n"
            return response
        else:
            return f"No extreme weather events detected at ({latitude}, {longitude})"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_climate_summary(latitude: float, longitude: float) -> str:
    """Get a comprehensive climate summary for a location."""
    try:
        weather = meteo_client.get_weather(latitude, longitude)
        air_quality = meteo_client.get_air_quality(latitude, longitude)
        
        hourly_w = weather.get("hourly", {})
        hourly_a = air_quality.get("hourly", {})
        
        temps = hourly_w.get("temperature_2m", [])[:24]
        humidity = hourly_w.get("relative_humidity_2m", [])[:24]
        precip = hourly_w.get("precipitation", [])[:24]
        wind = hourly_w.get("wind_speed_10m", [])[:24]
        pm25 = hourly_a.get("pm2_5", [])[:24]
        
        def safe_avg(lst):
            return sum(lst) / len(lst) if lst else 0
        
        return f"""Climate Summary for ({latitude}, {longitude}):

Temperature: {temps[0]:.1f}°C (24h range: {min(temps):.1f}-{max(temps):.1f}°C)
Humidity: {humidity[0]:.0f}% (Avg: {safe_avg(humidity):.0f}%)
Precipitation (24h): {sum(precip):.1f}mm
Wind: {wind[0]:.0f} km/h (Max: {max(wind):.0f} km/h)
PM2.5: {pm25[0] if pm25 else 'N/A'} µg/m³"""
    except Exception as e:
        return f"Error: {str(e)}"


class ClimateAnomalyAgent(BaseAgent):
    
    def __init__(self, google_api_key: Optional[str] = None, memory_manager: Optional['MemoryManager'] = None):
        super().__init__("ClimateAnomalyAgent", google_api_key, memory_manager=memory_manager)
    
    def get_tools(self) -> List[Callable]:
        return [detect_heat_wave, get_weather_anomalies, get_extreme_events, get_climate_summary]
    
    def get_system_prompt(self) -> str:
        return """You are a Climate Anomaly Detection agent. Help users understand unusual weather patterns.

You have these tools:
- detect_heat_wave: Check for heat wave conditions (3+ days ≥35°C)
- get_weather_anomalies: Identify unusual temperature, rain, humidity, wind
- get_extreme_events: Detect storms, droughts, floods, cold snaps
- get_climate_summary: Get comprehensive weather overview

Climate anomaly thresholds:
- Heat wave: 3+ consecutive days ≥35°C
- Extreme heat: Single day ≥42°C
- Heavy rainfall: 100mm+ in 72 hours
- Flash flood risk: 50mm+ in 6 hours
- Storm: Winds ≥80 km/h

Provide actionable safety recommendations for detected anomalies."""
    
    def get_alerts(self, locations: List[tuple] = None, temp_threshold: float = 40) -> List[Dict]:
        """Check for climate anomaly alerts."""
        locations = locations or [(28.6139, 77.2090), (19.0760, 72.8777)]  # Delhi, Mumbai
        alerts = []
        
        for lat, lon in locations:
            try:
                data = meteo_client.get_weather(lat, lon)
                temps = data.get("hourly", {}).get("temperature_2m", [])[:24]
                
                if temps and max(temps) >= temp_threshold:
                    alerts.append({
                        "type": "extreme_heat",
                        "location": {"lat": lat, "lon": lon},
                        "max_temp": max(temps),
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except:
                pass
        
        return alerts
