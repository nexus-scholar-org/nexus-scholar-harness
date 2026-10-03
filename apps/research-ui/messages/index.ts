import type { Locale } from "../i18n/locales";
import ar from "./ar";
import en, { type MessageKey } from "./en";
import fr from "./fr";

/**
 * The three catalogs, indexed by locale.
 *
 * The type is the structural guarantee (D-I18N-03, N5): `fr` and `ar` are
 * `Record<MessageKey, string>`, so a key present in `en` and missing from a
 * translation is a *compile* error rather than an `undefined` that renders as
 * nothing at runtime. The value type is `string` and not `typeof en[keyof]`
 * because the literals are the source strings' types only for `en`; the parity
 * that matters is the key set, which `tests/i18n-catalog.test.ts` also asserts
 * at runtime so a `as any` cannot defeat it.
 */
export const CATALOGS: Readonly<Record<Locale, Record<MessageKey, string>>> = {
  en,
  fr,
  ar,
};

/** Every key in the catalog surface, as a runtime array (for parity tests). */
export const MESSAGE_KEYS = Object.keys(en) as readonly MessageKey[];

export { ar, en, fr };
export type { MessageKey };