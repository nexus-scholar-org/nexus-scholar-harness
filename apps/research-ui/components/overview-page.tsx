import { translate, translateParts, type Locale, type MessagePart } from "@/i18n";
import { demoEvidence, demoProject } from "@/lib/mock-project";

import { EvidenceChain } from "./evidence-chain";
import { WorkflowTimeline } from "./workflow-timeline";

/**
 * A translated sentence whose substituted values are fixture text.
 *
 * Renders each part of the message in the order the *catalog* gives it: literal
 * chunks as plain text, substituted values inside `<bdi>`. Nothing here decides
 * where a value belongs — that is the template's job — and nothing here
 * concatenates wording, so the sentence in `fr` or `ar` is exactly the sentence
 * in that catalog (D-I18N-02, D-I18N-03).
 *
 * The element's `textContent` is the whole translated sentence with the value
 * substituted, which is what `tests/home-page.test.tsx` asserts, *and* the value
 * is separately assertable as its own node. Both hold at once.
 */
function TranslatedSentence({ parts }: Readonly<{ parts: MessagePart[] }>) {
  return (
    <>
      {parts.map((part, index) =>
        part.kind === "text" ? part.value : <bdi key={index}>{part.value}</bdi>,
      )}
    </>
  );
}

/**
 * The locale overview (packet UI-01c composition, packet UI-01d localization).
 *
 * Composition as a record rather than a dashboard: a masthead whose eyebrow sits
 * in the leading margin, a ruled workflow method, an annotated evidence trail
 * with a hairline spine, and the explanatory note set as an editorial aside with
 * a heavy ink-blue rule instead of a dark panel.
 *
 * This file used to be `app/page.tsx`. It is a component now, not a route,
 * because the route is `app/[locale]/page.tsx` and that route's only job is to
 * decide whether a segment is a supported locale. Moving the composition out of
 * the route also lets the in-process suite render the whole overview in any
 * locale without a router, because locale is a required prop and never a context
 * lookup (D-I18N-05).
 *
 * **Two kinds of text, and the seam between them is the design.** Every string
 * the product is responsible for comes from the catalogs and is rendered as
 * plain text. Every string the frozen fixture is responsible for is rendered
 * inside a `<bdi>` element, byte for byte (D-I18N-02). The element is what tells
 * a reader which is which, and it is also what stops the bidirectional algorithm
 * from reordering an English title inside an Arabic sentence: `<bdi>` isolates
 * the run and lets the browser resolve its own direction for it, so the text
 * stays readable without being reversed. `<bdi>` carries no styling of its own,
 * so the contrast measurements recorded in `GATES.md` §3.7 are unaffected by its
 * insertion.
 *
 * Nothing was removed: the research question, the six fixture stages with their
 * labels, descriptions, states and counts, the claim-to-source trail and the
 * explanatory statement are all still present.
 */
export function OverviewPage({ locale }: Readonly<{ locale: Locale }>) {
  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8 lg:py-14">
        {/* ---- masthead: the record's title block -------------------------- */}
        <section className="grid gap-x-8 gap-y-3 lg:grid-cols-[9rem_minmax(0,1fr)]">
          <p className="text-[0.6875rem] uppercase leading-5 tracking-[0.16em] text-evidence rtl:tracking-normal rtl:text-[0.75rem]">
            {translate(locale, "overview.eyebrow")}
          </p>
          <div className="min-w-0">
            <h1 className="max-w-3xl font-display text-3xl leading-tight text-ink lg:text-4xl">
              <bdi>{demoProject.title}</bdi>
            </h1>
            <p className="mt-4 max-w-3xl text-lg leading-8 text-ink-muted">
              <bdi>{demoProject.researchQuestion}</bdi>
            </p>
            {/*
              The ledger caption: a hanging entry marked by a hairline rule, the
              same treatment the evidence trail uses. It was one text node before
              packet UI-01d and is now several children, because one of them is
              fixture text that has to be isolated from the translated prefix.
            */}
            <p className="mt-6 max-w-3xl border-s border-rule-strong ps-4 text-sm leading-6 text-ink-muted">
              <TranslatedSentence
                parts={translateParts(locale, "overview.lastEvent", {
                  event: demoProject.lastEvent,
                })}
              />
            </p>
          </div>
        </section>

        {/* ---- the workflow record ----------------------------------------- */}
        <section className="mt-14" aria-labelledby="workflow-title">
          <div className="mb-5">
            <h2 id="workflow-title" className="font-display text-xl leading-8 text-ink">
              {translate(locale, "overview.workflowHeading")}
            </h2>
            <p className="mt-1 text-sm leading-6 text-ink-muted">
              {translate(locale, "overview.workflowLede")}
            </p>
          </div>
          <WorkflowTimeline locale={locale} stages={demoProject.stages} />
        </section>

        {/* ---- the evidence trail, with its editorial aside ---------------- */}
        <section
          className="mt-14 grid gap-x-10 gap-y-8 lg:grid-cols-[minmax(0,1fr)_20rem]"
          aria-labelledby="evidence-title"
        >
          <div className="min-w-0">
            <h2 id="evidence-title" className="font-display text-xl leading-8 text-ink">
              {translate(locale, "overview.traceHeading")}
            </h2>
            <p className="mb-5 mt-1 text-sm leading-6 text-ink-muted">
              {translate(locale, "overview.traceLede")}
            </p>
            <EvidenceChain locale={locale} nodes={demoEvidence} />
          </div>
          {/*
            An editorial aside, not a dark callout panel: a heavy ink-blue rule
            down the leading edge and the type in ink. `self-start` is kept from
            UI-00b so the note hugs its content instead of stretching into an
            oversized empty block beside the longer trail.
          */}
          <aside className="self-start border-s-2 border-evidence ps-5">
            <p className="text-[0.6875rem] uppercase leading-5 tracking-[0.16em] text-evidence rtl:tracking-normal rtl:text-[0.75rem]">
              {translate(locale, "overview.asideEyebrow")}
            </p>
            <h2 className="mt-2 font-display text-xl leading-snug text-ink">
              {translate(locale, "overview.asideHeading")}
            </h2>
            <p className="mt-4 text-sm leading-6 text-ink-muted">
              {translate(locale, "overview.asideBody")}
            </p>
          </aside>
        </section>
      </div>
    </div>
  );
}