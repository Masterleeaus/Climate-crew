"""
Article processor for normalization, deduplication, and chunking.
"""

import hashlib
import logging
import re
from typing import List, Dict, Optional, Any
from datetime import datetime
from bs4 import BeautifulSoup

from ..models import NewsArticle, NewsChunk
from ..ingestion.news_fetcher import RawArticle
from ...rag.text_chunker import TextChunker

logger = logging.getLogger(__name__)


class ArticleProcessor:
    """Process and normalize raw articles."""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        default_image_url: str = "https://via.placeholder.com/800x450?text=Climate+News"
    ):
        self.chunker = TextChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.default_image_url = default_image_url
        self._seen_hashes = set()  # For deduplication
    
    def generate_article_id(self, url: str, title: str) -> str:
        """Generate unique article ID from URL and title."""
        content = f"{url}:{title}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def generate_content_hash(self, url: str, title: str) -> str:
        """Generate hash for deduplication."""
        content = f"{url}:{title}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def is_duplicate(self, url: str, title: str) -> bool:
        """Check if article is duplicate."""
        content_hash = self.generate_content_hash(url, title)
        if content_hash in self._seen_hashes:
            return True
        self._seen_hashes.add(content_hash)
        return False
    
    def normalize_article(self, raw_article: RawArticle) -> Optional[NewsArticle]:
        """Normalize raw article to NewsArticle model."""
        # Check for duplicates
        if self.is_duplicate(raw_article.url, raw_article.title):
            logger.debug(f"Skipping duplicate article: {raw_article.title}")
            return None
        
        # Validate required fields
        if not raw_article.title or not raw_article.url:
            logger.warning("Article missing title or URL")
            return None
        
        # Generate ID
        article_id = self.generate_article_id(raw_article.url, raw_article.title)
        
        # Ensure content exists
        content = raw_article.content or raw_article.summary or raw_article.title
        if not content or len(content.strip()) < 50:
            logger.warning(f"Article content too short: {raw_article.url}")
            return None
        
        # Strip HTML from content
        content = self.strip_html(content) or content.strip()
        
        # Strip HTML from summary and limit length
        summary = None
        if raw_article.summary:
            summary = self.strip_html(raw_article.summary)
            if summary:
                summary = summary[:500].strip()
        
        # Ensure image URL exists (use default if none provided)
        image_url = raw_article.image_url
        if not image_url or image_url.strip() == "":
            image_url = self.default_image_url
        
        # Create normalized article
        article = NewsArticle(
            id=article_id,
            title=raw_article.title.strip(),
            content=content,
            summary=summary,
            source=raw_article.source,
            url=raw_article.url,
            published_at=raw_article.published_at,
            tags=raw_article.tags or [],
            image_url=image_url,
            bucket=raw_article.bucket or "Mainstream Media"
        )
        
        return article
    
    def chunk_article(self, article: NewsArticle) -> List[NewsChunk]:
        """Chunk article into smaller pieces for vector storage."""
        chunks = []
        
        # Use text chunker
        chunked_texts = self.chunker.chunk_text(
            article.content,
            metadata={
                "article_id": article.id,
                "title": article.title,
                "source": article.source,
                "url": article.url,
                "published_at": article.published_at.isoformat(),
                "bucket": article.bucket,
                "tags": article.tags
            }
        )
        
        for idx, chunk_data in enumerate(chunked_texts):
            chunk = NewsChunk(
                chunk_id=f"{article.id}_chunk_{idx}",
                article_id=article.id,
                text=chunk_data["text"],
                chunk_index=idx,
                metadata=chunk_data.get("metadata", {})
            )
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} chunks for article {article.id}")
        return chunks
    
    def process_articles(self, raw_articles: List[RawArticle]) -> List[NewsArticle]:
        """Process multiple raw articles."""
        normalized = []
        
        for raw in raw_articles:
            try:
                article = self.normalize_article(raw)
                if article:
                    normalized.append(article)
            except Exception as e:
                logger.error(f"Error processing article {raw.url}: {e}")
        
        logger.info(f"Processed {len(normalized)} articles from {len(raw_articles)} raw articles")
        return normalized
    
    def reset_deduplication(self):
        """Reset deduplication cache (useful for testing)."""
        self._seen_hashes.clear()
    
    def strip_html(self, text: Optional[str]) -> Optional[str]:
        """Strip HTML tags from text."""
        if not text:
            return None
        
        try:
            # Use BeautifulSoup to parse and extract text
            soup = BeautifulSoup(text, 'html.parser')
            # Get text and clean up whitespace
            cleaned = soup.get_text(separator=' ', strip=True)
            # Remove extra whitespace
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            return cleaned if cleaned else None
        except Exception as e:
            logger.warning(f"Error stripping HTML: {e}")
            # Fallback: simple regex removal
            cleaned = re.sub(r'<[^>]+>', '', text)
            cleaned = re.sub(r'\s+', ' ', cleaned).strip()
            return cleaned if cleaned else None
