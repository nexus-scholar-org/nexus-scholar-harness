import { type Locale } from "./locales";

/**
 * Long-string inflation: an env-gated, test-only transform that lengthens every
 * catalogued string so the layout can be measured under translation expansion
 * (D-I18N-15).
 *
 * Why it exists. A translation of the same sentence is routinely 20–35 % longer
 * than the English, and the way that shows up on a screen is not "longer text"
 * in the abstract: it is a nav label that no longer fits, a state stamp pushed
 * out of its column, a heading that wraps into the block below it. None of that
 * is visible in the English screenshots. So acceptance criterion AC-9 requires
 * a measurement at >= 30 % expansion, and this module is what makes that
 * measurement exist.
 *
 * Three properties it must keep, and a reviewer should check all three:
 *
 * 1. **Off by default.** `expansionPercent()` returns 0 unless the environment
 *    says otherwise, so no production build and no `npm test` run is affected.
 * 2. **Real, not nominal.** The env var is read as the *literal* member
 *    expression `process.env.NEXT_PUBLIC_I18N_EXPANSION_PERCENT`, never as
 *    `process.env[name]`. Next inlines `NEXT_PUBLIC_*` at **build** time by
 *    textual substitution; a computed property lookup is not inlined and would
 *    read `undefined` from a frozen build, which is exactly the vacuous-gate
 *    failure packet §13.2.1 records. The long-strings runner therefore performs
 *    its own `next build` with the variable set (AC-9P).
 * 3. **Script-correct per locale.** The filler is Latin for `en`/`fr` and Arabic
 *    for `ar`, so the `ar` measurement exercises Arabic glyph metrics rather
 *    than a Latin stand-in (D-I18N-15).
 *
 * Filler is appended, never prepended or interleaved: appended text exercises
 * wrapping and truncation at the end of a sentence, which is where a layout
 * breaks first, and it leaves every hole already filled and every `{…}`
 * placeholder count untouched.
 */

/** The environment variable that enables inflation. Spelled out for the record. */
export const EXPANSION_PERCENT_ENV = "NEXT_PUBLIC_I18N_EXPANSION_PERCENT";

/**
 * Filler phrase per locale, appended whole so the result reads like a longer
 * translation rather than a corrupted one.
 */
const FILLER: Readonly<Record<Locale, string>> = {
  en: " extended wording for expansion measurement",
  fr: " formulation étendue pour la mesure d'expansion",
  ar: " صياغة موسعة لقياس تمدد النصوص",
};

/**
 * The configured expansion percentage: an integer in `[0, 100]`.
 *
 * Anything unparseable, negative or absurd reads as 0, so a typo in a CI
 * environment degrades to "no expansion" — a build that renders the real
 * strings — instead of to an unmeasurable or arbitrarily long document.
 */
export function expansionPercent(): number {
  // Literal member expression on purpose; see this module's note (2).
  const raw = process.env.NEXT_PUBLIC_I18N_EXPANSION_PERCENT;
  if (typeof raw !== "string" || raw.trim() === "") {
    return 0;
  }
  const parsed = Number(raw);
  if (!Number.isFinite(parsed)) {
    return 0;
  }
  return Math.min(100, Math.max(0, Math.trunc(parsed)));
}

/**
 * Lengthen `message` by at least `percent` of its own length.
 *
 * Returns the message unchanged when inflation is off, which is the only path
 * production and the unit suite take. The expansion is computed against the
 * message's current length, so the guarantee is
 * `inflated.length >= message.length * (1 + percent / 100)`, and it holds for
 * every locale: the filler is a fixed phrase repeated until the threshold is
 * met, so a short string gets a proportionally short append rather than the
 * same absolute bulk as a paragraph.
 */
export function inflate(locale: Locale, message: string): string {
  const percent = expansionPercent();
  if (percent === 0 || message.length === 0) {
    return message;
  }
  const target = Math.ceil((message.length * percent) / 100);
  const filler = FILLER[locale];
  let inflated = message;
  while (inflated.length - message.length < target) {
    inflated += filler;
  }
  return inflated;
}