"""
News fetcher for multiple sources.
Supports RSS feeds, news APIs, and web scraping.
"""

import os
import logging
import hashlib
import re
import requests
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from urllib.parse import urljoin, urlparse
import feedparser
from bs4 import BeautifulSoup
import time

logger = logging.getLogger(__name__)


class NewsSource(str, Enum):
    """Supported news sources."""
    REUTERS = "Reuters"
    BBC = "BBC"
    NYT = "New York Times"
    GUARDIAN = "The Guardian"
    AP = "Associated Press"
    BLOOMBERG = "Bloomberg"
    CLIMATE_HOME = "Climate Home News"
    CARBON_BRIEF = "Carbon Brief"
    INSIDE_CLIMATE = "Inside Climate News"
    CLIMATE_WIRE = "Climate Wire"


@dataclass
class RawArticle:
    """Raw article data from source."""
    title: str
    content: str
    summary: Optional[str]
    source: str
    url: str
    published_at: datetime
    image_url: Optional[str] = None
    tags: List[str] = None
    bucket: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class NewsFetcher:
    """Fetch news from multiple sources."""
    
    def __init__(
        self,
        nyt_api_key: Optional[str] = None,
        guardian_api_key: Optional[str] = None,
        max_retries: int = 3,
        timeout: int = 30
    ):
        self.nyt_api_key = nyt_api_key or os.getenv("NYT_API_KEY")
        self.guardian_api_key = guardian_api_key or os.getenv("GUARDIAN_API_KEY")
        self.max_retries = max_retries
        self.timeout = timeout
        
        # Default image fallback
        self.default_image_url = "https://via.placeholder.com/800x450?text=Climate+News"
        
        # Source configurations
        self.source_configs = {
            NewsSource.REUTERS: {
                "rss": "https://www.reuters.com/rssFeed/worldNews",
                "bucket": "Mainstream Media",
                "climate_rss": "https://www.reuters.com/rssFeed/environment"
            },
            NewsSource.BBC: {
                "rss": "https://feeds.bbci.co.uk/news/rss.xml",
                "bucket": "Mainstream Media",
                "climate_rss": "https://feeds.bbci.co.uk/news/science_and_environment/rss.xml"
            },
            NewsSource.GUARDIAN: {
                "api": "https://content.guardianapis.com/search",
                "bucket": "Mainstream Media",
                "api_key": self.guardian_api_key
            },
            NewsSource.NYT: {
                "api": "https://api.nytimes.com/svc/search/v2/articlesearch.json",
                "bucket": "Mainstream Media",
                "api_key": self.nyt_api_key
            },
            NewsSource.AP: {
                "rss": "https://apnews.com/rss",
                "bucket": "Mainstream Media",
                "climate_rss": "https://apnews.com/rss/topics/climate"
            },
            NewsSource.BLOOMBERG: {
                "rss": "https://www.bloomberg.com/feeds/bloomberg.rss",
                "bucket": "Financial News",
                "climate_rss": "https://www.bloomberg.com/feeds/bloomberg.rss?tag=climate"
            },
            NewsSource.CLIMATE_HOME: {
                "rss": "https://www.climatechangenews.com/feed/",
                "bucket": "Blogs"
            },
            NewsSource.CARBON_BRIEF: {
                "rss": "https://www.carbonbrief.org/feed",
                "bucket": "Blogs"
            },
            NewsSource.INSIDE_CLIMATE: {
                "rss": "https://insideclimatenews.org/feed/",
                "bucket": "Blogs"
            },
            NewsSource.CLIMATE_WIRE: {
                "rss": "https://www.eenews.net/articles/feed/",
                "bucket": "Blogs"
            }
        }
    
    def _strip_html(self, text: Optional[str]) -> Optional[str]:
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
    
    def _extract_image_from_html(self, html_content: str, base_url: Optional[str] = None) -> Optional[str]:
        """Extract image URL from HTML content."""
        if not html_content:
            return None
        
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Try to find img tag
            img_tag = soup.find('img')
            if img_tag:
                image_url = img_tag.get('src') or img_tag.get('data-src') or img_tag.get('data-lazy-src')
                if image_url:
                    # Handle relative URLs
                    if image_url.startswith('//'):
                        image_url = 'https:' + image_url
                    elif image_url.startswith('/') and base_url:
                        image_url = urljoin(base_url, image_url)
                    elif not image_url.startswith(('http://', 'https://')) and base_url:
                        image_url = urljoin(base_url, image_url)
                    
                    # Validate it looks like an image URL
                    if image_url and any(ext in image_url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
                        return image_url
                    elif image_url and ('image' in image_url.lower() or 'photo' in image_url.lower()):
                        return image_url
            
            # Try to find og:image meta tag
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                image_url = og_image.get('content')
                if image_url.startswith('//'):
                    image_url = 'https:' + image_url
                elif image_url.startswith('/') and base_url:
                    image_url = urljoin(base_url, image_url)
                return image_url
                
        except Exception as e:
            logger.debug(f"Error extracting image from HTML: {e}")
        
        return None
    
    def _make_request(self, url: str, headers: Optional[Dict] = None, params: Optional[Dict] = None) -> Optional[requests.Response]:
        """Make HTTP request with retry logic."""
        headers = headers or {}
        params = params or {}
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(url, headers=headers, params=params, timeout=self.timeout)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                if attempt == self.max_retries - 1:
                    logger.error(f"Failed to fetch {url} after {self.max_retries} attempts: {e}")
                    return None
                time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def _parse_rss_feed(self, feed_url: str, source: NewsSource) -> List[RawArticle]:
        """Parse RSS feed and extract articles."""
        articles = []
        
        try:
            logger.info(f"Parsing RSS feed: {feed_url}")
            
            # Try to fetch feed content first for better error handling
            feed_content = None
            response = self._make_request(feed_url, headers={'User-Agent': 'Mozilla/5.0'})
            if response:
                feed_content = response.content
                feed = feedparser.parse(feed_content)
            else:
                # Fallback to direct URL parsing
                feed = feedparser.parse(feed_url)
            
            # Check if feed parsing was successful
            if feed.bozo and feed.bozo_exception:
                logger.warning(f"RSS feed parsing warning for {feed_url}: {feed.bozo_exception}")
            
            # Check if feed has entries
            if not hasattr(feed, 'entries') or not feed.entries:
                logger.warning(f"No entries found in RSS feed: {feed_url}")
                if hasattr(feed, 'status'):
                    logger.warning(f"Feed status: {feed.status}")
                if hasattr(feed, 'feed') and hasattr(feed.feed, 'title'):
                    logger.debug(f"Feed title: {feed.feed.title}")
                return articles
            
            logger.info(f"Found {len(feed.entries)} entries in feed {feed_url}")
            
            # Check if this is a climate-focused feed (skip keyword filtering)
            config = self.source_configs.get(source, {})
            is_climate_feed = config.get("climate_rss") == feed_url
            
            for entry in feed.entries[:50]:  # Limit to 50 most recent
                # Filter for climate-related content (skip for climate-focused feeds)
                title = entry.get("title", "")
                summary = entry.get("summary", "")
                
                if not is_climate_feed:
                    # Basic climate keyword filter for general feeds
                    climate_keywords = [
                        "climate", "warming", "emissions", "carbon", "renewable",
                        "solar", "wind", "fossil", "greenhouse", "temperature",
                        "drought", "flood", "wildfire", "hurricane", "typhoon",
                        "sea level", "glacier", "arctic", "antarctic", "biodiversity",
                        "deforestation", "pollution", "clean energy", "net zero"
                    ]
                    
                    content_lower = (title + " " + summary).lower()
                    if not any(keyword in content_lower for keyword in climate_keywords):
                        continue
                
                # Parse published date
                published_at = datetime.utcnow()
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    try:
                        published_at = datetime(*entry.published_parsed[:6])
                    except:
                        pass
                
                # Extract image - try multiple methods
                image_url = None
                entry_link = entry.get("link", "")
                
                # Method 1: Check media_content (Media RSS)
                if hasattr(entry, "media_content") and entry.media_content:
                    for media in entry.media_content:
                        if media.get("type", "").startswith("image/"):
                            image_url = media.get("url")
                            break
                
                # Method 2: Check media_thumbnail (Media RSS)
                if not image_url and hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
                    image_url = entry.media_thumbnail[0].get("url")
                
                # Method 3: Check enclosures
                if not image_url and hasattr(entry, "enclosures") and entry.enclosures:
                    for enc in entry.enclosures:
                        if enc.get("type", "").startswith("image"):
                            image_url = enc.get("href")
                            break
                
                # Method 4: Extract from HTML content/summary (most common for RSS feeds)
                if not image_url:
                    html_content = entry.get("content", [{}])[0].get("value", "") if entry.get("content") else summary
                    if html_content:
                        image_url = self._extract_image_from_html(html_content, entry_link)
                
                # Method 5: Check for image in links
                if not image_url and hasattr(entry, "links"):
                    for link in entry.links:
                        if link.get("type", "").startswith("image/"):
                            image_url = link.get("href")
                            break
                
                # Get full content if available
                content = entry.get("content", [{}])[0].get("value", "") if entry.get("content") else summary
                if not content:
                    content = summary
                
                # Strip HTML from summary
                cleaned_summary = self._strip_html(summary)
                if cleaned_summary:
                    cleaned_summary = cleaned_summary[:500]
                
                # Ensure we have an image URL (use default if none found)
                final_image_url = image_url if image_url else self.default_image_url
                
                articles.append(RawArticle(
                    title=title,
                    content=content,
                    summary=cleaned_summary,
                    source=source.value,
                    url=entry.get("link", ""),
                    published_at=published_at,
                    image_url=final_image_url,
                    tags=self._extract_tags(title, summary, content)
                ))
            
            logger.info(f"Successfully parsed {len(articles)} articles from {source.value} feed")
        
        except Exception as e:
            logger.error(f"Error parsing RSS feed {feed_url}: {e}")
            import traceback
            logger.debug(traceback.format_exc())
        
        return articles
    
    def _fetch_guardian_articles(self, source: NewsSource) -> List[RawArticle]:
        """Fetch articles from Guardian API."""
        articles = []
        
        if not self.guardian_api_key:
            logger.warning("Guardian API key not configured")
            return articles
        
        config = self.source_configs[source]
        url = config["api"]
        
        params = {
            "api-key": self.guardian_api_key,
            "q": "climate OR global warming OR emissions OR renewable energy",
            "section": "environment",
            "page-size": 50,
            "order-by": "newest"
        }
        
        response = self._make_request(url, params=params)
        if not response:
            return articles
        
        try:
            data = response.json()
            results = data.get("response", {}).get("results", [])
            
            for item in results:
                published_at = datetime.utcnow()
                if item.get("webPublicationDate"):
                    try:
                        published_at = datetime.fromisoformat(item["webPublicationDate"].replace("Z", "+00:00"))
                    except:
                        pass
                
                # Get full article content
                fields = item.get("fields", {})
                content = fields.get("body", "") or fields.get("trailText", "")
                trail_text = fields.get("trailText", "")
                
                # Strip HTML from summary
                cleaned_summary = self._strip_html(trail_text)
                
                articles.append(RawArticle(
                    title=item.get("webTitle", ""),
                    content=content,
                    summary=cleaned_summary,
                    source=source.value,
                    url=item.get("webUrl", ""),
                    published_at=published_at,
                    image_url=fields.get("thumbnail"),
                    tags=self._extract_tags(item.get("webTitle", ""), trail_text, content)
                ))
        
        except Exception as e:
            logger.error(f"Error fetching Guardian articles: {e}")
        
        return articles
    
    def _fetch_nyt_articles(self, source: NewsSource) -> List[RawArticle]:
        """Fetch articles from NYT API."""
        articles = []
        
        if not self.nyt_api_key:
            logger.warning("NYT API key not configured")
            return articles
        
        config = self.source_configs[source]
        url = config["api"]
        
        # Get articles from last 7 days
        begin_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y%m%d")
        
        params = {
            "api-key": self.nyt_api_key,
            "q": "climate change OR global warming OR emissions",
            "begin_date": begin_date,
            "sort": "newest",
            "page": 0
        }
        
        response = self._make_request(url, params=params)
        if not response:
            return articles
        
        try:
            data = response.json()
            results = data.get("response", {}).get("docs", [])
            
            for item in results:
                published_at = datetime.utcnow()
                pub_date = item.get("pub_date")
                if pub_date:
                    try:
                        published_at = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
                    except:
                        pass
                
                # Get multimedia
                image_url = None
                multimedia = item.get("multimedia", [])
                if multimedia:
                    # Find largest image
                    for media in multimedia:
                        if media.get("type") == "image" and media.get("subtype") == "xlarge":
                            image_url = f"https://www.nytimes.com/{media.get('url')}"
                            break
                
                # Get snippet
                headline = item.get("headline", {}).get("main", "")
                snippet = item.get("snippet", "")
                lead_paragraph = item.get("lead_paragraph", "")
                content = lead_paragraph or snippet
                
                # Strip HTML from summary
                cleaned_summary = self._strip_html(snippet)
                
                articles.append(RawArticle(
                    title=headline,
                    content=content,
                    summary=cleaned_summary,
                    source=source.value,
                    url=item.get("web_url", ""),
                    published_at=published_at,
                    image_url=image_url,
                    tags=self._extract_tags(headline, snippet, content)
                ))
        
        except Exception as e:
            logger.error(f"Error fetching NYT articles: {e}")
        
        return articles
    
    def _extract_tags(self, title: str, summary: str, content: str) -> List[str]:
        """Extract relevant tags from article content."""
        text = (title + " " + summary + " " + content).lower()
        tags = []
        
        tag_keywords = {
            "policy": ["policy", "regulation", "legislation", "law", "treaty", "agreement"],
            "energy": ["energy", "renewable", "solar", "wind", "nuclear", "fossil", "coal", "oil", "gas"],
            "disasters": ["disaster", "flood", "drought", "wildfire", "hurricane", "typhoon", "storm"],
            "carbon markets": ["carbon", "emissions", "trading", "offset", "credits", "cap and trade"],
            "climate science": ["science", "research", "study", "temperature", "warming", "climate model"],
            "adaptation": ["adaptation", "resilience", "infrastructure", "preparedness"],
            "mitigation": ["mitigation", "reduction", "cut", "decrease", "lower"],
            "international": ["un", "cop", "paris", "kyoto", "international", "global"]
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in text for keyword in keywords):
                tags.append(tag)
        
        return tags[:5]  # Limit to 5 tags
    
    def fetch_from_source(self, source: NewsSource) -> List[RawArticle]:
        """Fetch articles from a specific source."""
        config = self.source_configs.get(source)
        if not config:
            logger.warning(f"No configuration for source: {source}")
            return []
        
        articles = []
        
        if "rss" in config:
            rss_url = config.get("climate_rss") or config["rss"]
            articles = self._parse_rss_feed(rss_url, source)
        elif "api" in config:
            if source == NewsSource.GUARDIAN:
                articles = self._fetch_guardian_articles(source)
            elif source == NewsSource.NYT:
                articles = self._fetch_nyt_articles(source)
        
        # Assign bucket
        for article in articles:
            article.bucket = config.get("bucket", "Mainstream Media")
        
        return articles
    
    def fetch_all_sources(self, sources: Optional[List[NewsSource]] = None) -> List[RawArticle]:
        """Fetch articles from all configured sources."""
        if sources is None:
            sources = list(NewsSource)
        
        all_articles = []
        
        for source in sources:
            try:
                articles = self.fetch_from_source(source)
                all_articles.extend(articles)
                logger.info(f"Fetched {len(articles)} articles from {source.value}")
                time.sleep(1)  # Rate limiting
            except Exception as e:
                logger.error(f"Error fetching from {source.value}: {e}")
        
        return all_articles
    
    def validate_image_url(self, url: Optional[str]) -> Optional[str]:
        """Validate image URL and return fallback if invalid."""
        if not url:
            return self.default_image_url
        
        # Clean up URL
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            return self.default_image_url
        
        # Try HEAD request first (faster)
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.head(url, timeout=5, allow_redirects=True, headers=headers)
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "").lower()
                if content_type.startswith("image/"):
                    return url
        except requests.exceptions.RequestException:
            # If HEAD fails, try GET with range request (more compatible)
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Range': 'bytes=0-1023'  # Just get first 1KB to check
                }
                response = requests.get(url, timeout=5, allow_redirects=True, headers=headers, stream=True)
                if response.status_code in (200, 206):  # 206 is Partial Content
                    content_type = response.headers.get("content-type", "").lower()
                    if content_type.startswith("image/"):
                        return url
            except requests.exceptions.RequestException:
                pass
        
        # If validation fails, return default
        logger.debug(f"Image URL validation failed for: {url}")
        return self.default_image_url
