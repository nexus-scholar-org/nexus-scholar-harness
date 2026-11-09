"use client";

import { useState } from "react";

import type { Locale } from "@/i18n";
import { Button } from "@/components/ui/base";
import { inceptionHref, InceptionFrame, InceptionRefusal, StepHeader, useDraft } from "@/components/inception-frame";
import { inceptionT } from "@/lib/inception-copy";

/**
 * Step 1, Scope (spec 01, M4b): the topic, the review window and the languages.
 * The recon search the canvas starts here (mode, sample size, the first 25
 * papers) waits for recon over HTTP; this step only saves answers.
 */

/** A year field's value as the draft holds it: a number, or null when empty. */
export function parseYear(raw: string): number | null | "invalid" {
  const trimmed = raw.trim();
  if (trimmed === "") return null;
  return /^\d{4}$/.test(trimmed) ? Number(trimmed) : "invalid";
}

export function parseLanguages(raw: string): string[] {
  return raw
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
}

export function InceptionScope({ locale }: Readonly<{ locale: Locale }>) {
  const t = inceptionT(locale);
  const state = useDraft();
  const { draft, update, save, saving, saveError, origin, draftId } = state;
  const [fromYear, setFromYear] = useState<string | null>(null);
  const [toYear, setToYear] = useState<string | null>(null);
  const [languages, setLanguages] = useState<string | null>(null);

  const fromText = fromYear ?? (draft.start_year != null ? String(draft.start_year) : "");
  const toText = toYear ?? (draft.end_year != null ? String(draft.end_year) : "");
  const languagesText = languages ?? (draft.languages ?? ["en"]).join(", ");
  const from = parseYear(fromText);
  const to = parseYear(toText);
  const yearsValid = from !== "invalid" && to !== "invalid";

  const persist = async (next: "shape" | "") => {
    if (!yearsValid) return;
    const stored = await save({
      ...draft,
      start_year: from as number | null,
      end_year: to as number | null,
      languages: parseLanguages(languagesText),
    });
    if (stored) window.location.assign(inceptionHref(locale, next, next ? draftId : "", origin));
  };

  return (
    <InceptionFrame locale={locale} current="scope" draft={state}>
      <StepHeader kicker={t("scope.kicker")} title={t("scope.title")} lede={t("scope.lede")} />
      <form
        className="space-y-5"
        onSubmit={(event) => {
          event.preventDefault();
          void persist("shape");
        }}
      >
        <div>
          <label htmlFor="scope-topic" className="block text-sm font-medium text-ink">
            {t("scope.topic")}
          </label>
          <textarea
            id="scope-topic"
            rows={3}
            value={draft.topic ?? ""}
            onChange={(event) => update({ topic: event.target.value })}
            aria-describedby="scope-topic-help"
            className="mt-1 block w-full rounded-md border border-rule bg-paper p-2 text-ink"
          />
          <p id="scope-topic-help" className="mt-1 text-xs text-ink-muted">
            {t("scope.topicHelp")}
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="scope-from" className="block text-sm font-medium text-ink">
              {t("scope.fromYear")}
            </label>
            <input
              id="scope-from"
              inputMode="numeric"
              value={fromText}
              onChange={(event) => setFromYear(event.target.value)}
              aria-invalid={from === "invalid"}
              aria-describedby={from === "invalid" ? "scope-year-error" : undefined}
              className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink"
            />
          </div>
          <div>
            <label htmlFor="scope-to" className="block text-sm font-medium text-ink">
              {t("scope.toYear")}
            </label>
            <input
              id="scope-to"
              inputMode="numeric"
              value={toText}
              onChange={(event) => setToYear(event.target.value)}
              aria-invalid={to === "invalid"}
              aria-describedby={to === "invalid" ? "scope-year-error scope-to-help" : "scope-to-help"}
              className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink"
            />
            <p id="scope-to-help" className="mt-1 text-xs text-ink-muted">
              {t("scope.toYearHelp")}
            </p>
          </div>
        </div>
        {!yearsValid ? (
          <p id="scope-year-error" role="alert" className="text-sm text-blocked">
            {t("scope.yearInvalid")}
          </p>
        ) : null}
        <div>
          <label htmlFor="scope-languages" className="block text-sm font-medium text-ink">
            {t("scope.languages")}
          </label>
          <input
            id="scope-languages"
            dir="ltr"
            value={languagesText}
            onChange={(event) => setLanguages(event.target.value)}
            aria-describedby="scope-languages-help"
            className="mt-1 block min-h-11 w-full max-w-sm rounded-md border border-rule bg-paper px-2 text-ink"
          />
          <p id="scope-languages-help" className="mt-1 text-xs text-ink-muted">
            {t("scope.languagesHelp")}
          </p>
        </div>

        <p className="rounded-md border border-dashed border-rule p-3 text-sm text-ink-muted" data-recon-note>
          {t("recon.note")}
        </p>

        {saveError ? <InceptionRefusal locale={locale} refusal={saveError} draftId={draftId} origin={origin} onRetry={() => void persist("shape")} /> : null}

        <div className="flex flex-wrap gap-3">
          <Button variant="primary" type="submit" disabled={saving || !yearsValid || !(draft.topic ?? "").trim()} aria-describedby={(draft.topic ?? "").trim() ? undefined : "scope-need-topic"}>
            {saving ? t("saving") : t("scope.continue")}
          </Button>
          <Button onClick={() => void persist("")} disabled={saving || !yearsValid}>
            {t("saveAndExit")}
          </Button>
          {(draft.topic ?? "").trim() ? null : (
            <p id="scope-need-topic" className="self-center text-sm text-ink-muted">
              {t("scope.needTopic")}
            </p>
          )}
        </div>
        <p className="text-xs text-ink-muted">{t("nothingWritten")}</p>
      </form>
    </InceptionFrame>
  );
}
