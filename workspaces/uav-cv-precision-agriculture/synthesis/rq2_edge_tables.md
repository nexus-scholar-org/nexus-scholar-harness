# RQ2 Edge-Inference Tables (Scaffold) — UAV CV Precision Agriculture

Auto-generated from `literature/extraction/merged/records.json` + `synthesis/synthesis_matrix.json`. True-edge = device reported AND (fps OR latency) measured on hardware. Quote snippets = extraction evidence, to curate in the manuscript.

## Diagnostics
- device reported = 46 | resolution = 70 | precision = 13 | fps = 28 | latency = 31 | params = 34 | FLOPs = 21
- true-edge cohort (device + runtime measured) = 30
- deployment class: embedded on-device = 16 | desktop/cloud accelerator = 20 | unspecified = 55
- NOTE: the pipeline's earlier `true_edge_studies=15` stat used a stricter definition (embedded-class board only); reconcile one canonical definition before the manuscript.

## Table A — all studies with device or runtime information

| Study | Device | Family | Prec | Res | FPS | Lat(ms) | W | Params(M) | GFLOPS | evidence (fps/lat) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---|
| SCI-000005 | None - post-flight workstati | Desktop/Server G | FP16 (in | 256 | 78.000 | 12.8 |  | 22.80 | 33.6 | The full model uses 22.8 M parameters, 33.6 GFLOPs, 2.60 GB FP16 memory, and run |
| SCI-000007 | Desktop workstation: NVIDIA  | -None- |  | 512 |  |  |  |  |  |  |
| SCI-000012 | None - offline (trained with | Efficiency-only |  | 512 |  |  |  | 42.04 |  |  |
| SCI-000013 | None - offline experimentati | -None- |  | 224 |  |  |  |  |  |  |
| SCI-000016 | NVIDIA Titan X GPU (desktop) | -None- |  | None |  |  |  |  |  |  |
| SCI-000040 | FPS measured on NVIDIA GeFor | Desktop/Server G |  | 1024 | 10.330 | 96.8 |  | 10.68 | 45.0 | On PhenoBench, DAS-SK reaches the best mIoU while remaining the most compact and |
| SCI-000067 | NVIDIA RTX 4090 (consumer GP | Desktop/Server G |  | 512 | 141.440 | 7.1 |  | 3.71 | 7.4 | RoWeeder (SegFormer) 3.71 7.84 7.07 (Params(M), GMACs, Inference time(ms)) |
| SCI-000074 | None stated - offline model  | -None- |  | 512 |  |  |  |  |  |  |
| SCI-000083 | Desktop PC: Intel i5-9300H C | Desktop/Server G |  | 480 | 22.900 | 43.7 |  | 32.52 | 17.9 | Ours, with ConvNeXt V2 Tiny 32.52 M 17.93 G 0.8990 0.8851 0.9424 0.9376 22.90 |
| SCI-000084 | NVIDIA Jetson TX2 | Jetson TX2 |  | None |  | 600.0 |  |  |  | The performance of VGG-UNet architecture has been tested on an embedded GPU boar |
| SCI-000129 | NVIDIA GeForce RTX 4090 GPU  | Desktop/Server G |  | 512 | 1611.000 | 0.6 |  | 2.10 | 55.6 | the inference time is 0.000621 s per image per instance |
| SCI-000149 | NVIDIA Jetson AGX Xavier | Jetson AGX Xavie | TorchScr | 640 |  | 2.1 |  |  |  | The inference speed of the architecture was 2.1 ms and 2.3 ms per image for C4 a |
| SCI-000160 | No inference hardware/platfo | -None- |  | 256 |  |  |  |  |  |  |
| SCI-000286 | NVIDIA Jetson Nano | Jetson Nano | ONNX (Py | 224 | 3.690 | 271.3 |  |  |  | The combined duration of the model and real-time inference is observed to be 271 |
| SCI-000346 | NVIDIA Jetson TX2 (desktop c | Jetson TX2 |  | 320 | 17.050 | 58.6 |  | 13.30 | 41.5 | PRC-Net (Proposed) 13.30 0.58 41.46 10.53 94.97 58.65 17.05 |
| SCI-000440 | NVIDIA Jetson Nano | Jetson Nano | FP16 (qu | None | 1.864 | 536.6 | 4.806 |  |  | U-Net 3.6858 0.2713 4.684 0.5366 1.864 4.806 (TF-Lite: inference(s) FPS power(W) |
| SCI-000483 | Cloud GPU server (training;  | -None- |  | 512 |  |  |  |  |  |  |
| SCI-000488 | None - offline (Google Colab | -None- |  | 256 |  |  |  |  |  |  |
| SCI-000505 | NVIDIA Tesla V100 32 GB (seg | Desktop/Server G |  | 256 | 2.500 | 400.0 |  |  |  | the inference speed of the ensemble segmentation model under this study's experi |
| SCI-000548 | NVIDIA RTX 2080 Super GPU | Desktop/Server G |  | 256 | 24.450 | 40.9 |  |  |  | ST 40.90 ms (modified U-Net, Table 5) |
| SCI-000565 | NVIDIA Jetson TX2 | Jetson TX2 | FP16 | 1000x1000 | 4.500 |  |  |  |  | GTX 1060 FP16 80.9 62.8 35.6 / Jetson TX2 FP16 80.9 62.8 4.5 |
| SCI-000618 | None - offline (NVIDIA Quadr | Desktop/Server G |  | 640 |  | 70.0 |  |  |  | The inference times for image detection boxes and masks were 0.05s and 0.07s, re |
| SCI-000650 | None - offline (NVIDIA GeFor | Desktop/Server G |  | 318 |  | 46.5 |  |  |  | The processing time for DeepLabV3+ is 46.5ms |
| SCI-000669 | NVIDIA Jetson Orin Nano | Jetson Orin | FP32 | 256 | 44.000 |  |  | 1.93 |  | The proposed MobileNetV4-Seg SS model achieved real-time (44 FPS) inference spee |
| SCI-000683 | NVIDIA Jetson Nano | Jetson Nano | FP32 | 512 | 30.600 | 32.7 | 10.000 | 2.50 | 6.6 | the measured inference times correspond to average frame rates of 30.6 FPS for S |
| SCI-000708 | NVIDIA Jetson Xavier NX | Jetson Xavier NX |  | 100 |  |  |  | 17.30 |  | we measure the inference speed per 12-MPx frame (3000 x 4000 pixel) in FPS, as w |
| SCI-000754 | Google Colab T4 GPU (trainin | Cloud GPU (Colab | AMP mixe | 224 |  | 18.5 |  | 115.00 | 22.0 | Inference latency averaged 18 ms per 224 x 224 image (batch size = 32), confirmi |
| SCI-000810 | NVIDIA Jetson AGX Orin 64GB  | Jetson Orin | INT8 (ma | 640 | 47.180 | 21.5 | 13.150 | 3.71 | 29.7 | SegFormer-B0 reached 47.18 FPS and 0.2808 J/inference versus 31.95 FPS and 0.501 |
| SCI-000816 | None - no on-device deployme | Efficiency-only |  | 128 |  |  |  | 24.40 | 3.9 |  |
| SCI-000852 | NVIDIA Jetson Nano | Jetson Nano | FP32 | 512 | 4.250 | 235.0 |  | 2.50 |  | FPS, ranging from 4.25 for the 100% width network to 9.09 for the 25% width |
| SCI-000878 | None - offline training/expe | Efficiency-only |  | 512 |  |  |  | 18.10 | 169.9 |  |
| SCI-000881 | None - offline research trai | -None- |  | 480 |  |  |  |  |  |  |
| SCI-000962 | Windows 10 desktop (AMD Ryze | Other |  | 512 | 143.300 |  |  | 10.60 | 32.1 | LW-Segnet 693.4 36.8 11.0 117.5 LW-Unet 603.7 32.1 10.6 143.3 |
| SCI-000968 | Intel Core i7-1065G7 CPU (la | CPU |  | 256x256 | 1.890 | 530.0 |  | 9.49 |  | processing speed 0.53 s per 256x256 image on Intel Core i7-1065G7 CPU |
| SCI-000981 | Desktop: NVIDIA GeForce RTX  | Desktop/Server G |  | 256 | 77.180 | 13.0 |  | 31.00 | 54.8 | MSU-Net ... Parameters 3.10 x 10^7, FLOPs/G 54.78, FPS/(f s-1) 77.18 |
| SCI-001017 | None - offline. Models train | Cloud GPU (Colab |  | 128 | 17.000 | 58.5 |  | 135.00 |  | a relatively fast inference time of 58.5 ms (17 fps) per 128 x 128 image patch ( |
| SCI-001053 | NVIDIA Tesla T4 GPU (Google  | -None- |  | 640 |  |  |  |  |  |  |
| SCI-001084 | No physical hardware deploye | Efficiency-only |  | 600 |  |  |  | 31.40 |  |  |
| SCI-001085 | Orange Pi 5+ (Rockchip RK358 | Rockchip RK3588 | INT8 (po | 512 | 62.500 | 16.0 |  |  |  | YOLOv11s-seg.rknn 0.85 0.79 0.85 16 |
| SCI-001090 | Not specified (training-time | -None- |  | None |  |  |  |  |  |  |
| SCI-001096 | Desktop workstation: NVIDIA  | Desktop/Server G |  | 224 | 112.400 | 8.9 |  |  |  | Inference times for Mask2Former and Swin-Transformer are comparable (~8-9 ms per |
| SCI-001173 | ASUS Tinker Board S (onboard | Tinker Board S |  | None | 1.430 | 700.0 |  |  |  | The average inference speed of the semantic image segmentation model is 0.7s wit |
| SCI-001292 | NVIDIA Jetson TX2 (also RTX  | Jetson TX2 | FP32 (re | 768 | 7.000 | 142.9 |  | 0.19 | 9.4 | The proposed model achieves 42.05 FPS on RTX 3090 and 7.0 FPS on Jetson TX2 |
| SCI-001333 | NVIDIA Jetson AGX Xavier | Jetson AGX Xavie | FP16 (Te | 800 | 40.160 |  |  | 17.39 | 10.7 | FFB-BiSeNetV2 40.16 fps on Jetson AGX Xavier (TensorRT FP16); MobileNetV2-UNet 4 |
| SCI-001379 | CPU (desktop) | CPU |  | 448 | 31.750 | 31.5 |  |  |  | FPN with VGG16 emerged as the most efficient, exhibiting the lowest average late |
| SCI-001411 | None - offline experiments o | -None- |  | 512 |  |  |  |  |  |  |
| SCI-000371 |  | Unknown / not st |  | 224 | 98.910 |  |  | 1.34 | 12.7 | Table 1: Performance comparison of real-time semantic segmentation architectures |
| SCI-000637 |  | Unknown / not st |  | 640 |  | 6.2 |  |  |  | The proposed model achieved an inference time of 6.2 ms per image, demonstrating |
| SCI-000903 |  | Unknown / not st |  | 640 |  | 30.8 |  |  | 110.4 | YOLOv8m NRG speed 30.8 ms (Table 5); test set 25.2 ms (Table 6) |
| SCI-001334 |  | Unknown / not st |  | 256 |  | 2.0 |  | 6.74 |  | MSEA-Net achieves an average inference time of 0.0020 s per image |
| SCI-001335 |  | Unknown / not st |  | 224 |  | 20.4 |  | 4.25 |  | MobileNetV2 ... Inference Time(s) 0.0204[4] |
| SCI-001371 |  | Unknown / not st |  | 512 | 12.300 |  |  | 12.08 | 9.0 | In terms of prediction speed, our model is able to predict 512 x 512-pixel UAV v |
| SCI-001376 |  | Unknown / not st |  | None |  | 6000.0 |  |  |  | The end-to-end latency from video capture to segmentation visualization in the S |
| SCI-001413 |  | Unknown / not st |  | 512 | 40.360 |  |  | 43.94 | 184.3 | FPS is introduced as an indicator to measure the processing speed of the semanti |

## Table B — TRUE-EDGE cohort (device + measured inference, split by deployment class)

### B1 — Embedded on-device (RQ2 core answer set; 15 studies)

| Study | Device | Family | Prec | Res | FPS | Lat(ms) | params | evidence |
|---|---|---|---|---:|---:|---:|---:|---|
| SCI-000084 | NVIDIA Jetson TX2 | Jetson TX2 |  | None |  | 600.0 |  | The performance of VGG-UNet architecture has been tested on an embedded GPU board, namely  |
| SCI-000149 | NVIDIA Jetson AGX Xavier | Jetson AGX Xavie | TorchScr | 640 |  | 2.1 |  | The inference speed of the architecture was 2.1 ms and 2.3 ms per image for C4 and C5 cate |
| SCI-000286 | NVIDIA Jetson Nano | Jetson Nano | ONNX (Py | 224 | 3.690 | 271.3 |  | The combined duration of the model and real-time inference is observed to be 271.29 millis |
| SCI-000346 | NVIDIA Jetson TX2 (desktop compa | Jetson TX2 |  | 320 | 17.050 | 58.6 | 13.30 | PRC-Net (Proposed) 13.30 0.58 41.46 10.53 94.97 58.65 17.05 |
| SCI-000440 | NVIDIA Jetson Nano | Jetson Nano | FP16 (qu | None | 1.864 | 536.6 |  | U-Net 3.6858 0.2713 4.684 0.5366 1.864 4.806 (TF-Lite: inference(s) FPS power(W); Tensor-R |
| SCI-000565 | NVIDIA Jetson TX2 | Jetson TX2 | FP16 | 1000x1000 | 4.500 |  |  | GTX 1060 FP16 80.9 62.8 35.6 / Jetson TX2 FP16 80.9 62.8 4.5 |
| SCI-000669 | NVIDIA Jetson Orin Nano | Jetson Orin | FP32 | 256 | 44.000 |  | 1.93 | The proposed MobileNetV4-Seg SS model achieved real-time (44 FPS) inference speed on Jetso |
| SCI-000683 | NVIDIA Jetson Nano | Jetson Nano | FP32 | 512 | 30.600 | 32.7 | 2.50 | the measured inference times correspond to average frame rates of 30.6 FPS for Squeeze U-N |
| SCI-000810 | NVIDIA Jetson AGX Orin 64GB and  | Jetson Orin | INT8 (ma | 640 | 47.180 | 21.5 | 3.71 | SegFormer-B0 reached 47.18 FPS and 0.2808 J/inference versus 31.95 FPS and 0.5013 J/infere |
| SCI-000852 | NVIDIA Jetson Nano | Jetson Nano | FP32 | 512 | 4.250 | 235.0 | 2.50 | FPS, ranging from 4.25 for the 100% width network to 9.09 for the 25% width |
| SCI-000968 | Intel Core i7-1065G7 CPU (laptop | CPU |  | 256x256 | 1.890 | 530.0 | 9.49 | processing speed 0.53 s per 256x256 image on Intel Core i7-1065G7 CPU |
| SCI-001085 | Orange Pi 5+ (Rockchip RK3588, 6 | Rockchip RK3588 | INT8 (po | 512 | 62.500 | 16.0 |  | YOLOv11s-seg.rknn 0.85 0.79 0.85 16 |
| SCI-001173 | ASUS Tinker Board S (onboard) +  | Tinker Board S |  | None | 1.430 | 700.0 |  | The average inference speed of the semantic image segmentation model is 0.7s with segmenta |
| SCI-001292 | NVIDIA Jetson TX2 (also RTX 3090 | Jetson TX2 | FP32 (re | 768 | 7.000 | 142.9 | 0.19 | The proposed model achieves 42.05 FPS on RTX 3090 and 7.0 FPS on Jetson TX2 |
| SCI-001333 | NVIDIA Jetson AGX Xavier | Jetson AGX Xavie | FP16 (Te | 800 | 40.160 |  | 17.39 | FFB-BiSeNetV2 40.16 fps on Jetson AGX Xavier (TensorRT FP16); MobileNetV2-UNet 45.05 fps |

### B2 — Desktop/cloud accelerator (measured, but not edge hardware; 13 studies — auxiliary)

| Study | Device | Family | Prec | Res | FPS | Lat(ms) | params |
|---|---|---|---|---:|---:|---:|---:|
| SCI-000005 | None - post-flight workstation d | Desktop/Server G | FP16 (in | 256 | 78.000 | 12.8 | 22.80 |
| SCI-000040 | FPS measured on NVIDIA GeForce R | Desktop/Server G |  | 1024 | 10.330 | 96.8 | 10.68 |
| SCI-000083 | Desktop PC: Intel i5-9300H CPU,  | Desktop/Server G |  | 480 | 22.900 | 43.7 | 32.52 |
| SCI-000129 | NVIDIA GeForce RTX 4090 GPU (des | Desktop/Server G |  | 512 | 1611.000 | 0.6 | 2.10 |
| SCI-000505 | NVIDIA Tesla V100 32 GB (segment | Desktop/Server G |  | 256 | 2.500 | 400.0 |  |
| SCI-000548 | NVIDIA RTX 2080 Super GPU | Desktop/Server G |  | 256 | 24.450 | 40.9 |  |
| SCI-000618 | None - offline (NVIDIA Quadro RT | Desktop/Server G |  | 640 |  | 70.0 |  |
| SCI-000650 | None - offline (NVIDIA GeForce R | Desktop/Server G |  | 318 |  | 46.5 |  |
| SCI-000962 | Windows 10 desktop (AMD Ryzen 7  | Other |  | 512 | 143.300 |  | 10.60 |
| SCI-000981 | Desktop: NVIDIA GeForce RTX 3080 | Desktop/Server G |  | 256 | 77.180 | 13.0 | 31.00 |
| SCI-001017 | None - offline. Models trained a | Cloud GPU (Colab |  | 128 | 17.000 | 58.5 | 135.00 |
| SCI-001096 | Desktop workstation: NVIDIA GeFo | Desktop/Server G |  | 224 | 112.400 | 8.9 |  |
| SCI-001379 | CPU (desktop) | CPU |  | 448 | 31.750 | 31.5 |  |

## Table D — TARGET-EDGE (measured on accelerator but paper argues deployment on embedded; flag for careful reading — do NOT cite as on-device evidence)

| Study | Device | Family | Prec | Res | FPS | Lat(ms) | evidence |
|---|---|---|---|---:|---:|---:|---|
| SCI-000067 | NVIDIA RTX 4090 (consumer GPU; pap | Desktop/Server G |  | 512 | 141.440 | 7.1 | RoWeeder (SegFormer) 3.71 7.84 7.07 (Params(M), GMACs, Inference time(ms)) |
| SCI-000754 | Google Colab T4 GPU (training and  | Cloud GPU (Colab | AMP mixe | 224 |  | 18.5 | Inference latency averaged 18 ms per 224 x 224 image (batch size = 32), confirming real-ti |
| SCI-000816 | None - no on-device deployment per | Efficiency-only |  | 128 |  |  |  |

### D1 — Target-edge evidence note (read on 2026-09-09; verbatim from source full texts)

- **SCI-000067 (RoWeeder, Marinis et al. 2024):** "Inference time was calculated on a single NVIDIA RTX 4090, a consumer-grade GPU, which is more powerful than a typical edge device … Future work will focus on testing the model on edge devices to evaluate its performance in real-world scenarios." → 7.07 ms / 141 FPS is RTX 4090-only; **no on-board measurement reported**.
- **SCI-000754 (AgroVisionNet, Mahareek et al. 2025):** "Inference latency averaged 18 ms per 224 x 224 image (batch size = 32), confirming real-time feasibility for UAV and field-robot deployment" (measured on Google Colab T4); "In future research, we aim to (1) optimize AgroVisionNet for edge deployment through model compression techniques such as pruning, quantization, and knowledge distillation" → T4-only; **no on-board measurement reported**.
- Action: both rows are excluded from the embedded on-device cohort and must NOT be cited as on-device evidence. Optionally cite them in the Discussion as examples of the "claimed vs measured" deployment reporting gap.

## Table C — device deployed but no measured fps/latency (efficiency-only); flag for primary-justification checks

| Study | Device | Family | params | note |
|---|---|---|---|---|
| SCI-000007 | Desktop workstation: NVIDIA RT | -None- |  | PyTorch (PyTorch Lightning); AdamW optimizer LR 3e-5 (visual |
| SCI-000012 | None - offline (trained with 4 | Efficiency-only | 42.04 | TensorFlow (Adam optimizer, initial lr 0.005, batch size 24) |
| SCI-000013 | None - offline experimentation | -None- |  | PyTorch-based (SpecDeepMap API from EnMAP-Box, custom extens |
| SCI-000016 | NVIDIA Titan X GPU (desktop) | -None- |  |  |
| SCI-000074 | None stated - offline model tr | -None- |  | Deep-learning framework not explicitly named; training detai |
| SCI-000160 | No inference hardware/platform | -None- |  | Deep learning framework not stated in extracted text; models |
| SCI-000483 | Cloud GPU server (training; pe | -None- |  | PyTorch (batch size 4, SGD, cosine annealing LR 1e-2, dice l |
| SCI-000488 | None - offline (Google Colab c | -None- |  | Keras (Python), Adam optimizer lr 0.001, up to 100 epochs, e |
| SCI-000708 | NVIDIA Jetson Xavier NX | Jetson Xavier NX | 17.30 | TensorRT (network quantization and layer fusion/pruning) |
| SCI-000816 | None - no on-device deployment | Efficiency-only | 24.40 | PyTorch 2.1.0 + segmentation-models-pytorch library; torchvi |
| SCI-000878 | None - offline training/experi | Efficiency-only | 18.10 | PyTorch 2.8.0, Python 3.9.23, CUDA 12.8; AdamW lr 5e-5, 5-ep |
| SCI-000881 | None - offline research traini | -None- |  | PyTorch-based MMSegmentation 0.30.0 + mmcv-full 1.6.0, Pytho |
| SCI-001053 | NVIDIA Tesla T4 GPU (Google Co | -None- |  | PyTorch 2.1 / CUDA 12.2 (Python 3.12), Ultralytics (YOLO), D |
| SCI-001084 | No physical hardware deployed  | Efficiency-only | 31.40 |  |
| SCI-001090 | Not specified (training-time a | -None- |  |  |
| SCI-001411 | None - offline experiments on  | -None- |  | PyTorch 1.10 / CUDA 11.3 / Python 3.8 (Miniconda3); FCN/U-Ne |
