from ...base import BaseAgent
from langchain_core.messages import SystemMessage, HumanMessage

class JudgeAgent(BaseAgent):
    def __init__(self, google_api_key: str = None):
        super().__init__("JudgeAgent", google_api_key)

    def get_system_prompt(self) -> str:
        return """You are a Research Judge.
Your goal is to evaluate the debate between the Advocate and Critic and decide on the final set of facts.
Output a JSON object:
{
    "verdict": "ACCEPT" or "REJECT" or "NEEDS_MORE_INFO",
    "final_findings": "Summary of accepted facts...",
    "reasoning": "Why you made this decision..."
}
"""

    def get_tools(self):
        return []

    def judge(self, findings: str, advocacy: str, critique: str) -> str:
        prompt = f"""EVALUATE DEBATE:
        
FINDINGS:
{findings}

ADVOCATE ARGUMENT:
{advocacy}

CRITIC ARGUMENT:
{critique}
"""
        return self.run(prompt)
