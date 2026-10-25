# Researcher decisions — UAV crop/weed reliability pilot

Date: 2026-10-15 (UTC). Decided by the researcher in direct Q&A. These resolve
the open checklist in `calibration/REVIEW_DESIGN.md`. Nothing here assigns a
human, freezes the protocol, or performs screening — those remain separate
gated actions.

## Decided

1. **English scope: KEEP English-only + explicit bias statement.** Full-text
   language was never verified during calibration; the report must state
   English-only coverage as a limitation, not a finding about the literature.
2. **Date window: KEEP 2020 lower bound; cutoff = the future final search
   date.** WeedMap (2018) stays background-only. The S5 edge record (Crossref
   2026 vs OpenAlex 2025) is decided at execution: in-window iff published
   no later than the recorded final search date.
3. **Sources: NO IEEE Xplore / Scopus / WoS access.** Recorded as a coverage
   limitation. The search rests on OpenAlex / Semantic Scholar / Crossref /
   arXiv per `SEARCH_STRATEGY.md`.
4. **Reviewers: Option C — single reviewer with agent pre-sort.** The agent
   applies `SCREENING_CRITERIA.md` as triage suggestion ONLY; the human
   reviewer confirms/rejects every record and every agent-suggested exclude
   gets human review. **Reviewer assigned 2026-10-15: Mouadh Bekhouche
   (PhD student, the researcher). Verification-sample reviewers (added
   2026-10-15): Soumia Zertal (supervisor) and Fadhila Djenba (colleague)**
   — they independently re-screen a random ~10% sample plus all boundary
   excludes; agreement reported (e.g. Cohen's kappa via `scholar-search
   screen-compare`); disagreements resolved by full-text re-check, and any
   persistent disagreement is recorded with both positions. No separate
   adjudicator is assigned (none is required where no two humans screen
   the same full set). Requires before formal screening: (a) a logged
   protocol amendment stating the single-reviewer limitation and naming
   all three roles, and (b) prompt/version logging for the agent
   triage pass.
5. **Held-out set: ADOPT the 5 verified sentinels + 2–5 additions at
   full-text stage.** Sentinels are recall probes, not forced inclusions.
6. **Codebook: pilot-then-freeze.** Chart 2–3 full texts (dual-coded),
   decide the `heldout_date` vs `multiple_dates_no_heldout` rules there,
   log reasons for every change, then freeze. Abstract-only charting is
   insufficient (pilot: 100% `unavailable`) — full texts required.
7. **AvaRel-Fuse: NO eligibility constraint.** The draft stays
   motivation/background only; it includes nothing and excludes nothing.
8. **Background records: cite as related work in-text** (S2/WeedMap,
   D4-style reviews). No formal background appendix.

## Consequences recorded (not new decisions)

- Formal screening is still gated on: the logged single-reviewer amendment,
  the agent-triage prompt/version log, the executed final search with its
  recorded date, and the frozen codebook + protocol revision.
- The reviewer is the researcher themselves: valid under Option C
  (single reviewer, no inter-human comparison claimed), and the amendment
  must state this plainly rather than implying independent dual review.
- The agent triage prompt/version log is a deliverable of the triage pass,
  not of this decision.
- `protocol.json` is NOT amended by this file; the amendment is a separate
  gated protocol revision with its own fingerprint.
