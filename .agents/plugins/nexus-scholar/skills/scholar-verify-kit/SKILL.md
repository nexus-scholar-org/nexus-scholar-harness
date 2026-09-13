---
name: scholar-verify-kit
description: Instructions for using the scholar-verify-kit Python API and CLI to verify corpus trustworthiness — retraction status (OpenAlex/Crossref), open-science DAS/CAS artifact scanning, conflict-of-interest audit aggregation, and deterministic QUADAS-2/PROBAST risk-of-bias scoring.
---

# `scholar-verify-kit` Skill Instructions

You are the post-screening trust-verification specialist of the Nexus Scholar Suite. After a corpus is screened and extracted, your role is to certify that the evidence base feeding a synthesis is safe to quote: no retracted records, reproducible data/code where claimed, conflicts of interest surfaced, and reporting/verifiability risk scored per study.

## Core Capabilities

1. **Retraction & publication-status check** (OpenAlex `is_retracted`/`last_status_in_oa` via DOI/arXiv fallbacks + Crossref `update-to` event types).
2. **Open-science artifact scan** (DAS/CAS): deterministic regex baseline over extracted fulltext, classifying each study `public+link` / `request-only` / `statement-only` / `explicitly-unavailable` / `not-stated`.
3. **Conflict-of-interest audit aggregator**: normalizes per-chunk analyst COI classifications, validates coverage vs the theme manifest, applies a documented deterministic relabel for `no-statement` drift.
4. **Risk-of-bias scorer**: deterministic, metadata-driven adaptation of QUADAS-2/PROBAST domains (D1 dataset selection, D2 metric reporting, D3 ground-truth labeling, D4 runtime/efficiency claims). Overall = worst applicable domain.
5. **Trust-weighted consensus**: hermetic join of a Consensus Cartographer `synthesis/consensus.json` with the four Phase-4 outputs, annotating each cluster with per-study RoB/COI/retraction/open-science context, cluster aggregates, and a deterministic trust level (`BLOCKED` → `UNVERIFIED` → `WEAK` → `ADEQUATE` → `STRONG`) → `phase4/trust_consensus.{json,md}`.

---

## CLI Usage

```bash
uv run scholar-verify retraction --workspace workspaces/<project-slug>        # network (OpenAlex + Crossref); needs literature/included.json
uv run scholar-verify retraction --workspace <ws> --dry-run                  # validate plumbing only
uv run scholar-verify open-science --workspace workspaces/<project-slug>      # needs literature/extraction/merged/records.json + extracted/*.md
uv run scholar-verify coi --workspace workspaces/<project-slug>               # needs phase4/_manifest.json + phase4/_agent_results/coi_chunk_*.json
uv run scholar-verify risk-of-bias --workspace workspaces/<project-slug>      # needs records.json + phase4/_manifest.json
uv run scholar-verify all --workspace workspaces/<project-slug> --skip-retraction   # all 4 streams, offline
uv run scholar-verify trust-context --workspace workspaces/<project-slug>  # annotate synthesis/consensus.json with Phase-4 context (hermetic)
uv run scholar-verify trust-context --workspace workspaces/<project-slug> --rq-id RQ1  # scope to clusters whose claims belong to RQ1 (writes trust_consensus_RQ1.json/.md)
uv run scholar-verify verbatim-claims \
  --claims workspaces/<project-slug>/synthesis/claims.json \
  --extracted workspaces/<project-slug>/extracted/ \
  --output workspaces/<project-slug>/phase4/verbatim_claims.json    # verbatim quote verification (threshold 0.90)
```

Notes:
- **`all` ≠ all streams**: it runs the four core streams (retraction / open-science / coi /
  risk-of-bias) only — `trust-context` and `verbatim-claims` are separate commands.
- **`trust-context` is the only stream with a console action**; every stream is otherwise
  CLI-only (the MCP server exposes nothing but `verbatim-claims` as `nexus_verify_claims`).
- Outputs carry an envelope `{run_metadata, summary, results}`; files are
  `<ws>/phase4/{stream}.json` + `.md`.
- (2026-09-13) Fixed: the CLI crashed on Python 3.14 with
  `NameError: name 'Optional' is not defined` (`cli.py` used `Optional[Path]` without the
  `typing.Optional` import); all subcommands now resolve.

Outputs: `<ws>/phase4/{retraction_status_check,open_science_regex_baseline,coi_audit,risk_of_bias}.json|.md`.

## Python API

All streams are pure functions over their inputs — callable directly, no network required except `RetractionChecker`:

```python
from scholar_verify import coi, open_science, risk_of_bias, retraction

records  = json.loads((ws / "literature/extraction/merged/records.json").read_text())
manifest = json.loads((ws / "phase4/_manifest.json").read_text())

out = risk_of_bias.run(records, manifest)
md_ref = risk_of_bias.render_report(out)

out = open_science.run(records, ws / "extracted")
out = coi.run(manifest, coi.load_chunks(ws / "phase4/_agent_results"))

checker = retraction.RetractionChecker(sleep_s=0.2)
out = checker.check(records, included)          # hits OpenAlex + Crossref (rate-limited)
```

## Data contracts

- `records.json`: canonical merged extraction records with `workspace_id`; RoB reads `record["segmentation"][{dataset,metrics}]` and `record["edge"]`.
- `phase4/_manifest.json`: `[{workspace_id, title, year}]` — the audited corpus roster both `coi` and `risk-of-bias` validate against.
- `_agent_results/coi_chunk_*.json`: raw analyst COI entries; accepted schemas are flat (`coi_label`/`funding_statement`/`industry_entities`) and v2 (`study_id`/`coi_verbatim`/`affiliation_role`). `coi` raises if any duplicate/missing/extra id.
- Constant label vocabularies (import for downstream use): `open_science.DAS_CAS_LABELS`, `coi.LABELS`, `coi.ENTITY_KINDS`, `risk_of_bias.DOMAIN_NAMES`.

## Workflow notes

- Run in this order after screening/extraction: `open-science` → `coi` → `risk-of-bias` (offline), then `retraction` (online).
- Deterministic: same inputs → identical JSON, always. Only `retraction` adds runtime variance (live API state).
- The kit's schemas exactly match the legacy Phase-4 outputs on `uav-cv-precision-agriculture`; verified by parity smoke test (identical counts for all summaries).
- LOW/library-documented caveats: OpenAlex `is_retracted` is a metadata snapshot, not publisher live status; Crossref `correction` events are low-severity errata unless `type` is `retraction`/`expression-of-concern`.
- Do not re-implement these checks in harness code; call `scholar_verify` APIs / the `scholar-verify` CLI instead.

## Trust-weighted consensus (`scholar-verify trust-context`)

Joints `synthesis/consensus.json` against the four Phase-4 outputs (`risk_of_bias.json`, `coi_audit.json`, `retraction_status_check.json`, `open_science_regex_baseline.json`), all present under `phase4/` by default. Pure function `trust_context.annotate(consensus, phase4)`; outputs `phase4/trust_consensus.{json,md}`.

Deterministic trust levels (worst applies, per cluster):
- `BLOCKED` — any supporting study is retraction-flagged (`flagged`).
- `UNVERIFIED` — zero supporting studies found in Phase-4 (`coverage == 0`).
- `WEAK` — coverage < 50%, any `overall_risk == "H"`, or any industry-`funding` entity.
- `STRONG` — coverage ≥ 50%, no `overall_risk in ("?", None)`, no industry ties, and ≥ 1 study with DAS/CAS `public+link`.
- `ADEQUATE` — everything else (covered but with `?` ratings / mixed signals).

Per-study details stay in the JSON (`trust.studies`); cluster aggregates live in `trust.aggregates`. Only `retraction` introduces runtime variance; `trust-context` itself is hermetic and deterministic.

## Verbatim claim verification (`verbatim-claims` / MCP `nexus_verify_claims`)

Wraps `VerbatimClaimVerifier(threshold=0.90)` — token n-gram + char-window matching of each
claim's `evidence_quote` against the extracted markdown. Expects input claims with
`claim_id`/`workspace_id`/`study_id`/`evidence_quote`.

- ⚠ **Schema mismatch with scholar-rag `claims.json`**: `SynthesisClaim` emits
  `claim_text`/`citation_tokens` (no `evidence_quote`), so every RAG claim fails
  `MISSING_QUOTE`. Only aggregate `metrics` are returned — per-claim verdicts are discarded
  by the MCP wrapper. Do not use `nexus_verify_claims` on RAG claim output without
  constructing `evidence_quote` first.
- Internals: RAG entailment (embedding cosine) and verbatim verification (quote matching)
  are unrelated concepts sharing the word "verify".
- Other tooling facts: batch verification is self-rate-limiting (sleeps `sleep_s` per
  record — 94 studies ≈ +19 s); only retraction hits the network (OpenAlex `is_retracted`,
  Crossref update events, arXiv `10.48550` short-circuits to DataCite); 3 exponential
  retries, HTTP misses come back clean as `{"_status": 404|400|422}`. The kit is
  standalone (typer/rich/requests only).

### RQ-scoped reports

Per-RQ claim pools (`synthesis/claims_rq<N>.json`) are auto-loaded to attribute each cluster's claims to their originating RQ(s) — exact `(study_id, claim_text)` match against the claim pools. Every annotated cluster then carries `rq_ids` (all matching RQs; `rq_id` when unanimous). `--rq-id RQ1` scopes the report to clusters whose claims belong to that RQ (cross-RQ clusters are co-members of each RQ's report) and writes `phase4/trust_consensus_RQ1.{json,md}`; clusters with no RQ attribution fall back to the report-level codes parsed from `consensus["rq_id"]`. Provenance is chainable: claim pool → cluster → trust report, all hermetic.