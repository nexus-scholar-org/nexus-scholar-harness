"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";

import type { Locale } from "@/i18n";
import { DataCell, Hint } from "@/components/ui/base";
import { StateCard } from "@/components/screening-state-card";
import { inceptionStateKey } from "@/lib/screening-states";
import { isScreeningApiError } from "@/lib/screening-api";
import { markStepChecked, readDraft, saveDraft, type AcceptedFrom, type Draft, type DraftOrigin, type DraftRecord } from "@/lib/inception-api";
import { importLossLines } from "@/lib/inception-import";
import { localStamp } from "@/lib/local-time";
import { Stamp } from "@/components/stamp";

export { Stamp };
import { inceptionT, type InceptionCopyKey } from "@/lib/inception-copy";
import { CHECKS_COPY } from "@/lib/checks-copy";
import { proposalsCountTemplate, proposalsT } from "@/lib/proposals-copy";
import { AssistProvider, useAssist } from "@/components/assist-context";
import { fillNodes, focusAnchor } from "@/components/assist-anchor";
import { notifyReviewChanged } from "@/components/review-bus";

/**
 * The frame every inception screen shares (specs 01–08, M4b): the draft id and
 * save time, the six-step bar (every step a link since M4d, when Explore and
 * Direction were built over the recon routes), the load-and-save hook over `GET/PUT
 * /inception/drafts/{id}` with `base_updated_at`, and the refusal card.
 */

export type InceptionStep = "scope" | "explore" | "direction" | "shape" | "criteria" | "review" | "done";

const STEPS: { step: InceptionStep; n: number; key: InceptionCopyKey }[] = [
  { step: "scope", n: 1, key: "step.scope" },
  { step: "explore", n: 2, key: "step.explore" },
  { step: "direction", n: 3, key: "step.direction" },
  { step: "shape", n: 4, key: "step.shape" },
  { step: "criteria", n: 5, key: "step.criteria" },
  { step: "review", n: 6, key: "step.review" },
];

export function consoleOrigin(): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get("console") ?? "";
}

export function draftParam(): string {
  if (typeof window === "undefined") return "";
  return new URLSearchParams(window.location.search).get("draft") ?? "";
}

/**
 * `?draft=` and `?console=`, read after hydration. The pages are prerendered
 * without a query string, so reading `window.location` during the first render
 * gave the step bar hrefs the server never saw and React a hydration mismatch
 * on every inception screen. Until `ready`, the screen renders what the server
 * rendered: no draft id, no origin.
 */
export function useLocationParams(): { origin: string; draftId: string; ready: boolean } {
  const [params, setParams] = useState({ origin: "", draftId: "", ready: false });
  useEffect(() => {
    setParams({ origin: consoleOrigin(), draftId: draftParam(), ready: true });
  }, []);
  return params;
}

/** The link to one inception screen for this draft, keeping the console override. */
export function inceptionHref(locale: Locale, step: InceptionStep | "import" | "", draftId = "", origin = ""): string {
  const query = new URLSearchParams();
  if (draftId) query.set("draft", draftId);
  if (origin) query.set("console", origin);
  const q = query.toString();
  return `/${locale}/inception/${step ? `${step}/` : ""}${q ? `?${q}` : ""}`;
}

export type Refusal = { code: string; message: string; details?: unknown };

export function refusalOf(error: unknown): Refusal {
  return isScreeningApiError(error)
    ? { code: error.code, message: error.serverMessage, details: error.serverDetails }
    : { code: "ENGINE_UNREACHABLE", message: "" };
}

/** Which screen asks for each field the engine names in `DRAFT_INCOMPLETE.details.missing`. */
const FIELD_STEP: Record<string, InceptionStep> = {
  topic: "scope",
  paradigm: "shape",
  playbook: "shape",
  unit_of_analysis: "shape",
  proof: "shape",
  rqs: "shape",
  concepts: "criteria",
  title: "review",
  lead_researcher: "review",
};

/** The step a refusal card links to on the inception screens (action `inception-step`, M4d). */
const ACTION_STEP: Record<string, InceptionStep> = {
  STALE_BINDING: "direction",
  POOL_EMPTY: "scope",
  RECON_NO_POOL: "explore",
  RECON_SESSION_NOT_FOUND: "explore",
  // M10b Part C: the sample curation's full-draft refusal sends the researcher to a narrower question.
  SAMPLE_EXCLUSIONS_FULL: "scope",
};

const ENGINE_REASON = new Set(["DRAFT_INVALID", "DRAFT_TOO_LARGE", "BODY_INVALID", "INTENT_INVALID", "WORKSPACE_ROOT_UNAVAILABLE", "WORKSPACE_EXISTS"]);

/** A refusal as a sentence (the shared state card), plus what the engine's details name. */
export function InceptionRefusal({
  locale,
  refusal,
  draftId = "",
  origin = "",
  onRetry,
  command,
  copyCode,
  extraDetails,
  hideActionLabel,
}: Readonly<{
  locale: Locale;
  refusal: Refusal;
  draftId?: string;
  origin?: string;
  onRetry?: () => void;
  command?: string;
  /** The card key, when a screen scopes it further than `inceptionStateKey` (Explore's probe refusals, M10a). */
  copyCode?: string;
  /** What else the refusal's details name, shown under Details after the shared lines. */
  extraDetails?: ReactNode;
  /** The screen supplies this card's action itself (see `StateCard`). */
  hideActionLabel?: boolean;
}>) {
  const t = inceptionT(locale);
  const details = (refusal.details ?? {}) as { missing?: unknown };
  const missing = Array.isArray(details.missing) ? details.missing.map(String) : [];
  return (
    <div data-refusal={refusal.code} className="space-y-2">
      <StateCard
        locale={locale}
        code={refusal.code}
        copyCode={copyCode ?? inceptionStateKey(refusal.code)}
        actionHref={ACTION_STEP[refusal.code] ? inceptionHref(locale, ACTION_STEP[refusal.code], draftId, origin) : undefined}
        message={refusal.message}
        consoleOrigin={origin}
        onRetry={onRetry}
        command={command}
        hideActionLabel={hideActionLabel}
        details={
          <>
            <RefusalDetails locale={locale} refusal={refusal} />
            {extraDetails}
          </>
        }
      />
      {missing.length > 0 ? (
        <div className="rounded-lg border border-rule bg-leaf p-4" data-missing>
          <p className="text-sm text-ink">{t("fieldsMissing")}</p>
          <ul className="mt-2 space-y-1 text-sm">
            {missing.map((field) => {
              const label = `field.${field}` as InceptionCopyKey;
              const step = FIELD_STEP[field];
              return (
                <li key={field} className="flex flex-wrap items-center gap-x-3">
                  <span className="text-ink">{label in INCEPTION_FIELD_KEYS ? t(label) : field}</span>
                  {step ? (
                    <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, step, draftId, origin)}>
                      {t("missing.goTo", { step: t(STEPS.find((s) => s.step === step)?.key ?? "step.review") })}
                    </a>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}
      {ENGINE_REASON.has(refusal.code) && refusal.message ? (
        <p className="text-sm text-ink-muted" data-engine-reason>
          <bdi dir="ltr">{refusal.message}</bdi>
        </p>
      ) : null}
    </div>
  );
}

/** The job a replace waits for, and the files an interrupted archive did and did not move (M4d, F1). */
function RefusalDetails({ locale, refusal }: Readonly<{ locale: Locale; refusal: Refusal }>) {
  const t = inceptionT(locale);
  const details = (refusal.details ?? {}) as Record<string, unknown>;
  if (refusal.code === "WORKSPACE_JOB_ACTIVE" && details.job != null) {
    const job = details.job;
    const name =
      typeof job === "object"
        ? ["kind", "job_id", "state"].map((k) => (job as Record<string, unknown>)[k]).filter((v) => v != null && v !== "").join(" · ")
        : String(job);
    return (
      <p className="mt-1 text-sm text-ink-muted" data-refusal-job>
        {t("refusal.job")} <DataCell>{name}</DataCell>
      </p>
    );
  }
  if (refusal.code === "ARCHIVE_INCOMPLETE") {
    const list = (v: unknown) => (Array.isArray(v) ? v.map(String) : []);
    const files = (key: "refusal.moved" | "refusal.notMoved", items: string[], attr: string) => (
      <div className="mt-1 text-sm" {...{ [attr]: "" }}>
        <p className="text-ink-muted">{t(key, { n: String(items.length) })}</p>
        {items.length ? (
          <ul className="ms-4 list-disc">
            {items.map((item) => (
              <li key={item}>
                <DataCell>{item}</DataCell>
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    );
    return (
      <>
        {details.backup_dir ? (
          <p className="mt-1 text-sm text-ink-muted" data-backup-dir>
            {t("refusal.backup")} <DataCell>{String(details.backup_dir)}</DataCell>
          </p>
        ) : null}
        {files("refusal.moved", list(details.moved), "data-moved")}
        {files("refusal.notMoved", list(details.not_moved), "data-not-moved")}
      </>
    );
  }
  return null;
}

const INCEPTION_FIELD_KEYS: Record<string, true> = Object.fromEntries(
  ["topic", "paradigm", "playbook", "unit_of_analysis", "proof", "rqs", "concepts", "title", "lead_researcher"].map((f) => [`field.${f}`, true]),
);

/** The steps an import fills (M10b, `09-start-from-protocol`); Explore carries nothing. */
export const IMPORTED_STEPS: InceptionStep[] = ["scope", "direction", "shape", "criteria", "review"];

export function InceptionSteps({
  locale,
  current,
  draftId,
  origin,
  unchecked = [],
  badges = {},
}: Readonly<{ locale: Locale; current: InceptionStep; draftId: string; origin: string; unchecked?: InceptionStep[]; badges?: StepBadges }>) {
  const t = inceptionT(locale);
  return (
    <nav aria-label={t("stepsLabel")} className="mb-6">
      <ol className="flex flex-wrap gap-2 text-sm">
        <li>
          <a className="inline-flex min-h-11 items-center px-3 text-brand underline" href={inceptionHref(locale, "", "", origin)} data-drafts-link>
            {t("backToDrafts")}
          </a>
        </li>
        {STEPS.map(({ step, n, key }) => (
          <li key={step}>
            <a
              href={inceptionHref(locale, step, draftId, origin)}
              aria-current={step === current ? "step" : undefined}
              className={`inline-flex min-h-11 items-center rounded-md border px-3 ${step === current ? "border-brand bg-brand-soft text-brand" : "border-rule text-ink"}`}
            >
              {t("step.current", { n, label: t(key) })}
              {unchecked.includes(step) ? (
                <span className="ms-2 text-xs text-unclear" data-imported-mark={step}>
                  · {t("imported.mark")}
                </span>
              ) : null}
              {badges[step]?.checks ? (
                <span className="ms-2 text-xs text-unclear" data-step-checks={step}>
                  · {fillNodes(CHECKS_COPY[locale]["checks.stepBadge"], { n: <bdi dir="ltr">{badges[step]?.checks}</bdi> })}
                </span>
              ) : null}
              {badges[step]?.suggestions ? (
                <span className="ms-2 text-xs text-ink-muted" data-step-suggestions={step}>
                  · {fillNodes(proposalsCountTemplate(locale, "proposals.badge", badges[step]?.suggestions ?? 0), { n: <bdi dir="ltr">{badges[step]?.suggestions}</bdi> })}
                </span>
              ) : null}
            </a>
          </li>
        ))}
      </ol>
    </nav>
  );
}

/**
 * Load the draft named in `?draft=`, keep it editable, save it whole with the
 * `updated_at` it was read at. A save that lost a race comes back as
 * `DRAFT_CONFLICT` and overwrites nothing; the screen shows it and offers a reload.
 */
export function useDraft() {
  const { origin, draftId, ready } = useLocationParams();
  const [record, setRecord] = useState<DraftRecord | null>(null);
  const [draft, setDraft] = useState<Draft>({});
  const [loadError, setLoadError] = useState<Refusal | null>(null);
  const [saveError, setSaveError] = useState<Refusal | null>(null);
  const [saving, setSaving] = useState(false);
  // M10b Part B: the checks and proposals re-read when this moves; `notRecorded` is the last save's answer.
  const [assistVersion, setAssistVersion] = useState(0);
  const [notRecorded, setNotRecorded] = useState<AcceptedFrom[]>([]);
  // A write the page made (a save, a proposal decision, a dismissal, a sample change): the panel and the next-step bar re-read.
  const bumpAssist = useCallback(() => {
    setAssistVersion((n) => n + 1);
    notifyReviewChanged();
  }, []);

  const load = useCallback(async () => {
    setLoadError(null);
    setSaveError(null);
    // No `?draft=` is not something the engine refused; the frame says so in words.
    if (!ready || !draftId) return;
    try {
      const read = await readDraft(origin, draftId);
      setRecord(read);
      setDraft(read.draft ?? {});
    } catch (error) {
      setLoadError(refusalOf(error));
    }
  }, [origin, draftId, ready]);

  useEffect(() => {
    void load();
  }, [load]);

  const update = useCallback((patch: Partial<Draft>) => setDraft((current) => ({ ...current, ...patch })), []);

  /** Take a record the engine answered with (a bind, M4d) as the one the page now holds. */
  const adopt = useCallback((next: DraftRecord) => {
    setRecord(next);
    setDraft(next.draft ?? {});
    setAssistVersion((n) => n + 1);
  }, []);

  /** An answer write that left the draft's answers as they were (M10b Part C, a sample change): only its time moves. */
  const adoptTime = useCallback((updatedAt: string) => {
    setRecord((current) => (current ? { ...current, updated_at: updatedAt } : current));
  }, []);

  /**
   * A proposal decision's answer (M10b): the record takes the stored draft and
   * time; the page takes the decided field from it and keeps its other edits.
   */
  const adoptDecision = useCallback((answer: { draft: Draft; updated_at: string }, field: string) => {
    const top = (field.startsWith("concepts[") ? "concepts" : field) as keyof Draft;
    setRecord((current) => (current ? { ...current, draft: answer.draft, updated_at: answer.updated_at } : current));
    setDraft((current) => ({ ...current, [top]: answer.draft[top] }));
  }, []);

  /**
   * Save the whole draft; resolves true when the engine stored it. `acceptedFrom`
   * names the engine suggestions accepted in this save (M10b); a value the engine
   * cannot record comes back in `not_recorded` and the save still stands.
   */
  const save = useCallback(
    async (next?: Draft, acceptedFrom: AcceptedFrom[] = []): Promise<boolean> => {
      if (!record) return false;
      const body = next ?? draft;
      setSaving(true);
      setSaveError(null);
      try {
        const { not_recorded: missed, ...stored } = await saveDraft(origin, record.session_id, body, record.updated_at, undefined, acceptedFrom);
        setRecord(stored);
        setDraft(stored.draft ?? {});
        setNotRecorded(missed ?? []);
        bumpAssist();
        return true;
      } catch (error) {
        setSaveError(refusalOf(error));
        return false;
      } finally {
        setSaving(false);
      }
    },
    [origin, record, draft, bumpAssist],
  );

  return {
    origin, draftId, ready, record, draft, setDraft, update, save, saving, loadError, saveError, setSaveError, reload: load, adopt, adoptTime,
    assistVersion, bumpAssist, adoptDecision, notRecorded,
  };
}

export function InceptionFrame({
  locale,
  current,
  draft,
  children,
}: Readonly<{ locale: Locale; current: InceptionStep; draft: ReturnType<typeof useDraft>; children: ReactNode }>) {
  const t = inceptionT(locale);
  const { record, loadError, origin, draftId, ready } = draft;
  // M10b: an imported draft marks each step until it is opened; opening this one clears its mark.
  const [opened, setOpened] = useState<InceptionStep[]>([]);
  const imported = record?.origin?.kind === "import" ? record.origin : null;
  const emitted = !!record?.emitted;
  const needsMark = !!imported && !emitted && IMPORTED_STEPS.includes(current) && imported.checked?.[current] === false;
  useEffect(() => {
    if (!needsMark || !record || opened.includes(current)) return;
    const controller = new AbortController();
    markStepChecked(origin, record.session_id, current, controller.signal).then(
      () => setOpened((list) => [...list, current]),
      () => undefined, // the mark stays; nothing else depends on it
    );
    return () => controller.abort();
  }, [needsMark, record, origin, current, opened]);
  const unchecked = imported && !emitted ? IMPORTED_STEPS.filter((step) => imported.checked?.[step] === false && !opened.includes(step)) : [];
  const assisted = STEPS.some((s) => s.step === current);
  // M10b: a check's field link lands here with `#<field anchor>`; focus it once the screen has drawn it.
  const sessionId = record?.session_id ?? "";
  useEffect(() => {
    if (!sessionId || typeof window === "undefined" || !window.location.hash) return;
    return focusAnchor(decodeURIComponent(window.location.hash.slice(1)), 15);
  }, [sessionId]);
  return (
    <AssistProvider locale={locale} state={draft} active={assisted && !!record}>
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8 lg:py-12">
      <AssistedSteps locale={locale} current={current} draftId={draftId} origin={origin} unchecked={unchecked} />
      {!ready ? (
        <p role="status" className="text-ink-muted">
          {t("loading")}
        </p>
      ) : !draftId ? (
        <div className="space-y-3" data-no-draft>
          <h1 className="font-display text-3xl text-ink">{t("noDraft")}</h1>
          <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "", "", origin)}>
            {t("backToDrafts")}
          </a>
        </div>
      ) : loadError ? (
        <div className="space-y-3">
          <InceptionRefusal locale={locale} refusal={loadError} draftId={draftId} origin={origin} onRetry={() => void draft.reload()} />
          <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "", "", origin)}>
            {t("backToDrafts")}
          </a>
        </div>
      ) : !record ? (
        <p role="status" className="text-ink-muted">
          {t("loading")}
        </p>
      ) : (
        <>
          <p className="mb-4 flex flex-wrap gap-x-3 text-xs text-ink-muted" data-draft-meta>
            <span>{t("eyebrow")}</span>
            <span>
              {t("draftId", { id: "" })}
              <DataCell>{record.session_id}</DataCell>
            </span>
            <span aria-live="polite" data-saved>
              {t("saved", { at: "" })}
              <Stamp at={record.updated_at} />
            </span>
            {/* M10d (03-guidance I-F2): how drafts work is a hint beside the saved status; the one write is stated at Review's gate. */}
            <Hint locale={locale} label={t("draftLabel")} text={t("nothingWritten")} textKey="nothingWritten" className="-ms-2" />
          </p>
          {draft.notRecorded.length ? (
            <p className="mb-4 text-sm text-ink-muted" role="status" data-not-recorded>
              {proposalsT(locale)("proposals.notRecorded")}
            </p>
          ) : null}
          {imported ? <ImportedBanner locale={locale} origin={imported} /> : null}
          {children}
        </>
      )}
    </div>
    </AssistProvider>
  );
}

export type StepBadges = Partial<Record<InceptionStep, { checks: number; suggestions: number }>>;

/** The step bar with the engine's counts per step (M10b): open checks to look at, open suggestions. */
function AssistedSteps(props: Readonly<{ locale: Locale; current: InceptionStep; draftId: string; origin: string; unchecked: InceptionStep[] }>) {
  const assist = useAssist();
  const badges: StepBadges = {};
  for (const { step } of STEPS) {
    const checks = assist?.all?.by_step?.[step];
    const proposals = assist?.proposals?.by_step?.[step];
    badges[step] = { checks: checks ? checks.blocker + checks.warning : 0, suggestions: proposals?.open ?? 0 };
  }
  return <InceptionSteps {...props} badges={badges} />;
}

/** The heading block every step opens with: the kicker, the question, the lede. */
export function StepHeader({ kicker, title, lede, extra, ledeHint }: Readonly<{ kicker: string; title: string; lede: string; extra?: ReactNode; ledeHint?: ReactNode }>) {
  return (
    <header className="mb-6">
      <p className="text-xs font-semibold uppercase tracking-[0.05em] text-brand rtl:tracking-normal">{kicker}</p>
      <h1 className="mt-2 font-display text-3xl text-ink">{title}</h1>
      {extra}
      <p className="mt-2 max-w-2xl text-ink-muted" data-copy="lede">
        {lede}
        {ledeHint}
      </p>
    </header>
  );
}

/** An engine timestamp as `YYYY-MM-DD HH:MM` on the researcher's clock (H-ui-findings F6; the engine stores UTC). */
export function stamp(at: string | null | undefined): string {
  return localStamp(at);
}

/** "Started from {label} ..." under the stepper of an imported draft, with what was not carried (M10b). */
function ImportedBanner({ locale, origin }: Readonly<{ locale: Locale; origin: DraftOrigin }>) {
  const t = inceptionT(locale);
  const lines = importLossLines(locale, origin.report?.lost ?? [], origin.report?.needs_you ?? []);
  return (
    <section className="mb-4 rounded-lg border border-rule bg-leaf p-3 text-sm text-ink" data-imported-banner>
      <p>
        {t("imported.banner", { label: origin.source?.label ?? "", date: stamp(origin.source?.protocol_created_at ?? origin.imported_at) })}
      </p>
      {lines.length ? (
        <details className="mt-1">
          <summary className="min-h-11 cursor-pointer rounded-sm py-3 leading-5 text-brand focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus">{t("imported.bannerMore", { n: String(lines.length) })}</summary>
          <ul className="list-disc ps-5 text-ink-muted">
            {lines.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </details>
      ) : null}
    </section>
  );
}
