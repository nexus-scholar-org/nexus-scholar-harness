# UI-07 Presentation Specification (read-only)

Status: specification-in-review. No implementation authorized by this document.
Companion: [UI-07 Action Spec](./UI-07_ACTION_SPEC.md) (separately reviewed).
HCM prerequisite: [HCM-02 disposition](../harness-core-modularity/hcm-02-disposition.md).
Product direction: [individual researcher application](../decisions/individual-researcher-product.md).
Requesting packet: [AGENT_WORK_PACKETS.md](./AGENT_WORK_PACKETS.md) §UI-07.

All example payloads in this document are **illustrative** and use
obviously-synthetic values (`WSP-EXAMPLE-*`, `RUN-EXAMPLE`). They assert
nothing about any real workspace.

## 1. Scope and authority

This spec defines **read-only presentation shapes** for the UI-04 screening
journey (GATES §8: citation, abstract, criteria panel, decision choices,
reason field, disabled submit "until the API exists"). It authorizes no
write, no approval, no publication. The one screening-decision command and
all approval/publication operations belong to the Action Spec.

**Authoritative API location:** the existing console router family —
`src/scholar_harness/console/api/workspace.py` (read routes) plus the
screening-read routes in the same router (`GET /screening/batches`,
`GET /screening/batch/{n}`). New UI-07 read shapes are views served by this
router family over the workspace bound at app state. No new server, no
browser-to-file access, no parallel read path.

### 1.1 Exact existing read routes (evidence, read 2026-10-13)

Every route below lives in `console/api/workspace.py`. **None checks
generation currentness** — that is the gap this spec closes for
publication outputs (§5), by requiring the AG-03C gate at serve time
rather than by changing these routes' storage behavior.

| Route (line) | Returns | Currentness check |
|---|---|---|
| `GET /api/v1/workspace/meta` (:99) | `project.json` / `INDEX.md` / `protocol.json` text, or `-> missing: <name>` markers | none |
| `GET /api/v1/workspace/status` (:112) | `ResearchOrchestrator.get_status()` projection | none |
| `GET /api/v1/literature/candidates` (:120) | paginated `raw_search.json` (`total/offset/limit/items`) | none |
| `GET /api/v1/literature/included` (:131) | canonical `included.json` bytes | none |
| `GET /api/v1/literature/excluded` (:136) | canonical `excluded.json` bytes | none |
| `GET /api/v1/screening/batches` (:141) | per-batch `name/items/decisions_file/decisions_count/collected` | none |
| `GET /api/v1/screening/batch/{n}` (:177) | `batch_file/items/decisions_file/decisions` | none |
| `GET /api/v1/synthesis` (:193), `GET /api/v1/phase4` (:198) | file index (`name/kind/ext/is_markdown/size_bytes/mtime`) | none |
| `GET /api/v1/synthesis/{filename}` (:203), `GET /api/v1/phase4/{filename}` (:211) | `{filename, content}`; traversal rejected by `_safe_join` (:46 → 400) | none |
| `GET /api/v1/harvest/corpus` (:219) | pdf/extracted counts + `pdf_manifest.json` or `None` | none |
| `GET /api/v1/assets/graph` (:242) | `knowledge_graph.html` or `graph.html`, else 404 | none |
| `GET /api/v1/audit/events` (:254) | newest-first filtered/paginated journal projection (`total/offset/limit/items`) | none |
| `GET /api/v1/agents/actions` (:284) | `actions_payload` for the bound workspace | none |

Existing error behavior reused unchanged: `_read_json` (:28) → `404
missing file: <name>` / `500 unparseable JSON: <name>`; `_safe_join`
(:46) → `400 invalid file name`; `screening_batch` (:177) → `404
missing file: batch_NNN.json`. UI-07 shapes keep these codes and add
typed currentness errors only where §5 requires them.

For the record: the only POST in this surface area is
`POST /api/v1/screening/batch/{n}/decisions`
(`console/api/screening.py:98`). It writes the canonical
`batch_NNN_decisions.json` wrapper (`batch/decisions/reviewed_by/timestamp`),
rejects unknown decision ids (unknown ids → 422) — exact-coverage and
unresolved-row gates are enforced at approve/collect, not at draft —
and logs one `SCREEN_DECISIONS` event. It does **not** approve,
review, mint, stage, publish, or gate anything — no approval, review, or
generation route exists. The Action Spec names what must not bypass it.

## 2. Binding rules (normative)

- **R1 — backend-resolved references.** The workspace is bound once at app
  state (`request.app.state.workspace`, cf. `_ws` at `workspace.py:24`).
  Every project/batch reference in a response is resolved server-side from
  that binding. The browser never supplies a filesystem path, a workspace
  directory, or a file name outside the enumerated safe-name parameters
  (`synthesis/{filename}`, `phase4/{filename}`, both already guarded by
  `_safe_join`).
- **R2 — no caller-minted identities.** The browser never supplies a
  workspace identity, run id, protocol/corpus fingerprint, batch artifact
  id, or generation id as authority. Identity comes from the recorded
  workspace (`project.json: registered_workspace_id`, resolved via
  `workspace.identity.require_recorded_identity`) and from the
  manifest/registry parents the server reads. Caller-supplied ids are
  refused (§5 + §6(2)).
- **R3 — no direct browser-to-workspace-file access.** The browser reads
  only through these endpoints. There is no static mount of the workspace,
  no file-URL fallback, no "open the journal directly" affordance.
- **R4 — missing data is explicit.** Absent files/shape gaps render as a
  typed `missing` member with a `reason` (e.g. `NOT_PREPARED`,
  `NO_DECISIONS_YET`, `NO_GENERATION`), never as silent `null`, never as
  `0`/`[]` that implies a measured empty, never as an inferred count.
  (Precedent: `workspace_meta`'s `-> missing:` markers; `harvest_corpus`'s
  `manifest: None` becomes a typed `missing` in the new shapes.)
- **R5 — reads never mutate or repair.** A GET performs no write, no
  manifest projection, no INDEX refresh, no tmp sweep, no lock
  acquisition, no `recover_partial`. Crash staging stays invisible until
  an operator runs the explicit recovery path.
- **R6 — publication outputs serve only when CURRENT.** `included.json`,
  `excluded.json`, `conflicts.json`, `prisma_screening_report.md`,
  `prisma_report.json` are served to the UI only with a CURRENT generation
  per `authority.generations.require_current_generation`. Any other status
  → the typed currentness error in §5, not the file bytes, not a legacy
  fallback.

## 3. Shapes

All shapes are JSON objects. Field order is insignificant. Timestamps are
exact strings from the artifacts, never reformatted. Counts are
server-computed from canonical bytes, never browser-inferred (UI-02
precedent).

### (a) Project summary + workflow readiness

```json
{
  "shape": "ui07.project-summary-v1",
  "workspace_id": "WSP-EXAMPLE-00000000000000000000000000000000",
  "project_id": "example-review",
  "protocol": { "present": true, "fingerprint": "sha256:EXAMPLE" },
  "run": { "screening_run_id": "RUN-EXAMPLE", "batches": 2, "batches_resolved": 1 },
  "readiness": {
    "screening_prepared": true,
    "all_batches_resolved": false,
    "publication": { "status": "STALE", "code": "GENERATION_STALE", "generation_id": "GEN-EXAMPLE" }
  },
  "missing": []
}
```

`missing` lists each absent prerequisite with reason, e.g.
`{"file": "protocol.json", "reason": "NOT_PREPARED"}`. `publication`
reuses the §(e) status object verbatim so the summary can never disagree
with the publication endpoint.

Field discipline: `shape` (string, required, always
`ui07.project-summary-v1`); `workspace_id` (string, required,
server-resolved per R1, never caller-minted per R2); `project_id`
(string, required); `protocol` (object, required; `present`: boolean,
required; `fingerprint`: string|null, required — null when the protocol
is absent, with the `NOT_PREPARED` entry in `missing`); `run`
(object|null, required — null when screening was never prepared, with
the `NOT_PREPARED` entry in `missing`); `readiness` (object, required;
booleans required); `missing` (array, required, possibly empty — absent
prerequisites only, never silent null per R4). `publication.status` and
`publication.code` follow the §(e) enum verbatim (`code` is null if and
only if `status` is `CURRENT`).

### (b) Screening batches + records

```json
{
  "shape": "ui07.screening-batches-v1",
  "run_id": "RUN-EXAMPLE",
  "count": 1,
  "batches": [
    {
      "batch_index": 0,
      "batch_file": "batch_000.json",
      "items": 25,
      "decisions_file": "batch_000_decisions.json",
      "decisions_count": 25,
      "collected": true,
      "coverage": "COMPLETE",
      "unresolved_rows": []
    }
  ],
  "missing": []
}
```

Per-record rows (study citation, abstract, criteria refs, decision,
reason, uncertainty, source locators) reuse the canonical decision-file
bytes and the worker recommendation bytes as stored — the server does not
re-derive, summarize, or reword them. `coverage` is `COMPLETE` only when
the decision ids exactly cover the parent batch candidate set (AG-02
`check_exact_coverage`); otherwise the batch carries
`coverage: INCOMPLETE` plus the missing/extra id lists from the gate.
`unresolved_rows` names every non-terminal row (`PENDING_REVIEW`,
`MAYBE`, `CONFLICT`, any other non-`INCLUDE`/`EXCLUDE` value).

Field discipline: `shape` (string, required, always
`ui07.screening-batches-v1`); `run_id` (string|null, required — null if
and only if screening was never prepared, exactly the §4 empty example
with `NOT_PREPARED` in `missing`); `count` (integer, required,
server-computed, never browser-inferred); `batches` (array, required);
`missing` (array, required, possibly empty, per R4). Per batch:
`batch_index` (integer, required); `batch_file` (string, required);
`items` (integer, required, server-computed); `decisions_file`
(string|null, required — null when the sidecar is absent, with the
`NO_DECISIONS_YET` entry in `missing` per §5); `decisions_count`
(integer|null, required — null when the sidecar is absent);
`collected` (boolean, required); `coverage` (string, required — enum
`COMPLETE` | `INCOMPLETE`); `missing_ids` / `extra_ids` (arrays of
string, present if and only if `coverage` is `INCOMPLETE`);
`unresolved_rows` (array of string, required — row keys, empty when none);
`binding` (object, optional — present if and only if the batch binding
is non-current, as in the §4 stale example): `{state, reason}` with
`state` (string, required — enum currently `STALE_BINDING` only: the
parent batch was superseded after acceptance, re-resolve before
approval) and `reason` (string, required when `binding` is present —
human-readable cause). When the binding is current the member is absent
rather than carrying a `CURRENT` state, matching the §3(b) populated
example.

Per-record row type `ui07.screening-row-v1` — a presentation join of the
stored batch-paper bytes (identity, citation, abstract) and the stored
decision bytes (decision, reasons, uncertainty, refs, locators); the
server re-derives nothing:

- `study_id` (string, required) — the canonical row key;
  `workspace_id` (string, optional alias; at least one of the two is
  present — the coverage key per AG-02 `check_exact_coverage`, which
  keys on `workspace_id` or `study_id`).
- `citation` (string, required when the parent batch paper carries one;
  otherwise the §(c) missing rule applies).
- `abstract` (string, required when the source record carries one;
  otherwise the §(c) `NO_ABSTRACT` missing rule applies — the abstract
  the UI-04 journey renders (GATES §8 S1; UI-04 capsule Task) is served
  here exactly as stored, never translated, never synthesized).
- `decision` (string, required) — the canonical vocabulary of §3(d):
  terminal `INCLUDE` / `EXCLUDE`; unresolved `PENDING_REVIEW` /
  `MAYBE` / `CONFLICT` / any other non-terminal value. This supports the
  UI-04 S2/S3 contract: choices are distinct and none is preselected (a
  row with no researcher act carries the worker `PENDING_REVIEW`, never
  a defaulted `INCLUDE`), and a researcher-resolved `EXCLUDE` row
  carries a non-empty reason (the S3 exclude-requires-reason rule),
  while worker `PENDING_REVIEW` rows carry empty `reasons` by
  construction.
- `reasons` (array of string, required — possibly empty; worker rows
  carry `[]`).
- `uncertainty` (string, required — worker rows carry `UNREVIEWED`).
- `criterion_refs` (object, optional —
  `{inclusion: string[], exclusion: string[]}` criterion ids as stored).
- `source_locators` (object, optional — `{doi, url, venue, year}` as
  stored; absent locators are an explicit `missing` entry per §(c),
  never a synthesized placeholder).

Illustrative row (synthetic values only, asserting nothing about any
real workspace):

```json
{
  "shape": "ui07.screening-row-v1",
  "study_id": "STUDY-EXAMPLE-001",
  "workspace_id": "WSP-EXAMPLE-11111111111111111111111111111111",
  "citation": "Illustrative citation.",
  "abstract": "Illustrative abstract text served exactly as stored.",
  "decision": "PENDING_REVIEW",
  "reasons": [],
  "uncertainty": "UNREVIEWED",
  "criterion_refs": { "inclusion": ["INC-EXAMPLE-1"], "exclusion": ["EXC-EXAMPLE-1"] },
  "source_locators": { "doi": "10.0000/example", "url": "https://example.invalid/record", "venue": "Illustrative venue", "year": 2024 }
}
```

### (c) Criterion / source references

```json
{
  "shape": "ui07.criterion-refs-v1",
  "protocol_fingerprint": "sha256:EXAMPLE",
  "inclusion": [{ "id": "INC-EXAMPLE-1", "text": "Illustrative criterion text." }],
  "exclusion": [{ "id": "EXC-EXAMPLE-1", "text": "Illustrative criterion text." }],
  "sources": [
    {
      "workspace_id": "WSP-EXAMPLE-11111111111111111111111111111111",
      "citation": "Illustrative citation.",
      "abstract": "Illustrative abstract text served exactly as stored.",
      "doi": "10.0000/example",
      "url": "https://example.invalid/record",
      "venue": "Illustrative venue",
      "year": 2024
    }
  ],
  "missing": []
}
```

Criteria come from the protocol's `screening_criteria` as stored in the
batch envelope; sources come from the batch papers plus
`literature/verified.json` locators as stored. No DOI, URL, venue, year,
abstract, or quote is invented; a record without locators carries them as an
explicit `missing` entry, never as a synthesized placeholder.

`abstract` (string) is required when the source record carries one and
absent otherwise: a record with no abstract carries an explicit `missing`
entry with reason `NO_ABSTRACT` (e.g.
`{"study": "STUDY-EXAMPLE-001", "reason": "NO_ABSTRACT"}`), never a
synthesized placeholder, never silent null (R4). The abstract served
here is the one the UI-04 journey renders — study citation, abstract,
criteria panel per the UI-04 capsule Task, with all fixture text
direction-isolated per GATES §8 S1 — served exactly as stored, never
translated, never summarized. This rule governs the UI-07 shapes only; it
rewrites no stored batch bytes (§1.1: existing routes' storage behavior
is unchanged).

Field discipline: `shape` (string, required, always
`ui07.criterion-refs-v1`); `protocol_fingerprint` (string, required,
server-resolved per R1, never caller-minted per R2); `inclusion` /
`exclusion` (arrays, required, possibly empty — each entry
`{id: string (required), text: string (required)}`); per source:
`workspace_id` (string, required); `citation` (string, required when the
batch paper carries one, otherwise a `missing` entry per R4);
`abstract` (string, required-when-carried, otherwise the `NO_ABSTRACT`
`missing` entry above); `doi` / `url` / `venue` (string, optional);
`year` (integer, optional); `missing` (array, required, possibly empty,
per R4).

### (d) Recommendations, unresolved states, override history

```json
{
  "shape": "ui07.review-state-v1",
  "batch_index": 0,
  "recommendation": {
    "present": true,
    "schema": "harness-screening-recommendation-v1",
    "revision": 1,
    "method": "DETERMINISTIC_CLI",
    "rows_pending": 25
  },
  "resolution": { "resolved": 25, "total": 25, "unresolved_rows": [] },
  "override": {
    "superseded": true,
    "snapshot_fingerprint": "sha256:EXAMPLE",
    "recommendation_sha256": "sha256:EXAMPLE",
    "final_decision_sha256": "sha256:EXAMPLE"
  },
  "review": { "present": true, "approval_fingerprint": "sha256:EXAMPLE" },
  "deferral": { "present": false },
  "missing": []
}
```

Vocabulary is fixed: worker rows are `PENDING_REVIEW` with empty
`reasons` and `UNREVIEWED` uncertainty (worker makes no judgments);
unresolved-for-finalize values are `MAYBE`/`CONFLICT` (AG-02
`UNRESOLVED_VALUES`) plus worker-pending rows and any other
non-terminal value (AG-04 `_require_resolved`); terminal values are
exactly `INCLUDE`/`EXCLUDE`. Override history reports the AG-03B
`supersede` chain (original preserved, new revision bound) without
rewriting it.

Field discipline: `shape` (string, required, always
`ui07.review-state-v1`); `batch_index` (integer, required);
`recommendation` (object, required; `present`: boolean, required — when
`false` the members below it are absent; when `true`: `schema` (string,
required, e.g. `harness-screening-recommendation-v1`), `revision`
(integer, required), `method` (string, required, e.g.
`DETERMINISTIC_CLI`), `rows_pending` (integer, required,
server-computed)); `resolution` (object, required; `resolved` /
`total`: integers, required, server-computed; `unresolved_rows`: array
of string, required, empty when none); `override` (object, required;
`superseded`: boolean, required — the fingerprint members below are
required if and only if `superseded` is `true`:
`snapshot_fingerprint` / `recommendation_sha256` /
`final_decision_sha256`, each string); `review` (object, required;
`present`: boolean, required — `approval_fingerprint` (string) present
if and only if `present` is `true`); `deferral` (object, required;
`present`: boolean, required); `missing` (array, required, possibly
empty, per R4).

### (e) Publication / currentness status

The `status` is the honest output of
`authority.generations.require_current_generation` — pure read, no
writes. The five statuses and their codes are `CURRENT` (no code),
`STALE` (`GENERATION_STALE`), `SUPERSEDED` (`GENERATION_SUPERSEDED`),
`MISMATCHED` (`GENERATION_MISMATCHED`), `LEGACY_UNVERIFIED`
(`GENERATION_LEGACY_UNVERIFIED`). `details` carries the gate's evidence
(generation id, mismatched files, underlying approval code).

```json
{
  "shape": "ui07.publication-status-v1",
  "status": "CURRENT",
  "code": null,
  "generation_id": "GEN-EXAMPLE",
  "outputs": {
    "included.json": "sha256:EXAMPLE",
    "excluded.json": "sha256:EXAMPLE",
    "conflicts.json": "sha256:EXAMPLE",
    "prisma_screening_report.md": "sha256:EXAMPLE",
    "prisma_report.json": "sha256:EXAMPLE"
  },
  "message": "Illustrative message from the currentness gate.",
  "details": { "generation_id": "GEN-EXAMPLE" }
}
```

When `status` is anything but `CURRENT`, `outputs` digests are still
reported (they are manifest facts, not served file bytes) and the
publication files themselves are **not** served — the UI receives this
status object instead. Downgrade prevention is inherited from the gate:
absent `generation.json` beside surviving authorized material
(staged approval, registry/MANIFEST accepted lineage) reports
`MISMATCHED`, never `LEGACY_UNVERIFIED`.

### (f) Journey-scoped audit info

```json
{
  "shape": "ui07.audit-feed-v1",
  "total": 3,
  "offset": 0,
  "limit": 100,
  "items": [
    {
      "timestamp": "2026-01-01T00:00:00+00:00",
      "event_id": "EVT-EXAMPLE-1",
      "action": "SCREEN_DECISIONS",
      "agent_or_tool": "scholar-harness-console",
      "description": "Illustrative audit description.",
      "status": "SUCCESS"
    }
  ]
}
```

Projection of the existing `GET /api/v1/audit/events` (newest-first,
`action`/`agent` filters, `total/offset/limit/items`), scoped to the
screening journey by `action` filter. The UI never rewrites, reorders,
or appends events; technical timestamps stay exact (UI-06 packet
constraint, restated here so the shape cannot drift).

### (g) Paged corpus

```json
{
  "shape": "ui07.corpus-page-v1",
  "kind": "excluded",
  "total": 1,
  "corpus_total": 13506,
  "offset": 0,
  "limit": 25,
  "records": [
    {
      "shape": "ui07.corpus-record-v1",
      "workspace_id": "SCI-EXAMPLE-1",
      "title": "Illustrative excluded record.",
      "year": 2021,
      "provider": "crossref",
      "doi": null,
      "abstract": "Illustrative abstract.",
      "decision": "EXCLUDE",
      "confidence": 0.8,
      "reasoning": "Illustrative stored reasoning.",
      "reason_code": "WRONG_TASK",
      "criterion": "EXC-02",
      "lane": "mutual_exclude"
    }
  ],
  "missing": []
}
```

`GET /api/v1/ui/corpus/{kind}` with `kind` ∈ {`included`, `excluded`},
`limit` 1–200 (default 25), `offset` ≥ 0, and optional `q`/`reason`
filters. Filtering runs over the whole stored corpus **before** the page is
cut: `total` is the matched count, `corpus_total` the stored count. The screen
never parses `literature/included.json` / `excluded.json` itself — the console
projects `screening.decision`, `screening_reasoning`, provenance `reason_code`,
the violated-or-matched criterion and the lane, and an absent value stays
`null` rather than being invented. A missing dump is `200` with an explicit
`missing` entry (`CORPUS_MISSING`) and an empty page, not a transport error.
Reads are pure: no file is repaired or rewritten. Refusals follow §2:
caller-minted identity keys → `422 CALLER_IDENTITY_REFUSED`; unknown kind →
`404 CORPUS_KIND_UNKNOWN`; unparseable dump → `500 CORPUS_UNREADABLE`.

## 4. Illustrative acceptance examples

Each of the two stateful shapes below carries three examples: populated,
empty (explicit `missing`, never null-silence), and stale.

**Batches — populated:** §3(b) above (1 batch, `coverage: COMPLETE`,
`collected: true`).

**Batches — empty:**

```json
{
  "shape": "ui07.screening-batches-v1",
  "run_id": null,
  "count": 0,
  "batches": [],
  "missing": [{ "file": "literature/screening/MANIFEST.json", "reason": "NOT_PREPARED" }]
}
```

**Batches — stale (parent superseded after resolution):**

```json
{
  "shape": "ui07.screening-batches-v1",
  "run_id": "RUN-EXAMPLE",
  "count": 1,
  "batches": [
    {
      "batch_index": 0,
      "batch_file": "batch_000.json",
      "items": 25,
      "decisions_file": "batch_000_decisions.json",
      "decisions_count": 25,
      "collected": false,
      "coverage": "COMPLETE",
      "unresolved_rows": [],
      "binding": { "state": "STALE_BINDING", "reason": "Parent batch superseded after acceptance; re-resolve before approval." }
    }
  ],
  "missing": []
}
```

**Publication — populated (CURRENT):** §3(e) above.

**Publication — empty (true legacy, no authorized material anywhere):**

```json
{
  "shape": "ui07.publication-status-v1",
  "status": "LEGACY_UNVERIFIED",
  "code": "GENERATION_LEGACY_UNVERIFIED",
  "generation_id": null,
  "outputs": {},
  "message": "Illustrative: no screening generation record beside the outputs; legacy outputs are not authorized-current.",
  "details": { "generation_path": "literature/screening/generation.json" }
}
```

**Publication — stale (output digest drift):**

```json
{
  "shape": "ui07.publication-status-v1",
  "status": "STALE",
  "code": "GENERATION_STALE",
  "generation_id": "GEN-EXAMPLE",
  "outputs": { "included.json": "sha256:EXAMPLE" },
  "message": "Illustrative: included.json is missing or no longer matches the recorded digest.",
  "details": { "generation_id": "GEN-EXAMPLE", "output": "included.json" }
}
```

## 5. Error states (typed, stable codes)

| Condition | Code | HTTP | UI displays |
|---|---|---|---|
| Arbitrary filesystem path / traversal in a file parameter | `INVALID_FILE_NAME` | 400 | Refusal: the request named storage outside the served surface. |
| Caller-supplied workspace/run/identity/fingerprint/artifact id presented as authority | `CALLER_IDENTITY_REFUSED` | 422 | Refusal: identity comes from the bound workspace, never the browser. |
| Batch (or its decisions sidecar parent) absent | `BATCH_MISSING` (`missing file: batch_NNN.json`) | 404 | Explicit missing-file state naming the batch; offer prepare, not fabrication. |
| Decisions sidecar absent while batch exists | `NO_DECISIONS_YET` (in `missing`, HTTP 200 with `decisions: null` + reason) | 200 | "Nothing resolved yet" — displayable, never approvable. |
| Canonical JSON unparseable | `UNPARSEABLE_JSON` | 500 | Infrastructure error; nothing is served as if parsed. |
| Publication requested while generation is STALE/SUPERSEDED/MISMATCHED | gate code (`GENERATION_STALE`, `GENERATION_SUPERSEDED`, `GENERATION_MISMATCHED`) | 409 | Currentness refusal with the gate's message + details; no file bytes. |
| Publication with no generation and no authorized material | `GENERATION_LEGACY_UNVERIFIED` | 409 | "Legacy outputs are not authorized-current"; no silent legacy serve. |
| Journal unreadable line | skipped with debug log (existing `audit_events` behavior) | 200 | Feed serves parseable events; no refusal for one bad line. |

## 6. Negative cases (must hold at review)

1. A request naming an arbitrary path (`../../project.json`, an absolute
   path, a second workspace) is refused (400 via `_safe_join` or
   equivalent); the server never resolves caller paths.
2. A request carrying a caller-minted `workspace_id`/`run_id`/fingerprint
   is refused (422); the values are ignored, never bound.
3. A missing batch yields the explicit 404 shape naming
   `batch_NNN.json`, not an empty 200, not a guessed neighbor batch.
4. A stale generation yields the typed currentness error (§5), not the
   stale file bytes, not a legacy fallback.
5. No endpoint offers direct file access (no workspace mount, no file
   URL, no journal path disclosure beyond the existing safe-name
   parameters).
6. No GET writes, repairs, sweeps, or refreshes — verified by asserting
   byte-identical workspace state before/after a read battery.

## 7. Open questions

- **OQ-P1 — pagination shape for per-record rows.** §3(b) fixes the
  batch-level envelope; the row-level paging (`limit/offset` vs cursor)
  for large batches is deferred to implementation review. Reads must
  still serve exact stored bytes in whatever page size is chosen.
- **OQ-P2 — criterion-text sourcing when batch envelope and protocol
  disagree.** The batch envelope carries the criteria refs the worker
  preserved; if the live `protocol.json` fingerprint differs, the shape
  reports both fingerprints and marks the section stale rather than
  choosing silently. The exact stale-view precedence needs AG-03C-owner
  confirmation.
- **OQ-P3 — graph/harvest inclusion in the screening journey.** The
  existing `assets/graph` and `harvest/corpus` routes are out of the
  UI-04 journey; whether UI-07 serves them or leaves them to UI-05/06 is
  deferred. Nothing in this spec authorizes new graph/harvest shapes.

## 8. Traceability

- SPEC-01 (read-shapes): §3 + §4.
- SPEC-02 (error-states): §5 + §6(3–5).
- SPEC-03 (no-arbitrary-paths): R1–R3, §6(1–2, 5).
- SPEC-04 (currentness-on-reads): R6, §3(e), §4 publication examples, §5.
