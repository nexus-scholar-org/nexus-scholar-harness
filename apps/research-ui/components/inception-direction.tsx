"use client";

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

import type { Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge } from "@/components/ui/base";
import { DETAILS_LABEL } from "@/components/screening-state-card";
import { inceptionHref, InceptionFrame, InceptionRefusal, refusalOf, StepHeader, useDraft, type Refusal } from "@/components/inception-frame";
import {
  DoiLink,
  isOffline,
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
import {
  bindDirection,
  getDirections,
  getEvidence,
  getRecon,
  getSeeds,
  hasUsablePool,
  latestUsableProbe,
  startProbe,
  type Direction,
  type Directions,
  type Evidence,
  type ProbeRequest,
  type ReconJob,
  type ReconLeg,
  type ReconState,
  type Seeds,
} from "@/lib/recon-api";

/**
 * Step 3, Direction (spec 03, M4d): choose one of at most three directions the
 * first search supports, write your own, or go on without one, and bind the
 * choice to the draft (`POST .../recon/bind`). Then tick the pool papers the
 * discovery Recall check will look for (`golden_seeds`). Nothing is chosen or
 * ticked for the researcher; the order and every count are the engine's.
 */

const MAX_SEEDS = 25;
const DOIS_SHOWN = 2;

/** The engine's `detail` caption, in the reader's language when it has the known shape. */
function detailText(locale: Locale, detail: string | undefined): string {
  const t = inceptionT(locale);
  const match = /^pool (term|vocabulary) observed in (\d+) papers$/.exec(detail ?? "");
  if (!match) return detail ?? "";
  return t(match[1] === "term" ? "direction.card.detail.term" : "direction.card.detail.vocab", { n: match[2] });
}

export function InceptionDirection({ locale }: Readonly<{ locale: Locale }>) {
  const t = inceptionT(locale);
  const state = useDraft();
  const { draft, origin, draftId, record, save, saving, saveError, adopt } = state;
  const [recon, setRecon] = useState<ReconState | null>(null);
  const [reconError, setReconError] = useState<Refusal | null>(null);
  const [found, setFound] = useState<Directions | null>(null);
  const [foundError, setFoundError] = useState<Refusal | null>(null);
  const [seeds, setSeeds] = useState<Seeds | null>(null);
  const [choice, setChoice] = useState<string | null>(null);
  const [ownOpen, setOwnOpen] = useState(false);
  const [own, setOwn] = useState("");
  const [accept, setAccept] = useState(false);
  const [binding, setBinding] = useState(false);
  const [bindError, setBindError] = useState<Refusal | null>(null);
  const [rechoose, setRechoose] = useState(false);
  const [evidence, setEvidence] = useState<Evidence | null>(null);
  const [evidenceError, setEvidenceError] = useState<Refusal | null>(null);
  const [checking, setChecking] = useState(false);
  const [ticks, setTicks] = useState<string[] | null>(null);
  const [seedsSaved, setSeedsSaved] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [startError, setStartError] = useState<Refusal | null>(null);
  const [jobError, setJobError] = useState<Refusal | null>(null);
  const [notFound, setNotFound] = useState(false);
  const [warn, setWarn] = useState<ProbeRequest | null>(null);
  const [leaving, setLeaving] = useState(false);
  const [openDois, setOpenDois] = useState<Record<string, boolean>>({});
  const bindRequest = useRef(0);
  const evidenceRequest = useRef(0);
  const resultHeading = useRef<HTMLHeadingElement>(null);
  const cardsHeading = useRef<HTMLHeadingElement>(null);
  const progressHeading = useRef<HTMLHeadingElement>(null);
  const opener = useRef<HTMLElement | null>(null);

  const loadAll = useCallback(async () => {
    let read: ReconState;
    try {
      read = await getRecon(origin, draftId);
    } catch (error) {
      setReconError(refusalOf(error));
      return;
    }
    setRecon(read);
    setReconError(null);
    if (read.active_job && read.active_job.state === "running") setJobId(read.active_job.job_id);
    if (!hasUsablePool(read)) return;
    try {
      setFound(await getDirections(origin, draftId));
      setFoundError(null);
    } catch (error) {
      setFoundError(refusalOf(error));
    }
    if (read.grounding) {
      getSeeds(origin, draftId).then(setSeeds, () => setSeeds(null));
    }
  }, [origin, draftId]);

  useEffect(() => {
    if (record) void loadAll();
  }, [record?.session_id, loadAll]); // eslint-disable-line react-hooks/exhaustive-deps

  const onEnd = useCallback(
    (job: ReconJob | null, lostJob: boolean) => {
      setJobId(null);
      setStartError(null);
      if (lostJob) setNotFound(true);
      else if (job?.state === "failed" && job.error) setJobError({ code: job.error.code, message: job.error.message, details: job.error.details });
      setChoice(null);
      void loadAll().then(() => cardsHeading.current?.focus());
    },
    [loadAll],
  );
  const progress = useReconJob(origin, draftId, jobId, onEnd);
  const running = !!jobId;

  const grounding = record?.grounding ?? null;
  const stale = !!recon?.binding?.stale;
  const skipped = !!grounding && (grounding.choice === "none" || grounding.direction?.source === "none");
  const bound = !!grounding && !stale;
  const cardsLive = !bound || rechoose;
  const conflict = [bindError, saveError].some((r) => r?.code === "DRAFT_CONFLICT" || r?.code === "DRAFT_EMITTED");
  const offline = isOffline(reconError?.code) || isOffline(bindError?.code) || isOffline(startError?.code);
  const busy = binding || running || saving;
  const thin = !!found && !found.gates.pool.sufficient;
  const mailto = recon?.mailto_set !== false;
  const ownText = ownOpen ? own.trim() : "";
  const pursueLabel = choice ?? (ownText || null);
  const needsAccept = thin || bindError?.code === "POOL_TOO_SMALL";
  const reason = busy ? "busy" : !pursueLabel ? "choose" : needsAccept && !accept ? "thin" : null;
  const canPursue = cardsLive && !reason && !offline && !conflict;

  const savedSeeds = draft.golden_seeds ?? [];
  const ticked = ticks ?? savedSeeds;
  const seedsDirty = JSON.stringify(ticked) !== JSON.stringify(savedSeeds);

  const go = (step: "shape" | "explore" | "") => window.location.assign(inceptionHref(locale, step, step ? draftId : "", origin));

  const pursue = async () => {
    if (!record || !pursueLabel) return;
    const request = ++bindRequest.current;
    setBinding(true);
    setBindError(null);
    const body = choice
      ? { direction: choice, accept_thin_pool: needsAccept ? accept : false, base_updated_at: record.updated_at }
      : { own: ownText, accept_thin_pool: needsAccept ? accept : false, base_updated_at: record.updated_at };
    try {
      const stored = await bindDirection(origin, draftId, body);
      if (request !== bindRequest.current) return;
      adopt(stored);
      setRechoose(false);
      setChoice(null);
      setTicks(null);
      await loadAll();
      setTimeout(() => resultHeading.current?.focus(), 0);
    } catch (error) {
      if (request === bindRequest.current) setBindError(refusalOf(error));
    } finally {
      if (request === bindRequest.current) setBinding(false);
    }
  };

  const skip = async () => {
    if (!record) return;
    const request = ++bindRequest.current;
    setBinding(true);
    setBindError(null);
    try {
      await bindDirection(origin, draftId, { skip: true, base_updated_at: record.updated_at });
      if (request === bindRequest.current) go("shape");
    } catch (error) {
      if (request === bindRequest.current) setBindError(refusalOf(error));
    } finally {
      if (request === bindRequest.current) setBinding(false);
    }
  };

  const check = async () => {
    const term = own.trim();
    const request = ++evidenceRequest.current;
    setChecking(true);
    setEvidenceError(null);
    try {
      const answer = await getEvidence(origin, draftId, term);
      if (request === evidenceRequest.current) setEvidence(answer);
    } catch (error) {
      if (request === evidenceRequest.current) setEvidenceError(refusalOf(error));
    } finally {
      if (request === evidenceRequest.current) setChecking(false);
    }
  };

  const probe = async (body: ProbeRequest) => {
    setWarn(null);
    setStartError(null);
    setJobError(null);
    setNotFound(false);
    try {
      const { job } = await startProbe(origin, draftId, body);
      setJobId(job.job_id);
      setTimeout(() => progressHeading.current?.focus(), 0);
    } catch (error) {
      const refusal = refusalOf(error);
      setStartError(refusal);
      const active = (refusal.details as { job?: ReconJob } | undefined)?.job;
      if (refusal.code === "RECON_JOB_ACTIVE" && active?.job_id) setJobId(active.job_id);
    }
  };

  /** A search that makes a new pool the latest asks first when a direction is bound. */
  const askProbe = (body: ProbeRequest, from: HTMLElement | null) => {
    if (grounding) {
      opener.current = from;
      setWarn(body);
      return;
    }
    void probe(body);
  };

  const closeWarn = () => {
    setWarn(null);
    setTimeout(() => opener.current?.focus(), 0);
  };

  const toggleSeed = (doi: string) => {
    setSeedsSaved(false);
    setTicks(ticked.includes(doi) ? ticked.filter((d) => d !== doi) : ticked.length >= MAX_SEEDS ? ticked : [...ticked, doi]);
  };

  const saveSeeds = async (): Promise<boolean> => {
    if (!seedsDirty) return true;
    const stored = await save({ ...draft, golden_seeds: ticked });
    if (stored) {
      setTicks(null);
      setSeedsSaved(true);
    }
    return stored;
  };

  const exit = async () => {
    if (cardsLive && pursueLabel) {
      setLeaving(true);
      return;
    }
    if (await saveSeeds()) go("");
  };

  const usable = hasUsablePool(recon);
  const directions = found?.directions ?? [];
  const latest = latestUsableProbe(recon);
  const firstTopic = recon?.session?.probes.find((p) => p.purpose === "topic" && p.n_docs > 0) ?? null;
  const fromNarrower = latest?.purpose === "narrower";
  const narrowerLeft = found?.narrower_left ?? recon?.session?.narrower_left ?? 0;
  const failedLegs = ((jobError?.details as { legs?: ReconLeg[] } | undefined)?.legs ?? []).map((l) => ({ ...l, notes: l.notes ?? [] }));
  const pool = found?.pool;
  const changes = recon?.binding?.changes ?? (recon?.binding?.code === "SCOPE_CHANGED" ? (recon.scope_changes ?? []) : []);
  const earlierLabel = stale && grounding && !skipped ? grounding.direction.label : null;

  const primary =
    bound && !rechoose ? (
      <Button variant="primary" disabled={busy || conflict || offline} onClick={() => void saveSeeds().then((ok) => ok && go("shape"))} data-continue>
        {t("direction.continue")}
      </Button>
    ) : (
      <Button variant="primary" disabled={!canPursue} onClick={() => void pursue()} aria-describedby={reason ? `pursue-${reason}` : undefined} data-pursue>
        {pursueLabel ? t("direction.pursue", { direction: pursueLabel }) : t("direction.pursue.empty")}
      </Button>
    );

  return (
    <InceptionFrame locale={locale} current="direction" draft={state}>
      <StepHeader kicker={t("direction.kicker")} title={t("direction.title")} lede={t("direction.lede")} />
      <div className="space-y-6">
        {!recon && !reconError ? (
          <p role="status" aria-busy="true" className="text-ink-muted">
            {t("asking")}
          </p>
        ) : null}
        {reconError && !recon ? <InceptionRefusal locale={locale} refusal={reconError} draftId={draftId} origin={origin} onRetry={() => void loadAll()} /> : null}
        {recon && !mailto ? <InceptionRefusal locale={locale} refusal={{ code: "MAILTO_NOT_SET", message: "" }} draftId={draftId} origin={origin} command="SCHOLAR_MAILTO=<your email>" /> : null}

        {recon && !usable && !running ? (
          <section aria-labelledby="none-pool" className="rounded-lg border border-rule bg-leaf p-5" data-no-pool>
            <h2 id="none-pool" className="font-semibold text-ink">
              {t("direction.none.pool.title")}
            </h2>
            <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "explore", draftId, origin)}>
              {t("direction.none.pool.action")}
            </a>
          </section>
        ) : null}

        {stale ? (
          <section aria-labelledby="stale-title" className="rounded-lg border border-unclear bg-leaf p-4" data-stale>
            <h2 id="stale-title" className="font-semibold text-ink">
              {t("direction.stale.title")}
            </h2>
            <p className="mt-1 text-ink">{t("direction.stale.body")}</p>
            {changes.length ? <p className="mt-1 text-ink" data-stale-parts>{t("direction.stale.parts", { parts: partsText(locale, changes) })}</p> : null}
            <details className="mt-2 text-sm">
              <summary className="min-h-11 cursor-pointer rounded-sm py-3 leading-5 text-ink-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">{DETAILS_LABEL[locale]}</summary>
              {recon?.binding?.reason ? (
                <p dir="ltr" className="text-ink-muted">
                  {recon.binding.reason}
                </p>
              ) : null}
              {recon?.binding?.code ? (
                <p dir="ltr" className="font-mono text-ink-muted">
                  {recon.binding.code}
                </p>
              ) : null}
              <p className="text-ink-muted">
                <bdi dir="ltr">{t("direction.stale.detail", { bound: shortFingerprint(recon?.binding?.bound), current: shortFingerprint(recon?.binding?.current) })}</bdi>
              </p>
            </details>
          </section>
        ) : null}

        {startError ? <InceptionRefusal locale={locale} refusal={startError} draftId={draftId} origin={origin} onRetry={() => void loadAll()} /> : null}
        {notFound ? <InceptionRefusal locale={locale} refusal={{ code: "RECON_JOB_NOT_FOUND", message: "" }} draftId={draftId} origin={origin} onRetry={() => void loadAll()} /> : null}
        {jobError ? (
          <div className="space-y-2" data-job-error={jobError.code}>
            <InceptionRefusal locale={locale} refusal={jobError} draftId={draftId} origin={origin} onRetry={() => void loadAll()} />
            {failedLegs.length ? <LegsList locale={locale} legs={failedLegs} /> : null}
          </div>
        ) : null}
        {foundError ? <InceptionRefusal locale={locale} refusal={foundError} draftId={draftId} origin={origin} onRetry={() => void loadAll()} /> : null}

        {running ? <ProgressCard locale={locale} legs={progress.legs} lost={progress.lost} headingRef={progressHeading} /> : null}

        {usable && found && pool ? (
          <>
            <div className="flex flex-wrap items-center gap-3 text-sm text-ink-muted" data-pool-line>
              <bdi dir="ltr">
                {t("direction.pool.line", {
                  n: String(pool.n_docs),
                  date: stamp(pool.created_at),
                  years: yearsText(locale, pool.year_min, pool.year_max),
                  languages: (pool.languages ?? []).join(", "),
                })}
              </bdi>
              {pool.status === "partial" ? <DecisionBadge role="unclear">{t("explore.pool.partial")}</DecisionBadge> : null}
              <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "explore", draftId, origin)}>
                {t("direction.back")}
              </a>
            </div>
            {fromNarrower ? (
              <section className="rounded-lg border border-rule bg-leaf p-4 text-sm" data-from-narrower>
                <p className="text-ink">
                  <bdi>{t("direction.pool.fromNarrower", { label: latest?.query ?? "" })}</bdi>
                </p>
                {firstTopic && firstTopic.status !== "complete" ? <p className="text-ink-muted">{t("direction.pool.backFirstFresh")}</p> : null}
                <Button className="mt-2" disabled={busy || !mailto || conflict} onClick={(event) => askProbe({ refresh: false, semantic: false }, event.currentTarget)} data-back-first>
                  {t("direction.pool.backFirst")}
                </Button>
              </section>
            ) : null}
            {pool.status === "partial" ? <PartialBanner locale={locale} legs={pool.legs.map((l) => ({ ...l, notes: l.notes ?? [] }))} /> : null}
            {thin && cardsLive ? (
              <section className="rounded-lg border border-unclear bg-leaf p-4" data-thin>
                <h2 className="font-semibold text-ink">{t("direction.thin.title", { n: String(found.gates.pool.n_docs) })}</h2>
                <p className="text-ink">{t("direction.thin.body", { threshold: String(found.gates.pool.threshold) })}</p>
              </section>
            ) : null}

            {bound && !skipped && grounding ? (
              <section aria-labelledby="result-title" aria-live="polite" className="rounded-lg border border-rule bg-leaf p-5" data-bound>
                <h2 id="result-title" ref={resultHeading} tabIndex={-1} className="font-semibold text-ink">
                  <bdi>{t("direction.bound.title", { label: grounding.direction.label })}</bdi>
                </h2>
                <DecisionBadge role={grounding.direction.grounded ? "include" : "unclear"}>
                  {grounding.direction.grounded ? t("direction.bound.grounded") : t("direction.bound.ungrounded")}
                </DecisionBadge>
                <p className="mt-2 text-sm text-ink" data-bound-sentence>
                  {grounding.direction.source === "researcher"
                    ? t(grounding.direction.grounded ? "direction.own.grounded" : "direction.own.ungrounded", {
                        observed: String(grounding.direction.observed_in),
                        total: String(grounding.direction.n_docs),
                      })
                    : t("direction.card.occurs", { observed: String(grounding.direction.observed_in), total: String(grounding.direction.n_docs) })}
                </p>
                <ul className="mt-1 flex flex-wrap gap-x-4">
                  {grounding.direction.anchor_dois.map((doi) => (
                    <li key={doi}>
                      <DoiLink locale={locale} doi={doi} />
                    </li>
                  ))}
                </ul>
                <p className="mt-1 text-xs text-ink-muted">
                  <bdi dir="ltr">{t("direction.bound.at", { date: stamp(grounding.bound_at), pooldate: stamp(grounding.pool?.created_at) })}</bdi> · <DataCell>{shortFingerprint(grounding.pool?.fingerprint)}</DataCell>
                </p>
                {!rechoose ? (
                  <Button className="mt-2" disabled={busy || conflict} onClick={() => setRechoose(true)} data-rechoose>
                    {t("direction.bound.change")}
                  </Button>
                ) : null}
              </section>
            ) : null}
            {bound && skipped ? (
              <section aria-labelledby="result-title" aria-live="polite" className="rounded-lg border border-unclear bg-leaf p-5" data-skipped>
                <h2 id="result-title" ref={resultHeading} tabIndex={-1} className="font-semibold text-ink">
                  {t("direction.skip.none.title")}
                </h2>
                <DecisionBadge role="unclear">{t("direction.skip.none.badge")}</DecisionBadge>
                <p className="mt-2 text-sm text-ink">{t("direction.skip.none.body")}</p>
                {!rechoose ? (
                  <Button className="mt-2" disabled={busy || conflict} onClick={() => setRechoose(true)} data-rechoose>
                    {t("direction.skip.none.change")}
                  </Button>
                ) : null}
              </section>
            ) : null}

            {directions.length ? (
              <fieldset className="min-w-0" data-directions>
                <legend>
                  <h2 id="cards-title" ref={cardsHeading} tabIndex={-1} className="font-semibold text-ink">
                    {t("direction.card.legend")}
                  </h2>
                </legend>
                <div role="radiogroup" aria-labelledby="cards-title" className="mt-2 grid gap-4 md:grid-cols-3">
                  {directions.map((d, index) => (
                    <DirectionCard
                      key={d.label}
                      locale={locale}
                      direction={d}
                      index={index}
                      chosen={cardsLive ? choice === d.label : bound && !skipped && grounding?.direction.label === d.label}
                      earlier={earlierLabel === d.label}
                      disabled={!cardsLive || busy || conflict}
                      onChoose={() => {
                        setChoice(d.label);
                        setOwnOpen(false);
                      }}
                      allDois={!!openDois[d.label]}
                      onShowAll={() => setOpenDois((o) => ({ ...o, [d.label]: !o[d.label] }))}
                    />
                  ))}
                </div>
                <p className="mt-2 text-xs text-ink-muted">{t("direction.card.note")}</p>
              </fieldset>
            ) : (
              <section aria-labelledby="none-dir" className="rounded-lg border border-rule bg-leaf p-5" data-no-direction>
                <h2 id="none-dir" ref={cardsHeading} tabIndex={-1} className="font-semibold text-ink">
                  {t("direction.none.dir.title")}
                </h2>
                <p className="mt-1 text-ink">{t("direction.none.dir.body")}</p>
                <div className="mt-3 flex flex-wrap items-center gap-3">
                  <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "scope", draftId, origin)}>
                    {t("explore.change")}
                  </a>
                  <Button disabled={busy || !mailto || conflict} onClick={(event) => askProbe({ refresh: true, semantic: true }, event.currentTarget)} data-semantic>
                    {t("direction.none.dir.semantic")}
                  </Button>
                </div>
              </section>
            )}

            {cardsLive ? (
              <section className="space-y-3" data-actions>
                <div className="flex flex-wrap items-start gap-3">
                  {directions.length ? (
                    <div>
                      <Button
                        disabled={!choice || narrowerLeft <= 0 || busy || !mailto || conflict || offline}
                        onClick={(event) => choice && askProbe({ narrower: choice }, event.currentTarget)}
                        aria-describedby="narrow-help"
                        data-narrower
                      >
                        {narrowerLeft <= 0 ? t("direction.narrow.button.spent") : t("direction.narrow.button", { n: String(narrowerLeft) })}
                      </Button>
                      <p id="narrow-help" className="mt-1 text-xs text-ink-muted">
                        {choice ? t("direction.narrow.help") : t("direction.narrow.chooseFirst")}
                      </p>
                    </div>
                  ) : null}
                  <Button
                    aria-expanded={ownOpen}
                    disabled={busy || conflict}
                    onClick={() => {
                      setOwnOpen(!ownOpen);
                      setChoice(null);
                    }}
                    data-own-toggle
                  >
                    {t("direction.own.button")}
                  </Button>
                </div>
                {ownOpen ? (
                  <div className="rounded-lg border border-rule bg-leaf p-4" data-own>
                    <label htmlFor="own-direction" className="block text-sm font-medium text-ink">
                      {t("direction.own.label")}
                    </label>
                    <input
                      id="own-direction"
                      dir="auto"
                      value={own}
                      disabled={busy || conflict}
                      onChange={(event) => setOwn(event.target.value)}
                      aria-describedby="own-help"
                      onKeyDown={(event) => {
                        if (event.key === "Enter") event.preventDefault();
                      }}
                      className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink"
                    />
                    <p id="own-help" className="mt-1 text-xs text-ink-muted">
                      {t("direction.own.help")}
                    </p>
                    <Button className="mt-2" disabled={!own.trim() || checking || offline} onClick={() => void check()} data-check-phrase>
                      {checking ? t("direction.own.checking") : t("direction.own.check")}
                    </Button>
                    <div aria-live="polite" data-evidence>
                      {evidence && evidence.term.trim() === own.trim() ? (
                        <div className="mt-2 text-sm">
                          <p className={evidence.observed_in >= 2 ? "text-include" : "text-unclear"}>
                            {t(evidence.observed_in >= 2 ? "direction.own.check.grounded" : "direction.own.check.under", {
                              observed: String(evidence.observed_in),
                              total: String(evidence.n_docs),
                            })}
                          </p>
                          {evidence.anchor_dois.length ? (
                            <>
                              <p className="mt-1 text-xs text-ink-muted">{t("direction.own.dois", { n: String(evidence.anchor_dois.length) })}</p>
                              <ul className="flex flex-wrap gap-x-4">
                                {evidence.anchor_dois.map((doi) => (
                                  <li key={doi}>
                                    <DoiLink locale={locale} doi={doi} />
                                  </li>
                                ))}
                              </ul>
                            </>
                          ) : null}
                        </div>
                      ) : null}
                    </div>
                    {evidenceError ? <InceptionRefusal locale={locale} refusal={evidenceError} draftId={draftId} origin={origin} /> : null}
                  </div>
                ) : null}
                {needsAccept ? (
                  <label className="flex min-h-11 cursor-pointer items-center gap-3 text-sm text-ink" data-accept-thin>
                    <input type="checkbox" checked={accept} disabled={busy || conflict} onChange={(event) => setAccept(event.target.checked)} className="h-5 w-5" />
                    {t("direction.thin.accept")}
                  </label>
                ) : null}
                <div>
                  <Button variant="quiet" className="px-0" disabled={busy || conflict || offline} onClick={() => void skip()} aria-describedby="skip-note" data-skip>
                    {t("direction.skip.link")}
                  </Button>
                  <p id="skip-note" className="text-xs text-ink-muted">
                    {t("direction.skip.note")}
                  </p>
                </div>
              </section>
            ) : null}

            {bindError ? (
              <div className="space-y-1">
                <InceptionRefusal locale={locale} refusal={bindError} draftId={draftId} origin={origin} onRetry={() => void loadAll()} />
                {bindError.code === "POOL_TOO_SMALL" ? (
                  <p className="text-sm text-ink" data-too-small>
                    <bdi dir="ltr">
                      {t("direction.thin.raw", {
                        n: String((bindError.details as { n_docs?: number } | undefined)?.n_docs ?? ""),
                        floor: String((bindError.details as { floor?: number } | undefined)?.floor ?? ""),
                      })}
                    </bdi>
                  </p>
                ) : null}
              </div>
            ) : null}

            {grounding ? (
              <SeedsCard
                locale={locale}
                seeds={seeds}
                ticked={ticked}
                saved={savedSeeds}
                disabled={busy || conflict}
                onToggle={toggleSeed}
                onSave={() => void saveSeeds()}
                dirty={seedsDirty}
                savedNote={seedsSaved && !seedsDirty}
              />
            ) : null}
          </>
        ) : null}

        {saveError ? <InceptionRefusal locale={locale} refusal={saveError} draftId={draftId} origin={origin} /> : null}

        <div className="flex flex-wrap items-center justify-end gap-3">
          <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "explore", draftId, origin)} data-back>
            {t("direction.back")}
          </a>
          <Button onClick={() => void exit()} disabled={saving || conflict}>
            {t("saveAndExit")}
          </Button>
          {usable && found ? primary : null}
        </div>
        {usable && found && !(bound && !rechoose) && reason ? (
          <p id={`pursue-${reason}`} className="text-end text-sm text-ink-muted">
            {reason === "busy" ? t("direction.reason.busy") : reason === "choose" ? t("direction.reason.choose") : t("direction.reason.thin")}
          </p>
        ) : null}
      </div>
      {warn ? (
        <RefreshWarning
          locale={locale}
          direction={grounding?.direction?.label || t("direction.skip.none.title")}
          date={stamp(grounding?.pool?.created_at)}
          onKeep={closeWarn}
          onGo={() => void probe(warn)}
        />
      ) : null}
      {leaving ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4">
          <div
            role="alertdialog"
            aria-modal="true"
            aria-labelledby="leave-title"
            aria-describedby="leave-body"
            className="w-full max-w-lg rounded-lg border border-rule bg-paper p-5"
            onKeyDown={(event) => {
              if (event.key === "Escape") setLeaving(false);
            }}
            data-leave
          >
            <h2 id="leave-title" className="font-semibold text-ink">
              {t("saveAndExit")}
            </h2>
            <p id="leave-body" className="mt-2 text-sm text-ink">
              {t("direction.leave.body")}
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <Button autoFocus onClick={() => setLeaving(false)}>
                {t("direction.leave.stay")}
              </Button>
              <Button onClick={() => void saveSeeds().then((ok) => ok && go(""))}>{t("direction.leave.go")}</Button>
            </div>
          </div>
        </div>
      ) : null}
    </InceptionFrame>
  );
}

function DirectionCard({
  locale,
  direction,
  index,
  chosen,
  earlier,
  disabled,
  onChoose,
  allDois,
  onShowAll,
}: Readonly<{
  locale: Locale;
  direction: Direction;
  index: number;
  chosen: boolean;
  earlier: boolean;
  disabled: boolean;
  onChoose: () => void;
  allDois: boolean;
  onShowAll: () => void;
}>) {
  const t = inceptionT(locale);
  const id = `direction-${index}`;
  const n = direction.anchor_dois.length;
  const dois = allDois ? direction.anchor_dois : direction.anchor_dois.slice(0, DOIS_SHOWN);
  return (
    <div
      className={`min-w-0 rounded-lg bg-leaf p-4 ${chosen ? "border-2 border-brand" : "border border-dashed border-ink-muted"}`}
      data-direction={direction.label}
      data-chosen={chosen ? "true" : "false"}
    >
      <label className="block cursor-pointer">
        <span className="flex items-start gap-3">
          <input
            type="radio"
            name="direction"
            checked={chosen}
            disabled={disabled}
            onChange={onChoose}
            aria-labelledby={`${id}-label`}
            aria-describedby={`${id}-occurs ${id}-detail`}
            className="mt-1 h-5 w-5 shrink-0"
          />
          <span className="min-w-0">
            <span className="block text-xs text-ink-muted">
              {t("direction.card.position", { n: String(index + 1) })} · {t("direction.card.proposal")}
            </span>
            <span id={`${id}-label`} className="block font-semibold text-ink" dir="auto">
              {direction.label}
            </span>
          </span>
        </span>
        <span className="mt-2 flex flex-wrap gap-2">
          <span className="inline-flex items-center rounded-sm border border-rule px-2 py-0.5 text-xs text-ink" dir="ltr">
            {n === 1 ? t("direction.card.anchors.one") : t("direction.card.anchors", { n: String(n) })}
          </span>
          {chosen ? <span className="text-xs font-semibold text-brand">{t("direction.card.selected")}</span> : null}
          {earlier ? <span className="text-xs text-unclear">{t("direction.card.earlier")}</span> : null}
        </span>
        <span id={`${id}-occurs`} className="mt-2 block text-sm text-ink">
          {t("direction.card.occurs", { observed: String(direction.observed_in), total: String(direction.n_docs) })}
        </span>
        <span id={`${id}-detail`} className="block text-xs text-ink-muted">
          {detailText(locale, direction.detail)}
        </span>
        <span className="mt-1 block text-xs text-ink-muted" dir="auto">
          {direction.schools?.length ? t("direction.card.schools", { schools: direction.schools.join(t("list.sep")) }) : t("direction.card.noSchools")}
        </span>
      </label>
      <ul className="mt-2">
        {dois.map((doi) => (
          <li key={doi}>
            <DoiLink locale={locale} doi={doi} />
          </li>
        ))}
      </ul>
      {n > DOIS_SHOWN ? (
        <Button variant="quiet" className="px-0" aria-expanded={allDois} onClick={onShowAll}>
          {allDois ? t("explore.papers.less") : t("direction.card.showAll", { n: String(n) })}
        </Button>
      ) : null}
    </div>
  );
}

function SeedsCard({
  locale,
  seeds,
  ticked,
  saved,
  disabled,
  onToggle,
  onSave,
  dirty,
  savedNote,
}: Readonly<{
  locale: Locale;
  seeds: Seeds | null;
  ticked: string[];
  saved: string[];
  disabled: boolean;
  onToggle: (doi: string) => void;
  onSave: () => void;
  dirty: boolean;
  savedNote: boolean;
}>) {
  const t = inceptionT(locale);
  const papers = seeds?.papers ?? [];
  const listed = new Set(papers.map((p) => p.doi));
  const extra = [...new Set([...saved, ...ticked])].filter((doi) => !listed.has(doi));
  const full = ticked.length >= MAX_SEEDS;
  const row = (doi: string, body: ReactNode, title: string) => {
    const on = ticked.includes(doi);
    const blocked = !on && full;
    return (
      <li key={doi} className={`rounded-md p-3 ${on ? "border border-rule" : "border border-dashed border-ink-muted"}`} data-seed={doi} data-ticked={on ? "true" : "false"}>
        <label className="flex min-h-11 cursor-pointer items-start gap-3">
          <input
            type="checkbox"
            checked={on}
            disabled={disabled || blocked}
            onChange={() => onToggle(doi)}
            aria-label={t("direction.seeds.label", { title, doi })}
            aria-describedby={blocked ? "seeds-max" : undefined}
            className="mt-1 h-5 w-5 shrink-0"
          />
          <span className="min-w-0 text-sm">{body}</span>
        </label>
        <DoiLink locale={locale} doi={doi} title={title} />
      </li>
    );
  };
  return (
    <section aria-labelledby="seeds-title" className="rounded-lg border border-rule bg-leaf p-5" data-seeds>
      <h2 id="seeds-title" className="font-semibold text-ink">
        {t("direction.seeds.title")}
      </h2>
      <p className="text-sm text-ink-muted">{t("direction.seeds.caption")}</p>
      <p className="mt-1 text-sm text-ink" aria-live="polite" data-seeds-count>
        <bdi dir="ltr">{t("direction.seeds.count", { n: String(ticked.length) })}</bdi>
      </p>
      {full ? (
        <p id="seeds-max" className="text-sm text-unclear">
          {t("direction.seeds.max")}
        </p>
      ) : null}
      {seeds && papers.length === 0 && extra.length === 0 ? <p className="mt-2 text-sm text-ink" data-seeds-none>{t("direction.seeds.none")}</p> : null}
      <ul className="mt-3 space-y-2">
        {papers.map((p) =>
          row(
            p.doi,
            <>
              <span className="block text-ink [overflow-wrap:anywhere]" dir="auto">
                {p.title}
              </span>
              <span className="block text-xs text-ink-muted">
                <bdi dir="ltr">{[p.year, p.provider].filter((v) => v != null && v !== "").join(" · ")}</bdi>
              </span>
              <span className="block text-xs text-ink-muted" dir="auto">
                {t("direction.seeds.anchors", { anchors: [...p.anchors.directions, ...p.anchors.concepts].join(t("list.sep")) })}
              </span>
            </>,
            p.title ?? "",
          ),
        )}
        {extra.map((doi) =>
          row(
            doi,
            <span className="block text-xs text-ink-muted" data-seed-saved-only>
              {t("direction.seeds.saved")}
            </span>,
            "",
          ),
        )}
      </ul>
      <div className="mt-3 flex flex-wrap items-center gap-3">
        <Button disabled={disabled || !dirty} onClick={onSave} data-save-seeds>
          {t("direction.seeds.save")}
        </Button>
        {savedNote ? (
          <span role="status" className="text-sm text-include">
            {t("direction.seeds.savedNote")}
          </span>
        ) : null}
      </div>
    </section>
  );
}
