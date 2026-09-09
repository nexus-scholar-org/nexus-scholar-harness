# D1 manuscript tables (compiled, journal-ready)

Compiled 2026-09-09 from `literature/extraction/merged/records.json` and
`synthesis/rq1_metric_reporting.md`. Identical text is embedded in the manuscript
(`d1_manuscript_draft.md`); keep in sync via `scripts/build_d1_tables.py`.

#### Table 1. Metric reporting rates across the 94-study corpus (RQ1)
| Metric | Studies reporting | Share of 94 | Note |
|---|---|---|---|
| mIoU | 64 | 68% | dominant single metric |
| F1 | 32 | 34% | incl. class-level crop/weed F1 |
| Dice | 19 | 20% | |
| Pixel accuracy (PA) | 36 | 38% | after quote-backed relabel of one OA mis-record |
| Mean pixel accuracy (mPA) | 10 | 11% | |
| Weed-class F1 | 5 | 5% | crop-level F1: 8 |
| ≥2 numeric metrics | 59 | 63% | reporting-rich minority |
| ≥1 numeric ambiguity flag | 73 | 78% | human reconciliation required before citation |
| Flight altitude | 59 | 63% | median 10 m |
| Ground sampling distance | 50 | 53% | of dataset records |

#### Table 2. Embedded true-edge cohort (RQ2, n = 15): measured runtime on embedded-class hardware
| Study | Device | FPS | Latency (ms) | Precision | Input (px) |
|---|---|---|---|---|---|
| SCI-000149 | NVIDIA Jetson AGX Xavier | — | 2.1 | TorchScript & ONNX (FP32) | 640 |
| SCI-001085 | Orange Pi 5+ (Rockchip RK3588, 6 TOPS NPU) | 62.5 | 16.0 | INT8 (post-training quantized RKNN) | 512 |
| SCI-000810 | NVIDIA Jetson AGX Orin 64GB and Jetson Orin Nano Super | 47.18 | 21.514 | INT8 (matched-budget 15 W) / FP16 (native) TensorRT | 640 |
| SCI-000669 | NVIDIA Jetson Orin Nano | 44.0 | — | FP32 | 256 |
| SCI-001333 | NVIDIA Jetson AGX Xavier | 40.16 | — | FP16 (TensorRT) | 352x480 |
| SCI-000683 | NVIDIA Jetson Nano | 30.6 | 32.7 | FP32 | 512 |
| SCI-000346 | NVIDIA Jetson TX2 (desktop comparison: Intel/GPU 10.53 ms) | 17.05 | 58.65 | not stated | 320 |
| SCI-001292 | NVIDIA Jetson TX2 (also RTX 3090 / CPU compared) | 7.0 | 142.9 | FP32 (reparameterized single-path inference) | 768 |
| SCI-000565 | NVIDIA Jetson TX2 | 4.5 | — | FP16 | 1000x1000 |
| SCI-000852 | NVIDIA Jetson Nano | 4.25 | 235 | FP32 | 512 |
| SCI-000286 | NVIDIA Jetson Nano | 3.69 | 271.29 | ONNX (PyTorch, CUDA) | 224 |
| SCI-000968 | Intel Core i7-1065G7 CPU (laptop) | 1.89 | 530 | not stated | 256x256 |
| SCI-000440 | NVIDIA Jetson Nano | 1.864 | 536.6 | FP16 (quantized) | None |
| SCI-000084 | NVIDIA Jetson TX2 | — | 600 | not stated | None |
| SCI-001173 | ASUS Tinker Board S (onboard) + backend server (4G LTE offload) | 1.43 | 700 | not stated | None |

#### Table 3. Risk of bias (QUADAS-2-adapted), n = 94 (RQ3)
| Domain | Low | Unclear | High / n/a |
|---|---|---|---|
| Patient / selection | 71 | 20 | 3 |
| Index condition (data + labels) | 10 | 72 | 12 |
| Flow / timing | 37 | 56 | 1 |
| Reporting / nature of target | 18 | 32 | 44 (n/a) |
| **Overall** | **2** | **77** | **15** |
