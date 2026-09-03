---
title: "remotesensing-16-03538-v2"
doi: "10.3390/rs16183538"
extraction_engine: pymupdf
---

Citation: Lauwers, M.; De Cauwer, B.;
Nuyttens, D.; Maes, W.H.; Pieters, J.G.
Multispectral UAV Image
Classification of Jimson Weed (Datura
stramonium L.) in Common Bean
(Phaseolus vulgaris L.). Remote Sens.
2024, 16, 3538. https://doi.org/
10.3390/rs16183538
Academic Editor: Pedro Melo-Pinto
Received: 9 August 2024
Revised: 19 September 2024
Accepted: 20 September 2024
Published: 23 September 2024
Copyright: © 2024 by the authors.
Licensee MDPI, Basel, Switzerland.
This article is an open access article
distributed under the terms and
conditions of the Creative Commons
Attribution (CC BY) license (https://
creativecommons.org/licenses/by/
4.0/).
remote sensing 
Article
Multispectral UAV Image Classification of Jimson Weed
(Datura stramonium L.) in Common Bean (Phaseolus vulgaris L.)
Marlies Lauwers 1, Benny De Cauwer 1, David Nuyttens 2
, Wouter H. Maes 1 and Jan G. Pieters 1,*
1
Department of Plants and Crops, Ghent University, Coupure Links 653, 9000 Ghent, Belgium;
benny.decauwer@ugent.be (B.D.C.); wouter.maes@ugent.be (W.H.M.)
2
Flanders Research Institute for Agriculture, Fisheries and Food (ILVO), Burg. van Gansberghelaan 115,
9820 Merelbeke, Belgium; david.nuyttens@ilvo.vlaanderen.be
*
Correspondence: jan.pieters@ugent.be; Tel.: +32-9-264-61-88
Abstract: Jimson weed (Datura stramonium L.) is a toxic weed that is occasionally found in fields with
common bean (Phaseolus vulgaris L.) for the processing industry. Common bean growers are required
to manually remove toxic weeds. If toxic weed plants remain, the standing crop will be rejected.
Hence, the implementation of an automatic weed detection system aiding the farmers is badly needed.
The overall goal of this study was to investigate if D. stramonium can be located in common bean
fields using an unmanned aerial vehicle (UAV)-based ten-band multispectral camera. Therefore
four objectives were defined: (I) assessing the spectral discriminative capacity between common
bean and D. stramonium by the development and application of logistic regression models; (II)
examining the influence of ground sampling distance (GSD) on model performance; and improving
model generalization by (III) incorporating the use of vegetation indices and cumulative distribution
function (CDF) matching and by (IV) combining spectral data from multiple common bean fields
with the use of leave-one-group-out cross-validation (LOGO CV). Logistic regression models were
created using data from fields at four different locations in Belgium. Based on the results, it was
concluded that common bean and D. stramonium are separable based on multispectral information.
A model trained and tested on the data of one location obtained a validation true positive rate and
true negative rate of 99% and 95%, respectively. In this study, where D. stramonium had a mean plant
size of 0.038 m2 (σ = 0.020), a GSD of 2.1 cm was found to be appropriate. However, the results
proved to be location dependent as the model was not able to reliably distinguish D. stramonium
in two other datasets. Finally, the use of a LOGO CV obtained the best results. Although small
D. stramonium plants were still systematically overlooked and classified as common bean, the model
was capable of detecting large D. stramonium plants on three of the four fields. This study emphasizes
the variability in reflectance data among different common bean fields and the importance of an
independent dataset to test model generalization.
Keywords: toxic weeds; processing industry; logistic regression; machine learning; precision agriculture;
leave-one-group-out cross-validation; cumulative distribution function matching
1. Introduction
Flanders (Belgium) is the largest exporter of frozen vegetables in the world with
a production value of EUR 682 million [1]. Common bean (Phaseolus vulgaris L.) is an
important crop for this industry where the pods of beans are harvested mechanically.
However, common bean growers are facing increasing risks of toxic weeds, such as Datura
stramonium L. (jimson weed), Solanum nigrum subsp. nigrum L. (black nightshade), and
Solanum tuberosum L. (volunteer potato). In common bean, the weed D. stramonium poses
the biggest problem. It is an annual containing, among other toxins, the alkaloids atropine,
scopolamine, and hyoscyamine. The weed poses a significant problem due to its high
toxicity of all plant parts. Occurrences of D. stramonium poisoning resulting in death
Remote Sens. 2024, 16, 3538. https://doi.org/10.3390/rs16183538
https://www.mdpi.com/journal/remotesensing


Remote Sens. 2024, 16, 3538
2 of 24
(unrelated to the consumption of common bean) have been reported [2]. Moreover, the
weed is rapidly spreading in Belgium [3] and the rest of the world [4], and it has been
found in processed common bean [5].
There are very few active substances available to target this weed (clomazone, dimethe-
namid-P, bentazon, and ethofumesate), which raises concerns among growers and the
industry regarding inadequate control in the future. Moreover, if D. stramonium is discov-
ered in the field, the growers face the risk of income loss. The frozen/canned vegetables
processing industry commonly adopts a visual inspection approach to identify poisonous
weeds in bean fields. This inspection is carried out during the week preceding harvest,
where the field’s edges and diagonals are inspected for any problematic weeds [6]. Farmers
are required to manually remove the toxic weeds, failing which, the standing crop will be
rejected. However, this method has a significant limitation in terms of its low detection
probability, especially when the inspected field is large and the weeds are relatively small.
Moreover, visual field inspections are time-consuming; labor-intensive; and subject to the
inspector’s expertise, leading to subjectivity issues.
Datura stramonium and common bean have been shown to be distinguishable from
each other using spectrometer measurements performed during the growing season on
greenhouse-grown plants [7]. Simulations based on these measurements suggested that
the two species could be distinguished with the use of ten commercial of-the-shelf filters.
Research has shown that reflectance measurements in the visible and near infrared (NIR)
wavelengths can be used for discriminating between weeds and crops [8–11]. However,
these studies do not use data gathered at different locations to test their models’ generaliz-
ability. As a result, reported accuracies are often remarkably yet unreliably high, and results
do not demonstrate the usefulness in practice. By using an independent test set, researchers
can assess the model’s performance on unseen data, ensuring that it generalizes well to
new observations under different conditions beyond the training data. This is a major step
often overlooked in most research aimed at developing a practical weed detection system.
It is well established that machine learning models perform well on interpolation (or
near-interpolation) tasks but struggle with extrapolation, and although their generalizabil-
ity is usually tested on samples with attributes similar to the training data, real-world data
rarely align perfectly with the training data [12]. So, to develop a model that generalizes
well, it is important to obtain consistent reflectance measurements. However, variations
in reflectance measurements may be attributed to, e.g., biotic and abiotic stressors [13],
soil reflectance [14], and variations in illumination and atmospheric conditions [15]. One
way to address these challenges is the use of vegetation indices (VI). Another potential
correction method between different datasets involves the application of the cumulative
distribution function (CDF). This non-linear approach aims to eliminate systematic dis-
crepancies between datasets [16,17] by transforming the data to ensure that their CDFs are
equal. Implementing such correction methods is crucial to ensuring the dependability of
reflectance data over multiple growing seasons amidst varying environmental conditions
and stressors.
In this study, we opted for an unmanned aerial vehicle (UAV) as a platform, as they are
easy-to-use, flexible, do not disturb the plants, and are able to yield high spatial resolution
imagery [18]. However, a trade-off has to be made between ground sampling distance
(GSD) and flight duration. MicaSense [19] recommends a minimum flight height of 40 m
above the canopy for the RedEdge Dual camera, the sensor used in this study, to reduce the
discrepancies in the images captured by the different lenses. However, successful studies
have been conducted at lower flight heights [20–22]. If weeds are small, the resolution must
be adequately high to discriminate them, consequently restricting the drone’s mapping
capability to a smaller area.
The goal of this study was to locate D. stramonium in common bean fields. For this
reason, four objectives were specified. The first objective of this study was to test the
spectral distinctness of D. stramonium and common bean by creating and applying models
using a dataset derived from one location (I). The second objective was to assess the optimal


Remote Sens. 2024, 16, 3538
3 of 24
GSD considering the time-resolution trade-off and the quality of the orthomosaic (II). The
third and fourth objectives of this study tested the generalization of a model with a dataset
separated in space and time from the training dataset. Therefore, a model was applied to
fields with unseen data. To address differences between datasets, VI were incorporated
in the model and/or CDF-corrected data were used (III), and data from diverse fields
were incorporated by applying a leave-one-group-out cross-validation (LOGO CV) to
CDF-corrected data (IV). The novelty of this paper lies in two key contributions: first, the
detection of D. stramonium in common bean fields, and second, the development of a model
that can accurately predict outcomes in untrained scenarios.
2. Materials and Methods
2.1. Study Areas
Data were collected from fields of four different locations in Belgium: Merelbeke
(50◦58′47.5′′N, 3◦44′38.9′′E), Oudenaarde (50◦51′3.9′′N, 3◦37′2.5′′E), Houthulst (50◦57′47.1′′N,
2◦53′57.6′′E), and Meulebeke (50◦57′8.0′′N, 3◦18′11.6′′E). Table 1 provides information on
the species, study area, inter- and intra-row spacing, and time of image acquisition. The
fields in Oudenaarde, Meulebeke, and Houthulst were managed by farmers under the
supervision of commercial companies, and the one in Merelbeke was an experimental
field managed by ILVO (Flanders Research Institute for Agriculture, Fisheries and Food,
Merelbeke, Belgium). Figure 1 provides an overview of all locations.
Table 1. Information on crop, weed, image collection, resolution of orthomosaics, and flight height for
different locations (CS: clear sky (0/8–1/8), PC: predominantly cloudy (6/8–7/8), PCS: predominantly
clear sky (1/8–2/8)).
Oudenaarde
Merelbeke
Meulebeke
Houthulst
Phaseolus vulgaris (commercial)
variety
Koala and Nagano
Fresano
Sintra
Sintra
Datura stramonium (botanical)
variety
var. stramonium
var. stramonium
var. tatula
var. stramonium
Soil type
sandy loam
sandy loam
sandy loam
sandy loam
Number of D. stramonium
plants in screened area
>400
35
34
90
Screened area (m2)
2445
380
735
730
Planting date
26 June 2020
14 May 2020
15 July 2022
5 July 2022
Date of image collection
2 September 2020 (68 *, BBCH
7)
12 July 2020
(59 *, BBCH 7)
15 September 2022 (67 *,
BBCH 7)
11 September 2022 (68 *,
BBCH 7)
Date of harvest
29 July 2020 (76 *)
20 September 2022 (72 *)
19 September 2022 (76 *)
Inter-row spacing [cm]
30
37.5
37.5
Intra-row spacing [cm]
10.5
15
8.5
8.6
RGB camera type
Sony ILCE-6000
Sony ILCE-6000
Mavic 2 Pro
Mavic 2 Pro
Flight height (RGB) [m]
16
20
10
10
RGB ground sampling
distance [cm]
0.16
0.23
0.24
0.24
Time of multispectral image
collection
13 h 12–13 h 27
13 h 20–13 h 27
12 h 25–12 h 35
10 h 49–10 h 54
Cloudiness
PC
CS
PCS
PCS
Flight height
(multispectral) [m]
30
30
12
30
Multispectral ground
sampling distance [cm]
2.08
2.08
0.83
2.08
Number of training pixels for
common bean
60,584
15,152
9049
1721
Number of training pixels for
D. stramonium
17,334
1779
3753
195
BBCH 7: development of crop fruit. * in days after planting.


Remote Sens. 2024, 16, 3538
4 of 24
Figure 1. Locations of all fields in Belgium. For every field, the RGB orthomosaic is shown, as well as
an example of a D. stramonium and common bean plant.
The datasets of Oudenaarde and Merelbeke were collected in 2020, and those of
Meulebeke and Houthulst in 2022. All fields had a sandy-loam soil structure [23]. For the
interpretation of the data, it is important to acknowledge that the growing conditions in
2020 and 2022 were different, with 2020 being a relatively normal year, although May was
very dry, whereas the summer of 2022 was extremely dry in July and August [24–26].
In Merelbeke, common bean was sown on 14 May 2020. Every third row was spaced
further apart (±0.8 m) to facilitate access. In total, nine rows with a length of 35 m and
three rows with a length of 13 m were sown. Datura stramonium was sown in plugs in a
greenhouse, in a pot substrate provided with NPK fertilizer (14:16:18), to prevent contami-
nation of the field with toxic weed seeds. Seedlings were transferred to the field between 29
June and 7 July when at least one true leaf had developed. The seedlings were monitored
and watered when necessary. Datura stramonium was not naturally present in this field,
but a total of 35 D. stramonium plants were planted manually on predetermined locations.
Different scenarios were simulated by selecting specific locations: plants positioned in
the center of two rows, encompassed by crops; plants situated within the crop row; and
D. stramonium plants clustering together. The field was manually harvested.
Datura stramonium was naturally present in all other fields. Positions of the D. stra-
monium plants in Meulebeke and Houthulst were measured with an RTK GNSS device
(S10, Stonex, Paderno Dugnano, Lombardia, Italy). In total, 34 and 90 D. stramonium plants
were present, respectively. In Oudenaarde, D. stramonium was more abundant, and the
location of every single plant could not be measured. Other weed species were virtually
not present in Meulebeke; in Houthulst, S. nigrum (black nightshade) was present in large
numbers. The GNSS device was used to measure the locations of approximately ninety S.
nigrum plants in order to not include these pixels when calculating performance metrics.
In Oudenaarde, the weeds Chenopodium album L. (lamb’s quarters), Solanum tuberosum L.
(potato), Cirsium arvense L. (creeping thistle), and Mercurialis annua L. (annual mercury)
were sporadically present.


Remote Sens. 2024, 16, 3538
5 of 24
2.2. Data Collection
Multispectral and RGB data were collected on all study sites. Multispectral images
were collected with the MicaSense RedEdge-MX Dual camera system (AgEagle Aerial
Systems Inc., Wichita, KS, USA). The MicaSense Dual camera system is a commercial
multispectral camera with ten bands (Table 2). The RGB camera, used in 2020, was a
Sony ILCE-6000 with a 35 mm lens (Sony Group Corporation, Tokyo, Japan). Cameras
were separately attached to a UAV (M600, Shenzhen DJI Sciences and Technologies Ltd.,
Shenzhen, Guangdong, China). The RGB camera was attached to a gimbal on the drone. In
2022, RGB images were taken with a built-in camera (Mavic 2 Pro, Shenzhen DJI Sciences
and Technologies Ltd., Shenzhen, Guangdong, China). The camera has a 1” CMOS sensor
with 20 MP and 28 mm lens (35 mm equivalent). The areas were mapped with the DJI
Ground Station Pro app. For all cameras, the frontal and sideward overlay was 80%. Flight
heights for all different flights are displayed in Table 1. In 2022, after the Houthulst flight, it
was decided to further decrease the flight height in order to optimize resolution. However,
preliminary results showed poor classification results for the Meulebeke field, and it was
decided to simulate a larger GSD that matched the other fields. Ground control points
(GCPs) were distributed over each study area and measured with a RTK GNSS receiver.
At the northern border of the study area in Oudenaarde, the UAV was flown manually to
minimize the risk of collision with trees, and the RGB camera was triggered manually as
well. The degree of cloudiness during multispectral data collection is provided in Table 1.
To correct the multispectral data for changing ambient light conditions, MicaSense provides
a downwelling light sensor (DLS) and a calibrated reflectance panel. The DLS was attached
on top of the drone. The ISO value, aperture, and shutter speed of the Sony camera were
set manually at 320, f/2.8, and 1/1250 s, respectively. Both the Sony camera and the camera
on the Mavic 2 Pro were triggered by the mission planner app; approximately every second
and every two seconds an image was made, respectively. Sony images were saved in RAW
and JPEG format, and Mavic images in JPEG and DNG format.
2.3. (Pre-)Processing
Irrelevant images were removed (e.g., images taken during take-off and landing). JPEG
images were processed with Agisoft Metashape version 1.8.4 (Agisoft LLC, St. Petersburg,
Russia) using default settings. GCPs were used to georeference RGB and multispectral
(only in 2022) orthomosaics. For the field in Oudenaarde, a better multispectral orthomosaic
was obtained using only camera GNSS measurements (no RTK GNSS). The image was
later georeferenced in QGIS (version 3.24.2) with the help of the RGB orthomosaic. The
same method was used for the orthomosaics of the field in Merelbeke. In 2022, both
multispectral and RGB orthomosaics were georeferenced in Agisoft with the help of the
GCPs. Reflectance of the multispectral images was calculated using the workflow provided
by Agisoft [27]. Orthomosaics containing reflectance values and RGB orthomosaics were
exported to QGIS in TIFF format; the RGB orthomosaic of the field in Oudenaarde was
divided in separate blocks of 1000 × 1000 pixels to reduce file size. RGB orthomosaics were
only used as a visual aid, and no reflectance values were obtained. GSDs of all multispectral
images are displayed in Table 1. All reflectance orthomosaics were exported from QGIS
with identical resolution for further analysis, i.e., 2.08 cm, with the default resampling
method, which is the nearest neighbor [28].
Plant polygons were drawn manually on the reflectance orthomosaics of all fields in
QGIS to select D. stramonium and common bean pixels with the help of the RGB orthomosaic
and saved as a shape file. The numbers of training pixels are provided in Table 1. Another
shape file was created containing a polygon delineating the border of the study area and
was used to clip the orthomosaic (Figure 2c). All files were subsequently exported to Python
(version 3.9.12) for further processing. The packages OpenCV [29] (for raster calculations)
and scikit-learn [30] (for machine learning analyses) were used.


Remote Sens. 2024, 16, 3538
6 of 24
Figure 2. Schematic overview of all analyses. (a) Multispectral orthomosaic, (b) orthomosaic with excess-green index, (c) polygon delineating study area, (d) binary
orthomosaic with vegetation (white) and soil (black), (e) classified orthomosaic, (f) illustration of the post-processing procedure for two circular polygons with
a four-pixel threshold. Analyses I and II show the southern part of the Oudenaarde dataset. All steps of analysis I were also made for the other three locations.
Analyses III and IV illustrate the classification result for the Houthulst dataset. All steps were also made for the other two (in case of analysis III) or three (in case of
analysis IV) locations.


Remote Sens. 2024, 16, 3538
7 of 24
Table 2. Characteristics of the RedEdge-MX Dual camera system [31].
Band Number
Band Name
[-]
Center Wavelength
[nm]
Band Width
[nm]
1
Coastal blue
444
28
2
Blue
475
32
3
Green
531
14
4
Green
560
27
5
Red
650
16
6
Red
668
14
7
Red edge
705
10
8
Red edge
717
12
9
Red edge
740
18
10
Near IR
842
57
The excess-green index [32], calculated as ExG = 2 Green4-Red6-Blue2 (subscripts
indicate band numbers of the multispectral camera, Table 2), was used to isolate vegetation
from background (Figure 2b). Otsu’s method [33] was used to create a binary mask from the
excess-green index map (Figure 2d). This mask was combined with the plant polygons to
classify pixels as D. stramonium or common bean. The reflectance data were then extracted
from the classified pixels and were used as input in machine learning models for binary
classification.
In a preliminary phase, logistic regression, random forest, and support vector machine
were tested. Hyperparameters of the random forest and support vector machine models
were tuned using a randomized search of the parameter space. Logistic regression was
performed without regularization and default settings, and either outperformed or per-
formed equally well as other tested models, but with faster execution times. Therefore,
only the results from logistic regression are further included. Logistic regression is a simple
algorithm that is easy to implement and makes fast predictions. It performs well with
smaller datasets, whereas complex models often need a large amount of data to tune their
hyperparameters effectively. Therefore, logistic regression is a suitable choice for this study.
2.4. Post-Processing
The classification maps generated according to the procedure described in Section 2.3
are pixel based (Figure 2e). Given the large number of pixels in the orthomosaic, even a
model with a very high precision (very low number of false positives (FP)) would still
result in a large number of false positive pixels—in this case, of bean pixels wrongfully
classified as D. stramonium. These pixels are however often isolated or in very small groups,
in contrast with pixels of real D. stramonium plants, which are identified as larger clusters
of pixels. Hence, a further processing step was needed to take a decision on which group
of pixels actually represents D. stramonium.
To remove isolated ‘false positive’ pixels, a median filter, replacing the central pixel of
a kernel (of size 3) with the median value, was used to smooth the original classification
map. Then, in order to create a performance measure, pixels classified as D. stramonium
were counted. As there was a misalignment between the reflectance and RGB orthomosaic,
only pixels inside a small circular area were counted. Classification maps were imported
in QGIS, and circular polygons were drawn around D. stramonium and common bean
plants (Figure 2f). For the circles, a diameter of 0.4 m was chosen as it covers most of the
D. stramonium plants and accommodates for the minor misalignments. For the Oudenaarde
field, a random subset of D. stramonium and common bean plants was selected. Circles
were randomly placed over the study area using a randomized QGIS algorithm. Circles
assigned to D. stramonium were moved manually to the closest D. stramonium plant based
on the RGB orthomosaic. Circles for common bean were visually checked to not include
any D. stramonium pixels. Subsequently, pixels classified as D. stramonium were counted
in each circle with the use of the zonal statistics tool. Different threshold values of the


Remote Sens. 2024, 16, 3538
8 of 24
total number of D. stramonium pixels per circular polygon were defined to categorize a
circle as D. stramonium, and performance metrics were calculated. Metrics used in this
study were recall, which is the fraction of correctly classified D. stramonium plants; true
negative rate (TNR), which is the fraction of correctly classified common bean plants;
precision, the fraction of appointed D. stramonium plants that are truly D. stramonium plants;
and F1-score, the harmonic mean of precision and recall. For the purpose of enabling
comparisons between various outcomes, alternative metrics were computed using varying
pixel threshold values. This way, applying different threshold values can result in diverse
outcomes for a single classification map. Increasing the threshold value consistently leads
to reduced recall and increased TNR. To compare recall values, the threshold value was
adapted until TNRs were equal.
Additionally, the size of the D. stramonium plants in the field were estimated by
drawing their circumference on the RGB orthomosaic. Only pixels from visible plant parts
were included. In Merelbeke and Meulebeke, all D. stramonium plants were measured,
whereas for the fields in Houthulst and Oudenaarde, a subset of 50 D. stramonium plants
was randomly selected.
2.5. Image Analysis
Four analyses were performed in this research to fulfill the objectives:
I.
The development and application of logistic regression models utilizing reflectance
data acquired from the same common bean field for assessing the spectral discrimi-
native capacity between common bean and D. stramonium.
II.
The discriminative capacity was again investigated for varying simulated ground
sampling distances to examine the influence on classification performance.
III.
Examination of the generalization of a model created in analysis I by evaluating
its performance on unseen data from multiple distinct common bean fields. To
address differences between datasets, VI were incorporated in the dataset and/or
CDF-corrected data was used.
IV.
Examination of the generalization of leave-one-group-out cross-validation (LOGO
CV) models using multispectral data and VI, as well as the application to CDF-
corrected data to test whether classification performance increases when spectral
data from multiple common bean fields are combined.
Figure 2 provides a schematic overview of these analyses.
2.5.1. Spectral Distinctness of D. stramonium and Common Bean
The key question here is whether both species can be spectrally discriminated. This
was done by training a separate model per site. For the field of Oudenaarde, enough
D. stramonium plants were present to split the area in a training and a validation part.
The study area was divided by a spray track in a northern section, which was used for
training, and a southern section, used for validation. Datura stramonium plants grew very
densely in the northern part, with plants attaining a large-statured growth, making it
well-suited for obtaining pure weed pixels. Training data of D. stramonium were primarily
obtained from regions where the plants grouped together. The dataset was not balanced,
with bean reference data outnumbering D. stramonium data. The imbalance in the dataset
was approached pragmatically: logistic regression models were run with and without a
correction for the mild imbalance. Visual inspection of the classified maps (of the northern
section) showed, however, that the balanced datasets led to an increase in FP, i.e., common
bean pixels classified as D. stramonium. Hence, the imbalance was not corrected in any of
the models. For both D. stramonium and common bean, one hundred circular polygons were
drawn on the northern and on the southern area of the Oudenaarde field (400 polygons
in total).
For the fields of Meulebeke, Merelbeke, and Houthulst, training data were obtained
from D. stramonium plants that were visually distinguishable on the reflectance orthomosaic
and marking areas of pure pixels. This methodology was used as there was no perfect


Remote Sens. 2024, 16, 3538
9 of 24
overlay between the RGB and reflectance orthomosaic. This resulted in training data from
thirty-two, fourteen, and eleven D. stramonium plants, respectively. For the Houthulst field,
weeds and crops were hard to distinguish. Hence, the amount of training data was low. For
common bean, one hundred polygons were drawn. For D. stramonium, the polygons were
drawn around the GNSS measurements. The best pixel threshold value with the highest
recall value in the training data of Oudenaarde was applied to the other fields. Recall
was selected as the decision-making metric because misclassifying D. stramonium could
result in crop contamination, posing a public health risk. The F1-score was provided for
completeness; however, the score was not used to make decisions.
Ref. [34] explains that, in some data types, values of nearby observations can have
the tendency to be more similar than values of distant observations, and when data are
drawn from this dependence structure (e.g., data that is close in space and/or time), the
independence of evaluation data can be compromised [35], producing overly optimistic
estimates of prediction error. Data from geographically distinct locations can be used to
evaluate a model [34]. As mentioned, models for Meulebeke, Merelbeke, and Houthulst
were generated using the training data specific to each field and subsequently applied to the
corresponding orthomosaic. Consequently, the outcomes represent training scores rather
than validation scores. Throughout the remainder of this study, the term ‘training’ will
denote the model’s application to observed data, ‘validation’ will refer to the application of
the model to unseen data within the same field, and ‘test’ will pertain to unseen data from
a different field. The training scores attained by the individual models can be regarded
as the optimal outcome with this particular dataset and logistic regression as the model
type and can be used as a reference. Test scores, on the other hand, represent an unbiased
estimate of the model behavior in unknown situations.
2.5.2. The Impact of Ground Sampling Distance on Classification Performance
The multispectral image from the field in Oudenaarde was exported from QGIS with
three different ground sampling distances: 2.68 cm, 3.35 cm, and 4.10 cm, simulating flight
heights of 40 m, 50 m, and 60 m, respectively. For a 200 m × 200 m square field, raising the
flight height to the aforementioned heights resulted in 22%, 34%, and 44% reductions in
UAV flight duration according to the mission planner app, respectively. The analyses of
Section 2.5.1 for Oudenaarde were repeated using these adapted multispectral images. For
each GSD, a different pixel density threshold value was obtained from the training data.
2.5.3. Generalization of the Oudenaarde Model
The model of the field in Oudenaarde, created with the largest dataset, was selected
for application to unseen data of the other fields. Firstly, the Oudenaarde model (from
Section 2.5.1) was applied to the uncorrected orthomosaic (R-U) of the test fields. However,
different growth conditions can impact reflectance values. The extremely dry period in
August 2022 in particular could have induced stress in plants during flowering, leading to
alterations in their spectral characteristics. It has been reported that stress during flowering
has a large impact on the growth of bush beans [36]. Subsequently, two distinct approaches
were employed to reduce/remove variation between datasets caused by extraneous effects:
the utilization of VI and CDF-correction.
The data of the three test fields were corrected so their CDFs matched the data from
Oudenaarde. CDFs were created for each band of the multispectral test images using data
classified as vegetation by a binary image (see Section 2.3). A one-dimensional interpolating
spline was created using defaults settings with the Python package SciPy [37]. The inverse
of the CDF of the Oudenaarde data was created similarly. All bands of the test images were
subjected to their respective CDFs and the output was used in the inverse CDF to return
reflectance values, as follows:
ρcorrected = CDF−1
Oudenaarde, i

CDFtest f ield, i(ρ)



Remote Sens. 2024, 16, 3538
10 of 24
with ρ being the reflectance of the multispectral test image and i being the band number
(Table 2). The CDF-corrected orthomosaics (R-CDF) were classified using the Oudenaarde
model, and the result was multiplied with the binary vegetation mask.
Additionally, VIs were selected that amplify the vegetation signal while minimizing the
impact of solar irradiance, soil background effects, varying illumination, and atmospheric
conditions (Table 3). These indices were added as additional channels to the orthomosaic.
Training pixels of the Oudenaarde field, including VIs and the original reflectance values,
were included in a new logistic regression model with nineteen features and applied to
each test orthomosaic (VI-U).
Finally, both correction methods were combined: the new logistic regression model
(with VI) was applied to CDF-corrected test orthomosaics (VI-CDF). Subsequently, the
results were subjected to the post-processing procedure described in Section 2.4.
Table 3. Vegetation indices used in leave-one-group-out cross-validation. Subscripts in the formula
indicate band numbers described in Table 2.
Abbreviation
Name
Formula
Reference
NDVI
Normalized difference vegetation index
NIR10−RED5
NIR10+RED5
[38]
SAVI
Soil adjusted vegetation index
(NIR10−RED6)*(1+L)
NIR10+RED6+L
[39]
MSAVI
Modified soil adjusted vegetation index
2*NIR10+1−
q
(2*NIR10+1)2−8*(NIR10−RED6)
2
[40]
SR
Simple ratio
NIR10
RED6
[41]
DVI
Difference vegetation index
NIR10 −RED6
[38]
RDVI
Renormalized difference vegetation index
√
NDVI*DVI
[42]
VARI
Vegetation atmospherically
resistant index
GREEN4−RED6
GREEN4+RED6−BLUE2
[43]
NDRE
Normalized difference red edge index
NIR10−REDEDGE7
NIR10+REDEDGE7
[44]
GNDVI
Green normalized difference vegetation index
NIR10−GREEN3
NIR10+GREEN3
[45]
2.5.4. Generalization by Leave-One-Group-Out Cross-Validation
A logistic regression model was created with nineteen features using reflectance data
and VI from three locations as input. LOGO CV was performed for every field. The created
model was applied to the CDF-corrected multispectral orthomosaic of the omitted test field.
Subsequently, the results were subjected to the post-processing procedure described in
Section 2.4. For the Oudenaarde field, only data from the southern part was included.
3. Results
3.1. Vegetation Analysis
The mean plant size of the D. stramonium plants in the field of Meulebeke (var. tatula)
was 0.068 m2 (σ = 0.039). They had the largest mean plant size of all fields. All D. stramonium
plants had leaves extending above the crop canopy. The field almost achieved full canopy
closure. The D. stramonium plants from the field in Oudenaarde had the second largest
mean plant size (µ = 0.038 m2, σ = 0.020). The canopy consisted of healthy vegetation
and was fully closed except for some spots at the edges of the canopy. In Merelbeke, the
plant size was more variable (µ = 0.035 m2, σ = 0.051) due to the different planting dates.
Seedlings planted later in the season were often at least partly overgrown by common
bean. Seven D. stramonium plants were not visible on nadir looking RGB imagery and were
omitted in further analyses. Due to the wider inter-row spacing, the vegetation did not
achieve full closure, leaving a significant amount of bare soil exposed. The weeds in the
Houthulst field were substantially smaller (µ = 0.018 m2, σ = 0.012). The common bean
plants were stunted, leaving bare soil exposed between and in the rows.
Within all combinations of bands and locations, D. stramonium had a higher median
reflectance than common bean (Figure 3). Reflectance values of both species were very
low for the field of Merelbeke. After CDF matching, median reflectance values exhibited


Remote Sens. 2024, 16, 3538
11 of 24
a narrower range. Especially for common bean, CDF matching was able to align median
reflectance values for the different locations. Median reflectance values of D. stramonium
for the field in Houthulst were substantially higher than at other locations, which was not
the case for common bean. For the Meulebeke field, median reflectance of D. stramonium,
i.e., from var. tatula, was slightly higher for bands 9 and 10 after CDF matching.
Figure 3. Box plots with the reflectance of common bean and D. stramonium at different locations
before (top) and after (bottom) CDF matching.
3.2. Spectral Distinctness of D. stramonium and Common Bean
The results from analysis I are provided in Table 4. In the Oudenaarde dataset, training
recall exhibited a relatively high value at the single pixel threshold level (0.96) and showed
a gradual decline when the threshold value increased. When a threshold of 1 was used (i.e.,
a polygon is classified as D. stramonium if at least one single pixel inside the polygon is
classified as D. stramonium), 51% of the common bean plants were incorrectly categorized as
D. stramonium plants. Increasing the threshold value resulted in a slight reduction in recall,
but significantly increased the TNR as well as the precision and F1-score. The optimal
threshold was four pixels, since the recall of the training data start to decline at a threshold
value of five pixels. At this threshold value, the precision was 74%.
A threshold of four pixels resulted in a precision of 95% for the validation dataset. FP
were visually inspected on the RGB orthomosaic of the northern part of the Oudenaarde
field to see if other weed species might have been the reason for misclassification. However,
this was not the case.
For the field in Meulebeke, TNR was rather low (0.72). It is noteworthy that the three
smallest D. stramonium plants in the field were not correctly classified. Overall, the incor-
rectly classified D. stramonium plants were smaller in size. The Houthulst field obtained
a very high TNR (0.97), but recall was very low (0.53). A total of 36 of the 42 incorrectly
classified weeds exhibited a smaller than average plant size. For the Merelbeke field, only
10 out of 28 D. stramonium plants were classified correctly. The seven largest D. stramonium
plants were classified correctly.
A threshold value of eleven pixels removed a great deal of FP from the Meulebeke
classification map. This large threshold value indicates that there were numerous small
patches that were incorrectly classified as D. stramonium plants. However, the large majority
of D. stramonium pixels were classified correctly, resulting in a recall of 88%.


Remote Sens. 2024, 16, 3538
12 of 24
Table 4. Results from analysis I (assessing the spectral discriminative capacity between common
bean and D. stramonium by the development and application of logistic regression models). Recall,
TNR: true negative rate, precision, and F1-score are indicated for different locations and pixel density
threshold values. Threshold is the number of pixels classified as D. stramonium needed to classify a
polygon as a D. stramonium plant.
Location
Dataset
Threshold
[Pixels]
Recall
TNR
Precision
F1
Oudenaarde
Training
1
0.96
0.49
0.65
0.78
2
0.96
0.56
0.69
0.80
3
0.96
0.62
0.72
0.82
4
0.96
0.67
0.74
0.84
5
0.95
0.74
0.79
0.86
6
0.94
0.75
0.79
0.86
Validation
4
0.99
0.95
0.95
0.97
Meulebeke
Training
4
0.91
0.72
0.53
0.67
11
0.88
0.93
0.81
0.85
16
0.88
0.96
0.88
0.88
Houthulst
Training
4
0.53
0.97
0.94
0.68
Merelbeke
Training
4
0.36
0.92
0.56
0.43
5
0.36
0.94
0.63
0.45
3.3. The Impact of Ground Sampling Distance on Classification Performance
Results from analysis II are provided in Table 5. For a GSD of 2.68 cm, a two-pixel
threshold value worked best, whereas for GSDs of 3.35 cm and 4.10 cm, one pixel was
chosen as the threshold that maximizes recall. The validation recall values were 97%, 94%,
and 85%, respectively, and the validation TNRs were 95%, 96%, and 95%, respectively.
Despite the decrease in recall, TNR remained stable with increasing flight height.
Table 5. Results from analysis II (examining the influence of ground sampling distance on model
performance). Recall, TNR: true negative rate, precision, and F1-score are indicated for different
ground sampling distances and pixel density threshold values.
(Simulated) Flight
Height [m]
Ground Sampling
Distance [cm]
Dataset
Threshold
[Pixels]
Recall
TNR
Precision
F1
30
Training
1
0.96
0.49
0.65
0.78
2
0.96
0.56
0.69
0.80
3
0.96
0.62
0.72
0.82
2.01
4
0.96
0.67
0.74
0.84
5
0.95
0.74
0.79
0.86
6
0.94
0.75
0.79
0.86
Validation
4
0.99
0.95
0.95
0.97
40
Training
1
0.91
0.61
0.70
0.79
2
0.91
0.67
0.73
0.81
2.68
3
0.90
0.78
0.80
0.85
4
0.89
0.83
0.84
0.86
Validation
2
0.97
0.95
0.95
0.96
Training
1
0.85
0.83
0.83
0.84
2
0.83
0.86
0.86
0.84
50
3.35
3
0.78
0.87
0.86
0.82
4
0.75
0.90
0.88
0.81
Validation
1
0.94
0.96
0.96
0.95
60
Training
1
0.78
0.83
0.82
0.80
2
0.73
0.87
0.85
0.78
4.10
3
0.66
0.88
0.85
0.74
4
0.62
0.93
0.90
0.73
Validation
1
0.85
0.95
0.94
0.89


Remote Sens. 2024, 16, 3538
13 of 24
3.4. Generalization of the Oudenaarde Model
Results from analysis III are provided in Table 6 and Figures 4 and 5b–d. Here, four
different approaches were taken: (i) the approach when the model was constructed with the
reflectance data as input, without any corrections (R-U); (ii) a model constructed applying
reflectance and VI, without corrections (VI-U); (iii) the model, applied to CDF-corrected
orthomosaics (R-CDF); and (iv) the model with reflectance data and VI applied to CDF-
corrected orthomosaics (VI-CDF). For all results, a four-pixel threshold was used as this was
found to be a good threshold value in the training and validation datasets of Oudenaarde
(Section 3.2). In some cases, an alternative result with another threshold value is also shown
for comparison.
Figure 4. (a) RGB orthomosaic of a section of the field in Merelbeke. Classified image of that section
using (b) the uncorrected orthomosaic (R-U), (c) the CDF-corrected orthomosaic (R-CDF), (d) the
CDF-corrected orthomosaic and a model including vegetation indices (VI-CDF), and (e) leave-one-
group-out cross-validation (LOGO CV). Brown (D. stramonium) and white (common bean) circles
used to calculate performance metrics are shown.


Remote Sens. 2024, 16, 3538
14 of 24
Figure 5. (a) RGB orthomosaic of a section of the field in Houthulst. Classified image of that section
using (b) the uncorrected orthomosaic (R-U), (c) the CDF-corrected orthomosaic (R-CDF), (d) the
CDF-corrected orthomosaic and a model including vegetation indices (VI-CDF), and (e) leave-one-
group-out cross-validation (LOGO CV). Brown (D. stramonium) and white (common bean) circles
used to calculate performance metrics are shown.
Table 6. Test results from analysis III (improving model generalization by incorporating the use
of vegetation indices and applying cumulative distribution function matching). Recall, TNR: true
negative rate, precision, and F1-score are indicated for different locations, methods, and pixel density
threshold values.
Location
Method
Threshold
[Pixels]
Recall
TNR
Precision
F1
Meulebeke
R-U
4
1.00
0.00
0.25
0.40
VI-U
4
1.00
0.23
0.31
0.47
R-CDF
4
0.41
0.87
0.52
0.46
10
0.09
0.93
0.30
0.14
VI-CDF
4
0.26
0.93
0.56
0.36
Houthulst
R-U
4
0.06
0.95
0.50
0.10
VI-U
4
0.01
1.00
1.00
0.02
R-CDF
4
0.80
0.76
0.75
0.77
22
0.38
0.97
0.92
0.54
VI-CDF
4
0.80
0.81
0.79
0.80
14
0.52
0.97
0.94
0.67
Merelbeke
R-U
4
1.00
0.00
0.22
0.36
VI-U
4
0.00
1.00
-
0.00
R-CDF
4
0.54
0.66
0.31
0.39
27
0.11
0.92
0.27
0.15
VI-CDF
4
0.54
0.69
0.33
0.41
12
0.21
0.92
0.43
0.29
R-U: Application of the Oudenaarde model with reflectance data applied to the uncorrected orthomosaic. VI-U:
Application of the Oudenaarde model with reflectance data and vegetation indices applied to the uncorrected
orthomosaic. R-CDF: Application of the Oudenaarde model with reflectance data applied to the CDF-corrected
orthomosaic. VI-CDF: Application of the Oudenaarde model with reflectance data and vegetation indices applied
to the CDF-corrected orthomosaic.


Remote Sens. 2024, 16, 3538
15 of 24
The R-U approach resulted in poor classification. In Merelbeke, the whole field was
classified as D. stramonium (Figure 4b). Similarly for the field in Meulebeke (classification
maps not shown), more than half of the field was classified as D. stramonium, with shaded
crop pixels all being classified as D. stramonium. This resulted in a TNR of zero. For
the field in Houthulst, recall was very poor (0.06) (Figure 5b). The inclusion of VI in the
model (VI-U) did not yield a substantial improvement in classification performance. CDF
matching, on the other hand, improved precision for the fields of Meulebeke and Merelbeke,
and it improved recall for Houthulst. By applying CDF matching, the classification map
of Merelbeke clearly shows the circumference of various leaves of D. stramonium plants
(Figure 4c). However, there are a lot of false positive pixels at the north-eastern border
of the canopy. The combination of VI and CDF matching (VI-CDF) slightly improved
TNR and precision for all the test fields relative to the former method (Figures 4d and 5d).
Recall decreased for the Meulebeke field and was unaffected for the fields of Houthulst
and Merelbeke.
Across all fields, the best results for analysis III were achieved by VI-CDF. In Meule-
beke, this resulted in a recall of 26% (TNR adapted to match results of analysis I). Five of
the (nine) correctly classified D. stramonium plants had a higher-than-average plant size.
In Houthulst, recall was 52%, with the majority of the correctly classified D. stramonium
plants having a larger than average plant size. In Merelbeke, recall was 21%, and the three
largest weeds were correctly classified. However, four D. stramonium plants with a larger
than average plant size were not correctly classified.
3.5. Generalization by Leave-One-Group-Out Cross-Validation
Table 7 shows the results for the LOGO CV, using VI and reflectance data as input data.
Test results for the field in Oudenaarde, employing a five-pixel threshold, were identical
to the validation results. In the case of Meulebeke, all performance metrics improved in
comparison to the best method of analysis III. With a TNR of 96% and a recall of 44%, ten
out of thirteen D. stramonium plants with a larger than average plant size were correctly
classified. In the case of Houthulst, recall decreased slightly in comparison to VI-CDF
(0.49 vs. 0.52, with TNR = 0.97). Of the 21 D. stramonium plants with a larger than average
plant size, 19 were correctly classified. For the Merelbeke field, no threshold value could
be obtained to match the TNR from analysis III. However, at a four-pixel threshold value,
TNR was almost identical (0.69 vs. 0.70). With this threshold value, recall increased. Again,
of the eight D. stramonium plants with a larger than average plant size, six were correctly
classified. Overall, LOGO CV with inclusion of VI and application to a CDF-corrected
orthomosaic proved to be the best method.
Table 7. Test results from analysis IV (improving model generalization by combining spectral
data and vegetation indices from multiple agricultural fields with the use of leave-one-group-out
cross-validation). Recall, TNR: true negative rate, precision, and F1-score are indicated for differ-
ent locations.
Location
Threshold
[Pixels]
Recall
TNR
Precision
F1
Oudenaarde
4
0.99
0.92
0.93
0.96
5
0.99
0.95
0.95
0.97
Meulebeke
4
0.44
0.96
0.79
0.57
Houthulst
4
0.76
0.82
0.79
0.77
11
0.49
0.97
0.94
0.64
Merelbeke
4
0.61
0.70
0.36
0.45
16
0.21
0.94
0.50
0.30
For the field of Merelbeke, to compare results from LOGO CV and the training scores,
a TNR of 94% was also calculated. For the fields of Oudenaarde, Meulebeke, Houthulst,


Remote Sens. 2024, 16, 3538
16 of 24
and Merelbeke, relative weed detection rates of 100% (99/99), 50% (15/30), 92% (44/48),
and 60% (6/10) were obtained, respectively (calculated as the ratio of the number of
D. stramonium plants detected with LOGO CV and during validation (for Oudenaarde) or
training (for the test fields), each with a threshold value so TNR is equal for both methods).
Regression coefficients from LOGO CV are provided in Figure 6. Although the most
important features were the same for each field, their absolute values differed. The most
important VI in the models were RDVI and MSAVI. The coefficients of bands 1 (Coastal
blue) and 7 (Red edge) were the most important.
Figure 6. Regression coefficients of all features from the models created with LOGO CV. The graph’s
title indicates the field that was omitted in the model and to which the model was applied.
4. Discussion
The first objective of this study was to assess the spectral discriminative capacity
between common bean and D. stramonium by the development and application of a logistic
regression model for each individual common bean field. The scores from analysis I (Table 4)
confirm that D. stramonium and common bean are multispectrally separable, y-awith
D. stramonium having a higher spectral reflectance across all bands (Figure 3). To distinguish
false positive pixels from D. stramonium, a size-dependent threshold was used, assuming
larger groups of classified D. stramonium pixels are more likely truly D. stramonium plants.
As the industry applies a zero-tolerance policy and the study pertains to public health, the
recall was given priority over the TNR, and a four-pixel threshold was found optimal for
the field in Oudenaarde. Specifically, if it results in fewer missed D. stramonium plants, it is
favorable to categorize more common bean plants as D. stramonium. However, TNR and
precision are still important. If there are two million crop plants in a field, a TNR of 67%
would require 660,000 unnecessary checks, rendering the obtained result no more effective
than scanning the entire field. Likewise, a precision of 74% means a fourth of the labor time
will be dedicated to unproductive fieldwork. However, pixels of correctly classified solitary
D. stramonium plants in the Oudenaarde field often displayed a distinct grouping pattern,
attributed to the architectural features of D. stramonium. This was also the case in the test
field of Merelbeke, which can be observed in Figure 4c–e. However, this pattern can only
be observed when D. stramonium plants are large enough and leaves extend above the crop
canopy, which was not the case in Houthulst (Figure 5). In addition, visual inspection of


Remote Sens. 2024, 16, 3538
17 of 24
the classified image of Oudenaarde shows that incorrectly classified crop pixels tend to
cluster around the field’s edges where plant coverage is not 100%. Consequently, human
interpretation of the classification map is still necessary. However, since the removal of the
D. stramonium plants is still performed manually, this should not pose a problem in fields
with uniform plant distribution.
A possible explanation for the higher validation scores (than training scores) in Oude-
naarde (Table 4) is the manual flight of the UAV over the northern section of the field,
which resulted in a greater number of images and an increased image overlay. During
this flight, the weather was mostly cloudy, which could have caused significant variations
in incoming radiation. In [46], surface reflectance under overcast conditions was more
accurately calculated without DLS corrections as the sensor is sensitive to the orientation
of the sun. Inadequate calculation of the surface reflectance could have led to differences
in reflection between the selected training pixels and the rest of the northern part of the
field. As the training pixels only represent a small portion of the entire northern region,
this discrepancy could have contributed to the lower scores observed in the training set.
It should be noted that performance metrics in Oudenaarde might be overestimated as
the positions of the D. stramonium plants in Oudenaarde were not measured with a GNSS
device and, hence, small, overgrown weeds might have been overlooked.
The lower scores in Merelbeke and Houthulst were due to the fact that D. stramonium
plants were small and partially overgrown by beans. However, detecting these plants
as well is important, since the industry still fears small weeds, as the coil springs of the
harvester, responsible for pulling off the green pods and leaves, work at a height of 3–5 cm
above the ground and time between flowering and fruiting of these small D. stramonium
plants can be less than a week [47]. Smaller plants first of all resulted in fewer pure pixels:
while selecting D. stramonium pixels, only a limited number of pixels could unmistakably
be selected. This also explains the high reflectance values of the Houthulst field (Figure 3).
The analyses also confirmed that larger plants, with several pure pixels clustered together,
were consistently better detected. Second, in the visual region, it is not possible to see
through the canopy, so it is unrealistic to expect that overgrown plants can be detected.
Reference [48] conducted research on subcanopy species detection and discovered that the
detection rate decreased quickly as the canopy openness decreased, and no species were
detected when the canopy was nearly fully closed (<10%). Their study reports increased
detection rates when using oblique imagery. This could potentially be useful for identifying
smaller, partially hidden weed plants. An alternative approach is to schedule flights earlier
in the season compared to the current industry standard of conducting visual scouting
a few days before harvest. Common bean plants would be smaller and D. stramonium
plants less overgrown. Nonetheless, accurately monitoring these small weeds would mean
flying at lower heights, thereby substantially increasing the time required for field scanning.
Consequently, a trade-off has to be made by the industry.
So, although D. stramonium and common bean proved to be multispectrally distin-
guishable using UAV images, small, partly overgrown weeds were overlooked, and the
authors suggest to either use oblique imagery or fly early in the growing season. The last
approach, however, increases flight duration.
The second objective of this study was examining the influence of ground sampling
distance (GSD) on model performance. An increase in flight height to 40 m (2.68 cm GSD)
could be considered for this application. Depending on the available time, the threshold can
be reduced to one pixel, which may result in an increase in FP. However, according to [49],
resampling should be conducted using a weighted average based on the point spread
function of the sensor. The point spread function of an optical system is the irradiance
distribution that results from a single point source (Goodman, 2005). However, the point
spread function of the MicaSense sensor is not available, and the calculation is not within
the scope of this study. Simulated imagery might be unrealistically sharp and the obtained
results optimistic. Hence, obtaining imagery with a GSD of 2.08 cm or smaller for D.
stramonium plants of similar size than measured in Oudenaarde (µ = 0.038 m2, σ = 0.020)


Remote Sens. 2024, 16, 3538
18 of 24
might be suggested. On the other hand, UAVs and sensors are continuously being improved
with larger spatial resolutions. In the coming years, these cameras could potentially reduce
flight duration while simultaneously increasing its resolution. The current strategy’s
drawback is the use of a single threshold value for an entire field as this threshold value
should depend on the size of the D. stramonium plants. A plant-size-dependent flight height
might be appropriate; only decreasing flight height for fields infested with small weeds.
Flight height can also be decreased in areas with irregular germination of common bean or
at field borders. A larger GSD increases the number of D. stramonium pixels of each plant
on the multispectral orthomosaic, and this could increase the number of correctly classified
D. stramonium pixels. As correctly classified D. stramonium pixels often manifest as different
contiguous patches and misclassified common bean pixels as smaller solitary patches, an
object-based detection method, to account for the plant’s architecture, could be applied
after classification. The fusion of object-based and pixel-based methods indeed yielded
promising results in the detection of bindweeds (Convolvulus), C. album, and Digitaria
sanguinalis (crabgrass) in maize [50].
The third and fourth objectives of this study aimed at detecting D. stramonium plants in
a location without using training data from that specific location. Variations in reflectance
between different fields can be caused by soil reflectance, which are enhanced for discon-
tinuous canopies [51]. Furthermore, differences in reflectance observed between datasets
captured on different days and at varying flight heights may be attributed to variations
in both illumination and atmospheric conditions. Adding to this complexity, variations
in reflectance measurements may be attributed to both biotic and abiotic stressors. For
instance, ref. [52] observed increases in reflectance and a reduction in absorption within
the 695–725 nm wavelength range due to stress-induced factors. The most important VI
for discriminating between D. stramonium and common bean in the LOGO CV models
were RDVI and MSAVI. Considering the varying soil moisture levels and canopy densities
in different fields, it is reasonable to expect that a vegetation index less sensitive to these
factors would emerge as the predominant choice.
Bands 1 (Coastal blue) and 7 (Red edge) contributed the most to the LOGO CV model
(Figure 6). The red edge region of the electromagnetic spectrum has been found to be of
great importance for species discrimination in various vegetation studies [53]. Refs. [54,55]
found that the red-edge spectral band (691–785 nm) is among the most important bands for
distinguishing tree species. In addition, ref. [56] has highlighted the importance of the red
edge position (715 nm) in discriminating between an invasive weed and four co-occurring
plant species. Ref. [57] used a random forest classifier to discriminate between Cyperus
esculentus L. (yellow nutsedge) and two co-occurring weed species; feature importance of
bands around the red edge was significantly higher than for other wavelengths. On the
other hand, blue wavelengths have also been labeled important for species discrimination.
Ref. [58] found that wavelengths in the blue region of the spectrum (405, 410, and 430 nm)
are frequently selected for discrimination models. Ref. [59] discriminated between sugar
beet and weeds, and maize and weeds, finding that the selected wavelength ratios were
often in the visible wavelength range and around 800 nm.
Incorporating data from diverse fields improved classification results for Meulebeke
and Merelbeke with comparison to VI-CDF. Only for the Houthulst field was VI-CDF
slightly better. In comparison with the training scores, LOGO CV performed really well for
the Oudenaarde (1.00) and Houthulst (0.92) fields regarding the relative weed detection rate.
However, for the field in Meulebeke, this was substantially poorer, with a relative weed
detection rate of only 50%. One of the possible reasons is that the D. stramonium plants in this
field belonged to a different variety (Table 1). Ref. [7] showed that hyperspectral reflectance
of the two D. stramonium varieties (Datura stramonium var. tatula & var. stramonium) and
common bean differed sufficiently to be classified accordingly. In addition, preliminary
results showed both D. stramonium varieties also differ sufficiently from each other to be
classified accordingly [60]. Datura stramonium var. tatula was indeed not included in the
training set. Other data with this botanical variety should be included in the model to


Remote Sens. 2024, 16, 3538
19 of 24
improve results. In addition, the relative weed detection rate of the Merelbeke field was
rather poor (0.60). However, the total number of D. stramonium plants was rather low, and a
slight difference in the detected D. stramonium plants generates a large difference in relative
weed detection rate.
While the fields of Oudenaarde and Houthulst were accurately classified using data
from other fields, this was not the case for Meulebeke and Merelbeke. These diverse
outcomes highlight the importance of conducting tests in diverse fields and under varying
conditions. In literature, most UAV-based weed detection studies randomly select subsets
of the dataset to train, validate, and test a model [61–72]. Some authors divided the field
in different sections [73–76] or used two neighboring fields [77]. No study could be found
that applies a model to an independent test set, where this dataset is clearly separated in
space and/or time from the training dataset.
The third and fourth objectives of this study show that it is possible to detect D. stra-
monium in common bean fields with a model that was not trained with data from that field.
However, adequate measures need to be taken to adjust the training data to remove or
reduce variation between datasets caused by extraneous effects. Small D. stramonium plants
were still overlooked. As mentioned, machine learning models perform well in situations
of interpolation. When extrapolation occurs, this is when the distribution of reflectance
values, measured in another location and/or at another time, differ from the distribution
of the training data, and major model performance reductions can occur [78]. Here, this
problem was addressed by the use of VI and CDF matching. However, this methodology
failed in the Meulebeke field, where var. tatula was present. It is important to consider the
similarity of the measurements to the training data when classifying a new location, and
results should be interpreted with caution when extrapolating. To determine the similarity
to the existing training data, out-of-distribution detection can be performed [12].
While this study aimed to achieve the above-mentioned objectives, some aspects
of the design may have influenced the results and should be considered. The lack of
knowledge about the presence of small D. stramonium plants in the field of Oudenaarde
might have exaggerated the results of that field. As the results from other fields showed
small D. stramonium plants to be problematic, chances are small and (partially) hidden
weeds were ignored, overestimating recall. However, obtaining GNSS measurements
of all D. stramonium plants in such a dense and large field is very time consuming. In
addition, because of the misalignment between reflectance and RGB orthomosaic, it was
difficult to obtain training data of D. stramonium, especially for small plants. On the one
hand, small plants consist of fewer pixels than large plants, making them more difficult to
classify correctly. On the other hand, the limited amount of training data of these small
D. stramonium weeds may cause the model to be less sensitive for these weeds, as it has not
been adequately trained to recognize them. A great deal of multispectral data of smaller
D. stramonium plants should be collected to test this hypothesis.
As explained, single false positive pixels might be unavoidable in higher-resolution
datasets, due to soil reflection, edge effects, or BRDF issues, so a threshold value of a number
of positive pixels within an area must be used, maximizing recall and precision simultane-
ously. In this study, we were not able to obtain a generally applicable threshold value. The
classification maps of the fields of Houthulst and Merelbeke (Figures 4e and 5e) show some
FP consisting of a few pixels. To reduce the FP created by this noise, a higher threshold
value can be used. However, this results in misclassifying small D. stramonium plants as
common bean. Human interpretation of the classification map could be adequate, since
the maps do show clear clusters of pixels—even leaf shapes—that could be attributable to
D. stramonium. In this respect, deep learning could also be interesting. Deep convolutional
networks have been shown to acquire high accuracy rates in weed–crop classification
studies [79–82] and outperform traditional machine learning techniques [83,84].
As mentioned in the introduction, it is worth noting that agricultural fields may host
various toxic weed species. The primary focus of this study has been the precise detection of
D. stramonium. Nonetheless, the ultimate aim is to create a model capable of discriminating


Remote Sens. 2024, 16, 3538
20 of 24
between all prevailing toxic weeds species on the one hand and crop plants on the other
hand. However, the feasibility of developing such a model relies on the availability of
extensive training data of these toxic weeds. When such training data become available, a
model capable of classifying all relevant toxic weed species in (Belgian) vegetable crops
should be pursued.
5. Conclusions
Common bean and Datura stramonium are multispectrally separable using the ten-band
multispectral camera from MicaSense and logistic regression. For the largest dataset, in
Oudenaarde, the model obtained a validation recall of 99% and TNR of 95%. To apply this
model to other fields and address differences between datasets, vegetation indices were
incorporated in the dataset and/or data corrected by matching the cumulative distribution
functions (CDF) were used. Classification maps of CDF-corrected multispectral ortho-
mosaics improved in comparison with the uncorrected orthomosaics. Best results were
obtained with a model that was trained using data of all but one location with a leave-one-
group-out cross-validation and applied to the CDF-corrected orthomosaic of the omitted
field. However, small D. stramonium plants were systematically overlooked and classified
as common bean. Further research is needed to determine whether a model created from
lower-altitude UAV data (<30 m) or oblique imagery is able to detect these small plants. The
model, which was trained using Datura stramonium var. stramonium, was not able to detect
D. stramonium plants belonging to var. tatula. A drawback of the methodology is the use
of one threshold value. A flight height depending on the plant size and degree of canopy
closure could solve this problem. Alternatively, human interpretation of the classification
map can, in some cases, suffice. Other methods (e.g., deep convolutional networks) can
also be explored. The current detection strategy adopted by the industry is capable of
detecting large D. stramonium plants located at the field’s edges and narrow zones adjacent
to the field’s diagonals. The best classification strategy used in this paper was able to detect
large D. stramonium plants, regardless of their location in the field. Although small weed
plants remain a problem, the use of this method means an improvement in the detection
accuracy over the present approach of visual scouting. The industry has to trade off the
time required to scan the field and the resolution, which determines the accuracy. The study
also illustrates the importance of an independent test set. The field in Oudenaarde yielded
encouraging outcomes for employing a logistic regression model with UAV data from a
ten-band multispectral camera. However, application to other fields revealed challenges.
Author Contributions: Conceptualization, M.L., B.D.C., D.N., W.H.M. and J.G.P.; methodology, M.L.,
B.D.C., D.N., W.H.M. and J.G.P.; software, M.L.; validation, M.L., B.D.C., D.N., W.H.M. and J.G.P.;
formal analysis, M.L.; investigation, M.L.; resources, J.G.P.; data curation, M.L.; writing—original draft
preparation, M.L.; writing—review and editing, M.L., B.D.C., D.N., W.H.M. and J.G.P.; visualization,
M.L.; supervision, B.D.C., D.N., W.H.M. and J.G.P.; project administration, J.G.P.; funding acquisition,
J.G.P. All authors have read and agreed to the published version of the manuscript.
Funding: This research did not receive any specific grant from funding agencies in the public,
commercial, or not-for-profit sectors.
Data Availability Statement: The datasets presented in this article are not readily available because
it is used for ongoing research.
Acknowledgments: The authors thank Jan Hanssens and Chris Heyndrickx of Ardo (Ardo NV,
Ardooie, Belgium) for the supply of vegetable seeds, the insight in the vegetable processing industry,
and the help with locating fields with toxic D. stramonium plants. The authors also thank Stefaan
Goudeseune and Xavier Demeester of Greenyard (Greenyard Frozen Belgium NV, Westrozebeke,
Belgium) for their help in locating appropriate fields.
Conflicts of Interest: The authors declare no conflicts of interest.


Remote Sens. 2024, 16, 3538
21 of 24
References
1.
Departement Landbouw en Visserij, Groenten Openlucht: Sectoroverzicht Tuinbouw, Agentschap Landbouw & Zeevisserij.
Available online: https://landbouwcijfers.vlaanderen.be/landbouw/groenten-openlucht (accessed on 2 July 2024).
2.
McNally, W.D. A case of stramonium poisoning. J. Am. Med. Assoc. 1915, 19, 1640. [CrossRef]
3.
Waarnemingen.be, Waarnemingen van Doornappel en Zwarte Nachtschade. Available online: https://waarnemingen.be/
species/6683/statistics/ (accessed on 11 May 2023).
4.
www.inaturalist.org. Available online: https://www.inaturalist.org/taxa/55854-Datura-stramonium (accessed on 15 November
2023).
5.
Agriculture et Environnement. Du Datura Dans des Haricots Verts; Agriculture et Environnement: Paris, France, 2012.
6.
Hanssens, J.; (Ardo NV, Ardooie, Belgium). Personal communication, 2018.
7.
Lauwers, M.; Nuyttens, D.; De Cauwer, B.; Pieters, J. Hyperspectral classification of poisonous solanaceous weeds in processing
Phaseolus vulgaris L. and Spinacia oleracea L. Comput. Electron. Agric. 2022, 196, 106908. [CrossRef]
8.
Borregaard, T.; Nielsen, H.; Nørgaard, L.; Have, H. Crop-weed discrimination by line imaging spectroscopy. J. Agric. Eng. Res.
2000, 75, 389–400. [CrossRef]
9.
Gao, J.; Nuyttens, D.; Lootens, P.; He, Y.; Pieters, J.G. Recognising weeds in a maize crop using a random forest machine-learning
algorithm and near-infrared snapshot mosaic hyperspectral imagery. Biosyst. Eng. 2018, 170, 39–50. [CrossRef]
10.
de Souza, M.F.; Amaral, L.R.D.; de M Oliveira, S.R.; Coutinho, M.A.N.; Netto, C.F. Spectral differentiation of sugarcane from
weeds. Biosyst. Eng. 2020, 190, 41–46. [CrossRef]
11.
Piron, A.; Leemans, V.; Kleynen, O.; Lebeau, F.; Destain, M.F. Selection of the most efficient wavelength bands for discriminating
weeds from crop. Comput. Electron. Agric. 2008, 62, 141–148. [CrossRef]
12.
Chen, E.; Bao, H.; Dinh, N. Evaluating the reliability of machine-learning-based predictions used in nuclear power plant
instrumentation and control systems. Reliab. Eng. Syst. Saf. 2024, 250, 110266. [CrossRef]
13.
Carvalho, S.; Macel, M.; Schlerf, M.; Skidmore, A.K.; van der Putten, W.H. Soil biotic impact on plant species shoot chemistry and
hyperspectral reflectance patterns. New Phytol. 2012, 196, 1133–1144. [CrossRef]
14.
Prudnikova, E.; Savin, I.; Vindeker, G.; Grubina, P.; Shishkonakova, E.; Sharychev, D. Influence of soil background on spectral
reflectance of winter wheat crop canopy. Remote Sens. 2019, 11, 1932. [CrossRef]
15.
Hasler, O.K.; Winter, A.; Langer, D.D.; Bryne, T.H.; Johansen, T.A. Lightweight UAV payload for image spectroscopy and
atmospheric irradiance measurements. In IGARSS 2023–2023 IEEE International Geoscience and Remote Sensing Symposium; IEEE:
Piscataway Township, NJ, USA, 2023; pp. 4028–4031. [CrossRef]
16.
Reichle, R.H.; Koster, R.D. Bias reduction in short records of satellite soil moisture. Geophys. Res. Lett. 2004, 31, 2–5. [CrossRef]
17.
Brocca, L.; Hasenauer, S.; Lacava, T.; Melone, F.; Moramarco, T.; Wagner, W.; Dorigo, W.; Matgen, P.; Martínez-Fernández, J.;
Llorens, P.; et al. Soil moisture estimation through ASCAT and AMSR-E sensors: An intercomparison and validation study across
Europe. Remote Sens. Environ. 2011, 115, 3390–3408. [CrossRef]
18.
Maes, W.H.; Steppe, K. Perspectives for remote sensing with unmanned aerial vehicles in precision agriculture. Trends Plant Sci.
2019, 24, 152–164. [CrossRef] [PubMed]
19.
MicaSense, Best Practices: Collecting Data with MicaSense Sensors. Available online: https://support.micasense.com/hc/en-us/
articles/219241067-I-need-to-fly-at-low-altitudes-how-can-I-improve-the-odds-this-data-can-be-processed- (accessed on 27
April 2023).
20.
Su, J.; Liu, C.; Coombes, M.; Hu, X.; Wang, C.; Xu, X.; Li, Q.; Guo, L.; Chen, W. Wheat yellow rust monitoring by learning from
multispectral UAV aerial imagery. Comput. Electron. Agric. 2018, 155, 157–166. [CrossRef]
21.
Xiao, D.; Pan, Y.; Feng, J.; Yin, J.; Liu, Y.; He, L. Remote sensing detection algorithm for apple fire blight based on UAV multispectral
image. Comput. Electron. Agric. 2022, 199, 107137. [CrossRef]
22.
Zhang, J.; Wang, C.; Yang, C.; Xie, T.; Jiang, Z.; Hu, T.; Luo, Z.; Zhou, G.; Xie, J. Assessing the effect of real spatial resolution of in
situ UAV multispectral images on seedling rapeseed growth monitoring. Remote Sens. 2020, 12, 1207. [CrossRef]
23.
Vlaamse Overheid; Databank Ondergrond Vlaanderen: Bodemverkenner 2022. Available online: https://www.dov.vlaanderen.
be/portaal/?module=public-bodemverkenner (accessed on 12 December 2022).
24.
KMI, Klimatologische Overzichten van 2022.
Available online: https://www.meteo.be/nl/klimaat/klimaat-van-belgie/
klimatologisch-overzicht/2022/januari (accessed on 12 December 2022).
25.
KMI, Klimatologische Overzichten van 2020.
Available online: https://www.meteo.be/nl/klimaat/klimaat-van-belgie/
klimatologisch-overzicht/2016-2020/2020/januari (accessed on 12 December 2022).
26.
Waterinfo.Vlaanderen.be; Vlaamse Overheid: Waterinfo. Available online: https://waterinfo.vlaanderen.be/Rapporten (accessed
on 12 December 2022).
27.
MicaSense RedEdge MX Processing Workflow (Including Reflectance Calibration) in Agisoft Metashape Professional. Available
online: https://agisoft.freshdesk.com/support/solutions/articles/31000148780-micasense-rededge-mx-processing-workflow-
including-reflectance-calibration-in-agisoft-metashape-pro#Appendix-C.-Controlling-reflectance-calculation (accessed on 5
September 2022).
28.
QGIS Documentation: Raster Analysis. Available online: https://docs.qgis.org/3.4/en/docs/user_manual/working_with_
raster/raster_analysis.html (accessed on 1 April 2023).
29.
Bradski, G. The OpenCV Library. Dr. Dobb’s J. Softw. Tools 2000, 120, 122–125.


Remote Sens. 2024, 16, 3538
22 of 24
30.
Pedregosa, F.; Varoquaux, G.; Gramfort, A.; Michel, V.; Thirion, B.; Grisel, O.; Blondel, M.; Prettenhofer, P.; Weiss, R.; Dubourg, V.;
et al. Scikit-learn: Machine learning in Python. J. Mach. Learn. Res. 2011, 12, 2825–2830.
31.
MicaSense, What is the Center Wavelength and Bandwidth of each Filter for MicaSense Sensors?
Available online:
https://support.micasense.com/hc/en-us/articles/214878778-What-is-the-center-wavelength-and-bandwidth-of-each-
filter-for-MicaSense-sensors- (accessed on 25 February 2020).
32.
Woebbecke, D.M.; Meyer, G.E.; Von Bargen, K.; Mortensen, D.A. Color indices for weed identification under various soil, residue,
and lighting conditions. Trans. Am. Soc. Agric. Eng. 1995, 38, 259–269. [CrossRef]
33.
Otsu, N. A threshold selection method from gray-level histograms. IEEE Trans. Syst. Man. Cybern. 1979, 9, 62–66. [CrossRef]
34.
Roberts, D.R.; Bahn, V.; Ciuti, S.; Boyce, M.S.; Elith, J.; Guillera-Arroita, G.; Hauenstein, S.; Lahoz-Monfort, J.J.; Schröder, B.;
Thuiller, W.; et al. Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. Ecography
2017, 40, 913–929. [CrossRef]
35.
Dormann, C.F.; McPherson, J.M.; Araújo, M.B.; Bivand, R.; Bolliger, J.; Carl, G.; Davies, R.G.; Hirzel, A.; Jetz, W.; Kissling, W.D.;
et al. Methods to account for spatial autocorrelation in the analysis of species distributional data: A review. Ecography 2007, 30,
609–628. [CrossRef]
36.
Deproost, P.; Elsen, F.; Vanongeval, L.; Geypens, M. Beredeneerd Beregenen van Stamslaboon en Voorjaarsspinazie op Zandleem-
tot Leembodems. 2001. Available online: https://www.bdb.be/fr/base-de-connaissances/%C3%A9ditions/beredeneerd-
beregenen-van-stamslaboon-en-voorjaarsspinazie-op-zandleem-tot-leembodems (accessed on 1 April 2023).
37.
Virtanen, P.; Gommers, R.; Oliphant, T.E.; Haberland, M.; Reddy, T.; Cournapeau, D.; Burovski, E.; Peterson, P.; Weckesser, W.;
Bright, J.; et al. SciPy 1.0: Fundamental algorithms for scientific computing in Python. Nat. Methods 2020, 17, 261–272. [CrossRef]
[PubMed]
38.
Tucker, C.J. Red and photographic infrared linear combinations for monitoring vegetation. Remote Sens. Environ. 1979, 8, 127–150.
[CrossRef]
39.
Huete, A.R. A soil-adjusted vegetation index (SAVI). Remote Sens. Environ. 1988, 25, 295–309. [CrossRef]
40.
Qi, J.; Chehbouni, A.; Huete, A.R.; Kerr, Y.H.; Sorooshian, S. A modified soil adjusted vegetation index. Remote Sens. Environ.
1994, 48, 119–126. [CrossRef]
41.
Jordan, C.F. Derivation of leaf-are index from quality of light on the forest floor. Ecol. Soc. Am. 1969, 50, 663–666. [CrossRef]
42.
Roujean, J.L.; Breon, F.M. Estimating PAR absorbed by vegetation from bidirectional reflectance measurements. Remote Sens.
Environ. 1995, 51, 375–384. [CrossRef]
43.
Gitelson, A.A.; Stark, R.; Grits, U.; Rundquist, D.; Kaufman, Y.; Derry, D. Vegetation and soil lines in visible spectral space: A
concept and technique for remote estimation of vegetation fraction. Int. J. Remote Sens. 2002, 23, 2537–2562. [CrossRef]
44.
Gitelson, A.; Merzlyak, M.N. Quantitative estimation of chlorophyll-a using reflectance spectra: Experiments with autumn
chestnut and maple leaves. J. Photochem. Photobiol. B Biol. 1994, 22, 247–252. [CrossRef]
45.
Gitelson, A.A.; Kaufman, Y.J.; Merzlyak, M.N. Use of a green channel in remote sensing of global vegetation from EOS- MODIS.
Remote Sens. Environ. 1996, 58, 289–298. [CrossRef]
46.
Daniels, L.; Eeckhout, E.; Wieme, J.; Dejaegher, Y.; Audenaert, K.; Maes, W.H. Identifying the optimal radiometric calibration
method for UAV-based multispectral imaging. Remote Sens. 2023, 15, 2909. [CrossRef]
47.
Heyndrickx, C.; (Affiliation). Personal communication, 2023.
48.
Perroy, R.L.; Sullivan, T.; Stephenson, N. Assessing the impacts of canopy openness and flight parameters on detecting a
sub-canopy tropical invasive plant using a small unmanned aerial system. ISPRS J. Photogramm. Remote Sens. 2017, 125, 174–183.
[CrossRef]
49.
Inamdar, D.; Kalacska, M.; Darko, P.O.; Arroyo-Mora, J.P.; Leblanc, G. Spatial response resampling (SR2): Accounting for the
spatial point spread function in hyperspectral image resampling. MethodsX 2023, 10, 101998. [CrossRef] [PubMed]
50.
Gao, J.; Liao, W.; Nuyttens, D.; Lootens, P.; Vangeyte, J.; Pižurica, A.; He, Y.; Pieters, J.G. Fusion of pixel and object-based features
for weed mapping using unmanned aerial vehicle imagery. Int. J. Appl. Earth Obs. Geoinf. 2018, 67, 43–53. [CrossRef]
51.
Bégué, A. Leaf area index, intercepted photosynthetically active radiation, and spectral vegetation indices: A sensitivity analysis
for regular-clumped canopies. Remote Sens. Environ. 1993, 46, 45–59. [CrossRef]
52.
Carter, G.A.; Knapp, A.K. Leaf optical properties in higher plants: Linking spectral characteristics to stress and chlorophyll
concentration. Am. J. Bot. 2001, 88, 677–684. [CrossRef]
53.
Smith, A.M.; Blackshaw, R.E. Weed-crop discrimination using remote sensing: A detached leaf experiment. Weed Sci. Soc. Am.
2017, 17, 811–820. [CrossRef]
54.
Pant, P.; Heikkinen, V.; Hovi, A.; Korpela, I.; Hauta-kasari, M.; Tokola, T. Evaluation of simulated bands in airborne optical
sensors for tree species identification. Remote Sens. Environ. 2013, 138, 27–37. [CrossRef]
55.
Jackson, C.M.; Adam, E. Machine learning classification of endangered tree species in a tropical submontane forest using
worldview-2 multispectral satellite imagery and imbalanced dataset. Remote Sens. 2021, 13, 4970. [CrossRef]
56.
Ullah, S.; Shakir, M.; Iqbal, M.S.; Iqbal, A.; Ali, M.; Shafique, M.; Rehman, A.; Godwin, J. Identifying optimal waveband positions
for discriminating Parthenium hysterophorus using hyperspectral data. Ecol. Inform. 2021, 64, 101362. [CrossRef]


Remote Sens. 2024, 16, 3538
23 of 24
57.
Lauwers, M.; De Cauwer, B.; Nuyttens, D.; Cool, S.R.; Pieters, J.G. Hyperspectral classification of Cyperus esculentus clones and
morphologically similar weeds. Sensors 2020, 20, 2504. [CrossRef] [PubMed]
58.
De Castro, A.I.; Jurado-Expósito, M.; Gómez-Casero, M.T.; López-Granados, F. Applying neural networks to hyperspectral and
multispectral field data for discrimination of cruciferous weeds in winter crops. Sci. World J. 2012, 2012. [CrossRef]
59.
Vrindts, E.; Baerdemaeker, J.D.E.; Ramon, H. Weed detection using canopy reflection. Precis. Agric. 2002, 3, 63–80. [CrossRef]
60.
Lauwers, M.; De Cauwer, B.; Nuyttens, D.; Pieters, J.G. Ghent University: Gent, Belgium, 2021; unpublished work.
61.
Alexandridis, T.K.; Tamouridou, A.A.; Pantazi, X.E.; Lagopodi, A.L.; Kashefi, J.; Ovakoglou, G.; Polychronos, V.; Moshou, D.
Novelty detection classifiers in weed mapping: Silybum marianum detection on UAV multispectral images. Sensors 2017, 17,
2007. [CrossRef]
62.
Bah, M.D.; Hafiane, A.; Canals, R. Weeds detection in UAV imagery using SLIC and the hough transform. In Proceedings of the
2017 Seventh International Conference on Image Processing Theory, Tools and Applications (IPTA), Montreal, QC, Canada, 28
November–1 December 2017; pp. 1–6. [CrossRef]
63.
Ferreira, A.D.S.; Freitas, D.M.; da Silva, G.G.; Pistori, H.; Folhes, M.T. Weed detection in soybean crops using ConvNets. Comput.
Electron. Agric. 2017, 143, 314–324. [CrossRef]
64.
Barrero, O.; Perdomo, S.A. RGB and multispectral UAV image fusion for Gramineae weed detection in rice fields. Precis. Agric.
2018, 19, 809–822. [CrossRef]
65.
Sivakumar, A.N.V.; Li, J.; Scott, S.; Psota, E.; Jhala, A.J.; Luck, J.D.; Shi, Y. Comparison of object detection and patch-based
classification deep learning models on mid-to late-season weed detection in UAV imagery. Remote Sens. 2020, 12, 2136. [CrossRef]
66.
Haq, M.A. CNN Based Automated Weed Detection System Using UAV Imagery. Comput. Syst. Sci. Eng. 2021, 42, 837–849.
[CrossRef]
67.
Khan, S.; Tufail, M.; Khan, M.T.; Khan, Z.A.; Anwar, S. Deep learning-based identification system of weeds and crops in strawberry
and pea fields for a precision agriculture sprayer. Precis. Agric. 2021, 22, 1711–1727. [CrossRef]
68.
Genze, N.; Ajekwe, R.; Güreli, Z.; Haselbeck, F.; Grieb, M.; Grimm, D.G. Deep learning-based early weed segmentation using
motion blurred UAV images of sorghum fields. Comput. Electron. Agric. 2022, 202, 107388. [CrossRef]
69.
Xu, B.; Fan, J.; Chao, J.; Arsenijevic, N.; Werle, R.; Zhang, Z. Instance segmentation method for weed detection using UAV imagery
in soybean fields. Comput. Electron. Agric. 2023, 211, 107994. [CrossRef]
70.
Cai, Y.; Zeng, F.; Xiao, J.; Ai, W.J.; Kang, G.; Lin, Y.; Cai, Z.; Shi, H.; Zhong, S.; Yue, X. Attention-aided semantic segmentation
network for weed identification in pineapple field. Comput. Electron. Agric. 2023, 210, 107881. [CrossRef]
71.
Gallo, I.; Rehman, A.U.; Dehkordi, R.H.; Landro, N.; La Grassa, R.; Boschetti, M. Deep object detection of crop weeds: Performance
of YOLOv7 on a real case dataset from UAV images. Remote Sens. 2023, 15, 539. [CrossRef]
72.
El Imanni, H.S.; El Harti, A.; Bachaoui, E.M.; Mouncif, H.; Eddassouqui, F.; Hasnai, M.A.; Zinelabidine, M.I. Multispectral UAV
data for detection of weeds in a citrus farm using machine learning and Google Earth Engine: Case study of Morocco. Remote
Sens. Appl. Soc. Environ. 2023, 30, 100941. [CrossRef]
73.
Bah, M.D.; Hafiane, A.; Canals, R. Deep learning with unsupervised data labeling for weed detection in line crops in UAV images.
Remote Sens. 2018, 10, 1690. [CrossRef]
74.
Che’ya, N.N.; Dunwoody, E.; Gupta, M. Assessment of weed classification using hyperspectral reflectance and optimal multispec-
tral UAV imagery. Agronomy 2021, 11, 1435. [CrossRef]
75.
de Camargo, T.; Schirrmann, M.; Landwehr, N.; Dammer, K.H.; Pflanz, M. Optimized deep learning model as a basis for fast UAV
mapping of weed species in winter wheat crops. Remote Sens. 2021, 13, 1704. [CrossRef]
76.
Singh, V.; Singh, D. Development of an approach for early weed detection with UAV imagery. In Proceedings of the IGARSS
2022–2022 IEEE International Geoscience and Remote Sensing Symposium, Kuala Lumpur, Malaysia, 17–22 July 2022; pp.
4879–4882. [CrossRef]
77.
Gašparovi´c, M.; Zrinjski, M.; Barkovi´c, Ð.; Radoˇcaj, D. An automatic method for weed mapping in oat fields based on UAV
imagery. Comput. Electron. Agric. 2020, 173, 105385. [CrossRef]
78.
Barbu, A.; Mayo, D.; Alverio, J.; Luo, W.; Wang, C.; Gutfreund, D.; Tenenbaum, J.; Katz, B. ObjectNet: A large-scale bias-controlled
dataset for pushing the limits of object recognition models. Adv. Neural Inf. Process. Syst. 2019, 32, 1–11.
79.
Hu, K.; Coleman, G.; Zeng, S.; Wang, Z.; Walsh, M. Graph weeds net: A graph-based deep learning method for weed recognition.
Comput. Electron. Agric. 2020, 174, 105520. [CrossRef]
80.
Chen, D.; Lu, Y.; Li, Z.; Young, S. Performance evaluation of deep transfer learning on multi-class identification of common weed
species in cotton production systems. Comput. Electron. Agric. 2022, 198, 107091. [CrossRef]
81.
Jin, X.; Bagavathiannan, M.; McCullough, P.E.; Chen, Y.; Yu, J. A deep learning-based method for classification, detection, and
localization of weeds in turfgrass. Pest Manag. Sci. 2022, 78, 4809–4821. [CrossRef] [PubMed]
82.
Jin, X.; Sun, Y.; Che, J.; Bagavathiannan, M.; Yu, J.; Chen, Y. A novel deep learning-based method for detection of weeds in
vegetables. Pest Manag. Sci. 2022, 78, 1861–1869. [CrossRef] [PubMed]


Remote Sens. 2024, 16, 3538
24 of 24
83.
Hammad, M.; Johan, S.; Khalid, P.; Arif, M. Automation in agriculture by machine and deep learning techniques: A review of
recent developments. Precis. Agric. 2021, 22, 2053–2091. [CrossRef]
84.
GC, S.; Zhang, Y.; Koparan, C.; Ahmed, M.R.; Howatt, K.; Sun, X. Weed and crop species classification using computer vision and
deep learning technologies in greenhouse conditions. J. Agric. Food Res. 2022, 9, 100325. [CrossRef]
Disclaimer/Publisher’s Note: The statements, opinions and data contained in all publications are solely those of the individual
author(s) and contributor(s) and not of MDPI and/or the editor(s). MDPI and/or the editor(s) disclaim responsibility for any injury to
people or property resulting from any ideas, methods, instructions or products referred to in the content.
