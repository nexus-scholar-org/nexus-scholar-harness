# 06 — Deployment & Implementation Options

> Three independent surfaces can expose the Grounded Exploratory Inception Agent, sharing one core (`ReconEngine` + `distiller` + cache). They are complementary, not mutually exclusive.

## Option A — CLI wizard flag extension (first, least invasive)

**Seam:** `cli.py:84-94` → `inception_command()` → `run_wizard()`.

- Extend `scholar-harness inception` with `--grounded` (opt-in, default stays deterministic/local).
- When `--grounded` is passed, `run_wizard()` inserts the recon loop after Stage-1 topic capture and before the Stage-2 refraction grid.
- Interactive: after a probe, the TUI shows the 2-3 grounded directions + anchor citations; the researcher validates or issues a delta probe.
- Emits through the **same** `IntentPacket` → `protocol_compile` path as the base wizard (deterministic downstream unchanged).

| Pro | Con |
| :--- | :--- |
| Zero new infrastructure; reuse existing wizard UX | TUI interactive loop is slower for power users |
| Default behavior untouched | Limited to whatever the TUI can surface |
| Ships inside the existing harness CLI | Network calls on the hot path |

**Absorbs M0.1–M0.3.** Adaptive-horizon extras (M0.4-M0.5) plug into the same seam later without changing the user contract.

## Option B — Autonomous agent via MCP (recommended long-term)

**Entrypoint:** the Methodology Copilot skill driving `nexus_*` MCP tools (15 tools, all verified — see `09_mcp_integration.md`).

- Copilot launches `nexus_discover` (real search, deduped, JSON on disk) → distills → proposes directions → validates with the researcher in natural language.
- The recon lifecycle becomes a *conversation*: the copilot decides query phrasing, pool sizes, and when to delta-probe, all auditable through the session JSON + cache keys.
- No CLI changes needed at all; the core `ReconEngine`/`distiller` become MCP tools (or are called by existing 15).

| Pro | Con |
| :--- | :--- |
| Natural-language direction proposals (far better presentation) | The MCP server must reliably expose the new tools |
| Reuses the verified 15-tool surface | Depends on agent quality for query/discovery judgment |
| Conversations leave a full audit trail | More moving parts to test end-to-end |

## Option C — Harness web console (exploratory, resumable)

- A local web console (`uv run scholar-harness serve` exists at `cli.py:289`) that shows recon sessions, pools, terms, and lets the researcher browse candidate documents interactively.
- Sessions resume across page loads because state lives in `.cache/inception_recon/` (idempotent cache keys make UI re-render cheap).
- Best fit as a **front-end over Option A/B**, not a competing implementation.

## Feature matrix

| Feature | A (CLI) | B (Agent/MCP) | C (Console) |
| :--- | :---: | :---: | :---: |
| Grounded directions | ✅ | ✅ | ✅ (rendered) |
| Delta probing | ✅ | ✅ | ✅ (click-through) |
| Natural-language presentation | ⚠️ (templates) | ✅ (full) | ✅ |
| Resumable sessions | ⚠️ (future `--resume`) | ✅ (state on disk) | ✅ |
| Enables re-verify audit trail | ✅ | ✅ | ✅ |

## Cumulative plan

1. Ship M0.1-M0.3 behind the CLI seam (`--grounded`).
2. Expose `ReconEngine`/`distiller` as MCP tools; have the Copilot drive them (Option B).
3. If demand: wrap in the console (Option C).