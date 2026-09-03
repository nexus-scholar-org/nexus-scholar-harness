---
title: "A Multispectral U-Net Framework for Crop-Weed Semantic Segmentation"
doi: "10.1007/978-3-030-82064-0_2"
authors: "Daniel Leyva Rosas, Uziel Grajeda Gonzalez, Victor Gonzalez Huitron"
extraction_engine: pymupdf (per-page, from proceedings volume)
tags: [RQ1, multispectral, U-Net, NIR+RGB, semantic-segmentation]
---

A Multispectral U-Net Framework for
Crop-Weed Semantic Segmentation
Daniel Leyva Rosas, Uziel Grajeda Gonzalez, and Victor Gonzalez Huitron
Abstract The ability to visualize and understand the environment is essential for
farming robots and precision agriculture. It allows them to act as the situation requires
and take the necessary actions for a given scenario. The most recent state-of-the-art
approaches use deep learning to generate models capable of crop classiﬁcation, or
detecting diseases and pests to reduce herbicides and pesticides, allowing a consid-
erable reduction in pollution produced by the agricultural sector. In this work, we
propose implementing a Fully-Convolutional Network (FCN) to perform semantic
segmentation tasks. We use the U-Net architecture to visualize crops and weeds,
initially proposed for use in medical imaging. For our implementation, we used the
Sunﬂower dataset, which combines images in the Near-Infrared spectrum (NIR) and
three channels images (RGB). The proposed FCN was evaluated employing Inter-
section over Union (IoU), with satisfactory results in semantic segmentation tasks.
Keywords Semantic segmentation · Deep learning · Precision agriculture
1
Introduction
Precision agriculture is a farming management strategy oriented at supporting
decision-making based on the observation, measurement, analysis, and processing
of data that allows us to understand the current state of the soil or crops and their
variations. The main objective of precision agriculture is to reduce the environmen-
tal impact of pollution produced by the agricultural sector by reducing pesticides,
herbicides, and water, among others [10]. In this matter, the use of drones and farm-
D. L. Rosas (B) · U. G. Gonzalez
Tecnologico Nacional de México Campus Culiacén, Juan de Dios Batiz No. 310 Pte., Col.
Guadalupe, 80220 Culiacan Rosales, Mexico
e-mail: Daniel_leyva@itculiacan.edu.mx
V. G. Huitron
CONACyT-Tecnológico Nacional de México/Instituto Tecnológico de Culiacán, Sinaloa, Mexico
© The Author(s), under exclusive license to Springer Nature Switzerland AG 2022
K. L. Flores Rodríguez et al. (eds.), Recent Trends in Sustainable Engineering,
Lecture Notes in Networks and Systems 297,
https://doi.org/10.1007/978-3-030-82064-0_2
15


16
D. L. Rosas et al.
Fig. 1 Farming robots for data adquisition, a Bonirob system used in [11] for data adquisition, b
Bosch Bonirob Farming robot used in [3] for data adquisition
ing robots in conjunction with perception systems are beneﬁcial (Fig.1), as they are
capable of achieving automation, classiﬁcation, detection, and similar tasks [3].
Some novel solutions, which use perception systems based on advanced machine
learning techniques, can offer plant-level weed control treatments through selective
spraying systems or mechanical actuators. This task, however, requires classiﬁca-
tion systems capable of collecting data and images on the ﬁeld, analyzing them,
and generating information that allows us to understand the environment and ease
decision-making processes [11].
Models based on Convolutional Neural Networks (CNN) have shown a straight-
forward utility in solving image processing and computer vision problems. They
achieve a deep understanding of the analyzed images patterns and have been widely
used for classiﬁcation tasks in plants [2, 9, 17].
The utility of traditional CNN’s has been demonstrated for image classiﬁcation
tasks [6, 18], object detection [7, 14, 20] and image segmentation [1, 12, 16];
[8] shows particularly, applications for semantic segmentations. Altogether, Fully
Convolutional Networks are especially useful compared to CNN.
In Sect.2 we see how CNN’s have evolved and have been used for increasingly
specialized tasks, we discuss how state-of-the-art models address semantic segmen-
tation problems, and the way the use of multispectral images has become generalized
in the area. In Sect.3 we explain in a general way the U-Net architecture and the
Sunﬂower Dataset, as well as how they are integrated to achieve good performance.
In Sect.4 we explain in detail the data and parameters used for training the model
and the quality metrics obtained. Also in this section, we show some of the results
obtained with our model. And ﬁnally, in Sect.5, we express our conclusions.


A Multispectral U-Net Framework for Crop-Weed Semantic Segmentation
17
2
Related Work
In recent years, multiple models based on supervised learning have been proposed
addressingthecropclassiﬁcationtask.Afeasiblehardwareimplementationismanda-
tory due to the agroindustry requirements that adopt in short time innovative solutions
[9, 17]. Various efforts have been made to develop algorithms that approach the seg-
mentation task. Notably, the design of models capable of crop disease detection
through the use of convolutional neural networks have achieved outstanding results
[4, 9, 13, 17], which facilitates the possibility of implementing more competent and
capable precision agriculture systems through farming robots and drones.
The most recent, novel implementations employs models based on semantic seg-
mentation [3, 11, 12, 16], as it allows to speciﬁcally isolate the factor of interest,
allowing for a more accessible, cleaner visualization. The use of algorithms based
on CNN have been a hot topic research in computer vision tasks [6], where the
emergence of algorithms capable of large-scale image processing [18] allowed the
development of increasingly specialized models.
In [1] it can be noted how a topology identical to the convolutional layers presented
in [18] is used successfully, resulting in the already known SegNet.
Further specialization is achieved by Sa et al. [16]; proposing a model for
crop/weed semantic segmentation, based on the SegNet encoder-decoder architec-
ture, called weedNet. Sa et al. [16] also suggests using multispectral images in its
solution, stating that these provide the possibility of working with indices based on
radiance ratios that are more robust under varying lighting conditions, making its
use suitable for farming robots.
Moreover, the use of multispectral images in models oriented to agricultural appli-
cations, can be observed in datasets such as sugar beet [2] and Sunﬂower [3]. Ref-
erences [9, 13, 16, 19] also make use of images with extra channels additional to
traditional RGB in order to improve results by increasing the number of features to
process.
3
Proposed Method
We approach the crop-weed detection problem by using semantic segmentation tech-
niques based on Fully convolutional networks and multispectral images in this work.
The main workﬂows are as follows: ﬁrst, a Near-infrared (NIR) image spectrum is
combined with a three-channel (RGB) image; thus, a four-channel array is employed
as input for theCNNmodel. Secondly, anencoding-decodingCNNprocesses thedata
array in order to obtain a 4-channels array, consisting of a segmented mask image
and three channels for RGB segmented imaging. Finally, is obtained pixel-level
classiﬁcation for crop, weed, and soil from these results. A workﬂow is presented in
Fig.2.


18
D. L. Rosas et al.
Fig. 2 Representation of the proposed ﬂow for RGB and NIR images as inputs, and RGB segmented
mask image and pixel-level classiﬁcation array as outputs
Table 1 Hyperparameters used for multispectral U-Net models training
Hyperparameter
Value
Optimization algorithm
Adam
Epochs
300
Batch size
8–16
Loss function
Binary crossentropy
Learning rate
0.0001
DropOut value
0.05
Num ﬁlters
16
For our proposal model, an architecture based on U-Net [15] is adapted for its
use with multispectral images. It has shown to be capable of generating models
of notable performance training on relatively small datasets. As training data, the
Sunﬂower dataset was used for semantic crop-weed segmentation [3]. In Table1 we
show the hyperparameters used on the training of our models for both experiments.
This implementation is based on the tensorﬂow, keras and sklearn libraries for the
creation and training of the model, as well as numpy and skimage for the handling of
images and arrays. The model training was performed on the Google Colab platform
in conjunction with Google drive to save and access the datasets and models.


A Multispectral U-Net Framework for Crop-Weed Semantic Segmentation
19
3.1
Architecture
The U-Net architecture is based on an encoder-decoder model commonly employed
in deep learning for segmentation tasks. The convolutional layers perform feature
extraction. Then, upsampling layers estimate an output image from the extracted
features, as have been implemented in previous works such as segnet [1], or weednet
[16].
U-Net also combines the features maps extracted in each downsampling stage
with its upsampling counterpart in a similar fashion that resembles the architecture
proposed on resNet [5], which allows the network to deepen on features extraction
while preserving more general context information. As stated in Fig.3. Each blue
box corresponds to a multi-channel feature map. White boxes represent feature maps
copied from previous layers and each arrow represents a different action denoted in
the image bottom-right corner.
3.2
Dataset
As stated in [3] the creation of a semi-artiﬁcial dataset for crop-weed semantic
segmentation is possible with a novel approach that propounds modifying only the
areas of interest in the image, which correspond to plants and crops, and leaving
Fig. 3 U-Net architecture topology and layers, as shown in [15]


20
D. L. Rosas et al.
Fig. 4 An example of an original image and the synthetic one generated using the cGAN. image
extrated from [3]
Table 2 Pixel-wise segmentation performance for sunﬂower dataset, trained on RGB + NIR input
Dataset
Model
Mean IoU
Soil IoU
Crop IoU
Weed IoU
Syntetic crop
Bonnet
0.83
0.99
0.84
0.66
U-Net
0.701
0.99
0.69
0.41
U-Net-resNet
0.704
0.99
0.65
0.47
Bonnet
0.80
0.99
0.78
0.62
Original
U-Net
0.64
0.99
0.54
0.38
U-Net-resNet
0.66
0.99
0.60
0.43
Bonnet
0.86
0.99
0.88
0.69
Mixed
U-Net
0.51
0.99
0.68
0.40
U-Net-resNet
0.53
0.99
0.70
0.48
Extracted from [3]
Best results are shown in bold
the rest of the original image intact. A conditional generative adversarial network
(cGAN) was used to create semi-artiﬁcial data instances, replacing the original crops
and weeds with synthetic images. In Fig.4, an example is shown. The methodology
was used for both RGB and NIR dataset creation.


A Multispectral U-Net Framework for Crop-Weed Semantic Segmentation
21
Fig. 5 Extracted from [3]. Top row: from left to right, synthetic RGB and synthetic NIR samples,
respectively. Bottom row: from left to right, the pixel-wise ground-truth and the result obtained by
using a semantic segmentation deep neural network, respectively
The experiments carried out in [3] show how the use of mixed datasets (original
- enhanced) generates better results compared to the use of completely artiﬁcial or
original datasets as shown in Table 2 extracted from the original article.
The dataset contains a three-channel RGB image, as well as a one-channel image
in the NIR spectrum. For ground-truth and comparison purposes, an RGB segmented
mask and a one-channel class mask is provided. In Fig.5, a sample data is shown.
As is often the case on datasets designed for segmentation tasks, this dataset faces
the problem of manual labeling, so it does not contain a substantial amount of data.
In total, the Sunﬂower dataset has 500 examples distributed in 3 subsets; each stage
includes a combination of original and semi-artiﬁcial images.
4
Results
For our proposal, two of the three parts of the Sunﬂower dataset (jesi_05_12 and
jesi_05_18) were taken as a training set, using both RGB and NIR images rescaled
to a resolution of 512 * 512 pixels for experiment 1, and 704 * 704 pixels for
experiment 2. The third part of the dataset (jesi_06_13) was used as validation data.


22
D. L. Rosas et al.
Table 3 Objective results by means of Jaccard index (IoU) values for the Sunﬂower dataset
Model
Crop IoU
Weed IoU
Soil IoU
Mean IoU
U-Net (Ours, 704
* 704)
0.90
0.76
0.86
0.84
U-Net (Ours)
0.88
0.75
0.83
0.82
U-Net [3]
0.68
0.40
0.99
0.69
Bonnet [3]
0.88
0.69
0.99
0.86
U-net-resnet [3]
0.70
0.48
0.99
0.72
Best results are shown in bold
Table3 shows the values obtained by measuring the Jaccard index as seen in
Eq. (1), also known as intersection over union (IoU), for each of our models compared
to the results reported in [3].
DJaccard (A, B) = |A ∩B|
|A ∪B|
(1)
The IoU value for each class is the arithmetic average of the value obtained per
class for the total images in each subset. To obtain the Mean IoU value, the arithmetic
average of the IoU value for each of the three classes was calculated.
In our training and testing, we were limited by hardware capacity, which restrained
the use of the complete dataset for training, as well as using larger image sizes.
Despite this, the results obtained are helpful for implementations oriented to precision
agriculture, as Table3 states. Figure6 shows some examples of the results obtained
in this work.
The performance of the network is generally superior to the results obtained in
the experiments carried out in [3] using the same dataset. It is important to note that
in [3] the complete Sunﬂower dataset (500 images) with an image size of 512 *
512 pixels was used. In comparison, for our implementation, only two subsets (318
images) were used with a different size on each experiment (512 * 512 pixels for
experiment 1 and 704 * 704 pixels for experiment 2).
In Table 3, we can see how the IoU values measured for our 512 * 512 pixel model
are higher for the crop and weed classes compared to the U-Net, U-Net-resNet and
Bonnet models presented in [3], while obtaining lower IoU values for the soil class
which results in a lower Mean IoU value. Despite this, we consider that the crop
and weed classes are more signiﬁcant for precision agriculture uses, and a slightly
higher margin of error in the soil class does not represent a reduction in the model
functionality.
It can be seen that despite having a considerably smaller training set, our imple-
mentation obtains signiﬁcantly higher values than those obtained by [3] for U-Net
and U-Net-resnet, as well as slightly higher values than those obtained with Bonnet.
Finally, Table2 also compares our 704 * 704 pixel model, showing better results
for crop and weed classes compared to our 512 * 512 model and the three models


A Multispectral U-Net Framework for Crop-Weed Semantic Segmentation
23
Fig. 6 From left to right: original input RGB+NIR image, ground truth segmented RGB mask,
segmented RGB mask obtained with our model
presented in [3], which allows us to infer that larger image sizes should obtain better
results.
5
Conclusions
The U-net architecture is a handy tool for tasks oriented to semantic segmentation in
non-medical areas. Since it is possible to obtain reliable results with a surprisingly
small amount of training data, its use can signiﬁcantly help precision agriculture
tasks.
For the relatively large training datasets scenario, U-net might not be the best
ﬁt. There are alternatives such as Bonnet or segNet that can obtain better results,
translating into shorter processing times if the required hardware is available. Still,
these architectures usually need more data to get a better performance.


24
D. L. Rosas et al.
For semantic segmentation tasks with a limited training dataset, a U-net imple-
mentation with relatively large input image sizes is an excellent choice.
References
1. Badrinarayanan V, Kendall A, Cipolla R (2016) SegNet: a deep convolutional encoder-decoder
architecture for image segmentation. arXiv:151100561 [cs]
2. Chebrolu N, Lottes P, Schaefer A et al (2017) Agricultural robot dataset for plant classiﬁcation,
localization and mapping on sugar beet ﬁelds. Int J Robot Res 36:1045–1052. https://doi.org/
10.1177/0278364917720510
3. Fawakherji M, Potena C, Pretto A et al (2020) Multi-spectral image synthesis for crop/weed
segmentation in precision farming. arXiv:200905750 [cs]
4. Fuentes A, Yoon S, Kim S, Park D (2017) A robust deep-learning-based detector for real-
time tomato plant diseases and pests recognition. Sensors 17:2022. https://doi.org/10.3390/
s17092022
5. He K, Zhang X, Ren S, Sun J (2015) Deep residual learning for image recognition.
arXiv:151203385 [cs]
6. Lecun Y, Bottou L, Bengio Y, Haffner P (1998) Gradient-based learning applied to document
recognition. Proc IEEE 86:2278–2324. https://doi.org/10.1109/5.726791
7. Liu W, Anguelov D, Erhan D et al (2016) SSD: single shot MultiBox detector. arXiv:151202325
[cs] 9905:21-37. DOIurl10.1007/978-3-319-46448-0_2
8. Long J, Shelhamer E, Darrell T (2015) Fully convolutional networks for semantic segmentation.
arXiv:14114038 [cs]
9. Lowe A, Harrison N, French AP (2017) Hyperspectral image analysis techniques for the detec-
tion and classiﬁcation of the early onset of plant disease and stress. Plant Methods 13. https://
doi.org/10.1186/s13007-017-0233-z
10. McBratney A, Whelan B, Ancev T, Bouma J (2005) Future directions of precision agriculture.
Precis Agric 6:7–23. https://doi.org/10.1007/s11119-005-0681-8
11. Milioto A, Lottes P, Stachniss C (2018) Real-time semantic segmentation of crop and weed
for precision agriculture robots leveraging background knowledge in CNNs. In: 2018 IEEE
International conference on robotics and automation (ICRA). IEEE
12. Milioto A, Stachniss C (2019) Bonnet: an open-source training and deployment framework for
semantic segmentation in robotics using CNNs. In: 2019 International conference on robotics
and automation (ICRA). IEEE
13. Pourazar H, Samadzadegan F, Dadrass Javan F (2019) Aerial multispectral imagery for plant
disease detection: radiometric calibration necessity assessment. Eur J Remote Sens 52:17–31.
https://doi.org/10.1080/22797254.2019.1642143
14. Redmon J, Divvala S, Girshick R, Farhadi A (2016) You only look once: uniﬁed, real-time
object detection. arXiv:150602640 [cs]
15. Ronneberger O, Fischer P, Brox T (2015) U-Net: convolutional networks for biomedical image
segmentation. arXiv:150504597 [cs]
16. Sa I, Chen Z, Popovic M et al (2018) weedNet: dense semantic weed classiﬁcation using
multispectral images and MAV for smart farming. IEEE Robot Autom Lett 3:588–595. https://
doi.org/10.1109/lra.2017.2774979
17. Saleem Potgieter, Arif Mahmood (2019) Plant disease detection and classiﬁcation by deep
learning. Plants 8:468. https://doi.org/10.3390/plants8110468
18. Simonyan K, Zisserman A (2015) Very deep convolutional networks for large-scale image
recognition. arXiv:14091556 [cs]
19. Sosa-Herrera JA, Vallejo-Pérez MR, Álvarez-Jarquín N et al (2019) Geographic object-based
analysis of airborne multispectral images for health assessment of Capsicum annuum L. crops.
Sensors 19:4817. https://doi.org/10.3390/s19214817
20. Wong A, Shaﬁee MJ, Li F, Chwyl B (2018) Tiny SSD: a tiny single-shot detection deep
convolutional neural network for real-time embedded object detection. arXiv:180206488 [cs]
