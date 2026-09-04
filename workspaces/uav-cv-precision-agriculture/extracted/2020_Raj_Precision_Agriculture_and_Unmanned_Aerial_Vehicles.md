---
workspace_id: SCI-000411
doi: 10.1007/978-3-030-27157-2_2
title: Precision Agriculture and Unmanned Aerial Vehicles (UAVs)
authors:
- family_name: Raj
  given_name: Rahul
  orcid: null
- family_name: Kar
  given_name: Soumyashree
  orcid: null
- family_name: Nandan
  given_name: Rohit
  orcid: null
- family_name: Jagarlapudi
  given_name: Adinarayana
  orcid: null
year: 2020
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:26:14.095517+00:00'
---

# Precision Agriculture and Unmanned Aerial Vehicles (UAVs)

Chapter 2 Precision Agriculture and Unmanned Aerial Vehicles (UAVs)

Rahul Raj, Soumyashree Kar, Rohit Nandan, and Adinarayana Jagarlapudi

Abstract Farming in developing countries is majorly dependent on the traditional knowledge of farmers, with unscientiﬁc agricultural practices commonly implemented, leading to low productivity and degradation of resources. Moreover, mechanization has not been integral to farming, and thus managing a farm is a time- consuming and labor-intensive process. Consequently, precision agriculture (PA) offers great opportunities for improvement. Using geographic information and communication technology (Geo-ICTs) principles, PA offers the opportunity for a farmer to apply the right amount of treatment at the right time and at the right location in the farm. However, in order to collect timely high-resolution data, drone- based sensing and image interpretation is required. These high-resolution images can give detailed information about the soil and crop condition, which can be used for farm management purposes. Leaf area index, normalized difference vegetation index, photochemical reﬂectance index, crop water stress index, and other such vegetation indices can provide important information on crop health. Temporal changes in these indices can give vital information about changes in health and canopy structure of the crop over time, which can be related to its biophysical and biochemical stress. These stresses may have occurred due to insufﬁcient soil nutri- ent, inappropriate soil moisture, or pest attack. Through UAV-based PA, stressed areas can be identiﬁed in real time, and some corrective measures can also be carried out (e.g., fertilizer and pesticide spraying). Moreover, the advantages and different approaches to integrate the UAV data in the crop models are also described.

Keywords Drone-based sensors · Vegetation indices · Agricultural drones · UAV- based precision agriculture cycle

R. Raj Indian Institute of Technology Bombay – Monash Research Academy, Mumbai Maharashtra, India e-mail: rahul_raj@iitb.ac.in

S. Kar · R. Nandan · A. Jagarlapudi (*) Indian Institute of Technology Bombay, Mumbai, Maharashtra, India e-mail: karsoumya@iitb.ac.in; rohitnandan@iitb.ac.in; adi@csre.iitb.ac.in

© Springer Nature Switzerland AG 2020 R. Avtar, T. Watanabe (eds.), Unmanned Aerial Vehicle: Applications in Agriculture and Environment, https://doi.org/10.1007/978-3-030-27157-2_2

7

8 R. Raj et al.

2.1 Precision Agriculture

The Industrial Revolution has pushed agriculture practices toward greater energy inputs through the use of big machinery, chemicals, and fertilizers. However, these practices may lead to low soil fertility, soil erosion, soil salinization, compaction of subsoils, and soil-water pollution, which are having negative societal and environ- mental implications (Liaghat and Balasundram 2010). Precision agriculture (PA) is an innovative and integrated farming approach which enables farmers to use evidence-based decision-making at the farm level, to ensure optimal use of resources to minimize such societal and environmental implications (Tokekar et al. 2016). PA can use traditional knowledge together with spatial information and management- intensive technologies. This helps in making the system sustainable, productive, and proﬁtable. The technologies frequently used in PA include Geographic Information System, Global Positioning System, remote sensing, computer modelling, variable rate technology, and machine learning approach with advanced information processing for timely crop management (Liaghat and Balasundram 2010). The PA cycle can be explained in the following steps:

1. Data collection: Within-ﬁeld variability in soil and crop parameters and local weather conditions are measured, monitored, and mapped. 2. Data interpretation: Data interpretation using various crop models or image interpretation and/or data assimilation techniques are undertaken to identify spatially variable parameters. 3. Application: Based on data processing results, farm management can be tailored for the right place, the right time, and the right amount.

Precision agriculture cycle is shown as in Fig. 2.1.

Fig. 2.1 The precision agriculture cycle. (Comparetti et al. 2011)

2 Precision Agriculture and Unmanned Aerial Vehicles (UAVs) 9

Data collection and database generation is a very important part of PA, requiring wise selection of sensors and their deployment in the farm to ensure accuracy and precision of on-farm decision using a decision support system. Sensors can be on ground or airborne, with the purpose of ﬁnding information such as the health of the crop, its growth stage, physical and chemical properties of the soil/pant, temporal meteorological data, etc. Remote sensing and geospatial techniques are an integral part of the data collection and processing process and are used to detect in-ﬁeld variation. High-resolution satellite imagery is very useful for studying variations in crop and soil conditions. However, problems associated with the availability and cost of such imagery at an appropriate spatial and temporal resolution suggest that an alternative, such as “small unmanned aerial systems (UAS),” is needed for opera- tional PA (Zhang and Kovacs 2012).

2.2 Satellite vs Drone Sensing

Satellite-based remote sensing is one of the traditional methods to acquire remotely sensed data, but the freely available images can only help in getting data at a resolution of 30 m or greater, which is too coarse for many applications. Some commercial satellites provide sub-meter resolution satellite imagery (spatial resolu- tion < 1 m for panchromatic and > 1 m for multispectral) for a given time and place/ area at a given price but are typically infrequent in time (Liaghat and Balasundram 2010). While satellite images may be the best option in the case of very large areas, the coarse spatial and temporal resolution with long revisit durations signiﬁcantly limits its application, particularly during cloudy conditions of the atmosphere. Consequently, images taken by low-altitude remote sensing platforms such as small unmanned aerial vehicles or small manned aircraft provide an alternative.

The cost of operation is low for UAVs, and they can map areas with very high spatial resolution and at desired temporal repeat (Zhang and Kovacs 2012). More- over, they can ﬂy below the cloud, maximizing data availability. However, there are other problems which affect drone operation, including a high windy condition in which the drone can’t be ﬂown, higher risk of a crash in case of operator error, sudden weather change or loss of power, and low battery life which limits spatial coverage. Moreover, the commercial satellite takes usually 7 days to provide processed images, while drone-based images can be processed in near real time (Satimagingcorp 2018). While drones can be ﬂown at any time as per requirement with minimal operational cost, for a small- or medium-scale farmer, it is very difﬁcult to get commercial satellite images as the cost is high and the minimum area which can be ordered is the range of 25 km2 (Landinfo 2018). Another advantage of drone data is that canopy images can be taken at various view angles in order to analyze the structure of the canopy. The limitations associated with satellite data over drone-based high-resolution images are summarized in Table 2.1.

The type of drone which can be used for agricultural application may depend on the size of the farm and type of cameras/sensors which need to be used. Battery

10 R. Raj et al.


> **Table 2.1 Satellite data vs drone-based sensing**

Sub-meter resolution commercial satellite image Drone-based high-resolution image Cloud cover and atmospheric dust particles create a bottleneck on image acquisition

As ﬂight height is low thus limited effect of cloud cover Real-time image acquisition and processing are not possible and usually take 7 days of delay

Images can be obtained and processed in a few hours depending on the size of the farm Images captured at some ﬁxed time of day depending on the frequency of revolution of the satellite

Images can be captured at the desired time of day

Maximum available panchromatic geometrical resolution is 30 cm, while multispectral resolu- tion would be 1.24 m

Spatial resolution may go around 1 cm

Minimum area map which can be ordered is 25 square km or more (if only natural color map is required, then 10 square km)

Map can be generated for a small and medium area which would be much cheaper than sat- ellite imaging Images generally are taken from zenith Images at a different angle can be taken which will help in getting architectural information of canopies

capacity also plays an important parameter which decides ﬂight time of a drone. Table 2.2 shows the types of drones and their capability to carry various sensors.

2.3 UAV-Based Sensors in Precision Agriculture

Applied agricultural research is generally related to productivity improvement, yield quality enhancement, cost-effective technologies, selection of better crop genotypes, and weather-resistant crops. There have been a signiﬁcant number of studies conducted in this domain. However, more than 50% (~3000) of the papers available on drone use in agriculture are published after 2016, with almost 90% of the papers published after 2013 (Web of Science). This is due to improved efﬁciency of UAVs and scanning imagers over the last 5 years, together with dissatisfaction with satellite images for making on-farm decisions in near real time (Matese et al. 2015). Since satellite’s spatial resolution is coarse for small farm and ground-based sensors cannot cover a big area on the ﬁeld, thus drone-based data collection shows an alternative path to collect data at such temporal and spatial resolution.

UAVs have the capability to carry various sensors which are useful for studying crop-related parameters. Literature shows that drones can be integrated with optical sensors like RGB camera, multispectral camera, and hyperspectral camera. Thermal cameras can also be used on drones which help in identifying water stress in the crop (Calderón et al. 2013). LiDAR sensors are used on drones to estimate the height of the canopy which ultimately helps in biomass estimation of the crop. Apart from digital data collection, drones are also applied to do aerobiological sampling above agricultural ﬁelds for early identiﬁcation of pest attack on the crop (Schmale et al.

2 Precision Agriculture and Unmanned Aerial Vehicles (UAVs) 11


> **Table 2.2 Types of drones and their capability to carry sensor**

Weight in kg (including payload)

Area coverage capacity of the drone Nano Less than 0.25 kg This has not been used in agri- culture till now as sensors are usually of more weight and cannot be lifted by nano-drones

Types of sensors which can be mounted on the drone

Type

NA

Can cover up to 4–5 acres of ground area depending on the height of ﬂight. Flight height is generally kept lower than 100 m Small 2 < weight < 25 High-resolution RGB camera, multispectral camera, LiDAR sensor, lightweight hyperspectral imager, and small thermal imager can be mounted on the drone

Micro 0.25 < weight < 2 Small RGB, lighter multispec- tral camera, and small LiDAR sensor can be mounted on this drone

Can cover up to 10–20 acres of ground area depending on the height of ﬂight

Medium 25 < weight < 150 Bigger high-resolution RGB camera, multispectral camera, LiDAR sensor, medium-weight hyperspectral imager, and ther- mal camera can be mounted on the drone. It can also be used for spraying of pesticides

Can cover up to 100 acres of ground area depending on the height of ﬂight. Flight height is generally higher than 50 m

Large Greater than 150 Bigger and heavyweight cam- eras and sensors can be mounted on the drone. It can be used for spraying of pesticides

Can cover more than 100 acres of ground area. Flight height is generally higher than 100 m

2008). Drones can also be used to take corrective measures in farms like the spraying of pesticides in stressed areas of the farm. Table 2.3 shows the different sensors which can be installed on the drone to study various characteristics of crops.

2.3.1 Visible and IR Imagers and Sensors (400–2500 nm)

Imagers in visible and IR spectrum are popularly used from a drone platform for vegetation mapping. These optical sensors can be used for estimation of biomass, LAI, identiﬁcation of various growth stages, and healthiness of a crop. Pest identi- ﬁcation, survey of a farm, mapping, etc. are also done using these sensors. Below is the list of optical sensors available for drone-based sensing.

(a) RGB Camera

A digital RGB camera can be mounted on a UAV and top of the canopy or stereo images of farm can be captured. These images are in visible bands (400–700 nm)

12 R. Raj et al.


> **Table 2.3 Drone-based sensors and their use**

Drone-based sensing of vegetation The following cameras/sensors/instruments can be installed on a drone, and data can be collected which can be further used for estimation of various crop parameters: 1. PAR and IR imagers and sensors (400–2500 nm) (a) RGB camera (b) Multispectral camera/red-edge camera (c) Hyperspectral imager (400–2500 nm) (i) Snapshot imager (ii) Line scanner imager 2. Thermal camera (3000–12,000 nm) 3. LiDAR sensor 4. Aerobiological sampling 5. Spraying of pesticides through drone

which collect reﬂectance in three broad ranges of wavebands: red, green, and blue bands. The spatial resolution of the image depends on camera speciﬁcations and height from which drone was ﬂown. With good ﬂight planning, these cameras are capable of collecting very high spatial resolution images which might give pixel resolution up to 1 mm. However, the spatial resolution is decided as per objective of the work, and collecting extremely high spatial resolution data might not be a good idea as it will require more space to store and greater time to process.

These images can be used for making ortho-mosaic of the farm, studying the structural properties of the plants/trees (RAMI), detecting the weed location or pest- affected areas in the farm, and estimating the LAI of the crop. Height estimation of crop is also possible from drone-based RGB images which helps in biomass estimation. These cameras are cheaper than multispectral or hyperspectral imagers, easy to operate, lighter in weight, and thus very popular for vegetation studies.

(b) Multispectral Camera/Red-Edge Camera

Multispectral cameras consist of 4–6 bands of around 10–50 nm bandwidth in blue, green, red, red-edge, and NIR regions of the electromagnetic spectrum. These cameras are generally used to calculate normalized difference vegetation indices and are capable of estimation of biomass and identiﬁcation of highly stressed areas in the farm.

(c) Hyperspectral Imager (400–2500 nm)

(i) Snapshot imager: These imagers are capable of acquiring images in several

narrow bands from visible to IR region of EM spectrum. Bandwidth is generally around 10 nm (broader than line scanner imagers). These imagers are easy to handle (compared to line scanner), and data is relatively easy to process as raster ﬁle is generated by the imager which can be directly used in GIS software. (ii) Line scanner imager: These imagers are comparatively complex to oper-

ate. Speed of the drone is decided by the camera frame rate so drone should

2 Precision Agriculture and Unmanned Aerial Vehicles (UAVs) 13

ﬂy as per frame rate of the camera as the camera captures a narrow row on the ground in a given time, and thus ﬂight should be synchronized accord- ingly. Bandwidth can be narrow (around 2 nm). These imagers are relatively difﬁcult to handle and collected data is complex to process.

2.3.2 Thermal Camera (3000–12,000 nm)

Thermal cameras are very useful in determining water stress in the crop. It has been seen that the crops that have water stress are relatively at higher temperature than the crops which are not having water stress. However, this temperature difference is time dependent (morning, afternoon, or evening) and very much affected by varying solar radiations. The temperature difference captured by the thermal camera can distin- guish the water-stressed crop easily during afternoon when sky is clear and solar radiation is available (Bellvert et al. 2014).

2.3.3 LiDAR Sensor

Light Detection and Ranging (LiDAR) sensor is very useful in measuring canopy height. The sensor can collect data from up to 250-m height (depending on manu- facturer), and the accuracy may be of few millimeters. This sensor data is generally fed to a photogrammetry software for analysis purpose.

2.3.4 Aerobiological Sampling

An air sampler can be ﬁtted on a drone which can collect and store air samples above agricultural farms. The analysis of these aerobiological samples helps in early identiﬁcation of pest attack on crop (Schmale et al. 2008).

2.3.5 Spraying of Pesticides Through Drone

This is a corrective measure which can be implemented through the drone. Tankers ﬁlled with pesticide are carried by drones and the spraying can be done precisely in those areas which are found to be stressed.

14 R. Raj et al.

2.4 Vegetation Indices and Other Techniques for Drone- Based Data Analysis

From remote sensing techniques, different vegetation indices and soil properties can be calculated using various airborne sensors. For example, leaf area index and NDVI are two popular indices used to indicate crop health/state, while thermal cameras can be used to estimate water stress (Berni et al. 2009). Canopy reﬂectance can be used to identify various biophysical and biochemical properties of the canopy through either a physical or data-driven model such as machine learning model or machine learning technique that is evolving very quickly and has shown better results in many cases. To predict the crop health status efﬁciently, it is very important to collect reliable farm data which represents the farm at sufﬁcient spatial and temporal resolution.

Use of vegetation indices for estimating various crop biophysical and biochem- ical characteristics is one of the popular methods. However, there is always a sensitivity issue associated with indices, e.g., LAI or NDVI tends to saturate with the increasing amount of biomass in the area. Indices have shown good results with satellite data and with reasonable classiﬁcation accuracy. Let us discuss some popular indices in this chapter.

Leaf area index (LAI) is a parameter associated with the physiological processes of the crop. It is used to study growth, photosynthesis, and transpiration of plants and to know interception of radiation in the canopy. LAI is also used in crop yield prediction and water balance modelling, deﬁned as the total one-sided area of photosynthetic tissue per unit ground surface area (Jonckheere et al. 2004). When LAI value increased from approximately 3–4 (depending on the canopy), then NDVI loses its sensitivity toward change in LAI and starts saturating. This is because chlorophyll is a highly efﬁcient absorber of red radiation, and thus after some point adding more chlorophyll to the canopy or in other words increasing leafy material in the canopy will not change red reﬂectance much. To overcome this situation, several solutions have been developed. One of the simplest solutions is to use wide dynamic range vegetation index, i.e., WDRVI. To make this index, weighting factor ranging from 0 to 1 is used with NIR reﬂectance (in the numerator as well as in denominator) in the formula of NDVI (Gitelson 2004):

NDVI ¼ NIR  R

NIR þ R &WDRVI ¼ a  NIR  R

a  NIR þ R : ð2:1Þ

When weighting factor approaches to 0, the linear relationship between WDRVI and LAI graph tends to increase but with the reduction in sensitivity of LAI changes in sparse canopies. Another index which shows better sensitivity with LAI is designed with blue bands. This is called enhanced vegetation index:

 

EVI ¼ 2:5  NIR  R NIR þ 6  R ð Þ  7:5  B ð Þ þ 1

: ð2:2Þ

2 Precision Agriculture and Unmanned Aerial Vehicles (UAVs) 15

Later EVI is modiﬁed and blue band is removed. The modiﬁed version of EVI is known as EVI2. Apart from having a linear relationship with LAI, EVI2 has less soil sensitivity compared to NDVI:

EVI2 ¼ 2:5  NIR  R NIR þ 2:4  R ð Þ þ 1 ð Þ : ð2:3Þ

LAI can be combined with other vegetation indices to achieve maximal sensitiv- ity. For maize-soybean rotation crop, calculated gLAI for maize and soybean ranged from 0–6.5 to 0–5.5, respectively. For gLAI lower than 2, NDVI is most sensitive, while for gLAI greater than 2, simple ratio (SR ¼ NIR/R) and chlorophyll indices (CI ¼ NIR/G  1) are most sensitive. However, this relationship is crop speciﬁc and may change with other crops. The best index combination for maize and soybean is combination of NDVI and SR. With this combination, coefﬁcient of variance for maize and soybean was less than 20% and 23%, respectively (Nguy et al. 2012). In an experiment on grapevines, it is seen that NDVI values calculated through UAV-based camera show strong linear correlation (R2 ¼ 0.97) with NDVI calcu- lated by ﬁeld spectroradiometer (Primicerio et al. 2012).

There are various index-based and sensor-based methods to estimate crop water stress. Thermal cameras can also be used to estimate crop water stress, and CWSI can be found as shown in Eq. 2.4 (Bellvert et al. 2014):

CWSI ¼ Tc  Ta ð Þ  Tc  Ta ð ÞLL Tc  Ta ð ÞUL  Tc  Ta ð ÞLL ð2:4Þ

In Eq. 2.4, (Tc  Ta) is the canopy-air temperature difference, LL is the (Tc  Ta) values for lower limit, and UL is the upper limit of the same.

There is an index to estimate biomass of crop which is called “normalized green-red difference index (NGRDI).” NGRDI is found to be linearly related to biomass of alfalfa, corn, and soybean up to about 120 g m2 (Hunt et al. 2005) as shown in Eq. 2.5:

NGRDI ¼ Green DN  Red DN ð Þ Green DN þ Red DN ð Þ : ð2:5Þ

UAV platforms are also being used to acquire ﬂuorescence, temperature, and narrowband indices for water stress detection using a hyperspectral imager and a thermal camera. A strong relation is found among crown temperature, the blue- green BGI1 (R400/R550) index, and the chlorophyll ﬂuorescence estimates (Zarco et al. 2012). In research done on olive orchards, it is observed that canopy temperature and physiological hyperspectral indices such as PRI and chlorophyll ﬂuorescence are related with physiological stress caused by verticillium wilt (Calderón et al. 2013). Table 2.4 tabulates all the important vegetation indices compiled through a detailed literature.

16 R. Raj et al.


> **Table 2.4 Indices used for identiﬁcation of leaf water content and nitrogen content**

Indices Formula Source Structural indices

NDVI ¼ NIRR

NIRþR Jackson et al. (1980)

NDVI (normalized difference vegetation Index)

WDRVI ¼ aNIRR

WDRVI (wide dynamic range vegetation index)

aNIRþR (0 < a < 1) Gitelson (2004)

RDVI ¼ R800R670 R800þR670 ð Þ0:5 Roujean and Breon (1995)

RDVI (renormalized difference vegetation index)

OSAVI ¼ 1þ0:16 ð Þ R800R670 ð Þ R800þR670þ0:16 ð Þ Rondeaux et al. (1996)

OSAVI (optimized soil adjusted vegetation index)

EVI ¼ 2:5  NIRR NIRþ 6R ð Þ 7:5B ð Þþ1   Jiang et al. (2008)

EVI (enhanced vegetation index used for LAI estimation)

EVI2 ¼ 2:5  NIRR NIR þ 2:4R ð Þþ1 ð Þ

EVI2 (modiﬁed EVI) (less soil sensitive than NDVI)

NGRDI ¼ Green DNRed DN ð Þ Green DNþRed DN ð Þ Hunt et al. (2005)

Biomass estimation

NGRDI (normal- ized green-red difference index)

R750 R710 Zarco- Tejada et al. (2001) DCNI (double- peak canopy nitrogen Index)

Chlorophyll indices

Red-edge reﬂectance index

R720R700 R700R670 R720R760þ0:16 ð Þ Chen et al. (2010)

DCNI ¼



TCARI (transformed chlo- rophyll absorption in reﬂectance index)

Kim et al. (2002)

TCARI ¼ 3

ðR700  R670Þ



0:2ðR700  R550ÞR700

R670

TCARI OSAVI Haboudane et al. (2002) Carotenoid index R515 R570 Zarco- Tejada et al. (2013) Xanthophyll indices

Combined TCARI/OSAVI

PRI ¼ R570R539

PRI (photochemi- cal reﬂectance index)

R570þR539 Gago et al. (2015)

Normalized PRI PRI norm ¼ R515R531

R515þR531 Gago et al. (2015) Blue/green ratio index

BGI1 BGI1 ¼ R400

R550 Zarco- Tejada et al. (2012)

(continued)

2 Precision Agriculture and Unmanned Aerial Vehicles (UAVs) 17


> **Table 2.4 (continued)**

Indices Formula Source BGI2 BGI2 ¼ R450

R550 Zarco- Tejada et al. (2012) Leaf equiva- lent water thickness

MSI ¼ R1600

MSI (moisture stress index)

R820 Hunt et al. (1989) NDWI (normal- ized difference water index)

NDWI ¼ R860R1240

R860þR1240 Stimson et al. (2005)

NDII ¼ R820R1600

R820þR1600 Hardisky et al. (1983)

NDII (normalized difference infrared index)

MDWI ¼ R max R min R max þR min h i

Eitel et al. (2006)

MDWI (maximum difference water index)

from 1500  1700

CWSI CWSI ¼ TcTa ð Þ TcTa ð ÞLL TcTa ð ÞUL TcTa ð ÞLL Bellvert et al. (2014)

Crop water Stress

Apart from the index methods, hyperspectral drone data can also be analyzed based on its pixel-wise spectral signature. Various crops can be distinguished based on their characteristics of spectral signature. This might need machine learning approach to analyze the data. There are also physical models like PROSPECT, PROSAIL, LIBERTY, etc. that are available which take spectra as input and estimate plant’s chemical and biophysical properties.

2.5 UAV-Based Precision Agriculture Cycle

Drones can be helpful in on-farm decision-making even before sowing starts. When farm soil bed is being prepared for sowing, UAV-mounted LiDAR sensor can be ﬂown to check the ﬂatness of the farm. If it is found that the soil bed is not ﬂat enough, then based on elevation difference, the farm can be uniformly ﬂattened. A uniformly ﬂat ﬁeld is one of the important requirements in order to stop unwanted movement of water in the farm. Research is going on to estimate soil nutrient content from drone-based sensors.

After sowing, temporal monitoring of the farms can be done using drone- mounted RGB camera. Images taken from these cameras can be used to monitor crop growth (biomass, LAI, height, etc.). The images can detect weed location in the farm and can also identify the pest-affected areas. In some crops like maize where tasseling happens, these images are capable of counting number of tassels which helps in early estimation of yield. During crop vegetative stage, apart from RGB, multispectral and hyperspectral cameras can also be used to not only estimate biophysical properties of the crop but also biochemical properties like leaf nutrient, water content, etc. Once location of these nutrient or water stressed areas, weeds, and

18 R. Raj et al.

Fig. 2.2 The UAV-based precision agriculture cycle

pests are identiﬁed, drones can be used to take corrective measures and can spray pesticides or fertilizers or water precisely at the location in the farm. Figure 2.2 shows UAV-based precision agriculture cycle.

2.6 UAV in High-Throughput Plant Phenotyping

It has been observed that since the conceptualization of the process, phenotyping, there has been constant endeavor in evolving toward ﬁeld phenotyping from lab phenotyping (Fukai and Fischer 2012). While several studies focus on modelling various phenotypic behaviors (Huang et al. 2010), several others experiment with different platforms that can both scale up and help understand the regional phenol- ogy better (Wallace et al. 2016). It’s also stated in Wallace et al. (2016) that “the phenological development stage, however, can only be determined from an imagery collection rate that is unfeasible with aerial campaigns given the economic limita- tions of most natural resource budgets,” which clearly distinguishes the edge of UAV imaging over other aerial remote sensing methods.

Although UAVs have been increasingly used for HTPP, the sensors on board differ with different applications. While RGB cameras are used for the

2 Precision Agriculture and Unmanned Aerial Vehicles (UAVs) 19

morphological traits, multispectral/red-edge and hyperspectral cameras are used for the retrieval of biochemical traits. Holman et al. (2016) have used RGB camera- based UAV imagery to study both crop height and growth rate, by generating 3D digital surface models (via surface from motion, SfM, photogrammetry technique) from multi-temporal UAV data. The SfM model-derived estimates of the growth rate have been applied for the winter wheat ﬁeld phenotyping experiment which contained 25 different varieties grown with 4 different nitrogen fertilizer treat- ments, and it could be identiﬁed that the per-day growth rates differed between 13 mm/day and 17 mm/day. Hence, UAV imaging not only helps in high through- put but also “precise” phenotyping. In a similar study by Watanabe et al. (2017), the NIR-GB camera-based UAV imaging has been exploited to derive height of the sorghum plants. These height estimates have subsequently been successfully used as the training data to the genomic prediction models for delineating the genotypic differences in sorghum, since the predicted and the ground truth plant height values were highly correlated (r ¼ 0.842). There are also instances (Burud et al. 2017) where VIS/NIR multispectral cameras have been used to examine the efﬁciency of the UAVs as HTPP tools for plant breeding. In an attempt to delineate the ﬁeld plots based on different vegetation indices obtained from UAV imagery, Haghighattalab et al. (2016) have developed a semiautomated image processing pipeline to perform the critical photogrammetric operations and radiometric cali- bration of the images. The relationships between vegetation indices (VIs) extracted from high spatial resolution multispectral UAV imagery and ground truth spectral data collected using handheld spectroradiometer have also been mentioned. Thus, UAVs enable faster and higher-resolution crop data collection (as part of HTPP) while simultaneously facilitating scientists and growers with improved precision agriculture practices on increasingly larger farms, e.g., site-speciﬁc application of water and nutrients.

Even though there are many advancements in UAV-based high-resolution data acquisition techniques, there is a need for research on image interpretation tech- niques to identify and estimate various crop physical and chemical properties like LAI, counting of crop kernels, leaf water and nitrogen percentage, etc. so that input resources can be utilized optimally.

2.7 Integration of UAV Data with Crop Models

There are two types of crop models. Empirical models are based on the regression relation between one or a few parameters and the observed data. Statistical models are less data intensive. The major limitation of these models is that they cannot be used for the regions and for environmental conditions for which historical datasets are not available (Jones et al. 2017). Process-based models simulate the crop physiological properties through time using differential equations to describe crop production. Within this conceptual umbrella, models employ functions, which approximate the hypothetical mechanistic canopy, and soil processes being simu- lated for a given time step (Wallach et al. 2014). The input data requirements of these

20 R. Raj et al.

models are more than empirical models (Di Paola et al. 2016). The process-based models can be used to explore the crop responses to climate change/variability condition and sets of management practices. This is the main advantage of the process-based models over empirical models.

Cropping systems operate at different spatial and temporal scales. The crop modelling requires the spatial distribution of soil characteristics (soil moisture), canopy state variables (LAI, biomass, nitrogen content, etc.), and meteorological data which are uncertain. The geospatial information of soil characteristics and canopy state variables can be estimated using remote sensing data.

In India, commonly, the farmers hold limited farm, and this invokes the hetero- geneity in the farm. It is a challenging task to monitor the small farms accurately using satellite-based remote sensing data. For most of the agricultural applications, the physiological properties and high-resolution data are required, and these are the two major limitations in the satellite-based remote sensing. To overcome these two limitations, the crop models can be used to simulate the physiological properties, UAV can be used to collect the high-resolution remote sensing data, and both can be integrated. There are numerous researches carried out on the assimilation of satellite- based remote sensing and crop models (Jin et al. 2018). For accurate decision- making in heterogeneous farm, satellite sensing can be replaced by the drone sensing. To integrate remote sensing and crop models, the following approaches can be utilized:

In the ﬁrst approach, the state variables of the models are directly replaced by the biophysical or biochemical products of the remote sensing data at each model’s time step, viz., the remote sensing estimated LAI has been directly used to replace the state variables in the crop models (Schneider 2003; Hadria et al. 2006). This has reportedly improved the accuracy of the model’s simulated crop production variables.

In the second approach, the biophysical characteristics or the biomass or crop yield estimated from drone-sensed data can be used to calibrate the crop model by adjusting its parameters. Several algorithms have used the calibration approach (Jin et al. 2018).

In the third approach, the data assimilation methods are used. Here, the simulated data from the crop model, continuously assimilated based on the assumption that better simulation data on the current simulation time step, will increase the accuracy of the simulation at next time steps. This method was found more accurate and popular in the past studies. There were numerous data assimilation algorithms such as 4DVar, EnKF, POD4DVar, ensemble square root ﬁlter, etc. used to integrate the state variables of crop models and remote sensing products such as soil moisture, AGB, and LAI (Jin et al. 2018).

Satellite remote sensing data have errors due to mix pixels, atmosphere, etc. These errors are inherent in the remote sensing products. In the ﬁrst approach, crop models use remote sensing estimated products instead the simulated value, and the errors linked with remote sensing data directly affect the crop models’ accuracy. This error could be reduced by using the drone sensing data instead of satellite remote sensing data. The second and third approach have more advantages and the optimi- zation and assimilation algorithms are used to minimize the errors. If all three approaches are compared to each other, according to Jin et al. (2018), theoretically,

2 Precision Agriculture and Unmanned Aerial Vehicles (UAVs) 21

the second method is better than the other two; however, the only drawback of the second method is that it requires many iterations for optimization, which results in increased computation time.


## References

Bellvert J et al (2014) Mapping crop water stress index in a ‘Pinot-noir’vineyard: comparing ground

measurements with thermal remote sensing imagery from an unmanned aerial vehicle. Precis Agric 15(4):361–376 Berni JAJ et al (2009) Thermal and narrowband multispectral remote sensing for vegetation

monitoring from an unmanned aerial vehicle. IEEE Trans Geosci Remote Sens 47(3):722–738 Burud I, Lange G, Lillemo M, Bleken E, Grimstad L, From PJ (2017) Exploring robots and UAVs

as phenotyping tools in plant breeding. IFAC-PapersOnLine 50(1):11479–11484 Calderón R et al (2013) High-resolution airborne hyperspectral and thermal imagery for early

detection of Verticillium wilt of olive using ﬂuorescence, temperature and narrow-band spectral indices. Remote Sens Environ 139:231–245 Chen P et al (2010) New spectral indicator assessing the efﬁciency of crop nitrogen treatment in

corn and wheat. Remote Sens Environ 114(9):1987–1997 Comparetti A et al (2011) Precision agriculture: past, present and future. Conference: international

scientiﬁc conference “Agricultural engineering and environment. (Accessed from Researchgate) Di Paola A, Valentini R, Santini M (2016) An overview of available crop growth and yield models

for studies and assessments in agriculture. J Sci Food Agric 96:709–714 Eitel JUH et al (2006) Suitability of existing and novel spectral indices to remotely detect water

stress in Populus spp. For Ecol Manag 229(1–3):170–182 Fukai S, Fischer KS (2012) Field phenotyping strategies and breeding for adaptation of rice to

drought. Front Physiol 3:282 Gago J et al (2015) UAVs challenge to assess water stress for sustainable agriculture. Agric Water

Manag 153:9–19 Gitelson AA (2004) Wide dynamic range vegetation index for remote quantiﬁcation of biophysical

characteristics of vegetation. J Plant Physiol 161(2):165–173 Haboudane D et al (2002) Integrated narrow-band vegetation indices for prediction of crop

chlorophyll content for application to precision agriculture. Remote Sens Environ 81 (2–3):416–426 Hadria R, Duchemin BI, Lahrouni A, Khabba S, Er Raki S, Dedieu G, Chehbouni A, Olioso A

(2006) Monitoring of irrigated wheat in a semi-arid climate using crop modelling and remote sensing data: impact of satellite revisit time frequency. Int J Remote Sens 27:1093–1117 Haghighattalab A, Pérez LG, Mondal S, Singh D, Schinstock D, Rutkoski J, Ortiz-Monasterio I,

Singh RP, Goodin D, Poland J (2016) Application of unmanned aerial systems for high throughput phenotyping of large wheat breeding nurseries. Plant Methods 12(1):35 Hardisky MA, Klemas V, Smart M (1983) The inﬂuence of soil salinity, growth form, and leaf

moisture on spectral radiance of spartina alterniﬂora canopies. Photogramm Eng Remote Sens 16(9):1581–1598 Holman F, Riche A, Michalski A, Castle M, Wooster M, Hawkesford M (2016) High throughput

ﬁeld phenotyping of wheat plant height and growth rate in ﬁeld plot trials using UAV based remote sensing. Remote Sens 8(12):1031 Huang X, Sang T, Zhao Q, Feng Q, Zhao Y, Li C, Zhu C, Lu T, Zhang Z, Li M, Fan D (2010)

Genome-wide association studies of 14 agronomic traits in rice landraces. Nat Genet 42(11):961 Hunt Jr, Raymond E, Rock BN (1989) Detection of changes in leaf water content using near-and

middle-infrared reﬂectances. Remote Sens Environ 30(1):43–54

22 R. Raj et al.

Hunt ER et al (2005) Evaluation of digital photography from model aircraft for remote sensing of

crop biomass and nitrogen status. Precis Agric 6(4):359–378 Jackson RD et al (1980) Hand-held radiometry: a set of notes developed for use at the workshop of

Hand-held radiometry. USDA, Oakland Jiang Z et al (2008) Development of a two-band enhanced vegetation index without a blue band.

Remote Sens Environ 112(10):3833–3845 Jin X, Kumar L, Li Z, Feng H, Xu X, Yang G, Wang J (2018) A review of data assimilation of

remote sensing and crop models. Eur J Agron 92:141–152 Jonckheere I et al (2004) Methods for leaf area index determination. Part I: theories, techniques and

instruments. Agric For Meteorol 121:19–35 Jones JW, Antle JM, Basso B, Boote KJ, Conant RT, Foster I, Godfray HCJ, Herrero M, Howitt RE,

Janssen S et al (2017) Brief history of agricultural systems modeling. Agric Syst 155:240–254 Kim MS et al (2002) Assessment of environmental plant stresses using multispectral steady-state

ﬂuorescence imagery, Air Pollution and Plant Biotechnology. Springer, Tokyo, pp 321–341 LandInfo: “Buying Satellite Imagery: GeoEye, WorldView 1, 2, 3, QuickBird, IKONOS, Pléiades.”

[Online]. Available: http://www.landinfo.com/satellite-imagery-pricing.html. Assessed on 10 Jan 2018 Liaghat S, Balasundram SK (2010) A review: the role of remote sensing in precision agriculture.

Am J Agric Biol Sci 5(1):50–55 Matese A et al (2015) Intercomparison of UAV, aircraft and satellite remote sensing platforms for

precision viticulture. Remote Sens 7(3):2971–2990 Nguy-Robertson A et al (2012) Green leaf area index estimation in maize and soybean: combining

vegetation indices to achieve maximal sensitivity. Agron J 104(5):1336–1347 Primicerio J et al (2012) A ﬂexible unmanned aerial vehicle for precision agriculture. Precis Agric

13(4):517–523 RAMI: Radiative Transfer Model Intercomparison (RAMI). http://rami-benchmark.jrc.ec.europa.

eu/HTML/RAMI3/MODELS/4SAIL2/4SAIL2.php. Accessed on 06 Jan 2018 Rondeaux G, Steven M, Baret F (1996) Optimization of soil-adjusted vegetation indices. Remote

Sens Environ 55(2):95–107 Roujean J-L, Breon F-M (1995) Estimating PAR absorbed by vegetation from bidirectional

reﬂectance measurements. Remote Sens Environ 51(3):375–384 Satimagingcorp World view-4 Satellite imagery and satellite sensor speciﬁcations | satellite imaging

corp. [Online]. Available: http://www.satimagingcorp.com/satellite-sensors/geoeye-2/. Assessed on 10 Jan 2018 Schmale III, David G, Dingus BR, Reinholtz C (2008) Development and application of an

autonomous unmanned aerial vehicle for precise aerobiological sampling above agricultural ﬁelds. J Field Robot 25(3):133–147 Schneider K (2003) Assimilating remote sensing data into a land-surface process model. Int J

Remote Sens 24:2959–2980 Stimson HC et al (2005) Spectral sensing of foliar water conditions in two co-occurring conifer

species: Pinus edulis and Juniperus monosperma. Remote Sens Environ 96(1):108–118 Tokekar P et al (2016) Sensor planning for a symbiotic UAV and UGV system for precision

agriculture. IEEE Trans Robot 32(6):1498–1511 Wallace C, Walker J, Skirvin S, Patrick-Birdwell C, Weltzin J, Raichle H (2016) Mapping presence

and predicting phenological status of invasive buffelgrass in southern Arizona using MODIS, climate and citizen science observation data. Remote Sens 8(7):524 Wallach D, Makowski D, Jones JW, Brun F, Jones JW (2014) Working with dynamic crop models.

Academic, Cambridge, MA, pp 407–436 Watanabe K, Guo W, Arai K, Takanashi H, Kajiya-Kanegae H, Kobayashi M, Yano K,

Tokunaga T, Fujiwara T, Tsutsumi N, Iwata H (2017) High-throughput phenotyping of sor- ghum plant height using an unmanned aerial vehicle and its application to genomic prediction modeling. Front Plant Sci 8:421 Zarco-Tejada PJ et al (2001) Scaling-up and model inversion methods with narrowband optical

indices for chlorophyll content estimation in closed forest canopies with hyperspectral data. IEEE Trans Geosci Remote Sens 39(7):1491–1507

2 Precision Agriculture and Unmanned Aerial Vehicles (UAVs) 23

Zarco-Tejada PJ, González-Dugo V, Berni JAJ (2012) Fluorescence, temperature and narrow-band

indices acquired from a UAV platform for water stress detection using a micro-hyperspectral imager and a thermal camera. Remote Sens Environ 117:322–337 Zarco-Tejada PJ et al (2013) Estimating leaf carotenoid content in vineyards using high resolution

hyperspectral imagery acquired from an unmanned aerial vehicle (UAV). Agric For Meteorol 171:281–294 Zhang C, Kovacs JM (2012) The application of small unmanned aerial systems for precision

agriculture: a review. Precis Agric 13(6):693–712
