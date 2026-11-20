"use client";

import { useEffect, useRef, useState, type ReactNode, type RefObject } from "react";

import type { Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge, Hint } from "@/components/ui/base";
import { DETAILS_LABEL } from "@/components/screening-state-card";
import { refusalOf, stamp } from "@/components/inception-frame";
import { discoveryT } from "@/lib/discovery-copy";
import { inceptionT, type InceptionCopyKey } from "@/lib/inception-copy";
import { getReconJob, streamReconJob, type ReconJob, type ReconLeg, type ReconState } from "@/lib/recon-api";

/**
 * The parts Explore (spec 02) and Direction (spec 03) share, M4d: following a
 * recon job, the databases asked, the key lines, the partial-pool banner and
 * the warning before a search replaces a bound pool. Every value shown is the
 * engine's; nothing here judges a pool.
 */

/** How often a job is read again once its stream closed early (spec 02, Loading). */
export const POLL_MS = 2000;

export type LegProgress = { provider: string; fetched: number };

/**
 * Follow one recon job: the live `leg` lines from its event stream, then its
 * end. A stream that closes without `done` or `failed` falls back to reading
 * the job every two seconds; `RECON_JOB_NOT_FOUND` (the console restarted)
 * ends it with `notFound`, and the screen reads the session again.
 */
export function useReconJob(
  origin: string,
  draftId: string,
  jobId: string | null,
  onEnd: (job: ReconJob | null, notFound: boolean) => void,
): { legs: LegProgress[]; lost: boolean } {
  const [legs, setLegs] = useState<LegProgress[]>([]);
  const [lost, setLost] = useState(false);
  const endRef = useRef(onEnd);
  useEffect(() => {
    endRef.current = onEnd;
  });

  useEffect(() => {
    setLegs([]);
    setLost(false);
    if (!jobId) return;
    const controller = new AbortController();
    let cancelled = false;
    const seen = new Map<string, number>();
    const finish = (job: ReconJob | null, notFound = false) => {
      if (!cancelled) endRef.current(job, notFound);
    };
    const poll = async (): Promise<void> => {
      while (!cancelled) {
        try {
          const { job } = await getReconJob(origin, draftId, jobId, controller.signal);
          if (cancelled) return;
          setLost(false);
          if (job.state === "succeeded" || job.state === "failed") return finish(job);
        } catch (error) {
          if (cancelled) return;
          if (refusalOf(error).code === "RECON_JOB_NOT_FOUND") return finish(null, true);
          setLost(true);
        }
        await new Promise((resolve) => setTimeout(resolve, POLL_MS));
      }
    };
    void (async () => {
      let last: ReconJob | null = null;
      try {
        const result = await streamReconJob(
          origin,
          draftId,
          jobId,
          (event) => {
            if (event.event === "leg") {
              seen.set(event.data.provider, event.data.fetched);
              if (!cancelled) setLegs([...seen].map(([provider, fetched]) => ({ provider, fetched })));
            } else last = event.data.job;
          },
          controller.signal,
        );
        if (cancelled) return;
        if (result.ended && last) return finish(last);
      } catch (error) {
        if (cancelled) return;
        if (refusalOf(error).code === "RECON_JOB_NOT_FOUND") return finish(null, true);
        setLost(true);
      }
      await poll();
    })();
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [origin, draftId, jobId]);

  return { legs, lost };
}

/** A database's display name; an unknown id shows as the engine wrote it. */
export function providerLabel(locale: Locale, id: string): string {
  const key = `explore.provider.${id}` as InceptionCopyKey;
  return ["openalex", "semanticscholar", "crossref", "arxiv"].includes(id) ? inceptionT(locale)(key) : id;
}

/** The engine's codes are offline when the console cannot be reached at all. */
export function isOffline(code: string | undefined): boolean {
  return code === "ENGINE_UNREACHABLE" || code === "CONSOLE_UNREACHABLE" || code === "CONSOLE_TIMEOUT";
}

/** "{from} to {to}" with "present" for an open end, from the values the engine recorded. */
export function yearsText(locale: Locale, from: number | null | undefined, to: number | null | undefined): string {
  const t = inceptionT(locale);
  return t("explore.first.years", { from: from == null ? "" : String(from), to: to == null ? t("explore.first.toPresent") : String(to) });
}

/** The changed scope parts the engine named, in words. */
export function partsText(locale: Locale, parts: string[]): string {
  const t = inceptionT(locale);
  return parts
    .map((p) => (["topic", "years", "languages"].includes(p) ? t(`explore.changed.part.${p}` as InceptionCopyKey) : p))
    .join(t("list.sep"));
}

/** The two key lines exactly as the discovery Plan screen prints them (spec 02, Databases asked). */
export function KeyLines({ locale, keys, emptyNote = false }: Readonly<{ locale: Locale; keys: ReconState["keys"]; emptyNote?: boolean }>) {
  const t = inceptionT(locale);
  const d = discoveryT(locale);
  if (!keys) return null;
  return (
    <dl className="grid gap-3 text-sm sm:grid-cols-2" data-key-lines>
      <div data-openalex-key-set={keys.openalex_key_set ? "true" : "false"}>
        <dt className="text-ink-muted">
          {d("openalexKey.title")}
          {/* M10d (03-guidance I-E30): the background note is a hint; the missing key stays on the page as the badge. */}
          {!keys.openalex_key_set && emptyNote ? <Hint locale={locale} label={d("openalexKey.title")} text={t("explore.keys.openalex.emptyNote")} textKey="explore.keys.openalex.emptyNote" className="ms-1" /> : null}
        </dt>
        <dd className="text-ink">
          {keys.openalex_key_set ? (
            <DecisionBadge role="include">{d("plan.limits.mailto.set")}</DecisionBadge>
          ) : (
            <DecisionBadge role="unclear">
              <bdi>{t("explore.keys.openalex.unset")}</bdi>
            </DecisionBadge>
          )}
        </dd>
      </div>
      <div data-s2-key-set={keys.s2_key_set ? "true" : "false"}>
        <dt className="text-ink-muted">
          {d("s2Key.title")}
          <Hint locale={locale} label={d("s2Key.title")} text={d("plan.limits.s2Key.help")} textKey="plan.limits.s2Key.help" className="ms-1" />
        </dt>
        <dd className="text-ink">{keys.s2_key_set ? <DecisionBadge role="unclear">{d("plan.limits.s2Key.set")}</DecisionBadge> : t("explore.keys.s2.unset")}</dd>
      </div>
    </dl>
  );
}

/** The sentence the screen owns for a refused key, chosen from the leg's own code and note. */
function refusedLine(locale: Locale, leg: ReconLeg): string | null {
  const t = inceptionT(locale);
  if (leg.error_code !== "PROVIDER_REFUSED") return null;
  if (leg.provider === "openalex") return t("explore.legs.refused.openalex");
  if (leg.provider === "semanticscholar" && leg.notes.some((n) => n.includes("SCHOLAR_S2_KEY"))) return t("explore.legs.refused.s2");
  return null;
}

/**
 * One row per database: name, the result in words, fetched of reported, the reason and the notes verbatim.
 * With `shorten`, a database that found nothing gives the shorten advice when the engine flags its leg
 * (H-provenance-s2) and another database found papers. Off where the screen gives it once.
 */
export function LegsList({ locale, legs, shorten = false }: Readonly<{ locale: Locale; legs: ReconLeg[]; shorten?: boolean }>) {
  const t = inceptionT(locale);
  // When no database found anything, the search card gives the advice once, not once per database.
  const someFound = legs.some((l) => (l.fetched ?? 0) > 0);
  return (
    <ul className="mt-3 space-y-3" data-legs>
      {legs.map((leg) => {
        const failed = leg.status === "failed";
        // "0 results" only when the database answered, nothing was fetched and it
        // reported no papers (0 or no total); a reported total keeps "answered" (spec 02, M10a).
        const none = leg.status === "ok" && !leg.fetched && !leg.reported_total;
        const special = refusedLine(locale, leg);
        const total = leg.reported_total == null ? null : leg.cap_hit ? t("explore.legs.atLeast", { n: String(leg.reported_total) }) : String(leg.reported_total);
        return (
          <li key={leg.provider} className="border-t border-rule pt-3 text-sm" data-leg={leg.provider} data-leg-status={leg.status}>
            <dl className="grid gap-x-4 gap-y-1 sm:grid-cols-[10rem_1fr]">
              <dt className="text-ink-muted">{t("explore.legs.col.provider")}</dt>
              <dd className="font-medium text-ink">{providerLabel(locale, leg.provider)}</dd>
              <dt className="text-ink-muted">{t("explore.legs.col.result")}</dt>
              <dd>
                {failed ? (
                  <DecisionBadge role="blocked">{t("explore.legs.failed")}</DecisionBadge>
                ) : none ? (
                  <DecisionBadge role="unclear">{t("explore.legs.zero")}</DecisionBadge>
                ) : leg.status === "ok" ? (
                  <DecisionBadge role="include">{t("explore.legs.ok")}</DecisionBadge>
                ) : (
                  <span dir="ltr">{leg.status}</span>
                )}
              </dd>
              {!failed ? (
                <>
                  <dt className="text-ink-muted">{t("explore.legs.col.fetched")}</dt>
                  <dd className="text-ink" data-fetched>
                    {total == null ? String(leg.fetched ?? 0) : t("explore.legs.fetchedOf", { fetched: String(leg.fetched ?? 0), total })}
                  </dd>
                  {shorten && none && leg.shorten === true && someFound ? (
                    <dd className="text-ink sm:col-start-2" data-leg-shorten>
                      {t("explore.legs.shorten")}
                    </dd>
                  ) : null}
                </>
              ) : null}
              {leg.executed_query ? (
                <>
                  <dt className="text-ink-muted">{t("explore.legs.col.query")}</dt>
                  <dd className="min-w-0" data-executed-query>
                    <DataCell>{leg.executed_query}</DataCell>
                  </dd>
                </>
              ) : null}
              {failed ? (
                <>
                  <dt className="text-ink-muted">{t("explore.legs.col.reason")}</dt>
                  <dd className="min-w-0 text-ink">
                    {special ? <p data-refused-line>{special}</p> : null}
                    {leg.error ? (
                      <p className="font-mono text-[0.8125rem] [overflow-wrap:anywhere]" dir="ltr">
                        {leg.error}
                      </p>
                    ) : null}
                    {leg.error_code ? (
                      <details className="text-xs">
                        <summary className="min-h-11 cursor-pointer rounded-sm py-3 leading-5 text-ink-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">
                          {DETAILS_LABEL[locale]}
                        </summary>
                        <p className="font-mono" dir="ltr" data-leg-code>
                          {leg.error_code}
                        </p>
                      </details>
                    ) : null}
                  </dd>
                </>
              ) : null}
            </dl>
            {leg.notes.length ? (
              <ul className="mt-1 space-y-1 text-xs text-ink-muted" data-leg-notes>
                {leg.notes.map((note) => (
                  <li key={note}>
                    <bdi dir="ltr">{note}</bdi>
                  </li>
                ))}
              </ul>
            ) : null}
          </li>
        );
      })}
    </ul>
  );
}

/** The banner of a usable pool some databases did not answer (spec 02, Partial). */
export function PartialBanner({ locale, legs, action }: Readonly<{ locale: Locale; legs: ReconLeg[]; action?: ReactNode }>) {
  const t = inceptionT(locale);
  const failed = legs.filter((l) => l.status === "failed");
  return (
    <section role="status" aria-labelledby="partial-title" className="rounded-lg border border-unclear bg-leaf p-4" data-partial>
      <DecisionBadge role="unclear">{t("explore.pool.partial")}</DecisionBadge>
      <div className="mt-2 flex items-center gap-1">
        <h2 id="partial-title" className="font-semibold text-ink">
          {t("explore.partial.title")}
        </h2>
        <Hint locale={locale} label={t("explore.partial.title")} text={t("explore.legs.neverEmpty")} textKey="explore.legs.neverEmpty" />
      </div>
      <LegsList locale={locale} legs={failed} />
      <p className="mt-2 text-sm text-ink">{t("explore.partial.body")}</p>
      {action ? <div className="mt-3">{action}</div> : null}
    </section>
  );
}

/** "Searching", with one line per database as its `leg` event arrives. */
export function ProgressCard({
  locale,
  legs,
  lost,
  headingRef,
}: Readonly<{ locale: Locale; legs: LegProgress[]; lost: boolean; headingRef?: RefObject<HTMLHeadingElement | null> }>) {
  const t = inceptionT(locale);
  return (
    <section aria-busy="true" aria-labelledby="progress-title" className="rounded-lg border border-rule bg-leaf p-4" data-progress>
      <div className="flex items-center gap-1">
        <h2 id="progress-title" ref={headingRef} tabIndex={-1} className="font-semibold text-ink">
          {t("explore.progress.title")}
        </h2>
        <Hint locale={locale} label={t("explore.progress.title")} text={t("explore.progress.note")} textKey="explore.progress.note" />
      </div>
      <ul role="status" aria-live="polite" className="mt-2 space-y-1 text-sm text-ink">
        {legs.map((leg) => (
          <li key={leg.provider} data-progress-leg={leg.provider}>
            {t("explore.progress.leg", { provider: providerLabel(locale, leg.provider), fetched: String(leg.fetched) })}
          </li>
        ))}
      </ul>
      <div className="mt-2 space-y-2" aria-hidden="true">
        <div className="h-3 w-2/3 rounded-sm bg-rule" />
        <div className="h-3 w-1/2 rounded-sm bg-rule" />
      </div>
      {lost ? (
        <p className="mt-2 text-sm text-unclear" data-lost>
          {t("explore.progress.lost")}
        </p>
      ) : null}
    </section>
  );
}

/**
 * The warning before a search replaces the pool a direction was bound on
 * (specs 02 and 03). Focus starts on "Keep the current pool"; Escape keeps it;
 * nothing is sent until "Search again".
 */
export function RefreshWarning({
  locale,
  direction,
  date,
  onGo,
  onKeep,
  goDisabled = false,
  goDescribedBy,
}: Readonly<{
  locale: Locale;
  direction: string;
  date: string;
  onGo: () => void;
  onKeep: () => void;
  /** The caller's own check (Explore: a database ticked, the query not too long); the reason is named by id. */
  goDisabled?: boolean;
  goDescribedBy?: string;
}>) {
  const t = inceptionT(locale);
  const keep = useRef<HTMLButtonElement>(null);
  useEffect(() => keep.current?.focus(), []);
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40 p-4">
      <div
        role="alertdialog"
        aria-modal="true"
        aria-labelledby="refresh-warn-title"
        aria-describedby="refresh-warn-body"
        className="w-full max-w-lg rounded-lg border border-rule bg-paper p-5"
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            event.preventDefault();
            onKeep();
          }
        }}
        data-refresh-warning
      >
        <h2 id="refresh-warn-title" className="font-semibold text-ink">
          {t("explore.refreshWarn.title")}
        </h2>
        <p id="refresh-warn-body" className="mt-2 text-sm text-ink">
          <bdi>{t("explore.refreshWarn.body", { direction, date })}</bdi>
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Button ref={keep} onClick={onKeep}>
            {t("explore.refreshWarn.keep")}
          </Button>
          <Button onClick={onGo} disabled={goDisabled} aria-describedby={goDisabled ? goDescribedBy : undefined} data-warn-go>
            {t("explore.refreshWarn.go")}
          </Button>
        </div>
      </div>
    </div>
  );
}

/** A DOI as a link to its resolver page, named by the paper and warning about the new tab. */
export function DoiLink({ locale, doi, title }: Readonly<{ locale: Locale; doi: string; title?: string | null }>) {
  const t = inceptionT(locale);
  return (
    <a
      href={`https://doi.org/${doi}`}
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`${title?.trim() ? t("explore.papers.link", { title: title.trim(), doi }) : t("explore.papers.linkDoi", { doi })} · ${t("explore.papers.newTab")}`}
      className="inline-flex min-h-11 items-center text-brand underline"
      data-doi={doi}
    >
      <DataCell>{doi}</DataCell>
    </a>
  );
}

/** The short form of a fingerprint (`sha256:` and 12 characters), as identity of what is on screen. */
export function shortFingerprint(fp: string | null | undefined): string {
  if (!fp) return "";
  return fp.startsWith("sha256:") ? fp.slice(0, 19) : fp.slice(0, 12);
}

export { stamp };
