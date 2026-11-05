/**
 * The screening API, M1a routes (`docs/architecture/screening-api-contract.md` §3-§4).
 *
 * Types mirror the engine's responses (`src/scholar_harness/console/api/screening_v1.py`)
 * and are checked against the shared fixtures in `tests/fixtures/screening_api/`.
 * The engine is authoritative: this module never derives an outcome, a binding or
 * a refusal code. The only value it creates is a decision event's `event_id`,
 * which the contract assigns to the client (§3.1).
 *
 * Blinding: `getProposal` is the only call that returns the agent's call, and the
 * engine records every first read of it as a reveal (M1b-0). Callers must request
 * it only after the researcher has decided that record, never to prefetch.
 */

import { consoleBase, postJson, readJson } from "./screening-api";

const BASE = "/api/v1/screening";

export type Outcome = "INCLUDE" | "EXCLUDE" | "MAYBE";
export type Answer = "yes" | "no" | "not_reported";
export type QueueView = "needs_you" | "proposal_ready" | "no_proposal" | "title_only" | "decided";
export type EventResult = "accepted" | "duplicate" | "conflict" | "refused";

export interface Binding {
  protocol_fingerprint: string;
  batch_id: string;
  batch_sha256: string;
}

export interface Summary {
  total: number;
  decided: number;
  by_outcome: Record<Outcome, number>;
  agent_proposed: number;
  needs_you: number;
  conflicts: number;
  queued_on_phones?: number;
  lanes: { agent: number; you: number; second_screener: "PARKED" };
}

export interface QueueItem {
  study_id: string;
  title: string;
  batch_id: string;
  has_proposal: boolean;
  decided: boolean;
  flags: string[];
}

export interface QueuePage {
  items: QueueItem[];
  next_cursor: number | null;
}

export interface Criterion {
  id: string;
  text: string;
  kind: "inclusion" | "exclusion";
}

export interface CriterionAnswer {
  id: string;
  answer: Answer;
}

export interface DecisionEvent {
  event_id: string;
  study_id: string;
  screener_id: string;
  method: "HUMAN";
  outcome: Outcome;
  reason_code: string | null;
  note: string | null;
  criteria: CriterionAnswer[];
  decided_at: string;
  device: "desktop" | "phone";
  supersedes: string | null;
  proposal_shown: { proposal_id: string; revealed_after_decision: boolean } | null;
  binding: Binding;
}

/** A stored event: the client fields plus what the engine stamps on intake. */
export interface StoredEvent extends DecisionEvent {
  received_at: string;
  token_scope: string;
  changed_after_reveal: boolean;
}

export interface RecordDetail {
  study_id: string;
  title: string;
  abstract: string | null;
  year: number | null;
  venue: string | null;
  doi: string | null;
  highlights: { start: number; end: number; criterion_id: string }[];
  criteria: Criterion[];
  binding: Binding;
  my_decision: StoredEvent | null;
  history: StoredEvent[];
}

export interface Validator {
  name: string;
  ok: boolean;
  detail: string;
}

export interface Proposal {
  proposal_id: string;
  task_version: string | null;
  model: string | null;
  prompt_sha256: string | null;
  criteria: { id: string; answer: Answer; evidence?: { start: number; end: number; text: string } }[];
  derived_outcome: Outcome;
  reason_code: string | null;
  validators: Validator[];
  cannot_decide: boolean;
}

export interface Refusal {
  code: string;
  message: string;
}

export interface IntakeResult {
  event_id: string;
  result: EventResult;
  refusal?: Refusal;
}

export interface Conflict {
  study_id: string;
  screener_id: string;
  events: StoredEvent[];
}

export interface Settings {
  blinding: "reveal_after_decision" | "show";
  mode: "human_sees_every_record" | "ai_agreed_exclusion";
  sample_audit_size: number | null;
  screener_id: string;
}

export interface PrismaCheck {
  name: string;
  ok: boolean;
  detail: string;
}

export interface PrismaPreview {
  identified: number;
  duplicates_removed: number;
  screened: number;
  excluded: { total: number; by_reason: Record<string, number> };
  unclear_to_full_text: number;
  included: number;
  not_yet_decided: number;
  checks: PrismaCheck[];
}

export interface PairingBegun {
  batch_index: number;
  snapshot_fingerprint: string;
  code_expires_at: string;
  attempt_cap: number;
  code_shown_on: "terminal";
}

export const MAX_EVENTS_PER_REQUEST = 200;

export function getSummary(origin: string, signal?: AbortSignal): Promise<Summary> {
  return readJson<Summary>(`${BASE}/summary`, consoleBase(origin), signal);
}

export function getQueue(
  origin: string,
  options: { view?: QueueView; cursor?: number; limit?: number; order?: "seeded" | "agent_uncertainty" } = {},
  signal?: AbortSignal,
): Promise<QueuePage> {
  const query = new URLSearchParams();
  query.set("view", options.view ?? "needs_you");
  if (options.cursor !== undefined) query.set("cursor", String(options.cursor));
  if (options.limit !== undefined) query.set("limit", String(options.limit));
  if (options.order !== undefined) query.set("order", options.order);
  return readJson<QueuePage>(`${BASE}/queue?${query.toString()}`, consoleBase(origin), signal);
}

export function getRecord(origin: string, studyId: string, signal?: AbortSignal): Promise<RecordDetail> {
  return readJson<RecordDetail>(`${BASE}/records/${encodeURIComponent(studyId)}`, consoleBase(origin), signal);
}

/**
 * The agent's draft for one record. Throws `PROPOSAL_HIDDEN` (403) while
 * blinding is on and the record is undecided. A successful read is recorded by
 * the engine as a reveal, so call it only to show the draft.
 */
export async function getProposal(origin: string, studyId: string, signal?: AbortSignal): Promise<Proposal | null> {
  const body = await readJson<{ proposal: Proposal | null }>(
    `${BASE}/records/${encodeURIComponent(studyId)}/proposal`,
    consoleBase(origin),
    signal,
  );
  return body.proposal;
}

export async function postEvents(origin: string, events: DecisionEvent[], signal?: AbortSignal): Promise<IntakeResult[]> {
  if (events.length > MAX_EVENTS_PER_REQUEST) {
    throw new RangeError(`at most ${MAX_EVENTS_PER_REQUEST} events per request`);
  }
  const body = await postJson<{ results: IntakeResult[] }>(`${BASE}/decisions/events`, origin, { events }, signal);
  return body.results;
}

export async function getConflicts(origin: string, signal?: AbortSignal): Promise<Conflict[]> {
  const body = await readJson<{ items: Conflict[] }>(`${BASE}/decisions/conflicts`, consoleBase(origin), signal);
  return body.items;
}

export async function resolveConflict(
  origin: string,
  studyId: string,
  keepEventId: string,
  signal?: AbortSignal,
): Promise<IntakeResult[]> {
  const body = await postJson<{ results: IntakeResult[] }>(
    `${BASE}/decisions/conflicts/${encodeURIComponent(studyId)}/resolve`,
    origin,
    { keep_event_id: keepEventId },
    signal,
  );
  return body.results;
}

export function getSettings(origin: string, signal?: AbortSignal): Promise<Settings> {
  return readJson<Settings>(`${BASE}/settings`, consoleBase(origin), signal);
}

export function putSettings(
  origin: string,
  update: Partial<Omit<Settings, "screener_id">> & { confirm_ai_agreed_exclusion?: boolean },
  signal?: AbortSignal,
): Promise<Settings> {
  return postJson<Settings>(`${BASE}/settings`, origin, update, signal, "PUT");
}

export function prepare(origin: string, batchSize: number, signal?: AbortSignal): Promise<{ job_id: string }> {
  return postJson<{ job_id: string }>(`${BASE}/prepare`, origin, { batch_size: batchSize }, signal);
}

export function getPrismaPreview(origin: string, signal?: AbortSignal): Promise<PrismaPreview> {
  return readJson<PrismaPreview>(`${BASE}/prisma/preview`, consoleBase(origin), signal);
}

/** Stage approval for one batch. The code is printed in the engine's terminal, never returned. */
export function beginApproval(origin: string, batchIndex: number, signal?: AbortSignal): Promise<PairingBegun> {
  return postJson<PairingBegun>(`${BASE}/actions/pairing/begin`, origin, { batch: batchIndex }, signal);
}

/** A UUIDv7 (RFC 9562): 48-bit Unix milliseconds, then random bits. */
export function newEventId(now: number = Date.now(), random: Uint8Array = crypto.getRandomValues(new Uint8Array(10))): string {
  const bytes = new Uint8Array(16);
  let ms = now;
  for (let i = 5; i >= 0; i -= 1) {
    bytes[i] = ms % 256;
    ms = Math.floor(ms / 256);
  }
  bytes.set(random, 6);
  bytes[6] = (bytes[6] & 0x0f) | 0x70;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}

/** Build one desktop decision event. `supersedes` names the event it replaces (change, undo). */
export function decisionEvent(input: {
  record: Pick<RecordDetail, "study_id" | "binding">;
  screenerId: string;
  outcome: Outcome;
  reasonCode?: string | null;
  criteria: CriterionAnswer[];
  note?: string | null;
  supersedes?: string | null;
  decidedAt?: string;
  eventId?: string;
  /** The draft on screen when deciding, if any (contract §3.1). */
  proposalShown?: DecisionEvent["proposal_shown"];
}): DecisionEvent {
  return {
    event_id: input.eventId ?? newEventId(),
    study_id: input.record.study_id,
    screener_id: input.screenerId,
    method: "HUMAN",
    outcome: input.outcome,
    reason_code: input.outcome === "EXCLUDE" ? (input.reasonCode ?? null) : null,
    note: input.note ?? null,
    criteria: input.criteria,
    decided_at: input.decidedAt ?? new Date().toISOString(),
    device: "desktop",
    supersedes: input.supersedes ?? null,
    proposal_shown: input.proposalShown ?? null,
    binding: input.record.binding,
  };
}

// --- M1b-2: agent runs, calibration and agreement (contract §4, specs 06-07) ---

export type Provider = "anthropic" | "openai_compatible" | "gemini";
export type RunState = "queued" | "running" | "completed" | "stopped" | "cancelled" | "failed";

export interface RunEstimate {
  records: number;
  tokens: { input_tokens: number; cache_read_tokens: number; cache_write_tokens: number; output_tokens: number };
  assumptions: { chars_per_token: number; output_tokens_per_record: number };
  cost_usd: number | null;
  batch: boolean;
  prices_as_of: string;
  priced: boolean;
}

export interface Calibration {
  include_recall: number | null;
  ci_low: number | null;
  missed_includes: string[];
  compared: number;
  advisory: true;
}

export interface RunView {
  run_id: string;
  kind: "proposals" | "calibration";
  state: RunState;
  code: string | null;
  provider: Provider;
  model: string;
  effort: string;
  records: number;
  done: number;
  failed: number;
  refused: number;
  truncated: number;
  invalid: number;
  check_failures: number;
  cost_so_far: number | null;
  cost_ceiling_usd: number | null;
  started_at: string | null;
  finished_at: string | null;
  calibration?: Calibration;
}

export interface ProposalSetup {
  task: { task_version: string; prompt_sha256: string; model: string; effort: string };
  providers: { provider: Provider; key: "keychain" | "environment" | "none"; consent: { accepted_at: string; model: string; prompt_sha256: string } | null }[];
  data_flow: string;
  active_run: string | null;
  latest_run: RunView | null;
}

export interface RunRequest {
  provider: Provider;
  model: string;
  effort: string;
  scope?: { view?: "needs_you" | "no_proposal"; study_ids?: string[] };
  consent?: { provider: Provider; accepted_at: string };
  cost_ceiling_usd?: number | null;
  base_url?: string | null;
  dry_run?: boolean;
}

export interface Agreement {
  decided_with_proposal: number;
  decided_after_seeing_the_draft: number;
  agreement_pct: number | null;
  table_2x2: { both_include: number; you_include_agent_exclude: number; you_exclude_agent_include: number; both_exclude: number };
  splits_by_criterion: { criterion_id: string; n: number }[];
  unclear_either_side: number;
  kappa: null;
  kappa_note: string;
}

export function getProposalSetup(origin: string, signal?: AbortSignal): Promise<ProposalSetup> {
  return readJson<ProposalSetup>(`${BASE}/proposals/setup`, consoleBase(origin), signal);
}

/** The cost estimate for a run; sends nothing to a provider and needs no consent. */
export async function estimateRun(origin: string, run: RunRequest, signal?: AbortSignal): Promise<RunEstimate> {
  const body = await postJson<{ run_id: null; estimate: RunEstimate }>(`${BASE}/proposals/runs`, origin, { ...run, estimate_only: true }, signal);
  return body.estimate;
}

/** Start a run. Records leave the machine only from here, and only with consent on file or in `run.consent`. */
export function startRun(origin: string, run: RunRequest, signal?: AbortSignal): Promise<{ run_id: string; estimate: RunEstimate }> {
  return postJson<{ run_id: string; estimate: RunEstimate }>(`${BASE}/proposals/runs`, origin, run, signal);
}

export function getRun(origin: string, runId: string, signal?: AbortSignal): Promise<RunView> {
  return readJson<RunView>(`${BASE}/proposals/runs/${encodeURIComponent(runId)}`, consoleBase(origin), signal);
}

export function cancelRun(origin: string, runId: string, signal?: AbortSignal): Promise<{ run_id: string; state: RunState }> {
  return postJson<{ run_id: string; state: RunState }>(`${BASE}/proposals/runs/${encodeURIComponent(runId)}/cancel`, origin, {}, signal);
}

/** Check the agent on records you have decided. Advisory: it never blocks a run. */
export function startCalibration(
  origin: string,
  input: { study_ids: string[]; provider: Provider; model: string; effort: string; cost_ceiling_usd?: number | null },
  signal?: AbortSignal,
): Promise<{ run_id: string }> {
  return postJson<{ run_id: string }>(`${BASE}/proposals/calibrations`, origin, input, signal);
}

export function getAgreement(origin: string, signal?: AbortSignal): Promise<Agreement> {
  return readJson<Agreement>(`${BASE}/agreement`, consoleBase(origin), signal);
}
