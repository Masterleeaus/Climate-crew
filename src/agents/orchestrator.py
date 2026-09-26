from typing import Any, Dict, List, Optional, TYPE_CHECKING
from datetime import datetime
import time

from langsmith import traceable

from .base import BaseAgent
from .air_quality_agent import AirQualityAgent
from .earthquake_agent import EarthquakeAgent
from .wildfire_agent import WildfireAgent
from .flood_agent import FloodAgent
from .deforestation_agent import DeforestationAgent
from .ocean_agent import OceanAgent
from .biodiversity_agent import BiodiversityAgent
from .climate_anomaly_agent import ClimateAnomalyAgent
from .carbon_emissions_agent import CarbonEmissionsAgent
from .satellite_video_fusion_agent import SatelliteVideoFusionAgent
from .climatex_audit_agent import ClimateXAuditAgent
from .tool_builder_agent import ToolBuilderAgent
from .disaster_management_agent import DisasterManagementAgent

if TYPE_CHECKING:
    from ..memory import MemoryManager, AdvancedMemoryManager
    from ..rag import RAGManager


class OrchestratorAgent(BaseAgent):
    """
    Central orchestrator with dynamic LLM-based routing and meta-learning.
    
    Features:
    - Dynamic routing with LLM-based agent selection
    - Meta-learning from past routing decisions
    - Agent collaboration for complex queries
    - Fallback keyword-based routing
    """
    
    # Fallback keyword routing
    KEYWORDS = {
        "disaster_management": ["disaster", "emergency", "evacuate", "evacuation", "shelter", "crisis", "safety", "rescue", "humanitarian", "risk assessment", "alert", "warning"],
        "climatex_audit": ["audit", "verify", "verification", "carbon credit", "mrv", "report", "certification"],
        "air_quality": ["air", "aqi", "pollution", "pm2.5", "smog"],
        "earthquake": ["earthquake", "seismic", "tremor", "magnitude"],
        "wildfire": ["fire", "wildfire", "blaze", "burn"],
        "flood": ["flood", "rain", "precipitation", "storm"],
        "deforestation": ["forest", "tree", "deforestation", "amazon"],
        "ocean": ["ocean", "sea level", "coral", "marine", "reef", "sst", "waves"],
        "biodiversity": ["species", "wildlife", "animal", "biodiversity", "endangered", "habitat"],
        "climate_anomaly": ["heat wave", "heatwave", "anomaly", "extreme weather", "drought", "cold snap"],
        "carbon_emissions": ["carbon", "emission", "co2", "greenhouse", "ghg", "climate trace"],
        "satellite_video_fusion": ["satellite", "video", "fusion", "drone", "cctv", "imagery", "change detection"]
    }
    
    def __init__(
        self,
        google_api_key: Optional[str] = None,
        firms_api_key: Optional[str] = None,
        memory_manager: Optional['MemoryManager'] = None,
        enable_memory: bool = True,
        rag_manager: Optional['RAGManager'] = None,
        enable_rag: bool = True,
        enable_dynamic_routing: bool = True,
        enable_meta_learning: bool = True,
        enable_collaboration: bool = True
    ):
        super().__init__("OrchestratorAgent", google_api_key, memory_manager, enable_memory, rag_manager, enable_rag)
        
        self.enable_dynamic_routing = enable_dynamic_routing
        self.enable_meta_learning = enable_meta_learning
        self.enable_collaboration = enable_collaboration
        
        # Create ToolBuilder first
        tool_builder = ToolBuilderAgent(google_api_key=google_api_key, memory_manager=memory_manager)

        # Create child agents
        self.agents = {
            "tool_builder": tool_builder,
            "air_quality": AirQualityAgent(google_api_key, memory_manager=memory_manager),
            "earthquake": EarthquakeAgent(google_api_key, memory_manager=memory_manager),
            "wildfire": WildfireAgent(firms_api_key, google_api_key, memory_manager=memory_manager),
            "flood": FloodAgent(google_api_key, memory_manager=memory_manager),
            "deforestation": DeforestationAgent(None, google_api_key, memory_manager=memory_manager),
            "ocean": OceanAgent(google_api_key, memory_manager=memory_manager),
            "biodiversity": BiodiversityAgent(google_api_key, memory_manager=memory_manager),
            "climate_anomaly": ClimateAnomalyAgent(google_api_key, memory_manager=memory_manager),
            "carbon_emissions": CarbonEmissionsAgent(google_api_key, memory_manager=memory_manager),
            "satellite_video_fusion": SatelliteVideoFusionAgent(google_api_key=google_api_key, memory_manager=memory_manager),
            "climatex_audit": ClimateXAuditAgent(google_api_key=google_api_key, firms_api_key=firms_api_key, memory_manager=memory_manager),
            "disaster_management": DisasterManagementAgent(google_api_key=google_api_key, firms_api_key=firms_api_key, memory_manager=memory_manager)
        }

        # Inject ToolBuilder into all agents
        for agent in self.agents.values():
            if agent.name != "ToolBuilderAgent":
                agent.set_tool_builder(tool_builder)
        
        if hasattr(self.agents["biodiversity"], "set_satellite_agent"):
            self.agents["biodiversity"].set_satellite_agent(self.agents["satellite_video_fusion"])
        
        # Advanced routing components
        self.meta_learner = None
        self.dynamic_router = None
        self.negotiation_protocol = None
        self.message_bus = None
        
        self._init_advanced_features()
    
    def _init_advanced_features(self):
        """Initialize meta-learning, dynamic routing, and collaboration."""
        # Meta-learning & Dynamic routing
        if self.enable_dynamic_routing or self.enable_meta_learning:
            try:
                from .meta_learning import MetaLearner
                from .dynamic_router import DynamicRouter
                from ..memory.performance_store import PerformanceStore
                
                if self.enable_meta_learning:
                    self.meta_learner = MetaLearner(performance_store=PerformanceStore())
                    self.log("Meta-learner initialized")
                
                if self.enable_dynamic_routing:
                    self.dynamic_router = DynamicRouter(
                        agents=self.agents,
                        meta_learner=self.meta_learner,
                        google_api_key=self.api_key,
                        enable_meta_learning=self.enable_meta_learning,
                        enable_collaboration=self.enable_collaboration
                    )
                    self.log("Dynamic router initialized")
            except Exception as e:
                self.logger.warning(f"Advanced routing init failed: {e}")
                self.enable_dynamic_routing = False
        
        # Collaboration
        if self.enable_collaboration:
            try:
                from .protocols.negotiation import NegotiationProtocol
                from .protocols.message_bus import MessageBus
                
                self.negotiation_protocol = NegotiationProtocol(self.agents)
                self.message_bus = MessageBus()
                
                for agent in self.agents.values():
                    agent.set_negotiation_protocol(self.negotiation_protocol)
                    agent.set_message_bus(self.message_bus)
                
                self.log("Collaboration protocols initialized")
            except Exception as e:
                self.logger.warning(f"Collaboration init failed: {e}")
    
    def set_memory_manager(self, memory_manager: 'MemoryManager'):
        self.memory = memory_manager
        for agent in self.agents.values():
            agent.set_memory_manager(memory_manager)
    
    def set_rag_manager(self, rag_manager: 'RAGManager'):
        self.rag = rag_manager
        for agent in self.agents.values():
            agent.set_rag_manager(rag_manager)
    
    def get_tools(self):
        return []
    
    def get_system_prompt(self) -> str:
        return "You are a climate intelligence orchestrator."
    
    def _keyword_route(self, query: str) -> Optional[str]:
        """Fallback keyword-based routing."""
        query_lower = query.lower()
        for agent_name, kws in self.KEYWORDS.items():
            if any(kw in query_lower for kw in kws):
                return agent_name
        return None
    
    @traceable(name="orchestrator_route", run_type="chain")
    def run(self, query: str) -> str:
        start_time = time.time()
        selected_agent = None
        secondary_agents = []
        
        # Try dynamic routing
        if self.enable_dynamic_routing and self.dynamic_router:
            try:
                decision = self.dynamic_router.route(query)
                selected_agent = decision.primary_agent
                secondary_agents = decision.secondary_agents
                self.log(f"Dynamic route: {selected_agent} (conf={decision.confidence:.2f})")
            except Exception as e:
                self.logger.warning(f"Dynamic routing failed: {e}")
        
        # Fallback to keywords
        if not selected_agent:
            selected_agent = self._keyword_route(query)
            if selected_agent:
                self.log(f"Keyword route: {selected_agent}")
        
        # Final fallback
        if not selected_agent:
            self.log("Fallback to ToolBuilder")
            return self.agents["tool_builder"].build_and_execute(query)
        
        # Execute query
        result = self.agents[selected_agent].run(query)
        latency_ms = (time.time() - start_time) * 1000
        
        # Collaboration
        if secondary_agents and self.enable_collaboration and self.negotiation_protocol:
            result = self._collaborative_run(query, selected_agent, secondary_agents, result)
        
        # Record for meta-learning
        quality = self.agents[selected_agent].last_performance.get("reflexion_score", 0.8)
        self._record_outcome(query, selected_agent, quality, latency_ms)
        
        return result
    
    def _collaborative_run(self, query: str, primary: str, secondary: List[str], primary_result: str) -> str:
        """Execute collaborative query across agents."""
        responses = {primary: primary_result}
        
        for agent_name in secondary[:2]:  # Limit to 2 secondary agents
            if agent_name in self.agents:
                resp = self.negotiation_protocol.request_info(primary, agent_name, query)
                if resp.can_help:
                    responses[agent_name] = resp.content
        
        if len(responses) > 1:
            return self._synthesize(query, responses)
        return primary_result
    
    def _synthesize(self, query: str, responses: Dict[str, str]) -> str:
        """Synthesize multiple responses."""
        if not self.llm:
            return "\n\n".join([f"**{k}:** {v}" for k, v in responses.items()])
        
        prompt = f"Synthesize these expert responses into one:\nQuery: {query}\n" + \
                 "\n".join([f"[{k}]: {v[:800]}" for k, v in responses.items()])
        try:
            return self.llm.invoke([{"role": "user", "content": prompt}]).content
        except:
            return "\n\n".join([f"**{k}:** {v}" for k, v in responses.items()])
    
    def _record_outcome(self, query: str, agent: str, quality: float, latency_ms: float):
        if self.meta_learner:
            try:
                self.meta_learner.record_outcome(query, agent, quality, latency_ms)
            except Exception as e:
                self.logger.debug(f"Record outcome failed: {e}")
    
    def get_routing_insights(self, query: str) -> Dict:
        """Get routing insights for debugging."""
        if self.meta_learner:
            return self.meta_learner.get_routing_insights(query)
        return {}
    
    def get_agent_performance(self) -> Dict:
        """Get agent performance stats."""
        if self.meta_learner:
            return {n: {"queries": s.total_queries, "quality": round(s.avg_quality, 2)} 
                    for n, s in self.meta_learner.get_all_agent_performance().items()}
        return {}
    
    def get_all_alerts(self, **kwargs) -> Dict:
        satellite_alerts = []
        if "latitude" in kwargs and "longitude" in kwargs:
            try:
                satellite_alerts = self.agents["satellite_video_fusion"].get_alerts(
                    kwargs["latitude"], kwargs["longitude"],
                    radius_km=kwargs.get("radius_km", 25.0), days=kwargs.get("days", 7))
            except Exception as e:
                self.logger.warning(f"Satellite alerts failed: {e}")
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "air_quality": self.agents["air_quality"].get_alerts(),
            "earthquake": self.agents["earthquake"].get_alerts(),
            "wildfire": self.agents["wildfire"].get_alerts(),
            "flood": self.agents["flood"].get_alerts(),
            "deforestation": self.agents["deforestation"].get_alerts(),
            "ocean": self.agents["ocean"].get_alerts(),
            "biodiversity": self.agents["biodiversity"].get_alerts(),
            "climate_anomaly": self.agents["climate_anomaly"].get_alerts(),
            "carbon_emissions": self.agents["carbon_emissions"].get_alerts(),
            "satellite_video_fusion": satellite_alerts
        }
    
    def get_alerts(self, **kwargs) -> List[Dict]:
        all_alerts = self.get_all_alerts(**kwargs)
        combined = []
        for alerts in all_alerts.values():
            if isinstance(alerts, list):
                combined.extend(alerts)
        return combined
