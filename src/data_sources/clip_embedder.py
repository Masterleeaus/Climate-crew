import hashlib
import math
from typing import List


class CLIPEmbedder:
    """Lightweight, deterministic CLIP-like embedder for demo purposes."""

    def __init__(self, dim: int = 32):
        self.dim = dim

    def embed(self, content_id: str) -> List[float]:
        digest = hashlib.sha256(content_id.encode("utf-8")).digest()
        raw = (digest * ((self.dim // len(digest)) + 1))[: self.dim]
        return [b / 255.0 for b in raw]

    def similarity(self, a_id: str, b_id: str) -> float:
        a_vec = self.embed(a_id)
        b_vec = self.embed(b_id)
        dot = sum(a * b for a, b in zip(a_vec, b_vec))
        a_norm = math.sqrt(sum(a * a for a in a_vec)) or 1.0
        b_norm = math.sqrt(sum(b * b for b in b_vec)) or 1.0
        return dot / (a_norm * b_norm)
