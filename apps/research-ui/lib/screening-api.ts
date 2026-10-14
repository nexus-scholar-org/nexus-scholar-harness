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
  return readJson<ProjectSummary>("/api/v1/ui/project-summary", normalizeConsoleOrigin(origin), signal);
}

export function getPublicationStatus(origin: string, signal?: AbortSignal): Promise<PublicationStatus> {
  return readJson<PublicationStatus>("/api/v1/ui/publication-status", normalizeConsoleOrigin(origin), signal);
}

export function getPublicationOutput(
  origin: string,
  name: "included.json" | "excluded.json" | "conflicts.json" | "prisma_screening_report.md" | "prisma_report.json",
  signal?: AbortSignal,
): Promise<PublicationOutput> {
  return readJson<PublicationOutput>(
    `/api/v1/ui/publication/outputs/${name}`,
    normalizeConsoleOrigin(origin),
    signal,
  );
}

export function getScreeningBatches(origin: string, signal?: AbortSignal): Promise<ScreeningBatches> {
  return readJson<ScreeningBatches>("/api/v1/screening/ui/batches", normalizeConsoleOrigin(origin), signal);
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
    normalizeConsoleOrigin(origin),
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
    normalizeConsoleOrigin(origin),
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
    normalizeConsoleOrigin(origin),
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
    normalizeConsoleOrigin(origin),
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
    response = await fetch(`${origin}${path}`, {
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
    normalizeConsoleOrigin(origin),
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
    normalizeConsoleOrigin(origin),
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
    normalizeConsoleOrigin(origin),
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
    normalizeConsoleOrigin(origin),
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
    normalizeConsoleOrigin(origin),
    { request_id: options?.requestId ?? null },
    signal,
  );
}
