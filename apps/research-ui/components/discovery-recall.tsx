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
  discoveryHref,
  refusalOf,
  stamp,
  useDiscoveryParams,
  useJobStream,
  type Refusal,
} from "@/components/discovery-frame";
import { cancelJob, getPlan, getRecall, getRuns, startRecall, type DiscoveryJob, type Plan, type RecallCheck, type SeedKind } from "@/lib/discovery-api";
import { getCorpus } from "@/lib/screening-v1";
import { discoveryT, providerName, type DiscoveryCopyKey } from "@/lib/discovery-copy";

/**
 * 02 Recall check (spec `docs/ux/phase1-discovery/final/02-recall.md`): does the
 * frozen query reach papers the researcher already knows? Check-only
 * (decision 3): the query is never rewritten, a miss blocks nothing, and a
 * synonym is a protocol amendment through inception. Seeds are the
 * researcher's own (DOI or arXiv id); anchor seeds wait for an engine item.
 */

const MAX_SEEDS = 25;
type SeedRow = { key: number; kind: SeedKind; id: string };

const CELL: Record<string, { key: DiscoveryCopyKey; role: DecisionRole }> = {
  found: { key: "recall.found", role: "include" },
  not_found: { key: "recall.notFound", role: "exclude" },
  "n/a": { key: "recall.na", role: "exclude" },
  failed: { key: "recall.failed", role: "unclear" },
};

export function DiscoveryRecall({ locale }: Readonly<{ locale: Locale }>) {
  const t = discoveryT(locale);
  const { origin, ready } = useDiscoveryParams();
  const [check, setCheck] = useState<RecallCheck | null>(null);
  const [empty, setEmpty] = useState(false);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [loadError, setLoadError] = useState<Refusal | null>(null);
  const [startError, setStartError] = useState<Refusal | null>(null);
  const [accepted, setAccepted] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [otherJob, setOtherJob] = useState(false);
  const [cancelled, setCancelled] = useState(false);
  // The number of seeds this page sent (review 3); a reattached check prints no number.
  const [submitted, setSubmitted] = useState<number | null>(null);
  const [rows, setRows] = useState<SeedRow[]>([{ key: 0, kind: "doi", id: "" }]);
  const [loaded, setLoaded] = useState(false);
  const nextKey = useRef(1);
  const heading = useRef<HTMLHeadingElement>(null);
  const firstSeed = useRef<HTMLInputElement>(null);

  const readCheck = useCallback(async () => {
    try {
      const last = await getRecall(origin);
      setCheck(last);
      setEmpty(false);
      setRows(last.seeds.map((s) => ({ key: nextKey.current++, kind: s.kind === "arxiv" ? "arxiv" : "doi", id: s.id })));
    } catch (error) {
      const refusal = refusalOf(error);
      if (refusal.code === "RECALL_NOT_RUN") setEmpty(true);
      else setLoadError(refusal);
    }
  }, [origin]);

  const load = useCallback(async () => {
    setLoadError(null);
    try {
      setPlan(await getPlan(origin));
    } catch (error) {
      setLoadError(refusalOf(error));
      setLoaded(true);
      return;
    }
    await readCheck();
    getRuns(origin).then(
      (runs) => {
        const active = runs.active_job;
        if (active?.kind === "recall") setJobId(active.job_id);
        setOtherJob(!!active && active.kind !== "recall");
      },
      () => undefined,
    );
    getCorpus(origin).then((c) => setAccepted(c.state === "ACCEPTED"), () => undefined);
    setLoaded(true);
  }, [origin, readCheck]);

  useEffect(() => {
    if (ready) void load();
  }, [ready, load]);

  const onEnd = useCallback(
    (job: DiscoveryJob | null) => {
      setJobId(null);
      if (job?.state === "cancelled") setCancelled(true);
      else if (job?.state === "failed" && job.error) setStartError({ code: job.error.code, message: job.error.message, details: job.error.details });
      void readCheck().then(() => heading.current?.focus());
    },
    [readCheck],
  );
  const stream = useJobStream(origin, jobId, onEnd);
  const running = !!jobId && !stream.ended;

  const submit = async () => {
    setStartError(null);
    setCancelled(false);
    const seeds = rows.filter((r) => r.id.trim()).map((r) => ({ id: r.id.trim(), kind: r.kind, source: "you" as const }));
    try {
      const { job } = await startRecall(origin, seeds);
      setSubmitted(seeds.length);
      setJobId(job.job_id);
    } catch (error) {
      const refusal = refusalOf(error);
      setStartError(refusal);
      if (refusal.code === "SEEDS_INVALID") firstSeed.current?.focus();
    }
  };

  const cancel = async () => {
    if (!jobId) return;
    try {
      await cancelJob(origin, jobId);
    } catch (error) {
      setStartError(refusalOf(error));
    }
  };

  const follow = () => {
    const job = (startError?.details as { job?: DiscoveryJob } | undefined)?.job;
    if (job?.kind === "recall") {
      setStartError(null);
      setJobId(job.job_id);
    }
  };

  const filled = rows.filter((r) => r.id.trim()).length;
  const earlier = !!check && !!plan && check.protocol_fingerprint !== plan.protocol_fingerprint;
  const providers = check ? Object.keys(check.seeds[0]?.per_provider ?? {}) : [];

  return (
    <DiscoveryFrame locale={locale} current="recall" origin={origin}>
      {loadError && !plan ? (
        <DiscoveryRefusal locale={locale} refusal={loadError} origin={origin} onRetry={() => void load()} pageHeading />
      ) : !loaded ? (
        <Loading locale={locale} />
      ) : (
        <div className="space-y-6">
          <header>
            <Eyebrow locale={locale} step="recall" name={t("recall.eyebrowName")} />
            <h1 ref={heading} tabIndex={-1} className="mt-2 font-display text-3xl text-ink">
              {check ? t("recall.title", { found: check.found, total: check.total }) : t("recall.titleNone")}
            </h1>
            <p className="mt-2 max-w-2xl text-ink-muted">{check ? t("recall.lede") : t("recall.ledeEmpty")}</p>
          </header>
          {loadError ? <DiscoveryRefusal locale={locale} refusal={loadError} origin={origin} onRetry={() => void load()} /> : null}
          {otherJob ? (
            <p className="rounded-lg border border-rule bg-leaf p-3 text-ink">
              {t("job.otherKind")}{" "}
              <a className={LINK} href={discoveryHref(locale, "harvest", origin)}>
                {t("job.openHarvest")}
              </a>
            </p>
          ) : null}
          {startError ? (
            <div className="space-y-2">
              <DiscoveryRefusal locale={locale} refusal={startError} origin={origin} onRetry={startError.code === "MAILTO_NOT_SET" ? () => { setStartError(null); void load(); } : undefined} />
              {startError.code === "SEEDS_INVALID" && startError.message ? (
                <p className="text-sm text-ink" data-seeds-invalid>
                  <bdi dir="ltr">{startError.message}</bdi>
                </p>
              ) : null}
              {startError.code === "DISCOVERY_JOB_ACTIVE" ? (
                (startError.details as { job?: DiscoveryJob } | undefined)?.job?.kind === "recall" ? (
                  <Button onClick={follow}>{t("job.follow")}</Button>
                ) : (
                  <a className={LINK} href={discoveryHref(locale, "harvest", origin)}>
                    {t("job.openHarvest")}
                  </a>
                )
              ) : null}
            </div>
          ) : null}
          {cancelled ? (
            <p role="status" className="text-ink" data-cancelled>
              {t("recall.cancelled")}
            </p>
          ) : null}
          {stream.error ? <DiscoveryRefusal locale={locale} refusal={stream.error} origin={origin} /> : null}
          {stream.lost ? <ConnectionLost locale={locale} lastAt={stream.lastAt} onRetry={stream.retry} /> : null}
          {earlier ? (
            <p className="rounded-lg border border-rule bg-leaf p-3 text-ink" data-earlier-protocol>
              {t("recall.earlierProtocol")}
            </p>
          ) : null}

          <div className="grid gap-6 lg:grid-cols-3">
            <div className="space-y-6 min-w-0 lg:col-span-2">
              {running ? (
                <section className="rounded-lg border border-rule bg-leaf p-5" aria-live="polite" data-checking>
                  <h2 className="font-semibold text-ink">{submitted != null ? t("recall.checking", { n: submitted }) : t("recall.checkingAny")}</h2>
                  <p className="mt-1 text-sm text-ink-muted">{t("recall.asking")}</p>
                  <ul className="mt-2 space-y-1 text-sm">
                    {stream.legs.map((leg) => (
                      <li key={leg.provider} data-asking={leg.provider}>
                        {providerName(leg.provider)} · <bdi>{leg.cap_hit ? t("lowerBound", { n: leg.fetched }) : leg.fetched}</bdi> · {leg.status}
                      </li>
                    ))}
                  </ul>
                  {check ? <p className="mt-2 text-xs text-ink-muted">{t("recall.earlier")}</p> : null}
                </section>
              ) : null}
              {check ? (
                <section className="rounded-lg border border-rule bg-leaf p-5" data-recall-table>
                  <div className="overflow-x-auto">
                    <table className="w-full min-w-[32rem] text-sm">
                      <caption className="pb-2 text-start font-semibold text-ink">{t("recall.seeds.title")}</caption>
                      <thead>
                        <tr className="text-xs text-ink-muted">
                          <th scope="col" className="pb-2 pe-3 text-start">
                            {t("recall.col.seed")}
                          </th>
                          <th scope="col" className="pb-2 pe-3 text-start">
                            {t("recall.col.source")}
                          </th>
                          {providers.map((p) => (
                            <th key={p} scope="col" className="pb-2 pe-3 text-start">
                              {providerName(p)}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {check.seeds.map((seed) => {
                          const missed = check.missed_everywhere.includes(seed.id);
                          return (
                            <tr key={seed.id} className="border-t border-rule align-top" data-seed={seed.id}>
                              <th scope="row" className="py-2 pe-3 text-start font-normal">
                                <DataCell>{seed.id}</DataCell>
                                {seed.title ? (
                                  <span className="block text-ink" dir="auto">
                                    {seed.title}
                                  </span>
                                ) : null}
                                {seed.title_check === "DOI_TITLE_MISMATCH" || seed.title_check === "unresolved" ? (
                                  <span className="block text-xs text-unclear" data-title-check={seed.title_check}>
                                    {t(`recall.titleCheck.${seed.title_check}` as DiscoveryCopyKey)}
                                  </span>
                                ) : null}
                                {missed ? (
                                  <span className="block text-xs font-semibold text-blocked" data-missed>
                                    <span aria-hidden="true">✕ </span>
                                    {t("recall.missedEverywhere")}
                                  </span>
                                ) : null}
                              </th>
                              <td className="py-2 pe-3">{seed.source === "anchor" ? t("recall.source.anchor") : t("recall.source.you")}</td>
                              {providers.map((p) => {
                                const value = seed.per_provider[p];
                                const cell = CELL[value];
                                return (
                                  <td key={p} className="py-2 pe-3" data-cell={value}>
                                    {cell ? <DecisionBadge role={cell.role}>{t(cell.key)}</DecisionBadge> : value}
                                  </td>
                                );
                              })}
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                  <p className="mt-3 text-xs text-ink-muted">{t("recall.legend")}</p>
                  <ul className="mt-3 space-y-1 text-sm" data-legs>
                    {check.legs.map((leg) => (
                      <li key={leg.provider} data-leg={leg.provider}>
                        {providerName(leg.provider)}:{" "}
                        <bdi>{leg.reported_total == null ? "–" : leg.cap_hit ? t("lowerBound", { n: leg.reported_total }) : leg.reported_total}</bdi>
                        {leg.status === "failed" ? (
                          <>
                            {" "}
                            <DecisionBadge role="unclear">{t("recall.failed")}</DecisionBadge>{" "}
                            {leg.error_code ? (
                              <span className="font-mono text-[0.8125rem]" dir="ltr">
                                {leg.error_code}
                              </span>
                            ) : null}
                            {leg.error ? (
                              <details className="text-xs">
                                <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-ink-muted">{DETAILS_LABEL[locale]}</summary>
                                <p dir="ltr">{leg.error}</p>
                              </details>
                            ) : null}
                          </>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                </section>
              ) : null}

              {accepted ? (
                <p className="rounded-lg border border-rule bg-leaf p-3 text-ink" data-accepted>
                  {t("recall.accepted")}
                </p>
              ) : (
                <section aria-labelledby="recall-form" className="rounded-lg border border-rule bg-leaf p-5" data-recall-form>
                  <h2 id="recall-form" className="font-semibold text-ink">
                    {t("recall.form.title")}
                  </h2>
                  <p id="recall-help" className="mt-1 text-sm text-ink-muted">
                    {t("recall.form.help")}
                  </p>
                  <ol className="mt-3 space-y-3">
                    {rows.map((row, index) => (
                      <li key={row.key} className="flex flex-wrap items-end gap-2" data-seed-row>
                        <div>
                          <label className="block text-xs text-ink-muted" htmlFor={`seed-kind-${row.key}`}>
                            {t("recall.form.kind", { n: index + 1 })}
                          </label>
                          <select
                            id={`seed-kind-${row.key}`}
                            value={row.kind}
                            disabled={running}
                            onChange={(e) => setRows((rs) => rs.map((r) => (r.key === row.key ? { ...r, kind: e.target.value as SeedKind } : r)))}
                            className="min-h-11 rounded-md border border-rule-strong bg-paper px-2 text-ink"
                          >
                            <option value="doi">{t("recall.form.kind.doi")}</option>
                            <option value="arxiv">{t("recall.form.kind.arxiv")}</option>
                          </select>
                        </div>
                        <div className="min-w-0 flex-1">
                          <label className="block text-xs text-ink-muted" htmlFor={`seed-id-${row.key}`}>
                            {t("recall.form.id", { n: index + 1 })}
                          </label>
                          <input
                            id={`seed-id-${row.key}`}
                            ref={index === 0 ? firstSeed : undefined}
                            value={row.id}
                            disabled={running}
                            dir="ltr"
                            aria-describedby="recall-help"
                            aria-invalid={index === 0 && startError?.code === "SEEDS_INVALID" ? true : undefined}
                            onChange={(e) => setRows((rs) => rs.map((r) => (r.key === row.key ? { ...r, id: e.target.value } : r)))}
                            onKeyDown={(e) => {
                              if (e.key === "Enter") e.preventDefault();
                            }}
                            className="min-h-11 w-full rounded-md border border-rule-strong bg-paper px-3 font-mono text-[0.8125rem] text-ink"
                          />
                        </div>
                        <Button
                          disabled={running}
                          onClick={() => setRows((rs) => (rs.length > 1 ? rs.filter((r) => r.key !== row.key) : [{ key: nextKey.current++, kind: "doi", id: "" }]))}
                        >
                          {t("recall.form.remove", { n: index + 1 })}
                        </Button>
                      </li>
                    ))}
                  </ol>
                  <div className="mt-3 flex flex-wrap items-center gap-3">
                    <Button
                      disabled={running || rows.length >= MAX_SEEDS}
                      onClick={() => setRows((rs) => [...rs, { key: nextKey.current++, kind: "doi", id: "" }])}
                      data-add-seed
                    >
                      {t("recall.form.add")}
                    </Button>
                    <span className="text-xs text-ink-muted">{t("recall.form.max")}</span>
                  </div>
                  <div className="mt-4 flex flex-wrap gap-3">
                    {running ? (
                      <Button onClick={() => void cancel()} data-cancel>
                        {t("recall.cancel")}
                      </Button>
                    ) : (
                      <Button variant="primary" disabled={filled < 1 || filled > MAX_SEEDS} onClick={() => void submit()} data-check>
                        {check ? t("recall.submitAgain") : t("recall.submit")}
                      </Button>
                    )}
                  </div>
                </section>
              )}
              <section className="rounded-lg border border-rule bg-leaf p-5 text-sm">
                <h2 className="font-semibold text-ink">{t("recall.mean.title")}</h2>
                <p className="mt-2 text-ink">{t("recall.mean.one")}</p>
                <p className="mt-1 text-ink">{t("recall.mean.all")}</p>
              </section>
            </div>
            <aside className="space-y-4">
              {check ? (
                <section className="rounded-lg border border-rule bg-leaf p-5 text-sm">
                  <h2 className="font-semibold text-ink">{t("recall.queryChecked")}</h2>
                  <p className="mt-2">
                    <DataCell>{check.query_text}</DataCell>
                  </p>
                  <p className="mt-2 text-ink-muted">
                    <bdi>{t("recall.checkedAt", { date: stamp(check.checked_at) })}</bdi>
                  </p>
                  <p className="mt-1 text-xs text-ink-muted">
                    <DataCell>{check.protocol_fingerprint}</DataCell>
                  </p>
                </section>
              ) : empty ? null : null}
              <section className="rounded-lg border border-rule bg-leaf p-5 text-sm">
                <p className="text-ink-muted">{t("amend.help")}</p>
                <a className={LINK} href={`/${locale}/inception/${origin ? `?console=${encodeURIComponent(origin)}` : ""}`}>
                  {t("amend.link")}
                </a>
                <p className="mt-3">
                  <a className={LINK} href={discoveryHref(locale, "harvest", origin)} data-next>
                    {t("recall.next")}
                  </a>
                </p>
              </section>
            </aside>
          </div>
        </div>
      )}
    </DiscoveryFrame>
  );
}
