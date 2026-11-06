# golden-uav-30 — the golden screening workspace

The end-to-end quality gate of the production plan
(`docs/roadmap/production-plan.md` §6, M5-slim): the researcher screens these
30 records through the product, and `scripts/check_golden_workspace.py`
verifies the audit trail, the provenance of every decision and the PRISMA
counts.

## Contents

- **Protocol:** `protocol.json`, `intent.json`, `SCREENING_CRITERIA.md` and
  `protocol.sha256` are copied unchanged from `../uav-crop-weed-v03/`
  (protocol v0.3, frozen 2026-10-29).
- **Records:** `literature/verified.json` holds 30 records chosen from that
  workspace's screening batches by `scripts/build_golden_workspace.py`. The
  rule is deterministic, and `golden_selection.json` records it and the
  result:
  - 10 the agents included;
  - 15 clear exclusions, spread over six exclusion reasons;
  - 5 borderline exclusions (third-lane or second-pass).
- **Corpus:** the snapshot is accepted (`nexus-scholar accept-corpus`).
  Screening batches are not prepared yet; that is the first step of the
  golden run.

## What the strata are not

The strata come from **agent decisions that no human has confirmed**. They
only make the sample varied: they are not labels, they are not shown during
screening, and they are not ground truth. The golden run starts with no
decisions.

## Rebuild

```bash
uv run nexus-scholar init "Golden UAV 30" --dir workspaces/golden-uav-30 --scaffold-only
uv run python scripts/build_golden_workspace.py
uv run nexus-scholar accept-corpus -w workspaces/golden-uav-30
```

`init` also copies the agent skills into `.agents/`; that copy is removed here
because the repository root already provides them.
