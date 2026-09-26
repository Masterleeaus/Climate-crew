"""
NOAA Ocean and Marine Data Sources
- Sea level trends from NOAA CO-OPS
- Coral bleaching alerts from NOAA Coral Reef Watch
- Ocean conditions from Open-Meteo Marine API
"""
import requests
from typing import Any, Dict, List, Optional
from .base import BaseDataSource


class NOAAOceanClient(BaseDataSource):
    """NOAA CO-OPS API for sea level and tide data."""
    
    def __init__(self):
        super().__init__(base_url="https://api.tidesandcurrents.noaa.gov")
    
    def health_check(self) -> bool:
        try:
            response = requests.get(
                f"{self.base_url}/mdapi/prod/webapi/stations.json",
                params={"type": "tidepredictions"},
                timeout=15
            )
            return response.status_code == 200
        except:
            return False
    
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        return self.get_sea_level_trend(kwargs.get("station_id", "8518750"))
    
    def get_sea_level_trend(self, station_id: str = "8518750") -> Dict:
        """Get sea level trend for a NOAA station. Default: NYC Battery."""
        try:
            response = requests.get(
                f"{self.base_url}/dpapi/prod/webapi/product/sltrends.json",
                params={"station": station_id},
                timeout=15
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"Status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_water_level(self, station_id: str, hours: int = 24) -> Dict:
        """Get recent water level observations."""
        try:
            response = requests.get(
                f"{self.base_url}/api/prod/datagetter",
                params={
                    "station": station_id,
                    "product": "water_level",
                    "datum": "MLLW",
                    "units": "metric",
                    "time_zone": "gmt",
                    "format": "json",
                    "range": hours
                },
                timeout=15
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"Status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_stations_by_state(self, state: str) -> List[Dict]:
        """Get tide stations in a US state."""
        try:
            response = requests.get(
                f"{self.base_url}/mdapi/prod/webapi/stations.json",
                params={"type": "tidepredictions", "state": state.upper()},
                timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("stations", [])
            return []
        except:
            return []


class CoralReefWatchClient(BaseDataSource):
    """NOAA Coral Reef Watch for bleaching alerts."""
    
    def __init__(self):
        super().__init__(base_url="https://coralreefwatch.noaa.gov")
    
    def health_check(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/product/5km/", timeout=15)
            return response.status_code == 200
        except:
            return False
    
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        return self.get_bleaching_status()
    
    def get_bleaching_status(self) -> Dict:
        """Get current global coral bleaching status."""
        return {
            "source": "NOAA Coral Reef Watch",
            "product": "5km Bleaching Alert Area",
            "alert_levels": {
                0: "No Stress",
                1: "Watch - Bleaching possible",
                2: "Warning - Bleaching likely",
                3: "Alert Level 1 - Bleaching expected",
                4: "Alert Level 2 - Severe bleaching expected"
            },
            "data_url": f"{self.base_url}/product/5km/index.php",
            "note": "For specific region data, use NOAA Coral Reef Watch virtual stations"
        }
    
    def get_region_status(self, region: str) -> Dict:
        """Get bleaching status for a specific region."""
        regions = {
            "great_barrier_reef": {"lat": -18.0, "lon": 147.0, "name": "Great Barrier Reef"},
            "caribbean": {"lat": 17.0, "lon": -65.0, "name": "Caribbean"},
            "hawaii": {"lat": 20.0, "lon": -156.0, "name": "Hawaii"},
            "florida_keys": {"lat": 24.5, "lon": -81.5, "name": "Florida Keys"},
            "red_sea": {"lat": 22.0, "lon": 38.0, "name": "Red Sea"}
        }
        region_info = regions.get(region.lower().replace(" ", "_"))
        if region_info:
            return {
                "region": region_info["name"],
                "coordinates": {"lat": region_info["lat"], "lon": region_info["lon"]},
                "monitoring_url": f"{self.base_url}/product/5km/index.php"
            }
        return {"error": f"Unknown region: {region}. Available: {list(regions.keys())}"}


class OpenMeteoMarineClient(BaseDataSource):
    """Open-Meteo Marine API for ocean conditions."""
    
    def __init__(self):
        super().__init__(base_url="https://marine-api.open-meteo.com/v1/marine")
    
    def health_check(self) -> bool:
        try:
            response = requests.get(
                self.base_url,
                params={"latitude": 0, "longitude": 0, "hourly": "wave_height"},
                timeout=15
            )
            return response.status_code == 200
        except:
            return False
    
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        lat = kwargs.get("latitude", 0)
        lon = kwargs.get("longitude", 0)
        return self.get_ocean_conditions(lat, lon)
    
    def get_ocean_conditions(self, latitude: float, longitude: float) -> Dict:
        """Get comprehensive ocean conditions at a location."""
        try:
            response = requests.get(
                self.base_url,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "hourly": "wave_height,wave_direction,wave_period,ocean_current_velocity,ocean_current_direction,sea_surface_temperature",
                    "forecast_days": 7
                },
                timeout=15
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"Status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_sea_surface_temperature(self, latitude: float, longitude: float) -> Dict:
        """Get sea surface temperature forecast."""
        try:
            response = requests.get(
                self.base_url,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "hourly": "sea_surface_temperature",
                    "forecast_days": 7
                },
                timeout=15
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"Status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
