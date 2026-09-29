import type { WorkflowStage } from "@/lib/contracts";

import { StatusBadge } from "./status-badge";

export function WorkflowTimeline({ stages }: { stages: WorkflowStage[] }) {
  return (
    <ol className="grid gap-3 lg:grid-cols-3" aria-label="Research workflow">
      {stages.map((stage, index) => (
        <li key={stage.id} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-start justify-between gap-3">
            <div>
              <p className="text-xs font-semibold text-slate-600">Stage {index + 1}</p>
              <h3 className="mt-1 font-semibold text-slate-900">{stage.label}</h3>
            </div>
            <StatusBadge state={stage.state} />
          </div>
          <p className="mt-3 text-sm leading-6 text-slate-600">{stage.description}</p>
          {stage.count !== undefined ? <p className="mt-3 text-2xl font-semibold text-slate-900">{stage.count}</p> : null}
        </li>
      ))}
    </ol>
  );
}
