"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { formatNumber, type Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge, GatePanel } from "@/components/ui/base";
import { PilotCard } from "@/components/screening-pilot-card";
import { ScreeningSteps, StateCard } from "@/components/screening-state-card";
import { notifyReviewChanged } from "@/components/review-bus";
import { getScreeningBatches, isScreeningApiError, type ScreeningBatches } from "@/lib/screening-api";
import { amendMethod, getJob, getSettings, prepare, putSettings, type JobView, type MethodAmendment, type NotReportedPolicy, type Settings } from "@/lib/screening-v1";

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
    ruleUnclearExcludePolicy: "First, Unclear → full text: a check on the draft failed or the agent could not decide.",
    ruleExcludeExcludePolicy: "Otherwise exclude: any exclusion criterion answered yes, any inclusion criterion answered no, or any inclusion criterion not reported.",
    ruleIncludeExcludePolicy: "Otherwise include: every inclusion yes and no exclusion yes.",
    ruleExcludeDecisive: "Then exclude: any exclusion criterion answered yes, or any inclusion criterion answered no, even when other criteria are not reported.",
    ruleIncludeDecisive: "Then Unclear → full text: any criterion not reported. Otherwise include: every inclusion yes and every exclusion no.",
    setByProtocol: "Set by your protocol. A change is recorded as an amendment.",
    settings: "While screening",
    blinding: "The agent's draft",
    blindingAfter: "Reveal after my decision (recommended)",
    blindingShow: "Show beside the record",
    notReported: "A criterion the title and abstract do not report",
    notReportedUnclear: "It sends the record to Unclear (full text), even beside a decisive answer",
    notReportedDecisive: "A decisive answer first: an exclusion met or an inclusion not met excludes; otherwise Unclear",
    notReportedExclude: "An unreported inclusion criterion excludes the record",
    notReportedNote: "This rule shapes the agent's drafts and the reason the screen offers you; your own decision is never overridden. A change is recorded as an amendment.",
    notReportedDefault: "The rule shown is the harness default: the protocol does not set it and nobody has chosen it.",
    amendTitle: "Amend the protocol's method?",
    amendChange: "{field}: from “{from}” to “{to}”.",
    amendBody: "The change is recorded as an amendment: who, when, from and to go into the audit journal and into the methods paragraph of the export. The signed protocol, the corpus and your decisions are not changed.",
    amendDrafts: "Existing agent drafts keep their answers and are shown and counted under the new rule; each keeps the outcome first recorded.",
    amendConfirm: "Record the amendment",
    amendCancel: "Keep the protocol's value",
    amended: "Amended on {date} by {who}: {field}, from “{from}” to “{to}”.",
    amendedStatus: "Amendment recorded",
    advance: "After I decide",
    advanceDraft: "Show the draft, then N (default)",
    advanceNow: "Move on at once (drafts stay in the record's details)",
    advanceShown: "Drafts are already beside the record, so the next record always opens at once.",
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
    ruleUnclearExcludePolicy: "D'abord, Incertain → texte intégral : un contrôle du brouillon a échoué ou l'agent n'a pas pu décider.",
    ruleExcludeExcludePolicy: "Sinon exclure : un critère d'exclusion répondu oui, un critère d'inclusion répondu non, ou un critère d'inclusion non rapporté.",
    ruleIncludeExcludePolicy: "Sinon inclure : toutes les inclusions à oui et aucune exclusion à oui.",
    ruleExcludeDecisive: "Ensuite exclure : un critère d'exclusion répondu oui, ou un critère d'inclusion répondu non, même si d'autres critères ne sont pas rapportés.",
    ruleIncludeDecisive: "Ensuite Incertain → texte intégral : un critère non rapporté. Sinon inclure : toutes les inclusions à oui et toutes les exclusions à non.",
    setByProtocol: "Défini par votre protocole. Un changement est enregistré comme amendement.",
    settings: "Pendant la sélection",
    blinding: "Le brouillon de l'agent",
    blindingAfter: "L'afficher après ma décision (recommandé)",
    blindingShow: "L'afficher à côté de la notice",
    notReported: "Un critère que le titre et le résumé ne rapportent pas",
    notReportedUnclear: "Il envoie la notice en Incertain (texte intégral), même à côté d'une réponse décisive",
    notReportedDecisive: "Une réponse décisive d'abord : une exclusion remplie ou une inclusion non remplie exclut ; sinon Incertain",
    notReportedExclude: "Un critère d'inclusion non rapporté exclut la notice",
    notReportedNote: "Cette règle façonne les brouillons de l'agent et le motif que l'écran vous propose ; votre propre décision n'est jamais remplacée. Un changement est enregistré comme amendement.",
    notReportedDefault: "La règle affichée est celle du logiciel par défaut : le protocole ne la fixe pas et personne ne l'a choisie.",
    amendTitle: "Amender la méthode du protocole ?",
    amendChange: "{field} : de « {from} » à « {to} ».",
    amendBody: "Le changement est enregistré comme amendement : qui, quand, avant et après vont dans le journal d'audit et dans le paragraphe de méthode de l'export. Le protocole signé, le corpus et vos décisions ne changent pas.",
    amendDrafts: "Les brouillons existants de l'agent gardent leurs réponses et sont affichés et comptés selon la nouvelle règle ; chacun garde l'issue enregistrée d'abord.",
    amendConfirm: "Enregistrer l'amendement",
    amendCancel: "Garder la valeur du protocole",
    amended: "Amendé le {date} par {who} : {field}, de « {from} » à « {to} ».",
    amendedStatus: "Amendement enregistré",
    advance: "Après ma décision",
    advanceDraft: "Afficher le brouillon, puis N (par défaut)",
    advanceNow: "Passer tout de suite à la suivante (le brouillon reste dans les détails de la notice)",
    advanceShown: "Les brouillons sont déjà à côté de la notice ; la notice suivante s'ouvre donc toujours tout de suite.",
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
    ruleUnclearExcludePolicy: "أولًا، غير واضح ← النص الكامل: فشل فحص على المسودة أو لم يتمكن الوكيل من القرار.",
    ruleExcludeExcludePolicy: "وإلا فاستبعاد: أي معيار استبعاد أجيب بنعم، أو أي معيار إدراج أجيب بلا، أو أي معيار إدراج غير مذكور.",
    ruleIncludeExcludePolicy: "وإلا فإدراج: كل معايير الإدراج نعم ولا معيار استبعاد بنعم.",
    ruleExcludeDecisive: "ثم استبعاد: أي معيار استبعاد أجيب بنعم، أو أي معيار إدراج أجيب بلا، حتى لو كانت معايير أخرى غير مذكورة.",
    ruleIncludeDecisive: "ثم غير واضح ← النص الكامل: أي معيار غير مذكور. وإلا فإدراج: كل معايير الإدراج نعم وكل معايير الاستبعاد لا.",
    setByProtocol: "محدَّد في بروتوكولك. يُسجَّل أي تغيير كتعديل.",
    settings: "أثناء الفرز",
    blinding: "مسودة الوكيل",
    blindingAfter: "اعرضها بعد قراري (موصى به)",
    blindingShow: "اعرضها بجانب السجل",
    notReported: "معيار لا يذكره العنوان والملخص",
    notReportedUnclear: "يرسل السجل إلى غير واضح (النص الكامل)، حتى بجانب إجابة حاسمة",
    notReportedDecisive: "الإجابة الحاسمة أولًا: استبعاد متحقق أو إدراج غير متحقق يستبعد؛ وإلا فغير واضح",
    notReportedExclude: "معيار إدراج غير مذكور يستبعد السجل",
    notReportedNote: "تحدد هذه القاعدة مسودات الوكيل والسبب الذي تقترحه الشاشة؛ ولا يُتجاوز قرارك أبدًا. يُسجَّل أي تغيير كتعديل.",
    notReportedDefault: "القاعدة المعروضة هي القاعدة الافتراضية للأداة: لا يحددها البروتوكول ولم يخترها أحد.",
    amendTitle: "تعديل منهج البروتوكول؟",
    amendChange: "{field}: من «{from}» إلى «{to}».",
    amendBody: "يُسجَّل التغيير كتعديل: من ومتى والقيمة السابقة والجديدة تُكتب في سجل التدقيق وفي فقرة المنهج في التصدير. لا يتغير البروتوكول الموقَّع ولا المجموعة ولا قراراتك.",
    amendDrafts: "تحتفظ مسودات الوكيل الموجودة بإجاباتها وتُعرض وتُحسب وفق القاعدة الجديدة؛ وتحتفظ كل مسودة بالنتيجة المسجلة أولًا.",
    amendConfirm: "سجّل التعديل",
    amendCancel: "أبقِ قيمة البروتوكول",
    amended: "عُدِّل في {date} بواسطة {who}: {field}، من «{from}» إلى «{to}».",
    amendedStatus: "سُجِّل التعديل",
    advance: "بعد قراري",
    advanceDraft: "اعرض المسودة ثم N (الافتراضي)",
    advanceNow: "انتقل فورًا إلى التالي (تبقى المسودة في تفاصيل السجل)",
    advanceShown: "المسودات معروضة بجانب السجل أصلًا، لذا يُفتح السجل التالي فورًا دائمًا.",
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
  // H-screening-drafts: a method change waiting for its confirmation (nothing is sent before).
  const [pendingAmendment, setPendingAmendment] = useState<{ field: MethodAmendment["field"]; value: string } | null>(null);
  const [amendRefusal, setAmendRefusal] = useState<{ code: string; message: string } | null>(null);

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
        // Never sent when the protocol sets it (M7-method, spec 02 amendment).
        ...(settings.blinding_source === "protocol" ? {} : { blinding: draft.blinding }),
        mode: draft.mode,
        // Sent only when it changes, so saving other settings journals no no-op row (M6-beta).
        ...(draft.advance_on_decide && draft.advance_on_decide !== settings.advance_on_decide ? { advance_on_decide: draft.advance_on_decide } : {}),
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

  async function recordAmendment() {
    if (!pendingAmendment) return;
    setAmendRefusal(null);
    try {
      const { settings: next } = await amendMethod(origin, pendingAmendment);
      setSettings(next);
      // Only the method fields follow the engine; other unsaved choices stay as drafted.
      setDraft((d) => (d ? { ...d, blinding: next.blinding, not_reported_policy: next.not_reported_policy, method_amendments: next.method_amendments } : next));
      setPendingAmendment(null);
      setMessage(t("amendedStatus"));
    } catch (e) {
      setAmendRefusal(codeOf(e));
    }
  }

  // Follow the prepare job: a failed job must say so, not look like a slow one
  // (golden run, 2026-11-05). On success the batches are re-read.
  useEffect(() => {
    if (!job) return;
    let stopped = false;
    let timer: number | undefined;
    const tick = async () => {
      try {
        const view = await getJob(origin, job);
        if (stopped) return;
        setJobView(view);
        if (view.state === "queued" || view.state === "running") {
          timer = window.setTimeout(() => void tick(), 1000);
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
      window.clearTimeout(timer);
    };
  }, [job, origin, load]);

  async function runPrepare() {
    setConfirming(false);
    setRefusal(null);
    try {
      const started = await prepare(origin, size);
      notifyReviewChanged();
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
    // M7-method: the protocol's method block may set blinding and the not-reported policy;
    // H-screening-drafts: either can be changed after genesis, as a recorded amendment.
    const blindingFromProtocol = settings.blinding_source === "protocol";
    const policy: NotReportedPolicy = settings.not_reported_policy ?? "unclear";
    // M11b placeholder follow-up (decision item 8): a rule nobody chose is not shown as a choice.
    const ruleIsDefault = settings.not_reported_source === "defaults";
    const rules =
      policy === "exclude"
        ? (["ruleUnclearExcludePolicy", "ruleExcludeExcludePolicy", "ruleIncludeExcludePolicy"] as const)
        : policy === "decisive_first"
          ? (["ruleUnclearExcludePolicy", "ruleExcludeDecisive", "ruleIncludeDecisive"] as const)
          : (["ruleUnclear", "ruleExclude", "ruleInclude"] as const);
    const policyLabel: Record<NotReportedPolicy, PrepareCopyKey> = { unclear: "notReportedUnclear", decisive_first: "notReportedDecisive", exclude: "notReportedExclude" };
    const blindingLabel = (value: string) => t(value === "show" ? "blindingShow" : "blindingAfter");
    const fieldLabel = (field: string) => t(field === "blinding" ? "blinding" : "notReported");
    const valueLabel = (field: string, value: string) =>
      field === "blinding" ? blindingLabel(value) : value in policyLabel ? t(policyLabel[value as NotReportedPolicy]) : value;
    const amendments = settings.method_amendments ?? [];

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
                <li className="rounded-md bg-unclear-soft p-3 text-sm text-ink">{t(rules[0])}</li>
                <li className="rounded-md bg-exclude-soft p-3 text-sm text-ink">{t(rules[1])}</li>
                {/* Review F8: under decisive_first the last cell holds an Unclear rule too, so it is not green. */}
                <li className={`rounded-md p-3 text-sm text-ink ${policy === "decisive_first" ? "border border-rule bg-paper" : "bg-include-soft"}`}>{t(rules[2])}</li>
              </ol>
            </section>

            <section aria-labelledby="prepare-settings" className="rounded-lg border border-rule bg-leaf p-5">
              <h2 id="prepare-settings" className="font-semibold text-ink">
                {t("settings")}
              </h2>
              <fieldset className="mt-3" aria-describedby={blindingFromProtocol ? "blinding-protocol" : undefined}>
                <legend className="text-sm font-semibold text-ink">{t("blinding")}</legend>
                {blindingFromProtocol ? (
                  <p id="blinding-protocol" className="mt-1 text-sm text-ink-muted">
                    {t("setByProtocol")}
                  </p>
                ) : null}
                {(["reveal_after_decision", "show"] as const).map((value) => (
                  <label key={value} className="mt-2 flex min-h-11 items-center gap-2 text-ink">
                    <input
                      type="radio"
                      name="blinding"
                      checked={draft.blinding === value}
                      // H-screening-drafts: the protocol's value changes only through a confirmed
                      // amendment; until it is recorded the protocol's value stays selected.
                      onChange={() => {
                        if (!blindingFromProtocol) setDraft({ ...draft, blinding: value });
                        else if (value !== settings.blinding) setPendingAmendment({ field: "blinding", value });
                      }}
                    />
                    {value === "show" ? t("blindingShow") : t("blindingAfter")}
                  </label>
                ))}
              </fieldset>
              <fieldset className="mt-4" aria-describedby={ruleIsDefault ? "not-reported-note not-reported-default" : "not-reported-note"}>
                <legend className="text-sm font-semibold text-ink">{t("notReported")}</legend>
                <p id="not-reported-note" className="mt-1 text-sm text-ink-muted">
                  {t("notReportedNote")}
                </p>
                {ruleIsDefault ? (
                  <p id="not-reported-default" className="mt-1 text-sm text-ink">
                    {t("notReportedDefault")}
                  </p>
                ) : null}
                {(["unclear", "decisive_first", "exclude"] as const).map((value) => (
                  <label key={value} className="mt-2 flex min-h-11 items-center gap-2 text-ink">
                    <input
                      type="radio"
                      name="not_reported"
                      checked={policy === value}
                      onChange={() => {
                        if (value !== policy) setPendingAmendment({ field: "not_reported", value });
                      }}
                    />
                    {t(policyLabel[value])}
                  </label>
                ))}
              </fieldset>
              {pendingAmendment ? (
                <div
                  role="alertdialog"
                  aria-labelledby="amend-title"
                  aria-describedby="amend-body"
                  className="mt-4 rounded-md border border-brand p-4"
                  onKeyDown={(e) => e.key === "Escape" && setPendingAmendment(null)}
                >
                  <p id="amend-title" className="font-semibold text-ink">
                    {t("amendTitle")}
                  </p>
                  <p className="mt-1 text-sm text-ink">
                    {t("amendChange", {
                      field: fieldLabel(pendingAmendment.field),
                      from: valueLabel(pendingAmendment.field, pendingAmendment.field === "blinding" ? settings.blinding : policy),
                      to: valueLabel(pendingAmendment.field, pendingAmendment.value),
                    })}
                  </p>
                  <p id="amend-body" className="mt-1 text-sm text-ink-muted">
                    {t("amendBody")}
                  </p>
                  {pendingAmendment.field === "not_reported" ? <p className="mt-1 text-sm text-ink-muted">{t("amendDrafts")}</p> : null}
                  {amendRefusal ? (
                    <div className="mt-3">
                      <StateCard locale={locale} code={amendRefusal.code} message={amendRefusal.message} consoleOrigin={origin} />
                    </div>
                  ) : null}
                  <div className="mt-3 flex flex-wrap gap-2">
                    <Button variant="primary" autoFocus onClick={() => void recordAmendment()}>
                      {t("amendConfirm")}
                    </Button>
                    <Button
                      onClick={() => {
                        setPendingAmendment(null);
                        setAmendRefusal(null);
                      }}
                    >
                      {t("amendCancel")}
                    </Button>
                  </div>
                </div>
              ) : null}
              {amendments.length > 0 ? (
                <ul className="mt-3 space-y-1 text-sm text-ink-muted" data-amendments>
                  {amendments.map((a) => (
                    <li key={a.amendment_id}>
                      {t("amended", {
                        date: a.amended_at.slice(0, 10),
                        who: a.amended_by,
                        field: fieldLabel(a.field),
                        from: valueLabel(a.field, a.from),
                        to: valueLabel(a.field, a.to),
                      })}
                    </li>
                  ))}
                </ul>
              ) : null}
              <fieldset className="mt-4" disabled={draft.blinding === "show"} aria-describedby={draft.blinding === "show" ? "advance-shown" : undefined}>
                <legend className="text-sm font-semibold text-ink">{t("advance")}</legend>
                {draft.blinding === "show" ? (
                  <p id="advance-shown" className="mt-1 text-sm text-ink-muted">
                    {t("advanceShown")}
                  </p>
                ) : null}
                {(["show_draft_then_next", "next_at_once"] as const).map((value) => (
                  <label key={value} className="mt-2 flex min-h-11 items-center gap-2 text-ink">
                    <input
                      type="radio"
                      name="advance_on_decide"
                      checked={(draft.advance_on_decide ?? "show_draft_then_next") === value}
                      onChange={() => setDraft({ ...draft, advance_on_decide: value })}
                    />
                    {value === "next_at_once" ? t("advanceNow") : t("advanceDraft")}
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

            {batches.count > 0 ? <PilotCard locale={locale} origin={origin} /> : null}
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
                  // Review C round 1, finding 7: with batches, the pilot card holds the brand action (decision item 17).
                  <Button variant={batches.count > 0 ? "secondary" : "primary"} onClick={() => setConfirming(true)}>
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
