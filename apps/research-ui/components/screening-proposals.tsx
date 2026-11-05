"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { formatNumber, type Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge, GatePanel } from "@/components/ui/base";
import { ScreeningSteps, StateCard } from "@/components/screening-state-card";
import { isScreeningApiError } from "@/lib/screening-api";
import {
  cancelRun,
  estimateRun,
  getProposalSetup,
  getQueue,
  getRun,
  startCalibration,
  startRun,
  type ProposalSetup,
  type Provider,
  type RunEstimate,
  type RunRequest,
  type RunView,
} from "@/lib/screening-v1";

/**
 * Agent proposals run (spec 06): choose the provider, see what leaves this
 * machine and what it costs, consent, run, and watch it.
 *
 * Every gate is the engine's: consent, the key, the one-run lock and the cost
 * ceiling are checked by `POST /proposals/runs`; this screen only states them.
 * The key is never typed here (it is set in the engine's terminal and kept in
 * the OS keychain); the setup read names where a key is stored, never the key.
 * The screen shows no proposal content: drafts open in triage after you decide.
 */

const ANTHROPIC_MODELS = ["claude-opus-5-5", "claude-sonnet-5-5", "claude-haiku-5-5"] as const;
const PROVIDERS: Provider[] = ["anthropic", "openai_compatible", "gemini"];
const FINISHED = new Set(["completed", "stopped", "cancelled", "failed"]);
const POLL_MS = 2000;
const CALIBRATION_SIZE = 30;

const COPY = {
  en: {
    eyebrow: "Screening · agent proposals",
    title: "Which agent drafts the proposals, and what leaves this machine?",
    lede: "Optional. The agent drafts a proposal per record; you still decide every record. You can screen without any proposals at all.",
    loading: "Reading the run settings…",
    provider: "Provider",
    "provider.anthropic": "Anthropic",
    "provider.openai_compatible": "OpenAI-compatible endpoint",
    "provider.gemini": "Google Gemini",
    keyStored: "Key in the {source}",
    "keySource.keychain": "system keychain",
    "keySource.environment": "environment",
    keyNone: "No key set",
    keyNote: "The key stays in the engine. It is never written to the workspace or the journal, and the browser never sees it.",
    dataFlow: "What leaves this machine: {flow}.",
    mcp: "Using your own Claude instead? Run it from Claude over MCP (uv run scholar-agent); it submits drafts with the same checks and starts no run here.",
    settings: "Run settings",
    model: "Model",
    baseUrl: "Endpoint URL",
    effort: "Effort",
    promptHash: "Prompt",
    taskVersion: "Task version",
    records: "Records without a draft",
    estimate: "Cost estimate",
    estimateLoading: "Estimating…",
    cost: "About {cost}",
    costNone: "No price on file for this model",
    pricesAsOf: "prices as of {date}",
    pricing: "{mode} pricing",
    "pricing.batch": "Batch",
    "pricing.direct": "Direct-call",
    tokens: "{input} input and {output} output tokens",
    ceiling: "Cost ceiling (USD)",
    hardStop: "A hard stop: the run stops when its measured cost reaches the ceiling, and finished drafts are kept.",
    consent: "I consent to send the records above to {provider} for this run.",
    consentOnFile: "Consent on file since {date}.",
    calibration: "Check the agent on your labels first",
    calibrationBody: "Runs the agent on up to 30 records you have already decided and reports how many of your includes it would have missed. Advisory: it never blocks a run.",
    calibrationStart: "Check on {n} decided records",
    calibrationNone: "Decide some records first.",
    calibrationResult: "Include-recall {recall} (lower bound {low}) on {n} records.",
    calibrationMissed: "It would have missed {n} of your includes. Decide whether to trust it before a full run.",
    calibrationClean: "It missed none of your includes.",
    gate: "Run gate",
    gateBody: "Nothing leaves this machine until you start.",
    start: "Start agent proposals · {n} records",
    dryRun: "Dry run on 20 records",
    confirmTitle: "Send {n} records to {provider}?",
    confirmCeiling: "The run stops at {ceiling}.",
    confirmNoCeiling: "No cost ceiling is set.",
    confirm: "Start the run",
    back: "Back",
    whileItRuns: "While it runs",
    idle: "No run yet.",
    progress: "{done} of {records} proposed",
    costSoFar: "Cost so far: {cost}",
    counts: "{refused} refused · {truncated} cut off · {invalid} unreadable · {failed} failed · {checks} failed a check",
    countsNote: "Each of these is kept as an Unclear draft; no record is dropped.",
    "state.queued": "Queued",
    "state.running": "Running",
    "state.completed": "Completed",
    "state.stopped": "Stopped",
    "state.cancelled": "Cancelled",
    "state.failed": "Failed",
    cancel: "Cancel the run",
    partial: "The agent run stopped at {done} of {records}. {left} records have no draft. You can decide them without one.",
    resume: "Resume over the records without a draft",
    retention: "Proposals are kept in this workspace as provenance.",
    toTriage: "Open triage",
  },
  fr: {
    eyebrow: "Sélection · propositions de l'agent",
    title: "Quel agent rédige les propositions, et qu'est-ce qui quitte cette machine ?",
    lede: "Facultatif. L'agent rédige une proposition par notice ; vous décidez toujours chaque notice. Vous pouvez trier sans aucune proposition.",
    loading: "Lecture des réglages du passage…",
    provider: "Fournisseur",
    "provider.anthropic": "Anthropic",
    "provider.openai_compatible": "Point d'accès compatible OpenAI",
    "provider.gemini": "Google Gemini",
    keyStored: "Clé dans {source}",
    "keySource.keychain": "le trousseau du système",
    "keySource.environment": "l'environnement",
    keyNone: "Aucune clé définie",
    keyNote: "La clé reste dans le moteur. Elle n'est jamais écrite dans l'espace ni dans le journal, et le navigateur ne la voit jamais.",
    dataFlow: "Ce qui quitte cette machine : {flow}.",
    mcp: "Vous préférez votre propre Claude ? Lancez-le depuis Claude via MCP (uv run scholar-agent) ; il soumet ses brouillons avec les mêmes contrôles et ne lance aucun passage ici.",
    settings: "Réglages du passage",
    model: "Modèle",
    baseUrl: "URL du point d'accès",
    effort: "Effort",
    promptHash: "Consigne",
    taskVersion: "Version de la tâche",
    records: "Notices sans brouillon",
    estimate: "Estimation du coût",
    estimateLoading: "Estimation…",
    cost: "Environ {cost}",
    costNone: "Aucun prix enregistré pour ce modèle",
    pricesAsOf: "prix au {date}",
    pricing: "Tarif {mode}",
    "pricing.batch": "par lot",
    "pricing.direct": "par appel direct",
    tokens: "{input} jetons en entrée et {output} en sortie",
    ceiling: "Plafond de coût (USD)",
    hardStop: "Un arrêt ferme : le passage s'arrête quand son coût mesuré atteint le plafond, et les brouillons terminés sont conservés.",
    consent: "J'accepte d'envoyer les notices ci-dessus à {provider} pour ce passage.",
    consentOnFile: "Consentement enregistré depuis le {date}.",
    calibration: "Vérifier d'abord l'agent sur vos décisions",
    calibrationBody: "Fait passer l'agent sur jusqu'à 30 notices déjà décidées et indique combien de vos inclusions il aurait manquées. Indicatif : cela ne bloque jamais un passage.",
    calibrationStart: "Vérifier sur {n} notices décidées",
    calibrationNone: "Décidez d'abord quelques notices.",
    calibrationResult: "Rappel des inclusions {recall} (borne inférieure {low}) sur {n} notices.",
    calibrationMissed: "Il aurait manqué {n} de vos inclusions. Décidez si vous lui faites confiance avant un passage complet.",
    calibrationClean: "Il n'a manqué aucune de vos inclusions.",
    gate: "Lancement",
    gateBody: "Rien ne quitte cette machine avant que vous lanciez.",
    start: "Lancer les propositions · {n} notices",
    dryRun: "Essai sur 20 notices",
    confirmTitle: "Envoyer {n} notices à {provider} ?",
    confirmCeiling: "Le passage s'arrête à {ceiling}.",
    confirmNoCeiling: "Aucun plafond de coût n'est fixé.",
    confirm: "Lancer le passage",
    back: "Retour",
    whileItRuns: "Pendant le passage",
    idle: "Aucun passage pour l'instant.",
    progress: "{done} sur {records} proposées",
    costSoFar: "Coût à ce stade : {cost}",
    counts: "{refused} refusées · {truncated} tronquées · {invalid} illisibles · {failed} en échec · {checks} contrôles échoués",
    countsNote: "Chacune est conservée comme brouillon Incertain ; aucune notice n'est écartée.",
    "state.queued": "En attente",
    "state.running": "En cours",
    "state.completed": "Terminé",
    "state.stopped": "Arrêté",
    "state.cancelled": "Annulé",
    "state.failed": "Échoué",
    cancel: "Annuler le passage",
    partial: "Le passage de l'agent s'est arrêté à {done} sur {records}. {left} notices n'ont pas de brouillon. Vous pouvez les décider sans.",
    resume: "Reprendre sur les notices sans brouillon",
    retention: "Les propositions sont conservées dans cet espace comme provenance.",
    toTriage: "Ouvrir le tri",
  },
  ar: {
    eyebrow: "الفرز · مقترحات الوكيل",
    title: "أي وكيل يكتب المقترحات، وما الذي يغادر هذا الجهاز؟",
    lede: "اختياري. يكتب الوكيل مقترحًا لكل سجل، وتبقى أنت من يحسم كل سجل. يمكنك الفرز دون أي مقترحات.",
    loading: "جارٍ قراءة إعدادات التشغيل…",
    provider: "المزوّد",
    "provider.anthropic": "Anthropic",
    "provider.openai_compatible": "نقطة وصول متوافقة مع OpenAI",
    "provider.gemini": "Google Gemini",
    keyStored: "المفتاح في {source}",
    "keySource.keychain": "سلسلة مفاتيح النظام",
    "keySource.environment": "متغيرات البيئة",
    keyNone: "لم يُضبط مفتاح",
    keyNote: "يبقى المفتاح في المحرك. لا يُكتب أبدًا في المساحة ولا في السجل، ولا يراه المتصفح.",
    dataFlow: "ما يغادر هذا الجهاز: {flow}.",
    mcp: "تفضّل Claude الخاص بك؟ شغّله من Claude عبر MCP (uv run scholar-agent)؛ يرسل المسودات بالفحوص نفسها ولا يبدأ تشغيلًا هنا.",
    settings: "إعدادات التشغيل",
    model: "النموذج",
    baseUrl: "عنوان نقطة الوصول",
    effort: "الجهد",
    promptHash: "التعليمات",
    taskVersion: "إصدار المهمة",
    records: "سجلات دون مسودة",
    estimate: "تقدير التكلفة",
    estimateLoading: "جارٍ التقدير…",
    cost: "نحو {cost}",
    costNone: "لا سعر مسجّل لهذا النموذج",
    pricesAsOf: "الأسعار بتاريخ {date}",
    pricing: "تسعير {mode}",
    "pricing.batch": "الدفعات",
    "pricing.direct": "الاستدعاء المباشر",
    tokens: "{input} وحدة إدخال و{output} وحدة إخراج",
    ceiling: "سقف التكلفة (دولار)",
    hardStop: "توقف حتمي: يتوقف التشغيل حين تبلغ تكلفته المقيسة السقف، وتُحفظ المسودات المنجزة.",
    consent: "أوافق على إرسال السجلات أعلاه إلى {provider} في هذا التشغيل.",
    consentOnFile: "الموافقة مسجّلة منذ {date}.",
    calibration: "اختبر الوكيل على قراراتك أولًا",
    calibrationBody: "يشغّل الوكيل على ما يصل إلى 30 سجلًا حسمتها، ويبيّن كم من إدراجاتك كان سيفوته. إرشادي: لا يمنع أي تشغيل.",
    calibrationStart: "اختبر على {n} سجلًا محسومًا",
    calibrationNone: "احسم بعض السجلات أولًا.",
    calibrationResult: "استرجاع الإدراج {recall} (الحد الأدنى {low}) على {n} سجلًا.",
    calibrationMissed: "كان سيفوته {n} من إدراجاتك. قرّر هل تثق به قبل تشغيل كامل.",
    calibrationClean: "لم يفته أي من إدراجاتك.",
    gate: "بوابة التشغيل",
    gateBody: "لا يغادر شيء هذا الجهاز حتى تبدأ.",
    start: "ابدأ مقترحات الوكيل · {n} سجلًا",
    dryRun: "تجربة على 20 سجلًا",
    confirmTitle: "إرسال {n} سجلًا إلى {provider}؟",
    confirmCeiling: "يتوقف التشغيل عند {ceiling}.",
    confirmNoCeiling: "لم يُحدَّد سقف للتكلفة.",
    confirm: "ابدأ التشغيل",
    back: "رجوع",
    whileItRuns: "أثناء التشغيل",
    idle: "لا تشغيل بعد.",
    progress: "{done} من {records} مقترحة",
    costSoFar: "التكلفة حتى الآن: {cost}",
    counts: "{refused} مرفوضة · {truncated} مقطوعة · {invalid} غير مقروءة · {failed} فاشلة · {checks} أخفقت في فحص",
    countsNote: "تُحفظ كلٌّ منها مسودةً غير واضحة، ولا يُسقط أي سجل.",
    "state.queued": "في الانتظار",
    "state.running": "قيد التشغيل",
    "state.completed": "اكتمل",
    "state.stopped": "توقف",
    "state.cancelled": "أُلغي",
    "state.failed": "فشل",
    cancel: "ألغِ التشغيل",
    partial: "توقف تشغيل الوكيل عند {done} من {records}. {left} سجلًا دون مسودة. يمكنك حسمها دونها.",
    resume: "استأنف على السجلات التي بلا مسودة",
    retention: "تُحفظ المقترحات في هذه المساحة كمصدر موثّق.",
    toTriage: "فتح المراجعة",
  },
} as const satisfies Record<Locale, Record<string, string>>;

export type ProposalsCopyKey = keyof (typeof COPY)["en"];
export const PROPOSALS_COPY: Record<Locale, Record<ProposalsCopyKey, string>> = COPY;

function fill(template: string, values: Record<string, string | number> = {}): string {
  return template.replace(/\{(\w+)\}/g, (_, k: string) => {
    if (!(k in values)) throw new Error(`proposals copy needs {${k}}`);
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

function usd(locale: Locale, value: number): string {
  return new Intl.NumberFormat(locale === "ar" ? "ar-u-nu-latn" : locale, { style: "currency", currency: "USD", maximumFractionDigits: value < 1 ? 4 : 2 }).format(value);
}

type Loaded = { setup: ProposalSetup; decided: string[] };

export function ScreeningProposals({ locale }: Readonly<{ locale: Locale }>) {
  const t = useCallback((key: ProposalsCopyKey, values?: Record<string, string | number>) => fill(PROPOSALS_COPY[locale][key], values), [locale]);
  const n = useCallback((value: number) => formatNumber(locale, value), [locale]);
  const origin = useMemo(consoleOrigin, []);
  const [state, setState] = useState<{ status: "loading" } | { status: "ready"; data: Loaded } | { status: "error"; code: string; message: string }>({ status: "loading" });
  const [provider, setProvider] = useState<Provider>("anthropic");
  const [model, setModel] = useState<string>(ANTHROPIC_MODELS[0]);
  const [baseUrl, setBaseUrl] = useState("");
  const [ceiling, setCeiling] = useState("");
  const [consent, setConsent] = useState(false);
  const [estimate, setEstimate] = useState<RunEstimate | null>(null);
  const [confirming, setConfirming] = useState<null | { dryRun: boolean }>(null);
  const [run, setRun] = useState<RunView | null>(null);
  const [calibration, setCalibration] = useState<RunView | null>(null);
  const [refusal, setRefusal] = useState<{ code: string; message: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const polling = useRef<Record<string, boolean>>({});

  const load = useCallback(async () => {
    try {
      const [setup, decided] = await Promise.all([getProposalSetup(origin), getQueue(origin, { view: "decided", limit: CALIBRATION_SIZE })]);
      setState({ status: "ready", data: { setup, decided: decided.items.map((i) => i.study_id) } });
      setModel((m) => m || setup.task.model);
      if (setup.latest_run && setup.latest_run.kind !== "calibration") setRun(setup.latest_run);
    } catch (error) {
      setState({ status: "error", ...codeOf(error) });
    }
  }, [origin]);

  useEffect(() => {
    void load();
  }, [load]);

  const effort = state.status === "ready" ? state.data.setup.task.effort : "low";
  const request = useCallback(
    (extra: Partial<RunRequest> = {}): RunRequest => ({
      provider,
      model,
      effort,
      scope: { view: "no_proposal" },
      base_url: provider === "openai_compatible" ? baseUrl.trim() || null : null,
      cost_ceiling_usd: ceiling.trim() === "" ? null : Number(ceiling),
      ...extra,
    }),
    [provider, model, effort, baseUrl, ceiling],
  );

  // The estimate follows the provider and model; it sends nothing to a provider.
  useEffect(() => {
    if (state.status !== "ready" || !model.trim()) return;
    let live = true;
    setEstimate(null);
    estimateRun(origin, { ...request(), cost_ceiling_usd: null })
      .then((e) => live && setEstimate(e))
      .catch((error: unknown) => live && setRefusal(codeOf(error)));
    return () => {
      live = false;
    };
    // The ceiling does not change an estimate; `request` is rebuilt on every keystroke.
  }, [origin, state.status, provider, model, baseUrl]);

  const poll = useCallback(
    (runId: string, onView: (view: RunView) => void) => {
      if (polling.current[runId]) return;
      polling.current[runId] = true;
      const tick = async () => {
        try {
          const view = await getRun(origin, runId);
          onView(view);
          if (FINISHED.has(view.state)) {
            polling.current[runId] = false;
            return;
          }
        } catch (error) {
          setRefusal(codeOf(error));
          polling.current[runId] = false;
          return;
        }
        window.setTimeout(() => void tick(), POLL_MS);
      };
      void tick();
    },
    [origin],
  );

  useEffect(() => {
    if (run && !FINISHED.has(run.state)) poll(run.run_id, setRun);
  }, [run, poll]);

  useEffect(() => {
    if (!confirming) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setConfirming(null);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [confirming]);

  async function act(work: () => Promise<void>) {
    setBusy(true);
    setRefusal(null);
    try {
      await work();
    } catch (error) {
      setRefusal(codeOf(error));
    } finally {
      setBusy(false);
    }
  }

  const begin = (dryRun: boolean) =>
    act(async () => {
      setConfirming(null);
      const consentBody = consent ? { provider, accepted_at: new Date().toISOString() } : undefined;
      const started = await startRun(origin, request({ dry_run: dryRun, consent: consentBody }));
      const view = await getRun(origin, started.run_id);
      setRun(view);
      setConsent(false);
      await load();
    });

  const calibrate = (ids: string[]) =>
    act(async () => {
      const started = await startCalibration(origin, { study_ids: ids, provider, model, effort, cost_ceiling_usd: request().cost_ceiling_usd });
      poll(started.run_id, setCalibration);
    });

  const body = (() => {
    if (state.status === "loading") return <p className="text-ink-muted" role="status">{t("loading")}</p>;
    if (state.status === "error") return <StateCard locale={locale} code={state.code} message={state.message} consoleOrigin={origin} onRetry={() => void load()} />;
    const { setup, decided } = state.data;
    const chosen = setup.providers.find((p) => p.provider === provider);
    const keyMissing = chosen?.key === "none";
    const consentOnFile = chosen?.consent ?? null;
    const records = estimate?.records ?? 0;
    const active = run !== null && !FINISHED.has(run.state);
    const ready = !keyMissing && !active && !busy && model.trim() !== "" && (consent || consentOnFile !== null) && (provider !== "openai_compatible" || baseUrl.trim() !== "");
    const ceilingValue = request().cost_ceiling_usd;
    const providerName = t(`provider.${provider}` as ProposalsCopyKey);

    return (
      <div className="space-y-6">
        <header>
          <p className="text-xs font-semibold uppercase tracking-[0.05em] text-brand rtl:tracking-normal">{t("eyebrow")}</p>
          <h1 className="font-display mt-1 text-[1.75rem] leading-[2.25rem] text-ink">{t("title")}</h1>
          <p className="mt-2 max-w-prose text-ink-muted">{t("lede")}</p>
        </header>

        {refusal ? (
          <StateCard
            locale={locale}
            code={refusal.code}
            message={refusal.message}
            consoleOrigin={origin}
            command={refusal.code === "PROVIDER_KEY_MISSING" ? `uv run nexus-scholar keys set ${provider}` : undefined}
          />
        ) : null}

        <div className="flex flex-wrap gap-6">
          <div className="min-w-0 flex-[999_1_480px] space-y-6">
            <fieldset className="rounded-lg border border-rule bg-leaf p-5">
              <legend className="px-1 font-semibold text-ink">{t("provider")}</legend>
              <div className="mt-2 space-y-2">
                {setup.providers.map((p) => (
                  <label key={p.provider} className="flex min-h-11 flex-wrap items-center gap-3 rounded-md border border-rule px-3 py-2" data-provider={p.provider}>
                    <input
                      type="radio"
                      name="provider"
                      value={p.provider}
                      checked={provider === p.provider}
                      onChange={() => {
                        setProvider(p.provider);
                        setModel(p.provider === "anthropic" ? ANTHROPIC_MODELS[0] : "");
                        setConsent(false);
                        setRefusal(null);
                      }}
                    />
                    <span className="text-ink">{t(`provider.${p.provider}` as ProposalsCopyKey)}</span>
                    {p.key === "none" ? (
                      <DecisionBadge role="blocked">{t("keyNone")}</DecisionBadge>
                    ) : (
                      <DecisionBadge role="include">{t("keyStored", { source: t(`keySource.${p.key}` as ProposalsCopyKey) })}</DecisionBadge>
                    )}
                  </label>
                ))}
              </div>
              <p className="mt-3 text-sm text-ink-muted">{t("keyNote")}</p>
              {keyMissing ? (
                <div className="mt-3">
                  <StateCard locale={locale} code="PROVIDER_KEY_MISSING" consoleOrigin={origin} command={`uv run nexus-scholar keys set ${provider}`} />
                </div>
              ) : null}
              <p className="mt-3 text-sm text-ink" data-flow>
                {t("dataFlow", { flow: setup.data_flow })}
              </p>
              <p className="mt-2 text-sm text-ink-muted">{t("mcp")}</p>
            </fieldset>

            <section aria-labelledby="run-settings" className="rounded-lg border border-rule bg-leaf p-5">
              <h2 id="run-settings" className="font-semibold text-ink">
                {t("settings")}
              </h2>
              <div className="mt-3 space-y-3 text-sm">
                <label className="block text-ink">
                  {t("model")}
                  {provider === "anthropic" ? (
                    <select value={model} onChange={(e) => setModel(e.target.value)} className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink" dir="ltr">
                      {ANTHROPIC_MODELS.map((m) => (
                        <option key={m} value={m}>
                          {m}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input type="text" value={model} onChange={(e) => setModel(e.target.value)} spellCheck={false} dir="ltr" className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 font-mono text-ink" />
                  )}
                </label>
                {provider === "openai_compatible" ? (
                  <label className="block text-ink">
                    {t("baseUrl")}
                    <input type="url" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} spellCheck={false} dir="ltr" className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 font-mono text-ink" />
                  </label>
                ) : null}
                <dl className="grid grid-cols-[auto_1fr] gap-x-4 gap-y-1">
                  <dt className="text-ink-muted">{t("effort")}</dt>
                  <dd><DataCell>{effort}</DataCell></dd>
                  <dt className="text-ink-muted">{t("taskVersion")}</dt>
                  <dd><DataCell>{setup.task.task_version}</DataCell></dd>
                  <dt className="text-ink-muted">{t("promptHash")}</dt>
                  <dd><bdi dir="ltr"><DataCell>{setup.task.prompt_sha256}</DataCell></bdi></dd>
                  <dt className="text-ink-muted">{t("records")}</dt>
                  <dd className="text-ink">{estimate ? n(records) : "…"}</dd>
                </dl>
              </div>
            </section>

            <section aria-labelledby="run-estimate" className="rounded-lg border border-rule bg-leaf p-5">
              <h2 id="run-estimate" className="font-semibold text-ink">
                {t("estimate")}
              </h2>
              {estimate ? (
                <div className="mt-2 space-y-1 text-sm" data-estimate>
                  <p className="text-ink">
                    {estimate.cost_usd !== null ? t("cost", { cost: usd(locale, estimate.cost_usd) }) : t("costNone")}{" "}
                    <span className="text-ink-muted">· {t("pricesAsOf", { date: estimate.prices_as_of })} · {t("pricing", { mode: t(estimate.batch ? "pricing.batch" : "pricing.direct") })}</span>
                  </p>
                  <p className="text-ink-muted">{t("tokens", { input: n(estimate.tokens.input_tokens), output: n(estimate.tokens.output_tokens) })}</p>
                </div>
              ) : (
                <p className="mt-2 text-sm text-ink-muted" role="status">{t("estimateLoading")}</p>
              )}
              <label className="mt-4 block text-sm text-ink">
                {t("ceiling")}
                <input type="number" min="0" step="0.01" inputMode="decimal" value={ceiling} onChange={(e) => setCeiling(e.target.value)} dir="ltr" className="mt-1 block min-h-11 w-40 rounded-md border border-rule bg-paper px-2 text-ink" />
              </label>
              <p className="mt-1 text-xs text-ink-muted">{t("hardStop")}</p>
            </section>

            <section aria-labelledby="run-calibration" className="rounded-lg border border-rule bg-leaf p-5">
              <h2 id="run-calibration" className="font-semibold text-ink">
                {t("calibration")}
              </h2>
              <p className="mt-1 text-sm text-ink-muted">{t("calibrationBody")}</p>
              {decided.length === 0 ? (
                <p className="mt-3 text-sm text-ink">{t("calibrationNone")}</p>
              ) : (
                <div className="mt-3">
                  <Button disabled={busy || keyMissing || active || consentOnFile === null || (calibration !== null && !FINISHED.has(calibration.state))} onClick={() => void calibrate(decided)}>
                    {t("calibrationStart", { n: n(decided.length) })}
                  </Button>
                </div>
              )}
              {calibration?.calibration ? (
                <div className="mt-3 space-y-1 text-sm" data-calibration>
                  <p className="text-ink">
                    {t("calibrationResult", {
                      recall: calibration.calibration.include_recall === null ? "—" : n(calibration.calibration.include_recall),
                      low: calibration.calibration.ci_low === null ? "—" : n(calibration.calibration.ci_low),
                      n: n(calibration.calibration.compared),
                    })}
                  </p>
                  {calibration.calibration.missed_includes.length > 0 ? (
                    <p className="rounded-md bg-unclear-soft px-3 py-2 text-unclear" role="status">
                      {t("calibrationMissed", { n: n(calibration.calibration.missed_includes.length) })}
                    </p>
                  ) : (
                    <p className="text-include">{t("calibrationClean")}</p>
                  )}
                </div>
              ) : calibration ? (
                <p className="mt-3 text-sm text-ink-muted" role="status">
                  {t(`state.${calibration.state}` as ProposalsCopyKey)} · {t("progress", { done: n(calibration.done), records: n(calibration.records) })}
                </p>
              ) : null}
            </section>
          </div>

          <div className="w-full flex-[1_1_320px] space-y-6">
            <section aria-labelledby="run-progress" className="rounded-lg border border-rule bg-leaf p-5" data-run={run?.run_id ?? ""}>
              <h2 id="run-progress" className="font-semibold text-ink">
                {t("whileItRuns")}
              </h2>
              {run ? (
                <div className="mt-2 space-y-2 text-sm">
                  <p className="flex flex-wrap items-center gap-2">
                    <DecisionBadge role={run.state === "completed" ? "include" : run.state === "failed" ? "blocked" : "unclear"}>{t(`state.${run.state}` as ProposalsCopyKey)}</DecisionBadge>
                    <DataCell>{run.run_id}</DataCell>
                  </p>
                  <p className="text-ink">{t("progress", { done: n(run.done), records: n(run.records) })}</p>
                  <div role="img" aria-label={t("progress", { done: n(run.done), records: n(run.records) })} className="h-2 w-full overflow-hidden rounded-full bg-paper">
                    <div className="h-full bg-brand" style={{ width: `${run.records ? Math.round((100 * run.done) / run.records) : 0}%` }} />
                  </div>
                  <p className="text-ink-muted">
                    {t("costSoFar", { cost: usd(locale, run.cost_so_far) })}
                    {run.cost_ceiling_usd !== null ? ` / ${usd(locale, run.cost_ceiling_usd)}` : ""}
                  </p>
                  <p className="text-ink-muted">
                    {t("counts", { refused: n(run.refused), truncated: n(run.truncated), invalid: n(run.invalid), failed: n(run.failed), checks: n(run.check_failures) })}
                  </p>
                  <p className="text-xs text-ink-muted">{t("countsNote")}</p>
                  {active ? (
                    <Button disabled={busy} onClick={() => void act(async () => setRun({ ...run, ...(await cancelRun(origin, run.run_id)) }))}>
                      {t("cancel")}
                    </Button>
                  ) : null}
                  {run.code ? <StateCard locale={locale} code={run.code} consoleOrigin={origin} /> : null}
                  {!active && run.done < run.records ? (
                    <p className="rounded-md bg-unclear-soft px-3 py-2 text-unclear" data-partial>
                      {t("partial", { done: n(run.done), records: n(run.records), left: n(run.records - run.done) })}
                    </p>
                  ) : null}
                  <a className="inline-block text-brand underline" href={`/${locale}/screening/triage${origin ? `?console=${encodeURIComponent(origin)}` : ""}`}>
                    {t("toTriage")}
                  </a>
                </div>
              ) : (
                <p className="mt-2 text-sm text-ink-muted">{t("idle")}</p>
              )}
            </section>

            <GatePanel
              label={t("gate")}
              actions={
                <>
                  <Button variant="primary" disabled={!ready || records === 0} onClick={() => setConfirming({ dryRun: false })}>
                    {run && !active && run.done < run.records ? t("resume") : t("start", { n: n(records) })}
                  </Button>
                  <Button disabled={!ready || records === 0} onClick={() => setConfirming({ dryRun: true })}>
                    {t("dryRun")}
                  </Button>
                </>
              }
            >
              <p>{t("gateBody")}</p>
              {consentOnFile ? (
                <p className="mt-2 text-sm text-ink-muted">{t("consentOnFile", { date: new Date(consentOnFile.accepted_at).toLocaleDateString(locale) })}</p>
              ) : (
                <label className="mt-3 flex items-start gap-2 text-sm">
                  <input type="checkbox" checked={consent} onChange={(e) => setConsent(e.target.checked)} className="mt-1" />
                  <span>{t("consent", { provider: providerName })}</span>
                </label>
              )}
              <p className="mt-2 text-xs text-ink-muted">{t("retention")}</p>
            </GatePanel>

            {confirming ? (
              <div role="dialog" aria-modal="true" aria-labelledby="run-confirm" className="rounded-lg border border-brand bg-leaf p-5">
                <h2 id="run-confirm" className="font-semibold text-ink">
                  {t("confirmTitle", { n: n(confirming.dryRun ? Math.min(20, records) : records), provider: providerName })}
                </h2>
                <p className="mt-2 text-sm text-ink">{t("dataFlow", { flow: setup.data_flow })}</p>
                <p className="mt-1 text-sm text-ink-muted">{typeof ceilingValue === "number" ? t("confirmCeiling", { ceiling: usd(locale, ceilingValue) }) : t("confirmNoCeiling")}</p>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Button variant="primary" autoFocus disabled={busy} onClick={() => void begin(confirming.dryRun)}>
                    {t("confirm")}
                  </Button>
                  <Button onClick={() => setConfirming(null)}>{t("back")}</Button>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </div>
    );
  })();

  return (
    <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8 lg:py-14">
      <ScreeningSteps locale={locale} current="proposals" consoleOrigin={origin} />
      {body}
    </div>
  );
}
