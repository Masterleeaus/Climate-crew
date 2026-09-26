"""
Qdrant manager for climate news storage and retrieval.
"""

import os
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct, Filter, FieldCondition,
    MatchValue, MatchAny, Range, PayloadSchemaType
)
import numpy as np

from .models import NewsArticle, NewsChunk, NewsSearchRequest, NewsSearchResult
from ..rag.rag_manager import RAGManager

logger = logging.getLogger(__name__)

from dotenv import load_dotenv

load_dotenv()


class NewsQdrantManager:
    """Manage news articles in Qdrant vector database."""
    
    # Retry cooldown: wait this many seconds before retrying after a connection failure
    RETRY_COOLDOWN_SECONDS = 60
    
    def __init__(
        self,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        collection_name: str = "climate_news",
        google_api_key: Optional[str] = None,
        embedding_model: str = "gemini-embedding-001"
    ):
        self.qdrant_url = qdrant_url or os.getenv("QDRANT_URL")
        self.qdrant_api_key = qdrant_api_key or os.getenv("QDRANT_API_KEY")
        self.qdrant_path = os.getenv("QDRANT_PATH")
        self.collection_name = collection_name
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self._available = False
        self._last_failure_time: Optional[float] = None
        
        # Initialize Qdrant client
        if not self.qdrant_path and (not self.qdrant_url or not self.qdrant_api_key):
            logger.warning("Qdrant not configured (URL/Key or Path missing). News features will be unavailable.")
            self._qdrant_client = None
            self.rag_manager = None
            return
        
        # Initialize RAGManager for embeddings and Qdrant connection
        self.rag_manager = RAGManager(
            qdrant_url=self.qdrant_url,
            qdrant_api_key=self.qdrant_api_key,
            collection_name=collection_name,
            google_api_key=self.google_api_key,
            embedding_model=embedding_model
        )
        
        # Share Qdrant client with RAGManager to avoid local lock issues
        if self.rag_manager._ensure_initialized():
             self._qdrant_client = self.rag_manager._qdrant_client
        else:
             self._qdrant_client = None
             logger.warning("Failed to initialize RAGManager, NewsQdrantManager will be unavailable")
        
        self._try_initialize()
    
    def _try_initialize(self):
        """Attempt to initialize the Qdrant connection. Safe to call multiple times."""
        import time as _time
        try:
            self._ensure_collection_exists()
            self._available = True
            self._last_failure_time = None
            logger.info("NewsQdrantManager initialized successfully")
        except Exception as e:
            self._available = False
            self._last_failure_time = _time.time()
            logger.warning(f"Qdrant unavailable, news features degraded: {e}")
    
    def _is_available(self) -> bool:
        """Check if Qdrant is available, retrying after cooldown if previously failed."""
        if self._available:
            return True
        if self._qdrant_client is None:
            return False
        
        import time as _time
        # If we haven't failed yet, or cooldown has elapsed, retry
        if self._last_failure_time is None or (
            _time.time() - self._last_failure_time > self.RETRY_COOLDOWN_SECONDS
        ):
            self._try_initialize()
        
        return self._available
    
    def _ensure_collection_exists(self):
        """Ensure the climate_news collection exists with correct dimension."""
        # RAGManager already handles collection creation/verification with dimension checking
        # Just ensure it's initialized, which will create/verify the collection
        self.rag_manager._ensure_initialized()
        
        # Ensure payload indexes exist for efficient filtering
        self._ensure_payload_indexes()
        
        # Log collection status for visibility
        collection_info = self._qdrant_client.get_collection(self.collection_name)
        existing_dim = collection_info.config.params.vectors.size
        logger.info(f"Collection {self.collection_name} ready (size: {collection_info.points_count}, dim: {existing_dim})")
    
    def _ensure_payload_indexes(self):
        """Ensure required payload indexes exist for efficient filtering."""
        try:
            # Create index for article_id (used for filtering by article)
            try:
                self._qdrant_client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="article_id",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                logger.info("Created payload index for 'article_id'")
            except Exception as e:
                # Index might already exist, which is fine
                if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                    logger.debug(f"Could not create index for 'article_id' (may already exist): {e}")
            
            # Create index for bucket (used for filtering by bucket)
            try:
                self._qdrant_client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name="bucket",
                    field_schema=PayloadSchemaType.KEYWORD
                )
                logger.info("Created payload index for 'bucket'")
            except Exception as e:
                if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                    logger.debug(f"Could not create index for 'bucket' (may already exist): {e}")
            
        except Exception as e:
            logger.warning(f"Error ensuring payload indexes: {e}")
    
    def _mark_unavailable(self):
        """Mark Qdrant as unavailable and record failure time."""
        import time as _time
        self._available = False
        self._last_failure_time = _time.time()
        logger.warning("Qdrant marked unavailable, will retry after cooldown")
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text."""
        return self.rag_manager._get_embedding(text)
    
    def store_article_chunks(self, article: NewsArticle, chunks: List[NewsChunk]):
        """Store article chunks in Qdrant."""
        if not self._is_available():
            logger.warning("Qdrant unavailable, cannot store article chunks")
            return
        
        points = []
        
        for chunk in chunks:
            # Generate embedding
            try:
                embedding = self._get_embedding(chunk.text)
            except Exception as e:
                logger.error(f"Error generating embedding for chunk {chunk.chunk_id}: {e}")
                continue
            
            # Create point payload
            payload = {
                "article_id": article.id,
                "chunk_id": chunk.chunk_id,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
                "title": article.title,
                "source": article.source,
                "url": article.url,
                "published_at": article.published_at.isoformat(),
                "bucket": article.bucket,
                "tags": article.tags,
                "image_url": article.image_url,
                "summary": article.summary or ""
            }
            
            point = PointStruct(
                id=hash(chunk.chunk_id) % (2**63),  # Qdrant requires int64
                vector=embedding,
                payload=payload
            )
            points.append(point)
        
        if points:
            try:
                self._qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=points
                )
                logger.info(f"Stored {len(points)} chunks for article {article.id}")
            except Exception as e:
                logger.error(f"Error storing chunks in Qdrant: {e}")
                raise
    
    def search_articles(
        self,
        request: NewsSearchRequest
    ) -> List[NewsSearchResult]:
        """Search articles with vector similarity and filters."""
        results = []
        
        # Check if Qdrant is available (with retry cooldown)
        if not self._is_available():
            logger.debug("Qdrant unavailable, returning empty news results")
            return results
        
        # Check if collection exists and has data
        try:
            collection_info = self._qdrant_client.get_collection(self.collection_name)
            if collection_info.points_count == 0:
                logger.warning(f"Collection {self.collection_name} is empty. No articles to search.")
                return results
        except Exception as e:
            logger.error(f"Error checking collection {self.collection_name}: {e}")
            self._mark_unavailable()
            return results
        
        # Build filter
        query_filter = None
        conditions = []
        
        # Bucket filter
        if request.bucket:
            conditions.append(
                FieldCondition(
                    key="bucket",
                    match=MatchAny(any=request.bucket)
                )
            )
        
        if conditions:
            query_filter = Filter(must=conditions)
        
        # Vector search
        if request.query and request.use_vector_search:
            try:
                # Get query embedding
                try:
                    query_embedding = self._get_embedding(request.query)
                except Exception as e:
                    logger.error(f"Error generating embedding for query: {e}")
                    # Fall through to keyword search or recent articles
                    query_embedding = None
                
                if query_embedding:
                    search_results = self._qdrant_client.query_points(
                        collection_name=self.collection_name,
                        query=query_embedding,
                        query_filter=query_filter,
                        limit=request.limit * 2,  # Get more for deduplication
                        score_threshold=0.3
                    ).points
                else:
                    search_results = []
                
                # Deduplicate by article_id and apply recency boost
                seen_articles = {}
                for result in search_results:
                    try:
                        article_id = result.payload.get("article_id")
                        if not article_id:
                            continue
                        if article_id not in seen_articles:
                            # Apply recency boost if enabled
                            score = result.score
                            if request.recency_boost:
                                published_at_str = result.payload.get("published_at", "")
                                try:
                                    published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
                                    days_ago = (datetime.utcnow() - published_at.replace(tzinfo=None)).days
                                    recency_factor = max(0.1, 1.0 - (days_ago / 30.0))  # Decay over 30 days
                                    score = score * (1.0 + recency_factor * 0.2)  # Boost up to 20%
                                except:
                                    pass
                            
                            seen_articles[article_id] = {
                                "score": score,
                                "payload": result.payload
                            }
                    except (AttributeError, KeyError) as e:
                        logger.debug(f"Error processing search result: {e}")
                        continue
                
                # Sort by score and limit
                sorted_articles = sorted(
                    seen_articles.items(),
                    key=lambda x: x[1]["score"],
                    reverse=True
                )[:request.limit]
                
                for article_id, data in sorted_articles:
                    try:
                        payload = data["payload"]
                        image_url = payload.get("image_url")
                        # Ensure we always have an image URL
                        if not image_url or image_url.strip() == "":
                            image_url = "https://via.placeholder.com/800x450?text=Climate+News"
                        
                        # Parse published_at with error handling
                        published_at_str = payload.get("published_at")
                        if published_at_str:
                            try:
                                published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
                            except (ValueError, AttributeError):
                                published_at = datetime.utcnow()
                        else:
                            published_at = datetime.utcnow()
                        
                        result = NewsSearchResult(
                            id=payload.get("article_id", ""),
                            title=payload.get("title", ""),
                            summary=payload.get("summary"),
                            source=payload.get("source", ""),
                            url=payload.get("url", ""),
                            published_at=published_at,
                            image_url=image_url,
                            bucket=payload.get("bucket", "Mainstream Media"),
                            tags=payload.get("tags", []) or [],
                            score=data["score"]
                        )
                        results.append(result)
                    except Exception as e:
                        logger.warning(f"Error creating search result for article {article_id}: {e}")
                        continue
            
            except Exception as e:
                logger.error(f"Error in vector search: {e}")
        
        # Keyword search fallback or supplement
        if not results and request.query:
            # Use Qdrant's scroll with keyword matching
            try:
                scroll_results = self._qdrant_client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=query_filter,
                    limit=request.limit * 10,
                    with_payload=True,
                    with_vectors=False
                )
                
                # Handle scroll_results structure (can be tuple or list)
                points = scroll_results[0] if isinstance(scroll_results, tuple) else scroll_results
                
                # Simple keyword matching
                query_lower = request.query.lower()
                matched = {}
                
                for point in points:
                    try:
                        payload = point.payload
                        text = (payload.get("title", "") + " " + payload.get("text", "")).lower()
                        
                        if query_lower in text:
                            article_id = payload.get("article_id")
                            if article_id and article_id not in matched:
                                matched[article_id] = payload
                    except (AttributeError, KeyError) as e:
                        logger.debug(f"Error processing point in keyword search: {e}")
                        continue
                
                # Convert to results
                for article_id, payload in list(matched.items())[:request.limit]:
                    try:
                        image_url = payload.get("image_url")
                        # Ensure we always have an image URL
                        if not image_url or image_url.strip() == "":
                            image_url = "https://via.placeholder.com/800x450?text=Climate+News"
                        
                        # Parse published_at with error handling
                        published_at_str = payload.get("published_at")
                        if published_at_str:
                            try:
                                published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
                            except (ValueError, AttributeError):
                                published_at = datetime.utcnow()
                        else:
                            published_at = datetime.utcnow()
                        
                        result = NewsSearchResult(
                            id=payload.get("article_id", ""),
                            title=payload.get("title", ""),
                            summary=payload.get("summary"),
                            source=payload.get("source", ""),
                            url=payload.get("url", ""),
                            published_at=published_at,
                            image_url=image_url,
                            bucket=payload.get("bucket", "Mainstream Media"),
                            tags=payload.get("tags", []) or []
                        )
                        results.append(result)
                    except Exception as e:
                        logger.warning(f"Error creating search result for article {article_id}: {e}")
                        continue
            
            except Exception as e:
                logger.error(f"Error in keyword search: {e}")
        
        # If no query, just return recent articles
        if not request.query:
            try:
                scroll_results = self._qdrant_client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=query_filter,
                    limit=request.limit * 2,  # Get more for deduplication
                    with_payload=True,
                    with_vectors=False
                )
                
                # Handle scroll_results structure (can be tuple or list)
                points = scroll_results[0] if isinstance(scroll_results, tuple) else scroll_results
                
                seen_articles = {}
                for point in points:
                    try:
                        article_id = point.payload.get("article_id")
                        if article_id and article_id not in seen_articles:
                            seen_articles[article_id] = point.payload
                    except (AttributeError, KeyError) as e:
                        logger.debug(f"Error processing point: {e}")
                        continue
                
                # Sort by published_at
                articles_list = []
                for article_id, payload in seen_articles.items():
                    try:
                        published_at_str = payload.get("published_at")
                        if published_at_str:
                            try:
                                published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
                            except (ValueError, AttributeError):
                                published_at = datetime.utcnow()
                        else:
                            published_at = datetime.utcnow()
                        articles_list.append((published_at, payload))
                    except Exception as e:
                        logger.debug(f"Error parsing date for article {article_id}: {e}")
                        articles_list.append((datetime.utcnow(), payload))
                
                articles_list.sort(key=lambda x: x[0], reverse=True)
                
                for _, payload in articles_list[:request.limit]:
                    try:
                        image_url = payload.get("image_url")
                        # Ensure we always have an image URL
                        if not image_url or image_url.strip() == "":
                            image_url = "https://via.placeholder.com/800x450?text=Climate+News"
                        
                        # Parse published_at with error handling
                        published_at_str = payload.get("published_at")
                        if published_at_str:
                            try:
                                published_at = datetime.fromisoformat(published_at_str.replace("Z", "+00:00"))
                            except (ValueError, AttributeError):
                                published_at = datetime.utcnow()
                        else:
                            published_at = datetime.utcnow()
                        
                        result = NewsSearchResult(
                            id=payload.get("article_id", ""),
                            title=payload.get("title", ""),
                            summary=payload.get("summary"),
                            source=payload.get("source", ""),
                            url=payload.get("url", ""),
                            published_at=published_at,
                            image_url=image_url,
                            bucket=payload.get("bucket", "Mainstream Media"),
                            tags=payload.get("tags", []) or []
                        )
                        results.append(result)
                    except Exception as e:
                        logger.warning(f"Error creating search result: {e}")
                        continue
            
            except Exception as e:
                logger.error(f"Error fetching recent articles: {e}")
                import traceback
                logger.debug(traceback.format_exc())
        
        return results
    
    def get_article_by_id(self, article_id: str) -> Optional[NewsArticle]:
        """Retrieve full article by ID."""
        if not self._is_available():
            logger.debug("Qdrant unavailable, cannot retrieve article")
            return None
        try:
            scroll_results = self._qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="article_id",
                            match=MatchValue(value=article_id)
                        )
                    ]
                ),
                limit=1,
                with_payload=True,
                with_vectors=False
            )
            
            if scroll_results[0]:
                payload = scroll_results[0][0].payload
                
                # Reconstruct full content from chunks
                all_chunks = self._get_all_chunks_for_article(article_id)
                content = " ".join([chunk.get("text", "") for chunk in all_chunks])
                
                article = NewsArticle(
                    id=payload.get("article_id"),
                    title=payload.get("title", ""),
                    content=content or payload.get("text", ""),
                    summary=payload.get("summary"),
                    source=payload.get("source", ""),
                    url=payload.get("url", ""),
                    published_at=datetime.fromisoformat(
                        payload.get("published_at", datetime.utcnow().isoformat())
                    ),
                    tags=payload.get("tags", []),
                    image_url=payload.get("image_url"),
                    bucket=payload.get("bucket", "Mainstream Media")
                )
                return article
        
        except Exception as e:
            logger.error(f"Error retrieving article {article_id}: {e}")
        
        return None
    
    def _get_all_chunks_for_article(self, article_id: str) -> List[Dict]:
        """Get all chunks for an article, sorted by chunk_index."""
        try:
            scroll_results = self._qdrant_client.scroll(
                collection_name=self.collection_name,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="article_id",
                            match=MatchValue(value=article_id)
                        )
                    ]
                ),
                limit=100,
                with_payload=True,
                with_vectors=False
            )
            
            chunks = []
            for point in scroll_results[0]:
                payload = point.payload
                chunks.append({
                    "text": payload.get("text", ""),
                    "chunk_index": payload.get("chunk_index", 0)
                })
            
            chunks.sort(key=lambda x: x["chunk_index"])
            return chunks
        
        except Exception as e:
            logger.error(f"Error retrieving chunks for article {article_id}: {e}")
            return []
    
    def get_related_articles(
        self,
        article_id: str,
        limit: int = 5
    ) -> List[NewsSearchResult]:
        """Get articles related to a given article."""
        if not self._is_available():
            return []
        article = self.get_article_by_id(article_id)
        if not article:
            return []
        
        # Use article title and summary for similarity search
        query_text = f"{article.title} {article.summary or ''}"
        
        request = NewsSearchRequest(
            query=query_text,
            limit=limit + 1,  # +1 to exclude the original article
            use_vector_search=True
        )
        
        results = self.search_articles(request)
        
        # Filter out the original article
        return [r for r in results if r.id != article_id][:limit]
