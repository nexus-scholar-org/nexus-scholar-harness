---
workspace_id: SCI-000669
doi: 10.1016/j.compag.2025.110600
title: Towards real-time weed detection and segmentation with lightweight CNN models
  on edge devices
authors:
- family_name: Islam
  given_name: Md Didarul
  orcid: https://orcid.org/0000-0003-1174-2336
- family_name: Liu
  given_name: Wenxin
  orcid: https://orcid.org/0009-0001-6226-8112
- family_name: Izere
  given_name: Pascal
  orcid: null
- family_name: Singh
  given_name: Puranjit
  orcid: null
- family_name: Yu
  given_name: Chong Ho
  orcid: https://orcid.org/0000-0003-2617-4853
- family_name: Riggan
  given_name: Benjamin S.
  orcid: https://orcid.org/0000-0003-2293-0439
- family_name: Zhang
  given_name: Kuan
  orcid: https://orcid.org/0000-0003-4195-1198
- family_name: Jhala
  given_name: Amit J.
  orcid: null
- family_name: "Kne\u017Eevi\u0107"
  given_name: Stevan Z.
  orcid: https://orcid.org/0000-0003-4898-0063
- family_name: Ge
  given_name: Yufeng
  orcid: https://orcid.org/0000-0002-6460-0780
- family_name: Pitla
  given_name: Santosh
  orcid: https://orcid.org/0000-0002-3713-4569
- family_name: Luck
  given_name: Joe D.
  orcid: https://orcid.org/0000-0002-8278-9812
- family_name: Shi
  given_name: Yeyin
  orcid: https://orcid.org/0000-0003-3964-2855
year: 2025
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:21:25.771268+00:00'
---

# Towards real-time weed detection and segmentation with lightweight CNN models on edge devices

Computers and Electronics in Agriculture 237 (2025) 110600

Contents lists available at ScienceDirect

Computers and Electronics in Agriculture

journal homepage: www.elsevier.com/locate/compag

Towards real-time weed detection and segmentation with lightweight CNN  models on edge devices

Md Didarul Islam a, Wenxin Liu a, Pascal Izere a, Puranjit Singh a, Chong Yu b, Benjamin Riggan b,   Kuan Zhang b, Amit J. Jhala c, Stevan Knezevic c, Yufeng Ge a, Santosh Pitla a, Joe Luck a,   Yeyin Shi a,*

a Department of Biological Systems Engineering, University of Nebraska-Lincoln, USA b Department of Electrical and Computer Engineering, University of Nebraska-Lincoln, USA c Department of Agronomy and Horticulture, University of Nebraska-Lincoln, USA

A R T I C L E I N F O

A B S T R A C T

Keywords: Deep learning Object detection Semantic segmentation SSD DeepLabv3+ YOLOv8n MobileNetV4 UAV companion computer

With the resurgence of on-the-go site-specific weed control technologies, research has increasingly focused on  real-time weed identification using computer vision and machine learning. While Convolutional Neural Net­ works (CNNs) have been successfully used for automatic weed detection, many studies prioritize accuracy over  inference speed and computational resource demand. The objective of this work was to develop, deploy, and  evaluate CNN-based computer vision models on computationally resource-restrained edge devices for real-time  weed classification and segmentation. RGB images were collected by UAVs over corn and soybean fields infested  with Palmer Amaranth (Amaranthus palmeri). A few object detection (OD) and semantic segmentation (SS)  models were modified, if necessary, to be lightweight, then trained and deployed on edge devices for real-time  weed detection with resized input images in dimensions of 256 × 256 pixels. Specifically, the original backbones  of Single-Shot Detector (SSD) and DeepLabv3+ models were replaced by a pre-trained MobileNetV3 backbone  and deployed on a Jetson Nano. A YOLOv8n model and a proposed MobileNetV4-Seg model were trained and  deployed on a Jetson Orin Nano. All models achieved real-time performance with acceptable accuracies with the  data collected in corn and soybean fields. Among them, the MobilenetV4-Seg achieved the best performance,  with IoUs of 69.9 % and 76.8 %, F1 scores of 82.3 % and 86.9 %, for the corn and soybean datasets, respectively,  and 44 FPS on the Jetson Orin Nano. Overall, this study demonstrated a use case and feasible workflow for  developing and deploying lightweight CNN models on resource-constrained edge devices for on-the-go real-time  site-specific applications.


## 1. Introduction

tilling, hoeing, and hand removal. Biological weed control entails  introducing natural destroyers of the target weeds, such as insects,  mites, and pathogens, aiming to reduce and maintain its population to  an acceptable level. The most commonly and widely used approach for  weed management is chemical control, such as performing uniform  broadcast herbicide spraying as it is more efficient compared to the  mechanical and biological weed controls. However, the major draw­ backs of uniform rate herbicide application include the increased  chemical footprints in the environment and the evolution of herbicide-  resistant weeds (Nath et al., 2024). Other limitations are health haz­ ards, potential damage to non-target species, and related economic loss.  Because of this, the concept of Site-Specific Weed Management (SSWM)  was brought as a weed control method that considers the spatial

Weeds are the rivals of crops that fight for the air, water, soil nu­ trients, and space. To ensure optimum crop yield, it is important to  control the weeds. Based on the research conducted by the Weed Science  Society of America on the corn and soybean fields across North America  spanning from the year 2007 to 2013, the annual average corn yield loss  could reach 52 % and the average soybean yield loss could be 49.5 %,  resulting in combined potential losses of $43 billion if weed is left un­ treated (Soltani et al., 2016, 2017). Numerous mechanical, biological,  and chemical weed control measures have been used by farmers. Me­ chanical weed control techniques include cultivation prior to seeding,  inter-row cultivation, mowing, burning and flame weeding, mulching,

* Corresponding author at: 214 L.W. Chase Hall, East Campus, University of Nebraska-Lincoln, Lincoln, NE 68583, USA. E-mail address: yshi18@unl.edu (Y. Shi).

https://doi.org/10.1016/j.compag.2025.110600 Received 14 December 2024; Received in revised form 20 May 2025; Accepted 24 May 2025

Available online 1 June 2025  0168-1699/© 2025 The Authors. Published by Elsevier B.V. This is an open access article under the CC BY license ( http://creativecommons.org/licenses/by/4.0/ ).

M.D. Islam et al.                                                                                                                                                                                                                                 Computers and Electronics in Agriculture 237 (2025) 110600

variability and temporal dynamics of weed populations in the field. It  precisely targets individual weeds or patches of weeds to help reduce  herbicide use, increase biodiversity, and reduce the chances of herbicide  crop injury.

with input images in 1472 × 1120 pixels using a workstation computing  system with a NVIDIA GeForce GTX 1080 GPU. Habib et al. (2024) developed a new deep learning segmentation model DWUNet, and  compared it to other SOTA models (SharpUNet, SegNet, DCANet,  MobileNetv2UNet, MobileNetv3UNet) using a dataset of pea crops im­ ages. DWUNet achieved a Jaccard index of 0.825 and an inference speed  of 8 ms per image on a Tesla T4 GPU. DWUNet demonstrates superior  detection accuracy and generalization capability compared to state-of-  the-art models. Bhatti et al. (2024) used a CNN-based image segmen­ tation model with a U-Net architecture to segment agricultural imagery  for crop and weed identification. The study explored the impact of  training data split ratio on model performance. Key findings emphasized  the importance of training data size, with larger datasets leading to  superior segmentation performance (77.4 % IoU and 83.5 % F1 score).  Although they did not specifically mention the configuration, they  stated that they required high-performance GPU for their study.

With the resurgence of on-the-go, site-specific weed control ma­ chinery and technologies in recent years, there has been a surge of in­ terest in research focused on the rapid and precise identification of  weeds in real-time, leveraging cutting-edge computer vision and ma­ chine learning algorithms. A backbone technology enabling automatic  SSWM is computer vision-based weed identification. Traditionally,  weed pressure maps are derived first from data collected from remote  sensing platforms such as satellites and manned or unmanned aerial and  ground vehicles (Wu et al., 2021) before targeted weeding or variable-  rate spraying. Before the widespread adoption of Convolutional Neu­ ral Networks (CNNs), various image processing and machine learning  based computer vision algorithms were employed to develop weed  detection models. In these works, different visual characteristics have  been used for weed detection under the wide range of agricultural field  conditions. Extracting features for implementing the conventional su­ pervised machine learning models for weed detection is naturally  challenging due to the similar appearances of weeds and crops. CNN-  based Deep Learning (DL) models are a preferred choice compared to  the traditional supervised machine learning models and the conven­ tional unsupervised machine learning models. This is due to the fact  that, CNNs perform joint feature and classifier learning, where the  feature extraction is learned automatically through deep learning  models rather than handled separately before applying a classifier; and  the classifier is learned simultaneously with feature extraction (Gu et al.,  2018). Object detection (OD) (Zhao et al., 2019) and semantic segmentation  (SS) (Liu et al., 2019) are two main categories of CNN-based detection  approaches for weed detection that have been largely investigated and  adopted in recent years. A typical architecture of an OD model consists  of a backbone, Region Proposal Network, and a classification head. It is  less computationally complex and hence requires relatively less re­ sources but provides faster inference speeds. A typical architecture of a  SS model is built with a backbone and an encode-decoder structure. SS  models are often computationally more intensive and, hence, require  more resources and come with a lower inference speed compared to the  OD models. The OD model outputs a bounding box around the detected  object whereas the SS model performs the classification for every pixel  presented in the image and outlays polygon segmentation masks along  the detected object’s periphery. Hence, in the application of weed  detection, OD models are often used for species classification and  counting (Norouzzadeh et al., 2017), while SS models are often used  more for precise patch contour delineation and density estimation (Asad  and Bais, 2020). A lot of the previous studies on the OD and SS model  based weed detections were deployed on resourceful desktop or laptop  computers. In one such work, Goyal et al. (2025) utilized Mask RCNN  and YOLOv8 for weed detection in complex, highly occluded potato  fields during the post-emergence stage. YOLOv8 achieved a mAP@0.5 of  83.4 %, while Mask RCNN achieved 79.0 %. Mask RCNN showed higher  precision and recall for the weed class. The testing was conducted on a  computer with a Tesla T4 GPU. Rehman et al. (2024) introduced a novel  weed detection model for soybean crops by modifying YOLOv5 archi­ tecture, incorporating Ghost Convolution, BottleNeckCSP, and Efficient  Channel Attention (ECA) layers to enhance feature extraction and weed  identification accuracy from drone imagery. They achieved a precision  of 72.5 %, recall of 68.0 %, and mAP@0.5 of 73.9 %, outperforming  existing models like RT-DETR and YOLOv10 using NVIDIA TITAN Xp  GPU. In another work, Xu et al. (2023) presented a novel approach by  combining the visible color index with the instance segmentation  method for weed detection in soybean using ResNet101_v and DSASPP  encoder and decoder architectures. Experimental results on soybean  field imagery showed that the proposed approach achieved the overall  performance of a mean IoU (mIoU) of 93.9 % and an average 1.8 FPS

With the advancement of computational hardware and computer  vision techniques in recent years, on-the-go sensing, decision-making,  and application have become true. There are a few featured products  on the market. For example, John Deere Corporation (Moline, Illinois,  USA) introduced their See & Spray series of self-propelled sprayers in  2017 utilizing computer vision and machine learning to precisely apply  herbicides only where weeds are present. The onboard computers (i.e.,  edge devices) on the sprayers perform real-time inferences with up to 12  mph of a vehicle’s moving speed. Other similar technologies and sprayer  systems that are well known on the market include but are not limited to  the One Smart Spray system by Bosch and BASF, the selective spraying  technology by Greeneye Technology, the Spot Spraying system by  Agrifac, and the ARA targeted spraying by Ecorobotix. They are all self-  propelled sprayers or add-on systems.

Other than commercial systems, researchers also successfully  implemented OD and SS models on various types of edge devices. When  there is less limitation on system payload and power consumption, the  selection of the edge devices can be focused on maximizing the real-time  inference accuracy. This is often the case with the built-in computers or  third-party computing platforms on unmanned ground-based vehicle  platforms. Li et al. (2024) reproduced SOTA models (R-CNN, YOLO,  Transformer) to validate the new winter wheat weed dataset and then  improved YOLOv8 and DINO using spatial attention mechanism (SAM),  Non-local block (NLB) and deformable convolution network v2  (DCNv2). Results showed that NLB improved YOLOv8 and DINO per­ formance, with YOLOv8_NLB achieving 88.3 % mAP, and DINO_NLB  reaching 89.4 % mAP. For real-world deployment, YOLOv8_NLB was  converted to TensorRT format for Jetson Xavier NX, with the Ten­ sorRT_FP16 model having 40.5 FPS and 86.7 % mAP. Rai et al. (2024) deployed different YOLO-Spot models on an NVIDIA Jetson AGX Xavier  with 384 × 384 pixel input images, and achieved an accuracy of 84.0 %  and a 13.8 FPS with the YOLO Spot M model for the identification of four  weed species, namely, kochia, ragweed, horseweed, and redroot  pigweed in corn and soybean. Rai & Sun (2024) developed a single-stage  deep learning, YOLO-inspired architecture WeedVision, for weed  detection and instance segmentation in drone-acquired images. They  evaluated its performance on both a desktop GPU and an edge device,  AGX Xavier. Model conversion to TorchScript and ONNX formats was  performed for edge deployment. The model achieved 85.4 % bounding-  box precision and 82.8 % masking precision on the GPU. The converted  TorchScript version also performed well and provided real-time weed  detection on the edge device.

Deployment of OD and SS-based weed detection models on relatively  resource-constrained edge devices has also been investigated. In one  such work, Farooq et al. (2022) used the YOLOv4-tiny OD model for  weed detection and a mAP@0.5 up to 85.55 %. This model was con­ verted to TensorFlowLite and deployed on a Raspberry Pi 4 (model B)  and a 4 FPS inference speed was achieved for input images of 416 × 416  pixels. They used TensorRT as a conversion method for the model to be  edge-device deployable. Harders et al. (2023) evaluated the

2

M.D. Islam et al.                                                                                                                                                                                                                                 Computers and Electronics in Agriculture 237 (2025) 110600

performances of three lightweight deep learning models, i.e., YOLOv4-  tiny, YOLOv4-tiny-3l, and YOLOv7-tiny, on three edge devices, i.e.,  NVIDIA Jetson Nano, TX2, and Xavier NX. For Jetson Nano which has  the least computational power among the three, they achieved F1 scores  of 69.97 %, 74.30 %, and 68.55 %; and inference speed of 15.1, 13.3,  and 11.8 FPS, for YOLOv4-tiny, YOLOv4-tiny-3l, and YOLOv7-tiny,  respectively, with input images of 480 × 480 pixels and an FP32  quantization. For SS, DeepLabV3 SS model was deployed on the NVIDIA  Jetson Nano by Assunç˜ao et al. (2022)) and achieved 64.0 % mIoU with  5.9 FPS for input images of 1296 × 966 pixels. Despite the popularity and wide adoption of UAVs (commonly  known as drones) among farmers for sensing and spraying in many parts  of the world, few commercial UAV systems, if there are any, and little  research work can be found on real-time onboard sensing and decision-  making for specific agricultural applications such as weed detection. The  key limiting factors here are the payload and power supply of the UAV  system, while the fast mobile velocity of the UAVs compared to some  other cases requires a very fast inference speed for real-time applica­ tions. Compact and lightweight edge devices with lower power con­ sumption are needed without sacrificing too much inference speed and  accuracy. In this study, we used the NVIDIA Jetson Nano and Jetson  Orin Nano edge devices due to their availability when we conducted this  study and their compactness and less power consumption. Jetson Nano  used to be the lowest computational performance compared to the other  NVIDIA Jetson family members. Specifically, the Jetson Nano has 472  giga floating-point operations per second (GFLOPS), Jetson TX2 has  1.33 tera floating-point operations per second (TFLOPS), Jetson Xavier  NX has 21 TFLOPS, and Jetson AGX Xavier has 32 TFLOPS. Jetson Nano  board and development kit have the lowest weights in the series and the  lowest power consumption (10 W) compared to NVIDIA Jetson Orin  Nano, TX2, Xavier NX, and AGX Xavier’s power consumptions (15 W,  15 W, 20 W, and 30 W, respectively) (NVIDIA Developer, 2024). If an  acceptable benchmark model performance can be achieved with the  currently available Jetson Nano and Orin Nano systems, superior per­ formance can be achieved with upgraded edge computing devices. In  addition, as we discussed earlier, the type of the CNN models, i.e., the  OD versus the SS models, also have different applications in weed  detection and impact on real-time applications. Hence, the overall  objective of this study was to develop and compare CNN-based OD and  SS models that can be deployed on the resource-constrained edge de­ vices (e.g., companion computer for the spraying UAV) for real-time  weed identification. The specific objectives were:


> **Table 1**

> Detailed information and parameters of data collection, raw images, and image 
pre-processing.

Crop Corn Soybean

Date July 2021 July 2022 UAV and sensing system Phantom 4 RTK with  built-in RGB camera

Matrice 300 with  Zenmuse P1 RGB camera Altitude AGL (m) 10 5 GSD (cm/pixel) 0.27 0.06 Resolution of original

5472 × 3648 8192 × 5460

images

Dataset Dataset-1 Dataset-2 Dataset-1 Dataset-2 Number of original images

15 10 31 10

used

Split ratio 8 × 8 10 × 7 4 × 3 16 × 10 Resolution of split sub-

684 × 456 547 × 521 2048 × 1820 512 × 546 Resolution of resized sub-

images

256 × 256 256 × 256 256 × 256 256 × 256

images

time of data collection in 2021; and about 1.8 to 2.2 feet tall in 2022. The  UAVs were manually flown at 10 m and 5 m above ground level (AGL) in  order to bypass the lower limits of flight altitude set by the automatic  mission planning app to achieve finer ground sampling distances. The  original images collected from the corn field had a resolution of 5472 × 3648 and a ground sampling distance (GSD) of 0.27 cm/pixel; while the  original images collected from the soybean field had a resolution of  8192 × 5460 and a GSD of 0.06 cm/pixel. The highest GSD was achieved  in 2022 with the 5 m altitude at which the impact on the canopy  structure caused by the downwash airflow was minimized. Duplicate  scenes, blurred images, and images with UAV shadow were excluded.

In this study, two datasets were prepared from the collected data:  dataset-1 and dataset-2 (Table 1). Dataset-1 consisted of a total of 15  images (5472 × 3648 pixels) and 31 images (8192 × 5460 pixels) from  UAV data collections of mid-growth-stage corn and soybeans infested  with Palmer Amaranth. Dataset-1 was a dataset with existing pre-  processing and labels that we did in a previous study. With a higher  altitude used during the data collection (10 m AGL), raw images  collected from the corn field in 2021 were split into 8 × 8 sub-images,  each with a resolution of 684 × 456; while the raw images collected  in 2022 were split into 4 × 3 sub-images, each with a resolution of 2048  × 1820 due to a lower altitude (5 m AGL) used during the data collection  (Fig. 1). These split ratios were carefully selected to ensure enough  spatial information in a sub-image for weed and crop classification.  These sub-images were further resized as input images to the classifi­ cation deep-learning models. Dataset-2 was pre-processed and labeled in  the second phase, which consisted of 10 images (5472 × 3648 pixels)  from the same corn fields and 10 images (8192 × 5460 pixels) from the  same soybean fields. Slightly different split ratios were used for dataset-  2. The original corn images were split into 10 × 7 sub-images, each with  a resolution of 547 × 521; and the original soybean images were split  into 16 × 10 sub-images, each with a resolution of 512 × 546.

(1) To modify example off-the-shelf OD and SS models into light­

weight versions for real-time weed detection or segmentation on  resource-constrained edge devices. (2) To deploy the lightweight OD and SS models on two resource-

constrained edge devices (i.e., Jetson Nano and Jetson Orin  Nano) and evaluate their detection and segmentation perfor­ mance, as well as inference speed.


## 2. Materials and methods

Different resize ratios or resolutions of input images were tested. We  found that, at a resolution of 256 × 256 for input images, models ach­ ieved the optimal combination of classification accuracy and inference  speed. After removing some of the sub-images without any weeds in the  scene, we resulted with 480 resized sub-images from corn fields and 360  resized sub-images from soybean fields for OD models (i.e., SSD and  YOLOv8n); 120 resized sub-images from both crop fields for the Deep­ Labv3 + SS model; and 443 sub-images from corn fields and 353 sub-  images from soybean fields for the proposed segmentation model  MobileNetV4-Seg (Table 2). The resized images were labeled pixel-wise  for SS modeling and with bounding boxes for OD modeling, respectively,  using Computer Vision Annotation Tool (CVAT), which is an open-  source data annotation platform. The training, validation, and test  data split for all models are shown in Table 2.

2.1. Data collection and preparation

In this study, we targeted a major weed in row crop production in  North America − the Palmer Amaranth (Amaranthus palmeri). RGB im­ ages of Palmer Amaranth were collected in a commercial corn field in  Carleton, Nebraska, USA, on July 1st, 2021, using a sensing UAV  (Phantom 4 RTK, DJI, Shenzhen, China) and a built-in camera. Simi­ larly, RGB images were collected in a soybean field in South Central  Agricultural Lab (SCAL), Clay Center, Nebraska, USA, on July 18th,  2022, using another sensing UAV, which was the latest model then  (Matrice 300 RTK, DJI, Shenzhen, China), and a compatible plug-and-  play high-resolution camera (Zenmuse P1, DJI, Shenzhen, China)  (Table 1). Palmer amaranth plants were about 1.2 to 1.5 feet tall at the

3

M.D. Islam et al.                                                                                                                                                                                                                                 Computers and Electronics in Agriculture 237 (2025) 110600

Fig. 1. Steps followed in implementing the weed detection models. OD in the figure stands for object detection, and SS stands for semantic segmentation.

models deployed on the edge device were compared between them­ selves in terms of detection or segmentation performance and inference  speed. The methodology to work with the CNN based weed detection  models is explained in a step-by-step manner in Fig. 1. We also evaluated  additional two relatively newer lightweight models, the off-the-shelf  YOLOv8n (Ultralytics, 2023) for OD and a proposed MobileNetV4-Seg  for SS based on MobileNetV4 (Qin et al., 2024).


> **Table 2**

> Total number of images and training, validation, and testing splitting for the 
object detection (OD) and semantic segmentation (SS) models.

Crop Model Total  number of  resized  sub-  images  used

Number  of  training  sub-  images

Number of  validation  sub-images

Number  of testing  sub-  images

2.3. Model selection on laptop and desktop computers

Corn Object Detection (OD) SSD and  YOLOv8n

480 400 40 40

The original SSD model came with a VGG-16 backbone (Tao et al.,  2021) and the original DeepLabv3+ model came with a ResNet back­ bone (He et al., 2016). Since these original backbones contain a large  number of parameters, they would not provide satisfied real-time  inference if deployed directly on the Jetson Nano. Hence, the SSD’s  VGG-16 and the DeepLabv3+’s ResNet backbones were both replaced by  the MobileNetV3 backbone (Howard et al., 2019) to efficiently run on a  Jetson Nano for real-time inference, since the MobileNetV3 has a rela­ tively small number of parameters. The architecture of the MobileNetV3  is shown in Fig. 2 (a). After replacing the original backbones, the  modified SSD architecture with the MobileNetV3 backbone is shown in  Fig. 2 (b) and the modified DeepLabv3+ architecture with the Mobile­ NetV3 backbone is shown in Fig. 2 (c). Similarly, the proposed seg­ mentation model, MobileNetV4-Seg comprises an encoder-decoder  architecture for efficient semantic segmentation. The encoder module  utilizes the feature extractor functionality of the pretrained  MobileNetV4-Conv-Small (Qin et al., 2024) in the backbone to extract  multi-scale features while maintaining computational efficiency. To  enhance feature fusion and maintain spatial consistency, the extracted  feature maps are up-sampled to the same resolution as the 1/8 feature  map. A residual connection (skip connection) is then introduced to add  the 1/8 feature map to the 1/32 feature map, avoiding gradient degra­ dation and improving information propagation. In the decoder module,  a dedicated semantic segmentation head (Lu et al., 2024) is employed to  decode the extracted features into segmentation information. Finally,  another semantic segmentation head processes the refined features, and  the resulting segmentation map is up-sampled to match the original  image size. MobileNetV4-Seg’s architecture is depicted in Fig. 2(d).

Semantic Segmentation (SS) DeepLabv3+ 120 100 10 10 MobileNetV4-  Seg

443 390 10 43

Soybean Object Detection (OD) SSD and  YOLOv8n

360 300 30 30

Semantic Segmentation (SS) DeepLabv3+ 120 100 10 10 MobileNetV4-  Seg

353 310 10 33

2.2. Overview of model selection and deployment process

For OD models, we considered two widely used ones, Single-Shot  Detector (SSD) (W. Liu et al., 2016) and You Only Look Once  (YOLOv3) (Redmon & Farhadi, 2018). We compared these two OD  models on a laptop computer in terms of the IoU, F1 score, and FPS, and  found that the SSD model was better suited for our application (Table 4).  For SS models we considered DeepLabv3+ (Yurtkulu et al., 2019)) and  U-Net (Ronneberger et al., 2015), as they are two of the most commonly  used models for semantic segmentation. We compared these two SS  models on a laptop computer in terms of IoU, F1 score, and FPS, and  found that the DeepLabv3+ model performed better (Table 4). Both the  selected OD (SSD) and SS (DeepLabv3+) models’ original backbones  were replaced by a lightweight backbone, MobileNetV3. These modified  models were retrained with lower resolution (256 × 256) images and  deployed on the edge device’s GPU. Finally, the modified OD and SS

Before being deployed on the edge devices, the initial model train­ ings of the modified lightweight SSD, YOLOv3, U-Net, and DeepLabv3+

4

M.D. Islam et al.                                                                                                                                                                                                                                 Computers and Electronics in Agriculture 237 (2025) 110600

Fig. 2. Model architectures: (a) MobileNetV3 architecture adapted from Howard et al. (2019) and Nguyen et al. (2022). Conv2D is a convolutional layer, BtNk stands  for bottleneck. SE denotes whether there is a Squeeze-And-Excite in that block. The × in the parentheses indicates how many times the block has been repeated. Pool  represents the maxpooling layer. (b) Modified SSD architecture with MobileNetV3 backbone. Concept taken from Meng et al. (2022). (c) Modified DeepLabv3+ architecture with MobileNetV3 backbone adapted from Parajuli et al. (2023). (d) MobileNetV4-Seg architecture. The encoder module uses the down-sampling  structure of MobileNetv4-Conv-Small (Qin et al., 2024) which down-samples the input image through five stages, generating feature maps at1/2, 1/4, 1/8, 1/16,  and 1/32 dimensions. The decoder part uses a segmentation head (Lu et al., 2024) as shown at the bottom.

models were trained and evaluated on a laptop computer to utilize its  better computational resource to speed up the process. The configura­ tions of the laptop computer were CPU: 11th Gen Intel Core Processor i9-  11950H @ 2.60 GHz; SSD: 1 TB, Core: 8, Cache: 24 MB, RAM: 32 GB;  GPU: NVIDIA RTX A2000 Laptop GPU. PyTorch was used (torch version:  2.0.1, torchvision version: 0.15.2, and CUDA version: 12.5). Models  with the minimum validation loss were selected. Similarly, in the second  phase of the work, the YOLOv8n and MobileNetV4-Seg models were  trained on a desktop computer (Processor: Intel(R) Core(TM) i7-10700F  CPU @ 2.90 GHz, RAM: 32 GB, GPU: NVIDIA GeForce RTX 4090 24  GB GPU memory). The hyperparameters used during all the model  training are provided in Table 3. The optimal parameters were selected  based on the highest F1 score of the validation dataset.


> **Table 3**

> Hyperparameters used during model training.

Model Learning  rate

Optimizer Batch  size

Number of  epochs

SSD(original and

0.001 SGD 32 300

modified)

YOLOv3 0.001 Adam 2 300 DeepLabv3+(original

0.0001 Adam 4 300

and modified)

U-Net 0.0001 Adam 4 300 YOLOv8n 0.0001 Adam 20 300 MobileNetV4-Seg 0.0001 Adam 20 300

NVIDIA CUDA cores, CPU: Quad-core ARM Cortex-A57 MPCore pro­ cessor, RAM: 4 GB 64-bit LPDDR4, 1600 MHz 25.6 GB/s, storage: 16 GB  eMMC 5.1, computing performance: 472 GFLOPS, weight: 250 g)

2.4. Model deployment on edge devices

NVIDIA Jetson Nano (GPU: NVIDIA Maxwell architecture with 128

5

M.D. Islam et al.                                                                                                                                                                                                                                 Computers and Electronics in Agriculture 237 (2025) 110600

(NVIDIA, 2024) and Jetson Orin Nano (1024-core NVIDIA Ampere ar­ chitecture GPU with 32 Tensor Cores; 6-core Arm Cort4ex-A78AE v8.2  64-bit CPU; 8 GB 128-bit LPDDR5) were the two resource-constrained  edge devices explored in this study. CNN models were deployed on  Jetson Nano’s GPU utilizing PyTorch with torch version: 2.4.1, torch­ vision version: 0.19.1, and CUDA version: 11.4; and Jetson Orin Nano’s  GPU utilizing PyTorch but with torch version: 1.10.0, torchvision  version: 0.11.3, and CUDA version: 10.2. SSD and DeepLabv3+ models  were deployed on Jetson Nano, and YOLOv8n and MobileNetV4-Seg  models were deployed on Jetson Orin Nano. Due to differences in the  operating system architectures between the PC and the Jetson platform,  the versions of software packages supported on the PC may not always  be compatible with the Jetson system. In order to deploy the model  originally developed with the laptop or desktop onto the Jetson devices,  we often needed to install additional necessary supporting packages for  the Jetson system.


> **Table 4**

> Comparison of detection and segmentation performance, as well as inference 
speed, between OD models (SSD and YOLOv3), and between SS models (Deep­
Labv3+ and U-Net) for both corn and soybean datasets on PC.

Crop Model IoU (%) F1 score (%) Inference speed (FPS)

(OD) Corn SSD 64.3 75.8 72 YOLOv3 47.7 55.2 90 Soybean SSD 48.3 68.9 72 YOLOv3 46.4 40.0 90

(SS) Corn DeepLabv3+ 61.0 77.3 50 U-Net 53.0 72 40 Soybean DeepLabv3+ 65.5 82.7 50 U-Net 62.0 81.4 40

Fig. 3. Number of epochs versus validation loss for: (a) the SSD model for the corn dataset, (b) DeepLabv3+ model for the corn dataset, (c) the SSD model for the  soybean dataset, (d) DeepLabv3+ model for the soybean dataset. The point with the lowest validation loss is marked in red. For (a, c) only 50 out of 300 epochs, and  for (b, d) only 200 out of 300 epochs are shown for better visualization. (For interpretation of the references to color in this figure legend, the reader is referred to the  web version of this article.)

6

M.D. Islam et al.                                                                                                                                                                                                                                 Computers and Electronics in Agriculture 237 (2025) 110600

2.5. System performance evaluation


> **Table 5**

> Detection or segmentation performances and inference speeds of the OD and the 
SS models on edge devices (SSD and DeepLabv3+ on Jetson Nano, YOLOv8n and 
MobileNetV4-Seg on Jetson Orin Nano).

In this study, we used metrics including IoU (with a threshold of 0.5),  precision, recall, and F1 score (Eqs. (1)-(4)) to evaluate the model per­ formance on weed detection or segmentation. IoU is the ratio between  the overlap (or intersection) and the union, of the ground truth  bounding box (BBGT) and the prediction bounding box (BBpred). For OD,  if the IoU for a particular object was equal to or greater than 0.5, then it  was considered as a true positive, else false positive. Other parameters  such as True Positive (TP), True Negative (TN), False Positive (FP), False  Negative (FN) are explained below.

Model IoU  (%)

Precision  (%)

Recall  (%)

F1 score  (%)

Inference  speed (FPS)

(Corn) Lightweight SSD

58.8 62.5 95.2 75.5 33

(OD)

YOLOv8n (OD) 58.6 87.0 81.6 84.2 30 Lightweight

60.0 82.0 72.6 77.0 10

DeepLabv3+ (SS)

IoU = Area(BBpred∩BBGT)

MobileNetV4-Seg

69.9 80.9 83.7 82.3 44

Area(BBpred∪BBGT) (1)

(SS)

(Soybean) Lightweight SSD

Precision(Pr) = TP TP + FP (2)

42.3 63.6 77.8 70.0 33

(OD)

YOLOv8n (OD) 56.1 77.1 72.7 74.9 30 Lightweight

62.4 81.5 82.0 81.7 10

Recall(Rc) = TP TP + FN (3)

DeepLabv3+ (SS)

MobileNetV4-Seg

76.8 83.8 90.2 86.9 44

F1 score = 2 × Pr × Rc

(SS)

Pr + Rc (4)

33 FPS for 256 × 256 pixel images when deployed on Jetson Nano.  Performance metrics for the SSD model included an IoU of 58.8 %,  precision of 62.5 %, recall of 95.2 %, and an F1 score of 75.5 % for corn.  For soybean, it attained 42.3 % IoU, 63.6 % precision, 77.8 % recall, and  a 70 % F1 score. As for the lightweight DeepLabv3+ model operated at a  near real-time inference speed of 10 FPS for 256 × 256 pixel images on  Jetson Nano. It achieved an IoU of 60.0 %, precision of 82.0 %, recall of  72.6 %, and an F1 score of 77.0 % for corn. For soybean, it recorded 62.4  % IoU, 81.5 % precision, 82.0 % recall, and an 81.7 % F1 score. With  Jetson Orin Nano, YOLOv8n and the MobileNetV4-Seg both achieved  real-time inference speeds of 30 FPS and 44 FPS, respectively, for 256 × 256 pixel images. The YOLOv8n model recorded an IoU of 58.6 %,  precision of 87.0 %, recall of 81.6 %, and an F1 score of 84.2 % for corn,  while for soybean, it achieved 56.1 % IoU, 77.1 % precision, 72.7 %  recall, and an F1 score of 74.9 %. The MobileNetV4-Seg model achieved  an IoU of 69.9 %, precision of 80.9 %, recall of 83.7 %, and an F1 score of  82.3 % for corn. For soybean, it achieved 76.8 % IoU, 83.8 % precision,  90.2 % recall, and an F1 score of 86.9 %.


## 3. Results

3.1. Selected OD and SS models with original backbones on PC

Fig. 3 shows the number of epochs versus validation loss plots for  SSD and DeepLabv3+ models deployed on the laptop computer. Models  with the lowest validation loss were selected for the next step (i.e. per­ formance comparison). YOLOv3 and U-Net’s plots are not shown here as  they were outperformed by the other two models (refer to Table 4).  Table 4 shows the detection performance (IoU and F1 score) and infer­ ence speed comparison of the two OD models on the laptop computer.  From Table 4 we can see that, although YOLOv3 has a better inference  speed compared to SSD, SSD has a better IoU and F1 score with a  reasonable inference speed. For that reason, SSD was selected as the  better OD model. The segmentation performance and inference speed  comparison of the two SS models on the laptop computer are also shown  in Table 4. As shown in Table 4, DeepLabv3+ achieved better IoU, F1  score, and inference speed compared to U-Net in this case.

Between SSD and YOLOv3, we selected SSD for further deployment  on the edge device, since SSD achieved a higher IoU and F1 score with  reasonable inference speed on our datasets, despite YOLOv3 offering  faster inference speed. Similarly, DeepLabv3+ was selected over the U-  Net in terms of IoU, F1 score, and inference speed. DeepLabv3+ uses an  advanced technique called atrous (dilated) convolutions, which helps it  capture information at multiple scales. This improves the segmentation  performance of DeepLabv3+ on objects of different sizes, and hence it  was selected as the preferred weed detection SS model. Then we  modified the SSD and DeepLabv3+ models, deployed them on the Jetson  Nano, and tested their performance for weed in the corn and soybean  dataset.

3.2.1. Performance comparison on data collected in corn Images were randomly selected to show the performance of each  model on the data collected in corn and soybean (Figs. 4–9). Perfor­ mance of the three OD models in the corn datasets is shown in Fig. 4. The  lightweight SSD had lower Precision but higher Recall than the  YOLOv8n (Table 5). In Fig. 4(d), a false positive can be observed. Some  of the weeds were missed in being labeled as it was not clearly visible to  human eyes, but the model detected them. On the right side of the  image, instead of detecting the whole patch of weed, the model detected  two separate weeds. The reason is there are human errors and differ­ ences in how the images are labeled. Spread out weeds can be labeled  using bounding boxes in several ways, and thus detection may not  exactly match with the ground truth. In Fig. 4(e), there is a false positive  similar to Fig. 4(d). On the bottom right of the image, the model detected  weeds well. However, the model did not detect the weed above it, as it  was covered by the corn. Fig. 4(f), (g), and (h) gave almost similar re­ sults to SSD. For Fig. 4(i) and (j), YOLOv8n detected only the sharp weed  images and missed the subtle presence of weeds, which SSD detected.  This way YOLOv8n had better results than SSD as these subtle weed  images were not labeled in ground truth and hence considered as false  positives for SSD.

3.2. Performance comparison of lightweight OD and SS models on edge  devices

The selected OD and SS models with better performance on the  laptop computer from the previous subsection, i.e., the SSD and the  DeepLabv3+ models, were modified and deployed on the Jetson Nano  and tested with unseen resized sub-images in 256 × 256 pixel resolution.  Similarly, the YOLOv8n (OD model) and the proposed MobileNetV4-Seg  (SS model) were deployed on the Jetson Orin Nano. The performance  metrics (IoU, Precision, Recall, and F1 score) and inference speeds are  shown in Table 5.

Figs. 5 and 6 show the segmentations using DeepLabv3+ and  MobileNetV4-Seg SS models for five randomly selected images collected  from the corn fields. Fig. 5(k) does not exactly match with the ground

The lightweight SSD model achieved a real-time inference speed of

7

M.D. Islam et al.                                                                                                                                                                                                                                 Computers and Electronics in Agriculture 237 (2025) 110600

Fig. 4. Five example cases of Palmer Amaranth weed detection in corn using the lightweight SSD (a-e) and YOLOv8n (f-j) OD model. Red boxes represent the  detection of weeds by the model, and blue boxes represent the ground truth. (For interpretation of the references to color in this figure legend, the reader is referred  to the web version of this article.)

Fig. 5. Five example cases of Palmer Amaranth weed detection in corn using the lightweight DeepLabv3 + SS model. (a-e) are the resized RGB sub-images, (f-j) are  the ground truth masks, and (k-o) show the detections using the SS model. For the ground truth mask and detection, white indicates the weeds, while black represents  the background.

truth, Fig. 5(f). This is due to the fact that at one place there are weeds  underneath the corn. During the labeling, the corn part is excluded from  the weeds, but the model detected the whole weed segment. For Fig. 5 (b) and Fig. 5(c) the model performs really well for detecting if there is  any weed present or not. Fig. 5(d) has the similar issue of corn covering  the weed as Fig. 5(a), hence the detection, Fig. 5(n) and the ground  truth, Fig. 5(i) do not exactly match. Except for some false detections,  the detection, Fig. 5(o) is close enough to the ground truth, Fig. 5(j) for  Fig. 5(e). In Fig. 6(a), MobileNetV4-Seg detected weeds in the same  region as the ground truth. Whereas DeepLabv3+ also detected an  additional surrounding area of the ground truth as weed. For Fig. 6(b),  MobileNetV4-Seg detected the soil in the middle right of the image as

background, which was detected as weed by DeepLabv3+. In Fig. 6(c),  no weed was present, hence not detected. For Fig. 6(d) and (e), Mobi­ leNetV4-Seg’s detections are closer to the ground truth compared to  DeepLabv3+’s detections.

3.2.2. Performance comparison on data collected in soybean Similarly, images were randomly selected for the data collected from  the soybean fields. Fig. 7 shows the results of five images with the SSD  and YOLOv8n OD models. In Fig. 7(a) and Fig. 7(b), the whole image  scenes were covered by weeds. Although the whole patch of weeds was  detected, both images had additional sub-detections. In Fig. 7(c), the  model performs well as it detected a few weeds that were missed in the

8

M.D. Islam et al.                                                                                                                                                                                                                                 Computers and Electronics in Agriculture 237 (2025) 110600

Fig. 6. Five example cases of Palmer Amaranth weed detection in corn using the MobileNetV4-Seg SS model. (a-e) are the resized RGB sub-images, (f-j) are the  ground truth masks, and (k-o) show the detections using the SS model. For the ground truth mask and detection, white indicates the weeds, while black represents  the background.

Fig. 7. Five example cases of Palmer Amaranth weed detection in soybean using the lightweight SSD (a-e) and YOLOv8n (f-j) OD models. Red boxes represent the  detection of weeds by the model, and blue boxes represent the ground truth. (For interpretation of the references to color in this figure legend, the reader is referred  to the web version of this article.)

original labeling; however, the model missed the detection at the top  right corner. In Fig. 7(d), the weeds shown in the scene were not Palmer  Amaranth and hence were not detected by either model. The models  performed well for the cases in Fig. 7(e) and 7(j). For scenes shown in  Fig. 7(g), (i), and (j), YOLOv8n’s detections agreed with SSD. For Fig. 7 (h), YOLOv8n captured almost all weed patches including the top right  and bottom weed patches; however, it did not detect the upper left patch  that was missing in the labeling compared to SSD.

actually there are some bare soil in some small places. These very small  weed free locations were also detected by the model, so in that case, the  model performed better than the human. In Fig. 8(c), at the center of the  image, the model detects a few soybeans as weeds (false positives). For  Fig. 8(d), there is no weed labeled in Fig. 8(i) and the model does a great  job for the prediction in Fig. 8(n). Fig. 8(e) also has some false positives  in the detection as shown in Fig. 8(o) similar to Fig. 8(c), because it is  difficult to tell if these false positives are actually weed or soybean from  the low resolution images even though they are not labeled as weeds in  the ground truth in Fig. 8(j). For Fig. 9(a), (c), and (e), the detections are  almost identical to the ground truths. For Fig. 9(b) and (d), it can be said  that MobileNetV4-Seg performed better than the ground truth,

Examples of DeepLabv3+ and MobileNetV4-Seg SS models’ de­ tections are shown in Figs. 8 and 9, respectively. For Fig. 8(a), the  detection, Fig. 8(k) and the ground truth, Fig. 8(f) are almost identical.  For Fig. 8(b), the whole image was labeled as covered by weeds, but

9

M.D. Islam et al.                                                                                                                                                                                                                                 Computers and Electronics in Agriculture 237 (2025) 110600

Fig. 8. Five example cases of Palmer Amaranth weed detection in soybean using the lightweight DeepLabv3+ semantic segmentation model. (a-e) show the actual  images, (f-j) show the ground truth masks, and (k-o) show the detections using the SS model. For the ground truth mask and detection, white indicates the weeds,  while black represents the background.

Fig. 9. Five example cases of Palmer Amaranth weed detection in soybean using the MobileNetV4-Seg semantic segmentation model. (a-e) show the actual images,  (f-j) show the ground truth masks, and (k-o) show the detections using the SS model. For the ground truth mask and detection, white indicates the weeds, while black  represents the background.

considering the human error in the labeling. In Fig. 9(b), there is some  background in the middle of the image, which was not labeled in the  ground truth, but was detected by the model. Similarly, Fig. 9(d) was  labeled as all background. However, the small weeds were detected by  the model. By observing the Figs. 4-9, it can be suggested that using  large dataset (for training, validation, and testing) and being consistent  in labeling throughout the dataset are helpful to improve the perfor­ mance of the models.


## 4. Discussion

While extensive work has been carried out using machine or deep  learning models for automatic weed detection, many of these efforts  have focused on improving detection accuracy through the development  of advanced model structures. However, adapting these models for  deployment on edge devices, which have limited computational power  but require ultra-fast inference speeds, particularly for real-time aerial

10

M.D. Islam et al.                                                                                                                                                                                                                                 Computers and Electronics in Agriculture 237 (2025) 110600

applications such as those based on spray UAVs or spray drones, remains  a significant challenge. In this research, we demonstrated the process  and performance of developing and deploying lightweight computer  vision models on two of the most widely used resource-constrained edge  computing devices.

achieved comparable real-time performance (Table 5) with the partic­ ular input image size we used (256 × 256 pixels), which exceeded our  initial expectation, as we typically consider object detection to be su­ perior for real-time applications. The OD models achieved up to 33 FPS  on the Jetson Nano, while the SS models achieved up to 44 FPS of  inference time on a slightly more powerful Jetson Orin Nano, all with  comparable accuracies. Although YOLOv8n (OD model) performed  better than MobileNetV4-Seg (SS model) in some cases for the corn  dataset, MobileNetV4-Seg consistently outperformed YOLOv8n for the  soybean dataset. This may be partially due to the higher image resolu­ tion of the soybean datasets, but the efficient model structure of both  models also plays a significant role, especially given the challenge of  distinguishing between Palmar Amaranth and soybeans, which appear  similar to each other.

4.1. Model deployment on edge devices

We deployed modified lightweight weed detection models on two  resource-constrained edge devices, both of which are equipped with  GPUs for efficient parallel processing of computational tasks. Their CPUs  support multi-threaded processing, which is essential for handling the  multiple tasks required during model deployment. Use the Jetson Nano  we used as an example, it has a computing performance of 472 GFLOPS  and a lightweight design at just 250 g, which makes it well-suited for  edge deployments where both performance and portability are critical,  such as UAV-based applications. Similarly, the Jetson Orin Nano is the  latest model and computationally more resourceful with 1280 GFLOPS  for FP32 precision. Ensuring the models are lightweight so that the RAM  on the edge device can provide sufficient memory resources for running  the model is crucial.

The proposed MobileNetV4-Seg also showed faster inference speed  compared to YOLOv8n, as our developed model has only 1.93 million  parameters, whereas YOLOv8n has 3.2 million parameters (Ultralytics,  2023). The MobileNetV4-Conv-Small encoder of the MobileNetV4-Seg  efficiently captures multi-scale features with low computational over­ head, and the semantic segmentation head in the decoder combined  with residual connections enhances spatial consistency and gradient  flow, leading to better localization of object boundaries. Despite the  different spatial variation and scale differences introduced by these new  samples, the model maintained high accuracy for weed segmentation.  This indicates the model’s robustness and generalization capability to  dataset variations, making it suitable for diverse real-world applications.

We used PyTorch for model deployment on edge devices, utilizing  specific versions of software packages to ensure compatibility with  Jetson’s architecture. It is important to note that the architectural dif­ ferences between the Jetson devices and a laptop or desktop PC can lead  to compatibility issues. Specifically, certain software packages that are  supported and function properly on a laptop or desktop PC may not be  directly supported by the Jetson devices due to their unique architec­ ture. In many instances, additional support packages or modifications to  the existing code are required to ensure the reliable and efficient  deployment of the models, allowing them to run smoothly on Jetson  devices.

4.3. Limitations and future work

This study has several limitations that should be acknowledged in  order to clarify the scope and applicability of the results. First, the size  and complexity of the dataset used in model training and evaluation  were limited. Specifically, the datasets used for OD models (SSD and  YOLOv8n) were 480 and 360 sub-images for corn and soybean,  respectively, while the dataset for DeepLabv3+ SS model was 120 sub-  images for both corn and soybean, and datasets for MobileNetV4-Seg  were 443 sub-images for corn and 353 sub-images for soybean.  Although these datasets were sufficient for preliminary validation, such  sample sizes may not capture the full range of variability in field con­ ditions. Factors such as weed shape variation, lighting changes, occlu­ sion, soil background diversity, and plant density can greatly affect  model robustness. Expanding the dataset by including images from  different locations, times, and incorporating augmented and synthetic  data could significantly improve generalizability.

All inference speeds mentioned in this work refer solely to the time  required to process an image through the model. The time required to  load the image from the device’s storage was not included, though in our  case it was trivial. Additionally, there is a “model loading time” asso­ ciated with the inference, which refers to the time required to load the  model onto the GPU. This causes the inference of the first couple of  images to take relatively longer times, but reduces once the model is  loaded. Another factor is the time required to acquire images from the  camera in the on-the-go application. All these factors could vary and  impact the overall system speed, and need to be considered in  applications.

4.2. Lightweight OD and SS models for real-time applications

Second, the Jetson Nano was initially selected due to its low power  consumption, GPU acceleration, and its potential for lightweight UAV  integration. However, its low processing power and memory limited the  model complexity that could be deployed on it in real time. For instance,  DeepLabv3+ achieved only 10 FPS for 256 × 256 image inference,  which may be insufficient for fast-moving UAV-based applications.  Although the resourceful device, Jetson Orin Nano allowed deployment  of newer models like YOLOv8n and MobileNetV4-Seg, the study did not  explore deployment on other edge platforms or mini PCs having  powerful CPUs without GPUs, such as the Intel NUC or Google’s Coral  Dev Board, which may be capable of supporting quantized or pruned  versions of tiny deep learning models. Evaluation on these alternatives  could provide insights into cost-effective, GPU-free deployments suit­ able for constrained field settings.

In this study, some of the models we evaluated are lightweight as  they are, i.e., the YOLOv8n object detection model and the  MobileNetV4-Seg semantic segmentation model; some of the models, i.  e., the SSD and YOLOv3 object detection models and the U-Net and  DeepLabv3+ semantic segmentation models, were initially too heavy to  be run on a resource-constrained edge device and needed to be simpli­ fied and optimized before deployment. For models in the latter case, we  did not go the route of using a model optimizer such as TensorRT, but  replaced the original heavy backbones of the model with a pre-trained  lightweight MobileNetV3 backbone. Results showed acceptable accu­ racy with real-time performance.

When comparing the OD models used in this study by themselves, i.  e., the modified lightweight SSD and the YOLOv8n, the YOLOv8n did  not outperform the SSD model in every case, and it also had a lower FPS  compared to the modified SSD. When comparing the SS models, i.e., the  modified lightweight DeepLabv3+ and the proposed MobileNetV4-Seg,  it can be observed that the proposed MobileNetV4-Seg exhibits superior  performance to the DeepLabv3+ in most cases and also achieves a  significantly improved FPS.

Third, the study focuses on detecting Palmer Amaranth weeds only in  corn and soybean fields during specific crop growth stages. It limits the  system’s applicability to broader scenarios as other common weed  species (e.g., waterhemp, kochia, morning glory) and complex field  conditions such as overlapping weed and crop canopies, mixed-species  weed patches, or partial occlusion were not included. Furthermore,  data collection was done under relatively stable lighting and soil back­ ground conditions. The lack of variation in crop stages (e.g., early

In this study, both object detection and semantic segmentation

11

M.D. Islam et al.                                                                                                                                                                                                                                 Computers and Electronics in Agriculture 237 (2025) 110600

vegetative vs late reproductive) also limits the model’s generalization.  These gaps could affect detection accuracy in real-world deployments  and warrant further exploration.

Declaration of competing interest

The authors declare that they have no known competing financial  interests or personal relationships that could have appeared to influence  the work reported in this paper.

Finally, while this work contributes to a larger UAV-based precision  spraying project, the current study is limited to model training, evalu­ ation, and deployment on edge devices. It does not include the inte­ gration of the vision system with UAV flight controllers and its  performance evaluation under real aerial operating conditions. Impor­ tant environmental factors such as UAV vibration, motion blur, and  wind effect can influence both image quality and real-time detection  performance. Incorporating these elements in future studies will be  crucial to validate the robustness of the system in dynamic field condi­ tions. In future work, we aim to conduct full integration of the vision  system with the flight system and perform the flight-based validation of  the autonomous system.

Acknowledgments

This research was supported by the grant titled An Intelligent Un­ manned Aerial Application System for Site-Specific Weed Management  under AFRI Foundational and Applied Science Program of the United  States Department of Agriculture (USDA award No. 2021-67021-  34412).

Data availability


## 5. Conclusion

Data will be made available on request.

In this study, we successfully developed and deployed four light­ weight CNN OD and SS models on resource-constrained edge devices, i.  e., Jetson Nano and Jetson Orin Nano, for real-time detection and seg­ mentation of Palmar Amaranth in mid-growth stage corn and soybeans.  With input image size of 256 × 256 pixels, the modified lightweight SSD  OD model achieved real-time (33 FPS) inference speed on Jetson Nano,  with 58.8 % IoU, 62.50 % precision, 95.2 % recall, and 75.5 % F1 score  for corn, and 42.3 % IoU, 63.60 % precision, 77.8 % recall, and 70.0 %  F1 score for soybean. The modified lightweight DeepLabv3+ SS model  achieved near-real-time (10 FPS) inference speed on Jetson Nano, with  60.0 % IoU, 82.0 % precision, 72.6 % recall, and 77.0 % F1 score for  corn, and 62.4 % IoU, 81.5 % precision, 82.0 % recall, and 81.7 % F1  score for soybean. The un-modified YOLOv8n OD model achieved real-  time (30 FPS) inference speed on Jetson Orin Nano, with 58.6 % IoU,  86.96 % precision, 81.6 % recall, and 84.2 % F1 score for corn; 56.1 %  IoU, 77.1 % precision, 72.8 % recall, and 74.9 % F1 score for soybean.  The proposed MobileNetV4-Seg SS model achieved real-time (44 FPS)  inference speed on Jetson Orin Nano, with 69.9 % IoU, 80.9 % precision,  83.7 % recall, and 82.3 % F1 score for corn, and 76.8 % IoU, 83.8 %  precision, 90.2 % recall, and 86.9 % F1 score for soybean. All de­ ployments resulted in acceptable detection and segmentation accuracies  and inference speed, except for the modified DeepLabv3+ was a little  slow for our case. The semantic segmentation models, such as the  MobileNetV4-Seg model, had comparable if not superior performance  compared to state-of-the-art object detection models. The models with  top performance can be further improved and integrated into the on-the-  go systems.


## References

Assunç˜ao, E., Gaspar, P.D., Mesquita, R., Sim˜oes, M.P., Alibabaei, K., Veiros, A.,

Proença, H., 2022. Real-time weed control application using a jetson nano edge  device and a spray mechanism. Remote Sens. (Basel) 14 (17), 4217. https://doi.org/  10.3390/rs14174217. Bhatti, M.A., Syam, M.S., Chen, H., Hu, Y., Keung, L.W., Zeeshan, Z., Ali, Y.A.,

Sarhan, N., 2024. Utilizing convolutional neural networks (CNN) and U-Net  architecture for precise crop and weed segmentation in agricultural imagery: a deep  learning approach. Big Data Res. 36. https://doi.org/10.1016/j.bdr.2024.100465. Farooq, U., Rehman, A., Khanam, T., Amtullah, A., Bou-Rabee, M.A., Tariq, M., 2022.

Lightweight deep learning model for weed detection for IoT devices. In: 2022 2nd  International Conference on Emerging Frontiers in Electrical and Electronic Technologies  (ICEFEET), pp. 1–5. https://doi.org/10.1109/ICEFEET51821.2022.9847812. Goyal, R., Nath, A., Niranjan, U., 2025. Weed detection using deep learning in complex

and highly occluded potato field environment. Crop Prot. 187. https://doi.org/  10.1016/j.cropro.2024.106948. Gu, J., Wang, Z., Kuen, J., Ma, L., Shahroudy, A., Shuai, B., Liu, T., Wang, X., Wang, G.,

Cai, J., Chen, T., 2018. Recent advances in convolutional neural networks. Pattern  Recogn. 77, 354–377. https://doi.org/10.1016/j.patcog.2017.10.013. Habib, M., Sekhra, S., Tannouche, A., Ounejjar, Y., 2024. New segmentation approach

for effective weed management in agriculture. Smart Agric. Technol. 8. https://doi.  org/10.1016/j.atech.2024.100505. Harders, L.O., Ufer, T., Wrede, A., Hussmann, S., 2023. UAV-based real-time weed

detection in horticulture using edge processing. J. Electron. Imaging 32 (5), 52405.  https://doi.org/10.1117/1.JEI.32.5.052405. He, K., Zhang, X., Ren, S., Sun, J., 2016. Deep residual learning for image recognition. In:

Proceedings of the IEEE Computer Society Conference on Computer Vision and Pattern  Recognition. https://doi.org/10.1109/CVPR.2016.90. Howard, A., Sandler, M., Chu, G., Chen, L.-C., Chen, B., Tan, M., Wang, W., Zhu, Y.,

Pang, R., Vasudevan, V., 2019. Searching for mobilenetv3. Proceedings of the IEEE/  CVF International Conference on Computer Vision 1314–1324. https://doi.org/  10.48550/arXiv.1905.02244. Li, Z., Wang, D., Yan, Q., Zhao, M., Wu, X., Liu, X., 2024. Winter wheat weed detection

based on deep learning models. Comput. Electron. Agric. 227. https://doi.org/  10.1016/j.compag.2024.109448. Liu , W. , Anguelov , D. , Erhan , D. , Szegedy , C. , Reed , S. , Fu , C.-Y. , Berg , A.C. , 2016

CRediT authorship contribution statement

. Ssd: Single shot multibox detector. ComputerVision–ECCV 2016: 14th European  Conference, Amsterdam, The Netherlands, October 11–14, 2016, Proceedings, Part  I14 , 21 – 37 . doi: 10.48550/arXiv.1512.02325. Liu, X., Deng, Z., Yang, Y., 2019. Recent progress in semantic image segmentation. Artif.

Md Didarul Islam: Writing – review & editing, Writing – original  draft, Visualization, Validation, Software, Methodology, Investigation,  Formal analysis, Data curation. Wenxin Liu: Writing – review & editing,  Writing – original draft, Visualization, Validation, Software, Methodol­ ogy, Formal analysis, Data curation. Pascal Izere: Writing – review &  editing, Data curation. Puranjit Singh: Writing – review & editing,  Software, Data curation. Chong Yu: Writing – review & editing, Meth­ odology. Benjamin Riggan: Writing – review & editing, Methodology.  Kuan Zhang: Writing – review & editing, Methodology. Amit J. Jhala:  Writing – review & editing, Resources, Methodology. Stevan Knezevic:  Writing – review & editing, Methodology. Yufeng Ge: Writing – review  & editing, Methodology. Santosh Pitla: Writing – review & editing,  Methodology. Joe Luck: Writing – review & editing, Methodology.  Yeyin Shi: Writing – review & editing, Writing – original draft, Super­ vision, Resources, Project administration, Methodology, Funding  acquisition, Conceptualization.

Intell. Rev. 52 (2), 1089–1106. https://doi.org/10.1007/s10462-018-9641-3. Lu, W., Zhang, Z., Nguyen, M., 2024. A lightweight CNN–transformer network with

laplacian loss for low-altitude UAV imagery semantic segmentation. IEEE Trans.  Geosci. Remote Sens. 62, 1–20. https://doi.org/10.1109/TGRS.2024.3385318. Meng, J., Jiang, P., Wang, J., Wang, K., 2022. A MobileNet-SSD Model with FPN for

Waste Detection. J. Electr. Eng. Technol. 17 (2), 1425–1431. https://doi.org/  10.1007/s42835-021-00960-w. Nath, C.P., Singh, R.G., Choudhary, V.K., Datta, D., Nandan, R., Singh, S.S., 2024.

Challenges and Alternatives of Herbicide-Based Weed Management. In: Agronomy,  (Vol. 14, Issue 1).. Multidisciplinary Digital Publishing Institute (MDPI. https://doi.  org/10.3390/agronomy14010126. Nguyen, V.D., Bui, N.D., Do, H.K., 2022. Skin lesion classification on imbalanced data

using deep learning with soft attention. Sensors 22 (19), 1–24. https://doi.org/  10.3390/s22197530. Norouzzadeh, M.S., Nguyen, A., Kosmala, M., Swanson, A., Palmer, M., Packer, C., Clune,

J., 2017. Automatically identifying, counting, and describing wild animals in camera-trap  images with deep learning. http://arxiv.org/abs/1703.05830. NVIDIA, 2024. Nvidia Jetson Nano. https://www.nvidia.com/en-us/autonomous541

machines/embedded-systems/jetson-nano/product-development/. NVIDIA Developer, 2024. Jetson modules, support, ecosystem, and lineup. https://develope

r.nvidia.com/embedded/jetson-modules.

12

M.D. Islam et al.                                                                                                                                                                                                                                 Computers and Electronics in Agriculture 237 (2025) 110600

Parajuli, M., Shaban, M., Phung, T.L., 2023. Automated differentiation of skin

Intervention–MICCAI 2015: 18th International Conference, Munich, Germany, October 5-  9, 2015, Proceedings, Part III 18, 234–241. doi: 10.1007/978-3-319-24574-4_28. Soltani, N., Dille, J.A., Burke, I.C., Everman, W.J., VanGessel, M.J., Davis, V.M.,

melanocytes from keratinocytes in high-resolution histopathology images using a  weakly-supervised deep-learning framework. Int. J. Imaging Syst. Technol. 33 (1),  262–275. https://doi.org/10.1002/ima.22810. Qin , D. , Leichner , C. , Delakis , M. , Fornoni , M. , Luo , S. , Yang , F. , Wang , W. ,

Sikkema, P.H., 2016. Potential Corn Yield Losses from Weeds in North America.  Weed Technol. 30 (4), 979–984. https://doi.org/10.1614/WT-D-16-00046.1. Soltani, N., Dille, J.A., Burke, I.C., Everman, W.J., VanGessel, M.J., Davis, V.M.,

Banbury , C. , Ye , C. , Akin , B. , Aggarwal , V. , Zhu , T. , Moro , D. , Howard , A. ,  2024 . MobileNetV4: Universal Models for the Mobile Ecosystem . In: Leonardis , A. ,  Ricci , E. , Roth , S. , Russakovsky , O. , Sattler , T. , Varol , G. (Eds.), Computer Vision  – ECCV 2024. Springer Nature Switzerland , pp. 78 – 96 . doi: 10.1007/978-3-031-  73661-2_5. Rai, N., Sun, X., 2024. WeedVision: A single-stage deep learning architecture to perform

Sikkema, P.H., 2017. Perspectives on potential soybean yield losses from weeds in  North America. Weed Technol. 31 (1), 148–154. https://doi.org/10.1017/  wet.2016.2. Tao, J., Gu, Y., Sun, J., Bie, Y., Wang, H., 2021. Research on vgg16 convolutional neural

network feature classification algorithm based on Transfer Learning. In: 2021 2nd  China International SAR Symposium (CISS), pp. 1–3. https://doi.org/10.23919/  CISS51089.2021.9652277. Ultralytics, 2023. Ultralytics/yolov8 . Hugging Face. https://huggingface.co/Ultralyti

weed detection and segmentation using drone-acquired images. Comput. Electron.  Agric. 219. https://doi.org/10.1016/j.compag.2024.108792. Rai, N., Zhang, Y., Villamil, M., Howatt, K., Ostlie, M., Sun, X., 2024. Agricultural weed

cs/YOLOv8. Wu, Z., Chen, Y., Zhao, B., Kang, X., Ding, Y., 2021. Review of weed detection methods

identification in images and videos by integrating optimized deep learning  architecture on an edge computing technology. Comput. Electron. Agric. 216. https://  doi.org/10.1016/j.compag.2023.108442. Redmon, J., Farhadi, A., 2018. Yolov3: An incremental improvement. ArXiv Preprint

based on computer vision. Sensors 21, 3647. https://doi.org/10.3390/s21113647. Xu, B., Fan, J., Chao, J., Arsenijevic, N., Werle, R., Zhang, Z., 2023. Instance segmentation

ArXiv:1804.02767. Rehman, M.U., Eesaar, H., Abbas, Z., Seneviratne, L., Hussain, I., Chong, K.T., 2024.

method for weed detection using UAV imagery in soybean fields. https://www.elsevier.  com/open-access/userlicense/1.0/. Yurtkulu, S.C., Sahin, Y.H., Bili, B., 2019. Semantic segmentation with Extended DeepLabv3

Advanced drone-based weed detection using feature-enriched deep learning  approach. Knowl.-Based Syst. 305. https://doi.org/10.1016/j.knosys.2024.112655. Ronneberger, O., Fischer, P., Brox, T., 2015. U-net: Convolutional networks for


## Architecture. 10–13. doi: 10.1109/SIU.2019.8806244.

Zhao, Z.Q., Zheng, P., Xu, S.T., Wu, X., 2019. Object Detection with Deep Learning: A

biomedical image segmentation. Medical Image Computing and Computer-Assisted

Review. IEEE Trans. Neural Networks Learn. Syst. 30 (11), 3212–3232. https://doi.  org/10.1109/TNNLS.2018.2876865.

13
