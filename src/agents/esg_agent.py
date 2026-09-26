from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING
from datetime import datetime
import os

from langchain_core.tools import tool

from .base import BaseAgent
from ..data_sources.esg_data import FinnhubClient, AlphaVantageClient
from ..data_sources.web_search import WebSearchClient

if TYPE_CHECKING:
    from ..memory import MemoryManager

_finnhub_client = None
_alpha_vantage_client = None
_web_search_client = None

def get_finnhub():
    global _finnhub_client
    if _finnhub_client is None:
        _finnhub_client = FinnhubClient()
    return _finnhub_client

def get_alpha_vantage():
    global _alpha_vantage_client
    if _alpha_vantage_client is None:
        _alpha_vantage_client = AlphaVantageClient()
    return _alpha_vantage_client

def get_web_search():
    global _web_search_client
    if _web_search_client is None:
        _web_search_client = WebSearchClient()
    return _web_search_client

@tool
def get_esg_scores(ticker: str) -> str:
    """Get ESG (Environmental, Social, Governance) scores for a company from Finnhub."""
    try:
        data = get_finnhub().get_esg_scores(ticker)
        if "error" in data:
            return f"Error: {data['error']}"
        
        if not data.get("found"):
            return f"No ESG data available for {ticker}. This may be a smaller company not covered by ESG rating agencies."
        
        return f"""
ESG Scores for {ticker.upper()}:
Total ESG Score: {data.get('total_esg_score', 'N/A')}
Environmental: {data.get('environmental_score', 'N/A')}
Social: {data.get('social_score', 'N/A')}
Governance: {data.get('governance_score', 'N/A')}
Last Updated: {data.get('last_updated', 'N/A')}
"""
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_company_news(ticker: str) -> str:
    """Get recent company news from Finnhub (last 7 days)."""
    try:
        news = get_finnhub().get_company_news(ticker, days_back=7)
        if not news or (isinstance(news, list) and len(news) == 1 and "error" in news[0]):
            return f"No news found for {ticker}"
        
        output = f"Recent News for {ticker.upper()}:\n"
        for i, item in enumerate(news[:5], 1):
            headline = item.get("headline") or "No headline"
            source = item.get("source", "Unknown")
            date = item.get("datetime", "")[:10] if item.get("datetime") else ""
            output += f"\n{i}. {headline}\n   {date} | {source}\n"
        return output
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_climate_news(ticker: str) -> str:
    """Get climate-related news for a stock (filtered for ESG, carbon, sustainability keywords)."""
    try:
        news = get_finnhub().get_climate_news(ticker)
        if not news or (len(news) == 1 and "message" in news[0]):
            return f"No climate-related news found for {ticker} in the past 30 days."
        
        output = f"Climate-Related News for {ticker.upper()}:\n"
        for i, item in enumerate(news[:5], 1):
            headline = item.get("headline") or "No headline"
            source = item.get("source", "Unknown")
            output += f"\n{i}. {headline}\n   Source: {source}\n"
        return output
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_market_sentiment(topics: str = "energy_transportation") -> str:
    """Get market news sentiment from Alpha Vantage. Topics: technology, earnings, ipo, finance, energy_transportation."""
    try:
        data = get_alpha_vantage().get_news_sentiment(topics=topics, limit=20)
        if "error" in data:
            return f"Error: {data['error']}"
        
        articles = data.get("articles", [])
        if not articles:
            return "No news found for this topic."
        
        bullish = sum(1 for a in articles if a.get("overall_sentiment_label") == "Bullish")
        bearish = sum(1 for a in articles if a.get("overall_sentiment_label") == "Bearish")
        neutral = len(articles) - bullish - bearish
        
        output = f"Market Sentiment ({topics}):\n"
        output += f"Bullish: {bullish} | Bearish: {bearish} | Neutral: {neutral}\n\n"
        output += "Top Headlines:\n"
        
        for article in articles[:5]:
            title = (article.get("title") or "")[:60]
            sentiment = article.get("overall_sentiment_label", "Neutral")
            output += f"- [{sentiment}] {title}...\n"
        
        return output
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_stock_quote(ticker: str) -> str:
    """Get real-time stock quote from Finnhub."""
    try:
        data = get_finnhub().get_quote(ticker)
        if "error" in data:
            return f"Error: {data['error']}"
        
        return f"""
{ticker.upper()} Quote:
Current Price: ${data.get('current_price')}
Change: {data.get('change'):+.2f} ({data.get('percent_change'):+.2f}%)
Day Range: ${data.get('low')} - ${data.get('high')}
Open: ${data.get('open')}
Previous Close: ${data.get('previous_close')}
"""
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def web_search_esg(query: str) -> str:
    """Search the web for ESG research, sustainability reports, or corporate environmental initiatives."""
    try:
        results = get_web_search().search(query + " ESG sustainability environmental", max_results=5)
        if not results:
            return "No search results found."
        
        output = f"Web Search Results for: {query}\n\n"
        for i, r in enumerate(results[:5], 1):
            output += f"{i}. {r.title}\n   {r.snippet[:200]}...\n   URL: {r.url}\n\n"
        return output
    except Exception as e:
        return f"Error: {str(e)}"


class ESGAgent(BaseAgent):
    
    def __init__(self, google_api_key: Optional[str] = None, memory_manager: Optional['MemoryManager'] = None):
        super().__init__("ESGAgent", google_api_key, memory_manager=memory_manager)
    
    def get_tools(self) -> List[Callable]:
        return [
            get_esg_scores,
            get_company_news,
            get_climate_news,
            get_market_sentiment,
            get_stock_quote,
            web_search_esg
        ]
    
    def get_system_prompt(self) -> str:
        return """You are an ESG (Environmental, Social, Governance) Analyst. You help users understand company sustainability and ESG performance.

Your tools:
- get_esg_scores: Get ESG scores for a company
- get_company_news: Get recent company news
- get_climate_news: Get climate-specific news
- get_market_sentiment: Get market sentiment on topics
- get_stock_quote: Get real-time stock quote

STRATEGY:
1. When asked about a company's sustainability, get ESG scores first
2. Check for climate-related news that might affect scores
3. Provide context on what good/bad ESG scores mean
4. Explain how ESG affects investment decisions

ESG Score Guide:
- 8-10: Excellent (climate leaders)
- 6-8: Good (above average)
- 4-6: Average
- 0-4: Poor (laggards)

Be helpful and explain ESG concepts in simple terms for normal users."""
    
    def get_alerts(self) -> List[Dict]:
        return []
