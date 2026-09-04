---
workspace_id: SCI-000003
doi: 10.48550/arxiv.2508.03751
title: Modular Transformer Architecture for Precision Agriculture Imaging
authors:
- family_name: Gopalan
  given_name: Brian
  orcid: null
- family_name: Nascimento
  given_name: Nathalia
  orcid: null
- family_name: Monga
  given_name: Vishal
  orcid: null
year: 2025
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:28:01.741188+00:00'
---

# Modular Transformer Architecture for Precision Agriculture Imaging

Modular Transformer Architecture for

Precision Agriculture Imaging

1st Brian Gopalan University Park The Pennsylvania State University

2nd Nathalia Nascimento Engineering Division, Great Valley

3rd Vishal Monga University Park The Pennsylvania State University

The Pennsylvania State University

PA, United States

PA, United States nnascimento@psu.edu

PA, United States

briang@psu.edu

vum4@psu.edu

efficiency and select models based on dynamic fac- tors. The routing function utilizes a threshold for the Laplacian of the image to route information to the deblur module; and a threshold for the Mean Absolute Deviation of the image’s high-pass filtered coefficients to route information to the denoise module. 2) Modification of a vanilla vision transformer for address- ing blur by incorporating an unrolled Lucy-Richardson algorithm into the transformer decoder. 3) Modification of a vanilla vision transformer for address- ing noise by employing Fisher Vectors instead of patches in the transformer encoder.


## Abstract—This paper addresses the critical need for efficient

and accurate weed segmentation from drone video in precision
agriculture. A quality-aware modular deep-learning framework
is proposed that addresses common image degradation by ana-
lyzing quality conditions—such as blur and noise—and routing
inputs through specialized pre-processing and transformer mod-
els optimized for each degradation type. The system first analyzes
drone images for noise and blur using Mean Absolute Deviation
and the Laplacian. Data is then dynamically routed to one of
three vision transformer models: a baseline for clean images,
a modified transformer with Fisher Vector encoding for noise
reduction, or another with an unrolled Lucy-Richardson decoder
to correct blur. This novel routing strategy allows the system to
outperform existing CNN-based methods in both segmentation
quality and computational efficiency, demonstrating a significant
advancement in deep-learning applications for agriculture.

arXiv:2508.03751v2  [cs.CV]  7 Aug 2025

These contributions collectively enable weed segmentation from real-world degraded drone imagery using the Sorghum dataset [2], which contains 1,300 blurred–sharp image pairs captured over a sorghum field.

Index Terms—modular deep learning, context-aware, precision agriculture, weed segmentation, vision transformers

I. INTRODUCTION AI-powered computer vision is becoming essential for pre- cision agriculture, with drone-based systems providing critical data for tasks like automated weed identification. A major challenge for these systems is image degradation from drone- induced noise and motion blur. Although traditional CNN- based solutions are often used for denoising and deblurring, more powerful transformer architectures have proven to be more effective. However, this superior performance comes at a cost, as transformers require significantly more computational resources. In addition, recent studies have shown that even transformer-based models exhibit varying degrees of sensitiv- ity to different types of image degradation, particularly noise and blur, which can substantially impact their performance in real-world scenarios [1]. To address this performance- efficiency trade-off, a quality-aware modular deep-learning framework is proposed. This approach provides the flexibility to select and apply the most appropriate models on a per- image basis, allowing for high-quality segmentation while maintaining computational efficiency.

II. BACKGROUND

Modular deep learning [3] is a powerful approach that aims to solve two key challenges in traditional deep learn- ing: computational efficiency and generalizability. Unlike a standard, monolithic pipeline where all data is processed by the same set of operations, this framework uses a router to intelligently route incoming data to the most relevant components. This selective processing ensures that compu- tational resources are used efficiently by only activating the modules required for a specific task. The modular design also has significant benefits for development and collaboration. By breaking down the model into reusable components, the architecture becomes inherently more flexible and easier to extend. This makes it simpler for researchers and developers to add new functionalities or adapt the system for different applications. An extension of this modular concept is dynamic model selection [4]. This framework takes the idea of routing a step further by using context-aware factors to choose the most appropriate model from a collection of pre-trained options. Following the definition by Abowd et al. [5], we consider image quality—specifically degradation factors like blur and noise—as contextual information that characterizes the state of the input image. This context guides dynamic model selection in our framework.

This paper presents a modular deep learning approach with routing and shared computational functions to address noise and blur in drone footage for performing weed segmentation. The contributions of this paper include:

1) A modular deep learning approach that encompasses data routing and computational functions to optimize

The growing prevalence of drones in agriculture, particu- larly for tasks like automated weeding, has brought to light specific challenges inherent in aerial imagery. Two primary issues are common in these images and significantly impact subsequent analysis [6]. First, agricultural fields are often characterized by noise, which can be introduced by physical conditions such as dust and other particulates. Second, the movement of the drone itself during image capture can intro- duce motion blur. Both noise and blur degrade image quality, thereby hindering the performance of critical downstream tasks, such as the segmentation required to accurately identify the location of weeds.

language identification [15]. Similarly, authors [16] introduced the use of the Lucy-Richardson algorithm for deconvolution, utilizing the CNN architecture.

While CNN-based solutions have demonstrated success in computer vision, the transformer architecture, initially intro- duced by Vaswani et al. [17] for natural language processing (NLP) problems, has gained popularity. Dosovitskiy et al. [18] repurposed the transformer architecture for computer vision tasks. Another recently proposed framework is modular deep learning [3]. This framework modularizes computational, routing, and aggregation functionalities to enhance efficiency by eliminating redundancies and facilitating the extensibility of deep learning solutions. Additionally, the modular framework enables task generalization and efficient transfer learning.

III. RELATED WORK

Machine learning (ML) has emerged as a key driver in the agricultural sector [7]. Specifically, ML algorithms have made significant contributions in areas such as crop management for yield prediction and disease and weed detection. In an in- depth study, Rejeb et al. [8] conducted a bibliometric analysis and discovered a growing number of publications on the utilization of drones in agriculture. Notably, the drone market in the United States for agricultural purposes has reached a substantial value of USD 841.9 million. Recent examples of ML applications in agriculture include Van Essen et al. [9], who employed a reinforcement learning-based approach to optimize the route taken by a drone for weed detection. Similarly, Khuimphukhieo et al. [10] utilized drone footage to predict the yield from sugarcane fields using a random forest-based approach. Deep learning-based computer vision algorithms have made a substantial impact in weed detection by utilizing multispectral images captured from drones [11]. However, as Cavaliere et al. [6] point out, videos taken from drones are often degraded by noise and blur, which negatively affects the performance of computer vision tasks.

Extending the modular paradigm, Nascimento et al. [4] in- troduced a framework for selecting models based on dynamic factors. Their solution used simple neural networks and was applied to non-visual, structured sensor data. In contrast, we design a novel modular and context-aware framework specif- ically tailored for visual processing with transformer-based models, which are known to exhibit varying performance under different image quality conditions [1]. Our approach is not a direct application of previous architectures but a new design that integrates routing and quality-aware specialization to address degradation issues in drone imagery—a complex and high-variance visual domain.

IV. PROPOSED APPROACH

The proposed approach efficiently routes images to one of three models based on their characteristics. These three models are implemented in a modular manner to facilitate this process. The three modules involved are:

1) Vision transformer module (ViT) 2) Vision transformer with modular routing to address noise using Fisher Vector encoding (FV) 3) Vision transformer with modular routing to address blur using Lucy-Richardson algorithm (LR) The architecture also enables combinations of these modules. For instance, if both noise and blur are present, the router will select both Fisher Vector encoding and Lucy-Richardson deblurring techniques.

The solution space for addressing noise and blur encom- passes ML techniques such as convolutional neural networks (CNNs). Lecun et al. [12] introduced a pioneering CNN architecture for handwriting recognition, which became the foundation for decades of widespread use of CNNs in com- puter vision. CNNs have proven effective in deblurring images. Genze et al. [2] employed a combination of two CNN-based architectures—UNET and NAFNET—to remove blur from drone images, enabling weed segmentation. Similarly, Hou et al. [13] proposed QMix, a quality-aware CNN-based model that modulates internal feature processing based on input noise levels. While their work focuses on retinal disease classi- fication, it highlights the potential of incorporating quality- awareness into deep learning pipelines for robust prediction under image degradation.

A. Overall Framework

The modular deep learning framework [3] with model selection [4] is illustrated in Figure 1. As drone images enter the framework, they are initially analyzed by a router that inspects the frames for noise and blur. If there is no noise or blur, the frame is directed to a vanilla vision transformer architecture for segmentation. In contrast, if there is noise, the frame is routed to a modified vision transformer encoder that employs Fisher Vectors instead of patch extraction. If there is blur, the frame is directed to a vanilla vision transformer encoder and subsequently to a modified vision transformer decoder that utilizes the unrolled Lucy-Richardson algorithm for deblurring. If both noise and blur are present, the frame is subjected to both the modified encoder and decoder. The

As deep learning gained popularity, traditional computer vision algorithms have been adapted to leverage this paradigm. This includes the authors’ [14] innovation to introduce Fisher Vector encoding as part of their video classifier architecture, which effectively reduced noise. Within the context of the transformer architecture, the sole known application of Fisher Vectors pertains to natural language processing (NLP) for

Data

Vision  Transformer

Modular

Encoder

No noise

Shared Modular Shared

Noise

Modified

Video Frames Quality-aware

Aggregator

Vision  Transformer

Router

Modular Shared

Vision  Transformer

Modified

Vision  Transformer

Fig. 1. High-level architecture of the context-aware modular deep-learning approach.

final segmentation result is aggregated from one of the models and subsequently transmitted as output. By implementing modularity in the encoder, these functional components can be efficiently reused.

z′

l = MSA(LN(zl−1)) + zl−1 (2)

This is followed by Layer Normalization and MLP as shown below:

B. Modular Routing

l)) + z′

zl = MLP(LN(z′

l (3)

The modular router facilitates model selection by inspecting frames for noise and blur. To ascertain whether a frame is noisy, the router compares the Mean Absolute Deviation of the image’s high-pass filtered coefficients with a predefined threshold and routes information to the denoise module ac- cordingly. The routing function employs a threshold for the Laplacian of the image to route information to the deblur module. If both noise and blur are present in the frame, a model that incorporates both Fisher Vector encoding and a Lucy-Richardson-based decoder is selected.

y = LN(z0

L) (4)

Fisher Vectors encode the data as a Gaussian Mixture of Models (GMMs). Data is assigned to each model through a “soft” probability that positions data strongly belonging to a model closer to its center and noisier data further away. By varying the learnable parameters, Fisher Vectors have been employed in traditional image processing algorithms for denoising purposes.

FV descriptor,

C. De-noising Module

ρn(k) = N(fn|µk, σ2

k)vk Pk

(5)

If there is noise, the data is sent to the modified vision transformer encoder that uses Fisher Vector instead of regular images patches. Incorporating Fisher-encoded patches will enhance the accuracy of video segmentation when integrated into a transformer architecture by effectively managing noise in the source data.

j=1 N(fn|µj, σ2

j )vj

Instead of passing the entire noise patch for attention, the Fisher Vector can be calibrated to transmit only those features that are strongly associated with GMMs. This ensures that noises present in the patches will not disrupt the globally learned GMMs. Consequently, the transformer will be able to concentrate its attention on patches devoid of noise. This enhancement will augment the accuracy of the segmentation performed by the vision transformer.

Consider the video to be a set of image frames. This can be represented as: X ∈RT ×H×W ×C , where T is the frame number, H is height, W is width and C is number of channels.

Vision transformer [18] first breaks the image into patches as follows:xp ∈RN×(P 2 ˙C) , where N is the number of patches of dimension PxP.

D. De-blur Module

These patches, including the noise present in the data pass through multi-head attention step along with the position embedding:

If there is blur in the image, it will be sent to the normal vision encoder. Literature research suggests that the use of the Lucy-Richardson (LR) algorithm for deblurring images is effective. A novel idea proposed is that by introducing an unrolled version of the LR algorithm as part of the transformer

z0 = [xclass; x1

pE; x2

pE...; xpNE] + Epos (1)

decoder, it can deblur the video and improve the accuracy of segmentation.

corresponding sharp image. The fourth column consists of the ground truth segmentation mask obtained for the sharp image that is used for training. The dataset was partitioned to allocate 80% of the images for training and 20% for validation.

The LR algorithm iteratively estimates the deblurred image by comparing the predicted deblurred image in each iteration to the original deblurred image and deconvolving the differ- ence between the two. This can be replaced by a unrolled version that can be integrated into the transformer decoder.

B. Metrics

The experimental setup employs the same metric as the original authors [2] to facilitate systematic comparison of results. For the segmentation task, the authors employ the Sorenson-Dice coefficient, commonly referred to as the Dice- Score (DS). This can be represented as:

The following is the iterative step of a traditional LR algorithm:

 g(x, y) (f (k)(x, y) ∗h(x, y)) ∗hreversed(x, y)



f (k+1)(x, y) = f (k)(x, y) ·

(6) For the unrolled version, the Point Spread Function (PSF) update would be:

DS = 2 · TP 2 · TP + FP + FN (11)

In the context of segmentation evaluation, True Positive (TP) represents the number of correctly predicted segmentation results that were indeed positive. False Positive (FP) denotes the number of negative results that were erroneously predicted as positive. Conversely, False Negative (FN) signifies the number of positive results that were incorrectly predicted as negative.

 g(x, y) (h(k)(x, y) ∗f (k+1)(x, y)) ∗f (k+1)



h(k+1)(x, y) = h(k)(x, y)·

reversed(x, y)

(7) In the proposed architecture, in the transformer decoder, with the image features as keys and values, an estimate of the PSF is used as a query. This makes the attention mechanism look at different parts of the image and adjust the PSF. This results in the deblurred image being fed to the final segmentation step that performs in a more accurate manner. This can be represented as follows:

C. Hardware and Software

The experiments were conducted on an Apple computer equipped with an Apple M4 Pro processor, 24GB of memory, and a 10-core GPU. The software utilized Python 3.12.10, along with pytorch, scikit-learn, and scikit-image, for its development.

input = Concatenate(f (k), h(k), g, f (k) ∗h(k)) (8)

Features(k)

f (k+1) = UpdateLayer

Features(k)

 

input,

VI. RESULTS AND ANALYSIS

 (9)

TransformerBlockimage(PatchEmbed(Features(k)

input))


> **Figure 2 presents the output generated by this modular deep**

> learning framework. The ground truth images and masks are
displayed in columns one, three, and four, respectively. The
de-blurred and de-noised image is showcased in column two.
Column five depicts the predicted mask, while column six
overlays the predicted (green) and ground truth (red) masks
onto the blurred image. This visualization effectively demon-
strates the visually strong alignment between the predicted and
ground truth masks. Next, the results will be analyzed using
quantitative metrics.

h(k+1) = UpdateLayerh

Features(k)

 

input,

 (10)

TransformerBlockpsf(PatchEmbed(Features(k)

input))

Depending on the model to which the data was routed to, the segmentation results are aggregated to produce the final result.

V. EXPERIMENTAL SETUP

The dice scores from the experiment are presented in Table I. The original authors [2] reported a Dice-Score of 0.8373 for segmentation. When blurred images were segmented using a vanilla vision transformer without accounting for noise or blur, the Dice-Score was 0.7794. Employing the modular approach, the Dice-Score was enhanced to 0.8492, surpassing the results of the original authors. A more detailed ablation study is presented in the subsequent section.

This section describes the experimental setup, including the datasets, metrics, and evaluation procedures that were used. The experimental setup is designed to investigate the hypothe- sis that the modular deep learning framework, which addresses blur and noise, will substantially enhance the performance of segmentation on the sorghum dataset [2].

A. Dataset

The sorghum dataset [2] comprises 1300 non-overlapping, blurred-sharp image pairs captured by a drone traversing a sorghum field. The ground truth comprises labeled segmen- tation data derived from the blurred and sharp images. Each blurred-sharp image pair, along with its associated segmen- tation result, is represented as four quadrants within a single file. Figure 2 illustrates the contents of a typical file. The first column is the blurred image, while the third column is the

TABLE I SEGMENTATION RESULTS.

Metric Genze ViT ViT+Modular Routing+FV+LR Dice-Score 0.8373 0.7794 0.8492 Time (minutes) 3.5 11 Epochs 75 75

Fig. 2. Example data with results.

TABLE II ABLATION STUDIES.

Metric Genze ViT ViT+FV ViT+LR ViT+FV+LR ViT+Modular Routing+FV+LR Dice-Score 0.8373 0.7794 0.7768 0.7492 0.8512 0.8492 Time (minutes) 3.5 10.5 43 50 11

Lucy-Richardson based decoder was used to correct motion blur. This modular approach not only improved the overall segmentation accuracy, as demonstrated by an increased Dice- Score, but also significantly reduced the computational time. This work offers a powerful and efficient solution for precision agriculture, enabling more accurate and timely weed manage- ment. Future work includes testing this solution on the field and extending the agricultural application to predict harvest.

VII. DISCUSSION


> **Table II presents the ablation study conducted to evaluate**

> the performance of various components within the modular
deep learning framework for image segmentation. The first
column displays the Dice-Score, which was demonstrated
by the dataset creators [2]. The second column showcases
the vanilla vision transformer performing the segmentation,
resulting in a score of 0.7794 and requiring 3.5 minutes for
training.


## REFERENCES

Following the aforementioned modifications, the noise and blur reduction components were independently incorporated into the pipeline. The outcomes are presented in columns 3 and 4, respectively. Their performances were similar to the vanilla transformer. However, the training time increases without the presence of modular routing and quality based model selection.

[1] D. Varga, “Understanding how image quality affects transformer neural

networks,” Signals, vol. 5, no. 3, pp. 562–579, 2024. [2] N. Genze, M. Wirth, C. Schreiner, R. Ajekwe, M. Grieb, and

D. G. Grimm, “Improved weed segmentation in UAV imagery of sorghum fields with a combined deblurring segmentation model,” Plant Methods, vol. 19, no. 1, p. 87, Aug. 2023. [Online]. Avail- able: https://plantmethods.biomedcentral.com/articles/10.1186/s13007- 023-01060-8 [3] J. Pfeiffer, S. Ruder, I. Vuli´c, and E. M. Ponti, “Modular deep

Column 5 presents the results obtained by combining both the de-noise and de-blur modules. Notably, this combination achieves the highest Dice-Score of all the tested combinations, reaching 0.8512. This outcome arises from the fact that all the image quality improvements are performed regardless of their necessity. The increased Dice-Score is at the expense of a much longer computational time of 50 minutes for training.

learning,” 2023. [Online]. Available: https://arxiv.org/abs/2302.11529 [4] N. Nascimento, P. Alencar, C. Lucena, and D. Cowan, “A context-aware

machine learning-based approach,” in Proceedings of the 28th annual international conference on computer science and software engineering, 2018, pp. 40–47. [5] G. D. Abowd, A. K. Dey, P. J. Brown, N. Davies, M. Smith, and

P. Steggles, “Towards a better understanding of context and context- awareness,” in International symposium on handheld and ubiquitous computing. Springer, 1999, pp. 304–307. [6] D. Cavaliere, V. Loia, A. Saggese, S. Senatore, and M. Vento,

The final column underscores the versatility of the mod- ular deep learning framework. The segmentation quality, as assessed by the Dice-Score, is 0.8492, surpassing the score achieved by the original authors but falling short of the score obtained when de-blur and de-noise were applied to all images. However, by selectively utilizing these models, only when required, the solution achieves a significant reduction in computational time, albeit with a slight compromise in the Dice-Score.

“Semantically enhanced uavs to increase the aerial scene understanding,” IEEE Transactions on Systems, Man, and Cybernetics: Systems, vol. 49, no. 3, pp. 555–567, Mar. 2019. [Online]. Available: https://ieeexplore.ieee.org/document/8071144 [7] K. Liakos, P. Busato, D. Moshou, S. Pearson, and D. Bochtis, “Machine

learning in agriculture: a review,” Sensors, vol. 18, no. 8, p. 2674, Aug. 2018. [Online]. Available: https://www.mdpi.com/1424-8220/18/8/2674 [8] A. Rejeb, A. Abdollahi, K. Rejeb, and H. Treiblmaier, “Drones in agri-

culture: A review and bibliometric analysis,” Computers and Electronics in Agriculture, vol. 198, p. 107017, Jul. 2022. [Online]. Available: https://www.sciencedirect.com/science/article/pii/S0168169922003349 [9] R. van Essen, E. van Henten, and G. Kootstra, “UAV- based path planning for efficient localization of non-uniformly distributed weeds using prior knowledge: A reinforcement- learning approach,” Computers and Electronics in Agriculture, vol. 237, p. 110651, Oct. 2025. [Online]. Available: https://www.sciencedirect.com/science/article/pii/S0168169925007574 [10] I. Khuimphukhieo, M. Bhandari, J. Enciso, and J. A. da Silva, “Estimating sugarcane yield and its components using unoccupied aerial systems (Uas)-based high throughput

VIII. CONCLUSION AND FUTURE WORK

This study presented a novel, modular deep-learning ap- proach for weed segmentation in drone imagery. To ad- dress common challenges like noise and motion blur, the architecture was designed to route data through specialized pre-processing models before segmentation. A transformer- based encoder was used to effectively remove noise, and a

phenotyping (Htp),” Computers and Electronics in Agriculture, vol. 237, p. 110658, Oct. 2025. [Online]. Available: https://www.sciencedirect.com/science/article/pii/S0168169925007641 [11] X.-E. Pantazi, D. Moshou, and C. Bravo, “Active learning system for

weed species recognition based on hyperspectral sensing,” Biosystems Engineering, vol. 146, pp. 193–202, Jun. 2016. [Online]. Available: https://www.sciencedirect.com/science/article/pii/S1537511016000143 [12] Y. Lecun, L. Bottou, Y. Bengio, and P. Haffner, “Gradient-based

learning applied to document recognition,” Proceedings of the IEEE, vol. 86, no. 11, pp. 2278–2324, Nov. 1998. [Online]. Available: https://ieeexplore.ieee.org/document/726791 [13] J. Hou, J. Xu, R. Feng, and H. Chen, “Qmix: Quality-aware learning with

mixed noise for robust retinal disease diagnosis,” IEEE Transactions on Medical Imaging, 2025. [14] Q. Chen, Y. Cai, L. Brown, A. Datta, Q. Fan, R. Feris, S. Yan,

A. Hauptmann, and S. Pankanti, “Spatio-temporal fisher vector coding for surveillance event detection,” in Proceedings of the 21st ACM international conference on Multimedia. Barcelona Spain: ACM, Oct. 2013, pp. 589–592. [Online]. Available: https://dl.acm.org/doi/10.1145/2502081.2502155 [15] D. Krebbers, H. Kaya, and A. Karpov, “Multi-level fusion of fisher

vector encoded bert and wav2vec 2.0 embeddings for native language identification,” in International Conference on Speech and Computer. Springer, 2022, pp. 391–403. [16] L. Chen, J. Zhang, Z. Li, Y. Wei, F. Fang, J. Ren, and J. Pan,

“Deep richardson–lucy deconvolution for low-light image deblurring,” International Journal of Computer Vision, vol. 132, no. 2, pp. 428–445, 2024. [17] A. Vaswani, N. Shazeer, N. Parmar, J. Uszkoreit, L. Jones, A. N. Gomez,

Ł. Kaiser, and I. Polosukhin, “Attention is all you need,” Advances in neural information processing systems, vol. 30, 2017. [18] A. Dosovitskiy, L. Beyer, A. Kolesnikov, D. Weissenborn, X. Zhai,

T. Unterthiner, M. Dehghani, M. Minderer, G. Heigold, S. Gelly et al., “An image is worth 16x16 words: Transformers for image recognition at scale,” in International Conference on Learning Representations, 2021.
