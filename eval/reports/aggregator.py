"""Aggregate metrics across multiple evaluation runs."""
from typing import List, Dict, Any
import statistics
from collections import defaultdict
from ..types import EvaluationResult, AggregateMetrics, EvaluationReport, Difficulty


def aggregate_metrics(results: List[EvaluationResult]) -> List[AggregateMetrics]:
    """
    Aggregate metrics across multiple evaluation results.
    
    Args:
        results: List of EvaluationResult objects
        
    Returns:
        List of AggregateMetrics
    """
    # Group metrics by name
    metrics_by_name = defaultdict(list)
    metrics_by_difficulty = defaultdict(lambda: defaultdict(list))
    
    for result in results:
        difficulty = result.query.difficulty.value
        for metric in result.metrics:
            metrics_by_name[metric.metric_name].append(metric.value)
            metrics_by_difficulty[metric.metric_name][difficulty].append(metric.value)
    
    # Compute aggregates
    aggregates = []
    for metric_name, values in metrics_by_name.items():
        if not values:
            continue
        
        per_difficulty = {}
        for diff, diff_values in metrics_by_difficulty[metric_name].items():
            if diff_values:
                per_difficulty[diff] = statistics.mean(diff_values)
        
        aggregates.append(AggregateMetrics(
            metric_name=metric_name,
            mean=statistics.mean(values),
            std=statistics.stdev(values) if len(values) > 1 else 0.0,
            min=min(values),
            max=max(values),
            median=statistics.median(values),
            count=len(values),
            per_difficulty=per_difficulty
        ))
    
    return aggregates


def compute_deltas(
    baseline_results: List[EvaluationResult],
    ablation_results: List[EvaluationResult]
) -> Dict[str, float]:
    """
    Compute delta (difference) between baseline and ablation results.
    
    Args:
        baseline_results: Baseline evaluation results
        ablation_results: Ablation evaluation results
        
    Returns:
        Dict mapping metric_name to delta (ablation - baseline)
    """
    # Aggregate baseline metrics
    baseline_metrics = {}
    for result in baseline_results:
        for metric in result.metrics:
            if metric.metric_name not in baseline_metrics:
                baseline_metrics[metric.metric_name] = []
            baseline_metrics[metric.metric_name].append(metric.value)
    
    # Aggregate ablation metrics
    ablation_metrics = {}
    for result in ablation_results:
        for metric in result.metrics:
            if metric.metric_name not in ablation_metrics:
                ablation_metrics[metric.metric_name] = []
            ablation_metrics[metric.metric_name].append(metric.value)
    
    # Compute deltas
    deltas = {}
    for metric_name in set(baseline_metrics.keys()) | set(ablation_metrics.keys()):
        baseline_mean = statistics.mean(baseline_metrics.get(metric_name, [0.0]))
        ablation_mean = statistics.mean(ablation_metrics.get(metric_name, [0.0]))
        deltas[metric_name] = ablation_mean - baseline_mean
    
    return deltas


def create_report(
    results: List[EvaluationResult],
    config_name: str
) -> EvaluationReport:
    """
    Create evaluation report from results.
    
    Args:
        results: List of EvaluationResult objects
        config_name: Configuration name
        
    Returns:
        EvaluationReport
    """
    successful = [r for r in results if not r.run_output.errors]
    failed = [r for r in results if r.run_output.errors]
    
    aggregate_metrics_list = aggregate_metrics(successful)
    
    # Compute cost summary
    total_cost = sum(r.run_output.cost_usd for r in results)
    total_tokens = sum(sum(r.run_output.token_usage.values()) for r in results)
    avg_latency = statistics.mean([r.run_output.latency_ms for r in results]) if results else 0.0
    
    cost_summary = {
        "total_cost_usd": total_cost,
        "total_tokens": total_tokens,
        "avg_latency_ms": avg_latency,
        "cost_per_query": total_cost / len(results) if results else 0.0,
    }
    
    # Extract failure modes
    failure_modes = []
    error_counts = defaultdict(int)
    for result in failed:
        for error in result.run_output.errors:
            error_type = error.split(":")[0] if ":" in error else "Unknown"
            error_counts[error_type] += 1
    
    for error_type, count in error_counts.items():
        failure_modes.append({
            "error_type": error_type,
            "count": count,
            "percentage": count / len(failed) * 100 if failed else 0.0
        })
    
    return EvaluationReport(
        config_name=config_name,
        total_queries=len(results),
        successful_runs=len(successful),
        failed_runs=len(failed),
        aggregate_metrics=aggregate_metrics_list,
        per_query_results=results,
        cost_summary=cost_summary,
        failure_modes=failure_modes
    )
