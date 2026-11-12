"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge, GatePanel, type DecisionRole } from "@/components/ui/base";
import { DETAILS_LABEL, StateCard } from "@/components/screening-state-card";
import {
  ConnectionLost,
  DiscoveryFrame,
  DiscoveryRefusal,
  LINK,
  Loading,
  OpenAlexKeyCard,
  discoveryHref,
  refusalOf,
  screeningHomeHref,
  stamp,
  useDiscoveryParams,
  useJobStream,
  type LegView,
  type Refusal,
} from "@/components/discovery-frame";
import {
  acceptChase,
  cancelJob,
  getChase,
  getChaseRun,
  startChase,
  type ChaseAcceptAnswer,
  type ChaseLeg,
  type ChaseRequest,
  type ChaseRun,
  type ChaseState,
  type DiscoveryJob,
} from "@/lib/discovery-api";
import { discoveryT, providerName, type DiscoveryCopyKey } from "@/lib/discovery-copy";

/**
 * 09 Citation chase (spec `docs/ux/phase1-discovery/final/09-chase.md`, M3g):
 * after the screening is published, chase the citations of the included
 * studies (`POST /discovery/chase/runs`, a job in the console process), read
 * what is new, and send it to screening as the next round
 * (`POST /discovery/chase/accept`), the one gate of this screen. Every count is
 * the engine's; the browser sums nothing (the per-database rows are the
 * engine's `legs_summary`). The accepted state is shown only from the engine's
 * answer.
 */

const LEG_CODES = new Set(["PROVIDER_RATE_LIMITED", "PROVIDER_TIMEOUT", "PROVIDER_UNAVAILABLE", "PROVIDER_REFUSED"]);
const STATUSES = new Set(["SUCCESS", "PARTIAL", "FAILED", "EMPTY_RESULT"]);
const CEILING_MAX = 10000;

type Direction = "both" | "forward" | "backward";

function legRole(leg: { status: string; cap_hit: boolean }): DecisionRole {
  if (leg.status === "failed") return "blocked";
  if (leg.status === "skipped") return "exclude";
  if (leg.cap_hit) return "unclear";
  return "include";
}

function isOffline(code: string): boolean {
  return code === "ENGINE_UNREACHABLE" || code === "CONSOLE_UNREACHABLE" || code === "CONSOLE_TIMEOUT";
}

function roundFolder(n: number): string {
  return `literature/screening_rounds/round_${String(n).padStart(3, "0")}/`;
}

export function DiscoveryChase({ locale }: Readonly<{ locale: Locale }>) {
  const t = discoveryT(locale);
  const { origin, run: wanted, ready } = useDiscoveryParams();
  const [state, setState] = useState<ChaseState | null>(null);
  const [detail, setDetail] = useState<ChaseRun | null>(null);
  const [loadError, setLoadError] = useState<Refusal | null>(null);
  const [detailError, setDetailError] = useState<Refusal | null>(null);
  const [startError, setStartError] = useState<Refusal | null>(null);
  const [acceptError, setAcceptError] = useState<Refusal | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [lastJob, setLastJob] = useState<DiscoveryJob | null>(null);
  const [answer, setAnswer] = useState<ChaseAcceptAnswer | null>(null);
  const [offline, setOffline] = useState(false);
  const [starting, setStarting] = useState(false);
  const [stopping, setStopping] = useState(false);
  const [accepting, setAccepting] = useState(false);
  const [again, setAgain] = useState(false);
  const [direction, setDirection] = useState<Direction>("both");
  const [cap, setCap] = useState("");
  const [ceiling, setCeiling] = useState("");
  const [note, setNote] = useState("");
  const [capError, setCapError] = useState(false);
  const [ceilingError, setCeilingError] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const capField = useRef<HTMLInputElement>(null);
  const ceilingField = useRef<HTMLInputElement>(null);

  const load = useCallback(async () => {
    setLoadError(null);
    try {
      const next = await getChase(origin);
      setState(next);
      setOffline(false);
      const active = next.active_job;
      if (active && active.kind === "chase") setJobId(active.job_id);
    } catch (error) {
      const r = refusalOf(error);
      if (isOffline(r.code)) setOffline(true);
      setLoadError(r);
    }
  }, [origin]);

  useEffect(() => {
    if (ready) void load();
  }, [ready, load]);

  const latest = state?.latest ?? null;
  const selected = wanted || latest?.chase || "";
  const newest = !wanted || wanted === latest?.chase;

  useEffect(() => {
    if (!state) return;
    setDetailError(null);
    if (!selected) {
      setDetail(null);
      return;
    }
    if (newest) {
      setDetail(latest);
      return;
    }
    getChaseRun(origin, selected).then(setDetail, (error) => {
      setDetail(null);
      setDetailError(refusalOf(error));
    });
  }, [state, selected, newest, latest, origin]);

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

  const defaults = state?.defaults;

  const start = async () => {
    setStartError(null);
    setCapError(false);
    setCeilingError(false);
    const body: ChaseRequest = {};
    if (direction !== "both") body.directions = [direction];
    if (cap.trim()) {
      if (!/^\d+$/.test(cap.trim()) || Number(cap.trim()) < 1 || Number(cap.trim()) > CEILING_MAX) {
        setCapError(true);
        capField.current?.focus();
        return;
      }
      if (Number(cap.trim()) !== defaults?.forward_cap) body.cap_per_seed = Number(cap.trim());
    }
    if (ceiling.trim()) {
      if (!/^\d+$/.test(ceiling.trim()) || Number(ceiling.trim()) < 1 || Number(ceiling.trim()) > CEILING_MAX) {
        setCeilingError(true);
        ceilingField.current?.focus();
        return;
      }
      if (Number(ceiling.trim()) !== defaults?.run_ceiling) body.ceiling = Number(ceiling.trim());
    }
    if (note.trim()) body.note = note.trim();
    setStarting(true);
    try {
      const { job } = await startChase(origin, body);
      setLastJob(null);
      setAnswer(null);
      setJobId(job.job_id);
    } catch (error) {
      const r = refusalOf(error);
      if (isOffline(r.code)) setOffline(true);
      if (r.code === "OPENALEX_KEY_NOT_SET" || r.code === "SCREENING_NOT_PUBLISHED") void load();
      setStartError(r);
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
    if (job?.kind === "chase") {
      setStartError(null);
      setJobId(job.job_id);
    }
  };

  const accept = async () => {
    if (!detail) return;
    setAccepting(true);
    setAcceptError(null);
    try {
      const result = await acceptChase(origin, detail.chase);
      setAnswer(result);
      await load();
      heading.current?.focus();
    } catch (error) {
      const r = refusalOf(error);
      if (isOffline(r.code)) setOffline(true);
      if (r.code === "CHASE_ALREADY_ACCEPTED") {
        await load();
        heading.current?.focus();
      } else {
        setAcceptError(r);
      }
    } finally {
      setAccepting(false);
    }
  };

  const published = !!state?.screening.published;
  const round = state?.screening.round ?? 1;
  const seeds = state?.seeds;
  const keys = state?.keys;
  const otherJob = state?.active_job && state.active_job.kind !== "chase" ? state.active_job : null;
  const accepted = detail?.accepted ?? null;
  const counts = detail?.counts ?? null;
  const cancelled = lastJob?.state === "cancelled" || !!detail?.cancelled;
  const failedRun = !running && (lastJob?.state === "failed" || detail?.status === "FAILED");
  const nothingNew = !!detail && detail.published && !!counts && counts.new === 0;
  const canAccept = !!detail && detail.published && !!counts && counts.new > 0 && !accepted && newest && published && !cancelled;
  const startBlocked = !seeds || seeds.chaseable === 0 ? "noSeeds" : keys && !keys.openalex_key_set ? "key" : state?.active_job ? "job" : offline ? "offline" : null;

  const statusText = (status: string | null | undefined): string =>
    status && STATUSES.has(status) ? t(`chase.status.${status}` as DiscoveryCopyKey) : (status ?? "");
  const directionText = (d: string): string => (d === "forward" ? t("chase.dir.forward") : d === "backward" ? t("chase.dir.backward") : d);
  const seedTitle = (study: string): string => detail?.seeds.find((s) => s.study_id === study)?.title ?? study;
  const jobError = lastJob?.state === "failed" ? lastJob.error : null;

  const title = running
    ? t("chase.title.running")
    : accepted
      ? t("chase.title.accepted", { round: accepted.round })
      : cancelled && newest
        ? t("chase.title.cancelled")
        : failedRun && newest
          ? t("chase.title.failed")
          : !detail
            ? t("chase.title.ready")
            : !newest
              ? t("chase.title.older", { chase: detail.chase })
              : nothingNew
                ? t("chase.title.nothingNew")
                : t("chase.title.finished");

  const eyebrow = (
    <p className="text-xs font-semibold uppercase tracking-[0.05em] text-brand rtl:tracking-normal" data-eyebrow>
      {running && stream.job
        ? t("chase.eyebrowRun", { chase: detail?.chase ?? "", date: stamp(stream.job.started_at) }).replace(" ·  ·", " ·")
        : detail
          ? t("chase.eyebrowRun", { chase: detail.chase, date: stamp(detail.started_at) })
          : t("chase.eyebrow", { round })}
    </p>
  );

  const form = (
    <section aria-labelledby="chase-options" className="rounded-lg border border-rule bg-leaf p-5" data-chase-form>
      <h2 id="chase-options" className="font-semibold text-ink">
        {t("chase.options.title")}
      </h2>
      <fieldset className="mt-3" aria-invalid={startError?.code === "CHASE_DIRECTION_INVALID" || undefined}>
        <legend className="text-sm text-ink">{t("chase.options.directions")}</legend>
        {(["both", "forward", "backward"] as Direction[]).map((d) => (
          <label key={d} className="mt-1 flex min-h-11 items-center gap-2 text-sm text-ink">
            <input type="radio" name="chase-direction" value={d} checked={direction === d} onChange={() => setDirection(d)} />
            {t(`chase.options.dir.${d}` as DiscoveryCopyKey)}
          </label>
        ))}
      </fieldset>
      <p className="mt-3 text-sm text-ink">
        {t("chase.options.providers")}: {(defaults?.providers ?? []).map(providerName).join(", ")}
      </p>
      <label className="mt-3 block text-sm text-ink" htmlFor="chase-cap">
        {t("chase.options.cap")}
      </label>
      <input
        id="chase-cap"
        ref={capField}
        inputMode="numeric"
        value={cap}
        placeholder={String(defaults?.forward_cap ?? "")}
        onChange={(e) => setCap(e.target.value)}
        aria-invalid={capError || undefined}
        aria-describedby="chase-cap-help"
        className="mt-1 min-h-11 w-40 rounded-md border border-rule-strong bg-paper px-3 text-ink"
        dir="ltr"
      />
      <p id="chase-cap-help" className="mt-1 text-xs text-ink-muted">
        {capError ? t("chase.options.invalid", { ceiling: CEILING_MAX }) + " " : ""}
        {t("chase.options.capHelp")}
      </p>
      <label className="mt-3 block text-sm text-ink" htmlFor="chase-ceiling">
        {t("chase.options.ceiling")}
      </label>
      <input
        id="chase-ceiling"
        ref={ceilingField}
        inputMode="numeric"
        value={ceiling}
        placeholder={String(defaults?.run_ceiling ?? "")}
        onChange={(e) => setCeiling(e.target.value)}
        aria-invalid={ceilingError || undefined}
        aria-describedby="chase-ceiling-help"
        className="mt-1 min-h-11 w-40 rounded-md border border-rule-strong bg-paper px-3 text-ink"
        dir="ltr"
      />
      <p id="chase-ceiling-help" className="mt-1 text-xs text-ink-muted">
        {ceilingError ? t("chase.options.invalid", { ceiling: CEILING_MAX }) + " " : ""}
        {t("chase.options.ceilingHelp", { ceiling: defaults?.run_ceiling ?? "" })}
      </p>
      <p className="mt-3 text-xs text-ink-muted" data-seed-source>
        {t("chase.options.seedSource", { source: t(seeds?.source === "included+unclear" ? "chase.seeds.source.includedUnclear" : "chase.seeds.source.included") })}
      </p>
      <label className="mt-3 block text-sm text-ink" htmlFor="chase-note">
        {t("chase.options.note")}
      </label>
      <textarea
        id="chase-note"
        value={note}
        maxLength={2000}
        onChange={(e) => setNote(e.target.value)}
        aria-describedby="chase-note-help"
        dir="auto"
        rows={2}
        className="mt-1 w-full rounded-md border border-rule-strong bg-paper px-3 py-2 text-ink"
      />
      <p id="chase-note-help" className="mt-1 text-xs text-ink-muted">
        {t("chase.options.noteHelp")}
      </p>
      <div className="mt-4">
        <Button
          variant={detail ? "secondary" : "primary"}
          onClick={() => void start()}
          disabled={starting || startBlocked !== null}
          aria-describedby={startBlocked ? "chase-start-why" : undefined}
          data-start
        >
          {detail ? t("chase.again") : t("chase.start")}
        </Button>
        {startBlocked ? (
          <p id="chase-start-why" className="mt-2 text-sm text-ink-muted" data-start-blocked={startBlocked}>
            {t(`chase.startDisabled.${startBlocked}` as DiscoveryCopyKey)}
          </p>
        ) : null}
      </div>
      <p className="mt-3 text-xs text-ink-muted">{t("chase.warn.console")}</p>
    </section>
  );

  const seedsCard = seeds ? (
    <section aria-labelledby="chase-seeds" className="rounded-lg border border-rule bg-leaf p-5 text-sm" data-seeds>
      <h2 id="chase-seeds" className="font-semibold text-ink">
        {t("chase.seeds.title")}
      </h2>
      <p className="mt-2 text-ink">{t(seeds.source === "included+unclear" ? "chase.seeds.source.includedUnclear" : "chase.seeds.source.included")}</p>
      <p className="mt-1 text-ink" data-seeds-count>
        {t("chase.seeds.count", { chaseable: seeds.chaseable, total: seeds.total })}
      </p>
      {seeds.not_chaseable.length ? (
        <details className="mt-2" data-not-chaseable>
          <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-ink">
            {t("chase.seeds.notChaseable.title")} ({seeds.not_chaseable.length})
          </summary>
          <ul className="mt-1 space-y-1 text-ink-muted">
            {seeds.not_chaseable.map((s) => (
              <li key={s.study_id} data-not-chaseable-row>
                <bdi dir="auto">{t("chase.seeds.notChaseable.row", { title: s.title, reason: s.reason ?? "" })}</bdi>
              </li>
            ))}
          </ul>
          <p className="mt-1 text-xs text-ink-muted">{t("chase.seeds.notChaseable.help")}</p>
        </details>
      ) : null}
    </section>
  ) : null;

  const keysCard = keys ? (
    <section aria-labelledby="chase-keys" className="rounded-lg border border-rule bg-leaf p-5 text-sm" data-keys>
      <h2 id="chase-keys" className="font-semibold text-ink">
        {t("chase.keys.title")}
      </h2>
      <p className="mt-2 text-ink" data-key-openalex={keys.openalex_key_set ? "set" : "missing"}>
        {keys.openalex_key_set ? <DecisionBadge role="include">{t("chase.keys.openalex.set")}</DecisionBadge> : <DecisionBadge role="unclear">{t("chase.keys.openalex.missing")}</DecisionBadge>}
      </p>
      {!keys.openalex_key_set ? (
        <div className="mt-2">
          <OpenAlexKeyCard locale={locale} onCheck={() => void load()} />
        </div>
      ) : null}
      <p className="mt-2 text-ink-muted" data-key-s2={keys.s2_key_set ? "set" : "none"}>
        {keys.s2_key_set ? t("chase.keys.s2.set") : t("chase.keys.s2.none")}
      </p>
    </section>
  ) : null;

  const liveLegs = (legs: LegView[]) => (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[40rem] text-sm">
        <caption className="pb-2 text-start font-semibold text-ink">{t("chase.legs.perSeed")}</caption>
        <thead>
          <tr className="text-start text-xs text-ink-muted">
            {(["seed", "provider", "direction", "fetched", "status", "detail"] as const).map((c) => (
              <th key={c} scope="col" className="pb-2 pe-3 text-start">
                {t(`chase.col.${c}` as DiscoveryCopyKey)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {legs.map((leg) => {
            const known = ["ok", "failed", "skipped", "running"].includes(leg.status);
            return (
              <tr key={`${leg.seed}|${leg.provider}|${leg.direction}`} className="border-t border-rule align-top" data-leg={`${leg.provider}|${leg.direction}`} data-leg-status={leg.status}>
                <th scope="row" className="py-2 pe-3 text-start font-medium text-ink">
                  <bdi dir="auto">{seedTitle(leg.seed ?? "")}</bdi>
                </th>
                <td className="py-2 pe-3 text-ink">{providerName(leg.provider)}</td>
                <td className="py-2 pe-3 text-ink">{directionText(leg.direction ?? "")}</td>
                <td className="py-2 pe-3">
                  <bdi dir="ltr" data-count>
                    {leg.cap_hit ? t("lowerBound", { n: leg.fetched }) : leg.cap != null ? t("chase.count.of", { fetched: leg.fetched, cap: leg.cap }) : String(leg.fetched)}
                  </bdi>
                </td>
                <td className="py-2 pe-3">
                  <DecisionBadge role={legRole(leg)}>{known ? t(`chase.leg.status.${leg.status}` as DiscoveryCopyKey) : leg.status}</DecisionBadge>
                </td>
                <td className="py-2 text-ink">
                  {leg.status === "failed" ? (
                    <>
                      <p data-leg-error={leg.error_code ?? ""}>{leg.error_code && LEG_CODES.has(leg.error_code) ? t(`harvest.leg.code.${leg.error_code}` as DiscoveryCopyKey) : t("chase.leg.failedNoCode")}</p>
                      <details className="text-xs">
                        <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-ink-muted">{DETAILS_LABEL[locale]}</summary>
                        {leg.error_code ? (
                          <p className="font-mono text-blocked" dir="ltr">
                            {leg.error_code}
                          </p>
                        ) : null}
                      </details>
                    </>
                  ) : leg.cap_hit ? (
                    <p data-lower-bound>{t("chase.leg.capped")}</p>
                  ) : leg.notes?.length ? (
                    <p className="text-ink-muted">
                      <bdi dir="ltr">{leg.notes.join("; ")}</bdi>
                    </p>
                  ) : null}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );

  const fullLegs = (legs: ChaseLeg[]): LegView[] =>
    legs.map((l) => ({ provider: l.provider, fetched: l.fetched, reported_total: null, cap: l.cap, cap_hit: l.cap_hit, status: l.status, error_code: l.error_code, seed: l.seed, direction: l.direction, notes: l.notes }));

  const summaryTable = detail ? (
    <section className="rounded-lg border border-rule bg-leaf p-5" data-legs>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[32rem] text-sm">
          <caption className="pb-2 text-start font-semibold text-ink">{t("chase.legs.title")}</caption>
          <thead>
            <tr className="text-start text-xs text-ink-muted">
              {(["provider", "direction", "studies", "fetched", "capped", "failed"] as const).map((c) => (
                <th key={c} scope="col" className="pb-2 pe-3 text-start">
                  {t(`chase.col.${c}` as DiscoveryCopyKey)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {detail.legs_summary.map((row) => (
              <tr key={`${row.provider}|${row.direction}`} className="border-t border-rule" data-summary={`${row.provider}|${row.direction}`}>
                <th scope="row" className="py-2 pe-3 text-start font-medium text-ink">
                  {providerName(row.provider)}
                </th>
                <td className="py-2 pe-3 text-ink">{directionText(row.direction)}</td>
                <td className="py-2 pe-3 text-ink" dir="ltr">
                  {row.legs}
                </td>
                <td className="py-2 pe-3 text-ink">
                  <bdi dir="ltr" data-fetched>
                    {row.cap_hits > 0 ? t("lowerBound", { n: row.fetched }) : String(row.fetched)}
                  </bdi>
                </td>
                <td className="py-2 pe-3">
                  {row.cap_hits > 0 ? <DecisionBadge role="unclear">{String(row.cap_hits)}</DecisionBadge> : <span className="text-ink-muted">0</span>}
                </td>
                <td className="py-2">
                  {row.failed > 0 ? <DecisionBadge role="blocked">{String(row.failed)}</DecisionBadge> : <span className="text-ink-muted">0</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {detail.legs_summary.some((r) => r.cap_hits > 0) ? (
        <p className="mt-2 text-sm text-ink" data-lower-bound-note>
          {t("chase.leg.capped")}
        </p>
      ) : null}
      {detail.legs.some((l) => l.status === "failed") ? (
        <p className="mt-2 text-sm text-ink" data-failed-list>
          {detail.legs
            .filter((l) => l.status === "failed")
            .map((l) => `${providerName(l.provider)}, ${directionText(l.direction)}`)
            .filter((v, i, all) => all.indexOf(v) === i)
            .join(" · ")}
          : {t("chase.partial.failedNote")}
        </p>
      ) : null}
      <details className="mt-3" data-per-seed>
        <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-ink">{t("chase.legs.show")}</summary>
        <div className="mt-2">{liveLegs(fullLegs(detail.legs))}</div>
      </details>
    </section>
  ) : null;

  const countsCard =
    detail && counts ? (
      <section aria-labelledby="chase-counts" className="rounded-lg border border-rule bg-leaf p-5" data-counts>
        <h2 id="chase-counts" className="font-semibold text-ink">
          {t("chase.counts.title")}
        </h2>
        <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
          {(
            [
              ["raw", t("chase.counts.raw")],
              ["duplicates_within_chase", t("chase.counts.dupes")],
              ["already_in_corpus", t("chase.counts.inCorpus")],
              ["outside_year_window", t("chase.counts.window", { min: detail.year_min ?? "", max: detail.year_max ?? "" })],
              ...(counts.over_ceiling > 0 ? ([["over_ceiling", t("chase.counts.over")]] as const) : []),
              ["new", t("chase.counts.new")],
            ] as const
          ).map(([key, label]) => (
            <div key={key}>
              <dt className="text-ink-muted">{label}</dt>
              <dd className="text-ink" data-count={key} dir="ltr">
                {counts[key]}
              </dd>
            </div>
          ))}
        </dl>
        {counts.over_ceiling > 0 ? (
          <p className="mt-3 text-sm text-ink" data-ceiling-note>
            <DecisionBadge role="unclear">{t("chase.status.PARTIAL")}</DecisionBadge> {t("chase.partial.ceiling", { ceiling: detail.run_ceiling ?? "", over: counts.over_ceiling })}
          </p>
        ) : null}
        {detail.already_in_corpus.length ? (
          <details className="mt-3 text-sm" data-in-corpus>
            <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-ink">
              {t("chase.inCorpus.show")} ({detail.already_in_corpus.length})
            </summary>
            <ul className="mt-1 space-y-1 text-ink-muted">
              {detail.already_in_corpus.map((row, i) => (
                <li key={`${row.record}-${i}`} data-in-corpus-row>
                  <bdi dir="auto">{t("chase.inCorpus.row", { title: row.title, study: row.study_id ?? "" })}</bdi>
                </li>
              ))}
            </ul>
          </details>
        ) : null}
        {detail.notes.length ? (
          <p className="mt-3 text-sm text-ink" data-notes>
            {t("chase.notes")}: <bdi dir="auto">{detail.notes.join(" · ")}</bdi>
          </p>
        ) : null}
      </section>
    ) : null;

  const selector =
    state && state.runs.length > 1 ? (
      <details className="mt-3 text-sm" data-chase-selector>
        <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-ink">
          {t("chase.run.label")}: <DataCell>{selected}</DataCell>
        </summary>
        <ul className="mt-1 space-y-1">
          {state.runs.map((r, index) => (
            <li key={r.chase}>
              <a className={`${LINK} gap-2`} href={discoveryHref(locale, "chase", origin, index === 0 ? "" : r.chase)} aria-current={r.chase === selected ? "true" : undefined} data-chase-option={r.chase}>
                <bdi>{t("chase.run.option", { chase: r.chase, date: stamp(r.started_at), status: statusText(r.status) })}</bdi>
              </a>
            </li>
          ))}
        </ul>
      </details>
    ) : null;

  const acceptedPrevious = accepted ? accepted.round - 1 : round - 1;

  return (
    <DiscoveryFrame locale={locale} current="chase" origin={origin} chase={published || !!accepted}>
      {loadError && !state ? (
        <DiscoveryRefusal locale={locale} refusal={loadError} origin={origin} onRetry={() => void load()} pageHeading />
      ) : !state ? (
        <Loading locale={locale} />
      ) : running ? (
        <div className="space-y-6">
          <header>
            {eyebrow}
            <h1 ref={heading} tabIndex={-1} className="mt-2 font-display text-3xl text-ink" aria-live="polite">
              {title}
            </h1>
            <p className="mt-2">
              <DecisionBadge role="include">{stopping ? t("chase.stopping") : t("chase.badge.running")}</DecisionBadge>
            </p>
          </header>
          {startError ? <DiscoveryRefusal locale={locale} refusal={startError} origin={origin} /> : null}
          {stream.error ? <DiscoveryRefusal locale={locale} refusal={stream.error} origin={origin} /> : null}
          {stream.lost ? <ConnectionLost locale={locale} lastAt={stream.lastAt} onRetry={stream.retry} /> : null}
          <div className="grid gap-6 lg:grid-cols-3">
            <section className="min-w-0 rounded-lg border border-rule bg-leaf p-5 lg:col-span-2" data-live>
              {stream.legs.length ? liveLegs(stream.legs) : <p role="status">{t("chase.reading")}</p>}
            </section>
            <aside className="rounded-lg border border-rule bg-leaf p-5">
              <h2 className="font-semibold text-ink">{t("chase.stop.title")}</h2>
              <p className="mt-2 text-sm text-ink">{t("chase.stop.body")}</p>
              <Button className="mt-3" onClick={() => void stop()} disabled={stopping || offline} data-stop>
                {t("chase.stop")}
              </Button>
            </aside>
          </div>
        </div>
      ) : accepted && detail ? (
        <div className="space-y-6">
          <header>
            {eyebrow}
            <h1 ref={heading} tabIndex={-1} className="mt-2 font-display text-3xl text-ink" aria-live="polite">
              {title}
            </h1>
            {selector}
          </header>
          <section aria-labelledby="chase-accepted" className="rounded-lg border border-rule bg-leaf p-5" data-accepted>
            <h2 id="chase-accepted" className="font-semibold text-ink">
              {t("chase.accepted.card", { round: accepted.round })}
            </h2>
            <dl className="mt-3 space-y-2 text-sm">
              <div>
                <dt className="text-ink-muted">{t("chase.accepted.id")}</dt>
                <dd data-artifact>
                  <DataCell>{accepted.artifact_id}</DataCell>
                </dd>
              </div>
              <div>
                <dd className="text-ink">
                  <bdi>{t("chase.accepted.at", { date: stamp(accepted.accepted_at) })}</bdi>
                </dd>
              </div>
              <div>
                <dd className="text-ink" data-accepted-counts>
                  {t("chase.accepted.counts", { records: accepted.records, studies: accepted.studies })}
                </dd>
              </div>
              {detail.parent_corpus ? (
                <div>
                  <dt className="text-ink-muted">{t("chase.accepted.parent", { previous: acceptedPrevious })}</dt>
                  <dd>
                    <DataCell>{detail.parent_corpus.artifact_id}</DataCell>
                  </dd>
                </div>
              ) : null}
              <div>
                <dd className="text-ink" data-archived>
                  {t("chase.accepted.archived", { previous: acceptedPrevious, path: answer?.archive_path ? `${answer.archive_path}/` : roundFolder(acceptedPrevious) })}
                  {answer?.archived.length ? (
                    <details className="mt-1 text-xs">
                      <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-ink-muted">{DETAILS_LABEL[locale]}</summary>
                      <ul className="font-mono text-ink-muted" dir="ltr">
                        {answer.archived.map((p) => (
                          <li key={p}>{p}</li>
                        ))}
                      </ul>
                    </details>
                  ) : null}
                </dd>
              </div>
            </dl>
            <p className="mt-3 text-sm text-ink-muted">{t("chase.accepted.again", { round: accepted.round })}</p>
            <a className="mt-4 inline-flex min-h-11 items-center rounded-md bg-brand px-4 font-medium text-on-brand" href={screeningHomeHref(locale, origin)} data-go-screening>
              {t("chase.accepted.go")}
            </a>
          </section>
          {countsCard}
          {summaryTable}
        </div>
      ) : !published ? (
        <div className="space-y-4" data-not-published>
          {eyebrow}
          <StateCard locale={locale} code="SCREENING_NOT_PUBLISHED" consoleOrigin={origin} pageHeading />
          <p>
            <a className={LINK} href={discoveryHref(locale, "", origin)}>
              {t("chase.back")}
            </a>
          </p>
        </div>
      ) : !detail ? (
        <div className="space-y-6">
          <header>
            {eyebrow}
            <h1 ref={heading} tabIndex={-1} className="mt-2 font-display text-3xl text-ink">
              {title}
            </h1>
            <p className="mt-2 max-w-2xl text-ink-muted">{t("chase.lede")}</p>
          </header>
          {detailError ? <DiscoveryRefusal locale={locale} refusal={detailError} origin={origin} /> : null}
          {otherJob ? (
            <p className="rounded-lg border border-rule bg-leaf p-3 text-ink" data-other-job>
              {t("job.otherKind")}{" "}
              <a className={LINK} href={discoveryHref(locale, otherJob.kind === "recall" ? "recall" : "harvest", origin)}>
                {otherJob.kind === "recall" ? t("job.openRecall") : t("job.openHarvest")}
              </a>
            </p>
          ) : null}
          {startError ? (
            <div className="space-y-2">
              <DiscoveryRefusal locale={locale} refusal={startError} origin={origin} onRetry={startError.code === "OPENALEX_KEY_NOT_SET" ? () => { setStartError(null); void load(); } : undefined} />
              {startError.code === "DISCOVERY_JOB_ACTIVE" && (startError.details as { job?: DiscoveryJob } | undefined)?.job?.kind === "chase" ? (
                <Button onClick={() => follow(startError)}>{t("job.follow")}</Button>
              ) : null}
            </div>
          ) : null}
          {seeds && seeds.chaseable === 0 ? (
            <section className="rounded-lg border border-rule bg-leaf p-5" data-empty="noSeeds">
              <h2 className="font-semibold text-ink">{t("chase.empty.noSeeds")}</h2>
              <p className="mt-1 text-sm text-ink">{t("chase.empty.noSeedsBody")}</p>
            </section>
          ) : null}
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="min-w-0 space-y-6 lg:col-span-2">
              {seedsCard}
              {keysCard}
            </div>
            <aside>{form}</aside>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          <header>
            {eyebrow}
            <h1 ref={heading} tabIndex={-1} className="mt-2 font-display text-3xl text-ink" aria-live="polite">
              {title}
            </h1>
            <p className="mt-2 flex flex-wrap items-center gap-2 text-ink" data-headline>
              <DecisionBadge role={detail.status === "SUCCESS" ? "include" : detail.status === "FAILED" ? "blocked" : detail.status === "EMPTY_RESULT" ? "exclude" : "unclear"}>
                {statusText(detail.status)}
              </DecisionBadge>
              <span>
                <bdi dir="ltr">{detail.reason}</bdi>
              </span>
            </p>
            {selector}
            {!newest ? (
              <p className="mt-3 rounded-lg border border-rule bg-leaf p-3 text-sm text-ink-muted" data-older-run>
                {t("chase.stale")} {t("run.readonly")}
              </p>
            ) : null}
            {cancelled && newest ? <p className="mt-2 text-ink">{t("chase.cancelled.body")}</p> : null}
            {failedRun && newest ? <p className="mt-2 text-ink">{t("chase.failed.body")}</p> : null}
            {nothingNew && newest && !failedRun && !cancelled ? <p className="mt-2 text-ink">{t("chase.empty.nothingNewBody")}</p> : null}
          </header>
          {jobError ? <DiscoveryRefusal locale={locale} refusal={{ code: jobError.code, message: jobError.message, details: jobError.details }} origin={origin} /> : null}
          {startError ? (
            <div className="space-y-2">
              <DiscoveryRefusal locale={locale} refusal={startError} origin={origin} onRetry={startError.code === "OPENALEX_KEY_NOT_SET" ? () => { setStartError(null); void load(); } : undefined} />
              {startError.code === "DISCOVERY_JOB_ACTIVE" && (startError.details as { job?: DiscoveryJob } | undefined)?.job?.kind === "chase" ? (
                <Button onClick={() => follow(startError)}>{t("job.follow")}</Button>
              ) : null}
            </div>
          ) : null}
          {summaryTable}
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="min-w-0 space-y-6 lg:col-span-2">
              {countsCard}
              {detail.seeds.some((s) => !s.chaseable) ? (
                <section className="rounded-lg border border-rule bg-leaf p-5 text-sm" data-run-not-chaseable>
                  <h2 className="font-semibold text-ink">{t("chase.seeds.notChaseable.title")}</h2>
                  <ul className="mt-2 space-y-1 text-ink-muted">
                    {detail.seeds
                      .filter((s) => !s.chaseable)
                      .map((s) => (
                        <li key={s.study_id}>
                          <bdi dir="auto">{t("chase.seeds.notChaseable.row", { title: s.title, reason: s.reason ?? "" })}</bdi>
                        </li>
                      ))}
                  </ul>
                </section>
              ) : null}
            </div>
            <aside className="space-y-4">
              {acceptError ? (
                <DiscoveryRefusal
                  locale={locale}
                  refusal={acceptError}
                  origin={origin}
                  onRetry={acceptError.code === "ARCHIVE_INCOMPLETE" || isOffline(acceptError.code) ? () => void accept() : undefined}
                />
              ) : null}
              {acceptError?.code === "ARCHIVE_INCOMPLETE" && acceptError.details ? (
                <details className="text-xs" data-archive-details>
                  <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-ink-muted">{DETAILS_LABEL[locale]}</summary>
                  <pre className="whitespace-pre-wrap font-mono text-ink-muted" dir="ltr">
                    {JSON.stringify(acceptError.details, null, 2)}
                  </pre>
                </details>
              ) : null}
              {canAccept ? (
                <GatePanel
                  label={t("chase.gate.label")}
                  actions={
                    <Button
                      variant="primary"
                      onClick={() => void accept()}
                      disabled={accepting || offline || !!state.active_job || acceptError?.code === "PROTOCOL_CHANGED_SINCE_PUBLISH"}
                      aria-describedby={offline ? "chase-gate-offline" : state.active_job ? "chase-gate-running" : undefined}
                      data-accept
                    >
                      {accepting ? t("chase.gate.accepting") : t("chase.gate.accept", { new: counts!.new })}
                    </Button>
                  }
                >
                  <p className="font-semibold">{t("chase.gate.title", { new: counts!.new, round: round + 1 })}</p>
                  <p className="mt-2">{t("chase.gate.body", { round: round + 1, previous: round })}</p>
                  <p className="mt-2 text-sm text-ink-muted">{t("chase.gate.record")}</p>
                  {offline ? (
                    <p id="chase-gate-offline" className="mt-2 text-sm text-ink-muted">
                      {t("chase.gate.offline")}
                    </p>
                  ) : null}
                  {state.active_job ? (
                    <p id="chase-gate-running" className="mt-2 text-sm text-ink" data-gate-running>
                      {t("chase.gate.running")}
                    </p>
                  ) : null}
                </GatePanel>
              ) : null}
              {newest && published && !accepted ? (
                again ? (
                  form
                ) : (
                  <section className="rounded-lg border border-rule bg-leaf p-5">
                    <Button onClick={() => setAgain(true)} data-again>
                      {t("chase.again")}
                    </Button>
                    <p className="mt-3">
                      <a className={LINK} href={discoveryHref(locale, "", origin)}>
                        {t("chase.back")}
                      </a>
                    </p>
                  </section>
                )
              ) : null}
            </aside>
          </div>
        </div>
      )}
    </DiscoveryFrame>
  );
}
