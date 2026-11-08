# M6-hardening: the quiet hardening pass
Branch: `dev/m6h/hardening` · Lane: **STANDARD** (no contract, publication-semantics or UI change; `test_gate_policy.md` §lanes) · Status: IN PROGRESS · Started: 2026-11-08

Why: this is step 9 of the researcher's beta plan of 2026-11-07, "a hardening pass while testers work, small and quiet". No UI change, so testers never see a moving target. The items are the T-P2 findings that the [full review](../../assessment/full-review-2026-11-06.md) deferred from M6-beta. On 2026-11-08 the researcher added H6: the RIS reader fix, which a tester would hit with any export not from IEEE. This branch also carries the two M6-beta closing commits (the timed walk and the tester round, both waived). The researcher chose to fold them in here instead of opening a separate PR.

## Definition of done
- [ ] **H1. Atomic writes.** Screening settings, the operator context, and the batch review and approval files are each written to a temporary file, then `os.replace`d into place. A crash before the replace leaves the previous file readable and no temporary file behind. The bytes on disk are identical to before (same newline translation), so digests do not move. Tests: `tests/unit/test_atomic_write.py`, `tests/console/test_hardening_writes.py`.
- [ ] **H2. `os.replace` is retried on Windows.** A `PermissionError` caused by a transient hold (an antivirus scan, an indexer, or a reader) is retried with a short backoff. It is raised after the last attempt, and immediately on other systems. Sites: the new helper, `generations._rename_tmp`, `pipelines._write_spec`, `screening._atomic_write_json` and `mcp_setup`. Test: `tests/unit/test_atomic_write.py` (a simulated lock).
- [ ] **H3. `/healthz` reveals no path.** Before authentication it answers `{"status": "ok"}` only. Test: `tests/console/test_console_serve.py::test_healthz_reveals_no_workspace_path`.
- [ ] **H4. Dead code removed.** The six `/ui/*` console routes with no caller go (`console/api/screening.py`, `console/api/workspace.py`), along with the unused exports of `apps/research-ui/lib/screening-api.ts`. `tsc`, vitest and the Python suites still pass, and no remaining route or test refers to them.
- [ ] **H5. Machine-local `.claude/` files are ignored:** `.claude/launch.json`, `.claude/settings.local.json` and `.claude/worktrees/`. The tracked agents and skills are left alone (the researcher chose this, 2026-11-08). Check: `git status --short` no longer lists `.claude/launch.json`, and `select_test_gate.py --changed main --stage inner` stops falling back to the full suite because of it.
- [x] **H6. The RIS reader handles more exporters.** Done 2026-11-08 in `scholar_search/importers.py`. It reads authors from `A1` as well as `AU`; `A2`–`A4` are editors and series authors, so they are not read as authors. Wrapped values, meaning lines without a tag, are joined to the value they continue with one space, so long titles and abstracts arrive whole. It accepts tags with an empty value and `ER  -` with or without a trailing space. A record that has authors but no other tag is no longer dropped. Tests in `tests/kits/search/test_importers_exporters.py`: `test_ris_importer_reads_a1_authors_and_wrapped_values` (WoS style), `test_ris_importer_reads_lens_style_records`, `test_ris_importer_keeps_au_and_a1_together_in_order`, `test_ris_importer_reads_a_crlf_export`. All four failed first: no authors, title cut at the wrap, `['First']`, and `0 == 2`.
- [ ] **Gate:** `/gate checkpoint` per item, `/gate pr` once on the final executable commit, `generate_contract_baseline.py --check`, `git diff --check`.
- [ ] **Review:** the milestone-reviewer returns APPROVE.

## Findings fixed
| ID | Reproducing test | Fails before | Passes after |
| :-- | :-- | :-- | :-- |

## Decisions
None needed. H2 retries only `PermissionError`, and only on Windows. H6 changes what the importer reads, not the corpus schema.

## Evidence
| Stage | Commit | Command | Result | Duration |
| :-- | :-- | :-- | :-- | :-- |

## Deferred
- The other T-P2 items from M6-beta's Deferred list: argument injection beyond `--`, coverage, and the gate-selection gap for `corpus_accept.py`. None was asked for in plan step 9.
- If H6 lands, release it as `1.1.0b3`. The researcher decides on the tag after the merge.
