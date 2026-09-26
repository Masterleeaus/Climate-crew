"""Ablation study configurations."""
from typing import List, Dict, Any
from ..config import EvaluationConfig


def get_ablation_configs() -> List[EvaluationConfig]:
    """
    Get list of ablation study configurations.
    
    Returns:
        List of EvaluationConfig objects for different ablations
    """
    configs = []
    
    # Full system
    configs.append(EvaluationConfig.from_preset("full"))
    
    # No debate
    configs.append(EvaluationConfig.from_preset("no_debate"))
    
    # No memory
    configs.append(EvaluationConfig.from_preset("no_memory"))
    
    # No multihop
    configs.append(EvaluationConfig.from_preset("no_multihop"))
    
    # Single agent
    configs.append(EvaluationConfig.from_preset("single_agent"))
    
    # Baseline
    configs.append(EvaluationConfig.from_preset("baseline"))
    
    # No thought tree
    no_thought_tree = EvaluationConfig.from_preset("full")
    no_thought_tree.enable_thought_tree = False
    no_thought_tree.config_name = "no_thought_tree"
    configs.append(no_thought_tree)
    
    # No reranker
    no_reranker = EvaluationConfig.from_preset("full")
    no_reranker.rag_use_reranker = False
    no_reranker.config_name = "no_reranker"
    configs.append(no_reranker)
    
    return configs


def compare_configs(
    baseline_config: EvaluationConfig,
    ablation_config: EvaluationConfig
) -> Dict[str, Any]:
    """
    Compare two configurations and return differences.
    
    Args:
        baseline_config: Baseline configuration
        ablation_config: Ablation configuration
        
    Returns:
        Dict with differences
    """
    baseline_dict = baseline_config.to_dict()
    ablation_dict = ablation_config.to_dict()
    
    differences = {}
    for key in baseline_dict:
        if baseline_dict[key] != ablation_dict.get(key):
            differences[key] = {
                "baseline": baseline_dict[key],
                "ablation": ablation_dict.get(key)
            }
    
    return differences
