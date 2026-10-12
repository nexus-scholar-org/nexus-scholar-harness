# AG-03A: protected publisher authority feasibility

**Selection:** APPROVED by researcher on 2026-10-12 in this chat:
"fix the planning issues and persist your proposition i approve, and if you can init the uav protocol".
**Runtime state:** `BLOCKED_AUTHORITY_ENFORCEMENT`; no deployment isolation proven.
**Owner:** harness plus explicit deployment configuration; **runtime lane:** RELEASE.
**Parent:** [current AG plan](agent_controls_plan.md).

## Chosen authority model

A protected local publisher owns approval, accepted state, audit and final output.
A restricted scientific worker receives read-only assigned evidence and a draft
inbox. It cannot obtain operator credentials, drive the approval UI, alter the
publisher code or policy, write its authoritative files, or bypass the publisher.
The real operator reviews immutable content and performs an explicit approval
bound to workspace, run, batch, parents, recommendation revision, final decision
hash and policy version. Unrestricted development sessions are not this worker.

## Bounded first proof

1. Record the intended host, process identities, filesystem permissions, session
   access, network/tool routes and trust configuration. Select an actual isolation
   mechanism, initially investigate separate OS identities. Do not create accounts
   or alter host permissions as part of this documentation task.
2. Use one synthetic batch and a disposable publisher store. Demonstrate denied
   worker writes to approval/policy/code/registry/audit/final outputs. Include
   path traversal, symlink/junction and inherited-credential routes where applicable.
3. Prove an explicit operator action can approve the exact displayed snapshot.
   Worker-forged reviewer strings, HUMAN labels, local HTTP requests, copied
   session credentials, replayed requests and UI automation must not grant access
   in the supported deployment. State any unsupported threat assumptions.
4. Reject missing/expired/revoked authority and wrong-workspace/batch/content or
   policy approvals. Revalidate at promotion; preserve the request and refusal.
5. Demonstrate operator override creates a new review revision; it never rewrites
   the original suggestion or clears the registry to bypass CONTENT_CHANGED.
6. Independently review evidence and pass a bounded test packet before declaring
   this host supported. A test using only mock identity is insufficient.

AG-03A may build only the narrow feasibility adapter needed for this proof.
Production lifecycle and all-consumer publication adoption are AG-03B/C. Passing
this proof alone does not mean every production path is protected.

## Boundaries and fallback

No guarantee against administrator compromise. No claim of scientific truth,
human attention, or critic independence follows from authentication. A shared
unrestricted OS identity is unsupported for enforced approval. If isolation is
infeasible, report the failed assumption; use operator-attended procedural review
without an authorization claim, or bring an external publisher/signing service
as a separately reviewed alternative. Protect verifier and trust configuration;
a signature on a file alone is not enough. Do not silently change the approved
model or build a bespoke PKI.

No toolkit changes, generic scheduler, provider selection, research data migration,
or broad UI work are presumed. If the proof needs public/persisted semantic or kit
changes, declare those boundaries before implementation and use their release gates.

---

## Result (2026-10-12)

**Verdict: FEASIBILITY_PROVEN for the tested deployment; POSIX unproven.**

**Supported deployment.** Windows Mandatory Integrity Control: the publisher
store (approval records, policy, executable code, registry, audit, final
outputs) runs at Medium integrity; the restricted scientific worker runs in a
Low-integrity process (`S-1-16-4096`). The kernel's default no-write-up policy
denies the worker every write to publisher state while a Low-labelled inbox
stays writable. Established without administrator rights and without a
container runtime. POSIX requires a separately provisioned two-identity
arrangement that this proof does not implement — NOT proven on POSIX.

**Owner paths.** Adapter: `src/scholar_harness/authority/` (`binding.py` —
approval binding/verification/promotion; `isolation.py` — MIC provisioning,
Low-IL spawn, honest `capability_report`). Proof: `tests/authority/`
(`test_approval_binding.py` 37, `test_disposable_flow.py` 12,
`test_isolation_windows.py` 15). Harness-only; no toolkit, pin, contract, or
workspace change.

**Demonstrated path.** Accepted synthetic batch + immutable parents → AG-02
coverage/unresolved gates → restricted worker submits a recommendation →
publisher captures the immutable snapshot → operator reviews the exact bytes →
protected operator action mints a narrowly scoped approval → publisher
re-verifies approval against snapshot + parents at promotion → disposable final
output promoted with attributable audit evidence.

**Evidence.** `tests/authority/`: 64 passed, 0 failed, 0 skipped (isolation
tests executed on Windows, not skipped). Full harness suite: 1243 passed,
6 pre-existing platform skips, 0 failed. Independent reviewer APPROVE (one
repair round, 10 findings closed); independent tester PASS. Baseline, schemas,
fixture, pins `--check` all exit 0; `git diff --check` clean.

**Remaining limitations (for AG-03B/C).** Read-up is permitted (MIC denies
writes, not reads — secrets must never live in worker-reachable publisher
files). No guarantee against administrator compromise. No concurrency or
atomicity claims. Same-bytes-for-parse/hash/display is caller discipline until
AG-03B's single immutable buffer. Durable refusal audit and publication
generations belong to AG-03B/C. This verdict applies only to the tested
deployment and disposable flow; it closes neither AG-03B nor AG-03C and
establishes no scientific correctness, human attention, critic independence,
or deployment-wide security.
