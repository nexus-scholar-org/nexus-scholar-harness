import { formatNumber, translate, type Locale } from "@/i18n";
import { demoScreeningRecord } from "@/lib/mock-screening";

import { ScreeningForm } from "./screening-form";

/**
 * The screening workspace composition (packet UI-04).
 *
 * A server component that renders one demonstration record against the sealed
 * criteria, and hands the decision to `ScreeningForm`. The four sections read
 * as the argument a reviewer actually makes: here is the study (citation and
 * abstract), here is what it must satisfy (the criteria), here is your decision.
 *
 * Three boundaries are structural, not stylistic:
 *
 * - **No `main`.** The shell owns the single `MAIN_CONTENT_ID` landmark, exactly
 *   as it does for the overview; a nested `main` here would give the document
 *   two of them and break the skip link's contract.
 * - **Two kinds of text.** Catalog strings are plain text; every word of the
 *   fixture (citation, abstract, criteria) is rendered byte for byte inside
 *   `<bdi>` (D-I18N-02), so an English citation inside an Arabic page stays
 *   readable instead of being reordered by the bidirectional algorithm. Nothing
 *   here translates fixture prose, and nothing here invents an identifier: the
 *   citation carries no DOI, no accession number, no fingerprint.
 * - **Ordinals are formatted, not literal.** The criteria list numbers itself
 *   with `formatNumber`, so `ar` reads ١٬٢٬٣ in its own numerals rather than
 *   inheriting the page's Latin digits by accident (A4.5), and the marginal
 *   numeral is a real element with real text, mirroring `EvidenceChain`.
 *
 * Heading levels run h1 → h2 only, with no skip: record, criteria, decision.
 * The decision section's `<h2>` is the form's own heading, so the form's
 * `legend` stays a group label instead of competing with it.
 */
export function ScreeningPage({ locale }: Readonly<{ locale: Locale }>) {
  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8 lg:py-14">
        {/* ---- masthead: eyebrow in the leading margin, as on the overview --- */}
        <section className="grid gap-x-8 gap-y-3 lg:grid-cols-[9rem_minmax(0,1fr)]">
          <p className="text-[0.6875rem] uppercase leading-5 tracking-[0.16em] text-evidence rtl:tracking-normal rtl:text-[0.75rem]">
            {translate(locale, "screening.eyebrow")}
          </p>
          <div className="min-w-0">
            <h1 className="max-w-3xl font-display text-3xl leading-tight text-ink lg:text-4xl">
              {translate(locale, "screening.heading")}
            </h1>
            <p className="mt-4 max-w-3xl text-lg leading-8 text-ink-muted">
              {translate(locale, "screening.lede")}
            </p>
          </div>
        </section>

        {/* ---- the record: citation and abstract, as a ruled definition list -- */}
        <section className="mt-14" aria-labelledby="screening-record-title">
          <div className="mb-5">
            <h2 id="screening-record-title" className="font-display text-xl leading-8 text-ink">
              {translate(locale, "screening.recordHeading")}
            </h2>
          </div>
          <dl className="border-t border-rule-strong">
            <div className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-[9rem_minmax(0,1fr)]">
              <dt className="text-sm font-medium leading-6 text-ink">
                {translate(locale, "screening.citationLabel")}
              </dt>
              <dd className="min-w-0 text-sm leading-6 text-ink-muted">
                <bdi>{demoScreeningRecord.citation}</bdi>
              </dd>
            </div>
            <div className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-[9rem_minmax(0,1fr)]">
              <dt className="text-sm font-medium leading-6 text-ink">
                {translate(locale, "screening.abstractLabel")}
              </dt>
              <dd className="min-w-0 text-sm leading-6 text-ink-muted">
                <bdi>{demoScreeningRecord.abstract}</bdi>
              </dd>
            </div>
          </dl>
        </section>

        {/* ---- the sealed criteria, numbered in the reader's own numerals ----- */}
        <section className="mt-14" aria-labelledby="screening-criteria-title">
          <div className="mb-5">
            <h2 id="screening-criteria-title" className="font-display text-xl leading-8 text-ink">
              {translate(locale, "screening.criteriaHeading")}
            </h2>
            <p className="mt-1 text-sm leading-6 text-ink-muted">
              {translate(locale, "screening.criteriaLede")}
            </p>
          </div>
          <ol className="border-t border-rule-strong">
            {demoScreeningRecord.criteria.map((criterion, index) => (
              <li
                key={criterion}
                className="grid grid-cols-[1.5rem_minmax(0,1fr)] gap-x-3 border-b border-rule py-4 lg:grid-cols-[1.75rem_minmax(0,1fr)] lg:gap-x-5"
              >
                {/*
                  The marginal ordinal, the same treatment the evidence trail
                  uses: a real element holding `Intl` output, aligned to the
                  inline end with a logical utility so it sits on the same side
                  of the text in `ar` as in `en`.
                */}
                <span className="pt-0.5 text-end text-[0.6875rem] leading-4 text-ink-faint rtl:text-[0.75rem]">
                  {formatNumber(locale, index + 1)}
                </span>
                <div className="min-w-0 border-s border-rule-strong ps-3 lg:ps-5">
                  <p className="text-sm leading-6 text-ink">
                    <bdi>{criterion}</bdi>
                  </p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        {/* ---- the decision -------------------------------------------------- */}
        <section className="mt-14" aria-labelledby="screening-decision-title">
          <div className="mb-5">
            <h2 id="screening-decision-title" className="font-display text-xl leading-8 text-ink">
              {translate(locale, "screening.decisionHeading")}
            </h2>
          </div>
          <ScreeningForm locale={locale} />
        </section>
      </div>
    </div>
  );
}
