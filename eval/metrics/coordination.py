"""Coordination metrics: agent contribution, redundancy, failure cascade."""
from typing import Dict, List, Any
from collections import Counter
from ..types import MetricResult


def _compute_marginal_agent_contribution(
    agent_outputs: List[Dict[str, Any]],
    final_answer: str
) -> Dict[str, float]:
    """
    Compute marginal contribution of each agent.
    Returns dict of agent_name -> contribution_score.
    """
    if not agent_outputs:
        return {}
    
    # Simple heuristic: check how much of each agent's output appears in final answer
    contributions = {}
    final_answer_lower = final_answer.lower()
    
    for agent_output in agent_outputs:
        agent_name = agent_output.get("agent_name", "unknown")
        output = agent_output.get("output", "")
        
        if not output:
            contributions[agent_name] = 0.0
            continue
        
        # Extract key terms from agent output
        output_terms = set(output.lower().split())
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        output_terms = {t for t in output_terms if t not in stopwords and len(t) > 3}
        
        if not output_terms:
            contributions[agent_name] = 0.0
            continue
        
        # Check overlap with final answer
        found_terms = sum(1 for term in output_terms if term in final_answer_lower)
        contribution = found_terms / len(output_terms) if output_terms else 0.0
        
        contributions[agent_name] = contribution
    
    return contributions


def _compute_redundancy_score(
    agent_outputs: List[Dict[str, Any]]
) -> float:
    """
    Compute redundancy score: how much overlap between agent outputs.
    Higher = more redundant.
    """
    if len(agent_outputs) < 2:
        return 0.0  # No redundancy with single agent
    
    # Extract key terms from each agent output
    agent_terms = []
    for agent_output in agent_outputs:
        output = agent_output.get("output", "")
        terms = set(output.lower().split())
        stopwords = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"}
        terms = {t for t in terms if t not in stopwords and len(t) > 3}
        agent_terms.append(terms)
    
    if not agent_terms:
        return 0.0
    
    # Compute pairwise overlaps
    total_overlap = 0.0
    pairs = 0
    
    for i in range(len(agent_terms)):
        for j in range(i + 1, len(agent_terms)):
            terms_i = agent_terms[i]
            terms_j = agent_terms[j]
            
            if not terms_i or not terms_j:
                continue
            
            overlap = len(terms_i & terms_j)
            union = len(terms_i | terms_j)
            
            if union > 0:
                jaccard = overlap / union
                total_overlap += jaccard
                pairs += 1
    
    return total_overlap / pairs if pairs > 0 else 0.0


def _compute_failure_cascade_depth(
    agent_outputs: List[Dict[str, Any]],
    errors: List[str]
) -> float:
    """
    Compute failure cascade depth: how many agents were affected by errors.
    """
    if not errors:
        return 0.0
    
    # Check which agents have errors in their metadata or outputs
    affected_agents = set()
    
    for error in errors:
        # Try to extract agent name from error message
        for agent_output in agent_outputs:
            agent_name = agent_output.get("agent_name", "")
            if agent_name.lower() in error.lower():
                affected_agents.add(agent_name)
    
    # Also check agent metadata for error flags
    for agent_output in agent_outputs:
        metadata = agent_output.get("metadata", {})
        if metadata.get("error") or metadata.get("failed"):
            affected_agents.add(agent_output.get("agent_name", ""))
    
    total_agents = len(agent_outputs)
    if total_agents == 0:
        return 0.0
    
    return len(affected_agents) / total_agents


def compute(run_output: Dict[str, Any], ground_truth: Dict[str, Any]) -> Dict[str, MetricResult]:
    """
    Compute coordination metrics.
    
    Args:
        run_output: RunOutput as dict with agent_outputs, final_answer, errors
        ground_truth: Dict (not used, but kept for consistency)
        
    Returns:
        Dict of metric name to MetricResult
    """
    agent_outputs = run_output.get("agent_outputs", [])
    final_answer = run_output.get("final_answer", "")
    errors = run_output.get("errors", [])
    
    contributions = _compute_marginal_agent_contribution(agent_outputs, final_answer)
    redundancy = _compute_redundancy_score(agent_outputs)
    failure_cascade = _compute_failure_cascade_depth(agent_outputs, errors)
    
    # Average contribution score
    avg_contribution = sum(contributions.values()) / len(contributions) if contributions else 0.0
    
    return {
        "marginal_agent_contribution": MetricResult(
            metric_name="marginal_agent_contribution",
            value=avg_contribution,
            components=contributions
        ),
        "redundancy_score": MetricResult(
            metric_name="redundancy_score",
            value=redundancy,
            components={"redundancy": redundancy}
        ),
        "failure_cascade_depth": MetricResult(
            metric_name="failure_cascade_depth",
            value=failure_cascade,
            components={"cascade_depth": failure_cascade}
        ),
    }
