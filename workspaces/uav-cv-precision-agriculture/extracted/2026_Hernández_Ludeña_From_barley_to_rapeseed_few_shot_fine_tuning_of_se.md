---
workspace_id: SCI-000160
doi: 10.2139/ssrn.7345639
title: 'From barley to rapeseed: few-shot fine-tuning of semantic segmentation models
  for weed detection using UAV multispectral imagery'
authors:
- family_name: "Hern\xE1ndez Lude\xF1a"
  given_name: Patricio  Alonso
  orcid: null
- family_name: "Fern\xE1ndez Pi\xF1ar"
  given_name: Carlos
  orcid: null
- family_name: "L\xF3pez de Herrera"
  given_name: Juan
  orcid: null
- family_name: Herrero Tejedor
  given_name: "Tom\xE1s  Ram\xF3n"
  orcid: null
- family_name: "P\xE9rez Martin"
  given_name: Enrique
  orcid: null
- family_name: Raimundo
  given_name: Javier
  orcid: null
- family_name: "Calder\xF3n"
  given_name: Jonathan
  orcid: https://orcid.org/0009-0002-6988-5962
year: 2026
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:46:38.418622+00:00'
---

# From barley to rapeseed: few-shot fine-tuning of semantic segmentation models for weed detection using UAV multispectral imagery

Preprint not peer reviewed

1 From barley to rapeseed: few-shot fine-tuning of semantic segmentation models

2 for weed detection using UAV multispectral imagery

3 Patricio Alonso Hernández Ludeña¹*, Carlos Fernández Piñar¹, Juan López de Herrera¹,

4 Tomás Ramón Herrero Tejedor¹, Enrique Pérez Martin¹, Javier Raimundo¹, Jonathan

5 Calderón¹

6 ¹ Department of Agroforestry Engineering, Escuela Técnica Superior de Ingeniería

7 Agronómica, Alimentaria y de Biosistemas, Universidad Politécnica de Madrid,

8 Madrid, Spain.

9 * Corresponding author: Patricio Hernández

10 Email address: Patricio.hernandez@alumnos.upm.es

11 Abstract

12 Site-specific weed management requires accurate spatial information on weed

13 distribution, which remains challenging when models are transferred between crops and

14 field conditions. This study evaluated multispectral UAV imagery and semantic

15 segmentation models for weed mapping in barley, with a focus on spatial generalisation

16 to an independent field and cross-crop transfer to rapeseed. Four spectral configurations

17 (RGB, RGB + NIR + RedEdge, RGB + vegetation indices, and full multispectral) and

18 three modelling approaches (U-Net, DeepLabv3, and Random Forest) were compared.

19 The full configuration (RGB + NIR + RedEdge + NDVI + NDRE + VARI) combined

20 with U-Net achieved the best performance, with a weed F1-score of 0.5833 and an

21 mIoU of 0.5448. Spatial validation on an independent barley field yielded a weed F1-

22 score of 0.6455 (IoU = 0.4766). Direct transfer to rapeseed performed poorly (F1 =

23 0.0534), indicating a severe domain shift. However, few-shot fine-tuning with only 63

24 labelled rapeseed patches (15 % of the available dataset) recovered performance to F1 =

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

25 0.6274, approaching the barley-domain result. These findings show that domain

26 adaptation with limited labelled data can effectively transfer semantic segmentation

27 models to new crops while reducing annotation effort for operational deployment. The

28 resulting weed probability and density maps illustrate the practical potential of this

29 approach for supporting variable-rate herbicide application.

30 Keywords: site-specific weed management; cross-crop transfer; spatial validation;

31 variable-rate herbicide application; phenological variability; weed mapping

32 1. Introduction

33 Weeds represent one of the main threats to the productivity of extensive crops,

34 competing with the crop for water, nutrients, light and space, and causing significant

35 yield losses (Horvath et al., 2023; Soltani et al., 2016). In winter cereals, these losses

36 can exceed 30% in the absence of control  (Oerke, 2006). Conventional management

37 relies on the homogeneous application of herbicides across the entire field, ignoring that

38 weed communities typically show a spatially heterogeneous distribution within fields

39 (Nkoa et al., 2015; Rew and Cousens, 2001). This variability implies that a portion of

40 herbicide applications is carried out in areas with low or no weed pressure, generating

41 additional economic costs and unnecessary environmental burden. This scenario

42 reinforces the interest in site-specific management strategies (Gerhards et al., 2022;

43 López-Granados, 2011; San Martín et al., 2016), in which precision agriculture can play

44 a key role.

45 Precision agriculture provides the necessary tools to account for the spatial

46 heterogeneity of crops by integrating data acquisition technologies, image analysis and

47 decision support systems. In this context, unmanned aerial vehicles (UAVs) have

48 become key platforms for weed mapping, as they allow the acquisition of very high

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

49 spatial resolution imagery at specific phenological stages (Rasmussen et al., 2021;

50 Roslim et al., 2021). Unlike satellite sensors, UAV imagery captures canopy structure

51 and the distribution of unwanted vegetation at sub-field scale in greater detail.

52 Furthermore, the use of multispectral sensors expands the possibilities for spectral

53 discrimination by incorporating bands such as NIR and RedEdge, from which

54 vegetation indices related to vigour, cover and the physiological status of vegetation can

55 be computed (Sa et al., 2018; Xue and Su, 2017).

56 Despite these advantages, automatic weed detection under real field conditions remains

57 challenging. Spectral similarity between crop and weeds, plant overlap, shadows, soil

58 heterogeneity and phenological changes throughout the crop cycle hinder class

59 separation using approaches based solely on spectral information (Ampatzidis and

60 Partel, 2019; Lu and He, 2017; Müllerová et al., 2021; Shuai et al., 2019). In high-

61 resolution imagery, the greater spatial detail allows small objects to be identified, but

62 also increases intra-class variability, which further complicates discrimination.

63 Therefore, weed detection requires approaches that integrate spectral, spatial and

64 contextual information, a capability that deep learning models can provide.

65 In response to these limitations, deep learning models have been rapidly adopted for the

66 analysis of high-resolution agricultural imagery, outperforming traditional classifiers in

67 weed detection and segmentation tasks (Murad et al., 2023; Vasileiou et al., 2024; Wu

68 et al., 2021). In particular, convolutional neural networks (CNNs) automatically learn

69 complex spatial and spectral patterns, which is especially valuable in scenarios with

70 high visual heterogeneity. Among the most widely used architectures for semantic

71 segmentation, which assigns a class to each pixel, are U-Net (Ronneberger et al., 2015)

72 and DeepLabv3 (Chen et al., 2017), capable of generating detailed maps of crop, soil

73 and weeds (Sa et al., 2018; Zou et al., 2021). However, most evaluations have been

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

74 conducted on datasets from a single field or acquisition condition, so the extent to which

75 these models can generalise to new locations or different crops remains uncertain, a key

76 question for their practical application in precision agriculture.

77 In addition to model architecture, the choice of input variables decisively influences the

78 performance of segmentation systems. Although RGB images are the most accessible,

79 they can be insufficient when crops and weeds exhibit similar visual responses. The

80 incorporation of multispectral bands such as near-infrared (NIR) and RedEdge, together

81 with derived vegetation indices, allows information on vigour, cover and physiological

82 status to be captured (Xue and Su, 2017). However, the actual gain associated with

83 these additional variables is not systematic, as it depends on the crop, phenological

84 stage and acquisition conditions (Sa et al., 2018). Therefore, it is necessary to

85 empirically evaluate which combination of bands and indices is most suitable for weed

86 detection in each agronomic scenario.

87 Therefore, the objective of this study was to evaluate the capacity of semantic

88 segmentation models based on multispectral UAV imagery to detect and map weeds in

89 barley (Hordeum vulgare L.), with particular attention to the model’s spatial

90 generalisation to an independent field. For this purpose, different spectral input

91 configurations were compared, combining RGB, NIR, RedEdge bands and vegetation

92 indices, together with different modelling architectures (U-Net, DeepLabv3 and

93 Random Forest as a reference). Additionally, cross-crop transfer to rapeseed (Brassica

94 napus L.) was explored, and weed probability and density maps were generated as

95 products oriented towards site-specific management in precision agriculture.

96 Furthermore, a few-shot fine-tuning strategy was evaluated to adapt the model to the

97 rapeseed domain using a reduced number of labelled samples, in order to assess the

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

98 potential of this approach to facilitate cross-crop transfer while reducing annotation

99 effort

100 2. Materials and methods

101 2.1. Study area and UAV data acquisition

102 The study was conducted in Valdeavero (Community of Madrid; ~40°30′N, 3°22′W) on

103 three extensive crop fields: two barley fields, Barley 1 (11.83 ha) and Barley 2 (15.93

104 ha), and one rapeseed field (8.39 ha). Barley 1 was used for training and temporal

105 validation, Barley 2 for spatial validation, and rapeseed for exploratory cross-crop

106 transfer evaluation. All cartographic products were georeferenced to ETRS89/UTM

107 zone 30N (Fig. 1).

108

109 Fig. 1: Location of the study fields.

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

110 Images were acquired at an altitude of 120 m using a DJI Phantom 4 RTK for RGB

111 imagery (20 MP) and a DJI Matrice 600 Pro equipped with a MicaSense Altum-PT

112 camera for multispectral acquisition (Red, Green, Blue, NIR and RedEdge bands).

113 Radiometric calibration was performed before each flight using a calibrated reflectance

114 panel and an incident light sensor (ILS). Two acquisition campaigns were conducted:

115 V1 (3 March), corresponding to the late tillering stage of barley (BBCH 25–29), and V2

116 (14 May), coinciding with barley heading (BBCH 51–55) and rapeseed full flowering

117 (BBCH 65). While the canopy remained relatively open in V1, allowing greater

118 visibility of weeds between rows, canopy closure in V2 reduced soil exposure and

119 increased the occlusion of adventitious vegetation. The use of both phenological stages

120 allowed greater spectral and structural variability to be incorporated into the training set.

121 2.2. Image preprocessing and spectral variable generation

122 RGB and multispectral images were processed using Structure-from-Motion

123 photogrammetric workflows in Pix4D and Agisoft Metashape to generate georeferenced

124 orthomosaics. Subsequently, the orthomosaics were imported into ArcGIS Pro to verify

125 band alignment, clip the images to the study area, and stack the spectral layers required

126 for the analysis. The final orthomosaics had an approximate spatial resolution of 5

127 cm/pixel.

128 From the available spectral bands, six vegetation indices were computed: NDVI,

129 GNDVI, NDRE, CCCI, SAVI and VARI. To select the most representative indices and

130 reduce redundancy among variables, a Pearson correlation analysis was performed

131 between the spectral bands and the computed indices. Based on this analysis, NDVI,

132 NDRE and VARI were selected as input indices for the models: NDVI as a general

133 indicator of vegetative vigour, NDRE for its relationship with the response in the

134 RedEdge region and relative chlorophyll content, and VARI as a complementary index

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

135 based solely on visible-spectrum bands. Before introducing the spectral variables into

136 the models, all bands and indices were independently normalised using a scaling based

137 on the 2nd and 98th percentiles of each patch, subsequently rescaling the values to the

138 [0, 1] interval. This procedure reduces the influence of extreme values and improves

139 robustness against radiometric differences between flights without sharing statistics

140 between training and evaluation sets.

141 2.3. Reference mask generation and patch dataset construction

142 Reference masks were generated by manual digitisation in ArcGIS Pro on the RGB

143 orthomosaics of Barley 1 (V1 and V2), defining three classes: crop, weed and soil. The

144 digitised polygons were rasterised to the orthomosaic resolution, assigning a label to

145 each pixel and ensuring spatial alignment with the spectral layers and vegetation

146 indices. The same procedure was applied to Barley 2 (V2) and to the Rapeseed (V2)

147 field, subsequently used for spatial validation and cross-crop transfer evaluation. From

148 the images and their associated masks, patches of 256 × 256 pixels were generated with

149 50% overlap (stride = 128) using a Python script, maintaining spatial correspondence

150 between each patch and its mask.

151 Although the patches had a 50% overlap, the experimental design avoided the risk of

152 spatial data leakage, since in no experiment were the training and evaluation sets

153 obtained through a random split of patches from the same orthomosaic. Temporal

154 validation was performed using independent flights (Barley 1-V1 for training and

155 Barley 1-V2 for evaluation), while spatial validation used a completely independent

156 field (Barley 2). This approach follows the recommendations proposed to avoid

157 overestimation of performance caused by spatial autocorrelation in geographic data

158 (Meyer et al., 2018; Roberts et al., 2017).

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

159 This process produced 726 patches for Barley 1-V1 and 524 patches for Barley 1-V2,

160 used in the training, temporal validation, spatial validation and model comparison

161 phases. The masks corresponding to Barley 2 and Rapeseed were generated following

162 exactly the same manual digitisation protocol used for Barley 1. For the adaptation

163 experiments via few-shot fine-tuning, an additional 423 patches were generated from

164 the Rapeseed-V2 field. From this set, random samples without replacement equivalent

165 to approximately 5%, 10% and 15% of the total (21, 42 and 63 patches, respectively)

166 were taken for fine-tuning. The selected patches were subsequently excluded from the

167 evaluation set, ensuring in all cases the independence between training and testing.

168 2.4. Experimental design

169 The experimental design was organised into five phases in order to separately evaluate

170 the contribution of spectral information, model architecture and system generalisation

171 capacity. First, four spectral input configurations were compared using U-Net as the

172 reference architecture: i) RGB; ii) RGB + NIR + RedEdge; iii) RGB + selected indices,

173 including NDVI, NDRE and VARI; and iv) full configuration, consisting of RGB +

174 NIR + RedEdge + NDVI + NDRE + VARI. Second, once the best-performing spectral

175 configuration was identified, three modelling approaches were compared: U-Net,

176 DeepLabv3 and Random Forest (RF). The first two were used as semantic segmentation

177 models, while RF was used as a classical pixel-level reference classifier. Third, the best

178 model-configuration pair was retrained using both the Barley 1-V1 and Barley 1-V2

179 data, and evaluated on the independent Barley 2-V2 field. This phase aimed to analyse

180 the spatial generalisation capacity of the model within the same crop. Fourth, cross-crop

181 transfer was explored. For this purpose, the barley-trained model was applied directly to

182 the Rapeseed-V2 field, without retraining or fine-tuning, in order to quantify the effect

183 of domain shift between crops. Finally, after evaluating direct transfer to rapeseed, an

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

184 additional experiment was designed to analyse the model’s adaptation capacity using a

185 reduced number of labelled samples from the target crop. For this purpose, the complete

186 set of 423 patches generated from the Rapeseed-V2 orthomosaic was used. On this set,

187 random samples without replacement equivalent to approximately 5%, 10% and 15% of

188 the total (21, 42 and 63 patches, respectively) were taken for fine-tuning. The selected

189 patches were subsequently excluded from the evaluation set to ensure independence

190 between training and testing. Two adaptation strategies were evaluated: (i) partial fine-

191 tuning, keeping the encoder frozen and updating only the decoder, and (ii) full fine-

192 tuning, allowing the update of all network parameters. Performance was evaluated for

193 the three classes considered — crop, weeds and soil — although the analysis focused on

194 the weed class, as it is the class of greatest agronomic interest.

195

196 Fig. 2: Methodological workflow of the study, from UAV image acquisition and

197 preprocessing to the comparison of spectral configurations, model selection, spatial

198 validation, cross-crop transfer and final map generation.

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

199 2.5. Segmentation models and training setup

200 Two deep learning-based semantic segmentation architectures, U-Net and DeepLabv3,

201 were evaluated together with a pixel-wise Random Forest (RF) classifier used as a

202 baseline. This selection enabled the comparison of two convolutional neural network

203 architectures with different feature extraction strategies while providing a conventional

204 machine learning reference based exclusively on spectral information.

205 U‑Net (Ronneberger et al., 2015) was implemented from scratch without pre-trained

206 weights. The architecture followed a symmetric encoder-decoder design with skip

207 connections linking encoder and decoder feature maps at each resolution level. These

208 connections preserve fine spatial details lost during downsampling, which is particularly

209 important for segmenting small and irregular weed patches. Each convolutional block

210 consisted of two 3 × 3 convolutional layers followed by batch normalisation and ReLU

211 activation. Downsampling was performed using max-pooling, whereas upsampling

212 employed transposed convolutions.

213 DeepLabv3 (Chen et al., 2017) was implemented with a ResNet-50 backbone, also

214 without ImageNet pre-trained weights. The first convolutional layer was modified to

215 accept eight input channels (RGB, NIR, RedEdge, NDVI, NDRE and VARI) instead of

216 the standard three. The architecture incorporates an Atrous Spatial Pyramid Pooling

217 (ASPP) module that captures multi-scale contextual information through parallel dilated

218 convolutions with different dilation rates, increasing the receptive field while preserving

219 spatial resolution.

220 The Random Forest classifier consisted of 200 decision trees trained using the same

221 spectral variables provided to the deep learning models. Unlike convolutional neural

222 networks, RF classifies each pixel independently and does not exploit spatial context.

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

223 Its inclusion provided a conventional baseline for quantifying the benefits of spatial

224 feature learning achieved by semantic segmentation networks.

225 Unless otherwise specified, the deep learning models were trained for 30 epochs using

226 the Adam optimiser with an initial learning rate of 1 × 10⁻³ and a weighted cross-

227 entropy loss function to compensate for class imbalance. Training was performed using

228 the Barley 1-V1 dataset, whereas Barley 1-V2 was used for temporal validation.

229 2.6. Evaluation metrics

230 Model performance was assessed using the F1-score and Intersection over Union (IoU)

231 computed separately for the crop, weed and soil classes. Overall segmentation

232 performance was summarised using the mean Intersection over Union (mIoU). Because

233 weed detection is the primary objective of site-specific weed management and weeds

234 represented the minority class in the dataset, the analysis focused primarily on the weed

235 F1-score and weed IoU. The F1-score combines precision and recall into a single metric

236 and is particularly appropriate for imbalanced classification problems. For every

237 experiment, the model corresponding to the training epoch that achieved the highest

238 weed F1-score on the validation dataset was retained for subsequent analyses. During

239 the few-shot adaptation experiments, lower learning rates than those used during the

240 initial training were adopted (1 × 10⁻⁴ for partial fine-tuning and 5 × 10⁻⁵ for full fine-

241 tuning). Training was performed for a maximum of 30 epochs using the Adam

242 optimiser, and the final model was selected through early stopping based on the weed

243 F1-score on the validation dataset.

244 2.7. Weed probability and density mapping

245 The best-performing model identified during the comparison experiments was applied

246 to the complete Barley 2-V2 orthomosaic using a sliding-window inference strategy

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

247 with the full spectral configuration. Image patches of 256 × 256 pixels were extracted

248 with 50% overlap (stride = 128 pixels), matching the input dimensions used during

249 model training. For overlapping regions, the predicted weed probabilities were averaged

250 to generate a continuous probability surface while minimising border artefacts between

251 adjacent predictions. The resulting weed probability map was subsequently aggregated

252 into 2 × 2 m grid cells to produce a relative weed density map. Weed density was

253 calculated as the mean predicted weed probability within each grid cell. Finally, the

254 density values were classified into four infestation levels (very low, low, medium and

255 high) to facilitate agronomic interpretation and support site-specific herbicide

256 application.

257 3. Results

258 3.1. Dataset characteristics

259 Patch extraction produced 726 labelled patches from Barley 1-V1 and 524 from Barley

260 1-V2, resulting in a total of 1,250 patches used for model training and evaluation. In

261 both acquisition campaigns, the crop class accounted for the largest proportion of

262 labelled pixels, whereas weeds represented the minority class. This class imbalance was

263 considered during model training by applying a weighted loss function and was taken

264 into account when interpreting the class-specific performance metrics. The datasets used

265 for spatial validation and cross-crop transfer were generated from Barley 2-V2 and

266 Rapeseed-V2, respectively, following the same annotation and patch extraction

267 procedure.

268 3.2. Effect of spectral input configuration on U-Net performance

269 The four spectral input configurations evaluated with U-Net showed a progressive

270 improvement in weed detection performance as additional spectral information was

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

271 incorporated (Fig. 3). The RGB-only configuration achieved a weed F1-score of 0.5193

272 and an IoU of 0.3508. Adding the NIR and RedEdge bands resulted in only a marginal

273 improvement (F1 = 0.5238, IoU = 0.3548). Incorporating the selected vegetation indices

274 (NDVI, NDRE and VARI) into the RGB imagery produced a more substantial increase

275 in performance, reaching a weed F1-score of 0.5461 and an IoU of 0.3756. The highest

276 performance was obtained using the full spectral configuration (RGB + NIR + RedEdge

277 + NDVI + NDRE + VARI), which achieved a weed F1-score of 0.5833 and an IoU of

278 0.4117. Consequently, this configuration was selected for all subsequent experiments.

279

280 Fig. 3: U-Net performance obtained with the four evaluated spectral input

281 configurations. Bars represent weed F1-score and weed IoU. The full multispectral

282 configuration includes RGB, NIR, RedEdge, NDVI, NDRE and VARI.

283 3.3. Model comparison

284 Using the full spectral configuration, U-Net outperformed DeepLabv3 and Random

285 Forest across all evaluation metrics (Fig. 4). U-Net achieved the highest weed F1-score

286 (0.5833) and IoU (0.4117), together with the highest overall mIoU (0.5448).

287 DeepLabv3 obtained considerably lower performance (F1 = 0.2723, IoU = 0.1576,

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

288 mIoU = 0.2736), whereas Random Forest produced the lowest scores (F1 = 0.0794, IoU

289 = 0.0414, mIoU = 0.2248). The qualitative comparison presented in Fig. 5 supports

290 these quantitative results. U-Net generated spatially coherent predictions with well-

291 defined weed patches, whereas DeepLabv3 tended to produce smoother and more

292 homogeneous predictions with limited spatial detail. In contrast, Random Forest

293 generated fragmented predictions with a high level of pixel-level noise, reflecting its

294 inability to exploit spatial context. Based on these results, U-Net was selected for the

295 subsequent spatial validation, cross-crop transfer and few-shot adaptation experiments

296

297 Fig. 4: Comparison of U-Net, DeepLabv3 and Random Forest using the full spectral

298 configuration. Weed F1-score, weed IoU and mean Intersection over Union (mIoU) are

299 shown for each model.

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

300

301 Fig. 5: Representative image patch from the spatial validation dataset (Barley 2)

302 showing the RGB input and the corresponding predictions produced by U-Net,

303 DeepLabv3, and Random Forest. Ground-truth masks are not shown because the

304 reference annotations were generated by targeted polygon digitisation rather than

305 exhaustive pixel-level labelling. Colour code: green = crop, red = weed, brown = soil.

306 3.4. Spatial validation in an independent barley field

307 The U-Net model retrained using the combined Barley 1-V1 and Barley 1-V2 datasets

308 and evaluated on the independent Barley 2-V2 field achieved a weed F1-score of 0.6455

309 and an IoU of 0.4766 (Table 1). These values were higher than those obtained during

310 the initial temporal validation (F1 = 0.5833, IoU = 0.4117), indicating that incorporating

311 data from both acquisition campaigns improved the model's ability to generalise to an

312 independent barley field. The weed F1-score reached its maximum value at epoch 9,

313 with no further improvement during the remaining training epochs (Fig. 6A). The

314 corresponding normalised confusion matrix (Fig. 6B) showed high classification

315 accuracy for the weed class, although some confusion between crop and soil remained.

316 Table 1. Comparison of temporal and spatial validation performance obtained with U-

317 Net.

Validation

Training

dataset Test dataset Weed F1-score Weed IoU

type

Temporal  validation Barley 1-V1 Barley 1-V2 0.5833 0.4117

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

Spatial  validation

Barley 1-V1 +  Barley 1-V2 Barley 2-V2 0.6455 0.4766

318

319

320 Fig. 6: Spatial validation of the U-Net model on the independent Barley 2-V2 field. (A)

321 Evolution of the weed F1-score during training. The highest performance was obtained

322 at epoch 9. (B) Normalised confusion matrix corresponding to the selected model.

323 3.5. Cross-crop transfer and weed density maps

324 Direct application of the U-Net model trained on barley to the Rapeseed-V2 dataset,

325 without retraining or fine-tuning, resulted in a substantial decrease in performance. The

326 model achieved a weed F1-score of 0.0534 and an IoU of 0.0274 (Table 2), compared

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

327 with 0.6455 and 0.4766, respectively, obtained during spatial validation on Barley 2.

328 These results indicate that the model did not generalise effectively across crops, likely

329 because of differences in canopy architecture, spectral characteristics, and phenological

330 stage between barley and rapeseed.

331 The final U-Net model was subsequently applied to the complete Barley 2-V2

332 orthomosaic to generate weed probability and relative weed density maps (Fig. 7). The

333 weed probability map (Fig. 7A) represents the predicted probability of weed presence at

334 the pixel level, whereas the density map (Fig. 7B) was obtained by spatially aggregating

335 predictions into 2 × 2 m grid cells and classifying them into four relative infestation

336 levels (very low, low, medium, and high). Areas with medium and high weed density

337 formed spatially coherent clusters, highlighting the suitability of the proposed workflow

338 for supporting site-specific weed management.

339 Table 2. Comparison of U-Net performance in spatial validation and cross-crop

340 transfer.

Evaluation Target field Weed F1-score Weed IoU Spatial validation Barley 2 0.6455 0.4766 Cross-crop transfer Rapeseed 0.0534 0.0274

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

341

342

343 Fig. 7: Weed mapping products generated from the full Barley 2-V2 orthomosaic using

344 the selected U-Net model. (A) Pixel-wise weed probability map. (B) Relative weed

345 density map obtained by aggregating predictions into 2 × 2 m grid cells and classifying

346 them into four infestation levels (very low, low, medium, and high).

347 The poor performance obtained in the direct cross-crop transfer motivated the

348 evaluation of a few-shot fine-tuning strategy, presented in the following section.

349 3.6. Few-shot fine-tuning for domain adaptation to rapeseed

350 The fine-tuning experiments demonstrated that the recovery of weed detection

351 performance in rapeseed depended on both the amount of labelled target data and the

352 adaptation strategy employed (Fig. 8). Direct application of the barley-trained model

353 without adaptation (E0) confirmed the severe performance degradation observed in the

354 previous section, yielding a weed F1-score of 0.0534 and an IoU of 0.0274. Partial fine-

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

355 tuning progressively improved performance as more labelled rapeseed patches were

356 used for adaptation, reaching weed F1-scores of 0.1434, 0.1767, and 0.3707 using

357 approximately 5%, 10%, and 15% of the available labelled data, respectively.

358 Full fine-tuning consistently outperformed partial fine-tuning across all evaluated

359 scenarios. Using approximately 5% of the labelled dataset (21 patches), the model

360 achieved a weed F1-score of 0.3788 and an IoU of 0.2337, already exceeding the

361 performance obtained with partial fine-tuning using 15% of the data. Increasing the

362 adaptation set to 42 patches (≈10%) further improved performance to an F1-score of

363 0.4571 and an IoU of 0.2963. The best results were obtained with 63 labelled patches

364 (≈15%), reaching a weed F1-score of 0.6274, an IoU of 0.4571, and an mIoU of 0.7607.

365 Notably, the performance achieved after full fine-tuning with only 63 labelled patches

366 approached that obtained during spatial validation in barley (weed F1 = 0.6455, IoU =

367 0.4766), with absolute differences of only 0.018 in F1-score and 0.020 in IoU. These

368 results indicate that a limited amount of annotated target-domain data is sufficient to

369 effectively adapt the segmentation model to a new crop.

370

371 Fig. 8: Results of few-shot fine-tuning of the barley-trained U-Net model using labelled

372 rapeseed patches. (A) Weed F1-score as a function of the proportion of labelled

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

373 rapeseed data used for adaptation (0 %, 5 %, 10 % and 15 %, corresponding to 0, 21,

374 42 and 63 patches). (B) Evolution of the weed F1-score during training for the 15 %

375 fine-tuning experiment. The vertical dotted grey line marks the early-stopping point

376 (epoch 21) of the frozen encoder. In both panels: ■ – partial fine-tuning (frozen

377 encoder); ● – full fine-tuning (all parameters); – – –  – direct cross-crop transfer

378 without adaptation.

379 4. Discussion

380 4.1. Contribution of multispectral bands and vegetation indices to weed segmentation

381 The progressive improvement in weed detection performance observed across the

382 evaluated spectral configurations, from the RGB-only input (weed F1 = 0.5193) to the

383 full multispectral configuration (weed F1 = 0.5833), demonstrates that incorporating

384 NIR and RedEdge bands together with vegetation indices provided complementary

385 information for semantic segmentation. This finding is consistent with the ability of

386 multispectral imagery to capture physiological and structural characteristics of

387 vegetation that are not represented in the visible spectrum. In particular, NIR reflectance

388 is related to leaf internal structure and canopy density, whereas the RedEdge region is

389 sensitive to variations in chlorophyll content and plant physiological status (Kior et al.,

390 2024; Zhang et al., 2021).

391 Adding the NIR and RedEdge bands to the RGB configuration produced only a

392 marginal improvement over the RGB baseline (ΔF1 = 0.0045; ΔIoU = 0.0040),

393 suggesting that the raw reflectance values of these additional bands alone were

394 insufficient to substantially improve crop–weed discrimination under the evaluated

395 conditions. In contrast, combining RGB imagery with the selected vegetation indices

396 resulted in a more noticeable performance gain (ΔF1 = 0.0268; ΔIoU = 0.0248),

397 indicating that the normalised spectral information contained in the indices was more

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

398 discriminative than the direct incorporation of additional spectral bands. The best

399 performance was achieved using the full spectral configuration, which combined

400 multispectral bands and vegetation indices (ΔF1 = 0.0640; ΔIoU = 0.0609 relative to

401 RGB). This result suggests that raw spectral information and derived vegetation indices

402 provide complementary information for semantic segmentation. Similar improvements

403 have been reported in previous studies, where the integration of vegetation indices with

404 multispectral UAV imagery enhanced crop–weed discrimination compared with models

405 based solely on RGB imagery or raw multispectral bands (Jurišić et al., 2022; Sa et al.,

406 2018).

407 The selection of NDVI, NDRE, and VARI was based on a Pearson correlation analysis,

408 which revealed a high degree of redundancy among several of the evaluated indices,

409 particularly NDVI, SAVI, and GNDVI. Instead of incorporating all available indices, a

410 reduced set of complementary variables was selected to limit input dimensionality and

411 reduce the risk of overfitting when training with a relatively small labelled dataset

412 (Dong et al., 2025; Feng et al., 2023). The selected indices provide complementary

413 information: NDVI describes general vegetation vigour through the relationship

414 between red and NIR reflectance, NDRE incorporates RedEdge information associated

415 with relative chlorophyll content, and VARI provides vegetation information derived

416 exclusively from visible wavelengths (Dimyati et al., 2023; Picon et al., 2022). This

417 combination provided a compact and interpretable input representation while preserving

418 the spectral information required to discriminate crop, weeds, and soil.

419 4.2. Behaviour of deep learning models for weed segmentation

420 U-Net consistently outperformed both DeepLabv3 and Random Forest under the same

421 spectral input configuration, achieving a weed F1-score of 0.5833 and an mIoU of

422 0.5448, compared with 0.2723 and 0.2736 for DeepLabv3, and 0.0794 and 0.2248 for

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

423 Random Forest, respectively. The superior performance of U-Net can be attributed to its

424 encoder-decoder architecture with skip connections, which combines high-level

425 contextual information with fine spatial details. This characteristic is particularly

426 advantageous for UAV-based weed segmentation, where weeds often appear as small,

427 irregular, and partially occluded objects that require accurate boundary delineation (Ma

428 et al., 2023; Ronneberger et al., 2015).

429 The comparison between U-Net, DeepLabv3, and Random Forest was intended to

430 represent three commonly used approaches for agricultural image analysis: an encoder-

431 decoder architecture designed to preserve spatial detail, a network based on multi-scale

432 contextual feature extraction through atrous convolutions, and a conventional pixel-wise

433 classifier relying exclusively on spectral information. This experimental design allowed

434 the contribution of spatial context learning to be assessed relative to a traditional

435 classifier that does not explicitly model spatial relationships between neighbouring

436 pixels.

437 The superior performance of U-Net agrees with previous studies on UAV-based weed

438 segmentation. For example, Shahi et al. (2023) reported that U-Net outperformed

439 several deep learning architectures for multiclass weed detection, whereas DeepLabv3

440 showed lower performance when trained on relatively small datasets. A similar trend

441 was observed in the present study, where U-Net achieved more than twice the weed F1-

442 score obtained by DeepLabv3 using the same training data and spectral configuration.

443 Likewise, Zou et al. (2021) successfully applied a U-Net-based architecture for weed

444 segmentation in wheat UAV imagery, although their evaluation was limited to a single

445 field and did not include independent spatial validation.

446 The lower performance of DeepLabv3 should not be interpreted as an inherent

447 limitation of the architecture. DeepLabv3 relies on Atrous Spatial Pyramid Pooling

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

448 (ASPP) to capture multi-scale contextual information, a strategy that has proven

449 effective in large-scale semantic segmentation tasks. However, the relatively small

450 training dataset, class imbalance, and the absence of ImageNet pre-training may have

451 limited its ability to learn robust feature representations in the present study. Under

452 these conditions, the simpler U-Net architecture appeared better suited to the available

453 data. Previous studies have shown that DeepLabv3 generally benefits from larger

454 annotated datasets and transfer learning, suggesting that its performance could be

455 substantially improved under different training conditions (Shahi et al., 2023).

456 Random Forest showed the lowest performance among the evaluated models,

457 confirming the limitations of conventional pixel-wise classifiers for semantic

458 segmentation of UAV imagery. Because each pixel is classified independently, without

459 considering neighbouring information, Random Forest cannot effectively capture spatial

460 continuity, object boundaries, or contextual relationships between weeds, crops, and

461 soil. These limitations explain its fragmented predictions and poor weed detection

462 performance. Similar conclusions have been reported in agricultural remote sensing,

463 where convolutional neural networks consistently outperform traditional machine

464 learning algorithms when accurate spatial representation is required (Adhinata et al.,

465 2024).

466 4.3. Spatial generalisation within barley

467 Spatial validation, based on training with Barley 1-V1 and Barley 1-V2 and evaluating

468 the model on the independent Barley 2-V2 field, produced the best weed detection

469 performance of the study (F1 = 0.6455; IoU = 0.4766), outperforming the initial

470 temporal validation (F1 = 0.5833; IoU = 0.4117). This improvement can be explained,

471 at least in part, by two complementary factors. First, combining data from V1 and V2

472 enriched the training set with phenologically diverse observations, spanning from the

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

473 late tillering stage in March to the heading stage in May, thereby increasing the spectral

474 and structural variability available for model learning. Second, evaluation on an

475 independent field reduced the influence of spatial autocorrelation between training and

476 testing data, which is known to artificially inflate performance when models are

477 evaluated on spatially adjacent samples.

478 Crop phenology plays a major role in weed detectability in UAV imagery. In narrow-

479 row cereal crops such as barley, discrimination between crop plants and weeds is easier

480 during the early developmental stages, when the canopy remains relatively open and the

481 inter-row spaces allow weeds to be distinguished through both spectral and spatial

482 contrast (de Castro et al., 2018; Torres-Sánchez et al., 2014). As crop development

483 progresses and the canopy closes, weeds become increasingly occluded beneath the crop

484 foliage, reducing their visibility from overhead imagery and increasing spectral

485 confusion between classes (Anderegg et al., 2023). In the present study, the V1 flight (3

486 March, BBCH 25–29) captured weeds under favourable conditions, with an open

487 canopy and a large proportion of exposed soil between rows. By contrast, the V2 flight

488 (14 May, BBCH 51–55) was acquired during the heading stage, when canopy closure

489 considerably increased the occlusion of weeds. Combining both acquisition dates during

490 training likely enabled the model to learn complementary spectral and structural

491 representations of weeds under contrasting crop development conditions, providing a

492 plausible explanation for the improvement observed over temporal validation, where the

493 model was trained exclusively on V1 imagery.

494 The best performance was achieved relatively early during training, at epoch 9, after

495 which the weed F1-score fluctuated without further sustained improvement. This

496 behaviour is consistent with that typically observed when training deep learning models

497 on relatively small and class-imbalanced datasets. It suggests that the model rapidly

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

498 converged to a suitable representation of the weed class, whereas the limited size and

499 diversity of the training data constrained further performance gains.

500 The weed IoU obtained during spatial validation (0.4766) is lower than the values

501 reported in recent studies based on substantially larger datasets. Wang et al. (2026)

502 introduced BAWSeg, a multispectral UAV benchmark for weed segmentation in barley

503 built from repeated acquisition campaigns conducted over four years in two commercial

504 fields, reporting a weed IoU of 63.5% using the VISA architecture under a within-plot

505 evaluation protocol. However, under the more challenging cross-plot protocol—where

506 the model is trained on one field and evaluated on another, closely matching the spatial

507 validation strategy adopted in this study—the weed IoU decreases to approximately

508 57.6–58.4%. This considerably reduces the gap with the performance obtained here.

509 The remaining difference can largely be attributed to the greater spatial and temporal

510 diversity of the BAWSeg dataset, together with the use of a dual-stream architecture

511 specifically designed to integrate calibrated reflectance data and vegetation indices.

512 Nevertheless, the results obtained in this study demonstrate that a U-Net model trained

513 with multi-temporal data from a single barley field can achieve moderate spatial

514 generalization to an independent barley field, supporting its potential use for site-

515 specific weed management under real agricultural conditions.

516 These findings are consistent with previous studies highlighting the influence of crop

517 phenology on UAV-based weed detection. Anderegg et al. (2023) reported that weed

518 classification accuracy decreased progressively as crop development advanced and

519 canopy closure increased, despite achieving an overall classification accuracy of 72%.

520 Likewise, (de Castro et al., 2018) showed that UAV-based weed detection is more

521 reliable during the early stages of crop development, when the open canopy provides

522 greater spatial separation between crop plants and weeds. Although their study

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

523 employed an object-based image analysis approach combined with Random Forest

524 rather than deep learning, their agronomic conclusions agree with the results obtained

525 here and reinforce the importance of incorporating imagery acquired at multiple

526 phenological stages when training semantic segmentation models intended for

527 operational applications.

528 4.4. Cross-crop transfer

529 The direct transfer of the model trained on barley to the rapeseed field resulted in a

530 marked decline in performance, with a weed F1-score of 0.0534 and an IoU of 0.0274.

531 This result contrasts sharply with that obtained during spatial validation within barley

532 and highlights the limited ability of the model to generalise directly across crops. The

533 performance loss can be interpreted as a consequence of domain shift between the

534 source crop (barley) and the target crop (rapeseed), a common limitation of deep

535 learning models applied to agricultural imagery when the target domain is not

536 represented in the training data (Zhao and Wang, 2026). This loss of transferability can

537 be explained by concurrent differences in canopy architecture, phenological stage and

538 spectral response between the two crops. Whereas barley exhibits a row-structured

539 canopy, flowering rapeseed develops a much denser canopy with extensive floral cover,

540 substantially altering the spectral signature recorded by the sensor. Consequently, the

541 representations learned during training on barley were insufficient to accurately

542 distinguish crop, soil and weeds in a domain with substantially different visual

543 characteristics.

544 4.5. Domain adaptation through few-shot fine-tuning

545 The learning curve obtained with full fine-tuning revealed a non-linear trend: the

546 marginal improvement per additional labelled patch was greater between 42 and 63

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

547 patches (ΔF1 = 0.17) than between 21 and 42 patches (ΔF1 = 0.08). This behaviour

548 suggests the existence of an adaptation threshold beyond which the model is exposed to

549 sufficient spectral variability from the target domain to effectively refine the

550 representations learned during training on barley. Below this threshold, full fine-tuning

551 produced more modest improvements, comparable to those achieved by partial fine-

552 tuning with a larger number of samples, indicating that successful encoder adaptation

553 requires a minimum number of representative examples from the target domain.

554 The consistent performance gap between partial and full fine-tuning across all evaluated

555 training set sizes demonstrates that updating the entire network is essential when the

556 structural and phenological differences between source and target domains are as

557 pronounced as those observed between barley at heading and flowering rapeseed.

558 Notably, full fine-tuning using only 63 labelled patches achieved performance that was

559 nearly equivalent to that obtained during spatial validation within the original barley

560 domain (F1 = 0.6274 versus 0.6455). This finding suggests that the main limitation to

561 cross-crop transfer is not the segmentation architecture itself, but rather the lack of

562 representative samples from the target crop during the initial training stage.

563 From an application perspective, these results indicate that a model pre-trained on one

564 crop can be efficiently adapted to a new crop using a relatively small annotation effort,

565 avoiding the need to build a fully labelled training dataset for each species. Although

566 these findings should be validated under a wider range of crops and environmental

567 conditions, they demonstrate the potential of few-shot fine-tuning as a practical strategy

568 for extending the applicability of UAV-based weed segmentation models. This

569 interpretation is consistent with recent studies on few-shot domain adaptation for

570 semantic segmentation, which have likewise shown that a limited number of labelled

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

571 samples can be sufficient to successfully adapt pre-trained models to new domains (Xu

572 et al., 2025).

573 4.6. Agronomic relevance of weed probability and density maps

574 The weed probability and density maps generated through spatial inference over the

575 Barley 2 field translated the output of the segmentation model into products that are

576 directly interpretable from an agronomic perspective. The spatial clustering of areas

577 with medium and high weed density, rather than a homogeneous distribution across the

578 entire field, is consistent with the characteristic spatial heterogeneity of weed

579 infestations reported in the literature for arable crops (Gerhards et al., 2022). This

580 pattern reinforces the hypothesis that uniform herbicide application may result in

581 unnecessary treatments over large portions of a field.

582 The use of two complementary map products addresses different management needs.

583 The continuous probability map preserves the spatial uncertainty of the model

584 predictions and facilitates the identification of transition zones that may require field

585 verification. In contrast, the categorical weed density map, obtained by spatial

586 aggregation into 2 × 2 m cells and reclassification into four relative infestation levels,

587 provides a simpler representation that is directly compatible with site-specific

588 management and variable-rate herbicide application strategies (Gerhards et al., 2022;

589 Sapkota et al., 2023).

590 The practical value of these products should also be considered in the context of the

591 potential benefits of site-specific weed management. In a review of 58 experiments

592 conducted in cereals, maize, sugar beet and peas, Gerhards et al. (2022) reported

593 herbicide savings ranging from 23% to 89% through infestation-based management

594 strategies without additional yield losses. Although the present study did not directly

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

595 evaluate these economic benefits, the generated maps constitute an intermediate product

596 compatible with current precision agriculture systems and could be readily integrated

597 into variable-rate application workflows using standard geospatial formats such as

598 GeoTIFF or Shapefile.

599 The few-shot fine-tuning experiments further demonstrate the practical applicability of

600 the proposed framework. While direct cross-crop transfer produced insufficient

601 performance to generate reliable maps in rapeseed, fine-tuning the model using only a

602 small labelled dataset restored performance to a level that was nearly equivalent to that

603 achieved in barley. This finding suggests that operational weed mapping could be

604 extended to new crops without the need to develop entirely new models for each

605 agricultural scenario, substantially reducing the annotation effort required for

606 deployment. Nevertheless, the generated maps represent model-derived estimates rather

607 than direct measurements of actual weed infestation. Consequently, their use as

608 decision-support tools requires further validation through field observations to quantify

609 the agreement between model predictions and the actual spatial distribution of weeds

610 before being incorporated into operational site-specific weed management programmes.

611 4.7. Limitations and future work

612 Although training with images acquired at two phenological stages improved the

613 model's spatial generalisation and the few-shot fine-tuning experiments demonstrated

614 effective adaptation to rapeseed, the dataset remains limited to a single growing season

615 and a relatively small number of fields. This limitation restricts the spatial,

616 phenological, and environmental variability available during training. Expanding the

617 dataset to include additional growing seasons, fields, and cropping conditions would

618 likely improve the robustness and generalisation capability of the model.

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

619 Reference masks were generated through manual digitisation, which may introduce

620 uncertainty in transition zones between crop, weed, and soil classes, particularly where

621 class boundaries are not clearly defined. This limitation, which is common in semantic

622 segmentation studies based on agricultural imagery, directly affects the quality of the

623 supervision signal and, consequently, the final model performance. In this context,

624 semi-automatic annotation workflows, active learning, and AI-assisted annotation tools

625 could reduce the annotation effort and facilitate dataset expansion. In addition, field

626 validation of the weed density maps remains necessary to assess the correspondence

627 between model predictions and the actual weed distribution.

628 Furthermore, although the spatial resolution of the orthomosaic (≈ 5.5 cm pixel⁻¹) was

629 sufficient to detect weed patches and delineate their spatial distribution, it was not

630 sufficient to reliably discriminate individual weed species when they co-occurred within

631 the same patch or were partially occluded by the crop canopy. Consequently, the

632 objective of the model was limited to detecting the weed class as a whole rather than

633 performing taxonomic species classification. This limitation could be addressed in

634 future work through lower-altitude UAV flights or sensors providing higher spatial

635 resolution.

636 The comparison between models was performed under a common experimental

637 configuration, without architecture-specific hyperparameter optimisation. This approach

638 enabled a fair comparison between models but may have limited the maximum

639 achievable performance of some architectures. In particular, DeepLabv3 could benefit

640 from dedicated optimisation of its training parameters, exploration of alternative ASPP

641 configurations, or the use of pre-trained weights from datasets more closely related to

642 agricultural imagery. Future studies should therefore consider independent

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

643 hyperparameter optimisation for each architecture to provide a more comprehensive

644 assessment of their potential.

645 Finally, although the few-shot fine-tuning experiments demonstrated that model

646 adaptation to a new crop is feasible using only a limited number of labelled samples,

647 this approach was evaluated on only one target crop (rapeseed) and a single acquisition

648 season. In addition, model selection in these experiments was based on the weed F1-

649 score computed on the evaluation set itself, given the limited number of rapeseed

650 patches available; the reported metrics should therefore be interpreted as an upper-

651 bound estimate of adaptation performance. Future work should determine whether the

652 observed adaptation threshold remains consistent across different crops, phenological

653 stages, and environmental conditions, and should investigate the potential of foundation

654 models, such as DINOv2 (Oquab et al., 2024), combined with self-supervised learning

655 strategies, to further improve cross-crop generalisation while reducing dependence on

656 large annotated datasets.

657 5. Conclusions

658 This study evaluated the use of multispectral UAV imagery and semantic segmentation

659 models for weed detection and mapping in barley, with particular emphasis on spatial

660 generalisation to an independent field and cross-crop transfer to rapeseed through few-

661 shot fine-tuning. The results showed that the full spectral configuration (RGB, NIR,

662 RedEdge, NDVI, NDRE, and VARI) provided the best performance, and that U-Net

663 consistently outperformed both DeepLabv3 and Random Forest. In addition, training

664 with data acquired at two phenological stages improved within-crop spatial

665 generalisation, achieving a weed F1-score of 0.6455 and an IoU of 0.4766 on an

666 independent barley field.

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

667 Direct transfer of the barley-trained model to rapeseed resulted in a substantial

668 performance decline (F1 = 0.0534), confirming that cross-crop generalisation between

669 crops with different canopy structures and spectral responses requires explicit domain

670 adaptation. The main methodological contribution of this study was demonstrating that

671 this limitation can be effectively overcome through few-shot fine-tuning. Using only 63

672 labelled rapeseed patches (approximately 15% of the available dataset), full fine-tuning

673 achieved a weed F1-score of 0.6274, approaching the performance obtained in the

674 original barley domain (F1 = 0.6455). These findings indicate that adapting the encoder

675 is critical under severe domain shift and that only a limited amount of labelled target-

676 domain data may be sufficient to successfully transfer a semantic segmentation model

677 to a new crop.

678 Finally, the weed probability and density maps demonstrate the practical value of the

679 proposed methodology for supporting site-specific weed management and variable-rate

680 herbicide application. Although further validation across additional fields, growing

681 seasons, and crop species is still required, the results demonstrate that combining

682 multispectral UAV imagery, semantic segmentation, and few-shot fine-tuning provides

683 a promising and scalable framework for developing transferable weed detection systems

684 while substantially reducing annotation requirements.

685 Declaration of Competing Interest

686 The authors declare that they have no known competing financial interests or personal

687 relationships that could have appeared to influence the work reported in this paper.

688 Credit authorship contribution statement

689 Patricio Alonso Hernández Ludeña: Conceptualization, Methodology, Software,

690 Validation, Formal analysis, Investigation, Data Curation, Writing – Original Draft,

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

691 Visualization. Carlos Fernández Piñar: Conceptualization, Methodology, Supervision,

692 Writing – Review & Editing. Juan López de Herrera: Supervision, Writing – Review &

693 Editing. Tomás Ramón Herrero Tejedor: Supervision, Writing – Review &

694 Editing. Enrique Pérez Martin: Supervision, Writing – Review & Editing. Javier

695 Raimundo: Supervision, Methodology, Writing – Review & Editing. Jonathan

696 Calderon: Software, Validation, Writing – Review & Editing.

697 Declaration of Generative AI and AI-assisted technologies in the writing process

698 During the preparation of this work, the authors used ChatGPT (OpenAI) and Claude

699 (Anthropic) for language editing, grammar and style correction, and to improve the

700 clarity and scientific English of the manuscript. After using these tools, the authors

701 reviewed and edited the content as needed and takes full responsibility for the final

702 content of the publication.

703 Data Availability Statement

704 The multispectral UAV imagery and processed patch datasets generated during this

705 study have been deposited in the Mendeley Data repository (DOI:

706 https://doi.org/10.17632/mb4jvxk9dk.1) and are currently undergoing the repository's

707 standard moderation process; the dataset will be made publicly accessible upon

708 approval. The code used for model training, evaluation, and fine-tuning is available in a

709 public GitHub repository at (https://github.com/patitostyle/weed-detection-barley-

710 rapeseed). All data and code are shared under open licenses to ensure reproducibility

711 and transparency.

712 References

713 Adhinata, F.D., Wahyono, Sumiharto, R., 2024. A comprehensive survey on weed and  714 crop classification using machine learning and deep learning. Artificial Intelligence  715 in Agriculture. https://doi.org/10.1016/j.aiia.2024.06.005

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

716 Ampatzidis, Y., Partel, V., 2019. UAV-based high throughput phenotyping in citrus  717 utilizing multispectral imaging and artificial intelligence. Remote Sens. (Basel).  718 11. https://doi.org/10.3390/rs11040410

719 Anderegg, J., Tschurr, F., Kirchgessner, N., Treier, S., Schmucki, M., Streit, B., Walter,  720 A., 2023. On-farm evaluation of UAV-based aerial imagery for season-long weed  721 monitoring under contrasting management and pedoclimatic conditions in wheat.  722 Comput. Electron. Agric. 204. https://doi.org/10.1016/j.compag.2022.107558

723 Chen, L.-C., Papandreou, G., Schroff, F., Adam, H., 2017. Rethinking Atrous  724 Convolution for Semantic Image Segmentation.

725 de Castro, A.I., Torres-Sánchez, J., Peña, J.M., Jiménez-Brenes, F.M., Csillik, O.,  726 López-Granados, F., 2018. An automatic random forest-OBIA algorithm for early  727 weed mapping between and within crop rows using UAV imagery. Remote Sens.  728 (Basel). 10. https://doi.org/10.3390/rs10020285

729 Dimyati, M., Supriatna, S., Nagasawa, R., Pamungkas, F.D., Pramayuda, R., 2023. A  730 Comparison of Several UAV-Based Multispectral Imageries in Monitoring Rice  731 Paddy (A Case Study in Paddy Fields in Tottori Prefecture, Japan). ISPRS Int. J.  732 Geoinf. 12. https://doi.org/10.3390/ijgi12020036

733 Dong, J., Zhang, J., Zhang, S., Yu, Z., Song, Z., Meng, T., 2025. Vegetation extraction  734 through UAV RGB imagery and efficient feature selection. PLoS One 20.  735 https://doi.org/10.1371/journal.pone.0322180

736 Feng, C., Zhang, W., Deng, H., Dong, L., Zhang, H., Tang, L., Zheng, Y., Zhao, Z.,  737 2023. A Combination of OBIA and Random Forest Based on Visible UAV Remote  738 Sensing for Accurately Extracted Information about Weeds in Areas with Different  739 Weed Densities in Farmland. Remote Sens. (Basel). 15.  740 https://doi.org/10.3390/rs15194696

741 Gerhards, R., Andújar Sanchez, D., Hamouz, P., Peteinatos, G.G., Christensen, S.,  742 Fernandez-Quintanilla, C., 2022. Advances in site-specific weed management in  743 agriculture—A review. Weed Res. https://doi.org/10.1111/wre.12526

744 Horvath, D.P., Clay, S.A., Swanton, C.J., Anderson, J. V., Chao, W.S., 2023. Weed- 745 induced crop yield loss: a new paradigm and new challenges. Trends Plant Sci.  746 https://doi.org/10.1016/j.tplants.2022.12.014

747 Jurišić, M., Radočaj, D., Plaščak, I., Galić, S.D., Petrović, D., 2022. THE  748 EVALUATION OF THE RGB AND MULTISPECTRAL CAMERA ON THE  749 UNMANNED AERIAL VEHICLE (UAV) FOR THE MACHINE LEARNING  750 CLASSIFICATION OF MAIZE. Poljoprivreda 28, 74–80.  751 https://doi.org/10.18047/poljo.28.2.10

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

752 Kior, A., Yudina, L., Zolin, Y., Sukhov, V., Sukhova, E., 2024. RGB Imaging as a Tool  753 for Remote Sensing of Characteristics of Terrestrial Plants: A Review. Plants.  754 https://doi.org/10.3390/plants13091262

755 López-Granados, F., 2011. Weed detection for site-specific weed management:  756 Mapping and real-time approaches. Weed Res. 51, 1–11.  757 https://doi.org/10.1111/j.1365-3180.2010.00829.x

758 Lu, B., He, Y., 2017. Species classification using Unmanned Aerial Vehicle (UAV)- 759 acquired high spatial resolution imagery in a heterogeneous grassland. ISPRS  760 Journal of Photogrammetry and Remote Sensing 128, 73–85.  761 https://doi.org/10.1016/j.isprsjprs.2017.03.011

762 Ma, Z., Wang, G., Yao, J., Huang, D., Tan, H., Jia, H., Zou, Z., 2023. An Improved U- 763 Net Model Based on Multi-Scale Input and Attention Mechanism: Application for  764 Recognition of Chinese Cabbage and Weed. Sustainability (Switzerland) 15.  765 https://doi.org/10.3390/su15075764

766 Meyer, H., Reudenbach, C., Hengl, T., Katurji, M., Nauss, T., 2018. Improving  767 performance of spatio-temporal machine learning models using forward feature  768 selection and target-oriented validation. Environmental Modelling and Software  769 101, 1–9. https://doi.org/10.1016/j.envsoft.2017.12.001

770 Müllerová, J., Gago, X., Bučas, M., Company, J., Estrany, J., Fortesa, J., Manfreda, S.,  771 Michez, A., Mokroš, M., Paulus, G., Tiškus, E., Tsiafouli, M.A., Kent, R., 2021.  772 Characterizing vegetation complexity with unmanned aerial systems (UAS) – A  773 framework and synthesis. Ecol. Indic.  774 https://doi.org/10.1016/j.ecolind.2021.108156

775 Murad, N.Y., Mahmood, T., Forkan, A.R.M., Morshed, A., Jayaraman, P.P., Siddiqui,  776 M.S., 2023. Weed Detection Using Deep Learning: A Systematic Literature  777 Review. Sensors. https://doi.org/10.3390/s23073670

778 Nkoa, R., Owen, M.D.K., Swanton, C.J., 2015. Weed Abundance, Distribution,  779 Diversity, and Community Analyses. Weed Sci. 63, 64–90.  780 https://doi.org/10.1614/ws-d-13-00075.1

781 Oerke, E.C., 2006. Crop losses to pests. Journal of Agricultural Science.  782 https://doi.org/10.1017/S0021859605005708

783 Picon, A., Bereciartua-Perez, A., Eguskiza, I., Romero-Rodriguez, J., Jimenez-Ruiz,  784 C.J., Eggers, T., Klukas, C., Navarra-Mestre, R., 2022. Deep convolutional neural  785 network for damaged vegetation segmentation from RGB images based on virtual  786 NIR-channel estimation. Artificial Intelligence in Agriculture 6, 199–210.  787 https://doi.org/10.1016/j.aiia.2022.09.004

788 Rasmussen, J., Azim, S., Nielsen, J., 2021. Pre-harvest weed mapping of Cirsium  789 arvense L. based on free satellite imagery – The importance of weed aggregation

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

790 and image resolution. European Journal of Agronomy 130.  791 https://doi.org/10.1016/j.eja.2021.126373

792 Rew, L.J., Cousens, R.D., 2001. Spatial distribution of weeds in arable crops: are  793 current sampling and analytical methods appropriate? Weed Res. 41, 1–18.

794 Roberts, D.R., Bahn, V., Ciuti, S., Boyce, M.S., Elith, J., Guillera-Arroita, G.,  795 Hauenstein, S., Lahoz-Monfort, J.J., Schröder, B., Thuiller, W., Warton, D.I.,  796 Wintle, B.A., Hartig, F., Dormann, C.F., 2017. Cross-validation strategies for data  797 with temporal, spatial, hierarchical, or phylogenetic structure. Ecography.  798 https://doi.org/10.1111/ecog.02881

799 Ronneberger, O., Fischer, P., Brox, T., 2015. U-Net: Convolutional Networks for  800 Biomedical Image Segmentation.

801 Roslim, M.H.M., Juraimi, A.S., Che’ya, N.N., Sulaiman, N., Manaf, M.N.H.A., Ramli,  802 Z., Motmainna, M., 2021. Using remote sensing and an unmanned aerial system  803 for weed management in agricultural crops: A review. Agronomy.  804 https://doi.org/10.3390/agronomy11091809

805 Sa, I., Popović, M., Khanna, R., Chen, Z., Lottes, P., Liebisch, F., Nieto, J., Stachniss,  806 C., Walter, A., Siegwart, R., 2018. WeedMap: A large-scale semantic weed  807 mapping framework using aerial multispectral imaging and deep neural network  808 for precision farming. Remote Sens. (Basel). 10.  809 https://doi.org/10.3390/rs10091423

810 San Martín, C., Andújar, D., Barroso, J., Fernández-Quintanilla, C., Dorado, J., 2016.  811 Weed Decision Threshold as a Key Factor for Herbicide Reductions in Site- 812 Specific Weed Management. Weed Technology 30, 888–897.  813 https://doi.org/10.1614/wt-d-16-00039.1

814 Sapkota, R., Stenger, J., Ostlie, M., Flores, P., 2023. Towards reducing chemical usage  815 for weed control in agriculture using UAS imagery analysis and computer vision  816 techniques. Sci. Rep. 13. https://doi.org/10.1038/s41598-023-33042-0

817 Shahi, T.B., Dahal, S., Sitaula, C., Neupane, A., Guo, W., 2023. Deep Learning-Based  818 Weed Detection Using UAV Images: A Comparative Study. Drones 7.  819 https://doi.org/10.3390/drones7100624

820 Shuai, G., Martinez-Feria, R.A., Zhang, J., Li, S., Price, R., Basso, B., 2019. Capturing  821 maize stand heterogeneity across yield-stability zones using unmanned aerial  822 vehicles (UAV). Sensors (Switzerland) 19. https://doi.org/10.3390/s19204446

823 Soltani, N., Dille, J.A., Burke, I.C., Everman, W.J., VanGessel, M.J., Davis, V.M.,  824 Sikkema, P.H., 2016. Potential Corn Yield Losses from Weeds in North America.  825 Weed Technology 30, 979–984. https://doi.org/10.1614/wt-d-16-00046.1

826 Torres-Sánchez, J., Peña, J.M., de Castro, A.I., López-Granados, F., 2014. Multi- 827 temporal mapping of the vegetation fraction in early-season wheat fields using

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

828 images from UAV. Comput. Electron. Agric. 103, 104–113.  829 https://doi.org/10.1016/j.compag.2014.02.009

830 Vasileiou, M., Kyrgiakos, L.S., Kleisiari, C., Kleftodimos, G., Vlontzos, G.,  831 Belhouchette, H., Pardalos, P.M., 2024. Transforming weed management in  832 sustainable agriculture with artificial intelligence: A systematic literature review  833 towards weed identification and deep learning. Crop Protection 176.  834 https://doi.org/10.1016/j.cropro.2023.106522

835 Wang, H., Wang, X., Ibrahim, M., Severtson, D., Mian, A., 2026. BAWSeg: A UAV  836 Multispectral Benchmark for Barley Weed Segmentation. Remote Sens. (Basel).  837 18. https://doi.org/10.3390/rs18060915

838 Wu, Z., Chen, Y., Zhao, B., Kang, X., Ding, Y., 2021. Review of weed detection  839 methods based on computer vision. Sensors. https://doi.org/10.3390/s21113647

840 Xu, B., Werle, R., Chudzik, G., Zhang, Z., 2025. Enhancing weed detection using UAV  841 imagery and deep learning with weather-driven domain adaptation. Comput.  842 Electron. Agric. 237. https://doi.org/10.1016/j.compag.2025.110673

843 Xue, J., Su, B., 2017. Significant remote sensing vegetation indices: A review of  844 developments and applications. J. Sens. https://doi.org/10.1155/2017/1353691

845 Zhang, T., Xu, Z., Su, J., Yang, Z., Liu, C., Chen, W.H., Li, J., 2021. Ir-unet: Irregular  846 segmentation u-shape network for wheat yellow rust detection by uav multispectral  847 imagery. Remote Sens. (Basel). 13. https://doi.org/10.3390/rs13193892

848 Zhao, H., Wang, Y., 2026. Deep learning–based approaches for weed detection in crops.  849 Front. Plant Sci. 16. https://doi.org/10.3389/fpls.2025.1746406

850 Zou, K., Chen, X., Zhang, F., Zhou, H., Zhang, C., 2021. A field weed density  851 evaluation method based on uav imaging and modified u-net. Remote Sens.  852 (Basel). 13, 1–19. https://doi.org/10.3390/rs13020310

853

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=7345639

Preprint not peer reviewed

Preprint not peer reviewed

Preprint not peer reviewed

Preprint not peer reviewed

Preprint not peer reviewed

Preprint not peer reviewed

Preprint not peer reviewed

Preprint not peer reviewed
