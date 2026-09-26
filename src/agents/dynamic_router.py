"""
Dynamic Router - LLM-based intelligent agent selection.
Replaces keyword matching with context-aware routing using meta-learning and LLM reasoning.
"""
import os
import logging
import json
from typing import Dict, List, Optional, Tuple, Any, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum

from langchain_google_genai import ChatGoogleGenerativeAI

if TYPE_CHECKING:
    from .base import BaseAgent
    from .meta_learning import MetaLearner

logger = logging.getLogger(__name__)


class QueryComplexity(Enum):
    """Classification of query complexity."""
    SIMPLE = "simple"          # Single domain, straightforward answer
    MODERATE = "moderate"      # Single domain, requires reasoning
    COMPLEX = "complex"        # Multi-domain, needs collaboration
    UNKNOWN = "unknown"        # Cannot determine


@dataclass
class AgentCapability:
    """Description of an agent's capabilities."""
    name: str
    description: str
    domains: List[str]
    example_queries: List[str]
    can_collaborate_with: List[str] = field(default_factory=list)
    priority: int = 5  # 1-10, higher = more specialized


# Agent capability registry - defines what each agent can do
AGENT_CAPABILITIES: Dict[str, AgentCapability] = {
    "disaster_management": AgentCapability(
        name="disaster_management",
        description="Handles disaster emergencies, evacuations, shelter coordination, humanitarian crises, and risk assessments. Expert in emergency response protocols.",
        domains=["disaster", "emergency", "evacuation", "shelter", "crisis", "rescue", "humanitarian", "risk assessment"],
        example_queries=[
            "How do I evacuate from a flood zone?",
            "What shelters are open near me?",
            "Emergency response plan for earthquake"
        ],
        can_collaborate_with=["earthquake", "wildfire", "flood"],
        priority=10
    ),
    "climatex_audit": AgentCapability(
        name="climatex_audit",
        description="Verifies carbon credits, performs MRV (Monitoring, Reporting, Verification), audits climate data, and handles certification processes.",
        domains=["audit", "verification", "carbon credit", "MRV", "certification", "carbon offset"],
        example_queries=[
            "Verify this carbon credit certificate",
            "Audit the reforestation project data",
            "MRV report for solar project"
        ],
        can_collaborate_with=["carbon_emissions", "deforestation"],
        priority=8
    ),
    "air_quality": AgentCapability(
        name="air_quality",
        description="Monitors air quality indices, PM2.5, PM10, pollution levels, smog conditions, and air pollutant tracking.",
        domains=["air quality", "AQI", "pollution", "PM2.5", "PM10", "smog", "particulate matter", "air pollutants"],
        example_queries=[
            "What's the air quality in Delhi?",
            "PM2.5 levels in Beijing",
            "Is it safe to go outside today?"
        ],
        can_collaborate_with=["climate_anomaly", "wildfire"],
        priority=6
    ),
    "earthquake": AgentCapability(
        name="earthquake",
        description="Tracks seismic activity, earthquake magnitudes, tremors, tectonic events, and earthquake alerts.",
        domains=["earthquake", "seismic", "tremor", "magnitude", "tectonic", "fault line"],
        example_queries=[
            "Recent earthquakes in California",
            "Seismic activity near Tokyo",
            "Was there an earthquake today?"
        ],
        can_collaborate_with=["disaster_management"],
        priority=7
    ),
    "wildfire": AgentCapability(
        name="wildfire",
        description="Monitors active wildfires, fire spread, burn areas, fire risk, and smoke conditions using FIRMS satellite data.",
        domains=["wildfire", "fire", "blaze", "burn", "fire risk", "smoke", "FIRMS"],
        example_queries=[
            "Active fires near Los Angeles",
            "Wildfire status in Amazon",
            "Is there fire risk in my area?"
        ],
        can_collaborate_with=["air_quality", "disaster_management", "satellite_video_fusion"],
        priority=8
    ),
    "flood": AgentCapability(
        name="flood",
        description="Tracks flooding events, precipitation, storm conditions, water levels, and flood warnings.",
        domains=["flood", "flooding", "rain", "precipitation", "storm", "water level", "monsoon"],
        example_queries=[
            "Flood risk in Mumbai during monsoon",
            "Current flooding in Bangladesh",
            "Storm surge predictions"
        ],
        can_collaborate_with=["disaster_management", "climate_anomaly"],
        priority=7
    ),
    "deforestation": AgentCapability(
        name="deforestation",
        description="Monitors forest loss, tree cover change, Amazon deforestation, illegal logging, and forest preservation.",
        domains=["forest", "deforestation", "tree", "logging", "Amazon", "rainforest", "tree cover"],
        example_queries=[
            "Deforestation rate in Amazon",
            "Forest loss in Indonesia",
            "Illegal logging detection"
        ],
        can_collaborate_with=["biodiversity", "carbon_emissions", "satellite_video_fusion"],
        priority=6
    ),
    "ocean": AgentCapability(
        name="ocean",
        description="Monitors ocean conditions, sea surface temperature (SST), coral reefs, marine ecosystems, sea level rise, and wave conditions.",
        domains=["ocean", "sea", "marine", "coral", "reef", "SST", "sea level", "waves", "coastal"],
        example_queries=[
            "Sea surface temperature near Miami",
            "Coral bleaching status in Great Barrier Reef",
            "Wave conditions for surfing"
        ],
        can_collaborate_with=["climate_anomaly", "biodiversity"],
        priority=6
    ),
    "biodiversity": AgentCapability(
        name="biodiversity",
        description="Tracks species, wildlife, endangered animals, habitat conditions, and ecosystem health.",
        domains=["species", "wildlife", "animal", "biodiversity", "endangered", "habitat", "ecosystem", "conservation"],
        example_queries=[
            "Endangered species in this region",
            "Wildlife tracking in Serengeti",
            "Habitat loss for polar bears"
        ],
        can_collaborate_with=["deforestation", "ocean", "satellite_video_fusion"],
        priority=6
    ),
    "climate_anomaly": AgentCapability(
        name="climate_anomaly",
        description="Detects extreme weather events, heatwaves, cold snaps, droughts, and climate anomalies.",
        domains=["heatwave", "heat wave", "anomaly", "extreme weather", "drought", "cold snap", "temperature extreme"],
        example_queries=[
            "Heatwave forecast for Europe",
            "Is this temperature normal for July?",
            "Drought conditions in California"
        ],
        can_collaborate_with=["air_quality", "flood", "wildfire"],
        priority=7
    ),
    "carbon_emissions": AgentCapability(
        name="carbon_emissions",
        description="Tracks CO2 emissions, greenhouse gases, carbon footprint, climate trace data, and emission sources.",
        domains=["carbon", "emission", "CO2", "greenhouse", "GHG", "climate trace", "carbon footprint"],
        example_queries=[
            "CO2 emissions from this factory",
            "Carbon footprint of air travel",
            "Which countries emit the most?"
        ],
        can_collaborate_with=["climatex_audit", "deforestation"],
        priority=6
    ),
    "satellite_video_fusion": AgentCapability(
        name="satellite_video_fusion",
        description="Analyzes satellite imagery, drone footage, CCTV feeds, performs change detection, vegetation analysis, and anomaly detection using computer vision.",
        domains=["satellite", "imagery", "drone", "CCTV", "video", "change detection", "vegetation", "remote sensing"],
        example_queries=[
            "Analyze satellite imagery of this location",
            "Detect changes in land use",
            "Vegetation index analysis"
        ],
        can_collaborate_with=["wildfire", "deforestation", "biodiversity"],
        priority=7
    )
}


@dataclass
class RoutingDecision:
    """Result of a routing decision."""
    primary_agent: str
    confidence: float
    complexity: QueryComplexity
    secondary_agents: List[str] = field(default_factory=list)
    reasoning: str = ""
    source: str = ""  # "meta_learning" | "llm" | "hybrid"


class DynamicRouter:
    """
    Intelligent query router that combines meta-learning and LLM reasoning.
    
    Routing strategy:
    1. Check meta-learner for similar past queries
    2. If high confidence (>0.7), use historical routing
    3. Otherwise, use LLM to analyze query and select agent(s)
    4. For complex queries, identify collaboration opportunities
    """
    
    def __init__(
        self,
        agents: Dict[str, 'BaseAgent'],
        meta_learner: Optional['MetaLearner'] = None,
        google_api_key: Optional[str] = None,
        enable_meta_learning: bool = True,
        enable_collaboration: bool = True
    ):
        self.agents = agents
        self.meta_learner = meta_learner
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.enable_meta_learning = enable_meta_learning and meta_learner is not None
        self.enable_collaboration = enable_collaboration
        
        # Initialize LLM for routing decisions
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",  # Fast model for routing
            google_api_key=self.google_api_key,
            temperature=0.1  # Low temperature for consistent routing
        ) if self.google_api_key else None
        
        # Build capability registry for available agents
        self.capabilities = {
            name: AGENT_CAPABILITIES.get(name)
            for name in agents.keys()
            if name in AGENT_CAPABILITIES
        }
        
        logger.info(f"DynamicRouter initialized with {len(self.capabilities)} agent capabilities")
    
    def route(self, query: str) -> RoutingDecision:
        """
        Route a query to the best agent(s).
        
        Args:
            query: The user query to route
            
        Returns:
            RoutingDecision with primary agent and optional collaborators
        """
        # Step 1: Check meta-learner for historical guidance
        if self.enable_meta_learning and self.meta_learner:
            suggestion = self.meta_learner.suggest_agent(query, list(self.agents.keys()))
            
            if self.meta_learner.should_use_suggestion(suggestion):
                logger.info(f"Meta-learner suggests {suggestion.agent_name} with confidence {suggestion.confidence:.2f}")
                return RoutingDecision(
                    primary_agent=suggestion.agent_name,
                    confidence=suggestion.confidence,
                    complexity=QueryComplexity.SIMPLE,
                    reasoning=suggestion.reasoning,
                    source="meta_learning"
                )
        
        # Step 2: Use LLM for routing
        return self._llm_route(query)
    
    def _llm_route(self, query: str) -> RoutingDecision:
        """Use LLM to analyze query and select appropriate agent(s)."""
        if not self.llm:
            # Fallback to first available agent
            return RoutingDecision(
                primary_agent=list(self.agents.keys())[0] if self.agents else "tool_builder",
                confidence=0.3,
                complexity=QueryComplexity.UNKNOWN,
                reasoning="No LLM available for routing",
                source="fallback"
            )
        
        # Build agent descriptions for LLM
        agent_descriptions = []
        for name, cap in self.capabilities.items():
            if cap:
                agent_descriptions.append(
                    f"- **{name}**: {cap.description}\n  Domains: {', '.join(cap.domains[:5])}"
                )
        
        prompt = f"""You are a query router for a climate intelligence system. Analyze the query and select the most appropriate agent(s).

Available Agents:
{chr(10).join(agent_descriptions)}

Query: "{query}"

Analyze the query and respond with valid JSON:
{{
    "primary_agent": "<agent_name>",
    "confidence": <0.0-1.0>,
    "complexity": "<simple|moderate|complex>",
    "secondary_agents": ["<agent_name>", ...],  // Empty array if not needed
    "reasoning": "<brief explanation>"
}}

Rules:
1. Choose the most specific agent for the query
2. Set complexity to "complex" only if multiple domains are needed
3. Only include secondary_agents for complex queries requiring collaboration
4. If no agent matches well, use "tool_builder"
"""
        
        try:
            response = self.llm.invoke([{"role": "user", "content": prompt}])
            content = response.content
            
            # Parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', str(content), re.DOTALL)
            if json_match:
                result = json.loads(json_match.group(0))
                
                # Validate primary agent exists
                primary = result.get("primary_agent", "tool_builder")
                if primary not in self.agents:
                    primary = "tool_builder"
                
                # Validate secondary agents
                secondary = [a for a in result.get("secondary_agents", []) if a in self.agents]
                
                return RoutingDecision(
                    primary_agent=primary,
                    confidence=min(1.0, max(0.0, result.get("confidence", 0.5))),
                    complexity=QueryComplexity(result.get("complexity", "simple")),
                    secondary_agents=secondary if self.enable_collaboration else [],
                    reasoning=result.get("reasoning", ""),
                    source="llm"
                )
            
        except Exception as e:
            logger.error(f"LLM routing failed: {e}")
        
        # Fallback
        return RoutingDecision(
            primary_agent="tool_builder",
            confidence=0.3,
            complexity=QueryComplexity.UNKNOWN,
            reasoning="Routing analysis failed, using fallback",
            source="fallback"
        )
    
    def analyze_complexity(self, query: str) -> Tuple[QueryComplexity, List[str]]:
        """
        Analyze query complexity and identify relevant domains.
        
        Returns:
            Tuple of (complexity level, list of relevant domains)
        """
        query_lower = query.lower()
        
        # Find matching domains
        matching_agents = []
        for name, cap in self.capabilities.items():
            if cap:
                for domain in cap.domains:
                    if domain.lower() in query_lower:
                        matching_agents.append(name)
                        break
        
        # Determine complexity based on matches
        unique_matches = list(set(matching_agents))
        
        if len(unique_matches) == 0:
            return QueryComplexity.UNKNOWN, []
        elif len(unique_matches) == 1:
            return QueryComplexity.SIMPLE, unique_matches
        elif len(unique_matches) == 2:
            return QueryComplexity.MODERATE, unique_matches
        else:
            return QueryComplexity.COMPLEX, unique_matches
    
    def get_collaboration_chain(self, primary: str, query: str) -> List[str]:
        """
        Determine which agents should collaborate on a query.
        
        Returns ordered list of agents to consult.
        """
        if not self.enable_collaboration:
            return [primary]
        
        chain = [primary]
        cap = self.capabilities.get(primary)
        
        if cap and cap.can_collaborate_with:
            # Check if any collaborators are relevant to the query
            complexity, relevant_agents = self.analyze_complexity(query)
            
            for collaborator in cap.can_collaborate_with:
                if collaborator in relevant_agents and collaborator not in chain:
                    chain.append(collaborator)
        
        return chain[:3]  # Limit to 3 agents max
    
    def record_routing_outcome(
        self,
        query: str,
        agent: str,
        quality: float,
        latency_ms: float
    ):
        """Record routing outcome for meta-learning."""
        if self.enable_meta_learning and self.meta_learner:
            self.meta_learner.record_outcome(
                query=query,
                selected_agent=agent,
                response_quality=quality,
                latency_ms=latency_ms
            )
