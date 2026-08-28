# Missing Lessons: Proposed Additions
**Identified During:** Brainstorming session 2026-08-24
**Status:** Proposed — Pending approval to produce

---

## Proposed Lesson 1: Module 2.6 — Writing a Research Proposal

### The Gap
The course teaches students to read, find, and analyze literature, but never explicitly teaches them how to formally propose new research. Grant writing is often the single most career-defining skill after Year 3 of a PhD.

### Learning Objectives
1. **Apply** the SMART framework to define research objectives.
2. **Structure** a research proposal using standard sections (Background, Objectives, Methodology, Timeline, Budget, Impact).
3. **Write** a compelling "So What?" statement that justifies funding.
4. **Evaluate** a proposal using the reviewers' evaluation criteria.

### Key Concepts
- **The Heilmeier Catechism** (already introduced in Module 2.1) — extended here for grant applications
- **The Logic Model:** Inputs → Activities → Outputs → Outcomes → Impact
- **Timeline design:** Gantt charts for a 3-year research plan
- **Budget justification:** Direct vs. indirect costs, FTE calculations
- **The "Significance" section:** Convincing reviewers the problem is worth solving

### Positioning
Placed in Module 2 (Finding Literature phase) because students must know the literature landscape before they can propose new research that fills a gap.

---

## Proposed Lesson 2: Module 4.5 — Collaborative Research with Git

### The Gap
Modern research is collaborative. Students managing a shared LaTeX paper with 4 co-authors via email attachments (`final_v3_ACTUALLY_FINAL_revised.docx`) is one of the most common and painful problems in academic research.

### Learning Objectives
1. **Explain** the core concepts of version control (commit, branch, merge, conflict).
2. **Apply** Git for managing a shared LaTeX project.
3. **Implement** a simple GitHub-based collaboration workflow (fork, pull request, review).
4. **Avoid** common anti-patterns (binary files in Git, no `.gitignore`).

### Key Concepts
- **Git vs. GitHub:** Local tool vs. hosting platform
- **The Research Repo Structure:** `/paper`, `/data`, `/scripts`, `/figures`
- **The Pull Request as Peer Review:** Using GitHub PRs to get co-author feedback on sections
- **`.gitignore` for LaTeX:** Never commit `.aux`, `.log`, `.synctex.gz` files
- **Overleaf ↔ GitHub sync:** Many researchers already use Overleaf — they can connect it to GitHub for backup and collaboration

### Positioning
Placed in Module 4 (Writing phase) because the need for version control becomes critical at the manuscript stage when co-authors start editing.

---

## Approval Status

| Lesson | Decision |
|:---|:---:|
| 2.6 — Writing a Research Proposal | ✅ Approved & Published |
| 4.5 — Collaborative Research with Git | ✅ Approved & Published |
