"use client";

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

import type { Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge } from "@/components/ui/base";
import { StateCard } from "@/components/screening-state-card";
import { refusalOf, stamp, type Refusal } from "@/components/inception-frame";
import { getJob, streamJob, type DiscoveryJob, type JobEvent, type RunSummary } from "@/lib/discovery-api";
import { discoveryT, type DiscoveryCopyKey } from "@/lib/discovery-copy";

/**
 * What every discovery screen shares (spec 01 "Shared by 01–08", M3c-screens):
 * the address parameters read after hydration, the step bar, the run selector,
 * the job stream hook and the refusal card. Every number a screen prints comes
 * from a route answer; nothing here counts.
 */

export { refusalOf, stamp, type Refusal };

export type DiscoveryStep = "plan" | "recall" | "harvest" | "import" | "dedup" | "report" | "handoff";

const STEPS: { step: DiscoveryStep; key: DiscoveryCopyKey }[] = [
  { step: "plan", key: "steps.plan" },
  { step: "recall", key: "steps.recall" },
  { step: "harvest", key: "steps.harvest" },
  { step: "import", key: "steps.import" },
  { step: "dedup", key: "steps.dedup" },
  { step: "report", key: "steps.report" },
  { step: "handoff", key: "steps.handoff" },
];

/** The step's number (1–7) for the eyebrow. */
export function stepNumber(step: DiscoveryStep): number {
  return STEPS.findIndex((s) => s.step === step) + 1;
}

/**
 * `?console=` and `?run=`, read after hydration: the pages are prerendered
 * without a query string, so the first render prints neither (as the inception
 * screens do), then the screen updates.
 */
export function useDiscoveryParams(): { origin: string; run: string; ready: boolean } {
  const [params, setParams] = useState({ origin: "", run: "", ready: false });
  useEffect(() => {
    const query = new URLSearchParams(window.location.search);
    setParams({ origin: query.get("console") ?? "", run: query.get("run") ?? "", ready: true });
  }, []);
  return params;
}

/** The link to one discovery screen, keeping the console override and, when given, the run. */
export function discoveryHref(locale: Locale, step: DiscoveryStep | "", origin = "", run = ""): string {
  if (step === "import") {
    const query = new URLSearchParams({ return: "discovery" });
    if (origin) query.set("console", origin);
    return `/${locale}/screening/import?${query.toString()}`;
  }
  const query = new URLSearchParams();
  if (run) query.set("run", run);
  if (origin) query.set("console", origin);
  const q = query.toString();
  return `/${locale}/discovery/${step ? `${step}/` : ""}${q ? `?${q}` : ""}`;
}

export function screeningHomeHref(locale: Locale, origin = ""): string {
  return `/${locale}/screening/home${origin ? `?console=${encodeURIComponent(origin)}` : ""}`;
}

export const LINK = "inline-flex min-h-11 items-center text-brand underline";

export type StepMarks = Partial<Record<DiscoveryStep, "done" | "earlier" | "none">>;

export function DiscoverySteps({
  locale,
  current,
  origin,
  run = "",
  marks,
}: Readonly<{ locale: Locale; current?: DiscoveryStep; origin: string; run?: string; marks?: StepMarks }>) {
  const t = discoveryT(locale);
  return (
    <nav aria-label={t("steps.label")} className="mb-6" data-discovery-steps>
      <ol className="flex flex-wrap gap-2 text-sm">
        <li>
          <a className="inline-flex min-h-11 items-center px-3 text-brand underline" href={`/${locale}/workspaces${origin ? `?console=${encodeURIComponent(origin)}` : ""}`}>
            {t("steps.workspaces")}
          </a>
        </li>
        <li>
          <a className="inline-flex min-h-11 items-center px-3 text-brand underline" href={discoveryHref(locale, "", origin)} data-overview-link>
            {t("steps.overview")}
          </a>
        </li>
        {STEPS.map(({ step, key }) => {
          const mark = marks?.[step];
          return (
            <li key={step}>
              <a
                href={discoveryHref(locale, step, origin, step === "harvest" || step === "report" ? run : "")}
                aria-current={step === current ? "step" : undefined}
                data-step={step}
                className={`inline-flex min-h-11 items-center gap-2 rounded-md border px-3 ${step === current ? "border-brand bg-brand-soft text-brand" : "border-rule text-ink"}`}
              >
                {t(key)}
                {mark === "done" ? (
                  <span className="text-xs text-include" data-mark="done">
                    <span aria-hidden="true">✓ </span>
                    {t("steps.done")}
                  </span>
                ) : mark === "earlier" ? (
                  <span className="text-xs text-unclear" data-mark="earlier">
                    {t("steps.earlierProtocol")}
                  </span>
                ) : null}
              </a>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}

/** The page frame: the step bar, then the screen. */
export function DiscoveryFrame({
  locale,
  current,
  origin,
  run = "",
  marks,
  children,
}: Readonly<{ locale: Locale; current?: DiscoveryStep; origin: string; run?: string; marks?: StepMarks; children: ReactNode }>) {
  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8 lg:py-12">
      <DiscoverySteps locale={locale} current={current} origin={origin} run={run} marks={marks} />
      {children}
    </div>
  );
}

export function Eyebrow({ locale, step, name, extra }: Readonly<{ locale: Locale; step: DiscoveryStep; name: string; extra?: ReactNode }>) {
  const t = discoveryT(locale);
  return (
    <p className="text-xs font-semibold uppercase tracking-[0.05em] text-brand rtl:tracking-normal" data-eyebrow>
      {t("eyebrow", { n: stepNumber(step), name })}
      {extra}
    </p>
  );
}

export function Loading({ locale }: Readonly<{ locale: Locale }>) {
  return (
    <p role="status" aria-busy="true" className="text-ink-muted">
      {discoveryT(locale)("loading")}
    </p>
  );
}

/** A refusal as a sentence (the shared state card); the engine's message stays under Details when the card does not know the code. */
export function DiscoveryRefusal({
  locale,
  refusal,
  origin = "",
  onRetry,
  pageHeading = false,
}: Readonly<{ locale: Locale; refusal: Refusal; origin?: string; onRetry?: () => void; pageHeading?: boolean }>) {
  return (
    <div data-refusal={refusal.code} className="space-y-2">
      <StateCard locale={locale} code={refusal.code} message={refusal.message} consoleOrigin={origin} onRetry={onRetry} pageHeading={pageHeading} />
    </div>
  );
}

/** The contact-email state (decision 5): the exact line to set, where to put it, and Check again. The browser writes no setting. */
export function MailtoCard({ locale, onCheck }: Readonly<{ locale: Locale; onCheck?: () => void }>) {
  const t = discoveryT(locale);
  return (
    <div className="rounded-lg border border-rule bg-leaf p-4" data-mailto>
      <p className="font-semibold text-ink">
        {t("mailto.title")}: <DecisionBadge role="unclear">{t("plan.limits.mailto.notSet")}</DecisionBadge>
      </p>
      <p className="mt-2">
        <code className="rounded-sm bg-paper px-2 py-1 font-mono text-[0.8125rem] text-ink" dir="ltr" data-mailto-line>
          {t("mailto.line")}
        </code>
      </p>
      <p className="mt-2 text-sm text-ink-muted">{t("mailto.where")}</p>
      {onCheck ? (
        <Button className="mt-3" onClick={onCheck}>
          {t("mailto.check")}
        </Button>
      ) : null}
    </div>
  );
}

/**
 * F12 (M3h-providers): OpenAlex requires an API key since 2026-02-13. Printed
 * like the contact email: the exact line to set, never a settings form.
 */
export function OpenAlexKeyCard({ locale, onCheck }: Readonly<{ locale: Locale; onCheck?: () => void }>) {
  const t = discoveryT(locale);
  return (
    <div className="rounded-lg border border-rule bg-leaf p-4" data-openalex-key>
      <p className="font-semibold text-ink">
        {t("openalexKey.title")}: <DecisionBadge role="unclear">{t("plan.limits.mailto.notSet")}</DecisionBadge>
      </p>
      <p className="mt-2">
        <code className="rounded-sm bg-paper px-2 py-1 font-mono text-[0.8125rem] text-ink" dir="ltr" data-openalex-key-line>
          {t("openalexKey.line")}
        </code>
      </p>
      <p className="mt-2 text-sm text-ink-muted">{t("openalexKey.where")}</p>
      {onCheck ? (
        <Button className="mt-3" onClick={onCheck}>
          {t("mailto.check")}
        </Button>
      ) : null}
    </div>
  );
}

/** The run's status as words, by a fixed table; an unknown status prints as itself. */
export function statusText(locale: Locale, status: string | null | undefined): string {
  if (!status) return "";
  const key = `status.${status}` as DiscoveryCopyKey;
  const t = discoveryT(locale);
  return key in STATUS_KEYS ? t(key) : status;
}

const STATUS_KEYS: Record<string, true> = Object.fromEntries(
  ["PENDING_CORPUS_ACCEPT", "PARTIAL", "CANCELLED", "COMPLETED", "FAILED"].map((s) => [`status.${s}`, true]),
);

/**
 * The run selector (spec 01): the runs as the engine lists them, newest first;
 * the newest is selected when the address names none. Each option is a link,
 * so the choice lives in the address (`?run=`).
 */
export function RunSelector({
  locale,
  runs,
  selected,
  origin,
  step,
}: Readonly<{ locale: Locale; runs: RunSummary[]; selected: string; origin: string; step: DiscoveryStep }>) {
  const t = discoveryT(locale);
  if (!runs.length) return null;
  return (
    <details className="mt-3 text-sm" data-run-selector>
      <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-ink">
        {t("run.label")}: <DataCell>{selected}</DataCell>
      </summary>
      <ul className="mt-1 space-y-1">
        {runs.map((r, index) => (
          <li key={r.run}>
            <a
              className={`${LINK} gap-2`}
              href={discoveryHref(locale, step, origin, index === 0 ? "" : r.run)}
              aria-current={r.run === selected ? "true" : undefined}
              data-run-option={r.run}
            >
              <bdi>{t("run.option", { run: r.run, date: stamp(r.started_at), status: statusText(locale, r.status) })}</bdi>
              {r.stale ? <DecisionBadge role="unclear">{t("run.stale")}</DecisionBadge> : null}
            </a>
          </li>
        ))}
      </ul>
    </details>
  );
}

/** The stale or older-run marker for the selected run. */
export function OlderRunNote({ locale, summary, newest }: Readonly<{ locale: Locale; summary: RunSummary | undefined; newest: boolean }>) {
  const t = discoveryT(locale);
  if (!summary || newest) return null;
  return (
    <div className="mt-3 rounded-lg border border-rule bg-leaf p-3 text-sm" data-older-run>
      {summary.stale ? (
        <p>
          <DecisionBadge role="unclear">{t("run.stale")}</DecisionBadge> <span className="text-ink">{t("run.staleBody")}</span>
        </p>
      ) : null}
      <p className="text-ink-muted">{t("run.readonly")}</p>
    </div>
  );
}

export type LegView = { provider: string; fetched: number; reported_total: number | null; cap: number | null; cap_hit: boolean; status: string; error_code: string | null };
export type StageView = { stage: string; status: string; detail: unknown };

export interface JobStreamState {
  job: DiscoveryJob | null;
  legs: LegView[];
  stages: StageView[];
  ended: boolean;
  lost: boolean;
  lastAt: string;
  error: Refusal | null;
}

const EMPTY: JobStreamState = { job: null, legs: [], stages: [], ended: false, lost: false, lastAt: "", error: null };

function now(): string {
  return new Date().toISOString();
}

/**
 * Follow one discovery job (spec 01, job streams). The stream replays from the
 * start on every connect, so each connection rebuilds the state from its own
 * events: the last `leg` event per database wins, each `stage` once. On a drop
 * it reconnects once; after a second drop it keeps the last state, marks it
 * "connection lost", reads the job once and offers Retry. It never loops.
 */
export function useJobStream(origin: string, jobId: string | null, onEnd?: (job: DiscoveryJob | null) => void): JobStreamState & { retry: () => void } {
  const [state, setState] = useState<JobStreamState>(EMPTY);
  const [attempt, setAttempt] = useState(0);
  const endRef = useRef(onEnd);
  endRef.current = onEnd;

  useEffect(() => {
    if (!jobId) {
      setState(EMPTY);
      return;
    }
    const controller = new AbortController();
    let cancelled = false;

    const connect = async (drops: number): Promise<void> => {
      let view: JobStreamState = { ...EMPTY };
      const legs = new Map<string, LegView>();
      const stages = new Map<string, StageView>();
      const apply = (event: JobEvent) => {
        if (event.event === "snapshot" || event.event === "done" || event.event === "failed") view = { ...view, job: event.data.job, ended: event.event !== "snapshot" };
        else if (event.event === "leg") {
          const { job_id: _ignored, ...leg } = event.data;
          legs.set(leg.provider, leg);
        } else if (event.event === "stage") stages.set(event.data.stage, { stage: event.data.stage, status: event.data.status, detail: event.data.detail });
        view = { ...view, legs: [...legs.values()], stages: [...stages.values()], lastAt: now(), lost: false, error: null };
        if (!cancelled) setState(view);
      };
      try {
        const result = await streamJob(origin, jobId, apply, controller.signal);
        if (cancelled) return;
        if (result.ended) {
          endRef.current?.(view.job);
          return;
        }
        // The stream closed before the job ended: a drop.
        throw new Error("STREAM_DROPPED");
      } catch (error) {
        if (cancelled) return;
        const refusal = refusalOf(error);
        if (refusal.code === "DISCOVERY_JOB_NOT_FOUND") {
          setState((s) => ({ ...s, error: refusal }));
          return;
        }
        if (drops === 0) return connect(1);
        // Second drop: keep the last state, read the job once.
        try {
          const { job } = await getJob(origin, jobId, controller.signal);
          if (cancelled) return;
          if (job.state !== "running") {
            setState((s) => ({ ...s, job, ended: true, lost: false }));
            endRef.current?.(job);
            return;
          }
        } catch (readError) {
          if (cancelled) return;
          const read = refusalOf(readError);
          if (read.code === "DISCOVERY_JOB_NOT_FOUND") {
            setState((s) => ({ ...s, error: read }));
            return;
          }
        }
        setState((s) => ({ ...s, lost: true, lastAt: s.lastAt || now() }));
      }
    };
    void connect(0);
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [origin, jobId, attempt]);

  const retry = useCallback(() => setAttempt((n) => n + 1), []);
  return { ...state, retry };
}

/** "Connection lost · as of …" with the one Retry action. */
export function ConnectionLost({ locale, lastAt, onRetry }: Readonly<{ locale: Locale; lastAt: string; onRetry: () => void }>) {
  const t = discoveryT(locale);
  return (
    <div role="alert" className="flex flex-wrap items-center gap-3 rounded-lg border border-rule bg-leaf p-3" data-connection-lost>
      <p className="text-ink">
        <bdi>{t("job.connectionLost", { time: stamp(lastAt) })}</bdi>
      </p>
      <Button onClick={onRetry}>{t("job.retry")}</Button>
    </div>
  );
}

/** A count that stopped at the cap is never shown bare: "at least N". */
export function countText(locale: Locale, n: number | null | undefined, capped: boolean): string {
  if (n === null || n === undefined) return "";
  return capped ? discoveryT(locale)("lowerBound", { n }) : String(n);
}

/** A fraction the harness wrote, shown as a percentage for reading (the written value goes under Details). */
export function percent(fraction: number): string {
  return `${Math.round(fraction * 10000) / 100} %`;
}
