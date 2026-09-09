# PhD Execution Checklist (compact)

**Core:** D1 — UAV/CV systematic review & benchmark manuscript (thesis ch.3). Instrument is finished; the measurement is the work.
**Co-track:** D2 (trust-provenance method, ~80% material ready) runs in parallel. D3 (meta-review) and D4 (software) are post-D1.
**Full plan:** `workspaces/ai-research-harnesses-trust/reports/PHD_DELIVERABLES_PLAN.md`

---

## D1 sprint — 90 days

### Weeks 1–2 · Scaffold tables from the matrix
- [ ] Generator script: paired intra-study benchmark tables (RQ1) — group `synthesis/synthesis_matrix.json` by dataset; per row keep `workspace_id`, `best_model` class (CNN / Transformer / Hybrid), `mIoU`, `F1`, `uav_collected`
- [ ] RQ2 table: `edge_runtime=true` rows (15 true-edge) + the 50 edge-runtime / 40 runtime studies — device, precision, resolution, fps, latency, power
- [ ] Accuracy audit: cross-check the top-20 anchor rows against `extracted/*.md` sources
- [ ] Resolve the 39 provisional inclusions → classification note (confirmed vs excluded, with reasons)

### Weeks 3–4 · Protocol & PRISMA
- [ ] PRISMA 2020 flow diagram from `project.json` numbers (1488 screened → 150 included → 138 fulltext → 94 audited)
- [ ] OSF registry entry; attach `protocol.json` fingerprint + `SCREENING_CRITERIA.md`

### Weeks 5–10 · Manuscript
- [ ] Methods section (pipeline + Phase-4 trust streams, provenance ledger)
- [ ] Results: RQ1 comparative tables + narrative; RQ2 edge-device comparison
- [ ] Sensitivity framing for 77 unclear-RoB studies; COI context for 11 industry-tie studies
- [ ] Discussion + limitations; conclusion

### Weeks 11–13 · Submission
- [ ] Internal review pass, PRISMA checklist, data availability statement
- [ ] Submit to target venue (CEA / Precision Agriculture / Remote Sensing)

---

## D2 — parallel, weeks 1–8
- [x] Draft from existing material (`method_comparison.md`, `docs/phase_6/README.md`, Phase-6 tests, audit ledger) — `reports/manuscript_d2.md` v1.2
- [x] Core figure: RAG baseline 43.3% entailment-VERIFIED vs verbatim pipeline 510/510 ≥90% (figures 1–4)
- [x] Numbers audit: `scripts/reproduce_d2_stats.py` — 37 assertions, all pass
- [ ] Author review of v1.2 (prose + front matter), then submit (RSM / JAMIA / arXiv)

## After D1 submitted
- [x] D3 framing prep: decision memo `reports/D3_FRAMING_DECISION.md`; Option A (early-evidence/living scoping review) adopted; 23 pending author records resolved via arXiv/OpenAlex
- [x] D3 framing applied: `manuscript_draft.md` v2 — living-review title/front-matter, §3.8 protocol (cadence/versioning/preprint policy), §5.3 limitations, §7 declarations; 36/36 refs author-attributed
- [ ] D3: author review of v2, then submit (Systematic Reviews / RSM)
- [ ] D4: software paper (JOSS) — Phase-7 P7.1–P7.9 becomes its content

---

## Guardrails
1. Zero new harness/kit features until D1 is submitted.
2. Weekly check: "did this produce text/data a reviewer can read?" No → back to D1 scaffolding.
3. Phase-7 work is gated behind D4.
4. Progress metric = completed tables + manuscript word count, not commits.