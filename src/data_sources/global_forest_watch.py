import requests
from typing import Any, Dict, List, Optional
from .base import BaseDataSource


class GlobalForestWatchClient(BaseDataSource):
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key, base_url="https://data-api.globalforestwatch.org")
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    def health_check(self) -> bool:
        try:
            response = requests.get("https://www.globalforestwatch.org/", timeout=15)
            return response.status_code == 200
        except:
            return False
    
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        return {"message": "Use get_country_stats() or get_tree_cover_loss()"}
    
    def get_country_stats(self, iso_code: str) -> Dict:
        try:
            url = f"https://data-api.globalforestwatch.org/dataset/umd_tree_cover_loss/latest/query"
            params = {"sql": f"SELECT * FROM data WHERE iso = '{iso_code.upper()}' LIMIT 10"}
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            return {"status": response.status_code, "iso": iso_code}
        except Exception as e:
            return {"error": str(e), "iso": iso_code}
    
    def get_tree_cover_loss(self, iso_code: str, year: Optional[int] = None) -> Dict:
        try:
            base = "https://data-api.globalforestwatch.org"
            url = f"{base}/dataset/umd_tree_cover_loss/latest/query"
            sql = f"SELECT SUM(umd_tree_cover_loss__ha) as total_loss FROM data WHERE iso = '{iso_code.upper()}'"
            if year:
                sql += f" AND umd_tree_cover_loss__year = {year}"
            response = requests.get(url, params={"sql": sql}, headers=self.headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            return {"status": response.status_code, "iso": iso_code}
        except Exception as e:
            return {"error": str(e)}
    
    def get_available_datasets(self) -> List[str]:
        return [
            "umd_tree_cover_loss",
            "gfw_integrated_alerts",
            "umd_tree_cover_density_2000",
            "gfw_forest_carbon_gross_emissions"
        ]
