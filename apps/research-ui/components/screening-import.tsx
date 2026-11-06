"use client";

import { useCallback, useEffect, useMemo, useRef, useState, type FormEvent } from "react";

import { formatNumber, type Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge } from "@/components/ui/base";
import { ScreeningSteps, StateCard, stepHref } from "@/components/screening-state-card";
import { isScreeningApiError } from "@/lib/screening-api";
import { acceptCorpus, addCorpusSource, fileToBase64, getCorpus, removeCorpusSource, type Corpus, type CorpusDatabase } from "@/lib/screening-v1";

/**
 * Import the corpus (spec 11, M5b): one RIS export per file, labelled with its
 * database, counted, then accepted and frozen. Every count comes from the
 * engine (`GET /corpus`), which runs the snapshot's own deduplicator; the screen
 * adds nothing up. A label may repeat (a database exported in parts) and the
 * engine sums its files into one database row. Search details are optional and
 * sit behind a disclosure; a database without them is flagged "not stated".
 */

const COPY = {
  en: {
    eyebrow: "Screening · Import",
    title: "Import your search results",
    titleAccepted: "What was imported",
    lede: "Add one RIS file for each database you searched. Nothing is final until you accept.",
    ledeAccepted: "This corpus is frozen. Screening starts from it, so the app offers no way to change it.",
    loading: "Reading the import from the engine…",
    addTitle: "Add a database file",
    file: "RIS file (.ris or .txt)",
    fileHelp: "Export your results from the database as RIS, then choose the file. Up to {mb} MB.",
    label: "Database name (required)",
    labelHelp: "A database exported in parts: add each part under the same name; the parts are added up.",
    details: "Search details (optional)",
    searchedOn: "Date searched",
    searchedOnHelp: "The day you ran the search. PRISMA asks for it.",
    query: "Search string",
    queryHelp: "Paste the exact search you ran in this database.",
    add: "Add this file",
    reading: "Reading {file}…",
    added: "Added {file} to {label}.",
    removed: "Removed {file}.",
    databases: "Databases added",
    empty: "No databases added yet.",
    colDatabase: "Database",
    colFiles: "Files",
    colRecords: "Records",
    colSearched: "Date searched",
    colDetails: "Search details",
    stated: "Stated",
    notStated: "Not stated",
    remove: "Remove {file}",
    removeShort: "Remove",
    total: "Total records identified",
    counts: "Counts for your PRISMA flow diagram",
    draft: "Preview · not frozen",
    frozenBadge: "Counted when frozen",
    fromDb: "Records identified from {label}",
    identified: "Records identified, total",
    duplicates: "Duplicate records removed",
    studies: "Studies to screen",
    sentence: "Records identified from: {sources}; duplicate records removed (n = {duplicates}). Studies to screen: {studies}.",
    duplicatesHelp: "A duplicate is the same article found in more than one database, or twice in one file. The app matches them by DOI, then by near-identical title, first author and year (one year either way).",
    notStatedNote: "Search details not stated for: {labels}. Add them in each file's search details, or report them as not stated.",
    sideTitle: "What happens when you accept",
    sideFreeze: "The corpus is frozen as the starting point of screening.",
    sideNoChange: "No database can be added, removed or replaced afterwards.",
    sideFiles: "Copies of your files stay in literature/raw/ris/, and every step is recorded in the audit journal.",
    accept: "Accept and freeze the corpus",
    confirmTitle: "Freeze this corpus?",
    confirmBody: "You are about to freeze {studies} studies from {databases} databases. After this you cannot add, remove or replace a database. Check the counts first.",
    confirm: "Freeze the corpus",
    back: "Go back",
    freezing: "Freezing the corpus…",
    frozen: "Corpus frozen",
    frozenOn: "Frozen on {date}",
    fingerprint: "Corpus fingerprint",
    filesIn: "Copies of your files are in literature/raw/ris/.",
    continue: "Continue to Prepare",
    phone: "Importing is done on your desktop. Open this screen there to add your database files.",
    phoneLink: "Go to screening home",
    discovery: "This workspace's corpus came from the app's own search, not from database files.",
  },
  fr: {
    eyebrow: "Sélection · Import",
    title: "Importez vos résultats de recherche",
    titleAccepted: "Ce qui a été importé",
    lede: "Ajoutez un fichier RIS pour chaque base interrogée. Rien n'est définitif avant votre acceptation.",
    ledeAccepted: "Ce corpus est figé. La sélection part de lui ; l'application ne permet donc pas de le modifier.",
    loading: "Lecture de l'import auprès du moteur…",
    addTitle: "Ajouter un fichier de base",
    file: "Fichier RIS (.ris ou .txt)",
    fileHelp: "Exportez vos résultats depuis la base au format RIS, puis choisissez le fichier. Jusqu'à {mb} Mo.",
    label: "Nom de la base (obligatoire)",
    labelHelp: "Une base exportée en plusieurs parties : ajoutez chaque partie sous le même nom ; les parties sont additionnées.",
    details: "Détails de la recherche (facultatif)",
    searchedOn: "Date de la recherche",
    searchedOnHelp: "Le jour où vous avez lancé la recherche. PRISMA la demande.",
    query: "Équation de recherche",
    queryHelp: "Collez la recherche exacte lancée dans cette base.",
    add: "Ajouter ce fichier",
    reading: "Lecture de {file}…",
    added: "{file} ajouté à {label}.",
    removed: "{file} retiré.",
    databases: "Bases ajoutées",
    empty: "Aucune base ajoutée pour l'instant.",
    colDatabase: "Base",
    colFiles: "Fichiers",
    colRecords: "Notices",
    colSearched: "Date de recherche",
    colDetails: "Détails de la recherche",
    stated: "Indiqués",
    notStated: "Non indiqués",
    remove: "Retirer {file}",
    removeShort: "Retirer",
    total: "Total des notices identifiées",
    counts: "Totaux pour votre diagramme de flux PRISMA",
    draft: "Aperçu · non figé",
    frozenBadge: "Comptés au gel",
    fromDb: "Notices identifiées dans {label}",
    identified: "Notices identifiées, total",
    duplicates: "Doublons retirés",
    studies: "Études à examiner",
    sentence: "Notices identifiées dans : {sources} ; doublons retirés (n = {duplicates}). Études à examiner : {studies}.",
    duplicatesHelp: "Un doublon est le même article trouvé dans plusieurs bases, ou deux fois dans un fichier. L'application les repère par DOI, puis par titre quasi identique, premier auteur et année (à un an près).",
    notStatedNote: "Détails de la recherche non indiqués pour : {labels}. Ajoutez-les dans les détails de chaque fichier, ou déclarez-les non indiqués.",
    sideTitle: "Ce qui se passe quand vous acceptez",
    sideFreeze: "Le corpus est figé comme point de départ de la sélection.",
    sideNoChange: "Aucune base ne peut ensuite être ajoutée, retirée ou remplacée.",
    sideFiles: "Des copies de vos fichiers restent dans literature/raw/ris/, et chaque étape est consignée dans le journal d'audit.",
    accept: "Accepter et figer le corpus",
    confirmTitle: "Figer ce corpus ?",
    confirmBody: "Vous allez figer {studies} études issues de {databases} bases. Ensuite, vous ne pourrez plus ajouter, retirer ni remplacer de base. Vérifiez d'abord les totaux.",
    confirm: "Figer le corpus",
    back: "Revenir",
    freezing: "Gel du corpus…",
    frozen: "Corpus figé",
    frozenOn: "Figé le {date}",
    fingerprint: "Empreinte du corpus",
    filesIn: "Des copies de vos fichiers sont dans literature/raw/ris/.",
    continue: "Continuer vers Préparer",
    phone: "L'import se fait sur votre ordinateur. Ouvrez cet écran sur celui-ci pour ajouter vos fichiers de bases.",
    phoneLink: "Aller à l'accueil de la sélection",
    discovery: "Le corpus de cet espace vient de la recherche de l'application, pas de fichiers de bases.",
  },
  ar: {
    eyebrow: "الفرز · الاستيراد",
    title: "استورد نتائج بحثك",
    titleAccepted: "ما استُورد",
    lede: "أضف ملف RIS واحدًا لكل قاعدة بيانات بحثت فيها. لا شيء نهائي حتى تقبل.",
    ledeAccepted: "هذه المجموعة مجمّدة. يبدأ الفرز منها، لذا لا يتيح التطبيق تغييرها.",
    loading: "قراءة الاستيراد من المحرك…",
    addTitle: "أضف ملف قاعدة بيانات",
    file: "ملف RIS ‏(.ris أو .txt)",
    fileHelp: "صدّر نتائجك من قاعدة البيانات بصيغة RIS ثم اختر الملف. حتى {mb} ميغابايت.",
    label: "اسم قاعدة البيانات (مطلوب)",
    labelHelp: "قاعدة بيانات صُدّرت على أجزاء: أضف كل جزء تحت الاسم نفسه؛ تُجمع الأجزاء.",
    details: "تفاصيل البحث (اختياري)",
    searchedOn: "تاريخ البحث",
    searchedOnHelp: "اليوم الذي أجريت فيه البحث. يطلبه PRISMA.",
    query: "عبارة البحث",
    queryHelp: "الصق البحث كما أجريته بالضبط في هذه القاعدة.",
    add: "أضف هذا الملف",
    reading: "قراءة {file}…",
    added: "أُضيف {file} إلى {label}.",
    removed: "أُزيل {file}.",
    databases: "قواعد البيانات المضافة",
    empty: "لم تُضف أي قاعدة بيانات بعد.",
    colDatabase: "قاعدة البيانات",
    colFiles: "الملفات",
    colRecords: "السجلات",
    colSearched: "تاريخ البحث",
    colDetails: "تفاصيل البحث",
    stated: "مذكورة",
    notStated: "غير مذكورة",
    remove: "أزل {file}",
    removeShort: "إزالة",
    total: "مجموع السجلات المحددة",
    counts: "أعداد مخطط تدفق PRISMA",
    draft: "معاينة · غير مجمّدة",
    frozenBadge: "عُدّت عند التجميد",
    fromDb: "سجلات محددة من {label}",
    identified: "السجلات المحددة، المجموع",
    duplicates: "السجلات المكررة المزالة",
    studies: "دراسات للفرز",
    sentence: "سجلات محددة من: {sources}؛ سجلات مكررة مزالة (n = {duplicates}). دراسات للفرز: {studies}.",
    duplicatesHelp: "المكرر هو المقال نفسه موجودًا في أكثر من قاعدة بيانات، أو مرتين في ملف واحد. يطابقها التطبيق بالـ DOI، ثم بعنوان شبه مطابق والمؤلف الأول والسنة (بفارق سنة).",
    notStatedNote: "تفاصيل البحث غير مذكورة لـ: {labels}. أضفها في تفاصيل بحث كل ملف، أو صرّح بأنها غير مذكورة.",
    sideTitle: "ما يحدث عند القبول",
    sideFreeze: "تُجمَّد المجموعة نقطةَ بداية للفرز.",
    sideNoChange: "لا يمكن بعد ذلك إضافة قاعدة بيانات أو إزالتها أو استبدالها.",
    sideFiles: "تبقى نسخ ملفاتك في literature/raw/ris/، وتُسجَّل كل خطوة في سجل التدقيق.",
    accept: "اقبل المجموعة وجمّدها",
    confirmTitle: "أتجمّد هذه المجموعة؟",
    confirmBody: "أنت على وشك تجميد {studies} دراسة من {databases} قاعدة بيانات. بعد ذلك لا يمكنك إضافة قاعدة بيانات أو إزالتها أو استبدالها. تحقق من الأعداد أولًا.",
    confirm: "جمّد المجموعة",
    back: "رجوع",
    freezing: "تجميد المجموعة…",
    frozen: "المجموعة مجمّدة",
    frozenOn: "جُمّدت في {date}",
    fingerprint: "بصمة المجموعة",
    filesIn: "نسخ ملفاتك موجودة في literature/raw/ris/.",
    continue: "المتابعة إلى التحضير",
    phone: "يتم الاستيراد على حاسوبك. افتح هذه الشاشة هناك لإضافة ملفات قواعد البيانات.",
    phoneLink: "الذهاب إلى رئيسية الفرز",
    discovery: "جاءت مجموعة هذه المساحة من بحث التطبيق نفسه، لا من ملفات قواعد البيانات.",
  },
} as const satisfies Record<Locale, Record<string, string>>;

export type ImportCopyKey = keyof (typeof COPY)["en"];
export const IMPORT_COPY: Record<Locale, Record<ImportCopyKey, string>> = COPY;

/** Database names researchers use most; a hint, never a restriction. Product names, not translated. */
const SUGGESTIONS = ["Scopus", "Web of Science", "IEEE Xplore", "PubMed", "ACM Digital Library"];

function fill(template: string, values: Record<string, string | number> = {}): string {
  return template.replace(/\{(\w+)\}/g, (_, k: string) => {
    if (!(k in values)) throw new Error(`import copy needs {${k}}`);
    return String(values[k]);
  });
}

function consoleOrigin(): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get("console") ?? "";
}

type Load = { status: "loading" } | { status: "ready"; corpus: Corpus } | { status: "error"; code: string; message: string };
type Refusal = { code: string; message: string } | null;

function refusalOf(error: unknown): { code: string; message: string } {
  return isScreeningApiError(error) ? { code: error.code, message: error.serverMessage } : { code: "ENGINE_UNREACHABLE", message: "" };
}

export function ScreeningImport({ locale }: Readonly<{ locale: Locale }>) {
  const t = useCallback((key: ImportCopyKey, values?: Record<string, string | number>) => fill(IMPORT_COPY[locale][key], values), [locale]);
  const n = useCallback((value: number) => formatNumber(locale, value), [locale]);
  const origin = useMemo(consoleOrigin, []);
  const [load, setLoad] = useState<Load>({ status: "loading" });

  const reload = useCallback(async () => {
    setLoad({ status: "loading" });
    try {
      setLoad({ status: "ready", corpus: await getCorpus(origin) });
    } catch (error) {
      setLoad({ status: "error", ...refusalOf(error) });
    }
  }, [origin]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return (
    <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8 lg:py-14">
      <ScreeningSteps locale={locale} current="import" consoleOrigin={origin} />
      {load.status === "loading" ? (
        <p className="text-ink-muted" role="status">
          {t("loading")}
        </p>
      ) : load.status === "error" && load.code === "TOKEN_SCOPE_REFUSED" ? (
        <section className="rounded-lg border border-rule bg-leaf p-5" data-phone-pointer>
          <h1 className="font-display text-[1.75rem] leading-[2.25rem] text-ink">{t("title")}</h1>
          <p className="mt-2 text-ink">{t("phone")}</p>
          <a className="mt-3 inline-flex min-h-11 items-center text-brand underline" href={stepHref(locale, "home", origin)}>
            {t("phoneLink")}
          </a>
        </section>
      ) : load.status === "error" ? (
        <StateCard pageHeading locale={locale} code={load.code} message={load.message} consoleOrigin={origin} onRetry={() => void reload()} />
      ) : (
        <ImportReady
          locale={locale}
          origin={origin}
          corpus={load.corpus}
          onCorpus={(corpus) => setLoad({ status: "ready", corpus })}
          t={t}
          n={n}
        />
      )}
    </div>
  );
}

function ImportReady({
  locale,
  origin,
  corpus,
  onCorpus,
  t,
  n,
}: Readonly<{
  locale: Locale;
  origin: string;
  corpus: Corpus;
  onCorpus: (corpus: Corpus) => void;
  t: (key: ImportCopyKey, values?: Record<string, string | number>) => string;
  n: (value: number) => string;
}>) {
  const accepted = corpus.state === "ACCEPTED";
  const blockedByDiscovery = corpus.from_discovery && !accepted;
  const [refusal, setRefusal] = useState<Refusal>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [announce, setAnnounce] = useState("");
  const [confirming, setConfirming] = useState(false);
  const acceptRef = useRef<HTMLButtonElement>(null);
  const goBackRef = useRef<HTMLButtonElement>(null);
  const confirmRef = useRef<HTMLButtonElement>(null);
  const frozenRef = useRef<HTMLHeadingElement>(null);
  const justAccepted = useRef(false);

  useEffect(() => {
    if (accepted && justAccepted.current) {
      justAccepted.current = false;
      frozenRef.current?.focus();
    }
  }, [accepted]);

  useEffect(() => {
    if (confirming) goBackRef.current?.focus();
  }, [confirming]);

  const act = useCallback(
    async (status: string, run: () => Promise<Corpus>, done: string) => {
      setBusy(status);
      setRefusal(null);
      setAnnounce(status);
      try {
        onCorpus(await run());
        setAnnounce(done);
        return true;
      } catch (error) {
        setRefusal(refusalOf(error));
        setAnnounce("");
        return false;
      } finally {
        setBusy(null);
      }
    },
    [onCorpus],
  );

  const counts = accepted && corpus.accepted
    ? { identified: corpus.accepted.records, duplicates: corpus.accepted.duplicates, studies: corpus.accepted.studies }
    : { identified: corpus.preview.identified, duplicates: corpus.preview.duplicates, studies: corpus.preview.unique_studies };
  const missing = corpus.databases.filter((d) => d.search_details_missing).map((d) => d.label);
  const sentence = t("sentence", {
    sources: corpus.databases.map((d) => `${d.label} (n = ${n(d.records)})`).join("; "),
    duplicates: n(counts.duplicates),
    studies: n(counts.studies),
  });

  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.05em] text-brand rtl:tracking-normal">{t("eyebrow")}</p>
        <h1 className="font-display mt-1 text-[1.75rem] leading-[2.25rem] text-ink">{accepted ? t("titleAccepted") : t("title")}</h1>
        <p className="mt-1 text-ink-muted">{accepted ? t("ledeAccepted") : t("lede")}</p>
      </header>

      <p className="sr-only" role="status" aria-live="polite">
        {announce}
      </p>

      <section className="rounded-lg border border-rule bg-leaf p-5 sm:hidden" data-phone-pointer>
        <p className="text-ink">{t("phone")}</p>
        <a className="mt-3 inline-flex min-h-11 items-center text-brand underline" href={stepHref(locale, "home", origin)}>
          {t("phoneLink")}
        </a>
      </section>

      <div className="hidden flex-wrap gap-6 sm:flex">
        <div className="w-full min-w-0 flex-[2_1_480px] space-y-6">
          {blockedByDiscovery ? <StateCard locale={locale} code="VERIFIED_EXISTS" consoleOrigin={origin} /> : null}
          {refusal ? (
            <StateCard locale={locale} code={refusal.code} message={refusal.message} consoleOrigin={origin} onRetry={() => setRefusal(null)} />
          ) : null}
          {!accepted && !blockedByDiscovery ? (
            <AddForm
              refusal={refusal?.code ?? null}
              corpus={corpus}
              busy={busy !== null}
              primary={corpus.sources.length === 0}
              t={t}
              onTooLarge={() => setRefusal({ code: "SOURCE_TOO_LARGE", message: "" })}
              onAdd={async (file, label, searchedOn, query) => {
                const content_base64 = await fileToBase64(file);
                return act(
                  t("reading", { file: file.name }),
                  () => addCorpusSource(origin, { label, file_name: file.name, content_base64, searched_on: searchedOn || null, query: query || null }),
                  t("added", { file: file.name, label }),
                );
              }}
            />
          ) : null}

          <section aria-labelledby="import-databases" className="rounded-lg border border-rule bg-leaf p-5" data-import-databases>
            <h2 id="import-databases" className="font-semibold text-ink">
              {t("databases")}
            </h2>
            {corpus.databases.length === 0 ? (
              <p className="mt-2 text-sm text-ink-muted">{t("empty")}</p>
            ) : (
              <table className="mt-3 w-full text-sm">
                <caption className="sr-only">{t("databases")}</caption>
                <thead>
                  <tr className="text-ink-muted">
                    <th scope="col" className="py-1 text-start">{t("colDatabase")}</th>
                    <th scope="col" className="py-1 text-start">{t("colFiles")}</th>
                    <th scope="col" className="py-1 pe-6 text-end">{t("colRecords")}</th>
                    <th scope="col" className="whitespace-nowrap py-1 pe-4 text-start">{t("colSearched")}</th>
                    <th scope="col" className="py-1 text-start">{t("colDetails")}</th>
                  </tr>
                </thead>
                <tbody>
                  {corpus.databases.map((db) => (
                    <DatabaseRow
                      key={db.label}
                      db={db}
                      corpus={corpus}
                      removable={!accepted}
                      busy={busy !== null}
                      t={t}
                      n={n}
                      onRemove={(id, file) => void act(t("removed", { file }), () => removeCorpusSource(origin, id), t("removed", { file }))}
                    />
                  ))}
                </tbody>
                <tfoot>
                  <tr className="border-t border-rule-strong font-medium">
                    <th scope="row" colSpan={2} className="py-2 text-start">
                      {t("total")}
                    </th>
                    <td className="py-2 pe-6 text-end tabular-nums">{n(counts.identified)}</td>
                    <td colSpan={2} />
                  </tr>
                </tfoot>
              </table>
            )}
          </section>

          {corpus.databases.length > 0 ? (
            <section
              aria-labelledby="import-counts"
              className={`rounded-lg p-5 ${accepted ? "border border-rule bg-leaf" : "border border-dashed border-brand bg-brand-soft"}`}
              data-import-counts
            >
              <div className="flex flex-wrap items-center gap-2">
                <h2 id="import-counts" className="font-semibold text-ink">
                  {t("counts")}
                </h2>
                <DecisionBadge role={accepted ? "include" : "unclear"}>{accepted ? t("frozenBadge") : t("draft")}</DecisionBadge>
              </div>
              <table className="mt-3 w-full text-sm">
                <tbody>
                  {corpus.databases.map((db) => (
                    <tr key={db.label}>
                      <th scope="row" className="py-1 text-start font-normal">
                        {t("fromDb", { label: db.label })}
                      </th>
                      <td className="py-1 text-end">{n(db.records)}</td>
                    </tr>
                  ))}
                  <tr className="border-t border-rule">
                    <th scope="row" className="py-1 text-start font-normal">{t("identified")}</th>
                    <td className="py-1 text-end" data-count="identified">{n(counts.identified)}</td>
                  </tr>
                  <tr>
                    <th scope="row" className="py-1 text-start font-normal">{t("duplicates")}</th>
                    <td className="py-1 text-end" data-count="duplicates">{n(counts.duplicates)}</td>
                  </tr>
                  <tr>
                    <th scope="row" className="py-1 text-start font-semibold">{t("studies")}</th>
                    <td className="py-1 text-end font-semibold" data-count="studies">{n(counts.studies)}</td>
                  </tr>
                </tbody>
              </table>
              <p className="mt-3 text-sm text-ink" data-prisma-sentence>
                {sentence}
              </p>
              <p className="mt-2 text-xs text-ink-muted">{t("duplicatesHelp")}</p>
              {missing.length > 0 ? (
                <p className="mt-2 text-sm text-unclear" data-not-stated>
                  {t("notStatedNote", { labels: missing.join(", ") })}
                </p>
              ) : null}
            </section>
          ) : null}
        </div>

        <aside className="w-full flex-[1_1_280px] space-y-6">
          {accepted && corpus.accepted ? (
            <section aria-labelledby="import-frozen" className="rounded-lg border border-rule bg-leaf p-5" data-import-frozen>
              <DecisionBadge role="include">{t("frozen")}</DecisionBadge>
              <h2 id="import-frozen" ref={frozenRef} className="mt-2 font-semibold text-ink" tabIndex={-1}>
                {t("frozen")}
              </h2>
              {corpus.accepted.accepted_at ? (
                <p className="mt-1 text-sm text-ink-muted">{t("frozenOn", { date: corpus.accepted.accepted_at.slice(0, 10) })}</p>
              ) : null}
              <p className="mt-2 text-xs text-ink-muted">{t("fingerprint")}</p>
              <DataCell>
                <bdi dir="ltr">{corpus.accepted.artifact_id}</bdi>
              </DataCell>
              <p className="mt-3 text-sm text-ink-muted">{t("filesIn")}</p>
              <a className="mt-4 inline-flex min-h-11 items-center rounded-md bg-brand px-4 font-medium text-on-brand" href={stepHref(locale, "prepare", origin)}>
                {t("continue")}
              </a>
            </section>
          ) : !blockedByDiscovery ? (
            <section aria-labelledby="import-side" className="rounded-lg border border-rule bg-leaf p-5">
              <h2 id="import-side" className="font-semibold text-ink">
                {t("sideTitle")}
              </h2>
              <ul className="mt-2 list-disc space-y-1 ps-5 text-sm text-ink-muted">
                <li>{t("sideFreeze")}</li>
                <li>{t("sideNoChange")}</li>
                <li>{t("sideFiles")}</li>
              </ul>
              {confirming ? (
                <div
                  role="alertdialog"
                  aria-labelledby="import-confirm"
                  aria-describedby="import-confirm-body"
                  className="mt-4 rounded-md border border-brand p-4"
                  aria-modal="true"
                  onKeyDown={(e) => {
                    if (e.key === "Escape") {
                      setConfirming(false);
                      acceptRef.current?.focus();
                    } else if (e.key === "Tab") {
                      // Two controls: Tab and Shift+Tab move between them and never leave.
                      e.preventDefault();
                      (document.activeElement === goBackRef.current ? confirmRef : goBackRef).current?.focus();
                    }
                  }}
                >
                  <p id="import-confirm" className="font-semibold text-ink">
                    {t("confirmTitle")}
                  </p>
                  <p id="import-confirm-body" className="mt-1 text-sm text-ink">
                    {t("confirmBody", { studies: n(counts.studies), databases: n(corpus.databases.length) })}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Button
                      ref={goBackRef}
                      onClick={() => {
                        setConfirming(false);
                        acceptRef.current?.focus();
                      }}
                    >
                      {t("back")}
                    </Button>
                    <Button
                      ref={confirmRef}
                      variant="primary"
                      disabled={busy !== null}
                      onClick={() => {
                        setConfirming(false);
                        justAccepted.current = true;
                        void act(t("freezing"), () => acceptCorpus(origin), t("frozen"));
                      }}
                    >
                      {t("confirm")}
                    </Button>
                  </div>
                </div>
              ) : (
                <Button
                  ref={acceptRef}
                  variant={corpus.sources.length > 0 ? "primary" : "secondary"}
                  className="mt-4"
                  disabled={busy !== null || corpus.sources.length === 0}
                  onClick={() => setConfirming(true)}
                >
                  {busy === t("freezing") ? t("freezing") : t("accept")}
                </Button>
              )}
            </section>
          ) : null}
        </aside>
      </div>
    </div>
  );
}

function DatabaseRow({
  db,
  corpus,
  removable,
  busy,
  t,
  n,
  onRemove,
}: Readonly<{
  db: CorpusDatabase;
  corpus: Corpus;
  removable: boolean;
  busy: boolean;
  t: (key: ImportCopyKey, values?: Record<string, string | number>) => string;
  n: (value: number) => string;
  onRemove: (id: string, file: string) => void;
}>) {
  const files = corpus.sources.filter((s) => s.label === db.label);
  return (
    <tr className="border-t border-rule align-top" data-database={db.label}>
      <th scope="row" className="py-2 text-start font-medium">
        <bdi>{db.label}</bdi>
      </th>
      <td className="py-2">
        <ul className="space-y-1">
          {files.map((file) => (
            <li key={file.id} className="flex flex-wrap items-center gap-x-3">
              <DataCell>
                <bdi dir="ltr">{file.file_name}</bdi>
              </DataCell>
              <span className="text-ink-muted tabular-nums">{n(file.records)}</span>
              {removable ? (
                <Button
                  variant="quiet"
                  className="px-0 text-sm"
                  aria-label={t("remove", { file: file.file_name })}
                  disabled={busy}
                  onClick={() => onRemove(file.id, file.file_name)}
                >
                  {t("removeShort")}
                </Button>
              ) : null}
            </li>
          ))}
        </ul>
      </td>
      <td className="py-2 pe-6 text-end tabular-nums">{n(db.records)}</td>
      <td className="whitespace-nowrap py-2 pe-4">{db.searched_on.length ? <bdi dir="ltr">{db.searched_on.join(", ")}</bdi> : <span className="text-unclear">{t("notStated")}</span>}</td>
      <td className="py-2">
        {db.search_details_missing ? (
          <DecisionBadge role="unclear">{t("notStated")}</DecisionBadge>
        ) : (
          <DecisionBadge role="include">{t("stated")}</DecisionBadge>
        )}
      </td>
    </tr>
  );
}

function AddForm({
  refusal,
  corpus,
  busy,
  primary,
  t,
  onTooLarge,
  onAdd,
}: Readonly<{
  refusal: string | null;
  corpus: Corpus;
  busy: boolean;
  primary: boolean;
  t: (key: ImportCopyKey, values?: Record<string, string | number>) => string;
  onTooLarge: () => void;
  onAdd: (file: File, label: string, searchedOn: string, query: string) => Promise<boolean>;
}>) {
  const [file, setFile] = useState<File | null>(null);
  const [label, setLabel] = useState("");
  const [searchedOn, setSearchedOn] = useState("");
  const [query, setQuery] = useState("");
  const [fileKey, setFileKey] = useState(0);
  const limitMb = Math.round(corpus.limits.max_source_bytes / (1024 * 1024));
  const known = Array.from(new Set([...corpus.databases.map((d) => d.label), ...SUGGESTIONS]));

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file || !label.trim()) return;
    if (file.size > corpus.limits.max_source_bytes) {
      onTooLarge();
      return;
    }
    if (await onAdd(file, label.trim(), searchedOn, query)) {
      setFile(null);
      setFileKey((k) => k + 1);
      setSearchedOn("");
      setQuery("");
    }
  }

  return (
    <form onSubmit={(e) => void submit(e)} className="rounded-lg border border-rule bg-leaf p-5" data-import-form>
      <fieldset disabled={busy} className="space-y-4">
        <legend className="font-semibold text-ink">{t("addTitle")}</legend>
        <label className="block text-sm text-ink">
          {t("file")}
          <input
            key={fileKey}
            type="file"
            accept=".ris,.txt"
            aria-describedby="import-file-help"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
            className="mt-1 block w-full text-sm text-ink file:me-3 file:min-h-11 file:rounded-md file:border file:border-rule-strong file:bg-leaf file:px-4 file:text-ink"
          />
        </label>
        <p id="import-file-help" className="text-xs text-ink-muted">
          {t("fileHelp", { mb: limitMb })}
        </p>
        <label className="block text-sm text-ink">
          {t("label")}
          <input
            type="text"
            dir="auto"
            required
            list="import-database-names"
            maxLength={corpus.limits.label_max_length}
            value={label}
            aria-invalid={refusal === "SOURCE_LABEL_INVALID" ? true : undefined}
            aria-describedby="import-label-help"
            onChange={(e) => setLabel(e.target.value)}
            className="mt-1 block w-full rounded-md border border-rule bg-paper p-2 text-ink"
          />
          <datalist id="import-database-names">
            {known.map((name) => (
              <option key={name} value={name} />
            ))}
          </datalist>
        </label>
        <p id="import-label-help" className="text-xs text-ink-muted">
          {t("labelHelp")}
        </p>
        <details className="rounded-md border border-rule p-3" data-search-details open={refusal === "SOURCE_DATE_INVALID" ? true : undefined}>
          <summary className="cursor-pointer text-sm font-medium text-ink">{t("details")}</summary>
          <div className="mt-3 space-y-3">
            <label className="block text-sm text-ink">
              {t("searchedOn")}
              <input
                type="date"
                value={searchedOn}
                aria-invalid={refusal === "SOURCE_DATE_INVALID" ? true : undefined}
                aria-describedby="import-date-help"
                onChange={(e) => setSearchedOn(e.target.value)}
                className="mt-1 block rounded-md border border-rule bg-paper p-2 text-ink"
              />
            </label>
            <p id="import-date-help" className="text-xs text-ink-muted">
              {t("searchedOnHelp")}
            </p>
            <label className="block text-sm text-ink">
              {t("query")}
              <textarea
                dir="ltr"
                rows={3}
                value={query}
                aria-describedby="import-query-help"
                onChange={(e) => setQuery(e.target.value)}
                className="mt-1 block w-full rounded-md border border-rule bg-paper p-2 font-mono text-[0.8125rem] text-ink"
              />
            </label>
            <p id="import-query-help" className="text-xs text-ink-muted">
              {t("queryHelp")}
            </p>
          </div>
        </details>
        <Button type="submit" variant={primary ? "primary" : "secondary"} disabled={busy || !file || !label.trim()}>
          {t("add")}
        </Button>
      </fieldset>
    </form>
  );
}
