---
workspace_id: SCI-000397
doi: 10.1007/s11042-026-21299-2
title: Semantic segmentation performance of aerial image segmentation using weighted
  ensemble trained networks CNNs
authors:
- family_name: Faska
  given_name: Zahra
  orcid: https://orcid.org/0000-0002-2616-8448
- family_name: Khrissi
  given_name: Lahbib
  orcid: null
- family_name: Haddouch
  given_name: Khalid
  orcid: null
- family_name: El Akkad
  given_name: Nabil
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:26:13.705137+00:00'
---

# Semantic segmentation performance of aerial image segmentation using weighted ensemble trained networks CNNs

Multimedia Tools and Applications          (2026) 85:213  https://doi.org/10.1007/s11042-026-21299-2

Semantic segmentation performance of aerial image  segmentation using weighted ensemble trained networks  CNNs

Zahra Faska1  · Lahbib Khrissi1 · Khalid Haddouch1 · Nabil El Akkad1

Received: 27 October 2023 / Revised: 29 August 2025 / Accepted: 19 September 2025 © The Author(s), under exclusive licence to Springer Science+Business Media, LLC, part of Springer Nature 2026


## Abstract

The task of pixel-wise image segmentation remains significantly challenging in the do­
mains of computer vision and image processing. This paper tries to address the complexi­
ties involved in spatial understanding for the semantic segmentation of high-resolution 
upright images by using Deep Convolutional Neural Networks. In this study, we worked 
with high-resolution images of substantial size. However, in order to facilitate smooth 
processing on a moderately configured computer with standard specifications, we cropped 
the images and reduced their size. We employed the Unet model for the network, which 
is frequently used for input formats that are identical to its intended function. With the 
continuous emergence of new bracket networks, it is crucial to recognize that the back­
bone performance of semantic segmentation networks may differ depending on the bracket 
network utilized. This study presents a comparative analysis of the performance variations 
among ResNet34, InceptionV3, and VGG16 when employed as the backbone for Unet, 
each exhibiting distinct strengths and weaknesses. Consequently, this opens the possibility 
of leveraging a combination of various base learners, which may surpass the performance 
of a singular segmentation model, given the pronounced sensitivity of deep learning mod­
els to differing network architectures. This paper outlines the creation of a weighted en­
semble of multiple CNNs aimed at semantic segmentation of aerial images, harnessing the 
advantages provided by diverse CNN models to enhance both accuracy and generalization 
performance. The weighted ensemble algorithm was implemented by leveraging transfer 
learning on a Unet CNN model, with ResNet34, InceptionV3, and VGG16 serving as the 
encoder bases. Each U-Net model variant was trained using a unique pre-trained network, 
and their predictions were combined through a weighted average method aimed at multi-
class semantic segmentation. The contribution of each model to the weighted average is 
dictated by its assigned weight. Our methodology outperformed individual deep learn­
ing models in independent evaluation, demonstrating improved classification accuracy. 
Additionally, a grid search algorithm was employed to optimize the assigned weights. 
Our experiments utilizing the MBRSC Dubai Aerial Imagery Dataset demonstrated both 
quantitative and qualitative enhancements, suggesting that our approach boosts segmenta­
tion accuracy and reduces distance errors compared to relying on a single classifier. The 
experimental results demonstrate that the weighted average ensemble achieved superior

Extended author information available on the last page of the article


## 1 3

213    Page 2 of 30

Multimedia Tools and Applications          (2026) 85:213

segmentation on aerial images, reaching 87.08% accuracy, 87.06% Dice, and 78.13% IoU,  outperforming individual backbones, standard U-Net, FCN-8 s, and advanced segmenta­ tion architectures such as, HRNet, and DeepLabV3 + .

Keywords  Semantic segmentation · Deep learning · Weighted average ensemble model ·  Transfer learning · U-net · ResNet34 · Inception V3 · VGG16


## 1  Introduction

Image segmentation has long been a crucial subject within the domain of computer vision  and is essential for comprehensive understanding. A multitude of methodologies have been  recently developed [1–16] to improve upon and rectify the shortcomings of previously  established techniques documented in the literature. The three most common types of seg­ mentation techniques are semantic, instance, and panoptic segmentation. The most common  of these is probably semantic segmentation, respected as one of the most complex assign­ ments in the computer vision task towards scene understanding. Technically, this means that  a semantic label is given and associated with each pixel in an image [17–19]. This term is  to be distinctly separated from instance-level segmentation [20], in which the mask is cre­ ated along with the class label for every instance. Lately, panoptic segmentation [21, 22] is  the newest hype that combines both pixel-level and instance-level semantic segmentations.  While most of the problems can be suitably addressed by traditional machine learning algo­ rithms [23], in the newly found area of deep learning techniques [24, 25], a very wide lead  of great success over all other methods is experienced. One of the most fabulous algorithms  for the task of pattern recognition which is driven by images is known as Convolution  Neural Networks (CNN) [26]. Recurrent Neural Networks (RNN) [27, 28] are used to pre­ serve contextual features holding each information piece for some time. Major milestones  in the evolution of deep learning that has significantly pushed further the research area  of semantic segmentation. The challenge of semantic segmentation represents a consider­ able obstacle in the domain of computer vision today. This process finds application across  various forms of media, such as 2D images, videos, and even 3D or volumetric data. In the  broader context, semantic segmentation serves as an essential initial step toward achieving  a thorough comprehension of a scene. The increasing frequency of applications utilizing  image-based data highlights the importance of understanding scenes as a core challenge  within the realm of computer vision. These applications span various domains, including  autonomous driving [29–31], human-computer interaction [32], computer-generated imag­ ery [33], image retrieval systems [34], and augmented reality. Historically, this challenge  has been addressed through conventional computer vision techniques and machine learning  approaches. However, with the advent of the deep learning revolution, the situation has  shifted. Nowadays, many computer vision concerns, including semantic segmentation, can  be tackled by using deep architectures, particularly convolutional neural networks (CNN)  [35], which optimize the accuracy, and sometimes even the efficiency, of methods compared  to other methods. However, deep learning is nowhere near the level of maturity achieved by  computer vision and other historic branches of machine learning. The absence of any cohe­ sive publications or recent analyses is apparent. The constantly evolving nature of the field  poses a formidable challenge for those seeking to begin their research, and staying abreast


## 1 3

Page 3 of 30    213

Multimedia Tools and Applications          (2026) 85:213

of new advances demands a significant investment of time due to the sheer quantity of new  literature being generated. Consequently, this situation complicates the ability to monitor  work related to semantic segmentation, correctly interpret its proposals, prune underper­ forming methods, and validate results.

A significant rise in the utilization of advanced deep learning technologies has recently  been observed within the field of semantic segmentation [36]. This advancement has led to  the adoption of an increasing array of techniques that harness this sophisticated technology  for aerial imagery [37], which clearly surpasses conventional methods in accuracy. The  difficulties associated with semantic segmentation in high-resolution (HR) remote sensing  (RS) images are well acknowledged, primarily arising from the limited availability of train­ ing samples and the likelihood of labeling errors. Currently, HR and very high-resolution  (VHR) RS images provide a considerable amount of information regarding various ground  objects, including roads, buildings, and vehicles [38]. The segmentation of objects with  varying semantic significance has become a primary focus for the RS community [39].  However, it is often noted that these objects are unevenly distributed within HR and VHR- RS images. Furthermore, there are occasions when the boundaries between different objects  overlap. The pursuit of achieving accurate semantic segmentation of HR or VHR-RS images  is additionally hindered by the challenges related to distinguishing the characteristics of cer­ tain smaller objects [40].

In recent years, significant advancements in deep learning (DL) have been observed  within the domain of computer vision. A crucial development was marked by the launch  of AlexNet in 2012, which illustrated the capability to autonomously extract deep features  from diverse images [41]. Subsequently, in 2015, Long et al. [42] introduced a fully con­ volutional network (FCN), specifically tailored for semantic image segmentation and rec­ ognized as an end-to-end architecture. An enhanced version of the FCN was later created  by Sheila et al. [43], which utilized ImageNet for weight learning, thereby considerably  decreasing the necessary training duration. Furthermore, Caesar et al. [44] investigated the  application of weak labels for training in scenarios where obtaining a substantial number of  artificial labels poses challenges. Building on these innovations, various FCN-based archi­ tectures, including U-Net, SegNet, and DeepLab, have progressively emerged [45–47]. The  efficacy and performance of this advanced technology have outstripped those of alternative  classifiers. Typically, a CNN is organized in layers, with the primary layers concentrating  on the extraction of high-level features, while the final layers are employed for tasks related  to regression or classification. Within the wide array of CNN architectures available, sev­ eral pre-trained models are particularly noteworthy, such as AlexNet [48], VGG-Net [49],  ResNet [50], Inceptionv3 [51], DenseNet [52], and GoogLeNet [53].

Recent research demonstrates that deep learning offers considerable benefits for the  semantic segmentation of images; however, it is heavily dependent on large datasets and  extended training periods. The accuracy of labeling is also of paramount importance. For  instance, the study cited in [54] indicates that significant errors in training can result from  inaccuracies in pixel labeling when manual annotations are utilized. Furthermore, findings  from [55] highlight the susceptibility of deep neural networks to various attacks, suggest­ ing that the inaccuracies introduced by human annotations can greatly affect the precision  of experimental outcomes. While each semantic segmentation network possesses its own  unique advantages regarding accuracy, training efficiency, and resilience, it is unlikely that  any single model will attain optimal performance in the field of remote sensing images,


## 1 3

213    Page 4 of 30

Multimedia Tools and Applications          (2026) 85:213

especially those defined by limited training datasets and imprecise labels. Given the distinc­ tive benefits provided by different models, the amalgamation of multiple methodologies  may represent a promising strategy to improve segmentation effectiveness.

While the semantic segmentation network has numerous benefits such as improved accu­ racy, resilience, and training efficiency, applying a single model to remote sensing images  with meager training data and ambiguous labels can result in subpar performance. Thus,  it becomes the interest, and the main ideal for research is always to develop a robust and  coherent algorithm, along with alternative methods, to address the challenges and prob­ lems of semantic segmentation. One possible way to improve the capability of segmenta­ tion is to combine different models, each with its own unique strengths. This methodology  is motivated by the observation that integrating several base-learners can yield superior  results compared to utilizing a singular segmentation model, as well as the fact that deep  learning models can exhibit varying performance levels based on their network architec­ tures. This study focuses on the development of an adaptively weighted ensemble that inte­ grates multiple CNNs to perform semantic segmentation on aerial images. The aim is to  leverage the advantages of different CNN architectures to achieve enhanced accuracy and  better generalization capabilities. To improve segmentation performance during the col­ lective training of the ensemble networks, a blend of model weights and sample weights  was employed. Unlike traditional ensemble methods, we propose a dynamic weighted  ensemble strategy that adjusts weights based on per-class performance during validation.  This enhances the robustness of segmentation results, especially for imbalanced classes.  Moreover, our ensemble strategically combines U-Net backbones like ResNet34, Incep­ tionV3, and VGG16 diverse feature extraction capabilities to improve generalization across  complex datasets. Our experiments with Aerial Imagery dataset demonstrate quantitative  and qualitative improvements. Compared with a standard U-Net, the performance of our  method is superior for tested dataset.

The primary contribution of this research is outlined below:

● Our proposed methodology advocates for a hybrid ensemble model that utilizes multi­ ple convolutional neural networks (CNNs) in order to perform semantic segmentation in  aerial imagery. The algorithm for ensemble weighting was utilized on three different U- Net models that had varying backbones, namely: ResNet34, InceptionV3, and VGG16. 	 ● The ensemble comprises several Unet models, with each variant trained using a unique  pre-trained network, and the predictions generated by these models were integrated via  a weighted averaging technique to facilitate multi-class semantic segmentation. 	 ● The performance of each model is forecasted using the Weighted Average Ensemble  (WAE) technique. This approach entails assigning weights to the trained models in or­ der to attain the highest level of accuracy in the results. 	 ● The optimization of weights for the hybrid ensemble model is achieved by employing  the grid search method.

The organization of the following sections of this article is as follows: Section 2 provides  a review of prior research concerning semantic segmentation and the assessment of aerial  imagery. An in-depth description of the proposed methodology is presented in Section 3.  Section 4 details the experiments conducted, accompanied by an analysis of the resulting


## 1 3

Page 5 of 30    213

Multimedia Tools and Applications          (2026) 85:213

findings. A comparison between the obtained results and those produced by current methods  is made in Section 5. Finally, Section 6 offers a summary to conclude the article.


## 2  Related work

Machine learning algorithms depend on feature learning; however, the labor-intensive man­ ual process can be circumvented through the use of deep learning algorithms. This meth­ odology is especially effective in addressing the rapid growth of data volumes. While deep  learning algorithms made their debut in the late 1980 s [56, 57], their widespread application  was hindered by the constraints of computing power and the scarcity of training data during  that period. Nevertheless, these algorithms have reemerged and achieved remarkable suc­ cess, notably triumphing in the ImageNet Challenge in recent years [58, 59].

Convolutional Neural Networks (CNNs) are an integral part of the domain of semantic  segmentation due to their ability to perform nonlinear decision functions and integrate the  process of learning features from images through successive application of convolutional  and pooling layers [60]. The contemporary semantic segmentation models, namely, U-Net  [61], PSP-Net [62], and DeepLab-V3+ [63], follow an encoder-decoder design; it performs  downsampling of extracted dense image features along with contextual information sup­ plied by an effective interpolating feature decoder pathway in an upsample-symmetry con­ figuration. In U-Net, skip connections are used for connecting feature mapss; both PSP-Net  and DeepLab-V3+ use a hierarchy or “pyramid” of spatial pooling to add extra context to  the final prediction. Yet another, the DeepLab-V3+ model combines even more compli­ cated convolutional features to enhance the retrieval of context information and still uphold  an equal number of trainable parameters to the previous version. Many academic works  have outlined several encoder networks, among which VGG-16 [64] and ResNet [36] have  proven to be extremely relevant. Even though these networks were originally constructed  for the classification of images, they work well as feature extractors for semantic segmen­ tation. Improvements in network performance can be achieved with increased depth (by  more layers), width (by larger spatial dimensions of the layers), or resolution (more channel  capacity per layer) of the various architectures and their iterations of which the performance  of all these variants is fundamentally different.

Recently, convolutional neural networks (CNNs) have found applications in the domain  of remote sensing [65]. These networks are capable of converting initial inputs into continu­ ous vectors for regression tasks or multiple binary labels for classification tasks through  an automated learning process that develops multi-level representations [66]. Gradually,  traditional manual feature creation in classification and recognition applications is being  replaced by CNNs, which exhibit strong capabilities in “representation learning.” The use  of CNNs for feature extraction greatly streamlines the design process and yields promis­ ing results [67]. Numerous effective CNN architectures, including ResNet, AlexNet [58],  GoogleNet [68], and VGGNet, are commonly employed for image classification and seg­ mentation. Although these architectures typically produce a single class label for image  classification, CNNs have been instrumental in achieving semantic segmentation of images.  The authors of [42] built upon the basic CNN framework to create a pixel-to-pixel con­ volutional network (FCN) aimed at dense prediction. In a standard configuration of Fully  Convolutional Networks (FCN), feature maps are downsampled using convolutions, fol­


## 1 3

213    Page 6 of 30

Multimedia Tools and Applications          (2026) 85:213

lowed by the restoration of low-resolution features to their original input dimensions via  transposed convolution [69]. The emergence of FCN has led to the creation of multiple  architectures, including U-Net, DeconvNet [70], and SegNet [71].

The domain of satellite data, being almost synonymous with satellite pictures, has seen  a notable upswing in deep learning, more precisely the Convolutional Neural Networks  or CNNs. The extraordinary breakthroughs brought about by deep learning in image clas­ sification have now found applicability in land cover classification and change detection  [72]. Scientific research fully relating to semantic segmentation in both aerial and satellite  imagery goes back three decades [73]. For example, a model that can be used for binary  building segmentation by marking building boundaries on aerial images has been proposed  by Zhang et al. in [74]. More fully CNN-based techniques have also been presented for road  extraction from satellite aerial images [75]. Most of the proposed designs aimed to tackle  the aerial image segmentation challenge, with a major focus on the subproblems related  to the segmentation of aerial photographs. These frameworks use a holistic convolutional  structure that has two main building blocks: background information is first extracted and  then upscale it, whereby the already collected feature array now is made to match the size  of the initial input image dimensions [76–78].

For a comprehensive overview and in-depth understanding of the application of deep  learning in field of remote sensing tasks, those interested may refer to sources [36, 79]. This  domain typically involves tasks such as the identification of road networks [80, 81] and  building footprints [82], achieved through the use of semantic segmentation networks. These  networks have gained significant traction due to their participation in prestigious competi­ tions like DeepGlobe [83] and SpaceNet [77]. The predominant architecture employed for  semantic segmentation is the encoder-decoder model, which was brought to prominence by  U-Net. The encoder consists of multiple blocks that process an input image or feature map,  producing a sequence of downsampled feature maps while progressively discerning higher- level features. Both the encoder and decoder networks share a similar structural design. The  decoder network works to incrementally enhance the resolution of the encoder’s output by  performing upsampling. To recover the intricate details lost during downsampling, each  block in the decoder is connected to its corresponding block in the encoder via skip con­ nections. Typically, upsampling is executed using transposed convolutions, which feature  adjustable weights.

Recent advancements in aerial image segmentation have leveraged U-Net architectures  to enhance performance across various remote sensing tasks. For instance, Khan et al. [84]  introduced a U-Net model augmented with self-attention mechanisms and separable con­ volutions, achieving a significant accuracy improvement over previous models in urban  scene segmentation. Similarly, Ramos and Sappa [85] enhanced U-Net by integrating  SK-ResNeXt as the encoder, enabling better multi-scale feature extraction for land cover  classification using multispectral imagery. Other notable contributions include the devel­ opment of the AER U-Net architecture, which incorporates residual blocks, self-attention  mechanisms, and dropout layers to improve segmentation accuracy and generalization  capability. Additionally, Dimitrovski et al. [86] proposed an ensemble approach combining  multiple U-Net models with different backbone networks, demonstrating state-of-the-art  performance on several remote sensing datasets. These studies underscore the versatility  and effectiveness of U-Net-based models in aerial image segmentation, particularly when  enhanced with advanced architectural elements and ensemble strategies.


## 1 3

Page 7 of 30    213

Multimedia Tools and Applications          (2026) 85:213


## 3  Materials and methods

The development of CNNs draws expertise from different fields such as biology, mathemat­ ics, computer science, etc. and is arguably one of the most revolutionary and transformative  progressions in the entire field of computer vision. CNNs are meant to compute a systematic  transformation of the input signal and thereby engender the learning of hierarchical features  creating a derivation of representations [87]. Virtually every modern deep learning frame­ work designed for tasks like object detection, image classification, and semantic segmen­ tation uses strong convolutional backbones as feature extractors. These key architectural  elements essentially comprise a series of alternatively stacked convolutional and pooling  layers that enable the formation of features over multiple, systematically finer scales. In the  present work, three different backbones, VGG16, ResNet34, and InceptionV3, are experi­ mented with as encoding paths of the U-Nets, respectively [51].


### 3.1  U-net semantic model

The U-Net model has demonstrated its utility across a range of applications that require  semantic segmentation. One of its most effective applications lies in biomedical image seg­ mentation, a concept initially introduced by Ronneberger et al. [61], and recognized for  its distinctive “U” architecture. It has two main parts: encoding and decoding. It takes the  task of the first to extract high-dimensional features of input data and the second to recover  positional information. By unifying both encoding and decoding processes, the model can  aggregate both contextual and spatial information about objects and thus enables semantic  segmentation. The stages of encoding are five, each containing two 3 × 3 convolutional lay­ ers matched with a 2 × 2 pooling layer, shown on the left side of Fig. 1. There are five stages  to the decoding phase, the first four of which have two 3 × 3 convolutional layers and a  2 × 2 upsampling layer while all five finally have a 1 × 1 unfolding operation together with a  softmax classifier for making predictions. This kind of architecture U-Net has been verified  in many other tasks as well which further has led it to be widely adopted in most multiple  medical image segmentation assignments. The architecture of U-Net is widely preferred  for image segmentation endeavors due to the numerous advantages it provides, including:

● The network’s U-molded structure is proposed to support the transfer of setting infor­ mation from the unraveling way while keeping well-exact spatial subtleties from the  encoding way. This new design helps a lot in the network’s ability to achieve thorough  and accurate segmentations. 	 ● It can make sharp segmentations with small details when the high-resolution features  from the top path can mix with the low-resolution features from the bottom path. This  will let us have high-resolution feature maps made. 	 ● Optimal utilization of parameters: When compared to other methods in the realm of  deep learning, the effective use of models, U-Net adopts a more restricted parameter  count, leading to improved computational efficiency. This allows for training with  smaller datasets. 	 ● The U-Net algorithm excels in performing image segmentation tasks that require the  identification of small objects, especially within the realm of medical imaging. Its profi­ ciency stems from the capability to utilize data across various resolution levels, enabling


## 1 3

213    Page 8 of 30

Multimedia Tools and Applications          (2026) 85:213

Fig. 1  Illustration of the U-Net architecture

it to precisely and accurately identify and isolate these small entities. 	 ● The U-Net has undergone extensive training on a diverse array of medical image data­ sets, demonstrating a remarkable adaptability to new datasets that encompass various  imaging modalities or object types. This transferability stands out as one of its most  significant strengths.


### 3.2  Convolutional encoder-decoder network

The semantics of an image can be partitioned by a convolutional encoder-decoder network  [71]. The greater the depth in the hierarchy of networks, the encoder, the better the high- level features. Due to the large receptive field resulting from the depth in which features are  learned by the encoder, the network’s performance can be greatly enhanced. Meanwhile, the  decoder creates feature maps that enhance in resolution through up-sampling. To enhance  the accuracy of semantic segmentation, various techniques have been incorporated into con­ volutional neural networks, including the implementation of skip and recurrent connections,  as well as the use of larger convolutional kernels, as detailed in [88]. The best current prac­ tice for fine-tuning CNN models is through transfer learning. In other words, existing CNN  models are already optimized and will be re-optimized to be used in the same application.  Therefore, as the current practice of transfer learning, re-optimization of CNN models is  highly effective. This is what makes transfer learning so exciting between the fine-tuning of  CNN models. Consequently, that is also why training a neural network from the beginning  is typically done with much difficulty. Again, that is also where transfer learning, especially  fine-tuning a CNN, facilitates reusing weights and overcomes initialization. Among several  modern cutting-edge designs for convolutional neural networks, we chose VGG16 [64],


## 1 3

Page 9 of 30    213

Multimedia Tools and Applications          (2026) 85:213

ResNet34, and InceptionV3 [51] because of their latest improvements and because they  worked great on the ImageNet dataset [59].


### 3.2.1  VGG16

In the year 2014, In the ImageNet image classification competition, VGGNet secured the  second position. VGG16 is widely regarded as one of the most superior classification net­ works within the VGGNet framework. The VGG16 network is comprised of six distinct  segments: five of which are dedicated to convolution, and one to fully connected layers. The  VGG16 network possesses precisely 16 layers, consisting of five segments of convolutional  layers, which include 13 unique convolutional layers. The fully connected segment, which  refers to the network’s final three layers, is also present. The 16 layers in total are the result  of the summation of all 13 convolutional layers and 3 fully connected layers.

The process of extracting the image features for low, medium, and high winter layers is  accomplished using a 5-segment convolution process, where each segment is made up of 2  or 3 convolutional layers. To prevent overfitting, enhance the speed of network training, and  ensure that the gradient doesn’t vanish, the ReLU activation function is utilized following  the winter convolution. To decrease parameters, produce better nonlinear effects, and effec­ tively capture details, the 3 × 3 coupon kernel is used for each convolutional layer. In place  of larger kernels such as 5 × 5 and 7 × 7, stacking 3 × 3 convolutional kernels can lead to a  more concise network terminal structure. Connecting to the tail of the 5-segment convolu­ tion is the top pooling layer, which makes use of 2 × 2 pooling cores. This connection works  to decrease the potential mean deviation that may stem from an error in the convolutional  layer’s parameters. As a result, it becomes simpler to detect variations in both gradients and  images, which is an advantage when it comes to safeguarding intricate details such as tex­ tures. The final segment of the VGG16 network is comprised of three fully connected layers,  where each node in a given layer is interconnected with all nodes in the preceding layer.  This configuration facilitates the aggregation of output features derived from the prior layer.

In brief, the VGG16 architecture comprises a total of 16 layers. This sprawling network  employs a strategy of layer-by-layer learning, gradually identifying the traits of each layer,  ranging from those at the lowest level to those at the highest level. This results in a greater  capacity for nonlinear expression, allowing for more diverse features to be expressed and  more intricate input features to be accommodated. In addition, in the VGG16 network, there  is a provision for 64 3 × 3-sized initial convolutional kernels, which further increases in  quantity. As the network goes deeper, the number of convolutional kernels widens starting  from 64 to 128, then to 256, and finally to 512. Wider networks can learn increasingly com­ plex functions, thus providing the ability for each subsequent layer to capture more intricate  visual details.


### 3.2.2  ResNet34

The major problem in backpropagation, especially with more convolutional layers, is van­ ishing gradient. The current paper investigates the advancement introduced by He et al.,  known as ResNet, which is a deep residual network characterized by shortcut connections.  These connections facilitate the addition of the input x to the output following several con­ volutional layers, thereby effectively mitigating the vanishing gradient issue. The encoders


## 1 3

213    Page 10 of 30

Multimedia Tools and Applications          (2026) 85:213

utilized in this research were structured on ResNet34, which comprises a 7 × 7–64 layer, a  max-pooling layer of 3 × 3 with a stride of 2, and 16 residual blocks.


### 3.2.3  InceptionV3

InceptionV3 represents an architecture within the inception family of convolutional neural  networks [51, 89, 90]. The creators of InceptionV3 favor the use of factorized small and  imbalanced convolutions to reduce both the number of trainable parameters and the corre­ sponding computational power required. Currently, InceptionV3 comprises a total of eleven  inception modules, including five from the A family, four from the B family, and two from  the C family. Additional information concerning these inception modules is available in the  existing literature [51].


## 4  Proposed hybrid ensemble model

The subsequent section provides a comprehensive exploration of the different stages within  the proposed framework. To illustrate the progression of our recommended semantic seg­ mentation approach for aerial image segmentation, which employs a weighted average  ensemble model, a diagram depicting the procedure is presented in Fig. 2. The workflow  begins with data collection and loading. To enhance the dataset, various augmentation strat­ egies are applied, as deep learning models generally perform better with larger amounts  of training data. Afterward, the preprocessing stage concludes by dividing the dataset into  training, validation, and testing subsets. Pre-trained deep neural networks are then employed  on the training and validation sets, with fine-tuning performed to adapt the models to the  specific task. The outputs of these pre-trained networks constitute the first phase of the pro­ posed method. In the second phase, the models serve as base learners within an ensemble  learning framework. By combining their outputs through a weighted averaging strategy, the  ensemble produces the final segmentation results on the test data.


### 4.1  Input dataset

The dataset used in this research originates from the Mohammed Bin Rashid Space Centre  (MBRSC) and contains 72 high-resolution aerial images of Dubai. Each image has been

Fig. 2  Dataset semantic segmentation of aerial imagery


## 1 3

Page 11 of 30    213

Multimedia Tools and Applications          (2026) 85:213

pixel-wise annotated into six semantic classes: Building, Land, Road, Vegetation, Water, and  Unlabeled (the latter reserved for uncertain or unclassified areas). To streamline processing,  the images are grouped into eight large tiles. This dataset is highly valuable for developing  and validating semantic segmentation models in urban environments. Its annotations enable  in-depth analysis of Dubai’s urban structure, including buildings, road networks, vegetation,  and water regions. Such information supports applications in urban planning, infrastructure  management, and environmental monitoring. Owing to its spatial resolution and semantic  richness, the dataset has become an important benchmark in remote sensing and urban stud­ ies. The dataset is openly accessible via Kaggle, and an example image with its mask is  shown in Fig. 2.


### 4.2  Dataset pre-processing

After acquiring the dataset, the first step was data augmentation to expand the number  of satellite images available for training pre-trained models. Data augmentation is a pre- processing strategy that enhances dataset diversity by generating modified versions of the  original images while preserving their class labels. The dataset of 72 satellite images was  split into 56 training (~78%) and 16 validation (~22%) images and resized to a consistent  resolution. To increase dataset diversity and reduce overfitting, the training set was aug­ mented approximately ninefold using techniques such as cropping, flips, rotations, bright­ ness/contrast adjustments, CLAHE, grid distortion, and optical distortion, resulting in a  total of 504 training images. Figure 3 shows some sample augmented images and masks  from the dataset.


### 4.3  Base-learner construction

Training models that have a substantial number of parameters necessitates an extensive col­ lection of images for effective training. When utilizing a limited dataset, there exists a risk

Fig. 3  Preprocessed images after data augmentation


## 1 3

213    Page 12 of 30

Multimedia Tools and Applications          (2026) 85:213

of overfitting the model. To overcome this, researchers employ transfer learning techniques  to enhance their model training. Transfer learning involves adjusting a pre-trained neural  network for application to another dataset by leveraging its acquired features. Here, the  encoder was initialized with pre-trained weights obtained from the.

ImageNet database and then trained on our specific datasets. The advantages of using uti­ lizing pre-trained networks offers the advantage of an existing comprehensive understand­ ing of images, which encompasses information related to edges, textures, and shapes that  can be effectively utilized in image segmentation. Although training Unet from the ground  up on the ImageNet database is feasible, the considerable size of this dataset, compris­ ing over 14 million images, presents significant challenges. Although it is feasible to train  U-Net from the ground up using the ImageNet database, the dataset’s considerable size,  comprising over 14 million images, presents a significant challenge. Therefore, to optimize  costs, the use of pre-trained networks is strongly advised. To improve cost efficiency, the  use of pre-trained networks is strongly advised. Our research identified three pre-trained  networks that are regarded as leaders in the field. For the dataset, we substituted the encoder  of the U-Net model with one of the chosen pre-trained networks, resulting in the formation  of three unique base-learners. For an ensemble model to exceed the performance of the  individual base-learners, it is essential that these base-learners exhibit both accuracy and  diversity in their capacity to capture the fundamental structure of the data. Each pre-trained  network offers distinct characteristics and learning methodologies that enhance the perfor­ mance of the base-learners within the ensemble. Moreover, it is imperative to meticulously  choose the suitable pre-trained networks for our ensemble model. In our research, we have  chosen these three pre-trained networks based on three primary criteria. To qualify, net­ works must satisfy three significant conditions. Firstly, they should demonstrate a proven  history of consistently achieving peak performance. The second criterion requires that the  networks be architecturally distinct from one another. Lastly, a limited number of param­ eters is necessary for the networks to be considered. While the first criterion is straightfor­ ward, the second holds particular significance for the development of a diverse ensemble.  This results from the fact that different base learners possess varying properties and learning  paradigms. An ensemble that is diverse enhances the model’s capacity for learning while  simultaneously decreasing both variance and bias. A more comprehensive examination is  required for the final criterion regarding the network’s parameters.

Initially, three individual base learners, which constitute the ensemble, were trained  to form a weighted average ensemble. These base learners were constructed utilizing the  U-Net architecture. In this study, pre-trained models VGG-16, ResNet34, and Inception  V3 were utilized for the purpose of multi-class classification. The predictions generated by  these models were subsequently combined using a weighted average approach to yield the  final classification results.


### 4.4  Hybrid ensemble formulation using the weighted average ensemble method

In our experiments, the proposed ensemble approach was applied to segment aerial images  into five categories: buildings, land, roads, vegetation, and water. For the ensemble, we  selected the three base learners that demonstrated the strongest individual performance,  while weaker learners were excluded to avoid unnecessary computational overhead and  reduced efficiency (see Fig. 4).


## 1 3

Page 13 of 30    213

Multimedia Tools and Applications          (2026) 85:213

Fig. 4  Overall framework for the proposed ensemble algorithm follows a weighted framework, which  is composed of two main components. The first component involves the forward propagation process,  where images are entered into three distinct U-Net networks that utilize ResNet34, Inception V3, and  VGG16 backbones. The second component of the ensemble algorithm involves integrating the output  feature maps of these networks through an average weighting strategy. The backbones of ResNet34,  Inception V3, and VGG16 utilized in the ensemble algorithm are architecturally distinct from each other


## 1 3

213    Page 14 of 30

Multimedia Tools and Applications          (2026) 85:213


## Architectures of three backbones

ResNet34

Incepon V3

VGG16


> **Figure 4  (continued)**

Most of the time, a single model is used by research to generate classification results.  Though, it has been proved that the ensemble model can outperform the single model [91].  This is because a single model is unable to extract all of the features from a given dataset.  Consequently, researchers employ a variety of models to enhance performance. To create a  weighted average ensemble, predictive base learners are integrated, with each base learner’s  terminal prediction contribution being weighted according to its effectiveness. The inclu­ sion of base learners that perform poorly leads to unnecessary expenditure of computational  resources and time. For the weighted average ensemble method, selecting the appropri­ ate ensemble for each member poses a significant challenge. What is put forward here is  an improvement upon the average ensemble methodology where all the models contribute  equally to the predictive process. In the weighted average ensemble method, to each model a  weight is assigned, these values go from 0.0 to 1.0 with an increment of 0.01. The goal is to  identify the optimal weight combination for each model, which presents its own difficulties.  In this study, the grid search technique is utilized to optimize the weights for each model,  as demonstrated in Fig. 5. A key challenge in employing a weighted ensemble is determin­


## 1 3

Page 15 of 30    213

Multimedia Tools and Applications          (2026) 85:213

Fig. 5  The method of grid searching for identifying the most optimal combination of weights

ing the relative contribution of each model. To address this, we performed a grid search  is conducted to ascertain approximate weights for each member of the ensemble. In this  framework, learners with lower performance are assigned reduced weight, whereas those  that demonstrate higher success are allocated greater weight. Consequently, this mecha­ nism enhances the performance of the learners, allowing them to mutually benefit from  one another, which results in outcomes that surpass those achieved by other ensembles  or individual base learners. Each base learner generates a prediction, with corresponding  adjustments made to the weights. The outputs of the individual models are combined into a  weighted average ensemble. The weights are optimized via a randomized search using the  Dirichlet distribution on the validation set. The ensemble prediction is calculated as:

N ∑

N ∑

ˆyensemble =

wiˆyi with

wi = 1 (1)

i=1

i=1

where wi is the weight of the i-th model, ˆyi is its prediction, and N is the number of models.

The effectiveness of the ensemble was evaluated on test images, with the original U-Net  serving as the baseline for comparison.

Algorithm 1 displays the experimental arrangement that was utilized for the study.


## 1 3

213    Page 16 of 30

Multimedia Tools and Applications          (2026) 85:213

Algorithm 1: The experimental setup used for the proposed hybrid ensemble using the  WAE model.


### 4.5  Evaluation metrics

The success of the CNN model in segmentation is the degree of similarity or dissimilar­ ity between the regions as predicted by the model and the actual regions in the image. We  used several metrics to quantitatively evaluate the segmentation technique, such as overall  accuracy (OA), precision, recall, and Intersection of Union (IoU)/(Jaccard Coefficient). The  Dice and Jaccard coefficients have become somewhat of a tradition in image segmentation  because they tend to handle very well the class imbalance. The accuracy, and precision were  calculated based on true positives (TP), false positives (FP), and false negatives (FN).

● Overall accuracy (OA) predicted pixels in all test sets divided by the number of pixels  in the image is defined as follows:

Accuracy = TP + TN TP + TN + FP + FN (2)

● Precision: refers to the ratio of true positive data to the total number of data points clas­ sified as positive. The calculation of this ratio involves the application of the equation:


## 1 3

Page 17 of 30    213

Multimedia Tools and Applications          (2026) 85:213

Precision = (TP) (TP) + (FP) (3)

● Recall: is defined as the ratio of accurately identified positive data to the sum of the  accurately identified positive and negative data. It is calculated using the following for­ mula:

Recall = (TP) (TP) + (FN) (4)

● The Jaccard index: also known as the “ Jaccard similarity coefficient “ and occasion­ ally informally indicated as “IOU”, which stands for Intersection over Union, serves as  a metric for assessing the similarity or overlap between two sets. Initially designated as  “the coefficient of coincidence” by Grove Karl Gilbert” [92], it was subsequently redis­ covered by him [93]. This coefficient evaluates the similarity between two finite sam­ pled sets by determining the ratio of the size of their intersection to that of their union.

Jaccard index (A, B) = |A ∩B| (|A| + |B|) −|A ∪B| (5)

J (A, B) = (precision ∗recall) ((precision + recall) −(precision ∗recall))

In this particular context, the letters A and B are utilized as an abbreviation to represent  respectively the pixels located in the ground truth and the predicted output.

● The Dice Coefficient, more formally known as the F1-score, was independently created  by Thorvald-Sørensen [94] and Lee-Raymond Dice [95]. This metric, often termed the  Sørensen-Dice coefficient, serves to determine the similarity between two samples. The  calculation is performed using the following mathematical formula:

D (A, B) = 2 (|A ∩B|)

(|A| + |B|) (6)

D (A, B) = 2 ∗(precision ∗recall)

(precision + recall)

Both of these measurements are evaluated on a scale ranging from 0 to 1. A measurement  of 0 means that there is no intersection between the segments, whereas a measurement of 1  signifies that the segmentation is perfect and flawless.


## 1 3

213    Page 18 of 30

Multimedia Tools and Applications          (2026) 85:213

● The categorical cross-entropy: the loss function is a key measure that quantifies the  difference between the predicted outputs and the true labels. In image processing tasks,  it compares the network’s predictions against the ground truth. In this study, categorical  cross-entropy is employed as the loss function, and its computation is defined in Eq. (7):

output size ∑

yi logˆyi (7)

loss =

i=1


## 5  Experimental results and discussions

This section primarily addresses the results obtained from a conducted study. The research  focused on the evaluation of three advanced models VGG-16, ResNet34, and Inception V3,  each assessed individually for multi-classification tasks. Subsequently, these three models  were integrated and enhanced through the weighted average technique to improve their  performance. The models were built using Keras with TensorFlow as the backend. Keras is  an open-source, user-friendly framework for designing neural networks efficiently. Training  was conducted with a batch size of 1- over 50 epochs, where the batch size controls how  many samples are processed before updating the model’s weights, and epochs denote the  total passes over the dataset. The learning rate, set to 0.0001, regulates the speed of weight  updates, balancing convergence speed and stability. The Adam optimizer was used for train­ ing, and all convolutional layers employed the ReLU activation function, and the ensemble  weights were initialized equally with values of 0.1666 for each contributing model. Table 1  lists the key hyperparameters used for fine-tuning all pre-trained models in this study. Each  model was adapted according to these settings, and the resulting trained weights were saved  for subsequent use in the ensemble learning stage. To apply transfer learning, the parameters  specified in Table 1 were employed when integrating the pre-trained models from the Keras  applications library. Originally trained on ImageNet with 1000 output classes, the models’  final classification layers were modified: a GlobalAveragePooling layer was applied, fol­ lowed by an output layer with 6 classes corresponding to Building, Land, Road, Vegetation,  Water, and Unlabeled. During training, an early stopping callback monitoring the loss was  used to prevent overfitting. All experiments were conducted in Python using the Google  Colab environment, which supports online machine learning and deep learning workflows.  The analysis utilized TensorFlow 2.19.0, Keras 3.10.0, Matplotlib 3.10.0, and scikit-learn  1.6.1. The system ran on a GPU with CUDA 12.4 and NVIDIA driver 550.54.15. The proposed weighted average ensemble demonstrates superior performance compared  to benchmark models such as FCN, standard U-Net, and the individual backbone-based


> **Table 1  Fine-Tuning of**

> hyperparameters

NO Parameter Values 1 Optimizer Adam 2 Learning rate 0.01 to min 0.0000001 3 Loss function categorical_crossentropy 4 Metrics accuracy, dice_coeficient, IoU, precision, recall 5 Batch size 16 6 Epochs 50 7 Patience 10


## 1 3

Page 19 of 30    213

Multimedia Tools and Applications          (2026) 85:213


> **Table 2  Segmentation performance comparison between our proposed WAE and others methods**

> Model
Accuracy
Validation 
Accuracy

Valida­ tion Dice  coefficient FCN 57.57% 71.69% 79.32% 79.56% 35.97% 44.99% 50.55% 59.64% Unet 63.26% 71.82% 95.13% 96.33% 43.89% 47.11% 59.28% 61.98% Unet-  Incep­ tionV3

Loss Valida­ tion  Loss

IoU Valida­ tion  IoU

Dice  coefficient

81.76% 83.86% 20.67% 52.29% 66.99% 64.17% 79.52% 77.43%

Unet- Resnet34

80.62% 83.29% 21.06% 53.96% 66.96% 64.32% 79.50% 77.57%

Unet- VGG16

80.56% 84.72% 25.70% 50.34% 62.05% 62.58% 75.85% 76.27%

HRNet 69.17% 80.43% 52.73% 57.71% 46.77% 54.33% 62.74% 69.12% Deep­ lav3+

80.57% 83.06% 15.03% 52.23% 70.42% 66.03% 81.81% 78.81%

87.08% 86.48% 07.34% 50.08% 78.13% 72.79% 87.06% 83.79%

Proposed  WAE

U-Nets (InceptionV3, VGG16, ResNet34), as well as more advanced segmentation mod­ els like DeepLabV3+ and HRNet [96]. As shown in Table 2, our approach achieves the  highest scores in accuracy (87.08%), IoU (78.13%), and Dice coefficient (87.06%). This  improvement can be attributed to the ensemble’s robustness, which enhances segmenta­ tion precision and stability over traditional architectures. The model effectively generates  pixel-wise predictions for each semantic class Building, Land, Road, Vegetation, Water, and  Unlabeled—capturing complex patterns within aerial images. Visualization of the predicted  masks alongside the original images highlights the ensemble’s ability to recognize fine- grained details and accurately label diverse regions. These results demonstrate the model’s  practical value and potential for applications such as urban planning, environmental moni­ toring, and infrastructure assessment, confirming its readiness for real-world deployment.

To assess the effectiveness of our Aerial Image Segmentation method, a visual analysis  of the anticipated segmentation masks was performed on newly generated images produced


> **Table 3  Quantitative Compari­**

> son of satellite image segmenta­
tion studies

Reference Dataset Model Jaccard  index  (IoU)%

Dice  coeffi­ cient% [97] Massachusetts GMEDN 70.39 – FCN 66.50 – SegNet 63.43 – UNetPPL 65.65 – [98] Carvana U-Net – 68.70 [99] Inria SegNet 70.14 – [100] GPCV U-Net 70.27 87.13 Our study MBRSC Weighted  average  ensemble- based  UNet CNN  model

78.13 87.06


## 1 3

213    Page 20 of 30

Multimedia Tools and Applications          (2026) 85:213

Fig. 6  Overall semantic segmentation results by different methods of the state-of-the-art mechanisms for  MBRSC Dataset

by our proposed weighted ensemble approach. This evaluation was conducted in conjunc­ tion with three distinct transfer learning models: VGG16, ResNet34, and InceptionV3,  which served as the backbone for the U-Net architecture. The findings illustrated in Fig. 6  further validate the efficacy of our weighted average ensemble in capturing complex spatial


## 1 3

Page 21 of 30    213

Multimedia Tools and Applications          (2026) 85:213

patterns within Dubai’s aerial imagery. Moreover, the implementation of pixel-wise seman­ tic segmentation enabled the model to accurately define the boundaries among various land  classes, thus improving its overall reliability and precision. Such capability is crucial for  applications including urban planning, environmental monitoring, and infrastructure devel­ opment in Dubai and similar urban environments. Furthermore, the segmentation contours  produced by our approach closely resemble the manually annotated images and exceed the  segmentation quality achieved by the other three methods. As a result, the findings suggest  that the ensemble model outperforms the individual models.

The performance of both the proposed model and the transfer learning models was  assessed using metrics such as accuracy, loss, Dice coefficient, and IoU. The loss curves for  training and validation, shown in Fig. 7, indicate that the transfer learning models exhibit  similar behavior. While their performance trends closely resemble each other, the weighted  average ensemble demonstrates superior results. Specifically, the proposed ensemble  achieved the highest accuracy, IoU, and Dice coefficient, while also showing lower loss  compared to the Unet models built with VGG16, ResNet34, and InceptionV3 backbones.

The experimental results demonstrate that the proposed weighted ensemble model  outperforms individual backbone-based U-Nets (InceptionV3, ResNet34, VGG16), stan­ dard U-Net, and advanced segmentation architectures such as FCN-8 s, HRNet, and Dee­

Fig. 7  illustrates the accuracy, loss, IoU score, and dice coefficient curves of the CNN models across each  epoch throughout both the training and validation phases


## 1 3

213    Page 22 of 30

Multimedia Tools and Applications          (2026) 85:213

pLabV3+, Across multiple metrics, including accuracy, Dice coefficient, IoU, precision,  and recall, he proposed weighted average ensemble achieved the best performance with an  accuracy of 87.08%, Dice coefficient of 87.06%, IoU of 78.13%, precision of 81.70%, and  recall of 94.39%, demonstrating superior segmentation capability. Among the individual  backbone models, InceptionV3 achieved 81.76% accuracy, 79.52% Dice, and 66.99% IoU,  while ResNet34 reached 80.62% accuracy, 79.50% Dice, and 66.96% IoU. VGG16 obtained  80.56% accuracy, 75.85% Dice, and 62.05% IoU. Standard U-Net achieved lower results,  with 63.26% accuracy, 59.28% Dice, and 43.89% IoU, and FCN-8  s recorded 57.57%  accuracy, 50.55% Dice, and 35.97% IoU. HRNet and DeepLabV3+ showed competitive  results, with HRNet reaching 69.17% accuracy, 62.74% Dice, 46.77% IoU, and Deep­ LabV3+ achieving 80.57% accuracy, 81.81% Dice, and 70.42% IoU. Overall, the ensemble  consistently outperformed all individual models and advanced architectures, validating its  robustness and effectiveness for pixel-wise semantic segmentation in aerial imagery. Fig­ ure 8 shows the comparaison of model metrics in a graphical form. The Weighted Ensemble  dominates across all metrics, achieving the highest Accuracy (~87%), Dice (~87%), IoU  (~78%), Precision (~82%), and Recall (~94%). DeepLabV3+ and HRNet show strong per­ formance but still slightly underperform the weighted ensemble. This confirms that combin­ ing the individual models (InceptionV3, ResNet34, VGG16) with learned weights improves  robustness and predictive power compared to standalone models. The graph demonstrates  its superior robustness, segmentation accuracy, and reliability, making it the preferred  choice for semantic segmentation on aerial images.

To further evaluate the classification performance of the models, confusion matrices were  generated for U-Net with InceptionV3, ResNet34, and VGG16 backbones, as well as for the  proposed weighted ensemble model. These matrices provide a detailed, class-wise view  of the models’ predictions against the ground truth, highlighting the strengths and weak­ nesses in segmenting each semantic category—Building, Land, Road, Vegetation, Water,  and Unlabeled. The confusion matrices demonstrate that while individual U-Net variants  achieve reasonable accuracy, the weighted ensemble consistently reduces misclassifica­ tions across all classes, confirming its improved robustness and effectiveness for multi-class  semantic segmentation tasks. Figure 9 present the Confusion matrices of Unet-Inceptionv3,  Unet-Resnet34, Unet-VGG1–16, and weighted ensemble models.

Fig. 8  Comparative Analysis of evaluation metrics for different methods


## 1 3

Page 23 of 30    213

Multimedia Tools and Applications          (2026) 85:213

Fig. 9  Confusion matrices of Unet-Inceptionv3, Unet-Resnet34, Unet-VGG1–16, and weighted ensemble  models

Additionally, to further test how well our new way works, Fig. 10 illustrates the segmen­ tation performance of the evaluated models. The figure shows the original input images,  corresponding ground truth masks, and predictions from the standard U-Net, U-Nets with  three different backbones, FCN, DeepLabV3+, HRNet, and the proposed weighted aver­ age ensemble. The ensemble model consistently produced accurate pixel-wise segmentation  across all classes—Building, Land, Road, Vegetation, Water, and Unlabeled. Visual com­ parison demonstrates that the ensemble preserves fine structures and complex patterns more  effectively than individual models. These results highlight the robustness and reliability of  the proposed ensemble approach, confirming its suitability for practical applications such as  urban planning and environmental monitoring.

Unlike conventional ensemble strategies such as Softmax averaging or Bayesian averag­ ing, our approach assigns optimized weights to each backbone based on validation perfor­ mance using a grid search. This ensures that models contributing more to overall accuracy  have a proportionally greater influence on the final prediction. By combining three com­ plementary U-Net backbones ResNet34, InceptionV3, and VGG16 our ensemble captures  diverse feature representations, including residual learning, multi-scale feature extraction,  and deep hierarchical features. Empirical results demonstrate that this weighted ensemble  consistently outperforms individual backbones and equal-weight ensembles across multiple


## 1 3

213    Page 24 of 30

Multimedia Tools and Applications          (2026) 85:213

Fig. 10  Enlarged visualization of results obtained from different methods. It is not possible to make a  logical comparison due to the fact that the experimental studies were carried out on diverse satellite image  data sets and different metrics were employed in the literature. Nevertheless, Table 3 presents a brief  overview of the numerical outcomes attained from analogous studies. It is noteworthy that the weighted  average ensemble that has been suggested has achieved the greatest IOU at an impressive rate of 78.13%


## 1 3

Page 25 of 30    213

Multimedia Tools and Applications          (2026) 85:213


> **Figure 10  (continued)**

metrics, including accuracy, Dice coefficient, and Jaccard Index, confirming both its meth­ odological novelty and practical effectiveness.


## 6  Conclusion

This study presents a weighted ensemble strategy for semantic segmentation that integrates  U-Net architectures with ResNet34, InceptionV3, and VGG16 encoders. Each base model  is independently fine-tuned, and their outputs are combined via a weighted average, with  weights optimized using a random search approach. The ensemble leverages depth-wise  separable convolutions to improve efficiency while maintaining high accuracy. Comparative  evaluation shows that the proposed ensemble consistently outperforms individual models,  including the standard U-Net, U-Nets with the three different backbones, FCN, DeepLabV3+,  and HRNet. The efficacy of the proposed architecture was thoroughly demonstrated using  the MBRSC aerial imagery dataset. On this dataset, the ensemble achieves an accuracy of  87.08%, Dice coefficient of 87.06%, Jaccard Index (IoU) of 78.13%, precision of 83.79%,  and recall of 83.79%, surpassing the performance of all benchmark models. These results  highlight the ensemble’s robustness in segmenting complex visual patterns and its effective­ ness for remote sensing applications. Future work will extend the evaluation to multiple pub­ licly available datasets to further validate the model’s generalizability and practical utility.


## 1 3

213    Page 26 of 30

Multimedia Tools and Applications          (2026) 85:213

Authors’ contributions  FASKA Zahra as a corresponding author proposed the idea of the paper and wrote  the manuscript. FASKA Zahra, KHRISSI Lahbib, HADDOUCH Khalid, and EL AKKAD Nabil modeled the  system under Python software. FASKA et al. contributed to reviewing the paper and have directly partici­ pated in the planning, execution and analysis of this study. All authors read and approved the final manuscript.

Funding  The authors declare that they have no funding for the research.

Data Availability  The MBRSC dataset is accessible to the public on a specialized Kaggle page (​h​t​t​p​s​:​/​/​w​w​w​.​ k​a​g​g​l​e​.​c​o​m​/​d​a​t​a​s​e​t​s​/​h​u​m​a​n​s​i​n​t​h​e​l​o​o​p​/​s​e​m​a​n​t​i​c​-​s​e​g​m​e​n​t​a​t​i​o​n​-​o​f​-​a​e​r​i​a​l​-​i​m​a​g​e​r​y​/​d​a​t​a).

Declarations

Ethics approval and consent to participate  This research does not contain any studies with human participa­ tions or animals performed by any of the authors.

Consent for publication  Not applicable.

Competing interests  The authors declare that they have no known competing financial interests or personal  relationships that could have appeared to influence the work reported in this paper.


## References

1.	 Khrissi L, El Akkad N, Satori H, Satori K (2022) Clustering method and sine cosine algorithm for image  segmentation. Evol Intell 15:669–682. https://doi.org/10.1007/s12065-020-00544-z 2.	 Khrissi L, Satori H, Satori K, El Akkad N (2021) An efficient image clustering technique based on fuzzy  C-means and cuckoo search algorithm. Int J Adv Comput Sci Appl 12(6):423–432. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​.​1​ 4​5​6​9​/​i​j​a​c​s​a​.​2​0​2​1​.​0​1​2​0​6​4​7​ 3.	 Faska Z, Khrissi L, Haddouch K et al (2023) A robust and consistent stack generalized ensemble-learning  framework for image segmentation. J Eng Appl Sci 70:74. https://doi.org/10.1186/s44147-023-00226-4 4.	 Khrissi L, El Akkad N, Satori H, Satori K (2023) A feature selection approach based on Archimedes’  optimization algorithm for optimal data classification. Int J Interact Multimed Artif Intell. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​ g​/​1​0​.​9​7​8​1​/​i​j​i​m​a​i​.​2​0​2​3​.​0​1​.​0​0​5​ 5.	 Faska Z et al (2025) A coherent approach-based fine-tuning of segment anything model plus water­ shed algorithm for instance segmentation of mitochondria in electron microscopy images. IEEE Access  13:98088–98105. https://doi.org/10.1109/access.2025.3574555 6.	 Khrissi L, El Akkad N, Satori H, Satori K (2022) A performant clustering approach based on an  improved sine cosine algorithm. Int J Comput 21(2):159–168 7.	 Moussaoui H, El Akkad N, Benslimane M (2023) A brain tumor segmentation and detection technique  based on birch and marker watershed. SN Comput Sci 4(4):339 8.	 Faska Z et al (2025) "satellite imagery semantic segmentation using InceptionResNetV2-Unet transfer  learning model," 2025 international conference on control, automation and diagnosis (ICCAD). Barce­ lona, Spain, pp 1–6. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​.​1​1​0​9​/​I​C​C​A​D​6​4​7​7​1​.​2​0​2​5​.​1​1​0​9​9​1​5​5 9.	 Faska Z, Khrissi L, Haddouch K, El Akkad N (2024) “Seg_UResNet: a deep hybrid convolutional  neural network of road scenes for semantic segmentation,” 2024 international conference on circuit.  Morocco, Systems and Communication (ICCSC), Fes, pp 1–8. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​.​1​1​0​9​/​I​C​C​S​C​6​2​0​7​4​.​2​0​ 2​4​.​1​0​6​1​6​4​2​8 10.	 Moussaoui H, El Akkad N, Benslimane M (2023) A hybrid skin lesions segmentation approach based  on image processing methods. Stat Optim Inf Comput 11(1):95–105 11.	 Khrissi L, Akkad NEL, Satori H, Satori K (2020) Simple and Efficient Clustering Approach Based on  Cuckoo Search Algorithm. In: 4th International Conference on Intelligent Computing in Data Sciences,  ICDS 2020. IEEE, p 9268754 12.	 Faska Z, Khrissi L, Haddouch K et al (2023) Random Forest for Semantic Segmentation Using Pre- Trained CNN (VGG16) Features. In: Digital Technologies and Applications: Proceedings of ICDTA’23,  Fez, Morocco, Volume 2. Cham, Springer Nature Switzerland, pp 510–520


## 1 3

Page 27 of 30    213

Multimedia Tools and Applications          (2026) 85:213

13.	 Khrissi L, Akkad NE, Satori H, Satori K (2019) Color image segmentation based on hybridization  between Canny and k-means. 7th Mediterranean Congress of Telecommunications 2019. CMT, p  8931358 14.	 Moussaoui H, Benslimane M, El Akkad N (2022) Image segmentation approach based on hybridization  between K-means and mask R-CNN. In: WITS 2020. Springer, Singapore, pp 821–830 15.	 Faska Z, Khrissi L, Haddouch K, El Akkad N (2021) A powerful and efficient method of image seg­ mentation based on random forest algorithm. In: International conference on digital technologies and  applications. Springer, Cham, pp 893–903 8 16.	 Moussaoui H, El Akkad N, Benslimane M, El-Shafai W, Baihan A, Hewage C, Singh Rathore R (2024)  Enhancing automated vehicle identification by integrating YOLO v8 and OCR techniques for high- precision license plate detection and recognition. Sci Rep 14(1):14389 17.	 Ohta Y-i, Kanade T, Sakai T (1978) An analysis systemfor scenes containing objects with substructures,  proceedings of the fourth international joint conference on. Pattern Recogn:752–754 18.	 A. Garcia-Garcia, S. Orts-Escolano, S. Oprea, V. Villena-Martinez, J. Garcia-Rodriguez, A Reviewon  Deep Learning Techniques Applied to Semantic Segmentation, 2017. Preprint at ​h​t​t​p​s​:​/​/​a​r​x​i​v​.​o​r​g​/​a​b​s​/​1​ 7​0​4​.​0​6​8​5​7​.​ 19.	 Yu H, Yang Z, Tan L, Wang Y, Sun W, Sun M, Tang Y (2018) Methods and datasets on semantic seg­ mentation: a review. Neurocomputing 304:82–103 20.	 Edelman S, Poggio T (1989) Integrating visual cues for object segmentation and recognition. Opt News  15:8 21.	 A. Kirillov, K. He, R. Girshick, C. Rother, P. Dollár, Panoptic Segmentation, 2018. Preprint at ​h​t​t​p​s​:​/​/​a​ r​x​i​v​.​o​r​g​/​a​b​s​/​1​8​0​1​.​0​0​8​6​8​.​ 22.	 B. Cheng, M.D. Collins, Y. Zhu, T. Liu, T.S. Huang, H. Adam, L.-C. Chen, Panoptic-DeepLab: A Sim­ ple, Strong, and Fast Baseline for Bottom-up Panoptic Segmentation, https://arxiv.org/abs/1911.10194  2019. 23.	 Faska Z, Khrissi L, Haddouch K, Akkad EL, N. (2023) Random Forest for semantic segmentation using  pre-trained CNN (VGG16) features. In: International conference on digital technologies and applica­ tions. Springer, Cham. https://doi.org/10.1007/978-3-031-29860-8_52 24.	 LeCun Y, Bengio Y, Hinton G (2015) Deep learning. Nature 521:436 25.	 Goodfellow Y, Bengio A (2016) Courville. MIT Press, Deep Learning 26.	 LeCun Y, Bottou L, Bengio Y, Haffner P (1998) Gradient-based learning applied to documentrecogni­ tion. Proc IEEE 86:2278–2324 27.	 Z.C. Lipton, J. Berkowitz, C. Elkan, A Critical Review of Recurrent Neural Networks for Sequence  Learning, https://arxiv.org/abs/1506.00019 2015. 28.	 Visin F, Ciccone M, Romero A, Kastner K, Cho K, Bengio Y, Matteucci M, Courville A (2016) Reseg: a  recurrent neural network-based model for semantic segmentation. In: Proceedings of the IEEE Confer­ ence on Computer Vision and Pattern Recognition Workshops, pp 41–48 29.	 Ess A, Müller T, Grabner H, Van Gool LJ (2009) Segmentation-based urban traffic scene understanding.  BMVC 1:2 30.	 Geiger A, Lenz P, Urtasun R (2012) Are we ready for autonomous driving? The KITTI vision bench­ mark suite. In: 2012 IEEE Conference on Computer Vision and Pattern Recognition. IEEE, pp 3354– 3361. https://doi.org/10.1109/CVPR.2012.6248074 31.	 Cordts M, Omran M, Ramos S, Rehfeld T, Enzweiler M, Benenson R, Franke U, Roth S, Schiele B  (2016) The cityscapes dataset for semantic urban scene understanding. Proc IEEE Conf Comput Vis  Pattern Recognit:3213–3223 32.	 M. Oberweger, P. Wohlhart, V. Lepetit, Hands Deep in Deep Learning for Hand Pose Estimation, 2015.  Preprint at https://arxiv.org/abs/1502.06807. 33.	 Yoon Y, Jeon H-G, Yoo D, Lee J-Y, So Kweon I (2015) Learning a deep convolutional network for light- field image super-resolution. In: Proceedings of the IEEE International Conference on Computer Vision  Workshops, pp 24–32 34.	 Wan J, Wang D, Hoi SCH, Wu P, Zhu J, Zhang Y, Li J (2014) Deep learning for content-based image  retrieval: a comprehensive study. In: Proceedings of the 22nd ACM International Conference on Multi­ media. ACM, pp 157–166 35.	 Zhu H, Meng F, Cai J, Lu S (2016) Beyond pixels: a comprehensive survey from bottom-up to semantic  image segmentation and cosegmentation. J Vis Commun Image Represent 34:12–27. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​ .​1​0​1​6​/​j​.​j​v​c​i​r​.​2​0​1​5​.​1​0​.​0​1​2​ 36.	 He K, Zhang X, Ren S, Sun J (2016) Deep residual learning for image recognition. In: Proceedings of  the IEEE Conference on Computer Vision and Pattern Recognition, pp 770–778 37.	 Shelhamer E, Long J, Darrell T (2017) Fully convolutional networks for semantic seg-mentation. IEEE  Trans Pattern Anal Mach Intell 39(4):640–651


## 1 3

213    Page 28 of 30

Multimedia Tools and Applications          (2026) 85:213

38.	 Zhu S, Ma W, Yao J (2022) Global and local geometric constrained feature matching for high resolution  remote sensing images. Comput Electr Eng 103:108337 39.	 Wang X, Wang S, Ning C, Zhou H (2021) Enhanced feature pyramid network with deep semantic  embedding for remote sensing scene classification. IEEE Trans Geosci Remote Sens 59(9):7918–7932 40.	 Tang X, Ma Q, Zhang X, Liu F, Ma J, Jiao L (2021) Attention consistent network for remote sensing  scene classification. IEEE J Sel Top Appl Earth Observ Remote Sens 14:2030–2045 41.	 Krizhevsky A, Sutskever I, Hinton G (2012) ImageNet classification with deep convolutional neural  networks. In: Proc. adv. NIPS, pp 1106–1114 42.	 Long J, Shelhamer E, Darrell T (2015) Fully convolutional networks for semantic segmentation. In:  2015 IEEE Conference on Computer Vision and Pattern Recognition (CVPR), Boston, MA, USA, pp  3431–3440. https://doi.org/10.1109/CVPR.2015.7298965 43.	 Sherrah J. Fully convolutional networks for dense semantic labelling of high-resolution aerial imagery.  2016, Preprint at https://arxiv.org/abs/1606.02585. 44.	 Kaiser P, Wegner J, Lucchi A, Jaggi M, Hofmann T, Schindler K (2017) Learning aerial image segmen­ tation from online maps. IEEE Trans Geosci Remote Sens 55(11):6054–6068 45.	 Ronneberger O, Fischer P, Brox T (2015) U-net: convolutional networks for biomedical image segmen­ tation. In: International Conference on Medical Image Computing and Computer-Assisted Intervention.  Springer, Cham, pp 234–241 46.	 Badrinarayanan V, Handa A, Cipolla R (2017) Segnet: a deep convolutional encoder-decoder architec­ ture for robust semantic pixel-wise labelling. IEEE Trans Pattern Anal Mach Intell 39(12):2481–2495 47.	 Chen LC, Papandreou G, Kokkinos I, Murphy K, Yuille AL (2018) Deeplab: semantic image segmenta­ tion with deep convolutional nets, atrous convolution, and fully connected CRFs. IEEE Trans Pattern  Anal Mach Intell 40(4):834–848 48.	 Han J, Zhang D, Cheng G, Liu N, Xu D (2018) Advanced deep-learning techniques for salient and  category-specific object detection: a survey. IEEE Signal Process Mag 35:84–100 49.	 K. Simonyan, A. Zisserman, Very Deep Convolutional Networks for Large-Scale Image Recognition,  2014. Preprint at arXiv preprint https://arxiv.org/abs/1409.1556. 50.	 Yu S, Xie L, Liu L, Xia D (2019) Learning long-term temporal features with deep neural networks for  human action recognition. IEEE Access 8:1840–1850 51.	 Szegedy C, Vanhoucke V, Ioffe S, Shlens J, Wojna Z (2016) Rethinking the inception architecture for  computer vision. In: Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition.  IEEE, pp 2818–2826 52.	 Huang G, Liu Z, Van Der Maaten L, Weinberger KQ (2017) Densely connected convolutional networks.  In: Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition, pp 4700–4708 53.	 Al-Dhamari A, Sudirman R, Mahmood NH (2020) Transfer deep learning along with binary support  vector machine for abnormal behavior detection. IEEE Access 8:61085–61095 54.	 Su J, Vargas DV, Sakurai K (2019) One pixel attack for fooling deep neural networks. IEEE Trans Evol  Comput 23(5):1–13 55.	 Luo W., Wu C., Zhou N., Ni L. Random Directional Attack for Fooling Deep Neural Networks. 2019,  Preprint at https://arxiv.org/abs/1908.02658. 56.	 LeCun Y, Boser B, Fukushima JK, Miyake S (1982) Neocognitron: a self-organizing neural network  model for a mechanism of visual pattern recognition. In: Competition and cooperation in neural nets.  Springer, pp 267–285. https://doi.org/10.1007/978-3-642-46466-9_18 57.	 Denker S, Henderson D, Howard RE, Hubbard W, Jackel LD (1989) Backpropagation applied to hand­ written zip code recognition. Neural Comput 1(4):541–551. https://doi.org/10.1162/neco.1989.1.4.541 58.	 Krizhevsky A, Sutskever I, Hinton GE (2017) ImageNet classification with deep convolutional neural  networks. Commun ACM 60(6):84–90. https://doi.org/10.1145/3065386 59.	 Russakovsky O, Deng J, Su H, Krause J, Satheesh S, Ma S, Huang Z, Karpathy A, Khosla A, Bern­ stein M et al (2015) ImageNet large scale visual recognition challenge (ILSVRC). Int J Comput Vis  115(3):211–252. https://doi.org/10.1007/s11263-015-0816-y 60.	 Ball JE, Anderson DT, Chan CS (2017) Comprehensive survey of deep learning in remote sensing:  theories, tools, and challenges for the community. J Appl Remote Sens 11:042609. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​.​1​1​ 1​7​/​1​.​J​R​S​.​1​1​.​0​4​2​6​0​9​ 61.	 Ronneberger O, Fischer P, Brox T (2015) U-net: convolutional networks for biomedical image segmen­ tation. In: Navab N, Hornegger J, Wells WM, Frangi AF (eds) Medical Image Computing and Com­ puter-Assisted Intervention – MICCAI 2015. Springer International Publishing, Cham, pp 234–241.  https://doi.org/10.1007/978-3-319-24574-4_28 62.	 Zhao, H., Shi, J., Qi, X., Wang, X., Jia, J., 2017. Pyramid scene parsing network. Preprint at ​h​t​t​p​s​:​/​/​a​r​x​ i​v​.​o​r​g​/​a​b​s​/​1​6​1​2​.​0​1​1​0​5​.​ 63.	 Chen, L.-C., Papandreou, G., Schroff, F., Adam, H., 2017. Rethinking Atrous convolution for semantic  image segmentation. Preprint at https://arxiv.org/abs/1706.05587.


## 1 3

Page 29 of 30    213

Multimedia Tools and Applications          (2026) 85:213

64.	 Simonyan, K., Zisserman, A., 2015. Very deep convolutional networks for large-scale image recogni­ tion. Preprint at https://arxiv.org/abs/1409.1556. 65.	 Abdollahi A, Pradhan B, Gite S, Alamri A (2020) Building footprint extraction from high resolution  aerial images using generative adversarial network (GAN) architecture. IEEE Access. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​ 0​.​1​1​0​9​/​A​C​C​E​S​S​.​2​0​2​0​.​3​0​3​8​2​2​5​ 66.	 Maggiori E, Tarabalka Y, Charpiat G, Alliez P (2016) Convolutional neural networks for large-scale  remote-sensing image classification. IEEE Trans Geosci Remote Sens 55:645–657 67.	 Yuan J (2017) Learning building extraction in aerial scenes with convolutional networks. IEEE Trans  Pattern Anal Mach Intell 40:2793–2798 68.	 Szegedy C, Liu W, Jia Y, Sermanet P, Reed S, Anguelov D et al (2015) Going deeper with convolutions.  In: Proceedings of the IEEE conference on computer vision and pattern recognition, pp 1–9 69.	 Zeiler MD, Krishnan D, Taylor GW, Fergus R (2010) Deconvolutional networks. In: 2010 IEEE com­ puter society conference on computer vision and pattern recognition, pp 2528–2535 70.	 Noh H, Hong S, Han B (2015) Learning deconvolution network for semantic segmentation. In: Proceed­ ings of the IEEE international conference on computer vision, pp 1520–1528 71.	 Badrinarayanan V, Kendall A, Cipolla R (2017) Segnet: a deep convolutional encoder–decoder architec­ ture for image segmentation. IEEE Trans Pattern Anal Mach Intell 39:2481–2495 72.	 Zhu XX, Tuia D, Mou L, Xia GS, Zhang L, Xu F, Fraundorfer F (2017) Deep learning in remote sens­ ing: a comprehensive review and list of resources. IEEE Geosci Remote Sens Mag 5:8–36. ​h​t​t​p​s​:​/​/​d​o​i​.​ o​r​g​/​1​0​.​1​1​0​9​/​M​G​R​S​.​2​0​1​7​.​2​7​6​2​3​0​7​ 73.	 Lee K, Kim JH, Lee H, Park J, Choi JP, Hwang JY (2022) Boundary-oriented binary building segmen­ tation model with two scheme learning for aerial images. IEEE Trans Geosci Remote Sens 60:1–17.  https://doi.org/10.1109/TGRS.2021.3089623 74.	 Zhang X, Ma W, Li C, Wu J, Tang X, Jiao L (2020) Fully convolutional networkbased ensemble method  for road extraction from aerial images. IEEE Geosci Remote Sens Lett 17(10):1777–1781. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​ g​/​1​0​.​1​1​0​9​/​L​G​R​S​.​2​0​1​9​.​2​9​5​3​5​2​3​ 75.	 Verma U, Rossant F, Bloch I (2015) Segmentation and size estimation of tomatoes from sequences of  paired images. EURASIP J Image Video Process 2015(1):1–23. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​.​1​1​8​6​/​s​1​3​6​4​0​-​0​1​5​-​0​0​ 8​7​-​0​ 76.	 Zhou H, Kong H, Wei L, Creighton D, Nahavandi S (2017) On detecting road regions in a single UAV  image. IEEE Trans Intell Transp Syst 18(7):1713–1722. https://doi.org/10.1109/TITS.2016.2622280 77.	 Gibril MBA, Shafri HZM, Shanableh A, Al-Ruzouq R, Wayayok A, Hashim SJ (2021) Deep convolu­ tional neural network for large-scale date palm tree mapping from UAV-based images. Remote Sens  13(14):2787. https://doi.org/10.3390/rs13142787 78.	 Pandey A, Jain K (2021) An intelligent system for crop identification and classification from UAV  images using conjugated dense convolutional neural network. Comput Electron Agric:106–543. ​h​t​t​p​s​:​/​ /​d​o​i​.​o​r​g​/​1​0​.​1​0​1​6​/​j​.​c​o​m​p​a​g​.​2​0​2​1​.​1​0​6​5​4​3​ 79.	 R.K. Srivastava, K. Greff, J. Schmidhuber, Highway networks, 2015, Preprint at ​h​t​t​p​:​/​/​a​r​x​i​v​.​o​r​g​/​a​b​s​/​1​5​ 0​5​.​0​0​3​8​7​.​ 80.	 Bastani F, He S, Abbar S, Alizadeh M, Balakrishnan H, Chawla S, Madden S, DeWitt D (2018) Road­ Tracer: automatic extraction of road networks from aerial images. Computer Vision and Pattern Recog­ nition. https://doi.org/10.1109/CVPR.2018.00496 81.	 Sun T, Chen Z, Yang W, Wang Y Stacked U-nets with multi-output for road extraction. In: IEEE Com­ puter Society Conference on Computer Vision and Pattern Recognition Workshops, vol 2018, pp 187– 191. https://doi.org/10.1109/CVPRW.2018.00033 82.	 A. Van Etten, You only look twice: rapid multi-scale object detection in satellite imagery, 2018, Preprint  at http://arxiv.org/abs/1805.09512. 83.	 Demir I, Koperski K, Lindenbaum D, Pang G, Huang J, Basu S, Hughes F, Tuia D, Raska R (2018)  DeepGlobe 2018: A challenge to parse the earth through satellite images. In: IEEE Computer Society  Conference on Computer Vision and Pattern Recognition Workshops, pp 172–181. ​h​t​t​p​s​:​/​/​d​o​i​.​o​r​g​/​1​0​.​1​ 1​0​9​/​C​V​P​R​W​.​2​0​1​8​.​0​0​0​3​1​ 84.	 Khan BA, Jung JW (2024) Semantic segmentation of aerial imagery using U-net with self-attention and  separable convolutions. Appl Sci 14(9):3712. https://doi.org/10.3390/app14093712 85.	 Ramos LT, Sappa AD (2025) Leveraging U-net and selective feature extraction for land cover classifica­ tion using remote sensing imagery. Sci Rep 15(1):784. https://doi.org/10.1038/s41598-024-84795-1 86.	 Dimitrovski I, Spasev V, Loshkovska S, Kitanovski I (2024) U-net ensemble for enhanced semantic  segmentation in remote sensing imagery. Remote Sens 16:2077. https://doi.org/10.3390/rs16122077 87.	 Benali Amjoud A, Amrouch M (2020) Convolutional neural networks backbones for object detection,  Image and Signal Processing. In: 9th International Conference, ICISP 2020, Marrakesh, Morocco, June  4–6, 2020, Proceedings 9. Springer, pp 282–289


## 1 3

213    Page 30 of 30

Multimedia Tools and Applications          (2026) 85:213

88.	 Peng C, Zhang X, Yu G, Luo G, Sun J (2017) Large kernel matters - Improve semantic segmentation by  global convolutional network. In: Proceedings of the - 30th IEEE conference on computer vision and  pattern recognition, CVPR, pp 1743–1751. https://doi.org/10.1109/CVPR.2017.189 89.	 Szegedy C, Ioffe S, Vanhoucke V, Alemi A (2017) Inception-v4, inception-ResNet and the impact of  residual connections on learning. In: Proceedings of the 31st AAAI conference on artificial intelligence.  AAAI, pp 4278–4284 90.	 Szegedy C, Liu W, Jia Y, Sermanet P, Reed S, Anguelov D, Erhan D, Vanhoucke V, Rabinovich A (2014)  Going deeper with convolutions. In: Proceedings of the IEEE computer society conference on computer  vision and pattern recognition, pp 1–9 91.	 Shahhosseini M, Hu G, Pham H (2022) Optimizing ensemble weights and hyperparameters of machine  learning models for regression problems. Machine Learning with Applications 7:100251 92.	 Murphy AH (1996) The finley affair: a signal event in the history of forecast verification. Weather Fore­ cast 11(1):3 93.	 Jaccard P (1912) The distribution of the flora in the Alpine Zone.1. New Phytol 11(2):37–50. ​h​t​t​p​s​:​/​/​d​o​ i​.​o​r​g​/​1​0​.​1​1​1​1​/​j​.​1​4​6​9​-​8​1​3​7​.​1​9​1​2​.​t​b​0​5​6​1​1​.​x 94.	 Sørensen T (1948) A method of establishing groups of equal amplitude in plant sociology based on  similarity of species and its application to analyses of the vegetation on Danish commons. Kong Danske  Vidensk Selsk 5(4):1–34 95.	 Dice LR (1945) Measures of the amount of ecologic association between species. Ecology 26(3):297– 302. https://doi.org/10.2307/1932409 96.	 Sun K, Zhao Y, Jiang B, Cheng T, Xiao B, Liu D, Mu Y, Wang X, Liu W, Wang J (2019) High-resolution  representations for labeling pixels and regions. In: Proceedings of the IEEE/CVF International Confer­ ence on Computer Vision (ICCV), pp 6568–6577. https://doi.org/10.1109/ICCV.2019.00668 97.	 Ma J et al (2020) Building extraction of aerial images by a global and multi-scale encoder decoder  network. Remote Sens 12:2350 98.	 V. Iglovikov, A. Shvets, “Ternausnet: U-net with vgg11 encoder pre-trained on imagenet for image  segmentation.”Preprint at https://arxiv.org/abs/1801.05746, 2018. 99.	 G. Chhor, C. B. Aramburu, I. Bougdal-Lambert, Satellite image segmentation for building detection  using U-Net. ​h​t​t​p​:​/​/​c​s​2​2​9​.​s​t​a​n​f​o​r​d​.​e​d​u​/​p​r​o​j​2​0​1​7​/​f​i​n​a​l​-​r​e​p​o​r​t​s​/​5​2​4​3​7​1​5​.​p​d​f, 2017. 100.	Ataş İ (2023) Performance evaluation of JaccardDice coefficient on building segmentation from high  resolution satellite images. BAJECE 11(1):100–106

Publisher’s note  Springer Nature remains neutral with regard to jurisdictional claims in published maps and  institutional affiliations.

Springer Nature or its licensor (e.g. a society or other partner) holds exclusive rights to this article under a  publishing agreement with the author(s) or other rightsholder(s); author self-archiving of the accepted manu­ script version of this article is solely governed by the terms of such publishing agreement and applicable law.

Authors and Affiliations

Zahra Faska1  · Lahbib Khrissi1 · Khalid Haddouch1 · Nabil El Akkad1

Zahra Faska

zahra.faska@usmba.ac.ma

1	 Laboratory of Applied Sciences and Emerging Technologies, ENSA, Sidi Mohamed Ben  Abdellah University, Fez, Morocco


## 1 3
