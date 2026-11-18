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

/** M10b: the researcher's own matrix column (`05-criteria`); the engine derives `id` when absent. */
export interface MatrixColumnIn {
  id?: string | null;
  name: string;
  description?: string;
  data_type?: string;
  required?: boolean;
  fallback_value?: string;
  target_section_category?: string | null;
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
  /** M4d: the recall seeds kept on Direction (DOIs, at most 25); compiled into `search_strategy.golden_seeds`. */
  golden_seeds?: string[];
  /** M10b (R3): the number of records the researcher plans to screen; empty keeps the playbook preset. */
  pool_min?: number | null;
  pool_max?: number | null;
  /** M10b: the reason code of each out-of-scope line, keyed by its text. */
  out_of_scope_reasons?: Record<string, string>;
  /** M10b: the reason code of the paradigm's default exclusion. */
  default_exclusion_reason?: string | null;
  /** M10b: the researcher's own matrix columns. */
  custom_matrix_columns?: MatrixColumnIn[];
}

export interface Emitted {
  slug: string;
  path: string;
  protocol_fingerprint: string;
  replaced: boolean;
  /** For a replacement (M4b): kept on the draft so Done shows them after a reload. */
  previous_fingerprint?: string | null;
  backup_dir?: string | null;
  /** M4d (F1): what a replacement moved into the backup folder beside the old protocol. */
  archived?: string[] | null;
}

/** The direction bound to a draft (M4c); `source` is `none` for the explicit skip (M4d). */
export interface GroundingDirection {
  label: string;
  concept: string;
  anchor_dois: string[];
  observed_in: number;
  n_docs: number;
  schools?: string[];
  detail?: string;
  source: "pool" | "researcher" | "none" | string;
  grounded: boolean;
}

export interface Grounding {
  session_id: string;
  bound_at: string;
  pool: { fingerprint: string; created_at: string | null; status?: string; query?: string | null; n_docs?: number };
  direction: GroundingDirection;
  anchors: string[];
  /** `none` for the explicit skip (M4d); otherwise the direction's source. */
  choice?: "pool" | "researcher" | "none" | string;
}

export interface DraftRecord {
  session_id: string;
  created_at: string;
  updated_at: string;
  draft: Draft;
  emitted: Emitted | null;
  /** Written only by the engine's bind route (M4c); a save carries it through. */
  grounding?: Grounding | null;
  /** M10b: the earlier protocol a draft was started from; written only by the engine. */
  origin?: DraftOrigin | null;
}

/** M10b (`09-start-from-protocol`): what the import read. */
export interface ImportSourceSummary {
  kind: "workspace" | "file";
  label: string;
  read: "protocol" | "intent";
  slug?: string;
  file_name?: string;
  schema?: string | null;
  protocol_id?: string | null;
  protocol_created_at?: string | null;
  protocol_fingerprint: string | null;
  target_slug: string;
  collides_with_source: boolean;
}

/** One line of the import report, as the engine wrote it (`what` names the kind). */
export interface ImportLoss {
  what: string;
  [key: string]: unknown;
}

export interface ImportCarried {
  field: string;
  from: string;
  class: string;
}

export interface ImportReport {
  source: ImportSourceSummary;
  draft: Draft;
  carried: ImportCarried[];
  lost: ImportLoss[];
  needs_you: string[];
  earlier_pool: { min: number; max: number } | null;
}

export interface DraftOrigin {
  kind: "import";
  source: ImportSourceSummary;
  imported_at: string;
  checked: Record<string, boolean>;
  report: { carried: ImportCarried[]; lost: ImportLoss[]; needs_you: string[] };
  earlier_pool: { min: number; max: number } | null;
}

export type ImportSourceRequest =
  | { kind: "workspace"; slug: string }
  | { kind: "file"; file_name: string; content_base64: string };

export interface DraftListItem {
  session_id: string;
  readable: boolean;
  title?: string | null;
  topic?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  emitted?: Emitted | null;
  /** M10b: the label of the earlier protocol the draft was started from. */
  origin_label?: string | null;
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
  /** M10b: null when the draft has no proof answer (no template question is offered). */
  rq_draft: string | null;
  lexicon: string;
  lexicon_warnings: string[];
  /** M10b (R4): whether the proof answer is still needed; the engine decides. */
  proof_required?: boolean;
  /** M10b (R3): the chosen playbook's planned-size preset. */
  pool_preset?: { min: number; max: number } | null;
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
  /** M10b: false for an exclusion whose saved code breaks the reason rule (flagged, not refused). */
  reason_valid?: boolean;
}

/** M10b: a reason code the criteria step offers; `used` codes are already in this draft. */
export interface ReasonSuggestion {
  code: string;
  source: "used" | "default" | "wizard" | "protocol_model" | "screener" | "example_protocol" | string;
  phrases: boolean;
}

export interface CriteriaStep {
  step: "criteria";
  criteria: Criterion[];
  undecided: string[];
  missing_sides: ("inclusion" | "exclusion")[];
  reason_suggestions?: ReasonSuggestion[];
}

export interface MatrixColumn {
  name: string;
  description?: string;
  [key: string]: unknown;
}

export interface MatrixStep {
  step: "matrix";
  columns: MatrixColumn[];
  /** M10b: the researcher's own columns with the ids the engine derived. */
  custom_columns?: (MatrixColumn & { id: string })[];
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
  target?: {
    slug: string;
    path: string;
    exists: boolean;
    workspace: boolean;
    screening: ScreeningBinding | null;
    /** M4d (F1): the workspace paths a replacement archives beside the old protocol. */
    archive?: string[];
  };
}

export interface GenesisResult {
  session_id: string;
  slug: string;
  path: string;
  protocol_fingerprint: string;
  replaced: boolean;
  previous_fingerprint?: string | null;
  backup_dir?: string | null;
  archived?: string[] | null;
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

/** With `sessionId`, the engine checks the draft's bound direction first (`STALE_BINDING`, M4c). */
export function previewDraft(origin: string, draft: Draft, signal?: AbortSignal, sessionId?: string): Promise<Preview> {
  return postJson<Preview>(`${BASE}/preview`, origin, sessionId ? { draft, session_id: sessionId } : { draft }, signal);
}

export function runGenesis(origin: string, sessionId: string, request: GenesisRequest = {}, signal?: AbortSignal): Promise<GenesisResult> {
  return postJson<GenesisResult>(`${BASE}/drafts/${encodeURIComponent(sessionId)}/genesis`, origin, request, signal);
}

/** M10b: read a protocol into a draft. `dry_run` answers the report and stores nothing. */
export function importDraft(origin: string, source: ImportSourceRequest, signal?: AbortSignal): Promise<ImportReport> {
  return postJson<ImportReport>(`${BASE}/drafts/import`, origin, { source, dry_run: true }, signal);
}

/** M10b: create the draft from the source the report showed; the engine refuses a source that changed since. */
export function createImportedDraft(origin: string, source: ImportSourceRequest, expectFingerprint: string | null, signal?: AbortSignal): Promise<DraftRecord> {
  return postJson<DraftRecord>(`${BASE}/drafts/import`, origin, { source, dry_run: false, expect_fingerprint: expectFingerprint }, signal);
}

/** M10b: mark an imported step as opened; the draft's `updated_at` does not change. */
export function markStepChecked(origin: string, sessionId: string, step: string, signal?: AbortSignal): Promise<{ session_id: string; origin: DraftOrigin | null }> {
  return postJson(`${BASE}/drafts/${encodeURIComponent(sessionId)}/origin/checked`, origin, { step }, signal);
}
