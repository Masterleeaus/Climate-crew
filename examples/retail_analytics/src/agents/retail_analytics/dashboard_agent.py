from typing import Any, Dict
from src.agents.base import BaseAgent
from .models import DashboardPayload, CausalNode, ActionPlan, KPIGauge
from langchain_core.tools import tool

class DashboardAgent(BaseAgent):
    def __init__(self, google_api_key=None, memory_manager=None):
        super().__init__("DashboardAgent", google_api_key, memory_manager)

    def get_tools(self):
        return []

    def generate_dashboard(self, causal_tree: CausalNode, action_plan: ActionPlan, context: str) -> DashboardPayload:
        prompt = f"""
        You are the UI Controller for a sophisticated Retail Command Center.
        Generate the data payload to render the "Situational Awareness Dashboard".
        
        INPUT CONTEXT:
        {context}
        
        INPUT ANALYSIS:
        Root Event: {causal_tree.description}
        Impact Score: {causal_tree.impact_score}
        Action Plan Items: {len(action_plan.items)}
        
        TASKS:
        1. Extract coordinates from context for the map center.
        2. Identify specific map markers (e.g. "Store 101", "Highway Closure") based on the Action Plan.
        3. Create 3-5 punchy "Breaking News" style ticker headlines.
        4. Calculate KPIs:
           - Risk Score (0-100) based on impact.
           - Estimated Financial Impact (make a realistic estimate based on the scenario).
           - Supply Chain Delay (hours).
           
        JSON OUTPUT REQUIRED.
        """
        
        # extracted from the causal tree root which now has ML data
        ml_impact = causal_tree.impact_score
        ml_prob = causal_tree.probability
        
        # Calculate Risk Score (0-100) based on ML
        risk_score = int(ml_impact * 10)
        
        # Create ML-driven KPIs
        kpis = [
            KPIGauge(
                label="Predicted Impact", 
                value=ml_impact, 
                unit="/ 10", 
                threshold="Critical" if ml_impact > 7 else "Warning" if ml_impact > 4 else "Normal"
            ),
            KPIGauge(
                label="Disruption Probability", 
                value=round(ml_prob * 100, 1), 
                unit="%", 
                threshold="Critical" if ml_prob > 0.7 else "Warning" if ml_prob > 0.4 else "Normal"
            )
        ]

        if self.llm:
            # We pass the pre-calculated KPIs to the LLM to respect, or just override them after
            model = self.llm.with_structured_output(DashboardPayload)
            payload = model.invoke(prompt)
            # Force override KPIs with our hard ML data to prevent hallucination
            payload.kpis = kpis + payload.kpis[:2] # Keep 2 LLM generated ones, prepend ours
            payload.risk_score = risk_score
            return payload
            
        # Fallback dummy data if LLM fails
        return DashboardPayload(
            map_center_lat=0, map_center_lon=0, map_zoom=10,
            active_layers=[], markers=[], kpis=kpis, news_ticker=[], risk_score=risk_score
        )

    def get_system_prompt(self):
        return "You are the specialized UI Data Generator for the Retail Command Center."
