"use client";

import { useCallback, useEffect, useId, useRef, useState, type ReactNode, type RefObject } from "react";

import type { Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge, Fold, Hint, RecommendedBadge } from "@/components/ui/base";
import { guidanceT } from "@/lib/guidance-copy";
import { DatabasePicker } from "@/components/database-picker";
import { inceptionHref, InceptionFrame, InceptionRefusal, refusalOf, StepHeader, useDraft, type Refusal } from "@/components/inception-frame";
import { StepAssist } from "@/components/inception-assist";
import { LeftOutList, RowError, SampleDialogView, SampleRefusal, SampleToastView, useSampleCuration, type Curation, type PoolRead } from "@/components/inception-sample";

import {
  DoiLink,
  isOffline,
  KeyLines,
  LegsList,
  PartialBanner,
  partsText,
  providerLabel,
  ProgressCard,
  RefreshWarning,
  shortFingerprint,
  stamp,
  useReconJob,
  yearsText,
} from "@/components/inception-recon";
import { inceptionT, type InceptionCopyKey } from "@/lib/inception-copy";
import { probeStateKey } from "@/lib/screening-states";
import { inceptionRichT, Ltr } from "@/components/rich-copy";
import {
  DEFAULT_DATABASES,
  distill,
  getConcepts,
  getDirections,
  getRecon,
  hasUsablePool,
  latestUsableProbe,
  QUERY_MAX,
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
 *
 * M10a (decided 2026-11-14, item 1a): the query sent to the databases and the
 * databases asked, in order, are probe parameters too. They are pre-filled
 * from the latest topic probe (its `query` and `providers`), else from the
 * engine's `derived_query` and `databases_available`; the topic sentence is
 * never changed by them.
 */

const KNOWN_DATABASES = ["openalex", "semanticscholar", "crossref", "arxiv"];

/** Characters as the engine counts them (code points), not UTF-16 units. */
const length = (text: string) => [...text].length;

const DEFAULT_YEAR = 2000;
const POOL_MAX = 25;
const PAPERS_SHOWN = 5;
const TOPICS_SHOWN = 4;

type PaperSort = "anchors" | "year" | "title";

export function InceptionExplore({ locale }: Readonly<{ locale: Locale }>) {
  const t = inceptionT(locale);
  const rt = inceptionRichT(locale);
  const state = useDraft();
  const { draft, origin, draftId, record, bumpAssist, adopt, adoptTime } = state;
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
  const [query, setQuery] = useState("");
  const [databases, setDatabases] = useState<string[]>([]);
  const prefilled = useRef(false);
  const queryField = useRef<HTMLInputElement>(null);
  const progressHeading = useRef<HTMLHeadingElement>(null);
  const poolHeading = useRef<HTMLHeadingElement>(null);
  const opener = useRef<HTMLElement | null>(null);

  /**
   * Once per load: the latest topic probe's query and databases, else what the
   * engine would send. A narrower probe's query is a direction label, never the
   * topic's query, so only topic probes count. Once the question changed after
   * that probe (`scope_changes` names `topic`), its query belongs to the old
   * question: the field takes the new `derived_query`; the databases stay.
   */
  const prefill = useCallback((read: ReconState) => {
    if (prefilled.current) return;
    prefilled.current = true;
    const available = read.databases_available ?? DEFAULT_DATABASES;
    const probe = [...(read.session?.probes ?? [])].reverse().find((p) => p.purpose === "topic") ?? null;
    const asked = (probe?.providers ?? []).filter((id) => available.includes(id));
    const questionChanged = (read.scope_changes ?? []).includes("topic");
    setQuery((questionChanged ? null : probe?.query) ?? read.derived_query ?? "");
    setDatabases(asked.length ? asked : [...available]);
  }, []);

  const readSeq = useRef(0);
  /**
   * The pool, its directions and the concepts, read together. A read that a
   * later one overtook is dropped (M10b Part C: two sample changes in a row),
   * so the screen never shows an older answer over a newer one.
   */
  const readPool = useCallback(async (): Promise<PoolRead> => {
    const mine = ++readSeq.current;
    const [d, dirs, c] = await Promise.allSettled([distill(origin, draftId), getDirections(origin, draftId), getConcepts(origin, draftId)]);
    if (mine !== readSeq.current) return null;
    if (d.status === "fulfilled") {
      setPool(d.value);
      setPoolError(null);
    } else setPoolError(refusalOf(d.reason));
    const n = dirs.status === "fulfilled" ? dirs.value.directions.length : null;
    setNDirections(n);
    setConcepts(c.status === "fulfilled" ? c.value : null);
    return { directions: n, papers: d.status === "fulfilled" ? d.value.pool.n_docs : null };
  }, [origin, draftId]);

  /** After a sample change: the binding may now be out of date (`SAMPLE_CHANGED`), read from the session. */
  const rereadRecon = useCallback(async () => {
    try {
      setRecon(await getRecon(origin, draftId));
    } catch {
      // The pool on screen stays; the next read of the session says more.
    }
  }, [origin, draftId]);

  const running = !!jobId;
  const curation = useSampleCuration({
    locale,
    origin,
    draftId,
    record,
    draft,
    bound: !!recon?.grounding && !recon?.binding?.stale,
    grounded: !!recon?.grounding,
    directions: nDirections,
    generation: latestUsableProbe(recon)?.fingerprint ?? "",
    searching: running,
    readPool,
    rereadRecon,
    adoptTime,
    adopt,
    bumpAssist,
  });
  const readSample = curation.read;

  const loadRecon = useCallback(async () => {
    try {
      const read = await getRecon(origin, draftId);
      setRecon(read);
      prefill(read);
      setReconError(null);
      setAsOf(new Date().toISOString());
      if (read.active_job && read.active_job.state === "running") setJobId(read.active_job.job_id);
      if (hasUsablePool(read)) await Promise.all([readPool(), readSample()]);
      return read;
    } catch (error) {
      setReconError(refusalOf(error));
      return null;
    }
  }, [origin, draftId, readPool, readSample, prefill]);

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
      bumpAssist();
    },
    [loadRecon, bumpAssist],
  );
  const progress = useReconJob(origin, draftId, jobId, onEnd);

  const offline = isOffline(reconError?.code) || isOffline(startError?.code);
  const mailto = recon?.mailto_set !== false;
  const usable = hasUsablePool(recon);
  const topic = (draft.topic ?? "").trim();
  const tooLong = length(query.trim()) > QUERY_MAX;
  const noDatabase = databases.length === 0;
  // The screen keeps the engine's 422s out of normal use: no request without a database or with an over-long query.
  const canSearch = !!recon && mailto && !running && !offline && !!topic && !noDatabase && !tooLong;

  /** Every path to a probe goes through here, the refusal cards' "Search again" included, so the screen's checks hold for all. */
  const search = async (refresh: boolean, withSemantic: boolean) => {
    if (!canSearch) return;
    setWarn(null);
    setStartError(null);
    setJobError(null);
    setNotFound(false);
    try {
      // The field is sent trimmed; an empty one sends no query and the engine derives it.
      const sent = query.trim();
      const { job } = await startProbe(origin, draftId, { refresh, semantic: withSemantic, databases, ...(sent ? { query: sent } : {}) });
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

  /** A refusal card's "Search again" only while a search could be sent; otherwise the card shows no button. */
  const searchAgain = canSearch ? () => void search(true, semantic) : undefined;
  /** An unreachable engine at start is retried by reading the session again, which clears the offline state. */
  const reconnect = () => {
    setStartError(null);
    void loadRecon();
  };
  /** Why the search buttons are disabled, for their `aria-describedby` (the ids exist only while the reason holds). */
  const reasons = [tooLong ? "explore-query-long" : "", noDatabase && recon ? "explore-need-database" : ""].filter(Boolean);
  const reasonIds = reasons.join(" ") || undefined;
  const available = recon?.databases_available ?? DEFAULT_DATABASES;
  // The query field is on screen in the first-search card, the pool card, or on its own when the pool cannot be read.
  const fieldAlone = !!recon && usable && !pool && !!poolError && !running;
  const fieldShown = !!recon && ((!usable && !running) || (usable && !!pool) || fieldAlone);
  const editQuery = () => queryField.current?.focus();
  const controls = recon ? (
    <SearchControls
      locale={locale}
      query={query}
      setQuery={setQuery}
      derived={recon.derived_query ?? null}
      tooLong={tooLong}
      available={available}
      databases={databases}
      setDatabases={setDatabases}
      disabled={running || offline}
      fieldRef={queryField}
    />
  ) : null;
  const latest = recon?.session?.latest ?? null;
  const grounding = recon?.grounding ?? null;
  const groundingLabel = grounding?.direction?.label ?? "";

  const nextLabel = nDirections === null || nDirections === 0 ? t("explore.next.none") : nDirections === 1 ? t("explore.next.one") : t("explore.next", { n: String(nDirections) });

  const failedLegs = ((jobError?.details as { legs?: ReconLeg[] } | undefined)?.legs ?? []).map((l) => ({ ...l, notes: l.notes ?? [] }));
  // M10b Part C (C4): an empty or failed search shows one per-database list, its own; the earlier probe's card comes back with a pool.
  const emptySearch = (jobError?.code === "POOL_EMPTY" || jobError?.code === "PROVIDERS_FAILED") && failedLegs.length > 0;
  // The engine says when a shorter query may help (`details.shorten`); the browser never counts the words.
  const shorten = jobError?.code === "POOL_EMPTY" && (jobError.details as { shorten?: unknown } | undefined)?.shorten === true;

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
            <Button className="mt-2" disabled={!canSearch} onClick={(event) => askSearch(semantic, event.currentTarget)} aria-describedby={reasonIds}>
              {t("explore.changed.action")}
            </Button>
          </section>
        ) : null}
        {recon?.binding?.stale ? (
          <section className="rounded-lg border border-unclear bg-leaf p-4" data-stale-binding={recon.binding.code ?? ""}>
            {/* M10b Part C: a direction made out of date by the papers left out says so in its own words. */}
            <p className="text-ink">{recon.binding.code === "SAMPLE_CHANGED" ? t("sample.stale.body") : t("explore.stale.body")}</p>
            <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "direction", draftId, origin)}>
              {recon.binding.code === "SAMPLE_CHANGED" ? t("sample.stale.action") : t("explore.stale.action")}
            </a>
          </section>
        ) : null}

        {startError && !(startError.code === "MAILTO_NOT_SET" && !mailto) ? (
          <div className="space-y-2">
            {/* The probe's own cards (M10a); the screen gives their action as a button below, or none while the field is not on screen. */}
            <InceptionRefusal
              locale={locale}
              refusal={startError}
              draftId={draftId}
              origin={origin}
              onRetry={isOffline(startError.code) ? reconnect : searchAgain}
              copyCode={probeStateKey(startError.code)}
              hideActionLabel={startError.code === "PROVIDER_UNKNOWN" || startError.code === "BODY_INVALID"}
              extraDetails={startError.code === "PROVIDER_UNKNOWN" ? <UnknownNames locale={locale} details={startError.details} /> : null}
            />
            {startError.code === "PROVIDER_UNKNOWN" ? (
              <Button onClick={() => setDatabases([...available])} disabled={running} data-reset-databases>
                {t("explore.picker.reset")}
              </Button>
            ) : null}
            {startError.code === "BODY_INVALID" && fieldShown ? (
              <Button onClick={editQuery} data-edit-query>
                {t("explore.legs.editQuery")}
              </Button>
            ) : null}
          </div>
        ) : null}
        {notFound ? (
          <InceptionRefusal locale={locale} refusal={{ code: "RECON_JOB_NOT_FOUND", message: "" }} draftId={draftId} origin={origin} onRetry={() => void loadRecon()} />
        ) : null}
        {jobError ? (
          <div className="space-y-2" data-job-error={jobError.code}>
            <InceptionRefusal locale={locale} refusal={jobError} draftId={draftId} origin={origin} onRetry={searchAgain} />
            {failedLegs.length ? (
              <section className="rounded-lg border border-rule bg-leaf p-4" aria-labelledby="failed-legs">
                <div className="flex items-center gap-1">
                  <h2 id="failed-legs" className="font-semibold text-ink">
                    {t("explore.legs.title")}
                  </h2>
                  <Hint locale={locale} label={t("explore.legs.title")} text={t("explore.legs.neverEmpty")} textKey="explore.legs.neverEmpty" />
                </div>
                <LegsList locale={locale} legs={failedLegs} />
                {shorten && fieldShown ? (
                  <div className="mt-3 flex flex-wrap items-center gap-3" data-shorten>
                    <p className="text-sm text-ink">{t("explore.legs.shorten")}</p>
                    <Button onClick={editQuery} disabled={running} data-edit-query>
                      {t("explore.legs.editQuery")}
                    </Button>
                  </div>
                ) : null}
              </section>
            ) : null}
          </div>
        ) : null}

        {running ? <ProgressCard locale={locale} legs={progress.legs} lost={progress.lost} headingRef={progressHeading} /> : null}

        {recon && !usable && !running ? (
          <section aria-labelledby="first-title" className="rounded-lg border border-rule bg-leaf p-5" data-first-search data-card="first">
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
            {controls}
            <ModeControl locale={locale} semantic={semantic} onChange={setSemantic} />
            <p className="mt-3 text-sm text-ink">{t("explore.first.body", { max: String(POOL_MAX) })}</p>
            <div className="mt-3">
              <KeyLines locale={locale} keys={recon.keys} emptyNote />
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-3">
              <Button
                variant="primary"
                disabled={!canSearch}
                onClick={() => void search(false, semantic)}
                aria-describedby={[topic ? "" : "explore-need-topic", ...reasons].filter(Boolean).join(" ") || undefined}
                data-search
              >
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

        {fieldAlone ? (
          <div className="rounded-lg border border-rule bg-leaf p-5" data-controls-alone>
            {controls}
          </div>
        ) : null}

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
            controls={controls}
            reasonIds={reasonIds}
          />
        ) : null}

        {noDatabase && recon ? (
          <p id="explore-need-database" className="sr-only" data-need-database>
            {t("explore.picker.none")}
          </p>
        ) : null}

        {/* M10d (03-guidance rule 4): the key lines stay on the page; the per-database list is folded, its failures named in the summary. */}
        {latest && !emptySearch ? (
          <div className="space-y-3">
            {recon?.keys ? (
              <div className="px-1" data-databases-keys>
                <KeyLines locale={locale} keys={recon.keys} />
              </div>
            ) : null}
            <Fold
              locale={locale}
              title={t("explore.legs.title")}
              count={latest.legs.length}
              failed={latest.legs.filter((l) => l.status === "failed").length}
              empty={latest.legs.filter((l) => l.status === "ok" && !l.fetched && !l.reported_total).length}
              headingId="legs-title"
              data-databases
            >
              <p className="flex items-center gap-1 text-xs text-ink-muted">
                <span>{rt("explore.legs.latest", { date: <Ltr>{stamp(latest.at ?? latest.created_at)}</Ltr> })}</span>
                <Hint locale={locale} label={t("explore.legs.title")} text={t("explore.legs.neverEmpty")} textKey="explore.legs.neverEmpty" />
              </p>
              <LegsList locale={locale} legs={latest.legs.map((l) => ({ ...l, notes: l.notes ?? [] }))} />
            </Fold>
          </div>
        ) : null}

        {usable && concepts ? <ConceptsCard locale={locale} report={concepts} href={inceptionHref(locale, "criteria", draftId, origin)} /> : null}

        {usable && pool ? (
          <div className="grid gap-6 lg:grid-cols-[2fr_1fr]">
            <ReadingCard locale={locale} pool={pool} allTopics={allTopics} setAllTopics={setAllTopics} />
            <PapersCard
              locale={locale}
              pool={pool}
              sort={sort}
              setSort={setSort}
              all={allPapers}
              setAll={setAllPapers}
              curation={curation}
              offline={offline}
              asOf={asOf}
              draftId={draftId}
              origin={origin}
            />
          </div>
        ) : null}
        {/* M10b Part C: what a sample change moved, from the engine's two reads. */}
        <p role="status" aria-live="polite" className="sr-only" data-sample-moved>
          {curation.announce}
        </p>

        <StepAssist locale={locale} step="explore" />

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
          goDisabled={!canSearch}
          goDescribedBy={reasonIds}
        />
      ) : null}
      <SampleDialogView locale={locale} curation={curation} direction={groundingLabel} />
    </InceptionFrame>
  );
}

/**
 * `PROVIDER_UNKNOWN` (M10a): each name the engine did not know (`details.unknown`),
 * under Details as Plan and Harvest print them; an empty name shows as `""`.
 */
function UnknownNames({ locale, details }: Readonly<{ locale: Locale; details: unknown }>) {
  const t = inceptionT(locale);
  const unknown = (details as { unknown?: unknown } | undefined)?.unknown;
  if (!Array.isArray(unknown) || !unknown.length) return null;
  return (
    <div className="mt-1 text-sm" data-unknown-providers>
      <p className="text-ink-muted">{t("explore.picker.unknown")}</p>
      <ul className="mt-1 flex flex-wrap gap-x-3 gap-y-1">
        {unknown.map((name, i) => (
          <li key={i}>
            <code className="font-mono text-[0.8125rem] text-ink" dir="ltr" data-unknown-provider>
              {String(name) === "" ? '""' : String(name)}
            </code>
          </li>
        ))}
      </ul>
    </div>
  );
}

function ModeControl({ locale, semantic, onChange }: Readonly<{ locale: Locale; semantic: boolean; onChange: (v: boolean) => void }>) {
  const t = inceptionT(locale);
  const legendId = `mode-${useId().replace(/[^A-Za-z0-9_-]/g, "")}`;
  // The group is named by the legend's words alone, not by the hint button inside the legend.
  return (
    <fieldset className="mt-3" aria-labelledby={legendId} data-mode>
      <legend className="text-sm text-ink-muted">
        <span id={legendId}>{t("explore.mode.legend")}</span>
        <Hint locale={locale} label={t("explore.mode.legend")} text={t("explore.mode.help")} textKey="explore.mode.help" className="ms-1" />
      </legend>
      <div role="radiogroup" className="mt-1 flex flex-wrap gap-4">
        {([false, true] as const).map((value) => (
          <label key={String(value)} className="inline-flex min-h-11 cursor-pointer items-center gap-2 text-sm text-ink">
            <input type="radio" name="explore-mode" checked={semantic === value} onChange={() => onChange(value)} className="h-5 w-5" />
            {value ? t("explore.mode.semantic") : t("explore.mode.keyword")}
          </label>
        ))}
      </div>
    </fieldset>
  );
}

/**
 * The query sent to the databases and the databases to ask (M10a). Both are
 * probe parameters: nothing here is saved, and the topic is never changed.
 */
function SearchControls({
  locale,
  query,
  setQuery,
  derived,
  tooLong,
  available,
  databases,
  setDatabases,
  disabled,
  fieldRef,
}: Readonly<{
  locale: Locale;
  query: string;
  setQuery: (v: string) => void;
  derived: string | null;
  tooLong: boolean;
  available: string[];
  databases: string[];
  setDatabases: (v: string[]) => void;
  disabled: boolean;
  fieldRef: RefObject<HTMLInputElement | null>;
}>) {
  const t = inceptionT(locale);
  const items = available.map((id) => ({ id, label: providerLabel(locale, id) }));
  const idOf = (name: string) => items.find((item) => item.label === name)?.id ?? name;
  /** The row's own sentence for a known database; an unknown one keeps its name. */
  const rowText = (kind: "check" | "up" | "down", name: string) => {
    const id = idOf(name);
    return KNOWN_DATABASES.includes(id) ? t(`explore.picker.${kind}.${id}` as InceptionCopyKey) : name;
  };
  const describedBy = ["explore-query-help", tooLong ? "explore-query-long" : ""].filter(Boolean).join(" ");
  return (
    <div className="mt-4 space-y-4" data-search-controls>
      <div>
        <div className="flex items-center gap-1">
          <label htmlFor="explore-query" className="block text-sm text-ink-muted">
            {t("explore.query.label")}
          </label>
          {/* One hint per label (rule 1.7): with no derived query, the how-to sentence follows the field's own. */}
          <Hint
            locale={locale}
            label={t("explore.query.label")}
            text={derived == null ? `${t("explore.query.help")} ${t("explore.query.emptyHint")}` : t("explore.query.help")}
            textKey="explore.query.help"
            id="explore-query-help"
          />
        </div>
        <input
          id="explore-query"
          ref={fieldRef}
          type="text"
          dir="ltr"
          value={query}
          disabled={disabled}
          onChange={(event) => setQuery(event.target.value)}
          aria-describedby={describedBy}
          aria-invalid={tooLong || undefined}
          className="mt-1 block min-h-11 w-full min-w-0 rounded-md border border-rule-strong bg-paper px-3 font-mono text-[0.8125rem] text-ink disabled:cursor-not-allowed disabled:opacity-50"
          data-query
        />
        {tooLong ? (
          <p id="explore-query-long" role="alert" className="mt-1 text-sm text-unclear" data-query-long>
            {t("explore.query.tooLong")}
          </p>
        ) : null}
        {derived != null && query.trim() !== derived ? (
          <Button variant="quiet" className="px-0" disabled={disabled} onClick={() => setQuery(derived)} data-use-derived>
            {t("explore.query.useDerived")}
          </Button>
        ) : null}
      </div>
      <DatabasePicker
        items={items}
        value={databases}
        onChange={setDatabases}
        disabled={disabled}
        labels={{
          legend: t("explore.picker.legend"),
          orderHelp: t("explore.picker.orderHelp", { max: String(POOL_MAX) }),
          orderHelpHint: { locale, textKey: "explore.picker.orderHelp" },
          check: (name) => rowText("check", name),
          up: (name) => rowText("up", name),
          down: (name) => rowText("down", name),
          moved: (name, position, total) => t("explore.picker.moved", { name, n: String(position), total: String(total) }),
          none: t("explore.picker.none"),
        }}
      />
    </div>
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
  controls,
  reasonIds,
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
  controls: ReactNode;
  /** Why the search buttons are disabled (`aria-describedby`), when they are. */
  reasonIds?: string;
}>) {
  const t = inceptionT(locale);
  const rt = inceptionRichT(locale);
  const summary = pool.pool;
  const { pool: size, purity } = pool.gates;
  const partial = summary.status === "partial" || summary.legs.some((l) => l.status === "failed");
  const qei = pool.qei;
  return (
    <>
      <section aria-labelledby="pool-title" className="rounded-lg border border-rule bg-leaf p-5" data-pool data-pool-status={summary.status} data-card="pool">
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
          <div className="flex flex-wrap items-center gap-1">
            <Button disabled={!canSearch} onClick={(event) => onRefresh(semantic, event.currentTarget)} aria-describedby={reasonIds} data-refresh>
              {t("explore.pool.refresh")}
            </Button>
            <Hint locale={locale} label={t("explore.pool.refresh")} text={t("explore.pool.refreshNote")} textKey="explore.pool.refreshNote" />
          </div>
        </div>
        <ModeControl locale={locale} semantic={semantic} onChange={setSemantic} />
        {controls}
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
                {/* M10d (03-guidance rule 3): marked, never pressed for the researcher. */}
                <p className="mt-2">
                  <RecommendedBadge locale={locale} source={guidanceT(locale)("guidance.recommended.source.poolHealth")} />
                </p>
                <Button className="mt-1" disabled={!canSearch} onClick={(event) => onRefresh(true, event.currentTarget)} aria-describedby={reasonIds} data-thin-semantic>
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
              <div className="flex items-center gap-1">
                <h3 id="tile-echo" className="text-xs text-ink-muted">
                  {t("explore.tile.echo.title")}
                </h3>
                <Hint locale={locale} label={t("explore.tile.echo.title")} text={t("explore.tile.echo.body")} textKey="explore.tile.echo.body" />
              </div>
              <p className="mt-1 text-ink">
                {t("explore.tile.echo.value", { qei: String(qei) })}
              </p>
            </section>
          ) : null}
        </div>
      </section>
      {partial ? (
        <PartialBanner
          locale={locale}
          legs={summary.legs.map((l) => ({ ...l, notes: l.notes ?? [] }))}
          action={
            <Button disabled={!canSearch} onClick={(event) => onRefresh(semantic, event.currentTarget)} aria-describedby={reasonIds} data-search-again>
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
    <section aria-labelledby="concepts-title" className="rounded-lg border border-rule bg-leaf p-5" data-concepts data-card="concepts">
      <div className="flex items-center gap-1">
        <h2 id="concepts-title" className="font-semibold text-ink">
          {t("explore.concepts.title")}
        </h2>
        <Hint locale={locale} label={t("explore.concepts.title")} text={t("explore.concepts.note")} textKey="explore.concepts.note" />
      </div>
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
    <section aria-labelledby="reading-badge" className="min-w-0 rounded-lg border border-dashed border-ink-muted bg-leaf p-5" data-reading data-card="reading">
      <p id="reading-badge" className="text-xs font-semibold text-ink-muted">
        {t("explore.reading.badge")}
      </p>
      <p className="text-xs text-ink-muted">{t("explore.reading.source")}</p>
      <div className="mt-3 flex items-center gap-1">
        <h2 className="font-semibold text-ink">{t("explore.schools.title")}</h2>
        {pool.schools.some((s) => s.n === 1) ? (
          <Hint locale={locale} label={t("explore.schools.title")} text={t("explore.schools.oneNote")} textKey="explore.schools.oneNote" />
        ) : null}
      </div>
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
      {pool.gates.purity.label !== "indeterminate" && pool.topics.length ? (
        <Fold locale={locale} title={t("explore.topics.title")} count={pool.topics.length} className="mt-4 border-0 bg-transparent px-0" data-fold-topics>
          <ul className="flex flex-wrap gap-2">
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
        </Fold>
      ) : null}
      {chips.length ? (
        <Fold locale={locale} title={t("explore.metrics.title")} count={chips.length} className="border-0 bg-transparent px-0" data-fold-metrics>
          <ul className="flex flex-wrap gap-2">
            {chips.map((chip) => (
              <li key={chip.label} className="rounded-sm border border-rule px-2 py-1 text-sm text-ink" dir="auto">
                {chip.label} · <bdi dir="ltr">{String(chip.count)}</bdi>
              </li>
            ))}
          </ul>
        </Fold>
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
  curation,
  offline,
  asOf,
  draftId,
  origin,
}: Readonly<{
  locale: Locale;
  pool: Distilled;
  sort: PaperSort;
  setSort: (s: PaperSort) => void;
  all: boolean;
  setAll: (v: boolean) => void;
  /** M10b Part C: leaving papers out of the sample and putting them back. */
  curation: Curation;
  offline: boolean;
  asOf: string;
  draftId: string;
  origin: string;
}>) {
  const t = inceptionT(locale);
  const leftToggle = useRef<HTMLButtonElement>(null);
  const caption = useRef<HTMLTableCaptionElement>(null);
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
  const sample = curation.sample;
  // The controls need the engine's sample and its keys; an engine without them shows the table as before.
  const curating = !!sample && pool.papers.every((p) => !!p.key);
  const controlsOff = curation.disabled || offline;
  const empty = !!sample && sample.n_docs === 0 && sample.excluded.length > 0;
  /** After "Not relevant" focus goes to the next row's button, or to the table caption after the last row. */
  const focusAfter = (index: number) => () => {
    const next = shown[index + 1]?.key;
    const button = next ? Array.from(document.querySelectorAll<HTMLButtonElement>("[data-mark]")).find((b) => b.dataset.mark === next) : undefined;
    if (button) button.focus();
    else caption.current?.focus();
  };
  // M10d (03-guidance rule 4): the papers are folded behind their title and count; a refusal, the
  // empty sample and the Undo toast of the curation stay outside the fold, so none is one click away.
  return (
    <div className="min-w-0 space-y-3">
      <SampleRefusal locale={locale} curation={curation} draftId={draftId} origin={origin} />
      {empty ? (
        <div className="rounded-md border border-rule bg-paper p-3" data-sample-empty>
          <p className="text-sm text-ink">{t("sample.empty")}</p>
          <Button className="mt-2" disabled={controlsOff} onClick={curation.putAll} data-put-all>
            {t("sample.putAll")}
          </Button>
        </div>
      ) : null}
      {sample && !sample.has_reserve ? (
        <p className="text-xs text-ink-muted" data-no-reserve>
          {t("sample.noReserve")}
        </p>
      ) : null}
      {curating && curation.offline ? (
        <p className="text-xs text-ink-muted" data-sample-offline>
          {t("explore.offline")}
          {asOf ? ` · ${t("explore.asOf", { time: stamp(asOf) })}` : ""}
        </p>
      ) : null}
    <Fold locale={locale} title={t("explore.papers.title", { n: String(pool.papers.length) })} headingId="papers-title" className="min-w-0" data-papers>
      {sample ? (
        <p className="text-sm text-ink" data-sample-count>
          {sample.excluded_in_pool
            ? t("sample.count", { n: String(sample.n_docs), k: String(sample.excluded_in_pool) })
            : t("sample.countNone", { n: String(sample.n_docs) })}
        </p>
      ) : null}
      <p className="flex items-center gap-1 text-xs text-ink-muted">
        <span>{t("explore.papers.sorted")}</span>
        <Hint locale={locale} label={t("explore.papers.title", { n: String(pool.papers.length) })} text={t("explore.papers.note")} textKey="explore.papers.note" />
      </p>
      {rows.length ? (
        <table className="mt-2 w-full table-fixed text-sm">
          <caption ref={caption} tabIndex={-1} className="sr-only">
            {t("explore.papers.title", { n: String(pool.papers.length) })}
          </caption>
          <thead>
            <tr className="text-ink-muted">
              {header("title", t("explore.papers.col.paper"))}
              <th scope="col" className="w-16 py-1 pe-2 text-start font-medium" aria-sort={sort === "year" ? "descending" : "none"}>
                <button type="button" className="min-h-11 text-ink underline decoration-transparent hover:decoration-ink" onClick={() => setSort("year")}>
                  {t("explore.papers.col.year")}
                </button>
              </th>
              {header("anchors", t("explore.papers.col.anchors"))}
              {curating ? (
                <th scope="col" className="w-28 py-1 text-start font-medium">
                  <span className="sr-only">{t("sample.mark")}</span>
                </th>
              ) : null}
            </tr>
          </thead>
          <tbody>
            {shown.map((paper, index) => {
              const key = paper.key ?? "";
              const saving = curation.pending === key;
              return (
                <tr key={paper.key ?? paper.doi ?? `${paper.title}-${index}`} className="border-t border-rule align-top" data-paper={paper.doi ?? ""} data-paper-key={key}>
                  <td className="py-2 pe-2">
                    <span dir="auto" className="block text-ink [overflow-wrap:anywhere]">
                      {paper.title}
                    </span>
                    {paper.doi ? <DoiLink locale={locale} doi={paper.doi} title={paper.title} /> : <span className="text-xs text-ink-muted">{t("explore.papers.noDoi")}</span>}
                    {paper.added_for ? (
                      <span className="mt-1 block" data-added-for={paper.added_for}>
                        <DecisionBadge role="exclude">{t("sample.added")}</DecisionBadge>
                      </span>
                    ) : null}
                  </td>
                  <td className="py-2 pe-2" dir="ltr">
                    {paper.year ?? ""}
                  </td>
                  <td className="py-2 pe-2 text-ink-muted">{anchors(paper.directions_anchored)}</td>
                  {curating ? (
                    <td className="py-2">
                      <Button
                        className="w-full whitespace-normal px-2 text-sm"
                        disabled={controlsOff || saving}
                        aria-busy={saving || undefined}
                        aria-label={t("sample.mark.label", { title: paper.title ?? key })}
                        onClick={(event) => curation.mark(paper, event.currentTarget, focusAfter(index))}
                        data-mark={key}
                      >
                        {t("sample.mark")}
                      </Button>
                      <RowError locale={locale} curation={curation} rowKey={key} />
                    </td>
                  ) : null}
                </tr>
              );
            })}
          </tbody>
        </table>
      ) : null}
      {rows.length > PAPERS_SHOWN ? (
        <Button variant="quiet" className="px-0" onClick={() => setAll(!all)} aria-expanded={all}>
          {all ? t("explore.papers.less") : t("explore.papers.more", { n: String(rows.length - PAPERS_SHOWN) })}
        </Button>
      ) : null}
      {sample ? <LeftOutList locale={locale} curation={curation} toggleRef={leftToggle} /> : null}
    </Fold>
      {/* After the papers, so Undo is near when moving with Tab. */}
      <SampleToastView locale={locale} curation={curation} onClosed={() => setTimeout(() => document.getElementById("papers-title")?.focus(), 0)} />
    </div>
  );
}
