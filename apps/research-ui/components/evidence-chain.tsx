import type { EvidenceNode } from "@/lib/contracts";

export function EvidenceChain({ nodes }: { nodes: EvidenceNode[] }) {
  return (
    <ol className="divide-y divide-slate-200 rounded-xl border border-slate-200 bg-white shadow-sm">
      {nodes.map((node, index) => (
        <li key={`${node.kind}-${index}`} className="flex gap-4 p-4">
          <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">
            {index + 1}
          </div>
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-700">{node.kind}</p>
            <h3 className="mt-1 font-semibold text-slate-900">{node.label}</h3>
            <p className="mt-1 text-sm text-slate-600">{node.detail}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}
