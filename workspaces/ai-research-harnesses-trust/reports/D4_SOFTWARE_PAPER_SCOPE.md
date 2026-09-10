# D4 — Software/Artifact Paper Scope

**Status:** v0.1 scope (2026-09-10) — outline + claim↔build-item mapping; drafting begins only when D1/D2 are submitted (plan §3 item 4).
**Discipline:** Phase-7 distribution work (P7.1–P7.9) becomes *content* for this paper — build only what unblocks a paper claim; otherwise the item is dropped (plan §5.3).

---

## Target venues

- **Primary:** JOSS (Journal of Open Source Software) — short, artifact-review format, tests + docs as the review unit.
- **Alternates:** SoftwareX (Elsevier), GigaScience (Software track), or CS methods + arXiv paired with D2.
- Acceptance criterion: the *three-tier distribution* (umbrella package, workspace-portable CLI, universal MCP) is verifiable by a fresh user following the documented "1-minute" path.

## Working title

*nexus-scholar: an agent-agnostic, provenance-verified framework for systematic literature review*

## Paper claims (each must be anchored in a committed artifact)

1. **Agent-agnostic orchestration.** One file-based workspace contract (`protocol.json`, `intent.json`, `audit/journal.jsonl`, `literature/`, `extracted/`, `synthesis/`) that any AI agent CLI or MCP client can drive. Evidence today: `src/scholar_harness/cli.py` (status|sync|run|export|inception), `.agents/plugins/nexus-scholar/mcp_config.json`, `workspaces/*/` canonical layout.
2. **Append-only provenance ledger.** Every pipeline step as an immutable `audit/journal.jsonl` event (action/agent/outputs/metrics), reflected in `project.json`/`INDEX.md`; `batch_log.py` + `log_event.py` enforce it. Evidence: 68-event D3 ledger, 94-event D1 ledger, `workspace-manager` skill contract.
3. **Deterministic claim verification.** `VerbatimClaimVerifier` (≥0.90 glyph-normalized coverage on char-window or token 6-gram alignment) as the default trust gate; Phase-6/Phase-4 trust streams (retraction, DAS/CAS open-science scan, COI audit, QUADAS-2/PROBAST RoB). Evidence: `scholar-verify-kit`, D2 manuscript (510/510), D3 Phase-4 stream artifacts, D1 phase4/.
4. **Zero-friction distribution.** A first-time user reproduces the whole loop outside the monorepo: `uvx nexus-scholar init` → workspace scaffold → MCP wiring → search→screen→verify→synthesis→audit. Evidence: P7.1–P7.8 once built (this is the paper's validation section).
5. **Empirical credibility (not vaporware).** The framework has produced three peer-aimed deliverables: D1 UAV benchmark review (94-study audited corpus), D2 method paper (head-to-head vs RAG), D3 living scoping review (58 included, 510 claims). Evidence: committed manuscripts + regeneration scripts in both workspaces.

## Claim ↔ Phase-7 item mapping (build only this)

| Paper claim | P7 item(s) that unblock it | Current state |
|---|---|---|
| 4 (uvx init / MCP in any folder) | **P7.1** `--workspace` rootdir in `scholar_agent.server.main()` | Not built — blocks all uvx examples |
| 4 (single-install umbrella) | **P7.2** repo-root `nexus-scholar` metapackage; pins codegenned from `.agents/plugins/nexus-scholar/plugins.json` | Not built — `uvx nexus-scholar` fails today |
| 4 (workspace scaffold) | **P7.3** `nexus-scholar init <title>` wrapping `inception` wizard + `audit/journal.jsonl` + `.env.example` + skill symlinks | Reuse existing `inception.py`; symlinks not copies |
| 4 (harness integration) | **P7.4** `nexus-scholar setup-mcp` (`.mcp.json`, `.cursor/`, `.vscode/`, Claude Desktop snippet w/ absolute path + env page) | Not built |
| 4 (validation/diagnostics) | **P7.5** `nexus-scholar doctor` (kits vs plugins.json, keys, skills, layout) | Not built |
| 2 (ledger travels) | **P7.6** `nexus-scholar log` — importable CLI wrapping `log_event`/`batch_log`/INDEX-sync | Blocks claim 2 outside monorepo |
| 4 (1-minute honesty) | **P7.7** lazy-import rag/graph so light commands skip torch/chromadb | Not built — first uvx run minutes |
| 1+4 (end-to-end proof) | **P7.8** GitHub-Release wheel + CI end-to-end run in temp folder | Not built; CI runs plugin-install best-effort today |
| (back-pocket) distribution | **P7.9** PyPI publication of 8 kits + metapackage | Deferred; only if external consumers appear |

## What the paper does NOT need

- New research components beyond the runs already committed (D1/D2/D3 are the validation corpus).
- PyPI publishing before reviewers try `uvx --from <github-release>` (GH Release wheel satisfies claim 4).

## Sequencing note

- D4 drafting is gated on D1/D2 submission (plan §3.4). P7.1–P7.8 are build items that only make sense while the D4 paper is being drafted — they are evidence, not a pre-paper project.
- First build batch if approved: P7.1 + P7.2 + P7.3 (the "1-minute" spine); then P7.4/P7.6/P7.7 to close portability; P7.5/P7.8 as the paper's validation appendix.