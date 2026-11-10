import type { MessageKey } from "./en";

/**
 * The Arabic catalog.
 *
 * **Demonstration translation.** No fluent reviewer has approved this wording
 * (`README.md`'s i18n policy; packet UI-01d H2). It exists so the mirrored
 * reading flow, the document's `dir="rtl"`, the logical-CSS conversion and the
 * long-string measurement can be exercised in a real right-to-left script, and
 * it must be read as an unreviewed draft until a fluent Arabic reader signs it
 * off. See `I18N.md`.
 *
 * What is deliberately *not* here, and why:
 *
 * - **No Arabic-Indic digits or numbers.** The stage ordinal (`{number}`) and
 *   the stage counts are produced by `Intl.NumberFormat("ar-EG")` at render
 *   (F01–F02), so the digits follow the locale instead of this file. A catalog
 *   that carried a formatted number would freeze one digit shape for every
 *   browser that lacks full ICU.
 * - **No Latin words except the brand.** `brand.productName` stays Latin
 *   because it is a proper name, identical in all three catalogs by design
 *   (§4.2), and D-I18N-02 keeps it byte-identical rather than transliterated.
 * - **No translation of fixture content.** The record's own English text stays
 *   English and is isolated with `<bdi>` (D-I18N-02).
 *
 * Placeholder names match `en.ts` exactly (N4); their positions are Arabic
 * word order, which is why `{requested}` sits inside the quotation marks here
 * and after the noun in English. That is the reason a template is one entry
 * with named holes and never two pre-split fragments.
 */
const ar: Record<MessageKey, string> = {
  "app.meta.description": "مسارات مراجعة منهجية قابلة للتتبع لفرق البحث.",
  "a11y.skipToMain": "تخطَّ إلى المحتوى الرئيسي",
  "shell.descriptor": "فرز المراجعات المنهجية",
  "footer.local":
    "يعمل على هذا الحاسوب. لا يُرسَل شيء إلى أي مكان إلا إذا بدأت مقترحات الوكيل.",
  "footer.journal":
    "يُسجَّل كل قرار في سجل التدقيق الخاص بمساحة العمل.",
  "nav.discovery": "الاستكشاف",
  "nav.screening": "الفرز",
  "nav.workspaces": "مساحات العمل",
  "nav.landmark.primary": "التنقل الرئيسي",
  "a11y.openMainNavigation": "فتح قائمة التنقل الرئيسية",
  "a11y.closeMainNavigation": "إغلاق قائمة التنقل الرئيسية",
  "nav.landmark.primaryMobile": "التنقل الرئيسي (قائمة الجوال)",
  "nav.mobileDialogTitle": "القائمة الرئيسية",
  "locale.selectorLabel": "اللغة",
  "theme.selectorLabel": "المظهر",
  "theme.system": "النظام",
  "theme.light": "فاتح",
  "theme.dark": "داكن",
  "notFound.heading": "الصفحة غير موجودة",
  "notFound.body":
    "لا توجد صفحة بهذا العنوان. استخدم التنقل أعلاه، أو عُد إلى مساحات العمل.",
  "notFound.unsupportedLocale": "اللغة «{requested}» غير متاحة. اللغات المتاحة: {available}.",
  "notFound.backToDefault":
    "العودة إلى مساحات العمل",

  "brand.productName": "Nexus Scholar",
};

export default ar;