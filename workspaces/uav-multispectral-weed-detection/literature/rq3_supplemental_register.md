# RQ3 Supplemental Evidence Register

**Project:** uav-multispectral-weed-detection
**Target:** RQ3 — robustness to domain shifts (lighting variation, crop phenological stage,
sensor band calibration) across benchmark datasets.
**Added:** 2026-09-02

---

## Rationale

The original 26-paper corpus had the weakest explicit evidence coverage for RQ3: only
BAWSeg (10.3390/rs18060915) directly tested cross-plot/cross-year protocols. To strengthen
RQ3, three domain-generalization / cross-domain papers were identified and added.

---

## 1. Fully Ingested (PDF + full text)

### Gao et al. (2023) — Cross-domain transfer learning for weed segmentation
- **Title:** Cross-domain transfer learning for weed segmentation and mapping in precision farming using ground and UAV images
- **DOI:** `10.1016/j.eswa.2023.122980` (Expert Systems with Applications)
- **Authors:** Junfeng Gao, Wenzhi Liao, David Nuyttens, Peter Lootens, Erik Alexandersson, Jan Pieters
- **Access:** OA (hybrid) — downloaded from arXiv:2210.11545
- **File:** `pdfs/2023_Gao_CrossDomain_Transfer_Weed_Segmentation.pdf`
- **Extracted:** `extracted/2023_Gao_CrossDomain_Transfer_Weed_Segmentation.md` (53.0k chars)
- **RQ3 relevance:** Directly addresses **ground (RGB) → UAV (MSI) cross-domain transfer** for crop/weed
  semantic segmentation — the canonical imaging-platform domain shift. Provides quantitative
  cross-domain segmentation results, directly serving RQ3's cross-dataset robustness facet.

## 2. Catalogued as Supplementary (closed access — full text not obtainable)

### Zuo et al. (2026) — Cross-Date Generalization (temporal domain shift)
- **BibTeX Key:** `@zuo-2026-cross-date` (in `literature/references.bib`)
- **Title:** Improving Cross-Date Generalization in Multispectral Crop-Weed Segmentation via Shallow Feature-Statistics Mixing
- **DOI:** `10.1007/978-981-92-3531-5_10` (Springer, closed)
- **Authors:** Bingxin Zuo, Qinghao Shao, Jing Bi
- **RQ3 relevance:** Explicit **leave-one-date-out temporal domain-shift** protocol on the WeedsGalore
  dataset — measures robustness to **phenological stage / date** variation, the RQ3 "growth stage" facet.
- **Status:** catalogued for citation/synthesis; full text N/A (subscription).

### Weyler et al. (2023) — Domain Generalization in Crop-Weed Segmentation
- **BibTeX Key:** `@weyler-2023-domain-generalization` (in `literature/references.bib`)
- **Title:** Towards Domain Generalization in Crop and Weed Segmentation for Precision Farming Robots
- **DOI:** `10.1109/lra.2023.3262417` (IEEE Robotics and Automation Letters, closed)
- **Authors:** Jan Weyler, Thomas Läbe, Federico Magistri, Jens Behley, Cyrill Stachniss
- **RQ3 relevance:** Canonical domain-generalization method (RobustAverage / DG paradigm) for crop-weed
  segmentation across fields/sensors — supports the RQ3 **sensor calibration / lighting** robustness facet.
- **Status:** catalogued for citation/synthesis; full text N/A (subscription).

---

## Impact on RQ3 Evidence

| Evidence facet (RQ3) | Before | After |
|----------------------|--------|-------|
| Cross-field / cross-year | BAWSeg only | + Gao (cross-domain UAV), Weyler |
| Cross-date / phenological stage | none explicit | + Zuo (leave-one-date-out) |
| Cross-platform (ground↔UAV) | none | + Gao |
| Direct quantitative cross-domain scores | sparse | + Gao (full text) |

---

*This registry supplements the 26-paper primary corpus. The three RQ3 sources are tracked here so
they can be folded into RQ3 synthesis without altering the primary included-set counts.*
