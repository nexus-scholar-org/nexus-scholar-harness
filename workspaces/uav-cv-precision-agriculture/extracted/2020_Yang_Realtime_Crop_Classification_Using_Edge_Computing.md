---
workspace_id: SCI-001173
doi: 10.1109/ccnc46108.2020.9045498
title: Real-time Crop Classification Using Edge Computing and Deep Learning
authors:
- family_name: Yang
  given_name: Ming-Der
  orcid: null
- family_name: Tseng
  given_name: Hsin-Hung
  orcid: null
- family_name: Hsu
  given_name: Yu-Chun
  orcid: null
- family_name: Tseng
  given_name: W.
  orcid: null
year: 2020
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:41.674851+00:00'
---

# Real-time Crop Classification Using Edge Computing and Deep Learning

2020 IEEE 17th Annual Consumer Communications & Networking Conference (CCNC)

Real-time Crop Classification Using Edge

Computing and Deep Learning

Ming Der Yang   Department of Civil Engineering  National Chung Hsing University  Pervasive AI Research (PAIR) Labs

Hsin Hung Tseng  Department of Civil Engineering  National Chung Hsing University

Yu Chun Hsu  Department of Civil Engineering  National Chung Hsing University

Taichung, Taiwan  d108062001@mail.nchu.edu.tw

Taichung, Taiwan  d107062002@mail.nchu.edu.tw

Taichung, Taiwan  mdyang@nchu.edu.tw

Wei Chen Tseng  Department of Civil Engineering  National Chung Hsing University

Taichung, Taiwan  disapear1997@gmail.com

higher field usage and income, so the land land landscape  changes rapidly, the use of satellite imagery for crop species  surveys, limited by the low frequency of satellite access and  insufficient image resolution, making the application limited.


## Abstract—In recent years, edge computing and deep

learning have been successfully performed processing and 
classification tasks in a variety of fields including agriculture. 
Therefore, this research aims to use unmanned aerial vehicle 
(UAV) for agriculture applications with integrating edge 
computing and deep learning techniques. This research 
experiment was carried out in the NCHU Experimental Farm. 
The DJI Matrice 100 drone with ASUS Tinker Board S 
embedded system, which connects a Logitech C925e webcam to 
capture images are used in this study. The ASUS Tinker Board 
S runs a folder monitoring program and sends images over the 
4G LTE network to the backend server whenever new images 
are captured and stored. The backend server runs a pre-trained 
image semantic segmentation model and provides image 
inference service. The image inference results with the 
associated segmented image will be sent to the mobile device of 
the drone controller, and a dynamic flight control action can be 
triggered. The image semantic segmentation model adopts 
SegNet network architecture. For a comparison purpose, 
another network architecture, FCN-AlexNet, was also trained 
and 
validated. 
The 
preliminary 
results 
show 
SegNet 
outperformed FCN-AlexNet in image semantic segmentation 
tasks in terms of the evaluation between training and validation. 
The average inference speed of the semantic image segmentation 
model is 0.7s with segmentation identification accuracy is 89%. 
The promising results shed light on many agriculture 
applications, such as crop growth condition assessment, 
fertilizer management, and yield prediction. Additionally, this 
research provides possible solutions for the labor shortage issue 
of agriculture which is a common challenge in an aging 
community like Taiwan and many countries worldwide.

At present, the Taiwan government conducts agricultural  census frequency of five years, can not show the situation of  agricultural development in real time. In addition, the disaster  damage compensation mechanism is long and there is no  scientific evidence to judge. Therefore, this study uses the  uavor to carry the embedded system to carry out the real-time  image segmentation and identification of agricultural crops, so  as to get real-time information on crop types and distribution.

The goal of this study is to compare the multi-language  segmentation network architecture, and to use image testing  to find the neural network architecture most suitable for real- time marginal computation. This research area is located at the  Agricultural Practice Farm of National Chung Hsing  University, which mainly grows rice and corn crops. The  image of rice inverting was filmed in the Mill Shield Park in  the Fog Peak District of Taichung City.

II.  LITERATURE REVIEW

LeCun, Bottou, Bengio and Haffner (1998) released the  convolutional neural network LeNet [1] for document text  recognition as the beginning of modern applications.  Krizhevsky, Sutskever and Hilton (2012) published AlexNet  [2], trained images using ImageNet [3]'s huge image database,  and won the ILSVRC competition. Since then, convolutional  neural networks have been widely used for imaging.  classification. Simonyan and Zisserman (2014) published  VGGNet [4], which uses several stacked small window  convolution layers to achieve deeper network layers and better  network generalization capabilities.

Keywords—edge computing, deep learning, agriculture  applications

I.  INTRODUCTION

Agricultural problems have always been a major problem  for mankind. Agricultural resilience in the context of climate  change, the loss of agricultural experience, the fragmentation  of agricultural data, the lack of human resources and the lack  of real-time monitoring data are the main issues. With  information technology, we are able to record, preserve, view,  disseminate and analyze agricultural data.

Long, Shelhamer and Darrell (2015) proposed Fully  Convolutional Networks (FCN) for image semantic  segmentation [5], which is different from the original image  classification of simple network architecture. FCN can input  different image sizes. Perform image segmentation to obtain  classification results of the same size as the input image size.  Badrinarayanan, Kendall and Copula (2015) published  SegNet [6] using a symmetric neural network of down-and- down  sampling  architecture  called  Encoder-Decoder  architecture, using the feature extraction phase of VGG-16 as  the Encoder, and pooling The index of the (downsampling)  layer is used to upsample the layer, reducing the amount of

According to the Agricultural Committee of the  Administrative Council of the Republic of China 2016  Agricultural Report ,nearly a quarter of Taiwan's area is  farmland ,and78% of the fields cover less than one hectare .

This means that the field area is usually small. In addition,  farmers often practice recombination and rotation to obtain

XXX-X-XXXX-XXXX-X/XX/$XX.00 ©20XX IEEE

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:42:46 UTC from IEEE Xplore.  Restrictions apply.

978-1-7281-3893-0/20/$31.00 ©2020 IEEE

2020 IEEE 17th Annual Consumer Communications & Networking Conference (CCNC)

training parameters and improving the speed and accuracy of  the inference.

cover windows of 2x2, the input image length and width must  be an integer multiple of 32. Considering that the input image  ratio is unchanged (the original image is 16:9) and the  maximum image size is retained, the original image is  previously scaled to a size of 1536x864.

Huang et al. (2018) [7] used CNN's image tile  classification, moving window image classification and FCN  to distinguish rice and weeds for UAV images. The results  show that FCN has better full-image interpretation ability and  classification results. . Sa et al. (2018) [8] used SegNet to  segment the image of sugar beet and weed in multi-spectral  images, which can effectively distinguish different plant  species. The NVIDIA Jetson TX2 with NVIDIA GPU is also  used for edge computing device performance testing. The  results show that the edge computing device can also achieve  the real-time image segmentation computing performance.

The total number of images was 244, and the training  images were 80% of the total images, a total of 196. Verify  that the image is 20% of the total image, for a total of 48  images. Figure 2 shows the results of semantic segmentation.  Black [0,0,0] is the background, green [0,255,0] is the rice,  yellow [255,255,0] is the corn, gray [128,128,128] is the road.

The deep learning framework used in this study is the  TensorFlow [9] deep learning framework published by  Google Brain. It is compiled with C++/CUDA and provides  APIs for C++, Python, and Java programming languages. It  can be accelerated by multiple CPUs and multiple GPUs. The  speed of model training and inference is greatly improved, and  it is written in a variety of programming languages, making it  widely used in neural network applications.

Fig. 2. Crop semantic segmentation image Semantic segmentation network

IV.  METHODOLOGY

A. Semantic segmentation network

III.  DATA COLLECTION

The semantics of this study used to segment the network  into SegNet, the original architecture, and FCN-AlexNet,  which was changed from AlexNet. The network architecture  is shown in Figure 3 and Figure 4.

A. Crop Species Dataset


> **Figure 1 is the research field of the agronomy department**

> in the south side of National Chung Hsing University 
(NCHU). The camera was shot using a Logitech C925e 
webcam with a pixel of 1920x1080 and a horizontal viewing 
angle of 70.42°. The designed flying height is 30m and 40m, 
and the corresponding ground resolution is about 2.21cm/pix 
and 2.94cm/pix. This study is mainly aimed at food crops, so 
it is more suitable for rice and corn in this field. The image 
was taken on November 18, 2018. During the growing period 
of rice and corn, the plant width was about 15-20 cm and 20-
30 cm.

FCN-AlexNet is mainly to change the original three-layer  full-layer layer of AlexNet to the convolution layer of the  cover window 1x1, and finally add a sampling layer of 63x63  of the cover window to achieve the result of semantic  segmentation.

SegNet adopted the VGG16 network architecture in the  first half of the network, but dropped the last two fully  connected layers, followed by upsampling, and the second  half of the network was opposite to the first half. Another  feature of SegNet is the addition of a pooled (downsampled)  index that allows the value to be placed in the corresponding  position before downsampling in the upsampling process,  resulting in reduced training parameters and improved  performance.

Fig. 3. SegNet architecture

Fig. 1. Experimental field, the green frame area is rice, the yellow frame

area is corn, and the red frame area is the flight range.

The data set is a semantic segmentation image, the image  is labeled as a pixel type annotation, and the annotation  categories are divided into four categories: rice, corn, road and  background, and the labeling tool uses Labelbox [11].

Fig. 4. FCN-AlexNet architecture

B. Model Training

The neural network model training environment, using the  National High Speed Network and Computing Center of the  National Experimental Research Institute, provides the

The crop size dataset image size is based on the input layer  size of the SegNet model. Since the SegNet has a total of five

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:42:46 UTC from IEEE Xplore.  Restrictions apply.

2020 IEEE 17th Annual Consumer Communications & Networking Conference (CCNC)

TWGC (Taiwan GPU Cloud) cloud computing service. The  training environment uses the nchc-tensorflow-18.08-py3  environment, the tensorflow is updated to version 1.10.1, and  the keras-2.2.2 and scikit-image suites are installed. Calculate  the accelerated hardware using 4 NVIDIA Tesla V100 SMX2.

B.  Quantitative analysis   Table 1 compares the recall rate and overall accuracy of  each category in the semantic segmentation model of crop  types. Table 2 compares the recall rate and overall accuracy of  the rice lodging semantic segmentation model in each  category.

The two sets of semantic segmentation networks use the  same network hyperparameters. The optimizer uses the Adam  (Adaptive Momentum Estimation) optimizer, Learning rate =  0.001, B1 = 0.9, B2 = 0.999, Decay = 0.05, Batch size = 4,  epoch = 20, and in the lodging image training, Batch size =  24, Epoch=50.

TABLE I.   CROP SPECIES CLASSIFICATION RECALL RATE

AND OA

Network  Recall Rate of Classification Object (%)

Rice  Corn  Road  Background  OA  FCN- AlexNet  92.04  90.64  81.93  87.09  88.48

C. Real-time Inference

This study uses the embedded system mounted on the  drone to perform real-time image capture of the crop types of  the farmland. The research uses the DJI Matrice 100 as the  flight carrier, and is equipped with the ASUS Tinker Board S  embedded system and the Logitech C925e network camera.  The image is captured in seconds, and the stored image is  immediately transmitted to the remote inference server via the  4G mobile network. The inference result is then transmitted to  the user's mobile phone and the UAV controller, and the signal  is sent to the unmanned person according to the identification  result. Machine for dynamic flight control. The process is  shown in Figure 5.

SegNet  96.07  90.61  77.90  88.21  89.44

C.  Qualitative analysis  Qualitative analysis is compared by inference results.  Figure 6 shows the comparison between the inference results  of the two types of networks in the semantic segmentation  model of crops and the geomorphic comparison. Figure 6  shows the comparison between the inference results of the two  networks in the rice drop semantic segmentation model and  the geography.

The inference server environment is Ubuntu16.04.5 x86- 64, and runs the containerized environment of Docker. The  image inference service uses the TensorFlow container image  released by NVIDIA GPU Cloud, and Keras is installed as the  machine learning framework. The neural network uses the full  volume of Segnet. The neural network is used as the basis for  the semantic segmentation model. The hardware is equipped  with an NVIDIA GTX 1080 graphics card as a deep neural  network computing accelerator card.

V. RESULT

Fig. 6. Crop category classification results mask comparison, (top left)

This study used two types of full convolutional neural networks  for comparison. The efficacy evaluation was divided into qualitative  and quantitative analysis.

Original image, (top right) ground truth, (down left) FCN-AlexNet

and (down right) SegNet mask

From the qualitative analysis results, SegNet performs  better for small object recognition and edge segmentation,  because FCN-AlexNet directly upsamples at 32 times interval  in the deconvolution layer, and the performance of class  boundary processing can be imagined to be rough.

A.  Performance Evaluation

The effectiveness assessment uses the Confusion Matrix's  Precision, Recall [12] to assess classification performance,  and overall accuracy (OA).

VI. CONCLUSION

௉೎் ௉೎ାி௉೎, recall௖ൌ ்

௉೎் ௉೎ାிே೎  (1)

precision௖ൌ ்

This study used two kinds of full convolutional neural  networks for comparison. Although the FCN-AlexNet  network is simpler, the convolution operation takes less time,  but the convolution mask window is large and the number of  convolutions is small, which is more detailed in the details.  Inferior. After quantitative and qualitative analysis, it is

OA ൌ ∑் ௉೎் ௉೎ା்ே೎ାி௉೎ାிே೎ ௡ ௖ୀଵ   (2)

TPc, TFc, FPc, FNc are true positive, true negative, false  positive and false negative in category c.

Fig. 5. Real-time image segmentation inference and dynamic flight control process

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:42:46 UTC from IEEE Xplore.  Restrictions apply.

2020 IEEE 17th Annual Consumer Communications & Networking Conference (CCNC)

considered that SegNet is relatively complete in detail  processing, and the two network training parameters are not  much different, so SegNet is used as the neural network model  of inference service.

[2]  Krizhevsky, A., Sutskever, I., & Hinton, G. E. (2012). Imagenet  classification with deep convolutional neural networks. In Advances  in neural information processing systems (pp. 1097-1105).  [3]  Deng, J., Dong, W., Socher, R., Li, L. J., Li, K., & Fei-Fei, L.  (2009). Imagenet: A large-scale hierarchical image database. In  Computer Vision and Pattern Recognition, 2009. CVPR 2009. IEEE  Conference on (pp. 248-255). IEEE.  [4]  Simonyan, K., & Zisserman, A. (2014). Very deep convolutional  networks for large-scale image recognition. arXiv preprint  arXiv:1409.1556.  [5]  Long, J., Shelhamer, E., & Darrell, T. (2015). Fully convolutional  networks for semantic segmentation. In Proceedings of the IEEE  conference on computer vision and pattern recognition (pp. 3431- 3440).  [6]  Badrinarayanan, V., Kendall, A., & Cipolla, R. (2015). Segnet: A  deep convolutional encoder-decoder architecture for image  segmentation. arXiv preprint arXiv:1511.00561.  [7]  Huang, H., Deng, J., Lan, Y., Yang, A., Deng, X., & Zhang, L.  (2018). A fully convolutional network for weed mapping of  unmanned aerial vehicle (UAV) imagery. PloS one, 13(4),  e0196302.   [8]  Sa, I., Popović, M., Khanna, R., Chen, Z., Lottes, P., Liebisch, F.,  Nieto, J., Stachniss, C., Walter, A. & Siegwart, R. (2018).  Weedmap: a large-scale semantic weed mapping framework using  aerial multispectral imaging and deep neural network for precision  farming. Remote Sensing, 10(9), 1423.  [9]  Abadi, M., Barham, P., Chen, J., Chen, Z., Davis, A., Dean, J., ... &  Kudlur, M. (2016, November). Tensorflow: a system for large-scale  machine learning. In OSDI (Vol. 16, pp. 265-283).  [10]  Council of Agriculture, Executive Yuan, Taiwan., Agriculture  Statistics Data., Available at :  http://agrstat.coa.gov.tw/sdweb/public/inquiry/InquireAdvance.aspx  [Accessed April, 4th, 2019]  [11]  Labelbox: The best way to create and manage training data.  Available at : https://www.labelbox.com/ [Accessed Nov., 30th,  2019]  [12]  Boyd, K., Eng, K. H., & Page, C. D. (2013, September). Area under  the precision-recall curve: point estimates and confidence intervals.  In Joint European conference on machine learning and knowledge  discovery in databases (pp. 451-466). Springer, Berlin, Heidelberg.

The UAV is equipped with an embedded system for real- time image segmentation and identification of agricultural  crops, which can clearly identify and calculate the current  agricultural production status, and save the current manpower  expenses by quickly scanning the large-scale unmanned aerial  vehicles. The UAV in the field experiment of National Chung  Hsing University uses only a single standard battery, so it can  only fly for about 10 to 13 minutes under the load and  embedded system power consumption. Therefore, it is  recommended to install dual battery and embedded system  separately. Power supply may be more appropriate.

Wireless communication is measured. The embedded  system captures the image to the mobile device for about 4 to  6 seconds. After deducting the complete delay and inference  time for the file read and write, there is still a transmission  delay of about 3 to 4 seconds, but the wireless communication  is not the study. Expertise, I hope that the follow-up  cooperation team can provide the 4G signal of the regional  network, or wait for the maturity of the 5G network.

ACKNOWLEDGMENT (Heading 5)

This research is partially supported by the Ministry of  Science and Technology under Grant Number 108-2634-F- 005-003- through Pervasive AI Research (PAIR) Labs,  Taiwan.


## REFERENCES

[1]  LeCun, Y., Bottou, L., Bengio, Y., & Haffner, P. (1998). Gradient- based learning applied to document recognition. Proceedings of the  IEEE, 86(11), 2278-2324.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:42:46 UTC from IEEE Xplore.  Restrictions apply.
