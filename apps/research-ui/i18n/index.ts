/**
 * The public surface of the internationalization layer.
 *
 * Everything a component needs comes from here, so a component never imports
 * `messages/en` directly, never builds a key by concatenation, and never
 * reaches into a catalog's internals. The four modules behind it are:
 *
 * - `locales.ts` — which locales exist, and their direction and endonym.
 *   Locale metadata, not messages (D-I18N-06): a language's own name is not
 *   something the product says, and putting it in a catalog would make it
 *   translatable by accident.
 * - `translate.ts` — one message, one key, named holes, loud failures (N3/N4).
 * - `format.ts` — `Intl` numbers, and only numbers (§4.5).
 * - `long-strings.ts` — the env-gated expansion used by the AC-9 gate.
 *
 * Locale travels as an explicit prop (D-I18N-05), so nothing here needs React
 * and nothing here needs a context provider.
 */

export { formatNumber } from "./format";
export {
  DEFAULT_LOCALE,
  LOCALE_METADATA,
  SUPPORTED_LOCALES,
  isSupportedLocale,
  resolveLocale,
  swapLocale,
  type Direction,
  type Locale,
  type LocaleMetadata,
} from "./locales";
export {
  EXPANSION_PERCENT_ENV,
  expansionPercent,
  inflate,
} from "./long-strings";
export {
  MissingMessageError,
  UnmappedTokenError,
  countKey,
  evidenceKindKey,
  navKey,
  placeholdersOf,
  phaseDescriptionKey,
  phaseKey,
  stateKey,
  translate,
  translateParts,
  type MessageKey,
  type MessagePart,
  type MessageValues,
} from "./translate";