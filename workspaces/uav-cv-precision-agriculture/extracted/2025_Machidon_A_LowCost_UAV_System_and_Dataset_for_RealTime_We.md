---
workspace_id: SCI-000683
doi: 10.3390/electronics14204082
title: A Low-Cost UAV System and Dataset for Real-Time Weed Detection in Salad Crops
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
- family_name: Latini
  given_name: Daniele
  orcid: https://orcid.org/0000-0001-5033-7830
- family_name: Sasidharan
  given_name: Sarathchandrakumar T.
  orcid: https://orcid.org/0000-0002-6335-5955
- family_name: Frate
  given_name: Fabio Del
  orcid: https://orcid.org/0000-0002-1655-0643
- family_name: Machidon
  given_name: Octavian
  orcid: https://orcid.org/0000-0003-3133-1008
year: 2025
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:35:03.362011+00:00'
---

# A Low-Cost UAV System and Dataset for Real-Time Weed Detection in Salad Crops

Article A Low-Cost UAV System and Dataset for Real-Time Weed

Detection in Salad Crops

Alina L. Machidon 1 , Andraž Krašovec 1 , Veljko Pejovi´c 1,2,* , Daniele Latini 3 , Sarathchandrakumar T. Sasidharan 4,5 , Fabio Del Frate 4 and Octavian M. Machidon 1

1 Faculty of Computer and Information Science, University of Ljubljana, 1000 Ljubljana, Slovenia; alina.machidon@fri.uni-lj.si (A.L.M.); ak6688@student.uni-lj.si (A.K.); octavian.machidon@fri.uni-lj.si (O.M.M.) 2 Department of Computer Systems, Institut “Jožef Stefan”, 1000 Ljubljana, Slovenia 3 GEO-K s.r.l., 00133 Rome, Italy; daniele.latini@geo-k.co 4 Department of Civil Engineering and Computer Science Engineering, “Tor Vergata” University of Rome, 00133 Rome, Italy; thtsth01@uniroma2.it (S.T.S.); fabio.del.frate@uniroma2.it (F.D.F.) 5 Department of Civil, Building and Environmental Engineering, Sapienza University of Rome, 00138 Rome, Italy * Correspondence: veljko.pejovic@fri.uni-lj.si


## Abstract

The global food crises and growing population necessitate efficient agricultural land use. Weeds cause up to 40% yield loss in major crops, resulting in over USD 100 billion in annual economic losses. Camera-equipped UAVs offer a solution for automatic weed detection, but the high computational and energy demands of deep learning models limit their use to expensive, high-end UAVs. In this paper, we present a low-cost UAV system built from off-the-shelf components, featuring a custom-designed on-board computing system based on the NVIDIA Jetson Nano. This system efficiently manages real-time image acquisition and inference using the energy-efficient Squeeze U-Net neural network for weed detection. Our approach ensures the pipeline operates in real time without affecting the drone’s flight autonomy. We also introduce the AgriAdapt dataset, a novel collection of 643 high- resolution aerial images of salad crops with weeds, which fills a key gap by providing realistic UAV data for benchmarking segmentation models under field conditions. Several deep learning models are trained and validated on the newly introduced AgriAdapt dataset, demonstrating its suitability for effective weed segmentation in UAV imagery. Quantitative results show that the dataset supports a range of architectures, from larger models such as DeepLabV3 to smaller, lightweight networks like Squeeze U-Net (with only 2.5 M parameters), achieving high accuracy (around 90%) across the board. These contributions distinguish our work from earlier UAV-based weed detection systems by combining a novel dataset with a comprehensive evaluation of accuracy, latency, and energy efficiency, thus directly targeting deep learning applications for real-time UAV deployment. Our results demonstrate the feasibility of deploying a low-cost, energy-efficient UAV system for real-time weed detection, making advanced agricultural technology more accessible and practical for widespread use.

Academic Editors: Umberto Papa,

Giuseppe Del Core, Salvatore Ponte

and Gennaro Ariante

Received: 16 September 2025

Revised: 13 October 2025

Accepted: 14 October 2025

Published: 17 October 2025

Citation: Machidon, A.L.; Krašovec,

A.; Pejovi´c, V.; Latini, D.; Sasidharan,

S.T.; Del Frate, F.; Machidon, O.M. A

Low-Cost UAV System and Dataset

for Real-Time Weed Detection in Salad

Crops. Electronics 2025, 14, 4082.

https://doi.org/10.3390/

electronics14204082

Copyright: © 2025 by the authors.

Keywords: UAV weed detection; energy-efficient computing; squeeze U-Net; real-time inference; precision agriculture

Licensee MDPI, Basel, Switzerland.

This article is an open access article

distributed under the terms and

conditions of the Creative Commons

Attribution (CC BY) license

(https://creativecommons.org/

licenses/by/4.0/).

Electronics 2025, 14, 4082 https://doi.org/10.3390/electronics14204082

Electronics 2025, 14, 4082 2 of 25


## 1. Introduction

The 21st century demands a profound transformation in food production to confront challenges such as a rapidly growing global population, accelerating climate change, and the excessive use of pesticides and herbicides, all of which compromise both crop productivity and food quality. With the world’s population projected to approach 10 billion by 2050, achieving efficient and sustainable agricultural practices is no longer optional but imperative [1]. Precision agriculture (PA) has emerged as a promising paradigm, integrating Information and Communication Technologies (ICT) and Artificial Intelligence (AI) to optimize farm management. By enabling data-driven decision-making, PA supports more efficient use of resources, boosts productivity, and reduces the environmental footprint of farming operations [2].

Weeds remain one of the most pervasive and costly threats to agriculture, reducing crop yields by up to 34% [3] through competition for light, nutrients, and water. Effective weed management is therefore essential for food security. Traditional blanket herbicide application, however, incurs often irreversible environmental damage, including water poisoning, soil contamination, and bee die-offs, to name a few [4]. Furthermore, herbi- cides may have a negative effect on human health as well. Thus, exposure to a widely used herbicide—glyphosate—may cause DNA damage [5]. Finally, the current practice of herbicide use is unlikely to be economically sustainable as well, since the hidden cost of the resulting weed resistance, effect on humans and the environment, and the adjoining regulatory costs may easily overweight the benefits [6]. Instead, targeted approaches such as site-specific spraying can significantly reduce chemical use while maintaining yield potential. In this context, Unmanned Aerial Vehicles (UAVs) have emerged as powerful tools, capable of capturing high-resolution imagery from low altitudes and enabling de- tailed analysis of vegetation morphology, growth stage, and weed infestations [7]. These capabilities make UAVs particularly attractive for precision weed management.

The critical enabler of UAV-based precision agriculture is computer vision, where deep learning methods—especially semantic segmentation—enable fine-grained discrimination of crops, weeds, and background. These approaches have largely replaced manual scouting, opening new opportunities in crop health monitoring, yield estimation, and pest/disease detection [8]. Yet, a fundamental limitation remains: state-of-the-art deep neural networks are computationally demanding—state-of-the-art deep learning from the commonly used YOLO family of architectures may have up to tens of millions of parameters, requiring at least 16 GB of RAM for proper functioning [9]. UAV platforms, on the other hand, are resource-constrained, hosting low-end computing hardware, such as NVIDIA Jetson Nano, often with just a fraction of the necessary memory and computing capabilities. This mismatch between model complexity and on-board hardware capabilities restricts real-time inference, thereby preventing UAVs from realizing their full potential in field-deployable, autonomous weed detection [10].

In this paper, we address this challenge by presenting a low-cost UAV system built entirely from commercially available components and equipped with a custom-designed on-board computing platform based on the NVIDIA Jetson Nano. Our system integrates an energy-efficient semantic segmentation pipeline using the Squeeze U-Net architecture, enabling real-time weed detection during flight without compromising UAV autonomy. In addition, we contribute a novel dataset of 747 annotated UAV images of salad crops with weeds, collected in two fields in Rome, Italy. This dataset not only fills a gap in publicly available resources, which rarely cover leafy vegetable crops, but also provides a benchmark for evaluating real-time segmentation models under realistic field conditions.

The main contributions of this paper are as follows:

Electronics 2025, 14, 4082 3 of 25

• We design and implement a low-cost UAV platform tailored for computer vision tasks in precision agriculture, demonstrating that real-time inference is feasible even on embedded, resource-constrained hardware. • We develop an energy-efficient image acquisition and segmentation pipeline, employ- ing the Squeeze U-Net model to achieve real-time weed detection without sacrificing flight autonomy. • We introduce the AgriAdapt dataset, a new aerial imagery dataset for weed detection in salad crops, comprising 747 annotated images from two crop fields, and provide reference benchmarks using state-of-the-art networks suitable for UAV deployment.

Together, these contributions establish a practical framework for democratizing UAV- based weed detection by lowering costs, reducing energy demands, and providing the community with a benchmark dataset for further research. Our results demonstrate that advanced agricultural technologies can be made accessible and deployable at scale, paving the way for widespread adoption of precision weed management.

The remainder of this paper is organized as follows: Section 2 reviews related work on real-time UAV image processing and weed detection datasets. Section 3 details the UAV platform, dataset, and neural networks. Section 4 presents the experimental setup and results, including performance, timing, and resolution trade-offs. Section 5 discusses the implications of our findings, and Section 6 concludes the paper with key insights and directions for future research.


## 2. Background and Related Work

Precision agriculture increasingly relies on UAV platforms equipped with computer vision systems to monitor crop conditions, detect weeds, and enable targeted interven- tions. However, deploying such technologies in practice faces two critical challenges. First, most UAV systems capable of performing deep learning inference in real time remain prohibitively expensive, limiting their accessibility to large-scale operations. Second, while several aerial image datasets for weed detection exist, they are typically restricted to certain crop types, geographic regions, or offline post-processing, with limited consideration of lightweight architectures suitable for on-board deployment. In this section, we review related work addressing these two aspects. The first subsection examines efforts to design cost-effective UAV platforms for real-time agricultural imaging. The second subsection surveys publicly available UAV-based weed detection datasets, highlighting their strengths and limitations in relation to the contributions of our work: a low-cost UAV system for real- time weed detection and the introduction of the novel AgriAdapt dataset with benchmark results on state-of-the-art networks.

2.1. Real-Time UAV Image Processing in Precision Agriculture

Unmanned Aerial Vehicles (UAVs) have rapidly become central tools in precision agriculture, offering high-resolution imagery for tasks such as crop monitoring, yield estimation, and weed management. However, UAVs capable of performing on-board image processing with deep learning are often prohibitively expensive due to the substantial computational resources required. This has motivated a growing body of research into affordable UAV platforms that balance performance, cost, and energy efficiency.

Several studies have explored low-cost UAV solutions for agricultural applications. De Oca and Flores [11] introduced AgriQ, a cost-effective UAV system that integrates mod- ified multispectral cameras with open-source processing software, achieving competitive performance at a fraction of the cost of commercial systems. Czymmek et al. [12] developed a crop row detection system based on a Raspberry Pi and camera, showing that with tar- geted optimizations, even resource-constrained platforms can achieve frame rates sufficient

Electronics 2025, 14, 4082 4 of 25

for practical navigation in organic farming. Along similar lines, Cucho-Padin et al. [13] pro- posed IMAGRI-CIP, an affordable UAV-mounted multispectral sensor array coupled with open-source software for image alignment, stitching, and crop classification; validation in Peru and Tanzania demonstrated the potential of such systems for smallholder agriculture.

Beyond imaging, low-cost UAVs have also been coupled with IoT-based monitoring. Almalki et al. [14] presented a UAV–IoT system deployed in Tunisia to collect and trans- mit environmental data for cloud-based analysis, enabling real-time farm management. Karatzinis et al. [15] combined low-cost UAVs with intelligent coverage path planning (Spiral-STC) and image analysis, producing geo-referenced orthophotos for crop health monitoring and irregularity detection. Other domain-specific applications highlight the versatility of affordable UAV platforms: Vacca [16] used the DJI Mini2 to estimate tree height from 3D reconstructions, while Rangarajan et al. [17] applied deep convolutional networks (SqueezeNet and ResNet-18) on UAV imagery to detect Cercospora Leaf Spot in okra, exemplifying the role of compact deep learning models in plant disease monitoring.

Cost-effective UAVs have also been studied in broader agricultural workflows. Jang et al. [18] reviewed UAV platforms for high-throughput plant phenotyping, em- phasizing accessibility for research institutions. Cucchiaro et al. [19] proposed a low- cost UAV–SfM workflow for mapping vegetation obstructions in irrigation ditches, gen- erating high-resolution digital elevation models to aid water management. Jiménez- Jiménez et al. [20] similarly reviewed UAV photogrammetry techniques for digital terrain model (DTM) generation, highlighting accuracy and methodological considerations for agricultural use.

Taken together, these studies demonstrate that low-cost UAVs can deliver valuable agricultural insights across a range of sensing and monitoring tasks, making advanced technologies accessible to a wider audience. Nonetheless, one critical limitation emerges: while many systems provide affordable imaging and offline processing pipelines, the chal- lenge of real-time onboard operation remains only marginally addressed. Among the reviewed works, very few explicitly claim real-time performance of computer vision tasks on resource-constrained UAV hardware. While our preliminary research presents the initial conceptualzation of a low-cost UAV system [21], this paper directly addresses the identified gap by demonstrating that real-time deep learning inference for weed detection is feasible on a low-cost UAV system without compromising flight autonomy, thereby advancing the state of the art in practical, energy-efficient precision agriculture.

2.2. Aerial Image Weed Detection Datasets

The review of existing UAV-based weed detection datasets reveals impressive progress in terms of sensing modalities, annotation granularity, and crop diversity. Early efforts such as WeedMap [22] focused on multispectral orthomosaics of sugar beet fields, providing radiometrically calibrated, large-area maps but with limited real-time applicability. More recent collections, including CoFly-WeedDB for cotton [23] and WeedsGalore for maize [24], expanded into polygon- and instance-level annotations, sometimes across multiple time points, thus enabling species-level analysis and temporal robustness. Additional datasets cover soybean and common bean [25], sesame [26], tobacco [27], and sorghum [28], but are often constrained either by small geographic scope, crop-specific focus, or controlled conditions. Several datasets are also orthomosaic-oriented, prioritizing mapping and post-processing rather than the low-latency, frame-level inference required for onboard UAV operation.

Despite these advances, important gaps remain. First, leafy vegetables and salad crops are notably underrepresented in publicly available datasets, even though they are highly sensitive to weed competition and critical for fresh food supply chains. Second, few datasets explicitly report acquisition metadata such as UAV altitude, ground sampling

Electronics 2025, 14, 4082 5 of 25

distance, or illumination variability, which are essential for assessing generalization across different fields and conditions. Third, real-time applicability is seldom addressed: most datasets are designed for offline training and analysis, rather than validating complete UAV pipelines that must balance accuracy, latency, and energy efficiency.

Our AgriAdapt dataset introduced in this paper directly addresses these shortcom- ings. It provides 747 UAV-acquired RGB images of salad crops with weeds, systematically collected over two distinct fields in Rome, Italy. The dataset is annotated at the pixel level, designed not only for training but also for validating real-time inference in embedded UAV systems. By focusing on salad crops, AgriAdapt fills a clear crop-specific gap; by releasing acquisition parameters and flight context, it enhances reproducibility and benchmarking; and by coupling the dataset with a fully integrated low-cost UAV pipeline, it establishes a realistic testbed for advancing precision agriculture towards practical, energy-efficient deployment. Moreover, we provide reference benchmark results on AgriAdapt using sev- eral state-of-the-art deep learning models, including lightweight architectures suitable for real-time inference on UAV-compatible hardware. This dual contribution—a new dataset together with validated baselines—ensures that AgriAdapt serves both as a benchmark for academic research and as a foundation for practical UAV-based weed detection systems. As such, AgriAdapt complements and extends the current landscape of UAV weed detec- tion datasets, offering both a new benchmark and a concrete step toward democratizing AI-enabled crop monitoring.

2.3. Comparative Analysis of Existing UAV Systems and Datasets


> **Table 1 shows that prior UAV solutions frequently favor sensing diversity and accuracy**

> (e.g., multispectral, high-resolution orthomosaics) at the expense of cost and on-board
feasibility, resulting in offline pipelines [22–24,29]. In contrast, embedded approaches
demonstrate that real time is attainable on edge GPUs but throughput is highly sensitive
to model size and hardware power budget (e.g., NVIDIA Jetson TX2, NVIDIA, Santa
Clara, CA, USA at 15 W reaching 5–20 FPS) [30]. This evidences a clear trade-off: higher
resolution and complexity generally improve segmentation quality but increase compute
and energy demands; aggressive model compression reduces latency and power but can
degrade accuracy. The proposed AgriAdapt platform targets a balanced point on this
spectrum, sustaining on-board real-time inference (30.6 FPS on NVIDIA Jetson Nano,
5–10 W) with competitive segmentation performance (cf. Section 4) and a total system cost
below ∼EUR 1500, thereby improving deployability without sacrificing flight autonomy.


> **Table 1. Comparison of representative UAV-based weed detection systems and datasets versus the**

> proposed AgriAdapt platform, highlighting cost, resolution, processing mode, and main limitations.

Study/Dataset Crop Type Platform Image Resolution Processing Key Limitation

Expensive sensors; mapping-oriented; no

∼10 cm/pixel (orthomosaic) Offline

WeedMap [22] Sugar beet Multispectral UAV;

high cost

on-board inference

CoFly-WeedDB [23] Cotton Commercial UAV;

moderate cost 12 MP RGB Offline (dataset) Dataset-only; lacks real-time validation

Weeds-Galore [24] Maize Commercial UAV;

moderate cost 4000 × 3000 Offline (dataset) High-resolution multispectral;

offline segmentation

Milioto et al. [30] Sugar beet Robot/Jetson TX2

(15 W) 1024 × 1024 On-board Limited crop generalization;

higher power use

Multimodal input; computationally heavy

Bosilj et al. [29] Carrot, onion RGB+NIR sensors; moderate–high cost 2428 × 1985 Offline

for UAVs

Accurate (86 mIoU) but

DSC- DeepLabv3+ [31] Maize – 512 × 512 Offline

non-real-time; desktop

GPU only

AgriAdapt (ours) Salad crops RGB sensors

1280 × 1280 (GSD 0.4 cm/pixel) On-board (real-time) Balanced cost and accuracy; high efficiency under low power

Low-cost

Electronics 2025, 14, 4082 6 of 25


## 3. Materials and Methods

3.1. UAV System

For the AgriAdapt experiment, we developed a custom UAV system featuring a hexa- rotor design with a maximum take-off weight of up to 6 kg (as shown in Figure 1). This UAV is equipped with a Plug and Play System that allows for quick switching between different payloads. It supports real-time mission management and Autonomous Waypoint navigation, facilitated by the Pixhawk PX4 flight controller, manufactured by Dronecode Foundation, San Francisco, CA, USA. The PX4 integrates an Inertial Measurement Unit (IMU), which includes accelerometers and gyroscopes, along with a Global Positioning System (GPS) receiver. Table 2 summarizes the key hardware components of the UAV platform and their indicative single-unit prices, highlighting its affordability and suitability for low-cost precision agriculture applications.


> **Figure 1. The UAV system designed for the AgriAdapt experiment equipped with an ArduCam**

> camera and an NVIDIA Jetson Nano Board.

Our UAV configuration includes an Nvidia Jetson Nano, powered by an independent battery supply, and a radio transceiver module for remote communication with the ground control station. A schematic overview of the entire configuration is depicted in Figure 2. The Jetson Nano connects to the PX4 flight controller via a serial UART protocol, allowing access to telemetry data. The payload features an Arducam autofocus camera equipped with a Sony IMX519 sensor (Sony Corporation, Tokyo, Japan), offering 16 MP spatial resolution. To ensure high-quality image acquisition, the camera is mounted on a 2-axis gimbal with brushless motors for stabilization.


> **Figure 2. Diagram of the UAV system payload and ground control components. The payload includes**

> a Jetson Nano, RGB camera, GPS module, communication transceiver, and battery power system.
Ground control comprises a PC that connects via a COM port to the onboard transceiver, enabling
UAV and payload monitoring and control.

Electronics 2025, 14, 4082 7 of 25


> **Table 2. Bill of materials and indicative single-unit prices (EU retail, 2025) for the low-cost UAV**

> platform used in this study. Prices exclude shipping, customs, wiring/fasteners, and tools.

Component Model/Specification Function ~Cost (€)

Flight controller Pixhawk PX4 (Pixhawk

4-class) Autonomous navigation

and telemetry 130

On-board computer NVIDIA Jetson Nano

(4 GB) Real-time inference 150

Camera Arducam IMX519 (16 MP,

autofocus) RGB imaging 65

Gimbal 2-axis brushless (micro) Image stabilization 85 GPS module u-blox NEO-M9N Geotagging 50

Transceiver LoRa HM-TRLR-D

Ground–UAV communication 35

(868 MHz)

Battery pack (UAV) 6S Li-Po 14 Ah, ≥25 C (custom-assembled, Italy) Main propulsion battery 210

Neewer NP-F750, 7.4 V,

Jetson Nano exclusive

Battery pack (Jetson)

5200 mAh (Neewer, Shenzhen, China)

power supply 35

Frame + motors + ESCs Custom hexarotor kit (3508/3510, 13–15′′ props) Propulsion system 700

Total (UAV + payload) 1460

This system is capable of a maximum flight time of up to 20 min. The Italian Civil Aviation Authority (ENAC) has certified the design, ensuring compliance with both Italian and European (EASA) regulations.

The payload system is designed to integrate high-performance components that facilitate real-time weed detection and geotagging in agricultural fields. It includes an RGB camera, a GPS module, a processing unit, and a communication transceiver, all working together to ensure precise data collection, processing, and storage.

The Arducam 16 MP Autofocus Camera (Arducam Technology Co., Ltd., Hong Kong, China) plays a critical role in capturing high-resolution images of the agricultural field. With its 16 Megapixel resolution (4608 × 3456), the camera provides the detailed imagery necessary for precise analysis. The autofocus feature was enabled to maintain sharp image quality even when the UAV was in motion, ensuring that vegetation contours remained well-defined. The camera operated with fixed exposure and color parameters, as radiometric calibration and automatic white balance were not applied. This configuration ensured consistent image characteristics across flights, minimizing illumination-induced variations while preserving radiometric comparability. The camera is mounted on a 2-axis gimbal, which stabilizes the images during flight by compensating for UAV movements.

The NEO-M9N GPS Module (u-blox AG, Thalwil, Switzerland) provides accurate ge- olocation data. Supporting multiple GNSSs (Global Navigation Satellite Systems) including GPS, GLONASS, Galileo, and BeiDou, it enhances positioning accuracy. The GPS module offers horizontal accuracy within 2.0 m and vertical accuracy within 4.0 m, essential for precise mapping. While this level of accuracy is not sufficient for individual plant localiza- tion, it is adequate for field-level referencing and flight-path logging, as image overlap and relative positioning ensure spatial consistency within each field. Its high update rate, up to 10 Hz, ensures timely and continuous location updates during UAV operations, providing reliable data for geotagging.

Central to the payload system is the NVIDIA Jetson Nano, which performs real-time image analysis and processing using onboard AI algorithms. The Jetson Nano features an NVIDIA Maxwell architecture GPU with 128 CUDA cores, delivering the computational power required for deep learning tasks. Its quad-core ARM Cortex-A57 CPU supports efficient multitasking and data processing, while the 4 GB 64-bit LPDDR4 memory ensures

Electronics 2025, 14, 4082 8 of 25

smooth operation of multiple neural networks in parallel. Connectivity options, including Gigabit Ethernet, USB 3.0 ports, and MIPI CSI-2 for the camera interface, facilitate the inte- gration of various sensors and peripherals, making the Jetson Nano a powerful processing unit for the payload system.

The Jetson Nano was selected as the onboard computing platform because it provides a favorable balance between processing capability and energy efficiency, which is critical for real-time UAV operation. The board is capable of running modern deep learning inference tasks while consuming as little as 5–10 W of power, making it suitable for battery-powered aerial platforms. Its small form factor and low thermal profile further support seamless integration into lightweight UAV payloads.

The LoRa HM-TRLR-D TTL-868 Transceiver (Hope Microelectronics Co., Ltd., Shen- zhen, China) ensures robust long-range communication between the UAV and the ground station. Operating at a frequency of 868 MHz, the transceiver supports data rates of up to several hundred kbps, suitable for transmitting essential status updates and operational data. The LoRa transceiver maintains stable communication over several kilometers in line-of-sight conditions, ensuring reliable connectivity during UAV missions.

The Ground Station Control Software (custom-developed) is crucial for managing real-time monitoring and control of the UAV and its payload. Developed using Python and PyQt, the software provides a user-friendly interface for operators. It allows for starting, pausing, and stopping data acquisition, as well as monitoring the system’s status, including battery levels and live data feeds. This software ensures that UAV and payload operations are managed efficiently, facilitating seamless data collection and analysis.

3.2. Dataset

We evaluated our approach on two UAV-based weed detection datasets: an initial small-scale dataset for preliminary validation and a new, dedicated dataset that constitutes one of the main contributions of this work. The preliminary dataset consisted of several hundred raw UAV images collected with consumer-grade drones over mixed test fields containing different crop species. This dataset was used exclusively for early validation of the processing pipeline.

Building upon this, we acquired a new salad-weed dataset using the UAV system described in Section 3.1. The dataset was collected over salad fields at different growth stages (approximately 25–65 days old). Flights were conducted at an average altitude of 5 m, resulting in a ground sampling distance of 0.4 cm/pixel. All images were captured at a resolution of 1280 × 1280 pixels using the UAV’s stabilized RGB camera. Figure 3 shows representative UAV images of salad rows interspersed with weeds, while Figure 4 illustrates the manually annotated masks, where weeds are highlighted in red overlay and all other areas—including crop (salad) rows—are considered as background.

To facilitate systematic use, the dataset is organized into two main partitions: Field_ID_1 and Field_ID_2.

• Field_ID_1: Acquired during three consecutive short flights over adjacent salad fields. The original collection comprised 397 images. After manual inspection, images with no useful crop content (e.g., field edges, empty soil regions) were discarded, resulting in 322 annotated images. • Field_ID_2: Acquired more than one month later over a larger, adjacent field. The orig- inal set included 408 images, of which 321 were retained after quality control.


> **Table 3 summarizes the dataset partitions, including acquisition dates, locations,**

> and environmental conditions. In total, the dataset contains 643 high-quality images
across the two partitions. Each image was manually labeled in YOLOv7 PyTorch format,
distinguishing between salad crops and weeds. Pixel data were standardized by removing

Electronics 2025, 14, 4082 9 of 25

EXIF-based orientation metadata and resizing all images to 640 × 640 pixels, using bilinear interpolation. Because the original UAV images were captured at 1280 × 1280 pixels with a square aspect ratio, resizing to 640 × 640 did not require stretching, padding, or other aspect-ratio adjustments. No additional pre-processing was applied, preserving the raw visual information.

The annotation process was performed manually by two trained annotators using the Roboflow online platform [32]. Each image was independently segmented at the pixel level to distinguish between weed and crop regions. For morphologically similar cases (e.g., salad seedlings vs. low-growing broadleaf weeds), annotators relied on vis- ible leaf-edge serration and venation patterns to ensure consistent differentiation. To ensure consistency, the two annotators cross-checked and refined each other’s labels un- der supervision of the dataset curator. Final masks were exported in YOLOv7-compatible PyTorch format, ensuring standardized input for all network training procedures. This manual double-annotation process ensured high-quality ground truth data and minimized labeling bias.

This dataset is made publicly available (Dataset available at: https://app.roboflow. com/agriadaptweeddetection/agriadapt-uex2n/overview (accessed on 25 September 2025)) and serves as a benchmark for evaluating real-time weed detection in salad crops. Also, because it was acquired using the same hardware pipeline deployed for inference experiments, it provides a realistic testbed for developing and validating lightweight models suitable for embedded UAV platforms.


> **Figure 3. Sample images from the AgriAdapt dataset, showing UAV views of a crop field with salad**

> rows and interspersed weeds.


> **Figure 4. Sample images from the AgriAdapt dataset with weeds highlighted in red overlay, illustrat-**

> ing UAV views of a crop field containing rows of salad plants and interspersed weeds.

Electronics 2025, 14, 4082 10 of 25


> **Table 3. Summary of the AgriAdapt dataset partitions, including number of images, acquisition**

> details, and field conditions.

Field Id Nb. of Images Geographical Coord. (Lat./ Long.) Acquisition Date Soil Condition/

Sunlight

41°49′38.7′′ N, 12°29′54.9′′ E 41°49′40.0′′ N, 12°29′57.9′′ E

Warm soil, moderate

11 Septemner 2023 13:30

moisture, partly

001 322

cloudy, strong

sunlight

41°49′37.5′′ N, 12°29′55.3′′ E 41°49′40.2′′ N, 12°29′57.6′′ E

Warm soil, moderate

20 October 2023 14:30

moisture, partly

002 321

cloudy, strong

sunlight

3.3. Neural Networks

To evaluate the dataset and set baseline performance benchmarks across different network architectures, we train and evaluate on the proposed dataset several state-of-the- art deep learning models for image segmentation, specifically the DeepLab V3 [33] model, the LRASSP [34] model, and the Squeeze U-Net [35] model.

3.3.1. Model Architectures

DeepLabV3 is known for its powerful multi-scale feature extraction capabilities, largely due to its atrous (or dilated) convolutions and Atrous Spatial Pyramid Pooling module. Atrous convolutions allow the model to capture context across various scales without reducing spatial resolution, making it adept at handling images with objects of varying sizes. This is especially useful in segmentation tasks where distinguishing between large and small objects within the same image is crucial. The Atrous Spatial Pyramid Pooling module enhances this by applying multiple atrous convolutions with different rates, effectively capturing both fine-grained details and larger spatial contexts. However, the advanced architecture makes DeepLabV3 computationally expensive, requiring more processing power and memory compared to other segmentation architectures like U-Nets. This can be a limiting factor for real-time applications or environments with constrained hardware. Additionally, because DeepLabV3 does not inherently include symmetric skip connections, it may struggle to integrate low-level features from earlier layers with high- level semantic features. This can result in difficulties when segmenting objects with intricate shapes or boundaries, where fine-grained details are essential.

The LRASSP model [34] is a lighter segmentation model designed to be computation- ally efficient while maintaining accuracy by refining feature maps from multiple layers. Its symmetric skip connections are particularly useful for segmenting complex shapes, as they allow the model to leverage both high-resolution, low-level features (capturing details like edges) and lower-resolution, high-level features (understanding context). These skip con- nections make LRSSP effective in scenarios requiring high spatial accuracy and boundary detail. While LRSSP provides a more lightweight alternative to models like DeepLabV3, it may sacrifice some of the contextual understanding provided by the multi-scale Atrous Spatial Pyramid Pooling module in DeepLabV3. This can make LRSSP less effective for images containing objects of significantly different sizes, as it might struggle to recognize objects within a larger context.

Finally, Squeeze U-Net [35] is a compact model (in terms of parameter count) that combines U-Net’s symmetric skip connection design with Squeeze-and-Excitation blocks for parameter efficiency. Squeeze-and-Excitation blocks enable the model to selectively emphasize important features and suppress irrelevant ones, making the architecture lighter and faster. Like LRSSP, the symmetric skip connections in Squeeze U-Net allow it to retain

Electronics 2025, 14, 4082 11 of 25

detailed information from the input image, making it suitable for segmenting objects with complex boundaries and high-detail requirements. Its design is typically more computa- tionally efficient than DeepLabV3, making it well-suited for real-time segmentation tasks on lower-end hardware. One limitation of Squeeze U-Net comes from the fact that it may not properly handle images with substantial variation in object size or requiring extensive context. The lack of advanced multi-scale feature extraction methods like Atrous Spatial Pyramid Pooling can make it less effective in distinguishing between small and large objects within the same image.

3.3.2. Training Protocol

We train and evaluate all neural network models on the above-described publicly available AgriAdapt weed detection dataset. We employed an 80/20 train/test split on the entire dataset for obtaining the subsets for training and evaluation. All images were resampled to a uniform size of 512 × 512 pixels and rescaled to a range of [0.0, 1.0] to normalize pixel intensity values. The impact of the image resolution on the network performance is further discussed in Section 4.2.3.

We trained the models for a maximum of 500 epochs, with an early termination criteria, that stops the training if no validation accuracy improvement is observed for 10 consecutive epochs, a commonly adopted strategy to prevent overfitting while ensuring sufficient convergence time [36]. The batch size used for training was 16, which represents a compromise between the memory limitations of the GPU and training stability, in line with prior work on segmentation of high-resolution images [33]. For optimization, we used the Adam optimizer with an initial learning rate of 0.0001 which has been shown to provide stable convergence in complex deep architectures [37]. The learning rate was exponentially decreased with a factor of 0.99, for stabilizing the training process. To address the strong unbalance between the background and weed classes, we trained the networks with a weighted cross entropy loss function with weights of 0.1 and 0.9 for the background and the weeds class, respectively. Weighted loss functions are frequently used in semantic segmentation to counter the dominance of majority classes and improve minority class detection [38]. Finally, we applied an L2 regularization penalty of 0.0001 on the weights of the networks when computing the loss to prevent it from over-fitting to the majority (background) class, a standard practice to mitigate overfitting and improve generalization [37].

All neural network models were trained on an Nvidia RTX 3090 GPU with 24 GB of memory. The PyTorch deep learning framework was used to implement and train all models. Readers are referred to the open-source code at https://gitlab.fri.uni-lj.si/ lrk/agriadapt-electronics (accessed on 13 October 2025) for the details of the design and implementation of the training of the deep learning models.


## 4. Experimental Setup and Results

4.1. Evaluation Metrics

To assess the dataset and establish baseline performance scores achievable with various network architectures, we evaluate using metrics such as Intersection over Union (IoU) and accuracy, two widely adopted metrics for evaluating segmentation performance.

The IoU, also known as the Jaccard index, is defined as the intersection between the ground truth and the predicted segmentation mask, divided by the union of both:

IoU(truth, pred) = |truth ∩pred|

|truth ∪pred| (1)

Electronics 2025, 14, 4082 12 of 25

Accuracy measures the percentage of correctly classified pixels in the entire image dataset. It is calculated by dividing the sum of true positive (TP) and true negative (TN) pixels by the total number of pixels in the dataset, which includes the sum of true positive TP, false positive (FP), and false negative (FN) pixels. Mathematically, the formula for

semantic segmentation overall accuracy is:

OA = TP + TN TP + TN + FN + FP (2)

Recall is given by the ratio of correctly predicted positives within a set of all positive values:

Recall = TP TP + FN (3)

The F1-score is a harmonic mean of precision and recall:

F1-score = 2 · Precision · Recall

Precision + Recall = 2 TP 2 TP + FP + FN (4)

Additionally, we report the number of parameters and floating-point operations per second for each network. The number of parameters in a neural network represents the total count of adjustable weights and biases, determining the model’s capacity and complexity. GFLOPS quantifies the computational workload of a neural network by measuring the rate of billion floating-point operations performed per second during processing.

4.2. Image Segmentation Evaluation 4.2.1. Weed Detection Performance


> **Table 4 presents the performance metrics of several deep learning models trained**

> and evaluated on the AgriAdapt dataset: DeepLabV3 and LRASPP with a MobileNet V3
backbone, as well as Squeeze U-Net. DeepLabV3 (Mobilenet V3) has the highest number
of parameters (11.0 million) and GFLOPS (10.45), with an IoU of 56.87 and an accuracy of
91.08%. LRASPP (MobileNet V3) is more lightweight, with only 3.2 million parameters
and 2.09 GFLOPS, achieving an IoU of 59.25 and a higher accuracy of 91.72%. Squeeze
U-Net is the most parameter-efficient model with 2.5 million parameters and 6.6 GFLOPS.
It achieves an IoU of 55.45 and an accuracy of 89.84%. The comparison of the three models’
performance on the AgriAdapt data is also depicted in Figure 5, highlighting the trade-offs
between model complexity (in terms of parameters) and performance in terms of IoU
and accuracy.


> **Table 4. Performance metrics of deep learning models trained and evaluated on the collected dataset,**

> including accuracy, Intersection over Union (IoU), number of parameters (Params), and floating-point
operations per second (GFLOPS) across various neural network models.

Model Params (M) GFLOPS IoU Accuracy Recall F1-Score

DeepLabV3 (Mobilenet V3) 11.0 10.45 56.87 91.08 65.18 71.05 LRASPP (MobileNet V3) 3.2 2.09 59.25 91.72 67.30 72.99 Squeeze U-Net 2.5 6.6 55.45 89.84 59.36 69.68

Weed detection is particularly challenging due to class imbalance, as weeds are typi- cally underrepresented compared to background or crop pixels. The normalized confusion matrix for background and weeds (Figure 6) shows high accuracy for background pixels (more than 91%) and somewhat lower recall and precision for sparse weed pixels (73%), highlighting common misclassifications and the potential benefit of strategies such as data augmentation to further improve weed detection.

Electronics 2025, 14, 4082 13 of 25


> **Figure 5. The relationship between model size (in terms of parameters) and performance (IoU and**

> Accuracy) for the three neural network models.


> **Figure 6. Normalized confusion matrix for the DeepLabV3 model, showing classification performance**

> for background and weed classes.

The analysis of the weed prediction masks generated by the three deep learning mod- els, DeepLabV3, LRASPP, and Squeeze U-Net (Figure 7), reveals distinct characteristics in each model’s approach to segmentation, particularly in terms of sensitivity, precision, and overall coverage of weed patches. Each model exhibits different strengths and limita- tions, providing insights into their suitability for UAV-based weed detection applications.

DeepLabV3 demonstrates extensive weed coverage across the samples, effectively capturing larger weed clusters and providing a comprehensive representation of weed presence in areas with dense weed patches. This model is particularly sensitive to detecting a broad range of weed regions, which is beneficial in scenarios where missing any weeds is critical. However, DeepLabV3 has a tendency toward over-prediction, occasionally classifying non-weed areas as weeds. This over-prediction is especially noticeable in regions with bare soil, where the model inaccurately highlights sections as weed-covered (Figure 7b). In addition, while DeepLabV3’s high sensitivity is advantageous for ensuring maximum weed detection, it may lead to a higher rate of false positives in areas where weed density is low or where precise boundaries are needed, for example, to distinct between weeds and crops.

Electronics 2025, 14, 4082 14 of 25

(a) Image sample


## 1 Grountruth

(b) Image sample 1

(c) Image sample


## 1 LRASPP

(d) Image sample 1

DeepLabV3

Squeeze U-Net

(e) Image sample


## 2 Grountruth

(f) Image sample 2

(g) Image sample


## 2 LRASPP

(h) Image sample 2

DeepLabV3

Squeeze U-Net

(i) Image sample


## 3 Grountruth

(j) Image sample 3

(k) Image sample


## 3 LRASPP

(l) Image sample 3

DeepLabV3

Squeeze U-Net

(m) Image sample


## 4 Grountruth

(n) Image sample 4

(o) Image sample


## 4 LRASPP

(p) Image sample 4

DeepLabV3

Squeeze U-Net

(q) Image sample


## 5 Grountruth

(r) Image sample 5

(s) Image sample


## 5 LRASPP

(t) Image sample 5

DeepLabV3

Squeeze U-Net


> **Figure 7. Sample images from the AgriAdapt dataset with groundtruth annotations and weed**

> prediction masks (highlighted in red overlay) obtained using the DeepLabV3, LRASPP and Squeeze
U-Net deep learning models.

The LRASPP model, on the other hand, exhibits better precision with more accu- rately defined boundaries between weed and non-weed areas. LRASPP reduces the likelihood of false positives, which is advantageous for applications that prioritize con-

Electronics 2025, 14, 4082 15 of 25

tainment and require reliable exclusion of non-weed regions. This model’s outputs are generally more contained, with fewer instances of over-prediction compared to DeepLabV3, Figure 7b vs. Figure 7c. However, this focus on precision comes at the expense of sensitiv- ity. LRASPP occasionally under-predicts in sparse regions, failing to capture smaller or isolated weed patches effectively (Figure 7k). This limitation suggests that while LRASPP is beneficial for applications needing high accuracy in discriminating weeds from bare soil, it may miss some weeds in low-density areas, potentially impacting its effectiveness in more heterogeneous environments.

Squeeze U-Net offers a balanced approach, combining some of the coverage strengths of DeepLabV3 with the precision characteristics of LRASPP. This model captures both large and small weed clusters with a degree of accuracy, providing reasonable weed cov- erage without excessive over-prediction. Squeeze U-Net is effective for general weed detection tasks where both comprehensive coverage and precision are important, partic- ularly in applications that require a middle ground between maximizing weed detection and minimizing false positives. Nonetheless, Squeeze U-Net occasionally over-predicts in certain areas (Figure 7d), similar to DeepLabV3, suggesting that while it avoids the extremes of either sensitivity or precision, it is not entirely immune to classification errors in non-weed regions.

Overall, the analysis of the prediction masks produced by each model on the Agri- Adapt suggests that each model has distinct advantages that may make it more or less suitable depending on the specific requirements of a UAV-based weed detection application. DeepLabV3 is ideal for applications where high sensitivity is critical, as it captures extensive weed coverage with a tolerance for some false positives. LRASPP is more suited for con- trolled environments where precision is paramount, minimizing false positives but at the risk of missing smaller weeds. Squeeze U-Net, with its balanced performance, is versatile for general applications that need a compromise between detection coverage and precision. To address common failure modes, such as over-prediction on bare soil or missed small weed patches, future work could incorporate mitigation strategies including multi-scale feature extraction, data augmentation to simulate challenging conditions (e.g., low light), and transfer learning from related agricultural datasets to improve generalization.

A cross-domain comparison of our semantic segmentation models with previous work highlights the challenges of direct comparison, as datasets differ in crop type, scene complexity, number of classes, input modalities, and image resolution. In UAV-based weed detection, DSC-DeepLabv3+ [31] achieves an mIoU of 86.3% on maize fields using a large backbone (Xception, 54.7M parameters, 167 GFLOPs), but its high computational cost limits real-time deployment on embedded UAV platforms. In contrast, our models, Squeeze U-Net (2.5M parameters, 6.6 GFLOPs), LRASPP (3.2M, 2.09 GFLOPs), and DeepLabV3 Mo- bilenetV3 (11M, 10.45 GFLOPs), achieve reasonable IoU (55–59%) on the AgriAdapt dataset while delivering real-time inference (up to 42.9 FPS), emphasizing lightweight, deployable architectures. Importantly, DSC-DeepLabv3+ was tested on dense pixel-level annotations, which typically yield higher reported accuracy, whereas AgriAdapt uses patch-based la- beling that better reflects UAV imagery but poses a more challenging task. Comparisons with other agricultural datasets further illustrate the impact of dataset characteristics on performance. Milioto et al. [30] report mIoU values between 48% and 80% on sugar beet weed segmentation using 14-channel inputs. Their approach runs at 20 FPS on a GTX1080Ti GPU and 5 FPS on the Jetson TX2 (15 W peak power). By contrast, our Squeeze U-Net achieves 30.6 FPS directly on the lower-power Jetson Nano (5–10 W) with 55.45 mIoU and 89.8% accuracy, showing that real-time UAV deployment is feasible with much smaller models. Bosilj et al. [29] achieved 98.2% precision for soil, 80.6% for weeds, and 76.0% for crops using a SegNet architecture trained on carrots and onions with RGB and NIR images

Electronics 2025, 14, 4082 16 of 25

at a very high input resolution (2428 × 1985 pixels). While effective, this setup relies on multimodal inputs and significantly higher-resolution imagery, making it difficult to deploy on embedded UAV platforms.

4.2.2. Timing Evaluation

All inference timing and energy consumption measurements were performed di- rectly on the NVIDIA Jetson Nano platform integrated into the UAV system. Table 5 and Figures 8 and 9 compare the average inference time and energy consumption per image for the three deep learning models under evaluation: Squeeze U-Net, DeepLabV3, and LRASPP. The results clearly highlight the advantages of Squeeze U-Net in terms of computational efficiency. On average, Squeeze U-Net required only 0.0327 s per image, which is nearly 40% faster than LRASPP (0.0532 s) and more than 70% faster than DeepLabV3 (0.0565 s). This reduction in latency is particularly critical for real-time UAV deployment, where frame-by-frame inference must keep pace with image acquisition rates during flight.

In terms of throughput, the measured inference times correspond to average frame rates of 30.6 FPS for Squeeze U-Net, 18.8 FPS for LRASPP, and 17.7 FPS for DeepLabV3. While the latter two models approach the lower bounds of real-time capability, only Squeeze U-Net consistently surpasses the standard 25–30 FPS threshold required for continuous video processing. This demonstrates that our chosen model not only minimizes latency and energy consumption but also enables genuine real-time operation onboard UAV hardware.

Energy consumption followed a similar trend. Squeeze U-Net consumed 66.54 µAh per image, substantially lower than LRASPP (109.04 µAh) and DeepLabV3 (113.56 µAh). The improvement in energy efficiency, reaching nearly 40% savings relative to the alter- native models, directly translates into longer UAV flight times and extended operational autonomy. These results demonstrate that energy-efficient model design is as important as computational speed when targeting embedded deployment on UAV hardware, where battery capacity is often the limiting factor.

Taken together, these findings confirm that Squeeze U-Net offers the best trade-off between accuracy, inference speed, and energy consumption among the tested models. Its performance ensures that the UAV system can operate reliably in real time without compro- mising flight endurance, thereby validating our design choice for deploying lightweight architectures tailored to the constraints of low-cost aerial platforms.

In addition to inference, the end-to-end pipeline also includes preprocessing (image loading, resizing, and normalization) and postprocessing (argmax classification and mask conversion). These stages are lightweight relative to the forward-pass inference, typically contributing no more than 1–2 ms each per frame. As a result, the overall latency is only marginally higher than the reported inference times, keeping the total per-frame processing within approximately 32–35 ms for Squeeze U-Net. This confirms that even when considering the complete pipeline, the system maintains real-time performance on UAV-compatible hardware.


> **Table 5. Comparison of model performance on the NVIDIA Jetson Nano.**

Model

Metric

Squeeze U-Net DeepLabV3 LRASPP

Avg time per image (s) 0.0327 0.0565 0.0532 Avg energy per image (µAh) 66.54 113.56 109.04 Avg FPS 30.58 17.70 18.80

Electronics 2025, 14, 4082 17 of 25


> **Figure 8. Average inference time per image for the three deep learning models (DeepLabV3, LRASPP,**

> Squeeze U-Net) on the NVIDIA Jetson Nano.


> **Figure 9. Average energy consumption per instance for the three deep learning models (DeepLabV3,**

> LRASPP, Squeeze U-Net) on the NVIDIA Jetson Nano.

4.2.3. Impact of Image Resolution

In semantic segmentation tasks like weed detection, a primary challenge is balancing the trade-off between input image resolution and computational efficiency. Processing at high resolutions enhances the model’s ability to capture fine-grained details, such as edges, which is crucial for precise segmentation. However, low-resolution processing can improve context awareness by allowing the network to observe larger portions of the image, effectively capturing broader structural patterns. In addition to the demand for precise segmentation, there is also the need to keep the computational demands manageable, especially in deep neural networks, where high-resolution inputs quickly lead to high memory and processing requirements. Downscaling the inputs is an efficient way to mitigate memory issues, but it may sacrifice detail.

In order to offer insight into how image resolution impacts segmentation perfor- mance and to highlight the effects of various image resolutions on different architec- tures, Table 6 presents the segmentation performance metrics (IoU, Accuracy, Recall, and F1-score) achieved by the Squeeze U-Net, LRSSP, and DeepLabV3 models across three image resolutions: 128 × 128, 256 × 256, and 512 × 512. To complement these nu- merical findings, Figure 10 illustrates the variation in IoU values across image resolutions for each model, highlighting the effect of input size on overall segmentation precision. Figure 11 presents the corresponding Accuracy trends, showing how correctly classified pixels increase with higher image resolution. Figure 12 depicts the changes in Recall,

Electronics 2025, 14, 4082 18 of 25

emphasizing each model’s sensitivity to object boundaries and ability to capture all rel- evant regions. Finally, Figure 13 summarizes the combined influence of precision and recall through the F1-score, offering an integrated view of segmentation balance across the three models and resolutions. These figures complement the numerical results in Table 6, providing a clearer comparative visualization of how each network responds to changes in input size. This comparison underscores each model’s ability to balance fine-detail sensitivity and contextual accuracy, revealing the strengths and limitations associated with each resolution and architecture combination.


> **Table 6. Performance metrics of deep learning models on the collected dataset at various image resolutions.**

Model Image Size IoU Accuracy Recall F1-Score

128 × 128 36.42 78.90 39.42 51.83

256 × 256 47.67 86.56 51.11 62.97

DeepLabV3 (Mobilenet V3)

512 × 512 56.87 91.08 65.18 71.05

128 × 128 46.25 86.29 50.60 61.49

256 × 256 54.88 90.55 61.92 69.06

LRASPP (MobileNet V3)

512 × 512 59.25 91.72 67.30 72.99

128 × 128 47.71 86.06 50.29 62.85

256 × 256 52.10 88.42 54.54 66.64

Squeeze U-Net

512 × 512 55.45 89.84 59.36 69.68

The results in Table 6 reveal how increasing image resolution enhances segmentation performance across DeepLabV3, LRASPP, and Squeeze U-Net models, as measured by IoU, Accuracy, Recall, and F1-score. At the lowest resolution (128 × 128), all models show limited segmentation performance, with DeepLabV3 achieving the lowest scores, likely due to its reliance on detailed spatial information. LRASPP and Squeeze U-Net perform better at this resolution, maintaining a balance between precision and recall, but still show constrained results. As resolution increases to 256 × 256, performance improves substantially for all models. DeepLabV3 benefits from the added detail, though it still falls behind LRASPP and Squeeze U-Net in F1-score and IoU. LRASPP shows the best performance, benefiting from its architecture’s strength in extracting spatial features. Squeeze U-Net also performs well, demonstrating consistent gains, though its improvements are slightly less pronounced than those of LRASPP. At the highest resolution (512 × 512), all models reach their peak performance. LRASPP outperforms the other models, effectively balancing detail and context. DeepLabV3 shows the most significant gains, finally achieving competitive results, while Squeeze U-Net continues to perform consistently well, though slightly less optimized for fine details than LRASPP. Overall, LRASPP is the most adaptable across resolutions, while DeepLabV3 benefits most from high-resolution images.

Additionally, training time increases as image resolution decreases; nevertheless, these times remain relatively short for these lightweight models (under two hours) and are therefore negligible for practical purposes. For example, the LRASPP model required only 30 epochs for the 512 × 512 input resolution but needed 56 epochs for 256 × 256 and 144 epochs for 128 × 128. The longer training time required at lower resolutions stems from the model’s need to compensate for the reduced detail in each image, making it harder to learn meaningful features quickly. With lower-resolution inputs, the model sees fewer fine-grained features, which can result in slower convergence as it requires more epochs to capture relevant patterns and achieve accurate segmentation. In contrast, higher resolutions provide more detailed spatial information, enabling the model to learn features

Electronics 2025, 14, 4082 19 of 25

more effectively and converge in fewer epochs. Consequently, while lower resolutions reduce the computational load per image, they extend overall training time as the model must work harder to distinguish features accurately across more training epochs. However, training time is a one-time cost typically handled on resource-rich platforms, so this extended training requirement at lower resolutions is not a major issue. Once trained, the model can be deployed for inference, where computational efficiency and real-time processing are more critical—especially on resource-constrained devices like UAVs.


> **Figure 10. Intersection over Union (IoU) at various image resolutions for the three deep learning**

> models (DeepLabV3, LRASPP, Squeeze U-Net).


> **Figure 11. Accuracy at various image resolutions for the three deep learning models (DeepLabV3,**

> LRASPP, Squeeze U-Net).

However, higher image resolutions demand significantly more computational resources, often exceeding real-time processing capabilities, especially on resource- constrained devices like UAVs.

Electronics 2025, 14, 4082 20 of 25


> **Figure 12. Recall at various image resolutions for the three deep learning models (DeepLabV3,**

> LRASPP, Squeeze U-Net).


> **Figure 13. F1-score at various image resolutions for the three deep learning models (DeepLabV3,**

> LRASPP, Squeeze U-Net).

The results in Tables 7–9 emphasize the practical trade-offs between segmentation accuracy, energy consumption, and inference speed at different image resolutions. As ex- pected, higher resolutions increase both energy cost and inference latency across all models, with DeepLabV3 being the most demanding in terms of resources. By contrast, lower resolutions (128 × 128 and 256 × 256) substantially reduce inference time and energy use, with Squeeze U-Net achieving the most favorable balance and maintaining the lowest energy footprint across resolutions. Importantly, the corresponding frame rates show that Squeeze U-Net consistently sustains throughput above 30 FPS, comfortably meeting real- time requirements for UAV deployment, whereas DeepLabV3 and LRASPP achieve only 17–24 FPS, which may suffice for slower operations but falls short of smooth real-time per- formance. These findings highlight that while higher resolutions can improve segmentation metrics, the associated increase in computational load and power draw makes them imprac- tical for embedded UAVs; instead, Squeeze U-Net at moderate resolutions offers the most effective compromise, combining strong segmentation accuracy with real-time throughput and energy efficiency, thereby making it the most suitable candidate for deployment on low-cost UAV platforms.

Electronics 2025, 14, 4082 21 of 25


> **Table 7. Average energy consumption (in µAh) for inference on a single image at different resolutions**

> for the three networks on the NVIDIA Jetson Nano.

Resolution Squeeze U-Net DeepLabV3 LRASPP

128 × 128 61.6 101.7 94.0 256 × 256 67.1 107.2 102.4 512 × 512 68.2 111.2 109.0


> **Table 8. Inference time per image (in ms) at different resolutions for the three networks on the**

> NVIDIA Jetson Nano.

Resolution Squeeze U-Net DeepLabV3 LRASPP

128 × 128 29.6 49.3 41.5 256 × 256 32.2 54.5 50.0 512 × 512 32.7 56.6 53.2


> **Table 9. Average inference throughput in frames per second (FPS) for different resolutions across the**

> three networks on the NVIDIA Jetson Nano.

Resolution Squeeze U-Net DeepLabV3 LRASPP

128 × 128 33.8 20.3 24.1 256 × 256 31.1 18.3 20.0 512 × 512 30.6 17.7 18.8


## 5. Discussion

This work demonstrates that accurate, real-time weed detection can be achieved on a low-cost UAV platform using commercially available components and an embedded GPU. By integrating the NVIDIA Jetson Nano with the lightweight Squeeze U-Net architecture, we show that reliable semantic segmentation is possible without compromising flight autonomy. The experimental results confirm that energy-efficient models may operate onboard in real time, overcoming one of the main barriers that has limited UAV-based deep learning in precision agriculture to high-end, expensive platforms.

A second major contribution of this work is the introduction of the AgriAdapt dataset, which contains 747 annotated aerial images of salad crops with weeds, collected under real field conditions during two flights over different locations in Rome, Italy. To our knowledge, this is the first publicly available dataset focused specifically on weed detection in salad crops from UAV imagery. Beyond serving as the basis for our own evaluation, this dataset provides the community with a valuable resource for benchmarking future deep learning models in agricultural contexts. The controlled acquisition protocol, diversity of lighting conditions, and systematic labeling make it well suited for reproducibility and comparative studies. The dataset is therefore not only instrumental to validating our pipeline but also constitutes an independent contribution to the broader field of precision agriculture.

The comparative analysis of DeepLabV3, LRASPP, and Squeeze U-Net underscores the trade-offs between segmentation performance, computational complexity, and energy consumption. While DeepLabV3 excelled in sensitivity at high resolutions, its computa- tional demands render it impractical for low-cost UAVs. LRASPP achieves high precision with efficient use of resources but risked missing smaller weed clusters. Squeeze U-Net offers a balanced solution, enabling near real-time inference with sufficient accuracy to make it viable for embedded deployment. These results suggest that careful selection of the segmentation architecture, matched to hardware constraints, is critical for practical field applications, although further testing in diverse crops and environments is needed. We also note that training times are influenced by image resolution, as discussed in Section 4.2.3.

Electronics 2025, 14, 4082 22 of 25

Lower-resolution inputs require more epochs to converge due to the reduced detail in each image, while higher-resolution inputs enable faster learning. Although this increases the total training duration, it is a one-time cost typically handled on resource-rich platforms and does not affect real-time inference performance on the UAV.

Nevertheless, some limitations must be acknowledged. The dataset, while novel and valuable, is currently restricted to salad crops and specific growth stages; broader validation across crop types and geographic contexts is necessary to ensure generalizability. Additionally, our system was evaluated for detection only, without closing the loop to automated actuation (e.g., targeted spraying or mechanical removal). Integrating detection with precise, real-time intervention is an essential next step for realizing the full potential of UAV-based weed management. Finally, while the Jetson Nano proved sufficient for this study, emerging embedded platforms with greater computational capacity may allow for the deployment of more advanced models or multimodal sensing strategies.

Compared with previous UAV-based weed detection systems, the proposed AgriAdapt platform demonstrates clear gains in energy efficiency, cost-effectiveness, and real-time performance. The lightweight Squeeze U-Net model running on the Jetson Nano (5–10 W) achieves real-time inference at 30.6 FPS with only 66.5 µAh per image—approximately 40% lower energy use and 70% faster throughput than larger models such as DeepLabV3 and LRASPP. In contrast, related systems employing high-end GPUs, such as the GTX1080Ti or RTX-class devices (typically 150–300 W), report frame rates of around 5–20 FPS depend- ing on input resolution and model size [30]. This confirms that the AgriAdapt system attains real-time capability at a fraction of the energy cost, even when accounting for res- olution differences. As detailed in Table 2, the total cost of the onboard computing and sensing payload is approximately EUR 600, while the complete UAV platform—including the airframe and propulsion components—remains under EUR 1500, substantially below commercial agricultural UAV solutions.

To extend the system for larger and more heterogeneous agricultural environments, several pathways are feasible. Multi-UAV coordination with autonomous waypoint as- signment can enable simultaneous coverage of wide farmland areas while maintaining low per-unit cost and energy use. For scalability across crop varieties, the existing pipeline can be retrained using transfer learning with additional datasets representing different canopy structures, colors, and spatial layouts, improving cross-crop generalization. Fur- thermore, incorporating adaptive exposure control and multimodal sensing (e.g., RGB–NIR or thermal fusion) would enhance robustness to variable illumination, soil reflectance, and weather conditions. Future iterations may integrate lightweight attention or dynamic pruning mechanisms that adjust model complexity according to scene difficulty, ensuring both energy efficiency and stable accuracy in diverse field conditions. These enhance- ments would allow AgriAdapt to operate effectively across large-scale farms, multiple crop species, and more severe environmental scenarios.

In summary, our findings emphasize two key advances: (i) the feasibility of real- time weed detection on a low-cost UAV system without compromising energy efficiency and (ii) the provision of the AgriAdapt dataset as a new, publicly available benchmark for agricultural computer vision. Together, these contributions may help lower the entry barrier to AI-powered precision agriculture and create opportunities for future innovation aimed at sustainable crop management, but additional validation is required to assess generalizability across other crops, growth stages, and geographic regions.


## 6. Conclusions

This work advances the state of precision agriculture by demonstrating that real- time, deep learning-based weed detection can be achieved on an accessible, low-cost UAV

Electronics 2025, 14, 4082 23 of 25

platform. Through the integration of the NVIDIA Jetson Nano and the energy-efficient Squeeze U-Net architecture, we show that accurate segmentation is possible within the strict energy and timing constraints of small UAVs, without compromising flight autonomy. This result directly addresses a key bottleneck in current UAV-based agricultural technologies, which have been largely confined to high-cost systems due to computational demands.

Equally important, we introduce the AgriAdapt dataset, a novel collection of 747 anno- tated aerial images of salad crops with weeds, acquired under real field conditions in Rome, Italy. This dataset represents a unique resource for the research community, providing a foundation for benchmarking, comparative evaluation, and future improvements in weed detection and agricultural computer vision. By making this dataset publicly available, we aim to accelerate the development of robust, generalizable models for precision agriculture.

Taken together, the system design and dataset contribution provide a pathway to- ward democratizing UAV-based monitoring solutions, lowering financial and technical barriers to adoption. The validation of our approach across multiple fields under varying environmental conditions demonstrates its robustness and applicability in real-world agri- cultural scenarios. This positions low-cost UAV systems not as experimental prototypes, but as practical tools that can enhance crop management and contribute to sustainable farming practices.

Future work will focus on extending the approach to additional crop types, growth stages, and geographic regions, as well as integrating detection with automated actuation mechanisms such as targeted spraying or robotic weeding. Further energy efficiency improvements could be achieved with flexible deep learning architectures, as evident from our recent investigation of the topic [39]. Ultimately, by bridging affordability, efficiency, and real-time capability, the research presented in this paper significantly contributes to widespread adoption of UAV technology in the pursuit of sustainable agriculture and global food security.

Author Contributions: Conceptualization, A.L.M., A.K., O.M.M., S.T.S. and D.L.; methodology, A.L.M., A.K., O.M.M., S.T.S. and D.L.; software, A.L.M., A.K., O.M.M. and S.T.S.; validation, A.L.M., A.K., O.M.M. and S.T.S.; formal analysis, A.L.M. and O.M.M.; investigation, A.L.M., A.K., O.M.M., S.T.S. and D.L.; resources, F.D.F. and V.P.; data curation, A.L.M. and A.K.; writing—original draft preparation, A.L.M., S.T.S. and O.M.M.; writing—review and editing, A.L.M., S.T.S., O.M.M., F.D.F. and V.P.; visualization, A.L.M. and A.K.; supervision, O.M.M., F.D.F. and V.P.; project administration, O.M.M., F.D.F. and V.P.; funding acquisition, O.M.M., D.L., F.D.F. and V.P. All authors have read and agreed to the published version of the manuscript.

Funding: The research presented in this paper was funded by the Slovenian Research Agency project “Context-Aware On-Device Approximate Computing” (J2-3047), research core funding No. P2-0098

and P2-0426, and by the H2020 Smart4All 3rd FTTE grant “AgriAdapt”.

Institutional Review Board Statement: Not applicable.

Informed Consent Statement: Not applicable.

Data Availability Statement: The original data presented in the study are openly available in https://gitlab.fri.uni-lj.si/lrk/agriadapt-electronics (accessed on 13 October 2025) and https://app. roboflow.com/agriadaptweeddetection/agriadapt-uex2n/overview (accessed on 25 September 2025).

Conflicts of Interest: Author Daniele Latini was employed by the company GEO-K s.r.l., Rome, Italy. The remaining authors declare that the research was conducted in the absence of any commercial or financial relationships that could be construed as a potential conflict of interest.


## References

1. Dorling, D. World population prospects at the UN: Our numbers are not our problem? In The Struggle for Social Sustainability; Policy Press: Bristol, UK, 2021; pp. 129–154.

Electronics 2025, 14, 4082 24 of 25

2. Navarro, E.; Costa, N.; Pereira, A. A systematic review of IoT solutions for smart farming. Sensors 2020, 20, 4231. [CrossRef] [PubMed] 3. Mustafa, A.; Naveed, M.; Saeed, Q.; Ashraf, M.N.; Hussain, A.; Abbas, T.; Kamran, M.; Minggang, X. Application potentials of plant growth promoting rhizobacteria and fungi as an alternative to conventional weed control methods. In Sustainable Crop Production; IntechOpen: London, UK, 2019. [CrossRef] 4. Ba´cmaga, M.; Wyszkowska, J.; Kucharski, J. Environmental Implication of Herbicide Use. Molecules 2024, 29, 5965. [CrossRef] [PubMed] 5. Koller, V.J.; Fürhacker, M.; Nersesyan, A.; Mišík, M.; Eisenbauer, M.; Knasmueller, S. Cytotoxic and DNA-damaging properties of glyphosate and Roundup in human-derived buccal epithelial cells. Arch. Toxicol. 2012, 86, 805–813. [CrossRef] 6. Bourguet, D.; Guillemaud, T. The hidden and external costs of pesticide use. Sustain. Agric. Rev. 2016, 19, 35–120. 7. Fawakherji, M.; Potena, C.; Pretto, A.; Bloisi, D.D.; Nardi, D. Multi-spectral image synthesis for crop/weed segmentation in precision farming. Robot. Auton. Syst. 2021, 146, 103861. [CrossRef] 8. Anand, T.; Sinha, S.; Mandal, M.; Chamola, V.; Yu, F.R. AgriSegNet: Deep Aerial Semantic Segmentation Framework for IoT-Assisted Precision Agriculture. IEEE Sens. J. 2021, 21, 17581–17590. [CrossRef] 9. Tian, Y.; Ye, Q.; Doermann, D. Yolov12: Attention-centric real-time object detectors. arXiv 2025, arXiv:2502.12524. 10. Lateef, F.; Ruichek, Y. Survey on semantic segmentation using deep learning techniques. Neurocomputing 2019, 338, 321–348. [CrossRef] 11. de Oca, A.M.; Flores, G. The AgriQ: A low-cost unmanned aerial system for precision agriculture. Expert Syst. Appl. 2021, 182, 115163. [CrossRef] 12. Czymmek, V.; Schramm, R.; Hussmann, S. Vision based crop row detection for low cost uav imagery in organic agriculture. In Proceedings of the 2020 IEEE International Instrumentation and Measurement Technology Conference (I2MTC), Dubrovnik, Croatia, 25–28 May 2020. 13. Cucho-Padin, G.; Loayza, H.; Palacios, S.; Balcazar, M.; Carbajal, M.; Quiroz, R. Development of low-cost remote sensing tools and methods for supporting smallholder agriculture. Appl. Geomat. 2020, 12, 247–263. [CrossRef] 14. Almalki, F.A.; Soufiene, B.O.; Alsamhi, S.H.; Sakli, H. A low-cost platform for environmental smart farming monitoring system based on IoT and UAVs. Sustainability 2021, 13, 5908. [CrossRef] 15. Karatzinis, G.D.; Apostolidis, S.D.; Kapoutsis, A.C.; Panagiotopoulou, L.; Boutalis, Y.S.; Kosmatopoulos, E.B. Towards an integrated low-cost agricultural monitoring system with unmanned aircraft system. In Proceedings of the 2020 International Conference on Unmanned Aircraft Systems (ICUAS), Athens, Greece, 9–12 June 2020; pp. 1131–1138. [CrossRef] 16. Vacca, G. Estimating tree height using low-cost UAV. Int. Arch. Photogramm. Remote Sens. Spat. Inf. Sci. 2023, 48, 381–386. [CrossRef] 17. Rangarajan, A.K.; Balu, E.J.; Boligala, M.S.; Jagannath, A.; Ranganathan, B.N. A low-cost UAV for detection of Cercospora leaf spot in okra using deep convolutional neural network. Multimed. Tools Appl. 2022, 81, 21565–21589. [CrossRef] 18. Jang, G.; Kim, J.; Yu, J.K.; Kim, H.J.; Kim, Y.; Kim, D.W.; Kim, K.H.; Lee, C.W.; Chung, Y.S. Cost-effective unmanned aerial vehicle (UAV) platform for field plant breeding application. Remote Sens. 2020, 12, 998. [CrossRef] 19. Cucchiaro, S.; Straffelini, E.; Chang, K.J.; Tarolli, P. Mapping vegetation-induced obstruction in agricultural ditches: A low-cost and flexible approach by UAV-SfM. Agric. Water Manag. 2021, 256, 107083. [CrossRef] 20. Jiménez-Jiménez, S.I.; Ojeda-Bustamante, W.; Marcial-Pablo, M.d.J.; Enciso, J. Digital terrain models generated with low-cost UAV photogrammetry: Methodology and accuracy. ISPRS Int. J. Geo-Inf. 2021, 10, 285. [CrossRef] 21. Machidon, O.M.; Krašovec, A.; Machidon, A.L.; Pejovi´c, V.; Latini, D.; Sasidharan, S.T.; Del Frate, F. AgriAdapt: Towards Resource-Efficient UAV Weed Detection using Adaptable Deep Learning. In Proceedings of the 2nd Workshop on Networked Sensing Systems for a Sustainable Society, Madrid, Spain, 6 October 2023; pp. 193–200. 22. Sa, I.; Popovi´c, M.; Khanna, R.; Chen, Z.; Lottes, P.; Liebisch, F.; Nieto, J.; Stachniss, C.; Walter, A.; Siegwart, R. WeedMap: A large-scale semantic weed mapping framework using aerial multispectral imaging and deep neural network for precision farming. Remote Sens. 2018, 10, 1423. [CrossRef] 23. Krestenitis, M.; Raptis, E.K.; Kapoutsis, A.C.; Ioannidis, K.; Kosmatopoulos, E.B.; Vrochidis, S.; Kompatsiaris, I. CoFly-WeedDB: A UAV image dataset for weed detection and species identification. Data Brief 2022, 45, 108575. [CrossRef] 24. Celikkan, E.; Kunzmann, T.; Yeskaliyev, Y.; Itzerott, S.; Klein, N.; Herold, M. WeedsGalore: A multispectral and multitemporal UAV-based dataset for crop and weed segmentation in agricultural maize fields. In Proceedings of the 2025 IEEE/CVF Winter Conference on Applications of Computer Vision (WACV), Tucson, AZ, USA, 26 February–6 March 2025; pp. 4767–4777. 25. dos Santos Ferreira, A.; Freitas, D.M.; Da Silva, G.G.; Pistori, H.; Folhes, M.T. Weed detection in soybean crops using ConvNets. Comput. Electron. Agric. 2017, 143, 314–324. [CrossRef] 26. Moazzam, S.I.; Khan, U.S.; Nawaz, T.; Qureshi, W.S. Crop and weeds classification in aerial imagery of sesame crop fields using a patch-based deep learning model-ensembling method. In Proceedings of the 2022 2nd International Conference on Digital Futures and Transformative Technologies (ICoDT2), Rawalpindi, Pakistan, 24–26 May 2022; pp. 1–7. [CrossRef]

Electronics 2025, 14, 4082 25 of 25

27. Moazzam, S.I.; Khan, U.S.; Qureshi, W.S.; Nawaz, T.; Kunwar, F. Towards automated weed detection through two-stage semantic segmentation of tobacco and weed pixels in aerial Imagery. Smart Agric. Technol. 2023, 4, 100142. [CrossRef] 28. Genze, N.; Wirth, M.; Schreiner, C.; Ajekwe, R.; Grieb, M.; Grimm, D.G. Improved weed segmentation in UAV imagery of sorghum fields with a combined deblurring segmentation model. Plant Methods 2023, 19, 87. [CrossRef] [PubMed] 29. Bosilj, P.; Aptoula, E.; Duckett, T.; Cielniak, G. Transfer learning between crop types for semantic segmentation of crops versus weeds in precision agriculture. J. Field Robot. 2020, 37, 7–19. [CrossRef] 30. Milioto, A.; Lottes, P.; Stachniss, C. Real-time semantic segmentation of crop and weed for precision agriculture robots leveraging background knowledge in CNNs. In Proceedings of the 2018 IEEE international conference on robotics and automation (ICRA), Brisbane, Australia, 21–25 May 2018; pp. 2229–2235. [CrossRef] 31. Fu, H.; Li, X.; Zhu, L.; Xin, P.; Wu, T.; Li, W.; Feng, Y. DSC-DeepLabv3+: A lightweight semantic segmentation model for weed identification in maize fields. Front. Plant Sci. 2025, 16, 1647736. [CrossRef] 32. Roboflow Inc. Roboflow: Annotate, Train, Deploy Computer Vision Models. 2023. Available online: https://roboflow.com (accessed on 5 October 2025). 33. Chen, L.C.; Papandreou, G.; Schroff, F.; Adam, H. Rethinking Atrous Convolution for Semantic Image Segmentation. arXiv 2017, arXiv:1706.05587. [CrossRef] 34. Howard, A.; Sandler, M.; Chu, G.; Chen, L.C.; Chen, B.; Tan, M.; Wang, W.; Zhu, Y.; Pang, R.; Vasudevan, V.; et al. Searching for mobilenetv3. In Proceedings of the IEEE/CVF International Conference on Computer Vision, Seoul, Republic of Korea, 27 October–2 November 2019; pp. 1314–1324. [CrossRef] 35. Beheshti, N.; Johnsson, L. Squeeze U-Net: A Memory and Energy Efficient Image Segmentation Network. In Proceedings of the 2020 IEEE/CVF Conference on Computer Vision and Pattern Recognition Workshops (CVPRW), Seattle, WA, USA, 14–19 June 2020; pp. 1495–1504. [CrossRef] 36. Yao, Y.; Rosasco, L.; Caponnetto, A. On early stopping in gradient descent learning. Constr. Approx. 2007, 26, 289–315. [CrossRef] 37. Goodfellow, I.; Bengio, Y.; Courville, A. Deep Learning; MIT Press: Cambridge, MA, USA, 2016. Available online: http: //www.deeplearningbook.org (accessed on 10 September 2025). 38. Buda, M.; Maki, A.; Mazurowski, M.A. A systematic study of the class imbalance problem in convolutional neural networks. Neural Netw. 2018, 106, 249–259. [CrossRef] [PubMed] 39. Machidon, A.L.; Krašovec, A.; Pejovi´c, V.; Machidon, O.M. SqueezeSlimU-Net: An Adaptive and Efficient Segmentation Architecture for Real-Time UAV Weed Detection. IEEE J. Sel. Top. Appl. Earth Obs. Remote Sens. 2025, 18, 5749–5764. [CrossRef]

Disclaimer/Publisher’s Note: The statements, opinions and data contained in all publications are solely those of the individual author(s) and contributor(s) and not of MDPI and/or the editor(s). MDPI and/or the editor(s) disclaim responsibility for any injury to people or property resulting from any ideas, methods, instructions or products referred to in the content.
