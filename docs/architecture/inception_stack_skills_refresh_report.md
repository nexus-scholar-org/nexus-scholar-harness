# Inception-Stack Skills Refresh Report

**Task:** INCEPTION-STACK-SKILLS-REFRESH · **Lane:** FAST (documentation-only, no runtime change)
**Base:** `8448dfdbec4e1d888bf0e07a05cb5a3b455b395d` (`origin/main`, post-#80) · **Branch:** `cdx/inception-stack-skills-refresh`
**Worktree:** `C:/Users/mouadh/AppData/Local/Temp/opencode/inception-stack-skills-refresh` (isolated; primary + HCM worktrees untouched)
**Primary dirty baseline (preserved):** `M .opencode/agent/reviewer.md`, `M apps/research-ui/{AGENTS.md,README.md,docs/GATES.md,tests/*.test.tsx}`, `M docs/architecture/research_ui/AGENT_WORK_PACKETS.md`

## Scope

- **Allowed (changed):** `.agents/skills/{inception-agent,methodology-copilot,workspace-manager}/**/*.md` + byte-identical mirrors via `scripts/sync_skills_bundle.py` + this report. Helper `scripts/*.py` were read-only verification sources.
- **Immutable (untouched):** runtime code, helper scripts, `tools/**/`, pins (`plugins.json` unchanged since the last refresh — empty diff), dependencies, contracts, fixtures, UI, HCM docs, agent permissions, research workspaces.
- **Ownership:** harness surface only (`nexus-scholar-org/nexus-scholar-harness`). No `BLOCKED_CANONICAL_REPO`.

## Verified corrections

All examples below were verified against committed source before editing (live `--help` where side-effect-free, else exact argparse/Typer source reads — disclosed per file).

### All three skills
- `init_project.py` positional `title` (`scripts/init_project.py:184`; `--slug/-s`, `--description/-d`, `--paradigm/-p`, `--rq` repeatable, `--keyword/-k`, `--root` default `.`): every `--title` example corrected.
- `log_event.py` has **no `--metrics` CLI flag** (`:227-233`: positional `project`, required `--action`, `--agent`, `--description`, `--inputs/--outputs`, `--status`; `metrics` is a Python kwarg only at `:167`): unsupported examples removed; supported CLI alternative (`--inputs/--outputs/--status`, events file) or the Python-kwarg alternative documented.
- `scholar-protocol compile` / `render-criteria`: positional input + stdout, no `-i`/`-o`/`--fingerprint` (fingerprint is a separate command): all invented-flag examples corrected.
- Obsolete `src/scholar_harness/inception.py` references → verified package paths (`inception/wizard.py`, `inception/grounded.py`, `inception/genesis.py`, `inception/display.py`).
- `registered_workspace_id` (`WSP-` + 32 hex, minted once at init, recorded and preserved — slug is a label, never identity) vs human project slug explained in each skill.

### inception-agent (SKILL.md, 121→156 lines)
- Emission example fixed to positional title; parity-helper usage completed (`--terms`/`--topic` required, `--pool` optional, `--direction` emission variant with exit-2-on-mismatch, `--max-default-concepts` note); identity paragraph added; boundaries hardened (sparsity ≠ gap, proposal vs candidate vs accepted, dry-run writes nothing, generic ledger ≠ GENESIS publication); task-routing table + headless fallback flags; HCM-02/05 revisit pointer; volatile gate literals replaced with threshold-agnostic labels.

### methodology-copilot (SKILL.md + 4 refs, net −56 lines)
- Wizard fast-path flags verified (`--root/--grounded/--no-scaffold`, headless `--auto-select/--direction-id`); dead `docs/phase_0/04_socratic_inception_protocol.md` link → `specs/inception-ecosystem/`; legacy `literature/criteria.md` hand-write → root `SCREENING_CRITERIA.md` via renderer; fictional `performance_caching.md` runtime (`ParadigmRefractor`, `scripts/interview.py`, template cache — all verified absent) replaced with no-runtime note + supported seams.

### workspace-manager (SKILL.md + 4 refs)
- INDEX.md format corrected to committed `refresh_index_md` headings/labels/conditionals/catalog rule; manifest example corrected to committed `init_project.py:133-152` shape; lifecycle layout canonicalized (`intent.json`/`protocol.json`/`SCREENING_CRITERIA.md`/`phase4`; non-existent `verification_audit.json` removed); routing-matrix rows 8–9 fixed (RAG indexing MCP-unavailable → `scholar-rag index`); `performance_concurrency.md` purged of unwritten module/class/flags/scripts/caching claims, rewritten CLI-first.

## Verification evidence (FAST)

- `scripts/sync_skills_bundle.py --check` → 13/13 OK after sync.
- `git diff --check` → clean; `generate_nexus_scholar_pins.py --check` → OK; `ruff check scripts/` → pass.
- Removed-form greps (`--title`, `--metrics` CLI, `-i/-o/--fingerprint`, `inception.py`, unwritten module/class names) → zero in executable examples (only deliberate disclaimers).
- Link/ref existence (`Test-Path`) → all pass. No workspace creation, provider calls, audit writes, or server launches during verification.
- Full Python suite deliberately not rerun (Markdown-only repairs; policy evidence-reuse applies — no executable/pin/fixture change).

## Unresolved limitations

- Helper/recon surfaces verified by source inspection + side-effect-free `--help` only (bare worktree venv lacks kit deps, e.g. `networkx` chain); no live recon calls per scope.
- Kit-CLI flag details in the routing matrix are routed to owning kit skills rather than re-verified here (kit CLIs not installed in this env).

## Deferred defects (harness-owned, NOT fixed — `.py` edits forbidden)

- **D1:** `batch_log.py:72` passes `refresh_index=` to `log_project_event`, whose signature (`log_event.py:159-169`) accepts no such parameter → batch path raises `TypeError`; CLI contract mismatches runtime. Needs a harness-side `.py` fix (separate packet).
- D2: routing-matrix row-8 kit export flag details need kit-owner confirmation.
- D3: no archive/retention helper exists; retention policy deferred.
- `grounded_directions.py` bare-venv import chain (`scholar_harness/__init__ → orchestrator → networkx`) noted for harness runtime owner.

## HCM follow-up ownership

- **HCM-02** must revisit: Stage 6 + identity guidance (emission/acceptance sections).
- **HCM-05** must revisit: Stages 2–4 grounding guidance (probe/distill/delta sections).
- Revisit notes are recorded in each skill; no HCM behavior was documented or anticipated here.

## Next gate

### Maintainer review delta

Blocked executable batch recommendations with prominent D1 warnings in the
workspace skill and performance reference; retained examples as reference-only.
Clarified that compilation/logging is not Contract v1 acceptance in inception.
Runtime code remains unchanged; mirrors regenerated from canonical documents.

Scoped factual review → repair-delta verification only → fork PR (no merge, no pin change, no HCM work).
