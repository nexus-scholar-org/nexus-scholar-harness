# Pilot source register — accepted full-text codebook pilot (2026-10-13)

**Status:** PRELIMINARY — no Contract-accepted documents. Convenience
acquisition only. Do not cite `DOC-<hex>.pdf` filenames as accepted
`document_id`. See §5 for the missing acceptance dependency.

**Protocol:** `proto-20261012-uav-crop-weed-reliability` v0.2 provisional —
fingerprint `sha256:a1fd8d2a82e0a5fca77deabbad360a1d8190d2d017d3ffa38342d8ac7ff73451`
(VALID, unchanged). Protocol NOT frozen.

**Retrieval command (exact):**
`uv run scholar-pdf download --doi 10.1109/wacv61041.2025.00467 --doi
10.3389/fpls.2022.927368 --doi 10.3390/rs15215165 --output
workspaces/uav-crop-weed-reliability/pdfs --export json`
Retrieval wall time: 2026-10-13T10:18:50Z (UTC; filesystem LastWriteTimeUtc;
local 11:18:50+02:00). Export: `pdfs/download_summary.json` (2/3 success).

## 1. WeedsGalore — preprint bytes inspected, published report NOT inspected

| Field | Value |
|---|---|
| Study family | WeedsGalore (maize crop/weed segmentation dataset + baselines) |
| Canonical DOI (published) | `10.1109/wacv61041.2025.00467` |
| Preprint | arXiv `2502.13103v1` (single version; `published 2025-02-18T18:13:19Z`, `updated` same; 11 pages, 7 figs, 7 tabs) |
| Publisher record (Crossref) | `proceedings-article`, 2025 IEEE/CVF WACV, `published 2025-02-26`, pages 4767–4777, `created 2025-04-08` |
| Publisher record (OpenAlex W4409263155) | `publication_date 2025-02-26`, `primary pdf None`, `oa_url https://arxiv.org/pdf/2502.13103`, `best_oa https://arxiv.org/pdf/2502.13103` |
| Retrieved file (gitignored) | `pdfs/DOC-a55418fca030fd024f8c845294521ed0.pdf` — convenience content address, NOT an accepted `document_id` |
| Bytes | 4,971,455; SHA256 `a55418fca030fd024f8c845294521ed057a2783937c2af253205e1b90434e5ad` (uppercase hex from Get-FileHash; lowercase canonical in register) |
| PDF metadata | `creator LaTeX with hyperref`, `producer pdfTeX-1.40.25`, `creationDate D:20250219021323Z` — consistent with arXiv v1 build 2025-02-19, NOT an IEEE Xplore imprint |
| Header (p.1, verbatim) | “This paper has been accepted for publication at the IEEE/CVF Winter Conference on Applications of Computer Vision (WACV) 2025. © IEEE.” + “arXiv:2502.13103v1 [cs.CV] 18 Feb 2025” |
| Version reconciliation | Preprint v1 (2025-02-18) predates IEEE proceedings date (2025-02-26) by 8 days. Title/authors match (Celikkan et al.; multispectral multitemporal UAV maize). The v1 header already declares IEEE acceptance, so v1 is the accepted-manuscript lineage, but the IEEE paginated version (4767–4777) was **not** retrieved or diffed. Any delta (copy-edit, pagination, added experiments) is **unresolved**. Extraction below is from preprint v1 only and is NOT final published-report extraction. |
| Convenience extraction (non-authoritative) | `extracted_prelim/DOC-a55418fca030fd024f8c845294521ed0.md` via `PyMuPDFEngine.extract_markdown` (54,695 chars, real body, 7 sections §§1–6 + Refs). Frontmatter is heuristic (`title` = stem, no DOI); it is NOT E2 bound frontmatter and carries no `document_id`/`source_sha256`/`study_id`. |
| Acceptance | NOT accepted. No E1/E2 parent binding (see §5). Retained as preliminary source note. |

## 2. SemiWeedNet — publisher OA bytes inspected

| Field | Value |
|---|---|
| Report | SemiWeedNet — “Semi-supervised Learning for Weed and Crop Segmentation Using UAV Imagery” |
| DOI | `10.3389/fpls.2022.927368` (verified Crossref + OpenAlex W4283752107) |
| Publisher record (Crossref) | `journal-article`, Frontiers in Plant Science, `published 2022-07-01` (= `published-online 2022-07-01`), vol 13, license CC-BY 4.0 `vor` |
| Publisher record (OpenAlex) | `publication_date 2022-07-01`, `primary pdf https://www.frontiersin.org/articles/10.3389/fpls.2022.927368/pdf`, `oa_url` same, gold OA |
| Article history (extracted p.1) | “Received: 24 April 2022 Accepted: 10 June 2022”, “published: 01 July 2022 doi: 10.3389/fpls.2022.927368”, “ORIGINAL RESEARCH” |
| Retrieved file (gitignored) | `pdfs/DOC-144697f8ab64af335c90427884112e76.pdf` — convenience address, NOT accepted |
| Bytes | 9,892,784; SHA256 `144697f8ab64af335c90427884112e766da3fc28d357cca10b536de4d52ffbca` |
| PDF metadata | `creator Adobe InDesign 14.0 (Windows)`, `creationDate D:20220626172039+05'30'` — consistent with publisher typeset |
| Convenience extraction | `extracted_prelim/DOC-144697f8ab64af335c90427884112e76.md` via PyMuPDF (46,587 chars, real body). Same non-authoritative caveat as above. |
| Version reconciliation | Single publisher Vor; no preprint lineage claimed. No date conflict (Crossref/OpenAlex/extracted imprint all 2022-07-01). |
| Acceptance | NOT accepted (same §5 gate). Retained as preliminary source note. Eligibility at title/abstract was INCLUDE; full-text confirms primary empirical study (Proposed Method + Data/Dataset + Results), not a review. |

## 3. Transformer in UAV Image-Based Weed Mapping — UNRESOLVED retrieval

| Field | Value |
|---|---|
| Report | “Transformer in UAV Image-Based Weed Mapping”, Zhao / Berge / Geipel (NIBIO) |
| DOI | `10.3390/rs15215165` (verified Crossref + OpenAlex W4388108146) |
| Publisher record (Crossref) | `journal-article`, Remote Sensing, `published 2023-10-29` (= online), vol 15(21):5165, CC-BY 4.0 `vor` |
| Publisher record (OpenAlex) | `publication_date 2023-10-29`, gold OA, `oa_url https://www.mdpi.com/2072-4292/15/21/5165/pdf?version=1698571223`, `any_repository_has_fulltext true`, but `locations` lists only the MDPI PDF + a DOAJ landing with `pdf null` — no repository mirror to fall back to |
| Retrieval attempts | (a) `scholar-pdf download --doi 10.3390/rs15215165` → **Failed: 403 Forbidden** (`https://www.mdpi.com/2072-4292…`); (b) direct versioned PDF fetch with Chrome UA → 403; (c) MDPI landing HTML with Chrome UA → 403. Prior calibration: publisher index inspected, direct article requests 429 (verification.json). |
| Interpretation | Provider failure (WAF/rate-limit), NOT empty success and NOT evidence of paywall or ineligibility. No bytes, no checksum, no snapshot retained. The prior “likely review” label remains corrected (SENIOR_REVIEW.md: publisher methods describe model design, ablations, ground-reference validation — primary empirical study), but no full-text verification is claimed here. |
| Acceptance | No source to accept. Retained as **unresolved retrieval** preliminary note. Not charted. Not counted in any denominator as excluded. |

## 4. Boundary probes (not retrieval targets)

- **WeedMap 2018** (`10.3390/rs10091423`, 2018) — date-negative/background probe, outside 2020 lower bound. Not a retrieval target. Reused as a *dataset* inside SemiWeedNet (RGB subset of WeedMap 000–004); that reuse does not make WeedMap 2018 itself an included study.
- **S5 precision-weed-detection review** (`10.1016/j.atech.2025.101656`; Crossref 2026 / OpenAlex 2025 display) — report-type/background probe (review). Outside the primary empirical corpus irrespective of year disagreement. Not retrieved.

## 5. Acceptance dependency (why zero accepted documents)

The supported authoritative paths are parent-bound and fail closed:

- **E1 `scholar-pdf acquire`** requires already-accepted `corpus_snapshot` + `screening_decisions` (artifact_id + sha256 + workspace-relative path). This workspace has `search_executed false`, no `literature/` corpus, no screening decisions — only calibration `_tmp_*.json` scratch (not a corpus). Fabricating parents to force acquisition would be invented provenance.
- **E2 `extract-run`** requires exactly one accepted `screening_decisions` (+ transitive `corpus_fingerprint`); same missing parent.
- **Harness `extract publish`** requires the accepted manifest chain; `extract status` would refuse with `DOCUMENT_MANIFEST_NOT_ACCEPTED` before any backend.

No `acquire`/`extract-run` config was submitted with fabricated parents. The
`download` + `PyMuPDFEngine.extract_markdown` outputs above are the legacy
non-authoritative convenience path (cf. kits_surface_matrix §pdf findings 3,
E1/E2 boundaries). They verify nothing (no checksum-bound `document_id`, no
manifest, no registry entry) and are therefore **preliminary source notes**,
not accepted charting. The charting schema’s `DOC-*` + `source_sha256` +
locator + quote requirements remain unsatisfied by design; no IDs were minted.

**Counts:** retrieved 2/3 target PDFs (both preliminary, 0 accepted);
unresolved 1/3 (S4, provider 403); accepted charting rows 0; preliminary
study notes 2; preliminary evaluation-setting notes 4 (WG×3 + SWN×1);
background/boundary probes 2 (not counted as eligible).

## 6. Reproducibility

- Source URLs, retrieval time (2026-10-13T10:18:50Z UTC), byte sizes, SHA256,
  PDF creators, OpenAlex/Crossref dates, and arXiv API payload (`2502.13103`
  v1 only, `published/updated 2025-02-18T18:13:19Z`) are recorded above from
  live lookups on 2026-10-13. The `pdfs/` bytes are gitignored; the register
  is the durable provenance. Convenience `extracted_prelim/*.md` are working
  state (to be removed before PR; quotations are preserved in
  `CHARTING_PILOT_NOTES.md`).
- No IEEE/Scopus/WoS credentials were used or inferred. No paywall bypass was
  attempted. MDPI 403 is disclosed as unresolved, not as restricted-confirmed.
