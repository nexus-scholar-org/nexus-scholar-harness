import { streamEvents } from "./discovery-api";
import type { DraftRecord, Grounding } from "./inception-api";
import { consoleBase, postJson, readJson } from "./screening-api";

/**
 * The recon routes of an inception draft (M4c, M4d; `src/scholar_harness/console/api/recon.py`),
 * read by Explore (spec 02) and Direction (spec 03).
 *
 * Shapes mirror the engine's answers. Every count, gate label, direction,
 * anchor, fingerprint and stale mark is the engine's; the screens show them and
 * send back only what the researcher chose. The gap check (`POST .../recon/delta`)
 * is not carried: the browser never calls it (spec 03, decision 2026-11-11).
 */

const base = (draftId: string) => `/api/v1/inception/drafts/${encodeURIComponent(draftId)}/recon`;

/** One database of a probe: its status, counts, failure code and notes, as the engine wrote them. */
export interface ReconLeg {
  provider: string;
  status: "ok" | "failed" | string;
  reported_total: number | null;
  fetched: number | null;
  cap: number | null;
  cap_hit: boolean | null;
  error: string | null;
  error_code: string | null;
  notes: string[];
  /** `true`/`false` for a database that takes a key, `null` for one that does not. */
  key_set?: boolean | null;
}

export interface Probe {
  purpose: "topic" | "narrower" | "delta" | string;
  query: string | null;
  fingerprint: string;
  created_at: string | null;
  cache_key?: string;
  status: "complete" | "partial" | "empty" | string;
  n_docs: number;
  served_from_cache: boolean;
  year_min?: number | null;
  year_max?: number | null;
  languages?: string[] | null;
  legs: ReconLeg[];
  at: string;
}

export interface ReconSession {
  session_id: string;
  topic: string | null;
  latest: Probe | null;
  probes: Probe[];
  narrower_left: number;
}

export interface Binding {
  stale: boolean;
  code?: "POOL_CHANGED" | "SCOPE_CHANGED" | string;
  reason?: string;
  changes?: string[];
  bound?: string | null;
  current?: string | null;
}

export interface ReconJob {
  job_id: string;
  session_id: string;
  kind: "probe" | "delta" | string;
  state: "running" | "succeeded" | "failed" | string;
  started_at: string;
  finished_at: string | null;
  result: Probe | null;
  error: { code: string; message: string; details?: unknown } | null;
}

export interface ReconState {
  session_id: string;
  mailto_set: boolean;
  keys?: { openalex_key_set: boolean; s2_key_set: boolean };
  topic_changed?: boolean;
  scope_changed?: boolean;
  scope_changes?: string[];
  session: ReconSession | null;
  grounding: Grounding | null;
  binding: Binding | null;
  active_job: ReconJob | null;
}

export interface PoolSummary {
  fingerprint: string;
  created_at: string | null;
  status: "complete" | "partial" | "empty" | string;
  query: string | null;
  year_min: number | null;
  year_max: number | null;
  languages: string[] | null;
  semantic: boolean | null;
  n_docs: number;
  max_docs: number;
  legs: ReconLeg[];
}

export interface Gates {
  pool: { n_docs: number; sufficient: boolean; label: "sufficient" | "thin" | string; threshold: number };
  purity: { label: "coherent" | "fragmented" | "indeterminate" | string; purity?: number | null; n_topics?: number; top1_share?: number | null; top3_share?: number | null; threshold: number };
}

export interface Labelled {
  label: string;
  n: number;
  score?: number;
  anchor_dois?: string[];
}

export interface Distilled {
  pool: PoolSummary;
  gates: Gates;
  qei?: number | null;
  schools: Labelled[];
  topics: Labelled[];
  metrics: { label: string; count: number }[];
  datasets: { label: string; count: number }[];
  papers: { doi: string | null; title: string | null; year: number | null; provider: string | null; directions_anchored: number }[];
}

export interface Direction {
  label: string;
  concept: string;
  anchor_dois: string[];
  observed_in: number;
  n_docs: number;
  detail?: string;
  schools?: string[];
}

export interface Directions {
  pool: PoolSummary;
  gates: Gates;
  directions: Direction[];
  narrower_left: number;
}

export interface ConceptReport {
  fingerprint: string;
  n_docs: number;
  concepts: {
    concept: string;
    source: "draft" | "suggested" | string;
    terms: { term: string; observed_in: number; anchor_dois: string[] }[];
    anchored_in: number;
    suggestions: { term: string; observed_in: number }[];
  }[];
}

export interface Evidence {
  term: string;
  hits?: number;
  observed_in: number;
  anchor_dois: string[];
  n_docs: number;
}

export interface SeedPaper {
  doi: string;
  title: string | null;
  year: number | null;
  provider: string | null;
  anchors: { directions: string[]; concepts: string[] };
}

export interface Seeds {
  fingerprint: string;
  papers: SeedPaper[];
}

export type BindRequest =
  | { direction: string; accept_thin_pool: boolean; base_updated_at: string }
  | { own: string; accept_thin_pool: boolean; base_updated_at: string }
  | { skip: true; base_updated_at: string };

export type ProbeRequest = { refresh: boolean; semantic: boolean } | { narrower: string };

export function getRecon(origin: string, draftId: string, signal?: AbortSignal): Promise<ReconState> {
  return readJson<ReconState>(base(draftId), consoleBase(origin), signal);
}

export function startProbe(origin: string, draftId: string, body: ProbeRequest, signal?: AbortSignal): Promise<{ job: ReconJob }> {
  return postJson<{ job: ReconJob }>(`${base(draftId)}/probe`, origin, body, signal);
}

export function getReconJob(origin: string, draftId: string, jobId: string, signal?: AbortSignal): Promise<{ job: ReconJob }> {
  return readJson<{ job: ReconJob }>(`${base(draftId)}/jobs/${encodeURIComponent(jobId)}`, consoleBase(origin), signal);
}

export type ReconEvent =
  | { event: "snapshot"; data: { job: ReconJob } }
  | { event: "leg"; data: { job_id: string; provider: string; fetched: number } }
  | { event: "done"; data: { job: ReconJob } }
  | { event: "failed"; data: { job: ReconJob } };

export function streamReconJob(origin: string, draftId: string, jobId: string, onEvent: (event: ReconEvent) => void, signal?: AbortSignal): Promise<{ ended: boolean }> {
  return streamEvents<ReconEvent>(`${consoleBase(origin)}${base(draftId)}/jobs/${encodeURIComponent(jobId)}/events`, onEvent, signal);
}

/** A read of the latest usable pool (it writes a content-addressed file in the recon cache, nothing else). */
export function distill(origin: string, draftId: string, signal?: AbortSignal): Promise<Distilled> {
  return postJson<Distilled>(`${base(draftId)}/distill`, origin, {}, signal);
}

export function getDirections(origin: string, draftId: string, signal?: AbortSignal): Promise<Directions> {
  return readJson<Directions>(`${base(draftId)}/directions`, consoleBase(origin), signal);
}

export function getConcepts(origin: string, draftId: string, signal?: AbortSignal): Promise<ConceptReport> {
  return readJson<ConceptReport>(`${base(draftId)}/concepts`, consoleBase(origin), signal);
}

export function getEvidence(origin: string, draftId: string, term: string, signal?: AbortSignal): Promise<Evidence> {
  return readJson<Evidence>(`${base(draftId)}/evidence?term=${encodeURIComponent(term)}`, consoleBase(origin), signal);
}

export function getSeeds(origin: string, draftId: string, signal?: AbortSignal): Promise<Seeds> {
  return readJson<Seeds>(`${base(draftId)}/seeds`, consoleBase(origin), signal);
}

/** Bind a direction, your own phrase, or the skip; answers the whole draft record with its `grounding`. */
export function bindDirection(origin: string, draftId: string, body: BindRequest, signal?: AbortSignal): Promise<DraftRecord> {
  return postJson<DraftRecord>(`${base(draftId)}/bind`, origin, body, signal);
}

/** A session has a usable pool when any of its probes kept papers (an empty probe never replaces it). */
export function hasUsablePool(state: ReconState | null): boolean {
  return !!state?.session?.probes?.some((p) => p.n_docs > 0);
}

/** The probe whose pool is the session's latest usable one. */
export function latestUsableProbe(state: ReconState | null): Probe | null {
  const probes = state?.session?.probes ?? [];
  for (let i = probes.length - 1; i >= 0; i--) if (probes[i].n_docs > 0) return probes[i];
  return null;
}
