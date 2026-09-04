---
workspace_id: SCI-001079
doi: 10.48084/etasr.12465
title: Smart Detection of Sugarcane Leaf Rust Using UAV-Based Multispectral Imaging
  and Mask R-CNN
authors:
- family_name: Warni
  given_name: Elly
  orcid: null
- family_name: Indrabayu
  given_name: ..
  orcid: null
- family_name: Yusuf
  given_name: Muhammad
  orcid: null
- family_name: Kusyanto
  given_name: Kaisya Anindya Callista Putri
  orcid: null
- family_name: Rizal
  given_name: Muhammad H.
  orcid: null
year: 2025
extraction_engine: pymupdf
extracted_at: '2026-09-04T01:48:54.347147+00:00'
---

# Smart Detection of Sugarcane Leaf Rust Using UAV-Based Multispectral Imaging and Mask R-CNN

Engineering, Technology & Applied Science Research  Vol. 15, No. 6, 2025, 30290-30295  30290

Smart Detection of Sugarcane Leaf Rust Using  UAV-Based Multispectral Imaging and Mask  R-CNN

Elly Warni  Department of Informatics Engineering, Universitas Hasanuddin, Indonesia  elly@unhas.ac.id (corresponding author)    Indrabayu  Department of Informatics Engineering, Universitas Hasanuddin, Indonesia  indrabayu@unhas.ac.id    Muhammad Yusuf  Department of Informatics Engineering, Universitas Hasanuddin, Indonesia  yusufm17d@student.unhas.ac.id    Kaisya Anindya Callista Putri Kusyanto  Department of Informatics Engineering, Universitas Hasanuddin, Indonesia  kusyantokacp23d@student.unhas.ac.id    Muhammad H. Rizal  Department of Informatics Engineering, Universitas Teknologi Akba Makassar, Indonesia  rizal@unitama.ac.id

Received: 1 June 2025 | Revised: 14 August 2025 and 2 October 2025 | Accepted: 5 October 2025

Licensed under a CC-BY 4.0 license | Copyright (c) by the authors | DOI: https://doi.org/10.48084/etasr.12465


## ABSTRACT

Detecting and monitoring sugarcane leaf rust disease remains a significant challenge in precision  agriculture due to the complex symptoms and changing environmental conditions. This study introduces a  smart detection framework that combines Unmanned Aerial Vehicles (UAVs) equipped with multispectral  imaging with a deep learning-based Mask R-CNN model to identify and segment leaf rust-infected areas  on sugarcane leaves. The system was trained and validated using annotated multispectral images captured  from UAV footage at altitudes of 5, 6, and 7 meters above ground. Performance evaluation, based on  precision, recall, and F1 score, revealed a clear inverse relationship between detection accuracy and flight  altitude. The highest F1 Score of 0.70 was recorded at 5 meters, dropping to 0.48 at 6 meters and 0.30 at 7  meters. These results demonstrate that combining Mask R-CNN with UAV-based multispectral data has  strong potential for precise and scalable plant disease detection. Additionally, the study highlights key  factors that impact segmentation accuracy, including image resolution determined by UAV altitude,  natural shadow interference, and overlapping leaf structures. These findings support the development of  UAV- and deep learning-based plant disease detection systems, especially in tropical agricultural  environments, by enabling efficient, accurate, and field-adaptive monitoring of sugarcane leaf rust disease.

Keywords-Sugarcane Leaf Rust; Plant Disease Detection; Multispectral UAV Imaging; Mask R-CNN

commodity and included in the country's food security  framework, making sugarcane a crop of high economic  importance. Beyond its role in the national food supply,  sugarcane also supports millions of livelihoods. It relates to  energy production through bioethanol, making it a versatile  crop for both food and renewable energy sectors [3].

I.  INTRODUCTION

Sugarcane (Saccharum officinarum L.) plays a vital role in  global and regional agricultural economies, especially in  tropical and subtropical regions such as Indonesia, India, and  Brazil, where it serves as a significant raw material for sugar  production [1, 2]. In Indonesia, sugar is classified as a strategic

www.etasr.com  Warni et al.: Smart Detection of Sugarcane Leaf Rust Using UAV-Based Multispectral Imaging and …

Engineering, Technology & Applied Science Research  Vol. 15, No. 6, 2025, 30290-30295  30291

classification methods that fail to fully leverage the potential of  spatial-spectral data fusion [15, 20].

However, sugarcane productivity is significantly affected  by various biotic stresses, especially leaf diseases such as leaf  rust, caused by the fungus Puccinia melanocephala. This  disease reduces photosynthesis, weakens plant health, and can  cause yield losses of up to 40% in severe cases [4]. Leaf rust  outbreaks have been frequently reported in key production  regions and continue to threaten sustainable sugarcane farming.  These diseases not only reduce cane quality and yield but also  increase cultivation costs due to frequent chemical treatments  and disease monitoring [5]. Therefore, developing a timely and  accurate detection system is essential to minimize its effects  and sustain sugarcane production in response to increasing  global demand.

To fill these gaps, this study aims to develop and assess a  deep learning-based framework for segmenting and detecting  sugarcane leaf rust disease using multispectral images captured  by a UAV. The proposed method leverages the Mask R-CNN  architecture, known for its high accuracy in object-level  segmentation, and adapts it to handle multispectral image  channels for improved disease localization. The system's  performance will be evaluated across different flight altitudes  and preprocessing techniques to authenticate its suitability for  real-world agricultural settings. Ultimately, the research aims to  improve automated disease monitoring technologies that are  both scalable and robust for precision agriculture in sugarcane  farming.

Recent advances in precision agriculture have made UAVs  effective tools for large-scale farm monitoring. They enable  high-resolution, cost-effective, and rapid image collection  across extensive plantations, making them ideal for crop health  evaluation and disease detection. Their deployment is  expanding across various agricultural uses, from nutrient  monitoring and yield estimation to pest and disease detection  [6-9]. The agility and accessibility of UAV platforms have  revolutionized data collection in modern agriculture, offering  new  opportunities  for  intelligent  decision-making.  Furthermore, the adoption of multispectral imaging has  significantly enhanced UAVs' disease-detection capabilities.  Unlike conventional RGB cameras, multispectral sensors  acquire data beyond the visible spectrum, typically in the Near- Infrared (NIR), red-edge, and green bands, which are sensitive  to subtle alterations in leaf physiology resulting from early- stage infections [10-12]. Vegetation indices, such as the  Normalized Difference Vegetation Index (NDVI) and the  Green Normalized Difference Vegetation Index (GNDVI),  derived from these bands have been widely used to monitor  plant health and detect stress conditions. However, converting  raw multispectral data into useful disease maps remains a  complex task that often requires advanced algorithms and  specialized knowledge.

II.  METHODOLOGY

This study employs an experimental approach to develop  and assess a deep learning-based system for detecting leaf rust  disease in sugarcane using Mask R-CNN and UAV-based  multispectral imagery. The research methodology is divided  into two main stages: training and testing, as shown in the  workflow diagram above. Each stage is described in detail  below to demonstrate the procedural rigor necessary for  reproducibility and scientific validation. The proposed system  design is illustrated in Figure 1.


> **Table I shows the specifications of the UAV and sensor**

> used in the study. The UAV is the DJI Matrice 300 RTK, 
equipped with a MicaSense RedEdge-MX camera featuring 
five main spectral bands—Blue, Green, Red, RedEdge, and 
NIR—and their respective wavelength ranges. At a flight 
altitude of 5 meters, the spatial resolution is 0.25 cm/pixel, 
allowing for detailed image capture for precision analysis.

The research begins by collecting image data from frames  of  UAV-recorded  multispectral  imagery  of  sugarcane  plantations. These frames serve as the main input for both the  training and testing phases. The dataset is then divided into two  groups: training and validation. This split helps ensure that the  model's performance can be evaluated objectively during  training. Each data subset is manually annotated using the  LabelMe tool. This process involves marking the infected areas  on sugarcane leaves with polygon-shaped masks, producing  ground truth data essential for supervised learning. The  annotations are stored in JSON format and then converted into  the COCO format, which is compatible with Mask R-CNN.

Despite  these  technological  advancements,  many  limitations remain in current disease detection methods.  Traditional methods still depend heavily on manual scouting,  which is labor-intensive, subjective, and impractical for large- scale use. On the other hand, automated systems based solely  on RGB imagery have difficulty distinguishing between  overlapping leaves, shadows, and discoloration caused by non- pathogenic stress, resulting in a high false detection rate [13- 15]. Furthermore, traditional machine learning models often  struggle to capture the spatial and morphological complexities  of plant diseases, especially when symptoms are visually subtle  or obscured by environmental factors. Although deep learning  models such as Convolutional Neural Networks (CNNs) have  achieved significant success in image classification and object  detection, their use in plant disease detection is still in its early  stages. Among these, Mask R-CNN has demonstrated strong  performance in the instance segmentation of leaf rust-infected  regions [16-18]. However, a significant research gap remains in  integrating Mask R-CNN with UAV-based multispectral  imagery to detect specific diseases in sugarcane [19]. Most  existing studies either rely on RGB datasets or employ basic

A. Model Training

Once the dataset is prepared and annotated, the training  process starts. The training data and corresponding labels are  used to train the Mask R-CNN model, which is set up with a  specific backbone architecture (usually ResNet-101) and tuned  hyperparameters  to  improve  performance.  The  model  iteratively learns to distinguish healthy from infected leaf  regions via backpropagation and loss minimization. A key  stopping criterion is based on the loss value. Training continues  until the total loss reaches or drops below a set threshold of 0.2.  The loss function consists of three parts: classification loss,  bounding-box regression loss, and mask segmentation loss. If

www.etasr.com  Warni et al.: Smart Detection of Sugarcane Leaf Rust Using UAV-Based Multispectral Imaging and …

Engineering, Technology & Applied Science Research  Vol. 15, No. 6, 2025, 30290-30295  30292

the model does not meet this criterion, training is repeated or  adjusted until satisfactory results are achieved.

across epochs. In the subplot for 89 epochs, the model initially  shows a high total loss of over 2.0, which steadily decreases  throughout the training cycle. Although the loss trend declines,  the rate of decrease slows significantly after the initial 40  epochs.

B. Model Validation

During training, the validation dataset is used to monitor  and evaluate the model’s generalization ability. The validation  step doesn't influence the learning process but offers metrics  such as precision, recall, and F1 Score to assess how well the  model performs on unseen data. This evaluation helps identify  overfitting and provides an empirical basis for selecting the  best model.

All individual loss components—bbox, class, and mask  loss—show a similar pattern, approaching values near 0.1–0.2  by the final epoch. However, the total loss at the end remains  relatively high compared to more extended training periods.  The 100-epoch curve (see Figure 2) demonstrates improved  convergence compared to earlier epochs. The total loss  decreases more steadily and consistently, dropping below 0.4  by the end of training. Notably, the bbox and class losses each  decline nearly 0.05, while the mask loss remains just above 0.1.  This indicates that training beyond 89 epochs improves the  model's ability to tune its parameters and segment input data  more accurately.

Over 168 epochs, the downward trend in all loss  components becomes more noticeable. The graph shows a  steady decrease in loss with few fluctuations, indicating  stability and efficient learning. By the final epoch, the total loss  nears 0.2, while individual component losses stay below 0.1.  This demonstrates that extended training improves the model's  predictions for more complex sugarcane leaf rust cases. Finally,  the 182-epoch curve exhibits the best convergence among the  four scenarios. The total loss levels off just above 0.2, while  component losses (bbox, class, mask) remain consistently low,  especially after the 100th epoch. This curve indicates a highly  trained model with minimal overfitting or underfitting,  suggesting that epoch 180 (as shown in previous quantitative  analysis) produced the best-performing model in Experiment 1.

From the overall visualizations, several insights emerge.  First, the number of epochs plays a crucial role in reducing  loss, with noticeable improvements beyond 100 epochs.  Second, all component losses decrease together, showing a  balanced  learning  process  across  object  localization,  classification, and segmentation. Third, model stability  improves with longer training, especially after 150 epochs,  when loss fluctuations become minimal. Therefore, these loss  curves not only demonstrate the effectiveness of the Mask R- CNN architecture in segmenting disease on sugarcane leaves  but also support the empirical finding that epoch 180 achieved  the lowest total loss (0.2086), justifying its selection as the final  model checkpoint for deployment.

Fig. 1.   Proposed system design.

TABLE I.   UAV AND SENSOR SPECIFICATIONS

The visual outputs generated by the detection model are  presented in Figures 3, 4, and 5. Specifically, Figure 3  illustrates the detection results at a flight altitude of 5 meters,  Figure 4 shows the outcomes at 6 meters, and Figure 5 presents  the results at 7 meters. These figures collectively demonstrate  the model's performance in identifying leaf rust-infected areas  on sugarcane leaves from varying aerial perspectives, providing  valuable insight into its robustness across different spatial  resolutions and operational conditions.

Component  Specification  UAV Model DJI Matrice 300 RTK Camera MicaSense RedEdge-MX Bands  Blue (475±20nm), Green (560±20nm), Red (668±10nm),

RedEdge (717±10nm), NIR (840±40nm) GSD @ 5m 0.25 cm/pixel

III.  RESULTS AND DISCUSSION

The training performance of the Mask R-CNN model in  Experiment 1 is depicted in the loss curve plots illustrated in  Figure 2, which include four subplots corresponding to 89, 100,  168, and 182 epochs, respectively. Each graph displays the  total loss, bounding box loss, classification loss, and mask loss

www.etasr.com  Warni et al.: Smart Detection of Sugarcane Leaf Rust Using UAV-Based Multispectral Imaging and …

Engineering, Technology & Applied Science Research  Vol. 15, No. 6, 2025, 30290-30295  30293

Fig. 2.   Visualization of Mask R-CNN loss.


> **Table II shows the performance evaluation results of the**

> sugarcane leaf rust disease detection system based on UAV 
flight heights of 5, 6, and 7 meters, using ten test frames taken 
from UAV imagery. The metrics include precision, recall, and 
F1 Score, which measure the system's accuracy, sensitivity, and 
overall balanced performance.


> **Table III presents a performance comparison of four**

> segmentation models, Mask R-CNN, U-Net, DeepLabV3+, and 
YOLO-Seg, in detecting rust-infected sugarcane leaf areas, 
using IoU, Dice coefficient, Precision, Recall, and F1-Score 
metrics. The results show that U-Net achieved the highest 
scores across all metrics (IoU: 0.2643, Dice: 0.3725, Precision: 
0.8287, Recall: 0.3388, F1-Score: 0.3725), followed closely by 
DeepLabV3+. Mask R-CNN recorded lower performance 
compared to U-Net and DeepLabV3+, particularly in IoU and 
Recall, but maintained competitive precision (0.6378), 
indicating its ability to reduce false positive predictions. 
YOLO-Seg, although known for its speed in object detection, 
demonstrated very low performance across all metrics, 
suggesting that this model is less suitable for detailed disease 
segmentation on multispectral leaf imagery in the given 
dataset. These findings indicate that, for a limited dataset with 
high visual complexity, encoder–decoder-based architectures 
such as U-Net and DeepLabV3+ can achieve better 
generalization than Mask R-CNN, whereas pure object-
detection-based methods like YOLO-Seg are not optimal for 
high-resolution instance segmentation.

Fig. 3.    Example of detection results at an altitude of 5 meters.

Fig. 4.    Example of detection results at an altitude of 6 meters.

www.etasr.com  Warni et al.: Smart Detection of Sugarcane Leaf Rust Using UAV-Based Multispectral Imaging and …

Engineering, Technology & Applied Science Research  Vol. 15, No. 6, 2025, 30290-30295  30294

findings highlight the significance of low-altitude UAV  imagery and controlled lighting conditions in improving the  effectiveness of automated plant disease detection systems.

ACKNOWLEDGMENT  This work was supported by the Lembaga Penelitian dan  Pengabdian Masyarakat (LPPM) Universitas Hasanuddin  through a research grant (01260/UN4.22/PT.01.03/2025).


## REFERENCES

[1] T. F. Cardoso et al., "A regional approach to determine economic,

environmental and social impacts of different sugarcane production  systems in Brazil," Biomass and Bioenergy, vol. 120, pp. 9–20, Jan.  2019, https://doi.org/10.1016/j.biombioe.2018.10.018.  [2] Q. Wu, A. Li, P. Zhao, H. Xia, Y. Zhang, and Y. Que, "Theory to

Fig. 5.   Fig. 5. Example of detection results at an altitude of 7 meters

practice: a success in breeding sugarcane variety YZ08–1609 known as  the King of Sugar," Frontiers in Plant Science, vol. 15, May 2024,  https://doi.org/10.3389/fpls.2024.1413108.  [3] S. D. Artikanur, Widiatmaka, Y. Setiawan, and Marimin, "An

TABLE II.   PERFORMANCE METRICS

Performance Metrics  Precision  Recall  F1 Score  5  (m)

Evaluation of Possible Sugarcane Plantations Expansion Areas in  Lamongan, East Java, Indonesia," Sustainability, vol. 15, no. 6, Jan.  2023, Art. no. 5390, https://doi.org/10.3390/su15065390.  [4] M. S. Camargo et al., "Potential prophylactic role of silicon against

Frame

7  (m)  1 0.74 0.64 0.5 1 0.36 0.25 0.85 0.46 0.33 2 0.62 0.68 0.8 0.88 0.38 0.14 0.73 0.43 0.24 3 0.41 0.59 1 1 0.5 0.21 0.58 0.54 0.35 4 0.52 0.5 0.83 0.8 0.43 0.23 0.63 0.46 0.36 5 0.63 0.69 1 1 0.41 0.3 0.76 0.51 0.46 6 0.35 0.56 0.83 1 0.36 0.23 0.52 0.44 0.36 7 0.56 0.5 0.86 0.75 0.39 0.18 0.64 0.44 0.3 8 0.62 0.65 0.78 1 0.58 0.17 0.76 0.61 0.28 9 0.65 0.67 0.8 1 0.4 0.09 0.79 0.5 0.17 10 0.77 0.81 0.71 0.89 0.31 0.12 0.83 0.45 0.2

6   (m)

7   (m)

5  (m)

6  (m)

7  (m)

5  (m)

6  (m)

brown rust (Puccinia melanocephala) in sugarcane," European Journal  of Plant Pathology, vol. 157, no. 1, pp. 77–88, May 2020,  https://doi.org/10.1007/s10658-020-01982-2.  [5] R. Selvakumar and R. Viswanathan, "Sugarcane rust: changing disease

dynamics and its management," Journal of Sugarcane Research, vol. 9,  no. 2, pp. 97-118, 2019, https://doi.org/10.37580/JSR.2019.2.9.97-118.  [6] D. C. Tsouros, S. Bibi, and P. G. Sarigiannidis, "A Review on UAV-

Based Applications for Precision Agriculture," Information, vol. 10, no.  11, Nov. 2019, Art. no. 349, https://doi.org/10.3390/info10110349.  [7] T. B. Shahi, C.-Y. Xu, A. Neupane, and W. Guo, "Recent Advances in

TABLE III.   COMPARISON OF SEGMENTATION MODELS

Crop Disease Detection Using UAV and Deep Learning Techniques,"  Remote Sensing, vol. 15, no. 9, Jan. 2023, Art. no. 2450,  https://doi.org/10.3390/rs15092450.  [8] Z. Zhang and L. Zhu, "A Review on Unmanned Aerial Vehicle Remote

Fold  MASK R-

CNN  Unet  DeepLabV3+  YOLO-

Seg  IoU 0.1830 0.2643 0.2531 0.0012 Dice 0.2923 0.3725 0.3620 0.0024 Precision 0.6378 0.8287 0.7302 0.0096 Recall 0.2274 0.3388 0.3274 0.0014 F1-Score 0.2923 0.3725 0.3620 0.0024

Sensing:  Platforms,  Sensors,  Data  Processing  Methods,  and  Applications," Drones, vol. 7, no. 6, June 2023, Art. no. 398,  https://doi.org/10.3390/drones7060398.  [9] P. Ahmadi, S. Mansor, B. Farjad, and E. Ghaderpour, "Unmanned Aerial

Vehicle (UAV)-Based Remote Sensing for Early-Stage Detection of  Ganoderma," Remote Sensing, vol. 14, no. 5, Jan. 2022, Art. no. 1239,  https://doi.org/10.3390/rs14051239.  [10] C. Wang et al., "Cotton Blight Identification with Ground Framed

IV.  CONCLUSION   The research findings demonstrate that the sugarcane leaf  rust detection system was successfully developed using the  Mask R-CNN algorithm as the primary method for disease  identification. The system demonstrated the ability to segment  rust-infected areas on sugarcane leaves using data from UAV  multispectral images at heights of 5, 6, and 7 meters above  ground. The system achieved F1 Scores of 0.70, 0.48, and 0.30  for sugarcane leaf rust detection at flight altitudes of 5, 6, and 7  meters, respectively (see Table I). These results show a notable  drop in the detection accuracy of leaf rust-infected areas as  UAV altitude increases. Several factors contributed to the  lower F1 scores, including the high visual similarity between  rust-infected and naturally dried leaves, overlapping foliage  that causes shadowing under sunlight, and direct sunlight  exposure, which changes leaf color and texture. These  conditions introduced noise into the segmentation process,  causing false predictions. Additionally, increasing UAV flight  altitude reduced image resolution, further reducing the model’s  ability to accurately detect and localize infected areas. These

Canopy Photo-Assisted Multispectral UAV Images," Agronomy, vol. 13,  no.  5,  May  2023,  Art.  no.  1222,  https://doi.org/10.3390/agronomy13051222.  [11] K. Liao, F. Yang, H. Dang, Y. Wu, K. Luo, and G. Li, "Detection of

Eucalyptus Leaf Disease with UAV Multispectral Imagery," Forests,  vol.  13,  no.  8,  Aug.  2022,  Art.  no.  1322,  https://doi.org/10.3390/f13081322.  [12] C. Nguyen, V. Sagan, J. Skobalski, and J. I. Severo, "Early Detection of

Wheat Yellow Rust Disease and Its Impact on Terminal Yield with  Multi-Spectral UAV-Imagery," Remote Sensing, vol. 15, no. 13, Jan.  2023, Art. no. 3301, https://doi.org/10.3390/rs15133301.  [13] P. Dhoundiyal, V. Sharma, S. Vats, and P. Rawat, "A Progressive

Hierarchical Model for Plant Disease Diagnosis," SN Computer Science,  vol. 6, no. 2, Jan. 2025, Art. no. 102, https://doi.org/10.1007/s42979- 024-03582-x.  [14] P. S. Thakur, P. Khanna, T. Sheorey, and A. Ojha, "Trends in vision-

based machine learning techniques for plant disease identification: A  systematic review," Expert Systems with Applications, vol. 208, Dec.  2022, Art. no. 118117, https://doi.org/10.1016/j.eswa.2022.118117.

www.etasr.com  Warni et al.: Smart Detection of Sugarcane Leaf Rust Using UAV-Based Multispectral Imaging and …

Engineering, Technology & Applied Science Research  Vol. 15, No. 6, 2025, 30290-30295  30295

[15] M. Shoaib et al., "An advanced deep learning models-based plant

disease detection: A review of recent research," Frontiers in Plant  Science, vol. 14, Mar. 2023, https://doi.org/10.3389/fpls.2023.1158933.  [16] W. Ali, G. Wang, K. Ullah, M. Salman, and S. Ali, "Substation Danger

Sign Detection and Recognition using Convolutional Neural Networks,"  Engineering, Technology & Applied Science Research, vol. 13, no. 1,  pp. 10051–10059, Feb. 2023, https://doi.org/10.48084/etasr.5476.  [17] R. Srinivasan, R. Korah, and M. Ravichandran, "Revolutionizing

Diagnostic Insights: Exploring Advanced Image Processing Techniques  and Neural Networks in Traditional Indian Medicine," Engineering,  Technology & Applied Science Research, vol. 15, no. 1, pp. 19214– 19220, Feb. 2025, https://doi.org/10.48084/etasr.8975.  [18] S. Bondre and D. Patil, "Crop disease identification segmentation

algorithm based on Mask-RCNN," Agronomy Journal, vol. 116, no. 3,  pp. 1088–1098, 2024, https://doi.org/10.1002/agj2.21387.  [19] N. Amarasingam, F. Gonzalez, A. S. A. Salgadoe, J. Sandino, and K.

Powell, "Detection of White Leaf Disease in Sugarcane Crops Using  UAV-Derived RGB Imagery with Existing Deep Learning Models,"  Remote Sensing, vol. 14, no. 23, Jan. 2022, Art. no. 6137,  https://doi.org/10.3390/rs14236137.  [20] F. Shahoveisi, H. Taheri Gorji, S. Shahabi, S. Hosseinirad, S. Markell,

and F. Vasefi, "Application of image processing and transfer learning for  the detection of rust disease," Scientific Reports, vol. 13, no. 1, Mar.  2023, Art. no. 5133, https://doi.org/10.1038/s41598-023-31942-9.

www.etasr.com  Warni et al.: Smart Detection of Sugarcane Leaf Rust Using UAV-Based Multispectral Imaging and …
