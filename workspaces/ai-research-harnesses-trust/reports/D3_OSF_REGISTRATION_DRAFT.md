# OSF Registration Draft — AI Research Harnesses & Trust Living Scoping Review (D3)

Registration-ready content derived from `protocol.json`. Submit to OSF Registries as a
"research plan / systematic review" preregistration before journal submission (planned;
this is a living review — register Version 1.0, then version the registration at each
quarterly update).

## 1. General information

- Title: A Grounded, Verbatim-Verified Early-Evidence Living Scoping Review of AI Research Harnesses for Trustworthy Scholarly Synthesis: Traceability, Audit, and Reproducibility (Version 1.0)
- Registration date: [to be planned, before first journal submission]
- Principal investigator: Mouadh Bekhouche, University of Oum El Bouaghi, ORCID 0009-0009-7912-7656
- Authors: Mouadh Bekhouche; Soumia Zertal (supervisor, corresponding author)
- Corresponding author: Soumia Zertal (zertal.soumia@univ-oeb.dz)
- Planned registration type: Preregistration (living review protocol, Version 1.0)
- Protocol fingerprint (canonical sha256, scholar-protocol-kit): `sha256:9646d5ec6902c8f7687dfcb6568e473e1e01b78f666b20b74ec901f9703bf55c`
- Protocol source: `workspaces/ai-research-harnesses-trust/protocol.json` (schema-validated, compiled, fingerprint recorded in audit journal EVT-20260908074732-58180d)
- Review registrant entity: University of Oum El Bouaghi, Algeria
- Funding / COI declaration: none; both authors declare no conflict of interest; the Nexus Scholar toolkit was excluded from the review matrix (self-selection control)

## 2. Research questions

- RQ1 — What is the state of the art in academic research and literature review harnesses that integrate LLMs and agentic AI (2023–2026), and what concrete design mechanisms do they implement for execution provenance, audit trails, and process reproducibility?
- RQ2 — What evidence-trust and academic-integrity mechanisms (citation fact-checking, hallucination mitigation, retraction checks, risk-of-bias, open-science artifact verification) are incorporated into modern AI research harnesses?
- RQ3 — How are AI-assisted research harnesses empirically evaluated (benchmarks, ablations, inter-rater reliability, user studies), and what architectural gaps remain for constructing a novel, trustworthy research infrastructure?

## 3. Realisation as a living review

- Review type: early-evidence living scoping review (not a traditional one-shot systematic review); window 2023-01 to 2026-09, Version 1.0 corpus finalized 2026-09-09.
- Cadence: quarterly re-run of the five-source federation with the same concept-and-synonym strings; each run advances the trailing publication-date boundary.
- Versioning: each update publishes a new version (v1.1, v1.2, …) with corpus-finalization date; aggregate figures carry the version they were computed from.
- Preprint policy: preprint-track records (arXiv/bioRxiv/institutional repositories) are eligible and retained; preprint→published supersession tracked via Crossref `update-to`/OpenAlex status, diff-disciplined and versioned.
- The full protocol is in §3.8 of the manuscript; the living-review specifics are part of this registration so the later versions inherit them.

## 4. Eligibility criteria (verbatim from protocol.json)

Inclusion:
- INC-01: Proposes, implements, or evaluates a computational tool, system, harness, or multi-agent pipeline specifically designed for academic literature discovery, screening, extraction, citation graph analysis, or evidence synthesis. (RQ1–RQ3)
- INC-02: Incorporates Large Language Models (LLMs), agentic orchestration, or modern RAG mechanisms within the scientific literature workflow. (RQ1–RQ3)
- INC-03: Explicitly describes or evaluates mechanisms for execution provenance (audit logs, DAG pipelines), citation verification / hallucination mitigation, or academic integrity (retraction, risk-of-bias, or open-science checks). (RQ1, RQ2)
- INC-04: Provides an accessible codebase, architecture specification, or quantitative empirical evaluation (precision, recall, citation accuracy, benchmark metrics, or user study). (RQ2, RQ3)

Exclusion:
- EXC-01: Pure academic writing, paraphrasing, grammar, or paper-authorship tools (e.g., Paperpal, generic ChatGPT writing prompts) lacking literature workflow orchestration or provenance. (PURE_WRITING_TOOL)
- EXC-02: General-purpose conversational RAG or enterprise search systems not specifically targeted to academic research or scientific literature. (NON_SCHOLARLY_DOMAIN)
- EXC-03: Narrative opinion pieces, commentaries, or high-level philosophical manifestos lacking a described system architecture or empirical evaluation. (NO_COMPUTATIONAL_ARTIFACT)
- EXC-04: Published prior to 2023 (excluding pre-LLM historical literature). (TEMPORAL_OUT_OF_BOUNDS)
- EXC-05: Full text not available in English. (NON_ENGLISH)

## 5. Information sources and search

- Databases: OpenAlex, Semantic Scholar, Crossref, PubMed, arXiv (federated via scholar-search-kit); bioRxiv-track preprints captured through PubMed/Crossref indexing.
- Date range: 2023-01-01 to 2026-09-30 (Version 1.0; boundary advances each living update).
- Language: English only.
- Open-access preference: no (full-text OA preferred for extraction, but eligibility does not require OA).
- Core concept Boolean groups (OR within concept, AND across): (literature-review automation | systematic review automation | research harness | scholarly workflow | evidence synthesis | academic literature review) AND (large language model | LLM | agentic AI | AI agent | retrieval-augmented generation | generative AI | multi-agent).
- Full query evidence per version: `literature/search_log_<version>.json` (Version 1.0: `search_log_v1.0.json`).

## 6. Screening and data extraction plan

- Four independent AI screeners across 12 agent-in-the-loop batches with explicit criteria; Fleiss' κ reported.
- Majority voting (≥3 of 4) for routine resolutions; two-vs-two deadlocks escalated to a third-party senior adjudicator.
- Structured extraction (YAML-frontmatter Markdown) driven by matrix dimensions in protocol.json.
- Data verification: multi-agent full-text claim extraction (510 claims at Version 1.0) with threshold-verified evidence quotes (≥90% glyph-normalized coverage on char-window or token 6-gram matching); deterministic RAG baseline reported as comparison, not source of truth.

## 7. Trust and risk-of-bias plan

- Retraction check: OpenAlex/Crossref for all included records with resolvable PIDs (48/58 checked at v1.0; 0 flagged).
- Conflict-of-interest and funding audit: 47 studies scanned at v1.0; category tallies reported.
- Reproducibility artifact check: DAS/CAS open-science scan (repo links, code/artifacts).
- Risk-of-bias: PROBAST/QUADAS-2-adapted deterministic scoring via scholar-verify-kit.
- Living protocol (§3.8) defines how the search boundaries, preprint supersession, and claim ledger are updated at each version.

## 8. Synthesis plan

- Comparative matrix (RQ1/RQ2) and narrative + gap analysis (RQ3) per protocol synthesis_type.
- Semantic consensus clustering of the claim ledger (95 clusters at v1.0: 16 high-consensus, 7 debates, 37 unresolved, 35 provisional).
- No meta-analysis (scoping design).

## 9. Commitments

- Report in line with PRISMA-ScR + living-review guidance (adapted); flow of information and items in the manuscript.
- Prospective registration, then versioned re-registration at each living update.