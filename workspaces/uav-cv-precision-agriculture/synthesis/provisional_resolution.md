# Provisional Inclusion Resolution (39 studies — CAVEAT_EXC06_FULLTEXT_VERIFICATION)

Decision rule: CONFIRMED if a QUANTITATIVE segmentation benchmark metric exists (fulltext where retrieved, else abstract); EXCLUDED under EXC-06 otherwise. This is a manuscript-side resolution note; pipeline files are untouched.

## Resolution v2026-09-09 (post full-text read-through)

The 13 REVIEW_REQUIRED records were re-checked on 2026-09-09 during the full-corpus claim audit (`synthesis/fulltext_claim_audit.md`, `synthesis/fulltext_audit/`): **none has a route-B fulltext extraction, an extracted Markdown fulltext, or a PDF** (paywalled or restricted venues). Policy applied: **unretrievable-on-fulltext = excluded from the quantitative corpus**, documented in the PRISMA flow (`synthesis/prisma_2020_flow.md`, §3) rather than remaining "under manual review". Effective resolution buckets therefore are CONFIRMED=4, PENDING (CONFIRMED_PENDING_FULLTEXT)=9, EXCLUDE_TOPIC=8, EXCLUDE_EXC06=5, EXCLUDED_UNRETRIEVED=13 (39 total).

| # | Study | Year | Resolution | Justification |
|---|---|---|---|---|
Counts: CONFIRMED=4 | CONFIRMED_PENDING_FULLTEXT=9 | EXCLUDE_TOPIC=8 | EXCLUDE_EXC06=5 | EXCLUDED_UNRETRIEVED=13 (of 39 total)

## Bucket summaries

### CONFIRMED (4)
SCI-000010, SCI-000129, SCI-000440, SCI-000650

### CONFIRMED_PENDING_FULLTEXT (9)
SCI-000369, SCI-000397, SCI-000575, SCI-000877, SCI-000902, SCI-000910, SCI-001166, SCI-001221, SCI-001399

### EXCLUDE_TOPIC (8)
SCI-000416, SCI-000441, SCI-000442, SCI-000450, SCI-000451, SCI-000934, SCI-001445, SCI-001480

### EXCLUDE_EXC06 (5)
SCI-000002, SCI-000110, SCI-000148, SCI-000274, SCI-000639

### EXCLUDED_UNRETRIEVED (13) — formerly REVIEW_REQUIRED; excluded after 2026-09-09 full-text check
Policy: no route-B fulltext extraction / extracted MD / PDF exists for any of these (paywalled or restricted venues). Removed from quantitative corpus; tracked in PRISMA flow as unresolved-unretrieved.
SCI-000095, SCI-000140, SCI-000315, SCI-000398, SCI-000408, SCI-000411, SCI-000426, SCI-000433, SCI-000434, SCI-000439, SCI-000446, SCI-000666, SCI-001127

| SCI-000002 | Adaptive Path Planning for UAV-based Multi-Resolution Semantic Segment | 2021 | EXCLUDE_EXC06 | Adjudicator statement: no concrete quantitative segmentation metric in fulltext. |
| SCI-000010 | Semi-supervised GAN for Classification of Multispectral Imagery Acquir | 2019 | CONFIRMED | Fulltext extraction: F1=0.85 |
| SCI-000095 | Unmanned Aerial Vehicle (UAV) in Precision Agriculture to Identify the | 2023 | EXCLUDED_UNRETRIEVED | Metric keyword in abstract but no explicit numeric value — verify manually. |
| SCI-000110 | Optimization of Coverage Path Planning for Agricultural Drones in Weed | 2025 | EXCLUDE_EXC06 | Adjudicator statement: no concrete quantitative segmentation metric in fulltext. |
| SCI-000129 | Multispectral image fusion and attention-driven deep learning for prec | 2026 | CONFIRMED | Fulltext extraction: mIoU=0.9656, F1=0.9876, PA=0.988 |
| SCI-000140 | Mapping the future of farm management: A comprehensive analysis of app | 2024 | EXCLUDED_UNRETRIEVED | No numeric segmentation metric observable in abstract; no fulltext. |
| SCI-000148 | Sustainable Cotton Crop Productivity through Precision Weed Detection: | 2025 | EXCLUDE_EXC06 | Adjudicator statement: no concrete quantitative segmentation metric in fulltext. |
| SCI-000274 | A real-time efficient object segmentation system based on U-Net using  | 2021 | EXCLUDE_EXC06 | Adjudicator statement: no concrete quantitative segmentation metric in fulltext. |
| SCI-000315 | Deteksi Objek Pohon Secara Real-Time dari Udara Menggunakan YOLOv8 pad | 2026 | EXCLUDED_UNRETRIEVED | Metric keyword in abstract but no explicit numeric value — verify manually. |
| SCI-000369 | A Real-Time Aerial Semantic Segmentation System Based on U-Net Deep Le | 2025 | CONFIRMED_PENDING_FULLTEXT | Segmentation/benchmark paper by title; fulltext not retrieved (PDF missing), numeric metrics expected. |
| SCI-000397 | Semantic segmentation performance of aerial image segmentation using w | 2026 | CONFIRMED_PENDING_FULLTEXT | Segmentation/benchmark paper by title; fulltext not retrieved (PDF missing), numeric metrics expected. |
| SCI-000398 | Unmanned Aerial Vehicle (UAV)-Based Hyperspectral Imaging System for P | 2020 | EXCLUDED_UNRETRIEVED | No numeric segmentation metric observable in abstract; no fulltext. |
| SCI-000408 | Enhanced Agricultural Productivity: UAV-Based Technology for Precision | 2025 | EXCLUDED_UNRETRIEVED | No numeric segmentation metric observable in abstract; no fulltext. |
| SCI-000411 | Precision Agriculture and Unmanned Aerial Vehicles (UAVs) | 2020 | EXCLUDED_UNRETRIEVED | No numeric segmentation metric observable in abstract; no fulltext. |
| SCI-000416 | Real-time detection of cracks in tiled sidewalks using YOLO-based meth | 2023 | EXCLUDE_TOPIC | Off-scope topic ('Real-time detection of cracks in tiled sidewalks using YOLO-based meth') — not UAV crop/weed segmentation. |
| SCI-000426 | Real-time monitoring using unmanned aerial vehicle (UAV) | 2024 | EXCLUDED_UNRETRIEVED | No numeric segmentation metric observable in abstract; no fulltext. |
| SCI-000433 | Application of unmanned aerial systems to address real-world issues in | 2023 | EXCLUDED_UNRETRIEVED | No numeric segmentation metric observable in abstract; no fulltext. |
| SCI-000434 | 57. Optimizing peach management based on hyperspectral and unmanned ae | 2021 | EXCLUDED_UNRETRIEVED | Metric keyword in abstract but no explicit numeric value — verify manually. |
| SCI-000439 | Applications of UAV-AD (Unmanned Aerial Vehicle-Agricultural Drones) i | 2024 | EXCLUDED_UNRETRIEVED | No numeric segmentation metric observable in abstract; no fulltext. |
| SCI-000440 | On-Edge Weed Detection Using Unmanned Aerial Vehicles | 2024 | CONFIRMED | Fulltext extraction: mIoU=0.5192, Dice=0.6721 |
| SCI-000441 | The MR12-UAV Bombardier: A Cutting-Edge Unmanned Aerial Vehicle in Bom | 2023 | EXCLUDE_TOPIC | Off-scope topic ('The MR12-UAV Bombardier: A Cutting-Edge Unmanned Aerial Vehicle in Bom') — not UAV crop/weed segmentation. |
| SCI-000442 | Real-Time Vehicle Detection and Urban Traffic Behavior Analysis Based  | 2024 | EXCLUDE_TOPIC | Off-scope topic ('Real-Time Vehicle Detection and Urban Traffic Behavior Analysis Based ') — not UAV crop/weed segmentation. |
| SCI-000446 | Artificial Intelligence Implementation on Unmanned Aerial Vehicle for  | 2026 | EXCLUDED_UNRETRIEVED | No numeric segmentation metric observable in abstract; no fulltext. |
| SCI-000450 | Real-time human search and monitoring system using unmanned aerial veh | 2023 | EXCLUDE_TOPIC | Off-scope topic ('Real-time human search and monitoring system using unmanned aerial veh') — not UAV crop/weed segmentation. |
| SCI-000451 | High-Precision Time Synchronization Algorithm for Unmanned Aerial Vehi | 2023 | EXCLUDE_TOPIC | Off-scope topic ('High-Precision Time Synchronization Algorithm for Unmanned Aerial Vehi') — not UAV crop/weed segmentation. |
| SCI-000575 | Improved Real-Time Semantic Segmentation Network Model for Crop Vision | 2022 | CONFIRMED_PENDING_FULLTEXT | Segmentation/benchmark paper by title; fulltext not retrieved (PDF missing), numeric metrics expected. |
| SCI-000639 | CoFly: An automated, AI-based open-source platform for UAV precision a | 2023 | EXCLUDE_EXC06 | Adjudicator statement: no concrete quantitative segmentation metric in fulltext. |
| SCI-000650 | Harnessing UAVs and deep learning for accurate grass weed detection in | 2024 | CONFIRMED | Fulltext extraction: mIoU=0.888, F1=0.968 |
| SCI-000666 | Overcome the Fear Of Missing Out: Active sensing UAV scanning for prec | 2023 | EXCLUDED_UNRETRIEVED | Likely in scope with metrics not confidently abstracted; fulltext missing. |
| SCI-000877 | CamelinaWeed: an expert-agronomist-annotated UAV RGB and multispectral | 2026 | CONFIRMED_PENDING_FULLTEXT | Segmentation/benchmark paper by title; fulltext not retrieved (PDF missing), numeric metrics expected. |
| SCI-000902 | An instance segmentation dataset of cabbages over the whole growing se | 2024 | CONFIRMED_PENDING_FULLTEXT | Segmentation/benchmark paper by title; fulltext not retrieved (PDF missing), numeric metrics expected. |
| SCI-000910 | CoFly-WeedDB: A UAV image dataset for weed detection and species ident | 2022 | CONFIRMED_PENDING_FULLTEXT | Segmentation/benchmark paper by title; fulltext not retrieved (PDF missing), numeric metrics expected. |
| SCI-000934 | UAV-based real-time detection of corn earworm using EfficientNet and m | 2026 | EXCLUDE_TOPIC | Off-scope topic ('UAV-based real-time detection of corn earworm using EfficientNet and m') — not UAV crop/weed segmentation. |
| SCI-001127 | AI in weed management | 2025 | EXCLUDED_UNRETRIEVED | Metric keyword in abstract but no explicit numeric value — verify manually. |
| SCI-001166 | An Adaptive Spatial Network for UAV Image Real-Time Semantic Segmentat | 2022 | CONFIRMED_PENDING_FULLTEXT | Segmentation/benchmark paper by title; fulltext not retrieved (PDF missing), numeric metrics expected. |
| SCI-001221 | Semantic segmentation of remote sensing image based on Contextual U-Ne | 2023 | CONFIRMED_PENDING_FULLTEXT | Segmentation/benchmark paper by title; fulltext not retrieved (PDF missing), numeric metrics expected. |
| SCI-001399 | Real-Time Semantic Segmentation for UAV Perspectives on Embedded Platf | 2025 | CONFIRMED_PENDING_FULLTEXT | Segmentation/benchmark paper by title; fulltext not retrieved (PDF missing), numeric metrics expected. |
| SCI-001445 | Design and Implementation of Real-time Amphibious Unmanned Aerial Vehi | 2020 | EXCLUDE_TOPIC | Off-scope topic ('Design and Implementation of Real-time Amphibious Unmanned Aerial Vehi') — not UAV crop/weed segmentation. |
| SCI-001480 | Vision-Based UAV Navigation in Vineyards using a Disturbance-Aware NMP | 2025 | EXCLUDE_TOPIC | Off-scope topic ('Vision-Based UAV Navigation in Vineyards using a Disturbance-Aware NMP') — not UAV crop/weed segmentation. |
