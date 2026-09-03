# Screening Criteria: UAV Computer Vision for Precision Agriculture: Deep Learning Segmentation & Edge Inference Benchmark Review

**Protocol ID**: `proto-20260903-uav-cv-precision-agriculture`
**Lead Researcher**: AI Agent
**Playbook**: PRISMA_SLR
**Paradigm**: Positivist

## Context & Rationale
**Unit of Analysis**: Edge-deployed deep learning segmentation models for agricultural UAV imagery

Positivist empirical benchmark synthesis. Evaluates comparative pixel-wise segmentation accuracy (mIoU/F1) across architectural paradigms (CNNs, Transformers, Hybrids) using paired within-study comparisons and standard benchmarks, while quantifying hardware constraint trade-offs (FPS, latency, power) across edge computing devices.

## Research Questions

### RQ1
**Question**: What is the comparative segmentation performance (mIoU, F1-score) of CNNs, Transformers, and Hybrid architectures on agricultural UAV crop-weed imagery, specifically in paired intra-study benchmarks?
- **Required Evidence**: Quantitative Benchmark
- **Synthesis Type**: Comparative Matrix

### RQ2
**Question**: How do edge hardware constraints (thermal design power, compute capacity in TOPS) and execution configurations (quantization precision, input resolution) impact real-time inference throughput (FPS, latency) for UAV segmentation models?
- **Required Evidence**: Quantitative Benchmark
- **Synthesis Type**: Comparative Matrix

## Inclusion Criteria

### INC-01
**Criterion**: Focuses on deep learning architectures (CNN, Transformer, or Hybrid) applied to UAV aerial imagery for agricultural crop/weed pixel-level segmentation.
**Serves**: RQ1, RQ2

### INC-02
**Criterion**: Reports quantitative pixel-wise segmentation accuracy metrics (e.g., mIoU, class IoU, Dice/F1-score) on agricultural benchmark or custom UAV datasets.
**Serves**: RQ1

### INC-03
**Criterion**: Reports on-device empirical hardware execution metrics (e.g., FPS, latency in ms, power in Watts, memory footprint) on physical edge platforms or embedded accelerators.
**Serves**: RQ2

## Exclusion Criteria

### EXC-01
**Criterion**: Non-UAV imaging modalities (satellite-only, ground-vehicle/tractor-only, or laboratory bench-top setups without aerial flight context).
**Rejection Reason Code**: `OUT_OF_SCOPE_MODALITY`
**Serves**: RQ1, RQ2

### EXC-02
**Criterion**: Bounding-box object detection or whole-image classification without pixel-level semantic or instance segmentation masks.
**Rejection Reason Code**: `OUT_OF_SCOPE_TASK`
**Serves**: RQ1

### EXC-03
**Criterion**: Agricultural domains outside crop and weed management (e.g., orchard fruit counting, forestry canopy height, livestock tracking, soil moisture estimation).
**Rejection Reason Code**: `OUT_OF_SCOPE_DOMAIN`
**Serves**: RQ1, RQ2

### EXC-04
**Criterion**: Exclusively non-deep learning methods (e.g., classical vegetation indices like ExG/NDVI with Otsu thresholding or shallow SVM without learned features).
**Rejection Reason Code**: `METHODOLOGICAL_MISMATCH`
**Serves**: RQ1

### EXC-05
**Criterion**: Secondary literature without primary empirical benchmarks (surveys, systematic reviews, viewpoint letters, or tutorials).
**Rejection Reason Code**: `SECONDARY_LITERATURE`
**Serves**: RQ1, RQ2

### EXC-06
**Criterion**: Non-English text or records lacking retrievable quantitative results.
**Rejection Reason Code**: `INSUFFICIENT_DATA`
**Serves**: RQ1, RQ2

## Verification Constraints

- [x] Retraction check required
- [x] Conflict of Interest & Funding audit required
- [x] Reproducibility (Data/Code Availability) check required
- Minimum Trust Score: 6.0
