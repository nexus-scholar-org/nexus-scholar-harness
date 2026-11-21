"use client";

import { useEffect, useRef, useState } from "react";

import type { Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge, RecommendedBadge } from "@/components/ui/base";
import { guidanceT } from "@/lib/guidance-copy";
import { DiscoveryRefusal, LINK, refusalOf, stamp, type Refusal } from "@/components/discovery-frame";
import { postEstimate, type Estimate, type EstimateRequest, type EstimateRow } from "@/lib/discovery-api";
import { discoveryT, providerName, type DiscoveryCopyKey } from "@/lib/discovery-copy";
import { stateCopy } from "@/lib/screening-states";

/**
 * The size estimate before a harvest (M10b Part D; spec `docs/ux/phase1-discovery/final/01-plan.md`
 * "Size estimate (M10b)", and `03-harvest.md` for the Harvest copy of the card).
 *
 * Nothing is counted on load or on a timer: the researcher presses "Count what the databases
 * hold", which sends `POST /discovery/estimate` (count-only requests; the engine writes nothing).
 * Every figure is a field of the answer; the card prints them and computes none. The
 * recommendation never acts: on Plan it is a link to Harvest with the cap in the address, on
 * Harvest it fills the cap field. Start stays a separate click.
 */

const NOT_ASKED = ["not_selected", "off_by_default"];
/** The engine on this computer did not answer: the last estimate stays "As of" its time, and Try again counts again. */
const UNREACHABLE = ["ENGINE_UNREACHABLE", "CONSOLE_UNREACHABLE", "CONSOLE_TIMEOUT"];
const LEG_CODES = ["PROVIDER_RATE_LIMITED", "PROVIDER_TIMEOUT", "PROVIDER_UNAVAILABLE", "PROVIDER_REFUSED"];

export interface EstimateCardProps {
  locale: Locale;
  origin: string;
  /** The plan's current protocol fingerprint: an estimate counted for another one shows no figure. */
  fingerprint: string;
  /** The `providers` a run would be sent, or `null` when it sends none (the protocol's list). */
  providers: string[] | null;
  /** Harvest: the cap field's whole number, sent as a what-if; `null` when the field is empty or not a number. */
  cap?: number | null;
  /** Plan: the link a cap recommendation follows to Harvest. */
  harvestHref?: (cap: number) => string;
  /** Harvest: put the recommended cap in the cap field (nothing is sent). */
  onUseCap?: (cap: number) => void;
  /** The link to inception for "narrow" and "state a planned number". */
  inceptionHref: string;
  /** M11a part D: Plan's "Change the search"; the narrow and one-database advice links there (question 7). */
  searchHref?: string;
  /** On Plan itself: open the section instead of following the link (a same-page anchor may already be set). */
  onSearch?: () => void;
}

function rowReason(locale: Locale, row: EstimateRow): string {
  const t = discoveryT(locale);
  if (row.status === "not_countable") return t("estimate.row.notCountable");
  if (row.error_code && LEG_CODES.includes(row.error_code)) return t(`harvest.leg.code.${row.error_code}` as DiscoveryCopyKey);
  return row.error ?? row.status;
}

function EstimateRowView({ locale, row, cap }: Readonly<{ locale: Locale; row: EstimateRow; cap: number }>) {
  const t = discoveryT(locale);
  const name = providerName(row.name);
  const counted = row.fetch_estimate !== null && row.reported_total !== null;
  return (
    <li className="border-t border-rule pt-3" data-estimate-row={row.name} data-status={row.status}>
      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
        <span className="font-semibold text-ink">{name}</span>
        {counted ? (
          <>
            <span className="text-sm text-ink" data-found>
              {t("estimate.row.found", { n: row.reported_total! })}
            </span>
            <span className="text-sm text-ink" data-fetch>
              {row.fetch_is_upper_bound ? t("estimate.row.fetchUpTo", { n: row.fetch_estimate! }) : t("estimate.row.fetch", { n: row.fetch_estimate! })}
            </span>
            {row.cap_binds ? (
              <DecisionBadge role="unclear">{t("estimate.row.cut")}</DecisionBadge>
            ) : (
              <DecisionBadge role="include">{t("estimate.row.all")}</DecisionBadge>
            )}
          </>
        ) : (
          <DecisionBadge role="unclear">{t("estimate.row.notCounted", { reason: rowReason(locale, row) })}</DecisionBadge>
        )}
      </div>
      {counted ? (
        <p className="mt-1 text-xs text-ink-muted" data-cap-line>
          {row.cap_binds
            ? t("estimate.row.cutBody", { name, found: row.reported_total!, cap, rest: row.not_fetched ?? "" })
            : t("estimate.row.fits", { name, found: row.reported_total!, cap })}
          {row.cap_binds ? ` ${t("estimate.cap.lower")}` : ""}
        </p>
      ) : null}
      {row.status === "from_recall_check" ? <p className="mt-1 text-xs text-ink-muted">{t("estimate.row.recall")}</p> : null}
      {row.fetch_is_upper_bound ? <p className="mt-1 text-xs text-ink-muted">{t("estimate.row.arxiv")}</p> : null}
      {row.status === "failed" && row.error ? (
        <details className="mt-1 text-xs">
          <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-ink-muted">{t("estimate.row.details")}</summary>
          <p className="text-ink" data-row-error>
            {row.error_code ? <DataCell>{row.error_code}</DataCell> : null} <bdi dir="ltr">{row.error}</bdi>
          </p>
        </details>
      ) : null}
    </li>
  );
}

/** Where narrowing the query is done: Plan's "Change the search" when the page gives it, else inception. */
function NarrowLink({ locale, inceptionHref, searchHref, onSearch }: Readonly<{ locale: Locale; inceptionHref: string; searchHref?: string; onSearch?: () => void }>) {
  const t = discoveryT(locale);
  return (
    <a
      className={LINK}
      href={searchHref ?? inceptionHref}
      onClick={
        searchHref && onSearch
          ? (event) => {
              event.preventDefault();
              onSearch();
            }
          : undefined
      }
      data-estimate-narrow
    >
      {searchHref ? t("plan.search.open") : t("amend.link")}
    </a>
  );
}

export function EstimateCard({ locale, origin, fingerprint, providers, cap = null, harvestHref, onUseCap, inceptionHref, searchHref, onSearch }: Readonly<EstimateCardProps>) {
  const t = discoveryT(locale);
  const [estimate, setEstimate] = useState<Estimate | null>(null);
  const [counting, setCounting] = useState(false);
  const [refusal, setRefusal] = useState<Refusal | null>(null);
  const [paceText, setPaceText] = useState("");
  const [paceInvalid, setPaceInvalid] = useState(false);
  const [announce, setAnnounce] = useState("");
  // What the shown estimate was asked with: "Count again" refreshes past a recall check only when nothing changed.
  const shownWith = useRef<{ cap: number | null; pace: number | null } | null>(null);
  // The pace is sent only once the researcher edits it; until then the field shows the engine's.
  const paceEdited = useRef(false);
  const heading = useRef<HTMLHeadingElement>(null);
  const sequence = useRef(0);
  // A different choice of databases makes a shown estimate out of date: it is cleared, never shown as current.
  const providersKey = providers ? providers.join(",") : "";
  useEffect(() => {
    sequence.current++;
    setEstimate(null);
    setRefusal(null);
    setCounting(false);
    setAnnounce("");
  }, [providersKey]);

  const count = async (fromRecall = false) => {
    const body: EstimateRequest = {};
    if (providers) body.providers = providers;
    if (cap !== null && cap !== undefined) body.cap = cap;
    const pace = paceText.trim();
    if (paceEdited.current) {
      if (!/^\d+$/.test(pace)) {
        setPaceInvalid(true);
        return;
      }
      body.pace_seconds = Number(pace);
    }
    const asked = { cap: body.cap ?? null, pace: body.pace_seconds ?? null };
    // A what-if (another cap or pace) is answered from the cached counts; only a plain "Count again"
    // after an estimate built from a recall check asks the databases themselves (review finding 4).
    if (fromRecall && shownWith.current && shownWith.current.cap === asked.cap && shownWith.current.pace === asked.pace) body.refresh = true;
    const id = ++sequence.current;
    setCounting(true);
    setRefusal(null);
    setPaceInvalid(false);
    try {
      const answer = await postEstimate(origin, body);
      if (id !== sequence.current) return;
      setEstimate(answer);
      shownWith.current = asked;
      if (!paceEdited.current) setPaceText(String(answer.effort.pace_seconds));
      const works = answer.estimate.works;
      setAnnounce(
        works.high === null ? t("estimate.announce.atLeast", { low: works.low ?? "" }) : t("estimate.announce", { low: works.low ?? "", high: works.high }),
      );
    } catch (error) {
      if (id !== sequence.current) return;
      const next = refusalOf(error);
      if (next.code === "PACE_INVALID") setPaceInvalid(true);
      setRefusal(next);
      heading.current?.focus();
    } finally {
      if (id === sequence.current) setCounting(false);
    }
  };

  const stale = !!estimate && estimate.protocol_fingerprint !== fingerprint;
  const rows = estimate ? estimate.providers.filter((row) => !NOT_ASKED.includes(row.status)) : [];
  const notCounted = rows.filter((row) => row.fetch_estimate === null).map((row) => providerName(row.name));
  const comma = locale === "ar" ? "، " : ", ";
  const works = estimate?.estimate.works;
  const records = estimate?.estimate.records;
  const hours = estimate?.effort.hours;
  const rec = estimate?.recommendation;
  const warn = estimate?.warn;
  const planned = warn?.limit?.source === "planned";

  return (
    <section aria-labelledby="estimate-title" aria-busy={counting || undefined} className="rounded-lg border border-dashed border-ink-muted bg-leaf p-5" data-estimate>
      <h2 id="estimate-title" ref={heading} tabIndex={-1} className="font-semibold text-ink">
        {t("estimate.title")}
      </h2>
      <p className="mt-1 text-xs text-ink-muted">{t("estimate.badge")}</p>

      {refusal ? (
        <div className="mt-3">
          <DiscoveryRefusal locale={locale} refusal={refusal} origin={origin} onRetry={UNREACHABLE.includes(refusal.code) ? () => void count() : undefined} />
        </div>
      ) : null}

      {!estimate ? (
        <p className="mt-3 text-sm text-ink" data-estimate-empty>
          {t("estimate.empty")}
        </p>
      ) : stale ? (
        <p role="status" className="mt-3 text-sm text-ink" data-estimate-changed>
          {t("estimate.changed")}
        </p>
      ) : (
        <div className={`mt-3 space-y-3 ${counting ? "opacity-60" : ""}`.trim()} data-estimate-figures>
          {counting || refusal ? (
            <p className="text-xs text-ink-muted" data-estimate-as-of>
              {t("estimate.asOf", { time: stamp(estimate.counted_at) })}
            </p>
          ) : null}
          {estimate.recall_check ? (
            <p className="text-sm text-ink" data-estimate-from-recall>
              {t("estimate.fromRecall", { date: stamp(estimate.recall_check.checked_at ?? estimate.counted_at) })}
            </p>
          ) : null}
          {warn && warn.level !== "none" ? (
            <div role="status" className="space-y-1 rounded-md bg-unclear-soft p-3 text-sm" data-estimate-warn={warn.level}>
              <p className="font-semibold text-unclear">
                {warn.level === "warning"
                  ? t("estimate.warn.warning", { low: works?.low ?? "", threshold: warn.threshold_works })
                  : works?.high === null
                    ? t("estimate.warn.unbounded", { names: notCounted.join(comma) })
                    : t("estimate.warn.note", { high: works?.high ?? "", threshold: warn.threshold_works })}
              </p>
              <p className="text-ink">
                {planned
                  ? t("estimate.warn.why.planned", { low: works?.low ?? "", threshold: warn.threshold_works })
                  : t("estimate.warn.why.general", { low: works?.low ?? "", threshold: warn.threshold_works })}
              </p>
              {!planned ? (
                <a className={LINK} href={inceptionHref} data-estimate-set-plan>
                  {t("estimate.warn.setPlan")}
                </a>
              ) : null}
            </div>
          ) : null}
          {rec && rec.kind === "cap" && rec.cap !== null ? (
            <div className="space-y-2 rounded-md border border-rule bg-paper p-3 text-sm" data-estimate-rec="cap">
              {/* M10d (03-guidance rule 3): the suggested cap is marked; the field is never filled until the researcher uses it. */}
              <p>
                <RecommendedBadge locale={locale} source={guidanceT(locale)("guidance.recommended.source.estimate")} />
              </p>
              <p className="text-ink">{t("estimate.rec.cap", { cap: rec.cap, high: rec.expected_works?.high ?? "", k: rec.cuts ?? "" })}</p>
              <p className="text-xs text-ink-muted">{t("estimate.cap.order")}</p>
              {harvestHref ? (
                <a className={LINK} href={harvestHref(rec.cap)} data-estimate-use-cap>
                  {t("estimate.rec.cap.apply", { cap: rec.cap })}
                </a>
              ) : onUseCap ? (
                <Button onClick={() => onUseCap(rec.cap!)} data-estimate-use-cap>
                  {t("estimate.rec.cap.apply", { cap: rec.cap })}
                </Button>
              ) : null}
              <p className="text-xs text-ink-muted">{t("estimate.rec.cap.help")}</p>
              <details className="text-xs">
                <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-ink-muted">{t("estimate.rec.why")}</summary>
                <p className="text-ink">
                  {planned
                    ? t("estimate.warn.why.planned", { low: works?.low ?? "", threshold: warn?.threshold_works ?? "" })
                    : t("estimate.warn.why.general", { low: works?.low ?? "", threshold: warn?.threshold_works ?? "" })}
                </p>
              </details>
            </div>
          ) : rec && rec.kind === "one_database" && rec.provider ? (
            <div className="space-y-2 rounded-md border border-rule bg-paper p-3 text-sm" data-estimate-rec="one_database">
              {/* H-run-small-fixes (finding 10): no cap is offered when one database is the size. */}
              <p className="text-ink">
                {t("estimate.rec.oneDatabase", {
                  name: providerName(rec.provider),
                  n: rec.provider_total ?? "",
                  total: (rec.provider_total ?? 0) + (rec.others_total ?? 0),
                })}
              </p>
              <NarrowLink locale={locale} inceptionHref={inceptionHref} searchHref={searchHref} onSearch={onSearch} />
            </div>
          ) : rec && rec.kind === "narrow" ? (
            <div className="space-y-2 rounded-md border border-rule bg-paper p-3 text-sm" data-estimate-rec="narrow">
              <p className="text-ink">{t("estimate.rec.narrow")}</p>
              <NarrowLink locale={locale} inceptionHref={inceptionHref} searchHref={searchHref} onSearch={onSearch} />
            </div>
          ) : null}
          <ul className="space-y-3" data-estimate-rows>
            {rows.map((row) => (
              <EstimateRowView key={row.name} locale={locale} row={row} cap={estimate.cap.value} />
            ))}
          </ul>
          <div className="space-y-2 border-t border-rule pt-3 text-sm text-ink">
            <div data-estimate-records>
              {records?.high === null || records?.high === undefined
                ? t("estimate.records.atLeast", { low: records?.low ?? "" })
                : t("estimate.records", { high: records.high })}
            </div>
            <div data-estimate-works>
              <p>
                {works?.high === null || works?.high === undefined
                  ? t("estimate.works.atLeast", { low: works?.low ?? "" })
                  : t("estimate.works", { low: works.low ?? "", high: works.high })}
              </p>
              <p className="text-xs text-ink-muted">{t("estimate.works.assumption")}</p>
            </div>
            <div data-estimate-effort>
              <p>
                {hours?.high === null || hours?.high === undefined
                  ? t("estimate.effort.atLeast", { low: hours?.low ?? "" })
                  : t("estimate.effort", { low: hours.low ?? "", high: hours.high })}
              </p>
              <p className="text-xs text-ink-muted">{t("estimate.effort.basis", { pace: estimate.effort.pace_seconds })}</p>
            </div>
            <div>
              <label className="block text-xs text-ink-muted" htmlFor="estimate-pace">
                {t("estimate.pace.label")}
              </label>
              <input
                id="estimate-pace"
                inputMode="numeric"
                value={paceText}
                onChange={(e) => {
                  paceEdited.current = true;
                  setPaceText(e.target.value);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    void count();
                  }
                }}
                aria-invalid={paceInvalid || undefined}
                aria-describedby="estimate-pace-help"
                className="mt-1 min-h-11 w-28 rounded-md border border-rule bg-paper px-3 text-ink focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus"
                data-estimate-pace
              />
              {paceInvalid && !refusal ? (
                <p role="alert" className="mt-1 text-xs font-semibold text-unclear" data-estimate-pace-invalid>
                  {stateCopy(locale, "PACE_INVALID").title}
                </p>
              ) : null}
              <p id="estimate-pace-help" className="mt-1 text-xs text-ink-muted">
                {t("estimate.pace.help")}
              </p>
            </div>
            <p className="text-xs text-ink-muted" data-estimate-cap={estimate.cap.source}>
              {estimate.cap.source === "protocol"
                ? t("estimate.cap.protocol", { value: estimate.cap.value })
                : estimate.cap.source === "run_override"
                  ? t("estimate.cap.override", { value: estimate.cap.value })
                  : t("estimate.cap.engine", { value: estimate.cap.value })}
            </p>
            <p className="text-xs text-ink-muted" data-estimate-counted>
              {t("estimate.counted", { time: stamp(estimate.counted_at) })}
              {estimate.served_from_cache ? ` · ${t("estimate.cached")}` : ""}
            </p>
          </div>
        </div>
      )}

      <div className="mt-4 flex flex-wrap items-center gap-3">
        <Button onClick={() => void count(!!estimate?.recall_check && !stale)} disabled={counting} aria-busy={counting || undefined} data-estimate-count>
          {counting ? t("estimate.counting") : estimate ? t("estimate.again") : t("estimate.count")}
        </Button>
      </div>
      <p aria-live="polite" className="sr-only" data-estimate-announce>
        {counting ? t("estimate.counting") : announce}
      </p>
    </section>
  );
}
