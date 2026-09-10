# OSF Registries — Submission Snippet (Version 1.0)

Copy-paste-ready fields for the OSF Registries "Preregistration" flow. Full
registration body: `reports/D3_OSF_REGISTRATION_DRAFT.md` (long form). Every fact
below derives from `protocol.json`, the D3 draft, or the manuscript; no new
claims are introduced.

## 1. Copy-paste fields

- **Title**
  A Grounded, Verbatim-Verified Early-Evidence Living Scoping Review of AI
  Research Harnesses for Trustworthy Scholarly Synthesis: Traceability, Audit,
  and Reproducibility (Version 1.0)

- **Authors**
  Mouadh Bekhouche; Soumia Zertal (supervisor, corresponding author,
  zertal.soumia@univ-oeb.dz)

- **Description** (2–3 sentences for the form)
  Protocol-driven, five-source (OpenAlex, Semantic Scholar, Crossref, PubMed,
  arXiv; 2023–01 to 2026–09, Version 1.0) early-evidence living scoping review
  of AI research harnesses that integrate large language models and agentic AI.
  Two competing synthesis pipelines are compared — a deterministic RAG baseline
  and an authoritative multi-agent full-text claim-extraction pipeline whose
  510 claims pass threshold-verified evidence-quote matching (≥90% glyph-
  normalized coverage) — under a four-stream trust audit (retraction status,
  open-science artifacts, conflict of interest, risk-of-bias). Live at
  Version 1.0; corpus finalized 2026-09-09; quarterly living re-runs planned.

- **Keywords / tags**
  systematic review automation; scoping review; large language models; agentic
  AI; evidence synthesis; execution provenance; reproducibility; citation
  verification; living review

- **Registration type**
  Preregistration — living review protocol, Version 1.0 (re-registered at each
  quarterly update)

- **Protocol fingerprint (canonical sha256)**
  `sha256:9646d5ec6902c8f7687dfcb6568e473e1e01b78f666b20b74ec901f9703bf55c`
  (protocol.json compiled 2026-09-08, audit event EVT-20260908074732-58180d)

- **Research questions**
  RQ1: What is the state of the art in academic research and literature-review
  harnesses integrating LLMs and agentic AI (2023–2026), and what design
  mechanisms do they implement for execution provenance, audit trails, and
  process reproducibility?
  RQ2: What evidence-trust and academic-integrity mechanisms (citation
  fact-checking, hallucination mitigation, retraction checks, risk-of-bias,
  open-science artifact verification) do they incorporate?
  RQ3: How are they empirically evaluated (benchmarks, ablations, inter-rater
  reliability, user studies), and what architectural gaps remain for
  constructing trustworthy research infrastructure?

- **Funding / conflicts of interest**
  None. Both authors declare no conflict of interest. The Nexus Scholar toolkit
  (the authors' own harness) was excluded from the review matrix as a
  self-selection control.

- **Have any data been collected for this study already?**
  Version 1.0 review artefacts exist and are public in the versioned
  repository (deduplicated search log, PRISMA flow, 510-claim ledger, 95-cluster
  consensus map, Phase-4 trust streams). This registration is prospective for
  the submission pipeline and governs all subsequent living updates (v1.1+);
  each update publishes a new version with corpus-finalization date.

- **Planned start / completion**
  Registered at Version 1.0 (2026-09); quarterly updates thereafter.

## 2. Form body — paste the full protocol

Use the long-form content of `reports/D3_OSF_REGISTRATION_DRAFT.md` as the
registration body (sections: general information, research questions, living
realisation, verbatim eligibility criteria, information sources and search,
screening/extraction plan, trust and risk-of-bias plan, synthesis plan,
commitments).

## 3. Submission steps (human)

1. OSF → **Registries** → "New Registration" → choose the **Preregistration**
   template (or "Systematic Review" template where offered by the institute).
2. Fill the fields in §1 above; paste the body from §2.
3. Add OSF links: protocol.json (hash-pinned) and the living-review repository;
   attach `literature/search_log_v1.0.json` and the PRISMA flow figure as
   supplementary files.
4. Save as a **private registration** first; set the embargo/visibility per
   journal policy (public before or at submission).
5. Record the registration URL + DOI in manuscript §7 and `INDEX.md`, then log a
   `D3_OSF_REGISTRATION_SUBMITTED` audit event with the returned OSF DOI.