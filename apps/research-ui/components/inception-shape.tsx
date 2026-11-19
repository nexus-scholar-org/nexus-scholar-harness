"use client";

import { useEffect, useState } from "react";

import type { Locale } from "@/i18n";
import { Button, Hint, RecommendedBadge } from "@/components/ui/base";
import { guidanceT } from "@/lib/guidance-copy";
import { inceptionHref, InceptionFrame, InceptionRefusal, refusalOf, StepHeader, useDraft, type Refusal } from "@/components/inception-frame";
import { StepAssist } from "@/components/inception-assist";

import { runStep, type Draft, type ScopeStep, type ShapeStep } from "@/lib/inception-api";
import { inceptionT } from "@/lib/inception-copy";

/**
 * Step 4, Shape (spec 04, M4b): the lens, the playbook, the unit, the proof, what
 * is out of scope, and the research questions. The leaning, the recommended
 * playbook and the RQ template come from `POST /steps/scope` and `/steps/shape`
 * and are shown as drafts; nothing is applied until the researcher chooses it.
 */

function lines(text: string): string[] {
  return text
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

export function InceptionShape({ locale }: Readonly<{ locale: Locale }>) {
  const t = inceptionT(locale);
  const g = guidanceT(locale);
  const state = useDraft();
  const { draft, update, save, saving, saveError, origin, draftId, record } = state;
  const [scope, setScope] = useState<ScopeStep | null>(null);
  const [shape, setShape] = useState<ShapeStep | null>(null);
  // The answers `shape` was computed from; while it lags the form, the draft is stale.
  const [shapeFor, setShapeFor] = useState("");
  const [stepError, setStepError] = useState<Refusal | null>(null);
  const [outOfScope, setOutOfScope] = useState<string | null>(null);

  // The lenses and the leaning: asked once the draft is read.
  useEffect(() => {
    if (!record) return;
    const controller = new AbortController();
    runStep(origin, "scope", { topic: record.draft.topic ?? "" }, controller.signal).then(
      (answer) => setScope(answer),
      (error) => {
        if (!controller.signal.aborted) setStepError(refusalOf(error));
      },
    );
    return () => controller.abort();
  }, [origin, record]);

  // The playbook and RQ template follow the chosen lens, unit and proof.
  // M10b: the typed inclusions and their decisions decide whether the proof is still needed.
  const shapeKey = JSON.stringify([draft.topic, draft.paradigm, draft.playbook, draft.unit_of_analysis, draft.proof, draft.extra_inclusions, draft.criteria_decisions]);
  useEffect(() => {
    if (!record || !draft.paradigm) {
      setShape(null);
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(() => {
      const ask: Draft = {
        topic: draft.topic,
        paradigm: draft.paradigm,
        playbook: draft.playbook,
        unit_of_analysis: draft.unit_of_analysis,
        proof: draft.proof,
        extra_inclusions: draft.extra_inclusions,
        criteria_decisions: draft.criteria_decisions,
      };
      runStep(origin, "shape", ask, controller.signal).then(
        (answer) => {
          setShape(answer);
          setShapeFor(shapeKey);
          setStepError(null);
        },
        (error) => {
          if (!controller.signal.aborted) setStepError(refusalOf(error));
        },
      );
    }, 300);
    return () => {
      clearTimeout(timer);
      controller.abort();
    };
    // `shapeKey` lists exactly what the step reads.
  }, [origin, record, shapeKey]);

  const rqs = draft.rqs && draft.rqs.length > 0 ? draft.rqs : [""];
  const outText = outOfScope ?? (draft.out_of_scope ?? []).join("\n");

  const setRq = (index: number, text: string) => update({ rqs: rqs.map((rq, i) => (i === index ? text : rq)) });

  const planned = plannedProblem(draft.pool_min, draft.pool_max);

  const persist = async (next: "criteria" | "") => {
    if (planned) return;
    const stored = await save({ ...draft, out_of_scope: lines(outText), rqs: rqs.map((rq) => rq.trim()).filter(Boolean) });
    if (stored) window.location.assign(inceptionHref(locale, next, next ? draftId : "", origin));
  };

  // Spec 04: Continue needs a lens and a playbook the researcher chose; the marked playbook is never chosen for them.
  const needed = !draft.paradigm ? "lens" : !draft.playbook ? "playbook" : null;
  const leaning = scope?.recommended_paradigm;
  const firstEmpty = rqs.findIndex((rq) => rq.trim() === "");
  // The template is filled from the unit and the proof: it is offered only once
  // both are answered and the engine has answered for the answers on screen.
  // Otherwise a click would insert a sentence with blanks, or one from before
  // the last edit (the shape step is debounced).
  const draftFilled = Boolean(draft.unit_of_analysis?.trim()) && Boolean(draft.proof?.trim());
  // M10b (R4): the engine says whether the proof may stay empty.
  const proofOptional = shape?.proof_required === false;
  const draftCurrent = shape !== null && shapeFor === shapeKey;
  const draftHint = !draftFilled ? t("shape.draftNeeds") : !draftCurrent ? t("shape.draftWaiting") : "";

  return (
    <InceptionFrame locale={locale} current="shape" draft={state}>
      <StepHeader kicker={t("shape.kicker")} title={t("shape.title")} lede={t("shape.lede")} />
      <form
        className="space-y-6"
        onSubmit={(event) => {
          event.preventDefault();
          void persist("criteria");
        }}
      >
        <fieldset>
          <legend className="text-sm font-medium text-ink">
            {t("shape.paradigm")}
            <Hint locale={locale} label={t("shape.paradigm")} text={t("shape.leaningNote")} textKey="shape.leaningNote" className="ms-1" />
          </legend>
          {scope ? (
            <div className="mt-2 grid gap-3 sm:grid-cols-2" data-paradigms>
              {scope.paradigms.map((p) => {
                const chosen = draft.paradigm === p.name;
                return (
                  <label
                    key={p.name}
                    className={`flex min-h-11 cursor-pointer gap-3 rounded-lg border p-4 ${chosen ? "border-brand bg-brand-soft" : "border-rule bg-leaf"}`}
                    data-paradigm={p.name}
                  >
                    <input
                      type="radio"
                      name="paradigm"
                      value={p.name}
                      checked={chosen}
                      onChange={() => update({ paradigm: p.name, playbook: null })}
                      className="mt-1 h-5 w-5 shrink-0"
                    />
                    <span className="min-w-0">
                      <span className="block font-medium text-ink">{p.name}</span>
                      {/* M10d (03-guidance rule 3): the lens the word scan leans to is marked, with its source; the why is the legend's hint (never in a label). Nothing is chosen. */}
                      {p.name === leaning ? (
                        <span className="mt-1 block" data-leaning>
                          <RecommendedBadge locale={locale} source={g("guidance.recommended.source.wordScan")} />
                        </span>
                      ) : null}
                      <span className="mt-1 block text-sm text-ink-muted" dir="ltr">
                        {p.goal}
                      </span>
                    </span>
                  </label>
                );
              })}
            </div>
          ) : !stepError ? (
            <p role="status" className="mt-2 text-ink-muted">
              {t("asking")}
            </p>
          ) : null}
        </fieldset>

        {shape ? (
          <fieldset>
            <legend className="text-sm font-medium text-ink">{t("shape.playbook")}</legend>
            <div className="mt-2 space-y-2" data-playbooks>
              {shape.playbooks.map((p) => {
                const chosen = (draft.playbook ?? "") === p.name;
                return (
                  <label key={p.name} className="flex min-h-11 cursor-pointer items-center gap-3 rounded-md border border-rule bg-leaf px-3" data-playbook={p.name}>
                    <input type="radio" name="playbook" value={p.name} checked={chosen} onChange={() => update({ playbook: p.name })} className="h-5 w-5 shrink-0" />
                    <span className="min-w-0 [overflow-wrap:anywhere]">
                      <bdi dir="ltr" className="font-mono text-[0.8125rem] text-ink">
                        {p.name}
                      </bdi>{" "}
                      <span className="text-sm text-ink-muted" dir="ltr">
                        · {p.framework}
                      </span>
                      {p.name === shape.recommended_playbook ? (
                        <span className="ms-2" data-recommended-playbook>
                          <RecommendedBadge locale={locale} source={g("guidance.recommended.source.lens")} />
                        </span>
                      ) : null}
                    </span>
                  </label>
                );
              })}
            </div>
          </fieldset>
        ) : null}

        <PlannedRecords
          locale={locale}
          min={draft.pool_min ?? null}
          max={draft.pool_max ?? null}
          preset={shape?.pool_preset ?? null}
          earlier={record?.origin?.earlier_pool ?? null}
          problem={planned}
          onChange={(min, max) => update({ pool_min: min, pool_max: max })}
        />

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <div className="flex items-center gap-1">
              <label htmlFor="shape-unit" className="block text-sm font-medium text-ink">
                {t("shape.unit")}
              </label>
              <Hint locale={locale} label={t("shape.unit")} text={t("shape.unitHelp")} textKey="shape.unitHelp" id="shape-unit-help" />
            </div>
            <input
              id="shape-unit"
              value={draft.unit_of_analysis ?? ""}
              onChange={(event) => update({ unit_of_analysis: event.target.value })}
              aria-describedby="shape-unit-help"
              className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink"
            />
          </div>
          <div>
            <div className="flex items-center gap-1">
              <label htmlFor="shape-proof" className="block text-sm font-medium text-ink">
                {t("shape.proof")}
                {proofOptional ? (
                  <span className="ms-1 font-normal text-ink-muted" data-proof-optional>
                    {t("shape.proof.optional")}
                  </span>
                ) : null}
              </label>
              <Hint locale={locale} label={t("shape.proof")} text={t("shape.proofHelp")} textKey="shape.proofHelp" id="shape-proof-help" />
            </div>
            <input
              id="shape-proof"
              value={draft.proof ?? ""}
              onChange={(event) => update({ proof: event.target.value })}
              aria-describedby="shape-proof-help"
              className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink"
            />
            {record?.origin?.report?.needs_you?.includes("proof") && !(draft.proof ?? "").trim() && !proofOptional ? (
              <p className="mt-1 text-sm text-unclear" data-needs-proof>
                {t("imported.needs.line", { field: t("imported.needs.proof") })}
              </p>
            ) : null}
          </div>
        </div>

        <div>
          <div className="flex items-center gap-1">
            <label htmlFor="shape-out" className="block text-sm font-medium text-ink">
              {t("shape.outOfScope")}
            </label>
            <Hint locale={locale} label={t("shape.outOfScope")} text={t("shape.outOfScopeHelp")} textKey="shape.outOfScopeHelp" id="shape-out-help" />
          </div>
          <textarea
            id="shape-out"
            rows={3}
            value={outText}
            onChange={(event) => setOutOfScope(event.target.value)}
            aria-describedby="shape-out-help"
            className="mt-1 block w-full rounded-md border border-rule bg-paper p-2 text-ink"
          />
        </div>

        <section aria-labelledby="shape-rq-draft" className="space-y-3">
          {shape ? (
            <div className="rounded-lg border border-dashed border-rule p-4" data-rq-draft data-draft-current={draftCurrent ? "true" : "false"} aria-busy={!draftCurrent}>
              <div className="flex items-center gap-1">
                <p id="shape-rq-draft" className="text-xs font-semibold text-ink-muted">
                  {t("shape.rqDraft")}
                </p>
                {shape.lexicon ? (
                  <Hint locale={locale} label={t("shape.rqDraft")} text={`${t("shape.lexicon")}: ${shape.lexicon}`} textKey="shape.lexicon" />
                ) : null}
              </div>
              {shape.rq_draft ? (
                <p className={`mt-1 ${draftCurrent ? "text-ink" : "text-ink-muted"}`} dir="ltr">
                  {shape.rq_draft}
                </p>
              ) : null}
              <div className="mt-2">
                <Button
                  disabled={!draftFilled || !draftCurrent || !shape.rq_draft}
                  aria-describedby={draftHint ? "shape-rq-draft-hint" : undefined}
                  onClick={() => shape.rq_draft && setRq(firstEmpty >= 0 ? firstEmpty : rqs.length, shape.rq_draft)}
                >
                  {t("shape.useDraft", { n: (firstEmpty >= 0 ? firstEmpty : rqs.length) + 1 })}
                </Button>
              </div>
              {draftHint ? (
                <p id="shape-rq-draft-hint" className="mt-2 text-xs text-ink-muted" aria-live="polite">
                  {draftHint}
                </p>
              ) : null}
            </div>
          ) : (
            <p id="shape-rq-draft" className="text-sm text-ink-muted">
              {t("shape.chooseLens")}
            </p>
          )}
          {rqs.map((rq, index) => (
            <div key={index}>
              <label htmlFor={`shape-rq-${index}`} className="block text-sm font-medium text-ink">
                {t("shape.rq", { n: index + 1 })}
              </label>
              <textarea
                id={`shape-rq-${index}`}
                rows={2}
                value={rq}
                onChange={(event) => setRq(index, event.target.value)}
                className="mt-1 block w-full rounded-md border border-rule bg-paper p-2 text-ink"
              />
              {rqs.length > 1 ? (
                <Button variant="quiet" className="px-0" onClick={() => update({ rqs: rqs.filter((_, i) => i !== index) })}>
                  {t("shape.removeRq", { n: index + 1 })}
                </Button>
              ) : null}
            </div>
          ))}
          <Button onClick={() => update({ rqs: [...rqs, ""] })}>{t("shape.addRq")}</Button>
        </section>

        {stepError ? <InceptionRefusal locale={locale} refusal={stepError} draftId={draftId} origin={origin} /> : null}
        {saveError ? <InceptionRefusal locale={locale} refusal={saveError} draftId={draftId} origin={origin} onRetry={() => void persist("criteria")} /> : null}

        <StepAssist locale={locale} step="shape" />

        <div className="flex flex-wrap gap-3">
          <Button variant="primary" type="submit" disabled={saving || !draft.paradigm || !draft.playbook || !!planned} aria-describedby={needed ? "shape-need" : undefined}>
            {saving ? t("saving") : t("shape.continue")}
          </Button>
          <Button onClick={() => void persist("")} disabled={saving || !!planned}>
            {t("saveAndExit")}
          </Button>
          <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "direction", draftId, origin)} data-back>
            {t("shape.back")}
          </a>
          {needed ? (
            <p id="shape-need" className="self-center text-sm text-ink-muted" data-need={needed}>
              {t(needed === "lens" ? "shape.needLens" : "shape.needPlaybook")}
            </p>
          ) : null}
        </div>
      </form>
    </InceptionFrame>
  );
}

/**
 * Presentation-only checks of the two numbers as typed, so a sentence can say
 * what to fix before the save; the engine's `DRAFT_INVALID` stays the authority.
 */
function plannedProblem(min: number | null | undefined, max: number | null | undefined): "order" | "range" | "max" | null {
  const whole = (n: number) => Number.isInteger(n);
  if (max == null) return min == null ? null : "max";
  if (!whole(max) || max < 1 || max > 1_000_000) return "range";
  if (min != null && (!whole(min) || min < 0)) return "range";
  if (min != null && min > max) return "order";
  return null;
}

function numberOrNull(text: string): number | null {
  if (!text.trim()) return null;
  const n = Number(text);
  return Number.isFinite(n) ? n : NaN;
}

/** "How many records do you plan to screen?" (M10b, R3, `04-shape`). Never prefilled; the preset is offered, not marked. */
function PlannedRecords({
  locale,
  min,
  max,
  preset,
  earlier = null,
  problem,
  onChange,
}: Readonly<{
  locale: Locale;
  min: number | null;
  max: number | null;
  preset: { min: number; max: number } | null;
  earlier?: { min: number; max: number } | null;
  problem: "order" | "range" | "max" | null;
  onChange: (min: number | null, max: number | null) => void;
}>) {
  const t = inceptionT(locale);
  const shown = (n: number | null) => (n == null || Number.isNaN(n) ? "" : String(n));
  return (
    <fieldset className="rounded-lg border border-rule bg-leaf p-4" data-planned>
      <legend className="px-1 text-sm font-medium text-ink">
        {t("shape.planned.title")}
        <Hint locale={locale} label={t("shape.planned.title")} text={t("shape.planned.hint")} textKey="shape.planned.hint" id="shape-planned-hint" className="ms-1" />
      </legend>
      <div className="mt-2 flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor="shape-planned-min" className="block text-sm text-ink">
            {t("shape.planned.from")}
          </label>
          <input
            id="shape-planned-min"
            type="number"
            inputMode="numeric"
            min={0}
            dir="ltr"
            value={shown(min)}
            onChange={(event) => onChange(numberOrNull(event.target.value), max)}
            aria-describedby="shape-planned-hint"
            aria-invalid={problem === "order" || problem === "max" || undefined}
            className="mt-1 block min-h-11 w-32 rounded-md border border-rule bg-paper px-2 text-ink"
          />
        </div>
        <div>
          <label htmlFor="shape-planned-max" className="block text-sm text-ink">
            {t("shape.planned.upTo")}
          </label>
          <input
            id="shape-planned-max"
            type="number"
            inputMode="numeric"
            min={1}
            dir="ltr"
            value={shown(max)}
            onChange={(event) => onChange(min, numberOrNull(event.target.value))}
            aria-describedby="shape-planned-hint"
            aria-invalid={problem === "range" || problem === "max" || undefined}
            className="mt-1 block min-h-11 w-32 rounded-md border border-rule bg-paper px-2 text-ink"
          />
        </div>
      </div>
      {problem ? (
        <p className="mt-2 text-sm text-unclear" role="alert" data-planned-problem={problem}>
          {t(problem === "order" ? "shape.planned.err.order" : problem === "max" ? "shape.planned.err.max" : "shape.planned.err.range")}
        </p>
      ) : null}
      {preset ? (
        <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-ink-muted" data-planned-preset>
          <span>{t("shape.planned.preset", { min: String(preset.min), max: String(preset.max) })}</span>
          <Button onClick={() => onChange(preset.min, preset.max)} data-use-preset>
            {t("shape.planned.usePreset")}
          </Button>
        </div>
      ) : null}
      {earlier ? (
        <div className="mt-2" data-planned-earlier>
          <Button onClick={() => onChange(earlier.min, earlier.max)} data-use-earlier>
            {t("shape.planned.useEarlier", { min: String(earlier.min), max: String(earlier.max) })}
          </Button>
        </div>
      ) : null}
    </fieldset>
  );
}
