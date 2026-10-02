import type { WorkflowState } from "@/lib/contracts";

/**
 * The state stamp.
 *
 * This is the application's only definition of state colour, and packet UI-01c
 * extends its scope (decision D2) because redesigning the workflow record while
 * leaving a `Record<WorkflowState, string>` of raw `emerald`/`blue`/`slate`/
 * `rose` utilities in place would have left the raw generated palette as the
 * last thing on the screen.
 *
 * It reads as a provenance stamp rather than a pill: square corners, a hairline
 * in the state's own hue, uppercase tracked text and a filled dot. Pill shapes
 * are reserved in `VISUAL_DIRECTION.md` for compact provenance labels and are
 * deliberately not used here, so the one shape that survives the redesign is
 * the mobile dialog panel and the skip-link reveal.
 *
 * Colour is never the only channel: the state word itself is rendered inside
 * the stamp, and each of the four roles carries its own hue (ink-blue for
 * `active`, green for `complete`, ochre for `waiting`, oxide for `refused`).
 * `tests/status-badge.test.tsx` pins the class-string distinctness that the
 * browser suite cannot see, and `tests-browser/` measures the rendered colours.
 */

/** Shared shape. The per-state entry supplies colour only. */
const STAMP_SHAPE =
  "inline-flex items-center gap-1.5 border px-2 py-0.5 text-[0.6875rem] font-medium uppercase leading-4 tracking-[0.12em]";

const styles: Record<WorkflowState, string> = {
  complete: "border-success/45 text-success",
  active: "border-evidence/45 text-evidence",
  waiting: "border-warning/45 text-warning",
  refused: "border-refusal/45 text-refusal",
};

export function StatusBadge({ state }: { state: WorkflowState }) {
  return (
    <span className={`${STAMP_SHAPE} ${styles[state]}`}>
      {/*
        `aria-hidden`, and carrying no text, so the stamp's accessible name and
        its `textContent` are exactly the state word — which is what the
        component test asserts, and what keeps the visible label and the
        announced label the same string.
      */}
      <span aria-hidden="true" className="size-1.5 rounded-full bg-current" />
      {state}
    </span>
  );
}
