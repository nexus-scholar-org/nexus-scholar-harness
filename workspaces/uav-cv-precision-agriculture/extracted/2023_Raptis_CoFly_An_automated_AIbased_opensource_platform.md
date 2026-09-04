---
workspace_id: SCI-000639
doi: 10.1016/j.softx.2023.101414
title: 'CoFly: An automated, AI-based open-source platform for UAV precision agriculture
  applications'
authors:
- family_name: Raptis
  given_name: Emmanuel K.
  orcid: https://orcid.org/0000-0003-0033-7925
- family_name: Englezos
  given_name: Konstantinos
  orcid: https://orcid.org/0000-0002-9495-116X
- family_name: Kypris
  given_name: Orfeas
  orcid: https://orcid.org/0000-0001-7858-3259
- family_name: Krestenitis
  given_name: Marios
  orcid: https://orcid.org/0000-0002-7845-7719
- family_name: Kapoutsis
  given_name: Athanasios Ch.
  orcid: https://orcid.org/0000-0002-1688-036X
- family_name: Ioannidis
  given_name: Konstantinos
  orcid: https://orcid.org/0000-0001-6767-8762
- family_name: Vrochidis
  given_name: Stefanos
  orcid: https://orcid.org/0000-0002-2505-9178
- family_name: Kosmatopoulos
  given_name: Elias B.
  orcid: https://orcid.org/0000-0002-3735-4238
year: 2023
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:21:25.700816+00:00'
---

# CoFly: An automated, AI-based open-source platform for UAV precision agriculture applications

SoftwareX 23 (2023) 101414

Contents lists available at ScienceDirect

SoftwareX

journal homepage: www.elsevier.com/locate/softx

Original software publication

CoFly: An automated, AI-based open-source platform for UAV precision agriculture applications

Emmanuel K. Raptis a,c, Konstantinos Englezos b,∗, Orfeas Kypris b, Marios Krestenitis c, Athanasios Ch. Kapoutsis c, Konstantinos Ioannidis c, Stefanos Vrochidis c, Elias B. Kosmatopoulos a,c

a Department of Electrical and Computer Engineering, Democritus University of Thrace, Xanthi, 67100, Greece b iKnowHow SA, Athens, 11526, Greece c Information Technologies Institute, The Centre for Research & Technology, Hellas, Thessaloniki, 57001, Greece

a r t i c l e i n f o

a b s t r a c t

This paper presents a modular and holistic Precision Agriculture platform, named CoFly, incorpo- rating custom-developed AI and ICT technologies with pioneering functionalities in a UAV-agnostic system. Cognitional operations of micro Flying vehicles are utilized for data acquisition incorporating advanced coverage path planning and obstacle avoidance functionalities. Photogrammetric outcomes are extracted by processing UAV data into 2D fields and crop health maps, enabling the extraction of high-level semantic information about seed yields and quality. Based on vegetation health, CoFly incorporates a pixel-wise processing pipeline to detect and classify crop health deterioration sources. On top of that, a novel UAV mission planning scheme is employed to enable site-specific treatment by providing an automated solution for a targeted, on-the-spot, inspection. Upon the acquired inspection footage, a weed detection module is deployed, utilizing deep-learning methods, enabling weed classification. All of these capabilities are integrated inside a cost-effective and user-friendly end-to-end platform functioning on mobile devices. CoFly was tested and validated with extensive experimentation in agricultural fields with lucerne and wheat crops in Chalkidiki, Greece showcasing its performance.

Article history: Received 13 January 2023 Received in revised form 16 May 2023 Accepted 16 May 2023

Keywords: UAVs Precision agriculture Power efficient solutions Remote sensing applications

© 2023 The Author(s). Published by Elsevier B.V. This is an open access article under the CC BY license

(http://creativecommons.org/licenses/by/4.0/).

Code metadata

Current code version V1.0.0 Permanent link to code/repository used for this code version https://github.com/ElsevierSoftwareX/SOFTX-D-23-00036 Code Ocean compute capsule – Legal Code License MIT Code versioning system used git Software code languages, tools, and services used JS, Python, Electron, Node Compilation requirements, operating environments & dependencies >= Node JS v8.0, Python 3.6, pandas = 1.2.1, numpy = 1.20.3, matplotlib = 3.4.2 If available Link to developer documentation/manual https://github.com/CoFly-Project/cofly-gui#readme Support email for questions keglezos@iknowhow.com

∗Corresponding author.

E-mail addresses: eraptis@ee.duth.gr, emmarapt@iti.gr (Emmanuel K. Raptis), keglezos@iknowhow.com (Konstantinos Englezos), kypriso@gmail.com (Orfeas Kypris), mikrestenitis@iti.gr (Marios Krestenitis), athakapo@iti.gr (Athanasios Ch. Kapoutsis), kioannid@iti.gr (Konstantinos Ioannidis), stefanos@iti.gr (Stefanos Vrochidis), kosmatop@ee.duth.gr, kosmatop@iti.gr (Elias B. Kosmatopoulos).

https://doi.org/10.1016/j.softx.2023.101414 2352-7110/© 2023 The Author(s). Published by Elsevier B.V. This is an open access article under the CC BY license (http://creativecommons.org/licenses/by/4.0/).

Emmanuel K. Raptis, Konstantinos Englezos, Orfeas Kypris et al. SoftwareX 23 (2023) 101414


## 1. Motivation and significance


> **Table 1**

> A competitiveness matrix that compares commercially available products,
including CoFly, based on their farming technological features.

Agriculture constitutes a vital component of the economy in many less industrialized countries, leveraging natural resources to yield both income and export revenue. Improving productiv- ity in agriculture not only benefits the economy of individual countries but also contributes to global food production, as food insecurity and poor quality can have negative impacts on public health.

Software Path planning

Vegetation indices

Timeline Weed detection

Pix4D [1] ✓ ✓ ✓ ✗ Drone Deploy [2] ✓ ✓ ✓ ✗ Sentera FieldAgent [3] ✓ ✓ ✓ ✗ Agisoft [4] ✗ ✓ ✗ ✗ Botlink [5] ✓ ✓ ✗ ✗ Blue River Technology [6] ✗ ✗ ✗ ✓

Unmanned aerial vehicles (UAVs) equipped with artificial intelligence and visual analysis capabilities offer a promising solution to the aforementioned challenges faced in agriculture, particularly in the realm of precision agriculture (PA). To this end, commercial closed-source software and research agricul- tural products have been developed, leveraging digital farming technologies for precision agriculture and farming development. Commercial products, including Pix4D [1], DroneDeploy [2], and Sentera FieldAgent [3], which are drone mapping software that can create UAV flight paths, capture aerial photographs, visual- ize crop health indices, and provide a timeline view of previ- ous field scans for continuous monitoring. Additionally, Agisoft Metashape [4] employs photogrammetry to create 3D maps in- cluding crop yield and plant health maps. Botlink [5] is a UAV- based agricultural software with a flight planning framework that can produce high-definition 2D and 3D outputs and vegetation indices. Lastly, Blue River Technology [6] provides smart farm machines that use computer vision and deep learning techniques to individually monitor each plant in the field, a capability that is currently lacking in integrated UAV products. Table 1 compares these various commercial agricultural products based on their farming technological features.

CoFly ✓ ✓ ✓ ✓

information on seed yields, quality, and health. At the same time, the platform is capable of identifying problematic locations, identifying crop health deterioration sources, and providing tar- geted, on-the-spot inspections. Finally, a weed detection module is also integrated, providing detailed weed classification. These steps are adequate for everyday agriculture needs that require surveillance of a new crop, analysis of photometric indices, and detection of intrusive plant species with minimal hardware re- quirements to ensure cost-effectiveness. CoFly as a UAV-agnostic PA software, allows the integration of various robot-related and software-dependent systems, as well as multiple UAVs utilizing open-source or SDK-ready firmware. At the same time, we pro- vide the research community with a tool that enables them to create and evaluate customized solutions for several agricultural applications. The technical specifications of the developed field management system are outlined in Section 2.


## 2. Software description

Several research studies have also developed systems-level software for various agricultural practices, primarily focused on crop health and yield monitoring. According to a recent review paper [7], these systems mostly utilize commercial usage-based pricing models (Table 1) for their flight planning and photogram- metric services, thereby hindering their customization for agri- cultural applications, as it requires a certain level of expertise for consolidation and overall management. Additionally, most of them aim to improve specific workflows such as estimating plant volume [8], monitoring vegetation canopy reflectance [9] and evaluating chlorophyll levels in rice paddies [10]. Other prac- tices include periodic crop status inspections, pH level, and acid- ity calculations, as well as vineyard monitoring and mapping [11–13]. Regarding motion planning, while numerous options are available for flight control and mission planning using open- source UAV flight controllers and simulators [14,15] none of them extend their capabilities beyond flight control to include data post-processing, and they do not cater to the unique characteris- tics of each field, such as no-fly zones and automatic UAV-based weed detection.

CoFly-GUI is a hybrid user interface application that has been designed to facilitate easy installation on any computer system, regardless of the operating system. It employs HTTP [16] and MQTT [17] communication protocols for communication with the UAV and its sub-modules. The software features a user-friendly interface that enables users to effortlessly manage and modify settings through the use of graphical representations and in- structions that enable them to operate the individual subsystems within the software without the need for specialized knowledge. The user interface has been implemented in JavaScript using the Node JS software development platform and the Electron frame- work [18]. The design of the software places a strong emphasis on ease of use and user-friendliness.

2.1. Software architecture

As sketched in Fig. 1, the proposed precision agriculture plat- form consists of three main components: a graphical user inter- face, four robotic-related software capabilities, and a bidirectional communication system that enables message interactions and real-time communication between the proposed software and the UAV. As to the graphical interface, the first part concerns the class that creates, visualizes, and manages a world map pro- viding detailed information about geographical regions and sites worldwide (main_map.js). This service has been implemented using the Leaflet library [19], OpenStreet Maps [20], and one extra open-source add-on (draw tool [21]) to generate polygons and markers while simplifying the handling of imported/exported polygons, ultimately resulting in a user-friendly data visualization experience. The second class that surrounds the UI is the class that manages, saves, creates, and deletes the files required for the smooth operation of the software (main_file_manager.js). This file database management class has been developed to facilitate the recording of information and data of each drone

Owing to the lack of some advanced features, in this article, a novel UAV-based, low-cost, and user-friendly precision agri- culture platform, named CoFly, has been developed providing an open-source alternative while integrating pioneering function- alities with custom-developed robot-related services in a UAV- agnostic system. The CoFly-GUI platform is a field management tool for UAVs that generates tailored field monitoring paths to as- sist decision-making objectives and ensure optimal management of crop growth. The primary objective is to simplify the process of scanning, imaging, and parametric analysis of crops using UAVs, making it accessible even to non-experienced in UAV flight end-users without the need for complex manipulations such as autonomous control, precision flight control, obstacle avoidance, etc. The user interface (UI) was designed with the user workflow in mind, aiming to provide the operator or farmer with a cost- effective and end-to-end integrated system that provides valuable

2

Emmanuel K. Raptis, Konstantinos Englezos, Orfeas Kypris et al. SoftwareX 23 (2023) 101414

Fig. 1. Workflow of CoFly-GUI & Sub-modules.

mapping project so as to enable auto-save and local history command actions (Timeline). For example, when a user creates a new project with specific parameters (e.g., polygon, UAV mission details e.t.c), the system automatically creates folders and log files so that it can be reloaded in the future either in the same or in another system while keeping a history of the specific drone mapping project. All the parameters created and used by the system can be found in three settings files with the following names: field_settings.json (contains useful informa- tion such as geographic polygon describing the area of interest, drone’s initial position, coverage path, UAV mission parameters, etc.), map_data.geojson (contains the name of the field entered by the user and all the information of the geographic poly- gon of the field), disabled_paths.json (contains geographic poly- gons related to the obstacles defined by the user). Finally, the third and most important class of the CoFly software is the load-communication field (load-project.js) which creates a com- munication node (HTTP API) to facilitate the management and communication of the UI environment with the different sub- modules. The communication of data among different modules is implemented by a Restful API Service [22] which allows the different sub-systems to connect and interact with each other by retrieving the necessary data for their execution. The main communication channel between the sub-modules is reached through the address localhost:8081 and the data transmission is done via .json files with single post requests.

generated by both the UI and UAV, CoFly creates drone topics and connects to them (by listening and subscribing). Specifically, these topics ensure commands to the UAV (start/abort/stop mis- sion), the indication of the exact position of the drone marker on the world map, and its current mission status. Besides, through these topics, the UAV transfers in real-time the collected data to the software. In particular, the open-source library piexif [24] has been used for image handling, which converts the image from base64 encoding to .jpg and assigns to it metadata that will be needed afterward to extract the orthomosaic photo of the field. To display the orthomosaic photo on the world map we also used the piexif library that allows us to convert the exported ODM’s [25] .tiff image to .jpg with channel A enabled for transparency.

To ease both the installation of the overall CoFly software and the utilization of the robotic-related and computer vision services, each and every sub-module has been packed into an executable python file (.exe) with the usage of the PyInstaller [26] library without the need of any prerequisite and dependency. The overall framework of the CoFly-GUI program is developed using HTML, CSS, and JS web technologies.

2.2. Software functionalities

Once CoFly-GUI is installed and running, the end user is pre- sented with a set of options including Load project (view an existing project), Create project (create a new project), or Import project (import an existing project). Let us assume that the user selects the second option Create project. The first step is to input basic mission attributes, known as Coverage Mission Details, such as the area polygon to be surveyed, flight altitude, and scanning speed.

Additionally, load-project.js is also responsible for message interactions and real-time communication with the UAV. This bidirectional communication is done by the MQTT communica- tion protocol over the port 9090 and the Eclipse Mosquito MQTT Server [23] running on docker images. To handle all messages

3

Emmanuel K. Raptis, Konstantinos Englezos, Orfeas Kypris et al. SoftwareX 23 (2023) 101414

ability to interfere with the identified problematic locations via the user interface by differentiating them and adding or removing specific points to formulate a custom site-specific mission that caters to their requirements.

Following the acquisition of aerial imagery, the captured visual data are forwarded to the Weed detection service for further pro- cessing and analysis. In specific, existing weeds among the crop are automatically detected and highlighted for the end-user. The deployed module is employing the robustness of DeepLabv3+ [37], a well-known deep-learning architecture for semantic segmenta- tion, trained and evaluated in previously collected crop data [38]. Towards this direction, the visual input is processed via the deep-learning model, and the depicted weed instances are an- notated at pixel-level. As illustrated in Fig. 5, Weed detection service outputs the visualization of weed species to the UI, su- perimposed on the geo-referenced map, while the pixel-level annotation (pink) provides accurate spatial information regarding the detected weeds.

Fig. 2. Creation, parameterization and calculation of the coverage path.

Once the necessary attributes are defined, the user can select the ‘‘calculate path’’ button to initiate the Path Planning util- ity for the designated polygon, as shown in Fig. 2. To cover a continuous field, the well-known Spanning-Tree Coverage [27] algorithm is utilized, which is proficient in handling Coverage Path Planning (CPP) [28] operations, determining a collision-free trajectory that mitigates the limitations of UAVs, and ensuring the most energy-efficient path to comprehensively survey the given area. Once the computation is completed, the flight path is returned to the UI and superimposed on the map. As long as the users are satisfied with the computed flight path, they can proceed with initiating the mission by selecting the ‘‘Start Scanning’’ button. This action initiates the UAV adaptor topic and establishes a direct communication channel with the drone via an HTTP service, enabling the transmission of images captured by the drone without any intermediary processes. Concurrently, the drone’s real-time location on the global map is displayed to apprise the user of its precise position over the field and facilitate its supervision in real-time (Fig. 2).

The entirety of this data, retrievable via the Load or Import feature, is automatically archived in a timeline encompassing the entire crop growth cycle from the fallow period and land preparation, to crop establishment and maintenance, to harvest and storage. More details about the specifics of the developed methodologies can be found here [39]. A video demonstration illustrating the sequence of events among all the aforementioned services is attached to the following link.1


## 3. Illustrative examples

In this section, an experimental evaluation of the proposed software is carried out focusing on the evaluation of vegeta- tion health estimation in a real-life demonstration scenario. The experiment is intended to assess and validate the operational pro- ficiency of the developed software, encompassing both path plan- ning and remote sensing capabilities, leveraging the utilization of the custom-developed robot-related software solutions.

After the coverage mission is completed, the user can proceed with launching the Vegetation Indices services. By selecting the ‘‘Photo Indices" button, the UI forwards the UAV captured images to the corresponding services and obtains the geo-referenced stitched image along with the calculated vegetation index im- ages, as illustrated in Fig. 3. Specifically, an accurate orthomosaic map is acquired by deploying the robust OpenDroneMap (ODM) toolkit [25,29] for the stitching process, while the vegetation in- dex images correspond to 4 efficient indices, that are widely em- ployed in precision agriculture [30,31], namely Green Leaf Index (GLI) [32], Normalized Green–Blue Difference Index (NGBDI) [33], Normalized Green–Red Difference Index (NGRDI) [34], Visual At- mospheric Resistance Index (VARI) [35]. Each one of the employed indices utilizes different characteristics of the vegetation’s light reflectance and thus, it quantifies different aspects of crop health. This can be clearly conceived in Fig. 3 where vegetation indices present spatial variations in terms of crop health, while the com- bination of all of them can provide a concrete overview of the vegetation’s health status. Leveraging the acquired knowledge of vegetation, the system will automatically engage the Problematic Areas detection service to detect areas within the agricultural field that may pose difficulties, as demonstrated in Fig. 4.

3.1. Evaluation and results

For the experimentation study, a DJI Phantom 4 Pro equipped with an RGB camera was used for image acquisition. The UAV flight planning for monitoring an agricultural field was done by the developed software. The experiments were carried out in a rural region of Chalkidiki, Greece, featuring fertile soil cul- tivated with lucerne and wheat crops. To further demonstrate the efficiency of the developed software, we present a set of results acquired from different vegetation fields. In specific, Fig. 6 illustrates the orthomosaic of a lucerne (medicago sativa) cul- tivation with the corresponding VARI index, acquired via the developed tool. The estimated VI map is displayed to the operator by utilizing a red–green color map where regions with low VI values indicating poor vegetation health are displayed in red, and those with high VI values indicating good vegetation health are represented in green. The detected problematic areas are also annotated with blue dots, indicating the center of each area. Results imply that the deployed framework can be exploited to derive a detailed overview of the examined field, accompanied by high-level information regarding crop health and its spatial variation.

Towards assessing the extracted problematic locations, by se- lecting the ‘‘Calculate Path Problematic Areas" button, a UAV- based inspection mission is designed. The process of determining a path for visiting a finite set of points is a motion planning prob- lem, where the objective is to identify the most efficient route that results in the minimum realization cost. For the visual on-site inspection, the Traveling Salesman algorithm [36], a renowned method for finding the shortest path within an undirected graph, is applied. It should be noted that the end-user possesses the

Similarly, in Fig. 7, the corresponding results for an examined wheat crop are presented. The developed application provides a high-resolution map of the field through the extracted orthomo- saic. Additionally, via the deployed analysis tools (demonstrated for the NGBDI index), valuable information regarding the crop health and the local problematic areas is acquired.


## 1 https://www.youtube.com/watch?v=C0hdCu-ZRQk&ab_channel=

CoFlyProject

4

Emmanuel K. Raptis, Konstantinos Englezos, Orfeas Kypris et al. SoftwareX 23 (2023) 101414

Fig. 3. Visual representations of the geo-referenced orthomosaic and VI maps.


## 4. Impact

All in all, CoFly is an open-source and cost-effective agricul- tural software, that enables farmers easily acquire, analyze, and continuously monitor their fields. By combining cognitional oper- ations of micro flying vehicles, the system can optimize solutions and mitigate the negative impact of the UAV’s limited battery life, improving operational time and energy efficiency, serving, thus, as a tool for monitoring and site-specific precision farming. As demonstrated in the illustrative examples, CoFly retains all the essential characteristics of a typical commercial agricultural software, making it a valuable and highly accurate tool for the farming community to obtain contemporary field management skills. CoFly is designed aiming to maximize the usage of PA by non-experienced UAV flight end-users while, at the same time, offering the research community a tool, through a public re- lease on Github [40], for developing and testing custom solutions for several agricultural applications. An extensive demonstration of the proposed software’s practical utility in several real-life experiments can be found at [39].

Fig. 4. Problematic areas detection.


## 5. Conclusions

In this paper, an open-source pre- and post-processing frame- work for precision agriculture named CoFly is developed. The proposed system takes into account the sensing and operational capabilities of the UAVs while avoiding any no-fly zones or ob- stacles within the operational area. It processes aerial data to generate detailed field and crop health maps using vegetation indices, which provide information on seed yields and quality. The framework also includes a pixel-wise processing pipeline to detect and classify sources of crop health deterioration and a novel UAV mission planning scheme for targeted, on-the-spot inspection of potential problem areas. A weed detection module using deep learning methods is also included to classify weeds

Fig. 5. Weed detection module exports upon GLI & NGBDI vegetation indices.

Showcasing its performance, the current version of CoFly can proficiently manage the pre-and post-processing stages of a typ- ically precision agriculture software, presenting all the outcomes generated by the sub-plugins.

5

Emmanuel K. Raptis, Konstantinos Englezos, Orfeas Kypris et al. SoftwareX 23 (2023) 101414

Fig. 6. Visual outcome of the developed framework for a field of lucerne.

Fig. 7. Visual outcome of the developed framework for a wheat crop.


## References

based on inspection footage. All of these features are integrated into an end-to-end platform that can be used on mobile devices and is designed to make it easy for UAVs to be used in precision agriculture applications, enabling them to be effective tools for site-specific precision farming.

[1] Pix4D. Professional photogrammetry and drone mapping software. 2020,

https://www.pix4d.com/, [Online; accessed 22 October- 2020]. [2] Deploy D. Drone mapping software. 2020, https://www.dronedeploy.com/,

[Online; accessed 22 October- 2022]. [3] Sentera FieldAgent Analytics. Agriculture mapping software. 2020, https:

Code & Data Availability

//sentera.com/, [Online; accessed 22 October- 2022]. [4] Agisoft. Agisoft Metashape. 2020, https://www.agisoft.com, [Online; accessed 22 October- 2022]. [5] Botlink. Automated drone flight software. 2020, https://botlink.com/, [Online; accessed 22 October- 2022]. [6] Blue River Technology. Blue river technology. 2020, http://www. bluerivertechnology.com/, [Online; accessed 22 October- 2022]. [7] Radoglou-Grammatikis P, Sarigiannidis P, Lagkas T, Moscholios I. A compilation of UAV applications for precision agriculture. Comput Netw 2020;172(January):107148. http://dx.doi.org/10.1016/j.comnet.2020. 107148. [8] Christiansen MP, Laursen MS, Jørgensen RN, Skovsen S, Gislum R. Designing

The overall CoFly ecosystem is open-source and publicly avail- able at https://github.com/CoFly-Project to the community.

Declaration of competing interest

The authors declare that they have no known competing finan- cial interests or personal relationships that could have appeared to influence the work reported in this paper.

Data availability

and testing a UAV mapping system for agricultural field surveying. Sensors 2017;17(12):2703. [9] Primicerio J, Di Gennaro SF, Fiorillo E, Genesio L, Lugato E, Matese A, et al.

Data will be made available on request

A flexible unmanned aerial vehicle for precision agriculture. Precis Agric 2012;13(4):517–23. [10] Uto K, Seki H, Saito G, Kosugi Y. Development of UAV-mounted miniatu-

Acknowledgments

rure hyperspectral sensor system for agricultural monitoring. In: 2013 IEEE international geoscience and remote sensing symposium-IGARSS. IEEE; 2013, p. 4415–8. [11] Vasudevan A, Kumar DA, Bhuvaneswari N. Precision farming using unmanned aerial and ground vehicles. In: 2016 IEEE technological inno- vations in ICT for agriculture and rural development. TIAR, IEEE; 2016, p. 146–50. [12] Karatzinis GD, Apostolidis SD, Kapoutsis AC, Panagiotopoulou L, Boutalis YS, Kosmatopoulos EB. Towards an integrated low-cost agricultural monitoring system with unmanned aircraft system. In: 2020 international conference on unmanned aircraft systems. ICUAS, IEEE; 2020, p. 1131–8.

This research has been financed by the European Regional De- velopment Fund of the European Union and Greek national funds through the Operational Program Competitiveness, Entrepreneur- ship, and Innovation, under the call RESEARCH - CREATE - IN- NOVATE (T1EDK-00636) and from the European Commission un- der the European Union’s Horizon 2020 research and innova- tion programme under grant agreement no 101073952 (PERIVAL- LON). We also gratefully acknowledge the support of NVIDIA Corporation with the donation of GPUs used for this research.

6

Emmanuel K. Raptis, Konstantinos Englezos, Orfeas Kypris et al. SoftwareX 23 (2023) 101414

[29] Burdziakowski P. Evaluation of open drone map toolkit for geodetic grade

[13] Raptis EK, Karatzinis GD, Krestenitis M, Kapoutsis AC, Ioannidis K, Vrochidis S, et al. Multimodal data collection system for UAV-based preci- sion agriculture applications. In: 2022 sixth IEEE international conference on robotic computing. IRC, IEEE; 2022, p. 1–7. [14] Apostolidis SD, Kapoutsis PC, Kapoutsis AC, Kosmatopoulos EB. Cooper-

aerial drone mapping–case study. In: International multidisciplinary sci- entific geoconference surveying geology and mining ecology management. SGEM; 2017, p. 1–9. [30] Agapiou A. Vegetation extraction using visible-bands from openly licensed

unmanned aerial vehicle imagery. Drones 2020;4(2):27. [31] Jiménez-Muñoz JC, Sobrino JA, Plaza A, Guanter L, Moreno J, Martínez P.

ative multi-UAV coverage mission planning platform for remote sensing applications. Auton Robots 2022;46(2):373–400. [15] Aiello G, Valavanis KP, Rizzo A. Fixed-wing UAV energy efficient 3d path

Comparison between fractional vegetation cover retrievals from vegetation indices and spectral mixture analysis: Case study of PROBA/CHRIS data over an agricultural area. Sensors 2009;9(02):768–93. [32] Louhaichi M, Borman MM, Johnson DE. Spatially located platform and

planning in cluttered environments. J Intell Robot Syst 2022;105(3):1–13. [16] Wikipedia contributors. Hypertext transfer protocol — Wikipedia, the free

encyclopedia. 2022, https://en.wikipedia.org/w/index.php?title=Hypertext_ Transfer_Protocol&oldid=1127485375, [Online; accessed 22-December- 2022]. [17] Wikipedia contributors. MQTT — Wikipedia, the free encyclopedia. 2022,

aerial photography for documentation of grazing impacts on wheat. Geocarto Int 2001;16(1):65–70. [33] Yang D. Gobi vegetation recognition based on low-altitude photogramme-

try images of UAV. In: IOP conference series: earth and environmental science. Vol. 186, (5):IOP Publishing; 2018, 012053. [34] Hunt ER, Cavigelli M, Daughtry CS, Mcmurtrey JE, Walthall CL. Evaluation

https://en.wikipedia.org/w/index.php?title=MQTT&oldid=1127334174, [On- line; accessed 22-December-2022]. [18] Electron- a framework for building desktop applications using JavaScript,

of digital photography from model aircraft for remote sensing of crop biomass and nitrogen status. Precis Agric 2005;6(4):359–78. [35] Gitelson A, Stark R, Grits U, Rundquist D, Kaufman Y, Derry D. Vegetation

HTML, and CSS, https://www.electronjs.org/. [19] Leaflet-a JavaScript library for interactive maps, https://leafletjs.com/. [20] OpenStreetMap, https://www.openstreetmap.org/. [21] LeafLet Draw Toolbar, https://github.com/justinmanley/leaflet-draw- toolbar. [22] Richardson L, Amundsen M, Ruby S. RESTful Web APIs: Services for a

and soil lines in visible spectral space: a concept and technique for remote estimation of vegetation fraction. Int J Remote Sens 2002;23(13):2537–62. [36] Hoffman KL, Padberg M, Rinaldi G, et al. Traveling salesman problem.

In: Encyclopedia of operations research and management science. Vol. 1, Springer New York; 2013, p. 1573–8. [37] Chen L-C, Zhu Y, Papandreou G, Schroff F, Adam H. Encoder-decoder

changing world. O’Reilly Media, Inc.; 2013. [23] Eclipse Mosquitto, https://mosquitto.org/. [24] Piexif Library, https://piexif.readthedocs.io/en/latest/. [25] OpenDroneMap, https://github.com/OpenDroneMap/ODM. [26] PyInstaller, https://pyinstaller.org/en/stable/. [27] Gabriely Y, Rimon E. Spanning-tree based coverage of continuous areas by

with atrous separable convolution for semantic image segmentation. In: Proceedings of the european conference on computer vision. ECCV, 2018, p. 801–18. [38] Krestenitis M, Raptis EK, Kapoutsis AC, Ioannidis K, Kosmatopoulos EB,

Vrochidis S, et al. Cofly-weeddb: A UAV image dataset for weed detection and species identification. Data in Brief 2022;108575. [39] Raptis EK, Krestenitis M, Egglezos K, Kypris O, Ioannidis K, Doitsidis L, et

a mobile robot. Ann Math Artif Intell 2001;31(1):77–98. [28] Fevgas G, Lagkas T, Argyriou V, Sarigiannidis P. Coverage path plan-

al. End-to-end precision agriculture UAV-based functionalities tailored to field characteristics. J Intell Robot Syst 2023;107(2):23. [40] Egglezos K. CoFly-GUI: A precision agriculture software. 2023, https://

ning methods focusing on energy efficient and cooperative strategies for unmanned aerial vehicles. Sensors 2022;22(3):1235.

github.com/CoFly-Project/cofly-gui.

7
