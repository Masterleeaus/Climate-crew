from typing import Any, Dict, List, Optional, Callable, TYPE_CHECKING
from datetime import datetime

from langchain_core.tools import tool

from .base import BaseAgent
from ..data_sources.regulatory_data import RegulatoryDataClient, CarbonPricingClient
from ..data_sources.web_search import WebSearchClient

if TYPE_CHECKING:
    from ..memory import MemoryManager

regulatory_client = RegulatoryDataClient()
carbon_client = CarbonPricingClient()
web_search_client = WebSearchClient()

@tool
def get_carbon_prices() -> str:
    """Get global carbon pricing overview - all major carbon taxes and ETS systems worldwide."""
    try:
        data = carbon_client.get_all_prices()
        
        output = f"Global Carbon Pricing ({data.get('count')} systems):\n"
        output += f"Average Price: ${data.get('average_usd', 0):.0f}/tCO2\n\n"
        
        for p in data.get("prices", [])[:8]:
            output += f"- {p['name']}: ${p['price_usd']}/tCO2 ({p['type']})\n"
        
        return output
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_carbon_price(jurisdiction: str) -> str:
    """Get carbon price for a specific jurisdiction (e.g., EU ETS, California, China, Sweden)."""
    try:
        data = carbon_client.get_price(jurisdiction)
        if not data:
            return f"No carbon pricing data found for {jurisdiction}"
        
        sectors = ", ".join(data.get("sectors", []))
        
        return f"""
{data.get('name')}:
Price: ${data.get('price_usd')}/tCO2 ({data.get('price_local')} {data.get('currency')})
Type: {data.get('type')}
Coverage: {data.get('coverage')}
Sectors: {sectors}
Trend: {data.get('trend')}
"""
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def assess_regulatory_risk(country_code: str) -> str:
    """Assess climate regulatory risk for investing in a country. Use ISO 3-letter codes (USA, DEU, CHN, IND, GBR)."""
    try:
        data = regulatory_client.assess_regulatory_risk(country_code)
        if "error" in data:
            return f"Error: {data['error']}"
        
        factors = "\n".join([f"- {f}" for f in data.get("risk_factors", [])])
        recommendations = "\n".join([f"- {r}" for r in data.get("recommendations", [])])
        
        return f"""
Regulatory Risk: {data.get('country')}
Risk Score: {data.get('regulatory_risk_score')}/100
Risk Level: {data.get('risk_level')}

Risk Factors:
{factors}

Recommendations:
{recommendations}
"""
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def compare_regulatory_risk(country_codes: str) -> str:
    """Compare regulatory risk across multiple countries. Provide comma-separated ISO 3-letter codes (e.g., USA,DEU,CHN)."""
    try:
        codes = [c.strip().upper() for c in country_codes.split(",")]
        
        output = "Regulatory Risk Comparison:\n\n"
        
        results = []
        for code in codes:
            risk = regulatory_client.assess_regulatory_risk(code)
            results.append((code, risk.get('regulatory_risk_score', 0), risk.get('risk_level', 'Unknown')))
        
        results.sort(key=lambda x: x[1], reverse=True)
        
        for code, score, level in results:
            emoji = "🔴" if score >= 70 else "🟠" if score >= 50 else "🟡" if score >= 30 else "🟢"
            output += f"{emoji} {code}: {score}/100 ({level})\n"
        
        return output
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def get_carbon_pricing_overview() -> str:
    """Get comprehensive overview of global carbon pricing with statistics."""
    try:
        data = regulatory_client.get_global_carbon_pricing_overview()
        
        return f"""
Global Carbon Pricing Overview:
Total Systems: {data.get('total_systems')}
ETS Systems: {data.get('ets_systems')}
Carbon Taxes: {data.get('carbon_tax_systems')}
Highest Price: {data.get('highest_price')}
Average Price: ${data.get('average_price_usd')}/tCO2

Note: {data.get('note', '')}
"""
    except Exception as e:
        return f"Error: {str(e)}"


@tool
def web_search_regulatory(query: str) -> str:
    """Search the web for climate policy, carbon regulations, or government climate announcements."""
    try:
        results = web_search_client.search(query + " climate policy regulation carbon", max_results=5)
        if not results:
            return "No search results found."
        
        output = f"Web Search Results for: {query}\n\n"
        for i, r in enumerate(results[:5], 1):
            output += f"{i}. {r.title}\n   {r.snippet[:200]}...\n   URL: {r.url}\n\n"
        return output
    except Exception as e:
        return f"Error: {str(e)}"


class RegulatoryRiskAgent(BaseAgent):
    
    def __init__(self, google_api_key: Optional[str] = None, memory_manager: Optional['MemoryManager'] = None):
        super().__init__("RegulatoryRiskAgent", google_api_key, memory_manager=memory_manager)
    
    def get_tools(self) -> List[Callable]:
        return [
            get_carbon_prices,
            get_carbon_price,
            assess_regulatory_risk,
            compare_regulatory_risk,
            get_carbon_pricing_overview,
            web_search_regulatory
        ]
    
    def get_system_prompt(self) -> str:
        return """You are a Climate Regulatory Risk Analyst. You help users understand climate policies and their financial implications.

Your tools:
- get_carbon_prices: Get all global carbon prices
- get_carbon_price: Get price for a specific jurisdiction
- assess_regulatory_risk: Assess regulatory risk for a country
- compare_regulatory_risk: Compare risk across countries
- get_carbon_pricing_overview: Get global carbon pricing statistics

STRATEGY:
1. When asked about regulations, provide specific carbon prices
2. For investment questions, use assess_regulatory_risk
3. Compare multiple countries when relevant
4. Explain how regulations affect different sectors

Key Knowledge:
- EU ETS is the largest carbon market (~$85/tCO2)
- Sweden has the highest carbon tax (~$130/tCO2)
- China launched national ETS in 2021
- US has state-level systems (California)
- Carbon prices are expected to rise globally

Be helpful and explain regulatory impacts in simple terms."""
    
    def get_alerts(self) -> List[Dict]:
        return []
