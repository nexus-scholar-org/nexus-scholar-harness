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
- [ ] **Decisions recorded** in `docs/decisions.md` (items 1 to 9 accepted 2026-11-21 on the main session's recommendation; this milestone's own choices PROPOSED).
- [ ] **Spec FINAL**: the M8b amendment to `docs/ux/phase2-screening/final/03-triage-desktop.md` (and the alignment line in 05), every state and sentence in en/fr/ar, through the `ux-spec-writer` agent; open questions listed, none guessed.
- [ ] **Matcher**: one pure function `scholar_harness.term_match` (whole words and phrases, case-insensitive, English plurals, space and hyphen variants, no partial words, overlapping terms resolved). Pytest `tests/test_term_match.py`.
- [ ] **Record read** `search_terms` on `GET /records/{study_id}`: concepts in protocol order with their terms and mentions, and marks per field in UTF-16 offsets. Pytest in `tests/test_screening_highlights.py`; contract doc and fixtures regenerated.
- [ ] **Draft read** `quotes` on `GET /records/{study_id}/proposal`: per answer, where its quote sits in the shown title or abstract, or that it is not at its offsets; hidden exactly as the draft is (blinding). Pytest.
- [ ] **Highlighter component** `components/highlighted-text.tsx` taking any text and a span list (reusable for full text, M12a); overlap layering. Vitest `highlighted-text.test.tsx`.
- [ ] **Triage**: the two switches (remembered on this computer), the legend (present and absent concepts, the cap), quote marks tied to criteria both ways, a failed quote not highlighted and said so in the draft, no quote mark before the draft is shown. Vitest `triage.highlights.test.tsx`.
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

## Deferred
- Full text (decision 7): no record has a full text in the app before M12a; the highlighter takes any text and spans so M12a can reuse it.
- The phone (decision 9): spec 04's swipe card is not changed.
- Criterion highlights (`highlights`, `{start,end,criterion_id}`, spec 05): still empty; this milestone does not fill them.
