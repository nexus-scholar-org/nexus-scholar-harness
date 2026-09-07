# Conflict-of-Interest Audit

**Corpus**: 94 studies (post-audit); **run**: 2026-09-07T02:09:29.796033+01:00
**Method**: independent analyst read of extraction fulltext (parallel subagents); funding/acknowledgments/COI statements captured verbatim; industry entities tagged (`funding` / `affiliation` / `donated-equipment` / `tooling`); single severity-ordered label per study.

## Summary

| Label | Count |
|---|---|
| no-statement | 13 |
| academic-or-public | 18 |
| industry-money | 4 |
| industry-affiliation-or-equipment | 7 |
| declared-no-conflict | 52 |
| **Studies with any industry tie (money OR affiliation/equipment)** | **11** |
| — of which industry money | 4 |
| — of which industry affiliation / donated equipment | 7 |
| Analyst-label adjustments (no-statement -> relabel) | 9 |

Labels are severity-ordered: `industry-money` > `industry-affiliation-or-equipment` > `declared-no-conflict` > `academic-or-public` > `no-statement`. Vendor products merely used in methods are `tooling` and do NOT raise the label.

## Adjusted labels

Subagents occasionally used `no-statement` to mean "no COI section" even when a funding/COI statement exists; a deterministic relabel was applied (recorded per study in the JSON output).

| ID | Final label |
|---|---|
| SCI-000010 | academic-or-public |
| SCI-000012 | academic-or-public |
| SCI-000013 | academic-or-public |
| SCI-000017 | academic-or-public |
| SCI-000075 | academic-or-public |
| SCI-000083 | declared-no-conflict |
| SCI-000089 | declared-no-conflict |
| SCI-000092 | declared-no-conflict |
| SCI-000129 | declared-no-conflict |

## Industry-money studies

SCI-000067, SCI-000225, SCI-001005, SCI-001406

## Industry affiliation / donated-equipment studies

SCI-000016, SCI-000084, SCI-000136, SCI-000180, SCI-000683, SCI-000708, SCI-001090

## Top tagged industry entities (non-tooling)

| Entity | Kind | Studies |
|---|---|---|
| Exprivia S.p.A. | funding | 2 |
| NVIDIA Corporation | donated-equipment | 1 |
| IT+Robotics Srl | affiliation | 1 |
| Xmobots Aeroespacial e Defesa | donated-equipment | 1 |
| Pakistan Tobacco Company | donated-equipment | 1 |
| BASF Canada Inc. | donated-equipment | 1 |
| Bayer Crop Science Canada | donated-equipment | 1 |
| Pinduoduo (PDD Holdings) | funding | 1 |
| GEO-K s.r.l. | affiliation | 1 |
| Rakuten | affiliation | 1 |
| Naptaplaya co. | donated-equipment | 1 |
| Infosys Foundation | funding | 1 |

## Per-study detail (studies with tagged entities)

| ID | Year | Label | Entities |
|---|---|---|---|
| SCI-000016 | 2018 | industry-affiliation-or-equipment | NVIDIA Corporation (donated-equipment) |
| SCI-000067 | 2024 | industry-money | Exprivia S.p.A. (funding) |
| SCI-000084 | 2020 | industry-affiliation-or-equipment | IT+Robotics Srl (affiliation) |
| SCI-000136 | 2020 | industry-affiliation-or-equipment | Xmobots Aeroespacial e Defesa (donated-equipment) |
| SCI-000145 | 2023 | declared-no-conflict | Pakistan Tobacco Company (donated-equipment) |
| SCI-000180 | 2025 | industry-affiliation-or-equipment | BASF Canada Inc. (donated-equipment); Bayer Crop Science Canada (donated-equipment) |
| SCI-000203 | 2023 | declared-no-conflict | DJI (tooling); Hasselblad (tooling) |
| SCI-000225 | 2025 | industry-money | Pinduoduo (PDD Holdings) (funding) |
| SCI-000286 | 2024 | no-statement | NVIDIA (tooling); DJI (tooling) |
| SCI-000371 | 2024 | declared-no-conflict | DJI (tooling); NVIDIA (tooling); ENVI (tooling) |
| SCI-000440 | 2024 | no-statement | DJI (tooling); NVIDIA (tooling) |
| SCI-000482 | 2018 | academic-or-public | DJI (tooling) |
| SCI-000488 | 2023 | declared-no-conflict | DJI (tooling); Google (tooling) |
| SCI-000637 | 2025 | declared-no-conflict | DJI (tooling); Autel Robotics (tooling); Roboflow (tooling) |
| SCI-000650 | 2024 | declared-no-conflict | DJI (tooling); Jiangsu Dualix Spectral Imaging Technology Co., Ltd. (tooling); Agisoft LLC (tooling) |
| SCI-000669 | 2025 | declared-no-conflict | DJI (tooling); NVIDIA (tooling) |
| SCI-000683 | 2025 | industry-affiliation-or-equipment | GEO-K s.r.l. (affiliation); NVIDIA (tooling); ArduCam (tooling); Roboflow (tooling); Sony (tooling); u-blox (tooling) |
| SCI-000708 | 2022 | industry-affiliation-or-equipment | Rakuten (affiliation); DJI (tooling); MAPIR (tooling); NVIDIA (tooling) |
| SCI-000754 | 2025 | declared-no-conflict | Google Colab (T4 GPU) (tooling); NVIDIA (tooling); Google Coral TPU (tooling) |
| SCI-000810 | 2026 | declared-no-conflict | NVIDIA (tooling); NVIDIA (tooling); ONNX (tooling); Texas Instruments (tooling) |
| SCI-000816 | 2026 | no-statement | DJI (tooling); Elsevier (Mendeley Data) (tooling) |
| SCI-000852 | 2025 | academic-or-public | NVIDIA (tooling); ArduCam (tooling); Sony (tooling); Monsoon Solutions (tooling); NVIDIA (tooling) |
| SCI-001005 | 2023 | industry-money | Exprivia S.p.A. (funding) |
| SCI-001085 | 2026 | academic-or-public | Rockchip (tooling); Orange Pi (tooling); Ultralytics (tooling); RKNN (tooling) |
| SCI-001090 | 2026 | industry-affiliation-or-equipment | Naptaplaya co. (donated-equipment) |
| SCI-001096 | 2026 | declared-no-conflict | DJI (tooling); Dronelink (tooling); WebODM (tooling); NVIDIA (tooling) |
| SCI-001173 | 2020 | academic-or-public | DJI (tooling); ASUS (tooling); Logitech (tooling); NVIDIA (tooling); TensorFlow (tooling) |
| SCI-001203 | 2024 | declared-no-conflict | DJI (tooling); Agisoft (tooling); Labelme (tooling); NVIDIA (tooling) |
| SCI-001210 | 2021 | academic-or-public | DJI (tooling) |
| SCI-001292 | 2026 | academic-or-public | NVIDIA (tooling); NVIDIA Jetson (tooling); PyTorch (tooling) |
| SCI-001305 | 2023 | declared-no-conflict | DJI (tooling); Pix4D (tooling); Labelme (tooling); NVIDIA (tooling); TensorFlow/Keras (tooling) |
| SCI-001333 | 2021 | declared-no-conflict | DJI (tooling); DJI GS PRO (tooling); LabelMe (tooling); NVIDIA (tooling); NVIDIA TensorRT (tooling); NVIDIA (tooling); TensorFlow (tooling) |
| SCI-001334 | 2025 | declared-no-conflict | DJI (tooling); NVIDIA (tooling) |
| SCI-001335 | 2025 | academic-or-public | AliCloud (Tianchi) (tooling) |
| SCI-001368 | 2023 | academic-or-public | DJI (tooling); Pix4D (tooling); Esri (ArcGIS) (tooling) |
| SCI-001371 | 2024 | declared-no-conflict | DJI (tooling); Baidu (PP-LiteSeg) (tooling) |
| SCI-001376 | 2025 | no-statement | DJI (Mini 2 SE) (tooling) |
| SCI-001379 | 2023 | academic-or-public | NVIDIA (tooling) |
| SCI-001382 | 2025 | no-statement | Resonon (Pika L) (tooling); NVIDIA (tooling) |
| SCI-001406 | 2021 | industry-money | Infosys Foundation (funding); MicaSense (tooling) |
| SCI-001411 | 2026 | declared-no-conflict | DJI (tooling); AgriBrain (phenoAI air) (tooling) |
| SCI-001413 | 2025 | declared-no-conflict | DJI (tooling); Pix4D (tooling) |

## Studies with no statement available

SCI-000001, SCI-000003, SCI-000040, SCI-000074, SCI-000138, SCI-000286, SCI-000440, SCI-000514, SCI-000816, SCI-000980, SCI-001081, SCI-001376, SCI-001382

## Caution: declared-no-conflict with non-tooling entity tags

Analysts declared no financial conflict while still tagging a non-tooling entity (e.g. field access, donated data). Review verbatim quotes in the JSON output.

SCI-000145

## Methodological note

- Government/academic/university grants are NOT industry entities; they map to `academic-or-public` or `declared-no-conflict` when an explicit declaration exists.
- `industry-money` = any funding/salary/equity from a private-sector company (incl. corporate foundations); `industry-affiliation-or-equipment` = author employed by industry or equipment/data donated by industry without cash.
- Seed/variety donations from agrochemical companies (e.g. BASF, Bayer) are tagged `donated-equipment`.
- Verbatim statements and evidence are recorded per study in the JSON output for independent verification.
- Regenerate with `scholar-verify coi --workspace <dir>`; relabel rule: no-statement with a COI statement -> declared-no-conflict; no-statement with only funding -> academic-or-public; non-tooling entities upgrade to the matching industry label; adjustments recorded on each row.
