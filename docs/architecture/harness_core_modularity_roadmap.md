# Harness Core Modularity Roadmap

**Status:** deferred architecture roadmap, not an implementation packet.
**When:** after WP-01 Packet E4 closes and before a broad new workflow phase.
**Purpose:** reduce internal coupling and agent context cost without turning
harness-owned workflow responsibilities into more standalone packages.

## 1. Decision

Nexus Scholar remains a **modular monolith**:

```text
Reusable scientific capability        Trustworthy workflow coordination
------------------------------        --------------------------------
scholar-*-kit packages                nexus-scholar-harness
search / PDF / RAG / graph            contracts / workspace / audit
protocol / verification               screening / inception / recon
                                      pipeline coordination / interfaces
```

Do not flatten existing kits into the harness. Do not extract each harness
folder into a new package. A component belongs in a kit only when it is a
stable, independently useful scientific capability with ordinary typed inputs
and outputs. A component belongs in the harness when it owns workspace
lifecycle, acceptance, audit, identity, or composition across kits.

## 2. Why this is deferred

Packet E3/E4 establishes the evidence and index boundary. Refactoring it now
would mix architecture cleanup with Contract v1 adoption. This roadmap creates
no authority to weaken the frozen contract, change package pins, migrate legacy
workspaces, or alter E3/E4 behavior.

## 3. Target internal boundaries

### 3.1 Workspace policy service

Create a harness-internal `workspace/` service that is the sole owner of:

- `project.json` read, validation, and update policy;
- registered workspace identity minting and preservation;
- canonical workspace layout;
- append-only audit-journal operations.

CLI, inception, console, and bundled workspace-manager scripts become thin
adapters. A pre-registration workspace must refuse explicitly; it must never
receive a freshly minted identity during a re-run or migration by accident.

### 3.2 Neutral audit dependency

Move audit publication out of transport modules. Contract acceptance must not
import FastAPI console code. The intended direction is:

```text
contracts / screening / pipelines / console / CLI  ->  workspace audit service
```

not `contracts -> console.api.audit`. The audit service must preserve existing
append-only and atomic-publication guarantees.

### 3.3 Pipeline core and stage coordinators

Move reusable pipeline specifications, validation, and execution coordination
from presentation-facing console modules into a neutral harness pipeline core.
Then split orchestration by scientific stage:

```text
pipeline/
  discovery.py  verification.py  screening.py  acquisition.py
  extraction.py indexing.py      synthesis.py  coordinator.py
```

Each stage consumes accepted parents, calls kit APIs, returns typed outcomes,
and publishes only through the acceptance boundary. It must not invent IDs or
turn provider failure into empty success.

### 3.4 Recon as inception support

Keep recon harness-owned and conceptually nest it under `inception/`. It may
call `scholar-search-kit`; its cache and grounded-direction gates remain
inception-specific. MCP exposes recon through an explicit adapter rather than
duplicating it in `scholar-agent-kit` or relying on dynamic source discovery.

### 3.5 Interface ownership

Keep the FastAPI console as the local operator surface and the Next UI as the
researcher-facing surface. Both may consume a later, separately reviewed
read-only presentation API. Neither becomes an independent workflow engine;
all mutations go through harness services and audit publication.

## 4. Proposed packet order

| Packet | Outcome | Preconditions |
| --- | --- | --- |
| HCM-01 | Characterize workspace manifest, identity, and audit behavior; publish migration/refusal decision | E4 closed |
| HCM-02 | Introduce neutral workspace/audit service; move callers without behavior change | HCM-01 |
| HCM-03 | Move pipeline models/validation from console transport into pipeline core | HCM-02 |
| HCM-04 | Extract one orchestration stage at a time behind existing tests | HCM-03 |
| HCM-05 | Define MCP recon adapter and remove dynamic harness-source discovery | HCM-02 |
| HCM-06 | Specify shared read-only presentation API for console and Next UI | UI-07 request + HCM-02 |

Each packet is a separate PR. No packet may mix a kit change, a contract version
change, and an internal refactor.

## 5. Required evidence for every packet

- Characterization tests before behavior-moving refactors.
- Existing Contract v1 baseline, schemas, fixture, and pin checks remain green.
- A negative test proving an invalid workspace ID, stale parent, or failed audit
  publication cannot silently create authoritative state.
- No package pin or vendored toolkit drift unless the packet explicitly owns
  canonical-kit merge, full-SHA pin bump, and vendored synchronization.
- A Context Capsule naming only the affected internal boundary and tests, so
  small agents do not reload the full E3 history.

## 6. Explicit non-goals

- No new standalone `screening`, `inception`, `recon`, `audit`, or `contracts`
  package.
- No flattening of `scholar-*-kit` packages into the harness.
- No automatic legacy-workspace identity migration.
- No user-interface workflow writes before API and command boundaries are
  separately specified and reviewed.

## 7. Success criteria

The result is a simpler harness to reason about:

```text
kit capabilities -> harness stage -> acceptance/audit -> operator or researcher UI
```

Agents can change one stage or interface without reading unrelated kit internals,
while the scientific contract remains the single governing boundary.
