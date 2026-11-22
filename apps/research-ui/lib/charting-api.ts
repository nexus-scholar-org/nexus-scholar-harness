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

/**
 * Part F: a fetched file waiting for the researcher on a row ("Fetched, to
 * confirm"); `fulltext.status` keeps the earlier status (spec 03 "Data in").
 */
export interface PendingFetch {
  manifest_row: string;
  run_id: string | null;
  /** The service that listed the copy, as the engine names it ("Unpaywall", "OpenAlex", "arXiv"). */
  source: string | null;
  source_name?: string | null;
  host: string | null;
  host_type?: string | null;
  address?: string | null;
  version: string | null;
  version_label: string | null;
  licence: string | null;
  size: number | null;
  sha256: string;
  /** The kit's check of the first two pages: "doi found", "title found", "not found: check it", "not checked". */
  identity: string | null;
  at: string | null;
  /** Other kept records whose waiting or attached file has the same bytes. */
  duplicate_of: string[];
}

/** Part F: the newest look-up of a record (its newest manifest row). */
export interface LastLookup {
  run_id: string | null;
  manifest_row: string | null;
  at: string | null;
  outcome: string | null;
  message?: string | null;
  try_later: boolean;
  same_as_discarded?: boolean;
}

export type DiscardReason = "wrong_paper" | "not_full_text" | "unreadable" | "other";

export interface DiscardedFetch {
  reason: DiscardReason | null;
  reason_text: string | null;
  at: string | null;
  manifest_row: string | null;
}

export interface Fulltext {
  status: FulltextStatus;
  requested_on: string | null;
  reason: NotRetrievedReason | null;
  reason_text: string | null;
  attachment: Attachment | null;
  link: string | null;
  /** Part F; absent in an answer from before Part F. */
  pending_fetch?: PendingFetch | null;
  last_lookup?: LastLookup | null;
  discarded_fetch?: DiscardedFetch | null;
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
  /** Part F: the events that hold a confirm or a discard of a fetched file now. */
  fetched_confirm?: string | null;
  fetched_discard?: string | null;
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
  /** Part F: rows with a fetched file waiting; they are not in to get, requested or not retrieved. */
  to_confirm?: number;
  /** Part C: cells not charted yet (empty or to chart again) on rows not excluded, and those of required columns. */
  cells_open?: number;
  required_open?: number;
}

/** Part C: what the newest export wrote (`charting/last_export.json`), for the persistent last-export line. */
export interface LastExport {
  at: string;
  format: "csv" | "xlsx";
  view: ExportView | null;
  file_name: string;
  sha256: string;
  rows: number;
  not_charted: number;
  cells_open: number;
  required_open: number;
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
  /** Part C: the newest export, or null before the first; absent in an answer from before Part C. */
  last_export?: LastExport | null;
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

export type EventKind = "fulltext_status" | "fulltext_decision" | "attachment" | "link" | "cell" | "fetched_confirm" | "fetched_discard";

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
  /** Part F: an event the engine wrote with the client's (a confirm's attachment and status). */
  added_by_engine?: boolean;
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
export type ExportFormat = "csv" | "xlsx";

/** The export route of a file: a CSV of one view, or the spreadsheet (which has no view). */
export function exportUrl(format: ExportFormat, view: ExportView = "fulltext"): string {
  return format === "xlsx" ? `${BASE}/export?format=xlsx` : `${BASE}/export?format=csv&view=${view}`;
}

/** A file of the rows: the engine builds it, journals it with its SHA-256 and records it as the last export. */
export async function exportFile(
  origin: string,
  format: ExportFormat,
  view: ExportView = "fulltext",
  signal?: AbortSignal,
): Promise<{ blob: Blob; filename: string }> {
  let response: Response;
  try {
    response = await fetch(`${consoleBase(origin)}${exportUrl(format, view)}`, { method: "GET", signal });
  } catch (error) {
    throw new ScreeningApiError("CONSOLE_UNREACHABLE", 0, error instanceof Error ? error.message : "the console could not be reached");
  }
  if (!response.ok) throw await failure(response);
  const disposition = response.headers.get("content-disposition") ?? "";
  const fallback = format === "xlsx" ? "charting.xlsx" : `charting-${view}.csv`;
  const filename = /filename="([^"]+)"/.exec(disposition)?.[1] ?? fallback;
  return { blob: await response.blob(), filename };
}

/** A view of the rows as CSV; the engine builds the file and journals it. */
export function exportCsv(origin: string, view: ExportView, signal?: AbortSignal): Promise<{ blob: Blob; filename: string }> {
  return exportFile(origin, "csv", view, signal);
}

/** The Full text view as CSV (Part A's name, kept for its callers). */
export function exportFulltextCsv(origin: string, signal?: AbortSignal): Promise<{ blob: Blob; filename: string }> {
  return exportCsv(origin, "fulltext", signal);
}

// ---------------------------------------------------------------- Part C: the PRISMA full-text counts and the methods answer

/** One group of the PRISMA full-text counts (`report.py` `_empty`): a round, an arm or the total. */
export interface PrismaGroup {
  sought: number;
  not_retrieved: number;
  /** Keyed by the engine's own English words ("No access or paywalled", "Not found", "Authors did not reply", "Other"). */
  not_retrieved_reasons: Record<string, number>;
  assessed: number;
  excluded: number;
  /** Keyed by reason code (`EXC-n`, `FAILS-INC-n`, `OTHER`). */
  exclusion_reasons: Record<string, number>;
  included: number;
  awaiting_retrieval: number;
  to_confirm: number;
  retrieved_not_assessed: number;
  assessed_without_full_text: number;
  /** Reports not retrieved and decided from the abstract: counted under not_retrieved, apart from the boxes. */
  not_retrieved_decided?: number;
  not_retrieved_included?: number;
  not_retrieved_excluded?: number;
}

export interface PrismaRound extends PrismaGroup {
  round: number;
  arm: string | null;
  label: string;
  generation_id: string | null;
  published_at: string | null;
}

export interface PrismaFulltext {
  schema: string;
  unit: string;
  rounds: PrismaRound[];
  /** `databases` and `citation_searching`, each present in the engine's answer even when empty. */
  arms: Record<string, PrismaGroup>;
  total: PrismaGroup;
}

/** One recorded form amendment as the methods answer lists it (`report.py` `amendment_list`). */
export interface MethodsAmendment {
  at?: string | null;
  changes?: string[];
  reason?: string | null;
  [key: string]: unknown;
}

/** `GET /api/v1/charting/methods` (`report.py` `methods()`): a pure read, nothing is written. */
export interface ChartingMethods {
  shape: "charting.methods-v1" | string;
  sentences: string[];
  paragraph: string;
  figures: {
    prisma: PrismaFulltext;
    open_access: { used: number; discarded: number; services: string[] };
    reviewers: { fulltext_decisions: number; charting: number };
    charted: number;
    not_charted: number;
    cells_open: number;
    required_open: number;
    pilot: number;
    amendments: MethodsAmendment[];
  };
  caveats: string[];
  not_stated: string[];
  sources: { name: string; path: string; digest: string }[];
}

export function getChartingMethods(origin: string, signal?: AbortSignal): Promise<ChartingMethods> {
  return readJson<ChartingMethods>(`${BASE}/methods`, consoleBase(origin), signal);
}

/** The same, under the short names a caller inside this module family expects. */
export type Methods = ChartingMethods;
export const getMethods = getChartingMethods;

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

// ---------------------------------------------------------------- Part F: open-access copies

export type ServiceUse = "asked" | "not_asked" | "not_needed";

/** `GET /api/v1/charting/fetch/plan`: what a look-up would ask; nothing is sent (spec 03 "Data in"). */
export interface FetchPlan {
  shape: string;
  scope: "to_get" | "ids";
  /** The records in scope, those left out included. */
  total: number;
  /** The records the run would reach: `with_doi + with_arxiv_only + neither`. */
  asked: number;
  with_doi: number;
  with_arxiv_only: number;
  neither: number;
  arxiv_id_incomplete: number;
  already_have_file: number;
  waiting: number;
  discarded: number;
  email: string;
  openalex_key_set: boolean;
  services: { unpaywall: ServiceUse; openalex: ServiceUse; arxiv: ServiceUse };
  notes?: string[];
}

export type FetchState = "idle" | "running" | "cancelling" | "finished" | "cancelled" | "interrupted" | "failed";

/** `GET /api/v1/charting/fetch`: the running look-up, else the newest one, else idle. */
export interface FetchRun {
  state: FetchState;
  run_id: string | null;
  total?: number;
  reached?: number;
  found?: number;
  downloaded?: number;
  failed_checks?: number;
  /** Errors by kind, in the kit's short words ("HTTP 403", "timed out", "lookup failed"); the screen maps them. */
  errors?: Record<string, number>;
  /** The failed file checks by the kit's name (`pdf_header`, `size_floor`, …), each counted once per record; absent in older run files. */
  check_failures?: Record<string, number>;
  /** The look-ups that failed and are not "try later"; absent in older run files. */
  lookup_failures?: { service: string; http_status: number | null; error_kind: string | null; n: number }[];
  no_open_copy?: number;
  no_direct_pdf?: number;
  try_later?: number;
  skipped_no_id?: number;
  not_reached?: number;
  /** Records left out before or during the run; `changed_during_run` counts rows the researcher changed after the start. */
  left_out?: { already_have_file?: number; waiting?: number; discarded?: number; changed_during_run?: number };
  providers?: string[];
  email?: string;
  openalex_key_set?: boolean;
  now?: { phase: string; host: string | null; seconds?: number };
  recent_requests?: { host: string; answer: string }[];
  started_at?: string | null;
  finished_at?: string | null;
  error?: string | null;
}

export interface ManifestRequest {
  url: string;
  host: string;
  retry?: boolean;
  route?: string;
  http_status: number | null;
  final_url?: string | null;
  redirects?: string[];
  content_type?: string | null;
  error: string | null;
}

export interface ManifestLookup {
  service: string;
  state: "ANSWERED" | "NOT_FOUND" | "FAILED" | "NOT_ASKED" | string;
  http_status: number | null;
  error?: string | null;
}

/** One row of `charting/fetch_manifest.jsonl` (`src/scholar_pdf/manifest.py`, with the run's fields). */
export interface ManifestRow {
  row_id?: string;
  run_id?: string;
  study_id: string;
  doi?: string | null;
  outcome: string | null;
  status?: string | null;
  file?: string | null;
  size?: number | null;
  sha256?: string | null;
  address?: string | null;
  redirects?: string[];
  http_status?: number | null;
  version?: string | null;
  version_label?: string | null;
  license?: string | null;
  provider?: string | null;
  checks?: Record<string, string>;
  lookups?: ManifestLookup[];
  requests?: ManifestRequest[];
  time?: string | null;
  arxiv_version?: string | null;
}

export interface FetchTried {
  shape: string;
  study_id: string;
  rows: ManifestRow[];
}

/** The plan of a look-up of `ids`, or of every record To get when `ids` is null. */
export function getFetchPlan(origin: string, ids: readonly string[] | null, signal?: AbortSignal): Promise<FetchPlan> {
  const query = ids && ids.length ? `?ids=${encodeURIComponent(ids.join(","))}` : "";
  return readJson<FetchPlan>(`${BASE}/fetch/plan${query}`, consoleBase(origin), signal);
}

/** Start a look-up after the researcher confirmed its plan; 202 with the run. */
export function startFetch(origin: string, ids: readonly string[] | null, signal?: AbortSignal): Promise<FetchRun> {
  const body = ids && ids.length ? { ids: [...ids], confirm: true } : { scope: "to_get", confirm: true };
  return postJson<FetchRun>(`${BASE}/fetch`, origin, body, signal);
}

export function getFetchRun(origin: string, signal?: AbortSignal): Promise<FetchRun> {
  return readJson<FetchRun>(`${BASE}/fetch`, consoleBase(origin), signal);
}

export function cancelFetch(origin: string, signal?: AbortSignal): Promise<FetchRun> {
  return postJson<FetchRun>(`${BASE}/fetch/cancel`, origin, {}, signal);
}

/** What was tried for one record: its manifest rows, oldest first. */
export function getFetchTried(origin: string, studyId: string, signal?: AbortSignal): Promise<FetchTried> {
  return readJson<FetchTried>(`${BASE}/records/${encodeURIComponent(studyId)}/fetch`, consoleBase(origin), signal);
}

/** Where the fetched file waiting on a record is served, to open in a new tab before confirming it. */
export function fetchedHref(origin: string, studyId: string): string {
  return `${consoleBase(origin)}${BASE}/records/${encodeURIComponent(studyId)}/fetched`;
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

/** Export and methods (spec 04, Part C): the downloads, the PRISMA full-text counts and the methods paragraph. */
export function chartingReportHref(locale: Locale, origin = ""): string {
  return `/${locale}/charting/report${origin ? `?console=${encodeURIComponent(origin)}` : ""}`;
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
