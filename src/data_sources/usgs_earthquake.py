import requests
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from .base import BaseDataSource


class USGSEarthquakeClient(BaseDataSource):
    
    def __init__(self):
        super().__init__(base_url="https://earthquake.usgs.gov/fdsnws/event/1")
    
    def health_check(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/version", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        return self.get_earthquakes(**kwargs)
    
    def get_earthquakes(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        min_magnitude: float = 2.5,
        max_magnitude: Optional[float] = None,
        min_latitude: Optional[float] = None,
        max_latitude: Optional[float] = None,
        min_longitude: Optional[float] = None,
        max_longitude: Optional[float] = None,
        limit: int = 100,
        order_by: str = "time"
    ) -> Dict[str, Any]:
        if not start_time:
            start_time = datetime.utcnow() - timedelta(days=7)
        if not end_time:
            end_time = datetime.utcnow()
        
        params = {
            "format": "geojson",
            "starttime": start_time.strftime("%Y-%m-%d"),
            "endtime": end_time.strftime("%Y-%m-%d"),
            "minmagnitude": min_magnitude,
            "orderby": order_by,
            "limit": limit
        }
        
        if max_magnitude:
            params["maxmagnitude"] = max_magnitude
        if min_latitude:
            params["minlatitude"] = min_latitude
        if max_latitude:
            params["maxlatitude"] = max_latitude
        if min_longitude:
            params["minlongitude"] = min_longitude
        if max_longitude:
            params["maxlongitude"] = max_longitude
        
        response = requests.get(f"{self.base_url}/query", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_significant_earthquakes(self, days: int = 30) -> Dict[str, Any]:
        start_time = datetime.utcnow() - timedelta(days=days)
        return self.get_earthquakes(start_time=start_time, min_magnitude=5.0)
    
    def get_earthquakes_near_location(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 100,
        days: int = 30
    ) -> Dict[str, Any]:
        start_time = datetime.utcnow() - timedelta(days=days)
        params = {
            "format": "geojson",
            "starttime": start_time.strftime("%Y-%m-%d"),
            "latitude": latitude,
            "longitude": longitude,
            "maxradiuskm": radius_km,
            "orderby": "time"
        }
        
        response = requests.get(f"{self.base_url}/query", params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_real_time_feed(self, timeframe: str = "day", magnitude: str = "2.5") -> Dict[str, Any]:
        valid_timeframes = ["hour", "day", "week", "month"]
        valid_magnitudes = ["significant", "4.5", "2.5", "1.0", "all"]
        
        if timeframe not in valid_timeframes:
            timeframe = "day"
        if magnitude not in valid_magnitudes:
            magnitude = "2.5"
        
        url = f"https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/{magnitude}_{timeframe}.geojson"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
