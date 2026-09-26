"""
GBIF (Global Biodiversity Information Facility) API Client
Free access to species occurrence and biodiversity data.
No API key required for basic queries.
"""
import requests
from typing import Any, Dict, List, Optional
from .base import BaseDataSource


class GBIFClient(BaseDataSource):
    """GBIF API for biodiversity and species data."""
    
    def __init__(self):
        super().__init__(base_url="https://api.gbif.org/v1")
    
    def health_check(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/species/search", 
                                    params={"q": "test", "limit": 1}, timeout=15)
            return response.status_code == 200
        except:
            return False
    
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        query = kwargs.get("query", "")
        return self.search_species(query)
    
    def search_species(self, query: str, limit: int = 10) -> Dict:
        """Search for species by name."""
        try:
            response = requests.get(
                f"{self.base_url}/species/search",
                params={"q": query, "limit": limit},
                timeout=15
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"Status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_species_info(self, species_key: int) -> Dict:
        """Get detailed species information by GBIF key."""
        try:
            response = requests.get(f"{self.base_url}/species/{species_key}", timeout=15)
            if response.status_code == 200:
                return response.json()
            return {"error": f"Status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_occurrences_by_species(self, species_key: int, limit: int = 20) -> Dict:
        """Get occurrence records for a species."""
        try:
            response = requests.get(
                f"{self.base_url}/occurrence/search",
                params={"taxonKey": species_key, "limit": limit},
                timeout=15
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"Status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_occurrences_by_location(self, latitude: float, longitude: float, 
                                     radius_km: float = 50, limit: int = 50) -> Dict:
        """Get species occurrences near a location."""
        try:
            # GBIF uses decimal degrees for the geometry
            response = requests.get(
                f"{self.base_url}/occurrence/search",
                params={
                    "decimalLatitude": f"{latitude-radius_km/111},{latitude+radius_km/111}",
                    "decimalLongitude": f"{longitude-radius_km/111},{longitude+radius_km/111}",
                    "limit": limit,
                    "hasCoordinate": "true"
                },
                timeout=15
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"Status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_occurrences_by_country(self, country_code: str, limit: int = 100) -> Dict:
        """Get species occurrences in a country."""
        try:
            response = requests.get(
                f"{self.base_url}/occurrence/search",
                params={"country": country_code.upper(), "limit": limit},
                timeout=15
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"Status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_endangered_species(self, country_code: str = None, limit: int = 50) -> Dict:
        """Get occurrences of IUCN Red List species."""
        try:
            params = {
                "iucnRedListCategory": "CR,EN,VU",  # Critically Endangered, Endangered, Vulnerable
                "limit": limit,
                "hasCoordinate": "true"
            }
            if country_code:
                params["country"] = country_code.upper()
            
            response = requests.get(
                f"{self.base_url}/occurrence/search",
                params=params,
                timeout=15
            )
            if response.status_code == 200:
                return response.json()
            return {"error": f"Status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_species_count_by_country(self, country_code: str) -> Dict:
        """Get species count for a country."""
        try:
            response = requests.get(
                f"{self.base_url}/occurrence/counts/countries",
                timeout=15
            )
            if response.status_code == 200:
                data = response.json()
                count = data.get(country_code.upper(), 0)
                return {"country": country_code.upper(), "occurrence_count": count}
            return {"error": f"Status {response.status_code}"}
        except Exception as e:
            return {"error": str(e)}
