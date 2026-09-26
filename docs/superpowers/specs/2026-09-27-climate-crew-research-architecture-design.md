# Climate Crew Research Architecture

Canonical design for converting the existing ClimateX/Convolve/PRAKRITI codebase into Climate Crew, an evidence-driven multi-agent climate research and discovery system.

## Goal
Preserve and harden the existing platform rather than replace it. Climate Crew conducts persistent, auditable climate research grounded in traceable evidence, independent challenge, uncertainty analysis, replication and explicit validation gates.

## Core principle
Agent agreement is not scientific evidence. Reasoning, memory, evidence, validation and authority remain separate. Multiple agents citing one source are one evidentiary lineage, not independent confirmation.

## Research lifecycle
Research Question -> Scope/Success Criteria -> Hypotheses -> Research Plan -> Independent Investigations -> Evidence Collection -> Source Independence -> Competing Explanations -> Falsification -> Replication -> Uncertainty -> Scientific Review -> Synthesis -> Finding -> Novelty/Prior-Art -> Discovery Candidate -> Human/Expert Validation.

## Architecture
### Research mission
The durable unit is `ResearchProject` rather than a chat answer. It contains the research question, objectives, scope, success criteria, hypotheses, plan, crew assignments, research state, findings, contradictions and validation history.

### Crew
Reuse `BaseAgent`, orchestration, message bus, negotiation, memory, RAG, dynamic routing/tools, thought-tree and debate infrastructure. Organise existing agents into research leadership, scientific/domain specialists, research specialists, scientific challenge roles and synthesis roles. Add roles only when existing capabilities cannot be adapted.

### Evidence
Add a canonical evidence model above RAG and memory: `Claim`, `Evidence`, `Source`, `Dataset`, `Observation`, `Method`, `Experiment`, `Model`, `Assumption`, `Contradiction`, `Replication`, `Uncertainty`, `Finding` and `DiscoveryCandidate`. Relationships include SUPPORTS, CONTRADICTS, DERIVED_FROM, DEPENDS_ON, TESTED_BY, CHALLENGED_BY and REPLICATED_BY.

Every material claim records provenance, source lineage, method, assumptions, uncertainty, counter-evidence, agent provenance and timestamps. Data is typed OBSERVED, DERIVED, MODELLED, SIMULATED, ESTIMATED, SYNTHETIC or UNKNOWN. Placeholder/mock/fallback data can never silently enter scientific evidence.

### Research engine
Evolve the existing `deep_research` subsystem instead of creating a parallel engine. Query enrichment, planning, search, thought tree, debate and synthesis become stages in a persistent `ResearchProject`. The orchestrator writes structured research state/evidence rather than only an answer.

### Memory and RAG
Preserve existing memory and Qdrant/RAG. Memory is not evidence. Retrieved content becomes evidence only after source identity and lineage are recorded.

### Scientific challenge
Initial investigations should be independently committed before peer conclusions are revealed when practical. Track source independence and correlated evidence. Falsification, contradiction search, replication and uncertainty are first-class stages. Consensus is reasoning metadata, not truth.

### Discovery lifecycle
Observation -> Finding -> Candidate Finding -> Replicated Finding -> Novel Finding -> Discovery Candidate -> Externally Validated Discovery. Transitions require explicit criteria/evidence. Novelty requires literature/prior-art checks; external validation remains distinct from internal confidence.

### Evaluation
Preserve the existing evaluation framework and connect it to real executions. Evaluate retrieval, claim coverage, consensus, redundancy, source independence, agent contribution, early convergence, judge stability, failure cascades, replication, uncertainty calibration and end-to-end research quality.

### Data and tools
Preserve validated climate, air-quality, biodiversity, forest, fire, ocean, earthquake, satellite, regulatory, finance, news and web integrations. Every adapter exposes provenance and clearly distinguishes observed/live values from fallback/synthetic data.

### Interface
Evolve the React/TypeScript interface. Canonical concepts: Research, Projects, Crew, Evidence, Experiments, Models, Datasets, Discoveries, Observatory and Library. Preserve useful operational tools beneath the research model.

### Distributed research
Treat distributed compute as a later worker layer, not research authority. Climate Crew creates bounded work units such as parameter searches, replications, contradiction searches, dataset analyses and sensitivity tests. Results enter the same evidence/validation pipeline.

## Identity
Climate Crew is the canonical product name. Remove ClimateX, ClimateX.ai, Convolve MAS and PRAKRITI from active product documentation/user-facing metadata, retaining historical provenance only where necessary.

Recommended repository description: **Evidence-driven multi-agent climate research and discovery system for auditable, reproducible scientific investigation.**

## Migration sequence
1. Identity/documentation convergence.
2. `ResearchProject` and scientific domain model.
3. Evidence/provenance graph.
4. Deep Research conversion.
5. Existing-agent mapping and missing roles.
6. Falsification, replication, uncertainty and methodology review.
7. Evaluation integration.
8. Frontend convergence.
9. Distributed research work units.

No parallel agent framework, RAG system, memory stack, orchestration engine or evaluation framework should be created merely to fit the new architecture.

## Scientific integrity
- Never present synthetic/fallback data as observations.
- Never equate agent consensus with empirical confirmation.
- Preserve contradictory evidence and minority hypotheses.
- Record provenance for material claims.
- Keep uncertainty visible.
- Require replication where applicable.
- Distinguish simulation/inference from measurement.
- Human/expert validation is explicit for externally validated discoveries.

## Testing
Extend existing tests with research-state transitions, provenance completeness, source-lineage deduplication, evidence typing, mock-data exclusion, hypothesis/claim relationships, falsification outcomes, replication status, uncertainty handling and discovery gates. End-to-end tests take a research question through structured evidence and synthesis without requiring discovery promotion.

## Success criteria
Climate Crew can take a climate research question, create a persistent project, assign specialist agents, collect independently traceable evidence, preserve contradictions, perform challenge/replication/uncertainty stages, synthesize findings with provenance, and prevent unsupported findings from being represented as validated discoveries.