---
workspace_id: SCI-000487
doi: 10.1016/j.compag.2020.105446
title: Vine disease detection in UAV multispectral images using optimized image registration
  and deep learning segmentation approach
authors:
- family_name: Kerkech
  given_name: Mohamed
  orcid: https://orcid.org/0000-0002-4323-5913
- family_name: Hafiane
  given_name: Adel
  orcid: https://orcid.org/0000-0003-3185-9996
- family_name: Canals
  given_name: "Rapha\xEBl"
  orcid: https://orcid.org/0000-0001-9100-7539
year: 2020
extraction_engine: pymupdf
extracted_at: '2026-09-04T01:48:52.958833+00:00'
---

# Vine disease detection in UAV multispectral images using optimized image registration and deep learning segmentation approach

VINE DISEASE DETECTION IN UAV MULTISPECTRAL IMAGES

WITH DEEP LEARNING SEGMENTATION APPROACH

A PREPRINT

Mohamed Kerkech INSA-CVL, Univ. Orléans

Adel Haﬁane INSA-CVL, Univ. Orléans

Raphael Canals Univ. Orléans, INSA-CVL

arXiv:1912.05281v1  [eess.IV]  11 Dec 2019

PRISME, EA 4229 F18022, Bourges, France mohamed.kerkech@insa-cvl.fr

PRISME, EA 4229 F18022, Bourges, France adel.hafiane@insa-cvl.fr

PRISME, EA 4229 F45072, Orléans, France raphael.canals@univ-orleans.fr

December 12, 2019


## ABSTRACT

One of the major goals of tomorrow’s agriculture is to increase agricultural productivity but above all the quality of production while signiﬁcantly reducing the use of inputs. Meeting this goal is a real scientiﬁc and technological challenge. Smart farming is among the promising approaches that can lead to interesting solutions for vineyard management and reduce the environmental impact. Automatic vine disease detection can increase efﬁciency and ﬂexibility in managing vineyard crops, while reducing the chemical inputs. This is needed today more than ever, as the use of pesticides is coming under increasing scrutiny and control. The goal is to map diseased areas in the vineyard for fast and precise treatment, thus guaranteeing the maintenance of a healthy state of the vine which is very important for yield management. To tackle this problem, a method is proposed here for vine disease detection using a deep learning segmentation approach on Unmanned Aerial Vehicle (UAV) images. The method is based on the combination of the visible and infrared images obtained from two different sensors. A new image registration method was developed to align visible and infrared images, enabling fusion of the information from the two sensors. A fully convolutional neural network approach uses this information to classify each pixel according to different instances, namely, shadow, ground, healthy and symptom. The proposed method achieved more than 92% of detection at grapevine-level and 87% at leaf level, showing promising perspectives for computer aided disease detection in vineyards.

Keywords Unmanned aerial vehicle (UAV) · image registration · convolutional neural network · precision agriculture · disease mapping.

1 Introduction

Several studies have been carried out on the overuse of crop pesticides and their negative effects on human health [1, 2, 3]. Like other crops, vines are very vulnerable to viruses, bacteria and fungi. This vulnerability favours their contamination by several types of disease that are harmful and destructive [4], such as Esca [5], Flavescence dorée [6] and Mildew [7]. Vine contamination generally reduces productivity [8], which implies economic losses for the winegrower. To deal with this situation, winegrowers have to frequently check the state of the vine leaves. However, this traditional procedure is laborious and expensive, since it involves several experts for many days [9]. To reduce economic loss and the environmental impact, remote sensing methods are a promising approach for effective vineyard monitoring.

Remote sensing of agricultural crops [10] has evolved considerably over the past decade. Applications such as calculating fertilizer rates [11], monitoring biomass production [12], weed detection [13], detecting defective crops [14] or disease detection [15, 16, 17] have been proposed. These applications are constantly progressing as technology advances, especially with the evolution of Unmanned Aerial Vehicles (UAV) which have opened up further research opportunities thanks to their low manufacturing costs.

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT

UAVs are increasingly used in many ﬁelds, such as urban remote sensing, but also in a wide range of agricultural applications [18]. Previous studies have shown the importance of both the visible and the infrared spectrum for disease detection [19]. Combining these two imaging modalities would therefore ensure better detection. In UAV imaging systems, usually two separate sensors are used, one for each modality. However, an acquisition by two sensors generates a spatial shift between the visible and infrared image which makes it difﬁcult to process the information from the two sensors simultaneously. Therefore, multimodal alignment or registration [20, 21, 22, 23] is required to fuse both sensors information with deep learning.

Deep learning techniques have enabled great progress in the computer vision ﬁeld thanks to the convolutional neural networks (CNNs) approach [24, 25, 26, 27, 28, 29]. As in several ﬁelds of application, these technologies are increasingly used in the remote sensing domain for agriculture [30, 31, 32, 33, 34, 35, 36, 37, 38]. Most research on agricultural applications uses CNNs with the sliding window technique, which generally leads to fuzzy boundaries of the image regions. On the other hand, crop disease detection can be seen as an image segmentation problem. Therefore, one can beneﬁt from the deep learning segmentation approach to detect crop disease with a better boundary precision compared to the sliding window technique. Several segmentation architectures have been developed, such as SegNet [39], DeconvNet [40] and U-Net [41]. SegNet is the most popular architecture for semantic segmentation [42, 43, 44, 45]. It has shown a very good performance in solving problems related to semantic segmentation for several applications [46, 47, 48]. So far, very little attention has been paid to the role of deep learning segmentation for vine disease detection.

This paper presents a new methodology for vine disease detection in aerial images, using multispectral information. The aim was to develop algorithms and methods in order to investigate the possibility of detecting vine diseases, using the potential of deep learning segmentation architecture. The problem was addressed by the semantic segmentation approach in order to identify classes such as shadow, ground, healthy and symptomatic vines. The method consists in two main steps. The ﬁrst one deals with the problem of multispectral image registration, where a new method was proposed to effectively align images from the visible and infrared spectres. The second one uses the SegNet architecture to delineate semantic areas in each image type separately, then a fusion procedure was applied to the segmentation outputs. Data were collected under real conditions on two vineyard plots. Several experimental schemes have been set up to show the contribution of different elements of the proposed method. The study provides an important insight into the potential of recent machine learning approaches for disease mapping using UAV remote sensing technology.

The article is organized as follows: related work is presented in section 2, the study areas and materials are described in section 3, the proposed methods are detailed in section 4, the experiments and results are presented in section 5, the proposed system are discussed in section 6 and section 7 concludes the paper.

2 Related work

This section summarizes main studies carried out on image registration, and disease detection in vineyards, plants or crops.

2.1 Image registration

In the literature, the problem of image registration dates back to the 1980s. Since then, several methods have been implemented. The work accomplished in various ﬁelds has been surveyed in: medicine [49], computer vision [50], remote sensing [51] and various applications [52]. In all areas studied, it is concluded that image registration is based on two main methods: the area-based method, and the feature-based method.

The area-based method: This method is not widely used in the remote sensing ﬁeld, because most of the algorithms are

highly sensitive to several uncontrollable parameters, such as variations in brightness, image noise, etc. The method is therefore generally applicable only to non-rigid problems. However, Wang et al. [53] implemented an algorithm (An automatic cross-correlation (ACC)) insensitive to the light conditions and applied it to multimodal images (visible and infrared). The authors concluded that this algorithm performs better than other area-based algorithms and is suitable for multimodal images. Another registration method applied to precision agriculture was proposed by Erives et al. [54]. This method that processes multispectral images is based on the phase correlation algorithm (PC). The results obtained indicate that this algorithm is robust to modality change, brightness difference, noise, rotation and translation. Zhuang et al. [55] performed a multimodal registration based on mutual information with a combination of Particle Swarm Optimization (PSO) and Powell search algorithms. The proposed method was found to be faster in terms of runtime and more accurate in terms of results compared to traditional methods.

2

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT

The feature-based method: Lakshmi et al. [56] and Javadi et al. [57] worked on natural terrain and city video frames,

acquired by a UAV for the creation of an orthorectiﬁed image. In these studies, the standard registration method based on the SURF algorithm was used. In [56], this method was compared with the Cross-Correlation algorithm (Area-based method) which failed to register the aerial images, whereas the feature-based method using the variants of the SIFT algorithm outperformed the other methods in terms of results and in terms of runtime. Tsai et al. [22] conducted a similar study to compare the SIFT algorithm with ABRISK, and concluded that the ABRISK algorithm was up to312times faster than SIFT, and had a lower mean error. In another study, Onyango et al. [58] used the AKAZE algorithm to match oblique building images with images of cities taken by a UAV. The study concluded that the AKAZE algorithm outperformed other algorithms of the same type. More recently, image matching algorithms based on deep learning have appeared [59, 21]. The deep learning architecture is used as a feature extractor to create a correspondence between the two images. Wang et al. [21] worked on remote sensing images using a supervised architecture, while Yang et al. [59] used an unsupervised architecture to recalibrate multi-temporal images. The latter showed better accuracy than the SIFT type algorithms, but these results only correspond to multi-temporal images, of the same modality and on low resolution images.

2.2 Disease detection

A comprehensive review of the literature was conducted by Mahlein [60]. The survey lists several studies on disease detection by multispectral imaging. Among others, Oerke et al. [61] demonstrated that disease symptoms in the plants begin to appear in the infrared range several days before their appearance in the visible range. The potential of multispectral information in the early detection of plant disease is attracting more and more interest in the remote sensing ﬁeld. Two studies on the hyperspectral reﬂectance of vine leaves diseased by complex Esca, the ﬁrst one [62] at the leaf level, and the second one [63] at the vine ﬁeld level (UAV images). Both showed a difference between a reﬂectance of a healthy and diseased leaf.

In a ﬁrst study, Albetis et al. [64] investigated the detection of Flavescence dorée in UAV images. The study was carried out on plots of white and red cultivars. The results obtained indicate the feasibility of disease detection using aerial images. In a second study, Albetis et al. [65] examined the potential of multispectral imaging by UAV for the detection of symptomatic and asymptomatic vines. In addition to the ﬁrst study, a larger dataset was acquired and used to test 24 variables calculated from this new dataset. The best results were obtained by the red-green index (RGI) and the red-green vegetation index (GRVI).

In Al-Saddik et al. [66], a ﬁrst study on hyperspectral images at the vine leaf scale was carried out. The aim of the study was to develop spectral disease indices capable of detecting and identifying Flavescence dorée disease in vines, and achieved 90% classiﬁcation accuracy. A second study by Al-Saddik et al. [67] on disease identiﬁcation at the vine leaf level was carried out to differentiate between yellowing leaves, and leaves infected with Esca disease through a neural network classiﬁer. The best results were obtained when textural and spectral data were combined. A third study by the same authors [68] consisted in deﬁning the most signiﬁcant spectral channels for Flavescence dorée disease detection.

Rançon et al. [69] carried out a similar study on Esca disease detection in vineyards. The imaging system was mounted on a small vehicle that passed between the vine rows for image acquisition. Two methods for detecting Esca disease were used: Scale Invariant Feature Transform (SIFT) encoding, and the deep learning MobileNet network. The authors concluded that the deep learning method was better than the SIFT encoded method.

In our previous study [38], a new method for detecting Esca disease in UAV RGB images was proposed. The method uses LeNet5 CNN architecture and good results were obtained achieving 95% disease detection accuracy in the visible range.

To the best of our knowledge, no research has been conducted so far on the combination of visible and infrared UAV images for vine disease detection by a deep learning segmentation approach.

3 Study areas and materials

3.1 Study areas

This study is carried out on two parcels of vines located in the Center Val de Loire region in France. The ﬁrst plot (P1) can be seen in Figure 1a and the second one (P2) in Figure 1b. P1 and P2 are at an altitude of 110 and 114 meters respectively, a surface of 1.8 hectares for P1 and 1.5 hectares for P2, and are positioned on a silty sand soil for P1 and sandy loam soil for P2. The ground of P1 is slightly inclined (7% of slope) (Figure 2) and ﬂat for P2. The Center Val de

3

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT

Loire region is characterized by a moderate temperature variation between 1 to 26◦C, and the average annual rainfall reached 700 mm. The Table 1 gives more details about the plots.

In order to carry out this study and get a healthy and diseased samples, a part of the P1 plot was treated with phytosanitary products (to protect the vine against diseases), and the other part remained untreated in order to allow the development of the disease, and getting the disease and healthy samples of vine. During this time, late blight disease was spread to all untreated areas of the plot. The P2 plot is treated globally against diseases (totally healthy), in our study, it will be used for a qualitative validation.


> **Table 1: The study vineyard description.**

Types of information Description (P1) Description (P2) Surface 1.8 hectares 1.5 hectares Altitude 110 meter 114 meter Planting year 1976 1991 Variety Malbec Sauvignon Vine tree spacing 1 meter 1 meter Interline distance 1.5 meter 1.5 meter Slope 7% 0% Exposure North-South Northwester-Southeaster Coarse fraction 25% 17% Soil Organic Carbon 4.46% 3.94% Soil type Silty-Sand Sandy-Loam


> **Figure 1: The study vineyard seen by satellite. The plot (P1) in picture (a) and The plot (P2) in picture (b).**

4

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT


> **Figure 2: The plot (P1) seen from the ground.**

3.2 Materials

The UAV used in the data acquisition process is a Quadcopter drone (Figure 3a) which was manufactured by Scanopy. This drone embeds two cameras type sensors MAPIR Survey2 (Figure 3b). The ﬁrst is a visible light sensor (RGB) set to automatic lighting, and the second is an infrared light sensor (Near Infrared (NIR), Red and Normalized Difference Vegetation Index (NDVI)). For this one, the wavelength of its near infrared is 850 nm. Both image sensors have a high-resolution of 16 megapixels (a size of 4608 × 3456).

The data acquisition is carried out by the drone, which ﬂies over the plot at an altitude of 25 meters and with an average speed of 10 km/h. At this altitude, the ground resolution is 1cm2/pixel. Each 2 seconds an image is taken automatically and without the drone stop, each image taken has a overlap over 70% with the previous image. The drone has an average energy autonomy of 20 minutes. The climatic conditions of the acquisition are moderate, which means low winds and optimal lighting (the hours of acquisition are between 11:30 and 13:30 to avoid the shadow of the vinerow). The acquisition was made in summer 2018.


> **Figure 3: The acquisition materials used in this study. The quadcopter UAV drone (a) and the high-resolution Survey2**

> sensor (b).

5

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT

4 Methods

Using the multispectral and a standard RGB images, automatic processing and analysis methods were developed to extract relevant information and correlate it with the ground truth results. Deep learning segmentation was applied on the two types of images to automatically delineate different regions (healthy, symptomatic, etc.). This generates a disease map of the vineyard comprising different segmented regions, which can be used to monitor the vineyards.

The method comprises three main steps (see Figure 4). The ﬁrst one consists in image registration between the images acquired in the visible and infrared range. This step is essential for the third step, as it enables the pixel-wise superposition of the two images and thus allows segmentation fusion. Once the registration of the two images has been performed, the next stage consists in segmenting the plot in the visible and infrared range using the SegNet architecture. The two segmented images are merged in the third step, to generate a disease map.

Visible image  registered with

SegNet (CNN)

Visible image

Visible

visible model

segmented

image

Image  registration

IR image g Infrared image  registered with

Seg.  fusion Disease map

algorithm

Infrared image

SegNet (CNN)  infrared model

Infrared

segmented

image

visible image

Image registration between visible and

Image segmentation and symptom

Fusion between visible and infrared

infrared range

detection in each spectral range

segmentation for disease detection


> **Figure 4: Overview of disease detection system in grapevine ﬁelds.**

4.1 Image registration

The objective of the registration algorithm is to realign and geometrically correct the shift [70] between the visible and infrared images at the pixel-wise level. Generally, the UAV image is partially distorted due to the UAV vibrations, read in rolling shutter mode of the sensors and optics. Therefore, the rigid alignment model (translation and rotation) is not appropriate in our case. Hence, the proposed algorithm uses the non-rigid model. However, even if the registration model is correct it is not sufﬁcient to align the two types of images perfectly. Moreover, matching image points between the visible and infrared bands is difﬁcult, since the key points do not necessarily have the same visual properties in the two spectral bands. In order to improve the accuracy of the image alignment, an iterative process based on minimization of the registration error was implemented.

The registration algorithm proposed in this study is based on the Accelerated-KAZE (AKAZE) algorithm [71]. AKAZE is an algorithm used in computer vision for detecting objects or similarities in two images. Its principle is comparable to that of the Scale Invariant Feature Transform (SIFT) [72], Speeded Up Robust Features (SURF) [73], Features from Accelerated Segment Test (FAST), Binary Robust Independent Elementary Features (BRIEF), Oriented FAST and Rotated BRIEF (ORB) [74], KAZE [75] algorithms. However, AKAZE is much more efﬁcient in detection robustness, description and in the speed of calculation as it was created with high-performance algorithms in a pyramidal framework comparable to other algorithms of the same type. Even if AKAZE follows the same pyramidal steps as the other algorithms, the method used is very different. AKAZE integrates Fast Explicit Diffusion (FED) [76] systems for accelerated feature detection in a non-linear scale space. Moreover, a modiﬁed version of Local Difference Binary (M-LDB) [71] has been integrated into AKAZE. Unlike the old version, this modiﬁed version of LDB [77] is a rotationally invariant, scaled descriptor and can exploit gradient information from the non-linear scale space.

The proposed registration method is shown in Figure 5. The ﬁrst step is to extract the green channel (G) from the visible image, and the near infrared channel (NIR) from the infrared image (these channels were selected for their vegetation texture information). By using the normalization equation (1), the second phase normalizes the two spectral channels to improve their contrast. The third step is to extract the points of interest and calculate their features from the two channels (by the AKAZE algorithm). Based on the features of the interest points, the fourth stage is to map each point of interest extracted in the G channel to the corresponding point in the NIR channel. In the ﬁfth step, to eliminate some outliers, a ﬁrst thresholding algorithm performs a preselection of inlier matching points, then a ﬁnal selection is performed by the RANdom SAmple Consensus (RANSAC) algorithm [78]. To obtain the best setting for algorithms that contribute to removing the outliers, a dynamic setting (by threshold variation) method based on homographic matrix analysis is integrated into the registration system. This dynamic method (dynamic threshold) very

6

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT

signiﬁcantly reduces the number of registration failures. Note that X is the coordinates of the source infrared image (x, y), X’ is the coordinates of the registered infrared image (x’, y’) and H is the homographic matrix 2. In order to avoid the problems that lead to misregistration, a dynamic threshold regulation of the RANSAC algorithm was used, and the distance-based algorithm. For each given value, a homographic matrix is estimated. The viability of this matrix is then tested by equation 3. This test is performed by projecting the end coordinates of the source image into the new space of the registered image. If the result found is coherent (the distance between the old coordinates and the new coordinates does not exceed a certain threshold), this implies the end of the dynamic adjustment procedure, and the matrix tested is used to register the image. Otherwise, a new setting is made to repeat the same procedure. Once this step is ﬁnished, the pre-registered infrared image can be obtained by the homographic matrix validated by the dynamic adjustment procedure.

In order to reduce the registration error, an iterative method was implemented. After the pre-registration has been completed, an iterative phase starts from the result obtained, calculates the error by the Root Mean Squared Error (RMSE) [79] between matched points which are calculated on the X coordinates with equation (4), and on the Y coordinates with equation (5), and then calculates their module by equation (6). If the error decreases, another iteration is performed, if not, the iterative process stops and the best result, which is the result with the minimum RMSE, is kept.

Repeat the algorithm with last infrared image preregistered

AKAZE Algorithm

Image pre-processing

Image  normalization Green channel

Visible

Extraction of interest  points and their features

extraction

image

Infrared

Image  normalization Infrared channel

Extraction of interest  points and their features

image

extraction

Homographic

Removing outliers by distance

Matching between the

thresholding and RANSAC

matrix  computation

two interest points

(Dynamic setting)

If (new error < old error)

Infrared image

No

Yes

preregistered

Registration error

computation

Infrared image

Visible image

registered


> **Figure 5: Proposed method for non-rigid registration of multimodal (visible and infrared) image.**

INormalized = 255 × I−min(I) max(I)−min(I) (1)

where INormalized is the normalized image of the source image I (visible or infrared), min(I) and max(I) are respectively the minimum and maximum grey level value of the source image I.


## 1 + h00

h01
h02
h10
1 + h11
h12
h20
h21
1

!

H =

(2)

X′ = HX (3)

where (1 + h00) and (1 + h11) are stable scale factors respectively in the X and Y direction only. h01 and h10 are scale factors respectively in the X direction relative to the Y distance from the origin and Y direction relative to the X

7

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT

distance from the origin. h02 and h12 are respectively translation in the X and Y direction.h20 and h21 are relative scale factors X and Y respectively as a function of X and Y.

q PN

i=0(xV ISi−xIRi)2

N (4)

RMSEx =

q PN

i=0(yV ISi−yIRi)2

N (5)

RMSEy =

q

RMSE2x + RMSE2y (6)

RMSE =

where (xV ISi, yV ISi) and (xIRi, yIRi) are respectively the "i" th coordinates of correspondence between the visible and infrared images. N is the number of matches found between the visible and infrared images.

4.2 Segmentation and fusion

This subsection presents the visible and infrared image segmentation system, the deep learning architecture used in this process, the labelling and learning method, and ﬁnally, the overall operation.

4.2.1 Deep learning segmentation

The CNN architecture has been very successful in the pattern recognition and computer vision ﬁelds. Since then, there has been a continuous evolution of CNN architectures. The new architectures have become deeper, but also new types of architectures have emerged that directly segment an image, such as the SegNet [39] architecture, used in the present study. To segment an image, the SegNet architecture (Figure 6) operates through two opposite phases, an information encoding phase and a decoding and classiﬁcation phase (Table 2). The encoding phase is in fact a classic CNN architecture, usually with a VGG-16 [27] architecture. The coding phase consists of three types of processing, namely convolution layers, ReLU layers (ReLU is an activation function for removing the negative values that result from convolution and deconvolution. It is commonly used in deep learning networks, because it performs better than other activation functions) and MaxPooling layers (non linear sub-sampling function). Decoding consists of the same types of processing except for the convolution layers which are replaced by deconvolution layers, and the MaxPooling layers which are replaced by Upsampling layers. It is in the decoding part of the network that the segmented image is formed, until the ﬁnal decoding layer is reached. At this level, a pixel-wise segmentation is performed by the Softmax function.

In the present study, generation of the disease map of a vineyard ﬁeld is considered as a four-class segmentation problem in the visible and infrared range. The objective is to build a SegNet model capable of differentiating between shadow, ground, healthy and symptomatic (visible and infrared) classes in the two spectral bands. The distinction between each class is mainly based on variations in color, texture, spectral information and spatial relative position of each class. This important information must be extracted by the SegNet network during the encoding phase, also called the feature extraction phase, then rebuilt and segmented by the decoding phase.

4.2.2 Fusion of multimodal image segmentation

The fusion of segmentations is performed in order to obtain a disease map with more robust results. To generate a disease map, each pixel of the image segmented in the visible range is compared with the pixel of the same position in the infrared range. Here, three main cases are considered. The ﬁrst one is that the two pixels represent the symptomatic class. In this case, the result is symptom intersection class. The second case is when the pixel is classiﬁed as symptomatic in the infrared range, and healthy in the visible range. In this case, the resulting class is symptomatic infrared (This may be a case where the disease has not yet affected the visible range by discoloration of the leaves). The third case is when the pixel is classiﬁed as healthy in the infrared range, and symptomatic in the visible range. The resulting class is visible symptomatic.

To evaluate the disease map, two cases are evaluated. The ﬁrst one, is the case described in the previous paragraph, it is named fusion by intersection and symbolized "Fusion AND", the AND operator means the symptom is considered to be detected if it is present in both visible and infrared images. The second case is named fusion by union and is symbolized "Fusion OR". As are named, this case unites visible and infrared ranges detections with or operator.

8

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT

Encoder Decoder

Visible  SegNet Model

Visible train dataset

(89,688 patches)

Pooling indices

Infrared  SegNet Model

Infrared train dataset

(84,061 patches)

Visible image

RGB image +

segmented

Model

Deconv + ReLU

Conv + ReLU

Max Pooling (Undersampling) Upsampling

U li

NIR, Red, NDVI

Infrared image

segmented

image + Model

Softmax

SegNet Architecture

Input data

Output data


> **Figure 6: Visible and infrared image modeling and segmentation system.**

4.3 Dataset

The dataset was composed of visible and infrared range images. In our case, the visible sensor was used to detect the presence or absence of chlorophyll in the crop, i.e. to detect any anomalies in the vegetation in relation to its discoloration. The acquisition wavelength of the infrared sensor used here is 850 nm. Unlike visible wavelengths, this wavelength was chosen for its sensitivity to changes in the different states of vegetation. Indeed, due to the high reﬂectance generated by vegetation, near infrared waves are relevant for plant analysis.

The visible (Figure 7) and infrared (Figure 8) datasets were labelled based on four dominant classes in the visible and infrared range, fusion by intersection, and fusion by union. The ﬁrst class represents the shaded areas in the vine and on the ground (all the dark areas). This class does not reﬂect light, which means that no relevant information can be drawn from it. The second class represents the ground; it can be an area of weeds or an area of any type of soil. The third class represents the healthy vegetation of the vine. This class has a green color in the visible range and has a high reﬂectance level compared to the previous classes in the infrared range. Finally, the fourth class represents the symptomatic vegetation of the vine. This class is generally yellow or brown color in the visible range (in the case of an advanced symptom). This color results from a problem with chlorophyll production. In the infrared range, the symptomatic class is a variation in reﬂectance between a leaf and its neighbours. Visually this gives a special texture characterized by a signiﬁcant variation in reﬂectance, with which this class can be distinguished from the others. After merging the segmented visible and infrared images, a class called "symptomatic intersection" is created when symptoms are detected in the same visible and infrared area, and "symptomatic union" is created for uniﬁed the two symptoms class.

By using data augmentation methods (described in the following sub-section), a dataset of 105, 515 and 98, 895 patches (360 × 480 pixels for each patch) was generated for the visible and infrared range respectively. This dataset was used to train and validate the SegNet model. Among the dataset patches, 85% was randomly selected for training and the remain (15%) was used for validation. To evaluate and test the SegNet model, another area (the second area) at two different dates was used to test the visible and infrared model, then the fusion algorithm.

4.4 Data augmentation

Due to the huge amount of data required to train a deep learning network, the lack of data, and the difﬁculty of labelling images, several methods of data augmentation [80] were used. First, some images acquired by UAV with a size of 4608 × 3456 pixels were labelled by a semi-automatic method. Then each of these images underwent automatic data augmentation to generate 360 × 480 pixels labelled patches, which were used in SegNet network learning.

In this process, several data augmentation techniques were combined. The ﬁrst transformation consisted in horizontal shift by an overlap of 50% to enable the network to learn the transition areas. Rotation was also used, since it enables

9

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT


> **Table 2: SegNet setting.**

Phase Number Layer type Filter size Number of features maps

1 Conv1-1 3 × 3 64 Conv1-2 3 × 3 64

2 Conv2-1 3 × 3 128 Conv2-2 3 × 3 128

3 Conv3-1 3 × 3 256 Conv3-2 3 × 3 256 Conv3-3 3 × 3 256

Encoder

4 Conv4-1 3 × 3 512 Conv4-2 3 × 3 512 Conv4-3 3 × 3 512

5 Conv5-1 3 × 3 512 Conv5-2 3 × 3 512 Conv5-3 3 × 3 512

5 Deconv5-3 3 × 3 512 Deconv5-2 3 × 3 512 Deconv5-1 3 × 3 512

4 Deconv4-3 3 × 3 512 Deconv4-2 3 × 3 512 Deconv4-1 3 × 3 512

Decoder

3 Deconv3-3 3 × 3 256 Deconv3-2 3 × 3 256 Deconv3-1 3 × 3 256

2 Deconv2-2 3 × 3 128 Deconv2-1 3 × 3 128

1 Deconv1-2 3 × 3 64 Deconv1-1 3 × 3 64

the network to learn the different orientations of the vinerows. Several rotation values ranging between 0◦and 180◦ with a step of 30◦were used. The third transformation consisted in under and over sampling (scale change) in order to enable the network to learn that the thickness of the vine rows could change, but that it would not affect the classiﬁcation in the case of a scale change, such as a change in altitude of the UAV for image acquisition. For that purpose, a sub-sampling between 0.5 to 1 of the real scale, and an oversampling between 1 to 1.5 was performed with a step of 0.25. The fourth technique of data augmentation involved modiﬁcation of the brightness to make the network insensitive to light levels. As the image acquisition was done outdoors, the brightness parameters are uncontrollable because of changes in the weather. Thus, coefﬁcients between 0.8 to 1.2 with a step of 0.1 were multiplied with the grey levels of the images to generate dark, normal, and bright effects.

5 Experimentation

This section details the experiments, testing, validation and interpretation of the results. The algorithms were developed under the Python 2.7 development environment by using the Tensorﬂow 1.8.0, NumPy 1.16.2 and OpenCV 3.0.0 libraries. To run and evaluate the runtime of our algorithms, we used the following hardware; an Intel Xeon (R) W-2123 (a) 3.60 GHz×8 processor (CPU) with 32 GB of RAM, and a graphics processing unit (GPU) NVidia GTX 1080Ti with an internal RAM of 11 GB under the Linux operating system Ubuntu 16.04 LTS (64 bits).

The experiments section is divided into two subsections. The ﬁrst one concerns the visible and infrared image registration, and the second one details the segmentation and fusion steps.

10

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT

Shadow

Ground

Visible image

Visible image

manual  sample  selection

Healthy Visible  UAV image

Manual  correction

Automatic  classification

labeled

prelabeled

Symptom.

Samples examples for visible ground truth


> **Figure 7: Semi-automatic ground truth for the visible image.**

Shadow

Ground

Infrared image

manual  sample  selection Infrared  UAV image

Infrared image

Manual  correction

Automatic  classification

labeled

prelabeled

Healthy

Symptom.

Samples examples for infrared ground truth


> **Figure 8: Semi-automatic ground truth for the infrared image.**

5.1 Evaluations of image registration algorithm

Performance measurement was carried out by computing the RMSE Eq. 4, 5 and 6 between the points of interest matched, in pixel units. RMSE provides information on the geometric correction and the shift between the visible and infrared images.


> **Table 3: Statistical performance results for standard and optimized registration for a dataset of 150 images. Mean, Min**

> and Max are the average, minimum and maximum number of the statistic results, respectively.


## Methods

Standard registration
Optimized registration
Mean
Min
Max
Mean
Min
Max
RMSE "Pixels"
3.29 ± 1.57
1.13
9.75
2.43 ± 1.26
0.87
9.02
Runtime "Seconds"
92 ± 19
49
129
139 ± 40
67
238
Number of iterations
-
-
-
3.12 ± 1.48
1
7

Measure

5.2 Experiment on image segmentation and fusion

5.2.1 Data labelling

Due to the large amount of data and the difﬁculty of achieving accurate labelling, which must be provided for learning, the data labelling procedure was performed by a semi-automatic method. First, an automatic step was performed by a CNN LeNet5 network for pre-labelling. Then, the manual labelling was reinforced by the ground truth provided by technicians in the ﬁeld.

Two patch datasets were created for visible and infrared images, the patch size is 32 × 32, organized into 4 classes (shadow, ground, healthy and symptomatic class). Each dataset contains 70, 560 patches (17, 640 samples for each class, among these samples, there are 14, 994 samples for training and 2, 646 samples for validation). Then, two CNN LeNet5 models were created from these two datasets (visible and infrared). The sliding window method was used to perform

11

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT

+ Image registration

algorithm

Visible image Infrared image Infrared image registered to visible

image


> **Figure 9: Result on image registration.**

After seven iterations

Standard registration Optimized registration


> **Figure 10: Correction of the shift by seven iterations.**

automatic labelling on UAV images with a size of 4608 × 3456 pixels. To obtain the best possible accuracy, the sliding window was set with a displacement step of 2 × 2. The automatic labelling operation required just over an hour and a half of runtime to label only a single UAV image. The manual correction, performed by the free software "Paint.Net", consists in correcting possible classiﬁcation errors generated by automatic labelling and adding the symptomatic class. Indeed, technicians observed vines at the ground and reported all the diseased ones. By referring to the ground truth, each vine was referenced with its coordinates in the ﬁeld. Then, this information was used to label the areal images.

5.2.2 Learning and testing procedure

First, the labelled visible and infrared datasets were used in the learning phase. During this phase, the SegNet network uses the patches sized 360 × 480 pixels, with their labels. This learning phase was performed for visible and infrared ranges separately. The number of iterations was set to 100, 000, each batch was composed of 5 patches selected randomly.

The SegNet models generated were used for testing and evaluation. The segmented images were compared with the ground truth to estimate the segmentation accuracy. Due to the large size of the UAV image (4608 × 3456 pixels), images were divided into non overlapping blocks, with a size of 360 × 480 pixels. Segmented blocks were stitched together to retrieve the original size.

12

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT

5.2.3 Performance measurement

The segmentation performance was measured by two methods. The ﬁrst one (presented in Table.4) is based on the leaf-level (pixel-wise) computation of the Recall (eq.7), precision (eq.8), F1-Score (eq.9)/Dice coefﬁcient (eq.10) and Accuracy (eq.11) for each class (shadow, ground, healthy and symptomatic). The second evaluation is based on the grapevine-level (presented in Table.5). Indeed, the segmentation measurement at pixel-wise do not provide an information about the detection at the grapevine-level, it indicates a given grapevine is infected or not. This measurement uses a sliding window with a size of 64 × 64 pixels (corresponding to average size of a grapevine in the studied plots). Inside this window, only the dominant class in the ground truth is evaluated. If there is a match between the ground truth and the SegNet estimation, it is considered as true positive, otherwise it is false positive. At the end of this process, the same measurement is computed.

Recall = T P T P +F N (7)

Precision = T P T P +F P (8)

F1 −Score = 2 Recall×P recision

Recall+P recision = 2T P F P +2T P +F N (9)

Dice = 2|X∩Y |

|X|+|Y | = 2(T P ) (F P +T P )+(T P +F N) = 2T P F P +2T P +F N (10)

Accuracy = T P +T N T P +T N+F P +F N (11)

where TP, TN, FP and FN are the number of samples for "True Positive", "True Negative", "False Positive" and "False Negative". For the Dice equation, X is the set of ground truth pixels and Y is the set of pixels estimated by the SegNet classiﬁer.


> **Table 4: The leaf-level (pixel-wise) average result on two temporal tests by measuring Recall (Rec.), Precision (Pre.),**

> F1-Score/Dice (F1/D.) and Accuracy (Acc.) on the performance of visible, infrared image segmentation and fusion
(values presented in percent). Note that: "Fusion AND" and "Fusion OR" are the cases where their symptomatic classes
are respectively the intersection and the union of the symptomatic visible and infrared classes.

Class name Shadow Ground Healthy Symptomatic Total Measure Rec. Pre. F1/D. Rec. Pre. F1/D. Rec. Pre. F1/D. Rec. Pre. F1/D. Acc. Visible 76.31 87.25 81.05 91.37 95.95 93.51 86.86 66.89 75.31 80.22 77.99 78.72 85.13 Infrared 84.25 72.25 77.69 87.74 91.33 89.42 73.81 50.18 58.58 59.02 85.06 69.55 78.72 Fusion AND 87.84 86.78 87.30 95.73 95.95 95.84 83.73 69.09 75.60 53.70 94.02 67.93 82.20 Fusion OR 87.84 86.78 87.30 95.73 95.95 95.84 82.12 72.30 76.55 84.07 90.47 87.12 90.23


> **Table 5:**

> The grapevine-level average result on two temporal tests by measuring Recall (Rec.), Precision (Pre.),
F1-Score/Dice (F1/D.) and Accuracy (Acc.) on the performance of visible, infrared image segmentation and fusion
(values presented in percent). Note that: "Fusion AND" and "Fusion OR" are the cases where their symptomatic classes
are respectively the intersection and the union of the symptomatic visible and infrared classes.

Class name Shadow Ground Healthy Symptomatic Total Measure Rec. Pre. F1/D. Rec. Pre. F1/D. Rec. Pre. F1/D. Rec. Pre. F1/D. Acc. Visible 94.00 93.42 93.63 97.39 97.94 97.66 95.16 85.20 89.91 90.15 92.97 91.50 94.41 Infrared 97.53 79.97 87.55 97.30 95.41 96.32 93.72 69.19 79.19 70.49 96.92 81.66 89.16 Fusion AND 94.01 86.62 89.96 97.41 97.89 97.65 93.81 87.55 90.56 66.92 73.12 68.03 88.14 Fusion OR 94.00 94.03 93.95 97.39 97.94 97.66 93.81 89.65 91.68 92.91 92.78 92.81 95.02

13

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT


> **Table 6: Results on runtime performance (expressed in seconds) for the entire system as a function of the average**

> runtime of standard and optimized registration.

Step Registration SegNet seg. Fusion Total Standard registration 92 140 × 2 2 374 Optimized registration 139 140 × 2 2 421

UAV images              SegNet estimation


> **Figure 11: Segmentation qualitative results by the SegNet method for the P1 vineyard. On the left, images from UAV**

> and their right, the segmentation result of these images. The color code of the segmentation is; Black: Shadow, Brown:
Ground, Green: Healthy, Yellow: Visible symptom, Orange: Infrared symptom, Red: Symptom intersection.

14

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT

UAV images              SegNet estimation


> **Figure 12: Segmentation qualitative results by the SegNet method for the P2 vineyard. On the left, images from UAV**

> and their right, the segmentation result of these images. The color code of the segmentation is; Black: Shadow, Brown:
Ground, Green: Healthy, Yellow: Visible symptom, Orange: Infrared symptom, Red: Symptom intersection.

15

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT

Shadow

Ground

Healthy

(f)

(a)

(c)

Visible symptom

(h)

(e)

Infrared symptom

Symptom intersection

(g)

(b)

(d)


> **Figure 13: Example of segmentation and fusion of a healthy area. (a): Visible image, (b): Infrared image, (c): Visible**

> ground truth, (d): Infrared ground truth, (e): Fusion ground truth, (f): Visible SegNet estimation, (g): Infrared SegNet
estimation, (h): Fusion of segmentation results.

Shadow

Ground

Healthy

(f)

(a)

(c)

Visible symptom

(h)

(e)

Infrared symptom

Symptom intersection

(g)

(b)

(d)


> **Figure 14: Example of segmentation and fusion of an area contaminated by Mildew. (a): Visible image, (b): Infrared**

> image, (c): Visible ground truth, (d): Infrared ground truth, (e): Fusion ground truth, (f): Visible SegNet estimation, (g):
Infrared SegNet estimation, (h): Fusion of segmentation results.

6 Discussion

The ﬁrst question of this study was to determine the ability of multispectral drone imaging to map grapevine Mildew symptoms using machine learning approaches. This led to study imaging modalities in the visible and infrared spectral domains, since several researches have shown the interest of these domains for symptom detection. As our system consists of two cameras for each modality, image alignment was required. We were, therefore, led to develop an algorithm for image registration then using deep learning segmentation to detect the affected surfaces in the vineyard. Another question of this research was, how through the deep learning approach, we can combine the both types of images to delineate symptomatic areas as precisely as possible. Thus, the rate of affected areas can be obtained at the leaf scale or at the vine plant scale. The following sections ﬁrst discuss the results of the registration and then those of the image segmentation.

6.1 Image registration

In Figure 9 shows the qualitative result of the registration. On the left and in the middle are the visible and infrared images respectively. Images were taken at a very short time interval (less than one second) and in the same ﬁeld of view. After the registration of these two images (image on the right) two black areas can be observed on the left and at the bottom of this image. The two areas were captured only by the visible sensor, which explains why there are no equivalents in the infrared image registered at the moment of superposition. There are also areas captured only by the infrared sensor, but due to the fact that the infrared image is registered to the visible image, these areas are not displayed on the result.

An example of how the proposed registration method operates is shown in Figure 10. In the image on the left (image registered with the standard method) there is a certain shift between the vinerows present in the visible and infrared images. This is due to a lack of matched points between both images. However, after each iteration, some new correspondence points are detected thanks to the dynamic threshold, and gradually, seven iterations later, a good alignment of the vinerows is achieved as shown in the image on the right.

16

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT

The quantitative results obtained during the registration experiments are presented in Table 3. This table reports a statistical study on a dataset of 150 images, for a comparison between the standard registration method used in [56, 57] and the proposed optimized registration method. The values obtained are expressed in "pixels" for the RMSE error measurement, in "seconds" for the runtime and in "times" for the iteration. For each line, the ﬁgures in bold show the best results obtained. For standard registration, an average error of 3.29 pixels was obtained (this result corresponds to the range of results obtained in [58] by the same algorithm), compared to 2.43 pixels for the optimized method, i.e. an average error reduction of 0.86 pixels over the entire dataset. This error reduction can be explained by the appearance of new correspondence points, in subsequent iterations, between the two images. These points are used to calculate a new homographic matrix, which corrects the registration slightly, and reduces the RMSE error. However, there are special cases where the optimized method does not reduce the error, in which the result of the optimized method is cancelled and the output of the standard registration is kept. The best score obtained by the standard method yields an error of 1.13 pixels, whereas with the optimized method the minimum error is 0.87 pixels. However, both methods can produce larger errors, as we can ﬁnd errors up to 9.75 pixels with the standard method and 9.02 pixels with the optimized method. Note that our disease detection system performs better with an RMSE value ≤5; RMSE values between 5 and 10 may in some cases reduce the accuracy of disease localization.

The runtime measurement is shown in Table 3. For the standard registration, an average runtime of 92 seconds was obtained, versus 139 seconds with the optimized method. This increase in runtime is due to the additional processing performed by the optimized method (3.12 iterations on average). This is not the only reason, however: with the standard method, there is a very signiﬁcant difference (80 seconds) between the minimum and the maximum values. The difference is due to the number of interest points detected in an image by the AKAZE algorithm: the larger the number of interest points detected, the longer the processing time. In other words, there is a direct relation between these two parameters.

The proposed algorithm based on the AKAZE detector was tested by other feature extraction algorithms such as SIFT, SURF, ORB and KAZE. The results obtained by SIFT showed a slightly higher error than those obtained by AKAZE, and the runtime was between 2 to 10 times longer than AKAZE, conﬁrming the study by Tareen et al. [81]. For the other algorithms, several cases of failure were identiﬁed. They are mainly due to the lack of correspondence between the two images, which implies a sensitivity of these algorithms to the differences of modality between the two images. Another algorithm developed by Yang et al. [59], which is based on feature extraction through a deep learning architecture was tested, and several problem were observed. Not only, the deep learning method use much of RAM memory, making it very difﬁcult to register high resolution images, but even with a decrease in the resolution of the images, the algorithm cannot ﬁnd good matches, which leads to the failure of the registration process. This is due to the difference in image modalities.

Some other Area-based registration algorithms were also tested, such as: Normalized Cross-Correlation (NCC) [53] and Phase-Correlation (PC) [54]. But due mainly to the presence of some deformation on the used dataset images, these algorithms did not manage to correctly register most of the images. Another disadvantage of these algorithms is that they are very time consuming, and were therefore discarded.

6.2 Image segmentation and fusion

The qualitative results of the ﬁgures 11 and 12 represent the results on the vineyards of P1 and P2 respectively. For the P1 plot (Figure 11), a large part of the untreated plot was contaminated by Mildew. This presence of disease is well detected by segmentation. As can be observed, in most cases, the symptoms are better detected in the visible range (coded by the yellow color) than in the infrared range (coded by the orange color). This hypothesis has been conﬁrmed by the quantitative results in Table 4. Of course, there are in some cases false detections in both areas. However, when symptoms are detected in both ranges it is likely to be true detection.

For the P2 plot (Figure 12), the vineyard is healthy, where the SegNet estimation generally match the ground truth. However, in this example of 3 images, some misclassiﬁcation of symptomatic areas in the visible range can be observed. This generally occurs when there is a gap in the vegetation (a plant missing in a row, for example) and the color of the soil is similar to that of a symptomatic plant (brown or golden). Also, it is usually explained by the edge effects of the sliding window, because the information is not complete in some border (these effects are not always present in the outputs). In other cases, the symptom class comes out when there is a yellow color mix with green, this case is usually comparable to the symptomatic leaves. To counter this problem, it is necessary to check the neighboring images result which cover this area. If the symptom is detected in all or most of the images, therefore, that can be a real symptom, otherwise, it is a false detection. Misclassiﬁcation of the other classes can also appear, indeed, in these examples, it can be observed some misclassiﬁcation of the grass which is detected as healthy vine or symptom class (in the 1st example of Figure 12). Also, some confusion between the ground and shadow class because the ground low brightness (in the 2nd and 3rd examples of Figure 12).

17

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT

Figures. 13 and 14 show an example of SegNet segmentation and the fusion compared with ground truth. In Figure 13 the area is healthy, so there are no samples of the symptom class. In this case, it can be observed that the fusion is identical to the visible and infrared estimation (idem for the ground truth). Unlike Figure 14 which is an area almost completely contaminated by the Mildew, as it can be seen, the ground truth is identical in both spectres, apart from the color code which is different. But for the SegNet output, the result for the symptomatic class detection is not identical in both ranges, which lead to merge the symptomatic visible and infrared classes. In addition, the fusion by intersection is generated by AND operator between the two segmentations output.

The quantitative results obtained for the visible, infrared, fusion by intersection and union segmentation experiments are presented in Table 4 and 5, respectively for leaf-level and grapevine-level. They show the results obtained in terms of the Recall, Precision, F1-Score/Dice coefﬁcient and Accuracy measures, which expressed in percentages.

As shown in the "Accuracy" column of Table 4, the different classes were generally better detected from the visible image (accuracy of 85.13%) than from the infrared image (accuracy of 78.72%). This difference in result is due to the fact that the visible image provides a better colorimetric description than the infrared image for the different classes studied. The fusion by union gave a result of 90.23%, this result is better than the visible, because the method takes the best of visible and infrared information. It can be noticed that symptoms appear at different locations in the visible and infrared spectral ranges. One interesting ﬁnding is that detection in both ranges is complementary, since fusion by union increases the detection performance. The fusion by intersection yields a score of 82.20%, this result less than the visible range, because the method is conditioned by the intersection of the visible and infrared, and in this case, it is the infrared result that has decreased its result. The fusion by intersection give an important information about the position of the commune symptom detection in visible and infrared. This ﬁnding can be used to strengthen the robustness of Mildew detection, where detection can be considered reliable if it is in both types of images. Besides, the fusion by union gives an idea about the quantitative detection.

In addition to measuring the affected areas at leaf level, the second type of assessment consists in testing the detection at vine plant level, as this helps to better manage certain operations in the vineyard. The results present in the Table 5 gives a better insight into the symptoms detection at the grapevine-level. The results show that the symptoms detection in the fusion by union is much better (the detection is more than 92.81%) compared to the ﬁne scale detection (leaf level), followed by the visible range (91.50%), then the infrared range (81.66%). As can be seen, the result of infrared and fusion by intersection are less than pixel-wise evaluation (Table 4). On the other hand, an increase of precision for the cases of the fusion by union and the visible can be observed.

Results obtained by the proposed method are likely to be consistent with several studies in the ﬁeld of remote sensing [47, 82, 83, 84, 44, 85] using the SegNet network. Indeed, the overall accuracy range obtained by these studies is between 70% and 90%. In addition, it has been observed that when the surface area is large, the detection result is better. Conversely, the smaller the surface area, the more the SegNet network has trouble to correctly detect the diseased area. A possible explanation for this might be, the lose of the resolution information of small areas during the downsampling and upsampling operations in the SegNet network. Another reason why the results are limited is the difﬁculty of realizing an accurate ground truth for learning and testing the network, but also the difﬁculty identifying an area in a low resolution (1cm/pixel) (in the case of images taken by a UAV at high altitude). In other remote sensing applications with large databases studies that have tested and compared several types of deep learning architecture [86, 84] such as FCN, U-Net, DeepLab, PSPNet, etc., obtained best results from the SegNet network for semantic segmentation.

In the proposed system, the fusion by intersection of the two modalities indicates the locations where symptoms were located at the same position in the visible and infrared images. In other words, fusion provides important information about areas where the system conﬁdence is higher for the disease detection. In other hand, it also provides information about areas where the disease has been detected only in one range (visible or infrared). Therefore, even after the establishment of the method for the diseases detection, the fusion by intersection remains more reliable class than the symptomatic classes detected in the visible or infrared range.

6.3 Runtime system


> **Table 6 presents the runtime results of all stages of the disease detection system.**

> For the image registration
step, the average runtime value was used to evaluate the overall system, because the image registration runtime
is variable from one pair of images to another. For the SegNet segmentation step, the runtime was multiplied
by two (× 2) because the process must segment both images (visible and infrared) and the GPU can only
handle one process at a time, unlike registration and fusion operations, where the processing is joint for the
two images (visible and infrared).
Unlike image registration, the runtime of the SegNet on a UAV image is
constant, at 140 seconds. This value is the same for both visible and infrared images. The fusion between the

18

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT

two segmented images takes less than 2 seconds; this runtime value includes the computation and saving the fusion ﬁle. The runtime of the disease detection system varies according to the image registration method chosen. This implies that for better accuracy of the results, an additional average processing of 47 seconds per image is necessary.

7 Conclusion

In this study, a new method based on optimized images registration and deep learning segmentation method has been proposed for detecting vine disease using multimodal UAV images (visible and infrared ranges). The method consists in three steps. The ﬁrst one is the images alignment, where an iterative algorithm based on an interest points detector has been developed. The second step is the segmentation of visible and infrared images based on the SegNet architecture to identify four classes: shadow, ground, healthy and symptomatic vine. Lastly, the third step consists in generating a disease map by fusion of the segmentations obtained from the visible and infrared images. This study showed that the proposed method enables the detection of vine symptoms using information from images of visible and infrared spectra. It provides a framework for the exploration of earlier detection and mapping of the vine diseases. One of the limitations of this research is the small size of the training sample which has reduced the performance of the deep learning segmentation. As future work, improvements could be made. The segmentation method can be improved by enriching the dataset (diversiﬁcation of disease samples), and also by testing other deep learning architectures for segmentation. Another possibility is the use of 3D information from the vine canopy, thus reducing false detection and improving the accuracy of image registration.

Acknowledgment

This work is part of the VINODRONE project supported by the Region Centre-Val de Loire (France). We gratefully acknowledge Region Centre-Val de Loire for its support.


## References

[1] Wasim Aktar, Dwaipayan Sengupta, and Ashim Chowdhury. Impact of pesticides use in agriculture: Their beneﬁts

and hazards. Interdisciplinary Toxicology, 2(1):1–12, 2009.

[2] David Pimentel, Lori McLaughlin, Andrew Zepp, Benyamin Lakitan, Tamara Kraus, Peter Kleinman, Fabius

Vancini, W. John Roach, Ellen Graap, William S. Keeton, and Gabe Selig. Environmental and economic effects of reducing pesticide use in agriculture. Agriculture, Ecosystems and Environment, 46(1-4):273–288, 1993.

[3] Mauro Hernández and Antoni Margalida. Pesticide abuse in Europe: Effects on the Cinereous vulture (Aegypius

monachus) population in Spain. Ecotoxicology, 17(4):264–272, 2008.

[4] S. D. Tyerman, R. K. Vandeleur, M. C. Shelden, J. Tilbrook, G. Mayo, M. Gilliham, and B. N. Kaiser. Water

transport & aquaporins in grapevine. 2009.

[5] Valérie Hofstetter, Bart Buyck, Daniel Croll, Olivier Viret, Arnaud Couloux, and Katia Gindro. What if esca

disease of grapevine were not a fungal disease? Fungal Diversity, 54:51–67, 2012.

[6] Julien Chuche and Denis Thiéry. Biology and ecology of the Flavescence dorée vector Scaphoideus titanus: A

review. Agronomy for Sustainable Development, 34(2):381–403, 2014.

[7] Cesare Gessler, Ilaria Pertot, and Michele Perazzolli. Plasmopara viticola: A review of knowledge on downy

mildew of grapevine and effective disease management. Phytopathologia Mediterranea, 50(1):3–44, 2011.

[8] Sarah L. MacDonald, Matthew Staid, Melissa Staid, and Monica L. Cooper. Remote hyperspectral imaging of

grapevine leafroll-associated virus 3 in cabernet sauvignon vineyards. Computers and Electronics in Agriculture, 130:109–117, 2016.

[9] F Cointault H. Al-Saddik, JC. Simon, O. Brousse. Damav : Un Projet Interregional De Detection De Foyers

Infectieux De Flavescence Doree Par Imagerie De Drone. Journée technique VITINNOV « Viticulture de précision : les capteurs à la loupe » DAMAV, pages 32–35, 2016.

[10] Mustafa Teke, Husne Seda Deveci, Onur Haliloglu, Sevgi Zubeyde Gurbuz, and Ufuk Sakarya. A short survey of

hyperspectral remote sensing applications in agriculture. RAST 2013 - Proceedings of 6th International Conference on Recent Advances in Space Technologies, (June):171–176, 2013.

19

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT

[11] Antonius G.T. Schut, Pierre C.Sibiry Traore, Xavier Blaes, and Rolf A. de By. Assessing yield and fertilizer

response in heterogeneous smallholder ﬁelds with UAVs and satellites. Field Crops Research, 221(February):98– 107, 2018. [12] M. Karpina, M. Jarzabek-Rychard, P. Tymków, and A. Borkowski. Uav-based automatic tree growth measurement

for biomass estimation. International Archives of the Photogrammetry, Remote Sensing and Spatial Information Sciences - ISPRS Archives, 41(July):685–688, 2016. [13] M. Dian Bah, Adel Haﬁane, and Raphael Canals. Weeds detection in UAV imagery using SLIC and the hough

transform. Proceedings of the 7th International Conference on Image Processing Theory, Tools and Applications, IPTA 2017, 2018-January:1–6, 2018. [14] Mehmet Do˘gan Altınba¸s and Tacha Serif. Detecting Defected Crops: Precision Agriculture Using Haar Classiﬁers

and UAV. In Irfan Awan, Muhammad Younas, Perin Ünal, and Markus Aleksy, editors, 13th International Conference, MobiWIS 2016 Vienna, Austria, August 22–24, 2016, volume 11673 of Lecture Notes in Computer Science, pages 27–40. Springer International Publishing, Cham, 2019. [15] Sachin D. Khirade and A. B. Patil. Plant disease detection using image processing. Proceedings - 1st International

Conference on Computing, Communication, Control and Automation, ICCUBEA 2015, pages 768–771, 2015. [16] Loyce Selwyn Pinto, Argha Ray, M. Udhayeswar Reddy, Pavithra Perumal, and P. Aishwarya. Crop disease

classiﬁcation using texture analysis. 2016 IEEE International Conference on Recent Trends in Electronics, Information and Communication Technology, RTEICT 2016 - Proceedings, pages 825–828, 2017. [17] Noa Schor, Avital Bechar, Timea Ignat, Aviv Dombrovsky, Yigal Elad, and Sigal Berman. Robotic Disease

Detection in Greenhouses: Combined Detection of Powdery Mildew and Tomato Spotted Wilt Virus. IEEE Robotics and Automation Letters, 1(1):354–360, 2016. [18] Jayme Garcia Arnal Barbedo. A Review on the Use of Unmanned Aerial Vehicles and Imaging Sensors for

Monitoring and Assessing Plant Stresses. Drones, 3(2):40, 2019. [19] Wenjing Zhu, Hua Chen, Izabela Ciechanowska, and Dean Spaner. Application of infrared thermal imaging for

the rapid diagnosis of crop disease. IFAC-PapersOnLine, 51(17):424–430, 2018. [20] Francisco Peñaranda, Valery Naranjo, Rafael Verdú-Monedero, Gavin R. Lloyd, Jayakrupakar Nallala, and

Nicholas Stone. Multimodal registration of optical microscopic and infrared spectroscopic images from different tissue sections: An application to colon cancer. Digital Signal Processing: A Review Journal, 68:1–15, 2017. [21] Shuang Wang, Dou Quan, Xuefeng Liang, Mengdan Ning, Yanhe Guo, and Licheng Jiao. A deep learning

framework for remote sensing image registration. ISPRS Journal of Photogrammetry and Remote Sensing, 145:148–164, 2018. [22] Chung Hsien Tsai and Yu Ching Lin. An accelerated image matching technique for UAV orthoimage registration.

ISPRS Journal of Photogrammetry and Remote Sensing, 128:130–145, 2017. [23] Fabián Inostroza, Silvana Díaz, Javier Cárdenas, Sebastián E. Godoy, and Miguel Figueroa. Embedded regis-

tration of visible and infrared images in real time for noninvasive skin cancer screening. Microprocessors and Microsystems, 55(January):70–81, 2017. [24] Yann LeCun, Léon Bottou, Yoshua Bengio, and Patrick Haffner. Gradient-based learning applied to document

recognition. Proceedings of the IEEE, 86(11):2278–2323, 1998. [25] Burkhard Monien, Robert Preis, and Stefan Schamberger. Approximation algorithms for multilevel graph

partitioning. Handbook of Approximation Algorithms and Metaheuristics, pages 60–1–60–16, 2007. [26] Matthew D Zeiler and Rob Fergus. Visualizing and Understanding Convolutional Networks BT - Computer

Vision–ECCV 2014. European Conference on Computer Vision (ECCV), 8689(Chapter 53):818–833, 2014. [27] Jihong Zhang and Hehua Zhu. An empirical-theoretical calculation method and full-scale veriﬁcation test for the

ultimate bearing capacity of an expanded pedestal uplift pile. Modern Tunnelling Technology, 51(6):50–57, 2014. [28] Guangyong Zeng, Yi He, Zongxue Yu, Xi Yang, Ranran Yang, and Lei Zhang. InceptionNet/GoogLeNet - Going

Deeper with Convolutions. Cvpr, 91(8):2322–2330, 2016. [29] Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun. Deep residual learning for image recognition.

Proceedings of the IEEE Computer Society Conference on Computer Vision and Pattern Recognition, 2016- December:770–778, 2016. [30] Andreas Kamilaris and Francesc X. Prenafeta-Boldú. Deep learning in agriculture: A survey. Computers and

Electronics in Agriculture, 147(February):70–90, 2018. [31] Chi Hua Chen, Hsu Yang Kung, and Feng Jang Hwang. Deep learning techniques for agronomy applications.

Agronomy, 9(3):1–5, 2019.

20

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT

[32] Srdjan Sladojevic, Marko Arsenovic, Andras Anderla, Dubravko Culibrk, and Darko Stefanovic. Deep Neural

Networks Based Recognition of Plant Diseases by Leaf Image Classiﬁcation. Computational Intelligence and Neuroscience, 2016, 2016.

[33] Yang Lu, Shujuan Yi, Nianyin Zeng, Yurong Liu, and Yong Zhang. Identiﬁcation of rice diseases using deep

convolutional neural networks. Neurocomputing, 267:378–384, 2017.

[34] Qi Yang, Liangsheng Shi, Jinye Han, Yuanyuan Zha, and Penghui Zhu. Deep convolutional neural networks for

rice grain yield estimation at the ripening stage using UAV-based remotely sensed images. Field Crops Research, 235(February):142–153, 2019.

[35] Alvaro Fuentes, Sook Yoon, Sang Cheol Kim, and Dong Sun Park. A robust deep-learning-based detector for

real-time tomato plant diseases and pests recognition. Sensors (Switzerland), 17(9), 2017.

[36] Sang Sik Lee, Yi Na Jeong, Su Rak Son, and Byung Kwan Lee. A self-predictable crop yield platform (SCYP)

based on crop diseases using deep learning. Sustainability (Switzerland), 11(13), 2019.

[37] M. Dian Bah, Eric Dericquebourg, Adel Haﬁane, and Raphael Canals. Deep learning based classiﬁcation system

for identifying weeds using high-resolution UAV imagery. Advances in Intelligent Systems and Computing, 857(July):176–187, 2019.

[38] Mohamed Kerkech, Adel Haﬁane, and Raphael Canals. Deep leaning approach with colorimetric spaces and

vegetation indices for vine diseases detection in UAV images. Computers and Electronics in Agriculture, 155(October):237–243, 2018.

[39] Vijay Badrinarayanan, Alex Kendall, and Roberto Cipolla. SegNet: A Deep Convolutional Encoder-Decoder Ar-

chitecture for Image Segmentation. IEEE Transactions on Pattern Analysis and Machine Intelligence, 39(12):2481– 2495, 2017.

[40] Hyeonwoo Noh, Seunghoon Hong, and Bohyung Han. Learning deconvolution network for semantic segmentation.

Proceedings of the IEEE International Conference on Computer Vision, 2015 International Conference on Computer Vision, ICCV 2015:1520–1528, 2015.

[41] Olaf Ronneberger, Philipp Fischer, and Thomas Brox. U-net: Convolutional networks for biomedical image

segmentation. Lecture Notes in Computer Science (including subseries Lecture Notes in Artiﬁcial Intelligence and Lecture Notes in Bioinformatics), 9351:234–241, 2015.

[42] Alex Kendall, Vijay Badrinarayanan, and Roberto Cipolla. Bayesian SegNet: Model Uncertainty in Deep

Convolutional Encoder-Decoder Architectures for Scene Understanding. 2019.

[43] Iñigo Alonso and Ana C. Murillo. EV-SegNet: Semantic Segmentation for Event-based Cameras. 2018.

[44] Nicolas Audebert, Bertrand Le Saux, and Sébastien Lefèvre. Segment-before-detect: Vehicle detection and

classiﬁcation through semantic segmentation of aerial images. Remote Sensing, 9(4), 2017.

[45] Hao Guo, Guo Wei, and Jubai An. Dark spot detection in SAR images of oil spill using segnet. Applied Sciences

(Switzerland), 8(12), 2018.

[46] Hai-Duong Nguyen, In-Seop Na, and Soo-Hyung Kim. Hand Segmentation and Fingertip Tracking from Depth

Camera Images Using Deep Convolutional Neural Network and Multi-task SegNet.

[47] Zhenrong Du. Training SegNet for Cropland Classiﬁcation of High Resolution Remote Sensing Images. 21st

International Conference on Geographic Information Science (AGILE 2018), pages 1–6, 2018.

[48] Po-an Wei, Ching-chih Tsai, and Feng-chun Tai. Autonomous Navigation of an Indoor Mecanum-Wheeled Omni-

directional Robot Using Segnet. Proceedings of 2019 National Symposium on System Science and Engineering, pages 2–4, 2019.

[49] Enzo Ferrante and Nikos Paragios. Slice-to-volume medical image registration: A survey. Medical Image Analysis,

39:101–123, 2017.

[50] Barbara Zitová and Jan Flusser. Image registration methods: A survey. Image and Vision Computing, 21(11):977–

1000, 2003.

[51] Suma Dawn, Vikas Saxena, Bhudev Sharma, and Information Technology. Remote Sensing Image Registration

Techniques : Survey. Image and Signal Processing. Springer Berlin Heidelberg, 6134(c):103–112, 2010.

[52] Sayan Nag. Image Registration Techniques: A Survey. 2017.

[53] Xuezhi Wang, Weiping Yang, Ashley Wheaton, Nicola Cooley, and Bill Moran. Efﬁcient registration of optical and

IR images for automatic plant water stress assessment. Computers and Electronics in Agriculture, 74(2):230–237, 2010.

21

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT

[54] Hector Erives and Glenn J. Fitzgerald. Automated registration of hyperspectral images for precision agriculture.

Computers and Electronics in Agriculture, 47(2):103–119, 2005.

[55] Youwen Zhuang, Kun Gao, Xianghu Miu, Lu Han, and Xuemei Gong. Infrared and visual image registration

based on mutual information with a combined particle swarm optimization - Powell search algorithm. Optik, 127(1):188–191, 2016.

[56] Manikantha Teja Lingamsetti* Sreenu and Tadivaka Teja. Control of Brushless DC Motor with Direct Torque

and Indirect Flux using SVPWM Technique. Indian Journal of Science and Technology,, 8(November):507–515, 2015.

[57] Mohammad Saleh Javadi, Zulaikha Kadim, Hon Hock Woon, Khairunnisa Mohamed Johari, and Norshuhada

Samudin. An Automatic Robust Image Registration Algorithm for Aerial Mapping. International Journal of Image and Graphics, 15(02):1540002, 2015.

[58] F. A. Onyango, F. Nex, M. S. Peter, and P. Jende. Accurate estimation of orientation parameters of UAV images

through image registration with aerial oblique imagery. International Archives of the Photogrammetry, Remote Sensing and Spatial Information Sciences - ISPRS Archives, 42(1W1):599–605, 2017.

[59] Zhuoqian Yang, Tingting Dan, and Yang Yang. Multi-temporal remote sensing image registration using deep

convolutional features. IEEE Access, 6:38544–38555, 2018.

[60] Anne Katrin Mahlein. Plant disease detection by imaging sensors – Parallels and speciﬁc demands for precision

agriculture and plant phenotyping. Plant Disease, 100(2):241–254, 2016.

[61] E. C. Oerke, P. Fröhling, and U. Steiner. Thermographic assessment of scab disease on apple leaves. Precision

Agriculture, 12(5):699–715, 2011.

[62] Amanda Heemann Junges, Jorge Ricardo Ducati, Cristian Scalvi Lampugnani, and Marcus André Kurtz Almança.

Detection of grapevine leaf stripe disease symptoms by hyperspectral sensor. Phytopathologia Mediterranea, 57(3):399–406, 2018.

[63] Salvatore F. di Gennaro, Enrico Battiston, Stefano di Marco, Osvaldo Facini, Alessandro Matese, Marco Nocentini,

Alberto Palliotti, and Laura Mugnai. Unmanned Aerial Vehicle (UAV)-based remote sensing to monitor grapevine leaf stripe disease within a vineyard affected by esca complex. Phytopathologia Mediterranea, 55(2):262–275, 2016.

[64] Johanna Albetis, Sylvie Duthoit, Fabio Guttler, Anne Jacquin, Michel Goulard, Hervé Poilvé, Jean Baptiste Féret,

and Gérard Dedieu. Detection of Flavescence dorée grapevine disease using Unmanned Aerial Vehicle (UAV) multispectral imagery. Remote Sensing, 9(4):308, 2017.

[65] Johanna Albetis, Anne Jacquin, Michel Goulard, Hervé Poilvé, Jacques Rousseau, Harold Clenet, Gerard Dedieu,

and Sylvie Duthoit. On the potentiality of UAV multispectral imagery to detect Flavescence dorée and Grapevine Trunk Diseases. Remote Sensing, 11(1):0–26, 2019.

[66] Hania Al-Saddik, Jean Claude Simon, and Frederic Cointault. Development of spectral disease indices for

‘ﬂavescence dorée’ grapevine disease identiﬁcation. Sensors (Switzerland), 17(12), 2017.

[67] Hania Al-Saddik, Anthony Laybros, Bastien Billiot, and Frederic Cointault. Using image texture and spectral

reﬂectance analysis to detect Yellowness and Esca in grapevines at leaf-level. Remote Sensing, 10(4), 2018.

[68] Hania Al-saddik. Assessment of the optimal spectral bands for designing a sensor for vineyard disease detection :

the case of ‘ Flavescence dorée ’. Precision Agriculture, (0123456789), 2018.

[69] Florian Rançon, Lionel Bombrun, Barna Keresztes, and Christian Germain. Comparison of SIFT encoded and

deep learning features for the classiﬁcation and detection of esca disease in Bordeaux vineyards. Remote Sensing, 11(1):1–26, 2019.

[70] Richard Szeliski. Image Alignment and Stitching: A Tutorial. Springer US, Boston, MA, 2006.

[71] Pablo F. Alcantarilla, Jesús Nuevo, and Adrien Bartoli. Fast explicit diffusion for accelerated features in nonlinear

scale spaces. BMVC 2013 - Electronic Proceedings of the British Machine Vision Conference 2013, 2013.

[72] David G Lowe. Distinctive Image Features from Scale-Invariant Keypoints. International Journal of Computer

Vision, 60(2):91–110, nov 2004.

[73] M Jakab. Planar object recognition using local descriptor based on histogram of intensity patches. Proceedings of

the 17th Central European Seminar on ..., 2013.

[74] Martin Hasenbusch, Andrea Pelissetto, and Ettore Vicari. The critical behavior of 3D Ising spin glass models:

Universality and scaling corrections. Journal of Statistical Mechanics: Theory and Experiment, 2008(2):2564– 2571, 2008.

22

Vine disease detection in UAV multispectral images with deep learning segmentation approachA PREPRINT

[75] Adrien Bartoli Pablo Fernández Alcantarilla and Andrew J Davison. LNCS 7577 - KAZE Features. pages 1–14,

2012. [76] Sven Grewenig, Joachim Weickert, and Andrés Bruhn. From box ﬁltering to fast explicit diffusion. Lecture

Notes in Computer Science (including subseries Lecture Notes in Artiﬁcial Intelligence and Lecture Notes in Bioinformatics), 6376 LNCS:533–542, 2010. [77] Xin Yang and Kwang Ting Tim Cheng. Local difference binary for ultrafast and distinctive feature description.

IEEE Transactions on Pattern Analysis and Machine Intelligence, 36(1):188–194, 2014. [78] Martin a Fischler and Robert C Bolles. Paradigm for Model. Communications of the ACM, 24(6):381–395, 1981. [79] Kenton Ross. Geopositional Statistical Methods Lockheed Martin Integrated Systems & Solutions. 2004. [80] Ryan Dellana and Kaushik Roy. Data augmentation in CNN-based periocular authentication. Proceedings of the

6th International Conference on Information Communication and Management, ICICM 2016, pages 141–145, 2016. [81] Shaharyar Ahmed Khan Tareen and Zahra Saleem. A comparative analysis of SIFT, SURF, KAZE, AKAZE,

ORB, and BRISK. 2018 International Conference on Computing, Mathematics and Engineering Technologies: Invent, Innovate and Integrate for Socioeconomic Development, iCoMET 2018 - Proceedings, 2018-January:1–10, 2018. [82] Jie Jiang, Chengjin Lyu, Siying Liu, Yongqiang He, and Xuetao Hao. RWSNet: a semantic segmentation network

based on SegNet combined with random walk for remote sensing. International Journal of Remote Sensing, 00(00):1–19, 2019. [83] D. Marmanis, K. Schindler, J. D. Wegner, S. Galliani, M. Datcu, and U. Stilla. Classiﬁcation with an edge:

Improving semantic image segmentation with boundary detection. ISPRS Journal of Photogrammetry and Remote Sensing, 135:158–172, 2018. [84] Dengfeng Chai, Shawn Newsam, Hankui K. Zhang, Yifan Qiu, and Jingfeng Huang. Cloud and cloud shadow

detection in Landsat imagery based on deep convolutional neural networks. Remote Sensing of Environment, 225(September 2018):307–316, 2019. [85] Andres Milioto, Philipp Lottes, and Cyrill Stachniss. Real-Time Semantic Segmentation of Crop and Weed for

Precision Agriculture Robots Leveraging Background Knowledge in CNNs. Proceedings - IEEE International Conference on Robotics and Automation, pages 2229–2235, 2018. [86] Xu Ma, Xiangwu Deng, Long Qi, Yu Jiang, Hongwei Li, Yuwei Wang, and Xupo Xing. Fully convolutional

network for rice seedling and weed image segmentation at the seedling stage in paddy ﬁelds. PLoS ONE, 14(4):1–13, 2019.

23
