# uav-pilot-demo — Clean Demonstration Rerun

## Purpose

This workspace is a **clean demonstration rerun** scaffolded for testing and
demonstration purposes. It carries over **only the frozen provisional inputs**
(protocol v0.2, query calibration, sentinels, researcher decisions) from the
pilot workspace. It contains **no search results, no screening decisions, and
no findings**.

## Non-goals (explicit)

- **Not findings**: no factual claims about the literature exist anywhere in
  this workspace.
- **Not frozen**: the protocol is `PROVISIONAL_NOT_FROZEN` (revision 0.2);
  no freeze was performed here.
- **Not screening**: no screening batches, decisions, or adjudications were
  run or copied.
- **Not registered**: `registered_workspace_id` is `null`. This is an
  unregistered demo workspace; never claim registration.
- **No search executed**: neither the formal corpus search nor any
  calibration search was executed in this workspace (`search_executed=false`,
  `calibration_search_executed=false`).

## Origin

- Pilot workspace (read-only source):
  `C:\Users\mouadh\Documents\nexus-scholar-harness\workspaces\uav-crop-weed-reliability`
  (working tree, 2026-10-15).
- `protocol.json`, `protocol.sha256`, and `validation.json` (along with the
  other inputs below) are **byte-identical copies** of the pilot files —
  verified by sha256 comparison — not new protocol work.

## Input manifest

| File (demo workspace) | Source path (pilot) | sha256 (short) |
| :--- | :--- | :--- |
| `protocol.json` | `workspaces/uav-crop-weed-reliability/protocol.json` | `a1fd8d2a82e0` |
| `protocol.sha256` | `workspaces/uav-crop-weed-reliability/protocol.sha256` | `6c061042b3b3` |
| `validation.json` | `workspaces/uav-crop-weed-reliability/validation.json` | `a9fe86af2e95` |
| `intent.json` | `workspaces/uav-crop-weed-reliability/intent.json` | `3af21ee5afb5` |
| `SCREENING_CRITERIA.md` | `workspaces/uav-crop-weed-reliability/SCREENING_CRITERIA.md` | `e85c109ccc4d` |
| `SEARCH_STRATEGY.md` | `workspaces/uav-crop-weed-reliability/SEARCH_STRATEGY.md` | `0308d9557da1` |
| `RESEARCHER_DECISIONS.md` | `workspaces/uav-crop-weed-reliability/RESEARCHER_DECISIONS.md` | `99772c9edd78` |
| `calibration/QUERIES.md` | `workspaces/uav-crop-weed-reliability/calibration/QUERIES.md` | `fe012f6c3514` |
| `calibration/SENTINELS.md` | `workspaces/uav-crop-weed-reliability/calibration/SENTINELS.md` | `bbe599db7a3d` |

Deliberately **not** copied: any `search_execution*`, `search_union*`,
`HARVEST*`, `QUALITY*`, pilot `INDEX.md`, or pilot `audit/journal.jsonl`
content.

## Next step

A keyed 5-provider harvest is a separate future task; it is out of scope for
this scaffolding.
