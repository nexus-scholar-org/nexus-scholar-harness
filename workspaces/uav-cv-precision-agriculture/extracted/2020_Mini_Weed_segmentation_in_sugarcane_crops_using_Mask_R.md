---
workspace_id: SCI-000136
doi: 10.1109/csci51800.2020.00088
title: Weed segmentation in sugarcane crops using Mask R-CNN through aerial images
authors:
- family_name: Mini
  given_name: Gabriel Alberto
  orcid: null
- family_name: Oliva Sales
  given_name: Daniel
  orcid: null
- family_name: Luppe
  given_name: Maximilian
  orcid: null
year: 2020
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:40.640614+00:00'
---

# Weed segmentation in sugarcane crops using Mask R-CNN through aerial images

2020 International Conference on Computational Science and Computational Intelligence (CSCI)

Weed segmentation in sugarcane crops using Mask

2020 International Conference on Computational Science and Computational Intelligence (CSCI) | 978-1-7281-7624-6/20/$31.00 ©2020 IEEE | DOI: 10.1109/CSCI51800.2020.00088

R-CNN through aerial images

Gabriel Alberto Mini Department of Electrical and Computer Engineering (SEL-EESC-USP)

Daniel Oliva Sales Institute of Mathematics and Computer Sciences (ICMC-USP)

Maximilian Luppe Department of Electrical and Computer Engineering (SEL-EESC-USP)

University of S˜ao Paulo

University of S˜ao Paulo

University of S˜ao Paulo

S˜ao Carlos, Brazil Email: gabriel.mini@usp.br

S˜ao Carlos, Brazil Email: dsales@usp.br

S˜ao Carlos, Brazil Email: maxluppe@sc.usp.br


## Abstract—In this paper we describe an approach to detect

weed regions in sugarcane crops using Mask Regions with
Convolutional Neural Networks (Mask R-CNN) on aerial im-
ages. Experiments were held with twelve combinations using
ResNet-50 and ResNet-101 as backbones. We used both “trained
from scratch” and transfer-learning from pre-trained datasets
combined with image augmentation techniques for training. The
ResNet-101 model with pre-trained COCO achieved an Average
Precision (AP50) of 65.5% and obtained values of 0.803, 0.707
and 0.752 for Precision, Recall and F1 score. These results suggest
a potential use of Mask R-CNN for weed mapping using aerial
images.

Recently, alternative methods to segment regions on an image are based on CNN, such as Regions with CNN (R-CNN) [9] and posteriorly Mask R-CNN [10]. Recent work by [11] suggests the use of Mask R-CNN for detection and strawberry harvesting, and they achieved an average precision rate of 95.78% and a recall of 95.41% on 100 test images. Another recent work uses a method inﬂuenced by Mask R-CNN to segment instances of apple ﬂowers, obtaining values of 59.4% in mean Average Precision (mAP) and 0.9643, 0.9537, and 0.9590 of recall, precision and F1score [12]. According to [13], in some areas of agriculture deep learn- ing techniques have not been used appropriately, and large datasets are needed to train. Furthermore, the lack of available datasets leads the researchers to create their own datasets, becoming an onerous and challenging task [13].

Index Terms—Sugarcane, Weed Mapping, Mask R-CNN, In- stance Segmentation, Unmanned Aircraft System

I. INTRODUCTION

Sugarcane (Saccharum sp.) farms cover approximately 12% of Brazil’s planted area (about 9.6 million hectares in May 2019) [1]. This amount corresponds to around 38% of global production, 74% of the Americas [2]. The presence of weed in sugarcane crops can reduce crop yield between 12% to 72% [3]. Also, this is a serious problem for most crops, such as soybean, where the competitive ability and density of weeds reduce the purity and the commercial value of grains [3].

Moreover, few studies deal with a real and feasible solution for real farming conditions that employ drone imagery to detect weeds. Almost all studies surveyed using machine learning in aerial images proposed the use of Vertical Take-Off and Land (VTOL) drones, such as DJI Phantom multirotor, and there is only one study exploring ﬁxed-wing drones to map weeds [4]. Some faulty questions have been addressed to VTOL’s use in precision agriculture, including costs, en- durance, and ﬂight range limitation [14].

A study by [3] reports losses of R$ 9 bi a year in soybean crops in Brazil. In the USA, average cost per hectare is US$50 as a result of glyphosate resistance in corn. In the worst cases, some resistant populations can reduce yield above 75% in soybean and up to 70% on wheat [3].

Aiming to provide a solution for real farming scenarios, we present in this paper an approach to detect and classify regions of broadleaf and grass weeds through a Mask R-CNN on sugarcane farms, using images gathered using a ﬁxed- wing unmanned aircraft system (UAS). We tested multiple training scenarios using data augmentation, transfer learning, and backbone architectures such as ResNet-50 and ResNet- 101.

In [4], Site-Speciﬁc Weed Management (SSWM) [5] was studied in comparison to an uniform herbicide application. Authors proved an increase in biomass production while also saving herbicide. This way, the development of techniques for accurately detect weed regions in crops has a very important role.

Convolutional Neural networks (CNN) has been widely used for this task. [6] developed a CNN algorithm to recognize plant diseases achieving an accuracy between 91% and 98% on test datasets. However, the author mentions there is no commercial solution yet. The study of [7] developed a CNN to detect weeds types in soybean crops using aerial images and they compared with other classiﬁcation methods. They obtained an average accuracy of 99.5% using AlexNet [8].

II. MATERIALS AND METHODS

A. Image Dataset

A ﬁxed-wing Xmobots Arator 5A UAS equipped with a Sony ILCE-5100 RGB camera was used for image acquisition. Flights were performed between 120 and 240 m AGL (above ground level), resulting in a spatial resolution (Ground Sample Distance - GSD) between 2.7 and 5.8 cm/pixel. Six different

978-1-7281-7624-6/20/$31.00 ©2020 IEEE DOI 10.1109/CSCI51800.2020.00088

485

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:37:58 UTC from IEEE Xplore.  Restrictions apply.

geolocated orthomosaics were obtained for each ﬁeld, gener- ated in Pix4d software. The experimental ﬁelds are located in the state of S˜ao Paulo in Brazil, within a radius of 300 km with the centroid coordinates 21◦53′42.21′′S 49◦52′4.64′′W. The total area estimated is nearly 559 ha.

B. Training and Inference

The training algorithm is a modiﬁed version of the shapes1

tutorial that uses a Mask R-CNN [10], [15]. The script was adapted to receive the input images and masks produced by the extractor python script, as described in section II-A1. Several combinations of initial weights, backbone architecture, and image augmentation were tested. Table I shows how these arrangements are organized.

1) Samples Extraction: The regions of the images were annotated manually in order to build the image dataset, helped by an agronomist. The ﬁrst step to annotate images is to slice the orthomosaic into patches of 512x512 pixels. This size is the input size for the training and inference algorithm. A python script was written to slice the orthomosaic into small regions to annotate and extract masks (See section II-B3).

Backbone Augmented Initial Weights Model

From Scratch R50-NA-S Imagenet R50-NA-I Coco R50-NA-C



This software, called as “Extractor”, uses the library wx- Python version 4.0.4 for the user interface. The Extractor exports a masked image having one or more instances/weed types, determined by a level of weed infestation on an image. Mask regions are exported according to the following rules:

ResNet-50

From Scratch R50-A-S Imagenet R50-A-I Coco R50-A-C



From Scratch R101-NA-S Imagenet R101-NA-I Coco R101-NA-C



1) A class number represents each region (e.g., 1 is broadleaf class, 2 is grass class), except by number zero, which is the background class. The respective class must ﬁll the entire region. 2) The mask image requires to be in tiff format; data type uint8; lossless compression; with one channel. The original image size and the mask size must be equal. An amount of 1100 images were selected considering the weed incidence. 100 of them were used only for ﬁnal validation. All selected sliced images had their weed regions identiﬁed manually according to weed types, such as broadleaf (Ricinus communis; Ipomoea spp.; Mucuna spp. and Mo- mordica charantia) and grass weeds (Panicum maximum; Cyn- odon dactylon; Cyperus rotundus and Brachiaria decumbens). This resulted in 12364 regions annotated, being 8165 broadleaf regions and 4199 grass weeds regions. Sugarcane and ground were not annotated since both were considered as background class. The validation dataset is composed of 724 broadleaf samples and 752 grass samples, computing 1476 samples.

ResNet-101

From Scratch R101-A-S Imagenet R101-A-I Coco R101-A-C



TABLE I ALL TRAINING CONFIGURATION MODELS TESTED ON THIS WORK.

The inference algorithm is also inﬂuenced by shapes tutorial1. However, the inference image is opened using OpenCV instead of a random sample image in memory. In this work, we use an output conﬁdence threshold of 75%, ignoring all detections below this value. Both training and inference software work in the Graphical Processing Unit (GPU) with a tensorﬂow-gpu implementation compatible with Nvidia CUDA.

1) Hyperparameters: From all 1100 images, 800 were selected for training and 200 for validation, resulting in the 80/20 common train-validation split ratio. The remaining 100 images were selected for ﬁnal tests. These ﬁnal test images were not present in any training process in order to deliver an unbiased evaluation result.

2) Data Augmentation: The augmentation used in this work was inﬂuenced by the survey of [13] and [6] paper. However, afﬁne and perspective transformations were not performed, avoiding a higher training time. Figure 1 shows how the dataset was augmented.

This work uses three training stages, similar to the CrowdAI mapping challenge [16]. Each stage trains speciﬁc layers, so other layers are frozen and not updated. These training stages are speciﬁed as:

1) Heads: Responsible to mask generation [10]. 2) Conv 4 and upper layers: In this stage, only convo- lutional layers: conv4, conv5, and fully connected layer are trained [17]. 3) All: All trainable layers are enabled to train and update their respective weight values.


> **Table II shows the hyperparameters comparison between**

> training stages, including epochs and trainable layers.

Fig. 1. Demonstration of how the dataset was augmented. The highlighted “F” on upper left represents the original image extracted from orthomosaic. The other 7 “Fs” are the result of augmentation process. Below the horizontal line, an example using a real image is shown.

1https://github.com/matterport/Mask RCNN/blob/master/samples/shapes/ train shapes.ipynb

486

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:37:58 UTC from IEEE Xplore.  Restrictions apply.

Epochs Learning Rate Enabled Layers Stage 1 1 to 79 10−3 only heads Stage 2 80 to 149 10−3 conv 4 and up Stage 3 150 to 200 10−4 all

B. Training Summary

All graphs were obtained from two sources of data: the ﬁrst is from tensorﬂow training logs, with training loss, validation loss, training start and duration across all epochs. The second source is from a script designed to test all epochs in an exclusive set of 100 images - the validation dataset. The ﬁrst graph, presented in Fig. 3, shows the values of loss and validation loss in all training stages. Training loss values are represented by solid lines, and validation loss by dotted lines.

TABLE II HYPERPARAMETERS CONFIGURATION IN EACH STAGE. THE COLUMN ENABLED LAYERS SHOWS THE NAME OF LAYERS ALLOWED TO TRAIN AT

THE RESPECTIVE STAGE.

In both backbones tested, the overﬁtting seems more likely to aggressively appear with the pre-trained COCO dataset (with or without the augmented dataset). After the ﬁrst training stage, in both backbones (Figure 3), the validation loss quickly increases across the second stage, indicating clues of overﬁt- ting. The lowest values of loss were obtained on the backbone ResNet-101 (Figure 3b), despite the signiﬁcant values of validation loss. All models trained from scratch showed no signs of overﬁtting. Furthermore, a loss stabilization can be observed in ResNet-50 and ResNet-101 at stages 2 and 3. Visibly, the training of the second stage resulted in a decrease of training loss, when the curve begin to converge. All curves acted as expected, except by the high increase of validation loss at the second stage.

2) Initial Weights and Transfer-learning: We tested three scenarios of initial weights: two of them used transfer learning or pre-trained models and one scenario was trained from scratch with randomly initialized weights. Pre-trained models such as Imagenet [18] and the COCO dataset [19] were used. The matterport library makes available functions to download both pre-trained models [15].

3) Hardware and software: All training was performed at the Euler cluster2 in a node with hardware conﬁguration: a GPU Nvidia Tesla P100 (16GB), two processors Intel Xeon E5-2650v4 of base clock 2.2 GHz with 12 cores; RAM 128 GB DDR3 1866MHz and operational system CentOS Linux (7.2.1511) and Altair PBS Pro. The runtime version of Nvidia GPU libraries are cudnn 7.0; cuda-toolkit 9.0.176.

All scripts and algorithms use Python language version 3.6.8 with libraries: tensorﬂow-gpu 1.9.0, OpenCV 4.0.0 and numpy 1.14.5.

C. Performance of Stages


> **Figure 4 shows the progress of AP50 across training stages**

> and epochs. This graph was chosen to evaluate how the
training stages could inﬂuence the ﬁnal result of AP50 in both
backbones. The ﬁnal epoch AP50 are presented in Table III to
demonstrate the difference between trained models; Also, the
mAP and AP75 are shown.

III. RESULTS A. Employed Metrics

In this work, we use three metrics used in MS COCO Challenge [20] for object segmentation: AP50 (from PASCAL VOC [21]), AP75 (also called as strict metric) and mAP. Furthermore, this work also uses traditional metrics to evaluate the trained models: Recall (R), Precision (P), and F1 score [22].

The AP50 curves are similar, however, the ResNet-101 per- formed slightly better than ResNet-50. As expected, all aug- mented datasets performed better than those not augmented. Also, the pre-trained COCO dataset performed better than others. Interestingly, it is possible to see a smooth decrease in AP50 between stage 2 and stage 3 of training, especially on augmented with pre-trained COCO. So, the last stage gives no beneﬁt to training, except for trained from scratch models.

A real example is shown on Figure 2. In PASCAL VOC Challenge, the overlap percentage (ao) must exceed 50 % of area between ground truth to be considered an applicable detection [23].

Overall

Model mAP AP50 AP75

Precision Recall F1 score R50-NA-S 0.156 0.436 0.063 0.681 0.526 0.594 R50-NA-I 0.191 0.505 0.077 0.719 0.574 0.638 R50-NA-C 0.247 0.573 0.156 0.696 0.653 0.671 R50-A-S 0.220 0.526 0.135 0.680 0.624 0.650 R50-A-I 0.245 0.571 0.144 0.737 0.630 0.679 R50-A-C 0.267 0.610 0.165 0.717 0.673 0.694 R101-NA-S 0.120 0.346 0.037 0.676 0.416 0.515 R101-NA-I 0.190 0.503 0.085 0.681 0.574 0.623 R101-NA-C 0.219 0.530 0.118 0.710 0.600 0.650 R101-A-S 0.221 0.530 0.126 0.662 0.625 0.641 R101-A-I 0.252 0.603 0.150 0.739 0.663 0.699 R101-A-C 0.284 0.655 0.185 0.803 0.707 0.752

Fig. 2. Examples of detection types in object segmentation. Regions in green are annotated ground truth regions; regions in red are predicted by the algorithm. The ﬁgure (a) shows an original region for comparison. Figure (b) is an example of True Positive (Tp), where the algorithm correctly predicts region A with 86% of overlap. Figure (c) is an example of False Negative (Fn), when the algorithm does not detect the ground truth. In ﬁgure (d) two circumstances of False Positive (Fp) or regions classiﬁed incorrectly are shown: the ﬁrst, labeled as B, is a correct detection but has an insufﬁcient overlap of 23%; the second case, labeled as C, is a wrong detection region.

TABLE III RESULTS OF ALL METRICS AVERAGED IN BOTH CLASSES AT EPOCH 200. ALL METRICS USED IN THIS TABLE ARE DEFINED IN SECTION III-A. THE

BEST VALUES ARE PRESENTED IN BOLD.

2https://sites.google.com/site/clustercemeai/recursos/sistema

487

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:37:58 UTC from IEEE Xplore.  Restrictions apply.

Fig. 3. Validation loss (dotted lines) and training loss (solid lines) across the training epochs. Results of backbone architectures ResNet-50 (a) and ResNet-101 (b). The equivalent color lines have an identical conﬁguration in initial weights and dataset augmentation for both backbones.

Fig. 4. Curves of AP50 across all training epochs showing the training progress in all stages. Results of ResNet-50 (a) and ResNet-101 (b). The AP50 was extracted using the test dataset at the end of every epoch.

of Fp is considerable. Besides that, the number of broadleafs wrongly classiﬁed as a grass and vice versa is lower compared to undetected regions; this represents 2.8% of total ground truths. Broadleaf regions were classiﬁed better than grass considering Fp and Fn obtained. Some of these results are explained in section III-E.

D. Training Results

As mentioned in section III-A, this work uses a compilation of two analysis types, found in several articles that use image segmentation algorithms [10]–[12], [24], [25]. The following sections present each analysis.

1) Object Classiﬁcation: Table III also shows the results for Precision, Recall, and F1-score, considering overall between two weed types values. The most signiﬁcant values were achieved from ResNet-101 using an augmented dataset and COCO as pre-trained weights. The recall, precision and F1- score values of COCO are better than Imagenet; except in cases R50-A-I and R50-NA-I where Precision is better than models trained with COCO. All models trained from scratch showed the worst performance in comparison to pre-trained models, augmented or not.

Ground Truth Predicted Class Background Broadleaf Grass

Background * 80 135 Broadleaf 168 537 19 Grass 225 22 505

TABLE IV THE CONFUSION MATRIX OF THE BEST TRAINED MODEL (R101-A-C). VALUES IN BOLD ARE Tp. THE ASTERISK (*) VALUE IS A TRUE NEGATIVE

AND REPRESENTS A BACKGROUND CLASSIFIED AS BACKGROUND

The confusion matrix (Table IV) shows a signiﬁcant number of ground truth regions not detected (Fn). Also, the number

488

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:37:58 UTC from IEEE Xplore.  Restrictions apply.

2) Object Segmentation Results: All AP50 values are present at table III. The best AP50 values obtained are from R101-A-C (65.5%) and R50-A-C (61.0%). Notably, the con- ﬁguration with augmentation and pre-trained COCO dataset performs better than other arrangements for both backbones.

E. Visual Results


> **Figure 5 shows some examples of correct classiﬁcations**

> of broadleaf (red) and grass (blue). All of these images are
classiﬁcations from the model R101-A-C. The conﬁdence
values are annotated inside the respective region.

Fig. 6. Example of misclassiﬁcation types found. Conﬁdence scores are present inside the weed region in white color. Red and blue colors represent Broadleafs and Grass weed types, respectively. (a) and (b) were classiﬁed for both types in the same weed region. (c) and (d) were not detected in all weed region surrounded by the yellow line. (e) and (f) are incorrect classiﬁcations: (e) corresponds to grass weed regions and (f) to Broadleaf region.

Fig. 5. Example of correct classiﬁcations in samples of 100 x100 px. Red and blue colors represent Broadleafs and Grass weed types, respectively.

Three types of wrong classiﬁcations were found. The ﬁrst misclassiﬁcation, presented in 6a, and 6b are regions classiﬁed twice in different classes. In this case, the evaluation algorithm recognizes only the ﬁrst detection as correct and sets other regions as incorrect, even if they are in the same class. According to [23], multiple detections of the same regions are considered false detections. Another problem found (6c and 6d) is related to Fn regions, or regions not detected. Table IV shows this problem as a common drawback. The last problem is the inverted classiﬁcation, displayed in ﬁgure 6e and 6f, where broadleaf is classiﬁed as a grass and vice versa. All of these results can be observed more clearly in the confusion matrix (Table IV).

Fig. 7. Examples of a signiﬁcant drawback when multiple Tp regions are classiﬁed as Fp or Fn, producing a wrong classiﬁcation by Mask R-CNN. Blue and red colors are for grass and broadleaf, respectively. Subﬁgures shows examples of small regions classiﬁed as Fp. Therefore, the ground truth not detected results in a Fn due to insufﬁcient IoU. The ground truth column is composed by hand-annotated regions. The inference column shows the regions predicted by Mask R-CNN.

Moreover, other classiﬁcation problems were found when observing the inference results: some weed regions with correct class association presents weeds nearly connected classiﬁed as one single region, or vice-versa. Figure 7a shows three ground truth annotations and ﬁve inference detections. In this case, only two regions were classiﬁed as Tp, whereas the other three were considered as Fp due to the insufﬁcient IoU overlap. Also, in ﬁgure 7a, the largest region is considered a Fn because no region detected overlaps sufﬁciently. In the same way, ﬁgure 7b classiﬁed only two regions as correct instead of three. Technically, in both ﬁgures, all regions are correct. Another example is shown in ﬁgure 7c, and 7d, where central regions classiﬁed as Fp; however, if both regions were combined, the algorithm would classify correctly.

IV. DISCUSSION

A. Training Process

As described in section III-B, training reached overﬁtting using pre-trained COCO and Imagenet datasets. This behavior is consistent with [24] work, which used Mask-RCNN to characterize Arctic Ice-Wedge Polygons in aerial imagery. They observed overﬁtting after the eighth epoch and suggested two main causes: the use of a pre-trained COCO dataset and a small training data (subset of 340 images of 600x600 pixels). The AP50 decreases in stages 2 and 3 (See ﬁgure 4) due to overﬁtting and leads to reduction of Mask R-CNN generalization ability.

489

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:37:58 UTC from IEEE Xplore.  Restrictions apply.

Contrary to what was expected, the last stage of training provided no signiﬁcant beneﬁts to AP50 in all models. The third stage trains all layers of Mask R-CNN, with a learning rate of 10−4. The low value of the learning rate might be a signiﬁcant reason for stabilizing AP50 values in all trained models at the last stage, evidencing the need for a model ﬁne- tunning. Further work is required to ﬁne-tune the learning rate to extract the best performance in the second and third stages.

The survey of [13] considers the demand for large datasets as a signiﬁcant difﬁculty. Furthermore, the author mentions the need for some hundred images depending on problem complexity. Studies related to this work are using dataset sizes from 340 to 2000 images [11], [12], [24]. Unfortunately, the sample limitation in this work is attributed to a low number of orthomosaics available for sample extraction.

In general, it can be suggested that the increase in training datasets can be beneﬁcial to reduce overﬁtting. The overﬁtting pattern is not observed in validation loss curves from pre- trained Imagenet or training from scratch, which uses ran- domly initialized weights. The results obtained from tested models show that the use of transfer learning combined with an augmented dataset results in a better performance.

A previous study showed that Resnet-101 is not substan- tially better than ResNet-50 [11], and this was also observed in our study. Table III shows AP50 values of 65.5% and 61.0%, respectively. In summary, these results show that Resnet-50 can be suitable to detect weeds, also being a less complex backbone than Resnet-101. Also, it demands a lower training time.

This is consistent to a review of [13] that cites the use of transfer learning in 11 different works. In this work, we also mention some recent works that used transfer learning [6], [11], [24], [25]. The study of Barbedo [28] lists several factors that inﬂuence deep learning, including transfer learning to reduce the demand for massive datasets. They also states that use of dataset augmentation brings a better generalization of the model and this is coherent with this work results.

B. Metrics

The traditional Precision, Recall and F1 score are used as an evaluation metric for unranked sets [26]. In other words, these types of metrics do not need the item relevance resulting from Mask R-CNN conﬁdence output. [23] suggests the accuracy measure is not helpful when the distribution over classes is highly skewed. In another work, it is also explained why accuracy is an inappropriate measure [26]. Precision and recall focus on measuring Tp or percentage of relevant items retrieved.

D. Visual Results

Some misclassiﬁcation occurred. The most common is the Fn (Ground Truth not detected). In some cases, the model classiﬁes the region correctly but IoU is insufﬁcient to consider it as a valid detection (See Figure 6). The inversion of classes is the most severe case of misclassiﬁcation because broadleaf and weed have different shapes, colors, and textures. However, this trouble is not common, as observed at the confusion matrix (table IV). [23] mentions that the conﬁdence level allows evaluation of the trade-off between Tp and Fp, being a sign for a reasonable ﬁne tuning on conﬁdence threshold.

The review of [13] states that possibly there is a trade-off among metrics, as an example of a high recall (most weeds are detected), where undetected weeds are a signiﬁcant drawback - sustaining the idea that a lower precision could be satisfactory.

Some similar work from other study ﬁelds were found, mainly in remote sensing [11], [12], [24]. The original im- plementation [10] shows values of 60.0% in AP50 using a ResNeXt-101-FPN with the COCO dataset. This work archived a value o 65.5% using ResNet-101 with the model R101-A-C. The results of the current study are consistent with the original work. However, other studies achieved more remarkable results [12], [25] (84.8% and 84.6%, respectively). The [11] work presents values of Recall, Precision and mIoU as 0.9578, 0.9541, and 0.8985; Unfortunately values of mAP were not presented. Since no similar study was found using Mask R-CNN for weed detection using aerial images until the present investigation, the comparison of mAP values in this work is quite challenging.

Another problem is that the annotation of the weed region is entirely subjective, mainly when weeds are very close to each other, or do not have a deﬁned boundary. Figure 7 is a central example of how annotation can affect the number of Fp and Fn. No similarities were found about this limitation on surveyed studies. However, for further work is reasonable to improve the algorithm in order to build merged regions of identical classes as output masks.

V. CONCLUSION

This work evaluated several training combinations using different backbones, initial weights, and augmentation tech- niques. The most promising model is ResNet-101, with a pre- trained COCO dataset and data augmentation. This study has shown interesting results besides the weaknesses addressed to the limited number of images and a signiﬁcant number of Fp and Fn. As observed, the training stages can inﬂuence the performance of Average Precision and must be ﬁne-tuned in order to obtain the best model performance. The model also shows better results when transfer-learning and augmentation were used, proving that these aspects are beneﬁcial to train a Mask R-CNN model.

C. Training data

The training dataset is highly skewed since there is a natural predominance of broadleafs in a proportion of two broadleafs for each grass region. These unbalanced classes explain the worst performance of grass in all metrics.

The systematic study of [27] concludes that the class imbalance on convolutional neural networks is harmful and the impacts of imbalanced data depends on the distribution among classes. They suggest oversampling or undersample techniques, and they also conclude that oversampling does not cause overﬁtting [27].

490

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:37:58 UTC from IEEE Xplore.  Restrictions apply.

Unfortunately, the imbalance of classes can affect the ﬁnal result as observed with grass weeds, and for further work, the use of dataset undersampling or oversampling is suggested, including the increase of training dataset. This way, more tests are needed in order to ﬁnd the optimal training dataset.

[13] A. Kamilaris and F. X. Prenafeta-Bold´u, “Deep learning in agriculture: A

survey,” Computers and Electronics in Agriculture, vol. 147, pp. 70–90, apr 2018. [14] A. Matese, P. Toscano, S. Di Gennaro, L. Genesio, F. Vaccari, J. Prim-

icerio, C. Belli, A. Zaldei, R. Bianconi, and B. Gioli, “Intercomparison of UAV, Aircraft and Satellite Remote Sensing Platforms for Precision Viticulture,” Remote Sensing, vol. 7, no. 3, pp. 2971–2990, mar 2015. [15] W. Abdulla, “Mask R-CNN for object detection and instance segmentation on Keras and TensorFlow,” https://github.com/matterport/Mask RCNN, 2017. [16] S. P. Mohanty, “CrowdAI Mapping Challenge 2018 : Baseline with

The present research enhances the understanding of how parameters such augmentation, weight initialization and back- bones can inﬂuence training, bringing analytical data for further research. Due to the lack of studies on this ﬁeld, this approach can be a starting point for studies using UAS for weed regions detection. This study contributes to several real-world applications, including but not limited to intelligent herbicide patch spraying, crop counting and statistical analysis of weed infestation.

Mask RCNN,” https://github.com/crowdai/crowdai-mapping-challenge- mask-rcnn, 2018. [17] K. He, X. Zhang, S. Ren, and J. Sun, “Deep Residual Learning for

Image Recognition,” dec 2015. [18] J. Deng, W. Dong, R. Socher, L.-J. Li, K. Li, and L. Fei-Fei, “ImageNet:

A Large-Scale Hierarchical Image Database,” in CVPR09, 2009. [19] T. Y. Lin, M. Maire, S. Belongie, J. Hays, P. Perona, D. Ramanan,

P. Doll´ar, and C. L. Zitnick, “Microsoft COCO: Common objects in context,” Lecture Notes in Computer Science (including subseries Lec- ture Notes in Artiﬁcial Intelligence and Lecture Notes in Bioinformatics), vol. 8693 LNCS, no. PART 5, pp. 740–755, 2014. [20] COCO Challenge, “Common Objects in Context - Detection Evaluation.” [Online]. Available: https://cocodataset.org/#detection-eval [21] M. Everingham and J. Winn, The PASCAL Visual Object Classes

VI. ACKNOWLEDGEMENTS

Research carried out using the computational resources of the Center for Mathematical Sciences Applied to Industry (CeMEAI), funded by FAPESP (grant 2013/07375-0). The authors would like to thank Xmobots Aeroespacial e Defesa for having supported all stages of this research.

Challenge 2012 (VOC2012) Development Kit, 2012. [Online]. Available: http://host.robots.ox.ac.uk/pascal/VOC/voc2012/devkit doc.pdf [22] D. Harman, “Evaluation issues in information retrieval,” Information

Processing and Management, vol. 28, no. 4, pp. 439–440, 1992. [23] M. Everingham, L. Van Gool, C. K. I. Williams, J. Winn, and


## REFERENCES

A. Zisserman, “The Pascal Visual Object Classes (VOC) Challenge,” International Journal of Computer Vision, vol. 88, no. 2, pp. 303–338, jun 2010. [24] W. Zhang, C. Witharana, A. Liljedahl, and M. Kanevskiy, “Deep Con-

[1] Sistema IBGE de Recuperac¸˜ao Autom´atica, “Levantamento Sistem´atico

da Produc¸˜ao Agr´ıcola - maio 2020,” 2020. [Online]. Available: https://sidra.ibge.gov.br/home/lspa/brasil [2] Food and Agriculture Organization of the United Nations, “FAOSTAT

volutional Neural Networks for Automated Characterization of Arctic Ice-Wedge Polygons in Very High Spatial Resolution Aerial Imagery,” Remote Sensing, vol. 10, no. 9, p. 1487, sep 2018. [25] E. Kilic and S. Ozturk, “A subclass supported convolutional neural

Databass,” 2018. [Online]. Available: http://www.fao.org/faostat/en/ #data/QC [3] F. S. Adegas, L. Vargas, D. L. P. Gazziero, D. Karam, A. F. ds Silva, and

network for object detection and localization in remote-sensing images,” International Journal of Remote Sensing, vol. 40, no. 11, pp. 4193–4212, jun 2019. [26] M. and Rashmi, Introduction to Information Retrieval Systems. Cam- bridge University Press, 2015, vol. 3, no. 4. [27] M. Buda, A. Maki, and M. A. Mazurowski, “A systematic study of

D. Agostinetto, “Impacto econˆomico da resistˆencia de plantas daninhas a herbicidas no Brasil Introduc¸˜ao,” Circular T´ecnica, vol. 132, p. 12, 2017. [4] F. Castaldi, F. Pelosi, S. Pascucci, and R. Casa, “Assessing the potential

of images from unmanned aerial vehicles (UAV) to support herbicide patch spraying in maize,” Precision Agriculture, vol. 18, no. 1, pp. 76– 94, feb 2017. [5] C. Fern´andez-Quintanilla, J. M. Pe˜na, D. And´ujar, J. Dorado, A. Ribeiro,

the class imbalance problem in convolutional neural networks,” Neural Networks, vol. 106, pp. 249–259, oct 2018. [28] J. G. Barbedo, “Factors inﬂuencing the use of deep learning for plant

and F. L´opez-Granados, “Is the current state of the art of weed monitoring suitable for site-speciﬁc weed management in arable crops?” Weed Research, vol. 58, no. 4, pp. 259–272, aug 2018. [6] S. Sladojevic, M. Arsenovic, A. Anderla, D. Culibrk, and D. Stefanovic,

disease recognition,” Biosystems Engineering, vol. 172, pp. 84–91, aug 2018.

“Deep Neural Networks Based Recognition of Plant Diseases by Leaf Image Classiﬁcation,” Computational Intelligence and Neuroscience, vol. 2016, pp. 1–11, jun 2016. [7] A. dos Santos Ferreira, D. Matte Freitas, G. Gonc¸alves da Silva,

H. Pistori, and M. Theophilo Folhes, “Weed detection in soybean crops using ConvNets,” Computers and Electronics in Agriculture, vol. 143, pp. 314–324, dec 2017. [8] A. Krizhevsky, I. Sutskever, and H. Geoffrey E., “ImageNet Classiﬁca-

tion with Deep Convolutional Neural Networks,” Advances in Neural Information Processing Systems 25 (NIPS2012), pp. 1–9, 2012. [9] R. Girshick, J. Donahue, T. Darrell, and J. Malik, “Rich feature

hierarchies for accurate object detection and semantic segmentation,” Proceedings of the IEEE Computer Society Conference on Computer Vision and Pattern Recognition, pp. 580–587, 2014. [10] K. He, G. Gkioxari, P. Dollar, and R. Girshick, “Mask R-CNN,”

Proceedings of the IEEE International Conference on Computer Vision, vol. 2017-Octob, pp. 2980–2988, 2017. [11] Y. Yu, K. Zhang, L. Yang, and D. Zhang, “Fruit detection for strawberry

harvesting robot in non-structural environment based on Mask-RCNN,” Computers and Electronics in Agriculture, vol. 163, p. 104846, aug 2019. [12] Y. Tian, G. Yang, Z. Wang, E. Li, and Z. Liang, “Instance segmentation

of apple ﬂowers using the improved mask R–CNN model,” Biosystems Engineering, vol. 193, pp. 264–278, may 2020.

491

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:37:58 UTC from IEEE Xplore.  Restrictions apply.
