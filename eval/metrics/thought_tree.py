"""ThoughtTree (MCTS) metrics: node expansion, best path regret, exploration entropy, convergence."""
from typing import Dict, List, Any
import math
from ..types import MetricResult


def _compute_node_expansion_efficiency(
    thought_tree_trace: Dict[str, Any]
) -> float:
    """
    Compute node expansion efficiency: value gained per node expanded.
    """
    if not thought_tree_trace:
        return 0.0
    
    nodes = thought_tree_trace.get("nodes", [])
    if not nodes:
        return 0.0
    
    total_value = sum(node.get("value", 0.0) for node in nodes)
    total_visits = sum(node.get("visits", 0) for node in nodes)
    
    if total_visits == 0:
        return 0.0
    
    return total_value / total_visits


def _compute_best_path_regret(
    thought_tree_trace: Dict[str, Any]
) -> float:
    """
    Compute best path regret: difference between best found path and optimal.
    Lower is better.
    """
    if not thought_tree_trace:
        return 1.0  # Maximum regret if no exploration
    
    nodes = thought_tree_trace.get("nodes", [])
    if not nodes:
        return 1.0
    
    # Find best node (highest value/visits ratio)
    best_ratio = 0.0
    for node in nodes:
        visits = node.get("visits", 0)
        if visits > 0:
            ratio = node.get("value", 0.0) / visits
            best_ratio = max(best_ratio, ratio)
    
    # Regret is inverse of best ratio (normalized)
    regret = 1.0 - best_ratio
    
    return max(0.0, min(1.0, regret))


def _compute_exploration_entropy(
    thought_tree_trace: Dict[str, Any]
) -> float:
    """
    Compute exploration entropy: how evenly nodes were explored.
    Higher entropy = more balanced exploration.
    """
    if not thought_tree_trace:
        return 0.0
    
    nodes = thought_tree_trace.get("nodes", [])
    if not nodes:
        return 0.0
    
    visits = [node.get("visits", 0) for node in nodes]
    total_visits = sum(visits)
    
    if total_visits == 0:
        return 0.0
    
    # Compute entropy
    entropy = 0.0
    for visit_count in visits:
        if visit_count > 0:
            p = visit_count / total_visits
            entropy -= p * math.log2(p)
    
    # Normalize by max entropy (log2 of number of nodes)
    max_entropy = math.log2(len(nodes)) if len(nodes) > 1 else 1.0
    normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
    
    return normalized_entropy


def _compute_early_convergence_rate(
    thought_tree_trace: Dict[str, Any]
) -> float:
    """
    Compute early convergence rate: how quickly the algorithm converged to best path.
    Lower is better (converged too early = bad exploration).
    """
    if not thought_tree_trace:
        return 0.0
    
    iterations = thought_tree_trace.get("iterations", 0)
    if iterations == 0:
        return 0.0
    
    nodes = thought_tree_trace.get("nodes", [])
    if not nodes:
        return 0.0
    
    # Find when best node was first visited
    best_node = None
    best_ratio = 0.0
    
    for node in nodes:
        visits = node.get("visits", 0)
        if visits > 0:
            ratio = node.get("value", 0.0) / visits
            if ratio > best_ratio:
                best_ratio = ratio
                best_node = node
    
    if not best_node:
        return 0.0
    
    # Check if best node was found early (first half of iterations)
    # This is a simplified heuristic - in real MCTS you'd track visit history
    best_visits = best_node.get("visits", 0)
    early_convergence = best_visits / iterations if iterations > 0 else 0.0
    
    # If best node has most visits and was found early, that's early convergence
    return early_convergence if early_convergence > 0.5 else 0.0


def compute(run_output: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, MetricResult]:
    """
    Compute ThoughtTree (MCTS) metrics.
    
    Args:
        run_output: RunOutput as dict with thought_tree_trace
        ground_truth: Dict (not used, but kept for consistency)
        
    Returns:
        Dict of metric name to MetricResult
    """
    thought_tree_trace = run_output.get("thought_tree_trace")
    
    if not thought_tree_trace:
        # Return zero metrics if no thought tree trace
        return {
            "node_expansion_efficiency": MetricResult(
                metric_name="node_expansion_efficiency",
                value=0.0,
                components={"efficiency": 0.0}
            ),
            "best_path_regret": MetricResult(
                metric_name="best_path_regret",
                value=1.0,
                components={"regret": 1.0}
            ),
            "exploration_entropy": MetricResult(
                metric_name="exploration_entropy",
                value=0.0,
                components={"entropy": 0.0}
            ),
            "early_convergence_rate": MetricResult(
                metric_name="early_convergence_rate",
                value=0.0,
                components={"convergence": 0.0}
            ),
        }
    
    # Convert to dict if it's a ThoughtTreeTrace object
    if hasattr(thought_tree_trace, '__dict__'):
        trace_dict = {
            "nodes": [
                {
                    "node_id": getattr(n, "node_id", ""),
                    "value": getattr(n, "value", 0.0),
                    "visits": getattr(n, "visits", 0),
                    "depth": getattr(n, "depth", 0),
                }
                for n in getattr(thought_tree_trace, "nodes", [])
            ],
            "iterations": getattr(thought_tree_trace, "iterations", 0),
        }
    else:
        trace_dict = thought_tree_trace
    
    efficiency = _compute_node_expansion_efficiency(trace_dict)
    regret = _compute_best_path_regret(trace_dict)
    entropy = _compute_exploration_entropy(trace_dict)
    convergence = _compute_early_convergence_rate(trace_dict)
    
    return {
        "node_expansion_efficiency": MetricResult(
            metric_name="node_expansion_efficiency",
            value=efficiency,
            components={"efficiency": efficiency}
        ),
        "best_path_regret": MetricResult(
            metric_name="best_path_regret",
            value=regret,
            components={"regret": regret}
        ),
        "exploration_entropy": MetricResult(
            metric_name="exploration_entropy",
            value=entropy,
            components={"entropy": entropy}
        ),
        "early_convergence_rate": MetricResult(
            metric_name="early_convergence_rate",
            value=convergence,
            components={"convergence": convergence}
        ),
    }
