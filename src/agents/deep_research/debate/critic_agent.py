from ...base import BaseAgent
from langchain_core.messages import SystemMessage, HumanMessage

class CriticAgent(BaseAgent):
    def __init__(self, google_api_key: str = None):
        super().__init__("CriticAgent", google_api_key)

    def get_system_prompt(self) -> str:
        return """You are a Research Critic.
Your goal is to identify weaknesses, gaps, or contradictions in the findings.
Look for:
- Vague statements without numbers.
- Outdated information.
- Biased or unreliable sources.
- Missing perspectives.
"""

    def get_tools(self):
        return []

    def critique(self, context: str) -> str:
        return self.run(f"Critique these findings:\n{context}")
