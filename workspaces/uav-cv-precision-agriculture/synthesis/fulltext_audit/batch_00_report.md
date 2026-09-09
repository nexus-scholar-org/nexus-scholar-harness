# Full-text read-through batch 00

## SCI-000001 — Lightweight Multispectral Crop-Weed Segmentation for Precision Agriculture

attribution: CONFIRMED for model=Transformer-CNN hybrid (MSI: RGB + NIR + RE) backbone=Lightweight transformer-CNN hybrid dataset=WeedsGalore

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.7888 | CONFIRMED | "The Multispectral Input (MSI) model, using RGB, NIR, and RE, achieved an mIoU of 78.88%" (line 134) |
| resolution_input | 600 | CONFIRMED | "each tile is processed into a 5-channel array (RGB, NIR, Red-Edge) and resized to 600x600 pixels" (line 98) |
| framework | AdamW lr 1e-4 + cosine annealing, batch 8, Cross-Entropy + class-balanced focal | CONFIRMED | "The AdamW optimizer was employed with an initial learning rate of 1e-4, cosine annealing, and a batch size of 8...A combination of Cross-Entropy Loss and Class-Balanced Focal Loss addressed weed class imbalance." (line 134) |
| params_M | 8.7 | CONFIRMED | "In contrast, our model achieves 78.88% mIoU with only 8.7M parameters" (line 162) |

## SCI-000003 — Modular Transformer Architecture for Precision Agriculture Imaging

attribution: CONFIRMED for model=ViT+Modular Routing+FV+LR backbone=Vision Transformer dataset=Genze et al. sorghum weed drone video (blur/noise degraded frames)

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| Dice | 0.8492 | CONFIRMED | "Employing the modular approach, the Dice-Score was enhanced to 0.8492, surpassing the results of the original authors" (line 288) |
| framework | PyTorch, Python 3.12.10, scikit-learn, scikit-image; Apple M4 Pro (24 GB, 10-cor | CONFIRMED | "The experiments were conducted on an Apple computer equipped with an Apple M4 Pro processor, 24GB of memory, and a 10-core GPU. The software utilized Python 3.12.10, along with pytorch, scikit-learn, and scikit-image" (line 235) |

## SCI-000005 — BAWSeg: A UAV Multispectral Benchmark for Barley Weed Segmentation

attribution: CONFIRMED for model=VISA (within-plot mIoU 0.756, weed IoU 0.635) backbone=Two-stream (radiance conv + index-stream windowed self-attention/state-space/Slot Attention) dataset=BAWSeg (four-year UAV multispectral benchmark, barley paddocks near Kondinin, Western Australia)

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.756 | CONFIRMED | "When training and testing on disjoint spatial blocks from the same paddocks and seasons, VISA reaches 0.756 mIoU" (line 674) |
| F1 | 0.847 | CONFIRMED | Table 2 within-plot row: "P R F1 OA kappa ... 0.851 0.843 0.847 0.946 0.794" (line 598) |
| PA | 0.946 | MISMATCH | Table 2 within-plot row shows OA=0.946. The value 0.946 is Overall Accuracy (OA), not pixel-level Precision or Recall. The source does not report a metric named "PA" with value 0.946; P=0.851, R=0.843 in the same row. |
| device | None - post-flight workstation deployment only: single NVIDIA GeForce RTX 4090 (24 GB) workstation (AMD Ryzen 9 7950X, 32 GB RAM, Ubuntu 22.04.4 LTS). Authors explicitly state the system is 'more suitable for reliable offline decision support than for direct onboard UAV inference'. | CONFIRMED | "Hardware and software. All experiments ran on a single workstation with Ubuntu 22.04.4 LTS, an AMD Ryzen 9 7950X CPU, 32 GB RAM...and one NVIDIA GeForce RTX 4090 GPU with 24 GB VRAM." (line 512); "This makes the current system more suitable for reliable offline decision support than for direct onboard UAV inference" (line 698) |
| precision | FP16 (inference measured at FP16 batch 1; evaluation FP32; training automatic mi | CONFIRMED | "Training used automatic mixed precision, and evaluation used FP32." (line 512); ablation: "Throughput is measured at batch size 1 using FP16 inference" (line 643) |
| resolution_input | 256 | CONFIRMED | "Models were trained for 50 epochs on 256 x 256 patches." (line 514) |
| framework | PyTorch 2.7 / CUDA 12.6 / Python 3.10; AdamW lr 6e-4 cosine decay after 1500-ite | CONFIRMED | "The software stack used Python 3.10 and PyTorch 2.7 with CUDA 12.6." (line 512); "The initial learning rate was set to 6 x 10-4 and decayed with a cosine schedule after a linear warm-up of 1500 iterations." (line 514) |
| fps | 78 | CONFIRMED | "The full model uses 22.8 M parameters, 33.6 GFLOPs, 2.60 GB FP16 memory, and runs at 78 FPS for 256 x 256 patches on a single RTX 4090" (line 698) |
| latency_ms | 12.8 | CONFIRMED | 78 FPS = 1000/78 = 12.82 ms. Source confirms "runs at 78 FPS for 256 x 256 patches on a single RTX 4090" (line 698). Latency is consistent but not explicitly stated as ms; derived from FPS. |
| params_M | 22.8 | CONFIRMED | "The proposed two-stream fusion achieves mIoU 0.756 +/- 0.004 and weed IoU 0.635 with 22.8M parameters" (line 626) |
| gflops | 33.6 | CONFIRMED | "The full model uses 22.8 M parameters, 33.6 GFLOPs, 2.60 GB FP16 memory" (line 698) |

## SCI-000007 — Vision-Language Semantic Grounding for Multi-Domain Crop-Weed Segmentation

attribution: CONFIRMED for model=VL-WS (mean Dice 0.9164) backbone=ResNet-101 (DeepLabv3+ spatial encoder) + frozen CLIP dataset=UAV Soybean (McGill), PhenoBench, GrowingSoy, ROSE (multi-domain)

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| Dice | 0.9164 | CONFIRMED | "with VL-WS achieving a mean Dice score of 91.64% and outperforming the CNN baseline by 4.98%" (line 43); Table 1: VL-WS Avg=91.64 (line 355) |
| device | Desktop workstation: NVIDIA RTX 3080 GPU (10 GB); no embedded/edge deployment | CONFIRMED | "All experiments were conducted on a workstation equipped with an NVIDIA RTX 3080 GPU (10 GB)." (line 375). No embedded deployment mentioned. |
| resolution_input | 512 | CONFIRMED | "Input images are resized to 512 x 512 pixels" (line 375) |
| framework | PyTorch (PyTorch Lightning); AdamW optimizer LR 3e-5 (visual encoder) / 3e-6 (te | CONFIRMED | "the model is implemented in PyTorch using PyTorch Lightning. We employ the AdamW optimizer with an initial learning rate of 3x10-5 for the visual encoder and 3x10-6 for the text encoder." (line 375) |

## SCI-000010 — Semi-supervised GAN for Classification of Multispectral Imagery Acquired by UAVs

attribution: CONFIRMED for model=Semi-supervised GAN (Red+NIR, 50% labeled data) backbone= dataset=weedNet (MAV multispectral, sugar beet field)

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| F1 | 0.85 | CONFIRMED | "Results showed the F1 score of about 0.85 for two channels with 50% labeled data." (line 113) |

## SCI-000012 — Transferring learned patterns from ground-based field imagery to predict UAV-based imagery for crop and weed semantic segmentation in precision crop farming

attribution: CONFIRMED for model=Proposed network backbone=SegNet encoder, 42,037,391 params dataset=Self-collected maize field (ground) and UAV images (transfer)

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.767 | CONFIRMED | Table 2: "Proposed ... 0.767" (mIOU column); text: "The proposed network performed best among other networks with 0.859 mOA and 0.767 mIOU" (line 690) |
| mPA | 0.859 | CONFIRMED | Table 2: "Proposed 0.989 0.979 0.746 0.577 0.841 0.744 0.859 0.767" where 0.859 = mOA; text confirms "0.859 mOA" (line 690). mOA = mean Pixel Accuracy (mPA). |
| device | None - offline (trained with 4x NVIDIA Tesla P100-SXM2, 16 GB; no edge deployment) | CONFIRMED | "All networks were implemented using the Tensorflow framework and were trained with four NVIDIA Tesla P100-SXM2 GPU (16GB memory)." (line 655) |
| resolution_input | 512 | CONFIRMED | "randomly cropped image tiles (512*512) from the resized images (1200*800)" (line 384) |
| framework | TensorFlow (Adam optimizer, initial lr 0.005, batch size 24) | CONFIRMED | "All networks were implemented using the Tensorflow framework" (line 655); "The network was trained with the Adam optimizer using the initial learning rate of 0.005." (line 657); "The batch size was set as 24." (line 669) |
| params_M | 42.04 | CONFIRMED | "There are 42,037,391 parameters in total" (line 473) = 42.04M |

## SCI-000013 — Self-supervised training for high-resolution close-range multispectral remote sensing imagery

attribution: CONFIRMED for model=Swin Transformer pretrained with MoCo-v3 + U-Net decoder (best on Task A, cross-sensor on Task B) backbone=Swin Transformer (best), ViT-S/B compared dataset=WeedMap (Task A: Germany RedEdge-M; Task B: Switzerland Sequoia) + msuav500k+N pretraining

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.52 | CONFIRMED | "Overall, it achieved the best performance with IoU of 0.52 on the dataset at the 75% training data used, matching the ImageNet unfrozen model that also achieved 0.52 IoU." (line 257) |
| device | None - offline experimentation on a single GPU; no on-device/embedded deployment reported | CONFIRMED | Paper describes GPU-based pretraining and fine-tuning only; no embedded/on-device deployment. |
| resolution_input | 224 | CONFIRMED | "divided into 224x224 image chips" (line 116); "randomly cropped to 224x224 pixels" (line 176) |
| framework | PyTorch-based (SpecDeepMap API from EnMAP-Box, custom extension for MAE/MoCo-v3 | CONFIRMED | "we employed a custom adaptation of the SpecDeepMap API, extended to incorporate MAE and MoCo-v3 model encoders" (line 186); PyTorch-based SSL training described throughout. |

## SCI-000016 — WeedMap: A large-scale semantic weed mapping framework using aerial multispectral imaging and deep neural network for precision farming

attribution: CONFIRMED for model=Modified SegNet with 9 input channels (RGB + CIR/NDVI) backbone=VGG16 (SegNet encoder) dataset=Self-collected UAV multispectral orthomosaics (RedEdge-M and Sequoia)

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| device | NVIDIA Titan X GPU (desktop) | CONFIRMED | "we often fail to allocate six batches into our GPU memory, which is the maximum in our case with NVIDIA Titan X" (line 1282) |

## SCI-000017 — WeedsGalore: A Multispectral and Multitemporal UAV-based Dataset for Crop and Weed Segmentation in Agricultural Maize Fields

attribution: CONFIRMED for model=DeepLabv3+ (MSI, 3-class) backbone=ResNet50 dataset=WeedsGalore

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.829 | CONFIRMED | Table 3: "DeepLabv3+ ... MSI ... 82.90" (mIoU column) (line 231); text: "DeepLabv3+ MSI 98.45 72.93 77.31 82.90" |
| resolution_input | 600 | CONFIRMED | "the central 600x600 pixels...were cropped, which were finally annotated" (line 153) |
| framework | Adam (lr 1e-3 DeepLabv3+ / 3e-5 MaskFormer), batch 8, standard augmentation; tra | CONFIRMED | "We train the model with the same configuration as in Sec. 4.1.1...The learning rate is set to 0.001 and 0.00003 for DeepLabv3+ and MaskFormer respectively...batch size of 8, and standard data augmentation" (line 258) |

## Batch summary

| study_id | CONFIRMED | MISMATCH | NOT_FOUND | LOW_CONF |
|----------|-----------|----------|-----------|----------|
| SCI-000001 | 4 | 0 | 0 | 0 |
| SCI-000003 | 2 | 0 | 0 | 0 |
| SCI-000005 | 10 | 1 | 0 | 0 |
| SCI-000007 | 4 | 0 | 0 | 0 |
| SCI-000010 | 1 | 0 | 0 | 0 |
| SCI-000012 | 6 | 0 | 0 | 0 |
| SCI-000013 | 4 | 0 | 0 | 0 |
| SCI-000016 | 1 | 0 | 0 | 0 |
| SCI-000017 | 3 | 0 | 0 | 0 |
| **Overall** | **35** | **1** | **0** | **0** |
