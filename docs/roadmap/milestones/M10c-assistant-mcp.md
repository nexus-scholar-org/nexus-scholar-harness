# M10c-assistant-mcp: an assistant and a critic over MCP
Branch: `dev/m10c/assistant-mcp` (from `origin/main` at `7cd5fdca`) · Lane: **RELEASE** · Status: **BUILT (D0 to D9)**; decisions 1 to 14 accepted 2026-11-19 (item 9 as option (a)), 15 to 21 proposed; PR gate and review: see Evidence · Started: 2026-11-19

Third milestone of "Assisted inception" (approved 2026-11-14). Plan §6 row **M10c-assistant-mcp**: an assistant and a critic over MCP, no AI spend, with the test set of broken protocols (PR #238) the critic must catch; M9d-discovery-assistant's MCP half (synonyms, translation explanations, recall repair as proposals, `agent_autonomy_ladder.md` §8) is delivered here.

**Lane.** RELEASE, per `docs/architecture/test_gate_policy.md` ("public API, CLI, or MCP semantics"): new MCP tools are a public surface; the inception and discovery check answers gain rows with `source: "agent"` and `sources: ["check", "agent"]`; the draft record gains a key; the draft store takes an OS lock shared by two processes; and, with decision item 9(a), three console routes, one refusal code (`PROTOCOL_AMENDMENT_REFUSED`) and a protocol write after genesis. No Contract v1 model, schema or golden fixture changes (checked below): `audit/proposals.jsonl`, the draft record and the check answers are outside the baseline (`contract_v1_baseline.json` names none of them; `generate_contract_baseline.py --check` is current at `7cd5fdca`).

**Not in this milestone.** The in-app chat (M10e). Any AI call from the app or the tests. Any change to the Explore screen, the next-step bar or `EXPLORE_SAMPLE_MOSTLY_LEFT_OUT` (M10b Part C, in parallel). Lighter screens (M10d).

## Design

The AI is the researcher's own MCP client (Claude Desktop or Claude Code). The engine gives it read tools, and two write tools that only ever add a suggestion: a **proposal** (the M10b object, `01-proposals`) or a **finding** (a row of the M10b check object, `02-checks` "The slot for M10c"). Nothing it sends changes an answer, the draft's `updated_at`, the protocol or the corpus. The researcher applies, edits or rejects a proposal, and dismisses a finding, on the existing cards and panel.

### Where an assistant acts
Two targets, the two the app already has:
- **an inception draft** (`rec_…`, under the workspaces root, `resolve_root()` as the console uses it): before genesis;
- **a workspace** (a folder with `protocol.json` and `intent.json`): after genesis, Discovery.

### Tools (new, in `src/scholar_agent/server.py`; logic in `src/scholar_harness/assistant/`)
| Tool | Reads or writes | What |
| :-- | :-- | :-- |
| `nexus_assistant_drafts` | reads | The drafts under the workspaces root: id, topic, title, `updated_at`, emitted or not, open proposals and findings. |
| `nexus_assistant_read_draft` | reads | One draft: its answers; the **intent** it compiles to (`build_intent`, or the compiler's refusal); the fixed checks as the app computes them (nothing recorded: the check POST's proposal recording is not run); every proposal with its derived status; the findings; a summary of the recon pool (databases, counts, the sample's titles and DOIs) when there is one. |
| `nexus_assistant_read_workspace` | reads | One workspace: `intent.json`, `protocol.json`, the discovery plan (each database's translation and its `cannot_express` list, the cap), the last recall check (seeds found and missed per database), the discovery checks (findings among them), the workspace's proposals (`proposals`, as Plan lists them) and every line of `audit/proposals.jsonl` (`proposal_history`). |
| `nexus_assistant_propose` | adds one open proposal | A change to one field (`field`, `op`, `value`, `why`, `evidence`), with `model`, `task`, on a draft (`session_id`) or a workspace's search (`workspace_dir`). Source `agent:<model>`. |
| `nexus_assistant_report_finding` | adds one finding | The critic: a `locator` (a JSON pointer into the intent), a `severity` (`critical`, `major`, `minor`), the finding sentence, an optional `why`, with `model`, `task`. |

No tool starts a search or a harvest, accepts a corpus, writes a screening decision or publishes (decision 2026-11-14, item 3; item 11 below for the existing recon tools).

### An assistant's proposal
The M10b object unchanged, with:
- `source: "agent:<model>"` (the name the client gives for its own model, `[A-Za-z0-9._:-]{1,64}`, required, like `nexus_submit_proposal`'s `model`), and one extra key `agent: {model, task, task_version}`; `task` is one of `suggest`, `synonyms`, `translation`, `recall_repair` (M9d's three tasks and a general one), `task_version` is the tool's (`assistant-v1`);
- made by the same `proposals.make` against the draft as it is now (content-derived id: sending the same suggestion twice records it once); the value is checked at creation by applying it to a copy of the draft and running `parse_draft(saving=True)`, so a suggestion the draft could not take is refused before any card shows it;
- recorded by a **side write** (`DraftStore.transact(answer=False)`): no field changes, `updated_at` does not change, so the researcher's open tab never gets `DRAFT_CONFLICT` because an assistant spoke; refused `DRAFT_EMITTED` after genesis;
- shown on the existing card and list (step derived from the field), applied only by the researcher's Apply; genesis already writes it into `audit/proposals.jsonl` and `PROPOSALS_RECORDED` already counts sources by kind, so `agent` appears there without a change.
The browser still cannot create a proposal (no create route); `PROPOSAL_SOURCE_REFUSED` keeps refusing `agent:*` from any path but the assistant's.

### An assistant's finding (the critic)
A finding is a check row (`02-checks` "The check object") with `check_id: "ASSISTANT_FINDING"`, `subject: "find_<12 hex>"` (content-derived from locator, sentence and model, so a re-send is a no-op), `source: "agent"`, `agent: {model, task: "critic", task_version}`, `severity`, `level` (`warning` for critical and major, `note` for minor, never `blocker`), `step` (computed by the engine from the locator), `message` (the assistant's sentence, shown as its words), `why` (optional), `evidence` (the locator, and the hash of the located value when it was made), `action` (a link to the field's screen), `dismissible: true`. It is listed by the same check endpoints in the same list, counted in `by_step`, dismissed and restored by the same routes into the same record (`check_dismissals`; a warning needs a reason). It never makes `ready` false. When the located value has changed since, the row says so (`outdated: true`) and stays until dismissed.
- **Locator: a JSON pointer into the intent** (decision item 4): the same shape before genesis (the draft's `build_intent`) and after (the workspace's `intent.json`), and the shape the critic test set's manifest uses. A pointer must resolve in the current intent, or point at a missing element of a list or object that exists (to name what is absent). `draft:/…` points into a draft's answers (an incomplete draft has no intent), `protocol:/…` into a workspace's `protocol.json`.
- **Where a finding is kept** (decision item 5): on a draft, a new side key `assistant_findings` of the draft record, beside `proposals` and `check_dismissals`; on a workspace, `audit/assistant_findings.jsonl` (append-only, a `reported` line per finding), with an `ASSISTANT_FINDING_REPORTED` journal row. Findings are not carried at genesis (item 6).

### The discovery half (M9d over MCP)
- **Synonyms**: before genesis, a proposal on `concepts[<concept>].synonyms` (exists today). After genesis: a workspace proposal (item 9).
- **Translation explanations**: a read. `nexus_assistant_read_workspace` returns each database's executed form and `cannot_express`; the assistant explains it in its chat. Where it suggests another way (a language limit applied at screening instead), that is a proposal or a finding.
- **Recall repair**: the read returns the last recall check's missed seeds; the smallest change that would find one (a synonym, a wider year) is a workspace proposal (item 9).

### Workspace proposals (D5, item 9 option (a), accepted 2026-11-19)
- **Made** by `nexus_assistant_propose(workspace_dir=…)`: a `proposed` line in the workspace's `audit/proposals.jsonl` with `target.kind: "workspace"`, `step: "plan"` and `base.protocol_fingerprint`; journal `ASSISTANT_PROPOSAL_RECORDED`. Only the search (item 16): `core_concepts` add, `core_concepts[<name>].synonyms` add or remove, `start_year` and `end_year` replace, `languages`. Checked when made exactly as Apply would check it; refused once a corpus is accepted; at most 30 open.
- **Shown** on Discovery Plan, above the checks panel (`components/discovery-proposals.tsx`): the source with the model, the change, the assistant's why, Apply and Reject; a stale card says "The protocol changed after the suggestion was made." and offers only Dismiss; Apply is disabled with a line when the corpus is accepted or a search runs. Nothing shows while there is no suggestion.
- **Applied** only by `POST /api/v1/discovery/proposals/{id}/apply` (`scholar_harness/workspace_proposals.py`): refused while a discovery job runs (`DISCOVERY_JOB_ACTIVE`) and once a corpus is accepted (`CORPUS_ALREADY_ACCEPTED`); the amended intent is compiled with genesis's `compile_intent`, and the result may differ from the current `protocol.json` only under `search_strategy.core_concepts`, `.date_range`, `.languages`, else `PROTOCOL_AMENDMENT_REFUSED` and nothing is written (item 17). Then the backup under `audit/amended/<stamp>/`, the three files, the `applied` line, `PROPOSAL_DECIDED` and `PROTOCOL_AMENDED` (item 19). Reject writes a `rejected` line and `PROPOSAL_DECIDED`.
- **What a moved fingerprint does** (item 21): every other open workspace proposal is stale. An accepted corpus is never amended: Apply refuses once one is accepted, so the snapshot keeps the fingerprint it was accepted under. If the protocol were changed by hand after acceptance anyway, the existing F2 and snapshot signals apply (screening reads `protocol_changed`, earlier decisions count nowhere; a resumed run refuses `PROTOCOL_CHANGED_SINCE_SNAPSHOT`). Before acceptance, earlier runs read `search_changed` and their hand-off accept is refused `PROTOCOL_CHANGED_SINCE_RUN`, so the researcher searches again; earlier recall checks and estimates stop applying (keyed by fingerprint).

### The critic test set, run with no AI
`scripts/critic_set.py prepare <dir>` makes one workspace per document of `tests/fixtures/critic_protocols` (42: 40 variants and 2 bases; `intent.json` and the compiled `protocol.json`, as genesis writes them; the protocol-format variants get the protocol only). `scripts/critic_set.py score <dir>` reads each workspace's `audit/assistant_findings.jsonl` and scores it by the README's rule 1(a) (the locator is one of the defect's `fields` or `accepted_locators`, or contains one) and its rule 3 (major or critical findings on a base are false alarms); rule 1(b), "states the same problem", is a judgement left to a human or a separate judge, and the score says so. The test drives the real tool functions with three scripted clients: an **oracle** (the manifest's own findings: every defect is located, no false alarm), a **silent** client (nothing caught) and a **fixed-checks-only** client (it reports what the fixed checks report, so its ceiling is visible). A real critic run with the researcher's client uses the same two commands; it is not run in this milestone.

## Definition of done
- [x] D0 This record: design, lane, DoD; decision items in `docs/decisions.md` (2026-11-19); the researcher accepted items 1 to 14 on 2026-11-19 (item 9 as option (a)); items 15 to 21 (D5's build choices) proposed.
- [x] D1 **One lock across processes.** `DraftStore` writes take an OS lock on the draft (beside the thread lock), so the MCP server and the console cannot lose each other's keys. Reproducing test first: two processes interleave a side write and an answer write. `tests/console/test_draft_store_lock.py`.
- [x] D2 **Read tools.** `nexus_assistant_drafts`, `nexus_assistant_read_draft`, `nexus_assistant_read_workspace`; they write nothing (test: no file changes under the root). `tests/kits/agent/test_mcp_assistant.py`.
- [x] D3 **Assistant proposals on a draft.** `nexus_assistant_propose`: `agent:<model>` source and `agent` key; a side write (`updated_at` unchanged); value checked by `parse_draft`; idempotent; `DRAFT_EMITTED`; limit (item 7); provenance required; shown in `GET …/proposals` and applied, edited, rejected by the M10b routes; genesis counts `agent`. Tests: `test_mcp_assistant.py`, `tests/console/test_inception_proposals.py`.
- [x] D4 **Findings.** `nexus_assistant_report_finding` on a draft and a workspace; agent rows in `POST /inception/drafts/{id}/checks` and `GET /discovery/checks`, `sources` lists `agent`; dismissal and restore by the existing routes; `outdated`; never `blocker`, `ready` unaffected; locator validation. Tests: `test_mcp_assistant.py`, `tests/console/test_inception_checks.py`, `tests/console/test_discovery_checks.py`.
- [x] D5 **Workspace proposals** (item 9(a)): made over MCP, listed on Plan, applied or rejected only by the researcher's routes; Apply amends only the search and recompiles; refused while a search runs and once a corpus is accepted; stale when the fingerprint moved; negative test: an Apply that would change a field outside the search (the intent's title edited after the suggestion) is refused and writes nothing. `tests/kits/agent/test_mcp_workspace_proposals.py` (18), `apps/research-ui/tests/discovery-proposals.test.tsx` (5).
- [x] D6 **Limits.** No new tool starts a search or harvest, accepts, decides or publishes (a test lists the new tools against the forbidden actions); item 11 for the recon tools. Test: `test_mcp_assistant.py`.
- [x] D7 **UI**: a proposal card names an assistant and its model; a check row from an assistant shows "Assistant", its own words (`dir="auto"`) and the outdated line; nothing else on the screens changes. Vitest: `apps/research-ui/tests/proposals.test.tsx`, `checks-panel.test.tsx` (the M10b test "agent source is not rendered" is replaced).
- [x] D8 **The critic test set, no AI.** `scripts/critic_set.py prepare|score`; `tests/kits/agent/test_assistant_critic_set.py`: oracle locates 43 of 43 defects with no false alarm on the bases, silent 0, a noisy client's major finding on a base is counted as a false alarm; every finding stored and journaled as an agent row. (The design's "fixed-checks-only" client was dropped: the discovery checks that can run on a protocol alone point at `/core_concepts` as a whole, so the locator rule would credit them with defects they do not name; the README's "a critic that only restates the fixed checks catches at most 12" stays a statement, not a test.)
- [x] D9 **Docs.** `docs/architecture/inception-api.md` (agent rows, the record key), `docs/kits_surface_matrix.md` and `.agents/skills/scholar-agent-kit/SKILL.md` (tool count and the assistant tools, how a client should use them), the tool-count tests.
- [~] D10 **Gates.** `select_test_gate.py --changed origin/main` inner and checkpoint; `generate_contract_baseline.py --check`; ruff (both CI runs); the PR gate once on the final executable commit; `milestone-reviewer`; READY FOR PR, not pushed.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| (D1) a second process's draft write can lose a key | `test_draft_store_lock.py::test_a_side_write_in_another_process_does_not_undo_a_save` | yes, at `418e56da`: the save was lost (`{'topic': 'first words'}`) | yes, at `eb5acc4a` |

## Decisions
`docs/decisions.md`, "2026-11-19 — M10c: assistant and critic over MCP": items 1 to 14 accepted by the researcher 2026-11-19 ("Go with your recommendations", relayed word for word by the main session; item 9 as option (a)); items 15 to 21, D5's build choices, PROPOSED.

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| baseline | `7cd5fdca` | `uv run python scripts/generate_contract_baseline.py --check` | current | |
| D1 reproducing test | `418e56da` + test | `pytest tests/console/test_draft_store_lock.py` | failed (the save was lost) | |
| checkpoint | `819d7f78` | `select_test_gate.py --changed origin/main --stage checkpoint` (each command with `--no-sync`, `-n 6`, extras dev+pdf+rag): `git diff --check`; `tests/console tests/authority`; `tests/inception tests/recon …`; `tests --ignore=tests/kits`; `tests/kits/agent tests/mcp …`; skills bundle check; baseline check; both ruff runs; UI typecheck; `npm test` | 5 failures, all count or seam gates this change had to move: E1/E2/recon tool counts 27 → 32, evidence-boundaries and skill counts, one `search_fn=RECON_SEARCH_FN` seam; fixed in `1852e969`; everything else passed (UI 718 of 718) | about 17 min |
| re-run of the failed | `1852e969` | `pytest tests/conformance tests/mcp tests/unit/test_recon_adapter_characterization.py tests/kits/agent/test_mcp_assistant.py tests/kits/agent/test_assistant_critic_set.py -n 6` | passed | |
| contract | `819d7f78` | `generate_contract_baseline.py --check` | current | |

## Not verified
- No MCP client session with an AI has been run against these tools; the critic's real recall on the test set is unknown. The scripted clients prove the path, not the critic.
- `nexus_assistant_read_workspace` runs in the MCP process, so it does not see a discovery job running in the console (`active_job` is the console's); Plan's listing does.
- Apply checks the console's running job and then writes; a search started in the same instant (the async start route on the event loop, the Apply in a worker thread) is not excluded by a shared lock. Not reproduced; the window is the duration of the Apply's compile and three file writes.
- No Playwright run of the Plan cards (Vitest over the fake engine only); no live recall repair: the recall check's missed seeds were not turned into a proposal by a real client.

## Deferred
