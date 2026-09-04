---
workspace_id: SCI-000483
doi: 10.1109/jsen.2021.3071290
title: 'AgriSegNet: Deep Aerial Semantic Segmentation Framework for IoT-Assisted Precision
  Agriculture'
authors:
- family_name: Anand
  given_name: Tanmay
  orcid: https://orcid.org/0000-0002-5725-7048
- family_name: Sinha
  given_name: Soumendu
  orcid: https://orcid.org/0000-0003-3088-7637
- family_name: Mandal
  given_name: Murari
  orcid: https://orcid.org/0000-0002-0157-0967
- family_name: Chamola
  given_name: Vinay
  orcid: https://orcid.org/0000-0002-6730-3060
- family_name: Yu
  given_name: F. Richard
  orcid: https://orcid.org/0000-0003-1006-7594
year: 2021
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:40.999705+00:00'
---

# AgriSegNet: Deep Aerial Semantic Segmentation Framework for IoT-Assisted Precision Agriculture

IEEE SENSORS JOURNAL, VOL. 21, NO. 16, AUGUST 15, 2021 17581

AgriSegNet: Deep Aerial Semantic

Segmentation Framework for IoT-Assisted Precision Agriculture

Tanmay Anand , Soumendu Sinha , Murari Mandal , Member, IEEE, Vinay Chamola , Senior Member, IEEE, and Fei Richard Yu , Fellow, IEEE


## Abstract—Aerial inspection of agricultural regions can

provide crucial information to safeguard from numerous
obstacles to efﬁcient farming. Farmland anomalies such as
standing water, weed clusters, hamper the farming practices,
which causes improper use of farm area and disrupts agri-
cultural planning. Monitoring of farmland and crops through
Internet-of-Things (IoT)-enabled smart systems has potential
to increase the efﬁciency of modern farming techniques.
Unmanned Aerial Vehicle (UAV)-based remote sensing is a
powerful technique to acquire farmland images on a large
scale. Visual data analytics for automatic pattern recognition
from the collected data is useful for developing Artiﬁcial
intelligence (AI)-assisted farming models, which holds great
promise in improving the farming outputs by capturing the crop patterns, farmland anomalies and providing predictive
solutions to the inherent challenges faced by farmers. In this work, we propose a deep learning framework AgriSegNet for
automatic detection of farmland anomalies using multiscaleattention semantic segmentationof UAV acquired images. The
proposed model is useful for monitoring of farmland and crops to increase the efﬁciency of precision farming techniques.

Index Terms— Deep learning, IoT, agriculture, agriculture-vision, semantic segmentation, sensors.

I. INTRODUCTION U

have witnessed unprecedented growth in the last decade due to signiﬁcant technological advancements comprising rapid hardware and software developments [1]. Intelligent moni- toring through UAVs has become critical in various sectors including precision agriculture [2]–[4], post-disaster assess- ment [5], urban surveillance [6], [7], border surveillance [8], environmental monitoring [9] and several other civil as well as strategic scenarios [10], [11]. These applications are enabled by a robust information and communication framework which comprises of data acquisition through remote sensing devices, signal processing and data analysis with intelligent algo- rithms through cloud-based systems. Recent advancements in multi-modal sensing techniques, wireless communication, Internet of Things (IoT), artiﬁcial intelligence (AI) techniques and cloud computation has spurred rapid advancements in the proliferation of remote sensing based data analytics for auto- mated decision making [12], [13]. The UAVs offer promising advantages over the traditionally deployed sensors by lowering the cost, ease of deployment, proﬁciency in remote sensing and ability to capture high resolution images/videos of terrain in non-intrusive manner which is useful in extracting feature representations of the surveyed area [14], [15].

NMANNED aerial vehicles (UAVs) are being widely utilized for sensing and monitoring applications and they

Manuscript received January 2, 2021; revised March 13, 2021; accepted March 28, 2021. Date of publication April 5, 2021; date of current version August 13, 2021. The work of Vinay Chamola and Fei Richard Yu was supported by the SICI Shastri Institutional Collab- orative Research Grant (SICRG) through the Project Artiﬁcial Intelli- gence Enabled Security Provisioning and Vehicular Vision innovations for Autonomous Vehicles. The associate editor coordinating the review of this article and approving it for publication was Dr. Hari P. Gupta. (Corresponding author: Vinay Chamola.)

Tanmay Anand and Vinay Chamola are with the Department of Electrical and Electronics Engineering, Birla Institute of Technology and Science (BITS), Pilani, Pilani 333031, India, and also with the Anuradha and Prashanth Palakurthi Centre for Artiﬁcial Intelligence Research (APPCAIR), Birla Institute of Technology and Science (BITS), Pilani, Pilani 333031, India (e-mail: f20180378@pilani.bits-pilani.ac.in; vinay.chamola@pilani.bits-pilani.ac.in).

Soumendu Sinha is with the Smart Sensors Area, Council of Scientiﬁc and Industrial Research-Central Electronics Engineer- ing Research Institute (CSIR-CEERI), Pilani 333031, India (e-mail: soumendu@ceeri.res.in).

Murari Mandal is with the Department of Computer Science and Engineering, Indian Institute of Information Technology, Kota (IIIT Kota), Kota 302017, India (e-mail: murari023@gmail.com).

Fei Richard Yu is with the Department of Computer Science and Engineering, Carleton University, Ottawa, ON K1S 5B6, Canada (e-mail: richard.yu@carleton.ca).

Large-scale agricultural land monitoring has become important for assisting in precision farming [16]. Precision agriculture is a key component of the modern

Digital Object Identiﬁer 10.1109/JSEN.2021.3071290

1558-1748 © 2021 IEEE. Personal use is permitted, but republication/redistribution requires IEEE permission. See https://www.ieee.org/publications/rights/index.html for more information.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:39:56 UTC from IEEE Xplore.  Restrictions apply.

17582 IEEE SENSORS JOURNAL, VOL. 21, NO. 16, AUGUST 15, 2021

Fig. 1. A visual representation of the proposed IoT framework for deploying AgriSegNet in the cloud. The AgriSegNet obtains aerial scenes captured from UAVs and deep learning inference is performed for robust semantic segmentation.

agricultural revolution. Agricultural practices have become more speciﬁc and highly optimized after the addition of information and communications technology (ICT), IoT, AI, and other cutting-edge technologies. Inclusion of such modern practices and ideas acts as a boon for farming, as it increases productivity and provides greater environmental sustainability. It supports in site speciﬁc management (SSM), which is the idea of performing the right action at the correct place at the right point of time. Precision farming provides us an arrangement to integrate such ideas to agricultural applications. The remote deployment of sensing devices in the ﬁelds will help in monitoring the procedural parameters and offer real time data, which would provide us with updated status of ﬁeld and plant parameters continuously. Climate monitoring, crop monitoring, cattle monitoring and greenhouse automation are some of the popular IoT derived use cases which greatly help in agricultural maintenance and provide good amount of insight to farmers.

ters. Furthermore, the deep learning algorithms can assess the conditions for sowing, provide insights on right crop timing, etc., to enhance productivity and support sustainable farming practices. The pattern analysis of land images can greatly help in the prediction of agricultural yields, suitable crop patterns, biological parameters related to crops and farmland anomalies.

In this study we present AgriSegNet, a deep aerial semantic segmentation framework for agricultural pattern recognition using UAV acquired aerial images, for IoT-assisted precision agriculture. We propose a robust multi-scale hierarchical atten- tion network for semantic segmentation on farmland images. The AgriSegNet utilizes two different image-scales for feeding into the network during training. The network consists of the backbone, semantic head, and attention head. The backbone features are extracted from the DeepLabV3+ model. The attention head combines the features from multiple scales with weighted ratio. Average pooling as combination strategy treats all the scales as being equally important. Finer details are obtained at higher scales, while larger patches within the image are obtained at lower scales. In our approach, the model learns about relative attention mask in order to combine or attend predictions for multiple scales. The inference model makes use of three different image scales for making pre- dictions. The visual representation of AgriSegNet is shown in Fig. 1.

Deep learning techniques have been successfully utilized for numerous computer vision applications. Consequently, several works have also developed vision-based solutions for agri- cultural domain. Combination of deep learning with remote sensing and imaging technology can greatly support farm maintenance through analysis and prediction of farmland and crop parameters. From the UAV mounted sensors, the farmers can get data on moisture, humidity, and several other parame-

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:39:56 UTC from IEEE Xplore.  Restrictions apply.

ANAND et al.: AgriSegNet: DEEP AERIAL SEMANTIC SEGMENTATION FRAMEWORK 17583

of efﬁcient and effective algorithms are needed for aerial semantic segmentation.

B. Related Work

Sinha and Dolz [22] proposed a multi-scale attention model with guided attention for medical image segmentation. A novel attention gate model for medical imaging was proposed by Schlemper et al. [23], which focuses on target structures of varying sizes and shape. Wei et al. [24] utilized road struc- ture reﬁned convolutional neural network (RSRCNN) model for road extraction in aerial scenes. Tschannen et al. [25] proposed a structured CNN architecture consisting of a tree-like CNN feature extractor for semantic segmentation. Kaul et al. proposed a technique for incorporation of attention within CNNs using feature maps generated using a separate convolutional autoencoder [26]. Chen et al. have presented multi-modal data as input for Residual Shufﬂing Convolutional Neural Networks [27]. Rahnemoonfar et al. [28] presented the amalgamation of densely connected RNN and CNN net- works in order to semantically segment objects from aerial images of ﬂooded areas in Houston, TX. Niu [29] pro- posed an attention-based framework named Hybrid Multiple Attention Network for adaptively capturing global correlations from channel, category and space perspective in an effective manner. Chai et al. [30] discuss semantic segmentation of high-resolution aerial images using DCNN predicted distance maps. Furthermore, Alom et al. [31] proposed a U-Net based Recurrent Residual Convolutional Neural Network, named R2U-Net. The proposed model utilized a combination of Residual Networks, UNets and RCNN.

Fig. 2. Sample images from the Agriculture-vision challenge dataset. The segmentation for various ﬁeld anomalies: 1. cloud shadow, 2. double plant, 3. planter skip, 4. standing water, 5. waterway, 6. weed cluster.

We have used Agriculture-vision challenge dataset to iden- tify the anomalies in farmland which can help farmers in judiciously planning cultivation pattern for their crops [17]. The dataset comprises of different types of anomalies such as cloud shadow, double plant, standing water, etc. Fig. 2 shows the same images of farmland anomalies from the Agriculture-vision challenge dataset. The potential yield of farmlands and cultivation patterns are heavily impacted by these farmland anomalies. Hence, it is extremely important to locate them accurately.

II. MOTIVATION AND RELATED WORK A. Motivation

Recently, several novel works have been proposed in the domain of IoT-assisted smart agriculture. Murugan et al. [32] proposed a precision agriculture monitoring approach using satellite data in combination with drone-acquired data. Mehmood et al. [33] proposed a deep learning based light weight system for energy-constrained devices. Keshwani et al. [34] proposed an observance technique for timely data acquisitions and agricultural information stor- age. Their work utilized a structural similarity based water valve management mechanism which is used to locate farm regions with water deﬁciency. Pirbhulal et al. [35] proposed a resource allocation model for IoT based systems taking into consideration several parameters for proper optimization in terms of resource allocation. Sodhro [36] proposed a novel architecture of smart city system along with HABP and DS Algorithms adopting stored vedio stream. Hassan et al. [37] proposed a downsampler-encoder-based data generator trained to ensure better capture of actual distribution of attack models for the large IIoT attack surface. Moreover, Latif [4] present a detailed study on challenges and future direction pertaining to Unmanned Aerial Systems (UAS). Also. Oliveira et al. [38] propose a study of medium access control (MAC) layer protocols that are used in IoT. Han et al. [15] a study on application of certain emerging communication technologies in UAV Systems. [39] propose a matching theory based task ofﬂoading strategy (METO) that aims to reduce the total system energy and number of outages in an IoT-Fog interconnection network.

Inclusion of deep learning techniques have signiﬁcantly impacted the development of IoT-based smart systems [18]. Consequently, computer vision based systems for agricultural studies has seen unprecedented interest in recent years [19], [20]. More speciﬁcally, semantic segmentation plays a crucial role in higher-level decision makings in remote sensing for agricultural land monitoring [21]. Smart agriculture market is estimated to grow from 13.8 billion USD in 2020 to 22.0 billion USD by 2025. Across the globe, farmers are increasingly adopting advanced farming equipment such as guidance technology, display devices, sensors and farm man- agement software. Moreover, market for agriculture drones is estimated to reach 3.6 billion USD by 2027 exhibiting a growth rate of 18.14%. Our work can be greatly helpful in case of farmland anomaly detection to allow farmers to decide better crop rotation patterns, land usage patterns and other factors of agricultural planning. This work is motivated by the scope of aerial vision based solutions for precision agriculture. The technological advancement of semantic seg- mentation algorithms have led to improved performance for pattern recognition for aerial images. The existing approaches have used combination of attention schemes, residual networks and U-Net to obtain better accuracy of predictions. However, the aerial images present several challenges, such as object shape variations, complex background, large ﬁeld-of-view, high-density of objects, etc. [17]. Therefore, development

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:39:56 UTC from IEEE Xplore.  Restrictions apply.

17584 IEEE SENSORS JOURNAL, VOL. 21, NO. 16, AUGUST 15, 2021

Fig. 3. The proposed AgriSegNet architecture for training. The higher scale image is passed on to the segmentation head after feature extraction from the backbone network. The Attention Module of the next lower scale unit is useful for combining features from  . × scaled image and × scaled image. Results of the attention logits are multiplied with the segmentation head logits for lower scale and its complement if used for attending the higher scale logits.

III. AGRISEGNET NETWORK We propose AgriSegNet for semantic segmentation of farm- land from aerial view. The detailed description of the proposed AgriSegNet is presented below.

TABLE I LAYER BREAKDOWN OF THE SEGMENTATION HEAD

A. Overview

Multi-scale inputs with attention were introduced by Chen et al. [40], where three different image scales were used in training process (called as explicit model). In our network we use two image scales for training and three image scales during inference. This approach is known as a hierarchical model. We derive a pixel-wise dense relative attention between the lower and higher image scales by using image features obtained from the lower scale image. In order to obtain the differently scaled images, we scale down the original input image by a factor of 2 to obtain a 0.5× scaled input image along with the original 1× scaled input image. This enables our network to learn the relative attention for a range of dif- ferent image scales. During the inference, the learnt attention is hierarchically applied in order to combine predictions with respect to multiple scales together, in successive computations.


## architecture for training and inference has been presented in

Fig. 3 and Fig. 4, respectively.

B. AgriSegNet Architecture

We use DeepLabV3+ with ResNet50 (Output Channels = 128, Output Stride = 8) as the feature extraction backbone in the training model. This backbone is fed with 4 image channels which include RGB (3 channels) and NIR (Near- Infrared) frequency ranges. The larger scale image was passed on to the feature extraction backbone network, whose feature maps were further passed to a segmentation head. The lower scale image was also passed on to the backbone network with weights shared with the backbone used for larger scale image. However, for the lower scale images, the feature maps were passed on to the segmentation head as well as the attention head. We discuss the segmentation and attention head modules in the below Subsections.

Attention is an effective mechanism for selecting signiﬁcant features for deep learning tasks. Attention mechanism used in our AgriSegNet selects task-speciﬁc features from the multi-scale features extracted using the backbone network, which signiﬁcantly outperforms max-pooling and average pooling. It also helps us in visualizing the signiﬁcance of features at different scale and positions. It should be noted that image features at one position may not always be signiﬁcant within one particular image scale but may have signiﬁcance in another image scale [40]. Hence, our proposed attention mechanism learns attention prediction between adjacent scale pairs. Uniﬁcation of multi-scale features in CNNs has been instrumental in achieving state of the art results for complex computer vision problems [41]. Moreover, using multi-scale inference in computer vision models is helpful in achieving the best results. Thus, we utilize multiple image scales in our network and combine the results by utilizing attention mechanism. The graphical representation of the proposed

1) Segmentation Head: We utilize a fully convolutional layer for semantic predictions which consists of two blocks with 3 × 3 convolutional and batch normalization. The ﬁnal layer computes 1 × 1 convolution with channels equal to the number of classes to be segmented. The output is further generated, coupled with the attention maps and other image scale semantic logits, which is passed on to a Softmax layer. Table I presents a complete layer wise breakdown of the Segmentation Head.

2) Attention Head: The attention head has a similar structure to the segmentation head, with the exception that the ﬁnal layer involving 1×1 convolution has a single channel present, since

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:39:56 UTC from IEEE Xplore.  Restrictions apply.

ANAND et al.: AgriSegNet: DEEP AERIAL SEMANTIC SEGMENTATION FRAMEWORK 17585

Fig. 4. The proposed AgriSegNet architecture for inference. DeepLabV3+ backbone is used for feature extraction from all the three image scales. Further, the extracted features are passed on to segmentation head and attention head module. The largest image scale (1.0 here) is passed only to the segmentation head and the output is combined with attention applied segmentation head outputs of the next successive lower scales (0.25 and 0.5 here). The ﬁnal result of all the hierarchical combinations are passed on to the SoftMax Activation layer for the computation of segmentation.

(1-α) for each scale (lower), were combined to generate the output during training as per the relation given in Eq. 1.

TABLE II LAYER BREAKDOWN OF THE ATTENTION HEAD

Output = U(Lr=0.5 ∗αr=0.5) + Lr=1.0 ∗U(1 −αr=0.5) (1)

where U represents bilinear upsampling to the same scale as that of the logits from the previous stage.

We obtain signiﬁcant improvement in the efﬁciency of training using the hierarchical/chained structure in comparison to the categorical multi-scale attention methodology [40]. Hence, on using image scales of 0.25,0.5,1.0, the training cost is higher in case of explicit model while our hierarchical methodology employs only 2 image scales (0.5×, 1.0×) for learning relative attention, which indicates signiﬁcant perfor- mance improvement in terms of training.

we are predicting attention (during training) using a single image scale (lower) to learn the contribution of the next higher scale. The output is further passed on to a Sigmoid layer as parameters of the attention map ranges in [0,1]. The weights of the attention map reﬂect the importance of features at a particular scale and position. Thus, the amount of pixel-wise attention to be paid to features at different scales and position is decided by the attention module. This enables visualization of attention for each scale by visualizing the predicted logits. Table II presents a complete layer wise breakdown of the Attention Head.

2) Inference: We perform inference in a chained manner by combining predictions of multiple image scale. In order to perform evaluation, we utilize images scaled (bi-linearly) at 0.25×, 0.5× and 1.0×. Lower scale computations are given higher precedence and we move successively to higher scale computations due to their elevated global context, which would be instrumental in result reﬁnement. Moreover, it is possible to use a different image scaling other than those used, 2.0× or 0.125× can also be added to derive inferences. However, unlike the explicit method [40], our proposed methodology does not require re-training the network with newer scales. Scale relative training for two image scales is sufﬁcient for carrying inferences at multiple stages in a hierarchical manner. During inference, we can ﬂexibly select the scaling of the image to be used. Therefore, it is possible to add new scales (e.g. 0.125× or 2.0×) to a model trained with 0.5× and 1.0× image scaling through our proposed multi-scale

C. Training and Inference

1) Training: By utilizing the image features from a single lower scale image (scale = 0.5×), a pixel-wise dense relative attention is predicted between the lower (0.5×) image scale and the larger (1.0×) image scale. This predicted attention masks were applied to the segmentation head outputs. The generated segmentation logits (represented by L) and the attention mask (represented by α) along with its complement

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:39:56 UTC from IEEE Xplore.  Restrictions apply.

17586 IEEE SENSORS JOURNAL, VOL. 21, NO. 16, AUGUST 15, 2021

TABLE III CONFUSION MATRIX FOR THE PREDICTION OF SEMANTIC LABELS IN AGRIVISION DATASET. THE ROW HEADERS

INDICATE THE TRUE LABELS, AND THE COLUMN HEADERS INDICATE THE PREDICTED LABELS

attention based architecture hierarchically, which differs from the previously reported methodologies which were limited to use of the same scale of images for model training and inference.

TABLE IV TRAINING PARAMETERS USED FOR THE PROPOSED NETWORK

IV. RESULTS AND DISCUSSION In this section, we ﬁrst give a brief description of the Agriculture-vision challenge dataset along with the deﬁned evaluation metrics.

A. Dataset and Evaluation Metrics

B. Implementation Details

We use the Agriculture-Vision challenge dataset [17] for training and evaluation of the proposed methodology. It con- sists of 21,061 farmland images captured across the United States during the year 2019. Each image comprises of four 512 × 512 color channels, which include RGB and Near Infra-red (NIR). The images also accompany a boundary map and binary mask. The boundary map shows the region of the farmland within the image, while the binary mask displays the valid pixels within the image. We do not evaluate the regions lying outside either the boundary map or the mask. Seven categories of annotations are included, viz., background, double plant, cloud shadow, waterway, planter skip, weed cluster and standing water. The model is evaluated on the validation set, which consists of 4,431 NIR-RGB images and test set, which includes 3,729 images. For the purpose of training, the data was augmented by horizontal and vertical ﬂip, rotation by 90 degrees and hue and saturation values in the image were randomly shifted by appropriate values (with a probability of 50 %). We use mean Intersection-over- Union (mIoU) as the primary quantitative evaluation metric, which is calculated as mean value of IoU for each predicted segmentation across all the images. IoU is computed as given in Eq. 2.

The model is implemented in the PyTorch framework. We train the model using mini batches of size 4. We uni- formly rescale the training data (which contains 12901 images) using bilinear upsampling for the images. The training images were randomly ﬂipped, rotated and hue-saturation values were shifted (with a probability of 0.5) in order to perform data augmentation and also shufﬂed for each epoch. Weights are initialized using the glorot initialization, and the biases are initialized with zeros. We used combination of dice loss and adaptive class weighting loss [44] as our loss function during training. The use of adaptive class weighting loss helps in addressing problems where distribution of classes in segmentation is highly imbalanced. The dice loss considers loss information both globally and locally, which is criti- cal for obtaining high accuracy. The dice loss is computed using Eq. 4.

N

i=1 2 ∗|pi| ∗|ti| N

Ldice = 1 −

(4)

i=1 |pi| + |ti|

where pi and ti represent corresponding sum of pixel values for output logits and target labels, respectively for each class and N represents the total number of classes. If the adaptive class weighting loss is denoted as Lacw and dice loss by Ldice, the total loss is computed using Eq. 5.

 Area(Pc ∩Tc)

IoU = 1

Area(Pc ∪Tc) (2)

C

Ltotal = Lacw + Ldice (5)

where C represents the number of classes in the Image Segmentation, Pc is the Prediction Segmentation and Tc is the Target Segmentation.

The model is trained on Nvidia Titan XP GPU. It took roughly 144 hours to train our model for 60 epochs with batch size 4 over 12,901 NIR-RGB training images. The trajectory for training loss for our implementation has been presented in Fig. 5. Also, Table IV presents the values of training parameters used for the proposed network. The loss function is optimized using SGD optimizer. To train our network, the initial learning rate was set at 1e −2. We used

We also present the confusion matrix as shown in Table III, where each entry is calculated as:

Vij = No. of pixels from class i predicted as class j

Total no. pixels of class i in true segmentation (3)

where, Vij represents an entry for row i and column j within Table III.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:39:56 UTC from IEEE Xplore.  Restrictions apply.

ANAND et al.: AgriSegNet: DEEP AERIAL SEMANTIC SEGMENTATION FRAMEWORK 17587

TABLE V CLASS-WISE IOU ON VAL SET (OS STANDS FOR OUTPUT STRIDE)

TABLE VI CLASS-WISE IOU ON TEST SET (OS STANDS FOR OUTPUT STRIDE)

TABLE VII TEST SET MIOUS OF VARIOUS MODIFIED SEMANTIC SEGMENTATION

APPROACHES [17] ALONG WITH OUR MODEL

Fig. 5. The training graph of the proposed AgriSegNet network.

TABLE VIII TEST SET MIOUS OF FPN BASED MODEL [17] WITH VARIOUS

the cosine annealing learning rate scheduler while training our model.

RESNET BACKBONES ALONG WITH OUR MODEL

C. Quantitative Results

The performance of our proposed AgriSegNet is illustrated in Table V, Table VI, Table VIII, Table III and Table VII. Highlighted values in Table III represent the pixel accuracy values for each individual class segmentations for validation set. The proposed method remarkably outperforms the mod- iﬁed semantic segmentation models such as DeepLabV3 and DeepLabV3+ (with output strides of 8 and 16). We also compare our work with FPN architecture as proposed in [17] a novel encoder-decoder architecture using EfﬁcientNet and feature pyramid decoder [42] as well as Additive group normalisation (AGN) [43] based state of the art segmentation approaches in Table V, Table VI and Table VII. We obtain an mIoU of 51.7% (on validation set) and 50.20% (on test set) for weed cluster segmentation, which surpasses results as proposed in [17] by 23.37% on validation set and 19.33% on test set. Similar degree of improvements are seen for double plant segmentation, where our method surpasses segmentation results of FPN-based model [17] by 27.03% in validation and 18.52% in test set. For test set, the obtained mIoU is 47.96%. For validation set, our predicted segmentation obtained a dice

score/F1 score of 67%. As seen in Table VIII, our network’s performance is superior to FPN-based model in terms of test set mIoU. Speciﬁcally, it achieves 9.7%, 6.62%, 6.14%, 8.33%, 7.91%, and 4.3% higher mIoU for test set as com- pared to FPN with different ResNet backbones. Also, as per Table VII, our model achieves 15.78%, 8.91%, 5.74%, and 5.54% higher mIoU as compared to several modiﬁed semantic segmentation models as presented in Table VII. In case of cloud shadow segmentation, our proposed model achieves IoU of 49.12% on validation set and 46.3% on test Set. For planter skip segmentation, our results in test set are as low as 8.68%, which is due to shallow color distinction of image features for planter skip class to those of the associated image backgrounds which can be inferred from Table III where 45% of planter

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:39:56 UTC from IEEE Xplore.  Restrictions apply.

17588 IEEE SENSORS JOURNAL, VOL. 21, NO. 16, AUGUST 15, 2021

Fig. 6. Qualitative results of the proposed AgriSegNet on the Agriculture-vision challenge dataset.

skip pixels have been classiﬁed as background in validation set. Moreover, for waterway segmentation, we were not able to achieve a considerably better results in comparison to other state of the art models due to similarity in image features for weed clusters and waterway anomalies, which can be inferred from Table III 43% of waterway pixels have been wrongly classiﬁed as weed clusters. For classes such as weed clusters, double plant and cloud shadow 25%, 24% and 28% of the associated image pixels have been wrongly classiﬁed as background respectively. For cases where class segmentation are considerably larger, our predictions are quite accurate and robust.

the image predictions. However, despite of similarity in image features for waterway and weed cluster, robust segmentation have been generated with some erroneous predictions along the corners with background class. It is noteworthy that high accuracy in results has been achieved in spite of the class imbalance within the Agriculture-vision challenge dataset. While annotations for classes such as weed cluster have macroscopic segmentation, and are more in terms of number of images, some classes such as planter skip have microscopic context and present in very few images. Hence, the use of multi scale attention module along with consideration of adaptive class weighting loss was helpful in achieving outstanding results, and smaller sized classes are robustly segmented by our network as shown in Fig. 6.

D. Qualitative Results

V. CONCLUSION This work presents an efﬁcient deep learning frame- work AgriSegNet for agricultural pattern recognition in UAV acquired images. The network utilizes multi-scale attention for semantic segmentation of aerial images. Agriculture-vision challenge dataset was used for evaluation of the proposed network. The developed architecture is able to obtain higher IoU due to the inclusion of multi scale attention module and adaptive class weighting loss in combination with dice loss. These modules help optimizing the model training in the presence of class imbalance in the training set. We use a hierarchical model which helped the network in learning a relative attention scheme from a range of different image scales. Thus, in the case of change in the image quality (image scale or resolution), retraining the cloud GPU Server would

The multi scale attention based learning in AgriSegNet gives accurate predictions in cases where the class based pixel occurrence is lower than the rest of the image span. As seen in Fig. 6, rectangular subsection occupied by planter skip segmentation has been robustly segmented with respect to location and shape. For double plant segmentation, despite of having smaller region of interest and complex occurrence pattern, our model has accurately predicted the segmentation. Segmentation predictions for classes such as weed clusters, cloud shadow with much larger segmentation area are also precise. Our proposed model predicts presence of standing water on the farm ﬁeld despite of it shallowness as seen in Fig. 6, which has been ignored in case of target segmentation for the same image. Moreover, cases pertaining to complex shape occurrences have been dealt with in great detail as per

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:39:56 UTC from IEEE Xplore.  Restrictions apply.

ANAND et al.: AgriSegNet: DEEP AERIAL SEMANTIC SEGMENTATION FRAMEWORK 17589

not be necessary. This can be greatly effective for precision agricultural practices, which require resource allocation costs to be lower. The developed architecture facilitates automatic detection of farmland anomalies, which is helpful in formu- lating efﬁcient agricultural plans and abate challenges posed to the farmers due to changing environmental conditions.

[20] Y.-Y. Zheng, J.-L. Kong, X.-B. Jin, X.-Y. Wang, and M. Zuo,

“CropDeep: The crop vision dataset for deep-learning-based classiﬁ- cation and detection in precision agriculture,” Sensors, vol. 19, no. 5, p. 1058, Mar. 2019. [21] N. Kussul, M. Lavreniuk, S. Skakun, and A. Shelestov, “Deep learn-

ing classiﬁcation of land cover and crop types using remote sensing data,” IEEE Geosci. Remote Sens. Lett., vol. 14, no. 5, pp. 778–782, May 2017. [22] A. Sinha and J. Dolz, “Multi-scale self-guided attention for med-

ical image segmentation,” 2019, arXiv:1906.02849. [Online]. Available: http://arxiv.org/abs/1906.02849 [23] J. Schlemper et al., “Attention gated networks: Learning to lever-


## REFERENCES

[1] K. Nonami, F. Kendoul, S. Suzuki, W. Wang, and D. Nakazawa,

age salient regions in medical images,” Med. Image Anal., vol. 53, pp. 197–207, Apr. 2019. [24] Y. Wei, Z. Wang, and M. Xu, “Road structure reﬁned CNN for road

Autonomous Flying Robots: Unmanned Aerial Vehicles and Micro Aerial Vehicles. New York, NY, USA: Springer, 2010. [2] S. Candiago, F. Remondino, M. D. Giglio, M. Dubbini, and M. Gattelli,

extraction in aerial image,” IEEE Geosci. Remote Sens. Lett., vol. 14, no. 5, pp. 709–713, May 2017. [25] M. Tschannen, L. Cavigelli, F. Mentzer, T. Wiatowski, and L. Benini,

“Evaluating multispectral images and vegetation indices for precision farming applications from UAV images,” Remote Sens., vol. 7, no. 4, pp. 4026–4047, 2015. [3] A. Gupta, H. P. Gupta, P. Kumari, R. Mishra, S. Saraswat, and T. Dutta,

“Deep structured features for semantic segmentation,” in Proc. 25th Eur. Signal Process. Conf. (EUSIPCO), Aug. 2017, pp. 61–65. [26] C. Kaul, S. Manandhar, and N. Pears, “FocusNet: An attention-based

“A real-time precision agriculture monitoring system using mobile sink in WSNs,” in Proc. IEEE Int. Conf. Adv. Netw. Telecommun. Syst. (ANTS), Dec. 2018, pp. 1–5. [4] M. A. Latif, “An agricultural perspective on ﬂying sensors: State of the

fully convolutional network for medical image segmentation,” in Proc. IEEE 16th Int. Symp. Biomed. Imag. (ISBI), Apr. 2019, pp. 455–458. [27] K. Chen et al., “Residual shufﬂing convolutional neural networks

art, challenges, and future directions,” IEEE Geosci. Remote Sens. Mag., vol. 6, no. 4, pp. 10–22, Dec. 2018. [5] C. A. F. Ezequiel et al., “UAV aerial imaging applications for

for deep semantic image segmentation using multi-modal data,” ISPRS Ann. Photogramm., Remote Sens. Spatial Inf. Sci., vols. 4–2, pp. 65–72, May 2018. [Online]. Available: https://www.isprs-ann- photogramm-remote-sens-spatial-inf-sci.net/IV-2/65/2018/ [28] M. Rahnemoonfar, R. Murphy, M. V. Miquel, D. Dobbs, and A. Adams,

post-disaster assessment, environmental management and infrastructure development,” in Proc. Int. Conf. Unmanned Aircr. Syst. (ICUAS), May 2014, pp. 274–283. [6] M. Mandal, M. Shah, P. Meena, and S. K. Vipparthi, “SSSDET:

“Flooded area detection from UAV images based on densely connected recurrent neural networks,” in Proc. IGARSS-IEEE Int. Geosci. Remote Sens. Symp., Jul. 2018, pp. 1788–1791. [29] R. Niu, X. Sun, Y. Tian, W. Diao, K. Chen, and K. Fu, “Hybrid multiple

Simple short and shallow network for resource efﬁcient vehicle detection in aerial scenes,” in Proc. IEEE Int. Conf. Image Process. (ICIP), Sep. 2019, pp. 3098–3102. [7] M. Mandal, M. Shah, P. Meena, S. Devi, and S. K. Vipparthi, “AVDNet:

attention network for semantic segmentation in aerial images,” 2020, arXiv:2001.02870. [Online]. Available: http://arxiv.org/abs/2001.02870 [30] D. Chai, S. Newsam, and J. Huang, “Aerial image semantic segmentation

A small-sized vehicle detection network for aerial visual data,” IEEE Geosci. Remote Sens. Lett., vol. 17, no. 3, pp. 494–498, Mar. 2020. [8] S. J. Kim and G. J. Lim, “Drone-aided border surveillance with an

using DCNN predicted distance maps,” ISPRS J. Photogramm. Remote Sens., vol. 161, pp. 309–322, Mar. 2020. [31] M. Z. Alom, C. Yakopcic, M. Hasan, T. M. Taha, and V. K. Asari,

electriﬁcation line battery charging system,” J. Intell. Robot. Syst., vol. 92, nos. 3–4, pp. 657–670, Dec. 2018. [9] Y. Zhong et al., “Mini-UAV-borne hyperspectral remote sensing: From

“Recurrent residual U-Net for medical image segmentation,” J. Med. Imag., vol. 6, no. 1, Jan. 2019, Art. no. 014006. [Online]. Available: https://pubmed.ncbi.nlm.nih.gov/30944843/, doi: 10.1117/1.JMI.6.1.014006. [32] D. Murugan, A. Garg, and D. Singh, “Development of an adaptive

observation and processing to applications,” IEEE Geosci. Remote Sens. Mag., vol. 6, no. 4, pp. 46–62, Dec. 2018. [10] R. Mishra, H. P. Gupta, and T. Dutta, “A road health monitoring system

using sensors in optimal deep neural network,” IEEE Sensors J., early access, 2020, doi: 10.1109/JSEN.2020.3005998. [11] R. Bagi, T. Dutta, and H. P. Gupta, “Deep learning architectures for

approach for precision agriculture monitoring with drone and satellite data,” IEEE J. Sel. Topics Appl. Earth Observ. Remote Sens., vol. 10, no. 12, pp. 5322–5328, Dec. 2017. [33] I. Mehmood et al., “Efﬁcient image recognition and retrieval on

computer vision applications: A study,” in Advances in Data and Infor- mation Sciences. New York, NY, USA: Springer, 2020, pp. 601–612. [12] H. M. Jawad et al., “Accurate empirical path-loss model based

IoT-assisted energy-constrained platforms from big data reposito- ries,” IEEE Internet Things J., vol. 6, no. 6, pp. 9246–9255, Dec. 2019. [34] B. Keswani et al., “Adapting weather conditions based IoT enabled

on particle swarm optimization for wireless sensor networks in smart agriculture,” IEEE Sensors J., vol. 20, no. 1, pp. 552–561, Jan. 2020. [13] P. Garg, A. S. Chakravarthy, M. Mandal, P. Narang, V. Chamola, and

smart irrigation technique in precision agriculture mechanisms,” Neural Comput. Appl., vol. 31, no. 1, pp. 277–292, Jan. 2019. [35] S. Pirbhulal, W. Wu, K. Muhammad, I. Mehmood, G. Li, and

M. Guizani, “ISDNet: AI-enabled instance segmentation of aerial scenes for smart cities,” ACM Trans. Internet Technol, vol. 1, no. 1, pp. 1–19, 2020. [14] M. J. Sobouti et al., “Efﬁcient deployment of small cell base sta-

V. H. C. D. Albuquerque, “Mobility enabled security for optimizing IoT based intelligent applications,” IEEE Netw., vol. 34, no. 2, pp. 72–77, Mar. 2020. [36] A. H. Sodhro, S. Pirbhulal, Z. Luo, and V. H. C. D. Albuquerque,

tions mounted on unmanned aerial vehicles for the Internet of Things infrastructure,” IEEE Sensors J., vol. 20, no. 13, pp. 7460–7471, Jul. 2020. [15] T. Han et al., “Emerging drone trends for blockchain-based 5G networks:

“Towards an optimal resource management for IoT based green and sustainable smart cities,” J. Cleaner Prod., vol. 220, pp. 1167–1179, May 2019. [37] M. M. Hassan, M. R. Hassan, S. Huda, and V. H. C. D. Albuquerque,

Open issues and future perspectives,” IEEE Netw., vol. 35, no. 1, pp. 38–43, Jan./Feb. 2021. [16] H. Tian, T. Wang, Y. Liu, X. Qiao, and Y. Li, “Computer vision tech-

“A robust deep learning enabled trust-boundary protection for adversarial industrial IoT environment,” IEEE Internet Things J., early access, Aug. 24, 2020, doi: 10.1109/JIOT.2020.3019225. [38] L. Oliveira, J. Rodrigues, S. Kozlov, R. Rabelo, and V. Albuquerque,

nology in agricultural automation—A review,” Inf. Process. Agricult., vol. 7, no. 1, pp. 1–19, 2020. [17] M. T. Chiu et al., “Agriculture-vision: A large aerial image database for

“MAC layer protocols for Internet of Things: A survey,” Future Internet, vol. 11, no. 1, p. 16, Jan. 2019. [39] C. Swain et al., “METO: Matching theory based efﬁcient task ofﬂoading

agricultural pattern analysis,” in Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR), Jun. 2020, pp. 2828–2838. [18] E. Mavridou, E. Vrochidou, G. A. Papakostas, T. Pachidis, and

in IoT-fog interconnection networks,” IEEE Internet Things J., early access, Sep. 21, 2020, doi: 10.1109/JIOT.2020.3025631. [40] L.-C. Chen, Y. Yang, J. Wang, W. Xu, and A. L. Yuille, “Atten-

V. G. Kaburlasos, “Machine vision systems in precision agriculture for crop farming,” J. Imag., vol. 5, no. 12, p. 89, Dec. 2019. [19] A. Kamilaris and F. X. Prenafeta-Boldú, “Deep learning in agricul-

tion to scale: Scale-aware semantic image segmentation,” in Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR), Jun. 2016, pp. 3640–3649.

ture: A survey,” Comput. Electron. Agricult., vol. 147, pp. 70–90, Apr. 2018.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:39:56 UTC from IEEE Xplore.  Restrictions apply.

17590 IEEE SENSORS JOURNAL, VOL. 21, NO. 16, AUGUST 15, 2021

Murari Mandal (Member, IEEE) received the B.E. degree from the Birla Institute of Tech- nology and Science (BITS), Pilani, the M.E. degree from Thapar University, and the Ph.D. degree from MNIT Jaipur. He is a Postdoctoral Research Fellow with the National University of Singapore (NUS), Singapore. His research interests include deep learning, computer vision, and remote sensing.

[41] A. Tao, K. Sapra, and B. Catanzaro, “Hierarchical multi-scale attention

for semantic segmentation,” 2020, arXiv:2005.10821. [Online]. Avail- able: http://arxiv.org/abs/2005.10821 [42] M. T. Chiu et al., “The 1st agriculture-vision challenge: Methods and


## results,” in Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit.

(CVPR) Workshops, Jun. 2020. [Online]. Available: https://openaccess.
thecvf.com/content_CVPRW_2020/html/w5/Chiu_The_1st_Agriculture-
Vision_Challenge_ Methods_and_Results_CVPRW_2020_paper.html
[43] H. Sheng, X. Chen, J. Su, R. Rajagopal, and A. Ng, “Effective data

fusion with generalized vegetation index: Evidence from land cover segmentation in agriculture,” in Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. Workshops (CVPRW), Jun. 2020, pp. 267–276. [44] Q. Liu, M. C. Kampffmeyer, R. Jenssen, and A.-B. Salberg, “Multi-view self-constructing graph convolutional networks with adaptive class weighting loss for semantic segmentation,” in Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR) Workshops, Jun. 2020. [Online]. Available: https://openaccess.thecvf.com/content_ CVPRW_2020/html/w5/Liu_Multi-View_Self-Constructing_Graph_ Convolutional_Networks_With_Adaptive_Class_Weighting_Loss_ CVPRW_2020_paper.html

Vinay Chamola (Senior Member, IEEE) received the B.E. and M.E. degrees from the Birla Institute of Technology and Science (BITS), Pilani, India, in 2010 and 2013, respectively, and the Ph.D. degree from the National University of Singapore (NUS), Singapore, in 2016. He is an Assistant Professor with the EEE Department and APP- CAIR, BITS Pilani. His research interests include the IoT, 5G network management, blockchain, and security. He is also an Area Editor of the Ad Hoc Networks (Elsevier). He is also an Associate Editor of IEEE Internet of Things Magazine, IET Quantum Communica- tions, and IET Networks.

Tanmay Anand is currently pursuing the B.E. (Hons.) degree in electrical and electronics engi- neering with the Birla Institute of Technology and Science (BITS), Pilani. His research interests include computer architecture, deep learning, and hardware acceleration.

Fei Richard Yu (Fellow, IEEE) is a Professor with Carleton University, Canada. His research interests include blockchain, security, and green ICT. He has served as the technical program committee (TPC) co-chair of numerous con- ferences. He serves on the Editorial Board of several journals. He is also the Co-Editor- in-Chief for Ad Hoc & Sensor Wireless Net- works and a Lead Series Editor for IEEE TRANSACTIONS ON VEHICULAR TECHNOLOGY and IEEE COMMUNICATIONS SURVEYS and TUTORIALS.

Soumendu Sinha received the B.E. (Hons.) degree from the Birla Institute of Technology and Science (BITS), Pilani, and the M.Tech. degree from AcSIR, where he is currently pursuing the Ph.D. degree. He is working as a Scientist in the Semiconductor Devices Area at CSIR-CEERI, Pilani. His research interests are in the interdisci- plinary areas of solid state sensors, electrochem- ical sensors, mems, and machine learning.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:39:56 UTC from IEEE Xplore.  Restrictions apply.
