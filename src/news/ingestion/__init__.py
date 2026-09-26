"""News ingestion module."""

from .news_fetcher import NewsFetcher, NewsSource
from .article_processor import ArticleProcessor

__all__ = ["NewsFetcher", "NewsSource", "ArticleProcessor"]
