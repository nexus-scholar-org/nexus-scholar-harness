import { act, render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { ChartingPage } from "@/components/charting-page";
import { ChartingStudyPage } from "@/components/charting-study";
import type { Locale } from "@/i18n";
import type { Amendment, Cell, ChartingEvent, ChartingForm, ChartingRow, ChartingTable, FormColumn } from "@/lib/charting-api";

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
 * changes, an option it uses is removed or its column is split, and refuses an
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
  return {
    kept: live.length,
    to_get: by((r) => r.fulltext.status === "to_get"),
    requested: by((r) => r.fulltext.status === "requested"),
    retrieved: by((r) => r.fulltext.status === "retrieved"),
    not_retrieved: by((r) => r.fulltext.status === "not_retrieved"),
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
  return { event_id: event.event_id, result: "accepted" };
}

/** The engine's form change (`PUT /api/v1/charting/form`), in small: the changes it records and the cells it marks. */
function putForm(engine: FakeEngine, body: { base_version: number; columns: FormColumn[]; reason?: string }): Response {
  const form = engine.table.form!;
  if (body.base_version !== form.version) return json({ detail: { code: "CHARTING_FORM_STALE", message: "stale", version: form.version } }, 409);
  if (body.columns.some((c) => !c.name?.trim())) return json({ detail: { code: "BODY_INVALID", message: "a column name" } }, 422);
  const old = new Map(form.columns.map((c) => [c.column_id, c]));
  const fresh = new Map(body.columns.map((c) => [c.column_id, c]));
  const changes: Omit<Amendment, "amendment_id" | "reason" | "pilot" | "amended_by" | "amended_at" | "form_version_to">[] = [];
  const again = new Set<string>();
  const removedOptions = new Map<string, string[]>();
  const splits = new Map<string, string[]>();
  for (const c of body.columns) for (const parent of c.derived_from ?? []) if (old.has(parent) && !fresh.has(parent)) splits.set(parent, [...(splits.get(parent) ?? []), c.column_id]);
  for (const [parent, children] of splits) {
    changes.push({ change: "split", column_id: parent, from: old.get(parent)!.name, to: children.map((id) => fresh.get(id)!.name), columns: children });
    for (const child of children) again.add(child);
  }
  for (const c of body.columns) {
    const before = old.get(c.column_id);
    if (!before) {
      if (!(c.derived_from ?? []).some((p) => splits.has(p))) changes.push({ change: "added", column_id: c.column_id, from: null, to: c.name });
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
        const parent = (c.derived_from ?? [])[0];
        const earlier = parent ? row.cells?.[parent] : undefined;
        if (earlier && earlier.state !== null) cell = { ...cell, chart_again: true, history: [...cell.history, { state: earlier.state, value: earlier.value, note: earlier.note, where_from: earlier.where_from, at: null, form_version: earlier.form_version, event_id: earlier.event_id ?? "", column: old.get(parent)!.name }] };
        else if (cell.state !== null) cell = { ...cell, chart_again: true };
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
export function installEngine(table: ChartingTable, over: Partial<FakeEngine> = {}): FakeEngine {
  const engine: FakeEngine = { table: structuredClone(table), calls: [], ...over };
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
        const results = events.map((e) => apply(engine, e));
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
      if (method === "GET" && path === "/api/v1/charting/export") {
        const view = url.searchParams.get("view") ?? "fulltext";
        return new Response("﻿study_id\r\n", { status: 200, headers: { "content-type": "text/csv; charset=utf-8", "content-disposition": `attachment; filename="charting-${view}-20261121T100000Z.csv"` } });
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
