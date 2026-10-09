"use client";

import { useState, type FormEvent } from "react";

import { translate, type Locale, type MessageKey } from "@/i18n";

/**
 * The three decisions the form can record, and the message key that labels each
 * one.
 *
 * The keys are written out as literals rather than built by concatenating a
 * prefix with the id: the catalogs are flat maps with no partial lookup, and a
 * constructed key would compile fine and then fail at runtime on the first
 * render (N4's loud failure). The explicit table is also what lets
 * `tests/screening-form.test.tsx` assert that all three labels are *distinct*
 * — the negative case where "Include" and "Exclude" could collapse into one
 * indistinguishable choice.
 */
const DECISIONS = [
  { id: "include", key: "screening.decision.include" },
  { id: "exclude", key: "screening.decision.exclude" },
  { id: "unclear", key: "screening.decision.unclear" },
] as const satisfies readonly { id: string; key: MessageKey }[];

type Decision = (typeof DECISIONS)[number]["id"];

/**
 * The screening decision form (packet UI-04).
 *
 * A client component, and the only one packet UI-04 adds: the form holds two
 * pieces of local state — which decision is chosen and what the reason says —
 * and nothing else about this file is interactive. The record it screens is
 * rendered by the server composition around it; this component never imports
 * the fixture, so the demonstration data and the form's state are separate
 * objects with no path between them.
 *
 * What the form deliberately does **not** do is the heart of the packet:
 *
 * - **No decision is preselected.** Nothing is checked until the reader checks
 *   it. A preselected "Include" would present a machine default as a human
 *   decision, which is the exact failure the packet's negative cases name.
 * - **Nothing is submitted anywhere.** `onSubmit` prevents the default and
 *   returns; the submit button is `disabled` in every state, and its
 *   explanation is real, visible text (`screening.submitDisabledExplanation`)
 *   naming that no API exists — not a tooltip, not a comment, not a state the
 *   reader has to discover by pressing the button. `screening.noPersistence`
 *   states the second half: nothing is written to a workspace, a file, or this
 *   browser. The form keeps no storage call of any kind, so there is no
 *   persistence to leak through a side channel the text forgot to mention.
 * - **The validation message is not a live region.** Choosing "Exclude" with an
 *   empty reason shows `screening.reasonRequired` beside the field and links it
 *   into the textarea's `aria-describedby`; it is not `aria-live`, so it does
 *   not interrupt a screen reader mid-sentence to announce a condition the
 *   reader just created themselves. It is real text either way — visible without
 *   colour alone carrying it, since the field's own hint already explains when
 *   the reason is required.
 *
 * Structure: a `<fieldset>`/`<legend>` groups the radios (the legend is the
 * group's accessible name, so the choice is announced as "Decision, radio
 * group" rather than three loose radios), each radio is wrapped in its own
 * `<label>` so the whole row is a click target, and the reason textarea's hint
 * sits before the field it describes so a sighted reader meets the rule before
 * the box. The only state change on screen is the conditional requirement line;
 * no heading, tab stop, or landmark is added or removed by any choice.
 */
export function ScreeningForm({ locale }: Readonly<{ locale: Locale }>) {
  const [decision, setDecision] = useState<Decision | null>(null);
  const [reason, setReason] = useState("");

  const reasonRequired = decision === "exclude" && reason.trim() === "";

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
  }

  return (
    <form onSubmit={handleSubmit} className="max-w-3xl" aria-label={translate(locale, "screening.decisionLegend")}>
      <fieldset>
        <legend className="font-display text-xl leading-8 text-ink">
          {translate(locale, "screening.decisionLegend")}
        </legend>
        <div className="mt-3 flex flex-wrap gap-x-8 gap-y-3">
          {DECISIONS.map(({ id, key }) => (
            <label
              key={id}
              htmlFor={`screening-decision-${id}`}
              className="flex items-center gap-2 text-sm leading-6 text-ink"
            >
              <input
                type="radio"
                id={`screening-decision-${id}`}
                name="screening-decision"
                value={id}
                checked={decision === id}
                onChange={() => setDecision(id)}
                className="size-4 accent-evidence"
              />
              <span>{translate(locale, key)}</span>
            </label>
          ))}
        </div>
      </fieldset>

      <div className="mt-8">
        <label htmlFor="screening-reason" className="block text-sm font-medium text-ink">
          {translate(locale, "screening.reasonLabel")}
        </label>
        <p id="screening-reason-hint" className="mt-1 text-sm leading-6 text-ink-muted">
          {translate(locale, "screening.reasonHint")}
        </p>
        {/*
          Not `aria-live`: the message appears in response to a choice the
          reader just made, is anchored to the field it governs through
          `aria-describedby`, and is visible on its own merits — an
          interruption would repeat what the click already showed them.
        */}
        {/*
          No focus utilities here: the focus treatment is declared once in
          `globals.css` for `input` and `textarea` alike (the comment there
          explains why the form did not get its own), so this field's focus
          indicator is the nav's focus indicator. The prose deliberately avoids
          naming the bare utility the stylesheet would otherwise harvest —
          `tests-browser/hygiene.spec.ts` fails any emitted class with no
          product-code source.
        */}
        <textarea
          id="screening-reason"
          rows={4}
          value={reason}
          onChange={(event) => setReason(event.target.value)}
          aria-describedby={
            reasonRequired
              ? "screening-reason-hint screening-reason-required"
              : "screening-reason-hint"
          }
          className="mt-2 block w-full border border-rule-strong bg-leaf px-3 py-2 text-sm leading-6 text-ink"
        />
        {reasonRequired ? (
          <p id="screening-reason-required" className="mt-2 text-sm leading-6 text-warning">
            {translate(locale, "screening.reasonRequired")}
          </p>
        ) : null}
      </div>

      <div className="mt-8 border-t border-rule pt-5">
        {/*
          Disabled in every state, and the explanation sits beside it as plain
          text rather than waiting to be earned by a click: the absence of an
          API is a fact about the demonstration, not an error the reader caused.
        */}
        <button
          type="submit"
          disabled
          aria-describedby="screening-submit-disabled"
          className="border border-rule-strong bg-leaf px-4 py-2 text-sm font-medium text-ink disabled:cursor-not-allowed disabled:border-rule disabled:text-ink-faint"
        >
          {translate(locale, "screening.submit")}
        </button>
        <p id="screening-submit-disabled" className="mt-3 text-sm leading-6 text-ink-muted">
          {translate(locale, "screening.submitDisabledExplanation")}
        </p>
        <p className="mt-2 text-sm leading-6 text-ink-faint">
          {translate(locale, "screening.noPersistence")}
        </p>
      </div>
    </form>
  );
}
