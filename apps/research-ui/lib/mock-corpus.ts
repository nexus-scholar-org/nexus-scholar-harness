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
 * The rows carry the same `ui07.corpus-record-v1` shape the console serves, so
 * the demonstration path and the live path render through one row component.
 *
 * The strings deliberately avoid bare word shapes Tailwind compiles as
 * utilities, because `lib/` is inside the stylesheet's source scan and an
 * unexplained utility is reported by `tests-browser/hygiene.spec.ts`.
 */

import type { CorpusRecord } from "./screening-api";

export const demoCorpusIncluded: CorpusRecord[] = [
  {
    shape: "ui07.corpus-record-v1",
    workspace_id: "demo-record-a",
    title: "Aerial imagery for crop and weed separation: an example method study",
    year: 2023,
    provider: "demo index",
    doi: null,
    abstract:
      "Example abstract: the study reports how one aerial imaging method separates crop from weed in a managed field, with the split units and reported metrics described so the steps can be repeated.",
    decision: "INCLUDE",
    confidence: 0.9,
    reasoning:
      "Example reason: the record reports an aerial mapping task on a managed crop.",
    reason_code: "INC-01",
    criterion: "INC-01",
    lane: "mutual_include",
  },
  {
    shape: "ui07.corpus-record-v1",
    workspace_id: "demo-record-b",
    title: "A benchmark dataset for crop and weed segmentation from small aircraft",
    year: 2024,
    provider: "demo index",
    doi: null,
    abstract:
      "Example abstract: a dataset report describing acquisition, annotation and the split boundaries a reader would need before reusing the images.",
    decision: "INCLUDE",
    confidence: 0.8,
    reasoning: "Example reason: the record is a dataset report with a stated task.",
    reason_code: "INC-02",
    criterion: "INC-02",
    lane: "third_lane",
  },
];

export const demoCorpusExcluded: CorpusRecord[] = [
  {
    shape: "ui07.corpus-record-v1",
    workspace_id: "demo-record-c",
    title: "A review of field robotics for weed control",
    year: 2021,
    provider: "demo index",
    doi: null,
    abstract:
      "Example abstract: a narrative overview that synthesizes earlier work rather than reporting a primary study.",
    decision: "EXCLUDE",
    confidence: 0.95,
    reasoning: "Example reason: the record is a review, not a primary report.",
    reason_code: "WRONG_REPORT_TYPE",
    criterion: "EXC-03",
    lane: "mutual_exclude",
  },
  {
    shape: "ui07.corpus-record-v1",
    workspace_id: "demo-record-d",
    title: "Ground robot navigation between crop rows",
    year: 2022,
    provider: "demo index",
    doi: null,
    abstract:
      "Example abstract: navigation and control for a ground vehicle, with no aerial or remote-sensing component.",
    decision: "EXCLUDE",
    confidence: 0.9,
    reasoning:
      "Example reason: the platform is a ground robot, so the record leaves the review platform.",
    reason_code: "WRONG_PLATFORM",
    criterion: "EXC-01",
    lane: "third_lane",
  },
];
