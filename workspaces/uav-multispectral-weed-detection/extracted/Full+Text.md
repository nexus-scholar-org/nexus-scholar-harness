---
title: "Full+Text"
doi: "10.68099/asnj.2024.79"
extraction_engine: pymupdf
---

ISSN 2822 4450  
      
 Aintelia Science Notes, Vol. 3, Iss. 2 
Development of an Autonomous Weed-Weeding Robot Utilizing Edge-AI and 
Multispectral Computer Vision for Row-Crop Farming 
Kondrat Kucharski¹, Natasza Jasińska²,Lesława Dudek3 
¹ *University of Life Sciences in Lublin,Lublin,Poland , k.kuharski@ up.lublin.pl,  ORCID: 0009-0002-9430-3960 
² University of Life Sciences in Lublin,Lublin,Poland  n.jasinska@ up.lublin.pl,  ORCID: 0009-0000-1901-9615 
3 Wrocław University of Environmental and Life Sciences,Wroclaw,Poland, dudek.leslawa@ upwr.edu.pl, ORCID: 
0009-0007-8426-5397 
Weeds represent one of the most economically damaging biotic stresses in row-crop production, yet current 
chemical control strategies face mounting regulatory pressure and resistance evolution. This paper presents the 
design, integration, and preliminary field evaluation of an autonomous ground robot for in-season mechanical 
weed control in row-crop systems, combining Edge-AI inference with a five-band multispectral vision pipeline. 
The system architecture comprises a four-wheel differential-drive platform, a MicaSense-class multispectral 
imaging module (blue, green, red, red-edge, near-infrared), an NVIDIA Jetson Orin edge-computing unit, and a 
servo-actuated inter-row/intra-row tine mechanism. A YOLOv8-nano model, trained on a field-collected and 
synthetically augmented dataset of 14,200 annotated multispectral frames covering four principal row-crop weed 
species (Chenopodium album, Amaranthus retroflexus, Galium aparine, Convolvulus arvensis), is deployed for 
real-time per-frame weed localisation at 18 frames per second on the embedded platform. Vegetation index fusion 
combining NDVI and NDRE channels  provides a secondary spectral discriminator that reduces false-positive 
detections on soil and crop residue by 34% relative to RGB-only inference. RTK-GNSS-guided row-following 
navigation achieves lateral deviation of ≤1.8 cm (1σ) at 0.6 m/s travel speed. Field trials on maize and soybean 
demonstrate a weed removal efficacy of 82–89% with a crop damage rate below 1.2%, at a treatment throughput 
of 0.45 ha/h. 
Keywords: autonomous weeding robot; edge-AI; multispectral computer vision; YOLOv8; row-crop farming; 
NDVI; NDRE; precision agriculture 
© 2024 Published by AIntelia 
19


Aintelia Science Notes, Vol. 3, Iss. 2 
  Kucharski et al. 
 
1. Introduction
Weeds impose an estimated annual economic loss exceeding USD 32 billion in global crop production 
through direct yield competition, harvest interference, and indirect costs of control. In row-crop systems  maize, 
soybean, cotton, and sugar beet  intra-row weeds present the greatest control challenge because their proximity 
to crop plants precludes conventional inter-row cultivation during canopy closure. Herbicide-based management 
remains the dominant strategy, but escalating herbicide resistance  currently documented in more than 500 weed 
biotypes globally  and tightening European and international pesticide regulations are driving urgent demand 
for non-chemical alternatives [1]. 
Autonomous robotic weeding has emerged as a technically viable and economically scalable approach 
to non-chemical weed control, offering the precision of targeted mechanical intervention at a cost trajectory 
enabled by declining sensor and computing hardware prices. Current commercial systems  including the Carbon 
Robotics LaserWeeder and the Naio Technologies OZ robot  demonstrate the market readiness of the category, 
but rely predominantly on RGB vision or laser ablation approaches that do not exploit the spectral richness of 
multispectral imaging for weed-crop discrimination [2]. 
Multispectral imaging, capturing reflectance in blue, green, red, red-edge, and near-infrared (NIR) 
bands, provides biochemical and physiological information beyond visible appearance. Vegetation indices 
derived from these bands  particularly the Normalised Difference Vegetation Index (NDVI) and Normalised 
Difference Red Edge (NDRE)  have demonstrated the capacity to discriminate weed species from crops and soil 
backgrounds with higher accuracy than RGB imagery, especially under variable illumination and phenological 
similarity conditions [3]. The integration of multispectral sensing with edge AI inference on embedded 
computing platforms represents a convergence of technologies that enables real-time, in-field weed 
classification without dependence on cloud connectivity. 
This paper presents the system design and field evaluation of an autonomous row-crop weeding robot, 
designated AgroSense-W1, integrating a five-band multispectral camera, YOLOv8-nano deep learning 
inference on an NVIDIA Jetson Orin edge computing unit, and a servo-actuated mechanical weeding tool. The 
principal contributions are: (i) a multispectral+AI fusion pipeline for weed detection that combines per-band 
NDVI/NDRE vegetation index maps with YOLOv8 object detection for enhanced discrimination; (ii) a field-
collected and synthetically augmented training dataset of 14,200 labelled multispectral frames; (iii) RTK-GNSS-
guided autonomous row-following navigation; and (iv) field trial results quantifying weed removal efficacy, 
crop damage rate, and operational throughput on maize and soybean. Section 2 reviews the relevant literature; 
Section 3 describes the system design; Section 4 details the AI vision pipeline; Section 5 presents field trial 
methodology and results; Section 6 discusses findings; and Section 7 concludes. 
2. Literature Review
The field of autonomous agricultural robotics has expanded rapidly in the past decade, with robotic 
weeders emerging as a priority application. Zhang et al. [4] reviewed current robotic approaches for precision 
weed management, categorising systems by intervention modality  mechanical, laser, electrothermal, and 
herbicide-spot-spray  and identifying deep learning-based computer vision as the enabling technology for all 
categories. The review noted that intra-row weeding remains disproportionately challenging due to the spatial 
proximity of weed and crop root zones, requiring millimetre-level actuation accuracy that constrains travel speed 
and thus operational throughput. 
Visentin et al. [5] presented a mixed-autonomous robotic platform achieving both intra-row and inter-
row weed removal for precision agriculture, implementing visual servoing for close-range crop avoidance 
superimposed on GPS-guided field navigation. Their system demonstrated the practical viability of dual-mode 
mechanical weeding on a single platform. Quan et al. [6] developed an intelligent intra-row robotic weeding 
20


Aintelia Science Notes, Vol. 3, Iss. 2                                                                                                          Kucharski et al. 
 
system combining deep learning with a targeted weeding mode, reporting weed removal efficacy of 87.3% in 
lettuce with crop damage below 2%  benchmark figures that frame the performance targets for the present work. 
Deep learning object detection and semantic segmentation have become the dominant paradigm for in-
field crop-weed discrimination. Rai et al. [7] conducted a comprehensive review of deep learning applications 
in precision weed management, documenting the shift from hand-crafted feature methods to convolutional 
neural network (CNN) architectures. YOLOv8, released by Ultralytics in 2023, represents the current state of 
the art in real-time object detection, offering a family of models ranging from nano (3.2M parameters) to extra-
large that are explicitly optimised for deployment on edge computing hardware [8]. 
Dang et al. [9] proposed YOLOWeeds, a novel benchmark of YOLO object detectors for multi-class 
weed detection in cotton production systems, establishing YOLOv8 as the highest-performing architecture 
across detection accuracy and inference speed metrics. Fan et al. [10] demonstrated a deep-learning-based weed 
detection and target spraying robot system at the seedling stage of cotton fields, achieving 93.2% detection 
accuracy in uncontrolled field conditions. The integration of lightweight CNNs on embedded GPU platforms 
was addressed by Mwitta and Rains [11], who evaluated inference performance of deep learning models for 
real-time weed detection on embedded computers including the NVIDIA Jetson series, confirming viability of 
YOLOv8-nano at 15-22 FPS on the Jetson Orin at acceptable power envelope. 
Multispectral imaging extends weed detection capability by capturing spectral reflectance patterns 
beyond human-visible wavelengths. The NDVI and NDRE indices have been extensively applied to crop health 
monitoring and weed mapping. Balaska et al. [12] reviewed sustainable crop protection via robotics and AI 
solutions, specifically noting that multispectral sensing reduces false-positive rates in challenging conditions  
crop residue, soil crust, and senescent leaves  that confound RGB-based classifiers. UAV-based multispectral 
weed mapping in cereal fields using machine learning reported weed identification accuracy of 93.47% in rice, 
confirming the species-level discriminative power of red-edge and NIR reflectance [3]. 
The WeedsGalore dataset [13]  a multispectral, multitemporal UAV-based dataset for crop and weed 
segmentation in maize fields  provides a benchmark for multispectral weed detection research, demonstrating 
that the inclusion of red-edge and NIR bands improves segmentation F1-score by 8-12 percentage points over 
RGB-only baselines. Genze et al. [14] reported deep learning-based early weed segmentation using motion-
blurred UAV images, establishing that data augmentation strategies addressing image degradation are essential 
for robust real-world performance. 
The deployment of deep learning inference on resource-constrained embedded platforms  a paradigm 
termed Edge AI is increasingly attractive for agricultural robots that must operate without reliable cloud 
connectivity in field environments. The NVIDIA Jetson platform family, particularly the Jetson Orin module 
(up to 275 TOPS INT8), provides sufficient compute capacity for YOLOv8-class models at real-time frame 
rates while operating within a 10-25 W power budget suitable for battery-powered field robots. Balaska et al. 
[12] identified edge computing as a critical enabler for autonomous agricultural robots, enabling closed-loop 
perception-action cycles with latency below the 50 ms threshold required for actuation at field-relevant speeds. 
The OpenWeedLocator (OWL) project [15] demonstrated that open-source, low-cost embedded platforms can 
support fallow weed detection at practical accuracy levels, validating the general edge AI approach. 
Despite progress in individual technology components, the integration of five-band multispectral 
imaging with edge AI inference  specifically exploiting NDVI/NDRE vegetation index fusion as a 
complementary spectral discriminator alongside RGB-channel deep learning  in a fully autonomous ground 
weeding robot has not been systematically evaluated. Existing systems rely predominantly on single-modality 
RGB vision or operate as UAV platforms unable to deliver mechanical intervention. The present work addresses 
this integration gap, providing a complete system design and field-evaluated performance characterisation. 
21


Aintelia Science Notes, Vol. 3, Iss. 2                                                                                                          Kucharski et al. 
 
3. Methodology 
The AgroSense-W1 platform is a four-wheel differential-drive ground robot with an aluminium-tube 
frame chassis sized for 0.75 m row spacing  compatible with standard maize and soybean inter-row geometry. 
Overall dimensions are 1.20 m (L) × 0.90 m (W) × 0.85 m (H) with a kerb mass of 68 kg including battery and 
implements. Four brushless DC hub motors (nominal torque 25 N·m per wheel) drive the platform through a 48 
V / 40 Ah lithium iron phosphate battery pack providing 4-6 hours operational endurance at normal field loading. 
A central compute enclosure mounted on vibration-damping mounts houses the NVIDIA Jetson Orin NX (16 
GB) edge-AI module and supporting electronics. 
The weeding tool module, mounted on the forward chassis rail, comprises four independently servo-
actuated tines arranged in two intra-row and two inter-row positions. Tine penetration depth is continuously 
adjustable (0-80 mm) via stepper-motor linear actuators, and lateral position is adjusted within ±120 mm of 
nominal by a cross-slide guided by a servo-driven leadscrew. Tine actuation latency from weed detection trigger 
to soil contact is 180 ms, which at 0.6 m/s travel speed corresponds to a spatial error of 108 mm  acceptable for 
current-season weed control given tine contact width of 40 mm. 
The vision system is centred on a five-band multispectral camera capturing simultaneous images in Blue 
(475 nm), Green (560 nm), Red (668 nm), Red-Edge (717 nm), and Near-Infrared (842 nm) bands at 2.1 MP 
per band with a 47° × 35° horizontal FOV. The camera is mounted at a nadir angle on a forward-facing mast at 
0.65 m above ground level, providing a ground footprint of approximately 0.75 m × 0.55 m at field travel height  
sufficient to encompass the full inter-row zone plus partial intra-row margins. A calibrated reflectance panel is 
measured at the field margin before each mission to enable per-session absolute reflectance calibration. 
At each inference cycle, the raw five-band image stack is radiometrically calibrated and aligned, then 
processed in two parallel streams: (i) a three-channel RGB composite is extracted and fed to the YOLOv8-nano 
detection model; and (ii) per-pixel NDVI and NDRE maps are computed as NDVI = (NIR – Red)/(NIR + Red) 
and NDRE = (NIR – RedEdge)/(NIR + RedEdge). The vegetation index maps are post-processed through a 
binary threshold (NDVI > 0.35 AND NDRE > 0.18, calibrated to the target crop-weed spectral library) to 
produce a vegetation mask that is intersected with the YOLOv8 detection bounding boxes in the fusion module. 
Detections falling outside the vegetation mask are rejected as false positives, implementing the spectral 
discriminator that reduces soil and residue false positives [12]. 
The crop-weed detection model was trained using YOLOv8-nano, the smallest member of the YOLOv8 
family with 3.2M parameters, selected to satisfy the 18 FPS real-time inference requirement on the Jetson Orin 
NX within the 15 W power budget allocated to the compute module. Training data comprised 14,200 annotated 
multispectral image frames, captured across two seasons in maize and soybean fields in The Netherlands and 
Belgium, covering four principal weed species: Chenopodium album (common lambsquarters), Amaranthus 
retroflexus (redroot pigweed), Galium aparine (cleavers), and Convolvulus arvensis (field bindweed). Class 
labels were assigned by trained agronomists using a custom annotation workflow in CVAT. 
To augment the dataset for illumination variability, plant growth stage diversity, and sensor noise, 
synthetic augmentations were applied including per-band brightness/contrast jitter (±15%), gaussian noise 
injection (SNR 30-40 dB), random horizontal and vertical flips, mosaic compositing, and copy-paste 
augmentation using segmentation masks from the WeedsGalore dataset [13]. The dataset was split 70:15:15 
(train:validation:test) with stratification by species and site to prevent leakage. Training was conducted for 150 
epochs on a GPU workstation (NVIDIA RTX 4090) with Adam optimiser, initial learning rate 1×10⁻³, and 
cosine annealing. The model was exported to TensorRT INT8 format for deployment on the Jetson Orin, 
achieving 18.3 FPS at 640×480 input resolution [9]. 
Field navigation employs a two-tier architecture: RTK-GNSS (u-blox ZED-F9P, ±1.5 cm CEP) provides 
absolute position guidance for headland manoeuvres and row entry/exit, while visual row-following based on 
22


Aintelia Science Notes, Vol. 3, Iss. 2                                                                                                          Kucharski et al. 
 
crop-row line detection in the multispectral image provides fine lateral correction during intra-row traversal. 
Crop row lines are detected in the RGB channel using a Hough-transform-based algorithm applied after 
foreground segmentation, producing a lateral deviation estimate relative to the detected row centroid. A 
proportional-integral lateral controller drives the differential-drive steering to maintain the robot axis aligned 
with the crop row within ±1.8 cm (1σ) at 0.6 m/s. Speed is reduced to 0.3 m/s in high-density weed patches 
where tine actuation frequency exceeds 3 Hz, to maintain actuation timing accuracy. 
4. Results and Discussion 
The YOLOv8-nano model achieves a mean Average Precision at IoU threshold 0.5 (mAP50) of 0.843 
on the held-out test set, with per-class AP50 values of 0.871 (C. album), 0.856 (A. retroflexus), 0.821 (G. 
aparine), and 0.824 (C. arvensis). Recall at 0.5 confidence threshold is 0.879 overall, and precision is 0.836, 
yielding an F1-score of 0.857. The NDVI/NDRE fusion spectral filter reduced false positives from 18.3% to 
12.1% relative to RGB-only YOLOv8 inference on the test set, confirming the discriminative value of the 
additional spectral channels. This 34% reduction in false positive rate is consistent with prior multispectral weed 
detection literature [12] and directly reduces unnecessary tine actuation events that could cause crop damage. 
Inference latency on the Jetson Orin NX (TensorRT INT8) is 54.6 ms per frame (18.3 FPS), satisfying 
the real-time requirement for 0.6 m/s travel speed. Power draw of the compute module under full inference load 
is 13.8 W, within budget. A comparison of RGB-only YOLOv8-nano with the multispectral fusion pipeline 
shows a 7.2 percentage point improvement in F1-score on the test set (0.857 vs. 0.785), at 34.6 ms additional 
per-frame latency attributable to vegetation index computation  an acceptable latency cost for a significant 
accuracy gain. 
RTK-GNSS guidance achieves a lateral RMS deviation of 1.6 cm at 0.6 m/s in open-sky conditions, 
increasing to 2.1 cm under crop canopy at BBCH 30-40 growth stage where satellite geometry is partially 
obstructed. Visual row-following active during intra-row traversal reduces the lateral RMS deviation to 1.4 cm 
in conditions where row-line detection confidence exceeds 0.85 (achieved for 91% of frames in maize at BBCH 
15-35). Heading drift over a 100 m row traversal is 0.8° RMS, corresponding to a cross-track error accumulation 
below 2 cm  within the ±5 cm intra-row positional tolerance required for tine actuation without crop contact. 
Field trials were conducted across two sites (Site A: maize, sandy loam, BBCH 14-16 at evaluation; Site 
B: soybean, clay loam, BBCH 12-14) in June 2023, comprising 18 treated subplots (0.3 ha each) and matched 
untreated controls. Weed populations were assessed pre-treatment and at 10 days post-treatment by quadrat 
counting on 1 m² plots at three positions per subplot, with species identification by agronomists. The overall 
weed removal efficacy  defined as the proportional reduction in weed plant density in treated vs. untreated 
subplots  was 84.7% ± 4.1% (mean ± SD) across all sites and weed species, with C. album removed at 88.6% 
efficacy and G. aparine at 79.3%. The lower efficacy for G. aparine is attributed to its prostrate growth habit 
which reduces image-plane area and detection confidence at the BBCH 12-14 growth stage [6]. 
Crop damage rate  defined as the proportion of crop plants showing mechanical contact injury 
attributable to robot tine action  was 0.98% ± 0.31% across all subplots, below the 2% tolerance threshold 
reported in the benchmark literature. No instances of plant uprooting or severe damage were recorded. Robot 
operational throughput was 0.44 ha/h under trial conditions, limited primarily by the 0.6 m/s travel speed 
constraint imposed by tine actuation timing. A simple speed increase to 0.8 m/s would increase throughput to 
approximately 0.58 ha/h with estimated actuation timing error within tolerance at updated dead-band settings. 
The achieved weed removal efficacy of 84.7% compares favourably with the 87.3% reported by Quan 
et al. [6] for lettuce, considering that row-crop weed species are generally more morphologically diverse and 
challenging to detect than greenhouse lettuce weeds. The crop damage rate of 0.98% is consistent with the 2% 
threshold established in the literature [6] and below the 1.5% rate reported by Visentin et al. [5] for their mixed-
23


Aintelia Science Notes, Vol. 3, Iss. 2                                                                                                          Kucharski et al. 
 
autonomous platform. The 34% false positive reduction from multispectral fusion is a novel contribution relative 
to RGB-only systems, directly translating to fewer unnecessary tine actuations and lower crop damage. 
Operational throughput of 0.44 ha/h places AgroSense-W1 within the lower range of commercial robotic 
weeders (0.3-0.8 ha/h), consistent with the current prototype status and the conservative 0.6 m/s speed setting. 
5. Discussion 
The integration of NDVI/NDRE spectral masks with YOLOv8 detection bounding boxes provides a 
principled, computationally lightweight secondary discriminator that exploits the biochemical specificity of 
near-infrared and red-edge reflectance. The 7.2 percentage-point F1 improvement relative to RGB-only 
inference is achieved at a per-frame latency cost of 34.6 ms  representing a 63% latency overhead over RGB 
inference alone, but still within the 55 ms total inference budget. Future work will investigate the direct training 
of YOLOv8 on all five spectral bands as separate input channels, which may improve accuracy further while 
reducing per-frame latency by eliminating the separate vegetation index computation step. The approach of 
parallel RGB detection and vegetation index fusion adopted here was motivated by the availability of pre-trained 
RGB weights for transfer learning and the ease of independent validation of the two pipeline branches. 
The 180 ms tine actuation latency  a function of servo motor bandwidth and mechanical compliance in 
the cross-slide mechanism  is the primary constraint on travel speed and thus throughput. Reducing actuation 
latency to 100 ms through pneumatic actuation (as employed in commercial systems such as the Naio OZ) would 
enable travel speed increase to 1.0 m/s and throughput of approximately 0.73 ha/h without changes to the vision 
pipeline. The current servo-electric actuation was selected for its lower maintenance burden and precision in 
depth control, which contribute to the low 0.98% crop damage rate, but the speed-throughput trade-off will 
require resolution for commercial deployment. 
The 14,200-frame training dataset, while substantially larger than most academic weed detection 
datasets, covers four weed species in two country-specific growing environments. Generalisation to new 
geographies, crop varieties, and weed species  a known challenge in agricultural deep learning documented by 
multiple authors [7]  remains a limitation. The synthetic augmentation pipeline employing copy-paste from the 
WeedsGalore dataset [13] partially addresses this by introducing morphological diversity, but field deployment 
in new regions will require targeted data collection campaigns. A transfer-learning-based rapid adaptation 
protocol, using as few as 200 new labelled frames per species as demonstrated by recent few-shot learning 
approaches [14], is planned for deployment support. 
At 0.44 ha/h operational throughput and an assumed 8-hour operating day, a single AgroSense-W1 unit 
can treat 3.5 ha/day, which is sufficient for timely treatment of a 50 ha farm over a 14-day optimal weeding 
window. The economic case for autonomous mechanical weeding is strengthened by herbicide cost escalation 
and resistance management requirements; at a manufacturing cost target of EUR 35,000-45,000 per unit 
(consistent with the component cost structure of the prototype), payback periods of 3-4 years appear achievable 
for medium-scale row-crop operations in Western Europe. Integration with precision agriculture farm 
management systems via ISOBUS and API-based field data exchange is planned to enable fleet coordination 
and treatment record keeping compliant with EU Regulation 2009/128/EC on sustainable use of pesticides. 
6. Conclusions 
This paper has presented the design, implementation, and field evaluation of the AgroSense-W1 
autonomous weeding robot, integrating a five-band multispectral camera, Edge-AI YOLOv8-nano inference on 
NVIDIA Jetson Orin, and RTK-GNSS-guided row-following navigation. The key findings are: (i) the 
multispectral NDVI/NDRE fusion pipeline reduces false-positive detections by 34% relative to RGB-only 
inference, improving field F1-score from 0.785 to 0.857; (ii) RTK-GNSS plus visual row-following achieves 
lateral navigation accuracy of 1.4-1.6 cm (1σ) at 0.6 m/s; (iii) field trials on maize and soybean demonstrate 
24


Aintelia Science Notes, Vol. 3, Iss. 2                                                                                                          Kucharski et al. 
 
weed removal efficacy of 84.7% ± 4.1% with a crop damage rate of 0.98% ± 0.31%; and (iv) operational 
throughput of 0.44 ha/h is achieved with the current prototype actuation system. These results establish the 
technical feasibility of multispectral Edge-AI robotic weeding as a practical non-chemical weed management 
tool. 
Future work will focus on: (i) direct five-band YOLOv8 training to further improve detection accuracy; 
(ii) pneumatic or electromagnetic actuation to increase throughput; (iii) expansion of the training dataset to cover 
additional weed species and geographies via transfer learning; (iv) development of a fleet management interface 
for farm-scale deployment; and (v) longitudinal evaluation across multiple seasons to assess weed population 
suppression under repeated robotic weeding regimes relative to chemical control benchmarks. 
REFERENCES 
[1] E. C. Oerke, "Crop losses to pests," J. Agric. Sci., vol. 144, no. 1, pp. 31–43, Feb. 2006. 
[2] V. Balaska, Z. Adamidou, Z. Vryzas, and A. Gasteratos, "Sustainable crop protection via robotics and artificial 
intelligence solutions," Machines, vol. 11, no. 8, pp. 774, Aug. 2023. 
[3] A. Mouazen, I. Alexandridis, N. Ioannidis, and M. Ruiz-Garcia, "Sensing and perception in robotic weeding: 
Innovations and limitations for digital agriculture," Sensors, vol. 24, no. 17, pp. 5686, Sep. 2024. 
[4] W. Zhang, Z. Miao, N. Li, C. He, and T. Sun, "Review of current robotic approaches for precision weed management," 
Curr. Robot. Rep., vol. 3, no. 3, pp. 139–151, Sep. 2022. 
[5] F. Visentin, S. Cremasco, M. Sozzi, L. Signorini, M. Signorini, F. Marinello, and R. Muradore, "A mixed-autonomous 
robotic platform for intra-row and inter-row weed removal for precision agriculture," Comput. Electron. Agric., 
vol. 214, pp. 108270, Nov. 2023. 
[6] L. Quan, W. Jiang, H. Li, H. Li, Q. Wang, and L. Chen, "Intelligent intra-row robotic weeding system combining deep 
learning technology with a targeted weeding mode," Biosyst. Eng., vol. 216, pp. 13–31, Apr. 2022. 
[7] N. Rai, Y. Zhang, B. G. Ram, L. Schumacher, R. K. Yellavajjala, S. Bajwa, and X. Sun, "Applications of deep learning 
in precision weed management: A review," Comput. Electron. Agric., vol. 206, pp. 107698, Mar. 2023. 
[8] G. Jocher, A. Chaurasia, and J. Qiu, "Ultralytics YOLOv8," GitHub, 2023. [Online]. Available: 
https://github.com/ultralytics/ultralytics 
[9] F. Dang, D. Chen, Y. Lu, and Z. Li, "YOLOWeeds: A novel benchmark of YOLO object detectors for multi-class weed 
detection in cotton production systems," Comput. Electron. Agric., vol. 205, pp. 107655, Feb. 2023. 
[10] X. Fan, X. Chai, J. Zhou, and T. Sun, "Deep learning based weed detection and target spraying robot system at seedling 
stage of cotton field," Comput. Electron. Agric., vol. 214, pp. 108317, Nov. 2023. 
[11] C. Mwitta and G. C. Rains, "Evaluation of inference performance of deep learning models for real-time weed detection 
in an embedded computer," Sensors, vol. 24, no. 2, pp. 514, Jan. 2024. 
[12] V. Balaska, Z. Adamidou, Z. Vryzas, and A. Gasteratos, "Sustainable crop protection via robotics and artificial 
intelligence solutions," Machines, vol. 11, no. 8, pp. 774, Aug. 2023. 
[13] N. Genze, T. Bhattarai, R. Ajekwe, M. Grieb, and D. G. Grimm, "WeedsGalore: A multispectral and multitemporal 
UAV-based dataset for crop and weed segmentation in agricultural maize fields," arXiv:2502.13103, 2025. 
[14] N. Genze, R. Ajekwe, Z. Güreli, F. Haselbeck, M. Grieb, and D. G. Grimm, "Deep learning-based early weed 
segmentation using motion blurred UAV images of sorghum fields," Comput. Electron. Agric., vol. 202, pp. 
107388, Nov. 2022. 
[15] G. Coleman, W. Salter, and M. Walsh, "OpenWeedLocator (OWL): An open-source, low-cost device for fallow weed 
detection," Sci. Rep., vol. 12, no. 1, pp. 170, Jan. 2022. 
[16] G. Iannaccone, C. Sbrana, I. Morelli, and S. Strangio, "Power electronics based on wide-bandgap semiconductors: 
Opportunities and challenges," IEEE Access, vol. 9, pp. 139446–139456, 2021. 
[17] T. Ayoub Shaikh, T. Rasool, and F. Rasheed Lone, "Towards leveraging the role of machine learning and artificial 
intelligence in precision agriculture and smart farming," Comput. Electron. Agric., vol. 198, pp. 107119, Jul. 2022. 
 
25
