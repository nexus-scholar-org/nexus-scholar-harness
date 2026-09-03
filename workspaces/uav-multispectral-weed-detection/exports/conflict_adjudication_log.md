# Conflict Adjudication Log

**Project:** uav-multispectral-weed-detection
**Adjudicated:** 2026-09-02
**Adjudicator:** human-in-the-loop (lead researcher) with LLM sub-agent recommendation
**Paradigm:** Design Science

---

## 1. Adjudication Protocol

Conflicts arose at two screening stages. Each conflicted record was resolved against the
protocol's inclusion criteria (INC-01..INC-04) and exclusion criteria (EXC-01..EXC-05):

- **INC-01** Empirical crop/weed segmentation OR detection results reported.
- **INC-02** Multispectral (≥2 bands beyond RGB, incl. NDVI/channel-stack) imagery used.
- **INC-03** UAV or edge-computing deployment context (aerial/onboard).
- **INC-04** Evaluated on or introduces an open/benchmark dataset.
- **EXC-01** Wrong outcome (no segmentation/detection).
- **EXC-02** Satellite-scale only (no UAV/edge context).
- **EXC-03** RGB-only (no spectral advantage).
- **EXC-04** Non-empirical (review/survey without primary experiment).
- **EXC-05** Non-English / inaccessible.

Resolution rule: a paper is INCLUDED iff it satisfied **INC-01 AND INC-02 AND (INC-03 OR INC-04)**
AND violated **no** exclusion criterion, AND passed verification (trust score ≥ 5.0).

---

## 2. Keyword → Conflicts Stage

Keyword screening auto-assigned a tentative verdict to all 116 papers, of which **49** were
flagged "CONFLICT" (conflicting evidence in title/abstract) and routed to review.

- 21 conflicts had tentative **INCLUDE** (spectral + segmentation signals present, low confidence).
- 28 conflicts had tentative **EXCLUDE** (disqualifying phrase present, e.g. RGB-only).

All 49 were escalated to the LLM + human adjudication layer.

---

## 3. LLM Screening Pass

An independent LLM re-screen (8 parallel batches) applied criteria contextually to title +
abstract. Disagreement with the keyword pass was substantial (see §5, Cohen's κ = 0.11),
confirming that keyword-only screening over-recruits.

LLM pass produced 29 conflicts, which were combined with the keyword conflicts for a final
criteria-based review.

---

## 4. Final Adjudicated Decisions (26 INCLUDED / 90 EXCLUDED / 0 conflicts)

### 4.1 INCLUDED (26) — rationale summary

| DOI | 1st author (year) | Primary adjudication rationale |
|-----|-------------------|-------------------------------|
| 10.3390/rs18060915 | Wang (2026) | Benchmark (BAWSeg); MSI UAV; cross-year protocol → INC-01,02,03,04 |
| 10.1109/wacv61041.2025.00467 | Celikkan (2025) | WeedsGalore dataset; MSI + multitemporal; segmentation → INC-01,02,04 |
| 10.2139/ssrn.7345639 | Hernández Ludeña (2026) | MSI UAV few-shot segmentation; empirical → INC-01,02,03 |
| 10.1017/wsc.2023.41 | Cox (2023) | Black-grass cereal MSI detection; empirical → INC-01,02,03 |
| 10.1109/m2garss52314.2022.9839758 | Khoshboresh-Masouleh (2022) | MSI UAV crop/weed meta-learning → INC-01,02,03 |
| 10.3390/plants15152257 | Li (2026) | SCG-UNet soybean MSI segmentation; prescription map → INC-01,02,03/04 |
| 10.1117/1.jrs.15.034510 | Khoshboresh-Masouleh (2021) | MSI sugar-beet UAS weed segmentation → INC-01,02,03 |
| 10.1016/j.neucom.2023.126914 | Castellano (2023) | Lightweight ViT MSI weed mapping; benchmark → INC-01,02,04 |
| 10.1002/ps.70881 | Dong (2026) | ASVLB-Net; NDVI fusion; lightweight; 0.47M params → INC-01,02,03/04 |
| 10.2139/ssrn.7129570 | Wang (2026) | Water-hyacinth MSI UAV monitoring → INC-01,02,03 |
| 10.68099/asnj.2024.79 | Kucharski (2024) | Edge-AI weeding robot; MSI; Jetson → INC-01,02,03 |
| 10.35708/rc1869-126258 | Fawakherji (2020) | Pixel-wise crop/weed segmentation; MSI → INC-01,02,03 |
| 10.1016/j.cropro.2024.106721 | Mesías-Ruiz (2024) | UAV weed species CNN classification → INC-01,02,03 |
| 10.3390/s17092007 | Alexandridis (2017) | Novelty detection MSI UAV weed mapping → INC-01,02,03 |
| 10.3390/rs16183538 | Lauwers (2024) | MSI UAV jimson-weed classification → INC-01,02,03 |
| 10.1007/s11119-017-9558-x | Barrero (2018) | RGB+MSI UAV Gramineae weed fusion → INC-01,02,03 |
| 10.4316/aece.2026.02005 | BOUHADJER (2026) | Dual-branch CNN-transformer MSI U-Net → INC-01,02,03/04 |
| 10.1109/icssit69151.2026.11656575 | Krishna (2026) | WeedFormer transformer UAV segmentation → INC-01,02,03 |
| 10.1007/s11119-017-9528-3 | Louargant (2017) | UAV weed detection spectral-mixing simulation → INC-01,02,03 |
| 10.1007/978-3-032-26214-1_21 | Papadeas (2026) | CLIP+DINOv3 MSI crop/weed segmentation → INC-01,02,04 |
| 10.3390/agronomy11071435 | Che'Ya (2021) | Hyperspectral/MSI optimal UAV weed classification → INC-01,02,03 |
| 10.1016/j.compag.2024.109719 | Guo (2025) | CTFFNet UAV rice-field MSI segmentation → INC-01,02,03 |
| 10.1007/978-3-030-82064-0_2 | Rosas (2022) | Multispectral U-Net crop/weed segmentation → INC-01,02,04 |
| 10.1016/j.robot.2021.103861 | Fawakherji (2021) | MSI image synthesis for crop/weed segmentation → INC-01,02,03/04 |
| 10.3390/ecsa-12-26608 | Arangi (2025) | Federated edge learning MSI weed detection → INC-01,02,03 |
| 10.3390/rs15235615 | Khan (2023) | Drone MSI weed-crop segmentation encoder-decoder → INC-01,02,03/04 |

### 4.2 EXCLUDED (90) — rationale categories (top reasons)

| Exclusion reason | Count |
|------------------|-------|
| EXC-03 RGB-only (no multispectral advantage) | majority |
| EXC-04 non-empirical / review (no primary experiment) | several |
| EXC-02 satellite-scale only (no UAV/edge context) | several |
| EXC-01 wrong outcome (not segmentation/detection) | several |
| EXC-05 non-English / inaccessible full text | few |
| Low trust score (< 5.0) / not verifiable | few |

*(Full per-paper reasons reside in the `screening_reasoning` field of `literature/*.json`.)*

---

## 5. Inter-Annotator Agreement (Step 3)

Cohen's kappa between the **automated keyword screening** (Annotator A) and the **final
adjudicated outcome** (Annotator B, LLM + human) across all **N = 116** papers:

| Metric | Value |
|--------|-------|
| Both INCLUDE | 24 |
| Both EXCLUDE | 26 |
| A INCLUDE / B EXCLUDE (false-positive by keyword) | 64 |
| A EXCLUDE / B INCLUDE (false-negative by keyword) | 2 |
| Observed agreement (pₒ) | 43.1% |
| Expected agreement (pₑ) | 35.7% |
| **Cohen's κ** | **0.115** |
| Landis & Koch interpretation | **Slight** |

**Implication:** keyword-only screening agrees with the final evidence-based verdict only
"slightly" — it over-recruits (64/88 keyword-INCLUDE were subsequently excluded). This
quantitatively justifies the mandatory LLM + human adjudication layer and is a key
methodological finding of the pipeline.

---

## 6. Methodological Notes / Caveats

1. The intermediate standalone-LLM pass (15 INC / 72 EXC / 29 CONFLICT) was not persisted
   separately; the persisted `llm_*.json` reflect the post-adjudication final state. κ above
   therefore compares keyword-screening vs. final-gold-standard outcome.
2. The 2 keyword false-negatives (A EXCLUDE / B INCLUDE) were MSI papers whose abstracts
   lacked explicit spectral keywords — a known keyword-screening failure mode.
3. Absolute agreement metrics, not prevalence-adjusted, reported; the high INCLUDE imbalance
   in the keyword pass inflates the value of the principled κ over raw agreement.
