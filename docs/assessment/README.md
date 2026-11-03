# Harness and toolkit assessment — 2026-11-03

**Status:** independent, read-only assessment of the harness and all eight vendored
`scholar-*-kit` packages at commit `5deb3a1`. It supersedes earlier assessment material
as the current view; older dated reviews remain history.
`5deb3a1` is `main` at `4bd02c5` plus the inception UX quick-wins commit (`46f4a46`,
now merged), which changes only `inception/grounded.py` and `inception/wizard.py`.
Since the 2026-11-03 merge into one package, a cited `tools/scholar-<kit>-kit/src/<pkg>/…`
path lives at `src/<pkg>/…` and `tools/scholar-<kit>-kit/tests/…` at `tests/kits/<kit>/…`. Nothing was fixed — each
document ends with a prioritized recommendation table.

**Method.** Eleven documents written by nine parallel reviewers, each owning one scope.
Every reviewer read the code directly, treated existing docs (READMEs, `SKILL.md`,
[`kits_surface_matrix.md`](../kits_surface_matrix.md)) as claims to test rather than
evidence, ran the owning test suites, and reproduced defects with offline scripts
(stubbed HTTP/LLM, temp workspaces; no network, no installs, no commits). Each finding
cites `file:line` and is labelled **Reproduced** or **Static**. Lenses: code quality and
architecture, correctness, and research-method fitness (PRISMA 2020, PRISMA-S,
PRISMA-P, Cochrane norms). The orchestrator re-checked one top finding per report
against source (marked ✓ below).

## 1. Scorecard

| Scope | Document | Code & architecture | Correctness | Research method |
| :-- | :-- | :-- | :-- | :-- |
| Harness core (CLI, pipeline, workspace, integrations) | [harness-core.md](harness-core.md) | Weak | Weak | Weak |
| Harness contracts, authority, screening | [harness-contracts-screening.md](harness-contracts-screening.md) | Weak | Weak | Weak |
| Harness inception, recon, console | [harness-inception-recon-console.md](harness-inception-recon-console.md) | Weak | Weak | Weak |
| scholar-search-kit | [kit-search.md](kit-search.md) | Weak | Failing | Failing |
| scholar-pdf-kit | [kit-pdf.md](kit-pdf.md) | Weak | Failing | Weak |
| scholar-rag-kit | [kit-rag.md](kit-rag.md) | Weak | Weak | Failing |
| scholar-protocol-kit | [kit-protocol.md](kit-protocol.md) | Adequate | Weak | Weak |
| scholar-bib-kit | [kit-bib.md](kit-bib.md) | Weak | Failing | Failing |
| scholar-verify-kit | [kit-verify.md](kit-verify.md) | Weak | Failing | Failing |
| scholar-graph-kit | [kit-graph.md](kit-graph.md) | Weak | Weak | Weak |
| scholar-agent-kit (MCP) | [kit-agent.md](kit-agent.md) | Weak | Weak | Failing |

**Test suites at `5deb3a1`:** green for harness targeted suites, search (185), pdf
(195 passed / 8 skipped), protocol (144), verify (63), rag (research-path subset, 92).
**Red:** graph (3 failed of 83), agent (1 failed of 155 — the AGT-07 defect). The
harness `pytest` config (`testpaths = ["tests"]`) does not run kit suites, so these
failures are invisible to the repo's own gate. Across scopes, the green suites mock
exactly the joints where the reproduced defects sit.

## 2. Cross-cutting conclusion

The infrastructure layer (contract models, fingerprints, acquisition/extraction
services, index identity, single-reviewer coverage gates) is often careful. The
**research layer** — the parts whose outputs a reviewer would put in a methods section
or a results table — is not yet defensible, for five recurring reasons:

1. **"Couldn't check" collapses into "pass" or "success".** Retraction lookups that all
   fail report no flagged studies (VER-02); network failure yields a "built" graph
   (GRAPH-01); a failed index still logs `PIPELINE_RUN_COMPLETED SUCCESS` (CORE-08);
   an empty LLM key yields a heuristic screen reported as `SUCCESS` (AGT-16); failed
   PDF parsing writes placeholder text counted as extracted (PDF-08).
2. **Labels name a validated method the code does not implement.** "QUADAS-2/PROBAST"
   is a domain-specific keyword heuristic (VER-04); "entailment" is embedding
   similarity (RAG-01); "verbatim" accepts altered numbers and inserted negations
   (VER-05); "Louvain" is greedy modularity (GRAPH-06); "Fleiss κ = 1.0" with one
   screener (AGT-18); "anchored" concepts need no term match (INC-21);
   "hallucination detector" verifies a wrong-DOI citation (SRCH-10).
3. **Uncertainty is resolved toward EXCLUDE.** LLM MAYBE → EXCLUDE at 0.9 (SRCH-16);
   missing votes count as EXCLUDE (SRCH-17, AGT-18); MAYBE/MAYBE consensus filed as
   excluded (CON-14) — while the opposite error also exists: screener 2 is ignored
   unless an adjudication file exists (CON-10 ✓).
4. **Identity and provenance are not stable.** Record IDs depend on result order and
   are renumbered every run (CORE-06); the DOI bridge can merge two studies (CORE-10);
   bib dedup merges different DOIs by title (BIB-01); RAG attributes claims to the
   workspace, not the study (RAG-03); missing screening provenance is invented as
   `method: LLM` (CON-11).
5. **Search and synthesis are not reportable.** No per-database query string or hit
   count is recorded (SRCH-30, CORE-21); providers silently cap at 100 (SRCH-11);
   queries are silently rewritten or inverted (SRCH-12/13/14); synthesis uses the top
   5 chunks and never lists omitted studies (RAG-07); no model/prompt/temperature is
   recorded (RAG-09).

Two further gaps are structural: the **harness never reaches the PDF files the kit
downloads** (PDF-07 ✓ — it looks for `<slug>.pdf`, the kit writes `DOC-<sha256>.pdf`),
so Stage 5 "extracts" abstracts and reports DONE; and the **MCP front door bypasses
the human-in-the-loop screening handoff** and writes nothing to `audit/journal.jsonl`
(AGT-16, AGT-19).

## 3. Consolidated priority list

Ranked by risk to a published review, then by effort. Effort is the owning report's
estimate. "Repo" names where the fix lands (kit fixes go to
`nexus-scholar-org/scholar-<name>-kit`, then a `plugins.json` `default_rev` bump and
re-vendor, per AGENTS.md).

### P0 — silently wrong review outputs (fix before any real review run)

| # | IDs | Problem | Repo | Effort |
| :-- | :-- | :-- | :-- | :-- |
| 1 | CON-10 ✓, CON-14, CON-11 | Dual screening ignored without adjudication file; MAYBE/MAYBE counted excluded; missing provenance invented as LLM/INCLUDE | harness | S |
| 2 | CON-13, CON-02/03 | Acceptance gate skipped for multi-parent artifacts; approver identity from agent-writable file; one approval publishes all batches | harness | S–M |
| 3 | AGT-16, AGT-18, AGT-19 | MCP screening writes final included/excluded bypassing handoff, wrong PRISMA counts, κ on one screener, no audit rows | agent-kit | M |
| 4 | SRCH-16/17/35 | Screening helpers bias to EXCLUDE | search-kit | S |
| 5 | CORE-06, CORE-10 | Run-order-dependent record IDs; DOI bridge merges studies | harness | M |
| 6 | PDF-07 ✓, PDF-08 | Harness never finds downloaded PDFs; placeholder text counted as extracted | harness + pdf-kit | S |
| 7 | VER-01, VER-02, VER-04 | Retracted study can be `STRONG`; failed lookups read as clean; RoB is a mislabelled heuristic | verify-kit | M |
| 8 | RAG-01..05 | Fake entailment, uncited sentences unchecked, study attribution lost, invented matrix cells, truncated numbers | rag-kit (+ harness for RAG-05) | M–L |
| 9 | SRCH-10, SRCH-11/31 | Wrong-DOI citations "verified"; silent 100-record caps | search-kit | S–M |
| 10 | BIB-01, BIB-03 | False merges; resolver writes the wrong paper into an entry | bib-kit | S |

### P1 — reproducibility, reporting and safety

| # | IDs | Problem | Repo |
| :-- | :-- | :-- | :-- |
| 11 | SRCH-30, CORE-21, SRCH-12/13/14 | Record exact per-database query, hit count, cap/truncation, cache hits; stop silent query rewrites (PRISMA-S) | search-kit + harness |
| 12 | CORE-08, CORE-07, GRAPH-01, PDF-15 | Failed stages must stop the run and log a journal row; non-zero exit codes | harness, graph-kit, pdf-kit |
| 13 | INC-01, AGT-01, CORE-17 | Console runs arbitrary commands unauthenticated (Host header unchecked); MCP paths escape workspace; API keys written to non-ignored files | harness, agent-kit |
| 14 | INC-08, INC-22, INC-09 | Re-inception silently overwrites protocol; wizard injects criteria unseen; failed probes cached forever | harness |
| 15 | PROT-01..03, PROT-08 | Trust-score gate never enforced; compile skips cross-field checks; unknown keys silently dropped from fingerprint | protocol-kit (contract decision needed) |
| 16 | RAG-07, RAG-09 | List studies omitted from synthesis; record model/prompt/temperature | rag-kit |
| 17 | PDF-09, PDF-10, PDF-11/22 | Column-scrambling extractor; Docling never runs; no paper-identity check on download | pdf-kit |
| 18 | AGT-07, GRAPH-02, VER-06 ✓ | Crashing/always-wrong commands (`nexus_protocol_validate` ✓, graph coupling/hybrid, `verbatim-claims` missing `import re`) | agent-, graph-, verify-kit |

### P2 — method completeness

PRISMA-P fields absent from the protocol model (registration, amendments, RoB tool,
synthesis plan, certainty of evidence — PROT report §4); no inter-rater statistic for
real dual screening (CON report §4); PRISMA "reports not retrieved" reasons (PDF-21);
graph centrality must not be used as a quality or re-ranking signal (GRAPH report §4);
the nine 2026-10-09 inception/recon method findings remain open (INC report §4).

## 4. Relation to earlier documents

- [`inception_recon_scientific_review.md`](../architecture/inception_recon_scientific_review.md)
  (2026-10-09): re-verified in the INC report — 8 of 9 findings unchanged, 1 softened
  only in wording. Keep as history; INC report is current.
- [`kits_surface_matrix.md`](../kits_surface_matrix.md) (2026-09-13): several claims
  proven false (retry behaviour, validate parity "RESOLVED", resolver semantics,
  co-citation). Each report's §5 lists them; the matrix needs a regeneration sweep.
- [`test_suite_audit.md`](../architecture/test_suite_audit.md) and
  [`guideline_conformance_and_review_audit_2026-10-21.md`](../architecture/guideline_conformance_and_review_audit_2026-10-21.md):
  different questions (gate cost; guideline conformance). Not superseded line by line,
  but their positive conclusions about protection should be read against §2 above.

## 5. Limits

No live provider, LLM or full Docling/GROBID run; no real workspace pipeline end to
end; prevalence on an actual corpus is unmeasured; the rag index-governance layer
(~9.4k lines), `extraction_producer.py`, `index_acceptance.py`, `doctor.py` and
`skills_portability/` were read only partially. Reproduction scripts live in the
session scratchpad, not the repo. Findings must be rechecked once the cited files change.
