import { ScreeningApiError, consoleBase, postJson, readJson } from "./screening-api";
import type { Corpus } from "./screening-v1";

/**
 * The discovery routes (M3b-api, M3d-engine; `docs/architecture/research_ui/DISCOVERY_API_PACKET.md` §4,
 * `src/scholar_harness/console/api/discovery.py`). Screens 01–08 of Phase 1 (M3c-screens).
 *
 * Shapes mirror the engine's answers. Every count, share, rate, completeness
 * flag, tier, stale mark and the methods paragraph is written by the harness;
 * the screens only show them. The browser starts a run or a recall check
 * through its own typed route (never the generic job start), and the
 * corpus is frozen only by the hand-off accept (`POST /screening/corpus/accept`).
 */

const BASE = "/api/v1/discovery";

export type ProviderName = "openalex" | "semanticscholar" | "crossref" | "arxiv" | "pubmed" | "biorxiv" | string;

export interface PlanProvider {
  name: ProviderName;
  selected: boolean;
  executed_query: string | null;
  request: Record<string, unknown> | null;
  cannot_express: string[];
  notes: string[];
  status: "translated" | "selected" | "not_selected" | "off_by_default" | "no_connection" | string;
}

export interface Plan {
  shape: "discovery.plan-v1";
  protocol_fingerprint: string;
  query: { id: string; text: string; year_min: number | null; year_max: number | null; language: string | null };
  cap: { value: number; source: "protocol" | "engine_ceiling" | string; ceiling: number };
  mailto_set: boolean;
  /** M3h-providers (F12): a run that selects OpenAlex refuses OPENALEX_KEY_NOT_SET without it. Absent from older consoles. */
  openalex_key_set?: boolean;
  /** M3h-providers: the Semantic Scholar key is set (not verified until a search runs). Absent from older consoles. */
  s2_key_set?: boolean;
  /** M4d: the protocol's anchor papers kept in inception (`search_strategy.golden_seeds`, DOIs). Absent from older consoles. */
  golden_seeds?: string[];
  providers: PlanProvider[];
  imports_hint: string[];
}

export type LegErrorCode = "PROVIDER_RATE_LIMITED" | "PROVIDER_TIMEOUT" | "PROVIDER_UNAVAILABLE" | "PROVIDER_REFUSED";

/** `SearchLeg.to_dict()` (`scholar_search/models.py`). */
export interface SearchLeg {
  provider: ProviderName;
  query_id?: string;
  executed_query: string | null;
  request?: Record<string, unknown>;
  reported_total: number | null;
  fetched: number;
  pages?: number;
  cap: number | null;
  cap_source?: "protocol" | "run_override" | "query" | "engine_ceiling" | string | null;
  cap_hit: boolean;
  status: "ok" | "failed" | "stopped" | "running" | string;
  error?: string | null;
  error_code?: LegErrorCode | string | null;
  notes?: string[];
  mailto_set?: boolean;
  started_at?: string | null;
  finished_at?: string | null;
}

export type JobState = "running" | "succeeded" | "failed" | "cancelled";

export interface DiscoveryJob {
  job_id: string;
  kind: "run" | "recall" | "chase";
  state: JobState;
  started_at: string;
  finished_at: string | null;
  result: Record<string, unknown> | null;
  error: { code: string; message: string; details?: unknown } | null;
}

export interface RunSummary {
  run: string;
  status: string | null;
  started_at: string | null;
  finished_at: string | null;
  legs_total: number;
  fetched_total: number;
  raw_published: boolean;
  cap_override: number | null;
  stale: boolean;
  /** Review F3: the protocol was edited since this run (`null` when it cannot be read). */
  protocol_changed?: boolean | null;
  /** Review F3: the edit changed the search itself (query, years, language, cap, databases). */
  search_changed?: boolean | null;
}

export interface Runs {
  shape: "discovery.runs-v1";
  runs: RunSummary[];
  active_job: DiscoveryJob | null;
}

export interface RunDetail {
  run: string;
  status: string | null;
  query_id?: string;
  query_text?: string;
  year_min?: number | null;
  year_max?: number | null;
  raw_published?: boolean;
  corpus_published?: boolean;
  cap_override: number | null;
  notes?: string[];
  legs: SearchLeg[];
  report_path: string;
  recall_check: { check: string; checked_at: string | null; found: number | null; total: number | null; missed_everywhere: string[] | null } | null;
}

export type SeedKind = "doi" | "arxiv";
export interface SeedIn {
  id: string;
  kind: SeedKind;
  source: "anchor" | "you";
}

export interface RecallSeed extends SeedIn {
  title: string | null;
  title_check: "ok" | "DOI_TITLE_MISMATCH" | "unresolved" | string;
  per_provider: Record<string, "found" | "not_found" | "n/a" | "failed" | string>;
}

export interface RecallCheck {
  shape: "discovery.recall-v1";
  protocol_fingerprint: string;
  checked_at: string;
  query_text: string;
  seeds: RecallSeed[];
  found: number;
  total: number;
  missed_everywhere: string[];
  legs: SearchLeg[];
}

export interface Dedup {
  shape: "discovery.dedup-v1";
  run: string | null;
  input_records: number;
  unique_works: number;
  removed: number;
  removed_rate: number;
  tiers: { identifier: number; exact_title: number; fuzzy_title: number } | null;
  method: { title_similarity: number; year_tolerance: number; first_author: boolean; source: "protocol" | "default" | string } | null;
  near_twins: null;
}

export type Completeness = "full" | "lower_bound" | "failed" | "stopped" | "not_searched";

export interface IdentificationRow {
  database: string;
  kind: "search" | "import";
  executed_query: string | null;
  reported_total: number | null;
  fetched: number | null;
  completeness: Completeness | string;
  no_abstract_rate: number | null;
  cache: null;
  error_code: string | null;
  searched_at: string | null;
  notes: string[];
}

export interface Rejection {
  line: number;
  code: "IMPORT_NO_TITLE" | "IMPORT_BAD_TAG" | "IMPORT_BAD_YEAR" | string;
  reason: string;
}

export interface ReportImport {
  label: string;
  searched_on: string | null;
  query: string | null;
  limits: string | null;
  records: number;
  rejected: Rejection[];
}

export interface MethodsText {
  text: string;
  built_from: string;
  reviewed: boolean;
  reviewed_at: string | null;
  earlier_reviewed?: { run: string; text: string; reviewed_at: string | null } | null;
}

export interface PrismaPreviewLite {
  identified: number;
  duplicates_removed: number;
  screened: number;
  excluded: { total: number; by_reason: Record<string, number> };
  unclear_to_full_text: number;
  included: number;
  not_yet_decided: number;
}

export interface Report {
  shape: "discovery.report-v1";
  run: string;
  status: string | null;
  cap_override: number | null;
  identification: IdentificationRow[];
  not_searched: { database: string; reason: string }[];
  imports: ReportImport[];
  dedup: { removed: number | null; by_tier: Dedup["tiers"]; near_twins: null; unique_works: number | null };
  outside_year_window: number;
  prisma: PrismaPreviewLite | null;
  methods_text: MethodsText;
  runs: Runs;
}

export interface Handoff {
  shape: "discovery.handoff-v1";
  corpus: Corpus;
  run: string | null;
  provider_mix: { provider: string; records: number; share: number }[];
  abstracts: { with_abstract: number; title_only: number; share_with_abstract: number };
  outside_year_window: number;
  near_twins_undecided: null;
  lower_bound_databases: string[];
  protocol_fingerprint: string;
  /** Review F3: the protocol the corpus run searched (`null` for a run from before F3). */
  run_protocol_fingerprint?: string | null;
  protocol_changed?: boolean | null;
  search_changed?: boolean | null;
}

export interface RunRequest {
  cap_override?: number;
  providers?: string[];
  note?: string;
}

export function getPlan(origin: string, signal?: AbortSignal): Promise<Plan> {
  return readJson<Plan>(`${BASE}/plan`, consoleBase(origin), signal);
}

export function getRuns(origin: string, signal?: AbortSignal): Promise<Runs> {
  return readJson<Runs>(`${BASE}/runs`, consoleBase(origin), signal);
}

export function getRun(origin: string, run: string, signal?: AbortSignal): Promise<RunDetail> {
  return readJson<RunDetail>(`${BASE}/runs/${encodeURIComponent(run)}`, consoleBase(origin), signal);
}

/** The run's `search_report.md` as the engine wrote it (served as text/markdown). */
export function runReportHref(origin: string, run: string): string {
  return `${consoleBase(origin)}${BASE}/runs/${encodeURIComponent(run)}/report`;
}

export function startRun(origin: string, request: RunRequest = {}, signal?: AbortSignal): Promise<{ job: DiscoveryJob }> {
  return postJson<{ job: DiscoveryJob }>(`${BASE}/runs`, origin, request, signal);
}

export function startRecall(origin: string, seeds: SeedIn[], signal?: AbortSignal): Promise<{ job: DiscoveryJob }> {
  return postJson<{ job: DiscoveryJob }>(`${BASE}/recall`, origin, { seeds }, signal);
}

export function getRecall(origin: string, signal?: AbortSignal): Promise<RecallCheck> {
  return readJson<RecallCheck>(`${BASE}/recall`, consoleBase(origin), signal);
}

export function getJob(origin: string, jobId: string, signal?: AbortSignal): Promise<{ job: DiscoveryJob }> {
  return readJson<{ job: DiscoveryJob }>(`${BASE}/jobs/${encodeURIComponent(jobId)}`, consoleBase(origin), signal);
}

export function cancelJob(origin: string, jobId: string, signal?: AbortSignal): Promise<{ job: DiscoveryJob }> {
  return postJson<{ job: DiscoveryJob }>(`${BASE}/jobs/${encodeURIComponent(jobId)}/cancel`, origin, {}, signal);
}

export function getDedup(origin: string, signal?: AbortSignal): Promise<Dedup> {
  return readJson<Dedup>(`${BASE}/dedup`, consoleBase(origin), signal);
}

export function getReport(origin: string, run?: string, signal?: AbortSignal): Promise<Report> {
  return readJson<Report>(`${BASE}/report${run ? `?run=${encodeURIComponent(run)}` : ""}`, consoleBase(origin), signal);
}

export function putMethods(origin: string, body: { text: string; reviewed: boolean; run?: string }, signal?: AbortSignal): Promise<MethodsText> {
  return postJson<MethodsText>(`${BASE}/report/methods`, origin, body, signal, "PUT");
}

export function getHandoff(origin: string, signal?: AbortSignal): Promise<Handoff> {
  return readJson<Handoff>(`${BASE}/handoff`, consoleBase(origin), signal);
}

/** One server-sent event of a discovery job (`GET /discovery/jobs/{id}/events`). */
export type JobEvent =
  | { event: "snapshot"; data: { job: DiscoveryJob } }
  | { event: "leg"; data: { job_id: string; provider: string; fetched: number; reported_total: number | null; cap: number | null; cap_hit: boolean; status: string; error_code: string | null } }
  | { event: "stage"; data: { job_id: string; stage: string; status: string; detail: unknown } }
  | { event: "done"; data: { job: DiscoveryJob } }
  | { event: "failed"; data: { job: DiscoveryJob } };

/** Split an SSE text into events; comments (`: keepalive`) and partial tails are skipped. */
export function parseSse(text: string): { events: JobEvent[]; rest: string } {
  const events: JobEvent[] = [];
  const blocks = text.replace(/\r\n/g, "\n").split("\n\n");
  const rest = blocks.pop() ?? "";
  for (const block of blocks) {
    let name = "message";
    const data: string[] = [];
    for (const line of block.split("\n")) {
      if (line.startsWith(":")) continue;
      if (line.startsWith("event:")) name = line.slice(6).trim();
      else if (line.startsWith("data:")) data.push(line.slice(5).trimStart());
    }
    if (!data.length) continue;
    try {
      events.push({ event: name, data: JSON.parse(data.join("\n")) } as JobEvent);
    } catch {
      // A malformed event is skipped, never guessed at.
    }
  }
  return { events, rest };
}

/**
 * Read a job's event stream to its end. The engine replays every event on each
 * connect, so the caller rebuilds its view from the events of the current
 * connection. Resolves when the stream closes (`ended` tells whether a `done`
 * or `failed` event was seen); rejects on a refusal or a dropped connection.
 */
export function streamJob(
  origin: string,
  jobId: string,
  onEvent: (event: JobEvent) => void,
  signal?: AbortSignal,
): Promise<{ ended: boolean }> {
  return streamEvents(`${consoleBase(origin)}${BASE}/jobs/${encodeURIComponent(jobId)}/events`, onEvent, signal);
}

/**
 * Read one server-sent event stream to its end (a discovery job, or a recon
 * job of an inception draft, M4d). Resolves when the stream closes; `ended`
 * says whether a `done` or `failed` event was seen.
 */
export async function streamEvents<E extends { event: string }>(
  url: string,
  onEvent: (event: E) => void,
  signal?: AbortSignal,
): Promise<{ ended: boolean }> {
  let response: Response;
  try {
    response = await fetch(url, {
      headers: { accept: "text/event-stream" },
      signal,
    });
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new ScreeningApiError("CONSOLE_UNREACHABLE", 0, error instanceof Error ? error.message : "the console could not be reached");
  }
  if (!response.ok) {
    let detail: { code?: string; message?: string; details?: unknown } = {};
    try {
      const body = (await response.json()) as { detail?: typeof detail };
      detail = body.detail ?? {};
    } catch {
      // not JSON
    }
    throw new ScreeningApiError(detail.code ?? `HTTP_${response.status}`, response.status, detail.message ?? "", detail.details);
  }
  let ended = false;
  const handle = (events: JobEvent[]) => {
    for (const event of events) {
      if (event.event === "done" || event.event === "failed") ended = true;
      onEvent(event as unknown as E);
    }
  };
  if (!response.body || typeof response.body.getReader !== "function") {
    handle(parseSse(`${await response.text()}\n\n`).events);
    return { ended };
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    let chunk: ReadableStreamReadResult<Uint8Array>;
    try {
      chunk = await reader.read();
    } catch (error) {
      if (signal?.aborted) throw error;
      throw new ScreeningApiError("STREAM_DROPPED", 0, error instanceof Error ? error.message : "the event stream dropped");
    }
    if (chunk.done) break;
    buffer += decoder.decode(chunk.value, { stream: true });
    const parsed = parseSse(buffer);
    buffer = parsed.rest;
    handle(parsed.events);
  }
  handle(parseSse(`${buffer}\n\n`).events);
  return { ended };
}

// --------------------------------------------------------------------------- citation chasing (M3g)

/** `ChaseLeg` as `chase.json` writes it: one seed, one database, one direction. */
export interface ChaseLeg {
  seed: string;
  provider: ProviderName;
  direction: "forward" | "backward" | string;
  fetched: number;
  cap: number | null;
  cap_hit: boolean;
  status: "ok" | "failed" | "skipped" | "pending" | string;
  error: string | null;
  error_code: LegErrorCode | string | null;
  notes: string[];
  started_at: string | null;
  finished_at: string | null;
}

/** One row per database and direction, summed by the engine (`legs_summary`); the browser sums nothing. */
export interface ChaseLegsSummary {
  provider: ProviderName;
  direction: "forward" | "backward" | string;
  legs: number;
  ok: number;
  failed: number;
  skipped: number;
  fetched: number;
  cap_hits: number;
}

export interface ChaseCounts {
  raw: number;
  duplicates_within_chase: number;
  already_in_corpus: number;
  outside_year_window: number;
  over_ceiling: number;
  new: number;
}

export interface ChaseSeed {
  study_id: string;
  title: string;
  decision: "INCLUDE" | "MAYBE" | string;
  doi: string | null;
  openalex_id: string | null;
  s2_id: string | null;
  chaseable: boolean;
  reason: string | null;
}

export interface ChaseAccepted {
  round: number;
  artifact_id: string;
  accepted_at: string;
  records: number;
  studies: number;
}

/** `chase_summaries()` rows (`GET /discovery/chase` → `runs[]`). */
export interface ChaseRunSummary {
  chase: string;
  status: "SUCCESS" | "PARTIAL" | "EMPTY_RESULT" | "FAILED" | string | null;
  reason: string | null;
  started_at: string | null;
  finished_at: string | null;
  seeds: number;
  chaseable_seeds: number;
  providers: string[];
  directions: string[];
  counts: Partial<ChaseCounts>;
  published: boolean;
  accepted: ChaseAccepted | null;
}

/** `chase.json` with `legs_summary` added (`GET /discovery/chase` → `latest`, `GET /discovery/chase/runs/{chase}`). */
export interface ChaseRun {
  schema: "nexus.citation-chase.v1";
  chase: string;
  status: ChaseRunSummary["status"];
  reason: string;
  started_at: string;
  finished_at: string;
  seed_source: "included" | "included+unclear" | string;
  generation_id: string | null;
  parent_corpus: { artifact_id: string; sha256: string | null } | null;
  providers: string[];
  directions: string[];
  forward_cap: number | null;
  run_ceiling: number | null;
  year_min: number | null;
  year_max: number | null;
  seeds: ChaseSeed[];
  legs: ChaseLeg[];
  legs_summary: ChaseLegsSummary[];
  counts: ChaseCounts;
  already_in_corpus: { record: string; title: string; study_id: string | null; sources?: unknown[] }[];
  published: boolean;
  cancelled: boolean;
  notes: string[];
  accepted: ChaseAccepted | null;
}

export interface ChaseState {
  shape: "discovery.chase-v1";
  /** `code` (review R2): why the screening does not count as published (`SCREENING_NOT_PUBLISHED`, `PROTOCOL_CHANGED_SINCE_PUBLISH`, ...), else null. */
  screening: { published: boolean; generation_id: string | null; round: number; arm: "databases" | "citation_searching" | string | null; code?: string | null };
  seeds: { source: string; total: number; chaseable: number; not_chaseable: { study_id: string; title: string; reason: string | null }[] };
  keys: { openalex_key_set: boolean; s2_key_set: boolean };
  defaults: { directions: string[]; providers: string[]; forward_cap: number; run_ceiling: number };
  runs: ChaseRunSummary[];
  latest: ChaseRun | null;
  active_job: DiscoveryJob | null;
}

export interface ChaseRequest {
  directions?: ("forward" | "backward")[];
  providers?: string[];
  cap_per_seed?: number;
  ceiling?: number;
  seeds?: "included" | "included+unclear";
  note?: string;
}

export interface ChaseAcceptAnswer {
  shape: "discovery.chase-accept-v1";
  chase: string;
  round: number;
  corpus: { artifact_id: string; studies: number; records: number; outcome_status: string };
  parent_corpus: string;
  archived: string[];
  archive_path: string;
}

/** A chase job's `leg` event: one seed, one database, one direction, as it finished. */
export type ChaseLegEvent = {
  event: "leg";
  data: { job_id: string; seed: string; provider: string; direction: string; fetched: number; cap: number | null; cap_hit: boolean; status: string; error_code: string | null; notes: string[] };
};

export function getChase(origin: string, signal?: AbortSignal): Promise<ChaseState> {
  return readJson<ChaseState>(`${BASE}/chase`, consoleBase(origin), signal);
}

export function getChaseRun(origin: string, chase: string, signal?: AbortSignal): Promise<ChaseRun> {
  return readJson<ChaseRun>(`${BASE}/chase/runs/${encodeURIComponent(chase)}`, consoleBase(origin), signal);
}

export function startChase(origin: string, request: ChaseRequest = {}, signal?: AbortSignal): Promise<{ job: DiscoveryJob }> {
  return postJson<{ job: DiscoveryJob }>(`${BASE}/chase/runs`, origin, request, signal);
}

export function acceptChase(origin: string, chase?: string, signal?: AbortSignal): Promise<ChaseAcceptAnswer> {
  return postJson<ChaseAcceptAnswer>(`${BASE}/chase/accept`, origin, chase ? { chase } : {}, signal);
}
