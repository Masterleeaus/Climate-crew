from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import os
from .orchestrator import RetailSwarm
from ..air_quality_agent import AirQualityAgent
from ..wildfire_agent import WildfireAgent
from ..flood_agent import FloodAgent
from ..biodiversity_agent import BiodiversityAgent
from ..deforestation_agent import DeforestationAgent
from ..climate_anomaly_agent import ClimateAnomalyAgent

from .models import CausalNode, ActionPlan, CommunicationPackage, DashboardPayload

router = APIRouter(prefix="/retail", tags=["Retail Analytics"])

class AuditRequest(BaseModel):
    latitude: float
    longitude: float

class AuditResponse(BaseModel):
    causal_graph: CausalNode
    action_plan: ActionPlan
    communications: CommunicationPackage
    dashboard_payload: DashboardPayload

# Global instance lazy loading or dependency injection best practice
# For this simpler architecture, we initialize on startup or request if needed.
# Since agents are heavy, we'll initialize a global swarm helper.

_swarm_instance = None

def get_retail_swarm():
    global _swarm_instance
    if _swarm_instance is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not configured")
            
        domain_agents = {
            "Air Quality": AirQualityAgent(api_key),
            "Wildfire": WildfireAgent(google_api_key=api_key),
            "Flood": FloodAgent(google_api_key=api_key),
            "Biodiversity": BiodiversityAgent(google_api_key=api_key),
            "Deforestation": DeforestationAgent(google_api_key=api_key),
            "Climate Anomaly": ClimateAnomalyAgent(google_api_key=api_key)
        }
        
        _swarm_instance = RetailSwarm(
            google_api_key=api_key, 
            memory_manager=None, # Memory optional for API requests for now
            domain_agents=domain_agents
        )
    return _swarm_instance

@router.post("/audit", response_model=AuditResponse)
async def conduct_audit(request: AuditRequest):
    """
    Conducts a comprehensive Retail Analytics Audit for a specific location.
    Fetches real-time environmental data and generates actionable plans + public advice.
    """
    try:
        swarm = get_retail_swarm()
        results = swarm.audit_location(request.latitude, request.longitude)
        return results
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
