"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge, type DecisionRole } from "@/components/ui/base";
import { DETAILS_LABEL } from "@/components/screening-state-card";
import {
  ConnectionLost,
  DiscoveryFrame,
  DiscoveryRefusal,
  Eyebrow,
  LINK,
  Loading,
  MailtoCard,
  OlderRunNote,
  RunSelector,
  discoveryHref,
  refusalOf,
  stamp,
  statusText,
  useDiscoveryParams,
  useJobStream,
  type LegView,
  type Refusal,
} from "@/components/discovery-frame";
import { cancelJob, getPlan, getRun, getRuns, startRun, type DiscoveryJob, type Plan, type RunDetail, type Runs, type SearchLeg } from "@/lib/discovery-api";
import { getCorpus, type Corpus } from "@/lib/screening-v1";
import { discoveryT, providerName, type DiscoveryCopyKey } from "@/lib/discovery-copy";

/**
 * 03 Harvest (spec `docs/ux/phase1-discovery/final/03-harvest.md`): start the
 * search the protocol selects (`POST /discovery/runs`), follow each database as
 * the engine reports it, stop the whole harvest if needed, and read how each
 * database ended. One Cancel for the whole harvest: the engine has no stop for
 * a single database. A finished browser run is not frozen; the hand-off is.
 */

const LEG_CODES = new Set(["PROVIDER_RATE_LIMITED", "PROVIDER_TIMEOUT", "PROVIDER_UNAVAILABLE", "PROVIDER_REFUSED"]);

function legRole(leg: { status: string; cap_hit: boolean }): DecisionRole {
  if (leg.status === "failed") return "blocked";
  if (leg.status === "stopped") return "exclude";
  if (leg.cap_hit) return "unclear";
  return "include";
}

export function LegRow({ locale, leg, full }: Readonly<{ locale: Locale; leg: LegView; full?: SearchLeg }>) {
  const t = discoveryT(locale);
  const statusKey = `harvest.leg.status.${leg.status}` as DiscoveryCopyKey;
  const known = ["ok", "running", "failed", "stopped"].includes(leg.status);
  const count = leg.cap_hit
    ? t("lowerBound", { n: leg.fetched })
    : leg.reported_total == null
      ? t("harvest.count.unknown", { fetched: leg.fetched })
      : t("harvest.count.of", { fetched: leg.fetched, reported: leg.reported_total });
  const capSource = full?.cap_source;
  return (
    <tr className="border-t border-rule align-top" data-leg={leg.provider} data-leg-status={leg.status}>
      <th scope="row" className="py-2 pe-3 text-start font-medium text-ink">
        {providerName(leg.provider)}
      </th>
      <td className="py-2 pe-3">
        <bdi data-count>
          {count}
        </bdi>
        {leg.cap_hit && leg.reported_total != null ? (
          <span className="block text-xs text-ink-muted">
            <bdi>{t("harvest.count.of", { fetched: leg.fetched, reported: leg.reported_total })}</bdi>
          </span>
        ) : null}
      </td>
      <td className="py-2 pe-3">
        <DecisionBadge role={legRole(leg)}>{known ? t(statusKey) : leg.status}</DecisionBadge>
      </td>
      <td className="py-2 text-sm text-ink">
        {leg.status === "failed" ? (
          <>
            <p data-leg-error={leg.error_code ?? ""}>{leg.error_code && LEG_CODES.has(leg.error_code) ? t(`harvest.leg.code.${leg.error_code}` as DiscoveryCopyKey) : t("harvest.leg.failedNoCode")}</p>
            <details className="text-xs">
              <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-ink-muted">{DETAILS_LABEL[locale]}</summary>
              {leg.error_code ? (
                <p className="font-mono text-blocked" dir="ltr">
                  {leg.error_code}
                </p>
              ) : null}
              {full?.error ? (
                <p className="text-ink-muted" dir="ltr">
                  {full.error}
                </p>
              ) : null}
            </details>
          </>
        ) : leg.status === "stopped" ? (
          <p>{t("harvest.leg.stopped")}</p>
        ) : leg.cap_hit ? (
          <p data-lower-bound>{t("harvest.leg.capped")}</p>
        ) : null}
        {capSource && ["protocol", "run_override", "query", "engine_ceiling"].includes(capSource) ? (
          <p className="text-xs text-ink-muted" data-cap-source={capSource}>
            {t(`harvest.leg.capSource.${capSource}` as DiscoveryCopyKey)}
          </p>
        ) : null}
      </td>
    </tr>
  );
}

export function LegTable({ locale, legs, full }: Readonly<{ locale: Locale; legs: LegView[]; full?: SearchLeg[] }>) {
  const t = discoveryT(locale);
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[32rem] text-sm">
        <caption className="pb-2 text-start font-semibold text-ink">{t("harvest.legs.title")}</caption>
        <thead>
          <tr className="text-start text-xs text-ink-muted">
            <th scope="col" className="pb-2 pe-3 text-start">
              {t("harvest.col.database")}
            </th>
            <th scope="col" className="pb-2 pe-3 text-start">
              {t("harvest.col.count")}
            </th>
            <th scope="col" className="pb-2 pe-3 text-start">
              {t("harvest.col.status")}
            </th>
            <th scope="col" className="pb-2 text-start">
              {t("harvest.col.detail")}
            </th>
          </tr>
        </thead>
        <tbody>
          {legs.map((leg) => (
            <LegRow key={leg.provider} locale={locale} leg={leg} full={full?.find((l) => l.provider === leg.provider)} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function DiscoveryHarvest({ locale }: Readonly<{ locale: Locale }>) {
  const t = discoveryT(locale);
  const { origin, run: wanted, ready } = useDiscoveryParams();
  const [plan, setPlan] = useState<Plan | null>(null);
  const [runs, setRuns] = useState<Runs | null>(null);
  const [corpus, setCorpus] = useState<Corpus | null>(null);
  const [detail, setDetail] = useState<RunDetail | null>(null);
  const [loadError, setLoadError] = useState<Refusal | null>(null);
  const [detailError, setDetailError] = useState<Refusal | null>(null);
  const [startError, setStartError] = useState<Refusal | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [lastJob, setLastJob] = useState<DiscoveryJob | null>(null);
  const [otherJob, setOtherJob] = useState<DiscoveryJob | null>(null);
  const [cap, setCap] = useState("");
  const [note, setNote] = useState("");
  const [capError, setCapError] = useState(false);
  const [starting, setStarting] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [again, setAgain] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const capField = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    setLoadError(null);
    try {
      const [nextRuns, nextPlan] = await Promise.all([getRuns(origin), getPlan(origin)]);
      setRuns(nextRuns);
      setPlan(nextPlan);
      const active = nextRuns.active_job;
      if (active && active.kind === "run") setJobId(active.job_id);
      setOtherJob(active && active.kind !== "run" ? active : null);
    } catch (error) {
      setLoadError(refusalOf(error));
    }
    getCorpus(origin).then(setCorpus, () => undefined);
  }, [origin]);

  useEffect(() => {
    if (ready) void load();
  }, [ready, load]);

  const selected = wanted || runs?.runs[0]?.run || "";
  const newest = !!runs && runs.runs[0]?.run === selected;

  useEffect(() => {
    if (!ready || !selected) {
      setDetail(null);
      return;
    }
    setDetailError(null);
    getRun(origin, selected).then(setDetail, (error) => {
      setDetail(null);
      setDetailError(refusalOf(error));
    });
  }, [ready, origin, selected, runs]);

  const onEnd = useCallback(
    (job: DiscoveryJob | null) => {
      setLastJob(job);
      setJobId(null);
      setStopping(false);
      setAgain(false);
      void load();
      heading.current?.focus();
    },
    [load],
  );
  const stream = useJobStream(origin, jobId, onEnd);
  const running = !!jobId && !stream.ended;
  const discoveryDone = stream.stages.some((s) => s.stage === "discovery");

  const start = async () => {
    setStartError(null);
    setCapError(false);
    const body: { cap_override?: number; note?: string } = {};
    if (cap.trim()) {
      if (!/^\d+$/.test(cap.trim())) {
        setCapError(true);
        capField.current?.focus();
        return;
      }
      body.cap_override = Number(cap.trim());
    }
    if (note.trim()) body.note = note.trim();
    setStarting(true);
    try {
      const { job } = await startRun(origin, body);
      setLastJob(null);
      setJobId(job.job_id);
    } catch (error) {
      const refusal = refusalOf(error);
      if (refusal.code === "CAP_INVALID") {
        setCapError(true);
        capField.current?.focus();
      }
      if (refusal.code === "CORPUS_ALREADY_ACCEPTED") getCorpus(origin).then(setCorpus, () => undefined);
      setStartError(refusal);
    } finally {
      setStarting(false);
    }
  };

  const stop = async () => {
    if (!jobId) return;
    setStopping(true);
    try {
      await cancelJob(origin, jobId);
    } catch (error) {
      setStartError(refusalOf(error));
      setStopping(false);
    }
  };

  const follow = (refusal: Refusal) => {
    const job = (refusal.details as { job?: DiscoveryJob } | undefined)?.job;
    if (job?.kind === "run") {
      setStartError(null);
      setJobId(job.job_id);
    }
  };

  const accepted = corpus?.state === "ACCEPTED";
  const summary = runs?.runs.find((r) => r.run === selected);
  const legsFromDetail: LegView[] = (detail?.legs ?? []).map((l) => ({
    provider: l.provider, fetched: l.fetched, reported_total: l.reported_total, cap: l.cap, cap_hit: l.cap_hit, status: l.status, error_code: l.error_code ?? null,
  }));
  const changed =
    !!detail && !!plan && (detail.query_text !== plan.query.text || (detail.year_min ?? null) !== plan.query.year_min || (detail.year_max ?? null) !== plan.query.year_max);
  const unselected = plan?.providers.filter((p) => !p.selected) ?? [];
  const jobError = lastJob?.state === "failed" ? lastJob.error : null;
  const title = running
    ? t("harvest.title.running")
    : lastJob?.state === "cancelled"
      ? t("harvest.title.cancelled")
      : lastJob?.state === "failed"
        ? t("harvest.title.failed")
        : !selected
          ? t("harvest.title.ready")
          : newest
            ? summary?.status === "PARTIAL" && detail?.legs.some((l) => l.status === "stopped")
              ? t("harvest.title.cancelled")
              : t("harvest.title.finished")
            : t("harvest.title.older", { run: selected });
  const showReadyForm = !accepted && !running && !selected;

  const form = (
    <section aria-labelledby="harvest-form" className="rounded-lg border border-rule bg-leaf p-5" data-harvest-form>
      <h2 id="harvest-form" className="font-semibold text-ink">
        {t("harvest.form.title")}
      </h2>
      <label className="mt-3 block text-sm text-ink" htmlFor="harvest-cap">
        {t("harvest.form.cap")}
      </label>
      <input
        id="harvest-cap"
        ref={capField}
        inputMode="numeric"
        value={cap}
        onChange={(e) => setCap(e.target.value)}
        aria-invalid={capError || undefined}
        aria-describedby="harvest-cap-help"
        className="mt-1 min-h-11 w-40 rounded-md border border-rule-strong bg-paper px-3 text-ink"
        dir="ltr"
      />
      <p id="harvest-cap-help" className="mt-1 text-xs text-ink-muted">
        {capError ? t("harvest.form.capInvalid", { ceiling: plan?.cap.ceiling ?? 10000 }) + " " : ""}
        {t("harvest.form.capHelp", { value: plan?.cap.value ?? "", ceiling: plan?.cap.ceiling ?? 10000 })}
      </p>
      <label className="mt-3 block text-sm text-ink" htmlFor="harvest-note">
        {t("harvest.form.note")}
      </label>
      <textarea
        id="harvest-note"
        value={note}
        maxLength={2000}
        onChange={(e) => setNote(e.target.value)}
        aria-describedby="harvest-note-help"
        dir="auto"
        rows={2}
        className="mt-1 w-full rounded-md border border-rule-strong bg-paper px-3 py-2 text-ink"
      />
      <p id="harvest-note-help" className="mt-1 text-xs text-ink-muted">
        {t("harvest.form.noteHelp")}
      </p>
      <div className="mt-4">
        <Button variant={selected ? "secondary" : "primary"} onClick={() => void start()} disabled={starting} data-start>
          {selected ? t("harvest.again") : t("harvest.start")}
        </Button>
      </div>
      <p className="mt-3 text-xs text-ink-muted">{t("job.keepOpen")}</p>
      {!selected && corpus && corpus.state === "EMPTY" ? (
        <p className="mt-2 text-xs text-ink-muted" data-warn-imports>
          {t("harvest.warn.imports")}{" "}
          <a className={LINK} href={discoveryHref(locale, "import", origin)}>
            {t("steps.import")}
          </a>
        </p>
      ) : null}
    </section>
  );

  return (
    <DiscoveryFrame locale={locale} current="harvest" origin={origin} run={wanted}>
      {loadError && !runs ? (
        <DiscoveryRefusal locale={locale} refusal={loadError} origin={origin} onRetry={() => void load()} pageHeading />
      ) : !runs || !plan ? (
        <Loading locale={locale} />
      ) : (
        <div className="space-y-6">
          <header>
            <Eyebrow
              locale={locale}
              step="harvest"
              name={t("harvest.eyebrowName")}
              extra={
                running && stream.job ? (
                  <bdi dir="ltr" className="ms-2 normal-case">
                    · {stamp(stream.job.started_at)}
                  </bdi>
                ) : null
              }
            />
            <h1 ref={heading} tabIndex={-1} className="mt-2 font-display text-3xl text-ink" aria-live="polite">
              {title}
            </h1>
            {!selected && !running ? <p className="mt-2 max-w-2xl text-ink-muted">{t("harvest.lede.ready")}</p> : null}
            {running ? (
              <p className="mt-2">
                <DecisionBadge role="include">{stopping ? t("harvest.badge.stopping") : t("harvest.badge.running")}</DecisionBadge>
              </p>
            ) : summary ? (
              <p className="mt-2 flex flex-wrap items-center gap-2 text-ink" data-headline>
                <DecisionBadge role={summary.status === "PARTIAL" ? "unclear" : "include"}>{statusText(locale, summary.status)}</DecisionBadge>
                <span>{t("harvest.headline", { fetched: summary.fetched_total, legs: summary.legs_total })}</span>
              </p>
            ) : null}
            {!running ? <RunSelector locale={locale} runs={runs.runs} selected={selected} origin={origin} step="harvest" /> : null}
            {!running ? <OlderRunNote locale={locale} summary={summary} newest={newest} /> : null}
          </header>

          {otherJob ? (
            <p className="rounded-lg border border-rule bg-leaf p-3 text-ink" data-other-job>
              {t("job.otherKind")}{" "}
              <a className={LINK} href={discoveryHref(locale, "recall", origin)}>
                {t("job.openRecall")}
              </a>
            </p>
          ) : null}
          {startError ? (
            <div className="space-y-2">
              <DiscoveryRefusal locale={locale} refusal={startError} origin={origin} onRetry={startError.code === "MAILTO_NOT_SET" || startError.code === "OPENALEX_KEY_NOT_SET" ? () => { setStartError(null); void load(); } : undefined} />
              {startError.code === "DISCOVERY_JOB_ACTIVE" && (startError.details as { job?: DiscoveryJob } | undefined)?.job?.kind === "run" ? (
                <Button onClick={() => follow(startError)}>{t("job.follow")}</Button>
              ) : null}
            </div>
          ) : null}
          {jobError ? <DiscoveryRefusal locale={locale} refusal={{ code: jobError.code, message: jobError.message, details: jobError.details }} origin={origin} /> : null}
          {stream.error ? <DiscoveryRefusal locale={locale} refusal={stream.error} origin={origin} /> : null}
          {stream.lost ? <ConnectionLost locale={locale} lastAt={stream.lastAt} onRetry={stream.retry} /> : null}
          {accepted ? (
            <p className="rounded-lg border border-rule bg-leaf p-3 text-ink" data-accepted>
              {t("harvest.accepted")}
            </p>
          ) : null}

          {running ? (
            <div className="grid gap-6 lg:grid-cols-3">
              <section className="space-y-4 rounded-lg border border-rule bg-leaf p-5 min-w-0 lg:col-span-2" data-live>
                {stream.legs.length ? <LegTable locale={locale} legs={stream.legs} /> : <p role="status">{t("harvest.reading")}</p>}
                <Stages locale={locale} stages={stream.stages} />
              </section>
              <aside className="rounded-lg border border-rule bg-leaf p-5">
                <h2 className="font-semibold text-ink">{t("harvest.stop.title")}</h2>
                <p className="mt-2 text-sm text-ink">{t("harvest.stop.body")}</p>
                {discoveryDone ? (
                  <p className="mt-3 text-sm text-ink-muted" data-stop-late>
                    {t("harvest.stop.late")}
                  </p>
                ) : (
                  <Button className="mt-3" onClick={() => void stop()} disabled={stopping} data-stop>
                    {t("harvest.stop")}
                  </Button>
                )}
              </aside>
            </div>
          ) : !selected ? (
            <div className="grid gap-6 lg:grid-cols-3">
              <section aria-labelledby="harvest-will" className="rounded-lg border border-rule bg-leaf p-5 min-w-0 lg:col-span-2">
                <h2 id="harvest-will" className="font-semibold text-ink">
                  {t("harvest.willSearch")}
                </h2>
                <ul className="mt-3 space-y-1 text-ink">
                  {plan.providers.map((p) => (
                    <li key={p.name} data-will={p.name}>
                      {providerName(p.name)}
                      {!p.selected ? <span className="text-sm text-ink-muted"> · {p.status === "off_by_default" ? t("harvest.leg.offByDefault") : t("harvest.leg.notSelected")}</span> : null}
                    </li>
                  ))}
                </ul>
                <p className="mt-3 text-sm text-ink-muted">
                  {t("plan.limits.cap")}: <bdi dir="ltr">{plan.cap.value}</bdi> ·{" "}
                  {plan.cap.source === "protocol" ? t("harvest.leg.capSource.protocol") : t("harvest.leg.capSource.engine_ceiling")}
                </p>
                {!plan.mailto_set ? (
                  <div className="mt-4">
                    <MailtoCard locale={locale} onCheck={() => void load()} />
                  </div>
                ) : null}
              </section>
              <aside>{showReadyForm ? form : null}</aside>
            </div>
          ) : detailError && !detail ? (
            <DiscoveryRefusal locale={locale} refusal={detailError} origin={origin} />
          ) : !detail ? (
            <Loading locale={locale} />
          ) : (
            <div className="grid gap-6 lg:grid-cols-3">
              <div className="space-y-4 min-w-0 lg:col-span-2">
                {changed ? (
                  <p className="rounded-lg border border-rule bg-leaf p-3 text-ink" data-run-changed>
                    {t("harvest.changed")}
                  </p>
                ) : null}
                <section className="rounded-lg border border-rule bg-leaf p-5" data-run={detail.run}>
                  <LegTable locale={locale} legs={legsFromDetail} full={detail.legs} />
                  {detail.legs.some((l) => l.status === "failed") ? (
                    <p className="mt-3 text-sm text-ink" data-failed-list>
                      {detail.legs
                        .filter((l) => l.status === "failed")
                        .map((l) => providerName(l.provider))
                        .join(", ")}
                      : {t("harvest.failedList")}
                    </p>
                  ) : null}
                  {unselected.length ? (
                    <ul className="mt-3 space-y-1 text-sm text-ink-muted">
                      {unselected.map((p) => (
                        <li key={p.name}>
                          {providerName(p.name)} · {p.status === "off_by_default" ? t("harvest.leg.offByDefault") : t("harvest.leg.notSelected")}
                        </li>
                      ))}
                    </ul>
                  ) : null}
                  <p className="mt-3 text-xs text-ink-muted">{t("harvest.saved")}</p>
                </section>
                {stream.stages.length ? <Stages locale={locale} stages={stream.stages} /> : null}
                <section className="rounded-lg border border-rule bg-leaf p-5 text-sm text-ink">
                  <p data-recall-line>
                    {detail.recall_check
                      ? t("harvest.recall.line", { found: detail.recall_check.found ?? "", total: detail.recall_check.total ?? "", date: stamp(detail.recall_check.checked_at) })
                      : t("harvest.recall.none")}
                  </p>
                  {detail.cap_override != null ? (
                    <p className="mt-2" data-cap-override>
                      {t("harvest.capOverride.line", { value: detail.cap_override })}
                    </p>
                  ) : null}
                  {(detail.notes ?? []).length ? (
                    <p className="mt-2">
                      {t("harvest.note.label")}: <bdi dir="auto">{(detail.notes ?? []).join(" · ")}</bdi>
                    </p>
                  ) : null}
                </section>
              </div>
              <aside className="space-y-4">
                {newest ? (
                  <section className="rounded-lg border border-rule bg-leaf p-5" data-next-links>
                    <a className="inline-flex min-h-11 items-center rounded-md bg-brand px-4 font-medium text-on-brand" href={discoveryHref(locale, "dedup", origin)}>
                      {t("harvest.next.dedup")}
                    </a>
                    <p className="mt-2">
                      <a className={LINK} href={discoveryHref(locale, "report", origin)}>
                        {t("harvest.next.report")}
                      </a>
                    </p>
                    <p>
                      <a className={LINK} href={discoveryHref(locale, "handoff", origin)}>
                        {t("harvest.next.handoff")}
                      </a>
                    </p>
                  </section>
                ) : null}
                {newest && !accepted ? (
                  again ? (
                    form
                  ) : (
                    <section className="rounded-lg border border-rule bg-leaf p-5">
                      <p className="text-sm text-ink-muted">{t("harvest.againHelp")}</p>
                      <Button className="mt-3" onClick={() => setAgain(true)} data-again>
                        {t("harvest.again")}
                      </Button>
                    </section>
                  )
                ) : null}
              </aside>
            </div>
          )}
        </div>
      )}
    </DiscoveryFrame>
  );
}

function Stages({ locale, stages }: Readonly<{ locale: Locale; stages: { stage: string; status: string; detail: unknown }[] }>) {
  const t = discoveryT(locale);
  if (!stages.length) return null;
  return (
    <section aria-labelledby="harvest-stages" data-stages>
      <h2 id="harvest-stages" className="font-semibold text-ink">
        {t("harvest.stages.title")}
      </h2>
      <ol className="mt-2 space-y-1 text-sm">
        {stages.map((s) => {
          const known = ["discovery", "deduplication", "verification", "hydration", "corpus_snapshot"].includes(s.stage);
          return (
            <li key={s.stage} data-stage={s.stage}>
              <span className="text-ink">{known ? t(`harvest.stage.${s.stage}` as DiscoveryCopyKey) : s.stage}</span>{" "}
              <span className="font-mono text-[0.8125rem] text-ink-muted" dir="ltr">
                {s.status}
              </span>
              {s.stage === "corpus_snapshot" ? <span className="block text-ink-muted">{t("harvest.stage.corpusNotFrozen")}</span> : null}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
