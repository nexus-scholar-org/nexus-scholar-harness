# H-screening-read-performance

Status: **SPECIFICATION, DRAFT; questions 1 to 5 open; nothing built.** Lane proposed: **STANDARD** if question 2 is answered "per request only", **RELEASE** if results are kept between requests (a cache in front of the checks that guard publication). Written by the main session on 2026-11-22 at the researcher's request, from measurements on the published sensor-stress review. The start of any build is the researcher's to approve separately.

Findings it answers: 47 (`docs/roadmap/acceptance-run-sensor-stress-2026-11-20.md`), and the researcher's own reading that the engine, not the page, is slow.

## What was measured

Workspace: the sensor-stress review (2,176 records harvested, 1,062 screened in 54 batches, about 1,100 decision events, published). App built from `main` `76c445ef`; profile run on a copy of the workspace with the source at `main` `21a4e6a3`, on the researcher's PC. Nothing was written to the workspace.

**In the running app, Screening home:** the document loads in 0.1 s; the last of its eight API answers arrives at 9.8 s. The routes are ordinary (non-async) functions doing Python work, so under the interpreter lock they finish one after another although the page sends them together.

| Route | Alone, in the app | In the profile run | Files opened per call |
| :-- | --: | --: | --: |
| `GET /review/next-step` | 3.9 s | 4.9 s | 3,466 |
| `GET /workspaces` | 2.7 s | not profiled | not counted |
| `GET /screening/prisma/preview` | 2.5 s | 2.7 s | 3,302 |
| `GET /ui/publication-status` | 2.4 s | 3.3 s | 3,320 |
| `GET /screening/corpus` | 1.0 s | 1.0 s | 12 |
| `GET /screening/summary` | 0.5 s | 0.4 s | 116 |
| `GET /screening/agreement` | 0.3 s | 0.3 s | 61 |
| `GET /screening/ui/batches` | 0.2 s | 0.2 s | 325 |

A second call takes as long as the first: nothing is kept between requests.

## Where the time goes

1. **The decision log is reloaded once per batch.** `screening/events.py::stale_projections` calls `projection_is_current` for each of the 54 decision files; each call reads `project.json`, then `project_batch`, which calls `load_context` and `read_events` afresh. One call of `/ui/publication-status` therefore reads `protocol.json` and `project.json` 56 times each, the artifact registry and each artifact file 54 times, and parses about 60,600 JSON lines for a log of about 1,100 events. `screening_currentness` → `export.load_published` → `_check_decisions_unchanged` → `stale_projections` is the whole 3.2 s of that route.
2. **The latest decision of a record is found by scanning every event.** `events.heads` filters the full event list for one study; it ran 4,248 times in one `/review/next-step` call (about 6 million dictionary reads, 1.8 s).
3. **A frozen corpus is rebuilt on every call.** `corpus_accept.corpus_status` → `preview_staged` re-parses the five staged exports (2,181 records) and re-runs `scholar_search.dedup.Deduplicator` (22,183 pair checks), about 1 s, for a corpus accepted days earlier.
4. **The same work is repeated within one page.** `console/next_step.py::build_workspace` computes the currentness (3.2 s) and the corpus view (3.1 s under the profiler) that the page also requests separately; Screening home requests `/screening/corpus` twice.

**How much is disk.** In the 3.2 s currentness check: opening and reading files about 0.85 s (3,320 opens), JSON decoding about 1.0 s, the rest Python logic. Disk is about a quarter here; with antivirus scanning each open, or a slower disk, it would be more. One read per file removes it either way.

## Proposal

No route changes its answer. No Contract v1 file changes. The checks that guard publication keep comparing the same bytes.

1. **One load per request.** `stale_projections` (and `project_batch` beneath it) take an optional loaded context and event list; the callers load them once and pass them down. The projection of each batch is computed from the one event list.
2. **An index for the latest decision.** `heads` and `winning_event` read from a per-(study, screener) index built once from the event list; the functions keep their signatures for other callers.
3. **The accepted corpus is read, not rebuilt.** Once a corpus snapshot is accepted, `corpus_status` answers from the snapshot and its acceptance record; the staged exports are re-parsed and de-duplicated only while no snapshot is accepted, or when a staged file changed since.
4. **Results kept between requests (question 2).** A small in-process store per workspace, keyed by the names, sizes and modification times of the files a result was computed from (the event logs only grow; the decision files and the protocol are rewritten atomically). A result is reused only when every key matches; otherwise it is recomputed. Never written to disk.
5. **The page.** Screening home asks for the corpus once; the next-step bar and the page share the publication status; each screen shows a loading state with its headings in place while the engine answers (finding 47's blank page).

## Definition of done (proposed)

1. A fixture of the sensor-stress size (generated: 54 batches, 1,062 decided records, about 1,100 events) on which `/ui/publication-status`, `/review/next-step` and `/screening/prisma/preview` each open at most 150 files; the test fails on today's code (about 3,300).
2. On that fixture each of those three routes answers in under 0.5 s on the researcher's PC, recorded in the build record; the test asserts the file count, not the time (a time limit would be one more test that fails under load).
3. Every existing test of currentness, projection, conflicts and publication passes unchanged; a new test changes one decision event between two calls and sees the second call report the change (question 2's store must not hide it), and another edits a decision file by hand and sees it reported stale.
4. `/screening/corpus` on an accepted corpus does not call the de-duplicator (a test double counts the calls); on a staged, unaccepted corpus it still does.
5. Screening home sends `/screening/corpus` once; a vitest test counts the requests.
6. A before-and-after table of the eight routes on a copy of the sensor-stress workspace, in the build record.

## Open questions

1. **Scope.** Recommendation: screening's read routes and the next-step bar now, as measured; `/workspaces` (2.7 s, not profiled), Charting and Discovery measured first and fixed in a second part if they show the same pattern. Alternative: everything in one build.
2. **Keep results between requests?** Recommendation: yes, keyed by file sizes and times as in proposal 4. Without it, proposals 1 to 3 should already bring each route under a second (an estimate from the profile, not measured), but a page still pays for each route every time. Cost: a store that guards the publication check is the kind of code where a wrong key shows stale data, so the lane becomes RELEASE and the review looks at it specifically. Alternative: per-request reuse only, lane STANDARD, and measure again before deciding.
3. **A hand-edited file within the same second.** File times on Windows are fine-grained, but a file rewritten with the same size inside one tick of the clock would not be noticed by a size-and-time key. Recommendation: accept it for display routes, and have the two actions that write (approve, publish) always recompute from disk, ignoring the store. Alternative: key by content hash, which costs a read of every file per request (still far cheaper than today).
4. **Several requests at once.** Today they queue behind the interpreter lock. Recommendation: leave it; with each route under a second the queue stops mattering. Alternative: one combined "screening home" route, a new API surface.
5. **The loading state.** Recommendation: headings and empty cards in place, with the sentence the page already has ("Counts appear only once every file is read"), no spinner. Alternative: a skeleton animation; the brand book has no rule for one.

## Not verified

- The estimate "under a second" comes from the profile, not from a changed engine.
- `/workspaces`, Charting, Discovery and Inception were not profiled. Triage's per-record routes were not timed.
- One workspace, one machine, one run of each measurement (three repeats per route in the profile run; two in the app).
- Whether the artifact registry reads can share one load was not read in the code; the count comes from the open-file tally.
