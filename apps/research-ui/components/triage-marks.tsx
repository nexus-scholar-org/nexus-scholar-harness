"use client";

import type { ReactNode } from "react";

import type { Locale } from "@/i18n";
import { Hint } from "@/components/ui/guidance";
import { OTHER_STYLE, termClass, type QuoteSpan, type TermSpan } from "@/components/highlighted-text";
import { pluralTemplate } from "@/lib/plural";
import type { MarkedField, QuotePlace, SearchTerms } from "@/lib/screening-v1";
import { TRIAGE_COPY, tc } from "@/lib/triage-copy";

/**
 * The marks bar of the Triage record pane (spec 03, M8b points 2 and 3): the
 * two switches, the legend of the protocol's concepts and the matching hint.
 * The engine finds the words; this file only lays them out.
 */

export const TERMS_KEY = "nexus.triage.marks.terms";
export const QUOTES_KEY = "nexus.triage.marks.quotes";

/** A switch is on unless this computer remembers it off ("0"). */
export function rememberedOn(key: string): boolean {
  try {
    return typeof window === "undefined" || window.localStorage.getItem(key) !== "0";
  } catch {
    return true;
  }
}

export function rememberOn(key: string, on: boolean) {
  try {
    window.localStorage.setItem(key, on ? "1" : "0");
  } catch {
    /* storage refused: the choice lasts this page only */
  }
}

/** The mark style of the concept at `index`: its own for the first four, then one shared. */
export function styleOf(index: number): number {
  return Math.min(index, OTHER_STYLE);
}

export function termSpans(terms: SearchTerms | undefined, field: MarkedField): TermSpan[] {
  return (terms?.marks ?? [])
    .filter((m) => m.field === field)
    .map((m) => ({ start: m.start, end: m.end, style: styleOf(m.concept) }));
}

export function quoteSpans(quotes: readonly QuotePlace[], field: MarkedField): QuoteSpan[] {
  return quotes
    .filter((q) => q.found && q.field === field && q.start !== null && q.end !== null)
    .map((q) => ({ start: q.start as number, end: q.end as number, key: q.criterion_id }));
}

function Switch({ pressed, onChange, children, name }: Readonly<{ pressed: boolean; onChange: (on: boolean) => void; children: ReactNode; name: string }>) {
  return (
    <button
      type="button"
      aria-pressed={pressed}
      data-marks-switch={name}
      onClick={() => onChange(!pressed)}
      className="inline-flex min-h-11 items-center gap-2 rounded-md border border-rule-strong px-3 text-sm text-ink hover:bg-leaf-raised focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
    >
      <span
        aria-hidden="true"
        className={`inline-flex size-4 items-center justify-center rounded-sm border text-[0.75rem] leading-none ${pressed ? "border-brand bg-brand text-on-brand" : "border-rule-strong text-transparent"}`}
      >
        ✓
      </span>
      {children}
    </button>
  );
}

export function MarksBar({
  locale,
  terms,
  termsOn,
  onTerms,
  quotesAvailable,
  quotesOn,
  onQuotes,
}: Readonly<{
  locale: Locale;
  terms: SearchTerms | undefined;
  termsOn: boolean;
  onTerms: (on: boolean) => void;
  quotesAvailable: boolean;
  quotesOn: boolean;
  onQuotes: (on: boolean) => void;
}>) {
  const t = (key: Parameters<typeof tc>[1], values?: Record<string, string | number>) => tc(locale, key, values);
  const concepts = terms?.concepts ?? [];
  if (!terms && !quotesAvailable) return null;
  const mentioned = concepts.filter((c) => c.mentions > 0).length;
  const status = (n: number) =>
    n > 0
      ? pluralTemplate(locale, "marks.legend.mentions", n, TRIAGE_COPY[locale]["marks.legend.mentions"]).replace("{n}", String(n))
      : t("marks.legend.absent");
  const own = concepts.slice(0, OTHER_STYLE);
  const others = concepts.slice(OTHER_STYLE);
  const othersMentions = others.reduce((sum, c) => sum + c.mentions, 0);
  return (
    <div className="mb-3 space-y-2 border-b border-rule pb-3" data-marks-bar>
      <div role="group" aria-label={t("marks.region")} className="flex flex-wrap items-center gap-2">
        {concepts.length > 0 ? (
          <Switch name="terms" pressed={termsOn} onChange={onTerms}>
            {t("marks.terms.switch")}
          </Switch>
        ) : null}
        {quotesAvailable ? (
          <Switch name="quotes" pressed={quotesOn} onChange={onQuotes}>
            {t("marks.quotes.switch")}
          </Switch>
        ) : null}
        {concepts.length > 0 ? (
          <Hint locale={locale} label={t("marks.hint.label")} text={t("marks.hint.text")} textKey="marks.hint.text" />
        ) : null}
      </div>
      {terms && concepts.length === 0 ? (
        <p className="text-xs text-ink-muted" data-marks-no-concepts>
          {t("marks.noConcepts")}
        </p>
      ) : null}
      {concepts.length > 0 ? (
        <div className="text-xs text-ink-muted" data-marks-legend>
          <p>
            <span id="marks-legend-title" className="font-semibold">
              {t("marks.legend.title")}
            </span>
            <span aria-hidden="true"> · </span>
            <span data-marks-summary>{t("marks.legend.summary", { n: mentioned, m: concepts.length })}</span>
          </p>
          <ul aria-labelledby="marks-legend-title" className="mt-1 flex flex-wrap gap-x-4 gap-y-1">
            {own.map((c, i) => (
              <li key={i} data-concept={i} data-mentions={c.mentions} className="inline-flex items-baseline gap-1.5">
                <span aria-hidden="true" className={`text-ink ${termClass(i)} ${termsOn ? "" : "opacity-40"}`}>
                  Aa
                </span>
                <span className={c.mentions > 0 ? "text-ink" : ""}>
                  {t("marks.legend.item", { name: "⁨" + c.concept + "⁩", status: status(c.mentions) })}
                </span>
              </li>
            ))}
            {others.length > 0 ? (
              <li data-concept="other" data-mentions={othersMentions} className="inline-flex items-baseline gap-1.5">
                <span aria-hidden="true" className={`text-ink ${termClass(OTHER_STYLE)} ${termsOn ? "" : "opacity-40"}`}>
                  Aa
                </span>
                <span className={othersMentions > 0 ? "text-ink" : ""}>
                  {t("marks.legend.item", { name: t("marks.legend.other"), status: status(othersMentions) })}{" "}
                  <span dir="auto">({others.map((c) => c.concept).join(", ")})</span>
                </span>
              </li>
            ) : null}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
