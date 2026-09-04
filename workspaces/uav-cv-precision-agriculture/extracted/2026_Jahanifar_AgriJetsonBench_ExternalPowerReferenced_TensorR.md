---
workspace_id: SCI-000810
title: 'AgriJetsonBench: External-Power-Referenced TensorRT Benchmarking of Agricultural
  Vision Models on Jetson Edge Platforms'
authors:
- family_name: Jahanifar
  given_name: Hasan
  orcid: null
- family_name: Mirzakhaninafchi
  given_name: Hasan
  orcid: null
- family_name: Porter
  given_name: Wesley M.
  orcid: null
- family_name: Najar
  given_name: Abolfazl
  orcid: https://orcid.org/0000-0003-4299-5766
- family_name: Rains
  given_name: Glen C.
  orcid: https://orcid.org/0000-0002-2497-5422
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T01:48:55.364722+00:00'
---

# AgriJetsonBench: External-Power-Referenced TensorRT Benchmarking of Agricultural Vision Models on Jetson Edge Platforms

AgriJetsonBench: External-Power-Referenced TensorRT Benchmarking of Agricultural

Vision Models on Jetson Edge Platforms

Hasan Jahanifara,∗, Hasan Mirzakhaninafchia, Wesley M. Porterb, Abolfazl Najarc, Glen C. Rainsa,b

aCollege of Engineering, University of Georgia, Tifton, GA 31793, USA bCollege of Agricultural and Environmental Sciences, University of Georgia, Tifton, GA 31793, USA

cCollege of Engineering, University of Georgia, Athens, GA 30602, USA


## Abstract

Agricultural vision models are often selected from validation accuracy and reported frames per second, but deployment on embedded agricultural edge-GPU systems also depends on timing boundary, numeric precision, power mode, board-input energy, and sustained- run validity. We present AgriJetsonBench, a reproducible deployment benchmark for crop/weed detection and segmentation on NVIDIA Jetson AGX Orin 64GB and Jetson Orin Nano Super. Existing locked agricultural datasets were used as fixed deployment workloads, and seven model families were exported through ONNX and TensorRT. The benchmark combines pure TensorRT engine timing, external board-input power logging, internal Jetson telemetry, battery-continuation testing, run-validity screening, and archived reproducibility artifacts. Main energy tests used YOLO11s and SegFormer-B0 at batch size 1 and 640 × 640. Under matched 15 W INT8 operation, Orin Nano Super outperformed AGX Orin on both workloads: YOLO11s reached 145.82 FPS and 0.0767 J/inference versus 80.90 FPS and 0.1814 J/inference, and SegFormer-B0 reached 47.18 FPS and 0.2808 J/inference versus 31.95 FPS and 0.5013 J/inference. In native SegFormer-B0 FP16 operation, AGX Orin achieved higher throughput and lower p95 latency than Nano Super, 103.61 FPS and 9.441 ms versus 67.47 FPS and 15.020 ms, with similar energy per inference. Time-aligned analysis of 76,691 internal–external power samples showed high temporal association but a pooled internal-minus-external bias of −1.988 W. The results show that agricultural Jetson deployment decisions should be based on workload, precision, power mode, and measurement boundary rather than board class alone.

arXiv:2608.00927v1  [cs.PF]  2 Aug 2026

Keywords: Precision agriculture, Edge computing, Machine vision, NVIDIA Jetson, Energy measurement, Benchmarking, TensorRT


## 1. Introduction

common deep-learning frameworks and TensorRT optimiza- tion tools NVIDIA (2024b, 2026a). However, selecting a Jet- son platform and an agricultural vision model is not a simple accuracy-ranking problem. In field deployment, a model that performs well on a validation set may still be unsuitable if it has high latency, high tail latency, high memory pressure, exces- sive board-input power, or poor battery endurance. Conversely, a lightweight model may be attractive for a battery-powered system even if it is not the absolute accuracy leader. These trade- offs make agricultural edge-AI deployment a multi-objective decision problem.

Artificial intelligence is increasingly central to precision agriculture, where field decisions often depend on timely inter- pretation of visual data from cameras, robots, mobile platforms, and distributed sensing systems. Agricultural computer-vision models are now used for tasks such as weed detection, crop monitoring, disease assessment, livestock monitoring, yield esti- mation, and robotic perception Liakos et al. (2018); Kamilaris and Prenafeta-Boldú (2018); Shamshiri et al. (2018). In many of these applications, inference cannot rely exclusively on cloud computing because field connectivity may be limited, communi- cation latency can be unacceptable, and raw image transmission may increase bandwidth, cost, and energy demand. Edge AI therefore has an important role in agricultural systems that re- quire local autonomy, low latency, and energy-aware operation.

Recent agricultural edge-AI studies show that embedded inference is practical for detection, segmentation, monitoring, and robotic perception tasks Dang et al. (2023); Chamara et al. (2023); Gao et al. (2023); Zhang and Lv (2024); Islam et al. (2025); Wang et al. (2026). However, the reported deployment evidence remains difficult to compare across papers. FPS values often omit the timing boundary, power values may not specify whether they come from external board-input logging or internal telemetry, and platform comparisons rarely separate matched nominal-power operation from board-native high-performance operation. As a result, a validation-accuracy result cannot be re- liably translated into a battery-aware Jetson deployment choice.

NVIDIA Jetson platforms are widely used for agricultural edge-AI prototyping because they provide GPU acceleration, embedded deployment support, and software compatibility with

∗Corresponding author

Email addresses: hjahanifar@uga.edu (Hasan Jahanifar), hasan.mirzakhaninafchi@uga.edu (Hasan Mirzakhaninafchi), wporter@uga.edu (Wesley M. Porter), najar@uga.edu (Abolfazl Najar), grains@uga.edu (Glen C. Rains)

The overall AgriJetsonBench workflow is summarized in Fig. 1. In the workflow diagram, green boxes denote offline/pre-

AgriJetsonBench workflow

Reproducible training-to-deployment benchmark for agricultural edge AI on NVIDIA Jetson platforms

1

2

3

4

Deployment artifact generation

Jetson deployment benchmarking

Offline training and validation

Locked agricultural datasets

• Checkpoint → ONNX → TensorRT • FP32, FP16, INT8 engines • 640 input + resolution ablation

• Sapelo2 GPU training environment • 7 model families trained and tested • Detection and segmentation backbones

• CottonWeedDet12_v1 detection • CropAndWeed_v1 segmentation • Locked splits, labels, licenses

• AGX Orin 64GB and Orin Nano Super • Matched-budget: 15 W vs 15 W • Native modes: 50 W vs 25 W, batch 1

8

7

6

5

Deployment decision output • Cross-board deployment guidance • Nano Super: matched-budget INT8 • AGX Orin: native high-load FP16

Analysis and metrics

Battery continuation protocol • Power-bank window: 100% → 20% • Clean manual stop at 20% • Latency, temperature, events captured

Dual-source power measurement • External board-input logger • Internal Jetson telemetry in parallel • External/internal agreement analysis

• Accuracy, complexity, latency, FPS • J/inference, inferences/Wh, J/GMAC • Pareto, Bland–Altman, energy model

Main benchmark principle Board choice depends on workload complexity, precision, power mode, and timing boundary—not board class alone.


> **Figure 1: AgriJetsonBench workflow. Green boxes indicate offline/pre-deployment stages, including dataset locking, model training, and deployment-artifact**

> generation. Blue boxes indicate Jetson deployment, dual-source power measurement, battery continuation, analysis, and deployment-decision stages. Agricultural
detection and segmentation datasets were locked and split, models were trained and validated offline, deployment artefacts were exported to ONNX and TensorRT, and
Jetson inference was evaluated using external board-input power logging, internal telemetry, battery continuation tests, model-complexity analysis, and deployment
decision mapping.

deployment stages and blue boxes denote Jetson deployment, measurement, analysis, and decision stages.

logging can provide a more direct board-input reference when it is inserted before the device power input Texas Instruments (2026). For deployment studies, the most useful approach is to record both channels: external board-input logging as the primary energy reference and internal telemetry as a diagnostic and agreement-analysis channel. This dual-source design helps distinguish true board-input energy from internal rail estimates and enables transparent reporting of bias between the two. The same concern appears in broader embedded-ML benchmarking, where accuracy, latency, energy, hardware configuration, and measurement stack must be reported together for interpretable comparison (Banbury et al., 2021). It is also consistent with Green AI arguments that predictive performance should be re- ported alongside computational cost rather than treated as the only optimization target (Schwartz et al., 2020).


> **Table 1 summarizes this deployment-evidence gap for closely**

> related agricultural edge-AI studies. The table is not intended
as a ranking; it records whether each study reports the specific
evidence needed for reproducible, energy-aware Jetson compari-
son.

This gap matters because edge-AI deployment decisions are affected by interactions among model architecture, input size, precision mode, batch size, power mode, and measurement boundary. A model may be efficient in INT8 at a matched 15 W budget but less favourable in FP16 native mode. A larger board may appear inefficient when underutilized in low-power batch-1 inference, but may become favourable when a heavier workload exposes its native compute capacity. Similarly, a reported energy value is difficult to compare unless the measurement boundary is explicit and the energy source is clearly defined. For this reason, agricultural edge-AI benchmarks need to report not only accuracy and FPS, but also external board-input power, energy per inference, compute-normalized energy, thermal behaviour, run validity, and reproducibility evidence.

Another source of ambiguity is the timing boundary. End- to-end image-pipeline measurements include image loading, decoding, preprocessing, postprocessing, non-maximum sup- pression, mask decoding, visualization, and storage overhead. These measurements are useful for complete application profil- ing, but they should not be mixed with pure inference-engine measurements. TensorRT pure-engine benchmarking isolates the optimized model execution path and supports controlled comparison across models, precisions, power modes, and Jet- son platforms. Therefore, a reproducible benchmark should state whether it reports TensorRT engine-level inference, full image-pipeline inference, or both.

Power measurement is a particularly important source of am- biguity. Jetson devices provide internal telemetry that is useful for diagnostics, temperature monitoring, and rail-level trends NVIDIA (2026c, 2024a). However, internal telemetry does not necessarily equal total board-input energy, and rail coverage can differ by device and operating state. External inline power

2


> **Table 1: Gap mapping of closely related agricultural edge-AI studies.**

Study Agricultural task Jetson / multi-board

Sustained / thermal

Numeric precision / quantization

Power or energy Boundary

Primary emphasis

Reproducibility assets

stated

Not reported Code + dataset YOLO detector and dataset benchmark for multi-class cotton weed detection. AICropCAM (Chamara et al., 2023)

YOLOWeeds (Dang et al., 2023)

Cotton weed detection

No Jetson comparison

Not reported as deployment precision axis

Not reported Model benchmark

No; Raspberry Pi / Arduino system

Not reported as deployment precision axis

System power reported; no J/inference

Application pipeline

Not thermal; field-oriented platform

Partial Integrated edge camera system with speed and power reporting.

Crop monitoring: classification, segmentation, detection, counting

RTAL (Gao et al., 2023)

Not reported Real-time UAV edge-computing method for large-area rice lodging mapping.

Rice lodging area assessment

Single Jetson Xavier NX

Not reported as deployment precision axis

Not reported UAV area-throughput pipeline

Partial sortie-scale runtime; no thermal/power trace

Not reported Model / device FPS

Partial; pruning / quantization, no FP32/FP16/INT8 energy protocol

TinySegformer (Zhang and Lv, 2024)

Not reported Not reported Lightweight segmentation architecture with pruning/quantization for edge devices. Islam et al. (Islam et al., 2025)

Agricultural pest segmentation

Single Jetson deployment context

Not reported Application- level edge FPS

Not reported Data on request Real-time lightweight CNN

Not reported as deployment precision axis

Partial; Jetson Nano and Orin Nano deployments

Weed detection and segmentation

workflow for weed detection and segmentation on edge devices. Wang et al. (Wang et al., 2026)

Not reported Code + dataset Multi-platform livestock pose benchmark with deployability metrics. This work Crop/weed detection and segmentation

Partial; GPU / Jetson / CPU platforms

Not reported Latency, FPS, memory, model size

Not reported as deployment precision axis

Livestock keypoint detection

Yes; AGX Orin and Orin Nano Super

FP32, FP16, and INT8 TensorRT where calibration succeeded

External board-input J/inference and inferences/Wh

Battery continuation, temperature, events, idle baselines

Tables, figures, scripts, manifests, checksums, logger traces, telemetry

Unified matched-budget and native-mode Jetson benchmark for agricultural deployment decisions.

Pure TensorRT engine-level and supplementary end-to-end evidence

Note. “Numeric precision / quantization” refers to numeric deployment precision or quantization as an explicit benchmark axis, not the detection/segmentation precision metric. “Partial” means that the dimension is addressed in some form, but not as part of a unified, externally checked, dual-source, matched-budget agricultural Jetson benchmark protocol with explicit timing and board-input energy boundaries. “Not reported” means the dimension was not explicitly reported as a benchmark output in the cited study.

To address these needs, we developed AgriJetsonBench, a deployment-measurement benchmark for agricultural vision models on Jetson edge-AI platforms that links model complexity, TensorRT execution, and externally logged board-input energy. The benchmark connects offline model development to deploy- ment measurement. It uses locked agricultural detection and segmentation datasets, trains and validates representative model families, exports deployment artifacts to ONNX and TensorRT, evaluates inference on two Jetson platforms, records external and internal power channels, performs power-bank continuation tests, and reports deployment decisions using latency, through- put, energy, model complexity, and run-validity metrics.

The deployment study uses two Jetson boards: NVIDIA Jetson AGX Orin 64GB and NVIDIA Jetson Orin Nano Super. Two comparison views are separated throughout the paper. The matched-budget view compares AGX Orin 15 W against Nano Super 15 W. This view asks which board is preferable when both devices operate under the same nominal power class. The native/high-performance view compares AGX Orin 50 W against Nano Super 25 W. This view asks what each board can deliver in its practical high-performance mode. Keeping these views separate avoids overinterpreting either nominal-power fairness or board-native maximum performance.

The main latency and energy results are reported using a pure TensorRT engine-level boundary at batch size 1. This boundary was selected because the target use case is online agricultural inference, where frames arrive sequentially from cameras or field platforms and per-frame latency is deployment-relevant. Under this boundary, the reported energy metrics are J/inference, inferences/Wh, and Wh/1000 inferences. End-to-end image- pipeline evidence is retained only as supplementary context and is not mixed with the main TensorRT energy comparisons.

The benchmark evaluates two agricultural vision tasks: ob- ject detection and semantic segmentation. Detection models were trained on the locked CottonWeedDet12_v1 dataset, and segmentation models were trained on the locked CropAndWeed_v1 dataset Weed-AI (2023); Steininger et al. (2023). The retained model set covered three detection models and four segmentation models; Section 2.4 lists the individual architectures and their deployment roles. All accepted models were trained, validated, exported, and archived before Jetson deployment. Because this study uses existing agricultural image datasets, these datasets are treated as fixed deployment workloads for benchmarking rather than as newly collected agronomic datasets. The primary con- tribution is the externally referenced deployment-measurement protocol and measurement-boundary analysis for agricultural edge-computing systems.

The main contributions of this paper are as follows: 1. We define AgriJetsonBench, a training-to-deployment bench- mark protocol for agricultural vision models that couples locked datasets, TensorRT deployment, external board-input power logging, internal telemetry, run-validity screening, and reproducibility packaging.


## 2. We quantify accuracy, model complexity, artifact footprint,

3


> **Table 2: Locked datasets and split sizes used in AgriJetsonBench.**

TensorRT latency, throughput, external energy per inference, inferences/Wh, and J/GMAC for representative detection and segmentation model families.

Dataset Task Train Val Test Test annotations

CottonWeedDet12_v1 Detection 3,972 564 1,112 1,886 boxes CropAndWeed_v1 Segmentation 5,381 798 1,526 1,526 masks


## 3. We separate two deployment questions that are often con-

flated: matched-budget operation, where AGX Orin and
Orin Nano Super are compared at 15 W, and native/high-
performance operation, where each board is evaluated in its
practical high-performance mode.

The primary latency, throughput, and energy results use a pure TensorRT engine-level timing boundary. Unless explicitly stated otherwise, one “inference” refers to one batch-1 TensorRT engine invocation at the configured input size. The timed region excludes JPEG/image loading, dataset file I/O, CPU-side pre- processing, image resizing outside the engine, postprocessing, non-maximum suppression, mask decoding outside the engine, visualization, and prediction saving. Therefore, the main energy metrics are reported as J/inference, inferences/Wh, and Wh/1000 inferences, rather than end-to-end J/image.


## 4. We provide an artifact package containing split files, train-

ing metrics, model manifests, hardware/software metadata,
power logs, telemetry, run-validity summaries, tables, figures,
scripts, and SHA256 checksum manifests.

The results show that the deployment winner is not fixed by board class. In matched-budget 15 W INT8 operation, Nano Su- per outperformed AGX Orin for both YOLO11s and SegFormer- B0. In native high-load SegFormer-B0 FP16 operation, AGX Orin delivered substantially higher throughput and lower la- tency while maintaining comparable energy per inference and compute-normalized energy. A native RT-DETR-R18 FP16 con- trast case further shows that model architecture can change the energy ranking. Together, these findings support a practical deployment rule: board choice in agricultural edge AI should depend on workload complexity, precision, power mode, and measurement boundary, not on hardware class alone.

Two comparison views were used. The matched-budget view compares Jetson AGX Orin in 15 W mode with Jetson Orin Nano Super in 15 W mode. The native/high-performance view compares Jetson AGX Orin in 50 W mode with Jetson Orin Nano Super in 25 W mode. This separation prevents fair nominal-power comparison from being conflated with the prac- tical question of what each board provides in its board-native high-performance mode.

2.2. Datasets and locked splits Two agricultural vision tasks were evaluated: weed/crop ob- ject detection and crop/weed semantic segmentation. The detec- tion task used the locked CottonWeedDet12_v1 dataset. The segmentation task used the locked CropAndWeed_v1 dataset.

The remainder of this paper is organized as follows. Sec- tion 2 describes the datasets, model training, complexity profil- ing, Jetson hardware, TensorRT deployment, external and inter- nal power measurement, battery continuation protocol, and en- ergy metrics. Section 3 presents training outcomes, complexity– accuracy analysis, locked-640 benchmark results, battery contin- uation results, internal–external power agreement, idle baselines, and deployment decision guidance. Section 4 discusses the im- plications for agricultural edge-AI deployment, measurement validity, limitations, and future extensions. The final sections summarize the conclusions and describe data, code, and repro- ducibility availability.

The detection split contained 3,972 training images, 564 val- idation images, and 1,112 test images. The corresponding num- bers of bounding boxes were 6,576, 908, and 1,886. The class list was frozen in the dataset package through class_names.txt, class_names.json, and the locked dataset YAML file.

The segmentation dataset contained three semantic classes:

0 : background, 1 : crop, 2 : weed.


## 2. Materials and methods

The locked segmentation split contained 5,381 training images, 798 validation images, and 1,526 test images. The segmentation test package preserved paired image and mask lists, benchmark- order files, split metadata, class names, and dataset license notes.

2.1. Study overview and benchmark design We developed AgriJetsonBench, a reproducible AI deploy- ment benchmark for precision-agriculture vision models on NVIDIA Jetson edge platforms. The benchmark was designed to evaluate trained agricultural object-detection and semantic- segmentation models not only by predictive accuracy, but also by deployment-relevant behaviour: TensorRT latency, through- put, model complexity, board-input power, energy per inference, battery endurance, internal telemetry, thermal response, and run validity.

Dataset split files, class names, split policies, license notes, and runtime manifests were stored in the reproducibility package under raw_evidence/dataset_splits. Raw images were not redistributed when dataset licenses restrict redistribution. The Jetson deployment tables can be recomputed from the archived engine metadata, run logs, latency files, and external power traces, whereas independent retraining requires access to the original datasets through their source providers.

The experimental workflow followed the stages introduced in Fig. 1: dataset locking and split packaging, offline model training and validation, ONNX export and TensorRT engine generation, Jetson pure-engine benchmarking, and energy-aware deployment analysis.

2.3. Offline training and validation workflow Model training and validation were performed offline on the Sapelo2 GPU environment operated by the Georgia Advanced Computing Resource Center at the University of Georgia (Geor- gia Advanced Computing Resource Center, 2026). The Jetson

4

2.5. Model complexity profiling Model complexity was reported alongside accuracy and de- ployment metrics. For each retained model, we recorded param- eter count, MACs at 640 × 640, GMACs, GFLOPs-equivalent values under the convention 1 MAC = 2 FLOPs, checkpoint size, and ONNX artifact size. The complexity reference input was:

boards were used for deployment benchmarking and energy measurement, not for training. The training workflow followed the same high-level structure for all model families: 1. prepare locked dataset splits and runtime manifests;


## 2. run a smoke-training check where applicable;


## 3. perform hyperparameter tuning where applicable;

batch size = 1, input tensor = 1 × 3 × 640 × 640.


## 4. train the full model;


> **Table 3 lists the complexity values used for all complexity-**

> normalized metrics. These values were used to compute GMAC/s
and J/GMAC:


## 5. validate on the validation split;


## 6. evaluate on the held-out test split;

GMAC/s = Cm × FPS, (1)


## 7. export the accepted model to ONNX;

J/GMAC = J/inference

, (2)


## 8. archive metrics, manifests, checksums, and selected qualita-

tive outputs.

Cm

where Cm is the model complexity in GMACs per 640 inference.

The detection models were YOLO11n, YOLO11s, and RT- DETR-R18. The YOLO models were trained using the Ultr- alytics training stack with Optuna tuning (Akiba et al., 2019). The RT-DETR model used a separate RT-DETR training and export workflow. The segmentation models were BiSeNetV2, MobileNetV3-LRASPP, DeepLabV3+, and SegFormer-B0. Seg- mentation training used the locked three-class crop/weed dataset.

Model complexity was used for interpretation and normal- ized metrics, not as a substitute for measured deployment perfor- mance. TensorRT kernel fusion, precision mode, memory band- width, clock policy, and board power management can change the relationship between theoretical MACs and measured latency or energy.

Training evidence was collected in a metrics-only archive and a figures-only archive. The metrics archive included fi- nal summaries, validation and test metrics, training arguments, tuning reports, ONNX export reports, output manifests, source snapshots, and SHA256 checksums. The figures archive in- cluded selected training curves, confusion matrices, precision– recall curves, per-class plots, and validation batch visualizations. Heavy model weights and raw datasets were not required for manuscript-level tables, but model files were tracked by path, size, and SHA256 hash.

2.6. Jetson hardware platforms Two NVIDIA Jetson development kits were used: • NVIDIA Jetson AGX Orin 64GB Developer Kit;

• NVIDIA Jetson Orin Nano Super Developer Kit. The AGX Orin was treated as the higher-performance edge platform, and the Orin Nano Super as the lower-power edge platform. Two deployment views were defined as follows:

View AGX Orin Nano Super

matched-budget 15 W 15 W native/high-performance 50 W 25 W

2.4. Model set

The benchmark retained seven trained model families span- ning lightweight detection, larger detection, lightweight segmen- tation, conventional CNN segmentation, and transformer-style segmentation: • YOLO11n and YOLO11s for YOLO-family object detection;

Power-mode IDs and mode names were confirmed before experiments using:

sudo nvpmodel -q sudo nvpmodel -q –verbose

• RT-DETR-R18 for non-YOLO detection;

The exact software stack, JetPack/L4T version, CUDA version, TensorRT version, Python package versions, active nvpmodel mode, and clock policy were recorded in hardware/software metadata tables. Optional Nano MAXN_SUPER evidence was not merged into the main native comparison; if included, it is treated only as supplementary ceiling evidence.

• BiSeNetV2 and MobileNetV3-LRASPP for lightweight se- mantic segmentation;

• DeepLabV3+ for heavier CNN-based segmentation;

• SegFormer-B0 for transformer-style semantic segmentation. The main cross-board battery analysis focuses on YOLO11s and SegFormer-B0. YOLO11s represents a practical lightweight detector, while SegFormer-B0 represents a higher-load segmen- tation workload with strong predictive accuracy. RT-DETR-R18 is retained as a native-mode contrast case because it shows that board ranking can change with model architecture. BiSeNetV2 is included in the input-resolution ablation as a lightweight seg- mentation representative.

2.7. Model export and TensorRT deployment Each accepted trained model was exported through the fol- lowing deployment path:

trained checkpoint

↓ ONNX export

↓ TensorRT engine

↓ Jetson benchmark

5


> **Table 3: Model complexity and artifact footprint at 640 × 640.**

Model Task Parameters MACs at 640 GMACs GFLOPs equiv. Artifact footprint

YOLO11n Detection 2.63 M 3.76 × 109 3.76 7.53 checkpoint 5.2 MiB; ONNX 10.1 MiB YOLO11s Detection 9.46 M 1.18 × 1010 11.81 23.61 checkpoint 18.3 MiB; ONNX 36.2 MiB RT-DETR-R18 Detection 20.02 M 3.08 × 1010 30.82 61.63 checkpoint 307.5 MiB; ONNX 76.6 MiB BiSeNetV2 Segmentation 3.33 M 1.92 × 1010 19.23 38.47 checkpoint 39.9 MiB; ONNX 12.8 MiB MobileNetV3-LRASPP Segmentation 3.21 M 3.25 × 109 3.25 6.50 checkpoint 24.8 MiB; ONNX 12.3 MiB DeepLabV3+ Segmentation 40.32 M 1.08 × 1011 108.37 216.74 checkpoint 326.2 MiB; ONNX 153.8 MiB SegFormer-B0 Segmentation 3.71 M 1.48 × 1010 14.84 29.67 checkpoint 42.7 MiB; ONNX 14.3 MiB

For each model, input size, precision, and batch-size configu- ration, a separate TensorRT engine was generated. Static engines were not reused across input resolutions. The evaluated preci- sion modes were FP32, FP16, and TensorRT INT8 build mode. FP32 served as a reference precision where supported, and FP16 represented the main optimized deployment reference. INT8 cal- ibration was input-size-specific; a 640 calibration cache was not reused for other resolutions. For the main 640 cross-board en- gines used in the battery-energy comparison, each INT8 engine used 256 calibration images recorded in the corresponding local calibration manifest. Calibration-cache paths, TensorRT build commands/logs, engine metadata, engine SHA256 checksums, evaluator commands, and metric JSON files were archived with the corresponding run evidence.

pure-engine measurements when the timed region contained only batch-1 TensorRT inference. When random-input timing was used, it was interpreted only as TensorRT engine-execution tim- ing and energy; predictive accuracy was taken from the locked validation and test evaluations, not from random-input runs. End-to-end image-pipeline runs were archived as supplementary evidence, but they were not mixed with the main pure-engine tables because they measure a different boundary.

2.9. Locked 640 benchmark matrix The main benchmark matrix was locked at an input size of 640 × 640 and batch size 1. Batch size 1 was selected because the target deployment scenario is online agricultural inference, such as frame-by-frame processing from a camera mounted on a field robot, mobile inspection platform, or edge sensor node. This setting preserves directly interpretable per-frame median and p95 latency.

INT8 accuracy retention was checked for the main 640 cross- board engines, namely YOLO11s and SegFormer-B0 on AGX Orin and Orin Nano Super, against the corresponding FP16 TensorRT engine on the same board, input size, and batch-size configuration. For YOLO11s detection, INT8 was accepted when the absolute drops in COCO mAP50–95, mAP50, and AR100 were each no greater than 0.03 and no important class AP collapse was observed. The TensorRT COCO evaluator did not emit a standalone scalar precision value, so scalar precision was not used as a retention criterion. For SegFormer-B0 seg- mentation, INT8 was accepted when the absolute drops in mIoU and Dice were no greater than 0.05, crop and weed IoU drops were no greater than 0.10, and no foreground class collapsed. SegFormer-B0 INT8 engines allowed TensorRT FP16 fallback where required by the builder. This retention check is scoped to the main 640 cross-board INT8 engines and is not claimed as an exhaustive retention evaluation for every supplementary INT8 engine or resolution-ablation output.

The locked 640 matrix included all seven model families and up to three precision modes. AGX locked-640 results included matched 15 W and native 50 W modes. Nano Super locked-640 and battery evidence was merged into the cross-board paper tables where available. Each row recorded model, task, board, power mode, precision, input size, timing boundary, latency, FPS, external power, energy, memory, temperature, and run- validity fields.

2.10. Input-resolution ablation

Input-resolution experiments were performed as a supporting ablation, not as a replacement for the locked 640 matrix. The ablation identified: • S min: the smallest accuracy-preserving input size;

• S max: the largest memory-safe common native input size across both Jetson boards.

2.8. Primary timing boundary

The primary benchmark boundary was pure TensorRT engine- level inference. The timed region excluded: • JPEG/image loading and dataset file I/O;

For detection, candidate sizes were:

320, 416, 512, 640, 768, 896, 1024, 1280, 1536.

• CPU-side preprocessing and normalization;

For segmentation, candidate sizes were:

• postprocessing and non-maximum suppression;

256, 320, 384, 448, 512, 576, 640, 704, 768, 896, 1024, 1152.

• mask decoding outside the engine;

The 640 FP16 result was used as the reference. A smaller detection size was accepted only if the absolute drops in mAP50- 95, mAP50, and recall were each no greater than 0.03, and no important class suffered a large AP collapse. A smaller segmentation size was accepted only if mIoU and Dice dropped

• visualization and prediction saving;

• framework-specific per-image path overhead. Pure-engine timing used either trtexec_random_input or a preloaded TensorRT engine runner. Both were accepted as

6

mA, respectively; across loaded steps, the maximum absolute power difference was 0.354 W, corresponding to 0.533% of the reference power at the worst step. Linear voltage and current correction models were archived as characterization evidence, while the manuscript energy tables use the external logger traces consistently across all benchmark configurations.

by no more than 0.05 absolute, crop and weed IoU did not drop by more than 0.10 absolute, and no foreground class collapsed.

Maximum-size discovery used FP16 and the native/high- performance mode of each board: AGX 50 W and Nano Super 25 W. A large size was retained as S max only if it was memory- safe on both boards under these native modes. A large size passed only if the TensorRT engine built successfully, a short smoke run passed, no CUDA OOM occurred, no Linux OOM- killer event was observed, swap use remained zero or negligible, and peak RAM stayed below the safe memory threshold. Se- lected sizes were then confirmed with matched 15 W smoke tests.

Thus, the measurement hierarchy was:

external inline logger = primary board-input energy reference,

internal Jetson telemetry = diagnostic and agreement-analysis channel.

The external logger recorded raw voltage, current, and power samples at approximately 10 Hz. This raw external logger stream was the source for board-input energy integration. For internal– external agreement analysis only, external and internal power were converted to a separate paired 1 Hz overlap table; this table is not the raw external sampling rate. The power-bank display was used only to define the battery stop point; it was not used to compute energy. Figure 2 summarizes the measurement topology.

The full official resolution-power ablation was restricted to four representative models: YOLO11s, RT-DETR-R18, BiSeNetV2, and SegFormer-B0.

2.11. External power measurement topology

A central methodological feature of AgriJetsonBench is dual- source power measurement. The external inline logger measured board-input voltage, current, and power before the Jetson input and was treated as the primary energy reference. Internal Jetson telemetry was recorded in parallel but used only as a diagnostic and agreement-analysis channel.

2.12. Internal telemetry Internal telemetry was collected using Jetson-native moni- toring outputs, including tegrastats-derived power, temperature, memory, process, and rail-level information where available. The internal telemetry stream was used to estimate maximum in- ternal temperature, memory pressure, and internal power trends, and to quantify agreement with the external logger.

The upstream power-source stage was board- and run-type- specific. For adapter-powered runs, the original board-compatible power adapters or sources were used upstream of the external logger. The AGX Orin adapter/source path was routed through a 20 V USB-C PD trigger before entering the external logger. The Orin Nano Super adapter/direct-input path was routed upstream of the same external logger without a PD trigger, because the Nano Super input path did not require a separate PD trigger un- der that setup. For power-bank continuation tests, the upstream source was the UGREEN 25,000 mAh 145 W USB-C PD power bank; because the power-bank output was USB-C PD, a 20 V PD trigger was used upstream of the external logger whenever needed to provide the board-compatible DC input, including Nano Super power-bank runs. In all cases, the selected board- input source was routed through the external INA260 logger immediately before the Jetson board input.

Internal telemetry was not treated as the primary energy source because rail coverage and aggregation differ across boards and operating modes. Instead, the measurement hierarchy was:

external logger = primary board-input energy reference,

internal telemetry = diagnostic and agreement-analysis channel.

2.13. Battery continuation protocol Long-duration battery continuation tests were used to eval- uate sustained deployment behaviour under a field-like energy source. Each main battery run followed the same procedure: 1. charge the UGREEN power bank to 100%;

The external logging assembly used an INA260 inline power sensor for board-input voltage, current, and power measurement and a TMP119 sensor for local temperature monitoring. Both sensors were read by an Adafruit QT Py RP2040 over I2C and streamed to the logger PC over USB serial. The logger PC also maintained a LAN/Ethernet connection to the Jetson for run control and log transfer; this LAN link was not used for energy integration.


## 2. connect the board-specific power-source path through the

external logger;


## 3. boot the Jetson from the power bank;


## 4. confirm the active nvpmodel mode;

The INA260 external logger was checked using a Chroma 62150H-600 programmable DC power supply and a Chroma 63804 programmable AC/DC electronic load. The test matrix included no-load voltage checks at 5, 12, 20, and 30 V, followed by constant-current load points from approximately 0.28 to 4.03 A near the Jetson input-voltage range. Each step was logged for 30 s through the same INA260–QT Py RP2040 USB-serial path used for benchmark logging. Across step means, the maximum absolute voltage and current differences were 57.9 mV and 7.40


## 5. confirm that the external logger reports the expected board-

input voltage and nonzero power;


## 6. start internal telemetry logging;


## 7. enter the noise-guard screening context where supported;


## 8. start the pure-engine TensorRT benchmark;

9. continue until the power-bank display reaches 20% remain- ing;

7

External power and sensor logging topology for Jetson platforms

Jetson board under test one board connected per run

AGX Orin 64GB

or Orin Nano Super

AGX 20 V USB-C

USB-C PD trigger

Jetson AGX Orin 64GB

PD source

20 V output INA260 power sensor inline V/I/P measurement

⚡

+

Jetson DC input board input + / GND Nano 19 V DC barrel

-

source selected

per run

power source

Nano Super direct DC source

compatible DC input path

no PD trigger

⚡

Jetson Orin Nano Super

Legend

board-input power path

common ground

I2C bus, SDA/SCL

3V sensor power

USB serial to logger

LAN/Ethernet control/log transfer

QT Py RP2040 I²C–USB logger

TMP119 temperature sensor

Logger PC USB serial logging

I²C / STEMMA QT


> **Figure 2: External power and sensor logging topology for the Jetson AGX Orin and Jetson Orin Nano Super platforms. The upstream power-source stage differed by**

> board and run type: AGX Orin adapter/source runs used a 20 V USB-C PD trigger before the external logger, Nano Super adapter/direct-input runs used a compatible
direct input path without a PD trigger, and USB-C power-bank continuation runs used a 20 V PD trigger where required by the power-bank source. In all cases, the
INA260 inline sensor measured board-input voltage, current, and power immediately before the Jetson board input. The Adafruit QT Py RP2040 read the INA260 and
TMP119 sensors over I2C and streamed records to the logger PC over USB serial. The dashed LAN/Ethernet link was used only for Jetson run control and log
transfer, not for energy integration.

• SegFormer-B0 FP16, 640, AGX 50 W and Nano Super 25 W.

10. stop the run cleanly using manual Ctrl-C;

11. restore the noise-guard context after the run where applicable;

2.14. Noise-guard screening and run validity criteria Deployment runs used a best-effort noise-guard screening context when supported by the run scripts. The guard was de- signed to reduce common non-benchmark background activity while preserving the external logger/dashboard route. In the safe profile, it could disable Wi-Fi when the logger route did not require it, block Bluetooth, blank the local display, stop selected background services such as package update and discovery ser- vices, and then restore the prior state after the run. The guard wrote JSON summaries for enter and restore actions; these sum- maries were treated as diagnostic evidence and were not used to compute latency or energy. Noise-guard screening was used together with the validity checks below to exclude or flag runs affected by benchmark failures or unstable measurement condi- tions.

12. save summaries, latency files, event records, noise-guard summaries, sanitized run-validity summaries, external logger archives, internal telemetry, and stop annotations.

Because the UGREEN power bank output was USB-C PD, a 20 V PD trigger was used upstream of the external logger when needed to provide the board-compatible DC input for the power- bank continuation runs, including the Nano Super power-bank runs. The PD trigger was part of the power-bank input path and not part of the energy computation; all energy values were computed from the external logger.

All main battery continuation tests covered the displayed 100% to 20% power-bank state-of-charge window and were stopped at 20% remaining. This display window was used only as a standardized stop condition; runs were not allowed to continue to power-bank cutoff or Jetson reboot. The standardized stop reason was:

A benchmark run was considered valid only if all required configuration and measurement conditions were satisfied: • the intended board and nvpmodel mode were confirmed;

manual_ctrl_c_power_bank_80_percent_used_ 20_percent_remaining

• the intended model, precision, input size, and batch size were used;

The main continuation configurations were: • YOLO11s INT8, 640, AGX 15 W and Nano Super 15 W;

• the timing boundary matched the planned pure-engine or sup- plementary boundary;

• SegFormer-B0 INT8, 640, AGX 15 W and Nano Super 15 W;

8

• the external logger was active and external energy was inte- grable;

Throughput was calculated as:

FPS = N t1 −t0

. (8)

• external voltage was recorded throughout each run and checked for consistency with the board-compatible upstream source path described in Section 2.11; no main battery-continuation run was excluded for a voltage-validity failure;

When both full-logger and inference-aligned energy win- dows were available, the inference-aligned external energy win- dow was used for the main normalized metrics. Full-logger energy was retained only for sensitivity and traceability.

• logger gaps greater than 1 s were counted and reported; the six main battery-continuation runs had zero such gaps;

2.16. Internal–external power agreement analysis For agreement analysis only, the external logger trace and internal telemetry stream were aligned over overlapping times- tamp intervals using the archived paper-analysis workflow in scripts/build_agreement_figures_and_decision_m ap.py. External logger power and internal telemetry power were resampled to a common 1 Hz UTC timeline using mean power within each 1 s bin. The final agreement table was created by joining the external and internal 1 Hz series on matching timestamps within the overlapping run intervals, and rows were retained only for bins where both external and internal power val- ues were available. This produced the archived paper_tables /internal_external_time_aligned_samples_1hz.csv

• noise-guard summaries did not report fatal guard errors where the guard was used;

• run-validity summaries and diagnostic status records did not indicate benchmark failure;

• failed inference count was zero;

• no unexpected reboot, OOM event, or overtemperature shut- down occurred;

• battery tests used the standardized 100% to 20% stop rule;

• alarm events were saved and reported transparently. Non-fatal current or high-power alarms did not automatically invalidate a run if the benchmark completed cleanly, external energy was valid, no overtemperature event occurred, and no benchmark failure was present. Such runs were reported as valid with diagnostic warnings. Among the six main battery- continuation runs, the Nano Super native 25 W SegFormer-B0 FP16 run was the one reported with current/high-power diagnos- tic warnings. For that run, the archived diagnostic thresholds were 1.25 A for overcurrent warning, 1.50 A for overcurrent critical, 25.0 W for high-power warning, and 30.0 W for high- power critical. These flags were used to annotate the run and did not by themselves invalidate it.

table with 76,691 paired 1 Hz overlap samples across the six main battery-continuation runs. The table was used to charac- terize internal–external bias and temporal association; the main energy metrics remained based on the raw external logger power trace and the corresponding logger or inference-aligned energy window described in Section 2.15.

For each aligned sample i, the difference was:

di = Pinternal,i −Pexternal,i. (9)

Bias, mean absolute error, and root mean square error were computed as:

2.15. Measured energy integration External board-input energy was calculated from the exter- nal logger power trace. Let Pext(t) denote external board-input power in watts and N the number of timed TensorRT inferences. The external logger energy window, EWh, expressed in watt- hours, was computed as:

n X

bias = 1

di, (10)

n

i=1

n X

MAE = 1

|di|, (11)

n

i=1

v t

n X

Z t1

1 n

EWh = 1 3600

d2

RMSE =

i . (12)

Pext(t) dt. (3)

i=1

t0

Pearson and Spearman correlations were also computed. Bland–Altman limits of agreement were calculated as:

For discrete logger samples:

K X

EWh ≈ 1 3600

LoA = d ± 1.96sd, (13)

Pi∆ti. (4)

i=1

where d is the mean difference and sd is the standard deviation of the differences. The agreement analysis was used to characterize internal telemetry bias and variability; it did not replace external board-input energy in the main results.

The main energy-normalized metrics were:

J/inference = 3600EWh

N , (5)

inferences/Wh = N EWh

, (6)

Wh/1000 inferences = 1000EWh

N . (7)

9

2.17. Idle baselines Four short idle baseline runs were collected to estimate board/mode baseline external power P0: • AGX 15 W idle;

2.19. Statistical and reporting conventions

For short repeated benchmark runs, latency was summarized using median and p95 latency, and throughput and power were summarized using average values across repeats where avail- able. For long battery continuation runs, each run represented a sustained deployment trial from 100% to 20% power-bank state of charge and was reported descriptively using total inferences, elapsed time, FPS, latency, external energy, average and peak external power, J/inference, inferences/Wh, Wh/1000 inferences, maximum internal temperature, alarm status, and validity status.

• AGX 50 W idle;

• Nano Super 15 W idle;

• Nano Super 25 W idle. Each idle run used the same external logger and board- specific upstream power-source logic described in Sec- tion 2.11. Adapter-powered idle runs used the board-compatible adapter/source path upstream of the external logger; power-bank- specific PD triggering was used only when the upstream source required it. After setting the target nvpmodel mode and allowing a settling period, a 5-minute idle window was recorded with external logger and internal telemetry active. No TensorRT in- ference, Python benchmark, file copy, package installation, or model workload was allowed during the idle window.

The final interpretation used Pareto-style and deployment- decision views rather than a single accuracy-only leaderboard. Configurations were compared by accuracy, FPS, latency, J/inference, J/GMAC, thermal stability, and power-mode context.

2.20. Reproducibility package All evidence was archived in AgriJetsonBench_v1. The package includes: • dataset split files, class names, and license notes;

The external average power during the idle window was used as P0,b,r for board b and mode r in the empirical energy model.

• training summaries, validation/test metrics, training repro- ducibility summaries, and artifact manifests;

2.18. Complexity-aware empirical energy model A complexity-aware empirical energy model was used to interpret deployment behaviour beyond raw FPS and J/inference. For model m at input size S , complexity was represented as:

• model complexity summaries at 640;

• Jetson hardware/software version outputs;

• TensorRT engine metadata and model artifact manifests;

 S

qm

• battery run summaries, latency CSV files, event records, noise- guard summaries, sanitized run-validity summaries, and ex- ternal logger archives;

Cm(S ) = Cm,640

, (14)

640

where Cm(S ) is GMACs per inference, Cm,640 is the measured GMACs at 640, and qm is an empirical input-scaling exponent. For the main locked 640 analysis, Cm(S ) = Cm,640.

• internal telemetry logs and time-aligned internal–external agreement tables;

The compute rate was:

• idle baseline summaries;

R = Cm(S ) × FPS, (15)

• energy-model validation tables;

• paper figures, supplementary tables, scripts, and manifest files.

with units GMAC/s. External power was modeled as:

ˆPext = P0,b,r + ηb,r,pR, (16)

Each run was assigned a unique run ID and a paper-use category indicating whether it belonged to the main matched- budget results, the main native-mode results, a supplementary contrast case, or a supplementary non-comparable boundary case. Package-level manifests and SHA256 checksums were used to make the benchmark auditable and to support indepen- dent re-analysis of the reported tables.

where P0,b,r is the idle baseline power for board b and mode r, and ηb,r,p is an empirical dynamic energy slope for board b, mode r, and precision p.

The predicted energy per inference was:

ˆPext FPS = P0,b,r

ˆJinf =

FPS + ηb,r,pCm(S ). (17)


## 3. Results

This expression separates amortized platform overhead from workload-dependent compute energy. The term P0/FPS be- comes large when a board is underutilized or constrained by a low-power mode, while ηCm represents the workload-dependent energy component. The model was used as an interpretive de- ployment estimator; all primary energy values were measured directly from the external logger.

3.1. Training, validation, and export outcomes All seven target model families were successfully trained, validated, exported, and archived before Jetson deployment. The detection models were trained on CottonWeedDet12_v1, and the segmentation models were trained on CropAndWeed_v1. Table 4 summarizes the main validation and test metrics.

For object detection, YOLO11n and YOLO11s achieved similar test accuracy, with mAP50-95 values of 0.9035 and

10

0.9019, respectively. RT-DETR-R18 achieved a lower but still competitive test mAP50-95 of 0.8740, with COCO-style test AR@100 of 0.961. For semantic segmentation, SegFormer- B0 achieved the strongest predictive performance, with test mIoU of 0.8049, test Dice of 0.8854, and foreground mIoU of 0.7115. DeepLabV3+ followed with test mIoU of 0.7774, while MobileNetV3-LRASPP and BiSeNetV2 achieved 0.7631 and 0.7278, respectively. All retained models had traceable training and export ev- idence. For each model, the paper package includes a final summary, validation/test metrics, an exported ONNX model, checkpoint and ONNX SHA256 values, output manifests, and model artifact manifests. YOLO11n and YOLO11s each in- cluded six artifact manifest files; RT-DETR-R18 and the segmen- tation models included output manifests and checksum evidence. The ONNX export status was recorded as exported for all seven models.

Model complexity and predictive accuracy at 640

YOLO11n YOLO11s

0.900

Primary test accuracy (mAP50-95 or mIoU)

RT-DETR-R18

0.875

0.850

0.825

SegFormer-B0

0.800

DeepLabV3+

0.775

MobileNetV3-LRASPP

0.750

Task Detection Segmentation

BiSeNetV2

0.725

101 102

Model complexity at 640 (GMACs per inference, log scale)


> **Figure 3: Model complexity versus primary test accuracy. Detection models**

> are evaluated using mAP50-95 and segmentation models using mIoU. The plot
shows that parameter count and GMACs alone do not determine predictive
performance, motivating joint accuracy–complexity–energy analysis.

3.2. Model complexity versus predictive accuracy The retained models covered a wide complexity range. MobileNetV3-LRASPP and YOLO11n were the smallest mod- els by GMACs, at 3.25 and 3.76 GMACs per 640 inference, respectively. DeepLabV3+ was the largest model, with 108.37 GMACs and a 153.84 MiB ONNX artifact. RT-DETR-R18 was the largest detection model by checkpoint size and required 30.82 GMACs per 640 inference. SegFormer-B0 had only 3.71 M parameters, but required 14.84 GMACs, making it a moderate- parameter but computationally meaningful segmentation work- load.

3.4. Input-resolution ablation The input-resolution ablation remained separate from the locked 640 benchmark matrix. Table 7 summarizes the se- lected input sizes for the four representative ablation models. YOLO11s accepted a smaller accuracy-preserving size of 416

and scaled up to 1536. BiSeNetV2 accepted a smaller size of 448 and scaled up to 1152. RT-DETR-R18 and SegFormer-B0 re- mained at 640 under the predefined accuracy and memory-safety rules.


> **Figure 3 compares model complexity with primary test accu-**

> racy. The result shows that the most computationally expensive
model was not necessarily the most accurate. DeepLabV3+ re-
quired much higher computation than SegFormer-B0 but did not
exceed it in segmentation mIoU. Similarly, RT-DETR-R18 re-
quired more GMACs than YOLO11s but had lower test mAP50-
95. This motivated the use of deployment-aware metrics rather
than accuracy-only model ranking.

For the selected AGX native 50 W power runs, the best energy-throughput combinations were obtained with INT8 at the accepted sizes. YOLO11s INT8 at 416 achieved 518.33 FPS and 0.0435 J/inference. BiSeNetV2 INT8 at 448 achieved 212.05 FPS and 0.0870 J/inference. RT-DETR-R18 INT8 at 640 achieved 164.61 FPS and 0.1735 J/inference. SegFormer- B0 INT8 at 640 achieved 156.19 FPS and 0.2110 J/inference. Therefore, smaller input sizes improved deployment efficiency for some models, but the benefit was model-dependent rather than universal.

3.3. Locked 640 benchmark matrix on AGX Orin

The locked 640 AGX benchmark matrix contained 45 rows across seven model folders: DeepLabV3+, MobileNetV3-LRASPP, BiSeNetV2, RT-DETR-R18, SegFormer-B0, YOLO11n, and YOLO11s. The matrix included FP16, FP32, and INT8 preci-

3.5. Battery continuation run validity All six main battery continuation runs were valid under the final paper criteria. Each used a pure-engine timing boundary, had external logger coverage, had zero logger gaps greater than 1 s, had available external energy, had no failed inferences, no reboot, no OOM, and no overtemperature event. All were reported using the final standardized stop reason:

sions where supported, with matched 15 W and native 50 W AGX power tags.


> **Table 6 summarizes the best AGX locked-640 pure-engine**

> result per model group. INT8 was the fastest and most energy-
efficient precision for all seven AGX model groups. YOLO11n
INT8 achieved the lowest energy per inference, 0.0431 J/inference,
while DeepLabV3+ INT8 remained the most expensive of the
listed INT8 configurations at 0.2369 J/inference. These results
show that precision optimization can substantially affect deploy-
ment efficiency, but the best deployment choice still depends on
task, accuracy, model complexity, and board operating mode.

manual_ctrl_c_power_bank_80_percent_used_ 20_percent_remaining

The Nano Super native 25 W SegFormer-B0 FP16 run was the only main battery-continuation run reported with current/high- power diagnostic warnings. It recorded 7663 external overcurrent- warning hits at the 1.25 A warning threshold and 8013 high- power-warning hits at the 25.0 W warning threshold. However, the archived run-validation summary indicated no error-channel

11


> **Table 4: Training and held-out test accuracy for the retained models. Detection models are reported using AP/mAP metrics; YOLO rows also include scalar precision**

> and recall from the retained evaluation summaries, while RT-DETR-R18 includes COCO-style AR@100 where available. Segmentation models are reported using
mIoU, Dice, foreground mIoU, crop IoU, and weed IoU.

Model Task Dataset Val primary Test primary Test mAP50 Test AR100 Precision Recall Test Dice FG mIoU Crop IoU Weed IoU GMACs

YOLO11n Detection CottonWeedDet12 0.9298 0.9035 0.9573 – 0.9474 0.9091 – – – – 3.76 YOLO11s Detection CottonWeedDet12 0.9303 0.9019 0.9591 – 0.9593 0.9069 – – – – 11.81 RT-DETR-R18 Detection CottonWeedDet12 0.9180 0.8740 0.9290 0.961 – – – – – – 30.82 BiSeNetV2 Segmentation CropAndWeed 0.6785 0.7278 – – – – 0.8291 0.5972 0.6486 0.5457 19.23 MobileNetV3-LRASPP Segmentation CropAndWeed 0.7431 0.7631 – – – – 0.8560 0.6498 0.7009 0.5986 3.25 DeepLabV3+ Segmentation CropAndWeed 0.7393 0.7774 – – – – 0.8664 0.6705 0.7179 0.6230 108.37 SegFormer-B0 Segmentation CropAndWeed 0.8177 0.8049 – – – – 0.8854 0.7115 0.7665 0.6565 14.84 Note: For detection models, “primary” denotes AP/mAP50-95. RT-DETR-R18 was evaluated using COCO-style AP/AR metrics; its reported Test AR100 is AR at IoU=0.50:0.95, area=all, maxDets=100. YOLO precision and recall are scalar values from the retained YOLO evaluation summaries and are not directly interchangeable with COCO AR@100.


> **Table 5: Training reproducibility and artifact traceability summary. Manuscript tables use summarized metrics and artifact metadata rather than embedding full binary**

> model files; checkpoints and ONNX exports were tracked by path, size, and SHA256 hash.

Model Task Checkpoint (MiB) ONNX (MiB) Artifact manifests SHA256 content lines Export status

YOLO11n Detection 5.24 10.12 6 1139 exported YOLO11s Detection 18.31 36.19 6 512 exported RT-DETR-R18 Detection 307.52 76.59 2 717 exported BiSeNetV2 Segmentation 39.86 12.75 2 2608 exported MobileNetV3-LRASPP Segmentation 24.79 12.28 2 792 exported DeepLabV3+ Segmentation 326.22 153.84 2 1075 exported SegFormer-B0 Segmentation 42.70 14.29 2 1021 exported

failure, no failed inferences, no overtemperature event, and no tegrastats fault text. It was therefore retained as a valid native- mode run with power/current diagnostic warnings rather than as a failed run.

Using the YOLO11s complexity value of 11.81 GMACs per inference, AGX achieved 955.1 GMAC/s and 0.01536 J/GMAC. Nano achieved 1721.7 GMAC/s and 0.00650 J/GMAC. Thus, Nano was not only lower power; it delivered more YOLO11s computation per second and required less compute-normalized energy.

All energy formula checks passed. For each battery row, FPS, J/inference, inferences/Wh, and Wh/1000 inferences matched the reported inference count, elapsed time, and external energy window.

3.8. Matched-budget 15 W INT8 result: SegFormer-B0 The matched-budget SegFormer-B0 INT8 comparison also favoured Nano Super. AGX processed 414,130 inferences over 3.601 h at 31.95 FPS, whereas Nano processed 756,122 infer- ences over 4.452 h at 47.18 FPS. Nano therefore achieved a 1.48× throughput advantage. Median latency decreased from 29.523 ms on AGX to 21.514 ms on Nano, and p95 latency decreased from 29.566 ms to 21.582 ms.

3.6. Main battery continuation results Table 8 summarizes the six main pure-engine battery con- tinuation runs. All runs used batch size 1 and the 100% to 20% power-bank continuation protocol.

The two matched-budget INT8 comparisons favoured Nano Super. The native/high-performance SegFormer-B0 FP16 com- parison favoured AGX Orin in throughput and latency, while energy per inference was nearly tied.

Energy efficiency again favoured Nano. AGX required 0.5013 J/inference, while Nano required 0.2808 J/inference, a 44.0% reduction. Inferences/Wh increased from 7,182 on AGX to 12,821 on Nano.

3.7. Matched-budget 15 W INT8 result: YOLO11s In the matched 15 W comparison, Nano Super clearly outper- formed AGX Orin for YOLO11s INT8. Nano Super processed 2,760,205 inferences over 5.258 h, whereas AGX processed 1,136,477 inferences over 3.902 h. Nano achieved 145.82 FPS compared with 80.90 FPS on AGX, a 1.80× throughput advan- tage. Median latency decreased from 11.828 ms on AGX to 6.990 ms on Nano, and p95 latency decreased from 11.895 ms to 7.018 ms.

The compute-normalized result was consistent with the raw energy result. Using the SegFormer-B0 complexity value of 14.84 GMACs per inference, AGX achieved 474.0 GMAC/s and 0.03378 J/GMAC, whereas Nano achieved 700.0 GMAC/s and 0.01892 J/GMAC. The AGX run was stable rather than failed. Median and p95 latency were tightly grouped, and maximum internal temperature was 52.06◦C. The result therefore indicates underutilization of the larger AGX platform in the 15 W batch-1 INT8 regime, not a run validity problem.

Energy efficiency also favoured Nano. AGX required 0.1814 J/inference, while Nano required 0.0767 J/inference. This corre- sponds to a 57.7% reduction in energy per inference and a 2.36× increase in inferences/Wh. Because the two runs used compara- ble external energy windows, the Nano advantage reflects higher throughput and lower external power rather than only a longer runtime.

INT8 retention checks were performed for the four main 640 cross-board INT8 engines used in the battery-energy compari- son. All four main INT8 engines passed the aggregate retention criteria relative to their board-matched FP16 TensorRT refer- ences. The check was scoped to YOLO11s and SegFormer-B0

12


> **Table 6: Best AGX Orin locked-640 pure-engine result per model group. The original AGX table used an engine-level energy boundary; values are reported here as**

> J/inference.

Model group Best precision Median latency (ms) J/inference

DeepLabV3+ INT8 8.353 0.2369 MobileNetV3-LRASPP INT8 3.975 0.0800 BiSeNetV2 INT8 7.573 0.1269 RT-DETR-R18 INT8 6.499 0.1635 SegFormer-B0 INT8 7.029 0.2083 YOLO11n INT8 2.434 0.0431 YOLO11s INT8 3.390 0.0685


> **Table 7: Selected cross-board input sizes from the resolution ablation. S min is**

> the smallest accuracy-preserving input size relative to the 640 FP16 reference;
S max is the largest memory-safe common native FP16 input size across AGX
Orin 50 W and Orin Nano Super 25 W. The main benchmark matrix remains
locked at 640.

Pareto view: FPS vs energy per TensorRT inference

Nano YOLO11s INT8

agx 15W INT8 agx 50W FP16 nano_super 15W INT8 nano_super 25W FP16

140

120

Model Task Reference S min S max common

AGX SegFormer-B0 FP16

Throughput (FPS)

100

YOLO11s Detection 640 416 1536 RT-DETR-R18 Detection 640 640 640 BiSeNetV2 Segmentation 640 448 1152 SegFormer-B0 Segmentation 640 640 640

AGX YOLO11s INT8

80

Nano SegFormer-B0 FP16

60

Nano SegFormer-B0 INT8

at 640 on AGX Orin and Orin Nano Super, and was not intended as an exhaustive retention statement for every supplementary INT8 engine or resolution-ablation output.

40

AGX SegFormer-B0 INT8

0.1 0.2 0.3 0.4 0.5 External energy per inference (J/inference)

3.9. Native/high-performance result: SegFormer-B0 FP16 In the native/high-performance comparison, AGX Orin 50 W and Nano Super 25 W were evaluated using SegFormer-B0 FP16 at 640. This workload better exposed the AGX platform’s native throughput capacity than the matched-budget INT8 tests.


> **Figure 4: Pareto view of FPS versus J/inference for the main battery config-**

> urations. Marker size represents model complexity in GMACs. Nano Super
dominates the matched-budget INT8 configurations, while AGX provides the
native high-load SegFormer-B0 FP16 throughput advantage.

AGX achieved 103.61 FPS compared with 67.47 FPS on Nano, giving AGX a 1.54× throughput advantage. Median latency decreased from 14.842 ms on Nano to 9.420 ms on AGX, and p95 latency decreased from 15.020 ms to 9.441 ms. AGX therefore clearly won throughput and latency in the native SegFormer-B0 FP16 regime.

p95 latency of approximately 13.79 ms. However, Nano re- mained more energy-efficient for this model, requiring approx- imately 0.270 J/inference compared with approximately 0.311 J/inference on AGX.

This contrast case shows that model complexity alone does not determine energy efficiency. RT-DETR-R18 has higher GMACs than SegFormer-B0, yet its native-mode energy ranking differed. Architecture, TensorRT execution behaviour, memory access patterns, precision mode, and board power policy all influence the final deployment trade-off.

The normalized energy result was more nuanced. Using inference-aligned external energy, AGX required 0.3205 J/inference, while Nano required 0.3229 J/inference. The two boards were therefore nearly tied in energy per inference, with only a marginal AGX advantage. Compute-normalized energy showed the same pattern: AGX achieved 1537.2 GMAC/s and 0.02160 J/GMAC, whereas Nano achieved 1001.0 GMAC/s and 0.02177 J/GMAC.

3.11. Pareto view of throughput and energy Figure 4 summarizes the main battery configurations in the FPS versus J/inference plane. The matched-budget Nano Super INT8 points occupy the favourable high-FPS, low-energy region for YOLO11s and SegFormer-B0. AGX moves to the high- throughput region only under native high-load SegFormer-B0 FP16.

Thus, the strongest conclusion from the native SegFormer- B0 FP16 battery test is that AGX delivered substantially higher throughput and lower latency without a meaningful energy-per- inference or J/GMAC penalty.

3.10. Native RT-DETR-R18 FP16 contrast case

RT-DETR-R18 FP16 provided a useful contrast to the SegFormer- B0 native result. In native mode, AGX was faster, reaching approximately 105.1 FPS with p95 latency of approximately 9.73 ms, while Nano reached approximately 72.7 FPS with

3.12. Compute-normalized energy view Figure 5 shows the complexity-normalized deployment view. The matched 15 W Nano configurations had lower J/GMAC than AGX for both YOLO11s and SegFormer-B0. In contrast,

13


> **Table 8: Main pure-engine battery continuation results. All runs used batch size 1 and were stopped cleanly at 20% power-bank remaining. Energy is based on**

> external board-input logging.

Board Mode Model Prec. Inferences Runtime (h) FPS p95 (ms) Avg W Energy (Wh) J/inf. Inf./Wh

AGX Orin 15 W YOLO11s INT8 1,136,477 3.902 80.90 11.895 14.54 57.254 0.1814 19,850 Nano Super 15 W YOLO11s INT8 2,760,205 5.258 145.82 7.018 11.12 58.843 0.0767 46,908 AGX Orin 15 W SegFormer-B0 INT8 414,130 3.601 31.95 29.566 16.01 57.663 0.5013 7,182 Nano Super 15 W SegFormer-B0 INT8 756,122 4.452 47.18 21.582 13.15 58.974 0.2808 12,821 AGX Orin 50 W SegFormer-B0 FP16 660,564 1.771 103.61 9.441 33.20 58.807 0.3205 11,233 Nano Super 25 W SegFormer-B0 FP16 683,695 2.815 67.47 15.020 21.79 61.331 0.3229 11,148

Battery continuation summary

Complexity-normalized energy and throughput

1e6

0.035

AGX SegFormer-B0 INT8

agx 15W INT8 agx 50W FP16 nano_super 15W INT8 nano_super 25W FP16

5

2.5

Runtime from 100% to 20% remaining (h)

0.030

4

2.0

Total inferences

Compute-normalized energy (J/GMAC)

3

0.025

1.5

Nano SegFormer-B0 FP16

AGX SegFormer-B0 FP16

2

1.0

0.020

Nano SegFormer-B0 INT8

1

AGX YOLO11s INT8

0.5

0.015

0

nano_super

nano_super SegFormer-B0

nano_super SegFormer-B0

agx YOLO11s

agx SegFormer-B0

agx SegFormer-B0

YOLO11s

INT8 15W

INT8 15W

INT8 15W

INT8 15W

FP16 50W

FP16 25W

0.010

Nano YOLO11s INT8


> **Figure 6: Battery continuation runtime and total inference count. All main runs**

> used the power bank from 100% to 20% remaining and were stopped cleanly.
Nano Super ran longer in lower-power matched-budget configurations, while
AGX delivered higher native SegFormer-B0 FP16 throughput.

600 800 1000 1200 1400 1600 Compute throughput (GMAC/s)


> **Figure 5: Compute-normalized energy view. Matched-budget Nano Super INT8**

> runs achieved lower J/GMAC than AGX. In native SegFormer-B0 FP16, AGX
achieved higher GMAC/s while maintaining nearly the same J/GMAC as Nano
Super.

internal telemetry followed the external power trend but had non-negligible absolute bias. Because pooled correlations can be inflated by between-run differences in power level, per-run Pearson correlations are reported separately in Table 9. Bias, MAE, RMSE, and Bland–Altman limits were therefore treated as the main agreement evidence rather than correlation alone. Because adjacent 1 Hz samples within each run are temporally autocorrelated, the pooled sample count was used to charac- terize agreement over time and was not treated as independent replication.

native SegFormer-B0 FP16 showed nearly identical J/GMAC for AGX and Nano, while AGX delivered substantially higher GMAC/s.

3.13. Battery runtime and inference capacity


> **Figure 6 summarizes runtime and total inference count over**

> the 100% to 20% power-bank continuation window. Nano Super
ran longer in matched-budget INT8 configurations because its
observed external power was lower. It also processed more
total inferences for both YOLO11s and SegFormer-B0 INT8.
In native SegFormer-B0 FP16, Nano ran longer at lower power,
but AGX processed inferences at much higher throughput and
achieved a similar total inference count over a shorter time.


> **Table 9 summarizes per-run agreement. In matched-budget**

> INT8 runs, internal telemetry was generally below external
board-input power by approximately 2.0–2.6 W. The native
AGX SegFormer-B0 FP16 run showed a positive internal-minus-
external bias of 2.015 W, illustrating that internal rail aggregation
can differ by workload and board state. These findings support
the measurement hierarchy used in this paper: external inline
logging is the primary board-input energy reference, and internal
telemetry is a diagnostic channel.

3.14. Internal versus external power agreement The time-aligned agreement analysis used 76,691 paired 1 Hz overlap samples from the six main battery runs. These sam- ples were generated by mean-resampling external and internal power to one-second UTC bins and retaining only bins where both channels were present. They were used to quantify agree- ment and bias, not as the raw external logger sampling rate or as independent experimental replicates. The pooled internal- minus-external bias was −1.988 W, with MAE of 2.402 W and RMSE of 2.720 W. The pooled MAPE was 15.65%. Pearson and Spearman correlations were 0.970 and 0.932, respectively. Thus,

3.15. Idle baselines and empirical energy decomposition Idle baseline runs estimated board/mode baseline external power P0. AGX consumed 10.920 W in 15 W mode and 11.299 W in 50 W mode during idle. Nano Super consumed 5.308 W in 15 W mode and 5.663 W in 25 W mode. Table 10 lists the measured baseline values.

Using the complexity-aware model,

ˆJinf = P0

FPS + ηCm,

14


> **Table 9: Time-aligned internal–external power agreement over paired 1 Hz overlap samples. Bias is internal minus external power. Sample counts are paired**

> one-second bins used to characterize temporal agreement and were not treated as independent experimental replicates.

Board Mode Model/precision Samples Ext. W Int. W Bias W MAE W Pearson r

AGX 15 W YOLO11s INT8 13,330 14.729 12.141 -2.589 2.589 0.502 AGX 15 W SegFormer-B0 INT8 12,337 16.229 14.150 -2.079 2.085 0.585 Nano 15 W YOLO11s INT8 18,724 11.150 9.146 -2.004 2.074 0.395 Nano 15 W SegFormer-B0 INT8 16,029 13.145 10.974 -2.171 2.231 0.575 AGX 50 W SegFormer-B0 FP16 6,091 34.136 36.151 2.015 2.536 0.822 Nano 25 W SegFormer-B0 FP16 10,180 21.782 18.612 -3.169 3.335 0.722 Pooled Mixed All main runs 76,691 16.243 14.255 -1.988 2.402 0.970

Example time-aligned power trace

Time-aligned external vs internal power

External logger Internal telemetry

30

agx 15W agx 50W nano_super 15W nano_super 25W 1:1 line

40

25

35

20

Power (W)

30

Internal telemetry power (W)

15

10

25

5

20

0 5 10 15 20 25 30 Elapsed time in aligned window (min)

15


> **Figure 9: Example time-aligned external and internal power traces. External**

> board-input power and internal telemetry follow similar temporal structure but
differ in absolute level depending on board and workload.

10

5


> **Table 10: External idle baseline power used as P0 in the empirical energy model.**

5 10 15 20 25 30 35 40 External board-input power (W)

Board/mode Duration (s) Avg idle W Peak idle W


> **Figure 7: Time-aligned internal versus external power scatter. Internal telemetry**

> correlates with external board-input power but exhibits workload- and board-
dependent bias.

AGX 15 W 300 10.920 15.96 AGX 50 W 300 11.299 16.37 Nano 15 W 300 5.308 6.78 Nano 25 W 300 5.663 7.73

Bland Altman agreement: internal telemetry vs external logger

Mean bias = -1.99 W -1.96 SD = -5.63 W +1.96 SD = 1.65 W

10

sured energy was 0.5013 J/inference. In contrast, AGX 50 W SegFormer-B0 FP16 processed 103.61 FPS, reducing the amor- tized baseline contribution and producing 0.3205 J/inference.

5

Internal - external power (W)


> **Table 11 summarizes the direct energy decomposition for the**

> six main battery rows. Because the main battery set includes only
two matched-budget INT8 models per board and one native FP16
model per board, fitted dynamic slopes should be interpreted as
exploratory rather than as a universal predictive model. However,
the decomposition provides a useful explanation of the observed
regime dependence.

0

5

10

3.16. Supplementary end-to-end boundary check

5 10 15 20 25 30 35 40 Mean of external and internal power (W)

An AGX YOLO11s INT8 end-to-end image-pipeline battery run was also archived as a boundary check. This run processed 20,595 images at 1.075 FPS, with median latency of 914.758 ms, external energy of 62.213 Wh, and average external power of 11.695 W. The run was not included in the main cross-board en- ergy comparisons because it measured a different, non-optimized image-pipeline boundary rather than pure TensorRT engine ex- ecution. The contrast shows why TensorRT J/inference and image-pipeline J/image should be reported separately.


> **Figure 8: Bland–Altman analysis of internal and external power. The pooled**

> mean bias was −1.988 W, with limits of agreement from approximately −5.627
W to 1.651 W. The observed bias supports using the external inline logger as the
primary board-input energy reference.

the fixed platform term explains why low-throughput configu- rations can have high energy per inference. For example, AGX 15 W SegFormer-B0 INT8 had a relatively high baseline-to- throughput burden because it processed only 31.95 FPS. Its mea-

15


> **Table 11: Complexity-aware energy decomposition using idle baseline power. Dynamic power is observed average external power minus idle baseline power.**

Board Mode Model/precision FPS GMAC/s Avg W P0 W Dynamic W J/GMAC

AGX 15 W YOLO11s INT8 80.90 955.13 14.54 10.92 3.62 0.01536 Nano 15 W YOLO11s INT8 145.82 1721.71 11.12 5.31 5.81 0.00650 AGX 15 W SegFormer-B0 INT8 31.95 474.02 16.01 10.92 5.09 0.03378 Nano 15 W SegFormer-B0 INT8 47.18 699.96 13.15 5.31 7.84 0.01892 AGX 50 W SegFormer-B0 FP16 103.61 1537.23 33.20 11.30 21.90 0.02160 Nano 25 W SegFormer-B0 FP16 67.47 1001.01 21.79 5.66 16.12 0.02177

3.17. Deployment decision map

vision systems require joint reporting of task accuracy, latency, tail latency, board-input power, energy per inference, thermal stability, model complexity, and measurement boundary Liakos et al. (2018); Kamilaris and Prenafeta-Boldú (2018); Shamshiri et al. (2018). Separating the matched-budget and native/high- performance comparisons is therefore essential because they answer different engineering questions and can produce different board rankings.


> **Table 12 summarizes the deployment interpretation. Within**

> the tested configurations, Nano Super was preferred for matched-
budget INT8 operation, including YOLO11s INT8 and SegFormer-
B0 INT8. AGX Orin was preferred for native high-load SegFormer-
B0 FP16 when throughput and latency were the main priorities.
RT-DETR-R18 remains a contrast case because AGX is faster
but Nano is more energy-efficient.

4.2. Accuracy-only model selection is insufficient

3.18. Overall deployment finding The final results show that the deployment winner is not fixed by board class. In matched-budget 15 W INT8 opera- tion, Nano Super consistently outperformed AGX Orin for both YOLO11s and SegFormer-B0. Nano achieved higher through-

The training results show that all retained models were valid deployment candidates, but the most accurate or most computa- tionally expensive model was not automatically the best edge-AI choice. SegFormer-B0 achieved the strongest segmentation ac- curacy, whereas DeepLabV3+ required far more computation and a much larger artifact footprint. Similarly, RT-DETR-R18 required more GMACs than YOLO11s but achieved lower detec- tion test mAP50-95. This pattern is consistent with the broader deployment challenge in agricultural computer vision: accuracy- focused model development and resource-constrained field infer- ence are related but not identical objectives Dang et al. (2023); Chamara et al. (2023); Islam et al. (2025).

put, lower latency, lower external power, lower J/inference, and lower J/GMAC.

In native high-load SegFormer-B0 FP16 operation, AGX Orin became the stronger performance platform. It achieved substantially higher throughput and lower latency than Nano Super while maintaining comparable J/inference and J/GMAC. The native RT-DETR-R18 FP16 contrast case shows that this is not a universal AGX energy-efficiency win; model architecture and TensorRT execution behaviour also matter.

The complexity-versus-accuracy result in Fig. 3 therefore motivates the deployment measurements rather than replacing them. Parameter count and GMACs are useful explanatory variables, but they do not fully determine either accuracy or deployment cost. Measured TensorRT latency, external power, and energy-normalized metrics remain necessary when com- paring heterogeneous model families such as YOLO detectors, transformer-style detectors, lightweight CNN segmenters, and transformer-style segmentation models Ultralytics (2024); Zhao et al. (2024); Yu et al. (2021); Howard et al. (2019); Chen et al. (2018); Xie et al. (2021).

The concise deployment conclusion is: Nano Super wins matched-budget INT8; AGX Orin wins native high-load FP16 performance. More generally, agricultural edge-AI deployment efficiency is governed jointly by model complexity, precision, TensorRT execution boundary, batch size, and Jetson power mode, rather than by board class alone.


## 4. Discussion

4.1. Principal findings AgriJetsonBench should be interpreted as a deployment- measurement benchmark rather than a new model-architecture study. Its main finding is that agricultural edge-AI efficiency can- not be inferred from validation accuracy, board class, or model size alone. The preferred Jetson platform changed with work- load, precision, timing boundary, and operating mode: in the matched-budget 15 W INT8 regime, Jetson Orin Nano Super out- performed Jetson AGX Orin for both YOLO11s and SegFormer- B0, whereas in the native/high-performance SegFormer-B0 FP16 regime, Jetson AGX Orin delivered substantially higher through- put and lower latency with comparable energy per inference and compute-normalized energy.

4.3. Why Nano Super wins matched-budget INT8 inference The clearest result in the matched-budget setting was the Jetson Orin Nano Super advantage for INT8 inference. For YOLO11s INT8 at 15 W, Jetson Orin Nano Super achieved

higher throughput, lower latency, lower average external power, and lower energy per inference than Jetson AGX Orin, reducing energy from 0.1814 to 0.0767 J/inference. The same pattern held for SegFormer-B0 INT8 at 15 W, showing that the matched- budget Nano advantage was not limited to a lightweight detector but also applied to a transformer-style segmentation workload.

A likely explanation is that Jetson AGX Orin is underutilized in this low-power, batch-1 INT8 regime. The larger platform has more available compute capacity in native modes, but at 15 W it

This regime dependence supports the central premise of Agri- JetsonBench: deployment decisions for precision-agriculture

16


> **Table 12: AgriJetsonBench deployment decision map.**

Deployment goal Preferred tested configuration Evidence

Nano Super 15 W + YOLO11s INT8 640 145.8 FPS; 0.077 J/inference vs AGX 80.9 FPS; 0.181 J/inference Matched-budget INT8 segmentation Nano Super 15 W + SegFormer-B0 INT8 640 47.2 FPS; 0.281 J/inference vs AGX 31.9 FPS; 0.501 J/inference Native high-load FP16 segmentation throughput

Battery-oriented lightweight detection at matched 15 W

AGX Orin 50 W + SegFormer-B0 FP16 640 103.6 FPS vs Nano 67.5 FPS; lower p95 latency

Native high-load FP16 segmentation energy Near tie; marginal AGX edge in long battery run AGX 0.320 J/inference vs Nano 0.323 J/inference Highest SegFormer-B0 FP16 compute throughput

AGX Orin 50 W 1537 GMAC/s vs Nano 1001 GMAC/s

Measurement boundary interpretation Pure-engine main; end-to-end supplementary Do not mix TensorRT J/inference with image-pipeline J/image General deployment rule Choose by workload, precision, power mode, and boundary

Nano wins matched-budget INT8; AGX wins native high-load FP16 performance

cannot expose that capacity effectively for these workloads and retains higher platform overhead than Jetson Orin Nano Super. Jetson power-mode policies can constrain clocks, rail behaviour, and available compute resources NVIDIA (2024b,a). The idle baselines support this interpretation: the AGX idle baseline was approximately 10.9 W in 15 W mode, whereas the Nano idle baseline was approximately 5.3 W. When throughput is low, this fixed overhead is amortized across fewer inferences, increasing J/inference.

behaviour, memory access patterns, precision handling, and ker- nel fusion can therefore change the energy ranking, even when a larger board improves throughput Zhao et al. (2024); NVIDIA (2026a). A short, well-instrumented pure-engine benchmark remains necessary for each architecture and precision mode.

4.6. Importance of timing-boundary separation One of the main methodological lessons from this study is that timing boundary must be explicit. The main results use a pure TensorRT engine-level boundary to isolate accelerator- side model execution, precision mode, and power-mode pol- icy. This boundary enables fair comparison between random- input trtexec style execution and preloaded tensor execution when the timed region contains only batch-1 TensorRT inference NVIDIA (2026a,b).

4.4. Why AGX Orin becomes favourable in native SegFormer- B0 FP16 The native SegFormer-B0 FP16 result shows the other side of the deployment trade-off. In 50 W native/high-performance mode, Jetson AGX Orin reached 103.61 FPS for SegFormer-B0 FP16, compared with 67.47 FPS on Jetson Orin Nano Super in 25 W mode, and it reduced median and p95 latency substantially. Importantly, this higher throughput did not produce a meaningful energy-per-inference penalty: AGX required 0.3205 J/inference, while Nano required 0.3229 J/inference in the inference-aligned long battery comparison, with nearly tied compute-normalized energy.

Pure-engine results should not be interpreted as full application- level image-pipeline throughput. The archived AGX YOLO11s INT8 end-to-end image-pipeline run was much slower because it included image-path handling, preprocessing, postprocessing, and saving overhead. That supplementary run illustrates the pos- sible gap between engine-level inference and a full application pipeline, but it was not mixed with the main comparison to avoid confounding model execution efficiency with pipeline imple- mentation overhead. For agricultural deployment, pure-engine results answer how efficient the optimized TensorRT model is on the Jetson platform, while end-to-end results answer how efficient a specific application implementation is Chamara et al. (2023); Gao et al. (2023); Zhang and Lv (2024); Islam et al. (2025).

This result does not imply that Jetson AGX Orin is always more energy-efficient than Jetson Orin Nano Super or that higher power modes always improve efficiency. It shows that a larger platform can become favourable when the workload is heavy enough to expose its compute capacity and when throughput is important. TensorRT optimization, precision mode, kernel selection, and engine construction can strongly affect measured inference behaviour on embedded GPUs NVIDIA (2026a,b). Thus, battery-oriented lightweight detection favours Jetson Orin Nano Super in the tested matched-budget INT8 regime, whereas low-latency heavier segmentation can justify Jetson AGX Orin in native mode.

4.7. External board-input power should remain the primary energy reference

The time-aligned internal–external agreement analysis showed strong temporal correlation but non-negligible absolute bias. Us- ing the paired 1 Hz overlap workflow described in Section 2.16, 76,691 paired samples were compared. Internal telemetry and external power were strongly correlated, but the pooled internal- minus-external bias was approximately -1.99 W, with MAE of 2.40 W and RMSE of 2.72 W. The Bland–Altman limits of agreement further showed that internal telemetry can deviate

4.5. RT-DETR-R18 shows that architecture still matters The RT-DETR-R18 FP16 native result prevents an overly simple conclusion such as “AGX wins native mode” or “Nano wins energy.” AGX was faster for RT-DETR-R18, but Nano remained more energy-efficient. Architecture-specific TensorRT

17

4.10. Implications for agricultural edge-AI deployment The results lead to four practical recommendations. First, for battery-oriented lightweight detection at matched 15 W, Jet- son Orin Nano Super with YOLO11s INT8 is the preferred configuration among those tested. Second, for matched-budget SegFormer-B0 INT8 segmentation, Jetson Orin Nano Super again provides better throughput and energy efficiency than Jet- son AGX Orin. Third, for native high-load SegFormer-B0 FP16 segmentation, Jetson AGX Orin is the preferred performance platform when latency or frame rate is more important than maximum runtime duration. Fourth, model architecture and precision mode must be evaluated directly; the RT-DETR-R18 contrast case shows that a native-mode speed advantage does not automatically imply an energy advantage Dang et al. (2023); Chamara et al. (2023); Gao et al. (2023); Zhang and Lv (2024); Islam et al. (2025); Wang et al. (2026).

from board-input power by several watts depending on board, mode, and workload Bland and Altman (1986).

These results support the measurement hierarchy used through- out AgriJetsonBench. The external inline logger should be treated as the primary board-input energy reference, while in- ternal telemetry should be used as a diagnostic channel for tem- perature, memory pressure, rail-level behaviour, temporal power trends, and abnormal run conditions. Because rail aggregation and coverage differ across devices and operating states, internal telemetry should not replace external board-input logging when reporting energy per inference NVIDIA (2026c, 2024a); Texas Instruments (2026).

4.8. Battery continuation adds deployment realism Short benchmark runs are useful for latency and through- put characterization, but they do not fully represent sustained field operation. The power-bank continuation protocol added a deployment-oriented layer by running from 100% power-bank charge to 20% remaining and stopping cleanly before cutoff. Nano Super ran longer in the matched-budget INT8 configura- tions and processed more total inferences for both YOLO11s and SegFormer-B0 INT8. In native SegFormer-B0 FP16, Nano ran longer because it used lower power, but AGX processed at a higher rate and achieved a similar total inference count over a shorter period.

Pure-engine and end-to-end results should also be reported separately. A user deploying a full field pipeline should ex- pect additional overhead from image capture, decoding, pre- processing, postprocessing, storage, and communication. The deployment rule emerging from AgriJetsonBench is therefore:

Choose the board, precision, and power mode ac- cording to workload complexity, latency target, en- ergy budget, and measurement boundary. Nano Su- per wins matched-budget INT8 in this study, while AGX Orin wins native high-load FP16 segmenta- tion performance.

The battery protocol also made the stop condition explicit. The power-bank display was used only to define the 100% to 20% continuation window; all energy metrics were computed from the external logger. This distinction is important because power-source state-of-charge indicators are not equivalent to time-integrated board-input energy.

4.11. Reproducibility and auditability A major goal of AgriJetsonBench is to make the bench- mark auditable. The package records dataset splits, class names, license notes, training summaries, validation metrics, model artifact manifests, SHA256 checksums, TensorRT deployment evidence, hardware/software versions, battery summaries, la- tency CSV files, event records, noise-guard summaries, sani- tized run-validity summaries, external logger archives, internal telemetry, idle baselines, agreement tables, and analysis scripts. This structure allows the reported tables to be checked against run-level evidence.

4.9. Interpretation of the empirical energy model The complexity-aware energy model was used to interpret the observed regime dependence, not to claim universal predic- tive accuracy. The model separates measured external power into a board/mode baseline term and a workload-dependent compute term:

ˆPext = P0 + η(Cm × FPS), (18)

with corresponding energy per inference:

This matters because edge-AI benchmarking is vulnerable to ambiguity. FPS and energy values are difficult to interpret without knowing the input size, batch size, timing boundary, precision mode, power mode, and whether energy came from internal telemetry, external board-input logging, or a battery- percentage estimate. By preserving metadata, code, manifests, checksums, and raw evidence, AgriJetsonBench reduces this ambiguity and provides a starting point for larger agricultural edge-AI benchmark extensions Wilkinson et al. (2016); Peng (2011).

ˆJinf = P0

FPS + ηCm. (19)

This form explains why a larger board may appear inefficient under a low-power batch-1 regime: if P0 is high and FPS is low, the fixed overhead per inference becomes large. Conversely, when AGX was operated in 50 W mode with SegFormer-B0 FP16, throughput increased substantially, reducing the amor- tized baseline contribution and producing energy per inference comparable to Nano. Because the main battery set contains six long continuation runs, the fitted dynamic slopes should be interpreted as exploratory deployment estimators rather than universal coefficients.

4.12. Limitations Several limitations should be considered when interpreting the results. First, the main Jetson deployment metrics use a pure TensorRT engine-level boundary. This was intentional for

18

controlled comparison, but it does not measure full application- level image processing, which depends on camera input, decod- ing, preprocessing, postprocessing, storage, and communication. Second, all main runs used batch size 1. This reflects online agricultural inference, but it may underutilize larger platforms such as AGX Orin; future work could include batch-size scaling while keeping batch-1 as the main deployment baseline.

external board-input power measurement, internal telemetry, bat- tery continuation tests, and deployment decision analysis. By preserving tables, figures, scripts, telemetry, logger archives, manifests, and SHA256 checksums, AgriJetsonBench was de- signed not only to report results, but also to make the evidence behind those results auditable.

The results show that agricultural edge-AI deployment effi- ciency is not determined by board class alone. In the matched- budget 15 W INT8 regime, Jetson Orin Nano Super was the preferred platform for the tested workloads. For YOLO11s INT8, Nano Super achieved higher throughput, lower latency, and lower energy per inference than Jetson AGX Orin. For SegFormer-B0 INT8, Nano Super again achieved higher FPS and lower J/inference under the same nominal 15 W budget. These results support Nano Super as the better choice for battery- oriented matched-budget INT8 deployment in the evaluated de- tection and segmentation workloads.

Third, the long battery continuation tests were designed as sustained deployment trials rather than statistical repeat experi- ments. Short benchmark repeats and validity checks support run quality, but repeated long battery trials are needed to quantify run-to-run variability. Fourth, the empirical energy model is useful for interpretation but should not be treated as universal across all Jetson boards, workloads, and environmental condi- tions. Fifth, the evaluated datasets represent crop/weed detection and segmentation, so generalization to livestock monitoring, fruit counting, disease detection, or autonomous navigation should be tested directly.

The native/high-performance SegFormer-B0 FP16 compari- son showed a different deployment regime. When Jetson AGX Orin was operated in 50 W mode and Nano Super in 25 W mode, AGX Orin achieved substantially higher throughput and lower latency for SegFormer-B0 FP16 while maintaining nearly com- parable energy per inference and compute-normalized energy. This result shows that the larger AGX platform can become favourable when the workload is sufficiently heavy and the de- ployment objective emphasizes latency or throughput rather than minimum average power. The RT-DETR-R18 FP16 con- trast case further showed that architecture matters: AGX can be faster while Nano remains more energy-efficient for some models.

Finally, the main 640 cross-board INT8 engines were accom- panied by retention evidence relative to board-matched FP16 TensorRT references, and all four main engines passed the ag- gregate retention criteria used in this manuscript. This supports the matched-budget INT8 deployment comparisons reported for YOLO11s and SegFormer-B0. However, the retention check was

scoped to the main 640 engines and should not be interpreted as a complete retention guarantee for every supplementary INT8 engine, input resolution, or model family.

4.13. Future work Future work should extend AgriJetsonBench to additional agricultural tasks and datasets, including fruit detection, plant disease segmentation, livestock monitoring, and navigation- relevant perception. More edge platforms should be added, including other Jetson Orin variants and non-NVIDIA embed- ded accelerators, while preserving the same external power and validity protocol. A useful supplementary runtime-level compar- ison would evaluate ONNX Runtime with the TensorRT Execu- tion Provider, which would address deployments that prefer the ONNX Runtime API but should be reported separately from the pure TensorRT engine-level boundary used as the main bench- mark in this study (ONNX Runtime, 2026). Full end-to-end application pipelines should also be benchmarked separately from pure-engine inference, and the empirical energy model should be expanded with more models, repeated runs, input sizes, and batch sizes. The next step is field validation of the most promising configurations on mobile platforms with real sensors, enclosure constraints, variable ambient temperatures, and realistic duty cycles.

The dual-source power analysis also supports a clear mea- surement recommendation. Internal Jetson telemetry is useful for diagnostics, temperature tracking, memory and rail-level behaviour, and time-aligned agreement analysis. However, the observed internal–external bias confirms that external inline board-input logging should remain the primary reference for reporting energy per inference. For agricultural edge-AI studies, this distinction is important because internal telemetry, external board-input energy, and battery state-of-charge indicators are not interchangeable.

The study also emphasizes the need to separate measurement boundaries. Pure TensorRT engine-level inference provides a controlled way to compare models, precisions, power modes, and Jetson platforms. End-to-end image-pipeline measurements are useful for complete application profiling, but they should not be mixed with pure-engine J/inference results. This bound- ary separation is essential for interpretable energy-normalized benchmarking.

Overall, the main deployment rule from AgriJetsonBench is:


## 5. Conclusions

Nano Super wins matched-budget INT8 inference in the tested workloads, while AGX Orin wins na- tive high-load SegFormer-B0 FP16 performance. Board choice should therefore be made according to workload complexity, precision mode, power mode, latency target, energy budget, and measure- ment boundary.

This study introduced AgriJetsonBench, a reproducible complexity- aware energy benchmark for agricultural vision model deploy- ment on NVIDIA Jetson edge-AI platforms. The benchmark con- nects locked agricultural datasets, offline model training, ONNX and TensorRT deployment, pure-engine Jetson benchmarking,

19

These findings provide a practical framework for selecting agricultural edge-AI deployments. Rather than relying on accu- racy alone, future field systems should evaluate model accuracy together with latency, external board-input power, energy per inference, compute-normalized energy, thermal behaviour, and run validity. Future work should extend AgriJetsonBench to additional agricultural tasks, edge accelerators, repeated long- duration field trials, batch-size scaling studies, and fully opti- mized end-to-end application pipelines.

Bland, J.M., Altman, D.G., 1986. Statistical methods for assess-

ing agreement between two methods of clinical measurement. The Lancet 327, 307–310. URL: https://doi.org/10.1 016/S0140-6736(86)90837-8, doi:10.1016/S0140-673 6(86)90837-8.

Chamara, N., Bai, G., Ge, Y., 2023. AICropCAM: Deploying

classification, segmentation, detection, and counting deep- learning models for crop monitoring on the edge. Computers and Electronics in Agriculture 215, 108420. URL: https: //doi.org/10.1016/j.compag.2023.108420, doi:10.1

Data and code availability

016/j.compag.2023.108420.

The data and code that support the findings of this study are available from the corresponding author upon reasonable request.

Chen, L.C., Zhu, Y., Papandreou, G., Schroff, F., Adam, H.,

2018. Encoder-decoder with atrous separable convolution for semantic image segmentation, in: Proceedings of the Euro- pean Conference on Computer Vision, pp. 801–818. URL: https://doi.org/10.1007/978-3-030-01234-2_49, doi:10.1007/978-3-030-01234-2_49.

Declaration of competing interest

The authors declare that they have no known competing financial interests or personal relationships that could have ap- peared to influence the work reported in this paper.

Dang, F., Chen, D., Lu, Y., Li, Z., 2023. YOLOWeeds: A

novel benchmark of YOLO object detectors for multi-class weed detection in cotton production systems. Computers and Electronics in Agriculture 205, 107655. URL: https: //doi.org/10.1016/j.compag.2023.107655, doi:10.1

Funding

016/j.compag.2023.107655.

This research received no external funding.

Gao, R., Chang, P., Chang, D., Tian, X., Li, Y., Ruan, Z., Su, Z.,

2023. RTAL: An edge computing method for real-time rice lodging assessment. Computers and Electronics in Agriculture 215, 108386. URL: https://doi.org/10.1016/j.comp ag.2023.108386, doi:10.1016/j.compag.2023.1083 86.

CRediT authorship contribution statement

Hasan Jahanifar: Conceptualization, Methodology, Software, Data curation, Investigation, Formal analysis, Visualization, Writing – original draft. Hasan Mirzakhaninafchi: Method- ology, Validation, Writing – review and editing. Wesley M. Porter: Supervision, Resources, Project administration, Valida- tion, Writing – review and editing. Abolfazl Najar: Method- ology, Investigation, Validation. Glen C. Rains: Supervision, Resources, Validation, Writing – review and editing.

Georgia Advanced Computing Resource Center, 2026. Systems:

Sapelo2. https://wiki.gacrc.uga.edu/wiki/Systems. University of Georgia.

Howard, A., Sandler, M., Chu, G., Chen, L.C., Chen, B., Tan, M.,

Wang, W., Zhu, Y., Pang, R., Vasudevan, V., Le, Q.V., Adam, H., 2019. Searching for MobileNetV3, in: Proceedings of the IEEE/CVF International Conference on Computer Vision, pp. 1314–1324. URL: https://doi.org/10.1109/ICCV.201 9.00140, doi:10.1109/ICCV.2019.00140.


## References

Akiba, T., Sano, S., Yanase, T., Ohta, T., Koyama, M., 2019. Op-

tuna: A next-generation hyperparameter optimization frame- work, in: Proceedings of the 25th ACM SIGKDD Interna- tional Conference on Knowledge Discovery and Data Mining, pp. 2623–2631. URL: https://doi.org/10.1145/3292 500.3330701, doi:10.1145/3292500.3330701.

Islam, M.D., Liu, W., Izere, P., Singh, P., Yu, C., Riggan, B.,

Zhang, K., Jhala, A.J., Knezevic, S., Ge, Y., Pitla, S., Luck, J., Shi, Y., 2025. Towards real-time weed detection and seg- mentation with lightweight CNN models on edge devices. Computers and Electronics in Agriculture 237, 110600. URL: https://doi.org/10.1016/j.compag.2025.110600, doi:10.1016/j.compag.2025.110600.

Banbury, C., Janapa Reddi, V., Torelli, P., Holleman, J., Jef-

fries, N., Kiraly, C., Montino, P., Kanter, D., Ahmed, S., Pau, D., Thakker, U., Torrini, A., Warden, P., Cordaro, J., Di Guglielmo, G., Duarte, J., Gibellini, S., Parekh, V., Tran, H., Tran, N., Wenxu, N., Xuesong, X., 2021. MLPerf Tiny Benchmark. doi:10.48550/arXiv.2106.07597, arXiv:2106.07597.

Kamilaris, A., Prenafeta-Boldú, F.X., 2018. Deep learning in

agriculture: A survey. Computers and Electronics in Agricul- ture 147, 70–90. URL: https://doi.org/10.1016/j.co mpag.2018.02.016, doi:10.1016/j.compag.2018.02.0 16.

20

Ultralytics, 2024. Ultralytics YOLO11. https://docs.ult

Liakos, K.G., Busato, P., Moshou, D., Pearson, S., Bochtis, D.,

2018. Machine learning in agriculture: A review. Sensors 18, 2674. URL: https://doi.org/10.3390/s18082674, doi:10.3390/s18082674.

ralytics.com/models/yolo11/.

Wang, Y., Yuan, X., Wei, B., Ruchay, A., Pezzuolo, A., Guo, H.,

2026. Performance evaluation of a state-of-the-art keypoint detection method for precision livestock farming. Computers and Electronics in Agriculture 240, 111230. URL: https: //doi.org/10.1016/j.compag.2025.111230, doi:10.1

NVIDIA, 2024a. Jetson Orin NX Series and Jetson AGX Orin

Series: Platform Power and Performance. https://docs.n vidia.com/jetson/archives/r35.1/DeveloperGuide /text/SD/PlatformPowerAndPerformance/JetsonOri

016/j.compag.2025.111230.

nNxSeriesAndJetsonAgxOrinSeries.html.

Weed-AI, 2023. CottonWeedDet12 Dataset. https://weed-a

NVIDIA, 2024b. NVIDIA Jetson Linux Developer Guide. ht

i.sydney.edu.au/datasets/2c14915b-0827-4b65-9 908-d2a6df0d48f3.

tps://docs.nvidia.com/jetson/archives/r36.4/De veloperGuide/index.html.

Wilkinson, M.D., Dumontier, M., Aalbersberg, I.J., Apple-

NVIDIA, 2026a. NVIDIA TensorRT Documentation. https:

ton, G., Axton, M., Baak, A., Blomberg, N., Boiten, J.W., da Silva Santos, L.B., Bourne, P.E., Bouwman, J., Brookes, A.J., Clark, T., Crosas, M., Dillo, I., Dumon, O., Edmunds, S., Evelo, C.T., Finkers, R., Gonzalez-Beltran, A., Gray, A.J.G., Groth, P., Goble, C., Grethe, J.S., Heringa, J., ’t Hoen, P.A.C., Hooft, R., Kuhn, T., Kok, R., Kok, J., Lusher, S.J., Martone, M.E., Mons, A., Packer, A.L., Persson, B., Rocca-Serra, P., Roos, M., van Schaik, R., Sansone, S.A., Schultes, E., Sen- gstag, T., Slater, T., Strawn, G., Swertz, M.A., Thompson, M., van der Lei, J., van Mulligen, E., Velterop, J., Waag- meester, A., Wittenburg, P., Wolstencroft, K., Zhao, J., Mons, B., 2016. The FAIR guiding principles for scientific data management and stewardship. Scientific Data 3, 160018. URL: https://doi.org/10.1038/sdata.2016.18, doi:10.1038/sdata.2016.18.

//docs.nvidia.com/deeplearning/tensorrt/latest /index.html.

NVIDIA, 2026b. Performance benchmarking using trtexec.

https://docs.nvidia.com/deeplearning/tensorrt/ latest/performance/benchmarking.html.

NVIDIA, 2026c. Tegrastats Utility — NVIDIA Jetson Linux

Developer Guide. https://docs.nvidia.com/jetson/a rchives/r36.5/DeveloperGuide/AT/JetsonLinuxDev elopmentTools/TegrastatsUtility.html.

ONNX Runtime, 2026. TensorRT Execution Provider. https:

//onnxruntime.ai/docs/execution-providers/Ten

sorRT-ExecutionProvider.html.

Peng, R.D., 2011. Reproducible research in computational science. Science 334, 1226–1227. URL: https://doi.or g/10.1126/science.1213847, doi:10.1126/science. 1213847.

Xie, E., Wang, W., Yu, Z., Anandkumar, A., Alvarez, J.M.,

Luo, P., 2021. SegFormer: Simple and efficient design for semantic segmentation with transformers, in: Advances in Neural Information Processing Systems, pp. 12077–12090. URL: https://proceedings.neurips.cc/paper/202 1/hash/64f1f27bf1b4ec22924fd0acb550c235-Abstr act.html.

Schwartz, R., Dodge, J., Smith, N.A., Etzioni, O., 2020. Green

ai. Communications of the ACM 63, 54–63. doi:10.1145/ 3381831.

Yu, C., Gao, C., Wang, J., Yu, G., Shen, C., Sang, N., 2021.

Shamshiri, R.R., Weltzien, C., Hameed, I.A., Yule, I.J., Grift,

BiSeNet V2: Bilateral network with guided aggregation for real-time semantic segmentation. International Journal of Computer Vision 129, 3051–3068. URL: https://doi.or g/10.1007/s11263-021-01515-2, doi:10.1007/s11263 -021-01515-2.

T.E., Balasundram, S.K., Pitonakova, L., Ahmad, D., Chowd- hary, G., 2018. Research and development in agricultural robotics: A perspective of digital farming. International Jour- nal of Agricultural and Biological Engineering 11, 1–14. URL: https://doi.org/10.25165/j.ijabe.20181104.42 78, doi:10.25165/j.ijabe.20181104.4278.

Zhang, Y., Lv, C., 2024. TinySegformer: A lightweight visual

segmentation model for real-time agricultural pest detection. Computers and Electronics in Agriculture 218, 108740. URL: https://doi.org/10.1016/j.compag.2024.108740, doi:10.1016/j.compag.2024.108740.

Steininger, D., Trondl, A., Croonen, G., Simon, J., Widhalm,

V., 2023. The CropAndWeed dataset: A multi-modal learn- ing approach for efficient crop and weed manipulation, in: Proceedings of the IEEE/CVF Winter Conference on Applica- tions of Computer Vision Workshops, pp. 3729–3738. URL: https://doi.org/10.1109/WACV56688.2023.00372, doi:10.1109/WACV56688.2023.00372.

Zhao, Y., Lv, W., Xu, S., Wei, J., Wang, G., Dang, Q., Liu,

Y., Chen, J., 2024. DETRs beat YOLOs on real-time object

detection, in: Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition, pp. 16965–16974. URL: https://doi.org/10.1109/CVPR52733.2024.0 1605, doi:10.1109/CVPR52733.2024.01605.

Texas Instruments, 2026. INA260 36-V, 16-bit, Precision I2C

Output Current/Voltage/Power Monitor with Integrated Shunt Resistor. https://www.ti.com/product/INA260.

21
