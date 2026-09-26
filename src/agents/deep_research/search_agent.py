from typing import List, Dict, Any, Optional, Callable
from langchain_core.tools import tool
from ..base import BaseAgent
from ...data_sources.web_search import WebSearchClient

class SearchAgent(BaseAgent):
    def __init__(
        self, 
        google_api_key: str = None, 
        web_search_client: Optional[WebSearchClient] = None,
        domain_agents: Optional[List[BaseAgent]] = None
    ):
        super().__init__("SearchAgent", google_api_key)
        self.web_search = web_search_client or WebSearchClient()
        self.domain_agents = domain_agents or []

    def get_system_prompt(self) -> str:
        return """You are an Advanced Search Agent. 
Your goal is to gather high-quality, factual evidence to answer a specific research question.
You have access to:
1. Web Search: For general information, news, and reports.
2. Domain Tools: Specialized instruments for real-time environmental data (Earthquake, Wildfire, etc.).

When given a query:
- Determine if you need real-time data or general info.
- Use the most appropriate tools.
- If using Web Search, prefer official sources (govt, scientific organizations).
- Summarize your findings concisely but include specific data points (dates, numbers, locations).
- **ALWAYS include the Source URL for every finding.** Format: [Source Name](URL)
"""

    def get_tools(self) -> List[Callable]:
        tools = [self._web_search_tool]
        seen_tool_names = {"web_search"}
        
        # specific tools from domain agents
        for agent in self.domain_agents:
            for tool in agent.get_tools():
                # Check for duplication by name
                if hasattr(tool, "name") and tool.name not in seen_tool_names:
                    tools.append(tool)
                    seen_tool_names.add(tool.name)
                elif not hasattr(tool, "name") and tool not in tools:
                    # Fallback for structured tools without explicit name attr
                    tools.append(tool)
            
        return tools

    @property
    def _web_search_tool(self):
        @tool("web_search")
        def search(query: str) -> str:
            """Search the web for information. Use this for general queries, news, and reports."""
            results = self.web_search.search(query, max_results=3)
            return "\n\n".join([f"Source: {r.title}\nURL: {r.url}\nContent: {r.snippet}" for r in results])
        return search

    def search(self, query: str) -> Dict[str, Any]:
        """Execute search for a query using available tools."""
        response = self.run(f"Find information about: {query}")
        return {
            "query": query,
            "findings": response,
            "raw_results": [] # We could capture raw tool outputs if needed
        }
