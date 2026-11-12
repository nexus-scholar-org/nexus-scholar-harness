# Three phases together: test and hardening review (2026-11-10)

Scope: Phase 0 inception, Phase 1 discovery and Phase 2 screening, driven as one
flow over the console API at `main` `b6643a0` (after PR #215). The discovery
screens (M3c-screens) were still being built in their own session, so the
browser side of Phase 1 is not covered here; the inception and screening
screens are covered by the UI suites listed under "Evidence".

Companion: `docs/kits/search/PROVIDERS_2026-11.md` (what each data source
offers today, what the code sends, and what changed at the providers).

## 1. What was run

One script built the console app in process (`create_app`, loopback, desktop
token) on a scratch workspaces root, with the provider doubles the discovery
tests use (no network), and walked:

1. Phase 0: steps `scope`, `shape`, `criteria`; `POST /inception/preview`;
   draft; `POST /drafts/{id}/genesis` (workspace created, journal
   `PROJECT_INITIALIZED` + `GENESIS`).
2. Phase 1: `GET /discovery/plan` (dry run); `POST /discovery/runs` with a cap
   override and a note; the SSE stream (`snapshot`, 8 `leg`, 5 `stage`,
   `done`); `GET /runs`, `/runs/{run}`, `/runs/{run}/report`, `/report`,
   `/dedup`, `/handoff`; `POST /screening/corpus/accept`.
3. Phase 2: `POST /screening/prepare` (job); `/summary`, `/queue`,
   `/records/{id}`; decision events for every study; conflicts resolved;
   `PUT /approver`; pairing begun in process (the code is never served over
   HTTP) and redeemed; `POST /actions/publish`; `GET /export` (RIS),
   `/methods`, `/ui/publication-status`.
4. Phase 0 again: genesis over the same slug, then replace with the typed slug.

Around the happy path, 65 probes sent wrong, stale, oversized or out-of-order
requests. The script is not committed (it lives in the session scratchpad);
the findings below each name the test file where a permanent guard belongs.

## 2. Evidence

| Check | Result |
|---|---|
| Full flow, inception to export | Passed end to end. Published generation `CURRENT`, RIS export served, methods paragraph produced. |
| Phase gates that held | Second run while one is active: `DISCOVERY_JOB_ACTIVE`. Run or accept on a frozen corpus: `CORPUS_ALREADY_ACCEPTED`. Import after a browser run: `VERIFIED_EXISTS`. Accept after the query changed: `PROTOCOL_CHANGED_SINCE_RUN`. Unreadable protocol: `PROTOCOL_INVALID` (422 on plan, 409 on accept). Prepare before accept: `SNAPSHOT_NOT_ACCEPTED`. Unknown study, stale binding, agent method, missing or made-up reason code, empty screener: all refused with typed codes. Replayed events: `duplicate`. Second decision without `supersedes`: `conflict`. Publish before approval: `APPROVAL_MISSING`. Wrong pairing code: `PAIRING_CODE_INVALID`. Decision after publish makes the export `GENERATION_STALE`. Genesis over an existing slug: `WORKSPACE_EXISTS`; with screening: `SCREENING_BOUND` until the slug is typed. |
| Re-prepare with another batch size after 24 decisions | Safe: every decision kept (events bind by study and protocol, not by batch). |
| Python suite, `-n auto`, Windows, Python 3.14 | 6 failures in the parallel run; all 6 pass alone (see F10). |
| Research UI unit tests (`vitest run`, inception and screening screens) | 27 files, 360 tests, all passed. |

## 3. Findings, ranked

Severity: **P1** blocks or silently damages a researcher's work; **P2** wrong
or missing signal the screens cannot recover from; **P3** polish.

### F1 (P1) Replacing a protocol keeps the old corpus and decisions in place

After `genesis` with `replace: true` and the typed slug, the backup under
`audit/replaced/<stamp>/` holds only `protocol.json`, `intent.json` and
`SCREENING_CRITERIA.md`. Everything under `literature/` stays: the accepted
corpus, the batches, the decision events, the published generation. The new
protocol then sees `GET /screening/corpus` = `ACCEPTED` (from the old
protocol), `GET /screening/summary` = 20 to screen and 0 decided (the events
are bound to the old fingerprint, so they are invisible), and
`POST /discovery/runs` refuses with `CORPUS_ALREADY_ACCEPTED`. The researcher
can neither search under the new protocol nor see the decisions they made.

- Where: `src/scholar_harness/inception/emit.py:170` (backup set).
- Fix: when `literature/verified.json` or `literature/screening/events/` exist,
  move `literature/` (and `.harness-console/`, `artifacts/`) into the same
  backup folder, so the new protocol starts with an empty corpus; or refuse
  with a new code (`CORPUS_BOUND`) and a typed confirmation, like
  `SCREENING_BOUND`. The first is what "replace and back up" promises.
- Test: `tests/console/test_inception_api.py`: after a replace over an
  accepted corpus, `GET /screening/corpus` is `EMPTY`, `POST /discovery/runs`
  starts, and the backup folder holds `literature/verified.json`.

### F2 (P2) "Bound to current protocol" is vacuously true after a protocol edit

Edit a concept in `protocol.json` after decisions exist: `/summary` drops to
0 decided with no reason, a new decision is refused `STALE_BINDING`, and
`/prisma/preview` still reports `bound_to_current_protocol: true` because the
check runs over the winners that survived the fingerprint filter, which is
now an empty set.

- Where: `src/scholar_harness/console/api/screening_v1.py:687`.
- Fix: the check is `bool(winners) and all(...)`, plus a separate check that
  compares each batch file's bound fingerprint with the current protocol's;
  `/summary` and `/queue` carry `protocol_changed: true` (or refuse with
  `PROTOCOL_CHANGED_SINCE_BATCH`) so Home can say "the protocol changed after
  screening started" instead of showing an empty queue.
- Test: `tests/console/test_screening_api_v1.py`: a semantic protocol edit
  flips the check to false and sets the flag.

### F3 (P2) The hand-off and the runs list do not say the protocol changed

`GET /discovery/runs` marks a run `stale` only when a later run became the
corpus (`discovery.py:314`). `GET /discovery/handoff` returns the current
protocol fingerprint but never compares it with the run. The only signal is
the accept refusal, after the click. The accept itself compares the compiled
query text and year window (`corpus_accept.py:283`), so a change to the
databases list, languages or criteria is not detected at all.

- Fix: record `protocol_fingerprint` in `legs.json` at run time (it is not
  there today; the manifest keys are run, status, query, years, caps, notes,
  legs) and add `protocol_changed: bool` to each runs item and to the hand-off;
  keep the query/years comparison as the accept gate.
- Test: `tests/console/test_discovery_api.py`: after a semantic edit, the
  runs item and the hand-off carry the flag before any accept.

### F4 (P2) The corpus view shows zeros for a discovery corpus

After a browser run, `GET /screening/corpus` answers `state: STAGED`,
`sources: []`, `databases: []`, `preview.identified: 0`, with
`from_discovery: true`; after the accept it stays at zeros next to
`accepted.records: 20`. The hand-off has the provider mix, but the Import
screen and any consumer of the corpus view see an empty staged corpus.

- Where: `src/scholar_harness/corpus_accept.py` (`corpus_status`).
- Fix: when `from_discovery`, fill `databases` from the run's legs
  (provider, fetched, cap hit) and `preview` from `deduped.json`.
- Test: `tests/console/test_corpus_api.py`.

### F5 (P2) Validation errors bypass the refusal envelope

A wrong type or a missing field (`cap_override: "ten"`, `providers:
"openalex"`, a methods body without `reviewed`, a 2001-character note)
answers FastAPI's default `{"detail": [ ... ]}` list, not
`{"detail": {"code", "message"}}`. The screens and the proxy tests expect a
code on every refusal. This holds for all three phases.

- Where: `src/scholar_harness/console/serve.py` (no handler for
  `RequestValidationError`).
- Fix: one exception handler that answers 422 with code `BODY_INVALID`, a
  one-line message and `details` = the pydantic errors; register the code in
  `console/refusals.py`.
- Test: `tests/console/test_console_refusals.py` (every refusal has a code).
- Status: fixed in H-input-limits (`docs/roadmap/milestones/H-input-limits.md`);
  `details` is `{"errors": [...]}` without the client's `input`.

### F6 (P2) Inception drafts have no size limits

A 20 000-character topic and a draft with 500 research questions are
accepted and saved under `.drafts/`; genesis would write them into
`protocol.json`. Discovery caps its note at 2 000 characters; inception caps
nothing.

- Where: `src/scholar_harness/console/api/inception.py:56` (`DraftBody`).
- Fix: `Field(max_length=...)` on the text fields and a maximum count for
  `rqs`, `concepts`, `out_of_scope` and criteria; refuse with `DRAFT_TOO_LARGE`.
- Test: `tests/console/test_inception_api.py`.
- Status: fixed in H-input-limits; the limits sit on the draft shape
  (`inception/steps.py`, `DRAFT_LIMITS`), which every route parses, not on
  `DraftBody`; decision 2026-11-12 lists them.

### F7 (P3) Decision events trust three client-supplied values

Accepted as sent: a `decided_at` in 2031; `device: "phone"` from a desktop
token (the server does stamp `token_scope: desktop` next to it, so the
provenance is recoverable); a 50 000-character note.

- Where: `src/scholar_harness/screening/events.py:226`.
- Fix: refuse a `decided_at` more than a few minutes in the future
  (`PROVENANCE_MISSING`); derive `device` from the token scope or refuse the
  mismatch; cap `note` at 2 000 characters like the discovery note.
- Test: `tests/test_screening_events.py`, `tests/console/test_screening_api_v1.py`
  (the event-intake tests).
- Status: fixed in H-input-limits; a mismatched `device` is refused
  (`INVALID_OUTPUT`), not rewritten, and the future window is 5 minutes.

### F8 (P3) Journal noise and deterministic event ids

An idempotent publish retry logs `SCREENING_PUBLISH_COMPLETED` a second time;
a prepare logs `ARTIFACT_ACCEPTED` once per batch. The orchestrator-style
event id is `EVT-<second>-<hash(action+description)>` (`workspace/audit.py:258`),
so two events with the same action and text in the same second share an id.
Kept so far for HCM-02 parity; worth a uuid limb when the journal schema is
next touched.

### F9 (P3) The API process prints to stdout

Genesis prints one "skill ... COPIED (symlink unavailable ...)" paragraph per
skill, twelve lines per workspace, from inside the request. The approval code
is printed on purpose; the rest should go through logging.

### F10 (P3) Six tests fail only under `-n auto` on this machine

`tests/cli/test_cli_init.py::test_run_wizard_raw_target_handoff` (the GENESIS
journal line is missing), `tests/console/test_screening_api_contract.py::test_the_committed_fixtures_are_what_the_engine_produces`
(`record_detail.json` differs by one digit), and four version tests that read
`1.1.0b4` from the installed metadata. All six pass when run alone. CI is
green with the same flags, so this is worker interference (shared caches or
the installed dist-info) rather than code; worth a `pytest -p xdist --dist
loadfile` try and a version test that reads `pyproject.toml`.

### Provider side (from the companion file, spot-checked live on 2026-11-10)

- **F11 (P1) PubMed `[ab]` is not a field tag.** `pubmed.py:33` maps the
  abstract field to `[ab]`; a live esearch answers `FieldNotFound: ab` and
  silently widens the term to `[All Fields]`, while the leg's executed query
  still shows `[ab]`. Use `[tiab]`. Test: `tests/kits/search/` PubMed
  translation test against the recorded `QueryTranslation`.
- **F12 (P1) OpenAlex requires a key since 2026-02-13** (announcement of
  2026-01-14: keys only, the email parameter is gone; keyless calls get a
  small daily budget, then 409; cursor paging past page one needs a key).
  `openalex.py:152` still sends `mailto`, `config.py:20-22` calls the key
  optional, and `MAILTO_NOT_SET` gates nothing on OpenAlex. The plan screen
  should say "OpenAlex key not set" the way it says "contact email not set".
- **F13 (P2) OpenAlex `per_page` max is 100** (we send 200, "deprecated");
  the `title_and_abstract.search:` filter form is "no longer recommended"
  (`search.title_and_abstract` is the replacement); queries with more than
  five boolean operators are limited to 1 request per second keyless.
- **F14 (P2) Crossref rate limits changed** (2025-12-01, 2026-07-21): 1 rps
  public, 3 rps polite, limited per mailto address; we send 5 rps and never
  read the `x-rate-limit-*` headers (`http_client.py`). The User-Agent still
  says `scholar-search-kit/0.1.0`.
- **F15 (P2) Default database sets disagree**: engine, CLI and browser run
  five (with PubMed); `protocol_adapter.py:81-84` and the protocol model
  default to four; recon uses four.
- **F16 (P3)** arXiv terms ask for one request every 3 seconds (we send 1 per
  second) and do have a `submittedDate` range filter the leg note denies;
  Semantic Scholar citations are fetched in one 1 000-record call without
  paging; `legs.json` records neither endpoint, auth channel, page size nor
  client version.

## 4. Hardening plan

Order by value for the researcher's own acceptance test, one PR each,
STANDARD lane unless noted:

1. **F11 + F12 + F13 provider correctness** (PubMed `[tiab]`, OpenAlex key
   required and surfaced on the plan, `per_page` 100, the recommended search
   parameter). These change what a live harvest returns, so they come first
   and need one recorded-cassette run per provider.
   Status: fixed in M3h-providers (`docs/roadmap/milestones/M3h-providers.md`),
   with the Semantic Scholar key findings added; PR pending.
2. **F1 replace semantics** (needs a researcher decision: back up `literature/`
   or refuse). Engine only. RELEASE lane: it moves researcher data.
3. **F2 + F3 protocol-change signals** in one PR: the fingerprint in
   `legs.json`, `protocol_changed` on runs, hand-off, summary and queue, and
   the non-vacuous PRISMA check. M3c-screens should consume the flag on Home
   and on the hand-off screen.
4. **F5 + F6 + F7 input hardening**: one validation handler, draft limits,
   event limits. Small, mechanical, good Sonnet work.
   Status: fixed in H-input-limits (`docs/roadmap/milestones/H-input-limits.md`); PR pending.
5. **F14 + F15 + F16 provider resilience**: rate limits from the providers'
   current rules and headers, one default database set, the arXiv date
   filter, paged citations, a fuller leg record.
6. **F4 corpus view** for discovery corpora, together with the two M3d
   reviewer follow-ups (`limits` used for two things, `selected` status).
7. **F8, F9, F10** when a related file is next open.

## 5. Not covered

- Live providers: the run used in-memory doubles. The provider reference
  file covers what the live APIs changed; a recorded-cassette run against
  OpenAlex and Crossref is still the way to prove the translations.
- The discovery screens (M3c-screens, in progress) and the phone pairing
  flow (`/lan/pair` is M2).
- The agent proposal run (needs live spend).
