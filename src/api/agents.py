from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List
import os

from .agent_metadata import get_all_agent_metadata, get_agent_metadata

from ..agents.air_quality_agent import AirQualityAgent
from ..agents.wildfire_agent import WildfireAgent
from ..agents.flood_agent import FloodAgent
from ..agents.biodiversity_agent import BiodiversityAgent
from ..agents.deforestation_agent import DeforestationAgent
from ..agents.climate_anomaly_agent import ClimateAnomalyAgent
from ..agents.carbon_emissions_agent import CarbonEmissionsAgent
from ..agents.earthquake_agent import EarthquakeAgent
from ..agents.ocean_agent import OceanAgent
from ..agents.climatex_audit_agent import ClimateXAuditAgent
from ..agents.satellite_video_fusion_agent import SatelliteVideoFusionAgent

AVAILABLE_AGENTS = [
    "air_quality", "wildfire", "flood", "biodiversity", "deforestation",
    "climate_anomaly", "carbon_emissions", "earthquake", "ocean",
    "climatex", "satellite_fusion"
]

router = APIRouter(prefix="/agents", tags=["Domain Agents"])

class AgentQueryRequest(BaseModel):
    query: str

class AgentResponse(BaseModel):
    response: str

# Global Agent Registry
_agents: Dict[str, Any] = {}

def get_agent(name: str):
    global _agents
    name = name.lower()
    
    if name in _agents:
        return _agents[name]

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not configured")
    
    firms_key = os.getenv("NASA_FIRMS_API_KEY")
    
    try:
        if name == "air_quality":
            _agents[name] = AirQualityAgent(google_api_key=api_key)
        elif name == "wildfire":
            _agents[name] = WildfireAgent(google_api_key=api_key, firms_api_key=firms_key)
        elif name == "flood":
            _agents[name] = FloodAgent(google_api_key=api_key)
        elif name == "biodiversity":
            _agents[name] = BiodiversityAgent(google_api_key=api_key)
        elif name == "deforestation":
            _agents[name] = DeforestationAgent(google_api_key=api_key)
        elif name == "climate_anomaly":
            _agents[name] = ClimateAnomalyAgent(google_api_key=api_key)
        elif name == "carbon_emissions":
            _agents[name] = CarbonEmissionsAgent(google_api_key=api_key)
        elif name == "earthquake":
            _agents[name] = EarthquakeAgent(google_api_key=api_key)
        elif name == "ocean":
            _agents[name] = OceanAgent(google_api_key=api_key)
        elif name == "climatex":
            _agents[name] = ClimateXAuditAgent(google_api_key=api_key, firms_api_key=firms_key)
        elif name == "satellite_fusion":
            _agents[name] = SatelliteVideoFusionAgent(google_api_key=api_key)
        else:
            raise HTTPException(status_code=404, detail=f"Agent '{name}' is not registered.")
            
        return _agents[name]

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to initialize agent '{name}': {str(e)}")

@router.get("/list")
async def list_agents():
    """List all available domain agents."""
    return {"agents": AVAILABLE_AGENTS}

@router.get("/metadata")
async def get_agents_metadata():
    """Get metadata for all available agents including descriptions, categories, and capabilities."""
    return {"agents": get_all_agent_metadata()}

@router.get("/{agent_name}/info")
async def get_agent_info(agent_name: str):
    """Get detailed information about a specific agent."""
    metadata = get_agent_metadata(agent_name)
    if not metadata:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_name}' not found")
    return metadata

# --- Explicit Endpoints ---

@router.post("/air_quality/chat", response_model=AgentResponse, summary="Chat with Air Quality Agent")
async def chat_air_quality(request: AgentQueryRequest):
    try:
        agent = get_agent("air_quality")
        return AgentResponse(response=str(agent.run(request.query)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/wildfire/chat", response_model=AgentResponse, summary="Chat with Wildfire Agent")
async def chat_wildfire(request: AgentQueryRequest):
    try:
        agent = get_agent("wildfire")
        return AgentResponse(response=str(agent.run(request.query)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/flood/chat", response_model=AgentResponse, summary="Chat with Flood Agent")
async def chat_flood(request: AgentQueryRequest):
    try:
        agent = get_agent("flood")
        return AgentResponse(response=str(agent.run(request.query)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/biodiversity/chat", response_model=AgentResponse, summary="Chat with Biodiversity Agent")
async def chat_biodiversity(request: AgentQueryRequest):
    try:
        agent = get_agent("biodiversity")
        return AgentResponse(response=str(agent.run(request.query)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/deforestation/chat", response_model=AgentResponse, summary="Chat with Deforestation Agent")
async def chat_deforestation(request: AgentQueryRequest):
    try:
        agent = get_agent("deforestation")
        return AgentResponse(response=str(agent.run(request.query)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/climate_anomaly/chat", response_model=AgentResponse, summary="Chat with Climate Anomaly Agent")
async def chat_climate_anomaly(request: AgentQueryRequest):
    try:
        agent = get_agent("climate_anomaly")
        return AgentResponse(response=str(agent.run(request.query)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/carbon_emissions/chat", response_model=AgentResponse, summary="Chat with Carbon Emissions Agent")
async def chat_carbon_emissions(request: AgentQueryRequest):
    try:
        agent = get_agent("carbon_emissions")
        return AgentResponse(response=str(agent.run(request.query)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/earthquake/chat", response_model=AgentResponse, summary="Chat with Earthquake Agent")
async def chat_earthquake(request: AgentQueryRequest):
    try:
        agent = get_agent("earthquake")
        return AgentResponse(response=str(agent.run(request.query)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ocean/chat", response_model=AgentResponse, summary="Chat with Ocean Agent")
async def chat_ocean(request: AgentQueryRequest):
    try:
        agent = get_agent("ocean")
        return AgentResponse(response=str(agent.run(request.query)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/climatex/chat", response_model=AgentResponse, summary="Chat with ClimateX Audit Agent")
async def chat_climatex(request: AgentQueryRequest):
    try:
        agent = get_agent("climatex")
        return AgentResponse(response=str(agent.run(request.query)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/satellite_fusion/chat", response_model=AgentResponse, summary="Chat with Satellite Fusion Agent")
async def chat_satellite_fusion(request: AgentQueryRequest):
    try:
        agent = get_agent("satellite_fusion")
        return AgentResponse(response=str(agent.run(request.query)))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
