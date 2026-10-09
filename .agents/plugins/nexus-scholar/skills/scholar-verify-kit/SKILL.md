---
name: scholar-verify-kit
description: Instructions for using the scholar-verify-kit Python API and CLI to verify corpus trustworthiness — retraction status (OpenAlex/Crossref), open-science DAS/CAS artifact scanning, conflict-of-interest audit aggregation, and deterministic QUADAS-2/PROBAST risk-of-bias scoring.
---

# `scholar-verify-kit` Skill Instructions

You are the post-screening trust-verification specialist of the Nexus Scholar Suite. After a corpus is screened and extracted, your role is to certify that the evidence base feeding a synthesis is safe to quote: no retracted records, reproducible data/code where claimed, conflicts of interest surfaced, and reporting/verifiability risk scored per study.

> Verified against pinned `scholar-verify-kit` `44a8d63cc0a11694bbcb7a355a53f73c3f93145c` (`plugins.json` `default_rev`) and `docs/kits_surface_matrix.md` verify rows + findings 6/10/11 (resolved bridge, Phase-4 MCP, CLI import fix). See that matrix for the full API↔CLI↔MCP map; this file is the operational subset.

## Routing — choose the surface first

| Task | Use |
| :--- | :--- |
| Workspace run that persists `phase4/*.json\|.md` | CLI `uv run scholar-verify <stream> --workspace <ws>` |
| Hermetic join / import in Python | `scholar_verify` APIs (same functions the CLI calls) |
| Agent front-door (no shell) | MCP `nexus_verify_claims` / `nexus_verify_phase4` / `nexus_critique_methodology` |
| Full map, failure modes, cross-kit contracts | `docs/kits_surface_matrix.md` verify section |

## Core Capabilities

1. **Retraction & publication-status check** (`retraction.RetractionChecker`): OpenAlex `is_retracted`/`last_status_in_oa` (DOI, else arXiv-id/title-year/OpenAlex-id fallback) + Crossref `update-to` event types. Deterministic `flagged = OA is_retracted OR any Crossref update ∈ {retraction, expression-of-concern, correction, addendum, correction-addendum}`; sleeps `sleep_s` (default `0.2`) per record.
2. **Open-science artifact scan** (`open_science.run`): deterministic DAS/CAS regex + repo-host whitelist over extracted fulltext, per-study `public+link` / `request-only` / `statement-only` / `explicitly-unavailable` / `not-stated` (`DAS_CAS_LABELS`). Missing extraction **dropped by default** (`drop_missing=True`); missing ids listed in `run_metadata.missing_extractions`.
3. **Conflict-of-interest audit aggregator** (`coi.run`): normalizes per-chunk analyst entries (flat and v2 schemas), validates coverage vs the manifest, applies the documented deterministic `no-statement` relabel (recorded per row in `adjusted_from`). `coi.load_chunks` reads `coi_chunk_1..8.json` — they must be **contiguous** or it raises `SystemExit`; `run` raises `SystemExit` on any duplicate/missing/extra id.
4. **Risk-of-bias scorer** (`risk_of_bias.run`): deterministic metadata-driven QUADAS-2/PROBAST adaptation (D1 dataset selection, D2 metric reporting, D3 ground-truth labeling, D4 runtime/efficiency claims; names in `DOMAIN_NAMES`). Ratings `L / ? / H` (+ `n/a` for D4 when no edge/runtime claims); **overall = worst applicable domain**. Conservative `?` for self-collected datasets without annotation/benchmark documentation.
5. **Trust-weighted consensus** (`trust_context.annotate`): hermetic join of `synthesis/consensus.json` with the four Phase-4 outputs → `phase4/trust_consensus.{json,md}` (per-study `trust.studies`, cluster `trust.aggregates`, deterministic trust level).

---

## CLI Usage

```bash
uv run scholar-verify retraction --workspace workspaces/<project-slug>        # network (OpenAlex + Crossref); needs literature/included.json
uv run scholar-verify retraction --workspace <ws> --dry-run                  # validate plumbing only
uv run scholar-verify open-science --workspace workspaces/<project-slug>      # needs literature/extraction/merged/records.json + extracted/*.md
uv run scholar-verify coi --workspace workspaces/<project-slug>               # needs phase4/_manifest.json + phase4/_agent_results/coi_chunk_*.json
uv run scholar-verify risk-of-bias --workspace workspaces/<project-slug>      # needs records.json + phase4/_manifest.json
uv run scholar-verify all --workspace workspaces/<project-slug> --skip-retraction   # 4 core streams, offline
uv run scholar-verify trust-context --workspace workspaces/<project-slug>  # annotate synthesis/consensus.json with Phase-4 context (hermetic)
uv run scholar-verify trust-context --workspace workspaces/<project-slug> --rq-id RQ1  # scope to clusters whose claims belong to RQ1 (writes trust_consensus_RQ1.json/.md)
uv run scholar-verify verbatim-claims \
  --claims workspaces/<project-slug>/synthesis/claims.json \
  --extracted workspaces/<project-slug>/extracted/ \
  --output workspaces/<project-slug>/phase4/verbatim_claims.json    # verbatim quote verification (threshold 0.90)
```

Notes:
- **Workspace guard**: every `--workspace` stream (`retraction`/`open-science`/`coi`/`risk-of-bias`/`trust-context`/`all`) requires `protocol.json` **or** `INDEX.md` in `<ws>` (`cli._resolve_workspace`); `verbatim-claims` takes `--claims`/`--extracted` instead and has no workspace guard.
- **`all` ≠ all streams**: CLI `all` runs the four core streams (retraction / open-science / coi / risk-of-bias) only — `trust-context` and `verbatim-claims` are separate commands. MCP `all` additionally attempts `trust-context` but writes `SKIPPED (no synthesis consensus.json)` when no `synthesis/consensus.json` exists — never claim `trust-context` ran without that SKIP note.
- **Envelope**: the four core streams emit `{run_metadata, summary, results}`; files are `<ws>/phase4/{stream}.json` + `.md`.

Outputs: `<ws>/phase4/{retraction_status_check,open_science_regex_baseline,coi_audit,risk_of_bias}.json|.md`.

## Python API

All streams are pure functions over their inputs — callable directly, no network required except `RetractionChecker`:

```python
from scholar_verify import coi, open_science, risk_of_bias, retraction

records  = json.loads((ws / "literature/extraction/merged/records.json").read_text())
manifest = json.loads((ws / "phase4/_manifest.json").read_text())

out = risk_of_bias.run(records, manifest)
md_ref = risk_of_bias.render_report(out)

out = open_science.run(records, ws / "extracted")  # drop_missing=True by default
out = coi.run(manifest, coi.load_chunks(ws / "phase4/_agent_results"))  # 8 contiguous chunks

checker = retraction.RetractionChecker(sleep_s=0.2)
out = checker.check(records, included)          # hits OpenAlex + Crossref (rate-limited)
```

Constant vocabularies (import for downstream use): `open_science.DAS_CAS_LABELS`, `coi.LABELS`, `coi.ENTITY_KINDS`, `risk_of_bias.DOMAIN_NAMES`.

## Data contracts

- `records.json`: canonical merged extraction records with `workspace_id`; RoB reads `record["segmentation"][{dataset,metrics}]` and `record["edge"]`.
- `phase4/_manifest.json`: `[{workspace_id, title, year}]` — the audited corpus roster both `coi` and `risk-of-bias` validate against (`workspace_id` is the join key; a title is not an identity).
- `_agent_results/coi_chunk_*.json`: raw analyst COI entries; accepted schemas are flat (`coi_label`/`funding_statement`/`industry_entities`) and v2 (`study_id`/`coi_verbatim`/`affiliation_role`). `coi` raises `SystemExit` on any duplicate/missing/extra id.
- `trust-context` inputs: `synthesis/consensus.json` + the four `phase4/*.json` (missing streams are treated as absent coverage, not an error); RQ pools `synthesis/claims_rq*.json` when present.

## Workflow notes

- Run in this order after screening/extraction: `open-science` → `coi` → `risk-of-bias` (offline), then `retraction` (online).
- Deterministic: same inputs → identical JSON, always. Only `retraction` adds runtime variance (live API state).
- **Network boundary**: only `retraction` hits the network (OpenAlex + Crossref, `mailto verification@nexus-scholar.example`); everything else is hermetic. `10.48550/*` arXiv DOIs short-circuit Crossref (`{"_datacite": True}` — record not applicable). Transport: 3 retries with exponential backoff, HTTP misses come back clean as `{"_status": 404|400|422}`. The kit is standalone (typer/rich/requests only).
- LOW/library-documented caveats: OpenAlex `is_retracted` is a metadata snapshot, not publisher live status; Crossref `correction` events are low-severity errata unless `type` is `retraction`/`expression-of-concern`.
- Do not re-implement these checks in harness code; call `scholar_verify` APIs / the `scholar-verify` CLI instead. The `phase4/*.json` envelopes are the authoritative trust outputs; MCP wrappers below call the same helpers and write the same files (mirrors, not separate semantics).

## Trust-weighted consensus (`scholar-verify trust-context`)

Joints `synthesis/consensus.json` against the four Phase-4 outputs (`risk_of_bias.json`, `coi_audit.json`, `retraction_status_check.json`, `open_science_regex_baseline.json`), all present under `phase4/` by default. Pure function `trust_context.annotate(consensus, phase4)`; outputs `phase4/trust_consensus.{json,md}`.

Deterministic trust levels (worst applies, per cluster):
- `BLOCKED` — any supporting study is retraction-flagged (`flagged`).
- `UNVERIFIED` — zero supporting studies found in Phase-4 (`coverage == 0`).
- `WEAK` — coverage < 50%, any `overall_risk == "H"`, or any industry-`funding` entity.
- `STRONG` — coverage ≥ 50%, no `overall_risk in ("?", None)`, no industry ties, and ≥ 1 study with DAS/CAS `public+link`.
- `ADEQUATE` — everything else (covered but with `?` ratings / mixed signals).

Per-study details stay in the JSON (`trust.studies`); cluster aggregates live in `trust.aggregates`. Only `retraction` introduces runtime variance; `trust-context` itself is hermetic and deterministic. `_FLAG_REASON_SENSITIVE` is a dead constant — no sensitivity filtering exists; any flag blocks.

## Verbatim claim verification (`verbatim-claims` / MCP `nexus_verify_claims`)

Wraps `VerbatimClaimVerifier(threshold=0.90)` — token n-gram + char-window matching of each claim's `evidence_quote` against the extracted markdown. Expects input claims with `claim_id`/`workspace_id`/`study_id`/`evidence_quote`.

- **Verbatim ≠ entailment.** RAG `entailment_status` (`VERIFIED ≥ 0.85` / `AMBIGUOUS ≥ 0.50` / `UNSUPPORTED`) is embedding-cosine similarity vocabulary — similarity is not entailment and synthesis does not verify it. Verbatim verification is quote matching (`char_window_coverage` + `token_ngram_coverage`, NFKC-normalized, `max_coverage >= threshold`). Never conflate the two.
- **RAG claims bridge** (finding 6, resolved): `nexus_verify_claims` accepts a bare array or `{"claims": [...]}` (`SynthesisClaim` shape), falls back to `claim_text` when `evidence_quote` is absent, and returns per-claim verdicts plus a `failures_by_reason` breakdown (`MISSING_QUOTE` / `SOURCE_TEXT_NOT_FOUND` / `INSUFFICIENT_COVERAGE`). Each verdict surfaces the RAG `entailment_status` as `rag_entailment_status` alongside the verbatim verdict — read both, do not treat either as the other.
- Other tooling facts: batch verification is self-rate-limiting (sleeps `sleep_s` per record — 94 studies ≈ +19 s). The CLI `verbatim-claims` requires a JSON **list** and maps sources by stem / `workspace_id:` frontmatter / `SCI-xxxx` filename.

### RQ-scoped reports

Per-RQ claim pools (`synthesis/claims_rq<N>.json`) are auto-loaded to attribute each cluster's claims to their originating RQ(s) — exact `(study_id, claim_text)` match against the claim pools. Every annotated cluster then carries `rq_ids` (all matching RQs; `rq_id` when unanimous). `--rq-id RQ1` scopes the report to clusters whose claims belong to that RQ (cross-RQ clusters are co-members of each RQ's report) and writes `phase4/trust_consensus_RQ1.{json,md}`; clusters with no RQ attribution fall back to the report-level codes parsed from `consensus["rq_id"]`. Provenance is chainable: claim pool → cluster → trust report, all hermetic.

## MCP front-door (`scholar-agent-kit`)

- `nexus_verify_claims(claims_json_path, extracted_dir_path, threshold=0.90)` — the verbatim bridge above; returns `{status, metrics, failures_by_reason, claims}` with per-claim verdicts.
- `nexus_verify_phase4(workspace_dir, stream="all", sleep_s=0.2, skip_retraction=True, rq_id=None)` — wraps the same thin CLI helpers and module functions, writes `<ws>/phase4/<name>.{json,md}` mirrors of each stream, returns `{status, stream, written}`. `skip_retraction` defaults **`True`** (retraction is network-bound; pass `False` to run it). `trust-context`/`all` skip gracefully when no `synthesis/consensus.json` exists.
- `nexus_critique_methodology(workspace_dir, protocol_path=None, rq_id=None)` — wraps `risk_of_bias.run` and writes `phase4/methodological_critique.md` (domain summary + per-study table); protocol/RQ args scope the narrative context only.

## Limitations (kept, not fixed here)

- `coi` needs the 8 analyst chunk files; without them it refuses (`SystemExit`) rather than inventing coverage. `risk-of-bias` refuses (`SystemExit`) when manifest ids lack records. `open-science` degrades to `missing_extractions` listing. `trust-context` treats absent Phase-4 streams as absent coverage.
- Retraction lookups that do not resolve are `unresolved_lookups` / `{"_status": …}` sentinels, not errors; provider failure is never reported as an empty successful result.
