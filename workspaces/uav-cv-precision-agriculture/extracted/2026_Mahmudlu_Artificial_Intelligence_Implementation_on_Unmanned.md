---
workspace_id: SCI-000446
doi: 10.1007/978-3-032-07678-6_30
title: Artificial Intelligence Implementation on Unmanned Aerial Vehicle for Real-Time
  Detection
authors:
- family_name: Mahmudlu
  given_name: Firdovsi
  orcid: null
- family_name: Heybatov
  given_name: Dayanat
  orcid: null
- family_name: Samadov
  given_name: Samad
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:26:14.174666+00:00'
---

# Artificial Intelligence Implementation on Unmanned Aerial Vehicle for Real-Time Detection

Artiﬁcial Intelligence Implementation  on Unmanned Aerial Vehicle for Real-Time

Detection

Firdovsi Mahmudlu, Dayanat Heybatovenvelope symbol, and Samad Samadov

Air Transport Faculty, Department of Avionics, National Aviation Academy, Baku, Azerbaijan

{fmahmudlu,dayanat.heybatov}@naa.edu.az


## Abstract. This paper presents an AI-driven approach for real-time detection of

humans using an unmanned aerial vehicle (UAV). Leveraging the advanced capa-
bilities of YOLOv8 object detection model implemented with the PyTorch frame-
work on the Nvidia Jetson AGX Orin device, our methodology aims to enhance 
situational awareness and decision-making in critical missions. The implemen-
tation begins with the integration of the YOLOv8 model into the UAV system, 
enabling rapid and accurate detection of humans, allies, and enemies in dynamic 
environments.

The Nvidia Jetson AGX Orin device provides the necessary computational  power and efﬁciency to execute the YOLOv8 model seamlessly onboard the UAV,  ensuring real-time updates and reliable target identiﬁcation. Furthermore, we dis- cuss the technical speciﬁcations and advantages of using PyTorch with YOLOv8  on the Jetson AGX Orin device, highlighting the ease of development, deployment,  and scalability for artiﬁcial intelligence (AI) based applications in aerial surveil- lance and reconnaissance. Overall, our work contributes to advancing UAV-based  target detection capabilities, enabling efﬁcient detection of humans, allies, and ene- mies in real-time scenarios, thereby enhancing mission success and operational  effectiveness in dynamic environments.

Keywords: YOLOv8 cdot unmanned aerial vehicle (UAV) cdot Artiﬁcial Intelegence cdot human detection cdot deep learning

Nomenclature

UAV Unmanned aerial vehicle  YOLO You only look once  AI Artiﬁcial intelegence  CUDA Compute Uniﬁed Device Architecture  mAP Mean Average Precision

© The Author(s), under exclusive license to Springer Nature Switzerland AG 2026  T. H. Karakoc et al. (Eds.): ISUDEF 2024, SA, pp. 166–170, 2026.  https://doi.org/10.1007/978-3-032-07678-6_30

Artiﬁcial Intelligence Implementation 167

1  Introduction

Unmanned aerial vehicles (UAVs) have undergone rapid development in the consumer  market in recent years. Originally used for military purposes, UAVs are now applied in  a variety of industries. Owing to technological advancements, this development in UAV  technology has provided the consumer market with smaller, more economical, more  advanced, and safer UAVs (Ma et al., 2023). With the increase of computing power and  the emergence of large-scale labeled sample data sets, a deep neural network has been  widely studied for its fast, scalable, and end-to-end learning framework. Especially, com- pared with the traditional methods, the convolutional neural network (CNN) model has  been signiﬁcantly improved in image classiﬁcation and semantic segmentation(Wang,  2021). In this article, we delve into our journey of implementing AI on a UAV, speciﬁcally  utilizing a Jetson AGX Orin, to achieve real-time detection of Humans, Friends (allies),  and Enemies (adversaries). Our project commenced with the meticulous creation of a  specialized dataset on Roboﬂow, where images were annotated to teach the AI model  to distinguish between Humans, Friends, and Enemies. Choosing the Jetson AGX Orin  for our UAV platform was a strategic decision, considering its computational prowess  and suitability for real-time AI tasks. Compared to its previous generations the latest  YOLOv8 demonstrates more powerful performance in terms of accuracy and speed and  introduces the best-performing model (Dong & Du, 2024). By sharing our experiences  and insights, we aim to contribute to the continuous evolution of UAV technology and  its transformative potential in diverse domains.

2  Dataset Preparation and Training

In the dataset preparation phase, we meticulously curated a collection of 3350 images,  ensuring a diverse and comprehensive representation of real-world scenarios. To enhance  the robustness and generalization of our AI model, we applied a series of augmenta- tions to the images. These augmentations included ﬂipping, cropping, rotation, adjusting  hue, brightness, and exposure levels, as well as introducing controlled noise variations.  Furthermore, to distinguish between Friends (allies) and Enemies (adversaries), a spe- ciﬁc criterion was established. Friends were identiﬁed as soldiers wearing blue helmets  or berets, while any other soldiers were categorized as Enemies. This classiﬁcation  scheme ensured that the AI model could accurately differentiate between different enti- ties, contributing to more precise real-time detection capabilities. Additionally, to meet  the model’s input requirements, all images were resized to a standardized 640 × 640  resolution. This uniformity not only optimized data processing but also ensured compat- ibility with the YOLOv8 model’s input speciﬁcations, further enhancing the efﬁciency  and accuracy of our real-time detection system on the UAV platform.

The training phase of our AI model was conducted using the Ultralytics hub, with  a focus on the YOLOv8s architecture Fig. 1. This choice of architecture, known for its  balance of speed and accuracy, was complemented by speciﬁc conﬁgurations tailored  to our objectives. During the training phase, we ran the model through 150 epochs,  allowing it to progressively learn from the dataset over multiple iterations. This extended  training period ensured that the model gained a deep understanding of the data, improving

168 F. Mahmudlu et al.

its ability to detect Humans, Friends, and Enemies accurately. To optimize training  efﬁciency, we worked with a batch size of 64. This batch size parameter allowed the  model to process data in manageable chunks, enhancing computational performance and  training convergence. By ﬁne-tuning these conﬁgurations, we aimed to maximize the  model’s detection capabilities while maintaining computational effectiveness, setting  the stage for real-world deployment on our UAV platform (Fig. 1).

Fig. 1. Ultralytics YOLOv8.

The culmination of our training efforts yielded an impressive mean average precision  (mAP) score of 90.3 Fig. 2. This metric serves as a robust indicator of our model’s  accuracy in detecting and precisely localizing Humans, Friends, and Enemies in dynamic  environments—a critical aspect for informed decision-making and situational awareness  during UAV missions.

Fig. 2. Achieved mean Average Precision.

3  Inference

In the inference phase, we deployed our trained model on the Jetson AGX Orin platform  using PyTorch with CUDA acceleration, optimizing computational performance for  real-time detection tasks.

Artiﬁcial Intelligence Implementation 169

The Nvidia Jetson AGX Orin is a powerful embedded computing platform designed  for AI and deep learning applications. It features a high-performance system-on-module  (SoM) architecture with multiple GPU cores and a dedicated AI accelerator, making  it ideal for running complex AI algorithms efﬁciently on edge devices such as UAVs.  Jetson AGX Orin is known for its computational capabilities, low power consumption,  and support for CUDA and TensorRT, making it a popular choice for AI implementation  in resource-constrained environments.

PyTorch, on the other hand, is a popular open-source deep learning framework known  for its ﬂexibility, ease of use, and dynamic computation graph. It provides a Python-based  interface that simpliﬁes the development and deployment of AI models, including neural  networks for tasks like image recognition, object detection, and natural language pro- cessing. PyTorch’s compatibility with CUDA enables seamless integration with Nvidia  GPUs, including the Jetson AGX Orin, for accelerated training and inference (Redmon,  2016).  As a result of inference on the Jetson AGX Orin platform using PyTorch with CUDA  acceleration, we achieved an impressive processing speed of 20 frames per second (fps).  Which is descent for detection purposes Fig. 3.

Fig. 3. Inference Result.

By integrating TensorRT into our AI pipeline in the future, we aim to achieve  enhanced performance and responsiveness, particularly in dynamic and demanding  operational environments. TensorRT’s advanced optimizations, including layer fusion,  precision calibration, and efﬁcient memory management, have the potential to unlock  additional computational capabilities and improve the overall efﬁciency of our AI-driven  UAV system on the Jetson AGX Orin platform.

170 F. Mahmudlu et al.

4  Conclusion

In conclusion, our study has showcased the remarkable potential of integrating advanced  AI methodologies into UAV systems for real-time detection of humans, allies, and ene- mies. By implementing YOLOv8 with the PyTorch framework on the Nvidia Jetson  AGX Orin device, we have signiﬁcantly elevated the capabilities of our UAV platform.  Future directions for our research could focus on further reﬁning the AI models for  improved accuracy and scalability. Additionally, exploring integration possibilities with  other sensor technologies and data fusion techniques could lead to more comprehensive  and robust UAV-based surveillance and reconnaissance systems. In summary, our work  underscores the transformative potential of AI-driven technologies in enhancing UAV  capabilities for target detection, surveillance, and mission-critical operations, paving the  way for advancements in defense, security, and disaster response applications.


## References

Dong, C., Du, G.: An enhanced real-time human pose estimation method based on modiﬁed

YOLOv8 framework. Sci. Rep. 14, 8012 (2024). https://www.nature.com/articles/s41598-024- 58146-z  Ma, M.-Y., Shen, S.-E., Huang, Y.-C.: UAV visual landing recognition with YOLO’s object detec-

tion by onboard edge computing. Sensors 23(21), 8999 (2023). https://www.mdpi.com/1424- 8220/23/21/8999  Redmon, J., Divvala, S., Girshick, R., Farhadi, A.: You only look once: uniﬁed, real-time object

detection [Conference paper]. Proceedings of the IEEE Conference on Computer Vision and  Pattern Recognition (CVPR), pp. 779–788 (2016). https://www.cvfoundation.org/openaccess/  content_cvpr_2016/html/Redmon_You_Only_Look_CVPR_2016_paper.html  Wang, S.: Research towards Yolo-series algorithms: Comparison and analysis of object detection

models for real-time UAV applications. J. Phys. Conf. Ser. 1948, 012021 (2021). https://doi.  org/10.1088/1742-6596/1948/1/012021
