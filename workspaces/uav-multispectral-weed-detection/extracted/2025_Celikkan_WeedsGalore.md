---
title: "2025_Celikkan_WeedsGalore"
extraction_engine: pymupdf
---

This paper has been accepted for publication at the IEEE/CVF Winter Conference on Applications of Computer Vision
(WACV) 2025. © IEEE.
WeedsGalore: A Multispectral and Multitemporal UAV-based Dataset for Crop
and Weed Segmentation in Agricultural Maize Fields
Ekin Celikkan1,2
Timo Kunzmann1
Yertay Yeskaliyev1
Sibylle Itzerott1
Nadja Klein3
Martin Herold1
1GFZ German Research Centre for Geosciences
2Humboldt-Universit¨at zu Berlin
3Scientific Computing Center, Karlsruhe Institute of Technology
{ekin.celikkan, itzerott, herold}@gfz.de
nadja.klein@kit.edu
Abstract
Weeds are one of the major reasons for crop yield loss
but current weeding practices fail to manage weeds in an
efficient and targeted manner. Effective weed management
is especially important for crops with high worldwide pro-
duction such as maize, to maximize crop yield for meet-
ing increasing global demands. Advances in near-sensing
and computer vision enable the development of new tools
for weed management.
Specifically, state-of-the-art seg-
mentation models, coupled with novel sensing technologies,
can facilitate timely and accurate weeding and monitoring
systems. However, learning-based approaches require an-
notated data and show a lack of generalization to aerial
imaging for different crops.
We present a novel dataset
for semantic and instance segmentation of crops and weeds
in agricultural maize fields. The multispectral UAV-based
dataset contains images with RGB, red-edge, and near-
infrared bands, a large number of plant instances, dense
annotations for maize and four weed classes, and is mul-
titemporal. We provide extensive baseline results for both
tasks, including probabilistic methods to quantify predic-
tion uncertainty, improve model calibration, and demon-
strate the approach’s applicability to out-of-distribution
data.
The results show the effectiveness of the two ad-
ditional bands compared to RGB only, and better perfor-
mance in our target domain than models trained on existing
datasets. We hope our dataset advances research on meth-
ods and operational systems for fine-grained weed identifi-
cation, enhancing the robustness and applicability of UAV-
based weed management. The dataset and code are avail-
able at https://github.com/GFZ/weedsgalore.
1. Introduction
Weeds are a major reason for crop yield loss as they
compete with desired crops for resources like nutrients, wa-
Figure 1. WeedsGalore dataset. We present a novel reference
dataset for UAV-based weed monitoring for maize fields.
The
dataset a) contains images with 5-bands (RGB, near-infrared, red-
edge) and b) is recorded at different growth stages, fully reflecting
real-world agricultural practices. c) We provide detailed pixel-
level annotations for semantic (multiple weed classes) and in-
stance segmentation.
ter, and space [57]. The global demand for food is con-
stantly rising, while climate change and economic consid-
erations pose challenges to agricultural production [46,62].
Hence, any factor threatening the yield should be managed
and minimized, one such factor being weeds.
There are two common approaches to weeding: Chem-
ical (i.e. spraying herbicides) and mechanical (i.e. physi-
cal removal) weeding. Both treatments have negative en-
vironmental impacts and financial costs.
These are fur-
ther amplified by excessive usage of chemicals, leading to
herbicide-resistant weed populations [50]. In response to
those challenges, site-specific weed management (SSWM)
aims to target weeding to specific areas. To be able to re-
alize SSWM effectively and at scale, as is the case in real-
1
arXiv:2502.13103v1  [cs.CV]  18 Feb 2025


world agricultural fields, automated systems and data with
high temporal and spatial precision are crucial.
Unmanned aerial vehicle (UAV) based systems are one
of the most promising directions in agriculture. They do
not suffer from the drawbacks associated with ground-based
vehicles that have limited viewpoints and the inability to
navigate complex terrains. This makes UAVs ideal candi-
dates for weed monitoring. However, approaches relying
on existing datasets fail to transfer to UAV systems for un-
seen crop types. Maize fields, having the highest world-
wide production in the cereal category [22], are such a do-
main, for which such automated systems are crucial for fu-
ture agricultural practices. There is very limited publicly
available data for weed segmentation in general, especially
when it comes to UAVs and more advanced sensors be-
yond RGB, which contain extra information useful for plant
imaging [45,65]. We introduce WeedsGalore, a dataset for
pixel-level identification of maize and weeds. To the best of
our knowledge, it is the first UAV-based dataset providing
semantic and instance labels for crops and weeds in maize
fields. We use a non-invasive UAV for data acquisition and
provide labels for four weed classes, where the multitempo-
rality is incorporated in terms of diversity in growth stages.
Segmentation models are useful beyond SSWM and
there is an increasing interest in estimating the weed cover
for plant science research, where computer vision-based
weed localization can help in testing and comparing treat-
ments (e.g. herbicides). A typical approach is to conduct
different experiments regarding herbicide applications and
calculate the weed control efficiency of the tested herbi-
cide [39,49]. Traditionally, the weed cover during these ex-
periments has been measured manually, which is naturally
very cumbersome and error-prone [56, 61]. Hence, models
that can accurately segment weeds are vital to support and
accelerate agricultural research. To tackle the current lack
of publicly available datasets for fine-grained weed segmen-
tation in maize fields, our dataset WeedsGalore provides
images with five bands (red, green, blue (RGB), red-edge
(RE), near-infrared (NIR)) and contains four different weed
classes, enabling monitoring of different weed populations.
Model selection plays an integral role in the real-
world deployment of automated weed segmentation meth-
ods since real-world data is typically confronted with un-
seen objects and noisy measurements. As a result, models
that are well-calibrated and quantify prediction uncertainty
realistically are needed, to correctly detect overconfident
predictions and areas of high uncertainties. Both properties
can significantly contribute to risk management and gen-
eralizability in real-world agricultural fields. To meet the
need for reliable methods, we propose to deploy a Bayesian
model with uncertainty quantification on our dataset.
We evaluate WeedsGalore for the tasks of semantic and
instance segmentation. The results show that our dataset
uniquely enables the application of aerial monitoring in
maize fields, and through the use of probabilistic methods
the model performance and calibration can be significantly
improved, especially on out-of-distribution (OOD) data.
In summary, our contributions are:
1. We present a novel reference dataset for crop and weed
segmentation in maize fields, with dense annotations for
multiple weed species covering multiple phenological
stages. To the best of our knowledge, it is the first pub-
licly available multispectral UAV dataset for weed moni-
toring in maize fields, offering two extra bands compared
to conventional RGB datasets and with unprecedented
weed density.
2. We provide extensive quantitative evaluation for seman-
tic and instance segmentation with several state-of-the-
art methods, including probabilistic methods for im-
proved model calibration and uncertainty quantification.
3. We furthermore demonstrate the usefulness of our
dataset by testing our method under real-world condi-
tions and show that models trained on WeedsGalore can
be successfully deployed in unseen maize fields, includ-
ing large-scale orthomosaics.
2. Related Work
2.1. Weed Segmentation for Precision Agriculture
and Plant Science Research
As in many domains, computer vision techniques have
found interest in agricultural applications and research. One
such task is weed monitoring, as there is growing interest
in developing automated weeding systems that effectively
localize and remove weeds from agricultural croplands [6,
14,66]. Existing approaches can be analyzed based on their
choices for system components, such as imaging platform,
sensor/image modality, target application (i.e. crop type),
task formulation, and model selection.
Imaging platform. The majority of existing systems rely
on unmanned ground vehicles (UGVs), although they have
many limitations, for example, the inherent risk of damag-
ing plants, the need for mechanical adjustment to differ-
ent environments, and the deployment on crop fields with
minimal inter- and intra-row distances (e.g. wheat, barley,
etc. [4, 13]). A promising alternative is using images ac-
quired by UAVs (i.e., drones), and localizing and classifying
plants of interest. Our system and data are UAV-based, as
UAVs stand out due to their agile and non-invasive nature,
and commercial availability [35,43].
Imaging sensor.
The overwhelming majority of exist-
ing work on weed segmentation relies only on RGB data
[15,25,58,64], which is surprising as more bands hold use-
ful information for weed segmentation [45, 60]. We uti-
lize multispectral imagery (MSI), which contains two extra
bands compared to regular RGB sensors.
2


Dataset
Year
Crop
Platform
GSD [ px
mm]
Modality
Annotations
#weed classes
#Instances / Image
Multitemp.
Resolution
Semantic
Instance
Crop
Weed
Carrot-Weed [31]
2015
Carrot
UGV
8.95
MSI
✓
✗
1
–
–
✗
1296 × 966
WeedMap [54]
2018 Sugar beet
UAV
>8.3
MSI
✓
✗
1
–
–
✓
–
CoFly-WeedDB [40]
2022
Cotton
UAV
–
RGB
✓
✗
3
–
–
✗
1280 × 720
Sorghum-Weed [25]
2022
Sorghum
UAV
1.0
RGB
✓
✗
1
–
–
✗
–
WE3DS [38]
2023
7*
UGV
0.4
RGB-D
✓
✗
10*
–
–
✓
1600 × 1144
PhenoBench [64]
2023 Sugar beet
UAV
1.0
RGB
✓
✓
1
8.55
5.70
✓
1024 × 1024
CropAndWeed (Fine24) [58] 2023
8*
hand-held
–
RGB
✓
✗
16*
–
–
✓
1920 × 1088
WeedsGalore (Ours)
2024
Maize
UAV
2.5
MSI
✓
✓
4
13.91
64.30
✓
600 × 600
Table 1. Comparison of publicly available real-world agricultural datasets that provide pixel-level annotations for weed and crop
segmentation. GSD refers to ground sampling distance. *Multi-class datasets (i.e. multiple weed and crop classes).
Target crop. [53,64], [40] and [26] use UAV-based images
for weed segmentation, but they are for sugarbeet, cotton
and sorghum fields respectively. [58, 68] segment weeds in
maize fields, but from images acquired by hand-held cam-
eras. In this work, we present a system specifically tailored
for UAV-based weed segmentation in maize fields.
Task formulation. The task is often formulated as a seman-
tic or instance segmentation problem [2,6,45,54]. Given an
input image, the model outputs a prediction (or a full weed
map if the whole field is given as input [54]) indicating per-
pixel semantic classes or instance masks. While the former
is more fitting for targeted spraying (as it concerns larger
patches, and the species information is useful to decide on
the herbicide), and the latter is well-suited for mechanical
weeding (where individual plants are removed); it is possi-
bly the most effective when both are used in combination.
We provide a reference dataset with both semantic and in-
stance annotations, which can be used separately or in com-
bination based on the target task.
Model selection. Early work on weed segmentation heav-
ily relies on classical machine learning methods with multi-
stage pipelines and manual feature extraction [28, 30, 44].
Essentially, all recent approaches utilize state-of-the-art
deep-learning models for weed and crop segmentation. Mil-
ioto et al. [45] propose an encoder-decoder architecture for
pixel-wise segmentation of sugarbeet crops and weeds. [68]
use an improved Swin-Unet, and [51] the PSPNet [69]
(Pyramid Scene Parsing Network) for semantic segmenta-
tion of maize and weed. [61] and [54] deploy several CNN-
based architectures on large-scale orthomosaics for wheat
and sugar beet respectively. Weyler et al. [64] benchmark
various methods like Mask R-CNN [32] and Mask2Former
[9] for panoptic segmentation of sugarbeet and weed. Re-
cently there has been efforts for domain generalized meth-
ods for crop and weed segmentation to perform well under
different field conditions, however, those methods focus on
generalizing to different fields of the same crop and same
acquisition mode [24,63]. Our dataset can be used comple-
mentary with other existing datasets for cross-domain vali-
dation or improved generalization.
2.2. Weed Segmentation Datasets
One of the driving forces behind progress in computer
vision has been the availability of annotated data. Unfortu-
nately, the amount and diversity of agricultural datasets are
limited compared to more general datasets [12, 42] due to
several factors, like the complexity of scenes (e.g. complex
illumination conditions, occlusion, overlap of plant organs)
and the need for expert knowledge for annotations.
A comparison of existing datasets is provided in Tab. 1.
[31] is an early carrot dataset that suffers from low ground
resolution. CoFly-WeedDB [40] contains RGB images cap-
tured on a single day at a cotton field in Greece. It pro-
vides semantic masks only for the weeds, but not the crops.
PhenoBench [64] is a UAV dataset, with pixel-level annota-
tions for semantic and instance segmentation of sugarbeets
and uni-class weeds.
The average number of plants per
image is low, indicating a lack of challenging scenes and
weed infestations. In contrast, our WeedsGalore contains
around 64 weeds per image, compared to 5 of PhenoBench.
WeedMap [54] provides large-scale multispectral orthomo-
saics with semantic annotations for a uni-weed class and
sugarbeet crops, but does not provide raw drone images.
Furthermore, the ground resolution is low, limiting the an-
notation detail and the applicability potential of the dataset.
While less common, there have been recent datasets that
differentiate multiple weed classess.
WE3DS [38] is an
RGB-D dataset, collected with UGV. It contains multiple
crop and weed species. However, the field (near Vienna,
Austria) is a controlled research farm, and high-weed den-
sity areas are left out of the dataset, which does not fully re-
flect the real-life farming scenario. CropAndWeed Dataset
[58] is a collection of RGB images from over a hundred
locations in Austria. The images are collected manually
with a hand-held camera, which is not a suitable acquisition
mode for automated systems in large-scale fields. Tab. 1
highlights the need for a UAV-based crop-weed segmenta-
tion dataset targeting maize fields, with challenging real-
world scenes, which is addressed by our dataset.
3


2.3. Probabilistic Deep Learning and Uncertainty
Quantification for Semantic Segmentation
The majority of the existing state-of-the-art models are
deterministic. As a result, during test time, the model out-
puts a point estimate only. However, accurate uncertainty
quantification (UQ) via e.g., prediction intervals has re-
cently shown to be useful if not necessary to deploy vision
algorithms in real-world automated systems [3,21,34,55].
One approach to quantify model confidence is to rely
on softmax scores. However, this is not always a reliable
metric as uncertain models can output high softmax scores
[23, 52]. An alternative is a Bayesian approach, assuming
probability distributions over the network weights. Com-
monly, variational inference (VI) with Monte Carlo (MC)
dropout [23] and Bernoulli distribution as the variational
density is used to provide approximations to the true pos-
terior distribution. As a non-Bayesian alternative, deep en-
sembles [41] have gained popularity, where the same model
is trained multiple times with different initializations, and
the different samples during inference are used to calculate
predictive uncertainty. However, existing work for preci-
sion agriculture or autonomous weeding systems typically
does not include uncertainty scores in their systems [6]. Ex-
ceptions include [59], who consider epistemic uncertainty
within the acquisition function in an active learning set-
ting; and [5], who report predictive uncertainty scores for
semantic segmentation of crops and weeds on the Sugar-
beets2016 [7] dataset. In this paper, we deploy a proba-
bilistic method, which not only improves segmentation per-
formance but also reports reliable uncertainty scores. We
believe this information is vital to deploy perception algo-
rithms in real-world robotic weeding systems.
3. The WeedsGalore Dataset
We provide a high-resolution UAV dataset for weed
segmentation in maize fields.
In comparison to existing
datasets, we provide extra input bands through multispec-
tral sensing, dense semantic and instance annotations, and
offer by far the largest number of weed instances per image.
3.1. Data Collection
Field Description. The field is located in Marquardt, Pots-
dam, Germany (52°27’50.6”N 12°57’27.5”E) and covers
an area of approximately 1840m2.
To represent realis-
tic agricultural scenarios, the farmers carried out the usual
practices without experimental interference, and weeds oc-
curred naturally.
The maize (Zea mays L.) was planted
across the entire field, on May 9, 2023. The distance be-
tween rows was 70 cm with a 20 cm intra-row distance
between crops. Due to dry conditions, irrigation was ap-
plied on June 6. Herbicide treatment was done on June 12.
Weeds were abundant in quantity as well as species diver-
sity, the most dominant being common amaranth (Amaran-
thus retroflexus). Another species with a strong presence
was a grass-like weed barnyard grass (Echinochloa crus-
gall), with quickweed (Galinsoga parviflora) being the least
common. Apart from those three types of weed, there was
a variety of other species in substantially fewer quantities.
Data Acquisition. The dataset contains images from dif-
ferent dates, hence at different growth stages, plant cover,
and weather conditions. We carried out four data record-
ing campaigns at dates May 25, May 30, June 6, and June
15. The first campaign was when the first leaves of maize
crops appeared (i.e., V1 stage [67]) where there were almost
no weeds present, while the last campaign had almost full
plant cover (both from weeds and crops).
The images were taken with the DJI Phantom P4 Mul-
tispectral, a UAV equipped with five monochromic sen-
sors for multispectral imaging (Blue: 450±16 nm, Green:
560±16 nm, Red: 650±16 nm, Red-Edge: 730±16 nm,
Near-Infrared: 840±26 nm) with effective pixel of 2.08 MP
as well as an RGB sensor [17]. The flights were planned
with DJI GS Pro [16]. The UAV flew with an overlap of
70% side and 60% front overlap, and images were captured
in Hover&Capture mode to ensure the highest possible res-
olution. The flight height was 5 meters to be able to distin-
guish individual plant instances, which resulted in a GSD
(ground sampling distance) of 2.5mm. As a result, approx-
imately 1150 images were taken by the campaign.
Instead of creating the orthomosaic and annotating the
orthophotos, our dataset contains raw images captured by
the drone. This has multiple reasons. Firstly, similar to what
was reported by previous work [64], we have observed the
alignment causes artifacts, and this level of artifacts would
lead to errors in our fine-grained segmentation masks. Sec-
ondly, a model that is trained on raw images can be easily
deployed in the future by spraying robot drones that work
in real-time on the captured images, rather than relying on
a multi-step orthorectification process. Hence, we followed
these steps: First, the five single-band images were aligned
(which corresponds to a translation of few pixels [18]). Sec-
ond, the central 600x600 pixels (a square format that is flex-
ible for processing, e.g. data augmentation) were cropped,
which were finally annotated. There is no overlap between
annotated images. They are sampled from 48 separate loca-
tions as shown in Fig. 3. Yet, to have a clear overview of the
field, and to structure the annotation process, we created the
orthomosaic for each campaign using the software Agisoft
Metashape [1].
3.2. Data Annotation
To ensure the representation of different locations within
the field, we divided the whole field into 12 patches with
equal areas, and randomly sampled 4 geo-referenced point
locations from each patch, resulting in 48 locations (see
4


Fig. 3). 36 of them were annotated for the first three record-
ing dates (which are before the herbicide treatment, hence
more relevant for the weed identification task as the growth
stages of weeds on June 15 is too late for herbicide appli-
cation). The remaining 12 were annotated for all four dates
(marked with darker polygons in Fig. 3), to also provide
data for late-stage weeds, which can be used for either me-
chanical weeding or weed cover analysis. The total anno-
tated ground area corresponds to approximately 128 m2 (per
date). Example scenes from four different dates are shown
in Fig. 2.
May 25
May 30
June 6
June 15
Figure 2.
Change in plant cover over the acquisition time-
line.
Examples from four different dates and semantic masks
(maize, amaranth, barnyard grass, quickweed, weed other).
Best viewed on a colored screen, and zoomed in.
The images were annotated using the web-based tool En-
cord [20]. We used the AI-assisted tool with SAM [37]
point prompt option, where the model made the initial mask
prediction based on the click, which the annotators then re-
fined. Hence, a total of 156 images were annotated by two
annotators and mutually reviewed by three experts to ensure
a high quality of the dataset, where the object boundary of
each plant instance was marked with a polygon (i.e. in-
stance mask) which was also assigned to one of the seman-
tic classes from maize, amaranth, barnyard grass, quick-
weed, or weed other (in the case of rarely grown species or
when it was not possible to distinguish the class due to simi-
lar phenological appearance, especially during early growth
stages).
3.3. Dataset Statistics
We spatially split the data as 70:15:15 (i.e. 8/2/2
patches), such that images from the same location do not
appear in more than one split, even if the data was recorded
at a different date. Fig. 3 shows the splits and correspond-
ing locations in the orthomosaic, and the resulting dataset
statistics can be seen from Tab. 2. In addition to the anno-
tated single images, we include 4 large orthomosaics in our
dataset, providing a large amount of unlabeled data, which
can be utilized for further research (e.g. unsupervised learn-
ing, active learning, plant analysis, etc.) [11,19,59].
Figure 3. Ortohomosaic of the full field and georeferenced lo-
cations of annotated images. Points show captured image lo-
cations, while their colors encode acquisition dates. The dataset
splits are spatially separated by patches into train, validation, and
test. Smaller polygons are drawn around the annotated samples:
The multitemporal dataset contains samples from the same loca-
tions from all dates. Best viewed on screen and zoomed in.
Split
#crops
#weed
#amaranth
#grass
#quickweed
#weed other
#images
Train
1,461
6,512
2,618
1,813
161
1,920
104
Validation
451
1,808
857
258
57
636
26
Test
257
1,711
634
466
31
580
26
Total
2,169
10,031
4,109
2,537
249
3,136
156
Table 2. Dataset statistics. The number of plant instances for
each class within the defined splits are reported.
4. Experiments
We provide extensive evaluation and provide baselines
for our new dataset. Sec. 4.1.1 and Sec. 4.1.2 contain results
for semantic and instance segmentation for different input
data modalities. Sec. 4.2 presents UQ results on our dataset.
Sec. 4.3 presents results on the generalization capabilities of
models trained on our dataset, compared to existing ones.
4.1. Benchmarks
4.1.1
Semantic Segmentation
Implementation Details and Evaluation Metrics.
The
goal of semantic segmentation is to assign pixel-level class
labels. We evaluate two settings: 3-class (i.e., background,
crop, weed) and 6-class (i.e., multiple weed species). For
each task, we provide baselines using two different estab-
lished architectures: DeepLabv3+ [8], and MaskFormer
[10]. To study the influence of additional imaging bands,
we test 3-channel (RGB) and 5-channel (MSI) inputs. We
report intersection-over-union (IoU) scores for each class,
as well as mean IoU (mIoU) amongst all classes.
For both architectures, we start with a pre-trained
ResNet50 [33] backbone, only changing the first convolu-
5


Method
Input
IoUbg
IoUcrop
IoUweed
mIoU
DeepLabv3+ [8]
RGB
97.97
67.93
72.08
79.33
MSI
98.45
72.93
77.31
82.90
MaskFormer [10]
RGB
97.73
70.18
69.85
79.26
MSI
97.99
69.49
73.33
80.27
Table 3. Semantic segmentation scores (%) for the 3-class setting
(uni-weed) on our test set.
Method
Input
IoUbg
IoUcrop
IoUam
IoUgr
IoUqw
IoUwo
mIoU
DeepLabv3+ [8]
RGB
97.94
71.46
74.32
45.95
6.26
8.92
50.81
MSI
98.37
73.03
76.17
53.55
21.11
10.86
55.52
MaskFormer [10]
RGB
97.46
68.28
68.15
41.66
4.92
3.28
47.29
MSI
97.90
68.04
73.11
45.34
8.66
10.86
50.65
Table 4. Semantic segmentation scores (%) for the 6-class setting
on our test set. Crop, am, gr, qw and wo correspond to maize, ama-
ranth, barnyard grass, quickweed and weed other respectively.
tional layer to 5 input channels with random initialization
for the MSI input. The models are trained with Adam op-
timizer [36], batch size of 8, and standard data augmenta-
tion (i.e. rotation, flipping, random jitter) is applied. The
learning rate is set to 0.001 and 0.00003 for DeepLabv3+
and MaskFormer respectively, and training is done on an
Nvidia A100 GPU and an Intel Xeon Ice Lake CPU with
32GB memory, where the final parameters are chosen based
on the validation set.
Results. The results for the 3-class and 6-class variants
can be seen from Tab. 3 and Tab. 4 respectively. The re-
sults show that both architectures achieve similar mIoU,
with DeepLabv3+ having slightly higher scores. While the
additional NIR and RE bands consistently improve perfor-
mance, the effects are more pronounced for the more chal-
lenging 6-class case. An important observation is that the
improvements are most significant for quickweed and weed
other, which are the underrepresented classes. Hence, the
results show that MSI can provide additional information
where data is scarce. The class-wise improvements also dif-
fer between the two chosen architectures. The MSI boost is
the highest for amaranth (the class with most samples) for
MaskFormer, while it’s more prominent for barnyard grass
and quickweed for DeepLabv3+.
Confusion matrices for both cases are shown in Fig. 4
The results for 3-class setting show that 8% of crops are
missed (i.e. predicted as background) while 13% are mis-
classified as weeds. However, for weeds, almost the en-
tire misclassification comes from false negatives (i.e., weed
classified as background), which is especially the case for
very small (early growth-stage) weeds as it can be seen from
qualitative results in Fig. 5. In the 6-class case, the lowest
prediction performance is for quickweed and weed other.
The latter is expected, as several weed species are pooled
together in one class, and they are sometimes classified as
Figure 4. Normalized confusion matrices for semantic segmen-
tation. Scores reported for MSI input and DeepLabv3+ model,
and uni-weed (left) and multi-weed class cases (right).
Input
mAP
mAP50
mAP75
RGB
32.17
33.66
32.01
MSI
32.53
34.70
33.34
Table 5. Instance segmentation scores (%).
one of the other known three categories. Quickweed is clas-
sified as amaranth by 28%, which is a very high ratio. This
could be explained by the phenotypes (visual appearances)
of the two plants, which are both broad-leaf species with
very similar appearances.
4.1.2
Instance Segmentation
Implementation Details and Evaluation Metrics. We use
MaskFormer to provide baseline results for instance seg-
mentation for a 3-class case and both input modalities. We
train the model with the same configuration as in Sec. 4.1.1
and report mAP (mean average precision) scores, which is
calculated for IoU thresholds in the range [0.5, 0.95] with a
step size of 0.05. Moreover, we report mAP50 and mAP75
at 50% and 75% IoU respectively.
Results.
The quantitative scores are reported in Tab. 5.
The two input modalities yield similar results, with MSI
being slightly better.
The baseline scores for instance-
segmentation are overall lower than for other weed segmen-
tation datasets [64], which can be explained by the relatively
large number of plant instances in our dataset (on average
more than 78 plants per image), which makes the task chal-
lenging, especially for small weeds.
4.2. Uncertainty Quantification
Variational Inference with MC Dropout. To model un-
certainty, we employ VI with MC dropout. It is a widely
used UQ method, and has been shown to effectively quan-
tify prediction uncertainty for semantic segmentation of
crops and weeds [5]. We use predictive entropy as the un-
certainty metric.
6


Input
Method
IoUcrop
IoUweed
mIoU
↓ECE
RGB
DLv3+ [8]
67.93
72.08
79.33
0.0058
Prob. DLv3+
69.29
72.19
79.81
0.0041
MSI
DLv3+ [8]
72.93
77.31
82.90
0.0048
Prob. DLv3+
73.90
76.51
82.94
0.0018
Table 6. Comparison of deterministic and probabilistic vari-
ants. Scores for 3-class semantic segmentation on our test set.
Implementation Details and Evaluation Metrics. We im-
plement a probabilistic version of DeepLabv3+, by adding
dropout layers with pd =0.5 between each of the four con-
volutional blocks of the ResNet50 backbone. During infer-
ence, pd is kept at 0.5, and number of forward passes K=5.
We report IoU scores to compare performance with its
deterministic counterpart.
Moreover, we report the ex-
pected calibration error (ECE) [29], which is defined as:
ECE =
M
X
m=1
|Bm|
n
|acc(Bm) −conf(Bm)| ,
where acc and conf represent accuracy and confidence re-
spectively, n is the total number of MC samples and Bm
contains predictions that fall into the mth bin. For the de-
terministic case, the softmax scores are taken as confidence,
whereas for the MC dropout version, we take the average
over the K forward passes during test time.
Results. Tab. 6 shows segmentation scores for the 3-class
case, for both 3-channel (RGB) and 5-channel (MSI) inputs.
For both input modalities, the probabilistic model is sig-
nificantly better calibrated and has consistently higher IoU
scores. The improvement in calibration is the most pro-
nounced for the MSI input, where ECE drops to less than
half. Qualitative results including the predictions, as well
as error and predictive uncertainty are shown in Fig. 5.
Uncertainty, quantified by predictive entropy, is present
at the object borders, a common case in many domains
due to annotation artifacts and expected noise (captured by
aleatoric uncertainty) at the edges [27, 47, 48]. Moreover,
noisy and underrepresented areas, such as the small lumps
of soil or stones in the bottom example, have high uncer-
tainty, which can be attributed to both epistemic (not many
examples in training data) and aleatoric uncertainty (noisy
shadows and varying reflectance values due to changing
weather conditions). Most importantly, the results show a
high correlation between the error and high uncertainty re-
gions. This implies that the model is the most uncertain
about pixels that it misclassified, which is a must-have to
safely deploy algorithms in real-world applications.
4.3. Application to Unseen Data
This section quantitatively demonstrates the need for a
reference dataset, designed specifically for weed monitor-
RGB
Ground Truth
Predictions
Error
Entropy
Figure 5. Qualitative results for probabilistic crop and weed
segmentation for MSI input. The uncertainty is high in regions
that are misclassified, which is a desired and useful information.
ing in maize fields using UAVs, and showcases the gener-
alization potentials of WeedsGalore to unseen data. To this
end, we introduce an additional test field named Maize2024.
This OOD data includes recordings from a different field,
year, plant cover, and unseen (i.e. later) growth stages.
These are the domain shifts that we expect in our applica-
tion. Maize2024, an agricultural area in Marquardt, Pots-
dam, Germany, is an experimental field where half of the
field (12 out of 24 patches) are assigned as control areas
(ie. no herbicide treatment) whereas the other half are test
(ie. sprayed with herbicides). The data is collected with
the same drone after the treatment had its effect on the
field, which means that weeds were mostly eliminated in the
sprayed (test) patches whereas control areas had full plant
cover (i.e. complete weed infestation).
The experimental setup enables informative qualitative
evaluation. A well-performing model is expected to pre-
dict almost full weed cover in control patches, and little in
the sprayed test areas. For the task of 3-class semantic seg-
mentation, we train DeepLabv3+ separately on the follow-
ing datasets: WeedsGalore (ours), PhenoBench [64] (same
acquisition mode, different crop), CropAndWeed [58] (in-
cludes maize along others, different acquisition mode), and
another variant of CropAndWeed, which we refer to as
MaizeOrWeed, a subset of CropAndWeed (1753 images),
including only scenes with maize. Fig. 6 shows qualitative
predictions on the large-scale orthomosaic of Maize2024
for models trained on WeedsGalore and MaizeOrWeed. The
former clearly captures the high weed cover in control areas,
while the latter completely fails to segment any vegetation.
To get quantitative scores, from the Maize2024 orthomo-
saic Fig. 6(a) we annotate 6 cropped patches correspond-
ing to 90 m2 ground area, each of size 1000 × 1100px.
Tab. 7 shows the scores for 3-class semantic segmentation.
The model trained on WeedsGalore (our dataset) achieves
52.55% mIoU on OOD Maize2024 data, 23.22% higher
than the runner-up, confirming the qualitative results. The
scores confirm that the acquisition mode or crop type alone
isn’t sufficient to handle domain shifts, and datasets target-
ing UAV-based weed-maize monitoring are needed.
7


Figure 6. Weed cover monitoring on OOD data. (a) Full orthomosaic of Maize2024 field, where control areas (i.e. not sprayed) have
full plant cover because the weeds took over. Semantic segmentation results (weed vs. crop) for when (b) trained on WeedsGalore and (c)
trained on MaizeOrWeed. A sample patch with its predictions is shown zoomed in. Best viewed on colored screen and zoomed in.
control/test
Input
Ground truth
Prediction
(det., 51%)
Prediction
(prob., 67%)
Entropy
Figure 7. Predictions on Maize2024. Left side of the image from
control, and right from test area. Predictions from both determinis-
tic and probabilistic models are captioned with mIoU scores. The
uncertainty map (i.e. entropy) produced by the probabilistic model
highlights the challenging areas.
We deploy the probabilistic variant of the model on
Maize2024 to show the significance and potentials of prob-
abilistic approaches on unseen data. As it can be seen from
Tab. 7, the probabilistic variant yields a 15% boost in crop
IoU. This increased segmentation performance is accom-
panied by improved model calibration and informative un-
certainty scores. Fig. 7, which includes sample segments
from both control and test areas, qualitatively demonstrates
that the deterministic model tends to misclassify soil and
plant shadows, and parts of maize leaves as weeds, while
probabilistic variant handles those challenging areas better.
A common failure case is when there is full weed cover-
age (i.e. control areas), where many crops are missed by the
model. In those areas, the uncertainty is very high, which
could be useful in a real-world scenario (e.g. even though
the area is segmented as weed, the weeding system may de-
Model
Source
UAV
Maize
IoUbg
IoUcrop
IoUweed
↑mIoU
↓ECE
DLv3+
PhenoBench
✓
✗
56.94
30.80
0.25
29.33
0.4519
DLv3+
CropAndWeed
✗
✓
51.59
0.00
7.02
19.54
0.4130
DLv3+
MaizeOrWeed
✗
✓
50.25
0.00
0.21
16.82
0.5154
DLv3+
WeedsGalore (Ours)
✓
✓
67.10
35.70
54.84
52.55
0.1290
Prob. DLv3+
WeedsGalore (Ours)
✓
✓
68.65
50.37
57.32
58.78
0.0887
Table 7. Results on Maize2024 data. IoU for 3-class semantic
segmentation of DeepLabv3+ trained on different datasets, includ-
ing the probabilistic variant for WeedsGalore.
cide not spray to not to risk potential crops as the uncer-
tainty is very high).
5. Conclusion
We introduce a novel UAV dataset for crop and weed
segmentation in maize fields. The dataset includes mul-
titemporal images from different growth stages and five
spectral bands, along with high-quality instance and se-
mantic annotations.
This reference data can inspire fur-
ther research in aerial weed identification and monitoring.
We present baseline results for semantic and instance seg-
mentation tasks, including probabilistic methods to quan-
tify uncertainty, improve model calibration, and demon-
strate the approach’s applicability for weed cover monitor-
ing on OOD data. We believe that the increased availability
of more datasets targeting different species and using vari-
ous sensing technologies will enhance model development,
aiding automated weeding and monitoring systems.
6. Acknowledgements
The authors acknowledge the support of the Helmholtz
Einstein International Berlin Research School in Data Sci-
ence (HEIBRiDS) and the GFZ Potsdam. This work uti-
lized high-performance computing resources made possible
by funding from the Ministry of Science, Research and Cul-
ture of the State of Brandenburg (MWFK) and are operated
by the IT Services and Operations unit of the Helmholtz
Centre Potsdam.
References
[1] Agisoft.
Agisoft Metashape: Agisoft Metashape — ag-
isoft.com. https://www.agisoft.com/. [Accessed
15-07-2024]. 4
[2] Alireza Ahmadi, Michael Halstead, and Chris McCool.
Bonnbot-i: A precise weed management and crop monitor-
ing platform. In Proceedings of the IEEE/RSJ International
8


Conference on Intelligent Robots and Systems (IROS), pages
9202–9209, 2022. 3
[3] Victor Besnier, David Picard, and Alexandre Briot. Learning
uncertainty for safety-oriented semantic segmentation in au-
tonomous driving. In Proceedings of the IEEE International
Conference on Image Processing (ICIP), pages 3353–3357,
2021. 4
[4] Ullalena Bostr¨om, Lars Eric Anderson, and Ann-Charlotte
Wallenhammar. Seed distance in relation to row distance:
Effect on grain yield and weed biomass in organically grown
winter wheat, spring wheat and spring oats. Field Crops Re-
search, 134:144–152, 2012. 2
[5] Ekin Celikkan, Mohammadmehdi Saberioon, Martin Herold,
and Nadja Klein. Semantic segmentation of crops and weeds
with probabilistic modeling and uncertainty quantification.
In Proceedings of the IEEE/CVF International Conference
on Computer Vision (ICCV) Workshops, 2023. 4, 6
[6] Julien Champ, Adan Mora-Fallas, Herv´e Go¨eau, Erick Mata-
Montero, Pierre Bonnet, and Alexis Joly. Instance segmen-
tation for the fine detection of crop and weed plants by pre-
cision agricultural robots. Applications in Plant Sciences,
8(7):e11373, 2020. 2, 3, 4
[7] Nived Chebrolu, Philipp Lottes, Alexander Schaefer, Wera
Winterhalter, Wolfram Burgard, and Cyrill Stachniss. Agri-
cultural robot dataset for plant classification, localization and
mapping on sugar beet fields. The International Journal of
Robotics Research, 36(10):1045–1052, 2017. 4
[8] Liang-Chieh Chen, Yukun Zhu, George Papandreou, Florian
Schroff, and Hartwig Adam. Encoder-decoder with atrous
separable convolution for semantic image segmentation. In
Proceedings of the European Conference on Computer Vi-
sion (ECCV), pages 801–818, 2018. 5, 6, 7
[9] Bowen Cheng, Ishan Misra, Alexander G. Schwing, Alexan-
der Kirillov, and Rohit Girdhar.
Masked-attention mask
transformer for universal image segmentation. In Proceed-
ings of the IEEE/CVF Conference on Computer Vision and
Pattern Recognition (CVPR), pages 1290–1299, 2022. 3
[10] Bowen Cheng, Alex Schwing, and Alexander Kirillov. Per-
pixel classification is not all you need for semantic segmen-
tation. Advances in Neural Information Processing Systems
(NeurIPS), 34:17864–17875, 2021. 5, 6
[11] Yue Linn Chong, Jan Weyler, Philipp Lottes, Jens Behley,
and Cyrill Stachniss.
Unsupervised generation of labeled
training images for crop-weed segmentation in new fields
and on different robotic platforms. IEEE Robotics and Au-
tomation Letters (RA-L), 8(8):5259–5266, 2023. 5
[12] Marius Cordts, Mohamed Omran, Sebastian Ramos, Timo
Rehfeld,
Markus Enzweiler,
Rodrigo Benenson,
Uwe
Franke, Stefan Roth, and Bernt Schiele.
The cityscapes
dataset for semantic urban scene understanding. In Proceed-
ings of the IEEE/CVF Conference on Computer Vision and
Pattern Recognition (CVPR), pages 3213–3223, 2016. 3
[13] Pasquale De Vita, Salvatore Antonio Colecchia, Ivano
Pecorella, and Sergio Saia.
Reduced inter-row distance
improves yield and competition against weeds in a semi-
dwarf durum wheat variety. European Journal of Agronomy,
85:69–77, 2017. 2
[14] Boyang Deng, Yuzhen Lu, and Jiajun Xu. Weed database de-
velopment: An updated survey of public weed datasets and
cross-season weed detection adaptation. Ecological Infor-
matics, 81:102546, 2024. 2
[15] Jizhong Deng, Zhaoji Zhong, Huasheng Huang, Yubin Lan,
Yuxing Han, and Yali Zhang. Lightweight semantic segmen-
tation network for real-time weed mapping using unmanned
aerial vehicles. Applied Sciences, 10(20), 2020. 2
[16] DJI.
DJI GS Pro.
https://www.dji.com/uk/
ground-station-pro. [Accessed 15-07-2024]. 4
[17] DJI. P4 Multispectral Specs. https://www.dji.com/
uk/p4-multispectral/specs.
[Accessed 15-07-
2024]. 4
[18] DJI. P4 Multispectral Image Processing Guide, 2020. Ver-
sion: 20200717. 4
[19] Alessandro dos Santos Ferreira, Daniel Matte Freitas,
Gercina
Gonc¸alves
da
Silva,
Hemerson
Pistori,
and
Marcelo Theophilo Folhes. Unsupervised deep learning and
semi-automatic data labeling in weed discrimination. Com-
puters and Electronics in Agriculture, 165:104963, 2019. 5
[20] Encord. The Complete Data Development Platform for AI
— Encord. https://encord.com/. [Accessed 15-07-
2024]. 5
[21] Kuai Fang, Daniel Kifer, Kathryn Lawson, and Chaopeng
Shen.
Evaluating the potential and challenges of an un-
certainty quantification method for long short-term memory
models for soil moisture predictions. Water Resources Re-
search, 56(12), Dec. 2020. 4
[22] FAO. Agricultural production statistics 2000–2022. Tech-
nical Report 79, Food and Agriculture Organization of the
United Nations, Rome, 2023. 2
[23] Yarin Gal and Zoubin Ghahramani. Dropout as a bayesian
approximation:
Representing model uncertainty in deep
learning. In Proceedings of the International Conference on
Machine Learning (ICML), pages 1050–1059. PMLR, 2016.
4
[24] Junfeng Gao, Wenzhi Liao, David Nuyttens, Peter Lootens,
Wenxin Xue, Erik Alexandersson, and Jan Pieters. Cross-
domain transfer learning for weed segmentation and map-
ping in precision farming using ground and uav images. Ex-
pert Systems with Applications, 246:122980, 2024. 3
[25] Nikita Genze, Raymond Ajekwe, Zeynep G¨ureli, Flo-
rian Haselbeck, Michael Grieb, and Dominik G. Grimm.
Deep learning-based early weed segmentation using motion
blurred uav images of sorghum fields. Computers and Elec-
tronics in Agriculture, 202:107388, 2022. 2, 3
[26] Nikita Genze, Maximilian Wirth, Christian Schreiner, Ray-
mond Ajekwe, Michael Grieb, and Dominik G. Grimm. Im-
proved weed segmentation in uav imagery of sorghum fields
with a combined deblurring segmentation model.
Plant
Methods, 19(1), Aug. 2023. 3
[27] Ethan Goan and Clinton Fookes. Uncertainty in real-time
semantic segmentation on embedded systems. In Proceed-
ings of the IEEE/CVF Conference on Computer Vision and
Pattern Recognition (CVPR) Workshops, pages 4491–4501,
June 2023. 7
9


[28] J.M. Guerrero, G. Pajares, M. Montalvo, J. Romeo, and M.
Guijarro. Support vector machines for crop/weeds identi-
fication in maize fields. Expert Systems with Applications,
39(12):11149–11155, 2012. 3
[29] Chuan Guo, Geoff Pleiss, Yu Sun, and Kilian Q Weinberger.
On calibration of modern neural networks. In Proceedings of
the International Conference on Machine Learning (ICML),
pages 1321–1330. PMLR, 2017. 7
[30] Sebastian Haug, Andreas Michaels, Peter Biber, and J¨orn
Ostermann. Plant classification system for crop /weed dis-
crimination without segmentation.
In Proceedings of the
IEEE/CVF Winter Conference on Applications of Computer
Vision (WACV), pages 1142–1149, 2014. 3
[31] Sebastian Haug and J¨orn Ostermann. A crop/weed field im-
age dataset for the evaluation of computer vision based pre-
cision agriculture tasks. In Computer Vision - ECCV 2014
Workshops, pages 105–116, 2015. 3
[32] Kaiming He, Georgia Gkioxari, Piotr Doll´ar, and Ross Gir-
shick. Mask r-cnn. In Proceedings of the IEEE/CVF In-
ternational Conference on Computer Vision (ICCV), pages
2961–2969, 2017. 3
[33] Kaiming He, Xiangyu Zhang, Shaoqing Ren, and Jian Sun.
Deep residual learning for image recognition. In Proceed-
ings of the IEEE/CVF Conference on Computer Vision and
Pattern Recognition (CVPR), pages 770–778, 2016. 5
[34] S. Hern´andez and Juan L. L´opez. Uncertainty quantification
for plant disease detection using bayesian deep learning. Ap-
plied Soft Computing, 96:106597, 2020. 4
[35] J. L. E. Honrado, D. B. Solpico, C. M. Favila, E. Tongson,
G. L. Tangonan, and N. J. C. Libatique. Uav imaging with
low-cost multispectral imaging system for precision agricul-
ture applications. In 2017 IEEE Global Humanitarian Tech-
nology Conference (GHTC), pages 1–7, 2017. 2
[36] Diederik Kingma and Jimmy Ba.
Adam: A method for
stochastic optimization.
In International Conference on
Learning Representations (ICLR), 2015. 6
[37] Alexander Kirillov, Eric Mintun, Nikhila Ravi, Hanzi Mao,
Chloe Rolland, Laura Gustafson, Tete Xiao, Spencer White-
head, Alexander C Berg, Wan-Yen Lo, et al.
Segment
anything.
In Proceedings of the IEEE/CVF International
Conference on Computer Vision (ICCV), pages 4015–4026,
2023. 5
[38] Florian Kitzler, Norbert Barta, Reinhard W. Neugschwandt-
ner, Andreas Gronauer, and Viktoria Motsch. We3ds: An
rgb-d image dataset for semantic segmentation in agriculture.
Sensors, 23(5), 2023. 3
[39] Angeliki Kousta, Christos Katsis, Anastasia Tsekoura, and
Dimosthenis Chachalis. Effectiveness and selectivity of pre-
and post-emergence herbicides for weed control in grain
legumes. Plants, 13(2), 2024. 2
[40] Marios Krestenitis, Emmanuel K. Raptis, Athanasios Ch.
Kapoutsis, Konstantinos Ioannidis, Elias B. Kosmatopou-
los, Stefanos Vrochidis, and Ioannis Kompatsiaris. Cofly-
weeddb: A uav image dataset for weed detection and species
identification. Data in Brief, 45:108575, 2022. 3
[41] Balaji Lakshminarayanan, Alexander Pritzel, and Charles
Blundell.
Simple and scalable predictive uncertainty esti-
mation using deep ensembles. In Advances in Neural Infor-
mation Processing Systems (NeurIPS), volume 30, 2017. 4
[42] Tsung-Yi Lin, Michael Maire, Serge Belongie, James Hays,
Pietro Perona, Deva Ramanan, Piotr Doll´ar, and C Lawrence
Zitnick. Microsoft coco: Common objects in context. In
Proceedings of the European Conference on Computer Vi-
sion (ECCV), pages 740–755, 2014. 3
[43] Xu Liu, Steven W. Chen, Guilherme V. Nardari, Chao Qu,
Fernando Cladera, Camillo J. Taylor, and Vijay Kumar.
Challenges and opportunities for autonomous micro-uavs in
precision agriculture. IEEE Micro, 42(1):61–68, 2022. 2
[44] Philipp Lottes, Raghav Khanna, Johannes Pfeifer, Roland
Siegwart, and Cyrill Stachniss. Uav-based crop and weed
classification for smart farming.
In Proceedings of the
IEEE International Conference on Robotics and Automation
(ICRA), pages 3024–3031, 2017. 3
[45] Andres Milioto, Philipp Lottes, and Cyrill Stachniss. Real-
time semantic segmentation of crop and weed for precision
agriculture robots leveraging background knowledge in cnns.
In Proceedings of the IEEE International Conference on
Robotics and Automation (ICRA), pages 2229–2235, 2018.
2, 3
[46] Ant´onio Monteiro and S´ergio Santos. Sustainable approach
to weed management: The role of precision weed manage-
ment. Agronomy, 12(1), 2022. 1
[47] Jishnu Mukhoti and Yarin Gal. Evaluating bayesian deep
learning methods for semantic segmentation. arXiv preprint
arXiv:1811.12709, 2019. 7
[48] Jishnu Mukhoti, Andreas Kirsch, Joost van Amersfoort,
Philip H.S. Torr, and Yarin Gal.
Deep deterministic un-
certainty: A new simple baseline.
In Proceedings of the
IEEE/CVF Conference on Computer Vision and Pattern
Recognition (CVPR), pages 24384–24394, June 2023. 7
[49] Raghav Patel, A. K. Jha, Badal Verma, Muskan Porwal,
Oscar Toppo, and Sourabh Raghuwanshi. Performance of
pinoxaden herbicide against complex weed flora in wheat
(triticum aestivum l.). International Journal of Environment
and Climate Change, 13(7):339–345, May 2023. 2
[50] Mark A Peterson, Alberto Collavo, Ramiro Ovejero, Vinod
Shivrain, and Michael J Walsh. The challenge of herbicide
resistance around the world: a current summary. Pest Man-
agement Science, 74(10):2246–2259, 2018. 1
[51] Artzai Picon, Miguel G. San-Emeterio, Arantza Bereciartua-
Perez, Christian Klukas, Till Eggers, and Ramon Navarra-
Mestre.
Deep learning-based segmentation of multiple
species of weeds and corn crop using synthetic and real
image datasets. Computers and Electronics in Agriculture,
194:106719, 2022. 3
[52] Janis Postels, Mattia Seg`u, Tao Sun, Luca Daniel Sieber, Luc
Van Gool, Fisher Yu, and Federico Tombari. On the prac-
ticality of deterministic epistemic uncertainty. In Proceed-
ings of the International Conference on Machine Learning
(ICML), pages 17870–17909, 2022. 4
[53] Inkyu Sa, Zetao Chen, Marija Popovic, Raghav Khanna,
Frank Liebisch, Juan Nieto, and Roland Siegwart.
weed-
net: Dense semantic weed classification using multispectral
images and mav for smart farming. IEEE Robotics and Au-
tomation Letters, 3(1):588–595, Jan. 2018. 3
10


[54] Inkyu Sa, Marija Popovi´c, Raghav Khanna, Zetao Chen,
Philipp Lottes, Frank Liebisch, Juan Nieto, Cyrill Stachniss,
Achim Walter, and Roland Siegwart. Weedmap: A large-
scale semantic weed mapping framework using aerial multi-
spectral imaging and deep neural network for precision farm-
ing. Remote Sensing, 10(9), 2018. 3
[55] Abhinav Sagar. Uncertainty quantification using variational
inference for biomedical image segmentation. In Proceed-
ings of the IEEE/CVF Winter Conference on Applications of
Computer Vision (WACV) Workshops, pages 44–51, 2022. 4
[56] Gaini Sairam, AK Jha, Badal Verma, Muskan Porwal, MP
Sahu, and RK Meshram. Effect of pre and post-emergence
herbicides on weed flora of maize. International Journal of
Plant & Soil Science, 35(11):68–76, 2023. 2
[57] Aurelio Scavo and Giovanni Mauromicale. Integrated weed
management in herbaceous field crops. Agronomy, 10(4),
2020. 1
[58] Daniel Steininger, Andreas Trondl, Gerardus Croonen, Julia
Simon, and Verena Widhalm. The cropandweed dataset: A
multi-modal learning approach for efficient crop and weed
manipulation. In Proceedings of the IEEE/CVF Winter Con-
ference on Applications of Computer Vision (WACV), pages
3729–3738, 2023. 2, 3, 7
[59] Bart M van Marrewijk, Charbel Dandjinou, Dan Jeric Arcega
Rustia, Nicolas Franco Gonzalez, Boubacar Diallo, J´erˆome
Dias, Paul Melki, and Pieter M Blok.
Active learning
for efficient annotation in precision agriculture:
a use-
case on crop-weed semantic segmentation. arXiv preprint
arXiv:2404.02580, 2024. 4, 5
[60] Aichen Wang, Yifei Xu, Xinhua Wei, and Bingbo Cui. Se-
mantic segmentation of crop and weed using an encoder-
decoder network and image enhancement method under un-
controlled outdoor illumination.
IEEE Access, 8:81724–
81734, 2020. 2
[61] Yuemin Wang, Thuan Ha, Kathryn Aldridge, Hema Duddu,
Steve Shirtliffe, and Ian Stavness. Weed mapping with con-
volutional neural networks on high resolution whole-field
images. In Proceedings of the IEEE/CVF International Con-
ference on Computer Vision (ICCV) Workshops, pages 505–
514, 2023. 2, 3
[62] James H. Westwood, Raghavan Charudattan, Stephen O.
Duke, Steven A. Fennimore, Pam Marrone, David C. Slaugh-
ter, Clarence Swanton, and Richard Zollinger. Weed man-
agement in 2050: Perspectives on the future of weed science.
Weed Science, 66(3):275–285, 2018. 1
[63] Jan Weyler, Thomas L¨abe, Federico Magistri, Jens Behley,
and C. Stachniss.
Towards domain generalization in crop
and weed segmentation for precision farming robots. IEEE
Robotics and Automation Letters, 8:3310–3317, 2023. 3
[64] Jan Weyler, Federico Magistri, Elias Marks, Yue Linn
Chong, Matteo Sodano, Gianmarco Roggiolani, Nived Che-
brolu, Cyrill Stachniss, and Jens Behley.
PhenoBench: A
Large Dataset and Benchmarks for Semantic Image Inter-
pretation in the Agricultural Domain . IEEE Transactions
on Pattern Analysis & Machine Intelligence, 46(12):9583–
9594, 2024. 2, 3, 4, 6, 7
[65] Franziska Wolff, Tiina H. M. Kolari, Miguel Villoslada,
Teemu Tahvanainen, Pasi Korpelainen, Pedro A. P. Zamboni,
and Timo Kumpula. Rgb vs. multispectral imagery: Map-
ping aapa mire plant communities with uavs. Ecological In-
dicators, 148:110140, 2023. 2
[66] Xiaolong Wu, St´ephanie Aravecchia, Philipp Lottes, Cyrill
Stachniss, and C´edric Pradalier. Robotic weed control using
automated weed and crop classification.
Journal of Field
Robotics, 37(2):322–340, 2020. 2
[67] Yang Yue, Jin-Hai Li, Li-Feng Fan, Li-Li Zhang, Peng-Fei
Zhao, Qiao Zhou, Nan Wang, Zhong-Yi Wang, Lan Huang,
and Xue-Hui Dong. Prediction of maize growth stages based
on deep learning. Computers and electronics in agriculture,
172:105351, 2020. 4
[68] Jiaheng Zhang, Jinliang Gong, Yanfei Zhang, Kazi Mostafa,
and Guangyao Yuan.
Weed identification in maize fields
based on improved swin-unet. Agronomy, 13(7), 2023. 3
[69] Hengshuang Zhao, Jianping Shi, Xiaojuan Qi, Xiaogang
Wang, and Jiaya Jia. Pyramid scene parsing network. In Pro-
ceedings of the IEEE/CVF Conference on Computer Vision
and Pattern Recognition (CVPR), pages 2881–2890, 2017. 3
11
