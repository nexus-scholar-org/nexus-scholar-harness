---
workspace_id: SCI-000852
doi: 10.1109/jstars.2025.3536175
title: 'SqueezeSlimU-Net: An Adaptive and Efficient Segmentation Architecture for
  Real-Time UAV Weed Detection'
authors:
- family_name: Machidon
  given_name: Alina L.
  orcid: https://orcid.org/0000-0002-9330-3865
- family_name: "Kra\u0161ovec"
  given_name: "Andra\u017E"
  orcid: https://orcid.org/0009-0007-4077-0826
- family_name: "Pejovi\u0107"
  given_name: Veljko
  orcid: https://orcid.org/0000-0002-9009-0024
- family_name: Machidon
  given_name: Octavian
  orcid: https://orcid.org/0000-0003-3133-1008
year: 2025
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:41.179353+00:00'
---

# SqueezeSlimU-Net: An Adaptive and Efficient Segmentation Architecture for Real-Time UAV Weed Detection

IEEE JOURNAL OF SELECTED TOPICS IN APPLIED EARTH OBSERVATIONS AND REMOTE SENSING, VOL. 18, 2025 5749

SqueezeSlimU-Net: An Adaptive and Efﬁcient

Segmentation Architecture for Real-Time

UAV Weed Detection

Alina L. Machidon , Andraž Krašovec , Veljko Pejovi´c , and Octavian M. Machidon

I. INTRODUCTION U


## Abstract—The limited processing capacity of computing equip-

ment that is usually mounted on unmanned aerial vehicles (UAVs)
often prevents real-time execution of computer vision tasks, such
as image segmentation. In this article, we introduce SqueezeSlimU-
Net (SSU-Net), an adaptive and efﬁcient deep learning (DL) model
designed to enhance UAV capabilities in performing complex image
segmentation tasks under resource constraints, thereby advancing
real-time UAV vision—a crucial technology in ﬁelds, such as preci-
sion agriculture. SSU-Net combines beneﬁts of three specialized
DL architectures: the semantic segmentation capabilities of the
U-Net architecture, the computational efﬁciency of SqueezeNet’s
ﬁre modules, and the dynamic adaptability of slimmable neural
networks. This integration allows SSU-Net to adjust its network
width in real-time, thus striking the balance between inference
accuracy and computational load based on the operational pa-
rameters such as task requirements and UAV’s battery life. To
validate SSU-Net’s efﬁcacy, we applied it to a weed detection task
using two UAV-collected datasets and tested it on an edge comput-
ing platform for UAVs. Our experiments show that SSU-Net can
reduce inference energy consumption by up to 65% with only a
minimal 2% reduction in accuracy. A comparative evaluation with
other state-of-the-art DL image segmentation approaches shows
that SSU-Net achieves on par weed detection performance while
requiring signiﬁcantly fewer model parameters. In addition, SSU-
Net outperforms state-of-the-art network pruning techniques in
balancing accuracy and resource usage. Timing benchmarks show
SSU-Net fostering real-time weed detection even on low-resource
UAVs, making it ideal for UAV remote sensing applications.

NMANNED aerial vehicles (UAVs) have a wide range of remote sensing applications in ﬁelds, such as environmen- tal monitoring, disaster management, infrastructure inspection, and precision agriculture. In agriculture, in particular, the use of UAVs is rapidly expanding, driven by decreasing costs in aerospace engineering and sensor technology. In this domain, UAVs can be harnessed for aerial crop inspection and crop health monitoring, yield estimation, and pest and disease detection, among others [1], [2]. UAV computer vision can provide imme- diate visual information about large crop areas, thus enabling faster decision-making for farmers and leading to more efﬁcient land usage planning.

In UAV remote sensing applications, particularly relevant is the detection and discrimination in images of objects of interest fromthebackground,suchasrecognizingbuildings,crops,trees, or vehicles. This recognition is usually accomplished through semantic segmentation, which has replaced traditional manual observation and measurement. For instance, in precision agri- culture, computer vision segmentation techniques are used to perform crop detection and mass estimation [3], to discern be- tween crops and weeds in a given ﬁeld [4], to detect diseases [5], or to compute a crop canopy cover and monitor crop growth [6].

Nevertheless, the further advance of UAV remote sensing in agriculture is critically threatened by the limited computing and energy resources that can be mounted on a UAV. Due to the mismatch between the computational requirements of state-of- the-art computer vision techniques and capabilities of on-board computers, presently UAVs serve merely as remote cameras that ofﬂoad the collected data to static servers for processing. Such a distributed pipeline incurs severe delays and limits the possibilities for advanced UAV-based solutions in agriculture. For instance, nowadays, a solution for weed detection and exter- mination would require that a UAV conducts a prescribed ﬂight to collect images of a ﬁeld. Once the ﬂight is completed, images would be transferred, often manually, to a centralized server, wheretheimageswouldbepreprocessedandweedsidentiﬁedby a large machine learning model. The segmented images would then have to be tied with particular geographic coordinates, so that the images can be further used to guide the weed removal process.

Index Terms—Adaptive neural networks, computational efﬁ- ciency, image segmentation, precision agriculture, real-time unmanned aerial vehicle (UAV) vision, weed detection.

Received 18 October 2024; revised 16 December 2024; accepted 14 January 2025. Date of publication 29 January 2025; date of current version 21 February 2025. This work was supported in part by the “Context-Aware On-Device Ap- proximate Computing” under Grant J2-3047, in part by the Slovenian Research Agency research core under Grant P2-0098 and Grant P2-0426, and in part by the H2020 Smart4All 3rd FTTE grant “AgriAdapt.” (Corresponding author: Alina L. Machidon.)

Alina L. Machidon, Andraž Krašovec, and Octavian M. Machidon are with the Faculty of Computer and Information Science, University of Ljubljana, 1000 Ljubljana, Slovenia (e-mail: alina.machidon@fri.uni-lj.si; ak6688@student.uni-lj.si; octavian.machidon@fri.uni-lj.si).

Veljko Pejovi´c is with the Faculty of Computer and Information Science, University of Ljubljana, 1000 Ljubljana, Slovenia, and also with the Computer Systems Department, Institute Jožef Stefan, 1000 Ljubljana, Slovenia (e-mail: veljko.pejovic@fri.uni-lj.si).

The above-mentioned solution would usually take days be- tween the initial ﬂight and the weed removal. A key reason why

Digital Object Identiﬁer 10.1109/JSTARS.2025.3536175

© 2025 The Authors. This work is licensed under a Creative Commons Attribution 4.0 License. For more information, see

https://creativecommons.org/licenses/by/4.0/

5750 IEEE JOURNAL OF SELECTED TOPICS IN APPLIED EARTH OBSERVATIONS AND REMOTE SENSING, VOL. 18, 2025

an agile solution, where a UAV automatically detects weeds and takes an appropriate action, is not possible in the contemporary UAV-computing landscape lies in the inability of computing platforms deployed on UAVs to execute sophisticated deep learning (DL) models in real time. Enabling such execution would allow immediate data-driven decisions to be made di- rectly on a UAV. This capability could signiﬁcantly enhance applications, such as real-time monitoring of environmental changes, rapid disaster response, and efﬁcient precision farming.

brought by real-time computer vision. SSU-Net, which we de- velop in this article, is a step toward enabling real-time execution of computer vision tasks in low-resource environments. To fa- cilitate further research in this domain, we release the developed source code in a publicly accessible repository.1

II. BACKGROUND AND RELATED WORK

Computer vision processing pipelines commonly rely on resource-intensive DL models [10], unsuitable for deployment on UAVs which are typically characterized by limited resources, such as weak CPUs/GPUs, or even a complete absence of GPUs due to cost, size, and power constraints. This mismatch between the computational demands of computer vision models and the resource limitations of these hardware devices creates a perfor- mance bottleneck, hindering real-time execution of image seg- mentation or object detection applications [11]. Consequently, there is a necessity for innovative approaches that bridge the gap between the complex demands of image segmentation and the constrained resources of onboard UAV computing systems.

In this work we enable efﬁcient real-time execution of DL models on resource-constrained UAVs through a novel neu- ral network architecture termed SqueezeSlimU-Net (SSU-Net). SSU-Net leverages the strengths of the U-Net architecture [7], renowned for its success in semantic segmentation, incorporates the computational efﬁciency of SqueezeNet’s ﬁre modules [8], along with the dynamic adaptability of slimmable neural net- works (SNNs) [9]. This combination allows SSU-Net to adjust its network width in real-time, optimizing the balance between inference accuracy and computational load based on the UAV’s operational parameters such as task requirements, processing power, and battery life. We proceed to train SSU-Net for a weed recognition task on aerial images and implement our solution on an actual UAV-ready computing hardware. We then conduct extensive experiments to evaluate the network’s ability to dy- namically trade the accuracy of weed detection for energy sav- ings and show that SSU-Net enables signiﬁcantly more efﬁcient operation, without sacriﬁcing inference quality, compared to the conventional network compression methods, such as parameter pruning. Finally, we demonstrate that, compared to regular U-Net, SSU-Net achieves an order of magnitude improvement in processing speed, thus enabling real-time computer vision on-board UAVs.

A. Lightweight Architectures for UAVs

Specialized architectures tailored to low-resource settings are one way of bringing real-time DL execution to constrained de- vices. Lightweight network architectures have been proposed for UAV-based computer vision tasks, for instance in [12], where the authors experiment with lightweight convolutional neural net- works (CNNs), such as MobileNet and EfﬁcientNet, as the back- bone for the segmentation pipeline for real-time ﬂood detection using image segmentation on UAVs. Jiang et al. [13] proposed a lightweight detection model with a MobileNet-v2 backbone for real-time damage detection and localization, achieving fast inference speeds onboard UAVs. Wang et al. [14] also designed a lightweight, improved version of YOLOv5 that incorporates a residual dilated convolution module, a feature fusion module, and a double-head method that integrates fully connected and convolutional heads for efﬁcient real-time damage detection from UAV images. Similarly, Yang et al. [15] introduced the con- text aggregation network, a dual-branch CNN, where one of the branches relies on MobileNet, offering lower computational cost and competitive accuracy, which was subsequently validated in real-time segmentation tasks (road infrastructure monitoring) on-board a UAV [16]. In the ﬁeld of real-time object detection onboard UAVs, Bowman et al. [17] explored several DL variants for energy infrastructure damage assessment, demonstrating successful onboard deployment. Wang et al. [18] proposed an uncertainty-guided fusion network for RGB-Thermal semantic segmentation, achieving robust performance in diverse real-time UAV scenarios. Similarly, DF2Net [19] introduced a differential feature fusion strategy for hyperspectral image classiﬁcation, with potential applications in UAV-based multimodal segmen- tation tasks. Custom lightweight segmentation models have also been developed, yet, they often target very speciﬁc tasks, such as cloud detection [20], and, to the best of our knowledge, have not been demonstrated on UAVs.

The speciﬁc contributions of our work are as follows. 1) We propose SSU-Net, a novel architecture optimized for real-time image segmentation on resource-constrained UAV platforms, enabling efﬁcient execution of complex computer vision tasks. 2) Through extensive experiments on two UAV-collected datasets and an edge computing platform, we demonstrate that SSU-Net reduces inference energy consumption by up to 65% with only a minimal 3% reduction in IoU, outper- forming pruning-based methods with higher accuracy and lower energy consumption. 3) We demonstrate that SSU-Net supports a dynamic trade- off between resource usage and inference accuracy, enabling ﬂexible adaptation to the operational condi- tions of UAVs. We validate this through runtime eval- uations, showcasing adaptability in real-world dynamic scenarios. 4) We show that SSU-Net outperforms pruning-based meth- ods and achieves comparable performance to state-of-the- art image segmentation models, while using signiﬁcantly fewer parameters, making it ideal for resource-constrained environments. Advances in computer vision have largely remained out of reach of resource-constrained devices, such as UAVs. Yet, such devices are poised to beneﬁt the most from situational awareness

1[Online]. Available: https://gitlab.fri.uni-lj.si/lrk/agriadapt/

MACHIDON et al.: SQUEEZESLIMU-NET: AN ADAPTIVE AND EFFICIENT SEGMENTATION ARCHITECTURE 5751

B. DL Compression Techniques for UAVs

DL network compression techniques are another approach to signiﬁcantly reduce the computational burden of efﬁciently runningamodelonboardaUAV.Forexample,anetworkpruning approach originally proposed in [21], was validated in UAV on-board processing experiments for real-time forest ﬁre and ﬂood monitoring by Lee et al. [22]. Likewise, Kraft et al. [23] experimented with various quantization levels for real-time on- board UAV trash detection. Sharing weights across layers of a network is another means of compressing the model, and Ming et al. [24] proposed a lightweight network for crop spike head detection that incorporates a lightweight parameter sharing detection head, which reduces the model’s parameter count by sharing weights across convolutional layers, to ensure suitability for UAVs with limited computational resources. Knowledge distillation, another popular model compression technique that relies on a larger teacher model training a smaller student model, was applied in [25] for vehicle detection and road segmentation in UAV aerial imagery. The authors introduced a multitask model incorporating lightweight ghost-dilated convolution and the ghost-atrous spatial pyramid pooling module to reduce the model parameter count and accelerate inference.

Fig. 1. Illustration of the SNN approach, where a single model can be executed with different widths at each inference point. The widths illustrated are also the onesusedintheexperimentsdescribedinthisarticle:100%,75%,50%,and25%.

detail its building blocks and the rationale behind its design. To facilitate a comprehensive evaluation of this network, we implement an additional reference network for comparison and benchmarking: the slimmable U-Net (SU-Net). While the SU- Net lacks the squeezed implementation, it still beneﬁts from a slimmable architecture compared to traditional U-Nets. Conse- quently, the SU-Net should offer higher baseline performance than the SSU-Net at the cost of increased computational de- mands. Both the SSU-Net and SU-Net are implemented using the PyTorch DL framework. For a broader comparison, we also include additional state-of the-art segmentation neural network models and also an alternative neural network compression technique: network pruning. Thus, we implement and include for comparison two other DL models and also two pruned implementations of the standard U-Net and squeeze U-Net architectures with the same backbones as those used for training their slimmable counterparts.

C. Limitations of Existing Approaches

While the above-mentioned solutions achieve real-time exe- cution on UAVs, they often exhibit serious limitations. Most im- portantly, both specialized architectures and compressed mod- els enable only a ﬁxed tradeoff between inference accuracy and computational efﬁciency. Consequently, their performance cannot be readily adjusted based on varying contextual factors, such as lighting conditions, available resources, or speciﬁc task requirements. In real-world scenarios, however, a UAV would experience various situations, even during a single ﬂight. Thus, a model that could dynamically adapt its inference power and resource usage, would be able to better align with the operat- ing conditions, for instance, the battery level, the input image difﬁculty, and other factors.

1) SNN Primer: We base our implementation of the neural network architectures on the SNN [9] approach, a technique for reducing the computation of a neural network by enabling inference to be executed at different widths, trading off between accuracy and latency on the ﬂy (an illustration of this approach is provided in Fig. 1). SNNs robust training procedure enables executions at different widths by employing switchable batch normalization (BN) layers. The switchable BN privatizes all the BN layers for each network width by independently normalizing the feature mean and variance during testing and independently accumulating feature statistics for each network width. This enables efﬁcient training of different network widths by mit- igating the inconsistency generated by different numbers of input channels in layers, which result in different means and variances.

In this article, we propose SSU-Net, a novel approach that addresses the limitations of previous research by training and deploying a single dynamically adaptable neural network model on a UAV’s computing system. Our model architecture can vary the number of network’s parameters at runtime, thus allowing the network to optimize the tradeoff between accuracy and computational load based on the UAV’s operational parameters. This results in multiple adjustable points on the energy con- sumption/inference time versus inference performance tradeoff curve. Consequently, SSU-Net can signiﬁcantly reduce energy consumption while maintaining high segmentation accuracy, making it ideal for a wide range of UAV-based precision agri- culture tasks.

To develop SSU-Net, we follow the standard SNN training pipeline, repeatedly performing a forward and backward pass of batches of data to optimize the model parameters for the presented task. Every minibatch of training data is used for all separate network widths deﬁned by the slimmable architecture. Fortheexperimentsdescribedinthisarticle,allslimmableneural network architectures were trained using the following set of widths: 100%, 75%, 50%, and 25%.

2) Squeeze U-Net Primer: The U-Net [7] is one of the most popular DL architecture for image segmentation tasks. The architecture utilizes a fully convolutional network (FCN) that combines down/upsampled paths with feature map concatena- tion, enabling accurate pixelwise segmentation. However, U-Net may incur a signiﬁcant computational burden, especially when ran on low-resource devices, such as UAVs (more details in Section IV-C2).

III. METHODS AND MATERIALS

A. Toward Adaptable and Efﬁcient on-UAV DL Models

This section delves into the core of our contribution: the squeeze slimmable U-Net (SSU-Net) architecture. We will next

5752 IEEE JOURNAL OF SELECTED TOPICS IN APPLIED EARTH OBSERVATIONS AND REMOTE SENSING, VOL. 18, 2025

TABLE I INNER LAYERS OF A FIREMODULE IN SSU-NET

TABLE II SSU-NET BACKBONE NETWORK ARCHITECTURE

The squeeze U-Net [8] is an adaptation of the traditional U-Net which incorporates the SqueezeNet ﬁre modules [26]. These modules rely on the following innovations to replace the standard convolutional layers in the U-Net. i) Pointwise convo- lution, which signiﬁcantly reduces the number of 1 × 1 ﬁlters compared to a traditional U-Net convolution, and ii) inception layer with mixed ﬁlters, as this layer performs two parallel convolutions, one with 1 × 1 ﬁlters and another with 3 × 3 ﬁlters, further reducing computational cost while maintaining feature extraction capabilities.

By incorporating ﬁre modules, squeeze U-Net achieves a sig- niﬁcant reduction in model size and computational requirements compared to the original U-Net architecture. Nevertheless, with- out a dynamic adjustment capability it is still subject to a static tradeoff between resource consumption and performance.

ﬁre module. Finally, the network employs upsampling, concate- nation, and convolution layers to generate the ﬁnal segmentation mask. A detailed illustration of the SSU-Net architecture and its contracting and expansive paths is provided in Fig. 2.

3) SSU-Net: To achieve real-time adaptive image segmen- tation on UAVs, which typically carry resource-constrained computing hardware, we design the SSU-Net. Our proposed ar- chitecture enhances the computational efﬁciency of the Squeeze U-Net architecture within the dynamic adaptation capabilities of slimmable neural networks.

IV. EXPERIMENTS

A. Experimental Setup

We proceed in implementing the SSU-Net through a two-step process; ﬁrst, we replace the standard convolutional layers in both the contracting and expansive paths of the U-Net with slimmable ﬁre modules (SFMs). Each SFM, as detailed in Table I, consists of a squeeze layer and an expand layer. The squeeze layer employs a SlimmableConv2d operation that re- duces the number of input channels, thereby lowering computa- tional load. This is followed by a SwitchableBatchNorm2d layer to ensure normalized feature outputs across different widths. The expand layer then utilizes two parallel SlimmableConv2d operations—one with 1 × 1 ﬁlters (conv_left) and the other with 3 × 3 ﬁlters (conv_right)—to restore the spatial dimensionality while maintaining a manageable number of parameters. This dual-path approach allows the network to capture both local and contextual information efﬁciently. Second, we replace the remaining convolutional, BN, and transposed convolution layers with their slimmable variants. This enhancement empowers the SSU-Net to dynamically adjust its network width during runtime across all layers, optimizing the balance between computational efﬁciency and segmentation accuracy based on the contextual demands.

1) Datasets: We evaluate the performance of the SSU-Net on a weed detection task using real-world UAV imagery from two publicly available datasets: the AgriAdapt weed detection dataset [27] and the Tobacco Aerial Dataset [28]. Weed detection is a notoriously challenging task as it involves recognizing small objects (weeds) that provide limited visual information and are highly vulnerable to noise and background interference, which diminishes the network’s ability to capture discriminative information [29].

The AgriAdapt Weed Detection dataset [27] was captured in Rome, Italy, during Autumn 2023 using a custom-built hex- acopter UAV. The UAV weighed up to 6 kg and carried an NVIDIA Jetson Nano connected to an Arducam camera with a high-resolution (16MP) Sony IMX519 sensor. The camera was stabilized with a two-axis brushless gimbal. The dataset includes labels for background, salad, and weeds. For our experiments, we used the ﬁrst partition of this dataset, consisting of 497 aerial images of salad crops.

The Tobacco Aerial Dataset [28] was collected using a Mavic MinidroneovertobaccoﬁeldsinMardan,KhyberPakhtunkhwa, Pakistan in April 2021. pixels within the dataset for faster pro- cessing. Similar to the AgriAdapt dataset, the labels categorize pixels as background, crop, or weed. For our experiments, we utilize the largest partition (campaign number 2) containing 936 images. Sample labeled images from both datasets are provided in Fig. 3.

An overview of all the modules of the SSU-Net is provided in Table II. The contracting path of the SSU-Net utilizes two repetitions of two ﬁre modules, followed by a max pooling layer and four additional ﬁre modules. The expansive path consists of four upsampling layers, each followed by a concatenation with the corresponding feature map from the contracting path and a

MACHIDON et al.: SQUEEZESLIMU-NET: AN ADAPTIVE AND EFFICIENT SEGMENTATION ARCHITECTURE 5753

Fig. 2. SSU-Net architecture consists of slimmable downsampling units (SDS) in the contracting path and slimmable upsampling units (SUS) in the expansive path. Each SDS unit incorporates two SFMs to extract features, with extracted features being passed down to the next SDS unit and corresponding SUS unit. Each SUS unit consists of a Slimmable Conv Transpose2d layer and an SFM, which up-samples input, extracts features, and concatenates them to construct the output.

Fig. 3. Sample images from both datasets used in the experiments, with the weeds segmentation mask overlay (red rectangles). (a) AgriAdapt dataset. (b) Tobacco dataset.

2) ModelsUnderTest: WecomparetheperformanceofSSU- Netwithseveralcompetitiveandintuitivealternativesasfollows.

hardware during inference. This approach ensures that both SSU-Net and SU-Net are well-suited for deployment on resource-constrained devices, while still providing a robust framework for performance comparison. 2) Prunned networks, which harness a popular method for reducing a network’s size and computational demands during inferenceby systematically removing parameters (weights and biases) deemed less important for the net- work’s performance. Pruning strategies typically involve assigning scores to each parameter, often based on their magnitude, and then removing those with the lowest

1) SU-Net, which leverages the core structure of the U-Net while incorporating slimmable layers to achieve dynamic network width adjustment, thereby optimizing the balance between performance and resource consumption. This is accomplished by implementing slimmable versions of the standard convolutional and BN layers. In addition, in our implementation of the SU-Net, we opt for a single down- sampling and upsampling step within the network archi- tecture due to the computational constraints of our target

5754 IEEE JOURNAL OF SELECTED TOPICS IN APPLIED EARTH OBSERVATIONS AND REMOTE SENSING, VOL. 18, 2025

scores. However, removing parameters can degrade accu- racy, so pruned networks often require additional training or ﬁne-tuning to recover performance. For a fair compar- ison, we implemented two pruned network architectures, the pruned squeeze U-Net and the pruned U-Net, both sharing the same backbone architecture (number of layers, ﬁlter sizes, etc.) as their nonpruned counterparts. 3) State of the art segmentation models, among which FCN, Deeplab V3, LRASPP, SegNet and U-Net. 3) Model Training: We train and evaluate the SSU-Net and all reference neural network models on the previously described publicly available weed segmentation datasets (AgriAdapt weed detection and Tobacco Aerial Dataset). Both datasets include labels for background, crop, and weed. For our experiments, we focused solely on weed detection. Therefore, we merged the background and crop classes into a single class for both datasets. We employed an 80/20 train/test split on both datasets for training and evaluation. In addition, all dataset images were resampled to a uniform size of 512 × 512 pixels (other image sizes were also examined, but the size of 512 × 512 pixels was found to be optimal from both accuracy and running times).

Jetson Nano 4 GB [30] board running Ubuntu 20.04.6 LTS. This edge computing platform, along with others in the NVIDIA Jetson family, are commonly used onboard UAVs for real-time computer vision tasks. During evaluation on this platform, we used Python 3.8.10 and PyTorch 1.12.0 to execute the models. Power consumption was measured using a Monsoon power monitor tool [31], a well-established tool for embedded system power measurements [32].

To examine the quality of image segmentation achieved by the models, we calculate the intersection over union (IoU), accuracy, recall, and F1 score. The IoU, also known as the Jaccard index, is deﬁned as the intersection between the ground truth and the predicted segmentation mask, divided by the union of both:

IoU(truth,pred) = |truth ∩pred|

|truth ∪pred|. (1)

Next, accuracy, recall, and F1 score are all based on the confusion matrix, that in turn relies on the true positive (TP), false positive (FP), false negative (FN), and true negative (TN) values.

The overall accuracy (OA) accuracy measures the percentage of correctly classiﬁed pixels in the entire image dataset. It is cal- culated by dividing the total number of correctly classiﬁed pixels by the total number of pixels in the dataset. Mathematically, the formula for semantic segmentation OA is

We trained the slimmable models for a maximum of 300epochs,withearlyterminationcriteria,thatstopsthetraining if no validation accuracy improvement was observed for ﬁve consecutive epochs, to prevent overﬁtting. In both cases, we used a batch size of 8 and the Adam optimizer with an initial learning rate of 0.0001 that was exponentially decreased with a factor of 0.99, for stabilizing the training process. To address the strong unbalance between the background and weed classes, we train the networks with a weighted cross entropy loss function with weights of 0.1 and 0.9 for the background and the weeds class, respectively. We also add a L2 regularization penalty of 0.01 on the weights of the networks when computing the loss, to prevent it from overﬁtting to the majority (background) class.

OA = TP+TN TP+TN+FN+FP. (2)

Recall on the other hand focuses on the ratio of correctly predicted positives within a set of all positive values

recall = TP TP+FN. (3)

The pruned networks underwent pretraining on the same datasets used for the slimmable models, using the same hyper- parameters: the pretraining process utilized the Adam optimizer and an initial learning rate of 0.0001 that decayed exponentially by a factor of 0.99 per epoch, for a maximum of 300 epochs. Early termination was implemented to prevent overﬁtting, stop- ping training if no validation accuracy improvement was ob- served for ﬁve consecutive epochs. Following pretraining, un- structured pruning by weights’ magnitude was applied to both the U-Net and the squeeze U-Net variants. This technique re- moves weights with the smallest absolute values until the desired sparsity level (percentage of removed parameters) is achieved. The pruned networks were then ﬁne-tuned for 2–3 epochs using the Adam optimizer to recover some of their performance.

Finally, the F1-score is a harmonic mean of the two previous metrics

precision+recall = 2 ∗TP 2 ∗TP+FP+FN. (4)

F1score = 2 ∗precision ∗recall

B. Experimental Results

SSU-Net is designed for efﬁcient UAV resource usage during image segmentation tasks, reducing computational complex- ity while maintaining inference quality. In this section, we present the results of extensive evaluation experiments. First, we demonstrate that SSU-Net’s low resource usage has minimal impact on performance (see Section IV-C). Next, we show how SSU-Net can “glide” across different points on the resource usage—inference quality tradeoff curve (see Section IV-D). We also demonstrate the beneﬁts of automating dynamic selection of the model width using an auxiliary algorithm. In Section IV-E, we compare SSU-Net to a parameter pruning alternative, show- ing that pruning fails to offer the same beneﬁts. Finally, in Section IV-F, we highlight that SSU-Net achieves competitive performance using signiﬁcantly fewer parameters than other state-of-the-art models.

We trained all neural network models on an Nvidia RTX 3090 GPU with 24 GB of memory. The PyTorch DL framework was used to implement and train all models. Readers are referred to the open-source code for the details of the design and imple- mentation of the training of the DL models.

4) Performance Evaluation Metrics: To assess the suitability of the SSU-Net architecture for real-time deployment on UAVs, we evaluate all models in terms of execution time and energy consumption. The evaluation platform consists of an NVIDIA

MACHIDON et al.: SQUEEZESLIMU-NET: AN ADAPTIVE AND EFFICIENT SEGMENTATION ARCHITECTURE 5755

TABLE III PERFORMANCE EVALUATION (%) OF SSU-NET VERSUS SU-NET ON THE

TABLE IV PERFORMANCE EVALUATION (%) OF SSU-NET VERSUS SU-NET ON THE

AGRIADAPT DATASET

TOBACCO DATASET

C. SSU-Net Maximizes Efﬁciency

respectively. Notably, SSU-Net exhibited a higher recall score than SU-Net at a width of 100% (62.89% compared to 58.76%). This result might be attributed to the SSU-Net’s architecture, which produces slightly coarser segmentation maps (see Fig. 4), potentially incorporating more pixels into the segmented regions compared to its larger counterpart. Consequently, this might lead to a higher recall rate, without a corresponding increase in IoU, since some of the additional pixels might be FPs. However, the differences are nevertheless small, around 4%.

We ﬁrst examine the performance of SSU-Net against its larger counterpart SU-Net. Compared to SSU-Net, SU-Net does not harness the novel SFMs for network compression. We hy- pothesise that the lack of network compression leads to higher performance, but also higher energy usage of SU-Net.

1) Inference Performance: We ﬁrst compare the inference quality of the two networks in Table III. Surprisingly, on the AgriAdapt dataset SSU-Net consistently outperforms SU-Net across multiple metrics and widths. At 100% width, the SSU-Net achieved an IoU of 58.28%, surpassing the SU-Net’s 57.13%. This trend of superior IoU score extends across other widths as well. In terms of accuracy, the SSU-Net also demonstrates clear advantages. At 100% width, it achieved an accuracy of 90.47%, compared to the SU-Net’s 89.41%. This pattern is again consistent across other widths. In terms of the recall metric, the SSU-Net outperforms the SU-Net for the top three widths. The F1-score, balancing precision and recall, also highlights the SSU-Net’s dominance, which scores better at the top three widths.

The performance evaluation on the Tobacco dataset, as de- tailed in Table IV, reveals that, unlike for the AgriAdapt dataset, the SU-Net model demonstrated higher scores across all widths compared to the SSU-Net. Nevertheless, the differences are still quite small, across all metrics varying between 1.53% and 7.23%. For example, for IoU, the SU-Net at 100% width scores 63.58%, compared to the SSU-Net, which at the same width yields an IoU score of 59.67%. Similarly to the results from the AgriAdapt dataset, we observed an increase in all scores (IoU, accuracy, recall, and F1-score) as the width increased.

The slightly better performance of the SU-Net on the Tobacco dataset compared to the AgriAdapt dataset can be attributed to several factors. First, the expanded corpus of images within the Tobacco dataset allows both models to learn from more diverse examples, which particularly beneﬁts the more complex SU-Net. This larger dataset size reduces the risk of overﬁtting, enabling the SU-Net to leverage its higher capacity for improved performance. Second, the lower drone altitude at which the images were acquired provides ﬁner details, aiding the models in accurately distinguishing between weeds and their boundaries (in this case, tobacco plants or soil), thus enhancing the seg- mentation results. Finally, the labeling is also different for the two datasets, AgriAdapt has bounding boxes as labels, while the Tobacco dataset has segments. Because of the nature of the task and of the metrics used for evaluation, any slight deviation of a couple of pixels between the predicted mask and the marked labels can causes a signiﬁcant drop on IoU, leading to big differences between the datasets.

While the SSU-Net consistently outperforms the SU-Net across all metrics, nevertheless the two models perform quite closely. On average, the differences between the metric scores (IoU, accuracy, recall, and F1-score) achieved by the SSU-Net and those achieved by the SU-Net, at the same width, range between 0.95% and 4.13%, with the highest difference being in favor of the SSU-Net. Both models exhibit an increasing trend in all scores with increasing width, showcasing incremental improvements in their IoU, accuracy, recall, and F1-score.

The superior performance of the SSU-Net compared to its “unsqueezed” counterpart can be attributed primarily to the fact that the smaller number of parameters in the SSU-Net reduces the risk of overﬁtting, especially when dealing with limited training data. The AgriAdapt dataset has a relatively low number of images, which increases the risk of overﬁtting for models with more parameters. This explanation is further supported by the fact that, as we will see next, the situation reverses for the Tobacco dataset, which is considerably larger in terms of the number of images. Consequently, the SU-Net, with its higher capacity, performs better on this larger dataset. In addition, sim- ilar instances where the traditional squeeze U-Net has slightly outperformed the traditional U-Net on certain datasets have been reported in related literature [33].

2) Inference Time and Energy Consumption: In Fig. 5(a) we now compare the energy consumption of SSU-Net and SU-Net. The former consistently demonstrates signiﬁcantly higher efﬁciency compared to the latter, across all widths. The most pronounced difference can be seen at 75% width, where SSU- Net is approximately 6.7× more energy-efﬁcient than SU-Net.

The time required for inferring an image is another important aspect for many practical applications. The inference time of

Subtle variations for several metrics, suggest nuanced differ- ences in the segmentation capabilities of SSU-Net and SU-Net

5756 IEEE JOURNAL OF SELECTED TOPICS IN APPLIED EARTH OBSERVATIONS AND REMOTE SENSING, VOL. 18, 2025

Fig. 4. AgriAdapt sample annotated image (a) versus SSU-Net segmentation mask (b) and SU-Net segmentation mask (c). Red polygon overlays represent actual or predicted weeds. (a) AgriAdapt groundtruth image with annotated weeds overlay. (b) AgriAdapt image with segmentation mask produced by SSU-Net 100%. (c) AgriAdapt image with segmentation mask produced by SU-Net 100%.

Fig. 5. Per inference instance energy consumption (a) and runtime for the four widths of the SSU-Net (green bars) versus SU-Net (blue bars). The measurements were performed on an NVIDIA Jetson Nano computing platform using a Monsoon power monitor and averaged across multiple runs. (a) Energy consumption per instance. (b) Inference time per instance.

TABLE V FRAME PER SECOND FOR SSU-NET VERSUS SU-NET,

FPS, ranging from 4.25 for the 100% width network to 9.09 for the 25% width. Juxtaposing these ﬁgures with the above-listed FPS requirements, it is evident that SSU-Net is the only model that brings us toward the desired standards of real-time oper- ation. In contrast, SU-Net, even at its narrowest conﬁguration (25%), does not exceed 4 FPS, placing it below the performance thresholds established in [35]. This limitation reduces SU-Net’s practicality for real-time UAV applications. However, SU-Net’s larger conﬁgurations may ﬁnd utility when deployed to more powerful devices from NVIDIA Jetson family, including the Jetson TX2 platform, where higher computational resources may compensate for the model’s complexity and reduce the execution time.

SQUEEZE U-NET AND U-NET

SSU-Net is signiﬁcantly lower than that of SU-Net across all widths [see Fig. 5(b)], SSU-Net again being up to 6.8× faster than its counterpart at the same width.

The exhibited differences in inference time make an essential distinction between a solution that enables real-time inference and a solution that does not allow such operation. The minimal frames per second (FPS) requirement for real-time onboard weed detection depends on factors, such as UAV type, ﬂight speed, and altitude. Furthermore, as we advance toward highly responsiveUAVs,theneedforhigherFPSrateisgrowingaswell. While 0.43 FPS was deemed sufﬁcient in the past [34], recent literature suggests that rates of 4.5 [35] or even 14 FPS [36] may be needed.

3) Energy–Accuracy and Time–Accuracy Tradeoffs: One of the key contributions of this work is the introduction of a reliable method for trading off resource usage (and inference speed) with the segmentation accuracy. This is achieved through the inclusion of network slimming, supported by both SU-Net and SSU-Net, while SSU-Net comes with an additional beneﬁt of high efﬁciency afforded by the squeeze architecture modules. To illustrate the tradeoffs that our work brings, we plot the IoU versus energy consumption [in Fig. 6(a) on the AgriAdapt dataset and in Fig. 7(a) on the Tobacco dataset] and Io U versus time curves [Fig. 6(b) on the AgriAdapt dataset and Fig. 7(b) on the Tobacco dataset].


> **Table V summarizes the average FPS of different segmenta-**

> tion network architectures across varying widths (if supported).
As evident from the table, our SSU-Net achieves the highest

MACHIDON et al.: SQUEEZESLIMU-NET: AN ADAPTIVE AND EFFICIENT SEGMENTATION ARCHITECTURE 5757

Fig. 6. Average IoU–energy (a) and IoU–time (b) tradeoff curve for the four widths of the SSU-Net (blue) versus SU-Net (orange) on the AgriAdapt test dataset. The four blue dots represent the full width (100%) model, and the 75%, 50%, and 25% slimmed neural models, respectively.

Fig. 7. Average IoU–energy (a) and IoU–time (b) tradeoff curve for the four widths of the SSU-Net (blue) versus SU-Net (orange) on the Tobacco test dataset. The four blue dots represent the full width (100%) model, and the 75%, 50%, and 25% slimmed neural models, respectively.

to up to 7× faster inference with a loss of IoU of up to 1.5%. However, if we directly compare the SSU-Net with the SU-Net, we can see from the results that the SSU-Net is 7× faster than SU-Net, at roughly the same IoU (around +1% difference in the IoU score on the AgriAdapt dataset, and −4% on the Tobacco dataset).

The average IoU–energy consumption tradeoff curve plots for SSU-Net and SU-Net on both the AgriAdapt and the Tobacco test dataset [see Figs. 6(a) and 7(a), respectively] graphically illustrate the monotonically increasing relationship between the segmentation performance (IoU) and the energy consumption. For SSU-Net, the plots shown in Figs. 6(a) and 7(b) depict how the energy usage consistently decreases with the reduction of the network width, only slightly decreasing the average IoU. Speciﬁcally, in the case of the Tobacco dataset, the results show that as the energy consumption decreases threefold (from 0.1 to 0.03 mAh), the average IoU declines by just 3% (from 59% to 56%). Given that this decrease in energy consumption is enabled by the slimmable architecture, we see a similar trend in the case of the SU-Net [see Figs. 6(a) and 7(b)].

D. Input-Based Adaptation Performance

To further validate the beneﬁts of having a runtime adaptive slimmable segmentation architecture, in this section we present the results achieved using an adaptation strategy that adjusts the computational load of the network according to the input’s complexity. Prior studies have demonstrated that the difﬁculty of classifying images in real-world settings can vary widely. Simple samples can be classiﬁed with minimal computational effort, whereas more complex ones demand increased resources for precise inference. As a consequence, runtime-adaptive DL techniques greatly beneﬁt from optimizing their performance by

Figs. 6(b) and 7(b) show the tradeoff points between the average IoU and the total time spent for the inference of the AgriAdapt and Tobacco test set, respectively. The results show that SSU-Net can provide up to 3× faster inference times with a degradation in the IoU score of less than 4%, while SU-Net leads

5758 IEEE JOURNAL OF SELECTED TOPICS IN APPLIED EARTH OBSERVATIONS AND REMOTE SENSING, VOL. 18, 2025

Fig. 8. Average IoU–energy consumption tradeoff curve for the four slimmable widths (blue dots) and for the adaptation (green dots) of the SSU-Net on the AgriAdapt (a) and Tobacco (b) test datasets. The four blue dots represent the full width (100%) model, the 75%, 50%, and 25% slimmed neural models. The orange dots represent adaptation. (a) Adaptation on AgriAdapt dataset. (b) Adaptation on Tobacco dataset.

TABLE VI COMPARISON OF RESULTS FOR INDIVIDUAL SSU-NET WIDTHS AND THE

reducing computations for easier samples but still managing to accurately infer the more challenging ones.

ADAPTATION ALGORITHM (AGRIADAPT DATASET)

To minimize the number of unnecessary computations, we devise an input-based adaptation strategy. For the adaptation strategy, we use the DL supervised classiﬁer, AlexNet [37]. With its eight layers (ﬁve convolutional and three fully connected), and only 0.7 GFLOPS, AlexNet is a powerful yet reasonably small architecture, suitable for predicting which of the SSU-Net model widths should be used for each image instance.

TABLE VII COMPARISON OF RESULTS FOR INDIVIDUAL SSU-NET WIDTHS AND THE

The complexity of each image is assessed by the adaptation model’s feature extraction, and the optimal SSU-Net model width is determined using a labeling method based on the highest IoU score. The width that achieves the highest IoU for each image is labeled as optimal for that particular image. To prevent overﬁtting and account for data distribution shifts between training and test sets, a threshold margin is applied: if a smaller width achieves an IoU within the threshold margin of the highest scoring width, the smaller width is selected instead. This strategy enables computational savings in situations where the accuracy loss is negligible.

ADAPTATION ALGORITHM (TOBACCO DATASET)

when necessary. Similarly, a hybrid controller could combine in- put complexity with resource monitoring to make more holistic decisions, balancing performance and efﬁciency across varying conditions. In addition, a system-load-aware controller could evaluate the current computational load and dynamically slim down the network to mitigate issues, such as thermal throttling, which is common in low-power computing systems deployed on UAVs. These alternative controllers highlight the versatility of SSU-Net in adapting to different scenarios, ensuring robust performance and resource optimization across a wide range of edge computing applications.

We depict the results of using the adaptation strategy on the AgriAdapt and the Tobacco dataset with orange dots in Fig. 8. Using the adaptation technique we can achieve more than 60% reduction in energy consumption with only 2% drop in accuracy, when using the SSU-Net model on the AgriAdapt dataset. Similar results are achieved on the Tobacco dataset, the adaptation strategy enabling again 50% energy savings with less than 1.5% drop in accuracy. Tables VI and VII show that the beneﬁts of dynamic adaptation do not come at the expense of accuracy, recall, or F1-score.

While the experiments in this article focus on an input-based classiﬁer for dynamic adaptation, the SSU-Net framework is inherently ﬂexible and capable of incorporating other types of controllers to meet diverse operational requirements. For instance, a battery-aware controller could dynamically monitor theenergylevelsoftheUAVinreal-time,adjustingthenetwork’s width to prioritize mission completion by conserving power

E. SSU-Net’s Slimming Outperforms Pruning

To validate our approach against alternative neural network compressiontechniques,wecomparetheSSU-Net(andSU-Net) inference accuracy, energy consumption, and running time with the state-of-the-art pruning technique. We compare the IoU versus energy consumption and the IoU versus running time

MACHIDON et al.: SQUEEZESLIMU-NET: AN ADAPTIVE AND EFFICIENT SEGMENTATION ARCHITECTURE 5759

Fig. 9. Average IoU–energy consumption tradeoff curve for the four slimmable widths (blue dots) and for pruned conﬁgurations (green dots) of the SSU-Net (a) versus SU-Net (b) on the AgriAdapt test dataset. The four blue dots represent the full width (100%) model, the 75%, 50%, and 25% slimmed neural models. The four green dots represent the full width (100%) model, the 75%, 50%, and 25% pruned neural models, respectively. (a) SSU-Net. (b) SU-Net.

Fig. 10. Average IoU–time tradeoff curve for the four slimmable widths (blue dots) and for pruned conﬁgurations (green dots) of the SSU-Net (a) versus SU-Net (b) on the AgriAdapt test dataset. The four blue dots represent the full width (100%) model, and the 75%, 50%, and 25% slimmed neural models, respectively. The four green dots represent the full width (100%) model, and the 75%, 50%, and 25% pruned neural models, respectively. (a) SSU-Net. (b) SU-Net.

to better understand the tradeoff that can be obtained using each compression method. Figs. 9 and 11 summarize the seg- mentation performance comparison between the slimmed and the pruned versions of the same squeeze U-Net architecture [see Figs. 9(a) and 11(a)] and between the slimmed and the pruned versions of the same U-Net architecture [see Figs. 9(b) and 11(b)] on the AgriAdapt and Tobacco dataset, respectively.

post-training reduction of parameters, which severely affects network performance. Slimmable neural networks on the other hand, are designed to be trainable and usable at multiple widths since all the different widths are trained simultaneously, thus the network is inherently taught to perform well with fewer parameters. As a result, smaller, i.e., slimmer, versions of SNNs are not just a truncated version of a larger network (as is the case with pruned networks), but properly trained and optimized versions, thus exhibit better generalization and efﬁciency than pruned networks.

While both pruning and slimming provide a monotonic degra- dation of the IoU with the compression rate, slimming achieves signiﬁcantly better performance across the board. For instance, on the AgriAdapt dataset, the SSU-Net 25% has an IoU of 53%, while its pruned counterpart, PSU-Net 25% achieves an IoU of only 46%. At the same time, the SSU-Net 25% width consumes approximately 77% less energy and is more than twice as fast in terms of inference time per instance compared to the PSU-Net 25%. The higher accuracy penalty of the pruning method comes from the fact that unlike network slimming, pruning relies on

Crucially, while slimmed networks see reduced energy con- sumption and inference time when the number of active network parameters is decreased, this is not the case with pruned net- works. As seen in Figs. 9 and 10 for the AgriAdapt dataset, and Figs. 11 and 12 for the Tobacco dataset, the energy and time expenditure of pruned networks remains essentially the same, irrespective of the pruning ration. In real systems, neither DL

5760 IEEE JOURNAL OF SELECTED TOPICS IN APPLIED EARTH OBSERVATIONS AND REMOTE SENSING, VOL. 18, 2025

Fig. 11. Average IoU–energy consumption tradeoff curve for the four slimmable widths (blue dots) and for pruned conﬁgurations (green dots) of the SSU-Net (a) versus SU-Net (b) on the Tobacco test dataset. The four blue dots represent the full width (100%) model, the 75%, 50%, and 25% slimmed neural models, respectively. The four green dots represent the full width (100%) model, the 75%, 50%, and 25% pruned neural models, respectively. (a) SSU-Net. (b) SU-Net.

Fig. 12. Average IoU–time tradeoff curve for the four slimmable widths (blue dots) and for pruned conﬁgurations (green dots) of the SSU-Net (a) versus SU-Net (b) on the Tobacco test dataset. The four blue dots represent the full width (100%) model, the 75%, 50%, and 25% slimmed neural models, respectively. The four green dots represent the full width (100%) model, the 75%, 50%, and 25% pruned neural models, respectively. (a) SSU-Net. (b) SU-Net.

compilers nor the underlying hardware, can capitalize on the pruning—although pruning sets certain weights to zero, these weights are still involved in DL computation, and thus account for both latency and energy consumption in real-world systems.

delineations, with the ResNet50 backbone enhancing spatial featurecapturewhilemaintainingcomputationalefﬁciency.Seg- Net [41],another strong competitor, is a deep convolutional encoder–decoder model that efﬁciently captures spatial hierar- chies, delivering accurate pixelwise segmentation maps.

Finally, a U-Net network architecture [7] was also included in the comparison, as it is a widely recognized and foundational model in the ﬁeld of image segmentation, known for its effective use of an encoder-decoder architecture and skip connections, which help preserve spatial information and improve segmen- tation accuracy, making it a relevant baseline for comparing state-of-the-art models.

F. SSU-Net Vs. State-of-the-Art Networks

To further validate our approach, we compare the pro- posed slim squeeze U-Net with several state-of-the-art DL image segmentation models, including DeepLab V3 [38] and LRASSP [39]. The DeepLab V3 family, which includes the model implemented with a MobileNetV3-Large backbone, has demonstrated high performance across multiple challenging benchmarks. The LRASSP model [39] is a lightweight seg- mentation architecture that has also achieved state-of-the-art results on several datasets. In addition, we compare with the FCN model [40], a widely used segmentation model known for its ability to produce precise object boundary

The results in Table VIII demonstrate that SSU-Net achieves equivalent performance with other state-of-the-art models, with approximately 58% IoU and 90%–91% accuracy, while using signiﬁcantly fewer parameters. The fact that a smaller model, in terms of the number of parameters, performs on par with or slightly better than a deeper model is not surprising, as previous

MACHIDON et al.: SQUEEZESLIMU-NET: AN ADAPTIVE AND EFFICIENT SEGMENTATION ARCHITECTURE 5761

TABLE VIII COMPARISON BETWEEN THE PROPOSED SLIM SQUEEZE U-NET AND OTHER STATE-OF-THE-ART DEEP LEARNING APPROACHES FOR IMAGE SEGMENTATION

SSU-Net architecture can dynamically modify the number of parameters used for inference. This adaptability allows the net- work to adjust to various hardware constraints, contexts of use, and operational restrictions.

First, the lightweight and adaptable SSU-Net can be deployed on diverse UAV platforms with varying processing capabilities. For instance, on platforms that cannot sustain a high FPS pro- cessing rate when the full version of the network is used, the network can be automatically tuned to a low-resource version that uses only a fraction of the width. Moreover, our solution offers predictable performance, as the resource consumption and the expected inference accuracy of each network conﬁgu- ration (i.e., width) can be reliably precharacterized. In addition, the lack of the need to retrain the network makes the solution readily deployable to a wide range of end-users who are not necessarily computing experts.

Second, unlike existing real-time UAV computer vision ap- proaches that often rely on a single, pre-trained, lightweight model throughout a mission, the SSU-Net can be dynamically slimmed down during ﬂight, allowing it to adapt to various contextual factors that can signiﬁcantly impact inference. For weed detection, for instance, these factors include sowing errors, camera movements, crop–weed similarity [42], [43], lighting conditions, and plant growth stages [43]. This adaptability means that at any given moment, the network can be adjusted to use the least amount of computation necessary to reliably complete the inference task.

Fig. 13. Parameters versus IoU comparison for SSU-Net and other state-of- the-art models.

work have also supported this claim. The superiority of smaller models is based on the hypotheses that suggest that deeper models may not be more effective for size-limited objects as the highly structured representations in deeper layers, which often lack critical cues for small objects, are suboptimal for detecting small-scale objects such as weeds [29].

Finally, our solution can adapt to changing operating con- ditions during ﬂight. For example, SSU-Net’s dynamic width adjustment allows for using a lower network width when battery levels are low, potentially saving enough energy to complete a mission with minimal accuracy loss. Similarly, dynamic net- work slimming, as implemented in the SSU-Net, has also been shown to be effective in mitigating thermal throttling, a com- mon issue during continuous DL/ML model operation on edge devices [44].

The IoU versus Parameters plot depicted in Fig. 13 highlights SSU-Net’s ability to balance model complexity and segmenta- tion performance effectively. With 2.5 M parameters, SSU-Net achievesanIoUof58.28%,closelymatchinglargermodels,such as Deeplab V3 (58.35%, 11.0 M) and outperforming lightweight models, such as U-Net (52.61%, 0.5 M). Compared to much larger models such as FCN (62.62%, 35.3 M) and SegNet (43.01%, 29.44 M), SSU-Net offers a signiﬁcant reduction in size while maintaining high performance, enabling faster infer- ence speeds critical for real-time applications. Unlike SU-Net and U-Net, which do not meet real-time thresholds, SSU-Net achievesFPSrates(4.25–9.09)thatalignwithestablishedbench- marks for UAV-based weed detection.

B. Real-Time Operation

The adaptability of our model is complemented by its excep- tional real-time performance. Our SSU-Net’s inference speed aligns well with those reported by other state-of-the-art real-time image segmentation implementations on UAVs. For example, Deng et al. [35] achieved 4.5 FPS with their lightweight se- mantic segmentation network for real-time weed mapping on UAVs running on an NVIDIA Jetson TX2. Similarly, Shuf- ﬂeDet, a real-time vehicle detection algorithm for onboard UAV operation, reports a performance of 14 FPS on the same Jetson TX2 platform [36]. These benchmarks highlight the efﬁciency of our SSU-Net, which achieves comparable per- formance on the less powerful Jetson Nano. Despite the Jet- son TX2 offering up to 2.5× the performance of the Jetson Nano [45], our SSU-Net demonstrates signiﬁcant efﬁciency and speed even on this more constrained platform, underscoring its potential for widespread application in real-time UAV vision tasks.

V. DISCUSSION

A. Adaptability

In this article, we present a novel DL architecture ideally suited for image processing onboard a UAV. The key technical advancement we introduce is adaptability—to the best of our knowledge, no other existing solution for image segmentation allowsit.ByleveragingswitchableBNlayersandthespecialized training procedure of slimmable neural networks [9], our novel

5762 IEEE JOURNAL OF SELECTED TOPICS IN APPLIED EARTH OBSERVATIONS AND REMOTE SENSING, VOL. 18, 2025

C. Impact

VI. CONCLUSION

The utility of the DL architecture developed in this article was demonstrated on the problem of weed identiﬁcation in aerial images. Nevertheless, the SSU-Net is in no way constrained to this domain. In precision agriculture, there are numerous other tasks currently handled through expensive manual labor, such as plant height estimation [46], plant counting [47], canopy cover estimation [48], and biomass estimation [49], which have al- ready been shown to beneﬁt from UAV-based image processing. Our work represents a crucial step toward widely deployable, practical solutions to such tasks. In addition, other ﬁelds of UAV remotesensingthatinvolvesegmentation,suchasenvironmental monitoring (e.g., forest health assessment), disaster manage- ment (e.g., damage assessment), and infrastructure inspection (e.g., crack detection), can also beneﬁt from our approach.

In this work, we introduced a novel neural network archi- tecture, the SSU-Net, designed to tackle the complexities of real-time image segmentation on resource-constrained devices, such as UAVs. SSU-Net leverages the strengths of the U-Net architecture, renowned for its success in semantic segmentation, incorporates the computational efﬁciency of the SqueezeNet ﬁre module, and harnesses the adaptability of SNNs, allowing the network to dynamically adjust its width during runtime. This adaptability provides ﬂexibility for on-the-ﬂy adjustments be- tween accuracy and computational cost based on task speciﬁcs, operational conditions, or other guiding parameters.

We demonstrated the effectiveness of SSU-Net in achieving accurateinstancesegmentationforweeddetectionwhilerunning on a UAV-compatible edge computing device. Our results show that SSU-Net can provide up to 3× faster inference times with a accuracy degradation of only 2%. We also showed that the SSU-Net outperforms state-of-the-art neural network compres- sion techniques, such as network pruning, in balancing accu- racy and resource consumption, while offering the additional beneﬁt of runtime adaptability. This adaptability is critical for real-time UAV remote sensing operations, where conditions and requirements can change dynamically. At the same time, the SSU-Net achieves equivalent performance using signiﬁcantly fewer parameters than other state-of-the-art models.

Thereducedenergyconsumptionandprocessingtimeenabled by SSU-Net allow UAVs to run on-board image processing without signiﬁcant overhead. This opens the possibility for fully automated remote sensing operations, where a UAV performs imaging, processing, and on-board decision-making and action- ing. In the future, we envision fully autonomous systems for weed removal and precision spraying, potentially relying on the coordination of multiple units, such as a UAV and an on-ground robot.

Finally, to the best of our knowledge, there are only a few open-source solutions for UAV on-board vision with a focus on image segmentation. We deliberately designed our solution to be deployable to a wide range of low-cost computing devices (e.g., a single-board computer running Linux) that can easily be ﬁtted to an inexpensive off-the-shelf UAV. In precision agriculture, for example, our approach could be particularly beneﬁcial for small farms that cannot afford expensive investments, thereby ensuring sustainability and diversity in agricultural practices through affordable UAV-based remote sensing.

Our contribution represents a signiﬁcant advancement in bridging the gap between high-performance segmentation mod- els and the limitations of on-board UAV processing. The SSU- Net’s capability to reduce energy consumption and processing time, combined with its adaptability and ease of deployment across diverse hardware conﬁgurations, positions it as an ideal solution for real-time image segmentation. This work enhances the potential of real-time UAV remote sensing and provides a practical, deployable solution that can beneﬁt precision agricul- ture and other various ﬁelds, including environmental monitor- ing, disaster management, and infrastructure inspection.

D. Limitations and Future Work

Among the potential limitations of the proposed slim squeeze U-Net, one key concern is the requirement for good quality training datasets to fully utilize the model’s reduced complexity. If the training data does not adequately capture the diversity of weed appearances, including variations in shape, size, and environment, the model’s ability to generalize across different widthsmaybesigniﬁcantlyhindered,leadingtosituationswhere the widest widths of the network might overﬁt and underperform comparedtothemoreslimmedconﬁgurations. Inaddition, while slimmable models are designed to adjust their computational load based on available resources, maximizing their potential for real-time adaptability requires an efﬁcient adaptation algorithm. Such an algorithm was presented in Section IV-D, however other more complex strategies need to be investigated in the future. By integrating a robust and efﬁcient adaptation algorithm, the balance between performance and efﬁciency can be successfully attained, especially in dynamic, resource-constrained environ- ments where rapid adjustments are critical, such as precision agriculture.


## REFERENCES

[1] M. N. Tahir, Y. Lan, Y. Zhang, H. Wenjiang, Y. Wang, and S. M. Z. A.

Naqvi, “Chapter 4 - application of unmanned aerial vehicles in precision agriculture,” in Proc. Precis. Agriculture, 2023, pp. 55–70. [2] D. C. Tsouros, S. Bibi, and P. G. Sarigiannidis, “A review on UAV-based

applications for precision agriculture,” Information, vol. 10, no. 11, p. 349, 2019. [3] J. Lee, H. Nazki, J. Baek, Y. Hong, and M. Lee, “Artiﬁcial intelligence ap-

proach for tomato detection and mass estimation in precision agriculture,” Sustainability, vol. 12, no. 21, 2020, Art. no. 9138. [4] M. Fawakherji, C. Potena, A. Pretto, D. D. Bloisi, and D. Nardi, “Multi-

spectral image synthesis for crop/weed segmentation in precision farm- ing,” Robot. Auton. Syst., vol. 146, 2021, Art. no. 103861. [5] G. Storey, Q. Meng, and B. Li, “Leaf disease segmentation and detection

in apple orchards for precise smart spraying in sustainable agriculture,” Sustainability, vol. 14, no. 3, 2022, Art. no. 1458. [6] S. Rasti, C. J. Bleakley, N. Holden, R. Whetton, D. Langton, and G.

O’Hare, “A survey of high resolution image processing techniques for cereal crop growth monitoring,” Inf. Process. Agriculture, vol. 9, no. 2, pp. 300–315, 2022. [7] O. Ronneberger, P. Fischer, and T. Brox, “U-Net: Convolutional networks

for biomedical image segmentation,” in Proc. 18th Int. Conf. Med. Im- age Comput. Comput.-Assisted Intervention–MICCAI, Munich, Germany, Oct. 5-9, 2015, Proceedings, Part III 18. Springer, 2015, pp. 234–241.

MACHIDON et al.: SQUEEZESLIMU-NET: AN ADAPTIVE AND EFFICIENT SEGMENTATION ARCHITECTURE 5763

[8] N. Beheshti and L. Johnsson, “Squeeze U-Net: A memory and en-

[33] A. Pennisi, D. D. Bloisi, V. Suriani, D. Nardi, A. Facchiano, and A. R.

ergy efﬁcient image segmentation network,” in Proc. 2020 IEEE/CVF Conf. Comput. Vis. Pattern Recognit. Workshops (CVPRW), 2020, pp. 1495–1504. [9] J.Yu,L.Yang,N.Xu,J.Yang,andT.Huang,“Slimmableneuralnetworks,”

Giampetruzzi, “Skin lesion area segmentation using attention squeeze u- net for embedded devices,” J. Digit. Imag., vol. 35, no. 5, pp. 1217–1230, 2022. [34] A. Menshchikov et al., “Real-time detection of hogweed: UAV platform

in Proc. Int. Conf. Learn. Representations, 2018, pp. 1–12. [10] F. Lateef and Y. Ruichek, “Survey on semantic segmentation using deep

empowered by deep learning,” IEEE Trans. Comput., vol. 70, no. 8, pp. 1175–1188, Aug. 2021. [35] J. Deng, Z. Zhong, H. Huang, Y. Lan, Y. Han, and Y. Zhang, “Lightweight

learning techniques,” Neurocomputing, vol. 338, pp. 321–348, 2019. [11] J. Chen and X. Ran, “Deep learning with edge computing: A review,”

semantic segmentation network for real-time weed mapping using un- manned aerial vehicles,” Appl. Sci., vol. 10, no. 20, 2020. [36] S. Majid Azimi, “Shufﬂedet: Real-time vehicle detection network in on-

Proc. IEEE, vol. 107, no. 8, pp. 1655–1674, Aug. 2019. [12] D. Hernández, J. M. Cecilia, J.-C. Cano, and C. T. Calafate, “Flood detec-

board embedded uav imagery,” in Proc. Eur. Conf. Comput. Vis. (ECCV) Workshops, 2018, pp. 88–99. [37] A. Krizhevsky, “One weird trick for parallelizing convolutional neural

tion using real-time image segmentation from unmanned aerial vehicles on edge-computing platform,” Remote Sens., vol. 14, no. 1, p. 223, 2022. [13] S. Jiang, Y. Cheng, and J. Zhang, “Vision-guided unmanned aerial system

for rapid multiple-type damage detection and localization,” Struct. Health Monit., vol. 22, no. 1, pp. 319–337, 2023. [14] Y. Wang, W. Feng, K. Jiang, Q. Li, R. Lv, and J. Tu, “Real-time damaged

networks,” 2014, arXiv:1404.5997. [38] L.-C. Chen, “Rethinking atrous convolution for semantic image segmen-

tation,” 2017, arXiv:1706.05587. [39] A. Howard et al., “Searching for mobileNetV3,” in Proc. IEEE/CVF Int.

building region detection based on improved YOLOv5s and embedded system from UAV images,” IEEE J. Sel. Topics Appl. Earth Observ. Remote Sens., vol. 16, pp. 4205–4217, 2023. [15] M. Y. Yang, S. Kumaar, Y. Lyu, and F. Nex, “Real-time semantic seg-

Conf. Comput. Vis., 2019, pp. 1314–1324. [40] J. Long, E. Shelhamer, and T. Darrell, “Fully convolutional networks

for semantic segmentation,” in Proc. IEEE Conf. Comput. Vis. Pattern Recognit., 2015, pp. 3431–3440. [41] V. Badrinarayanan, A. Kendall, and R. Cipolla, “SegNet: A deep convolu-

mentation with context aggregation network,” ISPRS J. Photogrammetry Remote Sens., vol. 178, pp. 124–134, 2021. [16] S. Tilon, F. Nex, G. Vosselman, I. Sevilla de la Llave, and N. Kerle,

tional encoder-decoder architecture for image segmentation,” IEEE Trans. Pattern Anal. Mach. Intell., vol. 39, no. 12, pp. 2481–2495, Dec. 2017. [42] X. P. Burgos-Artizzu, A. Ribeiro, M. Guijarro, and G. Pajares, “Real-time

“Towards improved unmanned aerial vehicle edge intelligence: A road infrastructure monitoring case study,” Remote Sens., vol. 14, no. 16, 2022. [17] J. Bowman et al., “UAS edge computing of energy infrastructure dam-

image processing for crop/weed discrimination in maize ﬁelds,” Comput. Electron. Agriculture, vol. 75, no. 2, pp. 337–346, 2011. [43] Z. Wu, Y. Chen, B. Zhao, X. Kang, and Y. Ding, “Review of weed detection

age assessment,” Photogrammetric Eng. Remote Sens., vol. 89, no. 2, pp. 79–87, 2023. [18] Q. Wang, C. Yin, H. Song, T. Shen, and Y. Gu, “UTFNet: Uncertainty-


## methods based on computer vision,” Sensors, vol. 21, no. 11, 2021.

[44] Y. Zhou, F. Liang, T.-w. Chin, and D. Marculescu, “Play it cool: Dynamic

guided trustworthy fusion network for RGB-thermal semantic segmenta- tion,” IEEE Geosci. Remote Sens. Lett., vol. 20, 2023, Art. no. 7001205. [19] Q. Wang, J. Huang, Y. Meng, and T. Shen, “Df2net: Differential feature

shifting prevents thermal throttling,” 2022, arXiv:2206.10849. [45] N. Developer, “Jetson modules,” 2024. [Online]. Available: https://

fusion network for hyperspectral image classiﬁcation,” IEEE J. Sel. Topics Appl. Earth Observ. Remote Sens., vol. 17, pp. 10660–10673, 2024. [20] D. Chai, J. Huang, M. Wu, X. Yang, and R. Wang, “Remote sensing image

developer.nvidia.com/embedded/jetson-modules [46] L. Malambo et al., “Multitemporal ﬁeld-based plant height estimation

using 3 d point clouds generated from small unmanned aerial systems high-resolution imagery,” Int. J. Appl. Earth Observation Geoinformation, vol. 64, pp. 31–42, 2018. [47] F. Gnädinger and U. Schmidhalter, “Digital counts of maize plants by

cloud detection using a shallow convolutional neural network,” ISPRS J. Photogrammetry Remote Sens., vol. 209, pp. 66–84, 2024. [21] Z. Liu, J. Li, Z. Shen, G. Huang, S. Yan, and C. Zhang, “Learning efﬁcient

convolutional networks through network slimming,” in Proc. IEEE Int. Conf. Comput. Vis., 2017, pp. 2755–2763. [22] Y. J. Lee, H. G. Jung, and J. K. Suhr, “Semantic segmentation network

unmanned aerial vehicles (UAVs),” Remote sens., vol. 9, no. 6, p. 544, 2017. [48] L. Han, G. Yang, H. Yang, B. Xu, Z. Li, and X. Yang, “Clustering

slimming and edge deployment for real-time forest ﬁre or ﬂood monitoring systems using unmanned aerial vehicles,” Electronics, vol. 12, no. 23, 2023. [23] M. Kraft, M. Piechocki, B. Ptak, and K. Walas, “Autonomous, onboard

ﬁeld-based maize phenotyping of plant-height growth and canopy spectral dynamics using a UAV remote-sensing approach,” Front. plant Sci., vol. 9, 2018, Art. no. 1638. [49] L. Han et al., “Modeling maize above-ground biomass based on machine

learning approaches using UAV remote-sensing data,” Plant Methods, vol. 15, pp. 1–19, 2019.

vision-based trash and litter detection in low altitude aerial images col- lected by an unmanned aerial vehicle,” Remote Sens., vol. 13, no. 5, 2021. [24] R. Ming, Q. Gong, C. Yang, H. Luo, C. Song, and Z. Zhou, “Fdrmnet:

Alina L. Machidon received the Ph.D. degree in computer science and engineering from theTransilva- nia University of Brasov, Brasov, Romania, in 2020.

Feature diffusion reconstruction mechanism network for crop spike head detection,” Front. Plant Sci., vol. 15, 2024, Art. no. 1459515. [25] Z. Zhao and P. He, “Yolo-u: Multi-task model for vehicle detection and

She is currently a Researcher with the Faculty of Computer and Information Science, University of Ljubljana, Ljubljana, Slovenia. Her research fo- cuses on advancing the intersection of deep learning, compressive sensing, and remote sensing, with an emphasis on resource-efﬁcient systems and the devel- opment of novel algorithms for analyzing large-scale, high-dimensional data, particularly in the context of remote sensing.

road segmentation in UAV aerial imagery,” Earth Sci. Informat., vol. 17, pp. 3253–3269, 2024. [26] F. N. Iandola, S. Han, M. W. Moskewicz, K. Ashraf, W. J. Dally, and K.

Keutzer, “Squeezenet: Alexnet-level accuracy with 50x fewer parameters and< 0.5 mb model size,” 2016, arXiv:1602.07360. [27] AgriAdapt, “Weed detection dataset,” 2023. [Online]. Available: https:

//gitlab.fri.uni-lj.si/lrk/agriadapt/ [28] S. I. Moazzam, U. S. Khan, W. S. Qureshi, T. Nawaz, and F. Kunwar,

“Towards automated weed detection through two-stage semantic segmen- tation of tobacco and weed pixels in aerial imagery,” Smart Agricultural Technol., vol. 4, 2023, Art. no. 100142. [29] G. Cheng et al., “Towards large-scale small object detection: Survey and

Andraž Krašovec is currently working toward the Ph.D. degree with the Faculty of Computer and Infor- mation Science of University of Ljubljana, Ljubljana, Slovenia.

benchmarks,” IEEE Trans. Pattern Anal. Mach. Intell., vol. 45, no. 11, pp. 13467–13488, Nov. 2023. [30] N. Developer, “Jetson nano developer kit,” Sep. 2022. [Online]. Available:

He is currently a Researcher/Project Ofﬁcer with the Joint Research Centre of the European Com- mission. His research interests include alternative user authentication approaches, distributed comput- ing, and innovative IoT applications.

https://developer.nvidia.com/embedded/jetson-nano-developer-kit [31] M. S. Inc., “Monsoon solutions high voltage power monitor,” 2015.

[Online]. Available: http://msoon.github.io/powermonitor/HVPM.html [32] A. Schuler and G. Anderst-Kotsis, “Examining the Energy Impact of

Sorting Algorithms on Android: An Empirical Study,” in Proc. 16th EAI Int. Conf. Mobile Ubiquitous Systems: Comput., Netw. Services, Ser. MobiQuitous ’19. NY, USA: ACM, 2019, pp. 404–413.

5764 IEEE JOURNAL OF SELECTED TOPICS IN APPLIED EARTH OBSERVATIONS AND REMOTE SENSING, VOL. 18, 2025

Veljko Pejovi´c received the Ph.D. degree in computer science from the University of California Santa Bar- bara, Santa Barbara, CA, USA, in 2012.

Octavian M. Machidon received the Ph.D. degree in reconﬁgurable computing from the Transilvania University of Brasov, Brasov, Romania, in 2015.

He is currently an Associate Professor with the Faculty of Computer and Information Science, Uni- versity of Ljubljana, Ljubljana, Slovenia. He was a ResearchFellowwithComputerScienceDepartment, University of Birmingham, Birmingham, U.K. His research interests include resource-efﬁcient mobile systems, human–computer interaction, and cyberse- curity in ubiquitous systems. Dr. Pejovi´c was the recipient of the best paper nomination at ACM UbiComp, best paper runner-up at IEEE Pervasive Computing, and the ﬁrst prize at Orange D4D challenge for his work on epidemics modeling.

He is currently an Assistant Professor with the Faculty of Computer and Information Science, Uni- versityofLjubljana,Ljubljana,Slovenia.Hisresearch focuses on implementing approximate mobile com- puting solutions for enabling energy-efﬁcient mobile applications.
