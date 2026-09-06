# Outstanding Tasks & Roadmap Analysis

This document aggregates all the outstanding, "undone" work across the Nexus Scholar repository. I have synthesized this from the `OPEN_SCIENCE_ROADMAP.md`, `ROADMAP_ASSESSMENT_AND_TASK_LIST.md`, and the architectural retrospective.

## 1. Immediate Architectural Debt (The "Fixes")
*Derived from the Phase 1-3 Retrospective. These are critical stability improvements.*

- **[P0] Windows CLI Stability:** Force UTF-8 in `scholar-harness` to prevent Rich console crashes.
- **[P0] PDF Retrieval Resilience:** Add institutional proxy support and publisher URL patterns (IEEE, Elsevier) to `scholar-pdf-kit` to bypass Cloudflare. Add `%PDF` magic-byte validation.
- **[P1] State Syncing:** Add a `scholar-harness sync` command to atomically rebuild `project.json` and `INDEX.md` from filesystem state.
- **[P1] Screener Bias Calibration:** Add a 20-paper pre-flight calibration test and a boolean checklist to `scholar-agent-kit` to prevent wild variations in inclusion rates.
- **[P1] Discovery Integrity:** Enforce strict bidirectional title similarity when hydrating DOIs to prevent PubMed cross-contamination.

## 2. Unfinished Roadmap Tasks (The "Features")
*Derived from the `ROADMAP_ASSESSMENT_AND_TASK_LIST.md` and `OPEN_SCIENCE_ROADMAP.md`.*

### Phase 0: Intent Router
- [ ] **Interactive Inception CLI**: A terminal wizard to conduct the Socratic interview.
- [ ] **Protocol Generator**: A tool to explicitly generate the `protocol.json`.
- [ ] **Playbook Archetypes**: Preset templates for SLRs, Scoping Reviews, and Rapid Assessments.

### Phase 1: Discovery & Harvesting
- [ ] **Citation Snowballing**: Build backward/forward reference traversal directly into `scholar-search-kit`.

### Phase 2: Synthesis & Graphs
- [ ] **Consensus Cartographer**: A tool to automatically group claims into high-consensus vs. active debate.

### Phase 3: Interactive Interfaces
- [ ] **Jupyter Notebook Suite**: Pre-built templates (`00_research_inception.ipynb`, etc.) that researchers can execute cell-by-cell.
- [ ] **Zotero Sync**: Two-way web API integration.
- [ ] **Overleaf / Typst Bridge**: Automated Git-backed export of the final manuscript.

### Phase 4: Trust Layers
- [ ] **Abstracting Phase 4**: We just proved the concepts (Retraction, Open Science, COI, Risk of bias) as raw scripts inside the `uav` workspace. We need to abstract these into an official kit (e.g. `scholar-verify-kit`) so they can be run on *any* workspace.

### Phase 5: Collaboration
- [ ] **Shared Workspaces & No-Code Builder**: The final vision of a UI-driven, multi-user research environment.
