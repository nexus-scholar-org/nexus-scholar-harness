---
workspace_id: SCI-000180
doi: 10.1016/j.atech.2025.101472
title: 'CWRepViT-Net: An encoder-decoder deep learning framework with RepViT blocks
  for crop weed semantic segmentation in soybean fields through their life journey'
authors:
- family_name: Gomroki
  given_name: Masoomeh
  orcid: null
- family_name: Benaragama
  given_name: Dilshan
  orcid: https://orcid.org/0000-0002-5878-5432
- family_name: Henry
  given_name: Christopher James
  orcid: https://orcid.org/0000-0002-2624-1502
- family_name: Badreldin
  given_name: Nasem
  orcid: https://orcid.org/0000-0003-2539-6972
- family_name: Gulden
  given_name: Robert
  orcid: null
year: 2025
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:21:24.614326+00:00'
---

# CWRepViT-Net: An encoder-decoder deep learning framework with RepViT blocks for crop weed semantic segmentation in soybean fields through their life journey

Smart Agricultural Technology 12 (2025) 101472

Contents lists available at ScienceDirect

Smart Agricultural Technology

journal homepage: www.journals.elsevier.com/smart-agricultural-technology

CWRepViT-Net: An encoder-decoder deep learning framework with RepViT  blocks for crop weed semantic segmentation in soybean fields through their  life journey

Masoomeh Gomroki , Dilshan Benaragama , Christopher James Henry , Nasem Badreldin ,   Robert Gulden *

University of Manitoba, Canada

A R T I C L E I N F O

A B S T R A C T

Keywords: Crop and weed semantic segmentation Soybean Encoder-decoder architecture RepViT Precision agriculture

With the world’s population growing at a steady rate, demand for agricultural products continues to increase. To  meet this expanding need, it is critical to employ cutting-edge knowledge and technologies. Remote sensing data  in conjunction with computer vision algorithms, plays an emerging and increasingly important role in precision  weed management, which is essential for food security and safety. Drone images are one of the most accessible  and efficient remote sensing data that can be collected in field crop production. In this study, drone images were  captured at six intervals in June and July 2024 (i.e., 21, 26, 33, 39, 45, and 52 days after seeding (DAS)) during  soybean vegetative growth phases. By employing a Deep Learning (DL) network, we performed the crop vs. weed  semantic segmentation on these captured images. The data set employed in this research was from a soybean  experiment field that included five classes: soil, soybean crops, volunteer canola, other broadleaf weeds, and  volunteer wheat plus other grassy weeds. The proposed semantic segmentation method is based on an encoder-  decoder architecture, where the encoder path uses RepViT blocks, and the decoder path uses Modified UNet  (MUNet) blocks. Since the network is trained to segment soybean crops, volunteer canola and other weed species,  the proposed method is referred to Crop-Weed-RepViT-Net (CWRepViT-Net). This study outlines a five-step  framework designed to segment crops and weeds in soybean fields using drone imagery. The steps consist of:  (1) pre-processing image data, (2) training the segmentation network, (3) performing semantic segmentation of  crop and weed classes, (4) evaluating model performance, and (5) applying the trained network to early-season  soybean growth stages. The CWRepViT-Net model achieved an overall accuracy of over 95% and a Kappa co­ efficient of 0.91, indicating strong agreement between predicted and actual labels and confirming the method’s  effectiveness for early-stage crop and weed differentiation.

All authors agree that:

This research presents an accurate account of the work performed, all data presented are accurate and methodologies detailed enough to permit others to  replicate the work.

This manuscript represents entirely original works and or if work and/or words of others have been used, that this has been appropriately cited or quoted and  permission has been obtained where necessary.

This material has not been published in whole or in part elsewhere.  The manuscript is not currently being considered for publication in another journal.  That generative AI and AI-assisted technologies have not been utilized in the writing process or if used, disclosed in the manuscript the use of AI and AI-assisted  technologies and a statement will appear in the published work.

That generative AI and AI-assisted technologies have not been used to create or alter images unless specifically used as part of the research design where such use  must be described in a reproducible manner in the methods section.

All authors have been personally and actively involved in substantive work leading to the manuscript and will hold themselves jointly and individually  responsible for its content.

* Corresponding author. E-mail address: rob.gulden@umanitoba.ca (R. Gulden).

https://doi.org/10.1016/j.atech.2025.101472 Received 1 August 2025; Received in revised form 22 September 2025; Accepted 22 September 2025

Available online 24 September 2025  2772-3755/© 2025 The Author(s). Published by Elsevier B.V. This is an open access article under the CC BY license ( http://creativecommons.org/licenses/by/4.0/ ).

M. Gomroki et al.                                                                                                                                                                                                                                Smart Agricultural Technology 12 (2025) 101472


## 1. Introduction

dos Santos Ferreira et al. [8] utilized UAV data for the detection of weeds  within soybean fields. Their proposed method employed the SLIC super  pixel technique to achieve an array of segmented images and, then  classified the weeds and soybean crop with a ConvNet model. Their  classification method is based on ConvNet, which had a slower speed  compared to other object detection methods such as YOLOv5 [47],  Faster R-CNN [48], and Single Shot Multi-Box Detector (SSD) [9,32].

The world’s population expand continuation is drivingan increase in  the demand for agricultural products. The global population is projected  to reach nine billion by 2050, needing a significant rise (estimated at 70  %) in agricultural products to fulfill world food demand [44]. Soybeans  are among the most significant crops in agriculture, utilized extensively  in human food as protein, soy milk, tofu, and oil, as well as in animal  feed as an essential supplement [21,53]. Rich in protein, iron, calcium,  potassium, vitamin E, and other micronutrients, soybeans are a  extremely valuable crop for human health and well-being [35,53].

With most studies attempting to detect and segment crops and  weeds, RGB images are typically used because of their affordability and  accessibility [3,4,34,36,40,49,50,56]. Yu et al. [60] used RGB images  and a Swin-Deeplab network to classify two types of weeds, namely,  graminoid or broadleaf weeds. Their suggested model achieved the ac­ curacy of more than 91 %. Abouzahir et al., [1] applied RGB images  captured by an aerial (UAV) and a proximal (robot) to classify, segment  and recognize various crops such as soybean (Glycine max L. Merr.),  sugar beet (Beta vulgaris L.), and carrot (Daucus carota L.) as well as  various types of weeds. A back propagation neural network (BPNN)  technique is employed in their method, which registered an accuracy of  more than 97 %. Haq [19] used UAV RGB imagery with a Convolution  Neural Network with Learning Vector Quantization (CNN-LVQ) model  to classify and segment soybean, broadleaf and grassy weeds, achieving  99 % accuracy. Some studies have successfully employed multispectral  imagery and leveraged its spectral features, such as spectral signature, to  increase discrimination between weeds and crops [3,4,34,36,40,49,50, 56]. Convolutional Neural Networks (CNNs) tend to need a huge amount  of labeled dataset for successful training [2,31]. Since such datasets are  generally in scarce availability, data augmentation techniques have  been applied to enhance generalization [2,10,16]. The application of  transfer learning (TL) can greatly speed up the training process as well as  minimize reliance on large amounts of labeled data moreover, TL is well  suited for real-time classification, thereby facilitating substantial time  and cost savings [15,42,45,62]. Jin et al. [27] applied TL with ResNet,  GoogleNet, and DenseNet networks to weed control operations, and  DenseNet performed best. Similarly, in another study, Subeesh et al.,  [52] experimented with four models, including AlexNet, GoogleNet,  InceptionV3, and Xception, for detection of weeds in bell pepper plants  and stated that InceptionV3 performed better than the other models.

Yield loss due to weed competition is a major biotic constraint in  soybean production. Farmers rely heavily on herbicides to manage  weeds [5,53] as crops and weeds are constantly engaged in a relentless  battle for shared resources such as water, sunlight, nutrients, and  growing space [7,11,20,43]. Interventionist weed control methods,  typically classified as mechanical or chemical, are commonly applied  across entire fields, despite the substantial spatial heterogeneity of  weeds within fields [58]. Effective weed management involves contin­ uous early-season monitoring by farmers and/or highly skilled workers  such as agronomists [58]. Over the decades, blanket herbicide applica­ tion that ignores weed spatial heterogeneity has become the norm in  weed control. This has led to an increased chemical load on the envi­ ronment and also has contributed to increased herbicide-resistant weed  populations globally ([43,58]; Heap, 2025). Thus, there is a critical need  for cutting-edge technology that can effectively segment weeds and  crops during the complete growth cycle of crop plants which can lead to  site directed weed management and thereby reduce the reliance on  herbicides and other weed management approaches. Deep Learning  (DL) methods have the potential to solve this function in an effective  way [51].

Today, using remote sensing data, such as drone, satellite, and aerial  photography is becoming a necessity in expansive agriculture regions,  and one of these uses is in weed and crop detection and segmentation  [38]. Despite advancements in precision herbicide application and me­ chanical weed control techniques, accurate detection of weeds among  diverse variety of crops remains a challenge for implementation of  site-specific weed management strategies. Satellite based remote  sensing techniques are gaining momentum in agriculture, but their  image resolution is insufficient for use in precision weed management,  particularly at the early crop-weed developmental stage where inter­ ventionist techniques are most effective. The rise of Unmanned Aerial  Vehicle (UAV) technology, however, is providing high spatial resolution  imagery (e.g. 5 cm resolution) throughout the entire growing season for  use in precision weed management applications, which are increasingly  applied in crop production to improve crop productivity and lower  operating expenditures ([12,19]; S [30,39,46,54]; J [63])

According to recent research progress in digital agriculture, the weed  and crop semantic segmentation faces some major challenges, such as  semantic segmentation at early crop and weed developmental stages,  occlusion of leaves, and illumination effects [2]. It is therefore important  to develop a DL framework that can overcome these challenges while  ensuring an acceptable trade-off between accuracy and performance  [12]. The proposed method tries to overcome to such limitations as well  as be generalizable to identify other crops and weeds, robust against  different environmental conditions, and computationally efficient. The  current paper suggests an encoder-decoder framework to adjust the  Semi-Transfer Learning (Semi-TL) method [15] to segment soybean  (Glycine max L. Merr.) as crop, volunteer canola (Brassica napus L.),  broad leaf weeds (such as: Chenopodium album L., Amaranthus retroflexus  L. and Cirsium arvense L.), grassy weeds (included: volunteer wheat  which was sown and the naturally-occurring, late-emerging Setaria sp.  that could not always be completely eliminated, Secale cereale L. and  Avena fatua L.) and soil in experimental soybean fields as an improve­ ment over existing methods.

Improvements of DL methods in computer vision have triggered a  variety of DL-based approaches for crop and weed semantic segmenta­ tion, many of which have shown respectable outcomes ([12]; K [25,38];  J [64]). The integration of remote sensing data with DL methods for crop  and weed semantic segmentation has garnered increasing attention  among researchers in recent years. Khan et al., [29] introduce a deep  learning framework for farmland semantic segmentation. Their pro­ posed network consists of feature fusion module and a global contextual  module. In another study, Khan, Basalamah, et al., [28], proposed a  novel encoder-decoder deep learning frame work based on attention  modules for crop-weed segmentation. They achieved superior results on  a challenging dataset. Razfar et al., [46] introduced an edge-based weed  and crop detection framework based on deep networks such as Mobi­ leNetV2, ResNet50, and 5-layer CNN with open-source data. Yu et al.  [59] designed a soybean field weed detection system with the use of  DeepLabV3+ and Swin Transformer models with university lab datasets  for training. Tetila et al. [53] used RGB drone imagery to detect soybean  crops and two types of weed species: Conyza bonariensis L. and Digitaria  insularis L. They used the improved YOLOv5 network for this purpose.

The main contributions of this paper are as follows:


## 1. Introduce an encoder-decoder architecture with RepViT blocks

acting as encoder path and MUNet blocks acting as decoder path. 
Compared to the original RepViT network, this structure reduces the 
number of parameters, thus the speed of the training process in­
creases, making it useful for crop and weed semantic segmentation in 
a reasonable time frame with high accuracy.
2. The encoder blocks (RepViT) were pre-trained [55] by the ImageNet 
dataset to boost learning. Using the advantages of the Semi-Transfer

2

M. Gomroki et al.                                                                                                                                                                                                                                Smart Agricultural Technology 12 (2025) 101472

Fig. 1. Map of study location in Winnipeg, Canada; RGB drone images for (a) 21 DAS, (b) 26 DAS, (c) 33 DAS, (d) 39 DAS, (e) 45 DAS and (f) 52 DAS.

Learning technique improves the network training speed and enables  this architecture to overcome the limitation of GPU capacities. 3. For simultaneous segmentation of five classes: soybean as crop,  volunteer canola, soil, other broadleaf weeds and all grassy weeds  combined, a multilabel semantic segmentation network is proposed.  This kind of semantic segmentation is especially challenging due to  the high visual similarity among crops and weeds, particularly dur­ ing the early developmental stages. 4. Develop a network that predict segmentation of soybean crops under  various scenarios and over time, based on trained encoder-decoder  architecture, at six different days after seeding (DAS) 5. Construct a labeled dataset, optimized for semantic segmentation of  soybean, volunteer canola, other broadleaf weed and grassy weed

categories using drone images. Such a dataset is an asset to train AI  models.


## 2. Materials and datasets

The study site was the University of Manitoba Ian N. Morrison  Research Farm, located in Carman, MB, Canada (Fig. 1). The site has a  humid continental climate, the soil is an Orthic Black Chernozem that is  predominantly Denham series soil, with a loamy texture and an average  pH of 5.4 [6]. Each experiment was laid out as a split-block randomized  complete block design, with both weedy and weed-free blocks included  in each of the four replicates and consisted of three parts, namely,  broadleaf weed, grassy weeds and natural weeds. The data used in this  research wereRGB images captured using a DJI Matrice 300 RTK drone

Fig. 2a. The portion of image 26 DAS was considered as the first GT (market with the red rectangle). In the legend, canola, weed type I and weed type II stands for  volunteer canola, other broadleaf weeds and all grassy weeds, respectively.

3

M. Gomroki et al.                                                                                                                                                                                                                                Smart Agricultural Technology 12 (2025) 101472

Fig. 2b. The portion of image 45 DAS was considered as the second GT (market with the red rectangle). In the legend, canola, weed type I and weed type II stands for  volunteer canola, other broadleaf weeds and all grassy weeds, respectively.

Fig. 3. Flowchart of proposed method for crop weed semantic segmentation. The rectangles indicate the respective test, training and validations sets. The yellow and  red cogs indicate training and validation training process. They act like two powerful arms to generate the trained model which is showed by maroon cog, and the  green cog indicates the final model used for prediction, which is depicted via both an accuracy assessment (top right), and further prediction of field images (bottom).

(DJI Tehcnology Co. Ltd., Shenzhen, Guangdong, China) equipped with  a Zenmuse L1 LiDAR sensor (DJI Tehcnology Co. Ltd., Shenzhen,  Guangdong, ChChina) flown at an altitude of 18m. The images were  captured at 21 (soybean at V1 stage), 26 (V2 stage), 33 (V2 stage), 39  (V3-V4 stage), 45 (R1 stage), and 52 DAS (R1-R2 stage) for soybean and  surrogate weeds throughout June and July 2024 (Fig. 1). These time  points covered emergence to the R1 stages of soybean development.

chosen, and ground truth (GT) for image segmentation were created  manually (Figure 2a). At 21, 26, 33 and 39 DAS the soybean plants were  in the V (vegetative) developmental stages. During these times, although  there are differences in the size and the number of leaves, they can be  addressed by the network with a single GT. As soybean plants increased  in size through the vegetative phase and developed toward the repro­ ductive phase, a second GT for image segmentation was captured at 45  DAS. The 45 DAS covers the R (reproductive) developmental stages fo

To train the network, a portion of the image captured at 26 DAS was

4

M. Gomroki et al.                                                                                                                                                                                                                                Smart Agricultural Technology 12 (2025) 101472

Fig. 4. The structure of MobileNet and RepViT Blocks. The MobileNet block includes a 1 × 1 expansion convolution and a 1 × 1 projection layer to enable interaction  among channels. A 3 × 3 depthwise (DW) convolution (A. G [22]) is equipped after the 1 × 1 expansion convolution for the fusion of spatial information. The  optional squeeze-and-excitation (SE) layer (J [24]) is also moved up to be placed after the DW, as it depends on spatial information interaction.

soybean where the shape and size of the crop and weeds can be quite  different from those in the V stages. The soybean plants were at the late  vegetative, to early reproductive stage while volunteer canola plants had  begun anthesis as evidenced by the yellow flowers associated with the  canola plants at this time. A portion of the 45 DAS RGB image was  selected and labeled as a second GT for image segmentation sample, is  shown in Figure 2b To generate the GTs, these two portions of the 26  DAS and 45 DAS images were used. The polygons of crops and weeds  were drawn in QGIS software and different layers of “soybean”,

“volunteer canola”, “broad leaf weeds” and “grassy weeds” were sepa­ rated, and different numbers were assigned to them so the final GTs were  obtained as shown in Fig. 2a and b Each GT image segmentation con­ tained five classes: soil, soybean, volunteer canola, other broadleaf  weeds, and all grassy weeds


## 3. Proposed method

The method introduced in this research includes three main steps: (1)

Fig. 5. The network architecture diagram for RepViT [26]. In this figure, Act (activation function), FNN (feed-forward module), DW (depth-wise separable  convolution), SE (Squeeze-and-Excitation module).

5

M. Gomroki et al.                                                                                                                                                                                                                                Smart Agricultural Technology 12 (2025) 101472

Fig. 6. The structure of UNet and MUNet convolution layers.

raster data pre-processing, (2) training the Crop-Weed Rep ViT-Net  (CWRepViT-Net) network for crop and weed semantic segmentation,  and (3) prediction to evaluate the performance of the network and  generate crop and weed maps for the vegetative portion of the soybean  crop growth cycle. The overall workflow of the proposed method is  illustrated in Fig. 3. The training, validation and test data for the  CWRepViT-Net were considered as 60 %, 20 % and 20 % of data,  respectively. This procedure is depicted in the flowchart given in Fig. 3.

3.1. Raster data pre-processing

In the pre-processing stage, the captured images were georeferenced  and the orthophoto mosaics were generated. The input images were  subdivided into sub-images of dimensions of 128 × 128 pixels. All the  images were then normalized, and the training and validation data were  distinguished from the test data. After that, data augmentation was  carried out through image rotations by 90◦, 180◦, and 270◦for gener­ alization of the model. These processes prepared the dataset to be used  as the input for the DL network.

Fig. 7. Top: the structure of RepViT, which contains one stem and four stages (represented with a different color). Bottom: the structure of CWRepViT-Net using  RepViT as an encoder path and MUNet as a decoder path. The encoder path is concatenated with the decoder path at five different resolutions (Stem, Stage1, Stage2,  Stage3 and Stage4).

6

M. Gomroki et al.                                                                                                                                                                                                                                Smart Agricultural Technology 12 (2025) 101472

3.2. RepViT network

3.5. State-of-the-art methods

The RepViT model (Revisiting Mobile CNN from a ViT Perspective)  was proposed by Wang et al. [55] for the first time. They revisited  lightweight convolutional neural networks (CNNs) from the respect of  Vision Transformers (ViT) and introduced a revised model to leverage  the advantages of both architectures [55]. In the RepViT architecture,  the MobileNetV3 as a standard lightweight CNN is seamlessly fused with  a lightweight ViT architecture. The structure blocks of MobileNetV3 and  RepViT are shown in Fig. 4. An optional Squeeze-and-Excitation (SE)  module (J [24]) is depicted by the SE block in this figure. Normalization  layers and non-linearity components have been omitted for simplicity  [55].

The performance of CWRepViT-Net was compared with other state-  of-the-art deep learning networks. One of the main contributions of this  research is the development of a network that segments weeds and crops  with great precision with comparative training speeds. The proposed  method is compared with MobileNetV3 (A [23]), MobileViT [37],  TinyNet [18], and TinyViT [57] which are some cutting-edge DL net­ works. MobileNetV3 (A [23]) which is tuned to mobile phone CPUs  through a combination of hard-aware network architecture search; it is  applied for object detection and semantic segmentation, has been  selected for comparison because it has been used in the architecture of  RepViT as described in Section 3.2. MobileViT [37] is a lightweight and  general purpose vision transformer for mobile devices, which had  proper performance on semantic segmentation of MS-COCO dataset, so  it was considered for comparison. TinyNet [18] aims to explore the  twisting rules for obtaining DL networks with minimum model size and  computational costs. TinyViT [57] resolve the problem of having a large  number of parameters in vision transformer model, in which the main  idea is based on transformer knowledge from a large pre-trained model  to a small one. Since both TinyNet and TinyViT have training times  comparable to that of CWRepViR-Net, they are used for comparison with  our proposed network. For semantic segmentation purpose, all of these  methods were implemented as the encoder path in encoder-decoder  architectures.

Overall, the RepViT architecture has a single stem and four stages.  The stem is a module that processes the input image. In each stage, the  image is processed in hierarchical resolutions of B × C1 × H


## 4 × W

4, B × C2 
× H


## 8 × W

8, B × C3 × H
16 × W
16 and B × C4 × H
32 × W
32 where H ×W is the size of 
the original image, B is batch size, and Ci’s are channel sizes [26,55]. 
Stages 1 to 4 consist of RepViT blocks and optionally a RepViT SE Block 
Module ([26,55]; H [61]). The overall structure of the RepViT network 
is illustrated in Fig. 5. In this architecture: DW represented depth-wise 
separable convolution module (A. G [22]), SE indicates the 
squeeze-and-excitation module (J [24]), FFN stands for the feed-forward 
network module, FC includes fully connected layers, and pooling refers 
to global average pooling [26].

In the CWRepViT-Net, the stem and stage blocks of the RepViT  network are used as the encoder path. The RepViT network was pre-  trained using the ImageNet dataset, so the Semi-TL technique [15] is  used in this study. The architecture of CWRepViT-Net will be explained  in further detail in Section 3.4.


## 4. Experimental results

In this section, the performance of the proposed method is measured.  This section contains experimental parameter settings, accuracy  assessment metrics, and comparison of experimental results.

3.3. Modified UNet (MUNet) network

4.1. Experimental parameter settings

The UNet network was initially proposed by Ronneberger et al.  (2015) for the segmentation of medical images. The UNet is an encoder-  decoder network in which the encoder path extracts deep features from  the input image and the decoder path learns to extracts spatial locations  of the features ([13]; D [41]). The convolution layer of the original UNet  network is depicted in Fig. 6. In this study, a modification of UNet  (MUNet) blocks are used as decoder path as defined by [13]. The MUNet  layers are also shown in Fig. 6.

The CWRepViT-Net and other networks were implemented using  TensorFlow 2.10.1 and Python 3.9.21. The hardware configuration used  in this research study was a NVIDIA GeForce RTX 4070 GPU, an Intel(R)  Core (TM) i7–14,700 CPU, and 64GB of RAM. The dataset was parti­ tioned into patches of 128 × 128 pixels. 60 % of the data were assigned  to training, 20 % to validation and the remaining 20 % to test. In the first  GT, 237 patches were accounted as test data and 947 patches were  available as train-validation ones before augmentation. Following  augmentation using rotation with angles of 90◦, 180◦and 270◦this  value reached 3788 patches. In the second GT, 274 and 1094 patches  were considered as test and train-validation, respectively. After  augmentation, the train-validation patches reached 4376 patches. All  networks were trained with 100 epochs with a batch size of 16. The  Adam optimizer was applied with a learning rate and learning decay of  1.0E-4 and 1.0E-6, respectively. The encoder path of the proposed  network was pre-trained using the ImageNet dataset. In this study, the  network was proposed for multiclass semantic segmentation. The focal  loss function [14,33] is defined as:.

3.4. CWRepViT-Net architecture for crop and weed detection and  semantic segmentation

As discussed earlier, the proposed CWRepViT-Net is an encoder-  decoder DL network to segment various types of crops and weeds in  soybean fields. In the encoder path, RepViT blocks pre-trained by the  ImageNet dataset are used in a Semi-TL technique [15]. In the decoder  path of the CWRepViT-Net, for extracting the deep features of crop and  weeds through RGB images, the MUNet blocks [13] are used to recon­ struct the spatial location of crop and weed deep feature in purpose of  generating final segmented map. The CWRepViT-Net architecture was  used to detect and segment soil, soybean, volunteer canola, other  broadleaf weeds, and all grassy weeds in separate classes.

∑ c

Lfocal loss = −

αi(1 −yi)γtilog(yi) (1)

i=1

where c corresponds to the number of classes, ti denotes the true prob­ ability distribution, yi represents the probability distribution of predic­ tion, γ is a hyperparameter of the loss function, which in this study  equals to 2 and αi is another hyperparameter representing the class  weights.

CWRepViT-Net achieved high accuracy with reasonable training  speed. In addition, the proposed method is fully automated, and does not  need any further post process for semantic segmentation. Importantly,  this network can detect and segment weeds and crops well across  different stages of soybean vegetative and early reproductive develop­ ment. In this study, the RepViT architecture blocks with approximately  15 million (15 M) parameters were employed (Table1). RepViT has one  stem and four stages which are concatenated with Conv2D-Transpose  blocks in different hierarchical resolution, creating the CWRepViT-Net  framework (Fig. 7).

4.2. Performance metrics

The metrics for evaluating the performance of the networks are  Overall Accuracy (OA), Precision, Kappa Coefficient (KC), F1-score, and

7

M. Gomroki et al.                                                                                                                                                                                                                                Smart Agricultural Technology 12 (2025) 101472


> **Table 1**

> Quantitative evaluation results for the comparison of CWRepViT-Net with state-of-the-art models.

Method Accuracy  (%)

Kappa Coefficient  (KC)

Precision  (%)

F1-score  (%)

Intersection over Union  IoU (%)

Time of training  (min sec)

Parameters (Million)

original  form

encoder-  decoder form

MobileNetV3 94.11 0.89 98.68 98.47 96.98 22 min 45sec 5.5 6.5 MobileViT 92.65 0.87 97.72 98.05 96.17 34 min 50sec 5.5 9.7 TinyNet 91.77 0.86 98.74 97.88 95.75 29 min 35sec 6.2 7.2 TinyViT 92.20 0.86 98.61 98.01 96.01 32 min 55sec 11.0 11.2 CWRepViT-Net (Proposed

95.87 0.91 98.95 98.76 97.35 33 min 10sec 14.23 13.63

method)

Intersection over Union (IoU), which are expressed in terms of Equations  2 to 6.

weeds was also very challenging for those networks. In order to further  investigation of the performance of the proposed network compared  with the other networks in segmentation broadleaf weeds and volunteer  canola, Fig. 9 illustrates samples of these classes. The CWRepViT-Net  was effective in segmenting and distinguishing between canola and  other broadleaf weeds such as Redroot pigweed (Amaranthus retroflexus  L.), Canada thistle (Cirsium arvense L.) and Lambs quarters (Chenopodium  album L.) which can be challenging to identify even by human vision, at  the seedling and early vegetative developmental stages. The proposed  method, however, was still capable of accurately segmenting these  relatively similar plant species. Fig. 9(a-F) depict samples of broadleaf  weeds. In Fig. 9(a), a broadleaf weed is tiny and the illumination effects  during capturing cause blurring. Nevertheless, the proposed method  successfully segmented it, whereas the other networks fail to do so. In  Fig. 9(b), there is an overlapping between the leaves of the broadleaf  weed and the soybean crop. The proposed method can properly distin­ guish between the leaves and preserve the boundaries of both the soy­ bean crop and the broadleaf weed. In contrast, the other networks tend  to segment the broadleaf weed as soybean crop. In Fig. 9(c), the  broadleaf weed has complex leaves that resemble grassy weed shapes.  The proposed method addresses this challenge, whilst the other net­ works were unable to segment this broadleaf weed. Fig. 9(d) shows a  mixed dense area of weeds and the crop, in which the proposed method  was able to segment the broadleaf weed in this densely mixed region,  whereas the other networks failed. Additionally, the shape of the  broadleaf weed’s leaves presents a challenge for the other networks.  Fig. 9(e–g) show volunteer canola samples. All the networks can  segment them, but TinyNet and TinyViT failed to accurately preserve the  boundaries. In Fig. 9(h), there is a dense mixture of broadleaf weed and  volunteer canola, and the proposed method can segment them  effectively.

precision = TP TP + FP (2)

F1 −score = 2 × TP (2 × TP) + FP + FN (3)

IoU = TP TP + FP + FN (4)

Overall Accuracy (OA) = TP + TN TP + FN + TN + FP (5)

Kappa Coeficient (KC) = 2 × (TP × TN −FN × FP) (TP + FP)(FP + TN) + (TP + FN)(FN + TN)

(6)

where TP indicates the true positives, TN shows true negatives, FP and  FN represent the false positives and false negatives, respectively.

4.3. Comparison of experimental results

To compare the performance of the networks, Table 1 illustrates the  results using the accuracy evaluation metrics proposed in Section 4.2.  The MobileNetV3, MobileViT and TinyNet, when implemented as  encoder-decoder architecture are no longer lightweight as before; the  parameters of these networks in the encoder-decoder form are greater  than those in their original format as shown in Table1. The training  speed of the CWRepViT-Net is efficient compared to other networks,  with respect to the number of parameters. For instance, despite having  fewer parameters than CWRepViT-Net (13.63 M), MobileViT (9.7 M)  needs more training time and hence its training speed is comparatively  less efficient.

4.4. Ablation study

As the ablation study, the existence and non-existence of some parts  of the proposed method and their effects on the performances are dis­ cussed. Since the proposed encoder-decoder network is based on two  networks, the RepViT and MUnet is supposed in two models, S#1 and  S#2. The S#1 model was designed only with the RepViT network, and  the S#2 model is designed only with the MUNet network. Also, the S#3  model is designed based on conventional UNet. The results of these  models along with the main CWRepViT-Net are presented in Table2.

The highest OA and highest KC of 95.87 % and 0.91, respectively,  were obtained with the proposed method. One of the main contributions  of this study was to develop a network that could effectively segment  crops and weeds, and this was achieved successfully by the proposed  method. CWRepViT-Net also surpasses the comparative models as  indicated in precision, F1-score, and IoU scores (Table 1) which proves  high proficiency of the network to identify and segment the crop and  weeds in soybean fields.

As outlined in Table 2, the overall performance of the given method  decreases when any of the networks are eliminated or when the struc­ ture of the decoder path block is changed.

The dataset used in this study consists of soil, soybean, volunteer  canola, other broadleaf weeds and all grassy weeds classes from the  seedling to the early reproductive stages of soybean growth and devel­ opment. Fig. 8 illustrates the confusion matrices of the networks  providing an in-depth analysis of per-class classification performance.  As shown in Fig. 8(a), the proposed method correctly segments most  classes with more than 90 % accuracy. Among all classes, broadleaf  weeds are the most challenging because soybean and volunteer canola  are also broadleaf plants which exhibit large divergence in the shape of  their leaves. The confusion matrices of the other networks are given in  Fig. 8(b-e) which shows that semantic segmentation of other broadleaf


## 5. Discussion

The performance of the CWRepViT-Net for segmenting weeds and  crops is assessed through qualitative, quantitative, and visual assess­ ment. For this purpose, RGB drone images were captured at 21 (Soybean  at the V1 stage), 26 (V2 stage), 33 (V2 stage), 39 (V3–4 stage), 45 (R1  stage), and 52 DAS (R1-R2 stage) during June and July. The model was

8

M. Gomroki et al.                                                                                                                                                                                                                                Smart Agricultural Technology 12 (2025) 101472

Fig. 8. Confusion Matrix of: (a) proposed method, (b) MobileNetV3, (c) MobileViT, (d) TinyNet and (e) TinyViT. In the confusion matrices, canola, weed type I and  weed type II stand for volunteer canola, other broadleaf weeds and all grassy weeds, respectively.

trained by a portion of drone images at 26 and 45 DAS and the trained  model was then utilized for prediction at other growth stages of soybean.  Clearly, the network was very effective, having been trained on small,  labeled dataset and was able to make accurate predictions for all stages  of vegetative and early reproductive soybean growth. The trained  network was applied to predict at 21, 26, 33, 45 and 52 DAS and it had

proper performance in crop weed semantic segmentation. For more  detail, the results of these times are shown in the following figures.

Fig. 10 illustrates the 21 DAS RGB image of the whole soybean field  along with the results from the network. The three experiments that  comprised the study from left to right are arranged at the natural weed  experiment, the grassy weed experiment and the broadleaf weed

9

M. Gomroki et al.                                                                                                                                                                                                                                Smart Agricultural Technology 12 (2025) 101472

Fig. 9. Segmentation results of broad leaf weeds (a-d) and volunteer canola (e-h) for all networks.

The second prediction date was 26 DAS, where the crop and weeds  were noticeably larger . As a general trend, volunteer canola develops  more rapidly than soybean and is considerably larger at 26 DAS than at  21 DAS. In western Canada, canola has a higher growth rate than soy­ beans early during the cooler part of the growing season [17]. Two areas  were chosen for examinations in Fig. 11 to explore the 26 DAS results  further. Area1 belongs to the broadleaf weed portion of the experiment,  where volunteer canola was the seeded broadleaf weed in the soybean  crop. As illustrated in Fig. 11(c) and (d), the network distinguishes and  segments the two crops and preserves their leaf shapes very well. Area2  is the weed area of grass, where soybean and grassy weeds are dominant.  The suggested network also effectively separated and identified crops  and weeds in this area (Fig. 11(e) and (F)). In addition, the network was  capable to reconstruct the crop-weed boundaries well at disjunction,  preserving both soybean and grassy weeds boundaries.


> **Table 2**

> Ablation study of the proposed method.

Method Accuracy  ( %)

Kappa  Coefficient  (KC)

Precision  ( %)

F1-  score  ( %)

Intersection  Over Union (  %)

S#1 94.25 0.87 98.71 98.54 97.04 S#2 93.74 0.86 97.98 98.27 96.85 S#3 89.42 0.72 90.45 90.01 89.47 CWRepViT-

95.87 0.91 98.95 98.76 97.35

Net

experiment, respectively. CWRepViT-Net was utilized for detecting and  segmenting five classes, including: soil (dark blue), soybean (light blue),  volunteer canola (green), other broadleaf weeds (orange) and all grassy  weeds (crimson). To assess the performance of the proposed method,  two areas shown by red rectangles in the RGB image were chosen. At 21  DAS, the soybean crop and weeds were at the seedling stage and still  quite small. Area1 corresponds to a broadleaf section of the experiment  containing soybean, volunteer canola at different densities and some  naturally occurring weeds, all of which were segmented successfully by  the proposed network. For a precise investigation of shadow conditions  and how the network performs under such conditions, three zoomed-in  windows were considered in Area1, marked by yellow rectangles  (Fig. 10(c)). As shown in Fig. 10(e) and (f), the network can distinguish  soybean and volunteer canola in the presence of shadow effects. In the  21 DAS captured image, the impact of shadows is significant, but the  network can still differentiate between the boundaries of crops, weeds,  and their shadows. Area2 is part of the natural weeds portion of the  experiment, where a high presence of grassy weeds were observed. The  proposed network was able to accurately detect and segment these types  of weeds as well.

At 33 DAS, two regions indicated by the red rectangles (Fig. 12) were  analyzed. Area1 is from the region of natural weeds, where soybean  crops and grassy weeds were dense. The proposed network is able to  accurately segment them. In the most natural weed part, where the crop  and weeds are densely mixed, the network can segment them effectively.  To better showcase the dense mixture of weeds, a zoomed-in yellow  rectangle was selected in Area1. As depicted in Fig. 12(e) and (f), the  segmentation results demonstrate the network’s accurate performance  in conditions with densely mixed crops and weeds. Area2 includes an  area of wetter soil on the left side of the image that retained more water  after rainfall than other parts of the field. As can be seen from in 12, the  proposed method effectively segments soybean crops from grassy weeds  in this area without specific training under wet soil conditions. This  shows a degree of insensitivity of the suggested methodology to various  environmental conditions such as excessive water stress immediately  prior to capturing the remote sensed data. Under such conditions, the  captured remote sensing data experiences different illumination

10

M. Gomroki et al.                                                                                                                                                                                                                                Smart Agricultural Technology 12 (2025) 101472

Fig. 10. Prediction results at 21 DAS: (a) RGB image, (b) proposed network results, (c) RGB image of Area1, (d) results of Area1, (e) RGB images of zoomed-in  widows of Area1 for presenting shadow effects, (f) results of zoomed-in windows (g) RGB image of Area2 and (h) results of Area2. In the legend, canola, weed  type I and weed type II stands for volunteer canola, other broadleaf weeds and all grassy weeds, respectively.

11

M. Gomroki et al.                                                                                                                                                                                                                                Smart Agricultural Technology 12 (2025) 101472

Fig. 11. Prediction results at 26 DAS: (a) RGB image, (b) proposed network results, (c) RGB image of Area1, (d) results of Area1, (e) RGB image of Area2 and (f)  results of Area2. In the legend, canola, weed type I and weed type II stands for volunteer canola, other broadleaf weeds and all grassy weeds, respectively.

12

M. Gomroki et al.                                                                                                                                                                                                                                Smart Agricultural Technology 12 (2025) 101472

Fig. 12. Prediction results at 33 DAS: (a) RGB image, (b) proposed network results, (c) RGB image of Area1, (d) results of Area1, (e) RGB image of zoomed-in widow  of Area1 for presenting dense mixture of weeds condition, (f) results of zoomed-in window,(g) RGB image of Area2, (h) results of Area2, (i) RGB images of zoomed-in  widows of Area2 for presenting different illumination and environmental condition and (j) results of zoomed-in windows. In the legendre, canola, weed type I and  weed type II stands for volunteer canola, other broadleaf weeds and all grassy weeds, respectively.

13

M. Gomroki et al.                                                                                                                                                                                                                                Smart Agricultural Technology 12 (2025) 101472

Fig. 13. Prediction results at 39 DAS: (a) RGB image, (b) proposed network results, (c) RGB image of Area1, (d) results of Area1, (e) RGB images of zoomed-in  widows of Area1 for presenting dense mixture of weed and crops condition and overlapping leaves, (f) results of zoomed-in window, (g) RGB image of Area2,  (h) results of Area2, (i) RGB images of zoomed-in widows of Area2 for presenting effect of shadows and occlusion and (j) results of zoomed-in windows. In the  Legend, canola, weed type I and weed type II stands for volunteer canola, other broadleaf weeds and all grassy weeds, respectively.

14

M. Gomroki et al.                                                                                                                                                                                                                                Smart Agricultural Technology 12 (2025) 101472

(caption on next page)

15

M. Gomroki et al.                                                                                                                                                                                                                                Smart Agricultural Technology 12 (2025) 101472

Fig. 14. Prediction results at 45 DAS: (a) RGB image, (b) proposed network results, (c) RGB image of Area1, (d) results of Area1, (e) RGB images of zoomed-in  widows of Area1 for presenting dense overlapping between the leaves of crop and weed, (f) results of zoomed-in window, (g) RGB image of Area2, (h) results of  Area2, (i) RGB images of zoomed-in widows of Area2 for presenting effect of heavy overlapping between soybean and canola and (j) results of zoomed-in windows.  Based on the legend, soybean is in light blue, volunteer canola with flowers in yellow is in yellow, other broadleaf weeds (weed type I) in orange, all grassy weeds  (weed type II) in crimson, and soil in dark blue.

conditions compared to other times. To further investigate the effects of  varying environmental and illumination conditions, three zoomed-in  windows within Area2 (highlighted with yellow rectangles (Fig. 12g))  were considered. As shown in Figs. 12 (i) and (j), the network can  segment soybeans and grassy weeds under different lighting conditions,  even when the illumination is variable and the crop and weed colors  tend to appear yellow instead of green.

The performance of the proposed method is compared with other  state-of-the-art networks. As illustrated, the RGB images of two regions  and their correspond GTs were compared, which are delineated with red  rectangles (Fig. 16). Area1 includes crop, volunteer canola and other  broadleaf weeds, the CWRepViT-Net has the best performance in seg­ menting the soybean and volunteer canola and broadleaf weeds. Area2  is in the region of soybeans and grassy weeds and the suggested network  is able to successfully segment and reconstruct the boundaries and  shapes of soybean and weeds. The performance of the other methods in  Area2 is worth comparing to the proposed method.

Two areas at 39 DAS were considered (Fig. 13). At this time, soybean  and canola had grown significantly and all grassy weeds, volunteer  canola and soybean began to coalesce with significant overlap of leaves  among the classes at higher densities. Other broadleaf weeds remained  relatively rare at this time. Two areas are used to study the results in  further detail, as shown in Fig. 13. Area 1 is a part of the grassy weeds  and broadleaf weeds patches. The proposed network managed to  segment soybean, volunteer canola, and weeds in this field. For a better  investigation of the densely mixed crop and weed conditions, two  zoomed-in yellow rectangles were selected in Area1. As depicted in  Fig. 13(e) and (F), the proposed network can segment crops and weeds  even in dense areas with overlapping leaves and in densely mixed crop  and weed conditions. Area2 is a part of the weed-free region, with  soybean crops occupying over 90 % of the field. In this field, the network  also managed to segment and identify the soybean crops correctly. To  demonstrate the effect of shadows and occlusion, two zoomed-in win­ dows marked with yellow rectangles (Fig. 13(g)) were selected in Area  2. As shown in Fig. 13(i) and (j), occlusion and shadow effects are pre­ sent in the soybean crops. Nevertheless, the network is capable of  accurately segmenting and delineating the proper boundaries between  the crops and their shadows even under these conditions.

Generally, the CWRepViT-Net can accurately segment soybean,  volunteer canola, broadleaf and grassy weeds. The MobileNetV3 failed  to segment broadleaf weeds as well as preserve individual plant  boundaries. The MobileViT also missed broadleaf weeds and cannot  reconstruct the boundaries of the crop and weeds. Similarly, TinyNet  and TinyViT cannot reconstruct the boundaries of the crop and weeds  and did not provide precise segmented results.


## 6. Conclusion

A new encoder-decoder architecture, called CWRepViT-Net, was  introduced using the RepViT blocks in the encoder path and the MUNet  blocks in the decoder path for segmenting crops and weeds. Semi-  Transfer Learning technique was utilized to pre-train the encoder path of  the proposed network. RGB images captured by drone at 21, 26, 33, 39  (V stages), 45, and 52 (R stages) DAS were considered as datasets, and  the network is used for segmenting these six different developmental  stages. The training speed (33 min 10 s) of this method is efficient  relative to its number of parameters in encoder-decoder form. A five-  class multilabel semantic segmentation is generated as the result of  this network which consists of: volunteer canola, soybean, soil, all grassy  weeds, and other broadleaf weeds. Furthermore, a novel labeled dataset  for AI and DL methods for precision agriculture has been demonstrated.  The proposed network achieved an OA of 95.87 % and a KC of 0.91,  which verifies its strong capability in accurately segmenting the soybean  crop and weeds.

The results at 45 DAS, when soybean reached its peak vegetative  growth and volunteer canola had begun to flower, are reported (Fig. 14).  Both soybean and volunteer canola had also undergone a change in  shape from earlier time points. The 45 DAS result’s maximum abun­ dance is found in soybean, volunteer canola, and grassy weeds. Two  areas were chosen for a more detailed examination: Area1 is a part of the  natural weed region, where soybean and grassy weeds are intertwined,  and canola is sparsely scattered among them. The intended network is  capable of processing high-density areas effectively and distinguish all  weed classes from the crop. To better illustrate the densely overlapping  weeds and crops and their leaves, two zoomed-in yellow rectangles in  Area1 were selected (Fig. 14(g)). As shown in Fig. 14(e) and (f),  although there is significant overlap among the soybean crops, grassy  weeds, and volunteer canola, the network can effectively segment them  and accurately discover their boundaries. Area2 is in the broadleaf weed  region, where volunteer canola and soybean were grown in alternating  rows. In this region, the network is able to segment and distinguish  soybean and volunteer canola effectively. For further investigation, two  zoomed-in windows in Area2 were marked with yellow rectangles. In  these windows, there is a mixture of dense soybean crop and volunteer  canola with heavily overlapping leaves, and the network is able to  segment them properly.

Since the performance of this method is encouraging, it is recom­ mended to apply this method to expansive agricultural fields which  contained different crops and weeds and its semantic segmentation  performance is study. Moreover, the proposed network is suggested to  be applied on other remote sensing data, such as satellite and drone data  with alternate spectral bands like multispectral imagery for crops and  weeds semantic segmentation.

Ethics in publishing statement

I testify on behalf of all co-authors that our article submitted fol­ lowed ethical principles in publishing.

Statements

The last prediction date was 52 DAS (Fig. 15). Both soybean and the  surrogate and natural weeds were in the reproductive phase at this time.  Two areas are chosen for studying more detailed. Area1 is in the region  of grassy weeds, where soybean crops and the grassy weeds were highly  overlapped. As illustrated in Fig. 15, the proposed method kept the  edges between soybean crops and grassy weeds intact and separated  their shapes successfully. Area2 is in the broadleaf weed region, where  the proposed method separated volunteer canola and soybean effec­ tively even when their leaves are highly overlapping.

These two labeled datasets are accessible upon request to the cor­ responding author for research purposes in the field of AI-based preci­ sion agriculture.

CRediT authorship contribution statement

Masoomeh Gomroki: Writing – review & editing, Writing – original  draft, Visualization, Validation, Supervision, Software, Resources,

16

M. Gomroki et al.                                                                                                                                                                                                                                Smart Agricultural Technology 12 (2025) 101472

Fig. 15. Prediction results at 52 DAS: (a) RGB image, (b) proposed network results, (c) RGB image of Area1, (d) results of Area1, (e) RGB image of Area2 and (f)  results of Area2. Based on the legend, soybean is in light blue, volunteer canola—with flowers in yellow—is in yellow, other broadleaf weeds (weed type I) in orange,  all grassy weeds (weed type II) in crimson, and soil in dark blue.

17

M. Gomroki et al.                                                                                                                                                                                                                                Smart Agricultural Technology 12 (2025) 101472

Fig. 16. Comparison among the results of the proposed method and other networks. Two areas are shown with red rectangles in RGB image. soil (dark blue), soybean  (light blue), volunteer canola (green), other broadleaf weeds (orange) and all grassy weeds (crimson).


## Methodology, Investigation, Formal analysis, Data curation, Conceptu­

alization. Dilshan Benaragama: Writing – review & editing, Validation, 
Project administration, Funding acquisition, Data curation. Christopher 
James Henry: Writing – review & editing, Validation. Nasem Badrel­
din: Writing – review & editing, Validation. Robert Gulden: Writing – 
review & editing, Validation, Project administration, Funding acquisi­
tion, Data curation.

[8] A. dos Santos Ferreira, D.M. Freitas, G.G. da Silva, H. Pistori, M.T. Folhes, Weed

detection in soybean crops using ConvNets, Comput. Electron. Agric 143 (2017)  314–324. [9] A. dos Santos Ferreira, D.M. Freitas, G.G. da Silva, H. Pistori, M.T. Folhes, Weed

detection in soybean crops using ConvNets, Comput. Electron. Agric 143 (2017)  314–324. [10] A. Farooq, J. Hu, X. Jia, Analysis of spectral bands and spatial resolutions for weed

classification via deep convolutional neural network, IEEE Geosci. Remote Sens.  Lett. 16 (2) (2018) 183–187. [11] J. Gao, D. Nuyttens, P. Lootens, Y. He, J.G. Pieters, Recognising weeds in a maize

crop using a random forest machine-learning algorithm and near-infrared snapshot  mosaic hyperspectral imagery, Biosyst. Eng. 170 (2018) 39–50. [12] O.L. García-Navarrete, A. Correa-Guimaraes, L.M. Navas-Gracia, Application of

Declaration of competing interest

convolutional neural networks in weed detection and identification: a systematic  review, Agriculture 14 (4) (2024) 568. [13] M. Gomroki, M. Hasanlou, J. Chanussot, Automatic 3D multiple building change

The authors would like to thank the Western Grains Research  Foundation, Manitoba Crop Alliance, the Manitoba Pulse and Soybean  Growers Association, Manitoba Canola Growers Association and the  NSERC Alliance Program for providing funding for this research. The  authors also wish to thank R Dueck and J Roset for their technical  assistance and BASF Canada Inc. and Bayer Crop Science Canada for  supplying seed for this project.

detection model based on encoder–decoder network using highly unbalanced  remote sensing datasets, IEEe J. Sel. Top. Appl. Earth. Obs. Remote Sens 16 (2023)  10311–10325. [14] M. Gomroki, M. Hasanlou, J. Chanussot, D. Hong, UNet-GCViT: a UNet-based

framework with global context vision transformer blocks for building damage  detection, Int. J. Remote Sens (2025) 1–24. [15] M. Gomroki, M. Hasanlou, P. Reinartz, STCD-EffV2T Unet: semi transfer learning

EfficientNetV2 T-unet network for urban/land cover change detection using  Sentinel-2 satellite images, Remote Sens. (Basel) 15 (5) (2023) 1232. [16] E. Gothai, P. Natesan, S. Aishwariya, T.B. Aarthy, G.B. Singh, Weed identification

Data availability

using convolutional neural network and convolutional neural network  architectures, in: 2020 Fourth International Conference on Computing  Methodologies and Communication (ICCMC), 2020, pp. 958–965. [17] P. Gregoire, J.D. Rosset, R.H. Gulden, Volunteer Brassica napus (L.) interference

Data will be made available on request.


## References

with soybean [Glycine max (L.) Merr.]: management thresholds, plant growth, and  seed return, Can. J. Plant Sci. 101 (4) (2021) 556–567. [18] K. Han, Y. Wang, Q. Zhang, W. Zhang, C. Xu, T. Zhang, Model rubik’s cube:

[1] S. Abouzahir, M. Sadik, E. Sabir, Bag-of-visual-words-augmented histogram of

oriented gradients for efficient weed detection, Biosyst. Eng 202 (2021) 179–194. [2] F.D. Adhinata, R. Sumiharto, A comprehensive survey on weed and crop

twisting resolution, depth and width for tinynets, Adv. Neural Inf. Process. Syst 33  (2020) 19353–19364. [19] M.A. Haq, CNN based automated weed detection system using UAV imagery,

classification using machine learning and deep learning, Artif. Intell. Agric. (2024). [3] M.H. Asad, A. Bais, Weed detection in canola fields using maximum likelihood

Comput. Syst. Sci. Eng. 42 (2) (2022). [20] A.M. Hasan, D. Diepeveen, H. Laga, M.G. Jones, F. Sohel, Object-level benchmark

classification and deep convolutional neural network, Inf. Process. Agric. 7 (4)  (2020) 535–545. [4] N.N. Che’Ya, E. Dunwoody, M. Gupta, Assessment of weed classification using

for deep learning-based detection and classification of weed species, Crop Prot. 177  (2024) 106561. [21] J. Hou, C. Wang, X. Hong, J. Zhao, C. Xue, N. Guo, J. Gai, H. Xing, Association

hyperspectral reflectance and optimal multispectral UAV imagery, Agronomy 11  (7) (2021) 1435. [5] CONAB, C. (2023). nda Acompanhamento da safra brasileira: gr˜aos safra 2021/

analysis of vegetable soybean quality traits with SSR markers, Plant Breed. 130 (4)  (2011) 444–449. [22] Howard, A.G., Zhu, M., Chen, B., Kalenichenko, D., Wang, W., Weyand, T.,

2022. Superintendˆencia de Marketing e Comunicaç˜ao (Sumac, 2022. V. 8.  Disponível Em: https://www.Conab.Gov.Br/Info-Agro/Safras/Graos/Boletim-Da  -Safra-de-Graos. Acesso Em: 29 Out. [6] S.K. Curtis, M.H. Entz, K.A. Stanley, D.J. Cattani, K.D. Schneider, Cropping system

Andreetto, M., & Adam, H. (2017). Mobilenets: efficient convolutional neural  networks for mobile vision applications. ArXiv preprint arXiv:1704.04861. [23] A. Howard, M. Sandler, G. Chu, L.-C. Chen, B. Chen, M. Tan, W. Wang, Y. Zhu,

typologies perform differently under climate stress in Manitoba, Canada: multi-  criteria assessment, Can. J. Plant Sci. 104 (5) (2024) 441–459. [7] M.N. DO˘GAN, A. Ünay, ¨O. Boz, F. Albay, Determination of optimum weed control

R. Pang, V. Vasudevan, Searching for mobilenetv3, in: Proceedings of the IEEE/  CVF International Conference on Computer Vision, 2019, pp. 1314–1324.

timing in maize (Zea mays L.), Turk. J. Agric. For. 28 (5) (2004) 349–354.

18

M. Gomroki et al.                                                                                                                                                                                                                                Smart Agricultural Technology 12 (2025) 101472

[24] J. Hu, L. Shen, G. Sun, Squeeze-and-excitation networks, in: Proceedings of the

[44] P. Radoglou-Grammatikis, P. Sarigiannidis, T. Lagkas, I. Moscholios, A compilation

IEEE Conference on Computer Vision and Pattern Recognition, 2018,  pp. 7132–7141. [25] K. Hu, Z. Wang, G. Coleman, A. Bender, T. Yao, S. Zeng, D. Song, A. Schumann,

of UAV applications for precision agriculture, Comput, Netw 172 (2020) 107148. [45] A. Rahman, Y. Lu, H. Wang, Performance evaluation of deep learning object

detectors for weed detection for cotton, Smart Agric. Technol. 3 (2023) 100126. [46] N. Razfar, J. True, R. Bassiouny, V. Venkatesh, R. Kashef, Weed detection in

M. Walsh, Deep learning techniques for in-crop weed recognition in large-scale  grain production systems: a review, Precis. Agric 25 (1) (2024) 1–29. [26] M. HUANG, H. WEI, An efficient method for sea cucumber recognition and sorting

soybean crops using custom lightweight deep learning models, J. Agric, Food Res 8  (2022) 100308. [47] Redmon, J., & Farhadi, A. (2018). Yolov3: an incremental improvement. ArXiv

based on improved YOLOv9 and RepViT, IEICE Trans. Fundam. Electron. Commun.  Comput. Sci. (2024). [27] X. Jin, T. Liu, Z. Yang, J. Xie, M. Bagavathiannan, X. Hong, Z. Xu, X. Chen, J. Yu,

Preprint arXiv:1804.02767. [48] S. Ren, K. He, R. Girshick, J. Sun, Faster r-cnn: towards real-time object detection

Y. Chen, Precision weed control using a smart sprayer in dormant bermudagrass  turf, Crop Prot. 172 (2023) 106302. [28] S.D. Khan, L. Alarabi, S. Basalamah, Segmentation of farmlands in aerial images by

with region proposal networks, Adv, Neural Inf, Process, Syst 28 (2015). [49] I. Sa, M. Popovi´c, R. Khanna, Z. Chen, P. Lottes, F. Liebisch, J. Nieto, C. Stachniss,

A. Walter, R. Siegwart, WeedMap: a large-scale semantic weed mapping framework  using aerial multispectral imaging and deep neural network for precision farming,  Remote Sens. (Basel) 10 (9) (2018) 1423. [50] U. Shafi, R. Mumtaz, J. García-Nieto, S.A. Hassan, S.A.R. Zaidi, N. Iqbal, Precision

deep learning framework with feature fusion and context aggregation modules,  Multimed, Tools, Appl 82 (27) (2023) 42353–42372. [29] S.D. Khan, S. Basalamah, A. Lbath, Weed–Crop segmentation in drone images with

a novel encoder–decoder framework enhanced via attention modules, Remote  Sens. (Basel) 15 (23) (2023) 5615. [30] S. Khan, M. Tufail, M.T. Khan, Z.A. Khan, S. Anwar, Deep learning-based

agriculture techniques and practices: from considerations to applications, Sensors  19 (17) (2019) 3796. [51] D. Su, H. Kong, Y. Qiao, S. Sukkarieh, Data augmentation for deep learning based

identification system of weeds and crops in strawberry and pea fields for a  precision agriculture sprayer, Precis, Agric 22 (6) (2021) 1711–1727. [31] F.J. Knoll, V. Czymmek, L.O. Harders, S. Hussmann, Real-time classification of

semantic segmentation and crop-weed classification in agricultural robotics,  Comput, Electron, Agric 190 (2021) 106418. [52] A. Subeesh, S. Bhole, K. Singh, N.S. Chandel, Y.A. Rajwade, K.V.R. Rao, S.P. Kumar,

weeds in organic carrot production using deep learning algorithms, Comput,  Electron, Agric 167 (2019) 105097. [32] W. Liu, D. Anguelov, D. Erhan, C. Szegedy, S. Reed, C.-Y. Fu, A.C. Berg, in: Ssd:

D. Jat, Deep convolutional neural network models for weed detection in polyhouse  grown bell peppers, Artif. Intell. Agric. 6 (2022) 47–54. [53] E.C. Tetila, B.L. Moro, G. Astolfi, A.B. da Costa, W.P. Amorim, N.A. de Souza

Single shot multibox detector. Computer Vision–ECCV 2016: 14th European  Conference, Amsterdam, The Netherlands, October 11–14, 2016, Proceedings, Part I  14, 2016, pp. 21–37. [33] W. Liu, L. Chen, Y. Chen, Age classification using convolutional neural networks

Belete, H. Pistori, J.G.A. Barbedo, Real-time detection of weeds by species in  soybean using UAV images, Crop Prot. 184 (2024) 106846. [54] A.N. Veeranampalayam Sivakumar, J. Li, S. Scott, E. Psota, A. J Jhala, J.D. Luck,

Y. Shi, Comparison of object detection and patch-based classification deep learning  models on mid-to late-season weed detection in UAV imagery, Remote Sens.  (Basel) 12 (13) (2020) 2136. [55] A. Wang, H. Chen, Z. Lin, J. Han, G. Ding, Repvit: revisiting mobile cnn from vit

with the multi-class focal loss, IOP Conf. Ser.: Mater. Sci. Eng. 428 (2018) 012043. [34] P. Lottes, R. Khanna, J. Pfeifer, R. Siegwart, C. Stachniss, UAV-based crop and

weed classification for smart farming, in: 2017 IEEE International Conference on  Robotics and Automation (ICRA), 2017, pp. 3024–3031. [35] J.M.G. Mandarino, J.R. Bordignon, M.C. Carr˜ao Panizzi, J.M.G. Mandarino, J.

perspective, in: Proceedings of the IEEE/CVF Conference on Computer Vision and  Pattern Recognition, 2024, pp. 15909–15920. [56] A. Wang, W. Zhang, X. Wei, A review on weed detection using ground-based

R. Bordignon, M.C.C. Panizzi, A Soja e a Saúde Humana, 2003. [36] M. Mckay, M.F. Danilevicz, M.B. Ashworth, R.L. Rocha, S.R. Upadhyaya,

machine vision and image processing techniques, Comput, Electron, Agric 158  (2019) 226–240. [57] K. Wu, J. Zhang, H. Peng, M. Liu, B. Xiao, J. Fu, L. Yuan, Tinyvit: fast pretraining

M. Bennamoun, D. Edwards, Focus on the crop not the weed: canola identification  for precision weed management using deep learning, Remote Sens. (Basel) 16 (11)  (2024) 2041. [37] Mehta, S., & Rastegari, M. (2021). Mobilevit: light-weight, general-purpose, and

distillation for small vision transformers, Eur. Conf. Comput. Vis. (2022) 68–85. [58] J. You, W. Liu, J. Lee, A DNN-based semantic segmentation for detecting weed and

mobile-friendly vision transformer. ArXiv Preprint arXiv:2110.02178. [38] Pai, D.G., Kamath, R., & Balachandra, M. (2024). Deep Learning Techniques For

crop, Comput, Electron, Agric 178 (2020) 105750. [59] H. Yu, M. Che, H. Yu, J. Zhang, Development of weed detection method in soybean

Weed Detection in Agricultural Environments: A Comprehensive Review. IEEE  Access. [39] A.I.B. Parico, T. Ahamed, An aerial weed detection system for green onion crops

fields utilizing improved deeplabv3+ platform, Agronomy 12 (11) (2022) 2889. [60] H. Yu, M. Che, H. Yu, J. Zhang, Development of weed detection method in soybean

fields utilizing improved deeplabv3+ platform, Agronomy 12 (11) (2022) 2889. [61] H. Zhang, B. Gong, B. Ma, Z. Tao, S. Wang, Lightweight vision architecture with

using the you only look once (YOLOv3) deep learning algorithm, Eng. Agric.  Environ. Food 13 (2) (2020) 42–48. [40] J.M. Pe˜na, J. Torres-S´anchez, A.I. de Castro, M. Kelly, F. L´opez-Granados, Weed

mutual distillation for robust photovoltaic defect detection in complex  environments, Sol. Energy 291 (2025) 113386. [62] H. Zhang, Z. Wang, Y. Guo, Y. Ma, W. Cao, D. Chen, S. Yang, R. Gao, Weed

mapping in early-season maize fields using object-based analysis of unmanned  aerial vehicle (UAV) images, PLoS. One 8 (10) (2013) e77151. [41] D. Peng, Y. Zhang, H. Guan, End-to-end change detection for high resolution

detection in peanut fields based on machine vision, Agriculture 12 (10) (2022)  1541. [63] J. Zhang, F. Yu, Q. Zhang, M. Wang, J. Yu, Y. Tan, Advancements of UAV and deep

satellite images using improved UNet++, Remote Sens. (Basel) 11 (11) (2019)  1382. [42] H. Peng, Z. Li, Z. Zhou, Y. Shao, Weed detection in paddy field using an improved

learning technologies for weed management in Farmland, Agronomy 14 (3) (2024)  494. [64] J. Zhang, F. Yu, Q. Zhang, M. Wang, J. Yu, Y. Tan, Advancements of UAV and deep

RetinaNet network, Comput, Electron, Agric 199 (2022) 107179. [43] H.-R. Qu, W.-H. Su, Deep learning-based weed–crop recognition for smart

learning technologies for weed management in Farmland, Agronomy 14 (3) (2024)  494.

agricultural equipment: a review, Agronomy 14 (2) (2024) 363.

19
