# Full-text read-through batch 07

## SCI-001203 — Research on the Corn Stover Image Segmentation Method via an Unmanned Aerial Vehicle (UAV) and Improved U-Net Network

attribution: CONFIRMED for model=Improved U-Net (VGG19 + CBAM + Focal-Dice loss) backbone=VGG19 (first five layers) dataset=Self-collected UAV corn stover field images (2 classes: straw vs background). "The model utilizes transfer learning by replacing the encoder with the first five layers of the VGG19 network" (line 37); "replacing the first five layers of the VGG19 [37] network with the U-Net coding module" (line 204); "The Focal-Dice Loss function is selected" (line 106); "pixel-level binary classification task" (line 217); UAV acquisition "with a specific focus on corn fields as the research subject" (line 106).

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.8323 | CONFIRMED | "resulting in an impressive increase of 9.69 percentage points to reach 83.23%" (line 337); Table 4 (ablation, Expt. 4 = VGG19 + CBAM + Focal-Dice): "4 ✓ ✓ ✓ 83.23 93.87" (line 335); comparison table: "Our algorithm 83.23 90.66 91.98 93.87" (line 375). |
| PA | 0.9387 | CONFIRMED | "Experimental results prove that our algorithm achieves 93.87% accuracy in segmenting and extracting corn stalks from images with complex backgrounds" (line 37); Table 4 PA column: "93.87" (line 335); "The PA achieved a remarkable 93.87%, while the mIoU reached an impressive 83.23%" (line 379). Reported as overall "accuracy" and treated as pixel accuracy (PA) per the record's ambiguity note. |
| framework | PyTorch 1.7.1, Python 3.7, CUDA 11.0, OpenCV/Numpy/PIL; NVIDIA GeForce GTX 3050 | CONFIRMED | "using Pytorch 1.7.1 as the deep learning framework; the main dependency libraries are Random, Opencv, Numpy, PIL, etc.; and the Python version and CUDA are 3.7 and 11.0, respectively. The parameters of the hardware equipment are an Intel Core i5-1200H CPU (16 GB of RAM), an NVIDIA GeForce GTX 3050 GPU, and 4G memory." (line 252). |

## SCI-001333 — Real-Time Identification of Rice Weeds by UAV Low-Altitude Remote Sensing Based on Improved Semantic Segmentation Model

attribution: CONFIRMED for model=FFB-BiSeNetV2 backbone=BiSeNetV2 dataset=Self-collected UAV low-altitude rice paddy imagery (incl. video data; 3 classes: weed, rice, others). "two improved identiﬁcation models, MobileNetV2-UNet and FFB-BiSeNetV2, were proposed based on the semantic segmentation models U-Net and BiSeNetV2" (line 49); "The number of valid label categories is three, which are weed, rice, and others" (line 156).

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.8028 | CONFIRMED | "The FFB-BiSeNetV2 model improved the segmentation accuracy compared with the BiSeNetV2 model and achieved the highest pixel accuracy and mean Intersection over Union ratio of 93.09% and 80.28%" (line 49); Table 1: "FFB-BiSeNetV2 93.09 80.28 88.02 88.46 64.38" (line 349). |
| PA | 0.9309 | CONFIRMED | Same abstract quote (line 49); Table 1 PA column: "93.09" (line 349); "the PA and MIoU of FFB-BiseNetV2 reached 93.09% and 80.28%" (line 333). |
| device | NVIDIA Jetson AGX Xavier | CONFIRMED | "transplanted the improved models to the embedded hardware platform Jetson AGX Xavier" (line 49); "ﬁnally the trained improved model networks are transplanted to the embedded hardware platform NVIDIA Jetson AGX Xavier for models inference and prediction experiments" (line 252). Deployment/inference device (training ran on the PC platform, line 252). |
| precision | FP16 (TensorRT) | CONFIRMED | "the optimized MobileNetV2-UNet model and FFB-BiSeNetV2 model inferred 45.05 FPS and 40.16 FPS for a single image under the weight accuracy of FP16" (line 49); "it supports FP32/FP16/INT8 operation precisions" (line 256); "the inference speed under FP16 precision reached 40.16 FPS" (line 423). |
| resolution_input | 800 | MISMATCH | Claimed value is 800, but the actual model input is "the input images were resized to 352 × 480 pixels" (line 260). The "800" in the paper is the cropped dataset image width, not a model input: "was cut into four images and four label images with a resolution of 650 × 800 ... to reduce the size of input images for deep learning models" (line 156). No model is run at 800. |
| framework | TensorRT | CONFIRMED | "used TensorRT to optimize the model structure to improve the inference speed" (line 49); "we used the TensorRT tool to optimize model structure and accelerate model inference" (line 312). Inference optimization framework (training framework is TensorFlow, line 252). |
| fps | 40.16 | CONFIRMED | "the optimized MobileNetV2-UNet model and FFB-BiSeNetV2 model inferred 45.05 FPS and 40.16 FPS... under the weight accuracy of FP16" (line 49); "the inference speed under FP16 precision reached 40.16 FPS" (line 423); Table 3: "FFB-BiSeNetV2 19.42 25.58 40.16" (line 440). FFB-BiSeNetV2 FP16 = 40.16; MobileNetV2-UNet = 45.05. |
| params_M | 17.39 | CONFIRMED | Table 2 (model parameter comparisons): "FFB-BiSeNetV2 17,394,450 ..." (line 382) → 17,394,450 = 17.39 M. |
| gflops | 10.7 | CONFIRMED | Table 2 row: "FFB-BiSeNetV2 17,394,450 111 40.51 83.19 8.64 10.7 104.17" (line 382), GFLOPs column = 10.7. |

## SCI-001334 — MSEA-Net: Multi-Scale and Edge-Aware Network for Weed Segmentation

attribution: CONFIRMED for model=MSEA-Net backbone=Encoder-decoder with MSCA + EEBA modules dataset=Motion-Blurred UAV Images of Sorghum Fields (3 classes: sorghum, weeds, soil). "we propose the Multi-Scale and Edge-Aware Network (MSEA-Net)... introduce the Multi-Scale Spatial-Channel Attention (MSCA) module... the Edge-Enhanced Bottleneck Attention (EEBA) module integrates Sobel-based edge detection" (line 34); "The dataset includes pixel-level annotations with three classes, i.e., sorghum, weeds, and soil" (line 285).

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.8742 | CONFIRMED | "achieving a mean Intersection over Union (IoU) of 87.42% on the Motion-Blurred UAV Images of Sorghum Fields dataset and 71.35% on the CoFly-WeedDB dataset" (line 34); "On the Motion-Blurred UAV Images of Sorghum Fields dataset (Table 4), MSEA-Net again achieves the highest mean IoU (87.42%)" (line 397); Table 4: "MESA-Net MESA-Net 87.42 93.54 92.61 93.07" (line 391). |
| F1 | 0.9307 | CONFIRMED | "It also demonstrates superior precision (93.54%), recall (92.61%), and F1-score (93.07%)" (line 397); Table 4 F1 column: "93.07" (line 391). |
| resolution_input | 256 | CONFIRMED | "6300 image patches of 256 × 256 pixels were extracted from 19 images" (line 285); "Before being fed into the network, all images were preprocessed into 256 × 256 patches" (line 289); Table 6 header: "Resolution (256 × 256)" (line 269). |
| framework | PyTorch 2.4.0 (Python 3.8.9), Adam lr 0.002, batch 64, 200 epochs, early stop patience 20 | CONFIRMED | "All experiments were implemented in Python (Python version 3.8.9) using the PyTorch (version 2.4.0) framework and conducted on an NVIDIA GeForce RTX 4090" (line 289); Table 2 hyperparameters: "Epochs 200 Learning Rate (LR) 0.002 Batch Size 64 Patience 20 Optimizer Adam" (line 296); "early stopping was employed, with training halted if the validation loss failed to improve over 20 consecutive epochs" (line 289). |
| latency_ms | 2.0 | CONFIRMED | "MSEA-Net achieves an average inference time of 0.0020 s per image" (line 503); Table 10: "MESA-Net MESA-Net 06.74 25.74 0.0020" (line 605). 0.0020 s = 2.0 ms. |
| params_M | 6.74 | CONFIRMED | "MSEA-Net also maintains a compact architecture with only 6.74 M parameters and a model size of 25.74 MB" (line 34); "MSEA-Net maintains only 6.74 M parameters and a model size of 25.74 MB" (line 397); Table 10: "06.74 25.74 0.0020" (line 605). |

## SCI-001335 — Research on Intelligent Image Segmentation Based on UAV Remote Sensing and DeepLabV3+ Model

attribution: CONFIRMED for model=DeepLabV3+ (MobileNetV2) backbone=MobileNetV2 dataset=AliCloud Tianchi UAV crop imagery (Xingren, Guizhou; 5 classes: barley, maize, tobacco, Job's tears, buildings). "a controlled-variable comparison of five backbones—VGG16, ResNet50, ResNet101, Xception, and MobileNetV2—within the DeepLabV3+ segmentation framework" (line 86); "Data are sourced from AliCloud Tianchi[6]: GB-scale UAV images of farmland in Xingren, Guizhou, annotated at the pixel level for five classes (barley, maize, tobacco, Job's tears, buildings)" (line 98); "MobileNetV2 had the smallest memory footprint and robust performance, suitable for deployment" (line 322).

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.7274 | CONFIRMED | Validation table row: "MobileNetV2 0.8851[2] 0.0053 0.7274[2] 0.0126 0.7732[2]" (line 249) — Val Accuracy / Std Dev / Val IoU / Std Dev / Val Dice. Validation IoU 0.7274. |
| Dice | 0.7732 | CONFIRMED | Same table row (line 249), Val Dice = 0.7732. |
| PA | 0.8851 | CONFIRMED | Same table row (line 249), Val Accuracy = 0.8851, reported as "Val Accuracy" in the table and treated as pixel accuracy (PA) per the record's ambiguity note. |
| resolution_input | 224 | CONFIRMED | "the image is scaled down from 1024*1024 to 224*224" (line 113); tiling source: "Original images and labels were tiled into 1024×1024 patches" (line 102). |
| framework | PyTorch; Adam (lr 0.001), cross-entropy loss with class weights [1.0, 2.0, 2.0, 2.0, 2.0] | CONFIRMED | "All experiments used Adam (lr=0.001), cross-entropy loss, batch size 4, 50 epochs" (line 86); "class_weight = torch.tensor([1.0, 2.0, 2.0, 2.0, 2.0, 2.0])" (line 113) — PyTorch identified via the native torch.tensor API. |
| latency_ms | 20.4 | CONFIRMED | "Inference Time(s) 0.0204[4] ..." (line 312), MobileNetV2 column in the per-backbone inference-time table. 0.0204 s = 20.4 ms. |
| params_M | 4.25 | CONFIRMED | "Quantity of Parameters 140M 4.25M 22.91M 25.64M 44.71M" (line 232, MobileNetV2 column); "Quantity of participants 4.25M[1] 25.64M[3] 44.71M[4] 140M[5] 22.91M[2]" (line 320). |

## SCI-001368 — Kernelytics: Multispectral Drone Imagery and Deep Learning for Early Corn Assessment

attribution: CONFIRMED for model=U-Net with composite 5-band input, tile size 32 (crop & weed segmentation) backbone=ResNet-101 (SSD/U-Net/Mask R-CNN) dataset=Self-collected UAV multispectral (DJI Phantom 4 Multispectral; corn/weed, Creggan Hill Farm). "Aerial images were collected with a DJI Phantom 4 Multispectral Agriculture Drone at Creggan Hill Farm in Troupsburg, New York" (line 192); "The SSD, U-Net, and Mask R-CNN architectures utilized a Resnet-101 backbone" (line 194); "The U-Net model with the composite band and an image chip tile size of 32x32 pixels had the best performance for corn segmentation" (line 278).

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| PA | 0.98 | CONFIRMED | "A U-Net model of the same structure trained on the weed data achieved an accuracy of 98% for weed segmentation." (line 278). Value verbatim (98%); the paper does not define the metric — "accuracy" for weed segmentation is mapped to pixel accuracy per the record's low-confidence (<0.7) ambiguity note. |
| crop_F1 | 0.66 | CONFIRMED | Table II (U-Net metrics at tile size 32): "Non-Corn Corn Precision 97 72 Recall 98 60 F1 98 66" (line 272) — corn per-class F1 = 66 (= 0.66) at tile size 32, composite bands (tile size 64 corn F1 = 48, line 274). Overall/mean F1 not reported. |
| resolution_input | 32 | CONFIRMED | "The Mask R-CNN model with the composite band and an image chip tile size of 32x32 pixels achieved the highest precision score" (line 238); "The U-Net model with the composite band and an image chip tile size of 32x32 pixels had the best performance for corn segmentation" (line 278). |

## SCI-001376 — Mini Drone-Based Precision Agriculture for Indonesian MSMEs: A Low-Cost AI-Assisted Monitoring System

attribution: CONFIRMED for model=YOLOX (fruit instance segmentation) backbone=YOLOX (instance segmentation, integrated with Streamlit); U-Net for land-zone semantic segmentation dataset=DJI Mini 2 SE drone video of a 300 m^2 vegetable plot (Indonesia; 11 object classes). "By leveraging mini drones (DJI Mini 2 SE) and lightweight AI models... performs video processing offline using semantic segmentation (U-Net) and object detection (YOLOvX)" (line 59); "A YOLOX model integrated with Streamlit was used to perform object-level segmentation on frames extracted from drone livestreams." (line 394); "achieved a mean Average Precision (mAP) of 0.78 across 11 object classes" (line 398).

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| framework | Python Streamlit app, OBS Studio + private YouTube Live transport; processing of... | CONFIRMED | "The interface, built with Streamlit, provides real-time insights" (line 59); "Using OBS Studio (Open Broadcaster Software) installed on a laptop, the phone's display is mirrored via USB/airplay. The live video feed is broadcast to a private YouTube Live channel" (line 359); "A Python-based Streamlit application runs in parallel, pulling frames from the livestream" (line 359); "A YOLOX model integrated with Streamlit" (line 394). |
| latency_ms | 6000 | CONFIRMED | "The end-to-end latency from video capture to segmentation visualization in the Streamlit app remained under 6 seconds using a standard laptop." (line 408). 6 s = 6000 ms (reported as an upper bound — "under 6 seconds"). |

## SCI-001379 — Eggplant Leaf Semantic Segmentation in Aerial Imagery for Precision Agriculture

attribution: CONFIRMED for model=U-Net with VGG19 encoder (highest F1); FPN + VGG16 recommended for low latency backbone=VGG16 / VGG19 (U-Net & FPN) dataset=LeavesUAV (self-collected; 2 classes: leaf vs background). "The encoders utilized for each model were chosen from the VGG16 and VGG19 networks that had been pre-trained on the ImageNet dataset" (line 139); "this paper built a LeavesUAV dataset by obtaining images of mature eggplant leaves from the authors' own eggplant farming output" (line 135).

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| F1 | 0.808 | CONFIRMED | "U-Net with VGG19 has a consistently exceptional performance, attaining the highest F1 score of 0.8080 at the 0.5 threshold" (line 254); comparison: "a strong F1 score of 0.8002 at the 0.75 threshold" (line 225). Value 0.8080 = 0.808 at threshold 0.5. |
| PA | 0.9724 | CONFIRMED | "the VGG16-based FPN architecture for real-time leaf segmentation tasks as it acquires 97.24% and 96.73% accuracy with a latency time of 31.5 ms and 32.6 ms, on 0.5 and 0.75 threshold values" (lines 63–64); "FPN with VGG16 (97.24% and 96.73%)" (line 274). NOTE: 97.24% belongs to the FPN+VGG16 (latency-optimal) model at threshold 0.5, not the F1-optimal U-Net+VGG19 — mapping captured in the record's ambiguity note and treated as pixel accuracy. |
| device | CPU (desktop) | CONFIRMED | "The four models were evaluated on 1,350 test images through CPU." (line 165). Inference/evaluation on CPU (training ran on an NVIDIA RTX 3060 GPU per the paper). |
| resolution_input | 448 | CONFIRMED | "patched into 448x448 pixels" (line 123); "these images are divided into smaller image sizes of 448x448x3" (line 135); "Input layers of the model were optimized for 448x448-pixel images" (line 139). |
| fps | 31.75 | CONFIRMED | Derived: "FPN with VGG16 emerged as the most efficient, exhibiting the lowest average latency times for both thresholds, with 31.5 ms at 0.5 and 32.6 ms at 0.75" (line 229) → 1000/31.5 ≈ 31.75 FPS. FPS is not stated literally. |
| latency_ms | 31.5 | CONFIRMED | "with 31.5 ms at 0.5 and 32.6 ms at 0.75" (line 229); abstract: "a latency time of 31.5 ms and 32.6 ms, on 0.5 and 0.75 threshold values" (lines 63–64). FPN+VGG16 at threshold 0.5 = 31.5 ms. |

## SCI-001382 — HRS-UNet: A Semantic Segmentation Model for Precise Crop Classification in Hyperspectral Remote Sensing Image

attribution: CONFIRMED for model=HRS-UNet backbone=U-Net with Multiscale Spectral Aggregation (ResBlock + Spatial-Transformer + Global Attention) dataset=UAV-HSI-Crop benchmark. "The pipeline of our proposed model is based on the UNet framework, consisting of ResBlock, Spatial-Transformer and Global Attention mechanism. And we introduce the Multiscale Spectral Aggregation module" (line 210); "We have conducted our method in the UAV-HSI-Crop dataset" (line 149).

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| PA | 0.8996 | CONFIRMED | "achieving an overall classification accuracy of 89.96% and a Kappa coefficient of 0.8814" (abstract, line 29); "our method achieves a remarkable overall accuracy (OA) of 89.96% with a corresponding Kappa coefficient of 0.8814" (line 157); Table 1: "HRS-UNet(Ours) 89.96 0.8814" (line 174). Overall Accuracy mapped to global pixel accuracy (PA) per the record's ambiguity note. |
| resolution_input | 96 | CONFIRMED | "hyperspectral images of size 96×96 pixels, covering 27 distinct vegetation categories" (line 153). |
| framework | PyTorch; 8x NVIDIA RTX 3090 GPUs, 200 epochs, batch size 8, Adam lr 4e-5, weight decay 0.0005 | LOW_CONF | Training/hardware details verbatim: "All experiments are conducted with 8 × NVIDIA RTX 3090 GPUs. The training lasts for 200 epochs with the batch size of 8. The Adam optimizer is employed with an initial learning rate of 4e-5 and weight decay of 0.0005." (line 153). BUT the library "PyTorch" is never named in the extracted text (Select-String for PyTorch/torch/Python/TensorFlow/Paddle: 0 matches), rendering that component unverifiable. |

## SCI-001406 — Classification and Identification of Crops Using Deep Learning with UAV Data

attribution: CONFIRMED for model=U-Net (CIR + NDVI input) backbone=U-Net dataset=Self-collected UAV multispectral imagery (India; 5 classes: wheat, cotton, maize, grass, soil). "The objectives of this study is to apply U-Net convolutional neural networks (CNN) architecture to (i) find the best combination of input spectral bands for various crop classification such as wheat, cotton, maize, grass, and soil" (line 78); "inclusion of NDVI in CIR input dataset yield high segmentation accuracy of 83.85%" (lines 70–71).

| claim key | claimed value | verdict | verbatim source quote |
|-----------|---------------|---------|----------------------|
| mIoU | 0.8385 | CONFIRMED | "inclusion of NDVI in CIR input dataset yield high segmentation accuracy of 83.85% while dealing with..." (lines 70–71); Table 3 (CIR+NDVI column): "Image-1 94.24 ... Image-6 99.98 ... Average 83.85" (line 257). Metric value computed per image "by computing Jaccard index" (lines 236–238) and reported as "average segmentation accuracy" — IoU-like, mapped to mIoU per the record's low-confidence (<0.7) ambiguity note. |
| PA | 0.8385 | CONFIRMED | "Accuracy assessment revealed that CIR with NDVI gave most accurate results (83.85% average accuracy highlighted in bold in Table 3) for segregation of crops using U-Net" (lines 210–211); Table 3 CIR+NDVI "Average 83.85" (line 257). Averaged per-image overall accuracy on the CIR+NDVI input (best combination; RGB 83.35%, CIR 74.61%, lines 252/257). |

## Batch summary

| study_id | CONFIRMED | MISMATCH | NOT_FOUND | LOW_CONF |
|----------|-----------|----------|-----------|----------|
| SCI-001203 | 3 | 0 | 0 | 0 |
| SCI-001333 | 8 | 1 | 0 | 0 |
| SCI-001334 | 6 | 0 | 0 | 0 |
| SCI-001335 | 7 | 0 | 0 | 0 |
| SCI-001368 | 3 | 0 | 0 | 0 |
| SCI-001376 | 2 | 0 | 0 | 0 |
| SCI-001379 | 6 | 0 | 0 | 0 |
| SCI-001382 | 2 | 0 | 0 | 1 |
| SCI-001406 | 2 | 0 | 0 | 0 |
| **Overall** | **39** | **1** | **0** | **1** |