# Workspace stats reconciliation (T-TRUTH-COUNTS-01)

**Status:** implemented in the harness (`src/scholar_harness/`). No toolkit
source changed; no kit pin changed.

## The defect this closes

A harness summary is only useful if it is true. Before this change the
harness counted a corpus **only** at five canonical `literature/` paths
(`raw_search.json`, `deduped.json`, `verified.json`, `included.json`,
`excluded.json`). A corpus stored anywhere else was invisible, and the
`doctor` staleness check reported the disagreement as a soft `WARN`.

Measured on the live demo workspaces (read-only inputs, not modified):

| Workspace | Declared `discovered_papers` | Physical records | Physical deduped |
|---|---|---|---|
| `workspaces/uav-pilot-demo` | 0 | 2165 (`calibration/raw_union*.json`) | 2060 (`calibration/deduped.json`) |
| `workspaces/uav-crop-weed-v03` | 0 | 14413 (`calibration_v03/v03_r3d_20261017_union_hydrated.json`) | 14150 (`calibration_v03/v03_r3d_20261017_deduped.json`) |

(The `r3d` and `r3e` artifacts hold the same number of records; the
selection is content-based and never mtime-based, so the tie is broken
lexicographically -- `v03_r3d_...` wins over `v03_r3e_...`.)

Both workspaces hold a journal with many `DISCOVERY_SEARCH` events, so the
harvest demonstrably happened: only the *summary* was false. These numbers
are **measurements recorded here**; the test suite derives its expectations
from synthetic fixtures and never depends on the current content of a live
workspace.

## What the harness does now (the actual rules)

`src/scholar_harness/workspace/counts.py` owns the counting rules. This
section states what the code really does -- every claim below is covered by
a test.

### 1. Artifact discovery is content-based, not a filename whitelist

Every `*.json`, `*.jsonl` and `*.ndjson` file under the workspace is
inspected. A file the harness has never seen is still read; if it physically
carries a record list, its records are counted.

**Documented exclusions** (and why):

| Exclusion | Reason |
|---|---|
| `audit/` | the append-only event ledger -- its rows are events, not corpus records |
| `chroma_db/`, `rag/` | vector stores and heavy binary payloads |
| `__pycache__/`, `node_modules/`, dot-paths (any path part, the file name included) | build/runtime scratch |
| `project.json` | the manifest *declares* the counters being reconciled -- counting it would be circular |
| `literature/synthesis_matrix.json` | harness-owned *derived* artifact (protocol matrix rows) -- counting it would count the corpus twice |
| `literature/verified_unresolved.json` | harness-owned derived artifact (verification quarantine) |
| `literature/prisma_report.json` | harness-owned derived artifact (PRISMA counters) |
| `literature/graph.json`, `literature/knowledge_graph.json` | harness-owned derived artifact (citation graph nodes/edges) |
| `literature/extraction/**` | harness-owned derived artifact (the merged extraction records, e.g. `literature/extraction/merged/records.json`) |
| `literature/verification/**` | harness-owned derived artifact (verification artifacts) |
| `literature/screening/**` | harness-owned derived artifact (screening batches/decisions repeat corpus records under a decision context) |
| the screening stage's own artifact names (`batch_NNN*.json`, `pack_NNN*.json`, `*.view.json`) | the same derived screening artifacts, wherever the screening lane lives |

Every exclusion is an **explicitly named path** (or one of the harness' own
screening artifact names) -- never a guess about an arbitrary directory
prefix: a real corpus directory called `screening_corpus/` is inspected
normally. Everything else -- including files under `pdfs/` and `extracted/` --
**is** inspected. (Earlier revisions of this module skipped `pdfs/` and
`extracted/`; that skip was removed because a corpus artifact parked there
must not be invisible for that reason alone.)

### 2. Every inspected artifact gets exactly one named state

| State | Meaning |
|---|---|
| `COUNTED` | a physical record list was found and counted (a top-level array, or an array under a well-known record-list key: `documents`, `records`, `items`, `results`, `data`, `papers`, `hits`, `entries`) |
| `SUMMARY_ONLY` | the artifact carries **no** record list but does carry an explicit count field (`count`, `union_count`, `cluster_count`, `total_records`, `total`). The number is a *declared summary*, not physical truth, and the artifact is labelled as such |
| `CONFLICT` | the artifact carries **both** a record list and a count field that disagree. The physical list is the truth and is used for the counter, but the disagreement is surfaced (never silently dropped). A conflict artifact still **physically carries records**: it is part of the corpus, it contributes its physical count, and it never turns a corpus into "no corpus". When the record list is **empty** while the artifact declares a positive count, the physical count is **undetermined** (never a silent `0`) |
| `UNREADABLE` | the file could not be read or is not valid JSON. **Never** collapsed into "no candidate" and **never** into `0` |
| `UNKNOWN_SHAPE` | the file parsed, but it carries neither a record list nor a count field |

Line-oriented corpora (`.jsonl` / `.ndjson`) are swept too: one JSON object
per line is one record (a malformed line makes the artifact `UNREADABLE`).

The record-list search descends **only through the well-known record-list
keys** (bounded depth), so a nested corpus such as
`{"data": {"documents": [...]}}` is found, while an unrelated nested list
(e.g. `research_questions`) is never mistaken for a corpus.

A parse error is never silently treated as "no candidate": the affected
role's counter becomes **undetermined** (the reconciliation status
`UNRESOLVED`), and the doctor names the file.

### 3. Role assignment is best-effort, token-assisted and tokenised

A file **stem** is split into words and a role token matches only as a whole
word (or a whole consecutive word phrase) -- never as a bare substring.
Role-specific tokens **outrank** the generic ones, so `deduped_papers.json`
maps to `deduped_papers` and never to `discovered_papers`:

| Strength | Tokens |
|---|---|
| role specific | `deduped`, `deduplicated`, `verified`, `included`, `excluded` |
| generic | `all_raw_search`, `raw_search`, `raw_union`, `union`, `corpus`, `all_records`, `records`, `record`, `papers`, `results`, `hits` |

A file name containing a known provider name (`openalex`, `crossref`,
`arxiv`, `pubmed`, ...) is mapped to the *discovered* role as provider
evidence.

A record-bearing artifact with **neither** is still counted and reported as
an **UNCLASSIFIED corpus contribution** -- it is never dropped and never
silently counted as `0`. Because the declared counters cannot represent
those records, their presence makes the reconciliation `UNCLASSIFIED`, which
the doctor reports as a non-PASS state.

### 4. Selection is deterministic and content-based (never mtime-based)

For each role the counted artifact is chosen by, in order:

1. the canonical `literature/<name>` artifacts (in the canonical order);
2. the strongest role token (role-specific tokens outrank the generic ones; a
   longer token phrase outranks a shorter one);
3. an artifact that physically carries records, over one that only carries a
   summary;
4. the artifact with the most records;
5. the lexicographically smallest relative path (final tie-break, so the
   result never depends on directory iteration order).

**No timestamp/mtime enters the result.** A count must be reproducible from
the *content* of the workspace; "the freshest file wins" made the number
depend on filesystem timestamps, which are not part of the evidence.

Provider evidence is used only when no role-token artifact exists; it is
aggregated per provider (the best artifact per provider -- alternative
snapshots of the same provider output are not summed, to avoid double
counting) and the per-provider totals are summed.

**Stated limitation (provider overlap).** Provider harvests overlap: the
same document can be returned by two providers. A counter summed from more
than one provider artifact may therefore over-count the physical corpus.
This is not silently hidden: `CorpusCounts.provider_evidence` /
`CorpusCounts.provider_overlap` record it and the doctor reports a
`provider-evidence-overlap` WARN naming the providers. A union artifact is
the authoritative count.

**All** candidates of a role stay visible: `CorpusCounts.sources[role]` is
the list of every candidate path and `CorpusCounts.selected[role]` is the
path(s) whose count produced the counter. The `sources` block is
machine-readable (one path per list entry -- never a comma-joined string).

### 5. Determinism

The traversal is sorted and no timestamp enters the result, so two runs over
an unchanged workspace produce identical counts, identical sources and an
identical status.

### 6. Explicit status

**Reconciliation verdicts** (the status of the declared-vs-actual comparison):

| Reconciliation status | Meaning |
|---|---|
| `OK` | the declared counters match the physical state |
| `STALE` | at least one counter disagrees with the physical state |
| `UNCLASSIFIED` | at least one record-bearing artifact carries no known role, so the declared counters cannot represent the physical corpus |
| `UNRESOLVED` | a counted role is undetermined (an artifact that could not be read/understood maps to that role): the counter is undetermined, never `0` |
| `UNIDENTIFIED` | corpus artifacts exist but none could be identified or parsed: the workspace is **not reconciled** |
| `CONFLICT` | a corpus artifact's own summary disagrees with its own record list. The physical list is the truth and is used for the counter, but the corpus is not self-consistent, so the workspace is **not reconciled** (never a green verdict) |
| `SUMMARY` | the corpus exists only as a *declared summary* (no physical record list): a summary is **not** a verified physical reconciliation |
| `NO_CORPUS` | the workspace holds **no corpus artifact at all** -- a verifiable state that reconciles against a declared `0` |

`NO_CORPUS` and "the reconciliation never happened" are **different**
states: the first is a fact about the workspace that reconciles against a
declared `0` (the doctor reports `PASS`), the second is a fact about the
run (`FAIL`/`WARN`, never `PASS`).

`CONFLICT` and `SUMMARY` are **not** "no corpus": an artifact that
physically carries records (even one whose own summary contradicts that
record list) IS a corpus. The doctor therefore never writes "no corpus
artifact" / "0 corpus records" for such a workspace -- it states the
physical count and names the conflict. A workspace whose corpus is
conflict-only is reported as `CONFLICT` (not reconciled), never as
`NO_CORPUS` and never as a green "reconciled" verdict.

**Reconciliation-block statuses** (the reconciliation was *not performed* --
these are NOT verdicts about the workspace):

| Status | Meaning |
|---|---|
| `MISSING_MANIFEST` | `project.json` does not exist: the declared counters could not be read, so no comparison happened (`WARN`, never `PASS`) |
| `UNREADABLE_MANIFEST` | `project.json` could not be parsed: the declared counters could not be read, so no comparison happened (`WARN`, never `PASS`) |
| `NOT_APPLICABLE` | no reconciliation check was run at all (the directory is not a Nexus Scholar workspace) |

These three statuses are the `reconciliation.status` of the machine-readable
`--json` block when no reconciliation was performed. They are distinct from
every verdict above: a verdict says something about the workspace, these say
something about the *run*.

## Consumers

* `orchestrator.sync_state` writes the counted values into `project.json`
  (always present, `0` when the artifact is gone -- no stale carry-over),
  counts the corpus **once**, and records the declared-vs-actual
  reconciliation in the journal event -- whose `status` **is** the
  reconciliation status (never a generic `SUCCESS` next to a `STALE`
  payload). The PDF/extraction counters are written from the same helper the
  reconciliation compares against, so the declared state and the compared
  state can never diverge.
* `doctor.check_layout` compares the declared summary with the physical
  artifacts:
  * a mismatch is **FAIL** (`project.json-stats`), not `WARN` -- a stale
    summary is a correctness defect;
  * `project.json-stats` is **never** `PASS` when the reconciliation was not
    performed. It reports `FAIL` (`UNRESOLVED` / `UNCLASSIFIED` /
    `UNIDENTIFIED` / `STALE`), `WARN` ("no reconciliation was performed" --
    missing or unreadable manifest) or `PASS` (`OK`, and `NO_CORPUS`, which
    reconciles against a declared `0`). The state is distinguishable from a
    genuine `PASS` in the human table *and* in the `--json` output (the
    report carries a machine readable `reconciliation` block with
    `performed` / `reconciled` / `status`);
  * the `corpus-counts` check states the physical count and names the
    artifacts that no counter represents;
  * the `corpus-unreadable` check puts the artifacts that could not be read
    or understood on their **own line**. An artifact that maps to *no* role
    never turns the counted counters into "undetermined" and never poisons
    them -- the counted numbers stay the primary truth;
  * the `corpus-conflicts` check surfaces an artifact whose own summary
    disagrees with its own record list;
  * the `provider-evidence-overlap` check surfaces the known limitation of a
    summed provider counter;
  * the aggregate can never report `PASS` while the reconciliation row is
    non-`PASS` (the `--exit-code` gate therefore sees a real reconciliation).
    An ordinary optional `SKIP` sub-check stays harmless.
* `pipeline.discovery` publishes exactly one canonical `DISCOVERY_SEARCH`
  event through `workspace.audit.append_event` (the sole owner of the
  append-only journal discipline) and never reports `SUCCESS` for an empty
  or degraded harvest: `PARTIAL` names the providers that failed,
  `EMPTY_RESULT` / `FAILED` explain an empty harvest. A `FAILED` harvest
  publishes **no** raw corpus artifact at all.
* `pipeline.coordinator` propagates the harvest outcome to the pipeline
  result **without collapsing the two axes** (see the status vocabulary
  below): a `FAILED` harvest aborts the run before any downstream stage (and
  writes a `PIPELINE_RUN_ABORTED` row instead of a "completed" row), an
  `EMPTY_RESULT` harvest is never reported as `SUCCESS`, and a `PARTIAL`
  (degraded) harvest never overwrites the workflow state -- it is exposed
  through `results["degraded"]` / `results["degradation_reason"]`.

## The pipeline status vocabulary (two axes, never collapsed)

`run_pipeline` returns a mapping with **two orthogonal axes**. They are
never merged into one string (the same rule the frozen contract applies to
claims, XC-041).

**Axis 1 -- the workflow state** (`results["status"]`):

| Value | Meaning | What a consumer must do |
|---|---|---|
| `SUCCESS` | the pipeline ran every stage to the end | nothing special; but still check `results["degraded"]` (a degraded harvest keeps the workflow state) |
| `EMPTY_RESULT` | the harvest returned nothing, so the run is not an unqualified success | do **not** treat the corpus as non-empty; the empty harvest is also in `results["discovery"]["status"]` |
| `PENDING_AGENT_REVIEW` | the run is waiting for the PRISMA agent-in-the-loop handoff (`literature/included.json` not collected yet) | continue the screening handoff; do **not** read this as a failure |
| `FAILED` | hard failure (the discovery harvest failed) | the run aborted: no downstream artifact is authoritative; read `results["discovery"]["reason"]` |

`PARTIAL` is **not** a top-level workflow state: a degraded harvest is a
property of the *discovery outcome*, not of the workflow. A consumer that
needs the degradation reads `results["degraded"]` (a boolean that is always
present) and `results["degradation_reason"]` (the failing providers), plus
`results["discovery"]["status"] == "PARTIAL"`.

**A missing status is not a success.** When the pipeline result carries no
`status` at all (an empty mapping), the CLI renders the *unknown status*
headline ("Research Pipeline Completed with an unrecognised status") and
reports `Status: UNKNOWN` -- never the success headline. The pipeline
publishes one of the four states above; an absent status is an unusable
result, not an unqualified success.

**Axis 2 -- the discovery outcome** (`results["discovery"]`): `status`
(`SUCCESS` / `PARTIAL` / `EMPTY_RESULT` / `FAILED`), `reason`, `count`,
`corpus_published`, `audit_status` / `audit_reason` / `audit_workspace`
(the provenance of the `DISCOVERY_SEARCH` row) and `stale_artifacts_present`
/ `stale_artifacts` (see below). The same outcome is recorded in the
`DISCOVERY_SEARCH` ledger row.

### Precedence (pinned by a test)

1. `FAILED` (harvest) -> the pipeline status is `FAILED` and the run aborts
   before any downstream stage (hard failure; nothing else is consulted).
2. `EMPTY_RESULT` (harvest) -> a pipeline that would otherwise report
   `SUCCESS` reports `EMPTY_RESULT`. A pipeline that is *waiting* for the
   PRISMA handoff keeps `PENDING_AGENT_REVIEW` (it never claimed
   `SUCCESS`), and the empty harvest stays visible in
   `results["discovery"]["status"]` and in the `DISCOVERY_SEARCH` row.
3. `PARTIAL` (harvest) -> the workflow state is **never** overwritten; the
   degradation is exposed explicitly (`results["degraded"] is True`).
4. `SUCCESS` (harvest) -> the workflow state is untouched.

### The journal axis (row status expresses the row's own outcome)

A ledger row's status states **that row's own outcome**, never a generic
`SUCCESS` sitting next to a degraded payload:

| Row | Status |
|---|---|
| `DISCOVERY_SEARCH` | the harvest outcome (`SUCCESS` / `PARTIAL` / `EMPTY_RESULT` / `FAILED`) |
| `PIPELINE_RUN_PAUSED_FOR_SCREENING` | the harvest's success-ness: `SUCCESS` only when the harvest itself succeeded, otherwise `EMPTY_RESULT` / `PARTIAL` -- **never** `SUCCESS` for a harvest that was not a success |
| `PIPELINE_RUN_ABORTED` | `FAILED` |
| `PIPELINE_RUN_COMPLETED` | the harvest's success-ness: `SUCCESS` for a successful harvest, `EMPTY_RESULT` / `PARTIAL` for an empty or degraded one -- an unqualified `SUCCESS` would hide the degradation |
| `STATE_SYNC` | the **reconciliation** status (`OK` / `STALE` / `UNCLASSIFIED` / `UNRESOLVED` / `UNIDENTIFIED` / `CONFLICT` / `SUMMARY` / `NO_CORPUS`), never a generic `SUCCESS` |

The coordinator-owned rows are about the *run*, so their status states the
harvest's success-ness; the **workflow state** (including
`PENDING_AGENT_REVIEW`) lives in the returned mapping
(`results["status"]`), never merged into a ledger status. The pause itself
is stated by the row's action and description.

A provenance gap (a `DISCOVERY_SEARCH` row that could not be written,
`audit_status == "NOT_WRITTEN"`) is recorded in the description of the
coordinator-owned row, so the gap is visible in the ledger itself.

### Stage-mapping shapes

`results["stages"]` keeps one shape per stage on every path. The abort path
(a `FAILED` harvest) publishes the **successful-path keys** with neutral
zero values plus `"status": "SKIPPED"` and an explicit `reason` -- so a
consumer reading `stages.deduplication["unique"]` or
`stages.matrix_rows["rows"]` never hits a `KeyError` on an aborted run. The
stage *names* are the successful-path names (`matrix_rows`, `graph_nodes`),
never aliases. `results["stages"]["discovery"]` is the discovered document
count (a bare integer) on **every** path; the harvest status lives in
`results["discovery"]`.

### Stale artifacts after a failed harvest

A failed harvest never deletes anything: the artifacts of an earlier run
stay on disk (deleting a researcher's data would destroy evidence), but
they physically contradict the failed journal row. The outcome therefore
names them (`stale_artifacts_present`, `stale_artifacts`), the
`DISCOVERY_SEARCH` row records them
(`metrics.stale_artifacts_present` / `metrics.stale_artifacts`), and the
coordinator's row says so in its description. **A stale artifact must never
be treated as this run's corpus** -- `sync_state` will still count it
(physical truth), so the declared counters must be read together with the
journal.

## Audit action name and status vocabulary

The workspace-manager audit trace spec (section 3) lists the standard
action names and states that the writer *enforces no closed enum*. It has
no reconciliation-specific action, so the harness reuses its existing
`STATE_SYNC` action (the action `sync_state` has always written) rather
than inventing a new dialect. The reconciliation payload travels in the
event's `metrics.reconciliation` block: `status`, `declared`, `actual`,
`mismatches`, `sources`, `selected`, `corpus_present`, `unclassified`,
`unreadable`, `undetermined`.

One action name was added by this task: `PIPELINE_RUN_ABORTED` (written
instead of `PIPELINE_RUN_COMPLETED` when the discovery harvest FAILED). The
spec enforces no closed enum, and the alternative -- a "completed" row for
a failed run -- would be a false history entry.

The `STATE_SYNC` payload travels in the event's `metrics.reconciliation`
block: `status`, `declared`, `actual`, `mismatches`, `sources`, `selected`,
`corpus_present`, `unclassified`, `unreadable`, `undetermined`. The last
three keys are **added** by this task (they were documented but not
carried): they are the *evidence* for the `UNCLASSIFIED` / `UNREADABLE` /
`UNDETERMINED` states -- without them the row could state those states but
never justify them. They are the same lists the reconciliation object
already exposes (`Reconciliation.as_dict()`), so the payload and the
returned mapping never disagree.

**Explicit vocabulary extension.** `DEVELOPER_COMPASS.md` section 3
describes the outcome vocabulary as "successful, partial, waiting, or
failed", and the workspace audit writer's CLI documents only
`SUCCESS`/`FAILED`. The discovery stage adds `EMPTY_RESULT` ("the search
ran and legitimately returned nothing") as a third, distinct state; it is
recorded here because the writer enforces no closed enum, and it is never
used to mean success. The provenance `method` of the discovery event is
`EXTERNAL_PROVIDER` (the records come from an external provider, not from a
deterministic rule or an LLM), as required by `DEVELOPER_COMPASS.md`
section 3.

**Row status = the row's own outcome.** A row's `status` states what that
row is about, never a constant. `STATE_SYNC` is about the reconciliation,
so its status is the reconciliation status (`OK` / `STALE` / `UNCLASSIFIED`
/ `UNRESOLVED` / `UNIDENTIFIED` / `CONFLICT` / `SUMMARY` / `NO_CORPUS`); the
coordinator-owned pipeline rows carry the workflow state (and `PARTIAL` when
a completed run's harvest was degraded). A generic `SUCCESS` next to a
degraded payload would be a false history entry, so the writer's default
(`status="SUCCESS"`) is never relied on for these rows.

**One reconciliation, one verdict (the doctor and `sync` agree).** The
doctor and `orchestrator.sync_state` compute the reconciliation from the
SAME inputs: the same corpus counts and the same extra counters
(`counts.extra_actual_stats` -- the PDFs and the extracted markdown, always
emitted, `0` when the directory is absent). When the two sides used
different extra counters, one workspace got two verdicts: the doctor said
`FAIL` while the `STATE_SYNC` row said `OK`. The row reports the
reconciliation of the state **before** the manifest is rewritten (that is
the row's purpose: it records what was corrected); the doctor reports the
**current** state. After the repair both say `OK`.

## Scope limits (stated, not claimed)

* **Only the corpus counters are reconciled.** `CORPUS_STAT_KEYS`
  (`discovered_papers`, `deduped_papers`, `verified_papers`,
  `included_papers`, `excluded_papers`) plus the doctor's PDF/extraction
  counters are compared with the physical state. Declared counters such as
  `screening_batches`, `records_screened` or `graph_nodes` are **not**
  reconciled -- they are copied from the PRISMA report / graph artifacts by
  `sync_state` and are not verified against the physical files.
* **The PRISMA accounting generator is not implemented.** Lesson H4
  ("reconcile the declared counts against the physical files" + a stratified
  per-database identification table) is only half covered here: the
  reconcile-vs-physical-files check is enforced; the stratified
  per-database identification table is **not** in scope for this task and
  is not claimed.
* **Unclassified contributions need a human decision.** A record-bearing
  artifact the harness cannot map onto a declared counter is reported, not
  silently absorbed. Either the artifact is renamed into the documented role
  vocabulary, or it is a derived artifact that belongs in the documented
  exclusion list.

## Deliberately out of scope

The search kit still swallows per-provider exceptions inside
`SearchEngine.fetch_provider`; the harness observes the providers instead
of changing the kit. Fixing the kit belongs to the canonical
`nexus-scholar-org/scholar-search-kit` repository (with a `plugins.json`
SHA bump and a matching vendored snapshot), which this task does not do.
