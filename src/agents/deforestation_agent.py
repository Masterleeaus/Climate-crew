from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING
from datetime import datetime

from langchain_core.tools import tool

from .base import BaseAgent
from ..data_sources.global_forest_watch import GlobalForestWatchClient

if TYPE_CHECKING:
    from ..memory import MemoryManager

gfw_client = GlobalForestWatchClient()


@tool
def get_country_forest_stats(country_code: str) -> str:
    """Get forest statistics for a country. Use ISO 3-letter code (BRA, IDN, IND, etc)."""
    try:
        data = gfw_client.get_country_stats(country_code.upper())
        if "error" in data:
            return f"Error: {data['error']}"
        return f"Forest stats for {country_code}: {data}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_tree_cover_loss(country_code: str) -> str:
    """Get tree cover loss data for a country."""
    try:
        data = gfw_client.get_tree_cover_loss(country_code.upper())
        if "error" in data:
            return f"Error: {data['error']}"
        return f"Tree cover loss for {country_code}: {data}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def list_forest_datasets() -> str:
    """List available forest monitoring datasets."""
    datasets = gfw_client.get_available_datasets()
    return f"Available datasets: {', '.join(datasets)}"


from ..utils.geocoding import get_country_from_coords

class DeforestationAgent(BaseAgent):
    
    def __init__(self, gfw_api_key: Optional[str] = None, google_api_key: Optional[str] = None, memory_manager: Optional['MemoryManager'] = None):
        super().__init__("DeforestationAgent", google_api_key, memory_manager=memory_manager)
        if gfw_api_key:
            gfw_client.headers["Authorization"] = f"Bearer {gfw_api_key}"
    
    def get_tools(self) -> List[Callable]:
        return [get_country_forest_stats, get_tree_cover_loss, list_forest_datasets, get_country_from_coords]
    
    def get_system_prompt(self) -> str:
        return """You are a Deforestation monitoring agent. Help users understand forest loss and conservation.

You have these tools:
- get_country_from_coords: CRITICAL! Always use this first if the user provides coordinates (lat, lon) to find the country code.
- get_country_forest_stats: Get forest statistics for a country (requires ISO 3-letter code like BRA, IDN).
- get_tree_cover_loss: Get tree cover loss data for a country.
- list_forest_datasets: List available monitoring datasets.

STRATEGY:
1. If the user gives coordinates, IMMEDIATELY call `get_country_from_coords`.
2. Use the returned country code to call `get_tree_cover_loss` AND `get_country_forest_stats`.
3. Do NOT ask the user for permission.
4. Do NOT ask "Would you like to see...". JUST SHOW THE DATA.
5. If data is found, summarize the key figures (forest lost, total cover) in the final response.

Key countries for deforestation monitoring:
- BRA (Brazil)
- IDN (Indonesia)
- COD (DR Congo)

Context: Provide a direct report on the forest status of the identified region.

Provide context about the environmental impact of deforestation. Be concise."""
    
    def get_alerts(self, countries: List[str] = None) -> List[Dict]:
        countries = countries or ["BRA", "IDN", "COD"]
        alerts = []
        for code in countries:
            try:
                data = gfw_client.get_tree_cover_loss(code)
                if "data" in data:
                    alerts.append({
                        "type": "deforestation",
                        "country": code,
                        "data": data,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except:
                pass
        return alerts
