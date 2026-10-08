import type {
  OverviewCountField,
  ProjectOverviewReady,
  ProjectOverviewState,
} from "@/lib/project-state";

import {
  countKey,
  formatNumber,
  navKey,
  phaseDescriptionKey,
  phaseKey,
  translate,
  type Locale,
} from "@/i18n";

/**
 * The current-stage record (packet UI-02).
 *
 * A project-overview state model with two deliberately separate axes, so the
 * interface can answer "what is happening to this project?" and "did we even
 * get an answer?" without ever confusing one for the other:
 *
 * - **Record arrival** — `loading` (not yet), `error` (the read failed),
 *   `ready` (we have it). A failed read is *not* a refusal: the error branch
 *   renders the `overview.recordError` copy, never `state.refused` and never a
 *   phase stamp, because nothing observed the project in that branch.
 * - **Workflow phase** — only once the record arrived: `empty`, `setup`,
 *   `search`, `screening`, `extraction`, `indexing`, `refusal`, `degraded`,
 *   `ready`. A refusal *is* a project state (an authority said no) and renders
 *   as one, with its fixture reason isolated in `<bdi>` — distinct from the
 *   failed read beside it.
 *
 * **Counts are never inferred.** All five statistics are always rendered; a
 * field the fixture does not carry reads the translated `counts.unknown`, never
 * `0`, never a computed remainder. That is the packet's negative case, and the
 * value cell is where it lives: `state.counts[field]` is either a fixture
 * number or it is not there.
 *
 * **Text before colour.** Every state is a stamped word first — the same
 * provenance-stamp shape `components/status-badge.tsx` established, with the
 * hue secondary — so the nine phases are distinguishable in greyscale, to a
 * screen reader, and in a translation. The dot inside each stamp is
 * `aria-hidden`, so the stamp's accessible name is exactly the word.
 *
 * **No route is promised.** When a fixture names a continuation surface the
 * record renders its translated label as text plus the "not yet available"
 * annotation — never a link, because screening/evidence/audit have no route
 * yet and a dead link is precisely what the shell's navigation gate forbids.
 *
 * Layout uses logical properties only (leading/trailing, not left/right), so
 * the record mirrors intact under `dir="rtl"` — enforced by
 * `tests/i18n-direction-source.test.ts`.
 */

/** The stamp shape, byte-identical in spirit to the workflow state stamp. */
const STAMP_SHAPE =
  "inline-flex items-center gap-1.5 border px-2 py-0.5 text-[0.6875rem] font-medium uppercase leading-4 tracking-[0.12em] rtl:tracking-normal rtl:text-[0.75rem]";

/** The marginal annotation used next to a surface that has no route yet. */
const TAG_SHAPE =
  "border border-rule-strong px-1.5 py-0.5 text-[0.6875rem] font-medium uppercase leading-4 tracking-[0.12em] text-ink-faint rtl:tracking-normal rtl:text-[0.75rem]";

/**
 * Phase → hue. Secondary to the word, never a substitute for it.
 *
 * The four semantic hues of the visual direction carry the four readings:
 * ink-blue for running stages, ochre for waiting states (setup, screening,
 * degraded), oxide for refusal, green for ready, and the neutral rule/ink pair
 * for "there is nothing here yet".
 */
const PHASE_STYLES: Readonly<Record<ProjectOverviewReady["phase"], string>> = {
  empty: "border-rule-strong text-ink-muted",
  setup: "border-warning/45 text-warning",
  search: "border-evidence/45 text-evidence",
  screening: "border-warning/45 text-warning",
  extraction: "border-evidence/45 text-evidence",
  indexing: "border-evidence/45 text-evidence",
  refusal: "border-refusal/45 text-refusal",
  degraded: "border-warning/45 text-warning",
  ready: "border-success/45 text-success",
};

/**
 * The statistics, always all five, in a fixed reading order.
 *
 * The fixture decides the *values*; this decides only which rows exist, so
 * every state presents the same record shape and a reader learns where to look
 * for a number — including for the number nobody has.
 */
const COUNT_FIELDS: readonly OverviewCountField[] = [
  "recordsDiscovered",
  "studiesIncluded",
  "decisionsPending",
  "documentsExtracted",
  "chunksIndexed",
];

export function ProjectStateRecord({
  locale,
  state,
}: Readonly<{ locale: Locale; state: ProjectOverviewState }>) {
  return (
    <section aria-labelledby="project-state-title">
      <div className="mb-5">
        <h2 id="project-state-title" className="font-display text-xl leading-8 text-ink">
          {translate(locale, "overview.stateHeading")}
        </h2>
        <p className="mt-1 max-w-3xl text-sm leading-6 text-ink-muted">
          {translate(locale, "overview.stateLede")}
        </p>
      </div>
      {state.record === "ready" ? (
        <ReadyRecord locale={locale} state={state} />
      ) : (
        <UnarrivedRecord locale={locale} state={state} />
      )}
    </section>
  );
}

/**
 * The record has not arrived: pending, or the read failed.
 *
 * Neither branch may render a phase — no phase was observed — and neither may
 * render a count, because there is nothing to count from. The distinction is
 * carried by the stamped word and the sentence below it, not by the hue alone.
 */
function UnarrivedRecord({
  locale,
  state,
}: Readonly<{ locale: Locale; state: Extract<ProjectOverviewState, { record: "loading" | "error" }> }>) {
  const loading = state.record === "loading";
  return (
    <div className="border-s-2 border-rule-strong ps-5">
      <span
        className={`${STAMP_SHAPE} ${
          loading ? "border-rule-strong text-ink-muted" : "border-refusal/45 text-refusal"
        }`}
      >
        <span aria-hidden="true" className="size-1.5 rounded-full bg-current" />
        {translate(locale, loading ? "overview.recordLoadingLabel" : "overview.recordErrorLabel")}
      </span>
      <p className="mt-3 max-w-3xl text-sm leading-6 text-ink-muted">
        {translate(locale, loading ? "overview.recordLoading" : "overview.recordError")}
      </p>
    </div>
  );
}

/**
 * The arrived record: phase, explanation, optional fixture note, continuation
 * surface, and the five statistics.
 *
 * Fixture prose (`note`) is the record's own words, so it sits inside `<bdi>`
 * byte for byte; everything else is catalogued chrome rendered as plain text,
 * and the numerals are `Intl` output rendered bare — the two halves of the
 * translation boundary in `docs/I18N.md` §3, one element at a time.
 */
function ReadyRecord({
  locale,
  state,
}: Readonly<{ locale: Locale; state: ProjectOverviewReady }>) {
  return (
    <div className="grid gap-x-10 gap-y-6 lg:grid-cols-[minmax(0,1fr)_22rem]">
      <div className="min-w-0">
        <span className={`${STAMP_SHAPE} ${PHASE_STYLES[state.phase]}`}>
          <span aria-hidden="true" className="size-1.5 rounded-full bg-current" />
          {translate(locale, phaseKey(state.phase))}
        </span>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-ink-muted">
          {translate(locale, phaseDescriptionKey(state.phase))}
        </p>
        {state.note ? (
          <p className="mt-3 max-w-3xl border-s border-rule-strong ps-4 text-sm leading-6 text-ink-muted">
            <bdi>{state.note}</bdi>
          </p>
        ) : null}
        {state.next ? (
          <p className="mt-3 flex flex-wrap items-center gap-2 text-sm leading-6 text-ink">
            {translate(locale, "overview.nextDestination", {
              destination: translate(locale, navKey(state.next)),
            })}
            <span className={TAG_SHAPE}>{translate(locale, "nav.unavailable")}</span>
          </p>
        ) : null}
      </div>

      <div className="min-w-0 self-start">
        <p className="text-[0.6875rem] uppercase leading-5 tracking-[0.16em] text-evidence rtl:tracking-normal rtl:text-[0.75rem]">
          {translate(locale, "counts.heading")}
        </p>
        <div className="mt-2 border-t border-rule-strong">
          {COUNT_FIELDS.map((field) => {
            const value = state.counts[field];
            return (
              <div
                key={field}
                className="grid grid-cols-[minmax(0,1fr)_auto] items-baseline gap-x-4 border-b border-rule py-2"
              >
                <p className="text-sm leading-6 text-ink-muted">{translate(locale, countKey(field))}</p>
                {/*
                  The negative case, in one cell: a field the fixture does not
                  carry renders the translated "unknown" — never 0, never a
                  remainder computed here. A present value is `Intl` output in
                  this locale's own digits and is deliberately not wrapped for
                  bidirection, because a locale-native numeral already sits in
                  the document's own direction.
                */}
                <p
                  className={`text-end text-sm leading-6 ${
                    value !== undefined ? "text-ink" : "text-ink-faint"
                  }`}
                >
                  {value !== undefined ? formatNumber(locale, value) : translate(locale, "counts.unknown")}
                </p>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
