"""Optional provider adapters; these functions are never called by offline CI."""

from __future__ import annotations

import json
import os
import re
from functools import lru_cache
from typing import Any


def _prompt(payload: dict[str, Any]) -> str:
    return (
        "Classify the claim using only the evidence packet below. Do not use outside facts. "
        "Return exactly one JSON object with keys relationship (supports|contradicts|mixed|insufficient), "
        "evidence_ids (array of supplied evidence IDs), confidence (number from 0 to 1), and caveat (string).\n\n"
        + json.dumps(payload, ensure_ascii=False)
    )


def _prediction_from_text(text: str, valid_ids: set[str]) -> dict[str, Any]:
    decoder = json.JSONDecoder()
    for index, character in enumerate(text):
        if character != "{":
            continue
        try:
            candidate, _ = decoder.raw_decode(text[index:])
        except json.JSONDecodeError:
            continue
        if not isinstance(candidate, dict) or "relationship" not in candidate:
            continue
        candidate["evidence_ids"] = [
            value for value in candidate.get("evidence_ids", []) if value in valid_ids
        ]
        candidate.setdefault("confidence", 0.5)
        candidate.setdefault("caveat", "")
        return candidate
    raise ValueError("provider response did not contain the requested JSON prediction")


@lru_cache(maxsize=1)
def _crew():
    from src.agents.deep_research.orchestrator import DeepResearchOrchestrator

    key = os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_API_KEY is required for the Climate Crew adapter")
    return DeepResearchOrchestrator(
        google_api_key=key,
        enable_dynamic_routing=False,
        enable_meta_learning=False,
        enable_collaboration=False,
        enable_memory=False,
    )


def deep_research_crew(payload: dict[str, Any]) -> dict[str, Any]:
    """Run the repository's deep-research orchestrator on one evidence packet."""
    response = _crew().run_deep_research(_prompt(payload))
    report = response.get("report", "") if isinstance(response, dict) else str(response)
    valid_ids = {item["evidence_id"] for item in payload["evidence"]}
    return _prediction_from_text(report, valid_ids)


def single_llm_baseline(payload: dict[str, Any]) -> dict[str, Any]:
    """Run one OpenAI chat completion as a declared single-model baseline."""
    from openai import OpenAI

    model = os.getenv("CLIMATE_CREW_BASELINE_MODEL", "gpt-4.1-mini")
    response = OpenAI().chat.completions.create(
        model=model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": "You are a single-model baseline for classifying supplied evidence. Follow the requested JSON schema and do not use outside facts.",
            },
            {"role": "user", "content": _prompt(payload)},
        ],
    )
    text = response.choices[0].message.content or ""
    valid_ids = {item["evidence_id"] for item in payload["evidence"]}
    return _prediction_from_text(text, valid_ids)
