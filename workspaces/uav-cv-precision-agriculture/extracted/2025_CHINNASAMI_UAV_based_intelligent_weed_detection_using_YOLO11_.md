---
workspace_id: SCI-000637
doi: 10.15835/nbha53414822
title: UAV-based intelligent weed detection using YOLO11 and PSPNet for precision
  agriculture
authors:
- family_name: CHINNASAMI
  given_name: Rajavenkatesswaran KULLAMPALAYAM
  orcid: null
- family_name: Rajappan
  given_name: Sivaraj
  orcid: https://orcid.org/0000-0001-8170-5130
- family_name: Murugasamy
  given_name: Vijayakumar
  orcid: null
year: 2025
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:46:37.174872+00:00'
---

# UAV-based intelligent weed detection using YOLO11 and PSPNet for precision agriculture

Kullampalayam Chinnasami R et al. (2025)  Notulae Botanicae Horti Agrobotanici Cluj-Napoca

Volume 53, Issue 4, Article number 14822

AcademicPres Notulae Botanicae Horti

DOI:10.15835/nbha53414822

Cluj-Napoca Agrobotanici

Research Article Research Article Research Article Research Article.

UAV UAV UAV UAV-based intelligent  based intelligent  based intelligent  based intelligent weed detection using YOLO11 and weed detection using YOLO11 and weed detection using YOLO11 and weed detection using YOLO11 and  PSPNet for precision agriculture PSPNet for precision agriculture PSPNet for precision agriculture PSPNet for precision agriculture

Rajavenkatesswaran KULLAMPALAYAM CHINNASAMI1*,

Sivaraj RAJAPPAN2, Vijayakumar MURUGASAMY3

1Nandha College of Technology, Department of Information Technology, Erode, 638 052, Tamil Nadu,   India; rajannam318@gmail.com (*corresponding author)

2Nandha Engineering College, Department of Computer Science and Engineering, Erode, 638 052, Tamil Nadu,   India; rsivarajcse@gmail.com

3Erode Sengunthar Engineering College, Department of Information Technology, Erode, 638057, Tamil Nadu,   India; tovijayakumar@gmail.com      Abstract Abstract Abstract Abstract    Weeds significantly threaten rice yield and quality, necessitating precise herbicide spraying to control  their growth and enhance agricultural productivity. However, conventional methods address object detection  and segmentation separately, limiting their efficiency in identifying areas infested with weeds. This study  introduces YOLO11-PSPNet, a combination of YOLO11-s and the Pyramid Scene Parsing Network  (PSPNet), for weed detection and semantic segmentation using Unmanned Aerial Vehicle (UAV) images. A  dataset was developed that comprised real-time images of rice paddy fields captured via UAV, which included  weed varieties such as Echinochloa (barnyard grass), Cyperus difformis (small flower umbrella sedge), and  Echinochloa colona (jungle rice). YOLO11-s detects weed-infested regions by generating bounding boxes,  whereas PSPNet performs pixel-wise segmentation to ensure accurate weed localisation. Then, the proposed  RAdam optimiser with a Sharpness-Aware Minimization (SAM) function was introduced to train the model  YOLO11-PSPNet, which improved the training stability of the proposed model. The proposed YOLO11- PSPNet model was trained and tested on a UAV-based dataset, achieving a mAP50 of 99.56% with an inference  time of 6.2ms. These results validate the efficiency of the model in precise weed detection, leading to improved  crop health and higher yields. This study highlights the potential of YOLO11-PSPNet in precision agriculture  for optimizing weed management using advanced deep-learning techniques.

Keywords: Keywords: Keywords: Keywords: convergence speed; data annotation; EVO II Pro drone; pyramid pooling module;  region-specific segmentation; tillering stage; weed species      Introduction Introduction Introduction Introduction    Rice is one of the most important food crops in the world, thriving comfortably in hot and humid  tropical climates. However, weeds in paddy fields are the primary reason for the reduction in rice production

Received: 18 Oct 2025. Received in revised form: 01 Dec 2025. Accepted: 07 Dec 2025. Published online: 22 Dec 2025.  From Volume 49, Issue 1, 2021, Notulae Botanicae Horti Agrobotanici Cluj-Napoca journal uses article numbers in place of the  traditional method of continuous pagination through the volume. The journal will continue to appear quarterly, as before, with four  annual numbers.

Kullampalayam Chinnasami R et al. (2025). Not Bot Horti Agrobo 53(4):14822

and quality. Over 30,000 plant species are classified as weeds, with 250 posing significant threats (Xuan et al.,  2025), often reducing crop yields by as much as 34%. Weeds compete with rice for sunlight, nutrients, and  water, which hinders crop growth (Mao et al., 2024; Chen et al., 2025a). The aggravated growth of weeds can  be due to soil disturbance and changes in light, temperature, moisture, and pH in crop fields (Ameena et al.,  2024). In the past, various methods, including manual weeding, mechanical and machine weeding, and  traditional spraying, have been used to control weeds. Hand weeding is also a control solution for weeds, but it  requires a large number of workers. To overcome these challenges, remote sensing methods have been used to  enhance weed management by monitoring and capturing images of the Earth’s surface without direct contact.

To improve rice production, Unmanned Aerial Vehicles (UAVs) must be used in the fertiliser or  herbicide spraying process, which addresses the labour shortage in rural areas (Rosle et al., 2021; Meesaragandla  et al., 2024). UAVs, commonly referred to as drones, are extensively used in precision agriculture to detect  potential problems and capture high-resolution images for examination and research (Yu et al., 2022). The  advancement of Deep Learning (DL), computer vision, and Machine Learning (ML) algorithms has led to  rapid weed detection in paddy fields (Sharma et al., 2024). To reduce herbicide usage, Site-Specific Weed  Management (SSWM) using Variable Rate Technology (VRT) is employed to apply herbicides. These  methods primarily focus on weed sensing and mapping technologies (Genze et al., 2022).

Weed detection in paddy fields is challenging due to visual and environmental complexities. Rice and  weed species often share similar colour tones and leaf textures, resulting in high inter-class similarity. In this  situation, DL effectively detects weeds (Murad et al., 2023). Dense canopy structure leads to overlapping  vegetation, causing partial occlusion of weed pixels. UAV-based imaging additionally introduces scale variation,  illumination changes, water reflection, soil background noise, and shadow interference under field variability  (Moazzam et al, 2023). The YOLOv10n network enhances weed detection and fertiliser spraying capabilities  (Li et al., 2024). DL technology has become a significant image-processing approach. DL models, such as  Convolutional Neural Networks (CNNs) and Deep Neural Networks (DNNs), have yielded remarkable  results in weed detection, pest identification, and maturity grading (Zhang et al., 2024b). Although recent  advances in DL and UAV-based imaging have enabled object detection or segmentation tasks for weed  detection, existing methods often address these tasks separately, limiting their precision and practical  applicability for targeted weed localization. This study aims to bridge this gap by developing an integrated weed  detection and segmentation YOLO11-PSPNet (You Only Look Once-Pyramid Scene Parsing Network)  framework that leverages UAV imagery to enable precise, site-specific weed management in rice fields, reducing  chemical usage and promoting sustainable agriculture. The main contributions of this study are as follows:

•  We developed a real-world rice paddy field dataset created during the tillering stage to control weeds  at an early stage. In our study, the primary weed species observed and annotated in the dataset included  Echinochloa (barnyard grass), Cyperus difformis (small-flowered umbrella sedge), and Echinochloa  colona (jungle rice), as these are among the most widespread and problematic weed types in rice fields  in our study region.   •  This study proposes a YOLO11-PSPNet framework that performs weed detection and segmentation  simultaneously for spraying applications, whereas existing models perform only one of these functions.  This study utilised a YOLO11-s object detection model to detect weed-infested regions and generate  bounding boxes, enabling the immediate identification of weeds without scanning the entire field.  This study utilised region-specific semantic segmentation through PSPNet to generate pixel-wise  segmentation masks on the bounding boxes, thereby identifying the exact locations of weeds in paddy  fields.  •  We introduced a Rectified Adam (RAdam) optimiser with a Sharpness-Aware Minimization (SAM)  function that improved the training stability and convergence speed of the proposed model during  training. This enhanced the ability of the model to detect and segment weeds in previously unseen  fields correctly.

2

Kullampalayam Chinnasami R et al. (2025). Not Bot Horti Agrobo 53(4):14822

The remainder of this paper is organised as follows: Section 2 analyses existing works on weed detection  and target-spraying system approaches; Section 3 defines the workflow of the weed detection and segmentation  system; Section 4 presents the experimental results and a discussion; and Section 5 concludes the paper.

Literature survey  This section analyses existing studies on weed detection and segmentation approaches to identify the  objectives and research gaps of existing works.

Object detection-based weed detection approaches  Ahmad et al. (2021) utilized three pre-trained convolutional classifiers to differentiate weed species  from crop pixels. However, the effective controlled conditions, classification only approaches lack spatial  localisation and limiting their utility for field-level spraying. Peng et al. (2022) introduced a WeedDet model  based on RetinaNet to detect the complex information in the images through the extracted features using Det- ResNet. Guo et al. (2024) presented a multi-scale feature-enhanced DETR framework, termed RMS-DETR,  which improved the detection performance of weeds in rice fields and identified the exact location of weeds.  The model had limitations in detecting small-area targets, which affected its accuracy. Chen et al. (2025b)  developed a GE-YOLO model to detect weeds in paddy rice fields, which utilised an enhanced version of the  YOLOv8 object detection model. The model utilises the Efficient Multi-Scale Attention (EMA) mechanism  to improve feature representation. However, the model could not cover the stringent weeds that generally affect  rice fields. Ma et al. (2025) developed a YOLO-Crop Weed Detection (CWD) model that incorporates a  hybrid attention mechanism to enhance its ability to differentiate between crops and weeds. The model  requires improvements by adding advanced algorithms to the digital agricultural system to improve the  accuracy of weed detection.

Segmentation-based weed detection approaches  Chen et al. (2024) suggested a Point-supervised Instance Segmentation Network (PIS-Net) to develop  an effective method for segmenting weeds and provide effective support for future herbicide applications.  However, this model utilised low-resolution mobile phone images for weed detection, which limited the  segmentation performance. Similarly, Habib et al. (2024) introduced a segmentation model named DWUNet,  which combines depth-wise convolutions with the UNet architecture for effective weed management in  agriculture, thereby improving accuracy and speed in real-time applications. However, the model only utilised  the digital camera of the smartphone, which limited the accuracy of weed detection. Zhang et al. (2024a)  employed a lightweight weed localisation algorithm based on YOLO instance segmentation to accurately  identify and localise weeds. However, the model requires improvements to enhance the algorithm’s ability to  identify weed spots, and thus, it cannot achieve a higher detection accuracy. To overcome this, Machidon et al.  (2025) implemented a DL model, SqeeseSlimU-Net (SSU-Net), to enhance the abilities of UAVs in complex  segmentation tasks. The model achieved real-time weed segmentation in precision agriculture by combining  the semantic segmentation ability of the U-Net architecture. However, the model faced limitations owing to  the need for high-quality datasets.

Hybrid approach combing weed detection and segmentation  Islam et al. (2025) developed a CNN-based models for object detection and semantic segmentation tasks  in row crop production. The study demonstrated that object detection models achieve higher speed, while  segmentation models provide spatial detail. However, the study limited the system’s applicability to broader  situations as other common weed species.

Thus, analysing the existing works, object detection models provide field-scale weed detection and  segmentation approaches provide high-resolution masks for accurate spraying. Object detection model lacks  pixel-level precision, and semantic segmentation is more resource-intensive. The existing approaches mostly  rely on detection or segmentation rather than combining both for precise weed detection. This study aims to  bridge these gaps by developing a YOLO11-PSPNet for weed detection and segmentation sequentially to

3

Kullampalayam Chinnasami R et al. (2025). Not Bot Horti Agrobo 53(4):14822

support future targeted spraying, ensuring improved crop health and sustainable farming practices. The  combined YOLO11-PSPNet model provides efficient real-time object detection and robust semantic  segmentation in paddy fields.

Materials and methods Materials and methods Materials and methods Materials and methods    The proposed methodology detects weeds in rice paddy fields using the YOLO11-PSPNet framework,  as illustrated in Figure 1. Initially, the videos captured by the UAV were converted into frames and stored as a  raw dataset. The images were preprocessed to enhance the quality of the training dataset using histogram  equalisation and data augmentation techniques. The proposed framework was trained sequentially. Initially,  the YOLO11-s model detected weed-infested regions and generated bounding boxes. Then, the bounding box  regions were segmented using PSPNet, which generated pixel-wise segmentation masks to identify the locations  of the weeds. The introduced optimiser, RAdam with SAM, enhances the training stability and convergence  speed of the proposed weed detection system. This supports targeted fertiliser or herbicide spraying in paddy  fields, enhancing crop health and, consequently, the crop yield.


> **Figure 1.**

> Figure 1.
Figure 1.
Figure 1. Overview of the proposed YOLO11-PSPNet detection-segmentation framework 
 
Data acquisition 
The data were collected from the study area located at Therakalputhoor, Kanyakumari District, India, 
between July and August 2024, and updated in a Roboflow repository (Dataset Link: 
https://app.roboflow.com/pest-i22ng/weed-ge616/1). We utilised a UAV to gather images of paddy rice fields 
at the tillering stage. The study area was 150 m in length and 85 m in width, with 12,750 total square meters, 
as shown in Figure 2. We utilised the EVO II Pro drone manufactured by Autel Robotics to capture the images, 
flying at an altitude of 5m to 25m with a CMOS lens with an efficient 20 million pixels, and the Ground 
Sampling Distance (GSD) was 0.225 cm/pixel. The drone tracked a determined path with 80% forward and

4

Kullampalayam Chinnasami R et al. (2025). Not Bot Horti Agrobo 53(4):14822

80% side overlap. The rice field data were obtained from a vertical perspective to cover the total study area. A  total of 1215 rice field UAV images were collected, and the sample dataset images are shown in Figure 3. This  represents the weed-infested regions and rice paddy fields in the UAV images. The dataset images were split  into 70% for training, 20% for testing, and 10% for validation. For model training, the images were resized to  640 × 640 pixels.


> **Figure 2.**

> Figure 2.
Figure 2.
Figure 2. Schematic representation of the experimental rice field captured at an altitude of 5m to 25m from 
the ground


> **Figure 3.**

> Figure 3.
Figure 3.
Figure 3. Sample images from the UAV-captured dataset, displaying various weed-infested regions in rice 
fields  
 
Data annotation and preprocessing 
Preprocessing is an essential step in enhancing the quality of the dataset. The UAV rice field dataset was 
preprocessed using histogram equalisation and data augmentation techniques. We manually labelled the 
bounding boxes on the UAV images using the annotation tool Roboflow, as illustrated in Figure 4.

5

Kullampalayam Chinnasami R et al. (2025). Not Bot Horti Agrobo 53(4):14822


> **Figure 4.**

> Figure 4.
Figure 4.
Figure 4. Overview of data creation and processing pipeline 
 
Histogram equalization 
Histogram equalisation was used to strengthen the colour and enhance the contrast of paddy-field weed 
images. This approach is applied by allocating a gray value level. The images were processed by improving the 
range of colours with a lower limit to the darkest point and by reducing the range of colours with an upper limit 
to the brightest point. This phase is essential for ensuring accurate visualisation of minor features and patterns. 
Histogram equalisation is achieved using Equation (1).

   



(1)





Where  represents the number of images in the data, 	 signifies the range of grey values, which ranges  from 0 to the current grey value  , and  represents the number of images on the grey value.

Data augmentation  In this study, the data augmentation process improved the robustness and diversity of the training  dataset. Data augmentation included processes such as horizontal and vertical flipping, scaling, rotation,  translation, cropping, contrast adjustment, colour jitter, and adding noise to make the model more generalised  to variations of the same object in rice weeds and improve robustness. Random flipping and translation were  used to detect specific object locations. Efficient scaling and rotation allow the model to learn the different  ways in which weed patterns appear from various angles and sizes. To ensure efficient detection in complex  environments, colour jittering and contrast adjustments consist of varied lighting, occlusions, shading, and  canopy density to improve model robustness and diverse field conditions. After preprocessing, the preprocessed  images were sent for efficient weed detection using YOLO11.

Weed detection through YOLO11  YOLO11 is the latest version of the YOLO object detection model designed for high-speed and accurate  object detection and classification. In this study, YOLO11-s was used for rice-weed detection in paddy fields.  YOLO11-s was specifically chosen for this study because of its advanced multi-scale feature extraction, superior  detection accuracy, and real-time inference capabilities, which make it highly suitable for weed detection in rice  crops. Additionally, weed detection requires the ability to identify small, obstructed, and low-contrast objects  in paddy fields, which is a major limitation of previous detection models. YOLO11-s addresses this issue  through multi-scale feature extraction and anchor-free detection, thereby improving its ability to detect  concealed objects effectively. In this study, we trained YOLO11-s on preprocessed images to detect weeds in  paddy fields. The model detects weed-infested areas and generates bounding boxes on the images. The

6

Kullampalayam Chinnasami R et al. (2025). Not Bot Horti Agrobo 53(4):14822

YOLO11-s architecture includes three basic components: backbone, neck, and head. It introduces an effective  architecture with C3K2 blocks, Spatial Pyramid Pooling Fast (SPFF), and an advanced attention mechanism,  Cross-Stage Partial with Spatial Attention (C2PSA). The architectural diagram of YOLO11-s is shown in  Figure 5. The backbone serves as a feature extractor, using convolutional layers to create multi-scale feature  maps and reduce the spatial dimensions.


> **Figure 5.**

> Figure 5.
Figure 5.
Figure 5. Architecture diagram of the YOLO11-s model, highlighting key layers and detection 
components 
 
The C3k2 Cross Stage Partial (CSP) Bottleneck replaces the previous C2f block, utilising a smaller 
kernel size for faster processing while maintaining performance. The C2PSA block enhances spatial attention, 
allowing the model to focus on the critical image regions. The neck block integrates features at different scales 
and transforms them into the head block for final detection, employing C3k2 and C2PSA to improve feature 
aggregation and reduce the computational cost. The head block generates the final detection output through 
multiple Convolution-BatchNorm-Silu (CBS) layers after the C3k2 blocks. It acts as a basic element in both 
the feature extraction and detection process. Finally, the final detection output is generated for the rice-weed 
images based on the refined feature maps. The proposed framework was trained sequentially, YOLO11-s 
trained for weed object detection, and the resulting bounding-box regions then passed as PSPNet for semantic 
segmentation.

Region-specific segmentation using PSPNet  In the field of semantic segmentation tasks, specifically for complex paddy environments, such as rice  field segmentation from UAV images, YOLO11-s as a backbone architecture significantly impacted the model  performance, as illustrated in Figure 6.

7

Kullampalayam Chinnasami R et al. (2025). Not Bot Horti Agrobo 53(4):14822


> **Figure 6.**

> Figure 6.
Figure 6.
Figure 6. Structural overview of the PSPNet segmentation model used for precise weed localisation 
 
In this study, we utilised PSPNet as the segmentation model with the attention of our experimentation, 
choosing an effective and accurate backbone. The bounding box weed regions from YOLO11-s were sent to 
the PSPNet for fine-grained segmentation. The model applies pixel-wise segmentation masks to highlight the 
weeds in the paddy fields. The PSPNet utilised a YOLO11-s output image as an input image that was sent for 
feature extraction through a pretrained ResNet model with a dilated network that supports the extraction of 
comprehensive details through YOLO11-s bounding box images. The feature map size was one-eighth of the 
input image. Then, the Pyramid Pooling Module (PPM) is utilised to collect appropriate details on top of the 
extracted feature map. A four-level pyramid was generated to cover all weed-detected images. The pooling 
kernel captures several contextual scales at diverse levels. Details from the pyramid are shared with the original 
feature map through a process known as fusion. The PPM fuses features at four pyramid scales represented by 
1×1, 2×2, 3×3, and 6×6, which distinguishes the feature map into several sub-regions and generates pooled 
images for diverse positions. Each pyramid level is diminished using a 1×1 convolution to retain the global 
feature weights. The resulting low-dimensional feature maps were then upsampled using bilinear interpolation 
to match the size of the original feature map. Finally, the features from the four levels were concatenated to 
produce the final global feature for the PPM. A convolution layer processes this combined detail to create the 
final prediction map, which enhances the integrated details and provides a comprehensive prediction of rice-
field weeds by generating the masks.

RAdam with SAM optimiser  The combined model for object detection through YOLO11-s and segmentation through PSPNet  simultaneously can lead to unstable gradients and slow convergence, particularly with noisy UAV images. To  overcome these issues, we utilised the Rectified Adam (RAdam) optimiser with Sharpness-Aware  Minimization (SAM) to produce a training process. This leads to a more effective and reliable weed-detection  system. The SAM improves model generalisation by simultaneously minimising the loss value and loss  sharpness. RAdam optimiser is expressed in Equations (2) and (3).

  1 −  ,    1 − ,  (2)

   −.   + 

.   (3)

Where ,  denotes the training samples,  signifies the learning rate, and  represents the rectified  factor that stabilises early updates. The SAM allows the optimiser to find parameters in the flatter regions of  the loss. This was performed using a two-step update. Firstly, perturb the weights  slightly in the gradient  direction. Then, we optimise for the worst-case increase in the loss.

This ensures that the model is good at the training set and is also robust against small variations, such as  lighting or field condition changes in UAV images. This ensures that the proposed RAdam with SAM ensures  stable and smooth convergence, particularly in the early training phases.

8

Kullampalayam Chinnasami R et al. (2025). Not Bot Horti Agrobo 53(4):14822

Color mapping  Colour mapping is a process that uses colours to assign values to images. Colour mapping delivers a  simple method for attaining complex colour variations in rice field images by permitting the colour palette and  other characteristics of an image to be changed through another image as a reference. In this study, the  segmentation mask was overlaid on the original UAV image for better visualisation of weeds through colour  mapping, as illustrated in Figure 7. Colour-map visualisation is typically used to highlight variations in intensity  or texture.


> **Figure 7.**

> Figure 7.
Figure 7.
Figure 7. Visualisation of detected weeds, demonstrating the effectiveness of YOLO11-PSPNet in 
identifying weed regions, showing variations through a colour map 
The red and yellow regions indicate higher feature intensities, and the blue and green regions signify lower intensities 
 
Training configuration and experimental setup 
The YOLOv11-PSPNet model was trained using the preprocessed UAV dataset with 70% training, 
20% testing, and 10% validation splits. During the training process, we employed various data augmentation 
transformations, such as flipping, colour adjustment, rotation, and scaling, to prevent overfitting and ensure 
generalisation. The proposed model uses several hyperparameters to balance the model performance and 
computational efficiency, as illustrated in Table 1.


> **Table 1.**

> Table 1.
Table 1.
Table 1. Hyperparameters used for the YOLO11-PSPNet framework  
Hyperparameter
Hyperparameter
Hyperparameter
Hyperparameter 
Definition
Definition
Definition
Definition 
Values
Values
Values
Values 
YOLO11-s
Learning rate 
Controls the step size for updating model weights during training. 
0.001 
Batch size 
Number of training samples processed before the model's weights are updated. 
16 
Momentum 
Stabilize gradient updates. 
0.937 
Weight decay 
Controls the strength of the regularization technique to prevent overfitting 
0.0005 
Epochs
Total number of times the training dataset is passed through the model.
50

Optimizer  Minimize the loss function during training.  Stochastic Gradient

Descent  PSPNet  Segmentation  Backbone  ResNet-50  Pyramid pooling  module Captures contextual information at different spatial scales  Adaptive average

pool Pooling type Aggregate features in the pyramid pooling module Average pooling Loss function  Quantifies the difference between predicted segmentation masks and ground truth.  Cross-entropy loss

9

Kullampalayam Chinnasami R et al. (2025). Not Bot Horti Agrobo 53(4):14822

Evaluation metrics  The rice weed detection and segmentation performance were examined using metrics including the Dice  Similarity Coefficient (DSC), Intersection over Union (IoU), mean Average Precision (mAP), and mean IoU  (mIoU).

DSC: The DSC calculates the similarity between the segmented and ground-truth regions. The values  ranged from 0 to 1, and a higher value represented more accurate segmentation results. The DSC formulation  is expressed as follows:

 2 ∗!" #" + 2 ∗!" + #$  (4)

In equation (4), !" denotes the true positive, #" and #$ signify the false positive and false negative.  IoU: This metric evaluates the overlap between the segmented and ground truth areas. The IoU values  ranged from 0 to 1. The segmented and ground-truth regions are denoted by % and &' as represented in  equation (5).

()*  % ∩&'

(5)

% ∪&'

mAP: This is a measure of the object detection. To estimate the mAP, the Average Precision was  computed for all object classes. The mathematical representation of the mAP metric is given by Equation (6).

/

-."  1

$  ."

(6)




## Results

Results 
Results 
Results  
 
Performance analysis of the proposed model 
This section presents the performance metrics of the proposed model, as illustrated in Table 2. The 
proposed YOLO11-PSPNet model attained a precision of 99.4 % and a recall of 98.2 %. The model accurately 
detected weeds in the paddy field, with an mAP50 of 99.56 %, an IoU of 99.61 %, and a DSC score of 83.2 %. 
The proposed model accurately detected and segmented weeds in rice fields using YOLO11-s and PSPNet 
models. Figure 8 shows the loss curves of the proposed weed detection model. The model performance was 
evaluated through training and validation. The graph shows the model performance during training and 
validation. The loss graph records the value of learning from the data and decreases the error as it learns from 
the data.  Figure 9 illustrates the detection performance based on the IoU and the number of epochs. This graph 
in weed detection visually represents how the IoU metric evaluates predicted bounding boxes corresponding 
to the actual ground-truth boxes with respect to the changes as the model is trained through each epoch based 
on the trained dataset. This graph shows the pixel-level overlap accuracy between predicted masks and ground 
truth labels, reflecting segmentation quality in dense paddy vegetation


> **Table 2.**

> Table 2.
Table 2.
Table 2. Performance metrics of the proposed YOLO11-PSPNet framework

Metrics Metrics Metrics Metrics  Values Values Values Values  Precision (%) 99.4 Recall (%)  98.2  mAP50 99.56 mAP50-95  99.03  IoU (%)  99.61  mIoU (%)  98.27  DSC (%) 83.2

10

Kullampalayam Chinnasami R et al. (2025). Not Bot Horti Agrobo 53(4):14822


> **Figure 8.**

> Figure 8.
Figure 8.
Figure 8. Training and validation loss curves, showcasing model convergence and learning stability


> **Figure 9.**

> Figure 9.
Figure 9.
Figure 9. IoU performance evaluation of PSPNet segmentation across validation samples  
 
Performance analysis on weed detection 
The YOLO11-s model detected the weeds and generated bounding boxes that identified the weeds and 
paddy fields separately. This figure shows that the red boxes specify the paddy fields, and the blue boxes signify 
the weed-infested areas in the paddy fields, as demonstrated in Figure 10.

11

Kullampalayam Chinnasami R et al. (2025). Not Bot Horti Agrobo 53(4):14822


> **Figure 10.**

> Figure 10.
Figure 10.
Figure 10. Bounding boxes on the UAV high-resolution images, detecting weeds shown in blue colour 
bounding boxes for the sample three input images 
 
Performance analysis on weed segmentation 
The PSPNet segmentation model generates pixel-wise segmentation masks that accurately identify weed 
locations. The model detected weeds from the bounding boxes of YOLO11-s and then generated a segmented 
mask, as shown in Figure 11. This figure shows examples of weed images with annotation masks and PSPNet 
predictions. This analysis demonstrated that rice crop and weed coverage can be accurately predicted in rice 
paddy field weeds.


> **Figure 11.**

> Figure 11.
Figure 11.
Figure 11. Weed detection results: (a) four sample input images, (b) ground truth annotation masks, (c) 
the predictions of PSPNet for the input image

12

Kullampalayam Chinnasami R et al. (2025). Not Bot Horti Agrobo 53(4):14822

Analysis of the performance of RAdam optimiser with the SAM   Figure 12 illustrates the performance curve of the RAdam optimiser with the SAM. As shown in this  figure, the epochs are adjusted from large to small with the number of training iterations of the model. The  optimiser updates and calculates the network parameters that affect the model training and output to reach the  optimal value, thereby minimising the loss function. Thus, it is important to select an appropriate optimiser to  train the proposed model. The proposed RAdam optimiser with SAM had the best fitting effect, and the  fluctuation of the gradient descent curve was the most stable. Here, RAdam with SAM was used as the  optimiser when training the proposed model YOLO11-PSPNet. Table 3 compares the convergence behaviours  of various optimisers, including Adam, AdamW, and Adamax, with the proposed RAdam with SAM, based on  key performance metrics. The Epochs to convergence indicate how quickly each learning rate reaches a high  accuracy, with fewer epochs reflecting faster convergence. Loss variance represents the model’s fit on the  training and unseen data, with lower values indicating better performance and minimal overfitting. This  confirms its robustness, faster convergence, and higher efficiency. The results show that the proposed RAdam  with the SAM optimiser outperforms both the constant learning rate and step decay with a lower epoch to  convergence value of 50 and a lower loss variance value of 0.014.


> **Figure 12.**

> Figure 12.
Figure 12.
Figure 12. Impact of the proposed RAdam optimiser with SAM function on model performance  
 
Table 3.
Table 3.
Table 3.
Table 3. Convergence analysis of different optimisers 
Optimizer
Optimizer
Optimizer
Optimizer 
Precision (%)
Precision (%)
Precision (%)
Precision (%) 
Recall (%)
Recall (%)
Recall (%)
Recall (%) 
Epochs to Converge
Epochs to Converge
Epochs to Converge
Epochs to Converge 
Loss Variance
Loss Variance
Loss Variance
Loss Variance 
AdamW 
96.8 
95.3 
61 
0.023 
Adam 
97.2 
95.4 
57 
0.018 
Adamax
96.6
94.9
55
0.027
Proposed  
(RAdam + SAM) 
99.4 
98.2 
50 
0.014

Comparative analysis   Table 4 compares the existing weed detection approaches and the proposed model in terms of precision,  recall, and mAP50. The existing YOLOv3-tiny, YOLOv8n, and YOLO-CWD models achieved precisions of  87%, 96.5%, and 86.2%, respectively. In comparison, the proposed model achieved a precision of 99.4%, a recall  of 98.2%, and a mAP of 99.56%, demonstrating that the proposed YOLO11-PSPNet framework effectively  detects weeds in rice fields.

13

Kullampalayam Chinnasami R et al. (2025). Not Bot Horti Agrobo 53(4):14822


> **Table 4.**

> Table 4.
Table 4.
Table 4. Comparative analysis of weed detection performance between YOLO11-PSPNet and existing 
state-of-the-art approaches 
Ref
Ref
Ref
References
erences
erences
erences 
Methods
Methods
Methods
Methods 
Precision (%)
Precision (%)
Precision (%)
Precision (%) 
Recall (%)
Recall (%)
Recall (%)
Recall (%) 
mAP50
mAP50
mAP50
mAP50 
Farooque et al., 2023 
YOLOv3-tiny 
87 
75 
76.4 
Zhang et al., 2024a 
YOLOv8n 
96.5 
96.4 
98.2 
Ma et al., 2025 
YOLO-CWD 
86.2 
74.3 
75.1 
Proposed 
YOLO11-PSPNet 
99.4 
98.2 
99.56 
 
Table 5 compares the existing weed segmentation approaches and the proposed model in terms of 
mAP50 and IoU. The existing PIS-Net, SSU-Net, and F-YOLOv8n-Seg-CDA approaches achieved mAP50 
of 68.29%, 63.50%, and 98.4%, respectively. In comparison, the proposed model obtains a mAP value of 
99.56% and IoU of 99.61%. This highlights the proposed YOLO11-PSPNet framework efficiently segments 
weeds in rice fields.


> **Table 5.**

> Table 5.
Table 5.
Table 5. Weed segmentation performance between YOLO11-PSPNet and existing state-of-the-art 
approaches  
References
References
References
References 
Methods
Methods
Methods
Methods 
mAP50
mAP50
mAP50
mAP50 
IoU
IoU
IoU
IoU 
Chen et al., 2024 
PIS-Net 
68.29 
64.31 
Machidon et al., 2025 
SSU-Net 
63.50 
58.27 
Zhang et al., 2024 
F-YOLOv8n-Seg-CDA 
98.4 
96.4 
Proposed 
YOLO11-PSPNet 
99.56 
99.61 
 
Table 6 compares the inference time of the proposed model with that of existing approaches, including 
RMS-DETR (Guo et al., 2024), DWUNet (Habib et al., 2024), a single-stage DL model (Rai and Sun, 2024), 
and an improved UNet (Li et al., 2025). The existing approaches achieved inference times of 8.1, 8, 82.1, and 
55.9 ms per image, respectively. The proposed model achieved an inference time of 6.2 ms per image, 
demonstrating that the proposed YOLO11-PSPNet framework outperforms existing approaches.


> **Table 6.**

> Table 6.
Table 6.
Table 6. Inference time comparison per image between the proposed model and existing weed detection 
methods 
References
References
References
References 
Methods
Methods
Methods
Methods 
Inference time (ms)
Inference time (ms)
Inference time (ms)
Inference time (ms) 
Guo et al., 2024 
RMS-DETR
8.1
Habib et al., 2024 
DWUNet
8
Rai and Sun, 2024 
Single-stage DL model 
82.1 
Li et al., 2025 
Improved UNet
55.9
Proposed 
YOLO11-PSPNet 
6.2 
 
 
Discussion
Discussion
Discussion
Discussion 
 
The proposed YOLO11-PSPNet architecture effectively addresses the challenges of weed localisation 
in paddy fields by integrating block-wise detection with pixel-level segmentation. The model utilised UAV 
images for rice field weed detection to achieve fine-grained weed localisation in paddy fields. The proposed 
model addresses the limitations of existing approaches that rely on either detection or segmentation, enabling 
the precise identification of weed-infested regions through weed detection and segmentation for spraying 
applications. The YOLO11-s model demonstrated excellent capability to accurately detect weed-infested areas, 
whereas PSPNet provided fine-grained segmentation, enabling the separation of weed areas. Pixel-level 
segmentation enables precise mapping of weed distribution, which can be used to guide selective spraying 
tactics, reduce chemical inputs, and improve overall crop quality.

14

Kullampalayam Chinnasami R et al. (2025). Not Bot Horti Agrobo 53(4):14822

Additionally, the RAdam optimiser with SAM produced a training process that was both stable and  robust, leading to a more effective and dependable weed detection system. The system achieved a high mAP of  99.56% and an mIoU of 98.27% with an inference time of 6.2 ms, indicating the potential for real-time  deployment. The proposed YOLO11-PSPNet demonstrated significant improvements in the agricultural field  by achieving accurate weed localisation. The colour mapping method enhanced the interpretability of the  results for humans, facilitating accurate and targeted spraying. Existing works (Rai et al., 2024; Singh et al.,  2025) shows strong object detection performance but limited to precise mask generation of dense canopy  conditions. Segmentation approaches, U-Net++ and DeepLabV3+-based architectures perform segmentation  tasks but require higher compute resources. Compared to these approaches, proposed YOLOv11-PSPNet  sequential pipeline achieves both high mAP and high IoU while maintaining inference efficiency suitable for  UAV-based spraying. The proposed YOLO11-PSPNet was primarily developed to detect and segment weeds  in rice fields using UAV images for site-specific weed management. These two networks result in a more  efficient and lightweight design suitable for deployment on edge devices. The integrated YOLO11-PSPNet  model provides efficient real-time object detection and robust semantic segmentation in paddy fields. The  PSPNet components support YOLO11-s in challenging detection cases, such as small or partially occluded  objects. This contextual information helps to classify and localise objects more accurately in complex  environments. In our study, the primary weed species observed and annotated in the dataset included  Echinochloa, Cyperus difformis, and Echinochloa colona, as these are among the most widespread and  problematic weed types in rice fields in our study region. Although our training focused on these common  species, the proposed YOLO11-PSPNet was designed to learn general weed characteristics based on shape,  texture, and spatial patterns, enabling it to effectively detect other weed types that were not labelled during  training. In our trials, very few detection errors were observed when locating weeds. We reduced the  misclassification rates using advanced data augmentation processes and high-resolution UAV images. Future  work will focus on integrating these detection outputs with automated spraying and analysing the real-world  benefits. This ensures that the integration of advanced deep learning models and UAV technology provides a  comprehensive solution for precision weed management.


## Conclusion

Conclusion
Conclusion
Conclusion 
 
The proposed YOLO11-PSPNet intelligent weed detection system effectively utilises YOLO11-s and 
PSPNet for targeted fertiliser and herbicide spraying in precision agriculture. The approach enabled efficient 
weed localization and weed boundary extraction, resulting in highly accurate weed identification and mapping. 
This study contributes to precision agriculture by offering an automated weed detection and segmentation 
system that optimises herbicide use, reduces costs, and enhances crop health. The experimental results 
demonstrate that the proposed model outperforms existing approaches, with a precision and recall of 99.4% 
and 98.2%, respectively. The findings confirm that combining detection with targeted semantic segmentation 
can reduce processing overhead while maintaining high spatial accuracy. This ensures accurate weed detection 
at the early stages of crop growth. In the future, including multispectral UAV images across multiple growth 
stages and environmental conditions could expand weed classification by detecting variations in weeds and 
enhancing model robustness.

Authors’ Contributions  Authors’ Contributions  Authors’ Contributions  Authors’ Contributions     Conceptualization: R.C; Data curation: R.C, S.R; Formal analysis: R.C, V.M; Investigation: R.C, S.R;  Methodology: R.C, V.M; Project administration: R.C; Resources: S.R, V.M; Software: S.R; Supervision: V.M;

15

Kullampalayam Chinnasami R et al. (2025). Not Bot Horti Agrobo 53(4):14822

Validation: R.C; Visualization: S.R; Roles/Writing - original draft: R.C, S.R, V.M; and Writing - review &  editing: R.C, V.M.

All authors read and approved the final manuscript.

Availability of Data and Materials Availability of Data and Materials Availability of Data and Materials Availability of Data and Materials    https://universe.roboflow.com/jeho/weed-lkwvk/      Acknowledgements  Acknowledgements  Acknowledgements  Acknowledgements     This research received no specific grant from any funding agency in the public, commercial, or not-for- profit sectors

Conflict of Interests Conflict of Interests Conflict of Interests Conflict of Interests    The authors declare that there are no conflicts of interest related to this article.      References References References References    Ahmad A, Saraswat D, Aggarwal V, Etienne A, Hancock B (2021). Performance of deep learning models for classifying

and detecting common weeds in corn and soybean production systems. Computers and Electronics in  Agriculture 184:106081. https://doi.org/10.1016/j.compag.2021.106081   Ameena M, Deb A, Sethulakshmi VS, Sekhar L, Susha VS, Kalyani MSR, Umkhulzum F (2024). Weed ecology: Insights

for successful management strategies: A review. Agricultural Reviews. https://doi.org/10.18805/ag.R-2661   Chen H, Zhang Y, He C, Chen C, Zhang Y, Chen Z, … Qi L (2024). PIS-Net: Efficient weakly supervised instance

segmentation network based on annotated points for rice field weed identification. Smart Agricultural Technology  9:100557. https://doi.org/10.1016/j.atech.2024.100557   Chen Z, Cai Y, Liu Y, Liang Z, Chen H, Ma R, Qi L (2025a). Towards end-to-end rice row detection in paddy fields

exploiting two-pathway instance segmentation. Computers and Electronics in Agriculture 231:109963.  https://doi.org/10.1016/j.compag.2025.109963   Chen Z, Chen B, Huang Y, Zhou Z (2025b). GE-YOLO for weed detection in rice paddy fields. Applied

Sciences 15(5):2823. https://doi.org/10.3390/app15052823   Farooque AA, Hussain N, Schumann AW, Abbas F, Afzaal H, McKenzie-Gopsill A, Esau T, Zaman Q, Wang X (2023).

Field evaluation of a deep learning-based smart variable-rate sprayer for targeted application of  agrochemicals. Smart Agricultural Technology 3:100073. https://doi.org/10.1016/j.atech.2022.100073   Genze N, Ajekwe R, Güreli Z, Haselbeck F, Grieb M, Grimm DG (2022). Deep learning-based early weed segmentation

using motion blurred UAV images of sorghum fields. Computers and Electronics in Agriculture 202:107388.  https://doi.org/10.1016/j.compag.2022.107388     Guo Z, Cai D, Jin Z, Xu T, Yu F (2025). Research on unmanned aerial vehicle (UAV) rice field weed sensing image

segmentation method based on CNN-transformer. Computers and Electronics in Agriculture 229:109719.  https://doi.org/10.1016/j.compag.2024.109719   Guo Z, Cai D, Zhou Y, Xu T, Yu F (2024). Identifying rice field weeds from unmanned aerial vehicle remote sensing

imagery using deep learning. Plant Methods 20:105. https://doi.org/10.1186/s13007-024-01232-0   Habib M, Sekhra S, Tannouche A, Ounejjar Y (2024). New segmentation approach for effective weed management in

agriculture. Smart Agricultural Technology 8:100505. https://doi.org/10.1016/j.atech.2024.100505

16

Kullampalayam Chinnasami R et al. (2025). Not Bot Horti Agrobo 53(4):14822

Islam MD, Liu W, Izere P, Singh P, Yu C, Riggan B, Zhang K, Jhala AJ, Knezevic S, Ge Y, Pitla S (2025). Towards real-

time weed detection and segmentation with lightweight CNN models on edge devices. Computers and Electronics  in Agriculture 237:110600. https://doi.org/10.1016/j.compag.2025.110600   Li Y, Guo R, Li R, Ji R, Wu M, Chen D, Han C, Han R, Liu Y, Ruan, Y, Yang, J (2025). An improved U-net and attention

mechanism-based model for sugar beet and weed segmentation. Frontiers in Plant Science 15:1449514.  https://doi.org/10.3389/fpls.2024.1449514   Li Y, Guo Z, Sun Y, Chen X, Cao Y (2024). Weed Detection Algorithms in Rice Fields Based on Improved YOLOv10n.

Agriculture 14:2066. https://doi.org/10.3390/agriculture14112066   Ma C, Chi G, Ju X, Zhang J, Yan C (2025). YOLO-CWD: A novel model for crop and weed detection based on improved

YOLOv8. Crop Protection 192:107169. https://doi.org/10.1016/j.cropro.2025.107169   Machidon AL, Krašovec A, Pejović V, Machidon OM (2025). SqueezeSlimU-Net: An adaptive and efficient

segmentation architecture for real-time UAV weed detection. IEEE Journal of Selected Topics in Applied Earth  Observations and Remote Sensing 18:5749-5764. https://doi.org/10.1109/JSTARS.2025.3536175   Mao Y, Dang P, Zhang E, Tang C, Chen Y, Chen X (2024). Weed density evaluation using KCCA-CFBLS based on

fusion of visual and tactile features in special paddy field environment. Computers and Electronics in Agriculture  217:108619. https://doi.org/10.1016/j.compag.2024.108619   Meesaragandla S, Jagtap MP, Khatri N, Madan H, Vadduri AA (2024). Herbicide spraying and weed identification using

drone technology in modern farms: A comprehensive review. Results in Engineering 21:101870.  https://doi.org/10.1016/j.rineng.2024.101870   Moazzam SI, Khan US, Qureshi WS, Nawaz T, Kunwar F (2023). Towards automated weed detection through two-stage

semantic segmentation of tobacco and weed pixels in aerial Imagery. Smart Agricultural Technology 4:100142.  https://doi.org/10.1016/j.atech.2022.100142   Murad NY, Mahmood T, Forkan ARM, Morshed A, Jayaraman PP, Siddiqui MS (2023). Weed detection using deep

learning: A systematic literature review. Sensors 23:3670. https://doi.org/10.3390/s23073670   Peng H, Li Z, Zhou Z, Shao Y (2022). Weed detection in paddy field using an improved RetinaNet network. Computers

and Electronics in Agriculture 199:107179. https://doi.org/10.1016/j.compag.2022.107179   Rai N, and Sun X (2024). WeedVision: A single-stage deep learning architecture to perform weed detection and

segmentation using drone-acquired images. Computers and Electronics in Agriculture 219:108792.  https://doi.org/10.1016/j.compag.2024.108792   Rai N, Zhang Y, Villamil M, Howatt K, Ostlie M, Sun X (2024). Agricultural weed identification in images and videos by

integrating optimized deep learning architecture on an edge computing technology. Computers and Electronics  in Agriculture 216:108442. https://doi.org/10.1016/j.compag.2023.108442   Rosle R, Che’Ya NN, Ang Y, Rahmat F, Wayayok A, Berahim Z, ... Omar MH (2021). Weed detection in rice fields using

remote sensing technique: A review. Applied sciences 11:10701. https://doi.org/10.3390/app112210701   Sharma A, Kumar V, Longchamps L (2024). Comparative performance of YOLOv8, YOLOv9, YOLOv10, YOLOv11

and Faster R-CNN models for detection of multiple weed species. Smart Agricultural Technology 9:100648.  https://doi.org/10.1016/j.atech.2024.100648   Singh P, Perez MA, Donald WN, Bao Y (2025). A comparative study of deep semantic segmentation and UAV-Based

multispectral imaging for enhanced roadside vegetation composition assessment. Remote Sensing 17:1991.  https://doi.org/10.3390/rs17121991   Xuan TD, Khanh TD and Minh TTN (2025). Implementation of conventional and smart weed management strategies

in  sustainable  agricultural  production.  Weed  Biology  and  Management  25:e70000.  https://doi.org/10.1111/wbm.70000   Yu F, Jin Z, Guo S, Guo Z, Zhang H, Xu T, Chen C (2022). Research on weed identification method in rice fields based

on UAV remote sensing. Frontiers in Plant Science 13:1037760. https://doi.org/10.3389/fpls.2022.1037760   Zhang D, Lu R, Guo Z, Yang Z, Wang S, Hu X (2024a). Algorithm for locating apical meristematic tissue of weeds based

on YOLO instance segmentation. Agronomy 14:2121. https://doi.org/10.3390/agronomy14092121   Zhang J, Yu F, Zhang Q, Wang M, Yu J, Tan Y (2024b). Advancements of UAV and deep learning technologies for weed

management in Farmland. Agronomy 14:494. https://doi.org/10.3390/agronomy14030494

17

Kullampalayam Chinnasami R et al. (2025). Not Bot Horti Agrobo 53(4):14822

The journal offers free, immediate, and unrestricted access to peer-reviewed research and scholarly work. Users  are allowed to read, download, copy, distribute, print, search, or link to the full texts of the articles, or use them  for any other lawful purpose, without asking prior permission from the publisher or the author. License  License  License  License - Articles published in Notulae Botanicae Horti Agrobotanici Cluj Notulae Botanicae Horti Agrobotanici Cluj Notulae Botanicae Horti Agrobotanici Cluj Notulae Botanicae Horti Agrobotanici Cluj-Napoca Napoca Napoca Napoca are Open-Access,  distributed under the terms and conditions of the Creative Commons Attribution (CC BY 4.0) License.  © Articles by the authors; Licensee UASVM and SHST, Cluj-Napoca, Romania. The journal allows the  author(s) to hold the copyright/to retain publishing rights without restriction.

Notes: Notes: Notes: Notes:    Material disclaimer: The authors are fully responsible for their work and they hold sole responsibility for the articles published  in the journal.     Maps and affiliations: The publisher stay neutral with regard to jurisdictional claims in published maps and institutional  affiliations.    Responsibilities: The editors, editorial board and publisher do not assume any responsibility for the article’s contents and for  the authors’ views expressed in their contributions. The statements and opinions published represent the views of the authors  or persons to whom they are credited. Publication of research information does not constitute a recommendation or  endorsement of products involved.

18
