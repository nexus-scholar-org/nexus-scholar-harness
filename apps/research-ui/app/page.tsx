import { EvidenceChain } from "@/components/evidence-chain";
import { WorkflowTimeline } from "@/components/workflow-timeline";
import { demoEvidence, demoProject } from "@/lib/mock-project";

export default function HomePage() {
  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8">
        <section className="max-w-3xl">
          <p className="text-sm font-semibold text-blue-700">Project overview</p>
          <h1 className="mt-2 text-3xl font-semibold tracking-tight text-slate-950">{demoProject.title}</h1>
          <p className="mt-4 text-lg leading-8 text-slate-600">{demoProject.researchQuestion}</p>
          <p className="mt-4 text-sm text-slate-500">Latest: {demoProject.lastEvent}</p>
        </section>

        <section className="mt-10" aria-labelledby="workflow-title">
          <div className="mb-4">
            <h2 id="workflow-title" className="text-xl font-semibold text-slate-950">Workflow</h2>
            <p className="mt-1 text-sm text-slate-600">Every stage exposes its decisions, evidence, and refusals.</p>
          </div>
          <WorkflowTimeline stages={demoProject.stages} />
        </section>

        <section className="mt-12 grid gap-6 lg:grid-cols-[minmax(0,1fr)_22rem]" aria-labelledby="evidence-title">
          <div>
            <h2 id="evidence-title" className="text-xl font-semibold text-slate-950">Claim-to-source trace</h2>
            <p className="mb-4 mt-1 text-sm text-slate-600">Follow a research claim back to its protocol-bound decision.</p>
            <EvidenceChain nodes={demoEvidence} />
          </div>
          <aside className="self-start rounded-xl bg-slate-900 p-6 text-white">
            <p className="text-sm font-semibold text-blue-300">Why this matters</p>
            <h2 className="mt-2 text-xl font-semibold">A synthesis is not trusted because it sounds convincing.</h2>
            <p className="mt-4 text-sm leading-6 text-slate-300">
              Nexus Scholar makes the evidence path inspectable and refuses artifacts that do not satisfy the declared lineage.
            </p>
          </aside>
        </section>
      </div>
    </div>
  );
}
