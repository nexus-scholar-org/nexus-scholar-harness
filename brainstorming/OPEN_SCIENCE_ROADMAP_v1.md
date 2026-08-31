# Open Science for Everyone: Comprehensive Roadmap
**Version 1.0**  
**Date:** 2026-08-30  
**Principle:** Phased, idempotent, auditable research democratization

---

## Executive Summary

**Vision:** Make cutting-edge research accessible, verifiable, and actionable for:
- 👨‍🎓 **Students** learning a new domain
- 👩‍🏫 **Educators** preparing courses and materials
- 👨‍💼 **Practitioners** solving real-world problems

**Use Cases:**
- Literature reviews (students, researchers)
- Scoping reviews (mapping domains)
- Systematic reviews (PRISMA-compliant evidence synthesis)
- Domain exploration (understanding emerging areas)
- Database analysis (research trend analysis)

**Delivery:** Chat interface + Interactive notebooks + Tool integrations

**Trust Model:** Every finding is traceable to papers with full methodology audit trails

---

## Five-Phase Implementation Plan

### PHASE 0: Intent Router & Methodology Selection (2-3 weeks)

**Goal:** Before searching, clarify what the user actually needs

**Outputs:**
- User intent profile (research goal, scope, rigor level, timeline)
- Recommended methodology (SLR? Scoping review? Quick assessment?)
- Pre-configured project workspace
- Expected deliverables and timeline

**Using:** `methodology-copilot` SKILL (Socratic interview protocol)

**Example Flow:**
```
User: "I want to understand climate tech solutions"
     ↓
[Socratic Interview - 3 questions]
  Q1: "Are you exploring broadly or answering specific questions?"
      → Answer: "Exploring, but want to prioritize scalable solutions"
  Q2: "Academic rigor needed?"
      → Answer: "Yes, for publication"
  Q3: "Timeline?"
      → Answer: "3 months"
     ↓
[Recommendation]
  Methodology: Scoping review → Systematic review
  Timeline: Phase 1 (4 weeks) → Phase 2 (8 weeks)
  Template: PRISMA-compliant SLR protocol
  Expected papers: 150-300
```

---

### PHASE 1: Auditable Research Discovery (3-4 weeks)

**Goal:** Find papers with complete transparency and audit logging

**Features:**
- Multi-database search (OpenAlex, Semantic Scholar, arXiv, PubMed, bioRxiv, Crossref)
- Full audit trail of every search decision
- Progressive refinement workflow (narrow scope interactively)
- PDF extraction and validation
- Deduplication with provenance tracking

**Audit Trail Example:**
```json
{
  "research_id": "climate-tech-2026-08-30",
  "step_number": 1,
  "action": "DISCOVERY_SEARCH",
  "timestamp": "2026-08-30T14:23:00Z",
  "input": {
    "query": "climate technology solutions",
    "databases": ["openalex", "semanticscholar"],
    "filters": {"year_from": 2020, "open_access": true}
  },
  "output": {
    "discovered": 1247,
    "deduplicated": 1089,
    "duplicates_removed": 158
  },
  "reasoning": "Search for scalable approaches post-2020; open access for reproducibility"
}
```

**Using:** `scholar-search-kit` + `workspace-manager` batch logging

---

### PHASE 2: Transparent Synthesis & Knowledge Graphs (4-5 weeks)

**Goal:** Convert papers into understandable insights with source attribution

**Features:**
- Plain-language synthesis (claims linked to specific papers + pages)
- Interactive knowledge graphs (visualize relationships)
- Methodology comparison matrices (see how studies differ)
- Confidence scoring (based on consensus)
- Disagreement flagging (where experts diverge)

**Synthesis Example:**
```
FINDING: Perovskite solar cells show 25%+ efficiency improvements

Sources:
  ✓ Chen et al. 2024 - Nature Energy (30% efficiency, lab)
  ✓ Hoffmann & Lee 2023 - ACS (26% efficiency, field trial)
  ✓ Park et al. 2023 - Science (28% efficiency, lab)

Consensus: HIGH (3/5 recent papers align)
Uncertainty: "Cost scaling and longevity still open questions"
```

**Using:** `scholar-rag-kit` + `scholar-graph-kit`

---

### PHASE 3: Interactive Research Interfaces (4-5 weeks)

**Goal:** Let users explore research through different modalities

**Interfaces:**

**3a: Chat Interface** (conversational Q&A)
```
User: "What's the main blocker for perovskite commercialization?"
Bot: "Stability/durability - 67 papers identify this as top 3 challenge.
      Want to see why? I can show:
      • Technical comparisons across 3 solutions
      • Cost vs timeline tradeoffs
      • Companies working on this
      • Recent breakthroughs"
```

**3b: Jupyter Notebooks** (reproducible analysis)
- Pre-built templates for different research types
- Run cells to reproduce any analysis
- Built-in audit trail
- Export to LaTeX/PDF

**3c: Tool Integrations**
- Zotero/Mendeley (auto-import metadata)
- Overleaf (generate draft sections)
- Notion (database views)
- GitHub (version control on findings)

---

### PHASE 4: Verification & Trust Layers (4-6 weeks)

**Goal:** Build confidence in findings through transparency

**Features:**

**4a: Source Verification**
```
Paper: "Perovskite Solar Cells Achieve 30% Efficiency"
✅ Peer reviewed: Nature Energy (high impact)
✅ Open access: Full text available
✅ Reproducible: Code + data on GitHub
⚠️  Funding: Partially by solar company (potential bias noted)
❌ Independent replication: Not yet
Trustworthiness: 8.5/10
```

**4b: Methodology Rigor Scoring**
- Study design quality (RCT > observational)
- Sample size adequacy
- Reproducibility (code/data available)
- Peer review venue
- Conflict of interest assessment

**4c: Consensus & Disagreement Mapping**
```
WHERE EXPERTS AGREE:
✓ Stability is the critical blocker (80% of literature)

WHERE THEY DISAGREE:
✗ Solution path:
  • 35 papers: Manufacturing scale
  • 32 papers: Materials innovation
  • 25 papers: Hybrid approach

EMERGING MINORITY VIEWS:
! Lead-free perovskites (15% of literature, growing)
```

---

### PHASE 5: Collaboration & Empowerment (5-8 weeks)

**Goal:** Enable teams to research together and publish findings

**Features:**

**5a: Shared Research Workspaces**
```
Workspace: "Climate Tech Review Q3 2026"
├── Members: Alice (Lead), Bob (Reviewer), Carol (Editor)
├── Audit log: All decisions tracked and reversible
├── Sections: Renewable Energy | Storage | Carbon Capture
├── Status: Ready for peer review
└── Export: PRISMA checklist + findings + citations
```

**5b: No-Code Workflow Builder**
- Drag-and-drop research pipeline construction
- Visual node arrangement
- Auto-generate code for export
- Test on sample data before full run

**5c: Domain-Specific Templates**
- Systematic Literature Review (PRISMA-compliant)
- Scoping Review (landscape mapping)
- Rapid Evidence Assessment (48-hour turnaround)
- Meta-research (analyzing research trends)

---

## Why This Works: Idempotent Design

**Key principle:** Every phase is safe to re-run without data loss or corruption

```python
# Example 1: Same search twice = identical results
result1 = search(query="climate tech", year_from=2020)
result2 = search(query="climate tech", year_from=2020)
assert result1 == result2  # Guaranteed

# Example 2: Re-running synthesis produces same insights
synthesis1 = synthesize(papers=papers_set)
synthesis2 = synthesize(papers=papers_set)
assert synthesis1 == synthesis2  # Deterministic
```

**Benefits:**
- ✅ Audit-friendly (re-verify any finding)
- ✅ Collaboration-safe (no conflict overwrites)
- ✅ Publication-ready (reproducible methodology)
- ✅ Version-control friendly (track changes)

---

## Implementation Sequencing

**Must Do First (Blocker for Others):**
1. Phase 0: Intent router
2. Phase 1a: Discovery pipeline
   - Everything depends on consistent audit logging

**Can Parallelize:**
- Phase 1b/1c: PDF extraction (independent)
- Phase 3a/3b: Chat + Notebooks (both use Phase 1-2 output)
- Phase 4a/4b: Verification systems

**Must Wait For:**
- Phase 2: Requires Phase 1 (need papers)
- Phase 3: Requires Phase 2 (interfaces surface content)
- Phase 4: Requires Phase 3 (users verify what they see)
- Phase 5: Requires Phase 4 (confidence → collaboration)

---

## Minimum Viable Product (MVP)

**Scope: Phase 0 + Phase 1 + Phase 2 (8 weeks)**

**Result:** Users can ask a research question and get auditable synthesis

**Interfaces:**
- CLI: `scholar-harness research "climate tech solutions"`
- Jupyter notebook with results
- Audit trail accessible for verification

**Resources:**
- 2-3 engineers
- 1 methodology expert
- 1 QA/testing person

---

## Success Criteria

### Phase 1 Complete
- [ ] Same search run twice produces identical results
- [ ] Audit trail captures >95% of decisions
- [ ] PDF extraction succeeds for ≥85% of open-access papers

### Phase 2 Complete
- [ ] Every claim is attributed to ≥1 paper
- [ ] Users can drill: finding → paper → page number
- [ ] Knowledge graph auto-generates with minimal manual work

### Phase 3 Complete
- [ ] Chat handles ≥80% of common research questions
- [ ] Notebooks reproducible when re-run by different users
- [ ] Integrations with 2+ external tools working

### Phase 4 Complete
- [ ] Bias detection catches ≥80% of known conflicts
- [ ] Consensus mapping identifies >90% of major disagreements
- [ ] Users trust findings enough to cite in publications

### Phase 5 Complete
- [ ] No-code builder usable by non-programmers
- [ ] Shared workspace survives >50 concurrent edits
- [ ] Peer-reviewed papers published using platform

---

## Critical Questions for Refinement

**1. Priority:** Which phase should we build first?
- Phase 0 (Intent clarity)?
- Phase 1 (Discovery)?
- Phase 3 (Chat interface)?

**2. First Use Case:** Optimize for which scenario?
- Student literature reviews (high volume, forgiving)?
- SLR protocols (small volume, strict)?
- Domain exploration (discovery-focused)?

**3. Trust Level:** How strict on verification?
- Minimal (just link papers)?
- Medium (include bias detection)?
- Strict (require author contact)?

**4. Collaboration:** Shared workspaces now or Phase 5?
- Start solo → add collaboration later?
- Build collab from Phase 1 (crowdsource quality)?

**5. Integrations:** Which tools matter most?
- Zotero? Overleaf? Notion? GitHub? Others?

---

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| API rate limits block searches | Smart caching + batch requests + fallback databases |
| Hallucinations in synthesis | Require citations + human review before publishing |
| Scope creep delays delivery | Phase completion gates + user feedback loop |
| Reproducibility gaps | Version control all APIs, databases, algorithms |
| Too hard for non-programmers | No-code interfaces + templates + guided tutorials |

---

## Deliverables by Phase

| Phase | Deliverables | Tools |
|-------|--------------|-------|
| 0 | Intent decoder + templates | methodology-copilot |
| 1 | Search pipeline + audit logs | scholar-search-kit + workspace-manager |
| 2 | Synthesis engine + graphs | scholar-rag-kit + scholar-graph-kit |
| 3 | Chat + notebooks + integrations | MCP server + Jupyter |
| 4 | Verification system + scoring | Custom analysis tools |
| 5 | Workflow builder + shared workspaces | UI/UX + workspace-manager |

---

## Next Steps

**Option 1: Dive into Phase 0**
- Start building intent decoder
- Create interview protocol
- Generate sample project manifests

**Option 2: Spike Phase 1**
- Prototype multi-database search
- Test audit logging at scale
- Validate PDF extraction success rates

**Option 3: Brainstorm First Use Case**
- Pick one research scenario
- Work backwards through all phases
- Validate each phase with real users

**What would be most useful to prototype next?**
