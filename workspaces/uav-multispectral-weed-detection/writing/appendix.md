# Appendix: PRISMA 2020 Flow, Empirical Benchmark Tables & Evidence Traceability

**Companion Document to:** *Lightweight Multispectral UAV Vision Architecture for Real-Time Weed Detection and Precision Targeted Spraying*  
**Workspace:** `uav-multispectral-weed-detection`  
**Protocol ID:** `proto-20260902-uav-multispectral-weed-detection-v2`  
**Date:** 2026-09-03  

---

## Appendix A: PRISMA 2020 Flow & Screening Breakdown

```
========================================================================================
                                 IDENTIFICATION
========================================================================================
Records identified from multi-provider database search:
  • OpenAlex, Crossref, arXiv (N = 116)
  • Deduplication result: 116 unique records (0 duplicates removed)
                                      │
                                      ▼
========================================================================================
                                   SCREENING
========================================================================================
Records screened via dual automated & LLM-assisted protocol (N = 116)
  • Dual-pass screening agreement: 67 consensus decisions
  • Screening conflicts adjudicated: 49 records
  • Inter-annotator reliability: Cohen's kappa κ = 0.115 (systematic adjudicator reconciliation)

Records excluded after screening (N = 90):
  • E1: Wrong outcome (broad vegetation/crop health, non-weed): 42
  • E2: Satellite / macro-scale (MODIS/Sentinel, spatial res > 0.5m): 18
  • E3: RGB-only (no multispectral/NIR/RedEdge bands evaluated): 21
  • E4: Non-empirical / review / conceptual architecture: 7
  • E5: Non-English publication: 2
                                      │
                                      ▼
========================================================================================
                                   INCLUSION
========================================================================================
Studies meeting formal inclusion criteria (N = 26)
  • Full-text PDFs successfully retrieved and extracted: 25 studies
  • Documented availability gap (closed access / paywalled): 1 study (Barrero et al.)
  • Structural AST chunks indexed in vector store (`uav_msi_weeds`): 1,185 chunks
  • Supplemental hardware & domain-shift benchmarks catalogued:
      - RQ2 Edge Hardware Register: 3 studies (@assuncao-2022-rs14174217, @wang-2026-atech101924, @le-2019-access2911709)
      - RQ3 Domain Shift Register: 3 studies (@2023_gao_crossdomain_transfer_weed_segmentation [ingested], @zuo-2026-cross-date, @weyler-2023-domain-generalization)
========================================================================================
```

---

## Appendix B: Comprehensive Empirical Evidence Table & Citation Token Index

The table below summarizes key empirical studies from the 25-paper corpus, cross-referencing headline metrics against verified atomic citation tokens in the ChromaDB vector collection `uav_msi_weeds`.

| Study / Citation Key | Authors & Year | Architecture | Sensor Bands | Segmentation Accuracy | Edge Throughput & Parameters | Vector Chunk Token |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SCG-UNet** <br>`plants-15-02257-v2` | Wei et al. (2026) | SCG-UNet (Strip-Context Gating) | RGB + NIR (4 bands) | **mIoU: 83.43%** <br>mPA: 92.35% <br>F1: 80.77% | Unspecified edge latency; $+1.50$ pp mIoU over RGB baseline | `chk-1033-9b1e0e-abstract-intro-41` |
| **ASVLB-Net** <br>`10.1002/ps.70881` | Dong et al. (2026) | ASVLB-Net (Adaptive Spatial-Visual) | RGB + NIR + NDVI | **mIoU: 86.5%** | **0.47M params**, **16.15 GFLOPs**, **55.52 FPS** ($512\times 512$), **84.75 FPS** ($224\times 224$) | `chk-1010-3a54df-conclusion-04` |
| **SSRN-7345639** <br>`ssrn-7345639` | Hernández Ludeña et al. (2026) | Multi-scale U-Net / SegNet | RGB + RE + NIR + VIs (8 bands) | Weed F1: **0.5833** <br>Weed IoU: **0.4117** | Few-shot transfer ($63$ patches) restores F1 from $0.0534$ to $0.6274$ | `chk-1021-91498f-abstract-intro-23` |
| **BAWSeg** <br>`remotesensing-18-00915-v2` | Wang et al. (2026) | VISA (ViT-Spatial Attention) | RGB + RE + NIR (5 bands) | **mIoU: 75.6%** <br>Weed IoU: 63.5% | **22.8M params**, **33.6 GFLOPs**, **78.0 FPS** (Desktop RTX 4090) | `chk-1033-c65635-abstract-intro-45` |
| **WeedFormer** <br>`weedformer` | Krishna et al. (2026) | WeedFormer (Transformer) | RGB + NIR (4 bands) | **mIoU: 80.27%** | ViT edge latency reported; $+8.47$ pp gain over SegFormer baseline | `chk-1011-552a0b-abstract-intro-21` |
| **Kucharski et al.** <br>`Full+Text` | Kucharski et al. (2024) | YOLOv8-nano + RT-DETR | RGB + RE + NIR + NDVI | mAP50: **0.843** | Real-time onboard Jetson Orin NX; TensorRT INT8 verified | `chk-1068-09f2e6-abstract-intro-16` |
| **BOUHADJER et al.** <br>`aece_2026_2_5` | Bouhadjer et al. (2026) | Dual-Branch CNN-ViT | RGB + NIR + RE + 5 VIs | **Dice: 91.73%** <br>IoU: 85.22% | Dual-branch spatial/spectral feature separation | `chk-1043-bf41a3-abstract-intro-38` |
| **Gao et al.** <br>`2023_Gao_Transfer` | Gao et al. (2023) | Cross-Domain ResNet-UNet | Ground RGB $\rightarrow$ UAV MSI | **mOA: 0.859** <br>mIoU: 0.767 | Ground-to-air cross-platform domain transfer | `chk-1010-1713c4-abstract-intro-16` |

---

## Appendix C: SSFNet Architectural Parameter Justification

Each structural design choice of SSFNet is traceable directly to an empirical finding from the evidence base:

| Component | Target Value | Empirical Rationale | Supporting Evidence Base |
| :--- | :--- | :--- | :--- |
| **Parameter Budget** | $\le 0.50\text{ M}$ params (0.42M target) | Minimizes SRAM footprint and off-chip memory access on edge boards | ASVLB-Net (`10.1002/ps.70881`: 0.47M params); YOLOv8-nano (`10.68099/asnj.2024.79`) |
| **Computational Complexity** | $\le 15.0\text{ GFLOPs}$ ($512\times 512\times 5$) | Constrains per-frame compute to enable $>50\text{ FPS}$ within 15–20W TDP | ASVLB-Net (16.15 GFLOPs at 512×512 yields 55.5 FPS) |
| **Spectral Gating (ASG)** | 2-band gate ($C_{\text{MSI}}=2$, NIR/RE) | Avoids index feature redundancy (NDVI/NDRE) while retaining narrow-band gains | SCG-UNet (`10.3390/plants15152257`); SSRN-7345639 (`10.2139/ssrn.7345639`) |
| **Feature Normalization (SFSN)**| Shallow instance-whitening | Standardizes low-level activations against diurnal irradiance shifts | Zuo et al. (`10.1007/978-981-92-3531-5_10`); Weyler et al. (`10.1109/lra.2023.3262417`) |
| **Quantization Format** | TensorRT INT8 (PTQ) | Yields up to $14.8\times$ inference speedup with bounded $<15\%$ mIoU cost | Assunção et al. (`10.3390/rs14174217`); Wang et al. (`10.1016/j.atech.2026.101924`) |
