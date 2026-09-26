"""
Climate TRACE API Client (v6)
Open data for greenhouse gas emissions tracking.
Covers 10 sectors, 67 sub-sectors, 745M+ emission sources.
API Docs: https://api.climatetrace.org/v6/swagger
"""
import requests
from typing import Any, Dict, List, Optional
from .base import BaseDataSource


class ClimateTraceClient(BaseDataSource):
    """Climate TRACE API v6 for emissions data."""
    
    def __init__(self):
        super().__init__(base_url="https://api.climatetrace.org/v6")
    
    def health_check(self) -> bool:
        try:
            # v6 uses /definitions/sectors endpoint
            response = requests.get(f"{self.base_url}/definitions/sectors", timeout=15)
            if response.status_code == 200:
                return True
            # Try assets endpoint as fallback
            response = requests.get(f"{self.base_url}/assets", params={"limit": 1}, timeout=15)
            return response.status_code == 200
        except:
            return False
    
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        country = kwargs.get("country", "USA")
        return self.get_country_emissions(country)
    
    def get_sectors(self) -> List[Dict]:
        """Get all emission sectors tracked by Climate TRACE."""
        try:
            response = requests.get(f"{self.base_url}/definitions/sectors", timeout=15)
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []
    
    def get_country_emissions(self, country_code: str, year: int = 2022) -> Dict:
        """Get total emissions for a country using country endpoint."""
        try:
            # v6 API uses /country/{iso3}/emissions
            response = requests.get(
                f"{self.base_url}/country/{country_code.upper()}/emissions",
                params={"year": year},
                timeout=15
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"Status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_sector_emissions(self, country_code: str, sector: str, year: int = 2022) -> Dict:
        """Get emissions by sector for a country."""
        try:
            response = requests.get(
                f"{self.base_url}/country/{country_code.upper()}/emissions",
                params={"year": year, "sector": sector},
                timeout=15
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"Status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_emissions_trend(self, country_code: str, start_year: int = 2015, end_year: int = 2022) -> Dict:
        """Get emissions trend over time for a country."""
        results = []
        try:
            for year in range(start_year, end_year + 1):
                data = self.get_country_emissions(country_code, year)
                if "error" not in data:
                    results.append({"year": year, "data": data})
            return {"country": country_code, "trend": results}
        except Exception as e:
            return {"error": str(e)}
    
    def search_assets(self, country_code: str = None, sector: str = None, limit: int = 20) -> Dict:
        """Search emission sources/assets."""
        try:
            params = {"limit": limit}
            if country_code:
                params["countries"] = country_code.upper()
            if sector:
                params["sectors"] = sector
            
            response = requests.get(
                f"{self.base_url}/assets",
                params=params,
                timeout=15
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"Status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def compare_countries(self, country_codes: List[str], year: int = 2022) -> Dict:
        """Compare emissions between multiple countries."""
        results = []
        try:
            for code in country_codes:
                data = self.get_country_emissions(code, year)
                results.append({"country": code, "emissions": data})
            return {"year": year, "comparison": results}
        except Exception as e:
            return {"error": str(e)}
    
    def get_available_sectors(self) -> List[str]:
        """Get list of tracked sectors."""
        return [
            "power", "transportation", "manufacturing", "buildings",
            "agriculture", "fossil-fuel-operations", "waste",
            "mineral-extraction", "forestry-and-land-use", "other"
        ]

