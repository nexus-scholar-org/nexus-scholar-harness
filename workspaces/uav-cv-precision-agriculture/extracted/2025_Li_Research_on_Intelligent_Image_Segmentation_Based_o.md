---
workspace_id: SCI-001335
doi: 10.1109/iccvit67848.2025.11391355
title: Research on Intelligent Image Segmentation Based on UAV Remote Sensing and
  DeepLabV3+ Model
authors:
- family_name: Li
  given_name: Youying
  orcid: null
- family_name: Wang
  given_name: Zhiyuan
  orcid: null
- family_name: Li
  given_name: Xinyu
  orcid: null
- family_name: Xue
  given_name: Jiali
  orcid: null
- family_name: Ma
  given_name: Lisha
  orcid: null
- family_name: Jiang
  given_name: Mingfang
  orcid: null
year: 2025
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:42.049816+00:00'
---

# Research on Intelligent Image Segmentation Based on UAV Remote Sensing and DeepLabV3+ Model

Research on Intelligent Image Segmentation Based on UAV Remote Sensing and

DeepLabV3+ Model

1st Youying Li  Hunan First Normal University  Changsha, Hunan Province,410205, P.R. China

2nd Zhiyuan Wang  Hunan First Normal University  Changsha, Hunan Province,410205, P.R. China

2114640747@qq.com

3162916530@qq.com   3rd Xinyu Li*  Hunan First Normal University  Changsha, Hunan Province,410205, P.R. China

2025 IEEE 3rd International Conference on Computer, Vision and Intelligent Technology (ICCVIT) | 979-8-3315-7700-1/25/$31.00 ©2025 IEEE | DOI: 10.1109/ICCVIT67848.2025.11391355

4th Jiali Xue  Hunan First Normal University  Changsha, Hunan Province,410205, P.R. China

1651190535@qq.com   5th Lisha Ma  Hunan First Normal University  Changsha, Hunan Province,410205, P.R. China

lxy365@163.com

6th Mingfang Jiang  Hunan First Normal University  Changsha, Hunan Province,410205, P.R. China

mls2460169412@163.com

3282518@qq.com

structure had been proposed as an example by Long [5],  laying the foundation of semantic segmentation research  based on convolutional networks.


## Abstract—Semantic segmentation of UAV remote sensing

crop images faces the dual challenges of high-accuracy 
models that are difficult to deploy in edge devices and the 
impaired accuracy of lightweight networks. In this paper, 
based on DeepLabV3+, VGG16, ResNet50, ResNet101, 
Xception, and MobileNetV2 are used as the backbones for 
comparative experiments, and compared and analyzed in 
terms of segmentation accuracy (pixel accuracy, IoU, Dice) 
and computational efficiency (memory occupation, inference 
speed). The results show that: Xception and MobileNetV2 
perform best in terms of performance and efficiency, while 
MobileNetV2 is more suitable for deployment in resource-
constrained scenarios such as unmanned aerial vehicles 
(UAVs), considering the accuracy, model scale, stability, and 
generalization ability, which provides a feasible solution for 
efficient semantic segmentation of crop remote sensing 
images.

This paper uses DeepLabV3+ with five different  backbone networks to compare segmentation performance  and select the best one.

II.  RESEARCH METHODS AND DATA HANDLING

A. Neural Network Research Methods

This paper conducts a controlled-variable comparison  of five backbones—VGG16, ResNet50, ResNet101,  Xception, and MobileNetV2—within the DeepLabV3+  segmentation framework. To ensure methodological  consistency under the principle of a single variable, a  uniform configuration was adopted: All experiments used  Adam (lr=0.001), cross-entropy loss, batch size 4, 50  epochs; dataset split 70%/30%.

Keywords-  DeepLabV3+, Deep Learning,  Semantic  Segmentation, Agriculture

B. Data acquisition and pre-processing

1) Data Acquisition and the Potential Impact of the  Characteristics of the Data.

I.  INTRODUCTION

Agricultural production is the basis for food security  and rural stability, and its statistical surveys are of great  significance to national development. However, traditional  manual surveys are inefficient and data quality is difficult  to guarantee. With the development of UAV remote  sensing and deep learning, crop distribution extraction  based on semantic segmentation has become an important  tool for intelligent agricultural decision-making [1].

Data are sourced from AliCloud Tianchi[6]: GB-scale  UAV images of farmland in Xingren, Guizhou, annotated  at the pixel level for five classes (barley, maize, tobacco,  Job’s tears, buildings). Since the data were derived from  the AliCloud platform, they lacked precise weather, light,  shadow distribution, and growth information, and these  uncertainties may lead to a decrease in the classification  accuracy of the model and errors in texture feature  extraction. This study did not compensate for this at  present. In the future, the robustness of the model in  complex environments and throughout the full fertility  cycle should be evaluated and improved by supplementing  the data with diverse meteorological (e.g., cloudy, rainy,  hazy) conditions, various time periods (early morning, and  nighttime), and cross-seasonal aerial photographs.

At present, the research on image semantic  segmentation technology based on deep neural networks  has made breakthrough progress, The DeepLabV3+ model  with its excellent performance and wide adaptability, has  been widely used in smart agriculture. Existing studies  include: Chen L-C et al. proposed DeepLabV3+ [2], fused  with Xception decoder to optimize multi-scale feature  interaction; Fu Bihuan et al. used ResNet et al. for semantic  segmentation of predicted images, and obtained mIoUs  higher than 90% [3]; and Mu Taoyang [4] et al. combined  with remote sensing of unmanned aerial vehicles to  achieve rice fall recognition (IoU 93%); The VGG network

2) Data Preprocessing.   Given the huge volume of the original large image and  the high processing cost, Original images and labels were  tiled into 1024×1024 patches; patches with only  background pixels were discarded.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:48:25 UTC from IEEE Xplore.  Restrictions apply.


> **Figure 1. Data after Preprocessing (not fully shown) and Sample Mask Image(foreground=#040404)**

C. Network Hyperparameters

A standard semantic segmentation framework typically  adopts an encoder-decoder architecture. The encoder  usually employs a pre-trained backbone network (e.g.,  VGG, ResNet) for feature extraction, followed by a  decoder network for classification, in this paper  DeepLabV3+.

1) Loss Function and Optimizer.   The Adam optimizer and cross-entropy loss function.  2) Class Weights and Image Pooling.   To mitigate the problem of class imbalance in the  dataset, different weights are set for the background and  foreground when computing the loss: class_weight =  torch.tensor([1.0, 2.0, 2.0, 2.0, 2.0, 2.0]). To reduce the  training overhead, the image is scaled down from  1024*1024 to 224*224. For the original image, bilinear  interpolation is used, whereas for the annotated image,  nearest neighbor interpolation is taken to keep the mask  colors constant.

B. DeepLabV3+ Model

DeepLabV3+ uses dilated (atrous) convolutions and an  Atrous Spatial Pyramid Pooling (ASPP) module to capture  multi-scale context. ASPP contains parallel branches of  dilated convolutions with different dilation rates and a  global pooling branch, whose outputs are concatenated.  The formula is shown as (1).

III.  NETWORK ARCHITECTURE

A. Overall Model Architecture

 =   + 	 ⋅

1


> **Figure 2. Schematic Diagram of the Atrous Convolution**

Atrous Spatial Pyramid Pooling (ASPP) is designed as  a multi-scale feature extraction module in DeepLabV3+.  ASPP consists of four parallel branches [2]: three Atrous  Convolutions with three expansions (r = 6, 12, 18) and a  global average pooling branch. The global pooling first

downscales the input by 1×1 convolution, then up-samples  the result to the original feature map size by bilinear  interpolation, and the final output concated with the output  of each Atrous Convolution.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:48:25 UTC from IEEE Xplore.  Restrictions apply.


> **Figure 3. ASPP-Arbeitsprinzip-Diagram**

The DeepLabV3+ architecture is shown in Figure 4. Its  decoder is connected in series with the encoder, while the

ASPP module is positioned at the end of the encoder.


> **Figure 4. DeepLabV3+ Model Framework and Execution Process**

C. Image Semantic Segmentation Model Architecture Diagram


> **Figure 5. Image Semantic Segmentation Network Architecture**

IV.  EXPERIMENT AND RESULTS ANALYSIS

the curves. To assess the stability of the model  performance, a regression was conducted on the smoothed  curves of performance over rounds, and then the residual  sum of squares (RSS) was calculated as an indicator of  stability.

A. Evaluation Metrics

This experiment evaluates models by both cost  (learning rate, GPU memory usage, and inference time)  and performance (loss, accuracy, IoU, Dice) metrics. To  evaluate models’ generalization ability, the Normative  Generalization Gap (NGG) is defined as:

B. Experimental results and analysis

1) Dynamic Accuracy Visualization and Analysis.   The first metric that needs to be evaluated is the  correctness rate, and for this purpose, curves of accuracy  and Dice coefficients on the training set across epochs  were plotted for the models (we analyze the metrics on the  training set firstly because it is much more stable and hence

 =   ! "

   2

Due to the relatively large variance of much of the data,  sliding window means were used frequently to smooth out

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:48:25 UTC from IEEE Xplore.  Restrictions apply.

is suitable for initial judgments).


## architecture; the other models (except Xception and

MobileNetV2) leveled off around epoch 40. Xception 
continued to increase (near 95% accuracy at the end), 
suggesting potential overfitting; MobileNetV2 also 
increased steadily but more slowly. To evaluate each 
model’s actual performance more objectively, the 
following section presents a comparative analysis of 
dynamic accuracy on the validation dataset across training 
epochs.


> **Figure 7. Curves of Accuracy across Epochs**

Initial analysis shows that Xception and MobileNetV2  are close in val acc at the end of the training, confirming  that Xception may have significant overfitting compared  to the latter. In order to visualize the degree of overfitting  of the different models the following graphs were painted:


> **Figure 6. Curves of Train Accuracy and Train Dice across Epochs**

Training accuracy and Dice curves (Fig. 6) showed  VGG plateauing early due to its overly simplistic


> **Figure 8. Accuracy Curves on Training and Validation Datasets**

As shown in Figure 9, the ResNet variants exhibit  markedly poorer generalization, whereas MobileNetV2  and  Xception  deliver  similarly  high  and  stable  generalization ability. This contrast stems from ResNet’s  excessive  parameter  count,  which  encourages  memorization of irrelevant details; by contrast, the more  compact MobileNetV2 and Xception better matched the  complexity of this task, confirming that model capacity  should align with the problem difficulty. Furthermore, in  the final ten epochs, Xception exhibits a slightly higher  level of overfitting than MobileNetV2, which aligns with  our previous hypothesis. Notably, despite Xception  owning roughly five times as many parameters as  MobileNetV2, the degradation in its generalization

During the early training phase, MobileNetV2 and  Xception both had markedly higher validation accuracy  than training, likely because Dropout and BatchNorm were  active  during  training—suppressing  performance— whereas during validation Dropout was disabled and  BatchNorm utilized global statistics, allowing the models  to perform at full capacity. In the late training phase (epoch  ≥ 30), the difference (val acc − train acc) becomes negative  and declines monotonically, indicating the onset of  overfitting. In contrast, the ResNet variants exhibit large  swings in validation performance and poor stability. To  quantify each model’s generalization, let’s measure the  NGG, whose larger values signify a weaker ability of  generalization and more severe overfitting

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:48:25 UTC from IEEE Xplore.  Restrictions apply.

impose stronger regularization[7].

performance is disproportionate, which can be explained  by its Depthwise Separable Convolutions' parameter  sharing, and frequent usage of BatchNorm layers that


> **Figure 9. Curves of NGG across Epochs and Curves of the Sliding Window Means of NGG**

2) Visual Analyses of Performance Stability.   Next, the learning curves (smoothed val acc versus  epoch) of different models are going to be compared. The  sliding window mean curve of val acc:

During early training, Xception, MobileNetV2, and  VGG all show rapid gains; thereafter, Xception and  MobileNetV2 slow and stabilize, while VGG prematurely  stalls into a local optimum. By contrast, the ResNet  family’s  curves  are  almost  linear—ResNet50  approximates a straight line, and ResNet101 hovers around  70% (with large fluctuations, though). This suggests that  increasing parameter count leads to slower learning speed  and reduced stability. We quantified model stability by  fitting these curves (logarithmic fits for Xception,  MobileNetV2, VGG; linear fits for ResNet50/101) and  analyzing residuals to give information about the  rationality of our choice of models.


> **Figure 11. Sliding-Window Mean of |Residuals| (window_size=15)**


> **Figure 10. Curves of Sliding Window Mean of Val Acc when**

window_size=5, 15


> **Table 1. Comparison of Model Fit Statistics and Parameter Count**

VGG  MobilenetV2  Xception  ResNet50  ResNet101

RSS  0.001153[1]  0.004749[2]↑  0.011367[3]  0.015597[4]  0.034442[5]↓

Correlation Coefficients  0.9786  0.9732  0.9507  0.8697  0.0750

Quantity of Parameters  140M  4.25M  22.91M  25.64M  44.71M

Due to VGG16’s extremely poor performance, it is  excluded from the primary comparison. The abnormal  correlation coefficient of ResNet101 can be considered a  consequence of its extreme instability because that of  ResNet50 also slightly underperforms the lightweight  models. Excluding VGG16, model stability generally  increases with the parameter count. VGG16's anomalous  behavior likely stems from its highly symmetrical, non- residual architecture (which hinders gradient flow in deep

layers)  and  overly  aggressive  regularization  of  dropout=0.5. Overall, model stability ranks as follows:  MobileNetV2 > Xception > ResNet50 > ResNet101.  Larger models tend to overfit due to parameter redundancy,  leading  to  pronounced  fluctuations  in  validation  performance. The easiest way to mitigate this problem is  through data augmentation.

3) Quantitative Analysis of Overall Correctness.   In the final-epoch evaluation, the ideal approach is to

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:48:25 UTC from IEEE Xplore.  Restrictions apply.

these statistics using the data from the last ten epochs. For  clarity, standard deviations ≤ 0.002 are highlighted in  green, ≥ 0.003 in red, and values in between in light red.

compute the mean and standard deviation of each metric  from multiple independent runs; however, due to limited  computing resources and time, this study instead estimates


> **Table 2. Comparison of Training and Validation Performance and Standard Deviation of Each Model**

Val Dice  Std  Dev  MobileNetV2  0.8851[2]  0.0053  0.7274[2]  0.012 6  0.7732[2 ]

Model  Train Acc  Std  Dev

Train IoU  Std  Dev

Train

Std  Dev

Val Acc  Std  Dev

Val IoU  Std  Dev

Dice

0.024 6  ResNet50  0.8562[3]  0.0096  0.6964[3]  0.008 8  0.7443[3 ]

0.012 4  0.8562[2]  0.0118  0.7019[1] ↑

0.027 4  0.7499[1] ↑

0.008 0  0.8085[3]  0.047 1  0.6405[3]  0.049 9  0.6933[3]  0.048 7  ResNet101  0.8426[4] ↓

0.096 4  VGG  0.6352[5]  0.0104  0.4974[5]  0.007 6  0.5224[5 ]

0.0083  0.6777[4] ↓

0.010 4  0.7272[4 ]

0.009 5  0.6958[4] ↓

0.124 3  0.5734[4] ↓

0.097 7  0.6302[4] ↓

0.007 8  0.6733[5]  0.000 0  0.5275[5]  0.000 0  0.5502[5]  0.000 0  Xception  0.9133[1] ↑

0.0150  0.7550[1] ↑

0.012 9  0.7965[1 ]

0.0115  0.8695[1] ↑

0.009 7  0.6998[2]  0.027 6  0.7475[2]  0.026 0

Although validation metrics are more practically  relevant, their reliability was limited by large standard  deviations. On the validation set, Xception achieved  slightly higher accuracy than MobileNetV2 but slightly  lower IoU and Dice; Since the difference in means of  performance between the two models is smaller than their  standard deviations, the comparative performance can be  considered statistically indistinguishable based on the  current data. Considering that MobileNetV2 exhibits  milder overfitting and lower variance in later epochs, it  holds a marginal overall advantage; however, their relative  ranking in generalization ability briefly changed twice

during training, indicating that conclusions based solely on  the final few epochs may lack robustness.

ResNet variants consistently lag behind Xception and  MobileNetV2 – both architected with segmentation- specific components like multi-scale feature fusion layers  – in performance metrics across training and validation  datasets, with ResNet101 persistently underperforming  ResNet50. Larger models exhibit steeper learning curves  and have a poorer ability of generalization in addition,  resulting in inferior performance on relatively simple crop- segmentation tasks compared to lightweight architectures.

4) Quantitative Analysis of the Costs of Different Models.


> **Table 3. Comparison Table of Model Resource Consumption and Computational Efficiency**

MobileNetV2  ResNet50  ResNet101  VGG  Xception

Memory Usage(MB)  88.4700[1]↓  622.4500[4]  920.5700[5]↓  304.7798[2]  583.7100[3]

Std Dev  0.0000  0.0000  0.0000  0.0014  0.0000

Inference Time(s)  0.0204[4]  0.0167[3]  0.0256[5]↓  0.0040[1]  0.0133[2]↑

Std Dev  0.0048  0.0046  0.0023  0.0011  0.0033

Training Rate  215.8770[4]  263.1002[3]  160.2190[5]↓  1069.3790[1]  325.3308[2]↑

Std Dev  52.1427  56.5837  8.4797  196.9096  52.2157

Quantity of participants  4.25M[1]  25.64M[3]  44.71M[4]  140M[5]  22.91M[2]

For resource usage, VGG16 delivered the fastest  training/inference  speed  but  insufficient  accuracy;  MobileNetV2 had the smallest memory footprint and  robust performance, suitable for deployment; ResNet101  used nearly twice the resources of ResNet50 for little gain.  MobileNetV2 also controlled overfitting best, while  Xception trained and inferred faster; MobileNetV2’s  depthwise convolutions incur high memory-access  overhead,  reducing  its  computational  efficiency.  Consequently, shallower architectures may be preferable  for tasks involving relatively simple datasets or strict  resource/real-time constraints.

overall computational efficiency on GPU platforms.

C. Conclusions

VGG16 is almost unsuitable for these tasks; the ResNet  networks had low accuracy and heavy overfitting;  MobileNetV2 and Xception were comparable in accuracy,  stability, and generalization, with MobileNetV2 having the  smallest memory footprint (though about 1.4× the parallel  training/inference overhead of Xception). Considering  UAV resource constraints, MobileNetV2 is slightly  preferred.

V.  SUMMARY AND OUTLOOK

Moreover, while MobileNetV2 demonstrated superior  overfitting control and stability, Xception provided faster  training and inference. This difference seemed primarily  from MobileNetV2’s depthwise separable convolutions,  which incurred high memory-access overhead due to  frequent intermediate feature-map read/write operations  and underutilization of parallelism[8], thereby reducing its

In this study, based on the DeepLabV3+ framework,  we compared five backbone networks for UAV crop image  segmentation. MobileNetV2 had an extremely low  memory  footprint  and  stable  training/validation  performance,  with  accuracy  (~86.95%±0.97%)  comparable  to  Xception,  significantly  reducing

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:48:25 UTC from IEEE Xplore.  Restrictions apply.

computational cost and thus being better suited for mobile  deployment.


## REFERENCES

However, this study several has limitations: it did not  use data augmentation, causing considerable performance  fluctuations for some models on the validation set; and the  number of experimental repeats was insufficient (fewer  than five), undermining the statistical reliability of our  conclusions.

[1]

Cao Y et al 2024 Crop Disease Monitoring Using UAV Remote  Sensing J. Shenyang Agric. Univ.   Chen L C et al 2018 Encoder-Decoder with Atrous Separable  Convolution for Semantic Image Segmentation Proc. ECCV  arXiv:1802.02611.  Fu B H and Huang L 2022 Extraction of Tobacco Cultivation Area  from UAV Images Based on Deep Semantic Segmentation J.  Kunming Univ. Sci. Technol. (Nat. Sci. Ed.) 47(2) 7-15   Mu T Y, Zhao W, Hu X Y et al 2022 Rice Lodging Identification  via Improved DeepLabV3+ and UAV Remote Sensing J. Northeast  For. Univ.   Long J, et al. Fully Convolutional Networks for Semantic  Segmentation [C].DOI: 10.1109/CVPR.2015.7298965.  Tianchi, "Barley Remote Sensing Dataset" [Online Dataset]. 2020.  Available:  https://tianchi.aliyun.com/dataset/dataDetail?dataId=74952  Lange S, Helfrich K, Ye Q 2022 Batch Normalization  Preconditioning for Neural Network Training. J. Mach. Learn. Res.  23:1–43.  Sandler M et al. 2018 MobileNetV2: Inverted Residuals and Linear  Bottlenecks. Proc. CVPR 4510–4520  Székely G J, Rizzo ML, Bakirov N K 2007 Measuring and Testing  Dependence by Correlation of Distances. Ann. Stat.  [10] Reshef D N et al. 2011 Detecting Novel Associations in Large Data

[2]

[3]

Future work: (1) use statistical and information- theoretic metrics (e.g., distance correlation [9], and maximal  information coefficient [10]) to characterize dependencies  among performance metrics; (2) apply LOESS [11],  generalized additive models (GAM) [12], and elastic net  regression [13] to quantify nonlinear relationships between  network depth and model performance or cost (based on  ResNet variants). This framework aims to establish  empirically validated principles for backbone selection  focused on accuracy-efficiency trade-offs.

[4]

[5]

[6]

[7]

ACKNOWLEDGMENTS

[8]

This paper is funded by the General Project of the  Hunan  Provincial  Natural  Science  Foundation  (2024JJ5103), the Key Scientific Research Project of the  Hunan Provincial Department of Education (23A0650),  and the Teaching Reform Research Project of Ordinary  Colleges and Universities in Hunan Province (HNJG- 20231338)

[9]

Sets. Science 334(6062)  [11] Cleveland W S 1979 Robust Locally Weighted Regression and

Smoothing Scatterplots. J. Am. Stat. Assoc.   [12] Hastie T, Tibshirani R 1990 Generalized Additive Models  [13] Zou H, Hastie T 2005 Regularization and Variable Selection via the

Elastic Net. J. R. Stat. Soc.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:48:25 UTC from IEEE Xplore.  Restrictions apply.
