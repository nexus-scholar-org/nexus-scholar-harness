# PRISMA Dual-Screening Inter-Rater Dispute & Adjudication Ledger

- **Project Workspace**: `uav-cv-precision-agriculture`
- **Screened Corpus**: `1,488` papers (`literature/verified.json`)
- **Total Inter-Rater Disputes Adjudicated**: `690` (46.37% of corpus)
- **Inter-Rater Reliability**: Cohen's $\kappa = 0.115$ (*slight agreement*)
- **Adjudication Mechanism**: 6 independent third-party reviewing agent panels (Groups 1–6)
- **Date Reconciled**: 2026-09-04

---

## 1. Adjudication Protocol & Decision Architecture

Two independent screeners scored all 1,488 candidate papers:
- **Screener 1**: Highly permissive (52.8% inclusion rate), influenced by template heuristics that admitted out-of-domain power-line, LiDAR, and forestry works.
- **Screener 2**: Highly rigorous (7.5% inclusion rate), requiring strict evidence of UAV low-altitude imagery, deep learning segmentation masks, and empirical benchmark reporting.

### Confusion Matrix (N = 1,488)
| | S2 = INCLUDE | S2 = EXCLUDE | Row Total |
| :--- | :---: | :---: | :---: |
| **S1 = INCLUDE** | 104 | 682 | 786 |
| **S1 = EXCLUDE** | 8 | 694 | 702 |
| **Column Total** | 112 | 1,376 | 1,488 |

All **690 disagreements** were submitted to third-party adjudicating agents with access to full verified bibliographic metadata. The adjudication panel overturned 683 improper inclusions from Screener 1 to EXCLUDE and restored 7 critical benchmark studies to INCLUDE.

---

## 2. The 39 Flagged Caveat Studies (Option B: Provisional Full-Text Verification)

To prevent false-negative exclusion of seminal benchmark datasets and edge inference papers whose abstracts omitted numeric metric values, 39 studies have been provisionally advanced to Stage 3 Full-Text Retrieval:

| Workspace ID | Year | Title | Venue | Caveat Subtype | Verification Action |
| :--- | :---: | :--- | :--- | :--- | :--- |
| `SCI-000002` | 2021 | Adaptive Path Planning for UAV-based Multi-Resolution Semantic Segment | arXiv Preprint | `CONTESTED_EXC06_IN_SCOPE_NO_NUMERIC_METRIC` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000010` | 2019 | Semi-supervised GAN for Classification of Multispectral Imagery Acquir | arXiv Preprint | `CONTESTED_EXC06_IN_SCOPE_NO_NUMERIC_METRIC` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000095` | 2023 | Unmanned Aerial Vehicle (UAV) in Precision Agriculture to Identify the | Open Access Journal of Agricul | `CONTESTED_EXC06_IN_SCOPE_NO_NUMERIC_METRIC` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000110` | 2025 | Optimization of Coverage Path Planning for Agricultural Drones in Weed | Agriculture | `CONTESTED_EXC06_IN_SCOPE_NO_NUMERIC_METRIC` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000129` | 2026 | Multispectral image fusion and attention-driven deep learning for prec | GeoInformatica | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000140` | 2024 | Mapping the future of farm management: A comprehensive analysis of app | Journal of Crop and Weed | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000148` | 2025 | Sustainable Cotton Crop Productivity through Precision Weed Detection: | Journal of Aerospace Engineeri | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000274` | 2021 | A real-time efficient object segmentation system based on U-Net using  | Journal of Real-Time Image Pro | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000315` | 2026 | Deteksi Objek Pohon Secara Real-Time dari Udara Menggunakan YOLOv8 pad | Jurnal Fisika Unand | `CONTESTED_EXC06_IN_SCOPE_NO_NUMERIC_METRIC` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000369` | 2025 | A Real-Time Aerial Semantic Segmentation System Based on U-Net Deep Le | Lecture Notes in Networks and  | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000397` | 2026 | Semantic segmentation performance of aerial image segmentation using w | Multimedia Tools and Applicati | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000398` | 2020 | Unmanned Aerial Vehicle (UAV)-Based Hyperspectral Imaging System for P | Unmanned Aerial Vehicle: Appli | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000408` | 2025 | Enhanced Agricultural Productivity: UAV-Based Technology for Precision | Smart Agriculture | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000411` | 2020 | Precision Agriculture and Unmanned Aerial Vehicles (UAVs) | Unmanned Aerial Vehicle: Appli | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000416` | 2023 | Real-time detection of cracks in tiled sidewalks using YOLO-based meth | Automation in Construction | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000426` | 2024 | Real-time monitoring using unmanned aerial vehicle (UAV) | AIP Conference Proceedings | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000433` | 2023 | Application of unmanned aerial systems to address real-world issues in | Unmanned Aerial Systems in Agr | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000434` | 2021 | 57. Optimizing peach management based on hyperspectral and unmanned ae | Precision agriculture '21 | `CONTESTED_EXC06_IN_SCOPE_NO_NUMERIC_METRIC` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000439` | 2024 | Applications of UAV-AD (Unmanned Aerial Vehicle-Agricultural Drones) i | Signals and Communication Tech | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000440` | 2024 | On-Edge Weed Detection Using Unmanned Aerial Vehicles | SSRN Electronic Journal | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000441` | 2023 | The MR12-UAV Bombardier: A Cutting-Edge Unmanned Aerial Vehicle in Bom | SSRN Electronic Journal | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000442` | 2024 | Real-Time Vehicle Detection and Urban Traffic Behavior Analysis Based  | SSRN Electronic Journal | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000446` | 2026 | Artificial Intelligence Implementation on Unmanned Aerial Vehicle for  | Sustainable Aviation | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000450` | 2023 | Real-time human search and monitoring system using unmanned aerial veh | International Journal of Vehic | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000451` | 2023 | High-Precision Time Synchronization Algorithm for Unmanned Aerial Vehi | SSRN Electronic Journal | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000575` | 2022 | Improved Real-Time Semantic Segmentation Network Model for Crop Vision | Frontiers in Plant Science | `CONTESTED_EXC06_IN_SCOPE_NO_NUMERIC_METRIC` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000639` | 2023 | CoFly: An automated, AI-based open-source platform for UAV precision a | SoftwareX | `CONTESTED_EXC06_IN_SCOPE_NO_NUMERIC_METRIC` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000650` | 2024 | Harnessing UAVs and deep learning for accurate grass weed detection in | Plant Methods | `CONTESTED_EXC06_IN_SCOPE_NO_NUMERIC_METRIC` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000666` | 2023 | Overcome the Fear Of Missing Out: Active sensing UAV scanning for prec | Robotics and Autonomous System | `CONTESTED_EXC06_IN_SCOPE_NO_NUMERIC_METRIC` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000877` | 2026 | CamelinaWeed: an expert-agronomist-annotated UAV RGB and multispectral | Data in brief | `CONTESTED_EXC06_IN_SCOPE_NO_NUMERIC_METRIC` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000902` | 2024 | An instance segmentation dataset of cabbages over the whole growing se | Data in brief | `CONTESTED_EXC06_IN_SCOPE_NO_NUMERIC_METRIC` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000910` | 2022 | CoFly-WeedDB: A UAV image dataset for weed detection and species ident | Data in brief | `CONTESTED_EXC06_IN_SCOPE_NO_NUMERIC_METRIC` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-000934` | 2026 | UAV-based real-time detection of corn earworm using EfficientNet and m | Journal of environmental scien | `CONTESTED_EXC06_IN_SCOPE_NO_NUMERIC_METRIC` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-001127` | 2025 | AI in weed management | International journal of agric | `CONTESTED_EXC06_IN_SCOPE_NO_NUMERIC_METRIC` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-001166` | 2022 | An Adaptive Spatial Network for UAV Image Real-Time Semantic Segmentat | International Conference on In | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-001221` | 2023 | Semantic segmentation of remote sensing image based on Contextual U-Ne | Other Conferences | `CONTESTED_EXC06_IN_SCOPE_NO_NUMERIC_METRIC` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-001399` | 2025 | Real-Time Semantic Segmentation for UAV Perspectives on Embedded Platf | International Conference on In | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-001445` | 2020 | Design and Implementation of Real-time Amphibious Unmanned Aerial Vehi | Unknown | `MISSING_ABSTRACT` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |
| `SCI-001480` | 2025 | Vision-Based UAV Navigation in Vineyards using a Disturbance-Aware NMP | 2025 IEEE International Worksh | `CONTESTED_EXC06_IN_SCOPE_NO_NUMERIC_METRIC` | Retrieve full-text PDF in Phase 2; screen Section 4/5 for empirical segmentation benchmark metrics. |

---

## 3. Disputed Inclusions Adjudicated to Confirmed INCLUDE (N = 7)

| Workspace ID | Year | Title | S1 Decision | S2 Decision | Adjudication Rationale |
| :--- | :---: | :--- | :---: | :---: | :--- |
| `SCI-000084` | 2020 | Crop and Weed Classication Using Pixel-wise Segmentation on  | `EXCLUDE` | `INCLUDE` | Encoder-decoder CNNs perform pixel-wise crop/weed classification/segmentation on ground and aerial images, including a third CNN specifically for smal... |
| `SCI-000092` | 2020 | A DNN-based semantic segmentation for detecting weed and cro | `EXCLUDE` | `INCLUDE` | SemiWeedNet is a DNN-based semi-supervised semantic segmentation method for weed and crop identification on a publicly available dataset, reporting re... |
| `SCI-000134` | 2026 | Evaluating transformer- and CNN-based semantic segmentation  | `INCLUDE` | `EXCLUDE` | Transformer and CNN models (SegFormer, DPT, UPerNet, U-Net, DeepLabv3+, PSPNet) perform pixel-level semantic segmentation of sunflower inflorescences ... |
| `SCI-000487` | 2020 | Vine disease detection in UAV multispectral images using opt | `EXCLUDE` | `INCLUDE` | A fully-convolutional DL segmentation network classifies each vineyard pixel (shadow/ground/healthy/symptom) from fused UAV visible+infrared imagery f... |
| `SCI-000618` | 2022 | Detection and Counting of Maize Leaves Based on Two-Stage De | `INCLUDE` | `EXCLUDE` | Mask R-CNN (ResNet50 + SmoothLR) performs pixel-level instance segmentation of maize seedlings/leaves from UAV RGB images, reporting mask AP of 95.2% ... |
| `SCI-000810` | 2026 | AgriJetsonBench: External-Power-Referenced TensorRT Benchmar | `EXCLUDE` | `INCLUDE` | AgriJetsonBench is a reproducible deployment benchmark of crop/weed detection and segmentation models (including SegFormer-B0) on NVIDIA Jetson AGX Or... |
| `SCI-001088` | 2026 | Machine Learning-Based Instance Segmentation of Potato Virus | `EXCLUDE` | `INCLUDE` | YOLOv26-based instance segmentation localizes Potato Virus Y symptoms in seed-potato fields from UAV RGB imagery, reporting quantitative mask metrics ... |

---

## 4. Complete Audit Traceability
All individual batch decisions (`batch_NNN_decisions.json` and `batch_NNN_decisions_screener2.json`), adjudication panels (`_adjudication_resolved_group_1..6.json`), and comprehensive conflict details (`literature/conflicts.json`) are retained in the project repository for permanent audit compliance.