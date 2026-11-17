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
import { DatabasePicker } from "@/components/database-picker";
import { DiffersLine, ProviderUnknownCard, pickerItems, pickerLabels, protocolList, readDatabasesParam, sameList } from "@/components/discovery-plan";
import {
  cancelJob,
  finishPreparation,
  getPlan,
  getRun,
  getRuns,
  preparationUnfinished,
  startRun,
  type DiscoveryJob,
  type Plan,
  type Preparation,
  type RunDetail,
  type RunRequest,
  type Runs,
  type SearchLeg,
} from "@/lib/discovery-api";
import { getCorpus, type Corpus } from "@/lib/screening-v1";
import { discoveryT, providerName, type DiscoveryCopyKey } from "@/lib/discovery-copy";

/**
 * 03 Harvest (spec `docs/ux/phase1-discovery/final/03-harvest.md`): start the
 * search the protocol selects (`POST /discovery/runs`), follow each database as
 * the engine reports it, stop the whole harvest if needed, and read how each
 * database ended. One Cancel for the whole harvest: the engine has no stop for
 * a single database. A finished browser run is not frozen; the hand-off is.
 *
 * M10a (decided 2026-11-14, item 2a): the databases of this harvest are chosen
 * and ordered with the picker, pre-filled from `?databases=` (the Plan's link)
 * or the protocol. Start sends `providers` only once the picker was touched or
 * the address carried a choice; untouched, the run uses the protocol's list.
 *
 * M3i-harvest-robustness: the search is one of four steps; duplicates, abstracts
 * and checks follow it, and only the last makes the works the hand-off needs.
 * The screen reads each run's `preparation` (the engine's stage marker, the same
 * after the console restarted): it names the step while a job runs, says when
 * those steps failed, were stopped or never ended, and offers "Finish preparing
 * this corpus" (`POST /discovery/runs/{run}/prepare`), which searches nothing
 * again. Stop stays available in every step; after the search it takes effect
 * when the current step ends.
 */

const LEG_CODES = new Set(["PROVIDER_RATE_LIMITED", "PROVIDER_TIMEOUT", "PROVIDER_UNAVAILABLE", "PROVIDER_REFUSED"]);

/**
 * A database that finished `ok` with nothing fetched while it reported no
 * results (0, or no total): "0 results", never "Done". A database that
 * reported more than 0 but sent nothing keeps "Done" and its counts (M10a).
 */
export function isZeroLeg(leg: { status: string; fetched: number; reported_total?: number | null }): boolean {
  return leg.status === "ok" && leg.fetched === 0 && (leg.reported_total == null || leg.reported_total === 0);
}

function legRole(leg: { status: string; cap_hit: boolean; fetched: number; reported_total: number | null }): DecisionRole {
  if (leg.status === "failed") return "blocked";
  if (leg.status === "stopped") return "exclude";
  if (leg.cap_hit || isZeroLeg(leg)) return "unclear";
  return "include";
}

export function LegRow({ locale, leg, full }: Readonly<{ locale: Locale; leg: LegView; full?: SearchLeg }>) {
  const t = discoveryT(locale);
  const statusKey = `harvest.leg.status.${isZeroLeg(leg) ? "none" : leg.status}` as DiscoveryCopyKey;
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
        {/* M10a (PRISMA-S): the query this database received, as the leg recorded it. */}
        {full?.executed_query ? (
          <div className="mt-1">
            <p className="text-xs text-ink-muted">{t("harvest.leg.query")}</p>
            <code dir="ltr" className="block font-mono text-[0.8125rem] leading-[1.125rem] text-ink [overflow-wrap:anywhere]" data-leg-query>
              {full.executed_query}
            </code>
          </div>
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
  // M3i: a "finish preparing" request is being sent; the run the running job prepares (for its lede).
  const [finishing, setFinishing] = useState(false);
  const [jobRun, setJobRun] = useState<string | null>(null);
  // M10a: `?databases=` read after hydration (like `?run=`); the picker's choice; whether it was touched.
  const [address, setAddress] = useState<{ ready: boolean; value: string[] | null }>({ ready: false, value: null });
  const [choice, setChoice] = useState<string[] | null>(null);
  const [touched, setTouched] = useState(false);
  // M10a: the databases this page's Start asked, in order (the `providers` sent, else the protocol's list); null after a reattach.
  const [startedWith, setStartedWith] = useState<string[] | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const capField = useRef<HTMLInputElement>(null);
  // "Reset to the protocol" removes the button pressed (the card, or the reset once nothing differs):
  // focus goes to the h1, as soon as it is on the page (M10a).
  const focusHeading = useRef(false);

  useEffect(() => {
    setAddress({ ready: true, value: readDatabasesParam() });
  }, []);

  useEffect(() => {
    if (focusHeading.current && heading.current) {
      focusHeading.current = false;
      heading.current.focus();
    }
  });

  const load = useCallback(async () => {
    setLoadError(null);
    try {
      // A choice in the address is read through the plan, which checks it (`PROVIDER_UNKNOWN`).
      const [nextRuns, nextPlan] = await Promise.all([getRuns(origin), getPlan(origin, address.value)]);
      setRuns(nextRuns);
      setPlan(nextPlan);
      setChoice((current) => current ?? nextPlan.requested_providers ?? protocolList(nextPlan));
      const active = nextRuns.active_job;
      // M3i: a search and a "finish preparing" job are both followed here.
      const harvestJob = !!active && (active.kind === "run" || active.kind === "prepare");
      if (active && harvestJob) {
        setJobId(active.job_id);
        setJobRun(nextRuns.runs.find((r) => r.preparation?.job_id === active.job_id)?.run ?? null);
      }
      setOtherJob(active && !harvestJob ? active : null);
    } catch (error) {
      setLoadError(refusalOf(error));
    }
    getCorpus(origin).then(setCorpus, () => undefined);
  }, [origin, address.value]);

  useEffect(() => {
    if (ready && address.ready) void load();
  }, [ready, address.ready, load]);

  /** "Reset to the protocol": the protocol's list, untouched, and no address choice (so no `providers`). */
  const resetChoice = () => {
    focusHeading.current = true;
    setTouched(false);
    setStartError(null);
    setChoice(plan ? protocolList(plan) : null);
    if (address.value) setAddress({ ready: true, value: null });
  };

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
      setJobRun(null);
      setStartedWith(null);
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
  // M3i: the job is in the steps after the search (a search that ended, or a "finish preparing" job).
  const finishJob = stream.job?.kind === "prepare";
  const preparingJob = running && (finishJob || discoveryDone);

  const start = async () => {
    setStartError(null);
    setCapError(false);
    const body: RunRequest = {};
    // M10a: the chosen databases, in order, once touched or carried by the address; else the protocol's list.
    if ((touched || address.value) && choice) body.providers = choice;
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
      setStartedWith(body.providers ?? (plan ? protocolList(plan) : null));
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

  /** "Finish preparing this corpus": the remaining steps from the run's saved records, no search. */
  const finish = async () => {
    if (!selected) return;
    setStartError(null);
    setFinishing(true);
    try {
      const { job } = await finishPreparation(origin, selected);
      setLastJob(null);
      setStartedWith(null);
      setJobRun(selected);
      setJobId(job.job_id);
    } catch (error) {
      setStartError(refusalOf(error));
    } finally {
      setFinishing(false);
    }
  };

  const follow = (refusal: Refusal) => {
    const job = (refusal.details as { job?: DiscoveryJob } | undefined)?.job;
    if (job?.kind === "run" || job?.kind === "prepare") {
      setStartError(null);
      setStartedWith(null);
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
  const protocol = plan ? protocolList(plan) : [];
  // The databases the selected run asked: its `requested_providers` when it carries them (a stopped
  // run's legs can be a strict prefix of that list), else the protocol's list and whatever legs it has.
  // A protocol database it did not ask reads "Not selected for this harvest." (the report's `not_selected_for_run`).
  const asked = new Set(detail?.requested_providers ?? [...protocol, ...(detail?.legs ?? []).map((l) => l.provider)]);
  const notAsked = (plan?.providers ?? [])
    .filter((p) => !asked.has(p.name))
    .map((p) => ({
      name: p.name,
      text:
        detail?.requested_providers && protocol.includes(p.name)
          ? t("harvest.leg.notChosen")
          : p.status === "off_by_default"
            ? t("harvest.leg.offByDefault")
            : t("harvest.leg.notSelected"),
    }));
  // M3i: the steps after the selected run's search, as the engine reads them from its marker. The
  // runs list is read first after a job ends, so it wins over the run detail still on screen.
  const preparation: Preparation | null = summary?.preparation ?? detail?.preparation ?? null;
  const unfinished = !running && preparationUnfinished(preparation);
  // A job that failed after its search is told by the preparation card, not as a failed search.
  const jobError = lastJob?.state === "failed" && !unfinished ? lastJob.error : null;
  const title = running
    ? preparingJob
      ? t("harvest.title.preparing")
      : t("harvest.title.running")
    : unfinished && preparation
      ? t(`harvest.title.prep.${preparation.state}` as DiscoveryCopyKey)
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
        <Button variant={selected ? "secondary" : "primary"} onClick={() => void start()} disabled={starting || !choice?.length} data-start>
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

  // M10a: the database picker ("What will be searched"), the line naming how the choice differs, and the reset.
  const picker =
    plan && choice ? (
      <div className="mt-3 space-y-3" data-harvest-picker>
        <DatabasePicker
          items={pickerItems(locale)}
          value={choice}
          onChange={(next) => {
            setChoice(next);
            setTouched(true);
          }}
          labels={pickerLabels(locale)}
        />
        <DiffersLine locale={locale} chosen={choice} protocol={protocol} />
        {!sameList(choice, protocol) ? (
          <Button onClick={resetChoice} data-picker-reset>
            {t("plan.picker.reset")}
          </Button>
        ) : null}
      </div>
    ) : null;

  return (
    <DiscoveryFrame locale={locale} current="harvest" origin={origin} run={wanted}>
      {loadError && !runs ? (
        loadError.code === "PROVIDER_UNKNOWN" ? (
          <ProviderUnknownCard locale={locale} refusal={loadError} origin={origin} onReset={resetChoice} pageHeading />
        ) : (
          <DiscoveryRefusal locale={locale} refusal={loadError} origin={origin} onRetry={() => void load()} pageHeading />
        )
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
                <DecisionBadge role="include">{stopping ? t("harvest.badge.stopping") : preparingJob ? t("harvest.badge.preparing") : t("harvest.badge.running")}</DecisionBadge>
              </p>
            ) : summary ? (
              <p className="mt-2 flex flex-wrap items-center gap-2 text-ink" data-headline>
                {/* M3i: the search's own status is not shown as a green badge under a title that says the corpus is not prepared. */}
                {unfinished ? null : <DecisionBadge role={summary.status === "PARTIAL" ? "unclear" : "include"}>{statusText(locale, summary.status)}</DecisionBadge>}
                <span>{t("harvest.headline", { fetched: summary.fetched_total, legs: summary.legs_total })}</span>
              </p>
            ) : null}
            {!running ? <RunSelector locale={locale} runs={runs.runs} selected={selected} origin={origin} step="harvest" /> : null}
            {!running && !unfinished ? <OlderRunNote locale={locale} summary={summary} newest={newest} /> : null}
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
              {startError.code === "PROVIDER_UNKNOWN" ? (
                <ProviderUnknownCard locale={locale} refusal={startError} origin={origin} onReset={resetChoice} />
              ) : (
                <DiscoveryRefusal locale={locale} refusal={startError} origin={origin} onRetry={["MAILTO_NOT_SET", "OPENALEX_KEY_NOT_SET", "PREPARATION_NOT_AVAILABLE"].includes(startError.code) ? () => { setStartError(null); void load(); } : undefined} />
              )}
              {startError.code === "DISCOVERY_JOB_ACTIVE" && ["run", "prepare"].includes((startError.details as { job?: DiscoveryJob } | undefined)?.job?.kind ?? "") ? (
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
                {finishJob ? (
                  <p role="status" className="text-ink" data-preparing>
                    <bdi>{t("harvest.preparing.lede", { run: jobRun ?? selected })}</bdi>
                  </p>
                ) : stream.legs.length ? (
                  <LegTable locale={locale} legs={stream.legs} />
                ) : (
                  <p role="status">{t("harvest.reading")}</p>
                )}
                {/* Picker Loading (M10a): while the run runs, the picker gives way to the databases asked, in order. */}
                {startedWith?.length ? <AskedList locale={locale} names={startedWith} protocol={protocol} /> : null}
                <Stages locale={locale} stages={stream.stages} />
              </section>
              <aside className="rounded-lg border border-rule bg-leaf p-5">
                <h2 className="font-semibold text-ink">{t("harvest.stop.title")}</h2>
                {/* M3i: Stop in every step. After the search the engine reads it before the next step starts. */}
                {preparingJob ? (
                  <p className="mt-2 text-sm text-ink" data-stop-late>
                    {t("harvest.stop.late")}
                  </p>
                ) : (
                  <p className="mt-2 text-sm text-ink">{t("harvest.stop.body")}</p>
                )}
                <Button className="mt-3" onClick={() => void stop()} disabled={stopping} data-stop>
                  {preparingJob ? t("harvest.stop.prepare") : t("harvest.stop")}
                </Button>
              </aside>
            </div>
          ) : !selected ? (
            <div className="grid gap-6 lg:grid-cols-3">
              <section aria-labelledby="harvest-will" className="rounded-lg border border-rule bg-leaf p-5 min-w-0 lg:col-span-2">
                <h2 id="harvest-will" className="font-semibold text-ink">
                  {t("harvest.willSearch")}
                </h2>
                {picker}
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
                  {detail.requested_providers?.length ? (
                    <div className="mt-3">
                      <AskedList locale={locale} names={detail.requested_providers} protocol={protocol} />
                    </div>
                  ) : null}
                  {notAsked.length ? (
                    <ul className="mt-3 space-y-1 text-sm text-ink-muted">
                      {notAsked.map((p) => (
                        <li key={p.name} data-not-asked={p.name}>
                          {providerName(p.name)} · {p.text}
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
                {unfinished && preparation ? (
                  <>
                    <PreparationCard locale={locale} preparation={preparation} onFinish={() => void finish()} busy={finishing} />
                    <p>
                      <a className={LINK} href={discoveryHref(locale, "report", origin, selected)}>
                        {t("harvest.next.report")}
                      </a>
                    </p>
                  </>
                ) : null}
                {newest && !unfinished ? (
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
                    <>
                      <section aria-labelledby="harvest-again-will" className="rounded-lg border border-rule bg-leaf p-5">
                        <h2 id="harvest-again-will" className="font-semibold text-ink">
                          {t("harvest.willSearch")}
                        </h2>
                        {picker}
                      </section>
                      {form}
                    </>
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

const PREPARATION_STAGES = ["deduplication", "hydration", "verification"];

/**
 * M3i: the steps after the search did not end (`failed`, `stopped` or `interrupted`). Says which
 * step, in the engine's own record, shows the engine's message under Details, and offers the one
 * action: finish from the saved records. Nothing here is computed by the browser.
 */
function PreparationCard({ locale, preparation, onFinish, busy }: Readonly<{ locale: Locale; preparation: Preparation; onFinish: () => void; busy: boolean }>) {
  const t = discoveryT(locale);
  const stageName = (stage: string | null): string | null =>
    stage && PREPARATION_STAGES.includes(stage) ? t(`harvest.stage.${stage}` as DiscoveryCopyKey) : stage;
  const state = preparation.state as "failed" | "stopped" | "interrupted";
  const stage = stageName(preparation.stage);
  const ended = PREPARATION_STAGES.filter((name) => name in preparation.stages);
  return (
    <section
      aria-labelledby="harvest-prep"
      className="rounded-lg border border-rule-strong bg-leaf p-5"
      data-preparation={state}
      data-preparation-stage={preparation.stage ?? ""}
    >
      <h2 id="harvest-prep" className="font-semibold text-ink">
        {t("harvest.prep.card")}
      </h2>
      <p className="mt-2">
        <DecisionBadge role={state === "failed" ? "blocked" : "unclear"}>{t(`harvest.prep.badge.${state}` as DiscoveryCopyKey)}</DecisionBadge>
      </p>
      <p className="mt-2 text-sm text-ink" data-preparation-body>
        {state !== "interrupted" && stage ? t(`harvest.prep.${state}` as DiscoveryCopyKey, { stage }) : t("harvest.prep.interrupted")}
      </p>
      {state === "interrupted" && stage ? <p className="mt-1 text-sm text-ink">{t("harvest.prep.interruptedAt", { stage })}</p> : null}
      {preparation.marker ? (
        <div className="mt-3 text-sm">
          <h3 className="text-ink-muted">{t("harvest.prep.ended")}</h3>
          {ended.length ? (
            <ul className="mt-1 list-disc ps-5 text-ink">
              {ended.map((name) => (
                <li key={name} data-stage-ended={name}>
                  {stageName(name)}
                </li>
              ))}
            </ul>
          ) : (
            <p className="mt-1 text-ink">{t("harvest.prep.noneEnded")}</p>
          )}
        </div>
      ) : (
        <p className="mt-2 text-sm text-ink-muted" data-no-marker>
          {t("harvest.prep.noMarker")}
        </p>
      )}
      {preparation.message ? (
        <details className="mt-2 text-xs">
          <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-ink-muted">{DETAILS_LABEL[locale]}</summary>
          <p className="text-ink-muted">{t("harvest.prep.error")}</p>
          <p className="font-mono text-blocked [overflow-wrap:anywhere]" dir="ltr" data-preparation-message>
            {preparation.message}
          </p>
        </details>
      ) : null}
      {preparation.can_finish ? (
        <>
          <Button variant="primary" className="mt-4" onClick={onFinish} disabled={busy} data-finish>
            {t("harvest.prep.finish")}
          </Button>
          <p className="mt-2 text-xs text-ink-muted">{t("harvest.prep.finishHelp")}</p>
        </>
      ) : (
        <p className="mt-3 text-sm text-ink" data-cannot-finish={preparation.cannot_finish ?? ""}>
          {preparation.cannot_finish === "corpus_accepted" ? t("harvest.prep.cannotFinishAccepted") : t("harvest.prep.cannotFinish")}
        </p>
      )}
    </section>
  );
}

/** "Databases asked, in order" (M10a): a run's asked list, and the line naming how it differs from the protocol. */
function AskedList({ locale, names, protocol }: Readonly<{ locale: Locale; names: readonly string[]; protocol: readonly string[] }>) {
  const t = discoveryT(locale);
  return (
    <div data-asked-list>
      <h3 className="text-sm font-semibold text-ink">{t("harvest.asked.title")}</h3>
      <ol className="mt-1 list-decimal space-y-1 ps-5 text-sm text-ink">
        {names.map((name) => (
          <li key={name} data-asked={name}>
            {providerName(name)}
          </li>
        ))}
      </ol>
      <div className="mt-2">
        <DiffersLine locale={locale} chosen={names} protocol={protocol} />
      </div>
    </div>
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
