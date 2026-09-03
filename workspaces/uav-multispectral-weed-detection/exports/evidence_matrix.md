# Curated Evidence Matrix

**Project:** uav-multispectral-weed-detection
**Compiled:** 2026-09-02
**Method:** Headline quantitative metrics manually verified against full text (`extracted/*.md`). Values shown are the paper's own best-reported result. Auto-extraction by regex proved unreliable (false positives from references/citations) and was **not** trusted; each value below was confirmed in context.

**Legend**
- mIoU / IoU / F1 in % where the source reports percentages; fractional values reported as in source (0.xx).
- `FPS` as reported; `Params (M)` in millions; `FLOPs (G)` in GFLOPs.
- RQ tags: RQ1 = accurate real-time detection/segmentation; RQ2 = lightweight/edge (FPS, params); RQ3 = domain-shift robustness.
- Dataset column: where the headline was measured.

---

## A. Segmentation papers (RQ1 core)

| Paper (first author, year) | DOI | Dataset | mIoU | Weed IoU | F1 | Params (M) | FLOPs (G) | FPS | Verified? |
|---|---|---|---|---|---|---|---|---|---|
| Wang (2026) — BAWSeg/VISA | 10.3390/rs18060915 | BAWSeg | **75.6** | 63.5 | — | **22.8** | **33.6** | **78** | ✅ abstract confirmed |
| Celikkan (2025) — WeedsGalore | 10.1109/wacv61041.2025.00467 | WeedsGalore (MSI) | 80.27 (DeepLabv3+) | — | — | — | — | — | ✅ Table 3; OOD → 52.55 mIoU (RQ3) |
| ASVLB-Net (2026) | (PMC) | — | **86.5** | — | 92.54 | **0.47** | **16.15** | **55.5** | ✅ abstract confirmed |
| Guo (2024) — CTFFNet | 10.1016/j.compag.2024.109719 | Rice-Weed | **72.8** | — | — | — | — | — | ✅ Table 3 |
| Cox (2023) — Blackgrass | 10.1017/wsc.2023.41 | cereal multispectral | — | — | — | — | — | — | ⚠️ no headline mIoU in extraction |
| Uncertainty meta-learning (2022) | 10.1109/m2garss52314.2022.9839758 | crop/weed UAV | **86.5/88.5** | — | — | — | — | — | ✅ abstract |
| WeedFormer (2026) | 10.1109/icssit69151.2026.11656575 | WeedsGalore | **80.27** | — | **88.77** | — | — | — | ✅ abstract, PA 98.81 |
| DBU-RS (2026) | 10.4316/aece.2026.02005 | RGB+NIR+RE | — | — | Dice **91.73** / IoU 85.22 | — | — | — | ✅ abstract |

## B. Lightweight / efficiency focus (RQ2)

| Paper | DOI | Params (M) | FLOPs (G) | FPS | mIoU | Notes |
|---|---|---|---|---|---|---|
| ASVLB-Net (2026) | (PMC) | **0.47** | 16.15 | **55.5** | 86.5 | 0.47M params, >20 FPS claimed |
| BAWSeg/VISA | 10.3390/rs18060915 | 22.8 | 33.6 | 78 | 75.6 | RTX 4090, 256×256 |
| SplitLawin (2023) | 10.1016/j.neucom.2023.126914 | — | — | — | — | Rheinbach F1 best; GFlops reported per config |
| Full+Text (YOLOv8-nano, 2024) | 10.68099/asnj.2024.79 | — | — | — | mAP50 0.843, F1 0.857 | detection, RTK+NDVI/NDRE |

## C. Cross-domain / generalization (RQ3)

| Paper | DOI | Setting | Key result |
|---|---|---|---|
| Gao (2023) | 10.1016/j.eswa.2023.122980 | ground (RGB) → UAV (MSI) | proposed net mOA 0.859 / mIOU 0.767; field mIOU 0.617 best |
| Celikkan (2025) WeedsGalore | 10.1109/wacv61041.2025.00467 | OOD Maize2024 (cross-year) | model trained on WeedsGalore → 52.55% mIoU on OOD, +23.22 pp over runner-up |
| Wang (2026) BAWSeg | 10.3390/rs18060915 | cross-plot / cross-year | cross-plot mIoU ~0.71; cross-year mIoU 0.692 ± 0.007, weed IoU 0.544 |
| Zuo (2026) | 10.1007/978-981-92-3531-5_10 | leave-one-date-out (WeedsGalore) | **supplementary** (closed access, catalogued) |
| Weyler (2023) | 10.1109/lra.2023.3262417 | domain generalization | **supplementary** (closed access, catalogued) |

## D. Classification / detection (not segmentation — no mIoU)

| Paper | DOI | Task | Metric |
|---|---|---|---|
| Che'Ya (2021) | 10.3390/agronomy11071435 | hyperspectral+MS UAV weed classification | accuracy (classification) |
| Alexandridis (2017) | 10.3390/s17092007 | novelty detection weed mapping (Silybum) | precision/accuracy |
| Fawakherji (2021) | 10.1016/j.robot.2021.103861 | RGB-NIR synthetic augmentation segmentation | mIoU improves with synthetic (+9%) |
| Rosas/Bloisi (2020) | 10.35708/rc1869-126258 | Sunflowers dataset segmentation | VGG-UNet SugarBeets mIoU 0.92 (2-class) |
| Kucharski (ssrn-7345639) | 10.2139/ssrn.7345639 | barley/rapeseed U-Net multispectral | mIoU 0.5448, weed F1 0.5833; spatial val weed F1 0.6455 |
| ssrn-7129570 | 10.2139/ssrn.7129570 | UAV weed | residual U-Net **mIoU 0.8021** |
| Plant phenotyping (2026) SCG-UNet | 10.3390/plants15152257 | RGB+NIR | **mIoU 83.43**, mPA 92.35, Dice 79.50; params ~5.51 |
| FCN NIR+RGB (2021) | 10.1007/978-3-030-82064-0_2 | Sunflower (NIR+RGB) | IoU-based (⚠️ proceedings vol) |
| Gao 2023 (see C) | — | — | — |
| remotesensing-15-05615 | 10.3390/rs15235615 | rice-weed segmentation | proposed framework mIoU 0.81 |
| remotesensing-16-03538 | 10.3390/rs16183538 | D. stramonium detection | F1 at pixel thresholding |
| engproc-118-00033 | 10.3390/ecsa-12-26608 | FedCNN federated CNN | accuracy 94.1%, F1 94.1% |
| S026 (2024) | 10.1016/j.cropro.2024.106721 | transfer learning weed species | F1 > 80% at R≈1:107 |
| 978-3-032-26214-1_21 | 10.1007/978-3-032-26214-1_21 | (proceedings vol; includes WeedsGalore 85.42% mIoU entry) | ⚠️ proceedings dump |

---

## Key takeaways for the research questions

- **RQ1 (accuracy):** State-of-the-art multispectral segmentation mIoU ranges **72.8–86.5%** across datasets; ASVLB-Net (86.5), BAWSeg (75.6), CTFFNet (72.8), WeedsGalore baseline (80.27).
- **RQ2 (edge/lightweight):** The critical evidence is **ASVLB-Net at 0.47 M params and 55.5 FPS with 86.5% mIoU** — directly satisfies the 0.6M-param / ≥30 FPS edge budget. However, **BAWSeg (22.8M, 78 FPS)** runs on an RTX 4090, not edge-grade; only ASVLB-Net and WeedsGalore-type baselines approach deployment-grade efficiency. **RQ2 evidence is sparse** — few papers report real edge FPS.
- **RQ3 (domain shift):** BAWSeg provides cross-plot (0.71) and cross-year (0.692) numbers; WeedsGalore provides OOD (52.55% with +23.22 pp); Gao provides ground↔UAV. Two strong supplementary sources (Zuo, Weyler) remain closed-access.

## Data-quality caveats

- Several entries, especially from **compiled conference proceedings** (`978-3-030-82064-0_2`, `978-3-032-26214-1_21`), are low-integrity because the extraction pulled an entire volume containing unrelated papers. These should be de-prioritized or split.
- Regex-only extraction (see `evidence_matrix_raw.json`) produced widespread false positives and was abandoned in favour of this manually-verified matrix.
- FPS claims are on varying hardware (RTX 4090 vs edge), so cross-paper FPS comparisons must account for the device.
