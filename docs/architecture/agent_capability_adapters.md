# Agent Capability Adapters (agent-layer Phase E)

Normative spec: `specs/agent-layer-portability/04_capability_adapter_and_app_surface.md`.
Packet: `specs/agent-layer-portability/05_migration_plan.md` §5.

The adapter layer turns independence and provenance into **filesystem facts**
instead of prompt sentences. One interface, two implementations, and the split
is explicitly honest about which surface enforces what.

## The two surfaces

| Adapter | Surface | Enforcement | Module |
|---|---|---|---|
| `OpencodeAdapter` | this repo's dev loop | **Best-effort** — tri-state permissions plus adapter-side path checks before and after | `src/scholar_harness/capabilities/opencode.py` |
| `InProcessAdapter` | the application | **Enforced** — materialised run view, path validation at every I/O, egress control, adapter-written audit | `src/scholar_harness/capabilities/inprocess.py` |

A single implementation that claims both is how "read-only" ends up being a
sentence in a markdown file. The dev loop is not a sandbox; the application is.

## Guarantees in app mode

Driven by the role record (`roles/<id>.json`, Phase A):

- **Write boundary** — every role output is staged into
  `runs/{task_id}/out/`, validated against `write_glob` minus `deny_glob`,
  then promoted atomically. Writes elsewhere fail with `SCOPE_VIOLATION`
  **and leave no file**.
- **Read boundary** — the run view contains only `read_glob` matches.
  `deny_glob` is a *write* denylist and never subtracts from the read view
  (spec 01 R4).
- **Blinding** — `isolation: directory` gives each arm its own view; 
  `redacted-input` strips identifying fields (default: `title`,
  `authors`, `abstract`; per-role override via
  `independence.redacted_fields`) when the view is materialised. A blinded
  arm's view never contains a `blinded_from` role's outputs — the sibling's
  `write_glob` rows (Phase A records) are excluded before materialisation.
- **Network** — `network: deny` wraps the run in a socket guard: the connect
  attempt raises immediately (`EgressRefused`); it is never a
  timeout-and-retry.
- **Audit attribution** — the adapter (never the role) appends
  `audit/journal.jsonl` rows stamped with the role record's `audit.actor`
  template (`{role}@{version}`), `role_version`, envelope id, and
  sha256 of every input and output.

A role that declares `isolation: none` while an `arm` is set is refused at
the boundary, before any handler runs.

## Dev mode's residual risk (required disclosure)

`OpencodeAdapter` is best-effort. Its module docstring documents the four
residual gaps (filesystem writes outside the boundary are possible via
`bash`; egress is cooperative; views are advisory; the journal can also be
appended by dev tooling). Any statement that dev mode enforces app-grade
capability is a defect.

## Residual risks and accepted limits (both surfaces)

The adapter split is honest only when every limit is named where a reader looks.
The dev-mode four are above; app mode is *enforced on the session API*, which is
not the same as a sandbox. These are the accepted limits, each defined in code:

| # | Limit | What is actually guaranteed | Defined in |
|---|---|---|---|
| A1 | **Handler code is trusted.** `InProcessAdapter` calls the handler in the host process. `RoleSession` validates every read/list/write it serves, but a handler using `open()`, `subprocess`, `ctypes`, or a C extension bypasses it. | The boundary protects against protocol mistakes and accidental cross-arm reads, not against code that already has host execution. Handlers are part of the trusted computing base. | `capabilities/adapter.py` `RoleSession` |
| A2 | **Egress deny covers the patched Python entry points only.** Aliases captured before the guard, live sockets, child threads / `asyncio` executors (the deny flag is a `ContextVar`), `socketpair` and the private `_socket` module bypass it. | A direct `socket` / `create_connection` / resolver call on the guarded thread raises `EgressRefused` before the syscall; that is the claimed scope, not OS-level network isolation. | `RoleSession.egress_guard` docstring (items 1–5) |
| A3 | **The run view is a materialised copy, not a chroot.** The host workspace still exists at its absolute paths. | Session-mediated reads cannot leave the view; blinding holds for those reads. A handler that reads the real tree directly is outside the guarantee (see A1). | `materialise_view`; `RoleSession.read`/`list` |
| A4 | **Redaction covers `.json` artifacts only.** Under `isolation: redacted-input`, JSON payloads lose the citation fingerprint; any other file type matched by `read_glob` is copied unredacted. | The default redaction set is the full citation fingerprint (`title`, `authors`, `abstract`, `doi`, `url`, `venue`, `journal`, `year`, `publication_date`, `publisher`, `affiliations`), additively extended per role. | `RoleSession.DEFAULT_REDACTED_FIELDS`; `egress_guard` item 5 |
| A5 | **Promotion is per-artifact atomic, not transactional across a run.** Each staged artifact is promoted with a same-directory rename; a process crash between two promotions can leave a prefix published. | No single artifact is ever partially written. A crash prefix is visible to the next consumer (e.g. the integrity gates refuse incomplete coverage); nothing in the adapter claims a transactional multi-artifact publish. | `RoleSession.write`; `roll_back_promoted` |
| A6 | **Late-failure rollback can dangle an earlier journal row (P3-7).** If envelope construction fails after this run overwrote a pre-existing artifact, rollback removes the promoted path rather than restoring the old bytes. | A failed run publishes nothing. An earlier journal row naming the overwritten path can then point at a missing file — fail-closed, documented, and never a silent repair. | `roll_back_promoted` docstring |
| A7 | **A journal append failure after publication is not rolled back (P9).** The envelope is already valid and the output already promoted. | Callers must not treat a raised append as "unpublished": the output is authoritative and the append failure surfaces. The journal is append-only by convention, not tamper-evident against a privileged actor. | `InProcessAdapter.run` docstring; `append_journal` |

None of A1–A7 is a regression to fix by widening a claim. Removing one requires
the enforcement to change (an OS sandbox, a subprocess boundary, a transactional
publisher), not a documentation edit.

## Conformance

`tests/conformance/test_capability_adapter.py` drives the enforced surface
against synthetic workspaces and covers the Phase-E acceptance criteria and
negative cases (spec 05 §5).

For launcher wiring, see `docs/architecture/DEVELOPER_COMPASS.md` for the
gate policy (`RELEASE` lane) that must pass before this lands in a PR.
