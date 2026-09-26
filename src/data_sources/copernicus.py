"""
Copernicus Marine and Sentinel Data Sources
- Marine: Ocean physics, biogeochemistry, sea level
- Sentinel: Satellite imagery for land/ocean monitoring
"""
import requests
from typing import Any, Dict, List, Optional
from .base import BaseDataSource


class CopernicusMarineClient(BaseDataSource):
    """Copernicus Marine Service for ocean data."""
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None):
        super().__init__(base_url="https://data.marine.copernicus.eu")
        self.username = username
        self.password = password
    
    def health_check(self) -> bool:
        try:
            # Try the STAC API endpoint which is publicly accessible
            response = requests.get(
                "https://stac.marine.copernicus.eu/",
                timeout=15
            )
            if response.status_code == 200:
                return True
            # Fallback to main website
            response = requests.get("https://marine.copernicus.eu", timeout=15)
            return response.status_code in [200, 301, 302]
        except:
            return False
    
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        return {"products": self.get_available_datasets()}
    
    def get_available_datasets(self) -> List[Dict]:
        return [
            {"id": "cmems_mod_glo_phy_anfc_0.083deg_P1D-m", "name": "Global Ocean Physics Analysis and Forecast", "variables": ["thetao", "so", "uo", "vo", "zos"]},
            {"id": "cmems_mod_glo_bgc_anfc_0.25deg_P1D-m", "name": "Global Ocean Biogeochemistry Analysis and Forecast", "variables": ["chl", "no3", "o2", "ph"]},
            {"id": "cmems_obs-oc_glo_bgc-plankton_nrt_l4-gapfree-multi-4km_P1D", "name": "Global Ocean Colour", "variables": ["CHL"]},
            {"id": "cmems_mod_glo_wav_anfc_0.083deg_PT3H-i", "name": "Global Ocean Waves", "variables": ["VHM0", "VMDR", "VTM10"]},
            {"id": "cmems_obs-sl_glo_phy-ssh_nrt_allsat-l4-duacs-0.25deg_P1D", "name": "Global Sea Level", "variables": ["sla", "adt"]}
        ]
    
    def get_available_variables(self) -> List[str]:
        return ["thetao", "so", "uo", "vo", "zos", "chl", "no3", "o2", "ph", "VHM0", "sla"]
    
    def get_download_info(self) -> str:
        return """To download Copernicus Marine data, use the copernicusmarine package:
        pip install copernicusmarine
        
        import copernicusmarine as cm
        cm.subset(
            dataset_id="cmems_mod_glo_phy_anfc_0.083deg_P1D-m",
            variables=["thetao"],
            minimum_longitude=-180,
            maximum_longitude=180,
            start_datetime="2024-01-01",
            end_datetime="2024-01-02"
        )
        
        Register at: https://marine.copernicus.eu/"""


class CopernicusSentinelClient(BaseDataSource):
    """Copernicus Data Space (Sentinel satellites)."""
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None):
        super().__init__(base_url="https://dataspace.copernicus.eu")
        self.client_id = client_id
        self.client_secret = client_secret
    
    def health_check(self) -> bool:
        try:
            # Use the catalogue status endpoint
            response = requests.get(
                "https://catalogue.dataspace.copernicus.eu/resto/api/collections/describe.json",
                timeout=15
            )
            if response.status_code == 200:
                return True
            # Fallback
            response = requests.get("https://dataspace.copernicus.eu", timeout=15)
            return response.status_code in [200, 301, 302]
        except:
            return False
    
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        return self.search_products(**kwargs)
    
    def search_products(self, collection: str = "SENTINEL-2", bbox: Optional[List[float]] = None, 
                        start_date: Optional[str] = None, end_date: Optional[str] = None, 
                        cloud_cover: int = 30, limit: int = 10) -> Dict:
        base_url = "https://catalogue.dataspace.copernicus.eu/odata/v1/Products"
        filters = [f"Collection/Name eq '{collection}'"]
        
        if start_date:
            filters.append(f"ContentDate/Start ge {start_date}T00:00:00.000Z")
        if end_date:
            filters.append(f"ContentDate/Start le {end_date}T23:59:59.999Z")
        if cloud_cover and "SENTINEL-2" in collection:
            filters.append(f"Attributes/OData.CSC.DoubleAttribute/any(att:att/Name eq 'cloudCover' and att/Value le {cloud_cover})")
        if bbox:
            filters.append(f"OData.CSC.Intersects(area=geography'SRID=4326;POLYGON(({bbox[0]} {bbox[1]},{bbox[2]} {bbox[1]},{bbox[2]} {bbox[3]},{bbox[0]} {bbox[3]},{bbox[0]} {bbox[1]}))')")
        
        filter_str = " and ".join(filters)
        try:
            response = requests.get(f"{base_url}?$filter={filter_str}&$top={limit}&$orderby=ContentDate/Start desc", timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def get_available_collections(self) -> List[Dict]:
        return [
            {"name": "SENTINEL-1", "type": "SAR", "description": "SAR imagery for flood, oil spill detection", "resolution": "10m"},
            {"name": "SENTINEL-2", "type": "Optical", "description": "Multispectral imagery for land monitoring", "resolution": "10m"},
            {"name": "SENTINEL-3", "type": "Multi", "description": "Ocean and land monitoring", "resolution": "300m"},
            {"name": "SENTINEL-5P", "type": "Atmospheric", "description": "Atmospheric monitoring (TROPOMI)", "resolution": "7km"},
            {"name": "LANDSAT-8", "type": "Optical", "description": "Multispectral land imaging", "resolution": "30m"}
        ]

