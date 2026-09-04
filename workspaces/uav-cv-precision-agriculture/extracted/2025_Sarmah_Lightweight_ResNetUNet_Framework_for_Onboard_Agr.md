---
workspace_id: SCI-001425
doi: 10.1109/etaav66793.2025.11212973
title: Lightweight ResNet-U-Net Framework for Onboard Agricultural Boundary Delineation
  from Drone Imagery
authors:
- family_name: Sarmah
  given_name: Payel
  orcid: null
- family_name: Shaw
  given_name: Anil Kumar
  orcid: null
- family_name: Pandey
  given_name: Tulika
  orcid: null
- family_name: Das
  given_name: Pradip K.
  orcid: null
year: 2025
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:42.259183+00:00'
---

# Lightweight ResNet-U-Net Framework for Onboard Agricultural Boundary Delineation from Drone Imagery

Lightweight ResNet-U-Net Framework for Onboard

Agricultural Boundary Delineation from Drone

Imagery

2025 International Conference on Emerging Technology in Autonomous Aerial Vehicles (ETAAV) | 979-8-3315-9825-9/25/$31.00 ©2025 IEEE | DOI: 10.1109/ETAAV66793.2025.11212973

Payel Sarmah  Centre for Drone Technology  Indian Institute of Technology

Tulika Pandey  Ministry of Electronics and Information

Anil Kumar Shaw  National Institute of Electronics and  Information Technology (NIELIT)

Technology (MeitY)

Guwahati  Guwahati, Assam, India

Bhubaneswar, Odisha, India

New Delhi, India  tulikapandey@meity.gov.in

anilshaw2785@gmail.com

p.sarmah@iitg.ac.in

Pradip K. Das  Centre for Drone Technology  Indian Institute of Technology

Guwahati  Guwahati, Assam, India

pkdas@iitg.ac.in

A fundamental task in interpreting these detailed aerial  scenes is the automated detection and precise delineation of  boundaries between different semantic regions in the  agricultural landscapes. Traditional methods, such as  manually mapping agricultural boundaries or using classical  image processing techniques, are typically slow, expensive,  and less accurate, especially for complex fields or under  diverse  environmental  conditions.  Deep  learning  methodologies have significantly advanced the field of image  segmentation. Architectures such as the U-Net [4], establish a  highly effective encoder-decoder framework for precise pixel-  level tasks. Separately, the introduction of residual  connections within networks like ResNet [5], addressed the  challenge of training intense models by mitigating the  vanishing gradient problem, leading to powerful feature  extractors.


## Abstract—Automated analysis of high-resolution Unmanned

Aerial Vehicle (UAV) imagery is crucial for applications like 
precision agriculture. However, deploying deep learning models 
directly onto resource-constrained drone platforms for real- 
time processing remains a significant hurdle. This paper 
addresses this challenge by developing and evaluating an 
efficient pipeline for agricultural field boundary delineation. We 
employ a robust ResNet-based U-Net architecture to effectively 
handle complex visual features and field boundary delineation 
in challenging winter UAV imagery covering four different 
types of farmlands. While achieving an accuracy of 82%, 
our primary contribution lies in demonstrating the successful 
optimization of this segmented model into lightweight variants 
suitable for edge deployment, paving the way for future onboard 
processing. Initial tests on representative aerial data confirm 
that the optimized lightweight model successfully delineates 
field boundaries with an accuracy of 81% and a rapid inference 
time of approximately 1ms, underscoring its potential for edge 
execution. The optimized model represents a critical step 
towards autonomous, real-time boundary delineation directly 
on UAVs or mobile edge devices, paving the way for more 
responsive and intelligent aerial monitoring systems in 
agriculture and beyond.

Alternatively, researchers like Jong et al. [6] have explored  adversarial training techniques within deep learning  frameworks, showing that incorporating adversarial losses  with architectures like ResUNet can lead to enhanced  accuracy in agricultural field boundary detection. Similarly,  Alizadeh et al. [7] adapted U-Net++ architecture for  agricultural field boundary delineation by addressing the  challenges posed by complex field shapes through satellite  images. Additionally, Yang et al. [8] explored the  identification of functional field units from satellite imagery,  illustrating that deep learning approaches can effectively  delineate these boundaries directly, without first needing to  classify pixel types within the fields.

Keywords—Agricultural farmland boundary delineation,  ResNet, U-Net, Segmentation, lightweight, Edge device.

I. INTRODUCTION

Unmanned Aerial Vehicles (UAVs) have emerged as  transformative platforms in remote sensing, offering  unparalleled flexibility and the ability to acquire geospatial  data at exceptionally high spatial resolutions [1]. This  capability is fueling innovation across diverse applications  that demand fine-grained environmental understanding,  ranging from infrastructure inspection to environmental  monitoring and precision agriculture. However, the very high  resolution and volume of data generated by UAVs present  significant challenges for efficient processing and analysis,  particularly when real-time or near-real-time insights are  required directly from the platform [2]. Therefore, this can be  achieved by integrating drones into broader Internet of Things  (IoT) ecosystems that will enable real-time and autonomous  decision-making [3].

The choice of data source significantly influences the  delineation task as much of the earlier work focused  on satellite imagery (e.g., Landsat, Sentinel). While offering  broad area coverage, the spatial resolution of readily available  satellite data can sometimes limit the ability to precisely  capture intricate boundary details or delineate smaller fields  accurately. In contrast, UAV platforms provide imagery with  significantly higher spatial resolution (often centimeters),  enabling much finer-grained analysis. Despite the significant  progress in accuracy achieved by deep learning models, a  critical bottleneck remains for practical deployment,  especially the computational cost in on-board UAVs. Many  state-of-the-art deep learning models are large and require

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:47:02 UTC from IEEE Xplore.  Restrictions apply.

substantial processing power, making them unsuitable for  direct execution on the resource-constrained edge devices  typically available onboard UAVs. A review by Liu et al. [10]  summarized that precision agriculture supported by AI and  edge computing UAV remote sensing techniques enable  improvements in both productivity and efficiency alongside  cost reductions. They also concluded that algorithmically,  creating efficient, lightweight models using methods derived  from  model  compression,  especially  pruning,  and  quantization, is among the most prominent and widely  adopted techniques today.

nearest-neighbor interpolation for masks (to preserve the  binary nature). The images and masks, initially loaded as  NumPy arrays (using OpenCV), were converted into  PyTorch tensors. The pixel values of the input images were  scaled from the range [0, 255] to [0.0,1.0], and the ground  truth boundary masks were also scaled to [0.0, 1.0] and  ensured to have a single channel (representing the boundary  class).

B. Model Architecture

The proposed model utilizes a robust encoder-decoder  structure, employing convolutional blocks of ResNet34 as the  feature encoder and U-Net up-sampling blocks for the decoder  as shown in Fig.2.

Therefore, in this paper, we developed a lightweight  ResNet-based U-Net model suitable for edge deployment for  detecting agricultural field boundaries from high-resolution  UAV imagery. We utilized the Winter UAV dataset for  farmland boundary detection [11], a significant resource that  specifically targets the complexities of boundary detection in  winter conditions. By combining ResNet with U-Net  structure, our method provides a more robust and accurate  field boundary delineation. Thereafter, the model is optimized  for on-board edge deployment that can be adapted to run  within the computational constraints of the drone, enabling  automated boundary delineation directly on the platform. The  remainder of this paper is structured as follows: proposed  methodology, dataset description, experimental results, and  conclusion.

II. MATERIALS AND METHODS

The proposed system targets the automated detection of  agricultural boundaries from drone-acquired imagery, with a  focus on enabling efficient processing suitable for edge  deployment.

Fig. 2. ResNet-based U-Net architecture

1) Encoder block: The encoder leverages a ResNet34  model trained on ImageNet dataset [12]. We utilize all layers  of the ResNet34 except for the final average pooling layer and  the fully connected classification layer. This encoder acts as  a powerful feature extractor, capturing hierarchical features  from the input UAV images. The output of the final  convolutional block of the ResNet34 encoder serves as the  input to the decoder.

2) Decoder block: The decoder part is responsible for  upsampling the feature maps from the encoder back to the  original input resolution (256×256) to produce a dense, pixel-  wise boundary prediction map. It consists of five sequential  decoder  blocks  and  each  block  employs  a  “Conv2DTranspose” with a kernel size of 2 and stride of 2,  effectively doubling the spatial resolution while halving the  number of features.

3) Output layer: A final 1x1 convolutional layer maps the  64-channel feature map from the last decoder block to a  single-channel output map (256×256×1). This output map  represents the predicted probability for each pixel belonging  to the boundary class.

Fig.1. Schematic illustration of the proposed framework.

By processing high-resolution drone imagery, this model  demonstrates a powerful capability for accurate boundary  detection, offering essential spatial information to enhance  agricultural land management strategies.

C. Evaluation metrics

A. Preprocessing

1) Loss function: Choosing an appropriate loss function is  critical for segmentation, especially when dealing with  potentially imbalanced classes (boundary vs. non-boundary  pixels). We employ a composite loss function combining  Binary Cross-Entropy with Logits and Dice Loss as shown in  eqn (1).

The first step is to process an image. In this work, the  image is first converted to a greyscale image and thereafter  Gaussian filter is utilized to remove noise from the image  with a kernel size of 5*5. Both input images and the ground  truth boundary masks were resized to a uniform dimension of  256x256 pixels using bilinear interpolation for images and

ℒ𝑇𝑂𝑇𝐴𝐿 = ℒ𝐵𝐶𝐸 + ℒ𝐷𝐼𝐶𝐸  (1)

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:47:02 UTC from IEEE Xplore.  Restrictions apply.

where ℒ𝐵𝐶𝐸 is the loss function combines a sigmoid layer  and binary cross entropy loss in one single class defined in eqn  (2):

E. Dataset Description  This research utilizes high-resolution UAV remote sensing  imagery for boundary detection hosted on IEEE data port [12]  that contains 898 high-resolution drone images covering four  types of farmlands, including strip fields, polder fields, raised  fields, and terraces. The data was acquired using a DJI Air 3S  UAV platform over agricultural fields. The images were  captured during the winter months from December 2022 to  February 2025 (publicly available in March 2025). This  timing is significant as it presents challenging environmental  conditions, distinct from typical growing-season imagery.  ℒ𝐷𝐼𝐶𝐸 = 1 −  2 ∑𝑖 𝑝𝑖𝑔𝑖+ 𝗌

ℒ𝐵𝐶𝐸 (𝑥, 𝑦) = −[𝑦. log(𝜎(𝑥)) + (1 − 𝑦). log(1 − 𝜎(𝑥))]  (2)

where y denotes the ground truth label for the pixel and x  represents the raw output logit produced by the final layer of  the network for that corresponding pixel. However, ℒ𝐷𝐼𝐶𝐸  coefficient is a common metric for evaluating segmentation  overlap. The dice loss is derived from this coefficient as  defined in eqn (3):

∑𝑖 𝑝𝑖+ ∑𝑖 𝑔𝑖+ 𝗌  (3)  The dataset features an exceptionally high spatial resolution  with a reported Ground Sampling Distance (GSD) of  Where 𝑝𝑖 is the predicted probability for pixel 𝑖, 𝑔𝑖 is the  ground truth label (0 or 1) for pixel 𝑖, and 𝜀 is the small  positive constant to prevent division by zero and improve  stability.

approximately 2.74 cm. While described as multi-modal, our  work focuses on processing the high-resolution RGB images  provided.

F. Training details  The model was trained using the Adam optimizer with an  initial learning rate of 0.001. The Training was performed on  batches of size 4. The model was trained considering 50  epochs. Early stopping was implemented to prevent  overfitting and reduce training time. The training process  monitored the training loss after each epoch. The model  weights corresponding to the epoch with the lowest training

Combining these two loss functions leverages pixel-level  focus with class-imbalance and optimization for spatial  overlap yielding improved segmentation performance [14].

2) Intersection over Union (IoU): Also known as the  Jaccard index, IoU measures the overlap between the  predicted boundary mask (P) and the ground truth boundary  mask (G) as shown in eqn (4):

𝑇𝑃 + 𝐹𝑃 + 𝐹𝑁  (4)  loss were saved as the best model.

|𝑃 ∪ 𝐺| =  𝑇𝑃

|𝑃 ∩ 𝐺|

𝐼𝑜𝑈 =

III. EXPERIMENTAL RESULTS AND DISCUSSION  Where 𝑇𝑃, 𝐹𝑃, and 𝐹𝑁 are the counts of true positive,  false positive and false negative pixels, respectively. IoU  ranges from 0 to 1, with 1 indicating perfect overlap.

The dataset was divided into two parts: 80% for training  and 20% for testing. The model was evaluated on the test set,  which comprises challenging winter imagery. This season is  particularly difficult for boundary detection due to the lack of  vibrant vegetation, leading to low contrast between fallow  fields and boundaries, and the presence of complex textures  from frost or bare soil. Under these conditions, the model  achieves an accuracy of 82% with a test IoU of 80% and a test  loss of 45%. The IoU score, being a critical measure of spatial  overlap for segmentation tasks, indicates that the model  effectively learned to delineate the majority of agricultural  field boundaries. However, we conducted an initial  verification of the lightweight version of the model by passing  a test image to the model where it achieved an accuracy of  80% with a test IoU of 78%. Preliminary testing revealed a  promising inference speed for the lightweight model,  requiring approximately 1ms to process a single test image,  indicating a strong potential for near real-time performance in  contrast to the original model. Table 1 presents the  performance comparison between the original ResNet-based  U-Net model and its optimized lightweight version.

3) Pixel Accuracy: This metric measures the percentage of  pixels correctly classified (boundary or non-boundary) and it  is calculated as shown in eqn (5) below:

𝐴𝑐𝑐𝑢𝑟𝑎𝑐𝑦 =  𝑇𝑃 + 𝑇𝑁  (5)  𝑇𝑃+ 𝑇𝑁 +𝐹𝑃 + 𝐹𝑁  Where 𝑇𝑃, 𝐹𝑃, 𝐹𝑁 and 𝑇𝑁 represents true positive, false  positive, false negative and true negative pixel count.

D. Optimization technique  A key aspect of utilizing deep learning models with UAVs is  the potential for onboard, real-time processing on edge  devices. These devices typically have limited computational  power, memory, and energy budget compared to server-grade  GPUs used for training.

The trained model was converted into TorchScript  format using tracing. This creates a serialized representation  of the model that can be run independently of Python, often  yielding  performance  improvements  and  simplifying  deployment in mobile and edge device environments. The  traced model captures the execution graph based on a sample  input.


> **Table 1: Performance metrics of both models**

Test  accuracy

Test

Inference

IoU

time

Thereafter,  we  applied  post-training  static  quantization using Py-Torch’s ‘torch.quantization’ module.  This involves inserting quantization and dequantization  stubs, calibrating the model with representative data, and then  converting the model to use INT8 operations. This step is  essential as it reduces the memory footprint and  computational cost of the model by converting floating-point  weights and activations (FP32) to lower-precision integers  (INT8). This leads to minimum accuracy loss when deployed  on a hardware device.

ResNet-based U-Net  model  82%  80%  ~3ms

Lightweight model  81%  78%  ~1ms

Visual inspection of the model’s predictions provides  further insight into its performance. Fig. 3 illustrates the  model's delineation capabilities across the four different  farmland types present in the dataset. The model appears  capable of handling variations in field appearance typical of

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:47:02 UTC from IEEE Xplore.  Restrictions apply.

winter conditions, particularly in the 'Raised Field' and  'Terrace Field' examples. Here, the delineations are sharp and  closely follow the ground truth masks, demonstrating the  model's ability to capture intricate patterns. Conversely, the  'Strip Field' and 'Polder Field' examples highlight the  challenges of lower-contrast, linear boundaries typical of  winter imagery, where the model occasionally produces  slightly fragmented lines. Some minor discrepancies or  missed boundary segments can be observed in complex areas  (shown in Fig.3), which is common in segmentation tasks. In  Fig. 3, the boundaries of the raised farmland are mostly  delineated correctly when compared to the other farmlands.  This visual evidence directly supports the quantitative metrics  in Table 1, confirming that while the vast majority of  boundaries are correctly identified (leading to a high IoU),  minor imperfections persist in the most difficult, low-contrast  areas. However, our main goal is to develop a lightweight  model that can be deployed on board and can be handled by  drones. The trained model was subsequently optimized using  standard techniques to generate lightweight variants (as  discussed in section II) specifically targeting deployment on  resource-constrained platforms. A primary motivation for this  optimization is enabling efficient execution directly onboard  UAVs, facilitating real-time analysis and integration into  potential edge IoT ecosystems. To provide an initial functional  verification of these optimized formats, we conducted a  delineation test using the lightweight model on a  representative image randomly selected from the held-out test  dataset. This test was performed on a standard local  computing system. Therefore, to validate the lightweight  model, a random test sample was selected, and the result is  shown in Fig 4. The visual result of this single image  presented in Fig. 4, indicates that the optimized lightweight  model successfully processed the input data and performed the  intended task. While this single test serves primarily as a  functional check rather than a comprehensive performance  benchmark, its success provides preliminary evidence that the  optimization process did not fundamentally break the model's  predictive capability. The figure demonstrates that even after  quantization to INT8 precision, the model retains its ability to  accurately delineate the complex and fine-grained boundaries  of the farmland. This outcome lends support to the potential  for deploying these computationally efficient models onto  actual UAV edge hardware. Achieving such onboard  execution is crucial for enabling UAVs to perform boundary  delineation autonomously and in near real-time, a significant  step towards more intelligent and responsive aerial monitoring  systems. Of course, comprehensive validation is still required.  Rigorous benchmarking across the entire test set, executed on  representative target edge hardware, is essential to definitively  quantify the inference speedup, memory usage reduction,  power consumption, and the precise accuracy/IoU trade-offs  associated with each optimization strategy. This remains a  critical direction for future work to fully validate the  suitability of these lightweight models for real-world,  autonomous UAV operations. Nonetheless, the current results  strongly support the feasibility of our overall approach,  combining accurate deep learning-based perception with  practical optimization for edge deployment.

robust feature extraction from complex drone-captured  scenes. The central contribution of this work, however, was  the successful optimization of this model into a lightweight  variant using post-training quantization. However, evaluation  of the lightweight model revealed a minimal inference time of  approximately 1ms on a local test system, alongside a low rate  of  farmland  boundary  missed-delineation,  indicating  successful optimization without substantial degradation in  predictive quality.

From a UAV systems perspective, the most critical  contribution is the exploration of pathways towards onboard  deployment. By applying tracing and quantization, we  demonstrated that the lightweight boundary detection model  can be optimized for resource-constrained edge computing  platforms commonly integrated with drones. This work  represents a foundational step towards enabling UAVs to  perform sophisticated visual analysis tasks autonomously and  in near real-time, significantly enhancing their utility as  intelligent remote sensing platforms. While our results  demonstrate the feasibility of creating a lightweight model for  agricultural boundary delineation and to further validate and  extend the capabilities of our model, future work will explore  the following key aspects:

The first step is to validate the model's promising  performance in a real-world operational context. While our  tests on a standard computing system confirmed the  effectiveness of the quantization methodology, deploying the  model on representative UAV-compatible edge hardware,  such as an NVIDIA Jetson Nano, will be crucial by providing  definitive metrics on in-flight latency, power consumption,  and memory usage for practical onboard deployment.  Secondly, a comprehensive comparison analysis against other  established lightweight architectures will be helpful in  understanding the performance and efficiency trade-offs  inherent to this specific task. Finally, to enhance the model's  generalizability and create a truly versatile tool, we will be  focusing on its capabilities beyond the challenging winter  conditions explored here. Future work will focus on training  and evaluating the model on datasets encompassing a wider  range of scenarios, including different seasons with full  vegetation, diverse geographical regions, and various crop  types.


## REFERENCES

[1] Colomina, Ismael, and Pere Molina. "Unmanned aerial systems for

photogrammetry and remote sensing: A review." ISPRS Journal of  photogrammetry and remote sensing 92 (2014): 79-97.  [2] Adil, Muhammad, et al. "UAV-assisted IoT applications, QoS

requirements and challenges with future research directions." ACM  Computing Surveys 56.10 (2024): 1-35.  [3] McEnroe, Patrick, Shen Wang, and Madhusanka Liyanage. "A survey

on the convergence of edge computing and AI for UAVs: Opportunities  and challenges." IEEE Internet of Things Journal 9.17 (2022): 15435-  15459.  [4] Ronneberger, Olaf, Philipp Fischer, and Thomas Brox. "U-net:

Convolutional networks for biomedical image segmentation." Medical  image computing and computer-assisted intervention–MICCAI 2015:  18th international conference, Munich, Germany, October 5-9, 2015,  proceedings, part III 18. Springer international publishing, 2015.  [5] He,  Kaiming,  et  al.  "Deep  residual  learning  for  image  recognition." Proceedings of the IEEE conference on computer vision  and pattern recognition. 2016.  [6] Jong, Maxwell, et al. "Improving field boundary delineation in

IV. CONCLUSION

This paper addressed the challenge of automated boundary  detection from high-resolution drone-acquired imagery,  particularly under difficult winter conditions. We proposed  and validated a ResNet-based U-Net deep learning model, for

ResUNets via adversarial deep learning." International Journal of  Applied Earth Observation and Geoinformation 112 (2022): 102877.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:47:02 UTC from IEEE Xplore.  Restrictions apply.

[7] Alizadeh, Mehdi, Parvin Ahmadi, and Masoumeh Azimzadeh.

[10] Liu, Jia, et al. "Boost precision agriculture with unmanned aerial

"Boundary Detection in Agricultural Fields Using a Residual U-Net++  Architecture."  2024  11th  International  Symposium  on  Telecommunications (IST). IEEE, 2024.  [8] Yang, Ruoyu, et al. "Detecting functional field units from satellite

vehicle remote sensing and edge intelligence: A survey." Remote  Sensing 13.21 (2021): 4387.  [11] Yunfan Zhang, Lei Shu, Kailiang Li, Ru Han, Tingting Hu, March 5,

2025, "Winter UAV Remote Sensing Dataset for Farmland Boundary  Detection: A High-Resolution Multi-Terrain Agricultural Image  Collection", IEEE Dataport, doi: https://dx.doi.org/10.21227/ta8w-  a151.  [12] Koonce, Brett. "ResNet 34." Convolutional neural networks with swift

images in smallholder farming systems using a deep learning based  computer vision approach: A case study from Bangladesh." Remote  Sensing Applications: Society and Environment 20 (2020): 100413.  [9] Fouda, Mostafa M., et al. "A lightweight hierarchical AI model for

for tensorflow: image recognition and dataset categorization.  Berkeley, CA: Apress, 2021. 51-61.

UAV-enabled edge computing with forest-fire detection use-  case." IEEE Network 36.6 (2022): 38-45.

Fig 3. Delineation of farmland boundaries using ResNet-based U-Net model.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:47:02 UTC from IEEE Xplore.  Restrictions apply.

Fig. 4. Lightweight model boundary delineation on a randomly selected test image.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:47:02 UTC from IEEE Xplore.  Restrictions apply.
