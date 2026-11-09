import { consoleBase, postJson, readJson } from "./screening-api";

/**
 * The inception routes (M4a engine, M4b screens; `docs/architecture/inception-api.md`).
 *
 * Shapes mirror the engine's answers. Every proposal, criterion id, decision
 * status, fingerprint and refusal comes from the engine; the screens only show
 * them and send back what the researcher chose. Discarding a draft (DELETE) is
 * not carried by the browser surface.
 */

const BASE = "/api/v1/inception";

export interface ConceptIn {
  concept: string;
  synonyms?: string[];
}

export interface ExclusionIn {
  criterion: string;
  reason_category?: string;
}

/** Every interview answer (inception API §Draft). All optional until preview. */
export interface Draft {
  topic?: string;
  paradigm?: string | null;
  playbook?: string | null;
  secondary_paradigm?: string | null;
  unit_of_analysis?: string;
  proof?: string;
  out_of_scope?: string[];
  languages?: string[];
  start_year?: number | null;
  end_year?: number | null;
  rqs?: string[];
  concepts?: ConceptIn[];
  extra_inclusions?: string[];
  extra_exclusions?: ExclusionIn[];
  criteria_decisions?: Record<string, boolean>;
  matrix_columns?: string[];
  verification_checks?: boolean;
  title?: string;
  lead_researcher?: string;
  venue?: string;
  timeline_weeks?: number | null;
}

export interface Emitted {
  slug: string;
  path: string;
  protocol_fingerprint: string;
  replaced: boolean;
  /** For a replacement (M4b): kept on the draft so Done shows them after a reload. */
  previous_fingerprint?: string | null;
  backup_dir?: string | null;
}

export interface DraftRecord {
  session_id: string;
  created_at: string;
  updated_at: string;
  draft: Draft;
  emitted: Emitted | null;
}

export interface DraftListItem {
  session_id: string;
  readable: boolean;
  title?: string | null;
  topic?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  emitted?: Emitted | null;
}

export interface DraftListing {
  root: string;
  items: DraftListItem[];
}

export interface ScopeStep {
  step: "scope";
  leanings: { paradigm: string; score: number }[];
  recommended_paradigm: string;
  paradigms: { name: string; goal: string }[];
  refraction: { paradigm: string; goal: string; sample_rq: string; evidence: string; negatives: string }[];
  default_concepts: string[];
}

export interface ShapeStep {
  step: "shape";
  recommended_playbook: string;
  playbooks: { name: string; framework: string }[];
  trustworthiness_framework: string | null;
  rq_draft: string;
  lexicon: string;
  lexicon_warnings: string[];
}

export type CriterionStatus = "accepted" | "rejected" | "undecided";

export interface Criterion {
  id: string;
  kind: "inclusion" | "exclusion";
  criterion: string;
  reason_category: string | null;
  source: "proof" | "paradigm_default" | "out_of_scope" | "manual" | string;
  source_label: string;
  generated: boolean;
  status: CriterionStatus;
}

export interface CriteriaStep {
  step: "criteria";
  criteria: Criterion[];
  undecided: string[];
  missing_sides: ("inclusion" | "exclusion")[];
}

export interface MatrixColumn {
  name: string;
  description?: string;
  [key: string]: unknown;
}

export interface MatrixStep {
  step: "matrix";
  columns: MatrixColumn[];
  selected: string[];
}

export interface ScreeningBinding {
  bound: boolean;
  decision_events: number;
  decision_files: number;
  published: boolean;
}

export interface Preview {
  intent: Record<string, unknown>;
  protocol: Record<string, unknown>;
  protocol_fingerprint: string;
  screening_criteria: string;
  criteria: Criterion[];
  files: string[];
  written: string[];
  /** `workspace`: the folder holds a workspace (what genesis decides on); `exists` alone may be a folder that is not one. */
  target?: { slug: string; path: string; exists: boolean; workspace: boolean; screening: ScreeningBinding | null };
}

export interface GenesisResult {
  session_id: string;
  slug: string;
  path: string;
  protocol_fingerprint: string;
  replaced: boolean;
  previous_fingerprint?: string | null;
  backup_dir?: string | null;
}

export interface GenesisRequest {
  replace?: boolean;
  confirm_discard_screening_binding?: string;
}

export function listDrafts(origin: string, signal?: AbortSignal): Promise<DraftListing> {
  return readJson<DraftListing>(`${BASE}/drafts`, consoleBase(origin), signal);
}

export function createDraft(origin: string, draft: Draft = {}, signal?: AbortSignal): Promise<DraftRecord> {
  return postJson<DraftRecord>(`${BASE}/drafts`, origin, { draft }, signal);
}

export function readDraft(origin: string, sessionId: string, signal?: AbortSignal): Promise<DraftRecord> {
  return readJson<DraftRecord>(`${BASE}/drafts/${encodeURIComponent(sessionId)}`, consoleBase(origin), signal);
}

/** Save the whole draft; the engine refuses `DRAFT_CONFLICT` when `baseUpdatedAt` is not the stored one. */
export function saveDraft(origin: string, sessionId: string, draft: Draft, baseUpdatedAt: string, signal?: AbortSignal): Promise<DraftRecord> {
  return postJson<DraftRecord>(
    `${BASE}/drafts/${encodeURIComponent(sessionId)}`,
    origin,
    { draft, base_updated_at: baseUpdatedAt },
    signal,
    "PUT",
  );
}

export function runStep(origin: string, step: "scope", draft: Draft, signal?: AbortSignal): Promise<ScopeStep>;
export function runStep(origin: string, step: "shape", draft: Draft, signal?: AbortSignal): Promise<ShapeStep>;
export function runStep(origin: string, step: "criteria", draft: Draft, signal?: AbortSignal): Promise<CriteriaStep>;
export function runStep(origin: string, step: "matrix", draft: Draft, signal?: AbortSignal): Promise<MatrixStep>;
export function runStep(origin: string, step: string, draft: Draft, signal?: AbortSignal): Promise<unknown> {
  return postJson(`${BASE}/steps/${step}`, origin, { draft }, signal);
}

export function previewDraft(origin: string, draft: Draft, signal?: AbortSignal): Promise<Preview> {
  return postJson<Preview>(`${BASE}/preview`, origin, { draft }, signal);
}

export function runGenesis(origin: string, sessionId: string, request: GenesisRequest = {}, signal?: AbortSignal): Promise<GenesisResult> {
  return postJson<GenesisResult>(`${BASE}/drafts/${encodeURIComponent(sessionId)}/genesis`, origin, request, signal);
}
