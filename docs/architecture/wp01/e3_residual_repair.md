# E3 residual repair — 2026-10-09

## Scope

Harness-owned follow-up to the qualified WP-01 closure, based on canonical
main `8aea5284b026598429f53d84e7b84402d7a9a3c3`. No kit source, kit pin,
frozen contract, UI, or operator configuration changes are included.

## Installer authority

`scripts/install_plugins.py` resolves third-party requirements in one phase,
then installs the managed kits with `--no-deps` into the explicit harness
environment. Transitive managed dependencies and requested extras are expanded
from the registry, rather than following stale sibling Git references.
Remote dependency metadata is read at the selected full SHA. Local-only mode
does not fetch remote kit metadata. Verification runs in the harness directory
without synchronizing the environment; installation or verification failure
does not report an environment as ready.

A fresh isolated environment installed all eight managed kits. RAG's module
path and distribution `direct_url.json` both identify this checkout's editable
`tools/scholar-rag-kit`, not the stale agent-kit dependency revision.
Eight installer regression cases cover source selection, dependency extras,
cycles, remote metadata revision, environment selection, and failed installs.

## Formerly blocked ledger rows

The harness conformance gate now executes the vendored canonical service
battery against the verified harness-selected import:

| ID | Executed evidence |
|---|---|
| E3-NEG-021 | Absolute and traversal paths produce the exact typed PATH_OUTSIDE_WORKSPACE refusal, zero counts, no sidecar or backend. |
| E3-NEG-022 | A documents directory outside the accepted parent's scope refuses with PATH_OUTSIDE_WORKSPACE, without a run event or publication. |
| E3-NEG-050 | API and CLI refuse changed bytes under the stale accepted hash; the mixed batch is PARTIAL and the stale document has no visible chunks. |

The tests reuse their canonical owner assertions rather than maintaining
another copy of the kit implementation. The 29-row harness ledger contains
no MISSING entries. Proof-bound and declaration-only rows retain their original
limits; this does not make them full end-to-end runtime proofs.

## Mock and runtime repair

Replacement mocks now declare marker mode and return typed staged/visible
rows at the correct protocol stages. Identity tests observe the actual
IndexService requests instead of a retired ScholarIndexer path. Parent
assertions bind the accepted document manifest, whose screening lineage is
validated upstream. Audit assertions use canonical acceptance-event fields
and RAG_INDEX_REJECTED for failed runs.

An actual empty-run bug was exposed during that repair: the closed request
rejected an empty source tuple before the intended refusal branch could run.
The harness now returns an internal sentinel before request construction or
embedder creation, yielding the existing NO_DOCUMENTS_TO_INDEX outcome.
The real-subprocess JSON and no-success-event regressions remain active.
Stage 6 also retains the recorded screening decision ID in its JSON result
instead of returning a blank placeholder; no identifier is inferred or minted.

## Limits and handoff

Validation: full harness suite 795 passed / 6 platform skips; scripts lint,
all four generator checks, and eight kit entrypoint checks passed. The
screening-ID preservation delta additionally passed its two in-process and
real-subprocess indexing checks. No expected-failure allowance was used.

Historical E3/E4 completion reports remain historical records. This repair
discharges the installer, blocked-row, and obsolete-mock follow-ups; it does
not establish real acquired-PDF mutation coverage, independent physical-store
mutation coverage, deterministic fixture regeneration, or validated synthesis.
The user's intentional reviewer permissions and live UI work remain untouched.
