from typing import List, Dict, Any
import json
from ..base import BaseAgent
from langchain_core.messages import SystemMessage, HumanMessage

class QueryEnricher(BaseAgent):
    def __init__(self, google_api_key: str = None):
        super().__init__("QueryEnricher", google_api_key)

    def get_system_prompt(self) -> str:
        return """You are an expert research assistant. Your goal is to disambiguate and expand user queries for deep research.
Given a user query, you should:
1. Clarify any ambiguous terms.
2. Break down the query into 3-5 distinct, high-value research perspectives or sub-questions.
3. Identify implicit questions that need to be answered to fully address the user's intent.

Output must be a JSON object with this structure:
{
    "original_query": "...",
    "disambiguated_query": "...",
    "perspectives": ["perspective 1", "perspective 2", ...],
    "sub_questions": ["question 1", "question 2", ...]
}
"""

    def get_tools(self):
        return []

    def enrich(self, query: str) -> Dict[str, Any]:
        prompt = f"Analyze and enrich this query: {query}"
        response = self.llm.invoke([
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=prompt)
        ])
        
        try:
            content = response.content.replace("```json", "").replace("```", "").strip()
            return json.loads(content)
        except json.JSONDecodeError:
            self.logger.error("Failed to parse QueryEnricher output JSON")
            return {
                "original_query": query,
                "disambiguated_query": query,
                "perspectives": ["General analysis"],
                "sub_questions": [query]
            }
