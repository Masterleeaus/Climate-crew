"""Debate metrics: claim coverage, consensus accuracy, judge flip rate."""
from typing import Dict, List, Any
from ..types import MetricResult


def _compute_claim_coverage(
    debate_traces: List[Dict[str, Any]],
    expected_topics: List[str]
) -> float:
    """
    Compute claim coverage: how many expected topics were discussed in debate.
    """
    if not expected_topics:
        return 1.0
    
    if not debate_traces:
        return 0.0
    
    # Extract all claims from debate
    all_claims = []
    for trace in debate_traces:
        all_claims.append(trace.get("advocate_claim", "").lower())
        all_claims.append(trace.get("critic_response", "").lower())
    
    claims_text = " ".join(all_claims)
    
    # Check coverage of expected topics
    covered = sum(1 for topic in expected_topics if topic.lower() in claims_text)
    
    return covered / len(expected_topics)


def _compute_consensus_accuracy(
    debate_traces: List[Dict[str, Any]],
    ground_truth_answer: str
) -> float:
    """
    Compute consensus accuracy: whether final consensus aligns with ground truth.
    """
    if not debate_traces:
        return 0.0
    
    # Get final consensus (last round's judge decision or consensus)
    final_trace = debate_traces[-1]
    consensus = final_trace.get("judge_decision", "") or final_trace.get("advocate_claim", "")
    
    if not consensus or not ground_truth_answer:
        return 0.5  # Neutral
    
    # Simple keyword overlap
    consensus_terms = set(consensus.lower().split())
    gt_terms = set(ground_truth_answer.lower().split())
    stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
    consensus_terms = {t for t in consensus_terms if t not in stopwords and len(t) > 2}
    gt_terms = {t for t in gt_terms if t not in stopwords and len(t) > 2}
    
    if not gt_terms:
        return 0.5
    
    overlap = len(consensus_terms & gt_terms) / len(gt_terms)
    return overlap


def _compute_judge_flip_rate(debate_traces: List[Dict[str, Any]]) -> float:
    """
    Compute judge flip rate: how often judge decisions changed between rounds.
    """
    if len(debate_traces) < 2:
        return 0.0
    
    decisions = [trace.get("judge_decision", "") for trace in debate_traces]
    decisions = [d for d in decisions if d]  # Filter empty
    
    if len(decisions) < 2:
        return 0.0
    
    flips = sum(1 for i in range(1, len(decisions)) if decisions[i] != decisions[i-1])
    
    return flips / (len(decisions) - 1) if len(decisions) > 1 else 0.0


def compute(run_output: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, MetricResult]:
    """
    Compute debate metrics.
    
    Args:
        run_output: RunOutput as dict with debate_traces
        ground_truth: Dict with expected_topics and ground_truth_answer
        
    Returns:
        Dict of metric name to MetricResult
    """
    debate_traces = run_output.get("debate_traces", [])
    expected_topics = ground_truth.get("expected_topics", [])
    ground_truth_answer = ground_truth.get("ground_truth_answer", "")
    
    claim_coverage = _compute_claim_coverage(debate_traces, expected_topics)
    consensus_accuracy = _compute_consensus_accuracy(debate_traces, ground_truth_answer)
    judge_flip_rate = _compute_judge_flip_rate(debate_traces)
    
    return {
        "claim_coverage": MetricResult(
            metric_name="claim_coverage",
            value=claim_coverage,
            components={"coverage": claim_coverage}
        ),
        "consensus_accuracy": MetricResult(
            metric_name="consensus_accuracy",
            value=consensus_accuracy,
            components={"accuracy": consensus_accuracy}
        ),
        "judge_flip_rate": MetricResult(
            metric_name="judge_flip_rate",
            value=judge_flip_rate,
            components={"flip_rate": judge_flip_rate}
        ),
    }
