---
workspace_id: SCI-000271
doi: 10.1109/lgrs.2024.3358983
title: Crop Segmentation of Unmanned Aerial Vehicle Imagery Using Edge Enhancement
  Network
authors:
- family_name: Li
  given_name: Jinwen
  orcid: https://orcid.org/0009-0009-6411-9805
- family_name: Pu
  given_name: Fangling
  orcid: https://orcid.org/0000-0002-1490-0347
- family_name: Chen
  given_name: Hongjia
  orcid: https://orcid.org/0000-0001-5294-4386
- family_name: Xu
  given_name: Xin
  orcid: https://orcid.org/0000-0001-9211-6606
- family_name: Yu
  given_name: Yao
  orcid: https://orcid.org/0009-0007-5077-0344
year: 2024
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:40.875940+00:00'
---

# Crop Segmentation of Unmanned Aerial Vehicle Imagery Using Edge Enhancement Network

IEEE GEOSCIENCE AND REMOTE SENSING LETTERS, VOL. 21, 2024 6003805

Crop Segmentation of Unmanned Aerial Vehicle

Imagery Using Edge Enhancement Network

Jinwen Li , Fangling Pu , Member, IEEE, Hongjia Chen , Xin Xu , and Yao Yu

SVM to recognize the plastic mulched farmland from UAV images. The results showed that SegNet achieved the highest average accuracy among the three methods. However, SegNet lacks context information that leads to problems in spatial consistency [5] which refers to the likeness or continuity of the content within different regions of the image. U-Net [6] was proposed to fuse low-level features which comprise basic image attributes like shape and texture with high-level features which are more abstract and complex image recognizable features by skip-connections. U-Net has achieved better per- formance in the field of general-purpose segmentation and is widely used as a baseline. Wang et al. [7] used U-Net- based CNN to detect the degree of invasion of Solanum rostratum Dunal, achieving significant results. However, the continuous up-sampling fusion of U-Net may result in the loss of edge information [8], which refers to the specifics of boundaries or contours within the image. Additionally, the numerous convolutions, up-samplings, and skip-connections consume a large amount of computation and spent a longer time. PSPNet [9] used a feature pyramid module to obtain context information through multiscale feature fusion, and Yu et al. [10] used the improved PSPNet to achieve good results in detecting wheat inversion. Like U-Net, PSPNet consumed a large quantity of computing and storage resources because of a large number of model parameters. Although the proposed methods continuously improve the segmentation accuracy, precise edge segmentation remains a challenge when the proposed methods are applied to crop segmentation. Addi- tionally, reducing the number of model parameters is also a metric that needs to be taken into account with the aim of efficiency enhancement.


## Abstract— Crop segmentation enables agricultural producers

to comprehensively understand the state of their farmland,
make more informed management decisions and thereby ensure
food security. Unmanned aerial vehicle (UAV) remote sensing
technology offers cost-effective high-resolution imaging for crop
segmentation. Deep learning-based methods have continued to
improve the accuracy of crop segmentation over time, but
accurate edge segmentation remains a challenge. In this letter,
we introduce a convolutional neural network (CNN) termed edge
enhancement network (EENet) to improve the representation of
edge information for crop segmentation in UAV RGB images.
Our approach centers on an innovative edge enhancement (EE)
Strategy that augments the learning of edge information during
the training phase and refines the representation of edge details
during the generation phase. To facilitate the evaluation of our
method, we have produced a publicly available dataset for exper-
imentation. Our results, as demonstrated on this self-constructed
dataset, illustrate that our proposed approach surpasses compet-
ing methods in critical metrics such as mean intersection over
union (mIoU), F1_score, and model complexity.

Index Terms— Crop segmentation, edge enhancement (EE), unmanned aerial vehicle (UAV) RGB images.

I. INTRODUCTION U

NMANNED aerial vehicle (UAV) remote sensing tech- nology has the potential to significantly enhance crop segmentation, leading to more efficient and sustainable agri- cultural practices. It offers a wide range of advantages that include low cost, real-time data acquisition, and high resolu- tion among others [1]. By harnessing UAV imagery for crop segmentation, agricultural producers can gain deeper insights into the state of their farmlands, empowering them to optimize land management strategies and safeguard food security.

Over the past few years, the field of UAV remote sens- ing image segmentation driven by deep learning has made remarkable strides, owing to the relentless evolution of seman- tic segmentation algorithms. Fully convolutional networks (FCNs) [2] is a pioneering work that has enabled accurate and efficient classification of individual pixels, contributing to improving crop segmentation. SegNet [3] is one of the earliest convolutional neural networks (CNNs) that use the encoder-decoder network structure to improve the segmen- tation capacity. Yang et al. [4] applied SegNet, FCN, and

To elevate the precision of crop segmentation while simul- taneously mitigating computational demands, we propose a segmentation network named edge enhancement network (EENet), which can draw attention to edge information and enhance it. Firstly, we propose a training strategy called edge enhancement (EE) Strategy, which induces the low-level feature maps of the EENet to interpret edge information through input and ground truth. As low-level features retain richer spatial information [11], it is beneficial to capture edge information. The EE Strategy is capable of enriching the edge information of output through Edge Enhancer. Second, inspired by U-Net’s skip-connections, we design Seman- tic Enhancer to generate prediction using high-level feature maps, because high-level features contain richer semantic information [11]. Unlike U-Nets skip-connections for each

Manuscript received 4 September 2023; revised 23 January 2024; accepted 23 January 2024. Date of publication 26 January 2024; date of current version 9 February 2024. This work was supported by the National Natural Science Foundation of China (General Program) under Grant 62271356. (Corresponding author: Fangling Pu.) The authors are with the Electronic Information School, Wuhan University, Wuhan 430079, China (e-mail: flpu@whu.edu.cn).

Digital Object Identifier 10.1109/LGRS.2024.3358983

1558-0571 © 2024 IEEE. Personal use is permitted, but republication/redistribution requires IEEE permission. See https://www.ieee.org/publications/rights/index.html for more information.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:38:50 UTC from IEEE Xplore.  Restrictions apply.

6003805 IEEE GEOSCIENCE AND REMOTE SENSING LETTERS, VOL. 21, 2024

Fig. 1. Architecture of the EENet. EE Strategy denotes edge enhancement Strategy, and FFM denotes features fusion module. The structure in the red dashed box is defined as Feature Extractor. Purple area operations only in the training phase.

corresponding encoder and decoder, which consume a large number of convolutional operations, we reduce the number of skip-connections and the number of convolutional layers to greatly reduce the number of model parameters while maintaining accuracy. Third, we produced a publicly available dataset that can be used for crop segmentation tasks, and categorized rice, sesame, corn, ground, and other (indistin- guishable and unknown plant species). We have conducted extensive experiments on the self-built dataset to verify the effectiveness of the method. EENet outperforms U-Net, Seg- Net, and PSPNet in mIoU, F1_score.

Fig. 2. Structure of BasicBlock.

II. PROPOSED METHOD

learning and information transfer, capturing essential features more effectively during encoding thanks to direct layer-to- layer communication.

A. General Architecture Overview

The proposed EENet architecture is shown in Fig. 1. We designed the Feature Extractor in terms of the residual structure [12] which is composed of a cascade of three kinds of blocks. Prediction generation includes Edge Enhancer, Semantic Enhancer, and features fusion module (FFM). The segmentation results are obtained after fusion and up-sampling by FFM.

Lower-level layers have a smaller receptive field and require more channels to encode finer details, higher-level layers have a larger receptive field and focus more on high-level abstract information. Setting the same number of channels for both lower- and higher-level layers may lead to redundant information. It is beneficial to concatenate feature maps from different levels [15] with different sizes, so that the feature information will be enriched and the understanding of the context will be enhanced.

B. Feature Extractor

Feature Extractor is employed to extract various information from the input image, ranging from low-level to high-level features, including one ConvBlock, one BasicBlock, and three DownBlocks. ConvBlock consists of three units. Each unit is composed of a convolution layer (stride = 2 is set for the first unit and third unit, while stride = 1 is set for the second unit), followed by batch normalization [13] and ReLU [14].

We designed BasicBlock as shown in Fig. 2. We represent a convolutional layer (stride = 1), followed by batch nor- malization and ReLU, as ConvS. The number indicates the size of the convolutional kernel. Input feature maps with N channels pass through ConvS with output channels N/2, N/4, and N/4, respectively. The feature maps outputted by ConvS are concatenated through skip-connections, resulting in feature maps with N channels. This process is repeated, and the final output of the BasicBlock is obtained by adding the N-channel feature maps with input feature maps.

In our design, we incorporated BasicBlock and Down- Block with a residual structure to enhance the network. This design enables more effective gradient flow, solving issues of vanishing or exploding gradients. It improves the network’s

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:38:50 UTC from IEEE Xplore.  Restrictions apply.

LI et al.: CROP SEGMENTATION OF UAV IMAGERY USING EDGE ENHANCEMENT NETWORK 6003805

Fig. 4. Structure of Edge Enhancer. The output feature maps for ConvBlock are shown in blue and BasicBlock is shown in green.

Fig. 3. Structure of DownBlock.

DownBlock is similar to BasicBlock in structure. As shown in Fig. 3, the difference between BasicBlock and DownBlock is that before the forward propagation and addition, the feature maps go through a ConvS with stride = 2, doubling the output channels to reduce the impact of information loss caused by the reduction in size. Apart from the change in size and channel number, the feature maps of DownBlock follow the same logic as BasicBlock for subsequent feature learning.

Fig. 5. Structure of Semantic Enhancer. The output feature maps for the third DownBlock is shown in blue, and the second DownBlock is shown in green.

C. EE Strategy

We propose EE Strategy to enhance the performance of Fea- ture Extractor. Feature Extractor captures low-level features brimming with spatial information. This kind of information has not received additional focus in the previously men- tioned methods, leading to a disadvantage in expressing edge information. EE Strategy can make better use of the edge information contained in the low-level features to enhance the edge representation in the result.

In the training phase, we employ original and labeled edge maps to capture edge details. We convert input RGB images to gray scale and apply the Laplace operator to extract a detailed feature map. To deal with any blurring from neighboring plants of different classes, we use the same process on the ground truth for clarity. We performed a fusion with weights of the detail feature maps generated by the two paths (using 0.1 as a threshold) to convert them into the final edge detail information map. Pseudo-boundary maps are generated from ConvBlock’s output, guiding the learning of spatial details in low-level layers. In the prediction phase, we engage our Edge Enhancer to intensify edge details, which is diagrammed in Fig. 4. The feature maps are averaged and maximized across different channels from ConvBlock, then concatenated with BasicBlock’s output as the output result.

Fig. 6. Structure of FFM.

layers, which drastically reduces the number of model param- eters.

Semantic Enhancer: The structure of the Edge Enhancer is shown in Fig. 5. The feature maps outputted from the third DownBlock are weighted by taking the average and maximum values of all points in the same channel, then up-sampled and concatenated with the output of the second DownBlock to obtain the output result.

FFM: Edge Enhancer output contains spatial features and edge information, while Semantic Enhancer output contains semantic features. As shown in Fig. 6, both the Edge Enhancers outputs and the Semantic Enhancers outputs are first concatenated, and the scale of the concatenated outputs are balanced by normalization, then pooling into a feature vector, the weight vector is calculated by global average pooling and global maximum pooling to reweight the inputs of FFM.

D. Prediction Generation

The role of Prediction Generation is to generate segmen- tation results, with the aim of using the Edge Enhancer and Semantic Enhancer to enhance the low-level features and high- level features extracted by the Feature Extractor, respectively. These features are then combined through the FFM, ensuring that the result incorporates both global and detailed features. Prediction Generation does not require skip-connections for each corresponding encoder and decoder, significantly reduces the number of skip-connections and subsequent convolutional

III. EXPERIMENTS A. Data

Our data are collected by the UAV on-board RGB camera at Dazhangjiatai, Shahu Town, Xiantao City, Hubei Province, China on July 11, 2019. The UAV flew at an altitude of 70 m

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:38:50 UTC from IEEE Xplore.  Restrictions apply.

6003805 IEEE GEOSCIENCE AND REMOTE SENSING LETTERS, VOL. 21, 2024

Fig. 7. Examples of segmentation results on self-built dataset. (a) Image. (b) Select area and Ground truth.

TABLE I

and a spatial resolution of 0.02017 m/pixel. The drone image size is 20954 × 22941, and the vast majority of the crops in the image are rice. We selected three plots as shown in Fig. 7 as the source of datasets. The images are segmented into five categories, which are rice, sesame, corn, ground, and others. After manually labeling the ground truth using LabelMe [16], we clip the size of the images of the selected regions to 224× 224. 877 images are used as the training set and 331 images as the test set.

PROPOSED METHOD AND THREE BASELINES FOR IOU, MIOU,

F1_SCORE FOR FIVE CATEGORIES

B. Network Training

The training selects Adam as the optimizer, using β1 = 0.9, β2 = 0.99. The initial learning rate is set to 0.001, the number of step_size is 20, and the learning rate adjustment factor is 0.8. The batch size is set to 8. Cross Entropy Loss Function is taken as the loss function. The sum of dice loss and cross entropy loss is the Edge Loss.

TABLE II PROPOSED METHOD AND THREE BASELINES

FOR PARAMETERS AND FLOPS

C. Experimental Results

To facilitate comparing with different methods, IoU and F1_score are employed as metrics in this letter.


> **Table I shows the quantitative results of our method and**

> that of the several network models proposed in the previous
paper. Our method is the best of all metrics. Fig. 8 shows the
visual segmentation results of several methods.

Our method utilizes learnable up-samplings which are different from SegNet to reduce information attrition; sup- plants U-Net’s simplistic constant up-sampling with a fusion of low-level and high-level features, enhancing the demar- cation of adjacent varied flora; uses EE Strategy to rein- force the representation of edge information, preventing the over-smoothing common in PSPNet, and thus more accurately emulates the verisimilitude of nature.

SegNet’s nonlearnable up-sampling process can result in poor performance in intricate scene segmentation, particularly failing to preserve fine details along edges; despite U-Net’s capacity for resolution restoration through its consecutive up-sampling, pivotal details can be compromised, making it difficult to segment edges with precision at times, especially when the edges of the object have a similar texture or color to others; the pyramid pooling operation of PSPNet, which employs average pooling at varying scales, may result in the loss of edge details, yielding overly smoothed, nonfine borders. These experimental results indicate shortcomings in protecting boundaries with these methods.


> **Table II shows the difference in model complexity between**

> proposed method and three baselines. We compared two
metrics that were computed using Parameters and floating
point operations (FLOPs). The Proposed method demonstrates
a significant advantage in both metrics, which means it is more
efficient than the others.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:38:50 UTC from IEEE Xplore.  Restrictions apply.

LI et al.: CROP SEGMENTATION OF UAV IMAGERY USING EDGE ENHANCEMENT NETWORK 6003805

segmentation than the presented baseline methods. The weighted low-level feature maps output by the edge enhancer retain rich spatial information, and the weighted high-level fea- ture maps output by the semantic enhancer have rich semantic information. FFM is utilized to generate segmentation results with protected edge information. Experiments have been con- ducted on a self-constructed dataset to demonstrate that the proposed EENet outperforms U-Net, SegNet, and PSPNet, and ablation experiments also show the computation effectiveness of the EE Strategy. Furthermore, we have achieved improved results in terms of comparatively low model complexity as well. In the future, We will add the input image with Laplace transform to assist in the prediction process of the network and enhance the network’s ability to utilize context information.


## REFERENCES

[1] W. H. Maes and K. Steppe, “Perspectives for remote sensing with

unmanned aerial vehicles in precision agriculture,” Trends Plant Sci., vol. 24, no. 2, pp. 152–164, Feb. 2019. [2] J. Long, E. Shelhamer, and T. Darrell, “Fully convolutional networks

for semantic segmentation,” in Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR), Jun. 2015, pp. 3431–3440. [3] V. Badrinarayanan, A. Kendall, and R. Cipolla, “SegNet: A deep

Fig. 8. Examples of segmentation results on self-built dataset. Leg- end—Green: Rice; Olive: Ground; Navy Blue: Sesame; Blue Green: Corn; Maroon: Other. From left to right: (a) Image. (b) Ground Truth. (c) SegNet. (d) U-Net. (e) PSPNet. (f) Ours.

convolutional encoder–decoder architecture for image segmentation,” IEEE Trans. Pattern Anal. Mach. Intell., vol. 39, no. 12, pp. 2481–2495, Dec. 2017. [4] Q. Yang, M. Liu, Z. Zhang, S. Yang, J. Ning, and W. Han, “Mapping

plastic mulched farmland for high resolution images of unmanned aerial vehicle using deep semantic segmentation,” Remote Sens., vol. 11, no. 17, p. 2008, Aug. 2019. [5] S. Huang, W. Han, H. Chen, G. Li, and J. Tang, “Recognizing zucchinis

intercropped with sunflowers in UAV visible images using an improved method based on OCRNet,” Remote Sens., vol. 13, no. 14, p. 2706, Jul. 2021. [6] O. Ronneberger, P. Fischer, and T. Brox, “U-Net: Convolutional net-

works for biomedical image segmentation,” in Proc. Int. Conf. Med. Image Comput. Comput.-Assist. Intervent. Cham, Switzerland: Springer, 2015, pp. 234–241. [7] Q. Wang et al., “An image segmentation method based on deep learning

for damage assessment of the invasive weed solanum rostratum dunal,” Comput. Electron. Agricult., vol. 188, Sep. 2021, Art. no. 106320. [8] Z. Xu, W. Zhang, T. Zhang, and J. Li, “HRCNet: High-resolution context

extraction network for semantic segmentation of remote sensing images,” Remote Sens., vol. 13, no. 1, p. 71, Dec. 2020. [9] H. Zhao, J. Shi, X. Qi, X. Wang, and J. Jia, “Pyramid scene parsing

Fig. 9. Examples of ablation experiment visualization display. From left to right: (a) Image. (b) Ground Truth. (c) Without EE Strategy. (d) With EE Strategy.

network,” in Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR), Jul. 2017, pp. 6230–6239. [10] J. Yu et al., “Wheat lodging segmentation based on Lstm_PSPNet deep

D. Ablation Study

learning network,” Drones, vol. 7, no. 2, p. 143, Feb. 2023. [11] M. D. Zeiler and R. Fergus, “Visualizing and understanding convolu-

The ablation experiments aim to verify the beneficial orientation of our proposed EE Strategy on the results. We per- formed a comparison of the results of two sets of images with distinct boundaries, as shown in Fig. 9. It can be seen that after utilizing EE Strategy, our method can clearly identify the existence of Edge. Statistical analysis shows that the mIoU is 0.8097 and the F1_score is 0.8778 without EE Strategy, and the mIoU is 0.8507 and the F1_score is 0.9088 when EE Strategy is used.

tional networks,” in Proc. Eur. Conf. Comput. Vis., Cham, Switzerland: Springer, 2014, pp. 818–833. [12] K. He, X. Zhang, S. Ren, and J. Sun, “Deep residual learning for

image recognition,” in Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR), Jun. 2016, pp. 770–778. [13] S. Ioffe and C. Szegedy, “Batch normalization: Accelerating deep

network training by reducing internal covariate shift,” in Proc. Int. Conf. Mach. Learn., 2015, pp. 448–456. [14] X. Glorot, A. Bordes, and Y. Bengio, “Deep sparse rectifier neu-

ral networks,” in Proc. 14th Int. Conf. Artif. Intell. Statist., 2011, pp. 315–323. [15] G. Huang, Z. Liu, L. Van Der Maaten, and K. Q. Weinberger, “Densely

IV. CONCLUSION

connected convolutional networks,” in Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR), Jul. 2017, pp. 2261–2269. [16] B. C. Russell, A. Torralba, K. P. Murphy, and W. T. Freeman, “LabelMe:

In this letter, we propose a segmentation network called EENet for crop segmentation on UAV images. The introduced EE Strategy can better perceive the edge information in the

A database and web-based tool for image annotation,” Int. J. Comput. Vis., vol. 77, nos. 1–3, pp. 157–173, May 2008.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:38:50 UTC from IEEE Xplore.  Restrictions apply.
