"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import type { Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge, type DecisionRole } from "@/components/ui/base";
import {
  DiscoveryFrame,
  DiscoveryRefusal,
  Eyebrow,
  LINK,
  Loading,
  MailtoCard,
  OpenAlexKeyCard,
  discoveryHref,
  refusalOf,
  type Refusal,
} from "@/components/discovery-frame";
import { getPlan, getRuns, type Plan } from "@/lib/discovery-api";
import { discoveryT, providerName, type DiscoveryCopyKey } from "@/lib/discovery-copy";

/**
 * 01 Plan (spec `docs/ux/phase1-discovery/final/01-plan.md`): what each
 * database will receive, from `GET /discovery/plan` (the engine's dry run). The
 * screen writes nothing: there is no approve action, starting a harvest is the
 * record. The cap shown is the protocol's only; a run override lives on Harvest.
 */

const STATUS_ROLE: Record<string, DecisionRole> = { translated: "include", selected: "unclear", not_selected: "exclude", off_by_default: "exclude" };

export function DiscoveryPlan({ locale }: Readonly<{ locale: Locale }>) {
  const t = discoveryT(locale);
  const [origin, setOrigin] = useState("");
  const [ready, setReady] = useState(false);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [hasRun, setHasRun] = useState(false);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [changed, setChanged] = useState(false);
  const [copied, setCopied] = useState(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const fingerprint = useRef<string | null>(null);

  useEffect(() => {
    setOrigin(new URLSearchParams(window.location.search).get("console") ?? "");
    setReady(true);
  }, []);

  const load = useCallback(
    async (focus = false) => {
      setRefusal(null);
      try {
        const next = await getPlan(origin);
        if (fingerprint.current && fingerprint.current !== next.protocol_fingerprint) setChanged(true);
        fingerprint.current = next.protocol_fingerprint;
        setPlan(next);
        if (focus) heading.current?.focus();
      } catch (error) {
        setRefusal(refusalOf(error));
      }
    },
    [origin],
  );

  useEffect(() => {
    if (!ready) return;
    void load();
    // Read once on load: "Check again" re-reads the plan and nothing else (spec 01 acceptance).
    getRuns(origin).then(
      (runs) => setHasRun(runs.runs.length > 0),
      () => undefined,
    );
  }, [ready, load, origin]);

  const copyAll = async () => {
    if (!plan) return;
    const text = plan.providers
      .filter((p) => p.executed_query)
      .map((p) => `${providerName(p.name)}: ${p.executed_query}`)
      .join("\n");
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
    } catch {
      setCopied(false);
    }
  };

  return (
    <DiscoveryFrame locale={locale} current="plan" origin={origin}>
      {refusal && !plan ? (
        <DiscoveryRefusal locale={locale} refusal={refusal} origin={origin} onRetry={() => void load()} pageHeading />
      ) : !plan ? (
        <Loading locale={locale} />
      ) : (
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="space-y-6 min-w-0 lg:col-span-2">
            <header>
              <Eyebrow locale={locale} step="plan" name={t("plan.eyebrowName")} />
              <h1 ref={heading} tabIndex={-1} className="mt-2 font-display text-3xl text-ink">
                {t("plan.title")}
              </h1>
              <p className="mt-2 max-w-2xl text-ink-muted">{t("plan.lede")}</p>
            </header>
            {refusal ? <DiscoveryRefusal locale={locale} refusal={refusal} origin={origin} onRetry={() => void load()} /> : null}
            {changed ? (
              <p role="status" className="rounded-lg border border-rule bg-leaf p-3 text-ink" data-plan-changed>
                {t("plan.changed")}
              </p>
            ) : null}
            <section aria-labelledby="plan-strings" className="rounded-lg border border-rule bg-leaf p-5">
              <h2 id="plan-strings" className="font-semibold text-ink">
                {t("plan.strings.title")}
              </h2>
              <p className="mt-1 text-xs text-ink-muted">
                {t("plan.fingerprint")} <DataCell>{plan.protocol_fingerprint}</DataCell>
              </p>
              {plan.providers.every((p) => !p.selected) ? <p className="mt-3 text-ink">{t("plan.noneSelected")}</p> : null}
              <div className="mt-4 space-y-4">
                {plan.providers.map((p) => {
                  const statusKey = `plan.status.${p.status}` as DiscoveryCopyKey;
                  const known = p.status in STATUS_ROLE;
                  return (
                    <section key={p.name} aria-label={providerName(p.name)} className="border-t border-rule pt-4" data-provider={p.name} data-status={p.status}>
                      <div className="flex flex-wrap items-center gap-2">
                        <h3 className="font-semibold text-ink">{providerName(p.name)}</h3>
                        <DecisionBadge role={STATUS_ROLE[p.status] ?? "exclude"}>{known ? t(statusKey) : p.status}</DecisionBadge>
                      </div>
                      {p.executed_query ? (
                        <div className="mt-2 rounded-md border border-rule bg-paper p-3">
                          <p className="text-xs text-ink-muted">{t("plan.string.badge")}</p>
                          <p className="mt-1" data-executed>
                            <DataCell>{p.executed_query}</DataCell>
                          </p>
                        </div>
                      ) : p.selected ? (
                        <p className="mt-2 text-sm text-ink">{t("plan.noPreview")}</p>
                      ) : (
                        <p className="mt-2 text-sm text-ink-muted">{p.notes.length ? null : t("plan.notSearched")}</p>
                      )}
                      {p.request ? (
                        <details className="mt-2 text-sm">
                          <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-ink-muted">{t("plan.request.show")}</summary>
                          <pre className="overflow-x-auto rounded-sm bg-paper p-2 font-mono text-[0.8125rem] text-ink" dir="ltr">
                            {JSON.stringify(p.request, null, 2)}
                          </pre>
                        </details>
                      ) : null}
                      {p.selected ? (
                        p.cannot_express.length || p.notes.length ? (
                          <ul className="mt-2 space-y-1 text-sm text-ink-muted">
                            {p.cannot_express.length ? (
                              <li>
                                {t("plan.cannotExpress", { list: "" })}
                                <bdi dir="ltr">{p.cannot_express.join(", ")}</bdi>
                              </li>
                            ) : null}
                            {p.notes.map((note) => (
                              <li key={note}>
                                <bdi dir="ltr">{note}</bdi>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <p className="mt-2 text-sm text-ink-muted">{t("plan.nothingDropped")}</p>
                        )
                      ) : p.notes.length ? (
                        <ul className="mt-2 space-y-1 text-sm text-ink-muted">
                          {p.notes.map((note) => (
                            <li key={note}>
                              <bdi dir="ltr">{note}</bdi>
                            </li>
                          ))}
                        </ul>
                      ) : null}
                    </section>
                  );
                })}
              </div>
              <div className="mt-4 flex flex-wrap items-center gap-3 border-t border-rule pt-4">
                <Button onClick={() => void copyAll()} data-copy-all>
                  {t("plan.copyAll")}
                </Button>
                <span aria-live="polite" className="text-sm text-ink-muted">
                  {copied ? t("copied") : ""}
                </span>
              </div>
              <p className="mt-3 text-sm text-ink-muted">
                {t("plan.imports.hint")}{" "}
                {hasRun ? (
                  <span data-imports-after-run>{t("plan.imports.afterRun")}</span>
                ) : (
                  <a className={LINK} href={discoveryHref(locale, "import", origin)}>
                    {t("steps.import")}
                  </a>
                )}
              </p>
            </section>
          </div>
          <aside className="space-y-4">
            <section aria-labelledby="plan-limits" className="rounded-lg border border-rule bg-leaf p-5">
              <h2 id="plan-limits" className="font-semibold text-ink">
                {t("plan.limits.title")}
              </h2>
              <dl className="mt-3 space-y-3 text-sm">
                <div>
                  <dt className="text-ink-muted">{t("plan.limits.window")}</dt>
                  <dd className="text-ink">
                    {plan.query.year_min == null && plan.query.year_max == null ? (
                      t("plan.limits.noLimit")
                    ) : (
                      <bdi dir="ltr">
                        {plan.query.year_min ?? "…"}–{plan.query.year_max ?? "…"}
                      </bdi>
                    )}
                  </dd>
                </div>
                <div>
                  <dt className="text-ink-muted">{t("plan.limits.language")}</dt>
                  <dd className="text-ink">{plan.query.language ? <bdi dir="ltr">{plan.query.language}</bdi> : t("plan.limits.noLimit")}</dd>
                </div>
                <div data-cap={plan.cap.source}>
                  <dt className="text-ink-muted">{t("plan.limits.cap")}</dt>
                  <dd className="text-ink">
                    <bdi dir="ltr">{plan.cap.value}</bdi>
                  </dd>
                  <dd className="mt-1 text-xs text-ink-muted">
                    {plan.cap.source === "protocol" ? t("plan.limits.cap.protocol") : t("plan.limits.cap.engine_ceiling", { ceiling: plan.cap.ceiling })}
                  </dd>
                </div>
                <div>
                  <dt className="text-ink-muted">{t("mailto.title")}</dt>
                  <dd className="text-ink">
                    {plan.mailto_set ? (
                      <DecisionBadge role="include">{t("plan.limits.mailto.set")}</DecisionBadge>
                    ) : (
                      <DecisionBadge role="unclear">{t("plan.limits.mailto.notSet")}</DecisionBadge>
                    )}
                  </dd>
                  <dd className="mt-1 text-xs text-ink-muted">{t("plan.limits.mailto.help")}</dd>
                </div>
                {plan.openalex_key_set === undefined ? null : (
                  <div data-openalex-key-set={plan.openalex_key_set ? "true" : "false"}>
                    <dt className="text-ink-muted">{t("openalexKey.title")}</dt>
                    <dd className="text-ink">
                      {plan.openalex_key_set ? (
                        <DecisionBadge role="include">{t("plan.limits.mailto.set")}</DecisionBadge>
                      ) : (
                        <DecisionBadge role="unclear">{t("plan.limits.mailto.notSet")}</DecisionBadge>
                      )}
                    </dd>
                    <dd className="mt-1 text-xs text-ink-muted">{t("plan.limits.openalexKey.help")}</dd>
                  </div>
                )}
              </dl>
            </section>
            {!plan.mailto_set ? <MailtoCard locale={locale} onCheck={() => void load(true)} /> : null}
            {plan.openalex_key_set === false && plan.providers.some((p) => p.name === "openalex" && p.selected) ? (
              <OpenAlexKeyCard locale={locale} onCheck={() => void load(true)} />
            ) : null}
            <section className="rounded-lg border border-rule bg-leaf p-5">
              <p className="text-sm text-ink-muted">{t("amend.help")}</p>
              <a className={LINK} href={`/${locale}/inception/${origin ? `?console=${encodeURIComponent(origin)}` : ""}`} data-amend>
                {t("amend.link")}
              </a>
              <p className="mt-3">
                <a className={LINK} href={discoveryHref(locale, "recall", origin)} data-next>
                  {t("plan.next")}
                </a>
              </p>
            </section>
          </aside>
        </div>
      )}
    </DiscoveryFrame>
  );
}
