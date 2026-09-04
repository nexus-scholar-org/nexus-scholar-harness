---
workspace_id: SCI-001081
doi: 10.1109/m2garss52314.2022.9839758
title: Uncertainty Estimation in Deep Meta-Learning for Crop and Weed Detection from
  Multispectral UAV Images
authors:
- family_name: Khoshboresh-Masouleh
  given_name: M.
  orcid: null
- family_name: Shah-Hosseini
  given_name: R.
  orcid: null
year: 2022
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:41.429041+00:00'
---

# Uncertainty Estimation in Deep Meta-Learning for Crop and Weed Detection from Multispectral UAV Images

UNCERTAINTY ESTIMATION IN DEEP META-LEARNING FOR CROP AND WEED

DETECTION FROM MULTISPECTRAL UAV IMAGES

2022 IEEE Mediterranean and Middle-East Geoscience and Remote Sensing Symposium (M2GARSS) | 978-1-6654-2795-1/22/$31.00 ©2022 IEEE | DOI: 10.1109/M2GARSS52314.2022.9839758

Mehdi Khoshboresh-Masouleh and Reza Shah-Hosseini

School of Surveying and Geospatial Engineering, College of Engineering, University of Tehran, Tehran, Iran

m.khoshboresh@ut.ac.ir; rshahosseini@ut.ac.ir


## ABSTRACT

Knowing the confidence with which one can trust the crop 
and weed map is essential for decision-making in smart 
farming. In conventional deep learning approaches, crop 
and weed detection of the trained model can be just 
blindly assumed accurate but the truth is not. Due to the 
real observations in smart farming, uncertainty modeling 
should be an important stage of predictive algorithm 
output, such as crop and weed mapping. This study 
focuses on uncertainty estimation in deep meta-learning 
for crop and weed detection from multispectral UAV 
images by proposing a new deep meta-learning method 
based on squeeze-and-attention CNN. To build the 
effective trained model in crop and weed detection, deep 
meta-learning methods have been developed and prove to 
be a robust method in small training data. The proposed 
method achieves a mean IoU for the crop and weed 
detection of 88.5% and 86.5% for the multispectral UAV 
images based on the RedEdge-MX sensor.


> **Figure 1: Illustrations of spectral similarities between**

> crop and weed in multispectral UAV image. (a) RGB, (b) 
color infrared, (c) ground truth, and (d) legend. 
 
Due to the spectral similarities between crop and weed, 
visual crop and weed detection is an extremely difficult 
problem in smart farming based on Unmanned Aerial 
Vehicle (UAV) imagery (Fig. 1). Despite recent 
breakthroughs in deep learning and UAV imaging, 
confident and robust crop and weed detection remain a 
challenge for smart farming (also known as precision 
agriculture or E-agriculture) [3], [4]. In general, the crop 
and weed detection of the trained model can be just 
blindly assumed accurate but the truth is not for decision 
making in smart farming. In smart farming, uncertainty 
modeling should be an important stage of predictive 
output due to the real observations. 
Deep meta-learning can perform on unseen tasks after 
training a few labeled data and considers several tasks to 
produce a predictive function [5]–[7]. In this study, we 
developed 
the 
Squeeze-and-Attention 
Convolutional 
Neural Network (also known as SA-CNN) for crop and 
weed detection. SA-CNN is the newest deep meta-
learning method in remote sensing [8]. 
We aim to fill important gaps in the uncertainty estimation 
in deep meta-learning based on developed SA-CNN for 
crop and weed detection from large-scale remote sensing 
images (e.g., multispectral UAV images).  Our motivation

Index Terms— Target detection, deep meta-learning,  uncertainty estimation, multispectral UAV images


## 1. INTRODUCTION

High-resolution mapping from crops and weeds is a 
fundamental topic in precision farming and is critical for 
various agricultural scene understanding issues based on 
multispectral images. In precision farming, high-
resolution mapping based on multispectral images 
formulated as a task of predicting the category of the crop 
and weed in each spectral channel (e.g., red, green, blue, 
red edge, and near infrared) that the pixel belongs to. 
However, the interest in developing high-resolution 
mapping methods from multispectral UAV images is 
rapidly increasing due to high precisions, and lower costs 
compared to traditional methods (e.g., ground-based 
sensors). Weed monitoring in a farm field is the first and 
most important step in a site-specific crop and weed 
management mission. Weed in farm fields dramatically 
reduces the quality and quantity of the crops and impede 
the growth of the crops by competing with the crop for 
resources including light, moisture, and nutrients [1]. 
Moreover, weeds occupy a large space in the farm field 
thus space left for growing crops is get reduced. In this 
regard, timely crop and weed monitoring in the farm fields 
is extremely important to obtain high-quality production 
[2].

165 978-1-6654-2795-1/22/$31.00 ©2022 IEEE M2GARSS 2022

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:40:51 UTC from IEEE Xplore.  Restrictions apply.

behind the employment of SA-CNN and multispectral  UAV images is to create a confident trained model to  detect the crop and weed in the farm fields that focus on  small training data.

confidential crop and weed detection as a pixel-wise  problem.


## 3. PROPOSED METHOD

A visual summary of the proposed method for crop and 
weed detection is presented in Figure 3. The proposed 
method takes the DeepMultiFuse [4] as the main 
backbone model. DeepMultiFuse is a lightweight CNN 
model with a model size of 85MB for pixel-wise 
segmentation. This model is trained using a small dataset 
(200 samples with a size of 480×360 pixels) that includes 
multispectral UAV images, which helps the generalization 
ability of the trained model. To reduce the class imbalance 
issue related to conventional loss functions, a loss 
function designed based on the weighted binary cross-
entropy and the focal loss for crop and weed mapping.


## 2. RELATED WORK

In real world, annotating images is very expensive so 
developing a robust method based on small training data 
is important. One of the major advantages of deep meta-
learning methods is their capability to perform end-to-end 
optimization and low training data. Figure 2 shows 
statistics relating to the number of papers at the theoretical 
basis of deep meta-learning (blue) and deep meta-learning 
in image segmentation (red) from January 2011 until June 
2021. The number of papers in deep meta-learning in 
image segmentation (e.g., target detection) is increasing 
rapidly as can be observed from Figure 2.


> **Figure 2: Number of papers published per year [9].**

> Based on Figure 2, a common deep meta-learning method 
is pre-trained a CNN on the large-scale dataset and fine-
tuning it on another task. For example, a model trained on 
the ImageNet dataset [10] can be used in another patch-
wise classification problem, because the ImageNet dataset 
contains over 1000 classes. This method is known as 
transfer learning [11] and requires a big dataset for 
training and which parameters to fine-tune. However, 
transfer learning focuses on a limited number of selected 
tasks (e.g., patch-wise classification). 
In [5], a Model-Agnostic Meta-Learning (MAML) 
method was evaluated for remote sensing image 
classification and segmentation. MAML extends gradient 
descent by optimizing for a model initialization that leads 
to good performance on a set of related tasks. In [4], a 
gated encoder-decoder CNN, called DeepMultiFuse, is 
proposed for pixel-wise weed detection in sugar beet 
fields from multispectral UAV images. Recently, a new 
deep meta-learning method, called SA-CNN, based on 
uncertainty estimation for target detection is proposed for 
RGB images [8]. To the best of the authors’ knowledge, 
although the related algorithms are fairly powerful for 
object detection, there is not still good performance for


> **Figure 3: The proposed SA-CNN for crop and weed**

> detection from multispectral images. MF denotes the 
MultiFuse, and SA denotes squeeze-and-attention. 
 
The proposed method learns non-local spatial-spectral 
representations features and therefore overcomes the 
constraints of convolutional layers and masks generation

166

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:40:51 UTC from IEEE Xplore.  Restrictions apply.

for crop and weed detection. To aggregate multistage non- local features, we adopt SA blocks on the multistage  outputs of the DeepMultiFuse model, resulting in better  crop and weed boundaries. The SA-CNN block is defined  as follows:

multispectral samples with a size of 480×360 pixels and a  ground sample distance of 1cm.


## 4. EXPERIMENTAL RESULTS

In this study, experimental scenarios in Rheinbach, 
Germany are used to study crop and weed detection 
assessment, which are from [13]. Visualization of crop 
and weed results of the test set for the proposed method is 
shown in Figure 4. The entropy measure for uncertainty 
map and the intersection-over-union (IoU) for the 
classified map are used for evaluating the effectiveness of 
the proposed method. IoU is formulated as [14]:

( ) ( ) ( ) ( ) ( ) ( )

=  +

SA UP ReLU f Pooling input x

att res

(

(1)

UP ReLU f Pooling input

(

att

where UP denotes the up-sampled function to expand the  output of the attention channel, fatt represents the attention  function, xres denotes the residual feature map.  In this study, we focus on Monte Carlo dropout [12] as the  epistemic and aleatoric uncertainty estimator for crop and  weed detection. Epistemic is uncertainty over the actual  values of a model's parameters arising from the finite size  of the training images and aleatoric is an uncertainty  metric of the intrinsic, irreducible noise found in the  image, usually associated with the image acquisition  process. The proposed method is trained using the 100

TP IoU

TP FN FP =

(2)

+ +

where TP denotes the true positive pixels, FN denotes the  false negative pixels, and FP denotes the false positive  pixels.


> **Figure 4: Crop and weed detection results from multispectral UAV images. In an uncertainty map, darker color**

> represents a larger value and more uncertainty.

167

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:40:51 UTC from IEEE Xplore.  Restrictions apply.

[3] M. H. Asad and A. Bais, “Weed detection in canola fields  using maximum likelihood classification and deep convolutional  neural network,” Information Processing in Agriculture, vol. 7,  no. 4, pp. 535–545, Dec. 2020, doi: 10.1016/j.inpa.2019.12.002.    [4] M.  Khoshboresh-Masouleh  and  M.  Akhoondzadeh,  “Improving weed segmentation in sugar beet fields using  potentials of multispectral unmanned aerial vehicle images and  lightweight deep learning,” JARS, vol. 15, no. 3, p. 034510, Aug.  2021, doi: 10.1117/1.JRS.15.034510.    [5] M. Ruswurm, S. Wang, M. Korner, and D. Lobell, “Meta- Learning for Few-Shot Land Cover Classification,” Jun. 2020,  pp. 788–796. doi: 10.1109/CVPRW50498.2020.00108.    [6] M. Huisman, J. N. van Rijn, and A. Plaat, “A survey of  deep meta-learning,” Artif Intell Rev, vol. 54, no. 6, pp. 4483– 4541, Aug. 2021, doi: 10.1007/s10462-021-10004-4.    [7] C. Finn, “Learning to Learn with Gradients,” PhD Thesis,  EECS Department, University of California, Berkeley, 2018.    [8] M.  Khoshboresh-Masouleh  and  R.  Shah-Hosseini,  “Building panoptic change segmentation with the use of  uncertainty estimation in squeeze-and-attention CNN and remote  sensing observations,” International Journal of Remote Sensing,  vol.  42,  no.  20,  pp.  7798–7820,  Oct.  2021,  doi:  10.1080/01431161.2021.1966853.    [9] “Scopus preview - Scopus - Welcome to Scopus.”  https://www.scopus.com/home.uri (accessed Sep. 23, 2021).    [10] J. Deng, W. Dong, R. Socher, L.-J. Li, K. Li, and L. Fei- Fei, “ImageNet: A large-scale hierarchical image database,” in  2009 IEEE Conference on Computer Vision and Pattern  Recognition,  Jun.  2009,  pp.  248–255.  doi:  10.1109/CVPR.2009.5206848.    [11] S. J. Pan and Q. Yang, “A Survey on Transfer Learning,”  IEEE Transactions on Knowledge and Data Engineering, vol.  22,  no.  10,  pp.  1345–1359,  Oct.  2010,  doi:  10.1109/TKDE.2009.191.    [12] Y. Gal and Z. Ghahramani, “Dropout as a Bayesian  Approximation: Representing Model Uncertainty in Deep  Learning,” in Proceedings of The 33rd International Conference  on Machine Learning, Jun. 2016, pp. 1050–1059. Accessed: Sep.  23,  2021.  [Online].  Available:  https://proceedings.mlr.press/v48/gal16.html    [13] I. Sa et al., “WeedMap: A Large-Scale Semantic Weed  Mapping Framework Using Aerial Multispectral Imaging and  Deep Neural Network for Precision Farming,” Remote Sensing,  vol. 10, no. 9, Art. no. 9, Sep. 2018, doi: 10.3390/rs10091423.    [14] M. Khoshboresh-Masouleh and R. Shah-Hosseini, “A Deep  Multi-Modal Learning Method and a New RGB-Depth Data Set  for Building Roof Extraction,” Photogrammetric Engineering &  Remote Sensing, vol. 87, no. 10, pp. 759–766, Oct. 2021,  doi:10.14358/pers.21-00007r2.


> **Figure 5 shows the quantitative results for crop and weed**

> detection from the proposed method. The proposed 
method achieves a mean IoU for the crop and weed 
detection of 86.5% and 88.5% for the 4 tested images, 
respectively, while the mean entropy for the crop and 
weed detection of the proposed method is 25.3%. 
In an uncertainty map, a higher value of entropy 
represents a darker color and more uncertainty. As a 
result, there is a strong inverse relationship between IoU 
and uncertainty in crop and weed detection. Experimental 
results verified this point for the proposed method, but this 
inverse relationship is not linear and depends on network 
structure.


> **Figure 5: Accuracy assessment of crop and weed**

> detection for different sample images with the proposed 
method.


## 5. CONCLUSIONS

The purpose of this study is to investigate the capabilities 
of uncertainty estimation in deep meta-learning for smart 
farming. In this paper, using the SA-CNN and 
DeepMultiFuse, an efficient method was presented and 
implemented for crop and weed detection from 
multispectral UAV images. The proposed method can 
make automatic detection possible with a relatively 
inexpensive multispectral UAV image, with full coverage 
of different regions.


## REFERENCES

[1] M. Pérez-Ortiz, J. M. Peña, P. A. Gutiérrez, J. Torres-
Sánchez, C. Hervás-Martínez, and F. López-Granados, “A semi-
supervised system for weed mapping in sunflower crops using 
unmanned aerial vehicles and a crop row detection method,” 
Applied Soft Computing, vol. 37, pp. 533–544, Dec. 2015, doi: 
10.1016/j.asoc.2015.08.027. 
 
[2] P. Lottes, R. Khanna, J. Pfeifer, R. Siegwart, and C. 
Stachniss, “UAV-based crop and weed classification for smart 
farming,” in 2017 IEEE International Conference on Robotics 
and Automation (ICRA), May 2017, pp. 3024–3031. doi: 
10.1109/ICRA.2017.7989347.

168

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:40:51 UTC from IEEE Xplore.  Restrictions apply.
