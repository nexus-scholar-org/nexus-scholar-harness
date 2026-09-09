# OSF Registration Draft - UAV CV Precision Agriculture Review (D1)

Registration-ready content derived from `protocol.json`. Submit to OSF Registries as a
"research plan / systematic review" preregistration before manuscript submission (planned: 2026-09-22).
Registrator must fill [bracketed] fields.

## 1. General information

- Title: UAV Computer Vision for Precision Agriculture: Deep Learning Segmentation and Edge Inference Benchmark Review
- Registration date: [YYYY-MM-DD]
- Principal investigator: [Name, affiliation, ORCID]
- Contributing reviewers: [Names]
- Corresponding author: [email]
- Planned registration type: Preregistration (review protocol)
- Protocol fingerprint (canonical sha256, scholar-protocol-kit): `sha256:e1bbcb791d9108b2277fa468982f59cbdc611a66288556c5f4812fde34f1b077`
- Protocol source: `workspaces/uav-cv-precision-agriculture/protocol.json` (schema-validated, compiled 2026-09-03)
- Review registrant entity: [institution / IRB as applicable]
- Funding / COI declaration: none known; all reviewers declare no conflict of interest

## 2. Research questions

- RQ1 - Comparative segmentation performance (mIoU, F1-score) of CNN, Transformer, and Hybrid architectures on agricultural UAV crop-weed imagery (facet: algorithmic accuracy).
- RQ2 - How do edge hardware constraints (TDP, compute in TOPS) and execution configurations (quantization precision, input resolution) impact inference throughput/latency for agricultural UAV segmentation (facet: hardware efficiency).
- RQ3 - What is the trust and reporting quality of the evidence base (retraction status, open-science artifact availability, conflicts of interest, risk-of-bias) - consensus synthesis.

## 3. Eligibility criteria (verbatim from protocol.json)

Inclusion:
- INC-01: Focuses on deep learning architectures (CNN, Transformer, or Hybrid) applied to UAV aerial imagery for agricultural crop/weed pixel-level segmentation. (RQ1, RQ2)
- INC-02: Reports quantitative pixel-wise segmentation accuracy metrics (e.g., mIoU, class IoU, Dice/F1) on agricultural benchmark or custom UAV datasets. (RQ1)
- INC-03: Reports on-device empirical hardware execution metrics (e.g., FPS, latency ms, power W, memory footprint) on physical edge platforms or embedded accelerators. (RQ2)

Exclusion:
- EXC-01: Non-UAV imaging modalities (satellite-only, ground-vehicle/tractor-only, laboratory bench-top without aerial flight context).
- EXC-02: Bounding-box detection or whole-image classification without pixel-level segmentation masks.
- EXC-03: Agricultural domains outside crop and weed management (orchard fruit counting, forestry canopy, livestock, soil moisture).
- EXC-04: Exclusively non-deep-learning methods (classical vegetation indices, shallow ML without learned features).
- EXC-05: Secondary literature without primary empirical benchmarks (surveys, reviews, tutorials).
- EXC-06: Non-English text or records lacking retrievable quantitative results.

## 4. Information sources and search

- Databases: OpenAlex, Semantic Scholar, Crossref, PubMed, arXiv (federated via scholar-search-kit).
- Date range: 2018-01-01 to 2026-12-31 (end inclusive).
- Language: English.
- Open-access preference: yes (harvest Gold OA + PDFs).
- To-be-expected pool: 500-2,000 candidates per provider config; engine-enforced in protocol.
- Core concept Boolean groups (OR within concept, AND across): UAV platform; crop/weed agriculture; deep-learning segmentation; edge computing/deployment. Synonym lists verbatim in protocol.json search_strategy.

## 5. Screening and data extraction plan

- Dual independent title/abstract screening (template + criteria-driven screeners) with third-party adjudication of every dispute. Expected kappa disclosure; disputes adjudicated by 6 panels.
- Stage-3 full-text verification for provisional caveats (CAVEAT_EXC06), resolved per decision rule: numeric segmentation metric required for inclusion; otherwise exclude (EXC-06).
- Structured extraction (YAML-frontmatter Markdown) driven by matrix dimensions in protocol.json (model architecture, benchmark dataset + altitude/GSD, segmentation metrics, edge runtime metrics, dataset split/validation, code/artifacts).
- Data verification: multi-agent full-text claims override deterministic RAG output; claims require quote-level evidence with page references.

## 6. Trust and risk-of-bias plan

- Retraction check: OpenAlex/Crossref (required).
- COI and funding audit (required).
- Reproducibility artifact check: DAS/CAS open-science scan (required).
- Risk-of-bias: QUADAS-2-adapted + PROBAST scoring (deterministic).
- Minimum trust score threshold: 6.0 (protocol verification block).
- Consensus synthesis over trust clusters to guard reports against single-source bias.

## 7. Synthesis plan

- RQ1: comparative benchmark matrix across architecture families x datasets (mIoU/F1), with paired intra-study comparisons where multiple models are evaluated on the same dataset.
- RQ2: hardware x runtime matrix (device, precision, resolution, fps, latency, power, params, FLOPs); true-edge definition = embedded-class board AND measured fps/latency.
- RQ3: trust consensus (ADEQUATE / WEAK / UNVERIFIED clusters) reported alongside streams; sensitivity framing for 2026 preprint-heavy evidence.
- No quantitative meta-analysis planned across distinct datasets (88 distinct datasets identified); narrative synthesis with reported metrics per dataset.

## 8. Ethics and data availability

- Publicly available literature only; no human subjects.
- All pipeline artifacts (screening batches, decisions, extraction, audit ledger) versioned in the review repository.
- Deviation handling: any divergence from this protocol must be logged in the append-only audit ledger (audit/journal.jsonl) with timestamp and justification.