import Link from "next/link";

import { DEFAULT_LOCALE, SUPPORTED_LOCALES, translate, translateParts } from "@/i18n";

/**
 * The catalog-backed 404 for an unsupported locale (packet UI-01d, D-I18N-13).
 *
 * The framework's own 404 would be a bare page with no shell, no navigation and
 * no explanation — and, worse, one whose text changes with the framework version.
 * A reader who typed `/de` deserves to be told which locales exist and why that
 * address is not one of them, in the application's own voice, and to be able to
 * get back to a working document from there.
 *
 * Three constraints, all of them about not making things worse:
 *
 * - **English, deliberately.** The locale layout falls back to `en` for an
 *   unsupported segment, so this page renders in English even when the request
 *   was for `/ar-EG`. Declaring a language the reader did not ask for, or
 *   guessing one from `Accept-Language`, would be worse than being explicit: the
 *   document's `lang` is a promise about the text, and the text here is English.
 * - **Exactly one `h1`, no landmark, one focusable control.** The shell already
 *   owns the single `main`; a second one would be a `landmark-one-main`
 *   violation, and a second landmark here would be a fourth `banner` on a page
 *   that is not a banner. The only control is the link back to the default
 *   locale, so the tab order on a 404 is the skip link and that link.
 * - **No duplicated keys.** The strings are read through
 *   `translate(DEFAULT_LOCALE, …)` rather than imported from a catalog, because
 *   this file is not a component that receives a locale prop — it *is* the
 *   default-locale document — and importing a catalog here would add a second
 *   place where a key list has to be kept in step with the first.
 */

/**
 * The refusal that names the refused segment (`T39`'s single template over
 * `{requested}` and `{available}`).
 *
 * **Not wired to a route, on purpose, pending the packet amendment.** Naming the
 * segment requires a component that still knows what the reader asked for, and
 * in Next 16.3.6 there is no such component on a `notFound()` path — measured
 * with temporary probes rather than assumed, and recorded in
 * `app/[locale]/layout.tsx`:
 *
 * - this boundary is invoked with **no props at all**, so `params.locale` does
 *   not exist here;
 * - `headers()` is no help: a request for `/de` arrives with only `host`,
 *   `user-agent`, `accept`, `x-forwarded-host`, `x-forwarded-port`,
 *   `x-forwarded-proto` and `x-forwarded-for`. No header carries the path.
 *
 * Rendering it from the layout would name the segment, but the page that calls
 * `notFound()` is then never rendered and the status becomes 200; rendering it
 * alongside `children` keeps the 404 and produces a served document whose only
 * text is the brand. Neither is a trade this packet may settle on its own, so
 * both are with the packet owner.
 *
 * It stays here, exported and covered, because it is `T39`'s artifact and the
 * amendment decides *where* it is mounted — not whether the reader gets told
 * which locales exist and what was refused.
 */
export function LocaleNotFound({ requested }: Readonly<{ requested: string }>) {
  return (
    <div className="mx-auto max-w-3xl px-6 py-10 lg:px-8 lg:py-14">
      <h1 className="font-display text-3xl leading-tight text-ink">
        {translate(DEFAULT_LOCALE, "notFound.heading")}
      </h1>
      <p className="mt-4 text-base leading-7 text-ink-muted">
        {translate(DEFAULT_LOCALE, "notFound.body")}
      </p>
      <p className="mt-4 text-sm leading-6 text-ink-muted">
        {translateParts(DEFAULT_LOCALE, "notFound.unsupportedLocale", {
          requested,
          available: SUPPORTED_LOCALES.join(", "),
        }).map((part, i) =>
          part.kind === "text" ? (
            <span key={i}>{part.value}</span>
          ) : (
            <bdi key={i}>{part.value}</bdi>
          )
        )}
      </p>
      <p className="mt-6">
        <Link
          href={`/${DEFAULT_LOCALE}`}
          className="text-sm font-medium text-evidence underline decoration-2 underline-offset-4"
        >
          {translate(DEFAULT_LOCALE, "notFound.backToDefault")}
        </Link>
      </p>
    </div>
  );
}

/**
 * The not-found boundary as shipped: everything a reader needs to get back to a
 * working document, minus the segment-naming sentence.
 *
 * `notFound.heading` and `notFound.body` are about "no page at that address"
 * rather than about locales, so both stay true here; the one line this drops is
 * the segment name, because that line is only true where a segment was actually
 * observed. A `{requested}` rendered as an empty string would be worse than
 * silence — it is precisely the failure mode `translate` exists to prevent, and
 * `translate` refuses it.
 */
export default function LocaleNotFoundBoundary() {
  return (
    <div className="mx-auto max-w-3xl px-6 py-10 lg:px-8 lg:py-14">
      <h1 className="font-display text-3xl leading-tight text-ink">
        {translate(DEFAULT_LOCALE, "notFound.heading")}
      </h1>
      <p className="mt-4 text-base leading-7 text-ink-muted">
        {translate(DEFAULT_LOCALE, "notFound.body")}
      </p>
      <p className="mt-6">
        <Link
          href={`/${DEFAULT_LOCALE}`}
          className="text-sm font-medium text-evidence underline decoration-2 underline-offset-4"
        >
          {translate(DEFAULT_LOCALE, "notFound.backToDefault")}
        </Link>
      </p>
    </div>
  );
}