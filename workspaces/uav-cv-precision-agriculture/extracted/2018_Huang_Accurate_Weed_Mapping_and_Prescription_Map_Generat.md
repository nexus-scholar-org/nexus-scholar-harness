---
workspace_id: SCI-000582
doi: 10.3390/s18103299
title: Accurate Weed Mapping and Prescription Map Generation Based on Fully Convolutional
  Networks Using UAV Imagery
authors:
- family_name: Huang
  given_name: Huasheng
  orcid: https://orcid.org/0000-0002-6546-6501
- family_name: Deng
  given_name: Jizhong
  orcid: https://orcid.org/0009-0002-1456-5494
- family_name: Lan
  given_name: Yubin
  orcid: https://orcid.org/0000-0001-6664-5571
- family_name: Yang
  given_name: Aqing
  orcid: https://orcid.org/0009-0005-7049-2017
- family_name: Deng
  given_name: Xiaoling
  orcid: https://orcid.org/0000-0001-5588-3443
- family_name: Wen
  given_name: Sheng
  orcid: null
- family_name: Zhang
  given_name: Huihui
  orcid: https://orcid.org/0000-0002-9781-6086
- family_name: Zhang
  given_name: Yali
  orcid: https://orcid.org/0000-0001-7795-9277
year: 2018
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:35:03.462934+00:00'
---

# Accurate Weed Mapping and Prescription Map Generation Based on Fully Convolutional Networks Using UAV Imagery

sensors

Article Accurate Weed Mapping and Prescription Map

Generation Based on Fully Convolutional Networks Using UAV Imagery

Huasheng Huang 1,2, Jizhong Deng 1,2,*, Yubin Lan 1,2,*, Aqing Yang 3, Xiaoling Deng 2,3, Sheng Wen 2,4, Huihui Zhang 5 and Yali Zhang 1,2

1 College of Engineering, South China Agricultural University, Wushan Road, Guangzhou 510642, China; huanghsheng@stu.scau.edu.cn (H.H.); ylzhang@scau.edu.cn (Y.Z.) 2 National Center for International Collaboration Research on Precision Agricultural Aviation Pesticide Spraying Technology, Wushan Road, Guangzhou 510624, China; dengxl@scau.edu.cn (X.D.); vincen@scau.edu.cn (S.W.) 3 College of Electronic Engineering, South China Agricultural University, Wushan Road, Guangzhou 510624, China; yangaqing@stu.scau.edu.cn 4 Engineering Fundamental Teaching and Training Center, South China Agricultural University, Wushan Road, Guangzhou 510624, China 5 USDA, Agricultural Research Service, Water Management Research Unit, 2150 Centre Ave., Building D, Suite 320, Fort Collins, CO 80526-8119, USA; huihui.zhang@ars.usda.gov * Correspondence: jz-deng@scau.edu.cn (J.D.); ylan@scau.edu.cn (Y.L.)

 

Received: 25 August 2018; Accepted: 18 September 2018; Published: 1 October 2018

Abstract: Chemical control is necessary in order to control weed infestation and to ensure a rice yield. However, excessive use of herbicides has caused serious agronomic and environmental problems. Site speciﬁc weed management (SSWM) recommends an appropriate dose of herbicides according to the weed coverage, which may reduce the use of herbicides while enhancing their chemical effects. In the context of SSWM, the weed cover map and prescription map must be generated in order to carry out the accurate spraying. In this paper, high resolution unmanned aerial vehicle (UAV) imagery were captured over a rice ﬁeld. Different workﬂows were evaluated to generate the weed cover map for the whole ﬁeld. Fully convolutional networks (FCN) was applied for a pixel-level classiﬁcation. Theoretical analysis and practical evaluation were carried out to seek for an architecture improvement and performance boost. A chessboard segmentation process was used to build the grid framework of the prescription map. The experimental results showed that the overall accuracy and mean intersection over union (mean IU) for weed mapping using FCN-4s were 0.9196 and 0.8473, and the total time (including the data collection and data processing) required to generate the weed cover map for the entire ﬁeld (50 × 60 m) was less than half an hour. Different weed thresholds (0.00–0.25, with an interval of 0.05) were used for the prescription map generation. High accuracies (above 0.94) were observed for all of the threshold values, and the relevant herbicide saving ranged from 58.3% to 70.8%. All of the experimental results demonstrated that the method used in this work has the potential to produce an accurate weed cover map and prescription map in SSWM applications.

Keywords: UAV; semantic labeling; FCN; weed mapping; prescription map


## 1. Introduction

Chemical control is necessary to control weed infestation and to ensure rice production [1]. Traditionally, the chemical control strategy has three steps: a single pre-emergence herbicide application, a post-emergence herbicide treatment, and an optional late post-emergence chemical spray [2].

Sensors 2018, 18, 3299; doi:10.3390/s18103299 www.mdpi.com/journal/sensors

Sensors 2018, 18, 3299 2 of 12

This strategy has been proven to be effective for weed control, through years of rice cultivation applications [3]. However, the consistently increased use of herbicides has caused a negative impact on rice production and the environment [4]. Usually farmers carry out uniform herbicide spraying over the entire field and do not consider the distribution of weed infestations [5]. Excessive herbicides are applied over the areas with an absence of weed infestations, resulting in environmental pollution and chemical residues [1]. Site specific weed management (SSWM) recommends a chemical reduction in the application and utilization of adequate herbicides based on the weed coverage [6]. In the context of SSWM, the prescription map can provide decision making information for a variable-rate spraying machine (i.e., tractors or UAVs), which may reduce the use of herbicides while enhancing their chemical effects [7].

However, in order to obtain a prescription map, it is necessary to produce a weed cover map [8]. UAV remote sensing provides a non-destructive and cost-effective platform for rapid monitoring of weed infestations [9]. Compared with other remote sensing platforms (i.e., satellite and piloted aircraft remote sensing), UAV is able to ﬂy at a low altitude and can capture high resolution imagery, which may monitor small weed patches in detail [10]. Several works on weed mapping using UAV remote sensing have been conducted [4,6,8]. Peña et al. [6] used UAV multispectral imagery for weed mapping in maize ﬁelds. An automatic object-based image analysis (OBIA) procedure was developed, and a weed cover map was produced with 86% overall accuracy. López-Granados et al. [4] focused on the evaluation of different sensors (red, green, and blue (RGB) and multispectral cameras) and altitudes (30 and 60 m) for weed mapping. A robust image analysis method was developed for weed mapping, and high accuracies were observed using the multispectral camera at any ﬂight altitude. Most of these studies were based on the OBIA framework. The use of the OBIA method requires a process of feature selection, which must be performed by manual designs [6]. Although hand-designed features (i.e., texture features and vegetation indices) [11–13] are a proven approach, they are application dependent and hard to generalize [14].

Fully convolutional networks (FCN) is an automatic feature learning algorithm that can address the disadvantages of OBIA approaches [15]. FCN implements the forward and backward process in an end-to-end mode, which performs the feature learning automatically [16]. In recent years, FCN has achieved great success in computer vision [16,17] and remote sensing applications [18–20]. FCN introduces the pixel-to-pixel translation in an end-to-end mode, which shows great potential for the weed mapping of UAV imagery. However, no related study on weed mapping using FCN can be accessed, except for the work of [21,22]. In these works, semantic labeling approaches were directly applied on the collected UAV imagery. The experimental results showed that the semantic labeling approaches outperformed others in terms of accuracy and efﬁciency. However, both of these works did not generate a weed cover map or a prescription map for the whole ﬁeld, which may not satisfy the requirement of practical SSWM applications. The objective of this work is as follows: to (1) compare the performance of different workﬂows so as to generate a weed cover map for the whole ﬁeld; (2) carry out the theoretical analysis and practical evaluation to seek for an architecture improvement of FCN, which may bring a performance boost in accuracy and efﬁciency; and (3) generate a prescription map, which may provide decision-making information for SSWM applications.


## 2. Data Collection

2.1. Study Field and Data Collection

Experiments were conducted in a rice ﬁeld located in Guangdong Province, China (23◦14’25” N, 113◦38’12” E, in reference system datum WGS84). The ﬁeld was a rectangle area of 90 × 60 m with ﬂat ground. The seeds were sown on 21 August 2017, and the rice started to emerge 15 days after sowing. The study plot was naturally infested with Cyperus iric [23] and L. chinensis [24]. The photograph of the studied ﬁeld is illustrated in Figure 1.

Sensors 2018, 18, 3299 3 of 12


> **Figure 1. The photograph of the studied rice ﬁeld.**

Data collection was carried out on 2nd and 10th October 2017, when the rice and weeds were both in their early growth stages, and when the herbicide treatment was recommended. Phantom 4 (SZ DJI Technology Co., Ltd., Shenzhen, China) was used for data collection, and a 50 × 60 m plot was delimited in order to perform the ﬂights. During the experiments, the ﬂight altitude was set to 10 m, with a resolution of 0.5 cm per pixel. Sequences with a 70% forward-lap and 60% side-lap imagery were collected to cover the entire experimental plot. On 2nd and 10th October, 54 and 50 imagery (3000 × 4000 pixels) were collected in the experiments, respectively.

2.2. Dataset Preparation

Image mosaicking is an important step prior to image analysis [4]. In this work, the collected imagery were stitched together to form the ortho-mosaicked imagery using the software of Photoscan [25]. However, the ortho-mosaicked imagery is usually quite large (14,000 × 13,000 pixels in our work), making it a difficult task to carry out the data processing with limited CPU and GPU memory. In order to address this problem and to retain the original spatial resolution, we split the ortho-mosaicked imagery into small patches (1000 × 1000 pixels), similar with the work of Zhang et al. [26]. Following this strategy, the datasets of D02-1 and D10-1 were generated from the ortho-mosaicked imagery obtained on 2nd and 10th October 2017. Besides that, we also directly split the collected imagery into small patches (1000 × 1000 pixels), which generated the dataset of D02-2 and D10-2, as shown in Table 1.


> **Table 1. Speciﬁcation for the dataset.**

Name Flight Date Number of Patches Description

D02-1 2nd October 2017 182 Divided from the ortho-mosaic imagery D10-1 10th October 2017 182 Divided from the ortho-mosaic imagery D02-2 2nd October 2017 648 Divided from the collected imagery D10-2 10th October 2017 600 Divided from the collected imagery

For each imagery in the dataset, its corresponding ground truth (GT) label data was produced by careful manual labeling. With the high spatial resolution of UAV imagery, the weed-crop discrimination can be visually accessed, making it feasible to manually label the imagery at a pixel level. Thus, each sample in the dataset represented one image-GT label pair, and the GT label is used as the standard when evaluating the performance of the classiﬁers. Three image-GT label pairs are illustrated in Figure 2.

Sensors 2018, 18, 3299 4 of 12


> **Figure 2.**

> Three image-ground truth (GT) label pairs in the dataset: (a) images in the dataset;
(b) corresponding GT labels.


## 3. Methodology

In this work, two different workﬂows were applied to produce the weed cover map for the whole ﬁeld. The performance of both workﬂows were evaluated and compared. Fully convolutional networks (FCN) was employed for the pixel level classiﬁcation. Finally, the chessboard segmentation method was used to produce the prescription map based on the weed cover map.

3.1. Workﬂow

Two different workﬂows were adopted as candidates, as shown in Figure 3. The ﬁrst workﬂow conducted the mosaicking operation to generate the ortho-mosaicked imagery for the whole ﬁeld, and then it performed a per-pixel classiﬁcation to create the weed cover map. Inspired by the fact that some sections in the ortho-mosaicked imagery were blurring, which made it difﬁcult to distinguish and may cause misclassiﬁcation during the classiﬁcation stage, we directly applied the labeling process on the collected imagery in the second workﬂow, which may avoid the ambiguous pixels in the classiﬁcation stage. After that, the mosaicking process was conducted on the classiﬁcation results, using the geo-information in the collected imagery. All of the mosaicking operations were performed using the software of Photoscan.


> **Figure 3. Two workﬂows to produce the weed cover map for the whole ﬁeld. (a) The workﬂow of**

> mosaicking-labeling; (b) the workﬂow of labeling-mosaicking.

Sensors 2018, 18, 3299 5 of 12

The evaluation of the workﬂows was measured for accuracy and efﬁciency. The accuracy was evaluated by the overall accuracy and the mean intersection over union (mean IU) [16], and the time efﬁciency was measured using the total time required to generate the weed cover map, including data collection and data processing.

3.2. Semantic Labeling

Classical FCN-8s was proven to be effective on weed mapping of UAV imagery [21], which outperformed the traditional methods in terms of accuracy and efﬁciency. In this work, we sought for an optimal network architecture that will bring about a performance improvement.

Similar with the network architecture of classical FCN-8s [16], an ImageNet pre-trained Convolutional Neural Network (CNN) [27] was adapted to fully convolutional networks and was transferred to our study using a fine-tuning technique. Besides that, two modifications were conducted on the baseline architecture of FCN-8s. (1) In the previous experiments on the skip architecture [21], it was proven that the fusion of the prediction results (fc8) and the shallow layer of pool4 can effectively increase the prediction accuracy, as shown in Figure 4a. However, the fusion with other shallow layers brings no performance boost. This result indicated that the information from pool4 is crucial for the classification task, so that the fusion with this layer can make up the information loss caused by the downsampling operation. However, this strategy cannot properly address this problem, which resulted in low precision and blurred edges in the classification result [26]. Based on this result, the skip architecture and the last pooling operation (pool5) were removed so as to avoid the information loss of the layer of pool4. (2) The original network was designed for the dataset of PASCAL VOC 2011 segmentation challenge [28], which has 1000 different classes. However, our dataset only has three categories (rice, weeds, and others). According to the work of Stathakis et al. [29], there should be a positive correlation between the number of output classes and the number of neurons in the intermediate fully connected layers. Based on this theory, the number of feature maps of intermediate layers (fc6 and fc7, which were transformed from the fully connected layers) was reduced. The number of feature maps of the intermediate layers (fc6 and fc7) was set to 2048 through several experiments and an evaluation on the validation set (refer to Section 4). The network architecture of classical FCN-8s and the modified FCN-4s can be seen from Figure 4.


> **Figure 4. The illustration of the architecture of fully convolutional networks (FCN): (a) architecture of**

> classical FCN-8s; (b) architecture of the modiﬁed FCN-4s.

Besides the modiﬁed FCN-4s, the classical FCN-8s [21] and Deeplab [22] were also applied and evaluated as comparison. For the FCN-8s, an ImageNet pre-trained CNN [27] was applied as a baseline architecture. The ﬁnal classiﬁcation layer was removed, and all of the fully connected layers were converted to convolutions. Skip architecture was built to improve the prediction precision. The lower

Sensors 2018, 18, 3299 6 of 12

layers (pool4 and pool5) were fused with the higher layer (fc8), as shown in Figure 4a. For the Deeplab approach, a 101-layer ResNet [30] was adapted in fully convolutional forms, similar with the approach of FCN-8s. The weights pre-trained on ImageNet [30] were transferred to our dataset using ﬁne-tuning. Atrous convolution [17] was applied to extend the ﬁeld of view (FOW) of the convolutional ﬁlters, and the fully connected random ﬁled (CRF) [31] was used to further improve the prediction accuracy.

In this section, the accuracy was evaluated by the overall accuracy and mean intersection over union (mean IU) [16], similar to Section 3.1. However, the time efﬁciency was also measured using the processing time for one single image, which is the normal way for the evaluation adopted by most semantic labeling approaches [16,17].

3.3. Prescription Map Generation

The prescription map can be generated from the weed cover map. According to the work of López-Granados [4], a chessboard segmentation process was applied to build a grid framework of the prescription map. The weed cover map was split into small grids, and the comparison between the weed coverage of each grid and a given threshold was conducted: if the weed coverage of the grid is larger than the threshold value, it will be marked as a treatment area, otherwise it will be marked as a non-treatment area. The grid size is adjustable according to the different spraying machines, and it was set to 0.5 × 0.5 m in this work, in accordance with the site-speciﬁc sprayer [32].

For this section, the accuracy was calculated from two prescription maps (one generated from the weed cover map output by our algorithm, and the other from the GT label), which can be given by the following:

accuracy = The number o f grid −based areas correcly classi f ied

The number o f all grid −based areas (1)

For each prescription map, its relevant herbicide saving was calculated. According to the work of de Castro [8], herbicide saving is calculated in terms of the non-treatment area, which can be given by the following:

herbicide saving = Pnon = 1 −Ptreatment (2)

where Pnon and Ptreatment represent the proportion of the non-treatment and treatment areas.


## 4. Results and Discussions

In this section, the experiments on workﬂows, semantic labeling, and prescription map generation will be conducted. In the experiments on workﬂows and semantic labeling approaches, the dataset was divided into training, validation, and testing set. The three datasets were used for parameter updating, hyper parameter tuning, and performance evaluation, respectively. All of the experiments were conducted on a computer with an Intel i7-7700 CPU and a NVIDIA GTX 1080 Ti GPU. During the process of weed mapping, the mosaicking operation was carried out in the CPU, while the semantic labeling approaches were performed using the GPU.

4.1. Workﬂow

In this section, two workﬂows (mosaicking-labeling and labeling-mosaicking) were applied in order to generate the weed cover map for the whole ﬁeld. For the workﬂow of mosaicking-labeling, the dataset D02-1 (182 samples) was adopted as a training set. From dataset D10-1, 30% was randomly selected as validation set (54 samples), and the rest samples in the dataset D10-1 (128 samples) were used as the testing dataset. There were two reasons for this choice, namely: (1) the training set and testing set were chosen from different dates, which may evaluate the generalization capability of the algorithm, and (2) the validation set and testing set were selected from the same date, which may ensure that the two datasets belonged to the same distribution. For the workﬂow of labeling-mosaicking, the dataset D02-2 (648 samples) was used as training set, and 30% of dataset D10-2 (180 samples)

Sensors 2018, 18, 3299 7 of 12

was randomly selected as the validation set. However, we still used the testing set of the previous workﬂow (mosaicking-labeling) as the testing set of this workﬂow (labeling-mosaicking), since the classiﬁcation on the ortho-mosaicked imagery is the ultimate objective of our algorithm.

In this section, the classical FCN-8s was used for the semantic labeling tasks. The quantitative results are listed in Table 2. From Table 2, it can be seen that both workﬂows obtained an approximate accuracy. However, because of the high overlapping in the collected imagery, directly processing on the collected imagery introduced too much redundant computation, which signiﬁcantly lowered the inference speed. From this perspective, the workﬂow of mosaicking-labeling is the optimal solution, and will be considered as the default framework for the following experiments.


> **Table 2. Experimental results of different workﬂows. The speed was measured using the total time**

> required to generate the weed cover map for the whole ﬁeld, including data collection and data
processing. Mean IU-mean intersection over union.

Workﬂow Overall Accuracy Mean IU Speed

Mosaicking–labeling 0.9096 0.8303 24.8 min Labeling–mosaicking 0.9074 0.8264 32.5 min

4.2. Semantic Labeling

In this section, the dataset (training, validation and testing set) was the same as the workﬂow of mosaicking-labeling (Section 4.1). FCN-8s, Deeplab, and our modiﬁed FCN-4s were applied for our dataset, respectively. The quantitative results and confusion matrix by different approaches are shown in Tables 3 and 4. From Table 3, it is obvious that Deeplab and FCN-4s outperformed FCN-8s in accuracy. From Table 4, it can be seen that the weed recognition rate of Deeplab and FCN-4s is above 0.90, which is higher than that of FCN-8s. There were two reasons possible for this result, namely: (1) the Deeplab used CRF to reﬁne the spatial details, which increased the prediction accuracy, and (2) the FCN-4s removed the last pooling layer, which reduced the information loss and obtained performance boost.


> **Table 3. Experimental results on different semantic labeling approaches. Speed-1 was measured using**

> the inference time for a single imagery (1000 × 1000 pixels), and speed-2 was measured using the total
time required to generate the weed cover map for the whole ﬁeld, including data collection and data
processing. FCN—fully convolutional networks.

Method Overall Accuracy Mean IU Speed-1 Speed-2

FCN-8s 0.9096 0.8303 0.413 s 24.8 min Deeplab 0.9191 0.8460 5.279 s 39.6 min FCN-4s 0.9196 0.8473 0.356 s 24.7 min


> **Table 4. Confusion matrix by different semantic labeling approaches. GT—ground truth.**

Method GT/Predicted Category Others Rice Weeds

others 0.939 0.042 0.018 rice 0.037 0.894 0.069 weeds 0.078 0.027 0.895

FCN-8s

others 0.922 0.044 0.034 rice 0.023 0.924 0.052 weeds 0.056 0.036 0.907

Deeplab

others 0.938 0.030 0.031 rice 0.037 0.913 0.049 weeds 0.055 0.039 0.905

FCN-4s

Sensors 2018, 18, 3299 8 of 12

Although the Deeplab method achieved a satisfactory result for accuracy, the CRF introduced too much computation, which signiﬁcantly slowed down the inference speed (Table 3). Therefore, it can be concluded that the FCN-4s strikes the best tradeoff between accuracy and efﬁciency. From Table 3, it can be found that the total time (including data collection and data processing) needed to generate the weed cover map for the entire ﬁeld (50 × 60m) using FCN-4s is less than half an hour, demonstrating its rapid response capability on weed infestation monitoring.

The weed cover maps generated by the different approaches are shown in Figure 5. From Figure 5, it can be seen that (1) the weeds (in yellow dashed lines) were misclassiﬁed as others by FCN-8s, while they were properly recognized by Deeplab and FCN-4s; (2) the rice (in blue dashed lines) was misclassiﬁed as weeds by FCN-8s, while they were well classiﬁed by Deeplab and FCN-4s. From the qualitative results of Figure 5, it can be concluded that the FCN-4s obtained a satisfactory result with a simpliﬁed architecture in an end-to-end mode, which required no post-processing.


> **Figure 5.**

> Weed cover maps output by different approaches.
(a) Ortho-mosaicked imagery.
(b) Corresponding GT-labels. The areas outside the studied plot were masked out (in black) and ignored
in the training and evaluation. (c) Output by FCN-8s. (d) Output by Deeplab. (e) Output by FCN-4s.

4.3. Prescription Map Generation

The prescription map can be generated from a weed cover map with a given weed threshold. According to the experimental results in Table 3, the weed cover map obtained by FCN-4s was used to generate the prescription map. For a given weed threshold, the grid with a higher weed coverage will be marked as the treatment area. In this section, six thresholds (0.00–0.25, with an interval of 0.05) were evaluated. The accuracy using different weed thresholds is shown in Figure 6. From Figure 6, it can be seen that, with increasing threshold values, the accuracy consistently increases. The reason for this result is that large weed patches were easier for the classifiers to detect, thus resulting in a higher accuracy. High accuracies (above 0.94 for all thresholds) were observed from Figure 6, demonstrating that our algorithm is qualified for treatment area prediction. The treatment area and herbicide saving with different weed thresholds were calculated and are shown in Table 5. From Table 5, it can be seen that, with increasing the weed thresholds, the treatment area consistently decreases. The relevant herbicide saving ranges from 58.3% to 70.8%, demonstrating great potential to reduce the use of herbicides in SSWM applications. From a practical perspective, a threshold of 0.0 would be recommended as the optimal weed threshold for SSWM applications. There are two reasons for this choice, namely:

Sensors 2018, 18, 3299 9 of 12

(1) the accuracy (above 0.94) of this threshold is qualified and the relevant herbicide saving (58.3%) is acceptable, and (2) this threshold would minimize the risk of missing weed infestation, which may cause weed-crop competition.


> **Figure 6. The accuracy curve with different weed thresholds.**


> **Table 5. Herbicide saving with different weed thresholds.**

Threshold Treatment Area Herbicide Saving

0.00 41.7% 58.3% 0.05 35.9% 64.1% 0.10 33.6% 66.4% 0.15 31.9% 68.1% 0.20 30.4% 69.6% 0.25 29.2% 70.8%

The prescription maps generated with different thresholds are illustrated in Figure 7. From Figure 7, it can be seen that the changes of the threshold value have little influence on the areas with a high weed coverage (in blue dashed lines), as the weed coverage of these areas is higher than all of the threshold values. However, for the areas with a lower weed coverage (in yellow dashed lines), the weed threshold can effectively adjust the treatment areas, as the areas with lower weed coverage than the threshold will be ignored. The prescription maps generated by our method (with all thresholds) generally correspond to that generated by the GT label, thanks to the high accuracy of the output weed cover map. From Figure 7, it can also be seen that an overestimation for treatment areas was observed in the results of all of the thresholds. However, from an agronomic perspective, it is acceptable, as it can reduce the risk allowing the weeds to go untreated [33].

Sensors 2018, 18, 3299 10 of 12


> **Figure 7. Prescription map generated with different weed thresholds. (a–c) Prescription map generated**

> from the GT label using the weed thresholds of 0.0, 0.1 and 0.2. (d–f) Prescription map generated
from the output weed cover map using the thresholds of 0.0, 0.1 and 0.2. From reference system
datum WGS84.


## 5. Conclusions

Prescription maps can provide decision making support for the spraying machine, which may effectively reduce the use of herbicide while enhancing the chemical effects. In this paper, the study on weed mapping and prescription map generation was conducted using UAV imagery. (1) The UAV imagery over a rice ﬁeld were captured at a high spatial resolution, and pre-processing was performed so as to generate our dataset. (2) Two different workﬂows (mosaicking-labeling and labeling-mosaicking) were applied in order to generate the weed cover maps. These workﬂows were evaluated and compared. The experimental results showed that the workﬂow of mosaicking-labeling outperformed the others in terms of efﬁciency with an approximate accuracy. (3) A modiﬁed FCN-4s introduced pixel-to-pixel translation from UAV imagery to weed cover maps. Theoretic analysis was conducted to seek for architecture improvement. The improved architecture was evaluated and compared with the classical FCN-8s and Deeplab. The experimental results showed that the modiﬁed FCN-4s outperformed others in both accuracy and efﬁciency. (4) A chessboard segmentation method was used to build the grid framework of the prescription map. Different weed thresholds were applied and evaluated. High accuracies (above 0.94) were observed for all of the thresholds, and the relevant herbicide savings ranged from 58.3% to 70.8%. The method applied in this paper was superior in efﬁciency, which may produce a prescription map for a rice ﬁeld (50 × 60 m) within half an hour, demonstrating its rapid response capability to the emergency of weed infestation.

However, for the study of weed mapping and prescription map generation, more data is needed to extend and evaluate the generalization capability of the algorithm. Besides rough weed recognition, classiﬁcation for speciﬁc weed species is also important for the SSWM applications, which can be extended based on our current work. All of these issues will be left as our future work.

Author Contributions: Conceptualization, J.D. and Y.L.; funding acquisition, Y.L.; methodology, S.W.; project administration, J.D.; software, H.H. and A.Y.; writing (original draft), H.H.; writing (review and editing), X.D., H.Z. and Y.Z.

Sensors 2018, 18, 3299 11 of 12

Funding: This research was funded by the Educational Commission of Guangdong Province of China for Platform Construction: International Cooperation on R&D of Key Technology of Precision Agricultural Aviation (grant no. 2015KGJHZ007), the Science and Technology Planning Project of Guangdong Province, China (grant no. 2017A020208046), the National Key Research and Development Plan, China (grant no. 2016YFD0200700), the National Natural Science Fund, China (grant no. 61675003), the Science and Technology Planning Project of Guangdong Province, China (grant no. 2016A020210100), the Science and Technology Planning Project of Guangdong Province, China (grant no. 2017B010117010), and the Science and Technology Planning Project of Guangzhou city, China (grant no. 201707010047).

Conﬂicts of Interest: The authors declare no conﬂict of interest.


## References

1. Dass, A.; Shekhawat, K.; Choudhary, A.K.; Sepat, S.; Rathore, S.S.; Mahajan, G.; Chauhan, B.S. Weed management in rice using crop competition-a review. Crop Prot. 2017, 95, 45–52. [CrossRef] 2. Qiu, G.; Li, J.; Li, Y.; Shen, S.; Ming, L.; Lu, Y. Aplication Technology of Two Times of Closed Weed Control in Mechanical Transplanted Rice Field. J. Weed Sci. 2016, 4, 33–38. 3. Gao, B.; Liu, D.; Hui, K.; Wu, X. Weed control techniques in direct seeding rice ﬁeld. Mod. Agric. Sci. Technol. 2007, 17, 114–117. 4. López-Granados, F.; Torres-Sánchez, J.; Serrano-Pérez, A.; de Castro, A.I.; Mesas-Carrascosa, F.J.; Peña, J. Early season weed mapping in sunﬂower using UAV technology: Variability of herbicide treatment maps against weed thresholds. Precis. Agric. 2016, 17, 183–199. [CrossRef] 5. Nordmeyer, H. Spatial and temporal dynamics of Apera spica-venti seedling populations. Crop Prot. 2009, 28, 831–837. [CrossRef] 6. Peña, J.; Torressánchez, J.; Serranopérez, A.; Lópezgranados, F. Weed mapping in early-season maize ﬁelds using object-based analysis of unmanned aerial vehicle (UAV) images. PLoS One 2013, 8, e77151. [CrossRef] [PubMed] 7. Lan, Y.; Thomson, S.J.; Huang, Y.; Hoffmann, W.C.; Zhang, H. Current status and future directions of precision aerial application for site-speciﬁc crop management in the USA. Comput. Electron. Agric. 2010, 74, 34–38. [CrossRef] 8. De Castro, A.; Torres-Sánchez, J.; Peña, J.; Jiménez-Brenes, F.; Csillik, O.; López-Granados, F. An Automatic Random Forest-OBIA Algorithm for Early Weed Mapping between and within Crop Rows Using UAV Imagery. Remote Sens. 2018, 10, 285. [CrossRef] 9. Lan, Y.; Shengde, C.; Fritz, B.K. Current status and future trends of precision agricultural aviation technologies. Int. J. Agric. Biol. Eng. 2017, 10, 1–17. 10. Castaldi, F.; Pelosi, F.; Pascucci, S.; Casa, R. Assessing the potential of images from unmanned aerial vehicles (UAV) to support herbicide patch spraying in maize. Precis. Agric. 2017, 18, 76–94. [CrossRef] 11. Ahonen, T.; Hadid, A.; Pietikäinen, M. Face Recognition with Local Binary Patterns. In Proceedings of the European Conference on Computer Vision, Prague, The Czech Republic, 11–14 May 2004; Springer: Berlin/Heidelberg, Germany, 2004; pp. 469–481. 12. DEFRIES, R.S.; TOWNSHEND, J.R.G. NDVI-derived land cover classiﬁcations at a global scale. Int. J. Remote Sens. 1994, 15, 3567–3586. [CrossRef] 13. Gitelson, A.A.; Kaufman, Y.J.; Stark, R.; Rundquist, D. Novel algorithms for remote estimation of vegetation fraction. Remote Sens. Environ. 2002, 80, 76–87. [CrossRef] 14. Hung, C.; Xu, Z.; Sukkarieh, S. Feature Learning Based Approach for Weed Classiﬁcation Using High Resolution Aerial Images from a Digital Camera Mounted on a UAV. Remote Sens. 2014, 6, 12037–12054. [CrossRef] 15. LeCun, Y.; Bengio, Y.; Hinton, G. Deep learning. Nature 2015, 521, 436–444. [CrossRef] [PubMed] 16. Shelhamer, E.; Long, J.; Darrell, T. Fully Convolutional Networks for Semantic Segmentation. IEEE Trans. Pattern Anal. Mach. Intell. 2014, 4, 640–651. [CrossRef] [PubMed] 17. Chen, L.C.; Papandreou, G.; Kokkinos, I.; Murphy, K.; Yuille, A.L. DeepLab: Semantic Image Segmentation with Deep Convolutional Nets, Atrous Convolution, and Fully Connected CRFs. IEEE Trans. Pattern Anal. Mach. Intell. 2018, 40, 834–848. [CrossRef] [PubMed] 18. Sherrah, J. Fully Convolutional Networks for Dense Semantic Labelling of High-Resolution Aerial Imagery. arXiv 2016, arXiv:1606.02585.

Sensors 2018, 18, 3299 12 of 12

19. Maggiori, E.; Tarabalka, Y.; Charpiat, G.; Alliez, P. High-Resolution Semantic Labeling with Convolutional Neural Networks. arXiv 2016, arXiv:1611.01962. 20. Maggiori, E.; Tarabalka, Y.; Charpiat, G.; Alliez, P. Fully Convolutional Neural Networks For Remote Sensing Image Classiﬁcation. In Proceedings of the 2016 IEEE International Geoscience and Remote Sensing Symposium (IGARSS), Beijing, China, 10–15 July 2016; pp. 5071–5074. 21. Huang, H.; Deng, J.; Lan, Y.; Yang, A.; Deng, X.; Zhang, L. A fully convolutional network for weed mapping of unmanned aerial vehicle (UAV) imagery. PLoS One 2018, 13, e196302. [CrossRef] [PubMed] 22. Huang, H.; Lan, Y.; Deng, J.; Yang, A.; Deng, X.; Zhang, L.; Wen, S. A Semantic Labeling Approach for Accurate Weed Mapping of High Resolution UAV Imagery. Sensors 2018, 18, 2113. [CrossRef] [PubMed] 23. Schwartz, A.M.; Paskewitz, S.M.; Orth, A.P.; Tesch, M.J.; Toong, Y.C.; Goodman, W.G. The lethal effects of Cyperus iria on Aedes aegypti. J. Am. Mosq. Control Assoc. 1998, 14, 78–82. [PubMed] 24. Yu, J.; Gao, H.; Pan, L.; Yao, Z.; Dong, L. Mechanism of resistance to cyhalofop-butyl in Chinese sprangletop ( Leptochloa chinensis (L.) Nees). Pestic. Biochem. Physiol. 2017, 143, 306–311. [CrossRef] [PubMed] 25. Dandois, J.P.; Ellis, E.C. High spatial resolution three-dimensional mapping of vegetation spectral dynamics using computer vision. Remote Sens. Environ. 2013, 136, 259–276. [CrossRef] 26. Zhang, W.; Huang, H.; Schmitz, M.; Sun, X.; Wang, H.; Mayer, H. Effective Fusion of Multi-Modal Remote Sensing Data in a Fully Convolutional Network for Semantic Labeling. Remote Sens. 2018, 10, 52. [CrossRef] 27. Simonyan, K.; Zisserman, A. Very Deep Convolutional Networks for Large-Scale Image Recognition. arXiv 2014, arXiv:1409.1556. 28. Everingham, M.; Van Gool, L.; Williams, C.; Winn, J.; Zisserman, A. PASCAL Visual Object Classes Recognition Challenge 2011 (VOC2011)–Training & Test Data. Available online: http://www.pascal-network. org/?q=node/598 (accessed on 5 November 2017). 29. Stathakis, D. How many hidden layers and nodes? Int. J. Remote Sens. 2009, 30, 2133–2147. [CrossRef] 30. He, K.; Zhang, X.; Ren, S.; Sun, J. Deep Residual Learning for Image Recognition. In Proceedings of the 2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR), Las Vegas, NV, USA, 27–30 June 2016; pp. 770–778. 31. Kr Henbühl, P.; Koltun, V. Efﬁcient Inference in Fully Connected CRFs with Gaussian Edge Potentials. arXiv 2012, arXiv:1210.5644. 32. Gonzalez-de-Santos, P.; Ribeiro, A.; Fernandez-Quintanilla, C.; Lopez-Granados, F.; Brandstoetter, M.; Tomic, S.; Pedrazzi, S.; Peruzzi, A.; Pajares, G.; Kaplanis, G.; et al. Fleets of robots for environmentally-safe pest control in agriculture. Precis. Agric. 2017, 18, 574–614. [CrossRef] 33. Gibson, K. Detection of Weed Species in Soybean Using Multispectral Digital Images. Weed Technol. 2004, 18, 742–749. [CrossRef]

© 2018 by the authors. Licensee MDPI, Basel, Switzerland. This article is an open access

article distributed under the terms and conditions of the Creative Commons Attribution (CC BY) license (http://creativecommons.org/licenses/by/4.0/).
