import json, io

chunk = json.loads(open('_adjudication_chunk_4.json', encoding='utf-8').read())
ids = chunk['disputed_ids']

def load_all(pattern):
    out = {}
    for f in glob.glob(pattern):
        for rec in json.loads(open(f, encoding='utf-8').read()):
            out[rec['workspace_id']] = rec
    return out
import glob
s1 = load_all('batch_*_decisions.json')
s2 = load_all('batch_*_decisions_screener2.json')

# manual adjudication: wid -> (decision, confidence, final_codes, reasoning)
A = {
"SCI-001051":("EXCLUDE",0.75,["EXC-02"],"Edge-AI CNN framework (Jetson Nano/drones/Raspberry Pi) performs real-time paddy weed detection/removal reporting up to 92% detection accuracy; this is a bounding-box/classification weed-detection task with no pixel-level semantic segmentation masks and no mIoU/Dice/F1/PA segmentation metric, so it fails INC-01/INC-02 despite on-device deployment."),
"SCI-001052":("EXCLUDE",0.8,["EXC-02","EXC-03"],"UAS plus reconstructed satellite multispectral imagery is used to assess vineyard state via spectral vegetation indices on a Greco cultivar; no deep-learning segmentation and no crop/weed pixel masks, and the object is vineyard VIs, so out of crop/weed segmentation scope."),
"SCI-001054":("EXCLUDE",0.8,["EXC-02"],"UAV multispectral wheat disease detection uses a fine-tuned VGG19 CNN with Grad-CAM for interpretability; the task is image classification of diseases, not pixel-level crop/weed segmentation masks, hence EXC-02."),
"SCI-001055":("EXCLUDE",0.8,["EXC-02"],"Reinforcement-learning hybrid with drone networks and IoT identifies pests and optimizes pesticide application (96.8% accuracy, 98% AUC); pest identification/management is a detection/classification task, not crop/weed pixel segmentation."),
"SCI-001056":("EXCLUDE",0.82,["EXC-02"],"MobileNetV2+EfficientNetB0 fusion classifies pests/diseases on the CCMT dataset (89.5% accuracy, <10ms inference on edge); an image-classification/detection task with no segmentation masks and no mIoU/Dice metric, so fails INC-01 despite edge metrics."),
"SCI-001057":("EXCLUDE",0.82,["EXC-02"],"ResVNet (ResNet152+ViT+LoRA) classifies tomato leaf diseases on PlantVillage at 97.45% mean accuracy; whole-image classification only, no pixel-level crop/weed segmentation, hence EXC-02."),
"SCI-001058":("EXCLUDE",0.82,["EXC-02"],"CNNs (EfficientNetB0 best, 97.5%) classify crop diseases from UAV RGB/multispectral imagery with deployment latency 0.45s; a disease-classification task, not pixel-level segmentation."),
"SCI-001060":("EXCLUDE",0.85,["EXC-05"],"A review of automated weed-classification techniques (CNNs, DenseNet, transfer learning, XAI) surveying benchmark datasets and edge deployment; secondary literature without a primary empirical crop/weed segmentation benchmark."),
"SCI-001061":("EXCLUDE",0.8,["EXC-02"],"YOLO-Res residual-enhanced YOLO detects weeds in maize fields on WeedsGalore with bounding-box detection accuracy; a detection task, not pixel-level semantic segmentation."),
"SCI-001063":("EXCLUDE",0.7,["EXC-02"],"UAV weed-spraying pipeline uses SAM-ViT-H vegetation masks plus an EfficientNet-B2 species classifier with severity scoring; reported metrics are classification precision/recall (95.14%) and spray activations, not a pixel-segmentation mIoU/Dice benchmark, so fails INC-02 for RQ1."),
"SCI-001064":("EXCLUDE",0.8,["EXC-02"],"FusionNet-GLD combines Xception+InceptionV3 to classify grapevine leaf diseases (99.63% accuracy); grapevine disease classification, not crop/weed pixel segmentation."),
"SCI-001067":("EXCLUDE",0.72,["EXC-02"],"CNN-based system classifies weeds vs paddy crops from drone/ground imagery with targeted removal; primary task is weed classification/detection rather than an explicit pixel-segmentation benchmark with mask metrics."),
"SCI-001068":("EXCLUDE",0.85,["EXC-02","EXC-03"],"CNN+Random Forest detects and deters harmful birds in tomato cultivation; an animal-detection task outside crop/weed segmentation domain and not a segmentation benchmark."),
"SCI-001069":("EXCLUDE",0.8,["EXC-02"],"Attention-GCN+SPP framework classifies UAV-captured soybean disease imagery (97.61% validation accuracy); whole-image classification, not pixel-level segmentation."),
"SCI-001070":("EXCLUDE",0.72,["EXC-02","EXC-03"],"Semantic-segmentation networks with NDVI classify crop types (table grapes, corn, quinoa) across phenological phases; this is crop-type/land-cover classification (incl. fruit crops), not crop-vs-weed segmentation with mIoU/Dice."),
"SCI-001072":("EXCLUDE",0.8,["EXC-02"],"VGG16 transfer-learning system classifies plant diseases and pests from RGB images; an image-classification task, no pixel-level segmentation."),
"SCI-001074":("EXCLUDE",0.75,["EXC-02"],"PSO-optimized deep classifier (MDNN) recommends crops and predicts yields from soil data and UAV NDVI/RGB; a crop-recommendation/yield-regression task, not a computer-vision crop/weed segmentation benchmark."),
"SCI-001080":("EXCLUDE",0.8,["EXC-02","EXC-03"],"ML-based UAV flight-path planning for arable lands with a CNN pest-detection module; trajectory-planning and pest-detection study, not crop/weed pixel-level segmentation."),
"SCI-001082":("EXCLUDE",0.82,["EXC-02"],"Transfer-learning CNN estimates citrus leaf chlorophyll content across leaf/canopy/UAV scales (R2 up to 0.784); a biophysical trait-regression task, not crop/weed segmentation."),
"SCI-001083":("EXCLUDE",0.78,["EXC-02"],"AgriVision CNN detects crop diseases in early stages from drone imagery with a dashboard; a disease-detection/decision system, not pixel-level crop/weed segmentation."),
"SCI-001086":("EXCLUDE",0.85,["EXC-03"],"Superpixel-aided multiscale CNN segments UAV imagery on the Urban Drone Dataset (UDD) for urban scenes; not agricultural crop/weed imagery."),
"SCI-001088":("INCLUDE",0.78,["INC-01","INC-02"],"YOLOv26-based instance segmentation localizes Potato Virus Y symptoms in seed-potato fields from UAV RGB imagery, reporting quantitative mask metrics (mAP@50 ~65%, precision 73%, recall 65%); this is DL pixel-level segmentation of a field crop with segmentation accuracy, so in scope for RQ1 (no on-device edge figures reported, so only INC-01/INC-02 apply)."),
"SCI-001089":("EXCLUDE",0.7,["EXC-02"],"Faster R-CNN detects rice plants (bounding boxes) then U-Net segments leaves to extract RGB for health classification via IRRI Leaf Color Chart; segmentation is a preprocessing step toward whole-plant health classification, and no mIoU/Dice/F1/PA segmentation metric is benchmarked."),
"SCI-001092":("EXCLUDE",0.8,["EXC-02"],"Attention-augmented CNN classifies wheat/rice/maize diseases from drone RGB and multispectral images; a disease-classification task, not pixel-level crop/weed segmentation."),
"SCI-001093":("EXCLUDE",0.78,["EXC-02","EXC-03"],"U-Net/CNN segment coconut trees from drone imagery and classifiers diagnose disease; coconut is a plantation/fruit crop and the workflow is segmentation-for-disease-classification rather than a crop/weed segmentation benchmark."),
"SCI-001094":("EXCLUDE",0.8,["EXC-02"],"Hybrid CNN+XGBoost classifies crop health from drone footage (96.4% accuracy); a crop-health classification task, not segmentation."),
"SCI-001098":("EXCLUDE",0.85,["EXC-05"],"Comparative review of modern deep-learning techniques for plant disease detection (architectures, datasets, metrics); secondary literature without a primary segmentation benchmark."),
"SCI-001100":("EXCLUDE",0.8,["EXC-02"],"Optimized CNN with Environmental Adaptation Method classifies sugarcane diseases (89% accuracy); a disease-classification task, not pixel-level crop segmentation."),
"SCI-001102":("EXCLUDE",0.7,["EXC-02"],"SAM segmentation + RF classification maps cropland and crop planting structures from multi-temporal UAV data (OA 92.66%, Kappa 0.9163); a crop-type/land-cover mapping task reporting classification accuracy, not a crop-vs-weed segmentation benchmark with mIoU/Dice."),
"SCI-001103":("EXCLUDE",0.72,["EXC-02"],"Drone system uses CNN for weed detection (92% accuracy, F1 0.92) plus NDVI and LSTM growth monitoring; weed detection/classification rather than pixel-level segmentation with mask metrics."),
"SCI-001104":("EXCLUDE",0.72,["EXC-01"],"Ensemble semantic segmentation detects weed pixels in rice paddies (weed IoU 0.441, mIoU 0.706, PA 0.971) but imagery is from a forward-facing camera on an aquatic drone navigating between rice plants, an in-water/ground-level platform rather than an aerial UAV-borne system, so fails the UAV criterion."),
"SCI-001105":("EXCLUDE",0.72,["EXC-01"],"Semantic segmentation detects weed pixels from a front-facing camera on an aqua-drone (duck's perspective) in rice paddies (weed IoU 0.383, mIoU 0.676, PA 0.970); the imaging platform is an aquatic/gound-level drone, not an aerial UAV."),
"SCI-001106":("EXCLUDE",0.85,["EXC-05"],"Review of UAV, satellite remote sensing, and machine learning in precision agriculture covering yield, nutrients, and disease; a survey without a primary crop/weed segmentation benchmark."),
"SCI-001107":("EXCLUDE",0.8,["EXC-02"],"Faster R-CNN recognizes spraying vs non-spraying areas for UAV-based sprayers (87.77% crops, 88.57% orchards); an area-recognition/detection task for spray decisions, not crop/weed pixel segmentation."),
"SCI-001112":("EXCLUDE",0.8,["EXC-02"],"Agro Drone AI uses DeiT-small with Real-ESRGAN for multi-class crop-disease classification from low-cost drone imagery; a disease-classification task, not pixel-level segmentation."),
"SCI-001115":("EXCLUDE",0.8,["EXC-02"],"CNN classifies rice bacterial blight from drone/satellite remote sensing (98.2% accuracy); a disease-classification task, not pixel-level segmentation."),
"SCI-001117":("EXCLUDE",0.82,["EXC-02","EXC-03"],"CrossCapsViT performs hyperspectral-image classification with RL active learning on land-cover/saltmarsh datasets; a general HSI land-cover classification task, not crop/weed segmentation."),
"SCI-001118":("EXCLUDE",0.82,["EXC-02"],"Single-stream CNN fuses RGB/thermal/hyperspectral for multi-modal plant-disease detection; a classification task, not pixel-level crop/weed segmentation."),
"SCI-001119":("EXCLUDE",0.82,["EXC-02"],"DDF-DETR detection transformer localizes small cotton seedlings from UAV field imagery (mAP@0.5 83.72%); object detection with bounding boxes, not pixel-level segmentation."),
"SCI-001121":("EXCLUDE",0.7,["EXC-02"],"BP-MOPS tiling dataset method segments farmland cultivation zones (MPFCZ) from multi-temporal UAV imagery (mIoU >0.82); the task is field/land-delineation rather than crop-vs-weed segmentation."),
"SCI-001122":("EXCLUDE",0.8,["EXC-02"],"Conv1D CNN estimates soil gravimetric moisture from UAV multispectral bands (R2=0.91); a soil-property regression task, not computer-vision crop/weed segmentation."),
"SCI-001123":("EXCLUDE",0.75,["EXC-03"],"Mamba-UAV-SegNet real-time semantic segmentation is benchmarked on urban/general UAV datasets (UAV-City, VDD, UAVid, mIoU 69-78%) with farmland only mentioned as an application; not a crop/weed agricultural segmentation benchmark."),
"SCI-001124":("EXCLUDE",0.78,["EXC-03","EXC-04"],"Hierarchical fuzzy-rule-based system generates crop/vegetation status maps for artichoke and vineyard using spectral indices; a non-deep-learning fuzzy-control approach in artichoke/vineyard domains, not a DL crop/weed segmentation benchmark."),
"SCI-001125":("EXCLUDE",0.78,["EXC-02"],"Federated-learning CNN with DCGAN augmentation performs land-cover/land-use classification from UAV imagery (97% accuracy); a land-cover classification task, not pixel-level crop/weed segmentation."),
"SCI-001126":("EXCLUDE",0.85,["EXC-02","EXC-03"],"YOLOv5s/Faster R-CNN/Mask R-CNN perform object-based detection of individual oil palm trees (mAP 0.764) for health classification; a plantation-tree bounding-box task, not crop/weed segmentation."),
"SCI-001127":("EXCLUDE",0.7,["EXC-06"],"General overview of AI weed-management approaches (smartphone app, cloud service) discussing crop/weed discrimination; it reports no specific quantitative pixel-level segmentation benchmark metric on UAV imagery, so no recoverable results for RQ1/RQ2."),
"SCI-001129":("EXCLUDE",0.8,["EXC-02"],"ANN/CNN regression estimates wheat above-ground biomass from UAV RGB (MAE/RMSE/R2); a regression task, not pixel-level segmentation and no segmentation metric reported."),
"SCI-001130":("EXCLUDE",0.82,["EXC-02"],"Deep Siamese few-shot network classifies watermelon diseases from UAV imagery (94.5% accuracy); whole-image classification, not pixel-level segmentation."),
"SCI-001131":("EXCLUDE",0.82,["EXC-02"],"YOLOv11 object detector localizes crop-pest infestation for micro-dose spraying (97.2% detection accuracy); a bounding-box detection task, not pixel-level segmentation."),
"SCI-001132":("EXCLUDE",0.8,["EXC-02"],"ARCNN classifies vegetable categories from multi-temporal UAV RGB (overall accuracy 92.80%); crop-type classification rather than pixel-wise segmentation masks."),
"SCI-001134":("EXCLUDE",0.8,["EXC-02"],"Hybrid CNN/EfficientNet with ECA classifies maize diseases on PlantVillage (98.85% accuracy); image classification, no pixel-level segmentation benchmark."),
"SCI-001135":("EXCLUDE",0.85,["EXC-05"],"Critical review of 100+ articles on drone-assisted AI plant-disease identification; secondary literature without a primary benchmark."),
"SCI-001139":("EXCLUDE",0.85,["EXC-03"],"U-Net/ResNet-34 runway segmentation for autonomous landing (IoU ~0.80); an aviation domain outside crop/weed agriculture."),
"SCI-001140":("EXCLUDE",0.85,["EXC-03"],"UAV power transmission-line conductor/fitting defect recognition via segmentation/detection; infrastructure-inspection domain, not crop/weed agriculture."),
"SCI-001141":("EXCLUDE",0.85,["EXC-03"],"Real-time semantic segmentation of solar PV arrays for UAV navigation (IoU 98.2%); solar-infrastructure domain, not crop/weed."),
"SCI-001142":("EXCLUDE",0.85,["EXC-03"],"Battlefield tactical path planning using semantic segmentation + DRL; military/terrain domain, not agriculture."),
"SCI-001143":("EXCLUDE",0.8,["EXC-03"],"CV-Cast linear coding/transmission optimization for remote vision inference (segmentation/detection); a communication-engineering focus with no agricultural segmentation benchmark."),
"SCI-001144":("EXCLUDE",0.82,["EXC-03"],"WaterSegLite semantic segmentation for UAV water-surface inspection/navigation (mIoU 93.81%); water-body monitoring domain, not crop/weed."),
"SCI-001145":("EXCLUDE",0.85,["EXC-03"],"DDRNet-23-slim semantic segmentation for UAV emergency landing-spot detection; UAV safety/landing domain, not agriculture."),
"SCI-001146":("EXCLUDE",0.85,["EXC-03"],"YOLOv8-SMR instance segmentation of transmission towers/conductors (TTPLA dataset); power-line infrastructure domain, not agriculture."),
"SCI-001147":("EXCLUDE",0.82,["EXC-03"],"U-Net/DeepLabV3+/SegFormer/YOLOv8 detect vegetation encroachment on power-line corridors (VEPL dataset, DeepLabv3+ mIoU 87.95%); power-line vegetation management, not crop/weed precision agriculture."),
"SCI-001148":("EXCLUDE",0.85,["EXC-03"],"Projection-based LiDAR point-cloud landing-zone detection for VTOL/drones; aviation/safety domain, not agriculture."),
"SCI-001149":("EXCLUDE",0.85,["EXC-03"],"Transformer-CNN seismic building damage assessment on satellite/UAV images; disaster/structural-engineering domain, not agriculture."),
"SCI-001150":("EXCLUDE",0.82,["EXC-03"],"Multi-task CNN human-crowd detection/segmentation for UAV flight safety; human/urban safety domain, not agriculture."),
"SCI-001151":("EXCLUDE",0.82,["EXC-03"],"Edge-feature-fusing Deeplabv3+ (EMNet) for UAV semantic segmentation on UAVid and ISPRS Vaihingen; urban/land-use benchmarks, not agricultural crop/weed."),
"SCI-001152":("EXCLUDE",0.82,["EXC-03"],"Lightweight dual-branch semantic segmentation for generic UAV imagery; no crop/weed agricultural domain or agricultural dataset."),
"SCI-001154":("EXCLUDE",0.85,["EXC-03"],"Detection/classification of small UAVs and birds in sparse LiDAR point clouds for airspace safety; not agriculture."),
"SCI-001155":("EXCLUDE",0.85,["EXC-03"],"Occlusion-aware UAV recognition using transformer semantic segmentation for urban surveillance/security; not agricultural crop/weed domain."),
"SCI-001156":("EXCLUDE",0.82,["EXC-03"],"Federated-learning aerial image segmentation for collision-free drone movement/landing (ResNet50+U-Net 91.51% pixel accuracy); UAV navigation domain, not agriculture."),
"SCI-001157":("EXCLUDE",0.85,["EXC-03"],"AI image-processing framework for military threat/target detection (YOLOv8, Faster R-CNN, DeepLabv3+); defence domain, not agriculture."),
"SCI-001158":("EXCLUDE",0.82,["EXC-03"],"Comparison of segmentation/detection networks (U-Net, DeepLabV3+, YOLO) for spatial orientation of UAVs on UAVid/synthetic imagery; navigation domain, not crop/weed."),
"SCI-001159":("EXCLUDE",0.8,["EXC-02","EXC-03"],"Semantic-aware correlation tracking (SARCT) for UAV video object tracking; an object-tracking task in a non-agricultural domain."),
"SCI-001160":("EXCLUDE",0.82,["EXC-03"],"Boundary-enhancement loss for land-cover semantic segmentation (buildings, roads) on remote-sensing imagery; urban land-use, not crop/weed."),
"SCI-001161":("EXCLUDE",0.85,["EXC-03"],"TMBNet lightweight unstructured road extraction from UAV images; road/transportation domain, not agriculture."),
"SCI-001162":("EXCLUDE",0.82,["EXC-03"],"RTMamba real-time remote-sensing segmentation on Vaihingen/Potsdam/LoveDA; urban/land-use benchmarks, not agricultural crop/weed."),
"SCI-001163":("EXCLUDE",0.82,["EXC-03"],"Design-sense-plan DCNN semantic segmentation for autonomous geometric-semantic mapping/inspection; exploration/inspection domain (dry dock demo), not agriculture."),
"SCI-001164":("EXCLUDE",0.85,["EXC-03"],"ES-Net edge-semantic collaborative network for forest canopy-gap mapping/disturbance monitoring; forestry domain, not crop/weed management."),
"SCI-001165":("EXCLUDE",0.8,["EXC-03"],"TAVIC-DAS task/channel-aware image compression for distributed multi-agent perception (semantic/instance segmentation); communication/compression focus with no agricultural segmentation benchmark."),
"SCI-001166":("EXCLUDE",0.7,["EXC-06"],"No abstract available; cannot verify crop/weed segmentation task or recoverable quantitative metrics for RQ1/RQ2."),
"SCI-001167":("EXCLUDE",0.85,["EXC-03"],"Point-based neural network (ConvPoint) landing-zone detection for VTOL LiDAR navigation; aviation domain, not agriculture."),
"SCI-001168":("EXCLUDE",0.85,["EXC-03"],"GangaFlow real-time river pollution detection with drone imagery (YOLOv8, U-Net, AlexNet); water/environmental monitoring domain, not crop/weed."),
"SCI-001169":("EXCLUDE",0.82,["EXC-03"],"ASEP autonomous semantic exploration planner for GPS-denied indoor UAV navigation; exploration/navigation domain, not agriculture."),
"SCI-001170":("EXCLUDE",0.82,["EXC-03"],"SA-Net.v2 real-time vehicle detection from oblique UAV images (UAVid dataset); urban traffic/vehicle domain, not agriculture."),
"SCI-001171":("EXCLUDE",0.82,["EXC-03"],"U-Net/MobileNetV2 semantic segmentation for autonomous UAV navigation in GNSS-denied settings (satellite-annotated data); navigation domain, not agricultural crop/weed."),
"SCI-001172":("EXCLUDE",0.85,["EXC-03"],"Semantic segmentation models (U-Net, LinkNet, FPN, UNet++) for infrastructure crack detection on shelled-UAV imagery; structural-inspection domain, not agriculture."),
"SCI-001174":("EXCLUDE",0.85,["EXC-03"],"U-Net geo-crack detection on drone photos of rock massifs for tunnel/geological assessment; geoscience domain, not agricultural crop/weed."),
"SCI-001176":("EXCLUDE",0.85,["EXC-03"],"CDSFusion dense semantic SLAM for indoor CPU-based UAV navigation/reconstruction; indoor-robotics domain, not crop/weed agriculture."),
"SCI-001177":("EXCLUDE",0.82,["EXC-03"],"SAAF-Net multi-source data fusion for high-precision 3D mapping of complex landforms (urban canyons, forests); surveying/mapping domain, not crop/weed."),
"SCI-001178":("EXCLUDE",0.85,["EXC-03"],"Deep-learning semantic segmentation (U-Net, DeepLab, PSPNet, RefineNet) for autonomous corrosion detection on metallic surfaces via UAV; infrastructure/material inspection, not agriculture."),
"SCI-001179":("EXCLUDE",0.82,["EXC-03"],"NoctuDroneNet real-time nighttime UAV semantic segmentation on NUI-Night/VDD/Night-City; urban/nighttime scene domain, not agricultural crop/weed."),
"SCI-001181":("EXCLUDE",0.82,["EXC-03"],"UAV path planning via semantic segmentation of 3D reality mesh (buildings/vegetation/ground/water) for photogrammetry; 3D-reconstruction domain, not crop/weed agriculture."),
"SCI-001183":("EXCLUDE",0.85,["EXC-03"],"BiSeNet semantic segmentation + BIM-GIS for bridge construction-progress monitoring (UAV aerial, PA 0.994, MIoU 0.990); construction/engineering domain, not agriculture."),
"SCI-001184":("EXCLUDE",0.85,["EXC-03"],"Region-based logit distillation for edge-friendly segmentation on Cityscapes/CamVid (Jetson Xavier NX FPS/power) has strong INC-03 edge metrics, but INC-01/INC-02 require agricultural crop/weed imagery; urban driving domain."),
"SCI-001185":("EXCLUDE",0.85,["EXC-03"],"Egospheric spatial memory module with semantic segmentation on ScanNet for drone/manipulator control; embodied-robotics/indoor domain, not agriculture."),
"SCI-001186":("EXCLUDE",0.85,["EXC-03"],"MISF measures standing tree size (height, DBH, crown width) via UAV multi-vision semantic segmentation; forestry-inventory domain, not crop/weed management."),
"SCI-001187":("EXCLUDE",0.82,["EXC-02","EXC-03"],"Adaptive YOLO11 framework localizes/tracks/imagines small aerial targets (drones/aircraft) via PTZ camera; object detection/tracking of aircraft, not segmentation or agriculture."),
"SCI-001188":("EXCLUDE",0.82,["EXC-03"],"NeuroSymLand neuro-symbolic framework for UAV safe landing-site assessment; aviation/recovery domain, not agricultural crop/weed."),
"SCI-001189":("EXCLUDE",0.8,["EXC-03"],"Runs real-time semantic segmentation on Raspberry Pi Zero attached to a DJI Tello toy drone for people/parking-slot detection; although edge-deployment results are central, the domain (human/parking detection) is outside crop/weed agriculture."),
"SCI-001190":("EXCLUDE",0.85,["EXC-03"],"YOLOv7-tiny + DeepLabv3+ UAV assessment of tree structural defects (cracks, holes); forestry/tree-health domain, not crop/weed segmentation."),
"SCI-001191":("EXCLUDE",0.82,["EXC-03"],"Fast GAN-augmented semantic segmentation for autonomous driving/aerial-perspective systems on driving datasets; general autonomous-driving domain, not agricultural."),
"SCI-001192":("EXCLUDE",0.82,["EXC-03"],"Synthetic-to-real OneFormer pipeline for safe UAV landing-zone detection (UAVid benchmark); aviation-landing domain, not agriculture."),
"SCI-001193":("EXCLUDE",0.8,["EXC-02","EXC-03"],"Integrated HRNet segmentation + YOLOv11 + DeepSORT framework for UAV vehicle detection/traffic monitoring; urban-traffic domain, detection-centric, not agricultural."),
"SCI-001194":("EXCLUDE",0.85,["EXC-03"],"BKFE-UNet individual tree-canopy segmentation from UAV imagery (mPA 92.62%, mIoU 86.50%); forestry canopy-parameter domain, not crop/weed management."),
"SCI-001195":("EXCLUDE",0.85,["EXC-03"],"Digital-twin/BIM/CV/IoT intelligent construction-site monitoring (YOLOv8, SlowFast, DeepLabV3+); construction-management domain, not agriculture."),
"SCI-001196":("EXCLUDE",0.82,["EXC-03"],"SegFormer evaluation for UAV semantic segmentation on UAVid; urban scene/land-cover benchmark, not agricultural crop/weed."),
"SCI-001197":("EXCLUDE",0.82,["EXC-03"],"Adaptive monocular visual odometry for outdoor pose estimation using depth/semantic segmentation; localization domain, not crop/weed agriculture."),
"SCI-001198":("EXCLUDE",0.85,["EXC-03"],"UAVSeg dual-encoder cross-scale attention for UAV semantic segmentation on UAVid/Urban Drone/AeroScapes; urban general-aerial benchmarks, not agricultural."),
"SCI-001199":("EXCLUDE",0.85,["EXC-03"],"USV-UAV cooperative trajectory planning where UAV provides semantic segmentation of obstacles for a surface vehicle; marine/robotic-navigation domain, not agriculture."),
"SCI-001200":("EXCLUDE",0.85,["EXC-03"],"Efficient real-time semantic segmentation for large-scale natural-disaster damage assessment (RescuNet dataset); disaster-management domain, not crop/weed."),
"SCI-001201":("EXCLUDE",0.8,["EXC-03"],"Improved DeepLabv3+ extracts citrus-orchard navigation/road lines for agricultural-drone navigation (mPA 94.71%, 96.62 fps); intra-orchard path-segmentation in an orchard domain, not crop/weed segmentation."),
"SCI-001202":("EXCLUDE",0.82,["EXC-03"],"Co-SemDepth joint depth/semantic prediction for low-altitude unstructured environments, focused on marine domain (MidSea/SMD); depth estimation and marine scenes, not agricultural crop/weed."),
"SCI-001204":("EXCLUDE",0.82,["EXC-03"],"VFM-CAKD category-aware knowledge distillation for lightweight aerial semantic segmentation on Aeroscapes/UAVid/Potsdam/Vaihingen/RescueNet; urban/disaster remote-sensing benchmarks, not agricultural crop/weed."),
"SCI-001206":("EXCLUDE",0.82,["EXC-03"],"Semantic visual-inertial SLAM (VINS-Mono + dynamic feature removal) for localization in dynamic environments; localization/SLAM domain, not agriculture."),
"SCI-001207":("EXCLUDE",0.75,["EXC-03"],"GEA-UNet lightweight semantic segmentation of irrigation canals from UAV imagery (accuracy 98.9%, mIoU 85.4%, F1 92.2%) for agricultural-drone navigation; although agricultural context, the segmented object is water-conveyance infrastructure (canals), not crop/weed plants."),
"SCI-001208":("EXCLUDE",0.8,["EXC-03"],"Edge-AI UAV platform with onboard RGB/MS semantic extraction for generic monitoring with 5G/digital twin; application-agnostic monitoring, not specifically agricultural crop/weed."),
"SCI-001209":("EXCLUDE",0.85,["EXC-03"],"Dual-branch semantic segmentation of solid-waste piles from UAV imagery (OA >94%, recall 88.6%); environmental/solid-waste domain, not agriculture."),
"SCI-001211":("EXCLUDE",0.85,["EXC-03"],"SSRA semantic-segmentation-guided region-attention for infrared image colorization on drone datasets (SAM2 masks); image-colorization task, not agricultural segmentation."),
"SCI-001212":("EXCLUDE",0.85,["EXC-03"],"Real-time progressive 3D semantic segmentation of indoor scenes (SceneNN/ScanNet); indoor-recognition domain, not agriculture."),
"SCI-001213":("EXCLUDE",0.82,["EXC-03"],"Intelligent monitoring and route-adaptation system for drones using neural-network risk analysis (object detection, segmentation, trajectory planning); generic UAV navigation/safety domain, not agriculture."),
"SCI-001214":("EXCLUDE",0.82,["EXC-03"],"Scene identification via semantic segmentation + classifier on Jetson edge devices for service robots/drone inspection/visual surveillance; generic scene-recognition domain, not agriculture."),
"SCI-001215":("EXCLUDE",0.85,["EXC-03"],"Aerial procedural modeling of city buildings via facade semantic segmentation + shape grammar; urban/building-modeling domain, not agriculture."),
"SCI-001217":("EXCLUDE",0.85,["EXC-03"],"U-Net-based infrared image stitching of wind-turbine blades from UAV flight data; wind-energy infrastructure domain, not agriculture."),
"SCI-001219":("EXCLUDE",0.85,["EXC-03"],"Cognitive-fusion path planning for UAV inspection of power-tower insulators (LiDAR + RGB semantic segmentation); power-infrastructure domain, not agriculture."),
"SCI-001220":("EXCLUDE",0.85,["EXC-03"],"YOLOv7 + U-Net recognition of industrial instrument panels from a UAV (pruning/quantization for mobile edge); industrial-instrumentation domain, not agriculture."),
"SCI-001221":("EXCLUDE",0.82,["EXC-03","EXC-06"],"Contextual U-Net (BFE/AFS/RFF) for generic UAV remote-sensing semantic segmentation (4509 images, 6 categories); categories/applications are generic land-use with no crop/weed specificity and quantitative per-class crop metrics not detailed."),
"SCI-001223":("EXCLUDE",0.85,["EXC-03"],"MDLab lightweight DeepLabV3+ variant for concrete bridge surface-crack detection from drones (mIoU 88.27%, 22ms); civil/infrastructure domain, not agriculture."),
"SCI-001224":("EXCLUDE",0.82,["EXC-03"],"CrossSeg cross-scene few-shot aerial semantic segmentation with probabilistic prototypes; general aerial imagery (UAV remote sensing), not agricultural crop/weed."),
}

missing = [i for i in ids if i not in A]
print("total ids:", len(ids), "adjudicated:", len(A), "missing:", missing)
dup = set(ids) if len(ids)!=len(set(ids)) else set()
print("dup ids:", dup)

records = []
for wid in ids:
    dec, conf, codes, reason = A[wid]
    r1 = s1.get(wid,{})
    r2 = s2.get(wid,{})
    records.append({
        "workspace_id": wid,
        "decision": dec,
        "confidence": conf,
        "final_codes": codes,
        "adjudication_reasoning": reason,
        "s1_decision": r1.get('decision'),
        "s2_decision": r2.get('decision')
    })

with io.open('_adjudication_resolved_group_4.json','w',encoding='utf-8') as f:
    f.write(json.dumps(records, ensure_ascii=False, indent=2))

inc = sum(1 for r in records if r['decision']=='INCLUDE')
exc = sum(1 for r in records if r['decision']=='EXCLUDE')
print("INCLUDE:", inc, "EXCLUDE:", exc, "total:", len(records))
