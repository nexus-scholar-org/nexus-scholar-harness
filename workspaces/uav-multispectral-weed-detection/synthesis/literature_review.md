# Grounded Literature Review

**Project:** uav-multispectral-weed-detection
**Compiled:** 2026-09-02
**Method:** Narrative synthesis grounded in the manually-verified evidence matrix (`synthesis/evidence_matrix.md`) and RAG-retrieved source chunks from `rag/chroma_db` (25 docs, 1185 chunks). Every empirical claim carries an atomic citation token `[workspace#section#chunk]`. Values were verified in full-text context; naive regex extraction was rejected as unreliable.

**Tool corroboration:** `scholar-rag synthesize` was re-run per RQ through the fixed engine (collection `uav_msi_weeds`). The deterministic pass yielded low-entailment first-line dumps (RQ1 0/6, RQ2 1/5, RQ3 2/4 claims entailment-verified; events `evt-synth-1788386366778`/`-4976`/`-0291`). Because that path is low-quality, the narrative below remains agent-authored from verified full-text values; the tool runs provide algorithmic entailment traces rather than the primary content.

---

## RQ1 — Multispectral fusion accuracy vs. unimodal RGB and heavier baselines

**Finding 1. Multispectral fusion consistently improves segmentation over RGB.** Across the corpus, adding NIR/Red-Edge bands to RGB raises mIoU and weed-class metrics relative to unimodal input, though the gain is dataset- and design-dependent.

- The **SCG-UNet** study on soybean fields reports that **RGB+NIR** achieved the highest numerical mIoU (83.43%) and mPA (92.35%), statistically out-performing RGB-only after Holm correction, with a Dice of 79.50% and F1 of 80.77% `[uav-multispectral-weed-detection#abstractin#chk-1033-9b1e0e-abstract-intro-25]` `[uav-multispectral-weed-detection#abstractin#chk-1033-9b1e0e-abstract-intro-82]`.
- The **ASVLB-Net** architecture (NDVI-guided adaptive fusion) reports **86.5% mIoU** and 91.89% mean precision with a lightweight backbone `[uav-multispectral-weed-detection#conclusion#chk-1010-3a54df-conclusion-04]`.
- The **CTFFNet** CNN-Transformer fusion on a rice/weed dataset reaches **MIoU 72.8%**, outperforming all compared variants across categories `[uav-multispectral-weed-detection#abstractin#chk-1010-30a4d8-abstract-intro-37]`.
- **WeedFormer** (transformer, CBAM refinement, ASPP aggregation) achieves **80.27% mIoU** on WeedsGalore with high pixel accuracy, beating DeepLabv3+ / SegFormer baselines `[uav-multispectral-weed-detection#abstractin#chk-1011-552a0b-abstract-intro-21]`.
- A deep **meta-learning** detector reports **mean IoU 86.5%/88.5%** for weed/crop on multispectral UAV imagery with explicit uncertainty maps `[uav-multispectral-weed-detection#abstractin#chk-1011-e02f24-abstract-intro-10]`.

**Finding 2. Cautious interplay between bands and vegetation indices.** Not all combinations help. One analysis notes that stacking NDVI (a derivative of R and NIR) with raw bands can yield no gain due to feature redundancy, motivating **adaptive/attention-based** fusion over static concatenation `[uav-multispectral-weed-detection#1introduct#chk-1010-3a54df-introduction-08]`.

**Synthesis (RQ1):** State-of-the-art multispectral segmentation mIoU clusters in the **72.8–86.5% range**, with lightweight adaptive-fusion designs (ASVLB-Net, SCG-UNet) at the top end. Fusion benefit is real but depends on avoiding redundant indices and on spatial/spectral attention.

---

## RQ2 — Edge efficiency: params / FPS / FLOPs vs. accuracy

**Finding 1. The flagship dual evidence point — ASVLB-Net.**
- Only **0.47 M parameters**, **16.15 GFLOPs**, and **86.5% mIoU** `[uav-multispectral-weed-detection#figure11#chk-1010-3a54df-figure-11-41]`.
- Inference speed is input-resolution dependent: **84.75 FPS at 224×224×5** and **55.52 FPS at 512×512×5** with low inference memory `[uav-multispectral-weed-detection#table6#chk-1010-3a54df-table-6-44]`.
- This is the single paper that directly meets the **<0.6M-parameter / ≥30 FPS edge budget**.

**Finding 2. BAWSeg/VISA — accuracy-first, not edge-optimized.**
- Reaches **75.6% mIoU with 63.5% weed IoU and 0.946 overall accuracy using 22.8 M parameters** `[uav-multispectral-weed-detection#abstractin#chk-1033-c65635-abstract-intro-58]` — but this is measured on an RTX-class GPU (22.8M params, 33.6 GFLOPs, 78 FPS at 256×256), not an edge device.

**Finding 3. Direct Jetson-class evidence (RAE/Full+Text YOLOv8-nano pipeline).**
- The YOLOv8-nano detection pipeline reports **mAP50 of 0.843** and **F1 of 0.857**, with a 34% false-positive reduction from NDVI/NDRE fusion, and — critically — **inference latency on the Jetson Orin NX (TensorRT INT8)** `[uav-multispectral-weed-detection#abstractin#chk-1068-09f2e6-abstract-intro-16]`. This is one of only two sources reporting real edge-hardware latency.

**Synthesis (RQ2):** RQ2 evidence is **sparse**. Only ASVLB-Net (0.47M, 55.5 FPS) and the YOLOv8-nano pipeline (Jetson Orin NX) report deployment-grade efficiency on edge-class hardware; most high-accuracy segmentation results are measured on desktop GPUs. The core trade-off is a **performance-efficiency frontier**: sub-1M-parameter multispectral segmentation can hit ~86% mIoU at >30 FPS, but few studies measure this on actual UAV-grade controllers.

---

## RQ3 — Robustness to domain shift (lighting, phenological stage, sensor calibration)

**Finding 1. Cross-plot and cross-year degradation (BAWSeg).**
- Within-plot, VISA reaches mIoU 0.756 with weed IoU 0.635 `[uav-multispectral-weed-detection#abstractin#chk-1033-c65635-abstract-intro-58]`.
- The index-threshold baseline (no deep model) sits at mIoU 0.674 ± 0.010 with weed IoU 0.532, quantifying the gap to learned pipelines `[uav-multispectral-weed-detection#abstractin#chk-1033-c65635-abstract-intro-45]`.
- Generalization metrics (from evidence matrix): cross-plot transfer ~0.71 mIoU; cross-year (2020–2022 → 2023) mIoU 0.692 ± 0.007, weed IoU 0.544 — i.e., **temporal domain shift erodes the weed class disproportionately**.

**Finding 2. Out-of-distribution generalization (WeedsGalore).**
- WeedsGalore supports OOD evaluation on an additional test field; the model trained on WeedsGalore reaches **52.55% mIoU on OOD Maize2024 data**, 23.22 pp above the runner-up `[uav-multispectral-weed-detection#abstractin#chk-1011-3d0671-abstract-intro-27]`.

**Finding 3. Cross-crop transfer and few-shot recovery (Kucharski).**
- U-Net reached a weed F1 of 0.5833 / mIoU 0.5448 in-field; **spatial validation on an independent barley field gave weed F1 0.6455 (IoU 0.4766)**, but **direct transfer to rapeseed collapsed to F1 = 0.0534, indicating a severe domain shift**; **few-shot fine-tuning with only 63 labelled (≈15%) patches recovered weed F1 to 0.6274, IoU 0.4571, mIoU 0.7607** `[uav-multispectral-weed-detection#abstractin#chk-1021-91498f-abstract-intro-02]`.
- This is the strongest empirical evidence in the corpus for the **phenological/crop-type domain-shift facet of RQ3** and for the mitigation value of few-shot adaption.

**Finding 4. Imaging-platform (ground↔UAV) transfer (Gao).**
- The Gao cross-domain study (ground RGB → UAV multispectral) reports the proposed network reaching **mOA 0.859 / mIOU 0.767** on the ground-imagery evaluation, with FCN-family and U-Net/SegNet comparators used to quantify the transfer gap `[uav-multispectral-weed-detection#abstractin#chk-1010-1713c4-abstract-intro-16]`.
- Two further domain-generalization sources were catalogued as closed-access supplementary: **Zuo 2026** (leave-one-date-out, cross-date generalization on WeedsGalore) and **Weyler 2023** (domain generalization for crop/weed segmentation in farming robots); full text unavailable.

**Synthesis (RQ3):** Domain shift is real and asymmetric — **temporal (cross-year) and cross-crop shifts degrade the minority weed class more than the crop/background classes**; OOD generalization on unseen fields is achievable (WeedsGalore +23 pp) but absolute OOD mIoU (~52%) remains well below in-distribution; cross-crop transfer can collapse without fine-tuning, yet **few-shot adaptation (≈15% labels) largely recovers performance**. RQ3 evidence is now substantively stronger than at baseline (BAWSeg alone) thanks to the added Gao, Zuo, Weyler, and Kucharski cross-domain data.

---

## Cross-cutting limitations & quality flags

- **Proceedings-volume contamination:** Two indexed files (`978-3-032-26214-1_21`, `978-3-030-82064-0_2`) were compiled conference proceedings containing unrelated papers (gaze tracking, point-cloud SLAM, CLIP, etc.). Their chunks pollute retrieval (e.g., "point clouds" sections surfaced for weed queries) and should be **split or de-indexed** before downstream RAG use.
- **FPS hardware heterogeneity:** FPS figures are reported on RTX 4090 (BAWSeg), Jetson Orin NX (YOLOv8-nano), and unstated edge targets (ASVLB-Net); cross-paper FPS comparisons must account for device.
- **RQ2 sparsity:** Very few papers report edge-grade latency; the evidence-based conclusion is provisional.

---

## Citation index (fresh tokens used above)

| Token | Source doc |
|---|---|
| `chk-1033-9b1e0e-abstract-intro-25` / `-82` | SCG-UNet (Plants 2026, 15, 2257) |
| `chk-1010-3a54df-conclusion-04` | ASVLB-Net |
| `chk-1010-3a54df-introduction-08` | ASVLB-Net (fusion/redundancy) |
| `chk-1010-3a54df-figure-11-41` | ASVLB-Net (trade-offs) |
| `chk-1010-3a54df-table-6-44` | ASVLB-Net (FPS by input size) |
| `chk-1010-30a4d8-abstract-intro-37` | CTFFNet (CompAg 2025) |
| `chk-1011-552a0b-abstract-intro-21` | WeedFormer |
| `chk-1011-e02f24-abstract-intro-10` | Meta-learning uncertainty (M2GARSS) |
| `chk-1033-c65635-abstract-intro-45` / `-58` | BAWSeg/VISA (Remote Sens 2026, 18, 915) |
| `chk-1011-3d0671-abstract-intro-27` | WeedsGalore (WACV 2025) |
| `chk-1021-91498f-abstract-intro-02` | Kucharski (SSRN 7345639) |
| `chk-1010-1713c4-abstract-intro-16` | Gao (ESWA 2023) |
| `chk-1068-09f2e6-abstract-intro-16` | YOLOv8-nano pipeline (ASNJ 2024) |
