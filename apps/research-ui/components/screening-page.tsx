"use client";

import { useEffect, useRef, useState } from "react";

import { formatNumber, translate, type Locale } from "@/i18n";
import {
  getBatchRows,
  getCriterionRefs,
  getPairingStatus,
  getProjectSummary,
  getPublicationStatus,
  getScreeningBatches,
  isScreeningApiError,
  consoleBase,
  postDeferBatch,
  postPairingRedeem,
  postPublishScreening,
  type CriterionRefs,
  type DeferResult,
  type PairingStatus,
  type ProjectSummary,
  type PublicationStatus,
  type PublishResult,
  type RedeemResult,
  type ScreeningApiError,
  type ScreeningBatches,
  type ScreeningRows,
} from "@/lib/screening-api";
import { demoScreeningRecord } from "@/lib/mock-screening";

import { ACTION_CHROME, PairingDialog, type PairingServerError } from "./pairing-dialog";
import { ScreeningForm } from "./screening-form";

/**
 * The screening workspace composition (packet UI-04, live read wiring HCM-06).
 *
 * A composition that renders one demonstration record against the sealed
 * criteria, and hands the decision to `ScreeningForm`. The four sections read
 * as the argument a reviewer actually makes: here is the study (citation and
 * abstract), here is what it must satisfy (the criteria), here is your decision.
 *
 * Three boundaries are structural, not stylistic:
 *
 * - **No `main`.** The shell owns the single `MAIN_CONTENT_ID` landmark, exactly
 *   as it does for the overview; a nested `main` here would give the document
 *   two of them and break the skip link's contract.
 * - **Two kinds of text.** Catalog strings are plain text; every word of the
 *   record (citation, abstract, criteria) is rendered byte for byte inside
 *   `<bdi>` (D-I18N-02), so an English citation inside an Arabic page stays
 *   readable instead of being reordered by the bidirectional algorithm. Nothing
 *   here translates record prose, and nothing here invents an identifier: the
 *   demonstration citation carries no DOI, no accession number, no fingerprint.
 * - **Ordinals are formatted, not literal.** The criteria list numbers itself
 *   with `formatNumber`, so `ar` reads ١٬٢٬٣ in its own numerals rather than
 *   inheriting the page's Latin digits by accident (A4.5), and the marginal
 *   numeral is a real element with real text, mirroring `EvidenceChain`.
 *
 * Heading levels run h1 → h2 only, with no skip: record, criteria, decision.
 * The decision section's `<h2>` is the form's own heading, so the form's
 * `legend` stays a group label instead of competing with it.
 *
 * Live read wiring (HCM-06, UI-07 presentation only): when the URL carries
 * `?source=live`, the record and criteria sections are replaced by data read
 * from the local console over HTTP through `@/lib/screening-api`. The default
 * stays the demonstration record: no request is sent unless the reader asked
 * for the live source. The live source gains the operator-approval panel
 * (`ScreeningActions`): redeeming a terminal-staged pairing code, recording a
 * deferral with a reason, and triggering the gated collect are the only
 * writes the screen performs, each over loopback and each refused loudly
 * with the server typed code. The demonstration form itself stays untouched:
 * its disabled submit keeps submitting nowhere.
 */

/**
 * The few live-source chrome strings that name the live panel itself.
 *
 * These live beside the component rather than in the catalogs because the
 * catalogs are frozen to this packet's scope; they are demonstration-grade
 * translations pending fluent review (GATES §5.6 H1/H2), and every
 * server-supplied value around them (identifiers, codes, refusal text) keeps
 * its own element, untranslated, exactly as served.
 */
export const LIVE_CHROME = {
  en: {
    liveStamp: "Live console data",
    liveLede:
      "The records below were read from the local console over HTTP. They are live workspace data, not the demonstration record.",
    liveUnavailable: "Live data unavailable",
    liveEmpty: "The console reports no prepared screening batches.",
    liveTechIds: "Technical identifiers",
  },
  fr: {
    liveStamp: "Données en direct de la console",
    liveLede:
      "Les notices ci-dessous ont été lues depuis la console locale via HTTP. Ce sont des données réelles de l'espace de travail, et non la notice de démonstration.",
    liveUnavailable: "Données en direct indisponibles",
    liveEmpty: "La console ne signale aucune vague de sélection préparée.",
    liveTechIds: "Identifiants techniques",
  },
  ar: {
    liveStamp: "بيانات مباشرة من المنصة",
    liveLede:
      "السجلات أدناه قُرئت من المنصة المحلية عبر HTTP. وهي بيانات حية من مساحة العمل وليست سجل العرض.",
    liveUnavailable: "تعذّر جلب البيانات المباشرة",
    liveEmpty: "لا تبلغ المنصة عن أي دفعات فرز مُعدّة.",
    liveTechIds: "معرّفات تقنية",
  },
} as const;

type SourceMode = { kind: "fixture" } | { kind: "live"; origin: string };

type LiveState =
  | { status: "idle" }
  | { status: "loading"; origin: string }
  | { status: "empty"; origin: string; batches: ScreeningBatches }
  | {
      status: "ready";
      origin: string;
      summary: ProjectSummary;
      batches: ScreeningBatches;
      publication: PublicationStatus;
      rows: ScreeningRows;
      refs: CriterionRefs;
    }
  | { status: "error"; origin: string; error: unknown };

/** The console origin the live source reads, or null when not requested. */
function readLiveOrigin(): string | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  if (params.get("source") !== "live") return null;
  return params.get("console") ?? "";
}

function decisionLabel(locale: Locale, decision: string): string {
  const token = decision.trim().toUpperCase();
  if (token === "INCLUDE") return translate(locale, "screening.decision.include");
  if (token === "EXCLUDE") return translate(locale, "screening.decision.exclude");
  return translate(locale, "screening.decision.unclear");
}

function LiveErrorBody({ locale, error }: { locale: Locale; error: unknown }) {
  const chrome = LIVE_CHROME[locale];
  const code = isScreeningApiError(error) ? error.code : "UNKNOWN_ERROR";
  const message =
    isScreeningApiError(error) && error.serverMessage ? error.serverMessage : String(error);
  return (
    <div>
      <p className="text-sm leading-6 text-warning">{chrome.liveUnavailable}</p>
      <p className="mt-2 text-sm leading-6 text-ink-muted">
        <bdi dir="ltr">{code}</bdi>
        {": "}
        <bdi dir="ltr">{message}</bdi>
      </p>
    </div>
  );
}

function LiveReadyBody({
  locale,
  origin,
  batchIndex,
  summary,
  batches,
  publication,
  rows,
  refs,
}: {
  locale: Locale;
  origin: string;
  batchIndex: number;
  summary: ProjectSummary;
  batches: ScreeningBatches;
  publication: PublicationStatus;
  rows: ScreeningRows;
  refs: CriterionRefs;
}) {
  const chrome = LIVE_CHROME[locale];
  return (
    <div>
      <dl className="border-t border-rule-strong">
        <div className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-[9rem_minmax(0,1fr)]">
          <dt className="text-sm font-medium leading-6 text-ink">Workspace</dt>
          <dd className="min-w-0 text-sm leading-6 text-ink-muted">
            <bdi>{summary.workspace_id ?? "unknown"}</bdi>
          </dd>
        </div>
        <div className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-[9rem_minmax(0,1fr)]">
          <dt className="text-sm font-medium leading-6 text-ink">Run</dt>
          <dd className="min-w-0 text-sm leading-6 text-ink-muted">
            <bdi>{summary.run?.screening_run_id ?? "unknown"}</bdi>
            {" · "}
            {formatNumber(locale, batches.count)}
          </dd>
        </div>
        <div className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-[9rem_minmax(0,1fr)]">
          <dt className="text-sm font-medium leading-6 text-ink">Publication</dt>
          <dd className="min-w-0 text-sm leading-6 text-ink-muted">
            <bdi>{publication.status}</bdi>
            {publication.generation_id ? (
              <>
                {" · "}
                <bdi>{publication.generation_id}</bdi>
              </>
            ) : null}
          </dd>
        </div>
      </dl>

      <ul className="mt-8 border-t border-rule-strong">
        {rows.rows.map((row) => (
          <li key={row.study_id} className="border-b border-rule py-4">
            <p className="text-sm leading-6 text-ink">
              <bdi>{row.citation ?? row.study_id}</bdi>
            </p>
            {row.abstract ? (
              <p className="mt-1 text-sm leading-6 text-ink-muted">
                <bdi>{row.abstract}</bdi>
              </p>
            ) : null}
            <p className="mt-2 text-sm leading-6 text-ink-muted">
              {decisionLabel(locale, row.decision)}
              {row.reasons.length > 0 ? (
                <>
                  {" — "}
                  <bdi>{row.reasons.join("; ")}</bdi>
                </>
              ) : null}
            </p>
          </li>
        ))}
      </ul>

      {refs.inclusion.length > 0 || refs.exclusion.length > 0 ? (
        <ol className="mt-8 border-t border-rule-strong">
          {[...refs.inclusion, ...refs.exclusion].map((criterion, index) => (
            <li
              key={criterion.id}
              className="grid grid-cols-[1.5rem_minmax(0,1fr)] gap-x-3 border-b border-rule py-4 lg:grid-cols-[1.75rem_minmax(0,1fr)] lg:gap-x-5"
            >
              <span className="pt-0.5 text-end text-[0.6875rem] leading-4 text-ink-faint rtl:text-[0.75rem]">
                {formatNumber(locale, index + 1)}
              </span>
              <div className="min-w-0 border-s border-rule-strong ps-3 lg:ps-5">
                <p className="text-sm leading-6 text-ink">
                  <bdi>{criterion.text}</bdi>
                </p>
              </div>
            </li>
          ))}
        </ol>
      ) : null}

      <details className="mt-8">
        <summary className="text-sm font-medium text-evidence underline decoration-2 underline-offset-4">
          {chrome.liveTechIds}
        </summary>
        <dl className="mt-3 border-t border-rule-strong">
          <div className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-[9rem_minmax(0,1fr)]">
            <dt className="text-sm font-medium leading-6 text-ink">Batch</dt>
            <dd className="min-w-0 text-sm leading-6 text-ink-muted">
              <bdi>{rows.batch_file}</bdi>
            </dd>
          </div>
          <div className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-[9rem_minmax(0,1fr)]">
            <dt className="text-sm font-medium leading-6 text-ink">Protocol</dt>
            <dd className="min-w-0 text-sm leading-6 text-ink-muted">
              <bdi>{refs.protocol_fingerprint ?? "unknown"}</bdi>
            </dd>
          </div>
          {publication.generation_id ? (
            <div className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-[9rem_minmax(0,1fr)]">
              <dt className="text-sm font-medium leading-6 text-ink">Generation</dt>
              <dd className="min-w-0 text-sm leading-6 text-ink-muted">
                <bdi>{publication.generation_id}</bdi>
              </dd>
            </div>
          ) : null}
        </dl>
      </details>

      <ScreeningActions locale={locale} origin={origin} batchIndex={batchIndex} />
    </div>
  );
}

type PairingPanel =
  | { status: "loading" }
  | { status: "error"; error: unknown }
  | { status: "ready"; pairing: PairingStatus };

function toServerError(error: unknown): PairingServerError {
  return {
    code: isScreeningApiError(error) ? error.code : "UNKNOWN_ERROR",
    message:
      isScreeningApiError(error) && error.serverMessage
        ? error.serverMessage
        : String(error),
  };
}

/**
 * The minimal action wiring for the connected UI-04 journey (packet UI-07).
 *
 * Rendered only in live mode, under the read panel, and deliberately heading-
 * free: the composition owns h1 → h2 and the criteria own the single `ol`, so
 * this panel adds no heading and no list of its own. It performs the only
 * writes the screen allows — redeeming a terminal-staged pairing code,
 * recording a deferral with a reason, triggering the gated collect — and
 * every refusal arrives as server text in its own element, never invented.
 * While any action is pending every button is disabled, so a double press
 * sends one request.
 */
function ScreeningActions({
  locale,
  origin,
  batchIndex,
}: Readonly<{ locale: Locale; origin: string; batchIndex: number }>) {
  const chrome = ACTION_CHROME[locale];
  const [panel, setPanel] = useState<PairingPanel>({ status: "loading" });
  const [dialogOpen, setDialogOpen] = useState(false);
  const [redeemPending, setRedeemPending] = useState(false);
  const [redeemError, setRedeemError] = useState<PairingServerError | null>(null);
  const [redeemResult, setRedeemResult] = useState<RedeemResult | null>(null);
  const [reason, setReason] = useState("");
  const [deferPending, setDeferPending] = useState(false);
  const [deferResult, setDeferResult] = useState<DeferResult | null>(null);
  const [deferError, setDeferError] = useState<PairingServerError | null>(null);
  const [publishPending, setPublishPending] = useState(false);
  const [publishResult, setPublishResult] = useState<PublishResult | null>(null);
  const [publishError, setPublishError] = useState<PairingServerError | null>(null);
  const busy = redeemPending || deferPending || publishPending;
  // Synchronous single-flight guard: React state lands after paint, so a
  // second press before the re-render must see the in-flight flag now.
  const flightRef = useRef(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const pairing = await getPairingStatus(origin, batchIndex);
        if (!cancelled) setPanel({ status: "ready", pairing });
      } catch (error: unknown) {
        if (!cancelled) setPanel({ status: "error", error });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [origin, batchIndex]);

  async function refreshPairing() {
    try {
      const pairing = await getPairingStatus(origin, batchIndex);
      setPanel({ status: "ready", pairing });
    } catch (error: unknown) {
      setPanel({ status: "error", error });
    }
  }

  async function handleRedeem(code: string) {
    if (flightRef.current) return;
    flightRef.current = true;
    setRedeemPending(true);
    setRedeemError(null);
    try {
      const result = await postPairingRedeem(origin, batchIndex, code);
      setRedeemResult(result);
      setDialogOpen(false);
      await refreshPairing();
    } catch (error: unknown) {
      setRedeemError(toServerError(error));
    } finally {
      flightRef.current = false;
      setRedeemPending(false);
    }
  }

  async function handleDefer() {
    if (reason.trim() === "") return;
    if (flightRef.current) return;
    flightRef.current = true;
    setDeferPending(true);
    setDeferError(null);
    try {
      const result = await postDeferBatch(origin, batchIndex, reason.trim());
      setDeferResult(result);
      await refreshPairing();
    } catch (error: unknown) {
      setDeferError(toServerError(error));
    } finally {
      flightRef.current = false;
      setDeferPending(false);
    }
  }

  async function handlePublish() {
    // Single-shot per view: the synchronous flag absorbs a second press
    // before paint, and the completed result absorbs the late press a real
    // browser re-dispatches after the pending round trip — the button reads
    // enabled again once current, so that late click must land here and do
    // nothing rather than send a second POST. A refused publish leaves the
    // result empty, so retry after an error still sends.
    if (publishResult !== null) return;
    if (flightRef.current) return;
    flightRef.current = true;
    setPublishPending(true);
    setPublishError(null);
    try {
      const result = await postPublishScreening(origin);
      setPublishResult(result);
    } catch (error: unknown) {
      setPublishError(toServerError(error));
    } finally {
      flightRef.current = false;
      setPublishPending(false);
    }
  }

  const stagedFingerprint =
    panel.status === "ready" ? panel.pairing.snapshot_fingerprint : null;

  return (
    <section aria-label={chrome.actionsTitle} className="mt-8 border-t border-rule-strong">
      <p className="mt-4 font-display text-xl leading-8 text-ink">{chrome.actionsTitle}</p>
      <p className="mt-1 text-sm leading-6 text-ink-muted">{chrome.actionsLede}</p>
      {panel.status === "loading" ? (
        <p role="status" className="mt-3 text-sm leading-6 text-ink-muted">
          {chrome.loadingLabel}
        </p>
      ) : panel.status === "error" ? (
        <p role="alert" className="mt-3 text-sm leading-6 text-warning">
          <bdi dir="ltr">{toServerError(panel.error).code}</bdi>
          {": "}
          <bdi dir="ltr">{toServerError(panel.error).message}</bdi>
        </p>
      ) : (
        <dl className="mt-3 border-t border-rule-strong">
          <div className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-[9rem_minmax(0,1fr)]">
            <dt className="text-sm font-medium leading-6 text-ink">{chrome.challengeLabel}</dt>
            <dd className="min-w-0 text-sm leading-6 text-ink-muted">
              <bdi>{panel.pairing.state}</bdi>
              {panel.pairing.snapshot_fingerprint ? (
                <>
                  {" · "}
                  <bdi>{panel.pairing.snapshot_fingerprint}</bdi>
                </>
              ) : null}
            </dd>
          </div>
        </dl>
      )}
      <div className="mt-3">
        <button
          type="button"
          onClick={() => {
            setRedeemError(null);
            setDialogOpen(true);
          }}
          disabled={busy || panel.status !== "ready" || panel.pairing.state !== "STAGED"}
          className="inline-flex items-center gap-2 border border-rule-strong bg-leaf px-3 py-2 text-sm font-medium text-ink hover:bg-paper disabled:cursor-not-allowed disabled:border-rule disabled:text-ink-faint"
        >
          {chrome.approveButton}
        </button>
        <button
          type="button"
          onClick={handlePublish}
          disabled={busy}
          className="inline-flex items-center gap-2 border border-rule-strong px-3 py-2 text-sm font-medium text-ink hover:bg-paper disabled:cursor-not-allowed disabled:border-rule disabled:text-ink-faint"
        >
          {publishPending ? chrome.workingLabel : chrome.publishButton}
        </button>
      </div>
      <div className="mt-3">
        <label htmlFor="screening-defer-reason" className="block text-sm font-medium text-ink">
          {chrome.reasonLabel}
        </label>
        <input
          id="screening-defer-reason"
          type="text"
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          className="mt-2 block w-full border border-rule-strong bg-leaf px-3 py-2 text-sm leading-6 text-ink"
        />
        <button
          type="button"
          onClick={handleDefer}
          disabled={busy || reason.trim() === ""}
          className="mt-2 inline-flex items-center gap-2 border border-rule-strong px-3 py-2 text-sm font-medium text-ink hover:bg-paper disabled:cursor-not-allowed disabled:border-rule disabled:text-ink-faint"
        >
          {deferPending ? chrome.workingLabel : chrome.deferButton}
        </button>
      </div>
      {redeemResult ? (
        <p role="status" className="mt-3 text-sm leading-6 text-ink-muted">
          <span>{chrome.approvedNote}</span>
          {" "}
          <bdi>{redeemResult.approval_fingerprint}</bdi>
          {" · "}
          {chrome.requestLabel}
          {": "}
          <bdi>{redeemResult.request_id}</bdi>
        </p>
      ) : null}
      {deferResult ? (
        <p role="status" className="mt-3 text-sm leading-6 text-ink-muted">
          <span>{chrome.deferredNote}</span>
          {" "}
          {chrome.requestLabel}
          {": "}
          <bdi>{deferResult.request_id}</bdi>
        </p>
      ) : null}
      {deferError ? (
        <p role="alert" className="mt-3 text-sm leading-6 text-warning">
          <bdi dir="ltr">{deferError.code}</bdi>
          {": "}
          <bdi dir="ltr">{deferError.message}</bdi>
        </p>
      ) : null}
      {publishResult ? (
        <p role="status" className="mt-3 text-sm leading-6 text-ink-muted">
          <span>{chrome.publishedNote}</span>
          {" "}
          <bdi>{publishResult.generation_id}</bdi>
        </p>
      ) : null}
      {publishError ? (
        <p role="alert" className="mt-3 text-sm leading-6 text-warning">
          <bdi dir="ltr">{publishError.code}</bdi>
          {": "}
          <bdi dir="ltr">{publishError.message}</bdi>
        </p>
      ) : null}
      <PairingDialog
        locale={locale}
        open={dialogOpen}
        pending={redeemPending}
        serverError={redeemError}
        snapshotFingerprint={stagedFingerprint}
        onClose={() => setDialogOpen(false)}
        onSubmit={handleRedeem}
      />
    </section>
  );
}

export function ScreeningPage({ locale }: Readonly<{ locale: Locale }>) {
  const [mode, setMode] = useState<SourceMode>({ kind: "fixture" });
  const [live, setLive] = useState<LiveState>({ status: "idle" });

  useEffect(() => {
    // Fixture is the default and stays request-free: this effect only arms
    // the live source when the URL explicitly asks for it, so the default
    // render performs no request and changes no state.
    const rawOrigin = readLiveOrigin();
    if (rawOrigin === null) return;
    let origin: string;
    try {
      origin = consoleBase(rawOrigin);
    } catch (error: unknown) {
      const failure: ScreeningApiError = error as ScreeningApiError;
      setMode({ kind: "live", origin: rawOrigin });
      setLive({ status: "error", origin: rawOrigin, error: failure });
      return;
    }
    setMode({ kind: "live", origin });
    setLive({ status: "loading", origin });
    let cancelled = false;
    (async () => {
      try {
        const [summary, batches, publication] = await Promise.all([
          getProjectSummary(origin),
          getScreeningBatches(origin),
          getPublicationStatus(origin),
        ]);
        if (cancelled) return;
        const first = batches.batches[0];
        if (batches.count === 0 || first === undefined) {
          setLive({ status: "empty", origin, batches });
          return;
        }
        const [rows, refs] = await Promise.all([
          getBatchRows(origin, first.batch_index),
          getCriterionRefs(origin, first.batch_index),
        ]);
        if (cancelled) return;
        setLive({ status: "ready", origin, summary, batches, publication, rows, refs });
      } catch (error: unknown) {
        if (!cancelled) setLive({ status: "error", origin, error });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const chrome = LIVE_CHROME[locale];
  const liveActive = mode.kind === "live";

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8 lg:py-14">
        {/* ---- masthead: eyebrow in the leading margin, as on the overview --- */}
        <section className="grid gap-x-8 gap-y-3 lg:grid-cols-[9rem_minmax(0,1fr)]">
          <p className="text-[0.6875rem] uppercase leading-5 tracking-[0.16em] text-evidence rtl:tracking-normal rtl:text-[0.75rem]">
            {translate(locale, "screening.eyebrow")}
          </p>
          <div className="min-w-0">
            <h1 className="max-w-3xl font-display text-3xl leading-tight text-ink lg:text-4xl">
              {translate(locale, "screening.heading")}
            </h1>
            <p className="mt-4 max-w-3xl text-lg leading-8 text-ink-muted">
              {translate(locale, "screening.lede")}
            </p>
          </div>
        </section>

        {liveActive ? (
          /* ---- the live source: console data over HTTP, never the record ---- */
          <section className="mt-14" aria-labelledby="screening-live-title">
            <div className="mb-5">
              <p className="mb-3">
                <span
                  aria-hidden="true"
                  className="inline-flex items-center border border-evidence/45 px-2 py-0.5 text-[0.6875rem] font-medium uppercase leading-4 tracking-[0.12em] text-evidence rtl:tracking-normal rtl:text-[0.75rem]"
                >
                  {chrome.liveStamp}
                </span>
              </p>
              <h2 id="screening-live-title" className="font-display text-xl leading-8 text-ink">
                {chrome.liveStamp}
              </h2>
              <p className="mt-1 text-sm leading-6 text-ink-muted">{chrome.liveLede}</p>
            </div>
            {live.status === "idle" || live.status === "loading" ? (
              <p role="status" className="text-sm leading-6 text-ink-muted">
                {translate(locale, "overview.recordLoading")}
              </p>
            ) : live.status === "error" ? (
              <LiveErrorBody locale={locale} error={live.error} />
            ) : live.status === "empty" ? (
              <div>
                <p className="text-sm leading-6 text-ink-muted">{chrome.liveEmpty}</p>
                <ul className="mt-3 border-t border-rule-strong">
                  {live.batches.missing.map((entry, index) => (
                    <li key={index} className="border-b border-rule py-4 text-sm leading-6 text-ink-muted">
                      <bdi dir="ltr">{entry.reason}</bdi>
                      {entry.file ? (
                        <>
                          {" — "}
                          <bdi dir="ltr">{entry.file}</bdi>
                        </>
                      ) : null}
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              <LiveReadyBody
                locale={locale}
                origin={live.origin}
                batchIndex={live.rows.batch_index}
                summary={live.summary}
                batches={live.batches}
                publication={live.publication}
                rows={live.rows}
                refs={live.refs}
              />
            )}
          </section>
        ) : (
          <>
            {/* ---- the record: citation and abstract, as a ruled definition list -- */}
            <section className="mt-14" aria-labelledby="screening-record-title">
              <div className="mb-5">
                <h2 id="screening-record-title" className="font-display text-xl leading-8 text-ink">
                  {translate(locale, "screening.recordHeading")}
                </h2>
              </div>
              <dl className="border-t border-rule-strong">
                <div className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-[9rem_minmax(0,1fr)]">
                  <dt className="text-sm font-medium leading-6 text-ink">
                    {translate(locale, "screening.citationLabel")}
                  </dt>
                  <dd className="min-w-0 text-sm leading-6 text-ink-muted">
                    <bdi>{demoScreeningRecord.citation}</bdi>
                  </dd>
                </div>
                <div className="grid gap-x-6 gap-y-1 border-b border-rule py-4 lg:grid-cols-[9rem_minmax(0,1fr)]">
                  <dt className="text-sm font-medium leading-6 text-ink">
                    {translate(locale, "screening.abstractLabel")}
                  </dt>
                  <dd className="min-w-0 text-sm leading-6 text-ink-muted">
                    <bdi>{demoScreeningRecord.abstract}</bdi>
                  </dd>
                </div>
              </dl>
            </section>

            {/* ---- the sealed criteria, numbered in the reader's own numerals ----- */}
            <section className="mt-14" aria-labelledby="screening-criteria-title">
              <div className="mb-5">
                <h2 id="screening-criteria-title" className="font-display text-xl leading-8 text-ink">
                  {translate(locale, "screening.criteriaHeading")}
                </h2>
                <p className="mt-1 text-sm leading-6 text-ink-muted">
                  {translate(locale, "screening.criteriaLede")}
                </p>
              </div>
              <ol className="border-t border-rule-strong">
                {demoScreeningRecord.criteria.map((criterion, index) => (
                  <li
                    key={criterion}
                    className="grid grid-cols-[1.5rem_minmax(0,1fr)] gap-x-3 border-b border-rule py-4 lg:grid-cols-[1.75rem_minmax(0,1fr)] lg:gap-x-5"
                  >
                    {/*
                      The marginal ordinal, the same treatment the evidence trail
                      uses: a real element holding `Intl` output, aligned to the
                      inline end with a logical utility so it sits on the same side
                      of the text in `ar` as in `en`.
                    */}
                    <span className="pt-0.5 text-end text-[0.6875rem] leading-4 text-ink-faint rtl:text-[0.75rem]">
                      {formatNumber(locale, index + 1)}
                    </span>
                    <div className="min-w-0 border-s border-rule-strong ps-3 lg:ps-5">
                      <p className="text-sm leading-6 text-ink">
                        <bdi>{criterion}</bdi>
                      </p>
                    </div>
                  </li>
                ))}
              </ol>
            </section>
          </>
        )}

        {/* ---- the decision -------------------------------------------------- */}
        <section className="mt-14" aria-labelledby="screening-decision-title">
          <div className="mb-5">
            <h2 id="screening-decision-title" className="font-display text-xl leading-8 text-ink">
              {translate(locale, "screening.decisionHeading")}
            </h2>
          </div>
          <ScreeningForm locale={locale} />
        </section>
      </div>
    </div>
  );
}
