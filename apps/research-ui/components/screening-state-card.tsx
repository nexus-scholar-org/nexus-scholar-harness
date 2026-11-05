"use client";

import type { Locale } from "@/i18n";
import { Button, DecisionBadge } from "@/components/ui/base";
import { AFFECTS_LABEL, stateCopy } from "@/lib/screening-states";

/**
 * One state card (spec 08): what happened, what it affects, one next step, and
 * the typed code in the role colour as selectable text. Colour is never the
 * only cue: the badge names the state.
 */

export type ScreeningStep = "home" | "prepare" | "triage" | "publish";

/** The new screening screens sit beside the legacy `/screening` page until M5-slim. */
export function stepHref(locale: Locale, step: ScreeningStep, consoleOrigin = ""): string {
  const path = { home: "home", prepare: "prepare", triage: "triage", publish: "publish" }[step];
  return `/${locale}/screening/${path}${consoleOrigin ? `?console=${encodeURIComponent(consoleOrigin)}` : ""}`;
}

const STEP_LABELS: Record<Locale, Record<ScreeningStep, string>> = {
  en: { home: "Home", prepare: "1 Prepare", triage: "2 Triage", publish: "3 Publish" },
  fr: { home: "Accueil", prepare: "1 Préparer", triage: "2 Trier", publish: "3 Publier" },
  ar: { home: "الرئيسية", prepare: "1 التحضير", triage: "2 المراجعة", publish: "3 النشر" },
};

const STEPS_LABEL: Record<Locale, string> = { en: "Screening steps", fr: "Étapes de la sélection", ar: "خطوات الفرز" };

export function ScreeningSteps({ locale, current, consoleOrigin = "" }: Readonly<{ locale: Locale; current: ScreeningStep; consoleOrigin?: string }>) {
  return (
    <nav aria-label={STEPS_LABEL[locale]} className="mb-6">
      <ol className="flex flex-wrap gap-2 text-sm">
        {(Object.keys(STEP_LABELS[locale]) as ScreeningStep[]).map((step) => (
          <li key={step}>
            <a
              href={stepHref(locale, step, consoleOrigin)}
              aria-current={step === current ? "page" : undefined}
              className={`inline-flex min-h-11 items-center rounded-md border px-3 ${step === current ? "border-brand bg-brand-soft text-brand" : "border-rule text-ink"}`}
            >
              {STEP_LABELS[locale][step]}
            </a>
          </li>
        ))}
      </ol>
    </nav>
  );
}

export function StateCard({
  locale,
  code,
  consoleOrigin = "",
  onRetry,
  message,
}: Readonly<{ locale: Locale; code: string; consoleOrigin?: string; onRetry?: () => void; message?: string }>) {
  const state = stateCopy(locale, code);
  const roleText = { include: "text-include", unclear: "text-unclear", blocked: "text-blocked", exclude: "text-exclude" }[state.role];
  const href =
    state.action === "prepare" || state.action === "triage" || state.action === "publish" || state.action === "home"
      ? stepHref(locale, state.action, consoleOrigin)
      : null;
  return (
    <section role="alert" aria-labelledby={`state-${code}`} className="rounded-lg border border-rule bg-leaf p-5" data-state={code}>
      <DecisionBadge role={state.role}>{state.title}</DecisionBadge>
      <h2 id={`state-${code}`} className="mt-2 font-semibold text-ink">
        {state.title}
      </h2>
      <p className="mt-1 text-ink">{state.body}</p>
      {message && !state.known ? (
        <p className="mt-1 text-sm text-ink-muted">
          <bdi dir="ltr">{message}</bdi>
        </p>
      ) : null}
      {state.affects ? (
        <p className="mt-1 text-sm text-ink-muted">
          {AFFECTS_LABEL[locale]} {state.affects}
        </p>
      ) : null}
      <p className={`mt-2 font-mono text-[0.8125rem] ${roleText}`} dir="ltr">
        {code}
      </p>
      <div className="mt-3">
        {state.action === "retry" && onRetry ? (
          <Button onClick={onRetry}>{state.actionLabel}</Button>
        ) : state.action === "reload" ? (
          <Button onClick={() => window.location.reload()}>{state.actionLabel}</Button>
        ) : state.action === "terminal" ? (
          <code className="rounded-sm bg-paper px-2 py-1 font-mono text-[0.8125rem] text-ink" dir="ltr">
            {state.actionLabel}
          </code>
        ) : href ? (
          <a className="text-brand underline" href={href}>
            {state.actionLabel}
          </a>
        ) : state.actionLabel ? (
          <p className="text-sm text-ink-muted">{state.actionLabel}</p>
        ) : null}
      </div>
    </section>
  );
}
