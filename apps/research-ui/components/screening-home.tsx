"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { formatNumber, type Locale } from "@/i18n";
import { DataCell, DecisionBadge } from "@/components/ui/base";
import { DETAILS_LABEL, ScreeningSteps, StateCard, exportHref, stepHref } from "@/components/screening-state-card";
import { getPublicationStatus, getScreeningBatches, isScreeningApiError, type ScreeningBatches } from "@/lib/screening-api";
import { getConflicts, getCorpus, getSettings, getSummary, type Conflict, type Corpus, type Settings, type Summary } from "@/lib/screening-v1";

/**
 * Screening home (spec 01): how far screening is, what needs you, who screens,
 * and the batches. Counts come from the engine (`/summary`, `/ui/batches`);
 * nothing here reveals the agent's call for an undecided record: "agent
 * proposed" counts only that a draft exists. Phone access is M2 and shown as
 * parked.
 */

const COPY = {
  en: {
    eyebrow: "Screening",
    title: "{decided} of {total} records are decided; {needs} still need you.",
    titleDone: "All {total} records are decided.",
    titleEmpty: "Nothing to screen yet: prepare the batches first.",
    lede: "The agent drafts, you decide. Drafts stay hidden until you have decided each record.",
    ledeShown: "The agent drafts, you decide. Drafts are shown beside each record, before you decide.",
    live: "Live data from this workspace's screening engine",
    exportLink: "Export and methods",
    openTriage: "Open triage · {n} need you",
    seeChange: "See the change",
    loading: "Counts appear only once every file is read; no partial number is shown as final.",
    progress: "Progress",
    decided: "Decided by you",
    needsYou: "Still need you",
    agentProposed: "Records with an agent draft",
    agentProposedNote: "A draft exists; on an undecided record its call stays hidden until you decide.",
    conflicts: "Conflicts to resolve",
    included: "Included",
    excluded: "Excluded",
    unclear: "Unclear → full text",
    batches: "Batches",
    batch: "Batch",
    records: "Records",
    batchDecided: "Decided",
    coverage: "Coverage",
    complete: "Complete",
    incomplete: "Incomplete",
    stale: "Protocol changed",
    who: "Who screens",
    agent: "The agent",
    agentBody: "Writes a draft per record: a checklist with quotes. Not a decision. {n} drafts so far.",
    you: "You",
    youBody: "Decide every record. {n} decided so far.",
    second: "Second screener",
    secondBody: "Team feature, not production yet.",
    phone: "Phone",
    phoneBody: "The phone can triage; it approves on your desktop. Phone access comes with the next milestone.",
    terminal: "Run from the terminal",
    terminalBody: "The same steps are available without the UI:",
    settings: "Drafts: {blinding} · Mode: {mode}",
    blindingHidden: "hidden until you decide",
    blindingShow: "shown beside records",
    modeEvery: "you see every record",
    modeAi: "AI-agreed exclusion (opt-in)",
    progressLabel: "{decided} of {total} records decided",
    includedSoFar: "Included so far",
    publishedStale: "Published, {n} studies changed since.",
    publishAgain: "Publish again",
    batchN: "Batch {n}",
    importCta: "Import your search results",
    imported: "{records} records from {databases}, {duplicates} duplicates removed.",
    importedLink: "What was imported",
  },
  fr: {
    eyebrow: "Sélection",
    title: "{decided} notices sur {total} sont décidées ; {needs} vous attendent encore.",
    titleDone: "Les {total} notices sont toutes décidées.",
    titleEmpty: "Rien à examiner pour l'instant : préparez d'abord les lots.",
    lede: "L'agent rédige, vous décidez. Les brouillons restent masqués jusqu'à votre décision sur chaque notice.",
    ledeShown: "L'agent rédige, vous décidez. Les brouillons sont affichés à côté de chaque notice, avant votre décision.",
    live: "Données en direct du moteur de sélection de cet espace",
    exportLink: "Export et méthodes",
    openTriage: "Ouvrir le tri · {n} à traiter",
    seeChange: "Voir la modification",
    loading: "Les totaux n'apparaissent qu'une fois tous les fichiers lus ; aucun chiffre partiel n'est présenté comme définitif.",
    progress: "Avancement",
    decided: "Décidées par vous",
    needsYou: "Vous attendent encore",
    agentProposed: "Notices avec un brouillon de l'agent",
    agentProposedNote: "Un brouillon existe ; sur une notice non décidée, son avis reste masqué jusqu'à votre décision.",
    conflicts: "Conflits à résoudre",
    included: "Incluses",
    excluded: "Exclues",
    unclear: "Incertain → texte intégral",
    batches: "Lots",
    batch: "Lot",
    records: "Notices",
    batchDecided: "Décidées",
    coverage: "Couverture",
    complete: "Complète",
    incomplete: "Incomplète",
    stale: "Protocole modifié",
    who: "Qui sélectionne",
    agent: "L'agent",
    agentBody: "Rédige un brouillon par notice : une grille avec citations. Pas une décision. {n} brouillons à ce jour.",
    you: "Vous",
    youBody: "Décidez chaque notice. {n} décidées à ce jour.",
    second: "Second évaluateur",
    secondBody: "Fonction d'équipe, pas encore en production.",
    phone: "Téléphone",
    phoneBody: "Le téléphone peut trier ; il approuve sur votre ordinateur. L'accès par téléphone arrive au prochain jalon.",
    terminal: "Depuis le terminal",
    terminalBody: "Les mêmes étapes sont disponibles sans l'interface :",
    settings: "Brouillons : {blinding} · Mode : {mode}",
    blindingHidden: "masqués jusqu'à votre décision",
    blindingShow: "affichés à côté des notices",
    modeEvery: "vous voyez chaque notice",
    modeAi: "exclusion validée par l'IA (option)",
    progressLabel: "{decided} notices décidées sur {total}",
    includedSoFar: "Incluses à ce jour",
    publishedStale: "Publiée, {n} études modifiées depuis.",
    publishAgain: "Publier de nouveau",
    batchN: "Lot {n}",
    importCta: "Importer vos résultats de recherche",
    imported: "{records} notices issues de {databases}, {duplicates} doublons retirés.",
    importedLink: "Ce qui a été importé",
  },
  ar: {
    eyebrow: "الفرز",
    title: "حُسم {decided} من {total} سجلًا؛ وما زال {needs} بانتظارك.",
    titleDone: "حُسمت السجلات الـ{total} كلها.",
    titleEmpty: "لا شيء للفرز بعد: حضّر الدفعات أولًا.",
    lede: "الوكيل يكتب المسودات وأنت تقرر. تبقى المسودات مخفية حتى تحسم كل سجل.",
    ledeShown: "الوكيل يكتب المسودات وأنت تقرر. تُعرض المسودات بجانب كل سجل قبل أن تقرر.",
    live: "بيانات حية من محرك الفرز لهذه المساحة",
    exportLink: "التصدير والمنهجية",
    openTriage: "فتح المراجعة · {n} بانتظارك",
    seeChange: "عرض التغيير",
    loading: "لا تظهر الأعداد إلا بعد قراءة كل الملفات؛ ولا يُعرض رقم جزئي على أنه نهائي.",
    progress: "التقدم",
    decided: "حسمتها أنت",
    needsYou: "ما زالت بانتظارك",
    agentProposed: "سجلات لها مسودة من الوكيل",
    agentProposedNote: "توجد مسودة، ويبقى رأيها في السجل غير المحسوم مخفيًا حتى تقرر.",
    conflicts: "تعارضات للحسم",
    included: "مُدرجة",
    excluded: "مستبعدة",
    unclear: "غير واضح ← النص الكامل",
    batches: "الدفعات",
    batch: "الدفعة",
    records: "السجلات",
    batchDecided: "المحسومة",
    coverage: "التغطية",
    complete: "كاملة",
    incomplete: "ناقصة",
    stale: "تغيّر البروتوكول",
    who: "من يفرز",
    agent: "الوكيل",
    agentBody: "يكتب مسودة لكل سجل: قائمة تحقق مع اقتباسات. ليست قرارًا. {n} مسودة حتى الآن.",
    you: "أنت",
    youBody: "تحسم كل سجل. {n} محسوم حتى الآن.",
    second: "مراجع ثانٍ",
    secondBody: "ميزة فرق، ليست جاهزة للإنتاج بعد.",
    phone: "الهاتف",
    phoneBody: "يستطيع الهاتف المراجعة، ويتم الاعتماد على حاسوبك. يأتي الوصول من الهاتف في المرحلة التالية.",
    terminal: "التشغيل من الطرفية",
    terminalBody: "الخطوات نفسها متاحة دون الواجهة:",
    settings: "المسودات: {blinding} · الوضع: {mode}",
    blindingHidden: "مخفية حتى تقرر",
    blindingShow: "معروضة بجانب السجلات",
    modeEvery: "ترى كل سجل",
    modeAi: "استبعاد يوافق عليه الذكاء الاصطناعي (اختياري)",
    progressLabel: "حُسم {decided} من {total} سجلًا",
    includedSoFar: "المُدرجة حتى الآن",
    publishedStale: "منشور، وتغيّرت {n} دراسة منذ ذلك.",
    publishAgain: "انشر مجددًا",
    batchN: "الدفعة {n}",
    importCta: "استورد نتائج بحثك",
    imported: "{records} سجلًا من {databases}، وأُزيل {duplicates} مكررًا.",
    importedLink: "ما استُورد",
  },
} as const satisfies Record<Locale, Record<string, string>>;

export type HomeCopyKey = keyof (typeof COPY)["en"];
export const HOME_COPY: Record<Locale, Record<HomeCopyKey, string>> = COPY;

function fill(template: string, values: Record<string, string | number> = {}): string {
  return template.replace(/\{(\w+)\}/g, (_, k: string) => {
    if (!(k in values)) throw new Error(`home copy needs {${k}}`);
    return String(values[k]);
  });
}

function consoleOrigin(): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get("console") ?? "";
}

type Publication = { status: string; changed: number | null } | null;
type Loaded = { summary: Summary; batches: ScreeningBatches; conflicts: Conflict[]; settings: Settings; publication: Publication; corpus: Corpus | null };

export function ScreeningHome({ locale }: Readonly<{ locale: Locale }>) {
  const t = useCallback((key: HomeCopyKey, values?: Record<string, string | number>) => fill(HOME_COPY[locale][key], values), [locale]);
  const n = useCallback((value: number) => formatNumber(locale, value), [locale]);
  const origin = useMemo(consoleOrigin, []);
  const [state, setState] = useState<{ status: "loading" } | { status: "ready"; data: Loaded } | { status: "error"; code: string; message: string }>({ status: "loading" });

  const load = useCallback(async () => {
    setState({ status: "loading" });
    try {
      const [summary, batches, conflicts, settings, publication, corpus] = await Promise.all([
        getSummary(origin),
        getScreeningBatches(origin),
        getConflicts(origin),
        getSettings(origin),
        // The export link shows only while the publication is CURRENT (spec 10, decision 3);
        // a failed read of the status hides the link and nothing else.
        // Published means current (M6-beta): STALE after a later decision, with the changed count.
        getPublicationStatus(origin).then(
          (s): Publication => ({ status: s.status, changed: typeof s.details?.changed === "number" ? (s.details.changed as number) : null }),
          (): Publication => null,
        ),
        // The import (spec 11): an entry until the corpus is accepted, then one
        // line of what was brought in. A failed read hides both and nothing else.
        getCorpus(origin).then((c): Corpus | null => c, () => null),
      ]);
      setState({ status: "ready", data: { summary, batches, conflicts, settings, publication, corpus } });
    } catch (error) {
      setState({
        status: "error",
        code: isScreeningApiError(error) ? error.code : "ENGINE_UNREACHABLE",
        message: isScreeningApiError(error) ? error.serverMessage : "",
      });
    }
  }, [origin]);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8 lg:py-14">
      <ScreeningSteps locale={locale} current="home" consoleOrigin={origin} />
      {state.status === "loading" ? (
        <p className="text-ink-muted" role="status">
          {t("loading")}
        </p>
      ) : state.status === "error" ? (
        <StateCard
          pageHeading
          locale={locale}
          code={state.code}
          message={state.message}
          consoleOrigin={origin}
          onRetry={() => void load()}
        />
      ) : (
        <HomeReady locale={locale} data={state.data} origin={origin} t={t} n={n} />
      )}
    </div>
  );
}

function HomeReady({
  locale,
  data,
  origin,
  t,
  n,
}: Readonly<{
  locale: Locale;
  data: Loaded;
  origin: string;
  t: (key: HomeCopyKey, values?: Record<string, string | number>) => string;
  n: (value: number) => string;
}>) {
  const { summary, batches, conflicts, settings, publication, corpus } = data;
  const published = publication?.status === "CURRENT";
  const publishedStale = publication?.status === "STALE" && publication.changed !== null;
  const importOpen = corpus !== null && corpus.state !== "ACCEPTED" && !corpus.from_discovery;
  const imported = corpus?.state === "ACCEPTED" && corpus.accepted && corpus.databases.length > 0 ? corpus : null;
  const stale = batches.batches.some((b) => b.binding?.state === "STALE_BINDING");
  const percent = summary.total > 0 ? Math.round((summary.decided / summary.total) * 100) : 0;
  const triage = stepHref(locale, "triage", origin);

  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.05em] text-brand rtl:tracking-normal">{t("eyebrow")}</p>
        <h1 className="font-display mt-1 text-[1.75rem] leading-[2.25rem] text-ink">
          {summary.total === 0
            ? t("titleEmpty")
            : summary.needs_you === 0
            ? t("titleDone", { total: n(summary.total) })
            : t("title", { decided: n(summary.decided), total: n(summary.total), needs: n(summary.needs_you) })}
        </h1>
        <p className="mt-1 text-ink-muted">{settings.blinding === "show" ? t("ledeShown") : t("lede")}</p>
        <p className="mt-2 inline-block border border-rule-strong px-2 py-0.5 text-xs text-ink-muted">{t("live")}</p>
        <p className="mt-4">
          {importOpen ? (
            <a className="inline-flex min-h-11 items-center rounded-md bg-brand px-4 font-medium text-on-brand" href={stepHref(locale, "import", origin)} data-import-entry>
              {t("importCta")}
            </a>
          ) : stale ? (
            <a className="inline-flex min-h-11 items-center rounded-md bg-brand px-4 font-medium text-on-brand" href={stepHref(locale, "prepare", origin)}>
              {t("seeChange")}
            </a>
          ) : batches.count === 0 ? null : (
            <a className="inline-flex min-h-11 items-center rounded-md bg-brand px-4 font-medium text-on-brand" href={triage}>
              {t("openTriage", { n: n(summary.needs_you) })}
            </a>
          )}
        </p>
        {imported?.accepted ? (
          <p className="mt-2 text-sm text-ink" data-imported-line>
            {t("imported", {
              records: n(imported.accepted.records),
              databases: new Intl.ListFormat(locale, { type: "conjunction" }).format(imported.databases.map((d) => d.label)),
              duplicates: n(imported.accepted.duplicates),
            })}{" "}
            <a className="text-brand underline" href={stepHref(locale, "import", origin)}>
              {t("importedLink")}
            </a>
          </p>
        ) : null}
        {published ? (
          <p className="mt-2">
            <a className="inline-flex min-h-11 items-center text-brand underline" href={exportHref(locale, origin)} data-export-link>
              {t("exportLink")}
            </a>
          </p>
        ) : publishedStale ? (
          <p className="mt-2 text-sm text-ink" data-publication-stale>
            {t("publishedStale", { n: n(publication!.changed!) })}{" "}
            <a className="inline-flex min-h-11 items-center text-brand underline" href={stepHref(locale, "publish", origin)}>
              {t("publishAgain")}
            </a>
          </p>
        ) : null}
      </header>

      {stale ? <StateCard locale={locale} code="STALE_BINDING" consoleOrigin={origin} /> : null}
      {batches.count === 0 && !importOpen ? <StateCard locale={locale} code="NOT_PREPARED" consoleOrigin={origin} /> : null}
      {conflicts.length > 0 ? <StateCard locale={locale} code="conflict" consoleOrigin={origin} /> : null}

      <section aria-labelledby="home-progress" className="rounded-lg border border-rule bg-leaf p-5">
        <h2 id="home-progress" className="font-semibold text-ink">
          {t("progress")}
        </h2>
        <div role="img" aria-label={t("progressLabel", { decided: n(summary.decided), total: n(summary.total) })} className="mt-3 h-2 w-full rounded-sm bg-rule">
          <div className="h-2 rounded-sm bg-brand" style={{ width: `${percent}%` }} />
        </div>
        <dl className="mt-4 grid grid-cols-3 gap-4" data-home-tiles>
          <Tile label={t("needsYou")} value={n(summary.needs_you)} />
          <Tile label={t("decided")} value={n(summary.decided)} />
          <Tile label={t("includedSoFar")} value={n(summary.by_outcome.INCLUDE)} />
        </dl>
        <details className="mt-3 text-sm" data-home-details>
          <summary className="inline-flex min-h-11 cursor-pointer items-center rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-ink-muted">{DETAILS_LABEL[locale]}</summary>
          <dl className="mt-2 grid grid-cols-2 gap-4">
            <Tile label={t("agentProposed")} value={n(summary.agent_proposed)} note={t("agentProposedNote")} />
            <Tile label={t("conflicts")} value={n(summary.conflicts)} />
          </dl>
        </details>
        <p className="mt-4 flex flex-wrap gap-2 text-sm">
          <DecisionBadge role="include">
            {t("included")} {n(summary.by_outcome.INCLUDE)}
          </DecisionBadge>
          <DecisionBadge role="exclude">
            {t("excluded")} {n(summary.by_outcome.EXCLUDE)}
          </DecisionBadge>
          <DecisionBadge role="unclear">
            {t("unclear")} {n(summary.by_outcome.MAYBE)}
          </DecisionBadge>
        </p>
      </section>

      {batches.count > 0 ? (
        <section aria-labelledby="home-batches" className="rounded-lg border border-rule bg-leaf p-5">
          <h2 id="home-batches" className="font-semibold text-ink">
            {t("batches")}
          </h2>
          <table className="mt-3 w-full text-sm">
            <thead>
              <tr className="text-ink-muted">
                <th scope="col" className="py-1 text-start">{t("batch")}</th>
                <th scope="col" className="py-1 text-start">{t("records")}</th>
                <th scope="col" className="py-1 text-start">{t("batchDecided")}</th>
                <th scope="col" className="py-1 text-start">{t("coverage")}</th>
              </tr>
            </thead>
            <tbody>
              {batches.batches.map((b) => (
                <tr key={b.batch_index} className="border-t border-rule">
                  <th scope="row" className="py-2 text-start font-normal">
                    {t("batchN", { n: n(b.batch_index) })}
                    <details className="text-xs text-ink-muted">
                      <summary className="inline-flex min-h-11 cursor-pointer items-center rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">{DETAILS_LABEL[locale]}</summary>
                      <DataCell>{b.batch_file}</DataCell>
                    </details>
                  </th>
                  <td className="py-2">{n(b.items)}</td>
                  <td className="py-2">{n(b.decisions_count ?? 0)}</td>
                  <td className="py-2">
                    {b.binding?.state === "STALE_BINDING" ? (
                      <DecisionBadge role="blocked">{t("stale")}</DecisionBadge>
                    ) : b.coverage === "COMPLETE" ? (
                      <DecisionBadge role="include">{t("complete")}</DecisionBadge>
                    ) : (
                      <DecisionBadge role="unclear">{t("incomplete")}</DecisionBadge>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      ) : null}

      <section aria-labelledby="home-who" className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <h2 id="home-who" className="sr-only">
          {t("who")}
        </h2>
        <Card title={t("agent")} body={t("agentBody", { n: n(summary.lanes.agent) })} dashed />
        <Card title={t("you")} body={t("youBody", { n: n(summary.lanes.you) })} />
        <Card title={t("second")} body={t("secondBody")} parked />
        <Card title={t("phone")} body={t("phoneBody")} parked />
      </section>

      <p className="text-sm text-ink-muted" data-home-settings>
        {t("settings", {
          blinding: settings.blinding === "show" ? t("blindingShow") : t("blindingHidden"),
          mode: settings.mode === "ai_agreed_exclusion" ? t("modeAi") : t("modeEvery"),
        })}
      </p>

      <details className="rounded-lg border border-rule bg-leaf p-5 text-sm">
        <summary className="inline-flex min-h-11 cursor-pointer items-center rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus font-semibold text-ink">{t("terminal")}</summary>
        <p className="mt-2 text-ink-muted">{t("terminalBody")}</p>
        <pre className="mt-2 overflow-x-auto rounded-md bg-paper p-3 font-mono text-[0.8125rem] text-ink" dir="ltr">
          {"uv run python src/scholar_harness/agent_screen.py prepare <workspace>\nuv run python src/scholar_harness/agent_screen.py collect <workspace>"}
        </pre>
      </details>
    </div>
  );
}

function Tile({ label, value, note }: Readonly<{ label: string; value: string; note?: string }>) {
  return (
    <div>
      <dt className="text-xs text-ink-muted">{label}</dt>
      <dd className="mt-1 text-[1.5rem] leading-8 text-ink">{value}</dd>
      {note ? <dd className="text-xs text-ink-faint">{note}</dd> : null}
    </div>
  );
}

function Card({ title, body, dashed, parked }: Readonly<{ title: string; body: string; dashed?: boolean; parked?: boolean }>) {
  return (
    <div
      aria-disabled={parked ? "true" : undefined}
      className={`rounded-lg p-4 ${dashed ? "border border-dashed border-rule-strong" : "border border-rule"} ${parked ? "opacity-70" : ""} bg-leaf`}
    >
      <h3 className="font-semibold text-ink">{title}</h3>
      <p className="mt-1 text-sm text-ink-muted">{body}</p>
    </div>
  );
}
