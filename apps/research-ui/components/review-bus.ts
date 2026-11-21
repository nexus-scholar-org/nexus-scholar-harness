"use client";

/**
 * The next-step bar re-reads its answer after a write the page made and after a
 * discovery job event (`docs/ux/shared/final/04-next-step.md` "When the bar
 * refreshes"): the screens announce it on the window and the bar listens.
 */

export const REVIEW_CHANGED_EVENT = "nexus:review-changed";

export function notifyReviewChanged(): void {
  if (typeof window !== "undefined") window.dispatchEvent(new Event(REVIEW_CHANGED_EVENT));
}

/**
 * M12a Part A (DoD 9): the bar announces each workspace answer it shows, so the
 * site header can offer "Charting" once screening is published without a read
 * of its own. The header remembers the last word for the browser session, for
 * routes where the bar does not read (the workspaces list, triage).
 */
export const NEXT_STEP_ANSWER_EVENT = "nexus:next-step-answer";
export const CHARTING_OPEN_KEY = "nexus.charting.open";

export interface NextStepSignal {
  scope: string;
  phase: string | null;
  state: string;
  round: number;
}

/** Charting is offered once a round is published: phase "published", the PUBLISHED state, or a later round. */
export function chartingOpen(signal: NextStepSignal): boolean {
  return signal.phase === "published" || signal.state === "PUBLISHED" || signal.round > 1;
}

export function announceNextStep(signal: NextStepSignal): void {
  if (typeof window === "undefined" || signal.scope !== "workspace") return;
  try {
    window.sessionStorage.setItem(CHARTING_OPEN_KEY, chartingOpen(signal) ? "1" : "0");
  } catch {
    /* private window: the header still hears the event */
  }
  window.dispatchEvent(new CustomEvent<NextStepSignal>(NEXT_STEP_ANSWER_EVENT, { detail: signal }));
}
