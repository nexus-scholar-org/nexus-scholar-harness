# 03 — Skills Portability

The skills are the strongest asset in this repository. They are also the least portable thing in it, for mechanical reasons that are cheap to fix and expensive to keep.

This file defines what a skill must contain to serve both the dev loop and an application, and the tests that keep it that way.

---

## 1. What is already right

Keep these properties; they are the reason a stranger can trust a skill:

- **Line-cited command surfaces.** Claims point at CLI definitions rather than paraphrasing them.
- **Gotcha callouts.** The non-obvious failure (silent empty success, engine defaults, retry semantics) is stated next to the command that triggers it.
- **Refusal semantics.** Declared-unsupported operations say so (`E1`/`E2`/`E3`) instead of returning empty results.
- **Return-shape split.** Whether a tool returns JSON or prose is stated explicitly, so an agent does not parse a table as data.
- **Encoding discipline.** UTF-8 with no mojibake; earlier console artifacts were verified as display-only.

None of that is what breaks. What breaks is every reference to *this machine*.

## 2. What breaks outside this repository

| Blocker | Example | Fails for |
|---|---|---|
| Literal CLI invocation | `uv run scholar-pdf download ...` | Any environment without `uv` and these entry points |
| Repo-relative paths | `tools/scholar-agent-kit/src/...` | Installed wheels; customer workspaces |
| Pins in prose | `pinned rev 79ffe42…` (stale: actual `50c0b3fb…`) | Anyone who trusts the skill instead of the manifest |
| Dangling doc pointer | `docs/kits_surface_matrix.md` | Wheel users — the file is not force-included |
| No preflight | Commands run before checking the CLI exists / workspace resolves | Errors surface as tracebacks, not refusals |

The stale pin is the instructive one: a version fact written in prose has no owner and no test, so it drifted. Pins belong in exactly one place, and that place is generated from.

## 3. Skill contract

```yaml
---
name: scholar-pdf-kit
description: Discover, validate, and extract Open Access PDFs; resolve OA status without downloading.
applies_to: [extractor-a, extractor-b, acquisition]
requires: [scholar-pdf]
variables: [CLI, WORKSPACE, CACHE]
returns: json
layer: domain            # domain | procedure | policy
---

# scholar-pdf-kit

## Preflight
...typed checks...

## Commands
...parameterised...
```

| Field | Meaning | Rule |
|---|---|---|
| `name` | Skill id, matches directory | Unique |
| `applies_to` | Role ids that may load it | ⊆ `roles/*.json` |
| `requires` | CLI/package that must resolve before use | Drives preflight; a missing requirement is `BLOCKED_INPUT`, not a traceback |
| `variables` | Environment placeholders used in the body | ⊆ global registry (§4) |
| `returns` | `json` \| `prose` \| `files` | Prevents parsing a human table as data |
| `layer` | `domain` (how a kit works) \| `procedure` (how a workflow runs) \| `policy` (what must not happen) | Used for context budgeting |

## 4. The environment preamble

Skills stop naming their environment. They name *roles for parts of an environment*, and the adapter binds them.

| Placeholder | Dev loop | Application | Notes |
|---|---|---|---|
| `{CLI:<kit>}` | `uv run scholar-<kit>` | the app's command alias or in-process call | Never a literal path |
| `{WORKSPACE}` | `workspaces/<slug>` | the user's project root | Absolute at runtime |
| `{KIT_ROOT}` | `tools/<kit>` | installed package root | Read-only in app mode |
| `{CACHE}` | `<repo>/.cache/...` or `NEXUS_RECON_ROOT` | app-managed cache dir | Must be CWD-independent |
| `{CONFIG}` | `.agents/plugins/nexus-scholar/plugins.json` | bundled pin manifest | The only place pins are read |

Rewrite rule, applied mechanically:

```
uv run scholar-search search ...   →   {CLI:search} search ...
tools/scholar-rag-kit/src/...      →   {KIT_ROOT:rag}/src/...
workspaces/<slug>/literature/...   →   {WORKSPACE}/literature/...
```

**Banned in a skill body:** `uv run`, absolute paths, `C:\`, `~/`, bare `tools/`, `workspaces/<literal>`, and commit SHAs.

## 5. Pin hygiene

| Wrong | Right |
|---|---|
| `SKILL.md` states a commit SHA | `SKILL.md` says "pin: see `{CONFIG}`" |
| "Last verified 2026-10-14 (79ffe42)" written by hand | `SKILL.meta.json` generated at install with `{rev, verified_at, source}` |
| Version claims duplicated in two skills | One manifest, many readers |

Generated at install time:

```json
{ "skill": "scholar-agent-kit", "kit": "scholar-agent-kit",
  "rev": "50c0b3fbf52fc1a9768b219bc2e894d713eb38af",
  "source": ".agents/plugins/nexus-scholar/plugins.json",
  "verified_at": "2026-10-23T10:00:00Z" }
```

The skill body reads the manifest or omits the number. Prose that restates a version is deleted.

## 6. Doc pointers must resolve where the skill ships

A skill may only reference a document that is present in the same distribution as the skill.

Today `.agents/skills/**` is force-included in the wheel, and `docs/kits_surface_matrix.md` is not. Three skills point at it. Wheel users therefore follow a pointer into nothing.

Two acceptable fixes, in preference order:

1. **Force-include** the referenced doc (one line in the packaging manifest) — keeps one authoritative copy.
2. **Inline the minimum** the skill actually needs and delete the pointer.

A third option — "it exists in the repo" — is not a fix.

## 7. Standard skill skeleton

Every skill, in this order. Sections that do not apply are omitted, not left empty.

```markdown
# <skill-id>

<one sentence: what this lets you do, and what it does not.>

## Preflight
- {CLI:<kit>} --help  succeeds  → else BLOCKED_INPUT
- {WORKSPACE}/protocol.json exists → else BLOCKED_INPUT
- (any declared `requires`)

## Commands
Parameterised invocations only, each with its return shape.

## Inputs and outputs
Formats, required fields, absence states. Link the schema; do not restate it.

## Gotchas
The non-obvious failures, each attached to the command that triggers it.

## Refusals
Declared-unsupported operations and the codes returned (E1/E2/E3, BLOCKED_*).

## Verification
How to prove the step actually produced what it claims.

## Pointers
Only documents shipped alongside this skill.
```

The `Preflight` block is the single highest-value addition. It converts "the command failed" into `BLOCKED_INPUT` with a named missing requirement — the same improvement the envelope makes at the role boundary.

## 8. Portability test

`tests/conformance/test_skill_portability.py` — deterministic, no network.

| Assertion | Catches |
|---|---|
| Frontmatter validates; `applies_to` ⊆ known roles | Orphan skills |
| No literal `uv run` in any fenced block or inline code | Dev-environment leakage |
| No absolute path (`C:\`, `/home/`, `/Users/`) | Machine coupling |
| No bare `tools/` or `workspaces/<literal>` | Repo coupling |
| No 7–40 char hex SHA in prose | Pin drift (`79ffe42…` class of bug) |
| Every `variables` entry is in the registry | Undefined placeholder |
| Every referenced doc path is in the wheel manifest | Dangling pointer (`kits_surface_matrix.md` class of bug) |
| Every skill with `requires` has a `## Preflight` section | Missing refusal path |
| `returns:` present | Agents guessing the shape |
| Skill size ≤ declared context budget | Context bloat, per `context_efficiency_policy.md` |

### Negative cases (must fail)

1. Skill body containing `uv run scholar-search search`.
2. Skill citing `docs/kits_surface_matrix.md` while that path is not force-included.
3. Skill stating `pinned rev 79ffe42…`.
4. Skill with `requires: [scholar-pdf]` and no Preflight section.
5. Skill whose `applies_to` names a role that does not exist.
6. Skill returning JSON with `returns: prose`.

## 9. Skill ↔ role mapping

| Skill | Primary roles | Layer |
|---|---|---|
| `scholar-protocol-kit` | inception-agent, screener | domain |
| `scholar-search-kit` | screener, inception-agent | domain |
| `scholar-pdf-kit` | extractor-a, extractor-b | domain |
| `scholar-rag-kit` | extractor-a, extractor-b | domain |
| `scholar-verify-kit` | extraction-critic | domain |
| `scholar-bib-kit` | inception-agent | domain |
| `scholar-graph-kit` | inception-agent | domain |
| `scholar-agent-kit` | orchestrator, inception-agent | domain |
| `doer-contract` | screener, extractor-a, extractor-b, adjudicator | policy |
| `critic-contract` | screening-critic, extraction-critic, reviewer | policy |
| `workspace-manager` | orchestrator, inception-agent | procedure |
| `methodology-copilot` | inception-agent | procedure |
| `inception-agent` | inception-agent | procedure |
| `pull-request-gate` | *(none — dev-only)* | policy |

Fourteen skill directories exist. Thirteen are research-facing and belong in the app distribution; `pull-request-gate` encodes the contribution workflow and must be excluded from any customer-facing package, since it describes shipping changes to this repository.

`doer-contract` and `critic-contract` are **policy** skills: they encode what must never happen. They are the natural home for the envelope and refusal rules from `02_envelope_and_refusals.md`, which currently exist only in orchestrator prose.

## 10. Migration

Mechanical, not editorial. The content of the skills is not changing.

| Step | Work | Effort |
|---|---|---|
| 1 | Add `Preflight`, `Refusals`, `returns:` to every research-facing skill | ~3 h |
| 2 | Replace `uv run <cli>` → `{CLI:<kit>}` and strip repo paths | ~1 h, scriptable |
| 3 | Delete prose pins; emit `SKILL.meta.json` at install | ~1 h |
| 4 | Fix the three dangling doc pointers (force-include or inline) | ~30 m |
| 5 | Land `test_skill_portability.py` | ~2 h |

Total: about one day, no scientific content touched, and every skill becomes executable by the application adapter without a fork.
