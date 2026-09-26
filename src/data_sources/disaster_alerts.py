"""
Disaster alert aggregation from live data sources.

Data sources:
  • USGS Earthquake API  — seismic events
  • NASA FIRMS           — active fire detections
  • Open-Meteo           — precipitation, river discharge, temperature, wind

Design principle: this module fetches and structures raw data.
It does NOT apply risk thresholds — that is the job of risk_math.py.
Every non-trivial measurement is passed through so the physics models
can score it properly.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import requests
import logging
import math

from .base import BaseDataSource
from .open_meteo import OpenMeteoClient
from .usgs_earthquake import USGSEarthquakeClient
from .nasa_firms import NASAFIRMSClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DisasterAlertsClient:
    """Aggregates disaster alerts from multiple live sources."""

    # Earthquake: M2.5+ is the USGS standard "felt" threshold.
    EARTHQUAKE_MIN_MAGNITUDE = 2.5

    def __init__(self, firms_api_key: Optional[str] = None):
        self.meteo_client = OpenMeteoClient()
        self.usgs_client = USGSEarthquakeClient()
        self.firms_client = NASAFIRMSClient(api_key=firms_api_key)

    # ════════════════════════════════════════════════════════
    #  PUBLIC — get everything
    # ════════════════════════════════════════════════════════

    def get_all_alerts(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 100.0,
        days: int = 30,
    ) -> Dict[str, Any]:
        """
        Fetch all hazard data within *radius_km* of (lat, lon).

        Returns a dict with:
            earthquakes, fires, floods, weather_warnings, summary
        """
        alerts: Dict[str, Any] = {
            "earthquakes": [],
            "fires": [],
            "floods": [],
            "weather_warnings": [],
            "summary": {
                "total_alerts": 0,
                "highest_severity": "none",
                "last_updated": datetime.utcnow().isoformat(),
            },
        }

        # Earthquakes
        try:
            alerts["earthquakes"] = self._get_earthquake_alerts(
                latitude, longitude, radius_km, days
            )
        except Exception as e:
            logger.warning(f"Earthquake fetch failed: {e}")

        # Fires
        try:
            alerts["fires"] = self._get_fire_alerts(latitude, longitude, radius_km)
        except Exception as e:
            logger.warning(f"Fire fetch failed: {e}")

        # Flood / precipitation
        try:
            alerts["floods"] = self._get_flood_alerts(latitude, longitude)
        except Exception as e:
            logger.warning(f"Flood fetch failed: {e}")

        # Weather (heat, wind, fire-weather)
        try:
            alerts["weather_warnings"] = self._get_weather_warnings(latitude, longitude)
        except Exception as e:
            logger.warning(f"Weather fetch failed: {e}")

        total = sum(
            len(alerts[k])
            for k in ("earthquakes", "fires", "floods", "weather_warnings")
        )
        alerts["summary"]["total_alerts"] = total
        alerts["summary"]["highest_severity"] = self._highest_severity(alerts)

        return alerts

    # ════════════════════════════════════════════════════════
    #  EARTHQUAKES  (USGS)
    # ════════════════════════════════════════════════════════

    def _get_earthquake_alerts(
        self, lat: float, lon: float, radius_km: float, days: int
    ) -> List[Dict]:
        try:
            result = self.usgs_client.get_earthquakes_near_location(
                latitude=lat, longitude=lon, radius_km=radius_km, days=days
            )

            alerts = []
            for eq in result.get("features", []):
                props = eq.get("properties", {})
                coords = eq.get("geometry", {}).get("coordinates", [])
                if len(coords) < 2:
                    continue

                magnitude = props.get("mag")
                if magnitude is None:
                    continue
                if magnitude < self.EARTHQUAKE_MIN_MAGNITUDE:
                    continue

                eq_lon, eq_lat = coords[0], coords[1]
                depth_km = coords[2] if len(coords) >= 3 else 10.0
                distance = self._haversine(lat, lon, eq_lat, eq_lon)

                alerts.append({
                    "type": "earthquake",
                    "magnitude": magnitude,
                    "depth_km": round(depth_km, 1) if depth_km else 10.0,
                    "location": props.get("place", "Unknown"),
                    "distance_km": round(distance, 1),
                    "time": props.get("time"),
                    "severity": self._eq_severity(magnitude),
                    "coordinates": {"lat": eq_lat, "lon": eq_lon},
                    "recommended_action": self._eq_action(magnitude),
                })

            return sorted(alerts, key=lambda x: x["magnitude"], reverse=True)[:15]
        except Exception as e:
            logger.error(f"Earthquake alert error: {e}")
            return []

    # ════════════════════════════════════════════════════════
    #  FIRES  (NASA FIRMS)
    # ════════════════════════════════════════════════════════

    def _get_fire_alerts(
        self, lat: float, lon: float, radius_km: float
    ) -> List[Dict]:
        if not self.firms_client.api_key:
            return []
        try:
            deg = radius_km / 111.0
            fires = self.firms_client.get_fires_by_bbox(
                lon - deg, lat - deg, lon + deg, lat + deg, days=2
            )
            alerts = []
            for f in fires:
                f_lat = f.get("latitude", f.get("lat"))
                f_lon = f.get("longitude", f.get("lon"))
                if not f_lat or not f_lon:
                    continue

                dist = self._haversine(lat, lon, f_lat, f_lon)
                confidence = f.get("confidence", "low")
                if confidence in ("high", "h", "nominal", "n"):
                    severity = "high"
                elif confidence in ("medium", "m"):
                    severity = "moderate"
                else:
                    severity = "low"

                alerts.append({
                    "type": "wildfire",
                    "distance_km": round(dist, 1),
                    "brightness": f.get("bright_ti4", f.get("brightness")),
                    "confidence": confidence,
                    "severity": severity,
                    "coordinates": {"lat": f_lat, "lon": f_lon},
                    "satellite": f.get("satellite", "Unknown"),
                    "recommended_action": self._fire_action(dist, severity),
                })

            return sorted(alerts, key=lambda x: x["distance_km"])[:20]
        except Exception as e:
            logger.error(f"Fire alert error: {e}")
            return []

    # ════════════════════════════════════════════════════════
    #  FLOOD / PRECIPITATION  (Open-Meteo)
    # ════════════════════════════════════════════════════════

    def _get_flood_alerts(self, lat: float, lon: float) -> List[Dict]:
        """
        Always emit a precipitation record if > 1 mm/24h.
        The risk_math sigmoid decides the actual risk score.
        """
        try:
            weather = self.meteo_client.get_weather(lat, lon)
            hourly = weather.get("hourly", {})
            precip = hourly.get("precipitation", [])[:72]

            alerts = []

            precip_24h = sum(precip[:24]) if len(precip) >= 24 else sum(precip)
            precip_48h = sum(precip[:48]) if len(precip) >= 48 else sum(precip)
            precip_72h = sum(precip)

            # Emit if ANY meaningful precipitation (> 1mm)
            if precip_24h > 1.0:
                if precip_24h > 100:
                    severity = "critical"
                elif precip_24h > 50:
                    severity = "high"
                elif precip_24h > 20:
                    severity = "moderate"
                else:
                    severity = "low"

                alerts.append({
                    "type": "flood_risk",
                    "precipitation_24h_mm": round(precip_24h, 1),
                    "precipitation_48h_mm": round(precip_48h, 1),
                    "precipitation_72h_mm": round(precip_72h, 1),
                    "severity": severity,
                    "coordinates": {"lat": lat, "lon": lon},
                    "recommended_action": self._flood_action(severity),
                })

            # River discharge
            try:
                flood_data = self.meteo_client.get_flood_forecast(lat, lon)
                daily = flood_data.get("daily", {})
                discharge = daily.get("river_discharge", [])
                if discharge:
                    max_q = max(d for d in discharge if d is not None) if any(d is not None for d in discharge) else 0
                    if max_q > 50:  # Any significant discharge
                        if max_q > 1500:
                            severity = "critical"
                        elif max_q > 800:
                            severity = "high"
                        elif max_q > 300:
                            severity = "moderate"
                        else:
                            severity = "low"
                        alerts.append({
                            "type": "river_flood_risk",
                            "max_river_discharge_m3s": round(max_q, 1),
                            "severity": severity,
                            "coordinates": {"lat": lat, "lon": lon},
                            "recommended_action": self._flood_action(severity),
                        })
            except Exception:
                pass

            return alerts
        except Exception as e:
            logger.error(f"Flood alert error: {e}")
            return []

    # ════════════════════════════════════════════════════════
    #  WEATHER  (Open-Meteo)
    # ════════════════════════════════════════════════════════

    def _get_weather_warnings(self, lat: float, lon: float) -> List[Dict]:
        """
        Always emit weather observations when they are non-trivial.
        The risk_math Heat Index / Beaufort models decide the score.
        """
        try:
            weather = self.meteo_client.get_weather(lat, lon)
            hourly = weather.get("hourly", {})

            temps = hourly.get("temperature_2m", [])[:48]
            wind = hourly.get("wind_speed_10m", [])[:48]
            humidity = hourly.get("relative_humidity_2m", [])[:48]

            alerts = []

            # ── Heat: emit if max temp > 28°C (let Heat Index model score it) ──
            if temps:
                max_temp = max(temps)
                if max_temp >= 28:
                    avg_hum = (
                        sum(humidity[:24]) / len(humidity[:24])
                        if humidity and len(humidity) >= 24
                        else 50.0
                    )
                    if max_temp >= 42:
                        severity = "critical"
                    elif max_temp >= 35:
                        severity = "high"
                    elif max_temp >= 30:
                        severity = "moderate"
                    else:
                        severity = "low"

                    alerts.append({
                        "type": "heat_wave",
                        "max_temperature_c": round(max_temp, 1),
                        "avg_humidity_pct": round(avg_hum, 1),
                        "severity": severity,
                        "duration_hours": sum(1 for t in temps if t >= 30),
                        "coordinates": {"lat": lat, "lon": lon},
                        "recommended_action": self._heat_action(severity),
                    })

            # ── Wind: emit if > 30 km/h (let Beaufort model score it) ──
            if wind:
                max_wind = max(wind)
                if max_wind >= 30:
                    if max_wind >= 100:
                        severity = "critical"
                    elif max_wind >= 60:
                        severity = "high"
                    elif max_wind >= 40:
                        severity = "moderate"
                    else:
                        severity = "low"

                    alerts.append({
                        "type": "high_wind",
                        "max_wind_speed_kmh": round(max_wind, 1),
                        "severity": severity,
                        "coordinates": {"lat": lat, "lon": lon},
                        "recommended_action": (
                            "Secure loose objects. Stay indoors if possible."
                            if max_wind < 60
                            else "Dangerous wind speeds. Stay indoors. Avoid driving."
                        ),
                    })

            # ── Fire weather: temp > 28 + humidity < 40 + wind > 15 ──
            if temps and humidity and wind:
                avg_temp = sum(temps[:24]) / len(temps[:24])
                avg_hum = sum(humidity[:24]) / len(humidity[:24])
                max_w24 = max(wind[:24])
                if avg_temp > 28 and avg_hum < 40 and max_w24 > 15:
                    alerts.append({
                        "type": "fire_weather",
                        "temperature_c": round(avg_temp, 1),
                        "humidity_pct": round(avg_hum, 1),
                        "wind_speed_kmh": round(max_w24, 1),
                        "severity": "high" if (avg_temp > 35 and avg_hum < 25) else "moderate",
                        "coordinates": {"lat": lat, "lon": lon},
                        "recommended_action": "Fire danger elevated. No open flames. Monitor conditions.",
                    })

            return alerts
        except Exception as e:
            logger.warning(f"Weather warning error: {e}")
            return []

    # ════════════════════════════════════════════════════════
    #  Helpers
    # ════════════════════════════════════════════════════════

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        R = 6371.0
        la1, lo1, la2, lo2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat, dlon = la2 - la1, lo2 - lo1
        a = math.sin(dlat / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin(dlon / 2) ** 2
        return R * 2 * math.asin(math.sqrt(a))

    @staticmethod
    def _eq_severity(mag: float) -> str:
        if mag >= 7: return "critical"
        if mag >= 6: return "high"
        if mag >= 5: return "moderate"
        return "low"

    @staticmethod
    def _eq_action(mag: float) -> str:
        if mag >= 7: return "EVACUATE immediately. Move to open ground. Expect aftershocks."
        if mag >= 6: return "Drop, Cover, Hold. Check for structural damage."
        if mag >= 5: return "Minor damage possible. Check gas lines and water pipes."
        if mag >= 4: return "Felt widely. Stay alert for aftershocks."
        return "Minor event. No action required."

    @staticmethod
    def _fire_action(dist: float, severity: str) -> str:
        if dist < 5: return "IMMEDIATE EVACUATION. Fire within 5km."
        if dist < 20: return "Prepare evacuation kit. Monitor updates."
        if dist < 50: return "Stay informed. Check air quality."
        return "Monitor situation. Fire detected in your region."

    @staticmethod
    def _flood_action(severity: str) -> str:
        if severity == "critical": return "EVACUATE to higher ground. Avoid floodwaters."
        if severity == "high": return "Move valuables to upper floors. Prepare to evacuate."
        if severity == "moderate": return "Monitor water levels. Avoid low-lying areas."
        return "Light rain expected. Stay aware of conditions."

    @staticmethod
    def _heat_action(severity: str) -> str:
        if severity == "critical": return "Extreme heat. Stay indoors with AC. Check on vulnerable."
        if severity == "high": return "Limit outdoor activity. Stay hydrated."
        if severity == "moderate": return "Warm conditions. Drink water regularly."
        return "Mild heat. Normal precautions."

    @staticmethod
    def _highest_severity(alerts: Dict) -> str:
        order = ["critical", "high", "moderate", "low", "none"]
        best = "none"
        for key in ("earthquakes", "fires", "floods", "weather_warnings"):
            for a in alerts.get(key, []):
                sev = a.get("severity", "low")
                if sev in order and order.index(sev) < order.index(best):
                    best = sev
        return best
