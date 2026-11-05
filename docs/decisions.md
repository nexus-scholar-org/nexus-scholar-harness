# Decisions

One entry per decision that still shapes the code, newest first. The full
records were removed in the 2026-11-03 docs cut; each entry names the commit
history to read if you need the original reasoning (`git log --follow -- <path>`).

## 2026-11-05 — No demonstration marker on the live-only screening steps (M1b-2)

The shell drew `Demonstration data` and "Read-only demonstrator" on every
route, including the six screening steps (`/screening/home`, `prepare`,
`proposals`, `triage`, `agreement`, `publish`) that only read the workspace's
engine and record decisions. There the labels were false. On those six routes
the shell now leaves the marker out and its footer says the data is live
(`isLiveOnlyPath`, `tests/shell.test.tsx`). Every other route keeps both,
including `/screening`, `/corpus`, `/lineage` and `/audit`, which still default
to fixtures; the rule "no mock data without the label" is unchanged
(researcher, 2026-11-05).

## 2026-11-05 — A minimal workspace screen joins M5-slim

The researcher asked why workspace management, Inception and Discovery came
after screening. The order stands (2026-11-03 entry below): screening is the
wedge, `accept-corpus` is its entry path, web Inception (M4) is past the
horizon and Discovery (M3) is stretch. One gap is pulled forward: a packaged
desktop app that can only open the single folder named on the command line is
not sellable. M5-slim therefore adds a **minimal workspace screen**: list the
workspaces under the workspaces root, open one, and create one (the same
scaffold as `nexus-scholar init`), with no Inception wizard. Its spec is written
before M5-slim starts; the M4 multi-workspace server and Inception spec 00 stay
in M4 (researcher, 2026-11-05).

## 2026-11-05 — The checked record text carries the publication year (M1b-2)

The text an agent sees and quotes, and that the engine checks quotes against
(`proposals.record_text`), is the title, a blank line and the abstract, then,
when the record has a year, a blank line and `Published: <year>`. Date
criteria (v03 INC-03, EXC-04) can then be answered with a verifiable quote;
before, the agent could only answer `not_reported`, so every record became
Unclear and the prompt gate measured nothing useful (researcher, 2026-11-05).

- Without a year the text and its `input_sha256` are unchanged, so earlier
  proposals keep their ids. With one, the hash and `proposal_id` change; no
  real proposals existed yet (only sandbox and test ones).
- Language still has no field; a language criterion is answered from the
  abstract or stays `not_reported`.
- The MCP record tool returns this `text` with the year, so an agent using
  MCP quotes the same string.
- **Usefulness is reported, not gated:** the prompt-gate report also gives
  the share of confirmed excludes the agent excludes and its Unclear rate;
  the pass bar stays include-recall.

## 2026-11-05 — The screening prompt gate: bar, sample and models (M1b-2)

The researcher set the prompt gate of agent-system §5 for the screening task:

- **Bar:** the 95% Wilson lower bound of include-recall is at least **0.90**.
  Include-recall counts an agent Unclear as not excluded, because Unclear goes
  on to full text. The bar applies per task version (provider, model, prompt,
  effort).
- **Sample:** every human-confirmed include of `uav-crop-weed-v03` (644) and
  1,000 of its confirmed excludes, drawn with a fixed, recorded seed. The set
  is frozen as a list of study ids with its SHA-256, so every model and prompt
  version is measured on the same records.
- **Models:** `claude-opus-5-5` (the default), `claude-sonnet-5-5` and
  `claude-haiku-5-5`. A cheaper model is adopted only if it meets the bar
  (agent-system §9 item 3).
- **The live run spends the researcher's key.** It runs only after the
  researcher sees the token-counted estimate and starts it; the key is stored
  in the OS keychain and never seen by the agent or written to a file.

**Caveat (carried from 2026-11-04):** the v03 labels are confirmations of agent
drafts. The gate measures recall against labels a person reviewed with a
draft in view, not against independent blind screening; the methods text says
so.

## 2026-11-05 — M1b is three PRs; three screening providers

M1b splits into **M1b-0** reveal tracking (RELEASE, backend only), **M1b-1**
desktop triage UI (STANDARD) and **M1b-2** drivers and the prompt-gate eval
(STANDARD). The researcher agreed the split on 2026-11-05. The reveal change is
isolated so the strict lane covers only the engine change to stored decision
events.

**Providers (researcher, 2026-11-05):** one driver interface with Anthropic
(the default), any **OpenAI-compatible** endpoint (a base URL and a key) and
Gemini. They share the prompt, the output schema, the plain-code outcome rule
and the rule that a refusal or a failed check becomes Unclear. Each provider
and model is its own task version and must pass the prompt gate on its own.
This settles agent-system §9 item 1: Gemini stays, behind the interface.

**Reveal semantics (contract §3.1, applied literally):** a reveal is the first
time the API returns a proposal for a study to a screener. It is recorded in
`literature/screening/reveals.jsonl` under the events lock and journaled as
`SCREENING_PROPOSAL_REVEALED` without the outcome. A superseding event received
after a reveal of that study's proposal, by that screener and in the current
generation, is stamped `changed_after_reveal: true`, whether or not the outcome
changes; the methods paragraph can compare outcomes from the event chain.
Events stored before M1b-0 keep `false`, which for them means "not tracked".

## 2026-11-04 — `accept-corpus` is the screening entry path until Packet B (M0)

`nexus-scholar accept-corpus` builds the Contract-v1 corpus snapshot with the
search kit's `build_corpus_snapshot_artifact` from `literature/verified.json`.
It publishes the snapshot through the existing acceptance gate, which
validates it against the frozen schema and journals the acceptance; `prepare`
then works on a fresh workspace.
- **RIS import:** `--ris <file>` imports a RIS export first. Each record gets
  a record-derived `SCI-` id (from title, year, DOI and author names), so a
  re-import yields the same ids. The import refuses to overwrite an existing
  `verified.json`.
- **Re-runs:** re-running on unchanged records publishes nothing.
- **No CSV importer:** none exists yet, so CSV is deferred.
- **Snapshot semantics unchanged:** the builder and acceptance are reused as
  they are, so the lane stays STANDARD.
- **Packet B:** full adoption, with discovery producing the snapshot itself,
  remains M3.

## 2026-11-04 — Approval: terminal-only code; event-decided batches need no worker step (CON-02/03)

**The code stays on the terminal.** The approval code is printed only in the
terminal running `nexus-scholar serve`, never returned over HTTP, and the
researcher types it into the publish screen. This keeps the existing pinned
rule: something that can call the console API (a malicious page that got the
token, another local process) still cannot approve on its own. The contract's
`qr_payload` for `pairing/begin` is dropped; spec 09 follows.

**Events replace the worker step.** A batch decided entirely by human decision
events is approved on its event projection. No worker recommendation is
required. The approval binds that batch's projected bytes only, never another
batch's (CON-03), and the approver is recorded as an unauthenticated local
attestation, not an identity (CON-02). The worker path stays for
agent-screened batches. Researcher's choices, 2026-11-04.

## 2026-11-04 — The v03 screening labels are human-confirmed: the M1b eval set

`uav-crop-weed-v03` has a signed screening confirmation:
`literature/screening/HUMAN_CONFIRMATION.json` (`HumanConfirmation@1`, PR
#172, 2026-10-31). Its lead reviewer, Mouadh BEKHOUCHE, confirmed all 14,150
agent decisions and changed none, and the record pins the 283 decision files
by SHA-256. The M0 note that v03 had no human labels was wrong: it read the
README and the `decision_status: FINAL_AGENT_UNCONFIRMED` fields and missed
this record.

**Consequences:**
- The v03 labels are the human-confirmed eval set for the M1b prompt gate
  (agent-system §5).
- The 200-record AI reference screening (`method: LLM`, 2026-11-04) is no
  longer needed as a stopgap. It stays available only as a model-versus-human
  comparison.
- The stale status fields are not rewritten: they sit in hashed decision
  files, a published report and the append-only journal. The README says so,
  and a `SCREENING_CONFIRMATION_RECOGNISED` journal row records that the
  confirmation supersedes them.

**Caveat for the methods text:** these are confirmations of agent drafts,
none changed. The eval measures recall against labels a human reviewed with
the draft in view, not against independent blind screening.

## 2026-11-04 — Unclear records go forward to full text (PRISMA)

A record the researcher marks Unclear (stored as `MAYBE`, labelled "Unclear →
full text") passes title and abstract screening. In the PRISMA flow it is
counted in "records sought for retrieval" with the includes, and shown on its
own line (`unclear_to_full_text`), never with the exclusions. The collector
stops refusing `MAYBE` at finalize (M1a), and `check_golden_workspace.py`
reconciles included + unclear + excluded + conflicts with records screened.
Researcher's choice, 2026-11-04.

## 2026-11-04 — CON-13 is guarded outside the Contract v1 lock

`contracts/acceptance.py` and `contracts/chain.py` check batch identity,
binding and membership only when a `screening_decisions` artifact has exactly
one `screening_batch` parent; zero or several parents skip those checks
(CON-13). Both files are locked by the Contract v1 baseline. Rather than a
contract change, the harness refuses to submit a decisions artifact without
exactly one batch parent, before it calls the frozen gate (M1a). A caller that
bypasses the harness and calls `accept_artifact` directly is not covered; that
gap is recorded for Contract v1.1. Researcher's choice, 2026-11-04.

## 2026-11-04 — Console guards and the `--lan` threat model (INC-01)

**Threats.** In stage 1 the console holds unpublished review data and can run
kit commands. Three kinds of caller can reach it:
- a web page in the researcher's browser: cross-site requests, and DNS
  rebinding through a name that resolves to 127.0.0.1;
- another process on the machine, including an AI agent's sandbox;
- from M2, a device on the same LAN.

**Guards, on every request** (`console/serve.py`):
- **Host.** The `Host` must be a loopback name (`HOST_REFUSED`).
- **Origin.** A browser `Origin` must be loopback (`ACTION_ORIGIN_REFUSED`,
  the code the screening actions already used).
- **Token.** Every route except `/healthz` needs `Authorization: Bearer
  <token>` (`TOKEN_REQUIRED`). `serve` takes the token from
  `NEXUS_CONSOLE_TOKEN`, or generates one and prints it once.
- **Loopback bind.** `serve` refuses a non-loopback `--host`.

**What a caller can run.**
- **Pipeline nodes** may run only the kit CLIs and the screening handoff
  script (`COMMAND_NOT_ALLOWED` in `validate_spec`). This applies in the
  console and in `scholar-harness run`; tests that run `python -c` stub nodes
  extend the list explicitly.
- **Jobs** run only in the served workspace (`WORKSPACE_MISMATCH`).

**The UI proxy** adds the token server-side, so the browser never holds it. It
answers only on a loopback host and forwards a POST only when its `Origin` is
the app's own.

**Residual risk, accepted for stage 1.** A process running as the same user
can forge `Origin` and POST through the proxy. It already has the user's
files, so this grants no new privilege. M5-slim serves the UI from the same
FastAPI process and replaces the proxy with a session cookie.

**`--lan` (M2).** It never exposes this app. `nexus-scholar ui --lan` mounts a
separate restricted sub-app on the LAN address:
- **Routes:** screening reads and decision-event POSTs only. The jobs,
  pipelines, streams and audit-writer routers are never mounted there; a test
  proves they are unreachable.
- **Pairing:** a phone pairs through a one-time token in the desktop QR code.
  The token lives 2 minutes and is exchanged for a session cookie scoped to
  the sub-app; no token appears in a URL after the first load.
- **Session end:** on stop, on process exit, or after 12 hours.
- **Transport:** plain HTTP on the LAN, so someone on the network can read
  abstracts and decisions in transit. That is accepted for stage 1, shown on
  the pairing screen, and fixed by opt-in HTTPS (`mkcert`) or the sync tier.
- **Desktop only:** approval stays on the desktop (contract §4, §9.1).

## 2026-11-04 — MCP tool paths are contained in the workspace (AGT-01)

Every path argument of a `scholar-agent` tool, for reading and for writing, must
resolve inside the MCP workspace (`--workspace`, else `NEXUS_MCP_WORKSPACE`, else
the repository root). Relative paths are joined onto it; absolute paths are
allowed only when they land inside it. Symlinks and `..` are resolved first. An
escaping path raises `PathOutsideWorkspace` (`PATH_OUTSIDE_WORKSPACE`) before
any I/O, which the MCP client sees as a tool error. Consequence: a researcher
who wants a tool to read a file elsewhere (a PDF in Downloads) copies it into
the workspace first. Reads are contained too, because an agent could otherwise
use a reader tool to pull any local file into its context. Path parameters never pass
anything through by its content (`'["/../x"]'` is valid JSON and, on POSIX, a
legal path). Only the four parameters that accept an inline payload
(`intent_json`, `protocol_json`, `screeners_json`, `adjudication_json`) keep a
value that parses as JSON, and never open it as a path (review findings, M0).

## 2026-11-04 — MCP keys stay in the env file, never in a config file (CORE-17)

`setup-mcp` used to copy provider keys from `.env` into an `env:` block of each
MCP config, including `<workspace>/.mcp.json` and `.cursor/mcp.json`, which git
tracked. Now it adds `--env-file <path>` to the server command, and
`scholar-agent` loads the approved keys (`SCHOLAR_*`, `NEXUS_*`, the three
provider keys) from that file at start. Variables already set in the
environment win. No config file holds a key value, VS Code works like the
other targets, and `.env`, `.mcp.json` and `.cursor/mcp.json` are gitignored.
Configs written by older versions keep their `env:` block until `setup-mcp` is
run again.

## 2026-11-04 — Screening API contract accepted

The researcher decided the contract's six open questions:
- a fresh approval code for each batch generation, refused while any phone has queued events;
- an OS file lock on each screener's event file;
- an Exclude on the phone needs a reason only, with no checklist;
- 200 events per request, with the UI sending larger backlogs in chunks;
- methods-paragraph wording and sample-audit size deferred to M5-slim;
- a dated price table, updated each release, behind the cost estimate.

All nine screening screen specs are now FINAL. Details:
[`architecture/screening-api-contract.md`](architecture/screening-api-contract.md) §9.

## 2026-11-03 — Plan revised after independent review: screening wedge at week 6

An independent review of the production plan found that screening could not be
reached before week 6: no code builds a corpus snapshot outside tests, and the
import path was not scheduled. It also found that M1 was too large for one
person. The researcher accepted three changes:

- **Order.** M0 (adding a minimal `accept-corpus` entry path) → M1a screening
  backend → M1b desktop UI and driver → M2 mobile → M5-slim package, where the
  wedge ships. Discovery (M3) is stretch. The web Inception wizard (M4) moves
  past the two-month horizon; inception stays CLI/MCP, labelled beta.
- **You see every record by default.** The agent orders the queue and
  proposes. Exclusion without a human look is an explicit opt-in with a sample
  audit, and the methods paragraph discloses it (PRISMA 2020 item 8).
- **Unclear is stored as the existing `ScreeningDecisionValue.MAYBE`.** It is
  labelled "Unclear → full text". There is no Contract v1 version change; only
  the collector's refusal of MAYBE at finalize changes, in M1a.

The review also moved the prompt-gate eval from the 30-record golden workspace
to the human-labelled `uav-crop-weed-v03` screening data (at least 200 records,
at least 30 includes). It restricted `--lan` to a sub-app without the
job-running routers, and keyed decision IDs on the client event ID so replays
cannot void approvals. Details: `roadmap/production-plan.md` §2, §4, §6;
`architecture/agent-system.md` §2–§6, §8.

## 2026-11-03 — Agent system: proposals only, least autonomy per job

The AI behind Phases 0–2 is built as versioned *tasks*: a prompt, an output
schema, a model and effort setting, and an eval set. Most tasks are plain code
or single structured calls. Only the inception conversation and the
researcher's own Claude Code or Claude Desktop (through MCP) run agent loops.
Model output is always a proposal in an append-only store with full provenance
(model, prompt hash, input hash, checks, usage). Plain-code validators check
each proposal, and anything that fails, refuses or is truncated goes to the
researcher as Unclear, never Exclude. Only the engine writes artifacts and the
journal, and only after a human decision. The in-app driver (the researcher's
own API key, with Message Batches and prompt caching) and the MCP driver share
the same tasks. Changing a prompt, model or effort setting needs a new task
version and an eval re-run, mirroring the contract-baseline gate. Default
model: `claude-opus-5-5`. Open: whether to keep Gemini, whether to build the
in-app inception chat, and whether a cheaper screening model holds recall.
Design: [`architecture/agent-system.md`](architecture/agent-system.md).

## 2026-11-03 — Claude Code dev workflow and area-based test gates

The OpenCode four-agent loop is no longer the development workflow; the files
stay, baseline-locked, as history. Development runs in Claude Code with three
project slash commands (`/milestone`, `/gate`, `/ship` in `.claude/skills/`) and
four narrow subagents (`.claude/agents/`): a read-only finding auditor, a test
gatekeeper, an independent milestone reviewer, and a UX spec writer. The
researcher approves milestone starts, contract decisions and every push.

The test selector was keyed to E3 RAG tasks, so after the one-package merge a
screening edit selected an unrelated RAG test and a search, protocol or UI edit
fell back to the full ten-minute Python suite. Selection is now by source area
(`areas` in `docs/architecture/test_gate_manifest.json`, `--changed` from git).
Inner gates skip `@pytest.mark.slow`, and the PR gate runs the full suite once in
parallel (`pytest-xdist`, `-n auto`). The full suite still runs once per PR
candidate; that rule did not change. Details are in
[`architecture/test_gate_policy.md`](architecture/test_gate_policy.md) §Selector.

## 2026-11-03 — Deployment: local engine first, hybrid sync later (option C staged from A0)

Nexus Scholar ships first as a local engine. `uv tool install nexus-scholar`,
then `nexus-scholar ui`, serves the static-exported research UI and `/api/v1`
from the one FastAPI process on loopback, behind a per-launch token. `--lan`
plus a QR code lets a phone on the same network screen. Workspaces stay local
folders, with no hosted infrastructure. AI proposals come first from the
researcher's own Claude Code or Claude Desktop through the `scholar-agent` MCP
server, which writes proposals only. A bring-your-own Anthropic key is the
second path, for in-app runs. Whether Gemini stays as a third option is open
(`architecture/agent-system.md` §9). The maintainer never pays for or resells
tokens. The engine, UI and MCP server stay MIT. Paid features (end-to-end
encrypted sync of decision and journal events, team dual screening with real
κ, institutional SSO) go in a separate proprietary service, built only after
10–20 real users. Stage 1 sells onboarding and support, not code-gated
features. A signed desktop app (Tauri with a Python sidecar) waits for user
demand. Hosted web-first (option B) was rejected: it contradicts the privacy
of unpublished reviews and adds operations work that one maintainer cannot
carry. The full option study is in
[`roadmap/production-plan.md`](roadmap/production-plan.md) §5.

## 2026-11-03 — Brand book replaces VISUAL_DIRECTION as the UI design system

`docs/ux/brand/tokens.json` and `BRAND_BOOK.md` become the design system of
record for `apps/research-ui`. This reverses VISUAL_DIRECTION decision D1 (no
web fonts, no radius, light only). Tokens generate the Tailwind 4 theme, with
light and dark modes. The fonts (Literata, Public Sans, IBM Plex Mono) are
self-hosted, not loaded from Google, so the tool works offline and makes no
third-party calls. VISUAL_DIRECTION rules that do not conflict are kept as
amendments. GATES and the browser colour tests are updated in the same PR.

## 2026-11-03 — Production scope: Inception, Discovery, Screening over two months

Only Phases 0–2 are brought to production, on the two-month sequence M0–M5 in
[`roadmap/production-plan.md`](roadmap/production-plan.md) §6. Screening comes
first. The quality gate is a real end-to-end run on the golden UAV workspace,
not the autonomous agent loop. Everything else is labelled "not production —
parked" in UI, docs, CLI and MCP.

## 2026-11-03 — One package instead of eight kit repositories

The harness and the eight `scholar-*-kit` packages ship as one distribution,
`nexus-scholar`, from the root `pyproject.toml`. Kit code lives in
`src/scholar_<kit>/`, kit tests in `tests/kits/<kit>/`. The per-kit repositories,
vendored snapshots, `plugins.json` pins, pin codegen, installer and separate
metapackage were removed: syncing eight repositories cost a single maintainer a
great deal and bought nothing while no one installs a kit on its own. If a kit
gains independent users it can be split out again with `git subtree split`.
Contract producer provenance keeps the component names and now reports the
package version and repository commit. See the
[assessment](assessment/README.md) for why this came first.

## 2026-11-03 — Fresh assessment replaces earlier audit material as the current view

[`assessment/`](assessment/README.md) is the current, evidence-backed view of
the harness and kits, with a ranked P0/P1/P2 list. Older dated reviews remain
as history only.

## 2026-10-26 — Human confirmation is a separate package outside the frozen baseline (Phase C)

`contracts/confirmation/` and its schema sit outside the non-recursive globs
that `generate_contract_baseline.py` hashes, so adding confirmation did not
change the frozen Contract v1 payload. The refusal registry is imported, never
extended. Behaviour: [`architecture/confirmation.md`](architecture/confirmation.md).
Spec: `specs/agent-layer-portability/06_human_confirmation.md`.
Original record: `docs/architecture/decision_phase_c_confirmation_2026-10-26.md`.

## 2026-10-26 — The agent envelope is a package, not a flat module (Phase B)

`scholar_harness.contracts.envelope` is a package for the same reason: a flat
module or a schema under `schemas/v1/` would have entered the frozen lock set.
Refusal codes: [`architecture/refusals.md`](architecture/refusals.md).
Spec: `specs/agent-layer-portability/02_envelope_and_refusals.md`.
Original record: `docs/architecture/decision_phase_b_envelope_2026-10-26.md`.

## 2026-10-25 — Agent roles are generated from `roles/*.json` (Phase A)

Role definitions (`roles/*.json` plus prompts) are the source; the OpenCode
agent files are generated by `scripts/generate_agent_roles.py`. Write
permissions are derived (a critic is denied what it judges; `deny_glob` is a
write denylist; `audit/journal.jsonl` is protected).
Spec: `specs/agent-layer-portability/01_role_model.md`.
Original record: `docs/architecture/decision_phase_a_role_generation_2026-10-25.md`.

## 2026-10-23 — T-SC1 accepted without a recorded independent review (accepted risk)

PR #144 (cross-kit canonical and identifier parity pin) entered `main` without
the independent reviewer and tester evidence the gates require. The researcher
accepted that risk explicitly; it is not a precedent for skipping review.
Original record: `docs/architecture/decision_t_sc1_acceptance_without_review_2026-10-23.md`.

## 2026-10-13 — Product direction: the individual researcher

The first user is an individual researcher running a review directly in Nexus:
a local research service with a browser review interface, with CLI and MCP as
advanced interfaces. First journey: provisional protocol → bounded retrieval →
review recommendations with preserved overrides → authorized screening
decisions → transparent screening record. Full-text charting and synthesis
follow as separately validated capabilities.
Original record: `docs/architecture/decisions/individual-researcher-product.md`.

## 2026-10-12 — TD-E3-CURRENTNESS: stale extracted bodies are refused (Option B)

When an extracted body is stale, the indexing stage writes one
`RAG_INDEX_REJECTED` event and returns the typed `STALE_EXTRACTED_BODY` refusal
before any backend call or index publication (it previously crashed on an
unsupported `parameters=` argument).
Original record: `docs/architecture/decisions/td_e3_currentness_decision.md`.

## 2026-10-12 — Agent instructions must reference files that exist

The baseline-locked agent definitions pointed at two spec files that never
existed; they were corrected to `10_cross_kit_contracts.md` and
`12_execution_roadmap.md`. Backticked paths are not caught by link checks, so
such references need review.
Original record: `docs/architecture/decisions/agent-instruction-reference-repair.md`.

## 2026-10-10/12 — Authorized screening: protected publisher, restricted worker (AG)

The researcher approved a protected local publisher with a restricted
scientific worker: agents may propose screening decisions, but publication of
final decisions requires the researcher's authorization. Approval of the
direction is not proof of isolation; the
[assessment](assessment/harness-contracts-screening.md) (CON-02/03) found the
authorization still bypassable.
Current state: [`architecture/agent-controls/README.md`](architecture/agent-controls/README.md).
Original record: `docs/architecture/agent-controls/agent_controls_decision.md`.
