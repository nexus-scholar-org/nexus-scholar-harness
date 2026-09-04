---
workspace_id: SCI-001368
doi: 10.1109/urtc60662.2023.10534990
title: 'Kernelytics: Multispectral Drone Imagery and Deep Learning for Early Corn
  Assessment'
authors:
- family_name: Aplin
  given_name: Oliver
  orcid: null
- family_name: Famolari
  given_name: Kavya
  orcid: null
- family_name: Liu
  given_name: Sophia
  orcid: null
- family_name: Mehta
  given_name: Bhaumik
  orcid: null
- family_name: Xiong
  given_name: Max
  orcid: null
- family_name: Mesham
  given_name: Michael
  orcid: null
- family_name: Jafari
  given_name: Mohsen
  orcid: null
year: 2023
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:42.095592+00:00'
---

# Kernelytics: Multispectral Drone Imagery and Deep Learning for Early Corn Assessment

Kernelytics: Multispectral Drone Imagery and Deep

Learning for Early Corn Assessment

Oliver Aplin*

Kavya Famolari*

Sophia Liu*

Bhaumik Mehta*

oeaplin@gmail.com

kfamolari@gmail.com

sophia.ch102@gmail.com

bhaumikmehta343@gmail.com

Max Xiong*

Michael Mesham**

Dr. Mohsen Jafari**

mxiong24@rutgersprep.org

mjm796@rutgers.edu

jafari@soe.rutgers.edu

*New Jersey Governor’s School of Engineering & Technology, Rutgers University–New Brunswick, NJ, USA **Corresponding Author *All indicated authors contributed equally to this paper

2023 IEEE MIT Undergraduate Research Technology Conference (URTC) | 979-8-3503-0965-2/23/$31.00 ©2023 IEEE | DOI: 10.1109/URTC60662.2023.10534990

stand count, crop and weed area, and plant health on early corn crops.


## Abstract—Rising

pressures
from
climate
change
and
population growth have prompted farmers to explore modern
technologies, such as drones and artificial intelligence to optimize
conventional and manual crop monitoring practices. We present
a new algorithm, Kernelytics, to efficiently assess corn fields
early in the season, producing more optimal yields, allocating
resources more efficiently, and identifying corn health issues
earlier in the season. The proposed experimental procedure
utilizes a low-cost drone to collect aerial images of the Visible
Light, Red, Green, Blue, Near-Infrared (NIR), and Red Edge
bands.
After
preprocessing
the
collected
data,
Kernelytics
involves
three
machine
learning-based
assessments:
object
detection for corn stand count, semantic segmentation for plant
and weed area, and instance segmentation for plant health. The
research additionally determines the optimal model type, image
size, and band combinations for each task.

II. RELATED WORK

This section describes past research on UAVs, machine learning, and image processing for corn detection and health assessment.

Past research demonstrates the potential of using UAV-based imagery to capture high-resolution RGB (red, green, blue) images for detecting and analyzing corn. For instance, Gnadinger and Schmidhalter [2] utilized image processing to identify and count corn plants from UAV aerial imaging. The study first enhanced the contrast of the images in MATLAB, then detected and counted green pixels within images with an error less than or equal to 5%. Since weeds and corn plants have the same spectral reflectance on the visible spectrum, weed-free conditions on the fields are a requirement for their procedure.

Keywords—multispectral imagery, remote sensing, computer vision, precision agriculture

I. INTRODUCTION Corn, the highest globally produced crop, holds mass importance in the farming industry and global economy. During the 2022-2023 marketing year, corn crops spanned 201 million hectares of planted area globally and produced over 1,440 million metric tons of food [1]. Once harvested, corn is processed into livestock feed, fuel ethanol, starch, sweeteners, and more.

Moreover, Kitano et al. [3] examined the performance of a U-Net deep learning model in automating corn detection and stand counting, comparing model performance on different plant densities, flight heights, and growth stages. The study utilized a low-cost UAV along with an RGB sensor for imaging.

To assess plant health, Barzin et al. [4] utilized multispectral UAV imagery in combination with machine learning to predict the nitrogen levels in corn leaves. Specifically, they compared the performance of eight different models and different combinations of multispectral bands and vegetation indices. Their gradient boosting and random forest models were the best-fitted models, with a coefficient of determination of approximately 80%.

As with many other crop industries, the corn industry has seen a significant increase in interest in precision agriculture in recent years. Precision agriculture is the farm management strategy of utilizing data analytics and technologies–such as unmanned aerial vehicles (UAVs) and artificial intelligence–to monitor and assess crops. It enables as-needed and site-specific farming, where farmers can determine specific areas that require treatment and the optimal type and amount of treatment (eg. water, herbicides, pesticides, and fertilizers) to apply. Thus, precision agriculture improves conventional methods of agriculture by creating significant savings for farmers while reducing food and resource waste.

This paper expands on previous studies, which mainly focused on isolated assessments of individual crop field metrics, by introducing a cohesive workflow to evaluate multiple facets of early corn crops–stand count, crop and weed area, and health–with data collected in one drone flight. By incorporating multiple assessments into a unified process, the

The purpose of this research is to leverage multispectral drone imagery and deep learning to perform evaluations of

979-8-3503-0965-2/23/$31.00 ©2023 IEEE

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:44:46 UTC from IEEE Xplore.  Restrictions apply.

study allows farmers to gain a holistic understanding of their fields and to maximize insight while minimizing cost and resource use.

III. BACKGROUND

A. Unmanned Aerial Vehicles (UAVs) and Multispectral Imagery

Unmanned aerial vehicles (UAVs) are a common component in precision agriculture applications because they capture images at higher resolutions than traditional satellite technologies and enable multispectral imagery [5]. Multispectral imagery is the collection of image data from specific wavelength ranges, or spectral bands, on the electromagnetic spectrum.

Fig. 2: CNN Architecture [9].

1) Object Detection: Object detection is the task of performing image classification for the individual objects within an image and localizing them with a bounding box. Object detection models include Single Shot Detector (SSD) and You Only Look Once (YOLO) [10] [11].

B. Normalized Difference Vegetation Index (NDVI)

The Normalized Difference Vegetation Index (NDVI) is a well-established metric to estimate overall plant health using remote sensing data. The NDVI is based on the reflectance and absorbance properties of plants, under red light and near-infrared waves. Specifically, the chlorophyll in plants absorbs red light while the chloroplasts reflect near-infrared (NIR) wavelengths [6]. Thus, healthy, photosynthetically active vegetation will have a high reflectance of near-infrared waves while reflecting little red light. On the other hand, unhealthy vegetation yields a smaller difference between the two reflectance rates, as demonstrated in Figure 1.

2) Semantic Segmentation: Semantic segmentation models classify pixels within an image but do not differentiate between two instances of the same class. A common semantic segmentation model is the U-Net, which has shown strong performance in precision agriculture tasks [12].

3) Instance Segmentation: Instance segmentation models classify objects within an image and delineate their shape with a pixel mask. Multiple instances of the same class are distinguished as separate segments. One example of an instance segmentation model is Mask R-CNN [13].

D. Pix4D Software and Orthomosaic Maps

Pix4D is an image processing software that specializes in photogrammetry–the process of stitching together images to make a digital model of a physical place. By identifying key reference points in the overlap between hundreds or thousands of images, Pix4D can construct a large, detailed image known as an orthomosaic map, as shown in Figure 3.

Fig. 1: Reflectance of spectral bands for healthy and unhealthy plants and NDVI formula [7].

Equation 1 details the calculation of this index. The NDVI index ranges from -1 to 1 with healthier vegetation reaching values closer to 1 [8].

NDVI = NIR −Red

NIR + Red (1)

C. Convolutional Neural Networks

Fig. 3: Orthomosaic map of a corn field at Creggan Hill Farm constructed in Pix4D.

Convolutional neural networks (CNNs) are a type of neural network that are advantageous for extracting features and patterns from image data. The two key layers of a CNN–convolutional and pooling layers–help extract high-level features from images, as seen in Figure 2. Convolutional neural networks are frequently applied for computer vision tasks, such as object detection, semantic segmentation, and instance segmentation.

E. ArcGIS and Data Processing

ArcGIS is a Geographic Information System that assists in visualizing and analyzing geographic data. It can be used to process and analyze multispectral imagery, and to develop deep learning models. ArcGIS enables various data

2

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:44:46 UTC from IEEE Xplore.  Restrictions apply.

preprocessing and postprocessing techniques, such as contrast stretching and non-maximum suppression.

chip tile size and band combination. Specifically, a composite combination containing all five spectral band layers and an NDVI combination containing only the NDVI layer were compared.

In ArcGIS, contrast stretching via the standard deviation stretch function can be used to linearly transform pixel intensity values to span a more extensive range, making subtle differences more discernible. Moreover, Non-Maximum Suppression (NMS) is a post-processing technique used to filter out redundant bounding boxes from object detection models. NMS aims to retain only the most confident and non-overlapping bounding boxes for each detected object instance.

V. DEEP LEARNING

Deep learning models were developed for object detection, semantic segmentation, and instance segmentation. Single Shot Detector (SSD) and YOLO models were used for object detection, and hyperparameter tuning was conducted to optimize image chip tile size and band combination. The U-Net was utilized for semantic segmentation and the Mask R-CNN for instance segmentation. Hyperparameter tuning was conducted to optimize image chip size for both model types.

IV. EXPERIMENTAL PROCEDURE

A. Data Collection

Aerial images were collected with a DJI Phantom 4 Multispectral Agriculture Drone at Creggan Hill Farm in Troupsburg, New York. The Phantom 4 collects data from six separate camera sensors detecting Visible Light (RGB), Red, Red Edge, Blue, Green, and Near Infrared wavelengths. The drone unit costs $6,499.00 [14].

The models were trained with a fixed batch size of 8, a learning rate determined by ArcGIS’s learning rate finder, and a train-validation split of 90-10. The SSD, U-Net, and Mask R-CNN architectures utilized a Resnet-101 backbone. The YOLO architecture used a Darknet-53 backbone. Validation loss-based early stopping was implemented to prevent overfitting. Metrics such as accuracy, precision, recall, and F1 score were considered to select the optimal model for each task. Once the optimal object detection, semantic segmentation, and instance segmentation models were determined, they were utilized to estimate stand count, crop and weed area, and the health of individual plants, respectively. For object detection and instance segmentation, a non-maximum suppression was applied with a threshold of 0.2.

The drone was flown over a 7.62-acre field of Roundup Ready corn. The data was collected on June 20, 2023, during an early corn growth stage when the juvenile corn stood at 4 inches in height. The drone’s flight path was predetermined utilizing the DJI Ground Station Pro software.

The drone completed its mapping by producing 655 images–containing data from the visible light camera and each of the five sensors–taken at a height of 38.1 meters with a resolution of 2 cm/pixel. The drone also collected unique metadata for each image, such as location data, radial and tangential lens distortion, and positioning data. Using Pix4D, the drone images were stitched together into an orthomosaic map.

VI. RESULTS

A. Object Detection Models Results

The validation accuracy of SSD and YOLO models trained with various hyperparameter combinations can be found in Table I.

B. Data Preprocessing and Labeling

The orthomosaic map produced by Pix4D contained six layers corresponding to each of the drone’s sensor types: visible light, red, green, blue, red edge, and near-infrared. Once exported to ArcGIS, an additional layer derived from NDVI values was created. A standard deviation stretch function was applied to the orthomosaic map to improve contrast.

TABLE I: Validation accuracy of object detection models using different combinations of hyperparameters

Tile size 128

Tile size 256

Tile size 64

SSD Yolo NDVI 48 35 Comp 63 39

SSD Yolo 50 31 80 30

SSD Yolo 65 6 15 15

Then, individual corn plants were manually identified and labeled using image classification tools within ArcGIS. Seven patches of the field were randomly selected for image annotation. Two types of image annotation were used: bounding boxes were drawn around the juvenile corn crops to be used for object detection models and pixel segments were created for instance and semantic segmentation models. For corn, a total of 625 bounding boxes were drawn for object detection, and a total of 1,500 pixel segments were drawn for segmentation. For weeds, a total of 1,200 pixel segments were drawn. The labeled orthomosaic map was then broken down into image chips and exported as training data for deep learning. Different types of image chips were used to evaluate how model performance was influenced by image

The models’ performance indicated certain trends. Firstly, the models trained on the composite bands consistently outperformed those trained on the NDVI band. This may be because the values in the NDVI band are derived from the spectral band values of the composite combination. Furthermore, the results suggest that tile size has a significant impact on model accuracy, although the specific relationship between the two is not clear. Finally, SSD models outperformed the YOLO models for all tile sizes and band combinations.

The SSD model utilizing the composite band and a tile size of 128x128 pixels was identified as the optimal model and

3

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:44:46 UTC from IEEE Xplore.  Restrictions apply.

used to estimate the stand count. The model’s corn detections on a subsection of the field can be seen in Figure 4.

a result of the models falsely detecting a number of weeds and bushes on the edge of the field as corn.

The Mask R-CNN model with the composite band and an image chip tile size of 32x32 pixels achieved the highest precision score for instance segmentation.

TABLE III: Precision of Tile Size 32 and 64 Mask R-CNN Models

Tile 32 Tile 64 Precision 65 47

D. Stand Count

Stand count is determined by counting the number of detections the model made across the entire field. Only the object detection and instance segmentation models were used because they are able to isolate individual crops. Results of detection are summarized in table IV.

Fig. 4: Bounding boxes generated by the optimal SSD model.

B. Semantic Segmentation Models Results

TABLE IV: Stand Count Estimation from SSD and Mask R-CNN

The performance metrics and results for the U-Net models for corn segmentation can be found in Table II. The F1 score for corn greatly improves with a lower tile size, while the F1 score for non-corn remains relatively consistent. These results can potentially be attributed to the data generation process: image chips of a larger tile size contain more unlabeled corn, which leads to inconsistencies when evaluating model performance.

MODEL TYPE STAND COUNT

SSD Object Detection 56320 Mask R-CNN Instance Segmentation 65475

The difference between SSD and Mask R-CNN estimates may be due to the excess amount of weeds and bushes on the edge of the field that the Mask R-CNN detects as corn.

TABLE II: Metrics of Tile Size 32 and 64 U-Net Models

E. Crop and Weed Area

Tile size 32

Tile size 64

After semantic segmentation was applied to the entire field using the optimized U-Net model, the total area of corn plants was estimated to be 936.95 square meters and the total area of weeds was estimated to be 1217.29 square meters.

Non-Corn Corn Precision 97 72 Recall 98 60 F1 98 66

Non-Corn Corn Precision 98 63 Recall 99 39 F1 98 48

F. Plant Health

The U-Net model with the composite band and an image chip tile size of 32x32 pixels had the best performance for corn segmentation. A U-Net model of the same structure trained on the weed data achieved an accuracy of 98% for weed segmentation. The corn and weed segments generated by this model are shown in Figure 5.

As shown in Figure 6, image segmentation masks were overlaid on top of the field orthomosaic map to detect and localize plants and evaluate their health. The color of the segmentation mask reflects the plant’s mean NDVI value. Red indicates an NDVI value below 0.21 and signifies that a plant needs heavy inspection. Orange indicates an NDVI value between 0.21 and 0.33 and signifies that the corn is in poor condition. Light green indicates an NDVI value between 0.33 and 0.45, meaning the corn is in relatively good condition. Finally, dark green indicates an NDVI value above 0.81 and means that a plant is healthy.

Fig. 5: Image segments generated by the optimized U-Net model for crop (left) and weed area (right)

C. Instance Segmentation Models Results

For instance segmentation we used the Mask R-CNN model architecture. Table III details the precision of the models tested. The results also indicated that a smaller tile size improved model performance. The lower precisions may be

Fig. 6: Mean NDVI values overlaid on top of plant image segments.

4

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:44:46 UTC from IEEE Xplore.  Restrictions apply.

VII. CONCLUSIONS

management and assistance; Michael Mesham for his patience and expertise; Residential Teaching Assistant Trinity Pham for her support; Residential Teaching Assistant Vivian Liu for her LaTeX help; Research Coordinator Megha Senthil for her guidance and support; Head Residential Teaching Assistant Harry Gavilanes for his supervision and management.

A. Significance of Findings

This research aimed to outline a novel algorithm, Kernelytics, for early analysis of corn crops. Firstly, our research provides a proof of concept for a multi-faceted analysis of corn fields and supports the viability and utility of multispectral imagery for computer vision tasks. Furthermore, our research centers on using relatively cheap drone equipment, which furthers the accessibility of precision agriculture for small farmers. To make this point more concrete, we analyzed the potential savings we could generate at Creggan Hill Farm.


## REFERENCES

[1] U. D. of Agriculture, World agriculture production, https : / / apps . fas . usda . gov / psdonline / circulars / production.pdf. [2] F. Gnadinger and U. Schmidhalter, “Digital counts of maize plants by unmanned aerial vehicles (uavs),” Remote Sensing, vol. 9, p. 544, Mar. 2017. DOI: 10. 3390/rs9060544. [3] B. Kitano, C. C. T. Mendes, A. R. Geus, H. C. Oliveira, and J. R. Souza, “Corn plant counting using deep learning and uav images,” IEEE Geoscience and Remote Sensing Letters, pp. 1–5, 2019. [4] R. Barzin, H. Kamangir, and G. C. Bora, “Comparison of machine learning methods for leaf nitrogen estimation in corn using multispectral uav images,” Transactions of the ASABE, vol. 9, no. 190, 2021. [5] R. Latif, A. Saddik, and A. Eouardi, “Metrics in precision agriculture using multispectral images: Review and evaluation,” Studies in Distributed Intelligence, Jun. 2022. [6] B. Johansen and B. Tommervik, “The relationship between phytomass, ndvi and vegetation communities on svalbard,” International Journal of Applied Earth Observation and Geoinformation, vol. 27, Apr. 2014. [7] L. Loures, A. Chamizo, P. Ferreira, A. Loures, R. Castanho, and T. Panagopoulos, “Assessing the effectiveness of precision agriculture management systems in mediterranean small farms,” Sustainability, vol. 12, no. 9, Mar. 2020. DOI: 10.3390/su12093765. [8] GISGeography, What is ndvi (normalized difference vegetation index)? https : / / gisgeography. com / ndvi - normalized-difference-vegetation-index/, 2023. [9] A. Vidhya, Cnn architecture, 2022. [10] W. Liu, D. Anguelov, D. Erhan, et al., “Ssd: Single shot multibox detector,” CoRR, vol. abs/1512.02325, 2015. [11] J. Zhu, T. Park, P. Isola, and A. Efros, “You only look once: Unified, real-time object detection,” CoRR, Aug. 2015. [12] F. Safarov, K. Temurbek, D. Jamoljon, et al., “Improved agricultural field segmentation in satellite imagery using tl-resunet architecture,” Sensors, vol. 22, no. 24, Dec. 2022. DOI: 10.3390/s22249784. [13] K. He, G. Gkioxari, P. Doll´ar, and R. Girshick, Mask r-cnn, 2018. [14] DJI, Dji phantom 4, https://www.dji.com/phantom-4. [15] C. Nguyen, V. Sagen, S. Bhadra, M. Maimaitijiang, and S. Moose, “Maize phenotyping using uav-borne hyperspectral, lidar, and thermal data fusion and machine learning,” AGU Fall Meeting 2021, Dec. 2021.

Herbicide treatment is typically sprayed across the entire field, but by targeting only weed areas, farmers can save money and prevent the harmful effects of runoff. Specifically, our U-Net model detected that weeds only covered 3.94% (0.3008/7.62 acres) of the entire field, meaning by spraying only weed pixels, small farmers can save up to 96% of their current savings on weed management. Based on the typical cost of their herbicide treatment, we estimated that these savings would amount to $4,392 for Creggan Hill Farm.

B. Limitations

The study has various limitations. One is low-resolution imagery. This constraint occurred primarily due to the high altitudes at which the drone was flown to optimize battery usage, avoid crashing into tree cover, and reduce flight time. However, the higher altitude reduced the quality of the image and required preprocessing to work around. Flying at a lower height, such as 10-20 meters, would increase the pixel resolution. Additionally, the processing of tiling the orthomosaic into image chips meant that some corn plants in the test set were left unlabeled, leading to lower-quality data. All these factors posed considerable challenges during model training.

C. Future Work

One potential avenue for future work is to implement Kernelytics to analyze corn plants later in the season so that comparisons can be made to calculate growth and other metrics. Another area of research involves including other data–such as plant density, soil quality, soil type, and soil moisture–to gain more insights into crop health. Finally, another possible avenue for further exploration is to combine the 2D aerial images with 3D data, such as those collected by Light Detection and Ranging (LiDAR) technology [15].

ACKNOWLEDGMENTS

The authors of this paper would like to thank the Rutgers School of Engineering, Rutgers University, and the State of New Jersey Office of the Secretary of Higher Education for the chance to further explore engineering and opening up new opportunities; Governor’s School of Engineering and Technology alumni and benefactors for their continued participation and support; Dean Jean Patrick Antoine, the director of the Governor’s School of Engineering, for his

5

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:44:46 UTC from IEEE Xplore.  Restrictions apply.
