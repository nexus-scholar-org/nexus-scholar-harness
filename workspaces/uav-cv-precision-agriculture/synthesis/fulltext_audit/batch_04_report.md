# Full-text read-through batch 04

## SCI-000582 — Accurate Weed Mapping and Prescription Map Generation Based on Fully Convolutional Networks Using UAV Imagery

attribution: CONFIRMED for model=Modified FCN-4s backbone=VGG-16 (ImageNet-pretrained CNN fine-tuned into an FCN; text never names "VGG-16" literally) dataset=Self-collected UAV rice field (3 classes: rice, weeds, others)

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.8473 | CONFIRMED | Table 3: "FCN-8s 0.9096 0.8303 0.413 s 24.8 min Deeplab 0.9191 0.8460 5.279 s 39.6 min FCN-4s 0.9196 0.8473 0.356 s 24.7 min" (line 197); abstract: "the overall accuracy and mean intersection over union (mean IU) for weed mapping using FCN-4s were 0.9196 and 0.8473" (line 52) |
| PA | 0.9196 | CONFIRMED | "the overall accuracy and mean intersection over union (mean IU) for weed mapping using FCN-4s were 0.9196 and 0.8473" (line 52); Table 3 OA column: "FCN-4s 0.9196..." (line 197) |

## SCI-000618 — Detection and Counting of Maize Leaves Based on Two-Stage Deep Learning with UAV-Based RGB Image

attribution: CONFIRMED for model=Mask R-CNN with ResNet50 + SmoothLR loss backbone=ResNet50 (Mask R-CNN, via MMDetection) dataset=self-collected UAV RGB maize seedlings. "Mask R-CNN with Resnet50 and SmoothLR was selected as the optimal instance segmentation model" (line 321).

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| device | None - offline (NVIDIA Quadro RTX 8000 48 GB, Intel Xeon Gold 6246R, 128 GB RAM, Windows 10) | CONFIRMED | "The main hardware configurations of the experimental platform of the two models are: Intel (R) Xeon (R) Gold 6246R CPU with 3.4 GHz and 128 GB RAM; NVIDIA Quadro RTX 8000GPU with 48 GB video memory. The operating environment is Windows 10." (line 247) |
| resolution_input | 640 | CONFIRMED | "The original images were cropped into 1005 images with 640 × 640 pixels." (line 134) |
| framework | PyTorch 1.7.1, Python 3.7, OpenCV 4.5.1 (Mask R-CNN via MMDetection w/ ImageNet-pretrained weights) | CONFIRMED | "Python 3.7 was used with the Pytorch1.7.1 deep learning framework and OpenCV4.5.1 computer vision library. The trained weight file on the ImageNet dataset was used as a pre-trained weight for the Mask R-CNN" (line 247); "the Mask R-CNN (https://github.com/open-mmlab/mmdetection...) [45] was used to generate complete maize seedlings masks" (line 146) |
| latency_ms | 70 | CONFIRMED | "The inference times for image detection boxes and masks were 0.05s and 0.07s, respectively." (line 522; also abstract line 48, Table 2 line 313). Mask segmentation time 0.07 s = 70 ms. |

## SCI-000624 — Deep Convolutional Neural Networks for Weeds and Crops Discrimination From UAS Imagery

attribution: CONFIRMED for model=DeepLab v3+ (best on CWFID); FCN-8s (best on sugarcane) backbone=ResNet-18 (per abstract) dataset=CWFID (crop/weed field image dataset) and sugarcane UAS dataset. "Based on the results in Table 3, in overall, DeepLabV3+ has a better classification performance than FCN-8s, U-Net, FCN-16s, FCN-32s, and SegNet" (CWFID, line 232); Table 4: "SegNet 62.8 0.63 FCN-32s 69.8 0.71 FCN-16s 71.6 0.73 FCN-8s 76.62 0.76 U-Net 74 0.72 DeepLab v3+ 70.99 0.74" (sugarcane, line 238 — FCN-8s best).

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| PA | 0.843 | CONFIRMED | "the classification accuracy achieved by U-Net is 77.9% higher than 62.6% of SegNet, 68.4% of FCN-32s, 77.2% of FCN-16s, and slightly lower than 81.1% of FCN-8s, and 84.3% of DepLab v3+" (abstract, line 43); Table 3: "U-Net 77.9 0.76 DeepLab v3+ 84.3 0.82" (line 216; CWFID accuracy) |
| resolution_input | 512 | CONFIRMED | "We extracted a total of 32 patches (512 p512) per image. The patches were inserted into the networks with a batch size of 4." (line 220) — 512 × 512 training patch size |

## SCI-000669 — Towards real-time weed detection and segmentation with lightweight CNN models on edge devices

attribution: CONFIRMED for model=MobileNetV4-Seg backbone=MobileNetV4-Conv-Small dataset=UAV RGB images of corn and soybean fields infested with Palmer Amaranth

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.768 | CONFIRMED | "with IoUs of 69.9 % and 76.8 %, F1 scores of 82.3 % and 86.9 %, for the corn and soybean datasets, respectively, and 44 FPS on the Jetson Orin Nano" (abstract, line 73); Table 5 soybean row: "76.8 83.8 90.2 86.9 44" (line 332); "For soybean, it achieved 76.8 % IoU, 83.8 % precision, 90.2 % recall, and an F1 score of 86.9 %." (line 340). Soybean-dataset IoU used. |
| F1 | 0.869 | CONFIRMED | Same quotes as mIoU (soybean F1 86.9%). |
| device | NVIDIA Jetson Orin Nano | CONFIRMED | "A YOLOv8n model and a proposed MobileNetV4-Seg model were trained and deployed on a Jetson Orin Nano." (line 73) |
| precision | FP32 | LOW_CONF | The paper never states a precision mode for the MobileNetV4-Seg deployment. Line 414's "1280 GFLOPS for FP32 precision" describes the Orin Nano's compute capability, and line 106's "FP32 quantization" refers to a related-work YOLOv4-tiny study, not this one. FP32 is the implicit PyTorch default but is not stated in the extracted text. |
| resolution_input | 256 | CONFIRMED | "RGB images were collected by UAVs... deployed on edge devices for real-time weed detection with resized input images in dimensions of 256 × 256 pixels" (line 73); "at a resolution of 256 × 256 for input images, models achieved the optimal combination of classification accuracy and inference speed" (line 153); Table 5 FPS row "44" for 256 × 256 inputs (line 340) |
| framework | PyTorch (Jetson Orin Nano: torch 1.10.0 / torchvision 0.11.3 / CUDA 10.2; Jetson Nano: torch 2.4.1 / torchvision 0.19.1 / CUDA 11.4) | CONFIRMED | "CNN models were deployed on Jetson Nano's GPU utilizing PyTorch with torch version: 2.4.1, torchvision version: 0.19.1, and CUDA version: 11.4; and Jetson Orin Nano's GPU utilizing PyTorch but with torch version: 1.10.0, torchvision version: 0.11.3, and CUDA version: 10.2." (line 250) |
| fps | 44.0 | CONFIRMED | "and 44 FPS on the Jetson Orin Nano" (line 73); "The proposed MobileNetV4-Seg SS model achieved real-time (44 FPS) inference speed on Jetson Orin Nano" (line 461); "YOLOv8n and the MobileNetV4-Seg both achieved real-time inference speeds of 30 FPS and 44 FPS, respectively, for 256 × 256 pixel images" (line 340) |
| params_M | 1.93 | CONFIRMED | "our developed model has only 1.93 million parameters, whereas YOLOv8n has 3.2 million parameters" (line 416) |

## SCI-000683 — A Low-Cost UAV System and Dataset for Real-Time Weed Detection in Salad Crops

attribution: CONFIRMED for model=Squeeze U-Net backbone=U-Net with SqueezeNet fire modules dataset=AgriAdapt (self-collected 747 UAV aerial images of salad crops with weeds, Rome, Italy)

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.5545 | CONFIRMED | "U-Net is the most parameter-efficient model with 2.5 million parameters and 6.6 GFLOPS. It achieves an IoU of 55.45 and an accuracy of 89.84%." (lines 454-455); Table 4: "Squeeze U-Net 2.5 6.6 55.45 89.84 59.36 69.68" (line 468); Table 6 512 × 512 row: "55.45 89.84 59.36 69.68" (line 674). Single IoU reported at 512 × 512 input. |
| F1 | 0.6968 | CONFIRMED | Table 4/Table 6 512 × 512 row: "Squeeze U-Net 2.5 6.6 55.45 89.84 59.36 69.68" (lines 468, 674). F1-score 69.68%. |
| PA | 0.8984 | CONFIRMED | "It achieves an IoU of 55.45 and an accuracy of 89.84%." (line 455). Paper defines Accuracy as overall pixel-level accuracy (Eq. 2: OA); mapped to PA per record. |
| device | NVIDIA Jetson Nano | CONFIRMED | "featuring a custom-designed on-board computing system based on the NVIDIA Jetson Nano" (line 45); "The Jetson Nano was selected as the onboard computing platform" (line 307); "All inference timing and energy consumption measurements were performed directly on the NVIDIA Jetson Nano platform integrated into the UAV system." (line 604) |
| precision | FP32 | LOW_CONF | No precision mode is stated anywhere in the paper for inference on Jetson Nano (PyTorch default FP32 implied, not asserted). |
| resolution_input | 512 | CONFIRMED | "All images were resampled to a uniform size of 512 × 512 pixels and rescaled to a range of [0.0, 1.0]" (line 405); Table 6 Peak row: "512 × 512 55.45 89.84 59.36 69.68" (line 674) |
| framework | PyTorch (trained on NVIDIA RTX 3090, 16 batch, Adam lr 1e-4 exp-decay 0.99, 500 epochs max w/ early stopping) | CONFIRMED | "We trained the models for a maximum of 500 epochs, with an early termination criteria..." (line 407); "The batch size used for training was 16" (line 407); "we used the Adam optimizer with an initial learning rate of 0.0001... exponentially decreased with a factor of 0.99" (line 407); "All neural network models were trained on an Nvidia RTX 3090 GPU with 24 GB of memory. The PyTorch deep learning framework was used..." (line 409) |
| fps | 30.6 | CONFIRMED | "the measured inference times correspond to average frame rates of 30.6 FPS for Squeeze U-Net, 18.8 FPS for LRASPP, and 17.7 FPS for DeepLabV3" (line 606); Table 5: "Avg FPS 30.58 17.70 18.80" (line 623); "sustaining on-board real-time inference (30.6 FPS on NVIDIA Jetson Nano" (line 166) |
| latency_ms | 32.7 | CONFIRMED | "On average, Squeeze U-Net required only 0.0327 s per image, which is nearly 40% faster than LRASPP (0.0532 s)" (line 604); Table 5: "Avg time per image (s) 0.0327 0.0565 0.0532" (line 623). 0.0327 s = 32.7 ms. |
| power_w | 10.0 | CONFIRMED | "The board is capable of running modern deep learning inference tasks while consuming as little as 5–10 W of power" (line 307); "our Squeeze U-Net achieves 30.6 FPS directly on the lower-power Jetson Nano (5–10 W)" (line 596). Paper states a 5–10 W nominal range; 10.0 W is the upper bound of that range (no single measured value reported). |
| params_M | 2.5 | CONFIRMED | "the most parameter-efficient model with 2.5 million parameters and 6.6 GFLOPS" (line 454) |
| gflops | 6.6 | CONFIRMED | "the most parameter-efficient model with 2.5 million parameters and 6.6 GFLOPS" (line 454) |

## SCI-000708 — Drone-Aided Detection of Weeds: Transfer Learning for Embedded Image Processing

attribution: CONFIRMED for model=U-Net (the framework's segmentation networks are U-Net, line 166) and for dataset=self-collected UAV (RGB + multispectral NIR, hogweed). NOTE: headline mIoU figure below belongs to the TrueRGN (real-NIR) variant, not the claimed SynthFakeRGN transfer-learning model.

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.753 | MISMATCH | Value exists: "the U-Net model (see Table II) trained on orthophoto data gives a score of 75.3% when evaluated on frame data, which is 6.3% less than that of the same model evaluated on the frame test set" (line 250). BUT the preceding sentence identifies this 75.3% as an example of **TrueRGN** (real RGN) generalization ("from Tables I and II, it is clear that TrueRGN models better generalize to the different test data. As an example, the U-Net model..."). The SynthFakeRGN models trained on orthophoto data overfit on cross-domain evaluation with a 26 percentage-point difference (line 250); their absolute orthophoto-to-frame mIoU is not stated in the text. Reported value therefore does not match the attributed SynthFakeRGN model. |
| device | NVIDIA Jetson Xavier NX | CONFIRMED | "We have used NVIDIA Jetson Xavier NX as a target device, since it was proven to be an efficient low-cost solution for various vision tasks in edge computing" (line 224) |
| resolution_input | 100 | CONFIRMED | "we have performed a tile inference, where each frame is first divided into nonoverlapping regions of size 100 × 100, which are fed to the network with batch size 1" (line 264) |
| framework | TensorRT (network quantization and layer fusion/pruning) | CONFIRMED | "we have applied the well-known techniques of network quantization and layer fusion (pruning)... we have used NVIDIA TensorRT inference optimizer and runtime, which performs all the optimizations" (line 224) |
| params_M | 17.3 | CONFIRMED | "for the segmentation network, we have used a U-Net backbone consisting of three blocks in both the encoder and decoder parts with 17.3M parameters in total" (line 166) |

## SCI-000810 — AgriJetsonBench: External-Power-Referenced TensorRT Benchmarking of Agricultural Vision Models on Jetson Edge Platforms

attribution: CONFIRMED for model=SegFormer-B0 (segmentation workload in benchmark) backbone=SegFormer-B0 (transformer) dataset=Locked agricultural crop/weed datasets: CropAndWeed (segmentation) + CottonWeedDet12 (detection)

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.8049 | CONFIRMED | "SegFormer-B0 achieved the strongest predictive performance, with test mIoU of 0.8049, test Dice of 0.8854, and foreground mIoU of 0.7115" (line 814); Table 5: "SegFormer-B0 Segmentation CropAndWeed 0.8177 0.8049 – – – – 0.8854 0.7115 0.7665 0.6565 14.84" (line 914). Held-out CropAndWeed_v1 test set. |
| Dice | 0.8854 | CONFIRMED | "with test mIoU of 0.8049, test Dice of 0.8854" (line 814); Table 5 (line 914). |
| device | NVIDIA Jetson AGX Orin 64GB and Jetson Orin Nano Super | CONFIRMED | "Agricultural vision models... deployment benchmark for crop/weed detection and segmentation on NVIDIA Jetson AGX Orin 64GB and Jetson Orin Nano Super" (line 41); "The deployment study uses two Jetson boards: NVIDIA Jetson AGX Orin 64GB and NVIDIA Jetson Orin Nano Super." (line 249) |
| precision | INT8 (matched-budget 15 W) / FP16 (native) TensorRT | CONFIRMED | "Under matched 15 W INT8 operation, Orin Nano Super outperformed AGX Orin" (line 41); "The evaluated precision modes were FP32, FP16, and TensorRT INT8 build mode." (line 413) |
| resolution_input | 640 | CONFIRMED | "The main benchmark matrix was locked at an input size of 640 × 640 and batch size 1." (line 417); "Checkpoint → ONNX → TensorRT • FP32, FP16, INT8 engines • 640 input + resolution ablation" (line 84) |
| framework | TensorRT (ONNX export) | CONFIRMED | "seven model families were exported through ONNX and TensorRT" (line 41); "Checkpoint → ONNX → TensorRT" (line 84) |
| fps | 47.18 | CONFIRMED | "SegFormer-B0 reached 47.18 FPS and 0.2808 J/inference versus 31.95 FPS and 0.5013 J/inference" (line 41); "Nano processed 756,122 inferences over 4.452 h at 47.18 FPS" (line 931). Matched-budget 15 W INT8, Orin Nano Super. |
| latency_ms | 21.514 | CONFIRMED | "Median latency decreased from 29.523 ms on AGX to 21.514 ms on Nano, and p95 latency decreased from 29.566 ms to 21.582 ms." (line 931). Claim uses median latency; the energy-table value (line 1040) is p95 = 21.582 ms. |
| power_w | 13.15 | CONFIRMED | "Nano Super 15 W SegFormer-B0 INT8 756,122 4.452 47.18 21.582 13.15 58.974 0.2808 12,821" (Table 8, line 1040). External board-input power 13.15 W. |
| params_M | 3.71 | CONFIRMED | "SegFormer-B0 had only 3.71 M parameters, but required 14.84 GMACs" (line 861); Table 3: "SegFormer-B0 Segmentation 3.71 M 1.48 × 10¹⁰ 14.84 29.67" (line 411) |
| gflops | 29.67 | CONFIRMED | Table 3: "SegFormer-B0 Segmentation 3.71 M 1.48 × 10¹⁰ 14.84 29.67" (line 411) — GFLOPs-equivalent at 1 MAC = 2 FLOPs. |

## SCI-000816 — Deblurring-aware semantic segmentation of crops and weeds in UAV sorghum imagery via a UNet-ResNet architecture

attribution: CONFIRMED for model=UNet-ResNet-34 + NAFNet (restoration-aware front-end) backbone=ResNet-34 (best depth; variants ResNet-18/50/101 also evaluated) dataset=DeBlurWeedSeg (public UAV sorghum dataset, Mendeley Data; Genze et al.)

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.7185 | CONFIRMED | Table 6: "Proposed (UNet-ResNet34 + NAF) 0.8223 0.7185 0.8424 0.8067" (line 801); "the proposed UNet-ResNet34 with the restoration-aware NAFNet front-end attains the highest mDS (0.8223), mIoU (0.7185) and mPrecision (0.8424) on the combined test set" (line 803). Combined sharp + motion-blurred hold-out set. |
| Dice | 0.9198 | CONFIRMED | "a systematic comparison across four ResNet encoder variants (ResNet-18, ResNet-34, ResNet-50, and ResNet-101) reveals that ResNet-34 achieves the highest mean Dice Score of 0.9198" (line 63); "ResNet-34 achieves the highest mean Dice Score of 0.9198" (line 709); Table 2: "ResNet-34 0.9975 0.9047 0.8570 0.9198" (line 678). Best single-encoder (sharp-set) mean Dice. |
| device | None - no on-device deployment. Complexity analysis targets a conceptual NVIDIA Jetson pipeline; training on desktop NVIDIA RTX 3090 24 GB | CONFIRMED | "a direct on-device throughput validation on embedded NVIDIA Jetson hardware was not performed and is left for future work" (line 69); "Training and evaluation were performed on a single NVIDIA GeForce RTX 3090 GPU with 24 GB of memory." (line 648); "Fig. 8 Schematic of the proposed on-board deployment pipeline (a conceptual diagram, not a field photograph)" (line 873) |
| resolution_input | 128 | CONFIRMED | "The dataset comprises 1,300 pairs of 128x128 pixel image patches, each consisting of a motion-blurred image and its corresponding sharp counterpart." (line 559) |
| framework | PyTorch 2.1.0 + segmentation-models-pytorch; torchvision ImageNet-pretrained ResNet encoders | CONFIRMED | "All models were implemented in PyTorch 2.1.0 using the segmentation models pytorch library, with the ResNet encoders initialised from torchvision ImageNet-pretrained weights" (line 648) |
| params_M | 24.4 | CONFIRMED | Table 7: "Proposed Seg (UNet-R34) 24.4 1.97" (line 831); "the segmentation network alone (24.4 M parameters, 1.97 GMACs) is comparable in complexity to the standard CNN baselines" (line 838 caption / line 847) |
| gflops | 3.94 | CONFIRMED | Derived: "the segmentation network alone (24.4 M parameters, 1.97 GMACs)" (lines 838-840); 3.94 GFLOPs = 1.97 GMACs × 2 FLOPs/MAC (per the paper's 1 MAC = 2 FLOPs convention). GFLOPs value not stated literally in text. |

## SCI-000852 — SqueezeSlimU-Net: An Adaptive and Efficient Segmentation Architecture for Real-Time UAV Weed Detection

attribution: CONFIRMED for model=SSU-Net (100% width) backbone=Slimmable U-Net with SqueezeNet fire modules (SNN-style, widths 100/75/50/25%) dataset=AgriAdapt (partition 1) and Tobacco Aerial Dataset (campaign 2)

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.5828 | CONFIRMED | "At 100% width, the SSU-Net achieved an IoU of 58.28%, surpassing the SU-Net's 57.13%." (line 235) |
| PA | 0.9047 | CONFIRMED | "In terms of accuracy, the SSU-Net also demonstrates clear advantages. At 100% width, it achieved an accuracy of 90.47%, compared to the SU-Net's 89.41%." (line 235). Overall pixel-level accuracy mapped to PA per record. |
| device | NVIDIA Jetson Nano | CONFIRMED | "Jetson Nano 4 GB [30] board running Ubuntu 20.04.6 LTS. This edge computing platform... are commonly used onboard UAVs" (line 183); "The measurements were performed on an NVIDIA Jetson Nano computing platform using a Monsoon power monitor" (line 255) |
| precision | FP32 | LOW_CONF | No precision mode is stated in the paper. Line 183 ("Python 3.8.10 and PyTorch 1.12.0 to execute the models") implies PyTorch default FP32; not asserted in text. |
| resolution_input | 512 | CONFIRMED | "all dataset images were resampled to a uniform size of 512 × 512 pixels (other image sizes were also examined, but the size of 512 × 512 pixels was found to be optimal from both accuracy and running times)" (line 181) |
| framework | PyTorch (trained on NVIDIA RTX 3090 24 GB, batch 8, Adam lr 1e-4 exp-decay 0.99, 300 epochs max) | CONFIRMED | "We trained the slimmable models for a maximum of 300 epochs... we used a batch size of 8 and the Adam optimizer with an initial learning rate of 0.0001 that was exponentially decreased with a factor of 0.99" (line 195); "We trained all neural network models on an Nvidia RTX 3090 GPU with 24 GB of memory. The PyTorch DL framework was used..." (line 215); on-device Python 3.8.10 / PyTorch 1.12.0 (line 183) |
| fps | 4.25 | CONFIRMED | "FPS, ranging from 4.25 for the 100% width network to 9.09 for the 25% width" (line 259); "SSU-Net achieves FPS rates (4.25–9.09)" (line 367) |
| latency_ms | 235 | CONFIRMED | Derived: 1000/4.25 ≈ 235.3 ms from the reported 4.25 FPS at 100% width (line 259). The paper reports FPS and per-instance inference times (Fig. 5b); no literal "235 ms" figure appears in the text. |
| params_M | 2.5 | CONFIRMED | "With 2.5 M parameters, SSU-Net achieves an IoU of 58.28%, closely matching larger models, such as Deeplab V3 (58.35%, 11.0 M)" (line 367); "Fig. 13 highlights SSU-Net's ability to balance model complexity and segmentation performance" (line 367) |

## Batch summary

| study_id | CONFIRMED | MISMATCH | NOT_FOUND | LOW_CONF |
|----------|-----------|----------|-----------|----------|
| SCI-000582 | 2 | 0 | 0 | 0 |
| SCI-000618 | 4 | 0 | 0 | 0 |
| SCI-000624 | 2 | 0 | 0 | 0 |
| SCI-000669 | 7 | 0 | 0 | 1 |
| SCI-000683 | 11 | 0 | 0 | 1 |
| SCI-000708 | 4 | 1 | 0 | 0 |
| SCI-000810 | 11 | 0 | 0 | 0 |
| SCI-000816 | 7 | 0 | 0 | 0 |
| SCI-000852 | 8 | 0 | 0 | 1 |
| **Overall** | **56** | **1** | **0** | **3** |