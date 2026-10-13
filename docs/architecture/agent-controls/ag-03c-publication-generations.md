# AG-03C: shared authorization enforcement and coherent publication generations

**Status:** OPEN — implementation packet. **Lane:** RELEASE.
**Supported deployment:** Windows MIC protected publisher (AG-03A proven); POSIX unproven.
**Parent:** [AG architecture decision](agent_controls_decision.md) (invariants D1–D9);
extends AG-03A (`binding.py`, `isolation.py`) and AG-03B (`lifecycle.py`).

## 1. Supported deployment and threat boundary

Same as AG-03A: publisher store at Medium integrity, restricted worker at Low
integrity (`S-1-16-4096`), kernel no-write-up denies worker writes to publisher
state; Low-labelled inbox stays writable. No admin rights, no container.
`OperatorIdentity` is publisher-constructed (`source="publisher-operator-context"` only).

**In scope as attackers:** a worker process that ignores prompts, forges
human-looking fields (`actor`/`method: HUMAN`/confidence/critic PASS), calls
harness APIs directly, replays approvals across scope, swaps content
post-review, writes via traversal/junction/inherited-handle routes, races a
second writer, kills the publisher mid-publication, or breaks the audit sink.
**Excluded (stated, not silently dropped):** administrator compromise; read-up
(secrets must never live in worker-reachable publisher files); POSIX hosts;
multi-host deployments; concurrency beyond two competing writers on one host.

## 2. Producer / publication / consumer paths in scope

| Role | Exact path | Change |
|---|---|---|
| Producer | `src/scholar_harness/screening/collector.py` `cmd_collect` (decision files `literature/screening/batch_NNN_decisions.json` → partition) | Insert the shared authorization gate between partition and ANY final write; publish a generation record; tmp+rename discipline; commit point = generation manifest rename |
| Publication outputs | `literature/included.json`, `excluded.json`, `conflicts.json`, `prisma_screening_report.md`, `prisma_report.json` + NEW `literature/screening/generation.json` | All five content files staged to tmp then renamed; `generation.json` renamed LAST |
| Consumer (production) | `src/scholar_harness/extraction_producer.py::_included_records` | Refuse stale/mismatched/superseded/legacy generations with typed codes |
| Consumer (pipeline gate) | `src/scholar_harness/pipeline/coordinator.py` stages 5–9 gate | Missing/stale generation → stages stay SKIPPED/PENDING with explicit reason (not silent pass) |
| Consumer (phase trigger) | `src/scholar_harness/handoff.py` SCREENING trigger | Trigger requires a current generation, not mere file existence |
| Display-only (explicit disposition, NOT gated) | `src/scholar_harness/orchestrator.py` stats reads; console/API readers | May read for counts/display; MUST NOT be treated or described as authorization decisions. Logged as display-only in code comments |

**Legacy disposition:** an `included.json` WITHOUT a sibling current
`generation.json` is `LEGACY_UNVERIFIED`: consumers refuse to treat it as
authorized-current and report the status explicitly; no silent consumption, no
retroactive approval fabrication, no automatic migration.

**Migration exception (2026-10-13, bounded):** workspaces with NO authorized
material ever — no staged `publication_approval.json`, no registry
`screening_decisions` lineage (`decision_file_sha256`), no MANIFEST accepted
lineage rows, no generation history — are true-legacy. During migration,
consumers REPORT `LEGACY_UNVERIFIED` explicitly (typed code in the
refusal/report path — a `logger.warning` carrying
`GENERATION_LEGACY_UNVERIFIED` at each proceeding call site — never silent)
and may proceed for read/display/golden-fixture compatibility. The moment ANY
authorized material exists, strict refusal applies: an absent
`generation.json` beside such evidence is a downgrade/tamper deletion and
reports `MISMATCHED` (the `require_current_generation` downgrade check).
Old-format fixtures (E4 golden: MANIFEST rows and registry envelopes without
the lineage keys, no staged approval) match none of the downgrade signals and
stay true-legacy. Removal of this exception is conditioned on fixture
migration (E4 golden + pre-authorization suites moving to staged-approval
collects); until then the exception is dated and scoped, not a standing
bypass. Fixture-compat workspaces (true-legacy, explicitly reported) may
proceed through full downstream publication during the window; this is a
dated, bounded, explicitly-logged compatibility shim, not an authorization.

## 3. Generation and currentness semantics

`literature/screening/generation.json` (`harness-screening-generation-v1`):

```json
{
  "schema": "harness-screening-generation-v1",
  "generation_id": "GEN-< workspace-short>-<run>-<batch-set-hash8>",
  "workspace_id": "WSP-…", "run_id": "…",
  "batch_bindings": [{"batch_index": 0, "batch_artifact_id": "…", "batch_sha256": "sha256:…"}],
  "protocol_fingerprint": "sha256:…", "corpus_fingerprint": "sha256:…",
  "snapshot_fingerprint": "…", "approval_fingerprint": "…",
  "operator_identity": "…", "policy_version": "…",
  "outputs": {"included.json": "sha256:…", "excluded.json": "sha256:…",
              "conflicts.json": "sha256:…", "prisma_screening_report.md": "sha256:…",
              "prisma_report.json": "sha256:…"},
  "supersedes": null,
  "published_at": "…"
}
```

**Currentness rule** (`require_current_generation(workspace)`): a generation is
CURRENT iff (a) `generation.json` parses and carries the expected schema, (b)
every listed output file exists and hashes to the recorded digest, (c) the
approval fingerprint resolves to a non-revoked, non-expired, scope-matching
approval for the recorded binding, (d) no newer generation supersedes it.
Otherwise the status is STALE (content/parent changed), SUPERSEDED (a newer
generation exists), MISMATCHED (cross-workspace/run/batch replay), or
LEGACY_UNVERIFIED (no generation record). Consumers refuse all four with typed
codes; the coordinator reports them explicitly.

**Supersession:** a new authorized collect writes generation N+1 with
`supersedes: <fingerprint-N>`; generation N's files are retained as historical
evidence but are no longer CURRENT. Retrying an identical collect is idempotent
(byte-identical outputs + same approval → same generation id, no rewrite).

## 4. Acceptance / refusal matrix

| Situation | Gate outcome | Consumer outcome |
|---|---|---|
| Valid approval + exact snapshot + accepted parents | PUBLISH generation N | CURRENT — consume |
| Missing approval | `APPROVAL_MISSING`, no output | n/a (nothing published) |
| Forged actor/method/confidence/critic (no approval) | `APPROVAL_MISSING` | — |
| Changed recommendation/final bytes | `APPROVAL_CONTENT_CHANGED`, no output | STALE — refuse |
| Changed protocol/corpus parents | scope/parent refusal, no output | STALE — refuse |
| Cross-workspace/run/batch replay | `APPROVAL_SCOPE_MISMATCH`, no output | MISMATCHED — refuse |
| Superseded generation presented | — (superseded at publish) | SUPERSEDED — refuse, point at current |
| No `generation.json` beside outputs, no authorized material ever (true-legacy) | — | LEGACY_UNVERIFIED — REPORT explicitly (typed code), may proceed for read/display/fixture compatibility (migration exception 2026-10-13, bounded) |
| No `generation.json` beside surviving authorized material (staged approval, registry/MANIFEST lineage) | — | MISMATCHED — refuse, never legacy (unapproved review lineage when no prior generation is recorded — details carry `lineage_without_generation: True` — or post-authorization deletion when one is — `prior_generation_deleted: True`) |
| Mixed-generation assembly (outputs from N and N+1) | — | MISMATCHED — refuse |
| Audit-sink failure at publish | `PROMOTION_AUDIT_FAILED`, outputs removed | — |
| Crash between renames | recovery: no `generation.json` → not CURRENT | refuse until re-collect |

## 5. Crash, race, retry, audit-failure expectations

- **Commit point:** the rename of `generation.json` into place is the single
  authoritative commit point. Content files are renamed before it; nothing is
  CURRENT until it lands. Do NOT claim filesystem atomicity/durability beyond
  what tmp+rename on one host provides — document the limit.
- **Crash recovery:** on collect start, a previous run's tmp files (`*.tmp`,
  `generation.json.tmp`) are removed; outputs without a matching generation are
  never treated as current. Recovery behavior is tested by fault injection at
  each material boundary (before content renames / between content and
  generation rename / after generation rename).
- **Races:** two concurrent collects for the same batch set serialize on a
  lock file (`literature/screening/.collect.lock`, best-effort exclusive
  create); the loser re-reads and either joins the identical generation
  (idempotent) or refuses on scope mismatch. Concurrent attempts MUST NOT
  produce a silently mixed current generation — tested with two competing
  writers.
- **Retries:** identical retry → same generation id, no rewrite (idempotent).
  Changed retry → new review + new approval required.
- **Audit failure:** any audit-sink failure during publish removes staged
  outputs (including `.tmp`) and returns failure; required refusal-audit
  failures surface, never masquerade as success.

## 6. Mandatory tests and completion criteria

New `tests/authority/test_publication_generations.py` (hermetic, synthetic
`tmp_path`; Windows-MIC enforcement tests reuse the existing isolation file —
no new OS tests required unless the gate adds a new enforcement surface):

1. gate-before-write: collect without approval writes NO partition file;
2. coherent generation: publish → `generation.json` matches all five output hashes + approval/snapshot fingerprints;
3. consumer-current: extraction-producer path consumes a CURRENT generation;
4. stale/mismatched/superseded/legacy: each refuses with its typed code;
5. mixed-generation assembly refuses;
6. crash injection at each of the 3 material boundaries → recovery state defined, nothing falsely CURRENT;
7. competing writers → one generation wins, no mixed CURRENT;
8. idempotent retry (no rewrite) vs changed retry (new approval required);
9. audit-sink failure → no consumable output;
10. AG-02 gates still enforced through the gated path (coverage/duplicate/unresolved/parent refusals unchanged).

**Completion:** all of the above green + full suite + closure checks + independent
review APPROVE + tester PASS. Bounded to the tested Windows deployment and the
four consumer paths in §2; AG-04+ untouched; no toolkit/pin/contract change.
