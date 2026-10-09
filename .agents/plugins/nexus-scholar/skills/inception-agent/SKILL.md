---
name: inception-agent
description: Runs the Grounded Exploratory Inception Agent interactively in opencode chat. Probes the academic literature, distills a grounded taxonomy, proposes DOI-anchored research directions, checks gaps for saturation, and emits a scoped research protocol + workspace. Use when the user wants to start a literature-grounded research project or scope/refine a topic conversationally ("start a grounded inception", "I want to research X with literature grounding", "probe and scope my idea", "grounded wizard").
---

# `inception-agent` Skill Instructions

You run the **Grounded Exploratory Inception Agent** as a chat conversation. You are the interviewer: instead of the interactive terminal wizard (`uv run scholar-harness inception --grounded`), you drive the same lifecycle — probe → distill → propose anchored directions → refine (gap check) → validate → emit — turn by turn in opencode, so the human steers everything and nothing is emitted without their explicit approval.

This is **not** a re-implementation. You reuse the real machinery:

- **MCP recon tools** (nexus-scholar server): `recon_probe`, `recon_distill`, `recon_delta`. They carry FAIR session memory under the **canonical recon root** (`NEXUS_RECON_ROOT` if set, else `<project-root>/.cache/inception_recon`, resolved by walking up from the source tree so the MCP server and the CLI agree) and are idempotent (content-addressed cache keys — re-probing the same query is free).
- **Parity helper** `scripts/grounded_directions.py`, which imports the *actual* wizard functions from the `scholar_harness.inception` package (`grounded._grounded_directions_for_terms`, `grounded._grounded_default_concepts`) so the directions you propose are **exactly** the ones the `--grounded` wizard would compute — same anchor filter (≥ 2 distinct DOIs), same ordering (multi-word → frequency → lexicographic), same ≤ 3 cap, and the same P1 behaviour: junk fragments (numeric/verb/venue-scrape) are filtered and at most one direction per lexical family is proposed (plural-normalized, so LLM spelling variants collapse but `vision-language-action vla models` and `self-regulated learning srl` stay distinct).
- **workspace-manager** skill scripts for emission (`init_project.py`, `log_event.py`); **methodology-copilot** for the classic interview/intent-packet conventions when you reach the non-grounded stages.

## Task routing

| Chat task | Do this | Detail source |
| :-- | :-- | :-- |
| Frame the topic | Stage 1 | Below |
| Probe the literature | `recon_probe` | Stage 2 + server signature |
| Distill + propose directions | `recon_distill` + parity helper | Stage 3 |
| Check a thin frontier | `recon_delta` + saturation reading | Stage 4 |
| Pick a direction | Human decision only | Stage 5 |
| Interview + emit workspace/protocol/GENESIS | methodology-copilot interview, then emission block | Stage 6 |
| MCP unavailable | Headless CLI fallback | Tooling fallback |
| Why an example looks this way | Verified source slice | References |

---

## The chat flow (mirrors `run_wizard(grounded=True)` lifecycle)

### Stage 1 — Problem framing (chat)

Ask, in chat (only what's not already obvious):

1. **Topic** — one scoped sentence (e.g. "drone-mounted crop-disease detection with on-device deep learning").
2. **Year + scale** — `start_year` (default 2020), cap `limit` (default 10).
3. **Mode** — semantic (`semantic=True`, OpenAlex embeddings, better topic grounding — recommend it; cache keys stay isolated via `/m/semantic/`) vs keyword (matches CLI default; `semantic=False`).
4. Any standing scope/preference for later stages (paradigm, venue/venue type, language).

### Stage 2 — Probe (MCP)

```text
recon_probe(topic="<STAGE1.topic>", semantic=True, start_year=<year>, limit=10)
```

Signature (server surface only): `topic` required; `session_id` optional (omit for a new `rec_<hex>` session, pass back to extend); `start_year` default 2020; `limit` default 10 (pool capped at 25); `semantic` default False. Report to the user: `session_id`, `cache_key` (lineage; note the `/m/semantic/` segment if semantic), `pool_path`, `n_docs`. If a provider rate-limits, the engine degrades gracefully — say so, don't treat it as failure. If `status:"error"` is returned, echo the message and ask the user to refine the topic. Record the recon root actually used in the `recon_context` lineage so a later audit can find the session. Legacy sessions may exist under `tools/scholar-agent-kit/.cache/inception_recon` from before the root fix; treat them as stale.

### Stage 3 — Distill + grounded directions (parity helper)

```text
recon_distill(session_id="<STAGE2.session_id>")
uv run python .agents/skills/inception-agent/scripts/grounded_directions.py \
  --terms <terms_path> --topic "<STAGE1.topic>" --pool <STAGE2.pool_path>
```

The helper needs `--terms` plus `--topic` (both required); `--pool` adds topic-level anchor DOIs. It prints `directions` plus the pool `qei` and a `qei_note`. To build the emission record after the user picks a direction, re-run adding `--direction "<validated label>"` (fails with exit 2 unless the label matches a proposed direction exactly); add `--max-default-concepts N` only to pre-truncate the chat seed — omitting it keeps full wizard parity. Present in chat:

- **Observed sub-schools / topics** (with `n` and score, e.g. "Advanced Text Analysis Techniques (n=3, 0.77)"), metrics/datasets if present.
- **Pool admission gates** (read `pool` and `purity` from the `recon_distill` reply): `pool.label == "thin"` (`n_docs` below threshold; materials trial produced `11 kcal mol`) → directions may be fragmentary; recommend a higher `limit` or a `recon_delta` before validating. `purity.label == "indeterminate"` (no OpenAlex topics) → coherence is unknown, not zero — say so. `purity.label == "fragmented"` (top-3 topic share below threshold) → the pool spans subfields; prefer the most context-relevant school.
- **QEI interpretation** (`qei`): `≤ 0.3` with a *coherent* pool → pool is novel relative to the prompt (good). `> 0.3` on a *coherent* pool → **inversion caveat**: high echo on a well-scoped seed reflects tight topicality, not poor inquiry — do **not** reject on QEI alone; steer toward a narrower sub-field only when the pool is also fragmented/thin. `qei == 1.0` on a fragmented pool = prompt echo; force refinement.
- **Grounded directions** from the helper: `label`, `detail`, `anchor_dois` (≥ 2 each). Show the anchor DOIs inline so the user sees they're real.
- If the helper returns **no directions** (no ≥ 2-anchor term), do **not** invent concepts. Mirror the wizard's hard rule and tell the user the pool had no direction with ≥ 2 citation anchors, then iterate the topic or delta-probe.

### Stage 4 — Gap due diligence (optional, thin frontiers)

If a thin frontier shows up in schools/topics (`n ≤ 2`) and the user is considering it as a "gap", run:

```text
recon_delta(session_id="<STAGE2.session_id>")
```

Defaults to at most 3 follow-ups (hard cap 3, cache-reusing). The follow-ups carry `corpus_total` (uncapped OpenAlex works-count) + `saturation_label` (`scant|sparse|dense|unknown`) plus the gap-confidence reason under both `reason` and `confidence.detail` (`confidence.label` is `gap`). Interpret for the user: `dense` (large corpus) → heavily researched field; the pool was merely tangential to it. `scant`/`sparse` (incl. a real `corpus_total == 0`, which is an observation, not an error) → genuinely thin literature. Either way, **search sparsity alone never proves a research gap** — the saturation label is a thinness signal for the human to weigh alongside the anchors, not a gap certificate. The user decides whether a thin frontier is worth pursuing.

### Lexicon bootstrap (Loop B, only for specialized registers)

The **shipped default lexicon already carries a curated cross-domain core** (CV/LLM plus climate/health/finance/education/materials school patterns, RMSE/MAE/AUC metrics, ERA5/CMIP/TCGA/MIMIC datasets), so non-tech pools get `schools`/`metrics`/`datasets` signal on day one. Bootstrap a custom lexicon only to add **specialized** registers (e.g. OS/DFS oncology metrics, checkpoint-inhibitor sub-schools). When a school/keyword you need is missing from the distilled tables, or a thin frontier deserves targeted probing, pass a lexicon to `recon_distill` — the parameter accepts either a JSON **string** or an already-parsed dict:

```text
recon_distill(session_id="<STAGE2.session_id>",
              lexicon_json={"schools": {"pattern regex": "label"}, "metrics": {...}, "datasets": {...}})
```

Merge semantics: your tables merge **onto the shipped default**, field-wise, and extras win per key; the artifact gets a lexicon-hash name (same lexicon ⇒ same name). **Verify each submitted pattern matches ≥ 1 pool DOI before submitting** (an unverified regex can silently match 0 docs and the seam reports nothing) — drop, or relax, otherwise.

### Stage 5 — Selection & refinement (chat, human decision)

The user picks a direction (or steers). You may propose a refined single-sentence topic based on the anchor DOIs, but **the user chooses** the `direction` label. Record `concept` (the direction's concept) as the seed at the top of the core-concept list. Helper output is a ranked **proposal**, the user pick is a **candidate**. Compilation and logging record outputs; they do not confer Contract v1 acceptance, which requires the owning acceptance gate.

### Stage 6 — Remaining interview + emission

Follow **methodology-copilot** for the interviews that follow a direction choice (paradigm refractions, unit of analysis, RQs, inclusion/exclusion criteria, matrix dimensions), but seed against the grounded evidence:

- `core_concepts` = validated `concept` first, then a **curated, bounded set (≤ ~8 distinct) drawn from the helper's `default_concepts`** — the raw wizard default can be *hundreds* of pool-anchored terms on a rich pool; curate it the way a researcher edits the wizard's Stage-4b default (pass the helper truncation flag if you want a pre-truncated seed).
- Every concept/synonym must end up **anchored** (APR). If the user adds a concept/synonym not in the anchored evidence, run a bounded supplementary `recon_probe` for it; if it yields no `anchor_dois`, drop the synonym (warn) or refuse the concept — **never emit an unanchored concept into `core_concepts`**. Enforce this before compiling, like the wizard's anchor enforcement.

Then emit **only after the user's explicit confirmation** (ask, mirroring the wizard's final confirm; a declined or dry run writes nothing):

```bash
# 1. Scaffold the workspace (workspace-manager). Title is positional;
#    slug/description/paradigm/rq/keyword/root stay optional flags.
uv run python .agents/skills/workspace-manager/scripts/init_project.py \
  "<Title>" --slug <project-slug> \
  --paradigm "<Paradigm>" --rq "RQ1: <Q1>" --rq "RQ2: <Q2>"

# 2. intent.json (methodology-copilot IntentPacket schema)
#    GENESIS logs recon_context as a provenance sidecar + bounded inline summary (step 4)
# 3. Compile + render canonical artifacts (both print to STDOUT, redirect to persist)
uv run scholar-protocol compile workspaces/<slug>/intent.json > workspaces/<slug>/protocol.json
uv run scholar-protocol render-criteria workspaces/<slug>/protocol.json > workspaces/<slug>/SCREENING_CRITERIA.md

# 4. Audit ledger (hard convention): GENESIS with recon_context.
#    The CLI takes the slug positionally plus action/agent/description/outputs/status flags.
uv run python .agents/skills/workspace-manager/scripts/log_event.py <slug> \
  --action GENESIS --agent scholar-harness/inception --status SUCCESS \
  --description "<description> recon_context={bounded summary json}" \
  --outputs audit/recon_context.json protocol.json SCREENING_CRITERIA.md
```

**Identity:** `init` mints `registered_workspace_id` (`WSP-` plus 32 lowercase hex, OS randomness) once and records it in `project.json`; `project_id` keeps the human slug. Preserve the recorded value on every later read — never derive one from a slug and never mint a second one over recorded state. A non-conforming or unreadable recorded value is a typed refusal to repair, not a cue to re-mint.

**`recon_context` (must be in the GENESIS event):** take the helper's `recon_context` (`anchor_dois`, `direction`, `concept`, `default_concepts`, `anchored_terms`) and add the session lineage from the MCP replies: `session_id`, `cache_keys` (all probe/distill keys), `pool_sizes` (all pool sizes).

**Write path (Windows argv safety):** write the **full** `recon_context` verbatim to `workspaces/<slug>/audit/recon_context.json` — that sidecar is the provenance of record and goes in `--outputs`. Embed only a **bounded inline summary** in the `--description` (`session_id`, `cache_keys`, `pool_sizes`, `direction`, `concept`, `anchor_dois`, `default_concepts`, `anchored_term_count`, `provenance_file`). Never embed the raw dict in the argv — a rich pool's anchored-term map is hundreds of entries and overflows the Windows command line; `log_genesis` in `src/scholar_harness/inception/genesis.py` implements exactly this contract (50-per-list inline cap from `display._bounded`, full dict on disk). Only emit when the workspace is scaffolded; if the user declines or wants a dry run, write nothing and say so.

---

## Hard contracts (never violated)

1. **Anchoring** — every proposal, `core_concept`, and `synonym` carries real evidence (≥ 2 anchor DOIs for a direction; ≥ 1 DOI for a concept/synonym before compiling). No evidence → no concept. If nothing anchors, tell the user plainly (the wizard hard-aborts; you explain instead).
2. **Human gate** — emission (workspace scaffold, intent, protocol, GENESIS) happens only after the user confirms in chat. Interactive default stays intact.
3. **Byte-identical discipline** — you only run this flow when the user asks for grounded inception; you never change default-facing behavior of the CLIs/MCP tools.
4. **Placement** — all project output under `workspaces/<slug>/`; recon state under the canonical `.cache/inception_recon/` root (gitignored; `NEXUS_RECON_ROOT` override, repo-anchored default — never launch-dependent). Never dump into the repo root or `tools/`.
5. **Audit trail** — GENESIS (with `recon_context`: full provenance sidecar `audit/recon_context.json` + bounded inline summary) is mandatory and records only work actually done; log intermediate probes/distills only as generic ledger entries when the user wants the full ledger. Generic entries never substitute for the GENESIS publication event and never imply acceptance.
6. **Tools first** — prefer the MCP recon tools and the parity helper over computing taxonomy scoring by hand or re-deriving wizard logic.

## Tooling fallback

If the MCP recon tools are unavailable in the session, fall back to the headless CLI seam (same engine): `uv run scholar-harness inception --grounded --auto-select` (best/only direction) or `--direction-id <N>` (specific 1-based direction) — deterministic, cached, no blocked prompts. `--root` selects the repo root; `--no-scaffold` runs the interview with no writes. Read its output back into the chat conversation.

## HCM revisit note

This skill describes the committed interfaces only. HCM-02 must revisit the Stage 6 emission block and the Identity paragraph; HCM-05 must revisit the recon signatures, pool/purity gate readings, and helper flags cited in Stages 2–4. Do not anticipate those revisions here.

## References

- Wizard lifecycle: `src/scholar_harness/inception/wizard.py` (`run_wizard`, `inception_command`, `init_command`).
- Grounded recon + anchors: `src/scholar_harness/inception/grounded.py` (`_run_grounded_recon`, `_grounded_directions_for_terms`, `_grounded_default_concepts`, `_enforce_grounded_anchors`).
- Emission + identity: `src/scholar_harness/inception/genesis.py` (`scaffold_project`, `compile_protocol_files`, `log_genesis`, `mint_registered_workspace_id`, `recorded_or_minted_workspace_id`); inline cap `display._INLINE_LIST_CAP` (50).
- Parity helper CLI: `.agents/skills/inception-agent/scripts/grounded_directions.py` (`--terms` + `--topic` required; `--pool`, `--direction`, `--max-default-concepts` optional).
- Emission CLIs: `.agents/skills/workspace-manager/scripts/init_project.py` (positional title; `--slug/--description/--paradigm/--rq/--keyword/--root` optional); `.agents/skills/workspace-manager/scripts/log_event.py` (positional project; `--action/--agent/--description/--inputs/--outputs/--status`; the metrics field is a Python keyword argument only).
- Protocol CLIs: `tools/scholar-protocol-kit/src/scholar_protocol/cli.py` (`compile <intent>`, `render-criteria <protocol>`, both positional-input plus stdout).
- Evaluation gates (pool sufficiency, purity, saturation): `specs/exploratory-grounding-agent/13_evaluation.md`.
- Agent loops + seams: `specs/exploratory-grounding-agent/14_agent_loops.md`.
- Classic interview/intent packet: `.agents/skills/methodology-copilot/SKILL.md`.
