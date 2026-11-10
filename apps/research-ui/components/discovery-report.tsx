"use client";

import { useCallback, useEffect, useState } from "react";

import type { Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge, type DecisionRole } from "@/components/ui/base";
import { DETAILS_LABEL } from "@/components/screening-state-card";
import {
  DiscoveryFrame,
  DiscoveryRefusal,
  Eyebrow,
  LINK,
  Loading,
  OlderRunNote,
  RunSelector,
  discoveryHref,
  percent,
  refusalOf,
  stamp,
  statusText,
  useDiscoveryParams,
  type Refusal,
} from "@/components/discovery-frame";
import { getReport, putMethods, runReportHref, type IdentificationRow, type Report } from "@/lib/discovery-api";
import { getCorpus } from "@/lib/screening-v1";
import { discoveryT, providerName, type DiscoveryCopyKey } from "@/lib/discovery-copy";

/**
 * 06 Search report (spec `docs/ux/phase1-discovery/final/06-report.md`): what
 * each database was asked and returned, as `GET /discovery/report` wrote it.
 * No total is added up here. A capped database is "at least N". The methods
 * paragraph is a draft until the researcher's own review is recorded by the
 * engine (`PUT /discovery/report/methods`, `reviewed: true`, the one HUMAN
 * record of this phase); "reviewed" is shown only from the engine's answer.
 */

const MAX_TEXT = 20_000;

function completeness(locale: Locale, row: IdentificationRow): { role: DecisionRole; text: string } {
  const t = discoveryT(locale);
  switch (row.completeness) {
    case "full":
      return { role: "include", text: t("report.completeness.full") };
    case "lower_bound":
      return { role: "unclear", text: t("report.completeness.lowerBound") };
    case "failed":
      return { role: "blocked", text: t("report.completeness.failed") };
    case "stopped":
      return { role: "unclear", text: t("report.completeness.stopped") };
    default:
      return { role: "exclude", text: String(row.completeness) };
  }
}

export function DiscoveryReport({ locale }: Readonly<{ locale: Locale }>) {
  const t = discoveryT(locale);
  const { origin, run: wanted, ready } = useDiscoveryParams();
  const [report, setReport] = useState<Report | null>(null);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [saveError, setSaveError] = useState<Refusal | null>(null);
  const [text, setText] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [confirmDraft, setConfirmDraft] = useState(false);
  const [announce, setAnnounce] = useState("");
  const [copied, setCopied] = useState("");
  const [accepted, setAccepted] = useState(false);

  const load = useCallback(async () => {
    setRefusal(null);
    try {
      const next = await getReport(origin, wanted || undefined);
      setReport(next);
      setText(null);
    } catch (error) {
      setRefusal(refusalOf(error));
    }
    getCorpus(origin).then((c) => setAccepted(c.state === "ACCEPTED"), () => undefined);
  }, [origin, wanted]);

  useEffect(() => {
    if (ready) void load();
  }, [ready, load]);

  const runs = report?.runs.runs ?? [];
  const newest = !!report && runs[0]?.run === report.run;
  const summary = runs.find((r) => r.run === report?.run);
  const methods = report?.methods_text;
  const shown = text ?? methods?.text ?? "";
  const edited = text !== null && text !== methods?.text;

  const save = async (reviewed: boolean) => {
    if (!report) return;
    setSaving(true);
    setSaveError(null);
    try {
      const saved = await putMethods(origin, { text: shown, reviewed, run: report.run });
      setReport({ ...report, methods_text: { ...report.methods_text, ...saved } });
      setText(null);
      setConfirmDraft(false);
      setAnnounce(t("report.methods.saved"));
    } catch (error) {
      setSaveError(refusalOf(error));
    } finally {
      setSaving(false);
    }
  };

  const copy = async (value: string, label: string) => {
    try {
      await navigator.clipboard.writeText(value);
      setCopied(label);
    } catch {
      setCopied("");
    }
  };

  const tooLong = shown.length > MAX_TEXT;
  const canWrite = newest;

  return (
    <DiscoveryFrame locale={locale} current="report" origin={origin} run={wanted}>
      {refusal && !report ? (
        <DiscoveryRefusal locale={locale} refusal={refusal} origin={origin} onRetry={() => void load()} pageHeading />
      ) : !report || !methods ? (
        <Loading locale={locale} />
      ) : (
        <div className="space-y-6">
          <header>
            <Eyebrow locale={locale} step="report" name={t("report.eyebrowName")} />
            <h1 className="mt-2 font-display text-3xl text-ink">{t("report.title")}</h1>
            <p className="mt-2 max-w-2xl text-ink-muted">{t("report.lede")}</p>
            <p className="mt-2 flex flex-wrap items-center gap-2 text-ink">
              <DataCell>{report.run}</DataCell>
              <DecisionBadge role={report.status === "PARTIAL" ? "unclear" : "include"}>{statusText(locale, report.status)}</DecisionBadge>
            </p>
            {report.cap_override != null ? (
              <p className="mt-1 text-sm text-ink" data-cap-override>
                {t("report.capOverride", { cap: report.cap_override })}
              </p>
            ) : null}
            <RunSelector locale={locale} runs={runs} selected={report.run} origin={origin} step="report" />
            <OlderRunNote locale={locale} summary={summary} newest={newest} />
          </header>
          {report.runs.active_job ? (
            <p className="rounded-lg border border-rule bg-leaf p-3 text-ink" data-running>
              {t("report.running")}{" "}
              <a className={LINK} href={discoveryHref(locale, "harvest", origin)}>
                {t("job.openHarvest")}
              </a>
            </p>
          ) : null}

          <div className="grid gap-6 lg:grid-cols-3">
            <div className="min-w-0 space-y-6 lg:col-span-2">
              <section aria-labelledby="report-ident" className="rounded-lg border border-rule bg-leaf p-5">
                <h2 id="report-ident" className="font-semibold text-ink">
                  {t("report.identification")}
                </h2>
                <div className="mt-3 overflow-x-auto">
                  <table className="w-full min-w-[40rem] text-sm">
                    <caption className="sr-only">{t("report.identification")}</caption>
                    <thead>
                      <tr className="text-xs text-ink-muted">
                        {(["database", "query", "reported", "fetched", "completeness", "noAbstract", "searched"] as const).map((c) => (
                          <th key={c} scope="col" className="pb-2 pe-3 text-start">
                            {t(`report.col.${c}` as DiscoveryCopyKey)}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {report.identification.map((row) => {
                        const c = completeness(locale, row);
                        return (
                          <tr key={`${row.kind}-${row.database}`} className="border-t border-rule align-top" data-ident={row.database} data-completeness={row.completeness}>
                            <th scope="row" className="py-2 pe-3 text-start font-medium text-ink">
                              {row.kind === "import" ? row.database : providerName(row.database)}
                              {row.kind === "import" ? <span className="block text-xs text-ink-muted">{t("report.kind.import")}</span> : null}
                            </th>
                            <td className="max-w-[18rem] py-2 pe-3">
                              {row.executed_query ? (
                                <>
                                  <DataCell>{row.executed_query}</DataCell>
                                  <Button variant="quiet" onClick={() => void copy(row.executed_query ?? "", row.database)}>
                                    {t("report.copy", { database: providerName(row.database) })}
                                  </Button>
                                </>
                              ) : null}
                            </td>
                            <td className="py-2 pe-3">
                              <bdi dir="ltr">{row.reported_total ?? t("report.reportedNone")}</bdi>
                            </td>
                            <td className="py-2 pe-3" data-fetched>
                              <bdi dir="ltr">{row.completeness === "lower_bound" ? t("report.completeness.atLeast", { n: row.fetched ?? 0 }) : row.fetched}</bdi>
                            </td>
                            <td className="py-2 pe-3">
                              <DecisionBadge role={c.role}>{c.text}</DecisionBadge>
                              {row.completeness === "lower_bound" ? <span className="block text-xs text-ink-muted">{t("report.completeness.lowerBoundNote")}</span> : null}
                              {row.error_code ? (
                                <span className="block font-mono text-[0.8125rem] text-blocked" dir="ltr" data-error-code>
                                  {row.error_code}
                                </span>
                              ) : null}
                            </td>
                            <td className="py-2 pe-3">
                              <bdi dir="ltr">{row.no_abstract_rate == null ? t("report.noAbstractNone") : percent(row.no_abstract_rate)}</bdi>
                            </td>
                            <td className="py-2 pe-3">
                              <bdi dir="ltr">{stamp(row.searched_at)}</bdi>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                <p aria-live="polite" className="mt-2 text-xs text-ink-muted">
                  {copied ? t("copied") : ""}
                </p>
                <p className="mt-2 text-xs text-ink-muted">{t("report.stringsNote", { run: report.run })}</p>
                {newest && !accepted && report.identification.some((r) => r.completeness === "lower_bound" || r.completeness === "failed") ? (
                  <p className="mt-2 text-sm text-ink" data-again>
                    {t("report.again")}{" "}
                    <a className={LINK} href={discoveryHref(locale, "harvest", origin)}>
                      {t("steps.harvest")}
                    </a>
                  </p>
                ) : null}
              </section>

              <section className="rounded-lg border border-rule bg-leaf p-5 text-sm" data-not-searched>
                <h2 className="font-semibold text-ink">{t("report.notSearched.title")}</h2>
                <ul className="mt-2 space-y-1 text-ink">
                  {report.not_searched.map((n) => (
                    <li key={n.database}>
                      {providerName(n.database)} ·{" "}
                      {n.reason === "off by default" ? t("report.notSearched.off") : n.reason === "not selected in the protocol" ? t("report.notSearched.notSelected") : n.reason}
                    </li>
                  ))}
                </ul>
              </section>

              <section className="rounded-lg border border-rule bg-leaf p-5 text-sm" data-imports>
                <h2 className="font-semibold text-ink">{t("report.imports.title")}</h2>
                {report.imports.length === 0 ? (
                  <p className="mt-2 text-ink-muted">{t("report.imports.none")}</p>
                ) : (
                  <ul className="mt-2 space-y-3">
                    {report.imports.map((imp) => (
                      <li key={imp.label} data-import={imp.label}>
                        <p className="font-medium text-ink">
                          {imp.label} · {t("report.imports.records", { n: imp.records })}
                        </p>
                        {imp.limits ? (
                          <p className="text-ink-muted">
                            {t("report.imports.limits", { limits: "" })}
                            <bdi dir="ltr">{imp.limits}</bdi>
                          </p>
                        ) : null}
                        {imp.rejected.length ? (
                          <ul className="mt-1 text-xs text-ink-muted">
                            {imp.rejected.map((r) => (
                              <li key={`${r.line}-${r.code}`}>
                                <bdi dir="ltr">
                                  {r.line} · <span className="font-mono text-unclear">{r.code}</span> · {r.reason}
                                </bdi>
                              </li>
                            ))}
                          </ul>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                )}
              </section>

              <section className="rounded-lg border border-rule bg-leaf p-5 text-sm" data-dedup>
                <h2 className="font-semibold text-ink">{t("report.dedup.title")}</h2>
                {report.dedup.removed == null ? (
                  <p className="mt-2 text-ink" data-not-this-run>
                    {t("report.dedup.notThisRun")}
                  </p>
                ) : (
                  <dl className="mt-2 space-y-1">
                    <div className="flex gap-3">
                      <dt className="text-ink-muted">{t("report.dedup.removed")}</dt>
                      <dd className="text-ink">{report.dedup.removed}</dd>
                    </div>
                    {report.dedup.by_tier ? (
                      <>
                        <div className="flex gap-3">
                          <dt className="text-ink-muted">{t("dedup.tier.identifier")}</dt>
                          <dd className="text-ink">{report.dedup.by_tier.identifier}</dd>
                        </div>
                        <div className="flex gap-3">
                          <dt className="text-ink-muted">{t("dedup.tier.exactTitle")}</dt>
                          <dd className="text-ink">{report.dedup.by_tier.exact_title}</dd>
                        </div>
                        <div className="flex gap-3">
                          <dt className="text-ink-muted">{t("dedup.tier.fuzzyTitle")}</dt>
                          <dd className="text-ink">{report.dedup.by_tier.fuzzy_title}</dd>
                        </div>
                      </>
                    ) : null}
                    <div className="flex gap-3">
                      <dt className="text-ink-muted">{t("report.dedup.unique")}</dt>
                      <dd className="text-ink">{report.dedup.unique_works ?? t("report.dedup.notThisRunShort")}</dd>
                    </div>
                  </dl>
                )}
                <p className="mt-3 text-ink" data-window>
                  {t("report.window", { n: report.outside_year_window })}
                </p>
              </section>

              <section className="rounded-lg border border-rule bg-leaf p-5 text-sm" data-prisma>
                <h2 className="font-semibold text-ink">{t("report.prisma.title")}</h2>
                {report.prisma ? (
                  <dl className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-3">
                    {(
                      [
                        ["report.prisma.identified", report.prisma.identified],
                        ["report.prisma.duplicates", report.prisma.duplicates_removed],
                        ["report.prisma.screened", report.prisma.screened],
                        ["report.prisma.excluded", report.prisma.excluded.total],
                        ["report.prisma.included", report.prisma.included],
                      ] as const
                    ).map(([key, value]) => (
                      <div key={key}>
                        <dt className="text-ink-muted">{t(key)}</dt>
                        <dd className="text-ink">{value}</dd>
                      </div>
                    ))}
                  </dl>
                ) : (
                  <p className="mt-2 text-ink-muted">{t("report.prisma.none")}</p>
                )}
              </section>

              <section
                aria-labelledby="report-methods"
                className={`rounded-lg border p-5 ${methods.reviewed && !edited ? "border-rule bg-leaf" : "border-dashed border-ink-muted bg-leaf"}`}
                data-methods
                data-reviewed={methods.reviewed && !edited ? "true" : "false"}
              >
                <h2 id="report-methods" className="font-semibold text-ink">
                  {t("report.methods.title")}
                </h2>
                <p className="mt-1" aria-live="polite">
                  {edited ? (
                    <DecisionBadge role="unclear">{t("report.methods.badgeEdited")}</DecisionBadge>
                  ) : methods.reviewed ? (
                    <DecisionBadge role="include">{t("report.methods.badgeReviewed", { date: stamp(methods.reviewed_at) })}</DecisionBadge>
                  ) : (
                    <DecisionBadge role="exclude">{t("report.methods.badgeDraft")}</DecisionBadge>
                  )}{" "}
                  <span className="text-xs text-ink-muted">{announce}</span>
                </p>
                <p id="methods-built" className="mt-2 text-xs text-ink-muted">
                  {t("report.methods.built", { run: methods.built_from })}
                </p>
                <label htmlFor="methods-text" className="mt-3 block text-sm text-ink">
                  {t("report.methods.label", { run: report.run })}
                </label>
                <textarea
                  id="methods-text"
                  value={shown}
                  readOnly={!canWrite}
                  dir="auto"
                  rows={8}
                  aria-describedby="methods-built methods-count"
                  onChange={(e) => {
                    setText(e.target.value);
                    setAnnounce("");
                  }}
                  className="mt-1 w-full rounded-md border border-rule-strong bg-paper p-3 text-ink"
                />
                <p id="methods-count" className={`mt-1 text-xs ${tooLong ? "text-blocked" : "text-ink-muted"}`}>
                  {tooLong ? t("report.methods.tooLong") : t("report.methods.count", { n: shown.length })}
                </p>
                {saveError ? <DiscoveryRefusal locale={locale} refusal={saveError} origin={origin} onRetry={() => setSaveError(null)} /> : null}
                {confirmDraft ? (
                  <div role="alert" className="mt-3 rounded-md border border-rule bg-paper p-3 text-sm" data-unreview>
                    <p className="text-ink">{t("report.methods.unreview")}</p>
                    <div className="mt-2 flex flex-wrap gap-2">
                      <Button onClick={() => void save(false)} disabled={saving}>
                        {t("report.methods.confirmDraft")}
                      </Button>
                    </div>
                  </div>
                ) : null}
                <div className="mt-3 flex flex-wrap gap-2">
                  <Button onClick={() => void copy(shown, "methods")}>{t("report.methods.copy")}</Button>
                  {canWrite ? (
                    <>
                      <Button
                        disabled={saving || tooLong || !shown.trim()}
                        onClick={() => (methods.reviewed ? setConfirmDraft(true) : void save(false))}
                        data-save-draft
                      >
                        {t("report.methods.draft")}
                      </Button>
                      <Button variant="primary" disabled={saving || tooLong || !shown.trim()} onClick={() => void save(true)} data-review>
                        {saving ? t("report.methods.saving") : t("report.methods.review")}
                      </Button>
                    </>
                  ) : null}
                </div>
                {methods.earlier_reviewed ? (
                  <details className="mt-4 text-sm" data-earlier-reviewed>
                    <summary className="min-h-11 cursor-pointer py-3 leading-5 text-ink">
                      {t("report.methods.earlier", { run: methods.earlier_reviewed.run, date: stamp(methods.earlier_reviewed.reviewed_at) })}
                    </summary>
                    <p className="whitespace-pre-wrap text-ink" dir="auto">
                      {methods.earlier_reviewed.text}
                    </p>
                  </details>
                ) : null}
              </section>
            </div>

            <aside className="space-y-4">
              <section className="rounded-lg border border-rule bg-leaf p-5 text-sm">
                <h2 className="font-semibold text-ink">{t("report.history.title")}</h2>
                <ul className="mt-2 space-y-1">
                  {runs.map((r) => (
                    <li key={r.run}>
                      <a className={LINK} href={discoveryHref(locale, "report", origin, r === runs[0] ? "" : r.run)}>
                        <bdi dir="ltr">
                          {r.run} · {stamp(r.started_at)} · {statusText(locale, r.status)}
                        </bdi>
                      </a>
                    </li>
                  ))}
                </ul>
                <p className="mt-2 text-xs text-ink-muted">{t("report.history.note")}</p>
                <p className="mt-3">
                  <a className={LINK} href={runReportHref(origin, report.run)} target="_blank" rel="noreferrer" data-markdown>
                    {t("report.markdown")}
                  </a>
                </p>
              </section>
              <section className="rounded-lg border border-rule bg-leaf p-5">
                <p>
                  <a className={LINK} href={discoveryHref(locale, "dedup", origin)}>
                    {t("report.back")}
                  </a>
                </p>
                <p>
                  <a className={LINK} href={discoveryHref(locale, "handoff", origin)} data-next>
                    {t("report.next")}
                  </a>
                </p>
              </section>
              <details className="text-xs">
                <summary className="min-h-11 cursor-pointer py-3 leading-5 text-ink-muted">{DETAILS_LABEL[locale]}</summary>
                <p className="text-ink-muted">
                  <DataCell>{report.shape}</DataCell>
                </p>
              </details>
            </aside>
          </div>
        </div>
      )}
    </DiscoveryFrame>
  );
}
