from typing import Any, Dict, List, Optional, TYPE_CHECKING
from datetime import datetime

from .base import BaseAgent
from .market_impact_agent import MarketImpactAgent
from .regulatory_risk_agent import RegulatoryRiskAgent
from .esg_agent import ESGAgent

if TYPE_CHECKING:
    from ..memory import MemoryManager


class ClimateFinanceOrchestrator(BaseAgent):
    
    def __init__(
        self,
        google_api_key: Optional[str] = None,
        memory_manager: Optional['MemoryManager'] = None,
        enable_memory: bool = True
    ):
        super().__init__("ClimateFinanceOrchestrator", google_api_key, memory_manager, enable_memory)
        
        self.agents = {
            "market_impact": MarketImpactAgent(google_api_key, memory_manager=memory_manager),
            "regulatory_risk": RegulatoryRiskAgent(google_api_key, memory_manager=memory_manager),
            "esg": ESGAgent(google_api_key, memory_manager=memory_manager)
        }
    
    def set_memory_manager(self, memory_manager: 'MemoryManager'):
        self.memory = memory_manager
        for agent in self.agents.values():
            agent.set_memory_manager(memory_manager)
    
    def get_tools(self):
        return []
    
    def get_system_prompt(self) -> str:
        return "You are a climate finance intelligence orchestrator."
    
    def run(self, query: str) -> str:
        query_lower = query.lower()
        
        keywords = {
            "market_impact": ["stock", "price", "ticker", "portfolio", "invest", "buy", "sell", "share", "market", "trade"],
            "regulatory_risk": ["regulation", "regulatory", "carbon", "tax", "policy", "ets", "emission", "government", "law", "compliance", "country", "risk"],
            "esg": ["esg", "environmental", "social", "governance", "sustainability", "sustainable", "green", "ethical", "rating", "score", "news", "sentiment"]
        }
        
        for agent_name, kws in keywords.items():
            if any(kw in query_lower for kw in kws):
                self.log(f"Routing to {agent_name}")
                return self.agents[agent_name].run(query)
        
        self.log("Defaulting to market_impact agent")
        return self.agents["market_impact"].run(query)
    
    def analyze_investment(self, ticker: str, country_code: str = "USA") -> Dict[str, Any]:
        market = self.agents["market_impact"]
        client = market.get_tools()[1].__wrapped__(ticker)
        
        regulatory = self.agents["regulatory_risk"]
        reg_tools = regulatory.get_tools()
        reg_risk = reg_tools[2].__wrapped__(country_code)
        
        return {
            "ticker": ticker,
            "country": country_code,
            "climate_risk": client,
            "regulatory_risk": reg_risk
        }
    
    def get_alerts(self) -> List[Dict]:
        return []
