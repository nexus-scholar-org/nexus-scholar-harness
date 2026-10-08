import type {
  ProjectOverviewReady,
  ProjectOverviewState,
} from "./project-state";

/**
 * Fixture-backed states for the project-overview record (packet UI-02).
 *
 * **Demonstration data.** These are presentation fixtures, not harness
 * artifacts: no identifier, fingerprint, checksum, acceptance result or refusal
 * code is minted here, and nothing in this file is, or claims to be, a live API
 * response. The shell's visible `Demonstration data` label covers them.
 *
 * Two rules the fixtures obey, and which `tests/project-state-record.test.tsx`
 * checks mechanically:
 *
 * 1. **Counts are only ever copied from the frozen demonstration corpus**
 *    (`lib/mock-project.ts`: 143 discovered, 18 included/extracted) or left
 *    absent. Nothing is computed, summed or inferred — an absent field renders
 *    `counts.unknown`, never `0`. Note that even the `ready` fixture leaves
 *    `decisionsPending` and `chunksIndexed` absent: the record carries what it
 *    carries, and the presentation layer does not fill the holes.
 * 2. **`note` is fixture prose**, rendered byte for byte inside `<bdi>`, so an
 *    English sentence stays English inside a right-to-left document
 *    (D-I18N-02). It never contains an identifier or a refusal code — a code is
 *    authoritative vocabulary the UI may not invent.
 *
 * `lib/mock-project.ts` and `lib/contracts.ts` are byte-pinned by
 * `tests/i18n-catalog.test.ts`, which is why this model lives in new files
 * rather than being added to them.
 */

const CORPUS = {
  recordsDiscovered: 143,
  studiesIncluded: 18,
  documentsExtracted: 18,
} as const;

/** The record has not arrived yet. No phase is known, so none is declared. */
export const loadingOverviewState: ProjectOverviewState = { record: "loading" };

/** The read failed. A failed read is not a refusal, and carries no phase. */
export const errorOverviewState: ProjectOverviewState = { record: "error" };

/** No project yet: the record arrived and says there is nothing to show. */
const emptyState: ProjectOverviewReady = {
  record: "ready",
  phase: "empty",
  counts: {},
};

/** Protocol and criteria being written; no corpus exists yet. */
const setupState: ProjectOverviewReady = {
  record: "ready",
  phase: "setup",
  counts: {},
};

/** Records discovered; how many remain to be judged is not carried. */
const searchState: ProjectOverviewReady = {
  record: "ready",
  phase: "search",
  counts: { recordsDiscovered: CORPUS.recordsDiscovered },
  next: "screening",
};

/**
 * Screening, waiting for a human. `decisionsPending` is deliberately absent:
 * the fixture does not know how many decisions remain, so the interface must
 * render `unknown` rather than invent a backlog or a zero.
 */
const screeningState: ProjectOverviewReady = {
  record: "ready",
  phase: "screening",
  counts: { recordsDiscovered: CORPUS.recordsDiscovered },
  next: "screening",
};

/** Extraction of the included studies, with lineage kept back to the source. */
const extractionState: ProjectOverviewReady = {
  record: "ready",
  phase: "extraction",
  counts: {
    recordsDiscovered: CORPUS.recordsDiscovered,
    studiesIncluded: CORPUS.studiesIncluded,
  },
  next: "evidence",
};

/**
 * Indexing the extracted passages. `chunksIndexed` is absent on purpose: this
 * is the state where a reader is most likely to expect a number, and the
 * fixture does not carry one.
 */
const indexingState: ProjectOverviewReady = {
  record: "ready",
  phase: "indexing",
  counts: { documentsExtracted: CORPUS.documentsExtracted },
  next: "evidence",
};

/** A step was refused by the authority that runs it. No partial result stands. */
const refusalState: ProjectOverviewReady = {
  record: "ready",
  phase: "refusal",
  counts: {},
  note: "The record source refused the request, so no partial result was accepted in its place.",
  next: "audit",
};

/** Part of the record is unreachable; what it does not carry stays unknown. */
const degradedState: ProjectOverviewReady = {
  record: "ready",
  phase: "degraded",
  counts: { recordsDiscovered: CORPUS.recordsDiscovered },
  note: "One record source is unreachable, so the statistics it would carry are absent.",
  next: "audit",
};

/**
 * The state the overview route renders.
 *
 * `ready`, because the frozen demonstration corpus has completed screening,
 * full text and extraction while its grounded report has not started — which is
 * exactly what `lib/mock-project.ts` says (`synthesis`: `waiting`, "Grounded
 * report not started"). `tests/project-state-record.test.tsx` reconciles this
 * fixture's counts against the frozen stage counts so the two cannot drift.
 */
export const demoOverviewState: ProjectOverviewReady = {
  record: "ready",
  phase: "ready",
  counts: {
    recordsDiscovered: CORPUS.recordsDiscovered,
    studiesIncluded: CORPUS.studiesIncluded,
    documentsExtracted: CORPUS.documentsExtracted,
  },
  next: "evidence",
};

/**
 * Every fixture, keyed by a stable name, for the state-matrix test.
 *
 * Eleven entries: the two record-arrival states plus the nine phases. The keys
 * are test vocabulary, not product data.
 */
export const overviewStateFixtures: Readonly<Record<string, ProjectOverviewState>> = {
  loading: loadingOverviewState,
  error: errorOverviewState,
  empty: emptyState,
  setup: setupState,
  search: searchState,
  screening: screeningState,
  extraction: extractionState,
  indexing: indexingState,
  refusal: refusalState,
  degraded: degradedState,
  ready: demoOverviewState,
};

/** The nine phase fixtures, in declaration order, for matrix assertions. */
export const readyOverviewStateFixtures: readonly ProjectOverviewReady[] = [
  emptyState,
  setupState,
  searchState,
  screeningState,
  extractionState,
  indexingState,
  refusalState,
  degradedState,
  demoOverviewState,
];
