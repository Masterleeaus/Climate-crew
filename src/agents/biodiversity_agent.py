from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING
from datetime import datetime

from langchain_core.tools import tool

from .base import BaseAgent
from ..data_sources.gbif import GBIFClient

if TYPE_CHECKING:
    from ..memory import MemoryManager

gbif_client = GBIFClient()


@tool
def search_species(query: str) -> str:
    """Search for species by name (common or scientific)."""
    try:
        data = gbif_client.search_species(query, limit=5)
        if "error" in data:
            return f"Error: {data['error']}"
        
        results = data.get("results", [])
        if not results:
            return f"No species found for '{query}'"
        
        response = f"Found {len(results)} species matching '{query}':\n"
        for sp in results:
            name = sp.get("scientificName", "Unknown")
            common = sp.get("vernacularName", "")
            rank = sp.get("rank", "")
            key = sp.get("key", "N/A")
            status = sp.get("taxonomicStatus", "")
            response += f"- {name}"
            if common:
                response += f" ({common})"
            response += f" | {rank} | Key: {key}\n"
        return response
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_species_occurrences(species_name: str, country_code: str = None) -> str:
    """Get occurrence records for a species. Optionally filter by country (ISO 2-letter code)."""
    try:
        # First search for the species to get its key
        search = gbif_client.search_species(species_name, limit=1)
        if "error" in search:
            return f"Error: {search['error']}"
        
        results = search.get("results", [])
        if not results:
            return f"Species '{species_name}' not found"
        
        species_key = results[0].get("key")
        name = results[0].get("scientificName", species_name)
        
        # Get occurrences
        occurrences = gbif_client.get_occurrences_by_species(species_key, limit=10)
        if "error" in occurrences:
            return f"Error: {occurrences['error']}"
        
        records = occurrences.get("results", [])
        total = occurrences.get("count", 0)
        
        response = f"Occurrences of {name}: {total} total records\n"
        response += f"Recent observations:\n"
        
        for rec in records[:5]:
            country = rec.get("country", "Unknown")
            locality = rec.get("locality", "")
            year = rec.get("year", "N/A")
            lat = rec.get("decimalLatitude", "N/A")
            lon = rec.get("decimalLongitude", "N/A")
            response += f"- {country}"
            if locality:
                response += f", {locality}"
            response += f" ({year}) at ({lat}, {lon})\n"
        
        return response
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def check_endangered_species(country_code: str) -> str:
    """Check for endangered species occurrences in a country (ISO 2-letter code like IN, US, BR)."""
    try:
        data = gbif_client.get_endangered_species(country_code, limit=20)
        if "error" in data:
            return f"Error: {data['error']}"
        
        records = data.get("results", [])
        count = data.get("count", 0)
        
        if not records:
            return f"No endangered species occurrence data found for {country_code}"
        
        # Group by species
        species_map = {}
        for rec in records:
            species = rec.get("species", rec.get("scientificName", "Unknown"))
            iucn = rec.get("iucnRedListCategory", "Unknown")
            if species not in species_map:
                species_map[species] = {"count": 0, "iucn": iucn}
            species_map[species]["count"] += 1
        
        response = f"Endangered species occurrences in {country_code}: {count} records\n"
        response += "Species found (IUCN status):\n"
        for species, info in list(species_map.items())[:10]:
            response += f"- {species} ({info['iucn']}): {info['count']} records\n"
        
        return response
    except Exception as e:
        return f"Error: {str(e)}"


from ..tools.rag_tool import search_climate_knowledge

@tool
def get_area_biodiversity(latitude: float, longitude: float, radius_km: float = 50) -> str:
    """Get species diversity near a location."""
    try:
        data = gbif_client.get_occurrences_by_location(latitude, longitude, radius_km, limit=100)
        if "error" in data:
            return f"Error: {data['error']}"
        
        records = data.get("results", [])
        
        if not records:
            return f"No species records found within {radius_km}km of ({latitude}, {longitude})"
        
        # Count unique species
        species_set = set()
        for rec in records:
            species = rec.get("species", rec.get("scientificName"))
            if species:
                species_set.add(species)
        
        response = f"Biodiversity near ({latitude}, {longitude}) within {radius_km}km:\n"
        response += f"Unique species observed: {len(species_set)}\n"
        response += f"Sample species:\n"
        
        for species in list(species_set)[:10]:
            response += f"- {species}\n"
        
        if len(species_set) > 10:
            response += f"... and {len(species_set) - 10} more species"
        
        return response
    except Exception as e:
        return f"Error: {str(e)}"


class BiodiversityAgent(BaseAgent):
    
    def __init__(self, google_api_key: Optional[str] = None, memory_manager: Optional['MemoryManager'] = None):
        super().__init__("BiodiversityAgent", google_api_key, memory_manager=memory_manager)
    
    def get_tools(self) -> List[Callable]:
        return [search_species, get_species_occurrences, check_endangered_species, get_area_biodiversity, search_climate_knowledge]
    
    def get_system_prompt(self) -> str:
        return """You are a Biodiversity and Wildlife monitoring agent. Help users track species and understand ecosystem health.

You have these tools:
- search_species: Find species by common or scientific name
- get_species_occurrences: Get where a species has been observed
- check_endangered_species: Find endangered species in a country
- get_area_biodiversity: Assess species diversity near a location (Default radius: 50km if not specified)

STRATEGY:
1. If the user asks for biodiversity near coordinates, call `get_area_biodiversity`.
2. Do NOT ask for the radius. Use the default 50km if the user doesn't specify.
3. Be direct and provide the list of species and richness count.

Key conservation insights:
- IUCN Red List categories: CR (Critically Endangered), EN (Endangered), VU (Vulnerable)
- Species richness indicates ecosystem health
- Migration patterns show seasonal changes

Use ISO 2-letter country codes: IN (India), US (USA), BR (Brazil), ID (Indonesia), AU (Australia)."""
    
    def get_alerts(self, countries: List[str] = None) -> List[Dict]:
        """Check for endangered species alerts in countries."""
        countries = countries or ["IN", "BR", "ID"]
        alerts = []
        
        for code in countries:
            try:
                data = gbif_client.get_endangered_species(code, limit=10)
                count = data.get("count", 0)
                if count > 0:
                    alerts.append({
                        "type": "endangered_species",
                        "country": code,
                        "occurrence_count": count,
                        "timestamp": datetime.utcnow().isoformat()
                    })
            except:
                pass
        
        return alerts
