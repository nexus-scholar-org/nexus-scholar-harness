"use client";

import { useCallback, useEffect, useRef, useState, type Ref } from "react";

import type { Locale } from "@/i18n";
import { formatNumber } from "@/i18n";
import { Button, DataCell, Hint } from "@/components/ui/base";
import { DiscoveryRefusal, discoveryHref, LINK, type DiscoveryStep } from "@/components/discovery-frame";
import { inceptionHref, refusalOf, stamp, type Refusal } from "@/components/inception-frame";
import { QueryWorkbench } from "@/components/query-workbench";
import { discoveryT } from "@/lib/discovery-copy";
import { inceptionT } from "@/lib/inception-copy";
import { postAmend, type AmendAnswer, type Version } from "@/lib/workbench-api";
import { workbenchT } from "@/lib/workbench-copy";

/**
 * "Change the search" on Plan (M11a part D; spec `docs/ux/phase1-discovery/final/10-plan-amend-search.md`).
 *
 * The secondary button sits in the header of the "Executed string per database"
 * card (`PlanSearchToggle`); opened, the region (`PlanChangeSearch`) is drawn by
 * Plan full width above its two columns. It holds the protocol's search read only
 * and the workbench on it (the counts, the known papers, the comparison).
 * "Record this amendment" opens the confirmation: one sentence of reason, the
 * engine's list of what the amendment makes obsolete, the counts before and
 * after from the count log, then the one write (the M10c 9(a) path,
 * `POST /discovery/workbench/amend`). After the corpus is accepted the workbench
 * still opens and counts, and records nothing.
 */

export type PlanSearch = {
  query_key: string;
  concepts: { concept: string; synonyms: string[] }[];
  start_year: number | null;
  end_year: number | null;
  languages: string[];
  golden_seeds: string[];
};

export const PLAN_SEARCH_REGION = "plan-search-region";

const DATABASE_NAMES: Record<string, string> = {
  openalex: "OpenAlex", semanticscholar: "Semantic Scholar", crossref: "Crossref", arxiv: "arXiv", pubmed: "PubMed", biorxiv: "bioRxiv",
};
const nameOf = (id: string) => DATABASE_NAMES[id] ?? id;

/** Which screen follows a running job (the shared "Follow the running job"). */
const JOB_PAGE: Record<string, DiscoveryStep> = { run: "harvest", prepare: "harvest", recall: "recall", chase: "chase" };

/** The entry, in the header of Plan's executed-strings card (spec "Entry / exit"). */
export function PlanSearchToggle({ locale, open, onToggle, buttonRef }: Readonly<{ locale: Locale; open: boolean; onToggle: () => void; buttonRef?: Ref<HTMLButtonElement> }>) {
  const t = discoveryT(locale);
  return (
    <span className="flex items-center gap-1">
      <Button ref={buttonRef} aria-expanded={open} aria-controls={open ? PLAN_SEARCH_REGION : undefined} onClick={onToggle} data-plan-search-open>
        {t("plan.search.open")}
      </Button>
      <Hint locale={locale} label={t("plan.search.open")} text={t("plan.search.help")} textKey="plan.search.help" />
    </span>
  );
}

type Focus = "region" | "record-open" | "confirm" | "refusal" | null;

export function PlanChangeSearch({
  locale, origin, search, fingerprint, providers, accepted, onClose, onRecorded, onProtocolChanged,
}: Readonly<{
  locale: Locale;
  origin: string;
  search: PlanSearch;
  fingerprint: string;
  providers: string[] | null;
  accepted: boolean;
  onClose: () => void;
  /** The amendment was written: Plan takes the new fingerprint as its own, reads again and moves focus to its h1. */
  onRecorded: (answer: AmendAnswer) => void;
  /** The engine says the protocol changed elsewhere: Plan reads it again. */
  onProtocolChanged: () => void;
}>) {
  const t = discoveryT(locale);
  const wt = workbenchT(locale);
  const [confirming, setConfirming] = useState<{ version: Version; key: string } | null>(null);
  const [reason, setReason] = useState("");
  const [dry, setDry] = useState<AmendAnswer | null>(null);
  const [dryRefusal, setDryRefusal] = useState<Refusal | null>(null);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [recording, setRecording] = useState(false);
  const [done, setDone] = useState<AmendAnswer | null>(null);
  // The engine may tidy what it records (spaces, repeated synonyms): after the researcher's own
  // amendment the workbench starts again from the protocol as recorded (review D-R2). A change made
  // elsewhere does not remount it, so edits in this tab stay (decision D item 13).
  const [recorded, setRecorded] = useState(0);
  const [reasonMissing, setReasonMissing] = useState(false);
  const [focus, setFocus] = useState<Focus>("region");
  const versionKeyRef = useRef("");
  const region = useRef<HTMLDivElement>(null);
  const recordOpen = useRef<HTMLButtonElement>(null);
  const confirmHeading = useRef<HTMLHeadingElement>(null);
  const reasonField = useRef<HTMLInputElement>(null);
  const refusalLine = useRef<HTMLDivElement>(null);

  // Focus moves the spec asks for (Keyboard): into the region when it opens, back to
  // "Record this amendment" after Escape or Cancel, to the card heading after a refusal.
  useEffect(() => {
    if (!focus) return;
    const target = { region: region.current, "record-open": recordOpen.current, confirm: confirmHeading.current, refusal: refusalLine.current }[focus];
    if (!target) return;
    setFocus(null);
    target.focus();
    if (focus === "region") target.scrollIntoView?.({ block: "start" });
  }, [focus, confirming, refusal]);

  const close = (to: Focus = "record-open") => {
    setConfirming(null);
    setDry(null);
    setDryRefusal(null);
    setReasonMissing(false);
    setFocus(to);
  };

  // A confirmation is for one version: an edit (or Discard) closes it (review D-R1 #3).
  const onVersion = useCallback((key: string) => {
    versionKeyRef.current = key;
    setConfirming((open) => (open && open.key !== key ? null : open));
  }, []);

  // The consequences are the engine's: a dry call when the confirmation opens.
  useEffect(() => {
    if (!confirming) return;
    const controller = new AbortController();
    setDry(null);
    setDryRefusal(null);
    postAmend(origin, { query_key: "main", concepts: confirming.version.concepts, reason: "", protocol_fingerprint: fingerprint, dry_run: true }, controller.signal).then(
      setDry,
      (e) => {
        if (!controller.signal.aborted) setDryRefusal(refusalOf(e));
      },
    );
    return () => controller.abort();
  }, [confirming, origin, fingerprint]);

  const open = (version: Version) => {
    setRefusal(null);
    setDone(null);
    setConfirming({ version, key: versionKeyRef.current });
  };

  const record = async () => {
    if (!confirming || recording) return;
    if (!reason.trim()) {
      setReasonMissing(true);
      reasonField.current?.focus();
      return;
    }
    setRecording(true);
    setRefusal(null);
    try {
      const answer = await postAmend(origin, { query_key: "main", concepts: confirming.version.concepts, reason: reason.trim(), protocol_fingerprint: fingerprint, dry_run: false });
      setDone(answer);
      setRecorded((n) => n + 1);
      setConfirming(null);
      setDry(null);
      setReason("");
      onRecorded(answer);
    } catch (e) {
      const r = refusalOf(e);
      setRefusal(r);
      if (r.code === "WORKBENCH_PROTOCOL_CHANGED") {
        // The page reads the protocol again; Record waits until it is read (spec "Stale").
        setConfirming(null);
        setDry(null);
        onProtocolChanged();
        setFocus("refusal");
      } else {
        setFocus("confirm");
      }
    } finally {
      setRecording(false);
    }
  };

  const countsLine = (answer: AmendAnswer, side: "before" | "after") => {
    const entries = Object.entries(answer.counts ?? {});
    const sep = inceptionT(locale)("list.sep");
    const values = Object.fromEntries(entries.map(([db], i) => [`db${i}`, nameOf(db)]));
    return (
      <Isolated
        values={values}
        text={(m) =>
          t(side === "before" ? "plan.search.counts.before" : "plan.search.counts.after", {
            summary: entries.length
              ? entries.map(([, pair], i) => `${m[`db${i}`]} ${typeof pair[side] === "number" ? formatNumber(locale, pair[side] as number) : t("plan.search.counts.none")}`).join(sep)
              : t("plan.search.counts.none"),
          })
        }
      />
    );
  };

  const c = dry?.consequences;
  const nothing = c && !c.runs.length && !c.exports.length && !c.recall_checks.length && !c.proposals && !c.estimate;

  const refusalWords = (r: Refusal) => {
    if (r.code === "DISCOVERY_JOB_ACTIVE") {
      const kind = (r.details as { job?: { kind?: string } } | undefined)?.job?.kind ?? "run";
      return (
        <>
          {t("plan.search.err.jobActive")}{" "}
          <a className={LINK} href={discoveryHref(locale, JOB_PAGE[kind] ?? "harvest", origin)} data-follow-job>
            {t("job.follow")}
          </a>
        </>
      );
    }
    if (r.code === "PROTOCOL_AMENDMENT_REFUSED") {
      return (
        <>
          {t("plan.search.err.outside")}
          {r.message ? (
            <details className="mt-1 text-xs text-ink-muted">
              <summary className="min-h-11 cursor-pointer rounded-sm py-3 leading-5 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">{t("plan.search.details")}</summary>
              <bdi dir="ltr">{r.message}</bdi>
            </details>
          ) : null}
        </>
      );
    }
    if (r.code === "WORKBENCH_PROTOCOL_CHANGED") return t("plan.changed");
    if (r.code === "WORKBENCH_REASON_INVALID") return t("plan.search.reason.need");
    return null;
  };

  const refusalBlock = (r: Refusal) => {
    const words = refusalWords(r);
    return words ? (
      <div ref={refusalLine} tabIndex={-1} role="alert" className="text-sm text-blocked" data-amend-refusal={r.code}>
        {words} <span className="font-mono text-xs" dir="ltr">{r.code}</span>
      </div>
    ) : (
      <div ref={refusalLine} tabIndex={-1} data-amend-refusal={r.code}>
        <DiscoveryRefusal locale={locale} refusal={r} origin={origin} onRetry={() => setRefusal(null)} />
      </div>
    );
  };

  return (
    // A plain block, not a landmark: the workbench inside is the one region named "Search" (axe landmark-unique).
    <div id={PLAN_SEARCH_REGION} ref={region} tabIndex={-1} className="space-y-3 rounded-lg border border-rule bg-leaf p-5 focus:outline-none" data-plan-search>
      <div className="flex flex-wrap items-center justify-end gap-2">
        <Button onClick={onClose} data-plan-search-close>
          {t("plan.search.close")}
        </Button>
      </div>
      {done ? (
        <p role="status" className="text-sm text-ink" data-amended>
          {t("plan.search.done")} {t("plan.search.backup", { path: done.backup ?? "" })} <DataCell>{done.protocol_fingerprint}</DataCell>
        </p>
      ) : null}
      {refusal && !confirming ? refusalBlock(refusal) : null}
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
          <div role="group" aria-labelledby="plan-search-version" data-this-version>
            <p id="plan-search-version" className="mb-1 text-xs font-semibold text-ink">
              {t("plan.search.version")}
            </p>
            <QueryWorkbench
              key={recorded}
              locale={locale}
              origin={origin}
              place={{ kind: "workspace" }}
              saved={search.concepts}
              startYear={search.start_year}
              endYear={search.end_year}
              languages={search.languages}
              seeds={search.golden_seeds}
              providers={providers}
              onVersion={onVersion}
              // Ctrl+Enter: once the version differs, it opens the confirmation (never records).
              onPrimaryKey={({ version, changed }) => {
                if (accepted || !changed || confirming) return false;
                open(version);
                return true;
              }}
              primary={({ version, changed }) =>
                accepted ? null : (
                  // The decision bar's one primary action: Count, then this; while the confirmation is open its own button is.
                  <Button ref={recordOpen} variant={changed && !confirming ? "primary" : "secondary"} onClick={() => open(version)} disabled={!changed} data-record-open>
                    {t("plan.search.record")}
                  </Button>
                )
              }
            />
          </div>
        </>
      )}
      {accepted ? (
        <p className="text-sm text-ink" data-plan-search-accepted>
          {t("plan.search.accepted")}{" "}
          <a className={LINK} href={inceptionHref(locale, "import", "", origin)} data-plan-search-new>
            {t("plan.search.accepted.new")}
          </a>
        </p>
      ) : null}
      {confirming && !accepted ? (
        // Not a <form>: Enter in the one-line reason field never records (spec "Keyboard"); only the button does.
        <div
          role="group"
          aria-labelledby="plan-search-confirm"
          className="space-y-3 rounded-md border border-rule bg-paper p-3"
          onKeyDown={(event) => {
            if (event.key === "Escape") {
              event.preventDefault();
              close();
            }
          }}
          data-amend-confirm
        >
          <h3 id="plan-search-confirm" ref={confirmHeading} tabIndex={-1} className="font-semibold text-ink focus:outline-none">
            {t("plan.search.confirm.title")}
          </h3>
          <div>
            <label htmlFor="plan-search-reason" className="block text-sm text-ink">
              {t("plan.search.reason.label")}
            </label>
            <input
              id="plan-search-reason"
              ref={reasonField}
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
              onKeyDown={(event) => {
                if (event.key === "Enter") event.preventDefault();
              }}
              className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink"
            />
            <p id="plan-search-reason-help" className="mt-1 text-xs text-ink-muted">
              {reasonMissing ? t("plan.search.reason.need") : t("plan.search.reason.help")}
            </p>
          </div>
          {dryRefusal ? (
            refusalBlock(dryRefusal)
          ) : !dry ? (
            <p role="status" className="text-sm text-ink-muted">{t("plan.search.conseq.loading")}</p>
          ) : (
            <ul id="plan-search-consequences" className="list-disc space-y-1 ps-5 text-sm text-ink" data-consequences>
              {nothing ? <li>{t("plan.search.conseq.none")}</li> : null}
              {c?.runs.map((r) => (
                <li key={r.run} data-conseq="run">
                  <Isolated values={{ run: r.run }} text={(m) => t("plan.search.conseq.run", { run: m.run, n: formatNumber(locale, r.records ?? 0) })} />
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
              {c?.estimate ? <li data-conseq="estimate">{t("plan.search.conseq.estimate")}</li> : null}
              {c?.proposals ? <li data-conseq="proposals">{t("plan.search.conseq.proposals", { n: formatNumber(locale, c.proposals) })}</li> : null}
            </ul>
          )}
          {dry ? (
            <div className="text-sm text-ink" data-amend-counts>
              <p>{countsLine(dry, "before")}</p>
              <p>{countsLine(dry, "after")}</p>
            </div>
          ) : null}
          {refusal ? refusalBlock(refusal) : null}
          <div className="flex flex-wrap gap-2">
            <Button onClick={() => close()} data-record-cancel>
              {t("plan.search.cancel")}
            </Button>
            <Button variant="primary" onClick={() => void record()} disabled={recording || !dry} aria-describedby="plan-search-consequences" data-record>
              {recording ? t("plan.search.recording") : t("plan.search.record")}
            </Button>
          </div>
        </div>
      ) : null}
    </div>
  );
}

/**
 * A catalog sentence with some values isolated left to right (I18N.md: dates, run ids, database
 * names and database strings go in `<bdi dir="ltr">`; in Arabic text the digits of 2026-11-01
 * would otherwise be laid out right to left). The sentence itself follows the page's direction.
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
  const values: Record<string, string> = query ? { database, date, string: query } : { database, date };
  return (
    <Isolated
      values={values}
      text={(m) =>
        t("plan.search.conseq.export", {
          database: m.database,
          n: formatNumber(locale, records),
          date: m.date,
          searched: query ? t("plan.search.conseq.exportString", { string: m.string }) : t("plan.search.conseq.exportNoString"),
        })
      }
    />
  );
}
