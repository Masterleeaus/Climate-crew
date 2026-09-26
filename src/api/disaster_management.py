"""
Disaster Management API — physics-based risk scoring, parallel execution.

Risk models (see src/models/risk_math.py for full documentation):
  • Earthquake : Wald et al. (1999) MMI attenuation
  • Fire       : Exponential distance-decay
  • Flood      : Logistic sigmoid on precipitation / discharge
  • Weather    : NWS Heat Index + Beaufort wind scale
  • Overall    : Probability-union (no arbitrary weights)
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import asyncio
import os
import logging
from datetime import datetime
from dotenv import load_dotenv

from src.agents.disaster_management_agent import DisasterManagementAgent
from src.data_sources.disaster_alerts import DisasterAlertsClient
from src.data_sources.evacuation_routing import EvacuationRouter
from src.models.risk_math import (
    earthquake_risk_score,
    aggregate_earthquake_risk,
    aggregate_fire_risk,
    aggregate_flood_risk,
    aggregate_weather_risk,
    multi_hazard_risk,
    risk_level,
    recommended_action,
)

load_dotenv()
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/disaster", tags=["Disaster Management"])

# ── Singletons ─────────────────────────────────────────────
disaster_agent = DisasterManagementAgent(
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    firms_api_key=os.getenv("NASA_FIRMS_API_KEY"),
)

alerts_client = DisasterAlertsClient(
    firms_api_key=os.getenv("NASA_FIRMS_API_KEY"),
)

evacuation_router = EvacuationRouter()


# ══════════════════════════════════════════════════════════
#  Request / Response Models
# ══════════════════════════════════════════════════════════

class LocationRequest(BaseModel):
    latitude: float = Field(..., description="Latitude", example=28.6139)
    longitude: float = Field(..., description="Longitude", example=77.2090)
    radius_km: Optional[float] = Field(100.0, description="Radius in km")


class HazardScore(BaseModel):
    score: float
    model: str
    details: Optional[str] = None


class RiskAssessmentResponse(BaseModel):
    status: str
    overall_risk_level: str
    overall_risk_score: float
    risk_breakdown: Dict[str, float]
    total_alerts: int
    highest_severity: str
    recommended_action: str
    methodology: Dict[str, str]
    assessed_at: str


class AlertsResponse(BaseModel):
    status: str
    total_alerts: int
    highest_severity: str
    earthquakes: List[Dict[str, Any]]
    fires: List[Dict[str, Any]]
    floods: List[Dict[str, Any]]
    weather_warnings: List[Dict[str, Any]]


class ShelterRequest(BaseModel):
    latitude: float
    longitude: float
    limit: Optional[int] = Field(5, description="Max shelters to return")


class ShelterResponse(BaseModel):
    status: str
    shelters: List[Dict[str, Any]]
    total_found: int


class EvacuationRequest(BaseModel):
    start_lat: float
    start_lon: float
    end_lat: float
    end_lon: float


class EvacuationResponse(BaseModel):
    status: str
    distance_km: float
    duration_minutes: float
    steps: List[Dict[str, Any]]
    warning: Optional[str]


class ImpactRequest(BaseModel):
    latitude: float
    longitude: float
    radius_km: Optional[float] = Field(10.0)
    disaster_type: Optional[str] = Field("general")


class ImpactResponse(BaseModel):
    status: str
    radius_km: float
    area_sq_km: float
    disaster_type: str
    population_at_risk: int
    buildings_affected: int
    roads_affected_km: float
    density_source: Optional[str] = None


class ChatRequest(BaseModel):
    query: str


class ChatResponse(BaseModel):
    status: str
    response: str


# ══════════════════════════════════════════════════════════
#  Parallel Hazard Assessors
# ══════════════════════════════════════════════════════════

async def _assess_earthquake(alerts: Dict) -> float:
    """Score earthquakes using MMI attenuation model."""
    return aggregate_earthquake_risk(alerts.get("earthquakes", []))


async def _assess_fire(alerts: Dict) -> float:
    """Score fires using exponential distance-decay model."""
    return aggregate_fire_risk(alerts.get("fires", []))


async def _assess_flood(alerts: Dict) -> float:
    """Score floods using logistic precipitation model."""
    return aggregate_flood_risk(alerts.get("floods", []))


async def _assess_weather(alerts: Dict) -> float:
    """Score weather using Heat Index + Beaufort scale."""
    return aggregate_weather_risk(alerts.get("weather_warnings", []))


# ══════════════════════════════════════════════════════════
#  API Endpoints
# ══════════════════════════════════════════════════════════

@router.post("/risk-assessment", response_model=RiskAssessmentResponse)
async def get_risk_assessment(request: LocationRequest):
    """
    Multi-hazard risk assessment with physics-based scoring.

    Runs 4 hazard assessors in parallel, aggregates via
    probability-union (no arbitrary weights).
    """
    try:
        # Fetch all alerts (data layer)
        alerts = alerts_client.get_all_alerts(
            latitude=request.latitude,
            longitude=request.longitude,
            radius_km=request.radius_km,
            days=30,
        )

        # Run 4 hazard assessors in parallel
        eq_score, fire_score, flood_score, weather_score = await asyncio.gather(
            _assess_earthquake(alerts),
            _assess_fire(alerts),
            _assess_flood(alerts),
            _assess_weather(alerts),
        )

        scores = {
            "earthquake": round(eq_score, 1),
            "flood": round(flood_score, 1),
            "fire": round(fire_score, 1),
            "weather": round(weather_score, 1),
        }

        # Aggregate via probability union — no arbitrary weights
        overall = round(multi_hazard_risk(scores), 1)
        level = risk_level(overall)
        action = recommended_action(level)

        return RiskAssessmentResponse(
            status="success",
            overall_risk_level=level,
            overall_risk_score=overall,
            risk_breakdown=scores,
            total_alerts=alerts["summary"]["total_alerts"],
            highest_severity=alerts["summary"]["highest_severity"],
            recommended_action=action,
            methodology={
                "earthquake": "Atkinson & Wald (2007) MMI attenuation (USGS DYFI IPE) → 0-100",
                "fire": "Exponential distance-decay with brightness adjustment",
                "flood": "Logistic sigmoid on precipitation (P₅₀=75mm) and discharge (Q₅₀=800m³/s)",
                "weather": "NWS Heat Index (Rothfusz 1990) + Beaufort wind scale",
                "aggregation": "Probability union: P(any) = 1 − Π(1 − Pᵢ/100) — no arbitrary weights",
            },
            assessed_at=datetime.utcnow().isoformat() + "Z",
        )

    except Exception as e:
        logger.error(f"Risk assessment error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/alerts", response_model=AlertsResponse)
async def get_emergency_alerts(request: LocationRequest):
    """Active emergency alerts within radius."""
    try:
        alerts = alerts_client.get_all_alerts(
            latitude=request.latitude,
            longitude=request.longitude,
            radius_km=request.radius_km,
            days=30,
        )
        return AlertsResponse(
            status="success",
            total_alerts=alerts["summary"]["total_alerts"],
            highest_severity=alerts["summary"]["highest_severity"],
            earthquakes=alerts.get("earthquakes", []),
            fires=alerts.get("fires", []),
            floods=alerts.get("floods", []),
            weather_warnings=alerts.get("weather_warnings", []),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/shelters", response_model=ShelterResponse)
async def find_shelters(request: ShelterRequest):
    """Find nearby emergency shelters / hospitals / safe zones."""
    try:
        shelters = evacuation_router.find_nearby_shelters(
            latitude=request.latitude,
            longitude=request.longitude,
            radius_km=25.0,
            limit=request.limit,
        )
        return ShelterResponse(
            status="success",
            shelters=shelters,
            total_found=len(shelters),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evacuation-route", response_model=EvacuationResponse)
async def plan_evacuation(request: EvacuationRequest):
    """Evacuation route from A → B."""
    try:
        route = evacuation_router.get_evacuation_route(
            start_lat=request.start_lat,
            start_lon=request.start_lon,
            end_lat=request.end_lat,
            end_lon=request.end_lon,
        )
        return EvacuationResponse(
            status=route.get("status", "success"),
            distance_km=route.get("distance_km", 0),
            duration_minutes=route.get("duration_minutes", 0),
            steps=route.get("steps", []),
            warning=route.get("warning"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/impact-estimate", response_model=ImpactResponse)
async def estimate_impact(request: ImpactRequest):
    """Estimate population & infrastructure at risk."""
    try:
        impact = evacuation_router.estimate_population_at_risk(
            latitude=request.latitude,
            longitude=request.longitude,
            radius_km=request.radius_km,
            disaster_type=request.disaster_type,
        )
        estimates = impact["estimates"]
        return ImpactResponse(
            status="success",
            radius_km=impact["radius_km"],
            area_sq_km=impact["area_sq_km"],
            disaster_type=impact["disaster_type"],
            population_at_risk=estimates["population_at_risk"],
            buildings_affected=estimates["buildings_affected"],
            roads_affected_km=estimates["roads_affected_km"],
            density_source=impact.get("data_source"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/emergency-contacts/{country_code}")
async def get_emergency_contacts(country_code: str = "IN"):
    """Emergency contact numbers for a country."""
    try:
        return evacuation_router.get_emergency_contacts(country_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """Natural-language interface to the Disaster Management Agent."""
    try:
        response = disaster_agent.run(request.query)
        return ChatResponse(status="success", response=response)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "disaster-management",
        "architecture": "parallel-multi-assessor",
        "risk_models": {
            "earthquake": "Atkinson & Wald (2007) MMI",
            "fire": "Exponential distance-decay",
            "flood": "Logistic sigmoid",
            "weather": "NWS Heat Index + Beaufort",
            "aggregation": "Probability union",
        },
        "tools_available": [
            "risk-assessment",
            "alerts",
            "shelters",
            "evacuation-route",
            "impact-estimate",
            "emergency-contacts",
            "chat",
        ],
    }
