---
name: inception-agent
description: Runs the Grounded Exploratory Inception Agent interactively in opencode chat. Probes the academic literature, distills a grounded taxonomy, proposes DOI-anchored research directions, checks gaps for saturation, and emits a scoped research protocol + workspace. Use when the user wants to start a literature-grounded research project or scope/refine a topic conversationally ("start a grounded inception", "I want to research X with literature grounding", "probe and scope my idea", "grounded wizard").
---

# `inception-agent` Skill Instructions

You run the **Grounded Exploratory Inception Agent** as a chat conversation. You are the interviewer: instead of the interactive terminal wizard (`uv run scholar-harness inception --grounded`), you drive the same lifecycle — probe → distill → propose anchored directions → refine (gap check) → validate → emit — turn by turn in opencode, so the human steers everything and nothing is emitted without their explicit approval.

This is **not** a re-implementation. You reuse the real machinery:

- **MCP recon tools** (nexus-scholar server): `recon_probe`, `recon_distill`, `recon_delta`. They carry FAIR session memory under `.cache/inception_recon/` and are idempotent (content-addressed cache keys — re-probing the same query is free).
- **Parity helper** `scripts/grounded_directions.py`, which imports the *actual* wizard functions (`scholar_harness.inception._grounded_directions_for_terms`, `_grounded_default_concepts`) so the directions you propose are **exactly** the ones the `--grounded` wizard would compute — same anchor filter (≥ 2 distinct DOIs), same ordering (multi-word → frequency → lexicographic), same ≤ 3 cap.
- **workspace-manager** skill scripts for emission (`init_project.py`, `log_event.py`); **methodology-copilot** for the classic interview/intent-packet conventions when you reach the non-grounded stages.

---

## The chat flow (mirrors `run_wizard(grounded=True)` lifecycle)

### Stage 1 — Problem framing (chat)
Ask, in chat (only what's not already obvious):
1. **Topic** — one scoped sentence (e.g. "drone-mounted crop-disease detection with on-device deep learning").
2. **Year + scale** — `start_year` (default 2020), cap `limit`.
3. **Mode** — semantic (`semantic=True`, OpenAlex embeddings, better topic grounding — recommend it; cache keys stay isolated via `/m/semantic/`) vs keyword (matches CLI default).
4. Any standing scope/preference for later stages (paradigm, venue/venue type, language).

### Stage 2 — Probe (MCP)
```text
recon_probe(topic="<STAGE1.topic>", semantic=True, start_year=<year>, limit=10)
```
Report to the user: `session_id`, `cache_key` (lineage; note the `/m/semantic/` segment if semantic), `pool_path`, `n_docs`. If a provider rate-limits, the engine degrades gracefully — say so, don't treat it as failure. If `status:"error"` is returned, echo the message and ask the user to refine the topic.

### Stage 3 — Distill + grounded directions (parity helper)
```text
recon_distill(session_id="<STAGE2.session_id>")        # returns terms_path, qei, metrics, datasets, schools, topics
uv run python .agents/skills/inception-agent/scripts/grounded_directions.py \
  --terms <terms_path> --topic "<STAGE1.topic>" --pool <STAGE2.pool_path>
```
Present in chat:
- **Observed sub-schools / topics** (with `n` and score, e.g. "Advanced Text Analysis Techniques (n=3, 0.77)"), metrics/datasets if present.
- **QEI interpretation** (`qei`): `≤ 0.3` → pool is novel relative to the prompt (good). `> 0.3` → the top-10 taxonomy mostly echoes the prompt — the inquiry is too generic; **steer the user toward a narrower sub-field before validating**. (`qei == 1.0` means pure prompt echo — force refinement.)
- **Grounded directions** from the helper: `label`, `detail`, `anchor_dois` (≥ 2 each). Show the anchor DOIs inline so the user sees they're real.
- If the helper returns **no directions** (no ≥ 2-anchor term), do **not** invent concepts. Mirror the wizard's hard rule and tell the user the pool had no direction with ≥ 2 citation anchors, then iterate the topic or delta-probe.

### Stage 4 — Gap due diligence (optional, thin frontiers)
If a thin frontier shows up in schools/topics (`n ≤ 2`) and the user is considering it as a "gap", run:
```text
recon_delta(session_id="<STAGE2.session_id>")
```
The follow-ups carry `corpus_total` + `saturation_label` (`scant|sparse|dense|unknown`). Interpret for the user:
- `dense` (large corpus) → heavily researched field; **not a novel gap** — the pool was merely tangential to it.
- `scant`/`sparse` (incl. a real `corpus_total == 0`) → genuinely thin; a defensible gap claim.
A `corpus_total == 0` is a real observation, not an error (map to `scant`).

### Stage 5 — Selection & refinement (chat, human decision)
The user picks a direction (or steers). You may propose a refined single-sentence topic based on the anchor DOIs, but **the user chooses** the `direction` label. Record `concept` (the direction's concept) as the seed at the top of the core-concept list.

### Stage 6 — Remaining interview + emission
Follow **methodology-copilot** for the interviews that follow a direction choice (paradigm refractions, unit of analysis, RQs, inclusion/exclusion criteria, matrix dimensions), but seed against the grounded evidence:
- `core_concepts` = validated `concept` first, then a **curated, bounded set (≤ ~8 distinct) drawn from the helper's `default_concepts`** — the raw wizard default can be *hundreds* of pool-anchored terms on a rich pool; curate it the way a researcher edits the wizard's Stage-4b default (pass `--max-default-concepts N` to the helper if you want a pre-truncated seed).
- Every concept/synonym must end up **anchored** (APR). If the user adds a concept/synonym not in the anchored evidence, run a bounded supplementary `recon_probe` for it; if it yields no `anchor_dois`, drop the synonym (warn) or refuse the concept — **never emit an unanchored concept into `core_concepts`**. Enforce this before compiling, like the wizard's `_enforce_grounded_anchors`.

Then emit **only after the user's explicit confirmation** (ask, mirroring the wizard's final confirm):

```bash
# 1. Scaffold the workspace (workspace-manager)
uv run python .agents/skills/workspace-manager/scripts/init_project.py \
  --title "<Title>" --slug <project-slug> \
  --paradigm "<Paradigm>" --rq "RQ1: <Q1>" --rq "RQ2: <Q2>"

# 2. intent.json (methodology-copilot IntentPacket schema)
#    GENESIS logs recon_context as a provenance sidecar + bounded inline summary (step 4)
# 3. Compile + render canonical artifacts (MCP nexus_protocol_compile / nexus_protocol_render_criteria
#    or the equivalent scholar-protocol CLIs)
uv run scholar-protocol compile -i workspaces/<slug>/intent.json -o workspaces/<slug>/protocol.json --fingerprint
uv run scholar-protocol render-criteria workspaces/<slug>/protocol.json -o workspaces/<slug>/SCREENING_CRITERIA.md

# 4. Audit ledger (hard convention): GENESIS with recon_context
uv run python .agents/skills/workspace-manager/scripts/log_event.py <slug> \
  --action GENESIS --agent scholar-harness/inception --status SUCCESS \
  --description "<description> recon_context={bounded summary json}" \
  --outputs audit/recon_context.json protocol.json SCREENING_CRITERIA.md
```

**`recon_context` (M0.3 DoD 4 — must be in the GENESIS event):** take the helper's `recon_context` (`anchor_dois`, `direction`, `concept`, `default_concepts`, `anchored_terms`) and add the session lineage from the MCP replies: `session_id`, `cache_keys` (all probe/distill keys), `pool_sizes` (all pool sizes).

**Write path (Windows argv safety):** write the **full** `recon_context` verbatim to `workspaces/<slug>/audit/recon_context.json` — that sidecar is the provenance of record and goes in `--outputs`. Embed only a **bounded inline summary** in the `--description` (`session_id`, `cache_keys`, `pool_sizes`, `direction`, `concept`, `anchor_dois`, `default_concepts`, `anchored_term_count`, `provenance_file`). Never embed the raw dict in the argv — a rich pool's anchored-term map is hundreds of entries and overflows the Windows command line (`WinError 206`); `log_genesis` in `src/scholar_harness/inception.py` implements exactly this contract (50/cap lists inline, full dict on disk). Only emit when the workspace is scaffolded; if the user declines or wants a dry run, write nothing and say so.

---

## Hard contracts (never violated)

1. **Anchoring** — every proposal, `core_concept`, and `synonym` carries real evidence (≥ 2 anchor DOIs for a direction; ≥ 1 DOI for a concept/synonym before compiling). No evidence → no concept. If nothing anchors, tell the user plainly (the wizard hard-aborts; you explain instead).
2. **Human gate** — emission (workspace scaffold, intent, protocol, GENESIS) happens only after the user confirms in chat. Interactive default stays intact.
3. **Byte-identical discipline** — you only run this flow when the user asks for grounded inception; you never change default-facing behavior of the CLIs/MCP tools.
4. **Placement** — all project output under `workspaces/<slug>/`; recon state under `.cache/inception_recon/` (gitignored). Never dump into the repo root or `tools/`.
5. **Audit trail** — GENESIS (with `recon_context`: full provenance sidecar `audit/recon_context.json` + bounded inline summary) is mandatory; log intermediate probes/distills when the user wants the full ledger.
6. **Tools first** — prefer the MCP recon tools and the parity helper over computing taxonomy scoring by hand or re-deriving wizard logic.

## Tooling fallback
If the MCP recon tools are unavailable in the session, fall back to the headless CLI seam (same engine): `uv run scholar-harness inception --grounded --auto-select` (best/only direction) or `--direction-id <N>` (specific 1-based direction) — deterministic, cached, no blocked prompts. Read its output back into the chat conversation.

## References
- Grounded wizard internals: `src/scholar_harness/inception.py` (`_run_grounded_recon`, `_enforce_grounded_anchors`).
- Evaluation gates (QEI ≤ 0.3, APR, saturation): `specs/exploratory-grounding-agent/13_evaluation.md`.
- Agent loops + seams: `specs/exploratory-grounding-agent/14_agent_loops.md`.
- Classic interview/intent packet: `.agents/skills/methodology-copilot/SKILL.md`.