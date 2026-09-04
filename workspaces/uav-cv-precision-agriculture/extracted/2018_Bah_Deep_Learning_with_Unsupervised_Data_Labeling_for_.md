---
workspace_id: SCI-000482
doi: 10.3390/rs10111690
title: Deep Learning with Unsupervised Data Labeling for Weed Detection in Line Crops
  in UAV Images
authors:
- family_name: Bah
  given_name: Mamadou Dian
  orcid: https://orcid.org/0000-0002-0733-8587
- family_name: Hafiane
  given_name: Adel
  orcid: https://orcid.org/0000-0003-3185-9996
- family_name: Canals
  given_name: "Rapha\xEBl"
  orcid: https://orcid.org/0000-0001-9100-7539
year: 2018
extraction_engine: pymupdf
extracted_at: '2026-09-04T01:48:52.624985+00:00'
---

# Deep Learning with Unsupervised Data Labeling for Weed Detection in Line Crops in UAV Images

1

Deep Learning with unsupervised data labeling for

weeds detection on UAV images

M.Dian. Bah∗, Adel Haﬁane†, Rapha¨el Canals∗

∗University of Orl´eans, PRISME EA 4229, Orl´eans F45072, France †INSA Centre Val de Loire, PRISME EA 4229, Bourges F-18022, France

Unmanned Aerial Vehicle (UAV) is fast becoming an inter- esting vision based acquisition system, since it enables rapid acquisition of the entire crop area with a very high spatial res- olution and at low cost [5], [6]. Despite the important advances in UAV acquisition systems, the automatic detection of weeds remains a challenging problem. In recent years, deep learning techniques have shown a dramatic improvement for many computer vision tasks, but still not widely used in agriculture domain. Indeed recent development showed the importance of these techniques for weeds detection [7], [8]. However, the huge quantities of the data required in the learning phase, have accentuated the problem of the manual annotation of these datasets. The same problem rises in agriculture data, where labeling plants in a ﬁeld image is very time consuming. So far, very little attention have been payed to the unsupervised annotation of the data to train the deep learning models, particularly for agriculture.


## Abstract—In modern agriculture, usually weeds control con-

sists in spraying herbicides all over the agricultural ﬁeld.
This practice involves signiﬁcant waste and cost of herbicide
for farmers and environmental pollution. One way to reduce
the cost and environmental impact is to allocate the right
doses of herbicide at the right place and at the right time
(Precision Agriculture). Nowadays, Unmanned Aerial Vehicle
(UAV) is becoming an interesting acquisition system for weeds
localization and management due to its ability to obtain the
images of the entire agricultural ﬁeld with a very high spatial
resolution and at low cost. Despite the important advances in
UAV acquisition systems, automatic weeds detection remains a
challenging problem because of its strong similarity with the
crops. Recently Deep Learning approach has shown impressive
results in different complex classiﬁcation problem. However, this
approach needs a certain amount of training data but, creating
large agricultural datasets with pixel-level annotations by expert
is an extremely time consuming task. In this paper, we propose
a novel fully automatic learning method using Convolutional
Neuronal Networks (CNNs) with unsupervised training dataset
collection for weeds detection from UAV images. The proposed
method consists in three main phases. First we automatically
detect the crop lines and using them to identify the interline
weeds. In the second phase, interline weeds are used to constitute
the training dataset. Finally, we performed CNNs on this dataset
to build a model able to detect the crop and weeds in the images.
The results obtained are comparable to the traditional supervised
training data labeling. The accuracy gaps are 1.5% in the spinach
ﬁeld and 6% in the bean ﬁeld.

arXiv:1805.12395v1  [cs.CV]  31 May 2018

In this paper, we propose a new fully automatic learning method using Convolutional Neuronal Networks (CNNs) with unsupervised training set construction for weeds detection on UAV images. This method is performed in three main phases. First we automatically detect the crop lines and using them to identify the interline weeds. In the second phase interline weeds are used to constitute our training dataset. Finally, we performed CNNs on this database to build a model able to detect the crop and weeds in the images.

Index Terms—Deep learning, Image processing, Unmanned aerial vehicle, Precision agriculture, Crop lines detection, Weeds detection.

This paper is divided into ﬁve parts. In the section 2 we discuss the related work. Section 3 presents the proposed method. In section 4 we comment and discuss the experimental results obtained. Section 5 concludes the paper.

I. INTRODUCTION

Currently, losses due to pests, diseases and weeds can reach 40% of global crop yields each year and this percentage is expected to increase signiﬁcantly in the coming years [1]. The usual weeds control practices consist in spraying herbicides all over the agricultural ﬁeld. Those practices involve signiﬁcant wastes and costs of herbicides for farmers and environmental pollution [2]. In order to reduce the amount of chemicals while continuing to increase productivity, the concept of precision agriculture was introduced [3], [4]. Precision agriculture is deﬁned as the application of technology for the purpose of improving crop performance and environmental quality [3]. The main goal of precision agriculture is to allocate the right doses of input at the right place and at the right time. Weeds detection and characterization represent one of the major challenges of the precision agriculture.

II. RELATED WORK

In literature, several approaches have been used to detect weeds with different acquisition systems. The main approach for weeds detection is to extract vegetation from the image using a segmentation and then discriminate crop and weeds. Common segmentation approaches use color and multispectral information, to separate vegetation and background (soil and residues). Speciﬁc indices are calculated from these informa- tion to effectively segment vegetation [9].

However, weeds and crop are hard to discriminate by using spectral information because of their strong similarity. Regional approaches and spatial arrangement of pixels are preferred in most cases. In [10], Excess Green Vegetation Index (ExG) [11] and the Otsu’s thresholding [12] have helped

2

to remove background (soil, residues) before to perform a double Hough transform [13] in order to identify the main crop lines in perspective images. Then, to discriminate crop and weeds in the segmented image, the authors applied a region-based segmentation method developing a blob coloring analysis. Thus any region with at least one pixel belonging to the detected lines is considered to be crop, otherwise it is weeds. Unfortunately, this technique failed to handle weeds close to crop region. In [14] an object-based image analysis (OBIA) procedure was developed on series of UAV images for automatic discrimination of crop rows and weeds in maize ﬁeld. For that, they segmented the UAV images into homogeneous multi-pixel objects using the multi-scale algorithm [15]. Thus, the large scale highlights structures of crop lines and the small scale brings out objects that lie within crop lines. They have found that the process is strongly affected by the presence of weed plants very close or within the crop rows.

dataset using purely supervised training [24]. Nowadays deep learning is applied in several domains to help solve many big data problems such as computer vision, speech recognition, and natural language processing. In agriculture domain, CNNs are applied to classify patches of water hyacinth, serrated tussock and tropical soda apple in [25]. [26] used CNNs for semantic segmentation in the context of mixed crops on images of an oil radish plot trial with barley, grass, weed, stump and soil. [27] provide accurate weeds classiﬁcation in real sugar beet ﬁelds with mobile agricultural robots. [7] applied AlexNet for the detection of weeds in soybean crops. In [8] AlexNet is applied for weeds detection in different crop ﬁelds such as the beet, spinach and bean in UAV imagery.

The main common point between the supervised machine learning algorithms is the need of training data. For a good optimisation of deep learning models it is necessary to have a certain amount of labeled data. But as mentioned before creating large agricultural datasets with pixel-level annotations is an extremely time consuming task.

In [16], 2-D Gabor ﬁlters was applied to extract the features and ANN for broadleaf and grass weeds classiﬁcation. Their results showed that joint space-frequency texture features have potential for weed classiﬁcation. In [17], the authors rely on morphological variation and use neural network analysis to separate weeds from maize crop. Support Vector Machine (SVM) and shape features was suggested for the effective classiﬁcation of crops and weeds in digital images in [18]. On their experiment, a total of fourteen features that characterize crops and weeds in images were tested to ﬁnd the optimal combination of features which provides the highest classiﬁca- tion rate. [19] suggested that in the image, edge frequencies and veins of both the crop and the weed have different density properties (strong and weak edges) to separate crop from weed. A semi-supervised method has been proposed in [20] to discriminate weeds and crop. The Ostu thresholding was applied twice on ExG. In ﬁrst step, authors used segmentation to remove the background then, in the second one they create two classes supposed to be crop and weeds. K-means clustering was used to select one hundred samples of each class for the training. SVM classiﬁer with geometric features, spatial features, ﬁrst and second-order statistics was extracted on the red, blue, green and ExG bands. The method has proven to be effective in sunﬂower ﬁeld, but less robust in the corn ﬁeld because of shade produced by corn plants.

Little attempts have been made to develop fully automatic system for training and identiﬁcation of weeds in agricultural ﬁelds. In a Recent work, [28] suggest the use of synthetic training datasets. However, this technique requires a precise modeling in terms of texture, 3D models and light conditions.

To the best of our knowledge there is no work for automatic labeling of weeds using UAV imagery system.

III. PROPOSED METHOD

In modern agriculture, most of crops are grown in regular rows separated by a deﬁned space that depends on type of the crop. Generally, plants that grow out of the rows are considered as weeds commonly referred as inter-line weeds. Several studies have used this assumption to locate weeds using the geometric properties of the rows [29]. The main advantage of such technique is that it is unsupervised and does not depend on the training data. Indeed, based on this hypothesis. Intra and inter line vegetation are then used to constitute our training database which is categorized into two classes crop and weed. Thereafter, we performed CNNs on this database to build a model able to detect the crop and weeds in the images. The ﬂowchart (Fig 1) depicts the main steps of the proposed method. Next sections describes in details each step.

In [21], authors used texture features extracted from wavelet sub-images to detect and characterize four types of weeds in a sugar beet ﬁeld. Neural networks have been applied as classiﬁer. The use of wavelets proved to be efﬁcient for the detection of weeds even at a stage of growth of beet greater than 6 leaves. [22] evaluate weeds detection with support vector machine and artiﬁcial neural networks in four species of common weeds in sugar beet ﬁelds using shape features.

A. Crop lines detection

A crop row can be deﬁned as a composition of several parallel lines. The aim is to detect the main line of each crop row. For that purpose we have used a Hough transform to highlight the alignments of the pixels. In Hough space there is one cell by line which involve an aggregation of cells by crop row. The main lines in Hough space correspond to the cells which contains the maximum of vote (peak) on each aggregation. Before starting any line detection procedure, generally pre-processing is required to remove undesirable perturbations such as shadows, soil or stones. Here we have used the ExG (Eq. 1) with the Otsu adaptive thresholding to discriminate between vegetation and background.

Recently, convolutional neural networks have emerged as a powerful approach for computer vision tasks. CNNs [23] pro- gressed mostly through the success of this method in ImageNet Large Scale Vision Recognition Challenge 2012 (ILSCVR12) and the creation of AlexNet network in 2012 which showed that a large, deep convolutional neural network is capable of achieving record-breaking results on a highly challenging

3

Fig. 1: Flowchart of the proposed method

in Hnorm(θ, ρ), we identify the corresponding skeleton, and then we delete the votes of this skeleton in Hnorm(θ, ρ) before continuing. All the steps are summarized in algorithm 1.

ExG = 2g −r −b (1)

where r, g and b are the normalized RGB coordinates.

Hough transform is one of the most widely used methods for lines detection and it is often integrated in tools for guiding agricultural machines because of its robustness and ability to adjust discontinuous lines caused by missing crop plants in the row or poor germination [30]. Usually, for crop lines detection, Hough transform is directly applied to the segmented image. This procedure is computational expensive and depends on the density of the vegetation in crop rows and there is also a risk of the lines over-detection. We have addressed this problem by using the skeleton of each row instead of the binary region, this approach has shown better performances in (Bah et al. 2017). The skeleton provided a good overall representation of the structure of the ﬁeld, namely orientations and periodicity. Indeed, the Hough transform H(θ, ρ) is computed on the skeleton with a θ resolution equal to 0.1◦letting θ take values in the range of ]−90◦; 90◦] and ρ resolution equal to 1. Thanks to a histogram of the skeletons directions, the most represented angle is chosen as the main orientation θlines of crop lines. H(θ, ρ) has been normalized Hnorm(θ, ρ) in order to give the same weight to all the crop lines, especially the short ones close to the borders of the image [10]. Hnorm(θ, ρ) is deﬁned as the ratio between the accumulator of the vegetation image and the accumulator of a totally white image of the same size Hones(θ, ρ). To disregard the small lines created by aggrega- tion of weeds in inter-row a threshold of 0.1 was applied to the normalized Hough transform. Moreover in modern agriculture crops are usually sown in parallel lines with the same interline distance that is the main peaks corresponding to the crop lines are aligned around an angle in the Hough space with same gaps. Unfortunately, because of the realities in the agricultural ﬁeld the lines are not perfectly parallel, thus the peaks in the Hough space have close but different angles and the interline distance is not constant. In order to not skip any crop line during the detection, all the lines which have in Hough space a peak whose angle compared to the overall orientation (θlines) of the lines does not exceed 20◦are retained. Fig. 2 presents the ﬂowchart of the lines detection method. However, to avoid detecting more than one peak in an aggregation (reduce over- detection), every time that we identify a peak of a crop row

Algorithm 1: Crop lines detection.

input : skeletons output: crop lines


## 1 Computation of the skeletons angle


## 2 Computation of the main orientation θlines of the crop

lines


## 3 Hough transform of the skeletons H(θ, ρ)


## 4 Hnorm(θ, ρ)=H(θ, ρ)/Hones(θ, ρ)


## 5 while maximum of Hnorm(θ, ρ) > 0.1 do

6 Computation of the maximum of Hnorm(θ, ρ) and

the corresponding angle θm

7 Recovery of the line corresponding to the maximum

(Lineskeleton)

8 Computation of the normalized Hough transform

(Htemp(θ, ρ)) of the Lineskeleton

9 Hnorm(θ, ρ)=Hnorm(θ, ρ) −Htemp(θ, ρ)

10 if θm > θlines −20◦and θm < θlines + 20◦then

11 The detected line is a crop line

B. Unsupervised training data labeling

The unsupervised training dataset annotation is based on the detected lines obtained in previous section. According to hypothesis that the lines detected are mainly at the center of the crop rows (Fig. 3) we performed a mask to delimit the crop rows. Hence, the vegetation overlapped by the mask correspond to the crop. This mask is obtained from the intersection of superpixels formed by the simple linear iterative clustering (SLIC) algorithm [31] and the detected lines. SLIC is chosen since it is simple and efﬁcient in terms of results quality and computation time. It is an adaptation of k-means for superpixels generation with a control on size and compactness of superpixels. SLIC creates a local grouping of pixels based on their spectral values deﬁned by the values of the CIELAB color space and their spatial proximity. A higher value of compactness makes superpixels more regularly shaped. A lower value makes superpixels adhere to boundaries

4

Fig. 2: Flowchart of crop lines detection method.

(a) (b)

Fig. 3: From left to right lines detection in bean (a) and spinach (b) ﬁelds. Detected lines are in blue. In the spinach ﬁeld interline distance and the crop rows orientation are not regular. The detected lines are mainly in the center of the crop rows.

better, making them irregularly shaped. Since here the goal is to create a mask around the detected crop lines able to delimit the crop rows we have chosen a compactness of 20 because we found it was less sensitive to the variation of color caused by the effect of light and shadow. Fig. 4 shows examples of images segmented with different size of superpixels.

the potential weeds. Fig. 5 shows the mask of crop, interline weeds and potential weeds. To construct the training dataset, we extracted patches from the original images using positions of the detected inter-row weeds and crops. For weeds samples we performed bounding boxes on each segmented intra-row weed. For the crop samples, sliding window has been applied on the input image using positions relative to the segmented crop lines. Thus, for a given position of the window if it intersects the binary mask and there is no inter-lines weeds pixels we attribute it to the crop class. Generally, the crop class has much more samples than the weed. In the case that we have less interline weeds samples and in the same time we have a wide potential weeds as in Fig.5 we propose to collect

Once the crop is identiﬁed, next step consists in detection of the interlines weeds. Interline weed is plant which grows up in the interline crop. To detect weeds that lie in inter-row we performed a blob coloring algorithm. Hence any region that does not intersect with the crop mask is regarded as weed. Besides, vegetation pixels which do not belong to the crop mask neither to the interlines weeds are attributed to

5

(a) (b) (c)

Fig. 4: Examples of superpixels computed on images of dimensions N=7360×4912. From left to right, the image is segmented with a number of superpixels equal to 0.5% × N, 0.1%×N and 0.01% ×N respectively.

samples from the potential weeds. Hence, the window which contains only potential weeds is labeled as weeds. Windows which contain crop and potential weeds, where we have more potential weeds than crop are not retained.

[33] because it has shown a better result than AlexNet and VGG13 [34] in the ImageNet challenge. Due to abundant categories and signiﬁcant number of images in ImageNet, studies revealed the performance of transferability of networks trained with ImageNet dataset. Thus we performed ﬁne tuning to train the networks in our data. Fine-tuning means that we start with the learned features on the ImageNet dataset, we truncate the last layer (softmax layer) of the pre-trained network and replace it with new softmax layer that are relevant to our own problem. Here the thousand categories of ImageNet have been replaced by two categories (crop and weeds).

IV. EXPERIMENTS AND RESULTS


## Experiments were conducted on two different ﬁelds of

bean and spinach (Fig.6). The images are acquired by a DJI
Phantom 3 Pro drone that embeds a 36 MP RGB camera at
an altitude of 20 m. This acquisition system enables to obtain
very high resolution images with a spatial resolution about
0.35 cm.
To build the unsupervised training database, we selected
two different parts of given ﬁeld. The ﬁrst one (Part1) is used
to collect the training data and the other (Part2) for test data
collection.

Fig. 5: Detection of interline weeds (red) after lines detection (blue) in a bean image. The mask of crop is represented in green and the potential weeds in magenta.

C. Crop/Weeds classiﬁcation using Convolutional Neural Net- works

To create the crop binary mask after line detection the superpixels compactness have been set to 20 and the number of superpixels is equal to 0.1%×N, where N=7360×4912 (Fig.4b). In this experiments, we used a 64 by 64 window to create the weed and crop training databases. This window size provides a good trade off between plant type and overall information. A small window is not sufﬁcient to capture whole plant and can lead to confuse culture and non culture, because in some conditions crop and weed leaves have the same visual characteristics. In other hand, too large size presents a risk of having crop and weeds in the same window.

CNNs are a part of Deep learning approach, they showed impressive performances in many computer vision tasks [32]. CNNs are made up of two types of layers, the convolutional layers which extract different characteristics of images and the fully connected layers based on multilayer perceptron. The number of convolutional layers depends on the classiﬁcation task and also the number and the size of the training data.

In this work we used a Residual Network (ResNet), this network architecture was introduced in 2015 [33]. It won the ImageNet Large Scale Vision Recognition Challenge 2015 with 152 layers. However, according to the size of data we used the ResNet with 18 layers (ResNet18) described in

In the bean ﬁeld, the weeds present are thistles and young sprouts of potato from previous sowing on the same ﬁeld. This ﬁeld has few interline weeds so we have decided to

6

(a) (b)

Fig. 6: Example of images taken in the bean (a) and spinach ﬁelds (b). The bean ﬁeld has less interline weeds and is predominately composed of potential weeds. The inter-row distance is stable and the plant is sparse compared to the spinach ﬁeld which presents a dense vegetation in the crop rows and irregular inter-row distance. Spinach ﬁeld has more interlines weeds and it has few potential weeds.

TABLE I: Training and validation data in the bean ﬁeld.

include the potential weeds in weeds samples. After applying the unsupervised labeling method, the number of samples collected is 673 for weeds and 4861 for crops. Even with potential weeds the collected samples was unbalanced. To address this problem we realized data-augmentation. Hence we have performed 2 contrast changes, a smoothing with a Gaussian ﬁlter and 3 rotations (90◦, 180◦, 270◦). The strong heterogeneity in the ﬁelds can often be encountered from one part of the ﬁeld to another. This heterogeneity may be a difference of soil moisture, presence of straw, etc... In order to make our models robust to the background, we mixed samples with background and no background. Samples without background were obtained by applying ExG followed by Otsu’s thresholding on previously created samples (see Fig. 7). We evaluated the performance of our method by comparing models created by data labeled in supervised and unsupervised way.

Data Class Training Validation Total

Supervised Crop 17192 11694 28886 labeling Weed 17076 9060 16136 Total 34868 20754 45022

Unsupervised Crop 7688 1928 9616 labeling Weed 5935 1493 7428 Total 13623 3421 17044

background. The same processing has been applied on the supervised data. Table II presents the number of samples.

After the creation of both weed and crop classes, 80% of samples were selected randomly for the training, and the remaining ones were used for validation. The Tables I and II present the training and validation data performed on each ﬁeld.

The supervised training dataset were labeled by human experts. A mask is performed manually on the pixels of weeds and crops. Fig. 8 presents weeds manually delineated by an expert in red.

For ﬁnetuning we tested different values of the learning rate. The initial learning rate is set to 0.01 and updated every 200 epochs. The update is done by dividing the learning rate by factor of 10. Fig. 9 shows the evolution of the loss function during training for supervised and unsupervised datasets for spinach and bean ﬁelds. From these ﬁgures we can notice that the validation loss curves decrease during about the ﬁrst 80 epochs before to increase and to converge (behavior close to overﬁtting phenomenon). This overﬁting phenomenon is less emphasized in the supervised labeled data of bean. The best models were obtained during the ﬁrst learning phase with a learning rate of 0.01.

The supervised data collected were also unbalanced so we have carried out the same data augmentation procedure performed on the unsupervised data. The total number of samples is shown in the Table I.

The spinach ﬁeld is more infected than the bean ﬁeld, there are mainly thistles. In total 4303 samples of crop and 3626 samples of weed were labeled in unsupervised way. Unlike bean ﬁeld we have obtained a less unbalanced data. Therefore, the only data augmentation applied is adding samples without

Performance of models have been evaluated on test ground

7

(a) (b) (c) (d)

(e) (f) (g) (h)

Fig. 7: Example of crop and weed samples of size 64×64 with and without background. Bean: samples of crop (a and b), samples of weed. (c and d). Spinach: samples of crop (e and f) and samples of weed (g and h). Depending on the size of the plant and the position of the window we obtain a plant or aggregation of plants per window.

(a) (b)

Fig. 8: Parts of bean ﬁeld (a) and spinach ﬁeld (b) with the weeds labeled manually by an expert in red. The manual labeling has taken about 2 working days.

TABLE II: Training and validation data in the spinach ﬁeld.

TABLE III: Number of test samples used for each ﬁeld.

Data Class Training Validation Total

Field samples of crop Sample of weed

Supervised Crop 11350 2838 14188 labeling Weed 8234 2058 10292 Total 19584 4896 34772

Bean 2139 1852 Spinach 1523 1825

Unsupervised Crop 6884 1722 8606 labeling Weed 5800 1452 7252 Total 12684 3174 15858

their results are comparable. On both ﬁelds we remark that positive rate of 20% provides a true positive rate greater than 80%. The differences of performance between supervised and unsupervised data labeling are about 6% in the bean ﬁeld and about 1.5% in the spinach ﬁeld (Table IV). The performance gap in the bean ﬁeld can be explained by the low presence of weeds in the inter-row.

truth data collected in Part2 by supervised way on each ﬁeld, the Table III presents the samples. The performance of the classiﬁcation results are illustrated with Receiver Operating Characteristic (ROC) curves.

From the ROC curves (Fig.10) we can notice that the AUC (Area Under the Curve) are close to or greater than 90%. Although both types of learning data provide good results and

Both ﬁelds are infested mainly by thistles, we tested the robustness of our models by exchanging the samples of weeds from the bean ﬁeld with that of the spinach ﬁeld.

8

(a) (b)

(c) (d)

Fig. 9: Evolution of the loss during training for supervised and unsupervised data in the ﬁelds of spinach and bean. The validation loss curves decrease during about the ﬁrst 80 epochs before to increase and converging. First line represents the spinach ﬁeld and the second one the bean ﬁeld. The ﬁrst and second column are respectively the training on the the supervised and unsupervised data.

TABLE IV: Results on test data with ResNet18 network.

of images, we applied an overlapping window to classify each pixel in UAV images. For each position of the window the CNNs models provide the probability of being weeds or crops. Thus, the center of the extracted image is marked by a colored dot according to the probabilities. Blue, red and white dot mean respectively that the extracted image is identiﬁed as weed, crop and uncertain decision (Figs. 12a and 12c). Uncertain decision means the both probabilities are very close to 0.5. Thereafter, we used crop lines information and superpixels that have been created before, to classify all the pixels of the image. On each superpixel we look which color of dot has the majority. A superpixel is classed as crop or weed if the most represented dots are in blue respectively in red. For superpixels that have white dots as majority we used crop lines information. Hence, superpixels which are in the crop lines are regarded as crop and the others are weeds. The superpixels created in the background are removed. Figs. 12a and 12c present the classiﬁcation result in parts of spinach and bean ﬁelds. On those ﬁgures we remark that interline weeds and intra-line weeds have been detected with a low overdetection. Overdetections are mainly found on the edges of the crop rows where the window cannot overlap the whole plant. Some pixels of weeds are not entirely in red, because after performing the threshold on the ExG, the parts of these

Field AUC% of unsupervised AUC% supervised data labeling data labeling

Bean 88.73 94.84 Spinach 94.34 95.70

TABLE V: Results on test data with weeds data of the bean ﬁeld exchanged with that of the spinach ﬁeld.

Field AUC% of unsupervised AUC% supervised data labeling data labeling

Bean 91.37 93.25 Spinach 82.70 94.34

In Fig. 11 the results obtained show that despite the small samples harvested in the bean ﬁled, those data are suitable to the spinach ﬁeld and the model created with unsupervised labeling in the spinach ﬁeld is most sensitive to the presence of young potato sprouts among bean weed samples. Table V shows the results on test data with weeds data of the bean ﬁeld exchanged with that of the spinach ﬁeld.

In addition to the classiﬁcation evaluations on the patches

9

(a) (b)

Fig. 10: ROC curves of the test data with the unsupervised and supervised data labeling.From left to right the ROC curves computed on the bean (a) and spinach (b) test data.

(a) (b)

Fig. 11: ROC curves of test data with weeds data of the bean ﬁeld exchanged with that of the spinach ﬁeld. From left to right the ROC curves computed on the bean (a) and spinach (b) test data.

1.5% in the spinach ﬁeld and 6% in the bean ﬁeld. Supervised labeling is an expensive task for human experts and according to the gaps of accuracies between the supervised and the unsupervised labeling, our method can be a better choice in the detection of weeds, especially when the crop rows are spaced. The proposed method is interesting in terms of ﬂexibility and adaptivity, since the models can be easily trained in new dataset. We also found that ResNet18 architecture can extract useful features for classiﬁcation of weeds in bean or spinach ﬁelds with supervised or unsupervised data collection. In addition the developed method could be a key of online weeds detection with UAV. As future work we plan to use multispectral images because in some conditions near infra red could help to distinguish plant even if they have a similarity in the visible spectral and leave shape. With the near infra-red we plan also to improve the background segmentation.

plants which are less green are considered as soil.

However, the unsupervised data collection method depends strongly on the efﬁciency of the crop line detection method and also the presence of weeds in the interline. The used line detection approach has already shown its effectiveness in beet and corn ﬁelds in our previous work [35]. With the bean ﬁeld we found even if a ﬁeld does not have a lot of samples of weeds in the interline it is possible to create a robust model with data-augmentation. We also noticed using a deep learning architecture such as ResNet18 we can create robust models for classiﬁcation of weeds in bean or spinach ﬁelds with supervised or unsupervised data annotation. The main advantage of our method is that it is fully automatic and well suited for large scale training data.

V. CONCLUSION

In this paper, we proposed a novel fully automatic learning method using Convolutional Neuronal Networks CNNs) with unsupervised training dataset collection for weeds detection from UAV images taken in bean and spinach ﬁelds. The results obtained have shown close performance to the supervised data labeling ones. The Area Under Curve (AUC) differences are

VI. ACKNOWLEDGMENT

This work is part of the ADVENTICES project supported by the Centre-Val de Loire Region (France), grant number ADVENTICES 16032PR. We would like to thank the Centre- Val de Loire Region for supporting the work.

10

(a) (b)

(c) (d)

Fig. 12: Example of UAV image classiﬁcation with models created by unsupervised data in two different ﬁelds. From ﬁrst to the second line we have samples from spinach and bean ﬁelds. On the ﬁrst column we have the samples obtained after using sliding window, without crop lines and background information. Blue, red and white dot mean that the plants are is identiﬁed as weed, crop and uncertain decision respectively. On the second column we have the detected weeds in red after crop lines and background information have been applied.


## REFERENCES

[10] C. G´ee, J. Bossu, G. Jones, and F. Truchetet, “Crop/weed discrimina-

tion in perspective agronomic images,” Computers and Electronics in Agriculture, vol. 60, no. 1, pp. 49–59, 2008. [11] D. Woebbecke, G. Meyer, K. Von Bargen, and D. Mortensen, “Color

[1] European Crop Protection, “With or without pesticides? — ECPA,”

indices for weed identiﬁcation under various soil, residue, and lighting conditions,” Transactions of the ASAE, vol. 38, no. 1, pp. 259–269, 1995. [12] N. Otsu, “A threshold selection method from gray-level histograms,”

2017. [Online]. Available: http://www.ecpa.eu/with-or-without [2] E.-C. Oerke, “Crop losses to pests,” The Journal of Agricultural Science,

vol. 144, no. 01, p. 31, feb 2006. [3] F. J. Pierce and P. Nowak, “Aspects of Precision Agriculture,” 1999, pp.

IEEE Transactions on Systems, Man, and Cybernetics, vol. 9, no. 1, pp. 62–66, jan 1979. [13] P. V. C. Hough, “Method and means for recognizing complex patterns,”

1–85. [4] A. McBratney, B. Whelan, T. Ancev, and J. Bouma, “Future Directions

US Patent 3,069,654, vol. 21, pp. 225–231, dec 1962. [14] J. M. Pe˜na, J. Torres-S´anchez, A. Isabel De Castro, M. Kelly, and

of Precision Agriculture,” Precision Agriculture, vol. 6, no. 1, pp. 7–23, feb 2005. [5] J. Torres-S´anchez, F. L´opez-Granados, and J. M. Pe˜na, “An automatic

F. L´opez-Granados, “Weed Mapping in Early-Season Maize Fields Us- ing Object-Based Analysis of Unmanned Aerial Vehicle (UAV) Images,” PLoS ONE, vol. 8, no. 10, 2013. [15] T. Blaschke, “Object based image analysis for remote sensing,” ISPRS

object-based method for optimal thresholding in UAV images: Appli- cation for vegetation detection in herbaceous crops,” Computers and Electronics in Agriculture, vol. 114, pp. 43–52, 2015. [6] C. Zhang and J. M. Kovacs, “The application of small unmanned

Journal of Photogrammetry and Remote Sensing, vol. 65, no. 1, pp. 2–16, jan 2010. [16] L. Tang, L. Tian, and B. L. Steward, “Classiﬁcation of Broadleaf and

aerial systems for precision agriculture: a review,” Precision Agriculture, vol. 13, no. 6, pp. 693–712, dec 2012. [7] A. Dos Santos Ferreira, D. Matte Freitas, G. Gonc¸alves da Silva,

Grass Weeds Using Gabor Wavelets and an Artiﬁcial Neural Network,” Transactions of the American Society of Agricultural Engineers, vol. 46, no. 4, pp. 1247–1254, 2003. [17] H. Y. Jeon, L. F. Tian, and H. Zhu, “Robust crop and weed segmentation

H. Pistori, and M. Theophilo Folhes, “Weed detection in soybean crops using ConvNets,” Computers and Electronics in Agriculture, vol. 143, pp. 314–324, dec 2017. [8] M. D. Bah, E. Dericquebourg, A. Haﬁane, and R. Canals, “Deep learning

under uncontrolled outdoor illumination,” Sensors, vol. 11, no. 6, pp. 6270–6283, 2011. [18] F. Ahmed, H. A. Al-Mamun, A. S. M. H. Bari, E. Hossain, and P. Kwan,

based classiﬁcation system for identifying weeds using high-resolution UAV imagery,” in Computing Conference 2018, 2018. [9] E. Hamuda, M. Glavin, and E. Jones, “A survey of image processing

“Classiﬁcation of crops and weeds from digital images: A support vector machine approach,” Crop Protection, vol. 40, pp. 98–104, 2012. [19] M. Latha, A. Poojith, A. Reddy, and V. Kumar, “Image Processing in

techniques for plant extraction and segmentation in the ﬁeld,” Computers and Electronics in Agriculture, vol. 125, pp. 184–199, 2016.

Agriculture,” International Journal Of Innovative Research In Electrical,

11

Electronics, Instrumentation And Control Engineering, vol. 2, no. 6, pp. 2321–2004, 2014. [20] M. P´erez-Ortiz, J. M. Pe˜na, P. A. Guti´errez, J. Torres-S´anchez,

C. Herv´as-Mart´ınez, and F. L´opez-Granados, “Selecting patterns and features for between- and within- crop-row weed mapping using UAV- imagery,” Expert Systems With Applications, vol. 47, pp. 85–94, 2015. [21] A. Bakhshipour, A. Jafari, S. M. Nassiri, and D. Zare, “Weed seg-

mentation using texture features extracted from wavelet sub-images,” Biosystems Engineering, vol. 157, pp. 1–12, 2017. [22] A. Bakhshipour and A. Jafari, “Evaluation of support vector machine

and artiﬁcial neural networks in weed detection using shape features,” Computers and Electronics in Agriculture, vol. 145, pp. 153–160, feb 2018. [23] Y. LeCun, L. Bottou, Y. Bengio, and P. Haffner, “Gradient-based learning

applied to document recognition,” Proceedings of the IEEE, vol. 86, no. 11, pp. 2278–2323, 1998. [24] A. Krizhevsky, I. Sutskever, and G. E. Hinton, “ImageNet Classiﬁca-

tion with Deep Convolutional Neural Networks,” Advances In Neural Information Processing Systems, pp. 1–9, 2012. [25] C. Hung, Z. Xu, and S. Sukkarieh, “Feature Learning Based Approach

for Weed Classiﬁcation Using High Resolution Aerial Images from a Digital Camera Mounted on a UAV,” Remote Sensing, vol. 6, no. 12, pp. 12 037–12 054, dec 2014. [26] A. K. Mortensen, M. Dyrmann, H. Karstoft, R. Nyholm Jørgensen,

and R. Gislum, “Semantic Segmentation of Mixed Crops using Deep Convolutional Neural Network,” in CIGR-AgEng conference, 2016. [27] A. Milioto, P. Lottes, and C. Stachniss, “Real-time blob-wise sugar

beets vs weeds classiﬁcation for monitoring ﬁelds using convolutional neural networks,” ISPRS Annals of Photogrammetry, Remote Sensing and Spatial Information Sciences, vol. IV-2/W3, pp. 41–48, aug 2017. [28] M. Di Cicco, C. Potena, G. Grisetti, and A. Pretto, “Automatic model

based dataset generation for fast and accurate crop and weeds detection,” in 2017 IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS). IEEE, sep 2017, pp. 5188–5195. [29] G. Jones, C. G´ee, and F. Truchetet, “Modelling agronomic images for

weed detection and comparison of crop/weed discrimination algorithm performance,” Precision Agriculture, vol. 10, no. 1, pp. 1–15, 2009. [30] M. Montalvo, G. Pajares, J. M. Guerrero, J. Romeo, M. Guijarro,

A. Ribeiro, J. J. Ruz, and J. M. Cruz, “Automatic detection of crop rows in maize ﬁelds with high weeds pressure,” Expert Systems With Applications, vol. 39, no. 15, pp. 11 889–11 897, 2012. [31] R. Achanta, A. Shaji, K. Smith, A. Lucchi, P. Fua, and S. S¨usstrunk,

“SLIC Superpixels Compared to State-of-the-Art Superpixel Methods,” Pattern Analysis and Machine Intelligence, IEEE Transactions on, vol. 34, no. 11, pp. 2274–2282, 2011. [32] A. Kamilaris and F. X. Prenafeta-Bold´u, “Deep learning in agriculture: A

survey,” Computers and Electronics in Agriculture, vol. 147, pp. 70–90, apr 2018. [33] K. He, X. Zhang, S. Ren, and J. Sun, “Deep Residual Learning for

Image Recognition,” in 2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR). IEEE, jun 2016, pp. 770–778. [34] K. Simonyan and A. Zisserman, “Very Deep Convolutional Networks

for Large-Scale Image Recognition,” arXiv preprint arXiv:1409.1556, pp. 1–14, 2015. [35] M. D. Bah, A. Haﬁane, and R. Canals, “Weeds detection in UAV imagery

using SLIC and the hough transform,” in 2017 Seventh International Conference on Image Processing Theory, Tools and Applications (IPTA). IEEE, nov 2017, pp. 1–6.
