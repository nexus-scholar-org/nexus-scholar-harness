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

## Conformance

`tests/conformance/test_capability_adapter.py` drives the enforced surface
against synthetic workspaces and covers the Phase-E acceptance criteria and
negative cases (spec 05 §5).

For launcher wiring, see `docs/architecture/DEVELOPER_COMPASS.md` for the
gate policy (`RELEASE` lane) that must pass before this lands in a PR.
