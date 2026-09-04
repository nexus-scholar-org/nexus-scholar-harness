---
workspace_id: SCI-000225
doi: 10.1109/agro-geoinformatics66479.2025.11136213
title: 'Adapting Vision-Language Models for Precision Agriculture: A Study on Crop
  Segmentation based on UAV Remote Sensing Data'
authors:
- family_name: Bie
  given_name: Yuhui
  orcid: null
- family_name: Xu
  given_name: Guowei
  orcid: null
- family_name: Wang
  given_name: Yaojun
  orcid: null
year: 2025
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:40.789654+00:00'
---

# Adapting Vision-Language Models for Precision Agriculture: A Study on Crop Segmentation based on UAV Remote Sensing Data

Adapting Vision-Language Models for Precision  Agriculture: A Study on Crop Segmentation  based

on UAV Remote Sensing Data

2025 13th International Conference on Agro-Geoinformatics (Agro-Geoinformatics) | 979-8-3315-6853-5/25/$31.00 ©2025 IEEE | DOI: 10.1109/Agro-Geoinformatics66479.2025.11136213

Yuhui Bie  College of Information and Electrical

Guowei Xu  College of Information and Electrical

Yaojun Wang*  College of Information and Electrical

Engineering  China Agricultural University

Engineering  China Agricultural University

Engineering  China Agricultural University

Beijing, China

Beijing, China

Beijing, China  wangyaojun@cau.edu.cn


## Abstract—With increasing global food security challenges,

agricultural remote sensing image analysis has become 
particularly important for improving production efficiency and 
resource utilization in precision agriculture. However, 
traditional crop segmentation methods for UAV remote sensing 
images rely heavily on large amounts of labeled data and 
specialized deep learning architectures, which pose significant 
challenges for practical agricultural applications due to high 
annotation costs and limited model generalization. Although 
general vision-language models (VLMs) have demonstrated 
remarkable capabilities in natural image understanding, their 
effectiveness in processing specialized agricultural remote 
sensing data, particularly for precise crop segmentation tasks, 
remains largely unexplored.

I. INTRODUCTION

Benefiting from the development of a new generation of  earth observation satellites and unmanned aerial vehicle  (UAV) technologies, the number of high-quality remote  sensing images has increased substantially [1]. In agriculture,  UAV-based remote sensing technologies are increasingly  used to improve agriculture productivity while reducing  drudgery, inspection time, and crop management cost,  covering large areas in a matter of a few minutes [2]. Using  remote sensing images for crop classification and  segmentation is an important application in precision  agriculture, as semantic segmentation enables fine-grained  understanding of agricultural scenes by providing pixel-level  annotations for different crop types [3]. However, despite the  existence of a large amount of unannotated remote sensing  data, routine supervised learning methods are limited by data  annotation requirements, making it difficult to fully utilize  these data for agricultural applications.

This research proposes a novel approach that adapts  multimodal large language models for crop segmentation in  UAV remote sensing images by reformulating the segmentation  task as a conversational format. Our method transforms  traditional pixel-level segmentation into a text-based coordinate  prediction task, where segmentation masks are converted to  polygon coordinates and represented in XML format. To  address the unique characteristics of agricultural remote  sensing data, we designed two types of conversational prompts:  general object segmentation and crop-specific segmentation.

Traditional semantic segmentation methods for remote  sensing images rely heavily on deep learning approaches such  as  Convolutional  Neural  Networks  (CNNs),  U-Net  earchitectures, and specialized encoder-decoder models [4,5].  These methods typically require large amounts of agricultural  data to train deep learning models, and the rapid access to  crop data has long been a challenge for research organizations  and industrial companies worldwide [6]. While these  approaches have demonstrated effectiveness in crop  identification tasks, they are often labor-intensive, time- consuming, and require extensive manual annotation  processes [7]. Furthermore, the success of deep learning  relies on complex network structures and large amounts of  labeled data, where obtaining large amounts of labeled data  in remote sensing is both time-consuming and expensive,  which limits the application of deep learning in agricultural  fields [8].

Methodologically,  we  introduce  a  coordinate-to-text  conversion strategy that transforms segmentation labels into  structured XML tags containing polygon coordinates, enabling  VLMs to perform segmentation through natural language  generation. We systematically evaluate four state-of-the-art  vision-language  models  (Qwen2-VL-7B,  Qwen2.5-VL-7B,  LLaVA-1.5-7B, and LLaMA3-LLaVA-Next-8B) using Low- Rank Adaptation (LoRA) fine-tuning techniques that selectively  optimize only the language model components while keeping the  visual encoders frozen.

Experimental validation demonstrates that adapted VLMs  can effectively perform crop segmentation tasks with varying  degrees of success across different crop types. Qwen2-VL  achieves the best overall performance with an F1-score of 49.16%  and IoU of 46.61%, significantly outperforming other models.  Notably, tobacco segmentation shows superior results (F1:  78.42%, IoU: 75.64%) compared to corn and barley, indicating  crop-specific adaptation capabilities. The results reveal that  while VLM-based approaches may not yet match specialized  segmentation models in absolute accuracy, they offer unique  advantages in few-shot learning scenarios and provide a  promising foundation for developing more generalizable  agricultural remote sensing solutions.

The remarkable achievements of ChatGPT and GPT-4  have sparked a wave of interest and research in the field of  large language models for Artificial General Intelligence  (AGI), providing intelligent solutions close to human  thinking and enabling us to use general artificial intelligence  to solve problems in various applications [9]. Recently, the  advancements in Vision-Language Models (VLMs) have  pushed this enthusiasm to new heights, as VLMs frame tasks  as generative models and align language with visual  `problems [10]. However, in remote sensing, the scientific  literature on the implementation of AGI remains relatively  scant, as existing AI-related research primarily focuses on

Keywords—Remote sensing, vision-language models, crop  segmentation, precision agriculture, UAV imagery.

979-8-3315-6853-5/25/$31.00 ©2025 IEEE

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:38:40 UTC from IEEE Xplore.  Restrictions apply.

visual understanding tasks while neglecting the semantic  understanding of the objects and their relationships [11].

This is where vision-language models excel, as they  enable reasoning about images and their associated textual  descriptions, allowing for a deeper understanding of the  underlying semantics. Vision-language models can go  beyond visual recognition of remote sensing images, model  semantic relationships, and generate natural language  descriptions of the image [12]. The remote sensing field has  embraced this new trend and introduced several VLM-based  remote sensing methods that have demonstrated promising  performance and enormous potential, including EarthGPT  [13], Falcon [14], GeoChat [15], RemoteCLIP [16], and  RSGPT [17].

Despite these advances, current VLM applications in  remote sensing primarily focus on high-level tasks such as  image captioning, visual question answering, and scene  classification, with limited exploration of pixel-level  understanding tasks like semantic segmentation. The unique  characteristics of agricultural remote sensing data, including  diverse crop types, varying growth stages, and complex field  boundaries, pose significant challenges for adapting general- purpose VLMs to precise crop segmentation tasks. Moreover,  the  conventional  approach  of  training  specialized  segmentation models from scratch requires substantial  computational resources and extensive labeled datasets,  which may not be readily available in many agricultural  contexts.

Fig. 1. Study area location map showing Xingren City in Guizhou Province,  China.

II. MATERIALS

A. Study Area and Data Acquisition

In this study, we used a high-resolution UAV remote  sensing dataset covering crop-growing areas in Xingren City,  Guizhou Province, China. The study area is located in the  southwestern region of China, characterized by diverse  topographical features and typical subtropical agricultural  landscapes that are representative of mountainous farming  systems in this region (Fig. 1). The dataset consists of four  large-scale remote sensing images captured during the peak  growing season, each with extremely high resolution, ranging  in size from 18,576 × 68,363 pixels to 55,128 × 49,447 pixels,  with an average file size of approximately 1.8 GB per image.  These images were acquired using commercial UAV  platforms equipped with high-resolution RGB sensors,  providing detailed spectral and spatial information essential  for accurate crop identification and segmentation tasks.

To address these limitations, this research proposes a  novel approach that adapts multimodal large language  models for crop segmentation in UAV remote sensing images  by reformulating the segmentation task as a conversational  format. Unlike traditional pixel-level segmentation methods,  our approach transforms segmentation masks into structured  text representations using polygon coordinates, enabling  VLMs to perform segmentation through natural language  generation. This paradigm shift offers several advantages:  reduced dependency on large-scale labeled datasets,  enhanced generalization capabilities across different crop  types and geographical regions, and the potential for few-shot  learning in agricultural applications.

B. Dataset Preprocessing and Preparation

Due to the large size of these original images, they cannot  be directly input into neural networks for processing.  Therefore, we employed a sliding window cropping strategy  to divide them into multiple 512 × 512 pixel sub-images,  which represents an optimal balance between computational  efficiency and spatial context preservation for crop  segmentation tasks. After cropping, the dataset contained a  total of 11,750 sub-images, with 9,413 images allocated to the  training set and 2,337 to the test set, maintaining a training-to- test ratio of approximately 4:1. This dataset provides abundant  remote sensing imagery for model training and testing,  ensuring the reliability and generalization capability of the  classification task.

The main contributions of this work are: (1) We propose  the first systematic study of adapting vision-language models  for crop segmentation in UAV remote sensing images  through a text-based coordinate prediction approach. (2) We  design a novel coordinate-to-text conversion strategy that  transforms traditional segmentation labels into structured  XML format, enabling VLMs to understand and generate  segmentation results through natural language processing. (3)  We conduct comprehensive experiments comparing four  state-of-the-art vision-language models on a challenging  agricultural dataset containing three major crop types. (4) We  provide detailed analysis of crop-specific performance  differences and discuss the potential and limitations of VLM- based approaches for agricultural remote sensing applications.

The original dataset contains pixel-level annotations for  three major crop types commonly cultivated in the study  region: corn (Zea mays), barley (Hordeum vulgare), and  tobacco (Nicotiana tabacum). Each 512 × 512 remote sensing  image corresponds to a single-channel PNG format label file,  where different pixel values represent different crop  categories. To adapt these traditional segmentation labels for  vision-language model training, we developed a novel  coordinate-to-text conversion methodology that transforms  pixel-level masks into structured text representations.

C. Data Format Conversion for VLM Training

To  enable  vision-language  models  to  perform  segmentation tasks through natural language generation, we

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:38:40 UTC from IEEE Xplore.  Restrictions apply.

converted the traditional pixel-level segmentation masks into  polygon coordinate format suitable for conversational  training. The conversion process involved several key steps:  First, we applied appropriate thresholding techniques to  process pixel boundaries and extract contour information  from the segmentation masks. Second, we simplified the  extracted contours into polygon representations using  coordinate sequences. Finally, we wrapped each crop region  with  XML-style  tags  containing  the  corresponding  coordinate sequences in the format of (x,y)(x,y)(x,y)...

The processed data format enables direct integration with  large language model training frameworks. Each training  sample consists of an image-text pair where the image  contains the original 512 × 512 UAV remote sensing data,  and the text represents the segmentation targets in structured  coordinate format. For example, a typical data entry includes  the image path, image dimensions, and the corresponding  label containing XML-wrapped coordinate sequences for  each identified crop region.

D. Instruction Dataset Construction

To  facilitate  conversational  training  for  crop  segmentation tasks, we constructed instruction-following  datasets with two types of prompts designed to evaluate  different aspects of VLM performance. The first type uses  general object segmentation prompts: "Segment out all  objects in the image," which tests the model's ability to  identify and segment all crop regions without specific  category guidance. The second type employs crop-specific  segmentation prompts: "Segment out all {crop} in the  image," where {crop} is replaced with specific crop names  (corn, barley, or tobacco), enabling evaluation of the model's  capacity for targeted crop identification and segmentation.

Fig. 2. Example of fine-tuning data format for vision-language model  training.

III. METHODS

A. Vision-Language Model Architecture

To address the challenge of adapting multimodal large  language models for crop segmentation tasks, we selected  four state-of-the-art vision-language models with varying  parameter scales and capabilities (Table 1). These models  represent  the  current  frontier  in  vision-language  understanding and provide a comprehensive evaluation  framework for our proposed approach.

The final training dataset was formatted according to  standard conversational AI training protocols, with each  sample containing a "messages" field including user prompts  and assistant responses, along with the corresponding image  paths. This format ensures compatibility with modern vision- language model training frameworks while maintaining the  spatial precision required for accurate crop segmentation (Fig.  2). The dataset split maintains the original 4:1 training-to-test  ratio, with 10% of the training data reserved for validation  purposes to monitor model performance during fine-tuning.

The fundamental architecture of vision-language models  follows a unified design paradigm that effectively integrates  visual and textual information processing capabilities [18].  As illustrated in Fig. 3, the network architecture consists of  three primary components: a pre-trained visual encoder, a  projection layer, and a large language model. The visual  encoder processes input images to extract high-dimensional  visual features, while the projection layer serves as a bridge  to align visual representations with the language model's  embedding space. The large language model then generates  textual responses based on the integrated multimodal  representations.

TABLE I.   VISION-LANGUAGE MODELS USED IN THIS STUDY.

Model  Parameters  Release

Year  Reference

Specifically, for an input image Xv, the pre-trained visual  encoder (typically based on CLIP ViT architectures) extracts  visual features Zv = g(Xv). A trainable projection matrix W  then converts these visual features into language embedding  tokens Hv that have the same dimensionality as the word  embedding space in the language model: Hv = W · Zv. This  projection scheme enables seamless integration of visual  information into the language model's processing pipeline,  allowing the model to generate text-based responses that  incorporate visual understanding.

Qwen2-VL-7B  7B  2024  [19]  Qwen2.5-VL-7B  7B  2024  [20]  LLaVA-1.5-7B  7B  2023  [18]  LLaMA3- LLaVA-Next-8B  8B  2024  -

B. Parameter-Efficient Fine-tuning Strategy

Given the substantial computational requirements of full  model fine-tuning for large-scale vision-language models, we  employed Low-Rank Adaptation (LoRA) as our parameter- efficient fine-tuning strategy. LoRA enables effective model

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:38:40 UTC from IEEE Xplore.  Restrictions apply.

adaptation by introducing trainable low-rank decomposition  matrices into specific layers of the large language model  while keeping the majority of pre-trained parameters frozen  (Fig. 4). This approach significantly reduces the number of  trainable parameters and computational overhead while  maintaining competitive performance.

specifically targeting the query and value projection matrices.  The visual encoder weights remained frozen throughout the  training process to preserve the robust visual feature  extraction capabilities learned during pre-training. Only the  projection layer weights W and the LoRA adapter parameters  were updated during fine-tuning, resulting in a dramatic  reduction in trainable parameters compared to full model  fine-tuning.

In our implementation, LoRA adapters were applied to  the attention layers of the language model component,

Fig. 3. Architecture of vision-language models for crop segmentation tasks.

model's embedding space. The projection matrix W was  trained while keeping both the visual encoder and language  model weights frozen.

C.  Coordinate-to-Text Conversion Methodology

Our approach transforms traditional pixel-level segment  into a text generation task by converting segmentation masks  into structured coordinate representations. The conversion  process involves several key steps:

In the second stage, we conducted end-to-end fine-tuning  using our crop segmentation dataset. During this phase, we  kept the visual encoder frozen while updating both the  projection layer and the language model parameters through  LoRA adapters. The training objective was to maximize the  likelihood of generating correct coordinate sequences given  the input image and segmentation prompt.

local and global features of the image as well as temporal  contextual relationships to recover the reflectance of the  analyzed pixels across all masked timesteps in order to  capture high-level spatial and temporal dependencies in the  data and learn discriminative features.

The training was conducted using conversational formats  with two types of instructions: general object segmentation  ("Segment out all objects in the image") and crop-specific  segmentation ("Segment out all {crop} in the image"). Each  training sample consisted of an image-text pair where the  model was expected to generate the appropriate XML- formatted coordinate sequences as responses.

After pre-training, the network can be adapted to the crop  classification task through fine-tuning. The fine-tuning  process involves supervised learning on task-relevant data to  update the model parameters to solve a specific task.

1) Contour Extraction

For each crop category in the segmentation mask, we  apply contour detection algorithms to identify the boundary  pixels of connected regions. These contours are then  simplified using polynomial approximation to reduce  coordinate redundancy while preserving shape accuracy.

2) Coordinate Formatting

The simplified contours are converted into sequences of  (x,y) coordinate pairs and wrapped with XML-style tags to  indicate the corresponding crop type.

3) Text Integration

Fig. 4. LoRA fine-tuning strategy illustration.

The complete segmentation result is represented as a  concatenated string containing all crop regions with their  respective coordinate sequences, enabling direct integration  with language model training frameworks.

IV. RESULTS

A. Training Configuration

D. Training Protocol

The training process was conducted using a carefully  optimized parameter configuration to ensure effective fine- tuning while maintaining computational efficiency. Table 2  presents the key training hyperparameters employed across  all model experiments. We utilized the Adam optimizer with

We adopted a two-stage training approach adapted from  the standard vision-language model training paradigm. In the  first stage, we performed feature alignment training to ensure  compatibility between visual features and the language

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:38:40 UTC from IEEE Xplore.  Restrictions apply.

a learning rate of 1.0×10⁻⁴ and implemented a cosine learning  rate scheduler with a warmup ratio of 0.1 to ensure stable  training convergence. The LoRA rank was set to 8, targeting  all applicable layers to balance parameter efficiency with  model expressiveness. Training was performed for 3 epochs  with a per-device batch size of 1 and gradient accumulation  steps of 8, resulting in an effective batch size of 8. Mixed  precision training (bf16) was enabled to accelerate  computation while maintaining numerical stability.

predicted crop pixels (overlap area/predicted area), recall  indicates the ratio of correctly identified crop pixels to all  ground truth crop pixels (overlap area/ground truth area), and  IoU measures the overlap between predicted and ground truth  regions relative to their union (overlap area/union area).  Importantly, if a model predicted regions where no crops  should exist, both precision and recall were set to zero for that  prediction. Similarly, if ground truth crop regions were  completely missed by the model, the corresponding metrics  were also assigned zero values.

TABLE II.  TRAINING CONFIGURATION PARAMETERS

The experimental results reveal significant performance  variations across different models and crop types. Qwen2- VL-7B achieved the highest overall performance with an F1- score of 0.4916 and IoU of 0.4661, demonstrating superior  capability in adapting to the coordinate-based segmentation  task. Notably, all models exhibited substantially better  performance on tobacco segmentation compared to corn and  barley, with Qwen2-VL-7B achieving an impressive F1- score of 0.7842 for tobacco identification.

Parameter  Value

Optimizer  AdamW

Learning Rate  1.0×10⁻⁴

Training Epochs  3

LR Scheduler  Cosine

The performance hierarchy clearly shows Qwen2-VL-7B >  Qwen2.5-VL-7B > LLaVA-1.5-7B > LLaMA3-LLaVA- Next-8B, indicating that the Qwen series models demonstrate  better adaptation capabilities for this specific agricultural  remote sensing task. The consistent pattern of tobacco  achieving the highest segmentation accuracy across all  models suggests that this crop type possesses more distinctive  visual characteristics that are more readily captured by the  vision-language models' coordinate prediction mechanism.

Warmup Ratio  0.1

Precision  bf16

B. Quantitative Performance Analysis

We evaluated the performance of four vision-language  models on our crop segmentation dataset using standard  semantic segmentation metrics rather than conventional  language model evaluation metrics. The evaluation focused  on precision, recall, F1-score, and Intersection over Union  (IoU) calculated at the pixel level after converting the  predicted coordinate sequences back to segmentation masks.

V. CONCLUTION

In this paper, we focus on two issues: first, how to make  the model learn and fuse local and global features of the  image; second, how to make the model learn generic features  from remote sensing image data through masking

The metrics were computed as follows: precision  represents the ratio of correctly predicted crop pixels to all

TABLE III.   PERFORMANCE COMPARISON OF DIFFERENT VISION-LANGUAGE MODELS ON CROP SEGMENTATION.

Model  Crop Type  Precision  Recall  F1-Score  IoU

Corn  0.3535  0.319  0.3266  0.2801

Barley  0.4338  0.3882  0.4000  0.3673

Qwen2-VL-7B

Tobacco  0.8081  0.7798  0.7842  0.7564

Overall  0.5325  0.4799  0.4916  0.4661

Corn  0.2534  0.2211  0.2308  0.1909

Barley  0.3426  0.2908  0.3065  0.2718

Qwen2.5-VL-7B

Tobacco  0.7531  0.7088  0.7229  0.6873

Overall  0.4487  0.3841  0.4036  0.3726

Corn  0.1985  0.1866  0.1903  0.1433

Barley  0.2884  0.2625  0.2707  0.2316

LLaVA-1.5-7B

Tobacco  0.5766  0.5439  0.5541  0.5049

Overall  0.3584  0.3222  0.3332  0.2914

Corn  0.1263  0.1164  0.1195  0.0934

Barley  0.1738  0.16  0.1643  0.1396

LLaMA3-LLaVA-Next-8B

Tobacco  0.4285  0.3947  0.4098  0.3542

Overall  0.2429  0.2237  0.2312  0.1957

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:38:40 UTC from IEEE Xplore.  Restrictions apply.

[8] M. Kerkech, A. Hafiane, and R. Canals, "Deep leaning approach with

strategy and time series information processing. To this end,  we propose the pre-training AgriST-Trans method from the  Sentinel-2 time series in a self-supervised manner. Speci- fically, generic features in remote sensing images are lear- ned by masking the spectral and spatial dimensions, learning  the local and global features of the images using lightweight  CNN and ViT, and then capturing the temporal contextual  relationships through the Transformer coding module. After  the pre-training is completed, it can be fine-tuned on labeled  sparse datasets to adapt to downstream tasks and reduce the  dependence on large-scale labeled data.

colorimetric spaces and vegetation indices for vine diseases detection  in UAV images," Computers and Electronics in Agriculture, vol. 155,  pp. 237-243, 2018.  [9] X. Li, C. Wen, Y. Hu, and N. Yuan, "Vision-Language Models in

Remote Sensing: Current Progress and Future Trends," arXiv preprint  arXiv:2305.05726, 2023.  [10] L. Li et al., "Advancements in Visual Language Models for Remote

Sensing: Datasets, Capabilities, and Enhancement Techniques,"  Remote Sensing, vol. 17, no. 1, p. 162, 2025.  [11] W. Zhang, M. Cai, T. Zhang, Y. Zhuang, and X. Mao, "Vision-

Language Models in Remote Sensing: Current Progress and Future  Trends," IEEE Transactions on Geoscience and Remote Sensing, vol.  12, pp. 32-66, 2024.  [12] D. Muhtar, Z. Li, F. Gu, X. Zhang, and P. Xiao, "LHRS-Bot:

The experimental results show that the proposed pre- training scheme performs well in the downstream remote  sensing crop classification task, and the performance of the  model in the downstream task can be significantly improved  by pre-training. Since the self-supervised learning frame- work used in this study does not require a large number of  manually labeled labels in the pre-training phase, it can  significantly reduce the remote sensing labeling effort and is  easily scalable to specific downstream tasks.

Empowering Remote Sensing with VGI-Enhanced Large Multimodal  Language Model," in Proc. European Conference on Computer Vision,  vol. 15132, pp. 440-457, 2024.  [13] W. Zhang, M. Cai, T. Zhang, Y. Zhuang, and X. Mao, "EarthGPT: A

Universal Multi-modal Large Language Model for Multi-sensor Image  Comprehension in Remote Sensing Domain," arXiv preprint  arXiv:2401.16822, 2024.  [14] Y. Kelu et al. , "Falcon: A remote sensing vision-language foundation

model," arXiv preprint arXiv:2503.11070, 2025.   [15] K. Kartik, M. Danish, M. Naseer, A. Das, S. Khan, and F. Shahbaz

The pre-training strategy can significantly enhance the  performance of remote sensing crop classification and is also  applicable to other downstream tasks. However, there are  still numerous directions to explore for pre-training on  remotely sensed time series data. For instance, there is  potential to extend remote sensing time series data sources to  integrate both optical and radar data. Additionally,  researching methods to learn richer and more effective  features by incorporating multi-scale images presents a  valuable opportunity for further investigation.

Khan, "Geochat: Grounded large vision-language model for remote  sensing," Proceedings of the IEEE/CVF Conference on Computer  Vision and Pattern Recognition, pp. 27831-27840, 2024.   [16] F. Liu et al., "Remoteclip: A vision language foundation model for

remote sensing," IEEE Transactions on Geoscience and Remote  Sensing, vol. 62, pp. 1-16, 2024.   [17] Hu, Yuan et al, "Rsgpt: A remote sensing vision language model and

benchmark," ISPRS Journal of Photogrammetry and Remote  Sensing, vol. 224, pp. 272-286, 2025.   [18] H. Liu, C. Li, Q. Wu, and Y. J. Lee, "Visual instruction tuning,"

Advances in neural information processing systems, vol. 36, pp.  34892-34916, 2023.  [19] P. Wang et al., "Qwen2-vl: Enhancing vision-language model's

ACKNOWLEDGEMENTS

This research was supported by the National Key  Research and Development Program (2023yfd1701000,  2024YFD2000805), and Pinduoduo-China Agricultural  University Research Fund (PC2024A01003), and Beijing  Rural Revitalization Agricultural Science and Technology  Project (NY2502020025).

perception of the world at any resolution," arXiv preprint  arXiv:2409.12191, 2024.  [20] S. Bai et al., "Qwen2.5-vl technical report," arXiv preprint

arXiv:2502.13923, 2025.  [21] H. Liu, C. Li, Y. Li, and Y. Lee, "Improved baselines with visual

instruction tuning," In Proceedings of the IEEE/CVF Conference on  Computer Vision and Pattern Recognition, pp. 26296-26306, 2024.


## REFERENCES

[1] A. Bouguettaya et al., "Deep learning techniques to classify

agricultural crops through UAV imagery: a review," Neural  Computing and Applications, vol. 34, pp. 9511-9536, 2022.  [2] J. Cheng, C. Deng, Y. Su, Z. An, and Q. Wang, "Methods and datasets

on semantic segmentation for Unmanned Aerial Vehicle remote  sensing images: A review," ISPRS Journal of Photogrammetry and  Remote Sensing, vol. 211, pp. 1-34, 2024.  [3] C.-Y. Hung, Z. Xu, and S. Sukkarieh, "Feature learning based

approach for weed classification using high resolution aerial images  from a digital camera mounted on a UAV," Remote Sensing, vol. 6,  no. 12, pp. 12676-12696, 2014.  [4] L. Osco et al., "Semantic segmentation using deep learning with

vegetation indices for rice lodging identification in multi-date UAV  visible images," Remote Sensing, vol. 12, no. 4, p. 633, 2020.  [5] X. Li, Y. Li, J. Ai, Z. Shu, J. Xia, and Y. Xia, "Semantic segmentation

of UAV remote sensing images based on edge feature fusing and  multi-level upsampling integrated with Deeplabv3+," PLOS ONE, vol.  18, no. 1, p. e0279097, 2023.  [6] S. Liu, J. Cheng, L. Liang, H. Bai, and W. Dang, "Light-weight

semantic segmentation network for UAV remote sensing images,"  IEEE Journal of Selected Topics in Applied Earth Observations and  Remote Sensing, vol. 14, pp. 8287-8296, 2021.  [7] A. Milioto, P. Lottes, and C. Stachniss, "Real-time semantic

segmentation of crop and weed for precision agriculture robots  leveraging background knowledge in CNNs," in Proc. IEEE  International Conference on Robotics and Automation, Brisbane,  Australia, pp. 2229-2235, 2018.

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:38:40 UTC from IEEE Xplore.  Restrictions apply.
