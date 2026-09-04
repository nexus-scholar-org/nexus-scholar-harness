---
workspace_id: SCI-000138
doi: 10.1109/icdcc62744.2024.10961765
title: Crop and Weed Segmentation Using ResNet-Unet Architecture
authors:
- family_name: Purohit
  given_name: Aaryan
  orcid: null
- family_name: Pujari
  given_name: Pratik
  orcid: null
- family_name: Shah
  given_name: Krish
  orcid: null
- family_name: Nimkar
  given_name: Anant V.
  orcid: null
year: 2024
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:40.727153+00:00'
---

# Crop and Weed Segmentation Using ResNet-Unet Architecture

First International Conference on Data, Computation and Communication 2024

Crop and Weed Segmentation using ResNet-Unet


## Architecture

Aaryan Purohit   Department of Computer Engineering

Pratik Pujari   Department of Computer Engineering

Krish Shah  Department of Computer Engineering

2024 First International Conference on Data, Computation and Communication (ICDCC) | 979-8-3315-3295-6/24/$31.00 ©2024 IEEE | DOI: 10.1109/ICDCC62744.2024.10961765

Sardar Patel Institute of Technology

Sardar Patel Institute of Technology

Sardar Patel Institute of Technology

Mumbai, India  aaryan.purohit@spit.ac.in

Mumbai, India  pratik.pujari@spit.ac.in

Mumbai, India  krish.shah@spit.ac.in

Anant V. Nimkar  Department of Computer Engineering

Sardar Patel Institute of Technology

Mumbai, India  anant_nimkar@spit.ac.in

traditional image processing techniques and machine  learning algorithms like decision trees, random forests, and  support vector machines (SVM) [5].


## Abstract—The effectiveness of a ResNet-Unet (RU)

architecture for semantic segmentation of soil and weeds from 
sorghum plants in high-resolution UAV photos is investigated. 
The model makes use of Unet's encoder-decoder structure for 
precise segmentation and ResNet's deep residual learning for 
efficient feature extraction. To increase the resilience of the 
model, data augmentation methods such random rotations, 
flips, and horizontal and vertical adjustments were used, along 
with contrast enhancement methods like Gamma Correction 
and Contrast Limited Adaptive Histogram Equalization 
(CLAHE). Utilizing the ResNet-Unet framework, we were able 
to attain a maximum Sørensen-Dice Coefficient (DS) of 0.929, 
accompanied by a standard deviation of 0.0041. Classification 
measures show impressive accuracy: among background, 
sorghum, and weed classes, precision, recall, and F1-score 
range from 93.01\% to 99.68\%. The efficiency of RU 
architecture 
for 
precision 
agriculture 
applications 
is 
demonstrated by this study, which also provides a viable option 
for targeted weed management and automated weed detection.

The advent of deep learning, particularly CNNs, has  revolutionized weed detection and management in precision  agriculture [6]. Fully Convolutional Networks, SegNet, U- Net, and DeepLabv3 [7], have remarkably succeeded in  accurately segmenting weeds from crops in various  agricultural settings. Several studies have explored the  application of these models for weed mapping. Huang et al.  citehuang2018accurate utilized FCN with a conditional  random field (CRF) for weed distribution mapping,  achieving superior performance compared to traditional  pixel-based methods. Among these models, U-Net has  gained significant popularity for its ability to learn from  relatively small datasets and its effectiveness in capturing  fine-grained details, making it particularly suitable for weed  segmentation tasks [8] [9]. Researchers have further  enhanced  U-Net’s  performance  by  incorporating  modifications such as ResNet as the encoder backbone [10].

Keywords—Semantic Segmentation, Convolutional Neural  Networks (CNN), ResNet, Unet, Deep Learning, Precision  Agriculture.

This  work  investigates  the  RU  architecture’s  effectiveness for the precise segmentation of soil and weeds  from sorghum plants in high-resolution UAV photos,  addressing a critical challenge in precision agriculture.  Significant contributions include the development of a robust  segmentation model combining Unet’s encoder-decoder  structure for boundary delineation and ResNet’s deep  residual learning for feature extraction, demonstrating  remarkable accuracy with a maxi- mum Sørensen-Dice  Coefficient (DS) of 0.929. Additionally, comprehensive  exploration of preprocessing techniques, including data  augmentation  and  contrast  enhancement  methods,  significantly improves model robustness. Experimental  results highlight the model’s efficacy for practical  agricultural applications, offering insights and methodologies  for  automated  weed  detection  and  targeted  weed  management, ultimately contributing to advancements in  precision agriculture.

I.  INTRODUCTION

The global agricultural landscape faces a constant threat  from weed infestations, which significantly impact crop yield  and food production. Weeds, defined as unwanted wild  plants that grow naturally and spread rapidly, compete with  crops for essential resources such as water, sunlight,  fertilizers, and soil nutrients [1]. This competition hinders  growth, reduces yield, and, if uncontrolled, can lead to crop  failure [2]. Traditional weed control methods, including  mechanical approaches like mowing, mulching, and tilling  and chemical approaches using herbicides, have proven to be  labour-intensive, inefficient, and environmentally damaging  [3]. The need for sustainable and efficient weed management  has  driven  the  development  of site-specific  weed  management (SSWM). This approach involves precise  application of herbicides only in weed-infested areas,  minimizing herbicide usage and environmental impact [4].  Early attempts at automated weed detection relied on

The paper is structured as follows:

979-8-3315-3295-6/24/$31.00 ©2024 IEEE               1  DOI: 10.1109/ICDCC.2024.01

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:38:21 UTC from IEEE Xplore.  Restrictions apply.

In Section II, the literature survey reviews existing  research relevant to the topic under investigation, providing  an overview of the current state of knowledge in the field.  Section III details the proposed methodology and RU  architecture, accompanied by background knowledge and an  illustrative architectural diagram. Following this, Section IV  presents the experimental results obtained from the  evaluation of the RU Model. This section scrutinizes the  algorithm’s performance and presents results and findings  derived from the experimental analysis. Finally, Section V  serves as the conclusion section, summarizing the key  findings of our research

enhanced image super-resolution, underscoring the potential  of this approach for weed and crop segmentation tasks.

The effectiveness of different network architectures for  weed and crop segmentation has also been explored. Sa et al.  [15] introduced WeedMap, a large-scale semantic weed  mapping framework using aerial multispectral imaging and a  deep  neural  network.  Their  research  focused  on  distinguishing vegetation from soil, showcasing the  advantages of multispectral data in achieving precise  segmentation. Potena et al. [16] developed a multi-step  visual system for crop and weed classification using  RGB+NIR imagery. They employed two distinct CNN  architectures: a shallow one for vegetation detection and a  deeper one for distinguishing between crops and weeds.  Despite its effectiveness, the approach was limited by its pre-  segmentation step, making it unsuitable for handling heavily  overlapping plants, a common scenario in many agricultural  settings.

II. LITERATURE SURVEY

The past few years have seen a surge in research on  lever- aging deep learning for weed and crop segmentation,  driven by the demand for precise, automated solutions in  agriculture. CNNs have proven remarkably effective in  image processing, offering significant advantages. Modern  deep learning models go beyond basic segmentation by  incorporating sophisticated mechanisms to enhance their  performance. For example, Khan et al. [11] introduced a  novel  encoder-decoder  framework  for  weed-crop  segmentation in drone images. They recognized the  limitations and drawbacks of the existing U-Net and FCN-  based models in handling multi-scale variations and  capturing contextual information. Their proposed encoder  combines a Dense-inception network with the Atrous spatial  pyramid pooling module to extract multi-scale features and  incorporate global and local contextual details. The decoder,  equipped with deconvolution layers and attention units  (CnSAUs), effectively recovers spatial information and  enhances the localization of crops and weeds.

To address the issue of data limitations, Wendel and  Underwood [17] presented a method for generating training  data for self-supervised weed detection using a multi-spectral  line scanner. They mounted on a field robot, followed by  vegetation segmentation and crop-row detection. Pixels  within the crop rows were labelled as crops, while the  remaining pixels were labelled as weeds. This self- supervised approach offered a viable solution for reducing  reliance on manually labelled data, potentially simplifying  the deployment of deep learning models for weed detection.  Hall et al. [18] conducted a comprehensive evaluation of  different features for leaf classification, comparing the  performance of handcrafted and CNN features. They  concluded that CNN features significantly contributed to the  robustness and generalization of the classifier in challenging  real-world conditions. These studies demonstrate the  growing interest and success in utilizing deep learning for  weed and crop segmentation. Ongoing research continues to  explore more sophisticated architectures, innovative training  strategies, and efficient data utilization methods to further  refine the accuracy, speed, and robustness of these solutions,  paving the way for wider adoption in precision agriculture

Milioto et al. [12] addressed the challenge of real-time  semantic segmentation in sugar beet fields by proposing a  CNN-based  system.  Their  research  highlighted  the  difficulties in generalizing CNN classifiers to new fields due  to variations in lighting, soil, and weather conditions. To  overcome this, they incorporated knowledge of task-relevant  background into the network to expedite training. Their  system’s efficacy was demonstrated on a real agricultural  robot operating across different fields, showing potential for  online operation in diverse environments. Haug et al. [13]  presented a method for differentiating carrot from weeds  using RGB and NIR images, achieving an average accuracy  of 94% on a dataset of 70 images, demonstrating CNNs’  effectiveness for finer-grained plant classification tasks.

III. RESNET-UNET (RU MODEL)

In this section, we introduce the proposed methodology,  ResNet-Unet (RU Model), designed to achieve precision in  crop and weed segmentation. In the subsequent sections, we  delve into the background information, architectural design,  and process flow of RU, providing a comprehensive under-  standing of its implementation and functionality.  A. Background

Recent advancements also include incorporation of  attention  mechanisms  into  segmentation  networks,  enhancing accuracy by focusing on the most relevant image  regions. Hu et al. [14] proposed a Channel-wise and Spatial  Feature Modulation Net- work (CSFMN) for single image  super-resolution, employing a parallel combination of  channel and spatial attention units. This strategy allows for  concurrent  learning  of  spatial  and  channel-wise  dependencies, resulting in more comprehensive feature  representation. Their work demonstrated the benefits of  parallel attention in capturing intricate visual patterns for

In recent years, CNNs have exhibited remarkable  performance in various computer vision tasks, including  image segmentation. Among these architectures, ResNet- Unet has gained significant attention for its ability to  effectively segment objects in images with high accuracy and  efficiency.

1) Residual Networks (ResNet)

2

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:38:21 UTC from IEEE Xplore.  Restrictions apply.

ResNet, introduced by He et al [19], addresses the  degradation problem encountered in deep neural networks,  where adding more layers deteriorates the performance. The  core idea behind ResNet is the introduction of skip  connections, also known as residual connections, which  enable the gradient to flow directly through the network.  This architecture consists of residual blocks that facilitate  the learning of residual functions.

- Ui represents the feature map output of the i-th  upsampling convolutional layer in the decoder. - Ci  represents the concatenated feature map of the i-th decoder  layer with the corresponding feature map from the encoder  (Hn−i). The final segmentation map S is obtained by  applying a convolutional layer with softmax activation at  the end of the decoder.

3)  ResNet-Unet Architecture  The ResNet-Unet architecture combines the strengths of  both ResNet and Unet. By replacing the plain convolutional  layers in the encoder of Unet with residual blocks from  ResNet,  ResNet-Unet  enhances  feature  extraction  capabilities and facilitates the training of deeper networks.

In ResNet, L represents the total number of layers, and x  denotes the input to a residual block. The output of the l-th  residual block, denoted as Ft(x), is obtained by passing the  input x through a series of convolutional layers with  nonlinear activation functions, followed by the addition of  the input

In ResNet-Unet, let Hl represent the output of the l-th  residual block in the encoder, and Gl denote the output of  the corresponding decoder block. The skip connection  between the encoder and decoder layers is established by  concatenating Hl with Gl, enabling the decoder to leverage  rich hierarchical features extracted by the encoder. Weed  and crop segmentation require distinguishing similar plant  structures using accurate location and complex feature  extraction. Traditional UNet architectures excel in this due  to their skip connections, preserving fine features during up-  sampling. However, UNet struggles to learn intricate  features needed for differentiating plant species due to its  shallowness. Conversely, ResNet architectures, with their  deep networks and residual blocks, excel in feature  extraction but lose spatial resolution due to extensive  downsampling, making them less suitable for tasks  requiring  precise  localization.  The  ResNet-  UNet  architecture combines the strengths of both. ResNet serves  as the encoder for complex feature extraction, while UNet’s  decoder, with skip connections, preserves spatial in-  formation.  This  hybrid  approach  ensures  precise  segmentation by maintaining localization and mitigating  ResNet’s spatial resolution loss.

Fl(x) = x + 𝓕(x)     (1)  Here, 𝓕(x) represents the residual mapping learned  by the convolutional layers. The skip connection ensures  that the gradient can propagate through the network  effectively, alleviating the vanishing gradient problem and  enabling the training of deeper networks.

In ResNet, the output of the l-th residual block,  denoted as Hl, is computed as follows:

Hl  =  Fl ( Hl-1  ) + Hl-1    (2)  Where Hl-1 is the input to the l-th residual block. –  Fl (·) represents the residual mapping learned by the  convolutional layers within the l-th residual block.

2) Unet Architecture  Unet, proposed by Ronneberger et al [20], is a popular  architecture for semantic segmentation tasks. It consists of  an encoder-decoder structure with skip connections between  corresponding encoder and decoder layers. The encoder  extracts hierarchical features from the input image, while  the decoder generates a segmentation map using the features  obtained by the encoder.

The encoder of Unet downsamples the input image  through successive convolutional and pooling layers to  capture context and spatial information. Conversely, the  decoder upsamples the feature maps to generate the final  segmentation map. Skip connections concatenate feature  maps from the encoder with those from the decoder,  allowing the decoder to access low- level details captured by  the encoder.

B. RU Architecture

In our image segmentation task, we preprocess the  dataset, which includes images of size 5472x3648 pixels, by  resizing them to a manageable size of 256x256 pixels. To  enhance the diversity of the training dataset and improve the  robustness of the model, we employ various data  augmentation techniques, including horizontal and vertical  flips and random rotations. The architecture of our model is  visually explained in Figure 1.

In Unet, the encoder-decoder structure with skip  connections can be represented mathematically as follows:

Hi = Conv_ReLU( Hi-1 )    (3)  Pi = MaxPool( Hi )      (4)  Where:  - Hi represents the feature map output of the ith  convolutional layer in the encoder. – Pi represents the  feature map output of the ith pooling layer in the encoder.

During the encoder stage, the preprocessed 256x256  input image is fed through a ResNet-50 backbone, which  comprises a series of residual blocks. Each residual block  includes convolutional layers with a stride of two, which  reduce the spatial dimensions of the feature maps while  increasing  their  channel  count.  Initially,  the  first  convolutional layer processes the input image using three  channels (e.g., RGB), producing feature maps with 64  channels that typically measure 128x128. As the image

Ui  = UpConv_ReLU( Ui-1 )    (5)  Ci  = Concatenate( Ui, Hn-I )    (6)  Where:

3

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:38:21 UTC from IEEE Xplore.  Restrictions apply.

progresses through the encoder, the number of channels may  increase further, capturing more intricate details.

depicted in the encoder section, ensures that the  downsampling process captures increasingly complex  features at every stage. For instance, the feature maps  evolve from 256x256x64 at the initial stage to 128x128x128  and further to 64x64x256 as they pass through subsequent  residual  blocks,  progressively  reducing  the  spatial  dimensions while increasing the depth of the features.

For example, after passing through several residual  blocks, the feature maps may be reduced to 16x16 in size  and have 2048 channels. This hierarchical approach allows  the model to extract features at multiple scales, essential for  accurate image segmentation.

The UNet decoder is employed during the decoder stage  to upsample and segment the encoded feature maps. The  decoder comprises transpose convolutional layers, also  known as deconvolutional layers, which increase the spatial  dimensions of the feature maps. To concatenate feature  maps from corresponding encoder layers at each stage of the  decoder, skip connections are used allowing the model to  access both high-level and low-level features. For instance,  the encoder’s 16x16 feature maps with 2048 channels are  concatenated with the decoder’s feature maps to maintain  spatial dimensions and channel counts during the  upsampling process. Subsequent convolutional layers  further refine the feature maps to produce the final  segmentation map, which classifies the input image pixel- by-pixel into different categories.

In the decoder stage, the UNet architecture focuses on  the upsampling process. This involves using transpose  convolu- tions to increase the spatial dimensions of the  feature maps. The skip connections play a crucial role by  concatenating the feature maps from the encoder to the  corresponding layers in the decoder, thus retaining both  high-resolution and semantic information. For example, the  16x16x2048  feature  maps  from  the  encoder  are  concatenated with the decoder’s feature maps to ensure that  both fine and coarse details are preserved during  upsampling. The subsequent convolutional layers then  refine these feature maps, producing a final segmentation  map that classifies each pixel in the input image into  specific categories.

To further enhance image contrast and quality, advanced

Fig. 1. Proposed RU Model Architecture.

The model architecture leverages the strengths of both  ResNet-50 and UNet. ResNet-50, with its deep residual  learning framework, facilitates the learning of complex  features by utilizing identity mappings that add shortcut  connections to the convolutional layers. This structure helps  in mitigating the vanishing gradient problem and allows the  training of very deep networks. The ResNet-50 backbone, as

preprocessing techniques such as Contrast Limited Adaptive  Histogram Equalization (CLAHE) and gamma correction  are utilized. CLAHE improves the local contrast of the  image, making features more distinct, while gamma  correction adjusts the luminance of the image to enhance  visibility. Following these preprocessing steps, basic  operations like normalization and resizing are applied to  prepare the images for input into the model. This ensures

4

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:38:21 UTC from IEEE Xplore.  Restrictions apply.

that the input images are standardized, facilitating efficient  training and inference.

images. The UNet with ResNet-50 architecture was  evaluated using a four-fold cross-validation strategy. The  best-performing hyperparameter combination for this  architecture, determined by averaging the Sørensen-Dice  Coefficient (DS) across all validation sets, resulted in a DS  of 0.929 with a standard deviation of 0.0041.

In summary, the combination of UNet’s segmentation  and  upsampling  capabilities  with  ResNet-50’s  downsampling capabilities allows our model to effectively  capture both small features and the global context within the  input images. This integrated approach ensures reliable and  accurate image segmentation across various applications,  providing detailed and contextually aware segmentation  results. The architecture, as depicted in Figure 1,  demonstrates the flow of data through the encoder-decoder  structure with skip connections and up- sampling layers,  highlighting the synergy between ResNet-50 and UNet in  achieving high-performance image segmentation.

TABLE I. CLASSIFICATION METRICS

Class  Precision  Recall  F1-Score  Support

Background  99.80  99.92  99.86  137,909,280

Sorghum  91.58  86.10  88.76  1,249,145

Weed  87.64  72.71  79.48  574,567

IV. EXPERIMENTAL RESULTS

Macro avg  93.01  86.25  89.37  139,732,992

In this section, we provide an in-depth analysis of  the experimental results stemming from our proposed  methodology applied to the selected dataset. Our  investigation encompasses various performance metrics,  including precision, recall, and F1-score, alongside  qualitative assessments through visualizations of ground  truth and predicted masks. Through rigorous testing on  distinct subsets, such as training, testing, and validation sets,  we gain valuable insights into the segmentation model’s  efficacy in distinguishing weeds from sorghum plants in  UAV imagery. Additionally, we discuss the model’s adapt-  ability to diverse growth stages and environmental  conditions, offering a comprehensive understanding of its  performance across different scenarios.

Weighted avg  99.68  99.69  99.68  139,732.,992


> **Table 1 presents classification metrics for three classes:**

> Background, Sorghum, and Weed. Precision, recall, and F1- 
Score values indicate high performance, especially in the 
Background class. The macro and weighted averages demon- 
strate overall effectiveness, with precision, recall, and F1- 
Score ranging from 93.01% to 99.68%. These metrics affirm 
the model’s accuracy in classifying instances across diverse 
classes

Fig. 2 showcases qualitative results on the hold-out test  set. Different classes, including Weed (W) in orange,  Background (BG) in gray, and Sorghum (S) in blue are  visualized. Difference map is used for Misclassifications  between prediction and ground truth. Figure 4 represents the  confusion matrix representing the three classes Background,  Weed and Sorghum.

V. DATASET  The dataset1 utilized in this study comprises images  obtained from an unmanned aerial vehicle (UAV) survey  con- ducted over an experimental sorghum field located in  Southern Germany. The field was planted with the sorghum  variety ”Farmsughro 180,” with a row spacing of 37.5 cm  and a seeding density of 25 seeds per m², at the BBCH  growth stage 17. Throughout the image acquisition process,  the field exhibited various weed species, predominantly di-  cotyledons,  including  Cotton  thistle  (Onopordum  acanthium), Goosefoot (Chenopodium album L.), Wild  chamomile (Matricaria chamomilla), Field pennycress  (Thlaspi arvense), and Common gypsyweed (Veronica  officinalis). The images are of 5472 x 3648 pixels resolution  captured by a DJI Mavic 2 Pro consumer-grade drone  equipped with a 20 MP Hasselblad camera (L1D-20c) is  employed for data collection from a height of 5 meters from  the surface. The UAV executed automated flights with the  camera positioned directly downward (nadir) and a capture  overlap of ten percent.

In our study, we employed an additional two test datasets  II denoting different stages in the growth of sorghum plants.  The first dataset, test_1, represents an early growth stage  characterized by the emergence and full development of the  fifth leaf. Conversely, the second dataset, test_2, signifies a  more advanced stage with nine or more fully developed  leaves and a substantially larger leaf area. These datasets  facilitate the analysis and comparison of sorghum growth  dynamics across various developmental phases, offering  valuable insights into plant growth and development. Figure  2 and 3 represents the results generated from R-Net Model  from test_1 and test_2 respectively.

TABLE II. SUMMARY STATISTICS OF THE ADDITIONAL TEST SET USED

Test set  Patches  Sorghum  Weed

test_1  110  115  429

test_2  110  99  88.76

VI. RESULTS  This section presents the performance achieved by the  Unet architecture using a ResNet-50 feature extractor for  segmenting weeds from sorghum plants and soil in UAV

The model’s main drawback was its tendency to predict  sorghum plants as weeds for test_1. This misclassification

5

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:38:21 UTC from IEEE Xplore.  Restrictions apply.

might be attributed to the morphological changes during  growth (i.e., more leaves were present in test_1 compared to  test_2). In most cases, only parts of the plant were  misclassified; however, occasionally, entire sorghum plants  were predicted as weeds.

VII. DISCUSSION  Sodjinou et al. [21] tackled the challenge of segmenting  crops and weeds in complex agronomic images using a  combination of semantic segmentation and K-means  clustering. They employed a U-Net architecture for  semantic segmentation and a subtractive clustering  algorithm for K-means, achieving a high accuracy of  99.19%. The study focused on single-plant images,  achieving clean and precise segmentation, particularly in  scenarios where crops and weeds were visually similar.

Similarly, You et al. [22] developed a DNN-based  semantic segmentation model for detecting weeds and  crops, aiming to support autonomous robots in weed  removal. They enhanced a Res50 backbone network with  hybrid dilated convolutions, DropBlock regularization, and  a novel universal function approximation block for  generating color-based indices. Notably, they incorporated a  bridge attention block to capture long- range contextual  information and a spatial pyramid refinement block for  multi-scale feature fusion. Their approach achieved state-of- the-art performance on both the Bonn and Stuttgart datasets,  exceeding other prominent DNN architectures.

In contrast to these studies, our research focused on  segmenting weeds from sorghum plants and soil in UAV  images. We employed a Unet with a ResNet-50 feature  extractor, evaluating its performance using a four-fold  cross-validation strategy. Our model achieved a Sørensen- Dice coefficient of 0.929, with high precision, recall, and  F1-score values across all classes. Interestingly, our model  demonstrated robustness to variations in illumination and  could accurately predict weeds even in more advanced  stages of sorghum growth where the weed size exceeded  that of the training data.

Fig. 4. Normalized Confusion matrix representing the respective  classes Background, Sorghum and Weed

The model accurately predicted the overall distribution of  the weeds and the shape of large weeds. Sorghum was  predicted as few portions of weeds. In the case of test_2, the  model accurately predicted weeds, even though they had  grown larger than the weeds in the training data. Notably,  ”old weeds” that had grown significantly larger were also  mostly predicted correctly, as shown in Figure 3.

However, our model did exhibit a tendency to  misclassify sorghum plants as weeds in early growth stages,  potentially due to morphological similarities. This suggests  an area for future improvement, possibly by incorporating  growth stage- specific features or refining the model’s  ability to distinguish subtle morphological differences.  Despite this limitation, our approach offers a valuable  contribution to the field of weed detection, particularly in  the context of sorghum cultivation using UAV imagery.

TABLE III. MACRO-AVERAGED RESULTS GENERATED FROM USED

TEST SETS USING RESNET-UNET MODEL

Test set  Accuracy  Precision  Recall  Support

test_1  (Early  stage  crop  growth)

0.9900363  0.884283  0.820867  0.850646

test_2  (Advanced  stage  crop  growth)

0.978746  0.854367  0.841024  0.844189

VIII.  CONCLUSION

This work highlights the great potential of the  ResNet- Unet architecture for automated UAV imagery- based weed detection in sorghum fields. The model  effectively separates weeds from crops, as evidenced by its  high Sørensen-Dice Coefficient (DS) of 0.929 and standard  deviation of 0.0041. Furthermore, classification measures  support the effectiveness of the model even more; among  background, sorghum, and weed classifications, precision,  recall, and F1-score range from 93.01% to 99.68%. Future  research directions also include developing real-time weed  control systems that take advantage of the segmentation  capabilities of the proposed architecture, investigating the

These artifacts appear when a single plant is split up into  several patches, leaving little plant fragments on the edges of  the patches. As seen in Figure 2, these tiny portions were  incorrectly anticipated, as shown by the yellow shading.  Lastly, the illumination settings used to acquire the photos of  test_1 and test_2 differed from those used to capture the  training data. Interestingly, the model maintained its ability  to predict weeds in these images with high precision,  suggesting potential applicability to images with varying  quality.

6

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:38:21 UTC from IEEE Xplore.  Restrictions apply.

[11] SD Khan, S Basalamah, and A Lbath. Weed–crop segmentation in

effects of varying UAV picture resolutions, and expanding  the model’s applicability to additional crop types.

drone images with a novel encoder–decoder framework enhanced  via attention modules. Remote Sensing, 15(23):5615, 2023.   [12] A Milioto, P Lottes, and C Stachniss. Real-time semantic


## REFERENCES

segmentation of crop and weed for precision agriculture robots  leveraging background knowledge in cnns. In 2018 IEEE  International Conference on Robotics and Automation (ICRA),  pages 2229–2235. IEEE, 2018.   [13] H. Huang, Y. Lan, J. Deng, A. Yang, X. Deng, L. Zhang, et al.

[1]  A. M. Hasan, F. Sohel, D. Diepeveen, H. Laga, and M. G. Jones.  A survey of deep learning techniques for weed detection from  images. Computers and Electronics in Agriculture, 184:106067,  2021.   [2]  A. Wang, W. Zhang, and X. Wei. A review on weed detection  using ground-based machine vision and image processing  techniques. Computers and Electronics in Agriculture, 158:226– 240, 2019.   [3]  I. Rakhmatulin, A. Kamilaris, and C. Andreasen. Deep neural  networks to detect weeds from crops in agricultural environments  in real-time: a review. Remote Sensing, 13(21):4486, 2021.   [4]  H. G. Jensen, L. B. Jacobsen, S. M. Pedersen, and E. Tavella. So-  cioeconomic impact of widespread adoption of precision farming  and controlled traffic systems in denmark. Precision Agriculture,  13(6):661– 677, 2012.   [5]  A. J. Ishak, M. M. Mustafa, N. M. Tahir, and A. Hussain. Weed  detection system using support vector machine. In 2008  International Symposium on Information Theory and Its  Applications, pages 1–4. IEEE, December 2008.   [6]  Z. Wu, Y. Chen, B. Zhao, X. Kang, and Y. Ding. Review of weed  detection  methods  based  on  computer  vision.  Sensors,  21(11):3647, 2021.   [7]  L. C. Chen, G. Papandreou, F. Schroff, and H. Adam. Rethinking  atrous convolution for semantic image segmentation. arXiv  preprint arXiv:1706.05587, 2017.   [8]  K. Zou, X. Chen, Y. Wang, C. Zhang, and F. Zhang. A modified  u-net with a specific data argumentation method for semantic  segmentation of weed images in the field. Computers and  Electronics in Agriculture, 187:106242, 2021.   [9]  Lamkuche, H. S., Pramod, D., Onker, V., Katiya, S. A.,  Lamkuche, G. S., & Hiremath, G. R. (2019). SAL–a lightweight  symmetric cipher for Internet of Things. Int. J. Innov. Technol.  Explor. Eng, 8(11), 521-528..   [10] Lamkuche, H. S., Kondaveety, V. B., Sapparam, V. L., Singh, S.,

Accurate weed mapping and prescription map generation based on  fully convolutional networks using uav imagery. Sensors,  18(10):3299, 2018.   [14] Y Hu, J Li, Y Huang, and X Gao. Channel-wise and spatial feature

modulation network for single image super-resolution. IEEE  Transac- tions on Circuits and Systems for Video Technology,  30(11):3911–3927, 2020.   [15] I Sa, M Popovi´c, R Khanna, Z Chen, P Lottes, F Liebisch, and R

Siegwart. Weedmap: a large-scale semantic weed mapping  framework using aerial multispectral imaging and deep neural  network for precision farming. Remote Sensing, 10(9):1423, 2018.   [16] C Potena, D Nardi, and A Pretto. Fast and accurate crop and weed

identification with summarized train sets for precision agriculture.  In International Conference on Intelligent Autonomous Systems,  pages 105–121. Springer, 2016.   [17] Lamkuche, H. S., & Pramod, D. (2020). CSL: FPGA

implementation of lightweight block cipher for power-constrained  devices. International Journal of Information and Computer  Security, 12(2-3), 349-377..   [18] D Hall, CS McCool, F Dayoub, N Sunderhauf, and B Upcroft.

Eval- uation of features for leaf classification in challenging  conditions. In Proceedings of the IEEE Winter Conference on  Applications of Computer Vision, pages 797–804, 2015.   [19] Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun. Deep

residual learning for image recognition. pages 770–778, 06 2016.   [20] Olaf Ronneberger, Philipp Fischer, and Thomas Brox. U-net:

Convolutional networks for biomedical image segmentation.  volume 9351, pages 234–241, 10 2015.   [21] S. G. Sodjinou, V. Mohammadi, A. T. S. Mahama, and P. Gouton.

A deep semantic segmentation-based algorithm to segment crops  and weeds in agronomic color images. Information Processing in  Agriculture, 9:355– 364, 2022.   [22] J. You, W. Liu, and J. Lee. A dnn-based semantic segmentation

& Rajpurkar, R. D. (2022). Enhancing the security and  performance of cloud for e-governance infrastructure: Secure E- MODI. International Journal of Cloud Applications and  Computing (IJCAC), 12(1), 1-23.

for detecting weed and crop. Computers and Electronics in  Agriculture, 178:105750, 2020.

7

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:38:21 UTC from IEEE Xplore.  Restrictions apply.

2

Fig. 2. Segmentation results showing 4 ground patch image and its respective ground truth mask, prediction mask and difference of ground truth mask and

prediction mask generated test_1                                                      Fig. 3. Segmentation results showing 4 ground patch image and its respective ground truth mask, prediction mask and difference of ground truth mask and

prediction mask generated test_

8

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:38:21 UTC from IEEE Xplore.  Restrictions apply.
