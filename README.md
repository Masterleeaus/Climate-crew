# 🌍 Climate Crew

## Evidence-driven multi-agent climate research and discovery

Climate Crew is an open climate-research system built around teams of specialised AI agents that investigate questions, gather observational and published evidence, challenge competing explanations, reproduce results, quantify uncertainty, and advance only well-supported findings toward human validation.

> **Mission:** build an auditable research engine that helps people investigate climate problems faster without confusing model agreement with scientific evidence.

Climate Crew evolves the existing ClimateX/Convolve multi-agent platform rather than replacing it. The project retains its deep-research engine, domain agents, RAG, memory, message bus, debate, simulations, evaluation framework, climate-data integrations, FastAPI backend and React/TypeScript interface, while reorganising them around rigorous scientific research.

---

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

The durable unit of work is a **Research Project**, not a chat answer. Projects preserve hypotheses, evidence, methods, datasets, assumptions, contradictions, replications, uncertainty and research history.

---

## 🧠 Core principles

### Evidence before consensus
Multiple agents agreeing does not make a claim true. Climate Crew tracks the evidence supporting a claim and the independence of that evidence.

### Memory is not evidence
Agent memory helps researchers work efficiently. Scientific claims require attributable evidence, observations, datasets, methods or reproducible calculations.

### Contradictions are first-class research objects
Conflicting evidence is preserved and investigated rather than silently averaged away during synthesis.

### Findings must survive challenge
Important findings should face criticism, attempted falsification, replication and uncertainty analysis before becoming discovery candidates.

### Provenance must survive the pipeline
Research outputs should remain traceable to their sources, transformations, models and methods.

### Humans remain part of validation
Climate Crew can generate and assess discovery candidates. It does not declare scientific truth merely because an agent or model says so.

---

## 👥 The Crew

Climate Crew organises existing and future agents into scientific roles.

### Research leadership
- **Research Director** — owns the research mission and decomposition.
- **Strategic Planner** — turns questions into investigation plans.
- **Research Coordinator** — routes work and manages dependencies.

### Climate and Earth-system specialists
Existing Climate Crew capabilities provide foundations for specialists covering:
- climate anomalies
- atmospheric and air-quality systems
- carbon emissions
- oceans
- biodiversity and ecology
- deforestation
- wildfire
- flood and disaster systems
- geospatial and satellite intelligence
- climate finance, ESG and regulatory risk

The architecture is designed to expand into environmental chemistry, cryosphere science, energy systems, materials research and other climate-relevant disciplines.

### Research specialists
- Literature Researcher
- Dataset Researcher
- Observational Data Researcher
- Modelling Agent
- Statistical Analyst
- Experimental Designer
- Novelty / Prior-Art Researcher

### Scientific challenge team
- Critic
- Sceptic / Red-Team Researcher
- Falsification Agent
- Replication Agent
- Uncertainty Analyst
- Evidence Auditor
- Methodology Reviewer

### Synthesis and discovery
- Research Synthesizer
- Scientific Writer
- Discovery Assessor

Existing advocate, critic, judge, deep-research and thought-tree components are being hardened into this research workflow rather than duplicated.

---

## 🕸️ Evidence Graph

Climate Crew is moving from answer-centric research toward an explicit evidence graph.

Canonical research concepts include:

```text
ResearchProject
ResearchQuestion
Hypothesis
Claim
Evidence
Source
Dataset
Observation
Method
Experiment
Model
Assumption
Contradiction
Replication
Uncertainty
Finding
DiscoveryCandidate
```

Example relationships:

```text
Evidence ──SUPPORTS──────▶ Claim
Evidence ──CONTRADICTS───▶ Claim
Claim ─────DERIVED_FROM──▶ Dataset
Claim ─────DEPENDS_ON────▶ Assumption
Claim ─────TESTED_BY─────▶ Experiment
Claim ─────CHALLENGED_BY─▶ Critique
Claim ─────REPLICATED_BY─▶ Replication
```

Evidence provenance should distinguish observations from derived, modelled, simulated, estimated and synthetic information so fallback or demonstration data cannot silently become scientific evidence.

---

## 🤖 Existing research engine

Climate Crew already contains a substantial multi-agent foundation, including:

```text
src/agents/deep_research/
├── orchestrator.py
├── strategic_planner.py
├── query_enricher.py
├── search_agent.py
├── synthesizer.py
├── thought_tree.py
├── router.py
└── debate/
    ├── advocate_agent.py
    ├── critic_agent.py
    └── judge_agent.py
```

The upgrade strategy is **convergence, not replacement**: existing implementations remain canonical where they already provide the required capability. New code should fill genuine scientific-method gaps rather than create parallel agent frameworks.

---

## 🌐 Climate and observational data

The current platform includes integrations or tooling for sources such as:

- NASA FIRMS
- Copernicus climate services
- NOAA weather and ocean data
- OpenAQ
- Climate TRACE
- GBIF biodiversity data
- Global Forest Watch
- USGS earthquake data
- disaster alerts
- satellite imagery
- market and climate-finance information
- news and web research

Climate Crew combines these observational sources with literature, documents, datasets, modelling and agent reasoning. Availability depends on configured credentials and individual upstream services.

---

## 🧩 Existing platform capabilities retained

The transformation deliberately preserves and hardens useful infrastructure already present in the repository:

- specialised multi-agent architecture
- Deep Research orchestration
- advocate / critic / judge debate
- Thought Tree exploration
- agent-to-agent message bus
- negotiation protocols
- working, episodic and semantic memory
- shared memory and consolidation
- RAG and Qdrant retrieval
- dynamic routing and tool loading
- climate and geospatial integrations
- simulation infrastructure
- evaluation and ablation tooling
- execution tracing
- FastAPI APIs
- React + TypeScript research interface

---

## 🧪 Evaluation

Climate Crew aims to test whether research architecture actually improves outcomes rather than assuming that more agents are automatically better.

The repository already contains evaluation infrastructure for areas including retrieval, synthesis, debate, memory, coordination, efficiency, thought-tree behaviour and calibrated judging. As the upgrade progresses, these evaluations will be wired directly into research execution.

Important questions include:

- Does independent investigation improve claim quality?
- Does debate reduce unsupported conclusions?
- Does replication catch reasoning or data errors?
- Does source-independence analysis prevent false consensus?
- Does uncertainty analysis improve calibration?
- When does adding agents increase redundancy rather than knowledge?

---

## 🔎 Discovery lifecycle

Climate Crew distinguishes research progress from validated discovery:

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

A **Discovery Candidate** is not automatically a scientific discovery. External validation may require expert review, laboratory or field work, independent datasets, peer review or other domain-appropriate verification.

---

## 🌎 Distributed Climate Discovery

The longer-term architecture allows bounded research work to be distributed across many participating machines and agents.

Rather than asking thousands of systems to independently produce complete answers, Climate Crew can distribute specific research units such as:

- search for evidence contradicting hypothesis X
- reproduce calculation Y
- test parameter region Z
- analyse a specified dataset
- run a sensitivity analysis
- compare competing models
- search literature or prior art

Returned results feed the same provenance-aware evidence system and remain subject to validation gates.

This creates a path from **Climate Crew as the research brain** to a larger distributed climate-discovery network.

---

## 🏗️ Technology stack

| Layer | Current foundation |
|---|---|
| Backend | Python, FastAPI, Pydantic |
| Agent orchestration | LangChain / LangGraph and project-native orchestration |
| Retrieval | Qdrant-based RAG |
| Frontend | React, TypeScript, Vite |
| Geospatial | Mapbox, Leaflet, satellite/geospatial integrations |
| Research data | Climate, Earth-observation, biodiversity, emissions, disaster and web sources |
| Evaluation | Project-native evaluation, tracing, judges and ablation tooling |

Model providers and individual data integrations are configurable and should not be treated as permanent architectural dependencies.

---

## ⚡ Development setup

### Clone

```bash
git clone https://github.com/Masterleeaus/Climate-crew.git
cd Climate-crew
```

### Backend

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

FastAPI development documentation is normally available at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite development interface is normally available at `http://localhost:5173`.

Configuration and credentials required by external models/data providers should be supplied through the project's environment configuration rather than committed to source control.

---

## 🚧 Current status

Climate Crew is undergoing an architectural migration from the original ClimateX / Convolve climate-intelligence platform into an evidence-driven climate research system.

**Already present:** multi-agent orchestration, specialised climate agents, Deep Research, debate, RAG, memory, climate-data integrations, simulations, evaluation tooling, FastAPI and the React/TypeScript application.

**Being added/hardened:** durable Research Projects, canonical research objects, evidence provenance, evidence independence, contradictions, falsification, replication, uncertainty, discovery gates and research-first user experiences.

The repository may therefore still contain legacy ClimateX, PRAKRITI and Convolve terminology while migration work is underway. Those names describe historical implementation layers, not the target product identity.

---

## 📐 Canonical architecture

The approved architecture specification lives at:

`docs/superpowers/specs/2026-09-27-climate-crew-research-architecture-design.md`

New architectural work should converge on that specification and reuse existing implementations wherever practical.

---

## Climate Crew

**Investigate independently. Challenge aggressively. Preserve the evidence. Discover carefully.**
