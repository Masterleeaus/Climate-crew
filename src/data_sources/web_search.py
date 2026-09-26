import os
import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

try:
    from tavily import TavilyClient
except ImportError:
    TavilyClient = None


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    score: float = 0.0
    raw_content: Optional[str] = None


class WebSearchClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self._client = None
        
    def _get_client(self):
        if self._client is None:
            if TavilyClient is None:
                raise ImportError("tavily-python not installed. pip install tavily-python")
            self._client = TavilyClient(api_key=self.api_key)
        return self._client
    
    def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced",
        include_raw_content: bool = False
    ) -> List[SearchResult]:
        client = self._get_client()
        response = client.search(
            query=query,
            max_results=max_results,
            search_depth=search_depth,
            include_raw_content=include_raw_content
        )
        
        results = []
        for r in response.get("results", []):
            results.append(SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                snippet=r.get("content", ""),
                score=r.get("score", 0.0),
                raw_content=r.get("raw_content")
            ))
        return results
    
    async def search_async(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "advanced"
    ) -> List[SearchResult]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: self.search(query, max_results, search_depth)
        )
    
    def search_multiple(
        self,
        queries: List[str],
        max_results_per_query: int = 3
    ) -> Dict[str, List[SearchResult]]:
        results = {}
        for q in queries:
            results[q] = self.search(q, max_results=max_results_per_query)
        return results
    
    async def search_multiple_async(
        self,
        queries: List[str],
        max_results_per_query: int = 3
    ) -> Dict[str, List[SearchResult]]:
        tasks = [self.search_async(q, max_results_per_query) for q in queries]
        results_list = await asyncio.gather(*tasks)
        return dict(zip(queries, results_list))
