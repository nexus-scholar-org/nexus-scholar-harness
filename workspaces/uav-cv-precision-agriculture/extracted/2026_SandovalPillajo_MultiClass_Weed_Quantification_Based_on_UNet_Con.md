---
workspace_id: SCI-001017
doi: 10.3390/app16073149
title: Multi-Class Weed Quantification Based on U-Net Convolutional Neural Networks
  Using UAV Imagery
authors:
- family_name: Sandoval-Pillajo
  given_name: "Luc\xEDa"
  orcid: null
- family_name: "Pusd\xE1-Chulde"
  given_name: Marco
  orcid: null
- family_name: Pazos-Morillo
  given_name: Jorge
  orcid: null
- family_name: "Granda-Gudi\xF1o"
  given_name: Pedro D.
  orcid: null
- family_name: "Garc\xEDa-Santill\xE1n"
  given_name: "Iv\xE1n D."
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:35:02.481707+00:00'
---

# Multi-Class Weed Quantification Based on U-Net Convolutional Neural Networks Using UAV Imagery

Article Multi-Class Weed Quantiﬁcation Based on U-Net Convolutional Neural Networks Using UAV Imagery

Lucía Sandoval-Pillajo 1,2 , Marco Pusdá-Chulde 2 , Jorge Pazos-Morillo 2 , Pedro Granda-Gudiño 2 and Iván García-Santillán 2,*

1 Departamento de Sistemas Informáticos y Computación, Universitat Politècnica de València, 46022 Valencia, Spain; ansanpil@doctor.upv.es 2 Universidad Técnica del Norte, Ibarra 100150, Ecuador; mrpusda@utn.edu.ec (M.P.-C.); jrpazosm@utn.edu.ec (J.P.-M.); pdgranda@utn.edu.ec (P.G.-G.) * Correspondence: idgarcia@utn.edu.ec


## Abstract

Weed identiﬁcation and quantiﬁcation are processes that are usually manual, subjective, and error-prone. Weeds compete with crops for nutrients, minerals, physical space, sunlight, and water. Thus, weed identiﬁcation is a crucial component of precision agriculture for autonomous removal and site-speciﬁc treatments, efﬁcient weed control, and sustainability. Convolutional Neural Networks (CNNs) are very common in weed identiﬁcation. This work implemented CNN models for semantic segmentation based on the U-Net architecture for automatically segmenting and quantifying weeds in potato crops using RGB images acquired by a drone at 9–10 m height, ﬂying at 1 m/s. Remote sensing images are affected by factors that degrade image quality and the model’s accuracy. Five U-Net variants were evaluated: the original U-Net, Residual U-Net, Double U-Net, Modiﬁed U-Net, and AU-Net. The models were trained using the TensorFlow/Keras frameworks on Google Colab Pro+, following the Knowledge Discovery in Databases (KDD) methodology for image analysis. Each model was trained using a diverse custom dataset in uncontrolled environments, considering six classes: background, Broadleaf dock (Rumex obtusifolius), Dandelion (Taraxacum ofﬁcinale), Kikuyu grass (Cenchrus clandestinum), other weed species, and the crop potato (Solanum tuberosum L.). The models’ segmentation was widely assessed using Mean Dice Coefﬁcient, Mean IoU, and Dice Loss metrics. The results showed that the Residual U-Net model performed the best in multi-class segmentation, achieving a Mean IoU of 0.8021, a performance comparable to or superior to that reported by other authors. Additionally, a Student’s t-test was applied to complement the data analysis, suggesting that the model is reliable for weed quantiﬁcation.

Keywords: weed classiﬁcation; deep learning for agriculture; aerial imagery analysis; semantic segmentation; precision agriculture; crop–weed discrimination

Academic Editor: Nektarios Valous

Received: 12 December 2025

Revised: 25 February 2026


## 1. Introduction

Accepted: 27 February 2026

1.1. Problem Statement

Published: 25 March 2026

According to the Food and Agriculture Organization of the United Nations (FAO), unwanted plants, also known as weeds, represent one of the greatest challenges to agricul- tural production worldwide because they cause economic and social damage to farmers. The damage caused can range from 5% to 10% of production in developed countries and up to 30% in developing countries [1].

Copyright: © 2026 by the authors.

Licensee MDPI, Basel, Switzerland.

This article is an open access article

distributed under the terms and

conditions of the Creative Commons

Attribution (CC BY) license.

Appl. Sci. 2026, 16, 3149 https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 2 of 27

Weed identiﬁcation is a crucial component of precision agriculture for autonomous removal, site-speciﬁc treatments, and efﬁcient weed control. Accurate segmentation and mapping of weed spatial distribution are critical for successful farming, efﬁcient agricultural resource management, and contributing to agricultural sustainability. The presence of weeds signiﬁcantly threatens crop yield and harvest quality [2], as weeds compete for soil resources such as nutrients and water, affecting the normal growth and development of desired plants [3,4]. This problem in crops ranges from low production to economic losses and environmental deterioration of the land.

It is estimated that manual weed identiﬁcation can lead to signiﬁcant errors in quan- tiﬁcation, resulting in ineffective and untimely decisions in weed control and herbicide use. Visual inspection can be subjective and subject to human error, resulting in inaccurate quan- tiﬁcation of weed infestation [5]. Furthermore, this approach can be laborious, inefﬁcient, and error-prone. It consumes a great deal of time and labor and incurs additional costs for farmers since it requires a thorough inspection of the ﬁelds by these agricultural experts.

Precision agriculture (PA) uses technological tools to improve methods of combating weeds [6]. One approach used for weed identiﬁcation is deep learning [7], which has emerged as a promising candidate, as its algorithms allow the automatic extraction of features from large amounts of data [8]. Before the adoption of deep learning, early approaches to weed detection relied on classical image processing techniques, such as edge detection, color thresholding, texture analysis, and vegetation indices (e.g., NDVI), to distinguish crops from weeds. These methods represented a ﬁrst step toward automated weed identiﬁcation and provided valuable insights into spectral and spatial characteristics of vegetation, paving the way for the development of learning-based approaches such as Convolutional Neural Networks (CNNs).

CNNs have become increasingly popular in recent years across various application contexts [9–15], thanks to current hardware that enables the efﬁcient implementation of these algorithms [8,16]. CNNs have proven to offer good results concerning semantic segmentation and weed identiﬁcation [4,17–20]. Semantic segmentation aims to categorize each pixel in an image into a speciﬁc class (e.g., crop, weeds, soil), producing a segmenta- tion map of the plant within the input image [21]. The identiﬁcation task is challenging since the plants (crops and weeds) share similar physical characteristics, the plants overlap, and certain outdoor environmental conditions inﬂuence them [22]. Detecting multiple speciﬁc weed types instead of a single generic class is crucial for precision agricultural man- agement. Different weeds require differentiated control strategies and efﬁcient treatments, avoiding excessive herbicide application and collateral damage to soil biodiversity and human health.

The aim is to adopt the U-net CNN [23] for multi-class semantic segmentation to iden- tify and quantify four categories of weeds: Broadleaf dock (Rumex obtusifolius), Dandelion (Taraxacum ofﬁcinale), Kikuyu grass (Cenchrus clandestinum), and other unidentiﬁed plant classes in potato crop ﬁelds (Solanum tuberosum L.). Potato cultivation was selected because it is an icon in the northern area of Ecuador, where this research is carried out. Additionally, there are very few studies on this crop’s weed recognition, i.e., it is under-researched [24]. The categories of weeds treated are the most prevalent ones observed in the region. Five versions of the U-Net algorithm are tested, with modiﬁcations to the architecture, trying to make it more specialized and robust for weed image segmentation. The model variations were Original U-Net, Residual U-Net, Double U-Net, Modiﬁed U-Net, and AU-Net with attention module and residual blocks (a custom proposal), which have been widely used in medicine and are detailed below. The U-Net algorithm was selected for experimentation because it is one of the most preferred architectures for weed segmentation tasks, mostly on drone-acquired images, with high accuracy [25]. Likewise, it is important to note that

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 3 of 27

the U-Net model and the results presented in existing studies cannot be broadly applied to other sites with similar results [26]; therefore, it is necessary to evaluate it in our region and context.

This adoption and experimentation of network variants to the quantiﬁcation task of weed types (multi-class problem) in uncontrolled environments (lighting, weather, camera movements, plant morphology, etc.) using a custom annotated dataset represents an important contribution to the ﬁeld of study in our agricultural region for precise weed control in changing ﬁeld conditions. Potato ridges introduce strong three-dimensional structure, severe leaf overlap, variable soil exposure, and frequent occlusions, all of which create heterogeneous backgrounds and complex weed–crop boundaries. Such visual complexity, structural variability, and occlusion signiﬁcantly reduce class separability [27]. Uncontrolled environments pose major challenges for deep learning, as models must be robust, adaptable, and able to generalize to unpredictable conditions without manual tuning, unlike in more controlled environments, such as medicine, where images generally come from standardized equipment.

UAV-based imagery for weed detection is affected by multiple sources of variability that degrade image quality and segmentation accuracy, including illumination changes, atmospheric effects, camera motion, and crop structure [28]. In addition, the lack of repre- sentative public datasets for certain crops, such as potato [29], and the limited availability of annotated data for native weed species restrict model generalization and reproducibil- ity [30]. Furthermore, structured methodological frameworks are required to manage the entire data analysis process, from acquisition to validation, ensuring consistency and reliability in real agricultural scenarios [31]. These challenges highlight the need for robust segmentation approaches capable of handling real ﬁeld variability rather than controlled experimental settings.

To support reproducibility and future research, this study releases a publicly available UAV-based dataset for multi-class weed segmentation in potato crops, including annotated masks for native weed species. The dataset is accessible through a public GitHub repository, enabling comparative evaluation and reuse by the research community. This contribution addresses the current lack of open datasets for potato crops and underrepresented weed species in UAV-based precision agriculture studies.

The remaining structure of the manuscript is as follows. Section 1.2 presents engineer- ing contributions and technical highlights. Section 1.3 analyses related work and literature gaps. Section 2 indicates the methodology, dataset, and software used in developing this study for quantifying weeds. Section 3 shows the main results and statistical tests obtained in this proposal. Section 4 considers a discussion with other related studies, and ﬁnally, the conclusions and future work are presented in Section 5.

1.2. Engineering Contributions and Technical Highlights

This work presents an engineering-oriented contribution focused on the adaptation, evaluation, and validation of deep learning models for multi-class weed quantiﬁcation in potato crops using UAV imagery under uncontrolled ﬁeld conditions. Unlike studies that propose novel architectures, the contribution lies in the systematic design of the experimental pipeline, including dataset construction, model adaptation, training strategy, and validation protocol.

The technical highlights of this study are summarized as follows:

1. Construction of an extended UAV-based dataset with six semantic classes, including native weed species that are not present in existing public datasets. The number of annotated samples increases signiﬁcantly and incorporates additional ﬁelds, growth stages, and weed instances.

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 4 of 27

2. Patch-based training strategy designed to mitigate class imbalance and preserve spatial details in UAV imagery. 3. Comparative evaluation of ﬁve U-Net variants under identical conditions, enabling a fair engineering assessment of architectural trade-offs. 4. Integration of semantic segmentation metrics with statistical validation (Student’s t-test and correlation analysis) to assess the practical reliability of weed quantiﬁcation. 5. Release of a reproducible and transferable workflow for precision agriculture applications.

1.3. Related Work and Research Gaps

Below, we summarize some relevant studies classiﬁed into thematic subsections that served as a theoretical basis and for comparison purposes. For each category, we added a comparative and critical discussion highlighting methodological limitations, dataset constraints, and gaps in current approaches.

1.3.1. Ground-Based Weed Segmentation Approaches

Early studies on weed identiﬁcation and segmentation primarily relied on ground- based image acquisition systems, using handheld cameras, mobile devices, or ﬁxed plat- forms mounted close to the soil surface. These approaches provide high-resolution imagery and controlled viewpoints but suffer from limited scalability and operational efﬁciency in real agricultural scenarios.

Several works have successfully applied U-Net and encoder–decoder architectures to ground-level images for weed segmentation. For instance, Cui et al. [32], Zhang and Zhang [33], Zuo and Li [34], and Thiagarajan et al. [35] demonstrated high segmentation accuracy in maize and bean crops using CNN-based models. Liao et al. [36] and Asuka et al. [37] segmented rice weeds and seedlings, whereas Li and Yan [38] dealt with small objects in different crops and weeds. Similarly, Garibaldi et al. [21,39,40] and Ma et al. [41] evaluated both CNN and Transformer architectures for weed–crop segmentation under natural corn ﬁeld conditions. Despite their strong performance, these approaches require close-range data acquisition, which is time-consuming, labor-intensive, and impractical for large-scale monitoring.

Moreover, ground-based systems are highly sensitive to viewpoint changes, occlusions, and variations in plant morphology, which limits their generalization to heterogeneous ﬁeld conditions. These limitations have motivated the adoption of UAV platforms for weed detection, enabling rapid and large-area crop monitoring.

1.3.2. UAV-Based Weed Segmentation Using CNN and U-Net Variants

UAV imagery has become a key enabler of precision agriculture, allowing large-scale weed mapping with high spatial resolution. Several studies have applied CNN-based mod- els, particularly U-Net and its variants, to UAV-acquired images for semantic segmentation.

Gao et al. [6], Bretas et al. [42], and Amarasingam et al. [26] demonstrated the feasibility of U-Net-based models for weed detection using RGB and multispectral UAV images. Kong et al. [43] optimized a model based on the YOLOv5s architecture for weed segmentation in corn ﬁelds. More recent works, such as Machidon et al. [44] and Mei et al. [45], proposed lightweight and efﬁcient U-Net variants optimized for real-time or resource-constrained UAV applications. These models achieved promising results while reducing computational cost and energy consumption.

However, most UAV-based studies address binary segmentation problems (weed vs. background) or at most three classes (crop, weed, soil). Only a limited number of works consider multiple weed species, and even fewer address complex crop structures such as potato ridges, which introduce severe occlusions, background heterogeneity, and

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 5 of 27

overlapping vegetation. Additionally, many models are trained and evaluated on relatively small or homogeneous datasets, limiting their robustness in uncontrolled ﬁeld conditions.

1.3.3. Transformer and Hybrid Architectures for Weed Segmentation

Recently, Transformer-based and hybrid CNN–Transformer models have been ex- plored to capture global contextual relationships in complex agricultural scenes. Jiang et al. [46] introduced SWFormer, a hybrid architecture combining CNNs and Transformers for multi-class weed segmentation, while Guo et al. [47] proposed CTFFNet for rice ﬁelds using UAV imagery. In another context, Sumailan et al. [48] identiﬁed breast cancer in ultrasound images using an Attention-driven U-Net model. These models demonstrated improved feature representation and robustness to complex backgrounds.

Nevertheless, Transformer-based models typically involve high computational com- plexity, large memory requirements, and longer inference times, which hinder their practical deployment in UAV-based agricultural systems. Moreover, most Transformer-based studies rely on ground-based imagery or limited UAV datasets and do not address multi-species weed segmentation in crops with high structural variability, such as potato ﬁelds. Various approaches are widely observed using CNNs and, rarely, Transformers to segment weeds in agricultural ﬁelds [49].

1.3.4. Public Datasets and Limitations for Potato Weed Segmentation

The availability of public datasets is a critical factor for reproducibility and model comparison. Several UAV-based datasets have been published for crops such as soybean, maize, rice, wheat, lettuce, and sugar beet [48,50–61]. However, no publicly available dataset currently focuses on potato crops acquired by UAVs under real ﬁeld conditions.

Furthermore, existing datasets rarely include native weed species such as Broadleaf dock, Dandelion, and Kikuyu, which are prevalent in Andean agricultural regions. This lack of representative data signiﬁcantly limits model generalization across geographical regions, seasons, and crop types. Distributional shifts caused by differences in lighting, soil conditions, plant morphology, and growth stages further exacerbate this problem [6,42].

1.3.5. Identiﬁed Research Gaps

From the literature analysis, several gaps remain unaddressed:

• Most UAV-based weed segmentation studies focus on binary or low-class problems, neglecting multi-species weed discrimination. • There is a lack of studies targeting potato crops, which present unique structural and visual challenges due to ridge formation, leaf overlap, and high intra-class variability. • Public datasets do not include native weed species relevant to many agricultural regions, limiting model transferability across regions. • Few works combine robust semantic segmentation metrics with statistical validation methods to assess practical reliability for weed quantiﬁcation.

To address these gaps, this study evaluates multiple U-Net variants for multi-class weed quantiﬁcation in potato crops using UAV imagery acquired under uncontrolled ﬁeld conditions. Additionally, an extended dataset is publicly released, which is explicitly designed to represent native weed species and real agricultural variability. A combined evaluation strategy based on IoU metrics and statistical testing is applied to validate the model’s practical reliability.


## 2. Materials and Methods

KDD Methodology

The Knowledge Discovery in Databases (KDD) methodology [31] was used for data management and image analysis. The KDD comprises ﬁve phases, detailed below.

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 6 of 27

2.1. Data Collection

RGB images (5472 × 3648) were collected from 8 different potato crop ﬁelds in Carchi and Imbabura (Ecuador) to incorporate diverse climatic conditions, land, and plant variabil- ity. At different growth stages, these eight ﬁelds were sampled at crop ages of approximately 15–40 days. Thus, 3810 images were acquired from May 2023 to April 2024, signiﬁcantly extending the basic original dataset (unbalanced) proposed in our previous work [19] by about 56%, contributing to this study. The DJI Mavic 2 Pro UAV was used with the Android DroneDeploy application v5.7 to conﬁgure all the ﬂight parameters: ﬂight height 9–10 m, ﬂight speed 1 m/s, and cm/pixel ratio 0.25 (GSD). The distance between the camera and the ground is not strictly ﬁxed to create more image variations. The ﬂight height was selected because the best results were observed on images acquired at 10 m [62], representing a compromise between GSD and ground coverage [63]. It allows for capturing a larger area; hence, the efﬁciency of the UAV ﬂying is much higher [64]. Likewise, ﬂight speed must be substantially reduced at relatively low ﬂight altitudes to avoid motion blur [63]. Figure 1 shows the study area in northern Ecuador, showing the location of the provinces of Carchi and Imbabura. The eight plots of land are in the cantons of San Gabriel (2), Bolívar (2), El Ángel (2), Ibarra (1), and Cotacachi (1).

(a)

(b)  (c)


> **Figure 1. (a) Geographic location of the potato ﬁelds used for UAV data acquisition in Carchi and**

> Imbabura provinces, Ecuador. In (b) and (c) are shown examples of RGB images (5472 × 3648) taken
at 9–10 m height by the DJI Mavic 2 Pro UAV in potato ﬁelds in Carchi and Imbabura, respectively.

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 7 of 27

2.2. Data Selection, Preprocessing, and Transformation

This step consisted of the initial review and ﬁltering of the captured images, in which the sharpness of the objects of interest (crops and weeds) was considered. Images not suitable for the research were discarded according to the following criteria: (i) images that do not contain weeds, (ii) images with an exaggerated density of weeds, (iii) adjacent images, and (iv) blurred images. In our workﬂow, only frames exhibiting severe motion blur—typically caused by abrupt UAV acceleration or sudden wind gusts—were removed. Blurriness was assessed using a simple quantitative threshold based on the variance of the Laplacian operator, a widely used focus metric in computer vision [65]. Images with vari- ance values below 30 were excluded because they lacked sufﬁcient spatial detail for reliable annotation. The threshold was determined empirically based on the characteristics of our UAV imagery. Mild or moderate blur was intentionally retained to avoid overestimating model robustness, ensuring that the training set still reﬂected realistic in-ﬁeld conditions. Thus, this phase ensured that the dataset contained high-quality images, thereby facilitating accurate weed detection.

Subsequently, following the suggestion made in our previous work [19], the classes of the original dataset were balanced, with nearly the same amount of data per class, incorporating new images from other croplands not previously considered. The classes initially least represented were the Dandelion, Broadleaf dock, and other weed species, while the most represented were the Kikuyu and potato.

The images were then processed and transformed to prepare them properly for the U-Net architecture. Based on the idea of [66], 250 × 250 sub-image extraction from the images is used for manual image annotation. This choice was made because this resolution almost completely covers most large plants in the original images. Additionally, better results are achieved when the image is divided into patches instead of resizing the entire image [39]. Adobe Photoshop 2020 was used to delimit and extract the sub-images, as indicated in Figure 2.

(a)  (b)


> **Figure 2. Two examples of delimiting and extracting a 250 × 250 sub-image (62.5 cm × 62.5 cm on**

> the ground) at different ﬂight heights, showing crop in (a) and weeds in (b).

Each was categorized during the extraction of the 250 × 250 sub-images, considering the most signiﬁcant type of plant present in each sub-image, which may contain various plants. Weeds with the greatest coverage in the eight crop ﬁelds visited were chosen, mainly Broadleaf dock, Dandelion, and Kikuyu. In addition, a category called “other weeds” was used for plants that were difﬁcult to identify visually (unknown or small plants) and those with a low presence in the ﬁelds visited. This category also represents a heterogeneous class of weed species that are rare, unidentiﬁed, or visually ambiguous, such as wounded heart (Polygonum nepalense), turnip (Brassica rapa), radish (Raphanus raphanistrum), and nettle (Urtica urens). These species were not sufﬁciently represented across the dataset to deﬁne separate classes. This generic class is because there will always be plants that have not been considered in the training dataset in crop ﬁelds.

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 8 of 27

A total of 2100 correctly classiﬁed 250 × 250 sub-images were obtained. Each extracted sub-image was then resized to a resolution of 128 × 128 for image annotation for semantic segmentation and to be compatible with the input of the U-net CNN architecture detailed below. Semantic image segmentation is the labeling of each pixel in an image with its corresponding class. Thus, we selected an input resolution of 128 × 128 as a compromise between preserving sufﬁcient spatial context and ensuring efﬁcient and stable training. The UAV images captured (GSD of 0.25 cm/pixel) provide the level of detail necessary to represent small weeds. Each image was initially divided into 250 × 250-pixel patches, corresponding to 62.5 cm × 62.5 cm on the ground; these patches were subsequently resized to 128 × 128 pixels to ensure compatibility with the U-Net without altering the physical area represented. This downscaling signiﬁcantly reduces the model’s computational load, particularly relevant in scenarios with limited computational resources and moderate-sized datasets. This approach has been employed in patch-based training to control memory consumption and improve efﬁciency in some encoder–decoder architectures [39]. In the agricultural domain, it has also been shown that weed segmentation using convolutional networks remains feasible with reduced resolutions and patch-based strategies without compromising the model’s discriminative capability [27]. Additionally, the U-Net’s effective receptive ﬁeld remains sufﬁciently large to integrate meaningful visual context around each segmented pixel, enabling discrimination of small weeds within their local surroundings.

The online platform used for image annotation was Roboﬂow [67], which offers func- tionality to determine the number of individuals (plants) in the entire dataset. The classes were labelled: 0—background, 1—Broadleaf dock, 2—Dandelion, 3—Kikuyu, 4—other weeds, and 5—Potato. The extended dataset has a greater variety of weeds (size, light- ing, region, etc.) and a more balanced distribution of classes than the original dataset (unbalanced), as indicated in Table 1.


> **Table 1.**

> The number of plants in the extended dataset is more balanced than the original
dataset (unbalanced).

Type of Plant Number of Plants %

Broadleaf dock 1334 16.44% Dandelion 1448 17.84% Kikuyu 1838 22.63% Other weeds 1661 20.46% Potato (crop) 1838 22.63%

TOTAL 8119 100%

In short, a total of 3810 raw UAV images were acquired during multiple ﬂights over the eight potato ﬁelds at different crop development stages. These images were preprocessed and divided into overlapping patches to facilitate training and improve class balance, resulting in 2100 subimages used for model training and evaluation. The selected subimages include samples from all locations and growth stages to preserve spatial and temporal variability. In total, 8119 individual plant instances were annotated across all segmentation masks, which explains why the number of plants does not correspond directly to the number of images or subimages.

Manual annotation on the 2100 128 × 128 sub-images (containing 8119 plants) required 210 work hours and took approximately 6 min for each sub-image. The annotated dataset was split into training, validation, and testing sets in the ratio of 80% (1680 sub-images), 10% (210 sub-images), and 10% (210 sub-images), respectively, using a stratiﬁed sampling strategy to preserve the distribution of weed classes, locations, and crop development stages. The split was applied at the subimage level, and each subset contains samples from all

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 9 of 27

eight ﬁelds, ensuring representative spatial and temporal coverage and preventing dataset bias. The dataset split was performed with grouping at the raw image level to avoid spatial data leakage. All patches generated from the same original UAV frame and spatial region were assigned to a single dataset partition. This ensured that overlapping or neighboring patches did not appear in different splits, thereby preserving spatial independence between the training, validation, and test data.

The 80/10/10 split is a good balance in general, where one wants to maximize data usage for model training without sacriﬁcing adequate validation (hyperparameter tuning) or testing of the model’s generalization ability on unseen data.

We computed the pixel distribution across the training set. As expected in UAV imagery, the background class is dominant (83.35% of all pixels); however, the crop and weed classes collectively account for 16.65% of the dataset, with individual proportions of 3.47% (Broadleaf dock), 4.39% (Dandelion), 2.95% (Kikuyu), 1.24% (other weed species), and 4.60% (Potato). This pixel distribution is consistent with previous UAV-based weed segmentation studies, in which the background typically accounts for 70–90% of pixels due to soil exposure and crop structure [27]. Furthermore, using 128 × 128 patches increases the relative proportion of foreground pixels per batch, thereby mitigating the imbalance present in the full-resolution images.

Additionally, data augmentation was performed to increase the dataset size and improve model training. The operations applied to the sub-images were a 25% increase and decrease in brightness, a Gaussian blur with a 5 × 5 kernel, and rotations at angles of 90, 180, and 270◦. Seven types of data augmentation were applied, obtaining 11,760 sub-images for the model training set.

In brief, the dataset was ﬁrst split into training, validation, and test sets using stratiﬁed sampling (80/10/10). Data augmentation was applied only to the training subset to increase the number of training samples and improve model robustness. The validation and testing sets were kept unchanged to ensure an unbiased evaluation of model performance. This procedure follows standard practice in deep learning experiments to prevent information leakage between training and evaluation sets.

2.3. Data Mining

This phase consists of two main parts: the choice of the deep learning algorithm and its training.

2.3.1. The Deep Learning Algorithm (U-Net)

The well-known U-Net architecture was selected as justiﬁed above for its effective- ness in semantic segmentation, which is widely used in medical images [23] and, more recently, in weed segmentation tasks [25]. The U-Net offers a favorable trade-off between segmentation accuracy, training stability with limited datasets, computational efﬁciency, and suitability for deployment in precision agriculture workﬂows. The U-Net is known for its ability to capture both low-level features (edges, textures, simple patterns, colors, and gradients) and high-level features (complex patterns, semantic contexts, and spatial relationships between different regions of the image) [68–70]. Its architecture is an encoder– decoder-based approach, which is characterized by having a “U” shape composed of two main parts: the encoder (contraction) and the decoder (expansion). The encoder extracts features through convolutions and pooling operations, progressively reducing the image’s resolution. Low-level features are extracted in the ﬁrst layers of the encoder, while high- level features are captured in the deeper layers. On the other hand, the decoder restores the dimensionality to its original size by fusing low- and high-resolution features through transposed convolution (deconvolution), upsampling (interpolation), and concatenation.

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 10 of 27

The encoder performs feature extraction from the image, while the decoder is responsible for reconstruction and semantic segmentation for the six classes mentioned. To achieve this, a two-dimensional convolution layer (Conv2D) was added at the end of the architecture with many ﬁlters equal to the number of classes of the problem (six in this case) and a ﬁlter size of 3 × 3. Choosing this setting allows the model to generate pixel-wise probability maps for each class. The 3 × 3 ﬁlter size in this layer, as opposed to the more common 1 × 1, allows the model to consider a slightly broader context in the ﬁnal features, which can improve the ability to capture more complex patterns in the data. Using a 2D convolution layer instead of a dense layer is crucial to maintain the spatial structure of the image and generate outputs with the same dimensions as the input. The activation function used is Softmax, which is suitable for multi-category semantic segmentation tasks.

In addition to the standard implementation of U-Net [23], some variations were adapted to improve the accuracy and efﬁciency of weed segmentation in potato crops, inspired by recent approaches in computer vision. The implemented variations include the Residual U-Net [71], Double U-Net [72], MU-Net [33], and AU-Net. The last variant is custom here and detailed below, along with the rest. Adapting these U-Net variants to the weed detection task in uncontrolled environments using our custom dataset constitutes a contribution to this study.

2.3.2. Training the U-Net Model

The U-Net model and its variants were trained on Google Colab Pro+ using Tensor- Flow/Keras 2.8.0 and the Nvidia A100 GPU 40 GB VRAM, with 83.5 GB RAM and 201.2 GB of disk space. The trained models are summarized below.

• Original U-Net [23]: The classic U-Net model was compiled with the Adam optimizer and the sparse categorical cross_entropy loss function, suitable for multi-class segmen- tation. EarlyStopping callback is implemented to stop training when validation loss has not improved for 10 consecutive epochs, and ReduceLROnPlateau callback to reduce the learning rate when validation accuracy stagnates. Training was performed for a maximum of 100 epochs with a batch size of 32, using the validation data to evaluate the model’s performance. • Residual U-Net [71]: This variation incorporates residual blocks instead of plain con- volutional blocks, which help mitigate the gradient degradation problem in deep networks. In residual blocks, the input is directly added to the output of the intermedi- ate layers, which facilitates learning and improves prediction accuracy. The Residual U-Net model maintains the basic architecture of the U-Net but with skip connections in multiple layers. The total trained parameters were nearly 135 M, with a size of 515 MB. • Double U-Net [72]: This variation combines two U-Net architectures stacked on top of each other, using a conventional U-Net with a Residual U-Net in a hybrid setup. The output of the U-Net is used as input for the Residual U-Net, which improves the propagation of semantic information across layers and enables more accurate segmentation. The total trained parameters were just over 116 M, with a size of 443 MB. • Modiﬁed U-Net (MU-Net) [33]: This improved network introduces residual block (Resblock) and residual path (Respath) concepts into the U-Net. Resblocks are useful to overcome gradient disappearance and explosion problems, whereas Respaths improve the transformation of corresponding feature information between the contraction and expansion paths. Both are combined to increase the network depth, improving the network’s expression ability in complex image segmentation, such as that of diseased crop leaves. This architecture adapts the U-Net to work with 128 × 128 images,

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 11 of 27

maintaining the integrity of spatial information through skip connections. The total number of trained parameters was just over 14 M, and the size was 54 MB. • U-Net with attention modules and residual blocks (AU-Net): This custom varia- tion, following the idea of [26,48], combines attention modules with Residual blocks, trying to achieve a more precise and efﬁcient segmentation for detecting weeds in uncontrolled settings using UAV images. This architecture, like the original U-Net, is composed of two main parts: an encoder and a decoder, each with speciﬁc func- tions that enhance the learning capacity of the model. Attention modules (Attention Gate) allow the network to focus on the most relevant areas, such as weeds, and suppress irrelevant information, intending to improve segmentation and reduce false positives. Four Attention Gate (AG) modules are strategically placed in the decoder, in the skip connections, before merging them with the upstream layer, as shown in Appendix A. The AG1 module (16, 16, 512) works on an intermediate image rep- resentation with 16 × 16 pixels and 512 feature channels. Similarly, there are AG2 (32, 32, 256), AG3 (64, 64, 128), and AG4 (128, 128, 64). These attention modules are applied in the ﬁrst, second, third, and fourth reconstruction layers (Conv2DTranspose →AttentionGate →Concatenate →ResidualBlock). Multiple AG modules with dif- ferent spatial resolutions aim to improve segmentation by reﬁning feature selection at various image scales.

As mentioned, residual blocks mitigate vanishing gradient problems and information loss in deep neural networks by optimizing model learning by introducing skip connections. These residual blocks replace the standard convolutional layers of the U-Net and are placed in the encoder, where they are used at each convolution level before max pooling. This helps improve feature extraction while maintaining key information. They are also placed in the decoder and used in upsampling layers to reﬁne details without losing information. This improves segmentation reconstruction and avoids loss of details. The main difference with the literature mentioned is the combination of Attention Gates with other blocks (ResBlocks in this case). This model has just over 93 M trainable parameters and is 355 MB in size.


> **Table 2 summarizes the parameters and hyperparameters used during training for**

> each described model based on the U-Net. We adopted Sparse Categorical Cross-Entropy
(SCCE) because, although the background class naturally dominates in UAV-based weed
segmentation, the weed classes were not severely imbalanced relative to each other (Table 1),
and SCCE provided stable training behavior. In our experiments, SCCE showed consis-
tent convergence without bias toward the majority class, likely due to the use of small
128 × 128 patches, which effectively increased the proportion of foreground pixels seen
during training and reduced extreme class imbalance. Additionally, SCCE is computation-
ally efﬁcient and compatible with sparse label encoding, reducing memory usage during
training—an advantage for encoder–decoder architectures such as U-Net.


> **Table 2. Training parameters and hyperparameters of the ﬁve U-Net-based models.**

Hiperparameter Original U-Net Residual U-Net Double U-Net Modiﬁed U-Net AU-Net

Input size 128 × 128 × 3 128 × 128 × 3 128 × 128 × 3 128 × 128 × 3 128 × 128 × 3

Optimizer Adam (learning

Adam (learning

Adam (learning

Adam (learning

Adam (learning

rate = 0.001)

rate = 0.001)

rate = 0.001)

rate = 0.001)

rate = 0.001)

Loss function Sparse Categorical

Sparse Categorical

Sparse Categorical

Sparse Categorical

Sparse Categorical

Cross-entropy Batch size 32 16 32 32 32 Epochs 100 100 100 100 100

Cross-entropy

Cross-entropy

Cross-entropy

Cross-entropy

Callback EarlyStopping ReduceLROnPlateau

EarlyStopping ReduceLROnPlateau

EarlyStopping ReduceLROnPlateau ReduceLROnPlateau ReduceLROnPlateau

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 12 of 27

2.4. Evaluation and Interpretation

Three common metrics in semantic segmentation, dice loss, mean dice coefﬁcient, and mean intersection over union (IoU), were used to evaluate the performance of the versions of U-Net and its variants [43].

Dice loss is a function used, especially when imbalanced classes exist. It measures the match between the ground truth masks and the ones predicted by the model at the shape and overlap level. Its range is between [0, 1], with 0 indicating a perfect match between the segmentation masks [73].

Mean Dice Coefﬁcient is a metric used to evaluate the accuracy of models that segment or classify pixels into different classes. Its value range is between [0, 1], with 1 indicating a perfect match between segmentation masks [74].

Mean IoU is another widely used metric to evaluate the accuracy of semantic segmen- tation models. It provides a clear and balanced view of the model’s performance across all classes and is robust in class imbalance situations. Its value range is between (0, 1), where values close to 1 indicate that the model has excellent segmentation performance and high accuracy in class prediction.

Other metrics, such as overall accuracy (OA), have not been fully considered for evaluation and comparison because IoU is more robust than pixel accuracy in evaluating semantic segmentation, especially when unbalanced classes exist. In this case, OA could give high values even if small classes are poorly segmented [75,76].

Regarding the practical interpretation of the model, the purpose is to give meaning to the predictions made by the model, providing information that is understandable and useful for decision-making. Equation (1) is useful for calculating weed coverage [77]:

Weed coverage = Weed area

Total area × 100% (1)

The weed area is the number of pixels belonging to each category (Broadleaf dock, Dandelion, Kikuyu, other weeds) provided by the model’s semantic segmentation mask. The total area is the number of pixels in the whole image. Figure 3 shows the entire process for weed quantiﬁcation, from the image acquired by the UAV, the division into sub-images of 128 × 128 pixels, the semantic segmentation of weeds, the visualization, and the calculation of weed coverage.

As the 2802 × 1868 images are post-processed, the pixels belonging to each category of plant found are counted, and then weed coverage (Equation (1)) is applied for each type of plant.

Finally, to complement the data analysis and to contrast the weed coverages calcu- lated from the model’s predictions (U-Net) and the ground truth, the Student’s t-test and Pearson correlation coefﬁcient (r) statistical tests were used to verify whether there are statistically signiﬁcant differences and a linear association between both measurements [78,79], respectively.

The Student’s t-test is a parametric statistical test to determine whether there is a signiﬁcant difference in the weed coverage means (Equation (1)) between the ground truth and the values predicted by the best model. This allows us to complement the data analysis and to determine whether the Residual U-Net’s predictions are objectively reliable. In this case, they are considered dependent samples in the test since the manual assessments (ground truth) and those predicted by the model are carried out on the same set of images [78]. The null hypothesis H0 and alternative hypothesis H1 are established as follows:

H0: d = 0 (There is no signiﬁcant difference in the weed coverage means of both groups) H1: d̸ = 0

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 13 of 27

The decision rule is: If p-value ≤0.05, reject H0. Statistical evaluation was applied on the test set (10%) containing 210 images of 128 × 128 using the IBM SPSS v26 software. The paired t-test assumes the differences between paired observations (ground truth and model) follow a normal distribution. The sample is large enough (n ≥30) so that, according to the Central Limit Theorem, the differences approximate a normal distribution [78]. This makes the t-test valid and robust, even without explicit veriﬁcation of the normality of the differences.


> **Figure 3. The entire process for automatic weed quantiﬁcation from UAV images using the best**

> U-Net model, based on our previous work [19].

Generally, the IoU-based metric is used to validate the segmentation quality directly. It is complemented by the Student’s t-test to verify that there are no systematic biases in the full coverage. The IoU will be the key metric because it directly assesses the segmen- tation quality. However, the Student’s t-test is an essential complement to detect biases or inconsistencies in the full coverage, which could go unnoticed with the IoU. Combin- ing both evaluation criteria offers a comprehensive approach to validating the model in practical applications.


## 3. Results

3.1. U-Net Performance Metrics


> **Table 3 summarizes the values obtained in the validation stage of the ﬁve versions**

> of U-Net using the three evaluation metrics on the original dataset (unbalanced): Dice
Loss, Mean Dice Coefﬁcient, and mean IoU [80]. Only the best-performing model was also
trained on the extended (balanced) dataset, which is approximately 56% larger, as noted.

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 14 of 27


> **Table 3.**

> Evaluation metrics reached in the ﬁve versions of U-Net on the validation set
(10%, 210 images) for 100 epochs.

Model Dice Loss Mean Dice Coefﬁcient Mean IoU

Original U-Net 0.2424 0.7576 0.6542 Double U-Net 0.2470 0.7529 0.6488 MU-Net 0.2235 0.7764 0.6790 AU-Net 0.3352 0.6647 0.6150 Residual U-Net (unbalanced original dataset)

0.1765 0.8235 0.7755

Residual U-Net (balanced extended dataset)

0.1236 0.8763 0.8053

Note: Top values are in bold.

The U-Net Residual model performed best in all evaluation metrics using the original dataset (unbalanced), reaching a mean IoU = 0.7755. Thus, only this model was also trained on the extended dataset (balanced), achieving better performance with a Dice Loss of 0.1236, a mean Dice Coefﬁcient of 0.8763, and a mean IoU of 0.8053, reﬂecting a high accuracy in weed segmentation. The positive impact on the model’s performance (Residual U-Net) is evident due to balancing the classes in the dataset, with a 3.8% higher mean IoU.

AU-Net (mean IoU = 0.6150) using this traditional attention gate mechanism (AG) had the worst performance on this dataset. It is limited in identifying weed species on our custom dataset and may not be adaptable to different crops, although it is lighter than other variants. This lower performance may be due to limitations in using Attention Gates in UAV images, where weeds can be sparse and camouﬂaged, making it difﬁcult to focus attention correctly. In contrast, in medical images with more homogeneous and controlled data, attention can be focused on well-deﬁned lesions with high contrast. Additional factors include greater variability and complexity of the environment in agriculture (lighting, highly variable background, different object scales), spatial resolution, and noise in the image, dataset (imbalance in classes), and labeling (less accurate).


> **Table 4 details the IoU obtained in each class of the dataset using the best Residual**

> U-Net model on the test set (10%, 210 images), that is, on data not seen during training.


> **Table 4.**

> IoU results for each class of Residual U-Net (Balanced dataset) on the test set
(10%, 210 images).

Model Background IoU

Broadleaf Dock IoU

Dandelion IoU

Kikuyu IoU

Other Weeds IoU Potato IoU Mean IoU

Residual U-Net 0.9721 0.7984 0.7409 0.7730 0.5907 0.9376 0.8021

Overall, the Residual U-Net model performs well on the test set with a mean IoU = 0.8021, indicating that, on average, the model segments all six classes well. The performances of the model on the validation (Table 3) and test (Table 4) sets are comparable (mean IoU of 0.8053 and 0.8021, respectively), i.e., the difference in this evaluation metric is very small (≤0.4%), indicating that both datasets are representative. The model generalizes well to unseen data.

Speciﬁcally, the class with the highest IoU = 0.9721 is the background, which agrees with results obtained by other researchers [81–83] due to its signiﬁcant presence in all the images in the dataset. The second class with the highest IoU = 0.9376 is Potato, which

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 15 of 27

is in the same situation and probably due to its more distinctive and consistent visual characteristics. The class with the lowest IoU = 0.5907 is “other weeds” because this class has a limited size and encompasses the different types of weeds with heterogeneous visual characteristics (textures and patterns) that could not be visually identiﬁed as a speciﬁc category. This makes it difﬁcult for the CNN to ﬁnd and learn unique patterns of the plants in this category, signiﬁcantly harming the mean IoU of the model. The rest of the weed classes present an acceptable and similar segmentation between them (IoU > 0.7) but still present challenges, possibly due to the visual and morphological variability of the plants present in the different growth stages, and conditions of the terrain, region, weather (seasons), and lighting.


> **Figure 4 shows the RGB images, ground truth masks, and predictions of the best**

> version of Residual U-Net on four example sub-images of 128 × 128. The predicted
segmentation mask matches the ground truth, especially in image (c), which is more
evident due to several weeds.

(a)  (b)  (c)  (d)


> **Figure 4. Four examples of 128 × 128 sub-images (columns (a)–(d)) containing weeds and crop.**

> RGB sub-images (ﬁrst row), ground truth (second row), and Residual U-Net prediction (third row).
Kikuyu weed appears in mustard yellow, Dandelion in orange, Broadleaf dock in blue, potato crop in
green, and other weed species in purple.

3.2. Statistical Validation of Model Predictions

The following are the results of the Student’s t-test for all classes in the dataset. Applying the Student’s t-test on the coverage of the Broadleaf dock weed, a p-value = 0.053 was obtained. Therefore, according to the decision rule, H0 is not rejected, indicating no signiﬁcant difference between coverage measurements. This result could suggest that the model has been able to accurately predict the coverage of this weed without large deviations from the ground truth. The degree of agreement could be associated with visual characteristics of the plant that the model accurately captures, such as variability in the

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 16 of 27

shape or size of this weed. The Pearson correlation coefﬁcient r = 0.999 (p < 0.05) indicates a very high linear association between both measurements.

Using the t-test on the coverage of the Dandelion, a p-value = 0.392 was reached, indicating no signiﬁcant difference between the two coverage measurements. This suggests that the model has also been able to predict the coverage of this weed consistently and accurately. This may be due to a greater consistency in the visual characteristics of the plants in this group, which facilitates more accurate segmentation by the model. The Pearson correlation coefﬁcient r = 0.784 (p < 0.05) indicates a high linear association between both measurements.

Utilizing the t-test on the coverage of the Kikuyu, a p-value = 0.004 was achieved, indicating a signiﬁcant difference between the two coverage measurements. The model could have certain difﬁculties in accurately segmenting this class, possibly due to the plant’s particular characteristics or the variability in the images, such as the size or color of the weed in different growth stages. This discrepancy highlights the need to improve the model’s segmentation capacity for this class, probably by adjusting its parameters or including more representative data during training. The Pearson correlation coefﬁcient r = 0.996 (p < 0.05) indicates a very high linear association between both measurements.

Continuing with the t-test on “other weeds” coverage, a p-value = 0.363 was obtained, indicating no signiﬁcant difference between the two measurements. This result suggests that the model is more reliable in predicting this category. The Pearson correlation coefﬁ- cient r = 0.873 (p < 0.05) indicates a high linear association between both measurements.

The t-test on the coverage of potato crops reached a p-value of 0.970, indicating no signiﬁcant difference between the two coverage measurements. This suggests that the model handles potato crop segmentation well, with no major differences between actual and predictions. The Pearson correlation coefﬁcient r = 0.999 (p < 0.05) indicates a very high linear association between both measurements.

Lastly, the t-test on the coverage of background reached a p-value of 0.001, indicating a signiﬁcant difference between the two coverage measurements. This result may sug- gest that the model has some challenges in correctly distinguishing background areas. Background segmentation can be particularly complex due to noise, foreign objects, or insufﬁcient representation of background features in the training data, leading to signiﬁcant discrepancies in certain images. The Pearson correlation coefﬁcient r = 0.999 (p < 0.05) indicates a very high linear association between both measurements.


> **Table 5 summarizes the statistical validation, providing a clearer and more concise**

> presentation of the Student’s t-test.


> **Table 5. A summary of the Student’s t-test applied to all classes in the dataset. Signiﬁcance indicates**

> whether the difference between the compared measurements is statistically signiﬁcant (p < 0.05).

Class p-Value Signiﬁcance

Broadleaf dock 0.053 No Dandelion 0.392 No Kikuyu 0.004 Yes Other weeds 0.363 No Potato crops 0.970 No Background 0.001 Yes

It was concluded that the Residual U-Net model has a high concordance concerning the predictions of the three speciﬁc classes (Potato, Broadleaf dock, Dandelion, and Other weeds). However, this level of agreement is reduced for detecting pixels belonging to the Kikuyu and Background categories according to the t-test. This could be due to several factors related to unusual characteristics of the plants (size, shape, density), variability

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 17 of 27

in outdoor lighting conditions, capture angles, presence of shadows, overlapping plants, abrupt changes in the texture, presence of species not adequately represented in the train- ing data, noise in the images (mislabeled, blurry examples) and foreign objects (stones, sticks, branches).

Focusing on the Kikuyu class, a moderate IoU of 0.7730 is maintained (Table 4). Still, contradictorily, there are signiﬁcant differences between the actual and predicted measurements according to the Student’s t-test. This means that, although the model predicts this class well, on average, there are certain atypical images where the coverage prediction is substantially different from the actual coverage (ground truth). This was evidenced by moderate and extreme outliers identiﬁed using a box plot regarding the signiﬁcant difference in coverage between the ground truth and the model. Figure 5 shows some example images with signiﬁcant coverage differences in the test set due to some unusual factors of the plants and the dataset mentioned above.

(a)  (b)  (c)  (d)


> **Figure 5. Four examples of 128 × 128 sub-images (columns (a)–(d)) containing weeds and crop. RGB**

> sub-images (128 × 128) of the ground truth (ﬁrst row) and predicted (second row) with the largest
differences in plant coverage on the test set. Kikuyu weed appears in mustard yellow, Dandelion in
orange, Broadleaf dock in blue, Potato crop in green, and other weeds in purple.

This phenomenon regarding the discrepancy between the IoU metric and the t-student’s test in certain classes (Kikuyu and background) may be common in semantic segmentation problems. In the speciﬁc case where a low IoU is obtained for a certain class of weeds (Dandelion and other weeds), but the Student’s t-test indicates that there are no signiﬁcant differences between the predicted weed coverage and the ground truth, it may be due to the following factors related to the nature of the metrics, the data, and the model. The IoU is a local metric that assesses the precise overlap between the predicted and ground truth regions, penalizing differences in shape, position, or edge. In contrast, the Student’s t-test is based on a global metric (coverage percentage), which smooths out the effects of local errors, provided that the predicted area of the class is similar to the ground truth. Also, weed edges are areas where models often struggle more due to transitions with the background or between plant classes. Small errors at the edges can signiﬁcantly reduce the IoU, but the impact on the coverage percentage may be minimal. This test is less sensitive to local mistakes, such as small inconsistencies at the edges.

The opposite case, where a high IoU is obtained for the Background class, but the Student’s t-test indicates signiﬁcant differences in coverage, may be due to the following factors. The Student’s t-test may be more sensitive to small accumulated differences in

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 18 of 27

percentage coverage, i.e., systematic differences in area prediction. In contrast, the IoU reﬂects an average of overlaps that does not penalize accumulated excesses or deﬁcits as much if the local overlap is good. A high IoU can be obtained if the main areas of the weed are correctly segmented, but the model adds additional pixels (false positives) or excludes peripheral areas (false negatives) that alter the overall percentage coverage that can be detected as signiﬁcant differences by the Student’s t-test.

Discrepancies between IoU and Student’s t-test results often arise from differences between how the metrics capture local (IoU) and global (Student’s t-test) errors. The IoU metric accurately assesses the overlap between predicted areas and ground truth and is useful in cases where weeds’ shapes and exact locations are critical. The coverage-based Student’s t-test captures overall differences in the percentage of area covered by weeds. It is most relevant in applications where the total amount of weeds is of interest rather than their exact shape or location (e.g., estimating the amount of weeds in a plot for agricultural planning). The combination of both metrics or evaluation criteria offers a comprehensive approach to validate our model in practical applications.

On the other hand, the Residual U-Net model was trained on Google Colab Pro+ on a GPU Nvidia A100 for 100 epochs in 2.5 h, with a relatively fast inference time of 58.5 ms (17 fps) per 128 × 128 image patch (model input size), occupying 515 MB of storage. In real-world deployment, full-resolution UAV images would be processed using a sliding- window tiling strategy, where large images are divided into overlapping patches, processed individually, and reassembled to produce the ﬁnal segmentation map of the entire ﬁeld.

The evaluated models present different trade-offs between accuracy and computa- tional complexity. Large architectures such as Residual U-Net and Double U-Net achieve higher segmentation performance but involve a large number of parameters, making them more suitable for ofﬂine or ground-based processing. In contrast, lighter models offer faster inference and lower memory requirements, which are critical for real-time or onboard UAV deployment. A detailed evaluation of inference time and energy consumption was beyond the scope of this study and could be addressed in future work if necessary.


## 4. Discussion

4.1. Segmentation Performance and Model Comparison

This research explores ﬁve versions of the U-Net convolutional neural network [23], adapting them for the semantic segmentation of weeds in potato crops using UAV imagery, following the line of research of our previous work [19]. It aims to make the upsampling masks (decoder) better ﬁt the silhouettes and ﬁne details of the plants, which turns out to be a very challenging task with UAV images [84]. Throughout the implementation of the different architectures, experiments were carried out with varying hyperparameters of training to ﬁnd the optimal model for this task [85]. The models have been trained on a medium and diverse dataset, allowing them to learn robust and discriminative features. This adoption and experimentation of the U-Net network variants using a custom dataset represents an important impact on the ﬁeld of study in our region (Ecuador), considering native weeds.

The present study makes a distinct contribution for two key reasons relative to our prior work. First, the dataset used here is 56% larger, incorporating additional ﬁeld conditions that enable a more robust and comprehensive evaluation. Second, this study introduces a different segmentation architecture (Residual U-Net), which substantially changes the modeling approach, the receptive-ﬁeld characteristics, and the nature of the learned spatial representations, leading to signiﬁcant performance improvements over our previous approach. Thus, according to Table 3, the Residual U-Net is the best model on our

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 19 of 27

dataset, with a mean IoU of 0.8053. The AU-Net version is the worst model, with a mean IoU of 0.6150.


> **Table 6 compares the results of this work against different U-Net CNN model variants**

> used in binary and multi-class semantic weed segmentation, utilizing only UAV images
(for a fair comparison) on the test set, using mainly the mIoU metric, which is critical for
practical applications [43] and more robust than overall accuracy (OA) [75,76] as mentioned
before. As far as we know, a limited number of models focused on both U-Net architectures
and UAV images.


> **Table 6. Comparison of U-Net CNN model variants used in binary and multi-class semantic weed**

> segmentation, utilizing only UAV images for a fair comparison.

Authors Year Model Architecture Crop Weed Species Number of

Classes Mean IoU Overall ACC

(%)

Amarasingam

et al. [26] 2023 U-Net - Bitou bush 3 0.7320 92

Kong et al. [43] 2024 ECSNet Corn Generic weeds 2 0.909 90.2

Bretas et al. [42] 2024 U-Net Grass pastures Amaranthus

spinosus L. 2 - 94

Gao et al. [6] 2024 Similar to

U-Net Maize Generic weeds 3 0.617 73.4

Broadleaf dock,

Dandelion, Kikuyu, other

Vinueza et al. [19] 2025 Modiﬁed ResNeXt50 Potato

6 0.7350 75.5

weeds

Machidon et al. [44] 2025 SSU-Net Lettuce and

Tobacco Generic weeds 3 0.5828 90.47

Asuka et al. [37] 2025 U-Net++ Rice Generic weeds 2 0.7060 97.1 Mei et al. [45] 2025 SSMR-Net Wheat Generic weeds 3 0.865 -

Guo et al. [47] 2025 CTFFNet Rice Barnyard grass, Sagittaria trifolia 3 0.728 -

Broadleaf dock,

Our work 2026 Residual

Dandelion,

6 0.8021 82.4

U-Net Potato

Kikuyu, other weeds

Note: Top values are in bold for binary and multi-class segmentation.

Regarding works with multi-class segmentation (>2 classes) using UAV images, the best model is SSMR-Net [45], obtaining a mean IoU (mIoU) of 0.865, followed by our study using the Residual U-Net model, with a mIoU of 0.8021, the modiﬁed ResNeXt50 architecture [19] with 0.7350, U-Net [26] with 0.7320, the CTFFNet [47] with 0.728, the work similar to the U-Net model [6] with 0.617, and SSU-Net [44] with 0.58. Considering the number of classes, our work identiﬁes six classes, greater than the rest, with three and two classes, representing an important contribution to the ﬁeld of study and agricultural sustainability. Contrasting this work with our previous ResNeXt50-based [19], both iden- tifying six classes, the Residual U-Net model signiﬁcantly improves 9.1% with a mean IoU = 0.8021 versus 0.7350. This may be due to the model’s training with an extended dataset of about 56%, the balancing of the classes (crop and weeds), and the variant of the architecture (Residual U-Net) that better captures complex discriminant features of plants for the semantic segmentation task.

Regarding the works based on binary segmentation (crop and weed) using UAV images, the highest mIoU of 0.909 is reported in [43], followed by our model using Residual U-Net with 0.8021 and U-Net++ [37] with 0.7060. This metric is not reported in [42], although they achieve an overall accuracy (OA) of 94%. This conﬁrms that the lower the number of classes addressed, the higher the performance metric is. However, as mentioned, our proposal considers six classes (including background), allowing a more detailed and speciﬁc segmentation, adapted to real agricultural scenarios with multiple weed species (Broadleaf dock, Dandelion, Kikuyu, other weeds) and crops (potato), which are very

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 20 of 27

representative in the provinces of Imbabura and Carchi (Ecuador) where this study is carried out.

4.2. Generalization, Practical Implications, and Limitations

In general, the Residual U-Net model presents an adequate performance comparable to or superior to those found in the existing literature, but in our case, considering a larger set of classes (six), mostly from UAV images. This model’s good performance agrees with the results obtained by [21]. However, the “other weeds” class still penalizes the model’s overall performance. The “other weeds” class intentionally groups heterogeneous plant species with low frequency or ambiguous visual characteristics. While this reduces class separability and leads to lower IoU values, it reﬂects realistic agricultural conditions where unknown or rare weeds are present. This design enables the model to maintain robustness when encountering unseen species, at the cost of reduced interpretability for this speciﬁc class.

According to the literature on weed segmentation using UAV images [27], a mIoU > 0.70 is considered adequate for practical applications, while values above 0.80 (as in our work) indicate high performance even in challenging and complex scene conditions (similar species, high density, occlusion, variable illumination, UAV height, movement, etc.). It is important to note that IoU and Dice metrics directly evaluate pixel-level segmen- tation quality, while the Student’s t-test is used to assess the reliability of aggregated weed coverage estimates from a practical decision-making perspective. Although confusion ma- trices and per-class precision/recall could provide additional insight into misclassiﬁcation patterns, these analyses are complementary and will be explored in future work.

From a practical perspective, accurate semantic segmentation directly enables reli- able weed coverage estimation, which is a key input for agricultural decision-making. Coverage thresholds can be deﬁned to trigger site-speciﬁc treatments, such as localized herbicide application or mechanical weed control, reducing chemical use and operational costs. Therefore, improvements in IoU and Dice metrics translate into more accurate treatment maps, enabling precision agriculture strategies based on objective and spatially explicit information.

Although this study focuses on U-Net-based architectures, recent CNN–Transformer and hybrid models have shown promising results for weed segmentation. Evaluating these models under the same experimental conditions represents an important direction for upcoming work. However, such models typically require larger datasets and higher computational resources, which were beyond the scope of this study.

Regarding this study’s limitations, the dataset’s number of classes is still restricted to the six main categories mentioned, which limits the model’s ability to generalize in more complex agricultural scenarios. Additionally, the dataset is limited to a certain crop growth stage (15 to 40 days), which could reduce the model’s applicability across different seasons or other growth stages. Although the dataset includes images acquired from different ﬁelds, provinces, and crop growth stages, this study does not perform a strict cross-season or cross-region validation. UAV imagery is highly sensitive to environmental variability, including illumination changes, soil moisture, and plant phenology, which can affect model performance. Evaluating model robustness under these conditions remains an important challenge and will be addressed in future work through longitudinal data collection and domain adaptation strategies. Another restriction is the exclusive use of U-Net architec- tures focused on semantic segmentation, leaving aside other current deep architectures (including Transformers) or a combination of them (CNN + Transformer), which could limit the model’s ability to capture global features. The attention mechanism used on the AU-Net is limited to the Attention Gate (AG), without considering other mechanisms [38]. Further-

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 21 of 27

more, most integrated devices would consider our model large (515 MB) for UAV-based scouting. Although the inference time remained fast, achieving 58.5 ms per 128 × 128 patch (≈17 fps) on the Colab platform, it could be compatible with near real-time processing. These results indicate that, despite the model size, the inference latency can be sufﬁciently low for practical deployment in post-ﬂight analysis workﬂows. Nevertheless, we acknowl- edge that future work could explore lightweight model compression strategies—such as pruning, quantization, or knowledge distillation—to reduce storage requirements further and enable on-device inference on embedded hardware. Finally, our work uses a low-cost UAV to capture RGB images, mainly because they are popular and affordable, offering a cost-efﬁcient solution [77].


## 5. Conclusions

In the present study, ﬁve versions of the U-Net architecture are tested for the semantic segmentation of several kinds of native weeds in uncontrolled environments, successfully processing six categories: background, potato, Broadleaf dock, Dandelion, Kikuyu, and other weeds. The network architectures are original U-Net, Residual U-Net, Double U-Net, Modiﬁed U-Net, and AU-Net. Based on our previous work, the dataset for the model’s training is extended and balanced to achieve better results. The Residual U-Net is the best model for adjusting the resulting multi-class segmentation to the silhouettes of the native plants under study, with a mean IoU of 0.8021. This model obtains results comparable to or superior to those in the literature dealing with fewer categories (Table 6), taking a relatively fast inference time of 58.5 ms (17 fps) for a 128×128 image, occupying a storage size of 515 MB. Future work should increase the variability of images and weed classes in the dataset by incorporating greater variation in shape, size, and environment, and prioritize class balancing. It would also be advisable to experiment with a combination of modern deep neural networks based on CNNs and/or Transformers (to capture global relationships among image elements), as well as other attention mechanisms—beyond the Attention Gate module, such as self-attention, multi-head attention, or lightweight transformer blocks—to address small objects and plants of varying sizes. Further research will explore hybrid architectures to assess potential accuracy gains while maintaining feasibility for UAV- based agricultural deployment. Lighter models optimized for real-time implementation on embedded devices, applying techniques such as quantization, pruning, or knowledge distillation, are also recommended. Additionally, alternative loss functions can be explored that explicitly address the observed pixel-wise class imbalance, such as focal loss, class- balanced cross-entropy, or hybrid combinations of Dice and cross-entropy, to improve the segmentation of minority weed classes. Evaluating model robustness under strict cross-season or cross-region conditions through longitudinal data collection and domain adaptation strategies is suggested. Finally, following this research line, weed mapping is necessary to create georeferenced maps that indicate the spatial distribution and density of weeds within a ﬁeld.

Author Contributions: L.S.-P.: Conceptualization, Formal Analysis, Investigation, Methodology, Validation, Writing—Original Draft. M.P.-C.: Data curation, Methodology, Visualization, Writing— Original Draft. J.P.-M.: Software, Data Curation, Formal Analysis, Writing—Original Draft. P.G.-G.: Conceptualization, Writing—Review and Editing, Supervision. I.G.-S.: Formal Analysis, Funding acquisition, Resources, Validation, Writing—Review and Editing. All authors have read and agreed to the published version of the manuscript.

Funding: This research was mostly funded by the Universidad Técnica del Norte, Ibarra, Ecuador, under Grant Number: InvestigaUTN-2025-1516.

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 22 of 27

Institutional Review Board Statement: Not applicable.

Informed Consent Statement: Not applicable.

Data Availability Statement: Datasets used in this study were made publicly available for comparison purposes and can be found at the following link: https://github.com/JorgePazos- git/Dataset-of-weeds-in-potato-crops-in-the-province-of-Carchi-and-Imbabura-in- (last accessed 8 December 2025).

Acknowledgments: This research is supported by the Software Engineering and Artiﬁcial Intelligence research group from the Universidad Técnica del Norte (Ecuador) and the GTI-IA research group from Universitat Politècnica de València (Spain).

Conﬂicts of Interest: The authors declare no conﬂict of interest.

Appendix A

Proposed AU-Net with four attention gate modules and residual blocks (rectangles in red), following [26,48] about the use of attention mechanisms.

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 23 of 27


## References

1. FAO. Recommendations for Improved Weed Management; FAO: Rome, Italy, 2006; pp. 1–56. Available online: https://www.fao.org/4/a0884e/a0884e.pdf (accessed on 8 December 2025). 2. Singh, S.; Rawal, S.; Dua, V.; Roy, S.; Sadaworthy, M.; Charkrabarti, S.; Sadawarti, M. Weed management in conventional and organic potato production. Int. J. Chem. Stud. 2018, 2, 24–38. 3. Craine, J.M.; Dybzinski, R. Mechanisms of plant competition for nutrients, water and light. Funct. Ecol. 2013, 27, 833–840. [CrossRef] 4. Pusdá-Chulde, M.R.; Salazar-Fierro, F.A.; Sandoval-Pillajo, L.; Herrera-Granda, E.P.; García-Santillán, I.D.; De Giusti, A. Image Analysis Based on Heterogeneous Architectures for Precision Agriculture: A Systematic Literature Review. Adv. Appl. Comput. Sci. Electron. Ind. Eng. 2020, 1078, 51–70. [CrossRef] 5. Zimdahl, R.L. Weed Reproduction and Dispersal. In Fundamentals of Weed Science, 5th ed.; Academic Press: Cambridge, MA, USA, 2018; pp. 83–121. [CrossRef] 6. Gao, J.; Liao, W.; Nuyttens, D.; Lootens, P.; Xue, W.; Alexandersson, E.; Pieters, J. Cross-domain transfer learning for weed segmentation and mapping in precision farming using ground and UAV images. Expert Syst. Appl. 2024, 246, 122980. [CrossRef] 7. Jabed, M.A.; Azmi Murad, M.A. Crop yield prediction in agriculture: A comprehensive review of machine learning and deep learning approaches, with insights for future research and sustainability. Heliyon 2024, 10, e40836. [CrossRef] 8. Coulibaly, S.; Kamsu-Foguem, B.; Kamissoko, D.; Traore, D. Deep Convolution Neural Network sharing for the multi-label images classiﬁcation. Mach. Learn. Appl. 2022, 10, 100422. [CrossRef] 9. Cevallos, M.; Sandoval-Pillajo, L.; Caranqui-Sánchez, V.; Ortega-Bustamante, C.; Pusdá-Chulde, M.; García-Santillán, I. Mor- phological Defects Classiﬁcation in Coffee Beans Based on Convolutional Neural Networks. In Communications in Computer and Information Science; Springer: Cham, Switzerland, 2025; pp. 3–15. [CrossRef] 10. Chacua, B.; Garcia, I.; Rosero, P.; Suarez, L.; Ramirez, I.; Simbana, Z.; Pusdá-Chulde, M. People Identiﬁcation through Facial Recognition using Deep Learning. In Proceedings of the 2019 IEEE Latin American Conference on Computational Intelligence (LA-CCI), Guayaquil, Ecuador, 11–15 November 2019; IEEE: New York, NY, USA, 2019; pp. 1–6. 11. Montenegro, S.; Pusdá-Chulde, M.; Caranqui-Sánchez, V.; Herrera-Tapia, J.; Ortega-Bustamante, C.; García-Santillán, I. Android Mobile Application for Cattle Body Condition Score Using Convolutional Neural Networks. In Communications in Computer and Information Science; Springer: Cham, Switzerland, 2023; pp. 91–105. [CrossRef] 12. Salazar-Fierro, F.; Cumbal, C.; Trejo-España, D.; León-Fernández, C.; Pusdá-Chulde, M.; García-Santillán, I. Detection of Scoliosis in X-Ray Images Using a Convolutional Neural Network. In Communications in Computer and Information Science; Springer: Cham, Switzerland, 2025; pp. 167–183. [CrossRef] 13. Ulloa, F.; Sandoval-Pillajo, L.; Landeta-López, P.; Granda-Peñaﬁel, N.; Pusdá-Chulde, M.; García-Santillán, I. Identiﬁcation of Diabetic Retinopathy from Retinography Images Using a Convolutional Neural Network. In Communications in Computer and Information Science; Springer: Cham, Switzerland, 2025; pp. 121–136. [CrossRef] 14. Guaichico, E.; Pusdá-Chulde, M.; Ortega-Bustamante, M.; Granda, P.; García-Santillán, I. Mobile app for real-time academic attendance registration based on MobileFaceNet Convolutional neural network. Data Metadata 2025, 4, 193. [CrossRef] 15. Chamorro-Pinchao, A.; Pusdá-Chulde, M.; Trejo-España, D.; Caranqui-Sánchez, V.; García-Santillán, I. Binary classiﬁcation of defects in multiple coffee beans using lightweight convolutional neural networks for embedded systems. Data Metadata 2025, 4, 840. [CrossRef] 16. Valizadeh, M.; Wolff, S.J. Convolutional Neural Network applications in additive manufacturing: A review. Adv. Ind. Manuf. Eng. 2022, 4, 100072. [CrossRef] 17. Espejo-Garcia, B.; Mylonas, N.; Athanasakos, L.; Fountas, S.; Vasilakoglou, I. Towards weeds identiﬁcation assistance through transfer learning. Comput. Electron. Agric. 2020, 171, 105306. [CrossRef] 18. McCool, C.; Perez, T.; Upcroft, B. Mixtures of Lightweight Deep Convolutional Neural Networks: Applied to Agricultural Robotics. IEEE Robot. Autom. Lett. 2017, 2, 1344–1351. [CrossRef] 19. Vinueza, K.; Sandoval-Pillajo, L.; Giret-Boggino, A.; Trejo-España, D.; Pusdá-Chulde, M.; García-Santillán, I. Automatic weed quantiﬁcation in potato crops based on a modiﬁed convolutional neural network using drone images. Data Metadata 2025, 4, 194. [CrossRef] 20. Zhang, Y.; Cai, H.; Ye, J.; Pan, F.; Wu, S.; Zhang, B.; Qi, L.; Ma, R. Exploiting adversarial style for generalized and robust weed segmentation in rice paddy ﬁeld. Front. Plant Sci. 2025, 16, 1703811. [CrossRef] [PubMed] 21. Garibaldi-Márquez, F.; Flores, G.; Valentín-Coronado, L.M. Leveraging deep semantic segmentation for assisted weed detection. J. Agric. Eng. 2025, 56, 1741. [CrossRef] 22. García-Santillán, I.D.; Pajares, G. On-line crop/weed discrimination through the Mahalanobis distance from images in maize ﬁelds. Biosyst. Eng. 2018, 166, 28–43. [CrossRef] 23. Ronneberger, O.; Fischer, P.; Brox, T. U-Net: Convolutional Networks for Biomedical Image Segmentation. arXiv 2015. [CrossRef]

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 24 of 27

24. Darbyshire, M.; Coutts, S.; Bosilj, P.; Sklar, E.; Parsons, S. Review of weed recognition: A global agriculture perspective. Comput. Electron. Agric. 2024, 227, 109499. [CrossRef] 25. Rai, N.; Sun, X. WeedVision: A single-stage deep learning architecture to perform weed detection and segmentation using drone-acquired images. Comput. Electron. Agric. 2024, 219, 108792. [CrossRef] 26. Amarasingam, N.; Kelly, J.E.; Sandino, J.; Hamilton, M.; Gonzalez, F.; Dehaan, R.L.; Zheng, L.; Cherry, H. Bitou bush detection and mapping using UAV-based multispectral and hyperspectral imagery and artiﬁcial intelligence. Remote Sens. Appl. Soc. Environ. 2024, 34, 101151. [CrossRef] 27. Sandoval-Pillajo, L.; García-Santillán, I.; Pusdá-Chulde, M.; Giret, A. Weed detection based on deep learning from UAV imagery: A review. Smart Agric. Technol. 2025, 12, 101147. [CrossRef] 28. Yuan, J.; Wang, L.; Wang, T.; Bashir, A.K.; Al Dabel, M.M.; Wang, J.; Feng, H.; Fang, K.; Wang, W. YOLOv8-RD: High-Robust Pine Wilt Disease Detection Method Based on Residual Fuzzy YOLOv8. IEEE J. Sel. Top. Appl. Earth Obs. Remote Sens. 2025, 18, 385–397. [CrossRef] 29. Deng, B.; Lu, Y.; Xu, J. Weed database development: An updated survey of public weed datasets and cross-season weed detection adaptation. Ecol. Inform. 2024, 81, 102546. [CrossRef] 30. Goyal, R.; Nath, A. Utkarsh Niranjan IndianPotatoWeeds: A Novel Dataset and its Role in Weed Detection and Management for Potato Crops. SN Comput. Sci. 2025, 6, 466. [CrossRef] 31. Fayyad, U.; Piatetsky-Shapiro, G.; Smyth, P. From Data Mining to Knowledge Discovery in Databases. AI Mag. 1996, 17, 37. [CrossRef] 32. Cui, J.; Tan, F.; Bai, N.; Fu, Y. Improving U-net network for semantic segmentation of corns and weeds during corn seedling stage in ﬁeld. Front. Plant Sci. 2024, 15, 1344958. [CrossRef] 33. Zhang, S.; Zhang, C. Modiﬁed U-Net for plant diseased leaf image segmentation. Comput. Electron. Agric. 2023, 204, 107511. [CrossRef] 34. Zuo, Y.; Li, W. An Improved UNet Lightweight Network for Semantic Segmentation of Weed Images in Corn Fields. Comput. Mater. Contin. 2024, 79, 4413–4431. [CrossRef] 35. Thiagarajan, S.; Vijayalakshmi, A.; Grace, G.H. Weed detection in precision agriculture: Leveraging encoder-decoder models for semantic segmentation. J. Ambient Intell. Humaniz. Comput. 2024, 15, 3547–3561. [CrossRef] 36. Liao, J.; Chen, M.; Zhang, K.; Zhou, H.; Zou, Y.; Xiong, W.; Zhang, S.; Kuang, F.; Zhu, D. SC-Net: A new strip convolutional network model for rice seedling and weed segmentation in paddy ﬁeld. Comput. Electron. Agric. 2024, 220, 108862. [CrossRef] 37. Asuka, S.; Nakamura, T.; Shimizu, I.; Ookawa, T.; Nakajo, H. Ensemble Learning-Based Weed Detection from a Duck’s Perspective Using an Aquatic Drone in Rice Paddies. Appl. Sci. 2025, 15, 7440. [CrossRef] 38. Li, Z.; Yan, Y.; Wei, M.; Ge, B.; Su, N. FGOD-YOLOv8: Fine-Grained Object Detection for Crops and Weeds. IEEE Signal Process. Lett. 2025, 32, 791–795. [CrossRef] 39. Garibaldi-Márquez, F.; Flores, G.; Valentín-Coronado, L.M. Corn/Weed Plants Detection Under Authentic Fields based on Patching Segmentation and Classiﬁcation Networks. Comput. Sist. 2024, 28, 271–282. [CrossRef] 40. Garibaldi-Márquez, F.; Martínez-Barba, D.A.; Montañez-Franco, L.E.; Flores, G.; Valentín-Coronado, L.M. Enhancing site-speciﬁc weed detection using deep learning transformer architectures. Crop Prot. 2025, 190, 107075. [CrossRef] 41. Ma, Z.; Wang, G.; Yao, J.; Huang, D.; Tan, H.; Jia, H.; Zou, Z. An Improved U-Net Model Based on Multi-Scale Input and Attention Mechanism: Application for Recognition of Chinese Cabbage and Weed. Sustain. Switz. 2023, 15., 5764. [CrossRef] 42. Bretas, I.L.; Dubeux, J.C.B.; Zhao, C.; Queiroz, L.M.D.; Flynn, S.; Ingram, S.; Oduor, K.T.; Cruz, P.J.R.; Ruiz-Moreno, M.; Loures, D.R.S.; et al. Detection and mapping of Amaranthus spinosus L. in bermudagrass pastures using drone imagery and deep learning for a site-speciﬁc weed management. Agron. J. 2024, 116, 990–1002. [CrossRef] 43. Kong, X.; Liu, T.; Chen, X.; Jin, X.; Li, A.; Yu, J. Efﬁcient crop segmentation net and novel weed detection method. Eur. J. Agron. 2024, 161, 127367. [CrossRef] 44. Machidon, A.L.; Krašovec, A.; Pejovi´c, V.; Machidon, O.M. SqueezeSlimU-Net: An Adaptive and Efﬁcient Segmentation Architecture for Real-Time UAV Weed Detection. IEEE J. Sel. Top. Appl. Earth Obs. Remote Sens. 2025, 18, 5749–5764. [CrossRef] 45. Mei, X.; Li, C.; Jiao, Y.; Zhang, G.; Zhou, L.; Wu, X.; Cai, T. SSMR-Net and Across Feature Mapping Attention are jointly applied to the UAV imagery semantic segmentation task of weeds in early-stage wheat ﬁelds. Smart Agric. Technol. 2025, 12, 101077. [CrossRef] 46. Jiang, H.; Chen, Q.; Wang, R.; Du, J.; Chen, T. SWFormer: A scale-wise hybrid CNN-Transformer network for multi-classes weed segmentation. J. King Saud Univ.—Comput. Inf. Sci. 2024, 36, 102144. [CrossRef] 47. Guo, Z.; Cai, D.; Jin, Z.; Xu, T.; Yu, F. Research on unmanned aerial vehicle (UAV) rice ﬁeld weed sensing image segmentation method based on CNN-transformer. Comput. Electron. Agric. 2025, 229, 109719. [CrossRef] 48. Sulaiman, A.; Anand, V.; Gupta, S.; Rajab, A.; Alshahrani, H.; Al Reshan, M.S.; Shaikh, A.; Hamdi, M. Attention based UNet model for breast cancer segmentation using BUSI dataset. Sci. Rep. 2024, 14, 22422. [CrossRef] 49. Kamilaris, A.; Prenafeta-Boldú, F.X. Deep learning in agriculture: A survey. Comput. Electron. Agric. 2018, 147, 70–90. [CrossRef]

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 25 of 27

50. Valente, J.; Kooistra, L. Dataset on UAV High-Resolution Images from Grassland with Broad-Leaved Dock (Rumex Obtusifolius). [Data Set]. Zenodo. 2021. Available online: https://zenodo.org/records/5119205 (accessed on 25 February 2026). 51. Dos Santos Ferreira, A. Data for: Weed Detection in Soybean Crops Using ConvNets. Comput. Electron. Agric. 2017, 143, 314–324. [CrossRef] 52. Danilevicz, M.; Rocha, R.L.; Batley, J.; Bayer, P.E.; Bennamoun, M.; Edwards, D.; Ashworth, M. Segmentation of sandplain lupin weeds from morphologically similar narrow-leafed lupins in the ﬁeld. Remote Sens. 2023, 15, 1817. [CrossRef] 53. Imran Moazzam. Tobacco Aerial Dataset. [Data Set]. Mendeley Data. 2023. Available online: https://data.mendeley.com/datasets/5dpc5gb (accessed on 25 February 2026). 54. Sa, I.; Popovi´c, M.; Khanna, R.; Chen, Z.; Lottes, P.; Liebisch, F.; Nieto, J.; Stachniss, C.; Walter, A.; Siegwart, R. WeedMap: A Large-Scale Semantic Weed Mapping Framework Using Aerial Multispectral Imaging and Deep Neural Network for Precision Farming. Remote Sens. 2018, 10, 1423. [CrossRef] 55. Koshelev, I.; Savinov, M.; Menshchikov, A.; Somov, A. Drone-Aided Detection of Weeds: Transfer Learning for Embedded Image Processing. IEEE J. Sel. Top. Appl. Earth Obs. Remote Sens. 2023, 16, 102–111. [CrossRef] 56. Genze, N.; Ajekwe, R.; Güreli, Z.; Haselbeck, F.; Grieb, M.; Grimm, D.G. Deep learning-based early weed segmentation using motion blurred UAV images of sorghum ﬁelds. Comput. Electron. Agric. 2022, 202, 107388. [CrossRef] 57. Huang, H.; Deng, J.; Lan, Y.; Yang, A.; Deng, X.; Zhang, L. A Fully Convolutional Network for weed mapping of Unmanned Aerial Vehicle (UAV) Imagery. PLoS ONE 2018, 13, e0196302. [CrossRef] 58. Krestenitis, M.; Raptis, E.K.; Kapoutsis, A.C.; Ioannidis, K.; Kosmatopoulos, E.B.; Vrochidis, S.; Kompatsiaris, I. CoFly-WeedDB: A UAV image dataset for weed detection and species identiﬁcation. Data Brief 2022, 45, 108575. [CrossRef] 59. Rai, N.; Villamil Mahecha, M.; Christensen, A.; Quanbeck, J.; Howatt, K.; Ostlie, M.; Zhang, Y.; Sun, X. ImageWeeds: An Image Dataset Consisting of Weeds in Multiple Formats to Advance Computer Vision Algorithms for Real-Time Weed Identiﬁca- tion and Spot Spraying Application. 2023. Available online: https://data.mendeley.com/datasets/8kjcztbjz2/2 (accessed on 25 February 2026). 60. Yang, M.-D.; Tseng, H.-H.; Hsu, Y.-C.; Yang, C.-Y.; Lai, M.-H.; Wu, D.-H. A UAV Open Dataset of Rice Paddies for Deep Learning Practice. Remote Sens. 2021, 13, 1358. [CrossRef] 61. Machidon, O.M.; Krašovec, A.; Machidon, A.L.; Pejovi´c, V.; Latini, D.; Sasidharan, S.T.; Del Frate, F. AgriAdapt: Towards Resource-Efﬁcient UAV Weed Detection using Adaptable Deep Learning. In Proceedings of the 2nd Workshop on Networked Sensing Systems for a Sustainable Society, Madrid, Spain, 6 October 2023; ACM: New York, NY, USA, 2023; pp. 193–200. 62. Tian, F.; Ransom, C.J.; Zhou, J.; Wilson, B.; Sudduth, K.A. Assessing the impact of soil and ﬁeld conditions on cotton crop emergence using UAV-based imagery. Comput. Electron. Agric. 2024, 218, 108738. [CrossRef] 63. Anderegg, J.; Tschurr, F.; Kirchgessner, N.; Treier, S.; Schmucki, M.; Streit, B.; Walter, A. On-farm evaluation of UAV-based aerial imagery for season-long weed monitoring under contrasting management and pedoclimatic conditions in wheat. Comput. Electron. Agric. 2023, 204, 107558. [CrossRef] 64. Wang, Q.; Cheng, M.; Xiao, X.; Yuan, H.; Zhu, J.; Fan, C.; Zhang, J. An image segmentation method based on deep learning for damage assessment of the invasive weed Solanum rostratum Dunal. Comput. Electron. Agric. 2021, 188, 106320. [CrossRef] 65. Pertuz, S.; Puig, D.; Garcia, M.A. Analysis of focus measure operators for shape-from-focus. Pattern Recognit. 2013, 46, 1415–1432. [CrossRef] 66. Sarvini, T.; Sneha, T.; Sukanya Gowthami, G.; Sushmitha, S.; Kumaraswamy, R. Performance Comparison of Weed Detection Algorithms. In Proceedings of the 2019 International Conference on Communication and Signal Processing (ICCSP), Chennai, India, 4–6 April 2019; IEEE: New York, NY, USA, 2019; pp. 0843–0847. 67. Roboﬂow Docs Create a Project|Roboﬂow Docs. Available online: https://docs.roboﬂow.com/datasets/create-a-project (accessed on 28 January 2024). 68. Wang, J.; Hadjikakou, M.; Hewitt, R.J.; Bryan, B.A. Simulating large-scale urban land-use patterns and dynamics using the U-Net deep learning architecture. Comput. Environ. Urban Syst. 2022, 97, 101855. [CrossRef] 69. Çiçek, Ö.; Abdulkadir, A.; Lienkamp, S.S.; Brox, T.; Ronneberger, O. 3D U-Net: Learning Dense Volumetric Segmentation from Sparse Annotation. arXiv 2016. [CrossRef] 70. Tene-Hurtado, D.; Almeida-Galárraga, D.A.; Villalba-Meneses, G.; Alvarado-Cando, O.; Cadena-Morejón, C.; Salazar, V.H. Brain Tumor Segmentation Based on 2D U-Net Using MRI Multi-modalities Brain Images. In Smart Technologies, Systems and Applications (SmartTech-IC 2021); Narváez, F.R., Proaño, J., Morillo, P., Vallejo, D., González Montoya, D., Díaz, G.M., Eds.; Springer International Publishing: Cham, Switzerland, 2022; pp. 345–359. 71. Zhang, Z.; Liu, Q.; Wang, Y. Road Extraction by Deep Residual U-Net. IEEE Geosci. Remote Sens. Lett. 2018, 15, 749–753. [CrossRef] 72. Jha, D.; Riegler, M.A.; Johansen, D.; Halvorsen, P.; Johansen, H.D. DoubleU-Net: A Deep Convolutional Neural Network for Medical Image Segmentation. In Proceedings of the 2020 IEEE 33rd International Symposium on Computer-Based Medical Systems (CBMS), Rochester, MN, USA, 28–30 July 2020; IEEE: New York, NY, USA, 2020; pp. 558–564.

https://doi.org/10.3390/app16073149

Appl. Sci. 2026, 16, 3149 26 of 27

73. Celikkan, E.; Saberioon, M.; Herold, M.; Klein, N. Semantic Segmentation of Crops and Weeds with Probabilistic Modeling and Uncertainty Quantiﬁcation. In Proceedings of the 2023 IEEE/CVF International Conference on Computer Vision Workshops (ICCVW), Paris, France, 2–6 October 2023; IEEE: New York, NY, USA, 2023; pp. 582–592. 74. Ullah, H.S.; Asad, M.H.; Bais, A. End to End Segmentation of Canola Field Images Using Dilated U-Net. IEEE Access 2021, 9, 59741–59753. [CrossRef] 75. Garcia, V.; De Jesus Ochoa Dominguez, H.; Mederos, B. Analysis of Discrepancy Metrics Used in Medical Image Segmentation. IEEE Lat. Am. Trans. 2015, 13, 235–240. [CrossRef] 76. Müller, D.; Soto-Rey, I.; Kramer, F. Towards a guideline for evaluation metrics in medical image segmentation. BMC Res. Notes 2022, 15, 210. [CrossRef] 77. Zou, K.; Chen, X.; Zhang, F.; Zhou, H.; Zhang, C. A Field Weed Density Evaluation Method Based on UAV Imaging and Modiﬁed U-Net. Remote Sens. 2021, 13, 310. [CrossRef] 78. Lind, D.A.; Marchal, W.G.; Wathen, S.A. Basic Statistics in Business and Economics, 10th ed.; McGraw Hill: New York, NY, USA, 2022. 79. Juma, A.; Rodríguez, J.; Caraguay, J.; Naranjo, M.; Quiña-Mera, A.; García-Santillán, I. Integration and Evaluation of Social Networks in Virtual Learning Environments: A Case Study. In Communications in Computer and Information Science; Springer: Cham, Switzerland, 2019; pp. 245–258. [CrossRef] 80. Krizhevsky, A.; Sutskever, I.; Hinton, G.E. ImageNet Classiﬁcation with Deep Convolutional Neural Networks. In Advances in Neural Information Processing Systems 25 (NIPS 2012): 26th Annual Conference on Neural Information Processing Systems 2012; Morgan Kaufmann Publishers, Inc.: Burlington, MA, USA, 2012. 81. Cai, Y.; Zeng, F.; Xiao, J.; Ai, W.; Kang, G.; Lin, Y.; Cai, Z.; Shi, H.; Zhong, S.; Yue, X. Attention-aided semantic segmentation network for weed identiﬁcation in pineapple ﬁeld. Comput. Electron. Agric. 2023, 210, 107881. [CrossRef] 82. Nong, C.; Fan, X.; Wang, J. Semi-supervised Learning for Weed and Crop Segmentation Using UAV Imagery. Front. Plant Sci. 2022, 13, 927368. [CrossRef] 83. Shahi, T.B.; Dahal, S.; Sitaula, C.; Neupane, A.; Guo, W. Deep Learning-Based Weed Detection Using UAV Images: A Comparative Study. Drones 2023, 7, 624. [CrossRef] 84. Sapkota, R.; Stenger, J.; Ostlie, M.; Flores, P. Towards reducing chemical usage for weed control in agriculture using UAS imagery analysis and computer vision techniques. Sci. Rep. 2023, 13, 6548. [CrossRef] 85. Garcia-Garcia, A.; Orts-Escolano, S.; Oprea, S.; Villena-Martinez, V.; Garcia-Rodriguez, J. A Review on Deep Learning Techniques Applied to Semantic Segmentation. arXiv 2017. [CrossRef]

Disclaimer/Publisher’s Note: The statements, opinions and data contained in all publications are solely those of the individual author(s) and contributor(s) and not of MDPI and/or the editor(s). MDPI and/or the editor(s) disclaim responsibility for any injury to people or property resulting from any ideas, methods, instructions or products referred to in the content.

https://doi.org/10.3390/app16073149
