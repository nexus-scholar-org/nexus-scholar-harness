# H-key-precedence-2026-11-20 The provider key in use is predictable and visible
Branch: dev/fix/key-precedence · Lane: **RELEASE** · Status: READY FOR REVIEW (not pushed) · Started: 2026-11-20

Base: `origin/main` at `88e3d6fb`. No AI call, no paid API call, no real key and no real keychain in any test or command run for this change. Out of scope by agreement with the concurrent sessions: harvest provider attribution and the Semantic Scholar search in `src/scholar_search`; none of those files was edited.

**What happened (M9a record, "How the run was started, and what went wrong first").** On 2026-11-19 the paid `prompt-gate measure` failed three times with "401 invalid x-api-key" although a valid key was in `ANTHROPIC_API_KEY`: `scholar_agent.keys.resolve_key` returned the OS-keychain entry first, and the keychain held an old, refused key. `keys status` printed only "anthropic: keychain". Without the `ai` extra the same command died with `ModuleNotFoundError: anthropic`.

**Lane.** RELEASE, by the escalation rule in `docs/architecture/test_gate_policy.md` ("public API/CLI/MCP semantics"): which key a command uses is CLI behaviour (and the app's run and the setup screen use the same function), and `keys status` output changes. No Contract v1 model, schema, fixture or artifact identity changes. Evidence is the `pr` stage on the final executable commit, the contract baseline check, the wheel-help smoke, and an independent review; the cross-platform CI matrix (the `closure` row's Node build and `uv build --wheel` with the UI) is not run locally, see "Not verified".

## Definition of done
- [x] **1. Precedence.** A set, non-blank provider variable wins over the keychain; the keychain is the default when none is set. Earlier decisions checked: none chose keychain-first (decision 2026-11-04, CORE-17 says "variables already set in the environment win" for the MCP server, which already behaved so); the module docstring and one test title said keychain-first and are corrected.
- [x] **2. Visibility.** `keys status` names the source in use and the variable, and says when the other source also holds a key and is not used, with how to use or remove it; it says when the keychain library is missing. When a provider answers 401, `prompt-gate run` and `measure` say which source the refused key came from and how to replace or clear it. No key value or fragment is printed (tests check the first 8 characters too).
- [x] **3. Missing `ai` extra.** `prompt-gate run` and `measure` (not `--dry-run`, not `estimate`) say in one sentence what to install, before any estimate, cost or "--yes" line, with no traceback; `make_driver` gives the same sentence.
- [x] **4. Docs.** User guide §8 "Provider keys: which one is used", the variable table row, two troubleshooting rows; `keys` help text and the `keys status` docstring.
- [x] **5. Gates.** See Evidence.

## Findings fixed
| Item | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |
| Precedence | `tests/kits/agent/test_key_precedence.py::test_an_environment_variable_wins_over_the_keychain`, `::test_every_provider_follows_the_same_order` (3 providers), `::test_the_keychain_stays_the_default_when_no_variable_is_set`; `tests/kits/agent/test_keys.py::test_the_environment_wins_over_the_keychain_which_is_the_default` (was `test_keychain_wins_over_the_environment`, which asserted the old order) | `resolve_key` returned the keychain key | the variable is returned; the keychain only when no variable is set |
| Status | `::test_status_says_which_source_is_used_and_that_the_other_also_exists`, `::test_status_says_so_when_there_is_no_keychain_support` | `keys status` printed "anthropic: keychain" | "anthropic: environment (ANTHROPIC_API_KEY; a keychain key also exists and is not used)" plus the how-to line; neither key nor its first 8 characters in the output |
| Refusal, per-record 401 | `::test_measure_names_the_environment_as_the_source_of_a_refused_key`, `::test_measure_names_the_keychain_as_the_source_of_a_refused_key`, `::test_gate_run_names_the_source_of_a_refused_key` (fake driver whose every result is a 401) | "Not measured … First error: AuthenticationError … 401" and nothing about which key | the sentence names the source and the replacement |
| Refusal, batch raises | `::test_a_batch_that_the_provider_refuses_is_a_sentence_not_a_traceback` (a driver that raises an exception with `status_code` 401); guard: `::test_a_failure_that_is_not_a_refusal_is_not_blamed_on_the_key` (a `RuntimeError` is still raised) | the exception reached the user as a traceback | one sentence, exit 1 |
| Refusal detection | `::test_is_refusal_recognises_a_401_and_nothing_wider` (401 as status or text, `AuthenticationError`; not 429, not "1401 records") | no such function | pass |
| Missing SDK | `::test_ensure_sdk_says_what_to_install`, `::test_make_driver_gives_the_same_sentence_instead_of_a_module_error`, `::test_measure_without_the_sdk_says_so_before_any_spend_is_announced` (with and without `--yes`), `::test_gate_run_without_the_sdk_says_so_before_the_estimate`; guard: `::test_measure_dry_run_needs_no_sdk` | `ModuleNotFoundError: anthropic` from `make_driver` after the estimate was printed | one sentence naming `uv sync --extra ai` and the wheel command, first |

Before the fix the new tests were run against the old code (the file collected with the `ensure_sdk` import made lazy): 17 failed; the two guards (`..not_blamed_on_the_key`, `..dry_run_needs_no_sdk`) passed, as they should. The file as committed fails at collection on the old code (`ImportError: cannot import name 'ensure_sdk'`).

## One thing found on the way
`tests/console/test_agent_runs_api.py::test_setup_names_key_sources_never_keys_and_the_latest_run` set up a fake keychain key but left `ANTHROPIC_API_KEY` to the machine, so it passed only where that variable was unset (keychain-first hid this); it now removes the three variables. Other agent-kit tests could read the real keychain through `key_status`; `tests/kits/agent/conftest.py` now gives every test there a fake `keyring` and no provider variable.

## Decisions
`docs/decisions.md`, "2026-11-20 — Which provider key is used, and saying so": items 1 to 5, all PROPOSED.

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |
| inner | working tree before `8a1528fe` | `pytest` on the new file, `test_keys.py`, `test_measure.py`, `test_prompt_gate.py`, `tests/console/test_agent_runs_api.py`, `tests/mcp/test_mcp_setup.py`, `tests/cli` (`-m "not slow"`) | 175 passed | 1 min |
| pr (final executable commit) | `8a1528fe` | `git diff --check`; `uv run --extra dev --extra pdf --extra rag pytest -q -n auto`; `ruff check scripts/` | `git diff --check` clean; full suite exit 0 (5,734 passed dots, 20 skipped, 1 xfail; the log's summary line was not captured); `ruff check scripts/` clean | about 20 min |
| ruff, real-bug classes | `8a1528fe` | `ruff check src/ --select F821,F811,F823,F632,F7,B023,B006,E9` | clean | seconds |
| baseline, smoke | `8a1528fe` | `generate_contract_baseline.py --check`; `uv run nexus-scholar --help`; `uv run scholar-agent --help` (base environment, no `ai` extra) | baseline current; both answer | seconds |
| lint, gate's agent-kit line | `8a1528fe` | `ruff check src/scholar_agent tests/kits/agent` | still red: 27 pre-existing findings in files this change does not own (unused imports in `test_server.py` and others); the two findings in files this change touched were fixed. Not a CI gate | |

## Deferred / not changed
- The app's run API (`POST /proposals/runs`) still records the provider's per-record error text, and the Run screen does not show where a refused key came from; the sentence is CLI-only. The setup screen's `key` field reads `environment` where it read `keychain` when both exist.
- `OPENAI_API_KEY` for a local OpenAI-compatible endpoint that needs no key is unchanged (`resolve_key` returns None and the run goes on).
- The `.env` loaded by `scholar-agent --env-file` and the keychain keep the MCP server's own rule (`_apply_keychain_keys`), which already put the variable first.
