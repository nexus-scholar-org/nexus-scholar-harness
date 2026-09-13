# 03 · Skill tree topology and distribution policy

The skills exist in **two trees**. They serve different consumers and WILL drift
unless the canonical-source rule below is followed.

## 3.1 Topology

```text
.agents/skills/                                  ← CANONICAL (source of truth)
    methodology-copilot/
    workspace-manager/
    inception-agent/
    pull-request-gate/
    scholar-{search,pdf,bib,rag,graph,protocol,agent,verify}-kit/
                                                  ← opencode loads these directly
        (available_skills in the agent session)

.agents/plugins/nexus-scholar/skills/            ← DISTRIBUTION MIRROR
    methodology-copilot/
    workspace-manager/
    inception-agent/                             ← bundled (mirrors canonical)
    scholar-*-kit/
                                                  ← ships skills to external harnesses
        (Claude/Copilot/DSH agents that consume the nexus-scholar plugin)
```

Two consumers can therefore load the same skill name from different paths; the
**content must be identical**.

## 3.2 Canonical-source rule

1. `.agents/skills/<name>/` is **always** edited first. It is the registry opencode
   resolves at session start and the home of `SKILL.md` frontmatter (name,
   description, location) the agent sees.
2. `.agents/plugins/nexus-scholar/skills/` is a **generated mirror**: after editing
   the canonical copy, sync the bundle with `scripts/sync_skills_bundle.ps1` (or the
   equivalent manual copy). Never edit a bundle file and forget the canonical side.
3. `references/` dirs are identical in both trees and travel with the mirror.
4. The bundle additionally carries `plugin.json` (nexus-scholar v1.0.0) and the
   `mcp_config.json` launch manifest — those exist only in the plugin.

### Scope of the mirror

| Skill | In bundle? | Rationale |
| :-- | :-- | :-- |
| `methodology-copilot` | yes | pure instructions; harness-agnostic |
| `workspace-manager` | yes | pure instructions + standalone scripts |
| `inception-agent` | yes | instructions + parity helper; requires the `scholar_harness` package at runtime |
| `pull-request-gate` | **no** | repo-policy enforcement for this harness only |
| `scholar-*-kit` | yes | kit CLIs consumed by external harnesses |

### 3.2.1 Sync procedure (after every canonical edit)

```powershell
# Mirrors every canonical skill except pull-request-gate (spec §3.2 table):
uv run python scripts/sync_skills_bundle.py
# or, manually, per skill (e.g.):
#   Copy-Item .agents/skills/scholar-search-kit/*  .agents/plugins/nexus-scholar/skills/scholar-search-kit/ -Recurse -Force
git status   # expect only intended .agents changes
```

Because `libraries/skills/` improvements ship through the fork + PR gate
(`pull-request-gate`), a bundled skill edit must appear **together with** its
canonical edit in the same PR — a mirror change alone will be rejected on review.

## 3.3 Verification

```powershell
# Report-only: canonical vs bundle must be byte-identical for all in-scope skills
uv run python scripts/sync_skills_bundle.py --check   # expect "OK  <skill>" for every one
```

Non-zero exit (or any `DIFF` line) → sync again. **Zero** diffs for a skill you just
edited means the mirror wasn't updated.

## 3.4 Hygiene

- Never commit `__pycache__/` / `*.pyc` (gitignored; delete on disk after any run).
- Never hand-edit the *mirror* copy as a fix — you will be "fixed" on the next sync.
- `tools/` remains tracked source code (kit checkouts), separate from skill content.