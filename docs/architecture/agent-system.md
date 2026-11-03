# Agent system: the AI behind Inception, Discovery and Screening

**Status:** ACCEPTED as the design direction (2026-11-03). Three items are still open (§9). Nothing in this document is implemented yet. It lands in milestones M1, M3 and M4 of [`../roadmap/production-plan.md`](../roadmap/production-plan.md).
**Related:** [`../decisions.md`](../decisions.md) (deployment: local engine, MCP-first plus BYO key), [`confirmation.md`](confirmation.md), [`refusals.md`](refusals.md), `roles/*.json`, the final wireframes in `docs/ux/<phase>/final/`.

## 1. Principle

The agent proposes and the researcher decides. Everything below follows from that rule.

1. **Use the least autonomous form that does the job.** Plain code beats a single structured model call; a single call beats a fixed workflow; a fixed workflow beats an agent loop. Only two places get a true agent loop: the inception conversation, and the researcher's own Claude Code or Claude Desktop working through MCP.
2. **Agents never write authoritative artifacts.** Every model output is a *proposal* in an append-only store. Only the engine writes workspace artifacts and `audit/journal.jsonl`, and only after a human decision.
3. **Plain code checks every proposal before a person sees it.** If a proposal fails a check, or the model refuses or is truncated, the record goes to the researcher as **Unclear · needs you**. It is never resolved to Exclude and never filled with a default. This addresses assessment findings SRCH-16, SRCH-17 and CON-11.
4. **Every proposal can be reproduced and reported.** It records its model, prompt hash, inputs and checks, so a methods section can state exactly what the agent saw.

## 2. Layers

```
UI ──▶ Engine (FastAPI; the only writer of workspace artifacts and the journal)
          │
          ├─ Deterministic stages: search, dedup, batching, collect, PRISMA
          │
          └─ AI task layer
               task = versioned prompt + output schema + model/effort + eval set
               │
               ├─ Driver A  in-app, researcher's Anthropic API key
               │            (Message Batches for bulk, prompt caching)
               ├─ Driver B  researcher's Claude Code / Claude Desktop through
               │            the scholar-agent MCP server (their subscription)
               └─ Driver C  Gemini (existing code), only if kept (§9)
               │
               ▼
          Proposal store   <ws>/proposals/<task>/<run-id>.jsonl (append-only)
               ▼
          Validators (plain code): schema, verbatim quote, consistency, IDs exist
               ▼
          UI review ──▶ human decision event ──▶ collector ──▶ journal
```

**Both drivers run the same task definitions and submit through the same proposal path.** That parity is what makes it feel like Claude Code. The researcher's own agent works inside the workspace through MCP, its proposals appear live in the UI (over SSE), and the researcher decides there.

**MCP tool surface (Driver B).**
- Read tools: read the queue, read one record, read the protocol and criteria, read run status.
- Write tool: `submit_proposal`, which is schema-checked on the server.
- No tool writes decisions, approvals, published files or the journal.

The role model in `roles/*.json` (generated permissions, write deny-globs, protected journal) enforces these limits. AGT-01 (path containment) and AGT-16/19 (MCP writes final files and skips the journal) are fixed as part of this surface.

## 3. Tasks per phase

| Phase | Job | Done by | Form | Plain-code check | Human gate |
| :-- | :-- | :-- | :-- | :-- | :-- |
| Inception | Probe search, pool health, gates | code (`recon/`) | none | provider outcome recorded; empty or failed pools never cached (INC-09) | — |
| | Name schools and topics; propose up to 3 directions | Claude | single structured call | every cited paper ID is in the pool; anchored only when the term occurs in titles or abstracts, with a count (INC-21) | pick one or write your own |
| | Draft concepts, synonyms and criteria | Claude | single structured call | each criterion carries its source; none without one; paradigm defaults flagged (INC-22) | accept each criterion |
| | Conversational inception | Claude | **agent loop** (tool runner); tools: probe, distill, anchor check, update draft | can only edit the draft session | Review and emit is the only write gate (INC-08) |
| Discovery | Translate the query for each database | code (existing translators) | none | executed string recorded verbatim (SRCH-30) | approve the plan |
| | PRESS-style query critique | Claude | single call | suggestions only; never applied silently (SRCH-12/13/14) | accept or ignore each one |
| | Search, dedup, PRISMA-S counts | code | none | stable IDs (CORE-06); cap and lower-bound flags (SRCH-11) | — |
| | Near-twin "same paper?" (optional) | Claude | single call | the answer shows its evidence fields side by side | merge or keep both |
| | Methods text draft | Claude | single call | every number in the text must match the run's search records | edit, then mark as reviewed |
| Screening | Per-record proposal | Claude | single structured call per record, sent through Message Batches | quote must appear verbatim in the title or abstract; outcome must follow from the answers; schema failure, refusal or `max_tokens` → Unclear | your decision, made with the proposal hidden first |
| | Calibration on 30 of your labels | code + Claude | workflow | reports sensitivity for includes; never measured against a heuristic | you decide whether to trust the run |
| | Agreement, PRISMA preview, publish | code | none | per-batch approval (CON-03) | pairing code |

**The screening proposal schema** (one per record):
- one answer per criterion: `yes`, `no` or `not_reported`;
- for each answer, a verbatim evidence span with its character offsets;
- the derived outcome: `INCLUDE`, `EXCLUDE` with a reason code, or `UNCLEAR`;
- a `cannot_decide` flag.

The derived outcome uses UNCLEAR, which depends on the Contract v1 decision listed in plan §2. Until that decision lands, the engine maps UNCLEAR to "needs you" and never to a final decision.

**Screening has no agent loop.** It is high-volume classification. A single call with a fixed schema is cheaper, reproducible and auditable.

**Blinding.** By default the proposal is hidden until the researcher decides ("Reveal after my decision"). The setting is recorded in each decision's provenance. Neither the agent nor the researcher sees the database of origin.

## 4. What every proposal records

Each proposal is one JSONL line with these fields:

- `task_id`, `task_version`, `prompt_sha256`
- `driver` (`api`, `mcp` or `gemini`), `model`, `effort`
- `input_sha256` (record content), `protocol_fingerprint`, `batch_binding`
- `output` (the raw, schema-valid object), `validators` (the name and result of each check)
- `usage` (input, cached and output tokens), `cost_estimate`
- `request_id`, `batch_id`, `created_at`

Each run also appends `AGENT_RUN_STARTED` and `AGENT_RUN_COMPLETED` to `audit/journal.jsonl`. The completed event carries counts of proposals, check failures, refusals and truncations. A human decision references the hash of the proposal that was shown, if one was shown. An undo is a superseding decision event and never a deletion; see plan §4 for the decision-event model.

## 5. Task definitions and the prompt gate

Each task lives in `src/scholar_agent/tasks/<task>/`:

- `prompt.md`, with its sha256 recorded on every call;
- `schema.py`, a Pydantic output model that is also sent as `output_config.format`;
- `task.toml`, holding model, effort, and caching and batch settings;
- `eval/`, a small labelled set from the golden UAV workspace, plus the threshold the task must meet. For screening the threshold is include-recall.

**The prompt gate.** Any change to a prompt, schema, model or effort creates a new task version. The new version must re-run its eval and meet the threshold before it merges. This mirrors the Contract v1 baseline gate: a prompt change cannot silently move review results. Dev-time tests use recorded responses; the eval itself runs against the live API, at a cost shown before it runs.

## 6. Model, cost and API use

- **Default model:** `claude-opus-5-5`, at low effort for screening and higher effort for inception directions and criteria. Thinking cannot be disabled on this model; effort is the control. A cheaper model (`claude-sonnet-5-5`, `claude-haiku-5-5`) is used only if it meets the task's eval threshold (§9).
- **Caching:** the protocol and criteria form a stable prefix shared by every record, so they go first and are cached. The record goes last. The system prompt holds no timestamps or IDs.
- **Bulk:** screening runs use Message Batches, which are asynchronous and half price. Results are matched by `custom_id` (the study ID), never by position.
- **Refusals:** check `stop_reason` before reading content. A refusal becomes an Unclear proposal with the refusal category recorded. A refused record is never dropped.
- **Estimate:** 3,241 records on Opus 5.5 through Batches is roughly **$15–30** in total, before thinking-token variance. This is an estimate from list prices and an assumed ~1.5k input and ~300 output tokens per record. The UI shows a token-counted estimate before every run.
- **Who pays:** the researcher, on their own key (Driver A), or through their Claude subscription (Driver B). The maintainer runs no hosted proxy and pays for no tokens (`decisions.md`, deployment entry).

## 7. Privacy and prompt injection

- **Consent:** a per-provider consent screen before the first run says which text (titles, abstracts) leaves the machine and for which provider. The consent is recorded in the workspace.
- **Keys:** stored in the OS keychain and never written to workspace or config files (CORE-17).
- **Untrusted input:** abstracts and titles are untrusted data. They are wrapped as data in the prompt. The tool surface is limited, so injected text can at most produce a proposal that a person reviews and that the plain-code checks constrain.
- **Network:** search providers and the model API are the only outbound calls. The engine refuses non-loopback access without the per-launch token (INC-01).

## 8. Placement in the plan

| Milestone | Agent-system work |
| :-- | :-- |
| M1 Screening core | task framework (`tasks/`, proposal store, validators, journal events); screening proposal task; Anthropic driver with Batches and caching; MCP read tools and `submit_proposal`; prompt gate with the golden eval |
| M2 Screening mobile | none beyond M1 (proposals are read-only on the phone) |
| M3 Discovery | query critique task; near-twin task; methods-text task with the numeric check |
| M4 Inception | directions task; criteria task; conversational agent loop (unless cut, §9) |

## 9. Open decisions

1. **Gemini:** keep it as Driver C behind the same interface, or remove it? The screening code is Gemini-only today (`scholar_search/screening.py:591-621`). Recommendation: keep it behind the interface, with Claude as the default.
2. **In-app inception chat (M4):** build it, or let the MCP path cover conversational inception for now? Cutting it is cheaper and loses little for users who already have Claude Code or Claude Desktop.
3. **Cheaper screening model:** measure Sonnet 5.5 and Haiku 5.5 against the golden eval during M1, and adopt one only if it meets the include-recall threshold.
