# RQ1 Bench-Portable Tables (Scaffold) — UAV CV Precision Agriculture

Auto-generated from `literature/extraction/merged/records.json` + `synthesis/synthesis_matrix.json`. Architecture family from a keyword heuristic; every `UNCLASSIFIED` row needs manual verification. Intra-study variant cells cite the extractor's evidence (`ambiguity`), to be curated into final paired tables.

## Diagnostics
- studies = 94 | mIoU reported = 64 | F1 = 32 | weed_F1 = 5 | multi-model studies = 75 | ambiguity-with-numbers = 52
- family counts: {'Hybrid': 3, 'Transformer': 10, 'UNCLASSIFIED': 9, 'CNN': 69, 'VLM': 2, 'no-model': 1}
- UNCLASSIFIED: ['SCI-000005', 'SCI-000010', 'SCI-000091', 'SCI-000346', 'SCI-000371', 'SCI-000489', 'SCI-001005', 'SCI-001292', 'SCI-001334']

## Table A — quasi-paired dataset benchmark groups (same test bed, >=2 studies)

| Dataset | Study | Fam | Best model (reported) | mIoU | F1 | Weed F1 | conf |
|---|---|---|---|---:|---:|---:|---:|
| WeedsGalore | SCI-000001 | Hybrid | Transformer-CNN hybrid (MSI: RGB + NIR + RE) | 0.7888 |  |  | 0.9 |
| WeedsGalore | SCI-000017 | CNN | DeepLabv3+ (MSI, 3-class) | 0.8290 |  |  | 0.95 |
| WeedsGalore | SCI-001084 | CNN | DeepLabV3+ (highest mIoU 82.90%); ResUNet SCSE best for weed IoU 77.49 | 0.8290 |  |  | 0.9 |
| CoFly-WeedDB | SCI-000440 | CNN | U-Net with RGB bands (480 training images) as stated by authors; numer | 0.5192 |  |  | 0.85 |
| CoFly-WeedDB | SCI-000488 | CNN | UNet with EfficientNetB0 backbone (multiclass D2 segmentation) | 0.5621 | 0.8824 | 0.6326 | 0.9 |
| Self-collected UAV rice field | SCI-000565 | CNN | Modified AlexNet-FCN (FP16 precision calibration) | 0.6280 |  |  | 0.95 |
| Self-collected UAV rice field | SCI-000582 | CNN | Modified FCN-4s | 0.8473 |  |  | 0.97 |
| WeedMap | SCI-000089 | CNN | SemiWeedNet (Ours) with ResNet50 backbone, full labeled data | 0.7010 |  |  | 0.95 |
| WeedMap | SCI-001005 | UNCLASSIFIED | Continuation KD (student: lightweight Lawin-L0) |  | 0.8630 | 0.7360 | None |
| self-collected UAV multispectral (DJI Phantom 4 Multispectral) | SCI-000962 | Hybrid | LW-Segnet (LWSegnet), best on WN145 variety test set | 0.8706 | 0.9200 |  | 0.7 |
| self-collected UAV multispectral (DJI Phantom 4 Multispectral) | SCI-001368 | CNN | U-Net with composite 5-band input, tile size 32 (crop & weed segmentat |  |  |  | None |

## Table B — intra-study paired candidates (multiple models tested within one study)

| Study | Fam | Models tested | Best (mIoU) | F1 | Extractors' variant evidence (`ambiguity`) |
|---|---|---|---|---:|---|
| SCI-000007 | CNN | VL-WS (frozen CLIP dual-encoder + DeepLabv3+ spatial encoder + FiLM modulation) ; U-Net ;  |  |  |  |
| SCI-000012 | CNN | FCN-32s ; FCN-16s ; FCN-8s ; UNet ; SegNet ; Proposed network | 0.7670 |  |  |
| SCI-000016 | CNN | Modified SegNet (RGB baseline) ; Modified SegNet (multi-channel inputs, 13 RedEdge-M + 7 S |  |  |  |
| SCI-000017 | CNN | DeepLabv3+ ; MaskFormer | 0.8290 |  | 3-class setting (background, crop, weed) with MSI input; 6-class setting mIoU is 55.52 (Table 4). |
| SCI-000075 | CNN | Mask R-CNN ; YOLOv8 (original) ; YOLOv8 + Real-ESRGAN super-resolution (SR) ; YOLOv8 SR +  | 0.5150 |  | read from figure (Figure 11) caption text; MIOU 0.5150 for YOLOv8 original model (SR model 0.5116, SR+MW 0.5089). |
| SCI-000084 | CNN | VGG-SegNet ; UNet ; Bonnet ; FCN8 ; VGG-UNet (with/without vegetation indices) | 0.7500 |  | Per-dataset 3-class mIoU (with vegetation indices): SugarBeets 0.75, Stuttgart 0.60, Carrots 0.40, Sunflowers 0.41; best dataset value recorded. |
| SCI-000089 | CNN | DeepLabV3+ (SupOnly) ; DeepLabV3+ + Selective-Kernel Attention (CAC) ; ST++ ; SemiWeedNet  | 0.7010 |  | Columns are labeled-ratio splits (2/8, 3/7, 5/5, full); 0.701 is Ours-Resnet50 at full labels; SupOnly Resnet101 reaches 0.705 as a supervised upper bound. |
| SCI-000092 | CNN | PSPNet ; UNet ; SegNet ; FCN8s ; RSS* ; Proposed (HDC + DropBlock + UFAB + SPRB) | 0.8901 |  | Bonn test mIoU 89.01%. Stuttgart test set generalization: ours Res50 70.82%, Res50* 72.94% (Table 7). |
| SCI-000136 | CNN | Mask R-CNN ResNet-50 (scratch/pretrained +/- augmentation) ; Mask R-CNN ResNet-101 (scratc |  | 0.7520 |  |
| SCI-000145 | CNN | Stage-I segmentors ; Stage-II UNet backbones (VGG16, etc.) ; SegNet (single-stage baseline | 0.9200 |  | Best configuration (field 119, 936 test images) using VGG16 UNet in stage-II; class-wise IoU BG 0.98 / Crop 0.85 / Weed 0.91 (also repeated at L207: 'weed = 0.91 in stage-II using VGG16'). |
| SCI-000160 | CNN | U-Net ; DeepLabv3 ; Random Forest | 0.5448 |  | Best on barley (full multispectral config, U-Net). Spatial validation on independent barley field: weed F1 0.6455 (IoU 0.4766). Direct rapeseed transfer poor (F1 0.0534); few-shot fine-tuning recovers F1 0.6274. mIoU value is barley headlin |
| SCI-000203 | CNN | WeedSeg (scenario 1: blurry+sharp train) ; WeedSeg (scenario 2: sharp only) ; DeBlurWeedSe |  |  |  |
| SCI-000271 | CNN | EENet (Proposed) ; SegNet ; U-Net ; Baseline (third method) | 0.8507 | 0.9088 | Best mIoU = EENet with EE Strategy (ablation-reported in text). Table I (per-method IoU/F1 for 5 classes) and Table II (params/FLOPs) are not text-extractable in this PDF extraction. |
| SCI-000483 | CNN | Modified DeepLabV3/DeepLabV3+ (output strides 8/16) [17] ; FPN-based model [17] ; AgriSegN |  |  |  |
| SCI-000488 | CNN | SegNet ; U-Net ; PSPNet ; DeepLabV3+ (etc.) x backbones (VGG16, ResNet50, DenseNet121, Eff | 0.5621 | 0.8824 | mIoU 56.21% on multiclass D2 task reported in abstract (and Table 4 of the paper). |
| SCI-000492 | CNN | FCN-AlexNet (RGB/RGB+ExG/RGB+ExGR/RGB+ExG+ExGR) ; SegNet (same inputs) ; MLC (baseline) |  | 0.8000 |  |
| SCI-000501 | CNN | FCN-32s ; FCN-16s ; FCN-8s ; UNet ; DeepLabv3+ ; (each with ResNet feature extractors) |  | 0.8937 |  |
| SCI-000514 | CNN | FCN-32s ; FCN-16s ; FCN-8s ; Patch-based CNN ; Pixel-based CNN | 0.7520 |  |  |
| SCI-000547 | CNN | Pixel-based-SVM ; FCN-8s ; DFCN ResNet-101 (ASPP-12/ASPP-S/ASPP-L/ASPP-1) +/- CRF | 0.7751 |  |  |
| SCI-000548 | CNN | U-Net ; Modified U-Net | 0.9340 |  | Reported as overall crop-segmentation IoU of the best model (modified U-Net), not mean class IoU. |
| SCI-000565 | CNN | Modified AlexNet-FCN ; VGGNet-FCN ; GoogLeNet-FCN ; ResNet-FCN | 0.6280 |  | Primary row = deployed on-device Jetson TX2 FP16. FP32 on GTX 1060 reaches OA 91.2% / mIoU 70.5% before precision calibration. |
| SCI-000570 | CNN | Mask R-CNN training on real images ; Mask R-CNN on synthetic (real plant instances) ; Mask |  |  |  |
| SCI-000582 | CNN | FCN-8s ; Deeplab (ResNet-101 + CRF) ; Modified FCN-4s | 0.8473 |  |  |
| SCI-000618 | CNN | Mask R-CNN (ResNet50, SmoothLR) ; Mask R-CNN (ResNet50, Li Loss) ; YOLOv5 (leaf counting)  |  |  |  |
| SCI-000624 | CNN | SegNet ; FCN-32s ; FCN-16s ; FCN-8s ; U-Net ; DeepLab v3+ |  |  |  |
| SCI-000650 | CNN | ResNet-38 (MS COCO) ; PSPNet ; DeepLabV3 ; UNet ; DeepLabV3+ | 0.8880 | 0.9680 | MIoU 88.8% for DeepLabV3+ (Weed IoU 83.3, Wheat IoU 87.5, Land IoU 95.6). |
| SCI-000669 | CNN | SSD (MobileNetV3 backbone) ; DeepLabv3+ (MobileNetV3 backbone) ; YOLOv8n ; MobileNetV4-Seg | 0.7680 | 0.8690 | Per-dataset IoU: soybean 76.8% (used for mIoU), corn 69.9%. |
| SCI-000683 | CNN | DeepLabV3 (MobileNet V3) ; LRASPP (MobileNet V3) ; Squeeze U-Net | 0.5545 | 0.6968 | Paper reports a single IoU (55.45%) for the weed/background task; treated as mIoU. LRASPP reaches a higher IoU (59.25%) at much lower speed. |
| SCI-000708 | CNN | U-Net (NoRGN RGB) ; U-Net (SynthNoRGN) ; U-Net (TrueRGN) ; U-Net (SynthFakeRGN) ; U-Net (S | 0.7530 |  | READTHROUGH: 0.753 is U-Net TrueRGN cross-domain generalization example (trained on orthophoto, evaluated on frame data); the record's attributed best_model SynthFakeRGN is not the source of this value. SynthFakeRGN cross-domain mIoU is not |
| SCI-000816 | CNN | UNet-ResNet18/34/50/101 (ImageNet-pretrained) ; NAFNet deblurring front-end (cascaded rest | 0.7185 |  | mIoU on the combined (sharp + motion-blurred) hold-out test set for the proposed UNet-ResNet34 + NAFNet. Baselines on combined set: U-Net++ (w/o NAF) 0.6705, FPN 0.6689, DeepLabV3+ 0.6587; all baselines DEGRADE when NAFNet is naively prepen |
| SCI-000852 | CNN | U-Net ; SU-Net ; SSU-Net (proposed) ; FCN ; DeepLab V3 ; LRASPP ; SegNet | 0.5828 |  | Paper reports a single IoU (58.28%) at 100% network width; treated as mIoU. |
| SCI-000878 | CNN | SCG-UNet (SiLU-CPCA-Gate U-Net) ; baselines: UNet, DeepLabv3+, SegNet, GoogLeNet, UNet++,  | 0.8343 | 0.8077 | RGB+NIR input. Five-fold block CV mIoU 82.92 +/- 0.29%. |
| SCI-000898 | CNN | DeepLabv3+ (supervised baseline) ; Mamba-DeepLabv3+ (semi-supervised, proposed) | 0.8860 | 0.9410 | IoU (0.886) reported as single class-average metric for the binary rapeseed-flower task; treated as mIoU. |
| SCI-000903 | CNN | YOLOv8m ; YOLOv5m ; PointRend ; Mask Scoring R-CNN ; Mask R-CNN ; Cascade Mask R-CNN |  |  |  |
| SCI-000968 | CNN | U-Net ; FCN ; Mobile U-Net (RGB, RGB+DSM, RGB+ExG inputs) | 0.8070 | 0.8899 | Overall Table 4 (RGB+DSM) mIoU 80.7%. Stage-specific (filling stage, RGB+DSM) reached mIoU 87.99%. |
| SCI-001017 | CNN | Original U-Net ; Residual U-Net ; Double U-Net ; Modified U-Net ; AU-Net | 0.8021 |  | Mean IoU over 6 classes on test set. Assessed with Mean Dice Coefficient, Mean IoU, Dice Loss metrics. |
| SCI-001029 | CNN | YOLOv8-Seg ; YOLO series models ; Mask R-CNN |  |  |  |
| SCI-001053 | CNN | YOLOv8n ; YOLOv8s ; YOLOv8m ; YOLOv8l ; Mask R-CNN (Detectron2) ; U-Net |  | 0.9640 |  |
| SCI-001084 | CNN | U-Net ; Attention U-Net ; ResNet U-Net ; SCSE-embedded U-Net (ResUNet SCSE) ; DeepLabV3+ | 0.8290 |  | Headline mIoU 82.90% is DeepLabV3+ (highest); best U-Net variant Attention U-Net 82.82%. ResUNet SCSE weed IoU 0.7749 noted. |
| SCI-001085 | CNN | YOLOv11n-seg ; YOLOv11s-seg (PyTorch vs INT8 RKNN) |  |  |  |
| SCI-001090 | CNN | U-Net ; R2U-Net ; U-Net3+ ; Attention U-Net ; DeepLabV3+ | 0.7990 |  | Value extracted from table row U-Net3+ 79.9%; anomaly/pixel-level, not crop-vs-weed. Best overall model in table. |
| SCI-001153 | CNN | PSPNet ; DeepLabV3+ ; DNLNet ; OCRNet ; Improved OCRNet (channel attention + Lovasz-Softma | 0.9505 |  | Two test areas: TA1 mIoU 94.44%/mAcc 96.78%, TA2 mIoU 95.05%/mAcc 96.89%; best (TA2) recorded. |
| SCI-001173 | CNN | SegNet ; FCN-AlexNet |  |  |  |
| SCI-001203 | CNN | U-Net (baseline) ; SegNet ; ResNet ; Improved U-Net (VGG19 encoder + CBAM) (proposed) | 0.8323 |  |  |
| SCI-001210 | CNN | FCN ; PSPNet ; UNet ; DeepLabV3+ ; MAENet | 0.9374 |  | MIoU on the best farmland multi-classification test set (Dataset 3); per-dataset results in tables. Per-class farmland IoU 92.48%/96.49% on Datasets 1/2. |
| SCI-001333 | CNN | U-Net ; MobileNetV2-UNet ; BiSeNetV2 ; FFB-BiSeNetV2 | 0.8028 |  |  |
| SCI-001335 | CNN | DeepLabV3+ (VGG16) ; DeepLabV3+ (ResNet50) ; DeepLabV3+ (ResNet101) ; DeepLabV3+ (Xception | 0.7274 |  | Validation IoU (0.7274) from table row: Val Accuracy / Val IoU / Val Dice with standard deviations. |
| SCI-001368 | CNN | SSD (object detection) ; YOLO (object detection) ; U-Net (semantic segmentation) ; Mask R- |  |  |  |
| SCI-001376 | CNN | U-Net (semantic segmentation) ; YOLOX (object detection / instance segmentation) |  |  |  |
| SCI-001379 | CNN | U-Net + VGG16 ; U-Net + VGG19 ; FPN + VGG16 ; FPN + VGG19 |  | 0.8080 |  |
| SCI-001382 | CNN | HSI-TransUNet (baseline) ; HRS-UNet (proposed) |  |  |  |
| SCI-001411 | CNN | FCN ; U-Net ; DeepLabV3+ ; SE-enhanced U-Net (proposed) | 0.8599 | 0.9244 | Binary (Kenaf seedling vs soil) IoU 85.99% with SE-U-Net; FCN/U-Net/DeepLabV3+ compared. 'Dice' reported alongside IoU. |
| SCI-001413 | CNN | Baseline U-Net variant(s) ; EDM-UNet (proposed) | 0.8945 |  |  |
| SCI-000001 | Hybrid | Lightweight transformer-CNN hybrid (proposed) ; RGB-only variant | 0.7888 |  | MSI (RGB+NIR+RE) model; RGB-only variant achieves lower mIoU of 63.08%. |
| SCI-000754 | Hybrid | ResNet-50 ; EfficientNet-B0 ; ViT ; Mask R-CNN ; YOLOv9 ; Hybrid CNN-RNN ; ConvLSTM ; MSG- | 0.8780 | 0.9160 | IoU (87.8%) reported under the multi-label classification reformulation; treated as mIoU. |
| SCI-000962 | Hybrid | Segmenter ; SwiftNet ; DeepLabV3 ; BiSeNet ; MANet ; PSPNet ; LW-Segnet (Ours) ; LW-Unet ( | 0.8706 | 0.9200 | IoU = 87.06% for LW-Segnet on WN145 (Table 6, best across the three varieties); no single mIoU stated - mean across varieties not given. |
| SCI-000003 | Transformer | ViT (vanilla baseline) ; ViT+FV ; ViT+LR ; ViT+FV+LR ; ViT+Modular Routing+FV+LR (proposed |  |  |  |
| SCI-000013 | Transformer | ViT-Small (PA16) ; ViT-Base (PA16) ; Swin Transformer (MoCo-v3 / MAE pretrained on msuav50 | 0.5200 |  | Mean IoU over 3 classes on the spatially independent Task B test set (WeedMap Switzerland/Sequoia, 62 chips), best of the MoCo-v3-pretrained Swin U-Net at the 75% training-data fraction; matches ImageNet-unfrozen baseline. Task A (Germany/R |
| SCI-000067 | Transformer | Hough+SLIC+ResNet50 ; Hough+CC ; Hough+SLIC ; RoWeeder (SegFormer) ; RoWeeder (Pyramid dec |  | 0.7530 |  |
| SCI-000074 | Transformer | WeedFormer (SegFormer-B2 + CBAM + ASPP) ; DeepLabv3+ ; SegFormer-B1 ; SegFormer-B2 ; multi | 0.8027 | 0.8877 | mIoU 80.27% on WeedsGalore test. RGB-only input. |
| SCI-000083 | Transformer | U-Net variant + backbones (ConvNeXt V2 Tiny, Mamba Vision-T, FastViT_S12, FastViT_SA24, Re | 0.9225 |  | Best backbone ConvNeXt V2 Tiny 480x352: mIoU 0.9225, IoU crop 0.8990, IoU weed 0.8843, Dice crop 0.9424, Dice weed 0.9372, OA 0.979, kappa 0.9586, 22.90 img/s on GTX 1660Ti. |
| SCI-000505 | Transformer | FPN ; UNet ; DeepLabV3+ ; UNet++ ; MANet ; SegFormer (mit_b5) ; DPT + DINOv2 (vit_l/vi_tb/ | 0.9075 |  | Headline mIoU 90.75% is for the HR test set ensemble; best single model DPT+DINOv2(vit_b) mIoU 90.18% (Table 3 row 20). |
| SCI-000810 | Transformer | SegFormer-B0 (semantic segmentation) ; YOLO11n/s, RT-DETR-R18, BiSeNetV2, MobileNetV3-LRAS | 0.8049 |  | Held-out CropAndWeed_v1 test set. Best of four segmentation models: DeepLabV3+ mIoU 0.7774, MobileNetV3-LRASPP 0.7631, BiSeNetV2 0.7278. Per-class IoU for SegFormer-B0: crop 0.7665, weed 0.6565 (also reported for all segmentation models in  |
| SCI-001023 | Transformer | SegFormer (MiT-B1) ; SegFormer (MiT-B3) ; DeepLabV3 ; DeepLabV3+ ; AAFormer ; AgriFusion ( | 0.4931 | 0.6785 |  |
| SCI-001096 | Transformer | U-Net ; U-Net Xception-Style ; SegNet ; DeepLabV3+ ; Swin-UNet/Swin-Transformer ; SegForme | 0.8970 |  | Binary vegetation/background IoU on Opuntia test. After consolidation: IoU 0.894 on Opuntia and 0.760 on Agave. Not class-differentiated crop-weed; task is vegetation-cover quantification. |
| SCI-000005 | UNCLASSIFIED | VISA (two-stream radiance + index) ; baselines: Random Forest + indices, SegNet (RGB/MSI), | 0.7560 | 0.8470 | Within-plot protocol mIoU 0.756 +/- 0.004. Strongest multispectral baseline SegFormer-B1 MSI mIoU 0.744, weed IoU 0.616. Cross-plot/cross-year transfer lower. weed value is per-class IoU (0.635), not F1. |
| SCI-000091 | UNCLASSIFIED | VGG-16 FCN ; GoogleNet FCN ; AlexNet FCN ; U-Net ; U-Net++ ; SegNet ; DeepLabv3 ; Huang et | 0.8100 |  | Per-class IoU: Rice 0.81, Weeds 0.79, Others 0.84; mIoU 0.81 (macro mean). |
| SCI-000346 | UNCLASSIFIED | PRC-Net (proposed) ; SOTA: SegNet, UNet++, R2U-Net, TransUnet, Swin-Unet, DeepLabv3, UNet3 | 0.8397 | 0.8910 | Headline mIoU = best dataset (WeedMap RedEdge-M 0.8397). Sequoia 0.6520; Sesame Aerial 0.6961. Recorded best; alternatives in ambiguity. |
| SCI-000371 | UNCLASSIFIED | U-Net ; SegNet ; FSFNet ; DFANet ; FASSDNet ; ENet ; UNetFormer ; LMFFNet ; ResLMFFNet (pr | 0.8840 | 0.9130 |  |
| SCI-000489 | UNCLASSIFIED | Proposed model (trained on field images, cross-domain to UAV) ; Baseline models without pr | 0.7670 |  |  |
| SCI-001005 | UNCLASSIFIED | HRNet+OCR+PSA (teacher) ; No distillation ; Vanilla KD ; TAKD ; Annealing ; Continuation K |  | 0.8630 |  |
| SCI-001292 | UNCLASSIFIED | RPD-Net ; D-RPD-Net ; baselines (ERFNet, DeepLabV3+, SegNeXt-T, SegFormer-B0) | 0.8747 |  | mIoU 87.47±0.75 on PhenoBench validation. Abstract headline: ~70 IoU on the weed class. D-RPD variant improves weed IoU (+0.55 mIoU, +1.4 weed IoU). After reparameterization params drop 0.189M->0.14M, MACs 13.45G->4.71G (768 res). |
| SCI-001334 | UNCLASSIFIED | SegNet (DenseNet121/ResNet50) ; UNet (DenseNet121/EfficientNetB0) ; DeepLabV3+ (MobileNetV | 0.8742 | 0.9307 | mIoU (87.42%) on Motion-Blurred Sorghum dataset; CoFly-WeedDB mIoU is 71.35%. |
| SCI-000225 | VLM | Qwen2-VL-7B ; LLaVA-1.5-7B ; LLaMA3-LLaVA-Next-8B | 0.4661 | 0.4916 | IoU (0.4661) reported under VLM coordinate-to-text reformulation of segmentation; treated as mIoU. |
| SCI-001371 | VLM | PP-LiteSeg ; PP-LiteSeg-SSA (proposed) | 0.9479 |  |  |

## Table C — rows excluded from the architecture comparison (UNCLASSIFIED / VLM / no-model) — manual review required

| Study | Family | best_model | backbone |
|---|---|---|---|
| SCI-000005 | UNCLASSIFIED | VISA (within-plot mIoU 0.756, weed IoU 0.635) | Two-stream (radiance conv + index-stream windowed self-attention/state-space/Slot Attention) |
| SCI-000010 | UNCLASSIFIED | Semi-supervised GAN (Red+NIR, 50% labeled data) |  |
| SCI-000091 | UNCLASSIFIED | Proposed framework (DenseInception encoder + ASPP + attention decoder) | DenseInception (encoder) + ASPP + attention |
| SCI-000346 | UNCLASSIFIED | PRC-Net (PRF fusion + CSA attention + LCFE bottleneck) | Progressive receptive-field context-aware (PRC) blocks |
| SCI-000371 | UNCLASSIFIED | ResLMFFNet | SEM-B blocks (split-extract-merge bottleneck) with residual connections, PMCA attention, FFM-A/FFM-B fusion, MAD attention decoder with dropout 0.5 |
| SCI-000489 | UNCLASSIFIED | Proposed cross-domain model with enhanced preprocessing (field dataset) | Proposed deep learning model (encoder-decoder) |
| SCI-001005 | UNCLASSIFIED | Continuation KD (student: lightweight Lawin-L0) | Lawin-L0 (student) / HRNet+OCR+PSA (teacher) |
| SCI-001292 | UNCLASSIFIED | RPD-Net (reparameterized pixel-difference network; mIoU 0.8747 on PhenoBench val) | RPD blocks (PDC/repconv), lightweight |
| SCI-001334 | UNCLASSIFIED | MSEA-Net | Encoder-decoder with MSCA + EEBA modules |
