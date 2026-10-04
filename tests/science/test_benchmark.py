from eval.science_quality.runner import (
    Prediction,
    compare_predictions,
    load_cases,
    run_comparison,
    wilson_interval,
)


def test_benchmark_is_balanced_and_model_prompt_hides_labels():
    cases = load_cases()
    assert len(cases) == 60
    assert {case.ground_truth.relationship for case in cases} == {
        "supports", "contradicts", "mixed", "insufficient"
    }
    assert "ground_truth" not in cases[0].prompt_payload()


def test_mocked_crew_and_single_llm_compare_all_cases_offline():
    cases = load_cases()
    labels = {case.case_id: case.ground_truth.relationship for case in cases}
    evidence = {case.case_id: case.ground_truth.relevant_evidence_ids for case in cases}

    # These are test doubles for the comparison plumbing, not benchmark results.
    def crew_mock(payload):
        return {
            "relationship": labels[payload["case_id"]],
            "evidence_ids": evidence[payload["case_id"]],
            "confidence": 0.9,
            "caveat": "synthetic test response",
        }

    def single_mock(payload):
        return {
            "relationship": "insufficient",
            "evidence_ids": [],
            "confidence": 0.6,
            "caveat": "synthetic test response",
        }

    result, _ = run_comparison(cases, crew_mock, single_mock, bootstrap_replicates=500)
    assert result["case_count"] == 60
    assert result["crew"]["accuracy"] == 1.0
    assert result["single_llm_baseline"]["accuracy"] == 0.25
    interval = result["paired_accuracy_difference_crew_minus_baseline"]["95_ci"]
    assert interval[0] > 0
    assert interval[0] <= interval[1]


def test_prediction_validation_and_wilson_bounds():
    prediction = Prediction.model_validate({
        "relationship": "mixed", "evidence_ids": ["a", "b"], "confidence": 0.72
    })
    assert prediction.confidence == 0.72
    interval = wilson_interval(7, 10)
    assert 0 <= interval[0] < 0.7 < interval[1] <= 1


def test_comparison_requires_one_prediction_per_case():
    cases = load_cases()[:2]
    empty = {}
    try:
        compare_predictions(cases, empty, empty)
    except ValueError as error:
        assert "exactly one prediction" in str(error)
    else:
        raise AssertionError("incomplete model outputs must fail closed")
