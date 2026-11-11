"use client";

import { useCallback, useEffect, useRef, useState, type RefObject } from "react";

import type { Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge } from "@/components/ui/base";
import { inceptionHref, InceptionFrame, InceptionRefusal, refusalOf, StepHeader, useDraft, type Refusal } from "@/components/inception-frame";
import {
  DoiLink,
  isOffline,
  KeyLines,
  LegsList,
  PartialBanner,
  partsText,
  ProgressCard,
  RefreshWarning,
  shortFingerprint,
  stamp,
  useReconJob,
  yearsText,
} from "@/components/inception-recon";
import { inceptionT } from "@/lib/inception-copy";
import { inceptionRichT, Ltr } from "@/components/rich-copy";
import {
  distill,
  getConcepts,
  getDirections,
  getRecon,
  hasUsablePool,
  startProbe,
  type ConceptReport,
  type Distilled,
  type ReconJob,
  type ReconLeg,
  type ReconState,
} from "@/lib/recon-api";

/**
 * Step 2, Explore (spec 02, M4d): run the first search for the saved question,
 * then show the pool's health, the databases asked, the draft's concepts in the
 * pool, a heuristic reading and the papers. Every number is the engine's; the
 * search mode is a probe parameter, not a draft field, and nothing on this
 * screen is saved to the draft.
 */

const DEFAULT_YEAR = 2000;
const POOL_MAX = 25;
const PAPERS_SHOWN = 5;
const TOPICS_SHOWN = 4;

type PaperSort = "anchors" | "year" | "title";

export function InceptionExplore({ locale }: Readonly<{ locale: Locale }>) {
  const t = inceptionT(locale);
  const rt = inceptionRichT(locale);
  const state = useDraft();
  const { draft, origin, draftId, record } = state;
  const [recon, setRecon] = useState<ReconState | null>(null);
  const [reconError, setReconError] = useState<Refusal | null>(null);
  const [pool, setPool] = useState<Distilled | null>(null);
  const [poolError, setPoolError] = useState<Refusal | null>(null);
  const [nDirections, setNDirections] = useState<number | null>(null);
  const [concepts, setConcepts] = useState<ConceptReport | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [startError, setStartError] = useState<Refusal | null>(null);
  const [jobError, setJobError] = useState<Refusal | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [semantic, setSemantic] = useState(false);
  const [warn, setWarn] = useState<{ semantic: boolean } | null>(null);
  const [asOf, setAsOf] = useState("");
  const [sort, setSort] = useState<PaperSort>("anchors");
  const [allPapers, setAllPapers] = useState(false);
  const [allTopics, setAllTopics] = useState(false);
  const progressHeading = useRef<HTMLHeadingElement>(null);
  const poolHeading = useRef<HTMLHeadingElement>(null);
  const opener = useRef<HTMLElement | null>(null);

  const readPool = useCallback(async () => {
    setPoolError(null);
    const [d, dirs, c] = await Promise.allSettled([distill(origin, draftId), getDirections(origin, draftId), getConcepts(origin, draftId)]);
    if (d.status === "fulfilled") setPool(d.value);
    else setPoolError(refusalOf(d.reason));
    setNDirections(dirs.status === "fulfilled" ? dirs.value.directions.length : null);
    setConcepts(c.status === "fulfilled" ? c.value : null);
  }, [origin, draftId]);

  const loadRecon = useCallback(async () => {
    try {
      const read = await getRecon(origin, draftId);
      setRecon(read);
      setReconError(null);
      setAsOf(new Date().toISOString());
      if (read.active_job && read.active_job.state === "running") setJobId(read.active_job.job_id);
      if (hasUsablePool(read)) await readPool();
      return read;
    } catch (error) {
      setReconError(refusalOf(error));
      return null;
    }
  }, [origin, draftId, readPool]);

  useEffect(() => {
    if (record) void loadRecon();
    // Once per loaded draft, not per render or per save (build note 4).
  }, [record?.session_id, loadRecon]); // eslint-disable-line react-hooks/exhaustive-deps

  const onEnd = useCallback(
    (job: ReconJob | null, lostJob: boolean) => {
      setJobId(null);
      setStartError(null);
      if (lostJob) setNotFound(true);
      else if (job?.state === "failed" && job.error) setJobError({ code: job.error.code, message: job.error.message, details: job.error.details });
      void loadRecon().then(() => {
        if (job?.state === "succeeded") poolHeading.current?.focus();
      });
    },
    [loadRecon],
  );
  const progress = useReconJob(origin, draftId, jobId, onEnd);
  const running = !!jobId;

  const search = async (refresh: boolean, withSemantic: boolean) => {
    setWarn(null);
    setStartError(null);
    setJobError(null);
    setNotFound(false);
    try {
      const { job } = await startProbe(origin, draftId, { refresh, semantic: withSemantic });
      setJobId(job.job_id);
      setTimeout(() => progressHeading.current?.focus(), 0);
    } catch (error) {
      const refusal = refusalOf(error);
      setStartError(refusal);
      const active = (refusal.details as { job?: ReconJob } | undefined)?.job;
      if (refusal.code === "RECON_JOB_ACTIVE" && active?.job_id) setJobId(active.job_id);
    }
  };

  /** A search that replaces the pool asks first when a direction is bound on it. */
  const askSearch = (withSemantic: boolean, from?: HTMLElement | null) => {
    if (recon?.grounding) {
      opener.current = from ?? null;
      setWarn({ semantic: withSemantic });
      return;
    }
    void search(true, withSemantic);
  };

  const closeWarn = () => {
    setWarn(null);
    setTimeout(() => opener.current?.focus(), 0);
  };

  const offline = isOffline(reconError?.code) || isOffline(startError?.code);
  const mailto = recon?.mailto_set !== false;
  const usable = hasUsablePool(recon);
  const topic = (draft.topic ?? "").trim();
  const canSearch = !!recon && mailto && !running && !offline && !!topic;
  const latest = recon?.session?.latest ?? null;
  const grounding = recon?.grounding ?? null;
  const groundingLabel = grounding?.direction?.label ?? "";

  const nextLabel = nDirections === null || nDirections === 0 ? t("explore.next.none") : nDirections === 1 ? t("explore.next.one") : t("explore.next", { n: String(nDirections) });

  const failedLegs = ((jobError?.details as { legs?: ReconLeg[] } | undefined)?.legs ?? []).map((l) => ({ ...l, notes: l.notes ?? [] }));

  return (
    <InceptionFrame locale={locale} current="explore" draft={state}>
      <StepHeader kicker={t("explore.kicker")} title={t("explore.title")} lede={t("explore.lede")} />
      <div className="space-y-6">
        {!recon && !reconError ? (
          <p role="status" className="text-ink-muted">
            {t("asking")}
          </p>
        ) : null}
        {reconError && !recon ? (
          <InceptionRefusal locale={locale} refusal={reconError} draftId={draftId} origin={origin} onRetry={() => void loadRecon()} />
        ) : null}
        {recon && !mailto ? <InceptionRefusal locale={locale} refusal={{ code: "MAILTO_NOT_SET", message: "" }} draftId={draftId} origin={origin} command="SCHOLAR_MAILTO=<your email>" /> : null}

        {recon?.scope_changed ? (
          <section className="rounded-lg border border-unclear bg-leaf p-4" data-scope-changed>
            <p className="text-ink">{t("explore.changed.body", { parts: partsText(locale, recon.scope_changes ?? []) })}</p>
            <Button className="mt-2" disabled={!canSearch} onClick={(event) => askSearch(semantic, event.currentTarget)}>
              {t("explore.changed.action")}
            </Button>
          </section>
        ) : null}
        {recon?.binding?.stale ? (
          <section className="rounded-lg border border-unclear bg-leaf p-4" data-stale-binding>
            <p className="text-ink">{t("explore.stale.body")}</p>
            <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "direction", draftId, origin)}>
              {t("explore.stale.action")}
            </a>
          </section>
        ) : null}

        {startError && !(startError.code === "MAILTO_NOT_SET" && !mailto) ? (
          <InceptionRefusal locale={locale} refusal={startError} draftId={draftId} origin={origin} onRetry={() => void search(true, semantic)} />
        ) : null}
        {notFound ? (
          <InceptionRefusal locale={locale} refusal={{ code: "RECON_JOB_NOT_FOUND", message: "" }} draftId={draftId} origin={origin} onRetry={() => void loadRecon()} />
        ) : null}
        {jobError ? (
          <div className="space-y-2" data-job-error={jobError.code}>
            <InceptionRefusal locale={locale} refusal={jobError} draftId={draftId} origin={origin} onRetry={() => void search(true, semantic)} />
            {failedLegs.length ? (
              <section className="rounded-lg border border-rule bg-leaf p-4" aria-labelledby="failed-legs">
                <h2 id="failed-legs" className="font-semibold text-ink">
                  {t("explore.legs.title")}
                </h2>
                <LegsList locale={locale} legs={failedLegs} />
                <p className="mt-2 text-xs text-ink-muted">{t("explore.legs.neverEmpty")}</p>
              </section>
            ) : null}
          </div>
        ) : null}

        {running ? <ProgressCard locale={locale} legs={progress.legs} lost={progress.lost} headingRef={progressHeading} /> : null}

        {recon && !usable && !running ? (
          <section aria-labelledby="first-title" className="rounded-lg border border-rule bg-leaf p-5" data-first-search>
            <h2 id="first-title" className="font-semibold text-ink">
              {t("explore.first.title")}
            </h2>
            <dl className="mt-3 space-y-2 text-sm">
              <div>
                <dt className="text-ink-muted">{t("explore.first.question")}</dt>
                <dd className="text-ink" dir="auto">
                  {draft.topic ?? ""}
                </dd>
              </div>
              <div>
                <dd className="text-ink">
                  {yearsText(locale, draft.start_year ?? DEFAULT_YEAR, draft.end_year ?? null)} · <bdi dir="ltr">{(draft.languages ?? ["en"]).join(", ")}</bdi>
                </dd>
                {draft.start_year == null ? <dd className="text-xs text-ink-muted">{t("explore.defaultYear", { year: String(DEFAULT_YEAR) })}</dd> : null}
              </div>
            </dl>
            <ModeControl locale={locale} semantic={semantic} onChange={setSemantic} />
            <p className="mt-3 text-sm text-ink">{t("explore.first.body", { max: String(POOL_MAX) })}</p>
            <div className="mt-3">
              <KeyLines locale={locale} keys={recon.keys} emptyNote />
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <Button variant="primary" disabled={!canSearch} onClick={() => void search(false, semantic)} aria-describedby={topic ? undefined : "explore-need-topic"} data-search>
                {t("explore.first.go")}
              </Button>
              {!topic ? (
                <a id="explore-need-topic" className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "scope", draftId, origin)}>
                  {t("explore.first.needTopic")}
                </a>
              ) : null}
              {offline ? <span className="text-sm text-ink-muted">{t("explore.offline")}</span> : null}
            </div>
          </section>
        ) : null}

        {usable && poolError ? <InceptionRefusal locale={locale} refusal={poolError} draftId={draftId} origin={origin} onRetry={() => void readPool()} /> : null}

        {usable && pool ? (
          <PoolView
            locale={locale}
            pool={pool}
            latestCached={!!latest?.served_from_cache && latest.fingerprint === pool.pool.fingerprint}
            poolHeading={poolHeading}
            canSearch={canSearch}
            semantic={semantic}
            setSemantic={setSemantic}
            onRefresh={(withSemantic, from) => askSearch(withSemantic, from)}
            offline={offline}
            asOf={asOf}
          />
        ) : null}

        {latest ? (
          <section aria-labelledby="legs-title" className="rounded-lg border border-rule bg-leaf p-5" data-databases>
            <h2 id="legs-title" className="font-semibold text-ink">
              {t("explore.legs.title")}
            </h2>
            <p className="text-xs text-ink-muted">
              {rt("explore.legs.latest", { date: <Ltr>{stamp(latest.at ?? latest.created_at)}</Ltr> })}
            </p>
            <div className="mt-3">
              <KeyLines locale={locale} keys={recon?.keys} />
            </div>
            <LegsList locale={locale} legs={latest.legs.map((l) => ({ ...l, notes: l.notes ?? [] }))} />
            <p className="mt-2 text-xs text-ink-muted">{t("explore.legs.neverEmpty")}</p>
          </section>
        ) : null}

        {usable && concepts ? <ConceptsCard locale={locale} report={concepts} href={inceptionHref(locale, "criteria", draftId, origin)} /> : null}

        {usable && pool ? (
          <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
            <ReadingCard locale={locale} pool={pool} allTopics={allTopics} setAllTopics={setAllTopics} />
            <PapersCard locale={locale} pool={pool} sort={sort} setSort={setSort} all={allPapers} setAll={setAllPapers} />
          </div>
        ) : null}

        <div className="flex flex-wrap items-center justify-end gap-3">
          <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "scope", draftId, origin)} data-change-scope>
            {t("explore.change")}
          </a>
          <a className="inline-flex min-h-11 items-center rounded-md border border-rule-strong bg-leaf px-4 text-ink" href={inceptionHref(locale, "", "", origin)}>
            {t("saveAndExit")}
          </a>
          {usable ? (
            <Button variant="primary" disabled={offline || running} onClick={() => window.location.assign(inceptionHref(locale, "direction", draftId, origin))} data-next>
              {nextLabel}
            </Button>
          ) : null}
          {usable && offline ? <span className="text-sm text-ink-muted">{t("explore.offline")}</span> : null}
        </div>
      </div>
      {warn ? (
        <RefreshWarning
          locale={locale}
          direction={groundingLabel}
          date={stamp(grounding?.pool?.created_at)}
          onKeep={closeWarn}
          onGo={() => void search(true, warn.semantic)}
        />
      ) : null}
    </InceptionFrame>
  );
}

function ModeControl({ locale, semantic, onChange }: Readonly<{ locale: Locale; semantic: boolean; onChange: (v: boolean) => void }>) {
  const t = inceptionT(locale);
  return (
    <fieldset className="mt-3" data-mode>
      <legend className="text-sm text-ink-muted">{t("explore.mode.legend")}</legend>
      <div role="radiogroup" className="mt-1 flex flex-wrap gap-4">
        {([false, true] as const).map((value) => (
          <label key={String(value)} className="inline-flex min-h-11 cursor-pointer items-center gap-2 text-sm text-ink">
            <input type="radio" name="explore-mode" checked={semantic === value} onChange={() => onChange(value)} className="h-5 w-5" />
            {value ? t("explore.mode.semantic") : t("explore.mode.keyword")}
          </label>
        ))}
      </div>
      <p className="text-xs text-ink-muted">{t("explore.mode.help")}</p>
    </fieldset>
  );
}

function PoolView({
  locale,
  pool,
  latestCached,
  poolHeading,
  canSearch,
  semantic,
  setSemantic,
  onRefresh,
  offline,
  asOf,
}: Readonly<{
  locale: Locale;
  pool: Distilled;
  latestCached: boolean;
  poolHeading: RefObject<HTMLHeadingElement | null>;
  canSearch: boolean;
  semantic: boolean;
  setSemantic: (v: boolean) => void;
  onRefresh: (semantic: boolean, from: HTMLElement | null) => void;
  offline: boolean;
  asOf: string;
}>) {
  const t = inceptionT(locale);
  const rt = inceptionRichT(locale);
  const summary = pool.pool;
  const { pool: size, purity } = pool.gates;
  const partial = summary.status === "partial" || summary.legs.some((l) => l.status === "failed");
  const qei = pool.qei;
  return (
    <>
      <section aria-labelledby="pool-title" className="rounded-lg border border-rule bg-leaf p-5" data-pool data-pool-status={summary.status}>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <h2 id="pool-title" ref={poolHeading} tabIndex={-1} className="font-semibold text-ink">
              {t("explore.pool.title", { n: String(summary.n_docs) })}
            </h2>
            <p className="text-sm text-ink-muted" data-pool-meta>
              <span>
                {rt("explore.pool.meta", {
                  date: <Ltr>{stamp(summary.created_at)}</Ltr>,
                  mode: summary.semantic ? t("explore.mode.semantic") : t("explore.mode.keyword"),
                  from: summary.year_min == null ? "" : String(summary.year_min),
                  to: summary.year_max == null ? t("explore.first.toPresent") : String(summary.year_max),
                  languages: <Ltr>{(summary.languages ?? []).join(", ")}</Ltr>,
                })}
              </span>
            </p>
            <p className="text-xs text-ink-muted">{t("explore.pool.langNote")}</p>
            <p className="mt-1 flex flex-wrap items-center gap-2 text-xs text-ink-muted">
              {latestCached ? <span data-cached>{t("explore.pool.cached")}</span> : null}
              {partial ? <DecisionBadge role="unclear">{t("explore.pool.partial")}</DecisionBadge> : null}
              <span>
                {t("explore.pool.fingerprint", { fingerprint: "" })}
                <DataCell>{shortFingerprint(summary.fingerprint)}</DataCell>
              </span>
              {offline && asOf ? <span>{t("explore.asOf", { time: stamp(asOf) })}</span> : null}
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <Button disabled={!canSearch} onClick={(event) => onRefresh(semantic, event.currentTarget)} data-refresh>
              {t("explore.pool.refresh")}
            </Button>
          </div>
        </div>
        <ModeControl locale={locale} semantic={semantic} onChange={setSemantic} />
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          <section aria-labelledby="tile-size" className="rounded-md border border-rule bg-paper p-3" data-tile="size" data-sufficient={size.sufficient ? "true" : "false"}>
            <h3 id="tile-size" className="text-xs text-ink-muted">
              {t("explore.tile.size.title")}
            </h3>
            {size.sufficient ? (
              <>
                <DecisionBadge role="include">{t("explore.tile.size.ok")}</DecisionBadge>
                <p className="mt-1 text-ink">
                  {t("explore.tile.size.value", { n: String(size.n_docs), max: String(summary.max_docs) })}
                </p>
                <p className="text-xs text-ink-muted">{t("explore.tile.size.raw", { threshold: String(size.threshold) })}</p>
              </>
            ) : (
              <>
                <DecisionBadge role="unclear">{t("explore.tile.size.thin", { n: String(size.n_docs) })}</DecisionBadge>
                <p className="mt-1 text-sm text-ink">{t("explore.tile.size.thinBody", { threshold: String(size.threshold) })}</p>
                <p className="text-xs text-ink-muted">{t("explore.tile.size.thinRaw", { n: String(size.n_docs), threshold: String(size.threshold) })}</p>
                <Button className="mt-2" disabled={!canSearch} onClick={(event) => onRefresh(true, event.currentTarget)} data-thin-semantic>
                  {t("explore.thin.semantic")}
                </Button>
              </>
            )}
          </section>
          <section aria-labelledby="tile-spread" className="rounded-md border border-rule bg-paper p-3" data-tile="spread" data-purity={purity.label}>
            <h3 id="tile-spread" className="text-xs text-ink-muted">
              {t("explore.tile.spread.title")}
            </h3>
            {purity.label === "indeterminate" ? (
              <>
                <DecisionBadge role="exclude">{t("explore.tile.spread.none")}</DecisionBadge>
                <p className="mt-1 text-sm text-ink">{t("explore.tile.spread.noneBody")}</p>
              </>
            ) : (
              <>
                <DecisionBadge role={purity.label === "coherent" ? "include" : "unclear"}>
                  {purity.label === "coherent" ? t("explore.tile.spread.coherent") : purity.label === "fragmented" ? t("explore.tile.spread.fragmented") : purity.label}
                </DecisionBadge>
                {purity.top3_share != null ? (
                  <>
                    <p className="mt-1 text-ink">{t("explore.tile.spread.value", { pct: String(Math.round(purity.top3_share * 100)) })}</p>
                    <p className="text-xs text-ink-muted">
                      {t("explore.tile.spread.raw", { share: String(purity.top3_share), threshold: String(purity.threshold) })}
                    </p>
                  </>
                ) : null}
              </>
            )}
          </section>
          {qei != null ? (
            <section aria-labelledby="tile-echo" className="rounded-md border border-rule bg-paper p-3" data-tile="echo">
              <h3 id="tile-echo" className="text-xs text-ink-muted">
                {t("explore.tile.echo.title")}
              </h3>
              <p className="mt-1 text-ink">
                {t("explore.tile.echo.value", { qei: String(qei) })}
              </p>
              <p className="text-xs text-ink-muted">{t("explore.tile.echo.body")}</p>
            </section>
          ) : null}
        </div>
        <p className="mt-3 text-xs text-ink-muted">{t("explore.pool.refreshNote")}</p>
      </section>
      {partial ? (
        <PartialBanner
          locale={locale}
          legs={summary.legs.map((l) => ({ ...l, notes: l.notes ?? [] }))}
          action={
            <Button disabled={!canSearch} onClick={(event) => onRefresh(semantic, event.currentTarget)} data-search-again>
              {t("explore.partial.again")}
            </Button>
          }
        />
      ) : null}
    </>
  );
}

function ConceptsCard({ locale, report, href }: Readonly<{ locale: Locale; report: ConceptReport; href: string }>) {
  const t = inceptionT(locale);
  const suggested = report.concepts.some((c) => c.source === "suggested");
  return (
    <section aria-labelledby="concepts-title" className="rounded-lg border border-rule bg-leaf p-5" data-concepts>
      <h2 id="concepts-title" className="font-semibold text-ink">
        {t("explore.concepts.title")}
      </h2>
      {suggested ? <p className="text-sm text-ink-muted" data-suggested-concepts>{t("explore.concepts.suggested")}</p> : null}
      <ul className="mt-2 space-y-1 text-sm">
        {report.concepts.map((c) => (
          <li key={c.concept} data-concept-line={c.concept}>
            <bdi dir="auto">{t("explore.concepts.line", { concept: c.concept, anchored: String(c.anchored_in), total: String(report.n_docs) })}</bdi>
            {c.anchored_in === 0 ? (
              <>
                {" "}
                <DecisionBadge role="unclear">{t("explore.concepts.none")}</DecisionBadge>
              </>
            ) : null}
          </li>
        ))}
      </ul>
      <p className="mt-2 text-xs text-ink-muted">{t("explore.concepts.note")}</p>
      <a className="inline-flex min-h-11 items-center text-brand underline" href={href}>
        {t("explore.concepts.edit")}
      </a>
    </section>
  );
}

function ReadingCard({ locale, pool, allTopics, setAllTopics }: Readonly<{ locale: Locale; pool: Distilled; allTopics: boolean; setAllTopics: (v: boolean) => void }>) {
  const t = inceptionT(locale);
  const largest = Math.max(1, ...pool.schools.map((s) => s.n));
  const topics = allTopics ? pool.topics : pool.topics.slice(0, TOPICS_SHOWN);
  const chips = [...pool.metrics, ...pool.datasets];
  return (
    <section aria-labelledby="reading-badge" className="min-w-0 rounded-lg border border-dashed border-ink-muted bg-leaf p-5" data-reading>
      <p id="reading-badge" className="text-xs font-semibold text-ink-muted">
        {t("explore.reading.badge")}
      </p>
      <p className="text-xs text-ink-muted">{t("explore.reading.source")}</p>
      <h2 className="mt-3 font-semibold text-ink">{t("explore.schools.title")}</h2>
      <ul className="mt-2 space-y-2">
        {pool.schools.map((s) => (
          <li key={s.label} className="text-sm" data-school={s.label}>
            <div className="flex flex-wrap justify-between gap-2">
              <span dir="auto" className="text-ink">
                {s.label}
              </span>
              <span className="text-ink-muted">
                {s.n === 1 ? t("explore.schools.one") : t("explore.schools.count", { n: String(s.n) })}
              </span>
            </div>
            <div aria-hidden="true" className="mt-1 h-2 rounded-sm bg-rule">
              <div className="h-2 rounded-sm bg-brand" style={{ width: `${Math.round((s.n / largest) * 100)}%` }} />
            </div>
          </li>
        ))}
      </ul>
      {pool.schools.some((s) => s.n === 1) ? <p className="mt-2 text-xs text-ink-muted" data-one-paper-note>{t("explore.schools.oneNote")}</p> : null}
      {pool.gates.purity.label !== "indeterminate" && pool.topics.length ? (
        <>
          <h2 className="mt-4 font-semibold text-ink">{t("explore.topics.title")}</h2>
          <ul className="mt-2 flex flex-wrap gap-2">
            {topics.map((topic) => (
              <li key={topic.label} className="rounded-sm border border-rule px-2 py-1 text-sm text-ink" dir="auto">
                {topic.label} · <bdi dir="ltr">{String(topic.n)}</bdi>
              </li>
            ))}
          </ul>
          {pool.topics.length > TOPICS_SHOWN ? (
            <Button variant="quiet" className="px-0" onClick={() => setAllTopics(!allTopics)} aria-expanded={allTopics}>
              {allTopics ? t("explore.papers.less") : t("explore.topics.more", { n: String(pool.topics.length - TOPICS_SHOWN) })}
            </Button>
          ) : null}
        </>
      ) : null}
      {chips.length ? (
        <>
          <h2 className="mt-4 font-semibold text-ink">{t("explore.metrics.title")}</h2>
          <ul className="mt-2 flex flex-wrap gap-2">
            {chips.map((chip) => (
              <li key={chip.label} className="rounded-sm border border-rule px-2 py-1 text-sm text-ink" dir="auto">
                {chip.label} · <bdi dir="ltr">{String(chip.count)}</bdi>
              </li>
            ))}
          </ul>
        </>
      ) : null}
    </section>
  );
}

function PapersCard({
  locale,
  pool,
  sort,
  setSort,
  all,
  setAll,
}: Readonly<{ locale: Locale; pool: Distilled; sort: PaperSort; setSort: (s: PaperSort) => void; all: boolean; setAll: (v: boolean) => void }>) {
  const t = inceptionT(locale);
  const rows = [...pool.papers];
  if (sort === "year") rows.sort((a, b) => (b.year ?? 0) - (a.year ?? 0));
  else if (sort === "title") rows.sort((a, b) => String(a.title ?? "").localeCompare(String(b.title ?? "")));
  const shown = all ? rows : rows.slice(0, PAPERS_SHOWN);
  const anchors = (n: number) => (n === 0 ? t("explore.papers.anchors.none") : n === 1 ? t("explore.papers.anchors.one") : t("explore.papers.anchors", { n: String(n) }));
  const header = (key: PaperSort, label: string) => (
    <th scope="col" aria-sort={sort === key ? (key === "year" ? "descending" : key === "anchors" ? "descending" : "ascending") : "none"} className="py-1 pe-2 text-start font-medium">
      <button type="button" className="min-h-11 text-ink underline decoration-transparent hover:decoration-ink" onClick={() => setSort(key)}>
        {label}
      </button>
    </th>
  );
  return (
    <section aria-labelledby="papers-title" className="min-w-0 rounded-lg border border-rule bg-leaf p-5" data-papers>
      <h2 id="papers-title" className="font-semibold text-ink">
        {t("explore.papers.title", { n: String(pool.papers.length) })}
      </h2>
      <p className="text-xs text-ink-muted">{t("explore.papers.sorted")}</p>
      <table className="mt-2 w-full table-fixed text-sm">
        <caption className="sr-only">{t("explore.papers.title", { n: String(pool.papers.length) })}</caption>
        <thead>
          <tr className="text-ink-muted">
            {header("title", t("explore.papers.col.paper"))}
            <th scope="col" className="w-16 py-1 pe-2 text-start font-medium" aria-sort={sort === "year" ? "descending" : "none"}>
              <button type="button" className="min-h-11 text-ink underline decoration-transparent hover:decoration-ink" onClick={() => setSort("year")}>
                {t("explore.papers.col.year")}
              </button>
            </th>
            {header("anchors", t("explore.papers.col.anchors"))}
          </tr>
        </thead>
        <tbody>
          {shown.map((paper, index) => (
            <tr key={paper.doi ?? `${paper.title}-${index}`} className="border-t border-rule align-top" data-paper={paper.doi ?? ""}>
              <td className="py-2 pe-2">
                <span dir="auto" className="block text-ink [overflow-wrap:anywhere]">
                  {paper.title}
                </span>
                {paper.doi ? <DoiLink locale={locale} doi={paper.doi} title={paper.title} /> : <span className="text-xs text-ink-muted">{t("explore.papers.noDoi")}</span>}
              </td>
              <td className="py-2 pe-2" dir="ltr">
                {paper.year ?? ""}
              </td>
              <td className="py-2 pe-2 text-ink-muted">{anchors(paper.directions_anchored)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > PAPERS_SHOWN ? (
        <Button variant="quiet" className="px-0" onClick={() => setAll(!all)} aria-expanded={all}>
          {all ? t("explore.papers.less") : t("explore.papers.more", { n: String(rows.length - PAPERS_SHOWN) })}
        </Button>
      ) : null}
      <p className="mt-2 text-xs text-ink-muted">{t("explore.papers.note")}</p>
    </section>
  );
}
