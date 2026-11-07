"use client";

import { useCallback, useEffect, useMemo, useState, type KeyboardEvent } from "react";

import { formatNumber, type Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge, type DecisionRole } from "@/components/ui/base";
import { DETAILS_LABEL, ScreeningSteps, StateCard, stepHref } from "@/components/screening-state-card";
import { getPublicationStatus, isScreeningApiError, type PublicationStatus } from "@/lib/screening-api";
import {
  DEFAULT_EXPORT_SETS,
  downloadExport,
  getMethods,
  getPrismaPreview,
  type ExportFormat,
  type ExportSet,
  type Methods,
  type PrismaPreview,
} from "@/lib/screening-v1";

/**
 * Export and methods (spec 10, `/screening/export`): after the screening is
 * published, download the decisions (RIS or CSV) and copy the methods
 * paragraph. Nothing here writes: the engine builds the file and the
 * paragraph from the published generation, downloads are not journaled, and
 * the paragraph is shown and copied only (decision 5).
 *
 * The paragraph is engine-written English for a manuscript and is never
 * translated (spec 10, translation boundary): it sits in `lang="en" dir="ltr"`
 * with draft styling, because it is machine text the researcher must check.
 */

const COPY = {
  en: {
    eyebrow: "Screening · export and methods",
    title: "Take your screening with you.",
    lede: "Download the published decisions for a reference manager or a spreadsheet, and copy a methods paragraph that states what the workspace files show.",
    published: "Published · current",
    generation: "Generation",
    loading: "Reading the published screening…",
    differs: "Your current decisions differ from the published ones. The file and paragraph describe the published screening.",
    "methods.title": "Methods paragraph",
    "methods.draftBadge": "Draft · check before you submit",
    "methods.language": "Written in English for a manuscript. Check every number against your PRISMA box.",
    "methods.copy": "Copy paragraph",
    "methods.copied": "Copied",
    "methods.copyFailed": "Copying is blocked here; select the paragraph and copy it yourself.",
    "methods.counts": "PRISMA counts of the published screening",
    "counts.identified": "Records identified",
    "counts.duplicates": "Duplicates removed",
    "counts.screened": "Records screened",
    "counts.excluded": "Excluded",
    "counts.unclear": "Unclear, to full text",
    "counts.included": "Included",
    "counts.reason": "Exclusion reason",
    "counts.records": "Records",
    "methods.notStated": "Not stated",
    "methods.caveats": "Notes",
    "methods.sources": "What this statement is based on",
    "methods.file": "File",
    "methods.digest": "SHA-256",
    "export.title": "Export decisions",
    "export.sets": "Records to include",
    "sets.included": "Included",
    "sets.unclear": "Unclear, to full text",
    "sets.excluded": "Excluded",
    "export.format": "Format",
    "format.ris": "RIS (Zotero, EndNote, Mendeley)",
    "format.csv": "CSV (spreadsheet)",
    "default.ris": "By default RIS holds the included and unclear records; the excluded ones are in the CSV.",
    "default.csv": "By default the CSV holds all three sets.",
    "note.journalType": "All records are written as journal articles: the records carry no publication type.",
    "note.bom": "The CSV opens correctly in Excel.",
    "export.noSet": "Choose at least one set of records.",
    download: "Download",
    preparing: "Preparing the file",
    downloaded: "Downloaded {file}",
    "help.title": "How to open the file",
    "help.ris": "RIS: in Zotero choose File → Import; in EndNote, File → Import → File; in Mendeley, File → Import → RIS.",
    "help.csv": "CSV: open it in a spreadsheet. One row per record, with the decision and the reason code.",
    "empty.title": "Nothing is published yet",
    "empty.body": "Export and the methods paragraph describe a published screening only. Approve and publish it first.",
    goPublish: "Go to Publish",
    goTriage: "Decide the remaining records",
    fingerprint: "Generation fingerprint",
    missing: "Missing file:",
    "phone.desktopOnly": "Export and methods are on your desktop.",
    "phone.toScreening": "Go to screening",
  },
  fr: {
    eyebrow: "Sélection · export et méthodes",
    title: "Emportez votre sélection.",
    lede: "Téléchargez les décisions publiées pour un gestionnaire de références ou un tableur, et copiez un paragraphe de méthodes qui dit ce que montrent les fichiers de l'espace de travail.",
    published: "Publiée · à jour",
    generation: "Génération",
    loading: "Lecture de la sélection publiée…",
    differs: "Vos décisions actuelles diffèrent des décisions publiées. Le fichier et le paragraphe décrivent la sélection publiée.",
    "methods.title": "Paragraphe de méthodes",
    "methods.draftBadge": "Brouillon · à vérifier avant soumission",
    "methods.language": "Rédigé en anglais pour un manuscrit. Vérifiez chaque nombre avec votre diagramme PRISMA.",
    "methods.copy": "Copier le paragraphe",
    "methods.copied": "Copié",
    "methods.copyFailed": "La copie est bloquée ici ; sélectionnez le paragraphe et copiez-le vous-même.",
    "methods.counts": "Effectifs PRISMA de la sélection publiée",
    "counts.identified": "Notices identifiées",
    "counts.duplicates": "Doublons retirés",
    "counts.screened": "Notices examinées",
    "counts.excluded": "Exclues",
    "counts.unclear": "Incertaines, vers le texte intégral",
    "counts.included": "Incluses",
    "counts.reason": "Motif d'exclusion",
    "counts.records": "Notices",
    "methods.notStated": "Non indiqué",
    "methods.caveats": "Remarques",
    "methods.sources": "Sur quoi repose ce paragraphe",
    "methods.file": "Fichier",
    "methods.digest": "Empreinte SHA-256",
    "export.title": "Exporter les décisions",
    "export.sets": "Notices à inclure",
    "sets.included": "Incluses",
    "sets.unclear": "Incertaines, vers le texte intégral",
    "sets.excluded": "Exclues",
    "export.format": "Format de fichier",
    "format.ris": "RIS (Zotero, EndNote, Mendeley)",
    "format.csv": "CSV (tableur)",
    "default.ris": "Par défaut, le RIS contient les notices incluses et incertaines ; les exclues sont dans le CSV.",
    "default.csv": "Par défaut, le CSV contient les trois ensembles.",
    "note.journalType": "Toutes les notices sont écrites comme articles de revue : elles ne portent pas de type de publication.",
    "note.bom": "Le CSV s'ouvre correctement dans Excel.",
    "export.noSet": "Choisissez au moins un ensemble de notices.",
    download: "Télécharger",
    preparing: "Préparation du fichier",
    downloaded: "Téléchargé : {file}",
    "help.title": "Comment ouvrir le fichier",
    "help.ris": "RIS : dans Zotero, Fichier → Importer ; dans EndNote, File → Import → File ; dans Mendeley, File → Import → RIS.",
    "help.csv": "CSV : ouvrez-le dans un tableur. Une ligne par notice, avec la décision et le code du motif.",
    "empty.title": "Rien n'est encore publié",
    "empty.body": "L'export et le paragraphe de méthodes décrivent uniquement une sélection publiée. Approuvez-la et publiez-la d'abord.",
    goPublish: "Aller à Publier",
    goTriage: "Décider les notices restantes",
    fingerprint: "Empreinte de la génération",
    missing: "Fichier manquant :",
    "phone.desktopOnly": "L'export et les méthodes sont sur votre ordinateur.",
    "phone.toScreening": "Aller à la sélection",
  },
  ar: {
    eyebrow: "الفرز · التصدير والمنهجية",
    title: "خذ فرزك معك.",
    lede: "نزّل القرارات المنشورة لبرنامج إدارة المراجع أو لجدول بيانات، وانسخ فقرة منهجية تذكر ما تُظهره ملفات مساحة العمل.",
    published: "منشور · محدَّث",
    generation: "الجيل",
    loading: "جارٍ قراءة الفرز المنشور…",
    differs: "قراراتك الحالية تختلف عن القرارات المنشورة. يصف الملف والفقرة الفرز المنشور.",
    "methods.title": "فقرة المنهجية",
    "methods.draftBadge": "مسودة · راجعها قبل الإرسال",
    "methods.language": "مكتوبة بالإنجليزية لمخطوطة. طابق كل رقم مع مخطط PRISMA الخاص بك.",
    "methods.copy": "نسخ الفقرة",
    "methods.copied": "نُسخت",
    "methods.copyFailed": "النسخ محظور هنا؛ حدّد الفقرة وانسخها بنفسك.",
    "methods.counts": "أعداد PRISMA للفرز المنشور",
    "counts.identified": "السجلات المحددة",
    "counts.duplicates": "التكرارات المحذوفة",
    "counts.screened": "السجلات المفروزة",
    "counts.excluded": "المستبعدة",
    "counts.unclear": "غير واضحة، إلى النص الكامل",
    "counts.included": "المشمولة",
    "counts.reason": "سبب الاستبعاد",
    "counts.records": "السجلات",
    "methods.notStated": "غير مذكور",
    "methods.caveats": "ملاحظات",
    "methods.sources": "ما تستند إليه هذه الفقرة",
    "methods.file": "الملف",
    "methods.digest": "بصمة SHA-256",
    "export.title": "تصدير القرارات",
    "export.sets": "السجلات المطلوب تضمينها",
    "sets.included": "المشمولة",
    "sets.unclear": "غير واضحة، إلى النص الكامل",
    "sets.excluded": "المستبعدة",
    "export.format": "صيغة الملف",
    "format.ris": "RIS (زوتيرو، إندنوت، مندلي)",
    "format.csv": "CSV (جدول بيانات)",
    "default.ris": "افتراضيًا يضم ملف RIS السجلات المشمولة وغير الواضحة؛ والمستبعدة في ملف CSV.",
    "default.csv": "افتراضيًا يضم ملف CSV المجموعات الثلاث.",
    "note.journalType": "تُكتب كل السجلات بوصفها مقالات دوريات: لا تحمل السجلات نوع نشر.",
    "note.bom": "يُفتح ملف CSV بشكل صحيح في إكسل.",
    "export.noSet": "اختر مجموعة واحدة على الأقل من السجلات.",
    download: "تنزيل",
    preparing: "جارٍ تحضير الملف",
    downloaded: "نُزّل {file}",
    "help.title": "كيف تفتح الملف",
    "help.ris": "RIS: في زوتيرو اختر File ← Import؛ وفي إندنوت File ← Import ← File؛ وفي مندلي File ← Import ← RIS.",
    "help.csv": "CSV: افتحه في جدول بيانات. صف لكل سجل، مع القرار ورمز السبب.",
    "empty.title": "لم يُنشر شيء بعد",
    "empty.body": "يصف التصدير وفقرة المنهجية فرزًا منشورًا فقط. وافق عليه وانشره أولًا.",
    goPublish: "الانتقال إلى النشر",
    goTriage: "احسم السجلات المتبقية",
    fingerprint: "بصمة الجيل",
    missing: "الملف المفقود:",
    "phone.desktopOnly": "التصدير والمنهجية على حاسوبك.",
    "phone.toScreening": "الانتقال إلى الفرز",
  },
} as const satisfies Record<Locale, Record<string, string>>;

export type ExportCopyKey = keyof (typeof COPY)["en"];
export const EXPORT_COPY: Record<Locale, Record<ExportCopyKey, string>> = COPY;

const SET_ROLES: Record<ExportSet, DecisionRole> = { included: "include", unclear: "unclear", excluded: "exclude" };
const SETS: readonly ExportSet[] = ["included", "unclear", "excluded"];

function fill(template: string, values: Record<string, string | number> = {}): string {
  return template.replace(/\{(\w+)\}/g, (_, k: string) => {
    if (!(k in values)) throw new Error(`export copy needs {${k}}`);
    return String(values[k]);
  });
}

function consoleOrigin(): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get("console") ?? "";
}

type Refusal = { code: string; message: string; missing?: string };

function refusalOf(error: unknown): Refusal {
  if (!isScreeningApiError(error)) return { code: "ENGINE_UNREACHABLE", message: "" };
  const details = error.serverDetails as { missing?: unknown } | undefined;
  return { code: error.code, message: error.serverMessage, missing: details?.missing ? String(details.missing) : undefined };
}

/**
 * Whether the status says nothing was ever published. Only that case is
 * answered here, without asking for the paragraph; every other status goes to
 * the engine, whose typed refusal decides the card (a stale generation, a
 * missing or tampered published file, a deleted generation record).
 */
function neverPublished(status: PublicationStatus): boolean {
  return status.status === "LEGACY_UNVERIFIED" || (status.status === "MISMATCHED" && Boolean(status.details?.lineage_without_generation));
}

type Loaded = { methods: Methods; preview: PrismaPreview | null };
type State =
  | { status: "loading" }
  | { status: "ready"; data: Loaded }
  | { status: "not_published" }
  | { status: "refused"; refusal: Refusal };

export function ScreeningExport({ locale }: Readonly<{ locale: Locale }>) {
  const t = useCallback((key: ExportCopyKey, values?: Record<string, string | number>) => fill(EXPORT_COPY[locale][key], values), [locale]);
  const n = useCallback((value: number) => formatNumber(locale, value), [locale]);
  const origin = useMemo(consoleOrigin, []);
  const [state, setState] = useState<State>({ status: "loading" });
  const [format, setFormat] = useState<ExportFormat>("ris");
  const [sets, setSets] = useState<ExportSet[]>(DEFAULT_EXPORT_SETS.ris);
  const [downloading, setDownloading] = useState(false);
  const [downloadRefusal, setDownloadRefusal] = useState<Refusal | null>(null);
  const [announce, setAnnounce] = useState("");

  const load = useCallback(async () => {
    setState({ status: "loading" });
    try {
      const status = await getPublicationStatus(origin);
      if (neverPublished(status)) {
        setState({ status: "not_published" });
        return;
      }
      // Not CURRENT: the methods read refuses with the engine's own code.
      const methods = await getMethods(origin);
      // The live preview only tells whether decisions moved since publication;
      // a failed read of it hides that caption and nothing else.
      const preview = await getPrismaPreview(origin).catch(() => null);
      setState({ status: "ready", data: { methods, preview } });
    } catch (error) {
      const refusal = refusalOf(error);
      setState(refusal.code === "EXPORT_NOT_PUBLISHED" ? { status: "not_published" } : { status: "refused", refusal });
    }
  }, [origin]);

  useEffect(() => {
    void load();
  }, [load]);

  function chooseFormat(next: ExportFormat) {
    setFormat(next);
    setSets(DEFAULT_EXPORT_SETS[next]);
  }

  function toggleSet(set: ExportSet) {
    setSets((current) => (current.includes(set) ? current.filter((s) => s !== set) : SETS.filter((s) => s === set || current.includes(s))));
  }

  async function download() {
    setDownloading(true);
    setDownloadRefusal(null);
    setAnnounce(t("preparing"));
    try {
      const { blob, filename } = await downloadExport(origin, format, sets);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
      setAnnounce(t("downloaded", { file: filename }));
    } catch (error) {
      setDownloadRefusal(refusalOf(error));
      setAnnounce("");
    } finally {
      setDownloading(false);
    }
  }

  async function copy(paragraph: string) {
    try {
      await navigator.clipboard.writeText(paragraph);
      setAnnounce(t("methods.copied"));
    } catch {
      setAnnounce(t("methods.copyFailed"));
    }
  }

  const body = (() => {
    if (state.status === "loading") {
      return (
        <p className="text-ink-muted" role="status">
          {t("loading")}
        </p>
      );
    }
    if (state.status === "not_published") {
      return (
        <section aria-labelledby="export-empty" className="rounded-lg border border-rule bg-leaf p-5" data-state="not-published">
          <h1 id="export-empty" className="font-display text-[1.75rem] leading-[2.25rem] text-ink">
            {t("empty.title")}
          </h1>
          <p className="mt-2 max-w-2xl text-ink-muted">{t("empty.body")}</p>
          <div className="mt-4 flex flex-wrap gap-4">
            <a className="inline-flex min-h-11 items-center rounded-md bg-brand px-4 font-medium text-on-brand" href={stepHref(locale, "publish", origin)}>
              {t("goPublish")}
            </a>
            <a className="inline-flex min-h-11 items-center text-brand underline" href={stepHref(locale, "triage", origin)}>
              {t("goTriage")}
            </a>
          </div>
        </section>
      );
    }
    if (state.status === "refused") {
      return (
        <div className="space-y-2">
          <StateCard pageHeading locale={locale} code={state.refusal.code} message={state.refusal.message} consoleOrigin={origin} onRetry={() => void load()} />
          {state.refusal.missing ? (
            <p className="text-sm text-ink-muted">
              {t("missing")} <DataCell>{state.refusal.missing}</DataCell>
            </p>
          ) : null}
        </div>
      );
    }

    const { methods, preview } = state.data;
    const f = methods.figures;
    const reasons = Object.entries(f.exclusion_reasons ?? {}).sort(([a], [b]) => a.localeCompare(b));
    const differs =
      preview !== null &&
      (preview.included !== f.included || preview.excluded.total !== f.excluded || preview.unclear_to_full_text !== f.unclear);
    const setCounts: Record<ExportSet, number> = { included: f.included, unclear: f.unclear, excluded: f.excluded };
    const shortId = methods.generation_id.length > 16 ? `${methods.generation_id.slice(0, 16)}…` : methods.generation_id;

    const onParagraphKey = (event: KeyboardEvent<HTMLElement>) => {
      const target = event.target as HTMLElement;
      if (event.key === "c" && !event.ctrlKey && !event.metaKey && !event.altKey && target.tagName !== "INPUT") {
        event.preventDefault();
        void copy(methods.paragraph);
      }
    };

    return (
      <div className="space-y-6">
        <header>
          <p className="text-xs font-semibold uppercase tracking-[0.05em] text-brand rtl:tracking-normal">{t("eyebrow")}</p>
          <h1 className="font-display mt-1 text-[1.75rem] leading-[2.25rem] text-ink">{t("title")}</h1>
          <p className="mt-1 max-w-3xl text-ink-muted">{t("lede")}</p>
          <p className="mt-3 flex flex-wrap items-center gap-2 text-sm">
            <DecisionBadge role="include">{t("published")}</DecisionBadge>
          </p>
        </header>

        {differs ? (
          <p role="status" className="rounded-md bg-unclear-soft px-4 py-3 text-unclear" data-differs>
            {t("differs")}
          </p>
        ) : null}

        <div className="flex flex-wrap gap-6">
          <div className="min-w-0 flex-[999_1_480px] space-y-6">
            <section aria-labelledby="methods-title" className="rounded-lg border border-rule bg-leaf p-5" onKeyDown={onParagraphKey}>
              <h2 id="methods-title" className="font-semibold text-ink">
                {t("methods.title")}
              </h2>

              <div className="mt-4 rounded-lg border border-dashed border-brand bg-brand-soft p-4">
                <span id="methods-draft">
                  <DecisionBadge role="unclear">{t("methods.draftBadge")}</DecisionBadge>
                </span>
                <p
                  role="region"
                  aria-labelledby="methods-title methods-draft"
                  lang="en"
                  dir="ltr"
                  tabIndex={0}
                  className="mt-3 text-[0.9375rem] leading-[1.5rem] text-ink select-text"
                  data-paragraph
                >
                  {methods.paragraph}
                </p>
              </div>
              <p className="mt-2 text-xs text-ink-muted">{t("methods.language")}</p>
              <div className="mt-3 flex flex-wrap items-center gap-3">
                <Button onClick={() => void copy(methods.paragraph)} data-copy>
                  {t("methods.copy")}
                </Button>
              </div>

              <table className="mt-4 w-full text-sm">
                <caption className="pb-2 text-start text-xs text-ink-muted">{t("methods.counts")}</caption>
                <tbody>
                  {(
                    [
                      ["counts.identified", f.identified],
                      ["counts.duplicates", f.duplicates_removed],
                      ["counts.screened", f.screened],
                      ["counts.excluded", f.excluded],
                      ["counts.unclear", f.unclear],
                      ["counts.included", f.included],
                    ] as [ExportCopyKey, number][]
                  ).map(([key, value]) => (
                    <tr key={key} className="border-t border-rule">
                      <th scope="row" className="py-1.5 text-start font-normal text-ink-muted">
                        {t(key)}
                      </th>
                      <td className="py-1.5 text-end text-ink">{n(value)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {reasons.length > 0 ? (
                <table className="mt-4 w-full text-sm">
                  <thead>
                    <tr className="text-ink-muted">
                      <th scope="col" className="py-1 text-start font-medium">{t("counts.reason")}</th>
                      <th scope="col" className="py-1 text-end font-medium">{t("counts.records")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {reasons.map(([code, count]) => (
                      <tr key={code} className="border-t border-rule">
                        <th scope="row" className="py-1 text-start font-normal">
                          <DataCell>{code}</DataCell>
                        </th>
                        <td className="py-1 text-end">{n(count)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : null}

              {methods.not_stated.length > 0 ? (
                <div className="mt-5">
                  <h3 className="text-sm font-semibold text-ink">{t("methods.notStated")}</h3>
                  <ul lang="en" dir="ltr" className="mt-1 list-disc space-y-1 ps-5 text-sm text-ink-muted">
                    {methods.not_stated.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              ) : null}
              {methods.caveats.length > 0 ? (
                <div className="mt-4">
                  <h3 className="text-sm font-semibold text-ink">{t("methods.caveats")}</h3>
                  <ul lang="en" dir="ltr" className="mt-1 list-disc space-y-1 ps-5 text-sm text-ink-muted">
                    {methods.caveats.map((item) => (
                      <li key={item}>{item}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              <details className="mt-5 text-sm" data-methods-details>
                <summary className="cursor-pointer font-medium text-brand">{DETAILS_LABEL[locale]}</summary>
                <p className="mt-2 flex flex-wrap items-center gap-2 text-xs">
                  <span className="text-ink-muted">{t("generation")}</span>
                  <span title={methods.generation_id}>
                    <DataCell>{shortId}</DataCell>
                  </span>
                </p>
                <p className="mt-1 flex flex-wrap items-center gap-2 text-xs">
                  <span className="text-ink-muted">{t("fingerprint")}</span>
                  <DataCell>{methods.generation_fingerprint}</DataCell>
                </p>
                <h3 className="mt-3 text-sm font-semibold text-ink">{t("methods.sources")}</h3>
                <table className="mt-2 w-full">
                  <thead>
                    <tr className="text-ink-muted">
                      <th scope="col" className="py-1 text-start font-medium">{t("methods.file")}</th>
                      <th scope="col" className="py-1 text-start font-medium">{t("methods.digest")}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {methods.sources.map((source) => (
                      <tr key={source.path} className="border-t border-rule align-top">
                        <td className="py-1 pe-4">
                          <DataCell>{source.path}</DataCell>
                        </td>
                        <td className="py-1">{source.digest ? <DataCell>{source.digest}</DataCell> : null}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </details>
            </section>
          </div>

          <div className="w-full flex-[1_1_320px] space-y-6">
            <section aria-labelledby="export-title" className="rounded-lg border border-rule bg-leaf p-5">
              <h2 id="export-title" className="font-semibold text-ink">
                {t("export.title")}
              </h2>
              <fieldset className="mt-4">
                <legend className="text-sm font-medium text-ink">{t("export.format")}</legend>
                <div className="mt-2 space-y-1">
                  {(["ris", "csv"] as const).map((value) => (
                    <label key={value} className="flex min-h-11 items-center gap-3 text-sm text-ink">
                      <input type="radio" name="export-format" value={value} checked={format === value} onChange={() => chooseFormat(value)} className="size-4 accent-[var(--color-brand)]" />
                      {t(`format.${value}`)}
                    </label>
                  ))}
                </div>
                <p className="mt-1 text-xs text-ink-muted">{t(`default.${format}`)}</p>
              </fieldset>
              <fieldset className="mt-4">
                <legend className="text-sm font-medium text-ink">{t("export.sets")}</legend>
                <div className="mt-2 space-y-1">
                  {SETS.map((set) => (
                    <label key={set} className="flex min-h-11 items-center gap-3 text-sm text-ink" data-set={set}>
                      <input type="checkbox" checked={sets.includes(set)} onChange={() => toggleSet(set)} className="size-4 accent-[var(--color-brand)]" />
                      <DecisionBadge role={SET_ROLES[set]}>{t(`sets.${set}`)}</DecisionBadge>
                      <span className="ms-auto text-ink-muted">{n(setCounts[set])}</span>
                    </label>
                  ))}
                </div>
              </fieldset>
              {sets.length === 0 ? <p className="mt-2 text-sm text-unclear">{t("export.noSet")}</p> : null}
              <Button variant="primary" className="mt-4 w-full" disabled={downloading || sets.length === 0} onClick={() => void download()}>
                {downloading ? t("preparing") : t("download")}
              </Button>
              <p className="mt-3 text-xs text-ink-muted">{t(format === "ris" ? "note.journalType" : "note.bom")}</p>
              {downloadRefusal ? (
                <div className="mt-4">
                  <StateCard locale={locale} code={downloadRefusal.code} message={downloadRefusal.message} consoleOrigin={origin} onRetry={() => void download()} />
                </div>
              ) : null}
            </section>

            <section aria-labelledby="export-help" className="rounded-lg border border-rule bg-leaf p-5 text-sm">
              <h2 id="export-help" className="font-semibold text-ink">
                {t("help.title")}
              </h2>
              <p className="mt-2 text-ink-muted">{t("help.ris")}</p>
              <p className="mt-2 text-ink-muted">{t("help.csv")}</p>
            </section>
          </div>
        </div>

      </div>
    );
  })();

  return (
    <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8 lg:py-14">
      <section className="rounded-lg border border-rule bg-leaf p-5 sm:hidden" data-phone>
        <h1 className="text-base font-normal text-ink">{t("phone.desktopOnly")}</h1>
        <a className="mt-3 inline-flex min-h-11 items-center text-brand underline" href={stepHref(locale, "home", origin)}>
          {t("phone.toScreening")}
        </a>
      </section>
      <div className="hidden sm:block">
        <ScreeningSteps locale={locale} consoleOrigin={origin} />
        <p aria-live="polite" className="sr-only" data-announce>
          {announce}
        </p>
        {body}
      </div>
    </div>
  );
}
