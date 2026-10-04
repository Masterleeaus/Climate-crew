# Climate evidence reasoning benchmark

This benchmark contains 60 **synthetic, controlled evidence packets**: 15 each labelled supports, contradicts, mixed, and insufficient. The scenarios test whether a system reads the supplied trend estimate, retains contradictions, cites relevant evidence IDs, and states a limitation. They are not climate observations and do not measure real-world climate knowledge.

`runner.py` accepts two callables and compares their predictions on the same cases: Climate Crew and a single-LLM baseline. It reports relationship accuracy with Wilson 95% intervals, evidence-ID precision/recall/F1, nonempty caveat rate, Brier score for correctness confidence, and a paired bootstrap 95% interval for the accuracy difference. The JSON dataset keeps ground truth separate from each model's prompt payload.

## Offline tests

The CI tests run mocked adapters across all 60 cases. They verify dataset validation, ground-truth isolation, metric calculation, paired confidence intervals, and deterministic output without network or API keys. Their scores are harness checks only; they are not model-performance results.

```bash
python -m pip install -r requirements-science.txt
pytest -q tests/science
```

## Optional live comparison

The real adapters use the repository's `DeepResearchOrchestrator` (Google/Gemini, with optional search integrations configured by the app) and one OpenAI chat completion. This can make many provider requests: the crew orchestrator runs several research stages per case. Start with a small pilot and inspect usage before running all 60.

```bash
export GOOGLE_API_KEY=...
export OPENAI_API_KEY=...
python -m eval.science_quality.runner \
  --crew-adapter eval.science_quality.adapters:deep_research_crew \
  --baseline-adapter eval.science_quality.adapters:single_llm_baseline \
  --limit 5 --output /tmp/climate-crew-eval.json
```

For the full benchmark, omit `--limit 5`. Save and publish the resulting JSON only after a real provider run, including the exact commit, model IDs, provider configuration, date, and cost. No comparative model-performance result is claimed by the repository's offline CI.
