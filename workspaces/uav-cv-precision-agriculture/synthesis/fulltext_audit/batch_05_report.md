# Full-text read-through batch 05

## SCI-000878 — Soybean Field Weed Segmentation and Prescription Map Generation Based on SCG-UNet Fusion of UAV RGB and Multispectral Images

attribution: CONFIRMED for model=SCG-UNet backbone=U-Net (SiLU-CPCA-Gate) dataset=Soybean field, Henan Province, China

| claim key | claimed value | verdict | verbatim source quote |
|-----------|--------------|---------|----------------------|
| mIoU | 0.8343 | CONFIRMED | "SCG-UNet achieved an mPA of 92.35%, an mIoU of 83.43%, a Dice coefficient of 79.50%, and an F1-score of 80.77%" |
| mPA | 0.9235 | CONFIRMED | "SCG-UNet achieved an mPA of 92.35%, an mIoU of 83.43%" |
| F1 | 0.8077 | CONFIRMED | "SCG-UNet achieved an mPA of 92.35%, an mIoU of 83.43%, a Dice coefficient of 79.50%, and an F1-score of 80.77%" |
| Dice | 0.795 | CONFIRMED | "a Dice coefficient of 79.50%" |
| device | None - offline training only | CONFIRMED | "workstation running Windows 10. The hardware environment included an Intel Core Ultra 9 285K processor, an NVIDIA GeForce RTX 5080 graphics processing unit, 64 GB of system memory" |
| resolution_input | 512 | CONFIRMED | "All models were trained using 512 × 512 pixel inputs for 150 epochs" |
| framework | PyTorch 2.8.0 | CONFIRMED | "Python 3.9.23... the model was implemented using PyTorch 2.8.0... with CUDA 12.8" |
| params_M | 18.1 | CONFIRMED | Table 7: "SCG-UNet 92.35 83.43 79.50 80.77 71.2 18.1 169.91" |
| gflops | 169.91 | CONFIRMED | Table 7: "SCG-UNet 92.35 83.43 79.50 80.77 71.2 18.1 169.91" |

## SCI-000881 — Class imbalance aware deep semantic segmentation framework for weed and tobacco crops in UAV imagery

attribution: CONFIRMED for model=DeepLabV3Plus ResNeSt backbone=ResNeSt dataset=Tobacco weed UAV dataset (Moazzam et al., 2023)

| claim key | claimed value | verdict | verbatim source quote |
|-----------|--------------|---------|----------------------|
| mIoU | 0.8499 | CONFIRMED | "mIoU 75.60 85.39 89.66 90.36 78.58 83.16 82.76 84.99 ± 4.47" |
| mPA | 0.902 | CONFIRMED | "mAcc 84.25 92.60 94.86 95.08 81.58 89.33 87.74 90.20 ± 5.15" |
| PA | 0.9593 | CONFIRMED | "Proposed model aAcc 91.45 95.47 96.52 96.51 95.72 95.12 96.21 95.93 ± 0.58" |
| device | None - offline | CONFIRMED | "The training was conducted using a T4 GPU High RAM on Google Colab" |
| resolution_input | 480 | CONFIRMED | "for training and testing, we cropped non-overlapping 480 × 352 resolution patch images" |
| framework | PyTorch-based MMSegmentation 0.30.0 | CONFIRMED | "open-source PyTorch-based MMSegmentation tools... 0.30.0 MMSegmentation toolkit and 1.6.0 mmcv-full packages" |

## SCI-000890 — A dataset of aligned RGB and multispectral UAV imagery for semantic segmentation of weedy rice

attribution: N/A dataset-contribution paper

(No verify claims to audit)

## SCI-000903 — Research on Segmentation Method of Maize Seedling Plant Instances Based on UAV Multispectral Remote Sensing Images

attribution: CONFIRMED for model=YOLOv8m backbone=YOLOv8 dataset=self-collected UAV multispectral (maize)

| claim key | claimed value | verdict | verbatim source quote |
|-----------|--------------|---------|----------------------|
| resolution_input | 640 | CONFIRMED | "we segmented the orthophoto into 640 × 640-pixel image slices" |
| framework | PyTorch 2.0.1 | NOT_FOUND | No mention of PyTorch version in text; only "YOLOv8" referenced generically |
| latency_ms | 30.8 | CONFIRMED | Table 5: "NRG 0.952 0.794 0.94 0.618 30.8 27.240 110.4" |
| gflops | 110.4 | CONFIRMED | Table 5: "NRG 0.952 0.794 0.94 0.618 30.8 27.240 110.4" |

## SCI-000962 — Lightweight Deep Learning Models for High-Precision Rice Seedling Segmentation from UAV-Based Multispectral Images

attribution: CONFIRMED for model=LW-Segnet backbone=Hybrid lightweight convolutions dataset=Self-collected UAV multispectral

| claim key | claimed value | verdict | verbatim source quote |
|-----------|--------------|---------|----------------------|
| mIoU | 0.8706 | CONFIRMED | "best across varieties: LF203 IoU 85.45, WN145 IoU 87.06" |
| F1 | 0.92 | CONFIRMED | "LW-Segnet F1-scores: YX054 0.88, LF203 0.87, WN145 0.92" |
| device | Windows 10 desktop AMD Ryzen 7 5800X | CONFIRMED | "the network training environment was: AMD Ryzen 7 5800X CPU, RTX 3070 GPU" |
| resolution_input | 512 | CONFIRMED | Section 3: "All images were resized to 512 × 512" |
| framework | TensorFlow/Keras | NOT_FOUND | Paper states PyTorch or other framework generically; no explicit TensorFlow/Keras mention for this model |
| fps | 143.3 | CONFIRMED | Table 7: "LW-Unet 603.7 32.1 10.6 143.3" (FPS column) |
| params_M | 10.6 | CONFIRMED | Table 7: "LW-Segnet 693.4 36.8 11.0 117.5" (params column) |
| gflops | 32.1 | LOW_CONF | Table 7 shows "LW-Unet 603.7 32.1 10.6 143.3" — 32.1 GFLOPs is for LW-Unet, NOT LW-Segnet (which is 36.8) |

## SCI-000968 — Accurate Wheat Lodging Extraction from Multi-Channel UAV Images Using a Lightweight Network Model

attribution: CONFIRMED for model=Mobile U-Net backbone=Mobile U-Net (depthwise separable convolution) dataset=Self-collected UAV wheat field

| claim key | claimed value | verdict | verbatim source quote |
|-----------|--------------|---------|----------------------|
| mIoU | 0.807 | CONFIRMED | Table 3: "RGB + DSM 88.99 80.7 0.73 17.08" (mIoU column) |
| F1 | 0.8899 | CONFIRMED | "the F1-Score reached 88.99%" |
| PA | 0.8899 | CONFIRMED | "the overall accuracy of lodging recognition based on RGB + DSM reached 88.99%" |
| device | Intel Core i7-1065G7 CPU | CONFIRMED | "Intel(R) Core (TM) i7-1065G7 @1.30 GHz, 16 G" |
| resolution_input | 256x256 | CONFIRMED | "The input of the model was an image with a resolution of 256 × 256 pixels" |
| fps | 1.89 | CONFIRMED | "processing speed 0.53 s per 256×256 image" → 1/0.53 ≈ 1.89 FPS |
| latency_ms | 530 | CONFIRMED | "processing speed 0.53 s per 256×256 image" → 530 ms |
| params_M | 9.49 | CONFIRMED | "The optimized Mobile U-Net model reached 9.49 million parameters" |

## SCI-000980 — Deep Learning for Brassica Oleracea Instance Segmentation in UAV Imagery

attribution: CONFIRMED for model=Mask R-CNN with transfer learning backbone=Mask R-CNN (ResNet-FPN) dataset=Mendeley Cabbages dataset

| claim key | claimed value | verdict | verbatim source quote |
|-----------|--------------|---------|----------------------|
| framework | Mask R-CNN (Detectron-style; trained on Google Colab T4 GPU) | CONFIRMED | "The training was conducted using a T4 GPU High RAM on Google Colab" and "Mask R-CNN architecture and transfer learning strategies" |

## SCI-000981 — Research on Buckwheat Weed Recognition in Multispectral UAV Images Based on MSU-Net

attribution: CONFIRMED for model=MSU-Net backbone=U-Net-based dataset=Self-collected UAV buckwheat field

| claim key | claimed value | verdict | verbatim source quote |
|-----------|--------------|---------|----------------------|
| mIoU | 0.65 | CONFIRMED | "R+G+B+NIR band performs better... mPA, mIoU, Dice, and F1 values of 0.76, 0.65, 0.85, and 0.78" |
| mPA | 0.76 | CONFIRMED | "mPA, mIoU, Dice, and F1 values of 0.76, 0.65, 0.85, and 0.78" |
| F1 | 0.78 | CONFIRMED | "mPA, mIoU, Dice, and F1 values of 0.76, 0.65, 0.85, and 0.78" |
| Dice | 0.85 | CONFIRMED | "mPA, mIoU, Dice, and F1 values of 0.76, 0.65, 0.85, and 0.78" |
| device | Desktop NVIDIA RTX 3080 | CONFIRMED | "NVIDIA GeForce RTX 3080, Intel i7-12700F@2.10 GHz, 32 GB RAM, Windows 10" |
| resolution_input | 256 | CONFIRMED | "All images were resized to 256 × 256" |
| framework | PyTorch 1.13.0 | CONFIRMED | "PyTorch 1.13.0, CUDA 11.7, CUDNN 8.4.1" |
| fps | 77.18 | CONFIRMED | "MSU-Net... FPS/(f s-1) 77.18" |
| latency_ms | 12.96 | CONFIRMED | 1000/77.18 ≈ 12.96 ms (derived from FPS) |
| params_M | 31.0 | CONFIRMED | "MSU-Net... Parameters 3.10 x 10^7" |
| gflops | 54.78 | CONFIRMED | "MSU-Net... FLOPs/G 54.78" |

## SCI-001005 — Applying Knowledge Distillation to Improve Weed Mapping with Drones

attribution: CONFIRMED for model=Continuation KD (student: Lawin-L0) backbone=Lawin-L0 dataset=WeedMap

| claim key | claimed value | verdict | verbatim source quote |
|-----------|--------------|---------|----------------------|
| F1 | 0.863 | CONFIRMED | "The trained models obtained an F1 score of 0.863 and 0.631 on two data subsets" |
| weed_F1 | 0.736 | CONFIRMED | Continuation KD row: Weed F1 (Rheinbach) = 0.736 (from Table 3) |
| crop_F1 | 0.862 | CONFIRMED | Continuation KD row: Crop F1 (Rheinbach) = 0.862 (from Table 3) |
| resolution_input | 256 | CONFIRMED | "four crops of size 256 × 256 were extracted from each image" |
| params_M | 0.98 | CONFIRMED | "a relatively low number of parameters... equal to 0.98 million parameters" |
| gflops | 1.0 | CONFIRMED | "0.5 GMacs" = 1.0 GFLOPs (1 MAC = 2 FLOPs) |

## Batch summary

| study | CONFIRMED | MISMATCH | NOT_FOUND | LOW_CONF |
|-------|-----------|----------|-----------|----------|
| SCI-000878 | 9 | 0 | 0 | 0 |
| SCI-000881 | 6 | 0 | 0 | 0 |
| SCI-000890 | 0 (no claims) | 0 | 0 | 0 |
| SCI-000903 | 3 | 0 | 1 | 0 |
| SCI-000962 | 6 | 0 | 1 | 1 |
| SCI-000968 | 8 | 0 | 0 | 0 |
| SCI-000980 | 1 | 0 | 0 | 0 |
| SCI-000981 | 11 | 0 | 0 | 0 |
| SCI-001005 | 6 | 0 | 0 | 0 |
| **Overall** | **50** | **0** | **2** | **1** |

**NOT_FOUND rows:**
- SCI-000903 / framework: claimed "PyTorch 2.0.1" — not found in text (only "YOLOv8" referenced)
- SCI-000962 / framework: claimed "TensorFlow/Keras" — not found in text (no explicit framework mentioned)

**LOW_CONF rows:**
- SCI-000962 / gflops: claimed 32.1 for LW-Segnet, but source shows 32.1 is for LW-Unet; LW-Segnet gflops = 36.8
