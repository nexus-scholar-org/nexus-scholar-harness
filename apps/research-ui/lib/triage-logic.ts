/**
 * Presentation rules for the triage screen (spec 03 / 05), kept pure so they
 * are tested without rendering.
 *
 * None of these decide a record. They decide what the screen may *ask for*
 * (the blinding gate), which earlier event an Undo restores, and which reason
 * codes the Exclude chips offer. The engine validates every event it receives;
 * a chip the protocol does not know is refused there (`REASON_CODE_INVALID`).
 */

import type { Criterion, CriterionAnswer, Proposal, Settings, StoredEvent } from "./screening-v1";

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

/** Every criterion answered (the desktop checklist is required, spec 05 §9.3). */
export function checklistComplete(criteria: readonly Criterion[], answers: Readonly<Record<string, CriterionAnswer["answer"]>>): boolean {
  return criteria.every((c) => answers[c.id] !== undefined);
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

function isTextField(target: EventTarget | null): boolean {
  if (typeof HTMLElement === "undefined" || !(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  const tag = target.tagName;
  return tag === "TEXTAREA" || tag === "SELECT" || (tag === "INPUT" && (target as HTMLInputElement).type !== "checkbox" && (target as HTMLInputElement).type !== "radio");
}
