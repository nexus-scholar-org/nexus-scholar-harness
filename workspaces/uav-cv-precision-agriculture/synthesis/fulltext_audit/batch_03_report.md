# Full-text read-through batch 03

## SCI-000488 — Deep Learning-Based Weed Detection Using UAV Images: A Comparative Study

attribution: CONFIRMED for model=UNet with EfficientNetB0 backbone (multiclass D2 segmentation) backbone=EfficientNetB0 dataset=CoFly-WeedDB

| claim key | claimed value | verdict | verbatim source quote |
|---|---|---|---|
| mIoU | 0.5621 | CONFIRMED | "The results show that UNet with EfﬁcientNetB0 as a backbone CNN is the best-performing model compared with the other candidate models used in this study on the CoFly-WeedDB dataset, imparting Precision (88.20%), Recall (88.97%), F1-score (88.24%) and mean Intersection of Union (56.21%)." |
| F1 | 0.8824 | CONFIRMED | "The results show that UNet with EfﬁcientNetB0 as a backbone CNN is the best-performing model compared with the other candidate models used in this study on the CoFly-WeedDB dataset, imparting Precision (88.20%), Recall (88.97%), F1-score (88.24%) and mean Intersection of Union (56.21%)." |
| PA | 0.8897 | CONFIRMED | "D2 SegNet 53.30 85.68 86.66 85.98 86.66 UNet 56.21 88.20 88.97 88.24 88.97 DeepLabV3+ 40.74 84.46 85.94 84.60 85.94" |
| weed_F1 | 0.6326 | CONFIRMED | "Johnson grass 44.78 79.04 50.82 63.70 Bind weed 46.73 82.00 52.08 63.70 Purslane 45.31 72.94 54.47 62.37" |
| device | None - offline (Google Colab cloud, NVIDIA T4 GPU 12 GB RAM) | CONFIRMED | "All the experiments were carried out on Google Colab [57] cloud computing platform which utilized an NVIDIA T4 GPU with 12 GB RAM." |
| resolution_input | 256 | CONFIRMED | "Following this procedure, each UAV image is divided into patches of size (256 px × 256 px), which results in a total of 786 image patches." |
| framework | Keras (Python), Adam optimizer lr 0.001, up to 100 epochs, early stopping (patie | CONFIRMED | "The experimental setup to conduct the weed segmentation was built on Python-based Keras package [56]. ... each segmentation model was trained up to maximum epochs of 100, with a learning rate of 0.001 and Adam optimizer." |

## SCI-000489 — Cross-domain transfer learning for weed segmentation and mapping in precision farming using ground and UAV images

attribution: CONFIRMED for model=Proposed cross-domain model with enhanced preprocessing (field dataset) backbone=Proposed deep learning model (encoder-decoder) dataset=self-collected field + UAV (maize, weed, soil)

| claim key | claimed value | verdict | verbatim source quote |
|---|---|---|---|
| mIoU | 0.767 | CONFIRMED | "The proposed network performed best among other networks with 0.859 mOA and 0.767 mIOU." |
| mPA | 0.859 | CONFIRMED | "The proposed network performed best among other networks with 0.859 mOA and 0.767 mIOU." |
| resolution_input | 512 | CONFIRMED | "We instead first resized original images and then randomly cropped image tiles (512*512) from the resized images (1200*800)." |
| params_M | 42.04 | CONFIRMED | "There are 42,037,391 parameters in total with 42,018,441 trainable parameters and 18,950 non-trainable parameters." |

## SCI-000492 — Semantic Segmentation Using Deep Learning with Vegetation Indices for Rice Lodging Identification in Multi-date UAV Visible Images

attribution: CONFIRMED for model=FCN-AlexNet (RGB+ExGR) backbone=AlexNet (FCN-AlexNet) dataset=Self-collected UAV rice paddies (~40 ha, Taiwan; 2017 train/test + 2019 validation)

| claim key | claimed value | verdict | verbatim source quote |
|---|---|---|---|
| F1 | 0.8 | CONFIRMED | "For the identiﬁcation of rice lodging on the 2017 UAV images, the F1-score reaches 0.80 and 0.79 for FCN-AlexNet and SegNet, respectively." |
| PA | 0.9124 | CONFIRMED | "Based on the results of the validation dataset, the highest accuracy of FCN-AlexNet reaches 91.24%, which is achieved by using RGB+ExGR information." |
| crop_F1 | 0.93 | CONFIRMED | "RGB+ExGR 93.00 80.08 56.95 95.36 93.52 91.24" |

## SCI-000501 — Deep learning-based early weed segmentation using motion blurred UAV images of sorghum fields

attribution: CONFIRMED for model=UNet + ResNet-34 backbone=ResNet-34 dataset=Self-collected UAV sorghum fields (BBCH 15/17/19); 2156 patches of 256x256

| claim key | claimed value | verdict | verbatim source quote |
|---|---|---|---|
| F1 | 0.8937 | CONFIRMED | "DS Precision Recall F1-score | 99.69 93.01 86.25 89.37" |
| Dice | 0.9969 | CONFIRMED | "DS Precision Recall F1-score | 99.69 93.01 86.25 89.37" |
| resolution_input | 256 | CONFIRMED | "We divided each image in non-overlapping patches with a resolution of 256x256 pixel for an efficient training process." |

## SCI-000514 — A fully convolutional network for weed mapping of unmanned aerial vehicle (UAV) imagery

attribution: CONFIRMED for model=FCN-8s (VGG-16 transfer + skip) backbone=VGG-16 dataset=Self-collected UAV rice field (Guangzhou, South China)

| claim key | claimed value | verdict | verbatim source quote |
|---|---|---|---|
| mIoU | 0.752 | CONFIRMED | "pixel acc. 0.923 0.928 0.935 | mean acc. 0.795 0.811 0.807 | mean IU 0.728 0.749 0.752 | f.w. IU 0.876 0.886 0.892" |
| mPA | 0.807 | CONFIRMED | "pixel acc. 0.923 0.928 0.935 | mean acc. 0.795 0.811 0.807 | mean IU 0.728 0.749 0.752 | f.w. IU 0.876 0.886 0.892" |
| PA | 0.935 | CONFIRMED | "The overall accuracy of the FCN approach was up to 0.935 and the accuracy for weed recognition was 0.883" |

## SCI-000547 — A Semantic Labeling Approach for Accurate Weed Mapping of High Resolution UAV Imagery

attribution: CONFIRMED for model=DFCN ResNet-101 ASPP-1 with CRF backbone=ResNet-101 (DFCN) dataset=Self-collected UAV rice field (Guangdong, China)

| claim key | claimed value | verdict | verbatim source quote |
|---|---|---|---|
| mIoU | 0.7751 | CONFIRMED | "The mean intersection over union (mean IU), overall accuracy, and Kappa coefﬁcient of our method were 0.7751, 0.9445, and 0.9128, respectively." |
| PA | 0.9445 | CONFIRMED | "The mean intersection over union (mean IU), overall accuracy, and Kappa coefﬁcient of our method were 0.7751, 0.9445, and 0.9128, respectively." |

## SCI-000555 — Adaptive autonomous UAV scouting for rice lodging assessment using edge computing with deep learning EDANet

attribution: CONFIRMED for model=EDANet (RGB+ExG+ExGR) backbone=EDANet dataset=Self-collected UAV rice (Wufeng, Taiwan; 2017 and 2019 datasets)

| claim key | claimed value | verdict | verbatim source quote |
|---|---|---|---|
| F1 | 0.7851 | CONFIRMED | "Based on the results of the 2019 dataset, EDANet using RGB + ExG + ExGR information illustrations the highest value in recall (85.22%), accuracy (92.83%), and F1 score (78.51%)." |
| PA | 0.9445 | CONFIRMED | "RGB + ExG + ExGR 95.19 86.03 80.26 96.51 96.46 94.45" |
| crop_F1 | 0.9519 | CONFIRMED | "RGB + ExG + ExGR 95.19 86.03 80.26 96.51 96.46 94.45" |

## SCI-000565 — Lightweight Semantic Segmentation Network for Real-Time Weed Mapping Using Unmanned Aerial Vehicles

attribution: CONFIRMED for model=Modified AlexNet-FCN (FP16 precision calibration) backbone=AlexNet (modified FCN) dataset=Self-collected UAV rice field

| claim key | claimed value | verdict | verbatim source quote |
|---|---|---|---|
| mIoU | 0.628 | CONFIRMED | "GTX 1060 FP16 80.9 62.8 35.6 | Jetson TX2 FP16 80.9 62.8 4.5" |
| PA | 0.809 | CONFIRMED | "GTX 1060 FP16 80.9 62.8 35.6 | Jetson TX2 FP16 80.9 62.8 4.5" |
| device | NVIDIA Jetson TX2 | CONFIRMED | "The Jetson TX2 module (Nvidia Corporation, Santa Clara, CA, USA) was selected as a control center to realize ﬂight control, image collection, and! timage processing." |
| precision | FP16 | CONFIRMED | "In this case, we applied FP32 for training and used FP16 for inference." |
| resolution_input | 1000x1000 | CONFIRMED | "Images are cropped according to the central 720 × 720 pixel area and then resized to 1000 × 1000 pixels, which was proven to be a suitable image size for weed mapping by the previous work of our team [14]." |
| fps | 4.5 | CONFIRMED | "Our modiﬁed network architecture achieved an accuracy of 80.9% on the testing samples and its inference speed was 4.5 fps on a Jetson TX2 module" |

## SCI-000570 — Use of synthetic images for training a deep learning model for weed detection and biomass estimation in cotton

attribution: CONFIRMED for model=Mask R-CNN trained on original 2048x2048 real images (row-oriented synthetic second) backbone=Mask R-CNN dataset=self-collected UAV cotton (morningglory and grass weeds)

| claim key | claimed value | verdict | verbatim source quote |
|---|---|---|---|
| resolution_input | 2048 | CONFIRMED | "Since the input image size to the model was 2048 × 2048, the IMGS PER GPU parameter was set to 1 because setting value more than 1 resulted in “CUDA OUT OF MEMORY” error." |

## Batch summary

| study | CONFIRMED | MISMATCH | NOT_FOUND | LOW_CONF |
|---|---|---|---|---|
| SCI-000488 | 7 | 0 | 0 | 0 |
| SCI-000489 | 4 | 0 | 0 | 0 |
| SCI-000492 | 3 | 0 | 0 | 0 |
| SCI-000501 | 3 | 0 | 0 | 0 |
| SCI-000514 | 3 | 0 | 0 | 0 |
| SCI-000547 | 2 | 0 | 0 | 0 |
| SCI-000555 | 3 | 0 | 0 | 0 |
| SCI-000565 | 6 | 0 | 0 | 0 |
| SCI-000570 | 1 | 0 | 0 | 0 |
| **Overall** | **32** | **0** | **0** | **0** |