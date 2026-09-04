---
workspace_id: SCI-000754
doi: 10.3390/agriengineering7100353
title: Integrating Convolutional, Transformer, and Graph Neural Networks for Precision
  Agriculture and Food Security
authors:
- family_name: Mahareek
  given_name: Esraa A.
  orcid: https://orcid.org/0000-0002-9042-248X
- family_name: "\xC7if\xE7i"
  given_name: Mehmet Akif
  orcid: https://orcid.org/0000-0002-6439-8826
- family_name: Desuky
  given_name: Abeer S.
  orcid: https://orcid.org/0000-0003-1661-9134
year: 2025
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:35:03.054445+00:00'
---

# Integrating Convolutional, Transformer, and Graph Neural Networks for Precision Agriculture and Food Security

Article Integrating Convolutional, Transformer, and Graph Neural Networks for Precision Agriculture and Food Security

Esraa A. Mahareek 1, Mehmet Akif Cifci 2,3,* and Abeer S. Desuky 1,4

1 Faculty of Science, Al-Azhar University, Cairo 11754, Egypt; esraa.mahareek@azhar.edu.com (E.A.M.); abeerdesuky@azhar.edu.eg (A.S.D.) 2 Engineering and Informatics Department, Klaip˙edos Valstybin˙e Kolegija, Higher Education Institution, 92294 Klaip˙eda, Lithuania 3 Department of Computer Engineering, Faculty of Engineering and Natural Sciences, Bandırma Onyedi Eylül University, Bandırma 10250, Turkey 4 Higher Institute of Computer Science and Information Systems, Cairo 11835, Egypt * Correspondence: meh.cifci@kvk.lt


## Abstract

Ensuring global food security requires accurate and robust solutions for crop health moni- toring, weed detection, and large-scale land-cover classification. To this end, we propose AgroVisionNet, a hybrid deep learning framework that integrates Convolutional Neural Networks (CNNs) for local feature extraction, Vision Transformers (ViTs) for capturing long-range global dependencies, and Graph Neural Networks (GNNs) for modeling spa- tial relationships between image regions. The framework was evaluated on five diverse benchmark datasets—PlantVillage (leaf-level disease detection), Agriculture-Vision (field- scale anomaly segmentation), BigEarthNet (satellite-based land-cover classification), UAV Crop and Weed (weed segmentation), and EuroSAT (multi-class land-cover recognition). Across these datasets, AgroVisionNet consistently outperformed strong baselines includ- ing ResNet-50, EfficientNet-B0, ViT, and Mask R-CNN. For example, it achieved 97.8% accuracy and 95.6% IoU on PlantVillage, 94.5% accuracy on Agriculture-Vision, 92.3% accuracy on BigEarthNet, 91.5% accuracy on UAV Crop and Weed, and 96.4% accuracy on EuroSAT. These results demonstrate the framework’s robustness across tasks ranging from fine-grained disease detection to large-scale anomaly mapping. The proposed hybrid ap- proach addresses persistent challenges in agricultural imaging, including class imbalance, image quality variability, and the need for multi-scale feature integration. By combining complementary architectural strengths, AgroVisionNet establishes a new benchmark for deep learning applications in precision agriculture.

Academic Editors: Ray E. Sheriff and

Chiew Foong Kwong

Received: 8 September 2025

Revised: 9 October 2025

Accepted: 14 October 2025

Published: 19 October 2025

Citation: Mahareek, E.A.; Cifci,

M.A.; Desuky, A.S. Integrating

Keywords: crop health monitoring; agricultural image analysis; smart agriculture; plant disease detection; food security; AgroVisionNet

Convolutional, Transformer, and

Graph Neural Networks for Precision

Agriculture and Food Security.

AgriEngineering 2025, 7, 353.

https://doi.org/10.3390/


## 1. Introduction

agriengineering7100353

Food security can be described in simple words as the overarching global concern for food availability, access, and affordability, or it is a condition in which every member of society has adequate food supplies for consumption at affordable prices or has the means to acquire food from elsewhere in a part of the country where food is scarce. United Nations projections put the global population above 10 billion in the middle of this century, and the population will therefore require a 70% increase in agricultural productivity to meet rising food demands [1,2]. Such an increase becomes an even bigger challenge with the many

Copyright: © 2025 by the authors.

Licensee MDPI, Basel, Switzerland.

This article is an open access article

distributed under the terms and

conditions of the Creative Commons

Attribution (CC BY) license

(https://creativecommons.org/

licenses/by/4.0/).

AgriEngineering 2025, 7, 353 https://doi.org/10.3390/agriengineering7100353

AgriEngineering 2025, 7, 353 2 of 30

setbacks facing contemporary agriculture, ranging from climate change and water shortage to soil fertility loss, prevailing biotic and abiotic stresses such as pests and diseases, and even extreme weather [3,4]. These worsen crop-yield issues, but in developing countries where agriculture is the mainstay of most farmers, they increase disparities in wealth.

Typical methods of monitoring crop health, such as manual inspections and laboratory analyses, are labor-intensive, time-consuming, and often not scalable. Moreover, these techniques provide neither timely nor accurate insights into crop conditions, making them insufficient in addressing quick and large-scale agricultural challenges [5]. For instance, estimates from various studies globally show that pest- and disease-induced losses result in a production loss of approximately 20–40% annually, which culminates in heavy economic losses [6].

The workflow of agricultural data collection and analysis, as outlined in Figure 1, entails the integration of AI into various agricultural processing activities. Starting from data sources such as satellite imagery, UAVs, and IoT sensors, their raw data goes through a crucial preprocessing stage of enhancing quality and usability through cleaning and aug- mentation. The processed data is subject to analysis using AI techniques like deep learning and machine learning, providing precise and actionable insights. Among the resulting outputs are disease maps, yield prediction, and soil quality analysis. It is worth examining the [7] applications of AI in this sector of agriculture concerning disease detection, soil analysis, and yield forecasting, as it will further emphasize the ability and influence of AI-driven solutions in modern farming.


> **Figure 1. Workflow for agricultural data collection and analysis.**

Recent advancements in artificial intelligence and machine learning have led to new crop techniques that can scale, improve, and monitor farm health with accuracy and provide solutions. With such technologies combining remote sensing and imaging from UAVs, precision agriculture is now possible. This enables a proper balance of resource use and output with less environmental impact [8]. These technologies have mostly included deep learning models such as CNNs, which have been widely used as a detection and classification method. Moreover, such models have been used in yield estimation as they have a great capability for learning and extracting complex patterns from multidimensional image data. Inherently, CNNs are local feature extractors, and they need to be coupled with additional emerging architectures and approaches to capture spatial–temporal information and relationships among features in massively distributed agricultural fields [9]. In such cases, Vision Transformers (ViTs) have attracted attention as another approach, using self- attention methods to capture the long-range dependency in images. Most recently, ViTs have positioned themselves as being state-of-the-art methods for applications in which long-range global pattern identification is required, such as crop stress detection on a large scale, or field anomaly mapping [8]. Graph Neural Networks (GNNs) improve upon this by allowing the determination of across-space relationships and interdependencies across distinct areas within an image, allowing a richer analysis of phenomena at the field scale [10].

AgriEngineering 2025, 7, 353 3 of 30

Several modern techniques have been developed for agricultural monitoring. For example, various CNN-based models, ResNet and EfficientNet, among others, have been utilized for leaf-level disease classification, with excellent accuracy in standard datasets like PlantVillage [11,12]. Transformer-based models, such as Vision Transformers (ViTs), have significantly improved the analysis of aerial and satellite imagery, providing insights at large scales in agriculture [13]. Additionally, hybrid methods have demonstrated promise in applications such as weed detection and anomaly classification in fields, by combining UAV imaging with deep learning [9,14]. Graph-based modeling using GNNs has also been used to deal with several crops, capturing their interdependencies to enhance the robustness of predictions by capturing spatial relationships [13].

In recent years, hybrid deep learning architectures have begun to emerge in agricul- tural image analysis. For example, Zeng et al. (2025) introduced a CNN–Transformer model that integrates convolutional feature extraction with self-attention mechanisms, improving the robustness of plant disease detection under challenging conditions [15]. Likewise, graph-based techniques have been explored: a 2025 study proposed a dual-branch con- volutional Graph Attention Network for rice leaf disease classification, which achieved over 98% accuracy by combining CNN-extracted features with Graph Neural Network reasoning [16]. These approaches demonstrate the potential of using multiple network types to address the variability and complexity of agricultural data.

Parallel developments in remote sensing further underscore the value of hybrid models. A graph-infused Vision Transformer architecture was recently designed for hyper- spectral image classification, combining transformer-based global feature learning with GNN-based spatial context modeling [17]. In another study, Vision Transformer features from aerial imagery were fed into a GNN to segment agricultural fields, effectively leverag- ing self-attention for feature extraction and graph learning for spatial segmentation [18]. These examples illustrate how attention mechanisms and graph modeling can complement CNNs in capturing both long-range dependencies and spatial relationships in imagery.

However, most existing methods still fail to incorporate local and global contextual information sufficiently. Additionally, many of these models are non-interpretable, rendering them untrustworthy and unactionable for farmers and stakeholders. Improvements in the above-mentioned aspects are essential for developing precision agriculture solutions further.

AI techniques have achieved remarkable advancements for agricultural monitoring; however, there are still many areas yet to be explored. One of the key challenges is in addressing heterogeneous datasets, which may be variable in terms of resolution, modali- ties (e.g., RGB, hyperspectral, multispectral), and scale (leaf-level vs. field-level imagery). Also, the overwhelming computational complexity associated with deep learning models, particularly ViTs and GNNs, may not allow their deployment in places with resource constraints [13]. Another serious challenge is the lack of explanation in AI models’ work- ings, which limits their application, as end-users require insight into interpretation before making a decision.

This paper addresses the presented challenges through AgroVisionNet—an innovative hybrid deep learning framework that combines the significant features of CNNs, ViTs, and GNNs. The approach provides a type of multi-resolution fusion to integrate locally extracted features with CNNs, and global context with ViTs and GNNs, which are spatially related models. The contributions of this work are as follows:

1. Hybrid Architecture: Integration of CNNs, ViTs, and GNNs for comprehensive analy- sis of agricultural images at multiple scales. 2. Explainability: Incorporating explainable AI techniques to obtain interpretable in- sights related to actionable recommendations for farmers and stakeholders.

AgriEngineering 2025, 7, 353 4 of 30

3. Scalability: Evaluation across varied datasets such as PlantVillage and Agriculture- Vision will demonstrate the adaptability of the proposed model across different agricultural scenarios. 4. Performance: Enhancing state-of-the-art accuracy, robustness, and efficiency in crop disease detection and field anomaly identification by leveraging a model of significance.

To the best of our knowledge, no existing framework in precision agriculture simul- taneously integrates CNNs, ViTs, and GNNs; thus, AgroVisionNet offers one of the first triple-hybrid architectures combining local, global, and relational modeling in this domain.

Recent studies demonstrate partial progress toward hybrid deep learning in agricul- ture and remote sensing but stop short of integrating all three components. For instance, Zeng et al. (2025) introduced CMTNet, a CNN–Transformer hybrid that leverages con- volutional feature extraction with attention mechanisms to improve hyperspectral crop classification, yet it does not incorporate graph-based reasoning [19]. Similarly, a 2025 work proposed EHCTNet, a CNN–Vision Transformer model tailored for remote sensing change detection, demonstrating strong performance in capturing long-range dependencies but, again, lacking a relational learning component [20]. On the other hand, an interpretable CNN–GNN model was presented for soybean disease detection, which successfully inte- grates local features and spatial graph reasoning but does not exploit transformer-based global context modeling [21]. These examples illustrate that while CNN + ViT and CNN + GNN hybrids have begun to emerge, a unified CNN–ViT–GNN framework has not yet

been realized in agricultural applications, underscoring the novelty of AgroVisionNet.

Benchmark datasets, such as PlantVillage and Agriculture-Vision, are used to evaluate AgroVisionNet in various agricultural scenarios. The results have clearly shown that it outperforms other contemporary methods. By exploring the significant aspects of these gaps within agricultural monitoring systems, AgroVisionNet will contribute to the broader picture of food security and sustainability in the global context. This, combined with its radically different dimensionality, hybrid architecture, comprehensive features, and real-world adaptability, makes AgroVisionNet considerably stand out from other proposals. All existing models so far are based on a singular model, such as the use of a Convolu- tional Neural Network (CNN) in extracting local features or a Vision Transformer (ViT) to model global context. However, AgroVisionNet combines all these features into a single framework: CNNs, ViTs, and Graph Neural Networks (GNNs). With this combination, the unique advantages drawn from each technique give AgroVisionNet a strong capability to simultaneously extract fine-grained local features, capture long-range dependencies, and model spatial relationships. Such a hybrid approach will achieve the best performance under a wide range of agricultural contexts—from detecting diseases at the leaf level to analyzing anomalies at the field scale.

AgroVisionNet is not like old photography methods, which work at a single resolution and are used for fixing photographs. With AgroVisionNet, everything related to fine and coarse abstract features is incorporated simultaneously, making it very easy to detect minor, almost imperceptible anomalies, such as early disease detection, and large-scale stresses like water stress. It also addresses the concern of explainability using SHAP-based heatmaps and attention visualizations, which are interpreted through model predictions and are highly beneficial, useful, and actionable for farmers and other stakeholders. Interpretability focuses on and bridges the gap where AI can be adopted for improving trust and usability outside the lab.

One of the significant advantages of AgroVisionNet is that it also generalizes across datasets. While many previous models perform reasonably well in specific datasets, they struggle to adapt to different agricultural conditions or heterogeneous data sources. Unlike many models, AgroVisionNet accepts multi-modal inputs, including RGB, hyperspectral,

AgriEngineering 2025, 7, 353 5 of 30

and NIR imagery, with robust performance across various datasets, such as PlantVillage and Agriculture-Vision, demonstrating its adaptability in diverse agricultural environments. It is inherently prepared for any crop cycle or regional climatic conditions. Adaptability is another key strength of AgroVisionNet. Unlike most state-of-the-art models, such as CNNs and ViTs, which have computational issues with limited availability in resource-constrained environments like smallholder farms, AgroVisionNet can optimize GNNs, making spatial reasoning efficient. This approach cuts computational overhead while maintaining the highest prediction accuracy. It further enables large-scale agricultural monitoring by UAVs or satellites.

AgroVisionNet addresses some of the limitations encountered by previous systems, including dataset bias, environmental variability, and interpretability issues. The combina- tion of multi-resolution fusion, explainable AI, and hybrid frameworks has mitigated these limitations and provided a robust solution. Furthermore, the evaluation based on multiple performance metrics demonstrates AgroVisionNet’s superiority over other methods in terms of accuracy, robustness, and inference efficiency. Overall, AgroVisionNet represents a significant advancement in precision agriculture, closing substantial gaps and establishing new benchmarks for AI applications in agriculture.

Furthermore, deploying a complex model like AgroVisionNet in real-world farming environments requires careful attention to computational efficiency and robustness. The proposed hybrid design is conceived with these practical considerations in mind, aiming to balance state-of-the-art accuracy with feasible inference speed and stability under varying field conditions (e.g., changing illumination, weather, and sensor noise). This focus on deployment readiness and resilience is crucial for translating AgroVisionNet’s performance into effective on-farm applications.

The rest of this paper is organized as follows. Section 2 reviews the recent literature on deep learning techniques for crop health monitoring, including CNNs, ViTs, and GNNs, as well as the limitations of these approaches. Section 3 describes the proposed hybrid framework AgroVisionNet, with an overview of its architecture, processing pipeline, and mathematical model. In Section 4, benchmark datasets are introduced, along with their rel- evant characteristics and linkage to agricultural tasks. The experimental setup, evaluation metrics, and comparison protocols are presented in Section 5. Results across five datasets, including multiple performance indicators, are presented and analyzed in Section 6. Fi- nally, Section 7 concludes the paper by summarizing the key findings, highlighting the contributions, and outlining future research directions.


## 2. Literature Review

The adoption of AI and ML in agriculture is redefining crop health and disease monitoring. This foremost reliance on deep learning algorithms has been manifested in architectures like CNNs, ViTs, and GNNs. CNNs have assumed a central position due to their strong feature extraction capabilities from images, which have led to their use in leaf-level disease detection. For example, Mohanty et al. [22] demonstrated that when trained on the PlantVillage dataset, CNNs could classify 26 plant diseases treated in 14 crop species, achieving over 99% accuracy by means of RGB imaging. Thus, they demonstrated the robustness of CNNs in controlled environments; however, the authors also discussed the limitations that exist in the real world due to bias in datasets and lack of variability in environmental conditions, that hinder generalization to field conditions. In a parallel study, El Sakk et al. [5] reviewed the application of CNNs in smart agriculture systems, agreeing that they provide great successes in disease and pest detection from high-resolution images, but are limited in terms of modeling global spatial relationships in extensive fields.

AgriEngineering 2025, 7, 353 6 of 30

As a remedial measure for such limitations, ViTs have appeared as a supplementary option. An essential aspect of ViTs is that they utilize self-attention mechanisms to model the relationship at the global context level for images, which CNNs lack. ViTs were presented by Dosovitskiy et al. [8] as a scalable architecture that allowed for viewing images as a sequence of patches and thus allowed them to achieve state-of-the-art performance in large-scale image recognition tasks. For agriculture, a successful application of ViTs is the analysis of aerial and satellite imagery for crop health monitoring, as demonstrated in Chiu et al. [6] using the Agriculture-Vision dataset. According to their findings, ViTs outperform CNNs in detecting field-scale anomalies, which include deficiencies in nutrient supply and stress due to water shortages, as these require long-range pattern recognition. Yet computation intensity in ViTs is among the most prominent challenges it faces. Most of the memory and processing units are needed by the models, and Atapattu et al. [7] indicated that this poses a major challenge to their use in areas where agricultural technology has limited resources, representing a barrier to AI’s implementation in agriculture.

Agricultural fields have recently shown promise in the application of GNN-enabled modeling of spatial relationships and interrelationships across these fields. It enables better heterogeneous data analysis, combining local and global information. Gupta et al. [11] focused on GNNs in hybrid deep learning frameworks, considering crop health monitoring. They demonstrated how GNNs capture the spatial correlations that exist between diseased and healthy regions in crop fields. It was shown that the CNN-GNN approach, in contrast to CNN-only, for the PlantVillage dataset recording had a 5–10% improvement in accu- racy. These findings correlate with Singla et al. [9], who present an example of a possible GNN application, such as yield estimation or pest management, focused on modeling disease spread spatially. Though in the same manner as ViTs, GNNs carry the burden of being computationally expensive deep learning models, which makes them not scalable in applications for real-time use.

There has recently been an interesting trend of using hybrid deep learning models that combine CNNs with ViTs and GNNs. The goal of these models is to use the best of all three paradigms: CNNs to extract local features, ViTs for analyzing global context, and GNNs for spatial reasoning. Chitta et al. [23] proposed a hybrid model that uses a combination of CNN-extracted features, global patterns obtained from ViT techniques, and spatial relationships from GNNs. The hybrid model achieved an F1-Score of 0.92, beating the CNN (0.87) and ViT (0.89) as stand-alone alternatives. At the same time, Dewangan et al. [24] showed the benefits of hybrid models on the Agriculture-Vision dataset, where the incorporation of CNNs and attention mechanisms in hybrid models increased the accuracy of anomaly detection by 8% in comparison with conventional approaches. The advantages of hybrid models may enable them to overcome the limitations of their individual networks, as well as computational complexity, but this is yet to be discussed in the literature.

An issue that afflicts almost all studies concerns heterogeneous datasets differentiated by resolution, modality (RGB, hyperspectral, multispectral), and scale (leaf level vs. field level). Adao et al. [10] reviewed hyperspectral imaging applications in agriculture and pointed out that while hyperspectral data improves the sensitivity of disease detection, problems arise during the integration of this data into deep learning models, including variability in preprocessing and adaptability of the models. It would seem, according to Atapattu et al. [7], that most AI models encounter difficulties in fusing multimodal data, which weakens their generalization across agricultural settings. This discrepancy is starkly observed in Mohanty et al. [22], where CNN performance sharply deteriorated when images captured from the field were followed up, underlining the need to overcome dataset bias.

AgriEngineering 2025, 7, 353 7 of 30

Another major limitation facing AI in agriculture is the computational complexity involved, especially in regions that can access few resources. For instance, Li et al. [25] stated that ViTs have high demand for computational resources, making them infeasible in smallholder farming contexts, with only edge devices being available to support such appli- cations. Salcedo et al. [26] endorsed this by stating that deployment of ViT and GNN will require 10–20 times higher processing power than lightweight CNNs. Therefore, optimiza- tion strategies, such as pruning or quantization of the model, have to be applied to make these models implementable for agricultural use. Unfortunately, some of these techniques are still underexplored in the current literature. According to Borisov et al. [27], efficient inference strategies can help solve this problem, but it still remains mostly theoretical.

Interpretability is another major gap discussed in the literature. For AI models to be trusted and adopted by farmers and other stakeholders, they must offer actionable insights. However, numerous deep learning models, including CNNs and ViTs, are black boxes without any user-friendly interpretation of what goes on inside them. Gupta et al. [11] attempted to improve model interpretability by adding SHAP-based explainability and heat maps of disease-affected regions; however, their approach has not been validated over different crops. Dhal et al. [28] stress the importance of having interpretable AI, where trust and usability become critical factors in real-world agricultural scenarios.

Environmental variability includes climate changes and soil differences and poses a considerable challenge to AI model performance. As such, hyperspectral models were found by Adão et al. [10] to not transfer well when trained in one region and applied to others due to variations in spectral signatures. Likewise, Chiuet al. [6] found that aerial imagery models trained from one area performed poorly under different conditions. These observations demonstrate the need for domain-adaptive models, which are underdevel- oped in current research. Table 1 presents a summary of the various models, datasets, key tasks, and performance metrics, plus notable advantages and the weaknesses in each study, marking the evolution from standard Convolutional Neural Networks to hybrids embedding ViTs and GNNs for their accuracy and robustness.


> **Table 1. Summary of recent deep learning-based approaches in crop health monitoring and agricul-**

> tural image analysis.

Work Model Dataset Main Task Performance

Metric Strengths Limitations

High Accuracy

for Disease Detection in

Generalization

(2016) [22] CNN PlantVillage Plant Disease Classification 99% Accuracy

Mohanty et al.

to Real-World

Controlled Environments

Conditions

High Scalability and Performance

High Computational

Dosovitskiy et al. (2021) [8] ViT Custom Dataset Image Recognition

State-of-the-Art

in Large-Scale

Performance

Image Recognition

Complexity

Outperforms

High Memory and Processing

Anomaly Detection Accuracy +8%

CNNs for Long-Range

Chiu et al.

(2020) [6] ViT Agriculture-

Field Anomaly

Vision

Detection

Power Requirements

Pattern Recognition

AgriEngineering 2025, 7, 353 8 of 30


> **Table 1. Cont.**

Work Model Dataset Main Task Performance

Metric Strengths Limitations

Hybrid Models

Increased Computa- tional Cost

Gupta et al.

CNN, ViT,

GNN PlantVillage Crop Health

F1-Score of

Improve Accuracy and

(2024) [11]

Monitoring

0.92

Robustness

Enhances

Disease Detection using Hyper- spectral Data

Increased Sensitivity for

Integration Challenges

Disease Sensitivity with

Hyperspectral

Adão et al. (2017) [10]

Hyperspectral

Imaging +

Data

Disease Detection

with Deep

CNN

Hyperspectral

Learning

Data

Combines CNN, ViT, and

Increased Accuracy with

High Compu-

Atapattu et al.

CNN, ViT,

Custom Datasets

Crop Health

GNN for

tational Demands

(2024) [7]

GNN

Monitoring

Hybrid Models

Robust Prediction

Effective for Disease Spread

Limited Scalability for

Disease

Improved Prediction Robustness

Singla et al.

(2024) [9] GNN Custom Datasets

Spread Modeling

and Pest Management

Real-Time Applications

Excellent for

High Accuracy in

Lack of Explainability

Disease Classification in

Pest and

Smart Agriculture

El Sakka et al.

Disease Detection

(2024) [5] CNN

Disease Detection

and Inter- pretability

Dataset

Field Conditions


## 3. Proposed Methodology

The AgroVisionNet framework has been proposed with a view to utilizing hybrid deep learning, eradicating the primarily anomalous behavior of precision agriculture. It combines Convolutional Neural Networks (CNNs), Vision Transformers (ViTs), and Graph Neural Networks (GNNs) under one roof. Consequently, AgroVisionNet can identify local features, determine global spatial dependencies, and work out the relational interactions between regions of interest (ROIs) on agricultural images.

Starting with the preprocessing of the input image I, two versions of the image are obtained: Ifull, which will be utilized for complete extraction of features, and Ipatch, which is further dissected into many patches for subsequent processing. Local features come from Ifull, driven through a CNN. The CNN acts as a feature extractor that provides an image-to-vector mapping as follows:

FCNN = FCNN(Ifull) (1)

where FCNN represents the CNN model, and FCNN captures fine-grained details such as textures and disease symptoms.

Global Context Learning is achieved by partitioning Ipatch into uniform patches, em- bedding them into feature vectors, and applying a Vision Transformer (ViT). The ViT computes relationships between patches using the self-attention mechanism:



QKT

√dk

Z = Softmax

V (2)

AgriEngineering 2025, 7, 353 9 of 30

where Q, K, V are the query, key, and value matrices derived from the patch embeddings, and dk is the dimension of the key vectors. The output of the ViT, denoted as FViT, is a feature representation of the image that captures long-range dependencies:





FViT = FViT

Ipatch

(3)

To refine these features further, AgroVisionNet constructs a graph G = (V, E), where nodes V represent the image patches, and edges E represent the spatial relationships be- tween patches. A GNN processes this graph by using the layers of the Graph Convolutional Network (GCN), updating node features iteratively as follows:


## 2 ˆA ˆD−1

2 H(l)W(l)




ˆD−1

H(l+1) = σ

(4)

Here, ˆA = A + I is the adjacency matrix with self-loops, is the degree matrix of ˆA, H(l) is the node feature matrix at layer l, W(l) is a trainable weight, and σ is a non-linear activation function. After L layers, the GNN produces a refined feature matrix FGNN:

FGNN = H(L) (5)

The outputs of the CNN, ViT, and GNN components are then concatenated into a single feature vector, Ff usion, which is passed through a fully connected layer for classification. Let FCNN ∈Rd1 be the local feature vector extracted by the CNN, FViT ∈Rd2 be the global contextual embedding from the Vision Transformer, and FGNN ∈Rd3 be the spatially refined representation from the Graph Neural Network. The fused multi-resolution feature representation Ff usion is obtained as follows:





Wf · (α1 ⊙FCNN ⊕α2 ⊙FViT ⊕α3 ⊙FGNN) + bf

Ff usion = σ

(6)

where ⊕denotes concatenation; ⊙represents element-wise weighting; α1, α2, α3 ∈R+ are learnable attention coefficients that control each modality’s contribution; Wf and bf are the weights and bias of the fusion layer; and σ(·) is a non-linear activation function (e.g., ReLU). Finally, the classification output is computed as





ˆy = Softmax

WfusionFf usion + bc

(7)

where Wfusion and bc are the final layer’s weights and bias, and y is the predicted class distribution. The model is trained using a cross-entropy loss function:

L = −1





N i=1 ∑

C c=1 yi,clog

N∑

ˆyi,c

(8)

where N is the number of samples, C is the number of classes, yi,c is the ground truth for class c of sample i, and ˆyi,c is the predicted probability for the same.

An experimental investigation incorporates the Adam optimizer utilizing a learning rate scheduler to facilitate optimum convergence. The hybrid architecture and multi- resolution fusion combined with graph-based reasoning provide a robust and scalable solution in precision agriculture with AgroVisionNet. The model accurately interprets and predicts real-time applications in agriculture by leveraging both local and global features, as well as relational views.

The architectural design of AgroVisionNet is summarized in Table 2, which outlines the complete configuration of its three primary modules: the CNN-based local feature extractor, the Vision Transformer (ViT) for capturing long-range dependencies, and the

AgriEngineering 2025, 7, 353 10 of 30

Graph Neural Network (GNN) for relational reasoning across spatially connected regions. Each module is parameterized to ensure complementary functionality—where the CNN backbone (based on EfficientNet-B0) extracts low- to mid-level representations, the ViT encoder models global contextual relations across 16 × 16 patches, and the GNN (built using Graph Convolutional layers) captures inter-patch dependencies through dynamically constructed adjacency matrices. The fusion layer concatenates the outputs from these modules into a unified feature space, which is subsequently passed through fully connected layers for classification. This table provides a clear overview of layer configurations, embedding dimensions, activation functions, and output sizes, facilitating reproducibility and transparency of the proposed model architecture.


> **Table 2. Architecture specification of AgroVisionNet.**

Block Component Configuration/Layers Input →Output Tensor (Per Image) Key Hyperparameters/Notes

Optional RandAugment (N = 2, M = 9), MixUp = 0.2, CutMix = 0.2

Input and Preprocess — Resize →Center/Random Crop → Normalize (ImageNet mean/std)


## 3 × H × W →3 × 224 ×

224

Conv1(7 × 7, s2) →BN/ReLU → MaxPool →{Bottleneck × 3,4,6,3} → GAP

ResNet-50 (ImageNet-1k pretrained)


## 3 × 224 × 224 →2048 d

(post-GAP)

Output projected to 512 d via Linear (2048→512) for fusion

Local Feature Encoder (CNN)

Patchify (16 × 16) →14 × 14 = 196 tokens →Linear(768) + PosEmb → Encoder L = 12, H = 12 heads, MLP dim = 3072 →[CLS]

ViT-Base/16 (ImageNet- 21k→1k pretrained)


## 3 × 224 × 224 →[CLS]

768 d; patch tokens: 196 ×
768

[CLS] projected to 512 d via Linear(768→512); patch tokens feed GNN graph

Global Context Encoder (ViT)

Graph G = (V,E) with |V| = 196; E via 2 cues: (i) k-NN (k = 8) in 2-D patch grid; (ii) feature edges if cosine sim ≥τ = 0.7 (symmetric union). Global readout: mean + max pooling then Linear (512)

Node init: patch tokens (196 × 768) →Linear(768→256) →SAGEConv (256→256) →SAGEConv (256→256) →ReLU/Dropout(0.1)

GraphSAGE (or GAT, ablation-ready)

196 × 768 →196 × 256 → graph-pooled 512 d

Relational Encoder (GNN over patches)

Corrected fusion: Ffusion = Concat

LayerNorm before MLP; optional FiLM gating for dataset-specific tuning

F512

CNN, F512

ViT, F512

→1536 d →MLP: 1536→768 (GELU, Dropout 0.2) →512 d

 

[512 + 512 + 512] →1536 →512 d

Fusion Layer Concatenation + MLP

GNN

Classifier Head — Linear (512→C) + Softmax 512 →C C = #classes per dataset (e.g., PlantVillage C = 38; EuroSAT C = 10)

Fuse ViT patch features (14 × 14 × 768) + CNN stride-matched features →1 × 1 Conv →Upsample × 16 → C channels + Sigmoid/Softmax

Used on Agriculture-Vision/UAV datasets when segmentation is required

14 × 14 × 768 →224 × 224 × C

(Optional) Segmentation Head

Lightweight UPerNet-style

Classification: CE + Label-Smoothing (ε = 0.1); Segmentation: Dice + BCE (λ = 0.5); Class imbalance: focal (γ = 2) optional

— Multi-task: weighted sum (α_cls = 1.0, α_seg = 0.5)

Losses —

Optimizer: AdamW (β1 = 0.9, β2 = 0.999, wd = 1 × 10−4); LR = 3 × 10−4; Cosine decay; Warmup 5 epochs; Batch = 32; Epochs = 100

Splits: 80/10/10 (or official splits when provided); Seed = 42; AMP mixed precision

—

Training Setup —

Build 14 × 14 patch grid; compute 2-D neighbors (k = 8); compute cosine similarity on 768 d ViT tokens; add edge if sim ≥0.7; union both edge sets; add self-loops

Edges treated as undirected; degree-norm in SAGE/GAT; dropout on edges = 0.1

196 nodes; ~ (196 × 8) + E_sim edges

Graph Construction (summary) —

Dropout(0.1–0.2), Stochastic Depth (ViT drop-path 0.1), Weight decay 1 × 10−4 — Early-stopping on val F1 (patience 10)

Regularization —

Implementation — PyTorch 2.x; timm ViT-B/16; PyG (GraphSAGE/GAT); CUDA 12 — Repro

To ensure clarity and reproducibility, the following algorithms describe the procedural workflow of AgroVisionNet. Algorithm 1 details the graph construction process, where image patches are treated as nodes and connections are dynamically defined based on

AgriEngineering 2025, 7, 353 11 of 30

both spatial proximity and feature similarity. This algorithm formalizes how local and global contextual relationships are encoded before being passed to the GNN component. Algorithm 2 outlines the complete training and inference pipeline of AgroVisionNet, in- cluding the feature extraction, fusion, and optimization stages. The stepwise structure emphasizes how CNN-derived features, ViT embeddings, and GNN relational outputs are integrated within a unified framework. Together, these algorithms provide a transparent view of the model’s operation, highlighting the hierarchical information flow from raw images to final predictions.

Algorithm 1. GraphConstruction(P): Patch Graph over ViT Tokens

Inputs: P ∈Rˆ{N × D} //ViT patch tokens for one image (N = 196, D = 768) Grid size: 14 × 14 //N = 14 × 14 for ViT/16 at 224 × 224 k = 8 //spatial neighbors τ = 0.7 //cosine similarity threshold Procedure GraphConstruction(P): //1) Spatial k-NN on 2D grid

V ←{1..N}; E_spatial ←∅ for node u in V: N_sp(u) ←k nearest neighbors of u in (row, col) grid E_spatial ←E_spatial ∪{(u, v) | v ∈N_sp(u)} //2) Feature-similarity edges

E_feat ←∅ for (u, v) with u̸=v: sim ←cos(P[u], P[v]) = (P[u]·P[v])/(||P[u]||·||P[v]||) if sim ≥τ: E_feat ←E_feat ∪{(u, v)} //3) Final edges (undirected with self-loops)

E ←SymmetricClosure(E_spatial ∪E_feat) ∪{(u, u) ∀u∈V} //4) Node init & GNN runs inside TRAIN(): // Node init: hˆ0_u = Linear_768→256(P[u]) return Graph G = (V, E)

Algorithm 2. Fusion and Prediction Heads

Inputs: F_CNN ∈Rˆ{B × 512}, F_ViT ∈Rˆ{B × 512}, F_GNN ∈Rˆ{B × 512} Procedure FusionMLP(F_CNN, F_ViT, F_GNN): F_cat ←Concat(F_CNN, F_ViT, F_GNN) //shape [B, 1536] F_cat ←LayerNorm(F_cat) F_fuse ←GELU(Linear(1536→768)(F_cat)) F_fuse ←Dropout(0.2)(F_fuse) F_out ←Linear(768→512)(F_fuse) return F_out //[B, 512] Procedure Headκ(F_out): logits ←Linear(512→C)(F_out) //C = #classes return logits

The flowchart depicted in Figure 2 provides an exhaustive visual representation of the AgroVisionNet architecture, detailing every stage of the processing pipeline and data flow involved. From the very outset, there are input images, either RGB aerial or

AgriEngineering 2025, 7, 353 12 of 30

satellite imagery, say, from the PlantVillage or EuroSAT datasets, and these images then undergo preprocessing steps for consistent treatment. This encompasses resizing images to 224 × 224 pixels in some cases; normalization using mean and standard deviation values with respect to the dataset; and augmentation enhancement techniques, such as random cropping and/or random flipping, which are applied for creating further diversity in the training images to make the dataset slightly more robust with the model. The preprocessed images are fed into the CNN Feature Extraction module, giving a feature map of dimension 512. Further, two branches are created: Global Context Learning, which employs a Vision Transformer (ViT), and Graph-Based Refinement, which uses a Graph Neural Network (GNN). The Vision Transformer used patches, tokens, and self-attention mechanisms on the features to capture global contextual relationships, which are very important for land-cover classification. At the same time, the GNN builds the graph nodes and edges from the features that were extracted from the CNN to further enhance local information through graph convolutional layers. The resultant features from both the ViT and GNN modules are fused and fed into the classifier output layer, equipped with either SoftMax activation for classification or sigmoid activation for segmentation.


> **Figure 2. AgroVisionNet flowchart.**

AgriEngineering 2025, 7, 353 13 of 30


## 4. Datasets

AgroVisionNet has undergone evaluation using a wide variety of datasets, thereby demonstrating its efficacy across diverse agrarian environments. In fact, these datasets encompass various image forms and resolutions, as well as specific purposes, provid- ing a solid foundation for testing and evaluating the model’s capabilities in crop health monitoring and anomaly detection.

The PlantVillage dataset is a large-scale agricultural image collection aimed at plant disease diagnosis, containing 54,306 labeled images covering 38 crop–disease pairs dis- tributed among 14 crop species that include healthy and diseased leaves. Figure 3 shows samples of diseased crops from this dataset. Table 3 presents a summary of the dataset’s information. This dataset assists in identifying diseases such as apple scab, corn gray leaf spot, and tomato late blight for disease diagnosis. These classes comprise “healthy” and “disease-specific” labels. The diversity of images available helps to develop resilient machine learning models for plant disease diagnosis [22].


> **Figure 3. Samples from PlantVillage dataset [22].**

AgriEngineering 2025, 7, 353 14 of 30


> **Table 3. Summary of datasets used for evaluating AgroVisionNet.**

Dataset Image Type Source Applications Key Features

Leaf-level disease

Over 50,000 images, 14 crop species, multiple diseases

PlantVillage RGB Ground-based

detection and

classification

Field-level anomaly detection and semantic

High-resolution images, annotated field patterns

Agriculture-Vision RGB, NIR UAV

segmentation

Land-cover classification

BigEarthNet Multispectral,

Satellite (Sentinel-1/2)

Multi-label annotations cover diverse land types

and large-scale crop

SAR

monitoring

UAV-based Crop

and Weed RGB UAV Weed detection and crop

High-resolution images, segmentation annotations

monitoring

10 classes, including agricultural and non-agricultural areas

EuroSAT RGB, Multispectral

Satellite (Sentinel-2)

Land-cover classification

and anomaly detection

The Agriculture-Vision dataset comprises 94,986 aerial images derived for anomaly detection in agricultural land. The data is distributed in nine classes, which include Double Plant, Nutrient Deficiency, Dry Down, Weed Cluster, and others. Figure 4 shows samples from this dataset. Ideally, each image contains RGB and NIR information, which should make it possible to conduct a comprehensive assessment of agricultural anomalies under all environmental conditions [6].


> **Figure 4. Samples from Agriculture-Vision dataset. For each annotation, invalid regions have been**

> blacked out. Note the extreme size and shape variations of some annotations. The visualizations
above are chosen to best illustrate each pattern. Images best viewed with color and zoomed in [6].

BigEarthNet is a very large remote sensing dataset containing 549,488 Sentinel-1 and Sentinel-2 image patches over 19 different land-cover classes, including Forest, Urban Areas, Pasture, Shrubland, Wetland, and more. It was designed for a multiclass land-cover classification task that involved studying environmental changes and land-use monitoring using per-pixel annotations [29].

The Crop and Weed UAV dataset is designed for discriminating crops from weeds using aerial images. It is composed of 8034 high-resolution annotated images of crops, including maize, sugar beet, sunflower, and soy; also present are weeds, such as broadleaf and grassy weeds. The original dataset labels are divided into 8 crop and 16 weed classes. The dataset includes bounding boxes, segmentation masks, and stem annotations, which are key specifications that make it optimal for various precision agriculture tasks, such as weed detection and crop classification [30].

AgriEngineering 2025, 7, 353 15 of 30

The EuroSAT dataset comprises 27,000 Sentinel-2 satellite images, categorizing each image into one of 10 Earth-Cover types, including Annual Crops, Pasture, Forest, Urban Areas, and Water Bodies. The dataset has been heavily balanced, with each class assigned approximately 2000–3000 samples for classification. The resulting distribution will enable the data to rewrite class distributions, making it amenable to a number of land-cover classification and environment-monitoring tasks [31]. Figure 5 represents class distributions for the five datasets used in the compression and evaluation of AgroVisionNet.


> **Figure 5. Class distributions for the five datasets used in the evaluation of AgroVisionNet. This**

> combination of datasets means that AgroVisionNet undergoes thorough testing over different tasks,
resolutions, and scales, thus illustrating that such a system is versatile and robust for precision farming.


## 5. Evaluation Metrics

The performance evaluation of the AgroVisionNet framework should, on the other hand, provide a holistic assessment in a number of dimensions to determine how effective it is, how robust it could be, and its ultimate usage in IoT anomaly detection tasks. Hence the theorized metrics evaluation will be based on the following three aspects: classifica- tion accuracy, real-time efficiency, and computational resource utilization. The accuracy calculates the percentage of correctly classified samples:

Accuracy = TP + TN TP + TN + FP + FN (9)

where TP, TN, FP, and FN represent true positives, true negatives, false positives, and false negatives, respectively.

AgriEngineering 2025, 7, 353 16 of 30

Precision quantifies the proportion of correctly detected anomalies out of all instances classified as anomalies:

Precision = TP/TP + FP (10)

High precision indicates low false positive rates, critical for IoT environments where false alarms can lead to unnecessary actions [32].

Recall measures the proportion of correctly detected anomalies out of all actual anoma- lies:

Recall = TP/TP + FN (11)

High recall ensures that most anomalies are identified, reducing the risk of undetected threats.

The F1-Score is the harmonic mean of precision and recall, providing a balanced evaluation of both metrics:

F1 −Score = 2 · Precision · Recall

Precision + Recall (12)

It is particularly useful in imbalanced datasets where one class (e.g., anomalies) is underrepresented.

The ROC curve plots the true positive rate (TPR) against the false positive rate (FPR) at various classification thresholds:

TPR = TP TP + FN, FPR = FP FP + TN (13)

AUC-ROC stands for Area Under the ROC Curve. It determines the model’s ability to classify normal and anomalous data. The higher the AUC, the better the performance [1].

The PR curve, which plots precision as a function of recall, is a suitable way of presenting results when detecting anomalies. The Area Under the Precision–Recall Curve (AUC −PR) gives an especially helpful indication when it comes to skewed data, where it is often much more indicative of performance than ROC curves.

The mAP metric is derived by averaging AP values across all anomaly classes [33,34]. For a single class, AP is simply the area under the Precision–Recall (PR) curve:

Z 1

AP =

0 Precision(r) dr (14)

where r is the recall.

For multiple classes, mAP is the average of the AP values across all C classes:

mAP = 1

C C=1 APc (15)

C∑

For pixel-level classification tasks, such as identifying diseases or anomalies in leaves, intersection over Union (IoU) could be used to measure the overlap between predicted and ground-truth regions.

IoU = Area of Overlap

Area of Union (16)

Mean Absolute Error (MAE) is a metric that measures the average deviation between predicted probabilities (ˆyi) and true labels (yi) across all samples in a dataset. It evaluates how closely the predicted probabilities accompany the actual ground truth. This is obtained

AgriEngineering 2025, 7, 353 17 of 30

by calculating the mean value of the absolute differences between the predicted probability and the true label for each sample. Mathematically, it is expressed as

N ∑ i=1

MAE = 1

| yi −ˆyi | (17)

N

Here, N represents the total number of samples, ˆyi is the true label (typically 0 or 1 in binary classification), and ˆyi is the predicted probability (a value between 0 and 1). A lower MAE indicates better calibration of the model’s predicted probabilities to the true labels, with a perfect MAE of 0 implying that all predictions perfectly match the ground truth.

The Concordance Index (C-Index) would always measure whether our model correctly ranks predictions when compared to the ground truth, as the metric is applied in a broad array of tasks—including hazard estimation and ranking problems—and also (in the ranking of confirmative) classification based on confidence scores. In other words, the C-Index is defined as the ratio of the concordant pairs over all the pairs present in a set. A pair of samples (i, j) is considered concordant if the predicted ranking aligns with the ground truth. Specifically, the predictions are concordant if

ˆyi > ˆyj when yi > yj, or

(18)

ˆyi= ˆyj when yi = yj

The formula for the C-Index is

C-Index = Number of Concordant Pairs

Total Number of Pairs (19)

Here, ˆyi and ˆyj are the predicted scores for samples i and j, while yi and yj are their corresponding true labels. A C-Index of 1 indicates perfect ranking alignment with the ground truth, while a value of 0.5 suggests random ranking. This metric is particularly useful when the model’s ability to rank predictions accurately is more important than the exact predicted probabilities.

5.1. Experimental Setup

All experiments were performed using a Google Colab T4 GPU and the PyTorch framework. Input images were resized to 224 × 224, normalized, and augmented with random flipping and rotations. The models were trained using the Adam optimizer (learning rate = 0.001, cosine annealing scheduler, batch size = 32) for 100 epochs with a 70/15/15 train–validation–test split. For segmentation datasets (e.g., Agriculture-Vision, UAV Crop-Weed), outputs were reformulated as multi-label classification using sigmoid activation. The evaluation metrics included accuracy, precision, recall, F1-Score, IoU, AUC, and C-Index. All baseline models were retrained under identical conditions to ensure a fair comparison with AgroVisionNet.

5.2. Computational Complexity and Efficiency

The hybrid design of AgroVisionNet inevitably increases model parameters relative to single-stream networks. To quantify this overhead, we estimated the number of parameters and floating-point operations (FLOPs) for each major component. The ResNet-50 backbone contributes ≈25 M parameters (3.8 GFLOPs per image), the ViT-Base/16 encoder ≈86 M parameters (17.6 GFLOPs), and the GraphSAGE module ≈4 M parameters (0.6 GFLOPs). After fusion and classification, the total model footprint reaches ≈115 M parameters and 22 GFLOPs per inference—roughly 1.7× that of a stand-alone ViT but still tractable on modern GPUs and edge accelerators.

AgriEngineering 2025, 7, 353 18 of 30

Training on Google Colab converged in ≈22 h for 100 epochs on PlantVillage and ≈ 28 h on EuroSAT. Inference latency averaged 18 ms per 224 × 224 image (batch size = 32), confirming real-time feasibility for UAV and field-robot deployment.


## 6. Results and Discussion

This research compared AgroVisionNet with nine other modern methods over five diverse datasets: PlantVillage, Agriculture-Vision, BigEarthNet, UAV Crop and Weed, and EuroSAT. Thereby, a performance analysis could be conducted across different metrics, including accuracy, precision, recall, F1-Score, Intersection over Union (IoU), Area Under the Curve (AUC), Mean Absolute Error (MAE), and Concordance Index (C-Index) to comprehensively analyze their performance. The results proved that AgroVisionNet always outperformed most of the metrics, especially excelling in classification and segmentation tasks. AgroVisionNet enabled the fusion of all features and captured around two global features, but also helped to intensify predictive accuracy and enhance the rank function through a combination of a CNN, a Vision Transformer, and a Graph Neural Network. In this section, we assessed the performance of AgroVisionNet concerning other algorithms for each dataset. The best results represented in bold in the tables.

The comparative analysis in Table 4 highlights the superior performance of AgroVi- sionNet across most metrics. With the highest accuracy (97.8%), AUC (99.2%), and C-Index (97.4%), AgroVisionNet demonstrates its robust classification and segmentation capabilities. Its low MAE (0.6%) further underscores its precise probabilistic predictions. Vision Trans- former (ViT) and MSG-GCN also exhibit strong performance, particularly in global feature modeling and graph-based refinement, achieving high C-Index values of 96.5% and 96.0%, respectively. YOLOv9 balances high accuracy (96.3%) and a competitive C-Index (95.8%) with a low MAE (1.3%), making it a suitable choice for real-time applications. Traditional models like ResNet-50 and Hybrid CNN-RNN, while effective, lag in terms of IoU and C-Index, reflecting their limitations in handling complex spatial relationships and ranking tasks. As a result of its hybrid architecture, AgroVisionNet surpasses all other models, which demonstrates it to be an excellent choice for precision agriculture works using the PlantVillage dataset. AgroVisionNet demonstrates the highest IoU scores across most disease types, highlighting its superior capability in fine-grained leaf-level classification, as shown in Figure 6, which presents an IoU performance heatmap for the PlantVillage dataset across 12 crop disease classes using five competing models.


> **Table 4. Comparison of the performance of AgroVisionNet versus other state-of-the-art algorithms**

> on the PlantVillage dataset in various evaluation metrics.

Model Accuracy Precision Recall F1-Score IoU AUC MAE C-Index

AgroVisionNet 97.8 98.2 97.5 97.8 95.6 99.2 0.6 97.4 ResNet-50 93.5 92.7 93.8 93.2 89.4 96.1 2.1 92.5 EfficientNet-B0 95.1 94.3 95.0 94.7 90.8 97.4 1.6 94.1 Vision Transformer (ViT) 96.7 97.0 96.5 96.8 94.3 98.5 1.0 96.5 Graph Neural Network

(GNN) 95.9 96.1 96.3 96.2 93.6 97.9 1.2 96.1

YOLOv9 96.3 96.0 96.2 96.1 92.7 98.1 1.3 95.8 Mask R-CNN 95.3 94.8 94.6 94.7 91.5 96.8 1.8 94.2 Hybrid CNN-RNN 94.6 94.0 94.4 94.2 90.2 96.2 2.0 93.7 ConvLSTM 94.9 94.5 94.7 94.6 91.0 96.9 1.9 94.5 MSG-GCN 96.1 96.3 96.4 96.4 93.8 98.0 1.2 96.0

AgriEngineering 2025, 7, 353 19 of 30


> **Figure 6. IoU performance heatmap for the PlantVillage dataset across 12 crop diseases using the five**

> models.

The results in Table 5 reveal that AgroVisionNet achieves the highest overall per- formance on the Agriculture-Vision dataset, particularly excelling in terms of accuracy (94.5%), AUC (96.8%), and C-Index (95.6%), which demonstrates its robust capability in segmentation and large-scale anomaly detection tasks. The model’s low MAE (1.1%) fur- ther emphasizes its predictive reliability. Among the other algorithms, Vision Transformer (ViT) and MSG-GCN closely follow, achieving high C-Index values (93.7% and 93.5%, respectively) due to their ability to model spatial and relational dependencies. YOLOv9, while slightly behind in terms of AUC (94.8%) and C-Index (93.2%), maintains competitive performance with a balance of accuracy and computational efficiency. That said, traditional models like ResNet-50 and Hybrid CNN-RNN exhibit a lower IoU and C-relation, indicat- ing that such methods have a hard time dealing with spatially distributed anomalies in the dataset. EfficientNet-B0 performs better than ResNet-50, but still lags behind the modern architecture. All in all, AgroVisionNet exhibits higher performance than the other models. It represents a good fit for datasets dominated by image segmentation activities, such as in Agriculture-Vision. AgroVisionNet achieves the highest segmentation performance in complex aerial imagery, excelling particularly in classes such as Nutrient Deficiency and Water Stress. Figure 7 presents an IoU performance heatmap for the Agriculture-Vision dataset across nine agricultural anomaly classes, comparing AgroVisionNet with the other five models.

The results in Table 6 show that AgroVisionNet maintains the highest performance on the BigEarthNet dataset, achieving the highest accuracy (92.3%), AUC (95.7%), and C-Index (94.4%). The system has demonstrated its overall strength in handling tasks involving multi-label and multi-class land-cover classification, with an IoU of 88.5% and an MAE of 1.5, further corroborating its robust ability to predict land-cover types with very high confidence. VIT and MSG-GCN have nearly identical percentages of 93.0% and 92.9%, respectively, indicating that they are effective in modeling complex spatial patterns in satellite data. For instance, YOLOv9 and the Graph Neural Network (GNN) provided more-or-less balanced results, which can be beneficial for specific use cases where accuracy and computational efficiency are traded off. However, with very high IoU and C-Index values, traditional models such as ResNet-50 and Hybrid CNN-RNN appear to struggle

AgriEngineering 2025, 7, 353 20 of 30

in capturing multispatial information from satellite imagery. Although it has improved performance compared to ResNet-50, EfficientNet-B0 still lags behind other newer models in terms of performance. In all, AgroVisionNet demonstrates better performance and appears to be an efficient choice for tackling large-scale land-cover classification over the BigEarthNet dataset. The results in Figure 8, which represent the IoU performance heatmap for the BigEarthNet dataset covering 10 representative land-cover classes, confirm AgroVi- sionNet’s effectiveness in multi-class, large-scale satellite image segmentation compared to baseline and state-of-the-art models.


> **Table 5. Comparison of the performance of AgroVisionNet versus other state-of-the-art algorithms**

> on the Agriculture-Vision dataset in various evaluation metrics.

Model Accuracy Precision Recall F1-Score IoU AUC MAE C-Index

AgroVisionNet 94.5 95.1 94.0 94.5 90.3 96.8 1.1 95.6 ResNet-50 88.7 87.3 89.5 88.4 83.4 91.7 3.5 89.2 EfficientNet-B0 90.1 89.6 90.3 89.9 85.6 93.5 2.8 90.8 Vision Transformer (ViT) 92.6 93.3 92.0 92.6 88.5 95.1 1.6 93.7 Graph Neural Network

(GNN) 91.8 92.5 91.4 91.9 87.8 94.6 1.9 92.9

YOLOv9 92.0 92.1 91.8 92.0 87.2 94.8 1.8 93.2 Mask R-CNN 90.9 90.5 91.0 90.8 86.0 93.8 2.4 91.5 Hybrid CNN-RNN 89.5 88.7 89.3 89.0 84.5 92.8 3.1 90.0 ConvLSTM 89.8 89.0 89.7 89.3 85.1 93.2 2.9 90.4 MSG-GCN 92.3 93.0 92.1 92.5 88.0 94.9 1.7 93.5


> **Figure 7. IoU performance heatmap for the Agriculture-Vision dataset across nine agricultural**

> anomaly classes using the five models.

The results in Table 7 highlight that AgroVisionNet outperforms other models on the UAV Crop and Weed dataset, achieving the highest accuracy (91.5%), IoU (87.8%), AUC (95.2%), and C-Index (93.9%). Its low MAE (1.4%) indicates precise predictions, making it a robust solution for UAV-based crop and weed segmentation tasks. Vision Transformer (ViT) and MSG-GCN follow closely, with high C-Index values of 92.3% and 92.1%, respectively, reflecting their ability to capture spatial relationships effectively. YOLOv9 delivers com-

AgriEngineering 2025, 7, 353 21 of 30

petitive performance, striking a balance between high accuracy (89.8%) and a reasonable Model Error (MAE) of 2.1%, making it suitable for real-time UAV applications. Traditional models, such as ResNet-50 and Hybrid CNN-RNN, lag behind in terms of IoU and C-Index, revealing limitations in segmenting fine-grained crop and weed regions. EfficientNet-B0 offers improved results over ResNet-50 but does not match the performance of newer architectures. Overall, AgroVisionNet demonstrates superior segmentation accuracy and ranking capabilities, making it an excellent choice for UAV-based agricultural analysis. Figure 9 shows the IoU performance heatmap for the UAV Crop and Weed dataset across 10 fine-grained crop and weed categories, confirming that AgroVisionNet provides the most accurate segmentation. This demonstrates strong generalization across weed types and plant structures.


> **Table 6. Comparison of the performance of AgroVisionNet versus other state-of-the-art algorithms**

> on the BigEarthNet dataset in various evaluation metrics.

Model Accuracy Precision Recall F1-Score IoU AUC MAE C-Index

AgroVisionNet 92.3 92.8 91.9 92.3 88.5 95.7 1.5 94.4 ResNet-50 87.2 86.5 87.0 86.7 80.3 90.2 3.7 88.1 EfficientNet-B0 89.0 88.4 88.7 88.5 82.9 91.8 2.8 89.8 Vision Transformer (ViT) 91.2 91.5 90.8 91.1 87.0 94.2 1.9 93.0 Graph Neural Network

(GNN) 90.7 91.2 90.3 90.7 86.5 93.8 2.0 92.4

YOLOv9 90.8 90.5 90.6 90.6 86.2 93.9 1.8 92.6 Mask R-CNN 89.5 89.0 89.3 89.2 83.8 92.5 2.6 90.5 Hybrid CNN-RNN 88.4 87.6 88.2 87.9 82.2 91.5 3.1 89.3 ConvLSTM 88.9 88.2 88.7 88.5 82.8 91.9 2.9 89.6 MSG-GCN 91.0 91.3 90.7 91.0 86.8 94.0 1.8 92.9


> **Figure 8. IoU performance heatmap for the BigEarthNet dataset across 10 land-cover classes using**

> the five models.

AgriEngineering 2025, 7, 353 22 of 30


> **Table 7. Comparative performance of AgroVisionNet and other state-of-the-art algorithms on the**

> UAV Crop and Weed dataset across multiple evaluation metrics (presented as percentages).

Model Accuracy Precision Recall F1-Score IoU AUC MAE C-Index

AgroVisionNet 91.5 92.0 91.2 91.6 87.8 95.2 1.4 93.9 ResNet-50 85.7 84.9 85.5 85.2 78.5 89.7 3.9 87.0 EfficientNet-B0 87.9 87.2 87.7 87.4 81.1 91.2 2.9 89.0 Vision Transformer (ViT) 90.3 90.8 90.1 90.4 85.5 93.7 2.0 92.3 Graph Neural Network

(GNN) 89.7 90.1 89.4 89.8 84.8 93.2 2.2 91.6

YOLOv9 89.8 89.5 89.6 89.6 84.5 93.3 2.1 91.7 Mask R-CNN 88.5 88.0 88.3 88.2 82.7 91.8 2.7 90.2 Hybrid CNN-RNN 87.3 86.5 87.1 86.8 80.4 90.8 3.3 88.7 ConvLSTM 87.6 86.9 87.4 87.1 80.9 91.0 3.0 89.1 MSG-GCN 90.0 90.5 90.2 90.3 85.0 93.5 2.0 92.1


> **Figure 9. IoU performance heatmap for the UAV-Based Crop and Weed dataset across 10 crop and**

> weed classes using the five models.


> **Table 8 demonstrates that AgroVisionNet achieves the highest performance on the**

> EuroSAT dataset, excelling in terms of accuracy (96.4%), AUC (98.6%), and C-Index (97.3%).
Its low MAE (0.9%) highlights the model’s reliability and precise classification of satellite
imagery across diverse land-cover types. The high IoU (92.9%) further reflects its strong seg-
mentation capabilities. Vision Transformer (ViT) and MSG-GCN also perform exceptionally
well, with high C-Index values of 96.5% and 96.2%, respectively, showcasing their ability
to model spatial and hierarchical relationships. YOLOv9 offers balanced performance,
achieving an AUC of 97.4% and a C-Index of 96.0%, making it practical for scenarios that
require high accuracy and real-time efficiency. Traditional models, such as ResNet-50 and
Hybrid CNN-RNN, exhibit lower performance, particularly in terms of IoU and C-Index,
reflecting their reduced ability to capture complex patterns in satellite data. EfficientNet-B0,
while outperforming ResNet-50, does not match the performance of advanced models, such
as AgroVisionNet. Overall, AgroVisionNet’s hybrid design delivers superior performance,
making it the best choice for land-cover classification tasks on the EuroSAT dataset. Fig-
ure 10 presents an IoU performance heatmap for the EuroSAT dataset across 10 land-cover

AgriEngineering 2025, 7, 353 23 of 30

classes. AgroVisionNet leads in terms of segmentation accuracy, particularly in urban and agricultural regions, affirming its robustness for remote sensing classification tasks.


> **Table 8. Comparative performance of AgroVisionNet and other state-of-the-art algorithms on the**

> EuroSAT dataset across multiple evaluation metrics (presented as percentages).

Model Accuracy Precision Recall F1-Score IoU AUC MAE C-Index

AgroVisionNet 96.4 96.8 96.2 96.5 92.9 98.6 0.9 97.3 ResNet-50 91.8 91.1 91.6 91.4 85.6 94.0 2.5 92.0 EfficientNet-B0 93.2 92.7 93.1 92.9 87.5 95.1 1.9 93.5 Vision Transformer (ViT) 95.5 95.9 95.4 95.6 91.7 97.8 1.2 96.5 Graph Neural Network

(GNN) 94.9 95.4 94.7 95.0 90.9 97.3 1.4 95.8

YOLOv9 95.1 94.8 95.0 94.9 90.5 97.4 1.3 96.0 Mask R-CNN 93.8 93.2 93.6 93.4 88.3 95.8 1.7 94.5 Hybrid CNN-RNN 92.5 91.8 92.3 92.0 86.7 94.6 2.3 93.0 ConvLSTM 92.9 92.3 92.7 92.5 87.3 95.0 2.0 93.3 MSG-GCN 95.3 95.7 95.2 95.4 91.2 97.6 1.2 96.2


> **Figure 10. IoU performance heatmap for the EuroSAT dataset across 10 land-cover classes using the**

> five models.

To provide visual interpretability and validate that the model focuses on biologically meaningful features, Figure 11 presents SHAP/Grad-CAM visualizations of the AgroVi- sionNet model on representative tomato leaf disease samples. The left panels show the original images, while the right panels display the highlighted Regions of Interest (ROIs) identified by the final convolutional layer. These heatmaps emphasize the most influential pixels that contributed to each classification decision. In cases of (a) early blight, (b) leaf mold, (c) septoria leaf spot, and (d) yellow leaf curl virus, AgroVisionNet successfully localized the diseased regions, focusing on lesion boundaries, color changes, and texture distortions typical of the corresponding disease categories. This confirms that the model does not rely on background artifacts but rather learns disease-specific visual cues, thereby enhancing the explainability and trustworthiness of its predictions.

AgriEngineering 2025, 7, 353 24 of 30


> **Figure 11. Visualization of SHAP/Grad-CAM analysis. The left image shows the original image, and**

> the right image shows it highlighted by the final convolutional layer for the (a) early blight, (b) leaf
mold, (c) septoria leaf spot, and (d) yellow leaf curl viruses.


> **Figure 12 illustrates radar chart visualizations for comparative performance analyses**

> of AgroVisionNet in comparison to the ten leading benchmark algorithms on six separate
datasets: PlantVillage, Agriculture-Vision, BigEarthNet, UAV Crop and Weed, EuroSAT,
and an additional domain-specific dataset. Each radar chart displays seven evaluation
metrics among the competing approaches—accuracy, precision, recall, F1-Score, Intersection
over Union (IoU), Area Under the Curve (AUC), and Concordance Index (C-Index)—all
normalized to percentage values for direct comparison. From a radial layout perspective,
they allow simultaneous inspection of algorithms with impressive and less convincing
performance, again showing the sturdier profile of AgroVisionNet. It is worth noting that
AgroVisionNet stands out, exhibiting significantly higher performance across all metrics
while achieving the highest AUC, precision, and IoU on the PlantVillage and EuroSAT
datasets, which demonstrate its robustness and generalization capabilities in heterogeneous
agricultural imaging tasks. This visual comparison also clearly outlines the model’s optimal
compromise between classification accuracy on for instances of plant disease and the quality
of spatial segmentation, justifying its application in precision agriculture under various
real-world conditions.

For more validation, a comparison based on the statistical test was performed, and the non-parametric statistical hypothesis Wilcoxon signed-rank test (a paired difference, two- sided signed-rank test) as applied to perform a statistical significance analysis and derive strong and fair conclusions. All the applied methods were compared with AgroVisionNet for all five datasets. The differences were calculated for each of the two methods compared, then ranked from 1 (the smallest) to 5 (the largest). The signs ‘+ve’ or ‘−ve’ were subse- quently assigned to the corresponding differences in the ranks. R+ and R−were assigned to all the +ve and −ve ranks, respectively after summing them up separately. The T value was compared against a significance level of α = 0.20, with a critical value of 2 for the five datasets, where T = min {R+, R−}. The null hypothesis was that all performance differences between any two compared methods may occur by chance, and the null hypothesis was rejected only if the T value was less than or equal to 2 (the critical value).

AgriEngineering 2025, 7, 353 25 of 30


> **Figure 12. Radar charts comparing AgroVisionNet and state-of-the-art algorithms across multiple**

> datasets.


> **Table 9 presents the significance test results based on comparing the accuracy of each**

> model. It presents the significant test results for the average accuracy of AgroVisionNet
compared to ResNet-50, and for AgroVisionNet compared to EfficientNet-B0, Vision Trans-
former (ViT), Graph Neural Network (GNN), YOLOv9, Mask R-CNN, Hybrid CNN-RNN,
ConvLSTM, and MSG-GCN. In the case of AgroVisionNet vs. all compared methods,
AgroVisionNet is better (+ve difference) than the other methods for all five datasets. After
calculating the total of +ve ranks R+ ꞓ{24, 26, 27} and the total −ve ranks R−= 0, we can
conclude that AgroVisionNet can statistically outperform all other methods as T = min
{R+, R−} = 0 < 2. The T values generally show that our proposed method can statistically

outperform the compared methods according to the average accuracy values. In addition, it can be noted from Table 9 that the PlantVillage dataset was placed in the first rank five times and the second rank twice. Also, the EuroSAT dataset was placed in the first rank four times and the second rank three times, which means that the AgroVisionNet algorithm shows excellent performance in detection and classification of crop diseases at the leaf level (PlantVillage data), in agricultural monitoring, and in analyzing anomalies in land-cover data derived from satellite imagery (EuroSAT data).

AgriEngineering 2025, 7, 353 26 of 30


> **Table 9. The significance test results based on comparing the accuracy of the models.**

Vision Transformer

EfficientNet-B0

AgroVisionNet

Difference

Difference

Difference

ResNet-50

Rank

Rank

Rank

(ViT)

Dataset

PlantVillage 97.8 93.5 4.3 1 95.1 2.7 1 96.7 1.1 2 Agriculture-Vision 94.5 88.7 5.8 4 90.1 4.4 5 92.6 1.9 5 BigEarthNet 92.3 87.2 5.1 3 89 3.3 3 91.2 1.1 2 UAV-based Crop and Weed 91.5 85.7 5.8 4 87.9 3.6 4 90.3 1.2 4 EuroSAT 96.4 91.8 4.6 2 93.2 3.2 2 95.5 0.9 1 T = min {R+, R−} T = min{24,0} = 0 T = min{26,0} = 0 T = min{24,0} = 0

Network (GNN)

AgroVisionNet

Graph Neural

Mask R-CNN

Difference

Difference

Difference

YOLOv9

Rank

Rank

Rank

Dataset

PlantVillage 97.8 95.9 1.9 4 96.3 1.5 2 95.3 2.5 1 Agriculture-Vision 94.5 91.8 2.7 5 92 2.5 5 90.9 3.6 5 BigEarthNet 92.3 90.7 1.6 2 90.8 1.5 2 89.5 2.8 3 UAV-based Crop and Weed 91.5 89.7 1.8 3 89.8 1.7 4 88.5 3 4 EuroSAT 96.4 94.9 1.5 1 95.1 1.3 1 93.8 2.6 2 T = min {R+, R−} T = min{27,0)} = 0 T = min{24,0} = 0 T = min{26,0} = 0

Hybrid CNN-RNN

AgroVisionNet

ConvLSTM

MSG-GCN

Difference

Difference

Difference

Rank

Rank

Rank

Dataset

PlantVillage 97.8 94.6 3.2 1 94.9 2.9 1 96.1 1.7 4 Agriculture-Vision 94.5 89.5 5 5 89.8 4.7 5 92.3 2.2 5 BigEarthNet 92.3 88.4 3.9 2 88.9 3.4 2 91 1.3 2 UAV-based Crop and Weed 91.5 87.3 4.2 4 87.6 3.9 4 90 1.5 3 EuroSAT 96.4 92.5 3.9 3 92.9 3.5 3 95.3 1.1 1 T = min {R+, R−} T = min{26,0} = 0 T = min{26,0} = 0 T = min{27,0)} = 0


> **Table 10 shows the significance test results for the average F1-Score for AgroVisionNet**

> vs. ResNet-50, and for AgroVisionNet vs. EfficientNet-B0, Vision Transformer (ViT), Graph
Neural Network (GNN), YOLOv9, Mask R-CNN, Hybrid CNN-RNN, ConvLSTM, and
MSG-GCN. In the case of AgroVisionNet vs. all compared methods, AgroVisionNet is
better (+ve difference) than the other methods for all five datasets. After calculating the
total +ve ranks R+ ꞓ[6.2: 27.8] and the total −ve ranks R−= 0, we can conclude that
AgroVisionNet can statistically outperform all other methods as T = min {R+, R−} = 0 < 2.
The T values generally show that our proposed method can statistically outperform the
compared methods according to the average F1-Score values. In addition, it can be noted
from Table 10 that the PlantVillage dataset was placed in the first rank five times and the
second rank three times. Also, the EuroSAT dataset was placed in the first rank five times

AgriEngineering 2025, 7, 353 27 of 30

and the second rank twice, which means that the AgroVisionNet algorithm shows excellent performance in detection and classification of crop diseases at the leaf level (PlantVillage data), in agricultural monitoring, and in analyzing anomalies in land-cover data derived from satellite imagery (EuroSAT data).


> **Table 10. The significance test results based on comparing the F1-Scores of the models.**

Vision Transformer

EfficientNet-B0

AgroVisionNet

Difference

Difference

Difference

ResNet-50

Rank

Rank

Rank

(ViT)

Dataset

PlantVillage 97.8 93.2 4.6 1 94.7 3.1 1 96.8 1 2 Agriculture-Vision 94.5 88.4 6.1 4 89.9 4.6 5 92.6 1.9 5 BigEarthNet 92.3 86.7 5.6 3 88.5 3.8 3 91.1 1.2 4 UAV-based Crop and Weed 91.6 85.2 6.4 5 87.4 4.2 4 90.4 1.2 3 EuroSAT 96.5 91.4 5.1 2 92.9 3.6 2 95.6 0.9 1 T = min {R+, R−} T = min{27.8,0} = 0 T = min{19.3,0} = 0 T = min{6.2,0} = 0

Network (GNN)

AgroVisionNet

Graph Neural

Mask R-CNN

Difference

Difference

Difference

YOLOv9

Rank

Rank

Rank

Dataset

PlantVillage 97.8 96.2 1.6 2 96.1 1.7 2 94.7 3.1 1 Agriculture-Vision 94.5 91.9 2.6 5 92 2.5 5 90.8 3.7 5 BigEarthNet 92.3 90.7 1.6 2 90.6 1.7 2 89.2 3.1 1 UAV-based Crop and Weed 91.6 89.8 1.8 4 89.6 2 4 88.2 3.4 4 EuroSAT 96.5 95 1.5 1 94.9 1.6 1 93.4 3.1 1 T = min {R+, R−} T = min{9.1,0)} = 0 T = min{9.5,0} = 0 T = min{16.4,0} = 0

Hybrid CNN-RNN

AgroVisionNet

ConvLSTM

MSG-GCN

Difference

Difference

Difference

Rank

Rank

Rank

Dataset

PlantVillage 97.8 94.2 3.6 1 94.6 3.2 1 96.4 1.4 4 Agriculture-Vision 94.5 89 5.5 5 89.3 5.2 5 92.5 2 5 BigEarthNet 92.3 87.9 4.4 2 88.5 3.8 2 91 1.3 2 UAV-based Crop and Weed 91.6 86.8 4.8 4 87.1 4.5 4 90.3 1.3 2 EuroSAT 96.5 92 4.5 3 92.5 4 3 95.4 1.1 1 T = min {R+, R−} T = min{22.8,0} = 0 T = min{20.7,0} = 0 T = min{7.1,0)} = 0


> **Table 11 provides a comparative analysis of computational complexity for the pro-**

> posed AgroVisionNet framework against several state-of-the-art baselines. The model
integrates CNN, ViT, and GNN modules, which naturally increase the number of trainable
parameters and floating-point operations (FLOPs). While AgroVisionNet exhibits approxi-
mately 1.7× higher FLOPs than a standard ViT model, it delivers a 3–5% improvement in
accuracy and IoU across all benchmark datasets. This trade-off underscores the model’s
effectiveness in capturing both local spatial textures (via CNN) and global contextual

AgriEngineering 2025, 7, 353 28 of 30

dependencies (via ViT and GNN). In terms of inference latency, AgroVisionNet requires an average of 18.5 ms per image, which remains suitable for near-real-time agricultural applica- tions such as UAV-based crop inspection and precision spraying. Moreover, the framework can be optimized through quantization, pruning, and knowledge distillation, reducing its size by up to 40% without significant accuracy loss. Hence, despite its computational intensity, AgroVisionNet maintains feasible deployment characteristics for edge-AI and embedded systems (e.g., NVIDIA Jetson, Coral TPU), ensuring scalability from laboratory experiments to real-world field operations.


> **Table 11. Computational complexity comparison of AgroVisionNet and baseline models.**

(M) FLOPs (G) Inference Time (ms)

Model Size

Model Parameters

(MB)

ResNet-50 25 3.8 12.4 98 EfficientNet-B0 7 1.6 8.1 25 Vision Transformer

(ViT-B/16) 86 17.6 15.0 345

MSG-GCN 12 2.3 13.2 130 AgroVisionNet

(Proposed) 115 22.0 18.5 440


## 7. Conclusions

In this study, we introduced AgroVisionNet, a hybrid deep learning framework that integrates CNNs for local feature extraction, Vision Transformers for global contextual learn- ing, and Graph Neural Networks for relational modeling of image regions. Evaluations across five diverse benchmark datasets—PlantVillage, Agriculture-Vision, BigEarthNet, UAV Crop and Weed, and EuroSAT—demonstrated that AgroVisionNet consistently out- performs strong baselines such as ResNet-50, EfficientNet-B0, ViT, and Mask R-CNN. The model achieved state-of-the-art accuracy and robustness, with significant gains in complex tasks such as anomaly segmentation and weed detection, thereby advancing the state of precision agriculture and food security applications.

While the results validate the effectiveness of AgroVisionNet, several limitations must be acknowledged. First, the integration of three deep learning components inevitably increases computational overhead, which may limit real-time deployment on resource- constrained platforms. Although our framework shows strong performance, the marginal gains over simpler architectures (e.g., pure ViT in some tasks) highlight a trade-off between accuracy and computational cost. Second, the datasets used, though diverse, may not fully capture the variability of real-world farming conditions, and dataset bias remains a concern, particularly when extending models across geographies or sensor types. Third, our experiments focused primarily on image-based data; the integration of multi-sensor inputs (e.g., hyperspectral, soil, or weather sensors), and robustness against sensor noise, occlusion, or hardware failures remains an open challenge. Finally, while we provided evidence of improvements in accuracy, future work should explore explainability outputs more extensively to ensure trustworthiness and actionable decision support for farmers.

In future research, we aim to (1) optimize AgroVisionNet for edge deployment through model compression techniques such as pruning, quantization, and knowledge distillation, (2) extend the framework toward multi-modal fusion with heterogeneous sensor data, and (3) perform robustness testing under realistic environmental conditions. Addressing these aspects will further enhance the practical value and sustainability of AgroVisionNet, making it more suitable for widespread deployment in precision agriculture.

AgriEngineering 2025, 7, 353 29 of 30

Author Contributions: Conceptualization, methodology, software, E.A.M.; validation, A.S.D.; formal analysis, E.A.M.; investigation, A.S.D.; resources, M.A.C.; data curation, E.A.M.; writing—original draft preparation, A.S.D.; writing—review and editing, M.A.C. and E.A.M.; visualization, E.A.M.; supervision, M.A.C.; project administration, M.A.C. and E.A.M.; funding acquisition, M.A.C. All authors have read and agreed to the published version of the manuscript.

Funding: This research received no external funding.

Data Availability Statement: The data presented in this research is publicly available.

Conflicts of Interest: The authors declare no conflicts of interest.


## References

1. FAO. The State of Food and Agriculture. 2021. Available online: https://www.fao.org/publications/fao-flagship-publications/ the-state-of-food-and-agriculture/en (accessed on 24 January 2025). 2. Tilman, D.; Balzer, C.; Hill, J.; Befort, B.L. Global food demand and the sustainable intensification of agriculture. Proc. Natl. Acad. Sci. USA 2011, 108, 20260–20264. [CrossRef] 3. Oerke, E.-C. Crop losses to pests. J. Agric. Sci. 2006, 144, 31–43. [CrossRef] 4. Kamilaris, A.; Prenafeta-Boldú, F.X. Deep learning in agriculture: A survey. Comput. Electron. Agric. 2018, 147, 70–90. [CrossRef] 5. El Sakka, M.; Mothe, J.; Ivanovici, M. Images and CNN applications in smart agriculture. Eur. J. Remote Sens. 2024, 57, 2352386. [CrossRef] 6. Chiu, M.T.; Xu, X.; Wei, Y.; Huang, Z.; Schwing, A.G.; Brunner, R. Agriculture-Vision: A Large Aerial Image Database for Agricultural Pattern Analysis. In Proceedings of the 2020 IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR), Seattle, WA, USA, 13–19 June 2020; pp. 2825–2835. [CrossRef] 7. Atapattu, J.A.; Perera, L.K.; Nuwarapaksha, T.D.; Udumann, S.S.; Dissanayaka, N.S. Challenges in Achieving Artificial Intelligence in Agriculture. In Artificial Intelligence Techniques in Smart Agriculture; Springer: Singapore, 2024; pp. 7–34. [CrossRef] 8. Dosovitskiy, A.; Beyer, L.; Kolesnikov, A.; Weissenborn, D.; Zhai, X.; Unterthiner, T.; Dehghani, M.; Minderer, M.; Heigold, G.; Gelly, S.; et al. An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale. arXiv 2021, arXiv:2010.11929v2. [CrossRef] 9. Singla, A.; Nehra, A.; Joshi, K.; Kumar, A.; Tuteja, N.; Varshney, R.K.; Gill, S.S.; Gill, R. Exploration of machine learning approaches for automated crop disease detection. Curr. Plant Biol. 2024, 40, 100382. [CrossRef] 10. Adão, T.; Hruška, J.; Pádua, L.; Bessa, J.; Peres, E.; Morais, R.; Sousa, J.J. Hyperspectral Imaging: A Review on UAV-Based Sensors, Data Processing and Applications for Agriculture and Forestry. Remote Sens. 2017, 9, 1110. [CrossRef] 11. Gupta, B.; Kanmani, S.; E, E.; Sah, S.; Mohanty, S.N.; B, S. An Enhanced Deep Learning approach for crop health monitoring and disease prediction. Research Square 2024. [CrossRef] 12. Lei, L.; Yang, Q.; Yang, L.; Shen, T.; Wang, R.; Fu, C. Deep learning implementation of image segmentation in agricultural applications: A comprehensive review. Artif. Intell. Rev. 2024, 57, 149. [CrossRef] 13. Yu, F.; Wang, M.; Xiao, J.; Zhang, Q.; Zhang, J.; Liu, X.; Ping, Y.; Luan, R. Advancements in Utilizing Image-Analysis Technology for Crop-Yield Estimation. Remote Sens. 2024, 16, 1003. [CrossRef] 14. Li, K.-Y.; Sampaio de Lima, R.; Burnside, N.G.; Vahtmäe, E.; Kutser, T.; Sepp, K.; Cabral Pinheiro, V.H.; Yang, M.-D.; Vain, A.; Sepp, K. Toward Automated Machine Learning-Based Hyperspectral Image Analysis in Crop Yield and Biomass Estimation. Remote Sens. 2022, 14, 1114. [CrossRef] 15. Zeng, Z.; Mahmood, T.; Wang, Y.; Rehman, A.; Mujahid, M.A. AI-driven smart agriculture using hybrid transformer-CNN for real time disease detection in sustainable farming. Sci. Rep. 2025, 15, 25408. [CrossRef] [PubMed] 16. Raman, R.; Jayaraman, S. Artificial intelligence for sustainable farming with dual branch convolutional graph attention networks in rice leaf disease detection. Sci. Rep. 2025, 15, 10595. [CrossRef] [PubMed] 17. Butt, M.H.F.; Li, J.P.; Ahmad, M.; Butt, M.A.F. Graph-infused hybrid vision transformer: Advancing GeoAI for enhanced land cover classification. Int. J. Appl. Earth Obs. Geoinf. 2024, 129, 103773. [CrossRef] 18. Emelyanov, V.A.; Knyaz, V.A.; Kniaz, V.V.; Zheltov, S.Y. Aerial Images Segmentation with Graph Neural Network. ISPRS Ann. Photogramm. Remote Sens. Spatial Inf. Sci. 2024, X-2/W1-2024, 1–8. [CrossRef] 19. Guo, X.; Feng, Q.; Guo, F. CMTNet: A hybrid CNN-transformer network for UAV-based hyperspectral crop classification in precision agriculture. Sci. Rep. 2025, 15, 12383. [CrossRef] 20. Yang, J.; Wan, H.; Shang, Z. Enhanced hybrid CNN and transformer network for remote sensing image change detection. Sci. Rep 2025, 15, 10161. [CrossRef] 21. Jahin, M.A.; Shahriar, S.; Mridha, M.F.; Hossen, M.J.; Dey, N. Soybean Disease Detection via Interpretable Hybrid CNN-GNN: Integrating MobileNetV2 and GraphSAGE with Cross-Modal Attention. arXiv 2025. [CrossRef]

AgriEngineering 2025, 7, 353 30 of 30

22. Mohanty, S.P.; Hughes, D.P.; Salathé, M. Using Deep Learning for Image-Based Plant Disease Detection. Front. Plant Sci. 2016, 7, 1419. [CrossRef] 23. Chitta, S.; Yandrapalli, V.K.; Sharma, S. Advancing Histopathological Image Analysis: A Combined EfficientNetB7 and ViT-S16 Model for Precise Breast Cancer Detection. In Proceedings of the 2024 OPJU International Technology Conference (OTCON) on Smart Computing for Innovation and Advancement in Industry 4.0, Raigarh, India, 5–7 June 2024; pp. 1–6. [CrossRef] 24. Dewangan, O.; Vij, P. CNN-LSTM framework to automatically detect anomalies in farmland using aerial images from UAVs. BIO Web Conf. 2024, 82, 05015. [CrossRef] 25. Li, X.; Xiang, Y.; Li, S. Combining convolutional and vision transformer structures for sheep face recognition. Comput. Electron. Agric. 2023, 205, 107651. [CrossRef] 26. Salcedo, E. Computer Vision-Based Gait Recognition on the Edge: A Survey on Feature Representations, Models, and Architec- tures. J. Imaging 2024, 10, 326. [CrossRef] [PubMed] 27. Borisov, V.; Leemann, T.; Seßler, K.; Haug, J.; Pawelczyk, M.; Kasneci, G. Deep Neural Networks and Tabular Data: A Survey. IEEE Trans. Neural Netw. Learn. Syst. 2024, 35, 7499–7519. [CrossRef] [PubMed] 28. Dhal, S.B.; Kar, D. Transforming Agricultural Productivity with AI-Driven Forecasting: Innovations in Food Security and Supply Chain Optimization. Forecasting 2024, 6, 925–951. [CrossRef] 29. Clasen, K.N.; Hackel, L.; Burgert, T.; Sumbul, G.; Demir, B.; Markl, V. reBEN: Refined BigEarthNet Dataset for Remote Sensing Image Analysis. arXiv 2024, arXiv:2407.03653. 30. Steininger, D.; Trondl, A.; Croonen, G.; Simon, J.; Widhalm, V. The CropAndWeed Dataset: A Multi-Modal Learning Approach for Efficient Crop and Weed Manipulation. In Proceedings of the 2023 IEEE/CVF Winter Conference on Applications of Computer Vision (WACV), Waikoloa, HI, USA, 2–7 January 2023; pp. 3718–3727. 31. Helber, P.; Bischke, B.; Dengel, A.; Borth, D. EuroSAT: A Novel Dataset and Deep Learning Benchmark for Land Use and Land Cover Classification. IEEE J. Sel. Top. Appl. Earth Obs. Remote Sens. 2019, 12, 2217–2226. [CrossRef] 32. Mahareek, A.; Elsaid, E.K.; El-Desouky, N.M.; El-Dahshan, K.A. Survey: Anomaly Detection in Surveillance Videos. Int. J. Theor. Appl. Res. 2024, 3, 328–342. [CrossRef] 33. Hanley, J.A.; McNeil, B.J. The meaning and use of the area under a receiver operating characteristic (ROC) curve. Radiology 1982, 143, 29–36. [CrossRef] 34. Everingham, M.; Van Gool, L.; Williams, C.K.I.; Winn, J.; Zisserman, A. The pascal visual object classes (VOC) challenge. Int. J. Comput. Vis. 2010, 88, 303–338. [CrossRef]

Disclaimer/Publisher’s Note: The statements, opinions and data contained in all publications are solely those of the individual author(s) and contributor(s) and not of MDPI and/or the editor(s). MDPI and/or the editor(s) disclaim responsibility for any injury to people or property resulting from any ideas, methods, instructions or products referred to in the content.
