# Climate Crew

> Climate Crew brings specialist environmental agents, data adapters, and multi-stage research into one exploration workspace.

Researchers can investigate a question, challenge candidate findings, and assemble reports with extracted source links through a FastAPI backend and React interface. The platform is built for climate and engineering teams that need a structured path beyond a single chat response, with scenario artifacts and staged outputs that can guide the next round of analysis.

<p align="center">
  <img src="docs/images/B97B6D0D-BF7B-4C95-B84A-B75670FB988E.png" alt="Climate Crew — evidence-driven multi-agent climate research and discovery" width="100%" />
</p>

## Why Climate Crew is distinctive

The core research path is an explicit sequence: query enrichment, strategic planning, Monte Carlo tree search (MCTS) exploration, advocate/critic/judge debate, and synthesis. That separation makes it easier to inspect where a result came from, swap a specialist, and test a stage independently.

| Capability | Implementation evidence |
|---|---|
| Multi-stage research orchestration | `src/agents/deep_research/orchestrator.py` implements enrichment, planning, MCTS exploration, adversarial debate, synthesis, and optional routing/memory hooks. |
| Domain agent/API surface | `src/api/agents.py` exposes domain-agent discovery, metadata, and chat routes for air quality, wildfire, floods, biodiversity, deforestation, climate anomalies, emissions, earthquakes, oceans, and satellite fusion. |
| Environmental data integration | `src/api/data.py` and `src/data_sources/` provide the data-source adapter surface used by climate and research workflows. |
| Scenario exploration and visual artifacts | `src/agents/climate_time_machine/` generates best/worst/most-likely LLM scenarios, domain reports, image sequences, and GIF artifacts for a supplied event. |
| Evaluation and browser experience | `eval/` and `test/test_eval.py` provide a scoped offline harness; `main.py` composes the FastAPI app and `frontend/src/` contains the Vite/React client. |

<p align="center">
  <img src="docs/images/1C6C37B3-7DA3-4F08-820E-3341C0CA952F.png" alt="Climate Crew platform architecture" width="100%" />
</p>

> **Research principle:** agreement is not evidence. The platform makes debate and synthesis visible so researchers can decide what deserves further scrutiny.

**Evidence boundary:** the current codebase demonstrates real multi-stage orchestration, specialist routing, data adapters, report synthesis, and scenario visualization. Persistent `ResearchProject`/evidence-graph storage and independent replication remain next-stage architecture described later in this README. The deep-research report currently returns generated content plus regex-extracted source links. If every debate verdict rejects a candidate, the orchestrator currently falls back to unverified candidates before synthesis; the Time Machine produces LLM-generated scenarios and visual artifacts rather than numerical climate forecasts.

---

## 🏗️ Technology

| Layer | Technology direction |
|---|---|
| Backend | Python, FastAPI, Pydantic |
| Agent orchestration | Graph and project-native multi-agent orchestration |
| Retrieval | Vector and provenance-aware research retrieval |
| Frontend | React, TypeScript, Vite |
| Geospatial | Interactive Earth observation and mapping |
| Research data | Climate, environmental, scientific and Earth-observation sources |
| Models | Configurable cloud and local model providers |
| Evaluation | Research tracing, judging, replication and ablation |

Individual model providers and data services are integrations rather than permanent architectural dependencies.

## Implemented API surface and code map

The FastAPI composition root is `main.py`. It mounts the following implemented router families:

| Surface | Entry point | Representative tests / evidence |
|---|---|---|
| Agent discovery and specialist chat | `src/api/agents.py` | `test/test_agents.py`, `test/test_new_agents.py` |
| Deep research and adversarial debate | `src/agents/deep_research/` | `test/test_deep_research.py`, `test/test_deep_research_endpoint.py` |
| Retail audit and causal-analysis experiments | `src/agents/retail_analytics/` | `test/test_retail_analytics.py`, `test/test_retail_endpoint.py` |
| Climate time-machine simulation | `src/agents/climate_time_machine/` | `test/test_climate_simulator.py`, `test/test_simulator.py` |
| Climate data-source adapters | `src/api/data.py`, `src/data_sources/` | `test/test_data_sources.py` |
| Climate finance, disaster, news and media routes | `src/api/climate_finance.py`, `src/api/disaster_management.py`, `src/api/news.py`, `src/api/media.py` | focused tests under `test/` |
| Evaluation and tracing | `eval/` | `test/test_eval.py`, `test/test_agent_tracing.py` |
| Browser client | `frontend/src/` | Vite/React application; build separately from the API |

The API exposes `/health` and `/docs` locally. The repository contains a broad mixture of unit, integration, demo and provider-backed tests; the presence of a test file does not mean every external integration is available offline or that a scientific claim has been validated.

### Verification boundary

The repository demonstrates real orchestration, routing, retrieval, memory, simulation and evaluation code. It does not provide a single reproducible benchmark proving that the complete multi-agent workflow is production-ready, scientifically valid, or reliable across all providers. Run the narrowest relevant test and review its credentials/network requirements before interpreting a result.

### Reproducible offline baseline path

The committed `eval/data/benchmark.json` contains three labelled climate queries. The offline baseline uses `EvaluationConfig.from_preset("baseline")`, disables the LLM judge, and runs through `test/test_eval.py` without provider credentials or network access:

```bash
pytest test/test_eval.py -k offline_baseline
```

This verifies dataset loading, baseline configuration, mock-runner execution and report plumbing. `eval/runner.py` currently marks `_run_system` as a mock integration, so this path is harness evidence—not a model benchmark, scientific result, or claim about external-provider quality.

---

## ⚡ Development setup

```bash
git clone https://github.com/Masterleeaus/Climate-crew.git
cd Climate-crew
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

On Windows PowerShell, activate the environment with `venv\Scripts\Activate.ps1`.

Frontend:

```bash
cd frontend
npm install
npm run dev
```

FastAPI development docs are normally available at `http://localhost:8000/docs`; Vite normally runs at `http://localhost:5173`.

## 🧪 Tests

The repository includes Python test and demo scripts under `test/`. After installing the pinned dependencies, run an appropriate targeted test, for example:

```bash
pytest test/test_agents.py
```

Review each test's external-service requirements first; provider and data-source tests may need credentials or network access. A successful test run does not by itself validate scientific claims or external datasets.

Credentials required by external models or data providers should be supplied through environment configuration rather than committed to source control.

---

## Architecture direction

The following sections describe the broader research architecture Climate Crew is designed to grow toward. They are intentionally separated from the implemented code map and quickstart above: treat them as design direction, not proof that persistent evidence-graph storage, numerical climate modelling, independent replication, or a distributed research network are already complete.

## 🔬 Research lifecycle

```text
Research Question
      ↓
Research Project
      ↓
Problem Decomposition
      ↓
Competing Hypotheses
      ↓
Independent Investigation
      ↓
Evidence Collection + Provenance
      ↓
Cross-Agent Challenge
      ↓
Falsification Attempts
      ↓
Replication
      ↓
Uncertainty Analysis
      ↓
Scientific Synthesis
      ↓
Finding
      ↓
Novelty / Prior-Art Review
      ↓
Discovery Candidate
      ↓
Human / Expert Validation
```

The intended durable unit of work is a **Research Project**, not a chat answer. The architecture direction describes how a future persisted project model could preserve questions, hypotheses, claims, evidence, sources, datasets, observations, methods, models, assumptions, contradictions, replications, uncertainty and research history.

## Autonomous Lifecycle Example

### From environmental signal to a reviewable discovery candidate

A representative Climate Crew investigation follows the research lifecycle described by this repository:

1. **Frame the question.** A researcher or discovery signal becomes a durable Research Project with scope, objectives, assumptions, and measurable questions.
2. **Decompose and investigate independently.** Specialist roles examine literature, datasets, observations, models, and geospatial context through separate methods and sources.
3. **Preserve the evidence trail.** Claims link to their sources, datasets, transformations, methods, assumptions, uncertainty, and contradictions in the evidence graph.
4. **Try to break the explanation.** Critics and falsification work search for counter-evidence and alternative explanations; replication attempts use meaningfully independent inputs or methods.
5. **Synthesize without hiding uncertainty.** The project records what is observed, inferred, modelled, disputed, or unknown and assembles a finding for human or expert validation.
6. **Promote cautiously.** A discovery candidate carries its evidence, methods, contradiction history, uncertainty, replication, and novelty assessment for external evaluation.

**Evidence boundary:** this is the research workflow the project describes, not a claim that every provider integration or scientific stage has been production-validated. Current code demonstrates the multi-stage orchestrator and report pipeline; persistent project storage and independent replication remain architecture direction.

---

## 🧠 Scientific principles

- **Evidence before consensus** — agent agreement does not make a claim true.
- **Independent investigation** — important questions can be examined through separate agents, methods and data sources before synthesis.
- **Memory is not evidence** — remembered context supports continuity; scientific claims require attributable evidence.
- **Contradictions remain visible** — conflicting evidence is preserved and investigated rather than silently averaged away.
- **Findings must survive challenge** — criticism, red-team analysis, falsification and replication are part of the research process.
- **Provenance survives the pipeline** — outputs remain traceable to sources, transformations, datasets, models, methods and assumptions.
- **Uncertainty stays visible** — observed, inferred, modelled, simulated, estimated, disputed and unknown states remain distinguishable.
- **Humans remain part of validation** — an agent or agent majority cannot declare scientific truth.

---

## 👥 The Crew

Climate Crew organises specialised intelligence into complementary scientific roles.

### Research leadership
**Research Director · Strategic Planner · Research Coordinator**

### Climate & Earth-system specialists
Climate anomalies and attribution, atmosphere and air quality, greenhouse gases and carbon, oceans, biodiversity, ecology, forests, land-use change, wildfire, floods, natural hazards, geospatial and satellite intelligence, water and soil systems, environmental chemistry, cryosphere science, energy systems, climate finance, ESG, regulation and climate-relevant technologies.

### Research specialists
**Literature Researcher · Dataset Researcher · Observational Data Researcher · Modelling Agent · Statistical Analyst · Experimental Designer · Geospatial Researcher · Novelty / Prior-Art Researcher**

### Challenge team
**Critic · Sceptic / Red-Team Researcher · Falsification Agent · Replication Agent · Uncertainty Analyst · Evidence Auditor · Methodology Reviewer**

### Synthesis & discovery
**Research Synthesizer · Scientific Writer · Discovery Assessor**

Agents can form temporary research teams around a problem rather than forcing every investigation through one fixed workflow.

---

## 🕸️ Evidence Graph — Architecture Direction

The intended evidence model represents research as an interconnected system. The current runtime does not persist these entities as a graph; deep-research reports currently return generated content with regex-extracted source links.

```text
ResearchProject   ResearchQuestion   Hypothesis   Claim
Evidence          Source             Dataset      Observation
Method            Experiment         Model        Assumption
Contradiction     Critique           Replication  Uncertainty
Finding           DiscoveryCandidate
```

Relationships can include:

```text
Evidence ──SUPPORTS──────▶ Claim
Evidence ──CONTRADICTS───▶ Claim
Claim ─────DERIVED_FROM──▶ Dataset
Claim ─────DEPENDS_ON────▶ Assumption
Claim ─────TESTED_BY─────▶ Experiment
Claim ─────CHALLENGED_BY─▶ Critique
Claim ─────REPLICATED_BY─▶ Replication
Finding ───SUPPORTED_BY──▶ Evidence
```

Evidence records distinguish observational, experimental, published, derived, modelled, simulated, estimated and synthetic information.

---

## 🌐 Earth Observatory

The Earth Observatory connects research reasoning to live and historical environmental data, including satellite imagery, atmospheric observations, weather and climate records, ocean observations, emissions inventories, air quality, biodiversity, forest and land-use monitoring, wildfire, hydrology, floods, geological hazards, environmental monitoring and regulatory or industrial information.

Geospatial investigations can connect locations, observations, events, datasets and claims through the same evidence architecture.

---

## 🔭 Discovery Scouts

Discovery Scouts search for emerging research opportunities across independent environmental and scientific signals: observations, unexplained trends, literature, patents, regulatory data, industrial information, waste streams and discrepancies between models and observations.

```text
Signals → Pattern → Candidate Problem → Supporting Evidence → Investigation
```

The platform can therefore search for problems worth investigating instead of only waiting for people to define them.

---

## 🧪 Research engine

Capabilities include research-question decomposition, parallel investigation, literature and web research, dataset discovery and analysis, provenance-aware retrieval, geospatial investigation, competing-hypothesis analysis, structured scientific debate, modelling, simulation, statistical analysis, contradiction detection, falsification, replication, uncertainty analysis, synthesis, novelty review and research tracing.

The goal is not to maximise agent count. Climate Crew should select the smallest useful combination of genuinely complementary and independent capabilities for each problem.

<p align="center">
  <img src="docs/images/0ED9B80C-22EA-4698-BC40-08B375937F04.png" alt="Climate Crew research engine, agent team, Earth Observatory and validation architecture" width="100%" />
</p>

---

## ⚖️ Adversarial truth-seeking

Claims can be exposed to adversarial evaluation that searches for contradictory observations, methodological weaknesses, unsupported assumptions, alternative explanations, statistical errors, data leakage, correlated sources, model dependence, irreproducible calculations and prior research that undermines novelty.

Prediction and forecasting mechanisms can record explicit expectations about measurable future outcomes. Their resolution can inform method reliability, but does not replace scientific evidence about the underlying claim.

---

## 🔁 Replication, falsification & uncertainty

Climate Crew separates **producing a result** from **trusting a result**. Significant claims can be reconstructed using different agents, models, datasets, statistical methods, assumptions, searches, calculations and simulations.

Assessment can consider source, dataset, methodological and model independence; measurement and statistical uncertainty; assumption sensitivity; unresolved contradictions; replication history; and missing evidence.

Ten articles derived from one dataset should not automatically count as ten independent confirmations.

---

## 🔎 Discovery lifecycle

```text
Observation
   ↓
Finding
   ↓
Candidate Finding
   ↓
Replicated Finding
   ↓
Novel Finding
   ↓
Discovery Candidate
   ↓
Externally Validated Discovery
```

A **Discovery Candidate** contains the evidence, provenance, methods, contradictions, uncertainty, replication history and novelty assessment required for external evaluation. Validation may require experts, independent datasets, field investigation, laboratory work or peer review.

---

## 🌎 Distributed Climate Discovery Network

Large investigations can be decomposed into bounded research tasks and distributed across agents, machines, institutions or community contributors. Returned work enters the same evidence and provenance system and remains subject to validation gates.

Examples include reproducing calculations, analysing datasets, testing parameter regions, sensitivity analysis, comparing models, searching for contradictory evidence, investigating prior art and examining geographic anomalies.

---

## 🧬 Research memory & integrity

The intended research-memory layer would preserve previous questions, hypotheses, rejected explanations, evidence, contradictions, datasets, methods, model outputs, replication attempts, uncertainty assessments and findings without confusing remembered information with verified evidence.

Research records can preserve source attribution, timestamps, dataset identity, transformations, model and tool involvement, assumptions, agent contributions, critiques, contradictions, replication results and human validation decisions.

Synthetic, fallback, demonstration and simulated information must remain distinguishable from observational evidence throughout the pipeline.

---
## 🌍 Climate Crew

**Investigate independently. Challenge aggressively. Preserve the evidence. Discover carefully.**
