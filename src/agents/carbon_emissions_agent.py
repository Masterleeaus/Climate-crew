from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING
from datetime import datetime

from langchain_core.tools import tool

from .base import BaseAgent
from ..data_sources.climate_trace import ClimateTraceClient

if TYPE_CHECKING:
    from ..memory import MemoryManager

climate_trace = ClimateTraceClient()


@tool
def get_country_emissions(country_code: str, year: int = 2023) -> str:
    """Get total greenhouse gas emissions for a country. Use ISO 3-letter code (USA, IND, CHN, BRA)."""
    try:
        data = climate_trace.get_country_emissions(country_code.upper(), year)
        if "error" in data:
            return f"Error: {data['error']}"
        
        if isinstance(data, list) and len(data) > 0:
            emissions = data[0]
            total = emissions.get("emissions", {}).get("co2e_100yr", 0)
            # Convert to readable format
            total_mt = total / 1_000_000  # Convert to megatons
            return f"Emissions for {country_code.upper()} ({year}): {total_mt:,.0f} Mt CO2e"
        elif isinstance(data, dict):
            return f"Emissions data for {country_code.upper()}: {data}"
        return f"No emissions data found for {country_code}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_sector_emissions(country_code: str, sector: str) -> str:
    """Get emissions by sector for a country. 
    Sectors: power, transportation, manufacturing, buildings, agriculture, fossil-fuel-operations, waste."""
    try:
        data = climate_trace.get_sector_emissions(country_code.upper(), sector, 2023)
        if "error" in data:
            return f"Error: {data['error']}"
        
        if isinstance(data, list) and len(data) > 0:
            emissions = data[0]
            sector_data = emissions.get("emissions", {})
            total = sector_data.get("co2e_100yr", 0)
            total_mt = total / 1_000_000
            return f"{sector.title()} emissions in {country_code.upper()}: {total_mt:,.0f} Mt CO2e"
        return f"No sector data found for {sector} in {country_code}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_emission_trends(country_code: str, start_year: int = 2015, end_year: int = 2023) -> str:
    """Get emissions trend for a country over time."""
    try:
        data = climate_trace.get_emissions_trend(country_code.upper(), start_year, end_year)
        if "error" in data:
            return f"Error: {data['error']}"
        
        if isinstance(data, list) and len(data) > 0:
            yearly_emissions = []
            for entry in data:
                year = entry.get("year", "N/A")
                emissions = entry.get("emissions", {}).get("co2e_100yr", 0)
                emissions_mt = emissions / 1_000_000
                yearly_emissions.append(f"{year}: {emissions_mt:,.0f} Mt")
            
            response = f"Emissions Trend for {country_code.upper()} ({start_year}-{end_year}):\n"
            response += "\n".join(yearly_emissions[:10])
            return response
        return f"No trend data available for {country_code}"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def compare_countries(country_codes: str) -> str:
    """Compare emissions between multiple countries. Provide comma-separated ISO 3-letter codes (e.g., 'USA,CHN,IND')."""
    try:
        codes = [c.strip().upper() for c in country_codes.split(",")]
        data = climate_trace.compare_countries(codes, 2023)
        if "error" in data:
            return f"Error: {data['error']}"
        
        if isinstance(data, list) and len(data) > 0:
            comparisons = []
            for entry in data:
                country = entry.get("iso3_country", "Unknown")
                emissions = entry.get("emissions", {}).get("co2e_100yr", 0)
                emissions_mt = emissions / 1_000_000
                comparisons.append((country, emissions_mt))
            
            # Sort by emissions
            comparisons.sort(key=lambda x: x[1], reverse=True)
            
            response = "Emissions Comparison (2023):\n"
            for i, (country, emissions) in enumerate(comparisons, 1):
                response += f"{i}. {country}: {emissions:,.0f} Mt CO2e\n"
            return response
        return f"No comparison data available"
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def list_emission_sectors() -> str:
    """List all emission sectors tracked by Climate TRACE."""
    sectors = climate_trace.get_available_sectors()
    response = "Emission Sectors Tracked:\n"
    for sector in sectors:
        response += f"- {sector.replace('-', ' ').title()}\n"
    return response


from ..tools.rag_tool import search_climate_knowledge
from ..utils.geocoding import get_country_from_coords

class CarbonEmissionsAgent(BaseAgent):
    
    def __init__(self, google_api_key: Optional[str] = None, memory_manager: Optional['MemoryManager'] = None):
        super().__init__("CarbonEmissionsAgent", google_api_key, memory_manager=memory_manager)
    
    def get_tools(self) -> List[Callable]:
        return [get_country_emissions, get_sector_emissions, get_emission_trends, 
                compare_countries, list_emission_sectors, get_country_from_coords, search_climate_knowledge]
    
    def get_system_prompt(self) -> str:
        return """You are a Carbon Emissions monitoring agent. Help users understand greenhouse gas emissions.

You have these tools:
- get_country_from_coords: CRITICAL! Use this FIRST if user provides coordinates to find the country.
- get_country_emissions: Get total emissions for a country (requires ISO 3-letter code).
- get_sector_emissions: Get emissions by sector.
- get_emission_trends: Track emissions over time.

STRATEGY:
1. If coordinates are provided, use `get_country_from_coords` to get the ISO code.
2. AUTOMATICALLY call `get_country_emissions` and `get_sector_emissions` for that country.
3. Do NOT ask "Would you like to check...". JUST DO IT.
4. Report the total emissions and the top sector immediately.

Key emissions insights:
- Top emitters: CHN, USA, IND, RUS, JPN
- Power sector: Largest contributor globally
- Trends: Important for tracking Paris Agreement progress

Use ISO 3-letter country codes: USA, CHN, IND, BRA, DEU, GBR, JPN, RUS, IDN, etc."""
    
    def get_alerts(self, countries: List[str] = None) -> List[Dict]:
        """Check for emissions alerts."""
        countries = countries or ["CHN", "USA", "IND"]
        alerts = []
        
        for code in countries:
            try:
                data = climate_trace.get_country_emissions(code, 2023)
                if isinstance(data, list) and len(data) > 0:
                    emissions = data[0].get("emissions", {}).get("co2e_100yr", 0)
                    if emissions > 1_000_000_000_000:  # > 1000 Mt
                        alerts.append({
                            "type": "high_emissions",
                            "country": code,
                            "emissions_mt": emissions / 1_000_000,
                            "timestamp": datetime.utcnow().isoformat()
                        })
            except:
                pass
        
        return alerts
