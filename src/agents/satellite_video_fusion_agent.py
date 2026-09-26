from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING

from langchain_core.tools import tool

from .base import BaseAgent
from ..data_sources.satellite_imagery import SatelliteImageryClient
from ..data_sources.video_feeds import VideoFeedClient
from ..data_sources.clip_embedder import CLIPEmbedder

if TYPE_CHECKING:
    from ..memory import MemoryManager


satellite_client = SatelliteImageryClient()
video_client = VideoFeedClient()
clip_embedder = CLIPEmbedder()


@tool
def detect_satellite_anomalies(
    latitude: float,
    longitude: float,
    radius_km: float = 25.0,
    days: int = 7,
) -> str:
    """Detect vegetation or water anomalies from satellite imagery."""
    try:
        anomalies = satellite_client.detect_anomalies(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            days=days,
        )
        return f"Detected {len(anomalies)} satellite anomalies: {anomalies}"
    except Exception as exc:
        return f"Error: {str(exc)}"


@tool
def fetch_video_footage(
    latitude: float,
    longitude: float,
    time_window_hours: int = 24,
    sources: Optional[List[str]] = None,
) -> str:
    """Fetch nearby drone/CCTV footage around a location."""
    try:
        videos = video_client.fetch_video_snippets(
            latitude=latitude,
            longitude=longitude,
            time_window_hours=time_window_hours,
            sources=sources,
        )
        return f"Fetched {len(videos)} video clips: {videos}"
    except Exception as exc:
        return f"Error: {str(exc)}"


@tool
def compare_clip_embeddings(image_id: str, video_id: str) -> str:
    """Compare image/video embeddings and return a similarity score."""
    try:
        score = clip_embedder.similarity(image_id, video_id)
        return f"CLIP similarity {score:.3f} between {image_id} and {video_id}"
    except Exception as exc:
        return f"Error: {str(exc)}"


class SatelliteVideoFusionAgent(BaseAgent):

    def __init__(
        self,
        google_api_key: Optional[str] = None,
        gee_api_key: Optional[str] = None,
        video_api_key: Optional[str] = None,
        memory_manager: Optional['MemoryManager'] = None,
        enable_memory: bool = True,
    ):
        super().__init__("SatelliteVideoFusionAgent", google_api_key, memory_manager, enable_memory)
        if gee_api_key:
            satellite_client.api_key = gee_api_key
        if video_api_key:
            video_client.api_key = video_api_key

    def get_tools(self) -> List[Callable]:
        return [detect_satellite_anomalies, fetch_video_footage, compare_clip_embeddings]

    def get_system_prompt(self) -> str:
        return """You are a Satellite-Video Fusion agent for environmental anomaly detection.

You combine satellite change detection with nearby drone/CCTV footage confirmation.

Tools:
- detect_satellite_anomalies: Find vegetation or water anomalies by coordinates (Default: 25km radius, 7 days)
- fetch_video_footage: Pull nearby drone/CCTV clips for confirmation
- compare_clip_embeddings: Compare satellite and video evidence with CLIP similarity

STRATEGY:
1. Always call `detect_satellite_anomalies` first with the given coordinates.
2. Use default radius (25km) and days (7) if the user doesn't specify. DO NOT ASK FOR THEM.
3. Only if anomalies are found, call `fetch_video_footage`.

Return alerts with coordinates, timestamps, anomaly type, and confidence scores."""

    def get_alerts(
        self,
        latitude: float,
        longitude: float,
        radius_km: float = 25.0,
        days: int = 7,
        similarity_threshold: float = 0.6,
    ) -> List[Dict[str, Any]]:
        anomalies = satellite_client.detect_anomalies(
            latitude=latitude,
            longitude=longitude,
            radius_km=radius_km,
            days=days,
        )
        alerts: List[Dict[str, Any]] = []

        for anomaly in anomalies:
            coords = anomaly["coordinates"]
            videos = video_client.fetch_video_snippets(
                latitude=coords["lat"],
                longitude=coords["lon"],
                time_window_hours=24,
            )
            best_match = None
            best_score = 0.0
            for video in videos:
                score = clip_embedder.similarity(anomaly["image_id"], video["video_id"])
                if score > best_score:
                    best_score = score
                    best_match = video

            if best_match and best_score >= similarity_threshold:
                fusion_conf = round((anomaly["confidence"] + best_score) / 2, 3)
                alerts.append(
                    {
                        "type": "satellite_video_fusion",
                        "anomaly_type": anomaly["type"],
                        "coordinates": coords,
                        "timestamp": anomaly["timestamp"],
                        "satellite_confidence": anomaly["confidence"],
                        "video_match_score": round(best_score, 3),
                        "fusion_confidence": fusion_conf,
                        "satellite_image_id": anomaly["image_id"],
                        "video_id": best_match["video_id"],
                        "video_source": best_match["source"],
                        "video_url": best_match["url"],
                    }
                )

        return alerts
