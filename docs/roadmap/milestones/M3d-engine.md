# M3d-engine Discovery engine items
Branch: `dev/m3d-engine/engine-items` · Lane: **STANDARD** (packet §7; what the corpus snapshot is built from is unchanged, only *when* a browser run builds it; `generate_contract_baseline.py --check` at every commit) · Status: IN PROGRESS · Started: 2026-11-10

Why: M3b-api (PR #214) shipped the discovery routes and deferred four engine items to this milestone: the researcher's decision of 2026-11-10 "A browser harvest does not freeze the corpus; the hand-off screen does", and the packet's E1, E3 and E4a ([`DISCOVERY_API_PACKET.md`](../../architecture/research_ui/DISCOVERY_API_PACKET.md) §4.1, §4.4, §4.5, §7). No UI work.

## Definition of done
- [ ] **Hand-off accept** (decision 2026-11-10, packet §4.3, §4.8): a browser run ends with `stages.corpus_snapshot.status = "NOT_ACCEPTED"` and prepares no batches; `POST /screening/corpus/accept` builds the snapshot from `verified.json` with the artifact id the CLI run gives, journals `CORPUS_SNAPSHOT_ACCEPTED`; the CLI `run` still accepts. Tests: `tests/console/test_discovery_api.py`, `tests/pipeline/test_golden_search_cassettes.py`.
- [ ] **E1 plan dry run** (packet §4.1): `translate(query)` per provider, `compile_plan` in `scholar_search`, `GET /discovery/plan` fills `executed_query`, `request`, `cannot_express`, `notes`. Test: the preview equals the replayed golden legs (`tests/pipeline/test_golden_search_cassettes.py`).
- [ ] **E3 import rejections** (packet §4.4): RIS and `.nbib` importers return `rejected: [{line, code, reason}]` (`IMPORT_NO_TITLE`, `IMPORT_BAD_TAG`, `IMPORT_BAD_YEAR`); staged rows and `GET /screening/corpus` carry them; `limits` stored verbatim; `GET /discovery/report` lists both. Tests: `tests/kits/search/test_import_rejections.py`, `tests/console/test_corpus_import_api.py`.
- [ ] **E4a dedup tiers** (packet §4.5 Stage 1): `literature/dedup/clusters.json`, the tier per cluster, `GET /discovery/dedup`, `dedup.by_tier` in the report; `stable_order` and SCI ids unchanged. Tests: `tests/kits/search/test_dedup_tiers.py`, `tests/console/test_discovery_api.py`, the golden cassette test.
- [ ] **Gate**: `/gate inner` after each item, `/gate checkpoint` at its end, `/gate pr` once on the final commit, contract check, `milestone-reviewer` APPROVE.

## Tests written first
| Test | Fails before | Passes after |
| :-- | :-- | :-- |
| `tests/console/test_discovery_api.py::test_a_browser_run_stops_before_the_snapshot_and_the_handoff_accepts_it`, `::test_the_handoff_accept_keeps_a_failed_database_as_a_snapshot_warning`, `::test_run_events_replay_snapshot_legs_stages_and_done` (stages end at `corpus_snapshot` `NOT_ACCEPTED`) | yes: snapshot `ACCEPTED`, corpus `EMPTY` | yes |
| `tests/pipeline/test_golden_search_cassettes.py::test_the_handoff_accept_gives_the_snapshot_the_cli_run_gives` | yes: no `freeze_corpus`; first draft (two harvests compared) failed on the id, see decision 2 | yes |

## Decisions
Points the packet and the decision of 2026-11-10 did not settle, decided in this milestone.

1. **The browser run's end state** (packet §4.3). `run_pipeline(freeze_corpus=False)` (default `True`, so the CLI and the orchestrator are unchanged) stops after verification: `status: "PENDING_CORPUS_ACCEPT"`, `stages.corpus_snapshot = {status: "NOT_ACCEPTED", reason: "awaiting the hand-off accept"}`, the later stages `SKIPPED` with that reason, journaled `PIPELINE_RUN_PAUSED_FOR_CORPUS_ACCEPT` (the counterpart of `PIPELINE_RUN_PAUSED_FOR_SCREENING`). The job ends `succeeded`. The stage stream ends at `corpus_snapshot`; there is no `screening_prepare` stage event.
2. **"Same artifact id for the same inputs" is pinned on the same records.** The snapshot id is a function of the accepted rows, and each row carries its `retrieved_at`, so two harvests of the same cassette (two CLI runs too) never share an id. The golden test copies the browser run's workspace before the accept, freezes the copy with the CLI run's own accept step (`_accept_run_corpus`) and the original with the hand-off accept: the ids, the outcome status and the counts match, and a CLI run of the same search gives the same counts. Making the id independent of `retrieved_at` would change snapshot identity (RELEASE, Packet B) and is not done.
3. **The hand-off accept reads the run's failed databases back from `legs.json`** (`accept_discovery_corpus` in `pipeline/coordinator.py`): the newest run with `corpus_published` (or `raw_published` before M3b-api) gives the same provider warnings the pipeline passes, so a run with a failed database is still accepted `PARTIAL`. It journals `CORPUS_SNAPSHOT_ACCEPTED` (agent `scholar-harness-console`) with the same parameters as the pipeline's row plus `run`.
4. **`GET /screening/corpus` says `STAGED`** for a discovery `verified.json` that waits for the accept (`from_discovery: true`), as it does for staged exports; `EMPTY` stays for a workspace with neither.

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |

## Deferred
