"""Evaluation framework for the multi-agent system.

Keep the legacy runner lazy so lightweight subpackages such as
``eval.science_quality`` can run without importing the full app's optional
provider stack.
"""

from .types import (
    EvaluationQuery,
    RunOutput,
    EvaluationResult,
    EvaluationReport,
    MetricResult,
    AggregateMetrics,
    Difficulty,
)

__all__ = [
    "run_evaluation",
    "EvaluationQuery",
    "RunOutput",
    "EvaluationResult",
    "EvaluationReport",
    "MetricResult",
    "AggregateMetrics",
    "Difficulty",
]


def __getattr__(name: str):
    if name == "run_evaluation":
        from .runner import run_evaluation

        return run_evaluation
    raise AttributeError(name)
