from typing import List, Dict, Any
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from ..base import BaseAgent
from .models import CausalNode

class CausalAnalystAgent(BaseAgent):
    def __init__(self, name="CausalAnalyst", google_api_key=None, memory_manager=None, domain_agents=None, learner=None):
        super().__init__(name, google_api_key, memory_manager)
        self.domain_agents = domain_agents or {}
        self.learner = learner
        
    def get_tools(self):
        tools = []
        for name, agent in self.domain_agents.items():
            @tool(f"consult_{name.lower().replace(' ', '_')}")
            def consult_domain(query: str, agent_ref=agent) -> str:
                """Consults the specific domain agent for expert analysis."""
                return agent_ref.run(query)
            tools.append(consult_domain)
        return tools

    def analyze(self, scenario: str) -> CausalNode:
        # 1. Extract features using LLM (parsing the scenario text to numbers)
        # We need structured weather data to feed into the ML model
        feature_prompt = f"""
        Extract weather metrics from this scenario for ML analysis.
        Scenario: {scenario}
        
        Return exactly this JSON format:
        {{
            "max_temp": <float or 25.0>,
            "min_temp": <float or 15.0>,
            "total_rain": <float or 0.0>,
            "max_wind": <float or 10.0>,
            "avg_humidity": <float or 50.0>
        }}
        """
        
        # Default features if extraction fails
        features = {"max_temp": 25.0, "max_wind": 10.0, "total_rain": 0.0}
        
        if self.llm:
            try:
                # Simple extraction, in prod use structured output model
                response = self.llm.invoke(feature_prompt).content
                import json, re
                match = re.search(r'\{.*\}', response, re.DOTALL)
                if match:
                    features = json.loads(match.group())
            except Exception as e:
                print(f"Feature extraction failed: {e}")
        
        # Fallback: Regex-based extraction if LLM failed or not available
        if features.get("max_wind", 10.0) == 10.0 and features.get("total_rain", 0.0) == 0.0:
            import re
            # Try to find wind speed
            wind_match = re.search(r'(\d+)\s*(?:km/h|mph|knots)', scenario, re.IGNORECASE)
            if wind_match:
                features["max_wind"] = float(wind_match.group(1))
            
            # Try to find rain
            rain_match = re.search(r'(\d+)\s*(?:mm|cm|in)', scenario, re.IGNORECASE)
            if rain_match:
                features["total_rain"] = float(rain_match.group(1))
                
            # Try to find temperature
            temp_match = re.search(r'(\d+)\s*(?:C|F|degrees)', scenario, re.IGNORECASE)
            if temp_match:
                features["max_temp"] = float(temp_match.group(1))
        
        print(f"  > [Causal AI] Extracted Features: {features}")

        # 2. Get ML Prediction
        impact, prob = 0.0, 0.0
        ml_evidence = "ML Model not available"
        
        if self.learner:
            impact, prob = self.learner.predict(features)
            ml_evidence = f"ML Random Forest Prediction (Impact: {impact:.1f}, Prob: {prob:.1%})"
            
        print(f"  > [Causal AI] ML Prediction: Impact {impact}, Prob {prob}")

        # 3. Generate Causal Tree with LLM, injected with ML insights
        prompt = f"""
        Analyze this climate scenario recursively. Build a causal tree.
        Scenario: {scenario}
        
        QUANTITATIVE INSIGHTS (Use these as ground truth):
        - Predicted Impact Score: {impact:.1f} / 10.0
        - Probability of Disruption: {prob:.1%}
        
        Instructions:
        1. Set the root node's `impact_score` to exactly {impact:.1f}.
        2. Set the root node's `probability` to exactly {prob:.2f}.
        3. Set `evidence` to "{ml_evidence}".
        4. If Impact > 7.0, expand on "Supply Chain Disruption" and "Store Closure".
        5. If Impact < 4.0, focus on "Minor Delays" and "Monitoring".
        6. Build the tree at least 3 levels deep.
        """
        
        if self.llm:
            model = self.llm.with_structured_output(CausalNode)
            self.bind_tools(self.get_tools())
            return model.invoke(prompt)
            
        return CausalNode(
            description="LLM not initialized", 
            category="Root", 
            impact_score=impact,  # Even without LLM, we return ML score
            probability=prob,
            evidence=ml_evidence
        )
        
    def get_system_prompt(self):
        return "You are a Causal Analyst. Map the butterfly effect of climate events on retail."
