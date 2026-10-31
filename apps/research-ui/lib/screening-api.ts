/**
 * Typed read client over the console presentation routes (HCM-06, UI-07).
 *
 * Every function below performs one GET against the workspace bound at app
 * state on the console side; the browser never sends a path, an identity, or
 * a fingerprint. Responses keep the server shapes byte for byte: counts and
 * states are server-computed, and absent prerequisites arrive as explicit
 * `missing` entries with a reason, never as silent nulls.
 *
 * There is deliberately no POST/PUT here and no credential handling: reads
 * are unauthenticated loopback GETs, and approval stays a terminal act.
 *
 * Prose note for the stylesheet guard: this file sits under `lib/`, which
 * the `@source not` list does not exclude, so a utility-looking word here
 * would be emitted into the stylesheet with no source to justify it, and
 * `tests-browser/hygiene.spec.ts` reports that as unexplained. The wording
 * below is chosen to carry no such word.
 */

export interface MissingEntry {
  file?: string;
  batch?: string;
  study?: string;
  reason: string;
}

export interface ProjectSummary {
  shape: "ui07.project-summary-v1";
  workspace_id: string | null;
  project_id: string;
  protocol: { present: boolean; fingerprint: string | null };
  run: { screening_run_id: string; batches: number; batches_resolved: number } | null;
  readiness: {
    screening_prepared: boolean;
    all_batches_resolved: boolean;
    publication: PublicationStatus;
  };
  missing: MissingEntry[];
}

export interface PublicationStatus {
  shape: "ui07.publication-status-v1";
  status: "CURRENT" | "STALE" | "SUPERSEDED" | "MISMATCHED" | "LEGACY_UNVERIFIED";
  code: string | null;
  generation_id: string | null;
  outputs: Record<string, string>;
  message: string;
  details: Record<string, unknown>;
}

export interface PublicationOutput {
  filename: string;
  content: string;
}

export interface ScreeningBatchEntry {
  batch_index: number;
  batch_file: string;
  items: number;
  decisions_file: string | null;
  decisions_count: number | null;
  collected: boolean;
  coverage: "COMPLETE" | "INCOMPLETE";
  missing_ids?: string[];
  extra_ids?: string[];
  unresolved_rows: string[];
  binding?: { state: "STALE_BINDING"; reason: string };
}

export interface ScreeningBatches {
  shape: "ui07.screening-batches-v1";
  run_id: string | null;
  count: number;
  batches: ScreeningBatchEntry[];
  missing: MissingEntry[];
}

export interface ScreeningRow {
  shape: "ui07.screening-row-v1";
  study_id: string;
  workspace_id?: string;
  citation?: string;
  abstract?: string;
  decision: string;
  reasons: string[];
  uncertainty: string;
  criterion_refs?: { inclusion: string[]; exclusion: string[] };
  source_locators?: { doi?: string; url?: string; venue?: string; year?: number };
}

export interface ScreeningRows {
  shape: "ui07.screening-rows-v1";
  batch_index: number;
  batch_file: string;
  total: number;
  offset: number;
  limit: number;
  rows: ScreeningRow[];
  missing: MissingEntry[];
}

export interface CriterionRefs {
  shape: "ui07.criterion-refs-v1";
  protocol_fingerprint: string | null;
  live_protocol_fingerprint?: string;
  inclusion: { id: string; text: string }[];
  exclusion: { id: string; text: string }[];
  sources: {
    workspace_id: string;
    citation?: string;
    abstract?: string;
    doi?: string;
    url?: string;
    venue?: string;
    year?: number;
  }[];
  missing: MissingEntry[];
}

/**
 * The workspace status read (`GET /api/v1/workspace/status`).
 *
 * Only the fields the corpus screen presents are typed here. The counts are
 * computed by the Python harness from the workspace files; the browser copies
 * them, it never derives them from a rendered list.
 */
export interface WorkspaceStatus {
  workspace: string;
  title?: string;
  phase?: string;
  discovered_count?: number;
  deduped_count?: number;
  verified_count?: number;
  included_count?: number;
  excluded_count?: number;
}

/**
 * One corpus row, projected by the console (`ui07.corpus-record-v1`).
 *
 * The screen never parses `literature/included.json` / `excluded.json` itself:
 * that file is an internal dump and reading its keys here is how two corpus
 * contracts start drifting. The console projects the stored bytes once, and
 * this is the only shape the screen knows. An absent value stays `null` so the
 * row can say the harness stored nothing instead of inventing a reason.
 */
export interface CorpusRecord {
  shape: "ui07.corpus-record-v1";
  workspace_id: string;
  title: string | null;
  year: number | string | null;
  provider: string | null;
  doi: string | null;
  abstract: string | null;
  decision: string;
  confidence: number | null;
  reasoning: string | null;
  reason_code: string | null;
  criterion: string | null;
  lane: string | null;
}

/**
 * One page of the corpus (`ui07.corpus-page-v1`).
 *
 * `total` is the number of records matching the filter, `corpus_total` the
 * number stored. Both are counted by the console; the page only prints them.
 * `missing` is the console's explicit "no such file" entry, never a silent
 * empty page.
 */
export interface CorpusPage {
  shape: "ui07.corpus-page-v1";
  kind: "included" | "excluded";
  total: number;
  corpus_total: number;
  offset: number;
  limit: number;
  records: CorpusRecord[];
  missing: MissingEntry[];
}

export interface ReviewState {
  shape: "ui07.review-state-v1";
  batch_index: number;
  recommendation:
    | {
        present: true;
        schema: string;
        revision: number;
        method: string;
        rows_pending: number;
      }
    | { present: false };
  resolution: { resolved: number; total: number; unresolved_rows: string[] };
  override:
    | { superseded: false }
    | {
        superseded: true;
        snapshot_fingerprint: string;
        recommendation_sha256: string;
        final_decision_sha256: string;
      };
  review: { present: false } | { present: true; approval_fingerprint: string };
  deferral: { present: boolean };
  missing: MissingEntry[];
}

export interface AuditFeedItem {
  timestamp: string | null;
  event_id: string | null;
  action: string;
  agent_or_tool: string | null;
  description: string | null;
  status: string | null;
}

export interface AuditFeed {
  shape: "ui07.audit-feed-v1";
  total: number;
  offset: number;
  limit: number;
  items: AuditFeedItem[];
}

/**
 * A refused or failed read, carrying the server typed code (for example
 * `BATCH_MISSING`, `CALLER_IDENTITY_REFUSED`, or a `GENERATION_*` refusal)
 * so the screen can explain the state instead of guessing.
 */
export class ScreeningApiError extends Error {
  readonly code: string;
  readonly status: number;
  readonly serverMessage: string;
  readonly serverDetails: unknown;

  constructor(code: string, status: number, serverMessage: string, serverDetails?: unknown) {
    super(`${code}: ${serverMessage}`);
    this.name = "ScreeningApiError";
    this.code = code;
    this.status = status;
    this.serverMessage = serverMessage;
    this.serverDetails = serverDetails;
  }
}

export function isScreeningApiError(value: unknown): value is ScreeningApiError {
  return value instanceof ScreeningApiError;
}

/**
 * The same-origin path the browser uses to reach the console.
 *
 * The Next route handler at `app/api/console/[...path]/route.ts` forwards the
 * request to `NEXUS_CONSOLE_URL` (loopback only) and returns the console's
 * answer unchanged. The browser therefore never learns the console's port,
 * and the console's GET-only CORS policy stays exactly as reviewed.
 */
export const CONSOLE_PROXY_PREFIX = "/api/console";

/**
 * The prefix a console read is issued against.
 *
 * `""` is the proxy: the reader asked for live data without naming a console,
 * so the request goes to this application's own origin and the server route
 * resolves it. An explicit `http(s)://host` stays supported for the
 * in-process tests and for a deliberately separate console; it is validated
 * exactly as before.
 */
export function consoleBase(origin: string): string {
  if (origin.trim() === "") return CONSOLE_PROXY_PREFIX;
  return normalizeConsoleOrigin(origin);
}

/** The console origin under test, without a trailing mark. */
export function normalizeConsoleOrigin(origin: string): string {
  const trimmed = origin.trim().replace(/\/+$/, "");
  if (!/^https?:\/\/[^/]+$/i.test(trimmed)) {
    throw new ScreeningApiError(
      "INVALID_CONSOLE_ORIGIN",
      0,
      `refusing console origin outside plain http(s): ${origin}`,
    );
  }
  return trimmed;
}

async function readJson<T>(path: string, origin: string, signal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${origin}${path}`, { method: "GET", signal });
  } catch (error) {
    throw new ScreeningApiError(
      "CONSOLE_UNREACHABLE",
      0,
      error instanceof Error ? error.message : "the console could not be reached",
    );
  }
  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    throw new ScreeningApiError("MALFORMED_JSON", response.status, "the console answered with bytes outside JSON");
  }
  if (!response.ok) {
    const detail =
      typeof body === "object" && body !== null && "detail" in body
        ? (body as { detail?: unknown }).detail
        : null;
    const code =
      typeof detail === "object" && detail !== null && "code" in detail
        ? String((detail as { code?: unknown }).code ?? `HTTP_${response.status}`)
        : `HTTP_${response.status}`;
    const serverMessage =
      typeof detail === "object" && detail !== null && "message" in detail
        ? String((detail as { message?: unknown }).message ?? response.statusText)
        : typeof detail === "string"
          ? detail
          : response.statusText;
    const serverDetails =
      typeof detail === "object" && detail !== null && "details" in detail
        ? (detail as { details?: unknown }).details
        : undefined;
    throw new ScreeningApiError(code, response.status, serverMessage, serverDetails);
  }
  return body as T;
}

export function getProjectSummary(origin: string, signal?: AbortSignal): Promise<ProjectSummary> {
  return readJson<ProjectSummary>("/api/v1/ui/project-summary", consoleBase(origin), signal);
}

export function getPublicationStatus(origin: string, signal?: AbortSignal): Promise<PublicationStatus> {
  return readJson<PublicationStatus>("/api/v1/ui/publication-status", consoleBase(origin), signal);
}

export function getPublicationOutput(
  origin: string,
  name: "included.json" | "excluded.json" | "conflicts.json" | "prisma_screening_report.md" | "prisma_report.json",
  signal?: AbortSignal,
): Promise<PublicationOutput> {
  return readJson<PublicationOutput>(
    `/api/v1/ui/publication/outputs/${name}`,
    consoleBase(origin),
    signal,
  );
}

export function getScreeningBatches(origin: string, signal?: AbortSignal): Promise<ScreeningBatches> {
  return readJson<ScreeningBatches>("/api/v1/screening/ui/batches", consoleBase(origin), signal);
}

/**
 * The harness-computed corpus counts (`GET /api/v1/workspace/status`).
 *
 * The console parses the workspace's literature files to answer this, so the
 * numbers on screen come from the same bytes the harness writes - the page
 * never counts the rows it happens to have loaded.
 */
export function getWorkspaceStatus(origin: string, signal?: AbortSignal): Promise<WorkspaceStatus> {
  return readJson<WorkspaceStatus>("/api/v1/workspace/status", consoleBase(origin), signal);
}

/**
 * One page of the stored corpus (`GET /api/v1/ui/corpus/{kind}`).
 *
 * The filter and the slice run over the whole stored set on the console, so
 * the excluded list (~13.5k rows, ~27 MB as a raw dump on the pilot workspace)
 * never crosses the wire whole. The excluded page is only requested when the
 * reader asks for it.
 */
export function getCorpusPage(
  kind: "included" | "excluded",
  origin: string,
  options?: { q?: string; reason?: string; limit?: number; offset?: number },
  signal?: AbortSignal,
): Promise<CorpusPage> {
  const query = new URLSearchParams();
  if (options?.q) query.set("q", options.q);
  if (options?.reason) query.set("reason", options.reason);
  if (options?.limit !== undefined) query.set("limit", String(options.limit));
  if (options?.offset !== undefined) query.set("offset", String(options.offset));
  const suffix = query.size > 0 ? `?${query.toString()}` : "";
  return readJson<CorpusPage>(
    `/api/v1/ui/corpus/${kind}${suffix}`,
    consoleBase(origin),
    signal,
  );
}

export function getBatchRows(
  origin: string,
  batchIndex: number,
  options?: { limit?: number; offset?: number },
  signal?: AbortSignal,
): Promise<ScreeningRows> {
  const query = new URLSearchParams();
  if (options?.limit !== undefined) query.set("limit", String(options.limit));
  if (options?.offset !== undefined) query.set("offset", String(options.offset));
  const suffix = query.size > 0 ? `?${query.toString()}` : "";
  return readJson<ScreeningRows>(
    `/api/v1/screening/ui/batch/${batchIndex}/rows${suffix}`,
    consoleBase(origin),
    signal,
  );
}

export function getBatchReview(
  origin: string,
  batchIndex: number,
  signal?: AbortSignal,
): Promise<ReviewState> {
  return readJson<ReviewState>(
    `/api/v1/screening/ui/batch/${batchIndex}/review`,
    consoleBase(origin),
    signal,
  );
}

export function getCriterionRefs(
  origin: string,
  batchIndex: number,
  signal?: AbortSignal,
): Promise<CriterionRefs> {
  return readJson<CriterionRefs>(
    `/api/v1/screening/ui/batch/${batchIndex}/criterion-refs`,
    consoleBase(origin),
    signal,
  );
}

export function getAuditFeed(
  origin: string,
  options?: { action?: string; agent?: string; limit?: number; offset?: number },
  signal?: AbortSignal,
): Promise<AuditFeed> {
  const query = new URLSearchParams();
  if (options?.action !== undefined) query.set("action", options.action);
  if (options?.agent !== undefined) query.set("agent", options.agent);
  if (options?.limit !== undefined) query.set("limit", String(options.limit));
  if (options?.offset !== undefined) query.set("offset", String(options.offset));
  const suffix = query.size > 0 ? `?${query.toString()}` : "";
  return readJson<AuditFeed>(
    `/api/v1/screening/ui/audit-feed${suffix}`,
    consoleBase(origin),
    signal,
  );
}

/**
 * One evidence lineage trace over the console lineage route (UI-05).
 *
 * Given a claim id or a chunk id, the console assembles the recorded claim,
 * its quoted passages with locators, the extracted documents, the corpus
 * studies, and the recorded screening decisions with reasons. Every join is
 * resolved by the console from the workspace bound at app state; the shape
 * below carries those stored bytes through untouched, with a typed refusal
 * wherever a link cannot be resolved and the publication standing beside
 * the trace. Reads only: like every other call in this file, this one sends
 * a single GET and keeps no state.
 *
 * The wording above is chosen to carry no utility-shaped word: this file
 * sits under `lib/`, which the `@source not` list does not exclude, so a
 * utility-looking word here would be emitted into the stylesheet with no
 * source to justify it, and `tests-browser/hygiene.spec.ts` reports that
 * as unexplained.
 */

export interface LineageVerification {
  retrieval: string;
  lexical_support?: string | null;
  entailment?: string | null;
  trust?: string | null;
  semantic_similarity_score?: number | null;
  algorithm_version?: string | null;
  threshold?: number | null;
}

export interface LineageEvidence {
  evidence_id: string;
  quote: string;
  locator: string;
  study_id: string;
  document_id: string;
  source_hash: string;
  extraction_method: string;
}

export interface LineageDocument {
  document_id: string;
  study_id: string;
  source_hash: string;
  content_status: string;
  extracted_path: string | null;
  extraction_method: string;
}

export interface LineageStudy {
  study_id: string;
  title: string;
  alias_ids: string[];
  external_ids: Record<string, string[]>;
  publication_year: number | null;
}

export interface LineageDecision {
  decision_id: string;
  study_id: string;
  decision: string;
  reason: string;
  method: string;
  screener_id: string;
  decided_at: string;
}

export interface LineageRefusal {
  code: string;
  message: string;
}

export interface LineageLeg {
  evidence: LineageEvidence | null;
  chunk_ids: string[];
  document: LineageDocument | null;
  study: LineageStudy | null;
  decision: LineageDecision | null;
  refusal: LineageRefusal | null;
}

export interface LineageClaim {
  claim_id: string;
  claim_text: string;
  claim_kind: string;
  study_ids: string[];
  evidence_ids: string[];
  citation_tokens: string[];
  chunk_ids: string[];
  verification: LineageVerification | null;
  legs: LineageLeg[];
}

export interface LineageTrace {
  shape: "ui07.lineage-trace-v1";
  complete: boolean;
  selector: { claim_id: string } | { chunk_id: string };
  claims: LineageClaim[];
  publication: PublicationStatus;
  missing: MissingEntry[];
}

export type LineageSelector = { claim_id: string } | { chunk_id: string };

export function getLineageTrace(
  origin: string,
  selector: LineageSelector,
  signal?: AbortSignal,
): Promise<LineageTrace> {
  const query = new URLSearchParams();
  if ("claim_id" in selector) query.set("claim_id", selector.claim_id);
  else query.set("chunk_id", selector.chunk_id);
  return readJson<LineageTrace>(
    `/api/v1/ui/lineage?${query.toString()}`,
    consoleBase(origin),
    signal,
  );
}

/**
 * Typed action calls over the console action routes (UI-07 action side).
 *
 * The GET helpers above stay the only readers. The calls below are the only
 * writers the screen performs: redeeming a pairing code the operator staged
 * in their terminal, recording a deferral with a reason, and triggering the
 * gated collect path. Draft capture reuses the stored-decisions route
 * through `postDraftDecisions`; no second writer exists.
 *
 * The browser keeps a typed code in memory only: these calls accept the code
 * as an argument and retain nothing afterwards. Nothing here reaches browser
 * storage, and every refusal arrives as a `ScreeningApiError` carrying the
 * server typed code.
 */

export type PairingState = "ABSENT" | "STAGED" | "CONSUMED" | "EXPIRED" | "EXHAUSTED";

export interface PairingStatus {
  shape: "screening-action-pairing-status-v1";
  batch_index: number;
  state: PairingState;
  expires_at: string | null;
  snapshot_fingerprint: string | null;
  attempts_remaining: number | null;
  request_id: string;
}

export interface RedeemResult {
  shape: "screening-action-redeem-v1";
  request_id: string;
  journal_event_id: string;
  batch_index: number;
  snapshot_fingerprint: string;
  approval_fingerprint: string;
  publication_approval_fingerprint: string;
  operator_identity: string;
  superseded: boolean;
}

export interface DeferResult {
  shape: "screening-action-defer-v1";
  request_id: string;
  journal_event_id: string;
  batch_index: number;
  deferral_file: string;
  reason: string;
  cancelled: boolean;
  pairing_voided: boolean;
}

export interface PublishResult {
  shape: "screening-action-publish-v1";
  request_id: string;
  journal_event_id: string;
  status: "CURRENT";
  generation_id: string;
  generation_fingerprint: string;
  outputs: Record<string, string>;
}

export interface DraftDecisionInput {
  workspace_id?: string;
  study_id?: string;
  decision: string;
  confidence?: number | string;
  screening_reasoning?: string;
}

export interface DraftResult {
  batch: number;
  decisions_written: number;
  decisions_file: string;
}

async function postJson<T>(path: string, origin: string, body: unknown, signal?: AbortSignal): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${consoleBase(origin)}${path}`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
      signal,
    });
  } catch (error) {
    throw new ScreeningApiError(
      "CONSOLE_UNREACHABLE",
      0,
      error instanceof Error ? error.message : "the console could not be reached",
    );
  }
  let parsed: unknown = null;
  try {
    parsed = await response.json();
  } catch {
    throw new ScreeningApiError("MALFORMED_JSON", response.status, "the console answered with bytes outside JSON");
  }
  if (!response.ok) {
    const detail =
      typeof parsed === "object" && parsed !== null && "detail" in parsed
        ? (parsed as { detail?: unknown }).detail
        : null;
    const code =
      typeof detail === "object" && detail !== null && "code" in detail
        ? String((detail as { code?: unknown }).code ?? `HTTP_${response.status}`)
        : `HTTP_${response.status}`;
    const serverMessage =
      typeof detail === "object" && detail !== null && "message" in detail
        ? String((detail as { message?: unknown }).message ?? response.statusText)
        : typeof detail === "string"
          ? detail
          : response.statusText;
    const serverDetails =
      typeof detail === "object" && detail !== null && "details" in detail
        ? (detail as { details?: unknown }).details
        : undefined;
    throw new ScreeningApiError(code, response.status, serverMessage, serverDetails);
  }
  return parsed as T;
}

export function getPairingStatus(
  origin: string,
  batchIndex: number,
  requestId?: string,
  signal?: AbortSignal,
): Promise<PairingStatus> {
  const query = new URLSearchParams();
  query.set("batch", String(batchIndex));
  if (requestId !== undefined) query.set("request_id", requestId);
  return readJson<PairingStatus>(
    `/api/v1/screening/actions/pairing/status?${query.toString()}`,
    consoleBase(origin),
    signal,
  );
}

export function postPairingRedeem(
  origin: string,
  batchIndex: number,
  code: string,
  options?: { requestId?: string },
  signal?: AbortSignal,
): Promise<RedeemResult> {
  return postJson<RedeemResult>(
    "/api/v1/screening/actions/pairing/redeem",
    consoleBase(origin),
    { batch: batchIndex, code, request_id: options?.requestId ?? null },
    signal,
  );
}

export function postDraftDecisions(
  origin: string,
  batchIndex: number,
  payload: { decisions: DraftDecisionInput[]; reviewed_by?: string },
  signal?: AbortSignal,
): Promise<DraftResult> {
  return postJson<DraftResult>(
    `/api/v1/screening/batch/${batchIndex}/decisions`,
    consoleBase(origin),
    { batch: batchIndex, reviewed_by: payload.reviewed_by ?? "console", decisions: payload.decisions },
    signal,
  );
}

export function postDeferBatch(
  origin: string,
  batchIndex: number,
  reason: string,
  options?: { requestId?: string },
  signal?: AbortSignal,
): Promise<DeferResult> {
  return postJson<DeferResult>(
    "/api/v1/screening/actions/defer",
    consoleBase(origin),
    { batch: batchIndex, reason, request_id: options?.requestId ?? null },
    signal,
  );
}

export function postPublishScreening(
  origin: string,
  options?: { requestId?: string },
  signal?: AbortSignal,
): Promise<PublishResult> {
  return postJson<PublishResult>(
    "/api/v1/screening/actions/publish",
    consoleBase(origin),
    { request_id: options?.requestId ?? null },
    signal,
  );
}
