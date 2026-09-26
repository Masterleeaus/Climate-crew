import requests
from typing import Any, Dict, List, Optional
from datetime import datetime
from .base import BaseDataSource


class OpenAQClient(BaseDataSource):
    
    def __init__(self, api_key: str):
        super().__init__(api_key=api_key, base_url="https://api.openaq.org/v3")
        if not api_key:
            raise ValueError("OpenAQ v3 requires API key. Get one free at: https://openaq.org")
        self.headers = {"X-API-Key": api_key}
    
    def health_check(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/countries", params={"limit": 1}, headers=self.headers, timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        return {"locations": self.get_locations(**kwargs)}

    def get_locations(self, country: Optional[str] = None, limit: int = 100, coordinates: Optional[tuple] = None, radius: int = 10000) -> List[Dict]:
        params = {"limit": limit}
        if country:
            params["countries_id"] = country
        if coordinates:
            params["coordinates"] = f"{coordinates[0]},{coordinates[1]}"
            params["radius"] = radius
        response = requests.get(f"{self.base_url}/locations", params=params, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])

    def get_location(self, location_id: int) -> Dict:
        response = requests.get(f"{self.base_url}/locations/{location_id}", headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [{}])[0]

    def get_countries(self, limit: int = 200) -> List[Dict]:
        response = requests.get(f"{self.base_url}/countries", params={"limit": limit}, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])

    def get_parameters(self, limit: int = 100) -> List[Dict]:
        response = requests.get(f"{self.base_url}/parameters", params={"limit": limit}, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])

    def get_instruments(self, limit: int = 100) -> List[Dict]:
        response = requests.get(f"{self.base_url}/instruments", params={"limit": limit}, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])

    def get_manufacturers(self, limit: int = 100) -> List[Dict]:
        response = requests.get(f"{self.base_url}/manufacturers", params={"limit": limit}, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])

    def get_providers(self, limit: int = 100) -> List[Dict]:
        response = requests.get(f"{self.base_url}/providers", params={"limit": limit}, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])

    def get_owners(self, limit: int = 100) -> List[Dict]:
        response = requests.get(f"{self.base_url}/owners", params={"limit": limit}, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])

    def get_sensors(self, location_id: int) -> List[Dict]:
        location = self.get_location(location_id)
        return location.get("sensors", [])

    def get_sensor_measurements(self, sensor_id: int, date_from: Optional[str] = None, date_to: Optional[str] = None, limit: int = 1000) -> List[Dict]:
        params = {"limit": limit}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        response = requests.get(f"{self.base_url}/sensors/{sensor_id}/measurements", params=params, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])

    def get_sensor_hours(self, sensor_id: int, date_from: Optional[str] = None, date_to: Optional[str] = None, limit: int = 1000) -> List[Dict]:
        params = {"limit": limit}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        response = requests.get(f"{self.base_url}/sensors/{sensor_id}/hours", params=params, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])

    def get_sensor_days(self, sensor_id: int, date_from: Optional[str] = None, date_to: Optional[str] = None, limit: int = 1000) -> List[Dict]:
        params = {"limit": limit}
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        response = requests.get(f"{self.base_url}/sensors/{sensor_id}/days", params=params, headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])

    def get_latest(self, location_id: int) -> List[Dict]:
        response = requests.get(f"{self.base_url}/locations/{location_id}/latest", headers=self.headers, timeout=30)
        response.raise_for_status()
        return response.json().get("results", [])


class WAQIClient(BaseDataSource):
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key or "demo", base_url="https://api.waqi.info")
    
    def health_check(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/feed/beijing/?token={self.api_key}", timeout=15)
            return response.status_code == 200 and response.json().get("status") == "ok"
        except:
            return False
    
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        return self.get_city_feed(**kwargs)
    
    def get_city_feed(self, city: str) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/feed/{city}/?token={self.api_key}", timeout=30)
        response.raise_for_status()
        return response.json()
    
    def get_by_coordinates(self, lat: float, lon: float) -> Dict[str, Any]:
        response = requests.get(f"{self.base_url}/feed/geo:{lat};{lon}/?token={self.api_key}", timeout=30)
        response.raise_for_status()
        return response.json()
    
    def search_stations(self, keyword: str) -> List[Dict[str, Any]]:
        response = requests.get(f"{self.base_url}/search/?keyword={keyword}&token={self.api_key}", timeout=30)
        response.raise_for_status()
        return response.json().get("data", [])
    
    def get_map_stations(self, lat1: float, lon1: float, lat2: float, lon2: float) -> List[Dict]:
        response = requests.get(f"{self.base_url}/map/bounds/?latlng={lat1},{lon1},{lat2},{lon2}&token={self.api_key}", timeout=30)
        response.raise_for_status()
        return response.json().get("data", [])
