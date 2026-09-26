from typing import List, Dict, Any, Optional
import math
import json
from dataclasses import dataclass, field
from langchain_core.messages import SystemMessage, HumanMessage
from ..base import BaseAgent
from .search_agent import SearchAgent

@dataclass
class Node:
    state: str  # The "thought" or current finding
    parent: Optional['Node'] = None
    children: List['Node'] = field(default_factory=list)
    visits: int = 0
    value: float = 0.0
    depth: int = 0
    research_data: List[Dict] = field(default_factory=list)

class ThoughtTree(BaseAgent):
    def __init__(
        self, 
        google_api_key: str = None,
        search_agent: Optional[SearchAgent] = None,
        max_depth: int = 3,
        c_param: float = 1.414  # Exploration constant
    ):
        super().__init__("ThoughtTree", google_api_key)
        self.search_agent = search_agent
        self.max_depth = max_depth
        self.c_param = c_param
        self.root = None

    def get_system_prompt(self) -> str:
        return """You are a Research Evaluator.
Your goal is to score the "promise" of a research direction on a scale of 0.0 to 1.0.
A high score (near 1.0) means:
- The finding is highly relevant to the main topic.
- It provides specific, factual data.
- It opens up clear follow-up questions.

A low score (near 0.0) means:
- The finding is irrelevant, vague, or repetitive.
- It leads to a dead end.

Output ONLY a single float number between 0.0 and 1.0.
"""

    def get_tools(self):
        return []

    def initialize(self, initial_plan: List[Dict]):
        """Initialize the tree with user questions as children of root."""
        self.root = Node(state="Root: Start of Research")
        for item in initial_plan[:3]: # Limit width for efficiency
            query = item.get("initial_search_queries", [item["topic"]])[0]
            child = Node(
                state=f"Plan: {item['description']}", 
                parent=self.root,
                depth=1,
                research_data=[{"type": "plan", "content": item}]
            )
            self.root.children.append(child)

    def select(self, node: Node) -> Node:
        """Select a node to expand using UCB1."""
        while node.children:
            if not all(n.visits > 0 for n in node.children):
                return next(n for n in node.children if n.visits == 0)
            
            # UCB1
            node = max(
                node.children, 
                key=lambda n: (n.value / n.visits) + self.c_param * math.sqrt(math.log(node.visits) / n.visits)
            )
        return node

    def expand(self, node: Node) -> Node:
        """Expand a node by performing a search step."""
        if node.depth >= self.max_depth:
            return node

        # Extract a query from the current state
        query_prompt = f"Based on this finding: '{node.state}', what is the most important follow-up search query? Output ONLY the query."
        query_resp = self.llm.invoke([
             SystemMessage(content="You are a query generator. Output only the query string."),
             HumanMessage(content=query_prompt)
        ])
        query = query_resp.content.strip()

        # Perform search
        if self.search_agent:
            result = self.search_agent.search(query)
            finding_text = result.get("findings", "")[:500]  # Truncate for state
            
            new_node = Node(
                state=f"Finding: {finding_text}...",
                parent=node,
                depth=node.depth + 1,
                research_data=node.research_data + [result]
            )
            node.children.append(new_node)
            return new_node
        
        return node

    def simulate(self, node: Node) -> float:
        """Evaluate the node's value using the LLM."""
        prompt = f"Evaluate this research finding:\n{node.state}\n\nScore (0.0-1.0):"
        response = self.llm.invoke([
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=prompt)
        ])
        try:
            val = float(response.content.strip())
            return max(0.0, min(1.0, val))
        except:
            return 0.5

    def backpropagate(self, node: Node, value: float):
        """Update value and visit count up the tree."""
        while node:
            node.visits += 1
            node.value += value
            node = node.parent

    def run_mcts(self, iterations: int = 5) -> List[Dict]:
        """Run MCTS for a fixed number of iterations and return best collected data."""
        for _ in range(iterations):
            leaf = self.select(self.root)
            child = self.expand(leaf)
            value = self.simulate(child)
            self.backpropagate(child, value)

        # Collect best paths
        best_data = []
        if self.root:
            queue = [self.root]
            while queue:
                n = queue.pop(0)
                if n.visits > 0 and (n.value / n.visits) > 0.6: # High quality logic
                     best_data.extend(n.research_data)
                queue.extend(n.children)
        
        # Deduplicate by ensuring we have unique content
        unique_findings = []
        seen = set()
        for item in best_data:
            s_content = str(item)
            if s_content not in seen:
                seen.add(s_content)
                unique_findings.append(item)
                
        return unique_findings
