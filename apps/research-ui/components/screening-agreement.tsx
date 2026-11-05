"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { formatNumber, type Locale } from "@/i18n";
import { DataCell, DecisionBadge } from "@/components/ui/base";
import { ScreeningSteps, StateCard, stepHref } from "@/components/screening-state-card";
import { isScreeningApiError } from "@/lib/screening-api";
import { getAgreement, getSettings, getSummary, type Agreement, type Settings, type Summary } from "@/lib/screening-v1";

/**
 * Agreement with the agent (spec 07). Descriptive only: the agent is not a
 * second reviewer, so kappa stays empty (`kappa: null`) until a second human
 * screener exists. Every number is the engine's (`GET /agreement`), which
 * counts only decisions made before the draft was revealed and only records you
 * have decided, so nothing here shows the agent's call on an undecided record.
 */

const COPY = {
  en: {
    eyebrow: "Screening · agreement",
    title: "You and the agent agreed on {pct} of records; it would have dropped {missed} of your includes.",
    titleNoPairs: "Agreement with the agent",
    lede: "Not an inter-rater statistic: the agent is not a second reviewer.",
    loading: "Reading the agreement…",
    emptyDecided: "Decide some records first.",
    emptyProposals: "No agent proposals to compare.",
    toProposals: "Run agent proposals",
    soFar: "of {n} decided so far",
    agreement: "Agreement with the agent",
    missed: "Your includes it proposed to exclude",
    missedNote: "the number that matters most",
    extra: "Its includes you excluded",
    unclear: "Unclear on either side",
    matrix: "You and the agent",
    you: "You",
    agent: "Agent",
    include: "Include",
    exclude: "Exclude",
    byCriterion: "Where you and the agent split, by criterion",
    noSplits: "No criterion splits.",
    afterSeeing: "{n} records were decided with the draft already in view and are not counted.",
    kappa: "Cohen's kappa",
    kappaDisabled: "needs a second human screener · not production",
    sample: "Sample check of agreed exclusions",
    sampleNotNeeded: "You saw every record. No sample needed.",
    sampleOptIn: "AI-agreed exclusion is on: a sample of agreed exclusions must be re-checked before publishing. The sample size is set in M5-slim.",
    openMissed: "Open triage",
    toPublish: "Go to publish",
  },
  fr: {
    eyebrow: "Sélection · accord",
    title: "Vous et l'agent êtes d'accord sur {pct} des notices ; il aurait écarté {missed} de vos inclusions.",
    titleNoPairs: "Accord avec l'agent",
    lede: "Ce n'est pas une statistique inter-évaluateurs : l'agent n'est pas un second évaluateur.",
    loading: "Lecture de l'accord…",
    emptyDecided: "Décidez d'abord quelques notices.",
    emptyProposals: "Aucune proposition de l'agent à comparer.",
    toProposals: "Lancer les propositions de l'agent",
    soFar: "sur {n} décidées à ce stade",
    agreement: "Accord avec l'agent",
    missed: "Vos inclusions qu'il proposait d'exclure",
    missedNote: "le chiffre qui compte le plus",
    extra: "Ses inclusions que vous avez exclues",
    unclear: "Incertain d'un côté ou de l'autre",
    matrix: "Vous et l'agent",
    you: "Vous",
    agent: "Agent",
    include: "Inclure",
    exclude: "Exclure",
    byCriterion: "Désaccords par critère",
    noSplits: "Aucun désaccord par critère.",
    afterSeeing: "{n} notices ont été décidées avec le brouillon déjà visible et ne sont pas comptées.",
    kappa: "Kappa de Cohen",
    kappaDisabled: "exige un second évaluateur humain · pas en production",
    sample: "Contrôle par échantillon des exclusions concordantes",
    sampleNotNeeded: "Vous avez vu chaque notice. Aucun échantillon n'est nécessaire.",
    sampleOptIn: "L'exclusion concordante avec l'IA est activée : un échantillon des exclusions concordantes doit être revérifié avant publication. La taille de l'échantillon est fixée en M5-slim.",
    openMissed: "Ouvrir le tri",
    toPublish: "Aller à la publication",
  },
  ar: {
    eyebrow: "الفرز · الاتفاق",
    title: "اتفقت أنت والوكيل على {pct} من السجلات؛ وكان سيُسقط {missed} من إدراجاتك.",
    titleNoPairs: "الاتفاق مع الوكيل",
    lede: "ليس مقياسًا للاتفاق بين المقيّمين: الوكيل ليس مراجعًا ثانيًا.",
    loading: "جارٍ قراءة الاتفاق…",
    emptyDecided: "احسم بعض السجلات أولًا.",
    emptyProposals: "لا مقترحات للوكيل للمقارنة.",
    toProposals: "شغّل مقترحات الوكيل",
    soFar: "من {n} محسومة حتى الآن",
    agreement: "الاتفاق مع الوكيل",
    missed: "إدراجاتك التي اقترح استبعادها",
    missedNote: "الرقم الأهم",
    extra: "إدراجاته التي استبعدتها",
    unclear: "غير واضح لدى أحد الطرفين",
    matrix: "أنت والوكيل",
    you: "أنت",
    agent: "الوكيل",
    include: "إدراج",
    exclude: "استبعاد",
    byCriterion: "مواضع الاختلاف حسب المعيار",
    noSplits: "لا اختلاف حسب المعايير.",
    afterSeeing: "{n} سجلًا حُسمت والمسودة ظاهرة، فلا تُحتسب.",
    kappa: "كابا كوهين",
    kappaDisabled: "يحتاج إلى مراجع بشري ثانٍ · ليس للإنتاج",
    sample: "فحص عيّنة من الاستبعادات المتفق عليها",
    sampleNotNeeded: "رأيت كل سجل. لا حاجة إلى عيّنة.",
    sampleOptIn: "الاستبعاد المتفق عليه مع الذكاء الاصطناعي مفعّل: يجب إعادة فحص عيّنة من الاستبعادات المتفق عليها قبل النشر. يُحدَّد حجم العيّنة في M5-slim.",
    openMissed: "فتح المراجعة",
    toPublish: "الانتقال إلى النشر",
  },
} as const satisfies Record<Locale, Record<string, string>>;

export type AgreementCopyKey = keyof (typeof COPY)["en"];
export const AGREEMENT_COPY: Record<Locale, Record<AgreementCopyKey, string>> = COPY;

function fill(template: string, values: Record<string, string | number> = {}): string {
  return template.replace(/\{(\w+)\}/g, (_, k: string) => {
    if (!(k in values)) throw new Error(`agreement copy needs {${k}}`);
    return String(values[k]);
  });
}

function consoleOrigin(): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get("console") ?? "";
}

function codeOf(error: unknown): { code: string; message: string } {
  return isScreeningApiError(error) ? { code: error.code, message: error.serverMessage } : { code: "ENGINE_UNREACHABLE", message: "" };
}

type Loaded = { agreement: Agreement; summary: Summary; settings: Settings };

export function ScreeningAgreement({ locale }: Readonly<{ locale: Locale }>) {
  const t = useCallback((key: AgreementCopyKey, values?: Record<string, string | number>) => fill(AGREEMENT_COPY[locale][key], values), [locale]);
  const n = useCallback((value: number) => formatNumber(locale, value), [locale]);
  const origin = useMemo(consoleOrigin, []);
  const [state, setState] = useState<{ status: "loading" } | { status: "ready"; data: Loaded } | { status: "error"; code: string; message: string }>({ status: "loading" });

  const load = useCallback(async () => {
    try {
      const [agreement, summary, settings] = await Promise.all([getAgreement(origin), getSummary(origin), getSettings(origin)]);
      setState({ status: "ready", data: { agreement, summary, settings } });
    } catch (error) {
      setState({ status: "error", ...codeOf(error) });
    }
  }, [origin]);

  useEffect(() => {
    void load();
  }, [load]);

  const body = (() => {
    if (state.status === "loading") return <p className="text-ink-muted" role="status">{t("loading")}</p>;
    if (state.status === "error") return <StateCard pageHeading locale={locale} code={state.code} message={state.message} consoleOrigin={origin} onRetry={() => void load()} />;
    const { agreement: a, summary, settings } = state.data;
    const header = (title: string) => (
      <header>
        <p className="text-xs font-semibold uppercase tracking-[0.05em] text-brand rtl:tracking-normal">{t("eyebrow")}</p>
        <h1 className="font-display mt-1 text-[1.75rem] leading-[2.25rem] text-ink">{title}</h1>
        <p className="mt-2 text-ink-muted">{t("lede")}</p>
      </header>
    );
    if (summary.decided === 0 || summary.agent_proposed === 0) {
      return (
        <div className="space-y-6">
          {header(t("titleNoPairs"))}
          <section className="rounded-lg border border-rule bg-leaf p-5" data-empty={summary.decided === 0 ? "decided" : "proposals"}>
            {summary.decided === 0 ? (
              <>
                <p className="text-ink">{t("emptyDecided")}</p>
                <a className="mt-2 inline-block text-brand underline" href={stepHref(locale, "triage", origin)}>{t("openMissed")}</a>
              </>
            ) : (
              <>
                <p className="text-ink">{t("emptyProposals")}</p>
                <a className="mt-2 inline-block text-brand underline" href={stepHref(locale, "proposals", origin)}>{t("toProposals")}</a>
              </>
            )}
          </section>
        </div>
      );
    }

    const m = a.table_2x2;
    const soFar = summary.decided < summary.total ? t("soFar", { n: n(summary.decided) }) : null;
    const pct = a.agreement_pct === null ? null : `${n(a.agreement_pct)}%`;
    const maxSplit = Math.max(1, ...a.splits_by_criterion.map((s) => s.n));
    const cards: [AgreementCopyKey, string, "include" | "unclear" | "exclude", AgreementCopyKey | null][] = [
      ["agreement", pct ?? "—", "include", null],
      ["missed", n(m.you_include_agent_exclude), "unclear", "missedNote"],
      ["extra", n(m.you_exclude_agent_include), "exclude", null],
      ["unclear", n(a.unclear_either_side), "exclude", null],
    ];

    return (
      <div className="space-y-6">
        {header(pct === null ? t("titleNoPairs") : t("title", { pct, missed: n(m.you_include_agent_exclude) }))}

        <ul className="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-4">
          {cards.map(([key, value, role, note]) => (
            <li key={key} className={`rounded-lg border bg-leaf p-4 ${role === "unclear" ? "border-unclear" : "border-rule"}`} data-card={key}>
              <p className="text-sm text-ink-muted">{t(key)}</p>
              <p className="mt-1 text-2xl text-ink tabular-nums">{value}</p>
              {note ? <p className="text-xs text-unclear">{t(note)}</p> : null}
              {soFar ? <p className="text-xs text-ink-muted">{soFar}</p> : null}
            </li>
          ))}
        </ul>

        {a.decided_after_seeing_the_draft > 0 ? <p className="text-sm text-ink-muted">{t("afterSeeing", { n: n(a.decided_after_seeing_the_draft) })}</p> : null}

        <div className="flex flex-wrap gap-6">
          <div className="min-w-0 flex-[999_1_480px] space-y-6">
            <section aria-labelledby="agreement-matrix" className="rounded-lg border border-rule bg-leaf p-5">
              <h2 id="agreement-matrix" className="font-semibold text-ink">{t("matrix")}</h2>
              <table className="mt-3 w-full text-sm tabular-nums">
                <thead>
                  <tr>
                    <td />
                    <th scope="col" className="py-1 text-end text-ink-muted">{t("agent")}: {t("include")}</th>
                    <th scope="col" className="py-1 text-end text-ink-muted">{t("agent")}: {t("exclude")}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-t border-rule">
                    <th scope="row" className="py-1 text-start font-normal text-ink">{t("you")}: {t("include")}</th>
                    <td className="py-1 text-end" data-cell="both_include">{n(m.both_include)}</td>
                    <td className="bg-unclear-soft py-1 text-end" data-cell="you_include_agent_exclude">{n(m.you_include_agent_exclude)}</td>
                  </tr>
                  <tr className="border-t border-rule">
                    <th scope="row" className="py-1 text-start font-normal text-ink">{t("you")}: {t("exclude")}</th>
                    <td className="bg-unclear-soft py-1 text-end" data-cell="you_exclude_agent_include">{n(m.you_exclude_agent_include)}</td>
                    <td className="py-1 text-end" data-cell="both_exclude">{n(m.both_exclude)}</td>
                  </tr>
                </tbody>
              </table>
              {m.you_include_agent_exclude > 0 ? (
                <a className="mt-3 inline-block text-brand underline" href={stepHref(locale, "triage", origin)}>{t("openMissed")}</a>
              ) : null}
            </section>

            <section aria-labelledby="agreement-criteria" className="rounded-lg border border-rule bg-leaf p-5">
              <h2 id="agreement-criteria" className="font-semibold text-ink">{t("byCriterion")}</h2>
              {a.splits_by_criterion.length === 0 ? (
                <p className="mt-2 text-sm text-ink-muted">{t("noSplits")}</p>
              ) : (
                <ul className="mt-3 space-y-2 text-sm">
                  {[...a.splits_by_criterion].sort((x, y) => y.n - x.n).map((s) => (
                    <li key={s.criterion_id} className="grid grid-cols-[6rem_1fr_3rem] items-center gap-3" data-split={s.criterion_id}>
                      <DataCell>{s.criterion_id}</DataCell>
                      <div className="h-2 rounded-full bg-paper">
                        <div className="h-full rounded-full bg-unclear" style={{ width: `${Math.round((100 * s.n) / maxSplit)}%` }} />
                      </div>
                      <span className="text-end tabular-nums text-ink">{n(s.n)}</span>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>

          <div className="w-full flex-[1_1_320px] space-y-6">
            <section aria-labelledby="agreement-kappa" aria-disabled="true" tabIndex={0} className="rounded-lg border border-rule bg-exclude-soft p-5" data-kappa>
              <h2 id="agreement-kappa" className="font-semibold text-exclude">{t("kappa")}</h2>
              <p className="mt-1 text-2xl text-exclude">—</p>
              <p className="mt-1 text-sm text-exclude">{t("kappaDisabled")}</p>
            </section>

            <section aria-labelledby="agreement-sample" className="rounded-lg border border-rule bg-leaf p-5" data-sample={settings.mode}>
              <h2 id="agreement-sample" className="font-semibold text-ink">{t("sample")}</h2>
              {settings.mode === "ai_agreed_exclusion" ? (
                <p className="mt-2 text-sm text-ink">
                  <DecisionBadge role="unclear">{settings.sample_audit_size ?? "—"}</DecisionBadge> {t("sampleOptIn")}
                </p>
              ) : (
                <p className="mt-2 text-sm text-ink">{t("sampleNotNeeded")}</p>
              )}
            </section>

            <a className="inline-block text-brand underline" href={stepHref(locale, "publish", origin)}>{t("toPublish")}</a>
          </div>
        </div>
      </div>
    );
  })();

  return (
    <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8 lg:py-14">
      <ScreeningSteps locale={locale} current="agreement" consoleOrigin={origin} />
      {body}
    </div>
  );
}
