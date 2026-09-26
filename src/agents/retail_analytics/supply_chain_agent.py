from ..base import BaseAgent
from .models import CausalNode, ActionPlan

class SupplyChainOptimizerAgent(BaseAgent):
    def __init__(self, name="SupplyChainOptimizer", google_api_key=None, memory_manager=None):
        super().__init__(name, google_api_key, memory_manager)

    def get_tools(self):
        return []

    def optimize(self, causal_tree: CausalNode, context: str = "") -> ActionPlan:
        prompt = f"""
        Given this Causal Impact Tree and the specific Scenario Context, generate a HIGHLY DETAILED Supply Chain Action Plan.
        
        CONTEXT: {context}
        
        CRITICAL INSTRUCTIONS:
        1. **BE SPECIFIC**: Do not say "access roads", say "Highway 101" or "Route 199" if relevant to the coordinates. Do not say "products", say "N95 masks" or "HEPA filters" or "Bottled Water".
        2. **DEFINE OWNERSHIP**: Use the 'assigned_to' field to assign real corporate titles (e.g. "Regional Logistics Director", "Store Manager - Crescent City Branch").
        3. **REAL WORLD GROUNDING**: Cite specific standard protocols (e.g. "FEMA Supply Chain Resilience Guidelines") or reference similar historical events if applicable to explain *why* this action is needed.
        
        If the tree shows HIGH RISK: Focus on mitigation, rerouting, and emergency stock.
        If the tree shows LOW RISK: Focus on efficiency, cost reduction, and routine maintenance (e.g. "Update HVAC filters", "Review vendor contracts").
        
        Tree:
        {causal_tree.model_dump_json(indent=2)}
        """
        if self.llm:
            model = self.llm.with_structured_output(ActionPlan)
            return model.invoke(prompt)
        return ActionPlan(items=[])

    def get_system_prompt(self):
        return "You are a Supply Chain expert. specific, actionable logistics plans."
