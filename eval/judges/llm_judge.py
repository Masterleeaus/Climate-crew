"""LLM judge for pairwise and absolute scoring."""
from typing import Dict, List, Optional, Tuple
import os
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI


class LLMJudge:
    """LLM-based judge for evaluating answers."""
    
    def __init__(
        self,
        model_name: str = "gemini-1.5-pro",
        google_api_key: Optional[str] = None,
        blind_evaluation: bool = True
    ):
        """
        Initialize LLM judge.
        
        Args:
            model_name: Name of the LLM model to use
            google_api_key: Google API key (uses env var if not provided)
            blind_evaluation: If True, hide agent names from judge
        """
        self.model_name = model_name
        self.google_api_key = google_api_key or os.getenv("GOOGLE_API_KEY")
        self.blind_evaluation = blind_evaluation
        
        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY must be set")
        
        self.llm = ChatGoogleGenerativeAI(
            model=model_name,
            google_api_key=self.google_api_key,
            temperature=0.0
        )
    
    def pairwise_comparison(
        self,
        answer1: str,
        answer2: str,
        query: str,
        agent1_name: Optional[str] = None,
        agent2_name: Optional[str] = None
    ) -> Tuple[int, str]:
        """
        Compare two answers and return which is better.
        
        Returns:
            Tuple of (winner: 1 or 2, reasoning: str)
        """
        if self.blind_evaluation:
            agent1_label = "Answer A"
            agent2_label = "Answer B"
        else:
            agent1_label = agent1_name or "Answer A"
            agent2_label = agent2_name or "Answer B"
        
        prompt = f"""You are an expert evaluator comparing two answers to a query.

Query: {query}

{agent1_label}:
{answer1}

{agent2_label}:
{answer2}

Compare these answers based on:
1. Accuracy and correctness
2. Completeness
3. Clarity and coherence
4. Relevance to the query

Which answer is better? Respond with:
- "A" if {agent1_label} is better
- "B" if {agent2_label} is better
- "TIE" if they are equally good

Then provide a brief explanation (1-2 sentences).
"""
        
        response = self.llm.invoke([
            SystemMessage(content="You are an expert evaluator. Be precise and fair."),
            HumanMessage(content=prompt)
        ])
        
        content = response.content.strip().upper()
        
        # Parse response
        if content.startswith("A"):
            return (1, content)
        elif content.startswith("B"):
            return (2, content)
        else:
            # Default to tie
            return (0, content)
    
    def absolute_scoring(
        self,
        answer: str,
        query: str,
        ground_truth: Optional[str] = None,
        agent_name: Optional[str] = None
    ) -> Tuple[float, str]:
        """
        Score an answer on a 0-1 scale.
        
        Returns:
            Tuple of (score: float, reasoning: str)
        """
        if self.blind_evaluation:
            agent_label = "Answer"
        else:
            agent_label = agent_name or "Answer"
        
        ground_truth_section = ""
        if ground_truth:
            ground_truth_section = f"\n\nGround truth reference:\n{ground_truth}"
        
        prompt = f"""You are an expert evaluator scoring an answer to a query.

Query: {query}
{ground_truth_section}

{agent_label}:
{answer}

Score this answer on a scale of 0.0 to 1.0 based on:
1. Accuracy and correctness (0-0.4)
2. Completeness (0-0.3)
3. Clarity and coherence (0-0.2)
4. Relevance to the query (0-0.1)

Respond with:
- A single float number between 0.0 and 1.0
- Then a brief explanation (1-2 sentences)
"""
        
        response = self.llm.invoke([
            SystemMessage(content="You are an expert evaluator. Be precise and fair."),
            HumanMessage(content=prompt)
        ])
        
        content = response.content.strip()
        
        # Extract score (first float in response)
        import re
        score_match = re.search(r'\b0?\.\d+|\b1\.0|\b0\.0', content)
        if score_match:
            score = float(score_match.group())
            score = max(0.0, min(1.0, score))  # Clamp to [0, 1]
        else:
            score = 0.5  # Default if parsing fails
        
        return (score, content)


def pairwise_comparison(
    answer1: str,
    answer2: str,
    query: str,
    model_name: str = "gemini-1.5-pro",
    **kwargs
) -> Tuple[int, str]:
    """Convenience function for pairwise comparison."""
    judge = LLMJudge(model_name=model_name, **kwargs)
    return judge.pairwise_comparison(answer1, answer2, query)


def absolute_scoring(
    answer: str,
    query: str,
    ground_truth: Optional[str] = None,
    model_name: str = "gemini-1.5-pro",
    **kwargs
) -> Tuple[float, str]:
    """Convenience function for absolute scoring."""
    judge = LLMJudge(model_name=model_name, **kwargs)
    return judge.absolute_scoring(answer, query, ground_truth)
