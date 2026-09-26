"""Efficiency metrics: latency, token usage, API cost."""
from typing import Dict, Any
from ..types import MetricResult


def compute(run_output: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, MetricResult]:
    """
    Compute efficiency metrics.
    
    Args:
        run_output: RunOutput as dict with latency_ms, token_usage, cost_usd
        ground_truth: Dict (not used, but kept for consistency)
        
    Returns:
        Dict of metric name to MetricResult
    """
    latency_ms = run_output.get("latency_ms", 0.0)
    token_usage = run_output.get("token_usage", {})
    cost_usd = run_output.get("cost_usd", 0.0)
    
    total_tokens = sum(token_usage.values()) if token_usage else 0
    input_tokens = token_usage.get("input_tokens", 0)
    output_tokens = token_usage.get("output_tokens", 0)
    
    return {
        "latency_ms": MetricResult(
            metric_name="latency_ms",
            value=latency_ms,
            components={"latency": latency_ms}
        ),
        "total_tokens": MetricResult(
            metric_name="total_tokens",
            value=float(total_tokens),
            components={
                "total": float(total_tokens),
                "input": float(input_tokens),
                "output": float(output_tokens),
            }
        ),
        "cost_usd": MetricResult(
            metric_name="cost_usd",
            value=cost_usd,
            components={"cost": cost_usd}
        ),
        "tokens_per_second": MetricResult(
            metric_name="tokens_per_second",
            value=total_tokens / (latency_ms / 1000.0) if latency_ms > 0 else 0.0,
            components={"throughput": total_tokens / (latency_ms / 1000.0) if latency_ms > 0 else 0.0}
        ),
    }
