# Open work triage — 2026-10-20

> **Update 2026-10-29 (post-agent-layer).** The agent-layer portability phases
> A–E are merged (PRs #149–#159: roles, `Envelope@1`, `HumanConfirmation@1`,
> skill portability, capability adapters, plus the Windows lock repair and the
> app-mode residual-limits record). **No PRs are open.** The queue below is
> unchanged except: **protocol v0.3 is now FROZEN** (delegated decision,
> 2026-10-29; fingerprint `f81e6c58…f755`) and the **screening backlog is now
> resolved as agent decisions** — 14,150 records screened into 644 included /
> 13,506 excluded (346 of them *not retrieved*, deviation DEV-01), emitted as
> `literature/included.json`, `excluded.json` and the PRISMA pair in
> `workspaces/uav-crop-weed-v03/`. `HumanConfirmation@1` is still **unsigned**,
> so human screening confirmation and the reviewer-consent/redaction item
> remain open (they are not blocking the UI track); WP-06/WP-13 remain the only
> genuinely open WP rows; and the paperwork reconciliation is now recorded in
> [`UPCOMING_WORK.md`](../UPCOMING_WORK.md), the HCM track README, and
> `specs/agent-layer-portability/README.md`.

**Purpose.** One page that answers: *what is actually open?*
Everything else in this repo that reads like a backlog (the tracker, the packets
draft, the lessons backlog) is superseded by this file for triage purposes.

**Short version:** the list looks like ~48 items. It is really **4 things to do**,
**1 thing already running**, and **~43 labels that need no work** — most of them
because the work is already done and nobody reconciled the paperwork.

---

## The honest count

| Source | Reads as | Actually is |
|---|---|---|
| `docs/UPCOMING_WORK.md` packet inventory | 25 open packets | 2 genuinely open |
| `docs/architecture/packets_from_uav_demo_2026-10-19.md` | 10 packets | 2 next, 8 parked |
| `docs/lessons/…` backlog (K1–K6, H1–H6) | 12 items | 1 next, 11 parked |
| Orchestrator packet `T-D0D2` | 1 | running |
| **Total that reads as open** | **48** | **4 to do, 1 running** |

---

## Bucket 1 — DO NOW (4 items, ~2–3 days total)

| # | Item | Time | Why it can't wait |
|---|---|---|---|
| **1** | **Pilot close-out**: freeze the protocol, resolve the screening backlog, repair the counts, write the report honestly | done except human confirmation | The corpus exists and is paid for. Freeze + agent screening are done (644 included / 13,506 excluded, PRISMA emitted). What remains is the part only you can give: confirming decisions for AG-05's independent labels. |
| **2** | **K0 — repair + land the search-kit tree** | half a day + review | The kit is red and unpinned. It blocks B-D1 and every kit-side item. |
| ~~**3**~~ | ~~**UI CI job**~~ | 30 min | **DONE 2026-10-20** — see below. |
| **4** | **Fix the staged false claims** in `workspaces/uav-pilot-demo/` (`project.json` + `README.md` say "no search executed"; 2,165 records are staged for commit) | 5 min | It is queued for commit right now. |

### Item 3 — DONE (2026-10-20): the Research UI is now in CI

`.github/workflows/ci.yml` gained two jobs. Until now the app's 216 vitest tests,
its production build and its 82 Playwright browser tests ran on **no one**'s push.

| Job | Needs | Runs |
|---|---|---|
| `research-ui` | Python **and** Node | `npm ci` → `npm run typecheck` → `npm run test` → `npm run build` |
| `research-ui-browser` | Node only | `npm ci` → `npx playwright install --with-deps chromium` → `npm run test:browser` |

Two findings from building it, worth knowing:

1. **The vitest suite is not a pure-JS suite.** `tests/lineage.test.tsx` and
   `tests/screening-live.test.tsx` are cross-boundary "live mode against a real
   console" tests — they resolve the repo root from the checkout, build a
   `PYTHONPATH` over `src/` and `tools/*/src`, and spawn
   `uv run scholar-harness serve`. So the job needs the harness environment too.
   The kits come from the checkout's own `tools/*/src` via `PYTHONPATH` — no
   plugin install, no cloning.
2. **The browser suite is pure Node.** `tests-browser/screening-actions.spec.ts`
   fulfils the console at the network boundary with shape-conformant payloads, so
   it needs no live workspace.

Validated before landing: clean-room `npm ci` (160 packages, 82 s) → build exit 0
with all 9 locale/route prerenders → typecheck exit 0 **with no `next-env.d.ts`
and no `.next`** (both gitignored) → the two live-mode files fail outside a
harness checkout and pass inside one. The `taskkill` teardown in
`lineage.test.tsx` is `process.platform`-guarded, so Linux is safe.

**Not yet in CI (deliberate):** the long-strings gate, which runs its own second
build via `NEXT_DIST_DIR=.next-longstrings`. One extra step when wanted.


**Item 1 is the real one.** Items 2–4 are small. If you only do one thing, do the
pilot close-out — it is the only work that cannot be done by anyone else.

---

## Bucket 2 — RUNNING (1 item)

| Item | State |
|---|---|
| ~~**T-D0D2** — screening decision contract reader + validator~~ | **DONE 2026-10-20.** Reviewer APPROVE, tester gate PASS. |

### T-D0D2 — DONE (2026-10-20): the demo's validator is now a harness feature

`src/scholar_harness/screening/decision_contract.py` + the
`agent_screen.py validate` subcommand. 83 new tests; suite `1466 → 1549`
(+83, exactly the new tests); conformance `169 passed, 2 skipped`; all four
baseline checks green; Contract v1 path provably untouched (`git diff` on
`contracts/` and the collector/batcher/integrity/worker/report modules is **empty**).

**What it does for you immediately:** it reads the pilot's 566 decision files
and reproduces the pilot's recorded ledger **exactly** — A1 `247 VALID / 36 DEBT`,
A2 `254 VALID / 29 DEBT`, total `501 / 65 / 0 BAD`, every per-tag count identical.
So the schema-debt picture you have is now **re-derivable by a harness tool**
rather than only by a workspace driver.

```powershell
uv run python src/scholar_harness/agent_screen.py validate workspaces/uav-crop-weed-v03 `
  --decisions-dir calibration_v03/screening_scr1/decisions `
  --contract <your contract config> --out <path outside the workspace>
```

Two things it now catches that the demo driver did not: **reordered decision rows**
(the defect the pilot quarantined in `batch_0040_decisions_A2_reorder_quarantine.json`),
and **silent non-verification** — if the id order cannot be checked, it says so
(`ID_ORDER_NOT_VERIFIABLE`) instead of reporting a clean `VALID`.

Recorded follow-ups (not blocking): an opt-in `--fail-on-bad` flag, and a
misattributed `NO_PARENTS_RESOLVED` reason when the real cause is a corrupt
decision file. Both are written into the packet.

---

## Bucket 3 — ALREADY DONE, PAPERWORK ONLY (≈16 items, ~30 min total)

**Not tickets. One reconciliation pass.** These read as open because nobody
reconciled the close-out. The tracker itself warns: *"Report stale or missing
evidence as unverified; do not infer percentages from packet counts."*

### The 13 WP rows marked "completion unreconciled"

| WP | Reads as | Reality |
|---|---|---|
| WP-02 RAG identity/non-fabrication | open | WP-01 E3 adopted with recorded debt |
| WP-03 Screening generation gate | open | AG-02/03C/04 shipped the controls; `generation.json` exists |
| WP-04 Typed PipelineSpec | open | `console/SPECS.md` is the live contract; `pipelines.py` exists |
| WP-05 Agent pipeline truthfulness | open | AG-02/03C shipped related controls |
| WP-07 PDF/extraction truthfulness | open | WP-01 E1/E2 adopted |
| WP-08 Graph mode correctness | open | scholar-graph-kit shipped |
| WP-09 Protocol integrity | open | compiler shipped, baseline drift-gate green |
| WP-10 Verification integrity | open | scholar-verify-kit shipped (retraction/DAS/COI/RoB) |
| WP-11 Outcomes/audit/lifecycle | open | `OperationOutcome` v1 + audit service migrated |
| WP-12 Packaging/surface parity | open | Phase 7 shipped v1.0.0 |
| **WP-06 Transitive dedup** | open | **genuinely open** — the roadmap wants union-find; the kit has a greedy single pass. This is B-D1's umbrella. |
| **WP-13 Legacy migration** | open | **genuinely open** — one recorded legacy exception, small |
| WP-14 Docs/release | open | consolidation shipped |

**→ 11 of 13 are shipped. The WP backlog is 2 items, not 13.**

### The rest

| Item | Reality |
|---|---|
| HCM-02/03, HCM-04 closure | HCM-06 merged, HCM-05 adopted; close-out record pending |
| **UI-05** | **Shipped** — PR #137 `feat(ui05): evidence lineage route and trace view`. The tracker still says "Open/planned". |
| F2–F5 | deferred, explicitly. F1 merged. |
| AG-06/07 | deferred, explicitly |

---

## Bucket 4 — PARKED (≈28 items)

**Parked means: written down with a trigger, not on a to-do list.** Each row says
what would make it worth reopening. Nothing here is a promise.

### Toolkits (kit repo — all blocked behind K0)

| Item | Trigger to reopen |
|---|---|
| B-D1 near-twin dedup pass | after K0 lands, **and** only if you plan another harvest (Phase C) |
| K1 dedup copy-semantics | when a driver is written against the kit again |
| K2 universe probes / date-partition iterator | when the next harvest needs a cap-bound leg recovered |
| K3 genericize remaining domain knobs | when a new provider is added |
| K4 hydrator quota-circuit-breaker | when a hydration leg 429s again |
| K5 shared ID normalizer | when a new identifier namespace appears |
| K6 sentinel seeds as kit fixtures | when the kit needs its own regression corpus |

### Harness

| Item | Trigger to reopen |
|---|---|
| D-1 verification lane | after T-D0D2 lands — this is the next one, and it is genuinely valuable |
| D-2 alias reader | **being delivered by T-D0D2** — not separate work |
| D-3 outcome-prior ban | when a judgment lane is dispatched to an agent that could be told an outcome statistic |
| D-4 lane-split gate | with B-D1 |
| C-1 DEBT tier | **only after** answering "how is DEBT different from Contract v1 `PARTIAL`?" — it may not need a new tier at all |
| A-1 protocol amendment record | when the protocol is frozen and amendments become frequent |
| X-1 cross-kit contract version | when D-1/C-1/A-1 have actually introduced shared types |
| H1 factored harvest-driver library | when you write the second round of drivers |
| H2 partitioned-search planner | with the next cap-bound harvest |
| H3 credential assert helper | when a new driver is written |
| H4 PRISMA accounting generator | when a corpus is actually citable (Phase C) |
| H5 identity mint pipeline | with Phase C |
| H6 retry-window policy | when a quota window dies again |
| HCM-1 `_drivers/` promotion rule | **as an ADR**, alongside T-D0D2's close-out — 20 min of writing |

### Agent controls

| Item | Trigger to reopen |
|---|---|
| AG-1 rate ladder | when a wave dies on provider rate limits again |
| AG-2 real AG-03A fixture | after the pilot close-out produces the human-confirmed packet — **this one is worth doing** |
| AG-05 scientific evaluation | after AG-2 |
| AG-06/07 charting, synthesis | deferred; each needs its own evidence decision |

### Phase C — the clean re-harvest

| Item | Trigger to reopen |
|---|---|
| One re-harvest + re-screen with the fixed query shape | **only if you want a publishable review.** If you want a methodological pilot (which is what you have), this never triggers. |

---

## What is *not* on any list, because it is not work

- The pilot's **54 lessons**. Those are captured knowledge, not a backlog. Reading them
  once is enough.
- The **1,418 files** in `workspaces/uav-crop-weed-v03/`. Evidence, not work.
- The **stale tracker rows**. They will keep reading as scary until someone reconciles
  them — which is Bucket 3, one 30-minute pass.
- The **`docs/architecture/packets_from_uav_demo_2026-10-19.md` drafts**. They are a
  menu, not a commitment. Nothing there is dispatched.

---

## The stop rule

**The pilot is complete when the corpus is confirmed and reported.** It does not
require:

- a publishable systematic review (it never will be — relevance-ranked retrieval
  supports no PRISMA completeness claim, and that sentence stays attached);
- every lesson turned into a ticket;
- every WP row reconciled;
- the kit perfectly generalized for a domain you may never run again.

A **methodological pilot** is a legitimate, complete, valuable outcome: it proved
blinding holds, it fired a pre-registered void condition and quarantined the tainted
arm, it produced a schema-debt report instead of coercing 65 files, and it caught a
dedup defect that would have silently corrupted a real review.

---

## The one thing I will change on my side

I have been adding analysis, and some of that load is mine. From here:

- **No new packets unless you ask.** Bucket 4 is parked, not queued.
- **One thing in flight at a time.** You currently have one (T-D0D2).
- **No re-listing of parked items** unless a trigger fires.
- When something is ready, I bring you the *decision*, not another analysis.
