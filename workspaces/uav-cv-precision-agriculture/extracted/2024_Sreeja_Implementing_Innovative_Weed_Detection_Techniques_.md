---
workspace_id: SCI-001046
doi: 10.13074/jent.2024.12.243947
title: Implementing Innovative Weed Detection Techniques for Environmental Sustainability
authors:
- family_name: Sreeja
  given_name: K. A.
  orcid: null
- family_name: Pradeep
  given_name: Arun
  orcid: null
- family_name: Arshey
  given_name: M.
  orcid: null
- family_name: Warrier
  given_name: Gayathry S.
  orcid: null
- family_name: Ragesh
  given_name: K. T.
  orcid: null
year: 2024
extraction_engine: pymupdf
extracted_at: '2026-09-04T01:48:53.951027+00:00'
---

# Implementing Innovative Weed Detection Techniques for Environmental Sustainability

Journal of  Environmental

Research Article Nanotechnology

Implementing Innovative Weed Detection Techniques  for Environmental Sustainability

K. A. Sreeja1*, Arun Pradeep2, M. Arshey3, Gayathry S. Warrier4 and K. T. Ragesh5

1Department of Electronics and Communication Engineering, SCMS School of Engineering and Technology, Karukutty, KL, India  2Department of Electronics and Communication Engineering, Saveetha Engineering College, Chennai, TN, India  3Department of Computer Science and Engineering, Jain University, Infopark, Kochi, KL, India  4Department of Computer Science, Christ University, Bengaluru, KA, India  5Department of Agricultural Engineering, Saveetha Engineering College, Chennai, TN, India  Received: 03.09.2024        Accepted: 29.11.2024        Published: 30.12.2024  * kasreeja67@gmail.com


## ABSTRACT

Agriculture, supporting over half of India's population, grapples with the challenge of weed control.  Current  methods applied in plantation crops lack efficiency and pose environmental and health risks. This paper advocates a paradigm  shift, emphasizing the critical need for effective weed detection using cluttered unmanned aerial vehicle (UAV) images. The  research methodology integrates image processing, Mask R-Convolutional Neural Networks (R-CNN), and Internet of  Things (IoT). A dataset of 200 UAV images was subjected to a thorough preprocessing. In the initial phase, weeds and crops  were identified with precision employing an UAV-tailored Mask R-CNN with instance segmentation. This was found to  surpass traditional methods in terms of communication between the model and the agricultural environment. For timely  decision-making, real-time data were collected using IoT. Average Precision (AP) values reveal high accuracy, notably 89.1%  for weeds, 88.9% for crops, and an overall precision of 89.4%. The Mask R-CNN network segments and classifies images,  marking weed zones communicated to farmers via Raspberry Pi with a GSM module, enabling real-time alerts and informed  decision-making for efficient weed control. This holistic approach, providing object classifications, detailed bounding boxes,  and masks, addresses weed control challenges, highlighting the transformative potential of advanced technologies in  agriculture.

Keywords: Agriculture; Weed control; Mask R-CNN; UAV images; IoT integration; Precision.


## 1. INTRODUCTION

posing potential health hazards. On the other hand, AI- driven robotic solutions, while effective, come with a  higher price tag. Nevertheless, they eliminate the need for  human labour and circumvent health risks associated  with herbicides. In this dynamic landscape, the adoption  of AI in agriculture has become prevalent. The  deployment of AI technologies not only addresses the  challenge of weed infestations but also aligns with the  broader objective of sustainable and eco-friendly farming  practices (Gatys et al. 2015). The ongoing integration of  AI in agriculture signifies a strategic shift towards  precision farming, where targeted and efficient solutions  are  employed  to  optimize  crop  yield  without  compromising  environmental  safety.  The  dual  considerations of economic viability and environmental  sustainability underscore the importance of striking a  balance between traditional and cutting-edge approaches  in agriculture. As the agricultural sector continues to  embrace AI, there is a promising avenue for the  development  of  innovative,  cost-effective,  and  environmentally  conscious  solutions  that  can  revolutionize weed control and contribute to the overall  advancement of agriculture in the modern era (He et al.,  2017).

Innovative techniques offer a sustainable  solution to reduce greenhouse gas emissions while  safeguarding  environmental  and  human  health.  Traditional methods, which rely on chemical herbicides,  often result in the overuse of machinery, leading to higher  carbon emissions from fuel consumption (Leo et al.  2023; Krishnamoorthi et al. 2023; Kannan et al. 2024;  Mohanrajhu et al. 2024). Agriculture, an ancient and  indispensable profession, has evolved over millennia  with the integration of various technologies, including  artificial intelligence (AI), to enhance productivity and  efficiency while mitigating negative environmental  impacts. Currently, farmers are confronted with a major  obstacle:  a  substantial  decrease  in  agricultural  productivity caused by the presence of weeds.

Research indicates that the presence of weed  plants might reduce crop productivity by around 50%  (Abouziena and Haggag, 2016; LeCun et al. 1998),  leading to significant negative impacts on the economy.  The use of herbicides is a cost-effective approach;  however, it carries the risk of contaminating crop plants,

J. Environ. Nanotechnol.,Vol. 13(4), 287-294 (2024)

https://doi.org/10.13074/jent.2024.12.243947

K. A. Sreeja et al. / J. Environ. Nanotechnol., Vol. 13(4), 287-294 (2024)


## 2. SURVEYING THE LANDSCAPE OF RELEVANT

and Dilation Segmentation Algorithm. The system  employs a CCD camera placed at a 45°-inclination and  positioned 4 m above the ground, directly in front of the  tractor and the sequential operations of Erosion and  Dilation to categorise two distinct weed types - broad and  narrow. The Quadratic Polynomial and Region of Interest  (ROI) Techniques were utilised by Ishak et al. (2007) to  develop a weed detecting technique. The authors  investigated a curve detection technique that relies on the  quadratic polynomial method and incorporates the  utilisation of the ROI method. It is frequently employed  to extract features for image tasks like classification.  Burgos et al. (2010) presented a real-time system for  analysing images to distinguish between crops and weeds  in maize fields.

In recent years, a plethora of deep learning  models has been introduced to tackle object recognition  tasks, showcasing their versatility across various  domains. However, the agricultural sector poses unique  challenges, especially in object recognition tasks where  differentiating between weed and crop plants becomes  intricate due to shared characteristics such as colour,  texture, fill, and size (Yu et al. 2019a; Yu, et al. 2019b;  Ferreira et al. 2017). Although numerous public datasets  are available for species identification and disease  prediction at the leaf level (Mallah et al. 2013; Huang et  al. 2020; Chouhan et al. 2020; Mohanty et al. 2016), the  shift to real-time applications necessitates datasets at the  plant level (Olsen et al. 2019). Existing datasets often  concentrate on diseased crop identification, with limited  attention to weeds growing amidst the crops. For  instance, the Deep Weeds dataset, while addressing weed  species native to northern Australia, primarily serves  classification tasks and lacks information about plant  localization. Moreover, the role of lighting conditions in  agricultural tasks is paramount, and many datasets are  confined to a single lighting condition (Lameski et al.  2017). The Carrot-Weed dataset stands out by offering  images under diverse lighting conditions, albeit restricted  to carrot plants. However, the challenge persists in  datasets like Plant Phenotyping and Plant Seedling,  where the background consists of soil or stones rather  than other plants (Minervini et al. 2016; Giselsson et al.  2017; Sudars et al. 2020). Recently advanced object  detection has enabled collaboration between agriculture  and deep learning, resulting in precision agriculture  (Wang et al. 2019; Bakhshipour and Jafari, 2018).  Convolutional Neural Networks (CNNs) can detect  weeds in turf grass, ryegrass, and soybeans, making them  a useful weed management tool. Besides supervised  models, unsupervised models with minimal tagging can  detect weeds. These advancements underscore the  dynamic nature of the field and its potential to  revolutionize weed detection and management strategies  in agriculture (Ghazali et al. 2008). They introduced an  innovative method to improve the accuracy of a  computerised weed control system by employing  machine vision. Their research is centred around creating  a real-time system for removing unwanted plants in oil  palm fields. The system has been developed to utilise  image processing techniques in order to accurately detect  and classify different types of weeds, with a particular  focus on distinguishing between slender and bulky  weeds.  Kargar and Shirzadifar (2013) introduced an  Automated Weed Detection System and Intelligent  Herbicide Sprayer Robot specifically designed for maize  fields. This study focuses on implementing an automated  plantation system that utilises identification technology  to recognise fruits and vegetables in the plantation. It then  applies herbicides specifically to areas afflicted by  weeds.  The approach for Weed Recognition, as  presented by Siddiqi et al. (2009), utilises the Erosion

The survey highlights the growing significance  of deep learning models in addressing complex  challenges within the agricultural sector, particularly in  the context of weed detection. Despite the shared  characteristics between weed and crop plants, recent  advancements,  exemplified  by  various  studies,  demonstrate the potential of leveraging CNNs and  innovative image processing techniques. However,  existing datasets, often focus on diseased crops or lacking  plant-level localization, underscore the need for more  comprehensive and diverse data sources. The surveyed  studies showcase a promising trajectory towards more  accurate, efficient, and sustainable weed detection and  management practices, emphasizing the dynamic nature  of this field and its transformative potential for  agriculture.


## 3. METHODOLOGICAL FRAMEWORK FOR

WEED DETECTION

The research methodology initiates with a  meticulous dataset collection, encompassing 200  unmanned aerial vehicle (UAV) images set against  cluttered backgrounds, where weeds and crops serve as  the focal points for segmentation and detection. To  standardize this dataset, the images, initially sized at  9000 × 6000 pixels, undergo a preprocessing phase  involving resizing to 800 × 600 pixels and normalization,  enhancing overall quality. This foundational dataset  forms the basis for the incorporation of Internet of Things  (IoT) concepts into the research framework. In the first  stage, weeds and crops are identified using a Mask R- Convolutional Neural Network (R-CNN) with instance  segmentation. This advanced method is tailored to  identify and categorise weeds and crops in photos taken  by an UAV.

The integration of IoT principles improves the  approach by facilitating smooth communication between  the Mask R-CNN model and the agricultural setting.  Well-placed sensors and actuators facilitate real-time  data collection, augmenting the system’s responsiveness.  This innovative approach successfully mitigates the

288

K. A. Sreeja et al. / J. Environ. Nanotechnol., Vol. 13(4), 287-294 (2024)

limitations of traditional methods. Diverging from pixel- wise comparisons inherent in traditional methods, the  Mask R-CNN identifies and segments objects by creating  masks that precisely delineate the contours of the target  classes. The integration of IoT contributes to real-time  decision-making,  ensuring  prompt  responses  to  identified weed infestations. The holistic methodology  aims to present a comprehensive perspective on the  combined impact of instance segmentation, mask  creation, and IoT integration, providing a more precise  and efficient solution for detecting and localizing weeds  and crops in UAV images. This advanced technique  emerges as a promising alternative, particularly in  scenarios where traditional methods fall short due to  processing  time  and  accuracy  constraints.  The  culmination of the methodology results in an output that  not only includes object classifications but also  encompasses detailed bounding boxes and masks for  each identified instance. Rigorous validation and testing  on separate datasets evaluate the model’s generalization  capabilities. The research utilises criteria such as mean  Average Precision (mAP), precision, recall, and F1 score  to provide a thorough performance evaluation of the  suggested  method  in  comparison  to  previous  methodologies. This approach represents a refined and  accurate solution, overcoming the limitations associated  with template matching in the detection and localization  of target objects within cluttered UAV images.

their fields, assisting them in making prompt and well- informed decisions for efficient crop management.


### 3.1 Weeds and Crops Detection with Image

Processing and Mask R-CNN


### 3.1.1 Object Detection with Convolutional Neural Networks

Convolutional  Neural  Networks  have  significantly transformed computer vision by excelling in  tasks such as picture classification, segmentation, and  object detection. These networks draw inspiration from  the human visual system, utilize convolutional layers to  extract hierarchical characteristics from input images,  starting from edges and advancing to more intricate  shapes. The typical CNN architecture shown in Fig. 2  includes convolutional, pooling, and fully connected  layers, with deep layers capturing abstract patterns. In  object  detection,  CNNs  generate  feature  maps,  recognizing edges and textures to identify complex  structures. Deep Convolutional Neural Networks  (DCNNs) enhance CNN capabilities with deeper  architectures, learning intricate representations. These  neural networks excel in simultaneous localization and  classification, and their transfer learning ability, utilizing  pre-trained models, is advantageous for limited datasets.  Convolutional Neural Networks are a fundamental tool  in object detection. They automatically learn hierarchical  representations from data, making them highly effective  for identifying and classifying objects. By combining  convolutional operations with deep learning and transfer  learning techniques, CNNs excel in various computer  vision applications, enhancing accuracy and efficiency.

Proposed method shown in Fig.1 represents an  advanced and intricate approach to the detection and  recognition of weeds and crops in UAV images.

Region-Based Convolutional Neural Networks  (RCNNs) are a significant leap in object detection,  tackling the precise identification and localization of  objects within images. The innovative approach involves  using selective search to generate Regions of Interest  (ROIs),  allowing  independent  assessment  by  convolutional networks for each ROI. This method  revolutionizes object detection by classifying distinct  image regions into suggested classes. Selective search, a  pivotal component, iteratively merges adjacent regions  based on cues like color, texture, and intensity. This  process creates a diverse set of ROIs, forming a  comprehensive pool of potential objects of interest within  the image. Each ROI undergoes independent processing  by the convolutional network, extracting features for  precise object recognition. The RCNN architecture,  initially designed for image detection, has paved the way  for subsequent advancements, including Mask R-CNN,  by combining convolutional neural networks with  region-based strategies. In practical implementation, a  Python script employs RCNN for inference. Selective  search determines regions to be classified, and RCNN  evaluates and classifies these regions, yielding detailed  results with detected objects, their classes, and bounding  box coordinates. This integration of selective search and  RCNN provides a robust framework for accurate object  localization and classification

Collect Dada Set

Preprocessing Image  Annotation

(Weeds &

Crops)

Split into  Training and

Train the  Detected Model

Conver to COCO

Format

Test Images

Instance  Segmentation  (Weeds & Crop)

Prediction of

Segmented  Weeds & Crops

Fig. 1: Advanced weeds and crops detection methodology

The Mask R-CNN network conducts the  categorization of every segment in an image, assigning  them into categories of either crops or weeds. Upon  identifying a segment as a weed, the associated area in  the original image is tagged, thus indicating it as a zone  containing weeds. Afterwards, the image with clearly  indicated weed areas is sent to farmers via email using a  Raspberry Pi that has a GSM module. This  communication technique enables farmers to receive  visual notifications regarding the existence of weeds in

289

K. A. Sreeja et al. / J. Environ. Nanotechnol., Vol. 13(4), 287-294 (2024)

Fig. 2: Object detection with convolutional neural networks

Fig. 3: Proposed Mask R-CNN


### 3.1.2 Advancement to Mask R-CNN in Object Detection

segmentation masks for each proposed region. This  implies that, for every identified object, Mask R-CNN  not only discerns the object’s class but also furnishes a  meticulous mask depicting the object’s precise contours.  The operational sequence involves the generation of  region  proposals  utilizing  selective  search,  individualized processing through convolutional layers  for feature extraction, and three parallel pathways for  object classification, bounding box regression, and  segmentation mask generation. The pathway dedicated to  segmentation  masks  employs  supplementary  convolutional and up sampling layers to generate a binary  mask for each proposed region, encapsulating the  instance segmentation of the corresponding object. The  conclusive output encompasses class labels, bounding  box coordinates, and intricate segmentation masks  detailing  the  object’s  contours.  The  instance  segmentation functionality embedded in Mask R-CNN  proves to be particularly advantageous in scenarios  characterized by object overlap or close alignment,

The architectural paradigm of R-CNN shown in  Fig. 3 holds significant prominence in the domain of  computer vision, specifically tailored for object detection  tasks. Initially devised for proposing regions of interest  and subsequent independent classification, R-CNN  encountered drawbacks pertaining to operational speed  and the absence of end-to-end training capabilities. The  evolutionary stride culminating in Mask R-CNN sought  to  overcome  these  limitations,  introducing  a  transformative attribute—instance segmentation. In  contrast to conventional object detection methodologies,  Mask R-CNN achieves pixel-level precision in outlining  object boundaries through the generation of segmentation  masks. Mask R-CNN distinguishes itself by concurrently  executing three fundamental tasks: object detection,  classification,  and  instance  segmentation.  While  preserving the region proposal mechanism inherent in  RCNN, Mask R-CNN extends this by predicting

290

K. A. Sreeja et al. / J. Environ. Nanotechnol., Vol. 13(4), 287-294 (2024)

thereby amplifying precision in localization and  affording a nuanced comprehension of the spatial  distribution of objects within a given image.

lightweight linear bottleneck layer, followed by a depth- wise separable convolution layer, and conclude with a  linear expansion layer. This inverted structure enables the  capture  of  complex  patterns  while  minimizing  computational  costs,  making  it  well-suited  for  deployment in scenarios with resource constraints.  Within each inverted residual block, MobileNetV3  incorporates a linear bottleneck layer, which contributes  to enhanced feature representation by preventing the  network from discarding valuable information. The hard  sigmoid activation function and Parametric Rectified  Linear Unit (PReLU) activation increase the model’s  non-linearity  and  expressive  capability.  The  MobileNetV3 uses Squeeze-and-Excitation (SE) blocks  to tune channel-wise feature responses during training to  improve attention. This lets the network focus on more  informative channels, improving performance. The  MobileNetV3 has two sizes: Large and Small. The  former is powerful and accurate, whereas the latter  balances efficiency and performance for limited  computational resources. The last layers use lightweight  pooling instead of fully connected layers, decreasing  model parameters and computing complexity. This  model is a popular backbone network for computer vision  tasks like image categorization and object recognition,  especially in real-time applications when computational  resources are limited. Its unique design and optimizations  make it a versatile and effective solution for low- computational devices.

The Visual Geometry Group Image Annotator  (VIA) is employed for annotating images in the  development of computer vision algorithms, particularly  object detection. User-friendly interface of VIA  simplifies the process of labelling objects using polygons  or bounding boxes. Following the process of annotation,  images are stored in JSON format, providing flexibility  and adaptability. Subsequently, the dataset is partitioned  to facilitate efficient algorithm training and evaluation.  The suggested approach aims to enhance the accuracy  and precision of object detection in UAV images by  integrating Mask R-CNN with instance segmentation.  This approach prioritizes the efficient segregation of  desired objects by utilizing anchor boxes, a crucial  component in the process of object detection. In order to  ensure compatibility with Mask R-CNN, tagged UAV  images are transformed into the COCO (Common  Objects in Context) format. This format is widely used to  assess  real-time  object  identification  algorithms,  facilitating  smooth  performance  comparisons.  Intersection over Union (IOU) is a crucial statistic used  in object detection to evaluate the degree of overlap  between predicted and real bounding boxes. The IOU  bounding boxes play a crucial role in achieving precise  detection during Mask R-CNN training. The model  predicts categorization, bounding boxes, and masks at the  same time, making the process of detecting objects in  UAV images more efficient and precise.


### 3.2 Role of Internet of Things in Enhanced UAV

Weed Detection

The integration of the IoT within the research  methodology represents a profound advancement in the  realm of weeds and crop detection in UAV images. It  serves as a transformative element by strategically  placing sensors and actuators throughout the agricultural  landscape. These IoT devices function as intelligent  nodes, constantly collecting real-time data on various  facets, including environmental conditions, crop health  parameters, and potential weed infestations. The  significance of this real-time data acquisition cannot be  overstated, as it forms the foundation for an adaptive and  responsive system. In practice, IoT facilitates seamless  communication between the intricate Mask R-CNN  model  and  the  agricultural  ecosystem.  This  interconnectedness ensures that the model is not solely  reliant on static datasets but dynamically adjusts its  responses based on the evolving conditions in the field.


### 3.1.3 Deep Learning Model MobileNetV3 in Mask R-CNN

The deep learning model used to integrate Mask  R-CNN with instance segmentation greatly affects  performance. The proposed study chose MobileNetV3  due to its reputation for handling complicated datasets.  This model is ideal for real-time applications and low- resource environments because of its lightweight design  and quick feature extraction. This design balances model  accuracy and computational efficiency, achieving our  goal of improving object recognition and precision in  UAV  photos  while  taking  into  account  UAV  computational  constraints.  The  incorporation  of  MobileNetV3 is anticipated to contribute to improved  speed and accuracy, addressing the specific challenges  posed by instance segmentation in the context of UAV  image analysis. This model represents a notable  advancement in the realm of lightweight deep learning  architectures, specifically tailored for efficient neural  network inference on mobile and edge devices. Departing  from its predecessors, MobileNetV1 and MobileNetV2,  MobileNetV3 introduces innovative features and  optimizations aimed at achieving a delicate balance  between model accuracy and computational efficiency. A  distinctive characteristic of MobileNetV3 is its utilization  of inverted residual blocks. These blocks start with a

The placement of sensors and actuators at  strategic points contributes to a comprehensive  understanding of the agricultural environment, capturing  nuances that might be missed through static image  analysis alone. The collected IoT data becomes a crucial  component in the decision-making process of the Mask  R-CNN model. By assimilating information on  environmental changes, crop health fluctuations, and

291

K. A. Sreeja et al. / J. Environ. Nanotechnol., Vol. 13(4), 287-294 (2024)

potential weed threats, the model gains a holistic  perspective. This holistic approach empowers the system  to make informed decisions in real-time. For instance,  upon detecting a weed infestation, the system can trigger  immediate responses, such as alert notifications,  automated weeding equipment activation, or other  predefined actions. The synergy between image  processing and IoT in this methodology marks a  paradigm shift in precision agriculture. The adaptability  and responsiveness introduced by IoT not only enhance  the accuracy of weed and crop detection but also pave the  way for intelligent, data-driven agricultural practices.

accuracy and efficiency in target object detection.  Average Precision values are subsequently computed for  weeds, crops, and overall accuracy, revealing notably  high values of 89.1% for weeds, 88.9% for crops, and an  impressive overall precision of 89.4% for the specific  image under consideration.

The Mask R-CNN network is essential for  segmenting images and categorizing each segment as  crop or weed. An area indicated as a weed in the original  image is delineated as a weed zone. A Raspberry Pi with  a GSM module sends farmers an email alert with the  changed image emphasizing weed regions after  categorization. This intricate communication process not  only enables farmers to visually discern the presence of  weeds in their fields but also empowers them with  additional details for informed decision-making. The  real-time alerts facilitate timely interventions, aiding  farmers in implementing effective crop management  strategies based on the identified weed zones. This  comprehensive system enhances the overall efficiency of  weed control and contributes to optimized agricultural  practices.


## 4. RESULTS AND DISCUSSION

An Intel Xeon E5-2643v3 CPU at 3.40 GHz was  used in the experiment because of its computing power  and multicore capabilities needed for complicated deep  learning applications. Our weed detection system had 64  GB of RAM to manage large datasets and deep neural  networks. An NVIDIA Quadro M4000 GPU with 8 GB  of video memory accelerated deep neural network  training. Intel Xeon Toolkit 9.0, cuDNN V7.0, Python  3.5.2, TensorFlow GPU 1.8.0, and Keras were important  frameworks. To optimize convergence and GPU  parallelization, input images were organized into ten  batches and trained with an epoch-wise learning rate of  0.01.

The above work is mentioned to be a proposed  work. Sampling images has been considered only for the  implementation of the validity of the proposed work.


## 5. CONCLUSION

To address limitations in traditional method, the  study proposes the adoption of Mask Region-based CNN  as an advanced approach to target object detection. The  MASK R-CNN model undergoes fine-tuning with  specific parameters, including a learning rate of 0.003,  156 training epochs, and a batch size of 25. This  parameter configuration enables the model to effectively  discern various objects within the images. Quantitative  assessment includes performance metrics such as  accuracy for weeds, accuracy for crops, and mean  average precision, presented in Table 1.

The  research  methodology  seamlessly  integrates advanced technologies, including Image  Processing, Mask R-CNN, and IoT, fostering efficient  communication between the model and the agricultural  environment. The process commences with a meticulous  preprocessing of a substantial dataset comprising 200  UAV images. In the initial phase, a specialized UAV- tailored  Mask  R-CNN,  incorporating  instance  segmentation, outperforms conventional methods by  demonstrating exceptional precision in identifying both  weeds and crops. The integration of IoT facilitates real- time data collection, ensuring timely decision-making for  effective agricultural management. The evaluation of AP  values reveals a remarkable accuracy level, with specific  metrics such as 89.1% for weeds, 88.9% for crops, and a  remarkable overall precision of 89.4%. The Mask R- CNN network not only segments and classifies images  but also delineates weed zones. These identified zones  are then communicated to farmers through a Raspberry  Pi equipped with a GSM module, enabling real-time  alerts and informed decision-making. Looking towards  the future, the research opens avenues for further  enhancement and exploration. A potential future scope  involves the integration of machine learning algorithms  to adaptively optimize the detection model based on  evolving environmental conditions. Additionally, the  incorporation of robotic systems for targeted herbicide  application in weed-identified areas could further  enhance the precision and efficiency of weed control


> **Table 1. Comparison of performance metrics**

Models  Accuracy of

Accuracy

of Crop  mAP (%)

Weed

88.3  86.7  83.5(m12)

87.2  88.1  84.2(m19)

89.6  87.8  87.3(m24)

Mask  R-CNN

89.1  88.7  88.6(m43)

86.5  88.9  88.1(m69)

87.8  86.3  86.9(m95)

These metrics provide insights into the efficacy  of MASK R-CNN model in precisely detecting and  segmenting specified target objects. Results, grounded in  the implementation process, highlight the model’s  capability to surmount limitations associated with  traditional template matching, achieving heightened

292

K. A. Sreeja et al. / J. Environ. Nanotechnol., Vol. 13(4), 287-294 (2024)

measures. This forward-looking approach underscores  the transformative potential of advanced technologies in  agriculture, paving the way for sustainable and  technologically-driven farming practices.

Ghazali, K. H., Mustafa, M. M. and Hussain, A., Machine

vision system for automatic weeding strategy in oil  palm plantation using image filtering technique,  InTechOpen.,  (2008).  https://doi.org/10.5772/8215  Giselsson, T., Dyrmann, M., Jørgensen, R., Jensen, P. and

FUNDING

Midtiby, H., A public image database for benchmark  of  plant  seedling  classification  algorithms,  arXiv:1711.05458  (2017).  https://doi.org/10.48550/arXiv.1711.05458  He, K., Gkioxari, G., Dollár, P. and Girshick, R., Mask

This research received no specific grant from  any funding agency in the public, commercial, or not-for- profit sectors.

CONFLICTS OF INTEREST

R-CNN, 2017 IEEE International Conference on  Computer  Vision,  2961-2969  (2017).  https://doi.org/10.1109/ICCV.2017.322  Huang, M. L. and Chang, Y. H., Dataset of tomato leaves,

The authors declare that there is no conflict of  interest.

Mendeley  Data,  V1,  (2020).  https://doi.org/10.17632/ngdgg79rzb.1   Ishak, A. J., Mokri, S. S., Mustafa, M. M. and Hussain,

COPYRIGHT

This article is an open-access article distributed  under the terms and conditions of the Creative Commons  Attribution  (CC  BY)  license  (http://creativecommons.org/licenses/by/4.0/).

A., Weed detection utilizing quadratic polynomial  and ROI techniques, Proc. 5th Student Conf. Res. and  Dev.,  (2007).  http://dx.doi.org/10.1109/SCORED.2007.4451360  Jayabal, R., Optimization and Impact of Modified

Operating Parameters of a Diesel Engine Emissions  Characteristic Utilizing Waste Fat Biodiesel/Di-Tert- Butyl Peroxide Blend, Process Saf. Environ. Prot.,  186,  694–705  (2024).  https://doi.org/10.1016/j.psep.2024.04.019  Kannan,  R.,  Ramalingam,  S.,  Sampath,  S.,  Nedunchezhiyan, M., Dillikannan, D. and Jayabal,  R., Optimization and Synthesis Process of Biodiesel  Production from Coconut Oil Using Central  Composite Rotatable Design of Response Surface  Methodology, Proc. Inst. Mech. Eng., Part E: J.  Process  Mech.  Eng.,  (2024).  https://doi.org/10.1177/09544089241230251  Kargar, A. H. B. and Shirzadifar, A. M., Automatic weed


## REFERENCES

Abouziena, H. F. and Haggag, W. M., Weed control in

clean agriculture: a review, Planta Daninha, 34(2),  377-392  (2016).                http://dx.doi.org/10.1590/S0100-83582016340200019  Bakhshipour, A. and Jafari, A., Evaluation of support

vector machine and artificial neural networks in weed  detection using shape features, Comput. Electron.  Agric.,  145,  153-160  (2018).  http://dx.doi.org/10.1016/j.compag.2017.12.032  Burgos, A. X. P., Ribeiro, A., Guijarro, M. and Pajares,

detection system and smart herbicide sprayer robot  for corn fields, 2013 First RSI/ISM International  Conference on Robotics and Mechatronics, 468-473  (2013).  https://doi.org/10.1109/ICRoM.2013.6510152  Krishnamoorthi, T., Sudalaimuthu, G.,  Dillikannan, D.

G., Real-time image processing for crop/weed  discrimination in maize fields, Comput. Electron.  Agric.,  75(2),  337-346  (2010).  https://doi.org/10.1016/j.compag.2010.12.011  Chouhan, S. S., Kaul, A., Singh, U. P. and Science, M. I.

and Jayabal, R., Influence of Thermal Barrier Coating  on Performance and Emission Characteristics of a  Compression Ignition Engine Fueled with Delonix  Regia Seed Biodiesel, J. Clean. Prod., 420, 138413  (2023).  https://doi.org/10.1016/j.jclepro.2023.138413  Lameski, P., Zdravevski, E., Trajkovik, V. and Kulakov,

T., A database of leaf images: Practice towards plant  conservation with plant pathology, Mendeley Data,  V4,  (2020).  https://doi.org/10.17632/hb74ynkjcn.4   Ferreira, D, S., Freitas, A. D. M., Da, S. G. G., Pistori, H.

and Folhes, M. T., Weed detection in soybean crops  using ConvNets, Comput. Electron. Agric., 143, 314- 324  (2017).  https://doi.org/10.1016/j.compag.2017.10.027  Gatys, L. A., Ecker, A. S. and Bethge, M., A neural

A., Weed detection dataset with RGB images taken  under variable light conditions, Communications in  Computer and Information Science, 778, 112-119  (2017).      https://doi.org/10.1007/978-3-319-67597-8_11

algorithm of artistic style, arXiv:1508.06576, (2015).  https://doi.org/10.48550/arXiv.1508.06576

293

K. A. Sreeja et al. / J. Environ. Nanotechnol., Vol. 13(4), 287-294 (2024)

LeCun, Y., Bottou, L., Bengio, Y. and Haffner, P.,

Olsen, A., Konovalov, D. A., Philippa, B., Ridd, P.,

Gradient-based  learning  applied  to  document  recognition, Proc. IEEE, 86(11), 2278-2324 (1998).  https://doi.org/10.1109/5.726791  Leo, G. M. L., Chrispin, D. M., Jayabal, R.,

Wood, J. C., Johns, J. and White, R. D., Deep  Weeds: A multiclass weed species image dataset for  deep learning, Sci. Rep., 9(1), 1-12 (2019).  https://doi.org/10.1038/s41598-018-38343-3  Siddiqi, M. H., Ahmad, I. and Sulaiman, S. B., Weed

Murugapoopathi, S., Srinivasan, D. and Mukilarasan  N., Experimental Evaluation and Neural Network  Modelling of Reactivity-Controlled Compression  Ignition Engine Using Cashew Nut Shell Oil  Biodiesel-Alumina Nanoparticle Blend and Gasoline  Injection,  Energy,  282,  128923  (2023).  https://doi.org/10.1016/j.energy.2023.128923  Mallah, C., Cope, J. and Orwell, J., Plant leaf

recognition  based  on  erosion  and  dilation  segmentation  algorithm,  2009  International  Conference on Education Technology and Computer,  (2009).      http://dx.doi.org/10.1109/ICETC.2009.62  Sudars, K., Jasko, J., Namatevs, I., Ozola, L. and

Badaukis, N., Dataset of annotated food crops and  weed images for robotic computer vision control,  Data  Brief,  31,  105833  (2020).  https://doi.org/10.1016/j.dib.2020.105833  Wang, A., Zhang, W. and Wei, X., A review on weed

classification using probabilistic integration of shape,  texture and margin features, Signal Processing,  Pattern Recognition and Applications - 2013, 3842  (2013).      https://dx.doi.org/10.2316/P.2013.798-098  Minervini, M., Fischbach, A., Scharr, H. and Tsaftaris, S.

detection using ground-based machine vision and  image processing techniques, Comput. Electron.  Agric.,  158,  226-240  (2019).  http://dx.doi.org/10.1016/j.compag.2019.02.005  Yu, J., Schumann, A. W., Cao, Z., Sharpe, S. M., and

A., Finely-grained annotated datasets for image- based plant phenotyping, Pattern Recognit. Lett., 81,  80-89  (2016).  https://doi.org/10.1016/j.patrec.2015.10.013  Mohanrajhu, N., Sekar, S, Jayabal, R. and Sureshkumar,

Boyd, N. S., Weed detection in perennial ryegrass  with deep learning convolutional neural network,  Front.  Plant  Sci.,  10,  1422  (2019b).  https://doi.org/10.3389/fpls.2019.01422  Yu, J., Sharpe, S. M., Schumann, A. W. and Boyd, N. S.,

R., Screening Nano Additives for Favorable  NOx/Smoke Emissions Trade-off in a CRDI Diesel  Engine Fueled by Industry Leather Waste Fat  Biodiesel Blend, Process Saf. Environ. Prot., 187,  332–42  (2024).  https://doi.org/10.1016/j.psep.2024.04.115  Mohanty, S. P., Hughes, D. P. and Salathé, M., Using

Deep learning for image-based weed detection in  turfgrass, Eur. J. Agron., 104, 78-84, (2019a).  http://dx.doi.org/10.1016/j.eja.2019.01.004

deep learning for image-based plant disease  detection, Front. Plant Sci., 7, 1-10 (2016).  https://doi.org/10.3389/fpls.2016.01419

294
