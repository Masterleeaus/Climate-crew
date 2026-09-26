"""
Climate News Intelligence Module
Handles news ingestion, storage, retrieval, and chat functionality.
"""

from .models import NewsArticle, NewsChunk, BucketConfig
from .qdrant_manager import NewsQdrantManager
from .ingestion.news_fetcher import NewsFetcher
from .ingestion.article_processor import ArticleProcessor
from .chat import ArticleChatManager
from .deep_research import DeepResearchManager

__all__ = [
    "NewsArticle",
    "NewsChunk",
    "BucketConfig",
    "NewsQdrantManager",
    "NewsFetcher",
    "ArticleProcessor",
    "ArticleChatManager",
    "DeepResearchManager",
]
