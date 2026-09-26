"""
Agent Metadata Configuration
Provides structured information about all available agents for the Agent Uplink interface.
"""

from typing import Dict, List, Any

AGENT_METADATA: Dict[str, Dict[str, Any]] = {
    "air_quality": {
        "id": "air_quality",
        "name": "Air Quality Agent",
        "description": "Monitors and analyzes air pollution levels, AQI trends, and atmospheric conditions across regions.",
        "category": "Climate",
        "icon": "Wind",
        "color": "cyan",
        "capabilities": [
            "Real-time AQI monitoring",
            "Pollution source analysis",
            "Air quality forecasting",
            "Health impact assessment"
        ]
    },
    "wildfire": {
        "id": "wildfire",
        "name": "Wildfire Agent",
        "description": "Tracks active wildfires, fire risk assessments, and environmental impact using NASA FIRMS data.",
        "category": "Climate",
        "icon": "Flame",
        "color": "orange",
        "capabilities": [
            "Active fire detection",
            "Fire spread prediction",
            "Risk zone mapping",
            "Smoke dispersion analysis"
        ]
    },
    "flood": {
        "id": "flood",
        "name": "Flood Agent",
        "description": "Monitors flood events, water level analysis, and flood risk assessment for vulnerable regions.",
        "category": "Climate",
        "icon": "Waves",
        "color": "blue",
        "capabilities": [
            "Flood risk assessment",
            "Water level monitoring",
            "Precipitation analysis",
            "Evacuation zone planning"
        ]
    },
    "biodiversity": {
        "id": "biodiversity",
        "name": "Biodiversity Agent",
        "description": "Analyzes ecosystem health, species diversity, and conservation status across different habitats.",
        "category": "Climate",
        "icon": "Trees",
        "color": "green",
        "capabilities": [
            "Species diversity tracking",
            "Habitat health analysis",
            "Conservation status reports",
            "Ecosystem threat detection"
        ]
    },
    "deforestation": {
        "id": "deforestation",
        "name": "Deforestation Agent",
        "description": "Tracks forest loss, deforestation rates, and land use changes using satellite imagery.",
        "category": "Climate",
        "icon": "TreePine",
        "color": "emerald",
        "capabilities": [
            "Forest cover analysis",
            "Deforestation hotspot detection",
            "Carbon impact estimation",
            "Reforestation monitoring"
        ]
    },
    "climate_anomaly": {
        "id": "climate_anomaly",
        "name": "Climate Anomaly Agent",
        "description": "Detects unusual climate patterns, temperature anomalies, and extreme weather events.",
        "category": "Climate",
        "icon": "CloudRain",
        "color": "purple",
        "capabilities": [
            "Temperature anomaly detection",
            "Extreme weather tracking",
            "Climate pattern analysis",
            "Long-term trend identification"
        ]
    },
    "carbon_emissions": {
        "id": "carbon_emissions",
        "name": "Carbon Emissions Agent",
        "description": "Tracks greenhouse gas emissions, carbon footprint analysis, and mitigation strategies.",
        "category": "Climate",
        "icon": "Factory",
        "color": "gray",
        "capabilities": [
            "Emission source tracking",
            "Carbon footprint calculation",
            "Reduction strategy analysis",
            "Net-zero pathway planning"
        ]
    },
    "earthquake": {
        "id": "earthquake",
        "name": "Earthquake Agent",
        "description": "Monitors seismic activity, earthquake events, and geological risk assessment.",
        "category": "Climate",
        "icon": "Mountain",
        "color": "red",
        "capabilities": [
            "Seismic activity monitoring",
            "Earthquake event tracking",
            "Risk zone identification",
            "Aftershock prediction"
        ]
    },
    "ocean": {
        "id": "ocean",
        "name": "Ocean Agent",
        "description": "Analyzes ocean health, sea level changes, temperature variations, and marine ecosystem status.",
        "category": "Climate",
        "icon": "Ship",
        "color": "teal",
        "capabilities": [
            "Sea level monitoring",
            "Ocean temperature tracking",
            "Marine ecosystem health",
            "Coastal erosion analysis"
        ]
    },
    "climatex": {
        "id": "climatex",
        "name": "ClimateX Audit Agent",
        "description": "Comprehensive climate system auditor providing holistic environmental assessments and reports.",
        "category": "Special",
        "icon": "ShieldCheck",
        "color": "indigo",
        "capabilities": [
            "Multi-domain climate audits",
            "Integrated risk assessment",
            "Compliance verification",
            "Strategic recommendations"
        ]
    },
    "satellite_fusion": {
        "id": "satellite_fusion",
        "name": "Satellite Fusion Agent",
        "description": "Integrates multi-source satellite data for advanced Earth observation and environmental analysis.",
        "category": "Special",
        "icon": "Satellite",
        "color": "violet",
        "capabilities": [
            "Multi-spectral analysis",
            "Change detection",
            "Land cover classification",
            "Temporal trend analysis"
        ]
    }
}


def get_all_agent_metadata() -> List[Dict[str, Any]]:
    """Returns list of all agent metadata."""
    return list(AGENT_METADATA.values())


def get_agent_metadata(agent_id: str) -> Dict[str, Any]:
    """Returns metadata for a specific agent."""
    return AGENT_METADATA.get(agent_id)


def get_agents_by_category(category: str) -> List[Dict[str, Any]]:
    """Returns all agents in a specific category."""
    return [
        metadata for metadata in AGENT_METADATA.values()
        if metadata["category"] == category
    ]
