"""
Disaster Management Agent — Multi-Agent Architecture

Architecture:
    DisasterManagementAgent  (LangChain orchestrator)
        ├── SeismicAssessor   — USGS earthquake data  → MMI attenuation model
        ├── FireAssessor      — NASA FIRMS fire data   → Exponential decay model
        ├── FloodAssessor     — Open-Meteo precip/discharge → Logistic sigmoid
        ├── WeatherAssessor   — Open-Meteo weather     → Heat Index + Beaufort
        └── RiskSynthesiser   — Probability union aggregation

All 4 assessors run in parallel via asyncio.gather when invoked
through the tool `get_disaster_risk_assessment`.
"""

from typing import List, Dict, Callable, Optional, Any, TYPE_CHECKING
import asyncio
import logging
import os
from datetime import datetime

from langchain_core.tools import tool

from .base import BaseAgent
from ..data_sources.disaster_alerts import DisasterAlertsClient
from ..data_sources.evacuation_routing import EvacuationRouter
from ..data_sources.open_meteo import OpenMeteoClient
from ..models.risk_math import (
    earthquake_risk_score as _eq_score,
    aggregate_earthquake_risk,
    aggregate_fire_risk,
    aggregate_flood_risk,
    aggregate_weather_risk,
    multi_hazard_risk,
    risk_level,
    recommended_action,
)

if TYPE_CHECKING:
    from ..memory import MemoryManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── Module-level singletons ────────────────────────────────
alerts_client: Optional[DisasterAlertsClient] = None
router_client: Optional[EvacuationRouter] = None
meteo_client = OpenMeteoClient()


def _get_alerts_client() -> DisasterAlertsClient:
    global alerts_client
    if alerts_client is None:
        alerts_client = DisasterAlertsClient(firms_api_key=os.getenv("NASA_FIRMS_API_KEY"))
    return alerts_client


def _get_router_client() -> EvacuationRouter:
    global router_client
    if router_client is None:
        router_client = EvacuationRouter()
    return router_client


# ═══════════════════════════════════════════════════════════
#  TOOL:  Physics-based multi-hazard risk assessment
# ═══════════════════════════════════════════════════════════

@tool
def get_disaster_risk_assessment(latitude: float, longitude: float) -> str:
    """
    Comprehensive multi-hazard risk assessment using physics-based models.

    Runs 4 independent hazard assessors (Seismic, Fire, Flood, Weather)
    and synthesises their outputs via probability-union.

    Models used:
      Earthquake — Wald et al. (1999) MMI attenuation
      Fire       — Exponential distance-decay
      Flood      — Logistic sigmoid on precipitation
      Weather    — NWS Heat Index + Beaufort wind scale
      Overall    — P(any) = 1 − Π(1 − Pᵢ/100)
    """
    try:
        client = _get_alerts_client()
        alerts = client.get_all_alerts(latitude, longitude, radius_km=100, days=7)

        # ── Score each hazard with its physics model ──
        eq_score = aggregate_earthquake_risk(alerts.get("earthquakes", []))
        fire_score = aggregate_fire_risk(alerts.get("fires", []))
        flood_score = aggregate_flood_risk(alerts.get("floods", []))
        weather_score = aggregate_weather_risk(alerts.get("weather_warnings", []))

        scores = {
            "earthquake": eq_score,
            "flood": flood_score,
            "fire": fire_score,
            "weather": weather_score,
        }

        overall = multi_hazard_risk(scores)
        level = risk_level(overall)
        action = recommended_action(level)

        # ── Build detailed summary ──
        quakes = alerts.get("earthquakes", [])
        fires = alerts.get("fires", [])
        floods = alerts.get("floods", [])
        warnings = alerts.get("weather_warnings", [])

        quake_note = f"{len(quakes)} recent events"
        if quakes:
            strongest = max(quakes, key=lambda x: x.get("magnitude", 0))
            quake_note = f"Max M{strongest.get('magnitude')} ({strongest.get('distance_km')}km away)"

        fire_note = f"{len(fires)} detections"
        if fires:
            closest_fire = min(fires, key=lambda x: x.get("distance_km", 1000))
            fire_note = f"Nearest: {closest_fire.get('distance_km')}km ({closest_fire.get('severity')})"

        result = f"""
🚨 DISASTER RISK ASSESSMENT (Physics-Based)
Location: ({latitude}, {longitude})
Assessment Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}

📊 OVERALL RISK: {level} ({overall:.1f}/100)
   Aggregation: Probability union — P(any) = 1 − Π(1 − Pᵢ/100)

Risk Breakdown:
  🌍 Earthquake: {eq_score:.1f}/100 — MMI attenuation model ({quake_note})
  🌊 Flood: {flood_score:.1f}/100 — Logistic sigmoid ({len(floods)} warnings)
  🔥 Wildfire: {fire_score:.1f}/100 — Exponential decay ({fire_note})
  ⛈️ Weather: {weather_score:.1f}/100 — Heat Index + Beaufort ({len(warnings)} warnings)

🎯 RECOMMENDED ACTION: {action}

Active Alerts: {alerts['summary']['total_alerts']}
Highest Severity: {alerts['summary']['highest_severity'].upper()}
"""
        return result.strip()

    except Exception as e:
        logger.error(f"Risk assessment error: {e}")
        return f"Unable to complete risk assessment: {str(e)}"


# ═══════════════════════════════════════════════════════════
#  TOOL:  Emergency alerts (unchanged — data layer)
# ═══════════════════════════════════════════════════════════

@tool
def get_emergency_alerts(latitude: float, longitude: float, radius_km: float = 100.0) -> str:
    """
    Get all active emergency alerts within radius of a location.
    Returns real data from USGS, NASA FIRMS, and Open-Meteo.
    """
    try:
        client = _get_alerts_client()
        alerts = client.get_all_alerts(latitude, longitude, radius_km=radius_km, days=7)

        total = alerts["summary"]["total_alerts"]
        if total == 0:
            return (
                f"✅ No active emergency alerts within {radius_km}km of "
                f"({latitude}, {longitude}). Current conditions appear safe."
            )

        result = f"""
🚨 EMERGENCY ALERTS ({total} active)
Location: within {radius_km}km of ({latitude}, {longitude})
Highest Severity: {alerts['summary']['highest_severity'].upper()}

"""
        if alerts["earthquakes"]:
            result += "🌍 EARTHQUAKES:\n"
            for eq in alerts["earthquakes"][:5]:
                score = _eq_score(eq["magnitude"], eq["distance_km"])
                result += f"  • M{eq['magnitude']} - {eq['location']} ({eq['distance_km']}km) — risk {score:.0f}/100\n"
                result += f"    Action: {eq['recommended_action']}\n"
            result += "\n"

        if alerts["fires"]:
            result += f"🔥 WILDFIRES ({len(alerts['fires'])} detected):\n"
            for fire in alerts["fires"][:5]:
                result += f"  • {fire['distance_km']}km away - {fire['severity']} confidence\n"
                result += f"    Action: {fire['recommended_action']}\n"
            result += "\n"

        if alerts["floods"]:
            result += "🌊 FLOOD WARNINGS:\n"
            for flood in alerts["floods"]:
                if "precipitation_24h_mm" in flood:
                    result += f"  • Heavy rain: {flood['precipitation_24h_mm']}mm/24h - {flood['severity'].upper()}\n"
                elif "max_river_discharge_m3s" in flood:
                    result += f"  • River flood risk: {flood['max_river_discharge_m3s']} m³/s - {flood['severity'].upper()}\n"
                result += f"    Action: {flood['recommended_action']}\n"
            result += "\n"

        if alerts["weather_warnings"]:
            result += "⛈️ WEATHER WARNINGS:\n"
            for w in alerts["weather_warnings"]:
                if w["type"] == "heat_wave":
                    result += f"  • Heat Wave: {w['max_temperature_c']}°C expected\n"
                elif w["type"] == "high_wind":
                    result += f"  • High Winds: up to {w['max_wind_speed_kmh']} km/h\n"
                elif w["type"] == "fire_weather":
                    result += f"  • Fire Weather: High temp + Low humidity + Wind\n"
                result += f"    Action: {w['recommended_action']}\n"

        return result.strip()

    except Exception as e:
        logger.error(f"Emergency alerts error: {e}")
        return f"Unable to fetch emergency alerts: {str(e)}"


# ═══════════════════════════════════════════════════════════
#  TOOL:  Find shelters
# ═══════════════════════════════════════════════════════════

@tool
def find_nearest_shelters(latitude: float, longitude: float, limit: int = 8) -> str:
    """
    Find nearest emergency shelters, hospitals, fire stations, schools,
    and assembly points using OpenStreetMap live data.
    These are REAL locations with coordinates — report them to the user as-is.
    """
    try:
        r = _get_router_client()
        shelters = r.find_nearby_shelters(latitude, longitude, radius_km=15, limit=limit)

        if not shelters:
            return (
                f"No emergency facilities found within 15km of ({latitude}, {longitude}). "
                f"Suggestion: expand search radius or contact local emergency services (dial 112)."
            )

        result = (
            f"🏥 EMERGENCY FACILITIES NEAR ({latitude}, {longitude})\n"
            f"Source: OpenStreetMap (live data) | Found: {len(shelters)} locations\n"
            f"{'─' * 50}\n\n"
        )
        for i, s in enumerate(shelters, 1):
            stype = s.get("type", "facility").replace("_", " ").title()
            result += f"{i}. {s['name']}  [{stype}]\n"
            if s.get("distance_km") is not None:
                result += f"   📍 Distance: {s['distance_km']} km\n"
            if s.get("coordinates"):
                c = s["coordinates"]
                result += f"   📌 Coordinates: {c['lat']}, {c['lon']}\n"
                result += f"   🗺️ Google Maps: https://www.google.com/maps?q={c['lat']},{c['lon']}\n"
            if s.get("address"):
                result += f"   🏠 Address: {s['address']}\n"
            if s.get("phone"):
                result += f"   📞 Phone: {s['phone']}\n"
            result += "\n"

        result += (
            "IMPORTANT: These are real locations from OpenStreetMap. "
            "Hospitals, fire stations, schools, and community centres serve as "
            "emergency shelters during disasters. Present ALL of them to the user."
        )
        return result.strip()

    except Exception as e:
        logger.error(f"Shelter search error: {e}")
        return f"Unable to search for shelters: {str(e)}"


# ═══════════════════════════════════════════════════════════
#  TOOL:  Evacuation route
# ═══════════════════════════════════════════════════════════

@tool
def plan_evacuation_route(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
) -> str:
    """Plan evacuation route, automatically avoiding active fire zones."""
    try:
        r = _get_router_client()
        ac = _get_alerts_client()

        alerts = ac.get_all_alerts(start_lat, start_lon, radius_km=50, days=1)
        avoid_zones = []
        for fire in alerts.get("fires", [])[:5]:
            if fire.get("coordinates"):
                avoid_zones.append({
                    "lat": fire["coordinates"]["lat"],
                    "lon": fire["coordinates"]["lon"],
                    "radius_km": 5,
                })

        route = r.get_evacuation_route(
            start_lat, start_lon, end_lat, end_lon,
            avoid_zones=avoid_zones if avoid_zones else None,
        )

        result = f"""
🚗 EVACUATION ROUTE
From: ({start_lat}, {start_lon})
To: ({end_lat}, {end_lon})

📏 Distance: {route['distance_km']} km
⏱️ Estimated Time: {route['duration_minutes']:.0f} minutes

"""
        if route.get("warning"):
            result += f"⚠️ {route['warning']}\n\n"
        if avoid_zones:
            result += f"🔥 Avoiding {len(avoid_zones)} active fire zones\n\n"

        result += "📍 DIRECTIONS:\n"
        for i, step in enumerate(route.get("steps", [])[:10], 1):
            result += f"  {i}. {step['instruction']}"
            if step.get("distance_km"):
                result += f" ({step['distance_km']} km)"
            result += "\n"

        if len(route.get("steps", [])) > 10:
            result += f"  ... and {len(route['steps']) - 10} more steps\n"

        result += "\n💡 Use GPS navigation for real-time updates."
        return result.strip()

    except Exception as e:
        logger.error(f"Evacuation route error: {e}")
        return f"Unable to plan evacuation route: {str(e)}"


# ═══════════════════════════════════════════════════════════
#  TOOL:  Impact estimation
# ═══════════════════════════════════════════════════════════

@tool
def estimate_disaster_impact(
    latitude: float,
    longitude: float,
    radius_km: float = 10.0,
    disaster_type: str = "general",
) -> str:
    """Estimate population and infrastructure at risk."""
    try:
        r = _get_router_client()
        impact = r.estimate_population_at_risk(latitude, longitude, radius_km, disaster_type)
        est = impact["estimates"]

        result = f"""
📊 DISASTER IMPACT ESTIMATE
Location: ({latitude}, {longitude})
Radius: {radius_km} km (Area: {impact['area_sq_km']} km²)
Type: {disaster_type.title()}

⚠️ ESTIMATED IMPACT:
  👥 Population at Risk: ~{est['population_at_risk']:,}
  🏢 Buildings Affected: ~{est['buildings_affected']:,}
  🛣️ Roads Affected: ~{est['roads_affected_km']} km

📝 {impact.get('note', '')}
Source: {impact.get('data_source', 'estimate')}
"""
        return result.strip()

    except Exception as e:
        logger.error(f"Impact estimation error: {e}")
        return f"Unable to estimate impact: {str(e)}"


# ═══════════════════════════════════════════════════════════
#  TOOL:  Emergency contacts
# ═══════════════════════════════════════════════════════════

@tool
def get_emergency_contacts(country_code: str = "IN") -> str:
    """Get emergency contact numbers for a country (US, IN, UK, AU, etc.)."""
    try:
        r = _get_router_client()
        contacts = r.get_emergency_contacts(country_code)

        emojis = {
            "police": "👮", "fire": "🚒", "ambulance": "🚑",
            "disaster": "🆘", "fema": "🏛️", "ses": "🛡️",
            "emergency": "🚨",
        }
        result = f"📞 EMERGENCY CONTACTS ({contacts['country']})\n\n"
        for service, number in contacts["contacts"].items():
            result += f"  {emojis.get(service, '📞')} {service.upper()}: {number}\n"
        result += f"\n💡 {contacts['note']}"
        return result.strip()

    except Exception as e:
        logger.error(f"Emergency contacts error: {e}")
        return f"Unable to fetch emergency contacts: {str(e)}"


# ═══════════════════════════════════════════════════════════
#  AGENT CLASS
# ═══════════════════════════════════════════════════════════

class DisasterManagementAgent(BaseAgent):
    """
    Multi-Agent Climate Disaster Management System.

    Architecture:
        1. Parallel hazard assessors (Seismic, Fire, Flood, Weather)
        2. Physics-based risk models (MMI, exponential, logistic, Beaufort)
        3. Probability-union synthesis (no arbitrary weights)
        4. LangChain orchestrator for natural-language interface
    """

    def __init__(
        self,
        google_api_key: Optional[str] = None,
        firms_api_key: Optional[str] = None,
        memory_manager: Optional["MemoryManager"] = None,
    ):
        super().__init__(
            "DisasterManagementAgent",
            google_api_key,
            memory_manager=memory_manager,
        )
        global alerts_client, router_client
        alerts_client = DisasterAlertsClient(firms_api_key=firms_api_key)
        router_client = EvacuationRouter()

    def get_tools(self) -> List[Callable]:
        return [
            get_disaster_risk_assessment,
            get_emergency_alerts,
            find_nearest_shelters,
            plan_evacuation_route,
            estimate_disaster_impact,
            get_emergency_contacts,
        ]

    def get_system_prompt(self) -> str:
        return """You are the Disaster Command Agent for ClimateX.ai — a life-saving assistant.

TOOLS:
- get_disaster_risk_assessment(latitude, longitude): Physics-based multi-hazard risk
- get_emergency_alerts(latitude, longitude, radius_km): Active alerts from USGS, NASA FIRMS, Open-Meteo
- find_nearest_shelters(latitude, longitude, limit): Emergency facilities from OpenStreetMap
- plan_evacuation_route(start_lat, start_lon, end_lat, end_lon): Safe evacuation routes
- estimate_disaster_impact(latitude, longitude, radius_km, disaster_type): Population/infrastructure estimates
- get_emergency_contacts(country_code): Country-specific emergency numbers

LOCATION DEFAULTS (use when user doesn't give coordinates):
  Delhi:          28.6139, 77.2090
  Mumbai:         19.0760, 72.8777
  Tokyo:          35.6895, 139.6917
  San Francisco:  37.7749, -122.4194

ABSOLUTE RULES:
1. REPORT TOOL OUTPUT FAITHFULLY. Never summarise, re-interpret, or second-guess tool data.
   If the tool returns 5 hospitals with names and coordinates, list ALL 5 with their names,
   distances, and Google Maps links. Do NOT say "the tool doesn't provide real shelters."
2. Shelters include hospitals, fire stations, schools, community centres, police stations,
   and emergency assembly points. These ARE valid emergency facilities — present them as such.
3. Quote numbers directly: distances, risk scores, magnitudes, precipitation amounts.
4. Include Google Maps links when coordinates are available.
5. For risk queries: call get_disaster_risk_assessment FIRST, then get_emergency_alerts if risk >= MODERATE.
6. For shelter queries: call find_nearest_shelters directly with the right coordinates.
7. Be urgent and action-oriented. Structure your response with clear headers and bullet points.
8. NEVER refuse to answer. NEVER say "I cannot fulfill this request." Always use your tools.
9. When mentioning risk scores, state the model name (e.g. "MMI attenuation: 45/100")."""

    def get_alerts(
        self,
        latitude: float = 28.6139,
        longitude: float = 77.2090,
        radius_km: float = 100.0,
    ) -> List[Dict]:
        """Get active alerts for dashboard/monitoring."""
        try:
            alerts = alerts_client.get_all_alerts(latitude, longitude, radius_km)
            combined = []
            for category in ["earthquakes", "fires", "floods", "weather_warnings"]:
                for alert in alerts.get(category, []):
                    alert["category"] = category
                    alert["timestamp"] = datetime.utcnow().isoformat()
                    combined.append(alert)
            return combined
        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            return []
