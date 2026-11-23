"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { formatNumber, type Locale } from "@/i18n";
import { LoadingFrame } from "@/components/loading-frame";
import { Button, DataCell, DecisionBadge, GatePanel } from "@/components/ui/base";
import { DETAILS_LABEL } from "@/components/screening-state-card";
import { adoptedHref, ScreeningSteps, StateCard, exportHref, stepHref } from "@/components/screening-state-card";
import { adoptionText } from "@/lib/adoption-copy";
import { notifyReviewChanged } from "@/components/review-bus";
import {
  getBatchReviews,
  getPublicationStatus,
  getScreeningBatches,
  isScreeningApiError,
  postDeferBatch,
  postPairingRedeem,
  postPairingRedeemAll,
  postPublishScreening,
  type RedeemAllResult,
  type PublishResult,
  type ReviewState,
  type ScreeningBatches,
} from "@/lib/screening-api";
import {
  beginApproval,
  beginApprovalAll,
  getApprover,
  getPrismaPreview,
  getSettings,
  putApprover,
  type Approver,
  type PairingBegun,
  type PairingBegunAll,
  type PrismaPreview,
} from "@/lib/screening-v1";

/**
 * Publish (spec 09): the PRISMA screening preview with its checks, one
 * approval per batch with the code the engine shows on this computer (its
 * terminal, and its desktop window when the app has one; never sent over
 * HTTP, decision 2026-11-04), then the gated publish. Phone pairing by QR is
 * M2. Finding 38: one action stages the codes of every decided batch and one
 * paste redeems them; the per-batch controls are folded below it.
 *
 * Every gate is the engine's: Publish is offered only when every preview check
 * passes, and the publish call itself still runs collect's own gates
 * (`PROJECTION_STALE`, coverage, approval). The typed code is held in memory
 * for the one request and never stored.
 */

const COPY = {
  en: {
    eyebrow: "Screening · publish",
    title: "Approve each batch, then publish the screening.",
    titleBlocked: "Publishing waits until every check passes.",
    live: "Live data from this workspace's screening engine",
    exportLink: "Export and methods",
    loading: "Reading the preview…",
    prisma: "PRISMA 2020 screening preview",
    prismaScr: "PRISMA-ScR screening preview",
    prismaNone: "Screening preview",
    preview: "Preview · not written",
    identified: "Records identified",
    duplicates: "Duplicates removed",
    screened: "Records screened",
    excluded: "Excluded",
    unclear: "Unclear → full text",
    unclearNote: "Unclear records go on to full text; they are never excluded by default.",
    included: "Included",
    notYet: "Not yet decided",
    reason: "Reason",
    count: "Records",
    checks: "Checks",
    "check.human_provenance": "Every decision is recorded as the reviewer's",
    "check.adopted_decisions_declared": "Decisions stored from drafts are declared",
    look: "Look at this",
    "check.no_open_conflicts": "No open conflicts between devices",
    "check.bound_to_current_protocol": "Decisions are bound to the current protocol",
    "check.every_record_decided": "Every record is decided",
    "check.projections_current": "Every decisions file matches the decision log",
    pass: "Passes",
    fail: "Fails",
    batches: "Approval",
    batchesBody: "Approval needs one-time codes that appear only on this computer: in a Nexus Scholar window on the desktop when the app opened one, and always in the engine's terminal. Each code approves one batch, once. A decision changed after approval makes the approval stale.",
    bulkReady: "Batches fully decided and not approved yet: {ready} of {total}.",
    bulkAsk: "Show the codes for every decided batch",
    bulkShownDesktop: "The codes (batches: {n}) are in a Nexus Scholar window on this computer's desktop, and in the engine's terminal. They expire at {time}.",
    bulkShownTerminal: "The codes (batches: {n}) are printed in the engine's terminal. They expire at {time}.",
    bulkSkipped: "Left out: {approved} already approved, {deferred} deferred, {undecided} not fully decided.",
    bulkLabel: "Paste the codes (the lines that read “batch n: code”)",
    bulkApprove: "Approve the batches",
    bulkWorking: "Approving the batches… with many batches this takes up to a minute.",
    bulkPreparing: "Preparing the codes… with many batches this takes up to a minute.",
    bulkDone: "Batches approved: {n}.",
    bulkRefused: "Not approved: {batch} ({code}). Show the codes again for it.",
    bulkSkippedOther: "No code for {batches}.",
    oneByOne: "Approve one batch at a time",
    approved: "Approval on file",
    approvedNote: "A decision changed after this approval makes it stale; approve again. Publish refuses a stale approval.",
    notApproved: "Not approved",
    deferred: "Deferred",
    askCode: "Show a code for {batch}",
    codeShown: "Code printed in the terminal; it expires at {time}.",
    codeShownDesktop: "Code shown in a Nexus Scholar window on this desktop and in the terminal; it expires at {time}.",
    codeLabel: "Approval code for {batch}",
    approve: "Approve {batch}",
    defer: "Defer",
    deferReason: "Reason for deferring {batch}",
    deferSave: "Record the deferral",
    publish: "Publish the screening",
    publishGate: "Publish",
    publishBody: "Writes the kept studies (Include and Unclear), the excluded records and the PRISMA report for the approved generation. Full texts are handled on the Charting step.",
    publishBodyNone: "Writes the kept studies (Include and Unclear), the excluded records and the screening counts report for the approved generation. Full texts are handled on the Charting step.",
    published: "Published generation {id}",
    publishedPlain: "Published",
    batchN: "batch {n}",
    publishedStale: "Decisions changed after this was published ({n} studies). Approve and publish again.",
    toTriage: "Open triage",
    approverTitle: "Approver",
    approverBody: "Approvals are recorded under this name. It is a name typed on this computer, not a verified sign-in.",
    approverCurrent: "Approvals are recorded as {name}.",
    approverNone: "No name yet. Approving a batch needs your name first.",
    approverLabel: "Your name",
    approverSave: "Save name",
    approverSaved: "Name saved.",
  },
  fr: {
    eyebrow: "Sélection · publication",
    title: "Approuvez chaque lot, puis publiez la sélection.",
    titleBlocked: "La publication attend que tous les contrôles soient satisfaits.",
    live: "Données en direct du moteur de sélection de cet espace",
    exportLink: "Export et méthodes",
    loading: "Lecture de l'aperçu…",
    prisma: "Aperçu de sélection PRISMA 2020",
    prismaScr: "Aperçu de sélection PRISMA-ScR",
    prismaNone: "Aperçu de sélection",
    preview: "Aperçu · non écrit",
    identified: "Notices identifiées",
    duplicates: "Doublons retirés",
    screened: "Notices examinées",
    excluded: "Exclues",
    unclear: "Incertain → texte intégral",
    unclearNote: "Les notices incertaines passent au texte intégral ; elles ne sont jamais exclues par défaut.",
    included: "Incluses",
    notYet: "Pas encore décidées",
    reason: "Motif",
    count: "Notices",
    checks: "Contrôles",
    "check.human_provenance": "Chaque décision est enregistrée comme celle de l'évaluateur",
    "check.adopted_decisions_declared": "Les décisions enregistrées depuis les brouillons sont déclarées",
    look: "À examiner",
    "check.no_open_conflicts": "Aucun conflit ouvert entre appareils",
    "check.bound_to_current_protocol": "Les décisions sont liées au protocole actuel",
    "check.every_record_decided": "Chaque notice est décidée",
    "check.projections_current": "Chaque fichier de décisions correspond au journal",
    pass: "Satisfait",
    fail: "Échoue",
    batches: "Approbation",
    batchesBody: "L'approbation exige des codes à usage unique qui n'apparaissent que sur cet ordinateur : dans une fenêtre Nexus Scholar sur le bureau quand l'application en a ouvert une, et toujours dans le terminal du moteur. Chaque code approuve un lot, une seule fois. Une décision modifiée après approbation rend l'approbation périmée.",
    bulkReady: "Lots entièrement décidés et pas encore approuvés : {ready} sur {total}.",
    bulkAsk: "Afficher les codes de tous les lots décidés",
    bulkShownDesktop: "Les codes (lots : {n}) sont dans une fenêtre Nexus Scholar sur le bureau de cet ordinateur, et dans le terminal du moteur. Ils expirent à {time}.",
    bulkShownTerminal: "Les codes (lots : {n}) sont affichés dans le terminal du moteur. Ils expirent à {time}.",
    bulkSkipped: "Laissés de côté : {approved} déjà approuvés, {deferred} reportés, {undecided} pas entièrement décidés.",
    bulkLabel: "Collez les codes (les lignes « batch n: code »)",
    bulkApprove: "Approuver les lots",
    bulkWorking: "Approbation des lots… avec beaucoup de lots, cela prend jusqu'à une minute.",
    bulkPreparing: "Préparation des codes… avec beaucoup de lots, cela prend jusqu'à une minute.",
    bulkDone: "Lots approuvés : {n}.",
    bulkRefused: "Non approuvé : {batch} ({code}). Affichez de nouveau les codes pour ce lot.",
    bulkSkippedOther: "Pas de code pour {batches}.",
    oneByOne: "Approuver un lot à la fois",
    approved: "Approbation enregistrée",
    approvedNote: "Une décision modifiée après cette approbation la rend périmée ; approuvez à nouveau. La publication refuse une approbation périmée.",
    notApproved: "Non approuvé",
    deferred: "Reporté",
    askCode: "Afficher un code pour {batch}",
    codeShown: "Code affiché dans le terminal ; il expire à {time}.",
    codeShownDesktop: "Code affiché dans une fenêtre Nexus Scholar sur ce bureau et dans le terminal ; il expire à {time}.",
    codeLabel: "Code d'approbation pour {batch}",
    approve: "Approuver {batch}",
    defer: "Reporter",
    deferReason: "Motif du report de {batch}",
    deferSave: "Enregistrer le report",
    publish: "Publier la sélection",
    publishGate: "Publication",
    publishBody: "Écrit les études retenues (Inclure et Incertain), les notices exclues et le rapport PRISMA de la génération approuvée. Les textes intégraux se traitent à l'étape Extraction.",
    publishBodyNone: "Écrit les études retenues (Inclure et Incertain), les notices exclues et le rapport des effectifs de la sélection de la génération approuvée. Les textes intégraux se traitent à l'étape Extraction.",
    published: "Génération publiée {id}",
    publishedPlain: "Publiée",
    batchN: "lot {n}",
    publishedStale: "Des décisions ont changé après la publication ({n} études). Approuvez et publiez de nouveau.",
    toTriage: "Ouvrir le tri",
    approverTitle: "Approbateur",
    approverBody: "Les approbations sont enregistrées sous ce nom. C'est un nom saisi sur cet ordinateur, pas une connexion vérifiée.",
    approverCurrent: "Les approbations sont enregistrées au nom de {name}.",
    approverNone: "Aucun nom pour l'instant. Approuver un lot exige d'abord votre nom.",
    approverLabel: "Votre nom",
    approverSave: "Enregistrer le nom",
    approverSaved: "Nom enregistré.",
  },
  ar: {
    eyebrow: "الفرز · النشر",
    title: "اعتمد كل دفعة، ثم انشر نتائج الفرز.",
    titleBlocked: "ينتظر النشر حتى تنجح كل الفحوص.",
    live: "بيانات حية من محرك الفرز لهذه المساحة",
    exportLink: "التصدير والمنهجية",
    loading: "جارٍ قراءة المعاينة…",
    prisma: "معاينة فرز PRISMA 2020",
    prismaScr: "معاينة فرز PRISMA-ScR",
    prismaNone: "معاينة الفرز",
    preview: "معاينة · لم تُكتب",
    identified: "السجلات المحددة",
    duplicates: "المكررات المحذوفة",
    screened: "السجلات المفروزة",
    excluded: "المستبعدة",
    unclear: "غير واضح ← النص الكامل",
    unclearNote: "تُحال السجلات غير الواضحة إلى النص الكامل، ولا تُستبعد افتراضيًا أبدًا.",
    included: "المُدرجة",
    notYet: "لم تُحسم بعد",
    reason: "السبب",
    count: "السجلات",
    checks: "الفحوص",
    "check.human_provenance": "كل قرار مسجَّل على أنه قرار المراجع",
    "check.adopted_decisions_declared": "القرارات المحفوظة من المسودات مصرَّح بها",
    look: "انظر في هذا",
    "check.no_open_conflicts": "لا تعارضات مفتوحة بين الأجهزة",
    "check.bound_to_current_protocol": "القرارات مرتبطة بالبروتوكول الحالي",
    "check.every_record_decided": "حُسم كل سجل",
    "check.projections_current": "كل ملف قرارات مطابق للسجل",
    pass: "ناجح",
    fail: "فاشل",
    batches: "الاعتماد",
    batchesBody: "يحتاج الاعتماد إلى رموز لمرة واحدة لا تظهر إلا على هذا الحاسوب: في نافذة Nexus Scholar على سطح المكتب إن فتحها التطبيق، ودائمًا في طرفية المحرك. كل رمز يعتمد دفعة واحدة مرة واحدة. أي قرار يتغيّر بعد الاعتماد يجعل الاعتماد قديمًا.",
    bulkReady: "الدفعات المحسومة بالكامل وغير المعتمدة بعد: {ready} من {total}.",
    bulkAsk: "عرض الرموز لكل الدفعات المحسومة",
    bulkShownDesktop: "الرموز (عدد الدفعات: {n}) في نافذة Nexus Scholar على سطح مكتب هذا الحاسوب، وفي طرفية المحرك. تنتهي صلاحيتها في {time}.",
    bulkShownTerminal: "طُبعت الرموز (عدد الدفعات: {n}) في طرفية المحرك. تنتهي صلاحيتها في {time}.",
    bulkSkipped: "تُركت جانبًا: {approved} معتمدة من قبل، {deferred} مؤجلة، {undecided} غير محسومة بالكامل.",
    bulkLabel: "الصق الرموز (الأسطر التي تبدأ بـ «batch n: code»)",
    bulkApprove: "اعتماد الدفعات",
    bulkWorking: "جارٍ اعتماد الدفعات… مع دفعات كثيرة قد يستغرق ذلك دقيقة.",
    bulkPreparing: "جارٍ تحضير الرموز… مع دفعات كثيرة قد يستغرق ذلك دقيقة.",
    bulkDone: "الدفعات المعتمدة: {n}.",
    bulkRefused: "لم تُعتمد: {batch} ({code}). اعرض الرموز من جديد لها.",
    bulkSkippedOther: "لا رمز لـ{batches}.",
    oneByOne: "اعتماد دفعة واحدة في كل مرة",
    approved: "اعتماد مسجّل",
    approvedNote: "أي قرار يتغيّر بعد هذا الاعتماد يجعله قديمًا؛ اعتمد من جديد. يرفض النشر الاعتماد القديم.",
    notApproved: "غير معتمدة",
    deferred: "مؤجلة",
    askCode: "عرض رمز لـ{batch}",
    codeShown: "طُبع الرمز في الطرفية؛ تنتهي صلاحيته في {time}.",
    codeShownDesktop: "ظهر الرمز في نافذة Nexus Scholar على سطح المكتب وفي الطرفية؛ تنتهي صلاحيته في {time}.",
    codeLabel: "رمز اعتماد {batch}",
    approve: "اعتماد {batch}",
    defer: "تأجيل",
    deferReason: "سبب تأجيل {batch}",
    deferSave: "تسجيل التأجيل",
    publish: "نشر نتائج الفرز",
    publishGate: "النشر",
    publishBody: "يكتب الدراسات المُبقاة (مُدرجة وغير واضحة) والسجلات المستبعدة وتقرير PRISMA للجيل المعتمد. تُعالَج النصوص الكاملة في خطوة استخراج البيانات.",
    publishBodyNone: "يكتب الدراسات المُبقاة (مُدرجة وغير واضحة) والسجلات المستبعدة وتقرير أعداد الفرز للجيل المعتمد. تُعالَج النصوص الكاملة في خطوة استخراج البيانات.",
    published: "نُشر الجيل {id}",
    publishedPlain: "نُشر",
    batchN: "الدفعة {n}",
    publishedStale: "تغيّرت قرارات بعد النشر ({n} دراسة). اعتمد وانشر مجددًا.",
    toTriage: "فتح المراجعة",
    approverTitle: "المعتمِد",
    approverBody: "تُسجَّل الاعتمادات بهذا الاسم. إنه اسم مكتوب على هذا الحاسوب، وليس تسجيل دخول موثّقًا.",
    approverCurrent: "تُسجَّل الاعتمادات باسم {name}.",
    approverNone: "لا يوجد اسم بعد. يحتاج اعتماد أي دفعة إلى اسمك أولًا.",
    approverLabel: "اسمك",
    approverSave: "حفظ الاسم",
    approverSaved: "حُفظ الاسم.",
  },
} as const satisfies Record<Locale, Record<string, string>>;

export type PublishCopyKey = keyof (typeof COPY)["en"];
export const PUBLISH_COPY: Record<Locale, Record<PublishCopyKey, string>> = COPY;

/** The skip reasons the summary line counts; any other is the engine's refusal, named per batch. */
const SKIP_KINDS: ReadonlySet<string> = new Set(["ALREADY_APPROVED", "DEFERRED", "NOT_DECIDED"]);

function fill(template: string, values: Record<string, string | number> = {}): string {
  return template.replace(/\{(\w+)\}/g, (_, k: string) => {
    if (!(k in values)) throw new Error(`publish copy needs {${k}}`);
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

type Loaded = {
  preview: PrismaPreview;
  batches: ScreeningBatches;
  reviews: Record<number, ReviewState>;
  current: boolean;
  staleChanged: number | null;
  approver: Approver;
  /** The reporting guideline in force (M7b-guideline); an engine without it reads as PRISMA 2020. */
  reporting: string;
};

export function ScreeningPublish({ locale }: Readonly<{ locale: Locale }>) {
  const t = useCallback((key: PublishCopyKey, values?: Record<string, string | number>) => fill(PUBLISH_COPY[locale][key], values), [locale]);
  const n = useCallback((value: number) => formatNumber(locale, value), [locale]);
  const origin = useMemo(consoleOrigin, []);
  const [state, setState] = useState<{ status: "loading" } | { status: "ready"; data: Loaded } | { status: "error"; code: string; message: string }>({ status: "loading" });
  const [codes, setCodes] = useState<Record<number, string>>({});
  const [begun, setBegun] = useState<Record<number, PairingBegun>>({});
  const [begunAll, setBegunAll] = useState<PairingBegunAll | null>(null);
  // The pasted block is memory-only (UI-07 §3.6): cleared on submit, never stored.
  const [block, setBlock] = useState("");
  const [bulkResult, setBulkResult] = useState<RedeemAllResult | null>(null);
  const [bulkWorking, setBulkWorking] = useState<"preparing" | "approving" | null>(null);
  const [deferring, setDeferring] = useState<Record<number, string>>({});
  const [refusal, setRefusal] = useState<{ code: string; message: string } | null>(null);
  const [published, setPublished] = useState<PublishResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [approverDraft, setApproverDraft] = useState<string | null>(null);
  const [approverSaved, setApproverSaved] = useState(false);

  const load = useCallback(async () => {
    try {
      const [preview, batches, publication, approver, reporting] = await Promise.all([
        getPrismaPreview(origin),
        getScreeningBatches(origin),
        // Spec 10, decision 3: the export link shows only while the publication is CURRENT.
        getPublicationStatus(origin).then(
          (status) => ({
            current: status.status === "CURRENT",
            // Published means current (M6-beta): STALE after a decision made since publishing.
            staleChanged: status.status === "STALE" && typeof status.details?.changed === "number" ? (status.details.changed as number) : null,
          }),
          () => ({ current: false, staleChanged: null }),
        ),
        getApprover(origin),
        // M7b-guideline (spec 09): an engine without the field reads as PRISMA 2020;
        // a failed call names no guideline rather than guessing one (review 2).
        getSettings(origin).then(
          (s) => s.reporting ?? "prisma-2020",
          () => "none",
        ),
      ]);
      // H-screening-read-performance: every batch's review in one request (one per batch before).
      const reviews = batches.batches.length ? await getBatchReviews(origin) : {};
      setState({ status: "ready", data: { preview, batches, reviews, current: publication.current, staleChanged: publication.staleChanged, approver, reporting } });
    } catch (error) {
      setState({ status: "error", ...codeOf(error) });
    }
  }, [origin]);

  useEffect(() => {
    void load();
  }, [load]);

  // UI-07 §3.6: a typed or pasted code is cleared on expiry, not only on submit.
  useEffect(() => {
    const ends = [begunAll?.code_expires_at, ...Object.values(begun).map((b) => b.code_expires_at)]
      .filter((x): x is string => Boolean(x))
      .map((x) => new Date(x).getTime())
      .filter((x) => Number.isFinite(x));
    if (!ends.length) return;
    const wait = Math.max(0, Math.min(...ends) - Date.now());
    const timer = window.setTimeout(() => {
      const now = Date.now();
      if (begunAll && new Date(begunAll.code_expires_at).getTime() <= now) {
        setBlock("");
        setBegunAll(null);
      }
      const expired = Object.values(begun).filter((b) => new Date(b.code_expires_at).getTime() <= now).map((b) => b.batch_index);
      if (expired.length) {
        setCodes((p) => Object.fromEntries(Object.entries(p).filter(([k]) => !expired.includes(Number(k)))));
        setBegun((p) => Object.fromEntries(Object.entries(p).filter(([k]) => !expired.includes(Number(k)))));
      }
    }, wait + 50);
    return () => window.clearTimeout(timer);
  }, [begunAll, begun]);

  async function act(run: () => Promise<unknown>) {
    setBusy(true);
    setRefusal(null);
    try {
      await run();
      await load();
    } catch (error) {
      setRefusal(codeOf(error));
      // A refused bulk paste may still have approved the batches before it (a 500
      // after a journal failure): read the batch states again so they show.
      await load();
    } finally {
      setBusy(false);
    }
  }

  const body = (() => {
    if (state.status === "loading") return <LoadingFrame heading={t("eyebrow")} sentence={t("loading")} />;
    if (state.status === "error") return <StateCard pageHeading locale={locale} code={state.code} message={state.message} consoleOrigin={origin} onRetry={() => void load()} />;
    const { preview, batches, reviews, current, staleChanged, approver, reporting } = state.data;
    // H-adopted-decisions-disclosure (answer 3): an advisory check reads "Look at this" and never blocks.
    const allPass = preview.checks.every((c) => c.ok || c.advisory);
    const adoption = preview.adoption;
    const allApproved = batches.batches.every((b) => reviews[b.batch_index]?.review.present);
    // Decided and not approved, as the screen can see it; the engine's own count
    // (which also re-offers a stale approval) comes back from the begin call.
    const ready = batches.batches.filter((b) => {
      const r = reviews[b.batch_index];
      return b.coverage === "COMPLETE" && b.unresolved_rows.length === 0 && r && !r.review.present && !r.deferral.present;
    }).length;
    const reasons = Object.entries(preview.excluded.by_reason).sort(([a], [b]) => a.localeCompare(b));

    return (
      <div className="space-y-6">
        <header>
          <p className="text-xs font-semibold uppercase tracking-[0.05em] text-brand rtl:tracking-normal">{t("eyebrow")}</p>
          <h1 className="font-display mt-1 text-[1.75rem] leading-[2.25rem] text-ink">{allPass ? t("title") : t("titleBlocked")}</h1>
          <p className="mt-2 inline-block border border-rule-strong px-2 py-0.5 text-xs text-ink-muted">{t("live")}</p>
          {current ? (
            <p className="mt-3">
              <a className="inline-flex min-h-11 items-center text-brand underline" href={exportHref(locale, origin)} data-export-link>
                {t("exportLink")}
              </a>
            </p>
          ) : null}
        </header>

        {refusal ? <StateCard locale={locale} code={refusal.code} message={refusal.message} consoleOrigin={origin} /> : null}
        {published ? (
          <div role="status" className="rounded-md bg-include-soft px-4 py-3 text-include" data-published>
            <p>{t("publishedPlain")}</p>
            <details className="mt-1 text-xs">
              <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">{DETAILS_LABEL[locale]}</summary>
              <DataCell>{published.generation_id}</DataCell>
            </details>
          </div>
        ) : null}

        {staleChanged !== null ? (
          <div role="alert" className="rounded-md bg-unclear-soft px-4 py-3 text-ink" data-publication-stale>
            <p>{t("publishedStale", { n: n(staleChanged) })}</p>
            <details className="mt-1 text-xs text-ink-muted">
              <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">{DETAILS_LABEL[locale]}</summary>
              <span className="font-mono" dir="ltr">
                GENERATION_STALE
              </span>
            </details>
          </div>
        ) : null}

        <div className="flex flex-wrap gap-6">
          <div className="min-w-0 flex-[999_1_480px] space-y-6">
            <section aria-labelledby="publish-prisma" className="rounded-lg border border-rule bg-leaf p-5">
              <div className="flex flex-wrap items-center gap-2">
                <h2 id="publish-prisma" className="font-semibold text-ink">
                  {t(reporting === "prisma-scr" ? "prismaScr" : reporting === "none" ? "prismaNone" : "prisma")}
                </h2>
                <DecisionBadge role="exclude">{t("preview")}</DecisionBadge>
              </div>
              <dl className="mt-3 grid grid-cols-[1fr_auto] gap-x-6 gap-y-1 text-sm">
                {(
                  [
                    ["identified", preview.identified],
                    ["duplicates", preview.duplicates_removed],
                    ["screened", preview.screened],
                    ["excluded", preview.excluded.total],
                    ["unclear", preview.unclear_to_full_text],
                    ["included", preview.included],
                    ["notYet", preview.not_yet_decided],
                  ] as [PublishCopyKey, number][]
                ).map(([key, value]) => (
                  <div key={key} className="contents">
                    <dt className="text-ink-muted">{t(key)}</dt>
                    <dd className="text-end text-ink">{n(value)}</dd>
                  </div>
                ))}
              </dl>
              {reasons.length > 0 ? (
                <table className="mt-4 w-full text-sm">
                  <thead>
                    <tr className="text-ink-muted">
                      <th scope="col" className="py-1 text-start">{t("reason")}</th>
                      <th scope="col" className="py-1 text-end">{t("count")}</th>
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
              <p className="mt-3 text-xs text-ink-muted">{t("unclearNote")}</p>
            </section>

            <section aria-labelledby="publish-checks" className="rounded-lg border border-rule bg-leaf p-5">
              <h2 id="publish-checks" className="font-semibold text-ink">
                {t("checks")}
              </h2>
              <ul className="mt-3 space-y-2 text-sm">
                {preview.checks.map((c) => {
                  const key = `check.${c.name}` as PublishCopyKey;
                  return (
                    <li key={c.name} className="flex flex-wrap items-center gap-2" data-check={c.name}>
                      <DecisionBadge role={c.ok ? "include" : c.advisory ? "unclear" : "blocked"}>{c.ok ? t("pass") : c.advisory ? t("look") : t("fail")}</DecisionBadge>
                      <span className="text-ink">{key in PUBLISH_COPY[locale] ? t(key) : c.name}</span>
                      {c.ok ? null : (
                        <span className="text-xs text-ink-muted" dir="ltr">
                          {c.detail}
                        </span>
                      )}
                    </li>
                  );
                })}
              </ul>
              {preview.checks.some((c) => c.ok && c.detail) ? (
                <details className="mt-2 text-xs text-ink-muted" data-checks-details>
                  <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">{DETAILS_LABEL[locale]}</summary>
                  <ul className="mt-1 space-y-1">
                    {preview.checks
                      .filter((c) => c.ok && c.detail)
                      .map((c) => (
                        <li key={c.name} dir="ltr">
                          {c.name}: {c.detail}
                        </li>
                      ))}
                  </ul>
                </details>
              ) : null}
              {adoption && (adoption.undeclared_candidates > 0 || adoption.integrity.removed.length + adoption.integrity.unconfirmed.length > 0) ? (
                <p className="mt-3 text-sm text-ink" data-adoption-look>
                  {adoption.integrity.removed.length + adoption.integrity.unconfirmed.length > 0
                    ? adoptionText(locale, "integrity")
                    : adoptionText(locale, "undeclared", { n: n(adoption.undeclared_candidates) })}{" "}
                  {adoptionText(locale, "checkDeclaredNote")}{" "}
                  <a className="text-brand underline" href={adoptedHref(locale, origin)}>{adoptionText(locale, "declareLink")}</a>
                </p>
              ) : null}
              {adoption && adoption.declared > 0 ? (
                <p className="mt-3 text-sm text-ink" data-adoption-declared={adoption.declared}>
                  {adoptionText(locale, "storedCount", { n: n(adoption.declared) })}
                  {adoption.sample_owed ? (
                    <>
                      {" "}
                      {adoption.sample_owed_size !== null
                        ? adoptionText(locale, "publishOwed", { k: n(adoption.sample_owed_size) })
                        : adoptionText(locale, "publishOwedNone")}
                    </>
                  ) : null}
                </p>
              ) : null}
              {!preview.checks.find((c) => c.name === "projections_current")?.ok ? (
                <div className="mt-3">
                  <StateCard locale={locale} code="PROJECTION_STALE" consoleOrigin={origin} />
                </div>
              ) : preview.not_yet_decided > 0 ? (
                <a className="mt-3 inline-block text-brand underline" href={stepHref(locale, "triage", origin)}>
                  {t("toTriage")}
                </a>
              ) : null}
            </section>
          </div>

          <div className="w-full flex-[1_1_320px] space-y-6">
            <section aria-labelledby="publish-approver" className="rounded-lg border border-rule bg-leaf p-5" data-approver>
              <h2 id="publish-approver" className="font-semibold text-ink">
                {t("approverTitle")}
              </h2>
              <p className="mt-1 text-sm text-ink-muted">{t("approverBody")}</p>
              <p className="mt-3 text-sm text-ink" data-approver-state={approver.name ? "set" : "missing"}>
                {approver.name ? t("approverCurrent", { name: approver.name }) : t("approverNone")}
              </p>
              <form
                className="mt-3 space-y-2"
                onSubmit={(e) => {
                  e.preventDefault();
                  const name = (approverDraft ?? approver.name ?? "").trim();
                  void act(async () => {
                    setApproverSaved(false);
                    await putApprover(origin, name);
                    setApproverDraft(null);
                    setApproverSaved(true);
                  });
                }}
              >
                <label className="block text-sm text-ink">
                  {t("approverLabel")}
                  <input
                    type="text"
                    autoComplete="name"
                    dir="auto"
                    maxLength={120}
                    value={approverDraft ?? approver.name ?? ""}
                    onChange={(e) => {
                      setApproverDraft(e.target.value);
                      setApproverSaved(false);
                    }}
                    className="mt-1 block w-full rounded-md border border-rule bg-paper p-2 text-ink"
                  />
                </label>
                <Button type="submit" disabled={busy || !(approverDraft ?? approver.name ?? "").trim()}>
                  {t("approverSave")}
                </Button>
                {approverSaved ? (
                  <p role="status" className="text-xs text-include">
                    {t("approverSaved")}
                  </p>
                ) : null}
              </form>
            </section>

            <section aria-labelledby="publish-batches" className="rounded-lg border border-rule bg-leaf p-5">
              <h2 id="publish-batches" className="font-semibold text-ink">
                {t("batches")}
              </h2>
              <p className="mt-1 text-sm text-ink-muted">{t("batchesBody")}</p>
              <div className="mt-4 space-y-3" data-bulk-approval>
                <p className="text-sm text-ink" data-bulk-ready>
                  {t("bulkReady", { ready: n(ready), total: n(batches.batches.length) })}
                </p>
                <Button
                  disabled={busy || !approver.name}
                  onClick={() =>
                    void act(async () => {
                      setBulkResult(null);
                      setBulkWorking("preparing");
                      try {
                        setBegunAll(await beginApprovalAll(origin));
                      } finally {
                        setBulkWorking(null);
                      }
                    })
                  }
                >
                  {t("bulkAsk")}
                </Button>
                {begunAll ? (
                  <div className="space-y-1 text-xs text-ink-muted" role="status" data-bulk-begun>
                    <p>
                      {t(begunAll.code_shown_on === "desktop" ? "bulkShownDesktop" : "bulkShownTerminal", {
                        n: n(begunAll.batches.length),
                        time: new Date(begunAll.code_expires_at).toLocaleTimeString(locale),
                      })}
                    </p>
                    {begunAll.skipped.length ? (
                      <p>
                        {t("bulkSkipped", {
                          approved: n(begunAll.skipped.filter((x) => x.reason === "ALREADY_APPROVED").length),
                          deferred: n(begunAll.skipped.filter((x) => x.reason === "DEFERRED").length),
                          undecided: n(begunAll.skipped.filter((x) => x.reason === "NOT_DECIDED").length),
                        })}
                      </p>
                    ) : null}
                    {begunAll.skipped.some((x) => !SKIP_KINDS.has(x.reason)) ? (
                      <p data-bulk-skipped-other>
                        {t("bulkSkippedOther", {
                          batches: begunAll.skipped
                            .filter((x) => !SKIP_KINDS.has(x.reason))
                            .map((x) => `${t("batchN", { n: n(x.batch_index) })} (${x.reason})`)
                            .join(", "),
                        })}
                      </p>
                    ) : null}
                  </div>
                ) : null}
                <label className="block text-sm text-ink">
                  {t("bulkLabel")}
                  <textarea
                    rows={4}
                    autoComplete="off"
                    spellCheck={false}
                    dir="ltr"
                    value={block}
                    onChange={(e) => setBlock(e.target.value)}
                    className="mt-1 block w-full rounded-md border border-rule bg-paper p-2 font-mono text-xs text-ink"
                  />
                </label>
                <Button
                  disabled={busy || !approver.name || !block.trim()}
                  onClick={() =>
                    void act(async () => {
                      const text = block;
                      setBlock("");
                      setBulkWorking("approving");
                      try {
                        const result = await postPairingRedeemAll(origin, text);
                        setBulkResult(result);
                        setBegunAll(null);
                      } finally {
                        setBulkWorking(null);
                      }
                    })
                  }
                >
                  {t("bulkApprove")}
                </Button>
                {bulkWorking ? (
                  <p className="text-xs text-ink-muted" role="status">
                    {t(bulkWorking === "preparing" ? "bulkPreparing" : "bulkWorking")}
                  </p>
                ) : null}
                {bulkResult ? (
                  <div className="space-y-1 text-sm" role="status" data-bulk-result>
                    <p className="text-include">{t("bulkDone", { n: n(bulkResult.approved.length) })}</p>
                    {bulkResult.refused.map((r) => (
                      <p key={r.batch_index} className="text-ink">
                        {t("bulkRefused", { batch: t("batchN", { n: n(r.batch_index) }), code: r.code })}
                      </p>
                    ))}
                  </div>
                ) : null}
              </div>
              <details className="mt-4" data-one-by-one>
                <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm text-brand focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">{t("oneByOne")}</summary>
                <ul className="mt-2 space-y-4">
                  {batches.batches.map((b) => {
                    const review = reviews[b.batch_index];
                    const label = t("batchN", { n: n(b.batch_index) });
                    const approved = review?.review.present === true;
                    return (
                      <li key={b.batch_index} className="border-t border-rule pt-3" data-batch={b.batch_index}>
                        <p className="flex flex-wrap items-center gap-2">
                          <span className="inline-block font-medium text-ink first-letter:uppercase">{label}</span>
                          {approved ? (
                            <DecisionBadge role="include">{t("approved")}</DecisionBadge>
                          ) : review?.deferral.present ? (
                            <DecisionBadge role="unclear">{t("deferred")}</DecisionBadge>
                          ) : (
                            <DecisionBadge role="unclear">{t("notApproved")}</DecisionBadge>
                          )}
                        </p>
                        <details className="mt-1 text-xs text-ink-muted">
                          <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">{DETAILS_LABEL[locale]}</summary>
                          <DataCell>{b.batch_file}</DataCell>
                        </details>
                        {approved ? <p className="mt-1 text-xs text-ink-muted">{t("approvedNote")}</p> : null}
                        {(
                          <div className="mt-2 space-y-2">
                            <Button
                              disabled={busy || !approver.name}
                              onClick={() =>
                                void act(async () => {
                                  const staged = await beginApproval(origin, b.batch_index);
                                  setBegun((p) => ({ ...p, [b.batch_index]: staged }));
                                })
                              }
                            >
                              {t("askCode", { batch: label })}
                            </Button>
                            {begun[b.batch_index] ? (
                              <p className="text-xs text-ink-muted">
                                {t(begun[b.batch_index].code_shown_on === "desktop" ? "codeShownDesktop" : "codeShown", {
                                  time: new Date(begun[b.batch_index].code_expires_at).toLocaleTimeString(locale),
                                })}
                              </p>
                            ) : null}
                            <label className="block text-sm text-ink">
                              {t("codeLabel", { batch: label })}
                              <input
                                type="text"
                                autoComplete="off"
                                spellCheck={false}
                                dir="ltr"
                                value={codes[b.batch_index] ?? ""}
                                onChange={(e) => setCodes((p) => ({ ...p, [b.batch_index]: e.target.value }))}
                                className="mt-1 block w-full rounded-md border border-rule bg-paper p-2 font-mono text-ink"
                              />
                            </label>
                            <Button
                              disabled={busy || !approver.name || !(codes[b.batch_index] ?? "").trim()}
                              onClick={() =>
                                void act(async () => {
                                  const code = (codes[b.batch_index] ?? "").trim();
                                  setCodes((p) => ({ ...p, [b.batch_index]: "" }));
                                  await postPairingRedeem(origin, b.batch_index, code);
                                })
                              }
                            >
                              {t("approve", { batch: label })}
                            </Button>
                            <details className="text-sm">
                              <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-brand">{t("defer")}</summary>
                              <label className="mt-2 block text-ink">
                                {t("deferReason", { batch: label })}
                                <textarea
                                  rows={2}
                                  value={deferring[b.batch_index] ?? ""}
                                  onChange={(e) => setDeferring((p) => ({ ...p, [b.batch_index]: e.target.value }))}
                                  className="mt-1 block w-full rounded-md border border-rule bg-paper p-2 text-ink"
                                />
                              </label>
                              <Button
                                className="mt-2"
                                disabled={busy || !(deferring[b.batch_index] ?? "").trim()}
                                onClick={() => void act(() => postDeferBatch(origin, b.batch_index, (deferring[b.batch_index] ?? "").trim()))}
                              >
                                {t("deferSave")}
                              </Button>
                            </details>
                          </div>
                        )}
                      </li>
                    );
                  })}
                </ul>
              </details>
            </section>

            <GatePanel
              label={t("publishGate")}
              actions={
                <Button variant="primary" disabled={busy || !allPass || !allApproved} onClick={() => void act(async () => {
                  setPublished(await postPublishScreening(origin));
                  notifyReviewChanged();
                })}>
                  {t("publish")}
                </Button>
              }
            >
              {t(reporting === "none" ? "publishBodyNone" : "publishBody")}
            </GatePanel>
          </div>
        </div>
      </div>
    );
  })();

  return (
    <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8 lg:py-14">
      <ScreeningSteps locale={locale} current="publish" consoleOrigin={origin} />
      {body}
    </div>
  );
}
