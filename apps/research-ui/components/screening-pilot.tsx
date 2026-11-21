"use client";

import { useCallback, useEffect, useMemo, useRef, useState, type ReactNode } from "react";

import { formatNumber, type Locale } from "@/i18n";
import { Button, DataCell, DecisionBadge, Hint, PRIMARY_LINK } from "@/components/ui/base";
import { DrawPilot, triageHref } from "@/components/screening-pilot-card";
import { PILOT_COPY, type PilotKey } from "@/components/screening-pilot-copy";
import { CHEAPEST_ANTHROPIC_MODEL, LISTED_ANTHROPIC_MODELS } from "@/components/screening-proposals";
import { ScreeningSteps, StateCard, stepHref } from "@/components/screening-state-card";
import { isScreeningApiError } from "@/lib/screening-api";
import {
  amendCriteria,
  cancelRun,
  closePilot,
  estimateRun,
  getCriteria,
  getPilotResult,
  getProposalSetup,
  getRecord,
  getRun,
  getSummary,
  startCalibration,
  type AmendmentAnswer,
  type AmendmentOp,
  type AmendmentRequest,
  type CriteriaSide,
  type CriteriaView,
  type Observation,
  type Outcome,
  type PilotCriterionRow,
  type PilotRecord,
  type PilotResult,
  type ProposalSetup,
  type Provider,
  type RecordDetail,
  type RunEstimate,
  type RunView,
  type Share,
  type Summary,
} from "@/lib/screening-v1";

/**
 * The pilot result (spec 13, state C) with its three dialogs: end the pilot, revise a criterion
 * (state D) and check the agent on the pilot. Every figure is a field of the engine's answer; the
 * browser counts nothing, applies no threshold and derives no outcome. The agent shows per
 * criterion only, as counts, never per record (answer 11).
 */

const OUTCOMES: Outcome[] = ["INCLUDE", "MAYBE", "EXCLUDE"];
const ROLE = { INCLUDE: "include", MAYBE: "unclear", EXCLUDE: "exclude" } as const;
const WORD: Record<Outcome, PilotKey> = { INCLUDE: "include", MAYBE: "unclear", EXCLUDE: "exclude" };
const OPS: AmendmentOp[] = ["reword", "split", "merge", "remove", "add", "reason_category"];
const AGENT_KINDS = new Set(["hard_to_judge", "fire_together", "mirrored_pair", "read_differently"]);
const FINISHED = new Set(["completed", "stopped", "cancelled", "failed"]);
const PAGE = 25;
const POLL_MS = 2000;

function consoleOrigin(): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get("console") ?? "";
}

function pilotFromUrl(): string | null {
  if (typeof window === "undefined") return null;
  return new URLSearchParams(window.location.search).get("id");
}

function codeOf(error: unknown): { code: string; message: string } {
  return isScreeningApiError(error) ? { code: error.code, message: error.serverMessage } : { code: "ENGINE_UNREACHABLE", message: "" };
}

function fill(template: string, values: Readonly<Record<string, string | number>> = {}): string {
  return template.replace(/\{(\w+)\}/g, (_, k: string) => {
    if (!(k in values)) throw new Error(`pilot copy needs {${k}}`);
    return String(values[k]);
  });
}

function usd(locale: Locale, value: number): string {
  return new Intl.NumberFormat(locale === "ar" ? "ar-u-nu-latn" : locale, { style: "currency", currency: "USD", maximumFractionDigits: value < 1 ? 4 : 2 }).format(value);
}

/** The pilot's number for its column label ("pilot_002" is Pilot 2); the id itself if it has none. */
function pilotNumber(pilotId: string): string {
  const match = pilotId.match(/_(\d+)$/);
  return match ? String(Number(match[1])) : pilotId;
}

type Loaded = { result: PilotResult; summary: Summary; criteria: CriteriaView; setup: ProposalSetup | null };
type State =
  | { status: "loading" }
  | { status: "error"; code: string; message: string }
  | { status: "none"; summary: Summary }
  | { status: "ready"; data: Loaded };

export function ScreeningPilot({ locale }: Readonly<{ locale: Locale }>) {
  const t = useCallback((key: PilotKey, values?: Readonly<Record<string, string | number>>) => fill(PILOT_COPY[locale][key], values), [locale]);
  const n = useCallback((value: number) => formatNumber(locale, value), [locale]);
  const origin = useMemo(consoleOrigin, []);
  const [state, setState] = useState<State>({ status: "loading" });
  const [dialog, setDialog] = useState<null | { kind: "end" } | { kind: "revise"; ids: string[] } | { kind: "check" } | { kind: "record"; record: PilotRecord }>(null);
  const [announce, setAnnounce] = useState("");
  const [estimate, setEstimate] = useState<RunEstimate | null | "unknown">(null);
  const opener = useRef<HTMLElement | null>(null);
  const notice = useRef<HTMLParagraphElement>(null);

  const load = useCallback(async () => {
    try {
      const [summary, criteria, setup] = await Promise.all([getSummary(origin), getCriteria(origin), getProposalSetup(origin).catch(() => null)]);
      const id = pilotFromUrl() ?? summary.pilot?.pilot_id ?? null;
      if (!id) {
        setState({ status: "none", summary });
        return;
      }
      const result = await getPilotResult(origin, id);
      setState({ status: "ready", data: { result, summary, criteria, setup } });
    } catch (error) {
      setState({ status: "error", ...codeOf(error) });
    }
  }, [origin]);

  useEffect(() => {
    void load();
  }, [load]);

  const data = state.status === "ready" ? state.data : null;
  const result = data?.result ?? null;
  const setup = data?.setup ?? null;
  const provider: Provider = setup?.last_model?.provider ?? "anthropic";
  const keyed = setup?.providers.find((p) => p.provider === provider)?.key;
  const hasKey = keyed !== undefined && keyed !== "none";
  const decidedIds = useMemo(() => result?.records.map((r) => r.study_id) ?? [], [result]);
  const defaultModel = setup?.last_model?.model || CHEAPEST_ANTHROPIC_MODEL;

  // The estimate named in the "not computed" line; a dry estimate sends nothing to a provider.
  useEffect(() => {
    if (!setup || decidedIds.length === 0) return;
    let live = true;
    estimateRun(origin, { provider, model: defaultModel, effort: setup.task.effort, scope: { study_ids: decidedIds }, cost_ceiling_usd: null })
      .then((e) => live && setEstimate(e))
      .catch(() => live && setEstimate("unknown"));
    return () => {
      live = false;
    };
  }, [origin, setup, provider, defaultModel, decidedIds]);

  const open = (next: NonNullable<typeof dialog>) => {
    opener.current = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    setDialog(next);
  };
  const close = useCallback(() => {
    setDialog(null);
    window.setTimeout(() => opener.current?.focus(), 0);
  }, []);

  // Esc closes any dialog without writing.
  useEffect(() => {
    if (!dialog) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && close();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [dialog, close]);

  const primaryHref = result ? (result.open ? triageHref(locale, "pilot", origin) : triageHref(locale, "needs_you", origin)) : null;

  // Ctrl+Enter runs the screen's primary action when no dialog is open.
  useEffect(() => {
    if (!primaryHref || dialog) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Enter" && e.ctrlKey) window.location.assign(primaryHref);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [primaryHref, dialog]);

  const body = (() => {
    if (state.status === "loading") return <p className="text-ink-muted" role="status">{t("loading")}</p>;
    if (state.status === "error") return <StateCard pageHeading locale={locale} code={state.code} message={state.message} consoleOrigin={origin} onRetry={() => void load()} />;
    if (state.status === "none") {
      return (
        <div className="space-y-6">
          <Header t={t} title={t("noPilot")} />
          <section className="rounded-lg border border-rule bg-leaf p-5">
            <DrawPilot locale={locale} origin={origin} corpus={state.summary.total} onDrawn={() => window.location.assign(triageHref(locale, "pilot", origin))} />
          </section>
        </div>
      );
    }
    const { result: r, summary, criteria } = state.data;
    const soFar = r.open;
    const title = r.open ? t("titleOpen", { k: n(r.decided), n: n(r.n) }) : r.closed_reason === "ended" ? t("titleEnded", { k: n(r.decided), n: n(r.n) }) : t("titleDone", { k: n(r.decided), n: n(r.n) });
    const fixed = criteria.batch_approved || !criteria.can_amend;
    const changed = Boolean(summary.protocol_changed);
    const waiting = summary.recheck ?? 0;
    const canCheck = hasKey && r.decided > 0 && (!r.open || r.decided === r.n);
    const revision = [...criteria.amendments].reverse().find((a) => a.pilot_id === r.pilot_id) ?? null;
    const estimateWords =
      estimate === null || estimate === "unknown" || estimate.cost_usd === null ? t("estimateUnknown") : t("estimateAbout", { cost: usd(locale, estimate.cost_usd) });
    const restIsBrand = !r.open && waiting === 0;

    return (
      <div className="space-y-6">
        <Header t={t} title={title} />
        <p className="text-ink" data-not-counted>{t("notCounted")}</p>

        {changed ? (
          <p role="alert" className="rounded-md bg-blocked-soft px-4 py-2 text-blocked">
            {t("protocolChanged")} ·{" "}
            <a className="underline" href={stepHref(locale, "prepare", origin)}>
              {t("rebind")}
            </a>
          </p>
        ) : null}

        {revision ? (
          <p ref={notice} tabIndex={-1} className="rounded-md border border-rule bg-leaf px-4 py-2 text-ink" data-revision-notice>
            {revision.shown_again.total > 0
              ? t("revised", { v: n(revision.criteria_version_after), date: new Date(revision.amended_at).toLocaleDateString(locale), n: n(revision.shown_again.total) })
              : t("revisedNone", { v: n(revision.criteria_version_after), date: new Date(revision.amended_at).toLocaleDateString(locale) })}{" "}
            {revision.shown_again.total > 0 ? (
              <a className="text-brand underline" href={triageHref(locale, "recheck", origin)}>
                {t("openThem")}
              </a>
            ) : null}
          </p>
        ) : null}

        <div className="flex flex-wrap gap-6">
          <div className="min-w-0 flex-[999_1_640px] space-y-6">
            <Counts t={t} n={n} result={r} soFar={soFar} />
            <CriteriaTable t={t} n={n} result={r} criteria={criteria} soFar={soFar} />
            <p className="text-sm text-ink-muted" data-small-sample>{t("smallSample", { n: n(r.decided) })}</p>
            <Suggests
              t={t}
              n={n}
              result={r}
              estimate={estimateWords}
              canCheck={canCheck}
              canRevise={!fixed && !changed}
              onRevise={(ids) => open({ kind: "revise", ids })}
              onCheck={() => open({ kind: "check" })}
            />
            {setup?.earlier_wording_drafts && setup.earlier_wording_drafts.count > 0 ? (
              <p className="text-sm">
                <a className="text-brand underline" href={stepHref(locale, "proposals", origin)}>
                  {t("earlierDrafts", { n: n(setup.earlier_wording_drafts.count) })}
                </a>
              </p>
            ) : null}
            <Records t={t} n={n} result={r} onOpen={(record) => open({ kind: "record", record })} />

            <section aria-label={t("details")} className="sticky bottom-0 space-y-2 rounded-lg border border-rule bg-paper p-4" data-action-bar>
              {waiting > 0 ? <p className="text-sm text-ink">{t("waiting", { n: n(waiting) })}</p> : null}
              {fixed ? <p className="text-sm text-ink" data-fixed>{t("fixed")}</p> : null}
              <div className="flex flex-wrap items-center gap-2">
                {r.open ? (
                  <a className={PRIMARY_LINK} data-variant="primary" href={triageHref(locale, "pilot", origin)}>
                    {t("actions.continue")}
                  </a>
                ) : (
                  <a
                    className={restIsBrand ? PRIMARY_LINK : "inline-flex min-h-11 items-center px-4 text-brand underline"}
                    data-variant={restIsBrand ? "primary" : "quiet"}
                    href={triageHref(locale, "needs_you", origin)}
                  >
                    {t("actions.rest")}
                  </a>
                )}
                {!fixed ? (
                  <Button disabled={changed} onClick={() => open({ kind: "revise", ids: [] })}>
                    {t("actions.revise")}
                  </Button>
                ) : null}
                {r.open && !fixed ? (
                  <Button disabled={changed} onClick={() => open({ kind: "end" })}>
                    {t("end.confirm")}
                  </Button>
                ) : null}
                {canCheck ? (
                  <span className="inline-flex items-center gap-1">
                    <Button disabled={changed} onClick={() => open({ kind: "check" })}>
                      {t("actions.check", { n: n(r.decided) })}
                    </Button>
                    <Hint locale={locale} label={t("actions.checkHint")} text={t("checkHint")} textKey="screening.pilot.checkHint" />
                  </span>
                ) : null}
              </div>
              {!r.open && !fixed && !changed ? (
                <MorePilot locale={locale} origin={origin} corpus={summary.total} label={(size) => t("actions.more", { n: n(size) })} />
              ) : null}
            </section>
          </div>

          <aside className="w-full flex-[1_1_280px] space-y-4">
            <details className="rounded-lg border border-rule bg-leaf p-4 text-sm" data-side-details>
              <summary className="min-h-11 cursor-pointer py-2 font-semibold text-ink">{t("side.title")}</summary>
              <dl className="space-y-2">
                <Pair label={t("side.pilot")} value={r.pilot_id} />
                <Pair label={t("side.seed")} value={String(r.seed)} />
                <Pair label={t("side.drawnAt")} value={r.drawn_at} />
                <Pair label={t("side.snapshot")} value={r.snapshot_id ?? "—"} />
                <Pair label={t("side.version")} value={String(r.criteria_version)} />
                <Pair label={t("side.fingerprint")} value={r.protocol_fingerprint} />
                {criteria.amendments.length > 0 ? <Pair label={t("side.amendments")} value={criteria.amendments.map((a) => a.amendment_id).join(", ")} /> : null}
              </dl>
            </details>
          </aside>
        </div>

        {dialog?.kind === "end" ? (
          <EndDialog
            t={t}
            n={n}
            result={r}
            origin={origin}
            locale={locale}
            onClose={close}
            onEnded={() => {
              setDialog(null);
              void load();
            }}
          />
        ) : null}
        {dialog?.kind === "revise" ? (
          <ReviseDialog
            t={t}
            n={n}
            locale={locale}
            origin={origin}
            criteria={criteria}
            preset={dialog.ids}
            onClose={close}
            onRecorded={(answer) => {
              setDialog(null);
              setAnnounce(t("revisedAnnounce", { v: n(answer.criteria_version_after) }));
              void load().then(() => window.setTimeout(() => notice.current?.focus(), 0));
            }}
          />
        ) : null}
        {dialog?.kind === "check" && setup ? (
          <CheckDialog t={t} n={n} locale={locale} origin={origin} result={r} setup={setup} provider={provider} initialModel={defaultModel} onClose={close} onDone={() => void load()} />
        ) : null}
        {dialog?.kind === "record" ? <RecordView t={t} n={n} locale={locale} origin={origin} record={dialog.record} onClose={close} /> : null}
      </div>
    );
  })();

  return (
    <div className="mx-auto max-w-7xl px-6 py-10 lg:px-8 lg:py-14">
      <ScreeningSteps locale={locale} consoleOrigin={origin} />
      {body}
      <p className="sr-only" aria-live="polite">
        {announce}
      </p>
    </div>
  );
}

type T = (key: PilotKey, values?: Readonly<Record<string, string | number>>) => string;
type N = (value: number) => string;

function Header({ t, title }: Readonly<{ t: T; title: string }>) {
  return (
    <header>
      <p className="text-xs font-semibold uppercase tracking-[0.05em] text-brand rtl:tracking-normal">{t("eyebrow")}</p>
      <h1 className="font-display mt-1 text-[1.75rem] leading-[2.25rem] text-ink">{title}</h1>
      <p className="mt-2 max-w-prose text-ink-muted">{t("lede")}</p>
    </header>
  );
}

function Pair({ label, value }: Readonly<{ label: string; value: string }>) {
  return (
    <div>
      <dt className="text-ink-muted">{label}</dt>
      <dd>
        <DataCell>{value}</DataCell>
      </dd>
    </div>
  );
}

function Counts({ t, n, result, soFar }: Readonly<{ t: T; n: N; result: PilotResult; soFar: boolean }>) {
  const of = (value: number) => (soFar ? t("ofSoFar", { n: n(value) }) : t("of", { n: n(value) }));
  const previous = result.previous;
  const tiles: { key: string; label: string; value: number; of: number; role?: Outcome; before?: { value: number; of: number } }[] = [
    { key: "decided", label: t("decided"), value: result.decided, of: result.n, before: previous ? { value: previous.decided, of: previous.n } : undefined },
    ...OUTCOMES.map((o) => ({
      key: o,
      label: t(WORD[o]),
      value: result.by_outcome[o],
      of: result.decided,
      role: o,
      before: previous ? { value: previous.by_outcome[o], of: previous.decided } : undefined,
    })),
  ];
  return (
    <section aria-labelledby="pilot-counts">
      <h2 id="pilot-counts" className="sr-only">
        {t("countsTitle")}
      </h2>
      <ul className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {tiles.map((tile) => (
          <li key={tile.key} className="rounded-lg border border-rule bg-leaf p-4" data-count={tile.key}>
            <p className="text-sm text-ink-muted">{tile.role ? <DecisionBadge role={ROLE[tile.role]}>{tile.label}</DecisionBadge> : tile.label}</p>
            <p className="mt-1 text-2xl text-ink tabular-nums">{n(tile.value)}</p>
            <p className="text-xs text-ink-muted">{tile.key === "decided" ? t("of", { n: n(tile.of) }) : of(tile.of)}</p>
            {tile.before && previous ? (
              <p className="mt-1 text-xs text-ink-muted" data-previous>
                {t("pilotLabel", { k: pilotNumber(previous.pilot_id) })}: {n(tile.before.value)} {t("of", { n: n(tile.before.of) })}
              </p>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  );
}

function shareText(t: T, n: N, share: Share, key: "cellExclusions" | "cellAnswered" | "cellOf"): string {
  return t(key, { k: n(share.count), n: n(share.of) });
}

function retiredLabel(t: T, n: N, id: string, criteria: CriteriaView): string {
  const amendment = criteria.amendments.find((a) => a.from.some((c) => c.id === id) && !a.to.some((c) => c.id === id));
  return amendment ? t("retiredIn", { v: n(amendment.criteria_version_after) }) : t("retired");
}

function CriteriaTable({ t, n, result, criteria, soFar }: Readonly<{ t: T; n: N; result: PilotResult; criteria: CriteriaView; soFar: boolean }>) {
  const rows = result.criteria;
  const previous = result.previous;
  const before = new Map((previous?.criteria ?? []).map((row) => [row.id, row]));
  const ids = [...rows.map((r) => r.id), ...(previous?.criteria ?? []).map((r) => r.id).filter((id) => !rows.some((r) => r.id === id))];
  const byId = new Map(rows.map((r) => [r.id, r]));
  const withChecklist = rows.some((r) => r.checklist_not_reported !== null);
  const withDrafts = rows.some((r) => r.draft_not_reported !== null || r.read_differently !== null);
  const source = rows.find((r) => r.read_differently)?.read_differently?.source ?? "implied";
  const readDiffNote = source === "answers" ? t("readDiffAnswers") : source === "mixed" ? t("readDiffMixed") : t("readDiffImplied");
  const versions = (list: number[]) => list.join(", ");
  const caption = previous
    ? t("compareCaption", { a: versions(previous.criteria_versions_decided), b: versions(result.criteria_versions_decided) })
    : result.criteria_versions_decided.length > 1
      ? t("mixedVersions")
      : null;
  const label = (row: PilotCriterionRow) => (row.text.length > 60 ? `${row.text.slice(0, 60)}…` : row.text);
  return (
    <section aria-labelledby="pilot-table" className="rounded-lg border border-rule bg-leaf p-5">
      <h2 id="pilot-table" className="font-semibold text-ink">
        {t("tableTitle")}
      </h2>
      <div className="mt-3 overflow-x-auto">
        <table className="w-full text-sm tabular-nums">
          {caption ? <caption className="pb-2 text-start text-ink-muted">{caption}</caption> : null}
          <thead>
            <tr className="text-ink-muted">
              <th scope="col" className="py-1 text-start font-normal">
                {t("criterion")}
              </th>
              {previous ? (
                <th scope="col" className="py-1 text-start font-normal">
                  {t("exclusions")} · {t("pilotLabel", { k: pilotNumber(previous.pilot_id) })}
                </th>
              ) : null}
              <th scope="col" className="py-1 text-start font-normal">
                {t("exclusions")}
                {previous ? ` · ${t("pilotLabel", { k: pilotNumber(result.pilot_id) })}` : ""}
              </th>
              {withChecklist ? (
                <th scope="col" className="py-1 text-start font-normal">
                  {t("checklistNotReported")}
                </th>
              ) : null}
              {withDrafts ? (
                <>
                  <th scope="col" className="border-x border-dashed border-ink-muted py-1 text-start font-normal" data-draft-column>
                    <span className="block text-xs">{t("draftLabel")}</span>
                    {t("draftNotReported")}
                  </th>
                  <th scope="col" className="border-e border-dashed border-ink-muted py-1 text-start font-normal" data-draft-column>
                    <span className="block text-xs">{t("draftLabel")}</span>
                    {t("readDifferently")}
                    <span className="block text-xs">{readDiffNote}</span>
                  </th>
                </>
              ) : null}
            </tr>
          </thead>
          <tbody>
            {ids.map((id) => {
              const row = byId.get(id) ?? null;
              const old = before.get(id) ?? null;
              const shown = row ?? old!;
              return (
                <tr key={id} className="border-t border-rule align-top" data-criterion={id}>
                  <th scope="row" className="py-2 text-start font-normal text-ink">
                    <DataCell>{id}</DataCell>{" "}
                    <span dir="auto">{label(shown)}</span>
                    {shown.retired || !row ? <span className="block text-xs text-ink-muted">{retiredLabel(t, n, id, criteria)}</span> : null}
                    {shown.text.length > 60 ? (
                      <details className="text-xs text-ink-muted">
                        <summary className="cursor-pointer">{t("fullWording")}</summary>
                        <span dir="auto">{shown.text}</span>
                      </details>
                    ) : null}
                  </th>
                  {previous ? <td className="py-2">{old ? shareText(t, n, old.exclusions, "cellExclusions") : "—"}</td> : null}
                  <td className="py-2" data-cell="exclusions">
                    {row ? shareText(t, n, row.exclusions, "cellExclusions") : "—"}
                    {row && soFar ? <span className="block text-xs text-ink-muted">{t("ofSoFar", { n: n(result.decided) })}</span> : null}
                  </td>
                  {withChecklist ? <td className="py-2" data-cell="checklist">{row?.checklist_not_reported ? shareText(t, n, row.checklist_not_reported, "cellAnswered") : "—"}</td> : null}
                  {withDrafts ? (
                    <>
                      <td className="border-x border-dashed border-ink-muted py-2" data-cell="draft">
                        {row?.draft_not_reported ? shareText(t, n, row.draft_not_reported, "cellOf") : "—"}
                      </td>
                      <td className="border-e border-dashed border-ink-muted py-2" data-cell="read-differently">
                        {row?.read_differently ? shareText(t, n, row.read_differently, "cellOf") : "—"}
                      </td>
                    </>
                  ) : null}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function observationText(t: T, n: N, o: Observation): string {
  const c = o.counts;
  const [a, b] = o.criteria;
  switch (o.kind) {
    case "many_unclear":
      return t("obs.many_unclear", { k: n(c.count ?? 0), n: n(c.of ?? 0) });
    case "does_most_work":
      return t("obs.does_most_work", { id: a, k: n(c.count ?? 0), n: n(c.of ?? 0) });
    case "never_used":
      return o.form === "full" ? t("obs.never_used.full", { id: a, k: n(c.of ?? 0) }) : t("obs.never_used", { id: a, k: n(c.of ?? 0), n: n(c.decided ?? 0) });
    case "hard_to_judge":
      return t("obs.hard_to_judge", { id: a, k: n(c.count ?? 0), n: n(c.of ?? 0) });
    case "fire_together":
      return t("obs.fire_together", { a, b, k: n(c.count ?? 0), n: n(c.of ?? 0) });
    case "mirrored_pair":
      return t("obs.mirrored_pair", { a, b, k: n(c.count ?? 0), n: n(c.of ?? 0) });
    case "read_differently":
      return t("obs.read_differently", { id: a, k: n(c.count ?? 0), n: n(c.of ?? 0) });
  }
}

function Suggests({
  t,
  n,
  result,
  estimate,
  canCheck,
  canRevise,
  onRevise,
  onCheck,
}: Readonly<{ t: T; n: N; result: PilotResult; estimate: string; canCheck: boolean; canRevise: boolean; onRevise: (ids: string[]) => void; onCheck: () => void }>) {
  // The weaker "never used" sentence names the pilot size, which its counts leave out.
  const observations = result.observations.map((o) => (o.kind === "never_used" && o.form !== "full" ? { ...o, counts: { ...o.counts, decided: result.decided } } : o));
  const needsAgent = result.not_computed.filter((c) => c.needs.includes("agent_check")).map((c) => c.kind);
  const short = result.not_computed.filter((c) => c.min !== undefined);
  const allFour = [...AGENT_KINDS].every((k) => needsAgent.some((x) => x === k));
  const names = needsAgent.filter((k) => AGENT_KINDS.has(k)).map((k) => t(`kind.${k}` as PilotKey));
  return (
    <section aria-labelledby="pilot-suggests" className="space-y-3">
      <h2 id="pilot-suggests" className="font-semibold text-ink">
        {t("suggestsTitle")}
      </h2>
      {observations.length === 0 ? (
        <p className="text-sm text-ink" data-nothing>{t("suggestsNone", { n: n(result.decided) })}</p>
      ) : (
        <ul className="space-y-3">
          {observations.map((o, i) => (
            <li key={`${o.kind}-${o.criteria.join("-")}-${o.source ?? ""}-${i}`} className="rounded-lg border border-dashed border-ink-muted bg-leaf p-4" data-observation={o.kind}>
              <p className="text-xs text-ink-muted">{t("readingLabel")}</p>
              <p className="mt-1 text-ink" dir="auto">
                {observationText(t, n, o)}
              </p>
              {o.source === "drafts" || o.source === "checklist" ? <p className="text-xs text-ink-muted">{t(`source.${o.source}`)}</p> : null}
              {canRevise && o.criteria.length > 0 ? (
                <div className="mt-2 flex flex-wrap gap-2">
                  {o.criteria.map((id) => (
                    <Button key={id} variant="quiet" onClick={() => onRevise([id])}>
                      {t("revise", { id })}
                    </Button>
                  ))}
                </div>
              ) : null}
            </li>
          ))}
        </ul>
      )}
      {names.length > 0 ? (
        <div className="text-sm text-ink" data-not-computed>
          <p>
            {allFour ? t("notComputed", { n: n(result.decided), estimate }) : t("notComputedSome", { names: names.join(", "), n: n(result.decided), estimate })}{" "}
            {canCheck ? (
              <button type="button" className="inline-flex min-h-11 items-center text-brand underline" onClick={onCheck}>
                {t("notComputedAction", { n: n(result.decided) })}
              </button>
            ) : null}
          </p>
          <details className="text-ink-muted">
            <summary className="min-h-11 cursor-pointer py-2">{t("details")}</summary>
            <p>{t("notComputedDetails")}</p>
          </details>
        </div>
      ) : null}
      {short.length > 0 ? (
        <ul className="space-y-1 text-sm text-ink-muted" data-not-enough>
          {short.map((c) => (
            <li key={c.kind}>
              {t("notEnough", {
                name: t(`kind.${c.kind}` as PilotKey),
                min: n(c.min ?? 0),
                what: t(`needs.${c.needs[0]}` as PilotKey),
                have: n(c.have ?? 0),
              })}
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}

function Records({ t, n, result, onOpen }: Readonly<{ t: T; n: N; result: PilotResult; onOpen: (record: PilotRecord) => void }>) {
  const [criterion, setCriterion] = useState("");
  const [outcome, setOutcome] = useState("");
  const [page, setPage] = useState(0);
  const codes = [...new Set(result.records.map((r) => r.reason_code).filter((c): c is string => Boolean(c)))];
  const shown = result.records.filter((r) => (!criterion || r.reason_code === criterion) && (!outcome || r.outcome === outcome));
  const from = page * PAGE;
  const slice = shown.slice(from, from + PAGE);
  return (
    <section aria-labelledby="pilot-records" className="rounded-lg border border-rule bg-leaf p-5">
      <h2 id="pilot-records" className="font-semibold text-ink">
        {t("recordsTitle")}
      </h2>
      <div className="mt-3 flex flex-wrap gap-4">
        <label className="text-sm text-ink">
          {t("filterCriterion")}
          <select
            className="mt-1 block min-h-11 rounded-md border border-rule bg-paper px-2"
            value={criterion}
            onChange={(e) => {
              setCriterion(e.target.value);
              setPage(0);
            }}
          >
            <option value="">{t("filterAll")}</option>
            {codes.map((c) => (
              <option key={c} value={c}>
                {c}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm text-ink">
          {t("filterOutcome")}
          <select
            className="mt-1 block min-h-11 rounded-md border border-rule bg-paper px-2"
            value={outcome}
            onChange={(e) => {
              setOutcome(e.target.value);
              setPage(0);
            }}
          >
            <option value="">{t("filterAll")}</option>
            {OUTCOMES.map((o) => (
              <option key={o} value={o}>
                {t(WORD[o])}
              </option>
            ))}
          </select>
        </label>
      </div>
      {slice.length === 0 ? (
        <p className="mt-3 text-sm text-ink-muted">{t("recordsEmpty")}</p>
      ) : (
        <ul className="mt-3 divide-y divide-rule">
          {slice.map((record) => (
            <li key={record.study_id} className="flex flex-wrap items-center gap-2 py-2" data-record={record.study_id}>
              <button type="button" className="min-h-11 text-start text-brand underline" onClick={() => onOpen(record)}>
                <bdi>{record.title || record.study_id}</bdi>
              </button>
              <DecisionBadge role={ROLE[record.outcome]}>{t(WORD[record.outcome])}</DecisionBadge>
              {record.reason_code ? <DataCell>{record.reason_code}</DataCell> : null}
            </li>
          ))}
        </ul>
      )}
      {shown.length > PAGE ? (
        <div className="mt-3 flex flex-wrap items-center gap-2 text-sm">
          <span className="text-ink-muted">{t("recordsPage", { from: n(from + 1), to: n(Math.min(from + PAGE, shown.length)), n: n(shown.length) })}</span>
          <Button variant="quiet" disabled={page === 0} onClick={() => setPage(page - 1)}>
            {t("previousPage")}
          </Button>
          <Button variant="quiet" disabled={from + PAGE >= shown.length} onClick={() => setPage(page + 1)}>
            {t("nextPage")}
          </Button>
        </div>
      ) : null}
    </section>
  );
}

function MorePilot({ locale, origin, corpus, label }: Readonly<{ locale: Locale; origin: string; corpus: number; label: (n: number) => string }>) {
  return <DrawPilot locale={locale} origin={origin} corpus={corpus} brand={false} label={label} onDrawn={() => window.location.assign(triageHref(locale, "pilot", origin))} />;
}

function Dialog({
  role = "dialog",
  labelledBy,
  describedBy,
  children,
}: Readonly<{ role?: "dialog" | "alertdialog"; labelledBy: string; describedBy?: string; children: ReactNode }>) {
  return (
    <div className="fixed inset-0 z-40 flex items-center justify-center bg-ink/40 p-4">
      <div role={role} aria-modal="true" aria-labelledby={labelledBy} aria-describedby={describedBy} className="max-h-[90vh] w-full max-w-xl overflow-y-auto rounded-lg border border-rule bg-paper p-6 text-ink">
        {children}
      </div>
    </div>
  );
}

function EndDialog({ t, n, result, origin, locale, onClose, onEnded }: Readonly<{ t: T; n: N; result: PilotResult; origin: string; locale: Locale; onClose: () => void; onEnded: () => void }>) {
  const [busy, setBusy] = useState(false);
  const [refusal, setRefusal] = useState<{ code: string; message: string } | null>(null);
  async function end() {
    setBusy(true);
    setRefusal(null);
    try {
      await closePilot(origin, result.pilot_id);
      onEnded();
    } catch (error) {
      setRefusal(codeOf(error));
    } finally {
      setBusy(false);
    }
  }
  return (
    <Dialog role="alertdialog" labelledBy="pilot-end-title" describedBy="pilot-end-body">
      <h2 id="pilot-end-title" className="font-semibold">
        {t("end.title")}
      </h2>
      <p id="pilot-end-body" className="mt-2 text-sm">
        {t("end.body", { k: n(result.decided), n: n(result.n) })}
      </p>
      {refusal ? <StateCard locale={locale} code={refusal.code} message={refusal.message} consoleOrigin={origin} /> : null}
      <div className="mt-4 flex flex-wrap gap-2">
        <Button autoFocus onClick={onClose}>
          {t("notNow")}
        </Button>
        <Button variant="primary" disabled={busy} onClick={() => void end()}>
          {t("end.confirm")}
        </Button>
      </div>
    </Dialog>
  );
}

const SPLIT_FIELDS = 2;

function ReviseDialog({
  t,
  n,
  locale,
  origin,
  criteria,
  preset,
  onClose,
  onRecorded,
}: Readonly<{ t: T; n: N; locale: Locale; origin: string; criteria: CriteriaView; preset: string[]; onClose: () => void; onRecorded: (answer: AmendmentAnswer) => void }>) {
  const [op, setOp] = useState<AmendmentOp | null>(null);
  const [ids, setIds] = useState<string[]>(preset.length ? [preset[0], ""] : ["", ""]);
  const [texts, setTexts] = useState<string[]>(["", ""]);
  const [side, setSide] = useState<CriteriaSide | null>(null);
  const [category, setCategory] = useState("");
  const [reason, setReason] = useState("");
  const [dry, setDry] = useState<AmendmentAnswer | null>(null);
  const [busy, setBusy] = useState(false);
  const [refusal, setRefusal] = useState<{ code: string; message: string } | null>(null);
  const first = useRef<HTMLInputElement>(null);

  useEffect(() => {
    first.current?.focus();
  }, []);

  const inForce = criteria.criteria;
  const find = (id: string) => inForce.find((c) => c.id === id) ?? null;
  const option = (id: string) => {
    const c = find(id);
    return c ? `${c.id} · ${c.text.length > 60 ? `${c.text.slice(0, 60)}…` : c.text}` : id;
  };

  // Reword starts from the wording in force; the other operations start empty.
  const choose = (index: number, id: string) => {
    const next = [...ids];
    next[index] = id;
    setIds(next);
    if (op === "reword" && index === 0) setTexts([find(id)?.text ?? "", texts[1]]);
    if (op === "reason_category" && index === 0) setCategory(find(id)?.reason_category ?? "");
  };
  const pick = (next: AmendmentOp) => {
    setOp(next);
    setDry(null);
    setRefusal(null);
    if (next === "reword" && ids[0]) setTexts([find(ids[0])?.text ?? "", ""]);
    if (next === "reason_category" && ids[0]) setCategory(find(ids[0])?.reason_category ?? "");
  };

  const request = (): AmendmentRequest | null => {
    if (!op) return null;
    const chosen = op === "merge" ? ids.filter(Boolean) : ids.slice(0, 1).filter(Boolean);
    const sideOf = op === "add" ? side : (find(chosen[0] ?? "")?.side ?? null);
    if (!sideOf) return null;
    const body: AmendmentRequest = { op, side: sideOf, ids: op === "add" ? [] : chosen, reason: reason.trim() };
    if (op === "reword" || op === "merge" || op === "add") body.text = texts[0];
    if (op === "split") body.text = texts.slice(0, SPLIT_FIELDS);
    if (op === "reason_category") body.reason_category = category;
    return body;
  };

  async function send(confirm: boolean) {
    const body = request();
    if (!body) return;
    setBusy(true);
    setRefusal(null);
    try {
      const answer = await amendCriteria(origin, body, confirm);
      if (confirm) onRecorded(answer);
      else setDry(answer);
    } catch (error) {
      setRefusal(codeOf(error));
      setDry(null);
    } finally {
      setBusy(false);
    }
  }

  const criterionSelect = (index: number, labelText: string) => (
    <label className="block text-sm">
      {labelText}
      <select className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-leaf px-2" value={ids[index]} onChange={(e) => choose(index, e.target.value)}>
        <option value="">{t("rev.choose")}</option>
        {inForce
          .filter((c) => index === 0 || op !== "merge" || !ids[0] || c.side === find(ids[0])?.side)
          .map((c) => (
            <option key={c.id} value={c.id} dir="auto">
              {option(c.id)}
            </option>
          ))}
      </select>
    </label>
  );
  const textArea = (index: number, labelText: string) => (
    <label className="block text-sm">
      {labelText}
      <textarea
        dir="auto"
        className="mt-1 block w-full rounded-md border border-rule bg-leaf p-2"
        rows={3}
        value={texts[index]}
        onChange={(e) => {
          const next = [...texts];
          next[index] = e.target.value;
          setTexts(next);
        }}
      />
    </label>
  );

  if (dry) {
    const body = request()!;
    const shown = dry.shown_again;
    const cited = body.ids.join(", ");
    const before = body.ids.map((id) => find(id)).filter(Boolean);
    const afterTexts = body.op === "split" ? (body.text as string[]) : body.op === "remove" || body.op === "reason_category" ? [] : [String(body.text ?? "")];
    const what =
      body.op === "reword"
        ? t("rev.kept", { id: body.ids[0], v: n(dry.criteria_version_after) })
        : body.op === "reason_category"
          ? t("rev.keptCategory", { id: body.ids[0], v: n(dry.criteria_version_after) })
          : body.op === "add"
            ? t("rev.added", { ids: dry.new_ids.join(", ") })
            : body.op === "remove"
              ? t("rev.removed", { id: dry.retired_ids.join(", ") })
              : t("rev.retired", { id: dry.retired_ids.join(", "), ids: dry.new_ids.join(", ") });
    return (
      <Dialog role="alertdialog" labelledBy="revise-confirm-title" describedBy="revise-confirm-what">
        <h2 id="revise-confirm-title" className="font-semibold">
          {t("rev.confirmTitle")}
        </h2>
        <p id="revise-confirm-what" className="mt-2 text-sm">
          {what}
        </p>
        {before.length > 0 || afterTexts.length > 0 ? (
          <table className="mt-3 w-full text-sm">
            <tbody>
              <tr className="border-t border-rule align-top">
                <th scope="row" className="py-1 pe-2 text-start font-normal text-ink-muted">
                  {t("rev.before")}
                </th>
                <td className="py-1" dir="auto">
                  {before.map((c) => `${c!.id}: ${c!.text}`).join(" / ") || "—"}
                </td>
              </tr>
              <tr className="border-t border-rule align-top">
                <th scope="row" className="py-1 pe-2 text-start font-normal text-ink-muted">
                  {t("rev.after")}
                </th>
                <td className="py-1" dir="auto">
                  {body.op === "reason_category" ? category : afterTexts.join(" / ") || "—"}
                </td>
              </tr>
            </tbody>
          </table>
        ) : null}
        {shown.total > 0 ? (
          <p className="mt-3 text-sm" data-shown-again>
            {t("rev.shown", { n: n(shown.total), x: n(shown.INCLUDE), y: n(shown.MAYBE), z: n(shown.EXCLUDE), id: cited })}
          </p>
        ) : (
          <div className="mt-3 text-sm" data-shown-again="none">
            <p>{t("rev.none")}</p>
            <p className="text-ink-muted">{t("rev.pilotNote")}</p>
          </div>
        )}
        <p className="mt-3 text-sm text-ink-muted">{t("rev.stays")}</p>
        <p className="mt-3 text-sm">
          <span className="text-ink-muted">{t("rev.yourReason")}: </span>
          <span dir="auto">{reason.trim()}</span>
        </p>
        {refusal ? <StateCard locale={locale} code={refusal.code} message={refusal.message} consoleOrigin={origin} /> : null}
        <div className="mt-4 flex flex-wrap gap-2">
          <Button variant="primary" disabled={busy} onClick={() => void send(true)}>
            {t("rev.record")}
          </Button>
          <Button onClick={() => setDry(null)}>{t("rev.back")}</Button>
        </div>
      </Dialog>
    );
  }

  const ready = request() !== null && reason.trim() !== "";
  return (
    <Dialog labelledBy="revise-title">
      <h2 id="revise-title" className="font-semibold">
        {t("rev.title")}
      </h2>
      <fieldset className="mt-3">
        <legend className="text-sm font-medium">{t("rev.legend")}</legend>
        <div className="mt-2 space-y-1">
          {OPS.map((value, i) => (
            <label key={value} className="flex min-h-11 items-center gap-2 text-sm">
              <input ref={i === 0 ? first : undefined} type="radio" name="revise-op" value={value} checked={op === value} onChange={() => pick(value)} />
              {t(`rev.op.${value}` as PilotKey)}
            </label>
          ))}
        </div>
      </fieldset>
      {op ? (
        <div className="mt-4 space-y-3" data-op={op}>
          {op === "add" ? (
            <fieldset>
              <legend className="text-sm">{t("rev.side")}</legend>
              {(["inclusion", "exclusion"] as CriteriaSide[]).map((s) => (
                <label key={s} className="me-4 inline-flex min-h-11 items-center gap-2 text-sm">
                  <input type="radio" name="revise-side" checked={side === s} onChange={() => setSide(s)} />
                  {t(`rev.side.${s}` as PilotKey)}
                </label>
              ))}
            </fieldset>
          ) : (
            criterionSelect(0, op === "merge" ? t("rev.criterionN", { k: 1 }) : t("rev.criterion"))
          )}
          {op === "merge" ? criterionSelect(1, t("rev.criterionN", { k: 2 })) : null}
          {op === "reword" || op === "merge" || op === "add" ? textArea(0, t("rev.text")) : null}
          {op === "split" ? (
            <>
              {textArea(0, t("rev.textN", { k: 1 }))}
              {textArea(1, t("rev.textN", { k: 2 }))}
            </>
          ) : null}
          {op === "reason_category" ? (
            <label className="block text-sm">
              {t("rev.reasonCategory")}
              <input dir="auto" className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-leaf px-2" value={category} onChange={(e) => setCategory(e.target.value)} />
            </label>
          ) : null}
        </div>
      ) : null}
      <label className="mt-4 block text-sm">
        {t("rev.reason")}
        <textarea
          dir="auto"
          className="mt-1 block w-full rounded-md border border-rule bg-leaf p-2"
          rows={2}
          maxLength={500}
          aria-describedby="revise-reason-count"
          value={reason}
          onChange={(e) => setReason(e.target.value.slice(0, 500))}
        />
      </label>
      <p id="revise-reason-count" className="text-xs text-ink-muted">
        {t("rev.reasonCount", { k: n(reason.length) })}
      </p>
      {busy ? (
        <p role="status" className="mt-2 text-sm text-ink-muted">
          {t("rev.checking")}
        </p>
      ) : null}
      {refusal ? <StateCard locale={locale} code={refusal.code} message={refusal.message} consoleOrigin={origin} /> : null}
      <div className="mt-4 flex flex-wrap gap-2">
        <Button variant="primary" disabled={!ready || busy} onClick={() => void send(false)}>
          {t("rev.check")}
        </Button>
        <Button onClick={onClose}>{t("notNow")}</Button>
      </div>
    </Dialog>
  );
}

function CheckDialog({
  t,
  n,
  locale,
  origin,
  result,
  setup,
  provider,
  initialModel,
  onClose,
  onDone,
}: Readonly<{ t: T; n: N; locale: Locale; origin: string; result: PilotResult; setup: ProposalSetup; provider: Provider; initialModel: string; onClose: () => void; onDone: () => void }>) {
  const [model, setModel] = useState(initialModel);
  const [ceiling, setCeiling] = useState("");
  const [estimate, setEstimate] = useState<RunEstimate | null>(null);
  const [run, setRun] = useState<RunView | null>(null);
  const [stopping, setStopping] = useState(false);
  const [busy, setBusy] = useState(false);
  const [refusal, setRefusal] = useState<{ code: string; message: string } | null>(null);
  const ids = useMemo(() => result.records.map((r) => r.study_id), [result]);
  const effort = setup.task.effort;
  const consent = setup.providers.find((p) => p.provider === provider)?.consent ?? null;
  const models = provider === "anthropic" ? LISTED_ANTHROPIC_MODELS : [model];

  useEffect(() => {
    let live = true;
    setEstimate(null);
    estimateRun(origin, { provider, model, effort, scope: { study_ids: ids }, cost_ceiling_usd: null })
      .then((e) => live && setEstimate(e))
      .catch((error: unknown) => live && setRefusal(codeOf(error)));
    return () => {
      live = false;
    };
  }, [origin, provider, model, effort, ids]);

  const poll = useCallback(
    (runId: string) => {
      const tick = async () => {
        try {
          const view = await getRun(origin, runId);
          setRun(view);
          if (FINISHED.has(view.state)) {
            setStopping(false);
            onDone();
            return;
          }
        } catch (error) {
          setRefusal(codeOf(error));
          return;
        }
        window.setTimeout(() => void tick(), POLL_MS);
      };
      void tick();
    },
    [origin, onDone],
  );

  async function begin() {
    setBusy(true);
    setRefusal(null);
    try {
      const priced = estimate?.priced !== false;
      const started = await startCalibration(origin, {
        pilot_id: result.pilot_id,
        provider,
        model,
        effort,
        cost_ceiling_usd: ceiling.trim() === "" || !priced ? null : Number(ceiling),
      });
      poll(started.run_id);
    } catch (error) {
      setRefusal(codeOf(error));
    } finally {
      setBusy(false);
    }
  }

  async function cancel() {
    if (!run) return;
    setStopping(true);
    try {
      await cancelRun(origin, run.run_id);
    } catch (error) {
      setRefusal(codeOf(error));
    }
  }

  const cost = estimate?.cost_usd != null ? usd(locale, estimate.cost_usd) : null;
  const active = run !== null && !FINISHED.has(run.state);
  const calibration = run?.calibration ?? null;
  return (
    <Dialog labelledBy="check-title">
      <h2 id="check-title" className="font-semibold">
        {t("actions.check", { n: n(result.decided) })}
      </h2>
      {run ? (
        <div className="mt-3 space-y-2 text-sm" data-check-run={run.state}>
          {active ? <p role="status">{stopping || run.cancel_requested ? t("cal.stopping") : t("cal.running", { n: n(run.records), k: n(run.done) })}</p> : null}
          {!active && calibration ? (
            <>
              <p>{t("cal.done")}</p>
              <p data-missed>{t("cal.missed", { k: n(calibration.missed_includes_count ?? 0), n: n(calibration.compared) })}</p>
            </>
          ) : null}
          {refusal ? <StateCard locale={locale} code={refusal.code} message={refusal.message} consoleOrigin={origin} /> : null}
          {!active && run.code ? <StateCard locale={locale} code={run.code} consoleOrigin={origin} /> : null}
          <div className="flex flex-wrap gap-2">
            {active ? (
              <Button disabled={stopping || run.cancel_requested} onClick={() => void cancel()}>
                {t("cal.cancel")}
              </Button>
            ) : null}
            <Button onClick={onClose}>{t("close")}</Button>
          </div>
        </div>
      ) : (
        <div className="mt-3 space-y-3 text-sm">
          <p>{t("cal.count", { n: n(result.decided) })}</p>
          <label className="block">
            {t("cal.model")}
            <select className="mt-1 block min-h-11 rounded-md border border-rule bg-leaf px-2" dir="ltr" value={model} onChange={(e) => setModel(e.target.value)}>
              {models.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </label>
          <p data-estimate>
            {estimate === null
              ? "…"
              : estimate.priced && cost
                ? t("cal.estimate", { cost, n: n(estimate.records), model, date: estimate.prices_as_of })
                : t("cal.estimateNone")}
          </p>
          <p>{t("cal.flow", { n: n(result.decided), provider })}</p>
          <label className="block">
            {t("cal.ceiling")}
            <input
              type="number"
              min="0"
              step="0.01"
              inputMode="decimal"
              dir="ltr"
              disabled={estimate?.priced === false}
              className="mt-1 block min-h-11 w-40 rounded-md border border-rule bg-leaf px-2 disabled:opacity-60"
              value={ceiling}
              onChange={(e) => setCeiling(e.target.value)}
            />
          </label>
          {consent === null ? <StateCard locale={locale} code="CONSENT_REQUIRED" consoleOrigin={origin} /> : null}
          {refusal ? <StateCard locale={locale} code={refusal.code} message={refusal.message} consoleOrigin={origin} /> : null}
          <div className="flex flex-wrap gap-2">
            <Button onClick={onClose}>{t("notNow")}</Button>
            <Button variant="primary" disabled={busy || estimate === null || consent === null} onClick={() => void begin()}>
              {cost && estimate?.priced ? t("cal.run", { cost }) : t("cal.runNoCost")}
            </Button>
          </div>
        </div>
      )}
    </Dialog>
  );
}

function RecordView({ t, n, locale, origin, record, onClose }: Readonly<{ t: T; n: N; locale: Locale; origin: string; record: PilotRecord; onClose: () => void }>) {
  const [detail, setDetail] = useState<RecordDetail | null>(null);
  const [refusal, setRefusal] = useState<{ code: string; message: string } | null>(null);
  useEffect(() => {
    let live = true;
    getRecord(origin, record.study_id)
      .then((d) => live && setDetail(d))
      .catch((error: unknown) => live && setRefusal(codeOf(error)));
    return () => {
      live = false;
    };
  }, [origin, record.study_id]);
  return (
    <Dialog labelledBy="pilot-record-title">
      <h2 id="pilot-record-title" className="font-semibold">
        <bdi>{record.title || record.study_id}</bdi>
      </h2>
      <p className="mt-2 flex flex-wrap items-center gap-2 text-sm" data-pilot-decision>
        <DecisionBadge role={ROLE[record.outcome]}>{t(WORD[record.outcome])}</DecisionBadge>
        {record.reason_code ? <DataCell>{record.reason_code}</DataCell> : null}
      </p>
      <p className="mt-1 text-sm text-ink-muted">{t("recordsReadonly", { v: n(record.criteria_version) })}</p>
      {refusal ? <StateCard locale={locale} code={refusal.code} message={refusal.message} consoleOrigin={origin} /> : null}
      {detail ? (
        <p className="mt-3 text-sm" dir="auto">
          {detail.abstract ?? t("noAbstract")}
        </p>
      ) : null}
      <div className="mt-4">
        <Button autoFocus onClick={onClose}>
          {t("close")}
        </Button>
      </div>
    </Dialog>
  );
}
