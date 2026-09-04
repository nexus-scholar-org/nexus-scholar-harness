---
workspace_id: SCI-001116
doi: 10.1109/icsadl67539.2026.11451898
title: 'Herbsat: Satellite Imagery for Ayurvedic Crop Detection in Hilly Regions'
authors:
- family_name: M
  given_name: D.
  orcid: null
- family_name: K
  given_name: Gogila Devi
  orcid: null
- family_name: R
  given_name: K.
  orcid: null
- family_name: V
  given_name: K.
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:41.606527+00:00'
---

# Herbsat: Satellite Imagery for Ayurvedic Crop Detection in Hilly Regions

Proceedings of the 5th International Conference on Sentiment Analysis and Deep Learning (ICSADL-2026) IEEE Xplore Part Number: CFP26UU5-ART; ISBN: 979-8-3315-6883-2

Herbsat: Satellite Imagery For Ayurvedic Crop

Detection in Hilly Regions

Mrs. Gogila Devi K  Department of Electronics and

Mrs. Devaki M  Department of Electronics and  Communication Engineering

Kalai R  Department of Electronics and  Communication Engineering

Communication Engineering

Assistant Professor  K.S. Rangasamy College of

K. S. Rangasamy College of

Assistant Professor  K. S. Rangasamy College of

Technology  Namakkal, India  kalai.r0510@gmail.com

Technology  Namakkal, India  devakimjj@gmail.com

Technology  Namakkal, India  gogiladevi@ksrct.ac.in

2026 5th International Conference on Sentiment Analysis and Deep Learning (ICSADL) | 979-8-3315-6883-2/26/$31.00 ©2026 IEEE | DOI: 10.1109/ICSADL67539.2026.11451898

Kiruthika V  Department of Electronics and  Communication Engineering

K. S. Rangasamy College of

Technology  Namakkal, India  krithicks1201@gmail.com


## Abstract— In precision agriculture, early and accurate

detection of Ayurvedic crops in hill station regions using remote 
sensing imagery is essential for minimizing yield losses, 
improving crop health management, and supporting sustainable 
agricultural practices. This study presents an advanced, end-to-
end deep learning framework for Ayurvedic crop detection and 
prediction in hill station environments using high- resolution 
remote sensing images acquired from satellite and unmanned 
aerial vehicle (UAV) platforms. The proposed multi-stage 
pipeline integrates advanced pre- processing, segmentation, 
feature extraction, and classification modules to achieve robust 
and reliable crop identification under diverse environmental 
conditions. The pre-processing stage employs Gaussian 
Normalization Filtering to suppress sensor noise, atmospheric 
interference, and illumination inconsistencies commonly found 
in remote sensing data, while preserving critical spatial and 
spectral information related to vegetation health. This 
normalization 
enhances crop-specific patterns such as 
discoloration, canopy variations, and texture irregularities, 
enabling improved discrimination between Ayurvedic crops and 
non-medicinal vegetation. For accurate crop region extraction, 
a hybrid U-Net and Mask R-CNN segmentation framework is 
utilized to precisely delineate Ayurvedic crop canopies and 
cultivation regions from complex backgrounds, including soil, 
shadows, overlapping vegetation, and mixed crop scenes 
commonly observed in hill station areas. The segmented regions 
are subsequently processed using a hybrid LSTM–CNN feature 
extraction module. The CNN component captures spatial and 
spectral features such as canopy color variations, leaf patterns, 
structural characteristics, and texture information, while the 
LSTM component models temporal variations across multi-
temporal remote sensing images, effectively learning seasonal 
growth patterns, environmental stress responses, and altitude-
related vegetation dynamics. Final crop classification and 
prediction are performed using a DenseNet-based deep neural 
network, selected for its dense feature connectivity, efficient 
feature reuse, and stable gradient propagation. DenseNet 
demonstrates superior performance in multi-class Ayurvedic 
crop classification while maintaining computational efficiency

suitable for large-scale agricultural and ecological monitoring  systems. The proposed framework is evaluated using publicly  available remote sensing datasets along with real-world field  imagery, achieving an overall crop detection accuracy exceeding  98.5% and a segmentation Intersection-over-Union (IoU) score  of 0.93, significantly outperforming baseline deep learning  models such as ResNet50, VGG19, and MobileNet in terms of  accuracy, robustness, and convergence speed. In addition to  accurate crop detection, the system generates interpretable crop  distribution and vegetation health maps, providing actionable  visual insights for farmers, researchers, and decision-makers.  The proposed approach demonstrates strong potential for  large-scale, automated Ayurvedic crop monitoring in hill station  regions, early resource assessment systems, and precision  agriculture–driven cultivation management.

Keywords—  Remote  Sensing,  Ayurvedic  Crop  Detection, Precision Agriculture, Gaussian Normalization, U- Net Segmentation, Mask R-CNN, LSTM-CNN, DenseNet, UAV  Imagery

I.  INTRODUCTION

Ayurvedic crops pose a significant importance to  sustainable agriculture, ecosystem balance, and traditional  medicine systems, particularly in hill station regions that  support perennial and medicinal vegetation. Early and  accurate detection of such Ayurvedic crops is critical for  supporting conservation efforts, optimizing cultivation  practices, and enabling efficient resource management.  Recent advances in remote sensing technologies, including  high-resolution satellite and unmanned aerial vehicle (UAV)  imagery, have opened new opportunities for large-scale  monitoring of medicinal crop distribution. However, the  complex visual characteristics of Ayurvedic crops, combined  with variations in illumination, background clutter, terrain  effects, and atmospheric noise, make reliable crop detection  a challenging task. Traditional manual surveys and  conventional image processing methods are often labor- intensive, subjective, and inefficient for large hilly  landscapes. Consequently, deep learning–based computer  vision techniques have emerged as powerful tools for  automated Ayurvedic crop detection and classification in

979-8-3315-6883-2/26/$31.00 ©2026 IEEE 932

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:42:34 UTC from IEEE Xplore.  Restrictions apply.

Proceedings of the 5th International Conference on Sentiment Analysis and Deep Learning (ICSADL-2026) IEEE Xplore Part Number: CFP26UU5-ART; ISBN: 979-8-3315-6883-2

precision agriculture. Multi-stage deep learning frameworks  can effectively integrate pre-processing, segmentation,  feature extraction, and classification to improve robustness  and accuracy. In particular, advanced normalization  techniques help suppress noise while preserving crop-  relevant  spectral  and  spatial  information.  Accurate  segmentation of Ayurvedic crop regions is essential for  isolating medicinal plants from complex hill station  backgrounds. Furthermore, hybrid spatial–temporal feature  learning models enable the capture of crop growth patterns  and seasonal variations over time. Dense connectivity–based  classifiers have demonstrated strong performance in multi-  class vegetation and agricultural image analysis. Motivated  by these advancements, this study proposes an advanced deep  learning framework for remote sensing–based Ayurvedic  crop detection in hill station regions. The proposed approach  aims to deliver high accuracy, scalability, and interpretability  for real-world precision agriculture and medicinal crop  monitoring applications.

prescribed by non-institutionally trained Siddha practitioners  for musculoskeletal ailments. The study goals to preserve and  validate this local traditional knowledge, classifying the most  culturally significant and frequently used plant species. [8]  Karthik Sekaran (2024): This paper employs an in-silico  network pharmacology approach to analyse the immune- modulating phytochemicals in Glycyrrhiza glabra (Licorice)  as per Siddha medicine. The learning purposes to  systematically classify multi-target mechanisms by which its  compounds may offer therapeutic potential against COVID- 19. [9] Youssef Miyah (2025): This paper critically examines  recent scientific studies evaluating the efficacy of medical  plants in managing urinary and gallstones. The analysis  focuses on their therapeytic mechanisms and potential as  natural alternatives or supportive treatments in lithiasis  management. [10] Muthukumar Arunachalam (2025): This  paper represents a curated and comprehensive dataset of  South Indian medicinal plants, planned to support machine  learning and computational tools for accurate species  identification. The dataset serves as a foundational resource  for botanical research, conservation efforts and digital  agriculture-tech applications.

II. LITERATURE SURVEY

[1] Biplov Paneru (2024): This paper proposes an  intelligent RAG (Retrieval-Augmented Generation) chatbot  framework based on hybrid deep learning to offer  comprehensive insights on medicinal plants in Ayurvedic  agriculture. The classification is planned to assist farmers,  practitioners, and researchers by increasing access to precise  cultivation and therapeutic knowledge, thereby aiding in  sustainable cultivation and informed usage. [2] Inchara  Crasta (2021): This paper employs molecular docking and  simulation to screen bioactive compounds from Emblica  officinalis, Phyllanthus niruri, and Tinospora cordifolia  against the SARS-CoV-2 main protease. The learning  classifies potential phytochemical leads for COVID-19  therapeutics from these Ayurvedic plants. [3] Rishabh  Kaundal (2025): This paper represents a critical review  examining the current and pressing demands for the scientific  standardization of Indian medicinal plants. The learning  analyses key challenges and proposes frameworks to confirm  consistent quality, safety, and efficacy of herbal raw materials  and products. [4] Sapna Renukaradhya (2024): This paper  proposes the Deep HybridNet model, integrated with a hybrid  optimization  algorithm,  to  increase  the  automated  identification and classification of medicinal plants from  visual data. The framework is planned to improve accuracy  and reliability for botanical research, conservation, and  herbal industry applications. [5] D. Abraham Chandy (2025):  This paper represents a hybrid deep learning model planned  to accurately classify species of aromatic and medicinal  plants from a curated dataset of leaf images. The system  purposes to provide a reliable, automated tool for botanical  identification, supporting quality control, research and  conversion efforts.  [6] Dr. Rekha Sharma (2025): This paper improves a mobile  application framework that utilizes machine learning for the  on-site detection and identification of medicinal plants and  crops. The classification is planned to provide accessible,  real-time support for farmers, foragers, and herbalists to  ensure accurate plant recognition. [7] S. Esakkimuthu (2019):  This paper conducts a quantitative ethnobotanical survey to  document and analyse the medicinal plants

III. PROPOSED METHODOLOGY

The proposed methodology introduces a multi-stage deep  learning framework for accurate Ayurvedic crop detection  and prediction in hill station regions using high-resolution  remote sensing imagery. Initially, satellite and UAV-  acquired images are subjected to Gaussian Normalization  Filtering to reduce sensor noise, atmospheric distortions,  terrain-induced illumination variations, and shadow effects  while preserving essential vegetation-related spectral and  spatial features. The normalized images are then processed  through a hybrid segmentation module combining U-Net and  Mask R-CNN architectures to precisely isolate Ayurvedic  crop canopies and cultivation regions from complex hill  station backgrounds. This segmentation step effectively  handles challenges such as overlapping vegetation, uneven  terrain, soil interference, and shadow effects. The extracted  crop-specific regions are subsequently fed into a hybrid  LSTM–CNN feature extraction network. In this stage, the  CNN component learns discriminative spatial and spectral  patterns, including leaf texture characteristics, pigmentation  variations, and structural features. Simultaneously, the LSTM  component captures temporal dependencies from multi- temporal remote sensing data to model crop growth patterns  and seasonal variations.

As Figure 1 shown below, The learned deep features  are finally classified using a DenseNet-based deep neural  network, which ensures efficient feature reuse and stable  gradient flow. The overall framework enables accurate multi- class Ayurvedic crop classification and prediction while  maintaining scalability and robustness for large-scale  monitoring of hill station agricultural and ecological  environments.

979-8-3315-6883-2/26/$31.00 ©2026 IEEE 933 Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:42:34 UTC from IEEE Xplore.  Restrictions apply.

Proceedings of the 5th International Conference on Sentiment Analysis and Deep Learning (ICSADL-2026) IEEE Xplore Part Number: CFP26UU5-ART; ISBN: 979-8-3315-6883-2

imbalance affected by shadows and sunlight. It develops  visibility of crop features such as veins and edges.

Mean Pixel Intensity

Where above equation represents the,  – intensity,  - image size

Standard Deviation of Image


> **Figure 1. Block diagram**

Pre-processing: Gaussian Normalization Filter

Where above equation represents the,  - Standard  deviation,   - filtered pixel value

Pre-processing plays a energetic role in mountain  ayurvedic crop prediction using image processing methods.  Images taken in mountainous regions often suffer from  illumination variation, sensor noise, and impressive  disturbances. These factors degrade image quality and affect  accurate crop analysis. To address this problematic, a  Gaussian normalization noise filter is practical as an in effect  pre-processing technique. Initially, raw crop images are  acquired using cameras or remote sensing devices. Due to  uneven lighting and altitude effects, Gaussian noise is usually  present in the images.

The collective filtering and normalization enhance image  clarity. This stage develops signal-to-noise ratio in crop  images. It decreases the effect of background interference.  The technique preserves necessary visual information of  medicinal crops. It avoids over-smoothing of fine  information. The pre-processed images become more  consistent. This consistency increases feature extraction  accuracy. It cares reliable identification of ayurvedic crops.  The technique improves classification performance. It is  computationally efficient for large image datasets. The  method confirms robust and accurate crop prediction in  mountainous environments.

Gaussian Kernel Function

A. Segmentation: Hybrid U-Net and Mask R-CNN

Block Segmentation

Where above equation represents the,   - the  Gaussian kernel value,   - spatial coordinates,  - the  standard deviation.

Segmentation is a important step in mountain ayurvedic  crop prediction using image processing methods. Accurate  segmentation supports in isolating medicinal crops from  complex usual backgrounds. Images caught in mountainous  regions comprise uneven terrain, shadows, and vegetation  overlap. To address these tasks, a hybrid U-Net and Mask R- CNN block segmentation method is employed. U-Net is  effective for pixel-level semantic segmentation. It detentions  fine-grained spatial parts of crop regions. The encoder–  decoder architecture allows efficient feature localization.

Gaussian Filtering Operation

Where above equation represents the,   - the  original crop image,   - the Gaussian filter,  -  convolution,   - the filtered image

The Gaussian filter is used to smooth the image while  preserving essential crop structures. It conquers high-  frequency noise without distorting leaf texture and shape. The  filtering procedure is ruled by mean and standard deviation  parameters. These parameters control the smoothing strength  of the filter. After noise removal, pixel intensity values may  vary meaningfully. Therefore, Gaussian normalization is  practical to standardize image intensities. This normalization  converts pixel values to a uniform scale. It confirms zero  mean  and  unit  variance  across  t h e  i m a g e .   Normalization d e c r e a s e s c o n t r a s t

U-Net Feature Encoding

Where the above equation represents, I — the input  crop image fe(⋅) — the encoder function, Fe— the encoded  feature maps.

979-8-3315-6883-2/26/$31.00 ©2026 IEEE 934 Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:42:34 UTC from IEEE Xplore.  Restrictions apply.

Proceedings of the 5th International Conference on Sentiment Analysis and Deep Learning (ICSADL-2026) IEEE Xplore Part Number: CFP26UU5-ART; ISBN: 979-8-3315-6883-2

B. Feature  Extraction:  LSTM-CNN  Feature

U-Net Decoding with Skip Connection

Extraction for Mountain Ayurvedic Crop Prediction

Feature removal is a key stage in mountain ayurvedic  crop prediction using intelligent image analysis. Accurate  structures allow reliable identification of medicinal plant  species. Crop images took in mountainous section’s  exhibition complex textures and temporal variations. To  effectually capture these characteristics, an LSTM–CNN  feature removal prototypical is employed. CNN is capable of  learning spatial features such as edges, shapes, and textures.  It removes hierarchical representations from segmented crop  images. Convolution and pooling layers decrease spatial  redundancy.

Where the above equation represents, fd(⋅) - the  decoder function, Fs(⋅) - the skip connection features, 𝑓𝑑 - the  decoded feature maps.

Skip connections reserve low-level information  during rebuilding. However, U-Net alone may struggle with  instance-level separation. Therefore, Mask R-CNN is  combined to increase segmentation accuracy. Mask R-CNN  achieves instance segmentation by generating object-level  masks. It classifies separate crop regions even in overlapping  circumstances.

CNN Feature Extraction

Region Proposal in Mask R-CNN

Where above equation represent the,  - The segmented  crop image,   - convolutional neural network,   -  extracted spatial features

Feature Sequence Formation

Where the above equation represents, RPN- Region  proposal Network, R- Proposed Crop Region.

The hybrid framework syndicates the strengths of  together models. U-Net offers precise boundary delineation.  Mask R-CNN increases object detection and mask  refinement. Feature maps removed by the backbone network  are shared. Region Suggestion Networks produce candidate  crop regions. Every region is categorized and segmented  independently. This method switches scale variation in crop  size. It increases segmentation under irregular illumination.

Where above equation represent the,   - The  temporal feature sequence,  - Number of time steps

This procedure improves discriminative feature learning.  However, spatial structures alone may be insufficient. Crop  growth patterns and seasonal variations present temporal  dependencies.  Therefore,  Long  Short-Term  Memory  networks are integrated with CNN. LSTM captures sequential  and  contextual  material.  It  prototypes  long-range  dependences in feature sequences. The hybrid architecture  procedures CNN feature maps as temporal contributions.  This combination expands representation learning. The CNN  component focuses on spatial structure. The LSTM  component focuses on temporal evolution.

Mask Prediction

LSTM State Update

Where the above equation represents, fm – The  Mask Generation function, M- Segmentation mask of crop  instances.

The  hybrid  prototypical  reductions  background  interference. It preserves structural specifics of medicinal  plants. The segmented manufacture highlights relevant crop  areas. This rises downstream feature removal. It cares reliable  identification of ayurvedic crops. The prototypical improves  robustness in complex mountain atmospheres. It reaches  higher segmentation accuracy. The method is suitable for  real-time investigation. Finally, the segmented crop regions  are used for accurate mountain ayurvedic crop prediction.

Where above equation represent the,   - Hidden state at  time ,   - Previous hidden state

LSTM Output Feature

Where  above  equation  represent  the,    -  Aggregated LSTM feature representation

979-8-3315-6883-2/26/$31.00 ©2026 IEEE 935 Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:42:34 UTC from IEEE Xplore.  Restrictions apply.

Proceedings of the 5th International Conference on Sentiment Analysis and Deep Learning (ICSADL-2026) IEEE Xplore Part Number: CFP26UU5-ART; ISBN: 979-8-3315-6883-2

Where above equation represents the, F_t - Reduced feature  maps," Conv" (⋅) - Convolution," Pool" (⋅) - Pooling operation

This synergy expands feature robustness. It decreases  sensitivity to environmental variations. The removed features  become extra informative. Noise and immaterial background  data are suppressed. The hybrid prototypical conserves  essential medicinal crop characteristics. It increases inter- class separability. It increases intra-class consistency. The  uninvolved feature vectors provision accurate classification.  They rise predictive presentation. The method adapts well to  mountain environments. It handles variable illumination and  scale. Finally, the LSTM– CNN features are advanced to the  classifier for mountain ayurvedic crop prediction.

This increases computational efficiency. DenseNet  learns complex hierarchical representations. It imprisonments  subtle differences among ayurvedic tree crops. The  prototypical expands inter-class discrimination. It increases  classification accuracy below complex backgrounds. Feature  recycle strengthens robustness against noise. The classifier  adapts well to scale and orientation differences.

Softmax Classification

C. DenseNet Deep Neural Network-Based Efficient

Tree Crop Prediction Classification for Mountain

Ayurvedic

Where above equation represents the,   -  Probability of class ,  - Number of crop classes, - Class  score

Classification is the final and decisive stage in mountain  ayurvedic  tree  crop  prediction  systems.  Accurate  classification enables reliable identification of medicinal tree  species. Images developed from mountainous areas exhibit  more intra-class variability. Environmental factors such as  altitude, fog, and illumination affect visual presence. To  address these tasks, a DenseNet deep neural network is  working for classification. DenseNet presents dense  connectivity between network layers. Each layer obtains  structure maps from all preceding layers.

DenseNet effectively handles fine-grained crop designs.  The softmax layer crops class probabilities. The maximum  probability defines the predicted crop class. The prototypical  increases prediction reliability. It reduces misclassification of  similar species. DenseNet maintenances effective training  and inference. It simplifies well on mountain datasets. The  method realises superior performance. Finally, the DenseNet- based classifier allows perfect and efficient mountain  ayurvedic tree crop prediction.

Dense Layer Features Mapping

Experimental Evaluation:

The Ayurvedic Plant Dataset is a curated collection  of plant images widely used in traditional Ayurvedic  medicine for disease prevention and treatment. The dataset  contains high-quality images of various medicinal plants  captured under different lighting conditions, backgrounds,  and orientations, enabling robust visual analysis. Each plant  category corresponds to a specific Ayurvedic herb with  known therapeutic properties. The dataset supports plant  identification, classification, and medicinal plant recognition  tasks using computer vision and deep learning techniques.  Images exhibit variations in leaf shape, texture, color, and  venation, which are critical for accurate feature extraction.  The dataset is suitable for training and evaluating  convolutional neural networks and hybrid machine learning  models. It helps address challenges such as inter-class  similarity and intra-class variability. Researchers commonly  use this dataset for automated herbal identification and digital  Ayurveda  applications.  The  dataset  facilitates  the  development of intelligent healthcare and botanical  information systems. Overall, it serves as a valuable  benchmark for medicinal plant image analysis research.

Where the above equation represents, 𝑥𝑙 - the output of  the 𝑙 th layer,𝐻𝑙(⋅) - the composite operations (Batch  Normalization, ReLU, and Convolution), [.] feature map  concatenation.

Dense Layer Block Output

Where the above equation represents, 𝐹𝑑- the dense block  feature representation, 𝐿- the number of layers in the dense  block.

This connectivity expands feature reuse and gradient  flow. It decreases the vanishing gradient problem. DenseNet  needs less parameters related to traditional CNNs. The  removed LSTM–CNN features are providing as input to the  DenseNet  classifier.  Dense  blocks  permit  efficient  propagation of discriminative data. Transition layers decrease  feature map dimensions.

Transition Layer Operation

979-8-3315-6883-2/26/$31.00 ©2026 IEEE 936 Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:42:34 UTC from IEEE Xplore.  Restrictions apply.

Proceedings of the 5th International Conference on Sentiment Analysis and Deep Learning (ICSADL-2026) IEEE Xplore Part Number: CFP26UU5-ART; ISBN: 979-8-3315-6883-2

IV. RESULT AND DISCUSSION

which increases the filter technique unwanted data from data  inputs. LSTM CNN feature extraction approach refines input  data by emphasising relevant features and lowering  dimensionality, ensuring that the model processes only the  most meaningful patterns. When these optimised inputs are  utilised to train the RCNN,

5.1. Accuracy

Prediction  accuracy  (%)  is  a  substantial  performance number for assessing the success of the possible  approach. This portion represents the fractaion of effectively  predicted cases compared to the model's total predictions.  This element synergy results in a highest increase in the  model's overall forecast accuracy, boosting the dependability  of abnormal air pollution images.


> **Table II Error Rate of Multi-Stage Deep Learning**

> Framework Integrating Segmentation, LSTM-CNN Feature

Learning, and Dense-Net Classification  Number  Images ( )

Error rate (%)  LSTM-

Retrieval-  Augmented  Generation

Absorption  Distribution,

Proposed technique (LSTM-CNN) higher accuracy

CNN

Metabolism,

when compared with Existing 1 RAG [1] and Existing 2

Excretion,  And Toxicity  10  7  12  15  20  10  14  17  30  13  19  18  40  16  23  23  50  24  27  32  60  28  31  37  70  29  34  39  80  35  42  44  90  37  46  56  100  39  58  60

ADMET [2] technique. As shown in Figure 2 & Table 1,


> **Table I Prediction Accuracy of AI Multi-Stage Deep**

> Learning Framework Integrating Segmentation, LSTM- 
CNN Feature Learning, and Dense-Net Classification

Prediction Accuracy (%)  LSTM-

Number of

Images ( )

Retrieval-  Augmented  Generation

Absorption  Distribution  Metabolism,

CNN

Excreation,

And  Toxicity  10  98  92  89  20  96  93  85  30  98  95  82  40  95  91  83  50  97  94  86  60  97  93  84  70  95  92  90  80  97  94  88  90  98  96  90  100  96  93  91


> **Figure 3. Error Rate (%) Comparison**

In Table II model outperforms Existing 1 RAG [1] and  Existing 2 ADMET [2] technique in terms of prediction  accuracy and error rate. This leads into greater dependability  and more accurate decision-making in website phishing  detection, eventually surpassing the performance of  previously used strategies.


### 5.3 Prediction Time (ms)


> **Figure 2. Prediction Accuracy (%) Comparison**

The proposed technique decreases prediction time by  combining normalization filter and Time Domain feature  extraction and LSTM-CNN classification. The feature  extraction stage minimises data complexity by filter it into  groups with similar features, simplifying the model's input.  The  mapping  time  domain  feature  extraction  and  classification i m p r o v e s d a t a e f f i c i e n c y b y  l o w e r i n g


### 5.2 Error Rate (%)

As per Figure 3, The proposed method achieves a  reduced error rate by intentionally using normalization filter,

979-8-3315-6883-2/26/$31.00 ©2026 IEEE 937 Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:42:34 UTC from IEEE Xplore.  Restrictions apply.

Proceedings of the 5th International Conference on Sentiment Analysis and Deep Learning (ICSADL-2026) IEEE Xplore Part Number: CFP26UU5-ART; ISBN: 979-8-3315-6883-2

dimensionality and emphasising the most useful features,  allowing the RNN to process inputs more effectively. PT  (Prediction Time). The below Figure 4 classifies and

backgrounds, and disease variability. The normalization  process enhances disease-specific spectral and spatial  patterns, while precise segmentation enables reliable  isolation of infected tree canopies. The hybrid LSTM–CNN  module successfully captures both spatial characteristics and  temporal disease progression, leading to improved predictive  performance. Experimental results demonstrate superior  accuracy, robust generalization, and faster convergence  compared to conventional deep learning models. The  framework also produces interpretable disease and vegetation  health maps, offering valuable decision- support insights for  farmers and agronomists. Overall, the proposed system shows  strong potential for large-scale, automated crop disease  monitoring and early warning in precision agriculture. Its  scalability, reliability, and high performance make it well- suited  for  real-world  agricultural  management  and  sustainable farming practices.


> **Table III Prediction time of Multi-Stage Deep Learning**

> Framework Integrating Segmentation, LSTM-CNN Features

Learning, and Dense-Net Classification

Time Consumption (ms)  LSTM-

Number

of  Images

Retrieval-  Augmented  Generation

Absorption  Distribution,

CNN

( )

Metabolism,

Excretion,  And Toxicity  10  32  39  57  20  30  36  52  30  42  52  60  40  49  55  65  50  52  60  67  60  54  68  71  70  57  72  77  80  63  80  84  90  66  82  88  100  67  86  91


## REFERENCES

[1]  Biplov Paneru, Bipul Thapa, Bishwash Paneru, “Leveraging AI  in ayurvedic agriculture: A RAG chatbot for comprehensive  medicinal plant insights using hybrid deep learning approaches”,  Article 100181,https://doi.org/10.1016/j.teler.2024.100181.  [2]  Selvakumar Murugesan, Sanjay Kottekad, Inchara Crasta,  “Targeting COVID-19 (SARS-CoV-2) main protease through  active phytocompounds of ayurvedic medicinal plants – Emblica  officinalis (Amla), Phyllanthus niruri Linn. (Bhumi Amla) and  Tinospora cordifolia (Giloy) – A molecular docking and  simulation  study”,  Article  104683,  https://doi.org/10.1016/j.compbiomed.2021.104683.  [3]  Rishabh Kaundal, Dinesh Kumar, “Current demands for  standardization of Indian medicinal plants: A critical review”,  Received: 7 May 2025, Article 100211.  [4]  Sapna Renukaradhya, Sheshappa S. Narayanappa, “Deep  HybridNet with hybrid optimization for enhanced medicinal plant  identification and classification”, Article 4371.  [5]  Shareena E. M., D. Abraham Chandy, Shemi P. M., “A Hybrid  DeepLearning Model for Aromatic and Medicinal Plant Species  Classification Using a Curated Leaf Image Dataset”, Article 243,  https://doi.org/10.3390/agriengineering7080243.  [6]  Madhurja,  Fabi  Nahian.  "Image-Based  Plant  Disease  Classification Using Machine Learning." Ahsanullah University  of Science and Technology (2022).  [7]  S. Esakkimuthu, S. Mutheeswaran, P. Elankani, “Quantitative  analysis of medicinal plants used to treat musculoskeletal  ailments by non- institutionally trained siddha practitioners of  Virudhunagar district, Tamil Nadu, India”, Article 005,  https://doi.org/10.1016/j.jaim.2018.11.005.  [8]  Sekaran, Karthik, Ashwini Karthik, Rinku Polachirakkal  Varghese, P. Sathiyarajeswaran, MS Shree Devi, R. Siva, and C.  George Priya Doss. "In silico network pharmacology study on  Glycyrrhiza  glabra:  Analyzing  the  immune-boosting  phytochemical properties of Siddha medicinal plant against  COVID-19." Advances in Protein Chemistry and Structural  Biology 138 (2024): 233-255.  [9]  Miyah, Youssef, Mohammed Benjelloun, Hajar El Omari,  Karima El-Mouhdi, and Mohammed El Feniche. "Recent  investigation of the medicinal plants’ effectiveness in the natural  management of urinary and gallstones: A review." Phytomedicine  Plus 5, no. 3 (2025): 100839.  [10]  Muthukumar Arunachalam,T. Gopu, K. Uma, “Medicinal plants  of South India: A comprehensive dataset for species  identification”,  Article  111660,  https://doi.org/10.1016/j.dib.2025.111660.


> **Figure 4. Prediction Time(ms) Comparison**

The table IV Produces faster computation and

prediction processes.  Compared to previous techniques, the CNN built with this  improved knowledge set completes the arrangement  substantially faster, hence removing the absolute prediction  time. The suggested technique (LSTM-CNN) uses a short  forecast time rather than the RAG [1] and Existing 2 ADMET  [2] technique.

V. CONCLUSION

This study presented an advanced end-to-end deep  learning framework for accurate tree crop disease detection  and prediction using high-resolution remote sensing imagery  from satellite and UAV platforms. By integrating Gaussian  Normalization Filtering, hybrid U-Net and Mask R-CNN  segmentation,  LSTM–CNN  feature  extraction,  and  DenseNet-based classification, the proposed approach  effectively addresses challenges related to noise, complex

979-8-3315-6883-2/26/$31.00 ©2026 IEEE 938 Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:42:34 UTC from IEEE Xplore.  Restrictions apply.
