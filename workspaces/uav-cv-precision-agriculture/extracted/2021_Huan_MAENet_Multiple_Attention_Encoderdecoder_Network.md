---
workspace_id: SCI-001210
doi: 10.1109/lgrs.2021.3137522
title: 'MAENet: Multiple Attention Encoder-decoder Network for Farmland Segmentation
  of Remote Sensing Images'
authors:
- family_name: Huan
  given_name: Hai
  orcid: null
- family_name: Liu
  given_name: Yuan
  orcid: null
- family_name: Xie
  given_name: Yaqin
  orcid: null
- family_name: Wang
  given_name: Chao
  orcid: null
- family_name: Xu
  given_name: D.
  orcid: null
- family_name: Zhang
  given_name: Yi
  orcid: null
year: 2021
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:41.723213+00:00'
---

# MAENet: Multiple Attention Encoder-decoder Network for Farmland Segmentation of Remote Sensing Images

IEEE GEOSCIENCE AND REMOTE SENSING LETTERS, VOL. 19, 2022 2503005

MAENet: Multiple Attention Encoder–Decoder

Network for Farmland Segmentation

of Remote Sensing Images

Hai Huan , Member, IEEE, Yuan Liu, Yaqin Xie, Chao Wang, Dongdong Xu, and Yi Zhang

high-spatial-resolution remote sensing images is important for the development of smart agriculture.


## Abstract—With the rapid development of computer vision,

semantic segmentation as an important part of the technology
has made some achievements in different applications. However,
in the farmland segmentation scenario of remote sensing images,
the capability of common semantic segmentation methods in
restoring the farmland edge and identifying narrow farmland
ridges needs to be improved. Therefore, in this letter a semantic
segmentation method–multiple attention encoder–decoder net-
work (MAENet)–for farmland segmentation is proposed. The
design of a dual-pooling efﬁcient channel attention (DPECA)
module and its embedment in the backbone to improve the
efﬁciency of feature extraction is described; secondly, a dual-
feature attention (DFA) module is proposed to extract contextual
information of high-level features; ﬁnally, a global-guidance
information upsample (GIU) module is added to the decoder to
reduce the inﬂuence of redundant information on feature fusion.
We use three self-made farmland image datasets representing
UAV data to train MAENet and compare them with other
methods. The results show that the performances of segmentation
and generalization of MAENet are improved compared with
other methods. The MIoU and Kappa coefﬁcient in the farmland
multi-classiﬁcation test set can reach 93.74% and 96.74%.

The development of remote sensing image farmland seg- mentation is based on computer vision of image segmentation technology, which can be roughly divided into traditional algorithms and deep learning algorithms. Traditional algo- rithms [2] perform image segmentation by extracting low-level features in the image, such as color, texture, and shape. When remote sensing images have high spatial resolution against a complex background, parameters in traditional algorithms must be set artiﬁcially, making the method prone to over- segmentation. Recently, deep learning has developed rapidly in computer vision research. Semantic segmentation is the main research direction of deep learning in image segmentation work: it can extract deep semantic information from input images using convolutional neural networks (CNNs) [3], with high segmentation accuracy and efﬁciency. Some datasets and methods for terrain segmentation have been proposed in the study of farmland segmentation [4], [5]. However, the spatial resolution of these datasets is generally low, and they can only segment farmland, roads, water, etc., but fail to realize ﬁne segmentation of farmland and ridges, so in this letter an in-depth study of this problem is described.

Index Terms—Attention module, farmland segmentation, feature fusion, pyramid, UAV images.

In 2015, He et al. [6] proposed the residual network (ResNet) to avoid the problems of model overﬁtting and gradient explosion caused by increasing the depth of the network. Attention mechanisms can pay attention to global information and highlight the critical information needed, hence the research thereon. In 2017, Hu et al. [7] established the squeeze-and-excitation networks (SE-Net), which added a channel attention module to backbone and improved the efﬁciency of feature extraction. In 2018, the convolutional block attention module (CBAM) proposed by Liu et al. [8], Shi et al. [9], and Woo et al. [10] added global max-pooling to the SE module and introduced a spatial attention mechanism to extract position-related information within the feature map. In 2020, Wang et al. [11] found some local periodicity in the weights after global average-pooling by visualizing channel features, and thus proposed the efﬁcient channel attention (ECA) module as a replacement for the fully con- nected computation in the SE module with a 1-D convolution operation to facilitate information exchange between adjacent channels.

I. INTRODUCTION I

N RECENT years, with the wide application of AI in agriculture, smart agriculture has become a major research direction for modern and future agricultural development. The appearance of remote sensing by UAV is furthering the development of smart agriculture [1]. Farmland segmentation based on remote sensing images is an important research direction for smart agriculture and an important foundation of smart farmland management. Therefore, the study of an accurate farmland segmentation method that can be applied to

Manuscript received July 26, 2021; revised November 5, 2021; accepted December 17, 2021. Date of publication December 22, 2021; date of current version January 11, 2022. This work was supported in part by the National Natural Science Foundation of China under Grant 42176176, in part by the Guangxi Innovative Development Grand Grant, and in part by the Land Obser- vation Satellite Supporting Platform of National Civil Space Infrastructure Project. (Corresponding author: Dongdong Xu.)

Hai Huan and Dongdong Xu are with the School of Artiﬁcial Intelligence, Nanjing University of Information Science and Technology, Nanjing 210044, China (e-mail: haihuan@nuist.edu.cn; xdd@nuist.edu.cn).

Yuan Liu, Yaqin Xie, and Chao Wang are with the School of Electronic and Information Engineering, Nanjing University of Information Science and Technology, Nanjing 210044, China (e-mail: 20191219093@nuist.edu.cn; xyq@nuist.edu.cn; chaowang@nuist.edu.cn).

In 2014, Long et al. [12] developed the full convolutional network (FCN), the ﬁrst end-to-end semantic segmenta- tion network model. However, FCN cannot sufﬁciently extract contextual information. Both U-Net proposed by Ronneberger et al. [13] and Segnet proposed by Badrinarayanan et al. [14] used an encoder-decoder network

Yi Zhang is with the Nanjing Nanji Intelligent Agricultural Machin- ery Technology Research Institute, Nanjing 210008, China (e-mail: zhangy@jiagutech.com).

Digital Object Identiﬁer 10.1109/LGRS.2021.3137522

1558-0571 © 2021 IEEE. Personal use is permitted, but republication/redistribution requires IEEE permission. See https://www.ieee.org/publications/rights/index.html for more information.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:43:01 UTC from IEEE Xplore.  Restrictions apply.

2503005 IEEE GEOSCIENCE AND REMOTE SENSING LETTERS, VOL. 19, 2022

structure, which is a good solution to the problem of pixel spatial information loss. In 2017, PSPNet, proposed by Zhao et al. [15], used a pyramid pooling module, and in 2018, DeeplabV3+ proposed by Chen et al. [16] used atrous spatial pyramid pooling (ASPP). These backbone-style networks extract multi-scale semantic information and fuse it, but they only focus on spatial position information. In 2018, Fu et al. [17] proposed DANet using dual attention modules to simulate semantic interdependence in the spatial and channel dimensions, respectively. Li et al. [18] proposed the PAN model, which can recover object edge information using global attention upsampling (GAU) to assist low-level and high-level feature fusion in the decoding process. Although the aforementioned methods have facilitated some progress in the analysis of driverless and medical images, they cannot distinguish between farmland and weeds and accurately recover the farmland edge in the segmentation task of processing remote sensing farmland images with high interclass similarity.

Fig. 1. Detailed structure of our proposed MAENet.

In this letter, multiple attention encoder–decoder net- work (MAENet) is proposed for UAV image farmland segmen- tation. Compared with other semantic segmentation methods, our method can extract and fuse features efﬁciently, and improve the edge recovery of farmland. The main contribu- tions of this letter are demonstrated as follows.

Fig. 2. DPECA module.

pooling generates channel information statistics by compress- ing the spatial information within the channel to achieve channel description. Global max pooling can gather another important clue about distinctive object features to infer ﬁner channel-wise attention, following a published method [10]. To obtain the degree of association among channels after pooling, DPECA uses 1-D convolution to generate channel weights in each parallel branch. The experimental part of this letter discusses the setting of the 1-D convolutional kernel size in DPECA, and it is found that the performance improvement of the backbone is greatest when the convolutional kernel size is set to 3. After fusing the output of two parallel branches of DPECA, the output of this attention is obtained by multiplying it with the original feature map.

1) Combining with the actual needs, the land in the UAV images is divided to produce three farmland datasets with different spatial resolutions and different crop types. 2) Dual pooling efﬁcient channel attention (DPECA)- ResNet-50 is designed as backbone and a DPECA module is proposed. 3) A dual feature attention (DFA) module and a global-guidance Information Upsampling module are designed for multiple feature extraction and fusion in the decoding process.

DPECA is deﬁned as follows:

II. METHOD

M(X) = X · σ( f1×3(ga(X)) + f1×3(gm(X))). (1)

A. Data

In (1), X and M(X) are the input and output, both of size are W × H × C, W, H and C represent the width, height, and number of channels, f1×3 is the convolution ﬁlter of 1 × 3, ga and gm are the global average-pooling and global max- pooling, and σ is the Sigmoid activation function.

The image data presented here were captured with a DJI Phantom 4 RTK UAV. The imaging locations were south-west of Funan County, Fuyang City, Anhui Province (2018) and near Dapo Township, Qujing City, Yunnan Province (2020).

B. Network Architecture

Besides, the method of adding DPECA is discussed in this letter. Taking the ﬁrst residual module of ResNet-50 as an example, the common method of adding attention mechanisms is to add inside each residual block, as shown in Fig. 3(a). In contrast, in the present research, DPECA is added after each residual module, as shown in Fig. 3(b). Compared with the common method, our method not only improves the capability of discrimination of farmland edges and crop edges, but also slightly reduces the computational burden.

The model in this letter is the encoder–decoder structure. At ﬁrst, the encoder (backbone) extracts low-level features and high-level features from the input image. Secondly, in the center we use DFA to extract category information and multi- scale information from high-level features through a channel attention branch and pyramid attention branch to generate high-level features rich in contextual information. Then global- guidance information upsamples (GIUs) in the decoder grad- ually use the high-level features generated by DFA as a guide to weight the low-level features and then fuse them with the high-level features. Finally, the segmentation map is generated by upsampling. The overall structure of the network is shown in Fig. 1.

2) Center: In this letter, we propose the DFA module as the center between the encoder and decoder, which can both increase the focus of the model on small targets and improve the capability of discrimination between model categories. The structure of DFA is shown in Fig. 4, and the module consists of two parallel branches, pyramid attention and channel attention. Pyramid attention extracts features at three different scales by convolution of 3 × 3, 5 × 5, and 7 × 7, following a published letter [18]. The adjacent scale features of the pyramid structure are fused to generate pyramid features that are rich in contex- tual information. Then, the high-level features generated by

1) Encoder: The DPECA-ResNet-50 backbone is designed as an encoder in the present work. This structure consists of a DPECA and ResNet-50 which contains a convolution module and four residual modules (shown in yellow in Fig. 1). DPECA consists of two parallel branches of global average pooling and global max pooling, as shown in Fig. 2. Global average

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:43:01 UTC from IEEE Xplore.  Restrictions apply.

HUAN et al.: MAENet FOR FARMLAND SEGMENTATION OF REMOTE SENSING IMAGES 2503005

information after Sigmoid non-linear mapping. The channel weights after 1 × 1 convolution are multiplied with low- level features after convolution to attain the weighted low-level features. Then, the high-level features after upsampling are fused with the weighted low-level features. Finally, the third fused feature map is upsampled to generate the segmentation map. Compared with DeepLabV3+’s decoder structure for bilinear upsampling after channel merging, the decoder with this module can make better use of the position information in low-level features.

GIU is deﬁned as follows:

GIU(Xl, Xh) = f3×3(Xl) × f1×1(σ(ga(Xh) + gm(Xh))). (2)

Fig. 3. (a) Common method of adding attention mechanisms. (b) Our method of adding attention mechanisms.

In (2), Xl and Xh are low-level features and high-level feat- ures, f3×3 and f1×1 are 2-D convolutions of 3 × 3 and 1 × 1.

III. EXPERIMENTS Since there is no publicly available farmland segmentation dataset of high spatial resolution remote sensing images, three datasets with different scenarios and categories are produced and publicly available in this letter. In our dataset, farmland refers to agricultural land, including areas where no crops are grown. A ridge is deﬁned as an area that separates connected ﬁelds and forms an access road in the uncropped image. To verify the accuracy and robustness of our network, this model described in this letter is tested on each of the three datasets.

Fig. 4. DFA module structure. The blue and red lines represent the downsample and upsample operators, respectively.

A. Datasets

We crop the image data of the two imaging locations to 512 × 512 pixels, using a 12-pixel overlap, and divide (at random completely) the training and test sets in a 4:1 ratio. Dataset 1, with a total of 2420 images, is taken in the south-western part of Funan County with a spatial resolution of 15 cm. Dataset 2, with a total of 7264 images, is taken near Dapo Township with a spatial resolution of 2.92 cm. Datasets 1 and 2 are divided into two categories (farmland and background) representing low and high-resolution datasets, to achieve farmland segmentation at different spatial resolu- tions. Dataset 3 is divided into ﬁve categories according to the types of crops collected in Dataset 2, including background, three classes of tobacco, and other farmlands.

Fig. 5. GIU module structure. The red lines represent the upsample operators.

the backbone are multiplied with the pyramid features after 1 × 1 convolution to generate a multiscale feature map. High-level features embody much category information in the channel dimension, and high-level feature channels rich in this information are interrelated, so we use the channel attention module (CAM) [17] to extract the category infor- mation between high-level feature channels to improve the classiﬁcation capability of the network for indistinguishable samples. CAM is different from global pooling or an encoding layer to obtain channel relationships [19]. Instead, it frequently uses matrix operations and uses fewer parameters to extract the relationship information between channels. After CAM extracts channel information and performs 1 × 1 convolution, feature fusion is performed using a multi-scale high-level feature map with a pyramidal branch.

B. Training Setting

The experiments are mainly undertaken under the Keras framework based on Centos 7.8 system and run on an NVIDIA 2080TI with 11-GB video memory. The training process uses Adam as the optimizer: the batch size is set to 4, the initial learning rate is 0.0003, the loss function is cross-entropy, and the cosine annealing learning rate strategy is used. The network will converge within 30 batches in the two-category dataset and within 50 batches in Dataset 3.

C. Ablation Study

3) Decoder: Before the fusion of high-level and low-level features, in the decoder part a GIU module is proposed to weight the low-level features by using high-level features to enhance the focus of the network on key information. As shown in Fig. 5, ﬁrstly, GIU performs 3 × 3 con- volution on the low-level features and extracts them while reducing the number of channels. Secondly, the aggregated information is acquired by summing the results of global average-pooling and global max-pooling of high-level fea- tures. The channel weights are generated by the aggregated

To verify the effectiveness of each module, the model is tested for Dataset 1 and Dataset 2. We use IoU of the farmland category and Kappa coefﬁcient [20] as evaluation metrics. Table I lists the accuracies when adding and replacing modules to ResNet-50-PAN using it as a comparison baseline. Fig. 6 shows the visual results when adding different modules.

In the test results of Datasets 1 and 2, MAENet improves the IoU by 6.04% and 0.98%, and the Kappa coefﬁcient by 4.82% and 1.09%, compared with the baseline.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:43:01 UTC from IEEE Xplore.  Restrictions apply.

2503005 IEEE GEOSCIENCE AND REMOTE SENSING LETTERS, VOL. 19, 2022

TABLE I

TABLE II

ABLATION ANALYSES ON DATASETS 1 AND 2

COMPARISON WITH OTHER METHODS ON

DICHOTOMOUS FARMLAND DATASETS

Fig. 6. Comparison of ablation study results in datasets 1 and 2. (a) Orig- inal image. (b) ResNet-50-PAN. (c) Adding DPECA. (d) Adding DFA. (e) Adding GIU. (f) Ground truth.

Experiment 1 tests the addition of DPECA to the baseline using the method shown in Fig. 3(a). Experiment 2 tests different settings of the DPECA convolution kernel size. The value of k [11] in Table I can be deﬁned as







1 2

Fig. 7. Comparison of the results in datasets 1 and 2. (a) Original image. (b) FCN-8s. (c) DeepLabV3+. (d) DenseASPP. (e) PAN. (f) MAENet. (g) Ground truth.

k =

log2 (C) + 1

(3)

odd

where |t|odd indicates the nearest odd number of t, and C is the number of feature map channels. Since the number of channels in each residual block of backbone is greater than or equal to 64, k, as a constant, is greater than or equal to 3. Experimental results show that DPECA with a convolution kernel of 3 improves the accuracy of the evaluation.

Experiment 3 compares the different methods of adding DPECA. According to the experimental results, our method [see Fig. 3(b)] can improve network attention to farmland edges.

Fig. 8. Comparison of the results in dataset 3. (a) Original image. (b) FCN-8s. (c) DeepLabV3+. (d) DenseASPP. (e) PAN. (f) MAENet. (g) Ground truth.


## Experiments 4 and 5 replace the decoder in PAN with the

decoder proposed in this letter, and the test results show that
DFA and GIU can both improve the segmentation performance
of the network. Considering the effect of random error, ﬁve
replicate experiments for Experiments 4 and 5 are conducted,
and the data listed in Table I are the mean average values.
The standard deviation of each accuracy is also calculated. The
standard deviations in Experiment 4 are 0.08%, 0.05%, 0.04%,
and 0.03% (in order). The standard deviations in Experiment 5
are 0.15%, 0.12%, 0.03%, and 0.03% (in order).

On Dataset 1, only MAENet can accurately segment the connected ridge and better separate the two parcels of farm- land. The segmentation results on Dataset 2 show that other networks do not work well for narrow ridge segmentation and DeepLabV3+ cannot distinguish between farmland or a ridge because of the sparse crops in the farmland area, however MAENet still performs well and is closer to the ground truth.

Besides this, we performed tests on Dataset 3 (Table III lists the results): the segmentation result of MAENet is better than that of the other methods on Dataset 3. The two accuracy evaluation metrics reach 93.74% and 96.74%. From the IOU values of each category, the performance of MAENet is found to be improved compared with other methods except for the background category. In addition, the overall recog- nition capability of each method for Tobacco 2 is found to be low. It is found that there is a sample imbalance in Dataset 3, mainly because of the small number of samples of Tobacco 2. This leads to the low segmentation accuracy

D. Comparison and Analysis


> **Table II shows the segmentation performance of MAENet**

> compared with other methods in Datasets 1 and 2. The results
on both datasets show that MAENet achieves the best seg-
mentation results, with IoU of the farmland category reaching
92.48% and 96.49%, and Kappa coefﬁcient reaching 94.08%
and 95.25%.

Fig. 7 shows the segmentation results of the test sets of FCN-8s, DeepLabV3+, DenseASPP, PAN, and MAENet.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:43:01 UTC from IEEE Xplore.  Restrictions apply.

HUAN et al.: MAENet FOR FARMLAND SEGMENTATION OF REMOTE SENSING IMAGES 2503005

TABLE III

COMPARISON WITH OTHER METHODS ON DATASET 3

of each method in this category, thus reducing the MIoU. However, MAENet can obtain 84.89% of IOU in this category, which is greatly improved by 30.04% compared with Seg- Net, fully illustrating the classiﬁcation capability of MAENet for unbalanced datasets. Fig. 8 indicates that MAENet can distinguish Tobacco 2 and Tobacco 3 to a satisfactory extent and identify weeds that are more akin to the locally planted crops. In a sparsely planted crop farmland, global contextual information can be extracted more effectively than other methods to distinguish between farmland and a ridge between parcels of land.

[5] X.-Y. Tong, Q. Lu, G.-S. Xia, and L. Zhang, “Large-scale land

cover classiﬁcation in Gaofen-2 satellite imagery,” in Proc. IEEE Int. Geosci. Remote Sens. Symp. (IGARSS), Valencia, Spain, Jul. 2018, pp. 3599–3602. [6] K. He, X. Zhang, S. Ren, and J. Sun, “Deep residual learning for

image recognition,” in Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR), Las Vegas, NV, USA, Jun. 2016, pp. 770–778. [7] J. Hu, L. Shen, and G. Sun, “Squeeze-and-excitation networks,” in Proc.

IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR), Salt Lake City, UT, USA, Jun. 2018, pp. 7132–7141. [8] M. Liu, Q. Shi, A. Marinoni, D. He, X. Liu, and L. Zhang, “Super-

resolution-based change detection network with stacked attention mod- ule for images with different resolutions,” IEEE Trans. Geosci. Remote Sens., early access, Jul. 2, 2021, doi: 10.1109/TGRS.2021.3091758. [9] Q. Shi, M. Liu, S. Li, X. Liu, F. Wang, and L. Zhang, “A deeply super-

IV. CONCLUSION

vised attention metric-based network and an open aerial image dataset for remote sensing change detection,” IEEE Trans. Geosci. Remote Sens., early access, Jun. 29, 2021, doi: 10.1109/TGRS.2021.3085870. [10] S. Woo, J. Park, J.-Y. Lee, and I. S. Kweon, “CBAM: Convolutional

In this letter, we propose the use of MAENet for analysis of remote sensing images in farmland segmentation tasks. The network enhances the feature extraction capability of the network and improves the segmentation accuracy by adding DPECA. In the decoding process, a DFA module and GIU module are used to extract the contextual information of high-level features and fuse low-level features with high-level features to better effect. The experimental results show that the segmentation performance of the network meets practical requirements and there is a signiﬁcant improvement in the quality and accuracy of segmentation in the detail pertaining to that region of the farmland edge compared with other networks.

block attention module,” in Proc. Eur. Conf. Comput. Vis. (ECCV), Munich, Germany, Sep. 2018, pp. 3–19. [11] Q. Wang, B. Wu, P. Zhu, P. Li, W. Zuo, and Q. Hu, “ECA-Net: Efﬁcient

channel attention for deep convolutional neural networks,” in Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR), Seattle, WA, USA, Jun. 2020, pp. 11531–11539. [12] J. Long, E. Shelhamer, and T. Darrell, “Fully convolutional networks

for semantic segmentation,” in Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR), Boston, MA, USA, Jun. 2015, pp. 3431–3440. [13] O. Ronneberger, P. Fischer, and T. Brox, “U-Net: Convolutional net-

works for biomedical image segmentation,” in Proc. Int. Conf. Med. Image Comput. Comput.-Assist. Intervent. Cham, Switzerland: Springer, Oct. 2015, pp. 234–241. [14] V. Badrinarayanan, A. Kendall, and R. Cipolla, “SegNet: A deep

convolutional encoder-decoder architecture for image segmentation,” IEEE Trans. Pattern Anal. Mach. Intell., vol. 39, no. 12, pp. 2481–2495, Dec. 2017. [15] H. Zhao, J. Shi, X. Qi, X. Wang, and J. Jia, “Pyramid scene parsing

ACKNOWLEDGMENT

The dataset pertaining to farmland segmentation used in the research described in this letter is publicly available from: https://faculty.nuist.edu.cn/huanhai/zh_CN/zhym/62898/ list/index.htm

network,” in Proc. IEEE Conf. Comput. Vis. Pattern Recognit. (CVPR), Honolulu, HI, USA, Jul. 2017, pp. 6230–6239. [16] L.-C. Chen, Y. Zhu, G. Papandreou, F. Schroff, and H. Adam, “Encoder-

decoder with atrous separable convolution for semantic image segmen- tation,” in Proc. Eur. Conf. Comput. Vis. (ECCV), Munich, Germany, 2018, pp. 801–818. [17] J. Fu et al., “Dual attention network for scene segmentation,” in Proc.


## REFERENCES

IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR), Long Beach, CA, USA, Jun. 2019, pp. 3141–3149. [18] H. Li, P. Xiong, J. An, and L. Wang, “Pyramid attention network for

[1] P. Tripicchio, M. Satler, G. Dabisias, E. Ruffaldi, and C. A. Avizzano,

“Towards smart farming and sustainable agriculture with drones,” in Proc. Int. Conf. Intell. Environ., Prague, Czech Republic, Jul. 2015, pp. 140–143. [2] Z. Li, W. Shi, H. Zhang, and M. Hao, “Change detection based on Gabor

semantic segmentation,” 2018, arXiv:1805.10180. [19] H. Zhang et al., “Context encoding for semantic segmentation,” in Proc.

IEEE/CVF Conf. Comput. Vis. Pattern Recognit. (CVPR), Salt Lake City, UT, USA, Jun. 2018, pp. 7151–7160. [20] Y. Kim and Y. Kim, “Improved classiﬁcation accuracy based on the

wavelet features for very high resolution remote sensing images,” IEEE Geosci. Remote Sens. Lett., vol. 14, no. 5, pp. 783–787, May 2017. [3] A. Krizhevsky, I. Sutskever, and G. E. Hinton, “ImageNet classiﬁcation

output-level fusion of high-resolution satellite images and airborne LiDAR data in urban area,” IEEE Geosci. Remote Sens. Lett., vol. 11, no. 3, pp. 636–640, Mar. 2014. [21] M. Yang, K. Yu, C. Zhang, Z. Li, and K. Yang, “DenseASPP for

with deep convolutional neural networks,” Commun. ACM, vol. 60, no. 6, pp. 84–90, May 2017. [4] I. Demir et al., “DeepGlobe 2018: A challenge to parse the Earth

semantic segmentation in street scenes,” in Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit., Salt Lake City, UT, USA, Jun. 2018, pp. 3684–3692.

through satellite images,” in Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit. Workshops (CVPRW), Salt Lake City, UT, USA, Jun. 2018, pp. 172–181.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:43:01 UTC from IEEE Xplore.  Restrictions apply.
