"""Evaluation dataset loader."""
import json
from typing import List, Optional
from pathlib import Path
from .types import EvaluationQuery, Difficulty


def load_dataset(file_path: str) -> List[EvaluationQuery]:
    """
    Load evaluation dataset from JSON file.
    
    Expected format:
    [
        {
            "query": str,
            "expected_topics": List[str],
            "ground_truth_answer": str,
            "difficulty": "simple" | "moderate" | "complex",
            "requires_multihop": bool,
            "requires_debate": bool,
            "requires_memory": bool,
            "metadata": {}  # optional
        },
        ...
    ]
    
    Args:
        file_path: Path to JSON dataset file
        
    Returns:
        List of EvaluationQuery objects
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    queries = []
    for item in data:
        try:
            difficulty = Difficulty(item.get("difficulty", "moderate").lower())
            query = EvaluationQuery(
                query=item["query"],
                expected_topics=item.get("expected_topics", []),
                ground_truth_answer=item.get("ground_truth_answer", ""),
                difficulty=difficulty,
                requires_multihop=item.get("requires_multihop", False),
                requires_debate=item.get("requires_debate", False),
                requires_memory=item.get("requires_memory", False),
                metadata=item.get("metadata", {})
            )
            queries.append(query)
        except KeyError as e:
            raise ValueError(f"Missing required field in dataset item: {e}")
        except ValueError as e:
            raise ValueError(f"Invalid difficulty value: {e}")
    
    return queries


def filter_dataset(
    queries: List[EvaluationQuery],
    difficulty: Optional[Difficulty] = None,
    requires_multihop: Optional[bool] = None,
    requires_debate: Optional[bool] = None,
    requires_memory: Optional[bool] = None,
) -> List[EvaluationQuery]:
    """
    Filter evaluation queries by criteria.
    
    Args:
        queries: List of queries to filter
        difficulty: Filter by difficulty level
        requires_multihop: Filter by multihop requirement
        requires_debate: Filter by debate requirement
        requires_memory: Filter by memory requirement
        
    Returns:
        Filtered list of queries
    """
    filtered = queries
    
    if difficulty is not None:
        filtered = [q for q in filtered if q.difficulty == difficulty]
    
    if requires_multihop is not None:
        filtered = [q for q in filtered if q.requires_multihop == requires_multihop]
    
    if requires_debate is not None:
        filtered = [q for q in filtered if q.requires_debate == requires_debate]
    
    if requires_memory is not None:
        filtered = [q for q in filtered if q.requires_memory == requires_memory]
    
    return filtered
