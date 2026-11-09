"use client";

import { useEffect, useState } from "react";

import type { Locale } from "@/i18n";
import { Button, DecisionBadge } from "@/components/ui/base";
import { AFFECTS_LABEL, stateCopy } from "@/lib/screening-states";
import { getCorpus } from "@/lib/screening-v1";

/**
 * One state card (spec 08): what happened, what it affects, one next step, and
 * the typed code in the role colour as selectable text. Colour is never the
 * only cue: the badge names the state.
 */

export type ScreeningStep = "home" | "import" | "prepare" | "proposals" | "triage" | "agreement" | "publish";

/** The new screening screens sit beside the legacy `/screening` page until M5-slim. */
export function stepHref(locale: Locale, step: ScreeningStep, consoleOrigin = ""): string {
  return `/${locale}/screening/${step}${consoleOrigin ? `?console=${encodeURIComponent(consoleOrigin)}` : ""}`;
}

/** The export and methods screen (spec 10): after Publish, not one of the five steps. */
export function exportHref(locale: Locale, consoleOrigin = ""): string {
  return `/${locale}/screening/export${consoleOrigin ? `?console=${encodeURIComponent(consoleOrigin)}` : ""}`;
}

const STEP_LABELS: Record<Locale, Record<ScreeningStep, string>> = {
  en: { home: "Home", import: "Import", prepare: "1 Prepare", proposals: "2 Agent proposals", triage: "3 Triage", agreement: "4 Agreement", publish: "5 Publish" },
  fr: { home: "Accueil", import: "Importer", prepare: "1 Préparer", proposals: "2 Propositions de l'agent", triage: "3 Trier", agreement: "4 Accord", publish: "5 Publier" },
  ar: { home: "الرئيسية", import: "الاستيراد", prepare: "1 التحضير", proposals: "2 مقترحات الوكيل", triage: "3 المراجعة", agreement: "4 الاتفاق", publish: "5 النشر" },
};

const STEPS_LABEL: Record<Locale, string> = { en: "Screening steps", fr: "Étapes de la sélection", ar: "خطوات الفرز" };
/** The label of every Details disclosure (rule page 12, M6-beta). */
export const DETAILS_LABEL: Record<Locale, string> = { en: "Details", fr: "Détails", ar: "التفاصيل" };

/** The way back to the workspaces screen (spec 00, M5-slim). */
const WORKSPACES_LABEL: Record<Locale, string> = { en: "All workspaces", fr: "Tous les espaces", ar: "كل مساحات العمل" };

/**
 * Import (spec 11) is a step, unnumbered, only until the corpus is accepted
 * (researcher, 2026-11-06); afterwards Home links to what was imported. The bar
 * asks the engine; a failed read (a phone, an old engine) leaves the step out.
 */
function useImportStep(consoleOrigin: string, current?: ScreeningStep): boolean {
  const [open, setOpen] = useState(current === "import");
  useEffect(() => {
    if (current === "import") return;
    const controller = new AbortController();
    getCorpus(consoleOrigin, controller.signal).then(
      (corpus) => setOpen(corpus.state !== "ACCEPTED"),
      () => setOpen(false),
    );
    return () => controller.abort();
  }, [consoleOrigin, current]);
  return open;
}

export function ScreeningSteps({ locale, current, consoleOrigin = "", className = "mb-6" }: Readonly<{ locale: Locale; current?: ScreeningStep; consoleOrigin?: string; className?: string }>) {
  const showImport = useImportStep(consoleOrigin, current);
  return (
    <nav aria-label={STEPS_LABEL[locale]} className={className}>
      <ol className="flex flex-wrap gap-2 text-sm">
        <li>
          <a
            href={`/${locale}/workspaces${consoleOrigin ? `?console=${encodeURIComponent(consoleOrigin)}` : ""}`}
            className="inline-flex min-h-11 items-center px-3 text-brand underline"
            data-workspaces-link
          >
            {WORKSPACES_LABEL[locale]}
          </a>
        </li>
        {(Object.keys(STEP_LABELS[locale]) as ScreeningStep[]).filter((step) => step !== "import" || showImport).map((step) => (
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
  command,
  pageHeading = false,
}: Readonly<{
  locale: Locale;
  code: string;
  consoleOrigin?: string;
  onRetry?: () => void;
  message?: string;
  command?: string;
  /** The card stands in for the whole screen (a failed first read): its title is the page's h1. */
  pageHeading?: boolean;
}>) {
  const Heading = pageHeading ? "h1" : "h2";
  const state = stateCopy(locale, code);
  const roleText = { include: "text-include", unclear: "text-unclear", blocked: "text-blocked", exclude: "text-exclude" }[state.role];
  const href =
    state.action === "import" || state.action === "prepare" || state.action === "proposals" || state.action === "triage" || state.action === "publish" || state.action === "home"
      ? stepHref(locale, state.action, consoleOrigin)
      : null;
  return (
    <section role="alert" aria-labelledby={`state-${code}`} className="rounded-lg border border-rule bg-leaf p-5" data-state={code}>
      <DecisionBadge role={state.role}>{state.title}</DecisionBadge>
      <Heading id={`state-${code}`} className="mt-2 font-semibold text-ink">
        {state.title}
      </Heading>
      <p className="mt-1 text-ink">{state.body}</p>
      {message && !state.known ? (
        <p className="mt-1 text-sm text-ink-muted">
          <bdi dir="ltr">{message}</bdi>
        </p>
      ) : null}
      {/* The typed code sits behind Details (rule page 12): still in the DOM, still selectable. */}
      <details className="mt-2 text-sm" data-state-details>
        <summary className="min-h-11 cursor-pointer py-3 leading-5 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus text-ink-muted">{DETAILS_LABEL[locale]}</summary>
        {state.affects ? (
          <p className="mt-1 text-sm text-ink-muted">
            {AFFECTS_LABEL[locale]} {state.affects}
          </p>
        ) : null}
        <p className={`mt-1 font-mono text-[0.8125rem] ${roleText}`} dir="ltr">
          {code}
        </p>
      </details>
      <div className="mt-3">
        {state.action === "retry" && onRetry ? (
          <Button onClick={onRetry}>{state.actionLabel}</Button>
        ) : state.action === "reload" ? (
          <Button onClick={() => window.location.reload()}>{state.actionLabel}</Button>
        ) : state.action === "terminal" ? (
          <code className="rounded-sm bg-paper px-2 py-1 font-mono text-[0.8125rem] text-ink" dir="ltr">
            {command ?? state.actionLabel}
          </code>
        ) : href ? (
          <a className="text-brand underline" href={href}>
            {state.actionLabel}
          </a>
        ) : state.actionLabel ? (
          <p className="text-sm text-ink-muted">{state.actionLabel}</p>
        ) : null}
        {state.command ? (
          <p className="mt-2">
            <code className="rounded-sm bg-paper px-2 py-1 font-mono text-[0.8125rem] text-ink" dir="ltr">
              {command ?? state.command}
            </code>
          </p>
        ) : null}
      </div>
    </section>
  );
}
