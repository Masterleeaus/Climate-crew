"""Typed records for an evidence-to-falsification research review."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, model_validator


EvidenceKind = Literal["observation", "dataset", "publication", "derived", "modelled"]
HypothesisStatus = Literal["supported", "challenged", "unresolved"]
TestOutcome = Literal["falsified", "not_falsified", "inconclusive"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class EvidenceRecord(StrictModel):
    """An attributable input or derived result in a small evidence graph."""

    evidence_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    source_title: str = Field(min_length=1)
    source_url: AnyHttpUrl
    evidence_kind: EvidenceKind
    retrieved_at: date
    independence_group: str = Field(min_length=1)
    derived_from: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class Hypothesis(StrictModel):
    hypothesis_id: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    status: HypothesisStatus


class FalsificationTest(StrictModel):
    test_id: str = Field(min_length=1)
    hypothesis_id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    method: str = Field(min_length=1)
    outcome: TestOutcome
    result_summary: str = Field(min_length=1)
    evidence_ids: list[str] = Field(min_length=1)
    predeclared: bool = False


class UncertaintyAssessment(StrictModel):
    estimate: float
    unit: str = Field(min_length=1)
    interval_level: float = Field(gt=0.0, lt=1.0)
    lower_bound: float
    upper_bound: float
    method: str = Field(min_length=1)
    caveats: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def bounds_are_ordered(self) -> "UncertaintyAssessment":
        if self.lower_bound > self.upper_bound:
            raise ValueError("lower_bound must not exceed upper_bound")
        if not self.lower_bound <= self.estimate <= self.upper_bound:
            raise ValueError("estimate must lie inside the uncertainty interval")
        return self


class ScientificReport(StrictModel):
    """A reviewable result with explicit evidence, alternatives and limits."""

    question: str = Field(min_length=1)
    hypotheses: list[Hypothesis] = Field(min_length=2)
    evidence: list[EvidenceRecord] = Field(min_length=1)
    falsification_tests: list[FalsificationTest] = Field(min_length=1)
    uncertainty: UncertaintyAssessment
    conclusion: str = Field(min_length=1)
    limitations: list[str] = Field(min_length=1)

    @model_validator(mode="after")
    def graph_references_resolve(self) -> "ScientificReport":
        evidence_ids = {record.evidence_id for record in self.evidence}
        hypothesis_ids = {hypothesis.hypothesis_id for hypothesis in self.hypotheses}
        if len(evidence_ids) != len(self.evidence):
            raise ValueError("evidence_id values must be unique")
        if len(hypothesis_ids) != len(self.hypotheses):
            raise ValueError("hypothesis_id values must be unique")
        for record in self.evidence:
            unknown = set(record.derived_from) - evidence_ids
            if unknown:
                raise ValueError(f"{record.evidence_id} refers to unknown evidence: {sorted(unknown)}")
            if record.evidence_id in record.derived_from:
                raise ValueError("an evidence record cannot derive from itself")
        for test in self.falsification_tests:
            if test.hypothesis_id not in hypothesis_ids:
                raise ValueError(f"{test.test_id} refers to an unknown hypothesis")
            unknown = set(test.evidence_ids) - evidence_ids
            if unknown:
                raise ValueError(f"{test.test_id} refers to unknown evidence: {sorted(unknown)}")
        return self
