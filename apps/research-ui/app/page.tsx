import { EvidenceChain } from "@/components/evidence-chain";
import { WorkflowTimeline } from "@/components/workflow-timeline";
import { demoEvidence, demoProject } from "@/lib/mock-project";

/**
 * The `/` overview (packet UI-01c).
 *
 * Composition as a record rather than a dashboard: a masthead whose eyebrow sits
 * in the left margin, a ruled workflow table, an annotated evidence trail with a
 * hairline spine, and the explanatory note set as an editorial aside with a
 * heavy ink-blue rule instead of a dark rounded card.
 *
 * Two couplings from `tests/home-page.test.tsx` constrain the markup and are
 * design requirements, not accidents (packet UI-01c §7, finding F6): the
 * `Latest: …` line stays a single text node (it is the F1 contrast site), and
 * the route's total `<li>` count and first level-3 headings are pinned — so no
 * marginal label here is authored as a heading and no nested list is added.
 *
 * Nothing was removed. Research question, four-part workflow summary (six
 * stages in the fixture, with labels, descriptions, states and counts), the
 * claim-to-source trace, and the explanatory statement are all still present and
 * unchanged.
 */
export default function HomePage() {
  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8 lg:py-14">
        {/* ---- masthead: the record's title block -------------------------- */}
        <section className="grid gap-x-8 gap-y-3 lg:grid-cols-[9rem_minmax(0,1fr)]">
          <p className="text-[0.6875rem] uppercase leading-5 tracking-[0.16em] text-evidence">
            Project overview
          </p>
          <div className="min-w-0">
            <h1 className="max-w-3xl font-display text-3xl leading-tight text-ink lg:text-4xl">
              {demoProject.title}
            </h1>
            <p className="mt-4 max-w-3xl text-lg leading-8 text-ink-muted">
              {demoProject.researchQuestion}
            </p>
            {/*
              The ledger caption: a hanging entry marked by a hairline rule, the
              same treatment the evidence trail uses. Single text node — see the
              note above.
            */}
            <p className="mt-6 max-w-3xl border-l border-rule-strong pl-4 text-sm leading-6 text-ink-muted">
              Latest: {demoProject.lastEvent}
            </p>
          </div>
        </section>

        {/* ---- the workflow record ----------------------------------------- */}
        <section className="mt-14" aria-labelledby="workflow-title">
          <div className="mb-5">
            <h2 id="workflow-title" className="font-display text-xl leading-8 text-ink">
              Workflow
            </h2>
            <p className="mt-1 text-sm leading-6 text-ink-muted">
              Every stage exposes its decisions, evidence, and refusals.
            </p>
          </div>
          <WorkflowTimeline stages={demoProject.stages} />
        </section>

        {/* ---- the evidence trail, with its editorial aside ---------------- */}
        <section
          className="mt-14 grid gap-x-10 gap-y-8 lg:grid-cols-[minmax(0,1fr)_20rem]"
          aria-labelledby="evidence-title"
        >
          <div className="min-w-0">
            <h2 id="evidence-title" className="font-display text-xl leading-8 text-ink">
              Claim-to-source trace
            </h2>
            <p className="mb-5 mt-1 text-sm leading-6 text-ink-muted">
              Follow a research claim back to its protocol-bound decision.
            </p>
            <EvidenceChain nodes={demoEvidence} />
          </div>
          {/*
            An editorial aside, not a dark callout card: a heavy ink-blue rule
            down the left edge and the type in ink. `self-start` is kept from
            UI-00b so the note hugs its content instead of stretching into an
            oversized empty block beside the longer trail.
          */}
          <aside className="self-start border-l-2 border-evidence pl-5">
            <p className="text-[0.6875rem] uppercase leading-5 tracking-[0.16em] text-evidence">
              Why this matters
            </p>
            <h2 className="mt-2 font-display text-xl leading-snug text-ink">
              A synthesis is not trusted because it sounds convincing.
            </h2>
            <p className="mt-4 text-sm leading-6 text-ink-muted">
              Nexus Scholar makes the evidence path inspectable and refuses artifacts that do not
              satisfy the declared lineage.
            </p>
          </aside>
        </section>
      </div>
    </div>
  );
}
