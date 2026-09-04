---
workspace_id: SCI-000980
doi: 10.1109/ivcnz64857.2024.10794485
title: Deep Learning for Brassica Oleracea Instance Segmentation in UAV Imagery
authors:
- family_name: Macalisang
  given_name: Jonel R.
  orcid: null
- family_name: Alon
  given_name: A.
  orcid: null
- family_name: Susa
  given_name: Julie Ann B.
  orcid: null
- family_name: Austria
  given_name: Yolanda D.
  orcid: null
- family_name: Melegrito
  given_name: Mark P.
  orcid: null
- family_name: Militante
  given_name: Sammy V.
  orcid: null
year: 2024
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:41.375298+00:00'
---

# Deep Learning for Brassica Oleracea Instance Segmentation in UAV Imagery

Deep Learning for Brassica Oleracea Instance

Segmentation in UAV Imagery

Jonel R. Macalisang  College of Industrial Technology

Alvin Sarraga Alon  Center for AI Research  Department of Trade and Industry

Julie Ann B. Susa  Department of Computer Engineering

Technological University of the

Southern Luzon State University

Makati City, Philippines

Lucban, Quezon, Philippines

Philippines  Manila City, Philippines  jonelmacalisang@gmail.com

aalon.cair@dti.gov.ph

jannsusa@gmail.com

Mark Melegrito  Department of Electronics Engineering

Yolanda D. Austria  Department of Computer Engineering

Sammy V. Militante  College of Engineering and


## Architecture

University of Antique

Technological University of the

Adamson University

2024 39th International Conference on Image and Vision Computing New Zealand (IVCNZ) | 979-8-3315-1877-6/24/$31.00 ©2024 IEEE | DOI: 10.1109/IVCNZ64857.2024.10794485

Philippines  Manila, Philippines  mark_melegrito@tup.edu.ph

Manila, Philippines  yolanda.austria@adamson.edu.ph

Antique, Philippines  sammy.militante@antiquespride.edu.ph

scalability of manual monitoring systems is restricted, and  they may not provide timely information for timely actions  [6].


## Abstract—This work introduces a new method for

quantifying and sizing Brassica Oleracea instances via the use of 
unmanned aerial vehicle (UAV) imagery for instance 
segmentation. The goal of the project is to create a deep 
learning-based model that can recognize and classify Brassica 
Oleracea occurrences in images taken by unmanned aerial 
vehicles. The study uses the Mask R-CNN architecture and 
transfer learning strategies to train the model using a dataset of 
COCO-formatted annotated data and images of cabbage that 
was obtained from Mendeley Data. To improve resilience and 
variability, augmentation methods are used in dataset 
preparation. Evaluation criteria including mean Average 
Precision (mAP), precision, recall, and confidence levels are 
used to assess the model's performance. Findings show that the 
model performed very well, obtaining a remarkable mAP value 
of 98.6%. Moreover, inferencing test data shows how reliable 
the model is in identifying Brassica Oleracea occurrences in a 
variety of settings. The model continuously obtains high 
identification 
rates 
despite 
obstacles 
such 
as 
item 
incompleteness and illumination fluctuations, demonstrating its 
dependability and applicability for practical use in agricultural 
settings. The suggested strategy has the potential to advance 
crop management techniques and precision agriculture 
methods, enhancing agricultural sustainability and production.

Utilizing  remote  sensing  technology,  especially  Unmanned Aerial Vehicles (UAVs), for agricultural  monitoring has gained popularity in recent years [7]. High- resolution camera-equipped UAVs provide an effective and  non-destructive way to gather comprehensive images over  huge agricultural regions [8]. Frequent and high spatial  resolution data collecting made possible by UAV usage offers  more thorough and rapid evaluations of crop health and  growth [9].

In agricultural monitoring and management, plant instance  segmentation—the process of identifying individual plants  within images—is essential [10]. Plant density, size  distribution, and growth dynamics may be precisely quantified  by accurately segmenting Brassica Oleracea plants using  UAV images [11]. Nevertheless, there are several difficulties  in separating individual plants from aerial photos, such as  lighting fluctuations, occlusions, and overlapping foliage [12].

Convolutional neural networks (CNNs), one of the most  popular deep learning approaches, have completely changed  the area of computer vision, including the analysis of  agricultural images [13]. Plant instance segmentation tasks  have advanced significantly as a result of CNNs' amazing  capacities to learn intricate patterns and features straight from  raw image data [14]. Researchers can improve the precision  and effectiveness of Brassica Oleracea monitoring using UAV  images by utilizing deep learning techniques.

Keywords—Brassica  Oleracea;  Instance  Segmentation;  Unmanned Aerial Vehicle (UAV) Imagery; Transfer Learning;  Mask R-CNN Architecture.

I. INTRODUCTION

Known by several names such as broccoli, cabbage, or  cauliflower, Brassica Oleracea is an important agricultural  plant that is grown all over the globe because of its economic  and nutritional worth [1]. Brassica Oleracea, a member of the  Brassicaceae family, has a variety of morphological  characteristics and dynamic development patterns, which  make it difficult for agricultural practitioners to monitor and  manage [2]. Accurate yield estimation, early disease  detection, and ideal growing conditions are all dependent on  the effective monitoring of Brassica Oleracea crops [3].

This work offers a unique method for utilizing UAV  photography to partition Brassica Oleracea plant instances.  Modern deep learning methods and sophisticated image  processing algorithms are used in the suggested approach to  precisely identify individual plants from aerial photos. Our  technique provides useful information for agricultural  practitioners and academics by facilitating full analysis and  monitoring of Brassica Oleracea crops via exact segmentation  findings.

Conventional approaches to Brassica Oleracea crop  monitoring, such as vision inspection and manual field  surveys, are time-consuming, labor-intensive, and frequently  vulnerable to subjectivity mistakes [4]. These techniques  usually depend on observations and measurements made on  the ground, which could not fully account for the spatial  variability seen in agricultural fields [5]. Additionally, the

II. METHODOLOGY

A. Data Preprocessing and Acquisition

As shown in Fig. 1, the dataset used in this investigation  was obtained from Mendeley Data, a reliable source of  scientific  datasets  that  guarantees  repeatability  and

979-8-3315-1877-6/24/$31.00 ©2024 IEEE

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:40:37 UTC from IEEE Xplore.  Restrictions apply.

models because it adds variability to the training data, which  improves the model's ability to generalize to new data. The  annotated images in this research were subjected to many  modifications as part of the augmentation process used in this  investigation. These changes included vertical flipping to  further diversity the dataset and horizontal flipping to  practically double its size and introduce variance in object  orientations. Then, to improve the model's resilience to  varying viewing angles, random rotations were performed to  the images with equal probability for clockwise, counter- clockwise, and upside-down rotations—each with a 30%  chance. These rotations replicated fluctuations in the UAV's  orientation during image collecting. Random exposure  adjustments between -10% and +10% of the original exposure  level were also applied, simulating variations in camera  settings and ambient lighting conditions. Random brightness  adjustments between -15% and +15% of the original  brightness level were also applied to introduce variability in  illumination conditions. Lastly, 0.1% of the image's pixels had  salt and pepper noise introduced to them. This noise  introduces stochastic fluctuations in pixel values, further  diversifying the dataset. Salt and pepper noise is characterized  by randomly positioned white and black pixels. The dataset  size was greatly increased by using these augmentation  approaches, going from 458 initial images to 1100 images in  total.

accessibility [15]. The high-resolution photos in this dataset  show cabbage (Brassica oleracea var. capitata) plants.

Fig. 1. Cabbages Dataset [15].

Unmanned aerial vehicles (UAVs) were used to collect  images of the cabbage in the fields belonging to farmers in  Gifu Prefecture, Japan. The relevance of this geographic  region in the development of cabbage and its portrayal of a  variety of agricultural approaches led to its selection. The  images capture the full life cycle of the cabbage plants, from  the earliest growth phases to the time just before harvest.

C. Mask RCNN Architecture

B. Annotation and Augmentation of Dataset

Fig. 3. Mask R-CNN framework for Cabbage Segmentation.

A backbone network, a region proposal network (RPN),  and two task-specific brains for mask prediction and bounding  box regression make up the three main parts of the Mask R- CNN. By extracting feature maps from input photos, the  backbone network—typically a pre-trained convolutional  neural network (CNN) like ResNet or ResNeXt—captures  hierarchical representations of visual characteristics.

Fig. 2. Annotation of the Cabbages dataset.

Using the feature maps that the backbone network has  retrieved, the region proposal network (RPN) suggests  potential object bounding boxes and the objectness ratings that  go along with them. These suggested areas are sent into the  network's later stages for further categorization and fine- tuning.

The COCO (Common Objects in Context) segmentation  format, which is a well-recognized standard for object  recognition and instance segmentation tasks, was used to  annotate the dataset utilized in this investigation as seen in Fig.  2. To precisely delineate the borders of each cabbage  (Brassica oleracea var. capitata) instances, every image in the  set required meticulous annotation. The annotations were  represented as segmentation masks stored at the pixel level,  enabling accurate delineation of every cabbage plant in the  images.

To improve a pre-trained Mask R-CNN model on our  Brassica Oleracea instance segmentation challenge, the study  used transfer learning in the experimental setting as shown in  Fig. 3. Transfer learning is teaching a model to operate on a  smaller, task-specific dataset—our UAV imaging dataset,  which contains examples of Brassica Oleracea—by  initializing the model's weights with those learned from a  large, varied dataset, like the COCO dataset.

After the annotation process, several augmentation  techniques were used to increase the robustness of the instance  segmentation model and the richness of the dataset.  Augmentation is an important step in training deep learning

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:40:37 UTC from IEEE Xplore.  Restrictions apply.

The bounding box regression head adjusts the coordinates  of the suggested bounding boxes during training so that they  more closely match the limits of the ground truth objects. The  mask prediction head creates segmentation masks for each  proposed area concurrently, giving each pixel in the region a  binary mask that indicates whether or not it corresponds to the  item of interest.

classification loss, and depth focal loss are among the loss  components that go toward the model's ultimate optimization  goal. The training was conducted using a T4 GPU High RAM  on Google Colab.

By combining the Mask R-CNN architecture with transfer  learning [16]-[17], our research was able to get impressive  results in correctly measuring and sizing Brassica Oleracea  instances from UAV data. The study was able to make use of  the rich feature representations that were discovered from a  variety of images by using pre-trained weights and  optimizing the model on our particular dataset. This  improved the model's capacity to generalize to our target  domain.

Fig. 4.  Training Loss.

Training Box Loss: By the completion of training, the box  loss had progressively dropped from an initial value of around  1.7 to about 0.6. This suggests that as the model gained  experience, it became more adept at predicting bounding  boxes, which enhanced its capacity to locate Brassica  Oleracea occurrences in the UAV images.

D. Model Evaluation Metrics

One  important  metric  for  evaluating  instance  segmentation methods' efficacy is the mean Average Precision  (mAP) (1). In terms of computation, mAP is determined by  taking the average of the Average Precision (AP) (2) values  for each category of objects in the dataset.

Training Segmentation Loss: Similarly, near the  completion of training, the segmentation loss showed a  declining trend, beginning at around 3.5 and ending at about  1.2. This implies that the model improved the accuracy of its  pixel-level segmentation, successfully defining the borders of  cabbage instances in the images.

The following is the mAP equation:



 ∑ 	  	            (1)

 

Training Classification Loss: By the completion of  training, the classification loss had significantly dropped from  an initial value of around 2.5 to about 0.3. This suggests that  the model improved its capacity to distinguish between  various item categories and became better at accurately  identifying cabbage instances.

Where:

•   is the total number of categories that object may  have..

•  For the  object category, 	 _denotes the  Average Precision.

Training Depth Focal Loss: A declining trend was also  seen in the depth focal loss, which peaked at around 1.5 and  ended at about 0.9. This implies that the model gained the  ability to use depth information efficiently, which enhanced  the performance of depth-based segmentation.

The precision-recall curve is integrated to get the Average  Precision (AP) for each category, which is provided by:

            (2)

	   	

Validation Box Loss: Starting at around 1.4 and finishing  at about 0.8, the box loss for validation data showed a similar  declining pattern to that seen in the training loss. This suggests  that the model's proficiency in localizing object instances  transferred effectively to previously unknown data.

In this case, the accuracy for the  item category at each  recall level  is shown by 	.

Plotting accuracy versus recall at different confidence  levels for object recognition is what the precision-recall curve  does. Recall is the ratio of successfully recognized instances  to all ground truth instances, while precision is the ratio of  properly detected instances to all projected instances.

Across a variety of object categories, the precision and  recall components of object detection accuracy are captured  by the mAP measure, which provides a thorough evaluation  of model performance. Within our research on Brassica  Oleracea instance segmentation using UAV images, mAP is a  key metric for assessing how well the model performs in  precisely measuring and sizing cabbage instances under  various  development  stages  and  environmental  circumstances.

Fig. 5.  Validation Loss.

Validation Segmentation Loss: Starting at around 3.25  and finishing at about 1.5, the segmentation loss for validation  data showed a declining trend but had larger values than for  training. The decreasing trend, despite the higher values,  indicates that the model performed better at segmenting the  data on validation than it did during the training epochs.

III. RESULTS AND DISCUSSIONS

A. Training and Validation Results

The instance segmentation model's performance and  learning dynamics throughout 250 epochs are elucidated by  the loss curves for training (Fig. 4) and validation (Fig. 5). Box  loss (for bounding box regression), segmentation loss,

Validation Classification Loss: For the validation data,  there was a discernible decline in the classification loss, which  peaked at around 1.8 and ended at about 0.4. This suggests

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:40:37 UTC from IEEE Xplore.  Restrictions apply.

that the model successfully adapted to validation data and its  ability to categorize object instances with accuracy.

roughly 0.98. This suggests that the model improved the  quality of bounding box predictions for Brassica Oleracea  cases by achieving high precision and recall at lower IoU  thresholds.

Validation Depth Focal Loss: The validation results  showed a somewhat varying pattern for the depth focal loss,  with an estimated beginning at 1.20 and an ending at 0.95. The  decreasing trend, albeit not constant, indicates that the model  made good use of depth information for validation data  segmentation.

mAP50-95 (B): The Brassica Oleracea category's mAP  showed a notable improvement above IoU thresholds, ranging  from 0.5 to 0.95. It began at around 0.3 and ended at roughly  0.8. This implies that a greater variety of IoU thresholds were  covered by the model's excellent accuracy and recall,  demonstrating robust performance across varied degrees of  object overlap.

B. Evaluation using Precision/Recall/mAP

mAP50 (M): Comparably, the "Other" category's mAP at  the IoU threshold of 0.5 showed a notable improvement,  beginning at around 0.5 and finishing at roughly 0.97. This  shows that the model successfully detected and classified  occurrences that correspond to different categories with a high  degree of accuracy and recall.

Fig. 6. Precision/Recall Evaluation of the Model.

mAP50-95 (M): Notable improvement was also shown in  the mAP for the "Other" category spanning IoU thresholds  from 0.5 to 0.95; it began at around 0.2 and ended at roughly  0.7. This implies that the model performed robustly  throughout a range of object overlap, correctly classifying  examples that belong to different categories.

A comprehensive metric for evaluating the instance  segmentation model's performance across several object  categories is the mean Average Precision (mAP) (Fig. 7),  which sheds light on the precision and recall (Fig. 6)  components of object identification accuracy, with B  representing Brassica Oleracea (the target category) and M  representing all other categories (Miscellaneous).

The model performs very well in precisely identifying and  segmenting Brassica Oleracea instances from UAV images  for quantification and size purposes, as seen by the total mAP  score of 98.6%. This high mAP score highlights the model's  effectiveness in real-world deployment circumstances by  reflecting its exceptional accuracy and recall across several  object categories.

Precision (B): The Brassica Oleracea category's precision  improved significantly, with an estimated beginning and  ending precision of 0.65 and 0.96, respectively. This suggests  that when the model was used in different environmental  circumstances and development phases, it was more accurate  in recognizing Brassica Oleracea occurrences.

C. Instance Segmentation Testing

Brassica Oleracea instances were densely concentrated in  the test image (Fig. 8) which included 38 objects of the  cabbage class within the agricultural environment. Its strong  performance in detecting individual items among complicated  backdrops and varied environmental circumstances is shown  by the fact that the model was able to detect and properly  segment all 38 instances of cabbage included in the test image,  despite the complex background information. As evidence of  the model's high degree of confidence in its predictions, the  detection results gave confidence values for the discovered  items ranging from 71% to 86%. The model's flexibility to a  range of circumstances during inferencing is shown by the  variation in confidence levels, which may be ascribed to  elements like object size, occlusions, and image quality. A  thorough aerial view of the agricultural area was also provided  by the UAV's collection of the test image at its greatest  altitude.

Recall (B): In a similar vein, recall increased significantly  for the Brassica Oleracea group, peaking at around 0.95 after  initially hovering around 0.6. This implies that a greater  percentage of actual Brassica Oleracea cases were  successfully remembered by the model, demonstrating  increased sensitivity.

Precision (M): The "Other" group (non-Brassica Oleracea  cases) showed a significant improvement in precision, with  values ranging from around 0.55 to 0.96. This suggests that  the model reduced false positive detections by correctly  categorizing non-target cases with high accuracy.

Recall (M): The "Other" category's recall likewise saw a  discernible improvement, peaking at around 0.95 after  beginning at roughly 0.55. This implies that the model  minimized false negative detections by efficiently recalling a  greater percentage of real cases belonging to other categories.

Fig. 7. mAP Evaluation of the Model.

mAP50 (B): For the Brassica Oleracea group, the mAP at  the IoU (Intersection over Union) threshold of 0.5 showed a  significant rise, beginning at around 0.65 and finishing at

Fig. 8. Inference Results of Level 1 Height UAV Image Capture.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:40:37 UTC from IEEE Xplore.  Restrictions apply.

Brassica Oleracea examples were abundant in the test  image (Fig. 9), which included 53 objects from the cabbage  class in the agricultural environment. The model's ability to  recognize and properly segment all 53 instances of cabbage in  the test image was shown, despite the scene's complexity. This  demonstrated the model's resilience and efficacy in  distinguishing individual items among crowded backdrops  and variable environmental circumstances. The great degree  of trust the model had in its predictions was shown by the  detection findings, which gave confidence ratings for the  identified items ranging from 76% to 91%. This variation in  confidence levels illustrates how the model may be adjusted  to a variety of scenarios during inferencing, depending on  variables like object size, occlusions, and image quality. A  thorough aerial image of the agricultural area was also  provided by the UAV's acquisition of the test image at the  second-highest height.

Within the agricultural scene, the test image (Fig. 11) had  28 objects belonging to the cabbage class. However, just 23  objects were accurately identified by the model because of  several issues. item incompleteness was one of these issues;  one item was at the border of the picture, while other objects  were hidden by overlapping with nearby cabbage instances  and by differences in brightness intensity. Despite these  challenges, the model was able to offer both confident and  somewhat confident detections, as seen by the detection  results for the identified objects, which ranged in confidence  from 63% to 94%. The model's flexibility in various  inferencing scenarios, such as those in which objects are partly  hidden or impacted by lighting conditions, is shown by the  variation in confidence levels.

Fig. 11. Inference Results of Level 4 Height UAV Image Capture.

Fig. 9. Inference Results of Level 2 Height UAV Image Capture.

Furthermore, the UAV took the test image at its lowest  zoom height, providing a closer, more in-depth look at the  agricultural area. The model performed well in correctly  identifying and segmenting a significant percentage of the  cabbage occurrences in the test image, even though its lower  altitude may have restricted its viewpoint and reduced  detection accuracy. Overall, the model's efficacy in Brassica  Oleracea instance segmentation using UAV-captured imagery  is demonstrated by its ability to detect a significant number of  cabbage  instances,  despite  obstacles  like  object  incompleteness and a lower zoom height. This has led to  advancements in agricultural practices and crop management  strategies.

Because there were incomplete objects along the  periphery of the test image (Fig. 10), it was difficult to  recognize all 36 objects in the cabbage class inside the  agricultural scene. As a result, the model only identified 34  objects properly, demonstrating how important object  completeness is for accurate recognition, especially at the  edge of the image. The model produced remarkable detection  results despite these difficulties, with confidence levels for the  identified items ranging from 73% to 94%. This variation in  confidence levels highlights how flexible the model is during  inferencing, catching both detections with high and moderate  degrees of confidence. Furthermore, the test image was taken  by the UAV at the second-to-lowest zoom height, giving a  closer look at the farmland. Even though the model's  viewpoint may have been restricted and it was more difficult  to recognize things near the border of the image, the model  nonetheless performed well in identifying and classifying  instances of cabbage.

IV. CONCLUSION

Important results that highlight the usefulness of the  suggested methodology in agricultural applications were  obtained from the research on Brassica Oleracea instance  segmentation utilizing UAV images for quantification and  size. During the process of evaluation, several significant  findings surfaced, emphasizing the model's resilient  functionality and possible influence on agricultural practice  techniques.

Above all, across a variety of test circumstances, the  model showed remarkable accuracy in identifying Brassica  Oleracea occurrences. Despite obstacles like inconsistent  illumination and partial objects, the model continuously  produced high identification rates, correctly recognizing most  of the occurrences of cabbage in the test images. This shows  how well-suited the model is to a variety of agricultural  settings and how well-suited it is to manage intricate object  arrangements.

Impressive performance metrics were also revealed by the  evaluation measures, with the mean Average Precision (mAP)  providing a thorough assessment of the model's efficacy. The

Fig. 10. Inference Results of Level 3 Height UAV Image Capture.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:40:37 UTC from IEEE Xplore.  Restrictions apply.

achieved mean absolute percentage error (mAP) of 98.6%  indicates that the model performs very well in identifying and  classifying Brassica Oleracea cases. The model's accuracy and  recall across a variety of object categories are reflected in its  high mAP score, which emphasizes its applicability for actual  implementation in agricultural contexts.

Journal of Natural Pesticide Research, vol. 4, p. 100031, Jun. 2023.  doi:10.1016/j.napere.2023.100031.   [5] H. M. Ruhanen, A. O. Mofikoya, A. Vesterbacka, M. Kivimäenpää,

and J. D. Blande, “Trait-based cropping of brassicaceous plants:  Effects on ecosystem services and crop yield,” Biological Control, vol.  187, p. 105389, Dec. 2023. doi:10.1016/j.biocontrol.2023.105389.   [6] P. Karmakar et al., “Crop monitoring by Multimodal Remote Sensing:

A Review,” Remote Sensing Applications: Society and Environment,  vol. 33, p. 101093, Jan. 2024. doi:10.1016/j.rsase.2023.101093.  [7] Md. A. Istiak et al., “Adoption of unmanned aerial vehicle (UAV)

The results of the research highlight how important the  suggested model is to the advancement of crop management  techniques and precision agricultural methods. The model has  promising qualities that might enhance crop monitoring,  quantification, and sizing procedures, leading to increased  agricultural production and sustainability. These qualities  include its high accuracy, strong performance, and remarkable  mAP value. Additionally, further research is recommended to  explore whether the model can be generalized to other crops  beyond Brassica Oleracea and to assess how the model  handles varying weather conditions and seasons.

imagery in agricultural management: A Systematic Literature  Review,” Ecological Informatics, vol. 78, p. 102305, Dec. 2023.  doi:10.1016/j.ecoinf.2023.102305.   [8] A. Rejeb, A. Abdollahi, K. Rejeb, and H. Treiblmaier, “Drones in

agriculture: A review and Bibliometric Analysis,” Computers and  Electronics in Agriculture, vol. 198, p. 107017, Jul. 2022.  doi:10.1016/j.compag.2022.107017.   [9] A. D. Boursianis et al., “Internet of things (IOT) and Agricultural

Unmanned Aerial Vehicles (uavs) in Smart farming: A comprehensive  review,” Internet of Things, vol. 18, p. 100187, May 2022.  doi:10.1016/j.iot.2020.100187.   [10] V. G. Dhanya et al., “Deep Learning Based Computer Vision

ACKNOWLEDGMENT

Approaches  for  Smart  Agricultural  Applications,”  Artificial  Intelligence  in  Agriculture,  vol.  6,  pp.  211–229,  2022.  doi:10.1016/j.aiia.2022.09.007.   [11] V. G. Dhanya et al., “Deep Learning Based Computer Vision

The authors would like to thank everyone who helped to  complete this study and all the organizations that supported  them. Regards to Yui Yokoyama, Tsutomu Matsui, and S.T.  for their priceless assistance with the collection and  annotation of the dataset, Takashi Tanaka. Expressing  gratitude to the Institutions/Universities that supported and  provided the resources needed for this research. Furthermore,  the authors were grateful for the advice and criticism they got  from advisers and colleagues throughout the study process.  Without their cooperation and support, this endeavor would  not have been possible.

Approaches  for  Smart  Agricultural  Applications,”  Artificial  Intelligence  in  Agriculture,  vol.  6,  pp.  211–229,  2022.  doi:10.1016/j.aiia.2022.09.007.   [12] Z. Luo, W. Yang, Y. Yuan, R. Gou, and X. Li, “Semantic segmentation

of Agricultural Images: A survey,” Information Processing in  Agriculture, Feb. 2023. doi:10.1016/j.inpa.2023.02.001   [13] S. Khan and L. AlSuwaidan, “Agricultural Monitoring System in video

surveillance object detection using feature extraction and classification  by Deep  Learning Techniques,” Computers and Electrical  Engineering,  vol.  102,  p.  108201,  Sep.  2022.  doi:10.1016/j.compeleceng.2022.108201   [14] S. Mishra, “Internet of things enabled deep learning methods using


## REFERENCES

[1] H. Li et al., “Nutritional values, beneficial effects, and food

unmanned aerial vehicles enabled Integrated Farm Management,”  Heliyon, vol. 9, no. 8, Aug. 2023. doi:10.1016/j.heliyon.2023.e18659   [15] M. P. Melegrito et al., “Abandoned-cart-vision: Abandoned CART

applications of broccoli (brassica oleracea var. Italica Plenck),” Trends  in Food Science &amp; Technology, vol. 119, pp. 288–308, Jan. 2022.  doi:10.1016/j.tifs.2021.12.015.   [2] M. Drašković Berger et al., “Cabbage (brassica oleracea L. var.

detection using a deep object detection approach in a shopping parking  space,” 2021 IEEE International Conference on Artificial Intelligence  in  Engineering  and  Technology  (IICAIET),  2021.  doi:10.1109/iicaiet51634.2021.9573963   [16] M. P. Melegrito et al., “Abandoned-cart-vision: Abandoned CART

capitata) fermentation: Variation of bioactive compounds, sum of  ranking differences and cluster analysis,” LWT, vol. 133, p. 110083,  Nov. 2020. doi:10.1016/j.lwt.2020.110083.   [3] K. Zhao et al., “Evaluation of the storage longevity, postharvest

detection using a deep object detection approach in a shopping parking  space,” 2021 IEEE International Conference on Artificial Intelligence  in  Engineering  and  Technology  (IICAIET),  2021.  doi:10.1109/iicaiet51634.2021.9573963   [17] Yokoyama, Yui; Matsui, Tsutomu; Tanaka, S.T. Takashi (2023), “An

quality, and sugar metabolism-related gene expression in two lines (N1  and N3) of Chinese cabbage during long-term storage,” Postharvest  Biology and Technology, vol. 206, p. 112543, Dec. 2023.  doi:10.1016/j.postharvbio.2023.112543.   [4] T. Thorat, B. K. Patle, M. Wakchaure, and L. Parihar, “Advancements

annotated image dataset of cabbages for instance segmentation”,  Mendeley Data, V1, doi: 10.17632/5cp2dyjczk.1

in techniques used for identification of pesticide residue on crops,”

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:40:37 UTC from IEEE Xplore.  Restrictions apply.
