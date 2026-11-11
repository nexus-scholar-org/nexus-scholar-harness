"use client";

import { useCallback, useEffect, useState, type ReactNode } from "react";

import type { Locale } from "@/i18n";
import { DataCell } from "@/components/ui/base";
import { StateCard } from "@/components/screening-state-card";
import { inceptionStateKey } from "@/lib/screening-states";
import { isScreeningApiError } from "@/lib/screening-api";
import { readDraft, saveDraft, type Draft, type DraftRecord } from "@/lib/inception-api";
import { inceptionT, type InceptionCopyKey } from "@/lib/inception-copy";

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
export function inceptionHref(locale: Locale, step: InceptionStep | "", draftId = "", origin = ""): string {
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
};

const ENGINE_REASON = new Set(["DRAFT_INVALID", "INTENT_INVALID", "WORKSPACE_ROOT_UNAVAILABLE", "WORKSPACE_EXISTS"]);

/** A refusal as a sentence (the shared state card), plus what the engine's details name. */
export function InceptionRefusal({
  locale,
  refusal,
  draftId = "",
  origin = "",
  onRetry,
  command,
}: Readonly<{ locale: Locale; refusal: Refusal; draftId?: string; origin?: string; onRetry?: () => void; command?: string }>) {
  const t = inceptionT(locale);
  const details = (refusal.details ?? {}) as { missing?: unknown };
  const missing = Array.isArray(details.missing) ? details.missing.map(String) : [];
  return (
    <div data-refusal={refusal.code} className="space-y-2">
      <StateCard
        locale={locale}
        code={refusal.code}
        copyCode={inceptionStateKey(refusal.code)}
        actionHref={ACTION_STEP[refusal.code] ? inceptionHref(locale, ACTION_STEP[refusal.code], draftId, origin) : undefined}
        message={refusal.message}
        consoleOrigin={origin}
        onRetry={onRetry}
        command={command}
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

const INCEPTION_FIELD_KEYS: Record<string, true> = Object.fromEntries(
  ["topic", "paradigm", "playbook", "unit_of_analysis", "proof", "rqs", "concepts", "title", "lead_researcher"].map((f) => [`field.${f}`, true]),
);

export function InceptionSteps({ locale, current, draftId, origin }: Readonly<{ locale: Locale; current: InceptionStep; draftId: string; origin: string }>) {
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
  }, []);

  /** Save the whole draft; resolves true when the engine stored it. */
  const save = useCallback(
    async (next?: Draft): Promise<boolean> => {
      if (!record) return false;
      const body = next ?? draft;
      setSaving(true);
      setSaveError(null);
      try {
        const stored = await saveDraft(origin, record.session_id, body, record.updated_at);
        setRecord(stored);
        setDraft(stored.draft ?? {});
        return true;
      } catch (error) {
        setSaveError(refusalOf(error));
        return false;
      } finally {
        setSaving(false);
      }
    },
    [origin, record, draft],
  );

  return { origin, draftId, ready, record, draft, setDraft, update, save, saving, loadError, saveError, setSaveError, reload: load, adopt };
}

export function InceptionFrame({
  locale,
  current,
  draft,
  children,
}: Readonly<{ locale: Locale; current: InceptionStep; draft: ReturnType<typeof useDraft>; children: ReactNode }>) {
  const t = inceptionT(locale);
  const { record, loadError, origin, draftId, ready } = draft;
  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8 lg:py-12">
      <InceptionSteps locale={locale} current={current} draftId={draftId} origin={origin} />
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
              <bdi dir="ltr">{stamp(record.updated_at)}</bdi>
            </span>
          </p>
          {children}
        </>
      )}
    </div>
  );
}

/** The heading block every step opens with: the kicker, the question, the lede. */
export function StepHeader({ kicker, title, lede, extra }: Readonly<{ kicker: string; title: string; lede: string; extra?: ReactNode }>) {
  return (
    <header className="mb-6">
      <p className="text-xs font-semibold uppercase tracking-[0.05em] text-brand rtl:tracking-normal">{kicker}</p>
      <h1 className="mt-2 font-display text-3xl text-ink">{title}</h1>
      {extra}
      <p className="mt-2 max-w-2xl text-ink-muted">{lede}</p>
    </header>
  );
}

/** An engine timestamp as `YYYY-MM-DD HH:MM`, as the other screens print it (UTC, as stored). */
export function stamp(at: string | null | undefined): string {
  return at ? at.slice(0, 16).replace("T", " ") : "";
}
