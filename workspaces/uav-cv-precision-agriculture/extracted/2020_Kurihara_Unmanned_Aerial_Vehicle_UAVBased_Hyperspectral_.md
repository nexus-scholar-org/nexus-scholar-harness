---
workspace_id: SCI-000398
doi: 10.1007/978-3-030-27157-2_3
title: Unmanned Aerial Vehicle (UAV)-Based Hyperspectral Imaging System for Precision
  Agriculture and Forest Management
authors:
- family_name: Kurihara
  given_name: Junichi
  orcid: null
- family_name: Ishida
  given_name: Tetsuro
  orcid: null
- family_name: Takahashi
  given_name: Yukihiro
  orcid: null
year: 2020
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:26:14.024046+00:00'
---

# Unmanned Aerial Vehicle (UAV)-Based Hyperspectral Imaging System for Precision Agriculture and Forest Management

Chapter 3 Unmanned Aerial Vehicle (UAV)-Based Hyperspectral Imaging System for Precision Agriculture and Forest Management

Junichi Kurihara, Tetsuro Ishida, and Yukihiro Takahashi

Abstract Hyperspectral imaging is a powerful tool for remote sensing of vegetation and environment. Although unmanned aerial vehicles (UAVs) are increasingly utilized as a new platform for remote sensing, a conventional push-broom spectrom- eter is not suitable for hyperspectral imaging with commercial-grade UAVs. This paper presents a hyperspectral imaging system equipped with a sequential two-dimensional spectral imager, which is more practical for UAV-based hyperspectral imaging. Liquid crystal tunable ﬁlter technology, which is also used for spaceborne imagers on microsatellites, is applied to the UAV-based hyperspectral imager for wavelength scanning in 460–780 nm. The system has a total weight of 1.5 kg, and it is designed to operate remotely with multirotor UAVs. In this paper, image processing and analysis of the acquired hyperspectral images are also described in detail with examples. This system can be widely used for UAV-based hyperspectral imaging, especially in precision agriculture and forest management.

Keywords UAV · Hyperspectral imaging · Tunable ﬁlter · Precision agriculture · Image analysis

3.1 Introduction

Hyperspectral imaging by airborne/spaceborne sensors can provide detailed information on spectral reﬂectance of the Earth’s surface illuminated by sunlight, and it has been used for a wide variety of remote sensing applications, e.g., land cover and vegetation classiﬁcation (Im and Jensen 2008; Govender et al. 2007), forest diversity assessment (Ghiyamat and Shafri 2010), coastal ocean environment (Ryan et al. 2014), and mineral mapping (van der Meer et al. 2012). The

J. Kurihara (*) · T. Ishida · Y. Takahashi Faculty of Science, Hokkaido University, Sapporo, Japan e-mail: kurihara@sci.hokudai.ac.jp

© Springer Nature Switzerland AG 2020 R. Avtar, T. Watanabe (eds.), Unmanned Aerial Vehicle: Applications in Agriculture and Environment, https://doi.org/10.1007/978-3-030-27157-2_3

25

26 J. Kurihara et al.

hyperspectral imaging sensor equipped conventionally on airborne/spaceborne platforms is a push-broom/line-scanning spectrometer, which records spectral information in a linear ﬁeld of view and scans across the surface with the movement of the platform. The spatial resolution of the push-broom spectrometer is constrained by the altitude and the velocity of the platform, and thus, the typical spatial resolution is ~1 m for manned aircraft and ~30 m for satellites.

Recently, unmanned aerial vehicles (UAVs) are utilized increasingly as a new platform for remote sensing (Pajares 2015). Compared to manned aircraft and satellites, UAVs can offer higher spatial resolution to hyperspectral imaging by low-altitude and low-velocity ﬂights. UAV-based hyperspectral imaging can con- tribute to precision agriculture and forest management that require high spatial resolution remote sensing from leaf to plant scales. Many UAV-compatible hyperspectral sensors have already been commercially available (Adão et al. 2017). Currently, most of the UAV-based hyperspectral sensors are a push-broom spectrometer, which is employed conventionally by the airborne hyperspectral imaging systems. However, a push-broom spectrometer is quite sensitive to the performance of the inertial measurement unit implemented on UAVs, and the use of consumer-grade UAVs for the platform of a push-bloom spectrometer will result in low-quality georeferencing and imaging (Habib et al. 2017). This limitation makes it difﬁcult to utilize a push-broom spectrometer effectively for UAV-based hyperspectral imaging.

Two-dimensional (2D) spectral imagers, which can record 2D images of spectral bands instantaneously, are more practical for UAV-based hyperspectral imaging in terms of quality of georeferencing and imaging. Even with consumer-grade UAVs, the obtained 2D images are georeferenced easily by modern image processing techniques such as feature-based image matching. Aasen et al. (2018) categorized 2D spectral imagers for UAV-based remote sensing systems according to their technologies, e.g., multi-camera 2D imagers, sequential 2D imagers, and snapshot 2D imagers. A multi-camera 2D imager integrates several cameras of different spectral bands into a system. Several vegetation indices and biophysical parameters can be calculated from their spectral bands (Albetis et al. 2017). A sequential 2D imager uses a single camera with a tunable ﬁlter, which can change its spectral bands sequentially. Spectral features can be extracted from a sequence of spectral images after band-to-band registration, and they are investigated mostly using a machine learning technique (Näsi et al. 2018). A snapshot 2D imager can record its spectral bands at the same time. Although it has the great advantage that there is no need to conduct band-to-band registration, the number of pixels is still not enough to cover a large area with a high spatial resolution (Aasen et al. 2015).

Kurihara et al. (2018) applied liquid crystal tunable ﬁlter (LCTF) technology to a sequential 2D imager mounted on the RISING-2 microsatellite, which is a 50-kg platform developed jointly by the Tohoku and Hokkaido universities in Japan (Sakamoto et al. 2016). Following the success of the RISING-2, sequential 2D imagers with the LCTF were also mounted on subsequently launched microsatellites, e.g., the DIWATA-1, DIWATA-2, MicroDragon, and Rapid Inter- national Scientiﬁc Experiment Satellite (RISESAT). The advantage of the LCTF is that no mechanical component is used for the ﬁlter tuning. This allows the LCTF to

3 Unmanned Aerial Vehicle (UAV)-Based Hyperspectral Imaging System for. . . 27

have a compact size for easy installation, a low power consumption for wavelength scanning, and a high tolerance for vibration, shock, and vacuum environment; thus, the LCTF can be applied to a wide range of remote sensing platforms other than satellites. Consequently, a UAV-based hyperspectral imaging system with the LCTF was also developed in Hokkaido University, and it has already been used for various applications, e.g., the classiﬁcation of vegetation in the ﬁeld (Ishida et al. 2018).

This paper presents the speciﬁcations and the operation of the latest UAV-based hyperspectral imaging system that uses the LCTF for a sequential 2D imager. The paper also describes the image processing required to obtain high quality hyperspectral imaging dataset, which is applicable to precision agriculture and forest management.

3.2 UAV-Based Hyperspectral Imaging System

The development of the UAV-based hyperspectral imaging system in Hokkaido University commenced in 2012 as a spin-off product from the spaceborne multi- spectral sensors for microsatellites. The prototype of the system has 6.3 kg in weight including a tablet computer and a battery, and the ﬂight test mounted on a ﬁxed wing UAV was conducted in Indonesia in October 2012. Since then, several types of the UAV-based hyperspectral imaging systems have been developed and tested in some countries such as the Philippines (Ishida et al. 2018), and its practical utility has been improved gradually. In this section, the speciﬁcation and operation of the latest UAV-based hyperspectral imaging system are described in the following subsections.

3.2.1 Speciﬁcations

The UAV-based hyperspectral imaging system consists of a sequential 2D imager, a controller, a computer, a battery, and cables (Fig. 3.1). The sequential 2D imager, which uses the LCTF for wavelength scanning and a monochrome charge-coupled device (CCD) image sensor for imaging, was designed and manufactured by Genesia Corp. (Tokyo, Japan). The LCTF is a type of optical band-pass ﬁlter that is composed of several stacked layers of liquid crystal sandwiched between crossed polarizers, and its transmission wavelength is controlled by square-wave voltages that are applied to each layer. The voltage-controlling circuit, which is connected to the LCTF of the imager, is housed separately in the controller. The approximate size and weight of the LCTF are a cube of side 30 mm and 80 g, respectively. The power consumption of the voltage-controlling circuit is 0.2 W. The central wavelength of the LCTF is electrically selectable at 1-nm intervals from 460 to 780 nm. The peak transmittance and the full width at half maximum increase with the central wave- length from 6% and 6 nm (at 460 nm) to 15% and 23 nm (at 780 nm), respectively.

28 J. Kurihara et al.

Fig. 3.1 Appearance of the UAV-based hyperspectral imaging system

As the LCTF uses the polarizers, a depolarizer is placed in front of the LCTF to scramble the polarization of incoming light. To maintain the LCTF performance over a wide temperature range of 2–38 C, a temperature sensor is attached to the LCTF, and the optimum voltages at the measured temperature are applied automat- ically using a look-up table stored in the voltage-controlling circuit. The response time for switching from one central wavelength to another depends on the temper- ature and on the combination of wavelengths. The exposure of the CCD is designed to start after sufﬁcient time has elapsed for the switching of the wavelengths. The computer to control the imager and the controller is a commercial stick personal computer (PC) Diginnos Stick DG-STK4D (Thirdwave Diginnos Co., Ltd., Tokyo, Japan), which uses the Windows operating system. A dedicated control software for the imager is installed on the stick PC, and it can set parameters for hyperspectral imaging, e.g., wavelengths, exposure time, gain, and number of images to be captured. The stick PC does not have a display and input devices, and it is monitored and controlled remotely from another computer via Wi-Fi during the ﬂight. The captured images are stored on the stick PC and retrieved after the ﬂight. The battery to provide power to the controller and the computer is a lithium-ion polymer battery Energizer XP8000A (XPAL Power Inc., Modesto, CA, USA), which is commer- cially available for mobile devices. Table 3.1 summarizes the speciﬁcations of the UAV-based hyperspectral imaging system.

3.2.2 Operation

Hyperspectral imaging by the sequential 2D imager is enabled by changing spectral bands sequentially. Considering the bandwidth of the LCTF, the central wavelength of the imager is changed typically at 10-nm intervals; thus, a total of 33 spectral bands are acquired sequentially in the wavelength range of 460–780 nm. The exposure time is usually adjusted in the range of 3–15 ms depending on the elevation of the sun and the cloud cover of the sky. The frame rate is normally 1–2 frames/s

3 Unmanned Aerial Vehicle (UAV)-Based Hyperspectral Imaging System for. . . 29


> **Table 3.1 Speciﬁcations of the UAV-based hyperspectral imaging system**

Wavelength range 460–780 nm Minimum wavelength interval 1 nm Bandwidth 6–23 nm (FWHM) Frame rate 1–2 frames/s Number of pixels 656  494 pixel Field of view 90 (diagonal) Operating temperature 2–38 C Components Size Weight Imager 220  90  90 mm 790 g Controller 110  90  35 mm 230 g Computer 123  59  22 mm 95 g Battery 109  74  23 mm 225 g Cables 160 g Total weight 1500 g

because of the response time of the LCTF and the processing time of the image. Accordingly, it takes 25–30 s for the acquisition of an image sequence of the 33 spectral bands. The UAV-based hyperspectral imaging system is suitable for use with multirotor UAVs, which can keep a stationary ﬂight during the image sequence acquisition. Multirotor UAVs can also provide easier control, safer landing, and lower prices, compared to ﬁxed wing UAVs. As the imager has a wide ﬁeld of view of 90

diagonally, it can view an area of 1.6 h  1.2 h on the ground, where h is the ﬂight altitude of the UAV (Fig. 3.2a). In Japan, UAVs in unrestricted areas are required to stay below 150 m above ground level by the Civil Aeronautics Act. Therefore, the maximum area acquired by the imager is 240 m  180 m ¼ 43,200 m2 (i.e., 4.32 ha). In order to cover the wider area, the UAV needs to move horizontally to the adjacent area and then capture the image sequence again. The overlap between the images of adjacent areas requires at least 20% of the image because of the attitude ﬂuctuation of the UAV and the distortion of the image as described later. The effect of the attitude ﬂuctuation can be reduced signiﬁcantly by using a gimbal, which can stabilize a camera on UAVs. As shown in Fig. 3.2b, the system can be mounted on a commercially available gimbal RONIN-MX (DJI, Shenzhen, China), which is compatible with a DJI’s hexacopter UAV Matrice 600 (Fig. 3.2c).

The spatial resolution of the imager is also expressed as a function of the ﬂight altitude. The distance between pixel centers measured on the ground is approxi- mately 2.4  103 h; thus, the spatial resolution is higher than 0.36 m in the area where the ﬂight altitude limit is 150 m. If the attitude ﬂuctuation of the UAV is larger than 2.4  103 rad during the exposure time of the imager, the image blurring will appear in the acquired image. Assuming that the exposure time is 10 ms, the allowable attitude ﬂuctuation is 0.24 rad/s (i.e., 14 deg/s). When the operation of the UAV without a gimbal is carried out in windy conditions, the exposure time needs to be reduced to avoid the image blurring.

30 J. Kurihara et al.

Fig. 3.2 (a) Schematic of the ﬁeld of view of the system and (b) the system mounted on a gimbal RONIN-MX and (c) a UAV Matrice 600

3.3 Hyperspectral Image Processing

Image processing and analysis of the obtained hyperspectral images comprises ﬁve main steps: radiometric calibration, camera calibration, band-to-band registration, conversion to reﬂectance, and further analysis. In this section, the ﬁve main steps are described in detail in the following subsections.

3.3.1 Radiometric Calibration

Sensitivity of an image sensor cannot be completely uniform over the whole image, and hence, each pixel has a slightly different sensitivity. In addition, optical system causes vignetting, which is a reduction of the brightness in an image toward the periphery from the center. Nonuniformity in an image related to these intrinsic factors of the imager can be measured using a uniform light source in a laboratory experiment. Figure 3.3a shows a uniform light source HELIOS USLR-D12L- NMNN (Labsphere, Inc., North Sutton, NH, USA) used for the radiometric calibra- tion. The uniform light source employs an integrating sphere whose inside is coated by a highly diffuse reﬂecting material, Spectralon. The spectral radiance of the integrating sphere is calibrated with equipment and methods traceable to the US National Institute of Standards and Technology.

3 Unmanned Aerial Vehicle (UAV)-Based Hyperspectral Imaging System for. . . 31

Fig. 3.3 (a) Photograph of the radiometric calibration with a uniform light source, (b) the acquired image, and (c) the calibrated image

In the laboratory experiment, digital numbers of the pixels in the hyperspectral images taken by the imager are related to the spectral radiance of the integrating sphere as

L λ ð Þ ¼ Ci λ ð Þ  DNi λ ð Þ  B ð Þ=Texp, ð3:1Þ

where L(λ) is the spectral radiance of the integrating sphere at the wavelength λ, Ci(λ) is the unit conversion coefﬁcient of the ith pixel at the wavelength λ, DNi(λ) is the digital number (i.e., brightness value) of the ith pixel at the wavelength λ, B is the offset of the pixels, and Texp is the exposure time spent on acquisition of the image. By using the unit conversion coefﬁcients derived from Eq. 3.1, digital numbers of the hyperspectral images taken from the UAV can be converted to the spectral radiance as

Li λ ð Þ ¼ Ci λ ð Þ  DNi λ ð Þ  B ð Þ=Texp, ð3:2Þ

where Li(λ) is the spectral radiance of the ith pixel at the wavelength λ. Figure 3.3b shows the image of the inside of the integrating sphere taken by the imager at 600 nm, and Fig. 3.3c shows the image calibrated by the measured unit conversion coefﬁcients. As can be seen, nonuniformity in the original image, whose brightness is lower in the periphery than in the center, is indistinctive in the calibrated image. As the unit conversion coefﬁcients vary slightly from one imager to another, the nonuniformity measurement for the radiometric calibration is necessary for all the imagers at least once.

32 J. Kurihara et al.

3.3.2 Camera Calibration

The wide ﬁeld of view of the imager causes signiﬁcant barrel distortion of the image. Removing the distortion is necessary for subsequent image registration. Although there are many methods to remove distortion from an image, camera calibration algorithms implemented in an open-source library, OpenCV (http://opencv.org/), were used in this study. This camera calibration is conducted by taking images of a calibration object from various angles and obtaining geometric relationship between the points on the object and the pixels in the acquired image. A black-white chessboard pattern was used for the calibration object, and the corners of squares on the chessboard pattern were detected automatically as reference points. As the size of the chessboard pattern should be large enough to cover the wide ﬁeld of view of the imager, the chessboard pattern was shown on a large screen display instead of instead of being printed on a paper (Fig. 3.4a). After the camera calibration, the barrel distortion of the chessboard pattern in the original image (Fig. 3.4b) is removed entirely in the calibrated image (Fig. 3.4c). The corners of the original image are changed to acute angles and extended to the outside of the calibrated image frame, and thus, the ﬁeld of view of the calibrated mage is reduced by approximately 10% from the original.

3.3.3 Band-to-Band Registration

The acquired images deviate from one another spatially due to attitude ﬂuctuations of the UAV during the sequential image acquisition. Therefore, band-to-band registration using the feature-based matching approach is applied to a sequence

Fig. 3.4 (a) Photograph of the camera calibration with a displayed chessboard, (b) the acquired image, and (c) the calibrated image

3 Unmanned Aerial Vehicle (UAV)-Based Hyperspectral Imaging System for. . . 33

Fig. 3.5 Result of the feature matching between the images at 690 nm (left) and 700 nm (right)

of the images prior to the further image processing. Although many feature-based matching algorithms are also available in the OpenCV library, Accelerated-KAZE (A-KAZE) feature detection and description method (Alcantarilla et al. 2013) is used in this study.

In the previous study, the scale-invariant feature transform (SIFT) method (Lowe 2004), which is recognized as one of the most precise methods of feature matching, was employed. However, as the result of a comparison of the two methods, the performance of A-KAZE is at least ten times faster in computing and similar in precision compared to that of SIFT. In addition, the SIFT algorithm is patented, and a license is required for the commercial application of the algorithm.

As an example of the band-to-band registration, Fig. 3.5 shows a result of the feature matching between the spectrally sequential images at 690 nm and 700 nm. The matched feature points, which are connected and highlighted by colored lines in Fig. 3.5, can provide a homography matrix that describes a transformation from the coordinate system of the image at 690 nm to that at 700 nm. The homography matrixes are obtained for all the sequential images in the same manner, and ﬁnally, all the images are transformed into the coordinate system of the one image.

The band-to-band registration allows production of a hyperspectral cube, which is the three-dimensional dataset of hyperspectral images. In this step, the hyperspectral cube is still a radiance-based, and it is converted to a reﬂectance- based in the next step.

3.3.4 Conversion to Reﬂectance

In the ﬁeld of remote sensing, hyperspectral images are analyzed generally based on the spectral reﬂectance, because the spectral radiance depends on time-varying spectral irradiance by sunlight. In addition, UAV-based hyperspectral imaging is available under cloudy condition, in which the spectral irradiance changes locally and temporarily. However, simultaneous measurement of the spectral radiance and the spectral irradiance requires an additional spectrometer.

34 J. Kurihara et al.

If there is an object of known spectral reﬂectance in an image, it can be used as a reference for the other objects. Hence, a reﬂectance standard panel is used for the reference of spectral reﬂectance. Spectral reﬂectance of an object on the ground is deﬁned by

R λ ð Þ ¼ πL λ ð Þ=E λ ð Þ, ð3:3Þ

where R(λ) is the spectral reﬂectance of the object at the wavelength λ, L(λ) is the spectral radiance of the object measured by the imager at the wavelength λ, and E(λ) is the spectral irradiance of the object at the wavelength λ. If the reﬂectance standard panel is measured simultaneously by the imager, its spectral reﬂectance is

Rs λ ð Þ ¼ πLs λ ð Þ=E λ ð Þ, ð3:4Þ

where Rs(λ) and Ls(λ) are the spectral reﬂectance and the spectral radiance, respec- tively, of the reﬂectance standard panel at the wavelength λ. Accordingly, the spectral reﬂectance of the object becomes independent of the spectral irradiance as

R λ ð Þ ¼ Rs λ ð Þ L λ ð Þ=Ls λ ð Þ: ð3:5Þ

By means of this equation, the radiance-based hyperspectral cube is converted to reﬂectance-based hyperspectral cube.

Although the reﬂectance standard panel is commercially available, the product that is large enough to be measured by the imager from the ﬂight altitude of the UAV is expensive and heavy. In this study, an ethylene-vinyl acetate (EVA) foam sheet, which is marketed globally as an EVA joint mat, is adopted as a substitute for the reﬂectance standard panel. The advantages of the EVA mat are that it is cheap, light, and easy to spread out by jointing. Figure 3.6 shows spectral reﬂectance of two types

Fig. 3.6 (a) Spectral reﬂectance of the EVA mats for (b) and (c)

3 Unmanned Aerial Vehicle (UAV)-Based Hyperspectral Imaging System for. . . 35

of the EVA mat measured by a portable spectroradiometer ASD FieldSpec 4 (Ana- lytical Spectral Devices, Inc., Longmont, CO, USA). While the two EVA mats have quite different reﬂectance, their spectra are smooth enough to be used for the reference in the wavelength range of the imager.

3.3.5 Further Analysis

Further analysis of the hyperspectral cube varies with individual applications of UAV-based hyperspectral imaging. Nevertheless, there are essential information required commonly for many applications. For example, a color image is quite useful for the georeferencing of a hyperspectral image. In fact, many UAV-based hyperspectral imaging systems are equipped with a red-green-blue (RGB) camera only for that purpose (Aasen et al. 2018). Figure 3.7a shows a true color composite image produced from the hyperspectral cube. The spectral reﬂectance at 460–500 nm, 510–590 nm, and 600–690 nm is averaged and then assigned to the blue, green, and red channels, respectively, of the color composite image. Even though an additional weight is not given to its channels, the composite image has well-balanced natural colors. This composite image production allows the UAV-based hyperspectral imaging system to remove another RGB camera.

Another example is the normalized difference vegetation index (NDVI) image. The NDVI is widely used in multispectral remote sensing, and it is derived from the expression,

NDVI ¼ ρNIR  ρRED ð Þ= ρNIR þ ρRED ð Þ, ð3:6Þ

where ρRED and ρNIR are the reﬂectance of red and near-infrared (NIR) bands, respectively. The NDVI is useful not only for qualitative and quantitative analysis of vegetation in multispectral imaging but also for extraction of vegetation in preprocessing of hyperspectral imaging. Figure 3.7b shows the NDVI image pro- duced from the same hyperspectral cube with Fig. 3.7a by assigning the spectral

Fig 3.7 (a) A true color composite image and (b) the NDVI image

36 J. Kurihara et al.

Fig. 3.8 (a) Superpixel segmentation of the image and (b) the spectral reﬂectance of typical objects

reﬂectance of 680 and 770 nm to ρRED and ρNIR, respectively, in Eq. 3.6. As seen in Fig. 3.7b, vegetation is obviously distinguishable from other objects such as soil, according to the value of the NDVI. Note that the vegetation in the image includes trees and weeds without any distinction.

In precision agriculture and forest management, hyperspectral imaging is applied typically to classiﬁcation of vegetation. As hyperspectral imaging from manned aircraft and satellites presents relatively low spatial resolution images, different species of vegetation and other objects are mixed with each other in a single pixel of the acquired image. Thus, hyperspectral unmixing techniques are frequently required for the classiﬁcation (Bioucas-Dias et al. 2012). On the other hand, UAV-based hyperspectral imaging can provide higher spatial resolution, and objects in the acquired image are separated clearly from each other except for their boundary pixels. Therefore, object-based classiﬁcation is a more effective approach to UAV-based hyperspectral image analysis than pixel-based classiﬁcation (Cao et al. 2018). Image segmentation, in which neighboring pixels are grouped into objects based on their spectral information, is the ﬁrst process of object-based classiﬁcation. Figure 3.8a shows an example of the image segmentation using the Simple Linear Iterative Clustering (SLIC) superpixel segmentation algorithm (Achanta et al. 2012) implemented in OpenCV. The SLIC is a simple and fast algorithm that adapts a k-means clustering approach to generate superpixels efﬁciently. According to their colors, neighboring pixels in the color image (Fig. 3.7a) are grouped into superpixels, which are divided by the white boundaries in Fig. 3.8a. The spectral reﬂectance is averaged over each superpixel (Fig. 3.8b), and they can be investigated further by using machine learning techniques.

3.4 Conclusions

UAV-based hyperspectral imaging is an emerging technology that evolves rapidly in response to the recent development of UAV and remote sensing technologies. Although future applications of UAV-based hyperspectral imaging in precision

3 Unmanned Aerial Vehicle (UAV)-Based Hyperspectral Imaging System for. . . 37

agriculture and forest management are promising, the current technologies are still under the validation phase prior to the practical use. Regarding the use of consumer- grade UAVs, a sequential 2D imager has the advantage in quality of georeferencing and imaging over a push-bloom spectrometer. In this paper, the UAV-based hyperspectral imaging system using the sequential 2D imager is described in detail. The system employs the LCTF for wavelength scanning of the sequential 2D imager, and the speciﬁcations of the system are optimized to mount on multirotor UAVs. The operation of the system can be adapted ﬂexibly to the requirements of coverage and spatial resolution and the conditions of cloud and wind.

The high-quality dataset of UAV-based hyperspectral imaging is also required for the practical applications in precision agriculture and forest management. Image processing and analysis of hyperspectral images can be performed readily by open- source libraries and commercial software now. In this paper, the ﬁve steps of image processing of the acquired hyperspectral images are also described. The precise radiometric calibration and camera calibration are conducted to improve the quality of the acquired images based on the laboratory measurements. The accurate band-to- band registration and conversion to reﬂectance are important to produce the reﬂectance-based hyperspectral cube. Finally, some common processes prior to the further analysis are introduced with the examples. Although the real-time onboard processing is almost impossible for the UAV-based hyperspectral imaging system because of the huge amount of data, the processing time can be reduced signiﬁcantly by the automated and pipelined image processing.


## References

Aasen H, Burkart A, Bolten A, Bareth G (2015) Generating 3d hyperspectral information with

lightweight UAV snapshot cameras for vegetation monitoring: from camera calibration to quality assurance. ISPRS J Photogramm Remote Sens 108:245–259. https://doi.org/10.1016/j. isprsjprs.2015.08.002 Aasen H, Honkavaara E, Lucieer A, Zarco-Tejada PJ (2018) Quantitative remote sensing at ultra-

high resolution with UAV spectroscopy: a review of sensor technology, measurement pro- cedures, and data correction workﬂows. Remote Sens 10:1091. https://doi.org/10.3390/ rs10071091 Achanta R, Shaji A, Smith K, Lucchi A, Fua P, Süsstrunk S (2012) SLIC superpixels compared to

state-of-the-art superpixel methods. IEEE Trans Pattern Anal Mach Intell 34:2274–2281. https://doi.org/10.1109/TPAMI.2012.120 Adão T, Hruška J, Pádua L, Bessa J, Peres E, Morais R, Sousa J (2017) Hyperspectral imaging: a

review on UAV-based sensors, data processing and applications for agriculture and forestry. Remote Sens 9:1110. https://doi.org/10.3390/rs9111110 Albetis J, Duthoit S, Guttler F, Jacquin A, Goulard M, Poilvé H, Féret J-B, Dedieu G (2017)

Detection of Flavescence dorée grapevine disease using unmanned aerial vehicle (UAV) multispectral imagery. Remote Sens 9:308. https://doi.org/10.3390/rs9040308 Alcantarilla PF, Nuevo J, Bartoli A (2013) Fast explicit diffusion for accelerated features in

nonlinear scale spaces. Trans Pattern Anal Mach Intell 34:1281–1298. https://doi.org/10. 5244/C.27.13

38 J. Kurihara et al.

Bioucas-Dias J, Plaza A, Dobigeon N, Parente M, Du Q, Gader P, Chanussot J (2012)

Hyperspectral unmixing overview: geometrical, statistical, and sparse regression-based approaches. IEEE J Sel Top Appl Earth Obs Remote Sens 5:354–379. https://doi.org/10. 1109/JSTARS.2012.2194696 Cao J, Leng W, Liu K, Liu L, He Z, Zhu Y (2018) Object-based mangrove species classiﬁcation

using unmanned aerial vehicle hyperspectral images and digital surface models. Remote Sens 10:89. https://doi.org/10.3390/rs10010089 Ghiyamat A, Shafri H (2010) A review on hyperspectral remote sensing for homogeneous and

heterogeneous forest biodiversity assessment. Int J Remote Sens 31:1837–1856. https://doi.org/ 10.1080/01431160902926681 Govender M, Chetty K, Bulcock H (2007) A review of hyperspectral remote sensing and its

application in vegetation and water resource studies. Water SA 33:145–152. https://doi.org/ 10.4314/wsa.v33i2.49049 Habib A, Xiong W, He F, Yang HL, Crawford M (2017) Improving orthorectiﬁcation of

UAV-based push-broom scanner imagery using derived orthophotos from frame cameras. IEEE J Sel Top Appl Earth Obs Remote Sens 10:262–276. https://doi.org/10.1109/JSTARS. 2016.2520929 Im J, Jensen J (2008) Hyperspectral remote sensing of vegetation. Geogr Compass 2:1943–1961.

https://doi.org/10.1111/j.1749-8198.2008.00182.x Ishida T, Kurihara J, Viray FA, Namuco SB, Paringit EC, Perez GJ, Takahashi Y, Marciano JJ Jr

(2018) A novel approach for vegetation classiﬁcation using UAV-based hyperspectral imaging. Comput Electron Agric 144:80–85. https://doi.org/10.1016/j.compag.2017.11.027 Kurihara J, Takahashi Y, Sakamoto Y, Kuwahara T, Yoshida K (2018) HPT: a high spatial

resolution multispectral sensor for microsatellite remote sensing. Sensors 18:619. https://doi. org/10.3390/s18020619 Lowe DG (2004) Distinctive image features from scale-invariant keypoints. Int J Comput Vis

60:91–110. https://doi.org/10.1023/B:VISI.0000029664.99615.94 Näsi R, Viljanen N, Kaivosoja J, Alhonoja K, Hakala T, Markelin L, Honkavaara E (2018)

Estimating biomass and nitrogen amount of barley and grass using UAV and aircraft based spectral and photogrammetric 3D features. Remote Sens 10:1082. https://doi.org/10.3390/ rs10071082 Pajares G (2015) Overview and current status of remote sensing applications based on unmanned

aerial vehicles (UAVs). Photogramm Eng Remote Sens 81:281–330. https://doi.org/10.14358/ PERS.81.4.281 Ryan JP, Davis CO, Tuﬁllaro NB, Kudela RM, Gao B-C (2014) Application of the Hyperspectral

imager for the Coastal Ocean to phytoplankton ecology studies in Monterey Bay, CA, USA. Remote Sens 6:1007–1025. https://doi.org/10.3390/rs6021007 Sakamoto Y, Sugimura N, Fukuda K, Kuwahara T, Yoshida K, Kurihara J, Fukuhara T, Takahashi

Y (2016) Development and ﬂight results of microsatellite bus system for RISING-2. Trans JSASS Aerosp Technol Jpn 14:Pf_89–Pf_96. https://doi.org/10.2322/tastj.14.Pf_89 van der Meer FD, van der Werff HM, van Ruitenbeek FJ, Hecker CA, Bakker WH, Noomen MF,

van der Meijde M, Carranza EJM, de Smeth JB, Woldai T (2012) Multi- and hyperspectral geologic remote sensing: a review. Int J Appl Earth Obs Geoinf 14:112–128. https://doi.org/10. 1016/j.jag.2011.08.002
