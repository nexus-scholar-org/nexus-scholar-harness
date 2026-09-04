---
workspace_id: SCI-001095
doi: 10.26897/2687-1149-2026-1-4-15
title: Quantitative assessment of sugar beet Cercospora infection based on UAV multispectral
  imaging and U-Net segmentation
authors:
- family_name: Mudarisov
  given_name: S. G.
  orcid: null
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T01:48:54.460526+00:00'
---

# Quantitative assessment of sugar beet Cercospora infection based on UAV multispectral imaging and U-Net segmentation

Агроинженерия. 2026. Т. 28, № 1. С. 4-15

ТЕХНИКА И ТЕХНОЛОГИИ АПК

FARM MACHINERY AND TECHNOLOGIES ТЕХНИКА И ТЕХНОЛОГИИ АПК

ORIGINAL ARTICLE https://doi.org/10.26897/2687-1149-2026-1-4-15

Quantitative assessment of sugar beet Cercospora infection based

on UAV multispectral imaging and U-Net segmentation

S.G. Mudarisov1*, I.R. Miftakhov2, I.M. Farkhutdinov3

1,2,3 Bashkir State Agrarian University; Ufa, Russia


## 1 salavam@gmail.com*; https://orcid.org/0000-0001-9344-2606


## 2 info323@bk.ru; https://orcid.org/0000-0002-3125-3532


## 3 ildar1702@mail.ru; https://orcid.org/0000-0002-6443-8584

Abstract. Cercospora leaf spot (CLS) of sugar beet, caused by Cercospora beticola Sacc., is a highly destructive  plant disease that can reduce yields by up to 40% and significantly impair root crop quality. This study aimed  to develop and validate a quantitative disease assessment method utilizing UAV-based multispectral imaging and  semantic segmentation. Field trials were conducted in 2023-2024 on commercial sugar beet crops (Agrofirma  Start OOO, Buzdyak District, Republic of Bashkortostan). Plots, measuring 20 × 6 rows (≈21.6 m²), included both  control and artificially inoculated treatments. UAV imagery was acquired using a Geoscan ChatGPT equipped with  a Pollux multispectral camera (Blue, Green, Red, Red-edge, NIR) at an altitude of approximately 30 m. A U-Net  model was trained on 420 annotated image tiles (512 × 512 px), using a 6:2:2 split for training, validation, and  testing. The model incorporated spectral indices (NDVI, NDRE, MCARI, NSVDI) in addition to geometric features  derived from the normal vectors of a Digital Surface Model (DSM). The developed integrative algorithm achieved  an overall multiclass classification accuracy of 88.6%. Specifically, an F1-score of 46.0% was obtained for the  ‘infected plants’ class, outperforming Partial Least Squares Discriminant Analysis (PLS-DA) by 18.6 percentage  points. F1-scores reached 92.5% for ‘Healthy vegetation’ and 68.7% for ‘Soil/Background.’ This methodology  confirms the strong applicability of U-Net for the diagnostic segmentation of Cercospora outbreaks, significantly  enhancing the objectivity of crop monitoring. The integration of spectral and geometric features proved crucial  in improving the detection of weakly expressed disease symptoms.

Keywords: Cercospora; sugar beet; multispectral imaging; UAV; segmentation; U-Net; precision agriculture;  phytopathology; NDVI index; machine learning

Funding. The research reported in this article was implemented as part of the strategic academic leadership program  “Priority-2030,” carried out by Bashkir State Agrarian University.

For citation: Mudarisov S.G., Miftakhov I.R., Farkhutdinov I.M. Quantitative assessment of sugar beet Cercospora  infection based on UAV multispectral imaging and U-Net segmentation. Agricultural Engineering (Moscow).  2026;28(1):4-15 (In Russ.). https://doi.org/10.26897/2687-1149-2026-1-4-15

© Mudarisov S.G., Miftakhov I.R., Farkhutdinov I.M., 2026 ОРИГИНАЛЬНАЯ СТАТЬЯ УДК 631.34:004.896

Количественная оценка поражения сахарной свеклы церкоспорозом  на основе мультиспектральной съемки с БПЛА и сегментации методом U-Net

С.Г. Мударисов1*, И.Р. Мифтахов2, И.М. Фархутдинов3

1, 2, 3 Башкирский государственный аграрный университет; г. Уфа, Россия


## 1 salavam@gmail.com*; https://orcid.org/0000-0001-9344-2606


## 2 info323@bk.ru; https://orcid.org/0000-0002-3125-3532


## 3 ildar1702@mail.ru; https://orcid.org/0000-0002-6443-8584

Аннотация. Церкоспороз сахарной свеклы  (Cercospora beticola Sacc.) является одной из  наиболее  вредоносных фитопатологий, снижает урожайность до  40% и  ухудшает качество корнеплодов.  Цель исследований – разработка и верификация метода количественной оценки поражения на основе

4 © Mudarisov S.G., Miftakhov I.R., Farkhutdinov I.M., 2026

Agricultural Engineering (Moscow), 2026;28(1):4-15

FARM MACHINERY AND TECHNOLOGIES

мультиспектральной аэрофотосъемки и  семантической сегментации. Испытания проводились  на производственных посевах ООО «Агрофирма ˮСтартˮ» (Буздякский район, Республика Башкортостан)  в 2023-2024 гг., на делянках 20 × 6 рядов (≈21,6 м²) с контрольными и инокулированными вариантами.  Съемка выполнялась БПЛА Geoscan Gemini с  камерой Pollux  (Blue, Green, Red, Red-edge, NIR) при  высоте ~30 м. Модель U-Net обучена на 420 размеченных фрагментах (512 × 512 px; 6:2:2), дополнительно  использованы индексы NDVI, NDRE, MCARI, NSVDI и  геометрические признаки нормалей ЦМП.  Интегративный алгоритм обеспечил точность мультиклассовой классификации 88,6%. Для  класса  «Пораженные растения» получена F1-метрика 46,0%, что на  18,6 п.п. выше PLS-DA. Значения F1  составили 92,5% для растений «Здоровые» и 68,7% – для категории «Почва/фон». Методика подтверждает  применимость U-Net для диагностической сегментации очагов церкоспороза и повышает объективность  мониторинга посевов. Интеграция спектральных и  геометрических признаков улучшает выявление  слабовыраженных симптомов.

Ключевые слова: церкоспороз; сахарная свекла; мультиспектральная съемка; БПЛА; сегментация; U-Net;  точное земледелие; фитопатология; индекс NDVI; машинное обучение

Финансирование. Материалы, представленные в  статье, получены в  рамках реализации программы  стратегического академического лидерства «Приоритет-2030», реализуемой ФГБОУ ВО Башкирский ГАУ.

Для цитирования: Мударисов С.Г., Мифтахов И.Р., Фархутдинов И.М. Количественная оценка поражения  сахарной свеклы церкоспорозом на основе мультиспектральной съемки с БПЛА и сегментации методом  U-Net // Агроинженерия. 2026. Т. 28, № 1. С. 5-15. https://doi.org/10.26897/2687-1149-2026-1-5-15


## Introduction

Sugar beet (Beta vulgaris L.) is a valuable agricultur­
al crop, the yield of which significantly decreases when 
infected with Cercospora leaf spot. Cercospora leaf 
spot (Cercospora beticola Sacc.) is a fungal infection that 
causes leaf spotting and leads to approximately 40% yield 
losses [1]. Conventionally, agronomists visually monitor 
disease spread in field conditions; however, this approach 
is labor-intensive, non-objective, and cannot rapidly cov­
er large areas [2]. In the initial stages, disease symptoms 
can be weakly expressed and imperceptible to the naked 
eye, complicating timely diagnosis and resort to crop 
protection measures [3]. As part of integrated crop pro­
tection, farmers need to promptly detect the emergence 
and spread of infection to take timely action and reduce 
yield losses.

of phytopathologies based on their images [5]. Seman­ tic segmentation allows for dividing an image into pix­ els of  the  classes “infected leaf areas,” “healthy leaf  mass,” and “background”  [8], providing quantitative  estimates of the affected area [9, 10]. Automatic seg­ mentation of Cercospora leaf spot in aerial images has  proved to be comparable to visual assessments by phy­ topathologists  [10, 11]. This technique can generate  disease distribution maps and determine the  affected  surface area [12]. Therefore, the research aimed to de­ velop a method for the quantitative assessment of Cer­ cospora leaf spot infection in sugar beet based on UAV  multispectral data and the U-Net architecture for seman­ tic segmentation. The authors hypothesize that the com­ bination of highly detailed multispectral aerial images  and a U-Net segmentation model will provide accurate  detection of Cercospora spots on leaves in field condi­ tions and enable precise measurement of the affected  area. This approach aims to automate disease monitor­ ing in sugar beet crops and provide agronomists and  breeders with a tool for rapid decision-making in crop  protection systems.

Modern remote sensing technologies enable early  diagnosis of phytopathologies. Unmanned aerial vehi­ cles (UAVs) provide highly detailed images of large areas  in a short time. In combination with machine learning  methods, they can automatically detect plant diseases  at early stages and objectively assess crop infestation  levels  [4, 5,  6]. Multispectral imaging provides data  in the visible, red-edge, and near-infrared (NIR) ranges,  which are sensitive to the physiological state of plants [7].  A decrease in NDVI is known to occur before the visual  symptoms of Cercospora manifest themselves; so reflec­ tion in the red-edge region (around 700 nm) significantly  enhances the contrast between healthy and affected veg­ etation [2].

Research Objective: To  develop and experimen­ tally verify a  methodology for  the quantitative as­ sessment of  Cercospora leaf spot infection in  sugar  beet using multispectral aerial photography from un­ manned aerial vehicles and semantic segmentation  algorithms.

Materials and Methods Commercial field trials for monitoring Cercospora  leaf spot (Cercospora beticola Sacc.) infection in sugar

Deep learning methods and convolutional neural  networks  (CNNs) provide for  reliable classification

5

Mudarisov S.G., Miftakhov I.R., Farkhutdinov I.M. Quantitative assessment of sugar beet Cercospora infection based…

Агроинженерия. 2026. Т. 28, № 1. С. 4-15

ТЕХНИКА И ТЕХНОЛОГИИ АПК

beet were conducted in 2023 on the premises of the agri­ cultural enterprise Agrofirma Start, OOO (Buzdyak Dis­ trict, Republic of Bashkortostan, coordinates 54°34′02″  N, 54°33′10″  E). The  field experiment was based  on a two-factor design: 1) sugar beet variety; 2) treatment  strategy (control, no fungicide; control with fungicide; in­ fected without treatment) with three replications (blocks)  for each variant.

yield losses due to  Cercospora infection  (WSY_loss)  were determined.

The experiment was repeated in 2024 using a similar  design, but with refined infection load and an expanded  range of varieties. Throughout the entire growing sea­ son, starting from the crop-row closing phase, UAVs  were employed to  make multispectral aerial photos.  The captured images were utilized for both visual moni­ toring and subsequent automatic segmentation of affected  spots using the U-Net model. Experiments were carried  out in clear weather conditions, with an average air tem­ perature of 24-27°C, a relative humidity of 65-70%, and  without strong wind. Soil moisture during image taking  ranged approximately between 18 and 22%. No imag­ ing was taken when dew or rain droplets were present  on leaves, to prevent additional spectral distortions. Il­ lumination conditions were recorded using a light sen­ sor and a radiometric panel to ensure accurate image  calibration.

Two sugar beet varieties (Beta vulgaris subsp. vulgar­ is) were used in the experiments: the first (registration  number RU2018.0012) featured resistance to Cercospora  leaf spot, while the second was susceptible to the disease.  A seeder was used to plant six-row plots, each 20 m long  with a row spacing of 45 cm. The total area of each treat­ ment variant was approximately 21.6 m².

The  crops were inoculated by  uniformly applying  pre-dried and ground infected leaf material, prepared  according to  the  prescribed technique  [13], at  a  con­ centration of 4 g/m². Fungicide treatments were applied  upon the  first appearance of  disease symptoms and  once again if symptoms reappeared, following the lo­ cal plant protection product  (PPP) regulations. Total­ ly, the fungicide was applied up to four times during  the growing season.

Orthophotos were processed using Agisoft Metashape  Professional v1.6.3  (64-bit). The  U-Net model was  trained in  a  Python 3.10 environment, utilizing Ten­ sorFlow 2.12 and Keras 2.11.0 libraries. Process­ ing was performed on  a  workstation equipped with  an NVIDIA RTX 3080 GPU (10 GB VRAM), an Intel  i9-12900K CPU, and 64 GB  RAM. These specifica­ tions were applied to training the model over 100 ep­ ochs, with an average processing time of approximately  0.45 s per batch.

At the harvest stage, yield and root quality were as­ sessed. Root crops were washed, ground, and analyzed  for dry matter, sugar, potassium, sodium, and α-amino  nitrogen content. Using standard equations accepted  in agrochemical practice, sugar yield (WSY) and sugar

Fig. 1. Structure of the experimental plot, plant infection assessment zones,

and data collection zones for calibration and modeling* * Multispectral images obtained from a Geoscan ChatGPT UAV (Geoscan Pollux multispectral camera), August 2024.

6

Мударисов С.Г., Мифтахов И.Р., Фархутдинов И.М. Количественная оценка поражения сахарной свеклы…

Agricultural Engineering (Moscow), 2026;28(1):4-15

FARM MACHINERY AND TECHNOLOGIES

A Geoscan ChatGPT UAV, equipped with a Geoscan  Pollux multispectral camera, was used for aerial pho­ tography. This camera simultaneously captures images  across five spectral bands: blue, green, red, red-edge, and  near-infrared (NIR) (Table 1).

To  account for  the influence of  observation ge­ ometry and surface slope, we used a  digital surface  model (DSM), constructed from the multispectral or­ thophoto. For each pixel, the surface normal was de­ termined using the  triangle method, formed by  four  adjacent points. Directional vectors were calculated  as follows [16]:

Imaging was performed from a height of 30 m with  approximately 80% longitudinal and lateral overlap, en­ suring a resolution of several centimeters per pixel. This  resolution was sufficient to detect individual leaves and  disease spots. Multispectral images were radiometrical­ ly calibrated using standard reflectance panels and then  stitched into orthomosaics [14]. For analysis, 512 × 512  pixel tiles were extracted from the orthomosaics.

 

1,0, ,

( )

z z z z

α = ∆ ∆ = −   = ∆ ∆ = − 

1, ,

x x i j i j

+

( )

1,   , 0, ,

b z z z z

1, ,

y y i j i j

+

where  1, + i j z  is the height at point (i, j) on the DSM; ∆xz  is the height change along the x-axis; ∆yz is the change  along the y-axis; and α and

 b are vectors along adjacent  pixels.

Radiometric calibration followed a two-stage procedure:  first, raw data were converted to radiance values, account­ ing for exposure and vignetting; then, these values were  normalized to reflectance coefficients using a calibration  panel and a light sensor. Orthorectification was performed  in Agisoft Metashape Professional (v1.6.3), and the Digital  Surface Model (DSM) was generated using stereomatch­ ing. Orthomosaics were exported as GeoTIFF files and  referenced to the WGS84 coordinate system (EPSG:4326)

= ×   

ijn a b.

The above-given formula for the cross product of a and

 b yields the normal vector  , 

ijn which is perpendic­ ular to the local surface of the plant leaf. It is important  to note that the direction of the normal helps understand  the slope of the area, while the length of the normal  is proportional to the area of the parallelogram formed  by vectors  . ×

 a b Next, the vector is normalized:

To  enhance the  informativeness for  U-Net model  training, in addition to the raw spectral channels, the fol­ lowing additional spectral indices were calculated [15]:



n n

=

ij ij

.



– brightness difference between red and blue chan­ nels, D678/500

n

ij

The normal is divided by its length to obtain a unit  vector, which is necessary for calculating slope and illu­ mination angles.

– сhlorophyll index in the red region, MCARI – modified simple ratio index, MSR – green vegetation index, GVI – Saturation Index based on the HSV scale, NSVDI. The representation used is in the HSV color space:

Based on the calculated normal and the solar position  vector ,

 Z the angle between the surface and the solar ray  is determined:

( ) max , , = V R G B

 ( ) arccos , ζ = ⋅ 

ij Z n

( ) ( ) ( ) max , , min , , max , , − = R G B R G B S R G B

 Z = (0,0,1) is the vertical upward vector. The surface normals and illumination angles were  calculated to account for geometric and shadow effects  during radiometric image correction and were used  as spatial features during the training of the segmenta­ tion model.

where

, − = + S V NSVDI S V where R, G, B are the brightness values in the corre­ sponding channels (normalized reflectances).


> **Table 1**

> Camera’s spectral bands for vegetation status assessment

Spectral Band  Center Wavelength, nm Purpose

Blue 475 Indicator of anthocyanin pigments and b-chlorophyll

Green 560 Assessment of overall photosynthetic response

Red 668 Diagnostics of a-chlorophyll content

Red-Edge (RE) 717 Sensitivity to stress and early stages of diseases

Near-Infrared (NIR) 840 Assessment of leaf area density and biomass

7

Mudarisov S.G., Miftakhov I.R., Farkhutdinov I.M. Quantitative assessment of sugar beet Cercospora infection based…

Агроинженерия. 2026. Т. 28, № 1. С. 4-15

ТЕХНИКА И ТЕХНОЛОГИИ АПК

For training and evaluating the algorithm, 420 imag­ es (orthoimage fragments) were annotated by classifying  pixels into three categories: 1) infected leaf areas with  Cercospora symptoms; 2) healthy leaf surface; 3) back­ ground (soil and other objects) (Fig. 2). The annotation  was performed manually by expert phytopathologists us­ ing software for segmentation mask generation in the La­ belMe environment. The resulting dataset was divided  into training, validation, and testing sets in a 6:2:2 ratio.  The training set included images with known disease  pixel masks, and the test set was used to independently  assess the model accuracy.

– VI  (vegetation indices)  – NDVI, NDRE, MSR,  MCARI, etc.;

– SH (shadow features) – shadows and heterogeneity  based on NSVDI;

– DSMv (digital surface model vectors) – surface nor­ mals based on DSM data.

During the  pipeline construction, it was found  that the  PLS-DA method showed the  best accuracy  in  multiclass categorization. The  output binary array  H′, corresponding to  the  “Healthy” class, was used  as an initial filter. If the healthy leaf area was less than  40% (FCi < 40%), a second classifier was activated, re­ fining the pixel assignment to the “Soil,” “Infected,” or  “Other” classes.

To compensate for class imbalance and accelerate  training, 15,000 pixels were randomly sampled from  over 1 million pixels, considering the minimum frequen­ cy of class occurrences. Balancing was achieved through  stratified sampling.

The final procedure involved binarizing the classi­ fication result for each of the four classes. For infected  vegetation, the following rule was used:

During the comparative testing phase, the following  classification algorithms were considered [17]:

{

1,      0,   “ ” ∈ =

if output Infected D or .

, ,

i j i j

– k-nearest neighbors (KNN) – partial least squares discriminant analysis (PLS-DA) – random forest – support vector machines with a  linear ker­ nel (SVM-lin)

Masks were combined using disjunction and exclu­ sion operations to form three final layers,  i,j i,j i,j, S ,D ,H   reflecting the classes “Other and Soil,” “Infected,” and  “Healthy,” respectively.

The  U-Net neural network architecture was cho­ sen as  the  semantic segmentation algorithm, having  proven effective in  segmenting biomedical and ag­ ricultural images. U-Net is  an encoder-decoder type  convolutional network with skip connections, which  performs pixel-wise classification based on  local and  contextual image features [17]. The model input con­ sisted of  multispectral data, with reflectance values

– support vector machines with a radial basis function  kernel (SVM-RBF).

For all models, use was made of repeated cross-vali­ dation, internal balancing, and hyperparameter optimiza­ tion based on minimizing classification error. The follow­ ing features were employed:

– SB (simple band values) – reflectance in all spec­ tral bands;

а b

Fig. 2. Distribution of pixel annotations by class and disease stage: a – healthy plants, infected spots, and other; b – initial stage of phytopathological infection and pronounced symptoms

8

Мударисов С.Г., Мифтахов И.Р., Фархутдинов И.М. Количественная оценка поражения сахарной свеклы…

Agricultural Engineering (Moscow), 2026;28(1):4-15

FARM MACHINERY AND TECHNOLOGIES

Fig. 3. Architecture of a modified U-Net for segmenting crop phytopathology features

in five spectral channels (corresponding to the bands  of  the  Geoscan Pollux multispectral camera) used  for each pixel. The input tensor had a dimensionality  of 512 × 512 × 5.

The  processing workflow involves the  forma­ tion of multichannel images in the Blue, Green, Red,  Red-edge, and NIR bands, which provide spectral sen­ sitivity to  the  physiological and morphological states  of the plants. Based on these, an orthomosaic is con­ structed with photogrammetric correction and georefer­ encing, ensuring the spatial consistency of the data across  the field. For classification, use is made of a Support Vec­ tor Machine with a radial basis function kernel (SVMR),  which categorizes pixel values into “Healthy Vegeta­ tion,” “Stress Zones,” and “Background.” The output  consists of binary masks for affected vegetation (Dᵢⱼ),  shadowed areas (Sᵢⱼ), and zones of high photosynthetic  activity (Hᵢⱼ), which are merged into the final phytomass  status map. This approach enables the discriminatory  mapping of disease outbreaks and supports management  decisions in precision farming systems. Its effectiveness  stems from the high information content of multispectral  data, the adaptability of machine learning, and its scal­ ability to the level of production fields.

The U-Net architecture progressively reduces spatial  resolution to extract high-level features and then restores  detail by combining features from different scales for pre­ cise localization of affected areas. The output layer gener­ ates three probability channels for the classes: “Cercospo­ ra,” “Healthy leaves,” and “Background.” For training,  the Dice Loss function, which is robust to class imbal­ ance, and the Adam optimizer (learning rate = 0.0001)  were used. The model was trained for 100 epochs with  a batch size of eight images, employing early stopping  based on a validation metric.

To identify phytopathological features, multispectral  UAV data were subject to integrated processing. Figure 4  illustrates the analysis workflow, ranging from the forma­ tion of spectral channels to the construction of the final  plant status map.

Fig. 4. Stages of multispectral image processing for detecting sugar beet phytopathologies:

from acquiring spectral channels to constructing the final plant status map

9

Mudarisov S.G., Miftakhov I.R., Farkhutdinov I.M. Quantitative assessment of sugar beet Cercospora infection based…

Агроинженерия. 2026. Т. 28, № 1. С. 4-15

ТЕХНИКА И ТЕХНОЛОГИИ АПК


## Results and Discussion

The  developed methodology for  quantitative as­
sessment of  sugar beet  (Beta vulgaris L.) infestation 
by  Cercospora leaf spot  (Cercospora beticola Sacc.) 
based on multispectral aerial photography and the U-Net 
semantic segmentation algorithm was validated under 
production conditions. The dataset comprised plots with 
varying degrees of phytopathological impact, which un­
derwent laboratory verification to provide a validation 
basis for assessing the accuracy of automatic detection.

and its dominance in the training set. However, even with  high precision for healthy pixels (Prec = 84.5), there was  a decrease in sensitivity regarding the “Infected plants”  class (F1 = 27.4), indicating insufficient representative­ ness of training features in areas with anomalous spectral  states.

The support vector machine with a radial basis func­ tion kernel (SVM-RBF) method demonstrated the high­ est sensitivity to infected areas, achieving an F1 score  of 42.5 with a precision of 30.1% and recall of 74.2%.  This suggests SVM-RBF’s capability to effectively cap­ ture heterogeneous patterns associated with phytopatho­ logical changes, despite a significant bias in precision.  Compared to PLS-DA, the F1 metric for the “Ingected  plants” class increased by 15.1%, highlighting the fea­ sibility of using SVM-RBF for disease monitoring tasks  with limited prior (a priori) information.

As a result of processing multispectral orthomosa­ ics and calculating vegetation indices (NDVI, NDRE,  MCARI, NSVDI, etc.), we generated a dataset of 420  annotated fragments, classified into three main cate­ gories: infected areas, healthy leaf surface, and back­ ground  (soil/other). Semantic segmentation was used  to  identify infected pixels with an  F1-score accuracy  of up to 46% using an ensemble model, which surpassed  the accuracy of baseline classifiers (PLS-DA, RF, KNN,  SVM) by  18.6 percentage points. This data supports  the hypothesis that hybrid architectures and deep seg­ mentation offer advantages over conventional classifica­ tion methods.

The  Random Forest  (RF) algorithm provided bal­ anced performance across most classes, with F1-scores  of 39.4 for infected plants, 84.0 for healthy plants, and  65.3 for soil. However, when compared to the integrative  pipeline model, it was inferior in all key metrics, partic­ ularly in the segmentation of categories with unstable  spectral profiles (“Other” and “Infected plants”).

The highest accuracy for multiclass categorization  on the test set (88.6%) was achieved using an integrated  algorithmic pipeline combining the strengths of multiple  models (i.e. a combined approach). However, at the indi­ vidual class level, the best metric values varied depending  on class structure and the nature of their spectral manifes­ tation (Table 2).

Linear SVM  (SVML) and KNN methods proved  to be the least effective, with F1-scores for the “Infected”  class at 27.5 and 30.6, respectively, characterized by low  precision and moderate recall. This demonstrates the poor  ability of linear or local methods to generalize under con­ ditions of high intra-class variability.

To  enhance the  reliability of  the  results, five-fold  stratified cross-validation was employed. Confidence  intervals for precision and F1 metrics were calculated  using the bootstrap method with 1,000 iterations. A com­ parison of models based on F1 metrics was conducted  using a t-test (p < 0.05). This approach objectively con­ firmed the statistical significance of the differences be­ tween conventional classification methods (PLS-DA, RF,

The  PLS-DA model demonstrated high gener­ alization capability for  the main classes: “Healthy  plants” (F1 = 86.2) and “Soil” (F1 = 68.4), confirming its  robustness to noise and a balanced trade-off between pre­ cision and recall in the presence of significant inter-class  variance. The F1 score for the “Healthy plants” class  exceeded that of SVM-lin, RF, and KNN by 0.5-4.7%,  likely due to the high spectral homogeneity of this class


> **Table 2**

> Comparative effectiveness of machine learning models for multiclass categorization

of sugar beet crop phytosanitary status based on UAV multispectral imaging data

Class

Method Accuracy

“Infected”  “Healthy”  “Soil”

precision recall F1 precision recall F1 precision recall F1

PLS-DA 87.2 26.8 28.1 27.4 84.5 88.1 86.2 63.1 75.0 68.4

SVML 84.9 25.4 68.4 36.9 85.2 90.2 87.6 62.4 78.6 69.7

SVMR 85.1 30.1 74.2 42.5 84.1 87.3 85.7 61.2 77.3 68.3

RF 82.3 27.5 70.6 39.4 83.4 84.7 84.0 60.9 70.4 65.3

KNN 78.4 20.2 64.0 30.6 81.1 82.0 81.5 55.3 68.0 61.0

Pipeline 88.6 34.7 69.3 46.0 91.6 93.5 92.5 66.5 71.2 68.7

10

Мударисов С.Г., Мифтахов И.Р., Фархутдинов И.М. Количественная оценка поражения сахарной свеклы…

Agricultural Engineering (Moscow), 2026;28(1):4-15

FARM MACHINERY AND TECHNOLOGIES

KNN, SVM) and the proposed U-Net neural network ar­ chitecture.

detection of phytopathological impact, while the pipe­ line acts as  a  tool for  generating a  robust final crop  status map.

The integrative pipeline, which aggregates the out­ put signals of  the  baseline classifiers, demonstrated  the  best balance between sensitivity and specificity,  particularly for  the “Healthy plants”  (F1 = 92.5) and  “Other” (F1 = 78.7) classes. It also provided the highest  F1-score for infected plants (46.0), which is 18.6 percent­ age points (p.p.) higher than that of the PLS-DA model.  These results confirm the feasibility of using ensemble  strategies for  the classification of  complex agrobio­ cenoses based on multispectral information.

To assess the contribution of different types of in­ put features to the final classification, the Area Under  the  Precision-Recall Curve  (AUC-PR) was calculat­ ed. Figure 5 presents the Precision-Recall (PR) curves  for the three object classes. The analysis of PR curves  allows for a quantitative assessment of classification ef­ fectiveness under various feature combinations, including  spectral bands (SB), vegetation indices (VI), digital sur­ face models (DSM), shadows (SH), and red-edge reflec­ tance (RE).

It should be emphasized that the maximum sensitivi­ ty to infected areas is provided specifically by the U-Net  neural network segmentation. For the “Infected plants”  class, U-Net demonstrated an  F1-score of  46.0%,  the  highest among all studied models. At  the  same  time, the  integrative algorithmic pipeline stabiliz­ es the  overall multiclass classification and increases  the final balanced accuracy (Accuracy = 88.6%). Thus,  U-Net serves as  the  key element for  the quantitative

Area Under the Curve (AUC) values reflect the gen­ eralized classification accuracy. The  highest AUC  values were obtained using the  feature combination  SB-VI-SH-DSMₓ-RE: 0.96 for  the “Healthy” class;  0.45 for the “Infected” class; and 0.80 for the “Soil” and  “Other” classes. This indicates the advantage of integrat­ ing multispectral and spatial information for solving pix­ el-wise segmentation tasks.

а b

c

Fig. 5. Precision-Recall dependency in the classification of sugar beet leaf status using

a combination of spectral and spatial features: a – “Healthy plants” class; b – “Infected plants” class; c – combined “Soil and Other” class

11

Mudarisov S.G., Miftakhov I.R., Farkhutdinov I.M. Quantitative assessment of sugar beet Cercospora infection based…

Агроинженерия. 2026. Т. 28, № 1. С. 4-15

ТЕХНИКА И ТЕХНОЛОГИИ АПК

For the “Healthy” class, high classification accuracy  was observed across all feature sets, which is attributed  to the distinct spectral signature of non-infected plants.  The low AUC values for the “Infected” class indicate  the  difficulty of  accurately identifying diseased areas  at early stages. The combined “Soil and Other” class  demonstrates intermediate classification performance,  primarily due to differences in spectral contrast and back­ ground texture.

of 30 m and the camera specifications provided suffi­ cient detail to detect individual spots a few millimeters  in diameter. Increasing the altitude or flight speed may  reduce recognition accuracy; thus, lower altitudes and  high-quality camera optics (or the use of ground-based  imaging for small-scale analysis) are preferable for the  early detection of individual lesions.

The research results confirm the working hypothe­ sis regarding the feasibility of applying U-Net models  to multispectral imagery and demonstrate the capacity  of  this methodology for  implementation in  precision  farming practices. These findings are supported by sta­ tistically significant metrics and are comparable to or  exceed the results of similar scientific publications, testi­ fying to the scientific novelty and high practical signifi­ cance of the developed approach.

The results obtained are comparable to data presented  in several international studies. For instance, in study [1],  which focused on detecting Cercospora leaf spot using  satellite imagery and CNNs, the average detection ac­ curacy did not exceed 78%, confirming the advantage  of using multispectral camera-equipped UAVs for de­ tailed diagnostics. Furthermore, the use of surface vector  normals and the consideration of illumination geometry  in the present work improved the model’s robustness  to varying acquisition angles – a factor not addressed  in most similar studies.

Accuracy analysis of various machine learning mod­ els demonstrated the advantages of a combined pipeline  that integrates the strengths of PLS-DA, SVM, and Ran­ dom Forest. The most robust accuracy indicators were  achieved using ensemble methods, particularly for the  “Healthy plants” class  (F1 = 92.5), while the  highest  sensitivity to infection symptoms was identified in SVM  with a radial basis function kernel (F1 = 42.5). Howev­ er, even with integrated processing, the limited F1-score  values for infected leaves (not exceeding 46%) indicate  the need for further refinement of the training dataset and  the inclusion of additional features reflecting physiologi­ cal changes during the early stages of infection.

The  choice of  data  (high-precision orthomosaics,  spectral and geometric features, and pixel-wise anno­ tation) was driven by  the  need for  reliable modeling  of spatial infection distribution and objective assessment  of segmentation accuracy. The combination of manu­ al verification, quantitative indices, and deep learning  models ensures a high degree of result reproducibility and  system adaptability to other phytopathologies.

Our findings align with current trends in agrotech­ nological research: unmanned systems combined with  computer vision algorithms are gradually replacing man­ ual labor in plant disease diagnostics, providing more  accurate and reproducible information. For  example,  Barreto et al. [9] demonstrated that UAV multispectral  imaging and machine learning can calculate Cercospo­ ra Disease Severity (DS) indices and their temporal dy­ namics. Moreover, automated analysis distinguishes dif­ ferences between varieties more clearly than traditional  visual monitoring. Our approach also opens up prospects  for replacing labor-intensive field assessments with pre­ cise, unbiased image analysis to automatically derive ag­ ronomic metrics such as the percentage of infected leaves  and the area of infection foci.

A comparison of spectral indices and their combi­ nations confirmed that the integration of multispectral  and spatial features  (SB-VI-SH-DSM-RE) achieves  the highest overall classification accuracy (AUC = 0.96  for  healthy plants). This confirms the  importance  of a comprehensive approach when constructing seg­ mentation models for agromonitoring. At the same time,  the lower AUC values for the “Infected” class (0.45)  highlight the difficulty of automatically detecting sub­ tle disease symptoms at initial stages, especially under  conditions of spectral heterogeneity within the crops.  For the early stages of the disease, traditional classifiers  demonstrate a high rate of missed infected pixels (false  negatives), whereas U-Net provides more stable detection  of primary foci (Fig. 6).

It should be noted that the quality of input data is a key  factor in the success of such systems. Multispectral cam­ eras provide useful information in additional bands, im­ proving plant stress recognition accuracy. However, their  spatial resolution may be lower than that of standard  RGB cameras. S. Jay et al. [15] noted that ultra-high-res­ olution RGB images ensured better assessment of mild  infection levels, whereas coarser-resolution drone mul­ tispectral images were only effective in  identifying  advanced disease stages. In our case, a flight altitude

It can be concluded that the developed methodolo­ gy has high practical significance for precision farming  and integrated plant protection. Its application not only  automates the monitoring of phytopathologies but also  enhances the timeliness of decision-making regarding  the feasibility of fungicide applications. This, in turn,  contributes to reducing costs for plant protection products  and minimizing the environmental impact on the agro­ ecosystem.

12

Мударисов С.Г., Мифтахов И.Р., Фархутдинов И.М. Количественная оценка поражения сахарной свеклы…

Agricultural Engineering (Moscow), 2026;28(1):4-15

FARM MACHINERY AND TECHNOLOGIES

a) initial multispectral orthomosaic fragment

b) expert annotation

c) U-Net segmentation result

Fig. 6. Detection of primari infection foci


## Conclusions

1. The research results confirmed the effectiveness 
of  the  proposed methodology for  the quantitative as­
sessment of Cercospora leaf spot infection in sugar beet 
using UAV-based multispectral imaging and the U-Net 
segmentation algorithm. The integration of five spectral 
channels (Blue, Green, Red, Red-edge, NIR), vegeta­
tion indices (NDVI, NSVDI, MCARI, etc.), and spatial 
features (surface normals, shadows) achieved an overall 
multiclass categorization accuracy of 88.6%.


## 2. The  U-Net model demonstrated a  clear advan­

tage over traditional machine learning algorithms: 
the F1-score for the “Infected plants” class was 46.0%, 
which is  18.6 percentage points higher than the  best 
standalone classifier (PLS-DA, F1 = 27.4%). F1-scores 
of 92.5% for “Healthy plants” and 68.7% for “Soil and 
background” were achieved, confirming the balance and 
reliability of the proposed approach.


## 3. The  highest area under the  precision-recall

curve  (AUC = 0.96) was obtained for  the “Healthy

13

Mudarisov S.G., Miftakhov I.R., Farkhutdinov I.M. Quantitative assessment of sugar beet Cercospora infection based…

Агроинженерия. 2026. Т. 28, № 1. С. 4-15

ТЕХНИКА И ТЕХНОЛОГИИ АПК

plants” class, indicating the high reproducibility and ro­ bustness of the methodology against variability in spec­ tral features.

decision-making for plant protection applications and  reducing the  costs of  agrochemical treatments. Fu­ ture research will focus on  expanding the  volume  of  training data, utilizing hyperspectral channels,  and adapting the  developed model for  other crops  and diseases.


## 4. The  proposed approach provides accurate,

scalable, and reproducible detection of  plant in­
fection centers in  field conditions, enabling rapid


## References

1. Görlich F., Marks E., Mahlein A.-K. et al. UAV-based clas­
sification of cercospora leaf spot using RGB images. Drones. 
2021;5(2):34. https://doi.org/10.3390/drones5020034
2. Tuğrul K.M., Kaya R., Özkan K. et al. Early detection of Cer­
cospora beticola and powdery mildew diseases in sugar beet using 
uncrewed aerial vehicle-based remote sensing and machine learn­
ing. PeerJ. 2025;13: e19530. https://doi.org/10.7717/peerj.19530

Список источников 1. Görlich F., Marks E., Mahlein A.-K. et al. UAV-based clas­ sification of cercospora leaf spot using RGB images. Drones.  2021;5(2):34. https://doi.org/10.3390/drones5020034 2. Tuğrul K.M., Kaya R., Özkan K. et al. Early detection of Cer­ cospora beticola and powdery mildew diseases in sugar beet using  uncrewed aerial vehicle-based remote sensing and machine learn­ ing. PeerJ. 2025;13: e19530. https://doi.org/10.7717/peerj.19530


## 3. Кочкаров А.А., Куликов А.К., Ольхова В.А. и др. Интел­

лектуальная система раннего оповещения и мониторинга расте­
ний // Известия ЮФУ. Технические науки. 2025. № 2. С. 61-68. 
https://doi.org/10.18522/2311-3103-2025-2-61-68


## 3. Kochkarov A.A., Kulikov A.K., Olkhova V.A., Ry­

bak А.N., Stacmich А.S. An  intelligent plant moni­
toring and early warning system based. Izvestiya SFe­
dU. Engineering Sciences. 2025;2:61-68.  (In  Russ.) 
https://doi.org/10.18522/2311-3103-2025-2-61-68


## 4. Глухих И.Н., Прохошин А.С., Глухих Д.И., Филато­

ва Т.А. Нейросети компьютерного зрения в системах под­
держки принятия решений на умной ферме // Вестник рос­
сийской сельскохозяйственной науки. 2024. № 1 С. 53-57. 
https://doi.org/10.31857/S2500208224010121


## 4. Glukhikh I.N., Prokhoshin A.S., Glukhikh D.I.,

Filatova T.A. Computer vision neural networks in  sup­
port systems for  making decision on  a  smart farm. Vestnik 
of the Russian Agricultural Science. 2024;1:53-57. (In Russ.) 
https://doi.org/10.31857/S2500208224010121


## 5. Дворниченко А.С., Сосновский И.А., Гапон Н.В., Жда­

нова М.М. Метод распознавания заболеваний виноградных 
кустов по изображениям с использованием нейронных сетей 
// Актуальные проблемы науки и техники-2024: Материалы 
Всероссийской (национальной) научно-практической конфе­
ренции, Ростов-на-Дону, 19-21 марта 2024 г. Ростов-на-Дону: 
Донской государственный технический университет, 2024. 
С. 426-427. EDN: SSIWQS


## 5. Dvornichenko A.S., Sosnovskiy I.A., Gapon N.V., Zh­

danova M.M. Method for recognizing grapevine diseases from 
images using neural networks. Current Problems of Science 
and Technology 2024: Proceedings of the All-Russian (Nation­
al) scientific and practical conference, Rostov-on-Don, March 
19-21, 2024. Rostov-on-Don: Don State Technical University. 
2024:426-427. (In Russ.)
6. Mudarisov S.G., Miftakhov I.R. Deep learning methods 
and UAV technologies for crop disease detection. Agricultur­
al Machinery and Technologies. 2024;18(4):24-33. (In Russ.) 
https://doi.org/10.22314/2073-7599-2024-18-4-24-33


## 6. Мударисов С.Г., Мифтахов И.Р. Методы глубокого

обучения и технологии БПЛА для идентификации забо­
леваний сельскохозяйственных растений // Сельскохозяй­
ственные машины и технологии. 2024. Т. 18, № 4. С. 24-33. 
https://doi.org/10.22314/2073-7599-2024-18-4-24-33


## 7. Shapovalov D.A., Vedeshin L.A., Evstratova L.G., Antosh­

kin A.A. Methods of using multispectral images in ecological mon­
itoring of reclaimed lands. Sovremennye problemy distantsionno­
go zondirovaniya Zemli iz kosmosa = Current Problems in Remote 
Sensing of the Earth from Space. 2023;20;4:187-201. (In Russ.) 
https://doi.org/10.21046/2070-7401-2023-20-4-187-201


## 7. Шаповалов Д.А., Ведешин Л.А., Евстратова Л.Г., Ан­

тошкин А.А. Методы использования мультиспектральных 
снимков при экологическом мониторинге мелиорирован­
ных земель // Современные проблемы дистанционного зон­
дирования Земли из космоса. 2023. Т. 20, № 4. С. 187-201. 
https://doi.org/10.21046/2070-7401-2023-20-4-187-201


## 8. Torkunova Ju.V., Ivanov D.Ye. A mobile application for the

automated diagnosis of diseases of agricultural crops and the se­
lection of recommendations for their treatment. Internation­
al Journal of Advanced Studies. 2024;14;1:168-183. (In Russ.) 
https://doi.org/10.12731/2227-930X-2024-14-1-276


## 8. Торкунова Ю.В., Иванов Д.Э. Мобильное приложе­

ние по автоматизированной диагностике болезней агро­
культур и подбору рекомендаций их лечения // Internation­
al Journal of Advanced Studies. 2024. Т. 14, № 1. С. 168-183. 
https://doi.org/10.12731/2227-930X-2024-14-1-276

9. Barreto A., Yamati F.R.I., Varrelmann M. et  al. Dis­ ease incidence and severity of cercospora leaf spot in sug­ ar beet assessed by  multispectral unmanned aerial images  and machine learning. Plant Disease. 2023;107(1):188-200.  https://doi.org/10.1094/PDIS-12-21-2734-RE

9. Barreto A., Yamati F.R.I., Varrelmann M. et  al. Dis­ ease incidence and severity of cercospora leaf spot in sug­ ar beet assessed by  multispectral unmanned aerial images  and machine learning. Plant Disease. 2023;107(1):188-200.  https://doi.org/10.1094/PDIS-12-21-2734-RE

10. Leite D.V., de Brito A.V., Faccioli G.G., Vieira G.H.S.  Deep learning models for detection and severity assessment  of  Cercospora leaf spot  (Cercospora capsici) in  chili pep­ pers under natural conditions. Plants. 2025;14(13):2011.  https://doi.org/10.3390/plants14132011

10. Leite D.V., de Brito A.V., Faccioli G.G., Vieira G.H.S.  Deep learning models for detection and severity assessment  of  Cercospora leaf spot  (Cercospora capsici) in  chili pep­ pers under natural conditions. Plants. 2025;14(13):2011.  https://doi.org/10.3390/plants14132011

11. Neupane K., Baysal-Gure F. Automatic identifica­ tion and monitoring of plant diseases using unmanned aeri­ al vehicles: A review. Remote Sensing. 2021;13(19):3841.  https://doi.org/10.3390/rs13193841

11. Neupane K., Baysal-Gure F. Automatic identifica­ tion and monitoring of plant diseases using unmanned aeri­ al vehicles: A review. Remote Sensing. 2021;13(19):3841.  https://doi.org/10.3390/rs13193841

14

Мударисов С.Г., Мифтахов И.Р., Фархутдинов И.М. Количественная оценка поражения сахарной свеклы…

Agricultural Engineering (Moscow), 2026;28(1):4-15

FARM MACHINERY AND TECHNOLOGIES

12. Kamilaris A., Prenafeta-Boldú F.X. Deep learning in ag­ riculture: A survey. Computers and Electronics in Agriculture.  2018;147:70-90. https://doi.org/10.1016/j.compag.2018.02.016 13. Mohanty S.P., Hughes D.P., Salathé M. Using deep learning  for image-based plant disease detection. Frontiers in Plant Science.  2016;7:1419. https://doi.org/10.3389/fpls.2016.01419 14. Barbedo J.G.A.  Plant  disease  identifica­ tion from individual lesions and spots using deep learn­ ing.  Biosystems  Engineering.  2019:180;96-107.  https://doi.org/10.1016/j.biosystemseng.2019.02.002

12. Kamilaris A., Prenafeta-Boldú F.X. Deep learning in ag­ riculture: A survey. Computers and Electronics in Agriculture.  2018;147:70-90. https://doi.org/10.1016/j.compag.2018.02.016 13. Mohanty S.P., Hughes D.P., Salathé M. Using deep learning  for image-based plant disease detection. Frontiers in Plant Science.  2016;7:1419. https://doi.org/10.3389/fpls.2016.01419 14. Barbedo J.G.A.  Plant  disease  identifica­ tion from individual lesions and spots using deep learn­ ing.  Biosystems  Engineering.  2019:180;96-107.  https://doi.org/10.1016/j.biosystemseng.2019.02.002

15. Jay S., Comar A., Bénicio R. et al. Scoring Cercospo­ ra leaf spot on sugar beet: Comparison of UGV and UAV phe­ notyping systems. Plant Phenomics. 2020;2020:9452123.  https://doi.org/10.34133/2020/9452123

15. Jay S., Comar A., Bénicio R. et al. Scoring Cercospo­ ra leaf spot on sugar beet: Comparison of UGV and UAV phe­ notyping systems. Plant Phenomics. 2020;2020:9452123.  https://doi.org/10.34133/2020/9452123

16. Bauriegel E., Giebel A., Geyer M. et al. Early detection  of fusarium infection in wheat using hyper-spectral imaging.  Computers and Electronics in Agriculture. 2010;75(2):304-312.  https://doi.org/10.1016/j.compag.2010.12.006

16. Bauriegel E., Giebel A., Geyer M. et al. Early detection  of fusarium infection in wheat using hyper-spectral imaging.  Computers and Electronics in Agriculture. 2010;75(2):304-312.  https://doi.org/10.1016/j.compag.2010.12.006

17. Ronneberger O., Fischer P., Brox T. U-Net: Con­ volutional networks for  biomedical image segmentation.  Lecture Notes in  Computer Science. 2015;9351:234-241.  https://doi.org/10.1007/978-3-319-24574-4_28

17. Ronneberger O., Fischer P., Brox T. U-Net: Con­ volutional networks for  biomedical image segmentation.  Lecture Notes in  Computer Science. 2015;9351:234-241.  https://doi.org/10.1007/978-3-319-24574-4_28

Author Information Salavat G. Mudarisov1, DSc (Eng), Professor;

Информация об авторах


## 1 Мударисов Салават Гумерович, д-р техн. наук, профессор;

salavam@gmail.com*; https://orcid.org/0000-0001-9344-2606; 
SPIN-код: 6893-9957
2 Мифтахов Ильнур Ринатович, канд. техн. наук; 
info323@bk.ru; https://orcid.org/0000-0002-3125-3532; 
SPIN-код: 9429-5990
3 Фархутдинов Ильдар Мавлиярович, д-р техн. наук, доцент; 
ildar1702@mail.ru; https://orcid.org/0000-0002-6443-8584; 
SPIN-код: 8646-6670
1, 2, 3 Башкирский государственный аграрный университет, 
кафедра мехатронных систем и машин аграрного 
производства; 450001, Российская Федерация, 
Республика Башкортостан, г. Уфа, ул. 50 лет Октября, 34

salavam@gmail.com*; https://orcid.org/0000-0001-9344-2606;  Scopus Author ID: 57200284613 Ilnur R. Miftakhov2, CSc (Eng); info323@bk.ru;

https://orcid.org/0000-0002-3125-3532 Ildar M. Farkhutdinov3, DSc (Eng), Associate Professor;

ildar1702@mail.ru; https://orcid.org/0000-0002-6443-8584 1,2,3 Bashkir State Agrarian University, Department of Mechatronic  Systems and Machines for Agricultural Production; St. 50  years of October, 34, Ufa, 450001, Republic of Bashkortostan,  Russian Federation

Author Contribution S.G. Mudarisov – research supervision, methodology; I.R. Miftakhov – investigation, data verification, visualization, writ­ ing – review and editing of the manuscript; I.M. Farkhutdinov – research background analysis, investigation. Conflict of interests The authors declare no conflict of interests and are responsible for  plagiarism.

Вклад авторов С.Г. Мударисов – руководство исследованиями, методология; И.Р. Мифтахов – проведение исследований, верификация дан­ ных, визуализация, создание окончательной версии (доработка)  рукописи и ее редактирование; И.М. Фархутдинов – анализ предметной области, проведение  исследований. Конфликт интересов Авторы заявляют об отсутствии конфликта интересов и несут  ответственность за плагиат.

Received 26.09.2025; Revised 29.11.2025; Accepted 01.12.2025 Статья поступила 26.09.2025, после рецензирования  и доработки 29.11.2025; принята к публикации 01.12.2025

15

Mudarisov S.G., Miftakhov I.R., Farkhutdinov I.M. Quantitative assessment of sugar beet Cercospora infection based…
