from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv

from src.agents.climatex_audit_agent import ClimateXAuditAgent

load_dotenv()

router = APIRouter(prefix="/audit", tags=["Carbon Audit"])

# Initialize Agent
# In a real production app, we might want to dependency inject this or manage lifecycle better
audit_agent = ClimateXAuditAgent(
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    firms_api_key=os.getenv("FIRMS_API_KEY") # If needed
)

class AuditRequest(BaseModel):
    query: str
    latitude: float
    longitude: float

class AuditResponse(BaseModel):
    status: str
    compliance_score: int
    summary: str
    pdf_url: str
    evidence_count: int

@router.post("/verify", response_model=AuditResponse)
async def verify_project(request: AuditRequest):
    """
    Trigger a full Carbon Audit verification process.
    This includes Deep Research (text) + Satellite Analysis (maps) + PDF Generation.
    """
    try:
        # Run synchronous agent logic
        # Ideally this should be run in a threadpool or background task if it takes long
        # But for the demo flow, we wait for the result
        result = audit_agent.perform_full_audit(
            query=request.query, 
            lat=request.latitude, 
            lon=request.longitude
        )
        
        return AuditResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
