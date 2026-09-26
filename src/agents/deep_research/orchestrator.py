from typing import List, Dict, Any, Optional
import json
import asyncio
import time

from ..base import BaseAgent
from .query_enricher import QueryEnricher
from .strategic_planner import StrategicPlanner
from .thought_tree import ThoughtTree
from .search_agent import SearchAgent
from .debate import AdvocateAgent, CriticAgent, JudgeAgent
from .synthesizer import SynthesizerAgent

# Import new advanced features
try:
    from ..meta_learning import MetaLearner
    from ..dynamic_router import DynamicRouter, AGENT_CAPABILITIES
    from ..protocols.negotiation import NegotiationProtocol
    from ..protocols.message_bus import MessageBus, MessageType
    from ...memory.performance_store import PerformanceStore
    ADVANCED_FEATURES_AVAILABLE = True
except ImportError:
    ADVANCED_FEATURES_AVAILABLE = False


class DeepResearchOrchestrator(BaseAgent):
    """
    Orchestrates the entire Deep Research pipeline:
    Query -> Enrich -> Plan -> Explore (MCTS) -> Verify (Debate) -> Synthesize
    
    Enhanced with:
    - Dynamic routing for efficient agent selection
    - Meta-learning for routing optimization
    - Agent collaboration for multi-domain queries
    """
    
    def __init__(
        self,
        google_api_key: str = None,
        web_search_api_key: str = None,
        domain_agents: List[BaseAgent] = None,
        advanced_memory: Optional[Any] = None,  # AdvancedMemoryManager
        enable_dynamic_routing: bool = True,
        enable_meta_learning: bool = True,
        enable_collaboration: bool = True,
        enable_memory: bool = True
    ):
        super().__init__("DeepResearchOrchestrator", google_api_key)
        
        self.enricher = QueryEnricher(google_api_key)
        self.planner = StrategicPlanner(google_api_key)
        
        self.search_agent = SearchAgent(google_api_key, domain_agents=domain_agents)
        self.thought_tree = ThoughtTree(google_api_key, search_agent=self.search_agent)
        
        self.advocate = AdvocateAgent(google_api_key)
        self.critic = CriticAgent(google_api_key)
        self.judge = JudgeAgent(google_api_key)
        
        self.synthesizer = SynthesizerAgent(google_api_key)
        
        # Advanced features
        self.enable_dynamic_routing = enable_dynamic_routing and ADVANCED_FEATURES_AVAILABLE
        self.enable_meta_learning = enable_meta_learning and ADVANCED_FEATURES_AVAILABLE
        self.enable_collaboration = enable_collaboration and ADVANCED_FEATURES_AVAILABLE
        self.enable_memory = enable_memory
        
        # Advanced memory integration
        self.advanced_memory = advanced_memory
        
        self.domain_agents = {agent.name.lower().replace("agent", "").strip(): agent for agent in (domain_agents or [])}
        self.meta_learner = None
        self.dynamic_router = None
        self.negotiation_protocol = None
        self.message_bus = None
        
        self._init_advanced_features()
    
    def _init_advanced_features(self):
        """Initialize meta-learning, dynamic routing, and collaboration."""
        if not ADVANCED_FEATURES_AVAILABLE:
            self.log("Advanced features not available (import failed)")
            return
        
        try:
            # Meta-learning & Dynamic routing
            if self.enable_meta_learning:
                performance_store = PerformanceStore()
                self.meta_learner = MetaLearner(performance_store=performance_store)
                self.log("Meta-learner initialized for deep research")
            
            if self.enable_dynamic_routing and self.domain_agents:
                self.dynamic_router = DynamicRouter(
                    agents=self.domain_agents,
                    meta_learner=self.meta_learner,
                    google_api_key=self.api_key,
                    enable_meta_learning=self.enable_meta_learning,
                    enable_collaboration=self.enable_collaboration
                )
                self.log("Dynamic router initialized for deep research")
            
            # Collaboration
            if self.enable_collaboration and self.domain_agents:
                self.negotiation_protocol = NegotiationProtocol(self.domain_agents)
                self.message_bus = MessageBus()
                
                for agent in self.domain_agents.values():
                    if hasattr(agent, 'set_negotiation_protocol'):
                        agent.set_negotiation_protocol(self.negotiation_protocol)
                    if hasattr(agent, 'set_message_bus'):
                        agent.set_message_bus(self.message_bus)
                
                self.log("Collaboration protocols initialized for deep research")
                
        except Exception as e:
            self.logger.warning(f"Failed to initialize advanced features: {e}")

    def get_tools(self):
        return []

    def get_system_prompt(self):
        return (
            "You are the Deep Research Orchestrator, responsible for managing a multi-stage research pipeline: "
            "Query Enrichment, Strategic Planning, Deep Exploration (MCTS), Adversarial Verification (Debate), "
            "and Final Synthesis. Your goal is to coordinate these specialized components to produce "
            "comprehensive, accurate, and highly-verified research reports."
        )

    def _route_to_domain_agents(self, sub_query: str) -> List[str]:
        """
        Use dynamic routing to select relevant domain agents for a sub-query.
        Returns list of agent names best suited for this query.
        """
        if self.enable_dynamic_routing and self.dynamic_router:
            try:
                decision = self.dynamic_router.route(sub_query)
                agents = [decision.primary_agent]
                if decision.secondary_agents:
                    agents.extend(decision.secondary_agents[:2])
                return agents
            except Exception as e:
                self.logger.warning(f"Dynamic routing failed: {e}")
        
        # Fallback: return all domain agents
        return list(self.domain_agents.keys())

    def _collaborate_on_finding(self, finding: str, relevant_agents: List[str]) -> Dict[str, str]:
        """
        Get collaborative input from multiple agents on a finding.
        Uses negotiation protocol for structured communication.
        """
        responses = {}
        
        if self.enable_collaboration and self.negotiation_protocol:
            for agent_name in relevant_agents[:3]:
                if agent_name in self.domain_agents:
                    try:
                        response = self.negotiation_protocol.request_info(
                            from_agent="deep_research_orchestrator",
                            to_agent=agent_name,
                            query=f"Verify and expand on this finding: {finding[:500]}",
                            context={"source": "deep_research", "type": "verification"}
                        )
                        if response.can_help:
                            responses[agent_name] = response.content
                    except Exception as e:
                        self.logger.debug(f"Collaboration with {agent_name} failed: {e}")
        
        return responses

    def _record_research_outcome(self, query: str, primary_agent: str, quality: float, latency_ms: float):
        """Record research outcome for meta-learning."""
        if self.enable_meta_learning and self.meta_learner:
            try:
                self.meta_learner.record_outcome(
                    query=query,
                    selected_agent=primary_agent,
                    response_quality=quality,
                    latency_ms=latency_ms
                )
            except Exception as e:
                self.logger.debug(f"Failed to record outcome: {e}")

    def _retrieve_memory_context(self, query: str) -> str:
        """
        Retrieve relevant context from advanced memory system.
        Searches across episodic, semantic, and shared memory.
        """
        if not self.enable_memory or not self.advanced_memory:
            return ""
        
        try:
            # Search for relevant memories
            results = self.advanced_memory.search(
                query=query,
                agent_id="deep_research_orchestrator",
                limit=5,
                include_working=True,
                include_episodic=True,
                include_shared=True
            )
            
            if not results:
                return ""
            
            # Format context from memory
            context_parts = []
            for result in results:
                source = result.source.value if hasattr(result.source, 'value') else str(result.source)
                context_parts.append(f"[{source}] {result.content[:300]}")
            
            return "Relevant Context from Memory:\n" + "\n".join(context_parts)
            
        except Exception as e:
            self.logger.debug(f"Memory retrieval failed: {e}")
            return ""

    def _store_findings_to_memory(self, query: str, findings: List[str], report: str):
        """
        Store research findings to memory system.
        - Working memory: Current session context
        - Episodic memory: Research session for future reference
        - Shared memory: Key findings for other agents
        """
        if not self.enable_memory or not self.advanced_memory:
            return
        
        try:
            agent_id = "deep_research_orchestrator"
            
            # Store to working memory (session context)
            if self.advanced_memory.working:
                self.advanced_memory.working.add(
                    content=f"Research query: {query}",
                    agent_id=agent_id,
                    metadata={"type": "research_query"}
                )
            
            # Store key findings to episodic memory
            if self.advanced_memory.episodic and findings:
                for i, finding in enumerate(findings[:3]):  # Top 3 findings
                    self.advanced_memory.episodic.add(
                        content=f"Finding: {str(finding)[:500]}",
                        agent_id=agent_id,
                        metadata={"query": query, "finding_index": i, "type": "research_finding"}
                    )
            
            # Share summary to shared memory for other agents
            if self.advanced_memory.shared and report:
                summary = report[:800] if len(report) > 800 else report
                self.advanced_memory.shared.share(
                    content=f"Deep Research Summary: {summary}",
                    source_agent=agent_id,
                    visibility="global",
                    metadata={"query": query, "type": "research_summary"}
                )
                self.log("Research summary shared to memory pool")
                
        except Exception as e:
            self.logger.debug(f"Memory storage failed: {e}")

    def set_advanced_memory(self, advanced_memory):
        """Set the advanced memory manager."""
        self.advanced_memory = advanced_memory
        self.enable_memory = True


    def run_deep_research(self, user_query: str) -> Dict[str, Any]:
        start_time = time.time()
        self.log(f"Starting Deep Research for: {user_query}")
        
        # Determine relevant agents using dynamic routing
        relevant_agents = self._route_to_domain_agents(user_query)
        self.log(f"Dynamically selected agents: {relevant_agents}")
        
        # 0. Retrieve memory context (NEW)
        memory_context = ""
        if self.enable_memory:
            memory_context = self._retrieve_memory_context(user_query)
            if memory_context:
                self.log("Phase 0: Retrieved relevant memory context")
        
        # 1. Enrich (include memory context)
        self.log("Phase 1: Enrichment")
        enriched_query = user_query
        if memory_context:
            enriched_query = f"{user_query}\n\nContext from previous research:\n{memory_context}"
        enriched = self.enricher.enrich(enriched_query)
        self.log(f"Enriched query: {json.dumps(enriched, indent=2)}")
        
        # 2. Plan
        self.log("Phase 2: Planning")
        plan = self.planner.plan(enriched)
        self.log(f"Research Plan: {len(plan)} directions")
        
        # 3. Explore (MCTS)
        self.log("Phase 3: Exploration (MCTS)")
        self.thought_tree.initialize(plan)
        best_findings = self.thought_tree.run_mcts(iterations=10) 
        self.log(f"Exploration complete. Found {len(best_findings)} potential facts.")
        
        # 3.5 Collaborative Enhancement (NEW)
        if self.enable_collaboration and best_findings:
            self.log("Phase 3.5: Collaborative Enhancement")
            for i, finding in enumerate(best_findings[:5]):
                collab_insights = self._collaborate_on_finding(str(finding), relevant_agents)
                if collab_insights:
                    # Append collaborative insights to finding
                    enhanced = f"{finding}\n\n[Collaborative Insights from {', '.join(collab_insights.keys())}]: "
                    enhanced += " | ".join([f"{k}: {v[:200]}" for k, v in collab_insights.items()])
                    best_findings[i] = enhanced
        
        # 4. Verify (Debate)
        self.log("Phase 4: Verification (Debate)")
        verified_facts = []
        for finding in best_findings:
            finding_content = str(finding)
            # A simple 1-round debate for efficiency
            advocacy = self.advocate.advocate(finding_content)
            critique = self.critic.critique(finding_content)
            verdict_json = self.judge.judge(finding_content, advocacy, critique)
            
            # Simple check for acceptance
            if "ACCEPT" in verdict_json or "accept" in verdict_json.lower():
                verified_facts.append(finding)
            else:
                self.log(f"Rejected finding: {finding_content[:50]}...")
        
        # Fallback if everything rejected (unlikely)
        if not verified_facts:
            self.log("Warning: No facts passed verification. Using best unverified findings.")
            verified_facts = best_findings

        # 5. Synthesize
        self.log("Phase 5: Synthesis")
        final_report = self.synthesizer.synthesize(user_query, verified_facts)
        
        # Extract Sources (Advanced Regex)
        import re
        sources = []
        seen_urls = set()
        
        all_text = " ".join([str(f) for f in verified_facts]) + "\n" + final_report
        
        # 1. Regex for academic citations: [1] Title. URL or [1] Title (URL)
        citation_pattern = r'\[\d+\]\s*([^\[\]\(\)\n]{4,150})\.?\s*(https?://\S+)'
        citations = re.findall(citation_pattern, all_text)
        
        for title, url in citations:
            url = url.rstrip(').,' )
            if url not in seen_urls:
                sources.append({"title": title.strip(), "url": url, "type": "web"})
                seen_urls.add(url)

        # 2. Regex for markdown links [Title](URL) - if citations missed them
        md_links = re.findall(r'\[([^\]]+)\]\((http[^)]+)\)', all_text)
        for title, url in md_links:
            if url not in seen_urls:
                sources.append({"title": title, "url": url, "type": "web"})
                seen_urls.add(url)
                
        # 3. Fallback: Raw URLs
        if len(sources) < 3:
            raw_urls = re.findall(r'(https?://[^\s\)]+)', all_text)
            for url in raw_urls:
                if url not in seen_urls:
                    domain = url.split("//")[-1].split("/")[0]
                    sources.append({"title": domain, "url": url, "type": "web"})
                    seen_urls.add(url)
        
        # Clean up Report
        clean_report = re.split(r'\n#+\s*(References|Sources|Bibliography)', final_report, flags=re.IGNORECASE)[0]
        
        # Store findings to memory (NEW)
        if self.enable_memory:
            self._store_findings_to_memory(user_query, [str(f) for f in verified_facts], clean_report)
            self.log("Phase 6: Findings stored to memory")
        
        # Record outcome for meta-learning
        latency_ms = (time.time() - start_time) * 1000
        primary_agent = relevant_agents[0] if relevant_agents else "unknown"
        self._record_research_outcome(user_query, primary_agent, 0.85, latency_ms)
        
        # Broadcast knowledge via message bus
        if self.enable_collaboration and self.message_bus:
            try:
                self.message_bus.broadcast(
                    content=f"Deep research completed: {user_query[:100]}",
                    source_agent="deep_research_orchestrator",
                    message_type=MessageType.KNOWLEDGE_SHARE,
                    metadata={"type": "research_complete", "sources_count": len(sources)}
                )
            except:
                pass
        
        return {
            "report": clean_report.strip(),
            "sources": sources[:12],
            "agents_used": relevant_agents,
            "collaboration_enabled": self.enable_collaboration,
            "memory_enabled": self.enable_memory,
            "memory_context_used": bool(memory_context)
        }
