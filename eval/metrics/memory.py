"""Memory metrics: precision, context relevance, staleness, interference."""
from typing import Dict, List, Any
from datetime import datetime, timedelta
from ..types import MetricResult


def _compute_memory_precision(
    memory_operations: List[Dict[str, Any]],
    query: str
) -> float:
    """
    Compute memory precision: how many retrieved memories are relevant to query.
    """
    if not memory_operations:
        return 1.0  # No memory operations = perfect precision (nothing irrelevant)
    
    retrieve_ops = [op for op in memory_operations if op.get("operation_type") == "retrieve"]
    
    if not retrieve_ops:
        return 1.0
    
    query_terms = set(query.lower().split())
    stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
    query_terms = {t for t in query_terms if t not in stopwords and len(t) > 2}
    
    if not query_terms:
        return 0.5
    
    relevant_count = 0
    for op in retrieve_ops:
        value = str(op.get("value", "")).lower()
        value_terms = set(value.split())
        value_terms = {t for t in value_terms if t not in stopwords and len(t) > 2}
        
        # Check overlap
        overlap = len(query_terms & value_terms)
        if overlap >= len(query_terms) * 0.3:  # At least 30% overlap
            relevant_count += 1
    
    return relevant_count / len(retrieve_ops) if retrieve_ops else 0.0


def _compute_context_relevance(
    memory_operations: List[Dict[str, Any]],
    retrieval_results: List[Dict[str, Any]]
) -> float:
    """
    Compute context relevance: how well memories align with retrieved documents.
    """
    if not memory_operations or not retrieval_results:
        return 0.5  # Neutral if no data
    
    retrieve_ops = [op for op in memory_operations if op.get("operation_type") == "retrieve"]
    
    if not retrieve_ops:
        return 0.5
    
    # Extract terms from retrieved documents
    retrieved_text = " ".join([str(r.get("content", "")) for r in retrieval_results]).lower()
    retrieved_terms = set(retrieved_text.split())
    stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
    retrieved_terms = {t for t in retrieved_terms if t not in stopwords and len(t) > 2}
    
    if not retrieved_terms:
        return 0.5
    
    # Check memory alignment
    aligned = 0
    for op in retrieve_ops:
        value = str(op.get("value", "")).lower()
        value_terms = set(value.split())
        value_terms = {t for t in value_terms if t not in stopwords and len(t) > 2}
        
        overlap = len(retrieved_terms & value_terms)
        if overlap >= len(value_terms) * 0.3:
            aligned += 1
    
    return aligned / len(retrieve_ops) if retrieve_ops else 0.0


def _compute_staleness_penalty(
    memory_operations: List[Dict[str, Any]]
) -> float:
    """
    Compute staleness penalty: how old are the retrieved memories.
    Lower is better (more recent = less stale).
    """
    if not memory_operations:
        return 0.0  # No staleness if no memory
    
    retrieve_ops = [op for op in memory_operations if op.get("operation_type") == "retrieve"]
    
    if not retrieve_ops:
        return 0.0
    
    now = datetime.now()
    total_age_days = 0.0
    
    for op in retrieve_ops:
        timestamp = op.get("timestamp")
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp)
            except:
                timestamp = now
        elif not isinstance(timestamp, datetime):
            timestamp = now
        
        age = (now - timestamp).total_seconds() / (24 * 3600)  # Days
        total_age_days += age
    
    avg_age_days = total_age_days / len(retrieve_ops)
    
    # Normalize: 0 days = 0 penalty, 30+ days = 1.0 penalty
    penalty = min(1.0, avg_age_days / 30.0)
    
    return penalty


def _compute_interference_rate(
    memory_operations: List[Dict[str, Any]]
) -> float:
    """
    Compute interference rate: how often memory operations conflict.
    Simple heuristic: check for contradictory store/update operations.
    """
    if len(memory_operations) < 2:
        return 0.0
    
    # Group operations by key
    ops_by_key = {}
    for op in memory_operations:
        key = op.get("key", "")
        if key:
            if key not in ops_by_key:
                ops_by_key[key] = []
            ops_by_key[key].append(op)
    
    conflicts = 0
    total_keys = len(ops_by_key)
    
    if total_keys == 0:
        return 0.0
    
    # Check for rapid updates to same key (potential interference)
    for key, ops in ops_by_key.items():
        if len(ops) > 1:
            # Sort by timestamp
            sorted_ops = sorted(ops, key=lambda x: x.get("timestamp", datetime.now()))
            for i in range(1, len(sorted_ops)):
                prev_op = sorted_ops[i-1]
                curr_op = sorted_ops[i]
                
                # Check if operations are close in time and different
                prev_ts = prev_op.get("timestamp", datetime.now())
                curr_ts = curr_op.get("timestamp", datetime.now())
                
                if isinstance(prev_ts, str):
                    try:
                        prev_ts = datetime.fromisoformat(prev_ts)
                    except:
                        prev_ts = datetime.now()
                if isinstance(curr_ts, str):
                    try:
                        curr_ts = datetime.fromisoformat(curr_ts)
                    except:
                        curr_ts = datetime.now()
                
                time_diff = (curr_ts - prev_ts).total_seconds()
                
                # If operations within 1 second and different values, potential conflict
                if time_diff < 1.0:
                    prev_val = str(prev_op.get("value", ""))
                    curr_val = str(curr_op.get("value", ""))
                    if prev_val != curr_val:
                        conflicts += 1
    
    return conflicts / total_keys if total_keys > 0 else 0.0


def compute(run_output: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, MetricResult]:
    """
    Compute memory metrics.
    
    Args:
        run_output: RunOutput as dict with memory_operations and retrieval_results
        ground_truth: Dict (not used for memory metrics, but kept for consistency)
        
    Returns:
        Dict of metric name to MetricResult
    """
    memory_operations = run_output.get("memory_operations", [])
    query = run_output.get("query", "")
    retrieval_results = run_output.get("retrieval_results", [])
    
    precision = _compute_memory_precision(memory_operations, query)
    context_relevance = _compute_context_relevance(memory_operations, retrieval_results)
    staleness = _compute_staleness_penalty(memory_operations)
    interference = _compute_interference_rate(memory_operations)
    
    return {
        "memory_precision": MetricResult(
            metric_name="memory_precision",
            value=precision,
            components={"precision": precision}
        ),
        "context_relevance": MetricResult(
            metric_name="context_relevance",
            value=context_relevance,
            components={"relevance": context_relevance}
        ),
        "staleness_penalty": MetricResult(
            metric_name="staleness_penalty",
            value=staleness,
            components={"staleness": staleness}
        ),
        "interference_rate": MetricResult(
            metric_name="interference_rate",
            value=interference,
            components={"interference": interference}
        ),
    }
