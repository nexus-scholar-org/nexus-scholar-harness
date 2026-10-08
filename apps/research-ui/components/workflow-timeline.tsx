import { ArrowPathIcon, CheckCircleIcon, ClockIcon, NoSymbolIcon } from "@heroicons/react/24/outline";

import type { WorkflowStage, WorkflowState } from "@/lib/contracts";

import { formatNumber, translate, translateParts, type Locale } from "@/i18n";

import { StatusBadge } from "./status-badge";

/**
 * The workflow record (packet UI-01c, acceptance A13; localized in UI-01d).
 *
 * This was a `grid` of six interchangeable rounded cards, each carrying a soft
 * drop shadow. It is
 * now ONE record: a single ruled table of the kind a review keeps on paper, with
 * a hairline between entries, a heavier rule above and below the whole
 * sequence, a marginal `Stage N` ordinal, and the state stamp and count set in
 * their own column.
 *
 * Nothing was removed to achieve that. Every stage still renders its marginal
 * ordinal, its label as a level-3 heading, its description, its state stamp
 * and — where the fixture declares one — its count, in that order, and
 * `tests/workflow-timeline.test.tsx` still finds each of them scoped to its own
 * `<li>`.
 *
 * At 375px the columns collapse into label/description first and stamp/count
 * second, still as one entry rather than as a stack of cards; at 1440px all
 * three sit on one baseline, which is what makes the sequence read as a record
 * instead of a row of tiles.
 *
 * **What the locale prop changes, and what it must not (packet UI-01d).** Three
 * things are the product's and are translated: the list's accessible name, the
 * ordinal's `Stage {number}` template, and the state stamp's word. Two are the
 * record's and are not: the stage label and its description stay byte for byte
 * inside `<bdi>`, so a translated row is visibly a translated row wrapped around
 * the fixture's own text (D-I18N-02). The count is neither — it is fixture data
 * that happens to be a number, so it goes through `Intl` (F02) and is also
 * isolated, because a formatted numeral inside a right-to-left row is exactly the
 * run the bidirectional algorithm will reorder if nothing isolates it (N19).
 *
 * The ordinal is the one number that is *not* wrapped in `<bdi>`: it is the
 * sequence marker, it is generated rather than read from the fixture, and
 * `tests/evidence-chain.test.tsx` reads its parent's first element child as bare
 * text. `Intl` gives it the locale's digits and its position in the row gives it
 * its direction.
 *
 * **The icon is a second channel, never a replacement (packet UI-03).** Each
 * stamp cell opens with a shape that names the state before the word is read —
 * a check for `complete`, a rotating path for `active`, a clock for `waiting`
 * and a barred circle for `refused`. It is `aria-hidden`, it carries the
 * canonical state token in `data-stage-state-icon`, and all four take the
 * *same* `text-ink-muted` role: the shapes differ while the tone does not, so
 * this file introduces no second state-to-colour definition and
 * `components/status-badge.tsx` stays the application's only one (D2). What a
 * reader acts on is still the stamp's word (P3) — the icon accompanies it, and
 * none of the four shapes is mirrored in a right-to-left document (D-I18N-09,
 * decision recorded in `docs/UI-03_CONTEXT_CAPSULE.md`).
 */

/**
 * The four state shapes, keyed by the canonical token.
 *
 * This is a shape map, not a colour map: every entry is rendered with one
 * identical class string, and `tests/workflow-timeline-state-matrix.test.tsx`
 * asserts both properties (the four rendered markups are mutually distinct, and
 * their class strings are not).
 */
const stateIcon: Record<WorkflowState, typeof CheckCircleIcon> = {
  complete: CheckCircleIcon,
  active: ArrowPathIcon,
  waiting: ClockIcon,
  refused: NoSymbolIcon,
};

export function WorkflowTimeline({
  stages,
  locale,
}: {
  stages: WorkflowStage[];
  locale: Locale;
}) {
  return (
    <ol
      className="border-t border-rule-strong"
      aria-label={translate(locale, "workflow.listLabel")}
    >
      {stages.map((stage, index) => {
        const StateIcon = stateIcon[stage.state];
        return (
          <li
            key={stage.id}
            className="grid grid-cols-[4.25rem_minmax(0,1fr)] gap-x-4 gap-y-2 border-b border-rule py-4 lg:grid-cols-[4.25rem_minmax(0,1fr)_6.5rem] lg:items-baseline"
          >
            {/* Marginal ordinal. A real text node, not a CSS counter. */}
            <p className="text-[0.6875rem] uppercase leading-4 tracking-[0.16em] text-ink-faint rtl:tracking-normal rtl:text-[0.75rem]">
              {translateParts(locale, "workflow.stageOrdinal", { number: formatNumber(locale, index + 1) }).map(
                (part, i) =>
                  part.kind === "text" ? (
                    <span key={i}>{part.value}</span>
                  ) : (
                    <bdi key={i}>{part.value}</bdi>
                  )
              )}
            </p>

            <div className="min-w-0">
              <h3 className="text-base font-medium text-ink">
                <bdi>{stage.label}</bdi>
              </h3>
              <p className="mt-1 text-sm leading-6 text-ink-muted">
                <bdi>{stage.description}</bdi>
              </p>
            </div>

            <div className="col-start-2 flex items-center gap-3 lg:col-start-3 lg:flex-col lg:items-start lg:gap-2">
              {/*
                The shape channel (packet UI-03). It opens the stamp cell so the
                row reads shape-then-word, it is `aria-hidden` so the accessible
                text of the row is unchanged, and `data-stage-state-icon` is the
                hook the state-matrix test and the 375px browser check both read
                — a locale-stable handle, in the D-I18N-10 sense, because it
                names the canonical token rather than any translation of it.
              */}
              <StateIcon
                aria-hidden="true"
                data-stage-state-icon={stage.state}
                className="size-4 shrink-0 text-ink-muted"
              />
              <StatusBadge locale={locale} state={stage.state} />
              {stage.count !== undefined ? (
                <p className="text-lg leading-6 text-ink-muted">
                  {/*
                    A count is generated by `Intl` in this locale's own digits, not
                    read out of the frozen record, so it is chrome rather than
                    fixture bytes and is deliberately *not* wrapped in `<bdi>`. The
                    isolation rule is about preserving the record's own text
                    verbatim; a locale-native numeral is already in the document's
                    own direction, and wrapping it would obscure the very distinction
                    this markup exists to draw.
                  */}
                  {formatNumber(locale, stage.count)}
                </p>
              ) : null}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
