"""
Regulatory and Carbon Pricing Data Source.

Provides reliable carbon pricing data and regulatory risk assessment
using a curated database of global carbon pricing systems.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

from .base import BaseDataSource

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CarbonPricingClient(BaseDataSource):
    """
    Client for carbon pricing data.
    Uses World Bank Carbon Pricing Dashboard data (curated and reliable).
    """
    
    # Current carbon prices (updated January 2024)
    # Source: World Bank Carbon Pricing Dashboard
    CARBON_PRICES = {
        "EU_ETS": {
            "name": "EU Emissions Trading System",
            "price_usd": 85.0,
            "price_local": 78.0,
            "currency": "EUR",
            "type": "ETS",
            "coverage": "~40% of EU emissions",
            "sectors": ["Power", "Industry", "Aviation"],
            "trend": "rising",
            "last_updated": "2024-01"
        },
        "UK_ETS": {
            "name": "UK Emissions Trading Scheme",
            "price_usd": 70.0,
            "price_local": 55.0,
            "currency": "GBP",
            "type": "ETS",
            "coverage": "~30% of UK emissions",
            "sectors": ["Power", "Industry", "Aviation"],
            "trend": "stable",
            "last_updated": "2024-01"
        },
        "California_CaT": {
            "name": "California Cap-and-Trade",
            "price_usd": 35.0,
            "price_local": 35.0,
            "currency": "USD",
            "type": "ETS",
            "coverage": "~80% of CA emissions",
            "sectors": ["Power", "Industry", "Transport fuels"],
            "trend": "rising",
            "last_updated": "2024-01"
        },
        "China_ETS": {
            "name": "China National ETS",
            "price_usd": 12.0,
            "price_local": 85.0,
            "currency": "CNY",
            "type": "ETS",
            "coverage": "Power sector",
            "sectors": ["Power"],
            "trend": "rising",
            "last_updated": "2024-01"
        },
        "Canada_Federal": {
            "name": "Canada Federal Carbon Price",
            "price_usd": 65.0,
            "price_local": 80.0,
            "currency": "CAD",
            "type": "Carbon Tax",
            "coverage": "Economy-wide",
            "sectors": ["All"],
            "trend": "rising",
            "last_updated": "2024-01"
        },
        "Sweden": {
            "name": "Swedish Carbon Tax",
            "price_usd": 130.0,
            "price_local": 1330.0,
            "currency": "SEK",
            "type": "Carbon Tax",
            "coverage": "~40% of emissions",
            "sectors": ["Transport", "Heating"],
            "trend": "stable",
            "last_updated": "2024-01"
        },
        "Switzerland": {
            "name": "Swiss CO2 Levy",
            "price_usd": 130.0,
            "price_local": 120.0,
            "currency": "CHF",
            "type": "Carbon Tax",
            "coverage": "Heating fuels",
            "sectors": ["Buildings"],
            "trend": "stable",
            "last_updated": "2024-01"
        },
        "South_Korea": {
            "name": "Korea ETS",
            "price_usd": 15.0,
            "price_local": 20000.0,
            "currency": "KRW",
            "type": "ETS",
            "coverage": "~70% of emissions",
            "sectors": ["Power", "Industry", "Buildings", "Transport", "Waste"],
            "trend": "stable",
            "last_updated": "2024-01"
        },
        "New_Zealand": {
            "name": "New Zealand ETS",
            "price_usd": 45.0,
            "price_local": 70.0,
            "currency": "NZD",
            "type": "ETS",
            "coverage": "~50% of emissions",
            "sectors": ["Forestry", "Energy", "Industry"],
            "trend": "volatile",
            "last_updated": "2024-01"
        },
        "Germany_BEHG": {
            "name": "German National ETS (BEHG)",
            "price_usd": 45.0,
            "price_local": 45.0,
            "currency": "EUR",
            "type": "ETS",
            "coverage": "Transport, Buildings",
            "sectors": ["Transport", "Buildings"],
            "trend": "rising",
            "last_updated": "2024-01"
        }
    }
    
    def __init__(self):
        super().__init__()
    
    def health_check(self) -> bool:
        return True  # Static data always available
    
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        return self.get_all_prices()
    
    def get_all_prices(self) -> Dict[str, Any]:
        """Get all carbon prices."""
        prices = []
        for key, data in self.CARBON_PRICES.items():
            prices.append({
                "id": key,
                "jurisdiction": key.replace("_", " "),
                **data
            })
        
        # Sort by USD price descending
        prices.sort(key=lambda x: x["price_usd"], reverse=True)
        
        return {
            "count": len(prices),
            "prices": prices,
            "highest": prices[0] if prices else None,
            "average_usd": sum(p["price_usd"] for p in prices) / len(prices) if prices else 0,
            "source": "World Bank Carbon Pricing Dashboard (Updated 2024-01)"
        }
    
    def get_price(self, jurisdiction: str) -> Optional[Dict[str, Any]]:
        """Get carbon price for a specific jurisdiction."""
        # Try exact match first
        if jurisdiction in self.CARBON_PRICES:
            return {"id": jurisdiction, **self.CARBON_PRICES[jurisdiction]}
        
        # Try fuzzy match
        jurisdiction_lower = jurisdiction.lower().replace(" ", "_")
        for key, data in self.CARBON_PRICES.items():
            if jurisdiction_lower in key.lower() or jurisdiction_lower in data["name"].lower():
                return {"id": key, **data}
        
        return None
    
    def get_prices_by_type(self, price_type: str) -> List[Dict[str, Any]]:
        """Get carbon prices by type (ETS or Carbon Tax)."""
        results = []
        for key, data in self.CARBON_PRICES.items():
            if data["type"].lower() == price_type.lower():
                results.append({"id": key, **data})
        
        results.sort(key=lambda x: x["price_usd"], reverse=True)
        return results
    
    def compare_prices(self, jurisdictions: List[str]) -> Dict[str, Any]:
        """Compare carbon prices across jurisdictions."""
        results = []
        for j in jurisdictions:
            price = self.get_price(j)
            if price:
                results.append(price)
        
        return {
            "comparison": results,
            "count": len(results),
            "highest": max(results, key=lambda x: x["price_usd"]) if results else None,
            "lowest": min(results, key=lambda x: x["price_usd"]) if results else None
        }


class RegulatoryDataClient(BaseDataSource):
    """
    Client for regulatory risk assessment.
    Uses carbon pricing database and country-level regulatory knowledge.
    """
    
    def __init__(self):
        super().__init__()
        self.carbon_pricing = CarbonPricingClient()
    
    def health_check(self) -> bool:
        return True  # Static data always available
    
    def fetch_data(self, **kwargs) -> Dict[str, Any]:
        return self.assess_regulatory_risk(kwargs.get("country", "USA"))
    
    def assess_regulatory_risk(self, country_code: str) -> Dict[str, Any]:
        """
        Assess regulatory risk for investing in a country based on climate policies.
        """
        # Countries with strong carbon pricing
        high_carbon_price_countries = {
            "SWE": 90, "CHE": 85, "DEU": 75, "GBR": 70, "FRA": 70, 
            "CAN": 65, "NLD": 65, "NOR": 80, "DNK": 75, "FIN": 70,
            "AUT": 65, "IRL": 60, "BEL": 60, "LUX": 60
        }
        
        # Countries in major ETS systems
        ets_countries = {
            "USA": 40,  # California only
            "CHN": 35,  # National ETS
            "KOR": 50,  # Korea ETS
            "NZL": 55,  # NZ ETS
            "JPN": 30,  # Tokyo/Saitama ETS
        }
        
        # EU ETS member states
        eu_ets = ["DEU", "FRA", "ITA", "ESP", "POL", "NLD", "BEL", "GRC", 
                  "CZE", "PRT", "SWE", "HUN", "AUT", "BGR", "DNK", "FIN",
                  "SVK", "IRL", "HRV", "LTU", "SVN", "LVA", "EST", "CYP", "LUX", "MLT"]
        
        country = country_code.upper()
        risk_score = 30  # Base score
        factors = []
        
        # Check carbon pricing
        if country in high_carbon_price_countries:
            risk_score = max(risk_score, high_carbon_price_countries[country])
            factors.append(f"High carbon price jurisdiction")
        
        if country in ets_countries:
            risk_score = max(risk_score, ets_countries[country])
            factors.append("Has emissions trading system")
        
        if country in eu_ets:
            risk_score = max(risk_score, 70)
            factors.append("Part of EU ETS (~$85/tCO2)")
        
        # Major emitters face transition pressure
        major_emitters = ["CHN", "USA", "IND", "RUS", "JPN", "DEU", "IRN", "KOR", "SAU", "IDN"]
        if country in major_emitters:
            risk_score += 10
            factors.append("Major global emitter - transition pressure")
        
        risk_level = "Very High" if risk_score >= 70 else "High" if risk_score >= 50 else "Moderate" if risk_score >= 30 else "Low"
        
        recommendations = []
        if risk_score >= 70:
            recommendations = [
                "High carbon costs expected - factor into investment analysis",
                "Monitor regulatory developments closely",
                "Prefer companies with strong transition plans"
            ]
        elif risk_score >= 50:
            recommendations = [
                "Moderate carbon pricing exposure",
                "Review sector-specific regulations",
                "Consider ESG metrics in due diligence"
            ]
        else:
            recommendations = ["Standard climate risk monitoring recommended"]
        
        return {
            "country": country,
            "regulatory_risk_score": min(risk_score, 100),
            "risk_level": risk_level,
            "risk_factors": factors if factors else ["No major carbon pricing currently"],
            "recommendations": recommendations,
            "source": "Regulatory Risk Analysis"
        }
    
    def get_global_carbon_pricing_overview(self) -> Dict[str, Any]:
        """
        Get overview of global carbon pricing initiatives.
        """
        pricing = self.carbon_pricing.get_all_prices()
        
        # Add summary stats
        ets_count = sum(1 for p in pricing["prices"] if p["type"] == "ETS")
        tax_count = sum(1 for p in pricing["prices"] if p["type"] == "Carbon Tax")
        
        return {
            "total_systems": pricing["count"],
            "ets_systems": ets_count,
            "carbon_tax_systems": tax_count,
            "highest_price": f"{pricing['highest']['name']} (${pricing['highest']['price_usd']}/tCO2)" if pricing.get("highest") else "N/A",
            "average_price_usd": round(pricing["average_usd"], 2),
            "prices": pricing["prices"],
            "source": "World Bank Carbon Pricing Dashboard",
            "note": "Covers major carbon pricing systems globally. Prices updated January 2024."
        }
