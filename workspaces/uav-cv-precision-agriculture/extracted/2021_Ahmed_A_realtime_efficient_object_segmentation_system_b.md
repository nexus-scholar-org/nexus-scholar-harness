---
workspace_id: SCI-000274
doi: 10.1007/s11554-021-01166-z
title: A real-time efficient object segmentation system based on U-Net using aerial
  drone images
authors:
- family_name: Ahmed
  given_name: Imran
  orcid: null
- family_name: Ahmad
  given_name: Misbah
  orcid: null
- family_name: Jeon
  given_name: Gwanggil
  orcid: null
year: 2021
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:26:15.063130+00:00'
---

# A real-time efficient object segmentation system based on U-Net using aerial drone images

Journal of Real-Time Image Processing (2021) 18:1745–1758  https://doi.org/10.1007/s11554-021-01166-z

SPECIAL ISSUE PAPER

A real‑time efficient object segmentation system based on U‑Net  using aerial drone images

Imran Ahmed1 · Misbah Ahmad1 · Gwanggil Jeon2

Received: 29 April 2021 / Accepted: 23 August 2021 / Published online: 5 September 2021  © The Author(s), under exclusive licence to Springer-Verlag GmbH Germany, part of Springer Nature 2021


## Abstract

Real-time object detection and segmentation are considered as one of the fundamental but challenging problems in remote 
sensing and surveillance applications (including satellite and aerial). Consequently, it performs a crucial role in various 
management and monitoring applications and has received notable attention in recent years. This paper aims to present a 
real-time, efficient system in which a deep learning-based model U-Net is explored for multiple object segmentation in aerial 
drone images. We perform data augmentation and apply transfer learning to enhance the model efficiency. We experimented 
U-Net segmentation model with different base architectures, including VGG 16, ResNet-50, and MobileNet, and compare 
their performance. We also compare the results U-Net segmentation model with different base architectures and concludes 
that the U-Net (MobileNet) achieves good results. The experimental results demonstrate that data augmentation improves 
the model’s performance by achieving a segmentation accuracy of 92%, 93%, and 95% with base architectures VGG-16, 
ResNet-50, and MobileNet, respectively.

Keywords  Real-time · Satellite images · Deep leaning · Remote sensing · U-Net


## 1  Introduction

of remote sensing images and videos that have been chang- ing significantly in terms of spatial resolution, data quality,  and coverage of available areas, locations, and scenes.

Recent years witnessed dramatic advancement in modern  remote sensing technologies, including the development of  small, commercial, intelligent, and affordable satellites and  presently extensive availability of unmanned aerial vehicles  (UAVs). Remote sensing involves techniques of obtaining  information remotely (at a distance) utilizing high-resolution  optical devices (cameras or sensors). Conventionally, it has  been associated with satellites and unmanned aerial vehicles  with a collection of airborne sensors. However, development  in remote sensing technologies rapidly increased the number

Remote sensing images and videos can efficiently help  to control, monitor resources, and collect valuable infor- mation [1]. Efficient remote sensing techniques, increasing  developments, and advancements in technologies provide  excellent opportunities for the diversity of applications, like  urban management [2, 2–4], monitoring of land changes [5,  6], and [7] and monitoring of traffic [8], and [9]. Among  various applications, object detection and segmentation  from high-resolution images and videos have obtained more  consideration in the remote sensing community. However,  to classify, detect, and segment various objects in remote  sensing images efficiently are also a challenging problem  for researchers [10], because of various factors, including  camera heights, object appearance, different backgrounds,  and environmental conditions. Moreover, advancements in  sensor technology, spatial resolutions of satellite images,  and mobile services acceptance also increase demands for  real-time access to information. In general, image segmenta- tion is the process that allows a label to the pixels in an input  image or video frame so that pixels in the same region/ area  or object are correlated with the same class label. It helps to

*	 Gwanggil Jeon  	 gjeon@inu.ac.kr

Imran Ahmed  	 imran.ahmed@imsciences.edu.pk

Misbah Ahmad  	 misbahahmad4872@gmail.com

1	 Centre for Excellence in Information Technology,  IMSciences Peshawar, 1‑A, Sector E‑5, Phase VII,  Hayatabad, Peshawar, Pakistan

2	 Department of Embedded Systems Engineering, Incheon  National University, Incheon, Korea

Vol.:(0123456789) 1 3

1746 	 Journal of Real-Time Image Processing (2021) 18:1745–1758

•	 To compare the results of U-Net segmentation model  with different base architecture for aerial drone images  in terms of accuracy

determine whether a given aerial or satellite image or video  frame contains one or more objects belonging to the class  of interest and locates every predicted object’s position in  the image.

The work presented in the paper mainly consists of the fol- lowing sections: In Sect. 2, a review of different works used  for object detection in various remote sensing applications  is provided. Section 3, a summary of the dataset used for  the experimentation. In Sect. 4, we present a deep learning- based efficient real-time system for object detection using  aerial images. In Sect. 5, we elaborate on the testing and  performance evaluation results. Finally, in Sect. 6, we sum- marized the presented work with possible future directions.

Researchers have been developed various techniques for  the segmentation of different objects and regions in remote  sensing images and videos. The developed techniques have  been classified into different categories, such as traditional  feature-based and advanced deep learning-based segmenta- tion techniques [11]. Traditional feature-based techniques  [12, 13], initially learn different features (color, shape,  textual, edge, and background subtraction) of regions and  classify objects in remote sensing images and videos. These  techniques produce good results for the different remote  sensing applications, but they usually require a large number  of training images and may not identify or segment objects  whose characteristics or features are not present in the train- ing images. After the development of deep learning based  techniques, researchers have now utilized them in different  remote sensing applications to segment different objects and  regions. These developed and improved techniques signifi- cantly increased the overall segmentation accuracy for dif- ferent applications [14–19, 19–21].


## 2  Literature review

In this section, some of the recent techniques developed  for classification, detection and segmentation of different  objects have been briefly discussed. These techniques are  mainly categorized into conventional features/machine and  advance deep learning-based techniques.


### 2.1  Feature and machine learning‑based

techniques

Inspired by the successful results of the deep learning  models, in this work, we presented an efficient real-time  object segmentation system for remote sensing applica- tions. For object segmentation in aerial drone images, we  utilized U-Net, which is a deep learning based segmentation  model developed for biomedical image segmentation [22].  The overall system is based on two paths or sections. The  first path, also named as an encoder, is the contraction path  utilized to capture the context in the image, while the second  path, also named as the decoder, is the symmetric expanding  path applied to allow precise localization using transposed  convolutions. The overall work presented in the paper is as  follows: we first performed data augmentation to boost the  segmentation model’s performance. Then, we trained and  tested the model with Aerial Semantic Segmentation Drone  Dataset.1 Lastly, we experimented U-Net model with three  different base architectures, namely VGG-16, ResNet-50,  and MobileNet, and compare the experimentation and per- formance results. In general, the main objectives of the paper  are provided as follows:

In conventional feature-based techniques, researchers uti- lized various template-based approaches for detecting spe- cific objects/regions, e.g., roads having simplistic visual  appearance [23]. Zhang et al., [24] introduced a semi-auto- mated template matching system to monitor roads, using a  rectangular reference template model produced by entering a  seed point on a chosen road. Authors applied a spoke wheel  algorithm to get the road’s direction, the road’s width, and  the starting point of the road. Authors in [25] and [26] used  gray-scale images and applied morphological hit-or-miss  transform technique for building detection. Stankov et al.  presented supervised [25], and unsupervised [26] machine  learning systems that need a collection of source windows  for detection and segmentation of different roof colors in  aerial input images.

Liu et al. [27] proposed an algorithm utilizing a shape- based global minimization active contour design for extrac- tion of geo-spatial objects. Further, in [28], authors intro- duced a recognition method for an aircraft in high-resolution  satellite images. The method is based on a coarse-to-fine  shape prior-based approach; for aircraft, parametric shape  pattern features are minimized using principal component  analysis and kernel density function.

•	 To present an efficient real-time deep learning-based  object segmentation system for remote sensing applica- tions. •	 To explore, train and test the U-Net segmentation model  with different base architectures including VGG-16,  ResNet-50, and MobileNet using aerial drone images.

Martha et al. [29] proposed knowledge-based techniques  for detecting objects in remote sensing images. In [30],  authors utilized geometric information essential and exten- sively utilized to detect objects; it mainly encodes previous  1  https://​www.​tugraz.​at/​index.​php?​id=​22387.


## 1 3

1747 Journal of Real-Time Image Processing (2021) 18:1745–1758

data. [56], presented artificial intelligence based instance  segmentation model for aerial scenes. Marmanis et al. [57]  presented a semantic segmentation technique using ensem- ble convolution neural networks for aerial images. Authors  in [58] applied Segnet and U-Net deep learning-based tech- niques or building semantic segmentation from high-reso- lution aerial images. Marcu et al. [59] proposed a segmenta- tion technique for object detection in drone images.

knowledge using parametric generic or specific shape pat- terns. Researchers also used shadow information (context  knowledge) to identify buildings with different shapes using  high-resolution monocular images automatically [31]. They  developed the directional spatial connection among build- ings and their shadows via introducing a fuzzy landscape  generation method.

Some researchers also performed segmentation-based  techniques, such as Ming et al. [32] utilized mean shift  algorithm for multi-scale segmentation in remote sensing  images. Furthermore, authors in [33] presented a segmenta- tion technique to extract geographical information, like the  association of the object shape or spatial context in the clas- sification. These methods reduce the constraints of standard  pixel-based image classification techniques and have been  fortunately used in landslide mapping [34] and [35], land  cover and change detection [36].

Garg et al. [60] presented a U-Net-based method for land  use and land cover classification. In [61], authors applied  the U-Net model for building segmentation in aerial images.  Mou et al. [62] presented an instance segmentation tech- nique for vehicle detection using aerial images and videos.  In [63], authors used unmanned vehicle and U-Net segmen- tation model to extract rice lodging in aerial images. Anand  et al. [64], presented an IoT-assisted deep learning-based  framework for semantic segmentation in aerial imaginary. In  [65] authors used U-Net segmentation model for road extrac- tion in remote sensing images. Ahmad et al., [66] presented  a real time IoT enabled system for top view person detection  using Cascade-RCNN and transfer learning.

Besides the techniques discussed above, some researchers  also applied background subtraction like the Gaussian mix- ture model [37] and machine learning algorithms for detec- tion of objects in remote sensing images, Markov random  fields [38], random forest [39], texton forests [40], support  tensor machine [41], partial least squares classifier [42], and  logistic regression classifier [43]. Researchers also applied  artificial neural network-based techniques for various remote  sensing applications, e.g., ship detection [44], road detection  [45], and tree detection [46].

From the above brief literature review, it is concluded  that significant work has been done by researchers in recent  years. Researchers utilized various conventional features,  machine, and deep learning-based techniques, e.g., [67] and  [68] for different remote sensing applications. However, to  the best of our knowledge, mostly researchers’ work tar- geted detection, classification, and segmentation of specific  objects like the ship, vehicle, car, building, and tree, etc.  This work presented an efficient real-time system based on  U-Net for multiple object segmentation in aerial images.


### 2.2  Deep learning‑based techniques

Recently, with the advent of deep learning [47–49],  researchers now start utilizing deep learning and convolu- tional neural network-based techniques for remote sensing  applications. Like, authors in [44] presented a deep neural  network-based technique for detecting ships in space borne  optical images. Wang et al. [45], originated a neural dynamic  method using deep learning and a finite-state machine for  road extraction. Aptoula et al. [50] proposed a classifica- tion framework for remote sensing images using a combina- tion of Gabor filtering and a convolutional neural network.  Authors in [51] presented an improved fully convolutional  network-based system for detecting buildings in remote  sensing images. Authors in [52], introduced a deep neural  network-based architecture for UAV navigation in an indoor  environment. Jain et al. [53] also proposed a deep learn- ing approach for the detection of objects in aerial scenes  obtained by UAVs Researchers in [54] presented a convolu- tional neural network-based technique for automated object  detection in aerial images.


## 3  Aerial semantic segmentation drone

dataset

In this work, a publicly available benchmark dataset named  Aerial Semantic Segmentation Drone Dataset2 has been  used. This dataset mainly focuses on the understanding of  semantic information of urban areas/ scenes for improving  the security of the autonomous drone camera and land- ing systems. The recording contains images of more than  twenty houses obtained from a bird’s eye perspective at  the height of 5–30 m from the ground. To obtain images,  a high-resolution camera was utilized. The size of images  are 6000 × 4000 px (24 Mpx). The training set comprises  400 publicly available images, while the test set consists of  200 private images. The dataset also contains pixel accurate  annotation for the corresponding training and testing set.  The complexity of the dataset is restricted to twenty classes,

Along with deep learning-based detection and classifica- tion techniques, some researchers also utilized segmentation  techniques for remote sensing applications. In [55], authors  applied semantic segmentation model for earth observation


## 2  https://​www.​tugraz.​at/​index.​php?​id=​22387.


## 1 3

1748 	 Journal of Real-Time Image Processing (2021) 18:1745–1758


## 4  Efficient real‑time object segmentation

system for aerial drone images

This work introduces an efficient real-time deep learning- based automated object segmentation system for aerial  images. The general flow of the work is shown in Fig. 2.  The collected dataset is initially passed through the pre-pro- cessing step, in which image resizing, shuffling, and nor- malization are performed. Next, after pre-processing, data  augmentation is used to improve the diversity of the dataset  and the efficiency of the system. After pre-processing and  data augmentation, the images are divided into a training  and a testing set. The dataset has been splitted randomly  for training and testing, respectively. As described in Fig. 2,  the deep learning-based segmentation model is comprised  of two steps: the first stage comprises training base archi- tectures, including VGG-16, ResNet 50, and MobileNet for  object classification. We used the U-Net architecture for  object segmentation originally, developed for Biomedical  Image Segmentation [22]. The architecture includes two  paths, namely encoder, and decoder. We transfer the con- volution layer of the first step as the encoder part with the  help of transfer learning, as shown in Fig. 2, and then add  them with deconvolution layers as the decoder. After train- ing the model with the three different base architectures, we  use testing set to assess the performance of the segmenta- tion model for three different base architectures–the trained  model output segmentation map for each object in different  test images, and the output segmentation results are evalu- ated using a true label mask or ground truth. Lastly, the

Fig. 1   Sample images from aerial image dataset

including person, grass, tree, other vegetation, water, pool,  gravel, dirt, rocks, paved area, car, bicycle, dog, window,  door, wall, roof, fence, fence-pole, and obstacle. Some sam- ple images of the dataset are also shown in Fig. 1.

Fig. 2   An efficient real-time object segmentation system for aerial drone image. The overall system is based on a deep learning model, i.e.,  U-Net, with three different base architectures


## 1 3

1749 Journal of Real-Time Image Processing (2021) 18:1745–1758

Fig. 3   Different type of data  augmentation

shifted, flipped, and rotated as depicted in Fig. 3, enabling  the training of architectures or models on a considerably  larger number of images. This process utilizes the Keras  structure that augments the data in real-time while maintain- ing the network with batches.

common evaluation metrics are used for determining the  performance of the system.


### 4.1  Pre‑processing

To maintain consistency during training of the U-Net model  using pre-built base network architectures, pre-processing  is performed. As three different base architectures are  used, thus we resize images and the label mask images to  224 × 224 × 3 . Furthermore, image normalization is done to  maintain variation in image appearances, including bright- ness and contrast. Finally, the dataset is randomly shuffled  for training and testing purposes.


### 4.3  Base architectures

As discussed earlier that in this work, three different base  architectures are used for extraction of image context as  encoder part. The deep learning architectures comprise a  series of layers, particularly convolution, pooling, activation,  ReLu, and the fully connected layers also called the feature  layer. A brief detail of each model is provided as follows:


### 4.2  Data augmentation


### 4.3.1  VGG‑16

As discussed earlier, the dataset comprises 400 publicly  available training images and 200 private testing images. It  is a relatively small dataset for the training of deep learning  architectures. Thus, we apply data augmentation to retain  a reasonable number of images and avoid the over-fitting  problem by assuring enough in-variance and robustness of  the architecture. We used real-time data augmentation meth- ods to the training set, same as [22]. The aerial images are

The first architecture used as a base network is VGG-16  [69]. It is a convolution neural net architecture that is used  with the ImageNet dataset [70]. It is recognized to be one  of the best vision model architectures and used for various  classification tasks. VGG-16 centered on having convolu- tion layers of 3 × 3 filter with a stride one and constantly  utilized similar padding and max pool layer with a filter


## 1 3

1750 	 Journal of Real-Time Image Processing (2021) 18:1745–1758

Fig. 4   Visualization of the  VGG-16 architecture

Fig. 5   Visualization of the  ResNet-50 architecture

size of 2 × 2 and stride two instead of producing a high  number of hyper-parameter as shown in Fig. 4 (adopted  from [69]). It supports the order of convolution and max- pooling layers constantly during the entire architecture. It  has two fully connected layers at the end, accompanied by  a softmax layer for output classification. The 16 in VGG- 16 regards to the total 16 layers present in architecture  that have weights. This network is pretty large, with 138  million (approx) parameters.


### 4.4  MobileNet

MobileNet [72] is an effective and transferable convolu- tional neural network architecture that is utilized in vari- ous real-world applications. MobileNet proposes two new  global hyperparameters (width multiplier and resolution  multiplier) that enable developers to trade off accuracy or  latency rate and low size depending on their requirements.  It primarily uses depth-wise separable convolutions instead  of the conventional convolutions, which are utilized in ear- lier architectures to develop lighter models. All depth-wise  separable convolution layers are comprised of depth-wise  convolution and point-wise convolution layers. Estimating  depth-wise and point-wise convolutions as separate layers,  a MobileNet has a total of 28 layers. A regular MobileNet  has 4.2 million parameters that can be more decreased by  tuning the width multiplier in hyper-parameter appropriately.  The general architecture of MobileNet is shown in Fig. 6.


### 4.3.2  ResnNet‑50

ResNet-50 (Residual Network) is a convolutional neural  network having 50 deep layers and 26M parameters, intro- duced by Microsoft [71]. In ResNet-50, instead of learning  features, the model learns from residuals that are subtrac- tion of features learned from the layer’s inputs. ResNet  applied the skip connection to produce information across  layers. ResNet connects nth layer input directly to some  (n + x) th layer, enabling additional layers to be stacked and  establishing a deep network. It has 48 convolution layers  along with one max pool and one average pool layer. The  ResNet-50 architecture is given in Fig. 5.


### 4.5  U‑Net‑based segmentation model

In this work, we used the U-Net model for object segmen- tation in aerial images. It is introduced by [22], mainly  based on end-to-end fully convolutional networks. It


## 1 3

1751 Journal of Real-Time Image Processing (2021) 18:1745–1758

Fig. 6   Visualization of the MobileNet architecture

Fig. 7   Visualization of U-Net architecture (the encoder part shown at left side is replaced with three different base architectures) (right side  decoder)

simply contains convolutional layers instead of dense lay- ers; thus, it can accept arbitrary size images. The general  architecture shown in Fig. 7 (adopted from [22]) is mainly  classified into two main sections: encoder and decoder.  The first one is the encoder utilized to obtain the context in  the image consists of a conventional stack of convolutional  and max-pooling layers, while the decoder section is the  symmetric expanding path applied to allow precise locali- zation utilizing reversed or transposed convolutions. The  first section is also called the down-sampling path, which  applies different deep learning classification architecture  as backbone consists of four steps. Each step originally  utilizes two 3 × 3 convolution layers with batch normaliza- tion supported by 2 × 2 max-pooling layer, as determined  from Fig. 7. The horizontal bottleneck comprises two 3 × 3  convolution layers and 2 × 2 up-convolution layers. The  up-sampling path further has four stages, i.e., decoder

including two 3 × 3 convolutional layers supported by 2 × 2  up-sampling layer. At each step, features maps become  half.

It can be seen from Fig. 7 that to provide local and global  information during up-sampling, the architecture skips con- nections between up-sampling and down-sampling paths.  Lastly, at the output, the segmented map is provided by 1 × 1  convolutional layer, where the number of feature maps is the  same as the amount of desired segments.

It can be observed that the pre-processed 3-channel RGB  input images are given to the architecture for segmenta- tion. The input images’ shape is determined as (N, 3, H, W),  here the input images are represented with N, 3 represents  the number of channels, the height and width of the image  are described as H, and W. Over the final feature, map, the  energy function is determined as the cross-entropy loss cou- pled with pixel-wise soft-max [22]. It is described as:


## 1 3

1752 	 Journal of Real-Time Image Processing (2021) 18:1745–1758

fer learning technique is implemented for each archi- tecture. •	 At, testing phase, the testing set images are passed  through a trained segmentation model for object segmen- tation. Unlike other conventional methods, U-Net utilized  color information to assign label masks at the output to  the segmented objects. •	 The output is transformed into an RGB image. The seg- mented label of each object class pixel is matched with  its corresponding label mask information. According to  the color index value specified by the trained model, a  variable indicated as label color saves the color informa- tion for all specific object classes. For multiple objects,  different RGB values are saved and allotted by the color  variable. •	 Finally, at the output, segmented object or objects with  the assigned color value is obtained.

(1) pk(x) = exp(ak(x)) ∑K

.

k=1 exp(a

k(x))

In Eq. (1), activation in feature map, that is, rectified linear  unit (ReLu) is represented by ak . The total number of object  classes is denoted by K, and maximum function approxi- mation is described as pk(x) . pk(x) value is approximately  equal 1 for maximum activation ak(x) at the pixel position k.  For other values of it is considered as pk(x) ≈0 . The cross- entropy function is then penalized as at each location, [22]:

∑

(2) E =

log(pl(x)(x)).

w(x)휖Ω

In Eq. (2), true label of every pixel is described as  l ∶Ω →1, 2, ..., K . The weight map that provides extra atten- tion to pixels throughout training is given as w ∶Ω →IR  [22]. The true segmentation is pre-computed for various  frequency pixels. Using morphological operations in the  training dataset for some classes; the weight map is given as:


## 5  Experimental results

)

(

−(d1(x) + d2(x))2

(3) w(x) = wc(x) + wo.exp

.

This section elaborates on the training observation, testing,  visual, and evaluation results of the object segmentation sys- tem used for aerial images. The introduced system has been  implemented employing the python programming language  (Keras library) with OpenCV 3.6.

2휎2

Therefore, wc ∶Ω →IR denotes weight map applied for bal- ancing of class frequencies. The distance to first edge and  distance from second nearby edge is expressed with d1 and  d2 . The value of wo = 10 and 휎≈5 . (for further details, read- ers are referred to original work [22].)


### 5.1  Training and testing observation

This work introduced a real-time efficient object seg- mentation model based on U-Net architecture utilizing  well-known classification architectures as encoders (e.g.,  by leveraging architectures with training on aerial image  dataset). In this work, we implemented U-Net using three  different encoders: VGG-16, ResNet-50, and MobileNet.  In all cases, a “reflected” version of the encoder is applied  as the decoder. The details of the object segmentation sys- tem presented in Fig. 2 is presented as:

We firstly presented the training and testing observations of  segmentation model with three different base architectures  using the aerial image dataset. The training, testing loss,  and accuracy of the U-Net segmentation model with differ- ent base architectures are shown in Figs. 8 and 9. For each  base architecture, we performed training for 100 epochs. It is  noted that after the 10th epoch, the loss is reducing for both  training and testing, as determined in Fig. 8. The training  and testing loss VGG-16 is 0.5%, and 0.47%, ResNet-50 is  0.45%, and 0.4% and MobileNet is 0.35%, and 0.3%, respec- tively. Also, from Fig. 9, it can be noticed that training and  testing accuracy rates are significantly increased after the  first 20th epoch. The training and testing accuracy rate of  VGG-16 is 0.86, and 0.84, ResNet-50 is 0.87, and 0.9 and  MobileNet is 0.92, and 0.94, respectively.

•	 Three deep learning architectures, i.e., VGG-16, Res  net-50, and MobileNet, are used in this work, take a  high-resolution RGB image as input, normalized by  applying ImageNet mean and standard deviation pro- cess. Pre-processing is performed, and the image is  resized after normalization. •	 As discussed earlier, U-Net takes arbitrary-sized input  images and produces a similar sized segmented map  as output. Since the encoder is based on output strides,  thus down-sampling is performed for the given arbi- trary sized image. •	 A respective deconvolutional layer is generated for each  convolutional block at the decoder side, and a skip con- nection takes the features of the same size from the  encoder to the deconvolutional layer. Further, the trans-


### 5.2  Visualization results

The object segmentation model testing results are shown in  Figs. 10 and 11. It can be seen that the U-Net-based model  gives good results for multiple objects in aerial images. In  Figs. 10 and 11, the first column shows the original input  images; the second column shows the predicted output  image, while the third column shows the true label mask


## 1 3

1753 Journal of Real-Time Image Processing (2021) 18:1745–1758

Fig. 8   Training and testing loss  of U-Net with different base  architectures

Fig. 9   Training and Testing  Accuracy of U-Net with differ- ent base architectures

image. Due to space limitations, we have shown output  results for six test images. From the first row of Fig. 10, the  segmentation model efficiently segmented people, trees, and  ground in the image. In the second row of Fig. 10, the road  area is accurately segmented along with the different types  of trees and ground. The model also segmented the obscured  building effectively, as seen in the third row of Fig. 10.

are different sizes of trees that the model effectively seg- ments. Finally, in Fig. 11, in the third row, four people are  accurately segmented by the model.


### 5.3  Performance evaluation

The performance evaluation results of the system applied  for object segmentation in aerial images have been dis- cussed in this section. In addition, various evaluation  matrices are available for assessing and analyzing the  accuracy of segmentation systems [17]. We used different  evaluation parameters as shown in Fig. 12, where the red  rectangle describes predicted results, and the blue rectan- gle defines the ground truth or true results. According to

Same in the case of Fig. 11, the segmentation results of  the model are tested using different images. It can be seen  that images consider in Fig. 11 are captured from differ- ent heights, but the segmentation model output is almost  similar to the true label mask. In the first row of Fig. 11,  the person riding the bicycle is segmented along with few  plants and other objects. In the second row of Fig. 11, there


## 1 3

1754 	 Journal of Real-Time Image Processing (2021) 18:1745–1758

Fig. 10   Results of the segmentation model on different test images, the first column represents original images, the second presents predicted  segmentation map, and the third presents true label mask

prediction and ground truth results, each pixel image is  classified into four types that is true positive (TP), true  negative (TN), false positive (FP), and false negative (FN).

(6) F1−score = 2 × Prec × Rec

Prec + Rec .

•	 Pixel accuracy ( Pacc ): an extensively utilized evalua- tion metric for various segmentation techniques. It is  described as accuracy of pixel-wise prediction and pro- vided as:

Using different parameters shown in Fig. 12, various  evaluation matrices are utilized as follows;

•	 Recall Rec, Precision Prec and F1-score: These matri- ces are recognized as commonly utilized evaluation  matrices for several traditional image segmentation  methods defined as:

∑K

i=0(pii) ∑K

(7) Pacc =

.

∑K

j=0 .(pij)

i=0

In the above equation, K specifies the number of pixels  in the testing image, pii defined predicted pixels as class  i, and the true label is described as pij , that is the number  of pixels of object class i that is predicted as class j. •	 Intersection over union (IoU) IoU is identified as the  Jaccard Index, a generally utilized evaluation metric to  measure the performance of a segmentation system. It

(4) Rec = TP TP + FN,

(5) Prec = TP TP + FP,

While the F1-score is determined as the harmonic mean  between precision and recall value, calculated as;


## 1 3

1755 Journal of Real-Time Image Processing (2021) 18:1745–1758

Fig. 11   Segmentation model results on different test images captured from different camera heights; the first column represents original images,  the second presents predicted segmentation map, and the third presents true label mask

Fig. 12   Relationship between of TP, TN, FN, and FP

is commonly described as the ratio of intersection and  union area between the predicted segmentation map B  and true label masks A measured as:

Fig. 13   Evaluation results with different base architectures

(8) IoU = J(A, B) = |A ∩B|

|A ∪B|. to describe the segmentation systems’ performance. Its  value normally ranges between 1 and 0 presented as:

•	 Mean-IoU (mIoU) Another broadly utilized metric for  segmentation systems. It is defined as the average value  of IoU total label object classes k. It is usually utilized

k

tp ∑k

(9) mIoU = 1 k + 1

.

j=0 fn + ∑k

j=0 fp −fn

i=0


## 1 3

1756 	 Journal of Real-Time Image Processing (2021) 18:1745–1758


## References

Table 1   Pacc and mIoU with different base architectures

S. no Model name (%) Pacc (%) mIoU


## 1.	 Yang, C., Wong, D., Miao, Q., Yang, R.: Advanced geoinforma-

tion science. CRC Press, Boca Raton (2010) 	 2.	 Volpi, M., Tuia, D.: Dense semantic labeling of subdecimeter res-

1 U-Net (VGG-16) 88 82 2 U-Net (ResNet-50) 90 78 3 U-Net (MobileNet) 92 82

olution images with convolutional neural networks. IEEE Trans.  Geosci. Remote Sens. 55(2), 881 (2016) 	 3.	 Audebert, N., Saux, B. Le., Lefèvrey, S.: Fusion of heterogeneous

data in convolutional networks for urban semantic labeling. In:  2017 Joint Urban Remote Sensing Event (JURSE) (IEEE, 2017),  pp. 1–4 	 4.	 Mou, L., Zhu, X.X.: RiFCN: recurrent network in fully convo-

The performance evaluation results of the model are shown  in Fig. 13. It can be seen that the U-Net segmentation model  achieves good results with different base architectures. The  precision value of the U-Net segmentation model with VGG- 16 is 72%, ResNet-50 is 75%, and 78% with MobileNet. The  Recall value is 86%, 88% and 90% for VGG-16, ResNet-50  and MobileNet, respectively. The F1-score is also more than  80% for all base architecture. The accuracy of the segmen- tation model is high with MobileNet, i.e., 95%, while with  VGG-16 and ResNet-50, it is 92% and 93%, respectively.

lutional network for semantic segmentation of high resolution  remote sensing images. arXiv:​1805.​02091 (2018) 	 5.	 Vakalopoulou, M., Karantzalos, K., Komodakis, N., Paragios, N.:

Graph-based registration, change detection, and classification in  very high resolution multitemporal remote sensing data. IEEE J.  Sel. Top. Appl. Earth Observ. Remote Sens. 9(7), 2940 (2016) 	 6.	 Wu, C., Du, B., Cui, X., Zhang, L.: A post-classification change

detection method based on iterative slow feature analysis and  Bayesian soft fusion. Remote Sens. Environ. 199, 241 (2017) 	 7.	 Lyu, H., Lu, H., Mou, L.: Learning a transferable change rule

Furthermore, the pixel accuracy ( Pacc ) and mean-IoU  (mIoU) values for segmentation model with different base  architectures are shown in Table 1. The Pacc and mIoU of  U-Net with VGG-16 is 88%, and 82, with ResNet-50, it is  90%, and 78%, while with MobileNet it give bit good results  with Pacc and mIoU 92%, and 82%, respectively.

from a recurrent neural network for land cover change detection.  Remote Sens. 8(6), 506 (2016) 	 8.	 Mou, L., Zhu, X.X.: Spatiotemporal scene interpretation of space

videos via deep neural network and tracklet analysis. In: 2016  IEEE International Geoscience and Remote Sensing Symposium  (IGARSS) (IEEE, 2016), pp. 1823–1826 	 9.	 Kopsiaftis, G., Karantzalos, K.: Vehicle detection and traffic den-

sity monitoring from very high resolution satellite video data. In:  2015 IEEE International Geoscience and Remote Sensing Sym- posium (IGARSS) (IEEE, 2015), pp. 1881–1884 	10.	 Pires de Lima, R., Marfurt, K.: Convolutional neural network for


## 6  Conclusion and future directions

remote-sensing scene classification: transfer learning analysis.  Remote Sens. 12(1), 86 (2020) 	11.	 Zaitoun, N.M., Aqel, M.J.: Survey on image segmentation tech-

A real-time, efficient system is provided for multiple object  segmentation in aerial drone images in this work. The system  utilized a deep learning-based model, i.e., U-Net, for multiple  object segmentation. To enhance the model efficiency, data  augmentation is performed, and transfer learning is applied.  U-Net segmentation model has experimented with three dif- ferent base architectures, including VGG-16, ResNet-50, and  MobileNet. We also compare the results with these different  base architectures and conclude that the U-Net (MobileNet)  achieves excellent results. The experimental results show  that data augmentation improves the model’s performance  by achieving a segmentation accuracy of 92%, 93%, and 95%  with base architectures VGG-16, ResNet-50, and MobileNet,  respectively. In future work, we might extend this work with  other deep learning segmentation models. Furthermore, we  intend to utilize fine-tuning to additionally enhance the per- formance of the model with different benchmark datasets.

niques. Procedia Comput. Sci. 65, 797 (2015) 	12.	 Ahmed, I., Ahmad, M., Nawaz, M., Haseeb, K., Khan, S., Jeon,

G.: Efficient topview person detector using point based transfor- mation and lookup table. Comput. Commun. (2019). https://​www.​ scien​cedir​ect.​com/​scien​ce/​artic​le/​abs/​pii/​S0140​36641​93050​92?​ via%​3Dihub. Accessed 30 Aug 2010 	13.	 Ullah, K., Ahmed, I., Ahmad, M., Rahman, A.U., Nawaz, M.,

Adnan, A.: Rotation invariant person tracker using top view. J.  Ambient Intell. Humaniz. Comput. (2019). https://​doi.​org/​10.​ 1007/​s12652-​019-​01526-5 	14.	 Ahmad, M., Ahmed, I., Jeon, G.: An IoT-enabled real-time over-

head view person detection system based on cascade-RCNN and  transfer learning. J. Real-Time Image Process. 18, 1129–1139  (2021). https://​doi.​org/​10.​1007/​s11554-​021-​01103-0 	15.	 Ahmed, I., Din, S., Jeon, G., Piccialli, F.: Exploring deep learning

models for overhead view multiple object detection. IEEE Internet  Things J. 7(7), 5737 (2019) 	16.	 Ahmed, I., Ahmad, M., Khan, F.A., Asif, M.: Comparison of

deep-learning-based segmentation models: using top view person  images. IEEE Access 8, 136361 (2020) 	17.	 Minaee, S., Boykov, Y.Y., Porikli, F., Plaza, A.J., Kehtarnavaz,

Acknowledgement  This work was supported by Incheon National Uni- versity Research Concentration Professors Grant in 2020.

N., Terzopoulos, D.: Image segmentation using deep learning: a  survey. IEEE Trans. Pattern Anal. Mach. Intell. (2021). https://​ doi.​org/​10.​1109/​TPAMI.​2021.​30599​68 	18.	 Ahmed, I., Ahmad, M., Ahmad, A., Jeon, G.: Top view multiple

people tracking by detection using deep SORT and YOLOv3 with  transfer learning: within 5G infrastructure. Int. J. Mach. Learn.  Cybern. (2020). https://​doi.​org/​10.​1007/​s13042-​020-​01220-5


## 1 3

1757 Journal of Real-Time Image Processing (2021) 18:1745–1758

sensing, GIS, and ground observations: the case of L’Aquila  (Italy). Cartogr. Geogr. Inf. Sci. 43(2), 115 (2016) 	37.	 Arı, Ç., Aksoy, S.: Detection of compound structures using a

19.	 Ahmed, I., Jeon, G., Chehri, A., Hassan, M.M.: Adapting Gauss-

ian YOLOv3 with transfer learning for overhead view human  detection in smart cities and societies. Sustain. Cities Soc. 70,  102908 (2021) 	20.	 Ahmed, I., Ahmad, M., Ahmad, A., Jeon, G.: IoT-based crowd

Gaussian mixture model with spectral and spatial constraints.  IEEE Trans. Geosci. Remote Sens. 52(10), 6627 (2014) 	38.	 Benedek, C., Shadaydeh, M., Kato, Z., Szirányi, T., Zerubia, J.:

monitoring system: Using SSD with transfer learning. Comput.  Electric. Eng. 93, 107226 (2021). https://​doi.​org/​10.​1016/j.​compe​ leceng.​2021.​107226 https://​www.​scien​cedir​ect.​com/​scien​ce/​artic​ le/​pii/​S0045​79062​10021​47 	21.	 Ahmed, I., Ahmad, M., Ahmad, A., Jeon, G.: IoT-based crowd

Multilayer Markov random field models for change detection in  optical remote sensing images. ISPRS J. Photogramm. Remote  Sens. 107, 22 (2015) 	39.	 Dong, Y., Du, B., Zhang, L.: Target detection based on random

forest metric learning. IEEE J. Sel. Top. Appl. Earth Observ.  Remote Sens. 8(4), 1830 (2015) 	40.	 Lei, Z., Fang, T., Huo, H., Li, D.: Bi-temporal texton forest

monitoring system: using SSD with transfer learning. Comput.  Electr. Eng. 93, 107226 (2021) 	22.	 Ronneberger, O., Fischer, P., Brox, T.: U-net: convolutional

for land cover transition detection on remotely sensed imagery.  IEEE Trans. Geosci. Remote Sens. 52(2), 1227 (2013) 	41.	 Zhang, L., Zhang, L., Tao, D., Huang, X.: A multifeature tensor

networks for biomedical image segmentation. In: International  Conference on Medical Image Computing and Computer- Assisted Intervention, pp. 234–241 (Springer, 2015) 	23.	 Chaudhuri, D., Kushwaha, N., Samal, A.: Semi-automated road

for remote-sensing target recognition. IEEE Geosci. Remote  Sens. Lett. 8(2), 374 (2010) 	42.	 Kembhavi, A., Harwood, D., Davis, L.S.: Vehicle detection

detection from high resolution satellite images by directional  morphological enhancement and segmentation techniques.  IEEE J. Sel. Top. Appl. Earth Observ. Remote Sens. 5(5), 1538  (2012) 	24.	 Zhang, J., Lin, X., Liu, Z., Shen, J.: Semi-automatic road track-

using partial least squares. IEEE Trans. Pattern Anal. Mach.  Intell. 33(6), 1250 (2010) 	43.	 Corbane, C., Najman, L., Pecoul, E., Demagistri, L., Petit, M.:

A complete processing chain for ship detection using optical  satellite imagery. Int. J. Remote Sens. 31(22), 5837 (2010) 	44.	 Tang, J., Deng, C., Huang, G.B., Zhao, B.: Compressed-domain

ing by template matching and distance transformation in urban  areas. Int. J. Remote Sens. 32(23), 8331 (2011) 	25.	 Stankov, K., He, D.C.: Building detection in very high spatial

ship detection on spaceborne optical image using deep neural  network and extreme learning machine. IEEE Trans. Geosci.  Remote Sens. 53(3), 1174 (2014) 	45.	 Wang, J., Song, J., Chen, M., Yang, Z.: Road network extrac-

resolution multispectral images using the hit-or-miss transform.  IEEE Geosci. Remote Sens. Lett. 10(1), 86 (2012) 	26.	 Stankov, K., He, D.C.: Detection of buildings in multispec-

tral very high spatial resolution images using the percentage  occupancy hit-or-miss transform. IEEE J. Sel. Top. Appl. Earth  Observ. Remote Sens. 7(10), 4069 (2014) 	27.	 Liu, G., Sun, X., Fu, K., Wang, H.: Aircraft recognition in high-

tion: a neural-dynamic framework based on deep learning and  a finite state machine. Int. J. Remote Sens. 36(12), 3144 (2015) 	46.	 Malek, S., Bazi, Y., Alajlan, N., AlHichri, H., Melgani, F.: Effi-

cient framework for palm tree detection in UAV images. IEEE J.  Sel. Top. Appl. Earth Observ. Remote Sens. 7(12), 4692 (2014) 	47.	 Ahmad, M., Ahmed, I., Khan, F.A., Qayum, F., Aljuaid,

resolution satellite images using coarse-to-fine shape prior.  IEEE Geosci. Remote Sens. Lett. 10(3), 573 (2012) 	28.	 Liu, G., Sun, X., Fu, K., Wang, H.: Interactive geospatial object

H.: Convolutional neural network-based person tracking  using overhead views. Int. J. Distrib. Sensor Netw. 16(6),  1550147720934738 (2020) 	48.	 Ahmad, M., Ahmed, I., Ullah, K., Khan, I., Adnan, A.: View,

extraction in high resolution remote sensing images using  shape-based global minimization active contour model. Pattern  Recognit. Lett. 34(10), 1186 (2013) 	29.	 Martha, T.R., Kerle, N., van Westen, C.J., Jetten, V., Kumar,

robust background subtraction based person’s counting from  overhead. In: 9th IEEE Annual Ubiquitous Computing. Elec- tronics Mobile Communication Conference (UEMCON) 2018,  pp. 746–752 (2018). https://​doi.​org/​10.​1109/​UEMCON.​2018.​ 87965​95 	49.	 Khan, I., Ahmed, I., Ahmad, M., Ullah, K.: Towards a smart

K.V.: Segment optimization and data-driven thresholding for  knowledge-based landslide detection by object-based image  analysis. IEEE Trans. Geosci. Remote Sens. 49(12), 4928  (2011) 	30.	 Leninisha, S., Vani, K.: Water flow based geometric active

deformable model for road network. ISPRS J. Photogramm.  Remote Sens. 102, 140 (2015) 	31.	 Ok, A.O., Senaras, C., Yuksel, B.: Automated detection of arbi-

hospital: automated non-invasive patient’s discomfort detection  in ward using overhead camera. In: The 9th Annual Information  Technology, Electromechanical Engineering and Microelectron- ics Conference (IEMECON 2019) (2018), pp. 872–878. https://​ doi.​org/​10.​1109/​UEMCON.​2018.​87966​55 	50.	 Aptoula, E., Ozdemir, M.C., Yanikoglu, B.: Deep learning with

trarily shaped buildings in complex environments from monocular  VHR optical satellite imagery. IEEE Trans. Geosci. Remote Sens.  51(3), 1701 (2012) 	32.	 Ming, D., Li, J., Wang, J., Zhang, M.: Scale parameter selection by

attribute profiles for hyperspectral image classification. IEEE  Geosci. Remote Sens. Lett. 13(12), 1970 (2016) 	51.	 Shrestha, S., Vanneschi, L.: Improved fully convolutional net-

spatial statistics for GeOBIA: using mean-shift based multi-scale  segmentation as an example. ISPRS J. Photogramm. Remote Sens.  106, 28 (2015) 	33.	 Drăguţ, L., Csillik, O., Eisank, C., Tiede, D.: Automated param-

work with conditional random fields for building extraction.  Remote Sens. 10(7), 1135 (2018) 	52.	 Chhikara, P., Tekchandani, R., Kumar, N., Chamola, V., Gui-

eterisation for multi-scale image segmentation on multiple layers.  ISPRS J. Photogramm. Remote Sens. 88, 119 (2014) 	34.	 Feizizadeh, B., Tiede, D., Moghaddam, M.R., Blaschke, T.: Sys-

zani, M.: DCNN-GA: a deep neural net architecture for naviga- tion of UAV in indoor environment. IEEE Internet Things J. 86,  4448–4460 (2020). https://​doi.​org/​10.​1109/​JIOT.​2020.​30270​95 	53.	 Jain, A., Ramaprasad, R., Narang, P., Mandal, M., Chamola, V.,

tematic evaluation of fuzzy operators for object-based landslide  mapping. South-Eastern Eur. J. Earth Observ. Geomat. 3(2s), 219  (2014) 	35.	 Li, X., Cheng, X., Chen, W., Chen, G., Liu, S.: Identification of

Yu, F., Guizani, M.: AI-enabled object detection in UAVs: chal- lenges, design choices, and research directions. IEEE Netw. 35(4),  129–135. https://​doi.​org/​10.​1109/​MNET.​011.​20006​43

forested landslides using LiDar data, object-based image analysis,  and machine learning algorithms. Remote Sens. 7(8), 9705 (2015) 	36.	 Contreras, D., Blaschke, T., Tiede, D., Jilge, M.: Monitoring

recovery after earthquakes through the integration of remote


## 1 3

1758 	 Journal of Real-Time Image Processing (2021) 18:1745–1758

71.	 He, K., Zhang, X., Ren, S., Sun, J.: Deep residual learning for

54.	 Ševo, I., Avramović, A.: Convolutional neural network based auto-

image recognition. In: Proceedings of the IEEE Conference on  Computer Vision and Pattern Recognition (2016), pp. 770–778 	72.	 Howard, A.G., Zhu, M., Chen, B., Kalenichenko, D., Wang, W.,

matic object detection on aerial images. IEEE Geosci. Remote  Sens. Lett. 13(5), 740 (2016) 	55.	 Audebert, N., Saux, B. Le., Lefèvre, S.: Semantic segmentation

Weyand, T., Andreetto, M., Adam, H.: Mobilenets: efficient con- volutional neural networks for mobile vision applications. arXiv:​ 1704.​04861 (2017)

of earth observation data using multimodal and multi-scale deep  networks. In: Asian Conference on Computer Vision, pp. 180–196  (Springer, 2016) 	56.	 Garg, P., Chakravarthy, A.S., Mandal, M., Narang, P., Chamola,

V., Guizani, M.: Isdnet: Ai-enabled instance segmentation of  aerial scenes for smart cities. ACM Trans. Internet Technol. 1(3),  1–18 (2020). https://​doi.​org/​10.​1145/​34182​05 	57.	 Marmanis, D., Wegner, J.D., Galliani, S., Schindler, K., Datcu,

Publisher's Note  Springer Nature remains neutral with regard to  jurisdictional claims in published maps and institutional affiliations.

M., Stilla, U.: Semantic segmentation of aerial images with an  ensemble of CNSS. ISPRS Ann. Photogramm. Remote Sens. Spat.  Inf. Sci. 3, 473 (2016) 	58.	 Abdollahi, A., Pradhan, B., Alamri, A.M.: An ensemble architec-

Imran Ahmed  is currently working as Assistant Professor at the Insti- tute of Management Sciences, Hayatabad, Peshawar, Pakistan. He  received his Ph.D. degree with a Computer Science major from the  University of Southampton, UK. He did his MS-IT from the Institute  of Management Sciences, Hayatabad, Peshawar, Pakistan, with major  research in Computer Vision. He received a B.Sc. degree in Computer  Science and Mathematics from Edwardes College Peshawar, Paki- stan, and an M.Sc. degree in Computer Science from the University  of Peshawar, Pakistan. He has several research interests such as Deep  Learning, Machine Learning, Data Science, Computer Vision, Feature  extraction, Digital image and signal processing, Medical Image Pro- cessing, Bio-metrics, Pattern Recognition, and Data mining. He has  attended several national & international conferences in these areas. He  has been acting as a reviewer in journals such as IEEE industrial elec- tronics, IEEE Access, Journal of Ambient Intelligence, Elsevier, etc.

ture of deep convolutional Segnet and Unet networks for building  semantic segmentation from high-resolution aerial images. Geo- carto Int 1–16 (2020). https://​doi.​org/​10.​1080/​10106​049.​2020.​ 18561​99 	59.	 Marcu, A., Costea, D., Licaret, V., Leordeanu, M.: Towards

automatic annotation for semantic segmentation in drone videos.  arXiv:​1910.​10026 (2019) 	60.	 Garg, L., Shukla, P., Singh, S.K., Bajpai, V., Yadav, U.: Land use

land cover classification from satellite imagery using mUnet: a  modified Unet architecture. In: VISIGRAPP (4: VISAPP) (2019),  pp. 359–365 	61.	 Chhor, G., Aramburu, C.B., Bougdal-Lambert, I.: Satellite image

segmentation for building detection using U-Net. http://​cs229.​ stanf​ord.​edu/​proj2​017/​final-​repor​ts/​52437​15.​pdf (2017) 	62.	 Mou, L., Zhu, X.X.: Vehicle instance segmentation from aerial

Misbah  Ahmad  received her MSCS degree from the Institute of Man- agement Sciences, Peshawar, Pakistan, in 2019 and BS-Telecommu- nication system from Islamia College University, Peshawar in 2015.  Her research interests include Computer Vision, Image Processing,  Machine Learning, Deep Learning, and Data Science. She is involved  as a referee for many reputed international journals and conferences.

image and video using a multitask learning residual fully convo- lutional network. IEEE Trans. Geosci. Remote Sens. 56(11), 6699  (2018) 	63.	 Zhao, X., Yuan, Y., Song, M., Ding, Y., Lin, F., Liang, D., Zhang,

D.: Use of unmanned aerial vehicle imagery and deep learning  unet to extract rice lodging. Sensors 19(18), 3859 (2019) 	64.	 Anand, T., Sinha, S., Mandal, M., Chamola, V., Yu, F.R.: AgriSeg-

Gwanggil Jeon  received the B.S., M.S., and Ph.D. (summa cum  laude) degrees from the Department of Electronics and Computer  Engineering, Hanyang University, Seoul, Korea, in 2003, 2005, and  2008, respectively. From 2009.09 to 2011.08, he was with the School  of Information Technology and Engineering, University of Ottawa,  Ottawa, ON, Canada, as a Post-Doctoral Fellow. From 2011.09 to  2012.02, he was with the Graduate School of Science and Technol- ogy, Niigata University, Niigata, Japan, as an Assistant Professor. From  2014.12 to 2015.02 and 2015.06 to 2015.07, he was a Visiting Scholar  at Centre de Mathématiques et Leurs Applications (CMLA), École  Normale Supérieure Paris-Saclay (ENSCachan), France. From 2019 to  2020, he was a Prestigious Visiting Professor at Dipartimento di Infor- matica, Università degli Studi di Milano Statale, Italy. He is currently a  Full Professor at Incheon National University, Incheon, Korea. He was  a Visiting Professor at Sichuan University, China, Universitat Pompeu  Fabra, Barcelona, Spain, Xinjiang University, China, King Mongkut’s  Institute of Technology Ladkrabang, Bangkok, Thailand, and Univer- sity of Burgundy, Dijon, France. Dr. Jeon is an Associate Editor of Sus- tainable Cities and Society, IEEE Access, Real-Time Image Processing,  Journal of System Architecture, and MDPI Remote Sensing.Dr. Jeon  was a recipient of the IEEE Chester Sall Award in 2007, the ETRI  Journal Paper Award in 2008, and Industry-Academic Merit Award by  Ministry of SMEs and Startups of Korea Minister in 2020.

Net: deep aerial semantic segmentation framework for IoT- assisted precision agriculture. IEEE Sens. J. 21(16), 17581–17590  (2021). https://​doi.​org/​10.​1109/​JSEN.​2021.​30712​90 	65.	 Hou, Y., Liu, Z., Zhang, T., Li, Y.: C-UNet: complement UNet for

remote sensing road extraction. Sensors 21(6), 2153 (2021) 	66.	 Ahmad, M., Ahmed, I., Jeon, G.: An IoT-enabled real-time over-

head view person detection system based on cascade-RCNN and  transfer learning. J. Real-Time Image Process. 18, 1129–1139  (2021). https://​doi.​org/​10.​1007/​s11554-​021-​01103-0 	67.	 Ahmed, I., Jeon, G.: A real-time person tracking system based

on SiamMask network for intelligent video surveillance. J. Real- Time Image Process. 1–12 (2021). https://​doi.​org/​10.​1007/​ s11554-​021-​01144-5 	68.	 Ahmed, I., Ahmad, M., Rodrigues, J.J., Jeon, G.: Edge computing-

based person detection system for top view surveillance: using  CenterNet with transfer learning. Appl. Soft Comput. 107, 107489  (2021) 	69.	 Simonyan, K., Zisserman, A.: Very deep convolutional networks

for large-scale image recognition. arXiv:​1409.​1556 (2014) 	70.	 Deng, J., Dong, W., Socher, R., Li, L.J., Li, K., Fei-Fei, L.: Ima-

genet: A large-scale hierarchical image database. In: 2009 IEEE  Conference on Computer Vision and Pattern Recognition (IEEE,  2009), pp. 248–255


## 1 3
