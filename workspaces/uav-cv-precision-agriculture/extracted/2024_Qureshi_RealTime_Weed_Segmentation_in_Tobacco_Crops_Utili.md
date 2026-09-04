---
workspace_id: SCI-000286
doi: 10.1109/icect61618.2024.10581350
title: Real-Time Weed Segmentation in Tobacco Crops Utilizing Deep Learning on a Jetson
  Nano
authors:
- family_name: Qureshi
  given_name: Muhammad Farrukh
  orcid: null
- family_name: Amin
  given_name: Faisal
  orcid: null
- family_name: Mushtaq
  given_name: Zohaib
  orcid: null
- family_name: Ali
  given_name: Muhammad
  orcid: null
- family_name: Haris
  given_name: Ahmad Abdullah
  orcid: null
- family_name: Rana
  given_name: Aira Younas
  orcid: null
year: 2024
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:40.927446+00:00'
---

# Real-Time Weed Segmentation in Tobacco Crops Utilizing Deep Learning on a Jetson Nano

2024 International Conference on Engineering & Computing Technologies (ICECT)

Real-Time Weed Segmentation in Tobacco Crops

Utilizing Deep Learning on a Jetson Nano

Muhammad Farrukh Qureshi Department of Electrical Engineering

Faisal Amin Department of Biomedical Engineering

Zohaib Mushtaq College of Engineering and Technology

Riphah International University

Riphah International University

University of Sargodha

Islamabad, Pakistan muhammad.farrukh@riphah.edu.pk

Islamabad, Pakistan faisal.amin@riphah.edu.pk

Sargodha, Pakistan zohaib.mushtaq@uos.edu.pk

2024 International Conference on Engineering &amp; Computing Technologies (ICECT) | 979-8-3503-4971-9/24/$31.00 ©2024 IEEE | DOI: 10.1109/ICECT61618.2024.10581350

Aira Younas Rana Department of Biomedical Engineering

Ahmad Abdullah Haris Department of Biomedical Engineering

Muhammad Ali Department of Biomedical Engineering

Riphah International University

Riphah International University

Riphah International University

Islamabad, Pakistan airayounas.bme@gmail.com

Islamabad, Pakistan 22642@students.riphah.edu.pk

Islamabad, Pakistan 23753@students.riphah.edu.pk


## Abstract—This paper explores the deployment of a deep

learning model on an edge device, such as the Jetson Nano
for real-time weed detection in agricultural environments. The
U-Net-MobileNetV2 architecture is utilized to achieve accurate
and efficient detection of weeds while minimizing computational
costs and inference time. The effectiveness of the model in
accurately segmenting weed in aerial images of tobacco fields
has been demonstrated through a series of simulations and
real-time field validations. The methodology proposed in this
study demonstrated 96% accuracy, accompanied by a mean
intersection over union value of 0.851. Furthermore, the trained
model is implemented on the Jetson Nano platform, and real-time
validation is showcased. The successful deployment of the model
on a mobile setup in the tobacco fields of Mansehra, Pakistan,
underscores its practical applicability and relevance to precision
agriculture practices.

Fig. 1: Block diagram of the proposed study

accuracy [15]. Jiang et al. utilized a CNN feature-based graph convolutional network and attained recognition accuracy of up to 98.93% on four weed datasets [16]. Rizvi et al. propose machine and deep learning solutions for weed control, demonstrating high accuracy rates and offering sustainable solutions for modern agriculture [17]. Tao et al. proposed a hybrid CNN-SVM classifier for weed recognition in winter fields, addressing challenges in manual feature extraction and poor generalization performance [18]. Saqib et al. proposed a deep learning-based weed detection model using You Only Look Once (YOLO) [19].

Index Terms—Weed detection, Segmentation, Jetson Nano, U- Net-MobileNetV2, Real-time

I. INTRODUCTION

Weeds in the agricultural ecosystem challenge farmers worldwide. These unwanted plants compete with crops for water and nutrients, reducing crop yield and quality. Sustain- able agriculture requires effective weed management. How- ever, chemical herbicides and manual plucking rarely provide fast and environmentally friendly solutions. Deep learning, a subset of artificial intelligence that draws inspiration from the structure and operation of the human brain, has demonstrated its remarkable abilities to address problems in a number of important areas, such as power management [1], [2], signal classification [3]–[6], cancer detection [7]–[11], and agricul- tural optimization [12]–[14]. In agriculture, the application of deep learning techniques in weed detection has emerged as a promising approach for effective weed management.

Several studies have explored the application and effec- tiveness of deep learning approaches for weed detection. For instance, Haq developed an automated weed detection system using CNN classification on UAV imagery, achieving 99.44%

Fig. 2: An sample image of the dataset showing weed and tobacco crops

979-8-3503-4971-9/24/$31.00 ©2024 IEEE 1

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:39:26 UTC from IEEE Xplore.  Restrictions apply.

(a) (b)

Fig. 3: An image and a zoomed Image with a labeled mask, here purple color shows the background, green color shows the crops and yellow shows the weed.

Fig. 4: Architecture of Unet-MobileNetv2 [25]

Real-time edge detection techniques offer a promising ap- proach for early weed detection in ornamental lawns and sports turf, aiming to reduce pesticide usage. Nitin Rai et al. did a study on aerial-based weed detection using lightweight deep learning models deployed on edge platforms [20]. In their study, Harders et al. utilized a vision-based deep learning method for UAV-based weed detection in horticulture [21]. Mansoor Alam et al. presented a system utilizing computer vision and the Random Forest classifier to detect and classify crops and weeds in real-time, enabling variable-rate agro- chemical spraying based on field requirements [22]. Similarly, Siddhesh Badhan et al. propose a real-time weed detection system using machine learning and stereovision for 3D crop reconstruction [23]. Additionally, Junior et al. introduce a real-time weed detection system based on computer vision and deep learning, specifically utilizing YOLOv5 architectures [24].

Nano. A USB camera was connected to capture the real- time field videos, while the Jetson Nano provides real-time segmentation of the crop utilizing the trained model.

A. Dataset Description

We used the Tobacco Aerial Dataset [26] in this study. The dataset includes Mavic Mini drone images of eight tobacco fields in Mardan, Khyber Pakhtunkhwa, Pakistan. The dataset includes aerial images taken at 4 meters altitude of tobacco plants between 15 and 40 days old. The tobacco fields and surrounding vegetation were photographed at 1920 × 1080 pixels. See Fig. 2 for a sample image from the dataset.

In preprocessing, the resolution of all images was com- pressed and reduced to 480 x 352 pixels. Each image in the dataset was annotated using the MATLAB Image Labeler app. Three labels were defined: (a) background, (b) tobacco crop, and (c) associated weed, and it generated an 8-bit unsigned gray-scale label image with pixel values assigned as 0, 1, and 2, respectively. Fig. 3a and Fig. 3b provide visual representations of sample images from the dataset, along with their corresponding annotated masks. This illustrates the distinguishing boundaries of tobacco crops and associated weeds.

Several of these studies have proposed the classification, detection, or segmentation of weeds present in crops. Never- theless, the analysis of real-time weed segmentation in crops using deep learning still requires substantial investigation. In this paper, we present an application and implementation of a deep learning model on a jetson nano to achieve real-time segmentation of weeds present in tobacco crops. A lightweight encoder-decoder network is employed in order to achieve real- time segmentation while minimizing computational expenses and inference time.

B. Model Architecture

This paper is organized as follows: In Section II, we provide details of the utilized data and our proposed methodology. Section III presents and discusses the results obtained from the proposed methodology, and Section IV concludes the paper.

In this study, we employed a deep learning architecture by combining the U-Net [27] and MobileNetV2 [28] architectures for weed segmentation. Combining the two architectures uses the strengths of both models to detect weeds accurately and efficiently while reducing computational complexity. An encoder-decoder structure with skipping connections transfers high-resolution feature maps from encoder to decoder.

II. METHODOLOGY


> **Figure 1 illustrates the overall flow of the proposed study.**

> The public dataset was gathered from the repository and
contains images and their corresponding masks. The original
images were fed to a rescaling block before being split into a
train and test dataset. The distributed data was fed to the UNet-
MobileNetv2 model. After training and testing, the trained
model was saved and converted into ONNX format. The
ONNX model was subsequently implemented on the Jetson

Combining U-Net and MobileNetV2 architectures [25] yields a hybrid model with high detection accuracy and com- putational efficiency, as shown in Fig. 4. The MobileNetV2 backbone replaces the U-Net encoder, enabling efficient fea- ture extraction from input images. The U-Net decoder can find high-resolution segmentation masks in extracted features. The weeds can be precisely located in the images.

2 Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:39:26 UTC from IEEE Xplore.  Restrictions apply.

(a) (b) (c)

Fig. 5: Performance of Model actual dataset: (a) accuracy, (b) loss, and (c) mean IoU

(a) (b) (c)

Fig. 6: Segmentation validation of the model on an image: (a) the zoomed image, (b) ground truth, and (c) the segmentation output of the model. Here, green is the crop, while yellow is the weed. It is evident from (c) that the model failed to segment the crop and weed and painted all the crop as weed.

The U-Net-MobileNetV2 architecture can be divided into two main components: the encoder and the decoder. En- coder (MobileNetV2 Backbone): The encoder extracts fea- tures using MobileNetV2. MobileNetV2 efficiently extracts hierarchical features from input images using depth-wise separable convolutions and inverted residual blocks. As the input image is 224 x 224 x 3, the MobileNetV2 backbone processes it through multiple convolutional layers to create feature maps with reduced spatial dimensions that preserve visual information. Decoder (U-Net): The decoder uses U- Net architecture with upsampling layers and skip connections. The decoder reconstructs high-resolution segmentation masks from MobileNetV2 backbone feature maps. Skip connections fuse feature maps from different encoder and decoder layers to precisely localize objects in the input image. The decoder produces a segmentation mask of the same spatial dimensions as the input image showing weeds.

ing platform was used to implement this model for real-time agricultural inference.

NVIDIA’s CUDA GPU acceleration allowed us to use PyTorch’s deep learning framework on the Jetson Nano. By optimizing the model for the Jetson Nano’s GPU, real-time inference was possible. The model was also integrated with the Jetson Nano’s camera module for real-time image capture and processing.

D. Performance Evaluation Metrics

Accuracy: Accuracy measures the percentage of correctly classified pixels in the segmentation mask. It is calculated as the ratio of the number of correctly classified pixels to the total number of pixels in the image.

Accuracy = TP + TN TP + TN + FP + FN (1)

Where TP is the true positive, TN is the true negative, FP is the false positive, and FN is the false negative.

Model Output: The output of the U-Net-MobileNetV2 model is a binary segmentation mask of the same spatial dimensions as the input image (224 x 224). Each pixel in the segmentation mask is assigned a binary value indicating whether it belongs to a weed (foreground) or background.

Loss: Loss, often represented as the cross-entropy loss, quantifies the discrepancy between the predicted segmentation mask and the ground truth mask. It penalizes misclassifications and encourages the model to produce accurate predictions.

C. Jetson Nano

N X

3 X

Loss = −1

U-Net-MobileNetV2 was used to detect weeds in aerial tobacco field images. The NVIDIA Jetson Nano edge comput-

yi,c log(ˆyi,c) (2)

N

c=1

i=1

3 Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:39:26 UTC from IEEE Xplore.  Restrictions apply.

(a) (b) (c)

Fig. 7: Model performance on zoomed dataset: (a) accuracy, (b) loss, and (c) mean IoU

(a) (b) (c)

Fig. 8: Segmentation validation of the model on a zoomed image: (a) the zoomed image, (b) ground truth, and (c) the segmentation output of model

Where N is the total number of pixels, yi,c is the one-hot encoded ground truth for pixel i and class c, and ˆyi,c is the predicted probability.

A. Simulation Results

In the initial simulation phase, our focus was to evaluate the performance of the proposed methodology on aerial images captured at an altitude of 4 meters. Despite achieving an over- all accuracy of 79.8% as illustrated in Fig. 5a, the model ex- hibited limitations in accurately distinguishing between crops and weeds. The maximum Intersection over Union (IoU) value achieved was 0.54, indicating moderate alignment between the predicted segmentation mask and the ground truth annotation. This was evident from the observed misclassification of crops as weeds in the segmentation results, as shown in Fig. 6.

Mean Intersection over Union: Mean Intersection over Union (mIoU) computes the average Intersection over Union (IoU) across all classes in the segmentation task. It provides a comprehensive assessment of segmentation performance, accounting for variations in class size and shape.

IoU = |P ∩G|

|P ∪G| (3)

In response to the initial findings, adjustments were made to the experimental setup for the subsequent simulation phase. The images in the dataset were cropped to attain an altitude of approximately 0.5 meters above the ground. This modification allowed for a closer inspection of the agricultural landscape, further enabling the model to capture finer details in the vege- tation. As a result, the performance of the U-Net-MobileNetV2 model significantly improved, with an accuracy of 94% and the maximum IoU reaching 0.85, as shown in Fig. 7. Additionally, the model demonstrated enhanced capabilities in accurately delineating between crops, weeds, and background regions, as shown in Fig. 8.

C X

mIoU = 1

IoUi (4)

C

i=1

Where P is the predicted segmentation mask, G is the ground truth segmentation mask, C is the total number of classes, |P ∩G| denotes the intersection between P and G, |P ∪G| denotes the union of P and G, and IoUi is the IoU for class i.

III. RESULTS AND DISCUSSION

These results underscore the critical role of environmental factors, such as altitude and image resolution, in influencing the performance of deep learning models for weed detection

The dataset was split into 80-20 format, where 80% is used for training while 20% is used for testing. The model was trained on images and their corresponding masks.

4 Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:39:26 UTC from IEEE Xplore.  Restrictions apply.

(a)

Fig. 9: Drone setup for real-time weed segmentation

tasks. By capturing images in closer proximity to the ground, the model was better equipped to discern subtle differences in vegetation characteristics.

(b)

Fig. 10: Validation of real-time segmentation of weed in to- bacco field located at Mansehra, Pakistan: (a) Image captured by camera, and (b) real-time output of the model

B. Real-time Experimental Results

The real-time validation of the scaled U-Net-MobileNetV2 model is an important step in assessing its performance under real-world conditions. As the actual dataset location and the same vegetation were not available, a different location in Mansehra District was utilized for real-time testing. The location was chosen to have an environment with similar agricultural features to the dataset collection site in Mardan.

The experimental setup utiziled for real-time testing consists of the Jetson Nano, camera module, power bank, and other peripherals mounted on a drone. This mobile configuration enabled us to navigate through the tobacco field while cap- turing live aerial images and analyzing the performance of real-time weed detection and segmentation. Fig. 9 shows the drone setup for real-time weed segmentation.

Fig. 11: Real-time timing report of UNet-MobileNetV2 on Jetson Nano

To validate the model’s performance, ground truth observa- tions were obtained through manual inspection of the tobacco fields. Fig. 10 illustrates the real-time segmentation of weed in tobacco fields. The first image in both figures displays the actual image that the camera recorded and showed on the LCD. The second image in both figures illustrates two outputs: the smaller image on the right shows the segmentation masks provided by the model, and the larger image shows the overlap of the masks on the captured image.

and segmenting weeds but also demonstrated its practical applicability in agricultural settings.

The real-time validation of the proposed methodology showed that our algorithm could detect and segment weeds in tobacco fields in Mansehra, Pakistan. The model distinguished crop, weed, and background regions in captured images with high accuracy and IoU scores. The real-world deployment also proves our weed detection algorithm’s precision agriculture applicability. Our portable setup allowed real-time validation across multiple tobacco fields.

Additionally, the model’s real-time performance was mon- itored, as depicted in Fig. 11. The combined duration of the model and real-time inference is observed to be 271.29milliseconds. These findings demonstrate the effec- tiveness of the model in real-time scenarios. The real-time validation process not only confirmed the effectiveness of the scaled U-Net-MobileNetV2 model in accurately detecting

The proposed methodology also had validation challenges and limitations. Some weeds and crops were misclassified, es- pecially when densely vegetated and/or under lighting shadows and variation. However, overcoming these challenges should improve our algorithm’s accuracy and reliability in different environments.

5 Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:39:26 UTC from IEEE Xplore.  Restrictions apply.

IV. CONCLUSION

[11] H. G. M. Qamar, M. F. Qureshi, Z. Mushtaq, Z. Zubariah, M. Z. U.

Rehman, N. A. Samee, N. F. Mahmoud, Y. H. Gu, and M. A. Al-masni, “EMG gesture signal analysis towards diagnosis of upper limb using dual-pathway convolutional neural network,” Mathematical Biosciences and Engineering, vol. 21, no. 4, pp. 5712–5734, 2024. [12] M. K and R. R, “Crop Recommendation for Better Crop Yield for Pre-

In conclusion, this paper examines the real-time use of U- Net-MobileNetV2 for agricultural weed detection. We showed that the model can accurately segment weeds in aerial tobacco field images through simulations and real-time field valida- tions. The proposed methodology performed well in real- world and simulated tests, with high accuracy and IoU scores. The proposed methodology’s successful mobile deployment in Mansehra, Pakistan, tobacco fields shows its practicality and relevance to precision agriculture. The results were encourag- ing, but occasionally incorrect classifications and the need for additional optimization in various environmental conditions limited them. Future research will improve the performance by utilizing customized model architecture, several training datasets, and weed detection system integration into agricul- tural workflows.

cision Agriculture Using Ant Colony Optimization with Deep Learning Method,” Annals of the Romanian Society for Cell Biology, pp. 4783– 4794, Apr. 2021. [13] S. Coulibaly, B. Kamsu-Foguem, D. Kamissoko, and D. Traore, “Deep

learning for precision agriculture: A bibliometric analysis,” Intelligent Systems with Applications, vol. 16, p. 200102, Nov. 2022. [14] A. A. Khan, S. Raza, M. F. Qureshi, Z. Mushtaq, M. Taha, and F. Amin,

“Deep Learning-Based Classification of Wheat Leaf Diseases for Edge Devices,” in 2023 2nd International Conference on Emerging Trends in Electrical, Control, and Telecommunication Engineering (ETECTE), pp. 1–6, IEEE, 2023. [15] M. Anul Haq, “CNN Based Automated Weed Detection System Using

UAV Imagery,” Computer Systems Science and Engineering, vol. 42, no. 2, pp. 837–849, 2022. [16] H. Jiang, C. Zhang, Y. Qiao, Z. Zhang, W. Zhang, and C. Song, “CNN

feature based graph convolutional network for weed and crop recognition in smart farming,” Computers and Electronics in Agriculture, vol. 174, p. 105450, July 2020. [17] S. M. H. Rizvi, A. Naseer, S. U. Rehman, S. Akram, and V. Gruhn,


## REFERENCES

“Revolutionizing Agriculture: Machine and Deep Learning Solutions for Enhanced Crop Quality and Weed Control,” IEEE Access, vol. 12, pp. 11865–11878, 2024. [18] T. Tao and X. Wei, “A hybrid CNN–SVM classifier for weed recognition

[1] Q. Akhter, A. Siddique, S. A. Alqathani, A. Mahmood, M. Alam,

Z. Mushtaq, M. F. Qureshi, W. Aslam, and P. K. Pathak, “Efficient energy management for household: Optimization-based integration of distributed energy resources in smart grid,” IEEE Access, 2023. Pub- lisher: IEEE. [2] M. Akmal, M. F. Qureshi, F. Amin, M. Z. U. Rehman, and I. K.

in winter rape field,” Plant Methods, vol. 18, p. 29, Dec. 2022. [19] M. A. Saqib, M. Aqib, M. N. Tahir, and Y. Hafeez, “Towards deep

learning based smart farming for intelligent weeds management in crops,” Frontiers in Plant Science, vol. 14, p. 1211235, July 2023. [20] N. Rai, X. Sun, C. Igathinathane, K. Howatt, and M. Ostlie, “Aerial-

Niazi, “SVM-based real-time classification of prosthetic fingers using myo armband-acquired electromyography data,” in 2021 IEEE 21st international conference on bioinformatics and bioengineering (BIBE), pp. 1–5, IEEE, 2021. [3] M. F. Qureshi, Z. Mushtaq, M. Z. U. Rehman, and E. N. Kamavuako,

Based Weed Detection Using Low-Cost and Lightweight Deep Learning Models on an Edge Platform,” Journal of the ASABE, vol. 66, no. 5, pp. 1041–1055, 2023. [21] L. O. Harders, V. Czymmek, S. Hussmann, A. Wrede, and T. Ufer, “Deep

“E2CNN: An Efficient Concatenated CNN for Classification of Surface EMG Extracted From Upper Limb,” IEEE Sensors Journal, vol. 23, no. 8, pp. 8989–8996, 2023. Publisher: IEEE. [4] M. F. Qureshi, Z. Mushtaq, M. Z. ur Rehman, and E. N. Kamavuako,

learning approach for UAV-based weed detection in horticulture using edge processing,” in Applications of Machine Learning 2022 (M. E. Zelinski, T. M. Taha, and J. Howe, eds.), (San Diego, United States), p. 27, SPIE, Oct. 2022. [22] M. Alam, M. S. Alam, M. Roman, M. Tufail, M. U. Khan, and

“Spectral image-based multiday surface electromyography classification of hand motions using CNN for human–computer interaction,” IEEE Sensors Journal, vol. 22, no. 21, pp. 20676–20683, 2022. Publisher: IEEE. [5] M. Akmal, S. Khalid, M. Moiz, M. J. Abbass, M. F. Qureshi, and

M. T. Khan, “Real-Time Machine-Learning Based Crop/Weed Detection and Classification for Variable-Rate Spraying in Precision Agriculture,” in 2020 7th International Conference on Electrical and Electronics Engineering (ICEEE), (Antalya, Turkey), pp. 273–280, IEEE, Apr. 2020. [23] S. Badhan, K. Desai, M. Dsilva, R. Sonkusare, and S. Weakey, “Real-

Z. Mushtaq, “Leveraging Training Strategies of Artificial Neural Net- work for Classification of Multiday Electromyography Signals,” in 2022 International Conference on Emerging Trends in Electrical, Control, and Telecommunication Engineering (ETECTE), pp. 1–5, IEEE, 2022. [6] M. A. Latif, Z. Mushtaq, S. Arif, S. Rehman, M. F. Qureshi, N. A.

Time Weed Detection using Machine Learning and Stereo-Vision,” in 2021 6th International Conference for Convergence in Technology (I2CT), (Maharashtra, India), pp. 1–5, IEEE, Apr. 2021. [24] L. C. M. Junior and J. Alfredo C. Ulson, “Real Time Weed Detection

using Computer Vision and Deep Learning,” in 2021 14th IEEE Interna- tional Conference on Industry Applications (INDUSCON), (S˜ao Paulo, Brazil), pp. 1131–1137, IEEE, Aug. 2021. [25] O. Ronneberger, P. Fischer, and T. Brox, “U-net: Convolutional networks

Samee, M. Alabdulhafith, Y. H. Gu, and M. A. Al-masni, “Improving Thyroid Disorder Diagnosis via Ensemble Stacking and Bidirectional Feature Selection,” Computers, Materials & Continua, vol. 78, no. 3, pp. 4225–4241, 2024. [7] N. Afshan, Z. Mushtaq, F. S. Alamri, M. F. Qureshi, N. A. Khan,

for biomedical image segmentation,” in Medical Image Computing and Computer-Assisted Intervention–MICCAI 2015: 18th International Conference, Munich, Germany, October 5-9, 2015, Proceedings, Part III 18, pp. 234–241, Springer, 2015. [26] S. I. Moazzam, U. S. Khan, W. S. Qureshi, T. Nawaz, and F. Kun-

and I. Siddique, “Efficient thyroid disorder identification with weighted voting ensemble of super learners by using adaptive synthetic sampling technique,” AIMS Mathematics, vol. 8, no. 10, pp. 24274–24309, 2023. [8] A. Shahzad, A. Mushtaq, A. Q. Sabeeh, Y. Y. Ghadi, Z. Mushtaq, S. Arif,

war, “Towards automated weed detection through two-stage semantic segmentation of tobacco and weed pixels in aerial imagery,” Smart Agricultural Technology, vol. 4, p. 100142, 2023. [27] H. Huang, L. Lin, R. Tong, H. Hu, Q. Zhang, Y. Iwamoto, X. Han, Y.-W.

M. Z. ur Rehman, M. F. Qureshi, and F. Jamil, “Automated Uterine Fibroids Detection in Ultrasound Images Using Deep Convolutional Neural Networks,” in Healthcare, vol. 11, p. 1493, MDPI, 2023. Issue: 10. [9] S. Khalil, U. Nawaz, Zubariah, Z. Mushtaq, S. Arif, M. Z. ur Rehman,

Chen, and J. Wu, “Unet 3+: A full-scale connected unet for medical im- age segmentation,” in ICASSP 2020-2020 IEEE international conference on acoustics, speech and signal processing (ICASSP), pp. 1055–1059, IEEE, 2020. [28] M. Sandler, A. Howard, M. Zhu, A. Zhmoginov, and L.-C. Chen,

M. F. Qureshi, A. Malik, A. Aleid, and K. Alhussaini, “Enhancing Ductal Carcinoma Classification Using Transfer Learning with 3D U- Net Models in Breast Cancer Imaging,” Applied Sciences, vol. 13, no. 7, p. 4255, 2023. Publisher: MDPI. [10] Z. Mushtaq, M. F. Qureshi, M. J. Abbass, and S. M. Q. Al-Fakih, “Effec-

“Mobilenetv2: Inverted residuals and linear bottlenecks,” in Proceedings of the IEEE conference on computer vision and pattern recognition, pp. 4510–4520, 2018.

tive kernel-principal component analysis based approach for wisconsin breast cancer diagnosis,” Electronics Letters, vol. 59, no. 2, p. e212706, 2023.

6 Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:39:26 UTC from IEEE Xplore.  Restrictions apply.
