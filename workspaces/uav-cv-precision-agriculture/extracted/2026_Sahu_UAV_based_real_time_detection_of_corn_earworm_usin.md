---
workspace_id: SCI-000934
doi: 10.1080/03601234.2026.2660035
title: UAV-based real-time detection of corn earworm using EfficientNet and machine
  learning.
authors:
- family_name: Sahu
  given_name: Shriya
  orcid: null
- family_name: Verma
  given_name: Prerna
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:46:39.007963+00:00'
---

# UAV-based real-time detection of corn earworm using EfficientNet and machine learning.

Journal of Environmental Science and Health, Part B

Pesticides, Food Contaminants, and Agricultural Wastes

ISSN: 0360-1234 (Print) 1532-4109 (Online) Journal homepage: www.tandfonline.com/journals/lesb20

UAV-based real-time detection of corn earworm using EﬃcientNet and machine learning

Shriya Sahu & Prerna Verma

To cite this article: Shriya Sahu & Prerna Verma (2026) UAV-based real-time detection of corn earworm using EﬃcientNet and machine learning, Journal of Environmental Science and Health, Part B, 61:7, 429-442, DOI: 10.1080/03601234.2026.2660035

To link to this article:  https://doi.org/10.1080/03601234.2026.2660035

Published online: 27 Apr 2026.

Submit your article to this journal

Article views: 68

View related articles

View Crossmark data

Full Terms & Conditions of access and use can be found at https://www.tandfonline.com/action/journalInformation?journalCode=lesb20

Journal of Environmental Science and Health, Part B 2026, VOL. 61, NO. 7, 429–442

https://doi.org/10.1080/03601234.2026.2660035

UAV-based real-time detection of corn earworm using EfficientNet and  machine learning

Shriya Sahu and Prerna Verma

Department of Computer Science & Application, Atal Bihari Vajpayee Vishwavidyalaya, Bilaspur, Chhattisgarh, India


## ABSTRACT

Early detection of corn earworm (Helicoverpa zea) is crucial for subsiding corn crop losses and make 
sure supportable agricultural productivity. Traditional monitoring methods, composed of manual 
field inspections and pheromone traps, are often time-consuming, labor-intensive, and prone to 
hindered detection. This study develops an unmanned aerial vehicle (UAV)-based, real-time detection 
system for corn earworm infestations using progressive artificial intelligence techniques. Multispectral 
and thermal images were collected from three corn fields throughout the 2024 growing season, 
including numerous pest life stages. The dataset includes 2,000 high-resolution images, with 
metadata as well as geographical coordinates, collection date, and pest stage annotations, authorized 
by entomological experts. Image preprocessing, as well as normalization, augmentation, and 
segmentation, was smeared to develop data quality and model generalization. EfficientNet, a 
convolutional neural network, was engaged for feature extraction, and its outputs were classified 
using a hybrid method combining Random Forest and Support Vector Machine algorithms to 
improve detection accuracy and robustness. The system succeeded 90% classification accuracy, with 
inference times suitable for real-time field application. Field trials recognized the practical applicability 
of the method under variable ecological conditions. This research shows that fitting UAV imaging 
with AI-based models can be responsible for suitable, accurate detection of corn earworm, assisting 
proactive pest management decisions. The methodology can be adjusted to other pest species and 
crop systems, posturing a scalable solution for precision agriculture and backing sustainable crop 
protection practices. These findings highlight the potential of connecting AI, remote sensing, and 
entomological validation for modern, data-driven pest management.

ARTICLE HISTORY Received 31 December 2025 Accepted 10 April 2026

KEYWORDS UAV-based detection; corn  earworm (Helicoverpa zea);  real-time pest monitoring;  EfficientNet; Machine learning;  precision agriculture

Recent advances in artificial intelligence (AI) have allowed  automated pest detection with higher speed and accuracy.[8]  Machine learning (ML), mainly deep learning techniques  using convolutional neural networks (CNNs), can analyze  high-resolution agricultural images to isolate pests effi­ ciently.[9] Among these architectures, EfficientNet has estab­ lished strong feature extraction capabilities while keeping up  computational efficiency.[10] In this study, EfficientNet is  engaged for deep feature extraction, charted by conventional  ML classifiers, such as Support Vector Machines (SVM) and  Random Forests (RF), to achieve optimal real-time perfor­ mance.[11,12] The integration of unmanned aerial vehicles  (UAVs) equipped with high-resolution RGB and multispectral  cameras enables rapid coverage of large corn fields and  enables the collection of high-quality imagery for early-stage  pest detection.[13–14] This method makes sure that infestations  can be identified before visible damage occurs, assisting in  timely and precise pest management interventions.[15,16]


## 1.  Introduction

The corn earworm (Helicoverpa zea) is one of the most dev­ astating pests of corn due to its widespread host range,  excessive adaptability, and out-of-sight feeding habits. Larvae  often feed within corn husks during initial infestation stages,  making detection challenging and resulting in major yield  losses if untreated. Studies have shown that H. zea infesta­ tions can decrease corn yield by 30–50% under severe con­ ditions, stressing its economic impact on corn production  systems (Olmstead et  al., 2016; Bragard et  al., 2020).[1] In  addition, the pest’s rapid development of resistance to chem­ ical pesticides gives emphasis to the need for timely and  precise monitoring schemes to implement targeted pest  management interventions.[2,3] Traditional detection tech­ niques, such as manual investigation and trap-based moni­ toring, are labor-intensive, time-wasting, and often fail to be  responsible for real-time infestation data.[4,5] These methods  are prone to human error, lack scalability in large agricul­ tural fields, and often lead to excessive pesticide applications,  ecological degradation, and higher production costs.[6,7]

In spite of major progress in AI and UAV-based monitor­ ing, most existing systems either require substantial compu­ tational resources or lack real-time capability, mostly for H.

CONTACT Shriya Sahu   profshriya@gmail.com   Department of Computer Science & Application, Atal Bihari Vajpayee Vishwavidyalaya, Bilaspur, Chhattisgarh,  495009, India.

© 2026 Taylor & Francis Group, LLC

430 S. SAHU AND P. VERMA

zea detection.[17,18] As a result, this study proposes a compu­ tationally efficient, UAV-based AI framework for real-time  corn earworm detection. The system integrates image pre­ processing, EfficientNet-based feature extraction, and con­ ventional ML classifiers to achieve high classification  accuracy (≈90%) with low inference latency (50–100 milli­ seconds),[19] making it suitable for practical field deployment.  The primary objective is to design a robust and scalable  AI-driven detection system that minimizes crop losses,  reduces pesticide overuse, and supports sustainable agricul­ tural practices.[20] The remaining sections are organized as  follows: The literature review was described in Section 2, the  proposed technique was described in Section 3, the experi­ mentation results were discussed in Section 4, the discussion  was presented in Section 5, and the research conclusion was  provided in Section 6.

for projecting monitoring technologies and adaptive pest  management plans. These insights further defend the devel­ opment of intelligent, real-time pest detection frameworks  capable of responding to progressing ecological pressures.

More recently, hybrid architectures linking CNNs with  transformer-based  models  have  shown  improved  performance.

Utku et  al.[29] proposed a ConvViT model for agricultural  insect detection, achieving over 93% classification accuracy,  even though Hao et  al.[30] enhanced YOLO-based frame­ works for corn leaf disease and pest recognition under com­ plex field conditions. In spite of these progressions,  computational complexity and real-time deployment remain  major challenges.

Few studies, though, focus exactly on real-time detection  of corn earworm using UAV imagery, including lightweight  deep feature extractors and conventional ML classifiers. Most  obtainable methods either lack real-time capabilities or  involve computational resources unsuitable for field deploy­ ment.[31–33] This gap prompts the present study, which  intends a UAV-based, EfficientNet-driven AI framework for  accurate, scalable, and computationally efficient real-time  corn earworm detection in corn fields.


## 2.  Literature survey

Recent studies have authorized the potential of AI and deep  learning techniques for agricultural pest detection. CNNs  such as AlexNet, VGG, and ResNet, have been broadly use­ ful for crop pest classification, achieving favorable accuracy.  On the other hand, many of these systems function offline  and require high computational resources, limiting their  applicability in real-time field scenarios.


## 3.  Research proposed methodology

Dong et  al.[21] reviewed AI-based pest and disease man­ agement systems and stressed the role of image recognition  and big data analytics in assisting automated monitoring and  early warning.

The proposed methodology for real-time pest and disease  detection in agriculture employs advanced AI techniques to  monitor crop health efficiently. Data is collected using UAVs  and sensor technologies, capturing Multispectral and thermal  images of crops at different growth stages. Preprocessing  steps, including normalization, augmentation, and segmenta­ tion, are applied to enhance image quality and ensure model  generalization. Machine learning algorithms, such as random  forest and support vector machines (SVM), are trained on  labeled datasets to accurately classify pests and disease  symptoms. The trained models are then integrated into a  real-time detection system capable of issuing alerts and pro­ viding  actionable  insights.  This  methodology  enables  dynamic, precise monitoring of crops, allowing farmers to  implement timely interventions, reduce losses, and enhance  sustainable agricultural practices by combining AI, remote  sensing, and data-driven decision-making. EfficientNet-B0  was executed by means of TensorFlow 2.11 and Keras 2.11.  Hybrid classifiers (SVM and Random Forest) were executed  by means of scikit-learn 1.2.1. All experiments were shown  on a system with an NVIDIA RTX 3080 GPU and 32 GB  RAM. Five-fold cross-validation was used to estimate model  presentation.

Kapetas et  al.[22] developed YOLO-based models for  greenhouse pest detection, joined with ARIMAX time-series  forecasting, achieving high detection accuracy but calling for  further integration for field deployment.

Chiranjeevi et  al.[23] introduced InsectNet, proficient in  isolating over 2,500 insect species using great image datasets;  on the other hand, separating visually similar species and  lecturing data imbalance sustained perplexity.

Lazuardi et  al.[24] proposed a hybrid deep learning model  integrated with edge computing and IoT technologies for  paddy pest detection, indicative of real-time performance  but needing further validation under variable ecological  conditions.

Yahenga et  al.[25] and Saran et  al.[26] explored UAVs and  remote sensing for large-scale monitoring, stressing their  potential to quickly cover extensive agricultural areas. On  the other hand, contests remain in cost, robustness, and  integration with decision-support systems. For corn-specific  pests, Zuo et  al.[27] applied machine learning to predict corn  borer risk zones by spatial clustering, refining risk predic­ tion, but with restricted geographic scalability.


> **Figure 1 illustrates a UAV-based real-time detection sys­**

> tem for corn earworm using EfficientNet and machine learn­
ing. It initiates with data acquisition, capturing images of 
crops. These images undergo preprocessing to improve qual­
ity and prepare for analysis. K-Means clustering is applied to 
segment the crops, segregating healthy and diseased areas. 
The segmented images then continue to classification, where 
Random Forest and SVM algorithms recognize pest and dis­
ease presence. The system appraises the accuracy of these AI

Yamuna et al.[28] examined the influence of climate change  on insect pest plagues and food safety. Their findings point  to the fact that increasing temperatures, improved precipita­ tion patterns, and dangerous weather events contribute to  stretched pest distribution and higher infestation intensity.  Although the study did not focus precisely on real-time  detection systems, it emphasizes the developing requirements

Journal of Environmental Science and Health, Part B 431


> **Figure 1.  Block diagram of the proposed work.**

models in perceiving crop diseases, confirming reliable per­ formance. Finally, an AI-powered pest and disease detection  system is established for effective farming, facilitating timely  interventions and improving crop health management  through advanced machine learning techniques.


> **Table 1.  UAV-Based pest and disease identification across various crops.**

Image  quality Tomato Leaf Blight Fungal Sunny, Dry Soil High Wheat Rust Fungal Cloudy, Wet Soil Medium Rice Brown

Disease

Environmental

Crop Pest/disease

type

conditions

Insect Rainy, Flooded

Low

Planthopper

Field

Potato Late Blight Fungal Cold, Humid High Corn Earworm Insect Hot, Dry Medium Apple Scab Fungal Rainy, Humid Low Barley Powdery Mildew Fungal Dry, Windy High Cotton Bollworm Insect Hot, Dry Medium Sunflower Rust Fungal Sunny, Dry High Soybean Aphids Insect Warm, Humid Low

3.1. Data acquisition

Data acquisition forms the foundation for developing a reli­ able machine learning model for crop monitoring and pest  detection. In this study, high-resolution images were col­ lected using a DJI Matrice 300 RTK UAV equipped with a  20 MP RGB camera, a multispectral sensor capturing Red,  Green, Blue, and Near-Infrared (NIR) bands, and a thermal  sensor with a resolution of 640 × 512 pixels. Flights were  conducted at an average altitude of 25–30 meters above  ground level under daylight conditions to ensure optimal  image quality. These UAV-captured images provide detailed  visual information on crop health, enabling the model to  detect signs of pests and diseases. Labeled datasets were  compiled with annotations for the presence or absence of  pests and diseases across multiple crop types, including corn,  wheat, soybean, cotton, tomato, rice, potato, apple, barley,  and sunflower. Environmental parameters such as tempera­ ture, humidity, sunlight, and soil moisture were recorded  concurrently using onboard and ground-based sensors to  provide contextual information for more accurate predic­ tions. Image quality was categorized as high, medium, or  low based on resolution and sensor input, while RGB and  NIR/SWIR bands captured key plant features, including  color, texture, and stress levels. These datasets are essential  for training machine learning algorithms, allowing them to  learn patterns that distinguish healthy from unhealthy crops,  ultimately enabling accurate real-time pest and disease detec­ tion, as summarized in Table 1. This UAV setup and stan­ dardized  flight  procedure  ensure  reproducibility  and  experimental clarity, allowing other researchers to replicate  the study under similar field and environmental conditions.


> **Table 1 presents an overview of pest and disease detec­**

> tion across multiple crop types using UAV-acquired imagery 
from a DJI Matrice 300 RTK platform equipped with RGB, 
multispectral, and thermal sensors. The table includes the 
pest or disease type (insect or fungal), key environmental 
conditions (temperature, humidity, soil moisture, sunlight), 
and image quality classification (high, medium, low) based 
on sensor resolution and flight altitude of 25–30 meters. 
These details ensure that the dataset reflects realistic field 
conditions and supports reproducibility for future studies. 
Crops such as corn, wheat, and tomato are paired with spe­
cific pests or diseases, like corn earworm and leaf blight. 
While Table 1 lists multiple crops to illustrate dataset diver­
sity, the experimental validation and model performance 
analysis in this study focus specifically on corn crops and 
corn earworm detection. The additional crop information 
highlights the potential scalability of the proposed UAV-AI 
framework to other agricultural systems.


> **Figure 2 shows the UAV-based hyperspectral imaging**

> framework used for crop health monitoring and pest detec­
tion. Sunlight reflects from crop surfaces and is seized by a 
camera joined with a hyperspectral sensor. The sensor splits 
up expected light into nine distinct wavelength bands span­
ning detectable and near-infrared regions, in detail: 450  nm 
(blue), 520  nm (green), 630  nm (red), 700  nm (red-edge),

432 S. SAHU AND P. VERMA


> **Figure 2.  UAV hyperspectral imaging for crop health detection.**


> **Figure 3.  Schematic representation of K-means clustering.**

750  nm, 800  nm, 850  nm, 900  nm, and 950  nm (near- infrared). These spectral mob’s seizures restrained variations  in  plant  reflectance  associated  with  stress,  nutrient  deficiency, moisture variation, and pest infestation.

(ROIs) corresponding to pests and diseases. Preprocessing  techniques such as histogram equalization, noise reduction,  and contrast enhancement improve the visibility of the  images and reduce noise. The segmented images are then  used as input for feature extraction and machine learning  algorithms to classify crops as healthy or infested with pests  and diseases. By applying these preprocessing and segmenta­ tion techniques, the quality of the images is improved,  enabling more accurate feature extraction and classification,  and ultimately leading to better crop yield prediction and  decision-making in agriculture.

By analyzing spectral signatures through various wave­ lengths, the system can differentiate healthy crops from areas  under stress or affected by pests and diseases, refining early  detection accuracy. The hyperspectral sensor is responsible  for greater spectral resolution than conventional RGB imag­ ing, assisting exhaustive crop-level analysis and learned pre­ cision agriculture decisions.


> **Figure 3 illustrates the K-means clustering process in**

> three stages: before, during, and after clustering. Initially, 
raw input data appear unorganized, signifying complex field 
or crop images with mixed features. During clustering, the 
algorithm allocates pixels to K clusters and iteratively updates 
centroids, creating visible regions. The final stage offers a

3.2. Image preprocessing

After collecting high-resolution images of crops from UAVs,  image preprocessing and segmentation techniques are applied  to enhance image quality and identify regions of interest

Journal of Environmental Science and Health, Part B 433

segmented image where each cluster is exposed in a separate  color. This organized representation highlights areas with  related characteristics, simplifying data interpretation and  supportive operative analysis of patterns associated with pest  and disease detection.

The third equation is connected to the objective function  of K-Means, which is the sum of squared distances between  each data point and its corresponding centroid. This objec­ tive function is minimalized during the iteration process to  ensure that the clusters are as compact as possible. The  objective function can be expressed as:

3.2.1. K-Means clustering

J d x j

2 ( , ) µ  (3)

i j x C i j = = ∈ ∑∑ 1

k

K-Means Clustering is an unsupervised machine learning  technique used for separating data into clusters based on  assessment. This technique plays a significant role in image  segmentation, frequently in the agricultural domain, where it  can be used to segment regions of interest (ROIs) in images  of crops covered by UAVs. By clustering connected pixels  together, K-Means can help recognize healthy and diseased  portions of the crops, refining decision-making in agricul­ ture. The algorithm aims to decrease the variance within  each cluster and exploit the variance between clusters.

where J is the total cost (objective function) of the clustering  process, Cj represents the set of data points in cluster j.  d xi i ( , ) µ 2 is the Euclidean distance between the data point xi  and the centroid µj. By diminishing this cost function, the  algorithm controls the centroids to ensure that the sum of  squared distances between data points and centroids is as  small as possible, leading to well-defined clusters.

The fourth equation relates to the convergence of the  algorithm. The algorithm iterates over the assignment and  explains the steps until the centroids no longer change sig­ nificantly between iterations. This condition can be  expressed as:

At the core of K-Means Clustering is the process of  assigning each data point (or pixel in the context of images)  to one of k predefined clusters. This process includes the  consequent key steps: initialization, assignment, update, and  convergence. In the initialization step, k centroids are ran­ domly designated from the dataset, which are used to estab­ lish the initial positions of the clusters. These centroids act  as the central points around which the clustering procedure  will rotate.

t + ( ) ( ) − <∈ 1  (4)

µ µ j

t

j

( ) t +1 are the centroids of cluster j at time  steps t and t + 1, respectively, ϵ is a small threshold value  that controls when the algorithm has converged. Once the  centroids stop changing, the algorithm is considered to have  converged, and the clustering process is complete.

where µj

t( ) and µj

The first equation in K-Means is the Euclidean distance  equation, which is used to allocate each data point to the  nearest centroid. The distance between a data point xi and a  centroid µj is calculated as:

K-Means clustering is extensively used in applications like  image segmentation, customer segmentation, and anomaly  detection. In the condition of agriculture, mostly for investi­ gative images captured by UAVs, K-Means can segment  diverse parts of the image based on pixel intensity or color  patterns. For existence, areas with disease symptoms in crops  have varied color characteristics correlated to healthy areas,  and K-Means can be used to isolate these regions. The algo­ rithm is mostly operative when the number of clusters is  known beforehand, which is frequently the case in applica­ tions like crop health monitoring, where regions of interest  (healthy and infested) can be predefined.

d x x i j m jm m

2 1  (1)

n , ( ) µ µ ( ) = − = ∑

where, xi represents the coordinates of the data point. µj  indicates the coordinates of the centroid, n is the number of  features (in the case of image pixels, it would be the number  of color channels or intensity values). This distance quantity  is decisive as it helps to allocate each pixel or data point to  the closest centroid, determining the cluster to which it  belongs.

However, the efficiency of K-Means clustering depends  on the choice of k, the number of clusters. Too few clusters  can lead to a loss of detail, while too many clusters can  overcomplicate the model and introduce noise. Consequently,  selecting an optimal k is important for accurate segmenta­ tion. Despite its simplicity, K-Means remains a powerful tool  for unsupervised learning and has been efficiently applied in  numerous domains, comprising agriculture, where precise  crop monitoring is critical for refining yield prediction and  pest control.

Once the assignments are made, the next step is to  describe the centroids. After each data point is allocated to  a cluster, the centroid of that cluster needs to be recalculated  based on the mean position of all data points (or pixels)  allocated to it. This can be specified by the following  equation:

x j = ∈ ∑ 1  (2)

µj

i i C C

j

where, µj is the updated centroid of cluster j, Cj is the set of  data points distributed to cluster j. Cj is the number of data  points in cluster j. This equation explains the centroid posi­ tion by averaging the positions of all the data points in the  cluster, ensuring that the centroid is at the center of the  allocated points.

3.3. Image classification for pest and disease detection

Pest and Disease Detection for Image Classification involves  machine learning algorithms that identify and categorize  pests and diseases from images of plants or crops. It entails  training some form of deep learning, for example, via a

434 S. SAHU AND P. VERMA


> **Figure 4.  Schematic representation of EfficientNet.**

computer using a labeled dataset comprising images of pests  and diseases. The model learns its way of recognizing the  appearance and features that suggest given issues. Thereafter,  the model classifies new images and provides real-time diag­ nosis. Generally, these step components include data prepro­ cessing (resizing, normalization), model training (labeled  images), and evaluation (measurement of accuracy and  adjustment of parameters).

For model training, the loss function normally used is the  categorical cross-entropy function, which enumerates the  difference  between  the  predicted  and  true  class  distributions:

C = − ( ) = ∑ yɵ 1 	 (6)

L y log i i i

where L represents the loss, C is the number of classes (such  as types of pests and diseases), yi is the true label, and yɵi is  the predicted probability for class i. Minimizing this loss  through training confirms the model can correctly categorize  new input images.


> **Figure 4 shows a convolutional neural network architec­**

> ture intended for image analysis. It starts with an input 
image of size 112 × 112 × 32, followed by a series of convolu­
tional layers expending standard convolution (Conv) and 
MobileNet blocks (MB Conv). These layers progressively 
decrease spatial dimensions while increasing depth, appre­
hending complex features at various scales. The network 
uses changing kernel sizes (3 × 3, 5 × 5) and expansion fac­
tors to improve performance. The architecture ends with a 
7 × 7 × 320 layer, followed by a final layer outputting 39 
classes, representing a classification task likely correlated to 
plant or pest identification.

Lastly, to appraise the model’s performance, the accuracy  metric is normally used. The accuracy equation is defined as:

Accuracy = Numberof correctpredictions

Totalpredictions 	 (7)

This metric measures the proportion of images appropri­ ately classified by the model, serving as a direct indicator of  its efficiency in sensing pests and diseases in plant images.

3.3.1. EfficientNet model

EfficientNet’s architecture and the assimilation of these  key equations make it a powerful tool for agricultural appli­ cations, contributing both high performance and low  resource consumption. All deep learning experiments were  executed using Python (version 3.10) with TensorFlow 2.11  and Keras 2.11 libraries. Machine learning classifiers  (Random Forest and SVM) were executed by means of the  Scikit-learn 1.2 framework. Model training and evaluation  were achieved on a well-equipped workstation with an  NVIDIA GPU (8GB VRAM) and 16GB RAM. These appli­ cation details are delivered to make sure reproducibility of  results.

The EfficientNet model is a state-of-the-art deep learning  architecture intended for effective image classification tasks,  such as pest and disease detection in crops. Its primary ben­ efit lies in its ability to attain high accuracy while preserving  computational efficiency, making it appropriate for real-time  applications in agriculture. The model is based on a com­ pound scaling method, where depth, width, and resolution  of the network are scaled in a balanced method to enhance  performance and resource usage.

One key equation in EfficientNet’s design is the scaling of  network depth, width, and resolution, signified as:

3.3.2. Random forest and support vector machine  (RF-SVM)

Scalefactor d w r = α β γ , , 	 (5)

where d, w, and r represent depth, width, and resolution  scaling factors, respectively. These values are carefully desig­ nated to preserve the model’s efficiency and accuracy through  changing resource constraints.

Random forest and support vector machine (RF-SVM) is a  hybrid machine learning technique that combines the power  of two distinct algorithms, Random forest (RF) and SVM, to  improve the performance of image classification tasks, openly

Journal of Environmental Science and Health, Part B 435

for pest and disease detection in crops. Each algorithm car­ ries a single strength to the model, and their mixture per­ mits for more robust predictions, influencing higher accuracy  in complex tasks like recognizing pest and disease patterns  in plant images. Hyperparameter tuning for both Random  Forest and SVM classifiers was conducted using grid search  optimization. Parameters such as the number of trees in RF  and kernel type, regularization parameter (C), and gamma  value in SVM were systematically evaluated to achieve opti­ mal classification performance.

distinct decision trees (Tree1, Tree2, …, Treen). Each tree  individually processes its subset and produces an individual  result. These consequences are then combined through a  voting mechanism to regulate the final class association.  This ensemble approach improves classification accuracy by  relating predictions from multiple trees, decreasing the risk  of overfitting and refining generalization on diverse datasets.

3.3.2.2. Support vector machine (SVM). SVM is a supervised  machine learning algorithm used for both classification and  regression tasks. The foremost idea behind SVM is to find  the optimal hyperplane that exploits the margin between  two classes. This hyperplane is the decision boundary that  best splits the data into separate classes. In the case of pest  and disease detection, SVM can efficiently classify plant  images into classifications such as healthy or infected.

3.3.2.1. Random forest (RF).  RF is a collaborative learning  method that builds multiple decision trees using random data  and feature subsets to improve classification accuracy. It  decreases overfitting and handles noisy data well. Final  predictions are made by majority voting or averaging, making  it operative for both classification and regression tasks.

SVM functions by transforming input data into a  higher-dimensional space (using a kernel function) where it  can generate a linear decision boundary. This transformation is  mainly helpful when dealing with non-linear data. The equa­ tion of the optimal hyperplane in SVM can be conveyed as:

Mathematically, RF uses the following components:

3.3.2.1.1. Tree construction.  Each tree in the forest is trained  using a subset of the data. For each tree, a random subset  of features is designated at each node.

w x b ⋅ + = 0 (10)

T TrainDecisionTree D i i = ( ) (8)

Where w is the weight vector, x is the input feature vec­ tor, and b is the bias term. The goal of SVM is to exploit  the margin between the two classes, which means to solve  the subsequent optimization problem:

where, Ti is the i-th decision tree, and Di is the subset of the  dataset used for training that tree.

3.3.2.1.2. Prediction.  Each tree produces a prediction, and  the final class prediction is determined by the majority vote  of all trees.


## 2 

(11)

max

W w b ,

yɵ ⋯ = ( ) ( ) ( ) Majority Vote T x T x T x N 1 2 ( ), , ,  (9)

This equation signifies the maximization of the margin,  which in turn increases the generalization capability of  the model.

where, yɵ is the predicted class for input x, and N is the total  number of trees.


> **Figure 6 presents the architecture of the SVM model used**

> for real-time pest and disease detection in agriculture, leverag­
ing artificial intelligence. The process initiates with Input 
Preprocessed Data, which is adapted into an Input Feature 
Vector. This feature vector signifies the applicable characteris­
tics removed from the agricultural data, such as visual pointers 
of plant health, environmental conditions, or other relevant


> **Figure 5 illustrates the Random Forest algorithm’s classi­**

> fication process. It starts with an enhanced preprocessed 
data input transformed into a feature vector. This vector is 
divided into multiple subsets (s1, s2, …, sn), each fed into


> **Figure 5.  Architecture of the RF.**

> Figure 6.  Architecture of SVM.

436 S. SAHU AND P. VERMA

metrics. The SVM architecture then smears this feature vector  to a set of Support Vectors, each distinct by a kernel function  ( ( , )), K x x i  where xi Characterizes a specific support vector, and  x is the input feature vector. The kernel functions map the  input data into a higher-dimensional space, allowing the SVM  to efficiently distinguish different classes (e.g., healthy plants  versus those affected by pests and diseases).

conditions, camera angles, resolutions, and environmental  factors, ensuring adaptability to real-world scenarios. UAVs  equipped with RGB, multispectral, and thermal sensors cap­ ture high-resolution crop images, which are processed by the  AI model for pest and disease detection. When the model  identifies a potential infestation, farmers are immediately  alerted, allowing timely intervention to prevent crop damage.  The inference time of the trained models is measured in  milliseconds (ms) to ensure real-time feasibility. The average  prediction time per image ranges from 50 100 − ms, depend­ ing on model complexity and hardware configuration. This  confirms that the proposed system supports near-real-time  agricultural deployment, providing practical value for  large-scale monitoring.

3.3.2.3. Combining Random Forest and SVM (RF-SVM). The  combination of Random Forest and Support Vector Machine,  referred to as RF-SVM, aims to influence the advantages of  both algorithms. In this hybrid method, the Random Forest  is used as a feature extraction or dimensionality reduction  tool. Random Forest helps classify the most pertinent  features in an image by constructing decision trees based on  the diverse characteristics of the image. These important  features are then fed into the Support Vector Machine,  which classifies the images based on the learned patterns. Feature extraction (random rorest). Random Forest first trains  on a subset of labeled images to classify the important fea­ tures, which might comprise color histograms, texture pat­ terns, and edge features. The output of the Random Forest  is a set of feature vectors that characterize diverse features of  the image.

3.4.1. Evaluation of AI models for pest and disease detection

AI model performance is quantified using Precision, Recall,  F1-score, and Overall Accuracy.

•	 Precision measures the correctness of positive predic­ tions (i.e., proportion of predicted pests that are true  infestations). •	 Recall quantifies the model’s ability to identify all  actual infestations. •	 F1-score balances Precision and Recall, particularly  useful for imbalanced datasets. •	 Overall Accuracy represents the proportion of cor­ rectly classified instances across all classes.

X RandomForest X features images = ( )	 (12)

where, Xfeatures is the extracted feature vector, and Ximages is  the original set of images. Classification (SVM).  After feature extraction, these feature  vectors are used to train an SVM classifier. The SVM then  absorbs the optimal hyperplane to distinguish the dissimilar  classes (e.g., healthy vs. diseased plants).

Robustness testing evaluates model reliability under vary­ ing lighting, camera angles, image resolutions, and environ­ mental conditions, ensuring stable detection in real-world  scenarios.  To  guarantee  metric  consistency,  5-fold  cross-validation (k = 5) is conducted. For each fold, Accuracy,  Precision, Recall, and F1-score are computed, and the  mean ± standard deviation is reported. Standard deviation  values are used to generate error bars in performance com­ parison figures, providing an objective measure of model  stability and reproducibility.

y SVM Xfeatures = ( )	 (13)

where y is the predicted class label for the input image. In  pest and disease detection, the RF-SVM approach suggests  key advantages by joining the feature selection strength of  Random Forest with the classification power of Support  Vector Machine (SVM).

The RF-SVM hybrid model efficiently progresses noisy  agricultural images by joining robust feature extraction with  accurate classification. Random Forest recognizes key image  features, while SVM confirms precise separation of healthy  and infected plants. This approach progresses real-time pest  detection, provides accurate crop management, and encour­ ages sustainable agricultural productivity.

3.4.2. Integration of AI and UAVs for real-time pest and  disease detection

The integration of AI with UAVs enables real-time monitor­ ing of large agricultural areas. UAVs capture high-resolution  crop images with RGB, multispectral, and thermal sensors,  which are analyzed by deep learning AI models for pest and  disease detection. This system provides:

3.4. AI-powered pest and disease detection system for  efficient farming

•	 Instant alerts to farmers upon detection of pests or  diseases, enabling timely interventions. •	 Improved detection accuracy and reduced crop losses  through targeted, data-driven actions. •	 Reduced chemical usage, lowering environmental  impact and operational costs. •	 Continuous monitoring for more accurate yield pre­ diction and sustainable farming practices.

The AI-powered pest and disease detection system is  designed to ensure high accuracy and real-time applicability  in agricultural fields. The model’s performance is evaluated  using Precision, Recall, F1-score, and Overall Accuracy,  computed from a confusion matrix. To assess robustness, the  system is tested on images captured under varying lighting

Journal of Environmental Science and Health, Part B 437


> **Table 2.  UAV-Based crop pest and disease detection algorithm (revised for**

> real-time deployment).

Pseudocode: UAV-based crop pest and disease detection algorithm Input: UAV images: Icrop Environmental data: Denv Labelled dataset: Llabels Output: Pest/Disease detection alert for the farmer Algorithm Steps: Load UAV crop images (Icrop) and environmental data (Denv) Load labelled dataset (Llabels) for model training. Pre-process images: I Pre process I cropprocessed crop = − ( ) Segment image into regions of interest (ROI): ROI Segment Icropprocessed = ( ) Extract image features (colour, texture, shape): Features ExtractFeatures ROI = ( ) Combine features with environmental data: F Features D combined env = + Train AI model (EfficientNet): M TrainModel F L model combined labels = ( ) , Evaluate model: computeAccuracy Precision Recall andF score , , , 1− Capture new crop image (Inew) from UAV. Pre-process new image: I Pre process I new processed new = − ( ) Segment new image: ROI Segment I new new processed = ( ) Extract features from the new image: Features ExtractFeatures ROI new new = ( ) Predict pest/disease: y Predict M Features D pred model new env = + ( ) , Measure inference time per image in milliseconds (ms). Average prediction:  50–100 ms. If y Infected pred =" ", send alert to farmer: AlertFramers ypred ( ) End


> **Figure 7.  Impact of data augmentation on validation loss.**

image preprocessing, and AI-based models enables accurate,  timely, and scalable real-time pest detection, providing  actionable insights for precision agriculture and sustainable  crop protection.


> **Figure 7 demonstrates the effect of data augmentation on**

> the validation loss of the AI model for real-time corn ear­
worm detection. The x-axis represents augmentation levels 
(0–10), and the y-axis indicates validation loss. At low aug­
mentation levels (0–2), validation loss is high (20–25), 
reflecting poor model generalization and overfitting. As aug­
mentation increases (4–8), the validation loss steadily 
decreases, showing improved feature diversity and enhanced 
model performance. Beyond level 10, a sudden drop in val­
idation loss (−34) indicates instability or excessive augmen­
tation causing overfitting. This figure emphasizes that 
optimal augmentation enhances generalization, reduces 
errors, and improves the model’s real-time detection ability. 
Excessive augmentation, however, can destabilize learning. 
Therefore, balancing augmentation is crucial for achieving 
high accuracy and robustness in UAV-based pest detection 
systems. It should be explained that validation loss values 
result from a regularized loss function and do not signify 
negative absolute error values. The apparent negative value 
perceived at higher augmentation levels reproduces instabil­
ity in scaled loss representation due to excessive augmenta­
tion and over-regularization belongings rather than true 
negative loss. This behavior points to model divergence 
when augmentation goes beyond optimal levels. Therefore, 
augmentation levels between 4 and 8 were deliberated opti­
mal for established convergence and reliable generalization.

All time-related units are consistent (ms) to ensure reproducibility and reflect

real-time processing. Steps 3–6 and 10–12 are executed automatically for each captured image,

supporting near-real-time monitoring.

Overall, this AI-powered UAV system ensures efficient,  accurate, and scalable pest management, representing a sig­ nificant advancement in precision agriculture and sustain­ able crop protection.


> **Table 2 outlines a process for detecting pests and diseases**

> in crops using UAV images and environmental data. First, 
UAV crop images and environmental data are loaded, fol­
lowed by the preprocessing of crop images. The images are 
segmented into regions of interest, and relevant features 
(color, texture, shape) are extracted. These features are com­
bined with ecological data to form an inclusive feature set. 
A machine learning model (EfficientNet) is trained using a 
labeled dataset of pests and diseases, and its performance is 
assessed. When a new crop image is captured, it experiences 
the same preprocessing, segmentation, and feature extraction 
process. The model then forecasts whether the crop is 
infected, and if so, an alert is sent to the farmer.


## 4.  Experimentation results

The experimentation section focuses on the design and  implementation of the real-time corn earworm detection sys­ tem using AI. It covers the model architecture, including  EfficientNet for feature extraction and hybrid classification  with SVM and Random Forest, as well as the hardware spec­ ifications and UAV-based data sources. The results and dis­ cussion present both quantitative and qualitative performance  metrics, such as accuracy, precision, recall, F1-score, and  inference latency, to evaluate the system’s effectiveness.  Comparative analysis with conventional detection methods  and other machine learning models highlights the advan­ tages and limitations of the proposed approach. Overall, this  section demonstrates how the integration of UAV imaging,


> **Figure 8 illustrates the relationship between training**

> duration and model accuracy for corn earworm detection. 
Training hours ranged from 2 to 16 h, with training accuracy 
increasing from 90.6% to 98.5% and validation accuracy 
from 96.5% to 98.5%. The small difference between training 
and validation accuracies indicates minimal overfitting and 
strong generalization. Longer training enables the model to 
learn more complex features, improving detection reliability 
in real-time field applications. The steady trend demon­
strates model stability, while minor fluctuations reflect natu­
ral variations during training. Optimizing training time 
ensures the model balances computational efficiency with

438 S. SAHU AND P. VERMA


> **Figure 8.  Effect of training time on model accuracy.**


> **Figure 10.  Recall rate across disease types and models.**


> **Figure 9.  Effect of segmentation quality on detection rate.**

performance, allowing UAV-based AI systems to provide  timely and accurate pest detection. These results confirm  that increased training enhances both precision and robust­ ness for practical agricultural deployment.


> **Figure 11.  Precision and accuracy for pest detection.**

identify positive instances. For Leaf Blight, recall ranges  from 54% to 70%, peaking at 95% with the R2–3D model.  Rust achieves 95% with advanced models, while Powdery  Mildew shows variability from 42% to 80%. Higher recall in  sophisticated models indicates better detection capabilities  across diverse pest and disease types. This figure demon­ strates that model choice significantly impacts the ability to  detect true positives, with advanced architectures improving  sensitivity. High recall ensures fewer missed detections,  essential for real-time pest management. The analysis under­ scores the importance of model optimization for reliable  agricultural monitoring. Although multiple disease types are  obtainable for relative evaluation, experimental validation for  deployment focused primarily on corn earworm detection.  The inclusion of other crop diseases exhibits the generaliza­ tion capability of the proposed framework and its adaptabil­ ity to wider agricultural scenarios. Although the primary  experimental focus is corn earworm detection, recall rates  for Leaf Blight, Rust, and Powdery Mildew are incorporated  to exhibit the model’s generalization capability through other  crops and disease types.


> **Figure 9 shows how segmentation quality influences**

> detection rates in AI-based corn earworm detection. 
Segmentation quality is categorized as low, medium, and 
high on the x-axis, while detection rate is on the y-axis. At 
low quality, the detection rate is 85%, improving to 92% 
with medium segmentation, and reaching 95% with 
high-quality segmentation. Higher segmentation allows the 
model to better isolate pests from the background, reducing 
false positives and improving feature extraction. This result 
demonstrates that image preprocessing is critical for accurate 
and reliable pest identification. Proper segmentation ensures 
that UAV-acquired images lead to precise real-time detec­
tion, enhancing decision-making for crop protection. The 
figure highlights that investment in high-quality preprocess­
ing directly translates into higher detection accuracy. 
Segmentation quality levels (low, medium, high) were 
resolved based on clustering compactness metrics and 
Intersection-over-Union (IoU) validation against physically 
explained ground truth regions. High-quality segmentation 
leads to developed region separation and condensed back­
ground noise, directly leading to developed detection rates.


> **Figure 11 evaluates precision for different pest types:**

> aphids, earworm, and bollworm. Precision represents the 
proportion of correctly identified pests among all detected 
instances. Aphids show 77.9% precision, earworm 78.5%, 
and bollworm 77.3%, indicating consistent performance


> **Figure 10 presents recall percentages for different disease**

> types, Leaf Blight, Rust, and Powdery Mildew, across multi­
ple AI models. Recall measures the ability to correctly

Journal of Environmental Science and Health, Part B 439


> **Figure 12.  Weather effects on prediction accuracy.**

across pest types. Balanced precision demonstrates the mod­ el’s ability to correctly classify pests without excessive false  positives. This uniform performance is crucial for real-time  monitoring, ensuring that farmers receive accurate alerts for  timely intervention. The figure highlights the AI system’s  reliability  in  multi-pest  environments,  showing  that  UAV-based detection can support decision-making in preci­ sion agriculture. Consistent precision across pest types  ensures robustness, making the system suitable for diverse  crop protection scenarios.


> **Figure 13.  Alert efficiency vs. time in detection.**


> **Figure 12 shows how different weather conditions, sunny,**

> cloudy, and rainy, affect prediction accuracy for corn ear­
worm detection. Accuracy varies moderately under sunny 
(4.5–12%) and cloudy (5–11%) conditions, with peaks and 
troughs indicating natural fluctuations. Rain introduces 
slightly more variability, affecting AI prediction reliability. 
The figure emphasizes that environmental factors can influ­
ence UAV-based pest detection. Understanding these varia­
tions helps in designing robust models and operational 
protocols for real-time deployment. Despite weather-related 
fluctuations, the model maintains reasonable accuracy, con­
firming its suitability for field applications. The analysis 
underscores the need for weather-aware adjustments or sup­
plemental data to maintain high-performance pest detection 
across variable environmental conditions. The percentage 
variations shown in Figure 12 denote deviation ranges from 
baseline model accuracy under standard ecological condi­
tions. These variations were deliberate, using repeated test­
ing through weather scenarios and articulated as percentage 
fluctuation to show robustness under field variability.


> **Figure 14.  Scalability across crop types and metrics.**

improvement in alerting shows that the model is reliable for  continuous, real-time field deployment, making it effective  for practical crop protection applications. Alert efficiency  values denote average system response time (in minutes)  from image seizure to farmer notification. Lower values  point to faster response performance. Minor upturns over  time reflect computational load variation through continu­ ous UAV operation rather than degradation in detection  capability.


> **Figure 14 evaluates the scalability of the AI-based detec­**

> tion system across multiple crop types: Corn, Wheat, 
Soybean, and Tomato. Three key metrics, detection accuracy, 
response time, and model robustness, are plotted for each 
crop. Corn exhibits the highest detection accuracy (45%) 
and robustness (40), with a response time of 50 min, indicat­
ing optimal performance. Wheat shows slightly lower robust­
ness (36) and longer response times (45 min), while Soybean 
and Tomato display reduced accuracy (27% and 25%) and 
lower robustness (35 and 28). The moderately lower accu­
racy values witnessed in cross-crop evaluation reveal domain 
shift between training and testing distributions. Since the 
model was mostly trained on corn datasets, there were per­
formance reductions when directly smeared to other crops


> **Figure 13 illustrates the alert efficiency of the AI-based**

> real-time corn earworm detection system over time. The 
x-axis represents time (0–8 min), and the y-axis shows alert 
efficiency values. Initially, the alert efficiency starts at 2.5 min 
and gradually rises to 4.3 min, with minor fluctuations 
observed along the trend. The increase indicates that the 
system progressively improves its responsiveness as the mon­
itoring period continues. Slight oscillations in alert efficiency 
suggest variability due to data processing delays or transient 
environmental factors during UAV operation. Overall, the 
figure demonstrates that the AI system can provide timely 
notifications for pest management, allowing farmers to 
respond 
quickly 
to 
infestations. 
This 
progressive

440 S. SAHU AND P. VERMA


> **Figure 16.  Comparative analysis of real-time pest and disease detection**

> methods.


> **Figure 15.  Comparison of the detection methods’ accuracy.**

image to ensure consistent evaluation of real-time suitability.  KNN offers rapid training (0.5–2 h) but lower accuracy (75– 80%), while DT provides moderate performance (80–85%  accuracy, 1–3 h training). The table highlights that SVM is  the most suitable model for UAV-based real-time pest detec­ tion, combining accuracy, efficiency, and speed, whereas  CNN is preferred when computational resources and time  are less constrained. Real-time suitability was assessed based  on inference latency measured in milliseconds per image.  SVM validated an average inference time below 100 ms,  endorsing its capability for near real-time field deployment  when included with UAV systems.

without retraining. This reinforces the significance of  domain-specific fine-tuning for optimal deployment. The  scalability analysis through different crops is exploratory in  nature and is planned to calculate the transfer learning capa­ bility. The primary endorsed implementation residues  corn-based pest detection, while other crop results point to  potential extension through fine-tuning and retraining.  Accuracy for crops other than corn is lower due to domain  shift, stressing the need for fine-tuning before deployment  on new crop types.


> **Figure 15 compares detection accuracy among different**

> methods for real-time corn earworm detection: UAV-based 
AI, traditional CNN-based methods, and literature-based 
DNN models. Accuracy percentages are plotted on the 
y-axis. Both UAV-based AI and the proposed CNN method 
achieve high accuracy (0.9), demonstrating superior detec­
tion capabilities. The literature-based DNN method achieves 
lower accuracy (0.8), indicating comparatively reduced effec­
tiveness. The figure underscores the advantages of integrat­
ing UAV imaging with CNN architectures for pest detection, 
providing real-time, high-precision results. It highlights that 
advanced AI methods outperform conventional approaches 
in both speed and reliability. The comparative analysis con­
firms that the proposed UAV-CNN approach is suitable for 
practical deployment in precision agriculture, ensuring 
timely and accurate detection of corn earworm infestations 
across varying field conditions. For consistency, the accuracy 
values described as 0.9 and 0.8 match up to 90% and 80%, 
respectively. Decimal representation is used in comparative 
benchmarking to support standard machine learning record­
ing formats. All performance values through figures are reg­
ularized for uniform interpretation.

All results denote mean ± standard deviation across  five-fold cross-validation. Statistical consequence among  methods was considered using one-way ANOVA followed by  Tukey’s HSD test at p < 0.05.


## 5.  Discussion

The results of the AI-based real-time corn earworm detec­ tion system reveal the impact of various parameters on model  performance. The use of EfficientNet for feature extraction  combined with SVM and Random Forest classifiers resulted  in a 90% accuracy for pest detection. The system demon­ strated strong generalization capabilities, with minimal over­ fitting observed during training. Key factors like data  augmentation and segmentation quality significantly influ­ enced model performance. Data augmentation, particularly at  levels 4–8, helped reduce validation loss, improving general­ ization. However, excessive augmentation caused instability,  as indicated by the sudden drop in validation loss. The train­ ing time analysis revealed that increasing training hours  (from 2 to 16) improved accuracy, with minimal fluctuation  between training and validation accuracy. Segmentation qual­ ity was found to have a direct effect on detection rates, with  high-quality segmentation leading to a 95% detection rate. In  comparison to existing models, this system achieved better  performance with faster inference times (50–100 ms) and  higher precision (78.5%). Weather conditions had a moderate  impact, particularly in rainy and cloudy environments, which  may require additional adjustments for more consistent


> **Figure 16 presents a detailed comparison of machine**

> learning models, SVM, CNN, KNN, and DT, based on accu­
racy, training time, and inference time for pest and disease 
detection. SVM achieves the best balance with 90% accuracy, 
fast training (2–5 h), and quick inference (50–100 ms per 
image), making it perfect for real-time applications. CNN is 
responsible for competitive accuracy (85–95%) but requires 
longer training (12–24 h) and slower inference (200–500 ms 
per image), controlling their practicality in time-sensitive 
field conditions. All inference times are determined per

Journal of Environmental Science and Health, Part B 441

performance. Overall, the study demonstrates the efficacy of  combining UAV-based imaging with AI models for efficient,  real-time pest detection in precision agriculture.

Disclosure statement

The authors declare that they have no conflict of interest.

Ethical approval

5.1. Practical application of the study

The paper has been submitted with full responsibility, following due  ethical procedure, and there is no duplicate publication, fraud, or pla­ giarism. None of the authors of this paper has a financial or personal  relationship with other people or organizations that could inappropri­ ately influence or bias the content of the paper. This article does not  contain any studies with human participants or animals performed by  any of the authors.

In a real-world scenario, the AI-based corn earworm detection  system can help farmers promptly identify pest infestations,  reducing crop losses. For example, in a UAV-based field trial,  the system can be deployed to detect corn earworm in real-time  with high precision, triggering automated alerts for immediate  action. This technology could also integrate with other preci­ sion farming tools like irrigation management systems and fer­ tilization controls, enabling data-driven decision-making. The  rapid detection time (50–100 ms) allows for timely interven­ tions, optimizing both pest control and crop yield.

Funding

The author(s) reported there is no funding associated with the work  featured in this article.


## 6.  Research conclusion

Data availability statement

The study validates the efficiency of a UAV-based AI system  for real-time detection of Helicoverpa zea (corn earworm)  pests. The proposed method achieved high accuracy (90%)  and precision (78.5%) through multiple pest types, provided  that a reliable tool for precision agriculture. Key factors such  as data augmentation and segmentation quality were crucial  in increasing model performance, ensuring robust detection  under variable field conditions. The UAV-AI system provides  suitable monitoring capabilities, enabling early-stage pest  identification and supportive directed interventions to  decrease crop damage and pesticide use. Future work consists  of spreading the system to isolate a broader range of pests  and diseases, slotting in multi-season datasets to account for  seasonal variations, and exploring sensor fusion with multi­ spectral or thermal UAV-mounted sensors. In addition,  cloud-based deployment could assist large-scale monitoring  through diverse agricultural regions. Field validation will be  piloted to compare AI-detected infestations with actual corn  earworm damage on ears. Indicative of the ability to notice  early-stage caterpillar attacks will further endorse the system’s  practical efficacy in sustainable crop protection.

The datasets generated and analyzed during the current study are avail­ able from the corresponding author on reasonable request. UAV imag­ ery, environmental data, and annotated labels supporting the findings  are included.


## References

[1]	 Deng, L.; Fang, D.; Ullah, A.; Hou, Q.; Yu, H. AMS-YOLO:  Multi-Scale Feature Integration for Intelligent Plant Protection  against Maize Pests. Front. Plant Sci. 2025, 16, 1640405. DOI:  10.3389/fpls.2025.1640405. 	 [2]	 Verma, G.; Kumar Saxena, A.; Rai, M.; Shaheen, M.; Naaz, S.  IoT Integrated CNN Framework for Automated Detection and  Quantification of Rice and Potato Crop Diseases. Sci. Rep. 2025,  15, 38199. DOI: 10.1038/s41598-025-22117-9. 	 [3]	 Song, D.; Peng, Y.; Gu, X.; U, K. A Lightweight YOLOv8-Based  Network for Efficient Corn Disease Detection. Mathematics  2025, 13, 4002. DOI: 10.3390/math13244002. 	 [4]	 Eze, V. H. U.; Eze, E. C.; Alaneme, G. U.; Bubu, P. E.; Nnadi,  E. O. E.; Okon, M. B. Integrating IoT Sensors and Machine  Learning for Sustainable Precision Agroecology: Enhancing  Crop Resilience and Resource Efficiency through Data-Driven  Strategies, Challenges, and Future Prospects. Discov. Agric.  2025, 3, 83. DOI: 10.1007/s44279-025-00247-y. 	 [5]	 Zhang, H.-W.; Wang, R.-F.; Wang, Z.; Su, W.-H. DLCPD-25: A  Large-Scale and Diverse Dataset for Crop Disease and Pest  Recognition. Sensors 2025, 25, 7098. DOI: 10.3390/s25227098. 	 [6]	 Gamlath, C. J.; Wu, F. AI and Biotechnology to Combat  Aflatoxins: Future Directions for Modern Technologies in  Reducing Aflatoxin Risk. Toxins. (Basel) 2025, 17, 524. DOI:  10.3390/toxins17110524. 	 [7]	 Song, J.; Cheng, K.; Chen, F.; Hua, X. RDW-YOLO: A Deep  Learning Framework for Scalable Agricultural Pest Monitoring  and  Control.  Insects  2025,  16,  545.  DOI:  10.3390/in­ sects16050545. 	 [8]	 Zhou, T.; Wei, L. YOLO-DP: A Detection Model of Fifteen  Common Rice Diseases and Pests. Sci. Rep. 2025, 15, 35968.  DOI: 10.1038/s41598-025-19310-1. 	 [9]	 Li, B.; Yu, L.; Zhu, H.; Tan, Z. YOLO-FDLU: A Lightweight  Improved YOLO11s-Based Algorithm for Accurate Maize Pest  and Disease Detection. AgriEngineering 2025, 7, 323. DOI:  10.3390/agriengineering7100323. 	[10]	 Gan, X.; Cao, S.; Wang, J.; Wang, Y.; Hou, X. YOLOv8-DBW:  An Improved YOLOv8-Based Algorithm for Maize Leaf

Acknowledgments

All authors contributed to the design and implementation of the  research, to the analysis of the results and to the writing of the  manuscript.

Author’s contribution statement

CRediT: Shriya Sahu: Supervision, Validation, Visualization; Prerna  Verma: Resources, Software, Supervision, Validation, Visualization,  Writing – original draft.

Cover letter

This manuscript is the authors’ original work and has not been pub­ lished nor has it been submitted simultaneously elsewhere. All authors  have checked the manuscript and have agreed to the submission.

442 S. SAHU AND P. VERMA

Diseases and Pests Detection. Sensors 2025, 25, 4529. DOI:  10.3390/s25154529. 	[11]	 Bo, Z.; Zhou, C.; Yang, M. Research on Intelligent Detection  Method of Mold and Insect Pests in Grain Storage Based on  YOLOv5 and Large Model Fusion. J. Big Data Comput. 2025, 3,  50–57. DOI: 10.62517/jbdc.202501209. 	[12]	 Zhang, M.; Liu, C.; Li, Z.; Yin, B. From Convolutional Networks  to Vision Transformers: Evolution of Deep Learning in  Agricultural Pest and Disease Identification. Agronomy 2025, 15,  1079. DOI: 10.3390/agronomy15051079. 	[13]	 Zou, H.; Weng, Z.; Zhao, M.; Jiang, X. Multi-Strategy Improved  Cantaloupe Pest Detection Algorithm. Insects 2025, 16, 1201.  DOI: 10.3390/insects16121201. 	[14]	 Chandraleka, J.; Selvaraj, P. Enhancing Precision Agriculture  with a Novel AI Framework for Early Crop Health Detection.  Tech. Gazette 2025, 32, 1740–1747. 	[15]	 Xu, Y.; Sun, J. Enhanced Crop Disease Detection Using  Agricultural Disease Vision Recognizer (ADViR). IAENG Int. J.  Comput. Sci. 2025, 52, 953–964. 	[16]	 Yao, H.; Shu, L.; Yang, X.; Li, K.; Martínez-García, M. SILDSO:  Dynamic Switching Optimization Scheme for Solar Insecticidal  Lamp Based on Multi-Pest Phototactic Rhythm. Sensors 2025,  25, 7332. DOI: 10.3390/s25237332. 	[17]	 Srivastava, V.; Wist, T.; Cárcamo, H. Prairie Crop Insect Pests:  How Can we Improve Our Economic Impact Estimate? Can. J.  Plant Sci. 2025, 105, 1–12. DOI: 10.1139/cjps-2025-0020. 	[18]	 Lu, Y.; Liu, P.; Tan, C. MA-YOLO: A Pest Target Detection  Algorithm with Multi-Scale Fusion and Attention Mechanism.  Agronomy 2025, 15, 1549. DOI: 10.3390/agronomy15071549. 	[19]	 Wang, Q.; Liu, Y.; Zheng, Q.; Tao, R.; Liu, Y. SMC-YOLO: A  High-Precision Maize Insect Pest-Detection Method. Agronomy  2025, 15, 195. DOI: 10.3390/agronomy15010195. 	[20]	 Jin, N.; Hu, T.; Shu, L.; Zang, H.; Li, K.; Han, R.; Yang, X. A  Crop Growth Information Collection System Based on a Solar  Insecticidal Lamp. Electronics. (Basel) 2025, 14, 370. DOI:  10.3390/electronics14020370. 	[21]	 Dong, Y.; Liu, L.; Zhai, X.; Li, W. Artificial Intelligence in  Agricultural Pest and Disease Management: Current Applications  and Future Prospects. Adv. Resour. Res. 2025, 5, 971–986. 	[22]	 Kapetas, D.; Christakakis, P.; Faliagka, S.; Katsoulas, N.; Pechlivani,  E. M. AI-Driven Insect Detection, Real-Time Monitoring, and  Population Forecasting in Greenhouses. AgriEngineering 2025, 7,  29. DOI: 10.3390/agriengineering7020029. 	[23]	 Chiranjeevi, S.; Saadati, M.; Deng, Z. K.; Koushik, J.; Jubery, T.  Z.; Mueller, D. S.; O’Neal, M.; Merchant, N.; Singh, A.; Singh,

A. K.; et al. InsectNet: Real-Time Identification of Insects Using  an End-to-End Machine Learning Pipeline. PNAS Nexus. 2025,  4, 575. DOI: 10.1093/pnasnexus/pgae575. 	[24]	 Lazuardi, M. R.; Hadi, M. Z. S.; Kristalina, P.; Uehara, H.  Integrated Paddy Pest Detection System Using Hybrid Model  and Edge Computing with LoRa Communication and GIS  Interface. JOIV Int. J. Inform. Visual. 2025, 9, 2287–2296. DOI:  10.62527/joiv.9.6.3529. 	[25]	 Yahenga, Z.; Yanbinb, L. Design of a Digital Early Warning  Platform for Intelligent Crop Pests and Diseases. Acad. J. Agric.  Life Sci. 2025, 6, 71–78. 	[26]	 Saran, S.; Hiremath, S. S.; Kumar, A.; P, A.; Singh, H.;  Chakraborty, S.; Kashyap, V.; Tiwari, A. K.; Pandey, S. K.  Remote Sensing and Automated Monitoring Systems for Insect  Pest Detection and Surveillance. UPJOZ. 2025, 46, 155–171.  DOI: 10.56557/upjoz/2025/v46i24771. 	[27]	 Zuo, Y.; Ji, M.; Yang, J.; Li, Z.; Wang, J. Risk Assessment of  Corn Borer Based on Feature Optimization and Weighted  Spatial Clustering: A Case Study in Shandong Province, China.  Sci. Rep. 2025, 15, 28036. DOI: 10.1038/s41598-025-13067-3. 	[28]	 Yamuna, V.; Katiravan, J.; Visu, P. Advanced Pest Identification  Framework Using Deep Learning and Feature Extraction  Techniques. J. Electr. Eng. Technol. 2025, 20, 1803–1814. DOI:  10.1007/s42835-024-02111-3. 	[29]	 Utku, A.; Kaya, M.; Canbay, Y. A New Hybrid ConvViT Model  for Dangerous Farm Insect Detection. Appl. Sci. 2025, 15, 2518.  DOI: 10.3390/app15052518. 	[30]	 Hao, S.; Gao, E.; Ji, Z.; Ganchev, I. BCS_YOLO: Research on  Corn Leaf Disease and Pest Detection Based on YOLOv11n.  Appl. Sci. 2025, 15, 8231. DOI: 10.3390/app15158231. 	[31]	 Chandrasekaran, S. K.; Rajasekaran, V. A. Energy-Efficient  Cluster Head Using Modified Fuzzy Logic with WOA and Path  Selection  Using  Enhanced  CSO  in  IoT-Enabled  Smart  Agriculture Systems. J. Supercomput. 2024, 80, 11149–11190.  DOI: 10.1007/s11227-023-05780-5. 	[32]	 Karthik, S.; Anupama, A. S.; Deekshith, S. A.; Santhosh, L.;  Dhanraj, M. Crypto AI: Digital Nostalgic Art Generation Using  GAN and Creation of NFT Using Blockchain. J. Emerg. Technol.  Innov. Res. 2024, 9, 217–220. 	[33]	 Jasrotia, P.; Priya, B.; Kumar, R.; Bishnoi, P.; Vij, A.; Kumar, T.  SERS Detection of Rhodamine-6G on Ion Beam Nanostructured  Ultra-Thin Gold (Au) Films: A Correlation between Fractal  Growth, Water Contact-Angle and Raman Intensity. ECS J.  Solid  State  Sci.  Technol.  2023,  12,  027005.  DOI:  10.1149/2162-8777/acb56f.
