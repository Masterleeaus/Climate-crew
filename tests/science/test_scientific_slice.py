import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from analysis.reproduce_gistemp import DATA, OUTPUT, build_outputs, make_report
from src.science.models import ScientificReport
from src.science.statistics import (
    load_gistemp_annual,
    mann_kendall,
    moving_block_bootstrap_ci,
    sen_slope,
    trend_summary,
)


ROOT = Path(__file__).resolve().parents[2]


def test_trend_statistics_match_hand_calculable_series():
    years = [2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007]
    values = [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    assert sen_slope(years, values) == 1.0
    positive = mann_kendall(years, values)
    negative = mann_kendall(years, list(reversed(values)))
    tied = mann_kendall(years, [2.0] * len(years))
    assert positive["tau_b"] == 1.0
    assert positive["p_value"] < 0.01
    assert negative["tau_b"] == -1.0
    assert negative["p_value"] < 0.01
    assert tied["p_value"] == 1.0


def test_moving_block_bootstrap_is_seeded_and_contains_slope():
    years = list(range(1980, 2000))
    values = [0.04 * (year - 1980) + ((year % 3) - 1) * 0.05 for year in years]
    first = moving_block_bootstrap_ci(years, values, replicates=100, seed=7)
    second = moving_block_bootstrap_ci(years, values, replicates=100, seed=7)
    assert first == second
    assert first[0] < first[1]


def test_report_requires_valid_evidence_and_hypothesis_references():
    # Build a minimal valid graph through the production report builder's schema.
    report, _ = build_outputs(DATA)
    parsed = ScientificReport.model_validate(json.loads(report)["report"])
    assert len(parsed.hypotheses) >= 2
    assert all(test.evidence_ids for test in parsed.falsification_tests)
    assert all(not test.predeclared for test in parsed.falsification_tests)
    invalid = parsed.model_dump(mode="json")
    invalid["falsification_tests"][0]["evidence_ids"] = ["missing"]
    with pytest.raises(ValidationError, match="unknown evidence"):
        ScientificReport.model_validate(invalid)


def test_pinned_gistemp_result_and_endpoint_sensitivity():
    series = load_gistemp_annual(DATA)
    summary = trend_summary(series, bootstrap_replicates=200)
    assert (series.years[0], series.years[-1], len(series.years)) == (1880, 2025, 146)
    assert summary["ols_slope_c_per_decade"] > 0
    assert summary["ols_slope_95_ci_c_per_decade"][0] > 0
    assert summary["mann_kendall"]["p_value"] < 0.001
    assert summary["endpoint_falsification"]["period"] == [1880, 2015]
    assert summary["endpoint_falsification"]["outcome"] == "not_falsified"
    assert summary["endpoint_falsification"]["mann_kendall"]["p_value"] < 0.05


def test_checked_in_json_and_svg_reproduce_exactly():
    json_bytes, svg_bytes = build_outputs()
    assert (OUTPUT / "gistemp_trend_result.json").read_bytes() == json_bytes
    assert (OUTPUT / "gistemp_global_trend.svg").read_bytes() == svg_bytes
