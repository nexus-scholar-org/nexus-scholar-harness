import { LOCALE_METADATA, type Locale } from "./locales";

/**
 * Locale-aware number formatting, and nothing else.
 *
 * The shell renders exactly three kinds of numeric value: the marginal stage
 * ordinal (F01), the per-stage item count (F02) and the evidence trail's step
 * number (F03). All three are *presentation* numbers derived from the frozen
 * fixture, and all three go through here so that `ar` gets Arabic-Indic digits
 * without any catalog knowing about them.
 *
 * What does **not** come through here, and why (packet §4.5): identifiers,
 * slugs, stage ids, checksums, DOIs and refusal codes. Those are machine
 * strings whose byte sequence is part of their meaning; formatting one as a
 * number would corrupt it. If a future packet renders one, it goes inside
 * `<bdi>` and stays byte-exact — not through this function.
 */
export function formatNumber(locale: Locale, value: number): string {
  return new Intl.NumberFormat(LOCALE_METADATA[locale].tag, {
    // Counts in this layout are small (18, 143) and sit in a narrow marginal
    // column. Grouping separators would add a second, locale-dependent glyph
    // to a label that is meant to read as a single unit, and `Intl` would
    // introduce a non-breaking space or a comma that the screenshot and the
    // assertions would then have to carry. `Intl.NumberFormat("en").format(143)`
    // is "143" either way, so this costs the English assertions nothing.
    useGrouping: false,
  }).format(value);
}