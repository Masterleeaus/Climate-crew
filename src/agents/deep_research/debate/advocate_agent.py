from ...base import BaseAgent
from langchain_core.messages import SystemMessage, HumanMessage

class AdvocateAgent(BaseAgent):
    def __init__(self, google_api_key: str = None):
        super().__init__("AdvocateAgent", google_api_key)

    def get_system_prompt(self) -> str:
        return """You are a Research Advocate.
Your goal is to argue FOR the validity and importance of the collected findings.
Highlight:
- The credibility of sources.
- The specific data points (dates, numbers).
- How it answers the core research question.
"""

    def get_tools(self):
        return []

    def advocate(self, context: str) -> str:
        return self.run(f"Advocate for these findings:\n{context}")
