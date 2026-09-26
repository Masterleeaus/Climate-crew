from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import os
from typing import Optional, Dict, Any
from .orchestrator import DeepResearchOrchestrator

router = APIRouter(
    prefix="/deep-research",
    tags=["Deep Research"]
)

class ResearchRequest(BaseModel):
    query: str
    
class Source(BaseModel):
    title: str
    url: str
    type: str = "web"

class ResearchResponse(BaseModel):
    report: str
    sources: list[Source] = []

def get_deep_research_module():
    from ...agents.orchestrator import OrchestratorAgent
    
    google_api_key = os.getenv("GOOGLE_API_KEY")
    firms_api_key = os.getenv("FIRMS_API_KEY")
    
    if not google_api_key:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not configured on server")
        
    # Create base orchestrator with advanced features enabled
    base_orchestrator = OrchestratorAgent(
        google_api_key=google_api_key,
        firms_api_key=firms_api_key,
        enable_memory=True, 
        enable_rag=False,
        enable_dynamic_routing=True,
        enable_meta_learning=True,
        enable_collaboration=True
    )    
    domain_agents = list(base_orchestrator.agents.values())
    
    # Create deep research orchestrator with advanced features
    dro = DeepResearchOrchestrator(
        google_api_key=google_api_key,
        domain_agents=domain_agents,
        enable_dynamic_routing=True,
        enable_meta_learning=True,
        enable_collaboration=True
    )
    
    return dro

@router.post("/", response_model=ResearchResponse)
async def run_deep_research(
    request: ResearchRequest,
    dro: DeepResearchOrchestrator = Depends(get_deep_research_module)
):
    try:
        query = request.query
        result = dro.run_deep_research(query) # Now returns dict
        return ResearchResponse(
            report=result.get("report", ""), 
            sources=result.get("sources", [])
        )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
