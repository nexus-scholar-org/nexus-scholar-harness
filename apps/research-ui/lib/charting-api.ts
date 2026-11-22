import type { Locale } from "@/i18n";

import { ScreeningApiError, consoleBase, postJson, readJson } from "./screening-api";
import { newEventId } from "./screening-v1";

/**
 * The charting routes of M12a Part A (screen spec 01 of the extraction phase,
 * `src/scholar_harness/console/api/charting.py`), typed as the engine answers them.
 *
 * The engine computes the rows, their state, the counts and every refusal; this
 * file only types the answers, sends the researcher's events and carries bytes.
 * Part B adds the charting form beside the protocol, the cells of each row, the
 * pilot, the recorded amendments, the one-study read and the Charting CSV.
 * Event ids are minted here (`newEventId`, a UUID in small letters); the engine judges
 * each event and answers accepted, duplicate or refused.
 */

const BASE = "/api/v1/charting";

export const CHARTING_SHAPE = "charting.table-v1";

export type FulltextStatus = "to_get" | "requested" | "retrieved" | "not_retrieved";
export type NotRetrievedReason = "no_access" | "not_found" | "no_reply" | "other";
export type Outcome = "INCLUDE" | "EXCLUDE";

export interface Attachment {
  name: string;
  size: number;
  sha256: string;
  path: string;
  origin: string;
}

export interface Fulltext {
  status: FulltextStatus;
  requested_on: string | null;
  reason: NotRetrievedReason | null;
  reason_text: string | null;
  attachment: Attachment | null;
  link: string | null;
}

export interface FulltextDecision {
  outcome: Outcome;
  reason_code?: string | null;
  reason_text?: string | null;
}

export interface Heads {
  fulltext_status: string | null;
  fulltext_decision: string | null;
  attachment: string | null;
  link: string | null;
}

/** Part B: the five column types of the charting form (record (e)). */
export type ColumnType = "text" | "number" | "one" | "several" | "yes_no";

export interface FormColumn {
  column_id: string;
  name: string;
  definition: string;
  type: ColumnType;
  options: string[];
  required: boolean;
  from_protocol?: string | null;
  derived_from?: string[];
}

export interface Amendment {
  amendment_id: string;
  change_no?: number;
  change: string;
  column_id: string | null;
  from: unknown;
  to: unknown;
  options?: string[];
  columns?: string[];
  reason: string;
  pilot: boolean;
  amended_by: string;
  amended_at: string;
  form_version_from?: number;
  form_version_to: number;
}

export interface ChartingForm {
  schema?: string;
  version: number;
  columns: FormColumn[];
  pilot: { on: boolean; ended_at: string | null; ended_by: string | null; ended_at_version?: number | null };
  amendments: Amendment[];
  has_values: boolean;
}

export type CellState = null | "value" | "not_reported" | "not_applicable";
export type CellValue = string | number | string[] | null;

export interface CellHistory {
  state: CellState;
  value: CellValue;
  note: string | null;
  where_from: string | null;
  at: string | null;
  form_version: number | null;
  event_id: string;
  /** The name of the column the value was charted in, when it was another one (a split or a merge). */
  column?: string;
}

export interface Cell {
  state: CellState;
  value: CellValue;
  note: string | null;
  where_from: string | null;
  pilot: boolean;
  chart_again: boolean;
  history: CellHistory[];
  /** The event that holds the cell now (what a change or an undo supersedes); null when never charted. */
  event_id: string | null;
  form_version: number | null;
}

export interface ChartingRow {
  study_id: string;
  title: string | null;
  authors: string[];
  year: number | string | null;
  venue: string | null;
  doi: string | null;
  url: string | null;
  abstract: string | null;
  arxiv_id: string | null;
  round: number;
  arm: string;
  round_label: string;
  generation_id: string | null;
  ta_decision: "INCLUDE" | "MAYBE";
  ta_reason: string | null;
  kept: boolean;
  new_since: string | null;
  fulltext: Fulltext;
  ft_decision: FulltextDecision | null;
  heads: Heads;
  /** Part B: one cell per form column; absent in an answer from before Part B. */
  cells?: Record<string, Cell>;
  charted?: boolean;
  pilot?: boolean;
  no_full_text?: boolean;
}

export interface ReasonOption {
  code: string;
  label: string;
  kind: "exclusion" | "fails_inclusion" | "other" | string;
  category: string | null;
}

export interface ChartingCounts {
  kept: number;
  to_get: number;
  requested: number;
  retrieved: number;
  not_retrieved: number;
  included: number;
  excluded: number;
  to_decide: number;
  charted?: number;
  not_charted?: number;
  pilot?: number;
}

export interface ChartingTable {
  shape: typeof CHARTING_SHAPE | string;
  screener_id: string;
  publication: { status: string; code: string | null; generation_id: string | null; published_at: string | null; round: number };
  rounds: { round: number; arm: string; generation_id: string; published_at: string | null }[];
  chasing_pending: boolean;
  stale: boolean;
  changes: { published_at: string; added: number; no_longer_kept: number } | null;
  read_only: boolean;
  read_only_code: string | null;
  reason_options: ReasonOption[];
  not_retrieved_reasons: NotRetrievedReason[];
  counts: ChartingCounts;
  /** Part B: the form beside the protocol, seeded at the first read (pilot on). */
  form?: ChartingForm;
  rows: ChartingRow[];
}

/** `GET /api/v1/charting/records/{study_id}`: one study for the one-study view (spec 02). */
export interface ChartingRecord {
  shape: string;
  row: ChartingRow;
  form: ChartingForm;
  read_only: boolean;
  reason_options: ReasonOption[];
  not_retrieved_reasons: NotRetrievedReason[];
  publication: ChartingTable["publication"];
  counts: ChartingCounts;
}

export type EventKind = "fulltext_status" | "fulltext_decision" | "attachment" | "link" | "cell";

export interface ChartingEvent {
  event_id: string;
  study_id: string;
  screener_id: string;
  at: string;
  kind: EventKind;
  value: unknown;
  note?: string;
  where_from?: string;
  supersedes?: string;
}

export interface EventResult {
  event_id: string;
  result: "accepted" | "duplicate" | "refused";
  refusal?: { code: string; message: string };
}

export interface EventsAnswer {
  results: EventResult[];
  counts: ChartingCounts;
  rows: ChartingRow[];
}

export interface AttachAnswer {
  result: "accepted" | "duplicate";
  event_ids: string[];
  /** Each event the answer wrote, with its kind: an undo goes by kind, never by position. */
  events: { event_id: string; kind: string }[];
  row: ChartingRow | null;
  counts: ChartingCounts;
}

/** The engine's own limit per request. */
export const MAX_CHARTING_EVENTS = 200;

export function getCharting(origin: string, signal?: AbortSignal): Promise<ChartingTable> {
  return readJson<ChartingTable>(BASE, consoleBase(origin), signal);
}

export function chartingEvent(input: {
  studyId: string;
  screenerId: string;
  kind: EventKind;
  value: unknown;
  supersedes?: string | null;
  note?: string | null;
  whereFrom?: string | null;
  now?: Date;
}): ChartingEvent {
  const event: ChartingEvent = {
    event_id: newEventId(),
    study_id: input.studyId,
    screener_id: input.screenerId,
    at: (input.now ?? new Date()).toISOString(),
    kind: input.kind,
    value: input.value,
  };
  if (input.note) event.note = input.note;
  if (input.whereFrom) event.where_from = input.whereFrom;
  if (input.supersedes) event.supersedes = input.supersedes;
  return event;
}

export function postChartingEvents(origin: string, events: ChartingEvent[], signal?: AbortSignal): Promise<EventsAnswer> {
  if (events.length > MAX_CHARTING_EVENTS) throw new RangeError(`at most ${MAX_CHARTING_EVENTS} events per request`);
  return postJson<EventsAnswer>(`${BASE}/events`, origin, { events }, signal);
}

function attachmentPath(studyId: string): string {
  return `${BASE}/records/${encodeURIComponent(studyId)}/attachment`;
}

/** Where the attached PDF is served (opened in a new tab through the same-origin path). */
export function attachmentHref(origin: string, studyId: string): string {
  return `${consoleBase(origin)}${attachmentPath(studyId)}`;
}

async function failure(response: Response): Promise<ScreeningApiError> {
  let detail: unknown = null;
  try {
    detail = ((await response.json()) as { detail?: unknown }).detail ?? null;
  } catch {
    // Not JSON: the status alone names the failure.
  }
  const d = typeof detail === "object" && detail !== null ? (detail as { code?: unknown; message?: unknown }) : {};
  return new ScreeningApiError(d.code ? String(d.code) : `HTTP_${response.status}`, response.status, d.message ? String(d.message) : response.statusText);
}

/** The researcher's PDF as the raw body; attaching to a To get row also writes a Retrieved status event. */
export async function attachPdf(
  origin: string,
  studyId: string,
  file: Blob & { name?: string },
  ids: { eventId: string; statusEventId: string },
  signal?: AbortSignal,
): Promise<AttachAnswer> {
  const query = new URLSearchParams({ name: file.name || "attachment.pdf", event_id: ids.eventId, status_event_id: ids.statusEventId });
  let response: Response;
  try {
    response = await fetch(`${consoleBase(origin)}${attachmentPath(studyId)}?${query.toString()}`, {
      method: "POST",
      headers: { "content-type": "application/pdf" },
      body: file,
      signal,
    });
  } catch (error) {
    throw new ScreeningApiError("CONSOLE_UNREACHABLE", 0, error instanceof Error ? error.message : "the console could not be reached");
  }
  if (!response.ok) throw await failure(response);
  return (await response.json()) as AttachAnswer;
}

/** A pasted link, stored as text (no request is made to it). */
export function postLink(origin: string, studyId: string, link: string, eventId: string, signal?: AbortSignal): Promise<AttachAnswer> {
  return postJson<AttachAnswer>(attachmentPath(studyId), origin, { link, event_id: eventId }, signal);
}

export type ExportView = "fulltext" | "charting";

/** A view of the rows as CSV; the engine builds the file and journals it. */
export async function exportCsv(origin: string, view: ExportView, signal?: AbortSignal): Promise<{ blob: Blob; filename: string }> {
  let response: Response;
  try {
    response = await fetch(`${consoleBase(origin)}${BASE}/export?format=csv&view=${view}`, { method: "GET", signal });
  } catch (error) {
    throw new ScreeningApiError("CONSOLE_UNREACHABLE", 0, error instanceof Error ? error.message : "the console could not be reached");
  }
  if (!response.ok) throw await failure(response);
  const disposition = response.headers.get("content-disposition") ?? "";
  const filename = /filename="([^"]+)"/.exec(disposition)?.[1] ?? `charting-${view}.csv`;
  return { blob: await response.blob(), filename };
}

/** The Full text view as CSV (Part A's name, kept for its callers). */
export function exportFulltextCsv(origin: string, signal?: AbortSignal): Promise<{ blob: Blob; filename: string }> {
  return exportCsv(origin, "fulltext", signal);
}

/** One study for the one-study view; `RECORD_NOT_KEPT` when it is not in the kept set. */
export function getChartingRecord(origin: string, studyId: string, signal?: AbortSignal): Promise<ChartingRecord> {
  return readJson<ChartingRecord>(`${BASE}/records/${encodeURIComponent(studyId)}`, consoleBase(origin), signal);
}

/** A new form version; once any cell holds a value the engine asks for `reason` (`CHARTING_AMENDMENT_REASON_REQUIRED`). */
export function putChartingForm(
  origin: string,
  input: { baseVersion: number; columns: FormColumn[]; reason?: string | null },
  signal?: AbortSignal,
): Promise<ChartingForm> {
  const body: Record<string, unknown> = { base_version: input.baseVersion, columns: input.columns };
  if (input.reason) body.reason = input.reason;
  return postJson<ChartingForm>(`${BASE}/form`, origin, body, signal, "PUT");
}

/** "End pilot", one recorded action. */
export function endChartingPilot(origin: string, baseVersion: number, signal?: AbortSignal): Promise<ChartingForm> {
  return postJson<ChartingForm>(`${BASE}/form/pilot/end`, origin, { base_version: baseVersion }, signal);
}

/** Where the screen was when a study was opened, so Esc goes back to the same row, view and filter. */
export interface TablePlace {
  view?: "fulltext" | "charting";
  show?: string;
  excluded?: boolean;
  row?: string | null;
  form?: boolean;
}

function placeQuery(place: TablePlace, origin: string): URLSearchParams {
  const query = new URLSearchParams();
  if (place.view && place.view !== "fulltext") query.set("view", place.view);
  if (place.show && place.show !== "all") query.set("show", place.show);
  if (place.excluded) query.set("excluded", "1");
  if (place.row) query.set("row", place.row);
  if (place.form) query.set("form", "open");
  if (origin) query.set("console", origin);
  return query;
}

/** The charting screen's route, carrying a development build's console origin. */
export function chartingHref(locale: Locale, origin = "", place: TablePlace = {}): string {
  const query = placeQuery(place, origin).toString();
  return `/${locale}/charting${query ? `?${query}` : ""}`;
}

/**
 * The one-study view (spec 02). The study travels as a query parameter, not a
 * path segment: the packaged app is exported as prebuilt pages, which cannot hold a
 * page per study id.
 */
export function chartingStudyHref(locale: Locale, studyId: string, origin = "", place: TablePlace = {}): string {
  const query = placeQuery({ ...place, row: null, form: false }, origin);
  query.set("id", studyId);
  return `/${locale}/charting/study?${query.toString()}`;
}
