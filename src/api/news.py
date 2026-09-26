"""
API endpoints for Climate News Intelligence.
"""

import os
import logging
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from ..news.models import (
    NewsArticle, NewsSearchRequest, NewsSearchResult,
    ArticleChatRequest, ArticleChatResponse, NewsBucket
)
from ..news.qdrant_manager import NewsQdrantManager
from ..news.chat import ArticleChatManager
from ..news.deep_research import DeepResearchManager
from ..news.ingestion.news_fetcher import NewsFetcher, NewsSource
from ..news.ingestion.article_processor import ArticleProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/news", tags=["Climate News"])

# Initialize managers (lazy initialization)
_qdrant_manager: Optional[NewsQdrantManager] = None
_chat_manager: Optional[ArticleChatManager] = None
_deep_research_manager: Optional[DeepResearchManager] = None
_news_fetcher: Optional[NewsFetcher] = None
_article_processor: Optional[ArticleProcessor] = None


def get_qdrant_manager() -> NewsQdrantManager:
    """Get or create Qdrant manager."""
    global _qdrant_manager
    if _qdrant_manager is None:
        try:
            _qdrant_manager = NewsQdrantManager()
        except Exception as e:
            logger.error(f"Failed to create NewsQdrantManager: {e}")
            # Create a degraded instance that will retry later
            _qdrant_manager = NewsQdrantManager.__new__(NewsQdrantManager)
            _qdrant_manager._available = False
            _qdrant_manager._last_failure_time = None
            _qdrant_manager._qdrant_client = None
            _qdrant_manager.rag_manager = None
            _qdrant_manager.collection_name = "climate_news"
            _qdrant_manager.qdrant_url = os.getenv("QDRANT_URL")
            _qdrant_manager.qdrant_api_key = os.getenv("QDRANT_API_KEY")
            _qdrant_manager.google_api_key = os.getenv("GOOGLE_API_KEY")
    return _qdrant_manager


def get_chat_manager() -> ArticleChatManager:
    """Get or create chat manager."""
    global _chat_manager
    if _chat_manager is None:
        qdrant_manager = get_qdrant_manager()
        _chat_manager = ArticleChatManager(qdrant_manager)
    return _chat_manager


def get_deep_research_manager() -> DeepResearchManager:
    """Get or create deep research manager."""
    global _deep_research_manager
    if _deep_research_manager is None:
        qdrant_manager = get_qdrant_manager()
        chat_manager = get_chat_manager()
        _deep_research_manager = DeepResearchManager(qdrant_manager, chat_manager)
    return _deep_research_manager


def get_news_fetcher() -> NewsFetcher:
    """Get or create news fetcher."""
    global _news_fetcher
    if _news_fetcher is None:
        _news_fetcher = NewsFetcher()
    return _news_fetcher


def get_article_processor() -> ArticleProcessor:
    """Get or create article processor."""
    global _article_processor
    if _article_processor is None:
        _article_processor = ArticleProcessor()
    return _article_processor


@router.get("/buckets")
async def list_buckets():
    """List all available source buckets."""
    buckets = [
        {"name": bucket.value, "description": f"Articles from {bucket.value} sources"}
        for bucket in NewsBucket
    ]
    return {"buckets": buckets}


@router.get("", response_model=List[NewsSearchResult])
async def search_news(
    query: Optional[str] = Query(None, description="Search query"),
    bucket: Optional[List[str]] = Query(None, description="Filter by bucket(s)"),
    limit: int = Query(20, ge=1, le=100, description="Number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    use_vector_search: bool = Query(True, description="Use vector similarity search"),
    recency_boost: bool = Query(True, description="Boost recent articles")
):
    """Search climate news articles."""
    try:
        qdrant_manager = get_qdrant_manager()
        
        search_request = NewsSearchRequest(
            query=query,
            bucket=bucket,
            limit=limit,
            offset=offset,
            use_vector_search=use_vector_search,
            recency_boost=recency_boost
        )
        
        results = qdrant_manager.search_articles(search_request)
        return results
    
    except Exception as e:
        logger.error(f"Error searching news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{article_id}", response_model=NewsArticle)
async def get_article(article_id: str):
    """Get a specific article by ID."""
    try:
        qdrant_manager = get_qdrant_manager()
        article = qdrant_manager.get_article_by_id(article_id)
        
        if not article:
            raise HTTPException(status_code=404, detail=f"Article {article_id} not found")
        
        return article
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving article {article_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/article/{article_id}", response_model=ArticleChatResponse)
async def chat_about_article(article_id: str, request: ArticleChatRequest):
    """Chat about a specific article."""
    try:
        # Ensure article_id matches
        request.article_id = article_id
        
        if request.deep_research:
            deep_research_manager = get_deep_research_manager()
            response = deep_research_manager.deep_research(request)
        else:
            chat_manager = get_chat_manager()
            response = chat_manager.chat(request)
        
        return response
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in article chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/article/{article_id}/history")
async def get_conversation_history(article_id: str, conversation_id: str):
    """Get conversation history for an article."""
    try:
        chat_manager = get_chat_manager()
        history = chat_manager._get_conversation_history(conversation_id)
        
        # Format history for frontend
        formatted_history = [
            {
                "role": msg.get("role", "user"),
                "content": msg.get("content", ""),
                "timestamp": msg.get("timestamp", "")
            }
            for msg in history
        ]
        
        return {
            "conversation_id": conversation_id,
            "article_id": article_id,
            "messages": formatted_history
        }
    
    except Exception as e:
        logger.error(f"Error retrieving conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest")
async def ingest_news(
    sources: Optional[List[str]] = None,
    validate_images: bool = True
):
    """Ingest news from configured sources."""
    try:
        fetcher = get_news_fetcher()
        processor = get_article_processor()
        qdrant_manager = get_qdrant_manager()
        
        # Determine sources to fetch
        if sources:
            news_sources = [NewsSource[s.upper()] for s in sources if s.upper() in NewsSource.__members__]
        else:
            news_sources = None  # Fetch all
        
        # Fetch articles
        logger.info("Fetching news articles...")
        raw_articles = fetcher.fetch_all_sources(news_sources)
        
        # Process articles
        logger.info("Processing articles...")
        articles = processor.process_articles(raw_articles)
        
        # Store in Qdrant
        stored_count = 0
        for article in articles:
            try:
                # Validate image if requested
                if validate_images:
                    article.image_url = fetcher.validate_image_url(article.image_url)
                
                # Chunk article
                chunks = processor.chunk_article(article)
                
                # Store chunks
                qdrant_manager.store_article_chunks(article, chunks)
                stored_count += 1
            except Exception as e:
                logger.error(f"Error storing article {article.id}: {e}")
        
        return {
            "status": "success",
            "fetched": len(raw_articles),
            "processed": len(articles),
            "stored": stored_count
        }
    
    except Exception as e:
        logger.error(f"Error ingesting news: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{article_id}/related")
async def get_related_articles(article_id: str, limit: int = Query(5, ge=1, le=20)):
    """Get articles related to a specific article."""
    try:
        qdrant_manager = get_qdrant_manager()
        related = qdrant_manager.get_related_articles(article_id, limit=limit)
        
        return {
            "article_id": article_id,
            "related_articles": [
                {
                    "id": r.id,
                    "title": r.title,
                    "summary": r.summary,
                    "source": r.source,
                    "url": r.url,
                    "published_at": r.published_at.isoformat(),
                    "image_url": r.image_url,
                    "bucket": r.bucket
                }
                for r in related
            ]
        }
    
    except Exception as e:
        logger.error(f"Error getting related articles: {e}")
        raise HTTPException(status_code=500, detail=str(e))
