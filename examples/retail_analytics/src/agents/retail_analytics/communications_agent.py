from src.agents.base import BaseAgent
from .models import CausalNode, ActionPlan, CommunicationPackage

class CorporateCommsAgent(BaseAgent):
    def __init__(self, name="CorporateComms", google_api_key=None, memory_manager=None):
        super().__init__(name, google_api_key, memory_manager)

    def get_tools(self):
        return []

    def communicate(self, action_plan: ActionPlan, causal_tree: CausalNode) -> CommunicationPackage:
        prompt = f"""
        Generate role-specific alerts based on the Action Plan and Causal Context.
        
        If High Risk: Use "URGENT", "WARNING" tone.
        If Low Risk: Use "STATUS UPDATE", "PREPAREDNESS" tone. Focus on "Business as Usual" confirmation.
        
        Context: Root Event: {causal_tree.description}
        Action Plan: {action_plan.model_dump_json()}
        
        Tasks:
        1. Create alerts for: CEO (Strategic), Store Manager (Tactical), Logistics Head (Operational).
        2. Generate a 'public_advisory' for normal citizens in the region. Include safety tips and what to expect.
        """
        if self.llm:
            model = self.llm.with_structured_output(CommunicationPackage)
            return model.invoke(prompt)
        return CommunicationPackage(alerts=[], public_advisory="LLM Unavailable. Please check dashboards manually.")

    def get_system_prompt(self):
        return "You are a Corporate Communications Director. Clear, urgent, persona-based messaging."
