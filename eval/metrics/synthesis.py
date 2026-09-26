"""Synthesis metrics: faithfulness, completeness, LLM-judge quality."""
from typing import Dict, List, Any
import re
from ..types import MetricResult


def _compute_faithfulness(
    answer: str,
    retrieval_results: List[Dict[str, Any]]
) -> float:
    """
    Compute faithfulness: claims in answer are supported by retrieved documents.
    Simple heuristic: check if key claims appear in source documents.
    """
    if not answer or not retrieval_results:
        return 0.0
    
    # Extract claims from answer (simple sentence splitting)
    answer_sentences = re.split(r'[.!?]+', answer)
    answer_sentences = [s.strip() for s in answer_sentences if len(s.strip()) > 10]
    
    if not answer_sentences:
        return 0.5  # Neutral if no clear claims
    
    # Combine all retrieved content
    retrieved_text = " ".join([
        str(r.get("content", "")) for r in retrieval_results
    ]).lower()
    
    # Check how many claims are supported
    supported = 0
    for sentence in answer_sentences:
        # Extract key terms from sentence
        terms = set(sentence.lower().split())
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were"}
        key_terms = {t for t in terms if t not in stopwords and len(t) > 3}
        
        if not key_terms:
            continue
        
        # Check if majority of key terms appear in retrieved text
        found_terms = sum(1 for term in key_terms if term in retrieved_text)
        if found_terms >= len(key_terms) * 0.5:  # At least 50% of terms found
            supported += 1
    
    return supported / len(answer_sentences) if answer_sentences else 0.0


def _compute_completeness(
    answer: str,
    expected_topics: List[str]
) -> float:
    """
    Compute completeness: how many expected topics are covered in the answer.
    """
    if not expected_topics:
        return 1.0  # No topics to cover
    
    answer_lower = answer.lower()
    covered = sum(1 for topic in expected_topics if topic.lower() in answer_lower)
    
    return covered / len(expected_topics)


def _compute_llm_judge_quality(
    answer: str,
    query: str,
    ground_truth: str,
    llm_judge_fn=None
) -> float:
    """
    Compute LLM-judge quality score.
    If llm_judge_fn is provided, use it. Otherwise return a placeholder.
    """
    if llm_judge_fn:
        return llm_judge_fn(answer, query, ground_truth)
    
    # Placeholder: simple heuristic based on length and keyword overlap
    if not answer:
        return 0.0
    
    # Check if answer contains key terms from ground truth
    gt_terms = set(ground_truth.lower().split())
    answer_terms = set(answer.lower().split())
    stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
    gt_terms = {t for t in gt_terms if t not in stopwords and len(t) > 2}
    answer_terms = {t for t in answer_terms if t not in stopwords and len(t) > 2}
    
    if not gt_terms:
        return 0.5
    
    overlap = len(gt_terms & answer_terms) / len(gt_terms)
    
    # Also consider answer length (too short = bad, reasonable length = good)
    length_score = min(1.0, len(answer) / 100.0)  # Normalize to 100 chars
    
    return (overlap * 0.7 + length_score * 0.3)


def compute(run_output: Dict[str, Any], ground_truth: Dict[str, Any], llm_judge_fn=None) -> Dict[str, MetricResult]:
    """
    Compute synthesis metrics.
    
    Args:
        run_output: RunOutput as dict with final_answer and retrieval_results
        ground_truth: Dict with expected_topics and ground_truth_answer
        llm_judge_fn: Optional function to compute LLM judge score
        
    Returns:
        Dict of metric name to MetricResult
    """
    answer = run_output.get("final_answer", "")
    query = run_output.get("query", "")
    retrieval_results = run_output.get("retrieval_results", [])
    expected_topics = ground_truth.get("expected_topics", [])
    ground_truth_answer = ground_truth.get("ground_truth_answer", "")
    
    faithfulness = _compute_faithfulness(answer, retrieval_results)
    completeness = _compute_completeness(answer, expected_topics)
    quality = _compute_llm_judge_quality(answer, query, ground_truth_answer, llm_judge_fn)
    
    return {
        "faithfulness": MetricResult(
            metric_name="faithfulness",
            value=faithfulness,
            components={"faithfulness": faithfulness}
        ),
        "completeness": MetricResult(
            metric_name="completeness",
            value=completeness,
            components={"completeness": completeness}
        ),
        "llm_judge_quality": MetricResult(
            metric_name="llm_judge_quality",
            value=quality,
            components={"quality": quality}
        ),
    }
