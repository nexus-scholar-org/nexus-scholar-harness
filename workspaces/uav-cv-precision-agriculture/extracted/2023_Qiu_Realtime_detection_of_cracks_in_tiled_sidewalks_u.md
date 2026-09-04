---
workspace_id: SCI-000416
doi: 10.1016/j.autcon.2023.104745
title: Real-time detection of cracks in tiled sidewalks using YOLO-based method applied
  to unmanned aerial vehicle (UAV) images
authors:
- family_name: Qiu
  given_name: Qiwen
  orcid: null
- family_name: Lau
  given_name: Denvid
  orcid: null
year: 2023
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:21:25.097460+00:00'
---

# Real-time detection of cracks in tiled sidewalks using YOLO-based method applied to unmanned aerial vehicle (UAV) images

Automation in Construction 147 (2023) 104745

Contents lists available at ScienceDirect

Automation in Construction

journal homepage: www.elsevier.com/locate/autcon

Real-time detection of cracks in tiled sidewalks using YOLO-based method  applied to unmanned aerial vehicle (UAV) images

Qiwen Qiu a,*, Denvid Lau b

a School of Architecture and Civil Engineering, Huizhou University, Guangdong Province, China  b Department of Architecture and Civil Engineering, City University of Hong Kong, Hong Kong, China

A R T I C L E I N F O

A B S T R A C T

Keywords:  Crack detection  Tiled sidewalk  Deep learning  YOLO  Computer vision  Unmanned aerial vehicle

The conventional method of manually verifying the quality of tiled sidewalks is laborious, because of the time-  consuming identification of cracks from numerous grid-like elements of tiles. In this paper, the integration of You  Only Look Once (YOLO) into an unmanned aerial vehicle (UAV) is proposed to achieve real-time crack detection  in tiled sidewalks. Different network architectures of YOLOv2‑tiny, Darknet19-based YOLOv2, ResNet50-based  YOLOv2, YOLOv3, and YOLOv4‑tiny are reframed and compared to get better accuracy and speed of detection.  The results show that ResNet50-based YOLOv2 and YOLOv4‑tiny offer excellent accuracy (94.54% and 91.74%,  respectively), fast speed (71.71 fps and 108.93 fps, respectively), and remarkable ability in detecting small  cracks. Besides, they demonstrate excellent adaptability to environmental conditions such as shadows, rain, and  motion-induced blurriness. From the assessment, the appropriate altitude and scanning area for the YOLO-UAV-  based platform are suggested to achieve remote, reliable, and rapid crack detection.


## 1. Introduction

of road pavements, visual inspection via direct line-of-sight viewing is  the most typical traditional method used by many researchers and en­ gineering professionals worldwide [7]. Nevertheless, this method for  detecting cracks in tiled sidewalks relies on the interpretation of humans  and may have subjective errors in the field test as tiled sidewalks  generally feature countless block elements, diverse material types,  various surface textures, and crack discontinuities [8,9]. Human errors  can be reduced by adopting computational techniques such as edge  detection [10], wavelet transform [11], and other imaging-based  filtering algorithms (e.g., the Gabor function) [12]. Nevertheless, these  methods are laborious as they involve time-consuming manual proced­ ures for background removal and noise reduction under complex illu­ minance [13–15]. Moreover, the presence of numerous boundary  grooves around each tiled block might result in similar crack patterns,  which might increase the probability of false-positive predictions.  Identifying and learning cracks on images precisely and rapidly remain  challenging.

In most urban areas, tiled pavement blocks are widely constructed on  sidewalk street or vehicle road, playing important roles in traffic ser­ vices, economic development as well as aesthetic nourishment. Tiled  sidewalks are frequently exposed to service loading while deteriorating  over time owing to foundation settlement, overloads, temperature dif­ ferentials, or the combined effect of these factors. The premature frac­ ture of a tiled block evolves with the rapid growth of cracks due to the  fragility of the pavement material. Compared with cracks on a concrete  surface, the occurrence of cracking in tiled sidewalk can pose more  serious failure, damage, or breakage to the surface. Cracks in tiled  sidewalks tend to cause ponded water on roads, obstacles to pedestrian  activities in particular for those of blind persons, and declined brake  capacity of vehicles. Current societal concerns regarding pavement in­ spection and management necessitate effective technological tools that  can ascertain the damage location such that appropriate road mainte­ nance and/or rehabilitation activities can be implemented promptly.

A promising solution for road inspection, which features high  adaptability to real-world situations, object detection automation, and a  high level of intelligence, is the use of deep learning algorithms. Based  on neural network architectures, deep learning algorithms can simulate  the human cognition capability to identify feature representations from

Conventional inspection methods based on electromagnetic radia­ tion or stress wave propagation for the diagnosis of structural and  construction defects (e.g., pavement cracks) have been investigated  extensively [1–6]. Among the activities performed to verify the quality

* Corresponding author.  E-mail address: qwqiu3-c@hzu.edu.cn (Q. Qiu).

https://doi.org/10.1016/j.autcon.2023.104745  Received 24 May 2022; Received in revised form 2 January 2023; Accepted 4 January 2023

Available online 9 January 2023 0926-5805/© 2023 Elsevier B.V. All rights reserved.

Q. Qiu and D. Lau

Automation in Construction 147 (2023) 104745

unstructured/unlabeled data. The application of deep learning in  pattern recognition, object detection, segmentation tasks, surveillance,  and many other domains has intensified [16]. Researchers have recently  reported the feasibility of deep learning methods for the damage eval­ uation of buildings or construction structures [17–19]. Moreover, deep  learning can offer considerable information and recommendations to  road pathologists, urban management professionals, and research  groups engaged in optimizing pavement crack detection [20–22].

characteristic, the ResNet-based YOLOv2 is expected to enhance feature  expression and thus enable the detection of small objects (e.g., cracks in  tiled sidewalks). More recently, state-of-the-art YOLO versions, namely,  YOLOv3, YOLOv4, and the modified versions of YOLOv5, have been  developed [30]. These detectors offer a faster and more accurate object  detection.

Many state-of-the-art machine learning methods for crack detection  of concrete or asphalt pavement have been reported recently [31–37],  but they may not be suitable for tiled sidewalks featuring numerous grid  elements in the pavement blocks. The features of a tiled sidewalk require  a real-time classification process and sufficient precision to distinguish  cracks in the pavement context. As a promising deep learning method,  YOLO offers a viable solution to real-world recognition problems like  pavement crack detection. However, the efficacy of YOLO in detecting  tiled sidewalks in real-time practice has not been investigated suffi­ ciently. In recent years, YOLO has been integrated with mobile UAVs for  autonomous vision-based navigation [38,39]. The UAV platform allows  cracks to be detected remotely owing to its high mobility, but its oper­ ation with deep CNNs encounters a few issues that must be addressed.  First, YOLO may not effectively detect small cracks in tiled blocks from  the UAV imagery. The presence of numerous boundary grooves around  tiled blocks might result in similar crack patterns, which will likely in­ crease the number of false-positive predictions. In addition, the surface  context, color, and shape of tiled sidewalk are much more complicated  and diverse than those of concrete and asphalt pavements. These char­ acteristics might affect the model's ability to appropriately identify new  or previously unseen tiled pavement scenarios. Moreover, the perfor­ mance of the YOLO-based UAV in encoding the contextual information  of cracks can be affected by illumination condition, aircraft oscillation,  and weather. Meanwhile, the speed of different YOLO detectors selected  for testing sequential media (i.e., video frames) must be verified. These  issues have motivated researchers to construct suitable YOLO detectors  that provide a tradeoff between accuracy and speed, excellent adapt­ ability to complicated environmental conditions, and enhanced capacity  for feature extraction of small cracks.

A predominant reason for using machine learning which gains huge  amount of traction in object detection, is the recent renaissance of  convolutional neural networks (CNNs) in image classification. Inspired  by the animal visual cortex, CNNs can extract the grid-like topology of  images using the restricted region of a receptive field [23]. CNNs used in  image recognition and classification typically comprise a feature  extractor and a classifier. With the aid of CNNs, previous researchers  have come up with the sliding window in an image to locate an object.  As the spatial locations and aspect ratios of objects may differ, deter­ mining the target usually requires dense sampling with sliding windows  of various sizes, which incurs a tremendous computational cost. Hence,  a two-stage region-based CNN (R-CNN) has been proposed [24]. In the  R-CNN, the region proposals for determining where the object lies are  first recommended by the selective search algorithm. After this pro­ cedure, the network computes the convolutional features for classifica­ tion. Linear regression of bounding box offset is then implemented to  provide an optimal location prediction for the classified region. How­ ever, R-CNN is computationally expensive due to the multi-staged  training sessions involved (i.e., region proposal, convolution, classifi­ cation, and regression). To accelerate the process, region-of-interest  pooling has been applied to convert the region proposals into fixed-  shape feature maps before connecting them with fully connected  layers. This enables the convolution process to occur across the fixed  region proposals through an entire image, as mentioned in a paper  pertaining to fast R-CNN [25]. Nevertheless, fast R-CNN still requires a  significant amount of time to propose a region based on selective search.  Later on researchers used a region proposal network (RPN) for training  and predicting rectangular region proposals (i.e., anchors) and unified  the RPN with the fast R-CNN framework to develop faster R-CNN [26].  In the platform of graphics processing unit (GPU), faster R-CNN clarifies  a much improvement in terms of the speed of object detection. Also,  faster R-CNN offers high accuracy in object detection because of the  improved quality of the region proposals produced by the RPN.

The original contributions of the present research are highlighted as  follows. YOLO-based deep learning method and its integration with a  UAV are proposed for the crack detection of tiled sidewalks. Tiled blocks  always contain numerous grid boundary elements, which can compli­ cate the classification of cracks. The present work strives to establish a  YOLO-UAV-based prototype that can figure out miniscule cracks  rapidly. To optimize this performance, we reframed the network ar­ chitecture in YOLOv2 and created YOLOv2‑tiny, Darknet19-based  YOLOv2, and ResNet50-based YOLOv2. YOLOv2‑tiny is a simplified  and lightweight detector intended for advancing real-time driving.  Compared with Darknet19-based YOLOv2, ResNet50-based YOLOv2  enhances the feature extraction of fine cracks in images via the residual  function of ResNet, which is used for learning deeper layers. Moreover,  we employed state-of-the-art versions of YOLOv3 and YOLOv4‑tiny and  then compared their performance with that of the modified YOLOv2  versions. The performance of these detectors was tuned by different  training options (e.g., epochs and number of training images). As  pavement inspection may not necessarily be performed under normal  conditions owing to existing environmental factors, the effects of  shadows, darkness, plant twigs, rain water, and motion blur on the  performance of crack detection are elucidated in this study. Based on the  research findings, the application of the YOLO algorithm for tracking the  pavement cracks from UAV imagery is assessed. Additionally, several  methods for performing simple, real-time, and robust crack detections of  tiled sidewalks via the YOLO-UAV-based platform are recommended.

Although faster R-CNN promotes real-time object detection to some  extent, it remains unfeasible for applications in a few embedded plat­ forms (e.g., car, UAV, and satellite) owing to its computationally heavy  region-based stage. To achieve real-time operation, the latest several  years have witnessed a cutting-edge object detector named You Only  Look Once (YOLO) which is much faster than prior detection frame­ works. In contrast to the faster R-CNN, YOLO applies a single neural  network in the entire detection pipeline. This detector regresses  bounding boxes and scores category probabilities directly from an entire  image in one inference [27]. It uses a fully end-to-end algorithm in the  tasks of classification and prediction, and is highly generalizable for  training and testing of new domains or unexpected inputs. Since the  original version of YOLO yields a relatively low mean average precision  (mAP), the scholars have improved the model and built up YOLOv2  [28]. Under the improvements in the aspects of batch normalization,  anchor box, multi-scale training, fine-grained training, etc., YOLOv2  demonstrates a wonderful speed-accuracy trade-off in object detection.  To train YOLOv2, Darknet19 is primarily adopted as the base-network  architecture for efficient feature extraction due to its effectiveness in  reducing the number of convolution operations. Researchers has also  attempted to cascade ResNet networks (a deep transfer learning model  with a residual function [29]) with YOLOv2, recently. ResNet series (e.g.  ResNet50, ResNet101) have been proposed to alleviate the vanishing  gradient problem; in fact, they significantly reduce the difficulty of  training in deeper layers of neural networks. Because of this


## 2. Fundamentals of YOLO detector

2.1. Basic principle of YOLO

The concept of YOLO is to realize an end-to-end training strategy via

2

Q. Qiu and D. Lau

Automation in Construction 147 (2023) 104745

Fig. 1. YOLOv2 detectors: (a) YOLOv2‑tiny, (b) Darknet19-based YOLOv2, and (c) ResNet50-based YOLOv2.

a single neural network as well as the global prediction of bounding  boxes and class probabilities in full images. The algorithm partitions an  initial image into a set of S × S grid cells. Each cell predicts B bounding  boxes and the corresponding scores of class probability if an object ap­ pears in that cell. Specifically, the model predicts five elements of the  bounding box, namely four coordinates x, y, w, and h (relative to the box  location and size), and a confidence score C. The confidence score C

encodes the class probability predicted in a grid cell and the fitting de­ gree of the predicted bounding box relative to the ground truth, as  expressed in Eq. (1).

pred (1)

C = P(Classi|Object )*Pr(Object)*IOUtruth

pred = A ∩B

A ∪B (2)

IOUtruth

3

Q. Qiu and D. Lau

Automation in Construction 147 (2023) 104745

Fig. 1. (continued).

Here, P(Classi|Object) is the conditional probability of a class. Pr  (Object) = 1 if the bounding box contains objects in the grid cell;  otherwise, Pr(Object) = 0. IOUpred

tion of the sum-squared error. The function considers the loss L in five  terms related to the localization, the membership to an object as fore­ ground versus background (scored by “objectness”), and the class  probability, as described in Eq. (3). The first two terms of the equation  refer to the losses for the coordinates and the size of the bounding boxes.  The third and fourth terms are responsible to estimate the confidence of  an object to be the foreground. Finally, the fifth term refers to the  classification of an object for each grid cell. If a bounding box shields an  object, then YOLO increases its loss of coordinate predictions.

truth is the intersection over union (IOU)  between two areas, i.e., the areas of the ground truth box (A) and the  predicted bounding box (B), as expressed in Eq. (2). To assign the  candidate boxes, a threshold beyond which the bounding box scores for  the class-specific confidence is specified. Additionally, non-max sup­ pression is used to eliminate redundant box predictions. When C cate­ gories of objects are detected, a tensor of dimensions in the output of the  YOLO model can be calculated as S ✕ S ✕ (5 ✕ B + C).

YOLO optimizes its detection system using the multi-part loss func­

4

Q. Qiu and D. Lau

Automation in Construction 147 (2023) 104745

functionality. Researchers have demonstrated that this feature extractor  yields high training accuracy and speed. Additionally, in YOLOv2, route  layers were added to the network to merge layers of high- and low-  resolution features. Hence, the fine-grained features were obtained.

∑ S×S

∑ B

∑ S×S

[

(xi −̂ xi)2 + (yi −̂ yi)2 ]

1obj ij

+ βcoord

L = βcoord

i=0

j=0

i=0

[

√ )2 ]


## 2 +

(̅̅̅̅

∑ S×S

(̅̅̅̅̅ wi √ −̅̅̅̅̅̂ wi √

∑ B

hi √

1obj ij

−̅̅̅̅̅̂ hi

)

×

+

To improve the performance of small crack detection, the YOLOv2  architecture was reframed by incorporating deeper networks. However,  training deep layers of neural networks generally results in gradient  dispersion, which is undesirable. To tackle this issue, learning residual  functions were employed to reformulate the layers from the input and  collect them simultaneously [29]. The learning residual functions pre­ serve the information of some of the input data without requiring  training via a neural network. This keeps the deep learning with a high  accuracy of detection. Compared with VGG-16, ResNet18, and Dar­ knet53, ResNet50 has been proved to achieve better results for a dataset  of crops, with an average accuracy of 99.81% [44]. In this work, a  pretrained ResNet50 model was adopted as the feature extractor in the  YOLOv2 network to form ResNet50-based YOLOv2 for the crack  detection of tiled sidewalks. After performing an empirical analysis, we  selected the “activation_36_relu” as the feature extraction layer to  replace the remaining layers in the ResNet50 model. This level is ex­ pected to encode sufficient image features without a significant loss in  spatial resolution. In addition, a route layer was created from “activa­ tion_32_relu” to “yolov2_Relu1” to concatenate high- and low-resolution  features. Consequently, the network architecture of ResNet50-based  YOLOv2 comprised 138 layers, as shown in Fig. 1(c).

j=0

i=0

∑ B

∑ B

∑ S×S

∑ S×S

1obj ij (Ci −̂ Ci)2 + noobj

1noobj ij (Ci −̂ Ci)2 +

1obj i

×

j=0

i=0

j=0

i=0

• ∑

(pi(c) −̂ pi(c) )2 (3)

c∈classes

obj represents that the i-th grid cell contains  part of an object; 1ij

In the equation above, 1i

obj refers to the j-th bounding box in charge of the  prediction towards i-th grid cell; xi, yi, wi and hi refer to the coordinates,  width, and height of bounding box for that grid cell i; Ci and pi(c) refer to  objectness and class possibility in the i-th grid cell, respectively; ̂xi, ̂yi, ̂

wi, ̂hi, ̂Ci, and ̂pi(c) represent the corresponding values of model pre­ diction; B represents the number of bounding boxes; βcoord represents the  weight of the coordinate loss; and noobj represents the weight of loss for  bounding boxes without objects.

2.2. YOLOv2 with simple networks, Darknet19 and ResNet50

Based on the preliminaries of YOLO, YOLOv2 was developed with  certain improvements (e.g., batch normalization and high resolution  classifier) [28]. YOLOv2 uses the anchor box mechanism (as proposed in  [26]) to enhance the precision of bounding box prediction. An anchor  box with a certain aspect ratio was optimized by k-means clustering of  the training dataset. In the k-means clustering process, the distance of  the IOU metric was applied to determine the degree of overlap between  two bounding boxes, as described in Eq. (4). Compared to the classical  Euclidean distance, the IOU distance can reduce the errors caused by the  difference in the box size. Hence, automated anchor boxes with high  precision and speed can be generated. YOLOv2 outperforms other  cutting-edge detection approaches such as the R-CNN and single shot  detector in terms of the tradeoff between accuracy and detection speed.  YOLOv2 has been reported to achieve a mAP of 76.8% in the 2007 Visual  Object Classes Challenge (VOC2007).

2.3. YOLOv3

YOLOv3 is a single-shot deep learning algorithm, which is an  improved version of its predecessors. YOLOv3 employs Darknet-53 as  the backbone for feature extraction, which requires fewer floating-point  operations than ResNet101 or ResNet152 [30]. As such, the accuracy  and speed for object detection are further increased. Regarding the  classification, YOLOv3 uses logistic regression to predict the likeliness of  an object and the binary cross-entropy loss function to increase the  convergence of the category error [45]. Additionally, YOLOv3 actualizes  the strategy of multiscale fusion to predict objects at three different  spatial resolution scales. This is realized by using feature pyramid  network (FPN) which can merge the deep and shallow features of the  network. The up-sampling and cascading procedures maintain the fine-  grained feature, which enhances the fine target detection. Consequently,  the dimension of output tensor becomes S × S × (s*(4 + objn+C)) where  S × S indicates the grid dimensions, “s” the amount of predictions at  each scale, “4 + objn” the four bounding box offsets and the objectness  score of 1, and “C” the number of class predictions [46].

d(box, centroid) = 1 −IOU(box, centroid) (4)

In a training task, the network architecture of YOLOv2 is a CNN  structure that includes a series of convolutional, transform, and output  layers. The transform layer extracts activations from the last convolu­ tional layer and turns the raw feature into a form to improve the network  stability for object localization [40]. The output layer exploits the loss  function to train the network, generates the pixel coordinates of the box  and produces a confidence score of classified targets [41]. The number  of objects is represented by the number of predicted scores.

2.4. YOLOv4‑tiny

The network architectures of YOLOv2‑tiny and Darknet19-based  YOLOv2 are shown in Figs. 1(a) and (b), respectively. YOLOv2‑tiny  contains only 25 layers, among which seven are for convolution, six for  batch normalization, six for activation, three for Max Pooling, one for  image input, one for transformation, and one for detection output.  Particularly, the addition of batch normalization after each convolu­ tional layer can scale the activation to accelerate convergence and  reduce overfitting [42]. The fundamental structure of the feature  extraction layer is referred to as the DBL herein, which combines a  convolutional layer, a batch normalization and a leaky ReLU activation.  YOLOv2‑tiny contains fewer convolution layers, which is expected to  perform lightweight object detection. In Darknet19-based YOLOv2, the  feature extractor (i.e., Darknet19) provides feature representation by  circulating 3 × 3 convolutional layers with a plugged 1 × 1 convolu­ tional kernel [43]. Furthermore, Darknet19 applies a Max pooling layer  to reduce the data size, which leads to fewer operations required for  processing. In addition to this operation, a batch normalization layer  was used in Darknet19 to stabilize and streamline the training

YOLOv4 is an improved version of YOLOv3, which is constructed by  a Cross-Stage-Partial Darknet53 (CSP-Darknet53) as the backbone, a  spatial pyramid pooling (SPP) module, a path aggregation network  (PANet) and a YOLOv3 head [47]. Many bottom-up and top-down ag­ gregation paths are connected over the CSP-Darknet53 and SPP, which  can enrich the receptive field and separate out the most significant  contextual features. A PANet was used to manage different detector  levels to extract the features. Because YOLOv4 features complex  network structure and numerous network parameters, it requires a  powerful GPU computing source to achieve real-time object detection.  YOLOv4‑tiny, which is based on YOLOv4, features a simplified network  architecture and fewer parameters, thus rendering it more suitable for  application to mobile or driving devices such as UAVs. YOLOv4‑tiny  uses CSPDarknet53‑tiny as a backbone for lightweight object detection  and applies an FPN instead of SPP and a PANet to extract the feature  maps [47]. In addition, YOLOv4‑tiny offers only two-scale predictions  (26 × 26 and 13 × 13) instead of three-scale predictions in YOLOv4,  which further reduces the computational overhead. Moreover,

5

Q. Qiu and D. Lau

Automation in Construction 147 (2023) 104745

Fig. 2. Workflow for training YOLO detectors to perform crack detection of tiled sidewalks. Dataset creation, labeling, data augmentation, training and testing, data  output, and comparison of different YOLO detectors are presented.

YOLOv4‑tiny utilizes CBLblock and CSPBlock networks for feature  extraction. A complete IOU loss function is employed for regression of  bounding boxes.

2.5. Other YOLO versions

In the previous two years, researchers have developed new YOLO  versions, i.e., YOLOv5 and their modified models of TPH-YOLOv5 [48],  Transformer-YOLOv5 [49], and BCo-YOLOv5 [50]. Because these de­ tectors have not been widely applied for detecting different object cat­ egories such as persons, cars, and traffic lights, they are not used in the  present study. However, the authors plan to investigate these detectors  in future research studies.


## 3. Framework of machine learning

In this section, details of the training and testing of YOLO for pave­ ment crack detection are provided. Fig. 2 depicts the workflow of  training and testing in deep learning. All training was conducted by a  single GPU NVIDIA GeForce RTX 2080 Super with 8 GB of memory.  Through a cell phone camera, we captured a total of 1200 raw pavement  images, among which 1000 images were randomly stored in a training  dataset, whereas the remaining 200 images were collected as new im­ ages to be tested by the trained YOLO detectors. The images were  collected from cities in Hong Kong, Shenzhen and Huizhou. To train  YOLOv2 and YOLOv3, the images were resized to 448 × 448 pixels  before they were input to the network. YOLOv4‑tiny was trained with a  416× 416 image, as per a previous study [47]. During training, the  pavement cracks were manually annotated and labeled with rectangular  boxes, which were regarded as ground-truth boxes. Data augmentation  was performed to artificially enlarge the dataset of label-preserving  images, which increased the size of the training set by a factor of four.  The data augmentation involved a horizontal flip and an intensity  change of RGB channels to ensure that the object identity in each image  was invariant. Afterwards, the images and labeled data were combined  and input into the network architecture of YOLO for training based on  the following settings: initial learning rate, 0.001; mini-batch size, 20;  threshold, 0.5; and epochs 10 to 100. Stochastic gradient descent with  momentum was applied as an optimizer to enhance the performance of  YOLOv2 and YOLOv3 [51]. In addition, the Adam optimization algo­ rithm was used instead to train YOLOv4‑tiny. Based on the loss curve,  the training loss remained at a high level initially but declined signifi­ cantly thereafter. As recorded in this study, the eventual loss decreased

Fig. 3. Autonomous crack detection in different scenarios of tiled blocks by  Darknet19-based  YOLOv2,  ResNet50-based  YOLOv2,  YOLOv3,  and  YOLOv4‑tiny. All the YOLO detectors were trained by 4000 images at the  epochs of 90. A specific color is assigned to each type of YOLO detector (e.g.,  light blue for YOLOv4‑tiny). (For interpretation of the references to color in this  figure legend, the reader is referred to the web version of this article.)

to a magnitude of 0.01 when the iteration was performed 2000 times. In  the testing process, the specific location of a pavement crack was illus­ trated by a bounding box of the detectors. The crack detection perfor­ mance of the YOLO algorithms was compared in terms of accuracy and  speed.

6

Q. Qiu and D. Lau

Automation in Construction 147 (2023) 104745

Fig. 4. Comparison of YOLO detectors for crack detection of different scenarios of tiled blocks. YOLOv2‑tiny shows worse performance in classifying cracks and  distinguishing them from the surrounding grooves. Except for YOLOv2‑tiny, other YOLO detectors show robustness in identifying the fine-width cracks. YOLOv3 and  YOLOv4‑tiny outperform YOLOv2 in terms of confidence score prediction.


## 4. Results and discussion

designed to be light-weight for fast prediction. Nonetheless, it is subject  to an increase in false-positive predictions regarding grooves between  tiled blocks and false-negative predictions for small cracks. In addition,  YOLOv2‑tiny is less adaptable to pavement crack detection in blind  tracks. For most crack configurations in tiled sidewalks, the pre-trained  anchor box estimated from the training dataset has a length/width ratio  > 2. For the pavement scenario of a blind track, the specified texture and  roughness of the surface give a particular feature of crack configuration  or aspect ratio. Hence, the YOLO detectors generate bounding boxes  with reduced IOU values.

4.1. Crack detection of tiled sidewalks by YOLO

The trained YOLO detectors were applied for crack detection in tiled  sidewalks. The bounding box prediction is shown in Fig. 3. In general,  YOLO can identify, classify, and locate pavement cracks via rectangular  bounding boxes in different scenarios of tiled sidewalks. The aspect ratio  of the bounding box gives an indication of the crack length, which is  approximately the diagonal of the box. Additionally, the number of  cracks in an image can be estimated by the size of an array of confidence  scores, which are automatedly output and presented on top of the cor­ responding image. As another output parameter, the confidence score  from the YOLO detector is associated with the probability of objectness  and classification. Considering the characteristics above, we compared  the bounding box predictions of the detectors of YOLOv2‑tiny,  Darknet19-based YOLOv2, ResNet50-based YOLOv2, YOLOv3, and  YOLOv4‑tiny, and then distinguished the behaviors using colors (e.g.,  blue for Darknet19-based YOLOv2). As displayed in the figures, YOLOv2  exhibited a relatively lower confidence score than YOLOv3 and  YOLOv4‑tiny. The high confidence scores of YOLOv3 and YOLOv4‑tiny  (> 0.99) confirmed their robustness in classifying actual cracks.

4.2. Training factors

Accuracy is an important decision score for evaluating the quality of  deep learning models. It is typically defined in terms of four metrics, as  shown in Eq. (5):

Accuracy = TP + TN TP + TN + FP + FN (5)

where TP means true positive (number of correctly predicted crack  samples), FP means false positive (number of predictions where non-  crack objects are regarded as cracks), FN means false negative (num­ ber of undetected crack objects), and TN means true negative (number of  images without cracks and no prediction is performed). In addition, the  recall and the F1 score were adopted to evaluate the effectiveness of  constructed YOLO models used in detecting cracks. Recall denotes the  ratio of true-positive predictions to the total number of cracks observed,  as described in Eq. (6). This evaluation metric was used to detect how  sensitive the models identified the pavement cracks. F1 score represents  the harmonic mean of precision and recall, as expressed in Eqs. (7) and  (8). To assess reproducibility, we repeated the training of each type of  YOLO detector thrice and obtained the average metrics based on the test  results.

Occasionally, a machine learning-based method may yield the false-  positive results due to the influences of other objects with patterns  similar to the truth. In most tiled sidewalks, grooves around the tiled  blocks are likely to induce a “crack-like” fake feature, which results in  more mispredictions by YOLO. Hence, performing data augmentation on  the training image dataset is highly recommended. In addition, such  errors are primarily associated with the type of YOLO network used in  the detection. As illustrated in Fig. 4, except for YOLOv2‑tiny,  Darknet19-based YOLOv2, ResNet50-based YOLOv2, YOLOv3, and  YOLOv4‑tiny are capable of determining the large, medium, and fine  cracks and effectively separating them from the surrounding grooves.  Both YOLOv3 and YOLOv4‑tiny exhibited accurate predictions of the  bounding box for crack location and a high confidence score in the  classification task. Among these YOLO detectors, YOLOv2‑tiny is

Recall = TP TP + FN (6)

7

Q. Qiu and D. Lau

Automation in Construction 147 (2023) 104745

can be achieved. In this study, epochs 10–100 in the training were  investigated. To examine the effect yielded, the testing accuracy of >200  images was recorded, and the result is presented in Fig. 5 and listed in  Table 1. The error bands of accuracy for all the YOLO detectors were  generally <5%, which indicates high testing replicability. The accuracy  of pavement crack detection increased significantly as MaxEpochs  increased from 10 to 40. However, a further increase in MaxEpoch did  not yield much better detection performance yet extended the runtime.  Hence, the optimal MaxEpoch was determined to be 60–100 for  achieving accuracies exceeding 80% by Darknet19-based YOLOv2,  ResNet50-based  YOLOv2,  YOLOv3,  and  YOLOv4‑tiny.  For  YOLOv2‑tiny, the accuracy improved slightly after MaxEpochs was  increased, although the level remained <80% in general. ResNet50-  based YOLOv2 and YOLOv4‑tiny achieved higher accuracies (94.54%  and 91.74%, respectively) than YOLOv3 (88.57%). Additionally, the  article presents the recall and the F1 score for testing datasets, as shown  in Tables 2 and 3. Darknet19-based YOLOv2, ResNet50-based YOLOv2,  and YOLOv4‑tiny achieved values >90% for recall and F1-score. This  demonstrates the reliability of the above models to automatically detect  cracks from many different scenarios of pavement materials.

Fig. 5. Effect of MaxEpoch on crack detection accuracy of tiled sidewalks. The  accuracy was averaged with an error interval for each YOLO detector. Adjusting  MaxEpoch significantly affects the crack detection accuracy. To enhance the  crack detection performance of YOLO detectors, MaxEpochs should be at  least 40.

The reliability of autonomous object detection by a deep learning  method is very much dependent on the databank size of the training  images. During the training process, 800, 1600, 2400, 3200, and 4000  training images were created via data augmentation and input into the  deep learning network of YOLO. Fig. 6 displays the average accuracies of  five YOLO detectors trained by different numbers of images. In general,  the accuracy of pavement crack detection increased to a platform with  the number of training images. YOLOv2‑tiny presented a significant  improvement in accuracy, but the overall value was <80%. Darknet19-  based YOLOv2 and ResNet50-based YOLOv2 shown relatively high ac­ curacies in terms of crack detection, when the number of training images  was increased to 1600. Compared with YOLOv3, YOLOv4‑tiny indicated  better performance in terms of accuracy over the range of number of  training images. Based on this parametric evaluation, a minimum of  3200 training images are recommended for training a YOLO detector  such that it reliably detects cracks in tiled sidewalks.

Precision = TP TP + FP (7)

F1 score = 2* Precision*Recall

Recall + Precision (8)

An epoch refers to the total number of iterations through the entire  training dataset in one cycle and is critical to deep learning performance  [52]. Determining the number of MaxEpochs can provide information  regarding the maximum iterative epochs that enhance network perfor­ mance to a certain degree, although no further significant improvement


> **Table 1**

> Averaged accuracy and error of crack detection by five different YOLO detectors.

MaxEpoch  YOLOv2‑tiny  Darknet19-based YOLOv2  ResNet50-based YOLOv2  YOLOv3  YOLOv4‑tiny

Accuracy (%)  Error (%)  Accuracy (%)  Error (%)  Accuracy (%)  Error (%)  Accuracy (%)  Error (%)  Accuracy (%)  Error (%)

10  44.90  3.50  90.80  4.06  90.18  0.29  16.63  1.62  72.40  3.43  20  54.97  2.77  94.43  0.57  92.87  1.46  54.17  3.97  84.58  1.08  30  65.30  2.04  95.10  1.04  92.77  1.55  81.70  0.96  89.29  1.17  40  68.60  2.57  94.10  1.59  92.10  0.35  84.03  0.97  91.68  1.12  50  68.53  1.79  94.67  0.81  94.54  0.57  85.73  0.57  90.87  2.89  60  68.30  4.62  95.63  0.95  94.02  1.49  85.73  1.10  91.74  3.74  70  72.03  2.48  95.43  0.60  92.33  2.85  87.00  1.25  89.41  1.32  80  70.30  1.37  95.97  0.95  92.87  0.98  86.80  0.82  90.52  3.79  90  73.07  1.16  95.67  1.30  93.90  1.13  88.57  0.47  90.19  3.29  100  72.60  2.00  93.53  1.03  92.03  1.76  88.17  0.86  90.55  1.15


> **Table 2**

> Averaged recall and error of crack detection by five different YOLO detectors.

MaxEpoch  YOLOv2‑tiny  Darknet19-based YOLOv2  ResNet50-based YOLOv2  YOLOv3  YOLOv4‑tiny

Recall (%)  Error (%)  Recall (%)  Error (%)  Recall (%)  Error (%)  Recall (%)  Error (%)  Recall (%)  Error (%)

10  43.69  4.64  90.77  4.39  92.45  2.16  1.49  2.20  67.41  4.37  20  60.38  2.10  96.22  0.51  96.52  0.42  55.66  9.60  83.87  2.13  30  68.51  6.13  96.22  0.90  94.03  1.52  79.88  1.20  87.69  1.50  40  76.22  3.77  96.52  2.69  93.89  1.89  82.54  1.21  92.78  4.63  50  76.48  2.38  95.98  0.88  94.79  0.90  85.20  0.73  90.02  4.19  60  77.30  2.86  95.40  0.88  94.31  0.46  84.93  2.02  92.03  4.82  70  76.67  1.71  95.40  1.09  93.40  2.35  86.11  2.03  88.51  1.89  80  78.32  3.37  95.83  1.08  93.19  0.91  86.26  1.33  89.45  4.24  90  78.88  1.23  95.65  1.75  93.96  1.61  88.08  1.02  88.85  3.91  100  79.14  1.94  94.86  1.52  91.75  1.14  88.24  0.88  89.40  1.52

8

Q. Qiu and D. Lau

Automation in Construction 147 (2023) 104745


> **Table 3**

> Averaged F1 score and error of crack detection by five different YOLO detectors.

MaxEpoch  YOLOv2‑tiny  Darknet19-based YOLOv2  ResNet50-based YOLOv2  YOLOv3  YOLOv4‑tiny

F1 score (%)  Error (%)  F1 score (%)  Error (%)  F1 score (%)  Error (%)  F1 score (%)  Error (%)  F1 score (%)  Error (%)

10  54.23  4.14  94.24  2.68  93.66  0.70  2.87  4.23  80.41  3.03  20  66.06  2.63  96.64  0.34  95.68  0.94  64.62  4.91  90.14  0.82  30  75.27  2.26  97.07  0.62  95.56  1.01  87.94  0.74  93.29  0.77  40  78.22  2.18  96.46  1.02  95.69  1.05  89.62  0.69  94.46  0.81  50  78.02  1.07  96.81  0.51  96.25  1.01  90.84  0.41  94.57  2.18  60  78.02  3.48  97.36  0.59  96.21  0.81  90.82  0.80  94.89  2.42  70  80.80  1.94  97.24  0.38  95.72  1.27  91.73  0.85  93.39  0.92  80  79.60  0.90  97.58  0.59  95.54  0.37  91.60  0.56  94.11  2.47  90  81.65  0.87  97.41  0.81  96.10  0.63  92.78  0.32  93.85  2.15  100  81.27  1.57  96.13  0.56  95.13  1.08  92.49  0.61  94.11  0.74

induced blur. As shown in Fig. 7, the five YOLO detectors correctly  determined the location of cracks under the influence of tree shadows on  the ground. The confidence score is summarized in Table 4. Compared  with the result of testing for a normal case, the confidence score did not  reduce significantly. Also, crack detection was not significantly affected  by rainwater, even though ponded water can induce wet textural fea­ tures on the sidewalk surface and reduce the contrast between the  pavement block and crack. In addition, the motion-induced fuzziness in  the images did not result in errors in the bounding box prediction.  Nevertheless, the predicted confidence score decreased significantly  when the detectors were applied in darkness. Additionally, the existence  of plant twigs can introduce errors as they add false crack features to the  deep learning network. Compared with other YOLO detectors, YOLOv3  performed crack detection better in the presence of plant twigs. To  accommodate these environmental effects, the number of images for  training should be increased or a sufficient MaxEpoch value should be  defined.

4.4. YOLO-UAV-based crack detection

UAV has become the burgeoning robotic tool in a wide variety of  applications in tracking, mapping, surveillance, detection, and  surveying task due to its merits of high mobility, flexibility to different  view scopes, and most importantly high efficiency. The recent devel­ opment of real-time deep learning algorithms has enabled improve­ ments in methods for immediate decision-making in UAV platforms.  Combining a UAV with YOLO detectors allows real-time crack detection  along tiled sidewalks. However, crack detection based on this scheme  may encounter the issue during feature extraction from small cracks due  to a limited image resolution. In addition, UAVs operating at flight speed  may cause distortions or motion blur in the recorded video frames [53].  Although the findings above offer some indications of environmental  effects on crack detection in photographic images, it is still urgently  needed to examine the practical testing performance of YOLO-UAV-  based system. In the proposed prototype, the YOLO-UAV-based crack  detection scheme is composed of a quadrocopter, a control panel, a  camera, a GPU and a trained YOLO file. As shown in Fig. 8, the drone is  equipped with a video camera that offers an overhead view for the image  acquisition of tiled sidewalks. The onboard camera records and trans­ mits real-time video data via a wireless communication to the ground  computational station, i.e., the NVIDIA® GPU. The GPU code loads the  YOLO network for subsequent detection calls. Fig. 9 demonstrates an  example of crack detection in a sequence of video frames using the UAV  integrated with YOLOv4‑tiny. The predicted results can be stored in a  cloud center for the health assessment of tiled sidewalks at the final  stage.

Fig. 6. Accuracy of crack detection of tiled sidewalks by YOLO detectors with  different number of training images: (a) YOLOv2‑tiny, (b) Darknet19-based  YOLOv2, (c) ResNet50-based YOLOv2, (d) YOLOv3, and (e) YOLOv4‑tiny.

4.3. Environmental effects

Weather, sheltering conditions, and lighting environments are  considered to have influence on the semantic information provided by  photo images. These environmental effects can increase the un­ certainties in object detection performance when deep learning method  is used. In addition, fallen plant twigs on tiled sidewalks may introduce  pseudo information in the training images, which causes the detectors to  yield more false-positive predictions. It should also be recognized that  the image sequence from a UAV surveillance platform is more vulner­ able to blurry conditions caused by wind fluctuations, abrupt rolls, and  vibrations exerting on the camera of a flying UAV.

Using a manual control panel aided by a flight command, the UAV  was positioned at flying elevations of 0.5, 1.0, 2.0 and 3.0 m. The UAV  positioned at these heights can identify the sidewalk areas in the range  of 0.48, 1.32, 2.25, and 3.39 m2, respectively. Thus, the genericity of the  algorithms used for the UAV can be examined. Subsequently, the

To examine the adaptability of YOLO for automated crack detection  in various complex environments, we obtained a subset of test images  that included shadows, darkness, plant twigs, rain (water), and motion-

9

Q. Qiu and D. Lau

Automation in Construction 147 (2023) 104745

Fig. 7. Crack detection of tiled sidewalks using YOLOv2‑tiny, Darknet19-based YOLOv2, ResNet50-based YOLOv2, YOLOv3, and YOLOv4‑tiny under the influencing  factors of shadows, darkness, plant twigs, rain (water), and blur.


> **Table 4**

> Confidence score of crack detection by YOLO under different environmental scenarios.

Case  Detector

YOLOv2‑tiny  Darknet19-based YOLOv2  ResNet50-based YOLOv2  YOLOv3  YOLOv4‑tiny

Normal  0.73873  0.85219  0.88756  0.99993  0.99959  Shadow  0.68682  0.80584  0.91708  0.99694  0.99964  Darkness  0.68663  0.59921  /  0.68729  0.99643  Plant twig  FP  FP  FP  FP  FP  Rain  0.75123  0.86732  0.92986  0.99773  0.99944  Blur  0.75482  0.81458  0.89880  0.99978  0.99926

Note: / means not available.

balance between the view area and workability was determined to di­ agnose small cracks in the pavement. At the abovementioned flight  heights, targeted effort or manual flight control may be required to

avoid adverse effects on pedestrians. In this article, we suggest using a  drone equipped with a camera of higher definition and wider adjustable  view scope such that the vehicle can be elevated to a suitable level to

10

Q. Qiu and D. Lau

Automation in Construction 147 (2023) 104745

UAV

Camera Tiled sidewalks

Controller

CUDA® MEX

NVIDIA® GPU

YOLO detectors

Prediction

Cloud center

Video

Fig. 8. UAV-YOLO-based platform for crack detection of tiled sidewalks. The system consists of several modules, including a UAV equipped with a down-looking  camera, a manual control unit, wireless communication, a GPU (NVIDIA GeForce RTX 2080 Super with 8 GB of memory), a CUDA MEX platform, YOLO de­ tectors, and a cloud center for the data score.

YOLO-based system generates fewer predictions while generating  more false-positive results. Based on the results obtained, the recom­ mended flight height for implementing YOLO-UAV-based crack detec­ tion was 1–2 m. Regarding the models used in the proposed crack  detection scheme, YOLOv3 and YOLOv4‑tiny exhibited superior ca­ pacity to detect small objects due to the functionality of FPN adopted,  which provided rich semantics for multi-scale predictions. Additionally,  in ResNet50-based YOLOv2, the learning residual functions exerted in  ResNet50 enabled deeper extraction of crack features, and thus  rendering it a promising alternative to the model used in the YOLO-UAV-  based system for small crack detection.

The speed of object detection afforded by deep learning algorithm is  another important factor in the application of UAV surveys. In this  study, the detection speed was evaluated by an Intel(R) Core(TM) i9-  10980HK CPU, NVIDIA GeForce RTX 2080 Super with 8GB of mem­ ory, and a Windows 11 operating system with a 64-bit operating system.  We recorded the time elapsed during video processing for the five YOLO  detectors. Subsequently, based on the number of frames in the video, the  frame rates of crack detection were estimated, as listed in Table 5. The  results show that all the YOLO detectors achieved the speed baseline of  real-time video processing at 30 fps. YOLOv2‑tiny performed excep­ tionally fast in predictions (i.e., approximately 150 fps). Both ResNet50-  based YOLOv2 and YOLOv3 deal performed video processing at 70–80  fps, which is excellent for UAV operation. Meanwhile, YOLOv4‑tiny  achieved a speed of 108.93 fps, thus outperforming YOLOv3. The  measured values above support the selection of the YOLO detectors (i.e.  ResNet50-based YOLOv2, YOLOv3 and YOLOv4‑tiny) in the UAV for  real-time crack detection. In practice, the evaluated information can  serve as guidance for researchers/engineers intending to adopt an  appropriate algorithm in UAVs for pavement crack detection.

Fig. 9. Crack detection via UAV integrated with YOLOv4‑tiny.

facilitate road inspection.

ResNet50-based YOLOv2, YOLOv3 and YOLOv4‑tiny were favorable  and thus were embedded in UAVs at different flight elevations ranging  from 0.5 to 3 m to detect cracks in tiled sidewalks. The detector first  resized the input video frames to 224 × 224 pixels, before the subse­ quent prediction. As shown in Fig. 10, the three detectors effectively  identified the location of cracks in the video recorded from the UAV at a  height of 0.5 m. Increasing the altitude of the UAV lead to a larger view  of the pavement area, although it reduced the ability of the UAV in  predicting small cracks. When the altitude exceeded 2 m, the UAV-

4.5. Other discussion

As the YOLO detectors in UAV imagery can be executed for the rapid  detection of cracks in tiled sidewalks, they can reveal the scene where

11

Q. Qiu and D. Lau

Automation in Construction 147 (2023) 104745

Fig. 10. Practical crack detection in tiled sidewalks by YOLO-UAV-based method at different flight heights of 0.5, 1.0, 2.0, and 3.0 m. ResNet50-based YOLOv2,  YOLOv3, and YOLOv4‑tiny were applied as the models. A flight height of 1–2 m, which corresponds to a scanning area of 1.32–2.25 m2, can achieve better tradeoff  between accuracy and speed.

detection task. The main conclusions are as follows:


> **Table 5**

> Frames per second (fps) of different YOLO detectors implemented in 
UAV for pavement crack detection.

(1) YOLO presented robustness in the crack identification of tiled

sidewalks with numerous grid elements (typically in the form of  grooves) around pavement blocks. The pavement crack was  identifiable graphically by a generated boundary box with a  confidence score. The pixel coordinates of the bounding box  indicate the location and extent of the pavement crack. The score  represents the class probability of the crack and the fitting degree  of the bounding box. Especially, ResNet50-based YOLOv2,  YOLOv3 and YOLOv4‑tiny indicated high confidence scores for  small crack detection.   (2) Darknet19-based YOLOv2, ResNet50-based YOLOv2, and

YOLO detector  Frame rate (fps)

YOLOv2‑tiny  150.87  Darknet19-based YOLOv2  31.66  ResNet50-based YOLOv2  71.71  YOLOv3  77.82  YOLOv4‑tiny  108.93

the pavement cracks are annotated by multiple rectangular bounding  boxes on the ground. In fact, a rectangular bounding box cannot  represent a realistic configuration or shape of a crack, and it is difficult  to measure the resolution of the cracks. In this regard, the maximum  crack width cannot be precisely determined by YOLO models. Since the  rectangular bounding box provides information regarding the pixel co­ ordinates of a cracked object, it can be regarded as a boundary for image  refinement and used to facilitate crack segmentation. For instance, the  crack features within a bounding box at the block scale can be cropped  out and then input into fully convolutional networks (FCN) for pixel-  scale semantic segmentation. A hybrid YOLO-FCN-UAV-based system  for multi-scale crack detection may be developed. Moreover, integrating  CNNs into a UAV's on-board flight control can be considered to upgrade  intelligent operations, autonomous driving, and safety during the task of  crack detection.

YOLOv4‑tiny achieved values >90% for accuracy, recall and F1-  score. The indexes demonstrated these models' reliability to  detect cracks in many different species of tiled sidewalks.   (3) The accuracy of crack detection by YOLO network depended on

the number of epochs selected in the training interaction and the  quantity of training images. When YOLOv2, v3, and v4 were  applied, an overall accuracy of 80% can be achieved when at least  40 epochs and at least 3200 training images were input.   (4) Certain environmental variables should be considered to ensure

the reliability of pavement crack detection by YOLO. Shadows,  rain (water), and motion-induced blur had little effect on crack  identification using YOLO algorithms, whereas darkness and  plant twigs tend to increase the false-negative and false-positive  predictions, respectively.   (5) The architectural network of the feature extractor used in YOLO


## 5. Conclusions

significantly affected the crack detection accuracy. YOLOv2‑tiny  outperformed all other detectors in the speed of detection.  However, when using YOLOv2‑tiny, the average accuracy was

The present article demonstrates the autonomous crack detection in  tiled sidewalks by using YOLO-based deep learning method and pro­ poses a prototype of YOLO-UAV-based system for implementing this

12

Q. Qiu and D. Lau

Automation in Construction 147 (2023) 104745

relatively low. YOLOv4‑tiny exhibited an accuracy of 91.74%  and a speed of 108.93 fps, which outperforms YOLOv3 for crack  detection. ResNet50-based YOLOv2 also shows excellent accu­ racy of 94.54% and high speed of 71.71 fps in the detection task.   (6) Real-time, autonomous, and remote pavement crack detection

Transportation Systems (ITSC 2013), 2013, pp. 2039–2044, https://doi.org/  10.1109/ITSC.2013.6728529.  [13] Q. Qiu, J.H.M. Lam, A.M.C. Tang, M.W.K. Leung, D. Lau, An innovative

tomographic technique integrated with acoustic-laser approach for detecting  defects in tree trunk, Comput. Electron. Agric. 156 (2019) 129–137, https://doi.  org/10.1016/j.compag.2018.11.017.  [14] P.W. Tse, G. Wang, Sub-surface defects detection of by using active thermography

across tiled sidewalks via a YOLO-UAV-based scheme was pro­ posed. Wireless communication was established between a UAV  and YOLO. To satisfy the practical requirements towards rapid  and precise road inspection, the use of ResNet50-based YOLOv2  and YOLOv4‑tiny is recommended for UAVs operated at an alti­ tude of 1–2 m (which corresponds to a scanning area of  1.32–2.25 m2).

and advanced image edge detection, in: 12th International Conference on Damage  Assessment of Structures vol. 842, 2017, 012029, https://doi.org/10.1088/1742-  6596/842/1/012029.  [15] F.-C. Chen, M.R. Jahanshahi, R.-T. Wu, C. Joffe, A texture-based video processing


## methodology using bayesian data fusion for autonomous crack detection on

metallic surfaces, Comput.-Aided Civil Infrastruct. Eng. 32 (2017) 271–287, 
https://doi.org/10.1111/mice.12256. 
[16] Y. LeCun, Y. Bengio, G. Hinton, Deep learning, Nature 521 (2015) 436–444,

https://doi.org/10.1038/nature14539.  [17] Y.-J. Cha, W. Choi, O. Büyük¨oztürk, Deep learning-based crack damage detection

Additionally, we recommend some methods to achieve higher speed  and reliability in crack detection, i.e., (a) enriching the imagery dataset  available for training, (b) validating crack detection in different  metropolitan areas worldwide, and (c) comprehensively investigating  UAV flight speed versus accuracy. Furthermore, the YOLO-based deep  learning method can be integrated with satellite imagery to improve  remote pavement inspection.

using convolutional neural networks, Comput.-Aided Civil Infrastruct. Eng. 32 (5)  (2017) 361–378, https://doi.org/10.1111/mice.12263.  [18] Y.-Z. Lin, Z.-H. Nie, H.-W. Ma, Structural damage detection with automatic feature-

extraction through deep learning, Comput.-Aided Civil Infrastruct. Eng. 37 (12)  (2017) 1025–1046, https://doi.org/10.1111/mice.12313.  [19] N. Wang, X. Zhao, P. Zhao, Y. Zhang, Z. Zou, J. Ou, Automatic damage detection of

historic masonry buildings based on mobile deep learning, Autom. Constr. 103  (2019) 53–66, https://doi.org/10.1016/j.autcon.2019.03.003.  [20] L. Zhang, F. Yang, Y.D. Zhang, Y.J. Zhu, IEEE International Conference on Image

Processing (ICIP). Road crack detection using deep convolutional neural network,  IEEE, Phoenix, AZ, USA, 2016, https://doi.org/10.1109/ICIP.2016.7533052.  [21] J. Liu, X. Yan, S. Lau, X. Wang, S. Luo, V.C.-S. Lee, L. Ding, Automated pavement

Declaration of Competing Interest

crack detection and segmentation based on two-step convolutional neural network,  Comput.-Aided Civil Infrastruct. Eng. 35 (11) (2020) 1291–1305, https://doi.org/  10.1111/mice.12622.  [22] J. Guan, X. Yang, L. Ding, X. Cheng, V.C.S. Lee, C. Jin, Automated pixel-level

The authors declare that they have no known competing financial  interests or personal relationships that could have appeared to influence  the work reported in this paper.

pavement distress detection based on stereo vision and deep learning, Autom.  Constr. 129 (2021), 103788, https://doi.org/10.1016/j.autcon.2021.103788.  [23] A. Krizhevsky, I. Sutskever, G.E. Hinton, Imagenet classification with deep

convolutional neural networks, Commun. ACM 60 (2017) 84–90, https://doi.org/  10.1145/3065386.  [24] R. Girshick, J. Donahue, T. Darrell, J. Malik, Rich feature hierarchies for accurate

Data availability

Data will be made available on request.

object detection and semantic segmentation, Proc. IEEE Conf. Comput. Vis. Pattern  Recognit. (2014) 580–587, https://doi.org/10.1109/CVPR.2014.81.  [25] R. Girshick, Fast R-CNN, 2015 IEEE International Conference on Computer Vision

Acknowledgements

(ICCV), 2015, pp. 1440–1448, https://doi.org/10.1109/ICCV.2015.169.  [26] S. Ren, K. He, R. Girshick, J. Sun, Faster R-CNN: towards real-time object detection

with region proposal networks, IEEE Trans. Pattern Anal. Mach. Intell. 28 (2015),  https://doi.org/10.1109/TPAMI.2016.2577031.  [27] J. Redmon, S. Divvala, R. Girshick, A. Farhadi, You only look once: unified, real-

This research received no external funding.


## References

time object detection, in: 2016 IEEE Conference on Computer Vision and Pattern  Recognition (CVPR), 2016, pp. 779–788, https://doi.org/10.1109/CVPR.2016.91.  [28] J. Redmon, A. Farhadi, YOLO9000: Better, Faster, Stronger, 2017 IEEE Conference

[1] M.E. Torbaghan, W. Li, N. Metje, M. Burrow, D.N. Chapman, C.D.F. Rogers,

on Computer Vision and Pattern Recognition (CVPR), 2017, pp. 7263–7271,  https://doi.org/10.1109/CVPR.2017.690.  [29] K. He, X. Zhang, S. Ren, J. Sun, Deep residual learning for image recognition, in:

Automated detection of cracks in roads using ground penetrating radar, J. Appl.  Geophys. 179 (2020), 104118, https://doi.org/10.1016/j.jappgeo.2020.104118.  [2] S. Yashiro, J. Takatsubo, N. Toyama, An NDT technique for composite structures

2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR), 2016,  pp. 770–778, https://doi.org/10.1109/CVPR.2016.90.  [30] J. Redmon, A. Farhadi, YOLOv3: An Incremental Improvement, arXiv preprint

using visualized lamb-wave propagation, Compos. Sci. Technol. 67 (2007)  3202–3208, https://doi.org/10.1016/j.compscitech.2007.04.006.  [3] D. Zhang, Q. Zou, H. Lin, X. Xu, L. He, R. Gui, Q. Li, Automatic pavement defect

(2018), https://doi.org/10.48550/arXiv.1804.02767 arXiv:1804.02767.  [31] B. Kim, S. Cho, Image-based concrete crack assessment using mask and region-

detection using 3D laser profiling technology, Autom. Constr. 96 (2018) 350–365,  https://doi.org/10.1016/j.autcon.2018.09.019.  [4] Q. Qiu, D. Lau, Defect detection of FRP-bonded civil structures under vehicle-

based convolutional neural network, Struct. Control. Health Monit. 26 (2019),  e2381, https://doi.org/10.1002/stc.2381.  [32] T. Chen, Z. Cai, X. Zhao, C. Chen, X. Liang, T. Zou, P. Wang, Pavement crack

induced airborne noise, Mech. Syst. Signal Process. 146 (2021), 106992, https://  doi.org/10.1016/j.ymssp.2020.106992.  [5] Q. Qiu, D. Lau, Measurement of structural vibration by using optic-electronic

detection and recognition using the architecture of segNet, J. Ind. Inf. Integr. 18  (2020), 100144, https://doi.org/10.1016/j.jii.2020.100144.  [33] E.A. Shamsabadi, C. Xu, A.S. Rao, T. Nguyen, T. Ngo, D. Dias-da-Costa, Vision

sensor, Measurement 117 (2018) 435–443, https://doi.org/10.1016/j.  measurement.2017.12.040.  [6] Q. Qiu, D. Lau, A novel approach for near-surface defect detection in FRP-bonded

transformer-based autonomous crack detection on asphalt and concrete surfaces,  Autom. Constr. 140 (2022), 104316, https://doi.org/10.1016/j.  autcon.2022.104316.  [34] R. Ali, J.H. Chuah, M.S. AbuTalip, N. Mokhtar, M. AliShoaib, Structural crack

concrete systems using laser reflection and acoustic-laser techniques, Constr. Build.  Mater. 141 (2017) 553–564, https://doi.org/10.1016/j.conbuildmat.2017.03.024.  [7] N. Kheradmandi, V. Mehranfar, A critical review and comparative study on image

detection using deep convolutional neural networks, Autom. Constr. 133 (2022),  103989, https://doi.org/10.1016/j.autcon.2021.103989.  [35] D. Kang, S.S. Benipal, D.L. Gopal, Y.-J. Cha, Hybrid pixel-level concrete crack

segmentation-based techniques for pavement crack detection, Constr. Build. Mater.  321 (2022), 126162, https://doi.org/10.1016/j.conbuildmat.2021.126162.  [8] Q. Qiu, D. Lau, Defect detection in FRP-bonded structural system via phase-based

segmentation and quantification across complex backgrounds using deep learning,  Autom. Constr. 118 (2020), 103291, https://doi.org/10.1016/j.  autcon.2020.103291.  [36] Q. Mei, M. Gül, M.R. Azim, Densely connected deep neural network considering

motion magnification technique, Struct. Control. Health Monit. 25 (12) (2018),  e2259, https://doi.org/10.1002/stc.2259.  [9] E. Protopapadakis, A. Voulodimos, A. Doulamis, N. Doulamis, T. Stathaki,

Automatic crack detection for tunnel inspection using deep learning and heuristic  image post-processing, Appl. Intell. 49 (2019) 2793–2806, https://doi.org/  10.1007/s10489-018-01396-y.  [10] I. Abdel-Qader, O. Abudayyeh, M.E. Kelly, Analysis of edge-detection techniques

connectivity of pixels for automatic crack detection, Autom. Constr. 110 (2020),  103018, https://doi.org/10.1016/j.autcon.2019.103018.  [37] J. Deng, A. Singh, Y. Zhou, Y. Lu, V.C.-S. Lee, Review on computer vision-based

crack detection and quantification methodologies for civil structures, Constr. Build.  Mater. 356 (2022), https://doi.org/10.1016/j.conbuildmat.2022.129238. Article  No. 129238.  [38] K. Boudjit, N. Ramzan, Human detection based on deep learning YOLO-v2 for real-

for crack identification in bridges, J. Comput. Civ. Eng. 17 (2003) 255–263,  https://doi.org/10.1061/(ASCE)0887-3801(2003)17:4(255).  [11] P. Subirats, J. Dumoulin, V. Legeay, D. Barba, Automation of Pavement Surface

Crack Detection Using the Continuous Wavelet Transform, 2006 International  Conference on Image Processing, United States, 2006, https://doi.org/10.1109/  ICIP.2006.313007.  [12] M. Salman, S. Mathavan, K. Kamal, M. Rahman, Pavement crack detection using

time UAV applications, J. Exp. Theor. Artif. Intell. (2021) 1–18, https://doi.org/  10.1080/0952813X.2021.1907793.  [39] J. Zhu, J. Zhong, T. Ma, X. Huang, W. Zhang, Y. Zhou, Pavement distress detection

using convolutional neural networks with images captured via UAV, Autom.

the Gabor filter, in: 16th International IEEE Conference on Intelligent

13

Q. Qiu and D. Lau

Automation in Construction 147 (2023) 104745

Constr. 133 (2022), https://doi.org/10.1016/j.autcon.2021.103991. Article No.  103991.  [40] S. Saponara, A. Elhanashi, A. Gagliardi, Real-time video fire/smoke detection

[47] A. Bochkovskiy, C.-Y. Wang, H.-Y.M. Liao, Yolov4: Optimal speed and accuracy of

object detection, arXiv preprint (2020), https://doi.org/10.48550/  arXiv.2004.10934 arXiv:2004.10934.  [48] X. Zhu, S. Lyu, X. Wang, Q. Zhao, TPH-YOLOv5: Improved YOLOv5 based on

based on CNN in antifire surveillance systems, J. Real-Time Image Proc. 18 (2021)  889–900, https://doi.org/10.1007/s11554-020-01044-0.  [41] J. Zhang, X. Yang, W. Li, S. Zhang, Y. Jia, Automatic detection of moisture damages

transformer prediction head for object detection on drone-captured scenarios, in:  Proceedings of the IEEE/CVF International Conference on Computer Vision (ICCV)  Workshops, 2021, pp. 2778–2788, https://doi.org/10.1109/  ICCVW54120.2021.00312.  [49] Y. Yu, J. Zhao, Q. Gong, C. Huang, G. Zheng, J. Ma, Real-Time underwater

in asphalt pavements from GPR data with deep CNN and IRS method, Autom.  Constr. 113 (2020), 103119, https://doi.org/10.1016/j.autcon.2020.103119.  [42] S. Ioffe, C. Szegedy, Batch Normalization: Accelerating deep network training by

reducing internal Covariate shift, in: Proceedings of the 32nd International  Conference on Machine Learning vol. 37, 2015, pp. 448–456, https://doi.org/  10.48550/arXiv.1502.03167.  [43] E. Soylu, R. Demir, Development and comparison of skin cancer diagnosis models,

maritime object detection in side-scan sonar images based on transformer-YOLOv5,  Remote Sens. 13 (2021) 3555, https://doi.org/10.3390/rs13183555.  [50] R. Yang, Y. Hu, Y. Yao, M. Gao, R. Liu, Fruit target detection based on BCo-YOLOv5

model, Mob. Inf. Syst. 2022 (2022) 8457173, https://doi.org/10.1155/2022/  8457173.  [51] I. Sutskever, J. Martens, G. Dahl, G. Hinton, On the importance of initialization and

European, J. Sci. Technol. 28 (2021) 1217–1221, https://doi.org/10.31590/  ejosat.1013910.  [44] Y.-Y. Zheng, J.-L. Kong, X.-B. Jin, X.-Y. Wang, T.-L. Su, M. Zuo, CropDeep: the crop

momentum in deep learning, in: Proceedings of the 30th International Conference  on Machine Learning 28, 2013, pp. 1139–1147. https://dl.acm.org/d  oi/10.5555/3042817.3043064#d4051809e1.  [52] J. Deng, Y. Lu, V.C.S. Lee, Concrete crack detection with handwriting script

vision dataset for deep-learning-based classification and detection in precision  agriculture, Sensors 19 (2019) 1058, https://doi.org/10.3390/s19051058.  [45] T. Yulin, S. Jin, G. Bian, Y. Zhang, Shipwreck target recognition in side-scan sonar

images by improved YOLOv3 model based on transfer learning, IEEE Access 8  (2020) 173450–173460, https://doi.org/10.1109/ACCESS.2020.3024813.  [46] B. Benjdira, T. Khursheed, A. Koubaa, A. Ammar, K. Ouni, Car detection using

interferences using faster region-based convolutional neural network, Comput.-  Aided Civil Infrastruct. Eng. 35 (2019) 373–388, https://doi.org/10.1111/  mice.12497.  [53] Y. Liu, J.K.W. Yeoh, D.K.H. Chua, Deep learning–based enhancement of motion

unmanned aerial vehicles: Comparison between faster R-CNN and YOLOv3, in:  2019 1st International Conference on Unmanned Vehicle Systems-Oman (UVS),  Muscat, Oman, 2019, https://doi.org/10.1109/UVS.2019.8658300.

blurred UAV Concrete Crack Images, J. Comput. Civ. Eng. 34 (2020) 04020028,  https://doi.org/10.1061/(ASCE)CP.1943-5487.0000907.

14
