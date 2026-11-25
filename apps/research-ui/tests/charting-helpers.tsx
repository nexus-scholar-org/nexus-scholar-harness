import { act, render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { ChartingPage } from "@/components/charting-page";
import { ChartingStudyPage } from "@/components/charting-study";
import type { Locale } from "@/i18n";
import { ChartingReport } from "@/components/charting-report";
import type { Amendment, Attachment, Cell, ChartingEvent, ChartingForm, ChartingMethods, ChartingRow, ChartingTable, FetchPlan, FetchRun, FormColumn, Fulltext, LastExport, LastLookup, ManifestRow, PendingFetch, PrismaGroup } from "@/lib/charting-api";

/**
 * A small in-memory charting engine for the screen's tests (M12a Parts A and B).
 * It answers in the shapes of `src/scholar_harness/console/api/charting.py`
 * (`tests/console/test_charting_api.py` and `test_charting_form_api.py` show
 * each): the rows, the events route with per-event results and the touched
 * rows, the attachment route, the CSV of either view, the form (PUT, with the
 * reason asked once a value exists and `CHARTING_FORM_STALE` on an old version),
 * "End pilot" and the one-study read. It applies status, decision and cell
 * events the way the engine does (the value of the newest event, `heads` or the
 * cell's `event_id` naming it), marks a cell "Chart again" when its column's type
 * changes, an option it uses is removed or its column is split, merged or
 * replaced (the engine's `diff` rule: one into several, several into one, one
 * into one), and refuses an
 * event for a record that is not kept (`RECORD_NOT_KEPT`).
 */

export interface Call {
  method: string;
  path: string;
  body?: unknown;
}

export interface FakeEngine {
  table: ChartingTable;
  calls: Call[];
  /** Answer every request with this instead (a code, or "unreachable" for a failed fetch). */
  fail?: { status: number; code: string } | "unreachable";
  /** Refuse each event of these studies with this code. */
  refuse?: Record<string, string>;
  /** Hold the table read until the test releases it. */
  hold?: Promise<void>;
  /** Answer the form's PUT with this refusal instead. */
  formFail?: { status: number; code: string };
  /** Part F: the look-up of open-access copies (see `FakeFetch`). */
  fetch: FakeFetch;
  /** Part C: the answer of `GET /charting/methods` (`makeMethods()` when absent). */
  methods?: ChartingMethods;
  /** Part C: answer `GET /charting/methods` with this refusal instead. */
  methodsFail?: { status: number; code: string };
  /** Part C: answer an export with this refusal instead (`"unreachable"` for a failed fetch). */
  exportFail?: { status: number; code: string } | "unreachable";
  /** Part C: hold an export's answer until the test releases it ("Preparing the file"). */
  exportHold?: Promise<void>;
}

// ------------------------------------------------------------------ Part C: the PRISMA full-text counts and the methods block

export const XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";

/** One group of the PRISMA full-text counts (`report.py` `_empty`), all zero unless given. */
export function prismaGroup(over: Partial<PrismaGroup> = {}): PrismaGroup {
  return {
    sought: 0,
    not_retrieved: 0,
    not_retrieved_reasons: {},
    assessed: 0,
    excluded: 0,
    exclusion_reasons: {},
    included: 0,
    awaiting_retrieval: 0,
    to_confirm: 0,
    retrieved_not_assessed: 0,
    assessed_without_full_text: 0,
    not_retrieved_decided: 0,
    not_retrieved_included: 0,
    not_retrieved_excluded: 0,
    ...over,
  };
}

/** The databases arm of the default methods answer: numbers no other part of the fixture holds. */
export const DATABASES: PrismaGroup = prismaGroup({
  sought: 12,
  not_retrieved: 2,
  not_retrieved_reasons: { "No access or paywalled": 1, "Not found": 1 },
  assessed: 9,
  excluded: 3,
  exclusion_reasons: { "EXC-01": 2, OTHER: 1 },
  included: 6,
  awaiting_retrieval: 1,
  assessed_without_full_text: 1,
});

export const CHASING: PrismaGroup = prismaGroup({
  sought: 5,
  not_retrieved: 1,
  not_retrieved_reasons: { "Authors did not reply": 1 },
  assessed: 3,
  excluded: 1,
  exclusion_reasons: { "FAILS-INC-01": 1 },
  included: 2,
  awaiting_retrieval: 1,
  to_confirm: 1,
});

export const TOTAL: PrismaGroup = prismaGroup({
  sought: 17,
  not_retrieved: 3,
  not_retrieved_reasons: { "No access or paywalled": 1, "Not found": 1, "Authors did not reply": 1 },
  assessed: 12,
  excluded: 4,
  exclusion_reasons: { "EXC-01": 2, OTHER: 1, "FAILS-INC-01": 1 },
  included: 8,
  awaiting_retrieval: 2,
  to_confirm: 1,
  assessed_without_full_text: 1,
});

export const PARAGRAPH =
  "Of 17 reports sought for retrieval, 3 were not retrieved (No access or paywalled: 1; Not found: 1; Authors did not reply: 1). 12 reports were assessed at full text by one reviewer; 4 were excluded (EXC-01 Not a crop field: 2; FAILS-INC-01 UAV imagery: 1; Other: 1) and 8 were included. The counts are of reports; reports of the same study were not linked.";

/** `GET /api/v1/charting/methods` in the engine's shape (`report.py` `methods()`). */
export function makeMethods(
  over: { databases?: PrismaGroup; chasing?: PrismaGroup; total?: PrismaGroup; methods?: Partial<ChartingMethods>; figures?: Partial<ChartingMethods["figures"]> } = {},
): ChartingMethods {
  const databases = over.databases ?? DATABASES;
  const chasing = over.chasing ?? CHASING;
  const total = over.total ?? TOTAL;
  return {
    shape: "charting.methods-v1",
    sentences: [PARAGRAPH],
    paragraph: PARAGRAPH,
    figures: {
      prisma: {
        schema: "nexus.charting-prisma-fulltext.v1",
        unit: "reports",
        rounds: [
          { round: 1, arm: "databases", label: "Databases", generation_id: "gen-1", published_at: "2026-11-21T10:00:00Z", ...databases },
          { round: 2, arm: "citation_searching", label: "Citation chasing", generation_id: "gen-2", published_at: "2026-11-21T12:00:00Z", ...chasing },
        ],
        arms: { databases, citation_searching: chasing },
        total,
      },
      open_access: { used: 1, discarded: 0, services: ["Unpaywall"] },
      reviewers: { fulltext_decisions: 1, charting: 1 },
      charted: 5,
      not_charted: 3,
      cells_open: 7,
      required_open: 2,
      pilot: 2,
      amendments: [],
      ...over.figures,
    },
    caveats: [
      "2 reports are not yet retrieved or not yet assessed (2 awaiting retrieval, 0 retrieved and not assessed); the counts describe the work so far.",
      "1 fetched copy waits for the reviewer's confirmation and is not counted as retrieved.",
    ],
    not_stated: ["The sentences give totals over every round; the PRISMA counts are split by round."],
    sources: [
      { name: "included.json", path: "literature/included.json", digest: `sha256:${"d".repeat(64)}` },
      { name: "researcher_local.jsonl", path: "charting/events/researcher_local.jsonl", digest: `sha256:${"e".repeat(64)}` },
    ],
    ...over.methods,
  };
}

/** What `charting/last_export.json` holds after an export (`table.export`). */
export function lastExport(over: Partial<LastExport> = {}): LastExport {
  return {
    at: "2026-11-21T14:32:00Z",
    format: "xlsx",
    view: null,
    file_name: "charting-20261121T143200Z.xlsx",
    sha256: "c".repeat(64),
    rows: 68,
    not_charted: 3,
    cells_open: 7,
    required_open: 2,
    ...over,
  };
}

/**
 * Part F: the fake's look-up (`src/scholar_harness/charting/fetch.py` in small).
 * `GET /charting/fetch` answers `runs[0]` and moves on to the next answer each
 * time, the last one staying; a start answers `started` and puts `afterStart`
 * in `runs`; the plan is computed from the rows as the engine's `select` does
 * unless `plan` is given; `mailto: false` refuses the plan and the start with
 * `MAILTO_NOT_SET`; `manifest` holds each record's rows for "What was tried".
 */
export interface FakeFetch {
  runs: FetchRun[];
  started?: FetchRun;
  afterStart?: FetchRun[];
  startFail?: { status: number; code: string };
  plan?: FetchPlan;
  /** Hold the plan's answer until the test releases it ("Counting…"). */
  planHold?: Promise<void>;
  mailto?: boolean;
  openalexKey?: boolean;
  manifest: Record<string, ManifestRow[]>;
  /** Each start's body, in order. */
  starts: unknown[];
  /** Fail every read of the run (`"unreachable"` or a code), after the first `failAfter` answers. */
  pollFail?: { status: number; code: string } | "unreachable";
  /** What each confirm wrote, so its undo restores it (the engine's `links`). */
  confirmed: Record<string, { pending: PendingFetch; attachment: Attachment | null; status: Record<string, string | null>; attachmentId?: string; statusId?: string }>;
  discarded: Record<string, PendingFetch>;
}

export const IDLE_RUN: FetchRun = { state: "idle", run_id: null };

/** A waiting file as the engine shows it on a row (`fetch.pending_view`). */
export function pendingFetch(over: Partial<PendingFetch> = {}): PendingFetch {
  return {
    manifest_row: "FMR-000000000000000000000001",
    run_id: "FR-000000000000000000000001",
    source: "Unpaywall",
    source_name: "Europe PMC",
    host: "europepmc.org",
    host_type: "repository",
    address: "https://europepmc.org/articles/PMC1/pdf/paper.pdf",
    version: "publishedVersion",
    version_label: "publishedVersion",
    licence: "cc-by",
    size: 1_258_291,
    sha256: "b".repeat(64),
    identity: "doi found",
    at: "2026-11-22T14:30:00Z",
    duplicate_of: [],
    ...over,
  };
}

export function lastLookup(over: Partial<LastLookup> = {}): LastLookup {
  return { run_id: "FR-000000000000000000000001", manifest_row: "FMR-000000000000000000000009", at: "2026-11-22T14:31:00Z", outcome: "NO_OPEN_COPY_LISTED", message: null, try_later: false, same_as_discarded: false, ...over };
}

/** A row whose fetched file waits; its earlier status (To get by default) stays. */
export function waitingRow(i: number, pending: Partial<PendingFetch> = {}, over: Partial<ChartingRow> = {}): ChartingRow {
  const base = makeRow(i, over);
  const fulltext: Fulltext = { ...base.fulltext, pending_fetch: pendingFetch({ manifest_row: `FMR-${String(i).padStart(24, "0")}`, sha256: String(i % 10).repeat(64), ...pending }), last_lookup: lastLookup({ outcome: "ACQUIRED", manifest_row: `FMR-${String(i).padStart(24, "0")}` }) };
  return { ...base, fulltext };
}

/**
 * A record no longer kept whose fetched file still waits, in the engine's shape for such a row
 * (`table.table`, since f9f5f287): the record's summary with no authors, abstract, venue, link or
 * arXiv id, `kept: false`, and its fetch state (waiting file, last look-up, discard) as for a kept row.
 */
export function noLongerKeptWaitingRow(i: number, pending: Partial<PendingFetch> = {}): ChartingRow {
  const row = waitingRow(i, pending, { kept: false, authors: [], abstract: null, venue: null, url: null, arxiv_id: null, ta_reason: "" });
  return { ...row, fulltext: { ...row.fulltext, discarded_fetch: null } };
}

/** A run record as `GET /api/v1/charting/fetch` answers it (`fetch._view`). */
export function runView(over: Partial<FetchRun> = {}): FetchRun {
  return {
    state: "running",
    run_id: "FR-000000000000000000000002",
    total: 214,
    reached: 0,
    found: 0,
    downloaded: 0,
    failed_checks: 0,
    errors: {},
    no_open_copy: 0,
    no_direct_pdf: 0,
    try_later: 0,
    skipped_no_id: 0,
    not_reached: 0,
    providers: ["unpaywall"],
    contact_email_set: true,
    openalex_key_set: false,
    now: { phase: "starting", host: null },
    recent_requests: [],
    started_at: "2026-11-22T14:00:00Z",
    finished_at: null,
    error: null,
    check_failures: {},
    lookup_failures: [],
    ...over,
  };
}

/** A manifest row of `charting/fetch_manifest.jsonl` (`scholar_pdf/manifest.py` with the run's fields). */
export function manifestRow(over: Partial<ManifestRow> = {}): ManifestRow {
  return {
    row_id: "FMR-000000000000000000000009",
    run_id: "FR-000000000000000000000001",
    study_id: "STU-001",
    doi: "10.3390/rs1001",
    outcome: "NO_OPEN_COPY_LISTED",
    status: "UNRESOLVED",
    file: null,
    size: null,
    sha256: null,
    address: null,
    redirects: [],
    http_status: null,
    version: null,
    version_label: null,
    license: null,
    provider: null,
    checks: {},
    lookups: [
      { service: "unpaywall", state: "ANSWERED", http_status: 200, error: null },
      { service: "openalex", state: "NOT_ASKED", http_status: null, error: "OpenAlex was not asked (SCHOLAR_OPENALEX_KEY is not set)" },
    ],
    requests: [],
    time: "2026-11-22T14:31:00Z",
    ...over,
  };
}

export function makeRow(i: number, over: Partial<ChartingRow> = {}): ChartingRow {
  const id = `STU-${String(i).padStart(3, "0")}`;
  return {
    study_id: id,
    title: `Study number ${i}`,
    authors: ["Sa, I."],
    year: 2018 + (i % 5),
    venue: "Remote Sensing",
    doi: `10.3390/rs${1000 + i}`,
    url: null,
    abstract: null,
    arxiv_id: null,
    round: 1,
    arm: "databases",
    round_label: "Databases",
    generation_id: "gen-1",
    ta_decision: i % 3 === 0 ? "MAYBE" : "INCLUDE",
    ta_reason: "",
    kept: true,
    new_since: null,
    fulltext: { status: "to_get", requested_on: null, reason: null, reason_text: null, attachment: null, link: null },
    ft_decision: null,
    heads: { fulltext_status: null, fulltext_decision: null, attachment: null, link: null },
    ...over,
  };
}

export function counts(rows: ChartingRow[]): ChartingTable["counts"] {
  const live = rows.filter((r) => r.kept);
  const by = (test: (r: ChartingRow) => boolean) => live.filter(test).length;
  // Part F (question 1): a row whose fetched file waits is counted only in "to confirm".
  const waiting = (r: ChartingRow) => Boolean(r.fulltext.pending_fetch);
  return {
    kept: live.length,
    to_get: by((r) => r.fulltext.status === "to_get" && !waiting(r)),
    requested: by((r) => r.fulltext.status === "requested" && !waiting(r)),
    retrieved: by((r) => r.fulltext.status === "retrieved"),
    not_retrieved: by((r) => r.fulltext.status === "not_retrieved" && !waiting(r)),
    to_confirm: by(waiting),
    included: by((r) => r.ft_decision?.outcome === "INCLUDE"),
    excluded: by((r) => r.ft_decision?.outcome === "EXCLUDE"),
    to_decide: by((r) => !r.ft_decision),
    charted: by((r) => r.charted === true),
    not_charted: by((r) => !r.charted && r.ft_decision?.outcome !== "EXCLUDE"),
    pilot: by((r) => r.pilot === true),
  };
}

// ------------------------------------------------------------------ Part B: form and cells

export function makeColumn(id: string, over: Partial<FormColumn> = {}): FormColumn {
  return { column_id: id, name: id, definition: "", type: "text", options: [], required: false, from_protocol: id, derived_from: [], ...over };
}

/** The four columns of `tests/console/test_charting_form_api.py`, with their options, and a Yes/No one. */
export function uavColumns(): FormColumn[] {
  return [
    makeColumn("sensor_problems", { name: "Sensor problems addressed", definition: "Misregistration, missing band, change of camera", type: "several", options: ["Misregistration", "Missing band", "Change of camera"], required: true }),
    makeColumn("cameras", { name: "Cameras and evaluation design", definition: "Cameras, splits, cross-camera tests" }),
    makeColumn("n_images", { name: "Images", definition: "Number of images", type: "number" }),
    makeColumn("split", { name: "Data split", definition: "How the data are split", type: "one", options: ["Random tiles", "By field", "By date", "By camera"] }),
    makeColumn("cross_camera", { name: "Test camera absent from training", type: "yes_no", options: ["Yes", "No"], from_protocol: null }),
  ];
}

export function makeForm(columns: FormColumn[], over: Partial<ChartingForm> = {}): ChartingForm {
  return {
    schema: "nexus.charting-form.v1",
    version: 1,
    columns,
    pilot: { on: true, ended_at: null, ended_by: null, ended_at_version: null },
    amendments: [],
    has_values: false,
    ...over,
  };
}

export function emptyCell(over: Partial<Cell> = {}): Cell {
  return { state: null, value: null, note: null, where_from: null, pilot: false, chart_again: false, history: [], event_id: null, form_version: null, ...over };
}

/** A row with one empty cell per column (what the engine answers before any value). */
export function withCells(row: ChartingRow, columns: FormColumn[], cells: Record<string, Partial<Cell>> = {}): ChartingRow {
  const out: ChartingRow = { ...row, cells: Object.fromEntries(columns.map((c) => [c.column_id, emptyCell(cells[c.column_id])])) };
  return derive(out, columns);
}

function derive(row: ChartingRow, columns: FormColumn[]): ChartingRow {
  const cells = row.cells ?? {};
  const excluded = row.ft_decision?.outcome === "EXCLUDE";
  row.charted = columns.length > 0 && row.kept && !excluded && columns.every((c) => cells[c.column_id]?.state != null && !cells[c.column_id]?.chart_again);
  row.pilot = Object.values(cells).some((c) => c.pilot);
  row.no_full_text = row.fulltext.status !== "retrieved";
  return row;
}

/** Rows with the charting form: every row gets its cells. */
export function makeChartingTable(rows: ChartingRow[], columns: FormColumn[] = uavColumns(), over: Partial<ChartingTable> = {}, form: Partial<ChartingForm> = {}): ChartingTable {
  const full = rows.map((r) => (r.cells ? derive({ ...r }, columns) : withCells(r, columns)));
  return makeTable(full, { form: makeForm(columns, form), ...over });
}

function fits(column: FormColumn, state: string | null, value: unknown): string | null {
  if (state === null || state === "not_reported" || state === "not_applicable") return value == null ? null : "BODY_INVALID";
  if (state !== "value") return "BODY_INVALID";
  if (column.type === "text") return typeof value === "string" && value.trim() ? null : "CHARTING_VALUE_INVALID";
  if (column.type === "number") return typeof value === "number" && Number.isFinite(value) ? null : "CHARTING_VALUE_INVALID";
  if (column.type === "one" || column.type === "yes_no") return typeof value === "string" && column.options.includes(value) ? null : "CHARTING_VALUE_INVALID";
  return Array.isArray(value) && value.length > 0 && value.every((v) => column.options.includes(v)) ? null : "CHARTING_VALUE_INVALID";
}

export function makeTable(rows: ChartingRow[], over: Partial<ChartingTable> = {}): ChartingTable {
  return {
    shape: "charting.table-v1",
    screener_id: "researcher:local",
    publication: { status: "CURRENT", code: null, generation_id: "gen-1", published_at: "2026-11-21T10:00:00Z", round: 1 },
    rounds: [{ round: 1, arm: "databases", generation_id: "gen-1", published_at: "2026-11-21T10:00:00Z" }],
    chasing_pending: false,
    stale: false,
    changes: null,
    read_only: false,
    read_only_code: null,
    reason_options: [
      { code: "EXC-01", label: "Not a crop field", kind: "exclusion", category: null },
      { code: "FAILS-INC-01", label: "UAV imagery", kind: "fails_inclusion", category: null },
      { code: "OTHER", label: "Other", kind: "other", category: null },
    ],
    not_retrieved_reasons: ["no_access", "not_found", "no_reply", "other"],
    counts: counts(rows),
    rows,
    ...over,
  };
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json" } });
}

function apply(engine: FakeEngine, event: ChartingEvent): { event_id: string; result: string; refusal?: { code: string; message: string } } {
  const row = engine.table.rows.find((r) => r.study_id === event.study_id);
  const refused = engine.refuse?.[event.study_id];
  if (refused) return { event_id: event.event_id, result: "refused", refusal: { code: refused, message: refused.toLowerCase() } };
  if (!row || !row.kept) return { event_id: event.event_id, result: "refused", refusal: { code: "RECORD_NOT_KEPT", message: "not kept" } };
  const value = event.value as Record<string, string> | null;
  if (event.kind === "fulltext_status") {
    const v = value ?? { status: "to_get" };
    row.fulltext = { ...row.fulltext, status: v.status as never, requested_on: v.requested_on ?? null, reason: (v.reason ?? null) as never, reason_text: v.reason_text ?? null };
    row.heads = { ...row.heads, fulltext_status: event.event_id };
  } else if (event.kind === "fulltext_decision") {
    row.ft_decision = value ? ({ outcome: value.outcome, reason_code: value.reason_code ?? null, reason_text: value.reason_text ?? null } as never) : null;
    row.heads = { ...row.heads, fulltext_decision: event.event_id };
  } else if (event.kind === "attachment") {
    row.fulltext = { ...row.fulltext, attachment: (value as never) ?? null };
    row.heads = { ...row.heads, attachment: event.event_id };
  } else if (event.kind === "link") {
    row.fulltext = { ...row.fulltext, link: value ? (value as unknown as { url: string }).url : null };
    row.heads = { ...row.heads, link: event.event_id };
  } else if (event.kind === "cell") {
    const form = engine.table.form;
    const cellValue = event.value as { column_id: string; state: Cell["state"]; value: Cell["value"] };
    const column = form?.columns.find((c) => c.column_id === cellValue.column_id);
    if (!form || !column) return { event_id: event.event_id, result: "refused", refusal: { code: "CHARTING_COLUMN_UNKNOWN", message: "unknown column" } };
    const bad = fits(column, cellValue.state, cellValue.value);
    if (bad) return { event_id: event.event_id, result: "refused", refusal: { code: bad, message: bad.toLowerCase() } };
    const before = row.cells?.[column.column_id] ?? emptyCell();
    if (event.supersedes && event.supersedes !== before.event_id && !before.history.some((h) => h.event_id === event.supersedes)) {
      return { event_id: event.event_id, result: "refused", refusal: { code: "BODY_INVALID", message: "supersedes names no earlier event of this column" } };
    }
    const history = before.state !== null && before.event_id
      ? [...before.history, { state: before.state, value: before.value, note: before.note, where_from: before.where_from, at: null, form_version: before.form_version, event_id: before.event_id }]
      : before.history;
    const filled = cellValue.state !== null;
    row.cells = {
      ...row.cells,
      [column.column_id]: {
        state: cellValue.state,
        value: cellValue.state === "value" ? cellValue.value : null,
        note: filled ? event.note ?? null : null,
        where_from: filled ? event.where_from ?? null : null,
        pilot: filled && form.pilot.on,
        chart_again: false,
        history: history.slice(-5),
        event_id: event.event_id,
        form_version: form.version,
      },
    };
    if (filled) form.has_values = true;
    derive(row, form.columns);
  }
  // The row's charted, pilot and "no full text" follow every event, as the engine computes them.
  if (engine.table.form && row.cells) derive(row, engine.table.form.columns);
  return { event_id: event.event_id, result: "accepted" };
}

type EventAnswer = { event_id: string; result: string; refusal?: { code: string; message: string }; added_by_engine?: boolean };

const refused = (event: ChartingEvent, code: string): EventAnswer => ({ event_id: event.event_id, result: "refused", refusal: { code, message: code.toLowerCase() } });

/**
 * Part F's rules on the events route (`fetch.Hooks.refusal` and `expand`): a
 * status, a decision or an attachment on a row whose file waits is refused
 * `FETCH_FILE_WAITING`; a confirm brings the attachment (origin fetched) and
 * Retrieved with it, as two events of the engine's own; a discard needs one
 * reason (Other with words); a confirm or discard of a file that is not
 * waiting is `FETCH_NOT_PENDING`; an undo (a null value) restores the waiting file,
 * and takes back the attachment and the status the confirm wrote only while
 * they still hold, as the engine does (left as the researcher set them since).
 */
function applyAll(engine: FakeEngine, event: ChartingEvent): EventAnswer[] {
  const row = engine.table.rows.find((r) => r.study_id === event.study_id);
  if (engine.refuse?.[event.study_id] || !row || !row.kept) return [apply(engine, event)];
  const value = event.value as Record<string, string> | null;
  const waiting = row.fulltext.pending_fetch ?? null;
  const guarded = event.kind === "fulltext_status" || ((event.kind === "fulltext_decision" || event.kind === "attachment") && value !== null);
  if (guarded && waiting) return [refused(event, "FETCH_FILE_WAITING")];
  if (event.kind !== "fetched_confirm" && event.kind !== "fetched_discard") return [apply(engine, event)];
  const f = engine.fetch;
  const out: EventAnswer[] = [{ event_id: event.event_id, result: "accepted" }];
  if (value === null) {
    // An undo: the file waits again, as it was.
    if (event.kind === "fetched_confirm") {
      const saved = event.supersedes ? f.confirmed[event.supersedes] : undefined;
      if (!saved) return [refused(event, "BODY_INVALID")];
      const attachmentHolds = !saved.attachmentId || row.heads.attachment === saved.attachmentId;
      const statusHolds = !saved.statusId || row.heads.fulltext_status === saved.statusId;
      row.fulltext = {
        ...row.fulltext,
        ...(attachmentHolds ? { attachment: saved.attachment } : {}),
        ...(statusHolds ? { status: (saved.status.status ?? "to_get") as never, requested_on: saved.status.requested_on, reason: saved.status.reason as never, reason_text: saved.status.reason_text } : {}),
        pending_fetch: saved.pending,
      };
      // The engine's row rule: a row with a file or a status a look-up does not ask about shows no waiting file.
      const lookupStatus = ["to_get", "requested", "not_retrieved"].includes(row.fulltext.status);
      if (row.fulltext.attachment || !lookupStatus) row.fulltext = { ...row.fulltext, pending_fetch: null };
      row.heads = { ...row.heads, fetched_confirm: event.event_id };
    } else {
      const saved = event.supersedes ? f.discarded[event.supersedes] : undefined;
      if (!saved) return [refused(event, "BODY_INVALID")];
      row.fulltext = { ...row.fulltext, pending_fetch: saved, discarded_fetch: null };
      row.heads = { ...row.heads, fetched_discard: event.event_id };
    }
  } else if (event.kind === "fetched_discard") {
    if (!value.reason || (value.reason === "other" && !value.reason_text?.trim())) return [refused(event, "DISCARD_REASON_REQUIRED")];
    if (!waiting || waiting.manifest_row !== value.manifest_row) return [refused(event, "FETCH_NOT_PENDING")];
    f.discarded[event.event_id] = waiting;
    row.fulltext = { ...row.fulltext, pending_fetch: null, discarded_fetch: { reason: value.reason as never, reason_text: value.reason_text ?? null, at: event.at, manifest_row: value.manifest_row } };
    row.heads = { ...row.heads, fetched_discard: event.event_id };
  } else {
    if (!waiting || waiting.manifest_row !== value.manifest_row) return [refused(event, "FETCH_NOT_PENDING")];
    const ft = row.fulltext;
    const attachmentId = crypto.randomUUID();
    const statusId = crypto.randomUUID();
    f.confirmed[event.event_id] = { pending: waiting, attachment: ft.attachment, status: { status: ft.status, requested_on: ft.requested_on, reason: ft.reason, reason_text: ft.reason_text }, attachmentId, statusId };
    row.fulltext = {
      ...ft,
      status: "retrieved",
      requested_on: null,
      reason: null,
      reason_text: null,
      attachment: { name: `${row.study_id}.pdf`, size: waiting.size ?? 0, sha256: waiting.sha256, path: `pdfs/${row.study_id}.pdf`, origin: "fetched" },
      pending_fetch: null,
    };
    row.heads = { ...row.heads, fetched_confirm: event.event_id, attachment: attachmentId, fulltext_status: statusId };
    out.push({ event_id: attachmentId, result: "accepted", added_by_engine: true }, { event_id: statusId, result: "accepted", added_by_engine: true });
  }
  if (engine.table.form && row.cells) derive(row, engine.table.form.columns);
  else row.no_full_text = row.fulltext.status !== "retrieved";
  return out;
}

/** The engine's `select` and `plan` in small: what a look-up of `ids` (or every To get record) would ask. */
function planOf(engine: FakeEngine, ids: string[] | null): FetchPlan {
  const kept = engine.table.rows.filter((r) => r.kept);
  const candidates = ids ? kept.filter((r) => ids.includes(r.study_id)) : kept.filter((r) => r.fulltext.status === "to_get");
  const c = { with_doi: 0, with_arxiv_only: 0, neither: 0, already_have_file: 0, waiting: 0, discarded: 0 };
  let asked = 0;
  for (const r of candidates) {
    if (r.fulltext.pending_fetch) c.waiting += 1;
    else if (r.fulltext.attachment || r.fulltext.status === "retrieved") c.already_have_file += 1;
    else if (!ids && r.fulltext.discarded_fetch) c.discarded += 1;
    else {
      asked += 1;
      if (r.doi) c.with_doi += 1;
      else if (r.arxiv_id) c.with_arxiv_only += 1;
      else c.neither += 1;
    }
  }
  const key = engine.fetch.openalexKey === true;
  const needed = c.with_doi + c.with_arxiv_only > 0;
  return {
    shape: "charting.fetch-plan-v1",
    scope: ids ? "ids" : "to_get",
    total: candidates.length,
    asked,
    ...c,
    arxiv_id_incomplete: 0,
    email: "you@example.org",
    openalex_key_set: key,
    services: { unpaywall: needed ? "asked" : "not_needed", openalex: needed ? (key ? "asked" : "not_asked") : "not_needed", arxiv: c.with_arxiv_only ? "asked" : "not_needed" },
    notes: [],
  };
}

/** The fetch routes of the fake (spec 03 "Backend calls"), or null when the path is not one of them. */
async function fetchRoute(engine: FakeEngine, method: string, path: string, url: URL, body: unknown): Promise<Response | null> {
  const f = engine.fetch;
  if (method === "GET" && path === "/api/v1/charting/fetch/plan") {
    if (f.planHold) await f.planHold;
    if (f.mailto === false) return json({ detail: { code: "MAILTO_NOT_SET", message: "no contact e-mail" } }, 409);
    const ids = url.searchParams.get("ids");
    return json(f.plan ?? planOf(engine, ids ? ids.split(",").filter(Boolean) : null));
  }
  if (method === "POST" && path === "/api/v1/charting/fetch") {
    f.starts.push(body);
    if (f.mailto === false) return json({ detail: { code: "MAILTO_NOT_SET", message: "no contact e-mail" } }, 409);
    if (f.startFail) return json({ detail: { code: f.startFail.code, message: f.startFail.code.toLowerCase() } }, f.startFail.status);
    const b = body as { ids?: string[]; scope?: string; confirm?: boolean };
    if (!b.confirm || (b.ids && b.scope)) return json({ detail: { code: "BODY_INVALID", message: "confirm" } }, 422);
    const started = f.started ?? runView({ total: planOf(engine, b.ids ?? null).asked });
    f.runs = [...(f.afterStart ?? [started])];
    return json(started, 202);
  }
  if (method === "GET" && path === "/api/v1/charting/fetch") {
    if (f.pollFail === "unreachable") throw new TypeError("fetch failed");
    if (f.pollFail) return json({ detail: { code: f.pollFail.code, message: f.pollFail.code.toLowerCase() } }, f.pollFail.status);
    const answer = f.runs.length > 1 ? f.runs.shift()! : f.runs[0] ?? IDLE_RUN;
    return json(structuredClone(answer));
  }
  if (method === "POST" && path === "/api/v1/charting/fetch/cancel") {
    const now = f.runs[0];
    if (now && now.state === "running") f.runs = [{ ...now, state: "cancelling" }];
    return json(structuredClone(f.runs[0] ?? IDLE_RUN));
  }
  const tried = /^\/api\/v1\/charting\/records\/([^/]+)\/fetch$/.exec(path);
  if (tried && method === "GET") {
    const id = decodeURIComponent(tried[1]);
    return json({ shape: "charting.fetch-tried-v1", study_id: id, rows: structuredClone(f.manifest[id] ?? []) });
  }
  return null;
}

/** The engine's form change (`PUT /api/v1/charting/form`), in small: the changes it records and the cells it marks. */
function putForm(engine: FakeEngine, body: { base_version: number; columns: FormColumn[]; reason?: string }): Response {
  const form = engine.table.form!;
  if (body.base_version !== form.version) return json({ detail: { code: "CHARTING_FORM_STALE", message: "stale", version: form.version } }, 409);
  if (body.columns.some((c) => !c.name?.trim())) return json({ detail: { code: "BODY_INVALID", message: "a column name" } }, 422);
  const old = new Map(form.columns.map((c) => [c.column_id, c]));
  const fresh = new Map(body.columns.map((c) => [c.column_id, c]));
  // As the engine: only a column new in this save, or whose sources change, must name columns of the form.
  for (const c of body.columns) {
    const prior = old.get(c.column_id);
    const same = prior && JSON.stringify(prior.derived_from ?? []) === JSON.stringify(c.derived_from ?? []);
    if (!same && (c.derived_from ?? []).some((p) => !old.has(p))) return json({ detail: { code: "BODY_INVALID", message: "derived_from names no column of the form" } }, 422);
  }
  const changes: Omit<Amendment, "amendment_id" | "reason" | "pilot" | "amended_by" | "amended_at" | "form_version_to">[] = [];
  const again = new Set<string>();
  const removedOptions = new Map<string, string[]>();
  // As the engine's `diff`: an old column gone into several new ones is a split, several
  // gone into one new column a merge, one into one a replacement.
  const splits = new Map<string, string[]>();
  for (const c of body.columns) for (const parent of c.derived_from ?? []) if (old.has(parent) && !fresh.has(parent)) splits.set(parent, [...(splits.get(parent) ?? []), c.column_id]);
  const targets = new Map<string, string[]>();
  for (const [parent, children] of splits) for (const child of children) targets.set(child, [...(targets.get(child) ?? []), parent]);
  for (const [parent, children] of splits) {
    if (children.length < 2) continue;
    changes.push({ change: "split", column_id: parent, from: old.get(parent)!.name, to: children.map((id) => fresh.get(id)!.name), columns: children });
    for (const child of children) again.add(child);
  }
  for (const [child, parents] of targets) {
    if (parents.length > 1) changes.push({ change: "merged", column_id: child, from: parents.map((p) => old.get(p)!.name), to: fresh.get(child)!.name, columns: parents });
    else if (splits.get(parents[0])!.length === 1) changes.push({ change: "replaced", column_id: child, from: old.get(parents[0])!.name, to: fresh.get(child)!.name, columns: parents });
    else continue;
    again.add(child);
  }
  for (const c of body.columns) {
    const before = old.get(c.column_id);
    if (!before) {
      if (!targets.has(c.column_id)) changes.push({ change: "added", column_id: c.column_id, from: null, to: c.name });
      continue;
    }
    if (before.name !== c.name) changes.push({ change: "renamed", column_id: c.column_id, from: before.name, to: c.name });
    if (before.definition !== c.definition) changes.push({ change: "definition", column_id: c.column_id, from: before.definition, to: c.definition });
    if (before.type !== c.type) {
      changes.push({ change: "type", column_id: c.column_id, from: before.type, to: c.type });
      again.add(c.column_id);
    }
    const gone = before.options.filter((o) => !c.options.includes(o));
    if (before.type === c.type && c.type !== "yes_no" && gone.length) {
      changes.push({ change: "options_removed", column_id: c.column_id, from: before.options, to: c.options, options: gone });
      removedOptions.set(c.column_id, gone);
    }
    const added = c.options.filter((o) => !before.options.includes(o));
    if (before.type === c.type && c.type !== "yes_no" && added.length) changes.push({ change: "options_added", column_id: c.column_id, from: before.options, to: c.options, options: added });
    if (before.required !== c.required) changes.push({ change: "required", column_id: c.column_id, from: before.required, to: c.required });
  }
  for (const [id, c] of old) if (!fresh.has(id) && !splits.has(id)) changes.push({ change: "removed", column_id: id, from: c.name, to: null });
  if (changes.length === 0 && JSON.stringify(form.columns.map((c) => c.column_id)) !== JSON.stringify(body.columns.map((c) => c.column_id))) {
    changes.push({ change: "order", column_id: null, from: form.columns.map((c) => c.column_id), to: body.columns.map((c) => c.column_id) });
  }
  if (changes.length === 0) return json(structuredClone(form));
  if (form.has_values && !body.reason?.trim()) return json({ detail: { code: "CHARTING_AMENDMENT_REASON_REQUIRED", message: "reason" } }, 422);
  const version = form.version + 1;
  if (form.has_values) {
    const id = `amd_${String(engine.table.form!.amendments.length + 1).padStart(3, "0")}`;
    for (const change of changes) {
      form.amendments.push({ amendment_id: id, ...change, reason: body.reason!.trim(), pilot: form.pilot.on, amended_by: "researcher:local", amended_at: "2026-11-21T14:32:00Z", form_version_to: version } as Amendment);
    }
  }
  const columns = body.columns.map((c) => ({ ...c, options: c.type === "yes_no" ? ["Yes", "No"] : c.options }));
  form.columns = columns;
  form.version = version;
  for (const row of engine.table.rows) {
    const cells: Record<string, Cell> = {};
    for (const c of columns) {
      let cell = row.cells?.[c.column_id] ?? emptyCell();
      if (again.has(c.column_id)) {
        if (cell.state !== null) cell = { ...cell, chart_again: true };
        else {
          // An empty cell of a column made from others: each source's earlier value, as history (`cells.project`).
          for (const parent of (c.derived_from ?? []).filter((p) => old.has(p))) {
            const earlier = row.cells?.[parent];
            if (earlier && earlier.state !== null) cell = { ...cell, chart_again: true, history: [...cell.history, { state: earlier.state, value: earlier.value, note: earlier.note, where_from: earlier.where_from, at: null, form_version: earlier.form_version, event_id: earlier.event_id ?? "", column: old.get(parent)!.name }] };
          }
        }
      }
      const gone = removedOptions.get(c.column_id);
      if (gone && cell.state === "value" && (Array.isArray(cell.value) ? cell.value : [cell.value]).some((v) => gone.includes(String(v)))) cell = { ...cell, chart_again: true };
      cells[c.column_id] = cell;
    }
    row.cells = { ...row.cells, ...cells };
    derive(row, columns);
  }
  engine.table.counts = counts(engine.table.rows);
  return json(structuredClone(form));
}

/** Stub `fetch` with the fake engine; returns the engine so a test can read `calls`. */
export function installEngine(table: ChartingTable, over: Partial<Omit<FakeEngine, "fetch">> & { fetch?: Partial<FakeFetch> } = {}): FakeEngine {
  const { fetch: fetchOver, ...rest } = over;
  const engine: FakeEngine = {
    table: structuredClone(table),
    calls: [],
    ...rest,
    fetch: { runs: [IDLE_RUN], manifest: {}, starts: [], confirmed: {}, discarded: {}, ...fetchOver },
  };
  // The screen writes its view and filter into the address; each test starts from a clean one.
  window.history.replaceState(null, "", "/");
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: string, init?: RequestInit) => {
      const url = new URL(String(input), "http://localhost");
      const path = url.pathname.replace(/^\/api\/console/, "");
      const method = (init?.method ?? "GET").toUpperCase();
      let body: unknown;
      if (typeof init?.body === "string") body = JSON.parse(init.body);
      else if (init?.body) body = init.body;
      engine.calls.push({ method, path: `${path}${url.search}`, body });
      if (engine.fail === "unreachable") throw new TypeError("fetch failed");
      if (engine.fail) return json({ detail: { code: engine.fail.code, message: engine.fail.code.toLowerCase() } }, engine.fail.status);
      if (method === "GET" && path === "/api/v1/charting") {
        if (engine.hold) await engine.hold;
        return json(structuredClone(engine.table));
      }
      if (method === "POST" && path === "/api/v1/charting/events") {
        const events = (body as { events: ChartingEvent[] }).events;
        // As `events.request_refusal`: a decision, a confirm or a discard is one study per request.
        const decided = new Set(events.filter((e) => ["fulltext_decision", "fetched_confirm", "fetched_discard"].includes(e.kind)).map((e) => e.study_id));
        if (decided.size > 1) return json({ detail: { code: "BODY_INVALID", message: "one study at a time" } }, 422);
        const results = events.flatMap((e) => applyAll(engine, e));
        engine.table.counts = counts(engine.table.rows);
        const touched = new Set(events.map((e) => e.study_id));
        return json({ results, counts: engine.table.counts, rows: structuredClone(engine.table.rows.filter((r) => touched.has(r.study_id))) });
      }
      const attach = /^\/api\/v1\/charting\/records\/([^/]+)\/attachment$/.exec(path);
      if (attach && method === "POST") {
        const row = engine.table.rows.find((r) => r.study_id === attach[1])!;
        if (init?.headers && (init.headers as Record<string, string>)["content-type"] === "application/json") {
          const link = (body as { link: string; event_id: string });
          if (!/^https?:\/\//.test(link.link)) return json({ detail: { code: "LINK_INVALID", message: "bad link" } }, 422);
          apply(engine, { event_id: link.event_id, study_id: row.study_id, screener_id: "researcher:local", at: "", kind: "link", value: { url: link.link } });
          engine.table.counts = counts(engine.table.rows);
          return json({ result: "accepted", event_ids: [link.event_id], events: [{ event_id: link.event_id, kind: "link" }], row: structuredClone(row), counts: engine.table.counts });
        }
        const eventId = url.searchParams.get("event_id")!;
        const statusId = url.searchParams.get("status_event_id")!;
        const ids = [eventId];
        // The kinds are listed status first on purpose: the screen must read each event's kind, not its position.
        const events: { event_id: string; kind: string }[] = [];
        const wasToGet = row.fulltext.status === "to_get";
        apply(engine, { event_id: eventId, study_id: row.study_id, screener_id: "researcher:local", at: "", kind: "attachment", value: { name: url.searchParams.get("name"), size: 2048, sha256: "a".repeat(64), path: `pdfs/${row.study_id}.pdf`, origin: "attached" } });
        if (wasToGet) {
          apply(engine, { event_id: statusId, study_id: row.study_id, screener_id: "researcher:local", at: "", kind: "fulltext_status", value: { status: "retrieved" } });
          ids.push(statusId);
          events.push({ event_id: statusId, kind: "fulltext_status" });
        }
        events.push({ event_id: eventId, kind: "attachment" });
        engine.table.counts = counts(engine.table.rows);
        return json({ result: "accepted", event_ids: ids, events, row: structuredClone(row), counts: engine.table.counts });
      }
      if (method === "GET" && path === "/api/v1/charting/methods") {
        if (engine.methodsFail) return json({ detail: { code: engine.methodsFail.code, message: engine.methodsFail.code.toLowerCase() } }, engine.methodsFail.status);
        return json(structuredClone(engine.methods ?? makeMethods()));
      }
      if (method === "GET" && path === "/api/v1/charting/export") {
        if (engine.exportHold) await engine.exportHold;
        if (engine.exportFail === "unreachable") throw new TypeError("fetch failed");
        if (engine.exportFail) return json({ detail: { code: engine.exportFail.code, message: engine.exportFail.code.toLowerCase() } }, engine.exportFail.status);
        const format = url.searchParams.get("format") ?? "csv";
        const view = url.searchParams.get("view") ?? "fulltext";
        if ((format !== "csv" && format !== "xlsx") || (format === "csv" && view !== "fulltext" && view !== "charting")) {
          return json({ detail: { code: "CHARTING_EXPORT_FORMAT_INVALID", message: "csv or xlsx" } }, 422);
        }
        // As `table.export`: the file, then the record the last-export line reads.
        const c = engine.table.counts;
        const name = format === "xlsx" ? "charting-20261121T100000Z.xlsx" : `charting-${view}-20261121T100000Z.csv`;
        engine.table.last_export = {
          at: "2026-11-21T10:00:00Z",
          format: format as "csv" | "xlsx",
          view: format === "xlsx" ? null : (view as "fulltext" | "charting"),
          file_name: name,
          sha256: "c".repeat(64),
          rows: format === "csv" && view === "fulltext" ? c.kept : c.kept - c.excluded,
          not_charted: c.not_charted ?? 0,
          cells_open: c.cells_open ?? 0,
          required_open: c.required_open ?? 0,
        };
        if (format === "xlsx") {
          return new Response(new Uint8Array([0x50, 0x4b, 0x03, 0x04]), { status: 200, headers: { "content-type": XLSX_TYPE, "content-disposition": `attachment; filename="${name}"` } });
        }
        return new Response("﻿study_id\r\n", { status: 200, headers: { "content-type": "text/csv; charset=utf-8", "content-disposition": `attachment; filename="${name}"` } });
      }
      if (method === "PUT" && path === "/api/v1/charting/form") {
        if (engine.formFail) return json({ detail: { code: engine.formFail.code, message: engine.formFail.code.toLowerCase() } }, engine.formFail.status);
        return putForm(engine, body as { base_version: number; columns: FormColumn[]; reason?: string });
      }
      if (method === "POST" && path === "/api/v1/charting/form/pilot/end") {
        const form = engine.table.form!;
        if ((body as { base_version: number }).base_version !== form.version) return json({ detail: { code: "CHARTING_FORM_STALE", message: "stale" } }, 409);
        form.pilot = { on: false, ended_at: "2026-11-21T15:00:00Z", ended_by: "researcher:local", ended_at_version: form.version };
        return json(structuredClone(form));
      }
      const record = /^\/api\/v1\/charting\/records\/([^/]+)$/.exec(path);
      if (record && method === "GET") {
        if (engine.hold) await engine.hold;
        const row = engine.table.rows.find((r) => r.study_id === decodeURIComponent(record[1]));
        if (!row) return json({ detail: { code: "RECORD_NOT_KEPT", message: "not kept" } }, 409);
        return json({
          shape: "charting.record-v1",
          row: structuredClone(row),
          form: structuredClone(engine.table.form),
          read_only: engine.table.read_only,
          reason_options: engine.table.reason_options,
          not_retrieved_reasons: engine.table.not_retrieved_reasons,
          publication: engine.table.publication,
          counts: engine.table.counts,
        });
      }
      const fetched = await fetchRoute(engine, method, path, url, body);
      if (fetched) return fetched;
      return json({ detail: { code: "NOT_FOUND", message: path } }, 404);
    }),
  );
  return engine;
}

export async function flush() {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

/** Render the screen and wait for the table's first answer; `query` is the address's place (`?view=charting`). */
export async function renderCharting(locale: Locale = "en", query = "") {
  if (query) window.history.replaceState(null, "", `/${locale}/charting${query}`);
  const view = render(<ChartingPage locale={locale} />);
  await flush();
  await flush();
  return view;
}

/** Render the one-study view of `id` (spec 02) and wait for the table and the record. */
export async function renderStudy(id: string, locale: Locale = "en", query = "") {
  window.history.replaceState(null, "", `/${locale}/charting/study?id=${encodeURIComponent(id)}${query}`);
  const view = render(<ChartingStudyPage locale={locale} />);
  await flush();
  await flush();
  await flush();
  return view;
}

/**
 * Render Export and methods (spec 04) and wait until it left its loading state
 * (the table and the methods block answered, or a refusal). `settle: false`
 * returns at once, for the loading state and a phone window.
 */
export async function renderReport(locale: Locale = "en", options: { settle?: boolean; query?: string } = {}) {
  window.history.replaceState(null, "", `/${locale}/charting/report${options.query ?? ""}`);
  const view = render(<ChartingReport locale={locale} />);
  await flush();
  if (options.settle === false) return view;
  for (let i = 0; i < 20; i += 1) {
    const state = document.querySelector("[data-desktop] [data-state]")?.getAttribute("data-state");
    if (state && state !== "loading") break;
    await flush();
  }
  return view;
}

export function cellEvents(engine: FakeEngine): ChartingEvent[] {
  return postedEvents(engine).flat().filter((e) => e.kind === "cell");
}

export function grid(): HTMLElement {
  return screen.getByRole("grid");
}

export function postedEvents(engine: FakeEngine): ChartingEvent[][] {
  return engine.calls.filter((c) => c.method === "POST" && c.path === "/api/v1/charting/events").map((c) => (c.body as { events: ChartingEvent[] }).events);
}

/** Press a key on the element that has focus (the window listener hears it), as a person would. */
export async function press(key: string, init: Partial<KeyboardEventInit> = {}) {
  const target = (document.activeElement as HTMLElement | null) ?? document.body;
  await act(async () => {
    target.dispatchEvent(new KeyboardEvent("keydown", { key, bubbles: true, cancelable: true, ...init }));
  });
  await flush();
}
