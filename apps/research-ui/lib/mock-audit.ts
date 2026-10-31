/**
 * Demonstration events for the audit screen (packet UI-06).
 *
 * **Demonstration data.** Like `lib/mock-screening.ts` and `lib/mock-corpus.ts`
 * these are presentation fixtures covered by the shell's visible
 * `Demonstration data` marker. Three rules:
 *
 * 1. **No minted identifiers.** `event_id` is `null` in every row: the page
 *    then renders the "not recorded" wording, which is also a real state the
 *    console produces when a journal line carries no id. Nothing here can be
 *    mistaken for a canonical event id.
 * 2. **No workspace claims.** The actions are generic vocabulary, the
 *    descriptions read as examples, and the timestamps are fixed literal
 *    strings rather than "now".
 * 3. **Mixed outcomes.** One event is `FAILED` so the presentation of a
 *    non-success outcome is exercised, not just the happy path.
 */

import type { AuditFeedItem } from "./screening-api";

export const demoAuditEvents: AuditFeedItem[] = [
  {
    timestamp: "2026-01-04T09:12:41.512000+00:00",
    event_id: null,
    action: "DISCOVERY_SEARCH",
    agent_or_tool: "example search agent",
    description:
      "Example event: a federated search ran across the configured indexes and stored its raw hits.",
    status: "SUCCESS",
  },
  {
    timestamp: "2026-01-04T09:40:03.004000+00:00",
    event_id: null,
    action: "DEDUP_COMPLETED",
    agent_or_tool: "example dedup step",
    description: "Example event: duplicate records were merged and the surviving set was recorded.",
    status: "SUCCESS",
  },
  {
    timestamp: "2026-01-04T11:02:57.889000+00:00",
    event_id: null,
    action: "SCREENING_STARTED",
    agent_or_tool: "example screener",
    description: "Example event: a screening batch was prepared for review.",
    status: "SUCCESS",
  },
  {
    timestamp: "2026-01-04T11:31:18.201000+00:00",
    event_id: null,
    action: "SCREENING_DECISION_REJECTED",
    agent_or_tool: "example screener",
    description:
      "Example event: a decision was refused because its record was not part of the batch.",
    status: "FAILED",
  },
  {
    timestamp: "2026-01-05T08:15:44.730000+00:00",
    event_id: null,
    action: "SCREENING_FINALIZED",
    agent_or_tool: "example screener",
    description:
      "Example event: the reviewed decisions were reconciled into one final set for the corpus.",
    status: "SUCCESS",
  },
];
