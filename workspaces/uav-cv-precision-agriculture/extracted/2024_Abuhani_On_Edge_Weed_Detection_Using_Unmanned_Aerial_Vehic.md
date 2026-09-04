---
workspace_id: SCI-000440
doi: 10.2139/ssrn.4980431
title: On-Edge Weed Detection Using Unmanned Aerial Vehicles
authors:
- family_name: Abuhani
  given_name: Diaa  Addeen
  orcid: null
- family_name: Haj Hussain
  given_name: Maya
  orcid: null
- family_name: ElMohandes
  given_name: Mohamed
  orcid: null
- family_name: Khan
  given_name: Jowaria
  orcid: null
- family_name: Zualkernan
  given_name: Imran
  orcid: null
year: 2024
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:46:38.539401+00:00'
---

# On-Edge Weed Detection Using Unmanned Aerial Vehicles

Preprint not peer reviewed

Contents lists available at ScienceDirect

Internet of Things

journal homepage: www.elsevier.com/locate/compag

On-Edge Weed Detection Using Unmanned Aerial Vehicles


## Abstract

Weeds are undesirable, persistent plants that infiltrate fields and hamper the growth of surrounding crops and consume resources  required for keeping crops alive and sustaining their growth. Weeds cause significant yield loss and cause about 35% of global  crop yield loss annually. Traditional weed treatment techniques rely on naked eye observation and manual removal of weeds by  farmers. However, these methods are time-consuming, inefficient, and expensive. Recently, due to their efficiency and cost- effectiveness, Unmanned Aerial Vehicles (UAV) have been used for weed detection. Using computer vision, these systems can  quickly and accurately identify and target weeds for efficient eradication. However, most current UAV-based weeding solutions  rely heavily on expensive hyperspectral cameras, which may not be affordable to average farmers. In addition, the weed detection  is not done in real-time requiring an additional drone pass for spraying. This paper proposes an efficient, affordable, and power  efficient weed detection method to perform weed detection and spraying using consumer grade cameras and computing on the edge  (UAV). The proposed method introduces a custom and drone-deployable U-Net neural architecture with a novel methodology that  achieves state-of-the-art results on the CoFly dataset with an IoU Score above 50% and a Dice score exceeding 60% at multiple  augmentation levels. A key feature of the proposed solution is that it can be deployed on the edge.

© 2017 Elsevier Inc. All rights reserved. Keywords: Weed Detection; UAVs; Multispectral; Low Power; Deep Learning; Optimization.


## 1. Introduction

Precision Agriculture (PA) is an agricultural management strategy that aims to enhance agronomic output  and reduce resource waste through the integration and utilization of technology and farming management principles  in agricultural fields. Image segmentation is used in PA to identify different features or components of a field, such  as crops, weeds, soil types, and water content. By segmenting an image, farmers can obtain detailed information about  the spatial distribution and characteristics of these features, which can be used to inform decisions about planting,  fertilizing, irrigating, and harvesting. There are various methods for image segmentation in PA, including traditional  techniques such as thresholding, clustering, and edge detection, as well as more advanced methods such as deep  learning-based approaches. Deep learning-based approaches such as convolutional neural networks (CNNs) have  shown promising results in crop segmentation tasks, particularly in complex and variable environments. By combining  image segmentation with other PA technologies such as sensors, GPS, and drones, farmers can obtain real-time  information about their crops and fields, which can be used to make data-driven decisions and improve crop yields,

Please cite this article as: First author et al., Article title, Computer Vision and Image Understanding (2017),  http://dx.doi.org/10.1016/j.cviu.2017.00.000

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

2

efficiency, and sustainability. This agrarian data can then be used by farmers to optimize and tailor their farming  practices to their fields' requirements, allowing farmers to apply the right resources exactly where needed and at the  time needed. Therefore, PA aids in reducing resource waste and agrochemical usage, increasing crop yield and quality,  and reducing human labor. Since its advent in the 1980s, PA has continuously expanded, keeping pace with the rapid  emergence of new technologies for data acquisition and processing (Gebbers & Adamchuk, 2010).  PA has since then  been used to tackle complicated farming problems, including optimized fertilizer usage, weed and pest control, crop  disease management, and crop quality improvement. With the boom of machine learning (ML) and neural networks  (NN), especially for solving computer vision problems, both are being increasingly integrated in PA.        One of agriculture's most pressing problems today is weed infestation in fields. Given its severity and impact,  using PA to tackle this problem has recently become very appealing to many researchers in agriculture due to its cost- efficiency given PA technologies that reduce the need for blanket herbicide applications, improved efficacy, and  environmental sustainability amongst others (Bongiovanni & Lowenberg-Deboer, 2004). Notably, finding deep  learning solutions using remote sensing data and real-time data processing has garnered the most attention due to the  large-scale coverage aspect of remote sensing data, which can provide information about large areas of agricultural  land, allowing farmers to monitor and manage their crops more efficiently. Additionally, real-time data processing  allows farmers to obtain timely and actionable information about their crops, enabling them to make informed  decisions and respond quickly to changing conditions. Furthermore, deep learning solutions can be used to automate  the analysis of remote sensing data, reducing the need for manual labor and increasing efficiency. Hence, this study  aims to find a competitive solution for real-time weed detection and classification in agricultural fields, utilizing novel  deep-learning models that are deployable on a UAV.        Weeds are undesirable, persistent plants that infiltrate fields and hamper the growth of surrounding crops. Weeds  mainly cause problems by consuming resources required for keeping crops alive and sustaining their growth. To be  precise, weeds compete with crops over water, soil nutrients, space, and even sunlight. Hence, unsurprisingly, when  fields are infested with weeds, crop yield loss is noted. In fact, weeds have been the cause behind 35% of global crop  yield loss annually, presenting one of the most significant factors causing yield loss (Khan et al., 2021). Furthermore,  weeds present a major problem for surrounding crops by harboring pests, which feed on crops and spread diseases as  they move around in fields, weakening and killing off crops. In addition, certain weed species cause even graver  problems in agricultural fields. If left uncontrolled, these weeds present a considerable danger to their surrounding  ecosystem. Therefore, finding and applying early and effective weed control mechanisms is an important issue to  tackle to ensure a good yield from a field and to protect the surrounding environment. Traditionally, weed is detected  by farmers by manually surveying their fields. Once farmers find weeds, they quickly apply weed control mechanisms.  The most popular of which include the following two approaches: Physically uprooting weeds and spraying entire  fields with herbicides after their surveyal (Al-Badri et al., 2022). The first approach is time-consuming, laborious, and  can leave many weeds undetected. On the other hand, the second approach is quite wasteful and excessive, and  unnecessarily expensive. Extensive research has also been done to show the threats of excessive herbicide use on  weeds. As discovered, such a use results in the cultivation of herbicide-resistant populations of weeds. Currently,  around 270 species of weeds are resistant to herbicides (Rai & Ingle, 2012). Hence by using traditional herbicide  application methods for weed control, farmers run a more considerable risk of ruling herbicides ineffective in the  future.        The problem with the traditional weed control approaches is their reliance on human scouting of agricultural land.  Typically, this task is time-consuming, cumbersome, and susceptible to weeds getting bypassed by farmers during  scouting (Anderson, 2020). Thus, such a data collection strategy is inefficient and can cause weed infestations to  continue to grow unbeknownst to the farmers. Hence, a solution to the problem of weed management lies away from  traditional approaches and instead in integrating PA farming strategies with deep learning to perform accurate weed  detection, classification, and control. Today, deep learning models have reached competitively high accuracy levels  in object detection, sufficient for detecting such objects as weeds. These models can be deployed on an Unmanned  Aerial Vehicle (UAV), which represents a reasonably inexpensive and fast data acquisition method that can reach  hard-to-reach areas and does not disturb plants or soil (Koot, 2014). Upon the detection of weeds, UAVs can perform  on-the-spot herbicide spraying on their detected targets, eliminating the problem of inefficiency and wastefulness of  traditional methods. This comprehensive weed detection and control approach is fast, inexpensive, reduces herbicide

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

Author name / Computer Vision and Image Understanding  000 (2017) 000–000 3

usage and labor, and is highly accurate. Therefore, the main goal of our work is to implement such a system, which  can be described as a comprehensive deep-learning-based UAV deployable system for weed detection and control.

The main contributions of this paper are summarized in the following points:

 Propose a cost-effective end-to-end drone-based weed detection system that utilizes consumer-grade cameras  on the edge to achieve precise real-time weed detection in agricultural fields.  Develop two lightweight U-Net models capable of detecting small weeds with high precision that can be  deployed on the edge.  Conduct a comprehensive analysis on the influence of UAV image-specific image augmentation techniques  and the integration of RGB-derived features on overall model performance.

Nomenclature

CIVE Colour Index of Vegetation Extraction CNN  Convolutional Neural Network CWFID Crop/Weed Field Image Dataset ED Edge Detector ExG Excess Green ExR Excess Red FPS Frames Per Second GAN Generative Adversarial Networks GSD Ground Sample Distance HSV Hue, Saturation, Value IoU Intersection over Union ML Machine Learning mAP Mean Average Precision NDI Normalized Difference Index NDVI Normalized Difference Vegetation Index NIR Near-Infrared PA Precision Agriculture RGB Red, Green, Blue SoC System-on-Chip LBP Local Binary Patterns TGI Triangular Greenness Index UAV Unmanned Aerial Vehicle VI Vegetation Index


## 2. Related works


### 2.1 Semantic segmentation for efficient weed detection.

Recently, there has been a significant focus on the problem of weed detection in agricultural fields, leading to  extensive research efforts. Numerous proposals have emerged, presenting complete pipelines to tackle this issue.  Amongst the most notable are those that address the problem by deploying semantic segmentation techniques.  Semantic segmentation is a computer vision task that aims to assign a label to every pixel in each image, enabling  accurate classification and precise localization of objects within the image. Given its ability to accurately classify and  localize objects by precise boundary detection, this technique has been the subject of much PA work, specifically in  tackling the problem of weed and crop detection, where the objects (weeds and crops) are sometimes indifferentiable

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

4

and in many cases, interweaved. This ability allows segmentation models to be an essential component in effective,  comprehensive weeding systems.

Various approaches have been employed for effective crop and weed segmentation in agricultural land. Often,  multispectral imagery incorporating more than three bands is utilized, with the infrared band being particularly  important due to its sensitivity to vegetation. In certain cases, new bands are created by combining existing spectral  bands and thereafter incorporated into segmentation algorithms. A notable example is the Normalized Difference  Vegetation Index (NDVI), which combines the Near Infrared and Red bands into a single index. Sahin et al. (2023)  demonstrated the use of multispectral imagery by employing green wavelengths, filtered Near Infrared (NIR), and  NDVI channels for early-stage weed segmentation in sunflower fields. Similarly, Rosas et al. (2022) utilized RGB  and corresponding NIR images from the same dataset to create merged four-band images for weed detection in  sunflower fields. For the development of a precise real-time weed detection system, Alchanatis et al. (2005) extracted  two channels (660nm and 800nm) from a set of 100-channel images obtained through an acousto-optic tunable  hyperspectral sensor. These channels were then used as input for a weed detection algorithm. Lastly, Su et al. (2022)  aimed to accurately map blackgrass weeds in wheat fields by generating three-band images using 18 different  vegetation indices extracted from five spectral-band imagery. Notably, among all the calculated vegetation indices,  the Triangular Greenness Index (TGI) extracted from the RGB channels of their images was found to be the most  discriminative.

In cases where multispectral imagery is not available, filters and combinations of RGB channels can be used to  perform accurate segmentation of weeds. For instance, Parra et al. (2020) tested edge detection and sharpening filters  for the pixel-wise classification of weeds in ornamental lawns and sports turfs and identified that sharpening filters in  conjunction with aggregation techniques offered the best results. Furthermore, Ferreira et al. (2017) conducted a study  where they utilized and evaluated various techniques for shape, color, and texture extraction to achieve accurate  detection and segmentation of weeds in soybean fields. In their research, they explored two alternate color spaces,  namely HSV and CIELab, for representing RGB data. For texture extraction, they employed Local Binary Patterns  (LBP) and the Gray-Level Co-occurrence Matrix (GLCM) as texture extractors. Lastly, for shape extraction, they  utilized the Histogram of Oriented Gradients (HOG) feature extraction technique. In order to fully leverage the  available RGB data, Milioto et al. (2018) computed various vegetation indices and alternate representations of RGB  data used for plant classification in order to accurately segment weeds and crops in agricultural fields. The computed  indices include the Excess Green (ExG), Excess Red (ExR), Color Index of Vegetation Extraction (CIVE), and  Normalized Difference Index (NDI). In addition, they explored the HSV color space as an alternate representation to  RGB. The authors also employed edge detectors such as the Sobel derivatives and the Laplacian and Canny edge  detectors to enhance the segmentation process. In total, the authors obtained 11 representations of RGB data, which  they concatenated to the original RGB input images, resulting in 14 channel images that were subsequently fed into  the model and trained on.


### 2.2 U-Net architecture for the semantic segmentation of weeds and crops.

Various architectures have been proposed for the task of semantic segmentation of crops and weeds in agricultural  fields, with the U-NET being the most popular architecture. U-Net is a U-shaped fully convolutional encoder decoder  architecture with skip connections that was built for the task of semantic segmentation. The U-Net consists of an  encoder path that plays the role of a feature extractor and a decoder path that takes in the features learnt by the encoder  and projects them onto a higher resolution space. U-NETs can be easily customized to better fit the problem they’re  being used for. This adaptability has allowed many researchers working in semantic segmentation in agriculture to  tailor their architectures to their specific needs and hence achieve optimal performance.

In the context of weed and crop segmentation, the primary objective of many studies is to develop a lightweight  U-NET model capable of detecting small objects accurately. For instance, Zou et al. (2021a), constructed a VGG- based U-NET model with a reduced number of encoder blocks in an effort to reduce the size of the model, where they  only used 3 encoder blocks and 4 decoder blocks. Given the low complexity of their segmentation task of green bristle

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

Author name / Computer Vision and Image Understanding  000 (2017) 000–000 5

grass, the simplification of the encoder path did not affect the performance of the model, achieving an Intersection  over Union (IoU) score of 92.91% upon evaluation. Likewise, Ma et al. (2023) proposed an improved VGG-16-based  U-NET model for weed segmentation in Cabbage fields. To simplify the network and decrease its number of  parameters, the authors utilized only six convolutional layers from the VGG-16 model for the encoder of their U- NET. Similarly, the decoder path also underwent a reduction in the number of convolutional layers. In order to enhance  the model's segmentation accuracy, the max-pooling layers in the encoder blocks were replaced with average pooling  layers. Additionally, efficient channel attention (ECA) modules were introduced to the decoder blocks before the  concatenation of feature maps from the encoder and decoder paths, enabling the network to focus on important target  features within the feature maps. The authors trained their network on a dataset of Cabbage and weed images and  reported an mIoU of 88.96% and a pixel accuracy of 93.05%. Zou et al. (2022) constructed a simplified VGG-based  U-NET model for the segmentation of weeds in wheat fields. The model’s encoder depth was reduced, given the  simple nature of the problem. Convolutional layers were replaced with successive dilated convolutional layers to  increase the receptive field of the network without increasing computational costs, all the while ensuring no  information loss. In the decoder, the number of convolutional layers per block was reduced to one. The evaluation  results returned an IoU of 88.98% and an accuracy of 95.76%. In a similar study, Zou et al.  (2021b) utilized a modified  U-Net architecture to segment crops from images of crops and weeds taken in a marigold field. The encoder of the U- Net model was formed using the VGG-16 model. To simplify the model, dilated convolutional layers were used  instead of regular convolutional layers in the final two encoder blocks. Furthermore, like in their previous work, the  dilated convolutional layers were arranged in sets of three within each block to supplement each other and preserve  information, with dilation rates of 1, 2, and 5. Similarly, the number of convolutional layers in the decoder block was  reduced to one in each block. The reported IoU of the model was 93.40%, and its accuracy was 98.84%. Ullah et al.  (2021) presented an end-to-end crop and weed segmentation system based on a modified, Dilated U-NET. Their model  uses a modified ResNet-50-based encoder with three subsequent dilated convolutional layers at its input and identity  blocks of three convolutional layers each, with the middle layer being a dilated convolutional layer with a dilation rate  of 2. The inclusion of dilated convolutional layers was motivated by the objective of extracting shape and object  connectivity information to enhance segmentation accuracy, all while avoiding the use of computationally expensive  large kernels. In an effort to reduce the number of model parameters, all convolutional layers in both encoder and  decoder paths were changed to depth-wise separable convolutional layers. The model attained a mean average  precision of 99.45% and an mIoU of 89.12% and used 15M parameters.

Karimi et al. (2023), also presented a reduced U-NET architecture, with three encoder and three decoder blocks  for the pixel-wise segmentation of bur chervil in wheat and rye fields. The authors reported mean dice loss values that  ranged from 0.9801 to 0.9954 and mean Jaccard values that ranged from 0.9628 to 0.9909 on their wheat field dataset  and a mean dice loss value of 0.9605 and a Jaccard value of 0.9292 on their rye field dataset. Similarly, Arun et al.  (2020), built a reduced U-NET model for the semantic segmentation of images from the crop/weed field image dataset  (CWFID) that utilized a total of 19 convolutional layers across its encoder and decoder path, leading to a reduced  number of model parameters. After training and upon evaluation, their model returned an accuracy of 95.34% and an  error rate of 7.45%. In another work, Arun and Umamaheswari (2022), proposed a similar architecture that comprised  of 19 depth-wise separable convolutional layers, which they trained on the same dataset. In this work, the authors also  applied model pruning to further compress their model. They employed residual learning to enhance segmentation  accuracy and drop-channel dropout layers to reduce the model’s error rate. The reported performance of their model  on the metrics of F1 score, accuracy, and error rate was 97.10%, 95.40%, and 6.42%, respectively. Khan et al. (2020),  proposed a cascaded encoder-decoder network for the semantic segmentation of weeds in crop field imagery. Their  architecture utilizes four cascaded encoder-decoder networks to create a segmentation model that achieves competitive  performance compared to the state-of-the-art while requiring a significantly reduced number of parameters. The  authors employed four distinct datasets in their research: the rice seeding and weed dataset, the BoniRob dataset, the  carrot crop vs. weed dataset, and the paddy-millet dataset. On the rice seeding and weed dataset, their model achieved  an F1 score of 0.8308 and an mIoU of 0.7105. On the BoniRob dataset, it attained an F1 score of 0.9097 and an mIoU  of 0.8344. Regarding the carrot crop vs. weed dataset, it obtained an F1 score of 0.8739 and an mIoU of 0.7761.  Lastly, on the paddy-millet dataset, the authors reported the mAP of 0.3023, a mAP of 0.4913, and a mAP of 0.5570  for three different threshold levels which are 10, 15, and 20 respectively. The authors specify that the threshold is the

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

6

Euclidean distance between the centers of the prediction and the ground truth, and a true positive occurs when this  distance is less than the threshold. There could be two penalties if the distance is more than the threshold. The first  penalty occurs when the detection is at the wrong location, and is called a false positive, while the second penalty  occurs when the ground truth is not detected and is known as a false negative.

An example of research focused on achieving high segmentation accuracy is the work of Fathipoor et al. (2023),  who employed a modified version of the U-Net called U-Net++ for semantic segmentation of weeds and crops in a  carrot field. U-Net++ includes nested U-shaped paths, with each path functioning as a U-Net on its own. The authors  worked with a complex dataset consisting of a small number of images with significant overlap between crops and  weeds. Their adoption of the U-Net++ architecture aimed to achieve high segmentation accuracy while maintaining  efficient inference speed. Evaluation of their model showed a mean Intersection over Union (IoU) of 81.31%,  precision of 88.84%, recall of 89.56%, and F1 score of 89.20%, outperforming the original U-Net model. Likewise,  Hu et al. (2022) constructed a U-NET++ model, however, with the addition of deep supervision, to detect weeds and  crops in sugarbeet fields. In their study, the authors compared the original U-NET with a U-NET++ model and a U- NET++ model with deep supervision. Their evaluation results indicated that the U-NET++ with deep supervision  model was better at localizing weeds, achieving an mIoU score of 92.34%. Another work that has used the U-NET++  architecture is that of Barrientos-Espillco et al. (2023) who have conducted a comparative study of multiple  segmentation architectures to test their ability to segment Cyanobacterial Harmful Algal Blooms (CyanoHABs) in  lake water. The study evaluated a U-NET++ model alongside FPN, PSPNet, and DeepLabv3 models. Each  architecture was implemented twice, once with a ResNet50 backbone and once with an EfficientNet-b6 backbone.  The results of the study concluded that the U-NET++ model with EfficientNet-b6 as its backbone was the best  performing, achieving IoU scores ranging from 94.71% to 95.75% on validation sets after training-on-training sets  without data augmentation and from 95.95% to 97.97% after training on datasets with augmentation, in addition to  having the best generalization capability of all tested models.

Lan et al. (2021) conducted a comparative analysis of different architectures for weed segmentation in a rice  field. Their objective was to identify a segmentation model with high accuracy that could be deployed on an embedded  hardware platform for real-time on-edge inference. They trained and evaluated several architectures, including the  original U-Net and the MobileNetV2-U-Net. The MobileNetV2-U-Net model performed second best, achieving an  mIoU of 78.77% and an accuracy of 92.58% after the FFB-BiSeNetV2 model. Chicchón Apaza et al. (2020), explored  multiple variants of the U-Net for semantic segmentation of crops, weeds, and soil using the Crop Weed Field Image  Dataset (CWFID). They trained four variations of the U-Net: the original U-Net, a recurrent neural network-based U- NET, a residual neural network-based U-Net, and a recurrent residual neural network-based U-Net. Evaluation results  showed the following F1 scores in order: 0.8351, 0.8917, 0.8505, and 0.8376, respectively. Additionally, they  achieved Jaccard scores of 0.9760, 0.9783, 0.9749, and 0.9740 for the respective models. Brilhador et al. (2019)  employed a slightly modified U-Net architecture for pixel-wise segmentation of crops and weeds. In their model,  Exponential Linear Unit (ELU) activation functions were used instead of the commonly used ReLU activation  functions. This choice was motivated by ELU's faster convergence and higher accuracy. Furthermore, the Adadelta  optimization algorithm was employed in place of the stochastic gradient descent (SGD) algorithm, and dropout layers  were added between convolutional layers to mitigate overfitting. This model was capable of achieving an average dice  similarity of 83.44%. Nasiri et al. (2022) constructed a ResNet50-based U-NET for detecting weeds in sugar beet  fields. They developed a new custom linear loss function to improve the model's segmentation performance. This loss  function combined the focal and dice losses to overcome challenges associated with dataset imbalance and small  region segmentation. The authors reported an accuracy of 0.9606 and an IoU score of 0.8423 for their model. Diao et  al. (2023) developed a maize row centerline detection algorithm that uses an improved U-NET network for the  system’s maize row and background segmentation stage. Their model replaces the double convolutional layers in both  the encoder and decoder paths of the original U-NET with Atrous Spatial Pyramid Pooling (ASPP) modules. This  enhancement allowed for better feature extraction and increased segmentation accuracy. The authors reported an mIoU  score of 83.23%, a mean precision of 91.79%, and an accuracy of 90.18%. Yu et al. (2022) constructed a SE-Attention  U-NET with a ResNet34 backbone for the purpose of identifying and segmenting weeds in soybean fields. The added  attention blocks allowed the network to focus on more significant target features in the feature maps of the encoder,

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

Author name / Computer Vision and Image Understanding  000 (2017) 000–000 7

suppressing the weights of unimportant features and increasing those of important ones, thereby increasing the model's  segmentation accuracy. The model returned an mIoU of 92.82% and an accuracy of 96.11%.

2.3. On edge deployment.

In many studies, weed and crop segmentation models are developed as components of larger weeding systems,  where their inference results guide weeding robots in performing real-time precise agrochemical spraying. In such  systems, segmentation models must be deployed on edge, ensuring that their inference results are obtained in real- time.

Various edge devices have been previously used, including Raspberry Pi (Chechliński et al., 2019), Nvidia Jetson  TX2 (Deng et al., 2020), and Nvidia Jetson Nano (Menshchikov et al., 2021). For example, Deng et al. (2020) deployed  an FCN-Alexnet model for weed mapping in rice fields on a Jetson TX2 module and achieved an mIoU score of 70.5%  at an inference rate of 1.2 fps. To further optimize the inference process, the model size was reduced by changing the  data precision of the network from FP32 to FP16. The resulting optimized model achieved an mIoU of 62.8% and an  inference rate of 4.5 fps. The drop in mIoU can be tolerated given the application of the model and the more important  increase in inference rate. Similarly, Chechliński et al. (2019) developed a U-Net-based custom model that combines  concepts of MobileNets, DenseNets and ResNets for weed and crop identification. Their model was deployed on a  Raspberry Pi 3B+, on which it was able to achieve a weed detection rate in the range of 47% to 67% over an inference  rate of over 10 fps. However, in contrast with Deng et al. (2020) no quantization was performed, instead their model  used a FP32 precision as quantization resulted in higher processing times. Menshchikov et al. (2021) developed a real- time system for hogweed detection from an Unmanned Aerial Vehicle (UAV). Their system utilized an optimized  FCNN architecture for the semantic segmentation of Hogweed in crop fields. Their final model was subject to width  scaling, depth scaling, and compound scaling, in which both width and depth scaling are applied simultaneously. This  scaling pipeline was applied in order to achieve a lower inference time, suitable for real-time applications. The authors  developed multiple models and then performed a comparative study on the inference time of their models on different  embedded platforms, which included Jetson Nano, RPi 3B, RPi 3B+ Intel NCS2, and Google Coral. The results of the  comparative study showed that their best model, with inference rate, AUC ROC, and power consumption taken into  consideration, was a U-NET with a width of 4 and depth of 5 that was capable of achieving an inference rate of 0.46  fps with an AUC ROC of 0.958 and a power consumption of 5.5 W deployed on a Jetson Nano. Assunção at al. (2022)  developed a real-time weed control system that utilizes a DeeplabV3 model with a MobileNet backbone for the  semantic segmentation of crops and weeds. In order to be better suited for edge deployment, aside from performing  model optimization through hyperparameter tuning, the authors also created a frozen graph of their model and then  converted it into a Tensor-RT model. Converting their model into a Tensor-RT model resulted in a reduction in model  size and consequently a faster inference time. After deploying their model on the Nvidia Jetson Nano framework and  upon evaluation, they were able to achieve an mIoU of 64% at 5.9 fps with images at a resolution of 1296x966. Qin  et al. (2021) built a real-time system for autonomous agrochemical spraying in palm plantations. The authors use an  attention-guided YOLO (Ag-YOLO) architecture to perform palm tree detection, which they quantized and reduced  the precision of to an FP16 precision and then deployed on an NCS2. After testing and evaluation, the authors reported  an average F1 score of 0.9205 at an inference rate of 36.5 fps.


## 3. Methodology and proposed solution

3.1. Dataset accusation and pre-processing

The images used in this work are obtained from the publicly available CoFly-WeedDB dataset. The dataset contains  366 RGB images captured through a DJI Phantom 4 drone from a cotton field in Larissa, Greece during the first stage  of growth (Krestenitis et al., 2022). All images were captured at a 5 m altitude and 3 m/s speed with a resolution of  1280 × 720 pixels. The original dataset includes three types of weeds namely Johnson grass, Field bindweed, and  Purslane. While the dataset provides original segmentation labels, we have found that the masks provided are  imprecise as they extend to contain soil and crop areas. Hence, we have manually labelled the dataset using Label

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

8

Studio software after dropping out empty images resulting in a dataset of 201 images that was split using an 80%,  10%, 10%, training, validation, and testing split respectively. Fig. 1. illustrates a sample image with the corresponding  pixelwise mask annotation.

Fig. 1. (a) original image captured showing Johnson Grass weeds (b) corresponding mask annotation.

3.2. Evaluation metrics

3.2.1. Intersection over Union (IoU) score.      Intersection over Union (IoU) Score, also known as Jaccard Coefficient, is used to assess the accuracy of a  detection algorithm's output bounding boxes around an object of interest in an image when compared to ground truth  boxes. Generally, a high IoU score is desirable. Equation 1 shows the formula needed to calculate IoU score for one  image.

𝑨𝒓𝒆𝒂 𝒐𝒇 𝑶𝒗𝒆𝒓𝒍𝒂𝒑

𝑨𝒓𝒆𝒂 𝒐𝒇 𝑼𝒏𝒊𝒐𝒏 (1)

IoU Score =

3.2.2. Dice score. Dice Score, also known as detection F1-Score, is similar to the IoU in terms of the main concept. However, Dice  score pays more attention towards the pixel-wise overlap between the prediction and the ground truth. Equation 2  shows the formula needed to calculate Dice score for one instant.

Dice Score = 𝟐× 𝑨𝒓𝒆𝒂 𝒐𝒇 𝑶𝒗𝒆𝒓𝒍𝒂𝒑

𝑻𝒐𝒕𝒂𝒍 𝑨𝒓𝒆𝒂 (2)

3.2.3. Frames Per Second (FPS)       Frames Per Second (FPS) is a measure used to assess how fast a machine learning model is at analyzing and  processing images. Equation 3 shows the formula needed to calculate FPS score.

𝟏 𝑰𝒏𝒇𝒆𝒓𝒆𝒏𝒄𝒆 𝑻𝒊𝒎𝒆 (3)

FPS =

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

Author name / Computer Vision and Image Understanding  000 (2017) 000–000 9

3.3. Multispectral bands extraction

To obtain more features from RGB images we divided the type of features extracted into three forms namely Hue,  Saturation, and Value (HSV) alternate color representation, Vegetation Indices (VI)s derived from light spectra, and  Edge Detectors (ED)s features which are shown in Fig. 2.

Fig. 2. All spectral bands extracted from a single RGB image divided by the type.

3.3.1. Hue, Saturation, and Value (HSV) representation

The HSV color spectrum is widely utilized in image segmentation tasks due to its ability to enhance feature  extraction, particularly at lower resolution levels (Chernov et al., 2015). Within this spectrum, the hue component (H)  captures the inherent chromatic quality of a color, including red, yellow, green, cyan, blue, magenta, and others. It  represents primary and secondary colors in addition to the continuous mixtures that occur between each adjacent color  pair. The saturation component (S) is a measurement of color purity, and it provides useful information by quantifying  the extent to which a true color is diluted by white. Lower saturation channel values produce desaturated or nearly  grey colors, whereas higher saturation channel values intensify the overall color impression. Finally, the value  component (V) serves as an analog representation of brightness. It measures a color's departure from black, indicating  the absence of luminous energy. Gradually lowering the value, or devaluing the color, produces a deeper and darker  appearance, influencing our visual perception.

3.3.2. RGB based Vegetation Indices (VI)s

An accurate set of vegetation indices is required for precision crop management, weed control, computer vision  applications and plant ecological assessments since they enhance the presence of green, vegetation features and aid in  making them stand out from the other things in the scene (Meyer & Neto, 2008). The Excess Green Index (ExG),  which may also be used to forecast NDVI levels, contrasts the green section of the spectrum against the red and blue  to distinguish vegetation from soil. It has been demonstrated to perform better than other indices that use the visible  spectrum to differentiate vegetation (Mehrotra & Srinivasan, 2019). Next, the Excess Red Index (ExR) aims to  increase the contrast of the green and red levels, respectively, highlighting the plant from other elements, such as soil  and waste. ExG and ExR when combined generate even more efficient results in segmentation (Santos et al., 2021).  Additionally, the Normalized Difference Index (NDI) is used to separate plants from soil and residue background  images. It also uses only the Green and Red channels to derive its value (Meyer & Neto, 2008). Furthermore, the

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

10

Color Index of Vegetation Vegetative (CIVE) is based on the principal component analysis of the information  contained in the RGB bands. Lastly, The OSAVI (Optimized Soil-Adjusted Vegetation Index) is a vegetation index  commonly used in remote sensing and PA applications to assess the health and vigor of vegetation, particularly in  agricultural crops. OSAVI is a modification of the Normalized Difference Vegetation Index (NDVI), which uses the  difference between the near-infrared (NIR) and red bands of the electromagnetic spectrum to measure vegetation  health. However, OSAVI considers the soil background reflectance, which can affect the accuracy of NDVI in areas  with high soil brightness. OSAVI provides a measure of vegetation health and biomass, with higher values indicating  more vigorous and healthy vegetation. It is particularly useful for analyzing agricultural crops, as it can provide  information on crop growth and yield potential. (Steven, 1998). Table 1. shows a summary of the vegetation indices  used and the corresponding formula.


> **Table 1. RGB-Based Vegetation Indices (R: Red, G: Green, B: Blue)**

Vegetation Index Equation

Excess Green Index (ExG) 2G – R + B

Excess Red Index (ExR) 1.4R – G

Color Index of Vegetation Vegetative (CIVE) 0.881G – 0.441R – 0.385B – 18.78745

Normalized Difference Index (NDI) (G – R) // (G + R)

Optimized Soil-Adjusted Vegetation Index (OSAVI) (1.5(G-R)) // ((G+R)+0.16)

3.3.3. Edge detection features

Edge detection is a process in image processing and computer vision that identifies sharp discontinuities or  edges in an image. Edge detectors are algorithms or filters that are used to detect these edges in an image. First, Canny  edge detector is a more advanced edge detector that uses a multi-stage algorithm to detect edges with higher accuracy  and lower noise compared to other methods (Canny, 1986). The Sobel operator is a common edge detection algorithm  used in image processing and computer vision. It consists of two 3x3 kernels, one for detecting edges in the x-direction  (horizontal edges) and the other for detecting edges in the y-direction (vertical edges) (Spontón & Cardelino, 2015).  The Sobel x-operator, also known as the Sobel operator for horizontal edges, is the kernel used to detect horizontal  edges in an image. On the other hand, the Sobel y-operator is the kernel used to detect vertical edges in an image. It  is also called the Sobel operator for vertical edges. By convolving an image with both the Sobel x- and y-operators, a  gradient image is obtained that highlights all the edges in the original image. The gradient image represents the  magnitude and direction of the edges in the image. This gradient image can be further processed or analyzed to detect  and extract features in the original image, such as object boundaries or corners. Lastly, Laplacian is another edge  detector which is a mathematical operator used in image processing and computer vision for edge detection and feature  extraction. The Laplacian operator is defined as the sum of the second derivatives of the image intensity function with  respect to x and y. It is a scalar quantity that represents the rate of change of the gradient magnitude in an image  (Spontón & Cardelino, 2015).

3.4. Augmentation

Image augmentation has been employed to increase the size of the training dataset. Taking into consideration that  the images are captured through a UAV, the type of augmentation applied was chosen in a way such that it can reflect  an image captured in the same method. Thereby, we decided to augment our images by horizontally flipping the  images, randomly cropping certain segments of the image, and finally by applying grid distortion on the image at  hand. Fig 3. Illustrates the three types of augmentation applied on a given sample image. Augmentation was done at  three different levels to test its influence on our proposed model performance.

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

Author name / Computer Vision and Image Understanding  000 (2017) 000–000 11

Original Image

(a) Horizontal Flip (b) Random Crop (c) Grid Distortion

Fig. 3. Augmentation types applied to the original image. (a) shows a horizontal flip of the image. (b) shows random cropping and (c) shows a  grid distortion example on the same image.

3.5. Proposed architecture

We propose a custom model that follows a U-Net based architecture to perform image segmentation of weeds in  the CoFly dataset. The model is tested in two different configurations in which the first is a straightforward U-Net  model with five levels of convolutions while the second configuration contains attention blocks (See Fig. 4) to further  investigate the influence of attention on the overall performance and in comparison, to the addition of multispectral  channels with respect to different augmentation levels. The attention mechanism applied implements a gating layer in  which spatial information extracted from the encoder layers are added with the current decoder layers which tend to  contain deeper features (Oktay et al., 2018). This way, both the spatial and feature information are retained,  normalized, resampled, and fed to the following layer. The attention block in Fig. 4 provides the procedure followed  in further detail.


> **Table 2. A comparison between on-edge devices for deployment**

Component Intel NCS2 (RPi-3B+) Nvidia Jetson Nano Google Coral (RPi-3B+)

Weight 68 grams 140 grams 113.5 grams

Data Precision FP16 FP16/FP32 FP32

Nominal Power 1.5 W + 2.1 W 5 W 2 W + 2.1 W

HW Accelerator Myriad X VPU 128-core Nvidia Maxcell GPU Google Edge TPU ML

Peak Performance 150GFLOPs 472GFLOPs 4TFLOPs

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

12

Fig. 4. The proposed U-Net based model along with the attention block mechanism.

3.6. Optimization and deployment

The Jetson Nano model chosen for this paper had 16 GBs of memory and an NVIDIA Maxwell GPU with 128  NVIDIA CUDA cores. It was equipped with 4 GB 64-bit LPDDR4 memory running at a clock frequency of 1600MHz.  Given the clear RAM and disk space limitations of our edge computing device, in addition to the latency constraints  of our real-time system, we needed to optimize the selected models before deployment. As a result, we converted the  chosen models into two optimized compressed formats using the TensorFlow Lite and Tensor-RT libraries.  Optimization through TensorFlow Lite was achieved through quantization and weight pruning. Through quantization,  the models' precision was adjusted from FP32 to FP16, effectively reducing their sizes, latency, and power  consumption. On the other hand, weight pruning trimmed low-impact parameters in the models and allowed for more  efficient model compression. Additionally, we created frozen graphs of the original models and optimized them using  the Tensor-RT library. Tensor-RT is a specialized library used for optimizing model performance for faster inference  on NVIDIA GPUs. The optimization process with Tensor-RT involved quantization, where the models' precision was  reduced to FP16, layer and tensor fusion to optimize RAM usage, kernel auto-tuning, and optimized dynamic memory  allocation to enhance execution efficiency. Table 2 provides a thorough comparison between different on-edge devices  in terms of a variety of relevant components that are vital for deployment purposes. The Intel NCS2 and Google Coral  require a host device, which in this comparison is the Raspberry Pi 3B+. Therefore, when comparing nominal power  consumption, the Raspberry Pi 3B+ consumes 2.1W, which is added to the power required by the edge device.

3.7. Power consumption, drone speed, and inference time

This section details the feasibility of our model’s deployment on a drone in a real-time setting. The camera used  in our experiment is an RPi camera module V2. Therefore, our Ground Sample Distance (GSD) calculation is done  using this camera’s specifications. The GSD is the distance, measured on the ground, between the centers of two

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

Author name / Computer Vision and Image Understanding  000 (2017) 000–000 13

consecutive pixels. It is a metric for measuring accuracy in remote sensing and aerial mapping activities (Enterprise,  2022). The following equation illustrates the GSD formula:

GSD =  Sensor Width ∗ Drone Altitude Image Width ∗ Camera Focal Length (4)

Given the RPi module’s sensor width and focal length of 2.76mm and 3.04mm respectively, and our image width  and drone altitude of 720 pixels and 5m respectively, the GSD calculates to be 0.63 cm/pixel. Therefore, the linear  length captured by the drone in a single shot at 5m altitude given our image length of 1280 pixels is 8.04m. An altitude  of 5m is estimated here since most farming applications that employ drones also maintain the same resolution.  Furthermore, the dataset over which our model is trained is also acquired at a 5m resolution. Therefore, this altitude  estimation is chosen to maintain consistency. Ideal drone speed can be calculated using the following formula:

Ideal Speed = Linear Length Captured at 5m altitude ∗ FPS (5)

Power consumption was determined after measuring the current drawn by the Nvidia Jetson Nano during model  inference. To measure the current, a Yocto-Amp device was connected between the power source and the power jack  of the Nvidia Jetson Nano. The measured current values were then saved in a CSV file. These values were iterated  over, averaged, and subsequently used to calculate the power consumption during inference using the following  equation.

Pavg = Iavg ∗Vin (6)

where Iavg is the average current drawn by the Nvidia Jetson Nano during inference, and Vin is the 5V supplied to  the Nvidia Jetson Nano by the power supply.

3.8. Bands selection As we are aiming towards an edge-enabled solution, it is not practical to cascade all possible bands on top of each  other. Such a practice would result in an increase in computational complexity, memory footprint, and does not  necessarily guarantee a better performance, in fact, it can result in a decrease in performance if not chosen  appropriately. Hence, it is recommended to use a variable selection strategy for selecting the correct bands relative to  the problem at hand. Given that both weeds and crops are vegetations, it makes sense to rely on VI bands to enhance  performance. Nonetheless, near-infrared (NIR) band is not available in consumer-affordable cameras and therefore it  is difficult to obtain weed-sensitive bands that can make weed detection task much easier. While there are promising  attempts to generate reliable NIR estimations from RGB cameras (de Lima et al., 2019; de Lima et al., 2022) using  generative adversarial networks (GAN)s as an image translation task. Such estimations are almost impossible to  generalize on other aerial images obtained from different geographical locations. For that we decided to follow a  general approach by using forward variable selection strategy to discover the best bands and enhance our model’s  performance on weed detection.


## 4. Results and discussion

4.1. Weed detection results pre-optimization.

Weed detection Results were obtained using different number of training samples; specifically, using 160 samples,  320 samples, 480 samples, and 640 samples. The weights were stored using Float-32 decimal points. Forward variable  selection was implemented at each augmentation level and the top five performing combinations of multispectral  bands were recorded. Fig.5. shows some sample outputs of the weed detection results obtained from using RGB  channels along with an additional hue band along with the corresponding IoU score. Table 3 below summarizes the  results of our custom U-Net, U-Net with attention and the best performing multispectral bands added.

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

14

Fig. 5. Weed detection results using U-Net + Hue multispectral bands.

As can be seen in Table 3, U-Net which employed the RGB bands with a single additional multispectral band  resulted in the best performing model at three different augmentation levels. Hue spectrum and Laplacian edge  detector appeared to be more informative bands than others. In general, adding an additional spectral band appears to  be as influential as adding attention blocks to our architecture with a slight difference in performance in favor of the  additional band with a range of around 4% and less computational complexity. A further look into the features  extracted shows that while the attention model captures more shape features on the decoder end of the U-Net, the  addition of a multispectral band adds more spatial information on the encoder end of the U-Net. We argue that both  methods boost the U-Net performance in two different ways leading to almost equal enhancement in the overall  performance. It is worth mentioning that combing multispectral bands with attention did not result in an improvement  in the performance of our models. We believe that this is because the information gain is the same even though both  techniques provide enhancement in opposite ends of the U-Net model. Besides, attention model can be slightly  improved by modifying the spatial to feature information gain ratio within the attention block. Nonetheless, our  empirical results showed an improvement of around 0.7% and 1.5% in terms of IoU and Dice only, hence, it is not  significant.


> **Table 3. Results obtained using different multispectral bands.**

Bands Used # Images Model IoU F32 Dice Coefficient F32

RGB (3) 160 U-Net 0.2436 0.3696

RGB (3) 160 U-Net + Attention 0.4707 0.6226

RGB + H (4) 160 U-Net 0.5066 0.6605

RGB (3) 320 U-Net 0.4475 0.6039

RGB (3) 320 U-Net + Attention 0.4705 0.6261

RGB + LAP (4) 320 U-Net 0.4992 0.6522

RGB (3) 480 U-Net 0.5192 0.6721

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

Author name / Computer Vision and Image Understanding  000 (2017) 000–000 15

RGB (3) 480 U-Net + Attention 0.5181 0.6714

RGB + LAP (4) 480 U-Net 0.5018 0.6544

RGB (3) 640 U-Net 0.4740 0.6271

RGB (3) 640 U-Net + Attention 0.4926 0.6473

RGB + H (4) 640 U-Net 0.5212 0.6736

Generally speaking, RGB bands seemed to be enough given having around a threshold of 500 images. In fact, the  simple RGB model slightly outperformed both attention and multispectral U-Net models using 480 samples with a  mean IoU score of 51.92% and a Dice score of almost 67.21% in comparison to 51.81% and 67.14% for attention  models and 50.18% and 65.44% using Laplacian edge detector in terms of mean IoU and Dice scores respectively. To  further verify these findings, the top five best performing multispectral models were plotted along with the RGB model  and attention model with a 10% margin of error. As can be seen in Fig. 6. To Fig. 9. The addition of a multispectral  band and attention were significant as long as the number of images was below the second augmentation level (480  images) in terms of IoU and Dice scores. After crossing this threshold, the RGB bands provide enough information  for the U-Net model to perform well. This is important to point out as UAVs flight time ranges between 10 to 30  minutes capturing a small number of images at that time. Additionally, the Kruskal-Wallis test for significance was  carried out for the FPS rates at each augmentation level at a significance level of 0.05. For FPS at FP32, the Kruskal- Wallis H test indicated that there is a non-significant difference between the different augmentation levels, with a  mean rank score of 5.17, 8.0, 4.5, and 8.33 for each of the four augmentation levels respectively. Given that we aim  towards a low power consuming approach, adding multispectral bands seems to be the optimal approach as it requires  a smaller number of images that are required using RGB images only and has lower computational complexity than  that required by attention models.

Fig. 6. IoU Score results of attention enhanced RGB models in

Fig. 7. IoU results of multispectral models in comparison to RGB

comparison to multispectral models and RGB

Fig. 8. Dice Score results of attention enhanced RGB models in

Fig. 9. Dice results of multispectral models in comparison to RGB

comparison to multispectral models and RGB

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

16

4.2. Weed detection results post-optimization.         In order to deploy our models on a system-on-chip (SoC), it was necessary to further optimize the model given  that SoCs are resource limited in terms of memory, speed, and power. For that, we have decided to optimize our  models by storing the weights using Float-16 decimal points and on an Nvidia Jetson Nano micro-computer. The  models were optimized using two different libraries namely, Tensor-RT which utilizes GPU capabilities and TF-lite  which relies on CPU processor to study the influence of both processors’ utilization in terms of inference time and  power consumption in addition to the performance loss due to optimization. Table 4 summarizes the results obtained  after optimization across the three different models. Extended model results, along with the forward elimination  procedure, are available in Appendix A.


> **Table 4. Results obtained using different multispectral bands after quantization.**

Bands Used # Images Model IoU F16 Dice Coefficient F16

RGB 160 U-Net 0.2437 0.3698

RGB 160 U-Net + Attention 0.4704 0.6223

RGB + H 160 U-Net 0.5069 0.6608

RGB 320 U-Net 0.4475 0.6038

RGB 320 U-Net + Attention 0.4709 0.6265

RGB + LAP 320 U-Net 0.4994 0.6523

RGB 480 U-Net 0.5192 0.6721

RGB 480 U-Net + Attention 0.5182 0.6714

RGB + LAP 480 U-Net 0.4201 0.5698

RGB 640 U-Net 0.4742 0.6273

RGB 640 U-Net + Attention 0.4925 0.6471

RGB + H 640 U-Net 0.5212 0.6735

4.3. Power consumption, inference time, and speed.


> **Table 5 shows the average performance loss due to optimization and the**

> obtained Power consumption and inference time results using the two libraries. 
Both methods resulted in a negligible loss in the overall performance with an 
average loss of 0.01% for TF-Lite and 0.005% for Tensor-RT.  However, 
utilizing a GPU using Tensor-RT resulted in a lower inference time of almost 
3 seconds with a slight increase in power consumption which is approximately 
about 0.2 Watts.  For FPS at FP16, the Kruskal-Wallis H test indicated that 
there is a non-significant difference between the different augmentation levels, 
with a mean rank score of 4.67, 8.5, 5.0, and 7.83 for each of the four 
augmentation levels respectively. Given that real time detection requires fast 
inference time, it is safe to say that utilizing a GPU would be the optimal choice 
as it improves FPS without consuming much additional power.

Fig.10. Drone speed calculation at an

altitude of 5 meters.

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

Author name / Computer Vision and Image Understanding  000 (2017) 000–000 17


> **Table 5. Results obtained using different optimization platforms**

Optimization Platform Tensorflow Lite Tensor-RT

Model Inference time (s) FPS (1/s) Power (w) Inference time (s) FPS (1/s) Power (w)

U-Net 3.6858 0.2713 4.684 0.5366 1.864 4.806

U-Net + Attention 3.5850 0.2789 4.658 0.5370 1.862 4.760

U-Net + MS 3.6415 0.2746 4.656 0.5422 1.844 4.861

Our custom U-Net model was able to achieve maximum FPS rate of approximately 2. Accordingly, the ideal drone  speed given 2 FPS for inference would be 16.08 m/s. However, drones generally have a limitation of 5 m/s on its  maximum speed. Consequently, the maximum FPS rate required given the speed of 5 m/s is 0.62, and the minimum  FPS rate required given a minimum drone speed of 1 m/s is 0.12 as can be seen in Fig. 10. By capturing non- overlapping frames, these estimated values therefore elucidate our model’s high FPS rate and subsequently its  feasibility of conducting real-time inference.

Work Architecture Dataset Edge  Device

IoU IoU on

FPS on  Edge (s)

Power consumption

Edge

(W)

Beet,  Cauliflower,

RPi- 3B+ 0.67 0.47 10 N/A

Chechliński et al.

(2019) U-Net

Cabbage

Deng et al. (2020) FCN Rice fields Jetson

TX2 0.71 N/A 1.2 N/A

(2021) U-Net Hogweed Jetson

Menshchikov et al

Nano N/A N/A 0.46 5.5

(2020) DeepLabV3 Weed Jetson

Assunção et al.

Nano 0.64 N/A 5.9 N/A

Ours (2024) U-Net CoFly-WeedDB Jetson

Nano 0.52 0.52 1.864 4.806


> **Table 6. summarizes the results of the previous works on edge. As shown in the results there is a tradeoff between**

> performance, inference time, and power consumption. There are also factors that affect the performance of the model 
such as the nature of the problem. While there is no straightforward way to compare our work with other models given 
the lack of a benchmark dataset, the obtained results seems to be consistent with those achieved by other models while 
reporting a lower power consumption, comparatively fast inference time, and high model performance retravel upon 
deployment.


## 4. Conclusion and future work

In this work, we proposed an efficient real time weed detection pipeline using UAVs while maintaining a  lightweight model and utilizing low power consumption. The model proposed achieved state-of-the-art results on the  CoFly dataset and discusses the influence of adding attention blocks and multiple multispectral bands to the model to  enhance performance. We found that edge detectors such as Laplacian detector and Hue spectrums can rapidly  improve the model’s performance especially using small number of images. We have also shown that both attention  and multispectral bands addition improve the performance in their own way on opposite ends of the U-Net  architecture. However, the information gain seems to be equal as combing both techniques does not result in an  improvement in performance. Later, the models were optimized to be suitable for on-drone deployment and the  inference time, power consumption, and required speed were computed. For future work, power consumption can be  further reduced by using LoRaWAN network modules instead of Wi-Fi networks. The reason for this is that we require  an energy efficient method to send the processed images from the drone to the farmer’s device. According to de  Carvalho Silva et al., LoRaWAN has a low power consumption and can cover a large range when compared to Wi-Fi  (2017). Additionally, the system sets the floor for further improvements such as real-time herbicide spraying, whereby

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

18

weeds are sprayed by the drone as soon as they are detected. With this approach, we reduce the farmer’s workload of  planning spraying routes. Another option would be to generate optimal field spraying routes using the generated scan  reports, where an agricultural drone can use these routes at any time to perform efficient herbicide spraying of the  field. These two potential expansions of the system would render our project a comprehensive weed management and  control system. Our image dataset could also be enhanced further to reduce pixelation and improve results using an  Enhanced Super Resolution GAN (ESRGAN) but at the cost of higher memory footprint. Additionally, NIR  estimations from similar fields can be obtained to derive more weed sensitive indices.


## 5. CRediT authorship contribution statement

Diaa Addeen Abuhani: Methodology, Software, Validation, Data Curation, Formal analysis, Investigation, Writing –  Original Draft, Writing – Review & Editing, Visualization, Project administration. Maya Haj Hussain: Software,  Validation, Data Curation, Investigation, Writing – Original Draft, Writing – Review & Editing. Jowaria Khan:  Software, Formal analysis, Investigation, Writing – Original Draft, Writing – Review & Editing. Mohamed  Elmohandes: Software, Investigation, Writing – Original Draft, Writing – Review & Editing. Imran Zualkernan:  Conceptualization, Validation, Investigation, Writing – Review & Editing, Supervision, Project administration.

Appendix A. Extended Results.

Spectral Bands #images Model Loss mIoU mF1-Score

RGB (3) 160 U-Net + Attention 0.1124 0.4707 0.6226

RGB (3) 320 U-Net + Attention 0.1309 0.4705 0.6261

RGB (3) 480 U-Net + Attention 0.1050 0.5181 0.6714

RGB (3) 640 U-Net + Attention 0.1072 0.4926 0.6473

RGB + NDI (4) 160 U-Net 0.1101 0.4778 0.6337

RGB + NDI (4) 320 U-Net 0.1060 0.4894 0.6441

RGB + NDI (4) 480 U-Net 0.0968 0.4664 0.6206

RGB + NDI (4) 640 U-Net 0.1117 0.5024 0.6550

RGB + LAP (4) 160 U-Net 0.0751 0.4919 0.6456

RGB + LAP (4) 320 U-Net 0.1049 0.4992 0.6522

RGB + LAP (4) 480 U-Net 0.1021 0.5018 0.6544

RGB + LAP (4) 640 U-Net 0.1320 0.4201 0.5698

RGB + H (4) 160 U-Net 0.108 0.5066 0.6605

RGB + H (4) 320 U-Net 0.1190 0.4482 0.6037

RGB + H (4) 480 U-Net 0.1099 0.4725 0.6240

RGB + H (4) 640 U-Net 0.1000 0.5212 0.6736

RGB + ExR (4) 160 U-Net 0.1097 0.5050 0.6572

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

Author name / Computer Vision and Image Understanding  000 (2017) 000–000 19

RGB + ExR (4) 320 U-Net 0.1064 0.4903 0.6460

RGB + ExR (4) 480 U-Net 0.1137 0.4693 0.6188

RGB + ExR (4) 640 U-Net 0.1041 0.5174 0.6188

RGB + CIVE (4) 160 U-Net 0.1012 0.4638 0.6224

RGB + CIVE (4) 320 U-Net 0.1287 0.4503 0.6077

RGB + CIVE (4) 480 U-Net 0.0921 0.4910 0.6459

RGB + CIVE (4) 640 U-Net 0.1382 0.4509 0.6033

RGB (3) 160 U-Net 0.3488 0.2436 0.3696

RGB (3) 320 U-Net 0.1214 0.4475 0.6039

RGB (3) 480 U-Net 0.1015 0.5192 0.6721

RGB (3) 640 U-Net 0.1360 0.4740 0.6271


## References

Al-Badri, A. H., Ismail, N. A., Al-Dulaimi, K., Salman, G. A., Khan, A. R., Al-Sabaawi, A., & Salam, M. S. H. (2022). Classification of weed

using machine learning techniques: a review—challenges, current and future potential techniques. Journal of Plant Diseases and

Protection, 129(4), 745–768. https://doi.org/10.1007/s41348-022-00612-9

Alchanatis, V., Ridel, L., Hetzroni, A., & Yaroslavsky, L. (2005). Weed detection in multi-spectral images of cotton fields. Computers and

Electronics in Agriculture, 47(3), 243–260. https://doi.org/10.1016/j.compag.2004.11.019

Anderson, B. B. (2020, September 28). Using Drones to More Effectively Target Weed Escapes. Soybean Research & Information Network.

Retrieved November 30, 2022, from https://soybeanresearchinfo.com/research-highlight/using-drones-to-more-effectively-target-

weed-escapes/

Arun, R. A., & Umamaheswari, S. (2022). Efficient weed segmentation with reduced residual u-net using depth-wise separable convolution

network. Journal of Scientific & Industrial Research, 81(05), 482-494. https://doi.org/10.56042/jsir.v81i05.48642

Arun, R. A., Umamaheswari, S., & Jain, A. V. (2020). Reduced U-Net architecture for classifying crop and weed using pixel-wise segmentation.

2020 IEEE International Conference for Innovation in Technology (INOCON), 1–6.

https://doi.org/10.1109/INOCON50539.2020.9298209

Assunção, E., Gaspar, P. D., Mesquita, R., Simões, M. P., Alibabaei, K., Veiros, A., & Proença, H. (2022). Real-time weed control application

using a jetson nano edge device and a spray mechanism. Remote Sensing, 14(17), 4217. https://doi.org/10.3390/rs14174217

Barrientos-Espillco, F., Gascó, E., López-González, C. I., Gómez-Silva, M. J., & Pajares, G. (2023). Semantic segmentation based on deep

learning for the detection of Cyanobacterial Harmful Algal Blooms (CyanoHABs) using synthetic images. Applied Soft Computing,

141, 110315. https://doi.org/10.1016/j.asoc.2023.110315

Bongiovanni, R., & Lowenberg-Deboer, J. (2004). Precision agriculture and sustainability. Precision Agriculture, 5(4), 359–387.

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

20

https://doi.org/10.1023/b:prag.0000040806.39604.aa

Brilhador, A., Gutoski, M., Hattori, L. T., de Souza Inácio, A., Lazzaretti, A. E., & Lopes, H. S. (2019). Classification of weeds and crops at the

pixel-level using convolutional neural networks and data augmentation. 2019 IEEE Latin American Conference on Computational

Intelligence (LA-CCI), 1–6. https://doi.org/10.1109/LA-CCI47412.2019.9037044

Canny, J. (1986). A computational approach to edge detection. IEEE Transactions on Pattern Analysis and Machine Intelligence, PAMI-8(6),

679–698. https://doi.org/10.1109/TPAMI.1986.4767851

Chechliński, Ł., Siemiątkowska, B., & Majewski, M. (2019). A system for weeds and crops Identification—Reaching over 10 FPS on Raspberry

Pi with the usage of MobileNets, DenseNet and custom modifications. Sensors, 19(17), 3787. https://doi.org/10.3390/s19173787

Chernov, V., Alander, J., & Bochko, V. (2015). Integer-based accurate conversion between RGB and HSV color spaces. Computers & Electrical

Engineering, 46, 328–337. https://doi.org/10.1016/j.compeleceng.2015.08.005

Chicchón Apaza, M. Á., Monzón, H. M. B., & Alcarria, R. (2020). Semantic segmentation of weeds and crops in multispectral images by using a

convolutional neural networks based on U-Net. In M. Botto-Tobar, M. Zambrano Vizuete, P. Torres-Carrión, S. Montes León, G.

Pizarro Vásquez, & B. Durakovic (Eds.), Applied Technologies (Vol. 1194, pp. 473–485). Springer International Publishing.

https://doi.org/10.1007/978-3-030-42520-3_38

de Carvalho Silva, J., Rodrigues, J. J. P. C., Alberti, A. M., Solic, P., & Aquino, A. L. L. (2017). LORaWAN — A Low power WAN Protocol for

Internet of Things: A review and opportunities. 2017 2nd International Multidisciplinary Conference on Computer and Energy

Science (SpliTech). https://ieeexplore.ieee.org/abstract/document/8019271

de Lima, D. C., Saqui, D., Ataky, S., Jorge, L. A. D. C., Ferreira, E. J., & Saito, J. H. (2019). Estimating agriculture NIR images from aerial RGB

data. In J. M. F. Rodrigues, P. J. S. Cardoso, J. Monteiro, R. Lam, V. V. Krzhizhanovskaya, M. H. Lees, J. J. Dongarra, & P. M. A.

Sloot (Eds.), Computational Science – ICCS 2019 (Vol. 11536, pp. 562–574). Springer International Publishing.

https://doi.org/10.1007/978-3-030-22734-0_41

de Lima, D. C., Saqui, D., Mpinda, S. A. T., & Saito, J. H. (2022). Pix2Pix network to estimate agricultural near infrared images from RGB data.

Canadian Journal of Remote Sensing, 48(2), 299–315. https://doi.org/10.1080/07038992.2021.2016056

Deng, J., Zhong, Z., Huang, H., Lan, Y., Han, Y., & Zhang, Y. (2020). Lightweight semantic segmentation network for real-time weed mapping

using unmanned aerial vehicles. Applied Sciences, 10(20), 7132. https://doi.org/10.3390/app10207132

Diao, Z., Guo, P., Zhang, B., Zhang, D., Yan, J., He, Z., Zhao, S., & Zhao, C. (2023). Maize crop row recognition algorithm based on improved

UNet network. Computers and Electronics in Agriculture, 210, 107940. https://doi.org/10.1016/j.compag.2023.107940

Enterprise, D. (2022, March 29). Ground Sample Distance | DJI Enterprise. Retrieved June 25, 2023, from https://enterprise-

insights.dji.com/blog/ground-sample-distance

Fathipoor, H., Shah-hosseini, R., & Arefi, H. (2023). Crop and weed segmentation on ground-based images using deep convolutional neural

network. ISPRS Annals of the Photogrammetry, Remote Sensing and Spatial Information Sciences, X-4/W1-2022, 195–200.

https://doi.org/10.5194/isprs-annals-X-4-W1-2022-195-2023

Ferreira, A. D. S., Freitas, D. M., Da Silva, G. G., Pistori, H., & Folhes, M. T. (2017). Weed detection in soybean crops using ConvNets.

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

Author name / Computer Vision and Image Understanding  000 (2017) 000–000 21

Computers and Electronics in Agriculture, 143, 314–324. https://doi.org/10.1016/j.compag.2017.10.027

Gebbers, R., & Adamchuk, V. I. (2010). Precision Agriculture and food security. Science, 327(5967), 828–831.

https://doi.org/10.1126/science.1183899

Hu, X.-Z., Jeon, W.-S., & Rhee, S.-Y. (2022). Sugar beets and weed detection using semantic segmentation. 2022 International Conference on

Fuzzy Theory and Its Applications (IFUZZY), 1–4. https://doi.org/10.1109/iFUZZY55320.2022.9985222

Karimi, H., Navid, H., & Dammer, K.-H. (2023). A pixel-wise segmentation model to identify Bur Chervil (Anthriscus caucalis M. Bieb.) within

images from a cereal cropping field. Gesunde Pflanzen, 75(1), 25–36. https://doi.org/10.1007/s10343-022-00764-6

Khan, A., Ilyas, T., Umraiz, M., Mannan, Z. I., & Kim, H. (2020). CED-Net: Crops and weeds segmentation for smart farming using a small

cascaded Encoder-Decoder architecture. Electronics, 9(10), 1602. https://doi.org/10.3390/electronics9101602

Khan, S., Tufail, M., Khan, M. T., Khan, Z. A., Iqbal, J., & Alam, M. (2021). A novel semi-supervised framework for UAV based crop/weed

classification. PLoS ONE, 16(5), e0251008. https://doi.org/10.1371/journal.pone.0251008

Koot, T. M. (2014). Weed detection with unmanned aerial vehicles in agricultural systems [MSc Thesis]. Wageningen University.

Krestenitis, M., Raptis, E. K., Kapoutsis, A. Ch., Ioannidis, K., Kosmatopoulos, E. B., Vrochidis, S., & Kompatsiaris, I. (2022). CoFly-WeedDB:

A UAV image dataset for weed detection and species identification. Data in Brief, 45, 108575.

https://doi.org/10.1016/j.dib.2022.108575

Lan, Y., Huang, K., Yang, C., Lei, L., Ye, J., Zhang, J., Zeng, W., Zhang, Y., & Deng, J. (2021). Real-time identification of rice weeds by UAV

low-altitude remote sensing based on improved semantic segmentation model. Remote Sensing, 13(21), 4370.

https://doi.org/10.3390/rs13214370

Ma, Z., Wang, G., Yao, J., Huang, D., Tan, H., Jia, H., & Zou, Z. (2023). An improved U-Net model based on Multi-Scale input and attention

mechanism: application for recognition of Chinese cabbage and weed. Sustainability, 15(7), 5764. https://doi.org/10.3390/su15075764

Mehrotra, N., & Srinivasan, S. (2019, January 23). Analysing drone and satellite imagery using vegetation indices. Technology for Wildlife

Foundation. https://www.techforwildlife.com/blog/2019/1/22/analysing-drone-and-satellite-imagery-using-vegetation-indices

Menshchikov, A., Shadrin, D., Prutyanov, V., Lopatkin, D., Sosnin, S., Tsykunov, E., Iakovlev, E., & Somov, A. (2021). Real-time detection of

hogweed: UAV platform empowered by deep learning. IEEE Transactions on Computers, 70(8), 1175–1188.

https://doi.org/10.1109/TC.2021.3059819

Meyer, G. E., & Neto, J. C. (2008). Verification of color vegetation indices for automated crop imaging applications. Computers and Electronics

in Agriculture, 63(2), 282–293. https://doi.org/10.1016/j.compag.2008.03.009

Milioto, A., Lottes, P., & Stachniss, C. (2018). Real-time semantic segmentation of crop and weed for precision agriculture robots leveraging

background knowledge in CNNs. arXiv. http://arxiv.org/abs/1709.06764

Nasiri, A., Omid, M., Taheri-Garavand, A., & Jafari, A. (2022). Deep learning-based precision agriculture through weed recognition in sugar beet

fields. Sustainable Computing: Informatics and Systems, 35, 100759. https://doi.org/10.1016/j.suscom.2022.100759

Oktay, O., Schlemper, J., Folgoc, L. L., Lee, M., Heinrich, M., Misawa, K., Mori, K., McDonagh, S., Hammerla, N. Y., Kainz, B., Glocker, B., &

Rueckert, D. (2018). Attention U-Net: Learning where to look for the pancreas. arXiv. http://arxiv.org/abs/1804.03999

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

22

Parra, L., Marin, J., Yousfi, S., Rincón, G., Mauri, P. V., & Lloret, J. (2020). Edge detection for weed recognition in lawns. Computers and

Electronics in Agriculture, 176, 105684. https://doi.org/10.1016/j.compag.2020.105684

Qin, Z., Wang, W., Dammer, K.-H., Guo, L., & Cao, Z. (2021). A real-time low-cost artificial intelligence system for autonomous spraying in

palm plantations. arXiv. http://arxiv.org/abs/2103.04132

Rai, M., & Ingle, A. (2012). Role of nanotechnology in agriculture with special reference to management of insect pests. Applied Microbiology

and Biotechnology, 94(2), 287–293. https://doi.org/10.1007/s00253-012-3969-4

Rosas, D. L., Gonzalez, U. G., & Huitron, V. G. (2022). A multispectral U-Net framework for crop-weed semantic segmentation. In K. L. Flores

Rodríguez, R. Ramos Alvarado, M. Barati, V. Segovia Tagle, & R. S. Velázquez González (Eds.), Recent Trends in Sustainable

Engineering (Vol. 297, pp. 15–24). Springer International Publishing. https://doi.org/10.1007/978-3-030-82064-0_2

Sahin, H. M., Miftahushudur, T., Grieve, B., & Yin, H. (2023). Segmentation of weeds and crops using multispectral imaging and CRF-enhanced

U-Net. Computers and Electronics in Agriculture, 211, 107956. https://doi.org/10.1016/j.compag.2023.107956

Santos, J., Dias Junior, J., Backes, A., & Escarpinati, M. (2021). Segmentation of agricultural images using vegetation indices. Proceedings of the

16th International Joint Conference on Computer Vision, Imaging and Computer Graphics Theory and Applications, VISAPP-4, 506–

511. https://doi.org/10.5220/0010325005060511

Spontón, H., & Cardelino, J. (2015). A review of classic edge detectors. Image Processing On Line, 5, 90–123.

https://doi.org/10.5201/ipol.2015.35

Steven, M. D. (1998). The sensitivity of the OSAVI vegetation index to observational parameters. Remote Sensing of Environment, 63(1), 49–60.

https://doi.org/10.1016/S0034-4257(97)00114-4

Su, J., Yi, D., Coombes, M., Liu, C., Zhai, X., McDonald-Maier, K., & Chen, W.-H. (2022). Spectral analysis and mapping of blackgrass weed

by leveraging machine learning and UAV multispectral imagery. Computers and Electronics in Agriculture, 192, 106621.

https://doi.org/10.1016/j.compag.2021.106621

Ullah, H. S., Asad, M. H., & Bais, A. (2021). End to end segmentation of canola field images using dilated U-Net. IEEE Access, 9, 59741–59753.

https://doi.org/10.1109/ACCESS.2021.3073715

Yu, H., Men, Z., Bi, C., & Liu, H. (2022). Research on field soybean weed identification based on an improved UNet Model combined with a

channel attention mechanism. Frontiers in Plant Science, 13, 890051. https://doi.org/10.3389/fpls.2022.890051

Zou, K., Chen, X., Wang, Y., Zhang, C., & Zhang, F. (2021a). A modified U-Net with a specific data argumentation method for semantic

segmentation of weed images in the field. Computers and Electronics in Agriculture, 187, 106242.

https://doi.org/10.1016/j.compag.2021.106242

Zou, K., Chen, X., Zhang, F., Zhou, H., & Zhang, C. (2021b). A field weed density evaluation method based on UAV imaging and modified U-

Net. Remote Sensing, 13(2), 310. https://doi.org/10.3390/rs13020310

Zou, K., Liao, Q., Zhang, F., Che, X., & Zhang, C. (2022). A segmentation network for smart weed management in wheat fields. Computers and

Electronics in Agriculture, 202, 107303. https://doi.org/10.1016/j.compag.2022.107303

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431

Preprint not peer reviewed

Title Page Template

Title:

(On-Edge Weed Detection Using Unmanned Aerial Vehicles

Author Information

Author names:

Diaa Addeen Abuhania, Maya Haj Hussaina, Mohamed Elmohandesa, Jowaria Khana, Imran Zualkernana

Affiliations:

Computer Science and Engineering Department, American University of Sharjah, Sharjah, UAE

Corresponding author:

Imran Zualkernan, izualkernan@aus.edu

For more information, please refer to the relevant sections under submission guidelines for the journal  in the Guide for Authors.

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4980431
