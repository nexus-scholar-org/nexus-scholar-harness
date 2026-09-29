import type { WorkflowState } from "@/lib/contracts";

const styles: Record<WorkflowState, string> = {
  complete: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  active: "bg-blue-50 text-blue-700 ring-blue-600/20",
  waiting: "bg-slate-100 text-slate-600 ring-slate-500/20",
  refused: "bg-rose-50 text-rose-700 ring-rose-600/20",
};

export function StatusBadge({ state }: { state: WorkflowState }) {
  return (
    <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium capitalize ring-1 ring-inset ${styles[state]}`}>
      {state}
    </span>
  );
}
