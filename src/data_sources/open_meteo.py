import requests
from typing import Any, Dict, List, Optional
from datetime import datetime
from .base import BaseDataSource


class OpenMeteoClient(BaseDataSource):
    
    def __init__(self):
        super().__init__(base_url="https://api.open-meteo.com/v1")
    
    def health_check(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/forecast", params={"latitude": 0, "longitude": 0, "hourly": "temperature_2m"}, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        return self.get_weather(**kwargs)
    
    def get_weather(self, latitude: float, longitude: float, hourly: List[str] = None, daily: List[str] = None) -> Dict:
        params = {"latitude": latitude, "longitude": longitude}
        if hourly:
            params["hourly"] = ",".join(hourly)
        else:
            params["hourly"] = "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
        if daily:
            params["daily"] = ",".join(daily)
        response = requests.get(f"{self.base_url}/forecast", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_historical_weather(self, latitude: float, longitude: float, start_date: str, end_date: str, hourly: List[str] = None) -> Dict:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "start_date": start_date,
            "end_date": end_date
        }
        if hourly:
            params["hourly"] = ",".join(hourly)
        else:
            params["hourly"] = "temperature_2m,precipitation"
        response = requests.get("https://archive-api.open-meteo.com/v1/archive", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_air_quality(self, latitude: float, longitude: float) -> Dict:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "pm2_5,pm10,carbon_monoxide,nitrogen_dioxide,ozone,uv_index"
        }
        response = requests.get("https://air-quality-api.open-meteo.com/v1/air-quality", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_flood_forecast(self, latitude: float, longitude: float) -> Dict:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "daily": "river_discharge"
        }
        response = requests.get("https://flood-api.open-meteo.com/v1/flood", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_marine_forecast(self, latitude: float, longitude: float) -> Dict:
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": "wave_height,wave_direction,wave_period,ocean_current_velocity"
        }
        response = requests.get("https://marine-api.open-meteo.com/v1/marine", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
