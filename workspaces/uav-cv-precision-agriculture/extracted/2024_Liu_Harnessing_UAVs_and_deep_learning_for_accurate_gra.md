---
workspace_id: SCI-000650
doi: 10.1186/s13007-024-01272-6
title: 'Harnessing UAVs and deep learning for accurate grass weed detection in wheat
  fields: a study on biomass and yield implications'
authors:
- family_name: Liu
  given_name: Tao
  orcid: https://orcid.org/0000-0003-1451-5251
- family_name: Zhao
  given_name: Yuanyuan
  orcid: https://orcid.org/0000-0001-5298-2948
- family_name: Wang
  given_name: Hui
  orcid: https://orcid.org/0009-0005-6741-8166
- family_name: Wu
  given_name: Wei
  orcid: https://orcid.org/0000-0002-6625-2222
- family_name: Yang
  given_name: Tianle
  orcid: https://orcid.org/0000-0002-3682-4306
- family_name: Zhang
  given_name: Weijun
  orcid: https://orcid.org/0009-0006-1540-7382
- family_name: Zhu
  given_name: Shaolong
  orcid: https://orcid.org/0000-0002-2525-0095
- family_name: Sun
  given_name: Chengming
  orcid: https://orcid.org/0000-0003-0873-3922
- family_name: Yao
  given_name: Zhaosheng
  orcid: https://orcid.org/0009-0005-2757-1019
year: 2024
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:26:14.420024+00:00'
---

# Harnessing UAVs and deep learning for accurate grass weed detection in wheat fields: a study on biomass and yield implications

Liu et al. Plant Methods          (2024) 20:144  https://doi.org/10.1186/s13007-024-01272-6 Plant Methods

RESEARCH Open Access

Harnessing UAVs and deep learning  for accurate grass weed detection in wheat  fields: a study on biomass and yield  implications

Tao Liu1†, Yuanyuan Zhao1†, Hui Wang2†, Wei Wu3, Tianle Yang1, Weijun Zhang1, Shaolong Zhu1, Chengming Sun1  and Zhaosheng Yao1*


## Abstract

Weeds are undesired plants competing with crops for light, nutrients, and water, negatively impacting crop growth. 
Identifying weeds in wheat fields accurately is important for precise pesticide spraying and targeted weed control. 
Grass weeds in their early growth stages look very similar to wheat seedlings, making them difficult to identify. In 
this study, we focused on wheat fields with varying levels of grass weed infestation and used unmanned aerial 
vehicles (UAVs) to obtain images. By utilizing deep learning algorithms and spectral analysis technology, the 
weeds were identified and extracted accurately from wheat fields. Our results showed that the precision of weed 
detection in scattered wheat fields was 91.27% and 87.51% in drilled wheat fields. Compared to areas without 
weeds, the increase in weed density led to a decrease in wheat biomass, with the maximum biomass decreasing 
by 71%. The effect of weed density on yield was similar, with the maximum yield decreasing by 4320 kg·ha− 1, a 
drop of 60%. In this study, a method for monitoring weed occurrence in wheat fields was established, and the 
effects of weeds on wheat growth in different growth periods and weed densities were studied by accurately 
extracting weeds from wheat fields. The results can provide a reference for weed control and hazard assessment 
research.
Keywords  Grass weeds, Wheat field, Unmanned aerial vehicles (UAVs), Deep learning algorithm, Hyperspectral 
imaging

†Tao Liu, Yuanyuan Zhao and Hui Wang contributed equally to this  work.

*Correspondence: Zhaosheng Yao yzs@yzu.edu.cn 1Cultivation and Construction Site of National Key Laboratory for Crop  Genetics and Physiology in Jiangsu Province, Yangzhou University,  Yangzhou 225009, PR China 2Lixiahe Institute of Agricultural Sciences, Jiangsu, Yangzhou  225007, China 3Key Laboratory of Agro-information Services Technology, Ministry of  Agriculture, Beijing 100081, China

© The Author(s) 2024. Open Access  This article is licensed under a Creative Commons Attribution 4.0 International License, which permits use,  sharing, adaptation, distribution and reproduction in any medium or format, as long as you give appropriate credit to the original author(s) and  the source, provide a link to the Creative Commons licence, and indicate if changes were made. The images or other third party material in this  article are included in the article’s Creative Commons licence, unless indicated otherwise in a credit line to the material. If material is not included  in the article’s Creative Commons licence and your intended use is not permitted by statutory regulation or exceeds the permitted use, you will  need to obtain permission directly from the copyright holder. To view a copy of this licence, visit http://creativecommons.org/licenses/by/4.0/.

Page 2 of 15 Liu et al. Plant Methods          (2024) 20:144


## Introduction

Weeds are unwanted plants that compete with crops in 
terms of light, nutrition, water, and growth space. Weeds 
can lead to the deterioration of the field environment, and 
inhibit the growth and development of wheat, resulting 
in slow growth, stunted growth, and reduced yield and 
quality [1, 2]. A large infestation of weeds can cause a 60% 
reduction in wheat yield. The degree of yield reduction 
mainly depends on the density of weeds and the length of 
time of weed interference [3]. Monitoring weeds is essen­
tial for targeted control and precise spraying, which can 
help reduce pesticide consumption and non-point source 
pollution while improving the accuracy and effectiveness 
of field management. Therefore, it is important to investi­
gate effective weed identification methods in wheat fields 
to achieve precise pesticide spraying and targeted weed 
control in future experiments. Grass weeds are among 
the most challenging weeds to control in wheat fields and 
represent the primary weed species during the wheat’s 
overwintering and jointing stages.

finally distinguished weeds and plants through principal  component analysis.

The UAV remote sensing systems have clear advan­ tages, including being fast, non-destructive, low cost,  and high throughput. In recent years, UAV remote sens­ ing technology has been gradually applied to monitoring  crop growth in agriculture [11]. The UAV remote sensing  system comprises UAVs and micro-miniature multispec­ tral and hyperspectral sensors, which can obtain high- resolution images [12]. Zhao et al. [13] used the UAV  remote sensing platform to obtain the characteristics of  plants and weeds at the canopy scale, divided the vegeta­ tion and non-vegetation areas in the image by the maxi­ mum between-class variance method, and segmented  the weed areas. Using hyperspectral and deep learning  techniques can significantly improve the classification  of farmland vegetation in UAV images [14]. The method  also provides a reference for the identification of weeds.

In wheat cultivation, the predominant weed species  can be categorized into members of the Poaceae fam­ ily (commonly referred to as grass weeds) and broadleaf  weeds. The foliar morphology of broadleaf weeds mark­ edly differs from that of wheat seedlings, facilitating their  identification. Conversely, grass weeds display consid­ erable morphological similarities to wheat seedlings,  complicating their differentiation. Although previous  research has exten- sively addressed the identification of  broadleaf weeds within wheat fields, studies focusing on  the identification of Poaceae weeds remain limited. There  are also few published studies on the use of UAVs for  monitoring weeds in wheat fields. This is primarily due  to the minimal differences in color and spectral charac­ teristics between grass weeds and wheat, making it chal­ lenging to distinguish between them. In this study, we  focused on wheat fields with varying levels of weed infes­ tation, acquired UAV images, and investigated the impact  of different growth stages and weed densities on wheat  growth. This research aims to provide valuable insights  for weed management and risk assessment. The specific  objectives of this study are as follows:

The current research methods for weed monitoring can  be divided into artificial recognition, machine vision, var­ ious image acquisition technologies, and different image  extraction methods. Ashraf and Khan [4] used two meth­ ods to separate weeds and crops: one classified weeds  based on texture features, and the other classified weed  images based on plant shape and anatomical structure.  Sabzi and Sajad [5] used machine vision technology to  segment potato plants and weeds; their method achieved  correct detection, segmentation, and classification of  potato plants and weeds at a speed of 0.15 m·s-1. Raja et  al. [6] used machine vision technology and crop signal­ ing techniques to distinguish crops and weeds. Raveen­ dra et al. [7] demonstrated the capability of LabVIEW in  performing machine vision to reduce human interven­ tion in agricultural production. Their method can pro­ cess the digital images acquired by the camera and match  the captured weed leaves with a hypothetical database  for health confirmation. Jiang et al. [8] proposed a weed  detection method based on Mask R-CNN (a framework  for image segmentation tasks), which combines target  detection and semantic segmentation to classify weeds  and crops while detecting weeds. In the above studies,  RGB images were mostly used for weed identification.  The use of hyperspectral images in weed recognition  tasks can provide more information about the targets  than RGB images. It is also very beneficial for improv­ ing recognition accuracy. Li et al. [9] constructed a clas­ sification of perennial weeds based on hyperspectral  data. Pan et al. [10] used a variety of preprocessing and  characteristic wavelength extraction methods to process  the canopy hyperspectral data of plants and weeds, ana­ lyzed the spectra of different bands to establish the aver­ age reflectance spectrum curve of plants and weeds, and

(1)	To develop an identification model for grass weeds

in wheat fields based on deep learning algorithms,  pinpointing the locations of weeds; (2)	Construct a weed biomass estimation model utilizing

hyperspectral imagery to assess the prevalence of  weed infestations; (3)	Evaluate the impact of different models on the

accuracy of weed identification; (4)	Investigate wheat yield data under various weed

infestation scenarios and assess the implications of  weed-induced damage.

Page 3 of 15 Liu et al. Plant Methods          (2024) 20:144

Fig. 1  Study region


> **Table 1  Parameters of the image acquisition equipment**

> Equipment
Camera technology
Flight altitude
DJI Matrice 600 Pro
+
GaiaSky-mini Camera

Wavelength range: 400–1000 nm Spectral resolution: 3.5 nm Image resolution: 1920 × 2080 Weight: 1.5 kg

50 m

DJI Mavic 3 Positioning accuracy: 1–1.5 cm CMOS: Mavic 3 Image resolution: 5280 × 3956 Field of view: 84°

15 m

Materials and methods Data acquisition Our study was conducted in Yizheng and Sihong, Jiangsu  Province, China, in 2019–2020 (Fig.  1). Eight test plots  were selected as the research subjects, of which six  plots had varying degrees of weed infestation, while the  remaining two plots were kept weed-free as control. The

species of weed are Alopecurus pratensis (Alopecurus  aequalis Sobol.) and Poa pratensis (Poa annua L.). The  images were obtained by UAVs during the wintering,  seedling, and jointing periods. The sensor parameters  used are shown in Table 1. The images were acquired on  sunny days between 10:00 a.m. and 2:00 p.m. In hyper­ spectral image acquisition, there was a 50% overlap

Page 4 of 15 Liu et al. Plant Methods          (2024) 20:144

between routes and a 60% overlap between waypoints.  The corresponding percentages were 70% and 80% in  multispectral image acquisition. The images of the stan­ dard gray cloths were obtained during image acquisition.

points. Vegetation indexes, i.e., normalized difference  vegetation index (NDVI), ratio vegetation index (RVI),  and soil-adjusted vegetation index (SAVI), were extracted  on the acquired images [15]. The processing flow is  shown in Fig.  2. All experiments were conducted on a  high-performance computing setup with the following  hardware and software specifications: CPU: Intel Core  i7-9700  K, 8 cores; GPU: NVIDIA GeForce RTX 3090,  24GB VRAM; Memory (RAM): 64GB DDR4; Storage:  1 TB NVMe SSD.

Field sampling and image acquisition of weeds and  wheat were carried out simultaneously. The collected  samples were fixed at 105℃ for 30 min and then dried  at 80℃ to constant weight. The above-ground biomass of  both wheat and weeds were measured, respectively.

Data processing After lens calibration, reflectance calibration, and atmo­ spheric calibration through SpecView software (Jiangsu  Dualix Spectral Imaging Technology Co., Ltd. China),  hyperspectral images were stitched through HiSpec­ tralStitcher software (Jiangsu Dualix Spectral Imaging  Technology Co., Ltd. China). RGB images were stitched  through Metashape software (Agisoft LLC, Russia) to  generate orthophotos images, and the accuracy of image  stitching was further improved through ground control

Semantic segmentation algorithm In this research, DeepLabV3 + was used to segment  weeds and wheat. Based on the DeepLabV3 + framework  of deep learning, using the Encoder-Decoder structure  has a relatively better effect in boundary extraction appli­ cations, which can significantly improve the accuracy  of image segmentation [16, 17]. The encoder uses the  ResNet-50 residual network as a skeleton network for  feature extraction. ResNet-50 introduces the components

Fig. 2  The flow chart of this research

Page 5 of 15 Liu et al. Plant Methods          (2024) 20:144

4-fold and perform a 3 × 3 convolution operation. The  original resolution is restored after upsampling at 4-fold  again. Finally, we use the Softmax classifier to classify  each pixel to obtain the pixel classification probability  map. The principle is shown in Fig. 3A.

of residual modules to deepen network depth but does  not add additional parameters and calculations to  the network. In addition, compared with VGGNet, it  increases the training speed and obtains better training  effects and model accuracy. First, the first three groups  of residual blocks of ResNet-50 are serially concatenated,  and then the fourth group of residual blocks is modified  to use dilated convolution. Atrous spatial pyramid pool­ ing (ASPP) is introduced, which can capture multi-scale  information through different sampling rates and aggre­ gate the prediction results from five parallel branches  to obtain a 1 × 1 convolution feature map, which is then  input to the decoder for use. The decoder draws on fully  convolutional networks (FCNs) characteristics by com­ bining low-level feature and high-level feature prediction.  In the detailed information of low-level features passing  through, to reduce the number of channels, we first use  48-channel 1 × 1 convolution to convolve the low-level  feature map to obtain the prediction map. We then fuse  it with the high-level feature map that is upsampled at

A total of 1,000 RGB images of wheat field weeds in the  wintering period and jointing period were collected dur­ ing this study, and 10,000 sub-images were cropped into  318 × 318 pixels, of which 7,000 images were used for the  simple semantic segmentation model, and 3,000 images  were used for verification. The training images were man­ ually annotated using LabelMe software (MIT, Computer  Science and Artificial Intelligence Laboratory, USA), as  shown in Fig. 3B, where red labeled areas indicate wheat,  blue indicates weeds, and black indicates soil. The model  was developed based on Python 3.7. The study employs  the deep learning model to perform weed extraction,  consequently calculating the weed canopy cover (CC) for  weed biomass estimation.

Fig. 3  Extracting weed coverage using deep learning. (A) The network structure of deep learning; (B) The labeling processes and results

Page 6 of 15 Liu et al. Plant Methods          (2024) 20:144

SST = m

i=1(tyi −¯y)2 (8)

Accuracy evaluation One of the important indicators to measure the accuracy  of the remote sensing image semantic segmentation algo­ rithm is Mean Intersection over Union (MIoU), which is  the average of the ratio of the intersection and the union  of the ground truth and predicted segmentation sets,  i.e., the average value after the sum of Intersection over  Union (IoU) of each type of ground feature. Identifying  wheat field weeds is a three-class issue (wheat, weeds,  and land). We use F1 values, precision, and recall as the  accuracy evaluation indicators. The specific calculation  formulas are as follows:

R2 = 1 −SSE

SST  (9)

where m is the sample size, pyi is the predicted value  of model, tyi is the true value, and ¯y is the mean of the  observed data from the field.


## Results

The characteristics of weeds and wheat
The fundamental reason for the difficulty in identifying 
weeds in wheat fields is that the color difference between 
weeds and wheat is small. As shown in Fig. 4, in the RGB 
image, the histograms of weed and wheat on the three 
channels of red (R), green (G), and blue (B) are very simi­
lar, so it is very difficult to distinguish weeds from wheat 
directly using color images.

IoU = TP FN+FP+TP (1)

k

MIoU = 1 k+1

TP FN+FP+TP  (2)

i=0

We analyzed the spectral curves and common char­ acteristic parameters of wheat and weeds. As shown in  Fig. 5, the curves of weeds and wheat in the 400–1000 nm  band are very similar, and there are some differences only  in the green and red regions of visible light. Furthermore,  there is a large amount of overlap in other areas, making  it challenging to distinguish weeds and wheat by spec­ trum. In accordance with previous research advance­ ments, vegetation cover and canopy vegetation indices  such as NDVI are closely related to vegetation biomass.  Biomass regression models constructed using cover and  NDVI typically exhibit a high level of accuracy. However,  as evidenced by the results of this study (Fig. 6), it can  be observed that the biomass regression models devel­ oped using canopy cover and NDVI for weed estimation  yield relatively poor performance. Notably, the estima­ tion accuracy is relatively better during the overwintering  period, although the RMSE values exceed 10, and they  escalate to over 40 during the regreening period. Over­ all, the estimation performance using canopy cover is  slightly superior to that of NDVI. Several factors contrib­ ute to the suboptimal estimation performance, including:  (1) The DeepLab model used for weed cover estimation  cannot distinguish the extent of weed infestation, and it  can only differentiate between the presence and absence  of weeds; (2) When calculating weed biomass using veg­ etation indices, it is challenging to differentiate between  weeds and wheat. The calculation of biomass is influ­ enced by wheat, especially during the regreening period,  where increased biomass leads to larger errors.

F1 = 2×TP N+TP−TN (3)

Precision = TP TP+FP (4)

Recall = TP TP+FN (5)

where TP is true positive, TN is true negative, FN is  false negative, FP is false positive, N is the total number  of samples, and k is the segmentation of k-type ground  features.

The coefficient of determination (R2) values of the  models, the root mean square error (RMSE), and the rel­ ative error in prediction (REP) are used to test the perfor­ mance of the model. R2 and RMSE are used to describe  the stability of the model and the average deviation of the  measured value from the true value.

Modeling and validation The results of previous showed that regression model  such as linear regression, partial least squares regres­ sion (PLSR), Lasso regression, support vector regression  (SVR) and many other regression methods could be used  to estimate these agronomy parameters like biomass, LAI  and the content of nitrogen. In this study, the SVR algo­ rithm is employed to construct a weed biomass estima­ tion model. This study compared the effects of common  regression models with or without weeds CC calculated  by DeepLab V3+. RMSE and R2 were used for model  evaluation. Of the field data, 50% of 2022 and 2023 data  were selected for modeling and 50% for validation.

Semantic segmentation effect of weeds There was still some overlap between wheat and weeds  in the orthophotos during the wintering stage, which  resulted in large errors when attempting to distinguish  weeds directly from wheat. In this research, five semantic  segmentation methods were used to distinguish weeds,

m

i=1(pyi −tyi)2 (6)

1 m

RMSE =

SSE = m

i=1(pyi −tyi)2 (7)

Page 7 of 15 Liu et al. Plant Methods          (2024) 20:144

Fig. 4  Histogram of wheat and weeds

more accurately. The ResNet-38 model has the short­ est processing time per image, while the PSPNet has the  longest. The processing time for DeepLabV3 + is 46.5ms,  which is within an acceptable range.

As shown in Fig. 7, the segmentation performance of  different models on the original RGB images indicates  that DeepLabV3 + achieves the best results, accurately  identifying almost all wheat and weeds, with good per­ formance in the edge regions of the wheat. The main  issue with the lower accuracy of the other models is the  high rate of missed wheat identification and the high  rate of weed misidentification. PSPNet, which performs  the worst, can only identify the central regions of row- planted wheat, with the edge areas almost entirely mis­ identified as weeds. Additionally, the models show little  difference in their ability to identify land, with all models  accurately recognizing land.

Fig. 5  Reflectance curve of wheat and weeds

and the results were shown in Table  2. Most models  have high recognition accuracy for cultivated land, with  IoU values above 90; the UNet model was found to have  the highest IoU value. However, models other than Dee­ pLabV3 + have poor recognition effects on weeds and  wheat. It can recognize weeds and wheat with an MIoU  value of over 85, which can identify weeds and wheat

The choice of seeding method and different growth  stages have an impact on the results of the semantic  segmentation of weeds (Fig. 8). The results showed that  the F1, MIoU, precision, and Recall values of the model  for weed and wheat monitoring were higher than 85%.

Page 8 of 15 Liu et al. Plant Methods          (2024) 20:144

Fig. 6  The estimation of weed biomass using canopy cover or vegetation indices under different conditions. The unit of the RMSE is kg·ha-1

The segmentation accuracy of the model for wheat was  slighter than that of weeds. What’s more, we found that  sowing methods had a greater influence on the segmen­ tation results than under different growth stages, with  scattered wheat fields showing higher precision in detect­ ing both wheat and weeds. The segmentation precision

value for the scattered wheat was 91.27%, whereas for  drilled wheat, it was only 87.51%. In weeds, both missing  and improper segmentation occurred in the edge areas  regardless of the sowing method.

The DeepLabv3 + model exhibits clear advantages in  distinguishing weeds from wheat, but it is unable to

Page 9 of 15 Liu et al. Plant Methods          (2024) 20:144


> **Table 2  The detection results of different models**

> Method
Weed
Wheat
Land
MIoU
Recall
F1
Time (ms)
ResNet-38_MS_COCO
67.2
71.6
91.3
76.7
89.3
76.7
30.6
PSPNet
61.5
68.6
92.5
74.2
90.7
73.3
76.7
DeepLabV3
70.6
70.3
94.2
78.4
90.5
79.3
37.6
UNet
77.4
79.5
95.8
84.3
94.2
85.1
39.2
DeepLabV3+
83.3
87.5
95.6
88.8
90.6
96.8
46.5

Fig. 7  The semantic segmentation performance of different models

determine the amount of weeds and formulate preven­ tive measures. The vegetation index has been proven to  be highly reliable in estimating biomass. As shown in  Fig. 9, the common vegetation index correlates well with  wheat and weeds biomass in different growth periods.  Notably, the NDVI shows a higher correlation than other  vegetation indexes. The (960 nm, 733 nm) combination  of NDVI combination has the highest correlation with  wheat during the wintering period, whereas the (960 nm,  719  nm) combination has the highest correlation with  weeds during the same period. Similarly, the (960  nm,  710 nm) combination of NDVI has the highest correla­ tion with wheat during the jointing period, while the  (960 nm, 700 nm) combination has the highest correla­ tion for weeds during the same period. The correlation  between the combinations mentioned above and their  respective biomass all exceeds 0.92, indicating that they  can be utilized to estimate the corresponding biomass.

variables for SVR models to assess weed occurrences  during the wintering and regrowth stages of both drilled  and broadcast wheat. Remarkably, favorable results were  obtained, with modeling R2 consistently exceeding 0.85.  Weed biomass estimation during the wintering period  demonstrated higher precision, with modeling RMSE  remaining below 8  kg·ha-1 for both drilling and broad­ casting scenarios. However, during the regrowth stage,  due to the increased wheat population, modeling preci­ sion slightly diminished, with RMSE values not exceed­ ing 20  kg·ha-1. Model validation was conducted on  independent samples, as depicted in Fig. 10. The preci­ sion of weed biomass estimation substantially improved  for both seeding methods and growth stages. During  the wintering period, weed biomass estimation exhib­ ited superior accuracy compared to the regrowth stage,  with an average RMSE of only 40.03 kg·ha-1. Among the  winter scenarios, weed estimation accuracy was highest  for drilled conditions, with an RMSE of only 9.28 kg·ha-1.  Conversely, under broadcast conditions during the  regrowth stage, weed biomass estimation was the least  accurate, with an R2 of only 0.6 and an elevated RMSE  of 30.38 kg·ha-1. In summary, weed monitoring accuracy  was generally higher under drilled conditions, with an

Estimation of weed biomass Considering the difficulty of solely utilizing CC and  vegetation indices to estimate weed occurrences, and  recognizing the strong correlations between CC and  multiple vegetation indices with weed biomass, this study  employed CC and several vegetation indices as input

Page 10 of 15 Liu et al. Plant Methods          (2024) 20:144

Fig. 8  Segmentation results of DeepLabV3+. (A) and (B) are the original images of the broadcast sowing wheat field and drilled sowing wheat field; (C)  and (D) are the segmentation results; (E) and (F) are the segmentation accuracy values of wheat and weeds

average RMSE 2.17 kg·ha-1 lower than that under broad­ cast conditions.

under different treatments. As shown in Fig.  11, an  increase in the number of weeds led to a corresponding  decrease in wheat dry weight, with a maximum reduc­ tion of 71% compared to areas without weeds. Similarly,  the number of weeds also harmed yield, with a maximum  reduction of 4320 kg·ha-1, or a 60% drop. However, the

The impact of weeds To further clarify the effects of weeds on wheat, we ana­ lyzed the impacts on wheat dry weight and grain yield

Page 11 of 15 Liu et al. Plant Methods          (2024) 20:144

Fig. 9  Correlation analysis between spectrum and biomass of weeds and wheat

impact of weeds varied depending on the sowing meth­ ods. Planting density and growth stages. Specifically, scat­ tered wheat was more susceptible to weeds than drilled  wheat, and wheat in high density was more affected than  in low density. Additionally, weeds that emerged during  the wintering stage had a greater impact on wheat yield.

[21], convolutional neural networks have been used to  distinguish crops and weeds during the seedling period  [22], and deep convolutional neural networks have been  used to identify weeds among rapeseed rows [23]. How­ ever, these methods are limited to the seedling stage,  where the difference between weeds and crops is more  significant, and the images are mostly collected near the  ground. Similar characteristics of weeds and wheat make  monitoring weeds with UAVs more difficult. Considering  that the convolutional neural network model can better  identify weeds [24], the filtered convolution structure can  identify weeds in UAV images.


## Discussion

The identification of farmland weeds has always been a 
research focus in smart agriculture. Traditional meth­
ods primarily rely on extracting image color, morphol­
ogy, and texture features [5, 18], or distinguishing weeds 
and crops through morphological features [19]. However, 
wheat field weeds, especially grass weeds and wheat, 
share similar features, making it difficult to differentiate 
them. Gašparović et al. used UAV images to distinguish 
between oats and weeds [20]. They found that weed iden­
tification methods based on color features have large lim­
itations, especially when the crop and weeds are similar 
in color. Moreover, due to the color and spectral similari­
ties between wheat and weeds, it is not easy to success­
fully distinguish the two using conventional machine 
learning classification methods. Consequently, scholars 
have turned to deep learning algorithms to identify farm­
land weeds. For instance, the SegNet segmentation net­
work has been used to distinguish sugar beets and weeds

Therefore, this study constructed a comprehensive  wheat field weed dataset by acquiring images from mul­ tiple locations. What’s more, given the complexity of  precisely distinguishing these regions, some boundary  inaccuracies between these classes were unavoidable  when preparing the dataset. The primary focus was on  maximizing weed identification while minimizing the  labeling of wheat and bare soil. This strategy was cho­ sen to reduce the risk of missed weed detection, even  if it led to a higher false positive rate. In practical weed  management, intervention is usually required only when  weed populations reach a certain threshold, making  false positives less critical than missed detections. We  selected several classical semantic segmentation models

Page 12 of 15 Liu et al. Plant Methods          (2024) 20:144

Fig. 10  Model testing results using an independent dataset. The unit of RMSE is kg·ha-1

based on this dataset to perform weed segmentation in  wheat fields. To ensure the accuracy of the segmentation  results, this study compared the performance of different  models and continuously tuned parameters, ultimately  optimizing the DeepLabV3 + model, which exhibited the  best performance for weed segmentation in wheat fields.  This model utilizes an encoder-decoder architecture,  where the encoder architecture uses DeepLabV3, and the  decoder uses a simple but effective module to restore the  target boundary details. It can use expanded convolution

to control the resolution of features under specified com­ puting resources, resulting in better weed identification  accuracy. The model used in this research can identify  weeds in wheat fields and has an MIoU value of 88.8.

The findings of this study demonstrate that, with  proper tuning and adequate training, classical semantic  segmentation models can effectively segment wheat field  weeds and achieve satisfactory accuracy. However, these  classical models have certain limitations. For instance,  they typically require large datasets for effective training,

Page 13 of 15 Liu et al. Plant Methods          (2024) 20:144

Fig. 11  Effects of weeds on wheat growth. (A) The effects of weeds on wheat dry weight, (B) The effects of weeds on wheat grain yield. J: jointing stage,  W: wintering stage, B: Broadcast sowing, D: drill sowing, L: plant density of 180 × 104 plant·ha-1, H: plant density of 300 × 104 plant·ha-1

and their model sizes are relatively large, which may  pose challenges in practical applications. Future research  could build upon the results of this study by further  optimizing these classical models to reduce the training  data requirements and decrease the model size, thereby

enhancing their efficiency and applicability in real-world  scenarios.

The convolutional neural network has clear advan­ tages in distinguishing field weeds and wheat, but it is not  effective in evaluating the amount and degree of damage  of weeds. To realize the precise prevention and control

Page 14 of 15 Liu et al. Plant Methods          (2024) 20:144

of weeds, improve the UAV plant protection spray effi­ ciency, and protect the ecological environment, it is  necessary to construct a distribution map of the occur­ rence of weeds in the field. Although previous studies  have proposed methods for estimating vegetation bio­ mass with RGB images [25, 26], the estimation of weed  biomass in wheat fields based on RGB images is not sat­ isfactory due to the sowing methods and the interaction  between weeds and wheat. After analysis, some spectral  indexes have very significant correlations with the bio­ mass of wheat and weeds. After locating the weed occur­ rence area, we extract the spectral characteristics of weed  areas, use the vegetation index to estimate the occur­ rence of weeds, and evaluate its image of wheat growth. If  only hyperspectral UAVs are used to obtain images, and  then weeds are classified, the flying height of the UAV  must be set below 25  m to effectively train the Deep­ LabV3 + model, which will result in low image acquisition  efficiency. Therefore, our research combined the images  taken by hyperspectral UAV and the small RGB UAV  to achieve the highest image acquisition efficiency. This  study utilized a combination of hyperspectral cameras  and high-definition cameras to monitor the biomass of  graminaceous weeds in wheat fields. The reasons include:  graminaceous weeds in wheat fields have a high similar­ ity to wheat in terms of spectral and color characteristics,  but they can be distinguished based on leaf structure  and other texture information. These details can only be  captured by high-definition cameras. If deep learning  algorithms are to be used for the identification of grami­ naceous weeds in wheat fields, it is necessary to obtain  canopy images with high-definition cameras. While  hyperspectral cameras can effectively reflect the biomass  of crop populations, most current hyperspectral cameras  do not have a high enough resolution, making it difficult  to distinguish between graminaceous weeds and wheat  through spectral images. This research has confirmed  that the 960 nm and 710 nm bands are closely related to  the biomass of graminaceous weeds. In the future, with  the improvement of the resolution of spectral sensors, it  will be possible to estimate the occurrence of gramina­ ceous weeds using only multispectral drones.

a maximum occlusion of 20% during the jointing stage.  The wider row spacing of drilled wheat led to heavier  weed occlusion compared to scattered wheat. The occlu­ sion issue affects the accuracy of weed monitoring, but  it has less impact on the occurrence of weeds and fixed- point weeding. Therefore, we did not collect further data  pertinent to the occlusion issue.


## Conclusions

This study developed a method for monitoring weed 
occurrence in wheat fields using deep learning algo­
rithms and spectral analysis techniques. The findings 
indicate that traditional image attributes such as color 
and texture pose challenges in distinguishing grass 
weeds in wheat fields. However, the application of deep 
learning algorithms significantly enhances weed iden­
tification accuracy. Among the evaluated algorithms, 
DeepLabV3 + demonstrated superior performance, sur­
passing segmentation methods like UNet and PSPNet. 
By selecting sensitive NDVI bands, weed biomass can 
be effectively estimated, establishing a robust framework 
for assessing the impact of weed infestations. The deep 
learning-based weed canopy cover identification model 
in this study accurately estimates weed canopy cover. Fur­
thermore, integrating canopy cover with vegetation indi­
ces enhances the precision of weed biomass estimation. 
This proposed method facilitates efficient UAV-based 
weed monitoring in wheat fields and the development of 
targeted plant protection strategies, providing technical 
support for UAV and precision plant protection.

Author contributions TL: research design, model establishment and discussion. YZ: results analyzing  and discussion. HW: experiments and writing. WW: experiments. TY: model  establishment. WZ: discussion and writing. SZ: experiments. CS: experiments.  ZY: review & editing, project administration and supervision.

Funding This research was mainly supported by the Special Fund for Independent  Innovation of Agricultural Science and Technology in Jiangsu, China  (CX(22)3112) and National Natural Science Foundation of China (32172110,  31701355, 31771711, 31671615).

Data availability Data will be made available on request.

The method proposed in our study can realize the  monitoring of the occurrence of weeds in wheat fields,  but there is still no better way to solve the occlusion  problem. According to experimental surveys, different  wheat planting densities, sowing methods, and the occlu­ sion of wheat on weeds during growth periods are dif­ ferent. In the wintering period, the occlusion of wheat  on weeds generally did not exceed 5%, while the occlu­ sion increased in the jointing period but generally did  not exceed 10%. Increasing the planting density from  180 × 104 plant·ha-1 to 300 × 104 plant·ha-1 resulted in a  3% increase in occlusion during the wintering stage, with

Declarations

Ethical approval Not applicable.

Competing interests The authors declare no competing interests.

Received: 11 October 2023 / Accepted: 11 September 2024

Page 15 of 15 Liu et al. Plant Methods          (2024) 20:144


## References

1.	
Adeux G, Vieren E, Carlesi S, Bàrberi P, Munier-Jolain N, Cordeau S. Mitigating 
crop yield losses through weed diversity. Nat Sustain. 2019;2(11):1018–26.
2.	
San Martín C, Long DS, Gourlie JA, Barroso J. Spring crops in three year rota­
tions reduce weed pressure in winter wheat. Field Crop Res. 2019;233:12–20.
3.	
Nakka S, Jugulam M, Peterson D, Asif M, Innovations HP, Agronomy DO, Uni­
versity KS. Herbicide resistance: development of wheat production systems 
and current status of resistant weeds in wheat cropping systems. T Crop J. 
2019;7(6):750–60.
4.	
Ashraf T, Khan YN. Weed density classification in rice crop using computer 
vision. Comput Electron Agr. 2020;175:105590.
5.	
Sabzi; Sajad; Abbaspour-Gilandeh. García-Mateos; Ginés, a fast and accurate 
expert system for weed identification in potato crops using metaheuristic 
algorithms. Comput Ind. 2018;98:80–9.
6.	
Raja R, Nguyen TT, Slaughter DC, Fennimore SA. Real-time weed-crop classifi­
cation and localisation technique for robotic weed control in lettuce. Biosyst 
Eng. 2020;192:257–74.
7.	
Raveendra P, Siva Reddy V, Subbaiah GV. Vision based weed recognition using 
LabVIEW environment for agricultural applications. Materials Today: Proceed­
ings 2020, 23, 483–489.
8.	
Jiang H, Zhang C, Zhang Z, Mao W, Wang D, Wang D. Detection method of 
corn weed based on mask R-CNN. T. Chin Soc Agric Mach. 2020;51(6):220–8.
9.	
Li Y, Al-Sarayreh M, Irie K, Hackell D, Bourdot G, Reis MM, Ghamkhar K. Iden­
tification of weeds based on hyperspectral imaging and machine learning. 
Front Plant Sci. 2021;11:611622.
10.	 Pan R, Luo Y, Wang C, Zhang C, He Y, Feng L. Classifications of oilseed 
rape and weeds based on hyperspectral imaging. Spectrosc Spect Anal. 
2017;37(11):3567–72.
11.	 Zhang SH, He L, Duan JZ, Zang SL, Yang TC, Schulthess URS, Feng W. Aboveg­
round wheat biomass estimation from a low-altitude UAV platform based 
on multimodal remote sensing data fusion with the introduction of terrain 
factors. Precision Agric. 2024;25(1):119–145.
12.	 Wang T, Thomasson JA, Yang C, Isakeit T, Nichols RL. Automatic classifica­
tion of cotton root rot disease based on UAV remote sensing. Remote Sens. 
2020;12(8):1310.
13.	 Zhao J, Li Z, Lu L, Jia P, Yang H, Lan Y. Weed identification in maize field based 
on multispectral remote sensing of unmanned aerial vehicle. Scientia Agri­
cultural Sinica. 2020;53(8):1545–55.
14.	 Bouguettaya A, Zarzour H, Kechida A, Taberkit AM. Deep learning techniques 
to classify agricultural crops through UAV imagery: a review. Neural Comput 
Appl. 2022;34(12):9511–36.
15.	 Li B, Xu X, Zhang L, Han J, Bian C, Li G, Liu J, Jin L. Above-ground biomass 
estimation and yield prediction in potato by using UAV-based RGB and 
hyperspectral imaging. Isprs J Photogramm. 2020;162:161–72.

16.	 Chen LC, Papandreou G, Kokkinos I, Murphy K, Yuille AL. DeepLab: semantic  image segmentation with Deep Convolutional nets, atrous Convolution, and  fully connected CRFs. Ieee T Pattern Anal. 2018;40(4):834–48. 17.	 Krestenitis M, Orfanidis G, Ioannidis K, Avgerinakis K, Kompatsiaris I. Oil spill  identification from satellite images using deep neural networks. Remote  Sens. 2019;11(15):1762. 18.	 Elstone L, How KY, Brodie S, Ghazali MZ, Heath WP, Grieve B. High speed  crop and weed identification in lettuce fields for precision weeding. Sensors.  2020;20(2):455. 19.	 Bakhshipour A, Jafari A. Evaluation of support vector machine and artificial  neural networks in weed detection using shape features. Comput Electron  Agr. 2018;145:153–60. 20.	 Gašparović M, Zrinjski M, Barković Đ, Radočaj D. An automatic method for  weed mapping in oat fields based on UAV imagery. Comput Electron Agr.  2020;173:105385. 21.	 Sa I, Chen Z, Popovic M, Khanna R, Liebisch F, Nieto J, Siegwart R. weedNet:  dense semantic weed classification using multispectral images and MAV for  smart farming. IEEE Rob Autom Lett. 2018;3(1):588–95. 22.	 Jiang H, Zhang C, Qiao Y, Zhang Z, Zhang W, Song C. CNN feature based  graph convolutional network for weed and crop recognition in smart farm­ ing. Comput Electron Agr. 2020;174:105450. 23.	 Asad MH, Bais A. Weed detection in canola fields using maximum likelihood  classification and deep convolutional neural network. Inform Process Agric.  2019;6(4):1–12. 24.	 Farooq A, Hu J, Jia X. Analysis of spectral bands and spatial resolutions for  weed classification Via Deep Convolutional neural network. IEEE Geoence  Remote Sens Lett. 2019;16(2):183–7. 25.	 Maimaitijiang M, Sagan V, Sidike P, Maimaitiyiming M, Hartling S, Peterson KT,  Maw MJW, Shakoor N, Mockler T, Fritschi FB. Vegetation Index Weighted Can­ opy volume model (CVMVI) for soybean biomass estimation from unmanned  aerial system-based RGB imagery. Isprs J Photogramm. 2019;151:27–41. 26.	 Guo Z, Wang T, Liu S, Kang W, Chen X, Feng K, Zhang X, Zhi Y. Biomass and  vegetation coverage survey in the Mu us sandy land - based on unmanned  aerial vehicle RGB images. Int J Appl Earth Obs. 2021;94:102239.

Publisher’s note Springer Nature remains neutral with regard to jurisdictional claims in  published maps and institutional affiliations.
