import type { Locale } from "@/i18n";

/**
 * Count wording (H-ui-findings F4). A message that carries a count may have a
 * table entry here, keyed by the copy key; the copy catalogs keep their one
 * string per key (the general form, used for every count with no entry).
 *
 * Which form a count takes is the browser's own CLDR rule (`Intl.PluralRules`):
 * English and French have `one` and `other` (French counts 0 as `one`); Arabic
 * has `zero`, `one`, `two`, `few` (3 to 10), `many` (11 to 99) and `other`
 * (100 and over). A form the table lacks falls back to the catalog string, so
 * an entry lists only the forms that differ. A form may leave out `{n}` when
 * the words carry the number ("one suggestion", Arabic "اقتراح واحد").
 */
export type PluralForm = "zero" | "one" | "two" | "few" | "many" | "other";
export type PluralForms = Partial<Record<PluralForm, string>>;

const EN: Record<string, PluralForms> = {
  "charting.export.done": { one: "Exported {when} ({format}): {n} row. Changes after this are not in that file." },
  "charting.export.cellsOpen": { one: "{n} cell is not charted yet." },
  "charting.export.requiredOpen": { one: "{n} required cell is empty." },
  "charting.export.fileHad": { one: "That file had {n} cell not charted." },
  "proposals.badge": { one: "{n} suggestion" },
  "checks.waiting": { one: "{n} check is waiting for {need}" },
  "checks.earlier": { one: "{n} open check on earlier steps" },
  "checks.CRITERIA_UNDECIDED.sentence": { one: "{n} criterion still needs your decision: Accept or Reject." },
  "checks.REVIEW_PROPOSALS_OPEN.sentence": { one: "{n} suggestion is still open." },
  "checks.DIRECTION_SEEDS_FEW.sentence": { one: "Only {n} recall seed is kept." },
  "checks.EXPLORE_POOL_THIN.sentence": { one: "The sample has only {n} paper. {floor} or more gives steadier suggestions." },
  "checks.REVIEW_TARGET_HAS_SCREENING.sentence": { one: "That workspace has {n} screening decision." },
  "criteria.needYou": { one: "{n} still needs you." },
  "marks.legend.mentions": { one: "{n} mention" },
  "handoff.imports.unchecked": { one: "{n} record comes from your exports. It was not checked against Crossref or OpenAlex, and a missing abstract was not filled in." },
};

const FR: Record<string, PluralForms> = {
  "charting.export.done": { one: "Exporté {when} ({format}) : {n} ligne. Les changements ultérieurs ne sont pas dans ce fichier." },
  "charting.export.cellsOpen": { one: "{n} cellule n'est pas encore extraite." },
  "charting.export.requiredOpen": { one: "{n} cellule obligatoire est vide." },
  "charting.export.fileHad": { one: "Ce fichier avait {n} cellule non extraite." },
  "proposals.badge": { one: "{n} suggestion" },
  "checks.waiting": { one: "{n} vérification attend {need}" },
  "checks.earlier": { one: "{n} vérification ouverte aux étapes précédentes" },
  "checks.CRITERIA_UNDECIDED.sentence": { one: "{n} critère attend encore votre décision : Accepter ou Rejeter." },
  "checks.REVIEW_PROPOSALS_OPEN.sentence": { one: "{n} suggestion est encore ouverte." },
  "checks.DIRECTION_SEEDS_FEW.sentence": { one: "Seulement {n} article de rappel est gardé." },
  "checks.EXPLORE_POOL_THIN.sentence": { one: "L'échantillon ne compte que {n} article. À partir de {floor}, les suggestions sont plus stables." },
  "checks.REVIEW_TARGET_HAS_SCREENING.sentence": { one: "Cet espace de travail a {n} décision de sélection." },
  "criteria.needYou": { one: "{n} attend encore votre décision." },
  "marks.legend.mentions": { one: "{n} mention" },
  "handoff.imports.unchecked": { one: "{n} notice provient de vos exports. Elle n'a pas été vérifiée auprès de Crossref ou d'OpenAlex, et un résumé manquant n'a pas été complété." },
};

const AR: Record<string, PluralForms> = {
  "charting.export.done": {
    one: "صُدّر {when} ({format}): صف واحد. التغييرات بعد ذلك ليست في ذلك الملف.",
    two: "صُدّر {when} ({format}): صفّان. التغييرات بعد ذلك ليست في ذلك الملف.",
    many: "صُدّر {when} ({format}): {n} صفًّا. التغييرات بعد ذلك ليست في ذلك الملف.",
    other: "صُدّر {when} ({format}): {n} صف. التغييرات بعد ذلك ليست في ذلك الملف.",
  },
  "charting.export.cellsOpen": { one: "خلية واحدة لم تُستخرج بعد.", two: "خليتان لم تُستخرجا بعد.", many: "{n} خليةً لم تُستخرج بعد.", other: "{n} خلية لم تُستخرج بعد." },
  "charting.export.requiredOpen": { one: "خلية إلزامية واحدة فارغة.", two: "خليتان إلزاميتان فارغتان.", many: "{n} خليةً إلزامية فارغة.", other: "{n} خلية إلزامية فارغة." },
  "charting.export.fileHad": { one: "كان في ذلك الملف خلية واحدة لم تُستخرج.", two: "كان في ذلك الملف خليتان لم تُستخرجا.", many: "كان في ذلك الملف {n} خليةً لم تُستخرج.", other: "كان في ذلك الملف {n} خلية لم تُستخرج." },
  "marks.legend.mentions": { one: "إشارة واحدة", two: "إشارتان", few: "{n} إشارات", many: "{n} إشارةً", other: "{n} إشارة" },
  "proposals.badge": { one: "اقتراح واحد", two: "اقتراحان", few: "{n} اقتراحات", many: "{n} اقتراحًا", other: "{n} اقتراح" },
  "checks.waiting": {
    one: "فحص واحد بانتظار {need}",
    two: "فحصان بانتظار {need}",
    few: "{n} فحوص بانتظار {need}",
    many: "{n} فحصًا بانتظار {need}",
    other: "{n} فحص بانتظار {need}",
  },
  "checks.earlier": {
    one: "فحص واحد مفتوح في خطوات سابقة",
    two: "فحصان مفتوحان في خطوات سابقة",
    few: "{n} فحوص مفتوحة في خطوات سابقة",
    many: "{n} فحصًا مفتوحًا في خطوات سابقة",
    other: "{n} فحص مفتوح في خطوات سابقة",
  },
  "checks.CRITERIA_UNDECIDED.sentence": {
    one: "معيار واحد ما زال ينتظر قرارك: قبول أو رفض.",
    two: "معياران ما زالا ينتظران قرارك: قبول أو رفض.",
    few: "{n} معايير ما زالت تنتظر قرارك: قبول أو رفض.",
    many: "{n} معيارًا ما زالت تنتظر قرارك: قبول أو رفض.",
    other: "{n} معيار ما زالت تنتظر قرارك: قبول أو رفض.",
  },
  "checks.REVIEW_PROPOSALS_OPEN.sentence": { one: "ما زال اقتراح واحد مفتوحًا.", two: "ما زال اقتراحان مفتوحين." },
  "checks.DIRECTION_SEEDS_FEW.sentence": { one: "احتُفظ بورقة استدعاء واحدة فقط.", two: "احتُفظ بورقتي استدعاء فقط." },
  "checks.EXPLORE_POOL_THIN.sentence": {
    one: "في العينة ورقة واحدة فقط. من {floor} فأكثر تكون الاقتراحات أثبت.",
    two: "في العينة ورقتان فقط. من {floor} فأكثر تكون الاقتراحات أثبت.",
    many: "في العينة {n} ورقة فقط. من {floor} فأكثر تكون الاقتراحات أثبت.",
    other: "في العينة {n} ورقة فقط. من {floor} فأكثر تكون الاقتراحات أثبت.",
  },
  "checks.REVIEW_TARGET_HAS_SCREENING.sentence": {
    one: "في مساحة العمل تلك قرار فرز واحد.",
    two: "في مساحة العمل تلك قراران للفرز.",
    many: "في مساحة العمل تلك {n} قرارًا للفرز.",
    other: "في مساحة العمل تلك {n} قرار فرز.",
  },
  "criteria.needYou": {
    one: "ما زال معيار واحد بانتظار قرارك.",
    two: "ما زال معياران بانتظار قرارك.",
    few: "ما زالت {n} معايير بانتظار قرارك.",
    many: "ما زال {n} معيارًا بانتظار قرارك.",
    other: "ما زال {n} معيار بانتظار قرارك.",
  },
  "handoff.imports.unchecked": {
    one: "سجل واحد من صادراتك. لم يُتحقق منه لدى Crossref أو OpenAlex، ولم يُستكمل ملخصه إن كان ناقصًا.",
    two: "سجلان من صادراتك. لم يُتحقق منهما لدى Crossref أو OpenAlex، ولم تُستكمل الملخصات الناقصة.",
    few: "{n} سجلات من صادراتك. لم يُتحقق منها لدى Crossref أو OpenAlex، ولم تُستكمل الملخصات الناقصة.",
    other: "{n} سجل من صادراتك. لم يُتحقق منها لدى Crossref أو OpenAlex، ولم تُستكمل الملخصات الناقصة.",
  },
};

export const PLURALS: Readonly<Record<Locale, Readonly<Record<string, PluralForms>>>> = { en: EN, fr: FR, ar: AR };

const rules = new Map<Locale, Intl.PluralRules>();

/** The form a count takes in a language (CLDR, through the browser). */
export function pluralForm(locale: Locale, count: number): PluralForm {
  let rule = rules.get(locale);
  if (!rule) {
    rule = new Intl.PluralRules(locale);
    rules.set(locale, rule);
  }
  return rule.select(count) as PluralForm;
}

/** The template for `key` at `count`: the table's form when it has one, else the catalog's own string. */
export function pluralTemplate(locale: Locale, key: string, count: number | undefined, general: string): string {
  if (count === undefined || !Number.isFinite(count)) return general;
  return PLURALS[locale][key]?.[pluralForm(locale, count)] ?? general;
}
