---
workspace_id: SCI-000981
doi: 10.3390/agriculture15141471
title: Research on Buckwheat Weed Recognition in Multispectral UAV Images Based on
  MSU-Net
authors:
- family_name: Wu
  given_name: Jinlong
  orcid: null
- family_name: Wu
  given_name: Xin
  orcid: null
- family_name: Miao
  given_name: Ronghui
  orcid: null
year: 2025
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:35:02.285550+00:00'
---

# Research on Buckwheat Weed Recognition in Multispectral UAV Images Based on MSU-Net

Article Research on Buckwheat Weed Recognition in Multispectral UAV Images Based on MSU-Net

Jinlong Wu 1,2,*, Xin Wu 3 and Ronghui Miao 1

1 College of Information Science and Engineering, Shanxi Agricultural University, Jinzhong 030800, China; miaoronghui@sxau.edu.cn 2 College of Agricultural Engineering, Shanxi Agricultural University, Jinzhong 030800, China 3 School of Comprehensive Health, Jinzhong College of Information, Jinzhong 030800, China; wuxinsx@163.com * Correspondence: wujinlong@sxau.edu.cn


## Abstract

Quickly and accurately identifying weed areas is of great significance for improving weed- ing efficiency, reducing pesticide residues, protecting soil ecological environment, and increasing crop yield and quality. Targeting low detection efficiency in complex agricultural environments and inability of multispectral input in weed recognition of minor grain based on unmanned aerial vehicles (UAVs), a semantic segmentation model for buckwheat weeds based on MSU-Net (multispectral U-shaped network) was proposed to explore the influence of different band optimizations on recognition accuracy. Five spectral features—red (R), blue (B), green (G), red edge (REdge), and near-infrared (NIR)—were collected in August when the weeds were more prominent. Based on the U-net image semantic segmentation model, the input module was improved to adaptively adjust the input bands. The neuron death caused by the original ReLU activation function may lead to misidentification, so it was replaced by the Swish function to improve the adaptability to complex inputs. Five single-band multispectral datasets and nine groups of multi-band combined data were, respectively, input into the improved MSU-Net model to verify the performance of our method. Experimental results show that in the single-band recognition results, the B band performs better than other bands, with mean pixel accuracy (mPA), mean intersection over union (mIoU), Dice, and F1 values of 0.75, 0.61, 0.87, and 0.80, respectively. In the multi-band recognition results, the R+G+B+NIR band performs better than other combined bands, with mPA, mIoU, Dice, and F1 values of 0.76, 0.65, 0.85, and 0.78, respectively. Compared with U-Net, DenseASPP, PSPNet, and DeepLabv3, our method achieved a preferable balance between model accuracy and resource consumption. These results indicate that our method can adapt to multispectral input bands and achieve good results in weed segmentation tasks. It can also provide reference for multispectral data analysis and semantic segmentation in the field of minor grain crops.

Academic Editor: Bo Xu

Received: 26 May 2025

Revised: 3 July 2025

Accepted: 8 July 2025

Published: 9 July 2025

Citation: Wu, J.; Wu, X.; Miao, R.

Research on Buckwheat Weed

Recognition in Multispectral UAV

Keywords: UAV; multispectral; buckwheat; weed identification; U-Net; MSU-Net

Images Based on MSU-Net. Agriculture

2025, 15, 1471. https://doi.org/

10.3390/agriculture15141471

Copyright: © 2025 by the authors.


## 1. Introduction

Licensee MDPI, Basel, Switzerland.

This article is an open access article

Buckwheat is an important minor grain crop in China, and it is also a typical medicinal and edible crop. With rich health benefits, it can reduce blood pressure, control diabetes, and improve digestion and cholesterol levels [1,2]. It is suitable for planting as a minor crop in Shanxi, Hebei, Gansu, and other regions of China with a cold and dry climate. In the process of planting, the planting mode of oat and buckwheat intercropping can

distributed under the terms and

conditions of the Creative Commons

Attribution (CC BY) license

(https://creativecommons.org/

licenses/by/4.0/).

Agriculture 2025, 15, 1471 https://doi.org/10.3390/agriculture15141471

Agriculture 2025, 15, 1471 2 of 21

make full use of land resources, improve crop diversity, and reduce the risk of pests and diseases. In addition, this planting mode can effectively adjust the planting structure and improve the ecological environment [3]. Oats are usually planted in early March, and buckwheat is sown after the oats are harvested, from June to July. The mutual promotion of the two crops can not only increase yield but also increase farmers’ incomes. However, the disadvantage of the planting mode is that a large number of oat weeds will emerge during the growth of buckwheat. Weeds compete with crops for water, nutrients, and sunlight, seriously threatening crop yields and agricultural sustainability. Currently, the main weeding methods include manual, mechanical, and chemical. Manual weeding is time-consuming and laborious, and cannot be applied to large-scale scenes; although mechanical weeding is efficient and labor-saving, the input and maintenance costs are high, and it is prone to damage crops; meanwhile, improper use of chemical herbicides will destroy the soil structure and ecological balance [4]. Therefore, precise spraying can effectively inhibit the growth of weeds and improve the utilization rate of herbicides. Furthermore, with the rapid development of UAVs, remote sensing technology can be used to monitor crop growth, and it also provides new ideas for precise pesticide spraying.

Accurate and reliable weed identification is the key to intelligent weeding [5]. The application of deep learning technology in precision agriculture is becoming increasingly widespread. It can handle segmentation problems of complex background and large field of view, thereby effectively improving the accuracy of weed identification [6]. But there are complex spatial dependencies and remote context information in remote sensing im- ages, and traditional deep learning image semantic segmentation models are no longer able to achieve accurate segmentation. Due to its rich spatial, radiometric, spectral, and temporal information, multispectral or hyper-spectral data in UAVs has been widely used in crop growth monitoring [7], pest and disease detection [8,9], environmental quality monitoring [10], and other fields. Faced with complex situations such as different lighting conditions, shadows between crops, and similarities in appearance between weeds and crops, the recognition results in RGB data are mostly unsatisfactory. The spectral informa- tion provided by RGB three-band data is limited, making it difficult to better distinguish crops and weeds through spectra. Meanwhile, multispectral data can provide high-quality data for complex farmland environments. Furthermore, the REdge and NIR bands are sensitive to the chlorophyll content and cell structure of crops, ensuring efficient weed identification [11]. A single invisible light band cannot provide sufficient information to comprehensively assess crop health and environmental changes. Environmental factors such as soil type, topography, and lighting conditions will affect the measurements of REdge and NIR bands [12]. The effective fusion of visible and invisible bands in multispectral and hyperspectral data can reduce environmental interference and improve the accuracy and reliability of identification results. Multispectral data is an important component of the multimodal data system. Multispectral-based weed recognition research can provide key semantic information and the spatial distribution of weeds and is a high-quality data source for subsequent weed infestation rate prediction [13]. Therefore, integrating deep learning semantic segmentation technology with multispectral technology can better achieve weed recognition in buckwheat fields.

Researchers have applied multispectral UAV data to weed identification in corn, sugar vegetables, rice, and other crops. Yan et al. [14] explored the feasibility of barnyard grass identification using UAV hyperspectral data in complex rice field environments and drew spatial distribution and density maps of barnyard grass. Zhao et al. [15] took corn and weeds in UAV multispectral remote sensing images as research objects and extracted the vegetation index, texture, and reflectivity to realize semantic segmentation of corn and weeds. However, most of the above studies use machine learning algorithms

Agriculture 2025, 15, 1471 3 of 21

for manual feature selection and extraction to achieve pixel-level image segmentation; they rely too much on expert experience, which leads to limited generalization ability and difficulty in modeling nonlinear data. Xu et al. [16] proposed an improved path aggregation network (PANet) semantic segmentation model for weed segmentation in UAV multispectral images and respectively constructed datasets of near-infrared, red, and normalized difference vegetation index (NDVI) for model training; the experimental results showed that the model trained with three channels (near-infrared + red + NDVI) had the highest F1 value of 0.872. Although several studies have demonstrated notable success in combining multispectral images with segmentation models, limitations remain regarding the number of inputs and negative inputs. Deep-learning-based segmentation models can only deal with RGB (red, green, and blue) three-channel color images, and most studies focus on improving the backbone and feature fusion networks. However, there are relatively few studies on the optimization of model input. The three-channel band input cannot directly process the original multispectral data. Researchers usually use artificial methods to synthesize vegetation indices, color features, etc., and realize model input. In summary, in order to fully utilize the advantages of high-resolution and deep learning semantic segmentation models of UAV multispectral remote sensing data and fill the research gap in the application of minor grain crops, this study took a buckwheat experimental field in Taigu District, Jinzhong City, Shanxi Province, China, as the research area and carried out buckwheat weed recognition. The main contributions are as follows:

(1) The spectral information of red, blue, green, red edge, and near-infrared bands were obtained, and the performance of single-band and multi-band combination inputs for buckwheat weed identification were explored.

(2) The U-Net semantic segmentation model was improved to realize multi-band adaptive inputs, so as to obtain the optimal band for buckwheat weed identification under the multispectral remote sensing UAV platform.

(3) The distribution of weeds in the buckwheat field was obtained, which provided reference for the path and dosage planning of weeding by UAV crop protection.

The remainder of this study is organized as follows. The proposed methods are introduced in detail in Section 2. Then, Section 3 describes experiments conducted with the proposed method on single-band, multi-band, and other segmentation models and presents large-scene field maps of weeds in order to verify the effectiveness of our method. Section 4 discusses the performance of our method. Conclusions are presented in Section 5.


## 2. Materials and Methods

2.1. General Situation of Research Area

The research area was located in the buckwheat research experimental field of Shanxi Agricultural University in Shenfeng Village, Taigu District, Jinzhong City, Shanxi Province, China (37◦26′2.4′′~37◦26′06′′ N,112◦35′34.8′′~112◦35′42.0′′ E), with a total area of 80 acres. It has a temperate continental monsoon climate, with an average annual temperature and precipitation of 10.5 ◦C and 434.9 mm. The rainy season lasted from July to September, accounting for about 60% of the total precipitation. The average annual sunshine hours was 2407, with four distinct seasons and sufficient sunshine, and it was suitable for the cultivation of minor grain crops such as buckwheat and oats. The sowing time of buckwheat in this area was from June to July 2023, and the harvesting time was from September to October. The planting variety of buckwheat was “Jinqiao No.1” (Shanxi, China). Since the research object of this paper was the identification of weeds, we did not interfere with the growth of weeds. Data collection was conducted in August, when weeds were more obvious, which can provide reference for the last weeding before buckwheat ridge

Agriculture 2025, 15, 1471 4 of 21

sealing. Figure 1 shows the geographical location of the research area and the buckwheat experimental field.


> **Figure 1. Geographical location of the research area and buckwheat experimental field. (a) Geograph-**

> ical location of the research area (Shanxi province). (b) Geographical location of the research area
(Jinzhong city). (c) The buckwheat experimental field.

2.2. UAV Image Acquisition

The aerial image acquisition equipment was the DJI PHANTOM 4 (Shenzhen, China) multispectral version UAV (Figure 2), which integrated a visible light camera and five multispectral cameras (red, green, blue, near-infrared, and red edge spectra). It can achieve visible light and multispectral imaging. The image size was 1600 pixels × 1300 pixels, and the image format was TIFF. Each camera had a resolution of 2 million pixels and was equipped with a three-axis gimbal for stable and clear imaging. The parameters of the multispectral cameras are shown in Table 1.

Red edge Near infrared Green

Visible Red Blue

(a)  (b)


> **Figure 2. UAV multispectral image acquisition equipment. (a) DJI PHANTOM 4 multispectral version**

> UAV. (b) Imaging system of DJI PHANTOM 4 multispectral version UAV.


> **Table 1. Multispectral sensor parameters.**

Band Number Band Name Center Wavelength Band Width

1 Red, R 650 nm 16 nm 2 Green, G 560 nm 16 nm 3 Blue, B 450 nm 16 nm 4 Near-infrared, NIR 840 nm 16 nm 5 Red edge, REdge 730 nm 16 nm

Agriculture 2025, 15, 1471 5 of 21

In this study, the UAV adopted a TimeSync time synchronization system, which synchronized the flight control, camera, and real-time kinematic (RTK) clock system to achieve millisecond-level errors in camera imaging time. The real-time compensation module combines the center position of each camera lens, the center position of the antenna, and the device posture information to obtain more accurate position information in the image. In data collection, the professional edition of GS Pro (Ground Station Pro) was used for route planning, task execution, and flight speed management. The date of data collection was 5 August 2023. Aerial parameter settings: the flight height was 30 m; the flight speed was 2.6 m/s; the ground sample distance (GSD) was 0.82 cm/pixel; the heading overlap rate was 80%; the lateral overlap rate was 70%.

In order to achieve visualization of multispectral UAV data, the PIX4Dmapper 4.5.6 data processing software (Lausanne, Switzerland) was used to generate orthophoto maps. After image stitching, calibration, and slicing operations, visualized images of each band can be obtained. Figure 3 shows the multispectral sample images obtained from the same plot; Figure 3a–e are grayscale images of the R, G, B, NIR, and REdge bands, respectively. As can be seen from Figure 3, compared with red, green, and blue band images, the difference between crops and weeds in near-infrared and red band images is more significant, which will be further discussed in the subsequent data analysis process.

(a)  (b)  (c)  (d)  (e)


> **Figure 3. Multispectral sample image of buckwheat weeds. (a) R. (b) G. (c) B. (d) NIR. (e) REdge.**

2.3. Multispectral Image Annotation

Before the closure of buckwheat ridges, weeds and buckwheat are dense and continu- ous, and it is difficult to distinguish individual weeds from a canopy perspective. Under such intricate circumstances, weed recognition requires pixel-accurate classification, effec- tively turning it into an image segmentation task. The annotation of multispectral images is basically similar to traditional RGB images. This study used Labelme 5.5.0 (Massachusetts, USA) to annotate the obtained images. Since Labelme cannot directly read multispectral data, RGB images obtained by visible light sensors on the same plot were annotated. Partial RGB sample images and their corresponding annotated images are shown in Figure 4. In Figure 4, there were two representative plots; Figure 4a shows an irregular edge plot image, while Figure 4c shows a more regular one. In Figure 4a, the seeder cannot work normally, and there were varieties of weeds, making weed information relatively complicated. In Figure 4c, as the planting mode was oats intercropping buckwheat, the weeds were usually the fallen oats, and the weed information was relatively simple. As the flight height was 30 m, it was impossible to accurately distinguish weed types at this height. Therefore, all types of weeds were uniformly labeled as one category, which was represented in red, and the buckwheat was labeled in black. The annotation file format was JSON, and the file was subsequently converted to PNG.

Agriculture 2025, 15, 1471 6 of 21

(a)  (b)  (c)  (d)


> **Figure 4. Partial RGB sample images and their annotated result images. (a) Sample image 1.**

> (b) Annotation result of sample image 1. (c) Sample image 2. (d) Annotation result of sample image 2.

2.4. Multispectral Image Preprocessing

The range of the three channels in RGB images is from 0 to 255, while there is no clear pattern in the values of each band in multispectral data, and the maximum value of each band is also different. The multispectral data needed to be standardized, and the calculation formula is shown in Equation (1).

b = Xb −µb

X′

(1)

σb

where Xb is the original data of a certain band, µb is the mean value of the band, σb is the standard deviation of the band, and X′b is the standardized data of the band. Through Equation (1), the original data was transformed into a standard normal distribution, which helps to eliminate the influence between different characteristic dimensions.

The multispectral UAV data usually consists of a small dataset, and it cannot meet the requirements of commonly used deep learning semantic segmentation models. Data augmentation was needed to improve the generalization ability of the model. At present, common data augmentation methods are based on RGB images, which cannot be directly applied to multispectral images in TIFF format. Therefore, the data augmentation method was improved in this study. Firstly, a five-dimensional dataset was generated by merging the five single-band datasets. Then, common methods such as horizontal flipping, vertical flipping, random rotation, gaussian blur, etc., were used for data augmentation. Due to the particularity of multispectral data, data augmentation methods such as brightness and contrast cannot be used. Finally, the augmented data was written into the multispectral TIFF data. In this paper, eleven methods including sharpen, gaussian noise, horizontal flip, vertical flip, rotation, gaussian blur, and five sets of affine transformations were used for data augmentation. In order to improve the diversity of the samples, five methods of the above eleven were randomly selected for each multispectral sample to achieve data augmentation.

2.5. Construction of a Buckwheat Weed Recognition Model Based on UAV Multispectral Images

The identification of buckwheat weeds based on UAV images can evaluate the dis- tribution of weeds throughout the entire field. Quantifying the distribution of weeds can provide a foundation for precise spraying of herbicides and path planning of intelligent weeding machines, thus achieving automatic, efficient, and accurate weed identification. The images collected by UAV usually have high resolution, and the weeds are densely distributed, making it impossible to detect individual weed plants. Therefore, this study adopted image segmentation methods to achieve buckwheat weed recognition in UAV multispectral images, optimizing existing image segmentation techniques to make them applicable to multimodal input.

Agriculture 2025, 15, 1471 7 of 21

At present, the commonly used deep learning image segmentation models are mostly applied to RGB images, which cannot be directly applied to multispectral images. Therefore, it is necessary to optimize and improve the input and activation functions of the model. The U-Net model is a common image semantic segmentation model proposed by Ronneberger et al. [17] in 2015. With simple structure and strong expansibility, it has been widely used in fields such as medical imaging, remote sensing imaging, and intelligent driving [18,19]. Compared with other semantic segmentation models, the biggest advantage of U-Net is that it does not rely on large datasets, but it can still achieve an ideal effect by training with small sample datasets [20]. Therefore, the main improvement strategy of MSU-Net involved modifying the input module of the U-Net semantic segmentation network and improving the activation functions. The modified input module enabled it to directly read multispectral data and adaptively adjust the model input based on the number of channels. The improved MSU-Net model can combine multispectral data with semantic segmentation models to fully utilize the multispectral information, ultimately achieving high-precision identification of weeds in buckwheat fields.

2.5.1. U-Net Image Semantic Segmentation Model

The U-Net model usually consists of three parts: encoder, decoder, and skip connections. (1) The encoder employs a down-sampling process where each stage consists of two consecutive 3 × 3 convolutional layers with ReLU activations and a max pooling operation.

This part utilizes pooling layers to reduce spatial resolution while maintaining the number of channels, ultimately reducing information complexity and achieving image feature extraction [21,22].

(2) The decoder performs up-sampling through a structure typically symmetrical to the encoder. Each up-sampling operation consists of two 3 × 3 de-convolution layers, which are concatenated to improve the resolution of the feature map and ultimately achieve the same resolution output as the input image.

(3) The skip connections concatenate encoder and decoder feature maps of correspond- ing scales, effectively combining multi-level feature information to preserve spatial details and enhance segmentation accuracy.

The network structure of U-Net is shown in Figure 5, where the blue arrows represent the convolutional block, the gray arrows are the copy and crop blocks, the red arrows represent the down-sampling block, the green arrows represent the up-sampling block, the yellow arrows represent the convolutional layer, Conv 3 × 3 represents a convolution operation with a kernel size of 3 × 3, copy and crop represent cropping in the channel dimension, max pool 3 × 3 represents the maximum pooling down-sampling with a convolution kernel size of 3 × 3, up conv 2 × 2 represents up-sampling with a convolution kernel size of 2 × 2, and conv 1 × 1 represents a convolution operation with a kernel size of 1 × 1.

2.5.2. MSU-Net Image Semantic Segmentation Model

The improvement of U-Net mainly includes the input module and activation function. The network structure of the improved MSU-Net weed image segmentation model is shown in Figure 6. Multi-channel input can accept multi-source data and complete deep feature extraction during the encoding stage, which fully utilizes the spectral information of multispectral remote sensing images. In the encoding and decoding process, the Swish activation function was adopted instead of the original ReLU function. In classification and segmentation tasks, Swish performs better than ReLU and is more adaptable and efficient for complex inputs. As multispectral cameras cannot construct large-scale datasets, a skip connection in MSU-Net was used to connect the feature maps in the encoding and the

Agriculture 2025, 15, 1471 8 of 21

decoding stage. The incorporation of skip connections facilitates the effective utilization of multi-level feature information and helps maintain the efficiency of feature extraction. Due to its unique U-shaped network structure, skip connections, efficient feature extraction, and fusion capabilities, MSU-Net still has good segmentation performance in small sample situations.

conv 3×3,ReLU copy and crop max pool 3×3 up conv 2×2 conv 1×1


> **Figure 5. Network structure of the U-Net image semantic segmentation model.**

Multi spectral data  adaptive channel input

conv 3×3,Swish copy and crop max pool 3×3 up conv 2×2 conv 1×1


> **Figure 6. Network structure of the MSU-Net weed segmentation model.**

(1) Improvement of the multispectral input module. The multispectral data collected by UAV includes five bands: R, G, B, REdge, and NIR. Specifically, R, G, and B are common visible bands, while REdge and NIR are invisible ones. R, G, and B bands can form digital images, which can be used for extracting color features, texture features, shape features, etc. REdge and NIR can be used for extracting spectral features such as NDVI and normalized difference water index (NDWI). The traditional U-Net model is mainly designed for processing commonly used RGB images, and it cannot directly process multispectral data. At present, there is relatively little research on image segmentation networks for multispectral data. The most common method is to read TIFF format multispectral data and

Agriculture 2025, 15, 1471 9 of 21

manually select bands to construct model inputs. However, the above methods are limited and can only verify the combination inputs involving three channels. Therefore, this paper proposed an MSU-Net model to be well-suited for handling multispectral data inputs. The pseudocode of the improved multispectral input module is shown in Algorithm 1.

Algorithm 1: Adaptive multispectral band input module of MSU-Net

Input: multispectral data Xin = {x1, x2, x3, . . ., xi, . . ., xn},

xi = {xR, xG, xB, xREdge, xNIR}, multispectral selection input Bands = {BR, BG, BB, BREdge, BNIR} Output: multispectral output data Xout = {x1, x2, x3, . . .. . ., xn} 1: for i ∈{1, 2, . . .. . ., n} do 2: if file suffix = “tiff” then 3: obtain Bands 4: read the selected multispectral data Xout according to the Bands 5: for j ∈{0, 1, . . .. . ., nBands−1} do 6: if Band[j] = True then 7: read the selected multispectral data to Xout 8: end if 9: end for 10: Calculate the number_channels according Bands 11: else 12: process the data in the regular image format (“png”, “jpg”, etc.) 13: number_channels = 3 14: end if 15: end for 16: Set the number of input channels of the U-Net network to number_channels.

The specific improvement methods were as follows: (a) A multispectral selection function was integrated into the input module of the original U-Net architecture.

(b) The default three-channel input was replaced with a variable parameter, num- ber_channels. This allowed for dynamic configuration of input channels and supported the development of an adaptive module for multispectral band selection.

The improved MSU-Net can directly read multispectral data and achieve the combina- tion of different multispectral bands, overcoming the previous limitation of three channels. At the same time, it can adaptively adjust the input channel according to the number of extracted bands.

(2) Improvement of loss function. Multispectral data contains rich spectral information and can be used to extract features such as color, shape, texture, and vegetation indices. However, it is prone to problems such as information redundancy and model convergence. In the encoding stage, the correlation between multiple channels should be reasonably utilized to extract classification features with significant differences between weeds and crops. In U-Net, ReLU activation function is usually used to introduce nonlinear factors so as to improve the expressive ability of the model, but this function sets all negative outputs to 0. When there is a negative input, it will lead to the loss of information and incorrect recognition. Therefore, in this study, ReLU was replaced by the Swish activation function. Even if the input is negative, Swish can produce non-zero gradient, thus avoiding the problem of neuron death of ReLU [23].

Agriculture 2025, 15, 1471 10 of 21

2.6. Model Operating Environment and Evaluation Parameters 2.6.1. Model Operating Environment and Parameters

The MSU-Net semantic segmentation model ran on Windows 10 with an Intel (R) Core (TM) CPU model i7-12700F@2.10 GHz. The GPU was an NVIDIA GeForce RTX 3080, with 32 GB of RAM and 1 TB of mechanical hard disk. The programming language was Python 3.9. The deep learning framework was Pytorch 1.13.0. The GPU acceleration libraries were CUDA11.7 and CUDNN8.4.1. The input image resolution was 256 pixels × 256 pixels. The learning rate was 1 × 10−5. The weight attenuation index was 1 × 10−8, and the training epoch was 200.

2.6.2. Model Evaluation Indicators

To evaluate the performance of the segmentation model, mPA [24], mIoU [25], Dice coefficient [26], and F1 score were selected as evaluation indicators. Among them, mPA refers to the average pixel accuracy of all categories, and pixel accuracy (PA) is defined as the ratio of correctly classified pixels to the total number of pixels, which can reflect the overall performance of the model on all categories. MIoU is the average intersection over union (IoU) of all categories, which is used to measure the degree between the predicted and the actual segmentation results. The Dice coefficient is a set similarity measure, which is used to measure the similarity between the predicted and actual results, and the higher the value, the better the predicted results. The F1 score is the harmonic mean of precision and recall, which is used to measure the accuracy and completeness of the model. The calculation formulas are shown in Equations (2)–(7).

k ∑ i=0

pii ∑k

mPA = 1 k + 1

(2)

j=0 pij

k ∑ i=0

pii ∑k

MIoU = 1 k + 1

(3)

j=0 pij + ∑k

j=0 pji −pii

Dice = 2TP 2TP + FP + FN (4)

P = TP TP + FP (5)

R = TP TP + FN (6)

F1 = 2 P · R

P + R (7)

where k is the number of pixels, pii represents the total number of pixels belonging to class i and predicted as class i (TP), pjj represents the total number of pixels actually belonging to class j and predicted as class j (TN), pij represents the total number of pixels originally belonging to class i but predicted as class j (FP), pji represents the total number of pixels belonging to class j but predicted as class i (FN), P is precision, and R is recall.


## 3. Results

3.1. Multispectral Characteristic Analysis Results


> **Figure 7 shows the statistics of DN (digital number) values of two sample images**

> corresponding to different bands of TIFF data, in which the abscissa represents the DN
value of the band, and the ordinate represents the statistical value (frequency of occurrence)
of DN values in this band of a certain plot. As can be seen from Figure 7, the distribution of
R, G, B, and REdge bands conform to a normal distribution, while the NIR band exhibits a

Agriculture 2025, 15, 1471 11 of 21

clear bimodal property. When the DN value is in the range of 750~2500, the R band can better distinguish weeds from the background, and this range accounts for 75.85% of the total DN range. When the DN value is in the range of 2600~7800, the G band can better distinguish weeds from the background, and this range accounts for 68.43% of the total DN range. When the DN value is in the range of 1500~5800, the B band can better distinguish weeds from the background, and this range accounts for 69.45% of the total DN range. When the DN value is in the range of 3500~14,000, the NIR band can better distinguish weeds from the background, and this range accounts for 96.25% of the total DN range. When the DN value is in the range of 2800~11,500, the REdge band can better distinguish weeds from background, and this range accounts for 75.03% of the total DN range. To sum up, the range of distinguishable DN values of weeds and background in the five bands accounts for more than 68% of the total range, which indicates that it is feasible to identify and segment weeds and background based on multispectral data.

Sample image 1  Sample image 2

R

G

B

NIR


> **Figure 7. Cont.**

Agriculture 2025, 15, 1471 12 of 21

REdge


> **Figure 7. DN statistics of two sample images corresponding to different bands.**

3.2. Multispectral Single-Band Weed Identification Results

The five-band multispectral data was input into the segmentation model to verify the performance of each band in buckwheat weed identification. In this study, the effects of the R, B, G, NIR, and REdge bands on the segmentation results were compared and analyzed, and the experimental results are shown in Figure 8. As can be seen from Figure 8, when the input is single-band data, the five multispectral bands can basically identify the specific position of weeds. In the visible bands, the segmentation results of the B and R bands were better; when weeds appear in patches (sample image 1 and sample image 3), the segmentation effect of the G band was better, but when the distribution of weeds is not concentrated and the weed blocks are small (sample image 2), there will be misidentification. NIR was similar to the G band; the same problem existed that the identification effect was not good when the weed block is small. The overall segmentation results of the REdge band were good, which basically meets the needs of buckwheat weed recognition.

In this paper, mPA, mIoU, Dice, and F1 were used to evaluate the performance of single-band weed identification results, and the experimental results are shown in Table 2. According to Table 2, the mPA, mIoU, Dice, and F1 values of the B band were 0.75, 0.61, 0.87, and 0.80, respectively, which were all higher than other bands. In the subsequent selection of the optimal multispectral combination, the focus will be on studying the combination of the B band with other bands. The overall differences of mPA, mIoU, Dice, and F1 values between the R, G and NIR bands were not significant, and the recognition results were average. The experimental results of REgde were the worst, with the lowest mPA, mIoU, Dice, and F1 values. The four evaluation indicators can reflect the influence of different bands on weed identification well. Although the actual segmentation result of the REdge band in Figure 8 was unsatisfactory, it still has a certain advantage in identifying weed details, which can be used as the basis for multi-band combination input. Through experiments on weed recognition with single-band data, it was found that all five bands of the multispectral data contribute to the recognition task, providing theoretical reference for the initialization of multispectral combinations.


> **Table 2. Comparison results of single-band weed identification.**

Evaluation Indicators

Band

mPA mIoU Dice F1

R 0.74 0.49 0.66 0.61 G 0.75 0.48 0.60 0.59 B 0.75 0.61 0.87 0.80 NIR 0.71 0.48 0.68 0.63 REdge 0.63 0.41 0.62 0.56

Agriculture 2025, 15, 1471 13 of 21

Sample image 1

Sample image 2 Sample image 3

Sample

images

Annotation

images

R

G

B

NIR

REdge


> **Figure 8. Single-band weed recognition results.**

3.3. Multispectral Combination Weed Identification Results

When single-band data was used as the input of the network model, weeds can be identified, but the recognition performance was relatively poor. It is necessary to further explore the influence of multispectral combined data on segmentation performance. In order to make full use of the band information of multispectral remote sensing images, this paper designed nine groups of multispectral combinations (R+G+B, NIR+REdge,

Agriculture 2025, 15, 1471 14 of 21

R+G+B+NIR+REdge, R+G+B+REdge, R+G+B+NIR, B+NIR, B+REdge, R+B+REdge, and R+B+NIR) for experiments. Through comparative experiments, the optimal multispectral combination for weed recognition was obtained, which provides a research foundation for buckwheat UAV weed recognition based on multispectral data. Table 3 shows the identification results of multispectral combinations.


> **Table 3. Comparison results of multispectral combination weed identification.**

Band Evaluation Indicators

Multi-Band Combination Number

R G B NIR REdge mPA mIoU Dice F1

1 √ √ √ 0.75 0.64 0.85 0.78 2 √ √ 0.69 0.50 0.73 0.66 3 √ √ √ √ √ 0.73 0.62 0.85 0.76 4 √ √ √ √ 0.73 060 0.78 0.72 5 √ √ √ √ 0.76 0.65 0.85 0.78 6 √ √ 0.73 0.60 0.82 0.75 7 √ √ 0.75 0.62 0.84 0.76 8 √ √ √ 0.77 0.61 0.81 0.75 9 √ √ √ 0.66 0.46 0.65 0.58

As can be seen from Table 3, the combination of R+G+B bands achieves better seg- mentation performance, and its mPA, mIoU, Dice, and F1 values were all high, in which the value of Dice can reach up to 0.85. Compared with R+G+B, the performance of NIR+REdge bands was relatively poor. Therefore, in practical application, it is not rec- ommended to identify and analyze crop weeds by using invisible bands alone. Although the R+G+B+NIR+REdge full band combination provides abundant information for weed identification, with a Dice value of up to 0.85, compared with R+G+B bands, its mPA, mIoU, Dice, and F1 values were lower. It can be seen that a higher number of bands input into the model is not necessarily better, and it is still necessary to search for the best multispectral combination to ensure optimal segmentation performance and computational complexity. Similarly, the R+G+B+NIR band combination performs the best, with mPA, mIoU, Dice, and F1 values of 0.76, 0.65, 0.85, and 0.78, respectively, and this combination was optimal.


> **Figure 9 shows the image segmentation results of four optimal combinations: R+G+B,**

> NIR+REdge, R+G+B+NIR+REdge, and R+G+B+NIR. As can be seen from Figure 9, the
four sets of bands can achieve weed segmentation well. When weeds appear in patches
(sample image 1 and sample image 3), the recognition effect of NIR+REdge was poor, and
there was missing detection. When the distribution of weeds is not concentrated and the
weed blocks are small (sample image 2), the segmentation results of all the four sets were
good. Through comparison experiments, the R+G+B+NIR band combination was the best,
which can better realize weed identification.

3.4. Comparative Experiments of Different Activation Functions

To verify the effectiveness of the Swish activation function in our method, we replaced the original ReLU activation function with Sigmod [27], LeakyReLU [28], Mish [29], and Swish and conducted five sets of comparative experiments. The experimental results are shown in Table 4. The quantitative results reveal that replacing ReLU with LeakyReLU, Sigmod, Mish, and Swish led to an increase in all the evaluation indicators. Specifically, compared with ReLU, the mPA of Sigmod and Mish was slightly improved by 4% and 5%, respectively, while LeakyReLU remained the same; the mIoU of Sigmod, LeakyReLU, and Mish was improved by 9%, 4%, and 8%, respectively; the Dice of the three activation functions was improved by 5%, 2%, and 6%, respectively; the F1 of the three activation

Agriculture 2025, 15, 1471 15 of 21

functions was improved by 5%, 2%, and 5%, respectively. Notably, Swish performs the best, with mPA, mIoU, Dice and F1 values of 0.76, 0.65, 0.85, and 0.78, and the mPA, mIoU, Dice, and F1 were improved by 6%, 9%, 6%, and 6% respectively. These results demonstrate that Swish outperforms ReLU, Sigmod, LeakyReLU, and Mish activation functions in the task of multispectral buckwheat weed segmentation by UAV.

Sample image 1

Sample image 2 Sample image 3

Sample

images

R+G+B

NIR+ REdge

R+G+B +NIR+REdge

R+G+B

+NIR


> **Figure 9. Multispectral combination weed recognition results.**

Agriculture 2025, 15, 1471 16 of 21


> **Table 4. Experimental results of different activation functions.**

Evaluation Indicators

Models

ReLU Sigmod LeakyReLU Mish Swish mPA mIoU Dice F1

MSU-Net √ 0.70 0.56 0.79 0.72 MSU-Net √ 0.74 0.65 0.84 0.77 MSU-Net √ 0.70 0.60 0.81 0.74 MSU-Net √ 0.75 0.64 0.85 0.77 MSU-Net √ 0.76 0.65 0.85 0.78

3.5. Comparison Results of Different Semantic Segmentation Models

To further validate the advantages of the proposed algorithm, this paper compared it with commonly used deep semantic segmentation models (DenseASPP [30], PSPNet [31], and DeepLabv3 [32]), as well as the original U-Net model. To ensure a comprehensive evaluation, this comparison focuses on mPA, mIoU, Dice, F1, as well as memory consump- tion, parameters, FLOPs (floating-point operations), and FPS (frames per second). Table 5 shows the experimental results of different models. Since MSU-Net, DenseASPP, PSPNet, DeepLabv3, and U-Net only support three-channel input, the universal visible light images of RGB with three channels were selected as the input. Meanwhile, the optimal combination band R+G+B+NIR was selected as the input of the improved MSU-Net model.


> **Table 5. Comparison results of different semantic segmentation models.**

Bands Evaluation Indicators

Memory Consump-

Models

Parameters FLOPs/G FPS/(f·s−1)

R G B NIR mPA mIoU Dice F1

tion/MB

U-Net √ √ √ 0.75 0.64 0.85 0.78 98.00 2.80 × 107 53.64 56.36 DenseASPP √ √ √ 0.76 0.59 0.72 0.72 40.50 9.17 × 106 10.77 13.5 PSPNet √ √ √ 0.72 0.55 0.69 0.70 264.81 6.56 × 107 63.94 9.2 DeepLabv3 √ √ √ 0.79 0.62 0.75 0.75 237.68 5.86 × 107 60.53 12.8 MSU-Net √ √ √ √ 0.76 0.65 0.85 0.78 118.00 3.10 × 107 54.78 77.18

From Table 5, the experimental result of MSU-Net was close to U-Net, with a slightly higher performance than U-Net. Among all models, PSPNet performs the worst with the lowest values of mPA, mIoU, Dice, and F1. Compared with DenseASPP, PSPNet, and DeepLabv3, the mIoU was improved by 6%, 10%, and 3%, respectively; the Dice was improved by 13%, 16%, and 10%, respectively; and the F1 was improved by 6%, 8%, and 3%, respectively. In particular, the mPA fluctuated to some extent, since it represented the average PA for each category, and the background areas in this paper were relatively large, while the weed areas were relatively small, which may lead to higher mPA. Therefore, in the application scenario of this paper, a high mPA does not necessarily mean good segmentation results. In practical applications, in order to comprehensively evaluate the segmentation effect, other factors and evaluation indicators should be considered.

The memory consumption, parameters, and FLOPs of DenseASPP were the lowest compared with the other models, indicating that its computational complexity and demand for computational resources are much lower. However, the values of mPA, mIoU, Dice, and F1 of DenseASPP were unsatisfactory, and computational complexity should be considered while maintaining recognition accuracy. In contrast, the memory consumption, parameters, and FLOPs of PSPNet were the highest, and light weight was needed to reduce resource consumption and improve inference speed. In summary, considering all evaluation indi- cators comprehensively, the MSU-Net model in this paper achieved a preferable balance between model accuracy and resource consumption.

Agriculture 2025, 15, 1471 17 of 21


> **Figure 10 shows the segmentation results of different models on the self-built UAV**

> buckwheat weed dataset. As indicated in Figure 10, U-Net and MSU-Net perform well in
weed detail segmentation. The segmentation result of DenseASPP was worse than that of
U-Net and MSU-Net; when the distribution of weeds is not concentrated and the weed
blocks are small (sample image 2), some areas were not identified. Conversely, PSPNet
and DeepLabv3 perform poorly, with large areas of weeds connected (sample image 1 and
sample image 3) and lacking detailed segmentation (sample image 2), demonstrating their
limitations in finer detail segmentation.

Sample image 1

Sample image 2 Sample image 3

Sample

images

U-Net

DenseASPP

PSPNet

DeepLabv3

MSU-Net


> **Figure 10. Comparison results of different semantic segmentation models.**

Agriculture 2025, 15, 1471 18 of 21

3.6. Construction of a UAV Weed Map in Large Scenes

The ultimate goal of using multispectral data to identify weeds in buckwheat fields is to assist weeding operations in path planning and variable spraying. Therefore, it is of great significance to construct a weed map in a large scene for realizing precise agricultural management, improving farmland monitoring efficiency, reducing environmental pollution, and promoting green agriculture. With high resolution, the original multispectral data needs to be processed by a sliding block. In this paper, the sliding step size was 256 pixels, and the window size was 256 pixels × 256 pixels. There is no overlap between the obtained multispectral data. Then, weeds recognition was performed on the subgraph data obtained after the sliding block. Finally, a large-scene buckwheat weed map was obtained by splicing the weed identification results. Figure 10 shows the weed map in large scenes.

Images in three situations, namely, weed concentration, edge field, and common field, were selected for weed mapping. The optimal multispectral combination R+G+B+NIR bands was used in the process of model training and recognition. From Figure 11, it can be seen that in large-scene images, the distribution of buckwheat crop rows is more obvious, and weeds mostly exist between crop rows and are more concentrated in distribution. In Figure 11a, there is a mound in the experimental field, which makes it impossible to plant buckwheat. The weed distribution is concentrated, and the method proposed in this paper can effectively identify the weed concentration areas. Figure 11b shows the edge field area, and our method can effectively identify the distribution of weeds and effectively remove the influence of roads. Figure 11c is a common weed area in the field, and the identification effect is good. In summary, the method proposed in this paper can effectively construct maps of weed distribution under large scenarios, providing reference for path planning of weeding machinery.

(a)  (b)  (c)

(d)  (e)  (f)


> **Figure 11. Construction results of a UAV weed map in large scenes. (a) Large-scene image of weed**

> concentration. (b) Large-scene image of edge field. (c) Large-scene image of common field. (d) Weed
map of weed concentration. (e) Weed map of edge field. (f) Weed map of common field.

Agriculture 2025, 15, 1471 19 of 21


## 4. Discussion

This paper proposed a buckwheat weed recognition model named MSU-Net based on multispectral remote sensing data, and the self-built buckwheat weed multispectral data was verified and tested by experiments. Researchers have applied multispectral UAV data to citrus tree crown segmentation [33] and weed mapping [34], with optimal band combinations of R+B+NIR and R+G+NIR, respectively. Although the experimental results were satisfactory, they were unable to overcome the limitation of three-channel input. However, our method can adapt the number of input bands and performs well in prediction accuracy and inference speed.

In order to verify the performance of single–band data in buckwheat weed identi- fication, this paper compared and analyzed the effects of five bands—R, B, G, NIR, and REdge—on the segmentation results. The recognition result of the B band was the best, with the highest mPA, mIoU, Dice, and F1 values of 0.75, 0.61, 0.87, and 0.80, respectively, which were higher than others.

In order to fully utilize the band information of multispectral remote sensing images, a comparative analysis was conducted on the nine multispectral combinations of R+G+B, NIR+REdge, R+G+B+NIR+REdge, R+G+B+REdge, R+G+B+NIR, B+NIR, B+REdge, and R+B+REdge. The segmentation performance of the R+G+B+NIR band combination was the best, with mPA, mIoU, Dice, and F1 values of 0.76, 0.65, 0.85, and 0.78, respectively. This indicated that using a multi-band combination can better achieve weed recognition.

To further validate the advantages of the proposed algorithm, a comparative analysis was conducted based on U-Net, DenseASPP, PSPNet, and DeepLabv3. Considering all evaluation indicators comprehensively, the MSU-Net model in this paper achieved a preferable balance between model accuracy and resource consumption.

Large-scene UAV weed maps were constructed to improve agricultural management efficiency and promote the development of agriculture towards sustainability and intelli- gence. The algorithm in this paper can effectively identify weed areas in three situations of weed concentration, edge field, and common field. Weed maps combined with biological control or mechanical weeding technology can reduce the pollution of chemical agents to the environment and agricultural products.


## 5. Conclusions

The buckwheat weed identification model based on multispectral UAV data performs well in the task of weed segmentation, which proves the advantages of spectral features in semantic segmentation of remote sensing images. However, the resolution of the mul- tispectral camera is lower than that of the RGB sensor. Multispectral data can provide more spectral information, and its low resolution also limits its contribution to weed iden- tification. Subsequent research needs to fuse multispectral and RGB data, make full use of spectral information and combine the advantages of high resolution of RGB data, and finally realize high-precision segmentation of buckwheat weed identification by UAV. At present, deep learning semantic segmentation models are mostly aimed at RGB images, and the number of input channels is limited. This article focuses on the adaptive implemen- tation of multi-channel input modules, which is universal in both theoretical design and technical implementation. This study is an important foundation and key technical support for the multimodal weed infestation rate prediction system, providing the system with high-reliability information at the spectral level and playing a key role in the multimodal fusion mechanism. In the future, the model should be further applied to fields of other minor grain crops such as sorghum, millet, oats, and various public datasets to improve the stability and generality of the model.

Agriculture 2025, 15, 1471 20 of 21

Author Contributions: Conceptualization, J.W. and R.M.; methodology, J.W.; software, X.W.; vali- dation, J.W. and X.W.; investigation, X.W.; data curation, R.M.; writing—original draft preparation, R.M.; writing—review and editing, J.W.; visualization, X.W.; supervision, J.W. All authors have read and agreed to the published version of the manuscript.

Funding: This research was funded by the Shanxi Province Applied Basic Research Youth Project (No. 202203021212428 and No. 202203021212414).

Institutional Review Board Statement: Not applicable.

Data Availability Statement: All data needed to evaluate the conclusions in this paper is present in the paper. Further inquiries can be directed to the corresponding author.

Conflicts of Interest: The authors declare no conflicts of interest.


## References

1. Randell-Singleton, T.; Wright-Smith, H.E.; Hand, L.C.; Vance, J.; Culpepper, A. Identifying herbicides to manage weeds in a buckwheat cover crop and for the control of volunteers. Crop Forage Turfgrass Manag. 2025, 11, e70034. 2. Platov, Y.T.; Beletskii, S.L.; Metlenkin, D.A.; Platova, R.A. Identification and Classification of Buckwheat Grain by Microfocus Radiography and Hyperspectral Imaging Methods. Russ. J. Nondestruct. Test. 2024, 60, 446–454. 3. Ribeiro da Silva Lima, L.; Barros Santos, M.C.; PGomes, P.W.; Fernández-Ochoa, Á.; Simões Larraz Ferreira, M. Overview of the Metabolite Composition and Antioxidant Capacity of Seven Major and Minor Cereal Crops and Their Milling Fractions. J. Agric. Food Chem. 2024, 72, 22. 4. Rhioui, W.; Figuigui, J.A.; Belmalha, S. Assessing the Impact of Organic and Chemical Herbicides on Agronomic Parameters, Yield, and Weed Control Efficiency in Lentil (Lens culinaris Medik.) under a Direct-Seeding System: A Comparative analysis. BIO Web Conf. 2024, 109, 9. 5. Guo, Z.; Cai, D.; Jin, Z.; Xu, T.; Yu, F. Research on unmanned aerial vehicle (UAV) rice field weed sensing image segmentation method based on CNN-transformer. Comput. Electron. Agric. 2025, 229, 109719. 6. Lan, Y.; Huang, K.; Yang, C.; Lei, L.; Ye, J.; Zhang, J.; Zeng, W.; Zhang, Y.; Deng, J. Real-Time Identification of Rice Weeds by UAV Low-Altitude Remote Sensing Based on Improved Semantic Segmentation Model. Remote Sens. 2021, 13, 4370. 7. Guo, L.; Chen, Z.; Ma, Y.; Bian, M.; Fan, Y.; Chen, R.; Liu, Y.; Feng, H. Estimation of Potato LAI Using UAV Multispectral and Multiband Combioned Textures. Spectrosc. Spectr. Anal. 2024, 44, 3443–3454. 8. Song, Y.; Chen, B.; Wang, Q.; Wang, J.; Zhao, J.; Sun, L.; Chen, Z.; Han, Y.; Wang, F.; Fu, J. Estimation of Yield Loss in Diseased Cotton Fields Using UAV Multi-Spectral Images. Trans. Chin. Soc. Agric. Eng. 2022, 38, 175–183. 9. Wang, C.; Chen, Y.; Xiao, Z.; Zeng, X.; Tang, S.; Lin, F.; Zhang, L.; Meng, X.; Liu, S. Cotton Blight Identification with Ground Framed Canopy Photo-Assisted Multispectral UAV Images. Agronomy 2023, 13, 1222. [CrossRef] 10. Lu, Y.; Duan, J. Pond Water Quality Analysis and Visualization Design Utilizing Unmanned Aerial Vehicle Multi-Spectral Technology. Bull. Surv. Mapp. 2024, 6, 127. 11. Wan, L.; Ryu, Y.; Dechant, B.; Lee, J.; Zhong, Z.; Feng, H. Improving retrieval of leaf chlorophyll content from Sentinel-2 and Landsat-7/8 imagery by correcting for canopy structural effects. Remote Sens. Environ. 2024, 304, 114048. 12. Zhang, W.; Fan, M.; Yang, R.; Li, Z.; Qiu, Y.; Dong, M.; Song, P.; Wang, N.; Yang, Y.; Wang, Q. New features of edge-selectively hydroxylated graphene nanosheets as nir-ii photothermal agent and sonothermal agent for tumor therapy. J. Mater. Chem. B Mater. Biol. Med. 2024, 12, 13. 13. Huang, Y.; Wu, Z.; Liu, Z. Multimodal weed infestation rate prediction framework for efficient farmland management. Comput. Electron. Agric. 2025, 235, 110294. 14. Yan, Z.; Shen, Y.; Tang, W.; Zhang, Y.; Zhou, H. Unmanned Aerial Vehicle Hyperspectral Imaging for Weeds Identification and Spatial Distribution in Paddy Fields. Acta Laser Biol. Sin. 2024, 33, 335–346. 15. Zhao, J.; Li, Z.; Lu, L.; Jia, P.; Yang, H.; Lan, Y. Weed Identification in Maize Field Based on Multi-Spectral Remote Sensing of Unmanned Aerial Vehicle. Sci. Agric. Sin. 2020, 53, 1545–1555. 16. Xu, G.; Huang, M.; Huang, J. Weed segmentation in multispectral images of unmanned aerial vehicles based on improved semantic segmentation model. Jiangsu Agric. Sci. 2022, 50, 212–220. 17. Ronneberger, O.; Fischer, P.; Brox, T. U-Net: Convolutional Networks for Biomedical Image Segmentation. In Medical Image Computing and Computer-Assisted Intervention–MICCAI 2015: 18th International Conference, Munich, Germany, 5–9 October 2015; Springer International Publishing: Berlin, Germany, 2015; pp. 234–241. 18. Wang, H.; Wu, G.; Liu, Y. Efficient Generative-Adversarial U-Net for Multi-Organ Medical Image Segmentation. J. Imaging 2025, 11, 19.

Agriculture 2025, 15, 1471 21 of 21

19. Lim, K.; Ko, J.; Hwang, Y.; Lee, S.; Kim, S. TransRAUNet: A Deep Neural Network with Reverse Attention Module Using HU Windowing Augmentation for Robust Liver Vessel Segmentation in Full Resolution of CT Images. Diagnostics. Diagnostics 2025, 15, 118. 20. Wang, Z.; Ma, J.; Guo, Y.; Zhou, C.; Bai, B.; Li, F. Cloud removal in multitemporal remote sensing imagery combining U-Net and spatiotemporal generative networks. Natl. Remote Sens. Bull. 2024, 28, 2089–2100. 21. Hattie, S.; Mark, B.; Siu-Lun, Y.; Natasha, M.; Ben, M.; Jeyan, T. ContinUNet: Fast deep radio image segmentation in the Square Kilometre Array era with U-Net. RAS Tech. Instrum. 2024, 3, 315–332. 22. Zhang, Q.; Qi, W.; Zheng, H.; Shen, X. CU-Net: A U-Net architecture for efficient brain-tumor segmentation on BraTS 2019 dataset. In Proceedings of the 2024 4th International Conference on Machine Learning and Intelligent Systems Engineering (MLISE), Zhuhai, China, 28–30 June 2024; pp. 255–258. 23. Darooei, R.; Nazari, M.; Kafieh, R.; Rabbani, H. Loss-modified transformer-based U-Net for accurate segmentation of fluids in optical coherence tomography images of retinal diseases. J. Med. Signals Sens. 2023, 13, 253–260. [PubMed] 24. Wang, Y.; Chu, M.; Kang, X.; Liu, G. A deep learning approach combining DeepLabV3+ and improved YOLOv5 to detect dairy cow mastitis. Comput. Electron. Agric. 2024, 216, 108507. 25. Tang, C.; Zou, J.; Xiong, Y.; Liang, B.; Zhang, W. Automatic reconstruction of closely packed fabric composite RVEs using yarn-level micro-CT images processed by convolutional neural networks (CNNs) and based on physical characteristics. Compos. Sci. Technol. 2024, 252, 110616. 26. Rani, P.; Kumar, P.; Babulal, K.; Kumar, S. Interpolation of Erythrocytes and Leukocytes Microscopic image using MsR-CNN with Yolo v9 Model. Discov. Comput. 2025, 28, 18. 27. Pratiwi, H.; Windarto, A.; Susliansyah, S.; Susilowati, S.; Rahayu, L.; Fitriani, Y.; Merdekawati, A.; Rahadjeng, I. Sigmoid activation function in selecting the best model of artificial neural networks. J. Phys. Conf. Ser. IOP Publ. 2020, 1471, 012010. 28. Satsangi, A.; Jain, S. Strategic Feature Extraction for Improved Seizure Detection: A Tanh and LeakyReLU Activated Neural Network Model. In Proceedings of the World Conference on Artificial Intelligence: Advances and Applications, Singapore, 22–23 February 2024; pp. 289–300. 29. Zhang, Z.; Yang, Z.; Sun, Y.; Wu, Y.; Xing, Y. Lenet-5 convolution neural network with mish activation function and fixed memory step gradient descent method. In Proceedings of the 2019 16th International Computer Conference on Wavelet Active Media Technology and Information Processing, Chengdu, China, 13–15 December 2019; pp. 196–199. 30. Hu, P.; Li, X.; Tian, Y.; Tang, T.; Zhou, T.; Bai, X. Automatic pancreas segmentation in CT images with distance-based saliency- aware DenseASPP network. IEEE J. Biomed. Health Inform. 2020, 25, 1601–1611. 31. Yan, L.; Liu, D.; Xiang, Q.; Luo, Y.; Wang, T.; Wu, D.; Chen, H.; Zhang, Y.; Li, Q. PSP net-based automatic segmentation network model for prostate magnetic resonance imaging. Comput. Methods Programs Biomed. 2021, 207, 106211. 32. Yang, C.; Ashraf, M.; Riaz, M.; Umwanzavugaye, P.; Chipusu, K.; Huang, H.; Xu, Y. Enhanced thyroid nodule detection and diagnosis: A mobile-optimized DeepLabV3+ approach for clinical deployments. Front. Physiol. 2025, 16, 1457197. 33. Song, H.; You, H.; Liu, Y.; Tang, X.; Chen, J. Deep Learning-based Segmentation of Citrus Tree Canopy form UAV Multispectral Images. For. Eng. 2023, 39, 140–149. 34. Afroditi, T.; Thomas, A.; Xanthoula, P.; Anastasia, L.; Javid, K.; Dimitris, K.; Georgios, K.; Dimitrios, M. Application of Multilayer Perceptron with Automatic Relevance Determination on Weed Mapping Using UAV Multispectral Imagery. Sensors 2017, 17, 2307. [CrossRef]

Disclaimer/Publisher’s Note: The statements, opinions and data contained in all publications are solely those of the individual author(s) and contributor(s) and not of MDPI and/or the editor(s). MDPI and/or the editor(s) disclaim responsibility for any injury to people or property resulting from any ideas, methods, instructions or products referred to in the content.
