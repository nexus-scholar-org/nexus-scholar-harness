/**
 * Presentation rules for the triage screen (spec 03 / 05), kept pure so they
 * are tested without rendering.
 *
 * None of these decide a record. They decide what the screen may *ask for*
 * (the blinding gate), which earlier event an Undo restores, and which reason
 * codes the Exclude chips offer. The engine validates every event it receives;
 * a chip the protocol does not know is refused there (`REASON_CODE_INVALID`).
 */

import type { Criterion, CriterionAnswer, NotReportedPolicy, Proposal, Settings, StoredEvent } from "./screening-v1";

/**
 * Whether the screen may request the agent's draft for a record.
 *
 * The engine refuses an undecided read while blinding is on, and records every
 * successful read as a reveal (M1b-0). So the screen asks only when the draft
 * would be shown: the record has a draft, and either it is decided or the
 * researcher chose to see drafts beside records. Never to prefetch.
 */
export function mayReadProposal(input: {
  hasProposal: boolean;
  decided: boolean;
  blinding: Settings["blinding"];
}): boolean {
  if (!input.hasProposal) return false;
  return input.decided || input.blinding === "show";
}

/** Exclusion codes first, then `FAILS-<inclusion id>` (contract §3.1). */
export function reasonOptions(criteria: readonly Criterion[]): string[] {
  return [
    ...criteria.filter((c) => c.kind === "exclusion").map((c) => c.id),
    ...criteria.filter((c) => c.kind === "inclusion").map((c) => `FAILS-${c.id}`),
  ];
}

/** Every criterion answered. Not required (M6-beta, answer until decisive; M8-triage, the checklist is optional). */
export function checklistComplete(criteria: readonly Criterion[], answers: Readonly<Record<string, CriterionAnswer["answer"]>>): boolean {
  return criteria.every((c) => answers[c.id] !== undefined);
}

/**
 * What the answers given make possible (spec 03, M8-triage amendment: the
 * checklist is a tool for the reason, not a gate for the decision).
 *
 * - `include`: no answer given fails a criterion. Include needs no answers; it
 *   is off only while the researcher's own answers say the record fails.
 * - `exclude` / `failed`: a criterion fails on the answers given, so Exclude has
 *   its reason from the checklist (the first failure in protocol order). Exclude
 *   itself is always available; without a failure the reason is chosen from the chips.
 * - `includeReady`: every inclusion answered yes and nothing fails.
 *
 * Failing means an inclusion answered no or an exclusion answered yes; under the
 * protocol's `exclude` not-reported policy, an inclusion answered "not reported"
 * fails after the definite failures. This says what the screen may enable; it
 * never decides the record and never fills an unanswered criterion.
 */
export interface Decisiveness {
  include: boolean;
  exclude: boolean;
  failed: { id: string; answer: CriterionAnswer["answer"]; kind: Criterion["kind"] } | null;
  includeReady: boolean;
  /** How many criteria have an answer, of how many. */
  answered: number;
  total: number;
}

export function decisiveFor(
  criteria: readonly Criterion[],
  answers: Readonly<Record<string, CriterionAnswer["answer"]>>,
  /** The protocol's not-reported policy (M7-method, spec 03 amendment 2026-11-08). */
  policy: NotReportedPolicy = "unclear",
): Decisiveness {
  // A definite failure first, in protocol order; under "exclude" an inclusion
  // answered "not reported" fails after it. An exclusion not reported never fails.
  const failing =
    criteria.find(
      (c) => (c.kind === "inclusion" && answers[c.id] === "no") || (c.kind === "exclusion" && answers[c.id] === "yes"),
    ) ?? (policy === "exclude" ? criteria.find((c) => c.kind === "inclusion" && answers[c.id] === "not_reported") : undefined);
  const inclusions = criteria.filter((c) => c.kind === "inclusion");
  return {
    include: failing === undefined,
    exclude: failing !== undefined,
    failed: failing ? { id: failing.id, answer: answers[failing.id], kind: failing.kind } : null,
    includeReady: failing === undefined && inclusions.length > 0 && inclusions.every((c) => answers[c.id] === "yes"),
    answered: criteria.filter((c) => answers[c.id] !== undefined).length,
    total: criteria.length,
  };
}

/**
 * Whether a reason code contradicts an answer the researcher gave: `FAILS-INC-n`
 * with INC-n answered yes, or `EXC-n` with EXC-n answered no. The engine refuses
 * such an event (`REASON_CODE_INCONSISTENT`), so the chip is disabled. Absent and
 * "not reported" answers never contradict.
 */
export function contradicts(code: string, answers: Readonly<Record<string, CriterionAnswer["answer"]>>): boolean {
  const { id, fails } = criterionOfReason(code);
  return fails ? answers[id] === "yes" : answers[id] === "no";
}

/** The reason code the first failed criterion gives (`EXC-n`, or `FAILS-INC-n`). */
export function reasonFromChecklist(failed: Decisiveness["failed"]): string | null {
  if (failed === null) return null;
  return failed.kind === "exclusion" ? failed.id : `FAILS-${failed.id}`;
}

/** The criterion a reason code names, and whether it is a failed inclusion. */
export function criterionOfReason(code: string): { id: string; fails: boolean } {
  return code.startsWith("FAILS-") ? { id: code.slice("FAILS-".length), fails: true } : { id: code, fails: false };
}

/** A chip's label: the criterion's first clause, at most 60 characters (spec 03 amendment 2). */
export function firstClause(text: string, max = 60): string {
  const clause = text.split(/[;:.,(]/)[0].trim() || text.trim();
  return clause.length > max ? `${clause.slice(0, max - 1).trimEnd()}…` : clause;
}

/**
 * "Record k of total" (spec 03 amendment 4): the records already decided plus
 * this record's place in the "Needs you" list. Client-side, from the summary
 * and the loaded queue.
 */
export function positionOf(input: { decided: number; total: number; indexInView: number }): { k: number; total: number } {
  return { k: Math.min(input.decided + input.indexInView + 1, Math.max(input.total, 1)), total: input.total };
}

/** The answers in protocol order, as the event carries them. */
export function answersInOrder(
  criteria: readonly Criterion[],
  answers: Readonly<Record<string, CriterionAnswer["answer"]>>,
): CriterionAnswer[] {
  return criteria.filter((c) => answers[c.id] !== undefined).map((c) => ({ id: c.id, answer: answers[c.id] }));
}

/**
 * The event an Undo restores: the one the current decision superseded.
 *
 * The event log has no "undecided" entry, so a first decision cannot be
 * undone, only changed. Returns null then.
 *
 * Undo is one step: it restores the decision the current one replaced, as a
 * new event. Pressing it again restores the one that undo replaced, so two
 * presses toggle between the last two decisions rather than walking the
 * history back (review 8). The decision history lists every step.
 */
export function undoTarget(current: StoredEvent | null, history: readonly StoredEvent[]): StoredEvent | null {
  if (current === null || current.supersedes === null) return null;
  return history.find((e) => e.event_id === current.supersedes) ?? null;
}

export interface CriterionComparison {
  id: string;
  mine: CriterionAnswer["answer"] | null;
  agent: CriterionAnswer["answer"] | null;
  differs: boolean;
}

/** Your checklist beside the agent's, row by row (spec 05, revealed). */
export function compareAnswers(
  criteria: readonly Criterion[],
  mine: readonly CriterionAnswer[],
  proposal: Proposal,
): CriterionComparison[] {
  const own = new Map(mine.map((a) => [a.id, a.answer]));
  const agent = new Map(proposal.criteria.map((a) => [a.id, a.answer]));
  return criteria.map((c) => {
    const m = own.get(c.id) ?? null;
    const a = agent.get(c.id) ?? null;
    return { id: c.id, mine: m, agent: a, differs: m !== null && a !== null && m !== a };
  });
}

/** A draft whose checks failed is shown as rejected, with the failed checks. */
export function failedChecks(proposal: Proposal): string[] {
  return proposal.validators.filter((v) => !v.ok).map((v) => v.name);
}

/** The draft's answers, open ("not reported") ones first, otherwise in stored order. */
export function proposalAnswersOpenFirst(criteria: Proposal["criteria"]): Proposal["criteria"] {
  return [...criteria.filter((c) => c.answer === "not_reported"), ...criteria.filter((c) => c.answer !== "not_reported")];
}

/** Keys the triage map handles; none fire inside a text field (spec 03). */
export type TriageKey = "include" | "exclude" | "unclear" | "skip" | "undo" | "next" | "down" | "up" | "yes" | "no" | "notReported" | "help";

const KEYMAP: Record<string, TriageKey> = {
  i: "include",
  e: "exclude",
  u: "unclear",
  s: "skip",
  z: "undo",
  n: "next",
  j: "down",
  k: "up",
  "1": "yes",
  "2": "no",
  "3": "notReported",
  "?": "help",
};

export function triageKey(event: Pick<KeyboardEvent, "key" | "ctrlKey" | "metaKey" | "altKey">, target: EventTarget | null): TriageKey | null {
  if (event.ctrlKey || event.metaKey || event.altKey) return null;
  if (isTextField(target)) return null;
  return KEYMAP[event.key.toLowerCase()] ?? null;
}

export function isTextField(target: EventTarget | null): boolean {
  if (typeof HTMLElement === "undefined" || !(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  const tag = target.tagName;
  return tag === "TEXTAREA" || tag === "SELECT" || (tag === "INPUT" && (target as HTMLInputElement).type !== "checkbox" && (target as HTMLInputElement).type !== "radio");
}
