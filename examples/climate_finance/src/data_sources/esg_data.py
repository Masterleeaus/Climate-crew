from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import logging
import requests
import os

from src.data_sources.base import BaseDataSource

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FinnhubClient(BaseDataSource):
    BASE_URL = "https://finnhub.io/api/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("FINNHUB_API_KEY")
        super().__init__(api_key=self.api_key, base_url=self.BASE_URL)
        
        if not self.api_key:
            self.logger.warning(
                "FINNHUB_API_KEY not set. Get a free key at: https://finnhub.io/"
            )
    
    def health_check(self) -> bool:
        """Check if Finnhub API is accessible."""
        if not self.api_key:
            return False
        try:
            response = requests.get(
                f"{self.BASE_URL}/quote",
                params={"symbol": "AAPL", "token": self.api_key},
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def fetch_data(self, ticker: str) -> Dict[str, Any]:
        """Fetch ESG data for a ticker."""
        return self.get_esg_scores(ticker)
    
    def _make_request(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Make authenticated request to Finnhub API."""
        if not self.api_key:
            return {"error": "FINNHUB_API_KEY not configured. Get free key at: https://finnhub.io/"}
        
        params = params or {}
        params["token"] = self.api_key
        
        try:
            response = requests.get(
                f"{self.BASE_URL}/{endpoint}",
                params=params,
                timeout=10
            )
            
            if response.status_code == 401:
                return {"error": "Invalid API key"}
            elif response.status_code == 429:
                return {"error": "Rate limit exceeded. Free tier: 60 calls/minute"}
            elif response.status_code != 200:
                return {"error": f"API error: {response.status_code}"}
            
            return response.json()
        except requests.exceptions.Timeout:
            return {"error": "Request timeout"}
        except Exception as e:
            return {"error": str(e)}
    
    def get_esg_scores(self, ticker: str) -> Dict[str, Any]:
        """
        Get REAL ESG scores for a company from Finnhub.
        Returns environmental, social, and governance scores.
        """
        result = self._make_request("stock/esg", {"symbol": ticker.upper()})
        
        if "error" in result:
            return result
        
        if not result:
            return {
                "ticker": ticker.upper(),
                "found": False,
                "message": "No ESG data available for this ticker",
                "source": "Finnhub"
            }
        
        # Finnhub returns totalESGScore, environmentalScore, socialScore, governanceScore
        return {
            "ticker": ticker.upper(),
            "found": True,
            "total_esg_score": result.get("totalESGScore"),
            "environmental_score": result.get("environmentalScore"),
            "social_score": result.get("socialScore"),
            "governance_score": result.get("governanceScore"),
            "last_updated": result.get("data", [{}])[0].get("period") if result.get("data") else None,
            "raw_data": result.get("data", [])[:5],  # Include some raw data
            "source": "Finnhub (Live)"
        }
    
    def get_company_news(
        self, 
        ticker: str, 
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get REAL company news from Finnhub.
        """
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")
        
        result = self._make_request("company-news", {
            "symbol": ticker.upper(),
            "from": from_date,
            "to": to_date
        })
        
        if isinstance(result, dict) and "error" in result:
            return [result]
        
        if not result or not isinstance(result, list):
            return [{"message": "No news found", "ticker": ticker}]
        
        news = []
        for item in result[:20]:  # Limit to 20 items
            news.append({
                "headline": item.get("headline"),
                "summary": item.get("summary", "")[:300],
                "source": item.get("source"),
                "url": item.get("url"),
                "datetime": datetime.fromtimestamp(item.get("datetime", 0)).isoformat() if item.get("datetime") else None,
                "category": item.get("category"),
                "related": item.get("related"),
                "image": item.get("image")
            })
        
        return news
    
    def get_climate_news(self, ticker: str) -> List[Dict[str, Any]]:
        all_news = self.get_company_news(ticker, days_back=30)
        
        climate_keywords = [
            "climate", "carbon", "emission", "esg", "sustainable", "sustainability",
            "green", "renewable", "net zero", "environmental", "pollution",
            "wildfire", "flood", "hurricane", "drought", "regulation", "regulatory"
        ]
        
        climate_news = []
        for item in all_news:
            headline = (item.get("headline") or "").lower()
            summary = (item.get("summary") or "").lower()
            
            if any(kw in headline or kw in summary for kw in climate_keywords):
                item["climate_relevance"] = "High"
                climate_news.append(item)
        
        return climate_news if climate_news else [{"message": "No climate-related news found", "ticker": ticker}]
    
    def get_company_profile(self, ticker: str) -> Dict[str, Any]:
        result = self._make_request("stock/profile2", {"symbol": ticker.upper()})
        
        if "error" in result:
            return result
        
        return {
            "ticker": ticker.upper(),
            "name": result.get("name"),
            "country": result.get("country"),
            "currency": result.get("currency"),
            "exchange": result.get("exchange"),
            "industry": result.get("finnhubIndustry"),
            "ipo_date": result.get("ipo"),
            "logo": result.get("logo"),
            "market_cap": result.get("marketCapitalization"),
            "employees": result.get("employeeTotal"),
            "website": result.get("weburl"),
            "source": "Finnhub (Live)"
        }
    
    def get_quote(self, ticker: str) -> Dict[str, Any]:
        result = self._make_request("quote", {"symbol": ticker.upper()})
        
        if "error" in result:
            return result
        
        return {
            "ticker": ticker.upper(),
            "current_price": result.get("c"),
            "change": result.get("d"),
            "percent_change": result.get("dp"),
            "high": result.get("h"),
            "low": result.get("l"),
            "open": result.get("o"),
            "previous_close": result.get("pc"),
            "timestamp": datetime.fromtimestamp(result.get("t", 0)).isoformat() if result.get("t") else None,
            "source": "Finnhub (Live)"
        }
    
    def search_news_by_keyword(
        self, 
        keyword: str, 
        category: str = "general"
    ) -> List[Dict[str, Any]]:
        result = self._make_request("news", {"category": category})
        
        if isinstance(result, dict) and "error" in result:
            return [result]
        
        if not result or not isinstance(result, list):
            return [{"message": "No news found"}]
        
        # Filter by keyword
        keyword_lower = keyword.lower()
        filtered = []
        
        for item in result:
            headline = (item.get("headline") or "").lower()
            summary = (item.get("summary") or "").lower()
            
            if keyword_lower in headline or keyword_lower in summary:
                filtered.append({
                    "headline": item.get("headline"),
                    "summary": item.get("summary", "")[:300],
                    "source": item.get("source"),
                    "url": item.get("url"),
                    "datetime": datetime.fromtimestamp(item.get("datetime", 0)).isoformat() if item.get("datetime") else None,
                    "category": item.get("category")
                })
        
        return filtered[:20] if filtered else [{"message": f"No news found for keyword: {keyword}"}]


class AlphaVantageClient(BaseDataSource):
    BASE_URL = "https://www.alphavantage.co/query"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
        super().__init__(api_key=self.api_key, base_url=self.BASE_URL)
        
        if not self.api_key:
            self.logger.warning(
                "ALPHA_VANTAGE_API_KEY not set. Get free key at: https://www.alphavantage.co/"
            )
    
    def health_check(self) -> bool:
        if not self.api_key:
            return False
        try:
            response = requests.get(
                self.BASE_URL,
                params={"function": "TIME_SERIES_INTRADAY", "symbol": "IBM", "interval": "5min", "apikey": self.api_key},
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False
    
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        return self.get_news_sentiment()
    
    def get_news_sentiment(
        self, 
        tickers: Optional[str] = None,
        topics: Optional[str] = None,
        limit: int = 50
    ) -> Dict[str, Any]:
        if not self.api_key:
            return {"error": "ALPHA_VANTAGE_API_KEY not configured"}
        
        params = {
            "function": "NEWS_SENTIMENT",
            "apikey": self.api_key,
            "limit": min(limit, 200)
        }
        
        if tickers:
            params["tickers"] = tickers.upper()
        if topics:
            params["topics"] = topics
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=15)
            data = response.json()
            
            if "Note" in data:
                return {"error": "Rate limit exceeded. Free tier: 25 calls/day"}
            if "Error Message" in data:
                return {"error": data["Error Message"]}
            
            articles = data.get("feed", [])
            
            processed = []
            for article in articles[:limit]:
                ticker_sentiment = article.get("ticker_sentiment", [])
                
                processed.append({
                    "title": article.get("title"),
                    "url": article.get("url"),
                    "time_published": article.get("time_published"),
                    "source": article.get("source"),
                    "summary": article.get("summary", "")[:400],
                    "overall_sentiment_score": article.get("overall_sentiment_score"),
                    "overall_sentiment_label": article.get("overall_sentiment_label"),
                    "ticker_sentiments": [
                        {
                            "ticker": ts.get("ticker"),
                            "relevance_score": ts.get("relevance_score"),
                            "sentiment_score": ts.get("ticker_sentiment_score"),
                            "sentiment_label": ts.get("ticker_sentiment_label")
                        }
                        for ts in ticker_sentiment[:5]
                    ]
                })
            
            return {
                "articles_count": len(processed),
                "sentiment_score_model": data.get("sentiment_score_definition"),
                "articles": processed,
                "source": "Alpha Vantage (Live)"
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    def get_climate_news_sentiment(self) -> Dict[str, Any]:
        return self.get_news_sentiment(topics="energy_transportation", limit=50)


class ESGDataClient(BaseDataSource):
    def __init__(
        self, 
        finnhub_api_key: Optional[str] = None
    ):
        super().__init__()
        self.finnhub = FinnhubClient(api_key=finnhub_api_key)
    
    def health_check(self) -> bool:
        return self.finnhub.health_check()
    
    def fetch_data(self, ticker: str) -> Dict[str, Any]:
        return self.get_esg_profile(ticker)
    
    def get_esg_profile(self, ticker: str) -> Dict[str, Any]:
        # Try Finnhub first
        finnhub_esg = self.finnhub.get_esg_scores(ticker)
        company_profile = self.finnhub.get_company_profile(ticker)
        
        if "error" not in finnhub_esg and finnhub_esg.get("found"):
            return {
                "ticker": ticker.upper(),
                "company": company_profile.get("name") if isinstance(company_profile, dict) else None,
                "esg_data": finnhub_esg,
                "news": self.finnhub.get_climate_news(ticker)[:5],
                "source": "Finnhub (Live)"
            }
        
        # Fallback: return message with company info
        return {
            "ticker": ticker.upper(),
            "company": company_profile.get("name") if isinstance(company_profile, dict) and "error" not in company_profile else None,
            "industry": company_profile.get("industry") if isinstance(company_profile, dict) else None,
            "esg_data": {
                "found": False,
                "message": "ESG data not available for this ticker. Consider using sector-based estimates."
            },
            "source": "Finnhub (Live) - Limited Data"
        }
    
    def compare_esg(self, tickers: List[str]) -> Dict[str, Any]:
        results = []
        
        for ticker in tickers:
            profile = self.get_esg_profile(ticker)
            esg_data = profile.get("esg_data", {})
            
            results.append({
                "ticker": ticker.upper(),
                "company": profile.get("company"),
                "total_esg_score": esg_data.get("total_esg_score"),
                "environmental_score": esg_data.get("environmental_score"),
                "social_score": esg_data.get("social_score"),
                "governance_score": esg_data.get("governance_score"),
                "data_available": esg_data.get("found", False)
            })
        
        # Sort by total ESG score (nulls last)
        results.sort(key=lambda x: x.get("total_esg_score") or -1, reverse=True)
        
        return {
            "comparison": results,
            "tickers_with_data": sum(1 for r in results if r.get("data_available")),
            "source": "Finnhub (Live)"
        }
