"use client";

import { useCallback, useEffect, useState } from "react";

import type { Locale } from "@/i18n";
import { DataCell, DecisionBadge } from "@/components/ui/base";
import { DETAILS_LABEL } from "@/components/screening-state-card";
import { DiscoveryFrame, DiscoveryRefusal, Eyebrow, LINK, Loading, discoveryHref, percent, refusalOf, useDiscoveryParams, type Refusal } from "@/components/discovery-frame";
import { getDedup, type Dedup } from "@/lib/discovery-api";
import { discoveryT } from "@/lib/discovery-copy";

/**
 * 05 Duplicates (spec `docs/ux/phase1-discovery/final/05-dedup.md`): Stage 1,
 * counts per rule only (`GET /discovery/dedup`). The near-twin pair review is
 * M3e (RELEASE lane, decision 2): no merge or keep control, no decision is
 * recorded here. The screen describes the newest deduplication and says which run.
 */

export function DiscoveryDedup({ locale }: Readonly<{ locale: Locale }>) {
  const t = discoveryT(locale);
  const { origin, run: wanted, ready } = useDiscoveryParams();
  const [dedup, setDedup] = useState<Dedup | null>(null);
  const [refusal, setRefusal] = useState<Refusal | null>(null);

  const load = useCallback(async () => {
    setRefusal(null);
    try {
      setDedup(await getDedup(origin));
    } catch (error) {
      setRefusal(refusalOf(error));
    }
  }, [origin]);

  useEffect(() => {
    if (ready) void load();
  }, [ready, load]);

  return (
    <DiscoveryFrame locale={locale} current="dedup" origin={origin} run={wanted}>
      {refusal && !dedup ? (
        <div className="space-y-3">
          <DiscoveryRefusal locale={locale} refusal={refusal} origin={origin} onRetry={() => void load()} pageHeading />
          {refusal.code === "DEDUP_NOT_RUN" ? (
            <p className="text-sm text-ink-muted" data-import-note>
              {t("dedup.importNote")}{" "}
              <a className={LINK} href={discoveryHref(locale, "handoff", origin)}>
                {t("steps.handoff")}
              </a>
            </p>
          ) : null}
        </div>
      ) : !dedup ? (
        <Loading locale={locale} />
      ) : (
        <div className="space-y-6">
          <header>
            <Eyebrow locale={locale} step="dedup" name={t("dedup.eyebrowName")} />
            <h1 className="mt-2 font-display text-3xl text-ink">
              <bdi>{t("dedup.title", { input: dedup.input_records, unique: dedup.unique_works })}</bdi>
            </h1>
            <p className="mt-2 max-w-2xl text-ink-muted">{t("dedup.lede")}</p>
            <p className="mt-2 text-sm text-ink-muted" data-dedup-run>
              {t("dedup.run", { run: dedup.run ?? "" })}
            </p>
            {wanted && dedup.run && wanted !== dedup.run ? (
              <p className="mt-1 text-sm text-ink" data-run-mismatch>
                {t("dedup.runMismatch", { selected: wanted, run: dedup.run })}
              </p>
            ) : null}
          </header>
          {refusal ? <DiscoveryRefusal locale={locale} refusal={refusal} origin={origin} onRetry={() => void load()} /> : null}
          <section aria-labelledby="dedup-counts" className="rounded-lg border border-rule bg-leaf p-5">
            <h2 id="dedup-counts" className="font-semibold text-ink">
              {t("dedup.counts")}
            </h2>
            <dl className="mt-3 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <div>
                <dt className="text-sm text-ink-muted">{t("dedup.in")}</dt>
                <dd className="font-display text-2xl text-ink" data-in>
                  {dedup.input_records}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-ink-muted">{t("dedup.out")}</dt>
                <dd className="font-display text-2xl text-ink" data-out>
                  {dedup.unique_works}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-ink-muted">{t("dedup.removed")}</dt>
                <dd className="font-display text-2xl text-ink" data-removed>
                  {dedup.removed}
                </dd>
              </div>
              <div>
                <dt className="text-sm text-ink-muted">{t("dedup.rate")}</dt>
                <dd className="font-display text-2xl text-ink" data-rate>
                  <bdi dir="ltr">{percent(dedup.removed_rate)}</bdi>
                </dd>
                <dd>
                  <details className="text-xs">
                    <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-ink-muted">{DETAILS_LABEL[locale]}</summary>
                    <p className="text-ink-muted" data-rate-written>
                      {t("dedup.rateWritten", { fraction: "" })}
                      <DataCell>{String(dedup.removed_rate)}</DataCell>
                    </p>
                  </details>
                </dd>
              </div>
            </dl>
            <h3 className="mt-5 text-sm font-semibold text-ink">{t("dedup.tiers")}</h3>
            <dl className="mt-2 space-y-1 text-sm">
              {(
                [
                  ["identifier", "dedup.tier.identifier"],
                  ["exact_title", "dedup.tier.exactTitle"],
                  ["fuzzy_title", "dedup.tier.fuzzyTitle"],
                ] as const
              ).map(([tier, key]) => (
                <div key={tier} className="flex flex-wrap gap-x-3" data-tier={tier}>
                  <dt className="text-ink-muted">{t(key)}</dt>
                  <dd className="text-ink">{dedup.tiers ? dedup.tiers[tier] : <DecisionBadge role="exclude">{t("dedup.tier.notRecorded")}</DecisionBadge>}</dd>
                </div>
              ))}
            </dl>
          </section>
          {dedup.method ? (
            <section aria-labelledby="dedup-rules" className="rounded-lg border border-rule bg-leaf p-5 text-sm">
              <h2 id="dedup-rules" className="font-semibold text-ink">
                {t("dedup.rules.title")}
              </h2>
              <ul className="mt-2 space-y-1 text-ink">
                <li>{t("dedup.rules.similarity", { value: dedup.method.title_similarity })}</li>
                <li>{t("dedup.rules.years", { value: dedup.method.year_tolerance })}</li>
                <li>{t("dedup.rules.author", { yesNo: dedup.method.first_author ? t("dedup.yes") : t("dedup.no") })}</li>
              </ul>
              <p className="mt-2 text-ink-muted" data-method-source={dedup.method.source}>
                {dedup.method.source === "protocol" ? t("dedup.rules.sourceProtocol") : t("dedup.rules.sourceDefault")}
              </p>
            </section>
          ) : null}
          <p className="text-ink" data-pairs-note>
            {t("dedup.pairsNote")}
          </p>
          <p className="flex flex-wrap gap-4">
            <a className={LINK} href={discoveryHref(locale, "harvest", origin)}>
              {t("dedup.back")}
            </a>
            <a className={LINK} href={discoveryHref(locale, "report", origin, wanted)} data-next>
              {t("dedup.next")}
            </a>
          </p>
        </div>
      )}
    </DiscoveryFrame>
  );
}
