# Agent Handoff Protocol Specification

## 1. Phase Sequence

```
INCEPTION → SCREENING → EXTRACTION → GRAPH → SYNTHESIS → CRITIQUE → COMPLETE
```

Each phase represents a discrete stage in the systematic review pipeline.
The supervisor advances phases automatically when trigger files are detected.

## 2. State-File Trigger Conventions

| Phase | Trigger File(s) | Description |
| :--- | :--- | :--- |
| `INCEPTION` | `intent.json` | Inception interview completed |
| `SCREENING` | `protocol.json` | Protocol finalized; OR `literature/included.json` for screening complete |
| `EXTRACTION` | `literature/extraction/merged/records.json` | Fulltext extraction and merging done |
| `GRAPH` | `literature/knowledge_graph.json` | Citation graph built and PageRank computed |
| `SYNTHESIS` | `synthesis/consensus.json` | Grounded synthesis and consensus reached |
| `CRITIQUE` | `phase4/methodological_critique.md` | Methodology critique generated |
| `COMPLETE` | *(terminal)* | All phases completed |

### Trigger Resolution

- A phase is considered **completed** when **all** its trigger files exist and are non-empty.
- The `SCREENING` phase triggers on `literature/included.json` (the PRISMA collect handoff artifact).
- A phase may have **alternative triggers** (pipe-separated); any single match suffices.

## 3. `handoff_state.json` Schema

```json
{
  "current_phase": "SCREENING",
  "completed_phases": ["INCEPTION"],
  "workspace_dir": "/path/to/workspace",
  "updated_at": "2026-09-15T12:00:00+00:00"
}
```

| Field | Type | Description |
| :--- | :--- | :--- |
| `current_phase` | `str` | The phase currently in progress |
| `completed_phases` | `list[str]` | Phases that have been completed and verified |
| `workspace_dir` | `str` | Absolute path to the workspace |
| `updated_at` | `str` | ISO-8601 timestamp of last state update |

## 4. Supervisor Loop Behavior

1. **Load** `handoff_state.json` from workspace (or create default initial state).
2. **Scan** workspace filesystem for trigger files defined in `PHASE_TRIGGERS`.
3. **Compute** which phases are completed based on trigger file existence.
4. **Advance** to the next actionable phase (first phase in sequence whose prerequisites are met but not yet completed).
5. **Save** updated `handoff_state.json`.
6. **Emit** audit event to `audit/journal.jsonl`.
7. **Return** summary dict with `{action, from_phase, to_phase, completed_phases}`.

### Edge Cases

- **Missing workspace dir**: return empty set, no state change.
- **Malformed JSON**: return current state unchanged, log warning.
- **All phases complete**: return terminal state, no-op.
- **No trigger files found**: return current state unchanged.

## 5. Transition Table

| From | To | Trigger |
| :--- | :--- | :--- |
| `INCEPTION` | `SCREENING` | `intent.json` exists |
| `SCREENING` | `EXTRACTION` | `literature/included.json` exists |
| `EXTRACTION` | `GRAPH` | `literature/extraction/merged/records.json` exists |
| `GRAPH` | `SYNTHESIS` | `literature/knowledge_graph.json` exists |
| `SYNTHESIS` | `CRITIQUE` | `synthesis/consensus.json` exists |
| `CRITIQUE` | `COMPLETE` | `phase4/methodological_critique.md` exists |
