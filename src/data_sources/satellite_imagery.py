import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from .base import BaseDataSource


class SatelliteImageryClient(BaseDataSource):
    """Simulated Google Earth Engine change detection client."""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key, base_url="https://earthengine.googleapis.com")

    def health_check(self) -> bool:
        return True

    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        return {"anomalies": self.detect_anomalies(**kwargs)}

    def detect_anomalies(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 25.0,
        days: int = 7,
        anomaly_types: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        anomaly_types = anomaly_types or ["vegetation_loss", "water_change"]
        seed = self._stable_hash(f"{latitude:.4f}:{longitude:.4f}:{radius_km}:{days}")
        count = 1 + (seed % min(3, len(anomaly_types)))
        anomalies = []
        now = datetime.utcnow()

        for idx in range(count):
            anomaly_type = anomaly_types[idx % len(anomaly_types)]
            confidence = 0.45 + ((seed >> (idx + 2)) % 45) / 100.0
            change_pct = 3 + ((seed >> (idx + 5)) % 120) / 10.0
            offset_lat = ((seed >> (idx + 7)) % 200 - 100) / 10000.0
            offset_lon = ((seed >> (idx + 9)) % 200 - 100) / 10000.0
            ts = now - timedelta(hours=(seed >> (idx + 3)) % 24)
            image_id = f"gee:{latitude:.4f},{longitude:.4f}:{anomaly_type}:{idx}"

            anomalies.append(
                {
                    "id": f"anom-{seed % 10000}-{idx}",
                    "type": anomaly_type,
                    "change_percent": round(change_pct, 2),
                    "confidence": round(min(confidence, 0.95), 3),
                    "coordinates": {
                        "lat": round(latitude + offset_lat, 6),
                        "lon": round(longitude + offset_lon, 6),
                    },
                    "radius_km": radius_km,
                    "timestamp": ts.isoformat() + "Z",
                    "image_id": image_id,
                    "source": "google_earth_engine",
                }
            )

        return anomalies

    def _stable_hash(self, value: str) -> int:
        return int(hashlib.sha256(value.encode("utf-8")).hexdigest(), 16)
