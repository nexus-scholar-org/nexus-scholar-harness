---
workspace_id: SCI-000898
doi: 10.1186/s13007-025-01373-w
title: 'DM_CorrMatch: a semi-supervised semantic segmentation framework for rapeseed
  flower coverage estimation using UAV imagery.'
authors:
- family_name: Li
  given_name: Jie
  orcid: null
- family_name: Zhu
  given_name: Chengyong
  orcid: null
- family_name: Yang
  given_name: Chenbo
  orcid: null
- family_name: Zheng
  given_name: Quan
  orcid: null
- family_name: Wang
  given_name: Binhui
  orcid: null
- family_name: Tu
  given_name: Jingmin
  orcid: null
- family_name: Zhang
  given_name: Qian
  orcid: null
- family_name: Liu
  given_name: Sheng
  orcid: null
- family_name: Wang
  given_name: Xinfa
  orcid: null
- family_name: Qiao
  given_name: Jiangwei
  orcid: null
year: 2025
extraction_engine: pymupdf
extracted_at: '2026-09-04T01:48:54.106580+00:00'
---

# DM_CorrMatch: a semi-supervised semantic segmentation framework for rapeseed flower coverage estimation using UAV imagery.

Plant Methods

Li et al. Plant Methods           (2025) 21:54   https://doi.org/10.1186/s13007-025-01373-w

RESEARCH Open Access

DM_CorrMatch: a semi‑supervised semantic  segmentation framework for rapeseed flower  coverage estimation using UAV imagery

Jie Li1*, Chengyong Zhu1, Chenbo Yang1, Quan Zheng1, Binhui Wang1, Jingmin Tu1, Qian Zhang2, Sheng Liu2,  Xinfa Wang2 and Jiangwei Qiao2*


## Abstract

Rapeseed (Brassica napus L.) inflorescence coverage is a crucial phenotypic parameter for assessing crop growth 
and estimating yield. Accurate crop cover assessment is typically performed using Unmanned Aerial Vehicles (UAVs) 
in combination with semantic segmentation methods. However, the irregular and variable morphology of rapeseed 
inflorescences presents significant challenges in segmentation. To address these challenges, advanced methods 
that can improve segmentation accuracy, particularly under limited data conditions, are needed. In this study, we 
propose a cost-effective and high-throughput approach using a semi-supervised learning framework, DM_CorrMatch. 
This method enhances input images through strong and weak data augmentation techniques, while leveraging 
the Denoising Diffusion Probabilistic Model (DDPM) to generate additional samples in data-scarce scenarios. We 
propose an automatic update strategy for labeled data to dilute the proportion of erroneous labels in manual 
segmentation. Furthermore, a novel network architecture, Mamba-Deeplabv3+, is proposed, combining the strengths 
of Mamba and Convolutional Neural Networks (CNNs) for both global and local feature extraction. This architecture 
effectively captures key inflorescence features, even under varying poses, while reducing the influence of complex 
backgrounds. The proposed method is validated on the Rapeseed Flower Segmentation Dataset (RFSD), which 
consists of 720 UAV images from the Yangluo experimental station of the Oil Crops Research Institute of the Chinese 
Academy of Agricultural Sciences (CAAS). The experimental results showed that our method outperforms four 
traditional segmentation methods and eleven deep learning methods, achieving an Intersection over Union (IoU) 
of 0.886, Precision of 0.942, and Recall of 0.940. The proposed semi-supervised learning-based method, combined 
with the Mamba-Deeplabv3+ architecture, demonstrates superior performance in accurately segmenting rapeseed 
inflorescences under challenging conditions. Our approach effectively handles complex backgrounds and various 
poses of inflorescences, providing a reliable tool for rapeseed flower cover estimation. This method can aid 
in the development of high-yield cultivars and improve crop monitoring through UAV-based technologies.
Keywords  Semi-supervised semantic segmentation, Rapeseed, Diffusion model, Vision mamba

*Correspondence: Jie Li jielonline@hbut.edu.cn Jiangwei Qiao qiaojiangwei@caas.cn

© The Author(s) 2025. Open Access  This article is licensed under a Creative Commons Attribution-NonCommercial-NoDerivatives 4.0  International License, which permits any non-commercial use, sharing, distribution and reproduction in any medium or format, as long  as you give appropriate credit to the original author(s) and the source, provide a link to the Creative Commons licence, and indicate if  you modified the licensed material. You do not have permission under this licence to share adapted material derived from this article or  parts of it. The images or other third party material in this article are included in the article’s Creative Commons licence, unless indicated  otherwise in a credit line to the material. If material is not included in the article’s Creative Commons licence and your intended use is not  permitted by statutory regulation or exceeds the permitted use, you will need to obtain permission directly from the copyright holder. To  view a copy of this licence, visit http://​creat​iveco​mmons.​org/​licen​ses/​by-​nc-​nd/4.​0/.

Page 2 of 20 Li et al. Plant Methods           (2025) 21:54


## Introduction

In 2023, China’s consumption of edible vegetable oil 
reached 39.08 million tons, of which domestically 
produced vegetable oil accounting for approximately 
10.515 million tons [1], with a self-sufficiency rate of 
only about 30%. This indicates a severe supply–demand 
gap. Rapeseed(Brassica napus L.), as the primary source 
of domestic vegetable oil, holds a significant strategic 
role in the national edible oil supply security. Given the 
limited land resources, increasing the yield per unit area 
is the only way to enhance oilseed production capacity. 
The cultivation of high-yielding rapeseed varieties has 
become an urgent issue for ensuring the security of 
domestic vegetable oil supply.

normalized difference yellow vegetation index (NDYVI)  is proposed to monitor yellowing morphologies such  as flowers, based on GF- 6 images [15]. This approach  leverages the spectral reflectance features of crops  exhibiting yellowing. The aforementioned methods,  leveraging spectral information of canopys, has achieved  promising results in the estimation of crop canopy  coverage.  However,  modern  large-scale  breeding  programs typically encompass thousands of small plots,  distributed across various breeding environments.  The canopy phenotype needs to be distinguished at  a fine granularity. Spatial resolution is a challenge for  multispectral and satellite imaging, especially quantity  acquisition of flowers in small breeding plot.

In recent years, remote sensing technology with RGB  sensor has seen widespread application in agriculture,  enabling the collection of crop information across  different spatial and temporal scale [16–19]. Zhang  et  al. [20] proposed two lightweight neural network  architectures, LW-Segnet and LW-Unet, for high- precision rice seedling segmentation. Li et  al.[21]  proposed a hybrid attention and transfer learning  optimized semantic segmentation model for accurate  disease severity estimation in field conditions using leaf  images. Zhang et  al. [22] introduced a Transformer- based GANet-Mask algorithm to get the grassland  fractional vegetation cover. Chen et  al. [23] found  that  deep  learning-based  semantic  segmentation  not  only  streamlines  feature  extraction  through  trainable operators but also improves segmentation  accuracy for complex high-resolution UAV imagery.  Scholars transform the phenotypic analysis problem  into a semantic segmentation task, which has been  demonstrated to be highly effective.

Crop phenotype refers to the physical, physiological,  and biochemical traits observed during the crop growth.  It provides essential technical support for breeding and  precision management in crop production [2–4]. The  flowering period of oilseed rapeseed can last up to 30  days, which comprises nearly one-quarter of the plant’s  total growing period. This stage marks the critical  transition from vegetative to reproductive growth [5].  Flowering time and duration are key agronomic traits  closely linked to yield [6, 7]. The coverage of oilseed  rapeseed flower clusters accurately reflects the growth  conditions of various rapeseed varieties during different  stages of the flowering period [8], which is a widely  used phenotypic parameter to assess flower growth.  Additionally, studies have shown that peak flowering  in canola occurs when flower coverage reaches its  maximum, demonstrating a strong correlation between  flower coverage, and canola yield [9, 10]. Nevertheless,  traditional field observations of canola flowering are  time-consuming,  labor-intensive,  and  subjective.  Automatic,  non-destructive  and  high-throughput  methods to determine and analyze the flowering stage  of rapeseed are crucial for improving rapeseed yield and  breeding efficiency.

However, deep learning methods generally require  large-scale, pixel-wise labeled datasets [24], which  consist of numerous annotated images. Compared to  image classification and object detection tasks [25, 26],  accurately labeling datasets for semantic segmentation  is more expensive and time-consuming. To solve  this problem, Gao et  al. [27] created a simulated-to- realistic dataset, and found that a training set of 9600  images combined with only 60 real images achieved  the same segmentation accuracy as 2400 real images.  The utilization of synthetic images has demonstrated  potential as a promising strategy for augmenting the  training  dataset.  But  this  cross-spatial-resolution  model was specifically designed for field rice semantic  segmentation.

Studies have been paying close attention to the  application of remote sensing technology in high- throughput flowering phenotypic analysis. For example,  Fang et  al.[11] developed an approach for remote  estimation of vegetation fraction and flower fraction by  a multispectral system mounted on unmanned aerial  vehicle (UAV). Wan et  al. [12] combined vegetation  indices (VIs) extracted from RGB and multispectral  images to estimating flower number in oilseed rapeseed.  After that, an enhanced area yellowness index (EAYI)  is developed based on Moderate Resolution Imaging  Spectroradiometer (MODIS) time series data for  mapping rapeseed flowers [13]. Zhang et  al. [14]  investigated the application of vegetation indices in  estimating canola flower numbers. Even more, a new

Semi-supervised learning can leverage a limited  amount of annotated data alongside a vast pool of  unannotated data to train accurate segmentation  algorithms. This approach not only alleviates the burden

Page 3 of 20 Li et al. Plant Methods           (2025) 21:54

flower coverage estimation that differs from traditional  approaches. Our method requires diverse training data,  leverages a network with enhanced feature extraction  capabilities, and introduces an innovative pseudo- labeling strategy to improve segmentation accuracy.

of manual annotation but also capitalizes on the abundant  unlabeled data to enhance the precision of segmentation.  Semi-supervised learning approaches can be categorized  into self-training strategies that generate pseudo-labels  and consistency-based learning strategies predicated on  the smoothness assumption. The self-training strategy  initially employs labeled data to train a network, which  then produces a series of pseudo-labels[28, 29]. These  pseudo-labels are subsequently merged with the original  dataset, and the model is retrained until convergence.  However, the success of self-training strategies is highly  contingent upon the performance of the initial classifier,  and they often necessitate multiple iterations of training,  which can be particularly costly for large-volume images.

Our main contributions can be summarized as follows:

(1)	 To alleviate the burden of manual annotation, we

propose a semi-supervised semantic segmentation  framework named DM_CorrMatch, which is  designed with an innovative labeling update and an  alternative method for generating samples based  on the Denoising Diffusion Probabilistic (DDPM)  model. (2)	 To enhance the network’s sensitivity to salient

Nowadays, consistency regularization is widely applied  in semi-supervised semantic segmentation tasks [30, 31].  The mean teacher method, which is based on consistency  learning, is a more prevalent semi-supervised learning  strategy. It introduces different perturbations to both  labeled and unlabeled data, enforcing consistency  constraints on the model’s outputs after perturbation  to assist in optimizing the network and enhancing its  robustness and generalizability [32, 33]. Nevertheless,  within consistency-based semi-supervised methods,  there exists an unreliable prediction region in the  student network’s output for unlabeled data, which can  lead to erroneous consistency guidance. Implementing  meaningful consistency constraints between teacher  and student networks has remained a challenging issue.  Recent methods, such as FixMatch [34] and Unimatch  [35], combine these two approaches. They apply strong  perturbations to unlabeled images while leveraging  pseudo-supervision  from  predictions  on  weakly  perturbed images, using a high confidence threshold to  filter pseudo-labels for training.

visual information, we combine the strengths of  Convolutional Neural Networks (CNNs) and Visual  Mamba, integrating low-level detail information  and high-level semantic information through a  cascaded feature fusion approach. (3)	 To validate the effectiveness of the proposed

method,  we  establish  a  Rapeseed  Flower  Segmentation  Dataset  (RFSD)  consisting  of  720  high-definition  UAV  images  and  their  corresponding labels, spanning multiple stages of  the flowering stage. (4)	 We explore the application of coverage in oilseed

rapeseed breeding and discussed the relationship  between the accuracy of the proposed model and  the flight altitude of the UAV.

Materials and methods Overall process The overall process presented in this paper includes  data collection, data processing, dataset creation, model  training, model prediction, and model application. As  shown in Fig. 1, a UAV equipped with an RGB camera is  used to capture image data of the entire field. Along with  this, Agisoft PhotoScan is employed for image stitching.  Individual plot images are then cropped using Adobe  Photoshop to a fixed size of 256×256 pixels before being  labeled using the Labelme software. This process results  in the creation of the Rapeseed Flower Segmentation  Dataset (RFSD), which includes both original canola  images and corresponding semantic labels.

The rapeseed flower clusters exhibit distinct yellow  characteristics, thus allowing the coverage of flower  clusters to be transformed into an image segmentation  task. But rapeseed is a high-density planting crop. The  segmentation of rapeseed inflorescences presents notable  challenges within the context of natural environments,  as captured by Unmanned Aerial Vehicle-Red Green  Blue (UAV-RGB) imagery. The challenges are as  follows: The irregular and complex morphology of  rapeseed inflorescences, further complicated by blurred  boundaries, poses significant difficulties for accurate  manual labeling and prediction. Additionally, the  substantial variation in the condition, size, and color of  rapeseed inflorescences across different growth stages  complicates feature extraction for diverse periods and  morphologies.

To enhance model performance, the labeled dataset was  augmented using DDPM-based generative augmentation  alongside various traditional augmentation techniques.  The proposed DM_CorrMatch model was then trained  on this enhanced dataset and subsequently applied  to calculate rapeseed flower coverage, capturing the  coverage variation of different rapeseed varieties across

To address these challenges, we propose a novel  semi-supervised segmentation method for rapeseed

Page 4 of 20 Li et al. Plant Methods           (2025) 21:54

Fig. 1  General flowchart of the experiment

various flowering stages. In addition, we performed  flower bud counting based on the segmentation results to  further analyze flowering trends.

Data acquisition The data used in this experiment was collected from the  Yangluo experimental station of the Oil Crops Research  Institute of the Chinese Academy of Agricultural  Sciences (CAAS), located in Xinzhou District, Wuhan  City, Hubei Province (30°42′ E, 14°30′ N) at an altitude of  approximately 24 ms. As shown in Fig. 2a, b, the site has

Furthermore, we assessed the robustness of the  proposed model by evaluating its performance under  different GSD conditions, demonstrating its stability and  effectiveness in varying UAV flight altitudes.

Fig. 2  The collection site and segmentation target. a Data collection site. b Experimental field. c Different rapeseed flower corresponding to early  flowering, full flowering, and late flowering stages at different periods

Page 5 of 20 Li et al. Plant Methods           (2025) 21:54

deep learning segmentation network. We cropped the  orthophoto image into individual plots based on the  actual ground dimensions using the Agisoft PhotoScan  software. Then, the plot images were labeled using the  Labelme tool, and the corresponding JSON files were  converted into mask images for semantic segmentation.  For enhanced training efficiency, we croped the  labeled plot images to 256×256 pixels. As a result of  this processing, we obtained the Rapeseed Flower  Segmentation Dataset (RFSD), containing 720 images  and their corresponding labels.

a subtropical monsoon climate, and oilseed rapeseed was  planted in field plots, with plot sizes of 8 ­m2 (2 m × 4 m)  and 6 ­m2 (2 m × 3 m), both of which were used in this  study. Winter oilseed rapeseed, planted in late September  and harvested the following May, was selected as the  experimental crop. Data collection occurred between  February and May in both 2021 (for model training) and  2022 (for model robustness testing). The data collection environment is illustrated in Fig. 3.  Considering that variations in lighting and visual features  under different temperature conditions can significantly  influence the model’s capability to accurately segment  rapeseed inflorescences, we recorded the dates of data  acquisition and corresponding temperature conditions.  This information will facilitate a more refined data  filtering process in subsequent analysis.

DM_CorrMatch network flow Plants represent a self-regulating system, and when  observed via an unmanned aerial vehicle (UAV), the  canopy inflorescences exhibit a spectrum of colors and  morphologies, complicated by substantial occlusion  and interference, which poses a formidable challenge  for precise segmentation. Supervised deep learning  segmentation techniques have demonstrated potential  to solve the tough task. However, the requirement for  extensive pixel-level annotations incurs considerable  labeling expenses. The inflorescence possesses unique  color attributes, and integrating these with the intrinsic  characteristics of the crop alongside strengths of data- driven methodologies represents an emerging research  direction.

The UAV used for data acquisition was the DJI  Phantom 4 Pro V2.0, equipped with a 20.1 MP camera,  capturing images at a resolution of 5472×3648 pixels.  An automatic flight mode was employed for aerial  photography, with the heading and side overlap rates set  at 75%. The UAV flew at an altitude of 10 m, capturing  images at equidistant intervals at a speed of 1.9 m/s,  completing data acquisition for the study area within  approximately 30 min. After that, orthophoto images of  the field was stitched by Photoscan software.

Figure  3 illustrates the growth stages of rapeseed  within the same plot across different time periods,  arranged sequentially from left to right and top to  bottom. From the 2c, we can see that the size and color  of rapeseed flower buds vary significantly across different  growth stages. In addition to this, the background of  the inflorescence also changes considerably, with green  leaves gradually falling off, and in the later stages, distinct  pods can also be observed, which increases the difficulty  of precise segmentation.

The CorrMatch [36] achieves good results even with  a small amount of labeled data. It is a semi-supervised  learning method that leverages unlabeled data through  consistency regularization and dual-label propagation  strategies,  achieving  state-of-the-art  segmentation  performance on the Pascal VOC 2012 and Cityscapes  datasets. However, for crop segmentation, the precision  of manual annotations is suboptimal. The model  demands enhanced feature extraction capabilities to  accurately delineate fine details, including blurred edges,  obscured targets, and small targets set against complex  backgrounds. Furthermore, it need optimization and  updating strategies for training data.

Dataset construction To experiment on the proposed method, Rapeseed  Flower Segmentation Dataset (RFSD) was built for the

To address these challenges, DM_CorrMatch is  introduced. The proposed method captures long-range  dependencies, enhancing segmentation performance  for small objects and fine details. Additionally, a data  optimization strategy involving pseudo-labels and true  labels has been developed. As illustrated in Fig. 4a, the  upper-left section depicts the data augmentation process,  where weak and strong data augmentation techniques  are applied to enhance the input data. Besides this, the  DDPM model generates a large amount of unlabeled  data, providing diverse data for the experiments. The  middle section of the figure presents the proposed  Mamba-DeeplabV3+  network,  which  incorporates

Fig. 3  Rapeseed images collected by drones along with the  corresponding environments and dates

Page 6 of 20 Li et al. Plant Methods           (2025) 21:54

Fig. 4  DM_CorrMatch framework Workflow. a Overall workflow of the DM_CorrMatch framework. b Generative mechanism of the Diffusion Model  (DDPM). c Detailed workflow of the Mamba-DeepLabV3+ network

jittering, grayscale conversion, and CutMix. All  augmentation operations were applied randomly to  ensure diverse variations in the training dataset.

Vision Mamba blocks between the first and second layers  of the ResNet101 feature extraction network, enhancing  the ability to extract detail features. Below the Mamba- DeeplabV3+ network, the proposed automatic update  strategy of labeled data is outlined. After completing  custom training rounds, this strategy integrates the  images with confidence scores exceeding the threshold  τ from each round into the original labeled dataset for

In scenarios where unlabeled data is insufficient,  this study proposed leveraging diffusion models  to compensate for the shortage. This generative  enhancement strategy integrates additional unlabeled  data into the training process, which has been shown  to significantly benefit semi-supervised learning [37].  Traditional Generative Adversarial Networks (GANs)  are widely used for generating unlabeled images  through adversarial training between a generator and  a discriminator. While GANs can produce visually  appealing results, they often face challenges such as  training instability and mode collapse, which constrain  the diversity and quality of the generated data.

supervised loss computation, thereby optimizing the  labeled dataset.

Data augmentation In our experiments, we applied both weak and strong  data augmentation techniques to enhance the input  data.  Weak  augmentations  included  operations  such as scaling, cropping, and flipping, while strong  augmentations involved transformations like color

Page 7 of 20 Li et al. Plant Methods           (2025) 21:54

to capture fine-grained details and complex spatial  dependencies.

To address these limitations, we adopted the Denoising  Diffusion Probabilistic Model (DDPM) as our generative  approach. Unlike GANs, DDPM leverages probabilistic  modeling to progressively add and remove noise,  enabling it to generate high-quality images through a  robust backward diffusion process. This choice ensures  a more stable and reliable generation of diverse samples,  effectively complementing our augmentation strategies.

Fig. 4c illustrates the integration of the Vision Mamba  layer into the shallow residual block of ResNet101,  strategically positioned between layer1 and layer2.  Introducing the Vision Mamba layer at this early stage  offers two primary advantages. First, placing it within  the shallow residual block allows the model to enrich  foundational features early on, which is crucial for tasks  requiring precise segmentation of intricate structures,  such as the detailed contours of canola flower petals. In  contrast, ViTs typically emphasize deeper layers, which  may result in the loss of fine-grained spatial information.  Second, this early-stage enhancement ensures that  deeper layers receive a richer feature set, improving  the balance between local texture details and global  contextual information.

As illustrated in Fig.  4b, DDPM is a generative  model that achieves image generation through two key  processes: forward diffusion and reverse denoising. The  forward diffusion process transforms real images into  pure random noise by gradually adding Gaussian noise  over multiple time steps. At each step, a small amount  of noise is added, ultimately resulting in completely  random noise. Subsequently, the reverse denoising  process reconstructs the original image by progressively  removing noise, starting from random noise. This  iterative process generates samples that become  increasingly closer to real data with each step, based on  the output of the previous step.

The input image, represented as W ×H× C (where  W, H, and C denote the width, height, and channels,  respectively), undergoes a series of convolutional  operations, gradually reducing spatial resolution while  increasing the depth of the feature maps. By the time  the data reaches the Vision Mamba layer, it has been  transformed into a 64×64×256 feature map. The Vision  Mamba layer consists of bidirectional State Space  Models (SSMs): a forward SSM and a backward SSM.  Each SSM processes a 64×64×256 feature map, analyzing  the sequential dependencies in the data to enhance  contextual information. The bidirectional nature of this  layer enables it to capture the relationships between  local and global features in the image, akin to how  temporal dynamics are handled in time-series data. After  processing, the outputs from the forward and backward  SSMs are concatenated, effectively doubling the feature  dimensionality  to  64×64×512.  Subsequently,  this  enhanced feature map undergoes convolution to match  the resolution required by subsequent layers, returning  to 64×64×256.

Mamba‑DeeplabV3 network DeepLabV3+ implements multi-scale feature extraction  through dilated convolution and spatial pyramid  pooling modules, and integrates with an encoder- decoder structure. This approach effectively retains  high-resolution details, making it suitable for processing  complex scenes.

Although CNNs excel in local feature extraction,  they have limitations in capturing global contextual  information. Transformers, such as Vision Transformers  (ViTs) and Swin Transformers, introduce the self- attention  mechanism  to  enhance  global  feature  modeling. However, this improvement often comes  at the cost of significantly increased computational  complexity and memory consumption. Mamba, a variant  of structured state-space sequence models (SSM), offers  a more efficient alternative by optimizing information  retention and filtering through a reparameterization  mechanism, thereby improving both modeling efficiency  and performance. Unlike ViTs, which rely heavily on  computationally expensive self-attention mechanisms  to establish long-range dependencies, Mamba achieves  a balance between local and global feature modeling  through its unique bidirectional propagation strategy.  Vision Mamba enables the model to efficiently integrate  both local and global information by propagating feature  representations in two directions(forward and backward)  and subsequently merging the outputs. This bidirectional  feature propagation effectively reduces the computational  overhead typically associated with Transformer-based  architectures while enhancing the model’s ability

Automatic update strategy of labeled data (AUL) Obtaining high-quality segmentation labels for rapeseed  flower data presents considerable challenges due to the  intricate structure of the flowers and the labor-intensive  nature of manual annotation. Moreover, the presence  of inaccurate annotations within the original labeled  dataset may adversely affect model performance. These  challenges are particularly significant in semi-supervised  learning tasks, where the quality of labeled data directly  influences model accuracy.

In traditional semi-supervised segmentation methods  like FixMatch and Mean Teacher, pseudo-labels are  generated for unlabeled data, and these pseudo-labels  are used to augment the labeled dataset during training.

Page 8 of 20 Li et al. Plant Methods           (2025) 21:54

While both methods have shown success in improving  segmentation performance, they rely heavily on the  assumption that high-confidence pseudo-labels are  accurate. This can lead to issues in the presence of noisy  or low-quality annotations, as the model may amplify  errors from incorrect pseudo-labels.

Unlabeled loss defines three main loss functions, hard- supervised loss, soft-supervised loss, and correlation loss,  which play a key role in improving the quality of pseudo- labeling and enhancing the utilization of unlabeled data.  The hard supervision loss ( Lh

u ) employs a pixel-wise  cross-entropy loss to achieve output consistency between  strongly augmented and weakly augmented images in  high-confidence regions. Equation (2) is expressed as  follows:

FixMatch  uses  a  consistency-based  approach,  comparing strong and weak augmentations of unlabeled  data to enforce consistency between predictions. Pseudo- labels are assigned to high-confidence predictions,  assuming they are accurate. However, when the initial  labeled dataset contains noisy annotations, errors can  be propagated into the pseudo-labeled data, negatively  affecting training.

N

u = 1

(2) Lh

i), F(xw

F(xs

⊙Mi

i )

lc

N

i=1

where lc represents the pixel-wise cross-entropy loss  function, Mi is a binary mask used to identify high- confidence regions within the strongly augmented image  F(xw

Similarly, Mean Teacher generates pseudo-labels by  using an exponential moving average of the model’s  weights to ensure consistent predictions over time.  While effective, it can still suffer from inaccurate initial  labels, as errors in early pseudo-labels may accumulate,  reducing label refinement effectiveness.

i ) and F(xw

i  ) denote the predicted outputs of  the weakly and strongly augmented images xs

i  ). F(xs

i and xw

i  after processing through the network respectively. The  soft supervised loss(Ls

u ) considers the difference in logits  outputs between the weakly and strongly augmented  images and uses the Kullback–Leibler divergence to  measure their similarity within high-confidence regions.  Equation (3) is expressed as follows:

Given these challenges, our Automatic Update Strategy  of Labeled Data (AUL) offers a more controlled and  dynamic approach to address the issues associated with  noisy labels.In our approach, pseudo-labels are generated  for unlabeled data, and the label propagation process  begins after a specified number of training epochs (T).  From this point onward, pseudo-labels are filtered based  on confidence scores, and only those with confidence  exceeding a predefined threshold are incorporated into  the labeled dataset. This dynamic update strategy ensures  that only the most reliable pseudo-labels contribute to  model training, effectively preventing the propagation  of errors from noisy annotations while progressively  enhancing model performance.

N

u = 1

i), ˆF(xw

ˆF(xs

(3) Ls

⊙Mi

i )

KL

N

i=1

where KL is the Kullback–Leibler scatter, and ˆF(x)  denotes the logits output, Mi is the mask of the high  confidence region.

Correlation loss(Lc

u ) pixel propagation strategy is  introduced, which combines the correlation map  between features and propagates it into the pseudo-label  generation to improve the accurate recognition of the  same object region. The correlation loss formula (4) is:

Loss function The supervised loss(Ls ) is derived from both the labeled  dataset Dl and the subset of high-confidence data, which  is iteratively updated throughout the training process.  Specifically, the Ls is a weighted loss function consisting  of two components, the cross-entropy loss(Lh

N

u = 1 |N|

(4) Lc

i , F(xw

zu

⊙Mi

i )

lc

i=1

where zu

i is the pseudo-labeled representation after  correlation map propagation. So the unsupervised loss  formula (5) is:

s ) and the  supervised correlation loss(Lc

s ). Equation (1) is expressed  as follows:

(5) Lu = 1Lh

u + 2Ls

u + 3Lc

u

(1) Ls = 1

Lh

s + Lc

The default setting 1 , 2 , 3 is [0.5, 0.25, 0.25].

s

2

where cross-entropy loss(Lh

s ) is used to measure the  difference between model predictions and true labels  to ensure the model’s ability of accurate classification.  Supervised correlation(Lc

Evaluation indicators The performance of the segmentation model is evaluated  via Precision, Recall and Intersection over Union (IoU).  Precision, which is the ratio of the number of true  positive samples correctly identified to the total number  of positive samples classified by the classifier. Recall,

s ) helps the model understand  the spatial structure in an image by capturing the  similarity relationships between pixels.

Page 9 of 20 Li et al. Plant Methods           (2025) 21:54

which is the ratio of the number of true positive samples  correctly identified to the actual number of positive  samples. F1 score is a harmonic mean of Precision  and Recall, providing a balanced measure of model  performance. Accuracy is the ratio of correctly predicted  samples (both positive and negative) to the total number  of samples, reflecting the overall correctness of the  model. Intersection over Union (IoU), which measures  the overlap between the predicted results and the ground  truth by dividing their intersection by their union.

the network. These additional metrics, FLOPs and  parameters, allow for a more comprehensive evaluation,  ensuring a balance between model accuracy and  computational resource efficiency.

Ablation experiments Data generation enhancements In the context of semi-supervised semantic segmentation  tasks, effectively utilizing unlabeled data is crucial for  improving model performance. However, the quality and  quantity of unlabeled data are both critical factors.

It is an indicator that combines precision and recall,  and can well reflect the accuracy of the segmentation  results. Therefore, this paper adopts IoU to evaluate the  segmentation performance of the segmentation model.  The IoU value ranges from 0 to 1, with higher values  indicating better consistency between the predicted  segmentation and the true segmentation.

In this study, we first conducted an image quality  evaluation experiment on the generated images to ensure  their reliability for training. Following the training of the  DDPM model using a dataset of 300 images spanning  different flowering stages, we leveraged the trained  model to generate a variety of images representing  distinct flowering periods (as illustrated in Fig.  5). To  assess the quality of the generated images, we employed  three widely recognized image evaluation metrics: LPIPS,  FID, and SSIM. The Learned Perceptual Image Patch  Similarity (LPIPS) metric quantifies perceptual similarity  between images, where lower values indicate higher  perceptual similarity and, consequently, superior image  quality. LPIPS values typically range from 0 to 1, with  0.35 to 0.46 observed in our experiments. The Frechet  Inception Distance (FID) evaluates the distributional  similarity between real and generated images, with lower  values signifying that the generated images exhibit closer  resemblance to real images in terms of content and style.  FID scores generally range from 0 to infinity, where  values below 10 indicate high-quality generation. In our  case, the FID values range from 13.00 to 15.00, suggesting  a reasonable similarity to real images. The Structural  Similarity Index (SSIM) measures the structural  similarity between images, with values approaching  1 reflecting stronger alignment with the structural  features of real images. SSIM values fall within 0 to 1,  where higher values indicate better image quality. Our  generated images achieved SSIM values between 0.85  and 0.89, demonstrating strong structural consistency  with real images.

They are calculated as follows:

(6) Precision = TP TP + FP

(7) Recall = TP TP + FN

(8) IoU = TP TP + FN + FP

(9) F1 score =2 × Precision × Recall

Precision + Recall

(10) Accuracy = TP + TN TP + TN + FP + FN

where TP represents the true positives (the samples  correctly predicted as positive), TN denotes the true  negatives (the samples correctly predicted as negative),  FP is the false positives (the samples incorrectly predicted  as positive), and FN is the false negatives (the samples  incorrectly predicted as negative).

To provide a comprehensive evaluation of the model’s  performance,  we  incorporated  the  computational  efficiency measures. FLOPs (Floating Point Operations)  were used to quantify the computational cost of the  model, providing an indication of the total number of  arithmetic operations required during both training  and inference. FLOPs represent the number of floating- point multiplications and additions performed, offering a  measure of the computational burden. Additionally, the  number of parameters was considered as a key indicator  of the model’s complexity and memory consumption,  reflecting the total count of learnable weights in

As demonstrated by the boxplots in Fig.  5, the  generated images exhibit satisfactory quality across  various flowering stages. Collectively, these metrics  validate the quality of the generated images, confirming  their potential for use in subsequent training tasks. Having confirmed the quality of the generated images,  we proceeded to investigate the importance of unlabeled  data quantity in the experiment. Starting with an initial  dataset of 30 labeled images and 300 unlabeled images,  we expanded the unlabeled dataset using both real images  and generated images, as shown in Table  1. When the

Page 10 of 20 Li et al. Plant Methods           (2025) 21:54

Fig. 5  Visualization of original and generated images from different flowering stages, with quality validation of the generated images using LPIPS,  FID, and SSIM

Table 1  Comparison of the accuracy of different quantities of unlabeled data

Dataset (L/U) Precision(actual/ generated)

Recall(actual/ generated)

IoU(actual/generated) F1 score(actual/ generated)

Accuracy(actual/ generated)

30/300 0.921/- 0.923/- 0.875/- 0.922/- 0.922/-

30/600 0.939/0.936 0.936/0.932 0.884/0.882 0.937/0.934 0.937/0.934

30/900 0.945/0.942 0.948/0.940 0.893/0.886 0.946/0.941 0.945/0.940

30/1200 0.947/0.940 0.948/0.943 0.891/0.888 0.947/0.941 0.947/0.941

30/1500 0.948/0.938 0.951/0.942 0.893/0.885 0.949/0.940 0.947/0.940

Bold values indicate the highest performance achieved when using 30 labeled images and 900 unlabeled images, suggesting that this configuration offers the  optimal balance between segmentation accuracy and the image generation efficiency of the diffusion model

leveled off.The above results indicate that the quantity of  data involved in training is important.

number of unlabeled images reached 600, the precision,  recall, and IoU obtained through real image expansion  were 0.939, 0.936, and 0.884, respectively, while those  achieved using generated images were 0.936, 0.932, and  0.882. When the amount of unlabeled data increased to  900, both methods of increasing labels improved the IoU  accuracy by at least 1 percentage point. As the dataset  continued to expand to 1500 images, performance gains

Although the performance metrics for generated  images were slightly lower than the actual images, the use  of diffusion-generated images for training significantly  reduced the time costs associated with data collection  and processing. The diffusion model can rapidly produce  diverse unlabeled images, providing an efficient and  flexible solution for dataset expansion, especially in

Page 11 of 20 Li et al. Plant Methods           (2025) 21:54

epochs. To evaluate the reliability of these predictions,  we computed the confidence score for each stage using  the following formula:

scenarios where actual data collection is challenging or  costly. In this paper, we ultimately opted to expand the  unlabeled dataset with diffusion-generated images and  chose the 30/900 configuration to balance accuracy  improvements and training efficiency.

H

W

conﬁdence = 1 H × W

max(P(0 | i, j), P(1 | i, j))

i=1

j=1

(11)

Base network selection This paper employs Mamba-DeepLabv3+ as the base  network and compares its performance against several  widely used architectures, including UNet, SegNet,  Deeplabv3+, HRNet, and SegFormer. As shown in  Table 3, the DM_CorrMatch framework with the Mamba- DeepLabv3+ network achieves the highest scores across  all five evaluation metrics: precision, recall, IoU, F1  score, and accuracy. Notably, Mamba-DeepLabv3+  attains an IoU of 0.886, outperforming Deeplabv3+  (0.856) and other baseline models, demonstrating its  effectiveness in improving segmentation accuracy and  detail preservation. In terms of computational efficiency,  Mamba-DeepLabv3+ exhibits a FLOP value of 84.54  GFLOPS, which, while slightly higher than UNet (83.46  GFLOPS) and SegNet (79.67 GFLOPS), remains within  a reasonable range given its superior segmentation  performance. The improvements introduced by Mamba  layers enhance feature extraction capabilities, enabling  better multi-scale representation without significantly  increasing computational costs.

where H and W represent the height and width of the  image, and P(0 | i, j) and P(1 | i, j) denote the softmax  probabilities for the two classes at pixel (i, j) . The results  indicate that the confidence scores remain consistently  high across different flowering stages, suggesting that the  pseudo-labels are reliable.

To verify the reliability of the pseudo-labels used in  this strategy, we conducted a preliminary evaluation  by generating pseudo-labels using a model trained for  30 epochs on labeled data that was not included in the  training process. The quality of these pseudo-labels was  assessed by calculating their IoU with the corresponding  ground truth labels. As shown in Fig.  7, we further  explored different confidence thresholds to determine  the optimal balance between pseudo-label quality  and quantity. The results indicated that a confidence  threshold of 0.8 provided the most effective trade-off,  ensuring both reliable pseudo-labels and sufficient data  expansion. Specifically, at this threshold(τ ), the IoU of the  selected pseudo-labels reached 0.91, while the number of  pseudo-labels meeting this criterion amounted to 240,  effectively balancing label quality and dataset expansion.  This dynamic update strategy effectively enhances the  model’s segmentation performance by improving the  quality of labeled data while simultaneously expanding its  diversity, thereby contributing to the model’s robustness  across varying environmental conditions and rapeseed  flowering stages.

These results confirm that integrating Mamba into  the  Deeplabv3+  framework  effectively  enhances  segmentation accuracy while maintaining a favorable  trade-off between performance and efficiency. In  contrast, the transformer-based architectures, despite  their promising potential, did not achieve the same level  of segmentation accuracy and efficiency as Mamba- Deeplabv3+. This makes Mamba-Deeplabv3+ a more  well-balanced and effective choice for high-precision  segmentation tasks.

Mamba module selection This experiment demonstrates the superiority of Vision  Mamba by integrating various Vision Mamba layers into  the feature extraction network. As shown in Table  4,  Vision Mamba has the best performance in terms of  IoU, with a value of 0.886. That is because Vision Mamba  enhances the understanding of both local and global  features through the incorporation of a bidirectional  state space model (SSM). This capability is especially  beneficial  in  semi-supervised  learning  scenarios,  where it significantly enhances the model’s robustness.  Therefore, in the context of canola flower segmentation,  Vision Mamba, with its bidirectional propagation  characteristics, is more adept at handling complex  spatial relationships, rendering it more suitable for semi- supervised semantic segmentation tasks.

Experiment of automatic update strategy of labeled data  (AUL) The training epoch at which the AUL operation begins  plays a critical role in the model’s performance. As shown  in Fig. 8, our model achieved high segmentation accuracy  after 30 training epochs. Therefore, we initiated the AUL  operation starting from the 30 th epoch (T= 30). In  the AUL, the quality and quantity of pseudo-labels also  have a significant impact on the experiment, making the  selection of an appropriate confidence threshold crucial.

As shown in Fig. 6, the probability maps illustrate the  segmentation results for rapeseed flowers at different  flowering stages, predicted by a model trained for 30

Page 12 of 20 Li et al. Plant Methods           (2025) 21:54

Table 2  Comparison of ablation experiment accuracy

Base  Network

Mamba AUL Diffusion Precision Recall IoU F1 score Accuracy Flops (G) Parameters (M)

✓ 0.910 0.913 0.865 0.911 0.922 66.86 64.18

✓ ✓ 0.923 0.924 0.874 0.924 0.923 73.87 66.74

✓ ✓ 0.923 0.922 0.872 0.922 0.923 67.96 65.12

✓ ✓ ✓ 0.945 0.948 0.893 0.946 0.945 74.97 67.68

✓ ✓ 0.931 0.925 0.875 0.931 0.930 85.33 73.28

✓ ✓ ✓ ✓ 0.942 0.940 0.886 0.941 0.940 84.54 76.78

Bold values highlight the best results obtained in the ablation study in terms of accuracy and model complexity

Table 3  Comparison of the accuracy of different kinds of base network

Base Network Precision Recall IoU F1 Score Accuracy F(G)/P(M)

UNet 0.918 0.912 0.865 0.915 0.928 83.46/66.37

SegNet 0.910 0.900 0.858 0.905 0.920 79.67/74.21

Deeplabv3+ 0.932 0.929 0.856 0.930 0.938 80.35/71.72

Mamba-Deeplabv3+ 0.942 0.940 0.886 0.941 0.949 85.54/76.78

HRNet 0.922 0.913 0.848 0.917 0.926 88.23/71.41

SegFormer 0.925 0.912 0.872 0.918 0.932 90.12/99.32

Bold values emphasize the base network, the Mamba module, and our proposed DM_CorrMatch method, respectively, and mark the best accuracy attained under  each experimental condition

Table 4  Comparison of the accuracy of different kinds of  Mamba

Method Precision Recall IoU F1 Score Accuracy

Traditional Mamba 0.927 0.929 0.878 0.928 0.927

VMamba 0.928 0.932 0.873 0.930 0.929

Vision Mamba 0.942 0.940 0.886 0.941 0.940

Bold values emphasize the base network, the Mamba module, and our proposed  DM_CorrMatch method, respectively, and mark the best accuracy attained  under each experimental condition

Module ablation experiments In this paper, we conduct an ablation study to evaluate  the contribution of the Vision Mamba layer, the diffusion  model, and the Automatic Update Strategy Of Labeled  Data (AUL) in the DM_Corrmatch. We begin with  the base network DeeplabV3+ and sequentially add  Component Vision Mamba, the AUL and the diffusion  model to create a series of variant models. Each variant  is trained and evaluated on the same dataset to ensure  consistency.

The results are summarized in Table 2. The introduction  of the Mamba layer increases the model’s Precision to  0.923, Recall to 0.924, and IoU to 0.874. It indicates that  the Mamba layer performs well in capturing detailed

Fig. 6  Probability Distribution Map of Rapeseed Images at Different  Periods

Page 13 of 20 Li et al. Plant Methods           (2025) 21:54

to Lab and HSV spaces, and extracts nine color features  for each pixel. And then these features are used to classify  the pixels in the canola region as the foreground, with the  remaining pixels as background, thereby implementing  supervised image segmentation.

The twelve semantic segmentation methods include  seven fully supervised and four semi-supervised methods.  The fully supervised networks include UNet, PSPNet,  SegNet,  Attention-UNet,  DeepLabv3+,  SegFoemer,  and Swin-Unet. UNet is a classical encoder-decoder  architecture that fuses feature maps from the encoder  and decoder through skip connections, preserving high- resolution information. PSPNet enhances the global  contextual information by introducing a Pyramid Pooling  Module, which aggregates the multi-scale contextual  information to improve multi-scale feature modeling.  SegNet builds on the UNet by up-sampling at the  decoder stage using the encoder’s max-pooling indices,  thereby recovering spatial details more accurately.  Attention-UNet adds an attention mechanism to the  UNet’s structure, improving segmentation by allowing  the network to focus on the important feature regions  adaptively  while  suppressing  background  noise.  DeepLabv3+ introduces the Atrous Convolution in  the encoder to increase the receptive field and capture  multi-scale information, with the decoder recovering  high-resolution segmentation results. SegFormer [38] is  a transformer-based network that leverages self-attention  mechanisms to capture long-range dependencies and  global context, achieving high accuracy in segmentation  tasks with reduced computational complexity. Swin- UNet [39] utilizes a hierarchical transformer structure to  capture multi-scale features, combining the advantages  of both convolutional and transformer-based models,  making it effective for semantic segmentation with high- resolution outputs.

Fig. 7  Average quality and quantity of pseudo-labels under different  confidence thresholds

features, with a significant performance improvement,  albeit with an increase in computational complexity  and parameter count to 73.87 GFLOPs and 66.74  million, respectively. The AUL also improves the model’s  performance metrics, with a Precision of 0.923, Recall  of 0.922, and IoU of 0.872. It is worth noting that when  these two parts work together, the evaluation metrics  reach their highest. The combination of the Mamba  layer and AUL strategy substantially improves the overall  segmentation performance.

If it is a task with a limited samples, one can first  increase the sample size through the diffusion model.  From the Table 2, we can see that adding the Diffusion  Module for data augmentation alone also achieves the  goal of improving model performance, but at the cost of  an increased model complexity and computational load.  When combining the Mamba layer and the AUL strategy  simultaneously, the model achieves better performance  metrics, with an IoU of 0.886. However, this comes at  the cost of computational complexity peaking at 84.54  GFLOPs, and the parameter count reaching its maximum  at 76.78 million.

Semi-supervised semantic segmentation methods  include AugSeg, CorrMatch, UniMatch, FixMatch, and  our DM_CorrMatch. AugSeg improves the model’s  generalization ability by employing data augmentation  and consistency regularization on unlabeled data. By  maintaining prediction consistency across different  augmented views, it maximizes the use of unlabeled data.  CorrMatch enhances semi-supervised learning through  pseudo-label generation and alignment, progressively  improving the prediction quality of unlabeled data and  boosting overall segmentation performance. FixMatch  employs consistency regularization by weakly and  strongly  augmenting  unlabeled  data,  maintaining  prediction consistency between both views, thereby  facilitating effective utilization of unlabeled data and  significantly  enhancing  semi-supervised  learning.  UniMatch extends FixMatch by introducing a unified

Comparison with advanced methods In this paper, four traditional methods and twelve  semantic segmentation methods are used for tests.  The traditional methods include the Otsu method,  H-channel segmentation in HSV color space, k-means  clustering in Lab color space, and color feature-based  segmentation techniques. The Otsu method, proposed  in 1979, determines the optimal segmentation threshold  by maximizing inter-class variance, thereby binarizing  the image. H-channel segmentation in HSV color space  performs threshold segmentation based on the hue  channel. K-means clustering in Lab color space first  converts the image to Lab space and then applies the  k-means algorithm for clustering. The color feature- based segmentation method first converts the RGB image

Page 14 of 20 Li et al. Plant Methods           (2025) 21:54

complexity. However, they are significantly constrained  in performance when dealing with complex segmentation  tasks. This result also demonstrates the powerful feature  extraction capability of deep learning, a data-driven  approach, and its advantages in handling complex tasks.

matching strategy that aligns the feature distributions  across data sources, thereby leveraging information from  multiple data sources more effectively and improving  model robustness and accuracy.

All of these methods are applied to the RFSD dataset in  this study. For the fully supervised segmentation model,  a dataset ratio of 8:1:1 was used for training, validation,  and testing, while for the semi-supervised approach,  only 30 labeled samples and 900 unlabeled samples  were used. To ensure fairness in the experiment, all fully  supervised segmentation networks were also tested  using the same number of labeled samples as the semi- supervised approach (30 labeled samples). As shown in  Table 5, significant differences exist between traditional  and deep learning methods, where traditional methods  are outperformed by deep learning methods in terms of  Precision, Recall, IoU and F1 Score, Accuracy. Traditional  techniques such as the Otsu method and HSV color  segmentation, offer advantages in terms of computational

Fully-supervised  deep  learning  models  include  UNet, PSPNet, SegNet, Attention-UNet, DeepLabv3+,  SegFormer, and Swin-Unet. Table  5 shows that when  the fully supervised networks are trained with only 30  labeled samples, the models are undertrained compared  to when 576 labeled samples are used, resulting in  lower performance. In contrast, for the fully trained  models, except for Unet, all six models reached an IoU  above 0.81. This is because Unet is relatively simple  with fewer parameters, thus it has faster training and  inference speeds. SegFormer and Swin-Unet show  significantly higher IoU values compared to the other  fully supervised networks, with accuracies of 0.875 and  0.876, respectively, outperforming the lowest-ranking

Table 5  Comparison of different network evaluation indicators


## Methods

Label images
Precision
Recall
IoU
F1 score
Accuracy
FLOPs (G)
Parameters (M)

Traditional Methods

Otsu Method / 0.710 0.724 0.706 0.717 0.717 / /

HSV(H) / 0.673 0.775 0.615 0.719 0.719 / /

K-means clustering / 0.621 0.762 0.642 0.686 0.686 / /

Color characteristics / 0.794 0.838 0.780 0.815 0.815 / /

Deep Learning Methods (fully supervised)

Unet 576 0.803 0.897 0.794 0.848 0.869 11.25 31.03

30 0.752 0.812 0.730 0.780 0.780

Pspnet 576 0.840 0.836 0.810 0.838 0.858 38.83 65.32

30 0.775 0.820 0.745 0.797 0.798

SegNet 576 0.795 0.840 0.810 0.817 0.824 16.88 45.78

30 0.743 0.799 0.728 0.769 0.771

Attention-UNet 576 0.830 0.910 0.845 0.868 0.876 12.23 33.28

30 0.780 0.835 0.765 0.807 0.808

Deeplabv3+ 576 0.800 0.850 0.855 0.824 0.833 22.34 45.25

30 0.745 0.805 0.735 0.770 0.771

SegFormer 576 0.842 0.880 0.876 0.859 0.885 48.13 85.35

30 0.770 0.830 0.790 0.798 0.810

Swin-Unet 576 0.813 0.865 0.875 0.839 0.860 44.72 68.28

30 0.768 0.828 0.758 0.792 0.804

Deep Learning Methods (semi-supervised)

Augseg 30 0.911 0.924 0.853 0.917 0.920 26.07 59.55

Corrmatch 30 0.910 0.913 0.865 0.912 0.912 66.86 64.18

Unimatch 30 0.921 0.911 0.871 0.916 0.917 23.98 60.12

Fixmatch 30 0.900 0.909 0.842 0.904 0.905 23.94 59.50

DM_CorrMatch (without diffusion) 30 0.945 0.948 0.893 0.946 0.945 74.97 67.68

DM_CorrMatch (with diffusion) 30 0.942 0.940 0.886 0.941 0.940 84.54 76.78

Bold values emphasize the base network, the Mamba module, and our proposed DM_CorrMatch method, respectively, and mark the best accuracy attained under  each experimental condition

Page 15 of 20 Li et al. Plant Methods           (2025) 21:54

optimization process in the early stages. However, its  final Loss value remained higher compared to models  like DM_CorrMatch and DeepLabV3+, which showed  lower and more stable Loss values as training concluded.  These results emphasize the superior optimization and  stability of DM_CorrMatch despite its slower initial Loss  reduction.

Unet by 8%. However, this comes with relatively high  computational complexity.

The five semi-supervised methods, all using only 30  labeled data samples, can achieve IoU comparable to fully  supervised methods. Among them, the method proposed  in this paper achieved a segmentation accuracy IoU that  is even 1.1% higher than that of fully supervised methods,  reaching 0.886. The above results demonstrate that the  effective use of unlabeled data can indeed enhance the  segmentation performance of the task. However, this  comes with the cost of increased network overhead due  to the update strategies for unlabeled data. In this paper,  the network, due to the addition of a diffusion model  and a Mamba structure, has reached 84.54 in FLOPs and  76.78 in model parameters. During the 100-epoch training process, the models  exhibited distinct differences in Precision, Recall,  F1 Score, Accuracy, IoU, and Loss performance. As  illustrated in Fig. 8, DM_CorrMatch ultimately achieved  the highest final Precision, Recall, IoU and F1 Score,  Accuracy values, demonstrating superior segmentation  accuracy. However, in the early stages of training, its  improvement in these metrics was slower than certain  models, such as DeepLabV3+ and AugSeg, which showed  faster initial growth. Nevertheless, DM_CorrMatch  surpassed  these  models  as  training  progressed,  stabilizing around epoch 20 and maintaining the best  final performance.

To comprehensively assess the robustness of the model,  this paper provides visual predictions for different growth  stages of canola flowers, including the early, mid, full,  and late flowering stages. As illustrated in Fig. 9, we first  present the images and corresponding labels for the four  flowering stages of rapeseed. visual Subsequently, twelve  different deep learning methods were employed to predict  segmentation results for the images at various stages. To  provide a more intuitive reflection of the discrepancies  between the segmentation results and the labels, we  compared the segmentation outcomes with the ground  truth labels. In this comparison, Over Segmentation refers  to instances of excessive prediction, Exact Segmentation  denotes accurate predictions, and Under Segmentation  indicates  instances  of  insufficient  prediction.  The  visualization results indicate that the flowering stage,  characterized by abundant and plump inflorescences, yields  the best segmentation outcomes. In contrast, the early and  middle flowering stages of rapeseed, with yellowing buds,  and the late flowering stage, with pods obscuring the view,  both affect the model’s segmentation accuracy, leading to  instances of over-segmentation and under-segmentation.  As seen in the visual outcomes, it is evident that our

Interestingly, for Loss, SegNet demonstrated the fastest  reduction during the initial epochs, reflecting its rapid

Fig. 8  Precision, Recall, IoU and F1 Score, Accuracy training process precision curves

Page 16 of 20 Li et al. Plant Methods           (2025) 21:54

Fig. 9  Visual segmentation of different networks corresponding to different flowering periods

DM_CorrMatch model performed exceptionally well  in every stage. Consistent with the evaluation results in  Table 5.

full flowering cycle of most varieties of oilseed rapeseed.  Rapeseed flower coverage values were measured to map  the changes in coverage of the same plot at different  times. Figure  10b illustrates that the X-axis represents  different times during the flowering period collected in  2022, while the Y-axis denotes the flower coverage value.  The variation in the number of inflorescences during  flowering in different plots of rapeseed was depicted  using dotted lines of varying colors. The figure reveals  significant variation in flowering periods and growth  conditions among different varieties. Some rapeseed  varieties exhibited vigorous growth as early as February  14 but also withered sooner, while others bloomed and  withered later. Most canola varieties reach peak bloom  between March 4 th and March 18 th. These data are  important for assessing the growth status of oilseed  rapeseed and optimizing cultivation strategies.


## Discussion

Monitoring changes in the flower coverage
Monitoring changes in the coverage of canola flowers is 
crucial for breeding. By determining coverage changes in 
canola fields, the growth and wilting of canola flowers can 
be clearly observed. When the segmented image of canola 
flowers is acquired, the coverage value of the canola flowers 
can be determined by calculating the percentage of flower 
pixels, as shown in Eq. 12.

(12) Flower coverage = Number of ﬂower pixels Total number of plot pixels

This enables a clearer understanding of the growth  patterns of different canola varieties, as illustrated  in Fig.  10a. In addition to monitoring the flowering  coverage of different materials at the same time, 44 plots  from the 2022 field images were analyzed, covering  oilseed rapeseed flower data from February 14 th to  April 1 st over 12 distinct periods, encompassing the

To explore the differences among these varieties at  a deeper level, this paper employed RapeNet+ [40]  to analyze the data showing minimal differences in  coverage. Figure  10c illustrates the mid-flowering  and full-flowering periods for plot No. 1 and No. 3,  respectively. During the mid-flowering period, plot 3  showed slightly higher coverage than plot 1, with a bud

Page 17 of 20 Li et al. Plant Methods           (2025) 21:54

Fig. 10  Application. a Segmentation results and coverage values for 4 blocks of cells. b Performance Metrics for UAV Image Segmentation  at Different Flight Heights. c The rapeseed flower coverage and corresponding flower count during the mid-bloom and full bloom stages in Plot 1  and Plot 3

flight altitude can enhance data acquisition efficiency  while maintaining high segmentation accuracy. This  study aims to identify the optimal flight altitude and  resolution configuration to balance acquisition efficiency  and segmentation accuracy, providing practical insights  for UAV applications in agricultural settings.

count of 290, surpassing the 282 buds recorded in plot  1. However, during the full flowering period, although  plot 3 had lower coverage than plot 1, it still had a  significantly high bud count. The resulting data provide  breeding experts with essential quantitative assessments,  facilitating the evaluation of the performance of various  rapeseed varieties across distinct growth stages.

To simulate resolution variations at different flight  altitudes, this study employs a diffusion model to  generate images at varying resolutions.

Relationship between UAV flight height and coverage  measurement accuracy In this section, we investigate the impact of UAV-acquired  images at different flight altitudes on semi-supervised  semantic segmentation, validate the robustness of  DM_CorrMatch, and discuss the optimal balance  between flight altitude and model accuracy. As flight  altitude increases, shorter acquisition times facilitate  the coverage of larger areas and reduce the impact of  illumination variations caused by time differences on  image quality, despite a decrease in resolution. However,  the small and dense nature of rapeseed flower clusters  means that excessively high flight altitudes adversely  affect segmentation accuracy. Therefore, an appropriate

The relationship between UAV flight altitude and GSD  follows the principle of pinhole imaging, expressed by the  following equation:

(13) GSD = H · p

F

where GSD (Ground Sampling Distance) represents  the actual ground area covered by each pixel, H is the  flight altitude, p is the pixel size of the sensor, F is the  focal length of the camera. According to this formula  13, flight altitude is directly proportional to GSD. As  flight altitude increases, GSD increases, resulting in  a reduction in image resolution. Figure  11 illustrates

Page 18 of 20 Li et al. Plant Methods           (2025) 21:54

Fig. 11  Schematic diagram of UAV flight height and image resolution, flight height 10 m, 15 m, 20 m, 25 m, 30 m, 35 m images

Table 6  Performance Metrics for UAV Image Segmentation at Different Flight Heights

Height (m) GSD (mm/pixel) Precision Recall IoU F1 Score Accuracy

10 2.7 0.942 0.940 0.886 0.941 0.93

15 4.1 0.940 0.943 0.885 0.941 0.92

20 5.5 0.938 0.939 0.887 0.938 0.91

25 6.9 0.903 0.898 0.865 0.900 0.89

30 8.2 0.872 0.861 0.827 0.866 0.86

35 9.6 0.801 0.844 0.788 0.822 0.84

ANOVA F-statistic 17.78 15.25 18.45 16.20 14.30

p-value 3.52e- 08 5.24e- 07 2.11e- 08 3.76e- 07 1.85e- 06

ability to differentiate target regions. As the flight  altitude increases further to 25 ms, 30 ms, and 35 ms,  significant declines in precision, recall, IoU, and F1 score  are observed, particularly at 35 ms, where the IoU drops  sharply to 0.788. This implies that at higher altitudes, the  model’s ability to capture fine details diminishes, leading  to a reduction in segmentation accuracy. This is likely  due to the decrease in image resolution and the loss of  detailed information.

the image resolutions corresponding to different flight  altitudes. Then, we use the DM_CorrMatch model to  predict images captured by the UAV at various flight  altitudes and calculate the corresponding performance  metrics, as shown in Table 6. The results align with the  aforementioned  analysis,  demonstrating  significant  variations in segmentation accuracy, recall, F1 score, and  IoU at different flight altitudes. At flight altitudes of 10 ms  and 15 ms, the model performs similarly, with precision  and recall both around 0.94, and IoU values of 0.886  and 0.885, respectively. The F1 score also remains high,  indicating that at lower altitudes, the model effectively  captures details of the target area while maintaining high  predictive accuracy.

To  validate  these  observations  statistically,  we  performed an ANOVA test on the performance metrics  across different altitudes. The results indicate that  the differences between the altitudes are statistically  significant. The F-statistic values for precision, recall,  IoU, F1 score, and accuracy are 17.78, 15.25, 18.45, 16.20,  and 14.30, respectively, with corresponding p-values of  3.52e−08, 5.24e−07, 2.11e−08, 3.76e−07, and 1.85e−06.  These p-values are all well below the threshold of 0.05,  indicating that the observed differences in performance  metrics are not due to random chance but rather

However, when the flight altitude increases to 20 ms,  a slight decrease in precision and recall is observed,  dropping to 0.938 and 0.939, respectively, while the IoU  improves to 0.887. This suggests that at this altitude, the  model’s predictive consistency is enhanced, achieving  a better balance between image quality and the model’s

Page 19 of 20 Li et al. Plant Methods           (2025) 21:54

reflect a true effect of the flight altitude on the model’s  performance. This confirms that the model’s accuracy is  significantly influenced by the flight height, making the  findings robust and meaningful.

the field trials of rapeseed and provided professional expertise in rapeseed  studies. All authors read and approved the final manuscript.

Funding The research was supported by the National Key Research and  Development Program of China (2023YFD1201401), the Key Research  and Development Program of Hubei Province (2023BBB030), the National  Natural Science Foundation of China (Grant Numbers: 32172101, 42301515),  and the Knowledge Innovation Program of Wuhan-Basic Research  (2022020801010295).

In our oilseed rapeseed base, theoretically, a flight  altitude of 20 ms is the optimal height for data collection,  as the GSD at this altitude is 5.5 mm/pixel, ensuring high  accuracy while also reducing data acquisition time. This  provides a valuable reference for future data collection.

Data availability The dataset and code used in this study are not publicly available but can be  accessed upon reasonable request by contacting the corresponding author.


## Conclusion

This paper presents the DM_CorrMatch framework 
for monitoring rapeseed flower coverage, which 
addresses the challenges associated with limited 
labeled data through a semi-supervised approach. The 
framework integrates an Automatic Update Strategy 
Of Labeled Data (AUL), which enhances the quality 
of labeled datasets, and employs a diffusion model 
for dataset augmentation to effectively increase the 
sample size. The use of Mamba-DeeplabV3+ network 
further improves feature extraction by incorporating 
the Mamba layer into the shallow layers of ResNet101, 
enhancing both local and global feature capture.

Declarations

Ethics approval and consent to participate Not applicable.

Consent for publication Not applicable.

Competing interests The authors declare that they have no Competing interests.

Author details 1 Hubei Key Laboratory for High‑efficiency Utilization of Solar Energy  and Operation Control of Energy Storage System, Hubei University  of Technology, Wuhan 430068, China. 2 Key Laboratory of Biology and Genetic  Improvement of Oil Crops, Oil Crops Research Institute of the Chinese  Academy of Agricultural Sciences, Wuhan, China.

Our experiments show that the diffusion model- generated images provide results comparable to  those collected manually, demonstrating the efficacy  of this data augmentation strategy. Moreover, the  RFSD dataset, introduced in this work, is the first of  its kind for rapeseed flower segmentation in the field,  contributing a valuable resource for future research in  agricultural monitoring.

Received: 8 February 2025   Accepted: 4 April 2025


## References

1.	
China National Bureau of Statistics. China Statistical Yearbook 2023. 
Beijing, China: China Statistics Press; 2023.
	2.	
Sadras VO, Rebetzke GJ, Edmeades GO. The phenotype and the 
components of phenotypic variance of crop traits. Field Crop Res. 
2013;154:255–9.
	3.	
Xiuqing F, Bai Y, Zhou J, Zhang H, Xian J. A method for obtaining field 
wheat freezing injury phenotype based on RGB camera and software 
control. Plant Methods. 2021;17(1):120.
	4.	
Zhou J, Tardieu F, Pridmore TP, Doonan JH, Reynolds D, Hall N, Griffiths S, 
Cheng T, Zhu Y, Wang X, Jiang D, Ding Y. Plant phenomics: history, present 
status and challenges. J Nanjing Agric Univ. 2018;41:580–8.
	5.	
Maple R, Zhu P, Hepworth J, Wang J-W, Dean C. Flowering time: 
from physiology, through genetics to mechanism. Plant Physiol. 
2024;195:190–212.
	6.	
Yunhe W, Zhen T, Wanyi W, Daniele FL, Chunhong Q, Chuanhong W, Hui 
W, Shamsur R, Jian S, Yan Z, Peijin L. Molecular variation in a functionally 
divergent homolog of FCA regulates flowering time in arabidopsis 
thaliana. Nat Commun. 2020;11
	7.	
Song J-M, Guan Z, Jianlin H, Guo C, Yang Z, Wang S, Liu D, Wang B, 
Shaoping L, Zhou R, Xie W-Z, Cheng Y, Zhang Y, Liu K, Yang Q, Chen L-L, 
Guo L. Eight high-quality genomes reveal pan-genome architecture and 
ecotype differentiation of Brassica napus. Nature Plants. 2020;6:34–45.
	8.	
Kirkegaard John A, Lilley Julianne M, Brill Rohan D, Ware Andrew H, 
Christine W. The critical period for yield and quality determination in 
canola (Brassica napus L.). Field Crops Res. 2018;223:131–42.
	9.	
d’Andrimont R, Taymans M, Lemoine G, Ceglar A, Yordanov M, van der 
Velde M. Detecting flowering phenology in oil seed rape parcels with 
sentinel-1 and -2 time series. Remote Sens Environ. 2020;239: 111660.
	10.	 Ti Z, Sally V, Sudhakar DH, Parkin IA, P, Guo Xulin, Johnson Eric N, Shirtliffe

Nevertheless,  this  approach  presents  several  challenges. The model’s large number of parameters  and  substantial  computational  demands  create  significant obstacles for its deployment in real- world applications. We recognize the importance of  computational efficiency for practical implementation,  and in future work, we plan to explore optimization  strategies, including lightweight model design, model  compression, hardware acceleration, and adaptive  computing, to enable real-time applications. Moreover,  we aim to extend our approach to other crops,  thus broadening the applicability of this method in  agricultural research and practice.

Acknowledgements The author would like to thank the China Oil Crop Research Institute The  Chinese Academy of Agricultural Sciences Suggestions and data support  provided in the research. We also thank the anonymous reviewers and  Thank you for the valuable opinions and constructive suggestions from the  academic editor, This helps to improve the manuscript.

Author ontributions JL and CYZ wrote the manuscript and developed the final version of the  application code. JL, CYZ, CBY, and QZ conducted on-site image acquisition.  BHW and JMT provided guidance on the experimental plan. JWQ supervised

Steven J. Phenotyping flowering in canola (Brassica napus L.) and

Page 20 of 20 Li et al. Plant Methods           (2025) 21:54

estimating seed yield using an unmanned aerial vehicle-based imagery.  Front Plant Sci. 2021;12: 686332. 	11.	 Shenghui F, Wenchao T, Yi P, Yan G, Can D, Ruhui C, Kan L. Remote

31.	 Zhang B, Zhang Y, Li Y, Wan Y, Guo H, Zheng Z, Yang K. Semi-supervised

deep learning via transformation consistency regularization for remote  sensing image semantic segmentation. IEEE J Sel Top Appl Earth Observ  Remote Sens. 2023;16:5782–96. 	32.	 Wang H, Huang H, Jing W, Li N, Kaihao G, Xiaomei W. Semi-supervised

estimation of vegetation fraction and flower fraction in oilseed rape with  unmanned aerial vehicle data. Remote Sens. 2016;8:5. 	12.	 Liang W, Yijian L, Haiyan C, Jiangpeng Z, Wenxin Y, Weikang W, Hongyan

segmentation of cardiac chambers from LGE-CMR using feature  consistency awareness. BMC Cardiovasc Disord. 2024;24(1):571. 	33.	 Luo X, Wang G, Liao W, Chen J, Song T, Chen Y, Zhang S, Metaxas DN,

Z, Dawei S, Weijun Z, Yong H. Combining uav-based vegetation indices  and image classification to estimate flower number in oilseed rape.  Remote Sens. 2018;10:9. 	13.	 Yunze Z, Xuehong C, Jin C, Yugang T, Yusheng S, Xin C, Xihong C. Remote

Zhang S. Semi-supervised medical image segmentation via uncertainty  rectified pyramid consistency. Med Image Anal. 2022;80: 102517. 	34.	 Sohn K, Berthelot D, Li C-L, Zhang Z, Carlini N, DogusCubuk E, Kurakin A,

sensing index for mapping canola flowers using modis data. Remote  Sens. 2020;12:23. 	14.	 Ti Z, Sally V, Duddu Hema SN, Parkin Isobel AP, Xulin G, Johnson Eric N,

Zhang H, Raffel C. Simplifying semi-supervised learning with consistency  and confidence Fixmatch. Adv Neural Inf Process Syst (NeurIPS).  2020;33:596–608. 	35.	 Lihe Y, Lei Q, Litong F, Wayne Z, Yinghuan S. Revisiting weak-to-strong

Shirtliffe Steven J. Phenotyping flowering in canola (Brassica napus L.) and  estimating seed yield using an unmanned aerial vehicle-based imagery.  Front Plant Sci 12, 2021. 	15.	 Wei Y, Miao L, Qiangyi Yu, Li W, Wang C, Tang H, Wenbin W. The

consistency in semi-supervised semantic segmentation. In: 2023 IEEE/ CVF Conference on Computer Vision and Pattern Recognition (CVPR),  7236–7246, 2022. 	36.	 Bo S, Yuqi Y, Le Z, Ming-Ming C, Qibin H. Corrmatch: Label propagation

normalized difference yellow vegetation index (NDYVI): A new index for  crop identification by using gaofen-6 wfv data. Comput Electron Agric.  2024;226: 109417. 	16.	 Filippo Di Gennaro Salvatore, Alessandro M. Evaluation of novel precision

via correlation matching for semi-supervised semantic segmentation. In:  2024 IEEE/CVF Conference on Computer Vision and Pattern Recognition  (CVPR), 3097–3107, 2023. 	37.	 Zebin Y, Yong Z, Fan B, Jiacheng S, Chongxuan L, Jun Z. Diffusion models

viticulture tool for canopy biomass estimation and missing plant  detection based on 2.5d and 3d approaches using RGB images acquired  by UAV platform. Plant Methods. 2020;16(1):91. 	17.	 Linyuan L, Mu X, Hailan J, Francesco C, Hu R, Wanjuan S, Jianbo Q,

and semi-supervised learners benefit mutually with few labels. ArXiv,  abs/2302.10586, 2023. 	38.	 Enze X, Wenhai W, Zhiding Y, Anima A, Álvarez José Manuel, Ping L.

Shouyang L, Jiaxin Z, Ling C, Huaguo H, Guangjian Y. Review of ground  and aerial methods for vegetation cover fraction (fcover) and related  quantities estimation: definitions, advances, challenges, and future  perspectives. ISPRS J Photogrammet Remote Sens. 2023 	18.	 Salvador O-C, Tiago O, Manuel J-VA, Diego R, Nicolas R. RGB image-based

Segformer: Simple and efficient design for semantic segmentation with  transformers. In: Neural Information Processing Systems, 2021. 	39.	 Cao H, Wang Y, Chen J, Jiang D, Zhang X, Tian Q, Wang M. Swin-unet:

Unet-like pure transformer for medical image segmentation. In: ECCV  Workshops; 2021. 	40.	 Jie L, Enguo W, Jiangwei Q, Yi Fan L, Li L, Jian Y, Guisheng L. Automatic

method for phenotyping rust disease progress in pea leaves using R.  Plant Methods. 2023;19(1):86. 	19.	 Mahmudul HASM, Ferdous S, Dean D, Hamid L, Jones Michael GK. A

rape flower cluster counting method based on low-cost labelling and  UAV-RGB images. Plant Methods. 2023;19:40.

survey of deep learning techniques for weed detection from images.  Comput Electron Agric. 2021;184: 106067. 	20.	 Zhang P, Sun X, Zhang D, Yang Y, Wang Z. Lightweight deep learning

Publisher’s Note Springer Nature remains neutral with regard to jurisdictional claims in  published maps and institutional affiliations.

models for high-precision rice seedling segmentation from UAV-based  multispectral images. Plant Phenomics. 2023;5:0123. 	21.	 Li K, Zhang L, Li B, Li S, Ma J. Attention-optimized deeplab v3+ for

automatic estimation of cucumber disease severity. Plant Methods.  2022;18(1):109. 	22.	 Zhang Y, Wang T, You Y, Wang D, Mengyuan L, Wang H. A novel estimation

method of grassland fractional vegetation cover based on multi-sensor  data fusion. Comput Electron Agric. 2024;225: 109310. 	23.	 Cheng J, Deng C, Yanzhou S, An Z, Wang Q. Methods and datasets on

semantic segmentation for unmanned aerial vehicle remote sensing  images: a review. ISPRS J Photogramm Remote Sens. 2024;211:1–34. 	24.	 Cai M, Chen H, Zhang T, Zhuang Y, Chen L. Consistency regularization

based on masked image modeling for semisupervised remote sensing  semantic segmentation. IEEE J Select Top Appl Earth Observ Remote  Sens. 2024;17:17442–60. 	25.	 Moharram MA, Sundaram DM. Land use and land cover classification

with hyperspectral data: a comprehensive review of methods, challenges  and future directions. Neurocomputing. 2023;536:90–113. 	26.	 Cheng G, Yuan X, Yao X, Yan K, Zeng Q, Han J. Towards large-scale small

object detection: Survey and benchmarks. IEEE Trans Pattern Anal Mach  Intell. 2022;45:13467–88. 	27.	 Yangmingrui G, Linyuan L, Marie W, Wei G, Ming S, Hao L, Ruibo J, Yanfeng

D, Tejasri N, Rajalakshmi P, Frédéric B, Shouyang L. Bridging real and  simulated data for cross-spatial- resolution vegetation segmentation  with application to rice crops. ISPRS J Photogrammet Remote Sens.  2024;218:133–50. 	28.	 Yi Z, Zhongyue Z, Chongruo W, Zhi Z, Tong H, Hang Z, Manmatha R, Mu L,

Alexander S. Improving semantic segmentation via efficient self-training.  IEEE Trans Pattern Anal Mach Intell. 2024;46(3):1589–602. 	29.	 Zhang L, Lan M, Zhang J, Tao D. Stagewise unsupervised domain

adaptation with adversarial self-training for road segmentation of  remote-sensing images. IEEE Trans Geosci Remote Sens. 2022;60:1–13. 	30.	 Khatri R, Machart P, Bonn S. Dissect: deep semi-supervised consistency

regularization for accurate cell type fraction and gene expression  estimation. Genome Biol. 2024;25(1):112.
