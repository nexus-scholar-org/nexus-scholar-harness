/**
 * Demonstration rows for the corpus screen (packet UI-08).
 *
 * **Demonstration data.** Like `lib/mock-screening.ts`, these are presentation
 * fixtures and nothing more: the shell's visible `Demonstration data` marker
 * covers them, no identifier or fingerprint is minted here, and no row claims
 * to be a live workspace record.
 *
 * Two rules this file obeys, mirroring the screening fixture's reasoning:
 *
 * 1. **No identifiers.** No DOI, accession number, project slug or contract id
 *    appears, so no fixture row can be mistaken for a canonical identity.
 * 2. **Prose that reads as an example.** Titles and reasons describe the shape
 *    of a screening corpus (a decision, the criterion it cites, the lane that
 *    produced it) without asserting a result about any real study.
 *
 * The strings deliberately avoid bare word shapes Tailwind compiles as
 * utilities, because `lib/` is inside the stylesheet's source scan and an
 * unexplained utility is reported by `tests-browser/hygiene.spec.ts`.
 */

import type { CorpusRecord } from "./screening-api";

export const demoCorpusIncluded: CorpusRecord[] = [
  {
    workspace_id: "demo-record-a",
    title: "Aerial imagery for crop and weed separation: an example method study",
    year: 2023,
    provider: "demo index",
    doi: null,
    abstract:
      "Example abstract: the study reports how one aerial imaging method separates crop from weed in a managed field, with the split units and reported metrics described so the steps can be repeated.",
    screening: {
      workspace_id: "demo-record-a",
      decision: "INCLUDE",
      confidence: 0.9,
      screening_reasoning:
        "Example reason: the record reports an aerial mapping task on a managed crop.",
      matched_inclusion_criteria: ["INC-01"],
      violated_exclusion_criteria: [],
    },
    screening_provenance: { lane: "mutual_include", reason_code: "INC-01" },
  },
  {
    workspace_id: "demo-record-b",
    title: "A benchmark dataset for crop and weed segmentation from small aircraft",
    year: 2024,
    provider: "demo index",
    doi: null,
    abstract:
      "Example abstract: a dataset report describing acquisition, annotation and the split boundaries a reader would need before reusing the images.",
    screening: {
      workspace_id: "demo-record-b",
      decision: "INCLUDE",
      confidence: 0.8,
      screening_reasoning: "Example reason: the record is a dataset report with a stated task.",
      matched_inclusion_criteria: ["INC-01", "INC-02"],
      violated_exclusion_criteria: [],
    },
    screening_provenance: { lane: "third_lane", reason_code: "INC-02" },
  },
];

export const demoCorpusExcluded: CorpusRecord[] = [
  {
    workspace_id: "demo-record-c",
    title: "A review of field robotics for weed control",
    year: 2021,
    provider: "demo index",
    doi: null,
    abstract:
      "Example abstract: a narrative overview that synthesizes earlier work rather than reporting a primary study.",
    screening: {
      workspace_id: "demo-record-c",
      decision: "EXCLUDE",
      confidence: 0.95,
      screening_reasoning: "Example reason: the record is a review, not a primary report.",
      matched_inclusion_criteria: [],
      violated_exclusion_criteria: ["EXC-03"],
    },
    screening_provenance: { lane: "mutual_exclude", reason_code: "WRONG_REPORT_TYPE" },
  },
  {
    workspace_id: "demo-record-d",
    title: "Ground robot navigation between crop rows",
    year: 2022,
    provider: "demo index",
    doi: null,
    abstract:
      "Example abstract: navigation and control for a ground vehicle, with no aerial or remote-sensing component.",
    screening: {
      workspace_id: "demo-record-d",
      decision: "EXCLUDE",
      confidence: 0.9,
      screening_reasoning:
        "Example reason: the platform is a ground robot, so the record leaves the review platform.",
      matched_inclusion_criteria: [],
      violated_exclusion_criteria: ["EXC-01"],
    },
    screening_provenance: { lane: "third_lane", reason_code: "WRONG_PLATFORM" },
  },
];
