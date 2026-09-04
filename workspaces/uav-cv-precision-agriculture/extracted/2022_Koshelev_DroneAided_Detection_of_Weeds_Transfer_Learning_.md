---
workspace_id: SCI-000708
doi: 10.1109/jstars.2022.3224657
title: 'Drone-Aided Detection of Weeds: Transfer Learning for Embedded Image Processing'
authors:
- family_name: Koshelev
  given_name: Iaroslav
  orcid: null
- family_name: Savinov
  given_name: Maxim
  orcid: https://orcid.org/0000-0003-2000-5346
- family_name: Menshchikov
  given_name: Alexander
  orcid: https://orcid.org/0000-0003-2842-4414
- family_name: Somov
  given_name: Andrey
  orcid: https://orcid.org/0000-0002-4615-3008
year: 2022
extraction_engine: pymupdf
extracted_at: '2026-09-04T01:48:53.341222+00:00'
---

# Drone-Aided Detection of Weeds: Transfer Learning for Embedded Image Processing

102 IEEE JOURNAL OF SELECTED TOPICS IN APPLIED EARTH OBSERVATIONS AND REMOTE SENSING, VOL. 16, 2023

Drone-Aided Detection of Weeds: Transfer Learning

for Embedded Image Processing

Iaroslav Koshelev, Maxim Savinov, Alexander Menshchikov, and Andrey Somov

Eurasia region, including European and Asian countries, Great Britain, and Russia, as well as local parts of North American continent. Hogweed typically grows for up to 5 m and may have the diameter for up to 12 cm. It is capable of producing thousands of seeds, which are then distributed by wind across large area. The plant produces toxins, which are hazardous for human, but at the same time hogweed creates a danger to other crops including the farming ones by affecting their ecosystem. This hazardous weed must, therefore, be precisely identiﬁed and removed.


## Abstract—In this article, we address the problem of hogweed

detection using a drone equipped with red, green, blue (RGB)
and multispectral cameras. We study two approaches: 1) ofﬂine
detection running on the orthophoto of the area scanned within
the mission and 2) real-time scanning from the frame stream
directly on the edge device performing the ﬂight mission. We show
that by fusing the information from an additional multispectral
camera installed on the drone, there is an opportunity to boost the
detection quality, which can then be preserved even with a single
RGB camera setup by the introduction of an additional convolution
neural network trained with transfer learning to produce the fake
multispectral images directly from the RGB stream. We show that
this approach helps either eliminate the multispectral hardware
from the drone or, if only the RGB camera is at hand, boost
the segmentation performance by the cost of slight increase in
computational budget. To support this claim, we have performed an
extensive study of network performance in simulations of both the
real-timeandofﬂinemodes,whereweachieveatleast1.1%increase
in terms of the mean intersection over union metric when evaluated
on the RGB stream from the camera and 1.4% when evaluated on
orthophoto data. Our results show that the proper optimization
guarantees a complete elimination of the multispectral camera
from the ﬂight mission by adding a preprocessing stage to the
segmentation network without the loss of quality.

Traditionally, there are three typical approaches for weed localization: 1) inspection by human; 2) satellite imaging; and 3) unmanned aerial vehicle (UAV) monitoring. We discuss these approaches in Section II.

In this article, we rely on the UAV option due to its practical feasibility. The most commonly utilized sensor setup for this platform consists of a single video camera, capable of producing high-quality red, green, blue (RGB) images and a global naviga- tion satellite system sensor providing geographic coordinates for the measurements from the camera. An additional multispectral camera is also typically introduced for the crop monitoring missions to allow for a computation of vegetation indices. The same sensor could also be utilized to increase the crop detection accuracy, as it was shown, for example, in [2], but exploiting two video cameras on board is not weight and cost wise.

Index Terms—Deep learning, edge computing, semantic segmentation, transfer learning.

I. INTRODUCTION C

ONTINUOUSLY growing human population imposes strict demands to agricultural industry in terms of improv- ing the crop yields and making the food production efﬁcient. At the same time, high efﬁciency can be achieved by controlling and removing the weeds. To overcome this challenge, a high number of state-of-the-art technologies have been applied in the scope of precision agriculture (PA) [1].

In this article, we investigate the tradeoffs between the se- mantic segmentation quality of crops and the imaging sensor setup complexity. We use a task of hogweed detection as a playground and propose a solution based on the advances of deep learning, which allows for the complete avoidance of a multispectral camera from the mission without any deterioration of segmentation performance compared to the multiple-camera platform. More speciﬁcally, we report on the following novelty.

The distribution of weeds and, in particular, Hogweed of Sosnowsky, is a quickly growing problem for agricultural in- dustry. Hogweed of Sosnowsky is a weed that has spread across

1) Dataset collection, alignment, and labeling: We propose to label the hogweed plants by transforming a sequence of overlapping frames into a single orthophoto. It enables labeling the crops in the area of interest only once without repetition in intersecting parts of the images. The corre- sponding labels are then back-transformed to the camera frames using a greedy-feature-based image alignment pro- cedure. A similar procedure is applied to align the RGB and multispectral data, with the corresponding orthopho- tos acting as a reference. As a result, in our approach, the labeled and aligned RGB and multispectral images are produced fast without a need to synchronize frame streams coming from two separate camera sensors. To the best

Manuscript received 7 July 2022; revised 21 September 2022; accepted 20 November 2022. Date of publication 24 November 2022; date of current version 7 December 2022. (Corresponding author: Andrey Somov.) Iaroslav Koshelev and Andrey Somov are with the Skolkovo Institute of Science and Technology, 121205 Moscow, Russia (e-mail: iaroslav. koshelev@skoltech.ru; a.somov@skoltech.ru).

Maxim Savinov was with the Skolkovo Institute of Science and Technology, 121205 Moscow, Russia. He is now with the Saint Petersburg State Univer- sity of Aerospace Instrumentation, 190000 Saint Petersburg, Russia (e-mail: maxim.savinov@skoltech.ru).

Alexander Menshchikov was with the Skolkovo Institute of Science and Technology, 121205 Moscow, Russia. He is now with the Rakuten, Tokyo 158-0094, Japan (e-mail: alexander.menshchikov@skolkovotech.ru). Digital Object Identiﬁer 10.1109/JSTARS.2022.3224657

This work is licensed under a Creative Commons Attribution 4.0 License. For more information, see https://creativecommons.org/licenses/by/4.0/

KOSHELEV et al.: DRONE-AIDED DETECTION OF WEEDS: TRANSFER LEARNING FOR EMBEDDED IMAGE PROCESSING 103

of our knowledge, such methodology was never reported before. 2) Removal of the multispectral camera from the setup by replacement with the preprocessing network: Instead of using the two-camera setup, we propose to adopt a transfer learning procedure and learn a convolution neural network (CNN) from the collected paired data to mimic multispec- tral images. Such images are then synthesized during the preprocessing stage, which allows us to completely avoid multispectral hardware in the aerial platform without any deterioration of segmentation quality. The rest of this article is organized as follows. We introduce the readers to the relevant works in the area in Section II. In Section III, we discuss the methods used in this research. Our results are provided in Section IV. Finally, Section V concludes this article.

cameras enable crop monitoring with much greater precision as well as direct calculation of their vegetation characteristics. This is done at a cost of additional hardware carried on board during the mission, and additional efforts for accurate sensor synchronization and image alignment.

B. Image Analysis in PA

Even before the raise of deep learning, many algorithms were proposed to perform a high-level vision of the images. Most of them rely on handcrafted distinct features of the object of interest, and it was shown that this principle is suitable for the agriculture as well [5]. Now, almost all the state-of-the-art approaches involve the usage of CNNs and even transformers. Ronneberger et al. [6] were one of the pioneers who introduced a U-shaped neural architecture for the task of image segmen- tation, which is still applied in real high-level vision tasks. This architecture was shown to produce state-of-the-art results in agricultural tasks as well and being capable to run on the edge device. For example, in [7], U-shaped architecture was deployed to the unmanned ground vehicle (UGV) in order to perform a robust estimate a pixelwise labeling of the images into crop and weed. It was shown that this setup outperforms previous state-of-the-art approaches and improves the accuracy of crop–weed classiﬁcation without requiring a retraining of the model. Menshchikov et al. [8] reported on a comparison between other segmentation CNNs, which showed that U-Net performance is slightly lower than the competing SegNet and ReﬁneNet with ResNet backbone. However, the computational complexity of the latter two models does not allow for deploying them to an embedded unit and perform the inference in real time during the mission.

II. RELATED WORK

A. Weed Detection

Traditional approaches of weed localization include manual inspection with special handheld equipment, which is done either by foot or with the utilization of transport machines like cars or tractors [3]. Although these methods can still be in favor for farmers, there is a certain shift toward the systems allowing for the monitoring of larger areas while preventing the spread of seeds by feet and wheels. That is why the modern development of methods involving the UAVs and even satellites imaging starts to gain close attention for the purposes of more effective human-free ways of crop monitoring and weed control [4].

Currently, satellite imaging provides accurate images across huge areas with different spectral bands lying far beyond just conventional visual spectrum, provided by an ordinary RGB camera. However, satellite imaging still does not allow us to perform precise crop localization due to the large ground sam- pling distance (GSD), since the resolution of the best available satellite images does not exceed 30 cm/pixel. The typical size of the hogweed leafs is around the same 30 cm, which results in a situation when a single hogweed plant is resolved into the image area of several pixels, which makes its detection nearly impossible. In addition, the satellite monitoring system is vulnerable to the weather changes, since it becomes impossible to capture plants in a cloudy weather. At the same time, UAVs enable to select GSD from millimeters to meters per pixel depending on the needs by varying altitude during the mission. As for UAVs it is still impossible to perform monitoring in rainy conditions, the applicability of them is far more ﬂexible than satellites. Currently, the limitations on equipment and computa- tional resources the UAVs can carry, as well as the area UAVs can cover per a single mission, are strongly bounded by their lifting capacity and power supply resources. This issue poses the problem of effective management of sensors and computer vision algorithms used for monitoring.

In our previous work [8], we focused on the optimization of the most relevant FCNN architectures for inference on board the single-board computer (SBC). The point of this work was the feasibility of the application of such a drone with artiﬁcial intel- ligence (AI) on board in PA. However, the dataset was collected during a single day. It does not contain different phases of the hogweed growth. Thus, the capabilities of the FCNN, trained on such a dataset, are limited. Furthermore, the data were collected using the RGB camera only. The current article proposes an approach that enhances the capabilities of the monitoring system in several ways.

First, the dataset used in this study was collected in the same area with a weekly period of 2.5 months. It contains the data on the growth phases of the hogweed during this time span. Hence, such a dataset is valuable for both AI and PA areas. Moreover, the dataset was collected using both RGB and multispectral cameras. Additional channels give more information about the object of interest and improve the accuracy and robustness of the neural network. The current research’s contribution is the enhancement of the neural network capabilities due to the generation of artiﬁcial NIR channels. It provides a signiﬁcant advantage in terms of both the accuracy of predictions and the feasibility of such a monitoring system in practice. The application of the proposed approach allows us to get rid of the multispectral camera for hogweed detection. Thus, it makes

Nowadays, in PA, a multisensor setup is typically used. It combines a traditional RGB sensor together with the infrared one. For the latter, the near-infrared (NIR) band is usually con- sidered. Compared with a single RGB camera, the multispectral

104 IEEE JOURNAL OF SELECTED TOPICS IN APPLIED EARTH OBSERVATIONS AND REMOTE SENSING, VOL. 16, 2023

the monitoring system cheaper, more sustainable, and prolongs the ﬂight time.

report a UAV-based setup consisting of RGB and NIR-retroﬁtted cameras, which perform imaging missions over rice and corn ﬁelds in the Philippines. They comment on using a dual-camera setup in order to compute a precise NDVI of the crops. A survey performed by Radoglou-Grammatikis et al. [20] extends the list of possible multispectral camera usages toward the optimization of the image acquisition system and water stress indices. At the same time, robust quantitative studies require a proper usage of multispectral cameras and additional attention not only to their temporal calibration with visual band cameras, but also to the calibration of their spectral characteristics, as highlighted in [21].

It should be noted that the deployment of neural architecture to the edge device is not a trivial task [9], and various opti- mization techniques were proposed to overcome this problem. A hardware-based optimization for binary weight CNNs was proposed in [10], where the arithmetic core was optimized by the elimination of the need for expensive multiplications, as well as by the reduction of I/O bandwidth and storage. Typically, however, most well-known techniques to accelerate inference are software based and include architecture-related optimiza- tions, which are performed either manually or automatically via neural architecture search and pruning in [11]. It was also shown that another type of optimization performed by quantizing neu- ral network weights and inference procedure to uint8 or even binary can drastically accelerate the inference without a large deterioration of their performance. Such techniques were used, for example, in [12] to accelerate the semantic segmentation task on NVIDIA Jetson Xavier NX by the usage of computationally efﬁcient manually designed adaptive blocks, namely multiﬁber unit and attention module, as well as the quantization of model weights to int8 and pruning, helping achieve a good inference speed without a big drop of prediction quality.

By this reason, several approaches were proposed targeting the capture of multispectral information directly from the corre- sponding RGB camera frames. For example, several approaches propose to remove the NIR blocking ﬁlter installed inside all the consumer RGB cameras [22]. In this case, the signal from the NIR band is mixed with the red channel; however, the authors claim that it still helps to calculate the NDVI with high tolerance. Costa et al. [23] introduce a new NDVI mimicking index com- puted from RGB data by the use of a genetic algorithm. Finally, inspired by Pix2Pix [24] performance in conditional synthesis tasks, Yuan et al. [25] and Soni et al. [26] separately proposed to use the same conditional generative adversarial CNN for the purpose of sampling visually plausible NIR spectral band from the satellite and aerial RGB observations, respectively.

C. Intelligent Monitoring Systems in PA

There are different types of autonomous vehicles, which allow a precise monitoring of crops. Typically, they are classiﬁed into two groups, UAVs, that operate in the air, and UGVs, that operate on the ground. As UGVs are able to perform individual plant phenotyping, characteristic monitoring, and even manipulations with crops and weeds [13], in crop monitoring tasks, the priority is given to UAVs due to their ability to cover large areas relatively fast without disseminating the seeds.

III. METHODS

A. Data Collection

Owing to the individual features of a hogweed plant, large size of its leaves, and large height, we found it possible to perform an aerial collection of data. We have performed two ﬂight missions in two separate days with the time difference of two weeks in order to cover crops in different growth stages, scanning the two neighboring ﬁelds in x city and y country,1 and we used images captured from both the ﬁelds separately for train and evaluation purposes. In both the missions, we collected RGB images of size 3000 × 4000 (height × width) pixels using the DJI-FC330 camera mounted on a DJI drone capturing underneath ﬁeld in spatial locations predeﬁned during the mission planning. Specif- ically, for the ﬂight collecting training data, we have mounted an additional MAPIR Survey3 multispectral camera, capturing red (660 nm), green (550 nm), and NIR (850 nm) channels of the same spatial resolution at a predeﬁned frequency of 0.5 frames/s (FPS), and we denote the data from this camera as RGN.

Typically,theUAVsareequippedwithanRGBcameracaptur- ing the crops underneath in a visual spectrum, and the machine vision algorithms are processing the images from this camera in order to get the desired output. Typically, such processing is done ofﬂine after the mission is complete [14] since the frame stream is stored on an internal storage of the UAV [15] or is transferred to the intermediate server during the mission by a wireless protocol [16]. Since both the cases are not practically feasible as they require additional efforts and do not allow for fast decision making, it is important to consider inference being performed directly on the edge device [17]. This is especially vital for the hogweed detection, as the weed can spread very fast by generating up to 100 000 seeds a year that are quickly dis- seminated by wind. A proper detection and elimination of each poisonous plant is essential, and the edge computing enables it by providing the instant information on the geolocation of the plant.

In this research, we generate a fake infrared channel using a generative adversarial neural network. This approach is promis- ing from a practical point of view. There are several alignment issues that we address using an artiﬁcial channel.

1) First of all, the camera DJI-FC330 is attached to the drone’s gimbal. It allows a precise control of camera position during the ﬂight according to the mission require- ments. The gimbal is also used to stabilize the camera in

In order to improve the monitoring outcomes, additional information can be provided to the vision algorithm in a form of a separate multispectral frame stream. Typically, this is done to allow direct calculations of vegetation indices such as normalized difference vegetation index (NDVI) or normalized difference red edge index [18]. For example, Honrado et al. [19]

1Location is hidden due to the blind review and the manuscript submission requirements.

KOSHELEV et al.: DRONE-AIDED DETECTION OF WEEDS: TRANSFER LEARNING FOR EMBEDDED IMAGE PROCESSING 105

Fig. 1. Greedy pipeline of RGB and RGN orthophotos alignment and dataset creation for training neural networks. At the ﬁrst stage, two orthophotos are aligned with a single afﬁne transform, and the alignment is further reﬁned by a second region-adaptive transform.

the case of wind gusts. On the other hand, the multispectral cameraisﬁxedandisalwaysalignedwiththedrone’spose. Hence, there is no way to compensate for its shift in the case of any disturbances, and the resulted images from two cameras are not aligned with each other. 2) Owing to the different design of the lenses, the apertures of cameras are 20 cm away from each other, so both the ﬁeld ofviewandthesensorilluminationvariesbetweenthetwo. This effect also contributes to the alignment problems. 3) Two cameras have different frame rates and are not syn- chronized, so they do not perform every shot simulta- neously. It raises the issue of alignment in the case of real-time processing during the ﬂight. 4) Using two cameras also lead to issues even in the case of two-orthophoto alignment. There are separate GPS antennas for each camera. GPS data are critical for the orthophoto stitching; therefore, it will inﬂuence the preci- sion of the resulting orthophoto. 5) NIR cameras typically have lower resolution; then, we need to crop images from RGB cameras in the case of real-time data processing. It leads to the loss of data from the RGB camera, therefore decreasing the overall effectiveness of the system. 6) Finally, a multispectral camera is expensive in comparison with an SBC and a drone. Moreover, it is an additional payload. Then, it will decrease the time of ﬂight. To sum up, it is better to have a single cheap RGB camera on-board, rather than two cameras. To upgrade the RGB camera with NIR capabilities, we can use the algorithm described in this article. As a result, the monitoring system with a single camera will be cheap and reliable.

to label all the regions of interest within the RGB orthophoto, using any raster image processing software.

In order to align the images and construct a paired dataset for training, we have applied a greedy-region-based procedure. At the ﬁrst step, the two orthophotos are globally aligned based on the best afﬁne transformation between corresponding ORB features [27]. At the second stage, we divide both the orthopho- tos and the labels into overlapping patches of size 256 × 256 pixel. We use the same alignment procedure applied to each patch independently, and we search for the best match within the region of ±100 pixels around the patch. We depict the overall pipeline in Fig. 1.

Constructing training data for the online scanning regime involves additional RGB frame stream used to create the or- thophoto. For this scenario, an intermediate stage based on the same alignment procedure is required in order to ﬁnd the position of the entire frame in the RGB orthophoto. The selected region is cropped from both orthophotos and labels. Owing to the nature of texturing step used to synthesize orthophotos, the best match between the original frame and its region inside the orthophoto is achieved within the central part of the frame. Thus, we run the patch-based reﬁnement only on the central part of size 2000 × 2000 pixels. We have performed this procedure in order to sample both train and test data with random crops of size 128 × 128 for training purposes and 256 × 256 for the test. Since for the test dataset we do not collect multispectral images, we exclude these data from the discussed sampling procedure. Overall, we have collected more than 20 000 crops for training purposes and 83 crops for evaluation, and we carefully checked the correctness of the resulted labels by additional look at the images in the latter.

We should note, that the surface where we performed the data collection included both vegetating (young) hogweed crops and those, which have already faded (old). Since the procedures required to eliminate these two types of hogweed plants can vary, we have labeled such cases with different semantics classed to

B. Data Processing and Labeling

The collected dataset consists of two independent sequences of frames, which are not synchronized between each other. In order to align them, we propose to fuse both the frame streams into corresponding orthophotos, and we use an OpenDroneMap software for this.2 Once the step is completed, it is convenient

2ODM—a command line toolkit to generate maps, point clouds, 3-D models, and DEMs from drone, balloon, or kite images. Available at https://github.com/ OpenDroneMap/ODM.

106 IEEE JOURNAL OF SELECTED TOPICS IN APPLIED EARTH OBSERVATIONS AND REMOTE SENSING, VOL. 16, 2023

learn the segmentation network to distinguish between them, facilitating an effective practical application of our work. For all our reported data, we have used a manual labeling procedure in the GIMP graphic editor.3 It should be noted that only RGB orthophotos are required for labeling, since the produced labels can be back-projected to the corresponding RGN orthophotos and original frames using the procedure discussed above. We release the dataset consisting of training, validation, and testing samples, where we included both labeled orthophotos together with a paired crop suitable for training. The dataset is available at www.x.com.4

C. Neural Network Architectures

In this study, we do not provide extensive experiments with neural network architectures, since our main goal is to show the approaches to improve the performance of the existing prede- ﬁned architecture when additional data are at hand. However, we do compare different architectures in two modes, namely, computationally more and less intensive, and we do the spe- cial emphasis on the latter one in this article due to practical concerns. We depart from the high-capacity neural networks and use a SegNet architecture [28] with 29.5M parameters for the segmentation part and an encoder–decoder network with residual blocks [29] and 7.8M parameters for the fake NIR syn- thesis. Both the architectures were proven to perform well with the general-purpose segmentation and synthesis tasks, respec- tively [30], [31]. Targeting a balance between the performance and inference speed when evaluated on an embedded system, we have selected well-known U-Net architectures for both the segmentation and synthesis tasks in the less computationally intensive regime, since its superiority for satisfying both goals was shown in recent papers [7]. It is a fully CNN that was initially developed speciﬁcally for the semantic segmentation task; however, it was also shown that this network can efﬁciently solve image-to-image tasks [32]. Being an encoder–decoder architecture, the main beneﬁt is that it allows the processing and analysis of images at different scales, which allows us to greatly increase its receptive ﬁeld without the increase of computational complexity. Targeting the fast inference speeds, for the segmentation network, we have used a U-Net backbone consisting of three blocks in both the encoder and decoder parts with 17.3M parameters in total, and a backbone with two blocks and 2.2M parameters for synthesis. We found the capacity of these networks good enough to both obtain a good quality in semantic segmentation task and run them with high speed on an embedded system.

Fig. 2. Training procedure of the proposed segmentation pipeline. (a) Seg- mentation network is trained with real data. (b) Transfer learning procedure is used to train a synthesis network that provides the fake RGN frames. (c) At the last stage, the segmentation network is ﬁne-tuned on the fake RGN data.

multiple of 90◦rotations and random horizontal and vertical ﬂips to augment our training data. We minimized all the objec- tive functions using the Adam optimizer [34] with a learning rate of 1e−3, and a warm-up scheduling was enabled for the ﬁrst epoch. For training the synthesis neural network, we have used an adversarial learning adopted from pix2pix [24]. Since the network chosen to perform synthesis is relatively small, we have used an adaptive gradient step frequency [35] for both the generator and the discriminator in order to avoid discrimi- nator’s overﬁtting and other instabilities.

D. Training and Implementation Details

We have conducted all our experiments using the PyTorch framework [33], which allowed us to effectively deploy net- work training, involving parallel computations, to GPUs. In all the cases, we have trained our networks using crops of size 128 × 128 pixels. We have used random crops as well as random

Overall, our training strategy is depicted in Fig. 2 and consists of the following three steps.

1) During the ﬁrst one, we train our network to segment hogweed plants based on both RGB and RGN data con- catenated and passed as an input. For this task, we perform

3The GIMP Development Team. Available at https://www.gimp.org. 4It is the subject of double-blind review.

KOSHELEV et al.: DRONE-AIDED DETECTION OF WEEDS: TRANSFER LEARNING FOR EMBEDDED IMAGE PROCESSING 107

TABLE I PERFORMANCE OF TRAINED LARGE MODELS (SEGNET+RESNET) EVALUATED ON TEST DATA FROM TRAIN AND TEST FIELDS

TABLE II PERFORMANCE OF TRAINED SMALL MODELS (U-NETS) EVALUATED ON TEST DATA FROM TRAIN AND TEST FIELDS

a supervised learning by optimizing the cross-entropy objective, as shown in Fig. 2(a). 2) During the second step, we train another neural network to synthesize fake RGN-like images out of the real RGB ones. The training of this stage is highlighted in Fig. 2(b). For this task, we conduct the adversarial training similar to the earlier proposed pix2pix model [24], and we use the same loss function of the form

network to output images, which should beneﬁt to the target semantic segmentation task. For this purpose, we penalize L2 objective Lseg computed between the output features of the network from the previous step evaluated on the ground-truth and fake RGN data

Lseg = Ex,y ||T(x, y, θT ) −T(x, G(x, θG), θT )||2 (2)

where we have denoted the segmentation network from the previous step and its weights as T and θT . We use the traditional generative adversarial network (GAN) [36] min–max game to conduct the following optimization:

Lp2p = Ex,y log D(x, y, θD)

+ Ex log (1 −D(x, G(x, θG), θD))

+ λ1 Ex,y ||y −G(x, θG)||1. (1)

θG = arg min

θD Lp2p + λ2Lseg. (3)

θG max

Here,wedenoteRGBandRGNimagesasx and y,respec- tively, and θG and θD as the trainable weights of the gener- ator and discriminator networks G and D, respectively. In addition, we involve the transfer learning and force our

The intuition behind this step is to fuse information about valuable features from RGN images, which can beneﬁt the segmentation of hogweed plants into the preprocessing

108 IEEE JOURNAL OF SELECTED TOPICS IN APPLIED EARTH OBSERVATIONS AND REMOTE SENSING, VOL. 16, 2023

network trained at this stage. We have found values λ1 = 100 from (1) and λ2 = 10 from (3) to suit well for this goal. 3) During the ﬁnal step, we perform an iterative inference of the network trained at the previous step through all our dataset samples to obtain fake RGN images and then ﬁne-tune a semantic segmentation network on these data using the same procedure, as in step 1. This step is depicted in Fig. 2(c) and does not require real RGN data anymore, since information about this domain is fused inside param- eters of the synthesis network during the previous stage.

by the means of mIoU showed 95% and 90% for old and young crops, respectively, with the main source of error attributed to the inconsistencies introduced by the independent manual labeling of frames and orthophoto. Such ﬁndings demonstrate that the difference between the true labels and the labels transferred from orthophoto with our proposed strategy is negligible. As extensively studied and proven in [38] and [39], these small errors in labels do not affect the training and performance of neural networks. We also present an indicative example in Fig. 3 for a qualitative comparison.

We have trained our models separately with orthophoto im- ages and with images from the camera. For both the scenarios, we trained the following models.

E. Porting to the Embedded System

1) segmentation network working with RGB+RGN pair in- volving true RGN data (TrueRGN); 2) segmentation network working with only RGB frames (NoRGN); 3) network consisting of synthesis and segmentation parts trained end to end with only RGB data (SynthNoRGN); 4) network consisting of synthesis and segmentation parts trained using the transfer learning procedure with true RGN data (SynthFakeRGN); 5) network consisting of synthesis and segmentation parts trained without transfer learning procedure with true RGN data (SynthFakeRGNnoTL). In Tables I and II, we report on the results of all our models evaluated on both missions we performed directly for testing purposes (Test ﬁeld) as well as on a subset of data obtained during the collection of our training data (Train ﬁeld). In Fig. 4, we report the visual example of the synthesis U-Net network trained to mimic orthophoto data. It should be noted that there is no intersection of training and testing data.

We have used NVIDIA Jetson Xavier NX as a target device, sinceit was proventobeanefﬁcient low-cost solutionfor various vision tasks in edge computing [8]. In order to accelerate the inference speed of our network and make simulations of the proposed approach running on an embedded system, we have applied the well-known techniques of network quantization and layer fusion (pruning). Owing to speciﬁc choice of segmentation and synthesis networks in our less computationally intensive regime to be the standard U-Net architectures, the port of our models to the edge device is relatively straightforward. Owing to this reason, we have used NVIDIA TensorRT inference op- timizer and runtime, which performs all the optimizations, as well as other architecture-speciﬁc tunings.

F. Evaluation Metrics

Inordertoevaluateourmodelsandcompareittothebaselines, wehaveusedtwomostcommonapproachesfortheclassiﬁcation and semantic segmentation (i.e., classiﬁcation of each image pixel), namely, mean intersection over union (mIoU) and the area under the curve (AUC) of a receiver operating characteristic (ROC) curve, given by the true positive and false positive rates. For more informative evaluation, both the metrics are computed in a multiclass regime when young and old crops are treated as different classes and in a binary regime when both types of crops are treated as a single class. As a reference, we have observed that typical values of 60% of mIoU reported in various multiclass semantic segmentation benchmarks [37] are considered as an acceptable segmentation performance.

Several conclusions can be made from the tables. At ﬁrst, metrics obtained on a subset of train ﬁeld dataset are higher than those computed on test data. We think this change may indicate the difference in data collection and manual labeling performed for both train and test ﬁelds’ data separately at different time. The additional effect is overﬁtting, which is more pronounced for larger networks in Table I, where the gap between train and test ﬁelds is larger. Comparing the same models trained for either orthophoto data or frame data, but evaluated on both, it is clear that networks trained with frames are in general more robust with respect to the change of data type. Thus, the difference between multiclass mIoU metrics of SynthFakeRGN models trained with frames is, on average, 2% on test ﬁeld data and 5.9% on train ﬁeld one, while for the same models trained with orthophoto data, it is 6.3% and 24.2%, respectively. It means that frame stream from the camera is more favorable for the purpose of hogweed precise monitoring, which sup- ports our efforts in transferring all computations to the aerial platform.

To assess the performance of our approach ported to the embedded system, we measure the inference speed per 12-MPx frame (3000 × 4000 pixel) in FPS, as well as the power con- sumption of the hardware in watts (W).

IV. RESULTS

At the ﬁrst stage of our study, we validate the designed label transfer. For this purpose, we have randomly selected ten frames out of the sequence used to construct the training dataset. The proposed strategy was used to sample images of crops with corresponding labels transferred from orthophoto data. For the same set of frames, we have performed manual labeling, which allowed to get the true labels for the sampled crops and use them to perform a quantitative comparison. The evaluation performed

Comparing segmentation models trained with and without true RGN data, we can emphasize the superiority of the former. Indeed, in all the cases, when evaluated on data from train ﬁeld, TrueRGN and SynthFakeRGN models constantly perform betterthanNoRGNandevenitsmorecomputationallyexpensive analogue SynthNoRGN. For example, TrueRGN models trained

KOSHELEV et al.: DRONE-AIDED DETECTION OF WEEDS: TRANSFER LEARNING FOR EMBEDDED IMAGE PROCESSING 109

Fig. 3. Qualitative comparison of true frame labels with those transferred from orthophoto. Old and young crops are denoted with red and blue colors, respectively.

TABLE III PERFORMANCE OF TRAINED NETWORKS IN SIMULATIONS RAN ON AN EMBEDDED SYSTEM NVIDIA JETSON XAVIER NX AND ON SERVER

GPU NVIDIA TESLA V100

Fig. 4. Example of fake RGN frames synthesis with the synthesis part of the SynthFakeRGN model trained with frames and orthophoto data.

and evaluated on frame data perform on average 2.2% better than corresponding NoRGN models and 2.4% better than Syn- thNoRGN ones in terms of multiclass mIoU metric. In addition, from Tables I and II, it is clear that TrueRGN models better generalize to the different test data. As an example, the U-Net model (see Table II) trained on orthophoto data gives a score of 75.3% when evaluated on frame data, which is 6.3% less than that of the same model evaluated on the frame test set. At the same time, all the other U-Net models trained on orthophoto data overﬁt to the training domain, which results in the differences of 26%, 20.9%, and 24% for SynthFakeRGN, NoRGN, and SynthNoRGN, respectively.

NoRGN models, which have a smaller number of parameters and computational complexity. This fact supports our approach, since it again highlights the importance of a proper training procedure.

Finally, we observe that the models utilizing fake RGN data trained with the transfer learning approach (SynthFakeRGN) continuously perform better than their analogues trained with just RGB to NIR GAN (SynthFakeRGNnoTL). The highest difference occurs for models trained with frame data, where SynthFakeRGN outperforms SynthFakeRGNnoTL by 5.1% on average in terms of multiclass mIoU metric measured for the test data. This fact proves that the proposed transfer learning approach is a crucial component for fake NIR utilization if the semantic segmentation task is at hand.

It is clearly seen from Tables I and II that in almost all the cases, the SynthFakeRGN model performs considerably better than NoRGN and SynthNoRGN with both mIoU and ROC-AUC metrics, which means that it has beneﬁted from the training procedure introduced in this article. For example, trained on orthophoto data, SynthFakeRGN models on average outperform NoRGN by 3.4% and 0.017 in terms of multiclass mIoU and ROC-AUC metrics and by 2.8% and 0.019 in terms of binary ones when evaluated on the test dataset. It is also interesting to note that being trained within the uniﬁed pipeline, SynthNoRGN performance in general deteriorates from a lighter

Overall, we observe that multiclass metrics are lower than binary ones, and the difference is especially pronounced when evaluated on the test ﬁeld. Indeed, the binary classiﬁcation is an easier problem to solve, compared to the task of separating plants byage;however,evenforthelattercase,themetricsarerelatively high, which shows the success of our approach. We present the visual comparison of multiclass segmentation performance between SynthFakeRGN, SynthNoRGN, and NoRGN models with U-Net architecture in Fig. 5.

110 IEEE JOURNAL OF SELECTED TOPICS IN APPLIED EARTH OBSERVATIONS AND REMOTE SENSING, VOL. 16, 2023

Fig. 5. Performance of our models from Table I trained with orthophoto data on crop taken from the labeled orthophoto of test ﬁeld (best viewed in electronic version).

In order to show the direct applicability of our hogweed precise monitoring system, we have ported both U-Net semantic segmentation and fake NIR synthesis models to a Jetson Xavier NX embedded system and simulated its runtime during the mission by imitating a frame stream from the RGB camera. Owing to the memory limitations of this computational unit, we have performed a tile inference, where each frame is ﬁrst divided into nonoverlapping regions of size 100 × 100, which are fed to the network with batch size 1, and the resulting local maps are stitched back to form a global map corresponding to the full frame resolution. Interestingly enough, we have managed to deploy all our networks to an embedded platform without any loss of segmentation quality, so we do not report the difference in metrics for networks evaluated on different platforms. In Table III, we report on the runtime and a power consumption we have measured during the simulation. For comparison, we also report values for the run on NVIDIA Tesla V100, where we have used our original models without any optimizations and we passed the whole 3000 × 4000 frame to the network.

a real RGN data are provided. We ported our trained networks to an embedded system and showed that they are capable of performing the processing part of a real mission targeting precise location of hogweed crops. The proposed approach can be scaled to other agricultural-industry-related applications including the disease and insect detection.


## REFERENCES

[1] Y. Liu, X. Ma, L. Shu, G. P. Hancke, and A. M. Abu-Mahfouz, “From

Industry 4.0 to Agriculture 4.0: Current status, enabling technologies, and research challenges,” IEEE Trans. Ind. Informat., vol. 17, no. 6, pp. 4322–4334, Jun. 2021. [2] I. Sa et al., “WeedMap: A large-scale semantic weed mapping framework

using aerial multispectral imaging and deep neural network for precision farming,” Remote Sens., vol. 10, no. 9, 2018, Art. no. 1423. [3] A. Milioto, P. Lottes, and C. Stachniss, “Real-time semantic segmentation

of crop and weed for precision agriculture robots leveraging background knowledge in CNNs,” in Proc. IEEE Int. Conf. Robot. Autom., 2018, pp. 2229–2235. [4] J. Su et al., “Aerial visual perception in smart farming: Field study of

wheat yellow rust monitoring,” IEEE Trans. Ind. Informat., vol. 17, no. 3, pp. 2242–2249, Mar. 2021. [5] P. Lottes, R. Khanna, J. Pfeifer, R. Siegwart, and C. Stachniss, “UAV-based

crop and weed classiﬁcation for smart farming,” in Proc. IEEE Int. Conf. Robot. Autom., 2017, pp. 3024–3031. [6] O. Ronneberger, P. Fischer, and T. Brox, “U-Net: Convolutional networks

V. CONCLUSION

for biomedical image segmentation,” in Proc. Int. Conf. Med. Image Comput. Comput. Assist. Intervention, 2015, pp. 234–241. [7] P. Lottes, J. Behley, A. Milioto, and C. Stachniss, “Fully convolutional

In this article, we proposed and evaluated an idea of incor- porating knowledge about multispectral bands in the neural network performing the semantic segmentation of hogweed crops. We collected and labeled two datasets consisting of old and young hogweed crops from two different ﬁelds within the same region, one of which involved only RGB frame stream and is used for testing purposes, and the other was collected with an additional RGN camera on board. We proposed an idea of labeling frames by labeling the corresponding orthophotos, and wesuccessfullyapplieditforboththedatasets.Wealsoproposed an alignment strategy, which allowed us to align RGB, RGN, and label orthophotos between each other and RGB frames from the frame stream. With these data, we trained U-Net and SegNet architectures to perform semantic segmentation, and we used a transfer learning procedure to train a separate synthesis head consisting of another lighter network, which performs the synthesis of RGN data to facilitate further semantic segmen- tation task. We observed that this approach is at least 1.1% better than the end-to-end training of either segmentation or both synthesis and segmentation networks when only RGB data are involved. We also showed that this training procedure allows us to obtain the segmentation quality of the same level as when

networks with sequential information for robust crop and weed detection in precision farming,” IEEE Robot. Autom. Lett., vol. 3, no. 4, pp. 2870–2877, Oct. 2018. [8] A. Menshchikov et al., “Real-time detection of hogweed: UAV platform

empowered by deep learning,” IEEE Trans. Comput., vol. 70, no. 8, pp. 1175–1188, Aug. 2021. [9] M. Zhang et al., “Deep learning in the era of edge computing: Challenges

and opportunities,” in Fog Computing: Theory and Practice. Hoboken, NJ, USA: Wiley, 2020, pp. 67–78. [10] R. Andri, L. Cavigelli, D. Rossi, and L. Benini, “YodaNN: An architec-

ture for ultralow power binary-weight CNN acceleration,” IEEE Trans. Comput.-Aided Des. Integr. Circuits Syst., vol. 37, no. 1, pp. 48–60, Jan. 2017. [11] A. Kuzmin, M. Nagel, S. Pitre, S. Pendyam, T. Blankevoort, and M.

Welling, “Taxonomy and evaluation of structured compression of con- volutional neural networks,” pp. 1–33, 2019. [Online]. Available: https: //arxiv.org/abs/1912.09802 [12] J. Zheng, J. Li, Y. Liu, and W. Zhang, “Real-time semantic segmentation

network for edge deployment,” in Chin. Intell. Syst. Conf., 2019, vol. 7, pp. 154239–154252. [13] P. Gonzalez-De-Santos, R. Fernández, D. Sepúlveda, E. Navas, and

M. Armada, “Unmanned ground vehicles for smart farms,” in Agronomy- Climate Change & Food Security. Rijeka, Croatia: InTech, 2020, pp. 1–23. [14] L. Mendes dos Santos et al., “Determining the leaf area index and percent-

age of area covered by coffee crops using UAV RGB images,” IEEE J. Sel. Topics Appl. Earth Observ. Remote Sens., vol. 13, pp. 6401–6409, 2020.

KOSHELEV et al.: DRONE-AIDED DETECTION OF WEEDS: TRANSFER LEARNING FOR EMBEDDED IMAGE PROCESSING 111

[15] C. Zhang, D. Walters, and J. M. Kovacs, “Applications of low altitude

[39] ¸S. V˘adineanu, D. Pelt, O. Dzyubachyk, and J. Batenburg, “An analysis of

remote sensing in agriculture upon farmers’ requests—A case study in Northeastern Ontario,” Canada. PLoS One, vol. 9, no. 11, 2014, Art. no. e112894. [16] S. R. Herwitz et al., “Imaging from an unmanned aerial vehicle: Agri-

the impact of annotation errors on the accuracy of deep learning for cell segmentation,” in Proc. Med. Imag. Deep Learn. Conf., 2021, pp. 1–17.

cultural surveillance and decision support,” Comput. Elect. Agriculture, vol. 44, no. 1, pp. 49–61, 2004. [17] M. J. O’Grady, D. Langton, and G. M. P. O’Hare, “Edge computing: A

Iaroslav Koshelev received the B.Sc. and M.Sc. degrees in physics from Moscow State University, Moscow, Russia, in 2017 and 2019, respectively, and the M.Sc. (Hons.) degree in data science in 2019 from the Skolkovo Institute of Science and Technology, Moscow, where he is currently working toward the Ph.D. degree in data science.

tractable model for smart agriculture?,” Artif. Intell. Agriculture, vol. 3, pp. 42–51, 2019. [18] E. Barnes et al., “Coincident detection of crop water stress, nitrogen status,

and canopy density using ground based multispectral data,” Proc. of the 5th Int. Conf. Precision Agriculture, 2000, pp. 1–15. [19] J. L. Honrado, D. Solpico, C. Favila, E. Tongson, G. Tangonan, and

Hisresearchinterestsincludeimage/videoprocess- ing, deep learning, and sensors fusion.

N. Libatique, “UAV imaging with low-cost multispectral imaging system for precision agriculture applications,” in Proc. IEEE Glob. Humanitarian Technol. Conf., 2017, pp. 1–7. [20] P. Radoglou-Grammatikis, P. Sarigiannidis, T. Lagkas, and I. Moscholios,

“A compilation of UAV applications for precision agriculture,” Comput. Netw., vol. 172, 2020, Art. no. 107148. [21] L. Deng, Z. Mao, X. Li, Z. Hu, F. Duan, and Y. Yan, “UAV-based multi-

Maxim Savinov received the M.Sc. degree in infor- mation science and technology from the Skolkovo Institute of Science and Technology, Moscow, Russia, in 2022. He is currently working toward the Ph.D. degree with the Saint Petersburg State University of Aerospace Instrumentation, Saint Petersburg, Russia.

spectral remote sensing for precision agriculture: A comparison between different cameras,” ISPRS J. Photogrammetry Remote Sens., vol. 146, pp. 124–136, 2018. [22] L. Wang et al., “Precise estimation of NDVI with a simple NIR sensitive

RGB camera and machine learning methods for corn plants,” Sensors, vol. 20, no. 11, 2020, Art. no. 3208. [23] L. Costa, L. Nunes, and Y. Ampatzidis, “A new visible band index

Hisresearchinterestsincludemachinelearningand computer vision.

(VNDVI) for estimating NDVI values on RGB images utilizing genetic al- gorithms,” Comput. Electron. Agriculture, vol. 172, 2020, Art. no. 105334. [24] P. Isola, J.-Y. Zhu, T. Zhou, and A. A. Efros, “Image-to-image translation

with conditional adversarial networks,” Proc. IEEE Conf. Comput. Vis. Pattern Recognit., 2017, pp. 5967–5976. [25] X. Yuan, J. Tian, and P. Reinartz, “Generating artiﬁcial near infrared

Alexander Menshchikov received the M.S. degree in applied physics and mathematics from the Moscow Institute of Physics and Technology, Dolgoprudny, Russia, in 2014, and the Ph.D. degree in data science from the Skolkovo Institute of Science and Technol- ogy (Skoltech), Moscow, Russia, in 2020.

spectral band from RGB image using conditional generative adversarial network,” ISPRS Ann. Photogrammetry Remote Sens. Spatial Inf. Sci., vol. 3, pp. 279–285, 2020. [26] A. Soni, A. Loui, S. Brown, and C. Salvaggio, “High-quality multispectral

image generation using conditional GANs,” Electron. Imag., vol. 32, 2020, Art. no. art00004. [27] E. Rublee, V. Rabaud, K. Konolige, and G. Bradski, “ORB: An efﬁ-

He is currently a Research Engineer with Rakuten, Tokyo, Japan. Before joining Rakuten he had worked as an Engineer in Central Aerohydromechanis In- stitute (TsAGI), Russia, (2011–2014), as a Space Systems Engineer in Sputnix and Dauria Aerospace companies (2015–2016), as an Engineer in mechatronics and robotics group in TOPCON company (2017–2018), Machine Learning Researcher in Skoltech (2018–2020) and Senior Software Engineer in Huawei, Russia, (2021–2022). In 2015, he was a Visiting Student with the Department of Aeronautics and Astronautics, Massachusetts Institute of Technology, Cambridge, MA, USA. His current research interests include robotics, artiﬁcial intelligence and embedded systems.

cient alternative to sift or surf,” in Proc. Int. Conf. Comput. Vis., 2011, pp. 2564–2571. [28] V. Badrinarayanan, A. Kendall, and R. Cipolla, “SegNet: A deep convolu-

tional encoder-decoder architecture for image segmentation,” IEEE Trans. Pattern Anal. Mach. Intell., vol. 39, no. 12, pp. 2481–2495, Dec. 2017. [29] K. He, X. Zhang, S. Ren, and J. Sun, “Deep residual learning for image

recognition,” in Proc. IEEE Conf. Comput. Vis. Pattern Recognit., 2016, pp. 770–778. [30] S. Minaee, Y. Y. Boykov, F. Porikli, A. J. Plaza, N. Kehtarnavaz, and

D. Terzopoulos, “Image segmentation using deep learning: A survey,” IEEE Trans. Pattern Anal. Mach. Intell., vol. 44, no. 7, pp. 3523–3542, Jul. 2022. [31] T.-C. Wang, M.-Y. Liu, J.-Y. Zhu, A. Tao, J. Kautz, and B. Catanzaro,

Andrey Somov received the bachelor’s and Diploma degrees in electronic engineering from MATI— Russian State Technological University, Moscow, Russia, in 2004 and 2006, respectively, and the Ph.D. degree in power management in wireless sensor net- works (WSN) from the University of Trento, Trento, Italy, in 2009.

“High-resolution image synthesis and semantic manipulation with condi- tional GANs,” in Proc. IEEE Conf. Comput. Vis. Pattern Recognit., 2018, pp. 8798–8807. [32] Y. Cai and U. Kintak, “Low-light image enhancement based on modiﬁed

U-Net,” in Proc. Int. Conf. Wavelet Anal. Pattern Recognit., 2019, pp. 1–7. [33] A. Paszke et al., “PyTorch: An imperative style, high-performance deep

learning library,” in Proc. Int. Conf. Neural Inf. Process. Syst., 2019, pp. 8024–8035. [34] D. P. Kingma, and J. Ba, “Adam: A method for stochastic optimization,”

He is currently an Assistant Professor with the Skolkovo Institute of Science and Technology (Skoltech), Moscow. Before joining Skoltech in 2017, he was a Senior Researcher with the CREATE-NET Research Center, Trento, Italy, from 2010 to 2015, and a Research Fellow with the University of Exeter, Exeter, U.K., from 2016 to 2017. He has authored or coauthored more than 100 papers in peer-reviewed international journals and conference proceedings. His current research interests include intelligent sensing, machine learning, computer vision, and associated proof-of-concept implementation.

pp. 1–15, 2017. [Online]. Available: https://arxiv.org/abs/1412.6980 [35] X. Ma, R. Jin, K.-A. Sohn, J. Y. Paik, J. Sun, and T.-S. Chung, “Improving

generative adversarial networks with adaptive control learning,” in Proc. IEEE Vis. Commun. Image Process., 2018, pp. 1–4. [36] I. Goodfellow et al., “Generative adversarial nets,” in Proc. 27th Int. Conf.

Neural Inf. Process. Syst., 2014, pp. 2672–2680. [37] B. Zhou, H. Zhao, X. Puig, S. Fidler, A. Barriuso, and A. Torralba, “Scene

parsing through ADE20K dataset,” in Proc. IEEE Conf. Comput. Vis. Pattern Recognit., 2017, pp. 633–641. [38] A. Zlateski, R. Jaroensri, P. Sharma, and F. Durand, “On the importance

Dr. Somov is the recipient of some awards in the ﬁelds of WSN and Internet of Things (IoT), including the Google IoT Technology Research Award in 2016 and the Best Paper Award at IEEE International Conference on Internet of People in 2019.

of label quality for semantic segmentation,” in Proc. IEEE Conf. Comput. Vis. Pattern Recognit., 2018, pp. 1479–1487.
