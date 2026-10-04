"""Build the checked-in synthetic evidence-reasoning benchmark."""

from __future__ import annotations

import json
from pathlib import Path


CONTEXTS = [
    ("global annual surface-temperature anomaly", "°C/decade"),
    ("upper-ocean heat content", "10^22 J/decade"),
    ("global mean sea level", "mm/year"),
    ("September Arctic sea-ice area", "million km²/decade"),
    ("mountain glacier mass balance", "m water equivalent/year"),
    ("atmospheric carbon-dioxide concentration", "ppm/decade"),
    ("surface-ocean pH", "pH units/decade"),
    ("annual heatwave days", "days/decade"),
    ("Northern Hemisphere snow-cover duration", "days/decade"),
    ("summer soil moisture in a dryland region", "percent/decade"),
    ("coral-bleaching incidence in a monitored reef network", "percent/decade"),
    ("spring leaf-out date (later dates are positive)", "days/decade"),
    ("heavy-precipitation intensity", "mm/decade"),
    ("area burned by wildfires in a defined region", "km²/decade"),
    ("permafrost active-layer thickness", "cm/decade"),
]


def build() -> dict[str, object]:
    cases: list[dict[str, object]] = []
    for relation in ("supports", "contradicts", "mixed", "insufficient"):
        for index, (metric, unit) in enumerate(CONTEXTS, start=1):
            case_id = f"{relation[:3]}-{index:02d}"
            claim = f"The supplied record establishes a positive monotonic trend in {metric}."
            question = (
                "Using only the supplied evidence packet, classify its relationship to the claim as "
                "supports, contradicts, mixed, or insufficient. Cite the evidence IDs used and state "
                "the main limitation. Do not infer causation."
            )
            evidence: list[dict[str, str]]
            supporting: list[str] = []
            contradicting: list[str] = []
            if relation == "supports":
                amount = 0.03 + index * 0.007
                evidence = [{
                    "evidence_id": f"{case_id}-A",
                    "summary": f"Synthetic controlled result for {metric}, 1981–2020: slope +{amount:.3f} {unit}; 95% interval [+{amount*0.55:.3f}, +{amount*1.45:.3f}]; two-sided trend-test p=0.01.",
                    "source_title": "Synthetic benchmark record A",
                    "source_url": f"https://example.invalid/climate-crew/{case_id}/a",
                }]
                supporting = [f"{case_id}-A"]
            elif relation == "contradicts":
                amount = 0.03 + index * 0.007
                evidence = [{
                    "evidence_id": f"{case_id}-A",
                    "summary": f"Synthetic controlled result for {metric}, 1981–2020: slope -{amount:.3f} {unit}; 95% interval [-{amount*1.45:.3f}, -{amount*0.55:.3f}]; two-sided trend-test p=0.01.",
                    "source_title": "Synthetic benchmark record A",
                    "source_url": f"https://example.invalid/climate-crew/{case_id}/a",
                }]
                contradicting = [f"{case_id}-A"]
            elif relation == "mixed":
                amount = 0.04 + index * 0.005
                evidence = [
                    {
                        "evidence_id": f"{case_id}-A",
                        "summary": f"Synthetic controlled result for {metric}, 1981–2020, method A: slope +{amount:.3f} {unit}; 95% interval excludes zero; p=0.02.",
                        "source_title": "Synthetic benchmark record A",
                        "source_url": f"https://example.invalid/climate-crew/{case_id}/a",
                    },
                    {
                        "evidence_id": f"{case_id}-B",
                        "summary": f"Synthetic controlled result for the same metric and period, independent method B: slope -{amount*0.8:.3f} {unit}; 95% interval excludes zero; p=0.03.",
                        "source_title": "Synthetic benchmark record B",
                        "source_url": f"https://example.invalid/climate-crew/{case_id}/b",
                    },
                ]
                supporting = [f"{case_id}-A"]
                contradicting = [f"{case_id}-B"]
            else:
                evidence = [{
                    "evidence_id": f"{case_id}-A",
                    "summary": f"Synthetic controlled record for {metric}: the first and last readings differ by +0.4 {unit.split('/')[0]}, but intermediate observations, a trend estimate, measurement uncertainty, and method details are not supplied.",
                    "source_title": "Synthetic incomplete benchmark record",
                    "source_url": f"https://example.invalid/climate-crew/{case_id}/a",
                }]
            cases.append({
                "case_id": case_id,
                "question": question,
                "claim": claim,
                "evidence": evidence,
                "ground_truth": {
                    "relationship": relation,
                    "supporting_evidence_ids": supporting,
                    "contradicting_evidence_ids": contradicting,
                    "relevant_evidence_ids": sorted(set(supporting + contradicting)) or [f"{case_id}-A"],
                    "required_caveat": (
                        "This classification concerns only the supplied synthetic evidence and does not establish causation or a real-world climate fact."
                    ),
                },
            })
    return {
        "schema_version": 1,
        "title": "Climate Crew controlled supplied-evidence reasoning benchmark",
        "provenance": "Synthetic scenarios generated by eval/science_quality/build_dataset.py; not observational climate data.",
        "design": "15 metrics x 4 balanced evidence relationships; tests evidence classification, contradiction handling, citation use, and calibrated confidence over supplied records.",
        "cases": cases,
    }


if __name__ == "__main__":
    target = Path(__file__).with_name("data") / "climate_evidence_benchmark.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(build(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(build()['cases'])} synthetic cases to {target}")
