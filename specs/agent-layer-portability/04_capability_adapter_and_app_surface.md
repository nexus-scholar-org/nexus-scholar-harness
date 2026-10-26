# 04 — Capability Adapter and Application Surface

This file covers the two things that make the previous three files usable by someone else: the **adapter** that actually enforces a role, and the **surface** that hides the entire apparatus.

---

## 1. The adapter interface

One interface, two implementations. It is deliberately small.

```python
class CapabilityAdapter(Protocol):
    def resolve_env(self, *, workspace: Path, config: Path) -> dict[str, str]:
        """Bind {CLI:*}, {KIT_ROOT:*}, {WORKSPACE}, {CACHE}, {CONFIG}."""

    def run(self, request: RunRequest) -> Envelope:
        """Execute one role against one request under enforced capability."""

    def emit(self, event: AuditEvent) -> None:
        """Append an attributed event to the workspace journal."""
```

```python
@dataclass(frozen=True)
class RunRequest:
    task_id: str
    role_id: str
    role_version: str
    inputs: tuple[Path, ...]
    params: Mapping[str, str]        # {ws}, {batch}, {stu}, ...
    arm: str | None = None           # triggers isolation when set
```

| Implementation | Used by | Enforcement |
|---|---|---|
| `OpencodeAdapter` | this repo's dev loop | **Best-effort.** Tri-state permissions plus adapter-side path checks before and after. Sufficient because the operator is the owner. |
| `InProcessAdapter` | the application | **Enforced.** Materialised run view, path validation at every I/O, egress control, adapter-written audit. |

Be explicit about the split rather than pretending one is the other. The dev loop is not a sandbox; the application is. A single implementation that claims both is how "read-only" ends up being a sentence in a markdown file.

## 2. What the adapter must guarantee

| Guarantee | Mechanism | Failure if absent |
|---|---|---|
| Write boundary | Role's output is staged into `runs/{task_id}/out/`, validated against `write_glob`, then promoted. Writes elsewhere fail at the filesystem layer. | Critics editing the artifact they judge |
| Read boundary | Run view contains only `read_glob` matches. `deny_glob` is a **write** denylist and never subtracts from the read view (see `01_role_model.md` R4). | Blind arm reads the other arm |
| Blinding | `isolation: directory` — separate materialised dirs per arm. `redacted-input` — identifying fields stripped before the view is built. | Dual coding collapses to single coding |
| Network | Per-role egress policy; `deny` means no sockets. | A judge reaches the web mid-verdict |
| Audit attribution | Adapter writes the journal; roles never can. Actor, role version, input/output hashes stamped by the adapter. | Generic actor names, unverifiable provenance |
| Reproducibility | Canonical JSON, hashed inputs, `envelope_id` | "It produced different numbers the second time" |

### Why not prompts

The repository already demonstrates the answer. Three agents state in prose that they are read-only and grant themselves write access. The prose is the intent; the permission map is the capability; the capability wins. No amount of prompt engineering changes that ordering, because the prompt is data the model *may* honour and the filesystem is a constraint the model *cannot* cross.

The adapter's job is to make every guarantee a filesystem fact.

## 3. Structural independence

Independence is not a property of a model; it is a property of the execution graph.

```
        ┌──────────── run view A ────────────┐      ┌──────────── run view B ────────────┐
batch → │ screener@A  (full inputs)          │      │ screener@B  (redacted identifiers) │
        └────────────────┬───────────────────┘      └────────────────┬───────────────────┘
                         └──────────────┬─────────────────────────────┘
                                        ▼
                              adjudicator (sees both, by design)
```

Rules the adapter enforces:

1. **No shared writable state.** A and B write to disjoint directories. Neither can observe the other's in-progress output.
2. **Blinding is applied to the inputs**, not requested from the agent. Redaction happens when the view is materialised.
3. **Ordering is not information.** Completion order, file mtimes, and directory listings outside the view are not exposed.
4. **The adjudicator is the only role with both views.** Its independence is the opposite property: it must be able to see everything, and its output must cite lineage.

This is the same principle already used successfully in the calibration design — blinding was implemented in the data pipeline, not in instructions. The adapter generalises it.

## 4. The human as a role: `HumanConfirmation@1`

The protocol's Option C requires the lead reviewer to confirm all agent triage. That requirement currently exists as a sentence in `protocol.json` and as an absence everywhere else.

Consequence: the correct claim today is *"588 mutually suggested by two agents"*, not *"588 included."* The gap between those sentences is one missing artifact.

```json
{
  "confirmation": 1,
  "scope": "screening/scr1",
  "reviewer": { "id": "mb", "role": "lead_reviewer" },
  "created_at": "2026-10-23T10:00:00Z",
  "artifacts": [
    { "path": "literature/screening/scr1_decisions_A.json", "sha256": "..." },
    { "path": "literature/screening/scr1_decisions_B.json", "sha256": "..." }
  ],
  "summary": { "considered": 626, "confirmed": 589, "changed": 37, "deferred": 0 },
  "decisions": [
    { "screening_id": "SCI-000027",
      "agent_state": "include_mutual",
      "final": "include",
      "changed": false,
      "rationale": null,
      "evidence_seen": ["title", "abstract"] }
  ],
  "signature": null
}
```

Why this is not bureaucratic overhead:

- **It closes the accountability loop.** Every include traces to a named person and a timestamp, on a specific artifact hash.
- **It makes disagreement a data product.** `changed: true` rows are the interesting ones — where human judgment overrode agent consensus. That is a differentiator no competitor can fabricate after the fact.
- **It makes the audit trail honest.** Without it, any claim of confirmation is unverifiable, and an auditor who asks "who decided this?" gets a role name, not a person.

The `human-confirm` role declaration is deliberately minimal: `tools: [read]`, `network: deny`, `edit` limited to `workspaces/{ws}/confirmations/**`, `bash: deny`.

## 5. The application surface

What a user of the product sees:

```
create project → protocol → search → agent triage → YOUR exceptions → confirm → chart → export
                                                        │
                                          disagreements, pendings, ties,
                                          each with quote + locator + hash
```

| Visible | Hidden |
|---|---|
| Their protocol and criteria | Role names (`screener`, `critic`, `extractor-b`) |
| Records, abstracts, PDFs | Kit names and CLI entry points |
| Agent verdicts **as suggestions** | Pins, revisions, manifests |
| The exception queue | Lane vocabulary (A1/A2/T3, mutual_*, third_*) |
| Evidence with quote and locator | `uv`, `git`, branches, worktrees |
| Who confirmed what, when | Batch hashes, envelope ids, SHAs |
| The export bundle and its manifest | The existence of an agent layer at all |

The last row is not shyness. Leaking the org chart into the customer's workflow turns a product into a services engagement, and services do not scale.

### 5.1 The exception queue is the product

Every deterministic step can be automated. What cannot is judgment at the boundary. The queue surfaces only:

- records where two arms disagree,
- records where an arm deferred (`PENDING`),
- records where three arms tie,
- extractions where quotations or locators fail verification,
- identity collisions (same title, different DOI; same DOI, different reports).

Each row shows: the record, both verdicts with one-line rationale, the criteria clause at issue, the source text that matters, and three actions — confirm, override, defer. Each action writes a `HumanConfirmation` row preserving parent hashes.

A good review looks like a short queue. That is the metric to optimise, and it is measurable per workspace.

### 5.2 Lineage is the signature surface

Click any charted cell:

```
cell value → verbatim quote → page/paragraph locator → source sha256
           → extraction envelope → the two arms → adjudication (if any) → confirmer
```

Nobody can fake this after the fact, which is precisely why it is worth building. Everything above it — search, dedup, heuristics — is commodity.

### 5.3 Failure is a rendered state, not an error

| Envelope status | What the user sees |
|---|---|
| `BLOCKED_INPUT` | "7 records could not be screened: full text unavailable." With the list and two actions: add file, or exclude with a logged reason. |
| `PARTIAL` | "Screening covered 43 of 50 records." Never silently presented as complete. |
| `REFUSED` | "Automatic PDF retrieval does not support records without a DOI or arXiv id." With the manual path. |
| `GATE_FAILED` | "This change did not pass validation." With the failing command. |

The rule the whole system is built around — *provider failure is not empty success* — becomes a UI contract rather than a code review habit.

### 5.4 Export bundle

```
export/
  protocol.json  SCREENING_CRITERIA.md
  decisions/{A,B}.json  adjudication/  confirmations/
  extraction/{A,B}/  critique/
  charting/  synthesis/
  audit/journal.jsonl
  MANIFEST.sha256
  README.md            # method, roles, versions, limitations
```

`MANIFEST.sha256` covers every file except itself. The README names the role versions used, the kit revisions, the exception rate, and every unresolved item. A reviewer can verify the bundle without access to the product, and without trusting the product's word for it.

## 6. What the adapter must refuse to do

- Run a role without a declared `write_glob`.
- Write the audit journal on behalf of a role that did not emit an event.
- Promote an artifact whose parent hashes do not verify.
- Accept an `OK` envelope with incomplete coverage.
- Reuse an existing `envelope_id` for a different payload.
- Operate in `InProcessAdapter` mode without materialising a run view — "in-process" is not an exemption from isolation.
