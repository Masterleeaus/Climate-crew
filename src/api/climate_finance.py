from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os

from ..agents.climate_finance_orchestrator import ClimateFinanceOrchestrator
from ..agents.market_impact_agent import MarketImpactAgent
from ..agents.regulatory_risk_agent import RegulatoryRiskAgent
from ..agents.esg_agent import ESGAgent

router = APIRouter(prefix="/climate-finance", tags=["Climate Finance"])

class QueryRequest(BaseModel):
    query: str

class PortfolioRequest(BaseModel):
    tickers: List[str]

class CountryRequest(BaseModel):
    country_code: str

class QueryResponse(BaseModel):
    response: str
    agent: Optional[str] = None

class PillarScores(BaseModel):
    physical_risk: Optional[int] = None
    transition_risk: Optional[int] = None
    financial_vulnerability: Optional[int] = None
    market_sentiment: Optional[int] = None

class FeatureContribution(BaseModel):
    feature: str
    value: str
    percentile: Optional[int] = None
    risk_impact: Optional[int] = None
    weight: Optional[float] = None
    correlation: Optional[float] = None
    direction: str

class ScoreBreakdown(BaseModel):
    source: str
    pillars: PillarScores
    feature_contributions: List[FeatureContribution] = []

class RiskResponse(BaseModel):
    ticker: str
    company: Optional[str]
    sector: Optional[str]
    industry: Optional[str] = None
    risk_score: int
    risk_level: str
    key_risks: List[str]
    score_breakdown: Optional[ScoreBreakdown] = None
    historical_volatility: Optional[float] = None

class PortfolioRiskResponse(BaseModel):
    portfolio_size: int
    analyzed: int
    weighted_risk: float
    risk_level: str
    stocks: List[Dict[str, Any]]

_orchestrator = None
_market_agent = None
_regulatory_agent = None
_esg_agent = None

def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        _orchestrator = ClimateFinanceOrchestrator(google_api_key=api_key)
    return _orchestrator

def get_market_agent():
    global _market_agent
    if _market_agent is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        _market_agent = MarketImpactAgent(google_api_key=api_key)
    return _market_agent

def get_regulatory_agent():
    global _regulatory_agent
    if _regulatory_agent is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        _regulatory_agent = RegulatoryRiskAgent(google_api_key=api_key)
    return _regulatory_agent

def get_esg_agent():
    global _esg_agent
    if _esg_agent is None:
        api_key = os.getenv("GOOGLE_API_KEY")
        _esg_agent = ESGAgent(google_api_key=api_key)
    return _esg_agent


@router.post("/chat", response_model=QueryResponse, summary="Chat with Climate Finance Orchestrator")
async def chat_climate_finance(request: QueryRequest):
    try:
        orchestrator = get_orchestrator()
        response = orchestrator.run(request.query)
        return QueryResponse(response=response, agent="ClimateFinanceOrchestrator")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/market/chat", response_model=QueryResponse, summary="Chat with Market Impact Agent")
async def chat_market_impact(request: QueryRequest):
    try:
        agent = get_market_agent()
        response = agent.run(request.query)
        return QueryResponse(response=response, agent="MarketImpactAgent")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/regulatory/chat", response_model=QueryResponse, summary="Chat with Regulatory Risk Agent")
async def chat_regulatory_risk(request: QueryRequest):
    try:
        agent = get_regulatory_agent()
        response = agent.run(request.query)
        return QueryResponse(response=response, agent="RegulatoryRiskAgent")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/esg/chat", response_model=QueryResponse, summary="Chat with ESG Agent")
async def chat_esg(request: QueryRequest):
    try:
        agent = get_esg_agent()
        response = agent.run(request.query)
        return QueryResponse(response=response, agent="ESGAgent")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{ticker}/climate-risk", response_model=RiskResponse, summary="Get stock climate risk")
async def get_stock_climate_risk(ticker: str):
    try:
        from ..data_sources.yahoo_finance import YahooFinanceClient
        client = YahooFinanceClient()
        data = client.get_climate_risk_profile(ticker)
        
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
        
        risk = data.get("climate_risk", {})
        
        # Build score breakdown from ML model output
        breakdown_data = data.get("score_breakdown")
        score_breakdown = None
        if breakdown_data:
            pillars = breakdown_data.get("pillars", {})
            contribs = breakdown_data.get("feature_contributions", [])
            score_breakdown = ScoreBreakdown(
                source=breakdown_data.get("source", "ML Model"),
                pillars=PillarScores(**pillars),
                feature_contributions=[
                    FeatureContribution(**c) for c in contribs
                ],
            )
        
        return RiskResponse(
            ticker=ticker.upper(),
            company=data.get("company_name"),
            sector=data.get("sector"),
            industry=data.get("industry"),
            risk_score=risk.get("risk_score", 0),
            risk_level=risk.get("risk_level", "Unknown"),
            key_risks=risk.get("key_risks", []),
            score_breakdown=score_breakdown,
            historical_volatility=data.get("historical_volatility"),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/portfolio/climate-risk", response_model=PortfolioRiskResponse, summary="Get portfolio climate risk")
async def get_portfolio_climate_risk(request: PortfolioRequest):
    try:
        from ..data_sources.yahoo_finance import YahooFinanceClient
        client = YahooFinanceClient()
        data = client.calculate_portfolio_risk(request.tickers)
        
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
        
        return PortfolioRiskResponse(
            portfolio_size=data.get("portfolio_size", 0),
            analyzed=data.get("analyzed", 0),
            weighted_risk=data.get("weighted_average_risk", 0),
            risk_level=data.get("risk_level", "Unknown"),
            stocks=data.get("all_stocks", [])
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/country/{country_code}/regulatory-risk", summary="Get country regulatory risk")
async def get_country_regulatory_risk(country_code: str):
    try:
        from ..data_sources.regulatory_data import RegulatoryDataClient
        client = RegulatoryDataClient()
        return client.assess_regulatory_risk(country_code)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/carbon-prices", summary="Get global carbon prices")
async def get_carbon_prices():
    try:
        from ..data_sources.regulatory_data import CarbonPricingClient
        client = CarbonPricingClient()
        return client.get_all_prices()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{ticker}/quote", summary="Get stock price quote")
async def get_stock_quote(ticker: str):
    try:
        from ..data_sources.yahoo_finance import YahooFinanceClient
        client = YahooFinanceClient()
        data = client.get_current_price(ticker)
        
        if "error" in data:
            raise HTTPException(status_code=400, detail=data["error"])
        
        return data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{ticker}/esg", summary="Get stock ESG scores")
async def get_stock_esg(ticker: str):
    try:
        from ..data_sources.esg_data import FinnhubClient
        client = FinnhubClient()
        return client.get_esg_scores(ticker)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents", summary="List available climate finance agents")
async def list_climate_finance_agents():
    return {
        "agents": [
            {
                "name": "climate_finance",
                "description": "Orchestrator that routes to specialized agents",
                "endpoint": "/climate-finance/chat"
            },
            {
                "name": "market_impact",
                "description": "Stock prices, climate risk analysis, portfolio assessment",
                "endpoint": "/climate-finance/market/chat"
            },
            {
                "name": "regulatory_risk",
                "description": "Carbon pricing, regulatory risk, country comparisons",
                "endpoint": "/climate-finance/regulatory/chat"
            },
            {
                "name": "esg",
                "description": "ESG scores, sustainability news, market sentiment",
                "endpoint": "/climate-finance/esg/chat"
            }
        ],
        "data_endpoints": [
            "/climate-finance/stock/{ticker}/climate-risk",
            "/climate-finance/portfolio/climate-risk",
            "/climate-finance/country/{country_code}/regulatory-risk",
            "/climate-finance/carbon-prices",
            "/climate-finance/stock/{ticker}/esg"
        ]
    }
