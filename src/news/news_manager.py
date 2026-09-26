"""
News Manager for Climate News Intelligence.
Handles ingestion, storage, retrieval, and chat functionality.
"""

import os
import logging
import hashlib
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta

from ..rag.rag_manager import RAGManager
from ..rag.text_chunker import TextChunker
from ..data_sources.news_sources import NewsIngestionService, NewsArticle
from .models import NewsArticleResponse, NewsArticleDetailResponse

logger = logging.getLogger(__name__)


class NewsManager:
    """Manage climate news ingestion, storage, and retrieval."""
    
    def __init__(
        self,
        qdrant_url: Optional[str] = None,
        qdrant_api_key: Optional[str] = None,
        google_api_key: Optional[str] = None,
        collection_name: str = "climate_news"
    ):
        """
        Initialize News Manager.
        
        Args:
            qdrant_url: Qdrant server URL
            qdrant_api_key: Qdrant API key
            google_api_key: Google API key for embeddings
            collection_name: Qdrant collection name
        """
        self.collection_name = collection_name
        self.ingestion_service = NewsIngestionService()
        
        # Initialize RAG manager for news collection
        self.rag_manager = RAGManager(
            qdrant_url=qdrant_url,
            qdrant_api_key=qdrant_api_key,
            collection_name=collection_name,
            google_api_key=google_api_key,
            use_reranker=True,
            enable_multihop=False  # Disable multihop for news retrieval
        )
        
        # Initialize chunker
        self.chunker = TextChunker(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # In-memory article cache (for quick retrieval by ID)
        self._article_cache: Dict[str, Dict] = {}
        
        # Initialize Qdrant collection
        self._ensure_collection_initialized()
    
    def _ensure_collection_initialized(self):
        """Ensure Qdrant collection is initialized."""
        try:
            self.rag_manager._ensure_initialized()
            logger.info(f"News collection '{self.collection_name}' initialized")
        except Exception as e:
            logger.error(f"Failed to initialize news collection: {e}")
    
    def ingest_news(
        self,
        limit_per_source: int = 50,
        days_back: int = 7,
        validate_images: bool = True
    ) -> int:
        """
        Ingest news articles from all sources.
        
        Args:
            limit_per_source: Maximum articles per source
            days_back: Number of days to look back
            validate_images: Whether to validate image URLs
            
        Returns:
            Number of articles ingested
        """
        logger.info("Starting news ingestion...")
        
        # Fetch articles
        articles = self.ingestion_service.fetch_all_news(
            limit_per_source=limit_per_source,
            days_back=days_back
        )
        
        if not articles:
            logger.warning("No articles fetched")
            return 0
        
        # Validate images
        if validate_images:
            for article in articles:
                article.image_url = self.ingestion_service.validate_image_url(article.image_url)
        
        # Prepare documents for indexing
        documents = []
        for article in articles:
            # Create full text for chunking
            full_text = f"{article.title}\n\n{article.summary}\n\n{article.content}"
            
            # Chunk the article
            chunks = self.chunker.chunk_text(
                full_text,
                metadata={
                    "article_id": article.id,
                    "title": article.title,
                    "source": article.source,
                    "url": article.url,
                    "published_at": article.published_at.isoformat(),
                    "tags": article.tags,
                    "bucket": article.bucket,
                    "image_url": article.image_url or "",
                    "summary": article.summary
                }
            )
            
            documents.extend(chunks)
            
            # Cache article metadata
            self._article_cache[article.id] = {
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "summary": article.summary,
                "source": article.source,
                "url": article.url,
                "published_at": article.published_at.isoformat(),
                "tags": article.tags,
                "image_url": article.image_url,
                "bucket": article.bucket
            }
        
        # Index chunks into Qdrant
        indexed_count = self.rag_manager.index_documents(documents)
        
        logger.info(f"Ingested {len(articles)} articles ({indexed_count} chunks indexed)")
        return len(articles)
    
    def search_news(
        self,
        query: Optional[str] = None,
        bucket: Optional[str] = None,
        tags: Optional[List[str]] = None,
        limit: int = 20,
        days_back: Optional[int] = None
    ) -> List[NewsArticleResponse]:
        """
        Search for news articles.
        
        Args:
            query: Search query (semantic search)
            bucket: Filter by source bucket
            tags: Filter by tags
            limit: Maximum results
            days_back: Filter by recency
            
        Returns:
            List of news articles
        """
        # Build filter
        filter_metadata = {}
        if bucket:
            filter_metadata["bucket"] = bucket
        if tags:
            filter_metadata["tags"] = tags[0] if len(tags) == 1 else None  # Qdrant supports single value
        
        # Search using RAG manager
        if query:
            search_results = self.rag_manager.search(
                query=query,
                limit=limit * 2,  # Get more for deduplication
                filter_metadata=filter_metadata if filter_metadata else None
            )
        else:
            # No query - retrieve recent articles
            search_results = self._get_recent_articles(limit, filter_metadata, days_back)
        
        # Deduplicate by article_id and convert to responses
        seen_article_ids = set()
        articles = []
        
        for result in search_results:
            article_id = result.get("metadata", {}).get("article_id")
            if not article_id or article_id in seen_article_ids:
                continue
            
            seen_article_ids.add(article_id)
            
            # Get article from cache or metadata
            article_data = self._article_cache.get(article_id)
            if not article_data:
                # Reconstruct from metadata
                metadata = result.get("metadata", {})
                article_data = {
                    "id": article_id,
                    "title": metadata.get("title", ""),
                    "content": "",  # Not available in chunks
                    "summary": metadata.get("summary", ""),
                    "source": metadata.get("source", ""),
                    "url": metadata.get("url", ""),
                    "published_at": metadata.get("published_at", datetime.now().isoformat()),
                    "tags": metadata.get("tags", []),
                    "image_url": metadata.get("image_url"),
                    "bucket": metadata.get("bucket", "Mainstream Media")
                }
            
            # Apply recency filter
            if days_back:
                published_at = datetime.fromisoformat(article_data["published_at"])
                if (datetime.now() - published_at).days > days_back:
                    continue
            
            # Apply tag filter
            if tags and not any(tag in article_data.get("tags", []) for tag in tags):
                continue
            
            articles.append(NewsArticleResponse(**article_data))
            
            if len(articles) >= limit:
                break
        
        # Sort by recency (boost recent articles)
        articles.sort(
            key=lambda x: datetime.fromisoformat(x.published_at.isoformat()),
            reverse=True
        )
        
        return articles[:limit]
    
    def _get_recent_articles(
        self,
        limit: int,
        filter_metadata: Optional[Dict] = None,
        days_back: Optional[int] = None
    ) -> List[Dict]:
        """Get recent articles without semantic search."""
        # Use a generic query to retrieve articles
        results = self.rag_manager.search(
            query="climate news",
            limit=limit * 3,
            filter_metadata=filter_metadata
        )
        
        # Filter by recency
        if days_back:
            filtered = []
            cutoff_date = datetime.now() - timedelta(days=days_back)
            for result in results:
                published_str = result.get("metadata", {}).get("published_at")
                if published_str:
                    try:
                        published_at = datetime.fromisoformat(published_str)
                        if published_at >= cutoff_date:
                            filtered.append(result)
                    except Exception:
                        filtered.append(result)
            return filtered
        
        return results
    
    def get_article(self, article_id: str) -> Optional[NewsArticleDetailResponse]:
        """
        Get detailed article by ID.
        
        Args:
            article_id: Article ID
            
        Returns:
            Article details or None
        """
        # Check cache first
        article_data = self._article_cache.get(article_id)
        if article_data:
            return NewsArticleDetailResponse(**article_data)
        
        # Search Qdrant for article chunks
        results = self.rag_manager.search(
            query="",  # Empty query with filter
            limit=100,
            filter_metadata={"article_id": article_id}
        )
        
        if not results:
            return None
        
        # Reconstruct article from chunks
        metadata = results[0].get("metadata", {})
        chunks = [r.get("text", "") for r in results]
        content = "\n\n".join(chunks)
        
        article_data = {
            "id": article_id,
            "title": metadata.get("title", ""),
            "content": content,
            "summary": metadata.get("summary", ""),
            "source": metadata.get("source", ""),
            "url": metadata.get("url", ""),
            "published_at": metadata.get("published_at", datetime.now().isoformat()),
            "tags": metadata.get("tags", []),
            "image_url": metadata.get("image_url"),
            "bucket": metadata.get("bucket", "Mainstream Media")
        }
        
        return NewsArticleDetailResponse(**article_data)
    
    def chat_about_article(
        self,
        article_id: str,
        message: str,
        deep_research: bool = False
    ) -> Dict[str, Any]:
        """
        Chat about a specific article with optional deep research.
        
        Args:
            article_id: Article ID
            message: User message
            deep_research: Enable deep research mode
            
        Returns:
            Chat response with answer, citations, and related articles
        """
        # Get article
        article = self.get_article(article_id)
        if not article:
            return {
                "answer": "Article not found.",
                "citations": None,
                "related_articles": None
            }
        
        if deep_research:
            return self._deep_research_chat(article, message)
        else:
            return self._single_article_chat(article, message)
    
    def _single_article_chat(self, article: NewsArticleDetailResponse, message: str) -> Dict[str, Any]:
        """Chat about single article only."""
        # Search for relevant chunks from this article
        results = self.rag_manager.search(
            query=message,
            limit=5,
            filter_metadata={"article_id": article.id}
        )
        
        # Build context from retrieved chunks
        context_parts = [f"Article: {article.title}\nSource: {article.source}\n\n"]
        for result in results:
            context_parts.append(result.get("text", ""))
        
        context = "\n\n".join(context_parts)
        
        # Generate answer using LLM
        answer = self._generate_answer(message, context, article)
        
        return {
            "answer": answer,
            "citations": [article.url],
            "related_articles": None
        }
    
    def _deep_research_chat(
        self,
        article: NewsArticleDetailResponse,
        message: str
    ) -> Dict[str, Any]:
        """Deep research mode: expand beyond single article."""
        # Search for related articles
        related_results = self.rag_manager.search(
            query=message,
            limit=10,
            filter_metadata=None  # Search across all articles
        )
        
        # Get article IDs from results
        related_article_ids = set()
        for result in related_results:
            aid = result.get("metadata", {}).get("article_id")
            if aid and aid != article.id:
                related_article_ids.add(aid)
        
        # Build context from original article + related chunks
        context_parts = [
            f"Primary Article: {article.title}\nSource: {article.source}\n\n{article.content[:2000]}"
        ]
        
        for result in related_results[:5]:
            context_parts.append(f"\n\nRelated Information:\n{result.get('text', '')}")
        
        context = "\n\n".join(context_parts)
        
        # Generate comprehensive answer
        answer = self._generate_answer(message, context, article, deep_research=True)
        
        # Get related articles
        related_articles = []
        for aid in list(related_article_ids)[:5]:
            related_article = self.get_article(aid)
            if related_article:
                related_articles.append(NewsArticleResponse(**related_article.dict()))
        
        # Collect citations
        citations = [article.url]
        citations.extend([a.url for a in related_articles])
        
        return {
            "answer": answer,
            "citations": citations,
            "related_articles": related_articles
        }
    
    def _generate_answer(
        self,
        message: str,
        context: str,
        article: NewsArticleDetailResponse,
        deep_research: bool = False
    ) -> str:
        """Generate answer using LLM."""
        try:
            from google import genai
            from google.genai import types
            
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                return "LLM not configured. Please set GOOGLE_API_KEY."
            
            client = genai.Client(api_key=google_api_key)
            
            prompt = f"""You are a climate news intelligence assistant. Answer the user's question based on the provided article context.

Article Context:
{context}

User Question: {message}

Provide a clear, accurate answer based on the article. {"Include insights from related articles if relevant." if deep_research else "Focus only on the provided article."}

Answer:"""
            
            config = None
            if types:
                try:
                    config = types.GenerateContentConfig(temperature=0.7)
                except Exception:
                    pass
            
            response = client.models.generate_content(
                model="gemini-2.0-flash-001",
                contents=prompt,
                config=config
            )
            
            if hasattr(response, 'text'):
                return response.text
            elif isinstance(response, dict):
                return response.get('text', '') or response.get('content', '')
            else:
                return str(response)
                
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"I apologize, but I encountered an error generating a response: {str(e)}"
    
    def get_buckets(self) -> List[Dict[str, Any]]:
        """Get list of available source buckets with counts."""
        buckets = {
            "Mainstream Media": 0,
            "Scientific Journals": 0,
            "Financial News": 0,
            "NGOs": 0,
            "Blogs": 0
        }
        
        # Count articles per bucket from cache
        for article_data in self._article_cache.values():
            bucket = article_data.get("bucket", "Mainstream Media")
            if bucket in buckets:
                buckets[bucket] += 1
        
        return [
            {
                "name": name,
                "description": self._get_bucket_description(name),
                "article_count": count
            }
            for name, count in buckets.items()
        ]
    
    def _get_bucket_description(self, bucket: str) -> str:
        """Get description for bucket."""
        descriptions = {
            "Mainstream Media": "Major news outlets like Reuters, BBC, Guardian, AP, Bloomberg",
            "Scientific Journals": "Peer-reviewed research and scientific publications",
            "Financial News": "Financial and business-focused climate coverage",
            "NGOs": "Non-governmental organizations and advocacy groups",
            "Blogs": "Independent blogs and alternative news sources"
        }
        return descriptions.get(bucket, "Other sources")
