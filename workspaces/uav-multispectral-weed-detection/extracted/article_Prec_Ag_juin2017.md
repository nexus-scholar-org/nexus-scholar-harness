---
title: "article_Prec_Ag_juin2017"
doi: "10.1007/s11119-017-9528-3"
extraction_engine: pymupdf
---

Weed detection by UAV: simulation of the impact
of spectral mixing in multispectral images
M. Louargant1,2
• S. Villette1 • G. Jones1 • N. Vigneau2 •
J. N. Paoli1 • C. Ge´e1
 Springer Science+Business Media New York 2017
Abstract This study aimed to assess the spectral information potential of images captured
with an unmanned aerial vehicle, in the context of crop–weed discrimination. A model is
proposed in which the entire image acquisition chain is simulated in order to compute the
digital values of image pixels according to several parameters (light, plant characteristics,
optical ﬁlters, sensors…) to reproduce in-ﬁeld acquisition conditions. The spectral mixings
in the pixels are modeled, based on an image with a 60 mm spatial resolution, to estimate
the impact of the resolution on the ability to discriminate small plants. The classiﬁcation
potential (i.e. the ability to separate two classes) in soil and vegetation and in mono-
cotyledon and dicotyledon classes is studied using simulations for different vegetation rates
(deﬁned as the proportion of vegetation covering the surface projected in the considered
pixel). The classiﬁcation is unsupervised and based on the Mahalanobis distance compu-
tation. The results of soil-vegetation discrimination show that pixels with low vegetation
rates can be classiﬁed as vegetation: pixels with vegetation rate greater than 0.5 had a
probability to be correctly classiﬁed between 80 and 100%. Classiﬁcation between
monocotyledonous and dicotyledonous plants requires pixels with a high vegetation rate: to
obtain a probability to be correctly classiﬁed better than 80%, vegetation rates in the pixels
have to be over 0.9. To compare the results with data from real images, the same classi-
ﬁcation was tested on multispectral images of a weed infested ﬁeld. The comparison
conﬁrmed the ability of the model to assess vegetation–soil and crop–weed discrimination
potential for speciﬁc sensors (such as the multiSPEC 4C sensor, AIRINOV, Paris, France),
where the acquisition chain parameters can be tested.
Electronic supplementary material The online version of this article (doi:10.1007/s11119-017-9528-3)
contains supplementary material, which is available to authorized users.
& M. Louargant
christelle.gee@agrosupdijon.fr
1
Agroe´cologie, AgroSup Dijon, INRA, Univ. Bourgogne Franche-Comte´, 26 bd Docteur Petitjean,
21079 Dijon Cedex, France
2
AIRINOV SAS, 157 Boulevard Macdonald, 75019 Paris, France
123
Precision Agric
DOI 10.1007/s11119-017-9528-3


Keywords Modeling  Acquisition chain model  Multispectral image 
Weed classiﬁcation
Glossary
In this study different images were used. In this paper these images are mentioned as
follows:
Pole-MS-6 mm
Multispectral image captured with the pole
Pole-MS-6 mm
Multispectral image captured with the pole and degraded to a
60 mm spatial resolution
UAV-MS-60 mm
Multispectral image captured with the UAV ﬂying at 50 m height
Veg-rate-6 mm
Image presenting an estimation of the vegetation rates in the
pixels of the Pole-MS-6 mm image
Veg-rate-60 mm
Image presenting an estimation of the vegetation rates in the
pixels of the Pole-MS-60 mm image
Sim-unmixed-60 mm
Simulated image without mixed pixels for a spatial resolution of
60 mm
Sim-mixed-60 mm
Simulated image with mixed pixels for a spatial resolution of
60 mm
Introduction
More and more farmers apply the principles of precision agriculture to improve crop yield
and quality and to limit impact on the environment. The concept of precision agriculture is
particularly applicable to weed management, since weed distribution is heterogeneous in
the ﬁeld (Clay et al. 1999; Thornton et al. 1990). For example, mapping weed patches
would allow precision spraying, in which weed-free areas would not be sprayed, saving
herbicide and thus limiting input costs and losses in the environment (Gerhards et al. 2002;
Martı´n et al. 2016; Nordmeyer 2006; Stafford and Miller 1993).
In recent decades, numerous studies have addressed the problem of weed detection.
Most of these studies investigated spectral data for species discrimination by capturing
reﬂectance spectra from plants. Gausman (1985) noted a difference between mono-
cotyledonous and dicotyledonous plants in the infrared region, due to their leaf structure.
Feyaerts and van Gool (2001) used an imaging spectrograph to collect reﬂectance spectra
in ﬁeld conditions. Means and variances of the reﬂectance values of each wavelength were
compared to select those most appropriate for crop/weed discrimination. Moreover, several
classiﬁers were compared for the discrimination, such as minimal distance, k-nearest
neighbor or neural network classiﬁers. Vrindts et al. (2002) and Girma et al. (2005)
analyzed crop (sugar beet, maize and wheat) and weed reﬂectance spectra, as captured with
a spectroradiometer in laboratory conditions, to perform discriminant analyses. They
selected wavelengths appropriate for crop/weed discrimination and corresponding dis-
criminant models. Similar experiments have been conducted in ﬁeld conditions (Brown
et al. 1994; Hadoux et al. 2012; Lopez-Granados et al. 2008; Shapira et al. 2013). Lopez-
Granados et al. (2008) compared the classiﬁcation results obtained with discriminant
Precision Agric
123


analysis to those deduced from neural networks. Hadoux et al. (2012) added spatial
information to spectral data by capturing hyperspectral images with an imaging spectro-
graph. According to all these studies, different crops (sugar beet, maize or wheat) can be
discriminated from weed species by considering reﬂectance spectra.
Recent technologies have opened up a whole new perspective in in-ﬁeld data acquisition
using new aerial platforms known as unmanned aerial vehicle (UAV) (Zhang and Kovacs
2012). The advantages of UAVs compared with aircraft or satellites were highlighted by
Rango et al. (2009). UAVs can cover a large area in a short time while providing high
spatial resolution (up to 10 mm/pixel), which allows detection of small objects such as
weeds (Rasmussen et al. 2013). Due to weight constraints, UAVs use light-weight sensors
and especially four- to six-band multispectral cameras to take images in the visible and the
near infra-red (NIR). The main discrimination methods applied to images captured by
UAV are based on spatial algorithms and classiﬁcation tools. The spatial methods consider
the geometrical characteristics of the seedling. They are often based on row detection and
assume the weeds to be the vegetation between rows (Bossu et al. 2009; Jones et al. 2009;
Pen˜a et al. 2013; Vioix et al. 2003). The spectral methods use classiﬁcation and seg-
mentation tools to classify the image pixels according to their reﬂectance values (De Castro
et al. 2012; Garcia-Ruiz et al. 2015; Pe´rez-Ortiz et al. 2015).
At the present time, few of the developed spectral methods provide robust crop–weed
discrimination. Indeed, results obtained from spectral data acquired in a laboratory are
hardly reproducible in ﬁeld conditions, since numerous acquisition parameters affect
reﬂectance values. The results provided by both spatial and spectral methods are inﬂuenced
by the characteristics of the acquisition system. These characteristics impact the quality of
the signal recorded by the sensor and thus the classiﬁcation potential of the pixels as soil,
crop or weed. For example, different spatial resolutions cause subsequent spectral mixings,
depending on the size of each element in the scene. However, to the author’s knowledge,
the relationship between acquisition characteristics and weed detection potential has not
been clearly assessed. In this paper, the detection potential or the classiﬁcation potential
deﬁnes the ability for an algorithm to classify correctly a pixel as crop or weed. This
potential corresponds to the probability of correctly classifying a pixel. Some studies have
examined the relationship between the size of the object to be detected and the spatial
resolution. For example, based on Shannon’s sampling theory (Shannon 1949) for signal
processing, McBratney et al. (2003) suggested a resolution of at least 2 9 2 pixels in the
area of the smallest object that can be detected. However, no study has speciﬁcally
addressed the problem of plant detection by studying how spectral mixing due to image
resolution affects the potential of plant detection. Borra-Serrano et al. (2015), Mesas-
Carrascosa et al. (2015) and Pen˜a et al. (2015) compared different ﬂight heights in terms of
the ability to detect weeds with a UAV. The best weed detection was obtained on images
with the highest spatial resolution. For example, Pen˜a et al. (2015) correctly detected 91%
of weeds on images (of an infested sunﬂower ﬁeld) with a spatial resolution of 21.6 mm/
pixel but only 50% on images with a spatial resolution of 54.1 mm/pixel. But the direct
link between the size of the plant to be detected and image spatial resolution is not well
documented. Identifying this link is, however, important to assess small weed detection
possibilities. This is of particular interest in cases where herbicides are applied at early
phenological stages since missing these small weeds could signiﬁcantly affect crop pro-
duction. Moreover the cost of image acquisition increases with resolution, which is why
the link between spatial resolution and detectable weed size must be identiﬁed to propose
an affordable and reliable service to farmers.
Precision Agric
123


This study aimed to develop a model of the acquisition chain, transforming reﬂectance
spectra into modeled pixels to assess the weed detection potential according to different
parameters. By varying different acquisition parameters in the model, their impact on crop/
weed discrimination potential can be determined. This paper focuses on the impact of
spectral mixings, directly linked to spatial resolution, on weed detection potential. Using
that kind of model would allow the decision maker to choose the best parameters in the
acquisition chain (e.g. the spatial resolution) to ensure maximal discrimination between
crops and weeds (according to their sizes).
Materials and methods
To assess the impact of different parameters of the acquisition chain on the spectral quality
of the pixels and on crop/weed discrimination potential, a model of this acquisition chain
was developed. Two types of acquisition were used (cf. Fig. 1): a ﬁrst one, to create a
spectral database to feed the model, and a second one to compare the data obtained from
the simulation to real-life data. For the ﬁrst acquisition, plant and soil reﬂectance spectra
were acquired in laboratory conditions. These spectra were transformed into modeled
pixels by simulating the acquisition chain and spectral mixings. The modeled pixels were
then classiﬁed using a method based on the Mahalanobis distance (Mahalanobis 1936). The
results were compared to real-life data. Thus, multispectral images were captured at high
resolution (6 mm) to obtain a ground truth image, and then degraded to a lower resolution
(60 mm). The same classiﬁcation was implemented on these images.
Classification
Acquisition 
chain model
Image degradation
Mixing rates estimation
Classification
Results comparison
Laboratory 
reflectance spectra 
(plant + soil)
In-field 
multispectral 
image
Mixed pixels
Modeled 
mixed pixels
Fig. 1 Discrimination potential
assessment process. In the left
column, reﬂectance spectra are
used to feed the acquisition chain
model and create modeled pixels.
In the right column, multispectral
images are used to estimate
vegetation rates in real images at
different spatial resolution.
Modeled pixels and real image
pixels are then classiﬁed into soil
or vegetation and into crop or
weed and results are compared
Precision Agric
123


Study area
Two types of acquisition were implemented in the experiments: reﬂectance spectra, which
were acquired in laboratory conditions, and multispectral images acquired in the ﬁeld.
Reﬂectance spectra acquisitions were performed on dicotyledonous and monocotyle-
donous plants at different growth stages (cf. Table 1) and on the soil in which these plants
were growing. Weeds ready to germinate were sown in pots ﬁlled with clay-loam soil, a
soil type commonly encountered in Burgundy, France, the region of experimentation. The
pots were placed outdoors, to assure real-life conditions during plant growth and were
carried into the laboratory at the moment of the spectral acquisition. The acquisitions were
performed during phenological stages selected to correspond to spraying periods. They are
expressed in terms of the ‘‘Biologische Bundesanstalt, Bundessortenamt und CHemische
industrie’’ (BBCH) scale (Meier 2001). Table 1 presents the database of spectra created for
the simulations.
Multispectral images were acquired with a UAV and with a pole on 15th April 2015
from a commercial ﬁeld of 20 ha infested with lamb’s quarters (Chenopodium album) and
thistle (Cirsium arvense), two dicotyledonous plants (cf. Table 2). The crop in the ﬁeld was
maize (Zea mays), a monocotyledon. A study area of 25 m2 presenting both crop and
weeds was delimited by positioning a target at each corner. These targets were speciﬁcally
designed by AIRINOV, Paris, France, to be visible on the multispectral images captured
with the UAV. Soil color was homogenous in the area.
Data acquisition
Reﬂectance spectrum acquisition
To feed the simulation, a database of plant and soil reﬂectance spectra was created.
Spectral acquisitions were effected on the plants grown in pots, as described in Table 1.
Reﬂectance spectra were acquired in the laboratory with an ASD FieldSpec 3
Table 2 Species growing in the studied ﬁeld
Species
Plant type
BBCH stages
Density (number of plants/m2)
Lamb’s quarters (Chenopodium album)
Dicotyledon
10–16
48
Thistle (Cirsium arvense)
Dicotyledon
12–20
26
Maize (Zea mays)
Monocotyledon
12–14
17
Table 1 Database of spectra acquired with the spectrometer
Species
Plant type
BBCH stages
Number of spectra
Maize (Zea mays)
Monocotyledon
12–13
47
Sunﬂower (Helianthus annuus)
Dicotyledon
12–16
84
Rape (Brassica napus)
Dicotyledon
12–16
94
Sugar beet (Beta vulgaris)
Dicotyledon
12–16
85
Soil
286
Precision Agric
123


spectrometer (ASDInc., Boulder, Colorado, USA), equipped with 3 sensors for three dif-
ferent spectral ranges. Spectral ranges, spectral resolutions and sampling intervals are
described in Table 3.
The spectra were acquired in laboratory conditions, using a contact probe including an
internal light source and a ﬁber-optic input connected to the spectrometer. The light source
was stable and controlled. The probe was placed against the leaves or the soil. The contact
zone of this probe was a disk of 30 mm diameter, which was too large for the leaves of
small plants. Indeed, no spectrometers are available to capture the reﬂectance spectra of
very small plants. Consequently, the spectra in this work were acquired on plants with
leaves wider than 30 mm, as presented in Table 2. In these conditions, spectra could not be
captured on narrower weeds. The sunﬂower, rape and sugar beet spectra were thus used in
the model to simulate dicotyledonous weed pixels.
Aerial acquisition system and image acquisition protocol
The aerial acquisition system was composed of a UAV, a multispectral camera and a light
meter. The UAV used was an eBee (senseFly, Lausanne, Switzerland) with a wingspan of
one meter and automatic ﬂight capability. The UAV included GPS location and could ﬂy
from 50 to 150 m height according to the French regulations. The multispectral camera
was a multiSPEC 4C (AIRINOV, Paris, France) composed of four complementary metal
oxide semiconductor (CMOS) sensors, each one equipped with a different optical ﬁlter.
Bandwidths were centered in the green (550, 40 nm wide), red (660, 40 nm wide), red edge
zone (735, 10 nm wide) and near infra-red (790, 40 nm wide). The transmittance curve of
each optical ﬁlter is plotted in Fig. 2. CMOS sensors capture the luminous ﬂux with a
sensitivity that varies according to the wavelength radiation (Fig. 2). The sensitivity is the
ratio between the input signal and the output signal of the sensor.
Table 3 Spectral characteristics of the spectrometer sensors
Sensor
Spectral range (nm)
Spectral resolution (nm)
Sampling interval (nm)
Visible and near infra-red
350–1050
3
1.4
Short-wave infra-red 1
1000–1800
10
2
Short-wave infra-red 2
1800–2500
10
2
Fig. 2 Transmittance of the ﬁlters (left) and sensitivity curve of the sensors (right)
Precision Agric
123


This system captured multispectral images in the weed infested ﬁeld (cf. Table 2). Two
acquisition conditions were performed: one with the UAV ﬂying at a height of 50 m, and
one with the acquisition system ﬁxed to a pole 3 m above the ground. The images were
stored in lossless compression format (tagged image ﬁle format (TIFF) with Lempel–Ziv–
Welch (LVZ) compression) in order to lose no information on the images.
In order to correct the values relative to lighting conditions, reﬂectance must be computed.
Reﬂectance is the ratio between the luminous ﬂux reﬂected by the object and the incident
luminous ﬂux on this object. To compute this ratio, the incident luminous ﬂux was determined
at the beginning of each acquisition, by measuring the luminous ﬂux from a reﬂectance
reference surface. This surface, designed by AIRINOV (Paris, France) is lambertian and its
reﬂectance spectrum is known. In addition, the sensor measures the incident radiation vari-
ations during the acquisition thanks to its embedded light meter, providing a reﬂectance
correction factor. This correction factor is registered for each image, and then used to correct
the reﬂectance from the light variations that occurred during the acquisition.
The UAV ﬂew at 50 m height in parallel lines to obtain an overlap of 80% between
successive images. The resulting images had a spatial resolution of 60 mm. After the ﬂight,
an ortho-image was created using algorithms developed by AIRINOV and described in
Verger et al. (2014). The resulting images are called UAV-MS-60 mm.
To capture 6 mm spatial resolution images, the UAV equipped with the multispectral
camera was ﬁxed on a 3 m high pole to manually scan the study area. The area was
covered by foot in parallel lines so as to ensure the same overlap between images as in the
aerial acquisition. These images were corrected for light variations and for distortions
before being gathered into one ortho-image (Verger et al. 2014). These Pole-MS-6 mm
images were used as a ground truth, to identify weeds, crop and soil. Moreover, these high
spatial resolution images were also degraded to obtain a new image with a spatial reso-
lution of 60 mm (i.e. the spatial resolution obtained with the UAV ﬂying at 50 m height):
the Pole-MS-60 mm images.
For ground-truth data collection, all the plants (crop and weeds) in the study area were
identiﬁed and located manually by a ﬁeld survey. They were then marked on the Pole-MS-
6 mm ortho-image, resulting in a ground truth image (Fig. 3). To this end, each plant was
outlined in a shapeﬁle on QGIS software (Open Source Geospatial Foundation), and was
1 m
Fig. 3 Ground truth image: example of the NIR image extracted from the Pole-MS-6 mm ortho-image
(left) and manual species identiﬁcation image (right) on the study area of a weed infested maize ﬁeld
Precision Agric
123


identiﬁed as crops (monocotyledons) and weeds (dicotyledons). All other areas were
classiﬁed as soil. The shapeﬁle was then converted into a raster with the same spatial
resolution as the Pole-MS-6 mm image (i.e. 6 mm).
In addition, the vegetation rate in each pixel was estimated from the ground truth image.
The vegetation rate is deﬁned as the proportion of vegetation that covers the surface of the
ground projected in a pixel. On the new Veg-rate-6 mm image, the pixels corresponding to
soil were set at 0% vegetation rate. For vegetation pixels, the multispectral images pre-
sented a gradient in pixel values from the plant edges toward the center, due to an increase
in vegetation rates toward the plant centers. This gradient was set arbitrarily at 25, 50 and
75% vegetation rate on the three ﬁrst pixels on the plant edges. The pixels in the plant
center were set at 100% vegetation rate.
Acquisition chain modeling: from spectra to mixed pixels
The model (Fig. 4) aims to transform reﬂectance spectra, acquired in laboratory conditions, to
pixel values, as acquired in ﬁeld conditions by means of the UAV optical system. In this model,
aﬁeldsurfacepresentingseveral objects(crop, weed, soil)isprojectedinonepixel.Thespectral
reﬂectance of these objects is transformed into a pixel with four values (one for each ﬁlter).
Different parameterscan affectthe value of the output pixels(illuminant,sensor characteristics,
objects in the scene, etc.). By varying these parameters, their impact on crop–weed discrimi-
nationcanbestudied.Thispaperfocusesonone parameter: spectralmixing, affectedbythe size
of the objects in the scene with respect to the spatial resolution of the images.
Reﬂected luminous ﬂux
Image acquisition is performed outside, where the light source is the sun. Bird and Riordan
(1984) detailed different models of illuminant for the sun at sea level, in various conditions.
The illuminant spectrum extracted from the ASTM G173 reference spectra (ASTM 2012) is
used for the acquisition chain model. It represents the light coming from the sun after passing
through the atmosphere in mid-April, mid-day, at sea level, at a latitude of 48. These are the
conditions which correspond to those prevailing during spraying periods.
A part of this incident light is reﬂected by the object. This part was deducted from the
reﬂectance spectra of soils and plants, as measured in the laboratory:
xreflected ki
ð Þ ¼ R ki
ð Þ  xincident ki
ð Þ
ð1Þ
Simulated 
light 
Sensor 
characteristics
4 filters
+
Sensitivity
Spectrum 
reflected by the 
white reference
Multispectral 
values of the 
object
Multispectral
values of the 
reference
Corrected 
values of the 
pixel 
(reflectance)
Spectrum 
reflected by 
the object 
Object 
reflectance
(database)
Fig. 4 Acquisition chain model. Spectra reﬂected by the object (soil or vegetation) are computed from the
reﬂectance database and the illuminant. They are transformed into 4-D multispectral values according to the
sensor characteristics. The same process is used to compute multispectral values of a reference surface. The
ﬁnal reﬂectance is then computed
Precision Agric
123


where xreﬂected(ki), R(ki), xincident(ki) are respectively the luminous ﬂux reﬂected by the
object, the reﬂectance of the object and the incident luminous ﬂux at ki, the ith wavelength
of radiation.
Spectral mixing
In this study, a ‘‘mixed pixel’’ is deﬁned as a pixel whose digital values result from several
spectral classes (soil and vegetation) within the area on the ground that it covers.
The impact of image spatial resolution on plant detection is modeled by mixing the
initial spectra of the objects. Indeed, the reﬂectance spectrum of the area projected in one
pixel is the linear combination of the spectra of the objects located in this area. Thus, the
value of a mixed spectrum presenting soil and vegetation is computed as follows:
xmixed;reflected ki
ð Þ ¼ axplant;reflected ki
ð Þ þ 1  a
ð
Þxsoil;reflected ki
ð Þ
ð2Þ
where, a 2 [0; 1], is the vegetation rate in the resulting pixel, xplant(ki) is the luminous
ﬂux reﬂected by the plant at the ith wavelength, xsoil(ki) is the luminous ﬂux reﬂected by
the soil at the ith wavelength, xmixed(ki) is the simulated value (at the ith wavelength) of the
luminous ﬂux reﬂected by an area in which both plant and soil are observed.
The proportion a depends on the spatial resolution and plant size.
Each mixed spectrum was computed from three independent random selections. For
example, the creation of a mixed spectrum of maize consists of (1) the random selection of
xplant from the maize spectra database (47 spectra), (2) the random selection of xsoil from
the soil spectra database (286 spectra), (3) the random selection of a drawn from a veg-
etation rate distribution function.
Vegetation rate cumulative distribution
In an image, the vegetation rate cumulative distribution depends on vegetation abundance
as well as plant size. For example, the smaller the plant (with respect to the spatial
resolution), the lower the vegetation rate will be in the pixel. The vegetation rate cumu-
lative distribution used in this study was assessed from images captured with the actual
spatial resolution determined from the UAV-MS-60 mm images; as such, this distribution
corresponds closely to the reality of the ﬁeld.
The vegetation rate cumulative distribution (Fig. 5) represents the probability that the
vegetation rate has a value lower than x:
Fig. 5 Vegetation rate
cumulative distribution function,
computed for an ortho-image of a
weed infested maize ﬁeld
Precision Agric
123


Fa x
ð Þ ¼ P a  x
ð
Þ
ð3Þ
where, a is the vegetation rate, Fa is the cumulative distribution function of the vegetation
rate a, P(a B x) is the probability that a is less than x.
The vegetation rate cumulative distribution was computed from the Veg-rate-6 mm
image using Eq. (3). This image was degraded to a 60 mm spatial resolution averaging the
vegetation rates of the 6 mm pixels located in the new 60 mm pixel. The cumulative
distribution function was then computed.
This ﬁgure illustrates the probability to ﬁnd a pixel with a vegetation rate a lower than
x in the image. For example, in this ﬁgure, the probability to have a pixel with a vegetation
rate below 0.5 is 0.90.
Acquisition system characteristics
Combining the characteristics of the acquisition chain (Fig. 2), the continuous spectrum
(pure or mixed) was transformed into a 4-D output signal (one value for each ﬁlter). The
optical ﬁlters allowed the luminous ﬂux to pass through in various proportions according to
wavelength. Thus, the four sensors equipped with different optical ﬁlters receive four
distinct luminous ﬂuxes. The luminous ﬂux arriving at a given time on the sensor is then
transformed into an electrical signal. This signal depends on the sensor sensitivity. The
four components of the output signal p were computed for each ﬁlter, taking into account
these parameters:
p jð Þ ¼
X
n
i¼1
xreflected ki
ð Þ  sj ki
ð Þ  g ki
ð Þ  tint
ð4Þ
where j is the number of the ﬁlter (from 1 to 4), n is the number of wavelengths, xreﬂected(ki)
is the luminous ﬂux reﬂected by the objects at the ith wavelength, sj(ki) is the transmittance
of the jth ﬁlter at the ith wavelength, g(ki) is the sensitivity of the sensor at the ith
wavelength, and tint is the integration time.
Reﬂectance computation
To model the reﬂectance correction, the same process (Eq. 4) was used to transform the
reference spectra to output values of the sensor. The reﬂectance pixel was the ratio between
the output signal coming from the object being studied (i.e. plants or soil) and the output
signal from the reference. This reﬂectance was then corrected by means of a reﬂectance
correction factor deduced from the light variation measured by the light meter embedded in
the UAV.
The luminous ﬂux acquisition by the sensor and the creation of the ortho-image cause
noise in the ﬁnal data. A random noise, deduced from the multispectral images, was added
to the pixel reﬂectance. This was additive Gaussian noise with a standard deviation equal
to 0.03.
The corrected values (4-D vector) of the pixel were modeled as follows:
pc jð Þ ¼ p jð Þ
pref jð Þ  f þ d
ð5Þ
where pref(j) is the jth component (j from 1 to 4) of the pixel value obtained for the white
reference, f is the reﬂectance correction factor, d is the additive Gaussian noise.
Precision Agric
123


To summarize, this simulation consists in modeling mixed spectra with the spectral
database and in transforming them into 4-D vectors representing the reﬂectance values of
modeled mixed pixels: the Sim-mixed-60 mm pixels. A classiﬁcation was then tested on
these pixels to assess the impact of spectral mixings on the results.
Pixel classiﬁcation
To obtain a classiﬁcation that can be applied to images captured in varying conditions, an
unsupervised classiﬁcation was chosen. Indeed, the implementation of a supervised clas-
siﬁcation would require the use of a large database (including various illuminants, soil
types, species, growth stages, etc.), which is hardly feasible. The classiﬁcation method used
in this work is based on a K-means algorithm using a Mahalanobis distance (Melnykov and
Melnykov 2014). The Mahalanobis distance (Mahalanobis 1936) between the class Ck and
the pixel, whose value is pc, is:
dpc!Ck ¼
ﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃﬃ
pc  lk
ð
ÞTR1
k
pc  lk
ð
Þ
q
ð6Þ
where lk is the mean vector of the corrected pixels of the class Ck, Rk
-1 is the inverse
covariance matrix of the pixels of the class Ck, pc  lk
ð
ÞT is the transpose of the vector
ðpc  lkÞ.
The ﬁrst classiﬁcation tested discrimination between soil and vegetation. This classi-
ﬁcation was performed on pixels of soil and vegetation, as well as mixed pixels in various
proportions. The classiﬁcation method was adapted to classify the elements derived from
the two classes and presenting various mixing rates between each other. It is composed of
four main steps:
Step 1
Application of the classiﬁcation algorithm to identify three classes
Step 2
Computation of the mean Normalized Difference Vegetation Index (NDVI)
(Rouse et al. 1973) of each class, The NDVI is computed as follows:
NDVI ¼ NIR  R
NIR þ R
ð7Þ
where NIR is the value of the corrected pixels in the near infra-red (4th pixel
component) and R is the value of the corrected pixels in the red (2nd pixel
component). The remaining pixels are classiﬁed as Undetermined
Step 3
Classiﬁcation of the three classes into Soil, undetermined and vegetation as being
those with the lowest, intermediate and highest NDVI, respectively
Step 4
Classiﬁcation of the undetermined pixels into the soil or vegetation class,
according to the smaller Mahalanobis distance (cf. Eq. 6)
After applying the previous classiﬁcation (steps 1–4), only pixels classiﬁed as vegeta-
tion were selected for further classiﬁcation between monocotyledons and dicotyledons.
The discrimination procedure was conducted in three steps:
Step 1
Application of the classiﬁcation algorithm to identify three classes (from the
Vegetation pixels)
Step 2
Identiﬁcation of dicotyledons as the class with the highest values in the NIR
(Gausman 1985), undetermined (which are pixels mixed with soil) as having the
lowest values in the NIR and monocotyledons as being between the two
Precision Agric
123


Step 3
Classiﬁcation of the undetermined pixels into the monocotyledons or
dicotyledons class, computing the Mahalanobis distances
Classiﬁcation results were then analyzed by plotting the proportion of pixels correctly
classiﬁed according to the vegetation rates in the modeled pixels.
Simulation and real image comparison
To assess the detection potential on images presenting pixels with various vegetation rates,
the above classiﬁcation was tested on the Sim-mixed-60 mm pixels and the Pole-MS-
60 mm image.
Resolution reduction
The Pole-MS-6 mm ortho-image was degraded to lower resolutions by resizing the image
and replacing 10 by 10 pixels with only one whose value was the average of the original
pixels. The test was implemented on the image degraded to 60 mm: the Pole-MS-60 mm
image, which is the actual spatial resolution obtained with the aerial UAV imaging
campaign. To analyze the classiﬁcation results according to the spectral mixings, the Veg-
rate-6 mm image was also degraded to 60 mm, resulting on the Veg-rate-60 mm image.
The degraded image pixels were computed by averaging the vegetation rates corre-
sponding to the previously constructed ground truth image (Fig. 6).
The classiﬁcation was then applied to the degraded image pixels and the results could be
compared with the vegetation rates of this new ground truth image.
Classiﬁcation of real image pixels
Pixel values were extracted from the Pole-MS-60 mm image. A ﬁrst classiﬁcation was
performed to discriminate soil from vegetation and a second classiﬁcation was applied to
vegetation pixels to discriminate monocotyledons from dicotyledons. The classiﬁcation
procedure was the same as that used for the simulation, as described above. Classiﬁcation
Fig. 6 Example of vegetation rate image degradation from 6 to 60 mm. The NDVI image (on the top) is
converted into a vegetation rate image (on the left), which is degraded to lower resolutions (images on the
right)
Precision Agric
123


results were then plotted according to the computed vegetation rate in the pixel. The graphs
obtained could be compared to the simulation results.
Results and discussion
Classiﬁcation of soil and vegetation
The classiﬁcation algorithm was ﬁrst tested on the Sim-unmixed-60 mm pixels, where the
modeled pixels are without mixing. The classiﬁcation was performed on all modeled
vegetation pixels (310 pixels) and soil (286 pixels) from the database. The two classes were
easily distinguishable: all the pixels were correctly classiﬁed as Soil or Vegetation.
The classiﬁcation algorithm was then tested on the Sim-mixed-60 mm pixels. The
vegetation rates in the pixels were modeled from the distribution function computed from
the 60 mm spatial resolution. The results are presented in a histogram in which the pro-
portion of pixels detected as vegetation is plotted according to the vegetation rate in the
mixing (Fig. 7).
These results show that with this unsupervised classiﬁcation, a pixel is classiﬁed as
Vegetation with a probability greater than 80% as soon as the vegetation rate in the pixel is
greater than 0.5. Pixels presenting a vegetation rate lower than 0.4 will be classiﬁed as
Vegetation with a probability lower than 50%.
To compare the above results with the reality of the ﬁeld, the same classiﬁcation was
tested on the Pole-MS-60 mm image. The classiﬁcation results were plotted according to
the vegetation rates estimated in the Veg-rate-60 mm image (Fig. 8).
The classiﬁcation results from the Pole-MS-60 mm image were similar to the simula-
tion results. Indeed, both histograms present a sigmoid shape with:
–
the classiﬁcation as vegetation close to 0% for the lower vegetation rates.
–
a transition phase from 10 to 90% of pixels classiﬁed as Vegetation for the increasing
vegetation rates.
–
a plateau close to 100% of pixels classiﬁed as Vegetation for pixels with a high
vegetation rate.
However, there is a slight shift between the transition phases in the two histograms. This
may be due to the approximation of the vegetation rates in the ground truth image.
Fig. 7 Distribution of pixels
classiﬁed as Vegetation in the
simulation, according to their
vegetation rates
Precision Agric
123


In both cases, more than 95% of the pixels are detected as vegetation when their
vegetation rates are greater than 0.7. For such vegetation rates, almost all the pixels can be
correctly detected.
Classiﬁcation of the vegetation class into monocotyledons and dicotyledons
The classiﬁcation algorithm was ﬁrst tested without mixing on the Sim-unmixed-60 mm
pixels of monocotyledonous and dicotyledonous plants in the database (47 pixels of maize
and 84 pixels of sunﬂower). The algorithm computed two classes: soil and vegetation. The
two classes were easily distinguishable with the 4-pixel components since all the pixels
were correctly classiﬁed. Vegetation pixels were then classiﬁed as monocotyledons or
dicotyledons: 95% of the monocotyledons and 90% of the dicotyledons detected as veg-
etation were correctly classiﬁed.
The classiﬁcation algorithm was then tested on the Sim-unmixed-60 mm pixels. The
results are presented in histograms in which the proportion of pixels correctly classiﬁed as
monocotyledons or dicotyledons is plotted according to the rate of vegetation in the mixing
(Fig. 9). In these graphs, monocotyledons that are incorrectly classiﬁed are classiﬁed in the
dicotyledon class and vice versa.
These histograms reveal that the probability of classifying pixels with a vegetation rate
lower than 0.5 as monocotyledons or dicotyledons is lower than 60 and 10% respectively:
the classes are hardly distinguishable. To obtain a better classiﬁcation, the vegetation rate
Fig. 9 Distribution of classiﬁcation results of the Sim-mixed-60 mm pixels of monocotyledons (left) and
dicotyledons (right), according to their vegetation rates
Fig. 8 Distribution of pixels
classiﬁed as vegetation in the
Pole-MS-60 mm image,
according to their vegetation
rates
Precision Agric
123


in the pixel must be maximal: with pure pixels, the percentage of accurate classiﬁcation is
80% for monocotyledons and dicotyledons. Thus, this theoretical simulation shows that a
high rate of vegetation in the mixed pixels, and therefore a high spatial resolution, is
required to discriminate dicotyledons and monocotyledons.
Moreover, pixels with lower vegetation rates are more frequently classiﬁed as mono-
cotyledons rather than dicotyledons. This ﬁnding may be explained by a decrease in the
reﬂectance value of the infra-red plateau in mixed dicotyledon pixels, which should be
higher for dicotyledons. Thus, the mixed dicotyledon pixels may be mistaken for mono-
cotyledon pixels, which cause an overestimation of monocotyledons.
The same monocotyledon/dicotyledon classiﬁcation was tested on the Pole-MS-60 mm
image already classiﬁed as Vegetation. The results are plotted according to the vegetation
rates estimated on the Veg-rate-60 mm image (Fig. 10).
The classiﬁcation for dicotyledonous plants presents the same shape as that of the
simulation results. Both results increase from 0 to 80% as the vegetation rate in the pixel
increases from 0 to 1.
The classiﬁcation results in the simulation and in the Pole-MS-60 mm image seem
different in the case of monocotyledons. First, the results for the vegetation rates greater
than 0.9 are missing. Indeed, in the Pole-MS-60 mm image, there were no pure pixels of
monocotyledons. This ﬁnding may be explained by the fact that these plants had small
leaves and that they grow vertically, in contrast to dicotyledons which have larger leaves
and which grow in a horizontal spreading pattern on the soil. Due to these characteristics, a
small number of monocotyledon pixels presented a high vegetation rate, a fact which
produces noise in the results. Thus, if a classiﬁcation error occurred for one pixel, for
example because of an incorrect vegetation rate estimation, the result could not be bal-
anced with other pixel classiﬁcations. For this reason, the plateau cannot be identiﬁed in
the monocotyledon classiﬁcation graph and a conclusion is hard to reach from these results.
When comparing all these results, the histograms based on data from the real-life
images are similar in shape although more spread out than those obtained from simulation
data. This may be due to the vegetation rate estimation in the image pixels. Indeed, this
estimation was made empirically and was the same for dicotyledons and monocotyledons.
It does not take into account the plant shape and, in this way, may overestimate vegetation
rates in the monocotyledon pixels. Moreover it assumes that a pixel in the middle of a plant
is 100% vegetation; however, it may happen that holes appear in the middle of neighboring
plants. That is why the vegetation rates may be overestimated. The close results obtained
Fig. 10 Distribution of the classiﬁcation results of the Pole-MS-60 mm pixels for monocotyledons (left)
and dicotyledons (right), according to their vegetation rates
Precision Agric
123


from the simulation data and multispectral image data justify the use of this simulation to
assess detection potential.
Spectral information potential of UAV images
The results presented here show that the presence of vegetation in mixed pixels can be
detected even when this presence decreases to 40%. These are promising results in the
drive to detect small weeds in ﬁelds. Indeed, weeds must be controlled in young pheno-
logical stages, starting from the cotyledon stage which leads to pixels with few vegetation
rates in the images. However, these data must be linked to a spatial resolution and a
detectable weed size to quantify the ability to detect small weeds in images acquired by
UAV. Vegetation rates can be computed for different size of plants, various shape and
different spatial resolution. Table 4 presents examples of vegetation rates obtained for
circular shapes with respect to various plant surfaces and spatial resolutions. Details
concerning the equations are presented as supplementary material.
For example, in the case of a spatial resolution of 10 mm and a circular weed of
approximately 200 mm2 (a disk of 8 mm radius), the pixel will indicate 100% vegetation
in the best case and, in the worst case (when the weed is at the junction of four pixels), the
pixel will present 50% of vegetation. Thus, the probability of detecting this weed on bare
soil is between 80 and 100%, according to the simulation. The relationship between spatial
resolution and detectable plant size should be studied by modeling various realistic plant
shapes and assessing vegetation rates with these complex shapes.
The classiﬁcation between monocotyledons and dicotyledons shows good results for
pixels with a vegetation rate higher than 0.9 but is hardly feasible in the case of lower
vegetation rates. Thus, with the sensor tested here, the image needs to present pure plant
pixels, and thus a very high spatial resolution in order to obtain a good discrimination
between monocotyledonous and dicotyledonous plants.
To illustrate these results, Fig. 11 shows the results of monocotyledons/dicotyledons
classiﬁcation obtained on a Pole-MS-6 mm ortho-image acquired on the ground, and on
the UAV-MS-60 mm ortho-image acquired by the UAV. The corresponding ground truth
was presented in Fig. 3. On the Pole-MS-6 mm ortho-image, small weeds at the cotyledon
stages (stage 10 in the BBCH scale) can be detected and monocotyledons and dicotyledons
can be classiﬁed. However, on the UAV-MS-60 mm ortho-image, only weeds wider than
100 mm or distributed in patches are detected. On this image, monocotyledons are largely
Table 4 Minimum and maximum vegetation rates (in %) that can be found for the pixel in the center of the
plant, according to different spatial resolutions and for several plant surfaces
Spatial resolution
(mm)
Plant surface
100 mm2
200 mm2
500 mm2
1000 mm2
1500 mm2
5000 mm2
10000 mm2
6
[69–100]
[99–100]
100
100
100
100
100
10
[25–92]
[50–100]
[98–100]
100
100
100
100
20
[6–25]
[13–50]
[31–98]
[63–100]
[90–100]
100
100
30
[3–11]
[6–22]
[14–67]
[28–95]
[53–100]
100
100
60
[1–3]
[1–6]
[3–14]
[7–28]
[10–42]
[35–100]
[69–100]
100
[0–1]
[1–2]
[1–5]
[3–10]
[4–15]
[13–50]
[25–92]
150
0
[0–1]
[1–2]
[1–4]
[2–7]
[6–22]
[11–44]
Precision Agric
123


overestimated, as observed for the results of the simulation, on Fig. 9, due to the abun-
dance of mixed pixels. Thus, discrimination between dicotyledons and monocotyledons is
not applicable with such a resolution to detect all weeds. Nevertheless, these ortho-images
could be used to detect large weeds such as thistle.
Results of this study show that the spatial resolution must be adapted to the size and
type of the object to detect. Indeed, McBratney et al. (2003) proposed a resolution of at
least 2 9 2 pixels on the area of the smallest object that can be detected. This rule was
derived from information theory (Nyquist frequency) applied on spatial sampling prob-
lems. This rule matches with the results of the discrimination between monocotyledons and
dicotyledons, where the pixels must contain 100% of vegetation to be correctly classiﬁed.
However, the spectral characteristics of the vegetation allow a separation from the soil
despite lower resolutions. The study showed that to detect vegetation on soil with a
probability higher than 95%, a pixel must contain at least 60% of vegetation which allows
reducing the spatial resolution to have the area of the smallest object to detect on at least
60% of the square corresponding to 2 9 2 pixels. The same result can be compared with
Pen˜a et al. (2015), who got the best weed detection (91% of good detection) on multi-
spectral images with a spatial resolution of 21.6 mm on a weed infested sunﬂower ﬁeld. In
this study, phenological stages of crops and weeds varied from 14 to 18 on the BBCH
scale. According to the supplementary material, for a spatial resolution of 21.6 mm, the
vegetation rates in the pixels are higher than 0.6 when weed surfaces are greater than
1000 mm2, which represent a disk with a radius of 18 mm. Thus, to detect weed between
crop rows (soil-vegetation discrimination) with a probability of good detection greater than
95%, crops and weeds should be wider than a disk with a radius 18 mm. This plant size is
consistent with the stages of the plants detected by Pen˜a et al. (2015). Soil-vegetation
classiﬁcation results can be used to better understand the potentiality and the limits of the
detection of a vegetation pixel in bare soil. This applies to weed detection in the inter-row.
Indeed, most weed detection algorithms identify weeds by locating vegetation in the inter-
row. The monocotyledon/dicotyledon classiﬁcation results can be used to help users in
selecting the right acquisition system for the discrimination of plants in rows. To further
1 m
Dictotyledons
Monocotyledons
Fig. 11 Example of classiﬁcation between monocotyledons and dicotyledons on an ortho-image with a
spatial resolution of 6 mm/pixel (left) and 60 mm/pixel (right)
Precision Agric
123


the research presented here, the monocotyledon/dicotyledon mixings could be added to the
simulation.
The model presented in this study allows the transformation of reﬂectance spectra in
mixed pixels representing a multispectral image captured by means of a UAV. In this
simulation, dicotyledonous weeds were modeled with spectra from sunﬂowers, at different
stages (2–6 leaves), which is not sufﬁciently representative of dicotyledon spectrum
diversity. The results presented here should be assessed with more species and at speciﬁc
stages. Moreover, comparing two species only cannot eliminate the possibility that the
difference between the two classes is speciﬁc to these species. Nonetheless, the use of this
simple database makes possible the use of the model for the simulations and shows that the
simulation results were similar to results obtained on the multispectral images with real
dicotyledonous weeds although dicotyledonous species in the real ﬁeld were not those of
the database.
In future work, additional parameters could be tested in the model to assess their impact
on crop–weed discrimination potential. For example, various optical ﬁlters could be tested
in the simulation to discriminate between different species. After comparison of the
classiﬁcation results, a combination of optical ﬁlters could be selected. A speciﬁc sensor
particularly adapted to crop/weed discrimination could be proposed, along with a speciﬁc
prescription for optimal acquisition conditions.
Conclusion
This study aimed to assess soil-vegetation and crop–weed discrimination potential in
multispectral images captured with a UAV, modeling the whole image acquisition chain.
The model presented above is based on the AIRINOV image acquisition system, in which
images are characterized by a spatial resolution of 60 mm. The different parameters
(sensor, optical ﬁlters spatial resolution, etc.) of the acquisition chain were modeled to
transform reﬂectance spectra, acquired in laboratory conditions, into modeled pixels. In
particular, the mixing rates in the pixels were modeled to assess the impact of spatial
resolution on plant detection potential. In terms of the different levels of mixing, the
classiﬁcation of the modeled pixels demonstrated the possibility of detecting low rates of
vegetation in pixels (more than 80% of correct classiﬁcation when vegetation rates were
greater than 0.5) and the necessity of high vegetation rates to discriminate monocotyledons
from dicotyledons (80% accurate classiﬁcation for vegetation rates greater than 0.8). The
simulation results were compared to those obtained from multispectral images of an
infested ﬁeld. The results conﬁrmed the model ability to assess crop–weed discrimination
potential for speciﬁc sensors. Testing the different acquisition chain parameters in this
model would allow determination of the optimal sensor characteristics (e.g. optical ﬁlters),
and acquisition conditions (e.g. spatial resolution), for good crop/weed discrimination.
In addition, this study demonstrated that interpretation of the spatial resolution of the
image to a detection probability for a given weed size is possible. It is an important step in
the development of a weed detection service by UAV, since the potential of detection for
the smallest weeds must be known to assess the risk for crop development. Moreover,
being able to discriminate monocotyledonous and dicotyledonous plants would help to
improve the current algorithm to detect weeds in crop rows.
Precision Agric
123


Acknowledgements This project is supported by AIRINOV Company and the ANRT (Association
Nationale de la Recherche et de la Technologie). This study is also supported by the program ‘‘ANR
CoSAC’’ (ANR-14-CE18-0007).
References
ASTM G173-03 (2012). Standard tables for reference solar spectral irradiances: direct normal and hemi-
spherical on 37 tilted surface. ASTM International, West Conshohocken, PA, USA. Retrieved form
www.astm.org.
Bird, R. E., & Riordan, C. (1984). Simple Solar Spectral Model for Direct and Diffuse Irradiance on
Horizontal and Tilted Planes at the Earth’s Surface for Cloudless Atmospheres. Technical Report No.
SERI/TR-215-2436, Golden, CO, USA: Solar Energy Research Institute.
Borra-Serrano, I., Pen˜a, J. M., Torres-Sa´nchez, J., Mesas-Carrascosa, F. J., & Lo´pez-Granados, F. (2015).
Spatial quality evaluation of resampled unmanned aerial vehicle-imagery for weed mapping. Sensors,
15, 19688–19708.
Bossu, J., Ge´e, C., Jones, G., & Truchetet, F. (2009). Wavelet transform to discriminate between crop and
weed in perspective agronomic images. Computers and Electronics in Agriculture, 65(1), 133–143.
Brown, R. B., Steckler, J.-P. G. A., & Anderson, G. W. (1994). Remote sensing for identiﬁcation of weeds in
no-till corn. Transactions of the ASAE, 37(1), 297–302. doi:10.13031/2013.28084.
Clay, S. A., Lems, G. J., Clay, D. E., Forcella, F., Ellsbury, M. M., & Carlson, C. G. (1999). Sampling weed
spatial variability on a ﬁeldwide scale. Weed Science, 47(6), 674–681. doi:10.2307/4046133.
De Castro, A. I., Jurado-Exposito, M., Gomez-Casero, M.-T., & Lopez-Granados, F. (2012). Applying
neural networks to hyperspectral and multispectral ﬁeld data for discrimination of cruciferous weeds in
winter crops. The Scientiﬁc World Journal. doi:10.1100/2012/630390.
Feyaerts, F., & van Gool, L. (2001). Multi-spectral vision system for weed detection. Pattern Recognition
Letters, 22(6–7), 667–674. doi:10.1016/S0167-8655(01)00006-X.
Garcia-Ruiz, F. J., Wulfsohn, D., & Rasmussen, J. (2015). Sugar beet (Beta vulgaris L.) and thistle (Cirsium
arvensis L.) discrimination based on ﬁeld spectral data. Biosystems Engineering, 139, 1–15. doi:10.
1016/j.biosystemseng.2015.07.012.
Gausman, H. W. (1985). Plant Leaf Optical Properties in Visible and Near-Infrared Light. Graduate studies
No. 29, Lubbock, USA: Texas Tech University.
Gerhards, R., So¨kefeld, M., Timmermann, C., Ku¨hbauch, W., & Williams, M. M., II. (2002). Site-speciﬁc
weed control in maize, sugar beet, winter wheat, and winter barley. Precision Agriculture, 3(1), 25–35.
doi:10.1023/A:1013370019448.
Girma, K., Mosali, J., Raun, W. R., Freeman, K. W., Martin, K. L., Solie, J. B., et al. (2005). Identiﬁcation
of optical spectral signatures for detecting cheat and ryegrass in winter wheat. Crop Science, 45,
477–485.
Hadoux, X., Gorretta, N., & Rabatel, G. (2012). Weeds-wheat discrimination using hyperspectral imagery.
In CIGR (Ed.), International Conference on Agricultural Engineering. Valence, Spain.
Jones, G., Ge´e, C., & Truchetet, F. (2009). Assessment of an inter-row weed infestation rate on simulated
agronomic images. Computers and Electronics in Agriculture, 67(1–2), 43–50.
Lopez-Granados, F., PeNa-BarragAn, J., Jurado-ExpOsito, M., Francisco-FernAndez, M., Cao, R., Alonso-
Betanzos, A., et al. (2008). Multispectral classiﬁcation of grass weeds and wheat (Triticum durum)
using linear and nonparametric functional discriminant analysis and neural networks. Weed Research,
48(1), 28–37.
Mahalanobis, P. C. (1936). On the generalized distance in statistics. Proceedings of the National Institute of
Science of India, 12, 49–55.
Martı´n, C. S., Andu´jar, D., Barroso, J., Ferna´ndez-Quintanilla, C., & Dorado, J. (2016). Weed decision
threshold as a key factor for herbicide reductions in site-speciﬁc weed management. Weed Technology,
30(4), 888–897. doi:10.1614/WT-D-16-00039.1.
McBratney, A. B., Mendonc¸a Santos, M. L., & Minasny, B. (2003). On digital soil mapping. Geoderma,
117(1–2), 3–52. doi:10.1016/S0016-7061(03)00223-4.
Meier, U. (2001). Growth stages of mono-and dicotyledonous plants. BBCH Monograph. Braunschweig,
Germany: Federal Biological Research Centre for Agriculture and Forestry.
Melnykov, I., & Melnykov, V. (2014). On K-means algorithm with the use of Mahalanobis distances.
Statistics & Probability Letters, 84, 88–95. doi:10.1016/j.spl.2013.09.026.
Mesas-Carrascosa, F. J., Torres-Sa´nchez, J., Clavero-Rumbao, I., Garcı´a-Ferrer, A., Pen˜a, J.-M., Borra-
Serrano, I., et al. (2015). Assessing optimal ﬂight parameters for generating accurate multispectral
Precision Agric
123


orthomosaicks by UAV to support site-speciﬁc crop management. Remote Sensing, 7(10),
12793–12814. doi:10.3390/rs71012793.
Nordmeyer, H. (2006). Patchy weed distribution and site-speciﬁc weed control in winter cereals. Precision
Agriculture, 7, 219–231.
Pen˜a, J. M., Torres-Sa´nchez, J., de Castro, A. I., Kelly, M., & Lo´pez-Granados, F. (2013). Weed mapping in
early-season maize ﬁelds using object-based analysis of unmanned aerial vehicle (UAV) images. PLoS
ONE, 8(10), e77151. doi:10.1371/journal.pone.0077151.
Pen˜a, J. M., Torres-Sa´nchez, J., Serrano-Pe´rez, A., De Castro, A. I., & Lo´pez-Granados, F. (2015).
Quantifying efﬁcacy and limits of unmanned aerial vehicle (UAV) technology for weed seedling
detection as affected by sensor resolution. Sensors, 15(3), 5609–5626.
Pe´rez-Ortiz, M., Pena, J. M., Gutie´rrez, P. A., Torres-Sa´nchez, J., Herva´s-Martı´nez, C., & Lo´pez-Granados,
F. (2015). A semi-supervised system for weed mapping in sunﬂower crops using unmanned aerial
vehicles and a crop row detection method. Applied Soft Computing, 37, 533–544. doi:10.1016/j.asoc.
2015.08.027.
Rango, A., Laliberte, A., Herrick, J. E., Winters, C., Havstad, K., Steele, C., et al. (2009). Unmanned aerial
vehicle-based remote sensing for rangeland assessment, monitoring, and management. Journal of
Applied Remote Sensing, 3, 033542.
Rasmussen, J., Nielsen, J., Garcia-Ruiz, F., Christensen, S., & Streibig, J. C. (2013). Potential uses of small
unmanned aircraft systems (UAS) in weed research. Weed Research, 53(4), 242–248. doi:10.1111/wre.
12026.
Rouse, J. W., Haas, R. H., Schell, J. A., & Deering, D. W. (1973). Monitoring Vegetation Systems in the
Great Plains with ERTS. In Proceedings of the Third ERTS Symposium, NASA SP-351, NASA,
Washington, DC, 1, 309–317.
Shannon, C. E. (1949). Communication in the presence of noise. Proceedings of the IRE, 37(1), 10–21.
doi:10.1109/JRPROC.1949.232969.
Shapira, U., Herrmann, I., Karnieli, A., & Bonﬁl, D. J. (2013). Field spectroscopy for weed detection in
wheat and chickpea ﬁelds. International Journal of Remote Sensing, 34(17), 6094–6108. doi:10.1080/
01431161.2013.793860.
Stafford, J. V., & Miller, P. C. H. (1993). Spatially selective application of herbicide to cereal crops.
Computers and Electronics in Agriculture, 9(3), 217–229. doi:10.1016/0168-1699(93)90040-8.
Thornton, P. K., Fawcett, R. H., Dent, J. B., & Perkins, T. J. (1990). Spatial weed distribution and economic
thresholds for weed control. Crop Protection, 9(5), 337–342. doi:10.1016/0261-2194(90)90003-P.
Verger, A., Vigneau, N., Che´ron, C., Gilliot, J.-M., Comar, A., & Baret, F. (2014). Green area index from an
unmanned aerial system over wheat and rapeseed crops. Remote Sensing of Environment, 152,
654–664. doi:10.1016/j.rse.2014.06.006.
Vioix, J. B., Douzals, J. P., & Truchetet, F. (2003). Development of a spatial method for weed detection and
localization. In Proceedings of SPIE 5266, Wavelet Applications in Industrial Processing. doi:10.1117/
12.516253.
Vrindts, E., De Baerdemaeker, J., & Ramon, H. (2002). Weed Detection Using Canopy Reﬂection. Pre-
cision Agriculture, 3(1), 63–80.
Zhang, C., & Kovacs, J. (2012). The application of small unmanned aerial systems for precision agriculture:
A review. Precision Agriculture, 13(6), 693–712. doi:10.1007/s11119-012-9274-5.
Precision Agric
123
