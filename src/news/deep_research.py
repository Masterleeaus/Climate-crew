"""
Deep Research mode for expanded article analysis.
"""

import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime
from google import genai

from .models import ArticleChatRequest, ArticleChatResponse, NewsSearchRequest
from .qdrant_manager import NewsQdrantManager
from .chat import ArticleChatManager

logger = logging.getLogger(__name__)


class DeepResearchManager:
    """Manage deep research mode with multi-step retrieval and synthesis."""
    
    def __init__(
        self,
        qdrant_manager: NewsQdrantManager,
        chat_manager: ArticleChatManager,
        google_api_key: Optional[str] = None,
        model: str = "gemini-2.0-flash"
    ):
        self.qdrant_manager = qdrant_manager
        self.chat_manager = chat_manager
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.model = model
        
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY must be set")
        
        self._genai_client = genai.Client(api_key=self.google_api_key)
    
    def _extract_key_topics(self, article_content: str, query: str) -> List[str]:
        """Extract key topics from article and query for expanded search."""
        prompt = f"""Extract 3-5 key topics or themes from this article and query that would be useful for finding related climate news articles.

Article excerpt: {article_content[:1000]}
User query: {query}

Return a JSON array of topic strings, e.g., ["carbon emissions", "renewable energy policy", "climate adaptation"].
"""
        
        try:
            model = self._genai_client.models.get_model(self.model)
            response = model.generate_content(prompt)
            
            # Parse JSON response
            import json
            import re
            
            text = response.text.strip()
            # Extract JSON array
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                topics = json.loads(json_match.group())
                return topics[:5]
        except Exception as e:
            logger.error(f"Error extracting topics: {e}")
        
        # Fallback: simple keyword extraction
        keywords = ["climate", "emissions", "renewable", "policy", "warming"]
        return keywords[:3]
    
    def _retrieve_related_news(self, article_id: str, query: str, topics: List[str]) -> List[Dict]:
        """Retrieve related news articles from Qdrant."""
        related_articles = []
        
        # Search for each topic
        for topic in topics:
            search_request = NewsSearchRequest(
                query=topic,
                limit=5,
                use_vector_search=True
            )
            
            results = self.qdrant_manager.search_articles(search_request)
            
            for result in results:
                if result.id != article_id:  # Exclude original article
                    related_articles.append({
                        "id": result.id,
                        "title": result.title,
                        "summary": result.summary,
                        "source": result.source,
                        "url": result.url,
                        "published_at": result.published_at.isoformat(),
                        "score": result.score or 0.0
                    })
        
        # Deduplicate and sort by score
        seen_ids = set()
        unique_articles = []
        
        for article in sorted(related_articles, key=lambda x: x.get("score", 0), reverse=True):
            if article["id"] not in seen_ids:
                seen_ids.add(article["id"])
                unique_articles.append(article)
        
        return unique_articles[:10]  # Limit to top 10
    
    def _synthesize_insights(
        self,
        original_article: Dict,
        related_articles: List[Dict],
        query: str
    ) -> str:
        """Synthesize insights from original article and related articles."""
        # Build context
        related_summaries = "\n\n".join([
            f"Title: {a['title']}\nSource: {a['source']}\nSummary: {a.get('summary', 'N/A')}\nURL: {a['url']}"
            for a in related_articles[:5]
        ])
        
        prompt = f"""You are analyzing a climate news article in the context of related articles from multiple sources.

Original Article:
Title: {original_article['title']}
Source: {original_article['source']}
Content: {original_article['content'][:2000]}

Related Articles from Other Sources:
{related_summaries}

User Question: {query}

Provide a comprehensive answer that:
1. Directly addresses the user's question using the original article
2. Incorporates insights and perspectives from the related articles
3. Highlights any consensus, disagreements, or additional context across sources
4. Cites specific sources for each claim
5. Notes any important differences in reporting or emphasis

Be thorough but organized. Use clear citations like [Source: Article Title].
"""
        
        try:
            model = self._genai_client.models.get_model(self.model)
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Error synthesizing insights: {e}")
            return "Error generating synthesis. Please try again."
    
    def deep_research(
        self,
        request: ArticleChatRequest
    ) -> ArticleChatResponse:
        """Perform deep research on an article."""
        # Get original article
        article = self.qdrant_manager.get_article_by_id(request.article_id)
        if not article:
            raise ValueError(f"Article {request.article_id} not found")
        
        # Get conversation ID
        conversation_id = request.conversation_id or f"article_{request.article_id}_{datetime.utcnow().timestamp()}"
        
        # Extract key topics for expanded search
        article_dict = {
            "title": article.title,
            "source": article.source,
            "content": article.content,
            "summary": article.summary or ""
        }
        
        topics = self._extract_key_topics(article.content, request.message)
        logger.info(f"Extracted topics for deep research: {topics}")
        
        # Retrieve related articles
        related_articles = self._retrieve_related_news(request.article_id, request.message, topics)
        logger.info(f"Found {len(related_articles)} related articles")
        
        # Synthesize insights
        answer = self._synthesize_insights(article_dict, related_articles, request.message)
        
        # Build citations
        citations = [
            {
                "type": "article",
                "title": article.title,
                "url": article.url,
                "source": article.source
            }
        ]
        
        for rel in related_articles[:5]:
            citations.append({
                "type": "related_article",
                "title": rel["title"],
                "url": rel["url"],
                "source": rel["source"]
            })
        
        # Format related articles for response
        related_articles_response = [
            {
                "id": rel["id"],
                "title": rel["title"],
                "url": rel["url"],
                "source": rel["source"]
            }
            for rel in related_articles[:5]
        ]
        
        # Store in conversation (if chat manager has this method)
        if hasattr(self.chat_manager, '_add_to_conversation'):
            self.chat_manager._add_to_conversation(conversation_id, "user", request.message)
            self.chat_manager._add_to_conversation(conversation_id, "assistant", answer)
        
        return ArticleChatResponse(
            answer=answer,
            citations=citations,
            related_articles=related_articles_response,
            conversation_id=conversation_id,
            deep_research_used=True
        )
