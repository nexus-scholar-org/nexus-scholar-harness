"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge, GatePanel } from "@/components/ui/base";
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
import { getHandoff, type Handoff } from "@/lib/discovery-api";
import { acceptCorpus } from "@/lib/screening-v1";
import { discoveryT, providerName } from "@/lib/discovery-copy";

/**
 * 08 Hand-off (spec `docs/ux/phase1-discovery/final/08-handoff.md`): what
 * screening will receive, and the one gate of discovery: Accept this corpus
 * (`POST /screening/corpus/accept`), which freezes the corpus snapshot. The
 * accepted state is shown only from the engine's answer. Prepare stays on
 * screening Home; the hand-off sends the researcher there.
 */

export function DiscoveryHandoff({ locale }: Readonly<{ locale: Locale }>) {
  const t = discoveryT(locale);
  const { origin, run: wanted, ready } = useDiscoveryParams();
  const [handoff, setHandoff] = useState<Handoff | null>(null);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [acceptError, setAcceptError] = useState<Refusal | null>(null);
  const [accepting, setAccepting] = useState(false);
  const [offline, setOffline] = useState(false);
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
  }, [origin]);

  useEffect(() => {
    if (ready) void load();
  }, [ready, load]);

  const accept = async () => {
    setAccepting(true);
    setAcceptError(null);
    try {
      await acceptCorpus(origin);
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
  const empty = !!corpus && (corpus.state === "EMPTY" || (corpus.state === "STAGED" && !corpus.from_discovery && corpus.sources.length === 0));
  const preview = corpus?.preview ?? null;
  const fromDiscovery = !!corpus?.from_discovery;
  // The engine's corpus preview counts staged exports only; for a harvest it writes no works count, so the
  // headline carries no number then (route gap, M3c-screens Deferred). The browser adds nothing up.
  const works = fromDiscovery ? null : preview?.unique_studies;

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
                  <bdi dir="ltr">{t("handoff.accepted.at", { date: stamp(corpus.accepted.accepted_at) })}</bdi>
                </dd>
              </div>
              <div>
                <dd className="text-ink" data-accepted-counts>
                  {t("handoff.accepted.counts", { records: corpus.accepted.records, studies: corpus.accepted.studies, duplicates: corpus.accepted.duplicates })}
                </dd>
              </div>
            </dl>
            <a className="mt-4 inline-flex min-h-11 items-center rounded-md bg-brand px-4 font-medium text-on-brand" href={screeningHomeHref(locale, origin)} data-go-screening>
              {t("handoff.accepted.go")}
            </a>
          </section>
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
            <p className="mt-2 max-w-2xl text-ink-muted">{t("handoff.lede")}</p>
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
                <h2 id="handoff-mix" className="font-semibold text-ink">
                  {t("handoff.mix.title")}
                </h2>
                {handoff.provider_mix.length === 0 ? (
                  <p className="mt-2 text-ink-muted">{t("handoff.mix.none")}</p>
                ) : (
                  <>
                    <ul className="mt-3 space-y-2 text-sm">
                      {handoff.provider_mix.map((m) => (
                        <li key={m.provider} data-mix-row={m.provider}>
                          <div className="flex flex-wrap justify-between gap-2">
                            <span className="text-ink">{providerName(m.provider)}</span>
                            <bdi dir="ltr" className="text-ink-muted">
                              {t("handoff.mix.row", { records: m.records, share: percent(m.share) })}
                            </bdi>
                          </div>
                          <div aria-hidden="true" className="mt-1 h-2 rounded-sm bg-paper">
                            <div className="h-2 rounded-sm bg-brand" style={{ width: `${Math.min(100, m.share * 100)}%` }} />
                          </div>
                        </li>
                      ))}
                    </ul>
                    <p className="mt-3 text-xs text-ink-muted">{t("handoff.mix.note")}</p>
                  </>
                )}
              </section>
              <section aria-labelledby="handoff-receive" className="rounded-lg border border-rule bg-leaf p-5" data-receive>
                <h2 id="handoff-receive" className="font-semibold text-ink">
                  {t("handoff.receive.title")}
                </h2>
                {!fromDiscovery && !preview ? <p className="mt-2 text-ink-muted">{t("handoff.receive.noPreview")}</p> : null}
                <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-2">
                  {!fromDiscovery && preview ? (
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
                <p className="mt-2 text-xs text-ink-muted">
                  {t("handoff.failedNote")}{" "}
                  <a className={LINK} href={discoveryHref(locale, "report", origin)}>
                    {t("handoff.report")}
                  </a>
                </p>
              </section>
            </div>
            <aside className="space-y-4">
              <section aria-labelledby="handoff-from" className="rounded-lg border border-rule bg-leaf p-5 text-sm">
                <h2 id="handoff-from" className="font-semibold text-ink">
                  {t("handoff.from.title")}
                </h2>
                {handoff.run ? <p className="mt-2 text-ink">{t("handoff.from.run", { run: handoff.run })}</p> : null}
                {!fromDiscovery && corpus.sources.length ? (
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
                {fromDiscovery ? (
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
                  <Button variant="primary" onClick={() => void accept()} disabled={accepting || offline} aria-describedby={offline ? "handoff-offline" : undefined} data-accept>
                    {accepting ? t("handoff.gate.accepting") : t("handoff.gate.accept")}
                  </Button>
                }
              >
                <p>{t("handoff.gate.body")}</p>
                {offline ? (
                  <p id="handoff-offline" className="mt-2 text-sm text-ink-muted">
                    {t("handoff.gate.offline")}
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
