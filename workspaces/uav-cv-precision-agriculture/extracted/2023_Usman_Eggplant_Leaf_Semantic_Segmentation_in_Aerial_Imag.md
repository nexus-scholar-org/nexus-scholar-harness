---
workspace_id: SCI-001379
doi: 10.1109/hnicem60674.2023.10589006
title: Eggplant Leaf Semantic Segmentation in Aerial Imagery for Precision Agriculture
authors:
- family_name: Usman
  given_name: Nouran M.
  orcid: null
- family_name: Aleluya
  given_name: Earl Ryan M.
  orcid: null
- family_name: Clar
  given_name: Steve E.
  orcid: null
- family_name: Alagon
  given_name: F. J.
  orcid: null
- family_name: Salaan
  given_name: Carl John O.
  orcid: null
- family_name: Bahinting
  given_name: Maria Fe P.
  orcid: null
year: 2023
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:42.152959+00:00'
---

# Eggplant Leaf Semantic Segmentation in Aerial Imagery for Precision Agriculture

2023 IEEE 15th International Conference on Humanoid, Nanotechnology, Information Technology, Communication and Control, Environment, and Management (HNICEM) | 979-8-3503-8117-7/23/$31.00 ©2023 IEEE | DOI: 10.1109/HNICEM60674.2023.10589006

Eggplant Leaf Semantic Segmentation in

Aerial Imagery for Precision Agriculture

Nouran M. Usman1, Earl Ryan M. Aleluya2, Steve E. Clar3, Francis Jann A. Alagon4, Carl John O. Salaan5, and

Maria Fe P. Bahinting6

1,6Department of Computer Applications, College of Computer Studies 2,4Department of Computer Engineering and Mechatronics, College of Engineering 3Department of Electrical Engineering, College of Engineering 5Graduate School of Engineering Mindanao State University-Iligan Institute of Technology, Iligan City 9200, Philippines {nouran.usman, earlryan.aleluya, steveel.clar, francisjann.alagon, carljohn.salaan, mariafe.bahinting}@g.msuiit.edu.ph


## Abstract—Eggplant is one of the prominent vegetable crops in

the Philippines. Traditional farming practices, like agrochemical
spraying, often lack real-time, high-resolution data crucial for
informed decisions. Monitoring vegetation indices is vital for crop
growth assessment, health monitoring, and precision agriculture.
However, optimizing agrochemical spraying for specific crop
needs remains a challenge. Unmanned aerial vehicles (UAVs) offer
a transformative solution. RGB cameras, designed for visual im-
agery, may not provide accurate vegetation index measurements.
Computer vision, through leaf detection, plays a crucial role in
assessing crop health. This study aims to distinguish eggplant
leaves from their surroundings. Subsequently, the authors com-
pared two open-source segmentation models, namely U-Net and
FPN. Two pre-trained encoders, VGG16 and VGG19, were used
in both models to further evaluate their performance. Using a
drone-mounted RGB camera, the authors gathered images of
mature eggplant leaves. The experimental findings demonstrate
the effectiveness of the VGG16-based FPN architecture for real-
time leaf segmentation tasks as it acquires 97.24% and 96.73%
accuracy with a latency time of 31.5 ms and 32.6 ms, on 0.5 and
0.75 threshold values. The study recommends FPN with VGG16
for its accurate and low-latency performance in time-sensitive
leaf segmentation applications.

Fig. 1: Segmenting leaves semantically. From left to right are the randomly selected input image, the ground truth image, and the predicted segmentation overlay over the input image.

In precision agriculture and crop monitoring, vegetation indices provide valuable insights into plant growth factors, including canopy structure, chlorophyll content, leaf density, and moisture levels. These insights are critical for opti- mizing agricultural practices, including nutrient management, agrochemical application, timely harvesting, and sustainable farming. The Normalized Difference Vegetation Index (NDVI) is frequently used data designed to evaluate the health of vegetation through the utilization of multispectral sensors. Re- mote sensing utilizes passive sensors to capture reflections of electromagnetic waves from canopies, which exhibit variations influenced by elements such as plant species, moisture content of tissues, and inherent properties [3].

Index Terms—aerial sprayer system, agricultural drone, leaf segmentation, semantic segmentation, vegetation index

I. INTRODUCTION

For many years, the Philippines has been known for its solid agricultural foundation, a vital contributor to the nation’s economy, engaging approximately 24.5% of the workforce in 2023 [1]. The country, particularly in Asia, notably cultivates several major crops like eggplants, a vital source of income for many Filipino farmers. Throughout history, Filipino farmers have practiced sustainable agricultural methods, such as crop rotation, intercropping, and terrace farming, to effectively maximize the utilization of limited agricultural land. Similarly, traditional farming reflects a harmonious blend of indigenous knowledge and modern techniques. Agrochemicals, such as pesticides (fungicides, herbicides, insecticides), have been a common practice in crop management for decades, and are applied using sprayers. However, conventional spraying techniques have presented challenges in balancing economic growth with environmental conservation [2].

Subsequently, traditional sprayers were labor-intensive and lacked precision, leading to excessive pesticide use and issues with spray uniformity and loss. Manual measurements of plant parameters were also time-consuming. Fortunately, advances in spraying technology have introduced more efficient and precise methods, including variable rate sprayers, electrostatic sprayers, and UAV-based sprayers, which address these chal- lenges [4].

One of the researches conducted from the Mindanao State University-Iligan Institute of Technology has developed an aerial variable sprayer system. It optimizes agrochemical use by adjusting the flow rate in real-time based on the computed vegetation index of crops [5, 6]. While an RGB camera

979-8-3503-8117-7/23/$31.00 ©2023 IEEE

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:46:54 UTC from IEEE Xplore.  Restrictions apply.

is used for this purpose, it’s important to note that these cameras, designed for visual imagery, may not provide precise vegetation index measurements.

networks offer utility when the available image count is insuf- ficient to meet the requirements of state-of-the-art models [13]. In the ”ImageNet Large Scale Visual Recognition Challenge (ILSVRC)” competition, two of the winner models include VGG16 [14] and VGG19 [14]. Generally, image classification aims to assign a single label to the entire image. However, it operates at a lower level of detail and doesn’t consider individual pixels.

In the area of computer vision, the concept of image segmentation involves partitioning an image into pixel groups of the same category, simplifying the image for enhanced analysis and interpretation. Through this concept, this paper proposed improving the acquisition of vegetation indices from a drone-mounted RGB camera, by using leaf segmentation algorithms. The authors created LeavesUAV, a new dataset of mature eggplant leaves as shown in Fig. 1. Furthermore, this study aims to conduct a comparative analysis of segmentation architectures, namely U-Net [7] and FPN [8], to distinguish eggplant leaves from their surroundings.

Moving beyond image classification, object detection takes the task further by not only classifying objects but also localizing them within the image. In recent studies, various techniques have been employed to detect and locate objects, especially in the context of plant leaf analysis [16–18]. The study [16] uses TinyYOLOv3 network, which is a lightweight and efficient deep learning model. Another algorithm has presented [17] using YOLOv5 algorithm to extract leaf regions from the leaf disease image and deep metric learning to learn a representation of the leaf regions. Next, it uses the learned representation to retrieve similar leaf disease images from a database. Incorporating a space-to-depth module, a Convolu- tional Block Attention Module (CBAM), and Atrous Spatial Pyramid Pooling (ASPP), a recent study [18] enhances ex- isting deep learning-based object detection techniques. These modules help the algorithm to better extract features from leaf images and to deal with challenges such as occlusion and overlapping leaves. Therefore, object detection provides a higher level of detail than image classification, but may not achieve pixel-level accuracy since it deals with object localization rather than pixel-wise labeling.

The present paper is structured in the following manner. The next section, Section II, describes the related works. The following section, marked as Section III explains the general concept and methodology. The results are presented in Section IV, accompanied by an examination of the assessment metrics employed. Lastly, Section V summarizes the essential findings and insights derived from the study.

II. RELATED WORKS

Several studies have been done to explore the potential of various deep learning architecture in the field of plant leaf detection. The initial subsection examines the feature- based methodology for leaf detection. This article provides an overview of the three detection tasks in computer vision and the relevant studies connected to leaf detection.

Semantic segmentation surpasses object detection by as- signing labels to individual pixels within images or videos, demanding a deeper understanding of spatial relationships. One study [19] employed a genetic algorithm for automatic plant leaf disease detection and classification. Moreover, an improved U-shaped network is utilized [20] to improve se- mantic segmentation performance through spatial and channel attention mechanisms, enhancing the overall accuracy. Feature Pyramid Network (FPN) [8] enhances semantic segmenta- tion. The study [21] introduced the lighter Reshaped Feature Pyramid Network (RFPN), optimizing object segmentation across different sizes. Placing RFPN between the encoder and decoder, using the MobileNet as the encoder, and in- tegrating the Pyramid Pooling Module for adaptive pooling sizes substantially boosted segmentation performance, main- taining a favorable balance between accuracy (mean IoU) and computational efficiency (FLOPs). Significantly, segmentation algorithms precisely outline object boundaries and identify object classes for each pixel, making it the most detailed and accurate at the pixel level among the three tasks.

A. Feature-based Leaf Image Detection

Plant leaf analysis typically involves three hand-crafted features: shape, texture, and venation. Shape recognition meth- ods, aided by edge detection like the Canny operator, are commonly used for contour modeling. Several investigations, like the work of [9], employ Hand Crafted Shape (HCS) and Histogram of Curvature over Scale (HoCS) techniques. Others combine the use of shape and texture in order to recognize leaves. As an example, [10] utilizes the multiscale triangle descriptor (MTD) to analyze form characteristics, while the local binary pattern histogram Fourier (LBP-HF) is employed to examine texture properties. Vein patterns, like in [11], are also employed, with features like main vein-secondary vein angles and centroid vein angles used for species classification.

This paper will utilize shape features as leaf contours as they provide a compact, computationally efficient, and simplified representation of the leaf’s overall structure and characteristics.

B. Detection Tasks and Related Studies

This study will focus on using the shape feature for leaf contouring. Furthermore, it aims to enhance the accuracy of vegetation index computation through semantic segmentation using deep learning architecture. To achieve this, the research will utilize the encoders VGG16 and VGG19 and will be employed in both U-Net and the FPN architecture.

Image classification is the task of assigning a label to an image based on its content. In the study [12], transfer learning was used to learn leaf characteristics from a pre- trained deep neural network model. For transfer learning, one crucial feature is the use of pre-trained networks. Pre-trained

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:46:54 UTC from IEEE Xplore.  Restrictions apply.

Fig. 2: The general concept of an aerial variable sprayer system.

III. METHODOLOGY

The general concept of this study, as shown in Fig. 2, shares a conceptual foundation with the previous studies [5, 6] that involved the calculation of vegetation indices and implemen- tation of a variable sprayer system in agriculture. However, this study introduces a novel and sequential methodology.

Fig. 3: Extracted a frame from a 1080p video recording, then patched into 448x448 pixels.

In this methodology, the approach prioritizes leaf segmen- tation as the initial step, followed by vegetation index com- putation and subsequent variable sprayer system application. The authors are confident that using deep learning methods will result in more accurate vegetation index measurements. This heightened accuracy is expected to significantly enhance the efficiency of the variable sprayer system in the precise application of agrochemicals. This study aims to distinguish between eggplant leaves (foreground) and the surrounding land (background) when observed from the UAV perspective. In the upcoming section, the pre-processing techniques applied after obtaining a high-resolution aerial image will be discussed. To accomplish this task, the U-Net and FPN architecture were employed as segmentation models. Also, VGG16 and VGG19 encoders were utilized on both segmentation models, to facilitate comparison and evaluation.

Fig. 4: The augmented training image. Left to Right: The actual image, saturation, hue, brightness and flip adjustments.

main paths: a contracting path with repeated 3x3 convolutions followed by a ReLU and 2x2 max-pooling, and an expansive path that includes upsampling and 3x3 convolutions. Skip connections between the paths enable precise image localiza- tion, making U-Net efficient for segmentation, especially with limited training data.

The FPN architecture [8] enhances object detection by addressing objects of various sizes. It refines standard con- volutional networks with a top-down pathway and lateral connections, constructing an in-network feature pyramid from a single-scale input. The architecture merges deeper, semanti- cally strong features with spatially finer ones, enabling object detection at multiple scales without the need to rescale the input multiple times.

A. Eggplant Leaves Dataset

Initially, this paper built a LeavesUAV dataset by obtaining images of mature eggplant leaves from the authors’ own eggplant farming output. The images were obtained from video recordings captured at a resolution of 1080p during flight tests. The high resolution of UAV aerial photos compromises the efficiency of training. Hence, these images are divided into smaller image sizes of 448x448x3 through the imple- mentation of a sliding window split technique, as depicted in Figure 3. Due to the influence of weather conditions on the actual application test photos, and to mitigate the risk of overfitting during the training process, some data augmentation techniques were implemented on both training and validation datasets. In addition, no modifications were made to the testing set. Figure 4 displays a representative of trained data.

C. Implementation Details

The models previously mentioned were trained using the eggplant leaves dataset. After performing image normalization to align the images with the ImageNet mean and standard deviation, the authors rendered the images in grayscale. The encoders utilized for each model were chosen from the VGG16 and VGG19 networks that had been pre-trained on the Ima- geNet dataset. Input layers of the model were optimized for 448x448-pixel images. The model subsequently produced an output mask whose dimensions mirrored the input’s.

The segmentation models were trained utilizing binary cross-entropy (BCE) with logits as the loss function. By in- tegrating the sigmoid activation and binary cross-entropy loss into a solitary operation, this method achieves both numerical

B. Leaf Segmentation Models

U-Net, introduced in [7], is a U-shaped architecture initially developed for biomedical image segmentation. It features two

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:46:54 UTC from IEEE Xplore.  Restrictions apply.

TABLE I: The hyperparameters initialized in the training process.

Hyperparameters Value

Learning Rate 0.01 Decay Factor 0.01 Decay Frequency 0.01 Optimizers SGD, Ranger Momentum 0.9 Early Stopping Yes Epochs 100 Batch Size 4 Loss Function Binary cross entropy Encoders VGG16, VGG19

Fig. 5: Learning curves of U-Net and FPN, with both encoders VGG16 and VGG19.

stability and computational efficiency. Equation 1 describes the loss function, where N represents the total number of samples in the dataset, yi denotes the true label of the i-th sample, and

demonstrated the lowest validation loss of 0.3735 at epoch 86, underscoring their respective performances.

ˆybi signifies the predicted score (logit) for the i-th sample and class b respectively.

B. Performance Evaluation

The four models were evaluated on 1,350 test images through CPU. The authors used the dice coefficient, IoU, and pixel accuracy, and F1 score as the evaluation metrics. Images containing no eggplant leaves are also included in the evaluation.

N X

BCElogits = −1

yi·log(σ( ˆ ybi))+(1−yi)·log(1−σ( ˆ ybi))

N

i=0

(1) With respect to the parameters of training, the initial learning rate, decay frequency, and learning rate decay factor were all established at 0.01. Ranger and Stochastic Gradient Descent (SGD) are the optimizers in use; with SGD having a momentum of 0.9. Refer to Table I for a summary of the initialization hyperparameters utilized during the training procedure.

The Dice Coefficient is a metric used to quantify the degree of similarity or overlap between the anticipated and ground truth segmentation masks. The intersection of A∩B represents the count of pixels that are accurately segmented in both the predicted and ground truth masks. |A| and |B| represent the total number of pixels in the predicted and ground truth masks, respectively. The dice coefficient is formally defined in Eq. 2.

IV. EXPERIMENTAL RESULTS

Dice = 2 × |A ∩B|

|A| + |B| (2)

The U-Net and FPN leaf segmentation models were im- plemented in PyCharm on Windows 11 using an NVIDIA GeForce RTX 3060 GPU with 3,584 CUDA cores and 6GB memory. These models are implemented using PyTorch-based segmentation models package [22]. The training set consists of 60,750 images, with a 20% random split used to create a validation dataset. Furthermore, the authors determined the batch size for training based on the GPU’s capacity. As a result, the batch size was set at 4 for both U-Net and FPN.

The Intersection over Union (IoU) metric assesses the overlap between the expected and ground truth segmentation masks. IoU is effectively used to evaluate object delineation accuracy in segmentation tasks. Pixels classified as leaf in both predicted and ground truth masks are called the area of inter- section, while pixels classified as either leaf or background in either mask are called the area of union. Refer to Eq. 3 for the formula for IoU.

The model learns complex patterns and improves segmen- tation predictions through a predetermined number of training rounds. Next, the model is evaluated on the test images. The paper assessed the model’s accuracy in categorizing test images using particular metrics, as mentioned in sub-section IV-B.

IoU = Area of Intersection

Area of Union (3)

The authors additionally assessed the model’s pixel classifica- tion accuracy in segmented leaf pictures using pixel accuracy. It calculates the ratio of correctly recognized leaf pixels to the number of image pixels. The metric shows how well the model distinguishes leaf regions from the background, which is essential for agricultural leaf segmentation. The correctly classified pixels refers to the number of pixels in the anticipated segmentation mask that match the ground truth mask. Also, total pixels represents the total number of pixels

A. Training Results


> **Figure 5 depicts the decline in both training and validation**

> losses among the models, highlighting their effective learning
from the dataset as evidenced by converging learning curves.
Specifically, U-Net with VGG19 achieved a minimal training
loss of 0.2803 at epoch 79, while the FPN with VGG19 variant

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:46:54 UTC from IEEE Xplore.  Restrictions apply.

Fig. 7: Semantic segmentation results of U-Net and FPN architecture with encoders VGG16 and VGG19. The upper row has a 0.5 threshold value, while the bottom row has 0.75. A group of eggplant leaves is presented.

Fig. 6: Dice Coefficient, IoU, Pixel Accuracy, and F1 Score results, and their corresponding latency time between U-Net and FPN architecture with encoders VGG16 and VGG19.

in the image. The formula for pixel accuracy is given in Eq. 4.

Fig. 8: Semantic segmentation results of U-Net and FPN architecture with encoders VGG16 and VGG19. The upper row has a 0.5 threshold value, while the bottom row has 0.75. A small portion of the eggplant leaves is presented.

PixelAccuracy = Correctly Classified Pixels

Total Pixels ×100 (4)

After that, the F1 Score represents the harmonic mean of precision and recall. By balancing false positives (misclassi- fying non-leaf pixels as leaf) and false negatives (missing true leaf pixels), the model’s performance is comprehensively eval- uated. The Precision assesses the model’s ability to accurately identify leaf pixels and avoid misclassifying background pixels as leaves. Recall measures the model’s ability to accurately capture the whole leaf area by identifying all relevant leaf pixels without missing any. The F1 score is defined in Eq. 5.

strong F1 score of 0.8002 at the 0.75 threshold. Overall, U- Net with VGG19 stands out as a robust choice for accurate leaf segmentation.

C. Network Latency

The authors evaluated the latency performance of the four models under the same threshold values. Among these models, FPN with VGG16 emerged as the most efficient, exhibiting the lowest average latency times for both thresholds, with 31.5 ms at 0.5 and 32.6 ms at 0.75. Conversely, U-Net with VGG19 consistently demonstrated the poorest latency performance, registering the highest latency times among all models, with 38.5 ms at 0.5 and 39.6 ms at 0.75. Hence, FPN with VGG16 is an ideal choice for achieving the delicate balance between accuracy and low latency, making it partic- ularly valuable in time-sensitive agricultural and plant health applications. Meanwhile, U-Net with VGG19, while offering competitive accuracy, may introduce perceptible delays in real- time decision-making processes and should be approached with careful consideration of latency requirements. Results are shown in Fig. 6.

F1Score = 2 × Precision × Recall

Precision + Recall (5)


> **Figure 6 provides a comprehensive overview of the model**

> performance at two threshold values, 0.5 and 0.75. At the 0.5
threshold, U-Net with VGG19 emerges as the top-performing
model, achieving the highest scores in Dice Coefficient, IoU,
and Accuracy. U-Net with VGG16 and FPN with VGG16
also demonstrate strong performance, although slightly below
U-Net with VGG19. FPN with VGG19, while performing
marginally lower than U-Net with VGG16 models, remains
competitive. Upon increasing the threshold to 0.75, demanding
stricter segmentation criteria, U-Net with VGG19 maintains
its superior performance, showcasing its ability to achieve
precise segmentation even under stringent conditions. U-Net
with VGG16 and FPN with VGG16 exhibit respectable perfor-
mance, even though with a reduction in their scores compared
to the 0.5 threshold. FPN with VGG19 also sustains its com-
petitiveness at this higher threshold. U-Net with VGG19 has
a consistently exceptional performance, attaining the highest
F1 score of 0.8080 at the 0.5 threshold and maintaining a

D. Visual Assessment

As shown in Fig. 7 presenting a group of eggplant leaves, U-Net with VGG19 shows the most promising model com- bination in this test image, especially at a threshold of 0.5. This suggests that the VGG19 backbone gives U-Net a slight edge in the segmentation tasks at this threshold. Meanwhile,

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:46:54 UTC from IEEE Xplore.  Restrictions apply.

the authors noticed that the FPN with VGG16 encoder had missed areas on the edges of the segmentation. This likely in- dicates areas of uncertainty or lower confidence in the model’s predictions. Furthermore, it suggests that the model might be struggling to make a definitive decision about whether those regions belong to the target class or the background. Overall, both architectures with the two encoders have shown good performance in segmenting the leaves. The performance results are similar when the models are exposed to a small portion of the leaves, shown in Fig. 8.

[6] Manuel Chad Agurob, Amiel Jhon Bano, Immanuel Paradela,

Steve Clar, Earl Ryan Aleluya, and Carl John Salaan, ”Au- tonomous Vision-based Unmanned Aerial Spray System with Variable Flow for Agricultural Application,” IAENG International Journal of Computer Science, vol. 50, no.3, pp1058-1073, 2023 [7] Ronneberger, O., Fischer, P. & Brox, T. U-Net: Convolutional

Networks for Biomedical Image Segmentation. (2015) [8] T.-Y. Lin, P. Dollar, R. Girshick, K. He, B. Hariharan, and

S. Belongie, “Feature pyramid networks for object detection,” in Proceedings of the IEEE conference on computer vision and pattern recognition, 2017, pp. 2117–2125. [9] Hall, D., McCool, C., Dayoub, F., Sunderhauf, N. & Upcroft,

B. Evaluation of Features for Leaf Classification in Challeng- ing Conditions. Proceedings Of The 2015 IEEE Winter Confer- ence On Applications Of Computer Vision. pp. 797-804 (2015), https://doi.org/10.1109/WACV.2015.111 [10] Yang, C. Plant leaf recognition by integrating shape and texture

V. CONCLUSION This research study significantly contributes to the scien- tific field through two main research components. First, it compared deep learning-based semantic segmentation methods for UAV eggplant leaf detection. Second, the paper provides a new dataset, LeavesUAV, with photos of mature eggplant leaves. The segmentation models U-Net and FPN with en- coders VGG16 and VGG19 exhibited impressive performance outcomes. At the threshold values of 0.5 and 0.75, the accuracy rankings from highest to lowest are as follows: FPN with VGG16 (97.24% and 96.73%), U-Net with VGG19 (96.96% and 96.87%), FPN with VGG19 (96.91% and 96.33%), and U-Net with VGG16 (96.76% and 96.22%). While U-Net with VGG19 demonstrated the highest accuracy from the results of the three evaluation metrics (Dice Coefficient, Intersection over Union, and F1 Score), it exhibited latency issues of 38.5 ms and 39.6 ms that could impact real-time applications. In contrast, FPN with VGG16 outperformed in both accuracy and latency, achieving the highest accuracy with the lowest latency of 31.5 ms and 32.6 ms, ideal for time-sensitive scenarios. Hence, this study recommends using the FPN with the VGG16 model because of its harmonious balance between accuracy and low latency, making it particularly valuable for time- sensitive applications.

features. Pattern Recognition. 112 pp. 107809 (2021) [11] Charters, J., Wang, Z., Chi, Z., Tsoi, A. & Feng, D. EAGLE:

A novel descriptor for identifying plant species using leaf lamina vascular features. 2014 IEEE International Conference On Multi- media And Expo Workshops (ICMEW). pp. 1-6 (2014) [12] Beikmohammadi, A. & Faez, K. Leaf Classification for Plant

Recognition with Deep Transfer Learning. 2018 4th Iranian Con- ference On Signal Processing And Intelligent Systems (ICSPIS). pp. 21-26 (2018) [13] Sabu, A. & Sreekumar, K. Literature review of image features

and classifiers used in leaf based plant recognition through image analysis approach. 2017 International Conference On Inventive Communication And Computational Technologies (ICICCT). pp. 145-149 (2017) [14] K. Simonyan and A. Zisserman, “Very deep convolutional

networks for large-scale image recognition,” arXiv preprint arXiv:1409.1556, 2014. [15] Arda, M., Aleluya, E., Cahig, C., Librado, L., Sumagayan, M.,

Aldueso, K., Galangque, C. & Salaan, C. Semantic Segmentation Models for Crack Detection: Using Shelled Unmanned Aerial Vehicle Imagery. 2021 IEEE 13th International Conference On Humanoid, Nanotechnology, Information Technology, Communi- cation And Control, Environment, And Management (HNICEM). pp. 1-6 (2021) [16] Buzzy, M., Thesma, V., Davoodi, M. & Mohammadpour Velni,

J. Real-Time Plant Leaf Counting Using Deep Object Detec- tion Networks. Sensors. 20 (2020), https://www.mdpi.com/1424- 8220/20/23/6896 [17] Peng, Y. & Wang, Y. Leaf disease image retrieval with object detection and deep metric learning. Frontiers In Plant Science. 13 (2022), https://www.frontiersin.org/articles/10.3389/fpls.2022.963302 [18] Lu, S., Song, Z., Chen, W., Qian, T., Zhang, Y., Chen, M. & Li,

ACKNOWLEDGMENT This research is supported by the Department of Science and Technology - Engineering Research Development and Technology (DOST-ERDT).


## REFERENCES

[1] Mapa, CD. Labor Force Survey. Philippine Statistics Authority

Republic of the Philippines. Employment Rate in August 2023 Was Estimated at 95.6 Percent. (2023) [2] Yarpuz-Bozdogan, N. The importance of personal protective

G. Counting Dense Leaves under Natural Environments via an Im- proved Deep-Learning-Based Object Detection Algorithm. Agri- culture. 11 (2021), https://www.mdpi.com/2077-0472/11/10/10 [19] Singh, V. & Misra, A. Detection of plant leaf diseases using

equipment in pesticide applications in agriculture. Current Opin- ion In Environmental Science & Health. 4 pp. 1-4 (2018) [3] J. Xue and B. Su, ”Significant remote sensing vegetation indices:

image segmentation and soft computing techniques. Information Processing In Agriculture. 4, 41-49 (2017) [20] Kan, J., Gu, Z., Ma, C. & Wang, Q. Leaf Segmentation

A review of developments and applications,” J. Sensors, vol. 2017, 2017, doi: 10.1155/2017/1353691. [4] Ahmad, F., Khaliq, A., Qiu, B., Sultan, M. & Ma, J. Ad-

Algorithm Based on Improved U-shaped Network under Complex Background. 2021 IEEE 4th Advanced Information Management, Communicates, Electronic And Automation Control Conference (IMCEC). 4 pp. 87-92 (2021) [21] Sugimoto, Y. & Aono, M. Semantic Segmentation based on Ex-

vancements of Spraying Technology in Agriculture. Technology In Agriculture. (2021), https://doi.org/10.5772/intechopen.98500 [5] Chad Agurob, M., Jhon Bano, A., Paradela, I., Clar, S., Ryan

tended MobileNet with FPN. 2021 8th International Conference On Advanced Informatics: Concepts, Theory And Applications (ICAICTA). pp. 1-6 (2021) [22] P. Yakubovskiy, “Segmentation models pytorch,” GitHub repos-

Aleluya, E. & John Salaan, C. Vision-based Unmanned Aerial Spray System with Variable Flow for Agricultural Application. 2022 IEEE 14th International Conference On Humanoid, Nan- otechnology, Information Technology, Communication And Con- trol, Environment, And Management (HNICEM). pp. 1-6 (2022)

itory, 2020.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:46:54 UTC from IEEE Xplore.  Restrictions apply.
