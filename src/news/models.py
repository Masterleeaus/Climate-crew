"""
Pydantic models for Climate News Intelligence.
"""

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class NewsBucket(str, Enum):
    """Source bucket categories."""
    MAINSTREAM_MEDIA = "Mainstream Media"
    SCIENTIFIC_JOURNALS = "Scientific Journals"
    FINANCIAL_NEWS = "Financial News"
    NGOS = "NGOs"
    BLOGS = "Blogs"
    GOVERNMENT = "Government"
    INTERNATIONAL_ORGS = "International Organizations"


class BucketConfig(BaseModel):
    """Configuration for a source bucket."""
    name: str
    sources: List[str] = Field(default_factory=list)
    description: Optional[str] = None


class NewsArticle(BaseModel):
    """Normalized news article model."""
    id: str
    title: str
    content: str
    summary: Optional[str] = None
    source: str
    url: str
    published_at: datetime
    tags: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    bucket: str = Field(default="Mainstream Media")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NewsChunk(BaseModel):
    """Chunk of a news article for vector storage."""
    chunk_id: str
    article_id: str
    text: str
    chunk_index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)


class NewsSearchRequest(BaseModel):
    """Request model for news search."""
    query: Optional[str] = None
    bucket: Optional[List[str]] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    use_vector_search: bool = True
    recency_boost: bool = True


class NewsSearchResult(BaseModel):
    """Result model for news search."""
    id: str
    title: str
    summary: Optional[str] = None
    source: str
    url: str
    published_at: datetime
    image_url: Optional[str] = None
    bucket: str
    tags: List[str] = Field(default_factory=list)
    score: Optional[float] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ArticleChatRequest(BaseModel):
    """Request model for article chat."""
    message: str
    article_id: str
    deep_research: bool = False
    conversation_id: Optional[str] = None


class ArticleChatResponse(BaseModel):
    """Response model for article chat."""
    answer: str
    citations: List[Dict[str, str]] = Field(default_factory=list)
class NewsArticleResponse(NewsSearchResult):
    """Response model for news article summary."""
    pass


class NewsArticleDetailResponse(NewsArticle):
    """Response model for full news article detail."""
    pass

