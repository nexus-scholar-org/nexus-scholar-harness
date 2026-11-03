# scholar-verify-kit

Post-screening trust verification for a Nexus Scholar workspace. Given a
screened corpus with canonical extraction records, the kit produces the four
Phase-4 verification streams used to certify that the evidence base feeding a
synthesis is safe to quote:

| Stream | What it verifies | Inputs | Outputs |
|---|---|---|---|
| `retraction` | No study is retracted / subject to expression-of-concern | `literature/extraction/merged/records.json`, `literature/screening/included.json` | `phase4/retraction_status_check.json|md` |
| `open-science` | Data/Code availability (DAS/CAS) regex baseline | `records.json`, `extracted/*.md` | `phase4/open_science_regex_baseline.json|md` |
| `coi` | Conflict-of-interest audit aggregation + deterministic relabel | `phase4/_manifest.json`, `phase4/_agent_results/coi_chunk_*.json` | `phase4/coi_audit.json|md` |
| `risk-of-bias` | Deterministic QUADAS-2/PROBAST metadata scoring (D1–D4) | `records.json`, `phase4/_manifest.json` | `phase4/risk_of_bias.json|md` |

## Install

    python scripts/install_plugins.py        # from the harness repo root; auto-detects tools/scholar-verify-kit

## Use

    uv run scholar-verify retraction --workspace <ws>
    uv run scholar-verify open-science --workspace <ws>
    uv run scholar-verify coi --workspace <ws>
    uv run scholar-verify risk-of-bias --workspace <ws>
    uv run scholar-verify all --workspace <ws>          # skip-retraction to avoid API calls

All outputs land under `<ws>/phase4/`. The `retraction` stream contacts the
OpenAlex and Crossref public APIs (rate-limited, configurable `--sleep`).

## Library API

Every stream is a pure function over its inputs, so tests and orchestration
can call it directly:

    from scholar_verify import coi, open_science, retraction, risk_of_bias

    out = risk_of_bias.run(records, manifest)          # -> dict
    md  = risk_of_bias.render_report(out)              # -> str

    checker = retraction.RetractionChecker()
    out = checker.check(records, included)

## Design notes

- Deterministic by construction: the same inputs always produce the same JSON;
  humidity comes only from the live retraction API lookups.
- The kit extends the same four-output contract the raw Phase-4 scripts wrote;
  existing `phase4/*.json` outputs from `uav-cv-precision-agriculture` are fully
  compatible with the kit's schema.
- DAS/CAS labels, COI labels, and RoB domain ratings are kept as module
  constants (not magic strings) so downstream consumers can import them.