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
  "overview.eyebrow": "نظرة عامة على المشروع",
  "overview.lastEvent": "آخر حدث: {event}",
  "overview.workflowHeading": "مسار العمل",
  "overview.workflowLede": "تعرض كل مرحلة قراراتها وأدلتها وما رفضته.",
  "overview.traceHeading": "تتبّع من الدعوى إلى المصدر",
  "overview.traceLede": "تتبّع ادعاء بحثي حتى القرار المرتبط بالبروتوكول.",
  "overview.asideEyebrow": "لماذا يهم هذا",
  "overview.asideHeading": "لا تُوثَقُ الخلاصة لمجرد أنها تبدو مقنعة.",
  "overview.asideBody":
    "يتيح Nexus Scholar فحص مسار الأدلة ويرفض المواد التي لا تستوفي سلسلة الأدلة المعلن عنها.",
  "a11y.skipToMain": "تخطَّ إلى المحتوى الرئيسي",
  "shell.tagline": "نزاهة بحث يمكنك التحقق منها",
  "safety.demoDataLabel": "بيانات توضيحية",
  "shell.authorityStatement":
    "عرض توضيحي للقراءة فقط. تبقى منظومة Python هي المرجع في العقود والهوية ومعايير القبول وتنفيذ الأدوات وأحداث التدقيق.",
  "nav.overview": "نظرة عامة",
  "nav.screening": "الفرز",
  "nav.evidence": "الأدلة",
  "nav.audit": "التدقيق",
  "nav.unavailable": "غير متاح بعد",
  "nav.landmark.primary": "التنقل الرئيسي",
  "a11y.openMainNavigation": "فتح قائمة التنقل الرئيسية",
  "a11y.closeMainNavigation": "إغلاق قائمة التنقل الرئيسية",
  "nav.landmark.primaryMobile": "التنقل الرئيسي (قائمة الجوال)",
  "nav.mobileDialogTitle": "القائمة الرئيسية",
  "workflow.listLabel": "مسار عمل البحث",
  "workflow.stageOrdinal": "المرحلة {number}",
  "workflow.stageOrdinal.prefix": "المرحلة ",
  "state.complete": "مكتملة",
  "state.active": "قيد التنفيذ",
  "state.waiting": "لم تبدأ",
  "state.refused": "مرفوضة",
  "evidenceKind.claim": "ادعاء",
  "evidenceKind.chunk": "مقطع",
  "evidenceKind.document": "مستند",
  "evidenceKind.study": "دراسة",
  "evidenceKind.decision": "قرار",
  "locale.selectorLabel": "اللغة",
  "notFound.heading": "الصفحة غير موجودة",
  "notFound.body":
    "لا يحتوي هذا العرض التوضيحي على صفحة عند هذا العنوان. استخدم أحد روابط اللغة أدناه، أو عد إلى النظرة العامة.",
  "notFound.unsupportedLocale": "اللغة «{requested}» غير متاحة. اللغات المتاحة: {available}.",
  "notFound.backToDefault": "العودة إلى النظرة العامة بالإنجليزية",

  // ---- نموذج حالة المشروع (حزمة UI-02): 32 مفتاحًا ----
  "overview.stateHeading": "المرحلة الحالية",
  "overview.stateLede":
    "أين يقف هذا المشروع والإحصاءات التي يحملها السجل. أي إحصاء غير موجود في السجل يُعرض مجهولًا، لا صفريًا.",
  "overview.recordLoadingLabel": "جارٍ التحميل",
  "overview.recordLoading": "لم يصل سجل المشروع بعد. لا يُستنتج شيء أثناء انتظاره.",
  "overview.recordErrorLabel": "غير متاح",
  "overview.recordError": "تعذّر تحميل سجل النظرة العامة. هذه قراءة فاشلة، وليست قرارًا مرفوضًا.",
  "overview.nextDestination": "تابع في {destination}.",
  "phase.empty": "لا مشروع",
  "phase.empty.description": "لم يُنشأ مشروع بعد، فلا توجد دراسات ولا قرارات ولا أدلة لعرضها.",
  "phase.setup": "إعداد",
  "phase.setup.description": "يجري صياغة البروتوكول ومعاييره. يبدأ مسار العمل عند ختم البروتوكول.",
  "phase.search": "بحث",
  "phase.search.description": "تُكتشف السجلات وتُجتَنى من التكرار قبل أي فرز.",
  "phase.screening": "فرز",
  "phase.screening.description": "قرارات الإدراج والاستبعاد بانتظار أن يتخذها باحث. لا يُتخذ أي قرار تلقائيًا.",
  "phase.extraction": "استخلاص",
  "phase.extraction.description": "تُستخلص الدراسات المدرجة، ويحتفظ كل مقطع مستخلص بمساره إلى مصدره.",
  "phase.indexing": "فهرسة",
  "phase.indexing.description": "تُفهرس المقاطع المستخلصة ليستطيع تحليل لاحق استرجاعها مع سلسلة الأدلة سليمة.",
  "phase.refusal": "مرفوض",
  "phase.refusal.description": "رُفضت خطوة من جهة تنفيذها، فلا يحل أي جزئي محلها.",
  "phase.degraded": "متدهور",
  "phase.degraded.description": "جزء من السجل غير متاح. وما لا يحمله السجل يُعرض مجهولًا لا مخمّنًا.",
  "phase.ready": "جاهز",
  "phase.ready.description": "أنتج الفرز والنص الكامل والاستخلاص الدراسات المدرجة. لم يبدأ التقرير الموجّه.",
  "counts.heading": "إحصاءات المجموعة",
  "counts.recordsDiscovered": "السجلات المكتشفة",
  "counts.studiesIncluded": "الدراسات المدرجة",
  "counts.decisionsPending": "قرارات بانتظار شخص",
  "counts.documentsExtracted": "الوثائق المستخلصة",
  "counts.chunksIndexed": "المقاطع المفهرسة",
  "counts.unknown": "مجهول",

  "brand.productName": "Nexus Scholar",

  // ---- مساحة فرز السجلات (حزمة UI-04): 19 مفتاحًا ----
  "screening.eyebrow": "فرز السجلات",
  "screening.heading": "فرز سجل دراسة واحد",
  "screening.lede":
    "اقرأ الاستشهاد والملخص أدناه وفق المعايير المختومة، ثم سجّل قرارك. لا يُتخذ أي قرار تلقائيًا.",
  "screening.recordHeading": "سجل الدراسة",
  "screening.citationLabel": "الاستشهاد المرجعي",
  "screening.abstractLabel": "الملخص",
  "screening.criteriaHeading": "معايير الفرز",
  "screening.criteriaLede":
    "المعايير التي يُفرز هذا السجل وفقها، كما يعلنها البروتوكول.",
  "screening.decisionHeading": "تسجيل قرار",
  "screening.decisionLegend": "القرار",
  "screening.decision.include": "إدراج",
  "screening.decision.exclude": "استبعاد",
  "screening.decision.unclear": "غير محسوم",
  "screening.reasonLabel": "السبب",
  "screening.reasonHint": "مطلوب عند استبعاد السجل.",
  "screening.reasonRequired": "اذكر سببًا قبل استبعاد هذا السجل.",
  "screening.submit": "تسجيل القرار",
  "screening.submitDisabledExplanation":
    "التسجيل معطّل: هذا العرض التوضيحي لا يملك واجهة برمجية للقرارات، فلا يُرسَل أي قرار ولا يُحفظ ولا يُحتسب.",
  "screening.noPersistence":
    "لا يُكتب شيء في هذه الصفحة إلى مساحة عمل ولا إلى ملف ولا إلى هذا المتصفح.",
};

export default ar;