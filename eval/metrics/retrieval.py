"""Retrieval metrics: precision@k, recall@k, MRR, NDCG, answerability@k."""
from typing import Dict, List, Any
import math
from ..types import RunOutput, EvaluationQuery, MetricResult


def _compute_precision_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
    """Compute precision@k."""
    if k == 0:
        return 0.0
    retrieved_k = set(retrieved[:k])
    relevant_set = set(relevant)
    if not retrieved_k:
        return 0.0
    return len(retrieved_k & relevant_set) / len(retrieved_k)


def _compute_recall_at_k(retrieved: List[str], relevant: List[str], k: int) -> float:
    """Compute recall@k."""
    if not relevant:
        return 1.0 if not retrieved else 0.0
    retrieved_k = set(retrieved[:k])
    relevant_set = set(relevant)
    return len(retrieved_k & relevant_set) / len(relevant_set)


def _compute_mrr(retrieved: List[str], relevant: List[str]) -> float:
    """Compute Mean Reciprocal Rank."""
    if not relevant:
        return 0.0
    relevant_set = set(relevant)
    for i, doc_id in enumerate(retrieved, 1):
        if doc_id in relevant_set:
            return 1.0 / i
    return 0.0


def _compute_ndcg(retrieved: List[str], relevant: List[str], k: int) -> float:
    """Compute Normalized Discounted Cumulative Gain@k."""
    if k == 0:
        return 0.0
    if not relevant:
        return 0.0
    
    # Binary relevance (1 if relevant, 0 otherwise)
    relevant_set = set(relevant)
    dcg = 0.0
    for i, doc_id in enumerate(retrieved[:k], 1):
        rel = 1.0 if doc_id in relevant_set else 0.0
        dcg += rel / math.log2(i + 1)
    
    # Ideal DCG (all relevant docs at top)
    idcg = 0.0
    num_relevant = min(len(relevant), k)
    for i in range(1, num_relevant + 1):
        idcg += 1.0 / math.log2(i + 1)
    
    if idcg == 0:
        return 0.0
    return dcg / idcg


def _compute_answerability_at_k(
    retrieved: List[Any],
    query: str,
    ground_truth: str,
    k: int
) -> float:
    """
    Compute answerability@k: whether top-k results contain enough info to answer.
    Simple heuristic: check if key terms from ground truth appear in retrieved docs.
    """
    if k == 0 or not retrieved:
        return 0.0
    
    # Extract key terms from ground truth (simple word-based)
    gt_terms = set(ground_truth.lower().split())
    # Remove common stopwords
    stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
    gt_terms = {t for t in gt_terms if t not in stopwords and len(t) > 2}
    
    if not gt_terms:
        return 0.5  # Neutral if no meaningful terms
    
    # Check if retrieved docs contain these terms
    retrieved_text = " ".join([str(r.content) if hasattr(r, 'content') else str(r) 
                               for r in retrieved[:k]]).lower()
    found_terms = sum(1 for term in gt_terms if term in retrieved_text)
    
    return found_terms / len(gt_terms) if gt_terms else 0.0


def compute(run_output: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, MetricResult]:
    """
    Compute retrieval metrics.
    
    Args:
        run_output: RunOutput as dict with retrieval_results
        ground_truth: Dict with 'expected_topics' and 'ground_truth_answer'
        
    Returns:
        Dict of metric name to MetricResult
    """
    retrieval_results = run_output.get("retrieval_results", [])
    expected_topics = ground_truth.get("expected_topics", [])
    ground_truth_answer = ground_truth.get("ground_truth_answer", "")
    
    # Extract document IDs (use content hash if no ID)
    retrieved_doc_ids = []
    for i, result in enumerate(retrieval_results):
        doc_id = result.get("document_id") or result.get("content", "")[:50]
        retrieved_doc_ids.append(doc_id)
    
    # For evaluation, we assume documents matching expected topics are relevant
    # In real scenario, you'd have ground truth relevance labels
    relevant_doc_ids = expected_topics  # Simplified: topics as proxy for relevant docs
    
    # Compute metrics at different k values
    k_values = [1, 3, 5, 10]
    metrics = {}
    
    for k in k_values:
        precision = _compute_precision_at_k(retrieved_doc_ids, relevant_doc_ids, k)
        recall = _compute_recall_at_k(retrieved_doc_ids, relevant_doc_ids, k)
        ndcg = _compute_ndcg(retrieved_doc_ids, relevant_doc_ids, k)
        
        metrics[f"precision@{k}"] = MetricResult(
            metric_name=f"precision@{k}",
            value=precision,
            components={"precision": precision}
        )
        
        metrics[f"recall@{k}"] = MetricResult(
            metric_name=f"recall@{k}",
            value=recall,
            components={"recall": recall}
        )
        
        metrics[f"ndcg@{k}"] = MetricResult(
            metric_name=f"ndcg@{k}",
            value=ndcg,
            components={"ndcg": ndcg}
        )
    
    # MRR
    mrr = _compute_mrr(retrieved_doc_ids, relevant_doc_ids)
    metrics["mrr"] = MetricResult(
        metric_name="mrr",
        value=mrr,
        components={"mrr": mrr}
    )
    
    # Answerability@k
    for k in [1, 3, 5]:
        answerability = _compute_answerability_at_k(
            retrieval_results,
            run_output.get("query", ""),
            ground_truth_answer,
            k
        )
        metrics[f"answerability@{k}"] = MetricResult(
            metric_name=f"answerability@{k}",
            value=answerability,
            components={"answerability": answerability}
        )
    
    return metrics
