# Screening Criteria: SSFNet: Lightweight Multispectral UAV Vision Architecture for Real-Time Weed Detection and Precision Targeted Spraying

**Protocol ID**: `proto-20260902-uav-multispectral-weed-detection-v2`
**Lead Researcher**: AI PhD Researcher
**Playbook**: DESIGN_SCIENCE
**Paradigm**: Design Science

## Context & Rationale
**Unit of Analysis**: Multispectral deep learning segmentation architectures and their dual-branch spectral-visible fusion designs evaluated under empirical benchmark quantification

Design Science paradigm with empirical benchmark quantification across open agricultural datasets, requiring reported numeric segmentation accuracy and edge-side efficiency metrics on reproducible benchmarks.

## Research Questions

### RQ1
**Question**: Does a dual-branch spatial-spectral cross-attention architecture (SSFNet) outperform unimodal RGB and channel-stacked early-fusion multi-band baselines in weed-vs-crop segmentation accuracy (mIoU, weed IoU, weed F1) on open agricultural UAV datasets?
- **Required Evidence**: Quantitative Benchmark
- **Synthesis Type**: Comparative Matrix

### RQ2
**Question**: Can the multispectral fusion architecture sustain the real-time targeted-spraying threshold (>=30 FPS on NVIDIA Jetson-class edge) while keeping parameter count under 0.6M, and what is the measured latency (ms), FLOPs, and throughput trade-off against accuracy?
- **Required Evidence**: Latency & Resource Profiling
- **Synthesis Type**: Comparative Matrix

### RQ3
**Question**: How robust is the multispectral weed segmentation model to domain shifts from lighting variation, crop phenological stage, and sensor band calibration when evaluated across multiple agricultural benchmark datasets?
- **Required Evidence**: Generalization Evaluation
- **Synthesis Type**: Comparative Matrix

## Inclusion Criteria

### INC-01
**Criterion**: Reports empirical segmentation, detection, or classification results (numeric mIoU, F1, Precision/Recall, IoU, mAP) specifically for weed-vs-crop discrimination in agricultural imagery.
**Serves**: RQ1, RQ2

### INC-02
**Criterion**: Uses multispectral, hyperspectral, or multi-band aerial imagery (including at least one of NIR, RedEdge, NDVI, NDRE, or vegetation-index fusion) OR explicitly evaluates spectral band fusion against a visible/RGB baseline.
**Serves**: RQ1, RQ3

### INC-03
**Criterion**: Deployment or evaluation context is a UAV / UAS platform, aerial platform, or edge/embedded agricultural hardware; or the study reports edge-side efficiency metrics (latency ms, FPS, GFLOPs, parameter count).
**Serves**: RQ1, RQ2

### INC-04
**Criterion**: Evaluates on an open, public, or specifically identifiable agricultural benchmark dataset (e.g., WeedMap, Agriculture-Vision, SugarBeet2016, DeepWeeds) or a described reproducible experimental dataset with named crop/weed classes.
**Serves**: RQ1, RQ3

## Exclusion Criteria

### EXC-01
**Criterion**: No weed detection/segmentation outcome: studies on pest or disease classification, grain/crop quality grading, or general vegetation mapping without weed-crop discrimination.
**Rejection Reason Code**: `WRONG_OUTCOME`
**Serves**: RQ1

### EXC-02
**Criterion**: Includes only satellite-scale or fixed-wing macro remote sensing without usable UAV-resolution (aerial close-range) weed imagery or edge/embedded context.
**Rejection Reason Code**: `OUT_OF_SCOPE_RESOLUTION`
**Serves**: RQ1

### EXC-03
**Criterion**: Strictly RGB-only vision with no spectral/band-fusion component and no weed-specific segmentation or detection architecture.
**Rejection Reason Code**: `OUT_OF_SCOPE_MODALITY`
**Serves**: RQ1

### EXC-04
**Criterion**: Non-empirical meta-publications: surveys, review letters, position papers, or editorials without algorithmic implementation and benchmark numbers.
**Rejection Reason Code**: `NO_EMPIRICAL_EVALUATION`
**Serves**: RQ1, RQ2

### EXC-05
**Criterion**: Non-English text, unverified abstract-only records, or records lacking retrievable full text for code/data availability verification.
**Rejection Reason Code**: `LANGUAGE_OR_FORMAT`
**Serves**: RQ1, RQ2, RQ3

## Verification Constraints

- [x] Retraction check required
- [x] Conflict of Interest & Funding audit required
- [x] Reproducibility (Data/Code Availability) check required
- Minimum Trust Score: 5.0
