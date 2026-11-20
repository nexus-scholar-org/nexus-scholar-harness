"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { DiscoveryChecksPanel, EarlierChecksLine } from "@/components/discovery-checks";

import type { Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge, GatePanel, Hint, PRIMARY_LINK } from "@/components/ui/base";
import {
  DiscoveryFrame,
  DiscoveryRefusal,
  Eyebrow,
  LINK,
  Loading,
  discoveryHref,
  percent,
  refusalOf,
  screeningHomeHref,
  stamp,
  useDiscoveryParams,
  type Refusal,
} from "@/components/discovery-frame";
import { getHandoff, getRuns, preparationUnfinished, type Handoff } from "@/lib/discovery-api";
import { IncompleteChecks } from "@/components/incomplete-checks";
import { acceptCorpus } from "@/lib/screening-v1";
import { notifyReviewChanged } from "@/components/review-bus";
import { discoveryT, harvestStateWord, providerName, type DiscoveryCopyKey } from "@/lib/discovery-copy";

/**
 * 08 Hand-off (spec `docs/ux/phase1-discovery/final/08-handoff.md`): what
 * screening will receive, and the one gate of discovery: Accept this corpus
 * (`POST /screening/corpus/accept`), which freezes the corpus snapshot. The
 * accepted state is shown only from the engine's answer. Prepare stays on
 * screening Home; the hand-off sends the researcher there.
 *
 * M3i-harvest-robustness: a search is followed by three steps (duplicates,
 * abstracts, checks) and only the last makes the works this screen hands off.
 * While the corpus run's `preparation` says those steps are running, failed,
 * stopped or never ended, the screen says that and links to Harvest, where
 * "Finish preparing this corpus" is; it never says "nothing to hand off" for
 * a harvest that found records, and never offers an earlier run's works.
 */

const STAGE_KEYS = ["deduplication", "hydration", "verification"];

export function DiscoveryHandoff({ locale }: Readonly<{ locale: Locale }>) {
  const t = discoveryT(locale);
  const { origin, run: wanted, ready } = useDiscoveryParams();
  const [handoff, setHandoff] = useState<Handoff | null>(null);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [acceptError, setAcceptError] = useState<Refusal | null>(null);
  const [accepting, setAccepting] = useState(false);
  const [offline, setOffline] = useState(false);
  const [harvestRunning, setHarvestRunning] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);

  const load = useCallback(async () => {
    setRefusal(null);
    try {
      setHandoff(await getHandoff(origin));
      setOffline(false);
    } catch (error) {
      const r = refusalOf(error);
      if (r.code === "ENGINE_UNREACHABLE" || r.code === "CONSOLE_UNREACHABLE" || r.code === "CONSOLE_TIMEOUT") setOffline(true);
      setRefusal(r);
    }
    // Review follow-up: the accept route does not check a running harvest, so the screen
    // does not offer the accept while one runs (an engine guard is a follow-up).
    getRuns(origin).then(
      (runs) => setHarvestRunning(runs.active_job?.kind === "run"),
      () => setHarvestRunning(false),
    );
  }, [origin]);

  useEffect(() => {
    if (ready) void load();
  }, [ready, load]);

  const accept = async () => {
    setAccepting(true);
    setAcceptError(null);
    try {
      await acceptCorpus(origin);
      notifyReviewChanged();
      await load();
      heading.current?.focus();
    } catch (error) {
      const r = refusalOf(error);
      if (r.code === "CORPUS_ALREADY_ACCEPTED" || r.code === "NOTHING_STAGED") {
        await load();
        heading.current?.focus();
      } else {
        if (r.code === "ENGINE_UNREACHABLE" || r.code === "CONSOLE_UNREACHABLE" || r.code === "CONSOLE_TIMEOUT") setOffline(true);
        setAcceptError(r);
      }
    } finally {
      setAccepting(false);
    }
  };

  const corpus = handoff?.corpus;
  const accepted = corpus?.state === "ACCEPTED";
  // M3i: the corpus run's steps after its search have not ended, and nothing else is staged or frozen.
  const preparation = handoff?.preparation ?? null;
  const pending =
    !!corpus && !accepted && corpus.sources.length === 0 && !!preparation && (preparation.state === "running" || preparationUnfinished(preparation));
  const pendingStage = preparation?.stage
    ? STAGE_KEYS.includes(preparation.stage)
      ? t(`harvest.stage.${preparation.stage}` as DiscoveryCopyKey)
      : preparation.stage
    : null;
  const pendingRun = handoff?.run ?? "";
  const pendingBody = !preparation
    ? ""
    : preparation.state === "running"
      ? pendingStage
        ? t("handoff.pending.running", { run: pendingRun, stage: pendingStage })
        : t("handoff.pending.runningNoStage", { run: pendingRun })
      : preparation.state === "incomplete" && preparation.checks
        ? t("handoff.pending.incomplete", { run: pendingRun, unchecked: preparation.checks.unchecked, records: preparation.checks.records })
        : (preparation.state === "failed" || preparation.state === "stopped") && pendingStage
          ? t(`handoff.pending.${preparation.state}` as DiscoveryCopyKey, { run: pendingRun, stage: pendingStage })
          : t("handoff.pending.interrupted", { run: pendingRun });
  const empty = !!corpus && (corpus.state === "EMPTY" || (corpus.state === "STAGED" && !corpus.from_discovery && corpus.sources.length === 0));
  const preview = corpus?.preview ?? null;
  const fromDiscovery = !!corpus?.from_discovery;
  // Review F3: the protocol was edited after the corpus run searched it.
  const searchChanged = fromDiscovery && handoff?.search_changed === true;
  const otherChange = fromDiscovery && handoff?.protocol_changed === true && !searchChanged;
  // For a harvest the engine's preview (review F4) counts works after deduplication, before verification,
  // so it can differ from the accepted count: the headline carries no number then (H-protocol-signals
  // Deferred). The browser adds nothing up.
  // M3f: a combined corpus (harvest plus exports) is counted by the engine over both parts, so its
  // headline carries the number; a harvest alone keeps the M3c headline without one.
  const combined = corpus?.origin === "combined";
  const harvestOnly = fromDiscovery && !combined;
  const works = harvestOnly ? null : preview?.unique_studies;
  const harvestOut = !accepted && !!corpus?.harvest && !corpus.harvest.included && corpus.sources.length > 0 ? corpus.harvest : null;

  return (
    <DiscoveryFrame locale={locale} current="handoff" origin={origin} run={wanted}>
      {refusal && !handoff ? (
        <DiscoveryRefusal locale={locale} refusal={refusal} origin={origin} onRetry={() => void load()} pageHeading />
      ) : !handoff || !corpus ? (
        <Loading locale={locale} />
      ) : accepted && corpus.accepted ? (
        <div className="space-y-6">
          <header>
            <Eyebrow locale={locale} step="handoff" name={t("handoff.eyebrowName")} />
            <h1 ref={heading} tabIndex={-1} className="mt-2 font-display text-3xl text-ink" aria-live="polite">
              {t("handoff.accepted.title")}
            </h1>
          </header>
          <section aria-labelledby="accepted-card" className="rounded-lg border border-rule bg-leaf p-5" data-accepted>
            <h2 id="accepted-card" className="font-semibold text-ink">
              {t("handoff.accepted.card")}
            </h2>
            <dl className="mt-3 space-y-2 text-sm">
              <div>
                <dt className="text-ink-muted">{t("handoff.accepted.id")}</dt>
                <dd data-artifact>
                  <DataCell>{corpus.accepted.artifact_id}</DataCell>
                </dd>
              </div>
              <div>
                <dd className="text-ink">
                  <bdi>{t("handoff.accepted.at", { date: stamp(corpus.accepted.accepted_at) })}</bdi>
                </dd>
              </div>
              <div>
                <dd className="text-ink" data-accepted-counts>
                  {t("handoff.accepted.counts", { records: corpus.accepted.records, studies: corpus.accepted.studies, duplicates: corpus.accepted.duplicates })}
                </dd>
              </div>
            </dl>
            <a className={`mt-4 ${PRIMARY_LINK}`} href={screeningHomeHref(locale, origin)} data-variant="primary" data-go-screening>
              {t("handoff.accepted.go")}
            </a>
          </section>
        </div>
      ) : pending && preparation ? (
        <div className="space-y-4" data-pending={preparation.state} data-pending-stage={preparation.stage ?? ""}>
          <Eyebrow locale={locale} step="handoff" name={t("handoff.eyebrowName")} />
          <h1 ref={heading} tabIndex={-1} className="font-display text-3xl text-ink">
            {t("handoff.pending.title")}
          </h1>
          <p className="max-w-2xl text-ink" role="status" data-pending-body>
            <bdi>{pendingBody}</bdi>
          </p>
          {/* H-quota-hang: which database, when it resets, and what to do. */}
          {preparation.state === "incomplete" && preparation.checks ? (
            <div className="max-w-2xl">
              <IncompleteChecks locale={locale} checks={preparation.checks} canFinish={preparation.can_finish} />
            </div>
          ) : null}
          <p className="flex flex-wrap items-center gap-4">
            <span className="inline-flex items-center gap-1">
              <a className={PRIMARY_LINK} href={discoveryHref(locale, "harvest", origin, pendingRun)} data-variant="primary" data-pending-link>
                {preparation.state === "running" ? t("handoff.pending.follow") : preparation.can_finish ? t("handoff.pending.finish") : t("job.openHarvest")}
              </a>
              {/* M10d (03-guidance D-HO15): the reassurance is a hint on the link that names the action. */}
              {preparation.state !== "running" ? (
                <Hint locale={locale} label={t("handoff.pending.title")} text={t("handoff.pending.kept")} textKey="handoff.pending.kept" />
              ) : null}
            </span>
            <Button onClick={() => void load()} data-pending-check>
              {t("mailto.check")}
            </Button>
          </p>
        </div>
      ) : empty ? (
        <div className="space-y-4" data-empty>
          <Eyebrow locale={locale} step="handoff" name={t("handoff.eyebrowName")} />
          <h1 ref={heading} tabIndex={-1} className="font-display text-3xl text-ink">
            {t("handoff.empty.title")}
          </h1>
          <p className="text-ink-muted">{t("handoff.empty.body")}</p>
          <p className="flex flex-wrap gap-4">
            <a className={LINK} href={discoveryHref(locale, "harvest", origin)}>
              {t("steps.harvest")}
            </a>
            {!corpus.staging_refused ? (
              <a className={LINK} href={discoveryHref(locale, "import", origin)}>
                {t("handoff.import")}
              </a>
            ) : null}
          </p>
        </div>
      ) : (
        <div className="space-y-6">
          <header>
            <Eyebrow locale={locale} step="handoff" name={t("handoff.eyebrowName")} />
            <h1 ref={heading} tabIndex={-1} className="mt-2 font-display text-3xl text-ink">
              {works != null ? t("handoff.title", { n: works }) : t("handoff.titleNoCount")}
            </h1>
            <p className="mt-2 max-w-2xl text-ink-muted" data-copy="lede">
              {t("handoff.lede")}
              {/* M10d (03-guidance D-HO3): why the snapshot is frozen is a hint on the lede. */}
              <Hint locale={locale} label={t("handoff.gate.label")} text={t("handoff.lede.why")} textKey="handoff.lede.why" className="ms-1" />
            </p>
            {wanted && handoff.run && wanted !== handoff.run ? (
              <p className="mt-2 text-sm text-ink" data-run-differs>
                {t("run.describes", { run: handoff.run })}
              </p>
            ) : null}
          </header>
          {refusal ? <DiscoveryRefusal locale={locale} refusal={refusal} origin={origin} onRetry={() => void load()} /> : null}
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="min-w-0 space-y-6 lg:col-span-2">
              <section aria-labelledby="handoff-mix" className="rounded-lg border border-rule bg-leaf p-5" data-mix>
                <div className="flex items-center gap-1">
                  <h2 id="handoff-mix" className="font-semibold text-ink">
                    {t("handoff.mix.title")}
                  </h2>
                  {handoff.provider_mix.length ? (
                    <Hint locale={locale} label={t("handoff.mix.title")} text={t("handoff.mix.note")} textKey="handoff.mix.note" />
                  ) : null}
                </div>
                {handoff.provider_mix.length === 0 ? (
                  <p className="mt-2 text-ink-muted">{t("handoff.mix.none")}</p>
                ) : (
                  <>
                    <ul className="mt-3 space-y-2 text-sm">
                      {handoff.provider_mix.map((m) => (
                        <li key={`${m.kind ?? "search"}:${m.provider}`} data-mix-row={m.provider} data-mix-kind={m.kind ?? "search"}>
                          <div className="flex flex-wrap justify-between gap-2">
                            <span className="text-ink">
                              {providerName(m.provider)}{" "}
                              {m.kind ? (
                                <span className="text-xs text-ink-muted" data-mix-kind-word>
                                  ({t(m.kind === "import" ? "handoff.mix.kind.import" : "handoff.mix.kind.search")})
                                </span>
                              ) : null}
                            </span>
                            <bdi className="text-ink-muted">
                              {t("handoff.mix.row", { records: m.records, share: percent(m.share) })}
                            </bdi>
                          </div>
                          <div aria-hidden="true" className="mt-1 h-2 rounded-sm bg-paper">
                            <div className="h-2 rounded-sm bg-brand" style={{ width: `${Math.min(100, m.share * 100)}%` }} />
                          </div>
                        </li>
                      ))}
                    </ul>
                  </>
                )}
              </section>
              <section aria-labelledby="handoff-receive" className="rounded-lg border border-rule bg-leaf p-5" data-receive>
                <h2 id="handoff-receive" className="font-semibold text-ink">
                  {t("handoff.receive.title")}
                </h2>
                {!harvestOnly && !preview ? <p className="mt-2 text-ink-muted">{t("handoff.receive.noPreview")}</p> : null}
                <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
                  {!harvestOnly && preview ? (
                    <>
                      <div>
                        <dt className="text-ink-muted">{t("handoff.receive.identified")}</dt>
                        <dd className="text-ink">{preview.identified}</dd>
                      </div>
                      <div>
                        <dt className="text-ink-muted">{t("handoff.receive.duplicates")}</dt>
                        <dd className="text-ink">{preview.duplicates}</dd>
                      </div>
                      <div>
                        <dt className="text-ink-muted">{t("handoff.receive.works")}</dt>
                        <dd className="text-ink">{preview.unique_studies}</dd>
                      </div>
                    </>
                  ) : null}
                  <div>
                    <dt className="text-ink-muted">{t("handoff.receive.withAbstract")}</dt>
                    <dd className="text-ink" data-with-abstract>
                      {handoff.abstracts.with_abstract} <bdi dir="ltr" className="text-ink-muted">({percent(handoff.abstracts.share_with_abstract)})</bdi>
                    </dd>
                  </div>
                  <div>
                    <dt className="text-ink-muted">{t("handoff.receive.titleOnly")}</dt>
                    <dd className="text-ink" data-title-only>
                      {handoff.abstracts.title_only}{" "}
                      {handoff.abstracts.title_only > 0 ? <DecisionBadge role="unclear">{t("handoff.receive.hard")}</DecisionBadge> : null}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-ink-muted">{t("handoff.receive.window")}</dt>
                    <dd className="text-ink" data-window>
                      {handoff.outside_year_window}
                    </dd>
                  </div>
                  <div>
                    <dt className="text-ink-muted">{t("handoff.receive.lowerBound")}</dt>
                    <dd className="text-ink" data-lower-bound-dbs>
                      {handoff.lower_bound_databases.length ? handoff.lower_bound_databases.map(providerName).join(", ") : t("handoff.receive.none")}
                    </dd>
                  </div>
                </dl>
                {handoff.lower_bound_databases.length ? (
                  <p className="mt-3 rounded-md border border-rule bg-paper p-3 text-sm text-ink" data-lower-bound-note>
                    {t("handoff.receive.lowerBoundNote", { names: handoff.lower_bound_databases.map(providerName).join(", ") })}{" "}
                    <a className={LINK} href={discoveryHref(locale, "report", origin)}>
                      {t("handoff.report")}
                    </a>
                  </p>
                ) : null}
                {(handoff.imports_unchecked ?? 0) > 0 ? (
                  <p className="mt-3 text-sm text-ink-muted" data-imports-unchecked>
                    {t("handoff.imports.unchecked", { n: handoff.imports_unchecked ?? 0 })}
                  </p>
                ) : null}
              </section>
            </div>
            <aside className="space-y-4">
            <EarlierChecksLine locale={locale} origin={origin} />
            <DiscoveryChecksPanel locale={locale} step="handoff" origin={origin} />
              <section aria-labelledby="handoff-from" className="rounded-lg border border-rule bg-leaf p-5 text-sm">
                <h2 id="handoff-from" className="font-semibold text-ink">
                  {t("handoff.from.title")}
                </h2>
                {handoff.run ? <p className="mt-2 text-ink">{t("handoff.from.run", { run: handoff.run })}</p> : null}
                {!harvestOnly && corpus.sources.length ? (
                  <p className="mt-2 text-ink">
                    {t("handoff.from.sources")}: {corpus.sources.map((s) => s.label).join(", ")}
                  </p>
                ) : null}
                <p className="mt-2 text-ink-muted">{t("handoff.from.protocol")}</p>
                <p>
                  <DataCell>{handoff.protocol_fingerprint}</DataCell>
                </p>
                {corpus.staging_refused && corpus.staging_refused.code !== "CORPUS_ALREADY_ACCEPTED" ? (
                  <p className="mt-3 text-xs text-ink-muted" data-staging-refused={corpus.staging_refused.code}>
                    <bdi dir="ltr">{corpus.staging_refused.message}</bdi>
                  </p>
                ) : null}
                <p className="mt-3">
                  <a className={LINK} href={discoveryHref(locale, "report", origin)}>
                    {t("handoff.report")}
                  </a>
                </p>
                {/* M3f: a harvest can follow exports, so "Search again" is offered with exports staged too. */}
                {fromDiscovery || corpus.sources.length ? (
                  <p>
                    <a className={LINK} href={discoveryHref(locale, "harvest", origin)} data-search-again>
                      {t("handoff.again")}
                    </a>
                  </p>
                ) : null}
                {!corpus.staging_refused ? (
                  <p>
                    <a className={LINK} href={discoveryHref(locale, "import", origin)}>
                      {t("handoff.import")}
                    </a>
                  </p>
                ) : null}
              </section>
              {/* Review F3: say it before the click. A search change is refused by the accept. */}
              {searchChanged && !acceptError ? (
                <div data-protocol-changed="search">
                  <DiscoveryRefusal locale={locale} refusal={{ code: "PROTOCOL_CHANGED_SINCE_RUN", message: "" }} origin={origin} />
                </div>
              ) : null}
              {harvestOut ? (
                <section role="status" className="rounded-md border border-rule bg-paper p-3 text-sm text-ink" data-harvest-out={harvestOut.state}>
                  <DecisionBadge role="unclear">{harvestStateWord(locale, harvestOut.state)}</DecisionBadge>{" "}
                  <bdi>{t("handoff.harvestOut.note", { run: harvestOut.run, state: harvestStateWord(locale, harvestOut.state) })}</bdi>{" "}
                  <a className={LINK} href={discoveryHref(locale, "harvest", origin, harvestOut.run)} data-harvest-out-open>
                    {t("handoff.harvestOut.open")}
                  </a>
                </section>
              ) : null}
              {acceptError ? (
                <div className="space-y-2">
                  <DiscoveryRefusal locale={locale} refusal={acceptError} origin={origin} onRetry={() => void accept()} />
                  {acceptError.code === "PROTOCOL_CHANGED_SINCE_RUN" && acceptError.message ? (
                    <p className="text-sm text-ink-muted" data-accept-message>
                      <bdi dir="ltr">{acceptError.message}</bdi>
                    </p>
                  ) : null}
                </div>
              ) : null}
              <GatePanel
                label={t("handoff.gate.label")}
                actions={
                  <Button variant="primary" onClick={() => void accept()} disabled={accepting || offline || harvestRunning || searchChanged || acceptError?.code === "PROTOCOL_CHANGED_SINCE_RUN"} aria-describedby={offline ? "handoff-offline" : harvestRunning ? "handoff-running" : undefined} data-accept>
                    {accepting ? t("handoff.gate.accepting") : t("handoff.gate.accept")}
                  </Button>
                }
              >
                <p>{t("handoff.gate.body")}</p>
                {otherChange ? (
                  <p className="mt-2 text-sm text-ink" data-protocol-changed="other">
                    {t("handoff.gate.protocolChanged")}
                  </p>
                ) : null}
                {offline ? (
                  <p id="handoff-offline" className="mt-2 text-sm text-ink-muted">
                    {t("handoff.gate.offline")}
                  </p>
                ) : null}
                {harvestRunning ? (
                  <p id="handoff-running" className="mt-2 text-sm text-ink" data-harvest-running>
                    {t("handoff.gate.running")}
                  </p>
                ) : null}
              </GatePanel>
            </aside>
          </div>
        </div>
      )}
    </DiscoveryFrame>
  );
}
