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
- [x] **Abstracting Phase 4**: Retraction, Open Science, COI, and Risk-of-bias were proven as raw scripts inside the `uav` workspace, then abstracted into the `scholar-verify-kit` (in `tools/scholar-verify-kit/`, CLI `uv run scholar-verify ...`), runnable on *any* workspace. Verified by parity smoke test against the original `uav-cv-precision-agriculture/phase4/` outputs.

### Phase 5: Collaboration & Empowerment (The UI Platform)
Phase 5 transitions the toolkit from a CLI engine into a collaborative, UI-driven platform.
- [ ] **Shared Collaborative Workspaces**: Cloud-based environments with role-based access (Lead, Reviewer, Editor) and fully reversible audit trails for team-based screening and synthesis.
- [ ] **No-Code Workflow Builder**: A drag-and-drop visual interface to connect pipeline nodes (e.g., PubMed Search -> Deduplication -> Docling Extractor). Features include pipeline testing on sample papers and auto-generating Python/CLI code for export.
- [ ] **Domain-Specific Playbooks**: 1-click template pipelines for standardized methodologies, including PRISMA Systematic Reviews, Rapid Evidence Assessments (48-hour turnarounds), and Meta-Research Analysis.
