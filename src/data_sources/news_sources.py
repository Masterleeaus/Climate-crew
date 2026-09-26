"""
News source clients for fetching climate-related news from various providers.
Supports multiple news APIs and RSS feeds.
"""

import os
import logging
import hashlib
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from bs4 import BeautifulSoup
import feedparser
import time

logger = logging.getLogger(__name__)


@dataclass
class NewsArticle:
    """Standardized news article structure."""
    id: str
    title: str
    content: str
    summary: str
    source: str
    url: str
    published_at: datetime
    tags: List[str]
    image_url: Optional[str] = None
    bucket: str = "Mainstream Media"


class NewsAPIClient:
    """Client for NewsAPI.org"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("NEWS_API_KEY")
        self.base_url = "https://newsapi.org/v2"
        
    def fetch_climate_news(
        self,
        limit: int = 50,
        sources: Optional[List[str]] = None,
        days_back: int = 7
    ) -> List[NewsArticle]:
        """Fetch climate-related news from NewsAPI."""
        if not self.api_key:
            logger.warning("NEWS_API_KEY not set. Skipping NewsAPI.")
            return []
        
        articles = []
        sources = sources or ["reuters", "bbc-news", "the-guardian-uk", "associated-press", "bloomberg"]
        
        try:
            for source in sources:
                try:
                    url = f"{self.base_url}/everything"
                    params = {
                        "apiKey": self.api_key,
                        "sources": source,
                        "q": "climate OR global warming OR carbon emissions OR renewable energy OR climate change",
                        "sortBy": "publishedAt",
                        "pageSize": min(limit, 100),
                        "from": (datetime.now() - timedelta(days=days_back)).isoformat()
                    }
                    
                    response = requests.get(url, params=params, timeout=30)
                    response.raise_for_status()
                    data = response.json()
                    
                    for item in data.get("articles", []):
                        article = self._parse_newsapi_article(item, source)
                        if article:
                            articles.append(article)
                    
                    time.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    logger.warning(f"Error fetching from {source}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}")
        
        return articles
    
    def _parse_newsapi_article(self, item: Dict, source: str) -> Optional[NewsArticle]:
        """Parse NewsAPI article format."""
        try:
            article_id = hashlib.sha256(
                (item.get("url", "") + item.get("title", "")).encode()
            ).hexdigest()[:16]
            
            published_str = item.get("publishedAt", "")
            published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
            
            content = item.get("content", "") or item.get("description", "")
            summary = item.get("description", "")[:500]
            
            # Extract tags from title/content
            tags = self._extract_tags(item.get("title", "") + " " + content)
            
            return NewsArticle(
                id=article_id,
                title=item.get("title", "").strip(),
                content=content.strip(),
                summary=summary.strip(),
                source=item.get("source", {}).get("name", source),
                url=item.get("url", ""),
                published_at=published_at,
                tags=tags,
                image_url=item.get("urlToImage"),
                bucket=self._determine_bucket(source)
            )
        except Exception as e:
            logger.warning(f"Error parsing article: {e}")
            return None
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract relevant tags from text."""
        text_lower = text.lower()
        tags = []
        
        tag_keywords = {
            "policy": ["policy", "regulation", "law", "treaty", "agreement", "cop"],
            "energy": ["energy", "renewable", "solar", "wind", "nuclear", "fossil fuel"],
            "disasters": ["flood", "wildfire", "hurricane", "drought", "extreme weather"],
            "carbon markets": ["carbon", "emissions", "offset", "credits", "trading"],
            "climate science": ["research", "study", "scientists", "temperature", "warming"]
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(tag)
        
        return tags if tags else ["general"]
    
    def _determine_bucket(self, source: str) -> str:
        """Determine source bucket based on source name."""
        source_lower = source.lower()
        
        if any(x in source_lower for x in ["reuters", "bbc", "ap", "associated press", "bloomberg", "nyt", "times"]):
            return "Mainstream Media"
        elif any(x in source_lower for x in ["nature", "science", "journal"]):
            return "Scientific Journals"
        elif any(x in source_lower for x in ["bloomberg", "financial", "wsj", "ft"]):
            return "Financial News"
        elif any(x in source_lower for x in ["greenpeace", "wwf", "ngo", "climate"]):
            return "NGOs"
        else:
            return "Blogs"


class RSSFeedClient:
    """Client for fetching news from RSS feeds."""
    
    def __init__(self):
        self.feeds = {
            "Reuters Climate": {
                "url": "https://www.reuters.com/tools/rss",
                "bucket": "Mainstream Media"
            },
            "BBC Climate": {
                "url": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml",
                "bucket": "Mainstream Media"
            },
            "Guardian Climate": {
                "url": "https://www.theguardian.com/environment/climate-change/rss",
                "bucket": "Mainstream Media"
            },
            "Climate.gov": {
                "url": "https://www.climate.gov/news-features/all-news/rss.xml",
                "bucket": "Scientific Journals"
            }
        }
    
    def fetch_all_feeds(self, limit_per_feed: int = 20) -> List[NewsArticle]:
        """Fetch articles from all configured RSS feeds."""
        articles = []
        
        for feed_name, feed_config in self.feeds.items():
            try:
                feed_articles = self._fetch_feed(
                    feed_config["url"],
                    feed_name,
                    feed_config["bucket"],
                    limit_per_feed
                )
                articles.extend(feed_articles)
                time.sleep(1)  # Rate limiting
            except Exception as e:
                logger.warning(f"Error fetching feed {feed_name}: {e}")
                continue
        
        return articles
    
    def _fetch_feed(
        self,
        feed_url: str,
        source_name: str,
        bucket: str,
        limit: int
    ) -> List[NewsArticle]:
        """Fetch articles from a single RSS feed."""
        articles = []
        
        try:
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:limit]:
                try:
                    article_id = hashlib.sha256(
                        (entry.get("link", "") + entry.get("title", "")).encode()
                    ).hexdigest()[:16]
                    
                    # Parse published date
                    published_at = datetime.now()
                    if hasattr(entry, "published_parsed") and entry.published_parsed:
                        published_at = datetime(*entry.published_parsed[:6])
                    
                    # Extract content
                    content = ""
                    if hasattr(entry, "content"):
                        content = entry.content[0].value if entry.content else ""
                    elif hasattr(entry, "summary"):
                        content = entry.summary
                    
                    # Clean HTML
                    content = BeautifulSoup(content, "html.parser").get_text()
                    summary = content[:500] if len(content) > 500 else content
                    
                    # Extract image
                    image_url = None
                    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                        thumbnail = entry.media_thumbnail[0]
                        if isinstance(thumbnail, dict):
                            image_url = thumbnail.get("url")
                        else:
                            image_url = getattr(thumbnail, "url", None)
                    elif hasattr(entry, "enclosures"):
                        for enc in entry.enclosures:
                            type_val = enc.get("type", "") if isinstance(enc, dict) else getattr(enc, "type", "")
                            if type_val.startswith("image"):
                                image_url = enc.get("href") if isinstance(enc, dict) else getattr(enc, "href", None)
                                break
                    
                    # Extract tags
                    tags = []
                    if hasattr(entry, "tags"):
                        for tag in entry.tags:
                            term = tag.get("term") if isinstance(tag, dict) else getattr(tag, "term", None)
                            if term:
                                tags.append(term)
                    
                    if not tags:
                        tags = self._extract_tags_from_text(entry.get("title", "") + " " + content)
                    
                    article = NewsArticle(
                        id=article_id,
                        title=entry.get("title", "").strip(),
                        content=content.strip(),
                        summary=summary.strip(),
                        source=source_name,
                        url=entry.get("link", ""),
                        published_at=published_at,
                        tags=tags[:5],  # Limit tags
                        image_url=image_url,
                        bucket=bucket
                    )
                    
                    articles.append(article)
                    
                except Exception as e:
                    logger.warning(f"Error parsing RSS entry: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error fetching RSS feed {feed_url}: {e}")
        
        return articles
    
    def _extract_tags_from_text(self, text: str) -> List[str]:
        """Extract tags from text content."""
        text_lower = text.lower()
        tags = []
        
        tag_keywords = {
            "policy": ["policy", "regulation", "law", "treaty"],
            "energy": ["energy", "renewable", "solar", "wind"],
            "disasters": ["flood", "wildfire", "hurricane", "drought"],
            "carbon markets": ["carbon", "emissions", "offset"],
            "climate science": ["research", "study", "scientists"]
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(tag)
        
        return tags if tags else ["general"]


class NewsIngestionService:
    """Service for ingesting news from multiple sources."""
    
    def __init__(self):
        self.newsapi_client = NewsAPIClient()
        self.rss_client = RSSFeedClient()
    
    def fetch_all_news(
        self,
        limit_per_source: int = 50,
        days_back: int = 7
    ) -> List[NewsArticle]:
        """Fetch news from all configured sources."""
        all_articles = []
        
        # Fetch from NewsAPI
        try:
            newsapi_articles = self.newsapi_client.fetch_climate_news(
                limit=limit_per_source,
                days_back=days_back
            )
            all_articles.extend(newsapi_articles)
            logger.info(f"Fetched {len(newsapi_articles)} articles from NewsAPI")
        except Exception as e:
            logger.error(f"Error fetching from NewsAPI: {e}")
        
        # Fetch from RSS feeds
        try:
            rss_articles = self.rss_client.fetch_all_feeds(limit_per_feed=limit_per_source // 4)
            all_articles.extend(rss_articles)
            logger.info(f"Fetched {len(rss_articles)} articles from RSS feeds")
        except Exception as e:
            logger.error(f"Error fetching from RSS: {e}")
        
        # Deduplicate by URL + title hash
        seen = set()
        unique_articles = []
        for article in all_articles:
            key = (article.url, article.title.lower())
            if key not in seen:
                seen.add(key)
                unique_articles.append(article)
        
        logger.info(f"Total unique articles after deduplication: {len(unique_articles)}")
        return unique_articles
    
    def validate_image_url(self, image_url: Optional[str]) -> Optional[str]:
        """Validate image URL and return fallback if invalid."""
        if not image_url:
            return None
        
        try:
            response = requests.head(image_url, timeout=5, allow_redirects=True)
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                if content_type.startswith("image/"):
                    return image_url
        except Exception:
            pass
        
        # Return default placeholder image
        return "https://via.placeholder.com/800x400?text=Climate+News"
