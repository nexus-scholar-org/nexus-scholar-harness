"use client";

import { useEffect, useState } from "react";

import type { Locale } from "@/i18n";
import { DecisionBadge, Hint } from "@/components/ui/base";
import { DiscoveryFrame, DiscoveryRefusal, LINK, Loading, discoveryHref, refusalOf, useDiscoveryParams, type DiscoveryStep, type Refusal, type StepMarks } from "@/components/discovery-frame";
import { getDedup, getPlan, getRecall, getReport, getRuns, preparationUnfinished, type Dedup, type Plan, type RecallCheck, type Report, type Runs } from "@/lib/discovery-api";
import { getCorpus, type Corpus } from "@/lib/screening-v1";
import { discoveryT, type DiscoveryCopyKey } from "@/lib/discovery-copy";

/**
 * The discovery entry (spec 01 "The entry", researcher's answer 1 of
 * 2026-11-10): where the search stands, one line per step, each read from a
 * route. A failed read leaves that line without a mark; nothing is locked.
 */

interface Reads {
  plan: Plan | null;
  recall: RecallCheck | null;
  runs: Runs | null;
  corpus: Corpus | null;
  dedup: Dedup | null;
  report: Report | null;
}

const settle = <T,>(p: Promise<T>): Promise<T | null> => p.then((v) => v, () => null);

export function DiscoveryOverview({ locale }: Readonly<{ locale: Locale }>) {
  const t = discoveryT(locale);
  const { origin, ready } = useDiscoveryParams();
  const [reads, setReads] = useState<Reads | null>(null);
  const [refusal, setRefusal] = useState<Refusal | null>(null);

  useEffect(() => {
    if (!ready) return;
    let live = true;
    (async () => {
      try {
        const plan = await getPlan(origin);
        const [recall, runs, corpus, dedup, report] = await Promise.all([
          settle(getRecall(origin)),
          settle(getRuns(origin)),
          settle(getCorpus(origin)),
          settle(getDedup(origin)),
          settle(getReport(origin)),
        ]);
        if (live) setReads({ plan, recall, runs, corpus, dedup, report });
      } catch (error) {
        if (live) setRefusal(refusalOf(error));
      }
    })();
    return () => {
      live = false;
    };
  }, [ready, origin]);

  if (refusal) {
    return (
      <DiscoveryFrame locale={locale} origin={origin}>
        <DiscoveryRefusal locale={locale} refusal={refusal} origin={origin} onRetry={() => window.location.reload()} pageHeading />
      </DiscoveryFrame>
    );
  }
  if (!reads) {
    return (
      <DiscoveryFrame locale={locale} origin={origin}>
        <Loading locale={locale} />
      </DiscoveryFrame>
    );
  }

  const { plan, recall, runs, corpus, dedup, report } = reads;
  // M3i: a search or a "finish preparing" job is running; the steps after a search did not end.
  const harvestRunning = runs?.active_job?.kind === "run" || runs?.active_job?.kind === "prepare";
  const harvestUnfinished = corpus?.state !== "ACCEPTED" && !!runs?.runs.some((r) => preparationUnfinished(r.preparation));
  const marks: StepMarks = {
    recall: recall ? (recall.protocol_fingerprint === plan?.protocol_fingerprint ? "done" : "earlier") : "none",
    harvest: runs?.runs.length && !harvestUnfinished ? "done" : "none",
    import: corpus && corpus.sources.length > 0 && !corpus.from_discovery ? "done" : "none",
    dedup: dedup ? "done" : "none",
    report: report?.methods_text.reviewed ? "done" : "none",
    handoff: corpus?.state === "ACCEPTED" ? "done" : "none",
  };
  const lines: { step: DiscoveryStep; key: DiscoveryCopyKey; values?: Record<string, string | number> }[] = [
    { step: "plan", key: "overview.plan.line" },
    { step: "recall", key: marks.recall === "done" ? "overview.recall.done" : marks.recall === "earlier" ? "overview.recall.earlier" : "overview.recall.none" },
    {
      step: "harvest",
      key: harvestRunning
        ? "overview.harvest.running"
        : harvestUnfinished
          ? "overview.harvest.unfinished"
          : marks.harvest === "done"
            ? "overview.harvest.done"
            : "overview.harvest.none",
    },
    { step: "import", key: marks.import === "done" ? "overview.import.done" : "overview.import.none" },
    { step: "dedup", key: marks.dedup === "done" ? "overview.dedup.done" : "overview.dedup.none", values: { run: dedup?.run ?? "" } },
    { step: "report", key: marks.report === "done" ? "overview.report.done" : "overview.report.none", values: { run: report?.run ?? "" } },
    { step: "handoff", key: marks.handoff === "done" ? "overview.handoff.done" : "overview.handoff.none" },
  ];
  const order: DiscoveryStep[] = ["recall", "harvest", "dedup", "report", "handoff"];
  const next = harvestRunning || harvestUnfinished ? "harvest" : order.find((s) => marks[s] !== "done") ?? "handoff";
  const stepKey = (s: DiscoveryStep) => `steps.${s}` as DiscoveryCopyKey;

  return (
    <DiscoveryFrame locale={locale} origin={origin} marks={marks}>
      {/* M10d (03-guidance D-DS10 to D-DS12): the title alone; that every step stays open is a hint. */}
      <header className="flex items-center gap-1">
        <h1 className="font-display text-3xl text-ink">{t("overview.title")}</h1>
        <Hint locale={locale} label={t("overview.title")} text={t("overview.lede")} textKey="overview.lede" />
      </header>
      <ol className="mt-6 space-y-3">
        {lines.map((line) => {
          const mark = marks[line.step];
          return (
            <li key={line.step} className="flex flex-wrap items-center gap-3 rounded-lg border border-rule bg-leaf p-4" data-line={line.step} data-mark={mark ?? "none"}>
              <a className={`${LINK} font-medium`} href={discoveryHref(locale, line.step, origin)}>
                {t(stepKey(line.step))}
              </a>
              {mark === "done" ? (
                <DecisionBadge role="include">{t("steps.done")}</DecisionBadge>
              ) : mark === "earlier" ? (
                <DecisionBadge role="unclear">{t("steps.earlierProtocol")}</DecisionBadge>
              ) : line.step !== "plan" ? (
                <DecisionBadge role="exclude">{t("steps.notYet")}</DecisionBadge>
              ) : null}
              {/* M10d (03-guidance D-DS14): the plan line is background, a hint on the Plan link. */}
              {line.key === "overview.plan.line" ? (
                <Hint locale={locale} label={t(stepKey(line.step))} text={t(line.key)} textKey={line.key} />
              ) : (
                <span className="text-ink">{t(line.key, line.values)}</span>
              )}
            </li>
          );
        })}
      </ol>
      <p className="mt-6">
        <a className="inline-flex min-h-11 items-center rounded-md bg-brand px-4 font-medium text-on-brand" href={discoveryHref(locale, next, origin)} data-variant="primary" data-continue>
          {t("overview.continue", { step: t(stepKey(next)) })}
        </a>
      </p>
    </DiscoveryFrame>
  );
}
