# Full-text read-through batch 01

## SCI-000040 — DAS-SK: An Adaptive Model Integrating Dual Atrous Separable and Selective Kernel CNN for Agriculture Semantic Segmentation

attribution: CONFIRMED for model=DAS-SK backbone=MobileNetV3-Large/EfficientNet-B3 dataset=LandCover.ai, VDD, PhenoBench

| claim key | claimed value | verdict | verbatim source quote |
|---|---|---|---|
| mIoU | 0.8555 | CONFIRMED | "Our model (DAS-SK) 85.55 10.678 45.00 4.67 1.028 10.09 10.33" (Table VIII, PhenoBench) |
| device | FPS measured on NVIDIA GeForce RTX 3050 Ti GPU; training on A100-40GB (Alliance Canada, Narval cluster) | CONFIRMED | "Environment A100-40GB GPU (Alliance Canada, Narval cluster). NVIDIA GeForce RTX 3050 Ti GPU (to obtain FPS)" (Table V) |
| resolution_input | 1024 | CONFIRMED | "PhenoBench 0.1 3 1024 × 1024" (Table IV); "Input image size - 1024 × 1024" (Table VIII note) |
| framework | PyTorch 2.1, CUDA 12.1 | CONFIRMED | "Framework PyTorch 2.1 with CUDA 12.1" (Table V) |
| fps | 10.33 | CONFIRMED | "Our model (DAS-SK) 85.55 10.678 45.00 4.67 1.028 10.09 10.33" (Table VIII FPS column) |
| latency_ms | 96.8 | NOT_FOUND | No explicit latency or 96.8 ms figure found in the fulltext; only FPS (10.33) reported for PhenoBench. |
| params_M | 10.678 | CONFIRMED | "Our model (DAS-SK) 85.55 10.678 45.00 4.67 1.028 10.09 10.33" (Table VIII Param.(M) column) |
| gflops | 45.0 | CONFIRMED | "Our model (DAS-SK) 85.55 10.678 45.00 4.67 1.028 10.09 10.33" (Table VIII GFLOPs column) |

## SCI-000074 — WeedFormer: Transformer-based Crop-Weed Segmentation for UAV Imagery

attribution: CONFIRMED for model=WeedFormer backbone=SegFormer-B2 dataset=WeedsGalore

| claim key | claimed value | verdict | verbatim source quote |
|---|---|---|---|
| mIoU | 0.8027 | CONFIRMED | "SFB2-Enh. (Ours) 80.27 98.81 87.93 88.77" (Table I) |
| F1 | 0.8877 | CONFIRMED | "It achieves the highest mIoU of 80.27%, PA of 98.81%, Precision of 87.93%, and F1-Score of 88.77%." (Section IV.A) |
| PA | 0.9881 | CONFIRMED | "SFB2-Enh. (Ours) 80.27 98.81 87.93 88.77" (Table I, PA column = 98.81%) |
| device | None stated | CONFIRMED | No hardware or device reported; paper is offline training/evaluation only. |
| resolution_input | 512 | CONFIRMED | "Input images are resized to 512 × 512 pixels and normalized to the range [0, 1]." (Section III.A) |
| framework | Deep-learning framework not explicitly named | NOT_FOUND | No explicit framework name (e.g. PyTorch, TensorFlow) stated in the extracted text. |

## SCI-000075 — Weed Instance Segmentation from UAV ortho-mosaic Images based on Deep Learning

attribution: CONFIRMED for model=YOLOv8 backbone=YOLOv8/Mask R-CNN dataset=self-collected UAV ortho-mosaic (potato)

| claim key | claimed value | verdict | verbatim source quote |
|---|---|---|---|
| mIoU | 0.515 | CONFIRMED | "Original Model: PA: 0.9989, CPA: 0.5271, MPA: 0.5150, MIOU: 0.5150, Mean Dice: 0.5298" (Figure 11 caption) |
| mPA | 0.515 | CONFIRMED | "MPA: 0.5150" (Figure 11 caption for Original Model) |
| Dice | 0.5298 | CONFIRMED | "Mean Dice: 0.5298" (Figure 11 caption for Original Model) |
| PA | 0.9989 | CONFIRMED | "PA: 0.9989" (Figure 11 caption for Original Model) |
| resolution_input | 640 | CONFIRMED | "cropped into a small image size of 640x640 pixels" (Section 2.3) |
| framework | Detectron2 (Mask R-CNN) / ultralytics YOLOv8 | CONFIRMED | "Mask R-CNN model in this study was trained based on Detection2" (Section 2.6.1); "YOLOv8" referenced throughout. |

## SCI-000084 — Crop and Weed Classication Using Pixel-wise Segmentation on Ground and Aerial Images

attribution: CONFIRMED for model=VGG-UNet backbone=VGG-16 dataset=Public datasets: SugarBeets, Stuttgart, Carrots, Sunflowers

| claim key | claimed value | verdict | verbatim source quote |
|---|---|---|---|
| mIoU | 0.75 | CONFIRMED | "SugarBeets 0,75 0.998 0.94 0.80 0.99 0.92 0.70" (Table 5, 3-class multi-channel, mIOU column) |
| mPA | 0.95 | CONFIRMED | "RED+NIR+NDVI 0.95 0.98 0.88" (Table 6, 3-class sugar beet mean accuracy) |
| device | NVIDIA Jetson TX2 | CONFIRMED | "The performance of VGG-UNet architecture has been tested on an embedded GPU board, namely Jetson TX2" (Section 4.6) |
| latency_ms | 600 | CONFIRMED | "the processing time per image was 0.6 seconds when we use three channels together as input" (Section 4.6) |

## SCI-000089 — Semi-supervised Learning for Weed and Crop Segmentation Using UAV Imagery

attribution: CONFIRMED for model=SemiWeedNet backbone=ResNet-50 dataset=WeedMap

| claim key | claimed value | verdict | verbatim source quote |
|---|---|---|---|
| mIoU | 0.701 | CONFIRMED | "Ours Resnet50 0.698 0.695 0.695 0.701" (Table 1, full labels column) |
| resolution_input | 480 | CONFIRMED | "The input images are resized to 480 × 480 pixels" (Implementation Details) |

## SCI-000091 — Weed–Crop Segmentation in Drone Images with a Novel Encoder–Decoder Framework Enhanced via Attention Modules

attribution: CONFIRMED for model=Proposed framework backbone=DenseInception+ASPP+attention dataset=rice-weed dataset (Huang et al., Zengcheng, SCAU)

| claim key | claimed value | verdict | verbatim source quote |
|---|---|---|---|
| mIoU | 0.81 | CONFIRMED | "Proposed 0.81 0.79 0.84 0.81" (Table 2, Rice/Weeds/Others/mIoU) |
| resolution_input | 1000 | CONFIRMED | "each image is sorted into twelve tiles, where the size of each tile is 1000 × 1000 pixels" (Section 4.1) |

## SCI-000136 — Weed segmentation in sugarcane crops using Mask R-CNN through aerial images

attribution: CONFIRMED for model=Mask R-CNN ResNet-101 backbone=ResNet-101 (FPN) dataset=self-collected aerial sugarcane field imagery (Brazil)

| claim key | claimed value | verdict | verbatim source quote |
|---|---|---|---|
| F1 | 0.752 | CONFIRMED | "The ResNet-101 model with pre-trained COCO achieved an Average Precision (AP50) of 65.5% and obtained values of 0.803, 0.707 and 0.752 for Precision, Recall and F1 score." (Abstract) |

## SCI-000138 — Crop and Weed Segmentation Using ResNet-Unet Architecture

attribution: CONFIRMED for model=ResNet-Unet backbone=ResNet-50 (UNet encoder) dataset=self-collected UAV sorghum (Germany)

| claim key | claimed value | verdict | verbatim source quote |
|---|---|---|---|
| F1 | 0.8937 | CONFIRMED | "Macro avg 93.01 86.25 89.37" (Table I, F1-Score column for macro avg) |
| Dice | 0.929 | CONFIRMED | "we were able to attain a maximum Sørensen-Dice Coefficient (DS) of 0.929, accompanied by a standard deviation of 0.0041" (Abstract) |
| PA | 0.99 | CONFIRMED | "test_1 (Early stage crop growth) Accuracy 0.9900363" (Table III) |
| weed_F1 | 0.7948 | CONFIRMED | "Weed 87.64 72.71 79.48" (Table I, F1-Score column for Weed class) |
| crop_F1 | 0.8876 | CONFIRMED | "Sorghum 91.58 86.10 88.76" (Table I, F1-Score column for Sorghum class) |
| resolution_input | 256 | CONFIRMED | "resizing them to a manageable size of 256x256 pixels" (Section III.B) |

## SCI-000149 — WeedVision: A single-stage deep learning architecture to perform weed detection and segmentation using drone-acquired images

attribution: CONFIRMED for model=WeedVision trained on C4 backbone=YOLO-style CSPDarknet (C3/C3x/SPPF) dataset=self-collected UAV (soybean field, NDSU)

| claim key | claimed value | verdict | verbatim source quote |
|---|---|---|---|
| device | NVIDIA Jetson AGX Xavier | CONFIRMED | "The edge device chosen to perform inference test was Jetson AGX Xavier" (Section 2.5) |
| precision | TorchScript & ONNX (FP32) | CONFIRMED | "the developed DL architecture trained on five categories have been converted to two formats for edge deployment use case…TorchScript and Open Neural Network eXchange (ONNX)." (Section 2.5) |
| resolution_input | 640 | CONFIRMED | "clipped and converted to a resolution of 640 × 640" (Section 2.1) |
| framework | PyTorch TorchScript and ONNX Runtime | CONFIRMED | "TorchScript (Spisak et al., 2019) is a part of PyTorch framework" (Section 2.5) |
| latency_ms | 2.1 | CONFIRMED | "The inference speed of the architecture was 2.1 ms and 2.3 ms per image for C4 and C5 category, respectively." (Section 3.3) |

## Batch summary

| Study | CONFIRMED | MISMATCH | NOT_FOUND | LOW_CONF |
|---|---|---|---|---|
| SCI-000040 | 7 | 0 | 1 | 0 |
| SCI-000074 | 5 | 0 | 1 | 0 |
| SCI-000075 | 6 | 0 | 0 | 0 |
| SCI-000084 | 4 | 0 | 0 | 0 |
| SCI-000089 | 2 | 0 | 0 | 0 |
| SCI-000091 | 2 | 0 | 0 | 0 |
| SCI-000136 | 1 | 0 | 0 | 0 |
| SCI-000138 | 6 | 0 | 0 | 0 |
| SCI-000149 | 5 | 0 | 0 | 0 |
| **Overall** | **38** | **0** | **2** | **0** |

### NOT_FOUND rows

- **SCI-000040**, `latency_ms`: claimed value 96.8 — no explicit latency or 96.8 ms figure found in the fulltext; only FPS (10.33) is reported for PhenoBench. If latency was derived as 1000/FPS ≈ 96.8, it is an inference not an explicit source value.
- **SCI-000074**, `framework`: claimed value "Deep-learning framework not explicitly named" — confirmed NOT_FOUND (no framework name appears in the extracted text).
