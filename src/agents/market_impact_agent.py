from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING
from datetime import datetime

from langchain_core.tools import tool

from .base import BaseAgent
from ..data_sources.yahoo_finance import YahooFinanceClient
from ..data_sources.web_search import WebSearchClient
from ..rag.rag_manager import RAGManager

if TYPE_CHECKING:
    from ..memory import MemoryManager

yahoo_client = YahooFinanceClient()
web_search_client = WebSearchClient()
rag_manager_instance = None

@tool
def get_stock_price(ticker: str) -> str:
    """Get real-time stock price for a ticker symbol (e.g., AAPL, TSLA, MSFT)."""
    try:
        data = yahoo_client.get_current_price(ticker)
        if "error" in data:
            return f"Error: {data['error']}"
        
        price = data.get("price")
        prev_close = data.get("previous_close")
        change = (price - prev_close) if price and prev_close else None
        change_pct = (change / prev_close * 100) if change and prev_close else None
        
        return f"""
Stock: {ticker.upper()}
Price: ${price:,.2f}
Change: {f"${change:+,.2f} ({change_pct:+.2f}%)" if change else "N/A"}
Market Cap: ${data.get('market_cap', 0)/1e9:,.1f}B
52-Week Range: ${data.get('fifty_two_week_low', 0):,.2f} - ${data.get('fifty_two_week_high', 0):,.2f}
"""
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_stock_climate_risk(ticker: str) -> str:
    """Analyze a stock's climate risk exposure based on its sector. Returns risk score 0-100."""
    try:
        data = yahoo_client.get_climate_risk_profile(ticker)
        if "error" in data:
            return f"Error: {data['error']}"
        
        risk = data.get("climate_risk", {})
        key_risks = "\n".join([f"- {r}" for r in risk.get("key_risks", [])])
        
        return f"""
Company: {data.get('company_name')}
Sector: {data.get('sector')}
Industry: {data.get('industry')}
Climate Risk Score: {risk.get('risk_score')}/100
Risk Level: {risk.get('risk_level')}
Key Risks:
{key_risks}
Market Cap: ${data.get('market_cap', 0)/1e9:,.1f}B
"""
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_stock_news(ticker: str) -> str:
    """Get latest news for a stock ticker from Yahoo Finance."""
    try:
        news = yahoo_client.get_news(ticker)
        if not news or (isinstance(news, list) and len(news) == 1 and "error" in news[0]):
            return f"No news found for {ticker}"
        
        output = f"Recent News for {ticker.upper()}:\n"
        for i, item in enumerate(news[:5], 1):
            title = item.get("title") or "No title"
            publisher = item.get("publisher", "Unknown")
            output += f"\n{i}. {title}\n   Source: {publisher}\n"
        return output
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_historical_performance(ticker: str, period: str = "1mo") -> str:
    """Get historical price performance. Period: 1d, 5d, 1mo, 3mo, 6mo, 1y."""
    try:
        data = yahoo_client.get_historical_prices(ticker, period=period)
        if "error" in data:
            return f"Error: {data['error']}"
        
        return f"""
{ticker.upper()} Performance ({period}):
Start Price: ${data.get('start_price', 0):,.2f}
End Price: ${data.get('end_price', 0):,.2f}
Change: {data.get('change_percent', 0):+.2f}%
Data Points: {data.get('data_points')}
"""
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def calculate_portfolio_climate_risk(tickers: str) -> str:
    """Calculate aggregate climate risk for a portfolio. Provide comma-separated tickers (e.g., AAPL,TSLA,XOM)."""
    try:
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        data = yahoo_client.calculate_portfolio_risk(ticker_list)
        
        if "error" in data:
            return f"Error: {data['error']}"
        
        output = f"""
Portfolio Climate Risk Assessment:
Stocks Analyzed: {data.get('analyzed')}/{data.get('portfolio_size')}
Weighted Risk Score: {data.get('weighted_average_risk'):.1f}/100
Risk Level: {data.get('risk_level')}

Highest Risk:
"""
        for stock in data.get("highest_risk_stocks", [])[:3]:
            output += f"  - {stock['ticker']}: {stock['risk_score']}/100 ({stock['sector']})\n"
        
        output += "\nLowest Risk:\n"
        for stock in data.get("lowest_risk_stocks", [])[:3]:
            output += f"  - {stock['ticker']}: {stock['risk_score']}/100 ({stock['sector']})\n"
        
        return output
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def web_search_climate_finance(query: str) -> str:
    """Search the web for climate finance news, stock analysis, or market information. Use for recent events or data not in other tools."""
    try:
        results = web_search_client.search(query + " climate finance stock market", max_results=5)
        if not results:
            return "No search results found."
        
        output = f"Web Search Results for: {query}\n\n"
        for i, r in enumerate(results[:5], 1):
            output += f"{i}. {r.title}\n   {r.snippet[:200]}...\n   URL: {r.url}\n\n"
        return output
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def get_market_intelligence_rag(query: str) -> str:
    """
    Get deep market intelligence, specialized climate finance reports, and analyses using RAG.
    Use this for: "specific news connecting climate events to stock price", "detailed climate risk reports", or when standard news falls short.
    """
    global rag_manager_instance
    if not rag_manager_instance:
        return "RAG System not initialized yet."
    
    try:
        # Get context from RAG
        context = rag_manager_instance.get_context(query, limit=5)
        if not context:
            return "No relevant market intelligence found in the knowledge base."
        return f"Market Intelligence (RAG Retrieval):\n{context}"
    except Exception as e:
        return f"Error retrieving market intelligence: {str(e)}"


class MarketImpactAgent(BaseAgent):
    
    def __init__(self, google_api_key: Optional[str] = None, memory_manager: Optional['MemoryManager'] = None):
        super().__init__("MarketImpactAgent", google_api_key, memory_manager=memory_manager)
        global rag_manager_instance
        # Initialize RAG manager if not already done
        if not rag_manager_instance:
            rag_manager_instance = RAGManager(google_api_key=google_api_key, memory_manager=memory_manager)
    
    def get_tools(self) -> List[Callable]:
        return [
            get_stock_price,
            get_stock_climate_risk,
            get_stock_news,
            get_historical_performance,
            calculate_portfolio_climate_risk,
            web_search_climate_finance,
            get_market_intelligence_rag
        ]
    
    def get_system_prompt(self) -> str:
        return """You are a Climate-Finance Market Impact Analyst. You help users understand how climate change affects stock prices and investments.

Your tools:
- get_stock_price: Get real-time stock price
- get_stock_climate_risk: Analyze climate risk exposure for a stock
- get_stock_news: Get recent news for a stock (Yahoo Finance)
- get_market_intelligence_rag: Get deep analysis and specialized reports linking climate events to markets (RAG)
- get_historical_performance: Get price performance over time
- calculate_portfolio_climate_risk: Assess climate risk for multiple stocks
- web_search_climate_finance: General web search

STRATEGY:
1. When user asks about a stock, ALWAYS get both price AND climate risk.
2. For specific news linking climate to stock (e.g. "how did Hurricane X affect AAPL?"), use 'get_market_intelligence_rag' FIRST.
3. If RAG yields no results, fall back to 'get_stock_news' or 'web_search_climate_finance'.
4. For portfolio analysis, use calculate_portfolio_climate_risk.
5. Explain findings in simple terms suitable for normal users.
6. Highlight high-risk sectors: Energy, Utilities, Real Estate.

ERROR HANDLING:
- If `get_stock_price` returns an error (e.g. "Quote not found"), DO NOT GIVE UP.
- Usage `web_search_climate_finance` to find the correct ticker (e.g. search "JPMorgan stock ticker").
- Then retry with the correct ticker (e.g. JPM).

Climate Risk Score Guide:
- 70-100: Very High (Energy, Oil & Gas)
- 50-69: High (Utilities, Financials, Real Estate)
- 30-49: Moderate (Consumer, Industrials)
- 0-29: Low (Technology, Healthcare)

Be helpful and explain complex concepts simply."""
    
    def get_alerts(self) -> List[Dict]:
        return []
