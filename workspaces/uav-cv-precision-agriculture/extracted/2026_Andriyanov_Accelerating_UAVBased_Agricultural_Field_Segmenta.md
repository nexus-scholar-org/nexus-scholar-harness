---
workspace_id: SCI-001085
doi: 10.1109/synchroinfo70145.2026.11613432
title: Accelerating UAV-Based Agricultural Field Segmentation Using YOLOv11 and Rockchip
  NPU Quantization
authors:
- family_name: Andriyanov
  given_name: N.
  orcid: null
- family_name: Dementiev
  given_name: V.
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:41.477114+00:00'
---

# Accelerating UAV-Based Agricultural Field Segmentation Using YOLOv11 and Rockchip NPU Quantization

Accelerating UAV-Based Agricultural Field  Segmentation Using YOLOv11 and Rockchip NPU

2026 Systems of Signal Synchronization, Generating and Processing in Telecommunications (SYNCHROINFO) | 979-8-3195-0584-2/26/$31.00 ©2026 IEEE | DOI: 10.1109/SYNCHROINFO70145.2026.11613432

Quantization

Nikita Andriyanov   Artificial Intelligence Department  Financial Univeristy under the Government of the Russian

Vitaly Dementiev   Radio engineering, Telecommunications and Information

Protection Department  Ulyanovsk State Technical University

Federation  Moscow, Russia

Ulyanovsk, Russia

hierarchical visual features from complex image data [4].  Furthermore,  transformer-based  architectures  have  demonstrated superior representation learning capabilities by  modeling long-range dependencies through self-attention  mechanisms, enabling substantial improvements in computer  vision tasks [5]. These developments have accelerated the  adoption of artificial intelligence technologies across numerous  domains, including precision agriculture, autonomous vehicles,  industrial inspection, and environmental monitoring.


## Abstract— Real-time analysis of unmanned aerial vehicle

(UAV) imagery is an important task in precision agriculture. 
However, deploying deep learning models on embedded 
platforms is challenging due to limited computational resources 
and power constraints. This paper investigates the acceleration of 
agricultural image segmentation using YOLOv11 instance 
segmentation models, INT8 quantization, and Rockchip NPU 
deployment. A combined dataset consisting of real UAV images 
and synthetic samples was used for crop, weed, and soil 
segmentation. YOLOv11n-seg and YOLOv11s-seg models were 
trained, quantized, converted to the RKNN format, and deployed 
on an Orange Pi 5+ platform based on the RK3588 processor. 
Experimental results show that INT8 quantization reduces 
segmentation accuracy by approximately 2–3 percentage points 
while providing a 2.6–2.7× reduction in inference latency. The 
obtained results demonstrate the feasibility of real-time 
agricultural video analytics on low-power embedded hardware 
and confirm the effectiveness of Rockchip-based edge AI 
platforms for UAV applications.

The increasing availability of unmanned aerial vehicles  (UAVs) has further expanded the practical applicability of  computer vision systems in agriculture. Compared to  conventional satellite monitoring platforms, UAVs provide  significantly higher spatial resolution, flexible deployment  schedules, and lower operational costs for localized field  inspection. High-resolution aerial imagery enables the  identification of small weed clusters, crop stress symptoms,  and field anomalies that may remain undetected in lower- resolution satellite observations. As a result, UAV-based  monitoring has become an essential component of modern  precision agriculture systems.

Keywords— UAV imagery, precision agriculture, instance  segmentation, YOLOv11seg, weed detection, INT8 quantization,  RKNN, Rockchip RK3588, edge AI, embedded computer vision

Several recent studies have demonstrated the effectiveness  of deep learning methods for weed detection and segmentation  using UAV imagery. Shahi et al. performed a comprehensive  comparison of state-of-the-art segmentation architectures on  aerial agricultural datasets and reported that encoder-decoder  architectures based on U-Net achieved strong performance in  weed segmentation tasks [6]. To facilitate further research in  this area, the same research group introduced the CoFly- WeedDB dataset, which provides annotated UAV imagery  specifically designed for deep learning-based weed detection  and segmentation [7]. The availability of publicly accessible  datasets has significantly accelerated the development and  evaluation of modern agricultural computer vision algorithms.

I. INTRODUCTION

The rapid growth of precision agriculture has created a  strong demand for intelligent monitoring systems capable of  providing accurate and timely information about crop  conditions. Modern agricultural enterprises increasingly rely on  remote sensing technologies to improve productivity, reduce  resource consumption, and minimize environmental impact.  Among various agricultural challenges, weed infestation  remains one of the most significant factors affecting crop yield  and production efficiency. Weeds compete with cultivated  plants for nutrients, water, and sunlight, leading to substantial  economic losses and excessive herbicide usage. Consequently,  the development of automated weed detection and field  monitoring systems has become an important research  direction in modern agricultural engineering.

In addition to conventional RGB datasets, recent research  has increasingly focused on multispectral and multitemporal  data acquisition. The WeedsGalore dataset represents one of  the most comprehensive publicly available benchmarks for  crop and weed segmentation, incorporating RGB, red-edge,  and near-infrared spectral bands collected from UAV platforms  under different environmental conditions [8]. Similarly, the

Recent advances in deep learning have significantly  improved  object  detection  and  image  segmentation  performance [1–3], primarily due to the development of  convolutional neural networks (CNNs) capable of extracting

979-8-3195-0584-2/26/$31.00 ©2026 IEEE

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:41:14 UTC from IEEE Xplore.  Restrictions apply.

In this context, specialized neural processing units (NPUs)  have become increasingly attractive due to their ability to  perform  massively  parallel  inference  operations  with  significantly lower power consumption than conventional  CPUs and GPUs. The Rockchip RK3588 platform represents  one of the most promising embedded AI solutions currently  available, integrating an NPU capable of delivering up to 6  TOPS of computational performance while maintaining low  energy consumption [15].

recently proposed BAWSeg benchmark provides multispectral  aerial imagery for barley weed segmentation and highlights the  importance of spectral information for improving segmentation  accuracy in challenging agricultural environments [9]. These  studies indicate that data diversity and acquisition conditions  play a crucial role in the generalization capability of  segmentation models.

Among  contemporary  real-time  computer  vision  architectures, the YOLO family has attracted substantial  attention due to its favorable balance between detection  accuracy and computational efficiency. Lightweight variants of  YOLO-based models have been successfully applied to  agricultural monitoring tasks, including crop counting, disease  identification, and weed detection. A recent example is AGRI- YOLO, a lightweight adaptation of YOLOv11 designed  specifically for corn weed detection, which demonstrated  competitive detection accuracy while significantly reducing  computational complexity [10]. Such developments indicate  the growing importance of efficient deep learning architectures  for edge deployment in agricultural environments.

To facilitate deployment on Rockchip-based hardware, the  RKNN Toolkit provides a dedicated software framework for  converting and optimizing neural network models for  execution on the integrated NPU [16]. Furthermore, the  Ultralytics RKNN export pipeline enables efficient conversion  of YOLO models into a hardware-optimized format suitable for  embedded deployment [17]. These technologies provide a  practical pathway toward implementing real-time agricultural  video analytics directly on edge devices without relying on  cloud-based computation.

Motivated by these developments, this study investigates  the acceleration of UAV-based agricultural field segmentation  through the integration of YOLOv11seg models, INT8  quantization, and Rockchip NPU deployment. The proposed  approach combines real UAV imagery with synthetically  generated training samples to improve segmentation robustness  while maintaining computational efficiency. Two segmentation  architectures,  YOLOv11n-seg  and  YOLOv11s-seg,  are  evaluated before and after RKNN conversion on an Orange Pi  5+ platform based on the RK3588 processor.

The latest generation of the YOLO framework, YOLOv11,  introduces several architectural improvements aimed at  increasing accuracy while maintaining real-time inference  performance [11]. In addition to object detection, YOLOv11  supports  instance  segmentation,  enabling  pixel-level  localization of objects within a scene [12]. This capability is  particularly important for agricultural applications, where  precise delineation of crop rows, weeds, and soil regions is  required for site-specific treatment and decision-making.  Compared to conventional object detection approaches,  instance  segmentation  provides  more  detailed  spatial  information that can be directly utilized by precision spraying  and autonomous navigation systems.

- The main contributions of this work are summarized as  follows:

A combined agricultural segmentation dataset consisting of  real UAV imagery and synthetic samples is developed for field  and weed segmentation tasks.

Despite the remarkable progress achieved in deep learning- based agricultural monitoring, practical deployment of  segmentation models on UAV onboard computing platforms  remains challenging. High-performance neural networks often  require  substantial  computational  resources,  memory  bandwidth, and power consumption. These requirements  conflict with the strict energy and hardware constraints of  embedded systems deployed on aerial platforms. Consequently,  model compression and acceleration techniques have become  critical components of modern edge artificial intelligence  systems.

– The segmentation performance of YOLOv11n-seg and  YOLOv11s-seg architectures is evaluated for agricultural video  analytics applications.

An INT8 quantization workflow and RKNN deployment  pipeline targeting the Rockchip RK3588 NPU are implemented  and analyzed.

– The trade-off between segmentation accuracy and  inference latency is investigated, demonstrating the feasibility  of real-time agricultural video processing on low-power  embedded hardware.

Among various optimization approaches, neural network  quantization has emerged as one of the most effective  techniques for reducing computational complexity while  preserving model accuracy. By converting floating-point  operations into low-precision integer arithmetic, quantization  decreases memory requirements, reduces energy consumption,  and accelerates inference execution on specialized hardware  accelerators [13]. Such optimizations are particularly important  for agricultural UAV applications, where battery capacity and  onboard computational resources are inherently limited.

The remainder of this paper is organized as follows. Section  II reviews related work on deep learning-based weed  segmentation, YOLO-based agricultural monitoring systems,  and edge AI acceleration techniques. Section III describes the  proposed  methodology,  including  dataset  preparation,  segmentation  architecture,  quantization  workflow,  and  hardware deployment. Section IV presents the experimental  setup and evaluation metrics. Section V discusses the obtained  results, while Section VI concludes the paper and outlines  future research directions.

Recent developments in edge artificial intelligence have  demonstrated the feasibility of executing advanced deep  learning models on low-power embedded hardware [14].

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:41:14 UTC from IEEE Xplore.  Restrictions apply.

II. RELATED WORKS

The experimental dataset consists of both real UAV  imagery and synthetically generated samples. Synthetic images  were introduced to increase data diversity and provide accurate  pixel-level annotations for segmentation. All images were  resized to 512×512 pixels and annotated for three classes: crop  vegetation, weeds, and soil background. The dataset was  divided into training and testing subsets while preserving class  proportions. The resulting class distribution is presented in  Table I.

Recent advances in computer vision have enabled the  widespread adoption of deep learning methods for image  analysis across various domains, including remote sensing,  robotics, and agriculture. Convolutional neural networks  (CNNs) remain the foundation of modern visual recognition  systems [4], while transformer-based architectures have  demonstrated improved capability in modeling long-range  dependencies and semantic context [5]. These approaches have  been successfully applied to satellite image analysis [1], robotic  navigation in horticultural environments [2], and industrial  machine vision systems operating under real-time constraints [3].

TABLE I.   DATASET DISTRIBUTION

Class  Training Set (%)  Test Set (%)  Crop  68  70  Weed  22  20  Soil  10  10

In agriculture, UAV imagery has become an important source  of high-resolution data for crop and weed monitoring. Shahi et al.  compared several deep learning architectures for weed detection  using UAV images and demonstrated the effectiveness of  semantic segmentation approaches in agricultural scenarios [6].  The development of publicly available datasets has further  accelerated research in this field. CoFly-WeedDB provides  annotated UAV imagery for weed detection and species  identification [7], while WeedsGalore and BAWSeg extend the  concept toward multispectral crop and weed segmentation under  varying environmental conditions [8, 9].

An example of a UAV image used during model training is  shown in Fig. 1.

Among modern object detection frameworks, the YOLO  family has gained considerable attention due to its balance  between accuracy and computational efficiency. AGRI-YOLO  demonstrated that lightweight modifications of YOLOv11 can  achieve competitive weed detection performance while  reducing computational complexity [10]. The latest YOLOv11  architecture additionally supports instance segmentation,  making it suitable for precision agriculture applications that  require pixel-level object localization [11, 12].

Efficient deployment of deep learning models on embedded  platforms remains a challenging task because of limited  computational and energy resources. Quantization techniques  reduce memory consumption and inference latency while  preserving most of the original model accuracy [13]. Recent  studies on Edge AI systems have highlighted the importance of  lightweight  neural  networks  for  resource-constrained  agricultural applications [14]. In this context, the RK3588  platform equipped with a dedicated neural processing unit  (NPU) [15] and the RKNN deployment framework [16, 17]  provide a practical solution for real-time execution of deep  learning models on edge devices.

Fig. 1. Example images from the UAV training dataset

The  segmentation  task  was  performed  using  the  YOLOv11seg  architecture.  Two  model  variants  were  investigated: YOLOv11n-seg and YOLOv11s-seg. The nano  version provides lower computational complexity and faster  inference, whereas the small version contains a larger number  of parameters and is expected to achieve higher segmentation  accuracy. The segmentation head produces instance masks that  enable pixel-level localization of agricultural objects.

To deploy the trained models on embedded hardware, a  conversion  pipeline  based  on  RKNN  Toolkit2  was  implemented. First, trained PyTorch models were exported to  the ONNX format. Next, post-training INT8 quantization was  applied using a representative calibration dataset. Finally, the  optimized models were converted into the RKNN format and  executed on the Rockchip neural processing unit. The complete  processing pipeline is illustrated in Fig. 2.

Despite significant progress in agricultural segmentation  and embedded AI deployment, limited attention has been paid  to the combined use of YOLOv11 instance segmentation, INT8  quantization, and Rockchip NPU acceleration for real-time  UAV video analytics. This gap motivates the present study.

III. MATERIALS AND METHODS

The proposed approach is aimed at accelerating UAV video  analytics for agricultural monitoring through the integration of  YOLOv11 instance segmentation, INT8 quantization, and  Rockchip NPU deployment. The overall workflow includes  dataset preparation, model training, conversion to the RKNN  format, and execution on the embedded hardware platform.

Experimental evaluation was performed on an Orange Pi  5+ single-board computer based on the Rockchip RK3588  system-on-chip. The platform integrates a dedicated neural  processing unit supporting INT8 inference acceleration with a  theoretical performance of up to 6 TOPS.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:41:14 UTC from IEEE Xplore.  Restrictions apply.

In addition, the mean Average Precision at an intersection- over-union threshold of 0.5 (mAP@0.5) was used as the  primary metric for comparing segmentation models. Inference  latency was measured in milliseconds and used to evaluate the  effectiveness of INT8 quantization and NPU acceleration.

V. RESULTS AND DISCUSSION

The  experimental  results  demonstrate  that  both  YOLOv11seg  models  provide  reliable  segmentation  performance for agricultural UAV imagery. As expected, the  larger YOLOv11s-seg model achieved higher accuracy  compared to the lightweight YOLOv11n-seg variant. However,  the improvement in segmentation quality was accompanied by  increased computational complexity and inference latency.  Examples of instance segmentation results obtained on the test  dataset are presented in Fig. 3. The figure includes original  UAV images, ground-truth masks, and model predictions.  Visual inspection indicates that both models correctly identify  crop rows and weed regions, while the small model generally  produces more accurate object boundaries and fewer false- positive predictions.

Fig. 2. Proposed  workflow  including  YOLOv11seg  training,  INT8  quantization, RKNN conversion, and deployment on the Rockchip platform

All RKNN models were executed directly on the NPU,  while the original YOLOv11 models were evaluated in their  native format for comparison. The influence of quantization on  segmentation accuracy and inference speed was analyzed in  subsequent experiments.

To evaluate the influence of quantization and hardware  acceleration, the original PyTorch models were compared with  their RKNN counterparts executed on the Rockchip NPU. The  obtained results are summarized in Table II.

IV. EXPERIMENTAL SETUP

The  models  were  trained  using  the  Ultralytics  implementation of YOLOv11seg. Training was performed for  200 epochs with a batch size of 16. Input images were resized  to 512×512 pixels. Data augmentation included random  horizontal flipping, rotation, brightness adjustment, and  contrast variation in order to improve model robustness under  different UAV acquisition conditions. Two segmentation  models were evaluated: YOLOv11n-seg and YOLOv11s-seg.  After training, the models were exported to the ONNX format  and converted to RKNN using RKNN Toolkit2. INT8 post- training quantization was performed using a calibration subset  containing 100 representative images randomly selected from  the training dataset. The evaluation was conducted on an  Orange Pi 5+ single-board computer equipped with the  Rockchip RK3588 processor and integrated NPU. Inference  latency was measured using RKNN runtime tools, while  segmentation quality was assessed on the independent test  dataset.

Fig. 3. Examples of instance segmentation results on the test dataset: original  images, ground-truth masks, and model predictions

TABLE II.   COMPARISON OF SEGMENTATION EFFICIENCY AND

INFERENCE PERFORMANCE

Model  Precision  Recall  mAP@0.5  Latency

The following metrics were used for quantitative  evaluation:

(ms)  YOLOv11n-seg.pt  0.84  0.78  0.85  31  YOLOv11s-seg.pt  0.87  0.81  0.88  43  YOLOv11n-seg.rknn  0.82  0.76  0.82  12  YOLOv11s-seg.rknn  0.85  0.79  0.85  16

TP ecision + = Pr ,      (1)

FP TP

TP call + = Re ,      (2)

The results indicate that INT8 quantization introduces only  a moderate reduction in segmentation quality. For both  architectures, the decrease in mAP@0.5 is approximately 2–3  percentage points after conversion to the RKNN format.  Similar trends can be observed for Precision and Recall  metrics. Despite this loss in accuracy, the quantized models  maintain stable segmentation performance and preserve the  ability to correctly identify crop and weed regions.

FN TP

TP IoU + + = ,     (3)

FN FP TP

where TP, FP, and FN denote true positive, false positive, and  false negative predictions, respectively.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:41:14 UTC from IEEE Xplore.  Restrictions apply.

A significantly larger impact is observed in inference speed.  The RKNN models executed on the Rockchip NPU achieve a  latency reduction of approximately 2.6× for YOLOv11n-seg  and 2.7× for YOLOv11s-seg compared to the original PyTorch  implementations. Such acceleration is particularly important  for onboard UAV applications, where real-time processing and  low power consumption are critical requirements. The  comparison between the nano and small variants reveals a  typical trade-off between accuracy and computational  efficiency. The YOLOv11n-seg model provides the lowest  latency and therefore represents an attractive solution for  highly resource-constrained platforms. In contrast, YOLOv11s- seg delivers superior segmentation quality while still  maintaining real-time performance after RKNN optimization.  Overall, the obtained results confirm that the combination of  YOLOv11 instance segmentation, INT8 quantization, and  Rockchip NPU acceleration provides an effective framework  for real-time agricultural video analytics. The proposed  approach enables deployment on low-power embedded  hardware while preserving segmentation accuracy at a level  suitable for practical precision agriculture applications.


## REFERENCES

[1]  N. Andriyanov, A. Tashlinsky, and V. Dementiev, “Zero-Shot Detection in  Satellite Images,” in 2025 Systems of Signal Synchronization, Generating  and Processing in Telecommunications (SYNCHROINFO), Moscow, Russia,  2025, doi: 10.1109/SYNCHROINFO65403.2025.11079342.  [2] A. I. Kutyrev and N. A. Andriyanov, “Navigation of Robotic Platforms

in Commercial Horticulture: A Comparative Analysis of Transformers  for Semantic Segmentation,” Horticulture and Viticulture, no. 4, pp. 51– 59, 2025, doi: 10.31676/0235-2591-2025-4-51-59.  [3] O. Didmanidze, M. Karelina, V. Filatov, D. Rybakov, N. Andriyanov, S.

Korchagin, Y. Kafiyatullina, and D. Serdechnyy, “Development of a  Computer Vision System for an Optical Sorting Robot,” in Smart  Innovation, Systems and Technologies, Cham, Switzerland: Springer,  2024, doi: 10.1007/978-3-031-71360-6_16.  [4] A. Krizhevsky, I. Sutskever, and G. E. Hinton, “ImageNet Classification

with Deep Convolutional Neural Networks,” in Advances in Neural  Information Processing Systems 25 (NeurIPS 2012), Lake Tahoe, NV,  USA, 2012, pp. 1097–1105.  [5] A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N.

Gomez, Ł. Kaiser, and I. Polosukhin, “Attention Is All You Need,” in  Proc. 31st International Conference on Neural Information Processing  Systems (NeurIPS), Long Beach, CA, USA, 2017, pp. 6000–6010.  [6] T. B. Shahi, S. Dahal, C. Sitaula, A. Neupane, and W. Guo, “Deep

Learning-Based Weed Detection Using UAV Images: A Comparative  Study,” Drones, vol. 7, no. 10, Art. no. 624, 2023, doi:  10.3390/drones7100624.  [7] M. Krestenitis, E. K. Raptis, A. Ch. Kapoutsis, K. Ioannidis, E. B.

VI. CONCLUSIONS

This paper presented an approach for accelerating UAV- based agricultural video analytics through the combination of  YOLOv11 instance segmentation, INT8 quantization, and  Rockchip NPU deployment. The proposed framework was  designed for crop and weed segmentation in aerial imagery and  implemented on an Orange Pi 5+ platform based on the  RK3588 system-on-chip.

Kosmatopoulos, S. Vrochidis, and I. Kompatsiaris, “CoFly-WeedDB: A  UAV Image Dataset for Weed Detection and Species Identification,”  Data in Brief, vol. 45, Art. no. 108575, Dec. 2022, doi:  10.1016/j.dib.2022.108575.  [8] E. Celikkan, T. Kunzmann, Y. Yeskaliyev, S. Itzerott, N. Klein, and M.

Herold, “WeedsGalore: A Multispectral and Multitemporal UAV-Based  Dataset for Crop and Weed Segmentation in Agricultural Maize Fields,”  in Proc. IEEE/CVF Winter Conference on Applications of Computer  Vision (WACV), Tucson, AZ, USA, 2025, pp. 4767–4777.  [9] H. Wang, X. Wang, M. Ibrahim, D. Severtson, and A. Mian, “BAWSeg:

A combined dataset consisting of real UAV images and  synthetic samples was used to train and evaluate YOLOv11n- seg and YOLOv11s-seg models. The trained networks were  converted to the RKNN format using post-training INT8  quantization and deployed on the embedded neural processing  unit. Experimental results demonstrated that quantization  reduced segmentation accuracy by approximately 2–3  percentage points while providing a 2.6–2.7× reduction in  inference latency. The best accuracy was achieved by the  YOLOv11s-seg model, whereas YOLOv11n-seg provided the  lowest computational cost and the fastest execution speed.

A UAV Multispectral Benchmark for Barley Weed Segmentation,”  Remote Sensing, vol. 18, no. 6, Art. no. 915, 2026, doi:  10.3390/rs18060915.  [10] G. Peng, K. Wang, J. Ma, B. Cui, and D. Wang, “AGRI-YOLO: A

Lightweight Model for Corn Weed Detection with Enhanced  YOLOv11n,” Agriculture, vol. 15, no. 18, Art. no. 1971, 2025, doi:  10.3390/agriculture15181971.  [11] Ultralytics, “YOLO11 Documentation,” Ultralytics Documentation,

2024. [Online]. Available: https://docs.ultralytics.com/models/yolo11/.  [Accessed: Jun. 2026].  [12] Ultralytics,  “Instance  Segmentation  with  YOLO,”  Ultralytics  Documentation,  2024.  [Online].  Available:  https://docs.ultralytics.com/tasks/segment/. [Accessed: Jun. 2026].  [13]  L. Wei, Z. Ma, C. Yang, and Q. Yao, “Advances in Neural Network

The obtained results confirm that Rockchip-based edge AI  platforms can efficiently execute modern segmentation  networks while maintaining accuracy levels suitable for  practical precision agriculture applications. The proposed  solution enables real-time onboard processing of UAV imagery  without relying on cloud computing resources, making it  attractive for autonomous monitoring and site-specific crop  management systems.

Quantization: A Comprehensive Review,” Applied Sciences, vol. 14, no.  17, Art. no. 7445, 2024, doi: 10.3390/app14177445.  [14] H. Joshi, “Edge-AI for Agriculture: Lightweight Vision Models for

Disease Detection in Resource-Constrained Environments,” arXiv  preprint arXiv:2412.18635, 2024.  [15] Rockchip Electronics Co., Ltd., RK3588 Technical Reference Manual,

Version 1.0, Fuzhou, China, 2024.  [16] Rockchip Electronics Co., Ltd., RKNN Toolkit2 User Guide, Version

Future work will focus on expanding the dataset with additional  multispectral UAV imagery, investigating quantization-aware  training techniques, and evaluating transformer-based segmentation  architectures on embedded hardware platforms.

2.x, Fuzhou, China, 2024.  [17] Ultralytics, “Rockchip RKNN Export for Ultralytics YOLO Models,”

Ultralytics  Documentation,  2024.  [Online].  Available:  https://docs.ultralytics.com/integrations/rockchip-rknn/. [Accessed: Jun.  2026].

ACKNOWLEDGMENT

This research was supported by the Russian Science  Foundation (RSF) under Project No. 26-11-00336.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:41:14 UTC from IEEE Xplore.  Restrictions apply.
