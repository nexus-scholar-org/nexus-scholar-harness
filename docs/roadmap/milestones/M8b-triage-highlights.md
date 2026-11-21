# M8b-triage-highlights Highlights in the Triage record: search terms and the agent's quotes
Branch: `dev/m8b/triage-highlights` (from `origin/main` `1f218054`) · Lane: **RELEASE** (two additive read fields on public console routes: `search_terms` on `GET /records/{study_id}` and `quotes` on `GET /records/{study_id}/proposal`; `test_gate_policy.md` §lanes "public API"; no Contract v1 schema, identity, fingerprint, event or publication change) · Status: IN PROGRESS · Started: 2026-11-21

Why: the researcher's request of 2026-11-21 (plan §6, "Requested by the researcher on 2026-11-21"), after screening 1,062 records in Triage on 2026-11-20 with the agent's drafts beside each record. The reader should see at a glance why a record was found (and which concept it lacks) and what the agent based its answers on. Start approved in the main session ("launch the M8b with your recommendations"); decisions 1 to 9 of `docs/decisions.md` "2026-11-21 — M8b-triage-highlights" are accepted on that instruction.

## Facts checked at HEAD (`phase-auditor`, 2026-11-21, `1f218054`)
- `record_text` (`screening/proposals.py:77-86`) is `title + "\n\n" + abstract`, then `"\n\nPublished: <year>"` when a year exists; the run strips the abstract and reads "No abstract available." as none (`agent_runs.py:354-357`). Evidence offsets count Python code points into that string.
- The quote check (`validate_output`, `proposals.py:124-136`) is kept as the validator `quote_in_source` with a text detail per criterion; the quote stays in the draft. No per-quote flag reached the browser before this milestone.
- `GET /records/{study_id}` (`console/api/screening_v1.py:268`) serves title and abstract separately (abstract not stripped) and an always-empty `highlights` (criterion highlights, `{start,end,criterion_id}`, not built). The `Abstract` component (`components/triage-page.tsx:106`) renders those spans in the abstract only.
- The protocol's concepts (`search_strategy.core_concepts[]`, `{concept, synonyms[]}`) were not served to any screening screen. The query is compiled from the concept and its synonyms only (`scholar_search/protocol_adapter.py:52-56`), so "query terms" are those words.
- The guidance audit (`docs/ux/shared/final/03-guidance.md`, `tests/guidance.audit.test.tsx`) counts Inception and Discovery rows only (`I-`, `D-`); Triage is not in it.
- M11a's accepted question 8 (`M11a-query-workbench-for-review.md:39`): the workbench's matcher treats English plurals as one word; INC-21 (`recon/session.term_occurs`) stays as it is.

## Definition of done
- [x] **Decisions recorded** in `docs/decisions.md` (items 1 to 9 accepted 2026-11-21 on the main session's recommendation; this milestone's own choices PROPOSED).
- [x] **Spec FINAL** (2026-11-21; the draft's three open points settled as decisions 12, 14, 20, PROPOSED): the M8b amendment to `docs/ux/phase2-screening/final/03-triage-desktop.md` (and the alignment line in 05), every state and sentence in en/fr/ar, through the `ux-spec-writer` agent; open questions listed, none guessed.
- [x] **Matcher**: one pure function `scholar_harness.term_match` (whole words and phrases, case-insensitive, English plurals, space and hyphen variants, no partial words, overlapping terms resolved). Pytest `tests/test_term_match.py`.
- [x] **Record read** `search_terms` on `GET /records/{study_id}`: concepts in protocol order with their terms and mentions, and marks per field in UTF-16 offsets. Pytest in `tests/console/test_screening_highlights.py`; contract doc and fixtures regenerated.
- [x] **Draft read** `quotes` on `GET /records/{study_id}/proposal`: per answer, where its quote sits in the shown title or abstract, or that it is not at its offsets; hidden exactly as the draft is (blinding). Pytest.
- [x] **Highlighter component** `components/highlighted-text.tsx` taking any text and a span list (reusable for full text, M12a); overlap layering. Vitest `highlighted-text.test.tsx`.
- [x] **Triage**: the two switches (remembered on this computer), the legend (present and absent concepts, the cap), quote marks tied to criteria both ways, a failed quote not highlighted and said so in the draft, no quote mark before the draft is shown. Vitest `triage.highlights.test.tsx`. Guidance audit: rows S-TM1 to S-TM7 in `docs/ux/shared/final/03-guidance.md`, read by the audit test (a hint's key must be a HINT row) but not counted, because Screening has not adopted the audit.
- [ ] **Browser**: no page scroll at 1440×900 and 1280×720 with marks on; marks do not move text; axe light and dark, en and ar; RTL. Playwright `tests-browser/triage-highlights.spec.ts`; screenshots looked at.
- [ ] **Gates**: `/gate inner` after edits; `/gate checkpoint` per item; PR gate once on the final commit; `generate_contract_baseline.py --check`; `milestone-reviewer` APPROVE. No push, no PR.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |

## Decisions
- [2026-11-21 — M8b-triage-highlights](../../decisions.md)

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner (engine) | `ce475e90` | `uv run pytest tests/test_term_match.py tests/console/test_screening_highlights.py tests/console/test_screening_api_contract.py tests/console/test_screening_api_v1.py tests/console/test_screening_drafts_api.py -n auto`; `ruff check src/ --select F821,...` | 105 passed; ruff clean | 35 s |
| inner (UI) | `7c1a2ac1` | `npx vitest run tests/highlighted-text.test.tsx tests/triage.highlights.test.tsx tests/plural.test.tsx tests/triage.test.tsx`; `tsc --noEmit` | 85 passed; typecheck clean | about 1 min |
| inner (selector) | `7c1a2ac1` | `select_test_gate.py --changed origin/main --stage inner`: `git diff --check`, `test:related`, `pytest -n auto`, `ruff check scripts/` | diff check and ruff pass. Vitest related 845 passed, 5 failed: one real (`guidance.never-hidden`: a hint's key must be a HINT row; fixed in `67341f09` by reading `S-` rows), three timeouts under load that pass alone (`inception-sample`, `keyboard-traversal`, `proposals`), one that fails on `origin/main` too (`discovery-proposals` "names the assistant…", checked in a clean checkout of `1f218054`). Pytest: 1 failed under load (`test_lineage_api.py::test_lineage_complete_trace`, screening collection blocked), 17 of 17 pass alone; untouched by this branch | about 40 min (machine shared with another run) |
| browser | `67341f09` + working tree | `npx playwright test tests-browser/triage-highlights.spec.ts tests-browser/triage-desktop.spec.ts` (light and dark) | 28 passed, 4 failed: axe `link-in-text-block` on the quote link (a shadow frame is not a non-colour cue for axe). Fixed in `fd626af6` (solid bottom border; frame only when active) | 5.3 min |
| browser | `fd626af6` | `npx playwright test tests-browser/triage-highlights.spec.ts` (light and dark) | 12 passed; screenshots looked at (en/ar, light/dark, and a 3× crop of the legend and title) | 1.8 min |

## Deferred
- Full text (decision 7): no record has a full text in the app before M12a; the highlighter takes any text and spans so M12a can reuse it.
- The phone (decision 9): spec 04's swipe card is not changed.
- Criterion highlights (`highlights`, `{start,end,criterion_id}`, spec 05): still empty; this milestone does not fill them.
- Review follow-ups (P3, not blocking; `test_gate_policy.md`: unrelated or minor observations after the broad review become follow-ups, so the PR gate on `fd626af6` stays valid):
  - **MCP drafts and stripped text** (review #1): `quote_places` rebuilds the record text as the run does (abstract stripped); the MCP tools (`scholar_agent/server.py:2113,2175`) check quotes against the unstripped abstract. A draft written over MCP for an abstract with leading or trailing whitespace would pass `quote_in_source` and show "Not found at its place". Latent: 0 of 23,322 local abstracts carry such whitespace. Fix: pick the rebuilt text whose `input_sha256` equals the draft's, or make both producers strip; add a test.
  - **Legend summary plural** (review #3): "Mentions {n} of {m} concepts" has no singular or Arabic dual form ("Mentions 1 of 1 concepts"). Fix: a `pluralTemplate` entry on `m`.
  - Each draft read now parses the batch files a second time (`_papers` in the proposal route); text is not NFC-normalised before matching (decomposed accents split words); overlapping quotes of two criteria render as adjacent links, each named for its own fragment.
- Seen while gating, not this branch's: `discovery-proposals.test.tsx` "names the assistant and its model…" fails on `origin/main` `1f218054` too; `test_lineage_api.py::test_lineage_complete_trace` failed once under load and passes alone.
