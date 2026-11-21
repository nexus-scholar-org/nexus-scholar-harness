"use client";

import { useEffect, useState } from "react";

import type { Locale } from "@/i18n";
import { formatNumber } from "@/i18n";
import { Button, DataCell, Hint } from "@/components/ui/base";
import { refusalOf, stamp, type Refusal } from "@/components/inception-frame";
import { QueryWorkbench } from "@/components/query-workbench";
import { discoveryT } from "@/lib/discovery-copy";
import { inceptionT } from "@/lib/inception-copy";
import { postAmend, type AmendAnswer, type Version } from "@/lib/workbench-api";
import { workbenchT } from "@/lib/workbench-copy";

/**
 * "Change the search" on Plan (M11a part D; spec `docs/ux/phase1-discovery/final/10-plan-amend-search.md`).
 *
 * A closed section on Plan that opens the workbench on the protocol's query
 * (the counts, the known papers read only, the comparison with the harvest).
 * "Record this amendment" opens an inline confirmation: one sentence of
 * reason, the engine's list of what the amendment makes obsolete, the counts
 * before and after from the count log, then the one write (the M10c 9(a)
 * path, `POST /discovery/workbench/amend`). After the corpus is accepted the
 * workbench still opens and counts, and records nothing.
 */

export type PlanSearch = {
  query_key: string;
  concepts: { concept: string; synonyms: string[] }[];
  start_year: number | null;
  end_year: number | null;
  languages: string[];
  golden_seeds: string[];
};

const DATABASE_NAMES: Record<string, string> = {
  openalex: "OpenAlex", semanticscholar: "Semantic Scholar", crossref: "Crossref", arxiv: "arXiv", pubmed: "PubMed", biorxiv: "bioRxiv",
};
const nameOf = (id: string) => DATABASE_NAMES[id] ?? id;

export function PlanChangeSearch({
  locale, origin, search, fingerprint, providers, accepted, onRecorded,
}: Readonly<{
  locale: Locale;
  origin: string;
  search: PlanSearch;
  fingerprint: string;
  providers: string[] | null;
  accepted: boolean;
  onRecorded: () => void;
}>) {
  const t = discoveryT(locale);
  const wt = workbenchT(locale);
  const [open, setOpen] = useState(false);
  const [confirming, setConfirming] = useState<Version | null>(null);
  const [reason, setReason] = useState("");
  const [dry, setDry] = useState<AmendAnswer | null>(null);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [recording, setRecording] = useState(false);
  const [done, setDone] = useState<AmendAnswer | null>(null);
  const [reasonMissing, setReasonMissing] = useState(false);

  // The consequences are the engine's: a dry call when the confirmation opens.
  useEffect(() => {
    if (!confirming) return setDry(null);
    const controller = new AbortController();
    setDry(null);
    postAmend(origin, { query_key: "main", concepts: confirming.concepts, reason: "", protocol_fingerprint: fingerprint, dry_run: true }, controller.signal).then(
      setDry,
      (e) => {
        if (!controller.signal.aborted) setRefusal(refusalOf(e));
      },
    );
    return () => controller.abort();
  }, [confirming, origin, fingerprint]);

  const record = async () => {
    if (!confirming) return;
    if (!reason.trim()) return setReasonMissing(true);
    setRecording(true);
    setRefusal(null);
    try {
      const answer = await postAmend(origin, { query_key: "main", concepts: confirming.concepts, reason: reason.trim(), protocol_fingerprint: fingerprint, dry_run: false });
      setDone(answer);
      setConfirming(null);
      setReason("");
      onRecorded();
    } catch (e) {
      setRefusal(refusalOf(e));
    } finally {
      setRecording(false);
    }
  };

  const counts = (answer: AmendAnswer, side: "before" | "after") => {
    const parts = Object.entries(answer.counts ?? {}).map(([db, pair]) => {
      const v = pair[side];
      return `${nameOf(db)} ${typeof v === "number" ? formatNumber(locale, v) : t("plan.search.counts.none")}`;
    });
    return parts.length ? parts.join(inceptionT(locale)("list.sep")) : t("plan.search.counts.none");
  };

  const c = dry?.consequences;
  const nothing = c && !c.runs.length && !c.exports.length && !c.recall_checks.length && !c.proposals;

  // A plain card, not a landmark: the workbench inside is the one region named "Search" (axe landmark-unique).
  return (
    <div className="rounded-lg border border-rule bg-leaf p-5" data-plan-search>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-1">
          <h2 id="plan-search-title" className="font-semibold text-ink">
            {wt("workbench.title")}
          </h2>
          <Hint locale={locale} label={wt("workbench.title")} text={t("plan.search.help")} textKey="plan.search.help" />
        </div>
        <Button aria-expanded={open} aria-controls="plan-search-region" onClick={() => setOpen((o) => !o)} data-plan-search-open>
          {open ? t("plan.search.close") : t("plan.search.open")}
        </Button>
      </div>
      {done ? (
        <p role="status" className="mt-2 text-sm text-ink" data-amended>
          {t("plan.search.done")} {t("plan.search.backup", { path: done.backup ?? "" })}{" "}
          <DataCell>{done.protocol_fingerprint}</DataCell>
        </p>
      ) : null}
      {open ? (
        <div id="plan-search-region" className="mt-3 space-y-3" data-plan-search-region>
          {search.concepts.length === 0 ? (
            <p className="text-sm text-ink">{t("plan.search.noConcepts")}</p>
          ) : (
            <>
              <div role="group" aria-labelledby="plan-search-protocol" className="rounded-md border border-rule bg-paper p-3" data-in-protocol>
                <p id="plan-search-protocol" className="text-xs font-semibold text-ink">
                  {t("plan.search.protocol")}
                </p>
                <p className="text-xs text-ink-muted">
                  {t("plan.fingerprint")} <DataCell>{fingerprint}</DataCell>
                </p>
                <ul className="mt-1 space-y-1 text-sm">
                  {search.concepts.map((concept, i) => (
                    <li key={`${i}:${concept.concept}`} data-protocol-concept={i}>
                      {i > 0 ? <span className="me-1 text-xs text-ink-muted">{wt("workbench.op.and")}</span> : null}
                      <bdi dir="auto">{[concept.concept, ...concept.synonyms].join(` ${wt("workbench.op.or")} `)}</bdi>
                    </li>
                  ))}
                </ul>
              </div>
              <QueryWorkbench
                key={fingerprint}
                locale={locale}
                origin={origin}
                place={{ kind: "workspace" }}
                saved={search.concepts}
                startYear={search.start_year}
                endYear={search.end_year}
                languages={search.languages}
                seeds={search.golden_seeds}
                providers={providers}
                primary={({ version, changed }) =>
                  accepted ? null : (
                    <Button onClick={() => setConfirming(version)} disabled={!changed} data-record-open>
                      {t("plan.search.record")}
                    </Button>
                  )
                }
              />
            </>
          )}
          {accepted ? (
            <p className="text-sm text-ink" data-plan-search-accepted>
              {t("plan.search.accepted")}{" "}
              <a className="inline-flex min-h-11 items-center text-brand underline" href={`/${locale}/inception/import/`}>
                {t("plan.search.accepted.new")}
              </a>
            </p>
          ) : null}
          {confirming && !accepted ? (
            <form
              aria-labelledby="plan-search-confirm"
              className="space-y-3 rounded-md border border-rule bg-paper p-3"
              onSubmit={(event) => {
                event.preventDefault();
                void record();
              }}
              onKeyDown={(event) => {
                if (event.key === "Escape") setConfirming(null);
              }}
              data-amend-confirm
            >
              <h3 id="plan-search-confirm" className="font-semibold text-ink">
                {t("plan.search.confirm.title")}
              </h3>
              <div>
                <label htmlFor="plan-search-reason" className="block text-sm text-ink">
                  {t("plan.search.reason.label")}
                </label>
                <input
                  id="plan-search-reason"
                  value={reason}
                  autoFocus
                  maxLength={2000}
                  dir="auto"
                  aria-invalid={reasonMissing || undefined}
                  aria-describedby="plan-search-reason-help"
                  onChange={(event) => {
                    setReason(event.target.value);
                    setReasonMissing(false);
                  }}
                  className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink"
                />
                <p id="plan-search-reason-help" className="mt-1 text-xs text-ink-muted">
                  {reasonMissing ? t("plan.search.reason.need") : t("plan.search.reason.help")}
                </p>
              </div>
              {!dry ? (
                <p role="status" className="text-sm text-ink-muted">{t("plan.search.conseq.loading")}</p>
              ) : (
                <ul id="plan-search-consequences" className="list-disc space-y-1 ps-5 text-sm text-ink" data-consequences>
                  {nothing ? <li>{t("plan.search.conseq.none")}</li> : null}
                  {c?.runs.map((r) => (
                    <li key={r.run} data-conseq="run">
                      {t("plan.search.conseq.run", { run: r.run, n: formatNumber(locale, r.records ?? 0) })}
                    </li>
                  ))}
                  {c?.exports.map((x) => (
                    <li key={x.id ?? x.database} data-conseq="export">
                      <ExportLine locale={locale} database={x.database} records={x.records ?? 0} date={x.staged_on ?? ""} query={x.string ?? null} />{" "}
                      {t("plan.search.conseq.exportAdvice")}
                    </li>
                  ))}
                  {c?.recall_checks.map((r) => (
                    <li key={r.check} data-conseq="recall">
                      <Isolated values={{ date: stamp(r.checked_at) }} text={(m) => t("plan.search.conseq.recall", { date: m.date })} />
                    </li>
                  ))}
                  {c && (c.runs.length || c.recall_checks.length) ? <li data-conseq="estimate">{t("plan.search.conseq.estimate")}</li> : null}
                  {c?.proposals ? <li data-conseq="proposals">{t("plan.search.conseq.proposals", { n: formatNumber(locale, c.proposals) })}</li> : null}
                </ul>
              )}
              {dry ? (
                <div className="text-sm text-ink" data-amend-counts>
                  <p>{t("plan.search.counts.before", { summary: counts(dry, "before") })}</p>
                  <p>{t("plan.search.counts.after", { summary: counts(dry, "after") })}</p>
                </div>
              ) : null}
              <div className="flex flex-wrap gap-2">
                <Button variant="primary" type="submit" disabled={recording || !dry} aria-describedby="plan-search-consequences" data-record>
                  {recording ? t("plan.search.recording") : t("plan.search.record")}
                </Button>
                <Button onClick={() => setConfirming(null)} data-record-cancel>
                  {t("plan.search.cancel")}
                </Button>
              </div>
            </form>
          ) : null}
          {refusal ? (
            <p role="alert" className="text-sm text-blocked" data-amend-refusal={refusal.code}>
              {refusal.code === "DISCOVERY_JOB_ACTIVE"
                ? t("plan.search.err.jobActive", { kind: "job" })
                : refusal.code === "PROTOCOL_AMENDMENT_REFUSED"
                  ? t("plan.search.err.outside")
                  : refusal.code === "WORKBENCH_PROTOCOL_CHANGED"
                    ? t("plan.changed")
                    : refusal.code === "WORKBENCH_REASON_INVALID"
                      ? t("plan.search.reason.need")
                      : refusal.message || refusal.code}{" "}
              <span className="font-mono text-xs" dir="ltr">{refusal.code}</span>
            </p>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}

/**
 * A catalog sentence with some values isolated left to right (I18N.md: dates and database strings
 * go in `<bdi dir="ltr">`; in Arabic text the digits of 2026-11-01 would otherwise be laid out
 * right to left). The sentence itself follows the page's direction.
 */
function Isolated({ text, values }: Readonly<{ text: (marks: Record<string, string>) => string; values: Record<string, string> }>) {
  const names = Object.keys(values);
  const marks = Object.fromEntries(names.map((name, i) => [name, `\u0000${i}\u0000`]));
  const parts = text(marks).split(/\u0000(\d+)\u0000/);
  return (
    <>
      {parts.map((part, i) =>
        i % 2 ? (
          <bdi key={i} dir="ltr" className={names[Number(part)] === "string" ? "font-mono" : undefined}>
            {values[names[Number(part)]]}
          </bdi>
        ) : (
          part
        ),
      )}
    </>
  );
}

/**
 * One staged export in the consequences list (spec: "{database}, {n} records, staged {date}.
 * Searched there with: {string}. It stays as it is.").
 */
function ExportLine({ locale, database, records, date, query }: Readonly<{ locale: Locale; database: string; records: number; date: string; query: string | null }>) {
  const t = discoveryT(locale);
  const values: Record<string, string> = query ? { date, string: query } : { date };
  return (
    <Isolated
      values={values}
      text={(m) =>
        t("plan.search.conseq.export", {
          database,
          n: formatNumber(locale, records),
          date: m.date,
          searched: query ? t("plan.search.conseq.exportString", { string: m.string }) : t("plan.search.conseq.exportNoString"),
        })
      }
    />
  );
}
