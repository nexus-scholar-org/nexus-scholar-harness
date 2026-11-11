"use client";

import { useEffect, useState } from "react";

import type { Locale } from "@/i18n";
import { Button } from "@/components/ui/base";
import { inceptionHref, InceptionFrame, InceptionRefusal, refusalOf, StepHeader, useDraft, type Refusal } from "@/components/inception-frame";
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
  const shapeKey = JSON.stringify([draft.topic, draft.paradigm, draft.playbook, draft.unit_of_analysis, draft.proof]);
  useEffect(() => {
    if (!record || !draft.paradigm) {
      setShape(null);
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(() => {
      const ask: Draft = { topic: draft.topic, paradigm: draft.paradigm, playbook: draft.playbook, unit_of_analysis: draft.unit_of_analysis, proof: draft.proof };
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

  const persist = async (next: "criteria" | "") => {
    const stored = await save({ ...draft, out_of_scope: lines(outText), rqs: rqs.map((rq) => rq.trim()).filter(Boolean) });
    if (stored) window.location.assign(inceptionHref(locale, next, next ? draftId : "", origin));
  };

  const leaning = scope?.recommended_paradigm;
  const firstEmpty = rqs.findIndex((rq) => rq.trim() === "");
  // The template is filled from the unit and the proof: it is offered only once
  // both are answered and the engine has answered for the answers on screen.
  // Otherwise a click would insert a sentence with blanks, or one from before
  // the last edit (the shape step is debounced).
  const draftFilled = Boolean(draft.unit_of_analysis?.trim()) && Boolean(draft.proof?.trim());
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
          <legend className="text-sm font-medium text-ink">{t("shape.paradigm")}</legend>
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
                      {p.name === leaning ? (
                        <span className="mt-1 inline-block rounded-sm border border-dashed border-rule px-2 text-xs text-ink-muted" data-leaning>
                          {t("shape.leaning")}
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
          <p className="mt-2 text-xs text-ink-muted">{t("shape.leaningNote")}</p>
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
                      {p.name === shape.recommended_playbook ? <span className="ms-2 text-xs text-brand">{t("shape.recommended")}</span> : null}
                    </span>
                  </label>
                );
              })}
            </div>
          </fieldset>
        ) : null}

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label htmlFor="shape-unit" className="block text-sm font-medium text-ink">
              {t("shape.unit")}
            </label>
            <input
              id="shape-unit"
              value={draft.unit_of_analysis ?? ""}
              onChange={(event) => update({ unit_of_analysis: event.target.value })}
              aria-describedby="shape-unit-help"
              className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink"
            />
            <p id="shape-unit-help" className="mt-1 text-xs text-ink-muted">
              {t("shape.unitHelp")}
            </p>
          </div>
          <div>
            <label htmlFor="shape-proof" className="block text-sm font-medium text-ink">
              {t("shape.proof")}
            </label>
            <input
              id="shape-proof"
              value={draft.proof ?? ""}
              onChange={(event) => update({ proof: event.target.value })}
              aria-describedby="shape-proof-help"
              className="mt-1 block min-h-11 w-full rounded-md border border-rule bg-paper px-2 text-ink"
            />
            <p id="shape-proof-help" className="mt-1 text-xs text-ink-muted">
              {t("shape.proofHelp")}
            </p>
          </div>
        </div>

        <div>
          <label htmlFor="shape-out" className="block text-sm font-medium text-ink">
            {t("shape.outOfScope")}
          </label>
          <textarea
            id="shape-out"
            rows={3}
            value={outText}
            onChange={(event) => setOutOfScope(event.target.value)}
            aria-describedby="shape-out-help"
            className="mt-1 block w-full rounded-md border border-rule bg-paper p-2 text-ink"
          />
          <p id="shape-out-help" className="mt-1 text-xs text-ink-muted">
            {t("shape.outOfScopeHelp")}
          </p>
        </div>

        <section aria-labelledby="shape-rq-draft" className="space-y-3">
          {shape ? (
            <div className="rounded-lg border border-dashed border-rule p-4" data-rq-draft data-draft-current={draftCurrent ? "true" : "false"} aria-busy={!draftCurrent}>
              <p id="shape-rq-draft" className="text-xs font-semibold text-ink-muted">
                {t("shape.rqDraft")}
              </p>
              <p className={`mt-1 ${draftCurrent ? "text-ink" : "text-ink-muted"}`} dir="ltr">
                {shape.rq_draft}
              </p>
              <div className="mt-2">
                <Button
                  disabled={!draftFilled || !draftCurrent}
                  aria-describedby={draftHint ? "shape-rq-draft-hint" : undefined}
                  onClick={() => setRq(firstEmpty >= 0 ? firstEmpty : rqs.length, shape.rq_draft)}
                >
                  {t("shape.useDraft", { n: (firstEmpty >= 0 ? firstEmpty : rqs.length) + 1 })}
                </Button>
              </div>
              {draftHint ? (
                <p id="shape-rq-draft-hint" className="mt-2 text-xs text-ink-muted" aria-live="polite">
                  {draftHint}
                </p>
              ) : null}
              <p className="mt-2 text-xs text-ink-muted">
                {t("shape.lexicon")}: <span dir="ltr">{shape.lexicon}</span>
              </p>
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

        <div className="flex flex-wrap gap-3">
          <Button variant="primary" type="submit" disabled={saving || !draft.paradigm} aria-describedby={draft.paradigm ? undefined : "shape-need-lens"}>
            {saving ? t("saving") : t("shape.continue")}
          </Button>
          <Button onClick={() => void persist("")} disabled={saving}>
            {t("saveAndExit")}
          </Button>
          <a className="inline-flex min-h-11 items-center text-brand underline" href={inceptionHref(locale, "direction", draftId, origin)} data-back>
            {t("shape.back")}
          </a>
          {draft.paradigm ? null : (
            <p id="shape-need-lens" className="self-center text-sm text-ink-muted">
              {t("shape.needLens")}
            </p>
          )}
        </div>
      </form>
    </InceptionFrame>
  );
}
