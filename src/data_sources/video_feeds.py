import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

from .base import BaseDataSource


class VideoFeedClient(BaseDataSource):
    """Simulated drone/CCTV video retrieval client."""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__(api_key=api_key, base_url="https://video.local")

    def health_check(self) -> bool:
        return True

    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        return {"videos": self.fetch_video_snippets(**kwargs)}

    def fetch_video_snippets(
        self,
        latitude: float,
        longitude: float,
        time_window_hours: int = 24,
        sources: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        sources = sources or ["drone", "cctv"]
        seed = self._stable_hash(f"{latitude:.4f}:{longitude:.4f}:{time_window_hours}")
        now = datetime.utcnow()
        videos = []

        for idx, source in enumerate(sources[:3]):
            start_offset = (seed >> (idx + 2)) % max(time_window_hours, 1)
            start_time = now - timedelta(hours=start_offset)
            end_time = start_time + timedelta(minutes=10)
            video_id = f"{source}:{latitude:.4f},{longitude:.4f}:{seed % 10000}:{idx}"
            url = f"{self.base_url}/feeds/{video_id}.mp4"

            videos.append(
                {
                    "video_id": video_id,
                    "source": source,
                    "start_time": start_time.isoformat() + "Z",
                    "end_time": end_time.isoformat() + "Z",
                    "url": url,
                }
            )

        return videos

    def _stable_hash(self, value: str) -> int:
        return int(hashlib.sha256(value.encode("utf-8")).hexdigest(), 16)
