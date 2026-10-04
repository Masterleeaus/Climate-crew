#!/usr/bin/env python3
"""Reproduce a bounded, non-attribution trend analysis from a pinned NASA CSV."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.science.models import (
    EvidenceRecord,
    FalsificationTest,
    Hypothesis,
    ScientificReport,
    UncertaintyAssessment,
)
from src.science.statistics import AnnualSeries, load_gistemp_annual, ols_slope, trend_summary


DATA = ROOT / "data/science/GLB.Ts+dSST.csv"
MANIFEST = ROOT / "data/science/gistemp_manifest.json"
OUTPUT = ROOT / "artifacts/science"
SOURCE_PAGE = "https://data.giss.nasa.gov/gistemp/data_v4.html"
SOURCE_CSV = "https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv"


def make_report(series: AnnualSeries, summary: dict[str, object], sha256: str) -> ScientificReport:
    ci = summary["ols_slope_95_ci_c_per_decade"]
    primary = summary["mann_kendall"]
    endpoint = summary["endpoint_falsification"]
    rise_supported = primary["tau_b"] > 0 and primary["p_value"] < 0.05
    endpoint_survives = endpoint["outcome"] == "not_falsified"
    return ScientificReport(
        question=f"Did annual global GISTEMP land-ocean anomalies increase over {series.years[0]}–{series.years[-1]}?",
        hypotheses=[
            Hypothesis(
                hypothesis_id="H1",
                statement="The annual global land-ocean temperature anomaly series has a positive monotonic trend over the stated period.",
                status="supported" if rise_supported and endpoint_survives else "unresolved",
            ),
            Hypothesis(
                hypothesis_id="H2",
                statement="The apparent full-period rise is solely a recent-endpoint effect and disappears when the final ten years are omitted.",
                status="challenged" if endpoint_survives else "unresolved",
            ),
        ],
        evidence=[
            EvidenceRecord(
                evidence_id="E1",
                statement="NASA GISTEMP v4 global land-ocean annual mean temperature anomalies (J-D column), relative to the 1951–1980 baseline.",
                source_title="NASA GISS Surface Temperature Analysis v4 data downloads",
                source_url=SOURCE_PAGE,
                evidence_kind="dataset",
                retrieved_at="2026-10-04",
                independence_group="NASA-GISTEMP-v4",
                limitations=["A global aggregate does not represent local or regional trends.", "An anomaly series alone does not identify causal attribution."],
            ),
            EvidenceRecord(
                evidence_id="E2",
                statement=f"SHA-256 {sha256}; {summary['n']} complete annual values were analysed for {summary['period'][0]}–{summary['period'][1]}.",
                source_title="Pinned GISTEMP CSV snapshot and deterministic analysis",
                source_url=SOURCE_CSV,
                evidence_kind="derived",
                retrieved_at="2026-10-04",
                independence_group="NASA-GISTEMP-v4-derived",
                derived_from=["E1"],
                limitations=["A reproducibility snapshot can differ from later NASA revisions."],
            ),
            EvidenceRecord(
                evidence_id="E3",
                statement=f"Mann–Kendall tau-b={primary['tau_b']:.4f}, p={primary['p_value']:.3g}; Sen slope={summary['sen_slope_c_per_decade']:.4f} °C/decade; the block-bootstrap OLS 95% interval is {ci[0]:.4f} to {ci[1]:.4f} °C/decade.",
                source_title="Climate Crew reproducible calculation",
                source_url=SOURCE_CSV,
                evidence_kind="derived",
                retrieved_at="2026-10-04",
                independence_group="Climate-Crew-analysis-v1",
                derived_from=["E2"],
                limitations=["The bootstrap interval quantifies sampling sensitivity under the stated residual block scheme; it does not include all measurement or structural uncertainty."],
            ),
        ],
        falsification_tests=[
            FalsificationTest(
                test_id="F1",
                hypothesis_id="H1",
                question=endpoint["question"],
                method="Exploratory endpoint sensitivity: re-run Mann–Kendall and Sen-slope estimates through the year before the final ten observations.",
                outcome="not_falsified" if endpoint_survives else "inconclusive",
                result_summary=f"For {endpoint['period'][0]}–{endpoint['period'][1]}, Sen slope={endpoint['sen_slope_c_per_decade']:.4f} °C/decade and Mann–Kendall p={endpoint['mann_kendall']['p_value']:.3g}.",
                evidence_ids=["E2", "E3"],
            )
        ],
        uncertainty=UncertaintyAssessment(
            estimate=summary["ols_slope_c_per_decade"],
            unit="°C/decade",
            interval_level=0.95,
            lower_bound=ci[0],
            upper_bound=ci[1],
            method=summary["methods"]["interval"],
            caveats=["This interval reflects the specified block-bootstrap procedure, not all sources of uncertainty.", "The analysis is descriptive and does not attribute causes."],
        ),
        conclusion=(
            "The pinned global anomaly series shows a positive monotonic trend over the analysis period; "
            "the exploratory endpoint sensitivity check does not overturn that pattern. This is a descriptive "
            "time-series result, not a causal attribution analysis."
            if rise_supported and endpoint_survives
            else "The specified analysis does not establish a robust positive monotonic trend; treat the result as unresolved."
        ),
        limitations=[
            "One global annual series is not an independent replication across datasets.",
            "A monotonic trend test does not explain causes or predict local impacts.",
            "The pinned snapshot and the analysis choices should be revisited when reproducing later NASA revisions.",
        ],
    )


def render_svg(series: AnnualSeries) -> str:
    width, height = 1000, 560
    left, right, top, bottom = 86, 34, 70, 72
    values = series.anomalies_c
    years = series.years
    y_min = min(-0.6, min(values) - 0.08)
    y_max = max(1.2, max(values) + 0.08)
    plot_w, plot_h = width - left - right, height - top - bottom

    def px(year: int) -> float:
        return left + (year - years[0]) / (years[-1] - years[0]) * plot_w

    def py(value: float) -> float:
        return top + (y_max - value) / (y_max - y_min) * plot_h

    slope = ols_slope(years, values)
    x_bar = sum(years) / len(years)
    y_bar = sum(values) / len(values)
    intercept = y_bar - slope * x_bar
    points = " ".join(f"{px(year):.2f},{py(value):.2f}" for year, value in zip(years, values))
    trend_points = f"{px(years[0]):.2f},{py(intercept + slope * years[0]):.2f} {px(years[-1]):.2f},{py(intercept + slope * years[-1]):.2f}"
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        '<title id="title">NASA GISTEMP global annual land-ocean temperature anomalies</title>',
        '<desc id="desc">Annual anomalies for 1880 through 2025 and an ordinary least-squares trend line. Descriptive result; no causal attribution.</desc>',
        '<rect width="100%" height="100%" fill="#fbfdff"/>',
        '<style>text{font-family:Arial,sans-serif;fill:#263342}.grid{stroke:#dce4eb;stroke-width:1}.axis{stroke:#536273;stroke-width:1.2}.series{fill:none;stroke:#087e8b;stroke-width:2}.trend{stroke:#d9573f;stroke-width:2.5;stroke-dasharray:8 6}</style>',
        f'<text x="{left}" y="34" font-size="21" font-weight="700">Global land-ocean temperature anomalies (°C)</text>',
    ]
    for step in range(7):
        value = round(y_min + (y_max - y_min) * step / 6, 1)
        y = py(value)
        parts.append(f'<line class="grid" x1="{left}" x2="{width-right}" y1="{y:.2f}" y2="{y:.2f}"/>')
        parts.append(f'<text x="{left-12}" y="{y+5:.2f}" text-anchor="end" font-size="12">{value:.1f}</text>')
    for year in range((years[0] // 20) * 20, years[-1] + 1, 20):
        if years[0] <= year <= years[-1]:
            x = px(year)
            parts.append(f'<line class="grid" x1="{x:.2f}" x2="{x:.2f}" y1="{top}" y2="{height-bottom}"/>')
            parts.append(f'<text x="{x:.2f}" y="{height-bottom+24}" text-anchor="middle" font-size="12">{year}</text>')
    parts.extend([
        f'<line class="axis" x1="{left}" x2="{width-right}" y1="{height-bottom}" y2="{height-bottom}"/>',
        f'<line class="axis" x1="{left}" x2="{left}" y1="{top}" y2="{height-bottom}"/>',
        f'<polyline class="series" points="{points}"/>',
        f'<line class="trend" x1="{trend_points.split()[0].split(",")[0]}" y1="{trend_points.split()[0].split(",")[1]}" x2="{trend_points.split()[1].split(",")[0]}" y2="{trend_points.split()[1].split(",")[1]}"/>',
        f'<text x="{left + 12}" y="{height - 23}" font-size="12">NASA GISTEMP v4 • 1951–1980 baseline • Source CSV snapshot checked in</text>',
        f'<line x1="{width-285}" y1="38" x2="{width-252}" y2="38" class="series"/><text x="{width-244}" y="42" font-size="12">Annual anomaly</text>',
        f'<line x1="{width-135}" y1="38" x2="{width-103}" y2="38" class="trend"/><text x="{width-96}" y="42" font-size="12">OLS trend</text>',
        '</svg>',
    ])
    return "\n".join(parts) + "\n"


def build_outputs(data_path: Path = DATA) -> tuple[bytes, bytes]:
    series = load_gistemp_annual(data_path)
    summary = trend_summary(series)
    sha256 = hashlib.sha256(data_path.read_bytes()).hexdigest()
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if data_path.resolve() == DATA.resolve() and sha256 != manifest["snapshot_sha256"]:
        raise ValueError("Pinned GISTEMP snapshot hash does not match data/science/gistemp_manifest.json")
    report = make_report(series, summary, sha256)
    result = {
        "dataset": manifest["dataset"],
        "source_page": manifest["source_page"],
        "source_csv": manifest["source_csv"],
        "snapshot_sha256": sha256,
        "baseline": manifest["baseline_period"],
        "retrieved_at": manifest["retrieved_at"],
        "summary": summary,
        "report": report.model_dump(mode="json"),
    }
    json_bytes = (json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
    svg_bytes = render_svg(series).encode("utf-8")
    return json_bytes, svg_bytes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, default=DATA, help="Pinned NASA GISTEMP CSV")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT)
    parser.add_argument("--check", action="store_true", help="Fail if checked-in results differ")
    args = parser.parse_args()
    json_bytes, svg_bytes = build_outputs(args.data)
    json_path = args.output_dir / "gistemp_trend_result.json"
    svg_path = args.output_dir / "gistemp_global_trend.svg"
    if args.check:
        stale = [str(path) for path, data in ((json_path, json_bytes), (svg_path, svg_bytes)) if not path.exists() or path.read_bytes() != data]
        if stale:
            print("Reproducible output is stale: " + ", ".join(stale))
            return 1
        print(f"Verified {json_path.relative_to(ROOT)} and {svg_path.relative_to(ROOT)}")
        return 0
    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path.write_bytes(json_bytes)
    svg_path.write_bytes(svg_bytes)
    payload = json.loads(json_bytes)
    summary = payload["summary"]
    print(f"Years: {summary['period'][0]}–{summary['period'][1]} (n={summary['n']})")
    print(f"OLS slope: {summary['ols_slope_c_per_decade']:.4f} °C/decade, 95% block-bootstrap CI {summary['ols_slope_95_ci_c_per_decade'][0]:.4f} to {summary['ols_slope_95_ci_c_per_decade'][1]:.4f}")
    print(f"Mann–Kendall: tau-b={summary['mann_kendall']['tau_b']:.4f}, p={summary['mann_kendall']['p_value']:.3g}")
    print(f"Endpoint check: {summary['endpoint_falsification']['outcome']} through {summary['endpoint_falsification']['period'][1]}")
    print(f"Wrote {json_path} and {svg_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
