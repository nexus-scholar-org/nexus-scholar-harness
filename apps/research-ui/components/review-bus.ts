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
