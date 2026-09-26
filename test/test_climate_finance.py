"""
Test script for Climate-Finance Data Sources.
Tests all real API integrations.
"""

import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

def test_yahoo_finance():
    """Test Yahoo Finance client with real data."""
    print("\n" + "="*60)
    print("🧪 Testing Yahoo Finance Client")
    print("="*60)
    
    from src.data_sources.yahoo_finance import YahooFinanceClient
    
    client = YahooFinanceClient()
    
    # Test health check
    print("\n1. Health Check:")
    health = client.health_check()
    print(f"   Status: {'✅ Connected' if health else '❌ Failed'}")
    
    if not health:
        print("   ⚠️ yfinance may not be installed. Run: pip install yfinance")
        return False
    
    # Test get_current_price
    print("\n2. Get Current Price (AAPL):")
    price_data = client.get_current_price("AAPL")
    if "error" not in price_data:
        print(f"   ✅ Current Price: ${price_data.get('price', 'N/A')}")
        print(f"   Market Cap: ${price_data.get('market_cap', 0)/1e9:.1f}B")
    else:
        print(f"   ❌ Error: {price_data['error']}")
    
    # Test get_company_info
    print("\n3. Get Company Info (TSLA):")
    info = client.get_company_info("TSLA")
    if "error" not in info:
        print(f"   ✅ Name: {info.get('name')}")
        print(f"   Sector: {info.get('sector')}")
        print(f"   Industry: {info.get('industry')}")
    else:
        print(f"   ❌ Error: {info['error']}")
    
    # Test climate risk profile
    print("\n4. Get Climate Risk Profile (XOM - Energy Sector):")
    risk = client.get_climate_risk_profile("XOM")
    if "error" not in risk:
        print(f"   ✅ Company: {risk.get('company_name')}")
        print(f"   Sector: {risk.get('sector')}")
        print(f"   Risk Score: {risk.get('climate_risk', {}).get('risk_score')}/100")
        print(f"   Risk Level: {risk.get('climate_risk', {}).get('risk_level')}")
    else:
        print(f"   ❌ Error: {risk['error']}")
    
    # Test historical prices
    print("\n5. Get Historical Prices (MSFT - 1 month):")
    hist = client.get_historical_prices("MSFT", period="1mo")
    if "error" not in hist:
        print(f"   ✅ Data Points: {hist.get('data_points')}")
        print(f"   Period Change: {hist.get('change_percent')}%")
    else:
        print(f"   ❌ Error: {hist['error']}")
    
    # Test news
    print("\n6. Get Stock News (GOOGL):")
    news = client.get_news("GOOGL")
    if news and "error" not in news[0]:
        print(f"   ✅ Found {len(news)} news articles")
        if news and news[0].get('title'):
            title = news[0].get('title', 'N/A') or 'N/A'
            print(f"   Latest: {title[:50]}...")
    else:
        print(f"   ❌ No news or error")
    
    # Test portfolio risk
    print("\n7. Calculate Portfolio Risk (AAPL, TSLA, XOM, MSFT):")
    portfolio = client.calculate_portfolio_risk(["AAPL", "TSLA", "XOM", "MSFT"])
    if "error" not in portfolio:
        print(f"   ✅ Analyzed: {portfolio.get('analyzed')} stocks")
        print(f"   Weighted Risk: {portfolio.get('weighted_average_risk')}/100")
        print(f"   Risk Level: {portfolio.get('risk_level')}")
    else:
        print(f"   ❌ Error: {portfolio['error']}")
    
    print("\n✅ Yahoo Finance tests completed!")
    return True


def test_finnhub():
    """Test Finnhub client for ESG data."""
    print("\n" + "="*60)
    print("🧪 Testing Finnhub Client (ESG Data)")
    print("="*60)
    
    from src.data_sources.esg_data import FinnhubClient
    
    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        print("\n⚠️ FINNHUB_API_KEY not set in .env")
        print("   Get a free key at: https://finnhub.io/")
        print("   Add to .env: FINNHUB_API_KEY=your_key_here")
        return False
    
    client = FinnhubClient(api_key=api_key)
    
    # Test health check
    print("\n1. Health Check:")
    health = client.health_check()
    print(f"   Status: {'✅ Connected' if health else '❌ Failed'}")
    
    if not health:
        return False
    
    # Test get_quote
    print("\n2. Get Real-Time Quote (AAPL):")
    quote = client.get_quote("AAPL")
    if "error" not in quote:
        print(f"   ✅ Current: ${quote.get('current_price')}")
        print(f"   Change: {quote.get('percent_change')}%")
    else:
        print(f"   ❌ Error: {quote['error']}")
    
    # Test ESG scores
    print("\n3. Get ESG Scores (MSFT):")
    esg = client.get_esg_scores("MSFT")
    if "error" not in esg:
        print(f"   ✅ Found: {esg.get('found')}")
        print(f"   Total ESG: {esg.get('total_esg_score')}")
        print(f"   Environmental: {esg.get('environmental_score')}")
    else:
        print(f"   ❌ Error: {esg['error']}")
    
    # Test company news
    print("\n4. Get Company News (TSLA):")
    news = client.get_company_news("TSLA", days_back=7)
    if news and "error" not in news[0]:
        print(f"   ✅ Found {len(news)} articles")
        if news and news[0].get('headline'):
            print(f"   Latest: {news[0].get('headline', 'N/A')[:50]}...")
    else:
        print(f"   ❌ No news or error")
    
    print("\n✅ Finnhub tests completed!")
    return True


def test_alpha_vantage():
    """Test Alpha Vantage client for news sentiment."""
    print("\n" + "="*60)
    print("🧪 Testing Alpha Vantage Client (News Sentiment)")
    print("="*60)
    
    from src.data_sources.esg_data import AlphaVantageClient
    
    api_key = os.getenv("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        print("\n⚠️ ALPHA_VANTAGE_API_KEY not set in .env")
        print("   Get a free key at: https://www.alphavantage.co/support/#api-key")
        print("   Add to .env: ALPHA_VANTAGE_API_KEY=your_key_here")
        return False
    
    client = AlphaVantageClient(api_key=api_key)
    
    # Test news sentiment
    print("\n1. Get News Sentiment (Energy/Transportation):")
    sentiment = client.get_climate_news_sentiment()
    if "error" not in sentiment:
        print(f"   ✅ Articles: {sentiment.get('articles_count')}")
        if sentiment.get('articles'):
            article = sentiment['articles'][0]
            title = article.get('title', 'N/A') or 'N/A'
            print(f"   Sample: {title[:40]}...")
            print(f"   Sentiment: {article.get('overall_sentiment_label')}")
    else:
        print(f"   ❌ Error: {sentiment['error']}")
    
    print("\n✅ Alpha Vantage tests completed!")
    return True


def test_regulatory_client():
    """Test regulatory data client with carbon pricing."""
    print("\n" + "="*60)
    print("🧪 Testing Regulatory & Carbon Pricing Data")
    print("="*60)
    
    from src.data_sources.regulatory_data import RegulatoryDataClient, CarbonPricingClient
    
    # Test carbon pricing (always works - static data)
    print("\n1. Test Carbon Pricing Database:")
    carbon_client = CarbonPricingClient()
    prices = carbon_client.get_all_prices()
    print(f"   ✅ Carbon pricing systems: {prices.get('count')}")
    print(f"   Highest: {prices.get('highest', {}).get('name')} (${prices.get('highest', {}).get('price_usd')}/tCO2)")
    print(f"   Average price: ${prices.get('average_usd', 0):.0f}/tCO2")
    
    # Test get specific price
    print("\n2. Get Specific Carbon Price (EU ETS):")
    eu_price = carbon_client.get_price("EU_ETS")
    if eu_price:
        print(f"   ✅ {eu_price.get('name')}: ${eu_price.get('price_usd')}/tCO2")
        print(f"   Coverage: {eu_price.get('coverage')}")
        print(f"   Sectors: {', '.join(eu_price.get('sectors', []))}")
    
    # Test regulatory risk assessment
    client = RegulatoryDataClient()
    
    print("\n3. Assess Regulatory Risk (Multiple Countries):")
    countries = ["USA", "DEU", "CHN", "IND", "GBR"]
    for country in countries:
        risk = client.assess_regulatory_risk(country)
        score = risk.get('regulatory_risk_score', 0)
        level = risk.get('risk_level', 'Unknown')
        emoji = "🔴" if score >= 70 else "🟠" if score >= 50 else "🟡" if score >= 30 else "🟢"
        print(f"   {emoji} {country}: {score}/100 ({level})")
    
    # Test carbon pricing overview
    print("\n4. Get Global Carbon Pricing Overview:")
    overview = client.get_global_carbon_pricing_overview()
    print(f"   ✅ Total systems: {overview.get('total_systems')}")
    print(f"   ETS systems: {overview.get('ets_systems')}")
    print(f"   Carbon taxes: {overview.get('carbon_tax_systems')}")
    print(f"   Highest: {overview.get('highest_price')}")
    
    print("\n✅ Regulatory Data tests completed!")
    return True


def main():
    print("\n" + "🌍"*30)
    print("\n   CLIMATE-FINANCE DATA SOURCES TEST SUITE")
    print("\n" + "🌍"*30)
    
    results = {}
    
    # Test Yahoo Finance (no API key needed)
    results["Yahoo Finance"] = test_yahoo_finance()
    
    # Test Regulatory Client (no API key needed - uses static data)
    results["Regulatory/Carbon Pricing"] = test_regulatory_client()
    
    # Test Finnhub (needs API key)
    results["Finnhub (ESG)"] = test_finnhub()
    
    # Test Alpha Vantage (needs API key)
    results["Alpha Vantage"] = test_alpha_vantage()
    
    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    for name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED/SKIPPED"
        print(f"   {name}: {status}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\n   Total: {passed_count}/{total_count} passed")
    
    if passed_count < total_count:
        print("\n💡 To enable all features, add these to your .env file:")
        print("   FINNHUB_API_KEY=your_key_here      # Free at https://finnhub.io/")
        print("   ALPHA_VANTAGE_API_KEY=your_key     # Free at https://alphavantage.co/")
    
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
