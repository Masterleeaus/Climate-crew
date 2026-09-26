"""Shared dataclasses and types for the evaluation framework."""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from datetime import datetime


class Difficulty(str, Enum):
    """Query difficulty levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"


@dataclass
class EvaluationQuery:
    """Single evaluation query with ground truth."""
    query: str
    expected_topics: List[str]
    ground_truth_answer: str
    difficulty: Difficulty
    requires_multihop: bool
    requires_debate: bool
    requires_memory: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RetrievalResult:
    """Retrieval result from RAG system."""
    document_id: str
    content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    rank: int = 0


@dataclass
class AgentOutput:
    """Output from a single agent."""
    agent_name: str
    output: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DebateTrace:
    """Trace of a debate between agents."""
    round: int
    advocate_claim: str
    critic_response: str
    judge_decision: Optional[str] = None
    consensus_reached: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThoughtTreeNode:
    """Node in the ThoughtTree (MCTS)."""
    node_id: str
    state: str
    parent_id: Optional[str] = None
    children_ids: List[str] = field(default_factory=list)
    visits: int = 0
    value: float = 0.0
    depth: int = 0
    research_data: List[Dict] = field(default_factory=list)


@dataclass
class ThoughtTreeTrace:
    """Trace of ThoughtTree MCTS execution."""
    root_node_id: str
    nodes: List[ThoughtTreeNode] = field(default_factory=list)
    iterations: int = 0
    best_path: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MemoryOperation:
    """Memory operation trace."""
    operation_type: str  # "store", "retrieve", "update", "delete"
    key: str
    value: Optional[Any] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RunOutput:
    """Complete output from a single evaluation run."""
    query: str
    final_answer: str
    retrieval_results: List[RetrievalResult] = field(default_factory=list)
    agent_outputs: List[AgentOutput] = field(default_factory=list)
    debate_traces: List[DebateTrace] = field(default_factory=list)
    thought_tree_trace: Optional[ThoughtTreeTrace] = None
    memory_operations: List[MemoryOperation] = field(default_factory=list)
    latency_ms: float = 0.0
    token_usage: Dict[str, int] = field(default_factory=dict)
    cost_usd: float = 0.0
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricResult:
    """Result from a single metric computation."""
    metric_name: str
    value: float
    components: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationResult:
    """Complete evaluation result for a single query."""
    query: EvaluationQuery
    run_output: RunOutput
    metrics: List[MetricResult] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    config_name: str = "default"


@dataclass
class AggregateMetrics:
    """Aggregated metrics across multiple runs."""
    metric_name: str
    mean: float
    std: float
    min: float
    max: float
    median: float
    count: int
    per_difficulty: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvaluationReport:
    """Complete evaluation report."""
    config_name: str
    total_queries: int
    successful_runs: int
    failed_runs: int
    aggregate_metrics: List[AggregateMetrics] = field(default_factory=list)
    per_query_results: List[EvaluationResult] = field(default_factory=list)
    cost_summary: Dict[str, Any] = field(default_factory=dict)
    failure_modes: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
