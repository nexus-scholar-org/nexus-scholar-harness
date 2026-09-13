# Review Prompt — Inception-Agent → Kit Surface Sweep (fe55447 range)

Copy this whole file into the reviewer agent's prompt. It has everything needed to
find, scope, and verify the work without hunting for context.

---

## Mission

Adversarially review the combined work landed on branch `feat/inception-eval-fixes`
as 5 commits (`9ce8e45`→`fe55447`), covering **three related bodies of work**:

1. **Inception-agent agent + skill** — the chat-driven Grounded Exploratory Inception
   Agent (opencode agent, SKILL.md, parity helper, wizard lifecycle).
2. **Inception skill-stack + GENESIS hardening** — methodology-copilot /
   workspace-manager revisions, `genesis` provenance sidecar + bounded inline summary,
   P1–P6 recon improvements.
3. **8-kit surface sweep** — `docs/kits_surface_matrix.md`, per-kit SKILL.md updates,
   `scripts/sync_skills_bundle.py`, the `scholar-verify` CLI bugfix, `specs/inception-ecosystem/`.

Goal: one strict, evidence-cited review report so a human can confidently ship a PR.
You must **verify**, not just read — run the commands below and check every strong
claim against kit source. You never edit files; you only measure and report.

## Repo orientation (do this first, ~2 min)

- Working dir: `C:\Users\mouadh\Documents\nexus-scholar-harness` (win32, PowerShell).
- Always run through the project venv: `uv run <cmd>`. Never bare `pytest`/`ruff`.
- Read `AGENTS.md` (repo conventions; note `docs/kits_surface_matrix.md` is now the
  canonical API↔CLI↔MCP reference).
- Globs silently skip hidden dirs (`.agents`, `.cache`) — use `bash`/`rg` for those.

## Exact scope — the 5 commits (against branch point `bfea188` = origin/main)

| Commit | Subject | Body of work |
| :-- | :-- | :-- |
| `9ce8e45` | feat(inception-agent): new skill for chat-driven Grounded Exploratory Inception | skill + parity helper + hermetic tests |
| `447ae6c` | fix(inception): harden GENESIS provenance for Windows argv limits + bounded concept seeding | `log_genesis`, bounded concepts |
| `6af9814` | feat(agents): dedicated primary 'inception-agent' agent for opencode | `.opencode/agent/inception-agent.md` |
| `6833831` | feat(recon): post-evaluation inception improvements (P1/P2/P3/P4/P5/P6) | recon engine/agent-server changes |
| `fe55447` | docs(skills): inception skill-stack revision + verified 8-kit surface sweep | matrix doc, 8 kit skills, sync script, specs, verify-cli fix |

Navigation commands:
```powershell
git log --oneline bfea188..fe55447
git diff bfea188..fe55447 --stat        # full shape of the work
git diff bfea188..fe55447 -- <path>     # scoped diffs, e.g.:
#   src/scholar_harness/inception.py
#   tools/scholar-agent-kit/src/scholar_agent/server.py
#   tools/scholar-verify-kit/src/scholar_verify/cli.py
#   scripts/sync_skills_bundle.py
#   docs/kits_surface_matrix.md
#   specs/inception-ecosystem/
```

## Verification protocol (run all; record exact outputs)

```powershell
uv run pytest --tb=short            # expect: 248 passed, 3 skipped, 0 failures
uv run ruff check scripts/          # expect: all checks passed
uv run python scripts/sync_skills_bundle.py --check   # expect: OK <skill> x11
```

CLI/API spot-checks (each validates a matrix/skill claim; ~30 s each):
```powershell
uv run python -c "from scholar_search.models import Query, Document; print('ok')"
uv run python -c "import scholar_search as m; print('Query' in dir(m), 'Document' in dir(m))"   # expect: False False
uv run scholar-search dedup --help                 # only --output/-o, --format/-f (no --export/--csv-output)
uv run scholar-pdf extract --help                  # positional {pdf_path}; engines: docling|grobid only; no --input/--engine pymupdf
uv run scholar-protocol compile --help             # positional {path}; stdout only; no -i/-o/--fingerprint
uv run scholar-protocol render-criteria --help     # positional; stdout only; no -o
uv run scholar-agent --help | Select-String -Pattern "nexus_|recon_"   # expect 16 listed (screen_reconcile + verify_claims hidden)
uv run scholar-verify --help                       # must NOT crash (validates the Optional fix)
uv run scholar-graph build --help                  # --doi/--input/--output/--json-output
uv run scholar-rag query --help                    # --graph/--alpha/--beta present (graph boost is CLI-only)
uv run scholar-bib lint --help                     # --output (defaults overwrite); --generate-keys
```

## Verification checklist (map each finding to file:line evidence)

### A. `docs/kits_surface_matrix.md` (the big one — verify claims, not prose)
1. §"Critical cross-cutting findings" 1–11: each must be true. Especially:
   - Finding 2: `nexus_graph_build` 0-edge → confirm `CitationGraphBuilder(http_client=None)`
     in `tools/scholar-agent-kit/src/scholar_agent/server.py` and that `build_graph`
     swallows fetch failures (`tools/scholar-graph-kit/src/scholar_graph/builder.py`).
   - Finding 3: `nexus_extract_pdf` never passes `metadata=` → checkout the tool body.
   - Finding 4: `nexus_bib_clean` calls `lint(generate_keys=False)` only.
   - Finding 6: `nexus_verify_claims` reads `evidence_quote`/`claim_id`; `SynthesisClaim`
     in `tools/scholar-rag-kit` emits neither → all `MISSING_QUOTE`.
   - Finding 8: `nexus_screen` computes but never writes `conflicts.json`/`prisma_report.json`.
   - Finding 11: `scholar-verify` CLI crash fixed by the `Optional` import now present at
     `tools/scholar-verify-kit/src/scholar_verify/cli.py:18`.
2. Per-kit sections: cross-check 3–4 representative claims per kit against source
   (e.g. smart-filename `{year}_{author}_{title}.pdf`, chunk-id `chk-…` format, folder
   `synthesis/claim` token format, `coi_chunk_1..8.json` contiguity → `SystemExit`).
3. The tables (Quick map, env vars, dependency graph) — flag any symbol/path that
   doesn't exist in source it points to.

### B. Per-kit SKILL.md files (`~/.agents/skills/*/SKILL.md` + mirrored bundle)
1. Every code block must match verified CLI/API (see spot-checks), esp.
   `scholar-search-kit` (models import), `scholar-protocol-kit` (stdout-only compile/render),
   `scholar-pdf-kit` (positional extract), `scholar-graph-kit` (co-citation removed),
   `scholar-agent-kit` (18-tool inventory + CWD-relative-defaults warning).
2. **Mirror discipline**: canonical `.agents/skills/` and bundle
   `.agents/plugins/nexus-scholar/skills/` must be byte-identical — that is what
   spotlight tests of `sync --check` returns; if `--check` is clean, confirm nothing
   was hand-edited on one side only (diff both trees for scholar-verify-kit, which was
   *added* to the bundle in this sweep).
3. `inception-agent/SKILL.md` flow must match the real wizard lifecycle in
   `src/scholar_harness/inception.py` (`_run_grounded_recon`, `_enforce_grounded_anchors`,
   `log_genesis`) and the parity helper must import the real functions (not copy them).

### C. `specs/inception-ecosystem/` + `scripts/sync_skills_bundle.py`
1. Spec claims match code: canonical-source rule, mirror scope table
   (pull-request-gate excluded, 11 skills included), `--check` semantics.
2. Script correctness: exclusion set, `os.listdir` default (does NOT include
   pull-request-gate), `__pycache__` cleanup, exit code 1 on drift.

### D. Inception-agent dev-loop work (`9ce8e45`…`6833831`)
1. P-series (P1–P6): each improvement present in `src/scholar_harness/inception.py`.
2. `log_genesis` GENESIS contract: full sidecar `audit/recon_context.json` + bounded
   inline summary (50-limit lists), must be Windows argv-safe; parity with
   `.agents/skills/workspace-manager/SKILL.md` and `specs/inception-ecosystem/02_handoffs.md`.
3. `.opencode/agent/inception-agent.md` exists and its `[tools]`/permissions match normal
   agent conventions; `models` spec consistent with what the skill needs.
4. recon MCP wiring: `RECON_SEARCH_FN` test seam + `RECON_CACHE_ROOT` canonical root in
   `tools/scholar-agent-kit/src/scholar_agent/server.py`; error convention
   `status:"error"`; matches `specs/exploratory-grounding-agent/13_evaluation.md` §3.4/3.6.

### E. Docs cleanup correctness
- `docs/README.md`, root `README.md`, `AGENTS.md` index changes: links resolve, no
  dead references, test-count (`248 passed, 3 skipped`) matches the run you did.

## Report format (deliver this)

- **Header**: commit range, date, environment, exact command outputs for the 3 gates
  (pytest/ruff/sync).
- **Findings**: table `ID | Severity (BLOCKER|MAJOR|MINOR|NIT) | Area (A–E) | Finding |
  Evidence (file:line) | Suggested remediation`.
- **Verified-clean list**: claims you confirmed true (so the human doesn't re-check).
- **Unverifiable items**: anything you could not confirm offline (e.g. live OpenAlex
  behavior, MCP client-side default-path behavior) — say so explicitly.
- **Recommendation**: READY / READY-WITH-FIXES / NOT-READY for a PR onto main.

## Constraints

- Read-only: never edit, commit, or push anything.
- Cite file:line for every finding; industry-specific verbs ("verified by running X").
- Do not "fix" while reviewing — list remediation only.