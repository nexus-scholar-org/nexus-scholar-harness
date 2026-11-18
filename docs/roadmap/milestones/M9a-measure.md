# M9a-measure: measure the screening agent against the researcher's decisions
Branch: dev/m9a/measure-harness · Lane: **STANDARD** (see the lane note) · Status: **HARNESS BUILT; THE MEASUREMENT HAS NOT BEEN RUN. It needs the researcher's approval of AI spend** (all AI spend is deferred, 2026-11-18) · Started: 2026-11-18

Plan: [`production-plan.md`](../production-plan.md) §6 row M9a-measure. Design: [`agent_autonomy_ladder.md`](../../architecture/agent_autonomy_ladder.md) §4 (the gate), §9 (decisions of 2026-11-10, amended 2026-11-11), §10. The screening drivers and the first evaluation came with [`M1b-2.md`](M1b-2.md) (the `prompt-gate` group).

**What this milestone is.** The ladder sets its gates (draft: L1 35 includes and recall lower bound 0.90; L2 75 and 0.95) before any measurement of the agent exists. M9a-measure runs the agent once over the researcher's own decisions and reads the real numbers (include recall, precision on includes, how many records it leaves Unclear, truncations, tokens and cost) so the thresholds are set from data. This branch prepares that run so it is one command and spends nothing until the researcher approves it. Nothing in it calls a language model: the dry run reads files, and the tests use a scripted driver.

**Lane note.** The researcher set STANDARD for this preparatory work (2026-11-18). The review (round 1) pointed out that `test_gate_policy.md` sends public CLI semantics to RELEASE and that M1b-2, which created the `prompt-gate` group, was escalated. The case for STANDARD: `measure` is an additive maintainer command in the existing `prompt-gate` group; it adds no route, no MCP tool, no Contract v1 model, schema or fixture and changes no product behaviour (`agent_runs` is untouched; the one shared function whose behaviour changed, `prompt_gate.score`, has a single product caller that already maps labels first). The full suite runs once at the PR gate either way. Escalating to RELEASE is the researcher's call; it would add the clean-venv wheel checks only.

## What already existed (reused, not rebuilt)
| Piece | Where | Reused as |
| :-- | :-- | :-- |
| The frozen eval set: 644 human-confirmed includes and 1,000 seeded excludes of `uav-crop-weed-v03`, ids and hashes only, text checked against the hashes, decision files checked against `HUMAN_CONFIRMATION.json` | `src/scholar_agent/prompt_gate.py` (`build_set`, `load_set`, `verify_confirmation`), `tasks/screening/eval/v03_set.json` | the default scope |
| The task, the system prompt, the output schema | `scholar_agent.tasks.screening` | unchanged |
| Three drivers (Anthropic Batches, OpenAI-compatible, Gemini), one result type, a failed call is Unclear | `scholar_agent/drivers/` | the real run builds the same driver with the same options as a product run (`direct_limit`, `max_per_batch=CHUNK`, which `prompt-gate run` did not pass) |
| Outcome from the engine's validators and rule table; Wilson bound; dated price table; estimate | `prompt_gate.derive`, `wilson_lower`, `cost_usd`, `estimate`, `prices.toml` | unchanged |
| `prompt-gate estimate`, `run`, `export`, `import` | `src/scholar_harness/cli.py` | left as they are; `measure` is a fifth command |

What did **not** exist: precision on includes, the confusion table, the list of records the agent left undecided, truncated and malformed answers by name, tokens and cost per record, the batches below the ladder's thresholds, a plan that counts batches and gives a range and a hard ceiling, a run that stops at a cost ceiling the way a product run does, a check that the agent is never shown a statistic, and a test of the report on a fake driver.

## Definition of done
- [x] **D1 One command.** `uv run nexus-scholar prompt-gate measure` over a workspace with the researcher's decisions and a provider; no second driver and no second scorer (`src/scholar_agent/measure.py` calls `prompt_gate`).
- [x] **D2 The report.** Include recall (point and 95% Wilson lower bound) with the strict figure if failed calls counted as misses; precision on includes (agent Include, and counting its Unclear); the confusion table with the failed calls; the records the agent left undecided by reason (`cannot_decide`, a failed check, a criterion not reported); truncated, refused, invalid and error ids; failed checks on answers that parsed; tokens and cost per record and in total (and per 1,000); the batches below the draft L1 and L2 recall; the draft gates evaluated review-wide. Written as `measure_<stamp>_<provider>_<model>_<effort>.json` (every record) and `.md` under `.cache/m9a-measure/` (never inside the workspace).
- [x] **D3 Same batches as the product.** Records are sent as a product run sends them: Message Batches of `CHUNK` (200) records for Anthropic above the direct limit, the cost ceiling checked between chunks, a stopped run leaves the rest unreached; the report groups by the workspace's `batch_NNN` files. Differences from a product run, on purpose: no per-provider consent file (the command is the researcher typing `--yes` at a terminal, and it writes no proposals); the ceiling is refused up front when it is below the expected cost, as the product does; per-record cost is kept to 8 places where the product rounds to 4 (D7); the stop is chunk-granular (a Batch's results arrive when it ends, so one chunk of 200 can overshoot the ceiling by its cost, about $1.9 to $3.6 at the Opus figures).
- [x] **D4 The agent is blind.** Before any call the command checks that the system prompt is the task's prompt with the protocol's criteria (nothing appended), that the task's own text carries no outcome statistic or percentage, that the criteria carry no outcome words, and that every request is exactly the record's text (no label, no study id, no database). Ladder decision of 2026-11-11 and lesson 54.
- [x] **D5 Dry run.** `--dry-run` (and a run without `--yes`) prints records, workspace batches, calls, prompt sizes, expected tokens, the estimated cost, the cost with no caching, with heavier thinking, and a hard ceiling; it makes no network call and never reads a key (the tests make a key read or a driver build fail the test).
- [x] **D6 Tested on a fake driver.** `tests/kits/agent/test_measure.py`: scripted answers that include a truncated, a refused, an invalid, a malformed-but-parsed, a `cannot_decide`, a quote-not-in-source, a missed include, a false include and a researcher Unclear; the scorer, every report section, the batches, the gates, the ceiling stop, the blind check, the dry run and the CLI (dry run, no `--yes`, `--yes` with a fake key and driver, a run where no call succeeded).
- [x] **D7 Defects found in the existing evaluation code have a reproducing test first** (see Findings).
- [x] **D8 The exact command and its cost** are below.
- [ ] **D9 The measurement run itself.** NOT RUN. Needs the researcher's approval of AI spend and a key set by the researcher (`nexus-scholar keys set anthropic`).
- [ ] **D10 Thresholds decided from data** (ladder §4 numbers confirmed or changed) and recorded in `docs/decisions.md`. After D9.
- [x] **D11 Gates.** `/gate pr` once on the final executable commit, the contract baseline check, both ruff commands, `git diff --check`, the `milestone-reviewer` verdict: see Evidence (rows filled).

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| `prompt_gate.score` dropped a researcher's Unclear label from the includes and the excludes (the ladder counts it as an include; `calibration_result` already maps it before calling). The v03 labels hold none, so the gate never showed it. | `test_prompt_gate.py::test_m9a_a_researcher_unclear_counts_as_an_include_in_the_score` | yes (`missed_includes == []`, recall 1.0) | yes |
| `prompt_gate.cost_usd` rounds every call to 4 decimals: a Haiku record costs about $0.00015, so per-record and running costs were off by up to a third and a ceiling stopped a chunk late. Totals over many records are unaffected. `cost_usd` gains `ndigits` (default 4, unchanged for the product); the measurement uses 8. | `test_measure.py::test_a_stopped_run_does_not_score_the_records_it_never_reached` (ceiling of four records' cost; the run sent two chunks instead of one) | yes | yes |
| Review round 1 (P2): a gate passed on a run where every call failed (a failed call is Unclear, so kept: 80 of 80 includes kept is recall 1.0). `passes` now needs a run that measured something, and each gate also gives `passes_if_failed_calls_were_misses`. | `test_a_run_where_every_call_failed_passes_no_gate`, `test_a_gate_names_which_figure_passes_when_some_calls_failed` | yes, by arithmetic (`_gate(L2, 644, 644)` passed) | yes |
| Review round 1 (P3): records a driver silently dropped (no stop) were left out of recall without a flag; a smoke run looked like a full run; a key was read before the unpriced check; a ceiling below the estimate was not refused. Each is a warning or an earlier refusal now. | `test_results_a_driver_dropped_without_a_stop_are_flagged`, `test_a_smoke_run_says_so_in_the_report`, `test_cli_refuses_a_ceiling_below_the_estimate_and_an_unpriced_model_before_reading_a_key` | by reading | yes |
| `prompt_gate.report` kept no usage per record. Added `usage` (additive). | `test_measure.py::test_report_on_a_scripted_driver_proves_the_scorer_and_every_section` | n/a (an additive field; the report would show no per-record cost) | yes |

Latent, noted and not changed: `prompt_gate.build_set` keeps only `INCLUDE` and `EXCLUDE` labels, so a researcher Unclear in a workspace is absent from the frozen set. The v03 set is frozen with none (644 + 13,506 + 0), so its hash is unchanged; the measurement's `--scope all` counts the Unclear as an include.

## Decisions
Proposed in [`docs/decisions.md`](../../decisions.md) (2026-11-18, M9a-measure), for the researcher's acceptance.

## The estimate (no network call; `--dry-run`, prices as of 2026-11-11)
The figure the researcher needs to approve. Records and prompt sizes are real (read from `workspaces/uav-crop-weed-v03`, which was not modified); output tokens per record are an assumption (600, thinking included) because no run has measured them. Message Batches, half price.

Scope `frozen` (the gate's sample: all 644 includes and 1,000 excludes = **1,644 records** in 282 of the workspace's 283 batches, 9 calls of up to 200 records; system prompt 1,221 tokens, record 403 tokens on average, 2,203 at most):

| Model (effort low) | Expected | No caching | 1,500 output tokens per record, no caching | Hard ceiling (every record returns `max_tokens`, no caching) |
| :-- | --: | --: | --: | --: |
| `claude-opus-5-5` (the default) | **$11.39** | $15.20 | $30.00 | $72.68 |
| `claude-sonnet-5-5` | $5.70 | $7.60 | $15.00 | $36.34 |
| `claude-haiku-5-5` | $0.38 | $0.38 | $0.75 | $1.82 |

Expected tokens for Opus: 2.67 M input (2.01 M of them cache reads, if the prompt caches) and 0.99 M output. The system prompt is 1,221 tokens, which may be under a model's minimum cacheable length; the "no caching" column is the safer figure. **Plan on about $15 for Opus and expect up to about $30 if its thinking is heavy; the estimated hard ceiling is $72.68** (input is estimated at 3.5 characters per token, not by the model's tokenizer, so it is an estimate too). The default cost ceiling of the command is 1.5 x the no-caching figure ($22.80 for Opus), so a run that thinks more than assumed stops there with the report of what was reached, not at the hard ceiling. Pass `--cost-ceiling 35` to allow the heavier case.

Scope `all` (every record the researcher decided: 14,150 records, 644 includes, 71 calls): $97.11 expected, $129.93 with no caching, $257.28 heavy, $624.62 hard ceiling (Opus). Not recommended: the frozen sample already holds every include, which is what the gate counts (ladder §4).

Time: Message Batches finish within 24 hours (usually much less); the command polls every 30 seconds and can be left running.

## The command for the real run (not run)
After the researcher approves the spend and stores a key themselves (the agent never reads it):

```bash
uv run nexus-scholar keys set anthropic
uv run nexus-scholar prompt-gate measure --workspace workspaces/uav-crop-weed-v03 --yes --cost-ceiling 35
```

Defaults: `--scope frozen`, `--provider anthropic`, `--model claude-opus-5-5`, `--effort low`, `--max-tokens 4096`, report in `.cache/m9a-measure/`. To see the plan again at any time, with no key and no call, add `--dry-run` (or leave out `--yes`). Sonnet and Haiku are the same command with `--model claude-sonnet-5-5` / `claude-haiku-5-5` (about $5.70 and $0.38 expected); a cheaper model is adopted only if it meets the bar (decision 2026-11-05). A 20-record smoke run (`--limit 20 --yes`, a few cents on Haiku) checks the key and the pipe first.

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner (first build; superseded by the pr row, which ran the round-1 tests too) | working tree before `d4bb5ce7` | `pytest tests/kits/agent/test_measure.py tests/kits/agent/test_prompt_gate.py tests/kits/agent/test_driver_contract.py` | 49 passed | seconds |
| dry run | working tree | `uv run nexus-scholar prompt-gate measure --workspace workspaces/uav-crop-weed-v03 --dry-run` (frozen and all; opus, sonnet, haiku) | the table above; 0 network calls; workspace unchanged (`git status` clean) | seconds |
| pr (final executable commit) | `86ee6572` | `select_test_gate.py --changed origin/main --stage pr` (areas `harness-cli`, `agent-mcp`): `git diff --check`, `pytest -q -n auto`, `ruff check scripts/` | `git diff --check` clean; `ruff check scripts/` clean; full pytest: 1 failed under load, `tests/authority/test_ag04_interaction.py::test_low_il_worker_process_windows` (a Windows integrity-level test in a file this branch does not touch; passes alone, 32 of 32 in its file); the passed total was cut off by the log tail and is not recorded | 20 min 28 s |
| baseline, ruff | `86ee6572` | `generate_contract_baseline.py --check`; `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9` | current; clean | seconds |
| review | `d4bb5ce7`, then `86ee6572` | `milestone-reviewer` (Sonnet) | round 1 on `d4bb5ce7`: CHANGES (no P1; P2: gates passed on an all-failed run, D11 ticked early, lane unexplained; P3 x7); all fixed or recorded in `86ee6572`. Round 2 on `86ee6572`: **APPROVE** (all round-1 findings verified fixed; five P3 notes: two evidence rows made precise here, three small items in Deferred) | |

## Deferred
- The measurement run (D9) and the threshold decision (D10).
- Review round 2 (P3, not fixed, no code change after the PR gate): a run with some failed calls shows the headline `passes` without a warning when it differs from `passes_if_failed_calls_were_misses` (the two columns are side by side); the dry-run text says "hard ceiling" where the record says "estimated hard ceiling".
- `measure` runs only priced models (a ceiling is always set); an unpriced local or OpenAI-compatible endpoint is out of scope here.
- `--limit` takes the first N by study id, not a random sample (the report says SMOKE RUN).
- The score fix to `prompt_gate.score` is reached only by `calibration_result` and direct callers; `measure` maps a researcher Unclear to an include itself.
- The report does not say how many records the researcher must screen blind before a calibration passes at their own include rate (ladder §4, M9c); the per-batch table is descriptive, a batch holds about two includes.
- `prompt-gate run` still sends one Message Batch of up to 10,000 records (the product sends 200); left as it is, `measure` is the command to use.
- A cassette-style replay of a real run (so a recorded real run can be re-scored offline) is not built: `prompt-gate import` already scores recorded answers.
