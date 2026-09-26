"""Evaluation configuration and toggles."""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum


class AgentMode(str, Enum):
    """Agent execution modes."""
    ENABLED = "enabled"
    DISABLED = "disabled"
    ORACLE = "oracle"  # Use oracle instead of real agent


@dataclass
class EvaluationConfig:
    """Configuration for evaluation runs."""
    # System toggles
    enable_rag: bool = True
    enable_debate: bool = True
    enable_memory: bool = True
    enable_multihop: bool = True
    enable_thought_tree: bool = True
    
    # Agent toggles
    agents_enabled: Dict[str, bool] = field(default_factory=lambda: {
        "search_agent": True,
        "strategic_planner": True,
        "synthesizer": True,
        "query_enricher": True,
    })
    
    # Oracle modes
    use_oracle_retrieval: bool = False
    use_oracle_planner: bool = False
    use_oracle_memory: bool = False
    
    # RAG settings
    rag_limit: int = 5
    rag_use_reranker: bool = True
    rag_max_hops: int = 3
    
    # Debate settings
    max_debate_rounds: int = 3
    
    # ThoughtTree settings
    thought_tree_iterations: int = 5
    thought_tree_max_depth: int = 3
    
    # Evaluation settings
    max_retries: int = 3
    timeout_seconds: int = 300
    capture_traces: bool = True
    
    # LLM Judge settings
    use_llm_judge: bool = True
    llm_judge_model: str = "gemini-1.5-pro"
    num_judges: int = 1
    blind_evaluation: bool = True
    
    # Output settings
    output_dir: str = "eval/outputs"
    save_traces: bool = True
    save_metrics: bool = True
    
    # Metadata
    config_name: str = "default"
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_preset(cls, preset: str) -> "EvaluationConfig":
        """Create config from preset name."""
        presets = {
            "full": cls(
                config_name="full",
                enable_rag=True,
                enable_debate=True,
                enable_memory=True,
                enable_multihop=True,
                enable_thought_tree=True,
            ),
            "no_debate": cls(
                config_name="no_debate",
                enable_debate=False,
            ),
            "no_memory": cls(
                config_name="no_memory",
                enable_memory=False,
            ),
            "no_multihop": cls(
                config_name="no_multihop",
                enable_multihop=False,
            ),
            "single_agent": cls(
                config_name="single_agent",
                enable_debate=False,
                enable_thought_tree=False,
                agents_enabled={
                    "search_agent": True,
                    "strategic_planner": False,
                    "synthesizer": True,
                    "query_enricher": False,
                }
            ),
            "baseline": cls(
                config_name="baseline",
                enable_rag=True,
                enable_debate=False,
                enable_memory=False,
                enable_multihop=False,
                enable_thought_tree=False,
                agents_enabled={
                    "search_agent": True,
                    "strategic_planner": False,
                    "synthesizer": True,
                    "query_enricher": False,
                }
            ),
        }
        
        if preset not in presets:
            raise ValueError(f"Unknown preset: {preset}. Available: {list(presets.keys())}")
        
        return presets[preset]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "config_name": self.config_name,
            "enable_rag": self.enable_rag,
            "enable_debate": self.enable_debate,
            "enable_memory": self.enable_memory,
            "enable_multihop": self.enable_multihop,
            "enable_thought_tree": self.enable_thought_tree,
            "agents_enabled": self.agents_enabled,
            "use_oracle_retrieval": self.use_oracle_retrieval,
            "use_oracle_planner": self.use_oracle_planner,
            "use_oracle_memory": self.use_oracle_memory,
            "metadata": self.metadata,
        }
