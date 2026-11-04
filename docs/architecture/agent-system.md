# Agent system: the AI behind Inception, Discovery and Screening

**Status:** ACCEPTED as the design direction (2026-11-03). Three items are still open (§9). Nothing in this document is implemented yet. It lands in milestones M1, M3 and M4 of [`../roadmap/production-plan.md`](../roadmap/production-plan.md).
**Related:** [`../decisions.md`](../decisions.md) (deployment: local engine, MCP-first plus BYO key), [`confirmation.md`](confirmation.md), [`refusals.md`](refusals.md), `roles/*.json`, the final wireframes in `docs/ux/<phase>/final/` (added by PR #182).

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
- Write tool: `submit_proposal`, which is schema-checked on the server. Each proposal is keyed by `study_id` + `input_sha256` + `protocol_fingerprint`, so a proposal made against a changed abstract or protocol is refused. Calls are limited in rate and size per session.
- No tool writes decisions, approvals, published files or the journal.

**Where the drivers differ.** They share the prompt, the schema and the checks. They do not share cost or throughput: Driver B (MCP) runs inside the researcher's Claude session, so it cannot use Message Batches or this layer's prompt caching. Bulk screening of a large corpus is a Driver A job; Driver B suits small batches and interactive work.

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
| | Calibration on your own labels (the prompt-gate eval, §5) | code + Claude | workflow | reports include-recall with its confidence interval; never measured against a heuristic | you decide whether to trust the run |
| | Agreement, PRISMA preview, publish | code | none | per-batch approval (CON-03) | pairing code |

**The screening proposal schema** (one per record):
- one answer per criterion: `yes`, `no` or `not_reported`;
- for each answer, a verbatim evidence span with its character offsets;
- a `cannot_decide` flag.

**The outcome is derived in plain code, not by the model.** A versioned rule table in code turns the criterion answers into an outcome:
- every inclusion criterion `yes` and no exclusion criterion `yes` → INCLUDE;
- any exclusion criterion `yes`, or an inclusion criterion `no` → EXCLUDE, with that criterion as the reason code;
- any `not_reported`, `cannot_decide`, failed check, refusal or truncation → Unclear.

The model never chooses the outcome, so a prompt change cannot alter the rule. Unclear is stored as the existing `ScreeningDecisionValue.MAYBE` (`contracts/models.py:93`) and labelled "Unclear → full text" in the UI and provenance; no contract version bump is needed (`decisions.md`, 2026-11-03).

**Screening has no agent loop.** It is high-volume classification. A single call with a fixed schema is cheaper, reproducible and auditable.

**You see every record.** The agent orders the queue and proposes, but every record reaches the researcher, like prioritised screening in ASReview or Rayyan. Excluding records that the agent marks as clear exclusions without a human look is an explicit opt-in: it needs a sample audit, and the methods paragraph states it (PRISMA 2020 item 8). The opt-in also removes the human review that §7 relies on against prompt injection, and the opt-in screen says so.

**Blinding.** The proposal is hidden until the researcher decides ("Reveal after my decision"), and the setting is recorded in each decision's provenance. Queue views that reveal how the agent judged a record, such as "agent says exclude", are available only after the decision. Neither the agent nor the researcher sees the database of origin.

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
- `eval/`, a labelled set plus the threshold the task must meet. For screening the threshold is include-recall, judged on its lower confidence bound. The set comes from the researcher's existing human screening of `workspaces/uav-crop-weed-v03` (570 screening files), with at least 200 records and at least 30 includes. A set of 30 records with 3–5 includes cannot detect a regression. The 30-record golden workspace is the end-to-end gate (plan §6 M5-slim), not the prompt-quality gate.

**The prompt gate.** Any change to a prompt, schema, model or effort creates a new task version. The new version must re-run its eval and meet the threshold before it merges. This mirrors the Contract v1 baseline gate: a prompt change cannot silently move review results. Dev-time tests use recorded responses; the eval itself runs against the live API, at a cost shown before it runs.

## 6. Model, cost and API use

- **Default model:** `claude-opus-5-5`, at low effort for screening and higher effort for inception directions and criteria. Thinking cannot be disabled on this model; effort is the control. A cheaper model (`claude-sonnet-5-5`, `claude-haiku-5-5`) is used only if it meets the task's eval threshold (§9).
- **Caching:** the protocol and criteria form a stable prefix shared by every record, so they go first and are cached. The record goes last. The system prompt holds no timestamps or IDs.
- **Bulk:** screening runs use Message Batches, which are asynchronous and half price. Results are matched by `custom_id` (the study ID), never by position.
- **Refusals:** check `stop_reason` before reading content. A refusal becomes an Unclear proposal with the refusal category recorded. A refused record is never dropped.
- **Estimate:** roughly **$5–10 per 1,000 records** on Opus 5.5 through Batches, before thinking-token variance. This is unmeasured arithmetic from list prices, with an assumed ~1.5k input and ~300 output tokens per record. For scale, the v03 corpus has 14,150 records. M1b replaces this figure with the measured per-1,000-record cost from the eval run. The UI shows a token-counted estimate before every run.
- **Who pays:** the researcher, on their own key (Driver A), or through their Claude subscription (Driver B). The maintainer runs no hosted proxy and pays for no tokens (`decisions.md`, deployment entry).

## 7. Privacy and prompt injection

- **Consent:** a per-provider consent screen before the first run says which text (titles, abstracts) leaves the machine and for which provider. The consent is recorded in the workspace.
- **Keys:** stored in the OS keychain and never written to workspace or config files (CORE-17).
- **Untrusted input:** abstracts and titles are untrusted data. They are wrapped as data in the prompt. The tool surface is limited, and the outcome is derived in code. Injected text can at most produce a proposal that a person reviews, constrained by the plain-code checks. This holds only while a person sees every record (§3), which is why skipping that is an opt-in.
- **Network:** search providers and the model API are the only outbound calls. The engine refuses non-loopback access without the per-launch token (INC-01).

## 8. Placement in the plan

| Milestone | Agent-system work |
| :-- | :-- |
| M1a Screening backend | task framework (`tasks/`, proposal store, the outcome rule table in code, validators, journal events); MCP read tools and `submit_proposal` |
| M1b Screening UI + driver | screening proposal task; Anthropic driver with Batches, caching and refusal handling; prompt-gate eval on the v03 labelled set; the measured per-1,000-record cost |
| M2 Screening mobile | none beyond M1 (proposals are read-only on the phone) |
| M5-slim Package | the methods paragraph states how the agent was used (model, prompt version, whether a person saw every record) |
| M3 Discovery (stretch) | query critique task; near-twin task; methods-text task with the numeric check |
| M4 Inception web (after the horizon) | directions task; criteria task; conversational agent loop (unless cut, §9). Until then, conversational inception runs through the MCP path. |

## 9. Open decisions

1. **Gemini:** keep it as Driver C behind the same interface, or remove it? The screening code is Gemini-only today (`scholar_search/screening.py:591-621`). Recommendation: keep it behind the interface, with Claude as the default. Until this is decided, `decisions.md` names Gemini only as an existing option, not a commitment.
2. **In-app inception chat (M4):** M4 is now past the horizon, so this waits. The MCP path covers conversational inception meanwhile.
3. **Cheaper screening model:** measure Sonnet 5.5 and Haiku 5.5 against the prompt-gate eval during M1b, and adopt one only if it meets the include-recall threshold.
