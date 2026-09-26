from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import logging
import requests

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    yf = None

from .base import BaseDataSource

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ML-based climate risk model (replaces the old hardcoded sector lookup)
from ..models.climate_risk_model import ClimateRiskModel
_climate_risk_model = ClimateRiskModel()


class YahooFinanceClient(BaseDataSource):
    def __init__(self):
        super().__init__(api_key=None, base_url="https://finance.yahoo.com")
        if not YFINANCE_AVAILABLE:
            self.logger.warning("yfinance not installed. Run: pip install yfinance")
    
    def health_check(self) -> bool:
        if not YFINANCE_AVAILABLE:
            return False
        try:
            test = yf.Ticker("AAPL")
            info = test.fast_info
            return hasattr(info, 'last_price')
        except Exception:
            return False
    
    def fetch_data(self, ticker: str) -> Dict[str, Any]:
        return self.get_company_info(ticker)
    
    def get_current_price(self, ticker: str) -> Dict[str, Any]:
        if not YFINANCE_AVAILABLE:
            return {"error": "yfinance not installed. Run: pip install yfinance"}
        
        try:
            stock = yf.Ticker(ticker.upper())
            info = stock.info
            fast_info = stock.fast_info
            
            return {
                "ticker": ticker.upper(),
                "price": fast_info.last_price if hasattr(fast_info, 'last_price') else info.get("regularMarketPrice"),
                "previous_close": info.get("previousClose") or (fast_info.previous_close if hasattr(fast_info, 'previous_close') else None),
                "open": info.get("open") or (fast_info.open if hasattr(fast_info, 'open') else None),
                "day_high": info.get("dayHigh") or (fast_info.day_high if hasattr(fast_info, 'day_high') else None),
                "day_low": info.get("dayLow") or (fast_info.day_low if hasattr(fast_info, 'day_low') else None),
                "volume": info.get("volume"),
                "market_cap": info.get("marketCap") or (fast_info.market_cap if hasattr(fast_info, 'market_cap') else None),
                "currency": info.get("currency", "USD"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh") or (fast_info.year_high if hasattr(fast_info, 'year_high') else None),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow") or (fast_info.year_low if hasattr(fast_info, 'year_low') else None),
                "timestamp": datetime.now().isoformat(),
                "source": "Yahoo Finance (Live)"
            }
        except Exception as e:
            self.logger.error(f"Error fetching price for {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    def get_company_info(self, ticker: str) -> Dict[str, Any]:
        if not YFINANCE_AVAILABLE:
            return {"error": "yfinance not installed. Run: pip install yfinance"}
        
        try:
            stock = yf.Ticker(ticker.upper())
            info = stock.info
            
            return {
                "ticker": ticker.upper(),
                "name": info.get("longName") or info.get("shortName", "Unknown"),
                "sector": info.get("sector", "Unknown"),
                "industry": info.get("industry", "Unknown"),
                "country": info.get("country"),
                "website": info.get("website"),
                "employees": info.get("fullTimeEmployees"),
                "market_cap": info.get("marketCap"),
                "description": (info.get("longBusinessSummary") or "")[:500],
                "price": info.get("regularMarketPrice") or info.get("currentPrice"),
                "pe_ratio": info.get("trailingPE"),
                "forward_pe": info.get("forwardPE"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
                "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
                "average_volume": info.get("averageVolume"),
                "source": "Yahoo Finance (Live)"
            }
        except Exception as e:
            self.logger.error(f"Error fetching company info for {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    def get_historical_prices(
        self, 
        ticker: str, 
        period: str = "1mo",
        interval: str = "1d"
    ) -> Dict[str, Any]:
        if not YFINANCE_AVAILABLE:
            return {"error": "yfinance not installed"}
        
        try:
            stock = yf.Ticker(ticker.upper())
            hist = stock.history(period=period, interval=interval)
            
            if hist.empty:
                return {"error": f"No historical data for {ticker}", "ticker": ticker}
            
            records = []
            for date, row in hist.iterrows():
                records.append({
                    "date": date.strftime("%Y-%m-%d %H:%M:%S") if interval in ['1m', '2m', '5m', '15m', '30m', '60m', '90m', '1h'] else date.strftime("%Y-%m-%d"),
                    "open": round(row["Open"], 2),
                    "high": round(row["High"], 2),
                    "low": round(row["Low"], 2),
                    "close": round(row["Close"], 2),
                    "volume": int(row["Volume"])
                })
            
            # Calculate performance metrics
            first_close = records[0]["close"] if records else 0
            last_close = records[-1]["close"] if records else 0
            change_pct = ((last_close - first_close) / first_close * 100) if first_close else 0
            
            return {
                "ticker": ticker.upper(),
                "period": period,
                "interval": interval,
                "data_points": len(records),
                "start_price": first_close,
                "end_price": last_close,
                "change_percent": round(change_pct, 2),
                "prices": records,
                "source": "Yahoo Finance (Live)"
            }
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {ticker}: {e}")
            return {"error": str(e), "ticker": ticker}
    
    def get_climate_risk_profile(self, ticker: str) -> Dict[str, Any]:
        """
        ML-based climate risk profile.
        Uses the ClimateRiskModel which pulls real financial features and
        ESG data — no hardcoded sector/industry scores.
        """
        company_info = self.get_company_info(ticker)

        if "error" in company_info:
            return company_info

        # Run the ML model
        model_result = _climate_risk_model.score(ticker)

        if "error" in model_result:
            return model_result

        return {
            "ticker": ticker.upper(),
            "company_name": company_info.get("name"),
            "sector": company_info.get("sector", "Unknown"),
            "industry": company_info.get("industry", "Unknown"),
            "country": company_info.get("country"),
            "market_cap": company_info.get("market_cap"),
            "climate_risk": {
                "risk_level": model_result["risk_level"],
                "risk_score": model_result["risk_score"],
                "key_risks": model_result["key_risks"],
            },
            "score_breakdown": {
                "source": model_result["score_source"],
                "pillars": model_result["pillars"],
                "feature_contributions": model_result["feature_contributions"],
            },
            "esg_data": model_result.get("esg_data"),
            "historical_volatility": model_result.get("historical_volatility"),
            "source": "ML Model + Yahoo Finance (Live) + Finnhub ESG",
        }
    
    def get_news(self, ticker: str) -> List[Dict[str, Any]]:
        if not YFINANCE_AVAILABLE:
            return [{"error": "yfinance not installed"}]
        
        try:
            stock = yf.Ticker(ticker.upper())
            news = stock.news
            
            result = []
            for item in news[:10]:  # Limit to 10 items
                result.append({
                    "title": item.get("title"),
                    "publisher": item.get("publisher"),
                    "link": item.get("link"),
                    "published": datetime.fromtimestamp(item.get("providerPublishTime", 0)).isoformat() if item.get("providerPublishTime") else None,
                    "type": item.get("type"),
                    "thumbnail": item.get("thumbnail", {}).get("resolutions", [{}])[0].get("url") if item.get("thumbnail") else None
                })
            
            return result
        except Exception as e:
            self.logger.error(f"Error fetching news for {ticker}: {e}")
            return [{"error": str(e)}]
    
    def calculate_portfolio_risk(self, tickers: List[str]) -> Dict[str, Any]:
        results = []
        total_risk_score = 0
        total_market_cap = 0
        
        for ticker in tickers:
            profile = self.get_climate_risk_profile(ticker)
            
            if "error" not in profile:
                risk_score = profile["climate_risk"]["risk_score"]
                market_cap = profile.get("market_cap") or 1
                
                results.append({
                    "ticker": ticker.upper(),
                    "company": profile.get("company_name"),
                    "sector": profile.get("sector"),
                    "risk_score": risk_score,
                    "risk_level": profile["climate_risk"]["risk_level"],
                    "market_cap": market_cap
                })
                
                # Weight by market cap
                total_risk_score += risk_score * market_cap
                total_market_cap += market_cap
        
        weighted_risk = total_risk_score / total_market_cap if total_market_cap > 0 else 0
        simple_avg = sum(r["risk_score"] for r in results) / len(results) if results else 0
        
        results.sort(key=lambda x: x["risk_score"], reverse=True)
        
        return {
            "portfolio_size": len(tickers),
            "analyzed": len(results),
            "weighted_average_risk": round(weighted_risk, 1),
            "simple_average_risk": round(simple_avg, 1),
            "risk_level": "Very High" if weighted_risk >= 70 else "High" if weighted_risk >= 50 else "Moderate" if weighted_risk >= 30 else "Low",
            "highest_risk_stocks": results[:3],
            "lowest_risk_stocks": results[-3:] if len(results) > 3 else [],
            "all_stocks": results,
            "source": "Yahoo Finance (Live)"
        }
