"""
Climate-Finance Tools for LangChain Agents.

These tools wrap the real API data sources to provide:
- Stock climate risk analysis
- ESG scores and sustainability data
- Regulatory risk assessment
- Climate news and sentiment

All tools fetch LIVE data from real APIs.
"""

import logging
from typing import List, Optional
from langchain_core.tools import tool

from ..data_sources.yahoo_finance import YahooFinanceClient
from ..data_sources.esg_data import FinnhubClient, AlphaVantageClient, ESGDataClient
from src.data_sources.regulatory_data import RegulatoryDataClient, ClimateWatchClient

logger = logging.getLogger(__name__)

# Initialize clients (singleton pattern)
_yahoo_client: Optional[YahooFinanceClient] = None
_finnhub_client: Optional[FinnhubClient] = None
_alpha_vantage_client: Optional[AlphaVantageClient] = None
_esg_client: Optional[ESGDataClient] = None
_regulatory_client: Optional[RegulatoryDataClient] = None
_climate_watch_client: Optional[ClimateWatchClient] = None


def get_yahoo_client() -> YahooFinanceClient:
    global _yahoo_client
    if _yahoo_client is None:
        _yahoo_client = YahooFinanceClient()
    return _yahoo_client


def get_finnhub_client() -> FinnhubClient:
    global _finnhub_client
    if _finnhub_client is None:
        _finnhub_client = FinnhubClient()
    return _finnhub_client


def get_alpha_vantage_client() -> AlphaVantageClient:
    global _alpha_vantage_client
    if _alpha_vantage_client is None:
        _alpha_vantage_client = AlphaVantageClient()
    return _alpha_vantage_client


def get_esg_client() -> ESGDataClient:
    global _esg_client
    if _esg_client is None:
        _esg_client = ESGDataClient()
    return _esg_client


def get_regulatory_client() -> RegulatoryDataClient:
    global _regulatory_client
    if _regulatory_client is None:
        _regulatory_client = RegulatoryDataClient()
    return _regulatory_client


def get_climate_watch_client() -> ClimateWatchClient:
    global _climate_watch_client
    if _climate_watch_client is None:
        _climate_watch_client = ClimateWatchClient()
    return _climate_watch_client


# ==================== STOCK ANALYSIS TOOLS ====================

@tool
def get_stock_price(ticker: str) -> str:
    """
    Get the REAL-TIME current stock price and basic quote data.
    
    Args:
        ticker: Stock ticker symbol (e.g., AAPL, TSLA, MSFT)
        
    Returns:
        Current price, day change, and key metrics.
    """
    try:
        client = get_yahoo_client()
        data = client.get_current_price(ticker)
        
        if "error" in data:
            return f"Error: {data['error']}"
        
        price = data.get("price")
        prev_close = data.get("previous_close")
        change = (price - prev_close) if price and prev_close else None
        change_pct = (change / prev_close * 100) if change and prev_close else None
        
        return f"""
📈 {ticker.upper()} Stock Quote (Live)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Current Price: ${price:,.2f} {data.get('currency', 'USD')}
Change: {f"${change:+,.2f} ({change_pct:+.2f}%)" if change else "N/A"}
Day Range: ${data.get('day_low', 'N/A'):,.2f} - ${data.get('day_high', 'N/A'):,.2f}
52-Week Range: ${data.get('fifty_two_week_low', 'N/A'):,.2f} - ${data.get('fifty_two_week_high', 'N/A'):,.2f}
Market Cap: ${data.get('market_cap', 0)/1e9:,.1f}B
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Source: Yahoo Finance (Real-Time)
"""
    except Exception as e:
        logger.error(f"Error in get_stock_price: {e}")
        return f"Error fetching stock price: {str(e)}"


@tool
def get_stock_climate_risk(ticker: str) -> str:
    """
    Analyze a stock's exposure to climate-related risks.
    
    Args:
        ticker: Stock ticker symbol (e.g., XOM, TSLA, NEE)
        
    Returns:
        Climate risk assessment including sector risk, key threats, and recommendations.
    """
    try:
        client = get_yahoo_client()
        data = client.get_climate_risk_profile(ticker)
        
        if "error" in data:
            return f"Error: {data['error']}"
        
        risk = data.get("climate_risk", {})
        risk_score = risk.get("risk_score", 50)
        risk_level = risk.get("risk_level", "Unknown")
        
        # Risk emoji based on level
        emoji = "🔴" if risk_score >= 70 else "🟠" if risk_score >= 50 else "🟡" if risk_score >= 30 else "🟢"
        
        key_risks = risk.get("key_risks", [])
        risks_str = "\n".join([f"  • {r}" for r in key_risks])
        
        return f"""
{emoji} Climate Risk Analysis: {ticker.upper()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Company: {data.get('company_name', 'Unknown')}
Sector: {data.get('sector', 'Unknown')}
Industry: {data.get('industry', 'Unknown')}
Country: {data.get('country', 'Unknown')}

📊 Climate Risk Score: {risk_score}/100 ({risk_level})

⚠️ Key Climate Risks:
{risks_str}

💼 Market Cap: ${data.get('market_cap', 0)/1e9:,.1f}B
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Source: Yahoo Finance + Climate Risk Analysis (Live)
"""
    except Exception as e:
        logger.error(f"Error in get_stock_climate_risk: {e}")
        return f"Error analyzing climate risk: {str(e)}"


@tool
def get_stock_news(ticker: str) -> str:
    """
    Get the latest news for a stock from Yahoo Finance.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Recent news headlines and links.
    """
    try:
        client = get_yahoo_client()
        news = client.get_news(ticker)
        
        if not news or (isinstance(news, list) and len(news) == 1 and "error" in news[0]):
            return f"No news found for {ticker}"
        
        output = f"📰 Latest News for {ticker.upper()}\n"
        output += "━" * 40 + "\n"
        
        for i, item in enumerate(news[:5], 1):
            title = item.get("title", "No title")
            publisher = item.get("publisher", "Unknown")
            published = item.get("published", "")[:10] if item.get("published") else ""
            link = item.get("link", "")
            
            output += f"\n{i}. {title}\n"
            output += f"   📅 {published} | 📰 {publisher}\n"
            if link:
                output += f"   🔗 {link}\n"
        
        output += "\n━" * 40
        output += "\nSource: Yahoo Finance (Live)"
        
        return output
    except Exception as e:
        logger.error(f"Error in get_stock_news: {e}")
        return f"Error fetching news: {str(e)}"


@tool
def calculate_portfolio_climate_risk(tickers: str) -> str:
    """
    Calculate aggregate climate risk for a portfolio of stocks.
    
    Args:
        tickers: Comma-separated ticker symbols (e.g., "AAPL,TSLA,XOM,MSFT")
        
    Returns:
        Portfolio-level climate risk assessment with breakdown by stock.
    """
    try:
        ticker_list = [t.strip().upper() for t in tickers.split(",")]
        
        if len(ticker_list) > 10:
            return "Error: Maximum 10 tickers allowed per request"
        
        client = get_yahoo_client()
        data = client.calculate_portfolio_risk(ticker_list)
        
        if "error" in data:
            return f"Error: {data['error']}"
        
        risk_score = data.get("weighted_average_risk", 50)
        emoji = "🔴" if risk_score >= 70 else "🟠" if risk_score >= 50 else "🟡" if risk_score >= 30 else "🟢"
        
        output = f"""
{emoji} Portfolio Climate Risk Assessment
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Stocks Analyzed: {data.get('analyzed', 0)}/{data.get('portfolio_size', 0)}
Weighted Risk Score: {risk_score:.1f}/100
Risk Level: {data.get('risk_level', 'Unknown')}

📊 Highest Risk Stocks:
"""
        for stock in data.get("highest_risk_stocks", [])[:3]:
            output += f"  🔴 {stock['ticker']}: {stock['risk_score']}/100 ({stock['sector']})\n"
        
        output += "\n📊 Lowest Risk Stocks:\n"
        for stock in data.get("lowest_risk_stocks", [])[:3]:
            output += f"  🟢 {stock['ticker']}: {stock['risk_score']}/100 ({stock['sector']})\n"
        
        output += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Source: Yahoo Finance + Climate Risk Analysis (Live)
"""
        return output
    except Exception as e:
        logger.error(f"Error in calculate_portfolio_climate_risk: {e}")
        return f"Error calculating portfolio risk: {str(e)}"


# ==================== ESG TOOLS ====================

@tool
def get_esg_scores(ticker: str) -> str:
    """
    Get ESG (Environmental, Social, Governance) scores for a company from Finnhub.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        ESG scores and sustainability metrics.
        
    Note: Requires FINNHUB_API_KEY environment variable. Get free key at: https://finnhub.io/
    """
    try:
        client = get_finnhub_client()
        data = client.get_esg_scores(ticker)
        
        if "error" in data:
            return f"Error: {data['error']}"
        
        if not data.get("found"):
            return f"No ESG data available for {ticker}. This may be a smaller company not covered by ESG rating agencies."
        
        return f"""
🌱 ESG Scores: {ticker.upper()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total ESG Score: {data.get('total_esg_score', 'N/A')}

📊 Component Scores:
  🌍 Environmental: {data.get('environmental_score', 'N/A')}
  👥 Social: {data.get('social_score', 'N/A')}
  🏛️ Governance: {data.get('governance_score', 'N/A')}

Last Updated: {data.get('last_updated', 'N/A')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Source: Finnhub ESG Data (Live)
"""
    except Exception as e:
        logger.error(f"Error in get_esg_scores: {e}")
        return f"Error fetching ESG scores: {str(e)}"


@tool
def get_climate_news_sentiment(ticker: str) -> str:
    """
    Get climate-related news with sentiment analysis for a stock.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Climate-related news headlines with sentiment scores.
        
    Note: Requires FINNHUB_API_KEY. Get free key at: https://finnhub.io/
    """
    try:
        client = get_finnhub_client()
        news = client.get_climate_news(ticker)
        
        if not news or (isinstance(news, list) and len(news) == 1 and "message" in news[0]):
            return f"No climate-related news found for {ticker} in the past 30 days."
        
        output = f"🌍 Climate News for {ticker.upper()}\n"
        output += "━" * 40 + "\n"
        
        for i, item in enumerate(news[:5], 1):
            headline = item.get("headline", "No headline")
            source = item.get("source", "Unknown")
            date = item.get("datetime", "")[:10] if item.get("datetime") else ""
            
            output += f"\n{i}. {headline}\n"
            output += f"   📅 {date} | 📰 {source}\n"
            output += f"   🎯 Climate Relevance: {item.get('climate_relevance', 'Moderate')}\n"
        
        output += "\n━" * 40
        output += "\nSource: Finnhub (Live)"
        
        return output
    except Exception as e:
        logger.error(f"Error in get_climate_news_sentiment: {e}")
        return f"Error fetching climate news: {str(e)}"


@tool  
def get_market_climate_sentiment() -> str:
    """
    Get overall market sentiment on climate/energy topics from news.
    
    Returns:
        Recent climate and energy news with sentiment analysis.
        
    Note: Requires ALPHA_VANTAGE_API_KEY. Get free key at: https://www.alphavantage.co/
    """
    try:
        client = get_alpha_vantage_client()
        data = client.get_climate_news_sentiment()
        
        if "error" in data:
            return f"Error: {data['error']}"
        
        articles = data.get("articles", [])
        
        if not articles:
            return "No climate/energy news found."
        
        output = "🌍 Market Climate & Energy Sentiment\n"
        output += "━" * 45 + "\n"
        
        positive = sum(1 for a in articles if a.get("overall_sentiment_label") == "Bullish")
        negative = sum(1 for a in articles if a.get("overall_sentiment_label") == "Bearish")
        neutral = len(articles) - positive - negative
        
        output += f"\n📊 Sentiment Overview ({len(articles)} articles):\n"
        output += f"  🟢 Bullish: {positive}\n"
        output += f"  🔴 Bearish: {negative}\n"
        output += f"  ⚪ Neutral: {neutral}\n"
        
        output += "\n📰 Top Headlines:\n"
        for i, article in enumerate(articles[:5], 1):
            title = (article.get("title") or "")[:60] + "..." if len(article.get("title", "")) > 60 else article.get("title")
            sentiment = article.get("overall_sentiment_label", "Neutral")
            emoji = "🟢" if sentiment == "Bullish" else "🔴" if sentiment == "Bearish" else "⚪"
            
            output += f"\n{i}. {emoji} {title}\n"
            output += f"   Sentiment: {sentiment} (Score: {article.get('overall_sentiment_score', 'N/A')})\n"
        
        output += "\n━" * 45
        output += "\nSource: Alpha Vantage News Sentiment (Live)"
        
        return output
    except Exception as e:
        logger.error(f"Error in get_market_climate_sentiment: {e}")
        return f"Error fetching market sentiment: {str(e)}"


# ==================== REGULATORY TOOLS ====================

@tool
def get_country_climate_policies(country_code: str) -> str:
    """
    Get climate policies and regulations for a country.
    
    Args:
        country_code: ISO 3-letter country code (e.g., USA, GBR, DEU, CHN, IND)
        
    Returns:
        List of climate policies, emissions data, and NDC targets.
    """
    try:
        client = get_regulatory_client()
        data = client.get_country_climate_profile(country_code)
        
        output = f"🌍 Climate Profile: {country_code.upper()}\n"
        output += "━" * 40 + "\n"
        
        # Emissions
        emissions = data.get("emissions")
        if emissions and "error" not in emissions:
            output += "\n📊 Emissions Data:\n"
            recent = emissions.get("recent_emissions", {})
            for year in list(sorted(recent.keys(), reverse=True))[:3]:
                total = recent[year].get("Total GHG") or recent[year].get("All GHG")
                if total:
                    output += f"  • {year}: {total:,.0f} MtCO2e\n"
        
        # NDC Targets
        ndc = data.get("ndc_targets")
        if ndc and "error" not in ndc:
            output += f"\n🎯 NDC Targets: {ndc.get('targets_count', 0)} commitments\n"
        
        # Policies
        policies = data.get("policies")
        if policies and "error" not in policies:
            output += f"\n📋 Climate Policies: {policies.get('policies_count', 0)} active\n"
            for p in policies.get("policies", [])[:5]:
                output += f"  • {p.get('name', 'Unknown policy')[:50]}...\n"
        
        output += "\n━" * 40
        output += "\nSource: Climate Watch + Climate Policy Database (Live)"
        
        return output
    except Exception as e:
        logger.error(f"Error in get_country_climate_policies: {e}")
        return f"Error fetching climate policies: {str(e)}"


@tool
def get_country_emissions(country_code: str) -> str:
    """
    Get historical greenhouse gas emissions for a country.
    
    Args:
        country_code: ISO 3-letter country code (e.g., USA, CHN, IND, DEU)
        
    Returns:
        Historical emissions data from Climate Watch.
    """
    try:
        client = get_climate_watch_client()
        data = client.get_country_emissions(country_code)
        
        if "error" in data:
            return f"Error: {data['error']}"
        
        output = f"📊 Emissions History: {country_code.upper()}\n"
        output += "━" * 40 + "\n"
        output += f"Data Source: {data.get('data_source', 'CAIT')}\n"
        output += f"Years Available: {data.get('years_available', 'N/A')}\n\n"
        
        recent = data.get("recent_emissions", {})
        for year in sorted(recent.keys(), reverse=True)[:5]:
            year_data = recent[year]
            total = year_data.get("Total GHG") or year_data.get("All GHG") or sum(year_data.values())
            output += f"  📅 {year}: {total:,.0f} MtCO2e\n"
        
        output += "\n━" * 40
        output += "\nSource: Climate Watch - CAIT (Live)"
        
        return output
    except Exception as e:
        logger.error(f"Error in get_country_emissions: {e}")
        return f"Error fetching emissions data: {str(e)}"


@tool
def assess_regulatory_risk(country_code: str) -> str:
    """
    Assess regulatory risk for investing in a country based on climate policies.
    
    Args:
        country_code: ISO 3-letter country code
        
    Returns:
        Regulatory risk assessment with score and recommendations.
    """
    try:
        client = get_regulatory_client()
        data = client.assess_regulatory_risk(country_code)
        
        if "error" in data:
            return f"Error: {data['error']}"
        
        score = data.get("regulatory_risk_score", 50)
        emoji = "🔴" if score >= 70 else "🟠" if score >= 50 else "🟡" if score >= 30 else "🟢"
        
        factors = data.get("risk_factors", [])
        factors_str = "\n".join([f"  • {f}" for f in factors]) if factors else "  • No major risk factors identified"
        
        recommendations = data.get("recommendations", [])
        rec_str = "\n".join([f"  • {r}" for r in recommendations])
        
        return f"""
{emoji} Regulatory Risk: {country_code.upper()}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Risk Score: {score}/100
Risk Level: {data.get('risk_level', 'Unknown')}

📋 Risk Factors:
{factors_str}

💡 Recommendations:
{rec_str}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Source: Climate Policy Analysis (Live)
"""
    except Exception as e:
        logger.error(f"Error in assess_regulatory_risk: {e}")
        return f"Error assessing regulatory risk: {str(e)}"


@tool
def get_carbon_pricing_overview() -> str:
    """
    Get overview of global carbon pricing initiatives (carbon taxes and ETS).
    
    Returns:
        Summary of carbon pricing systems worldwide with current prices.
    """
    try:
        client = get_regulatory_client()
        data = client.get_global_carbon_pricing_overview()
        
        if "error" in data:
            return f"Error: {data['error']}"
        
        output = "🌍 Global Carbon Pricing Overview\n"
        output += "━" * 45 + "\n"
        output += f"\nHighest Price: {data.get('highest_price', 'N/A')}\n\n"
        
        output += "📊 Major Carbon Pricing Systems:\n"
        for name, info in data.get("known_carbon_prices", {}).items():
            price = info.get("price_usd", 0)
            price_type = info.get("type", "Unknown")
            output += f"  • {name}: ~${price}/tCO2e ({price_type})\n"
        
        output += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Note: Prices are approximate and fluctuate daily.
Source: World Bank Carbon Pricing Dashboard + Policy Database
"""
        return output
    except Exception as e:
        logger.error(f"Error in get_carbon_pricing_overview: {e}")
        return f"Error fetching carbon pricing data: {str(e)}"


# ==================== COMBINED ANALYSIS TOOLS ====================

@tool
def analyze_investment_climate_risk(ticker: str, country_code: str = "") -> str:
    """
    Comprehensive climate risk analysis for an investment, combining:
    - Stock climate risk exposure
    - ESG scores
    - Regulatory risk (if country provided)
    - Recent climate news
    
    Args:
        ticker: Stock ticker symbol
        country_code: Optional ISO 3-letter country code for regulatory analysis
        
    Returns:
        Comprehensive climate risk report.
    """
    try:
        yahoo = get_yahoo_client()
        finnhub = get_finnhub_client()
        
        # Get stock climate risk
        stock_risk = yahoo.get_climate_risk_profile(ticker)
        
        # Get ESG scores
        esg = finnhub.get_esg_scores(ticker)
        
        # Get climate news
        news = finnhub.get_climate_news(ticker)
        
        output = f"""
════════════════════════════════════════════════
🌍 CLIMATE RISK REPORT: {ticker.upper()}
════════════════════════════════════════════════

📋 COMPANY OVERVIEW
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Company: {stock_risk.get('company_name', 'Unknown')}
Sector: {stock_risk.get('sector', 'Unknown')}
Industry: {stock_risk.get('industry', 'Unknown')}

🌡️ CLIMATE RISK ASSESSMENT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        risk = stock_risk.get("climate_risk", {})
        score = risk.get("risk_score", 50)
        emoji = "🔴 HIGH" if score >= 70 else "🟠 ELEVATED" if score >= 50 else "🟡 MODERATE" if score >= 30 else "🟢 LOW"
        
        output += f"Risk Score: {score}/100 ({emoji})\n"
        output += "Key Risks:\n"
        for r in risk.get("key_risks", [])[:3]:
            output += f"  • {r}\n"
        
        output += """
🌱 ESG PROFILE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        if esg.get("found"):
            output += f"Total ESG: {esg.get('total_esg_score', 'N/A')}\n"
            output += f"Environmental: {esg.get('environmental_score', 'N/A')}\n"
            output += f"Social: {esg.get('social_score', 'N/A')}\n"
            output += f"Governance: {esg.get('governance_score', 'N/A')}\n"
        else:
            output += "ESG data not available for this ticker.\n"
        
        # Regulatory risk if country provided
        if country_code:
            reg_client = get_regulatory_client()
            reg_risk = reg_client.assess_regulatory_risk(country_code)
            
            output += f"""
📜 REGULATORY ENVIRONMENT ({country_code.upper()})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Regulatory Risk: {reg_risk.get('regulatory_risk_score', 'N/A')}/100
Level: {reg_risk.get('risk_level', 'Unknown')}
"""
        
        output += """
📰 RECENT CLIMATE NEWS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        if news and not (len(news) == 1 and "message" in news[0]):
            for item in news[:3]:
                output += f"• {item.get('headline', 'N/A')[:60]}...\n"
        else:
            output += "No recent climate-related news.\n"
        
        output += """
════════════════════════════════════════════════
Sources: Yahoo Finance, Finnhub, Climate Watch (Live)
════════════════════════════════════════════════
"""
        return output
    except Exception as e:
        logger.error(f"Error in analyze_investment_climate_risk: {e}")
        return f"Error generating climate risk report: {str(e)}"
