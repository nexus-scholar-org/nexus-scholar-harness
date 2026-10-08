/**
 * Presentation-only types for the project-overview state model (packet UI-02).
 *
 * These are **view models**, not Contract v1 models and not harness artifacts.
 * They describe what a fixture may declare about "where this project is in the
 * evidence workflow" and "did the overview record arrive", in shapes a server
 * component can render. The Python harness remains authoritative for identity,
 * acceptance, refusals and audit events; nothing here computes, infers or mints
 * any of them (see `apps/research-ui/AGENTS.md`).
 *
 * Two axes, kept deliberately apart because they answer different questions:
 *
 * - `record` — has the overview record itself arrived? `loading` means it is
 *   still pending, `error` means the read failed. Neither says anything about
 *   the project, because neither observed the project.
 * - `phase` — only declared once the record arrived (`record: "ready"`). It is
 *   where the project actually stands in the workflow, including the states
 *   that are about the record being thin (`empty`, `degraded`) or about an
 *   authority saying no (`refusal`).
 *
 * The separation is the point: a failed read is **not** a refusal, and a
 * refusal is **not** a failed read. Collapsing them into one "error" token
 * would make the interface report an infrastructure fault as a scientific
 * decision, or vice versa.
 */

/**
 * Where the project stands in the evidence workflow.
 *
 * A frozen token set, exactly like `WorkflowState` in `lib/contracts.ts`: the
 * token is data, the words a reader sees are translated, and a token with no
 * `phase.*` catalog key is a compile error (`i18n/translate.ts`).
 *
 * - `empty` — no project record exists yet; nothing has been searched or judged.
 * - `setup` — protocol and criteria are being written; the workflow starts at
 *   seal.
 * - `search` — records are being discovered and deduplicated.
 * - `screening` — inclusion/exclusion decisions are waiting for a **human**.
 *   The interface never presents a decision that no person made.
 * - `extraction` — included studies are being extracted with their lineage.
 * - `indexing` — extracted passages are being indexed for retrieval.
 * - `refusal` — an authority refused a step; no partial result stands in for it.
 * - `degraded` — part of the record is unavailable; what it does not carry is
 *   shown as unknown rather than guessed.
 * - `ready` — the upstream corpus is assembled and synthesis has not started.
 */
export type ProjectOverviewPhase =
  | "empty"
  | "setup"
  | "search"
  | "screening"
  | "extraction"
  | "indexing"
  | "refusal"
  | "degraded"
  | "ready";

/**
 * Did the overview record arrive?
 *
 * `loading` and `error` are properties of the *read*, not of the project, so
 * they carry no phase: a pending or failed read has observed nothing to report.
 */
export type OverviewRecord = "loading" | "error" | "ready";

/**
 * The corpus statistics the record may carry.
 *
 * Every field is optional and every field is always rendered: a field the
 * fixture does not declare renders the translated `counts.unknown`, never `0`
 * and never a computed remainder (UI-02 negative case — counts are never
 * inferred in the browser).
 */
export type OverviewCountField =
  | "recordsDiscovered"
  | "studiesIncluded"
  | "decisionsPending"
  | "documentsExtracted"
  | "chunksIndexed";

/** Absent field = unknown. The UI must not fill a hole with zero. */
export type OverviewCounts = Partial<Record<OverviewCountField, number>>;

/**
 * A continuation surface the overview may point at by name.
 *
 * The same three ids the primary navigation declares (screening, evidence,
 * audit — packets UI-04/05/06). None of them has a route yet, so the component
 * renders the destination as text plus the "not yet available" annotation and
 * never as a link: a link to a route that does not exist is exactly what the
 * shell's navigation gate forbids.
 */
export type OverviewDestination = "screening" | "evidence" | "audit";

/** The state once the record has arrived: a phase, its counts, and optional prose. */
export interface ProjectOverviewReady {
  readonly record: "ready";
  readonly phase: ProjectOverviewPhase;
  /** Always declared, possibly empty — the component renders every field. */
  readonly counts: OverviewCounts;
  /**
   * Fixture prose about this state (the refusal reason, the degraded extent).
   * Not chrome: rendered byte for byte inside `<bdi>` (D-I18N-02).
   */
  readonly note?: string;
  /** Which surface to continue in, as a nav id; rendered as text, not a link. */
  readonly next?: OverviewDestination;
}

/** The record did not arrive: pending, or the read failed. No phase is known. */
export interface ProjectOverviewUnavailable {
  readonly record: "loading" | "error";
}

/**
 * The whole model: one discriminated union on `record`.
 *
 * A narrowing check on `state.record === "ready"` is the only way to reach
 * `phase`, so a component cannot render a project state it never received.
 */
export type ProjectOverviewState = ProjectOverviewReady | ProjectOverviewUnavailable;
