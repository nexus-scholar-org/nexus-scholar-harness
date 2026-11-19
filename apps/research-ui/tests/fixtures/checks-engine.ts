/**
 * The test double of the M10b checks and dismissals (`docs/ux/shared/final/02-checks.md`),
 * shared by the inception and discovery fakes. It keeps the engine's shapes and
 * refusal codes (`src/scholar_harness/inception/checks.py`); which checks fire,
 * and their numbers, are the engine's (Python tests). Tests only.
 */

type Json = Record<string, unknown>;
export type Answer = { status: number; body: unknown; sse?: boolean };

export const INCEPTION_STEPS = ["scope", "explore", "direction", "shape", "criteria", "review"] as const;
export const DISCOVERY_STEPS = ["plan", "recall", "harvest", "dedup", "report", "handoff"] as const;
const LEVELS = ["blocker", "warning", "note"] as const;

const refuse = (status: number, code: string, message = code.toLowerCase(), details?: unknown): Answer => ({
  status,
  body: { detail: { code, message, ...(details ? { details } : {}) } },
});

/** A short content hash (the fake's stand-in for sha256 over the canonical JSON). */
export function digestOf(value: unknown): string {
  let h = 0;
  for (const ch of JSON.stringify(value)) h = (h * 31 + ch.charCodeAt(0)) >>> 0;
  return `sha256:${h.toString(16).padStart(16, "0")}`;
}

export interface CheckIn {
  check_id: string;
  step: string;
  level: "blocker" | "warning" | "note";
  subject?: string;
  params?: Json;
  message_key?: string;
  why_key?: string;
  evidence?: Json[];
  threshold?: Json | null;
  action?: Json;
  refusal?: string | null;
  dismissible?: boolean;
  source?: string;
  /** M10c: fields an assistant's finding adds or replaces (`message`, `agent`, `why`, `outdated`, …). */
  extra?: Json;
}

/** One check object, as the engine builds it. */
export function checkRow(c: CheckIn): Json {
  const subject = c.subject ?? "";
  const evidence = c.evidence ?? [];
  const params = c.params ?? {};
  const action = c.action ?? { kind: "step", step: c.step };
  return {
    check_id: c.check_id,
    subject,
    step: c.step,
    level: c.level,
    source: c.source ?? "check",
    message_key: c.message_key ?? `checks.${c.check_id}.sentence`,
    params,
    message: `${c.check_id} (en, for logs)`,
    why_key: c.why_key ?? `checks.${c.check_id}.why`,
    why_params: params,
    evidence,
    threshold: c.threshold ?? null,
    action: { ...action, label_key: `checks.${c.check_id}.action` },
    refusal: c.level === "blocker" ? (c.refusal ?? "DRAFT_INCOMPLETE") : null,
    dismissible: c.dismissible ?? c.level !== "blocker",
    status: "open",
    dismissal: null,
    previously_dismissed: null,
    evidence_digest: digestOf([c.check_id, subject, evidence]),
    ...(c.extra ?? {}),
  };
}

function last(dismissals: Json[], checkId: string, subject: string): Json | undefined {
  return [...dismissals].reverse().find((d) => d.check_id === checkId && (d.subject ?? "") === subject);
}

/** Each check's status from the dismissal record: dismissed for its own digest, else reopened with `previously_dismissed`. */
export function withDismissals(rows: Json[], dismissals: Json[]): Json[] {
  return rows.map((row) => {
    const entry = last(dismissals, String(row.check_id), String(row.subject));
    if (!entry || entry.action !== "dismissed" || !row.dismissible) return row;
    const stamp = { reason: entry.reason ?? "", at: entry.at };
    return entry.evidence_digest === row.evidence_digest ? { ...row, status: "dismissed", dismissal: stamp } : { ...row, previously_dismissed: stamp };
  });
}

/** The list response for a step, or every step with `by_step` (02-checks "The list response"). */
export function respond(rows: Json[], options: { step?: string; steps: readonly string[]; scope: Json; waiting?: Json[]; partial?: Json[]; ready?: boolean; at: string }): Json {
  const rank = (row: Json) => LEVELS.indexOf(row.level as (typeof LEVELS)[number]);
  const sorted = [...rows].sort((a, b) => rank(a) - rank(b));
  const byStep = Object.fromEntries(options.steps.map((s) => [s, { blocker: 0, warning: 0, note: 0 }])) as Record<string, Record<string, number>>;
  for (const row of sorted) if (row.status === "open" && byStep[String(row.step)]) byStep[String(row.step)][String(row.level)] += 1;
  const items = options.step ? sorted.filter((r) => r.step === options.step) : sorted;
  const waiting = (options.waiting ?? []).filter((w) => !options.step || w.step === options.step);
  const count = (level: string) => items.filter((r) => r.level === level && r.status === "open").length;
  return {
    shape: "checks-v1",
    scope: options.scope,
    computed_at: options.at,
    sources: ["check"],
    checks: items,
    waiting,
    counts: { blocker: count("blocker"), warning: count("warning"), note: count("note"), dismissed: items.filter((r) => r.status === "dismissed").length },
    partial: options.partial ?? [],
    ...(options.step ? {} : { by_step: byStep }),
    ...(options.ready === undefined ? {} : { ready: options.ready }),
  };
}

/** The dismissal or restore entry the engine appends, or its refusal. */
export function dismissal(rows: Json[], dismissals: Json[], checkId: string, action: "dismissed" | "restored", body: Json | null, at: string): { entry?: Json; refused?: Answer } {
  const subject = String(body?.subject ?? "");
  const row = rows.find((r) => r.check_id === checkId && r.subject === subject);
  if (!row) return { refused: refuse(404, "CHECK_NOT_FOUND", `no check ${checkId}`, { check_id: checkId, subject }) };
  if (action === "restored") {
    const prior = last(dismissals, checkId, subject);
    if (!prior || prior.action !== "dismissed") return { refused: refuse(409, "CHECK_NOT_DISMISSED", "this check is not dismissed", { status: row.status }) };
    return { entry: { check_id: checkId, subject, evidence_digest: prior.evidence_digest, action, reason: "", at } };
  }
  if (!row.dismissible) return { refused: refuse(409, "CHECK_NOT_DISMISSIBLE", "this check cannot be dismissed", { level: row.level, refusal: row.refusal }) };
  const reason = String(body?.reason ?? "").trim();
  if (row.level === "warning" && !reason) return { refused: refuse(422, "CHECK_REASON_REQUIRED", "write a short reason", { limit: 2000, level: row.level }) };
  if (body?.evidence_digest !== row.evidence_digest) return { refused: refuse(409, "CHECK_CHANGED", "the data changed", { current: row }) };
  return { entry: { check_id: checkId, subject, evidence_digest: row.evidence_digest, action, reason, at } };
}
