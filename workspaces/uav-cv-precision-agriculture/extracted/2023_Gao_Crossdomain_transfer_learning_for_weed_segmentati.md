---
workspace_id: SCI-000489
doi: 10.1016/j.eswa.2023.122980
title: Cross-domain transfer learning for weed segmentation and mapping in precision
  farming using ground and UAV images
authors:
- family_name: Gao
  given_name: Junfeng
  orcid: https://orcid.org/0000-0002-5622-8210
- family_name: Liao
  given_name: Wenzhi
  orcid: https://orcid.org/0000-0002-2183-0324
- family_name: Nuyttens
  given_name: David
  orcid: https://orcid.org/0000-0002-4531-0526
- family_name: Lootens
  given_name: Peter
  orcid: https://orcid.org/0000-0002-3275-3459
- family_name: Xue
  given_name: Wenxin
  orcid: null
- family_name: Alexandersson
  given_name: Erik
  orcid: https://orcid.org/0000-0001-6320-2492
- family_name: Pieters
  given_name: Jan
  orcid: https://orcid.org/0000-0003-4034-9269
year: 2023
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:21:25.341266+00:00'
---

# Cross-domain transfer learning for weed segmentation and mapping in precision farming using ground and UAV images

Expert Systems With Applications 246 (2024) 122980

Contents lists available at ScienceDirect

Expert Systems With Applications

journal homepage: www.elsevier.com/locate/eswa

Cross-domain transfer learning for weed segmentation and mapping in  precision farming using ground and UAV images

Junfeng Gao a,b,*, Wenzhi Liao c,d,*, David Nuyttens e, Peter Lootens e, Wenxin Xue a,*,  Erik Alexandersson f, Jan Pieters g

a Key Laboratory of Tobacco Pest Monitoring & Integrated Management, Tobacco Research Institute of Chinese Academy of Agricultural Sciences, Qingdao 266101,  China  b Lincoln Agri-Robotics (LAR), Lincoln Institute for Agri-Food Technology, University of Lincoln, Lincoln, UK  c Flanders Make, Kortrijk, Belgium  d Department of Telecommunications and Information Processing, Ghent University, Ghent, Belgium  e Flanders Research Institute for Agriculture, Fisheries and Food (ILVO), Merelbeke, Belgium  f Department of Plant Breeding, Swedish University of Agricultural Sciences, Alnarp, Sweden  g Biosystems Engineering Group, Ghent University, Ghent, Belgium

A R T I C L E I N F O

A B S T R A C T

Keywords:  Deep learning  Remote sensing  Cross-domain learning  Weighted loss  Feature visualization  Weed mapping

Weed and crop segmentation is becoming an increasingly integral part of precision farming that leverages the  current computer vision and deep learning technologies. Research has been extensively carried out based on  images captured with a camera from various platforms. Unmanned aerial vehicles (UAVs) and ground-based  vehicles including agricultural robots are the two popular platforms for data collection in fields. They all  contribute to site-specific weed management (SSWM) to maintain crop yield. Currently, the data from these two  platforms is processed separately, though sharing the same semantic objects (weed and crop). In our paper, we  have proposed a novel method with a new deep learning-based model and the enhanced data augmentation  pipeline to train field images alone and subsequently predict both field images and UAV images for weed seg­ mentation and mapping. The network learning process is visualized by feature maps at shallow and deep layers.  The results show that the mean intersection of union (IOU) values of the segmentation for the crop (maize),  weeds, and soil background in the developed model for the field dataset are 0.744, 0.577, 0.979, respectively,  and the performance of aerial images from an UAV with the same model, the IOU values of the segmentation for  the crop (maize), weeds and soil background are 0.596, 0.407, and 0.875, respectively. To estimate the effect on  the use of plant protection agents, we quantify the relationship between herbicide spraying saving rate and grid  size (spraying resolution) based on the predicted weed map. The spraying saving rate is up to 90 % when the  spraying resolution is at 1.78 × 1.78 cm2. The study shows that the developed deep convolutional neural network  could be used to classify weeds from both field and aerial images and delivers satisfactory results. To achieve this  performance, it is crucial to perform preprocessing techniques that reduce dataset differences between two  distinct domains.


## 1. Introduction

resources, new smart farming approaches are highly needed to increase  yield while minimizing environmental impacts. Precision crop farming  (PCF) is a whole-farm management approach using information tech­ nology, satellite position data, remote and proximal sensing data com­ bined in smart decision tools, and precision application techniques. The

Weeds generally emerge in natural fields. They cause a tremendous  loss in crop yield and quality (Oerke, 2006). To sustain an increasing  worldwide population with sufficient crop production with limited land

* Corresponding authors at: Key Laboratory of Tobacco Pest Monitoring & Integrated Management, Tobacco Research Institute of Chinese Academy of Agricultural  Sciences, Qingdao 266101, China (W. Xue, J. Gao). Lincoln Institute for Agri-Food Technology, University of Lincoln, Lincoln, UK (J. Gao). Flanders Make, Kortrijk,  Belgium (W. Liao).

E-mail addresses: jugao@lincoln.ac.uk (J. Gao), wenzhi.liao@flandersmake.be (W. Liao), david.nuyttens@ilvo.vlaanderen.be (D. Nuyttens), peter.lootens@ilvo.  vlaanderen.be (P. Lootens), xuewenxin@caas.cn (W. Xue), erik.alexandersson@slu.se (E. Alexandersson), jan.pieters@ugent.be (J. Pieters).

https://doi.org/10.1016/j.eswa.2023.122980  Received 1 November 2022; Received in revised form 9 November 2023; Accepted 15 December 2023

Available online 23 December 2023 0957-4174/© 2023 The Author(s). Published by Elsevier Ltd. This is an open access article under the CC BY license (http://creativecommons.org/licenses/by/4.0/).

J. Gao et al.

Expert Systems With Applications 246 (2024) 122980

main objective of PCF for weeding is to allocate the right doses of input  at the right time and in the right position for improving crop perfor­ mance and environmental sustainability (Zhang et al., 2002).

Ground-based images can be collected with a ground-based vehicle.  The collected images are typically used for developing weed recognition  systems in ground-based platforms such as autonomous weeding robots  and spot spraying tractors. UAVs enable mapping weeds with a global  view based on orthophotos generated from collected overlapping im­ ages. Data from these two platforms (UAV-based, ground-based) is  typically processed independently for weed detection. This is because  the two data sources have their characteristics in terms of resolution and  scale. For example, the training samples (tiles or regions) for aerial weed  mapping with deep learning, are usually randomly cropped from an  orthomosaic map generated by aligning overlapped aerial images. They  are typically in low resolution with blurry object boundaries, or they  might have artifacts from the process of image alignment to produce  orthomosaic imagery. By contrast, samples for field weed detection are  captured in a closer overhead view, and therefore are having a higher  image resolution. The resolution difference also impacts the process of  annotation for training networks. The annotation of the cropped small  tiles (low-resolution) usually consumes more time and is error-prone  compared to ground-based proximal images (high-resolution) due to  spatial resolution differences.

Conventional weed managements rely on whole-field management  (Shaw, 2005) without considering spatial differences in weed distribu­ tion. Site-specific weed management (SSWM), a subfield of PCF, refers  to the spatially variable application of a weed management strategy  without spraying chemicals uniformly (Burgos-artizzu et al., 2011). It  allows appropriate use of chemicals and thereby potential reduction of  adverse impacts to the environments. However, one of the main chal­ lenges to achieve SSWM is developing a reliable and accurate weed  recognition system under unstructured environments such as field  conditions. To address this challenge, a few studies have been attemp­ ted, mainly using computer vision with RGB images (Gao et al., 2020),  multispectral and hyperspectral images (Gao, Nuyttens, et al., 2018;  Lauwers et al., 2022; Zhang et al., 2019), and spectroscopy in visible and  near-infrared regions (Shapira et al., 2013). In addition, machine  learning has become an increasingly popular approach for precise real-  time weed and crop detection in fields (Wang et al., 2019). A typical  processing procedure based on machine learning includes pre-  processing, feature extraction, classification or recognition. While this  learning-based approach has made further improvements for weed  recognition compared to a system developed only based on image pro­ cessing, its effectiveness highly relies on robust feature extraction which  requires careful hand-crafted designs and significant domain expertise.  By contrast, deep learning, a subfield of machine learning, enables hi­ erarchical learning features and discovering potential complex patterns  automatically from large datasets (LeCun et al., 2015). It has shown  impressive advancements in solving various complex problems. In the  agricultural domain, deep learning is also a promising technique with  growing popularity. Kamilaris and Prenafeta-Boldú (2018) carried out a  survey about deep learning in agricultural applications. It indicates that  deep learning provides higher accuracy, outperforming typically ma­ chine learning techniques, in weed detection(Gao, 2020; Gao et al.,  2020; Milioto et al., 2017), crop disease recognition (Gao et al., 2021;  Van De Vijver et al., 2020, 2022) and plant stress phenotyping (Singh  et al., 2018).

Despite of sharing a same task for weed detection, these differences  bring the challenge of developing and training one network architecture  to achieve a satisfactory performance in the two domains (field and  aerial images). Bridging the domain gap from ground-based images to  aerial images for weed mapping is crucial for exploiting two different  datasets, transferring knowledge learned between the two similar tasks.  To the best of our knowledge, no specific studies have attempted to  connect or utilise these two different datasets for weed mapping.

In this study, we proposed a pipeline to pre-process field images in  order to develop an effective deep convolutional neural network with a  weighted loss function for weed and crop semantic segmentation in  precision farming. Specifically, our model was developed based on field  images alone and then applied to predict unseen tiles from the ortho­ mosaic imagery with larger mapping areas but at lower spatial resolu­ tion. Then the weed map was generated from the tile predictions.  Furthermore, different models were compared, and the optimal class  weight was determined for weed and crop segmentation. Moreover,  feature maps from different layers in the developed model were dis­ played for its accountability and interpretability.

Generally, weed recognition with deep learning can be categorized  into two groups: ground-based and aerial remote or proximal sensing.  Satellite imagery could be utilized for monitoring weed invasion at a  large scale, but it is difficult to map weed individuals due to low spatial  resolution (Peerbhay et al., 2016). In terms of ground-based systems,  Wang et al., (2007) developed a real-time, embedded weed detection  system based on a tractor platform with an integrated sprayer.  Furthermore, mobile robots have become widely utilized for in-field  scenarios to perform difficult tasks while maintaining high-level accu­ racy and robustness (Emmi & Gonzalez-de-Santos, 2017). The use of  ground-based autonomous robots can decrease the human labour input  required for weed management. Typically, a vision-based system in  combination with deep learning is one of the main components in field  robots (Bawden et al., 2017; Lottes et al., 2018). A field robotic platform  is also commonly used to collect images, providing a large number of  datasets for deep learning research. Recently, unmanned aerial vehicles  (UAVs) are becoming an increasingly popular tool for various remote  sensing applications. Compared to ground-based robotic platforms,  UAVs have been considered more efficient as they allow fast data  acquisition with relatively high resolution and low cost (Torres-S´anchez  et al., 2015). Perez-Ortiz et al., (2016) discussed patterns and features  for inter- and intra-row weed mapping using UAV imagery. Gao, Liao,  et al. (2018) fused pixel- and object-based features from aerial images  with a random forest classifier for weed mapping in a maize field.  Furthermore, Dian Bah et al., (2018) explored unsupervised data  labelling obtained from inter-row weeds for weed mapping on drone-  based aerial images. In addition, an end-to-end semantic weed map­ ping framework was developed based on aerial multispectral images and  deep learning (Sa, Chen, et al., 2018; Sa, Popovi´c, et al., 2018).

The main contributions of our work are summarized as follows:

(1) It bridges the gap between using ground-based field images (high-

resolution data) and UAV images (low-resolution data) for weed  and crop semantic segmentation which has not been fully  exploited so far. This cross-domain learning allows for the gen­ eration of weed maps with UAV-based remote sensing data by  using different source datasets for prediction performance by  bootstrapping.   (2) It develops a deep convolution neural network that integrates a

custom image pre-processing pipeline to remedy the influence of  the differences between the two domains for predictions.   (3) It systematically investigates and determines the relationships

between the grid size (spraying resolution) based on the pre­ dicted weed map and herbicide spraying saving rate for the site-  specific weed management (SSWM).   (4) It provides a comprehensive analysis to discuss what features

were learned by the model based on layer-wise visualization. This  analysis contributes to the development of deep learning and  remote sensing in precision farming tasks.


## 2. Materials and methods

2.1. Field image collection

The field images were manually collected with a visual camera  (Nikon D7200) under different lighting conditions from two maize fields

2

J. Gao et al.

Expert Systems With Applications 246 (2024) 122980

near Ghent and two maize fields near Merelbeke in Belgium in 2018. The  growth stages of maize plants range from 2 unfolded leaves to 5  unfolded leaves. The distance between the camera and the ground was  around 1 m which is not strictly fixed in order to create more variations  in the images. Multiple weed species were found in these fields. In our  study, we only classified three classes (weed, maize, soil) regardless of  different weed species. More than 10,000 images (48G) were randomly  collected during the early growth stages of maize crop in these four  maize fields.

of datasets share the same object classes (soil, crop, weed), but they  represent the main differences in object scales, resolution. Intuitively,  one straightforward approach is to downsample (from Fig. 3(a) to Fig. 3  (c)) and then apply image enhancement using the convertScaleAbs  (alpha = 1.3, beta = 50, in Fig. 3(d)) and the Gaussian smoothing with a  7x7 kernel functions in Opencv. In addition, in the thread of aerial im­ agery, the orthomosaic imagery was cropped into small patches with a  16x16 cutting grid. Then the small patches were resized to 512x512. The  resized images were enhanced with the Gamma correction (power law  transform, gamma = 0.8. in Fig. 3(i)). All these operations were done  before the images were fed into networks for training.

2.2. UAV-based image collection

Regarding the post processing to refine the predictions from the  models, we have employed a Conditional Random Field (CRF). A step-  by-step explanation of how CRFs are applied to the segmentation re­ sults is described in Section 2.6.

The UAV-based image data was collected at the experimental fields  of the Flanders Research Institute for Agricultural, Fisheries, and Food  Research (ILVO) in the agricultural region of Merelbeke, East-Flanders  Province, Belgium in 2016. Several weed species like bindweeds  (Convolvulus), lamb’s quarters (Chenopodium album) and crabgrass  (Digitaria sanguinalis) species were naturally infested in the field plots. A  12 coaxial rotors UAV (Hydra-12 Onyxstar, Mikrokopter, Germany),  equipped with a lightweight visual camera (Sony Alpha 6000, Sony,  Japan), was employed to collect aerial imagery at an altitude of 20 m  above ground. The details of the field experiments and imaging pa­ rameters can be seen in Gao et al., (2018a). The two cameras’ technical  specifications and parameter settings are listed in Table 1. The UAV flew  over the maize experimental field every week from the emergency of  maize plants until the maize canopy covered the crop rows. The maize  growth stage of UAV data in this study is 3–4 unfolded leaves, similar as  field imagery Fig. 1.

2.4. Encoder-decoder network architecture for semantic segmentation

Fully convolutional networks (FCN) are suitable for field and remote  sensing imagery and have demonstrated promising results in the studies  for semantic segmentation of very high-resolution UAV imagery (Huang  et al., 2019; Sa, Chen, et al., 2018). FCN models, such as FCN32s, FCN-  16s and FCN-8s (Long et al., 2015), DeconvNet (Noh et al., 2015), and  SegNet (Badrinarayanan et al., 2017), generally have an encoder-  decoder network architecture. The encoder comprises a series of con­ volutional operations, activation and pooling operations. Semantic  features from low-level to high-level could be extracted at the end of the  encoder process. Because of pooling layers, the spatial resolution of the  encoder output is smaller than the original input images. By contrast, the  decoder part upsamples the features learned from the encoder part and  generates the final prediction results with the same spatial size as the  original input images. The upsampling layers, such as deconvolution  layer, in the decoder are also capable of learning mapping from feature  maps to semantic segmentation results. The proposed network, illus­ trated in Fig. 4, also has the encoder-decoder symmetric architecture.1

2.3. Overall workflow

Fig. 2 depicts the entire pipeline implemented in this paper. There  are two main components in the pipeline. One is training the network  using field images alone, and then the pre-trained model is used to  predict both field images and orthomosaic images. For the training  dataset, we did not directly use original field images (6000*4000)  because of the processing difficulties associated with memory manage­ ment in available GPUs. We instead first resized original images and  then randomly cropped image tiles (512*512) from the resized images  (1200*800). There are 5000 field image tiles (512*512) in total which  were used to train the deep convolutional neural network. For the  validation dataset, 621 field images were used. After the network was  trained, not only its performance was evaluated in the field test dataset,  but also its generalizability was validated by directly testing UAV-based  imagery which had never been seen before by the network. In terms of  orthomosaic image generation, the Agisoft PhotoScan v1.2.3 (Agisoft  LLC, St. Petersburg, Russia) software was employed. The steps to process  aerial images in Agrisoft PhotoScan include image alignment, dense  cloud building, 3D mesh building, texture building, digital elevation  model building and finally orthomosaic photo generation (blending  mode). We set high accuracy and 4000 key points limited for image  alignment (Gao, Liao, et al., 2018). The other parameters were set by  default in PhotoScan.

There are 39 layers in total with 29 convolutional layers (14 for encode  part, 15 for decode part), 5 max pooling layers and 5 upsampling layers.  Each convolutional layer (1–28) is followed by batch normalization and  rectified linear unit (ReLu) activation operations. The last convolutional  layer, however, employs “Softmax” as activation function. The size of all  the kernels in the convolutional layers is 3 × 3. The indices (the location  of the maximum feature value in every max pooling operation) are  recorded during the max pooling (2 × 2) layers and then are passed to  the corresponding upsampling layers (2 × 2), which is similar to SegNet  (Badrinarayanan et al., 2017). In this way, substantial spatial informa­ tion is saved for more accurate object boundary prediction. Further­ more, we use skip connections to concatenate former layers together  with upsampling layers in the decoder part. This could fuse the fine-  grained features from former layers, which is different from the Seg­ Net using sum operations instead. There are 42,037,391 parameters in  total with 42,018,441 trainable parameters and 18,950 non-trainable  parameters. The number of parameters is higher than the other net­ works (FCNs, UNet and SegNet). The data augmentation was used and  the loss values in the training and validation datasets were monitored to  determine the timing to stop training further for preventing the risk of  overfitting.

It is critical to apply the pre-processing for field images to close the  gap between field images and aerial images to the utmost. The two types

2.5. Weighted loss


> **Table 1**

> Camera types and settings in two experiments.

Designing the loss function is key for training a robust and high-  performance network. The most commonly used loss function for se­ mantic segmentation is pixel-wise cross-entropy loss. In our study, the

Ground-based monitoring  UAV-based monitoring

Camera  Nikon D7200  Sony Alpha 6000  Resolution  6000 × 4000 pixels  6000 × 4000 pixels  Lens type  AF-S-NIKKOR 18–140 mm  Sony E 35 mm F 1.8 OSS  Shutter time  1/800 s  1/2000 s  ISO  1600  320  GSD  ___  1.78 mm/pixel


## 1 https://github.com/JunfengGaolab/weed-mapping-with-cross-domain-lear

ning-/tree/master.

3

J. Gao et al.

Expert Systems With Applications 246 (2024) 122980

Fig. 1. Field and UAV experiments data collection location.

Fig. 2. The diagram of this study. The network was trained with field images alone and predicted both field images and cropped aerial images to map weeds in fields.

frequency of appearance for each class (weed, maize and soil back­ ground) is heavily imbalanced. Generally, the number of soil back­ ground pixels is far more than pixels of crop and weed in field images at  early growth stages of the crop. Just using the standard loss function  without adaption would make a deep neural network model tend to only  correctly classify dominant class pixels (soil background), ignoring the  importance of weed and crop pixels. In order to draw the same attention  in different classes for network training, a weighted loss function was  finally used in the training process.

∑ C

∑ N

L = −1

Wc*yo,clogpo,c (1)

N

i=1

c=1

where N is the number of observations, C is the number of classes (weed,  crop and soil), Wc is the weight for class c, y is the binary indicator (0 or  1) if class label is corrected classified for observation o, p is predicted  probability observation o being of class c. we quantified the weights for  each class by the following calculation.

4

J. Gao et al.

Expert Systems With Applications 246 (2024) 122980

Fig. 3. Visualization of the proposed preprocessings to reduce differences between the two datasets.

Fig. 4. The developed encoder and decoder based neural network architecture.

2.6. Post-processing with fully connected conditional random fields  (CRFs)

Wc = log max(Pi, i ∈{1, ⋯C})

(2)

Pc

where Pc is the number of pixels belonging to class c. Based on the sta­ tistics of pixels in the training dataset, the weights for weed, crop and  soil background classes are 2.5, 1.5, and 1, respectively.

CRF has traditionally been used to smooth noisy segmentation edges  (Kohli et al., 2009), typically coupling nodes in the neighborhood fa­ voring the same label assignment to spatially proximal pixels. However,  these short-range of CRFs is to process the spurious segmentation results

5

J. Gao et al.

Expert Systems With Applications 246 (2024) 122980

of weak classifiers built on top of local hand-crafted features (L.-C. Chen  et al., 2018). In order to overcome this limitation, fully connected CRFs  are designed to connect to a deep convolutional neural network. By  combining single pixel prediction and shared structure through unary  and pairwise terms, the fully connected CRFs establish pairwise poten­ tial on all pairs of pixels in an image (Kr¨ahenbühl & Koltun, 2011). The  energy function for a model is

GPU (16 GB memory). The network was trained with the Adam opti­ mizer (Kingma & Ba, 2015) using the initial learning rate of 0.005. In  order to achieve the optimal converged point, the learning rate was  dropped by 0.1 to maintain further learning once the loss value stays the  same in 10 consecutive batches. The exponential decay rates for the first-  and second-moment estimates were set as 0.9 and 0.999, respectively.  The batch size was set as 24 and the number of epochs was 300. All the  models in this paper were fine-tuned based on initial weights of VGG16  model trained in ImageNet dataset and same hyperparameters.

∑

∑

(

)

(3)

E(x) =

θi(xi) +

xi, xj

θij

i

ij


## 3. Results

Where x stands for label assignment for each pixel, θi(xi) represents  pixel-wise unary likelihood which equal to −logP(xi) where P(xi) is label  assignment probability at pixel i calculated by the model. θij

3.1. Field-to-field prediction

(

)

is the  unary potential, given in below.

xi, xj

In our experiment, three types of semantic classes (soil, weed, and  maize) were investigated with the deep neural network-based pixel-wise  classifications. Table 2 presents the detailed metrics of the three classes  and the overall performances of the deep neural networks. In the FCN  network family, we can see the FCN-8 s (OA = 0.797, mIOU = 0.736)  provided better predictions compared to FCN-16 s (OA = 0.768, mIOU  = 0.704) and FCN-32 s (OA = 0.749, mIOU = 0.680), indicating that  increasing the number of upsampling or unpooling layers is one of the  effective ways to achieve finer predictions. The approach of Long et al.,  (2015) has similar conclusions. The proposed network performed best  among other networks with 0.859 mOA and 0.767 mIOU. Interestingly,  UNet obtained higher mOA (0.820) compared to SegNet (mOA = 0.811).  However, its mIOU value (0.698) is relatively lower than SegNet  (0.750). In terms of predictions in different classes, it is obvious that soil  background class is much more effortless to distinguish for networks due  to its large colour differences compared to plant classes. All the networks  achieved above 0.970 IOU values for the soil background class. Weeds  were more difficult to recognise compared to the maize crop. This is  mainly because maize crop tends to have similar colour and morpho­ logical characteristics while weeds generally present larger differences  in terms of size, growth stage and morphology as multiple weed species  appeared in our study fields. Thus, the network learns well maize crop  patterns, leading to better performance in classification. Fig. 5 displays  the prediction of the examples from the test field dataset. The proposed  network is able to detect small-sized weeds and produces a precise  segmentation boundary. Moreover, it also performed well in high oc­ clusion examples such as in Fig. 5(b) and (d) (occlusions between weed  and crop) and in Fig. 5(c) (occlusions between crop and crop). These are  generally quite challenging images to segment well by using conven­ tional image processing algorithms. In addition, it shows that the model  performed well under different soil backgrounds and lighting condi­ tions. Therefore, we concluded that the proposed network is very  capable of weed and crop classification in the early growth stage under  field conditions, despite the heterogeneous weed patterns.

Efficient interference is obtained by establishing pairwise potential  while employing a fully connected graph such as connecting all pairs of  image pixels i, j. A linear combination of Gaussian kernels can be used to  qualify the pairwise edge potential (Kr¨ahenbühl & Koltun, 2011).

[

(

2

(

)

(

)

−⃒⃒ pi −pj⃒⃒

= μ

xi, xj

xi, xj

θi,j

w1exp

2σ2 α

)

) ]

(

2

2

−⃒⃒ qi −qj⃒⃒

−⃒⃒ pi −pj⃒⃒

(4)

+ w2exp

2σ2 β

2σ2 ρ

{

(

)

1ifxi ∕= xj 0otherwise

μ

=

xi, xj

where μ is a label compatibility function and the remaining expression is  a Gaussian kernel depending on the feature extracted from pixels i and j,  and is weighted by w1, w2. The kernel can be divided into two compo­ nents. The first bilateral term is called appearance kernel and depends  on both pixel positions denoted as p and RGB colour denoted as q. This  term could convert pixels with similar colour and position to have the  same labels. The second kernel called the smooth kernel only depends on  pixel positions, removing small isolated pixels or regions. The scales of  Gaussian kernels are defined by σα,σβ,σρ. Parameters σα, σβ control the  degree of nearness and similarity (Shotton et al., 2009).

2.7. Evaluation metrics

Two common metrics, mean pixel accuracy and mean intersection  over union (mean IoU), are used to evaluate pixel-wise semantic seg­ mentation (Thoma, 2016). Mean pixel accuracy provides information  about the overall effectiveness of the classifier. It is the ratio of the  correctly predicted pixel numbers to the total pixel numbers in the entire  dataset. Mean pixel accuracy is also called overall accuracy (OA). Mean  IoU, also called Jaccard similarity coefficient, compares the similarity  and diversity of the complete sample set. The two metrics are defined in  the following Equations.

3.2. UAV imagery prediction

∑ m

In this study, we want to produce a network that could predict both  aerial images from a UAV platform and field images. To make it work,  preprocessing was firstly applied to close the differences between field  images and aerial images. Fig. 6 displays the selected maize field from  UAV orthomosaic imagery and its ground truth map (GTM). Note that  this maize field is from a different field where the field images were  collected, but the maize growth stages are similar (3–4 true full leaves).  Therefore, the robustness and generalization of the network can be  tested as well. It can be seen that maize plants are heavily overlapping in  the vertical direction. Weeds are distributed both in the intra- and inter-  rows. The detailed results of the networks in this dataset are reported in  Table 3. It is observed that FCN-8s performed better than FCN-32s and  FCN-16s which is similar to the field dataset discussed above. The pro­ posed network (0.617), UNet (0.601) and SegNet (0.609) achieved  better mIOU values than the FCN family with the best mIOU (0.538)

OA = 1

nii

(5)

m

ti

i=1

∑ m

mIoU = 1

nii ti + ∑m

(6)

j=1nji −nii

m

i=1

where ti is the total number of pixels of class i in the ground truth image,  nji is the number of pixels of class j predicted as belonging to class i and m  is the total number of classes.

2.8. Method implementation

Data augmentation was employed in the training dataset at the stage  of network training. All networks were implemented using the Tensor­ flow framework and were trained with four NVIDIA Tesla P100-SXM2

6

J. Gao et al.

Expert Systems With Applications 246 (2024) 122980


> **Table 2**

> Performance of the deep neural networks in the field test dataset.

Network  Soil background  Weed  Crop  Overall

OA  IOU  OA  IOU  OA  IOU  mOA  mIOU

FCN-32s   0.990   0.972   0.439   0.371   0.819   0.698  0.74.9   0.680  FCN-16s   0.992   0.973   0.514   0.435   0.799   0.705  0.768   0.704  FCN-8s   0.993   0.977   0.595   0.514   0.803   0.716  0.797   0.736  UNet   0.987   0.977   0.689   0.415   0.784   0.703  0.820   0.698  SegNet   0.993   0.979   0.634   0.534   0.807   0.736  0.811   0.750  Proposed*   0.954   0.959   0.522   0.401   0.781   0.622  0.752   0.661  Proposed   0.989   0.979   0.746   0.577   0.841   0.744  0.859   0.767

*The proposed network was trained using data without the preprocessings shown in Fig. 3.

achieved by FCN8. However, compared to performance in the field  dataset, all the corresponding metrics in the networks decreased in the  UAV dataset. This is mainly because the networks were trained with  field images alone. Although the preprocessing algorithms were applied,  trying to close the gap between the two datasets, the resolution and  object (weed species) differences were still present. The weed/crop  maps predicted by some of the networks are illustrated in Fig. 7. All the  networks are able to detect inter- and intra-row weeds. The FCN16 has  relatively rough prediction results, and weeds are overestimated  compared to GTM. The proposed network refined the predictions and  achieved 0.617 mIOU, though it still classified more weed pixels from  other class pixels. The over-estimated weeds could be acceptable in  practice as farmers generally prefer a conservative option to treat a  larger area than really needed to ensure a better crop development  (Borra-Serrano et al., 2015).

the proposed network. It can be seen that the outputs in the shallow  layers (Conv1) highlight different areas like vegetation and soil back­ ground independently within the given image. The content (maize and  weed objects) of images can still be distinguished which indicates that  the network learns some low-level features such as color, edges, and  texture in the shallow layers (512 × 512 × 64). There are some feature  maps highlighting the maize and weed pixels with the red color. It can be  seen that the vegetation part and soil background are displayed with  different colors, indicating the shallow layers already extract useful  features to segment the vegetation including weeds and maize from the  soil background, but not yet to extract enough features to differentiate  weed and maize pixels as they show similar color in all feature maps at  this layer. In the deeper layer (Conv26), because of a series of convo­ lution, and max pooling operations, the spatial information of feature  maps has been eliminated and it is difficult to interpret what features the  network learns. The features at this layer (32 × 32 × 512) become more  abstract. These high-level features are learned but the fine-grained  features could be lost because of pooling operations. In order to reme­ diate this issue, we, therefore, concatenated former layers to the deeper  layers in the decoder part.

Based on the predicted weed map from the proposed network, the  weed stress is visualised in Fig. 8(a). The corresponding spraying pre­ scription map is displayed in Fig. 8(b). The prescription weed map is a  map that could be used to control nozzles of a spraying boom for SSWM.  In SSWM, each nozzle is controlled individually instead of broadcast  spraying by switching on all nozzles. In this case, the ground area in each  grid of the prescription map (Fig. 8(b)) could be treated differently  based on the presence of pixels within that grid. From Table 4, we can  find that 238 out of 504 grids (the total number of grids) are free of  weeds, saving 47 % herbicides compared to conventional broadcast  spraying. It would save more with the increase of spraying resolution. As  illustrated in Table 4, the herbicide saving rate could increase up to 90.9  % if 10 × 10 spraying resolution (1.78 × 1.78 cm2) is guaranteed. The  spraying rates based on the prescription map at all three grid sizes are  slightly higher than those from the GTM. This also indicates the pro­ posed model predicted more weed pixels than the ground truth. With the  increase of spraying resolution (decrease of grid size), the spraying rate  difference gap between the prescription map and GTM is becoming  smaller, from 3.18 % at 100 × 100 grid size to 1.07 % at 10 × 10 grid  size. Fig. 9 shows the linear relationship (R2 = 0.949) between herbicide  saving rate and grid size based on GTM and Fig. 10 shows this linear  relationship (R2 = 0.947) based on the predicted prescription map. The  two fitted lines have the same trend, showing the negative relationship  between spraying saving rate and spraying resolution (grid size) under  the assumption that each nozzle only covers the whole area of the grid  and without overlapped spraying between two neighbour nozzles.


## 4. Discussion

The results demonstrate the feasibility of using one single deep  neural network trained with field data to produce a drone-based weed  map for precision farming. The network achieved satisfactory results  both for field data and aerial data. The reasons for the good performance  of our model are as follows. First, the use of the max-pooling layer with  indices and concatenation in the network largely keeps the spatial in­ formation and fine-grained features in the deep layers, which can  effectively detect small-sized weeds. Second, the weighted loss function  solves the problem of imbalanced samples. This means that the network  treats each class equally during the processing of training. The post-  processing algorithm (CRFs) can further fine-tune the predicted mask  such as noisy small object elimination and object boundary correction.  Most importantly, the preprocessing was applied in the field dataset  before training to close the gap between the two dataset differences. It is  difficult and unfair to directly compare the performances with other  studies as different datasets are used. In previous studies, Kim and Park,  (2022) developed a two-stage model MTS-CNN for weed and crop  detection and achieved 0.916 mIOU, slightly lower than the mIOU value  of 0.92 achieved in (Moazzam et al., 2023). This is higher than our  proposed network, which achieved mIOU values in our field dataset of  0.767 and aerial dataset of 0.617. We argue that our testing scenarios are  more complicated than the previous studies regarding the weed species  and size. The use of MTS-CNN for weed mapping in aerial images has not  been explored and validated. The use of synthetic images based on a cut-  and-paste method and PSPNet network doubled the segmentation per­ formance with a significant increase in the Dice-Sørensen Coefficient  (DSC) score from 25.32 to 45.20 (Picon et al., 2022). Generative  adversarial networks (GANs) and more advanced colour balancing  techniques were suggested to generate more realistic synthetic images to

3.3. Feature map visualization

The developed network trained with field images not only works well  in the test field dataset, but also is capable of predicting classes in the  remotely sensed UAV images that are never seen by the networks. The  outputs of the hidden layers in the network are helpful to understand  how a succession of convolutional layers translate their inputs, and to  get an intuition about the internal representations for each individual  convolutional filter. Fig. 11 shows the input image and its feature maps  at the first (shallow) and 26th (deep) layers. An input image was fed into

7

J. Gao et al.

Expert Systems With Applications 246 (2024) 122980

Fig. 5. The semantic segmentation of field examples (a-j) in the test dataset. The first row is original field images. The middle row is ground truth, and the third row  is prediction results by the proposed network.

further improve the weed and maize segmentation performance(Picon  et al., 2022). Jiang et al., 2022 investigated the three Transformer-based  models (Swin Transformer, SegFormer, and Sgmenter) for multiple  weed segmentations for grass management. The results show that Seg­ Former achieved the best performance with mOA and IoU values of  0.752 and 0.657, respectively. Although this transformer-based model  shows superiority compared with our proposed CNN-based method in  the ground dataset (mOA = 0.734, IoU = 0.617), it is worth noting that

this comparison is not based on the same dataset. The accuracy of the  weed map could be improved by adding labelled aerial images with the  same semantic objects in the training dataset. Besides, the public open  datasets can be used, e.g., in field annotation dataset for sugar beet and  weed segmentation. Chebrolu et al., (2017) published field multi-  channel image annotation dataset. Sa et al., (2018b) released a large  sugar beet and weed aerial annotation dataset. With the popularity of  drone-based remote sensing in precision farming, more available open

8

J. Gao et al.

Expert Systems With Applications 246 (2024) 122980

Fig. 6. The remotely sensed maize field from the UAV platform; (a) orthomosaic imagery, (b) the cropped interested field for testing performances of the networks,  (c) manually labelled ground truth map (GTM).


> **Table 3**

> Performance of the deep neural networks in the UAV orthomosaic imagery.

Network  Soil background  Weed  Crop  Overall

OA  IOU  OA  IOU  OA  IOU  mOA  mIOU

FCN-32s   0.760   0.562   0.389   0.169   0.483   0.328   0.544   0.353  FCN-16s   0.884   0.623   0.397   0.205   0.557   0.375   0.613   0.401  FCN-8s   0.903   0.767   0.525   0.356   0.608   0.491   0.679   0.538  UNet   0.935   0.829   0.534   0.402   0.647   0.573   0.705   0.601  SegNet   0.913   0.811   0.569   0.434   0.667   0.581   0.715   0.609  Proposed*   0.899   0.659   0.521   0.304   0.612   0.398   0.677   0.454  Proposed   0.932   0.815   0.582   0.441   0.689   0.596   0.734   0.617

*The proposed network was trained using data without the preprocessings shown in Fig. 3.

Fig. 7. The maps predicted from the FCN16 (a), SegNet (b) and the proposed network (c).

datasets will become available. Thus, transforming knowledge from  different datasets is becoming increasingly important to boost the per­ formance of deep neural networks and reduce the labour cost and time  of labelling of image data. Typically, crop/weed maps are produced by  using part of training samples in the orthomosaic imagery. This

procedure inevitably involves manual labelling. Our methodology pro­ vides a new direction for weed mapping with UAVs by utilizing other  data sources collected with field platforms with the same semantic ob­ jects. There are more publicly available field datasets (Chebrolu et al.,  2017) for weed and crop segmentation, which could allow transferring

9

J. Gao et al.

Expert Systems With Applications 246 (2024) 122980

Fig. 8. Weed heatmap in the field (a) and spraying prescription map (b) for SSWM (grid size: 100 × 100 pixels, representing17.8 × 17.8 cm2 in the ground).


> **Table 4**

> Quantitative results of SSWM based on two weed maps with three different grid 
sizes.

Map*  Free weed  grids

Weed  grids

Spraying  rate

Saving  rate

GTM (100 × 100)  254  250   49.60 %   50.40 %  Prescription Map (100

238  266   52.78 %   47.22 %

× 100)

GTM (50 × 50)  1466  550   27.28 %   72.72 %  Prescription Map (50

1429  587   29.12 %   70.88 %

× 50)

GTM (10 × 10)  46,771  4080   8.02 %   91.98 %  Prescription Map (10

46,230  4621   9.09 %   90.91 %

× 10)

*The grid sizes at 100 × 100, 50 × 50, 10 × 10 represent 17.8 × 17.8 cm2, 8.9 × 8.9 cm2 and 1.78 × 1.78 cm2 ground area, respectively.

Fig. 10. Fitted linear relationship between saved spraying rate and grid size  based on the predicted map by the proposed network.

prescription map could be directly integrated with a tractor platform for  SSWM if georeferenced information is provided. Some industries like  Croptic (https://www.croptic.ai/) are also working on integrating the  predicted weed map from a drone platform into conventional condor for  SSWM. The end goal of our research is to provide tangible benefits to the  farming community. The georeferencing of the predicted prescription  maps offers a direct avenue for integration with tractor platforms. This  allows for real-time SSWM, ensuring that weedicides are applied pre­ cisely where needed, reducing wastage, and ensuring efficient use. In  practical deployment, it would require RTK-GPS and section control in  ground-based vehicle such as tractors and condors in order to better  coordinate the predicted georeferenced weed map from UAV platforms.  The two fitted lines from GMP (Fig. 9) and the predicted prescription  map (Fig. 10) are very close, validating the effectiveness of our network  to produce a weed map from UAVs. It is worth noting the failures in the  predictions as illustrated in Fig. 13, and it is clear that the weed seed­ lings, especially grass weeds, are difficult objects to segment. Over­ lapping between objects could be another scenario where the network  does not predict well. In aerial imagery, the lower resolution and heavier  overlaps could limit the accuracy of weed maps generated from the

Fig. 9. Fitted linear relationship between saved spraying rate and grid size  based on the GTM.

the learned features in these datasets to predict and map weeds with  UAVs provided the two datasets share the same semantic objects.

An entire practical diagram is introduced in Fig. 12. The predicted

10

J. Gao et al.

Expert Systems With Applications 246 (2024) 122980

Fig. 11. Input image (a) and its feature maps at the first layer (b) and the twenty sixth layer (c).

11

J. Gao et al.

Expert Systems With Applications 246 (2024) 122980

Fig. 12. The pipeline of practical SSWM deployment with our proposed system.

in the process of max-pooling, which is known to improve the perfor­ mance of deep neural networks. Additionally, the proposed network has  been trained on a large and diverse dataset, allowing it to learn robust  and discriminative features. Therefore, it is likely that the improved  performance is a combination of the network architecture, training data,  and other optimization techniques used during training. Future research  could aim to investigate the relative contributions of each factor to the  overall performance of the proposed network.

One important consideration in the application of CRF post-  processing is its potential effect on computational time. The incorpora­ tion of CRFs introduces an additional computational overhead due to the  iterative nature of the CRF inference process. The time required for CRF  post-processing may vary depending on factors such as the size of the  input images and the complexity of the segmentation task. We observed  that while there is an increase in processing time (averaged 35.8 ms  more than no CRF applied), it remains within acceptable limits for  practical applications in our case for weed mapping without real-time  processing required. The benefits of improved segmentation quality  through CRF post-processing outweigh the moderate increase in pro­ cessing time. It is worth noting that the computational resources avail­ able, such as GPU capacity and parallel processing capabilities, can also  influence the practicality of using CRFs for post-processing. Overall,  while CRF post-processing introduces a modest increase in computa­ tional time, it is a valuable tool for enhancing segmentation quality,  especially in scenarios where precise object boundaries are critical.

Fig. 13. Segmentation result of a field image.

network. Intuitively, flying at a lower height leading to higher resolu­ tions could help. Other potential methods can be considered by using  more advanced imaging sensors such as multispectral or hyperspectral  cameras (Gao, Nuyttens, et al., 2018), which could utilize spectral fea­ tures beyond RGB bands. On the other hand, these multispectral data  typically have lower resolution (1–2 cm versus millimetre level), which  is again making things more difficult to classify. Also, super-resolution  imaging, a class of techniques to enhance the resolution of an imaging  system, is a way to improve the resolution of aerial images and thus  further close the difference gap (Chen et al., 2022).

Domain adaptation is a method that enables a model to perform well  on a target domain by learning from a source domain. In the case of our  study, the source domain is ground-based field images, and the target  domain is UAV images. Our target domain has no labels, and it is  difficult to label them accurately due to lower resolution. Our results  show that our transferable model could effectively learn the features and  patterns from the source domain (ground image) and apply them to the  different but related target domain (aerial image) by applying pre­ processings to reduce the differences. We highlight that it is important to  consider the factor of similarity between the source and target domains  to ensure the success. Other techniques in domain adaptation such as  adversarial training, instance re-weighting and domain adaptive  training could be further explored to improve the performances.

We show the feature learning process of plant objects with feature  map visualization. The visualization is helpful to understand what the  deep neural network learns. Moreover, it improves network architecture  such as model selection and parameter reduction. In Fig. 11(c), we find  that some feature maps at deep layers displayed in blue colour are not  activated and can be regarded as redundant features. This means the  network can be further optimized to improve its architecture. The spe­ cific relationship between the number of reduction parameters and  visualization results is a meaningful work to quantify interpretable pa­ rameters of deep neural networks (Toda & Okura, 2019).

The proposed network architecture is similar to U-Net and SegNet,  but with a higher number of network parameters. While it is true that  increased parameters may contribute to improved performance, it is not  the sole factor. The proposed network has been specifically designed to  handle the challenges of the target task, such as detecting tiny weed  seedlings in the images. The architecture includes the recorded indices


## 5. Conclusions

Deep learning has become increasingly significant in semantic seg­ mentation of UAV-based remote sensing imagery and has shown to be  powerful to extract multi-level features and find potential patterns from  a big image dataset. This paper presents a complete pipeline for

12

Expert Systems With Applications 246 (2024) 122980

J. Gao et al.

semantic weed/crop segmentation using deep convolutional neural  networks. The networks were trained only with field images, and then  were validated both using field test data and remotely sensed images  from a UAV platform. The proposed network outperformed in the field  test dataset, shown in Table 2. For the validation of UAV imagery, we  first generated an orthomosaic photo from the overlapped aerial images,  and then used the network to predict cropped subimages from the  orthomosaic photo. Finally, the predictions of subimages were merged  to generate crop/weed map. The result in the UAV dataset shows that  the proposed network still performs best compared to the other net­ works. While our dataset captures a range of conditions regarding weed  species, occlusion, and outdoor environments, it is limited to a specific  crop growth stage. Thus, the model’s performance in drastically  different growth stages remains untested. Our comparative analysis was  limited to a specific set of models. The performance could vary when  compared to newer or other relevant models in the field.

Bawden, O., Kulk, J., Russell, R., McCool, C., English, A., Dayoub, F., … Perez, T. (2017).

Robot for weed species plant-specific management. Journal of Field Robotics, 34(6),  1179–1199. https://doi.org/10.1002/rob.21727  Borra-Serrano, I., Pe˜na, J., Torres-S´anchez, J., Mesas-Carrascosa, F., & L´opez-

Granados, F. (2015). Spatial Quality Evaluation of Resampled Unmanned Aerial  Vehicle-Imagery for Weed Mapping. Sensors, 15(8), 19688–19708. https://doi.org/  10.3390/s150819688  Burgos-artizzu, X. P., Ribeiro, A., Guijarro, M., & Pajares, G. (2011). Real-time image

processing for crop / weed discrimination in maize fields. Computers and Electronics  in Agriculture, 75(2), 337–346. https://doi.org/10.1016/j.compag.2010.12.011  Chebrolu, N., Lottes, P., Schaefer, A., Winterhalter, W., Burgard, W., & Stachniss, C.

(2017). Agricultural robot dataset for plant classification, localization and mapping  on sugar beet fields. International Journal of Robotics Research, 36(10), 1045–1052.  https://doi.org/10.1177/0278364917720510  Chen, H., He, X., Qing, L., Wu, Y., Ren, C., Sheriff, R. E., & Zhu, C. (2022). Real-world

single image super-resolution: A brief review. Information Fusion, 79, 124–145.  https://doi.org/10.1016/j.inffus.2021.09.005  Chen, L.-C., Papandreou, G., Kokkinos, I., Murphy, K., & Yuille, A. L. (2018). DeepLab:

Semantic Image Segmentation with Deep Convolutional Nets, Atrous Convolution,  and Fully Connected CRFs. IEEE Transactions on Pattern Analysis and Machine  Intelligence, 40(4), 834–848. https://doi.org/10.1109/TPAMI.2017.2699184  Dian Bah, M., Hafiane, A., & Canals, R. (2018). Deep learning with unsupervised data

The use of a weighted loss function is a good way to remediate the  issue of imbalanced classes in the dataset. The weights of each class can  be quantified with the pixel statistics in the training dataset. Fully  connected CRFs were used to fine-tune the predictions by the networks.

labeling for weed detection in line crops in UAV images. Remote Sensing, 10(11).  https://doi.org/10.3390/rs10111690  Emmi, L., & Gonzalez-de-Santos, P. (2017). Mobile robotics in arable lands: Current state

and future trends. European Conference on Mobile Robots (ECMR), 2017, 1–6. https://  doi.org/10.1109/ECMR.2017.8098694  Gao, J. (2020). An exploration of the use of machine learning techniques for site-specific weed

We demonstrated that it is feasible to use deep convolutional neural  networks trained with field data to predict aerial images based on high-  resolution UAV orthomosaic imagery and field images. The pre­ processing procedure to reduce the dataset differences from two do­ mains is highlighted to ensure the superiority of the proposed network.  The crop/weed map finally could be produced through our proposed  pipeline, which opens a new path to generate a workflow for site-specific  weed management (SSWM) studies. Moreover, the study shows that  deep learning has the ability to integrate different source data and can  be used for multi-tasks. Our work can benefit some relevant commu­ nities such as UAV-based remote sensing, precision crop farming and  agricultural field robots.

management. Ghent University.   Gao, J., French, A. P., Pound, M. P., He, Y., Pridmore, T. P., & Pieters, J. G. (2020). Deep

convolutional neural networks for image-based Convolvulus sepium detection in  sugar beet fields. Plant Methods, 16(1). https://doi.org/10.1186/s13007-020-00570-  z  Gao, J., Liao, W., Nuyttens, D., Lootens, P., Vangeyte, J., Piˇzurica, A., … Pieters, J. G.

(2018). Fusion of pixel and object-based features for weed mapping using unmanned  aerial vehicle imagery. International Journal of Applied Earth Observation and  Geoinformation, 67, 43–53. https://doi.org/10.1016/j.jag.2017.12.012  Gao, J., Nuyttens, D., Lootens, P., He, Y., & Pieters, J. G. (2018). Recognising weeds in a

maize crop using a random forest machine-learning algorithm and near-infrared  snapshot mosaic hyperspectral imagery. Biosystems Engineering, 170, 39–50. https://  doi.org/10.1016/j.biosystemseng.2018.03.006  Gao, J., Westergaard, J. C., Sundmark, E. H. R., Bagge, M., Liljeroth, E., &

Alexandersson, E. (2021). Automatic late blight lesion recognition and severity  quantification based on field imagery of diverse potato genotypes by deep learning.  Knowledge-Based Systems, 214, Article 106723. https://doi.org/10.1016/j.  knosys.2020.106723  Huang, J., Zhang, X., Xin, Q., Sun, Y., & Zhang, P. (2019). Automatic building extraction

CRediT authorship contribution statement

Junfeng Gao: Conceptualization, Data curation, Formal analysis,  Methodology, Writing – original draft, Writing – review & editing.  Wenzhi Liao: Conceptualization, Methodology, Writing – review &  editing. David Nuyttens: Resources, Supervision, Writing – review &  editing. Peter Lootens: Data curation, Software, Visualization, Writing  – review & editing. Erik Alexandersson: Funding acquisition, Super­ vision, Writing – review & editing. Jan Pieters: Funding acquisition,  Project administration, Supervision, Writing – review & editing.

from high-resolution aerial images and LiDAR data using gated residual refinement  network. ISPRS Journal of Photogrammetry and Remote Sensing, 151, 91–105. https://  doi.org/10.1016/j.isprsjprs.2019.02.019  Jiang, K., Afzaal, U., & Lee, J. (2022). Transformer-Based Weed Segmentation for Grass

Management. Sensors, 23(1), 65. https://doi.org/10.3390/s23010065  Kamilaris, A., & Prenafeta-Boldú, F. X. (2018). Deep learning in agriculture: A survey.

Computers and Electronics in Agriculture, 147, 70–90. https://doi.org/10.1016/j.  compag.2018.02.016  Kim, Y. H., & Park, K. R. (2022). MTS-CNN: Multi-task semantic segmentation-

convolutional neural network for detecting crops and weeds. Computers and  Electronics in Agriculture, 199, Article 107146. https://doi.org/10.1016/J.  COMPAG.2022.107146  Kingma, D. P., & Ba, J. (2015). Adam: A Method for Stochastic Optimization.

Declaration of competing interest

International Conference for Learning Representations, 1–15. https://doi.org/http://  doi.acm.org.ezproxy.lib.ucf.edu/10.1145/1830483.1830503.  Kohli, P., Ladický, L., & Torr, P. H. S. (2009). Robust higher order potentials for enforcing

The authors declare that they have no known competing financial  interests or personal relationships that could have appeared to influence  the work reported in this paper.

label consistency. International Journal of Computer Vision, 82(3), 302–324. https://  doi.org/10.1007/s11263-008-0202-0  Kr¨ahenbühl, P., & Koltun, V. (2011). Efficient Inference in Fully Connected CRFs with

Data availability

Gaussian Edge Potentials. In J. Shawe-Taylor, R. S. Zemel, P. L. Bartlett, F. Pereira, &  K. Q. Weinberger (Eds.), Advances in Neural Information Processing Systems 24 (pp.  109–117). Curran Associates, Inc. http://papers.nips.cc/paper/4296-efficient-  inference-in-fully-connected-crfs-with-gaussian-edge-potentials.pdf.  Lauwers, M., Nuyttens, D., De Cauwer, B., & Pieters, J. (2022). Hyperspectral

Data will be made available on request.

Acknowledgement

classification of poisonous solanaceous weeds in processing Phaseolus vulgaris L.  and Spinacia oleracea L. Computers and Electronics in Agriculture, 196, Article 106908.  https://doi.org/10.1016/j.compag.2022.106908  LeCun, Y. A., Bengio, Y., & Hinton, G. E. (2015). Deep learning. Nature, 521(7553),

This work was supported by the Lincoln Agri-Robotics Grant (E3)  from Research England, and the Nordic Council of Ministers, Copenha­ gen, Denmark (PPP #6P2 and #6P3). We acknowledge the drone pilot  from ILVO for data collection.

436–444. https://doi.org/10.1038/nature14539  Long, J., Shelhamer, E., & Darrell, T. (2015). Fully Convolutional Networks for Semantic

Segmentation. IEEE Transactions on Pattern Analysis and Machine Intelligence, 39(4),  640–651. https://doi.org/10.1109/TPAMI.2016.2572683  Lottes, P., Behley, J., Milioto, A., & Stachniss, C. (2018). Fully Convolutional Networks


## References

With Sequential Information for Robust Crop and Weed Detection in Precision  Farming. IEEE Robotics and Automation Letters, 3(4), 2870–2877. https://doi.org/  10.1109/LRA.2018.2846289  Milioto, A., Lottes, P., & Stachniss, C. (2017). Real-Time BLOB-wise sugar beets vs weeds

Badrinarayanan, V., Kendall, A., & Cipolla, R. (2017). SegNet: A Deep Convolutional

Encoder-Decoder Architecture for Image Segmentation. IEEE Transactions on Pattern  Analysis and Machine Intelligence, 39(12), 2481–2495. https://doi.org/10.1109/  TPAMI.2016.2644615

classification for monitoring fields using convolutional neural networks. SPRS Annals

13

J. Gao et al.

Expert Systems With Applications 246 (2024) 122980

of the Photogrammetry, Remote Sensing and Spatial Information Sciences, 4(2W3),  41–48. https://doi.org/10.5194/isprs-annals-IV-2-W3-41-2017  Moazzam, S. I., Khan, U. S., Qureshi, W. S., Nawaz, T., & Kunwar, F. (2023). Towards

Shotton, J., Winn, J., Rother, C., & Criminisi, A. (2009). TextonBoost for image

understanding: Multi-class object recognition and segmentation by jointly modeling  texture, layout, and context. International Journal of Computer Vision, 81(1), 2–23.  https://doi.org/10.1007/s11263-007-0109-1  Singh, A. K., Ganapathysubramanian, B., Sarkar, S., & Singh, A. (2018). Deep Learning

automated weed detection through two-stage semantic segmentation of tobacco and  weed pixels in aerial Imagery. Smart Agricultural Technology, 4, Article 100142.  https://doi.org/10.1016/j.atech.2022.100142  Noh, H., Hong, S., & Han, B. (2015). Learning deconvolution network for semantic

for Plant Stress Phenotyping: Trends and Future Perspectives. In. Trends in Plant  Science, 23(10), 883–898. https://doi.org/10.1016/j.tplants.2018.07.004  Thoma, M. (2016). A Survey of Semantic Segmentation. ArXiv Preprint, arXiv:

segmentation. In Proceedings of the IEEE International Conference on Computer Vision.  https://doi.org/10.1109/ICCV.2015.178  Oerke, E. C. (2006). Crop losses to pests. The Journal of Agricultural Science, 144(01),

1602.06541. http://arxiv.org/abs/1602.06541.  Toda, Y., & Okura, F. (2019). How Convolutional Neural Networks Diagnose Plant

31–43.  Peerbhay, K., Mutanga, O., Lottering, R., Bangamwabo, V., & Ismail, R. (2016). Detecting

Disease. Plant Phenomics, 2019, 9237136. https://doi.org/10.1155/2019/9237136  Torres-S´anchez, J., L´opez-Granados, F., & Pe˜na, J. M. (2015). An automatic object-based

bugweed (Solanum mauritianum) abundance in plantation forestry using  multisource remote sensing. ISPRS Journal of Photogrammetry and Remote Sensing,  121, 167–176. https://doi.org/10.1016/j.isprsjprs.2016.09.014  Perez-Ortiz, M., Pena, J. M., Gutierrez, P. A., Torres-Sanchez, J., Hervas-Martinez, C., &

method for optimal thresholding in UAV images: Application for vegetation  detection in herbaceous crops. Computers and Electronics in Agriculture, 114, 43–52.  https://doi.org/10.1016/j.compag.2015.03.019  Van De Vijver, R., Mertens, K., Heungens, K., Nuyttens, D., Wieme, J., Maes, W. H., …

Lopez-Granados, F. (2016). Selecting patterns and features for between- and within-  crop-row weed mapping using UAV-imagery. Expert Systems with Applications, 47,  85–94. https://doi.org/10.1016/j.eswa.2015.10.043  Picon, A., San-Emeterio, M. G., Bereciartua-Perez, A., Klukas, C., Eggers, T., & Navarra-

Saeys, W. (2022). Ultra-High-Resolution UAV-Based Detection of Alternaria solani  Infections in Potato Fields. Remote Sensing, 14(24), 6232. https://doi.org/10.3390/  rs14246232  Van De Vijver, R., Mertens, K., Heungens, K., Somers, B., Nuyttens, D., Borra-Serrano, I.,

Mestre, R. (2022). Deep learning-based segmentation of multiple species of weeds  and corn crop using synthetic and real image datasets. Computers and Electronics in  Agriculture, 194, Article 106719. https://doi.org/10.1016/j.compag.2022.106719  Sa, I., Chen, Z., Popovi´c, M., Khanna, R., Liebisch, F., Nieto, J., & Siegwart, R. (2018).

… Saeys, W. (2020). In-field detection of Alternaria solani in potato crops using  hyperspectral imaging. Computers and Electronics in Agriculture, 168, Article 105106.  https://doi.org/10.1016/j.compag.2019.105106  Wang, A., Zhang, W., & Wei, X. (2019). A review on weed detection using ground-based

weedNet: Dense Semantic Weed Classification Using Multispectral Images and MAV  for Smart Farming. IEEE Robotics and Automation Letters, 3(1), 588–595. https://doi.  org/10.1109/LRA.2017.2774979  Sa, I., Popovi´c, M., Khanna, R., Chen, Z., Lottes, P., Liebisch, F., … Siegwart, R. (2018).

machine vision and image processing techniques. Computers and Electronics in  Agriculture, 158, 226–240. https://doi.org/10.1016/j.compag.2019.02.005  Wang, N., Zhang, N., Wei, J., Stoll, Q., & Peterson, D. E. (2007). A real-time, embedded,

weed-detection system for use in wheat fields. Biosystems Engineering, 98(3),  276–285. https://doi.org/10.1016/j.biosystemseng.2007.08.007  Zhang, N., Wang, M., & Wang, N. (2002). Precision agriculture - A worldwide overview.

WeedMap: A large-scale semantic weed mapping framework using aerial  multispectral imaging and deep neural network for precision farming. Remote  Sensing, 10(9). https://doi.org/10.3390/rs10091423  Shapira, U., Herrmann, I., Karnieli, A., & Bonfil, D. J. (2013). Field spectroscopy for weed

Computers and Electronics in Agriculture, 36(2–3), 113–132. https://doi.org/10.1016/  S0168-1699(02)00096-0  Zhang, Y., Gao, J., Cen, H., Lu, Y., Yu, X., He, Y., & Pieters, J. G. (2019). Automated

detection in wheat and chickpea fields. International Journal of Remote Sensing, 34  (17), 6094–6108. https://doi.org/10.1080/01431161.2013.793860  Shaw, D. R. (2005). Remote sensing and site-specific weed management. Frontiers in

spectral feature extraction from hyperspectral images to differentiate weedy rice and  barnyard grass from a rice crop. Computers and Electronics in Agriculture, 159, 42–49.  https://doi.org/10.1016/j.compag.2019.02.018

Ecology and the Environment, 3(10), 526–532. https://doi.org/10.1890/1540-9295  (2005)003[0526:RSASWM]2.0.CO;2

14
