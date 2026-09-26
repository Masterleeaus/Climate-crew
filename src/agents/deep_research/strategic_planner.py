from typing import List, Dict, Any
import json
from ..base import BaseAgent
from langchain_core.messages import SystemMessage, HumanMessage

class StrategicPlanner(BaseAgent):
    def __init__(self, google_api_key: str = None):
        super().__init__("StrategicPlanner", google_api_key)

    def get_system_prompt(self) -> str:
        return """You are a Strategic Research Planner. 
Your goal is to create a structured research plan based on an enriched query.
You must define the root nodes for a research tree. Each node represents a major direction of investigation.

Output must be a JSON object with this structure:
{
    "research_directions": [
        {
            "topic": "Brief topic name",
            "description": "Detailed description of what to investigate",
            "initial_search_queries": ["query 1", "query 2"]
        },
        ...
    ]
}
"""

    def get_tools(self):
        return []

    def plan(self, enriched_query: Dict[str, Any]) -> List[Dict[str, Any]]:
        prompt = f"""Create a research plan for:
Query: {enriched_query.get('disambiguated_query')}
Perspectives: {json.dumps(enriched_query.get('perspectives'))}
Sub-questions: {json.dumps(enriched_query.get('sub_questions'))}
"""
        response = self.llm.invoke([
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=prompt)
        ])
        
        try:
            content = response.content.replace("```json", "").replace("```", "").strip()
            data = json.loads(content)
            return data.get("research_directions", [])
        except json.JSONDecodeError:
            self.logger.error("Failed to parse StrategicPlanner output JSON")
            return [{
                "topic": "Main Investigation",
                "description": f"Investigate {enriched_query.get('original_query')}",
                "initial_search_queries": [enriched_query.get('original_query')]
            }]
