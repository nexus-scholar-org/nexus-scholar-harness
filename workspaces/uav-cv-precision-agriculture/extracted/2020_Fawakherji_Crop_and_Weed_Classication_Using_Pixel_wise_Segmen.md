---
workspace_id: SCI-000084
doi: 10.35708/rc1869-126258
title: Crop and Weed Classication Using Pixel-wise Segmentation on Ground and Aerial
  Images
authors:
- family_name: Fawakherji
  given_name: Mulham
  orcid: null
year: 2020
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:46:37.713664+00:00'
---

# Crop and Weed Classication Using Pixel-wise Segmentation on Ground and Aerial Images

International Journal of Robotic Computing Vol. 2, No. 1 (2020) 39-57 © KS Press, Institute for Semantic Computing Foundation DOI: 10.35708/RC1869-126258

Crop and Weed Classication Using Pixel-wise

Segmentation on Ground and Aerial Images

Mulham Fawakherji1, Ali Youssef1, Domenico D. Bloisi2, Alberto Pretto3, and

Daniele Nardi1


## 1 Department of Computer, Control, and Management Engineering,

Sapienza University of Rome, Rome, Italy

nardi@diag.uniroma1.it 2 Department of Mathematics, Computer Science, and Economics, University of Basilicata, Potenza, Italy

domenico.bloisi@unibas.it 3 IT+Robotics Srl, Padova, Italy alberto.pretto@it-robotics.it

Received (11/10/2018)

Revised (06/18/2019) Accepted (11/25/2019)

Articial Intelligence (AI) is a key tool in agriculture for implementing sus- tainable strategies for weed control. In traditional weed control, the agro-chemical inputs are uniformly applied to the eld, while innovative approaches using AI aim at minimizing the usage of chemical inputs thanks to local applications. In this paper, we focus on agricultural robotics systems that address the weeding problem by means of selective spraying or mechanical removal of the detected weeds. We present a set of deep learning based methods designed to enable a robot to eciently perform an accurate weed/crop classication from RGB or RGB+NIR (Near Infrared) images. In particular, we use two Convolutional Neural Networks (CNNs) to simplify and speed up the training process. A rst encoder-decoder segmentation network is designed to perform a "plant-type ag- nostic" segmentation between vegetation and soil. Each plant is hence classied between crop and weeds by using a second network, depending on the type of pipeline, for patch-level or pixel-level classication. We introduce also a third CNN, specically designed for setups with limited resources, like in small UAVs (Unmanned Aerial Vehicles), that exploits the proposed encoder-decoder seg- mentation network to eciently estimate crop/weeds local statistics. Quantita- tive experimental results, obtained using multiple publicly available datasets, demonstrate the eectiveness of the proposed approaches.

40 M. Fawakherji et al.

Keywords: Precision agriculture; crop/weed classication; image segmenta- tion.

1 Introduction

Autonomous robotics applications for precision agriculture represent a concrete solution towards a sustainable agriculture and chemical treatments reduction [5]. The term crop denes the cultivated plant, while the term weeds denes unwanted plants that grow spontaneously in the eld. Precision weed control is a challenging task that aims to reduce the amount of herbicides without com- promising the quality of crops. Since achieving that manually is time-consuming and expensive, selective spraying or accurate mechanical removal of weeds are preferable options.

Autonomous robots equipped with automatic weed detection systems (e.g., Fig. 1a) can be used to improve the eciency of precision farming techniques on weed control by modulating herbicide spraying appropriately to the level of weeds infestation. However, the great variety of crop and weeds shapes, size and colors,

(a)

(b) (c)

Fig. 1: (a) The robot used to acquire some of the datasets used in the experi- ments. (b) An example of RGB image provided by the camera mounted on the robot. (c) Label mask with bounding boxes predicted by our approach for image (b). Crop pixels are colored in green while weed pixels are colored in red.

Crop and Weed Classication . . . 41

Fig. 2: The proposed three-steps crop/weed detection approaches. The two pipelines (blue and green boxes) share the rst two steps. The rst step is a binary pixel-wise segmentation (i.e., soil/plant) of the RGB input image. The sec- ond step concerns the extraction of the image patches to be classied. Crop/weed classication is carried out in the third step, by means of a patch-based clas- sication CNN for the rst pipeline, and a segmentation CNN applied to the extracted patches for the second pipeline.

together with the presence of overlaps between plants, makes the automatic image based crop/weeds classication problem (see Fig. 1b,c) a challenging task for autonomous farming robots [13]. Moreover, when using supervised methods, the capability to generalize of the trained models still remains an obstacle to employ farming robots in dierent farm conditions caused by environmental changes, dierent plants characteristics, and types of soil [16,12].

In this paper, we present two novel pipelines (Fig. 2) that combine a ro- bust pixel-wise segmentation CNN, designed to be trained once to generalize the vegetation/soil segmentation problem, with a specialized crop/weeds classica- tion network, designed to be trained for each type of cultivation with a specic, reduced size dataset. The aim of the proposed approaches is to reduce the limi- tations of CNNs in generalizing when a limited amount of data with pixel-wise annotations is available: pixel-wise labeling is in fact the bottleneck for most crop/weeds classication methods. Our methods relies on a robust binary seg- mentation that aims to be agnostic to plant species, so easily trainable also by using external, ready to use pixel-wise labeled datasets that possibly do not includes the target crop. Specically, we use here a deep convolutional encoder- decoder architecture for robust background (soil) removal and the extraction of regions of interest (ROIs). The chosen network is based on the UNet architec- ture [19] with a modied VGG-16 encoder [23] followed by a binary pixel-wise classication layer. A coarse-to-ne classier based on CNN is used to classify the extracted ROIs into crop and weeds. The classication between crop and weeds is obtained feeding a classication or a segmentation CNN (depending on the pipeline, see Fig. 2) with image patches (i.e., bounding boxes) enclosing plant instances extracted by using the obtained vegetation/soil segmentation mask. Both these architectures have the advantage of requiring smaller datasets comparing to conventional 3-classes soil/crop/weeds classication systems. They

42 M. Fawakherji et al.

Fig. 3: Left: a multirotor UAV. Right: the Jetson TX2 embedded board that can be easily installed on an UAV.

just require a small dataset to specialize on the target crop species. The gener- ation of the specialized datasets is even more simple for the rst pipeline (see the blue box in Fig. 2) since it is not required pixel-wise labeling, but only one label for each bounding box. We extensively tested the introduced approaches by using 4 dierent datasets, showing good classication results and generalization properties.

To further validate our approach and to provide a more ecient classication pipeline, we introduce also a third pipeline designed for setups with limited resources, like in small UAVs (e.g., Fig. 3 left). The third pipeline is shown in Fig. 4. It exploits the proposed encoder-decoder segmentation network and it is used to address the 3-classes segmentation problem with RGB-NIR images as input. We added a post-processing step that, starting from the segmented image, divides it into a xed size grid and then computes for each cell the crop/weeds statistics (i.e., weed distribution and segmentation condence). We implemented this pipeline on an NVIDIA Jetson TX2 embedded board (Fig. 3 right) and we evaluated it on real data coming from two datasets acquired by UAVs.

Fig. 4: Crop/weeds detection pipeline for limited resources systems.

Crop and Weed Classication . . . 43

In summary, the main contributions of this work are:

 A context independent background removal method that uses a CNN based

pixel-wise segmentation to distinguish between soil and plants.  Two accurate three-steps crop/weed detection pipelines based on the intro-

duced segmentation network.  A computationally ecient method for estimating the crop and weed dis-

tribution that exploits a modied version of the introduced segmentation network to be used on embedded GPU boards.

The reminder of the paper is organized as follows. Section 2 contains a discus- sion of similar approaches found in the literature. Section 3 describes the details of the proposed method, while Section 4 shows both qualitative and quantita- tive results obtained on publicly available data. Finally, conclusions are drawn in Section 5.

2 Related Work

The problem of vision based crop and weeds classication has been addressed in dierent ways. Handcrafted features are used, among others, in [3,7]. De Rainville et al. [3] present an unsupervised classication method based on morphological features extracted taking into account the spatial localization of vegetation in the eld. Haug et al. [7] present a method to classify carrot plants and weeds from RGB and near-infrared (NIR) images that uses a background removal step based on the Normalized Dierence Vegetation Index (NDVI) and a Random Forest classier applied to features extracted at sparse pixel positions. The ap- proach described in [7] has been extended in [13], where a plant arrangement prior is added to the features list used for classication, and tailored for UAVs (Unmanned Aerial Vehicles) applications in [14].

The adoption of deep CNNs in overcoming the limitations of handcrafted features has been explored, among others, in [9,18,12]. Fine-tuned pre-trained CNN models are used for plant classication of 44 dierent species in [9]. Potena et al. [18] proposes an on-line perception system for weed-crop classication that uses a cascade of two dierent CNNs. A shallow CNN performs vegetation de- tection, while a second, deeper CNN discriminates between weeds and crops. Encoder-decoder architectures such as the SegNet segmentation network [1] are used in [21,16,4]. In [21], a SegNet network is fed with three channels images that include the NIR channel, the red channel from the RGB image, and the NDVI map. A similar approach is exploited in [16], where 14 channels images that include several vegetation indices are used as input for a modied version of the SegNet network. Synthetic training datasets are used to train a SegNet network in [4] by randomizing the key features of the target environment (i.e., crop and weed species, type of soil, and light conditions). The fully convolutional network (FCN) proposed in [22] is employed in [12,11]. In [12], the authors ex- ploits the crop arrangement as an additional source of information, by analyzing image sequences that cover a portion of the eld. Class-wise stem detection and pixel-wise crop/weeds semantic segmentation is jointly addressed in [11]. Model

44 M. Fawakherji et al.

Algorithm 1 The proposed crop/weed classication algorithm

1: Input: RGB image IRGB 2: Result: A set of classied blobs Bc 3: M ←Segmentation of IRGB using VGG-UNet 4: C ←Contour-Extraction(M) ▷set of contours belonging to connected regions 5: for i in range len(C) do 6: BM[i] ←BoundRect(C[i]) ▷BM[i] is the bounding box around the contour i 7: BRGB[i] ←(IRGB ∩BM[i]) ▷BRGB[i] is the corresponding bounding box from RGB image 8: Bc[i] ←(classify BRGB[i] using VGG-16 into weed or crop) ▷for the rst pipeline, or: 9: Bc[i] ←(segment BRGB[i] using VGG-UNet deep CNN into soil, weed or crop) ▷for the second pipeline 10: end for

compression and mixtures of lightweight CNNs are exploited in [15] to learn from a very deep, pre-trained model a lighter model which allows real-time weed seg- mentation also for robots with limited computing power. Multi-spectral features and 3D surface features are exploited for plant classication in [24].

The approach described in this paper builds upon our previous work pre- sented in [6]. Here, we introduce two new pipelines (see the blue box in Fig. 2 and Fig. 4) and we extend the experimental evaluation by using new datasets end by presenting additional results.

3 Methods

Our goal is to process an input RGB or multispectral image of the eld to extract semantic information. In particular, we present three pipelines to obtain:

1. A 3-steps pixel-wise image segmentation into 3 classes (i.e., weed, crop, and soil) for the rst two pipelines (see Fig. 2 and Sec. 3.1); 2. A 2-steps coarse-grained weed and crop density for the third pipeline (see Fig. 4 and Sec. 3.3).

The third pipeline is designed to reduce the computational burden while providing still accurate information with a lower resolution. We describe below each step involved in the three pipelines.

3.1 Pixel-wise Segmentation

The two pipelines of Fig. 2 take an RGB image as input and share the rst two steps, i.e., vegetation segmentation and patches extraction, to achieve the clas- sication goals exploiting two dierent approaches, i.e., on patch (Sec. 3.2) and pixel level (Sec. 3.2). All the steps of our full crop/weeds pixel-wise segmentation method are given in Algorithm 1.

Vegetation Segmentation To remove the background (i.e., the soil), we rstly apply a robust pixel-wise soil/plant segmentation of the RGB image in input. We use a modied version of the UNet semantic segmentation network

Crop and Weed Classication . . . 45

[19], which is composed by a contracting encoder along with a symmetric expand- ing decoder. In our implementation, the contracting path consists of a VGG-16 structure modied by removing the last fully connected layers and ne-tuning the other layers. The indices of spatial information in the pooling operations are spread through the expansive path, which contains a sequence of up-convolution operations of features encoded in the contracting path. The expanding decoder is designed with 4-convolutional layers, where each layer is composed of a batch normalization, 4-upsampling layers and a soft-max pixel-wise classier. Between the contracting and expanding paths, there is a bottleneck consisting of two con- volutional layers combined with batch normalization and a dropout activation function.

The lack of pixel-wise annotated datasets for each possible crop type and for dierent eld conditions can lead to strong challenges in generalizing an end-to- end crop/weeds segmentation network. The goal of the rst step is to obtain a robust binary segmentation mask that enables to generate blobs corresponding to vegetation pixels in the RGB image, so to simplify the following classication step. This is obtained by exploiting the similarities of various plants properties instead of dierentiate between them. The idea is to train the rst segmentation network by exploiting external, ready to use datasets coming from dierent con- texts, containing dierent plants categories, types of elds, and captured under varying environmental conditions. This context-independent training possibly enables to avoid to pixel-wise annotate large amount of data acquired in the target led, an operation that usually requires a lot of manual work.

3.2 Patches Extraction

The second step concerns the extraction of the image ROIs to be classied. This is obtained by extracting the vegetation blobs contained in the binary mask generated during the segmentation process. In this stage, the input consists in the original RGB image plus the binary mask generated during the segmentation process. A dilation operator is applied to the binary mask to gradually increase the boundaries of the foreground regions (i.e., the areas containing vegetation pixels) to reduce the holes between those regions. Then, the connected blobs from the dilated mask are extracted, and a bounding box for each blob is determined. Finally, a set of patches from the original RGB image corresponding to the bounding boxes is generated. Patch-Wise Classication A deep CNN for crop/weed classication is em- ployed for patch-wise classication. The image patches identied in the previous step are fed to the CNN classier, which is based on a ne-tuned model of VGG-16 exploiting the ability of deep CNN in object classication. The VGG- 16 network architecture for object classication is used as encoder. The network consists of 13-convolutional layers with a kernel of 3×3. A max-pooling operation with a kernel of 2×2 with a stride of 2 for down-sampling. Batch normalization and a ReLU activation function are used too. This step just requires a training dataset that includes labeled patches with positive and negative examples of the target crop. The annotation of such training dataset just requires to specify a label for each image that is a much faster operation than a pixel-wise annotation.

46 M. Fawakherji et al.

Fig. 5: Details of the architecture of the rst pipeline.

Fig. 5 shows the details of the rst pipeline. To create the gure, we have used a ne-tuned VGG-16 encoder model at early step of the training, showing randomly picked up lters to illustrate the ability of the network to learn weights based on neurons responses to image pixels (e.g., soil/plant pixel).

Pixel-Wise Classication In this step, we classify each pixel in the image patches identied in the previous step into one of three classes (soil, weed, and crop). To perform the segmentation, we used the same deep CNN architecture that is used for vegetation segmentation with 128×128 input size and three classes output.

3.3 Weeds Distribution Estimation

The goal of the pipeline shown in Fig. 4 is to process images, e.g., acquired by a limited resources system like a small UAV, to quickly extract high-level information about the eld, like weed and crop density, instead of nding the exact location for weed inside the images. This high-level information can be sent to a ground robot equipped with more powerful computational resources to perform a ne-grained pixel-wise segmentation (e.g., Sec. 3.1) and to perform selective spraying. We rst train a CNN to build a model able to detect crop and weed in the images, then we compute the distribution of the weed and the crop with a condence based on the output of the trained model.

Crop/Weed Segmentation To perform pixel-wise segmentation of the in- put image into 3 classes (i.e., weed, crop, and soil), we use a modied version of the UNet semantic segmentation network [19], very similar to the one intro- duced in Sec. 3.1, lled with one or three channels e.g., NIR, red, and/or the Normalized Dierence Vegetation Index (NDVI) [20].

Crop and Weed Classication . . . 47

Crop/Weed Distribution Estimation To compute the distribution of weed and crop inside the image, the mask generated during the segmentation process is divided using a xed size grid (28 cells) based on the segmentation output size. Then, we compute for each cell the crop/weeds statistics (e.g., weed distribution and segmentation condence). The distribution for a specic class in each cell is obtained by computing the number of pixels of that class inside the cell (Kc) divided by the total number of pixel inside the cell (see Eq. 1).

Dc = Kc Pn

(1)

i=1 Ki

where Dc represent the distribution of class c, n is the number of classes, and Kc is the total number of pixels belonging to class c inside the cell. For each cell, we also compute a per-class condence MConc as the average of the class probabilities P(·) provided by the network of Fig. 4 for all the cell pixels Xi that are classied with class c, i.e.:

PKc

i=1 P(Xi = c)

MConc =

(2)

Kc

4 Experimental Results


## Experiments are organized into four case studies:


## 1. The rst one (see Sec. 4.3) aims to demonstrate the performance of dierent

deep CNN architecture on pixel-wise segmentation in order to classify pixels
in image into two (soil and vegetation) or three classes (soil, crop, and weed).
2. In the second experiment (see Sec. 4.4), we study the eect of supporting
the input of our deep CNN (described in Sec. 3.1) by increasing the number
of input channels by a set of vegetation indices.
3. The third experiment (see Sec. 4.5) evaluates the performance of the two full
pipelines described in Sec. 3.1, where the rst one performs patch classi-
cation after background removal and blob extraction, where the second one
performs pixel-wise segmentation on the extracted patches.
4. The last experiment (see Sec. 4.6) aims at measuring the accuracy of the
pipeline shown in Fig. 4.

4.1 Datasets

In our experiments, we have used six datasets, some of them publicly available.

 Sunowers: 500 images acquired in a sunowers eld by a custom-built agri-

cultural eld robot;  SugarBeets: 10000 sugar beets images coming from the "Sugar Beets 2016"

datasets [2];  Carrots: 60 images acquired on a commercial organic carrots farm [8];  Stuttgart: 200 sugar beets coming from the so-called Stuttgart dataset;  UAV1: 155 multispectral images (NIR, Red) plus the NDVI index acquired

from an UAV in a sugar beets eld;

48 M. Fawakherji et al.

 UAV2: 75 multispectral images (NIR, Red) plus the NDVI index acquired

from an UAV in a corn eld.

All datasets are labeled with three classes (i.e., soil, crop and weed). Ground truth annotations consist in binary masks generated via manual segmentation. An intensity value of 1 in the binary masks corresponds to the segmented crop, 2 to segmented weeds, and pixels with 0 value correspond to the background soil.

4.2 Evaluation Metrics

For quantitatively evaluate the results, we used the following three metrics com- monly used in the literature [17].

Mean Intersection-Over-Union (mIOU):

C X

TPj TPj + FPj + FNj

mIOU = 1

(3)

C

j=1

Recall:

Recallj = TPj TPj + FNj

(4)

Precision:

Precisionj = TPj TPj + FPj

(5)

where TP stands for True Positive, FP for False Positive, FN for False Negative, and C is the total number of classes.

4.3 Architecture Evaluation

The rst experiment aims to demonstrate the performance of dierent deep CNN architectures on pixel-wise segmentation in order to classify pixels in image into three classes, namely soil, crop, and weed. Then, we measure the performance of the same networks on the background removal problem, i.e., pixel classication into only two classes: soil and plants. For this experiment, we use only RGB images as input to:


## 1. SegNet [1] based on VGG-16 encoder;

2. UNet [19];
3. UNet based on VGG-16 decoder (VGG-UNet);
4. BonNet [17];
5. Fully connected network FCN8 [10].

The training dataset is made of a set of 500 sunowers images. Data aug- mentation was performed using rotations, horizontal and vertical ipping, and zooming. The nal dataset was composed by 2000 images (see Fig. 6).

VGG-UNet has been trained by initializing the encoder (VGG-16) with the weights taken from training the VGG-16 on the ImageNet dataset, then we trained the whole network using Stochastic Gradient Descent (SGD) with a xed learning rate of 1 · e−4 and a momentum of 0.90. The parameters of the

Crop and Weed Classication . . . 49


> **Table 1: Quantitative results showing mIOU obtained by dierent networks**

> architectures on the Sunowers dataset


## Architecture 3-classes 2-classes

VGG-SegNet 0.68 0.90 UNet 0.62 0.90 Bonnet 0.80 0.90 FCN8 0.31 0.45 VGG-UNet 0.64 0.91

network are updated in a way that cross entropy loss is reduced. Mini-batches composed by one image were used for training. It is worth noticing that, the dataset used for the training procedure does not present all the challenges in- troduced when dealing with a real-world eld, because it does not contain data captured with dierent eld conditions and at dierent stages of plant level. For this reason, in order to properly evaluate our approach, we used for testing 1000 images coming from the SugarBeets dataset [2] and other 60 images from the Carrots dataset. It is important to note that Carrots and SugarBeets datasets were not included in ne tuning VGG-16 encoder and were used only to evaluate the capability of VGG-UNet to generalize. Table 1 shows the results obtained by using dierent network architectures on the Sunowers dataset. When consider- ing only two classes, namely soil/plants, the VGG-UNet approach outperforms the other tested approaches. Fig. 7 shows qualitative results.

4.4 Multi-Channel Architecture Evaluation

To improve the segmentation performance of the VGG-UNet architecture, we increase the number of input channels by a set of vegetation indices: Excess Green (ExG), Excess Red (ExR), Color Index of Vegetation Extraction (CIVE), and Normalized Dierence Index (NDI). In addition, we use the HSV (hue, saturation, value) representation of the input image, concatenating all those

Fig. 6: Samples from the dataset used for training and testing. The rst row contains the RGB images in input, while the second row shows the ground truth masks. In the rst, second, and third columns sunowers images taken under dierent lighting condition and dierent age of growth are shown. The fourth column refers to the organic Carrots dataset and the fth column refers to the SugarBeets dataset.

50 M. Fawakherji et al.

Fig. 7: Qualitative results achieved by dierent CNN structures. First column RGB images, second column ground truth mask, third, forth, fth, and sixth prediction from Bonnet, VGG-UNet,VGG-Segnet, and UNet.

representations along with the input RGB image to form a multi-channel input volume.

For training our deep CNN, we have used a dataset consisting of the 80% of the images in the SugarBeets dataset. For testing, we used a dataset consisting of the remaining 20% of images from the SugarBeets dataset, plus all the images in the Sunowers, Carrots, and Stuttgart datasets. Results for the 2 classes segmentation problem are reported in Table 2 (RGB input) and Table 3 (multi- channel input), while results for the 3 classes segmentation problem are reported in Table 4 (RGB input) and Table 5, respectively. Some qualitative results are reported in Fig. 8. It is noteworthy to underline that, this simple enrichment of the input has produced a substantial improvement in the results in almost all tests. Those indicators proved their ability to naturally segment vegetation and they do not present high sensitivity to soil types or weather condition, as reported in [16]


> **Table 2: Quantitative results obtained by VGG-UNet architecture for 2 classes**

> segmentation on dierent datasets with RGB input.

Dataset mIOU soil recall plant recall soil pre plant pre SugarBeets 0,93 0.99 0.96 0.99 0.90 Stuttgart 0,66 0.98 0.59 0.99 0.37 Carrots 0,64 0.96 0.43 0.94 0.55 Sunowers 0,63 0.95 0.39 0.96 0.53

Crop and Weed Classication . . . 51


> **Table 3: Quantitative results obtained by VGG-UNet architecture for 2 classes**

> segmentation on dierent datasets with multi-channel input.

Dataset mIOU soil recall plant recall plant pre plant pre SugarBeets 0,92 0.99 0.98 0.99 0.86 Stuttgart 0,85 0.99 0.89 0.99 0.77 Carrots 0,67 0.94 0.75 0.99 0.60 Sunowers 0,70 0.99 0.78 0.94 0.67


> **Table 4: Quantitative results obtained by VGG-UNet architecture for 3 classes**

> segmentation on dierent datasets with RGB input.

Dataset mIOU soil crop weed soil crop weed recall recall recall pre pre pre SugarBeets 0,71 0.99 0.94 0.80 0.95 0.90 0.68 Stuttgart 0,45 0.98 0.66 0.68 0.97 0.36 0.34 Carrots 0,35 0.923 0.36 0.29 0.94 0.43 0.32 Sunowers 0,39 0.92 0.33 0.37 0.96 0.32 0.29


> **Table 5: Quantitative results obtained by VGG-UNet architecture for 3 classes**

> segmentation on dierent datasets with multi-channel input .

Dataset mIOU soil crop weed soil crop weed recall recall recall pre pre pre SugarBeets 0,75 0.998 0.94 0.80 0.99 0.92 0.70 Stuttgart 0,60 0.984 0.75 0.71 0.90 0.63 0.59 Carrots 0,40 0.93 0.43 0.38 0.98 0.32 0.37 Sunowers 0.41 0.95 0.39 0.37 0.97 0.49 0.40

4.5 Pixel-wise Segmentation Evaluation

The third experiment aims to evaluate the performance of the two pipelines, the rst one depending on blobs classication after background removal, the second one being based on patch segmentation after background removal.

The evaluation of the two approaches based on object-wise classication ac- curacy are given in the form of two confusion matrices. The confusion matrix for the rst approach is shown in Fig. 9, while the confusion matrix for the second approach is shown in Fig. 10.

For the rst approach (i.e., background removal plus classication), the re- sult for correctly detected crops was 87%, while the 13% of crop was detected as weed and 22% of weed was detected as crop. This is mainly due to the overlap- ping problem between weed and crop. The 32% of soil detected as weed is due to inaccuracies in the binary masks coming from the segmentation process. The di- lation operation carried out to increase the boundaries of the foreground regions during the blob detection process increases the number of soil pixels included in weeds blobs.

In the second approach (i.e., background removal plus segmentation), we overcome the problem of overlapping between weeds and crop inside the blob, as can be noted looking at the confusion matrix in Fig. 10. Just 2% of crop

52 M. Fawakherji et al.

Fig. 8: Qualitative results obtained by VGG-UNet and multi-channel VGG- UNet.

Fig. 9: Confusion matrix obtained by evaluating the rst full pipeline (i.e., back- ground removal plus classication).

was detected as weed and 3% of weed was detected as crop. This is due to the fact that, in the rst approach, we classify the whole blob into one of two class types (i.e., crop or weed), while in the second approach each pixel in the blob is classied into one of the two class types (i.e., crop or weed). Qualitative results are shown in Fig. 11.

4.6 Weeds Distribution Evaluation

In the last experiment, we have used the two datasets UAV1 and UAV2 (see Sec. 4.1 and Fig. 12). For the rst dataset, we took 100 images and we applied

Crop and Weed Classication . . . 53

Fig. 10: Confusion matrix obtained by evaluating the second full pipeline (i.e., background removal plus segmentation).

Fig. 11: Qualitative results achieved using segmentation plus classication. White boxes denote true positive samples (weed), green boxes true negative samples (crop), blue boxes false positive samples, and red false negative samples.

to them a data augmentation process. In particular, we exploited rotations and horizontal and vertical ipping to create an augmented training dataset com- posed by 420 images. The remaining 55 images from the original dataset were used for testing purposes. The second dataset (UAV2) was used for testing only. We evaluated the generalization capability of the net for classifying the pixels in two classes, namely soil and plant.

Network Training. We trained the proposed VGG-UNet by initializing the encoder (VGG-16) with the weights taken from training the VGG-16 on the ImageNet dataset, then we trained the whole network using Stochastic Gradient Descent (SGD) with a xed learning rate of 1 · e−4 and a momentum of 0.90. The parameters of the network are updated in a way that cross entropy loss is reduced. Mini-batches composed by one image was used for training.

Qualitative results of using dierent input types for pixel-wise segmentation into soil, weed, and crop on sugar beet dataset are shown in the rst row of Fig. 13. The segmentation performance of VGG-UNet decreased when we used Red

54 M. Fawakherji et al.

Fig. 12: Image samples from the datasets UAV1 and UAV2. (a), (b), (c), and (d) represent NIR, NDVI, RED, and ground truth from sugar beet dataset. (e), (f), (g), and (h) represent NIR, RGB, RED, and ground truth from corn dataset.

Fig. 13: Qualitative results achieved by CNN with dierent input type. First and second rows represent the output for 3 classes segmentation on sugar beet dataset, the third row 2 classes segmentation output on corn dataset.

channel alone as input. The best results was achieved using the three channels together as input, while for pixel-wise segmentation into soil, and plant sugar beet dataset the best result for NDVI channel. Table 6 shows the quantitative results obtained by the used VGG-UNet architecture. We have performed also a quantitative comparison between the used VGG-UNet architecture and the SegNet network. Table 7 contains the results for the comparison. VGG-UNet performs slightly better on the sugar beet dataset.

The nal output of our approach is shown in Fig. 14, where the rst row shows the segmentation output, the second and third rows show the crop and weed distribution. The number in each cell describes the crop distribution (in the second row) and the weed distribution (in the third row). The green circles show the high density of crop, while the red ones show the high density of weed. The performance of VGG-UNet architecture has been tested on an embedded GPU board, namely Jetson TX2, and the processing time per image was 0.6

Crop and Weed Classication . . . 55


> **Table 6: Quantitative results illustrating mean accuracy obtained by VGG-UNet**

> using dierent input on the sugar beets and corn datasets.

3-classes 2-classes Input sugar beet sugar beet corn Red 0.84 0.91 0.73 NIR 0.90 0.96 0.85 NDVI 0.93 0.99 0.92 RED+NIR+NDVI 0.95 0.98 0.88


> **Table 7: Quantitative results illustrating mean accuracy obtained by SegNet and**

> VGG-UNet architecture on the sugar beet dataset.


## Architecture

3-classes
2-classes
RED+NIR+NDVI input NDVI input
SegNet
0.93
0.98
VGG-UNet
0.95
0.99

Fig. 14: Results from computing weed and crop distribution with dierent input types. The rst column represent the ground truth. The second and third columns shows the prediction output from VGG-UNet when using NIR+NDVI+RED and NDVI as input. The second and third rows represents crop and weed distribution.

seconds when we use three channels together as input, and around 0.2 seconds when we used each channel alone as input.

56 M. Fawakherji et al.

5 Conclusions In this paper, we have described two novel pipelines that combine a robust pixel-wise segmentation CNN, designed to be trained once to generalize the veg- etation/soil segmentation problem, with a specialized crop/weeds classication network, designed to be trained for each type of cultivation with a specic, re- duced size dataset. Our goal is to reduce the limitations of CNNs in generalizing when a limited amount of data with pixel-wise annotations is available.

Starting from the consideration that pixel-wise labeling is the bottleneck for most crop/weeds classication methods, we adopt an approach based on a robust binary segmentation to be agnostic with respect to plant species. Our network is trainable also by using external, ready to use pixel-wise labeled datasets that possibly do not includes the target crop. Specically, we use a deep convolu- tional encoder-decoder architecture for robust background (soil) removal and the extraction of regions of interest (ROIs).

A coarse-to-ne classier based on CNN is used to classify the extracted ROIs into crop and weeds. We describe two dierent methods for obtaining the classication between crop and weeds, i.e., by feeding a classication or a segmentation CNN with image patches (i.e., bounding boxes) enclosing plant instances extracted by using the obtained vegetation/soil segmentation mask. Both the presented architectures have the advantage of requiring smaller datasets comparing to conventional 3-classes soil/crop/weeds classication systems. They just require a small dataset to specialize on the target crop species.

We extensively tested the introduced approaches by using four dierent datasets, showing good classication results and generalization properties.

As future directions, we aim to insert between the segmentation and clas- sication steps an automatic alignment process to improve the classication accuracy of our pipeline.


## References


## 1. Badrinarayanan,

V.,
Kendall,
A.,
Cipolla,
R.:
Segnet:
A
deep
convolu-
tional encoder-decoder architecture for image segmentation. arXiv preprint
arXiv:1511.00561 (2015)
2. Chebrolu, N., Lottes, P., Schaefer, A., Winterhalter, W., Burgard, W., Stachniss,
C.: Agricultural robot dataset for plant classication, localization and mapping on
sugar beet elds. The International Journal of Robotics Research (2017)
3. De Rainville, F.M., Durand, A., Fortin, F.A., Tanguy, K., Maldague, X., Panneton,
B., Simard, M.J.: Bayesian classication and unsupervised learning for isolating
weeds in row crops. Pattern Analysis and Applications 17(2), 401414 (2014)
4. Di Cicco, M., Potena, C., Grisetti, G., Pretto, A.: Automatic model based dataset
generation for fast and accurate crop and weeds detection. In: IROS. pp. 51885195
(2017)
5. Duckett, T., Pearson, S., Blackmore, S., Grieve, B., Wilson, P., Gill, H., Hunter, A.,
Georgilas, I.: Agricultural Robotics: The Future of Robotic Agriculture. UK-RAS
White Papers, UK-RAS Network (2018)
6. Fawakherji, M., Youssef, A., Bloisi, D.D., Pretto, A., Nardi, D.: Crop and weeds
classication for precision agriculture using context-independent pixel-wise seg-
mentation. In: Proc. of the IEEE International Conference on Robotic Computing
(IRC) (2019). https://doi.org/10.1109/IRC.2019.00029

Crop and Weed Classication . . . 57

7. Haug, S., Michaels, A., Biber, P., Ostermann, J.: Plant classication system for crop/weed discrimination without segmentation. In: WACV. pp. 11421149. IEEE (2014) 8. Haug, S., Ostermann, J.: A crop/weed eld image dataset for the evaluation of computer vision based precision agriculture tasks. In: Computer Vision - ECCV 2014 Workshops. pp. 105116 (2015) 9. Lee, S.H., Chan, C.S., Wilkin, P., Remagnino, P.: Deep-plant: Plant identication with convolutional neural networks. In: ICIP. pp. 452456. IEEE (2015) 10. Long, J., Shelhamer, E., Darrell, T.: Fully convolutional networks for semantic segmentation. In: CVPR. pp. 34313440 (2015) 11. Lottes, P., Behley, J., Chebrolu, N., Milioto, A., Stachniss, C.: Joint stem detection and crop-weed classication for plant-specic treatment in precision farming. arXiv preprint arXiv:1806.03413 (2018) 12. Lottes, P., Behley, J., Milioto, A., Stachniss, C.: Fully convolutional networks with sequential information for robust crop and weed detection in precision farming. IEEE Robotics and Automation Letters (RA-L) 3, 30973104 (2018) 13. Lottes, P., Hoeferlin, M., Sander, S., Müter, M., Schulze, P., Stachniss, C.: An eective classication system for separating sugar beets and weeds for precision farming applications. In: ICRA. pp. 51575163 (2016) 14. Lottes, P., Khanna, R., Pfeifer, J., Siegwart, R., Stachniss, C.: Uav-based crop and weed classication for smart farming. In: ICRA. pp. 30243031 (2017) 15. McCool, C., Perez, T., Upcroft, B.: Mixtures of lightweight deep convolutional neural networks: Applied to agricultural robotics. IEEE Robotics and Automation Letters 2(3), 13441351 (2017) 16. Milioto, A., Lottes, P., Stachniss, C.: Real-time semantic segmentation of crop and weed for precision agriculture robots leveraging background knowledge in cnns. In: ICRA. pp. 22292235 (2018) 17. Milioto, A., Stachniss, C.: Bonnet: An open-source training and deployment framework for semantic segmentation in robotics using cnns. arXiv preprint arXiv:1802.08960 (2018) 18. Potena, C., Nardi, D., Pretto, A.: Fast and accurate crop and weed identication with summarized train sets for precision agriculture. In: International Conference on Intelligent Autonomous Systems. pp. 105121 (2016) 19. Ronneberger, O., Fischer, P., Brox, T.: U-net: Convolutional networks for biomedi- cal image segmentation. In: International Conference on Medical image computing and computer-assisted intervention. pp. 234241 (2015) 20. Rouse, Jr., J.W., Haas, R.H., Schell, J.A., Deering, D.W.: Monitoring vegetation systems in the great plains with ERTS. In: Proc. of the 3rd Earth Resource Tech- nology Satellite (ERTS) Symposium. vol. 1 (1974) 21. Sa, I., Chen, Z., Popovi¢, M., Khanna, R., Liebisch, F., Nieto, J., Siegwart, R.: weednet: Dense semantic weed classication using multispectral images and mav for smart farming. IEEE Robotics and Automation Letters 3(1), 588595 (2018) 22. Shelhamer, E., Long, J., Darrell, T.: Fully convolutional networks for semantic segmentation. IEEE Trans. Pattern Anal. Mach. Intell. 39(4), 640651 (2017) 23. Simonyan, K., Zisserman, A.: Very deep convolutional networks for large-scale image recognition. arXiv preprint arXiv:1409.1556 (2014) 24. Strothmann, W., Ruckelshausen, A., Hertzberg, J., Scholz, C., Langsenkamp, F.: Plant classication with in-eld-labeling for crop/weed discrimination using spec- tral features and 3d surface features from a multi-wavelength laser line prole system. Computers and Electronics in Agriculture 134, 7993 (2017)
