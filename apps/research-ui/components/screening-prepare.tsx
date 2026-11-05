"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { formatNumber, type Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge, GatePanel } from "@/components/ui/base";
import { ScreeningSteps, StateCard } from "@/components/screening-state-card";
import { getScreeningBatches, isScreeningApiError, type ScreeningBatches } from "@/lib/screening-api";
import { getJob, getSettings, prepare, putSettings, type JobView, type Settings } from "@/lib/screening-v1";

/**
 * Prepare (spec 02): the reveal and mode settings, the rule table (read-only:
 * the engine's plain-code rules, never computed here), the batches, and
 * prepare behind a confirmation. Nothing is written until confirmed.
 *
 * Accepting the corpus has no HTTP route yet (M0 shipped the CLI), so a
 * missing snapshot shows the terminal step instead of a button.
 */

const COPY = {
  en: {
    eyebrow: "Screening · prepare",
    title: "Prepare the screening batches.",
    live: "Live data from this workspace's screening engine",
    loading: "Reading the workspace…",
    rules: "How an agent draft's outcome is derived",
    rulesBody: "The engine applies these rules in plain code to the agent's answers; the model never chooses the outcome, and you always decide.",
    ruleExclude: "Otherwise exclude: any exclusion criterion answered yes, or any inclusion criterion answered no.",
    ruleUnclear: "First, Unclear → full text: a check on the draft failed, the agent could not decide, or any criterion is not reported.",
    ruleInclude: "Otherwise include: every inclusion yes and every exclusion no.",
    settings: "While screening",
    blinding: "The agent's draft",
    blindingAfter: "Reveal after my decision (recommended)",
    blindingShow: "Show beside the record",
    mode: "Who sees each record",
    modeEvery: "I see every record (default)",
    modeAi: "AI-agreed exclusion: skip records the agent calls clear exclusions",
    aiConfirm: "I understand this skips records I would otherwise read; it is journaled and disclosed in the methods paragraph.",
    sample: "Sample-audit size for skipped exclusions",
    saveSettings: "Save settings",
    saved: "Settings saved",
    batches: "Batches",
    noBatches: "No batches yet.",
    batchCount: "{n} batches prepared",
    batchSize: "Records per batch",
    prepare: "Prepare batches",
    confirmTitle: "Prepare batches of {size} records?",
    confirmBody: "Earlier decisions stay in the decision log. Records whose batch changes must be decided again.",
    confirm: "Prepare now",
    cancel: "Cancel",
    started: "Preparing (job {job}). The batches appear here when it finishes.",
    prepared: "Batches prepared (job {job}).",
    prepareFailed: "Preparing failed (job {job}). Nothing was prepared. The engine said: {reason}",
    refresh: "Refresh",
  },
  fr: {
    eyebrow: "Sélection · préparation",
    title: "Préparez les lots de sélection.",
    live: "Données en direct du moteur de sélection de cet espace",
    loading: "Lecture de l'espace de travail…",
    rules: "Comment l'issue d'un brouillon de l'agent est établie",
    rulesBody: "Le moteur applique ces règles en code simple aux réponses de l'agent ; le modèle ne choisit jamais l'issue, et c'est toujours vous qui décidez.",
    ruleExclude: "Sinon exclure : un critère d'exclusion répondu oui, ou un critère d'inclusion répondu non.",
    ruleUnclear: "D'abord, Incertain → texte intégral : un contrôle du brouillon a échoué, l'agent n'a pas pu décider, ou un critère n'est pas rapporté.",
    ruleInclude: "Sinon inclure : toutes les inclusions à oui et toutes les exclusions à non.",
    settings: "Pendant la sélection",
    blinding: "Le brouillon de l'agent",
    blindingAfter: "L'afficher après ma décision (recommandé)",
    blindingShow: "L'afficher à côté de la notice",
    mode: "Qui voit chaque notice",
    modeEvery: "Je vois chaque notice (par défaut)",
    modeAi: "Exclusion validée par l'IA : passer les notices que l'agent juge clairement exclues",
    aiConfirm: "Je comprends que cela passe des notices que je lirais sinon ; c'est journalisé et déclaré dans la section méthodes.",
    sample: "Taille de l'échantillon d'audit des exclusions passées",
    saveSettings: "Enregistrer les réglages",
    saved: "Réglages enregistrés",
    batches: "Lots",
    noBatches: "Pas encore de lots.",
    batchCount: "{n} lots préparés",
    batchSize: "Notices par lot",
    prepare: "Préparer les lots",
    confirmTitle: "Préparer des lots de {size} notices ?",
    confirmBody: "Les décisions antérieures restent dans le journal. Les notices dont le lot change doivent être décidées à nouveau.",
    confirm: "Préparer maintenant",
    cancel: "Annuler",
    started: "Préparation en cours (tâche {job}). Les lots apparaissent ici une fois terminée.",
    prepared: "Lots préparés (tâche {job}).",
    prepareFailed: "La préparation a échoué (tâche {job}). Rien n'a été préparé. Le moteur indique : {reason}",
    refresh: "Actualiser",
  },
  ar: {
    eyebrow: "الفرز · التحضير",
    title: "حضّر دفعات الفرز.",
    live: "بيانات حية من محرك الفرز لهذه المساحة",
    loading: "جارٍ قراءة مساحة العمل…",
    rules: "كيف تُستخرج نتيجة مسودة الوكيل",
    rulesBody: "يطبّق المحرك هذه القواعد بشيفرة بسيطة على إجابات الوكيل؛ لا يختار النموذج النتيجة أبدًا، وأنت من يقرر دائمًا.",
    ruleExclude: "وإلا فاستبعاد: أي معيار استبعاد أجيب بنعم، أو أي معيار إدراج أجيب بلا.",
    ruleUnclear: "أولًا، غير واضح ← النص الكامل: فشل فحص على المسودة، أو لم يتمكن الوكيل من القرار، أو معيار غير مذكور.",
    ruleInclude: "وإلا فإدراج: كل معايير الإدراج نعم وكل معايير الاستبعاد لا.",
    settings: "أثناء الفرز",
    blinding: "مسودة الوكيل",
    blindingAfter: "اعرضها بعد قراري (موصى به)",
    blindingShow: "اعرضها بجانب السجل",
    mode: "من يرى كل سجل",
    modeEvery: "أرى كل سجل (افتراضي)",
    modeAi: "استبعاد يوافق عليه الذكاء الاصطناعي: تخطي السجلات التي يعدّها الوكيل مستبعدة بوضوح",
    aiConfirm: "أفهم أن هذا يتخطى سجلات كنت سأقرؤها؛ ويُسجَّل ذلك ويُفصح عنه في فقرة المنهجية.",
    sample: "حجم عينة التدقيق للاستبعادات المتخطاة",
    saveSettings: "حفظ الإعدادات",
    saved: "حُفظت الإعدادات",
    batches: "الدفعات",
    noBatches: "لا توجد دفعات بعد.",
    batchCount: "{n} دفعة محضّرة",
    batchSize: "عدد السجلات في الدفعة",
    prepare: "تحضير الدفعات",
    confirmTitle: "تحضير دفعات من {size} سجلًا؟",
    confirmBody: "تبقى القرارات السابقة في سجل القرارات. ويجب حسم السجلات التي تتغير دفعتها من جديد.",
    confirm: "حضّر الآن",
    cancel: "إلغاء",
    started: "جارٍ التحضير (المهمة {job}). تظهر الدفعات هنا عند الانتهاء.",
    prepared: "حُضّرت الدفعات (المهمة {job}).",
    prepareFailed: "فشل التحضير (المهمة {job}). لم يُحضَّر شيء. قال المحرك: {reason}",
    refresh: "تحديث",
  },
} as const satisfies Record<Locale, Record<string, string>>;

export type PrepareCopyKey = keyof (typeof COPY)["en"];
export const PREPARE_COPY: Record<Locale, Record<PrepareCopyKey, string>> = COPY;

function fill(template: string, values: Record<string, string | number> = {}): string {
  return template.replace(/\{(\w+)\}/g, (_, k: string) => {
    if (!(k in values)) throw new Error(`prepare copy needs {${k}}`);
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

export function ScreeningPrepare({ locale }: Readonly<{ locale: Locale }>) {
  const t = useCallback((key: PrepareCopyKey, values?: Record<string, string | number>) => fill(PREPARE_COPY[locale][key], values), [locale]);
  const origin = useMemo(consoleOrigin, []);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [draft, setDraft] = useState<Settings | null>(null);
  const [aiConfirmed, setAiConfirmed] = useState(false);
  const [batches, setBatches] = useState<ScreeningBatches | null>(null);
  const [error, setError] = useState<{ code: string; message: string } | null>(null);
  const [refusal, setRefusal] = useState<{ code: string; message: string } | null>(null);
  const [size, setSize] = useState(20);
  const [confirming, setConfirming] = useState(false);
  const [job, setJob] = useState<string | null>(null);
  const [jobView, setJobView] = useState<JobView | null>(null);
  const [message, setMessage] = useState("");

  const load = useCallback(async () => {
    setError(null);
    try {
      const [s, b] = await Promise.all([getSettings(origin), getScreeningBatches(origin)]);
      setSettings(s);
      setDraft(s);
      setBatches(b);
    } catch (e) {
      setError(codeOf(e));
    }
  }, [origin]);

  useEffect(() => {
    void load();
  }, [load]);

  async function save() {
    if (!draft || !settings) return;
    setRefusal(null);
    try {
      const turningOn = draft.mode === "ai_agreed_exclusion" && settings.mode !== "ai_agreed_exclusion";
      const next = await putSettings(origin, {
        blinding: draft.blinding,
        mode: draft.mode,
        ...(draft.mode === "ai_agreed_exclusion" ? { sample_audit_size: draft.sample_audit_size } : {}),
        ...(turningOn ? { confirm_ai_agreed_exclusion: aiConfirmed } : {}),
      });
      setSettings(next);
      setDraft(next);
      setMessage(t("saved"));
    } catch (e) {
      setRefusal(codeOf(e));
    }
  }

  // Follow the prepare job: a failed job must say so, not look like a slow one
  // (golden run, 2026-11-05). On success the batches are re-read.
  useEffect(() => {
    if (!job) return;
    let stopped = false;
    const tick = async () => {
      try {
        const view = await getJob(origin, job);
        if (stopped) return;
        setJobView(view);
        if (view.state === "queued" || view.state === "running") {
          window.setTimeout(() => void tick(), 1000);
        } else if (view.state === "success") {
          await load();
        }
      } catch (e) {
        if (!stopped) setRefusal(codeOf(e));
      }
    };
    void tick();
    return () => {
      stopped = true;
    };
  }, [job, origin, load]);

  async function runPrepare() {
    setConfirming(false);
    setRefusal(null);
    try {
      const started = await prepare(origin, size);
      setJob(started.job_id);
      setJobView(null);
    } catch (e) {
      setRefusal(codeOf(e));
    }
  }

  const body = (() => {
    if (error) return <StateCard pageHeading locale={locale} code={error.code} message={error.message} consoleOrigin={origin} onRetry={() => void load()} />;
    if (!settings || !draft || !batches) return <p className="text-ink-muted" role="status">{t("loading")}</p>;
    const aiNeedsConfirm = draft.mode === "ai_agreed_exclusion" && settings.mode !== "ai_agreed_exclusion";
    const canSave = !aiNeedsConfirm || (aiConfirmed && (draft.sample_audit_size ?? 0) > 0);
    const stale = batches.batches.some((b) => b.binding?.state === "STALE_BINDING");

    return (
      <div className="space-y-6">
        <header>
          <p className="text-xs font-semibold uppercase tracking-[0.05em] text-brand rtl:tracking-normal">{t("eyebrow")}</p>
          <h1 className="font-display mt-1 text-[1.75rem] leading-[2.25rem] text-ink">{t("title")}</h1>
          <p className="mt-2 inline-block border border-rule-strong px-2 py-0.5 text-xs text-ink-muted">{t("live")}</p>
        </header>
        <p role="status" aria-live="polite" className="sr-only">
          {message}
        </p>
        {refusal ? <StateCard locale={locale} code={refusal.code} message={refusal.message} consoleOrigin={origin} /> : null}
        {stale ? <StateCard locale={locale} code="STALE_BINDING" consoleOrigin={origin} /> : null}

        <div className="flex flex-wrap gap-6">
          <div className="min-w-0 flex-[999_1_480px] space-y-6">
            <section aria-labelledby="prepare-rules" className="rounded-lg border border-rule bg-leaf p-5">
              <h2 id="prepare-rules" className="font-semibold text-ink">
                {t("rules")}
              </h2>
              <p className="mt-1 text-sm text-ink-muted">{t("rulesBody")}</p>
              <ol className="mt-3 grid gap-3 sm:grid-cols-3">
                <li className="rounded-md bg-unclear-soft p-3 text-sm text-ink">{t("ruleUnclear")}</li>
                <li className="rounded-md bg-exclude-soft p-3 text-sm text-ink">{t("ruleExclude")}</li>
                <li className="rounded-md bg-include-soft p-3 text-sm text-ink">{t("ruleInclude")}</li>
              </ol>
            </section>

            <section aria-labelledby="prepare-settings" className="rounded-lg border border-rule bg-leaf p-5">
              <h2 id="prepare-settings" className="font-semibold text-ink">
                {t("settings")}
              </h2>
              <fieldset className="mt-3">
                <legend className="text-sm font-semibold text-ink">{t("blinding")}</legend>
                {(["reveal_after_decision", "show"] as const).map((value) => (
                  <label key={value} className="mt-2 flex min-h-11 items-center gap-2 text-ink">
                    <input type="radio" name="blinding" checked={draft.blinding === value} onChange={() => setDraft({ ...draft, blinding: value })} />
                    {value === "show" ? t("blindingShow") : t("blindingAfter")}
                  </label>
                ))}
              </fieldset>
              <fieldset className="mt-4">
                <legend className="text-sm font-semibold text-ink">{t("mode")}</legend>
                {(["human_sees_every_record", "ai_agreed_exclusion"] as const).map((value) => (
                  <label key={value} className="mt-2 flex min-h-11 items-center gap-2 text-ink">
                    <input type="radio" name="mode" checked={draft.mode === value} onChange={() => setDraft({ ...draft, mode: value })} />
                    {value === "ai_agreed_exclusion" ? t("modeAi") : t("modeEvery")}
                  </label>
                ))}
                {draft.mode === "ai_agreed_exclusion" ? (
                  <div className="mt-3 space-y-2 rounded-md border border-rule-strong p-3">
                    <label className="block text-sm text-ink">
                      {t("sample")}
                      <input
                        type="number"
                        min={1}
                        value={draft.sample_audit_size ?? ""}
                        onChange={(e) => setDraft({ ...draft, sample_audit_size: e.target.value ? Number(e.target.value) : null })}
                        className="mt-1 block w-32 rounded-md border border-rule bg-paper p-2 text-ink"
                      />
                    </label>
                    {aiNeedsConfirm ? (
                      <label className="flex items-start gap-2 text-sm text-ink">
                        <input type="checkbox" checked={aiConfirmed} onChange={(e) => setAiConfirmed(e.target.checked)} className="mt-1" />
                        {t("aiConfirm")}
                      </label>
                    ) : null}
                  </div>
                ) : null}
              </fieldset>
              <Button className="mt-4" disabled={!canSave} onClick={() => void save()}>
                {t("saveSettings")}
              </Button>
            </section>
          </div>

          <div className="w-full flex-[1_1_320px] space-y-6">
            <section aria-labelledby="prepare-batches" className="rounded-lg border border-rule bg-leaf p-5">
              <h2 id="prepare-batches" className="font-semibold text-ink">
                {t("batches")}
              </h2>
              {batches.count === 0 ? (
                <p className="mt-2 text-ink-muted">{t("noBatches")}</p>
              ) : (
                <>
                  <p className="mt-2 text-ink">{t("batchCount", { n: formatNumber(locale, batches.count) })}</p>
                  <ul className="mt-2 space-y-1 text-sm">
                    {batches.batches.map((b) => (
                      <li key={b.batch_index} className="flex flex-wrap items-center gap-2">
                        <DataCell>{b.batch_file}</DataCell>
                        <span className="text-ink-muted">{formatNumber(locale, b.items)}</span>
                        {b.binding?.state === "STALE_BINDING" ? <DecisionBadge role="blocked">STALE_BINDING</DecisionBadge> : null}
                      </li>
                    ))}
                  </ul>
                </>
              )}
              {job ? (
                <div className="mt-3 space-y-2" data-job={jobView?.state ?? "running"}>
                  {jobView?.state === "success" ? (
                    <p role="status" className="rounded-md bg-include-soft px-3 py-2 text-sm text-include">{t("prepared", { job })}</p>
                  ) : jobView && jobView.state !== "queued" && jobView.state !== "running" ? (
                    <p role="alert" className="rounded-md bg-blocked-soft px-3 py-2 text-sm text-blocked">
                      {t("prepareFailed", { job, reason: jobView.error || `exit code ${jobView.exit_code ?? "?"}` })}
                    </p>
                  ) : (
                    <>
                      <p role="status" className="text-sm text-ink">{t("started", { job })}</p>
                      <Button onClick={() => void load()}>{t("refresh")}</Button>
                    </>
                  )}
                </div>
              ) : null}
            </section>

            <GatePanel
              label={t("prepare")}
              actions={
                confirming ? (
                  <>
                    <Button variant="primary" onClick={() => void runPrepare()}>
                      {t("confirm")}
                    </Button>
                    <Button onClick={() => setConfirming(false)}>{t("cancel")}</Button>
                  </>
                ) : (
                  <Button variant="primary" onClick={() => setConfirming(true)}>
                    {t("prepare")}
                  </Button>
                )
              }
            >
              {confirming ? (
                <div role="alertdialog" aria-labelledby="prepare-confirm" onKeyDown={(e) => e.key === "Escape" && setConfirming(false)}>
                  <p id="prepare-confirm" className="font-semibold">
                    {t("confirmTitle", { size: formatNumber(locale, size) })}
                  </p>
                  <p className="mt-1 text-sm">{t("confirmBody")}</p>
                </div>
              ) : (
                <label className="block text-sm">
                  {t("batchSize")}
                  <input
                    type="number"
                    min={1}
                    max={500}
                    value={size}
                    onChange={(e) => setSize(Math.max(1, Number(e.target.value) || 1))}
                    className="mt-1 block w-28 rounded-md border border-rule bg-paper p-2 text-ink"
                  />
                </label>
              )}
            </GatePanel>
          </div>
        </div>
      </div>
    );
  })();

  return (
    <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8 lg:py-14">
      <ScreeningSteps locale={locale} current="prepare" consoleOrigin={origin} />
      {body}
    </div>
  );
}
