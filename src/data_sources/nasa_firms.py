import requests
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as cx
import io
from .base import BaseDataSource


class NASAFIRMSClient(BaseDataSource):
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key, base_url="https://firms.modaps.eosdis.nasa.gov")
    
    def health_check(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/data_availability", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        return {"fires": self.get_fires(**kwargs)}
    
    def get_fires(
        self,
        source: str = "VIIRS_SNPP_NRT",
        area: str = "world",
        days: int = 1,
        format: str = "json"
    ) -> List[Dict[str, Any]]:
        if not self.api_key:
            raise ValueError("NASA FIRMS requires an API key. Get one at: https://firms.modaps.eosdis.nasa.gov/api/")
        
        url = f"{self.base_url}/api/area/csv/{self.api_key}/{source}/{area}/{days}"
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        
        if format == "json":
            return self._parse_csv_to_json(response.text)
        return response.text
    
    def get_fires_by_country(
        self,
        country_code: str,
        source: str = "VIIRS_SNPP_NRT",
        days: int = 1
    ) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/api/country/csv/{self.api_key}/{source}/{country_code}/{days}"
        response = requests.get(url, timeout=60)
        response.raise_for_status()
        return self._parse_csv_to_json(response.text)
    
    def get_fires_by_bbox(
        self,
        west: float,
        south: float,
        east: float,
        north: float,
        source: str = "VIIRS_SNPP_NRT",
        days: int = 1
    ) -> List[Dict[str, Any]]:
        area = f"{west},{south},{east},{north}"
        return self.get_fires(source=source, area=area, days=days)
    
    def _parse_csv_to_json(self, csv_text: str) -> List[Dict[str, Any]]:
        lines = csv_text.strip().split("\n")
        if len(lines) < 2:
            return []
        
        headers = lines[0].split(",")
        result = []
        for line in lines[1:]:
            values = line.split(",")
            if len(values) == len(headers):
                result.append(dict(zip(headers, values)))
        return result
    
    def get_available_sources(self) -> List[str]:
        return [
            "MODIS_NRT",
            "MODIS_SP",
            "VIIRS_NOAA20_NRT",
            "VIIRS_NOAA21_NRT",
            "VIIRS_SNPP_NRT",
            "VIIRS_SNPP_SP"
        ]

    def generate_fire_map(self, fires_data: List[Dict[str, Any]], output_path: str):
        """
        Generate a static map image of the fires overlaid on a satellite basemap.
        Args:
            fires_data: List of fire dictionaries (from get_fires).
            output_path: Path to save the PNG image.
        """
        if not fires_data:
            return

        try:
            df = pd.DataFrame(fires_data)
            # Ensure numeric types
            df['latitude'] = pd.to_numeric(df['latitude'])
            df['longitude'] = pd.to_numeric(df['longitude'])
            
            # 1. Convert to GeoDataFrame with WGS84 (EPSG:4326)
            gdf = gpd.GeoDataFrame(
                df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326"
            )
            
            # 2. Re-project to Web Mercator (EPSG:3857) for Contextily basemaps
            # Check if crs is set, if not set it
            if gdf.crs is None:
                gdf.set_crs(epsg=4326, inplace=True)
            gdf_web = gdf.to_crs(epsg=3857)
            
            # 3. Setup Plot
            fig, ax = plt.subplots(figsize=(10, 10))
            
            # 4. Plot Fire Points
            color = 'red'
            if 'confidence' in df.columns:
                # Simple logic: High confidence = Dark Red, others = Red
                # But for now keep simple red dots
                pass

            gdf_web.plot(ax=ax, color='red', markersize=30, alpha=0.7, edgecolor='black')

            # 5. Add Basemap (Esri World Imagery)
            try:
                cx.add_basemap(ax, source=cx.providers.Esri.WorldImagery)
            except Exception as e:
                print(f"Warning: Could not add basemap: {e}")

            ax.set_axis_off()
            ax.set_title(f"Fire Detection Map - {datetime.now().strftime('%Y-%m-%d')}")
            
            # 6. Save
            plt.savefig(output_path, bbox_inches='tight', dpi=150)
            plt.close()
            
        except Exception as e:
            print(f"Failed to generate map: {e}")
