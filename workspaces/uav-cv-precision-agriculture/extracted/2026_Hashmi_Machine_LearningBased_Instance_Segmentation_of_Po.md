---
workspace_id: SCI-001088
doi: 10.1109/ietc69527.2026.11568646
title: Machine Learning-Based Instance Segmentation of Potato Virus Y (PVY) Symptoms
  in Seed Potato Crops Using RGB Imagery
authors:
- family_name: Hashmi
  given_name: Muhammad Shehzore
  orcid: null
- family_name: Nesar
  given_name: Siddat B.
  orcid: null
- family_name: Zidack
  given_name: Walter E.
  orcid: null
- family_name: Whitaker
  given_name: Bradley M.
  orcid: null
- family_name: Nugent
  given_name: Paul W.
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:41.531441+00:00'
---

# Machine Learning-Based Instance Segmentation of Potato Virus Y (PVY) Symptoms in Seed Potato Crops Using RGB Imagery

Machine Learning-Based Instance Segmentation of

Potato Virus Y (PVY) Symptoms in Seed Potato

Crops Using RGB Imagery

Muhammad Shehzore Hashmi  Electrical and Computer Engineering

Siddat Nesar  Electrical and Computer Engineering

Walter Zidack  College of Agriculture  Montana State University  Bozeman, Montana, USA  walter.zidack@montana.edu

Montana State University  Bozeman, Montana, USA  muhammadshehz.hashmi@montana.edu

Montana State University  Bozeman, Montana, USA  siddatnesar@montana.edu

2026 Intermountain Engineering, Technology and Computing (IETC) | 979-8-3315-6167-3/26/$31.00 ©2026 IEEE | DOI: 10.1109/IETC69527.2026.11568646

Bradley M. Whitaker  Electrical and Computer Engineering

Paul W. Nugent  College of Agriculture  Montana State University  Bozeman, Montana, USA  paul.nugent@montana.edu

Montana State University  Bozeman, Montana, USA  bradley.whitaker1@montana.edu

symptoms is a critical requirement for seed potato certification  programs and effective disease management strategies [3].  However, PVY detection remains challenging under field  conditions due to symptom variability, spatial heterogeneity  within crop canopies, and the scale at which inspections must  be conducted.


## Abstract—Early and accurate detection of Potato Virus Y

(PVY) is critical for maintaining seed potato quality and 
preventing disease spread in commercial production systems. 
Conventional PVY monitoring relies on manual field scouting 
and laboratory diagnostics, which are labor-intensive, time-
consuming, and difficult to scale across large fields. Recent 
advances in uncrewed aerial systems (UAS) and machine 
learning provide an opportunity for scalable, spatially explicit 
disease detection using low-cost sensing modalities. This study 
presents an RGB-based instance segmentation framework for 
detecting and localizing PVY symptoms in seed potato fields 
using high-resolution UAV imagery collected from Washington 
State University (WSU) commercial seed lot trials and Montana 
State University (MSU) research fields. The workflow begins 
with polygon-based annotation supported by AI-assisted 
labeling and refinement using CVAT, Segment Anything 2, and 
Roboflow SAM-3, including label tightening and correction of 
missed plant instances to improve annotation quality. To 
address the localized nature of PVY symptoms within large 
UAV images, annotated imagery was subdivided into 512 × 512 
pixel tiles using a mask-preserving Python-based tiling pipeline. 
Dataset versioning, preprocessing, and augmentation were 
performed using the Roboflow platform. A YOLOv26-based 
instance segmentation model was then trained to simultaneously 
classify and segment individual plant instances. Experimental 
results achieved a mean Average Precision (mAP@50) of 
approximately 65%, with precision and recall values of 
approximately 73% and 65%, respectively, on an independent 
test set. These findings show that low-cost RGB UAV imagery, 
when combined with appropriate dataset construction and 
instance segmentation techniques, can provide reliable plant-
level PVY detection. The proposed framework offers a practical 
and scalable solution for field-scale disease monitoring and has 
strong potential for integration into seed potato inspection, 
certification, and precision agriculture workflows.

Current PVY monitoring procedures utilize a great deal of  manual field observation and laboratory testing to identify if  plants have become infected with PVY through the use of  ELISA and PCR [4]. Although both methods provide a high  degree of confidence in the presence of PVY at the individual  plant level, each method is also very labor-intensive and time- consuming. In addition, due to the labor-intensive nature of  each, it would be nearly impossible to conduct either method  over an entire commercial crop area. Visual scouting also  suffers from the same drawbacks as manual inspections and  may be affected by human errors and inconsistencies in the  evaluation of PVY symptoms, especially when symptoms are  faint or similar to those caused by environmental stresses on  the plant [5]. Therefore, there is a need to develop automation  in order to provide a scalable method to assist or enhance  visual scouting methods in agriculture.

Advances in precision agriculture and remote sensing have  made it possible to collect detailed images over vast areas  through the use of UAS. The combination of image data and  machine learning has the potential to create an automated  disease monitoring system capable of conducting individual  disease assessments of all plants across the entire field, rather  than a randomly sampled population as is currently done  manually [6], [7]. The use of remote sensing for detecting  diseases in plants has been studied extensively using various  types of sensing, including multispectral, hyperspectral, and  thermal imaging. The data acquired by these sensors captures  the physiological effects that occur in the crop canopy as a  result of infection [8], [9]. Unfortunately, multispectral,  hyperspectral, and thermal imaging require considerable  resources to obtain data and require significant expertise to  calibrate the sensor, which limits their practicality in routine  operational activities.

Keywords—Potato Virus Y (PVY), Precision Agriculture, UAV  Imagery, Roboflow, Plant Disease Detection.

I. INTRODUCTION

Potato Virus Y (PVY) is one of the most economically  damaging viral diseases affecting seed potato production  worldwide. Because seed potatoes serve as the foundation of  commercial potato supply chains, the presence of PVY in seed  lots can result in substantial yield losses, quality degradation,  and long-term disease propagation across production cycles  [1], [2]. Consequently, early and accurate detection of PVY

RGB imagery obtained from UAVs represents a low-cost  and widely available sensor that is used operationally  throughout much of the agricultural industry. Researchers  have demonstrated the ability to detect diseases in crops using

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:41:31 UTC from IEEE Xplore.  Restrictions apply.

deep learning algorithms to analyze RGB imagery [10], [11].  Even though the use of RGB imagery for disease detection has  produced good results, almost all of the research conducted to  date has focused on developing image-based classifications or  disease assessments at the plot level. While plot-level  assessments are useful for providing a general estimate of  disease occurrence, they do not provide sufficient information  to reliably support individual plant-level identification or  selection of diseased plants required for precision disease  management and seed certification programs [12], [13].

environments that would be found in seed potato certification  programs. These flights were done during clear to partly  cloudy days to reduce variation in lighting and low enough to  capture the plant-level detail needed for analysis. Each image  included a number of row plots with a high amount of detail,  including all healthy plants as well as plants showing signs of  PVY-related symptoms. Individual raw images often included  many plants and rows across a large area of the field and,  therefore, required additional processing to make the data  suitable for use with machine learning techniques.

More recent work has explored object detection  frameworks, such as YOLO-based architectures, to localize  diseased plants in UAV imagery [14]. While object detection  improves spatial awareness compared to classification,  bounding-box representations often fail to capture the  irregular shape and spatial extent of disease symptoms within  dense crop canopies. Instance segmentation, which enables  simultaneous classification and pixel-level delineation of  individual disease regions, offers a more precise and  interpretable representation of infection severity and  distribution. However, instance-level segmentation of PVY  symptoms using RGB UAV imagery remains largely  underexplored, particularly within practical, end-to-end  workflows suitable for real-world field conditions [15].

Fig. 1. Representative UAV-acquired RGB imagery of seed potato fields  used in this study, collected from commercial trials at Washington State  University (WSU) and experimental research plots at Montana State  University (MSU).

B. Annotation Strategy

In addition to creating three annotation classes, each  containing images of a specific class of plants: clean (all plants  that did not show symptoms of PVY), pvy_positive (all plants  that showed symptoms consistent with PVY infection), the  flags class represented the obvious PVY-infected plants. The  flags class was removed from the final model training to  increase the likelihood that the model will learn what is  biologically significant about the plants in the dataset.

To address these gaps, this study presents a complete  machine-learning pipeline for PVY symptom detection based  on RGB UAV imagery and instance segmentation. The  proposed framework integrates polygon-based manual  annotation, AI-assisted annotation refinement, Python-based  image tiling with polygon preservation, and dataset versioning  and augmentation using the Roboflow platform. A  YOLOv26-based instance segmentation model is trained and  evaluated using UAV imagery collected from Washington  State University (WSU) commercial seed potato trials and  Montana State University (MSU) research fields, enabling  plant-level localization of PVY symptoms under operational  field conditions. The primary contributions of this work  include the development of an RGB-based instance  segmentation framework for detecting and localizing Potato  Virus Y (PVY) symptoms in seed potato fields using UAV  imagery. The proposed approach integrates AI-assisted  annotation refinement, mask-preserving image tiling, and  Roboflow-based dataset management to support scalable and  reproducible model development. In addition, a YOLOv26- based instance segmentation model was trained and evaluated  using standard detection metrics, showing robust performance  under realistic field conditions. Finally, this study shows a  cost-effective and operationally feasible workflow for field- scale PVY monitoring and seed potato inspection that  leverages widely available RGB imagery, highlighting its  potential for practical deployment in precision agriculture  applications.

The annotations were created using polygon-based  instance segmentation so that the boundaries of individual  plants and their respective symptoms could be accurately  identified. This method of annotation was chosen instead of  bounding-box annotation because the shapes of the plants and  the symptoms they produce are highly variable and typically  irregular. To help reduce the time it takes to create these  polygons and to assist in reducing the fatigue that is common  when manually annotating large datasets, an AI-assisted  labeling tool was used. The tool was able to assist in defining  the polygons and to ensure uniform interpretation of class  definitions across the dataset. Quality control procedures  included visual inspection of annotations, cross-checking  class assignments, and removal of ambiguous or low-quality  instances. This process ensured that the final dataset reflected  consistent labeling standards, which are suitable for  supervised instance segmentation training.

II. METHODOLOGY

This section describes the data sources, annotation  strategy, dataset construction, and model training pipeline  developed for PVY symptom detection using UAV-based  RGB imagery.

Fig. 2. Polygon-based instance segmentation annotations applied to UAV  RGB  imagery,  distinguishing healthy  (clean)  and  PVY-infected  (pvy_positive) potato plants.

C. Image Tiling and Dataset Construction

A. Data Collection and Study Sites

The raw UAV images were much larger in terms of pixel  count compared to the input sizes required by the most recent  deep-learning architectures. Symptoms caused by PVY are  generally located in smaller areas of each image. A method to  correct the difference in the amount of detail present in the

RGB imagery was collected using a DJI Mavic 3M  uncrewed aerial system (UAS) over commercial seed potato  trial areas at WSU and experimental plots at MSU, capturing  both RGB and multispectral data. These represent the typical

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:41:31 UTC from IEEE Xplore.  Restrictions apply.

images, i.e., a tiling method to create a new set of images from  the original images, was created.

(mAP@50) calculated over both validation and test datasets  to evaluate the model's performance, so we could assess how  accurately localized objects were, and how reliably classified  they were under actual field conditions.

A custom tiling pipeline was created using Python to cut  the high-resolution images into tiles consisting of 512 × 512  pixels. During the process of creating the tiles, the polygonal  annotation data was intersected with the boundary of each tile.  As a result, the instance segmentation masks for each area of  the image remained intact after cropping. In the case of  instance segmentation tasks, maintaining the geometric  relationships between objects is important because resizing  objects can alter their shape and reduce the accuracy of the  masks generated [18]. Therefore, the tiling method preserved  the integrity of the annotations and properly accounted for  partial instances. The tiling method also accomplished two  major objectives: it increased the number of available samples  for training models, and it improved the models’ capability to  recognize fine-scale details of the symptoms associated with  PVY. The final tiled dataset represented both healthy plants  and plants infected with PVY in an equal manner across  various levels of spatial context.

III. EXPERIMENTAL SETUP

This section describes the dataset composition, train- validation-test split strategy, and evaluation metrics used to  assess the performance of the proposed PVY instance  segmentation framework.

A. Training, Validation, and Test Sets

The data was then processed through annotation  refinement, tiling of images, and data pre-processing.  Therefore, in its final form, the dataset contained 658 RGB  image tiles, all with their respective instance segmentation  labels. Prior to model training, all images were resized to a  standard pixel resolution of 512 x 512. In addition, the data  was separated into three separate sets to allow for unbiased  performance evaluations of the models being trained. These  three sets of data were the training set, validation set, and test  set. The training set was used to determine optimal values for  the model's parameters. The validation set was used to select  the best model and to assess the model's performance early on  in the development process. The test set was kept completely  isolated from the model during development so that it could  be used as a measure of the model's ability to generalize.

D. Dataset Versioning and Preprocessing Using Roboflow

The dataset was made available using the Roboflow  platform for data management, preprocessing, and versioning.  Roboflow is a tool that creates reproducible versions of  datasets  and  enables  users  to  create  standardized  preprocessing and augmentations on their data before they  train their models. Roboflow was chosen as it supports  workflows  using  instance  segmentation,  allows  for  reproducible versioning of datasets, and can be easily  integrated with pipelines that are based on YOLO for model  training [19], [20].

In the final dataset, the clean class contained a total of  1,492 examples, of which 1,011 were allocated to the training  set, 334 to the validation set, and 147 to the test set. In contrast,  the PVY-positive class comprised 166 total examples, with  120 used for training, 32 for validation, and 14 for testing. To  increase the effective sample size of the minority class and  improve model robustness, data augmentation techniques,  including horizontal and vertical flips, rotations, and shear  transformations, were applied during training. The dataset was  partitioned into training, validation, and test subsets to support  unbiased model evaluation. In total, 63 original images were  used for training and subsequently augmented to produce 658  training tiles, while 20 images were allocated to the validation  set and 8 images were reserved for the independent test set.  The validation set was used to monitor model performance  during training, whereas the test set was kept completely  isolated and used only for final performance assessment.  During the training process, the validation set was used to  monitor the model's performance and to make selections  regarding which model to use when developing the system.  The test set was completely isolated from the model and was  not used at all during the model development process. It was  only used after the model had been developed to assess the  model's overall performance.

Standardized pre-processing for all images was performed  through automatic orientation correction and the resizing of  all images to 512 x 512 pixels to guarantee that images were  processed with consistent dimensions. To provide robustness  and generalizability of models, data augmentation techniques  were applied. Horizontal and vertical flips, rotations (at 90- degree intervals), random rotation between ±15 degrees, and  shear transformations were applied horizontally and  vertically. Following standard practice for supervised  learning, the dataset was split into three separate sets for  training, validation, and testing. The majority of images were  allocated to the training set, with smaller proportions reserved  for validation and independent testing to enable unbiased  performance evaluation.

E. Roboflow Model Architecture and Training

In this work, we used a YOLOv26-based model for  instance segmentation due to an optimal trade-off between  detection accuracy and processing speed. YOLO based  architectures have shown high performance in agricultural  applications of computer vision, as well as being ideal for near  real-time/real-time deployment scenarios.

The two biologically meaningful classes were ultimately  in the last dataset: clean (healthy potato plants) and  pvy_positive (potato plants that show obvious PVY  symptoms). The flags class, which was initially thought about  as an option during the process of annotating, was removed  from training to give the model the opportunity to identify  agronomically meaningful plant-level disease occurrence. As  would be expected in seed potato fields for operational use,  the class distribution of the dataset was imbalanced. The  majority of the potato plants in the dataset were classified as  clean, while there were fewer PVY-positive potatoes. The  imbalance of the two classes in the dataset represents how  disease prevalence occurs in the real world when deploying a

We employed Roboflow's fully-integrated training  pipeline for our model to allow automated setup and  evaluation of our YOLO-based model. We trained the model  for many iterations until it reached convergence, and then  adjusted confidence/overlap thresholds to find an appropriate  balance between precision/recall for PVY detection. We also  designed the model to be able to classify individual plant  instances while producing a pixel-level segmentation mask for  each detected object. We used the standard detection metrics  that include precision, recall, and mean Average Precision

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:41:31 UTC from IEEE Xplore.  Restrictions apply.

diagnostic tool at the scale of a field. Class imbalance is  common in real-world agricultural disease datasets due to the  fact that infected plants are usually present at lower prevalence  rates than healthy plants. However, as stated previously, no  rebalancing techniques were specifically applied to this  dataset; however, data augmentation and tile-level sampling  were applied to help limit the effects of class imbalance during  training.

behavior, a numerical assessment of performance, and a  qualitative evaluation of the results.

A. Training Dynamics    The training of the model exhibited steady convergence  through the epochs, as indicated by the losses (box loss,  classification loss, and object loss), which were consistently  reduced throughout the training process. The training losses  showed that the model had learned the spatial and semantic  aspects of plant images that differentiated healthy plants from  those infected with PVY. The early epoch losses were  significantly decreased, but then gradually stabilized as the  model converged toward its final solution. The data  augmentation techniques used, as well as the tiling-based  expansion of the dataset, appear to have assisted the model in  generalizing better than it would have otherwise been able to  do. Also, the lack of persistent high loss values suggests that  the model did not underfit the data, even though the test  dataset was small.

TABLE I.   SUMMARY OF THE UAV RGB DATASET USED FOR PVY  INSTANCE SEGMENTATION AFTER TILING AND PREPROCESSING.

Item  Value

Study Sites  WSU (commercial), MSU (research)  Total tiled images  658  Training set  630 images  Validation set  20 images  Test set  8 images  Classes  clean, pvy_positive  Tile size  512 × 512 pixels

B. Evaluation Metrics    The performance of models was assessed using standard  object detection and instance segmentation metrics that have  been traditionally used in computer vision and remote sensing.  Primary performance metrics reported were Mean Average  Precision (MAP) at an intersection over union (IoU) threshold  of 0.50 (MAP @ 50), as well as MAP at multiple thresholds  from 0.50 to 0.95 (MAP @ 50 - 95) to evaluate the robustness  of a model's segmentation performance under more stringent  localization requirements, which represents how well a model  can locate and identify individual disease instances.

Fig. 3. Mean Average Precision (mAP@50 and mAP@50-95) curves for  the YOLOv26 instance segmentation model during training.

In addition to MAP, Precision and Recall were also  computed to represent the balance of false positives and false  negatives. Precision is defined as the proportion of true  positive PVY instances identified by the model out of all total  instances detected by the model; whereas, recall is defined as  the proportion of total true PVY instances identified by the  model. This type of information is especially important to seed  potato inspectors who may be able to take corrective action on  some missed PVY infections, but would need to discard entire  shipments due to a false alarm. In order to allow for the  evaluation of a model's overall performance, as well as its  performance with respect to specific classes of plants (clean  vs. PVY positive), performance was reported at both the  aggregate level and class-wise. All reported metrics were  computed on the held-out test set to ensure an unbiased  evaluation of generalization performance. Model performance  was evaluated using standard object detection metrics  including precision, recall, intersection over union (IoU), and  mean average precision (mAP), defined as follows.

Fig. 4. Box loss of the YOLOv26 instance segmentation model.

𝑇𝑃

Precision =

𝑇𝑃+𝐹𝑃                             (1)

𝑇𝑃

Recall =

𝑇𝑃+𝐹𝑁                              (2)

∣𝐵𝑝𝑟𝑒𝑑 ∩ 𝐵𝑔𝑡∣

IoU =

∣𝐵𝑝𝑟𝑒𝑑 ∪ 𝐵𝑔𝑡∣                            (3)

1

𝑁∑ 𝐴 𝑁 𝑖=1 𝑃𝑖                           (4)

mAP =

Fig. 5. Classification loss progression across training epochs

IV. RESULTS AND DISCUSSION  This section discusses how the training occurred for PVY  instance segmentation, including the model's training

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:41:31 UTC from IEEE Xplore.  Restrictions apply.

In many cases, the model was able to detect and segment  PVY-positive plants correctly, and to identify the irregular  symptoms of PVY in the canopy as separate areas. The ability  of this methodology to capture fine details of diseases at the  instance level has shown to be very effective; it would have  been much more difficult to obtain these fine detail  classifications with a bounding box or image classification  methodologies. False positives were mainly found on non- viral stressed areas, such as local discolorations and canopy  irregularities caused by environmental conditions. False  negatives were most commonly found when the PVY  symptoms were minimal, partially shaded, and/or visually  identical to the surrounding healthy foliage. Overlapping  leaves, row structures, and overall density of the canopy also  contributed to difficulties in detecting PVY symptoms in  dense canopy regions.

Fig. 6. Object loss across training epochs.

B. Performance

Quantitatively testing the proposed methodology with  respect to the held-out test data set yielded results that show  the ability to reliably locate and classify instances of plant  condition from RGB imagery alone at an overall mAP@50 of  approximately 64%, with class-wise performance of 61% for  PVY-positive plants. The results also show the decrease in the  performance of the methodology as the IoU threshold was  increased, which is consistent with the expectations, since as  the threshold becomes more restrictive, it will be increasingly  difficult to correctly align the masks. The proposed  methodology was able to achieve a precision of about 73%  and a recall of about 65%. These two metrics provide an  indication of the balance that exists between the number of  false positives and the number of missed PVY instances. High  precision indicates that the majority of PVY locations  predicted by the system are actually correct, and high recall  indicates that the system has been successful in detecting a  large percentage of the actual PVY instances. A comparison  of the performance of the system across different classes  indicated higher detection rates for the "clean" class than for  the "pvy_positive" class. The differences are due to a  combination of class imbalance (a much larger number of  images depicting healthy plants) and the fact that there is a lot  more visual variety in how PVY can manifest itself in  different plants, making it harder to predict whether a plant is  healthy or infected with PVY. Many times, the PVY-positive  images depicted small or partially occluded symptoms, which  made it difficult for the model to classify them correctly and  thereby reduce the true positive rate for the PVY class.

Fig. 8. Qualitative example of YOLOv26 instance segmentation results on  UAV RGB imagery, showing correct detection of clean and PVY-positive  potato plants with confidence scores, as well as an undetected plant instance.

C. Prevalence Estimation Under Model Misclassification

In practical field deployment, machine learning-based  disease detection systems must account for prediction errors  arising from false positive and false negative classifications.  These misclassifications can influence the estimated  infection prevalence when predictions are aggregated across  large numbers of plants. Therefore, an additional analysis was  conducted to evaluate how the current model performance  translates to field-level prevalence estimation. Let P denote  the true infection prevalence in a field, R the model recall  (true positive rate), and S the specificity (true negative rate).  The expected observed positive detection rate P̂ can be  expressed as

TABLE II.   QUANTITATIVE PERFORMANCE OF THE YOLOV26  INSTANCE SEGMENTATION MODEL ON VALIDATION AND TEST DATASETS.

Metric  Validation

Test  mAP@50  64.9%  64.0%  Precision  73.5%  ---  Recall  64.6%  ---  Clean mAP@50  94.0%  87.0%  PVY-positive mAP@50  61.0%  41.0%

𝑃̂ = 𝑃𝑅+ (1 −𝑃)(1 −𝑆)                     (5)  where the first term represents correctly detected infected  plants and the second term represents false positive detections  among healthy plants. Using the current model performance  and assuming a representative infection prevalence of 1%,  which reflects an early-stage disease monitoring scenario in  commercial lots, a prevalence estimation analysis was  conducted using a misclassification-aware calculator. The  analysis indicates that the proposed framework can provide  reasonable estimates of disease presence for early field  surveillance scenarios. The results further suggest that the

Fig. 7. Confusion matrix summarizing classification outcomes for clean  and PVY-positive classes on the test dataset.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:41:31 UTC from IEEE Xplore.  Restrictions apply.

virus Y detection: Machine learning insights,” Remote Sensing, vol. 17,  no. 10, p. 1735, 2025, doi: 10.3390/rs17101735.  [3] C. Singh, G. S. Randhawa, A. A. Farooque, Y. S. Gill, L. K. KM, M.

UAV-based detection framework would be sufficiently  accurate for surveying production potato fields, where  infection rates of approximately 5% are commonly observed.  At this scale, scanning large numbers of plants within an acre  results in relatively small binomial counting uncertainty, with  an estimated margin of error on the order of approximately  ±0.2 percentage points. However, for seed certification  programs, where acceptable infection thresholds may fall  below 0.5%, the current detection resolution and lack of  reliable individual plant-level identification may be  insufficient to distinguish extremely low infection levels.  These findings indicate that while the proposed system is well  suited for large-scale production field monitoring, further  improvements in detection sensitivity would be required for  strict seed certification applications. Thus, this analysis  shows the importance of evaluating machine learning  performance not only through standard detection metrics  (precision, recall, and mAP) but also through operational  prevalence estimation.

Singh, and K. Al-Mughrabi, “Evaluation of deep learning models for  RGB image-based detection of Potato virus Y strain symptoms (O, NO,  and NTN) in potato plants,” Smart Agricultural Technology, vol. 10, p.  100755, 2025.  [4] C. Singh, G. S. Randhawa, A. A. Farooque, Y. S. Gill, A. Fraser, L. K.

KM, et al., “AgriScout: AI-powered robot for precise detection of  PVY-infected potato plants,” Computers and Electronics in  Agriculture, vol. 238, p. 110781, 2025.  [5] L. M. Griffel and D. Delparte, “Detection of Potato virus Y in plant

foliage  using  convolutional  neural  network  classifiers  and  hyperspectral imagery,” Computers and Electronics in Agriculture,  vol. 244, p. 111499, 2026.  [6] R. Sugiura, S. Tsuda, H. Tsuji, and N. Murakami, “Virus-infected plant

detection in potato seed production field by UAV imagery,” in Proc.  2018 ASABE Annual International Meeting, American Society of  Agricultural and Biological Engineers, 2018, p. 1.  [7] M. V. Kozhekin, M. A. Genaev, E. G. Komyshev, Z. A. Zavyalov, and

D. A. Afonnikov, “Plant detection in RGB images from unmanned  aerial vehicles using segmentation by deep learning and an impact of  model accuracy on downstream analysis,” Journal of Imaging, vol. 11,  no. 1, p. 28, 2025.  [8] S. Wang, D. Xu, H. Liang, Y. Bai, X. Li, J. Zhou, C. Su, and W. Wei,

V. CONCLUSION AND FUTURE WORK

“Advances in deep learning applications for plant disease and pest  detection: A review,” Remote Sensing, vol. 17, no. 4, p. 698, 2025.  [9] T. Jia, M. Smigaj, G. Kootstra, and L. Kooistra, “Detection of diseased

This paper presented a practical approach for utilizing  machine learning for the detection and identification of Potato  Virus Y (PVY) in seed potato fields, as well as for identifying  and locating each plant within a field using RGB imagery  collected by unmanned aerial vehicles (UAVs), as well as for  applying instance segmentation to the images. The proposed  workflow integrates several methods, including polygon- based annotation, image tiling based upon masks that preserve  the original location of each plant, and the creation of dataset  versions and augmentations via Roboflow, as well as a  YOLOv26- based instance segmentation model. This provides  a complete workflow for plant-level disease detection within  a real-world field environment. The experimental results  showed that while low-cost RGB imagery can produce good  PVY-detection results, they also require the proper  preprocessing steps and instance segmentation algorithms to  achieve those results. The results indicate that the trained  model has a mean Average Precision (mAP@50) of  approximately 65%, with precision of approximately 73.5%  and recall of approximately 65%; therefore, the model  achieves excellent classification and accurate spatial  localization of both healthy and PVY-infected plants. These  results support the feasibility of using RGB-based UAV  imagery for spatially-explicit disease monitoring and show the  benefits of using instance segmentation as opposed to image- level or plot-level classification. From an operational  standpoint, the proposed pipeline provides a cost-effective and  scalable approach that aligns with current seed potato  inspection and certification practices. Since the model can  identify the exact location of infected plants, this supports  targeted field scouting and provides decision makers with  more informed options regarding disease management. Future  research efforts will include evaluating the robustness and  generalization capabilities of the models developed here by  collecting additional multi-year imagery and adding  additional fields and different potato varieties.

potato plants with UAV hyperspectral imagery,” in Proc. 14th  Workshop on Hyperspectral Imaging and Signal Processing: Evolution  in Remote Sensing (WHISPERS), IEEE, pp. 1-5, 2024.  [10] M. V. Kozhekin, M. A. Genaev, E. G. Komyshev, Z. A. Zavyalov, and

D. A. Afonnikov, “Plant detection in RGB images from unmanned  aerial vehicles using segmentation by deep learning and an impact of  model accuracy on downstream analysis,” Journal of Imaging, vol. 11,  no. 1, p. 28, 2025.  [11] C. Qi, M. Sandroni, J. C. Westergaard, E. H. R. Sundmark, M. Bagge,

E. Alexandersson, and J. Gao, “In-field early disease recognition of  potato late blight based on deep learning and proximal hyperspectral  imaging,” arXiv preprint arXiv:2111.12155, 2021.  [12] K. P. Ferentinos, “Deep learning models for plant disease detection and

diagnosis,” Computers and Electronics in Agriculture, vol. 145, pp.  311–318, 2018.  [13] S. P. Mohanty, D. P. Hughes, and M. Salathé, “Using deep learning for

image-based plant disease detection,” Frontiers in Plant Science, vol.  7, p. 1419, 2016.  [14] A. Fuentes, S. Yoon, S. C. Kim, and D. S. Park, “A robust deep-

learning-based detector for real-time tomato plant diseases and pests  recognition,” Sensors, vol. 17, no. 9, p. 2022, 2017.  [15] T. B. Shahi, C. Y. Xu, A. Neupane, and W. Guo, “Recent advances in

crop disease detection using UAV and deep learning techniques,”  Remote Sensing, vol. 15, no. 9, p. 2450, 2023.  [16] B. Liu, A. Yu, X. Zuo, Z. Xue, K. Gao, and W. Guo, “Spatial–spectral

feature classification of hyperspectral image using a pretrained deep  convolutional neural network,” European Journal of Remote Sensing,  vol. 54, no. 1, pp. 385–397, 2021.  [17] A. Milioto, P. Lottes, and C. Stachniss, “Real-time semantic

segmentation of crop and weed for precision agriculture robots  leveraging background knowledge in CNNs,” in Proc. IEEE  International Conference on Robotics and Automation (ICRA), IEEE,  pp. 2229–2235, 2018.  [18] J. Bendig, K. Yu, H. Aasen, A. Bolten, S. Bennertz, J. Broscheit, et al.,

“Combining UAV-based plant height from crop surface models,  visible, and near infrared vegetation indices for biomass monitoring in  barley,” International Journal of Applied Earth Observation and  Geoinformation, vol. 39, pp. 79–87, 2015.  [19] L. Kouadio, M. El Jarroudi, Z. Belabess, S.-E. Laasli, M. Z. K. Roni, I.


## REFERENCES

D. I. Amine, N. Mokhtari, F. Mokrini, J. Junk, and R. Lahlali, “A  review on UAV-based applications for plant disease detection and  monitoring,” Remote Sensing, vol. 15, no. 17, p. 4273, 2023.  [20] L. W. Kuswidiyanto, H. H. Noh, and X. Han, “Plant disease diagnosis

[1] G. Polder, P. M. Blok, H. A. de Villiers, J. M. van der Wolf, and J.

Kamp, “Potato virus Y detection in seed potatoes using deep learning  on hyperspectral images,” Frontiers in Plant Science, vol. 10, p. 209,  2019.  [2] S. B. Nesar, P. W. Nugent, N. K. Zidack, and B. M. Whitaker,

using deep learning based on aerial hyperspectral images: A review,”  Remote Sensing, vol. 14, no. 23, p. 6031, 2022.

“Unmanned aerial vehicle-based hyperspectral imaging for Potato

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:41:31 UTC from IEEE Xplore.  Restrictions apply.
