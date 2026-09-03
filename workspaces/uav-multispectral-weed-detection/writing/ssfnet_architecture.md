# SSFNet: Lightweight Spatial-Spectral Fusion Network for Real-Time Edge UAV Weed Segmentation

**Document:** Architecture Specification & Design Science Artifact Formulation  
**Project:** `uav-multispectral-weed-detection`  
**Paradigm:** Design Science Research (DSR)  
**Date:** 2026-09-03  

---

## 1. Architectural Motivation & Empirical Grounding

The design of **SSFNet** directly operationalizes the empirical findings consolidated across the 25-study systematic evidence matrix (`synthesis_matrix.csv`, 80.0% filled) and the grounded literature review (`literature_review.md`):

1. **Grounded in RQ1 (Spectral Fusion over Static Concatenation)**:
   - *Empirical Evidence*: Studies such as SCG-UNet (`10.3390/plants15152257`, +1.50 pp mIoU with RGB+NIR) and ASVLB-Net (`10.1002/ps.70881`, 86.5% mIoU) demonstrate that adding NIR and Red-Edge spectral bands reliably improves crop-weed discrimination. However, static concatenation with derived vegetation indices (NDVI/NDRE) causes feature redundancy and parameter bloat.
   - *SSFNet Mechanism*: A **Dual-Branch Decoupled Backbone** separating visible spatial geometry ($C_{\text{RGB}} = 3$) from narrow-band physiological reflectance ($C_{\text{MSI}} = 2$ [NIR, RedEdge]). Spectral interaction is governed by an **Adaptive Spectral Gate (ASG)** rather than naive channel stacking.

2. **Grounded in RQ2 (Edge Budget & Pareto Frontier)**:
   - *Empirical Evidence*: As documented in the RQ2 Supplemental Register (`rq2_supplemental_register.md`), only sub-1M parameter architectures can maintain $\ge 30\text{ FPS}$ on edge accelerators (NVIDIA Jetson Xavier/Orin NX, Jetson Nano). ASVLB-Net demonstrated that 0.47M parameters and 16.15 GFLOPs can achieve 55.52 FPS at $512 \times 512$, while TensorRT-INT8 quantization (Wang et al., 2026; Assunção et al., 2022) enables real-time onboard flight inference.
   - *SSFNet Mechanism*: SSFNet targets a **$\le 0.50\text{ M}$ parameter ceiling** and **$\le 15.0\text{ GFLOPs}$** at $512 \times 512 \times 5$. It employs reparameterizable depthwise-separable inverted residual blocks (`RepGhost` / `EfficientNeXt`) with INT8-friendly linear activations, eliminating non-quantizable complex operators.

3. **Grounded in RQ3 (Domain-Shift & Phenological Robustness)**:
   - *Empirical Evidence*: In-field domain shifts cause asymmetric performance degradation: temporal cross-year shifts erode weed IoU by 9–15 pp (BAWSeg, `10.3390/rs18060915`), and cross-crop transfers collapse without adaptation (Hernández Ludeña, `10.2139/ssrn.7345639`, dropping to F1 = 0.0534 before few-shot recovery).
   - *SSFNet Mechanism*: Introduction of a **Shallow Feature-Statistics Normalization (SFSN)** layer that standardizes low-level channel style statistics across variable sunlight and phenological growth stages, combined with **Few-Shot Calibration Heads** facilitating on-device fine-tuning with $\le 15\%$ labeled patches.

---

## 2. Structural Architecture

```
                  ┌────────────────────────────────────────────────────────┐
                  │          5-Band UAV Multispectral Input                │
                  │              (H x W x 5: R, G, B, RE, NIR)             │
                  └──────────────────────────┬─────────────────────────────┘
                                             │
                     ┌───────────────────────┴───────────────────────┐
                     ▼                                               ▼
      ┌─────────────────────────────┐                 ┌─────────────────────────────┐
      │     RGB Spatial Stream      │                 │     MSI Spectral Stream     │
      │         (H x W x 3)         │                 │         (H x W x 2)         │
      └──────────────┬──────────────┘                 └──────────────┬──────────────┘
                     │                                               │
      ┌──────────────▼──────────────┐                 ┌──────────────▼──────────────┐
      │  Lightweight Spatial Stage  │                 │ Lightweight Spectral Stage  │
      │   (Rep-Conv, Stride=2)      │                 │   (Depthwise Dilated Conv)  │
      └──────────────┬──────────────┘                 └──────────────┬──────────────┘
                     │                                               │
                     └───────────────────────┬───────────────────────┘
                                             │
                                ┌────────────▼────────────┐
                                │ Adaptive Spectral-      │
                                │ Spatial Attention Gate  │
                                │        (ASG)            │
                                └────────────┬────────────┘
                                             │
                                ┌────────────▼────────────┐
                                │ Shallow Feature-        │
                                │ Statistics Normalization│
                                │        (SFSN)           │
                                └────────────┬────────────┘
                                             │
                                ┌────────────▼────────────┐
                                │ Lightweight Multiscale  │
                                │ Decoder (ASPP-Lite)     │
                                └────────────┬────────────┘
                                             │
                                ┌────────────▼────────────┐
                                │ Pixel-Wise Segmentation │
                                │ (Background / Crop /    │
                                │        Weed)            │
                                └─────────────────────────┘
```

---

## 3. Mathematical Formulation of Core Modules

### 3.1. Adaptive Spectral Gate (ASG)
Let $\mathbf{F}_{\text{RGB}} \in \mathbb{R}^{H \times W \times C}$ denote the high-resolution spatial feature representation, and $\mathbf{F}_{\text{MSI}} \in \mathbb{R}^{H \times W \times C_s}$ denote the spectral reflectance features.

Instead of channel concatenation, the spectral gate computes a cross-channel importance vector $\mathbf{w}_s$:
$$\mathbf{z}_s = \text{GAP}(\mathbf{F}_{\text{MSI}}) = \frac{1}{H \times W} \sum_{i=1}^H \sum_{j=1}^W \mathbf{F}_{\text{MSI}}(i, j)$$
$$\mathbf{w}_s = \sigma\left( \mathbf{W}_2 \cdot \text{ReLU}\left( \mathbf{W}_1 \cdot \mathbf{z}_s \right) \right)$$
where $\sigma(\cdot)$ is the sigmoid activation, and $\mathbf{W}_1, \mathbf{W}_2$ are dimension-reduction linear transformations.

The gated fused representation is then formed via residual modulation:
$$\mathbf{F}_{\text{Fused}} = \mathbf{F}_{\text{RGB}} + \mathbf{F}_{\text{RGB}} \odot (\mathbf{w}_s \otimes \mathbf{1}_{H \times W}) + \text{PWConv}(\mathbf{F}_{\text{MSI}})$$
This ensures that spectral bands enhance boundaries and suppress chlorophyll-free soil artifacts without altering learned RGB spatial primitives.

### 3.2. Shallow Feature-Statistics Normalization (SFSN)
To guard against irradiance fluctuations and sensor gain shifts (RQ3), SFSN aligns intermediate feature representations to canonical distribution statistics:
$$\hat{\mathbf{F}}(c) = \frac{\mathbf{F}(c) - \mu_c}{\sqrt{\sigma_c^2 + \epsilon}} \cdot \gamma_c + \beta_c$$
where $\mu_c$ and $\sigma_c$ are channel-wise batch instance statistics, and $\gamma_c, \beta_c$ are learnable affine parameters initialized to preserve scale.

---

## 4. Hardware Deployment & Quantization Pipeline

1. **Target Hardware**: NVIDIA Jetson Orin NX (16GB, 20W TDP) or Jetson Xavier NX (15W TDP).
2. **Precision**: INT8 post-training quantization (PTQ) via NVIDIA TensorRT 10.x.
3. **Target Metrics**:
   - Total Parameters: **0.42 M**
   - FLOPs: **12.8 GFLOPs** (at $512 \times 512 \times 5$)
   - Inference Latency: **< 16.0 ms ( $\ge 62\text{ FPS}$ )** on Jetson Orin NX (TensorRT INT8)
   - Segmentation Performance: **$\ge 82.0\%\text{ mIoU}$** across standard benchmark datasets (WeedsGalore, WeedMap).
