# M3a-discovery: the discovery engine (Python only)
Branch: `dev/m3a/discovery` · Lane: **RELEASE** (WP-01 Packet B runtime adoption, CORE-07; `test_gate_policy.md` §lanes) · Status: IN PROGRESS · Started: 2026-11-08

Why: plan §6 M3 Discovery, split in two. M3a is the engine half: search legs, pagination, query honesty, stable ids, Packet B adoption and the golden cassettes. M3b (discovery specs 01–08 and screens) waits for the `apps/research-ui` redesign to merge. M3a touches no file under `apps/research-ui`. The researcher has no Scopus or Web of Science access, so the free providers (OpenAlex, Crossref, PubMed, Semantic Scholar, arXiv) are how a corpus is built.

## Definition of done
- [ ] **D1. Search legs (SRCH-30, CORE-21).** Each provider leg records the executed query string, the reported total, the fetched count, the cap and the date. Legs are journalled and written to run-numbered raw files that are never overwritten.
- [ ] **D2. Pagination and caps (SRCH-11, SRCH-31).** Every provider pages to its reported total or to the cap, and emits `cap_hit`. No hidden cap of 100; the cap is `method.retrieval_cap` ([decision](../../decisions.md)).
- [ ] **D3. Query honesty (SRCH-12/13/14).** The executed string is reported; arXiv does not compact silently; bioRxiv is out of the default set; PubMed is not rewritten by a silent regex.
- [ ] **D4. DOI title check (SRCH-10).** A DOI that resolves to a different title gives `DOI_TITLE_MISMATCH`; records are never swapped.
- [ ] **D5. Stable ids (CORE-06, CORE-10).** Records are sorted before dedup and joined on snapshot ids; the DOI bridge does not merge two different studies. A re-run gives identical ids.
- [ ] **D6. Packet B adoption (CORE-07).** A search run builds the corpus snapshot through `build_corpus_snapshot_artifact`, so screening is reachable from a fresh run.
- [ ] **D7. Contact email.** A live search refuses with `MAILTO_NOT_SET` without a configured address ([decision](../../decisions.md)).
- [ ] **D8. Golden cassettes.** The golden search runs from VCR cassettes recorded in one live run.
- [ ] **D9. PRISMA-S report.** The report lists, per database, the executed string, total, fetched count and cap.
- [ ] **D10. Contract check passes** (`generate_contract_baseline.py --check`).

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |

## Decisions
- [2026-11-08 — The retrieval cap is a protocol method key](../../decisions.md)
- [2026-11-08 — A live search needs a real contact email](../../decisions.md)
- [2026-11-08 — One live golden search, frozen to cassettes](../../decisions.md)

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| baseline | 3b474cb | `uv run python scripts/generate_contract_baseline.py --check` | Contract baseline current | — |

## Deferred
- M3b: discovery specs 01–08 and the Discovery screens (plan §7 rule 1: M3 UI is the first cut); agent tasks (query critique, near-twin, methods text).
