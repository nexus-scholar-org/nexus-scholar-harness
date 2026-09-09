# Full-text read-through batch 02

## SCI-000160 — From barley to rapeseed: few-shot fine-tuning of semantic segmentation models for weed detection using UAV multispectral imagery

attribution: CONFIRMED for model=U-Net (full multispectral config: RGB + NIR + RedEdge + NDVI + NDRE + VARI) backbone=U-Net (best) dataset=Barley fields (independent-field spatial validation) + rapeseed (cross-crop transfer), UAV multispectral

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.5448 | CONFIRMED | "The full configuration (RGB + NIR + RedEdge + NDVI + NDRE + VARI) combined with U-Net achieved the best performance, with a weed F1-score of 0.5833 and an mIoU of 0.5448" (line 75); "U-Net achieved the highest weed F1-score (0.5833) and IoU (0.4117), together with the highest overall mIoU (0.5448)" (line 286) |
| weed_F1 | 0.6455 | CONFIRMED | "The U-Net model retrained using the combined Barley 1-V1 and Barley 1-V2 datasets and evaluated on the independent Barley 2-V2 field achieved a weed F1-score of 0.6455 and an IoU of 0.4766 (Table 1)" (line 307) |
| device | No inference hardware/platform reported; no embedded/edge deployment (research/prototype pipeline) | CONFIRMED | No inference GPU/edge platform mentioned anywhere in the extracted text. Only acquisition drones are described: "Images were acquired at an altitude of 120 m using a DJI Phantom 4 RTK for RGB imagery (20 MP) and a DJI Matrice 600 Pro equipped with a MicaSense Altum-PT camera for multispectral acquisition" (line 110). |
| resolution_input | 256 | CONFIRMED | "From the images and their associated masks, patches of 256 × 256 pixels were generated with 50% overlap (stride = 128)" (line 355); inference "Image patches of 256 × 256 pixels were extracted with 50% overlap (stride = 128 pixels), matching the input dimensions used during model training" (line 573) |
| framework | Deep learning framework not stated; models implemented from scratch | CONFIRMED | "U‑Net (Ronneberger et al., 2015) was implemented from scratch without pre-trained weights." (line 205). No deep-learning framework (PyTorch/TensorFlow) is named in the extracted text. |

## SCI-000203 — Improved weed segmentation in UAV imagery of sorghum fields with a combined deblurring segmentation model

attribution: CONFIRMED for model=DeBlurWeedSeg (NAFNet + WeedSeg) backbone=NAFNet (deblur) + WeedSeg (UNet-style decoder with ResNet encoder, trained on sharp images) dataset=self-collected UAV sorghum (blurry-sharp pairs)

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| Dice | 0.8373 | CONFIRMED | Table 4 (Combined column): "DeBlurWeedSeg 0.8741 0.8011 0.8373" (line 229); abstract: "relative improvement of 13.4% in terms of the Sørensen-Dice coefficient" (line 56) |
| resolution_input | 128 | CONFIRMED | "a 128 × 128 px2 patch was extracted for each plant instance, with the plant in the center" (line 119) |

## SCI-000225 — Adapting Vision-Language Models for Precision Agriculture: A Study on Crop Segmentation based on UAV Remote Sensing Data

attribution: CONFIRMED for model=Qwen2-VL-7B (LoRA-fine-tuned) backbone=Qwen2-VL-7B dataset=Self-collected UAV crop dataset (corn, barley, tobacco)

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.4661 | CONFIRMED | "Qwen2- VL-7B achieved the highest overall performance with an F1- score of 0.4916 and IoU of 0.4661" (line 204); Table III Overall row: "Qwen2-VL-7B ... Overall 0.5325 0.4799 0.4916 0.4661" (line 244) |
| F1 | 0.4916 | CONFIRMED | Same quotes as mIoU. |
| crop_F1 | 0.7842 | CONFIRMED | "Qwen2-VL-7B achieving an impressive F1- score of 0.7842 for tobacco identification" (line 204); Table III Tobacco row: "0.8081 0.7798 0.7842 0.7564" (line 242) |
| resolution_input | 512 | CONFIRMED | "we employed a sliding window cropping strategy to divide them into multiple 512 × 512 pixel sub-images" (line 102) |
| framework | LoRA (rank 8, bf16, AdamW, lr 1e-4, cosine w/ warmup 0.1, 3 epochs, effective batch 8) | CONFIRMED | "The LoRA rank was set to 8...a learning rate of 1.0×10⁻⁴ and implemented a cosine learning rate scheduler with a warmup ratio of 0.1...Training was performed for 3 epochs with a per-device batch size of 1 and gradient accumulation steps of 8, resulting in an effective batch size of 8. Mixed precision training (bf16) was enabled" (line 198); Table II: "Optimizer AdamW" (line 208) |

## SCI-000271 — Crop Segmentation of Unmanned Aerial Vehicle Imagery Using Edge Enhancement Network

attribution: CONFIRMED for model=EENet (proposed) backbone=EENet (residual Feature Extractor + Edge/Semantic Enhancers + FFM) dataset=self-collected UAV RGB (rice plots)

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.8507 | CONFIRMED | "Statistical analysis shows that the mIoU is 0.8097 and the F1_score is 0.8778 without EE Strategy, and the mIoU is 0.8507 and the F1_score is 0.9088 when EE Strategy is used." (line 223) |
| F1 | 0.9088 | CONFIRMED | Same quote as mIoU. |
| resolution_input | 224 | CONFIRMED | "After manually labeling the ground truth using LabelMe [16], we clip the size of the images of the selected regions to 224× 224." (line 148) |

## SCI-000286 — Real-Time Weed Segmentation in Tobacco Crops Utilizing Deep Learning on a Jetson Nano

attribution: CONFIRMED for model=U-Net-MobileNetV2 backbone=MobileNetV2 (U-Net encoder) dataset=Deviation: records say "self-collected UAV tobacco (Mansehra, Pakistan)"; text states the public Tobacco Aerial Dataset (Mavic Mini drone images of eight tobacco fields in Mardan, Pakistan), with real-time field validation performed in Mansehra. Model/backbone confirmed; dataset description should say "public Tobacco Aerial Dataset (Mardan), real-time validation in Mansehra".

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.851 | CONFIRMED | "The methodology proposed in this study demonstrated 96% accuracy, accompanied by a mean intersection over union value of 0.851." (line 87) |
| PA | 0.96 | CONFIRMED | "The methodology proposed in this study demonstrated 96% accuracy, accompanied by a mean intersection over union value of 0.851." (line 87) |
| device | NVIDIA Jetson Nano | CONFIRMED | "The successful deployment of the model on a mobile setup in the tobacco fields of Mansehra, Pakistan" (line 91); "U-Net-MobileNetV2 was used to detect weeds in aerial tobacco field images. The NVIDIA Jetson Nano edge computing platform was used to implement this model for real-time agricultural inference." (line 188) |
| precision | ONNX (PyTorch, CUDA) | CONFIRMED | "the trained model was saved and converted into ONNX format. The ONNX model was subsequently implemented on the Jetson" (line 146); "NVIDIA's CUDA GPU acceleration allowed us to use PyTorch's deep learning framework on the Jetson Nano." (line 166) |
| resolution_input | 224 | CONFIRMED | "As the input image is 224 x 224 x 3, the MobileNetV2 backbone processes it through multiple convolutional layers" (line 162) |
| framework | PyTorch (ONNX) with CUDA on Jetson Nano | CONFIRMED | "NVIDIA's CUDA GPU acceleration allowed us to use PyTorch's deep learning framework on the Jetson Nano." (line 166) |
| fps | 3.69 | CONFIRMED | Derived: 1000/271.29 = 3.686 FPS. Source: "The combined duration of the model and real-time inference is observed to be 271.29milliseconds." (line 266). FPS is not stated literally but is consistent with the reported latency. |
| latency_ms | 271.29 | CONFIRMED | "The combined duration of the model and real-time inference is observed to be 271.29milliseconds." (line 266) |

## SCI-000346 — Unmanned aerial vehicle-based weed segmentation from multispectral imagery in an edge computing environment

attribution: CONFIRMED for model=PRC-Net (PRF fusion + CSA attention + LCFE bottleneck) backbone=Progressive receptive-field context-aware (PRC) blocks dataset=WeedMap (RedEdge-M, Sequoia) + Sesame Aerial

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.8397 | CONFIRMED | "PRC-Net is validated on the publicly available WeedMap (RedEdge-M, Sequoia) and Sesame Aerial datasets, achieving mean intersection over union (MIOU) values of 0.8397, 0.6520, and 0.6961, respectively" (line 55); Table 2 case 12: "0.9845 0.8321 0.7025 0.8397 0.9239 0.8603 0.8910" (line 717) |
| F1 | 0.891 | CONFIRMED | Table 2 case 12 (line 717): "12 (Proposed) ... 0.9845 0.8321 0.7025 0.8397 0.9239 0.8603 0.8910"; defined in text as harmonic mean of global precision/recall (P 0.9239 / R 0.8603). |
| device | NVIDIA Jetson TX2 (desktop comparison: Intel/GPU 10.53 ms) | CONFIRMED | "PRC-Net demonstrated notable computational efficiency on the Jetson TX2, thereby substantiating its suitability for edge-device-based weed control applications" (line 92); "An evaluation on the Jetson TX2 was conducted to assess the computational efficiency of PRC-Net in embedded system environments" (line 984) |
| resolution_input | 320 | CONFIRMED | "The original datasets comprise patches with a resolution of 480 × 360 pixels, which were resized to 320 × 320 pixels." (line 698) |
| framework | Python 3.10.12, PyTorch 2.6.0 on Ubuntu 20.04 (Intel i7-3770K 4 cores, 32 GB RAM) | CONFIRMED | "The experiments were performed using Python 3.10.12 and PyTorch 2.6.0." (line 687); "The experimentation was performed on a desktop workstation running Ubuntu 20.04 and equipped with an Intel® Core™ i7-3770K ... 32 GB of RAM" (line 687) |
| fps | 17.05 | CONFIRMED | "on the Jetson TX2 it requires 58.65 ms and achieves 17.05 FPS, which satisfies the real-time requirement for on-board UAV deployment" (line 986) |
| latency_ms | 58.65 | CONFIRMED | "on the Jetson TX2 it requires 58.65 ms and achieves 17.05 FPS" (line 986) |
| params_M | 13.3 | CONFIRMED | "the proposed model contains 13.30 M parameters, requires 0.58 GB of GPU memory, and incurs 41.46 GFLOPs" (line 986) |
| gflops | 41.46 | CONFIRMED | "the proposed model contains 13.30 M parameters, requires 0.58 GB of GPU memory, and incurs 41.46 GFLOPs" (line 986) |

## SCI-000440 — On-Edge Weed Detection Using Unmanned Aerial Vehicles

attribution: CONFIRMED for model=U-Net with RGB bands (480 training images) as stated by authors backbone=U-Net dataset=CoFly (records name "CoFly-WeedDB"; text: "achieves state-of-the-art results on the CoFly dataset" line 41)

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.5192 | CONFIRMED | "the simple RGB model slightly outperformed both attention and multispectral U-Net models using 480 samples with a mean IoU score of 51.92% and a Dice score of almost 67.21%" (line 350); Table 3: "RGB (3) 480 U-Net 0.5192 0.6721" (line 332) |
| Dice | 0.6721 | CONFIRMED | Same quotes as mIoU. |
| device | NVIDIA Jetson Nano | CONFIRMED | "The Jetson Nano model chosen for this paper had 16 GBs of memory and an NVIDIA Maxwell GPU with 128 NVIDIA CUDA cores." (line 270) |
| precision | FP16 (quantized) | CONFIRMED | "the models' precision was adjusted from FP32 to FP16, effectively reducing their sizes, latency, and power consumption" (line 270) |
| framework | TensorFlow-Lite / TensorRT (ONNX) | CONFIRMED | "we converted the chosen models into two optimized compressed formats using the TensorFlow Lite and Tensor-RT libraries" (line 270) |
| fps | 1.864 | CONFIRMED | Table 5 (Tensor-RT column): "U-Net 3.6858 0.2713 4.684 0.5366 1.864 4.806" (line 435) |
| latency_ms | 536.6 | CONFIRMED | Table 5 (Tensor-RT column): "U-Net 3.6858 0.2713 4.684 0.5366 1.864 4.806" (line 435). Inference time 0.5366 s = 536.6 ms (recorded in ms). |
| power_w | 4.806 | CONFIRMED | Table 5 (Tensor-RT column): "U-Net 3.6858 0.2713 4.684 0.5366 1.864 4.806" (line 435) |

## SCI-000482 — Deep Learning with Unsupervised Data Labeling for Weed Detection in Line Crops in UAV Images

attribution: CONFIRMED for model=CNN with unsupervised (line-detection-based) data labeling backbone=ResNet18 dataset=Self-collected UAV bean and spinach fields

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| resolution_input | 64 | CONFIRMED | "In this experiments, we used a 64 by 64 window to create the weed and crop training databases." (line 209) |

## SCI-000483 — AgriSegNet: Deep Aerial Semantic Segmentation Framework for IoT-Assisted Precision Agriculture

attribution: CONFIRMED for model=AgriSegNet backbone=ResNet-50 (DeepLabV3+) dataset=Agriculture-Vision (UAV farmland anomaly challenge dataset)

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| Dice | 0.67 | CONFIRMED | "For validation set, our predicted segmentation obtained a dice score/F1 score of 67%." (line 246) |
| device | Cloud GPU server (training; per text) | CONFIRMED | "The model is trained on Nvidia Titan XP GPU." (line 214); "retraining the cloud GPU Server would not be necessary." (line 262) |
| resolution_input | 512 | CONFIRMED | "Each image comprises of four 512 × 512 color channels, which include RGB and Near Infra-red (NIR)." (line 186). Dataset/training-tile size; model also uses multi-scale (0.5x/1.0x) sub-images at inference. |
| framework | PyTorch (batch size 4, SGD, cosine annealing LR 1e-2, dice loss + adaptive class weighting loss) | CONFIRMED | "The model is implemented in the PyTorch framework. We train the model using mini batches of size 4" (line 188); "The loss function is optimized using SGD optimizer. To train our network, the initial learning rate was set at 1e −2. We used the cosine annealing learning rate scheduler while training our model." (line 214); "We used combination of dice loss and adaptive class weighting loss as our loss function during training." (line 188) |

## Batch summary

| study_id | CONFIRMED | MISMATCH | NOT_FOUND | LOW_CONF |
|----------|-----------|----------|-----------|----------|
| SCI-000160 | 5 | 0 | 0 | 0 |
| SCI-000203 | 2 | 0 | 0 | 0 |
| SCI-000225 | 5 | 0 | 0 | 0 |
| SCI-000271 | 3 | 0 | 0 | 0 |
| SCI-000286 | 8 | 0 | 0 | 0 |
| SCI-000346 | 9 | 0 | 0 | 0 |
| SCI-000440 | 8 | 0 | 0 | 0 |
| SCI-000482 | 1 | 0 | 0 | 0 |
| SCI-000483 | 4 | 0 | 0 | 0 |
| **Overall** | **45** | **0** | **0** | **0** |