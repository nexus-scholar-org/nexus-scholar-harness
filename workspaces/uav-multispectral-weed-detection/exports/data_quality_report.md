# Data-Quality Audit Report

**Project:** uav-multispectral-weed-detection
**Run:** 2026-09-02 (post-corpus-cleanup, post-re-index)
**Scope:** Task-type re-classification of non-segmentation papers; full-text availability gaps; SSRN attribution integrity; chunk-count reconciliation.
**Corpus baseline:** 25 extracted full-text documents; RAG index `uav_msi_weeds` = **1185 chunks** (rebuilt; previously mis-stated as 2516).

---

## 1. Non-segmentation task re-classification

Two corpus members are **not semantic-segmentation** studies. They were retained for relevance (multispectral UAV weed sensing) but must **not** be counted as segmentation evidence in RQ1/RQ2 accuracy synthesis.

| Paper | DOI | Task type | Evidence role in corpus |
|---|---|---|---|
| Che'Ya (2021) — *Assessment of Weed Classification Using Hyperspectral Reflectance and Optimal Multispectral UAV Imagery* | 10.3390/agronomy11071435 | **Classification** (pixel/ROC classification, hyperspectral + MS UAV bands) | RQ1/RQ3 relevance only; **no mIoU/segmentation metric** — excluded from segmentation accuracy comparisons |
| Alexandridis (2017) — *Novelty Detection Classifiers in Weed Mapping: Silybum marianum Detection on UAV Multispectral Images* | 10.3390/s17092007 | **Novelty / one-class detection** (auto-encoder identity mapping, precision/accuracy) | RQ3 relevance only; **no mIoU/segmentation metric** — excluded from segmentation accuracy comparisons |

These two were already marked in `synthesis/evidence_matrix.md` (§D) and are carried in `literature/synthesis_matrix.csv` with `segmentation_accuracy` flagged as classification/novelty rather than mIoU. They remain in the 25-file corpus for breadth but are tagged non-segmentation.

---

## 2. Full-text availability gap — Barrero (2018)

| Field | Value |
|---|---|
| Paper | Barrero et al. (2018) — *RGB and multispectral UAV image fusion for Gramineae weed detection in rice fields* |
| DOI | 10.1007/s11119-017-9558-x |
| Access | **Closed access** — full text unobtainable (OpenAlex `is_oa: false`, `oa_status: closed`, no OA location; ResearchGate 403; europepmc `isOpenAccess: N`) |
| Doc | `evt-brr-3120` (`FULLTEXT_UNAVAILABLE`); abstract captured (M/MP 80–108%, fused RGB-NGRDI) |
| Impact | Abstract-level evidence only; **no full-text segmentation metrics** available. Tracked as a documented gap, not a silent omission. |

Barreto remains a *screened/excluded-from-fulltext* record — it has no extracted MD and is **not** in the 25-file corpus or the 25-entry `references.bib`.

---

## 3. SSRN attribution integrity

| Key | DOI | Title | Authors (verified) | UTF-8 intact? |
|---|---|---|---|---|
| `ssrn-7129570` | 10.2139/ssrn.7129570 | UAV-Based Monitoring of Water Hyacinth for Invasive Weed Management | Wang, Zhenglin; ray, Biplob; Hassan, Jahan; Islam, Nahina; Kiran, Pali Rushi; Rani, N. Shobha; Bhattarai, Surya | ✅ |
| `ssrn-7345639` | 10.2139/ssrn.7345639 | From barley to rapeseed: few-shot fine-tuning of semantic segmentation models for weed detection using UAV multispectral imagery | Hernández Ludeña, Patricio Alonso; Fernández Piñar, Carlos; López de Herrera, Juan; Herrero Tejedor, Tomás Ramón; Pérez Martin, Enrique; Raimundo, Javier; Calderón, Jonathan | ✅ |

- `references.bib` parses cleanly via bibtexparser 2.0.0b9 — **25/25 entries**, all `doi` fields resolve to the corresponding paper.
- Author-name encodings (ñ, á, ü) are **valid UTF-8** in `references.bib` (no replacement characters). Earlier display showed mojibake due to Windows cp1252 console rendering only — the on-disk bytes are correct.
- NOTE: `10.2139/ssrn.7129570` is a **preprint** (SSRN working paper, 2026) and `ssrn-7345639` likewise an SSRN preprint. Both carry `study_design = Empirical Evaluation Benchmark` in `references.bib` and should be cited as preprints rather than peer-reviewed articles in final writing.

---

## 4. Chunk-count reconciliation

| Metric | Old (stale) | New (verified) | Where |
|---|---|---|---|
| RAG vector chunks | 2516 | **1185** | rebuilt collection `uav_msi_weeds` |
| Extracted docs | 25 | **25** | `extracted/` |
| Synthesis matrix rows | 24 | **25** | `literature/synthesis_matrix.*` |
| Bibliography entries | — | **25** | `literature/references.bib` |
| Citation-graph nodes | 0 | see §graph (Item 6) | `literature/citation_graph.*` |

(The 2516 figure was inherited from the now-deleted contaminated/pre-reindex DB.)

---

*This report is the authoritative record for task-type classification, availability gaps, and attribution checks referenced in `INDEX.md` and the audit journal.*
