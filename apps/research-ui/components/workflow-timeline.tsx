import type { WorkflowStage } from "@/lib/contracts";

import { StatusBadge } from "./status-badge";

/**
 * The workflow record (packet UI-01c, acceptance A13).
 *
 * This was a `grid` of six interchangeable rounded cards, each carrying a soft
 * drop shadow. It is
 * now ONE record: a single ruled table of the kind a review keeps on paper, with
 * a hairline between entries, a heavier rule above and below the whole
 * sequence, a marginal `Stage N` ordinal, and the state stamp and count set in
 * their own right-hand column.
 *
 * Nothing was removed to achieve that. Every stage still renders its marginal
 * `Stage N`, its label as a level-3 heading, its description, its state stamp
 * and — where the fixture declares one — its count, in that order, and
 * `tests/workflow-timeline.test.tsx` still finds each of them scoped to its own
 * `<li>`.
 *
 * At 375px the columns collapse into label/description first and stamp/count
 * second, still as one entry rather than as a stack of cards; at 1440px all
 * three sit on one baseline, which is what makes the sequence read as a record
 * instead of a row of tiles.
 */
export function WorkflowTimeline({ stages }: { stages: WorkflowStage[] }) {
  return (
    <ol className="border-t border-rule-strong" aria-label="Research workflow">
      {stages.map((stage, index) => (
        <li
          key={stage.id}
          className="grid grid-cols-[4.25rem_minmax(0,1fr)] gap-x-4 gap-y-2 border-b border-rule py-4 lg:grid-cols-[4.25rem_minmax(0,1fr)_6.5rem] lg:items-baseline"
        >
          {/* Marginal ordinal. A real text node, not a CSS counter. */}
          <p className="text-[0.6875rem] uppercase leading-4 tracking-[0.16em] text-ink-faint">
            {`Stage ${index + 1}`}
          </p>

          <div className="min-w-0">
            <h3 className="text-base font-medium text-ink">{stage.label}</h3>
            <p className="mt-1 text-sm leading-6 text-ink-muted">{stage.description}</p>
          </div>

          <div className="col-start-2 flex items-center gap-3 lg:col-start-3 lg:flex-col lg:items-start lg:gap-2">
            <StatusBadge state={stage.state} />
            {stage.count !== undefined ? (
              <p className="text-lg leading-6 text-ink-muted">{stage.count}</p>
            ) : null}
          </div>
        </li>
      ))}
    </ol>
  );
}
