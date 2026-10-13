# HCM-02 disposition (evidence, not a packet)

Status: disposition-in-review. This document launches **no refactor** and
implements nothing. It records, with file paths and test evidence, how far
the neutral workspace/audit service (roadmap §3.1/§3.2, packet HCM-02) has
actually been delivered, so HCM-06/UI-07 can gate on facts rather than on
the roadmap's aspirations.

No HCM-02 packet document exists: the track directory holds only the
roadmap, the HCM-05 characterization, and the README
(`docs/architecture/harness-core-modularity/` listing, 2026-10-13), and
the README states "HCM-02/03/06 have no packet documents; the roadmap is
their only definition". That docs absence is recorded here as a
provenance fact; it is **not** the disposition. What follows is the
disposition.

Related: [UI-07 Presentation Spec](../research_ui/UI-07_PRESENTATION_SPEC.md)
(reads must route through the service) and
[UI-07 Action Spec](../research_ui/UI-07_ACTION_SPEC.md) (writes must route
through the service; the job-runner bypass in §3 is its one hard finding).

## 1. Element dispositions

### 1.1 Neutral workspace/audit service — IMPLEMENTED

`src/scholar_harness/workspace/audit.py` is the sole owner of append-only
journal discipline with two transport-neutral entry points (module
docstring :1-28; no FastAPI/Typer/console import — it imports only
`loader`, `manifest`, `errors`, stdlib):

- `append_event` (:144): canonical writer — server-minted
  `EVT-<ts>-<uuid6>`, uppercased action/status, `ensure_ascii=False`
  journal line, atomic `project.json` projection (pre-existing stats keys
  only), best-effort INDEX refresh. `OSError` propagates (acceptance maps
  to `ATOMIC_COMMIT_FAILED`); projection/INDEX failures swallowed. Alias
  `log_event = append_event` (:221) preserves existing monkeypatch seams.
- `append_legacy_event` (:229): orchestrator/handoff byte-compatible
  writer — preserves the observed `hex(hash(action + description))[-6:]`
  event-id scheme, no uppercasing, default `json.dumps` encoding, no
  manifest/INDEX update. HCM-01's odd scheme preserved and
  regression-tested, not normalized.
- `resolve_workspace` (:51): strict `audit_log` slug/path policy (plain
  dirs refused, no ledger created).
- `refresh_index` (:78, best-effort void) / `refresh_index_atomic`
  (:102, orchestrator-compatible backup/restore bool) share the portable
  loader with injectable seams.

Facade `workspace/__init__.py` re-exports only (no logic). Errors live in
`workspace/errors.py` (`NotWorkspaceError`,
`RegisteredWorkspaceIdentityMissingError`) and are imported by
orchestrator, genesis, audit_log, and CLI rather than redefined per
caller.

### 1.2 Caller migration — IMPLEMENTED with one genuine bypass (§3)

Direct importers of the neutral service (14 modules; `rg "workspace\.(audit|identity|loader|manifest|errors)" src/`, 2026-10-13 — matching dotted import paths; the two `from ... import loader` lines are verified by direct read):

| Module | Imports | Verdict |
|---|---|---|
| `console/api/audit.py` | `workspace.loader` (:49), `workspace.audit.append_event` (:92) | compliant thin adapter (see §2) |
| `contracts/acceptance.py` | `workspace.audit.log_event` (:16); calls at :203, :574 | compliant caller |
| `screening/collector.py` | `workspace.audit.log_event` (:24); calls at :207, :1046, :1191, :1220 | compliant caller |
| `extraction_producer.py` | `workspace.audit.log_event` (:102); call at :1484 | compliant caller |
| `index_acceptance.py` | `workspace.audit.log_event` (:97); call at :895 | compliant caller |
| `pipeline/coordinator.py` | `workspace.audit.append_legacy_event` (:87) | compliant legacy adapter |
| `pipeline/hydration.py` | `workspace.audit.append_legacy_event` (:30) | compliant legacy adapter |
| `pipeline/indexing.py` | `workspace.audit.append_legacy_event` (:108) + `workspace.identity.require_recorded_identity` (:109) | compliant caller |
| `pipeline/verification.py` | `workspace.audit.append_legacy_event` (:47) | compliant legacy adapter |
| `orchestrator.py` | `workspace.identity` (:29, :582), `workspace.audit.append_legacy_event` (:672, via `_log_audit_event` :655) | compliant adapters (legacy scheme preserved deliberately) |
| `handoff.py` | `workspace.audit.append_legacy_event` (:340, via `_log_audit_event` :324) | compliant adapter |
| `inception/genesis.py` | `workspace.identity` mint/validate/recorded-or-minted (:48-50, used :244) | compliant caller |
| `inception/__init__.py` | `workspace.loader` (:141) | compliant caller |
| `audit_log.py` | `workspace.loader.load_log_module_uncached` (:28), `workspace.audit.resolve_workspace` (:29), `workspace.errors` (:27) | adapter over the neutral loader for resolution; journal writes go through the `log_event.py` script, not the service (see §3) |

Transitive callers (through `console.api.audit.log_event`):
`console/api/screening.py` (:28) and `console/api/pipelines.py` (:48)
— both write via the thin adapter, hence via the service.

### 1.3 Identity policy — IMPLEMENTED

`workspace/identity.py`: `mint_registered_workspace_id` (:43, sole mint
point, CSPRNG `WSP-<32 hex>` validated against the frozen registry),
`validate_registered_workspace_id` (:71),
`require_recorded_identity` (:88, consumers: record-and-reread only,
never mint — byte-compatible with the orchestrator including HCM-01
defect (a), preserved), `recorded_or_minted_workspace_id` (:143,
initialization-only policy, byte-compatible with genesis). Adoption:
genesis mints at inception (:244); orchestrator's
`recorded_workspace_id` delegates (:578-584); `pipeline/indexing.py`
requires recorded identity at three call sites (:275, :355, :510);
`extraction_producer.py` validates (:451). The mirrored second writer
(`workspace-manager/scripts/init_project.py`, standalone, cannot import
the package) is held to the same shape by
`tests/inception/test_registered_workspace_id.py`.

### 1.4 Manifest policy — PARTIAL

`workspace/manifest.py`: `update_manifest_for_event` (:35) owns the
append-event projection (bump `updated_at`, overwrite only pre-existing
`stats` keys, atomic tmp+`os.replace`, all failures best-effort while
journal `OSError` propagates). It is called only from
`workspace/audit.append_event` (:199) — no other module imports
`workspace.manifest`. `orchestrator.sync_state` keeps its own merge
including HCM-01 defects (b)/(c), preserved and documented in the module
docstring (:13-15), not repaired here. So: the audit-path projection is
centralized; the sync-state merge is a deliberate, documented remainder.

### 1.5 Loader policy — IMPLEMENTED

`workspace/loader.py`: `resolve_skills_root` (:51, `NEXUS_SKILLS_SRC` →
wheel bundle → repo checkout, CWD-independent), `bundled_skills_root`
(:38), `load_log_module_uncached` (:81), `load_index_refresher_uncached`
(:117). Adoption: `console/api/audit.py` resolves its INDEX refresher
through it (:49, keeping its module-level cache only as a
fault-injection seam); `audit_log.py` resolves the log module through it
(:55); `inception/__init__.py` likewise (:141); genesis keeps its own
cache variables but delegates resolution (module comment :37, :210-213).
Precedence cannot drift; caching seams are caller-owned for test
compatiblity.

## 2. `console/api/audit.py`: thin adapter (compliant), not a bypass

Justification from its `log_event` body (:73-108): it calls the neutral
`workspace.audit.append_event` with `refresh_index=False`, then performs
the INDEX refresh through its local `refresh_index_md` (which itself
resolves through the neutral loader). The journal append, event-id
minting, uppercasing, encoding, and manifest projection are all the
service's; the adapter retains only the pre-existing
best-effort/refresher-failure seam (`_INDEX_MD_REFRESH` cache kept so
`monkeypatch.setattr(console_audit, "_load_index_refresher", …)` still
works). This is exactly what roadmap §3.1 prescribes ("CLI, inception,
console … become thin adapters"). The `POST /api/v1/audit/events`
endpoint (:122) therefore writes through the service. **Verdict:
compliant.**

## 3. Direct journal writers: each grep hit resolved (write vs read)

`rg "journal.jsonl" src/` plus write-site inspection, 2026-10-13:

- **Canonical writer (not a bypass):** `workspace/audit.py:178`
  (`append_event`) and `:253` (`append_legacy_event`). The service
  itself.
- **Compliant adapters (not bypasses):** `orchestrator.py:655-683` and
  `handoff.py:324-351` — both named `_log_audit_event`, both delegate to
  `append_legacy_event`, both document the preserved scheme. No direct
  file write remains in either.
- **GENUINE BYPASS — `console/runtimes/job_runner.py:409-440**
  (`_journal_event`). Opens `audit/journal.jsonl` in append mode and
  hand-rolls the canonical shape (`EVT-<ts>-<uuid6>`, uppercased action,
  `ensure_ascii=False`) instead of calling `workspace.audit.append_event`.
  Same shape today by coincidence, not by construction: a future service
  change (projection, encoding, id scheme) will silently diverge the two,
  and job-completion events skip the `project.json` projection and INDEX
  refresh the service guarantees. It also swallows all journal failures
  (`except Exception: return <synthetic id>`, :440) where the service
  propagates `OSError` for `ATOMIC_COMMIT_FAILED` mapping. **This is the
  smallest genuinely-absent HCM-02 item (§5).**
- **Parallel path (decision required, not a silent bypass):**
  `audit_log.py:142-174` (`run_log_event`) and `:224-270`
  (`run_log_batch`), reached by `cli.py` `log event/batch` (:201-265),
  write through the workspace-manager `log_event.py` **script** loaded via
  the neutral loader — byte-compatible with the service by shared
  contract, but not through it. Consolidation (route the CLI through
  `workspace.audit`) vs. recorded acceptance (script stays the CLI/standalone
  surface, service stays the in-process surface) needs an explicit
  follow-up decision; either way it must be written down, not drift.
- **Reads / path construction (not writes):** `console/api/workspace.py:262`
  (`audit_events` reads the journal); `authority/generations.py:1109`
  (`_prior_generation_recorded` reads for evidence); `orchestrator.py:313-321`
  (`get_status` reads latest events); `doctor.py:279,354-355` (layout
  validation reads); `console/runtimes/actions.py:112` (command template
  interpolates the journal path for a subprocess); `cli.py:234`
  (docstring); `audit_log.py:190` (batch *input* file read);
  `job_runner.py:170-317` (job stdout chunks — unrelated variable name).
  None of these append to the journal.

## 4. Test evidence

- `tests/unit/test_workspace_audit_service.py` — HCM-02 migration tests
  (HCM2-01…HCM2-10 + negative cases; header states zero behavior change,
  `tmp_path` fixtures, HCM-01 defects (a)-(c) preserved). Covers both
  append paths, console-adapter delegation, identity, loader, errors.
- `tests/unit/test_workspace_audit_characterization.py` — HCM-01
  characterization (17 tests; observed behavior + unproven limits +
  defects recorded-not-fixed, per HCM README).
- `tests/inception/test_registered_workspace_id.py` — holds both
  `project.json` writers (service + standalone script) to the same mint
  shape.
- `tests/unit/test_audit_log.py` — CLI/script audit surface.
- Negative coverage required by the roadmap (invalid workspace id, stale
  parent, failed audit publication cannot silently create state) lives in
  the service tests and the AG-02/AG-03 refusal suites; no new negative
  test is claimed by this disposition.

## 5. Conclusion

**No blocker for HCM-06/UI-07 reads; one bounded write-path remainder.**

The HCM-02 service and its callers are delivered: neutral audit service
plus strict resolution (§1.1), 14 direct-importing modules plus 2
transitive console writers all routed through it (§1.2), identity policy
with adoption (§1.3), loader policy with adoption (§1.5), and the console
audit module verified as a thin adapter (§2). Full HCM-02 "closure" is
**not** claimed: the packet never existed as a gated document, and the
remainders below are explicit.

Remaining work (each a separate, small scope — none launched here):

1. **Migrate `job_runner._journal_event` to `workspace.audit.append_event`**
   (or a documented legacy variant) — the smallest genuinely-absent
   item. Scope: replace the hand-rolled append with the service call,
   decide INDEX-refresh/projection behavior for job events, preserve the
   never-crash-jobs guarantee explicitly (return-value vs raise
   contract), add a regression test pinning byte-compatibility. **Gates
   UI-07 actions**: job completion is a mutation surface the action API
   must account for.
2. **Decide the `audit_log.py`/CLI script path** (consolidate through the
   service vs. record the script as the accepted standalone surface).
   Read-only UI-07 presentation does not depend on it.
3. **`orchestrator.sync_state` manifest merge** stays separate with
   defects (b)/(c) preserved — needs its own behavior-decision packet if
   ever unified; not an HCM-02 regression.
4. **HCM-03 pipeline-core extraction** is a different packet (roadmap
   §3.3); `console/api/pipelines.py` already delegates models/validation
   to `scholar_harness.pipeline` (HCM-03 partially in flight) — not
   counted for or against HCM-02 here.

## 6. Open questions

- **OQ-H1 — job_runner failure contract.** The service propagates
  `OSError`; the runner currently never raises from journaling. Which
  contract the migrated call uses (propagate-and-handle at the call site
  vs. a best-effort wrapper inside the service) is for the migration
  scope to decide, not this disposition.
- **OQ-H2 — characterization test count.** The HCM README cites "17 new
  characterization tests"; the count was not re-run for this prose-only
  disposition (F1 lane: no suite run solely for prose). A future
  implementation scope should quote a live run.
