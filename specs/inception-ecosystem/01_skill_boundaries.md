# 01 · Skill boundaries

The inception phase is orchestrated by a **three-layer stack** over the same
`workspaces/<slug>/` file contract. Each skill owns a distinct concern and
delegates *down* the stack; nothing is re-implemented.

## The stack

```text
inception-agent         (conversation driver — grounded recon, human-in-the-loop)
        │  delegates interview conventions + emission schema
        ▼
methodology-copilot     (classic interview — paradigm → RQs → intent → compile)
        │  delegates state writes
        ▼
workspace-manager       (state layer — scaffold, audit ledger, INDEX.md, tool paths)
```

All three orchestrate the same **`scholar-*` kit skills** / CLIs (`scholar-protocol`,
`scholar-search`, `scholar-pdf`, …) as leaves — they never re-derive kit logic.

## 1. `workspace-manager` — the state layer

**Owns:** where research output lives, and the paper trail for it.

- Scaffolds the canonical layout via `scripts/init_project.py` (title, slug,
  paradigm, RQs) → `workspaces/<slug>/` + `INDEX.md` + `PROJECT_INITIALIZED` audit event.
- Appends to the immutable `audit/journal.jsonl` via `scripts/log_event.py` /
  `scripts/batch_log.py` (single vs batch) — the only sanctioned way to write events.
- Rebuilds `INDEX.md` / `project.json` from filesystem state (`refresh_index_md`,
  `scholar-harness sync`).
- Queries state via `scripts/query_project.py` (`--stats`, `--events`, `--audit-export`).
- Enforces canonical tool paths: every kit command reads/writes inside the active
  workspace; nothing lands in the repo root or `tools/`.

**Does not:** conduct interviews, choose paradigms, or propose research questions.

## 2. `methodology-copilot` — the classic interview

**Owns:** the epistemological interview and the intent→protocol compile.

- Runs the 4-stage Socratic protocol: latent paradigm mining, 4-way refraction
  grid (Positivist / Interpretivist / Pragmatist / Design Science), boundary
  grill (unit of analysis, gold-standard proof, exclusions, lexicon), then RQ
  formulation and `IntentPacket` generation (`intent.json`).
- Emits the canonical artifacts: `scholar-protocol compile --fingerprint` →
  `protocol.json`, `scholar-protocol render-criteria` → `SCREENING_CRITERIA.md`.
- Fast path: the same lifecycle is executed deterministically by the wizard
  (`uv run scholar-harness inception --root <repo>`; `--grounded` for the
  literature-grounded variant) — prefer the wizard over hand-authoring `intent.json`.
- **Grounded mode:** when `inception-agent` drives, this skill supplies the
  *post-direction* interview conventions and the emission schema that Stage 6
  delegates to (see `02_handoffs.md`). Classical (non-grounded) runs are owned
  entirely by this skill.

**Does not:** run the reconnaissance probes, or write to the audit ledger directly
(workspace-manager owns that).

## 3. `inception-agent` — the grounded conversation driver

**Owns:** the grounded lifecycle as a human-in-the-loop chat, and **nothing else**.

- Runs the six-stage flow (frame → probe → distill+directions → gap due-diligence
  → select → remaining interview + emit) via the MCP recon tools (`recon_probe`,
  `recon_distill`, `recon_delta`) and the parity helper
  (`scripts/grounded_directions.py`, which imports the *real* wizard functions).
- Hard contracts it enforces: **anchoring** (every concept carries ≥ 1-2 real DOI
  anchors), **human gate** (nothing emitted without explicit confirmation),
  **byte-identical discipline** (never changes default-facing CLI/MCP behavior).
- Emission is explicitly delegated: `workspace-manager` scripts for scaffold +
  audit, `methodology-copilot` conventions for the interview + `intent.json`/
  compile schema after a direction is chosen.

**Does not:** re-implement taxonomy scoring, re-derive wizard logic, or write
events itself.

## Composition with the wizard

The headless wizard (`scholar_harness.inception.run_wizard`) is the **deterministic
substrate** both skills share: `inception-agent`'s parity helper computes exactly
what the `--grounded` wizard computes, and `methodology-copilot`'s classical flow is
the wizard's non-grounded mode. Agents should therefore prefer the wizard + parity
helper over re-implementing any step by hand.

## Responsibility map

| Concern | Owner |
| :-- | :-- |
| Workspace scaffold + layout | `workspace-manager` (`init_project.py`) |
| Audit ledger / events | `workspace-manager` (`log_event.py`, `batch_log.py`) |
| `INDEX.md` / `project.json` sync | `workspace-manager` (`refresh_index_md`, `scholar-harness sync`) |
| Paradigm refraction + RQs | `methodology-copilot` |
| `intent.json` (IntentPacket) | `methodology-copilot` conventions |
| `protocol.json` + `SCREENING_CRITERIA.md` | `methodology-copilot` → `scholar-protocol` CLIs |
| Literature recon + grounded directions | `inception-agent` → MCP recon tools + parity helper |
| `GENESIS` + `recon_context` provenance | handoff (see `02_handoffs.md`) |