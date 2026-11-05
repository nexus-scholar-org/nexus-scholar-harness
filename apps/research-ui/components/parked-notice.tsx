import { translate, type Locale } from "@/i18n";

/**
 * The "Not production — parked" banner (production plan §8, M5-slim).
 *
 * Synthesis, the extraction matrix, the citation graph, risk-of-bias/trust and
 * full text are parked: their screens stay, but anything that shows them says so
 * in words, never by quietly removing them. One component, so every parked
 * surface carries the same label; it sits in the page, beside the shell's
 * `Demonstration data` marker, which says something different (where the data
 * comes from, not whether the feature ships). The text is catalogued
 * (`parked.*`), as all chrome on these pages is.
 */

export type ParkedFeature = "overview" | "lineage";

export function ParkedNotice({ locale, feature }: Readonly<{ locale: Locale; feature: ParkedFeature }>) {
  return (
    <aside role="note" data-parked={feature} className="mb-6 border border-dashed border-rule-strong bg-leaf px-4 py-3">
      <p className="text-xs font-semibold uppercase tracking-[0.05em] text-ink rtl:tracking-normal">{translate(locale, "parked.label")}</p>
      <p className="mt-1 text-sm text-ink-muted">{translate(locale, feature === "overview" ? "parked.overview" : "parked.lineage")}</p>
    </aside>
  );
}
