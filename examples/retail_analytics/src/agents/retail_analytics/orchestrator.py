from typing import Dict, Any
from .causal_agent import CausalAnalystAgent
from .supply_chain_agent import SupplyChainOptimizerAgent
from .communications_agent import CorporateCommsAgent
from .dashboard_agent import DashboardAgent
from .causal_learning import CausalLearner

class RetailSwarm:
    def __init__(self, google_api_key, memory_manager, domain_agents):
        # Initialize ML Learner
        self.learner = CausalLearner()
        self.learner.load_models()  # Try to load existing models
        
        self.causal_agent = CausalAnalystAgent(
            google_api_key=google_api_key, 
            memory_manager=memory_manager, 
            domain_agents=domain_agents,
            learner=self.learner  # Dependency Injection
        )
        self.supply_agent = SupplyChainOptimizerAgent(google_api_key=google_api_key, memory_manager=memory_manager)
        self.comms_agent = CorporateCommsAgent(google_api_key=google_api_key, memory_manager=memory_manager)
        self.dashboard_agent = DashboardAgent(google_api_key=google_api_key, memory_manager=memory_manager)

    def train_models(self) -> Dict[str, Any]:
        """Trigger a retraining of the Causal ML models."""
        print("  > Starting Causal ML Model Training...")
        result = self.learner.train()
        print(f"  > Training Result: {result}")
        
        # Reload models in agent if successful
        if result.get("status") == "success":
            self.causal_agent.learner.load_models()
            
        return result

    def audit(self, scenario_description: str) -> Dict[str, Any]:
        print("  > 1. Running Causal Analysis (Recursive Tree)...")
        causal_tree = self.causal_agent.analyze(scenario_description)
        
        print("  > 2. Optimizing Supply Chain...")
        action_plan = self.supply_agent.optimize(causal_tree, scenario_description)
        
        print("  > 3. Generating Communications...")
        comms = self.comms_agent.communicate(action_plan, causal_tree)
        
        print("  > 4. Synthesizing Dashboard Data...")
        # Passing scenario_description as context for location info
        dashboard_data = self.dashboard_agent.generate_dashboard(causal_tree, action_plan, scenario_description)
        
        return {
            "causal_graph": causal_tree.model_dump(),
            "action_plan": action_plan.model_dump(),
            "communications": comms.model_dump(),
            "dashboard_payload": dashboard_data.model_dump()
        }

    def audit_location(self, latitude: float, longitude: float) -> Dict[str, Any]:
        print(f"  > Gathering Real-Time Intelligence for ({latitude}, {longitude})...")
        
        scenario_data = []
        scenario_data.append(f"Location Coordinates: {latitude}, {longitude}")
        
        if self.causal_agent.domain_agents:
            for name, agent in self.causal_agent.domain_agents.items():
                print(f"    - Querying {name}...")
                try:
                    # Construct a query specifically for coordinates
                    query = f"Assess conditions at latitude {latitude}, longitude {longitude}. Provide current status and risks."
                    report = agent.run(query)
                    scenario_data.append(f"[{name} Report]: {report}")
                except Exception as e:
                    scenario_data.append(f"[{name} Error]: {str(e)}")
        
        full_scenario_description = "\n\n".join(scenario_data)
        print(f"  > Generated Scenario Context ({len(full_scenario_description)} chars)")
        
        return self.audit(full_scenario_description)
