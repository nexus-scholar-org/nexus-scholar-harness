/**
 * The supported locales, and the metadata that belongs to a language rather
 * than to a message catalog (packet UI-01d, decision D-I18N-06).
 *
 * Everything here is *locale metadata*: a language's own name, its writing
 * direction, and its BCP-47 tag. None of it is translatable, which is exactly
 * why it does not live in `messages/`. A catalog is a table of things this
 * product says; a language's own name is not something the product says, and
 * putting it in a catalog would make it translatable by accident and would
 * inflate the 41-key parity check with three entries that must never move.
 *
 * There is no negotiation of any kind here. `resolveLocale` is an exact,
 * case-sensitive lookup: `/EN`, `/en-US`, `/fr-FR` and `/ar-EG` are all
 * unsupported and resolve to the default. That is deliberate (D-I18N-01): the
 * URL segment is the only source of locale truth, so the mapping has to be a
 * total, inspectable function of the URL and nothing else.
 */

/** The locales this application ships. Order is load-bearing: it is tab order. */
export const SUPPORTED_LOCALES = ["en", "fr", "ar"] as const;

/** One of the shipped locales. */
export type Locale = (typeof SUPPORTED_LOCALES)[number];

/** The locale an unsupported segment falls back to (D-I18N-01b). */
export const DEFAULT_LOCALE: Locale = "en";

/** Writing direction, as declared on the document element. */
export type Direction = "ltr" | "rtl";

export interface LocaleMetadata {
  /** The value for `<html lang>` and for a selector link's `lang`. */
  readonly lang: Locale;
  /** The value for `<html dir>`. */
  readonly dir: Direction;
  /** BCP-47 tag, used by `Intl`. Never used as a route segment. */
  readonly tag: string;
  /** The language's name in that language. Not translatable, by definition. */
  readonly endonym: string;
}

/**
 * Language names, directions and tags.
 *
 * The endonyms are what a reader of the selector expects to see: a French
 * speaker looking for the French page looks for "Français", not for "French".
 * An endonym is also the only label that can be correct in all three
 * documents at once, which is why the selector uses these instead of the
 * catalogued `locale.*` strings.
 */
export const LOCALE_METADATA: Readonly<Record<Locale, LocaleMetadata>> = {
  en: { lang: "en", dir: "ltr", tag: "en-US", endonym: "English" },
  fr: { lang: "fr", dir: "ltr", tag: "fr-FR", endonym: "Français" },
  ar: { lang: "ar", dir: "rtl", tag: "ar-EG", endonym: "العربية" },
};

/**
 * Is `value` one of the shipped locales?
 *
 * Exact and case-sensitive. `/EN` is not `en`: a URL is a machine identifier,
 * and folding case would make two different URLs resolve to one document
 * without anything recording which spelling the reader used.
 * Use `resolveLocale` for the URL-segment-to-locale mapping that includes
 * case-insensitive and base-language fallback per D-I18N-13B.
 */
export function isSupportedLocale(value: string): value is Locale {
  return (SUPPORTED_LOCALES as readonly string[]).includes(value);
}

/**
 * Extract the base language subtag from a BCP-47 locale tag.
 * e.g., "en-US" -> "en", "fr-FR" -> "fr", "ar-EG" -> "ar", "EN" -> "en".
 */
function extractBaseLocale(value: string): string {
  return value.split("-")[0].toLowerCase();
}

/**
 * The locale to render for a URL segment.
 *
 * Per D-I18N-13B: locale resolution is case-insensitive and falls back to the
 * base language subtag. Supported base locales resolve; unsupported ones 404.
 *   /EN -> en, /en-US -> en, /fr-FR -> fr, /ar-EG -> ar, /de -> DEFAULT_LOCALE (404 at page level)
 */
export function resolveLocale(value: string): Locale {
  const base = extractBaseLocale(value);
  return isSupportedLocale(base) ? base : DEFAULT_LOCALE;
}

/**
 * The same path in another locale: replace or insert the leading segment, keep
 * everything after it.
 *
 * `swapLocale("/fr/evidence?x=1", "ar")` is `/ar/evidence?x=1`, and
 * `swapLocale("/", "ar")` is `/ar`. Preserving the remainder is what makes the
 * selector keep a reader on the equivalent surface as the routes grow, rather
 * than dumping every reader back at the overview.
 *
 * The trailing slash is preserved too, and separately from the query tail: a
 * path is `segments` + `optional slash`, then the query or fragment hangs off
 * the *end* of that, so `/fr/evidence/` becomes `/ar/evidence/` and
 * `/fr/evidence/?x=1` becomes `/ar/evidence/?x=1`. Rebuilding the path from
 * filtered segments alone would silently drop both, which is the kind of change
 * a reader only notices by watching the address bar.
 *
 * The root `/` is not a trailing slash: it has no segments, so it becomes
 * `/ar` rather than `//ar`. That is the one case where the slash is a separator
 * rather than a suffix, and treating it as a suffix would produce a path no
 * route matches.
 */
export function swapLocale(pathname: string, target: Locale): string {
  const [path, suffix] = splitSuffix(pathname);
  const segments = path.split("/").filter((segment) => segment.length > 0);
  const trailingSlash = path.endsWith("/") && segments.length > 0;
  if (segments.length === 0 || isSupportedLocale(segments[0])) {
    segments[0] = target;
  } else {
    segments.unshift(target);
  }
  return `/${segments.join("/")}${trailingSlash ? "/" : ""}${suffix}`;
}

/** Separates a query/fragment tail from the path part, so it is never parsed. */
function splitSuffix(pathname: string): [path: string, suffix: string] {
  const cut = pathname.search(/[?#]/);
  return cut === -1
    ? [pathname, ""]
    : [pathname.slice(0, cut), pathname.slice(cut)];
}