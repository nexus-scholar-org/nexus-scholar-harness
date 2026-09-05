# Open-Science Artifact Scan (Data / Code Availability)

**Corpus**: 94 studies (post-audit); **run**: 2026-09-05T19:25:23.147564+01:00
**Method**: analyst read of extraction fulltext (8 parallel subagents), validated labels, cross-checked against a deterministic regex baseline.

## Summary

| Category | Data (DAS) | Code (CAS) |
|---|---|---|
| public+link | 21 | 18 |
| request-only | 22 | 3 |
| statement-only | 11 | 2 |
| explicitly-unavailable | 2 | 0 |
| not-stated | 38 | 71 |
| Studies with at least one repo/data link anywhere | 29 | — |
| Studies with BOTH public data and public code links | 11 | — |
| Regex-baseline agreement (DAS / CAS) | 64 / 76 | — |

Interpretation: `public+link` claims are independently verifiable; `request-only` and `statement-only` cannot be checked from the record alone.

## Per-study classification (any signal)

| ID | Year | DAS | CAS | Links | Regex DAS/CAS |
|---|---|---|---|---|---|
| SCI-000005 | 2026 | public+link | statement-only | https://doi.org/10.21227/f8e1-5934 | statement-only/not-stated |
| SCI-000007 | 2026 | request-only | not-stated | — | request-only/not-stated |
| SCI-000013 | 2026 | public+link | statement-only | https://doi.org/10.5281/zenodo.18233335 | statement-only/not-stated |
| SCI-000016 | 2018 | public+link | not-stated | https://goo.gl/ZsgeCV | statement-only/not-stated |
| SCI-000017 | 2025 | public+link | public+link | https://github.com/GFZ/weedsgalore | public+link/public+link |
| SCI-000040 | 2026 | not-stated | public+link | https://github.com/irene7c/DAS-SK.git | public+link/public+link |
| SCI-000067 | 2024 | not-stated | public+link | https://github.com/pasqualedem/RoWeeder | not-stated/statement-only |
| SCI-000075 | 2024 | statement-only | not-stated | — | statement-only/not-stated |
| SCI-000083 | 2026 | public+link | not-stated | https://doi.org/10.5281/zenodo.19422418 | statement-only/not-stated |
| SCI-000089 | 2022 | statement-only | not-stated | — | statement-only/not-stated |
| SCI-000091 | 2023 | public+link | not-stated | https://figshare.com/articles/dataset | statement-only/not-stated |
| SCI-000092 | 2020 | not-stated | public+link | https://github.com/kehuantiantang/A-DNN-based-Semantic-Segmentation-for-Detecting-Weed-and-Crop | public+link/public+link |
| SCI-000129 | 2026 | request-only | not-stated | — | request-only/not-stated |
| SCI-000145 | 2023 | public+link | public+link | https://data.mendeley.com/v1/datasets/5dpc5gbgpz/draft?a=888c40e2-c349-4c1a-ab69-0f478c6980c5; https://1drv.ms/u/s!Ao5jMGloq7Xlg70uK9br2hRbNvtClA?E=PfrWFq; https://1drv.ms/u/s!Ao5jMGloq7Xlg79dHZX7tU3e9POB3w?E=3NmilR | request-only/not-stated |
| SCI-000149 | 2024 | request-only | not-stated | — | request-only/not-stated |
| SCI-000160 | 2026 | public+link | public+link | https://doi.org/10.17632/mb4jvxk9dk.1; https://github.com/patitostyle/weed-detection-barley-rapeseed | public+link/public+link |
| SCI-000180 | 2025 | request-only | not-stated | — | request-only/not-stated |
| SCI-000203 | 2023 | public+link | public+link | https://github.com/grimmlab/DeBlurWeedSeg; https://data.mendeley.com/datasets/k4gvsjv4t3/1 | public+link/public+link |
| SCI-000271 | 2024 | statement-only | not-stated | — | statement-only/not-stated |
| SCI-000346 | 2026 | public+link | public+link | https://github.com/MuhammadIrfan92/PRC_Net | public+link/public+link |
| SCI-000371 | 2024 | not-stated | public+link | https://github.com/iremulku/Semantic-Segmentation-in-Precision-Agriculture | statement-only/statement-only |
| SCI-000488 | 2023 | public+link | public+link | https://zenodo.org/record/6697343; https://github.com/dahalsweekar/Deep-Weed-Segmentation | public+link/public+link |
| SCI-000489 | 2023 | request-only | public+link | https://github.com/JunfengGaolab/weed-mapping-with-cross-domain-learning/tree/master | public+link/public+link |
| SCI-000501 | 2022 | public+link | public+link | https://doi.org/10.17632/4hh45vkp38.4; https://github.com/grimmlab/UAVWeedSegmentation | public+link/public+link |
| SCI-000505 | 2025 | request-only | not-stated | — | request-only/not-stated |
| SCI-000548 | 2021 | request-only | not-stated | — | request-only/not-stated |
| SCI-000570 | 2022 | request-only | not-stated | — | request-only/statement-only |
| SCI-000618 | 2022 | statement-only | not-stated | — | public+link/public+link |
| SCI-000624 | 2022 | statement-only | not-stated | — | public+link/public+link |
| SCI-000637 | 2025 | public+link | not-stated | https://app.roboflow.com/pest-i22ng/weed-ge616/1; https://universe.roboflow.com/jeho/weed-lkwvk/ | statement-only/not-stated |
| SCI-000650 | 2024 | request-only | not-stated | — | request-only/not-stated |
| SCI-000669 | 2025 | request-only | not-stated | — | public+link/not-stated |
| SCI-000683 | 2025 | public+link | public+link | https://gitlab.fri.uni-lj.si/lrk/agriadapt-electronics; https://app.roboflow.com/agriadaptweeddetection/agriadapt-uex2n/overview | statement-only/not-stated |
| SCI-000708 | 2022 | statement-only | not-stated | — | public+link/public+link |
| SCI-000754 | 2025 | statement-only | not-stated | — | statement-only/not-stated |
| SCI-000810 | 2026 | request-only | request-only | — | request-only/statement-only |
| SCI-000816 | 2026 | public+link | public+link | https://doi.org/10.17632/k4gvsjv4t3.1; https://github.com/grimmlab/DeBlurWeedSeg; https://doi.org/10.5281/zenodo.20680100 | public+link/public+link |
| SCI-000852 | 2025 | not-stated | public+link | https://gitlab.fri.uni-lj.si/lrk/agriadapt/ | statement-only/statement-only |
| SCI-000878 | 2026 | request-only | request-only | — | request-only/not-stated |
| SCI-000881 | 2026 | statement-only | not-stated | — | statement-only/not-stated |
| SCI-000890 | 2025 | public+link | not-stated | https://data.mendeley.com/datasets/vt4s83pxx6/1; https://doi.org/10.17632/vt4s83pxx6.1 | not-stated/not-stated |
| SCI-000898 | 2025 | request-only | request-only | — | request-only/not-stated |
| SCI-000903 | 2024 | request-only | not-stated | — | request-only/not-stated |
| SCI-000962 | 2023 | request-only | not-stated | — | request-only/not-stated |
| SCI-000968 | 2021 | request-only | not-stated | — | request-only/not-stated |
| SCI-000981 | 2025 | statement-only | not-stated | — | statement-only/not-stated |
| SCI-001017 | 2026 | public+link | not-stated | https://github.com/JorgePazos-git/Dataset-of-weeds-in-potato-crops-in-the-province-of-Carchi-and-Imbabura-in- | public+link/public+link |
| SCI-001023 | 2025 | request-only | not-stated | — | request-only/not-stated |
| SCI-001029 | 2024 | request-only | not-stated | — | statement-only/not-stated |
| SCI-001053 | 2024 | request-only | not-stated | — | request-only/not-stated |
| SCI-001096 | 2026 | public+link | public+link | https://github.com/ArturoDuarteR/Semantic-Segmentation-in-Orthomosaics.git | public+link/public+link |
| SCI-001153 | 2021 | explicitly-unavailable | not-stated | — | statement-only/not-stated |
| SCI-001203 | 2024 | request-only | not-stated | — | request-only/not-stated |
| SCI-001210 | 2021 | public+link | not-stated | https://faculty.nuist.edu.cn/huanhai/zh_CN/zhym/62898/list/index.htm | not-stated/not-stated |
| SCI-001292 | 2026 | not-stated | public+link | https://github.com/chenfh21/RPD-Net; https://github.com/PRBonn/phenobench-baselines/tree/main/semantic segmentation | not-stated/public+link |
| SCI-001305 | 2023 | request-only | not-stated | — | request-only/not-stated |
| SCI-001333 | 2021 | explicitly-unavailable | not-stated | — | statement-only/not-stated |
| SCI-001334 | 2025 | public+link | public+link | https://github.com/AkramSyed002/MSEA_Net; https://github.com/CoFly-Project/CoFly-WeedDB; https://data.mendeley.com/datasets/4hh45vkp38/5 | public+link/public+link |
| SCI-001335 | 2025 | public+link | not-stated | https://tianchi.aliyun.com/dataset/dataDetail?dataId=74952 | not-stated/not-stated |
| SCI-001371 | 2024 | request-only | not-stated | — | request-only/not-stated |
| SCI-001376 | 2025 | not-stated | not-stated | https://agri-vision.github.io/AgriVision/; http://arxiv.org/abs/2502.08233 | not-stated/statement-only |
| SCI-001411 | 2026 | statement-only | not-stated | — | statement-only/not-stated |
| SCI-001413 | 2025 | statement-only | not-stated | — | statement-only/not-stated |

## Studies without any statement

SCI-000001, SCI-000003, SCI-000010, SCI-000012, SCI-000074, SCI-000084, SCI-000136, SCI-000138, SCI-000225, SCI-000286, SCI-000440, SCI-000482, SCI-000483, SCI-000492, SCI-000514, SCI-000547, SCI-000555, SCI-000565, SCI-000582, SCI-000980, SCI-001005, SCI-001046, SCI-001081, SCI-001084, SCI-001085, SCI-001090, SCI-001173, SCI-001368, SCI-001379, SCI-001382, SCI-001406

## Analyst vs regex-baseline disagreements

Diffs reflect false positives in the regex pass (third-party github/tool mentions) or statements the regex missed (reference-list "Available:" URLs).

| ID | DAS analyst/baseline | CAS analyst/baseline |
|---|---|---|
| SCI-000005 | public+link/statement-only | statement-only/not-stated |
| SCI-000013 | public+link/statement-only | statement-only/not-stated |
| SCI-000016 | public+link/statement-only | not-stated/not-stated |
| SCI-000040 | not-stated/public+link | public+link/public+link |
| SCI-000067 | not-stated/not-stated | public+link/statement-only |
| SCI-000083 | public+link/statement-only | not-stated/not-stated |
| SCI-000084 | not-stated/statement-only | not-stated/not-stated |
| SCI-000091 | public+link/statement-only | not-stated/not-stated |
| SCI-000092 | not-stated/public+link | public+link/public+link |
| SCI-000136 | not-stated/not-stated | not-stated/public+link |
| SCI-000145 | public+link/request-only | public+link/not-stated |
| SCI-000286 | not-stated/explicitly-unavailable | not-stated/not-stated |
| SCI-000371 | not-stated/statement-only | public+link/statement-only |
| SCI-000440 | not-stated/statement-only | not-stated/not-stated |
| SCI-000489 | request-only/public+link | public+link/public+link |
| SCI-000514 | not-stated/statement-only | not-stated/not-stated |
| SCI-000565 | not-stated/statement-only | not-stated/not-stated |
| SCI-000570 | request-only/request-only | not-stated/statement-only |
| SCI-000582 | not-stated/statement-only | not-stated/not-stated |
| SCI-000618 | statement-only/public+link | not-stated/public+link |
| SCI-000624 | statement-only/public+link | not-stated/public+link |
| SCI-000637 | public+link/statement-only | not-stated/not-stated |
| SCI-000669 | request-only/public+link | not-stated/not-stated |
| SCI-000683 | public+link/statement-only | public+link/not-stated |
| SCI-000708 | statement-only/public+link | not-stated/public+link |
| SCI-000810 | request-only/request-only | request-only/statement-only |
| SCI-000852 | not-stated/statement-only | public+link/statement-only |
| SCI-000878 | request-only/request-only | request-only/not-stated |
| SCI-000890 | public+link/not-stated | not-stated/not-stated |
| SCI-000898 | request-only/request-only | request-only/not-stated |
| SCI-001017 | public+link/public+link | not-stated/public+link |
| SCI-001029 | request-only/statement-only | not-stated/not-stated |
| SCI-001085 | not-stated/statement-only | not-stated/not-stated |
| SCI-001153 | explicitly-unavailable/statement-only | not-stated/not-stated |
| SCI-001210 | public+link/not-stated | not-stated/not-stated |
| SCI-001333 | explicitly-unavailable/statement-only | not-stated/not-stated |
| SCI-001335 | public+link/not-stated | not-stated/not-stated |
| SCI-001376 | not-stated/not-stated | not-stated/statement-only |
| SCI-001379 | not-stated/not-stated | not-stated/statement-only |

## Methodological note

- Labels follow TOP-level semantics: `public+link` requires an explicit availability statement plus an identifiable URL/DOI.
- Third-party tooling references (e.g. cited libraries or benchmarks) are not counted as the authors' code availability.
- Raw analyst evidence (verbatim snippets) is recorded per study in `open_science_artifacts.json`.
- Regenerate the aggregate with `uv run python phase4/open_science_aggregate.py`; raw chunk inputs are frozen in `_agent_results/`.
