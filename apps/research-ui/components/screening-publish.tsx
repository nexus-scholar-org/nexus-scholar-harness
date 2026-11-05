"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

import { formatNumber, type Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge, GatePanel } from "@/components/ui/base";
import { ScreeningSteps, StateCard, exportHref, stepHref } from "@/components/screening-state-card";
import {
  getBatchReview,
  getPublicationStatus,
  getScreeningBatches,
  isScreeningApiError,
  postDeferBatch,
  postPairingRedeem,
  postPublishScreening,
  type PublishResult,
  type ReviewState,
  type ScreeningBatches,
} from "@/lib/screening-api";
import { beginApproval, getPrismaPreview, type PairingBegun, type PrismaPreview } from "@/lib/screening-v1";

/**
 * Publish (spec 09): the PRISMA screening preview with its checks, one
 * approval per batch with the code the engine prints in its terminal (never
 * sent over HTTP, decision 2026-11-04), then the gated publish. Phone pairing
 * by QR is M2.
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
    "check.human_provenance": "Every decision is a human decision",
    "check.no_open_conflicts": "No open conflicts between devices",
    "check.bound_to_current_protocol": "Decisions are bound to the current protocol",
    "check.every_record_decided": "Every record is decided",
    "check.projections_current": "Every decisions file matches the decision log",
    pass: "Passes",
    fail: "Fails",
    batches: "Approval, one batch at a time",
    batchesBody: "Approval needs the one-time code the engine prints in its terminal. Ask for it, read it there, and type it here. A decision changed after approval makes the approval stale.",
    approved: "Approval on file",
    approvedNote: "A decision changed after this approval makes it stale; approve again. Publish refuses a stale approval.",
    notApproved: "Not approved",
    deferred: "Deferred",
    askCode: "Show a code in the terminal",
    codeShown: "Code printed in the terminal; it expires at {time}.",
    codeLabel: "Approval code for {batch}",
    approve: "Approve {batch}",
    defer: "Defer",
    deferReason: "Reason for deferring {batch}",
    deferSave: "Record the deferral",
    publish: "Publish the screening",
    publishGate: "Publish",
    publishBody: "Writes the included, excluded and full-text lists and the PRISMA report for the approved generation.",
    published: "Published generation {id}",
    toTriage: "Open triage",
  },
  fr: {
    eyebrow: "Sélection · publication",
    title: "Approuvez chaque lot, puis publiez la sélection.",
    titleBlocked: "La publication attend que tous les contrôles soient satisfaits.",
    live: "Données en direct du moteur de sélection de cet espace",
    exportLink: "Export et méthodes",
    loading: "Lecture de l'aperçu…",
    prisma: "Aperçu de sélection PRISMA 2020",
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
    "check.human_provenance": "Chaque décision est humaine",
    "check.no_open_conflicts": "Aucun conflit ouvert entre appareils",
    "check.bound_to_current_protocol": "Les décisions sont liées au protocole actuel",
    "check.every_record_decided": "Chaque notice est décidée",
    "check.projections_current": "Chaque fichier de décisions correspond au journal",
    pass: "Satisfait",
    fail: "Échoue",
    batches: "Approbation, lot par lot",
    batchesBody: "L'approbation exige le code à usage unique que le moteur affiche dans son terminal. Demandez-le, lisez-le là-bas et saisissez-le ici. Une décision modifiée après approbation rend l'approbation périmée.",
    approved: "Approbation enregistrée",
    approvedNote: "Une décision modifiée après cette approbation la rend périmée ; approuvez à nouveau. La publication refuse une approbation périmée.",
    notApproved: "Non approuvé",
    deferred: "Reporté",
    askCode: "Afficher un code dans le terminal",
    codeShown: "Code affiché dans le terminal ; il expire à {time}.",
    codeLabel: "Code d'approbation pour {batch}",
    approve: "Approuver {batch}",
    defer: "Reporter",
    deferReason: "Motif du report de {batch}",
    deferSave: "Enregistrer le report",
    publish: "Publier la sélection",
    publishGate: "Publication",
    publishBody: "Écrit les listes d'inclusions, d'exclusions et de texte intégral ainsi que le rapport PRISMA de la génération approuvée.",
    published: "Génération publiée {id}",
    toTriage: "Ouvrir le tri",
  },
  ar: {
    eyebrow: "الفرز · النشر",
    title: "اعتمد كل دفعة، ثم انشر نتائج الفرز.",
    titleBlocked: "ينتظر النشر حتى تنجح كل الفحوص.",
    live: "بيانات حية من محرك الفرز لهذه المساحة",
    exportLink: "التصدير والمنهجية",
    loading: "جارٍ قراءة المعاينة…",
    prisma: "معاينة فرز PRISMA 2020",
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
    "check.human_provenance": "كل قرار هو قرار بشري",
    "check.no_open_conflicts": "لا تعارضات مفتوحة بين الأجهزة",
    "check.bound_to_current_protocol": "القرارات مرتبطة بالبروتوكول الحالي",
    "check.every_record_decided": "حُسم كل سجل",
    "check.projections_current": "كل ملف قرارات مطابق للسجل",
    pass: "ناجح",
    fail: "فاشل",
    batches: "الاعتماد، دفعة تلو الأخرى",
    batchesBody: "يحتاج الاعتماد إلى رمز لمرة واحدة يطبعه المحرك في طرفيته. اطلبه واقرأه هناك ثم اكتبه هنا. أي قرار يتغيّر بعد الاعتماد يجعل الاعتماد قديمًا.",
    approved: "اعتماد مسجّل",
    approvedNote: "أي قرار يتغيّر بعد هذا الاعتماد يجعله قديمًا؛ اعتمد من جديد. يرفض النشر الاعتماد القديم.",
    notApproved: "غير معتمدة",
    deferred: "مؤجلة",
    askCode: "عرض رمز في الطرفية",
    codeShown: "طُبع الرمز في الطرفية؛ تنتهي صلاحيته في {time}.",
    codeLabel: "رمز اعتماد {batch}",
    approve: "اعتماد {batch}",
    defer: "تأجيل",
    deferReason: "سبب تأجيل {batch}",
    deferSave: "تسجيل التأجيل",
    publish: "نشر نتائج الفرز",
    publishGate: "النشر",
    publishBody: "يكتب قوائم المُدرجة والمستبعدة والنص الكامل وتقرير PRISMA للجيل المعتمد.",
    published: "نُشر الجيل {id}",
    toTriage: "فتح المراجعة",
  },
} as const satisfies Record<Locale, Record<string, string>>;

export type PublishCopyKey = keyof (typeof COPY)["en"];
export const PUBLISH_COPY: Record<Locale, Record<PublishCopyKey, string>> = COPY;

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

type Loaded = { preview: PrismaPreview; batches: ScreeningBatches; reviews: Record<number, ReviewState>; current: boolean };

export function ScreeningPublish({ locale }: Readonly<{ locale: Locale }>) {
  const t = useCallback((key: PublishCopyKey, values?: Record<string, string | number>) => fill(PUBLISH_COPY[locale][key], values), [locale]);
  const n = useCallback((value: number) => formatNumber(locale, value), [locale]);
  const origin = useMemo(consoleOrigin, []);
  const [state, setState] = useState<{ status: "loading" } | { status: "ready"; data: Loaded } | { status: "error"; code: string; message: string }>({ status: "loading" });
  const [codes, setCodes] = useState<Record<number, string>>({});
  const [begun, setBegun] = useState<Record<number, PairingBegun>>({});
  const [deferring, setDeferring] = useState<Record<number, string>>({});
  const [refusal, setRefusal] = useState<{ code: string; message: string } | null>(null);
  const [published, setPublished] = useState<PublishResult | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    try {
      const [preview, batches, current] = await Promise.all([
        getPrismaPreview(origin),
        getScreeningBatches(origin),
        // Spec 10, decision 3: the export link shows only while the publication is CURRENT.
        getPublicationStatus(origin).then((status) => status.status === "CURRENT", () => false),
      ]);
      const reviews = Object.fromEntries(
        await Promise.all(batches.batches.map(async (b) => [b.batch_index, await getBatchReview(origin, b.batch_index)] as const)),
      );
      setState({ status: "ready", data: { preview, batches, reviews, current } });
    } catch (error) {
      setState({ status: "error", ...codeOf(error) });
    }
  }, [origin]);

  useEffect(() => {
    void load();
  }, [load]);

  async function act(run: () => Promise<unknown>) {
    setBusy(true);
    setRefusal(null);
    try {
      await run();
      await load();
    } catch (error) {
      setRefusal(codeOf(error));
    } finally {
      setBusy(false);
    }
  }

  const body = (() => {
    if (state.status === "loading") return <p className="text-ink-muted" role="status">{t("loading")}</p>;
    if (state.status === "error") return <StateCard pageHeading locale={locale} code={state.code} message={state.message} consoleOrigin={origin} onRetry={() => void load()} />;
    const { preview, batches, reviews, current } = state.data;
    const allPass = preview.checks.every((c) => c.ok);
    const allApproved = batches.batches.every((b) => reviews[b.batch_index]?.review.present);
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
          <p role="status" className="rounded-md bg-include-soft px-4 py-3 text-include">
            {t("published", { id: published.generation_id })}
          </p>
        ) : null}

        <div className="flex flex-wrap gap-6">
          <div className="min-w-0 flex-[999_1_480px] space-y-6">
            <section aria-labelledby="publish-prisma" className="rounded-lg border border-rule bg-leaf p-5">
              <div className="flex flex-wrap items-center gap-2">
                <h2 id="publish-prisma" className="font-semibold text-ink">
                  {t("prisma")}
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
                      <DecisionBadge role={c.ok ? "include" : "blocked"}>{c.ok ? t("pass") : t("fail")}</DecisionBadge>
                      <span className="text-ink">{key in PUBLISH_COPY[locale] ? t(key) : c.name}</span>
                      <span className="text-xs text-ink-muted" dir="ltr">
                        {c.detail}
                      </span>
                    </li>
                  );
                })}
              </ul>
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
            <section aria-labelledby="publish-batches" className="rounded-lg border border-rule bg-leaf p-5">
              <h2 id="publish-batches" className="font-semibold text-ink">
                {t("batches")}
              </h2>
              <p className="mt-1 text-sm text-ink-muted">{t("batchesBody")}</p>
              <ul className="mt-4 space-y-4">
                {batches.batches.map((b) => {
                  const review = reviews[b.batch_index];
                  const label = b.batch_file.replace(/\.json$/, "");
                  const approved = review?.review.present === true;
                  return (
                    <li key={b.batch_index} className="border-t border-rule pt-3" data-batch={b.batch_index}>
                      <p className="flex flex-wrap items-center gap-2">
                        <DataCell>{label}</DataCell>
                        {approved ? (
                          <DecisionBadge role="include">{t("approved")}</DecisionBadge>
                        ) : review?.deferral.present ? (
                          <DecisionBadge role="unclear">{t("deferred")}</DecisionBadge>
                        ) : (
                          <DecisionBadge role="unclear">{t("notApproved")}</DecisionBadge>
                        )}
                      </p>
                      {approved ? <p className="mt-1 text-xs text-ink-muted">{t("approvedNote")}</p> : null}
                      {(
                        <div className="mt-2 space-y-2">
                          <Button
                            disabled={busy}
                            onClick={() =>
                              void act(async () => {
                                const staged = await beginApproval(origin, b.batch_index);
                                setBegun((p) => ({ ...p, [b.batch_index]: staged }));
                              })
                            }
                          >
                            {t("askCode")}
                          </Button>
                          {begun[b.batch_index] ? (
                            <p className="text-xs text-ink-muted">{t("codeShown", { time: new Date(begun[b.batch_index].code_expires_at).toLocaleTimeString(locale) })}</p>
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
                            disabled={busy || !(codes[b.batch_index] ?? "").trim()}
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
                            <summary className="cursor-pointer text-brand">{t("defer")}</summary>
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
            </section>

            <GatePanel
              label={t("publishGate")}
              actions={
                <Button variant="primary" disabled={busy || !allPass || !allApproved} onClick={() => void act(async () => setPublished(await postPublishScreening(origin)))}>
                  {t("publish")}
                </Button>
              }
            >
              {t("publishBody")}
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
