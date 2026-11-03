# Phase 4 trust and verification: UX review and wireframes (2026-11-03)

UX and methodology review of post-screening verification in `tools/scholar-verify-kit`
(`retraction.py`, `risk_of_bias.py`, `coi.py`, `open_science.py`, `verbatim.py`,
`trust_context.py`), its `scholar-verify-kit` skill, and how the harness connects to it
(`src/scholar_harness/handoff.py`).

Status: **proposal**. Code-reading review by an AI reviewer (Claude); no user testing.
Line references point to the code as of 2026-11-03. Previous phase: [Phase 3 extraction](../phase3-extraction/README.md).

## Where things are

| Item | Live (private, share from its Share menu) | Source in this folder |
| :-- | :-- | :-- |
| Wireframe canvas, 7 boards + 9 finding notes | https://claude.ai/artifact/HwZ21qTkCaDZrbXLAdAKbY | [`wireframes/`](wireframes/) (`canvas.json` + one `.dc.html` per board) |

Figures continue the Phase 3 worked example (142 included studies, 12 RQ1 claims). Titles,
quotes and company names are placeholders. Boards rendered and checked on 2026-11-03.

## Boards

| # | File | Shows |
| :-- | :-- | :-- |
| 1 | `Main.dc.html` | Five checks and when each runs (retraction at screening and before publishing) |
| 2 | `Retraction.dc.html` | Retracted, concern, correction, clean, unresolved, arXiv-only; each with its own action |
| 3 | `Bias.dc.html` | Tool chosen as a review setting; per-domain hints from the data table; your rating per domain |
| 4 | `Disclosures.dc.html` | Funding and conflicts, data and code availability, verbatim statements, dead-link check |
| 5 | `Claims.dc.html` | Quote found / partly / missing per claim, with support kept in a separate column |
| 6 | `Trust.dc.html` | Per-claim trust level with reasons, sensitivity ("changes if"), visible review rules |
| 7 | `States.dc.html` | No verified data, rules not set, disclosures incomplete, unresolved lookup, new retraction, no claims |

## Findings

| # | Finding | Code / evidence | Severity |
| :-- | :-- | :-- | :-- |
| V1 | Risk-of-bias rules are written for one review: UAV weed benchmark list, segmentation metrics, non-UAV studies rated High | `risk_of_bias.py:23`, `:34`, `:65`; lesson 21 | Major |
| V2 | Labelled QUADAS-2/PROBAST but scores reporting completeness; any "label" mention makes ground truth Low; trust levels still treat it as overall risk | `risk_of_bias.py:30`, `:108`; `trust_context.py:135` | Major |
| V3 | Corrections and addenda count as flags and any flag BLOCKS a claim, although the retraction report calls corrections low-severity; the severity list is unused | `retraction.py:23-27`, `:244`; `trust_context.py:40`, `:133` | Major |
| V4 | No pipeline stage produces Phase-4 inputs (`records.json`, `phase4/_manifest.json`, `synthesis/consensus.json`, COI chunks); the harness only lists them as hand-off paths | `handoff.py:65-69` | Major |
| V5 | COI audit needs exactly eight files `coi_chunk_1..8` | `coi.py:122` | Moderate |
| V6 | Retraction runs last, after extraction and synthesis | skill workflow notes | Moderate |
| V7 | Trust rules are fixed policy (Strong needs a public data link and no industry tie of any kind); no per-field setting, no sensitivity analysis | `trust_context.py:137` | Moderate |
| V8 | Strengths: deterministic; refuses rather than invents coverage; unresolved lookups kept visible; per-domain reasons stored; quote matching separated from similarity | kit-wide | Keep |
| V9 | Open-science scan drops studies without extracted text by default; listed only in run metadata | `open_science.py` (`drop_missing=True`) | Minor |

## Where fixes belong

- **scholar-verify-kit (canonical repo, fork + PR):** V1/V2 move domain rules, benchmarks and
  metric names into review configuration and rename the output to what it measures; V3 carry
  severity through to trust levels; V5 accept any number of chunk files; V7 configurable trust
  rules plus a leave-weakest-out sensitivity check; V9 count dropped studies in the summary.
- **Harness (this repo):** V4 produce Phase-4 inputs from the verified Phase-3 data table; V6 run
  the retraction check at screening and again before publishing.
- **Contract v1 gate:** bias-tool settings and trust rules stored in `protocol.json` change the
  protocol schema.
