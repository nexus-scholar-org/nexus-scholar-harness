# Full-text read-through batch 06

## SCI-001017 — Multi-Class Weed Quantification Based on U-Net Convolutional Neural Networks Using UAV Imagery

attribution: CONFIRMED for model=Residual U-Net (Mean IoU 0.8021) backbone=U-Net variants (Original/Double/MU-Net/AU-Net/Residual) dataset=Custom UAV potato-crop dataset (Andean weeds; 6 classes: background, potato, broadleaf dock, dandelion, kikuyu, other weeds). "The Residual U-Net is the best model for adjusting the resulting multi-class segmentation to the silhouettes of the native plants under study, with a mean IoU of 0.8021" (line 652; abstract line 38); "successfully processing six categories: background, potato, Broadleaf dock, Dandelion, Kikuyu, and other weeds" (line 652).

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.8021 | CONFIRMED | "The Residual U-Net is the best model for adjusting the resulting multi-class segmentation to the silhouettes of the native plants under study, with a mean IoU of 0.8021" (line 652); Table 4 (test set, 10% = 210 images): "Residual U-Net 0.9721 0.7984 0.7409 0.7730 0.5907 0.9376 0.8021" (line 443); "the Residual U-Net model performs well on the test set with a mean IoU = 0.8021" (line 445). Six-class mean IoU on the held-out test set. |
| Dice | 0.8763 | CONFIRMED | Table 3 (validation): "Residual U-Net (balanced extended dataset) 0.1236 0.8763 0.8053" (lines 412–414); "achieving better performance with a Dice Loss of 0.1236, a mean Dice Coefﬁcient of 0.8763, and a mean IoU of 0.8053" (line 418). Validation-set value (balanced dataset); test-set results are per-class IoU only (Table 4). |
| PA | 0.824 | CONFIRMED | Table 6 (literature comparison): "Our work 2026 Residual U-Net ... Potato ... Kikuyu, other weeds 6 0.8021 82.4" (lines 609–613). Accuracy 82.4% appears only in this table; the results section reports IoU/Dice only (record carries a reduced-confidence note for this mapping). |
| device | None - offline. Models trained and inferred on Google Colab Pro+ (Nvidia A100 40 GB VRAM, 83.5 GB RAM); 515 MB model deemed "large for UAV-based scouting" with on-device embedded inference left to future compression | CONFIRMED | "The U-Net model and its variants were trained on Google Colab Pro+ using Tensor-Flow/Keras 2.8.0 and the Nvidia A100 GPU 40 GB VRAM, with 83.5 GB RAM and 201.2 GB of disk space." (line 261); "most integrated devices would consider our model large (515 MB) for UAV-based scouting... future work could explore lightweight model compression strategies—such as pruning, quantization, or knowledge distillation—to reduce storage requirements further and enable on-device inference on embedded hardware" (line 647). No on-device deployment; inference measured on the Colab cloud GPU only (line 647). |
| resolution_input | 128 | CONFIRMED | Table 2 training hyperparameters: "Input size 128 × 128 × 3" (all five models; line 291); "58.5 ms (17 fps) per 128 x 128 image patch (model input size)" (line 536); "58.5 ms per 128 × 128 patch (≈17 fps) on the Colab platform" (line 647). |
| framework | TensorFlow/Keras 2.8.0 on Google Colab Pro+ (Nvidia A100 40 GB); Adam (lr 0.001) | CONFIRMED | "trained on Google Colab Pro+ using Tensor-Flow/Keras 2.8.0 and the Nvidia A100 GPU 40 GB VRAM" (line 261); Table 2 optimizer rows: "Adam (learning rate = 0.001)" for all five variants (lines 293–311). |
| fps | 17 | CONFIRMED | "in a relatively fast inference time of 58.5 ms (17 fps) per 128 x 128 image patch (model input size), occupying 515 MB of storage" (line 536); "58.5 ms per 128 × 128 patch (≈17 fps)" (line 647). 17 fps stated literally. |
| latency_ms | 58.5 | CONFIRMED | Same sources as fps (lines 536, 647): inference latency 58.5 ms. |
| params_M | 135 | CONFIRMED | "The Residual U-Net model maintains the basic architecture of the U-Net but with skip connections in multiple layers. The total trained parameters were nearly 135 M, with a size of 515 MB." (line 263). |

## SCI-001023 — AgriFusion: Multiscale RGB-NIR Fusion for Semantic Segmentation in Airborne Agricultural Imagery

attribution: CONFIRMED for model=AgriFusion (MiT-B1) backbone=Dual encoder (Mix Transformer MiT-B1 RGB + ResNet-18 NIR, multi-level attention fusion + MLP decoder) dataset=Agriculture-Vision benchmark (7 classes). NOTE: the record labels the family "CNN", but the architecture is hybrid CNN+Transformer ("an Asymmetric Dual-Encoder Network... a Transformer model (Mix Transformer (MiT)) captures the global context from RGB images while a CNN model (ResNet) extracts features from single-channel NIR images", line 99; "MiT-B1 (RGB) with ResNet-18 (NIR)", line 121).

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.4931 | CONFIRMED | "Experiments conducted on the Agriculture-Vision dataset demonstrate that AgriFusion achieves a mean Intersection over Union (mIoU) of 49.31%, Pixel Accuracy (PA) of 81.72%, and F1 score of 67.85%" (abstract, line 34); Table 1: "AgriFusion (MiT_B1) Hybrid 49.31 81.72 67.85" (line 329); "AgriFusion achieves the best performance across all evaluation metrics, with an mIoU of 49.31%" (line 333). |
| F1 | 0.6785 | CONFIRMED | Same abstract quote (line 34); Table 1 F1 column: "67.85" (line 329); "and F1 score of 67.85%" (line 333). The paper reports this metric as "F1 score" (matching the record key), not Dice. |
| PA | 0.8172 | CONFIRMED | Same abstract quote (line 34); Table 1 PA column: "81.72" (line 329). |
| framework | PyTorch; trained on NVIDIA RTX 2080Ti GPU (22 GB) for 100 epochs, batch size 64 | LOW_CONF | Hardware/training details verbatim: "All experiments were conducted on a workstation equipped with an NVIDIA RTX 2080Ti GPU (22 GB memory)... we set the batch size to 64 and trained the model for 100 epochs to ensure convergence. The optimizer was Adam with an initial learning rate of 0.001." (line 291). BUT the library "PyTorch" (and any DL framework — no torch/TensorFlow/Keras matches exist) is never named in the extracted text, so that component of the claim is unverifiable. |

## SCI-001029 — Enhancing sustainable Chinese cabbage production: a comparative analysis of multispectral image instance segmentation techniques

attribution: CONFIRMED for model=YOLOv8-Seg backbone=YOLOv8-Seg (best s-scale, 11.7 M params) dataset=Self-collected UAV multispectral Chinese cabbage imagery (1 class). "YOLOv8s-Seg strikes a balance between model size and detection speed" (line 223); SAM-assisted dataset of "24,774 distinct Chinese cabbage segmentation instances... 923 images" (line 227).

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| resolution_input | 640 | CONFIRMED | "orthomosaic images derived from assorted band combinations were segmented into 640 × 640 pixel frames, culminating in a collection of 923 images" (line 227). |
| framework | PyTorch 1.12.0, Python 3.8, CUDA 11.3; AMD Ryzen 7 5800X 8-core 3.8 GHz, NVIDIA GeForce RTX 3060 | CONFIRMED | "This study’s experiments were carried out on a platform featuring a 64-bit Windows 10 operating system, powered by an AMD Ryzen 75,800× 8-Core Processor at 3.8GHz and equipped with an NVIDIA GeForce RTX 3060 GPU. The computational framework for deep learning comprised Python 3.8, PyTorch 1.12.0, and CUDA 11.3." (line 452; OCR renders "Ryzen 75,800×" for the Ryzen 7 5800X). |
| params_M | 11.7 | CONFIRMED | Table 6 (YOLOv8-Seg scales): "YOLOv8s-Seg 97.7 96.5 93.9 97.6 95.6 87.5 11.7" (line 724) — Parameters column, 11.7 M. |

## SCI-001046 — Implementing Innovative Weed Detection Techniques for Environmental Sustainability

attribution: CONFIRMED for model=Mask R-CNN (UAV-tailored) backbone=MobileNetV3 (inverted-residual blocks with SE attention; chosen for real-time/low-resource deployment under UAV constraints) dataset=Self-collected cluttered UAV plantation images (2 classes: weeds and crops). "The proposed study chose MobileNetV3 due to its reputation for handling complicated datasets... ideal for real-time applications and low-resource environments because of its lightweight design" (line 163); "a specialized UAV-tailored Mask R-CNN, incorporating instance segmentation, outperforms conventional methods... The evaluation of AP values reveals... 89.1% for weeds, 88.9% for crops, and a remarkable overall precision of 89.4%" (line 189); dataset "comprising 200 UAV images" (line 189); "categorization of every segment... into categories of either crops or weeds" (line 126).

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| framework | Keras / TensorFlow GPU 1.8.0, cuDNN 7.0, Python 3.5.2, Intel Xeon E5-2643v3 3.40 GHz CPU | CONFIRMED | "An Intel Xeon E5-2643v3 CPU at 3.40 GHz was used... Our weed detection system had 64 GB of RAM... An NVIDIA Quadro M4000 GPU with 8 GB of video memory... Intel Xeon Toolkit 9.0, cuDNN V7.0, Python 3.5.2, TensorFlow GPU 1.8.0, and Keras were important frameworks." (line 180). |

## SCI-001053 — Deep Learning for Weed Detection and Segmentation in Agricultural Crops Using Images Captured by an Unmanned Aerial Vehicle

attribution: CONFIRMED for model=YOLOv8s backbone=YOLOv8s (CSPDarkNet53) dataset=Self-collected UAV images of soybean and bean crops (augmented 3021-image set). "The YOLOv8s variant achieved higher performance with an mAP50 of 97%, precision of 99.7%, and recall of 99%" (abstract, line 57); "An augmented dataset of 3021 images was used to train the models" (line 502).

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| F1 | 0.964 | CONFIRMED | Table 10 (500 epochs): "YOLOv8s CSPDarkNet53 0.980 0.987 0.985 0.964" (line 553; header line 551 "Model Backbone Acc_weed mAP_weed mAP Score F1-Score"); Table 11: "500 0.957 0.970 0.964" (line 575). YOLOv8s model-level F1-score 0.964; YOLOv7 0.951, YOLOv5s 0.960 for comparison (line 553). |
| PA | 0.961 | CONFIRMED | "The training set accuracy was 97.1%, with a loss value of 0.024, while for validation, the accuracy was 96.1%, with a loss value of 0.033." (line 637). This is the U-Net (ResNet50) validation accuracy at 100 epochs, interpreted as overall pixel accuracy per the record's ambiguity note; YOLO/Mask R-CNN "Acc" values (0.95–0.99) are detection accuracy, not pixel accuracy. |
| device | NVIDIA Tesla T4 GPU (Google Colaboratory); AMD Ryzen 7 6800H CPU; 16 GB RAM; Windows 10 | CONFIRMED | "Training and testing of all models in this study were carried out in Google Colaboratory using an NVIDIA graphics processor Google Compute Engine Tesla T4 in Python 3" (line 381); Table 4: "Operating System Windows 10 CPU AMD Ryzen 7 6800H GPU NVIDIA Tesla T4 RAM 16 GB (8GB x 2) Python V3.12" (line 390). |
| resolution_input | 640 | CONFIRMED | "The images were resized to 640 x 640 pixels and 512 x 512 pixels... for the YOLOv8, YOLOv7, YOLOv5s, and Mask R-CNN (with Detectron2) and U-Net models, respectively." (line 208). YOLOv8 variants → 640. |
| framework | PyTorch 2.1 / CUDA 12.2 (Python 3.12), Ultralytics (YOLO), Detectron2 (Mask R-CNN) | LOW_CONF | Verbatim components: Table 4: "Python V3.12 Pytorch V2.1 OpenCV V4.9.0 CUDA V12.2" (line 390); Detectron2 confirmed throughout ("instance segmentation dataset, in the 'COCO Segmentation' format, using the Roboflow tool", lines 366–368; Mask R-CNN "with three different backbones for the comparison, including R101-DC5, R101-FPN, and X101-FPN", line 383). BUT "Ultralytics" appears nowhere in the extracted text (Select-String: 0 matches); YOLO training is described via Roboflow tooling and MS COCO pretrained weights only (lines 158, 381). Rendering the Ultralytics component of the claim unverifiable. |

## SCI-001084 — A Preliminary Study on U-Net for Crop Monitoring Using Low-Altitude Drone Imagery

attribution: CONFIRMED for model=DeepLabV3+ (highest mIoU 82.90%); ResUNet-SCSE best for weed IoU 77.49%; best U-Net variant Attention U-Net backbone=U-Net variants (Baseline/Attention/ResUNet/ResUNet-SCSE) vs DeepLabV3+ (ResNet-50) dataset=WeedsGalore (public multispectral UAV maize dataset; 3 classes: background/crop/weed). "No real UAV hardware was deployed. All experiments used the public WeedsGalore multispectral UAV dataset released by Helmholtz GFZ (2025)" (line 88); "DeepLabV3+ [12] with a ResNet-50 backbone was included as a reference baseline" (line 130).

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.829 | CONFIRMED | "Among all evaluated architectures, DeepLabV3+ achieved the highest overall performance with an mIoU of 82.90%. However, the leading U-Net variants exhibited highly competitive results: Attention U-Net reached 82.82% mIoU, only 0.08% lower than DeepLabV3+, followed closely by ResUNet-SCSE with 82.69% mIoU." (line 165); Table 2: "DeepLabV3+ ... 82.90 ... 39.8" (line 157); "ResUNet-SCSE achieved the highest IoU-Weed (77.49%)" (line 167). Headline 82.90% is the DeepLabV3+ baseline. |
| device | No physical hardware deployed (preliminary feasibility study); training/GPU details not specified | CONFIRMED | Negative: "As this study is conducted at a preliminary feasibility stage, no real UAV hardware was deployed." (line 88). No training GPU/hardware named — training alongside a GPU is only implied by "the batch size was set to 2 due to GPU memory constraints" (line 126). |
| resolution_input | 600 | CONFIRMED | "All input images are standardized to a spatial resolution of 600×600 pixels." (line 106). |
| params_M | 31.4 | CONFIRMED | "By comparison, U-Net variants were substantially lighter: Attention U-Net (31.4M parameters) and Baseline U-Net (31.0M parameters)" (line 167); "Relative to DeepLabV3+, Attention U-Net reduced model size by 21.1% (≈8.4 million parameters) while maintaining nearly identical accuracy" (line 176). NOTE: 31.4 M is the Attention U-Net (best U-Net variant), not the headline DeepLabV3+ (39.8 M); the reduction is consistent (39.8 − 8.4 ≈ 31.4). |

## SCI-001085 — Accelerating UAV-Based Agricultural Field Segmentation Using YOLOv11 and Rockchip NPU Quantization

attribution: CONFIRMED for model=YOLOv11s-seg (RKNN INT8; mAP@0.5 0.85) backbone=YOLOv11 (seg heads) dataset=Combined real UAV + synthetic agricultural dataset (3 classes: crop/weed/soil). Table II: "YOLOv11s-seg.rknn 0.85 0.79 0.85 16" (line 170). NOTE: the record labels the dataset "Combined UAE + synthetic"; the text reads "A combined dataset consisting of real UAV images and synthetic samples was used for crop, weed, and soil segmentation" (line 47) — the real+synthetic nature is confirmed, but the "UAE" label does not appear verbatim.

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| device | Orange Pi 5+ (Rockchip RK3588, 6 TOPS NPU) | CONFIRMED | "deployed on an Orange Pi 5+ platform based on the RK3588 processor" (line 51); "The Rockchip RK3588 platform... integrating an NPU capable of delivering up to 6 TOPS of computational performance" (line 78); "Experimental evaluation was performed on an Orange Pi 5+ single-board computer based on the Rockchip RK3588 system-on-chip. The platform integrates a dedicated neural processing unit supporting INT8 inference acceleration with a theoretical performance of up to 6 TOPS." (line 140). |
| precision | INT8 (post-training quantized RKNN) | CONFIRMED | "post-training INT8 quantization was applied using a representative calibration dataset" (line 132); "INT8 post-training quantization was performed using a calibration subset containing 100 representative images randomly selected from the training dataset" (line 158). |
| resolution_input | 512 | CONFIRMED | "All images were resized to 512×512 pixels and annotated for three classes: crop vegetation, weeds, and soil background." (line 112); "Input images were resized to 512×512 pixels." (line 158). |
| framework | RKNN Toolkit2 / Ultralytics | CONFIRMED | "The models were trained using the Ultralytics implementation of YOLOv11seg" (line 158); "a conversion pipeline based on RKNN Toolkit2 was implemented. First, trained PyTorch models were exported to the ONNX format. Next, post-training INT8 quantization was applied... Finally, the optimized models were converted into the RKNN format and executed on the Rockchip neural processing unit." (line 132). |
| fps | 62.5 | CONFIRMED | Derived from latency: Table II header "Model Precision Recall mAP@0.5 Latency" (line 166); row "YOLOv11s-seg.rknn 0.85 0.79 0.85 16" (line 170) → 16 ms latency; 1000/16 = 62.5 FPS. FPS is not stated literally (latency measured in ms per line 144). |
| latency_ms | 16.0 | CONFIRMED | Table II row "YOLOv11s-seg.rknn 0.85 0.79 0.85 16" (line 170), Latency column (header, line 166). |

## SCI-001090 — Resolution-Accuracy Trade-offs in UAV-Based Semantic Segmentation for Precision Agricultural Imagery

attribution: CONFIRMED for model=U-Net3+ (mIoU 79.9% at 20 cm/pixel) backbone=U-Net variants / DeepLabV3+ (best config across the 10/20/40 cm-per-pixel GSD grid) dataset=Agriculture-Vision (UAV-acquired agricultural anomalies). "U-Net3+ achieves best mIoU (79.9%) which is better than all the other models and also better than its own performance at higher resolution" (lines 257–258); Table 4 (20 cm/pixel): "U-Net3+ 79.9" (line 509).

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.799 | CONFIRMED | "At medium resolution (20 cm/pixel) there is a remarkable change in performance. U-Net3+ achieves best mIoU (79.9%) which is better than all the other models" (lines 257–258); Table 4: "U-Net3+ 79.9" (line 509); "At low resolution (40 cm/pixel), U-Net3+ maintains robust performance (mIoU = 76.94%)" (line 262). Anomaly/pixel-level segmentation (not crop-vs-weed). |
| Dice | 0.9545 | CONFIRMED | Class-level Dice (DC), U-Net on Water Way at 20 cm/pixel: "U-Net 3509 195 196 54 3596 .9814 .9331 .8645 .9271 .9545 26" (Table row, line 318); identical Water Way DC at 10 cm/pixel: "U-Net 3509 195 196 107 1742 .9924 .9715 .9693 .913 .9545 26" (line 454). Highest single (per-class) value reported; the headline best config (U-Net3+, 20 cm) reaches DC 0.9135 on weed cluster — per-class values, not an average (per the record's ambiguity note). |
| device | Not specified (training-time analysis only; no inference-hardware details given) | CONFIRMED | Negative: no GPU/training/inference hardware is named anywhere in the extracted text; the study is a resolution (GSD) trade-off analysis. |

## SCI-001173 — Real-time Crop Classification Using Edge Computing and Deep Learning

attribution: CONFIRMED for model=SegNet backbone=VGG16 (SegNet encoder) dataset=Self-collected UAV crop fields (NCHU Experimental Farm; 4 classes: rice, corn, road, background). "This research experiment was carried out in the NCHU Experimental Farm. The DJI Matrice 100 drone with ASUS Tinker Board S embedded system" (lines 57–58); "The image semantic segmentation model adopts SegNet network architecture" (lines 68–69); "SegNet adopted the VGG16 network architecture in the first half of the network" (line 155); "the annotation categories are divided into four categories: rice, corn, road and background" (line 163).

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| PA | 0.8944 | CONFIRMED | Table I (per-class recall + OA): "SegNet 96.07 90.61 77.90 88.21 89.44" (line 195; OA column, header line 187); "The average inference speed of the semantic image segmentation model is 0.7s with segmentation identification accuracy is 89%." (lines 80–81). Per-class OA: rice 96.07%, corn 90.61%, road 77.90%, background 88.21%; SegNet OA 89.44%. |
| device | ASUS Tinker Board S (onboard) + backend server (4G LTE offload) | CONFIRMED | "The research uses the DJI Matrice 100 as the flight carrier, and is equipped with the ASUS Tinker Board S embedded system and the Logitech C925e network camera. The image is captured in seconds, and the stored image is immediately transmitted to the remote inference server via the 4G mobile network." (line 193); "The ASUS Tinker Board S runs a folder monitoring program and sends images over the 4G LTE network to the backend server" (lines 60–63). |
| framework | Keras + TensorFlow (Docker/NGCT) | CONFIRMED | "The inference server environment is Ubuntu16.04.5 x86-64, and runs the containerized environment of Docker. The image inference service uses the TensorFlow container image released by NVIDIA GPU Cloud, and Keras is installed as the machine learning framework." (line 199); training: "the nchc-tensorflow-18.08-py3 environment, the tensorflow is updated to version 1.10.1, and the keras-2.2.2 and scikit-image suites are installed" on TWGC (Taiwan GPU Cloud) (line 177). |
| fps | 1.43 | CONFIRMED | Derived: "The average inference speed of the semantic image segmentation model is 0.7s" (lines 80–81) → 1000/700 ≈ 1.43 FPS. FPS is not stated literally; derived from the 0.7 s inference time. |
| latency_ms | 700 | CONFIRMED | "The average inference speed of the semantic image segmentation model is 0.7s with segmentation identification accuracy is 89%." (lines 80–81). 0.7 s = 700 ms. |

## Batch summary

| study_id | CONFIRMED | MISMATCH | NOT_FOUND | LOW_CONF |
|----------|-----------|----------|-----------|----------|
| SCI-001017 | 9 | 0 | 0 | 0 |
| SCI-001023 | 3 | 0 | 0 | 1 |
| SCI-001029 | 3 | 0 | 0 | 0 |
| SCI-001046 | 1 | 0 | 0 | 0 |
| SCI-001053 | 4 | 0 | 0 | 1 |
| SCI-001084 | 4 | 0 | 0 | 0 |
| SCI-001085 | 6 | 0 | 0 | 0 |
| SCI-001090 | 3 | 0 | 0 | 0 |
| SCI-001173 | 5 | 0 | 0 | 0 |
| **Overall** | **38** | **0** | **0** | **2** |