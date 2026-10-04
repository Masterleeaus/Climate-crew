"""Run a paired evidence-reasoning comparison with pluggable model adapters."""

from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import math
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


ROOT = Path(__file__).resolve().parents[2]
DATASET = Path(__file__).with_name("data") / "climate_evidence_benchmark.json"
RELATIONSHIPS = ("supports", "contradicts", "mixed", "insufficient")
Adapter = Callable[[dict[str, Any]], Any]


class Evidence(BaseModel):
    model_config = ConfigDict(extra="forbid")
    evidence_id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    source_title: str = Field(min_length=1)
    source_url: str


class GroundTruth(BaseModel):
    model_config = ConfigDict(extra="forbid")
    relationship: Literal["supports", "contradicts", "mixed", "insufficient"]
    supporting_evidence_ids: list[str]
    contradicting_evidence_ids: list[str]
    relevant_evidence_ids: list[str]
    required_caveat: str


class BenchmarkCase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    case_id: str
    question: str
    claim: str
    evidence: list[Evidence] = Field(min_length=1)
    ground_truth: GroundTruth

    @model_validator(mode="after")
    def references_resolve(self) -> "BenchmarkCase":
        ids = {item.evidence_id for item in self.evidence}
        unknown = set(self.ground_truth.relevant_evidence_ids) - ids
        if unknown:
            raise ValueError(f"unknown relevant evidence IDs: {sorted(unknown)}")
        return self

    def prompt_payload(self) -> dict[str, Any]:
        """Return model input without leaking ground truth."""
        return {
            "case_id": self.case_id,
            "question": self.question,
            "claim": self.claim,
            "evidence": [item.model_dump(mode="json") for item in self.evidence],
        }


class Prediction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    relationship: Literal["supports", "contradicts", "mixed", "insufficient"]
    evidence_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    caveat: str = ""


def load_cases(path: Path = DATASET) -> list[BenchmarkCase]:
    raw = path.read_bytes()
    payload = json.loads(raw)
    cases = [BenchmarkCase.model_validate(item) for item in payload["cases"]]
    ids = [case.case_id for case in cases]
    if len(ids) != len(set(ids)):
        raise ValueError("benchmark case IDs must be unique")
    if len(cases) < 50:
        raise ValueError(f"benchmark needs at least 50 cases; found {len(cases)}")
    counts = {label: sum(case.ground_truth.relationship == label for case in cases) for label in RELATIONSHIPS}
    if any(count == 0 for count in counts.values()):
        raise ValueError(f"benchmark must contain every relationship; got {counts}")
    return cases


def wilson_interval(successes: int, total: int, z: float = 1.959963984540054) -> list[float]:
    if total == 0:
        return [0.0, 1.0]
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = (proportion + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total * total)) / denominator
    return [max(0.0, centre - margin), min(1.0, centre + margin)]


def _system_metrics(
    cases: list[BenchmarkCase],
    predictions: dict[str, Prediction],
) -> dict[str, Any]:
    correct = 0
    relevant_hit = relevant_total = cited_hit = cited_total = caveats_present = 0
    brier_total = 0.0
    per_case: dict[str, bool] = {}
    for case in cases:
        prediction = predictions[case.case_id]
        is_correct = prediction.relationship == case.ground_truth.relationship
        per_case[case.case_id] = is_correct
        correct += int(is_correct)
        brier_total += (prediction.confidence - float(is_correct)) ** 2
        expected = set(case.ground_truth.relevant_evidence_ids)
        cited = set(prediction.evidence_ids)
        relevant_hit += len(expected & cited)
        relevant_total += len(expected)
        cited_hit += len(expected & cited)
        cited_total += len(cited)
        caveats_present += int(bool(prediction.caveat.strip()))
    evidence_recall = relevant_hit / relevant_total if relevant_total else 0.0
    evidence_precision = cited_hit / cited_total if cited_total else 0.0
    evidence_f1 = 2 * evidence_precision * evidence_recall / (evidence_precision + evidence_recall) if evidence_precision + evidence_recall else 0.0
    return {
        "n": len(cases),
        "accuracy": correct / len(cases) if cases else 0.0,
        "accuracy_95_wilson_ci": wilson_interval(correct, len(cases)),
        "evidence_precision": evidence_precision,
        "evidence_recall": evidence_recall,
        "evidence_f1": evidence_f1,
        "nonempty_caveat_rate": caveats_present / len(cases) if cases else 0.0,
        "brier_score_correctness": brier_total / len(cases) if cases else 0.0,
        "per_case_correct": per_case,
    }


def paired_bootstrap_ci(
    crew_correct: dict[str, bool],
    baseline_correct: dict[str, bool],
    *,
    replicates: int = 10000,
    seed: int = 1042026,
) -> list[float]:
    ids = sorted(set(crew_correct) & set(baseline_correct))
    if not ids:
        return [0.0, 0.0]
    differences = [int(crew_correct[key]) - int(baseline_correct[key]) for key in ids]
    rng = random.Random(seed)
    means = []
    for _ in range(replicates):
        sample = [differences[rng.randrange(len(differences))] for _ in differences]
        means.append(sum(sample) / len(sample))
    means.sort()
    return [means[int(0.025 * (len(means) - 1))], means[int(0.975 * (len(means) - 1))]]


def compare_predictions(
    cases: list[BenchmarkCase],
    crew_predictions: dict[str, Prediction],
    single_predictions: dict[str, Prediction],
    *,
    bootstrap_replicates: int = 10000,
) -> dict[str, Any]:
    expected_ids = {case.case_id for case in cases}
    if set(crew_predictions) != expected_ids or set(single_predictions) != expected_ids:
        raise ValueError("each system must return exactly one prediction per benchmark case")
    crew = _system_metrics(cases, crew_predictions)
    single = _system_metrics(cases, single_predictions)
    delta = crew["accuracy"] - single["accuracy"]
    return {
        "case_count": len(cases),
        "crew": {key: value for key, value in crew.items() if key != "per_case_correct"},
        "single_llm_baseline": {key: value for key, value in single.items() if key != "per_case_correct"},
        "paired_accuracy_difference_crew_minus_baseline": {
            "estimate": delta,
            "95_ci": paired_bootstrap_ci(
                crew["per_case_correct"], single["per_case_correct"], replicates=bootstrap_replicates
            ),
            "method": "paired bootstrap over cases",
            "seed": 1042026,
            "replicates": bootstrap_replicates,
        },
    }


def run_comparison(
    cases: list[BenchmarkCase],
    crew_adapter: Adapter,
    baseline_adapter: Adapter,
    *,
    bootstrap_replicates: int = 10000,
) -> tuple[dict[str, Any], dict[str, Any]]:
    crew_predictions: dict[str, Prediction] = {}
    baseline_predictions: dict[str, Prediction] = {}
    for case in cases:
        payload = case.prompt_payload()
        crew_predictions[case.case_id] = Prediction.model_validate(crew_adapter(payload))
        baseline_predictions[case.case_id] = Prediction.model_validate(baseline_adapter(payload))
    result = compare_predictions(
        cases, crew_predictions, baseline_predictions, bootstrap_replicates=bootstrap_replicates
    )
    result["dataset_sha256"] = hashlib.sha256(DATASET.read_bytes()).hexdigest()
    result["run_kind"] = "provider-run; inspect adapter/model names before interpreting"
    return result, {"crew": crew_predictions, "single_llm_baseline": baseline_predictions}


def _load_callable(spec: str) -> Adapter:
    module_name, separator, attribute = spec.partition(":")
    if not separator:
        raise ValueError("adapter must use module:function syntax")
    function = getattr(importlib.import_module(module_name), attribute)
    if not callable(function):
        raise TypeError(f"adapter {spec} is not callable")
    return function


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--crew-adapter", required=True, help="module:function for the multi-agent crew")
    parser.add_argument("--baseline-adapter", required=True, help="module:function for one LLM call")
    parser.add_argument("--limit", type=int, default=None, help="run the first N cases for a cost-limited pilot")
    parser.add_argument("--output", type=Path, default=None, help="optional JSON report path")
    parser.add_argument("--bootstrap-replicates", type=int, default=10000)
    args = parser.parse_args()
    cases = load_cases()
    if args.limit is not None:
        if args.limit < 1:
            parser.error("--limit must be >= 1")
        cases = cases[:args.limit]
    result, predictions = run_comparison(
        cases, _load_callable(args.crew_adapter), _load_callable(args.baseline_adapter),
        bootstrap_replicates=args.bootstrap_replicates,
    )
    result["run_kind"] = "provider-run"
    result["adapters"] = {"crew": args.crew_adapter, "single_llm_baseline": args.baseline_adapter}
    result["created_at_utc"] = datetime.now(timezone.utc).isoformat()
    result["predictions"] = {
        name: {case_id: prediction.model_dump(mode="json") for case_id, prediction in rows.items()}
        for name, rows in predictions.items()
    }
    output = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
