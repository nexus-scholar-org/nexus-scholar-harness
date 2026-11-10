# Phase 1 discovery: UX review and wireframes (2026-11-02)

UX and methodology review of federated discovery and deduplication: the harness
stages `src/scholar_harness/pipeline/discovery.py` and `pipeline/deduplication.py`,
the kit query compiler `tools/scholar-search-kit/src/scholar_search/protocol_adapter.py`,
the `scholar-harness run` command, and the `scholar-search-kit` skill, read against the
[UAV harvest calibration lessons](../../lessons/2026-10-17_uav_harvest_calibration_lessons.md).

Status: **proposal**. Code-reading review by an AI reviewer (Claude); no user testing.
As of 2026-11-10 this review and its wireframes are history. The build source is the final specs in [`final/`](final/): 01 to 08 are FINAL and built (M3c-screens, PR #216, over the M3b-api and M3d-engine routes). Near-twin pair review is not built (M3e-neartwins).
Line references point to the code as of 2026-11-02. Previous phase: [Phase 0 inception](../phase0-inception/README.md).

## Where things are

| Item | Live (private, share from its Share menu) | Source in this folder |
| :-- | :-- | :-- |
| Wireframe canvas, 8 boards + 11 finding notes | https://claude.ai/artifact/SDAcdaGuEtn6zCZAgvUSd7 | [`wireframes/`](wireframes/) (`canvas.json` + one `.dc.html` per board) |

The `.dc.html` files render inside the Design-canvas editor, not as standalone pages.
Figures on the boards (1,343 of 1,344; ~13,100; the 70x precision gap) are taken from
the UAV v0.3 lessons as realistic examples; titles and DOIs are placeholders.

## Boards

| # | File | Shows |
| :-- | :-- | :-- |
| 1 | `Main.dc.html` | Six-step flow (Plan, Recall, Harvest, Report, Dedup, Hand-off) with two gates before any provider call |
| 2 | `Plan.dc.html` | Concepts from the protocol, compiled query, how each database reads it, limits (years, languages, cap) |
| 3 | `Recall.dc.html` | Seeds from inception anchors plus user papers; found or missed, with the reason and a fix |
| 4 | `Harvest.dc.html` | Live per-database progress against reported totals, caps, rate limits, per-query yield |
| 5 | `Report.dc.html` | PRISMA identification per database, completeness and lower bounds, methods text, run-numbered files |
| 6 | `Dedup.dc.html` | Merges per tier, near-twin review, snapshot-before-dedup, a dedup journal event |
| 7 | `States.dc.html` | Failed, empty, cap reached, protocol changed, no contact email, no audit owner |
| 8 | `Handoff.dc.html` | Provider mix, abstract coverage, abstract fill, screener blinding, next command |

## Findings

| # | Finding | Code / evidence | Severity |
| :-- | :-- | :-- | :-- |
| D1 | No query preview: `run` goes from protocol through search, dedup, hydration and screening prep under one spinner | `cli.py:826` | Major |
| D2 | One boolean string sent to every provider; relevance engines do not honour boolean AND | `protocol_adapter.py:64`; lesson 1 | Major |
| D3 | The protocol's expected pool size max becomes the per-query cap; capped counts look complete | `protocol_adapter.py:74`; lesson 12 | Major |
| D4 | Only the first protocol language is sent | `protocol_adapter.py:71` | Moderate |
| D5 | Records per database are observed but not journaled; PRISMA 2020 identification needs them | `discovery.py:505` | Major |
| D6 | Dedup writes no journal event; near-twins missed (0 of 356 merged); representatives mutated in place | `deduplication.py:9`; lessons 15, 52 | Major |
| D7 | Each successful run overwrites both raw files, which hold the same payload | `discovery.py:413`; lesson 25 | Moderate |
| D8 | Recall check (`validate-query --seed`) exists but is not in the flow; inception anchors are ready seeds | skill; lesson 2 | Moderate |
| D9 | Strength: honest SUCCESS / PARTIAL / EMPTY_RESULT / FAILED, fail-closed publication, stale-artifact disclosure | `discovery.py:216` | Keep |
| D10 | Provider precision differs ~70x; no Crossref type filter; no per-query yield during harvest | lessons 44, 46, 49 | Moderate |
| D11 | PubMed off by default; Scopus and Web of Science unsupported; MCP `nexus_discover` hardcodes 4 providers | skill, `models.py` defaults | Moderate |

## Where fixes belong

- **Harness (this repo):** D1 (split `run` into plan / check / run / report), D5 and D6 audit
  fields, D7 run-numbered files, D8 seed wiring, the state messages on board 7.
- **scholar-search-kit (canonical repo, fork + PR):** D2 per-provider translation, D4 languages,
  D6 near-twin pass and copy semantics (backlog K1), D10 Crossref type filter, D3 universe
  probes (backlog K2). Vendored `tools/` changes must land in the kit repo first.
- **Contract v1 gate:** D3 if the cap moves to a new protocol field, and any new audit
  fields the contract types cover.
