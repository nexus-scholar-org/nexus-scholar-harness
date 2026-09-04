---
workspace_id: SCI-001376
doi: 10.37396/jsc.v8i2.555
title: 'Mini Drone-Based Precision Agriculture for Indonesian MSMEs: A Low-Cost AI-Assisted
  Monitoring System'
authors:
- family_name: Hermanus
  given_name: Davy Ronald
  orcid: null
- family_name: Supangkat
  given_name: S.
  orcid: null
- family_name: Hidayat
  given_name: Fadhil
  orcid: null
year: 2025
extraction_engine: pymupdf
extracted_at: '2026-09-04T01:48:54.058209+00:00'
---

# Mini Drone-Based Precision Agriculture for Indonesian MSMEs: A Low-Cost AI-Assisted Monitoring System

Davy et al. / Jurnal Sistem Cerdas (2025) Vol 08-No 02  eISSN : 2622-8254 Page : 203 - 215

Mini Drone-Based Precision Agriculture for  Indonesian MSMEs: A Low-Cost AI-Assisted

Monitoring System

Davy Ronald Hermanus   1)School of Computer Science  Bina Nusantara University  Computer Science @Bandung

Suhono Harso Supangkat  1)School of Electrical and  Informatics Engineering           Bandung Institute of Technology

Fadhil Hidayat   1)School of Electrical and  Informatics Engineering           Bandung Institute of Technology

Bandung, Indonesia 2

Jakarta,Indonesia                 2) School of Electrical and  Informatics Engineering           Bandung Institute of Technology

Bandung, Indonesia   2)Smart City & Community

)Smart City & Community

Innovation Center                Bandung Institute of Technology

Innovation Center                Bandung Institute of Technology

Bandung, Indonesia   3)Smart City & Community

Bandung, Indonesia

Bandung, Indonesia  fadhil_hidayat@itb.ac.id

suhono@itb.ac.id

Innovation Center                Bandung Institute of Technology

Bandung, Indonesia

Abstract— This research introduces a cost-effective drone-based agricultural monitoring system targeted  at Indonesia’s smallholder farming enterprises (MSMEs). By leveraging mini drones (DJI Mini 2 SE) and  lightweight AI models, farmers can segment land, detect vegetation health, and count crops using simple  RGB video analysis. The system utilizes a mobile-to-YouTube private livestream pipeline and performs  video processing offline using semantic segmentation (U-Net) and object detection (YOLOvX). The  prototype system—tested on a 300m² vegetable plot—shows promising results with over 90% detection  accuracy and effective land use visualization. The interface, built with Streamlit, provides real-time insights,  affordability, and aligns with Smart City goals of accessibility and sustainability.

Keywords— Smart Precision Agriculture, Mini Drone, MSME, Smart City, Deep Learning, Streamlit

I. INTRODUCTION

This Indonesia's agricultural sector plays a pivotal role in supporting national food  security and rural employment. [1], [2]. A significant proportion of food production  comes from smallholder farmers and micro, small, and medium-sized enterprises  (MSMEs), which collectively contribute to national GDP and help sustain rural  livelihoods. However, these groups face persistent barriers to technology adoption due to  limited financial resources, infrastructure, and access to expertise. One such barrier is the  high cost of precision agriculture systems, particularly drone-based monitoring platforms- that can run into hundreds of millions of rupiah. [3], [4], [5].

This research aims to introduce a low-cost, AI-assisted precision agriculture system  based on commercially available mini drones [6], [7], [8], [9], specifically the DJI Mini 2  SE, and user-accessible software pipelines [3], [4], [10], [11], [12].

The main objectives of this study are:    To develop an affordable aerial monitoring system tailored for smallholder and  MSME farming needs.    To enable land segmentation, crop counting, and plant health analysis using RGB  imagery and lightweight AI models.    To deploy an interactive, explainable decision-support tool accessible to users  with minimal technical background.  The potential benefits of this system include improved decision-making, early  detection of crop issues, and optimized land management practices-all contributing to  increased productivity and income for MSME  [10], [13], [14], [15]On a national scale,  this approach supports several Sustainable Development Goals (SDGs), including:

©Asosiasi Prakarsa Indonesia Cerdas (APIC)

203

Davy et al. / Jurnal Sistem Cerdas (2025) Vol 08-No 02  eISSN : 2622-8254 Page : 203 - 215

  SDG 1 (No Poverty): By enhancing agricultural yield and reducing operational  costs     SDG 2 (Zero Hunger): Through improved food production monitoring and  sustainability.    SDG 8 (Decent Work and Economic Growth): By empowering MSMEs with  digital tools that boost efficiency.    SDG 12 (Responsible Consumption and Production): Through more efficient use  of land and water resources.    SDG 13 (Climate Action): Via low-emission drone operations and early climate- stress detection.  By delivering an accessible and effective solution, this study contributes to a broader  strategy of digital transformation in agriculture while reinforcing national objectives in  health, sustainability, and equitable economic development.

Additionally, this research aligns with the broader agenda of Smart X Studies- especially Smart Agriculture-within the Smart City ecosystem [15], [16], [17], [18], [19],  [20], [21]. By leveraging AI for real-time analysis, decision support, and sustainable food  management, the proposed system exemplifies how smart technologies can enhance  quality of life. Improved agricultural productivity directly impacts household income,  food availability, and rural resilience, thus contributing to more livable, sustainable, and  intelligent communities. The integration of AI in Smart Agriculture not only aids  individual farmers but also supports collective well-being, ecological preservation, and  digital inclusivity in underserved regions [15], [16], [17], [18], [19], [20], [21].

As part of Indonesia's national food strategy, smallholder farmers and MSMEs  represent the backbone of domestic agricultural output. However, technological access is  limited by economic and infrastructural constraints. Commercial-grade agricultural  drones, while powerful, often exceed budgets of tens or hundreds of millions of rupiah.  This research offers a practical alternative by utilizing consumer-level mini drones and  accessible AI pipelines for precision agriculture.

This system enables users to conduct visual monitoring and AI-based crop analysis  with only a DJI Mini 2 SE drone, a laptop, and free software tools. The resulting system  democratizes Smart Farming and introduces a feasible entry point for rural digital  transformation.

II. RELATED WORKS

A. AI in Precision Agriculture

Deep learning and image processing models have shown strong results in identifying  crop type, estimating yield, and detecting diseases [22],[23],[24].

Most implementations depend on high-resolution multispectral cameras, making them  less applicable to MSMEs.

B. Drone Applications in Farming

Drones improve spatial awareness and offer aerial perspectives for decision-making  [5], [6], [7], [8], [25]. However, usage is typically limited to enterprises or large  plantations. Mini drones, despite resolution and sensor limitations, can still support  visual-based monitoring.

C. Lightweight Object Detection and Segmentation

Heading YOLO V3. ,V4 and YOLOv5, Yolo V7 are widely used for semantic  segmentation and object counting in agriculture. Their efficient design allows deployment  on standard laptops or edge devices [26], [27], [28], [29], [30], [31], [32], [33], [34].

©Asosiasi Prakarsa Indonesia Cerdas (APIC)

204

Davy et al. / Jurnal Sistem Cerdas (2025) Vol 08-No 02  eISSN : 2622-8254 Page : 203 - 215

D. Citizen-Focused Smart Agriculture Tools

Smart City principles emphasize inclusivity, sustainability, and accessibility. Prior  studies lack public-facing, low-cost agricultural systems. This study bridges that gap by  offering an interactive tool tailored for rural MSMEs.


> **Figure 1. Example of methodology in Smart City using Agri Vision**

(https://agri-vision.github.io/AgriVision/)      E. Commercial Drone Comparisons for Agricultural Use

Smart RGB camera [35], [36], [37] performance plays a key role in determining the  effectiveness of aerial imagery in agriculture. Key parameters influencing quality include  sensor size, resolution, aperture, and dynamic range. Larger sensors and wider apertures  (e.g., f/1.7) allow more light intake, improving performance in low-light or cloudy  conditions—critical for outdoor agricultural monitoring. However, budget drones often  use smaller sensors with limited dynamic range, which may hinder accurate analysis  under harsh lighting.


> **Table 1.  Comparison of Industrial Standard Agricultural Drones**

Drone  Model

Est.  Cost  (IDR)

Camera  Type

Flight  Time

Payload  Support  Use Case

> Rp. 250  million

Multispectr al + RGB

40  min  Up to 50 kg  Industrial spraying + analytics

DJI Agras  T40

RGB +  RTK  GNSS

DJI  Phantom 4  RTK

~ Rp. 100  million

30  min  Low  Survey & mapping for plantation

~ Rp. 80  million

Multispectr al + RGB

25  min  Low  Crop analysis

Parrot  Bluegrass

Multispectr al +  thermal

> Rp. 300  million

50  min  Low  High-end precision agriculture

SenseFly  eBee X

Standard  RGB  (12MP)

~ Rp. 6  million

31  min  None  MSME monitoring, low-cost  mapping

DJI Mini 2  SE


> **Table 2. A Comparison of Mini Drone Variants**

DJI  Drone  Model

HDR/  Dynamic

Sensor

Obstacle

Flight

Size  Resolution  Aperture

Time  Est. Cost (IDR)

Sensing

Range

©Asosiasi Prakarsa Indonesia Cerdas (APIC)

205

Davy et al. / Jurnal Sistem Cerdas (2025) Vol 08-No 02  eISSN : 2622-8254 Page : 203 - 215

Min i 2 SE /

1/2.3 ″ CMOS

12 MP,  4K@30fps  f/2.8  Basic RGB, no

Downward

only  ~31 min  ~Rp 6–12

HDR

million

Mini 2

1/1.3 ″ CMOS

12 MP,  4K@30fps  f/1.7  Native HDR

Downward

Min i 3

only  34–51 min  ~Rp 12 million

Support

3-way  obstacle

1/1.3 ″ CMOS

48 MP,  4K@60fps  f/1.7  HDR, D- Cinelike color

~34 min  ~Rp 18–20

Min i 3 Pro

million

sensing

48 MP,  4K@60– 100fps  f/1.7  10-bit HDR +  D-Log M

1/1.3 ″ CMOS

Omnidirection

al sensing  34–45 min  ~Rp 25–30

Min i 4 Pro

million


> **Table 2  compares several DJI Mini drone variants commonly considered by**

> MSMEs in terms of these critical imaging specifications.

A comparison of Industrial standard agricultural drones like DJI Agras T40,  Phantom 4 RTK, Parrot Bluegrass, and SenseFly eBee X. It highlights the high cost (Rp.  80–300+ million), advanced sensors (multispectral, thermal), and industrial-scale use  cases—contrasted with the DJI Mini 2 SE as a low-cost alternative.

F. RGB Camera Characteristics and DJI Mini Series Comparison

A comparison table of DJI Mini drones (Mini 2 SE, Mini 3, Mini 3 Pro, Mini 4 Pro),  focusing on:

 Sensor quality   HDR capabilities   Obstacle sensing   Cost ranges (~Rp. 6 million to Rp. 30 million)  It positions the Mini 2 SE as an accessible starting point for MSMEs and details  upgrade benefits for more advanced use cases.

G.  Summary of Gaps and Future Directions

To contextualize the novelty and relevance of this research, Table 3 presents an  overview of key research domains, their contributions, and identified gaps that this study  aims to address.    Table 3. An Overview of Key Research, GAP

Research Domain  Key  References  Main Contributions  Identified Gaps

Disease, yield, and  classification using deep

High computational cost, limited

AI in Precision

Agriculture  [6]

MSME deployment

learning

[38],[39],  [40], [41]

Review of drones in large-scale

Limited examples for  fragmented, smallholder farms

UAV-based Crop

agriculture

Monitoring

Real-time object detection,

Lacks full validation under

Lightweight Deep

Learning Models  [30]

segmentation on modest

MSME constraints

devices

Public-Facing  Smart Agri-Tools  [6], [27], [42]  Accessible digital tools for

Rarely integrated with AI + drone

rural smart farming

pipelines

Role of digital tech using drone

Limited real-world  implementations for agriculture

[43],[44],  [45], [46]

Smart City &  Drone Integration

in sustainable urban/rural

in Smart Villages    H. Computer Vision and Object Detection Theory for Drone Imagery

systems

Computer vision (CV) is a core enabler of drone-based precision agriculture. It allows  machines to interpret aerial imagery to detect, count, and classify objects—such as plants,  rows, pests, or disease symptoms. In agriculture, key tasks include semantic

©Asosiasi Prakarsa Indonesia Cerdas (APIC)

206

Davy et al. / Jurnal Sistem Cerdas (2025) Vol 08-No 02  eISSN : 2622-8254 Page : 203 - 215

segmentation, object detection, and classification based on RGB values or spatial  patterns.

1) Popular deep learning architectures include:    YOLO (You Only Look Once): Real-time object detector capable of identifying  individual crops or fruits in aerial imagery[47].    U-Net: A convolutional neural network architecture ideal for pixel-level semantic  segmentation of agricultural land.[48], [49], [50], [51].    DeepLabv3+ and Mask R-CNN: Used for advanced segmentation and instance- aware predictions in dense crop environments.[52],[53].    2) Several public datasets have emerged as benchmarks for drone-based CV models:    AgriVision: For object detection on crops and farm equipment from aerial drone  footage [54].    Orchards with UAVs: Contains annotated drone footage of orchards and  plantations [55], [56].    Plantation Monitoring Using Drone Images [57].    UAVDT (Unmanned Aerial Vehicle Detection and Tracking): A dataset for  detecting dynamic targets (e.g., vehicles, animals)[58].    DOTA (Dataset for Object Detection in Aerial Images): Covers urban and  agricultural scenes with annotated objects.[59].    3) Evaluation Metrics commonly used in agricultural CV tasks include:    Precision and Recall: Measure object detection accuracy.    IoU (Intersection over Union): Quantifies the overlap between predicted and  ground truth bounding boxes.    mAP (mean Average Precision): Aggregated measure of detection accuracy  across multiple classes and thresholds.    Dice Coefficient and Jaccard Index: Used for semantic segmentation to assess  overlap.

Figure. 2. Example visualization of common evaluation metrics for drone-based object detection and

segmentation models      III. METHOD

©Asosiasi Prakarsa Indonesia Cerdas (APIC)

207

Davy et al. / Jurnal Sistem Cerdas (2025) Vol 08-No 02  eISSN : 2622-8254 Page : 203 - 215

A. System Architecture Overview

The architecture of the proposed system consists of four key components: (1) Mini  Drone for data acquisition, (2) Livestream pipeline for real-time monitoring, (3) AI-based  Processing unit for analytics, and (4) a Web Application interface for users. Figure 1  presents the system flow of methodology.

Figure. 3. Methodology Diagram in General    B. Experimental Setup Using Streamlit, OBS, and Mobile Integration

To test the feasibility of AI-powered monitoring, the system utilizes the following  low-cost experimental setup:  1) Drone Flight and Video Capture  The DJI Mini 2 SE is flown over small agricultural plots for ~5 minutes per session.  The drone’s live video feed is accessed through a connected smartphone, which is  mounted on the DJI controller.  2) Private Livestreaming Pipeline  Using OBS Studio (Open Broadcaster Software) installed on a laptop, the phone’s  display is mirrored via USB/airplay. The live video feed is broadcast to a private  YouTube Live channel, making it accessible in near real-time with minimal cost.  3) Object Detection from Livestream  A Python-based Streamlit application runs in parallel, pulling frames from the  livestream. Object detection (e.g., plant counting or disease patch identification) is  performed using pretrained YOLOv5 models. The results (bounding boxes, object class,  detection confidence) are displayed to the user via the web UI.  4) User Interface and Logging  The Streamlit interface enables live annotation, frame capture, and result logging.  Users can review insights and historical data Without needing specialized software.

©Asosiasi Prakarsa Indonesia Cerdas (APIC)

208

Davy et al. / Jurnal Sistem Cerdas (2025) Vol 08-No 02  eISSN : 2622-8254 Page : 203 - 215

Figure. 4. System architecture of AI-assisted agricultural monitoring using a mini drone and private

livestream pipeline.    C. Use Cases in Smart Agriculture

To illustrate the system’s functionality, we include example screenshots and outputs  from actual test deployments:

  Semantic Segmentation Output: Drone imagery is processed with U-Net to  segment rice field zones.    Tree and Object Detection Result: YOLOvX model highlights trees in the  plantation with bounding boxes.    Leaf Health Classification: Sample output shows yellowing areas flagged using  HSV-based segmentation.    Livestock Counting: Object detection model labels each livestock instance with  class and count.  These outputs are visualized using the Streamlit app interface, giving farmers  actionable insights in real time with no need for post-processing.

The proposed system enables various practical applications for precision agriculture  in small-scale environments:

  Semantic Segmentation of Rice Fields:    The drone captures top-down imagery of rice paddies.    AI models segment the field into zones based on vegetation density, allowing  identification of underperforming plots.  Tree and Land Mapping:    Object detection identifies and counts individual trees.    Land use classification helps delineate areas of crop growth, bare soil, or  pathways for irrigation planning.    Leaf Health Monitoring:    Visual symptoms such as yellowing or spots are detected using color-based  heuristics and trained classifiers.    Health maps can be generated to target fertilizer or pesticide application precisely.

©Asosiasi Prakarsa Indonesia Cerdas (APIC)

209

Davy et al. / Jurnal Sistem Cerdas (2025) Vol 08-No 02  eISSN : 2622-8254 Page : 203 - 215

  Livestock Counting and Monitoring:    The system can be adapted to detect and count livestock such as goats, cows, or  poultry.  This supports inventory logging and alerts for abnormal movement or missing  animals.These use cases highlight the system's potential to support both plant-based and  animal-based agriculture within the same digital platform, delivering real-time  intelligence to rural MSMEs.    IV. RESULT AND CONCLUSION


> **Figure 5. Sample instance segmentation output from the drone-based detection system, identifying fruit**

> contours (e.g., tomato, ginger, mango) using a YOLOX model

The experiment aimed to detect and count fruit objects (e.g., tomato, mango, ginger)  using a model trained on annotated agricultural datasets such as the publicly available  Roboflow-based "recognition-agriculture" dataset.    D.  Instance Segmentation Output

A YOLOX model integrated with Streamlit was used to perform object-level  segmentation on frames extracted from drone livestreams.

Fruits were successfully identified and segmented with contour masks for each  instance, enabling accurate counting and spatial distribution mapping.

Detection accuracy varied by object type and lighting, with optimal results for distinct  shapes and well-separated items.  A YOLOX model integrated with Streamlit was used to perform object-level  segmentation on frames extracted from drone livestreams.  Fruits were successfully identified and segmented with contour masks for each instance,  enabling accurate counting and spatial distribution mapping.  Detection accuracy varied by object type and lighting, with optimal results for distinct  shapes and well-separated items.    E. Model Performance  The instance segmentation pipeline achieved a mean Average Precision (mAP) of 0.78  across 11 object classes (e.g., apple, banana, onion).

©Asosiasi Prakarsa Indonesia Cerdas (APIC)

210

Davy et al. / Jurnal Sistem Cerdas (2025) Vol 08-No 02  eISSN : 2622-8254 Page : 203 - 215

F. System Responsiveness

The end-to-end latency from video capture to segmentation visualization in the  Streamlit app remained under 6 seconds using a standard laptop.  The model ran in real time with minor lag under dense object scenes.  This revised focus validates the practical feasibility of fruit detection and counting  through RGB-only instance segmentation. Future work may explore integration with  ripeness classification or cross-referencing detected yields with planting records for  inventory tracking.    V. CONCLUSION

This study demonstrates the feasibility and value of using low-cost, consumer-grade  drones in combination with lightweight AI models to support precision agriculture for  MSMEs in Indonesia. By integrating the DJI Mini 2 SE with open-source tools like OBS  Studio, YouTube Live, and Streamlit, we developed an accessible and affordable real- time monitoring system.

Our experimental implementation focused on instance segmentation of fruits from  aerial RGB video, achieving meaningful accuracy (mAP 0.78) in object detection and  counting. This confirms that even with hardware constraints, AI-powered insights can be  delivered to farmers with minimal investment and technical expertise.

The system supports diverse agricultural use cases—including land segmentation,  health monitoring, and crop counting—and contributes to national goals such as poverty  reduction, food security, and digital transformation in rural areas. It also aligns with the  Smart Agriculture vision of Smart City ecosystems by improving quality of life through  inclusive technological innovation.

Future work will expand on model training with localized datasets, enhance robustness  under varied weather conditions, and integrate geospatial mapping for broader adoption.  Ultimately, this research provides a foundational step toward democratizing Smart  Farming for smallholders across Indonesia and similar contexts.


## REFERENCES

[1]  F. I. Komunikasi, U. Bhayangkara, and J. Raya, ―Indonesia ’ S Communication  Strategy In  CTI-CFF Cooperation in Supporting National Food Security Strategi  Komunikasi Indonesia dalam Kerja Sama CTI -,‖ vol. 2, no. 3, pp. 3698–3706,  2025.  [2] L. Judijanto, D. O. Suparwata, M. Marjan, and L. Y. Andriyani, ―The Role of

Modern Harvesting Tools in Supporting Agricultural Modernization and National  Food Security,‖ West Science Agro, vol. 3, no. 02, pp. 125–130, 2025, doi:  10.58812/wsa.v3i02.1925.  [3] R. Boonprasert and P. Vijuksungsith, ―Agricultural UAVs in Recent Advances,

Innovations and Applications,‖ Advances in Unmanned Aerial Vehicles - New  Trends  and  Applications  [Working  Title],  pp.  1–31,  2025,  doi:  10.5772/intechopen.1010104.  [4] S. Beese, ―Role of Remote Sensing in Agricultural Survey and Monitoring,‖ no.

October, 2023.  [5] P. Chen et al., ―A Survey on Unauthorized UAV Threats to Smart Farming,‖

Drones, vol. 9, no. 4, pp. 1–38, 2025, doi: 10.3390/drones9040251.  [6] Dr. Tehseen Zia, ―Precision Farming: How AI and Drones Are Reshaping

Agriculture,‖  pp.  1–14,  2023,  [Online].  Available:  https://www.techopedia.com/precision-farming-how-ai-and-drones-are-reshaping- agriculture  [7] P. Tripicchio, M. Satler, G. Dabisias, E. Ruffaldi, and C. A. Avizzano, ―Towards

Smart Farming and Sustainable Agriculture with Drones,‖ in Proceedings - 2015

©Asosiasi Prakarsa Indonesia Cerdas (APIC)

211

Davy et al. / Jurnal Sistem Cerdas (2025) Vol 08-No 02  eISSN : 2622-8254 Page : 203 - 215

International Conference on Intelligent Environments, IE 2015, Institute of  Electrical and Electronics Engineers Inc., Aug. 2015, pp. 140–143. doi:  10.1109/IE.2015.29.  [8] M. S. Journal, ―IoT-Based Agriculture Monitoring and Smart Farming Using

Drones ‖ Mukt Shabd Journal, vol. IX, no. Iv, pp. 525–534, 2020.  [9] G. Mohyuddin, M. A. Khan, A. Haseeb, S. Mahpara, M. Waseem, and A. M. Saleh,

―Evaluation of Machine Learning Approaches for Precision Farming in Smart  Agriculture System: A Comprehensive Review,‖ IEEE Access, vol. 12, no. May, pp.  60155–60184, 2024, doi: 10.1109/ACCESS.2024.3390581.  [10] Y. A, M. A, and R. M, ―Economic Analysis of Drone Technology in Agriculture:

Insights from Farmer Producer Organisation in Tamil Nadu,‖ Journal of  Experimental Agriculture International, vol. 46, no. 12, pp. 611–617, 2024, doi:  10.9734/jeai/2024/v46i123168.  [11] M. Ö. Kollo, V.-A. Veres, and M. Mortan, ―From Perception to Practice: Drone

Technology in Romanian Agriculture,‖ Management and Economics Review, vol.  10, no. 1, pp. 5–21, 2025, doi: 10.24818/mer/2025.01-01.  [12] S. Datta et al., ―Drone technology in agriculture: A study on economic motivation of

farmers,‖ International Journal of Agriculture and Food Science, vol. 7, no. 7, pp.  330–332, 2025, doi: 10.33545/2664844x.2025.v7.i7d.527.  [13] S. Mukherjee, ―Applications of Modern Technologies , Drones , and IoT in Indian

Agriculture Applications of Modern Technologies , Drones , and IoT in Indian  Agriculture 20th June , 2025 For The World Agricultural Forum By Soumyajit  Mukherjee,‖ no. August, 2025, doi: 10.13140/RG.2.2.35146.07361.  [14] H. Kamal Mallick, S. Chatterjee, and R. Mallick, ―Application of Drone

Technology: A New Era for Sustainable Agriculture,‖ NL Journal of Agriculture  and Biotechnology, vol. 2, no. 1, pp. 37–48, 2025, doi: 10.71168/nab.02.01.105.  [15] F. Ç. Baz, ―Industry 4.0 in Agriculture: Smart Agricultural Applications and Drone

Use in Agriculture,‖ Turkish Journal of Agriculture - Food Science and Technology,  vol. 13, no. 5, pp. 1139–1145, 2025, doi: 10.24925/turjaf.v13i5.1139-1145.6905.  [16] S. F. A. Razak, S. Yogarayan, M. S. Sayeed, and M. I. F. M. Derafi, ―Agriculture


### 5.0 and Explainable AI for Smart Agriculture: A Scoping Review,‖ Emerging

Science Journal, vol. 8, no. 2, pp. 744–760, 2024, doi: 10.28991/ESJ-2024-08-02-
024. 
[17] Y. Su and X. Wang, ―Innovation of agricultural economic management in the

process of constructing smart agriculture by big data,‖ Sustainable Computing:  Informatics and Systems, vol. 31, Sep. 2021, doi: 10.1016/j.suscom.2021.100579.  [18] V. K. Quy et al., ―IoT-Enabled Smart Agriculture: Architecture, Applications, and

Challenges,‖ Applied Sciences (Switzerland), vol. 12, no. 7, 2022, doi:  10.3390/app12073396.  [19] C. Prabha and A. Pathak, ―Enabling Technologies in Smart Agriculture: A Way

Forward Towards Future Fields,‖ 2023 International Conference on Advancement in  Computation  &  Computer  Technologies  (InCACCT),  2023,  doi:  10.1109/incacct57535.2023.10141722.  [20] J. Shobana et al., ―Smart Agriculture: Integrating Air Quality Monitoring With Deep

Learning for Process Optimization*,‖ Scalable Computing, vol. 26, no. 3, pp. 1005– 1016, 2025, doi: 10.12694/scpe.v26i3.4190.  [21] O. Friha, M. A. Ferrag, L. Shu, L. Maglaras, and X. Wang, ―Internet of Things for

the Future of Smart Agriculture: A Comprehensive Survey of Emerging  Technologies,‖ IEEE/CAA Journal of Automatica Sinica, vol. 8, no. 4, pp. 718–752,  2021, doi: 10.1109/JAS.2021.1003925.  [22] R. Chin, C. Catal, and A. Kassahun, ―Plant disease detection using drones in

precision agriculture,‖ 2023, Springer. doi: 10.1007/s11119-023-10014-y.

©Asosiasi Prakarsa Indonesia Cerdas (APIC)

212

Davy et al. / Jurnal Sistem Cerdas (2025) Vol 08-No 02  eISSN : 2622-8254 Page : 203 - 215

[23] C. Singh, R. Mishra, H. P. Gupta, and P. Kumari, ―The Internet of Drones in

Precision Agriculture: Challenges, Solutions, and Research Opportunities,‖ IEEE  Internet of Things Magazine, vol. 5, no. 1, pp. 180–184, May 2022, doi:  10.1109/iotm.006.2100100.  [24] C. Singh et al., ―The Internet of Drones in Precision Agriculture: Challenges,

Solutions, and Research Opportunities,‖ IEEE internet of things magazine, 2022,  doi: 10.1109/iotm.006.2100100.  [25] Y. Inoue, ―Satellite- and drone-based remote sensing of crops and soils for smart

farming–a  review,‖  2020,  Taylor  and  Francis  Ltd.  doi:  10.1080/00380768.2020.1738899.  [26] J. Leng, M. Mo, Y. Zhou, C. Gao, W. Li, and X. Gao, ―Pareto Refocusing for

Drone-view Object Detection,‖ IEEE Transactions on Circuits and Systems for  Video Technology, Mar. 2022, doi: 10.1109/TCSVT.2022.3210207.  [27] W. Reckling, H. Mitasova, K. Wegmann, G. Kauffman, and R. Reid, ―Efficient

drone-based rare plant monitoring using a species distribution model and ai-based  object detection,‖ Drones, vol. 5, no. 4, 2021, doi: 10.3390/drones5040110.  [28] T. Q. Khoi, N. A. Quang, and N. K. Hieu, ―Object detection for drones on Raspberry

Pi potentials and challenges,‖ IOP Conf Ser Mater Sci Eng, vol. 1109, no. 1, p.  012033, Mar. 2021, doi: 10.1088/1757-899x/1109/1/012033.  [29] R. Walambe, A. Marathe, and K. Kotecha, ―Multiscale object detection from drone

imagery using ensemble transfer learning,‖ Drones, vol. 5, no. 3, pp. 1–24, 2021,  doi: 10.3390/drones5030066.  [30] Y. Egi, Y. Egi, M. Hajyzadeh, M. Hajyzadeh, E. Eyceyurt, and E. Eyceyurt, ―Drone-

Computer Communication Based Tomato Generative Organ Counting Model Using  YOLO V5 and Deep-Sort,‖ Agriculture, 2022, doi: 10.3390/agriculture12091290.  [31] B. Aydin and S. Singha, ―Drone Detection Using YOLOv5,‖ Engineer, 2023, doi:

10.3390/eng4010025.  [32] H. Liu, K. Fan, Q. Ouyang, and N. Li, ―Real-time small drones detection based on

pruned yolov4,‖ Sensors, vol. 21, no. 10, 2021, doi: 10.3390/s21103374.  [33] H. R. Alsanad et al., ―YOLO-V3 based real-time drone detection algorithm,‖

Multimed Tools Appl, 2022, doi: 10.1007/s11042-022-12939-4.  [34] L. L. Zhao and M. L. Zhu, ―MS-YOLOv7:YOLOv7 Based on Multi-Scale for

Object Detection on UAV Aerial Photography,‖ Drones, vol. 7, no. 3, Mar. 2023,  doi: 10.3390/drones7030188.  [35] X. Chen et al., ―Wildland Fire Detection and Monitoring using a Drone-collected

RGB/IR Image Dataset,‖ in 2022 IEEE Applied Imagery Pattern Recognition  Workshop  (AIPR),  IEEE,  Oct.  2022,  pp.  1–4.  doi:  10.1109/AIPR57179.2022.10092208.  [36] L. Parra, D. Mostaza-Colado, S. Yousfi, J. F. Marin, P. V. Mauri, and J. Lloret,

―Drone rgb images as a reliable information source to determine legumes  establishment success,‖ Drones, vol. 5, no. 3, 2021, doi: 10.3390/drones5030079.  [37] E. D. Detiana Yucky, A. Gautama Putrada, and M. Abdurohman, ―IoT Drone

Camera for a Paddy Crop Health Detector with RGB Comparison,‖ 2021 9th  International Conference on Information and Communication Technology, ICoICT  2021, pp. 155–159, 2021, doi: 10.1109/ICoICT52021.2021.9527421.  [38] K. Gayathri Devi, N. Sowmiya, K. Yasoda, K. Muthulakshmi, and B. Kishore,

―Review on application of drones for crop health monitoring and spraying pesticides  and  fertilizer,‖  2020,  Innovare  Academics  Sciences  Pvt.  Ltd.  doi:  10.31838/jcr.07.06.117.  [39] P. Gupta, S. Gopal, M. Sharma, S. Joshi, C. Sahani, and K. Ahalawat, ―Agriculture

Informatics and Communication: Paradigm of E-Governance and Drone Technology  for Crop Monitoring,‖ Institute of Electrical and Electronics Engineers (IEEE), Dec.  2023, pp. 113–118. doi: 10.1109/icscc59169.2023.10335058.

©Asosiasi Prakarsa Indonesia Cerdas (APIC)

213

Davy et al. / Jurnal Sistem Cerdas (2025) Vol 08-No 02  eISSN : 2622-8254 Page : 203 - 215

[40] P. Sidike and M. Maimaitiyiming, ―Scholars ’ Mine UAV / Satellite Multiscale Data

Fusion for Crop Monitoring and Early Stress Detection,‖ 2019.  [41] P. Rajalakshmi, B. Naik, and U. B. Desai, ―Intelligent Drought Stress Monitoring on

Spatio-Spectral-Temporal Drone based Crop Imagery using Deep Networks,‖ null,  2022, doi: null.  [42] R. Ravikumar et al., ―PokkahScan - An Intelligent Drone for detection of Pokkah

Boeng Disease in Sugarcane Using Transfer Learning and eXplainable AI,‖  International Conference on Computing Communication and Networking  Technologies, 2024, doi: 10.1109/icccnt61001.2024.10725385.  [43] A. Oltvoort, ―Is Smart City Enschede Ready for the Use of Safety and Security

Drones?‖  [44] M. H. Siddiqi et al., ―FANET: Smart city mobility off to a flying start with self-

organized drone-based networks,‖ IET Communications, vol. 16, no. 10, pp. 1209– 1217, Jun. 2022, doi: 10.1049/cmu2.12291.  [45] J. P. G. Sterbenz and J. P. G. Sterbenz, ―Drones in the Smart City and IoT:

Protocols, Resilience, Benefits, and Risks,‖ DroNet@MobiSys, 2016, doi:  10.1145/2935620.2949659.  [46] M. Bakirci, ―Smart city air quality management through leveraging drones for

precision  monitoring,‖  Sustain  Cities  Soc,  vol.  106,  Jul.  2024,  doi:  10.1016/j.scs.2024.105390.  [47] N. S. Rani, K. R. Bhavya, A. Vadivel, T. Vasudev, R. M. Devadas, and V.

Hiremani, ―A Novel Curriculum Learning Training Strategy for Pomegranate  Growth Stage Classification Using YOLO Models on Multi-Source Datasets for  Precision Agriculture,‖ IEEE Access, vol. 13, no. June, pp. 112594–112622, 2025,  doi: 10.1109/ACCESS.2025.3581794.  [48] G. Singh et al., ―Enhanced Leaf Disease Segmentation Using U-Net Architecture for

Precision Agriculture: A Deep Learning Approach,‖ Food Sci Nutr, vol. 13, no. 7,  2025, doi: 10.1002/fsn3.70594.  [49] ―DSGSU-Net : A U-Net-Based Model for Tomato Leaf Disease Segmentation Using

Depthwise Separable Convolutions and Ghost Sampling DSGSU-Net : A U-Net- Based Model for Tomato Leaf Disease Segmentation Using Depthwise Separable  Convolutions and Ghost Sampling,‖ pp. 0–20, 2025.  [50] Z. Liu, ―Image Recognition and Enhancements of the U-Net Model,‖ Applied and

Computational Engineering, vol. 172, no. 1, pp. 164–173, 2025, doi:  10.54254/2755-2721/2025.gl24843.  [51] Q. Liu and J. Zhao, ―MA-Res U-Net: Design of Soybean Navigation System with

Improved U-Net Model,‖ Phyton-International Journal of Experimental Botany, vol.  93, no. 10, pp. 2663–2681, 2024, doi: 10.32604/phyton.2024.056054.  [52] S. E. E. Profile, Benchmarking U-Net , FCN , and DeepLabV3 for Precision Plant

Segmentation in Agricultural Applications Metin Özetlemede Ekstraktif ve Abstraktif  Yakla şı mlar, no. June. 2025.  [53] Y. Cao et al., ―Case instance segmentation of small farmland based on Mask R-

CNN of feature pyramid network with double attention mechanism in high  resolution satellite images,‖ Comput Electron Agric, vol. 212, no. August 2022, p.  108073, 2023, doi: 10.1016/j.compag.2023.108073.  [54] M. T. Chiu et al., ―Agriculture-vision: A large aerial image database for agricultural

pattern analysis,‖ Proceedings of the IEEE Computer Society Conference on  Computer Vision and Pattern Recognition, pp. 2825–2835, 2020, doi:  10.1109/CVPR42600.2020.00290.  [55] D. Popescu, L. Ichim, and F. Stoican, ―Orchard monitoring based on unmanned

aerial vehicles and image processing by artificial neural networks: a systematic  review,‖ Front Plant Sci, vol. 14, no. November, pp. 1–30, 2023, doi:  10.3389/fpls.2023.1237695.

©Asosiasi Prakarsa Indonesia Cerdas (APIC)

214

Davy et al. / Jurnal Sistem Cerdas (2025) Vol 08-No 02  eISSN : 2622-8254 Page : 203 - 215

[56] N. Stefas, H. Bayram, and V. Isler, ―Vision-based monitoring of orchards with

UAVs,‖ Comput Electron Agric, vol. 163, no. May, p. 104814, 2019, doi:  10.1016/j.compag.2019.05.023.  [57] Y. Karumanchi, G. L. Prasanna, S. Mukherjee, and N. Kolagani, ―Plantation

Monitoring Using Drone Images: A Dataset and Performance Review,‖ 2025,  [Online]. Available: http://arxiv.org/abs/2502.08233  [58] H. Yu et al., ―The Unmanned Aerial Vehicle Benchmark: Object Detection,

Tracking and Baseline,‖ Int J Comput Vis, vol. 128, no. 5, pp. 1141–1159, 2020, doi:  10.1007/s11263-019-01266-1.  [59] G. S. Xia et al., ―DOTA: A Large-Scale Dataset for Object Detection in Aerial

Images,‖ Proceedings of the IEEE Computer Society Conference on Computer  Vision  and  Pattern  Recognition,  pp.  3974–3983,  2018,  doi:  10.1109/CVPR.2018.00418.

©Asosiasi Prakarsa Indonesia Cerdas (APIC)

215
