import type { EvidenceNode, WorkflowStage } from "@/lib/contracts";

/**
 * Presentation-only test fixtures.
 *
 * These are not harness artifacts. The `id` values below are React list keys
 * invented for this test file: they are not workspace slugs, study identities,
 * DOIs, artifact IDs, fingerprints, checksums, or contract versions, and no
 * stage here records an inclusion, exclusion, acceptance, or refusal verdict.
 * The UI never mints such decisions; see `apps/research-ui/AGENTS.md`.
 */

/** The four `WorkflowState` values the badge must render distinctly. */
export const ALL_WORKFLOW_STATES = ["complete", "active", "waiting", "refused"] as const;

/**
 * A five-stage sequence that exercises every `WorkflowState`, including
 * `refused`, which `lib/mock-project.ts` never uses.
 *
 * The `refused` row carries the *stage's own* presentation state — the step was
 * stopped — and, like every other row here, it records no verdict about any
 * record: no inclusion, exclusion, acceptance or refusal decision, no
 * identifier, and no refusal code (see the file header). The order is
 * deliberate: states only ever degrade along the sequence, so no later row
 * claims `complete` after an earlier row stopped being complete.
 */
export const ALL_STATES_STAGES: WorkflowStage[] = [
  { id: "fixture-a", label: "Sealed protocol", description: "Question and criteria written down", state: "complete" },
  { id: "fixture-b", label: "Record discovery", description: "Records gathered and deduplicated", state: "complete", count: 143 },
  { id: "fixture-c", label: "Extraction", description: "Extraction in progress", state: "active", count: 18 },
  { id: "fixture-d", label: "Synthesis", description: "Held back pending a decision", state: "waiting" },
  { id: "fixture-e", label: "Document access", description: "Stopped before anything was retrieved", state: "refused" },
];

/** Same stage label, used to isolate the presence/absence of `count`. */
export const STAGE_WITH_COUNT: WorkflowStage = {
  id: "fixture-count",
  label: "Record discovery",
  description: "Records gathered and deduplicated",
  state: "complete",
  count: 143,
};

/** Byte-for-byte the same presentation content as `STAGE_WITH_COUNT`, minus `count`. */
export const STAGE_WITHOUT_COUNT: WorkflowStage = {
  id: "fixture-count",
  label: "Record discovery",
  description: "Records gathered and deduplicated",
  state: "complete",
};

/**
 * Deliberately out of canonical chain order, so an order assertion proves the
 * component follows the input array rather than a hard-coded sequence.
 */
export const OUT_OF_ORDER_NODES: EvidenceNode[] = [
  { kind: "document", label: "Extracted document", detail: "Text derived from an acquired PDF", status: "source" },
  { kind: "claim", label: "Review claim", detail: "Provenance should be inspectable", status: "accepted" },
  { kind: "decision", label: "Screening decision", detail: "A human choice against sealed criteria", status: "reviewed" },
];
