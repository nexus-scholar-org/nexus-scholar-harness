---
workspace_id: SCI-001053
doi: 10.3390/rs16234394
title: Deep Learning for Weed Detection and Segmentation in Agricultural Crops Using
  Images Captured by an Unmanned Aerial Vehicle
authors:
- family_name: Silva
  given_name: Josef Augusto Oberdan Souza
  orcid: null
- family_name: Siqueira
  given_name: Vilson Soares de
  orcid: null
- family_name: Mesquita
  given_name: "M\xE1rcio"
  orcid: null
- family_name: Vale
  given_name: "Lu\xEDs S\xE9rgio Rodrigues"
  orcid: null
- family_name: Marques
  given_name: Thiago do Nascimento Borges
  orcid: null
- family_name: Silva
  given_name: J. L. B.
  orcid: null
- family_name: Silva
  given_name: M. V.
  orcid: null
- family_name: Lacerda
  given_name: L. N.
  orcid: null
- family_name: "Oliveira-J\xFAnior"
  given_name: "Jos\xE9 Francisco de"
  orcid: null
- family_name: Lima
  given_name: "Jo\xE3o L. M. P. de"
  orcid: null
- family_name: Oliveira
  given_name: H. F. E. D.
  orcid: null
year: 2024
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:35:01.738292+00:00'
---

# Deep Learning for Weed Detection and Segmentation in Agricultural Crops Using Images Captured by an Unmanned Aerial Vehicle

Article Deep Learning for Weed Detection and Segmentation in Agricultural Crops Using Images Captured by an Unmanned Aerial Vehicle

Josef Augusto Oberdan Souza Silva 1 , Vilson Soares de Siqueira 2, Marcio Mesquita 3 , Luís Sérgio Rodrigues Vale 1,4 , Thiago do Nascimento Borges Marques 4, Jhon Lennon Bezerra da Silva 1 , Marcos Vinícius da Silva 5 , Lorena Nunes Lacerda 6 , José Francisco de Oliveira-Júnior 7 , João Luís Mendes Pedroso de Lima 8,9 and Henrique Fonseca Elias de Oliveira 1,4,*

1 Cerrado Irrigation Graduate Program, Goiano Federal Institute—Campus Ceres, GO-154, km 218—Zona Rural, Ceres 76300-000, Goiás, Brazil; josef.silva@estudante.ifgoiano.edu.br (J.A.O.S.S.); luis.sergio@ifgoiano.edu.br (L.S.R.V.); jhon.silva@ifgoiano.edu.br (J.L.B.d.S.) 2 Faculty of Information Systems, Goiano Federal Institute—Campus Ceres, GO-154, km 218—Zona Rural, Ceres 76300-000, Goiás, Brazil; vilson.soares@ifgoiano.edu.br 3 Faculty of Agronomy, Federal University of Goiás (UFG), Nova Veneza, Km 0, Campus Samambaia—UFG, Goiânia 74690-900, Goiás, Brazil; marcio.mesquita@ufg.br 4 Faculty of Agronomy, Goiano Federal Institute—Campus Ceres, GO-154, km 218—Zona Rural, Ceres 76300-000, Goiás, Brazil; thiago.borges1@estudante.ifgoiano.edu.br 5 Postgraduate Program in Forestry Sciences, Federal University of Campina Grande (UFCG), Av. Universitária, s/n, Santa Cecília, Patos 58708-110, Paraíba, Brazil; marcos.viniciussilva@ufrpe.br 6 Crop and Soil Sciences Department, University of Georgia, Athens, GA 30602, USA; llacerda@uga.edu 7 Institute of Atmospheric Sciences (ICAT), Federal University of Alagoas (UFAL), Maceió 57072-260, Alagoas, Brazil; jose.junior@icat.ufal.br 8 Department of Civil Engineering, Faculty of Sciences and Technology, University of Coimbra, 3030-788 Coimbra, Portugal; plima@dec.uc.pt 9 MARE—Marine and Environmental Sciences Centre, University of Coimbra, 3000-456 Coimbra, Portugal * Correspondence: henrique.fonseca@ifgoiano.edu.br; Tel.: +55-(062)-3307-7100

Citation: Silva, J.A.O.S.; Siqueira,

V.S.d.; Mesquita, M.; Vale, L.S.R.;

Abstract: Artificial Intelligence (AI) has changed how processes are developed, and decisions are made in the agricultural area replacing manual and repetitive processes with automated and more efficient ones. This study presents the application of deep learning techniques to detect and segment weeds in agricultural crops by applying models with different architectures in the analysis of images captured by an Unmanned Aerial Vehicle (UAV). This study contributes to the computer vision field by comparing the performance of the You Only Look Once (YOLOv8n, YOLOv8s, YOLOv8m, and YOLOv8l), Mask R-CNN (with framework Detectron2), and U-Net models, making public the dataset with aerial images of soybeans and beans. The models were trained using a dataset consisting of 3021 images, randomly divided into test, validation, and training sets, which were annotated, resized, and increased using the Roboflow application interface. Evaluation metrics were used, which included training efficiency (mAP50 and mAP50-90), precision, accuracy, and recall in the model’s evaluation and comparison. The YOLOv8s variant achieved higher performance with an mAP50 of 97%, precision of 99.7%, and recall of 99% when compared to the other models. The data from this manuscript show that deep learning models can generate efficient results for automatic weed detection when trained with a well-labeled and large set. Furthermore, this study demonstrated the great potential of using advanced object segmentation algorithms in detecting weeds in soybean and bean crops.

Marques, T.d.N.B.; Silva, J.L.B.d.;

Silva, M.V.d.; Lacerda, L.N.;

Oliveira-Júnior, J.F.d.; Lima, J.L.M.P.d.;

et al. Deep Learning for Weed

Detection and Segmentation in

Agricultural Crops Using Images

Captured by an Unmanned Aerial

Vehicle. Remote Sens. 2024, 16, 4394.

https://doi.org/10.3390/rs16234394

Academic Editor: Guido D’Urso

Received: 6 September 2024

Revised: 7 November 2024

Accepted: 20 November 2024

Published: 24 November 2024

Copyright: © 2024 by the authors.

Licensee MDPI, Basel, Switzerland.

Keywords: remote sensing; agricultural crops; Detectron2; Mask R-CNN; precision agriculture; segmentation algorithms; U-Net; You Only Look Once (YOLO)

This article is an open access article

distributed under the terms and

conditions of the Creative Commons

Attribution (CC BY) license (https://

creativecommons.org/licenses/by/

4.0/).

Remote Sens. 2024, 16, 4394. https://doi.org/10.3390/rs16234394 https://www.mdpi.com/journal/remotesensing

Remote Sens. 2024, 16, 4394 2 of 23


## 1. Introduction

Several studies have recently emerged with the proposal of detecting and classifying plants using machine learning technologies [1–6]. Machine learning (ML) and deep learning (DL) models are used to automate agricultural procedures and help machines perform automatic, accurate, and efficient image-recognition processes [7–9]. ML is a subarea of Artificial Intelligence (AI), based on self-learning algorithms, which allow the system to learn patterns through experience, becoming intelligent over time and without human intervention. On the other hand, DL is a subcategory of machine learning and follows a neural network architecture approach. It refers to algorithms that learn patterns through experience but include a large amount of information provided in the input. The term “deep” refers to the multiple layers between the input and output of a neural network [10],

and the number of training epochs corresponds to the number of times the DL model traverses the entire data during the training phase. In summary, DL is a network model with neurons having several parameters and layers between input and output, and it provides automatic feature learning through its multi-level hierarchical representation [11].

AI applications in agriculture involve, among other aspects, the use of images from satellites to monitor crop stress, such as water deficit, plant diseases, agricultural pests, and weeds [12]. Studies with applications using satellites/sensors and airplanes for specific weed management techniques have proven successful in monitoring and detecting specific plants in their early stages of development [13]. However, in the plant development stage of bean and soybean crops, invasive plants can mix with the crop and make using satellites/sensors to monitor and detect weeds more challenging [14]. In this context, images captured by Unmanned Aerial Vehicles (UAVs) may be more efficient for identifying specific plants among crops [15–17].

Weed detection and classification methodologies using aerial images contribute to the implementation of weed management [18]. Images captured by a UAV operated at lower altitudes offer greater spatial resolution when compared to satellite images or conventional aircraft [19]. In commercial agricultural productions, weeds can be controlled using three conventional control techniques—mechanical, chemical, and cultural [20], involving specific plant monitoring procedures [21]. The specific weed management approach offers a map with geographic information about the plants presented in the specified location to assist in chemical product application for proper weed control [22,23]. DL and ML models can help locate these invasive plants found in the cultivation site and help control them [24,25].

Weeds grow spontaneously in cultivated fields and interfere with the development of commercial crops present in the area competing with natural resources, such as water, nutrients, and light [26,27]. These plants are seen as a problem because they present high resistance to adversity, adapting to environments that present water stress, high levels of salinity, and acidity in the soil and environments with high temperatures and humidity unfavorable for crop cultivation [28].

As a way of increasing the efficiency in identifying and combating invasive plants in commercial crops, the use of computational models for image analysis becomes a tool of great applicability in agricultural activity through the application of models, such as YOLO (You Only Look Once), Mask R-CNN (with Detectron2 framework), and U-Net [29,30]. The YOLO model considers the multiscale features of objects and uses three layers of detection with objects of different scales being able to classify and identify objects by examining the image or video dataset once [30,31]. The instance segmentation models include variations and versions of the YOLO model with an emphasis on YOLOv8. The YOLOv8 model, in particular, contains two main parts in its architecture, the backbone and the head, and can be used to detect new plants early, presenting results above 90%, compared to the YOLOv5 and Faster R-CNN models [31].

Detectron2 is a framework that contains implementations of several state-of-the-art algorithms used for object detection and segmentation while being designed for detection and segmentation tasks [32]. The backbone of the Detectron2 framework provides pre-

Remote Sens. 2024, 16, 4394 3 of 23

trained architectures based on large image datasets, e.g., ResNet, ResNetXt, and MobileNet, to extract image features [33]. The backbone network is composed of layers organized hierarchically to gradually reduce the dimensionality of the resource maps while increasing the number of channels [34,35].

U-Net is an image-segmentation model in the medical field based on a fully convolu- tional network (FCN) proposed by Ronneberger [36]. This symmetric network is divided into two main units: encoder and decoder [36,37]. The encoder aims to capture the context of the image, consisting of convolutional and pooling layers [37]. In this section, which contains two 3 × 3 convolution layers and a rectified linear unit (ReLu), spatial properties are extracted from the image and used to generate an unencoded segmentation map [37,38]. The second part is the decoder, which allows for precise object localization in the image using transposed convolutions [36,38]. The encoder is composed of successive layers, in which the pooling operators are exchanged for an upsampling operator, increasing the output resolution. For accurate localization in the decoder, the high-resolution features of the encoder are concatenated with the upsampled output [36,38].

ML models, to be properly evaluated for their performance, need to be trained and then based on evaluation analyses [39–41]. Evaluation scores are important performance indicators and summarize the final state of the model, including mathematical expressions for calculations, such as results, accuracy, average precision, and recall [42,43].

Many researchers that used architectures based on convolutional neural networks proposed weed detection; among the most used are the single-stage algorithms, such as SSD [32], Faster-RCNN [33], and YOLO [33,40], for example. In this sense, in recent studies, convolutional networks have been used to provide classification results for all types of weeds, quickly and accurately [29–31,35,38]. However, the classification models used by some authors to categorize weeds are also not evaluated and compared in terms of performance and loss in the model training and validation stages [28,36,42].

Given the wide applicability of DL models for aerial imaging applications of cultivated areas and the application gaps in this area, the objective of this study was to carry out a detailed evaluation of the advanced object segmentation algorithms Mask R-CNN (with Detectron2 framework), U-Net, YOLOv5s, YOLOv7, and YOLOv8 with the performances of their variants YOLOv8n, YOLOv8s, YOLOv8m, and YOLOv8l in detecting weeds in soybean and bean crops using RGB images captured by a UAV. More specifically, this study aims to improve cultivation techniques with the use of UAVs by offering greater predictive capacity and availability of crop data quickly and efficiently. Furthermore, this study aims to contribute to the following: (1) to amplify the understanding of the main deep learning models and their variants, when applied to remote sensing data; (2) compare the performance of AI models, using evaluation metrics, aimed at automatic weed detection; (3) create a well-labeled and robust database for future research involving deep learning.

The article is divided into the following sections: the material and methodology applied in this study are presented in Section 2. The results of performance tests of different backbones and their variants and different training periods are shown in Section 3. Discussions about the results of each trained deep learning model are presented in Section 4. Finally, the conclusion is presented in Section 5.


## 2. Material and Methods

2.1. Field Experiment

The experiment was installed at the Instituto Federal Goiano—Campus Ceres, Ceres municipality, state of Goiás, in the central-western region of Brazil. The experimental agricultural area was planted with common bean (Phaseolus vulgaris) and soybean (Glycine max), the type of soil at the site is Red Latosol with a clayey texture [44], and it is located specifically in the following geographic coordinates 15◦21′16′′S and 49◦36′23′′W, with an altitude of 570 m (Figure 1).

Remote Sens. 2024, 16, 4394 4 of 23


> **Figure 1. The study area is located in the central-western region of Brazil (a), in the state of Goiás (b),**

> at the Instituto Federal Goiano—Campus Ceres, in the Ceres municipality (c). The experimental area
was planted with common bean (Phaseolus vulgaris) and soybean (Glycine max) (d), and a flight plan
was used to cover the entire experimental area (e).

2.2. Weed Processing and Segmentation Steps

The workflow for weed detection and segmentation is comprised of four main steps, including data preparation, training, model performance evaluation, and deployment (Figure 2). During data preparation, the Roboflow [45] tool was used to label and resize each image in the set. These images were subsequently augmented and trained on U- Net, YOLO, and the Mask R-CNN (framework Detectron2) segmentation models during training. Trained models were then evaluated for model performance using six different evaluation metrics, and lastly, models were deployed in the field.

2.3. Acquisition of RGB Images

Image acquisition was performed with a Phantom® 3 Standard UAV (DJI, Shenzhen, China) with an RGB Full HD digital camera with a resolution of 1980 × 1080 pixels. A flight plan was created, and the parameters and flight conditions (date and time of collection, and flight height) were recorded on a spreadsheet. The UAV image capture in soybean and common bean crops was carried out over three months from December 2022 to February 2023 composing a dataset of 793 images. Flights were carried out once a day under favorable weather conditions (sunny days). The flight plan was created using the Pix4D®capture software, version 2.8.3. The frontal and side overlaps for image capture were 80% and 72%, respectively, and the flight height was 20 m resulting in a ground sampling distance (GSD—Ground Sample Distance) of 8.8 mm/px. Table 1 shows the date of image acquisition by the UAV and the respective phenological phase of the common bean (Phaseolus vulgaris) and soybean (Glycine max) crops, according to BBCH English [46].

Remote Sens. 2024, 16, 4394 5 of 23


> **Figure 2. Training process flow for weed segmentation. Steps: (1) images labeled and resized**

> using the Roboflow tool; (2) images augmented and trained on U-Net, YOLO, and Mask R-CNN
(framework Detectron2) segmentation models; (3) validation metrics used in the trained models;
(4) field testing the model with greater efficiency.


> **Table 1. Date of image acquisition and respective phenological phases of the bean (Phaseolus vulgaris)**

> and soybean (Glycine max).

BBCH- Identification

Cultures Month Day Year Principal Growth Stage

Keys

Bean (Phaseolus vulgaris)/Soybean (Glycine max) 11 19 2022 1: Leaf development 10 Bean (Phaseolus vulgaris)/Soybean (Glycine max) 11 23 2022 1: Leaf development 13 Bean (Phaseolus vulgaris)/Soybean (Glycine max) 11 25 2022 1: Leaf development 19 Bean (Phaseolus vulgaris)/Soybean (Glycine max) 12 12 2022 2: Formation of side shoots 21 Bean (Phaseolus vulgaris)/Soybean (Glycine max) 12 14 2022 2: Formation of side shoots 23 Bean (Phaseolus vulgaris)/Soybean (Glycine max) 12 19 2022 2: Formation of side shoots 28 Bean (Phaseolus vulgaris)/Soybean (Glycine max) 12 20 2022 2: Formation of side shoots 28 Bean (Phaseolus vulgaris)/Soybean (Glycine max) 12 28 2022 5: Inflorescence emergence 51 Bean (Phaseolus vulgaris)/Soybean (Glycine max) 1 4 2023 5: Inflorescence emergence 57 Bean (Phaseolus vulgaris)/Soybean (Glycine max) 1 11 2023 6: Flowering 64 Bean (Phaseolus vulgaris)/Soybean (Glycine max) 1 18 2023 7: Development of fruit 73 Bean (Phaseolus vulgaris)/Soybean (Glycine max) 1 24 2023 7: Development of fruit 78 Bean (Phaseolus vulgaris)/Soybean (Glycine max) 2 1 2023 8: Ripening of fruit and seed 81 Bean (Phaseolus vulgaris)/Soybean (Glycine max) 2 6 2023 8: Ripening of fruit and seed 85 Bean (Phaseolus vulgaris)/Soybean (Glycine max) 2 15 2023 8: Ripening of fruit and seed 88

Remote Sens. 2024, 16, 4394 6 of 23

2.3.1. Dataset Annotation

The Roboflow [45] tool was used to label and classify the objects in the dataset. The dataset contains three classes named “bean”, “soybean”, and “weed”, randomly divided into training, validation, and test sets, with 75%, 12%, and 13% of all images, respectively. The percentage of images randomly divided into the three groups (training, validation and testing), previously mentioned, follows an approximate percentage that can be seen in studies by Gallo et al. [32] and Butt et al. [33] for training deep learning models. To annotate the dataset, the images were labeled using the Roboflow tool, and the process was conducted with the automatic labeling of object polygons that the tool itself makes available in its system (Figure 3). The tool applied an initial label, and then, the system suggested a precise outline of the marked object. The resulting real positions of the objects in the image were stored in a JSON format and converted to the desired data format for training.


> **Figure 3. Isolation of objects from the image set.**

After the labeling process of each image in the set, it was possible to count the num- ber of instances (objects), subdivided by classes (“bean”, “soybean”, and “weed”). The characteristics of the generated dataset (soybean and beans) are shown in Table 2.


> **Table 2. Characteristics of the generated Bean Soy dataset.**

Characteristics Bean Soy Dataset

Number of images 793 Number of instances 16,113 Average weeds per picture 8.92 Total number of weeds 7074 Number of bean plants 4532 Number of soybean plants 4507

Remote Sens. 2024, 16, 4394 7 of 23

2.3.2. Dataset Resizing

The images were resized to 640 × 640 pixels and 512 × 512 pixels (Figure 4) for the YOLOv8, YOLOv7, YOLOv5s, and Mask R-CNN (with Detectron2) and U-Net models, respectively. By resizing the images in the dataset, it was possible to maintain the width and height ratio that the pre-trained models requested for data input. However, as the U-Net model does not have fully connected layers, it can accept images of arbitrary sizes. In the U-Net model, specifically, it is important to resize each image in the set to a minimum size (512 × 512 pixels) to reduce the calculation time of the training process, unlike other models [36].


> **Figure 4. Resizing of objects from the image set to 640 × 640 pixels and 512 × 512 pixels.**

2.3.3. Application of the Data Augmentation Technique

Data augmentation was performed to increase the number of images in the dataset. The 793 original images collected with the UAV were multiplied using augmentation operations, such as rotation, saturation, and noise (Figure 5). Images were flipped, and rotated at a 90◦angle clockwise and counterclockwise, at 10◦and 15◦angles, saturation was changed at 10%, and a blur of 2.5% was applied, with a noise of 1.01%.

Images from the initial dataset were expanded to increase the set size and avoid over- fitting. Overfitting occurs when the neural network overfits the training data, memorizing the data instead of learning its pattern. When this happens, the network starts to make mistakes more frequently when exposed to other situations [36]. The pre-processing and data augmentation techniques were used to ensure a more expressive amount of training data for the deep machine learning algorithms. Through the transformations made to the original images, the total number of images in the dataset increased from 793 to 3021 images, randomly divided into test, validation, and training sets (Table 3).

Remote Sens. 2024, 16, 4394 8 of 23


> **Figure 5. Implementation of image set augmentation.**


> **Table 3. Dataset after splitting, resizing, and enlarging images.**

Number of

Number of Images After Augmentation

Number of Images After Preprocessing

Pixels Resize (Stretch)

Number of

Images Collected by

Training Validation Testing

Classes

UAV

793 1886 4000 × 3000 640 × 640/ 512 × 512 3 3021 2270 370 381

2.3.4. Generation of Dataset Masks

The dataset masks were generated from the original augmented images and used only for training the U-Net model. To correctly train the U-Net model, segmentation masks need to be generated from the dataset (Ronneberger [36], Wang et al. [37]). To generate the masks, an algorithm was developed in the Python programming language, using Visual Studio Code®, version 1.87.0. The algorithm developed went through each pixel of the images in the dataset, obtained the value of the RGB color channels of the current pixel, then checked whether each pixel was in the range of green tones, and subsequently assigned the value of the pixel in the extracted image with white color. The masks generated to train the U-Net model were saved in the output folder with the same name and dimension as the original image. Lastly, the masks were divided into three parts for training, validation, and testing in the U-Net model. The result of mask generation is shown in Figure 6.

Remote Sens. 2024, 16, 4394 9 of 23


> **Figure 6. RGB images (512 × 512) labeled for mask creation from annotated and resized RGB images**

> (a) and final mask created (b). The white color represents the weeds, and the black color represents
the absence of weeds in the image.

The pseudocode of mask-generation from the images in the dataset is represented in Algorithm 1, generated using the Overleaf [47] website. The description of how the mask-generation algorithm works is described here: (1) the output folder is checked and if it does not exist, it is created to ensure that the processed files can be saved; (2) all the files in the input folder are listed so that the program can iterate over them; (3) for processing each image, the program defines the full file path, loads the image using a read function, and verifies that the image was loaded correctly; (4) if the image is not loaded, it displays an error message and moves to the next file; (5) it then creates a copy of the image to store only the white tones; (6) to change tones from green to white, each pixel of the image is examined, and the color values in the BGR channels are obtained; (7) right away, it checks whether the pixel is predominantly green, comparing the value of the green channel with the blue and red channels; (8) if the pixel is green, it assigns the white value to the pixel in the extracted image, and otherwise, it assigns black; (9) at the end, the processed image is saved in the output folder with the same original name.

Remote Sens. 2024, 16, 4394 10 of 23

Algorithm 1: Set Pixel to White in Images (Generate Mask)

Input: input folder: Path to the folder containing input images

output folder: Path to the folder for saving processed images

Output: Processed images in output folder with only white

tones  Preserved.  Data: image files: List of files in input folder  input path, output path: Paths for input and output files


## 1   Function extract green colors(input folder, output folder):

// Verify if the output folder exists, and create it if not

2  if output folder does not exist then

3  CREATE output folder

// List all files in the input folder

4  image files = list of files in input folder

5  foreach file name in image files do     // Define the full path to the input file

6  input path = input folder + file name

// Load the image from input path

7  image = load image(input path)

// Check if the image was loaded successfully

8  if image is None then

9  DISPLAY ”Error loading image”, file name

10  continue to the next file

// Create a copy of the image to store white tones only

11  extracted image = copy of image

12  foreach row in range (0 to image.height) do

13  foreach col in range (0 to image.width) do

// Get BGR color values of the current pixel

14  blue, green, red = image[row, col]

// Check if the pixel is in the green range

15  if green > blue AND green > red then

16  extracted image[row, col] = (255, 255, 255)

//  Set  pixel  to  white  in  extracted  image

17  else

18  extracted image[row, col] = (0, 0, 0)

//  Set  pixel  to  black  in  extracted  image

// Define the output path for saving the processed image

19  output path = output folder + file name

// Save the extracted image in the output folder

20  SAVE extracted image TO output path

21  DISPLAY ”Image”, file name, ”processed and

saved successfully!”

2.4. Models 2.4.1. You Only Look Once (YOLO)

The latest version of the YOLO (You Only Look Once) machine learning model (Ultra- lytics), YOLOv8 [33], was used for weed detection and segmentation in this study. During the training process, the YOLOv8 model focuses, firstly, on detecting the objects contained in the images, previously labeled, and delimiting the found object using bounding boxes (B). Then, the model generates segmentation masks (M) for each delimited object, outlining the object and revealing its shape in the image. Figure 7 presents the network structure of the YOLOv8 model, describing the parameters used to represent the total size of the feature map that makes up this model.

Remote Sens. 2024, 16, 4394 11 of 23


> **Figure 7. Network structure of the YOLOv8 model.**

Before each training of the dataset on the YOLOv8 model, a version of the dataset was generated using the Roboflow tool. The hosted dataset was loaded directly into the Google Colab notebook to facilitate training. Tuning of the YOLOv8 model hyperparameters was performed before training. The images were used as input objects for the model, which then traversed the set of images once to segment weeds in the images.

The YOLOv8 model used the modified backbone network, CSPDarkNet53 [34]. The input features are sampled five times to obtain five different scale features (Algorithm 1). The five variants of this model, which ranged from nano-scale models (YOLOv8n) to extra- large models (YOLOv8x) [34], were trained and compared with each other. At the end of all training, the model was validated and saved.

2.4.2. Detectron2


> **Figure 8 shows the architecture of the Mask R-CNN model, in the Detectron2 frame-**

> work. The backbone network is responsible for extracting image features from the in-
put. This network consists of hierarchically organized layers, capable of gradually reduc-
ing the spatial dimensions of feature maps by increasing the number of channels in the
model [33,48].


> **Figure 8. Detectron2 architecture of the Mask R-CNN model.**

Before using the dataset to train the Mask R-CNN model in the Detectron2 framework, the Python environment was configured and the versions of the libraries necessary for the process were installed. Then, the instance segmentation dataset was selected, in the “COCO Segmentation” format, using the Roboflow tool. The hyperparameter adjustment

of the Mask R-CNN model in the Detectron2 framework was performed before training, and the images were used as input objects for the model. The three models selected for this study based on the structure shown are R101-FPN, X101-FPN, and R101-DC5. At the end of all training, the generated trained model was validated and saved.

Remote Sens. 2024, 16, 4394 12 of 23

2.4.3. U-Net

The U-Net model, proposed by Ronneberger, Fisher, and Brox [36], was trained with the soybean and bean dataset. In Figure 9, it is possible to see a representation of the architecture of the U-Net model. The hyperparameters of the U-Net model were tuned before training, and the images were used as input objects for the model. The U-Net model, based on FCN, captured the image context with spatial properties being extracted from the image and used to generate a segmentation map in the decoder. The decoder was used to enable accurate object localization in the image using transposed convolutions [31,42]. The encoder, composed of successive layers, increased the output resolution [41]. At the end of all training, the generated trained model was validated and saved.


> **Figure 9. Architecture of the U-Net model.**

2.5. Models and Parameters

Training and testing of all models in this study were carried out in Google Colaboratory using an NVIDIA graphics processor Google Compute Engine Tesla T4 in Python 3. The software and hardware environment parameters used are described in Table 4. The models YOLO were trained with weights from the MS COCO dataset, as shown in Table 5.

Tables 6 and 7 present the different parameters used for training the Mask R-CNN models in the Detectron2 framework and U-Net. The Mask R-CNN instance segmentation model with Detectron2 used three different backbones for the comparison, including R101-DC5, R101-FPN, and X101-FPN, and the U-Net model used ResNet50.


> **Table 4. Software and hardware environment parameters.**

Name Parameters/Version

Operating System Windows 10 CPU 1 AMD Ryzen 7 6800H GPU 2 NVIDIA Tesla T4 RAM 3 16 GB (8GB × 2) Python V3.12 Pytorch V2.1 OpenCV 4 V4.9.0 CUDA 5 V12.2

1 Central processing unit (CPU), 2 graphic processing units (GPU), 3 random access memory (RAM), 4 Open-source computer vision libraries (OpenCV), and 5 compute unified device architecture (CUDA).

Remote Sens. 2024, 16, 4394 13 of 23


> **Table 5. Parameters used for training instance segmentation models, such as YOLOv8, YOLOv7,**

> and YOLOv5.

Parameters Values

Optimizer SGD 1

Learning rate SGD = 1 × 10–2

Optimizer momentum 0.937 Base weight decay 0.0005 Batch size per Image 16 Annotation format Pytorch TXT Pretrained MS COCO Dataset 2

Image Format PNG

1 Stochastic gradient descent (SGD), 2 Microsoft COCO dataset (MS COCO Dataset).


> **Table 6. Hyperparameters are used for training the Detectron2 instance segmentation model.**

Parameters Values

mask_rcnn_R_101_DC5_3x mask_rcnn_R_101_FPN_3x mask_rcnn_X_101_32x8d_FPN_3x Max Iteration 20,000 Evaluate Period 200 Learning Rate 0.001 Number of Classes (Class + 1) 4 Batch Size per Image 64 Annotation format COCO Image Format PNG


## Architectures


> **Table 7. Hyperparameters are used for training the U-Net instance segmentation model.**

Parameters Values


## Architecture

ResNet50
Optimizer
SGD
Learning Rate
SGD = 1 × 10–2

Batch Size per Image 4 Number of Classes 3 Image Format TIFF

2.6. Validation Metrics Model Performance Calculations

To validate the performance of the instance segmentation algorithms and their vari- ations, evaluation metrics were used to calculate the performance and generalization capacity of deep learning models, following the studies of Gallo et al. [32], Butt et al. [33], Lin et al. [35], Pan et al. [39], and Jaccard et al. [49]. Among the evaluation metrics used in this study, the following stand out: mean average precision (mAP), precision (p), recall (R), accuracy (Acc), F-beta score (F1-Score), average precision (AP), and IoU (intersection over union). Mean average precision (mAP) evaluation metrics were used and were de- termined by Precision (P) (Equation (1)), to measure the precision of the model, and recall (R) (Equation (2)), to recognize the categories of objects contained in it and their known positions [32,33].

Precision = TP TP+FP (1)

Recall = TP TP+FN (2)

where the true positive (TP) represents the correct detection of a weed with the bounding box. The false negative (FN) represents a weed that was not detected in the image, and the false positive (FP) indicates that the location of a bounding box was detected, but without having a weed in it.

Remote Sens. 2024, 16, 4394 14 of 23

The accuracy of weed detection predictions was measured indicating the number of correctly detected objects divided by all detected objects. To calculate recall, the number of correctly detected objects was divided by all objects in the ground truth. Accuracy was evaluated based on the proportion between correctly predicted observations and all observations in the dataset, which was calculated from a performance metric (Equation (3)), which describes the mathematical expression for the proper calculation [30,32].

Acc (accuracy) = (TP + TN) (TP + TN + FP + FN) (3)

where true negatives (TNs) represent the incorrect detection of a weed, with its bound- ing box.

Equation (4) describes the F-beta score, used in the weighted harmonic mean of precision and recall, for which the value varies between 0 and 1, with 1 being the best value and 0 being the worst value. The beta weight is assigned according to the scenario in which it is found, that is, for beta equal to 1 (default value), Equation (4) [31,33] is used.

F1 = 2 × Precision × Recall

Precision+Recall (4)

Average precision (AP) calculates the area under the precision and recall curve, ac- cording to Equation (5). The IoU metric (Equation (7)), also known as the Jaccard Index, was used to evaluate the accuracy of object segmentation and detection models. The IoU metric ranges from 0 to 1, where 0 indicates no overlap and 1 indicates a perfect match [49].

n–1





∑ k=0

(Recall (n)– Recall(n+1)) × Precisions(k)

AP =

(5)

IoU = (Object ∩Detected box)

(Object ∪Detected box) (6)

For the calculation of average precision (mAP), used to calculate the arithmetic mean of each list of results returned by the model, Equation (7) describes the calculation of mAP [33,39]. The concept of K-precision used in the mAP calculation means K-class average precision. It evaluates whether the predicted items are relevant and if the most relevant items are at the top. The number of correctly labeled predicted labels is calculated, where K represents the K quantity of top labels considered across the entire dataset [32,33,39].

∑n

 



k=1 APk

mAP =

n (7)

Two different thresholds were used for object detection for the mean AP, with confidence values varying between 0 and 50% (mAP0.5) and between 0.50 and 0.95 (mAP0.5:0.95) [39]. To evaluate performance, metrics AP0.5 and AP0.75 were also used, with an average precision of 50 and 75%, and APl (large), which calculates precision at different recovery values for objects with large sizes (area > 962), with a focus on evaluating the model’s performance when detecting larger objects in the dataset (Butt et al. [33]).


## 3. Results

The four instance segmentation models trained on the custom dataset included YOLOv8 and its variants YOLOv7, YOLOv5, U-Net, and Mask R-CNN (Detectron2 frame- work) on three different backbones of the latter model based on the feature network architecture in pyramid (R101-FPN, R101-DC5, and X101-FPN) using the Detectron2 frame- work. An augmented dataset of 3021 images was used to train the models. Validation metrics were used, and performance comparisons of different backbones and variants, at different times, were made.

Remote Sens. 2024, 16, 4394 15 of 23

3.1. Performance of Different Backbones and Model Variants


> **Table 8 presents the performance of five variants of the YOLOv8 model in detecting**

> and segmenting three classes (weed, bean, and soybean) and the precision, recall, and mAP
score metrics for two different thresholds (50 and 50-95). Each variant of the model indicates
the size of its architecture, being nano (YOLOv8n), small (YOLOv8s), medium (YOLOv8m),
and large (YOLOv8l). The YOLOv8s variant presented the highest accuracy value of 99.7%
among the other variants. Furthermore, the YOLOv8l and YOLOv8m variants of the YOLO
model presented mAP values of 97% for the two different limits predicted by the model (50
and 50-95), obtaining an average training accuracy higher than the other variants of the
model when trained on 500 epochs.


> **Table 8. Precision, recall, and mAP scores of YOLOv8 variants, trained for 500 epochs. The highest**

> results are highlighted in bold.

Model Precision Recall mAP0.5 (M) 1 mAP 2 0.5:0.95 (M)

YOLOv8n 0.991 0.989 0.959 0.956 YOLOv8s 0.997 0.990 0.970 0.968 YOLOv8m 0.994 0.991 0.974 0.972 YOLOv8l 0.993 0.990 0.974 0.972


## 1 Mask (M), 2 mean average precision (mAP).

Tables 9 and 10 show the precision, accuracy, F1 score, and mAP values of different versions of the YOLO model. All variants of the YOLO model presented accuracy above 90%; however, the variant that stands out in terms of accuracy value among all versions of the model is YOLOv8s, with a value above 99%.


> **Table 9. Precision, recall, and mAP scores of YOLOv8s, YOLOv7, and YOLOv5s models over**

> 500 epochs. The highest results are highlighted in bold.

Model Backbone Precision Recall mAP0.5 (M) mAP0.5 (B) 1 mAP0.5:0.95 (M) mAP0.5:0.95 (B)

YOLOv8s CSPDarkNet53 0.997 0.990 0.970 0.970 0.968 0.965 YOLOv7 CSPDarkNet53 0.983 0.981 0.954 0.954 0.946 0.944 YOLOv5s CSPDarkNet53 0.968 0.954 0.945 0.929 0.934 0.904


## 1 Bounding box (B).


> **Table 10. Accuracy scores, mAP, and F1-score of the YOLOv8s, YOLOv7, and YOLOv5s models over**

> 500 epochs. The highest results are highlighted in bold.

Model Backbone Acc_weed 1 mAP_weed mAP Score F1-Score

YOLOv8s CSPDarkNet53 0.980 0.987 0.985 0.964 YOLOv7 CSPDarkNet53 0.990 0.990 0.988 0.951 YOLOv5s CSPDarkNet53 0.980 0.987 0.991 0.960


## 1 Accuracy (Acc).

3.2. Performance of Different Training Epochs and Iterations

The accuracy, F1 score, and mAP results of different versions of the YOLO model at different training epochs are presented in Tables 11 and 12. Variations in model accuracy re- sults concern the proportion between correctly predicted observations and all observations. In general, all versions of the YOLO model showed accuracy above 90%. However, the comparison between the YOLO models showed that the YOLOv8s and YOLOv7 variants presented higher accuracy in weed segmentation, between 100 and 500 epochs with values above 95% compared to YOLOv5s. Furthermore, within the versions of the YOLO model, YOLOv7 stood out with mAP and F1 values above 95% in 300 and 700 epochs.

Remote Sens. 2024, 16, 4394 16 of 23


> **Table 11. Accuracy scores, mAP, and F1-Score of YOLOv8s, YOLOv7, and YOLOv5s models were**

> trained at different times. The highest results are highlighted in bold.

YOLOv8s YOLOv7 YOLOv5s

Number of Epochs

Acc mAP0.5 (M) F1-Score 1 Acc mAP0.5 (M) F1-Score Acc mAP0.5 (M) F1-Score

100 0.943 0.933 0.956 0.930 0.890 0.950 0.877 0.816 0.910 300 0.950 0.956 0.961 0.937 0.933 0.953 0.940 0.904 0.965 500 0.957 0.970 0.964 0.950 0.954 0.951 0.943 0.930 0.960 700 0.940 0.973 0.962 0.952 0.984 0.982 0.930 0.945 0.952


## 1 F-beta score (F1-score).


> **Table 12. Accuracy and precision scores of YOLOv8s, YOLOv7, and YOLOv5s models at different**

> epochs. The highest results are highlighted in bold.

YOLOv8s YOLOv7 YOLOv5s

Number of

Epochs

Acc_weed Precision Acc_weed Precision Acc_weed Precision

100 1.000 0.990 0.990 0.992 0.980 0.958 300 0.970 0.998 0.990 0.994 0.980 0.981 500 0.980 0.997 0.990 0.983 0.980 0.968 700 0.990 0.995 0.989 0.982 0.990 0.970

The AP scores for the different backbones of the Mask R-CNN (Detectron2) model are presented in Tables 13 and 14. Table 13 presents the AP scores and accuracy in different iter- ations for each backbone of the Mask R-CNN (Detectron2) model. The X101-FPN backbone showed an average accuracy and precision of 99%. Table 14 presents the AP and AR scores of the Detectron2 model with different backbones for the cases in which the maximum iteration was chosen. Variations in AP summarize the precision and recall capabilities of models at different IoU thresholds. These metrics can provide an understanding of the model’s ability to identify and segment weeds in crops. Given this, the R101-DC5 backbone of the Mask-RCNN model proved to have a greater capacity to detect weeds in 20,000 model iterations, when compared to the other backbones tested, with an average accuracy above 93%.


> **Table 13. Acc and AP scores of the Mask R-CNN model with Detectron2 on different backbones. The**

> highest values are in bold.

R101-FPN X101-FPN R101-DC5

Number

Acc Box AP_weed 1

Mask AP_weed Acc Box AP_weed

Mask AP_weed Acc Box AP_weed

Mask AP_weed

of Iters

5000 0.986 0.993 0.890 0.987 0.992 0.897 0.989 0.986 0.892 20000 0.988 0.977 0.888 0.991 0.995 0.914 0.989 0.995 0.906


## 1 Average precision (AP).


> **Table 14. AP scores of Mask R-CNN model with Detectron2 on different backbones. The highest**

> values are in bold.

Model Backbone Max Iteration/

Epoch AP IoU 1 = 0.50:0.95 AP50 AP75 APl 2

Mask R-CNN R101-FPN 20000 0.911 0.944 0.941 0.911 Mask R-CNN X101-FPN 20000 0.924 0.953 0.949 0.924 Mask R-CNN R101-DC5 20000 0.933 0.965 0.960 0.932


## 1 Intersection of union (IoU), 2 average precision large (APl).

Remote Sens. 2024, 16, 4394 17 of 23

The results for accuracy and loss values in the training and validation stages of the U-Net model showed an increase in accuracy and a decrease in loss as the number of epochs increase (Table 15). The highest Acc and lowest loss values were observed when using 100 different epochs. The training set accuracy was 97.1%, with a loss value of 0.024, while for validation, the accuracy was 96.1%, with a loss value of 0.033.


> **Table 15. Accuracy scores, training loss, and validation of the U-Net model at different epochs. The**

> highest results are highlighted in bold.

Model Number of

Epochs Train Acc Train Loss Valid Acc Valid Loss

U-Net 30 0.967 0.047 0.958 0.051 U-Net 50 0.968 0.040 0.958 0.047 U-Net 80 0.968 0.042 0.960 0.049 U-Net 100 0.971 0.024 0.961 0.033

The comparison between the predictions made and the ground truth masks of all evaluated models and their variants is shown in Figure 10. In this sense, it can be observed that the predictions made by the trained DL algorithms were accurate in their ability to detect each object delimited in the image.

(a)  (b)


> **Figure 10. Comparison of predicted and ground truth segmentation masks between instance seg-**

> mentation algorithms and their variants: (a) YOLOv8s, YOLOv7, and YOLOv5s; (b) Mask R-CNN
(Detectron2) and its different backbones.

The results showed the difference in performance between the YOLO and Mask R- CNN (Detectron2), showing that the precision and accuracy of all models evaluated varied between 94% and 99% (Figure 11). The YOLOv8s variant showed greater accuracy com- pared to other versions of the YOLO model, considering the correct plant prediction made by the model for all samples in the dataset. However, the YOLOv8m and YOLOv8l variants presented mAP50 and mAP50-95 of 97.4% and 97.2%, respectively. The highest performing backbone was R101-DC5, in the Mask R-CNN model (Detectron2), with an AP50 score of 96.5% and AP IoU (0.50–0.95) of 93.3%, when compared to the other backbones trained.

Remote Sens. 2024, 16, 4394 18 of 23

(a)  (b)


> **Figure 11. Training results for the instance segmentation models: (a) YOLOv8s, YOLOv7, and**

> YOLOv5s in 500 epochs; (b) Mask R-CNN (Detectron2) and its variants in 20,000 iterations.

The difference in accuracy, AP (50 and 50-95), and recall scores between the instance segmentation algorithms on different backbones at different times and interactions showed a higher performance of the YOLOv8s and Mask R-CNN with the R101-DC5 backbone (Table 16). The YOLOv8s had a mAP50 value of 97% and a recall of 99%. The 99% recall value describes the ability of the YOLOv8s model to find all relevant cases within the set, being the number of cases of correct weed predictions for all cases of real plants, and refers to the number of measurements that the model predicted correctly and that will be considered in the relevant total predictions [33,38]. The Mask R-CNN with R101-DC5 backbone had an mAP50 value of 96.5% and a recall value of 96.4%.


> **Table 16. Accuracy, AP, and recall scores for all models and their variants. The highest results are**

> highlighted in bold.

Models Backbone Max Iteration/

Epoch Acc AP0.5:0.95/mAP

0.5:0.95 AP0.5/mAP0.5 AR 1/Recall

Mask R-CNN R101-FPN 20000 0.980 0.911 0.944 0.948 Mask R-CNN X101-FPN 20000 0.989 0.924 0.953 0.924 Mask R-CNN R101-DC5 20000 0.991 0.933 0.965 0.964 YOLOv8s CSPDarkNet53 500 0.957 0.965 0.970 0.990 YOLOv7 CSPDarkNet53 500 0.950 0.944 0.954 0.981 YOLOv5s CSPDarkNet53 500 0.943 0.904 0.945 0.954 U-Net ResNet50 100 0.971 - - -


## 1 Average recall (AR).

The comparison between the models demonstrated that YOLOv8s performed signifi- cantly better than Mask R-CNN (Detectron2) and U-Net in three of the four performance metrics. Therefore, the YOLOv8 model and its variants presented the highest mAP and recall results, as well as the highest accuracy results.


## 4. Discussion

To annotate the objects in the dataset images in the Roboflow [45] application interface, the polygonal formats of the bounding boxes were used due to the curved and diagonal shapes of the classes present, such as weed plants, bean plants, and soybean plants [50,51]. The precise annotation of objects and the increased dataset proved important in achieving satisfactory results for this study. In the testing phases of DL models, it became evident

Remote Sens. 2024, 16, 4394 19 of 23

that the use of polygons for object labeling proved to be effective when segmenting weeds among commercial crops [52–54].

4.1. Performance of Different Backbones and Model Variants

The results demonstrated in the previous section showed the difference between the performance of YOLO, Mask R-CNN (Detectron2), and U-Net DL models. The YOLOv8s and YOLOv8m variants obtained the best results and, notably, identified and located objects within the images with greater accuracy. Accuracy is relevant when the number of false positives is close to the number of false negatives and the dataset is symmetric [33,34]. If the dataset is asymmetric, it is necessary to resort to other performance metrics, as considering a better model based solely on accuracy is incorrect, as described by Butt et al. [33]. The higher performance of the YOLOv8 model variants (YOLOv8s and YOLOv8m) may be associated with a newer and more efficient backbone network (CSPDarkNet53) and its ability to use larger feature maps that filter and aggregate complex relationships between features and recognize patterns and objects [33]. This variant of the YOLOv8 model (YOLOv8s) has a higher average precision index (mAP) compared to the other variants. Furthermore, the time taken for the YOLOv8s model to detect and segment weeds in the set of images is less than the time taken for the other variants to make the same inferences [14,30,33]. Furthermore, the YOLOv8 model can detect objects by dividing the image into a grid of equal dimensions, which is capable of locating objects in the center of the grid [34]. Thus, each grid can predict some bounding boxes, resulting in the selection of more representative boxes according to a study by Sportelli [55]. One potential reason why the YOLO model has the ability to localize an image with high precision, especially the YOLOv8, is the non-maximum suppression methods (NMSs) that are used in its architecture to perform this task [54,55].

The performance results of the YOLOv8 model and its variants were compared with the YOLOv7 and YOLOv5 models in the studies by Guo et al. [30] and Gallo et al. [32] for different periods, in a similar way. It was observed that the increase in the number of training epochs may interfere with the ability and performance of previous versions of the YOLO model to recognize the patterns of objects in the set. As a result, it may interfere with the response time to detect and segment objects in real-time, as seen by Feng et al. [14], Gallo et al. [32], and Butt et al. [33].

Unlike YOLOv8, the YOLOv5s model had the worst performance when compared to the most recent version of YOLO and the other models. This is because, according to Nnadozie et al. [50], YOLOv5s performs well in training efficiency and presents high precision in cases where there is the presence of weeds in the crop, but this version also presents low inference velocity in detecting objects in complex scenarios, when compared to other variants of this version.

4.2. Performance of Different Training Epochs

The YOLOv8s model showed superior accuracy when compared to previous versions (YOLOv7 and YOLOv5s) at 500 and 700 epochs, considering the most recent backbone network (CSPDarkNet53). The YOLOv7 and YOLOv5s models demonstrated performance with superior detection quality to the most recent version of the YOLO model (YOLOv8s) only in 700 training epochs. However, studies that have improved the YOLOv5s capacity by employing a convolutional block attention module (CBAM) to the model to extract features in the image can achieve an average precision above 90% and superior recall up to 85% in real-time field detection, obtaining greater performance in detection quality [56–58]. The Mask R-CNN algorithm R101-DC5 backbone (Detectron2) proved to be superior in training efficiency, when detecting instances in 20,000 iterations, to the YOLOv5s and YOLOv7 models and the other backbones of this model. The Mask R-CNN model achieved even greater accuracy in detection quality when compared to the U-Net model. This occurs because the accuracy in detection quality of Mask R-CNN can be associated with implementing the pyramid feature network (FPN) in the Detectron2 framework, which

Remote Sens. 2024, 16, 4394 20 of 23

allows the detection of objects and scales within the image [43]. Thus, the Mask R-CNN algorithm may be able to combine feature maps of different scales, making it possible to detect objects of different sizes in the image, which can contribute to increasing the number of objects detected in the image and, consequently, the detection quality [35]. Ajayi et al. [28] presented similar results in a study when training a convolutional neural network (CNN) to detect and classify weeds in mixed agricultural crops.

The Mask R-CNN (R101-DC5 backbone) and U-Net (ResNet50 backbone) models proved to be superior in detection quality by presenting higher accuracy than YOLOv8s and other models. However, the mAP scores of the YOLOv8 model were higher than Mask R-CNN, and this may be associated with the recent backbone present in the latest version of the YOLO model, in which the algorithm uses a layer called the fast spatial pyramid pooling module (SPPF) capable of grouping features of different scales into a fixed-size feature map to accelerate processing [33].

The YOLOv8 single-shot model and its variations managed to outperform the Mask R-CNN double-shot model, as well as the U-Net model, in average detection and seg- mentation accuracy. Furthermore, recent studies have shown that when comparing the performance of single-class and multi-class instance segmentation models, YOLOv8 and Mask R-CNN, using large image sets, YOLOv8 achieved better performance with over 92% precision and recall of 97% when detecting objects [57,58]. This is because one of the features of the DarkNet-53 architecture of the YOLOv8 model is its 53-layer-deep and optimized convolutional neural network (CSPDarkNet53) for extracting multi-objects in images. This significant difference in architecture, when compared to other YOLO versions and other learning models, makes the processing of the eighth version faster and with greater detection accuracy, given the replacement of the C3 module by the improved C2F version, making this model computationally efficient [58–63].

In 100 epochs, the U-Net model showed higher accuracy scores in both the training phase and the model validation phase, when compared to the YOLO model (in versions 5 and 7) in 500 epochs. In 100 epochs, the U-Net model showed higher accuracy scores in both the training phase and the model validation phase, when compared to the YOLO model, in 500 epochs. In other words, the U-Net model achieved higher accuracy than the YOLOv5 and YOLOv7 models, in fewer training epochs and, additionally, the U-Net model presented the lowest data loss score in training compared to the other epochs. The training loss implies model behavior after each epoch (i.e., the smaller the loss, the better the model) as described by Arab et al. [12]. Nasiri et al. [31] found similar results when training a U-Net model with ResNet50 for weed recognition in sugar beet and obtained an accuracy score of 96%. The metrics used to evaluate the U-Net model in this study were sufficient to validate the model with good results. Other metrics to evaluate the performance of the U-Net model could be considered (e.g., Dice-Sørensen coefficient, Kappa coefficient) [12,31,61,63]; however, the metrics evaluated in this study presented sufficient and consistent results. As the U-Net model is a recent model and its architecture is aimed at applications in the medical field, there is no significant support in the literature from authors who used this model for automatic analysis in agriculture [61].

The U-Net model, when improved and trained in 100 epochs to detect and segment weeds presented an F1 score coefficient and intersection over union (IoU) of 90% and 82%, respectively, according to the study by Habib et al. [61]. This is because this model is mainly based on the U-Net architecture, which has a symmetric encoder (expansion) and decoder (contraction), a fully convolutional network (FCN), and a feature for image dimension reduction (MaxPooling) for small spatial changes about the original image [63].


## 5. Conclusions

The variant YOLOv8s of the YOLOv8 models had the highest mAP and recall per- formance, showing a greater training efficiency compared to the other DL models. The YOLOv8m variant had the highest mAP and recall performance when compared to other

Remote Sens. 2024, 16, 4394 21 of 23

YOLOv8 model variants. The lowest performance was provided by YOLOv5, depending on the mAP value, when compared to the other models.

The Mask R-CNN (R101-DC5 backbone) and U-Net (ResNet50) models also showed quality when detecting and segmenting objects across the training epochs when compared to the YOLOv5s and YOLOv7 models. Compared to the YOLOv8 model, it achieved greater accuracy in detecting and segmenting multi-objects in the set, when compared to other learning models and previous versions of YOLO, given its recent DarkNet-53 architecture.

Data obtained in this study demonstrated that deep learning models and advanced object segmentation algorithms can generate efficient results for automatic weed detection in high-resolution RGB image databases captured by a UAV when trained with a well- labeled and augmented dataset.

Author Contributions: Conceptualization, J.A.O.S.S. and H.F.E.d.O.; methodology, J.A.O.S.S., H.F.E.d.O., J.L.B.d.S., M.V.d.S., L.N.L., M.M. and V.S.d.S.; software, J.A.O.S.S.; validation, J.A.O.S.S., H.F.E.d.O., L.N.L., M.M. and J.L.B.d.S.; formal analysis, J.A.O.S.S., V.S.d.S., T.d.N.B.M., L.S.R.V., J.L.M.P.d.L., J.F.d.O.-J., L.N.L., M.M., H.F.E.d.O., J.L.B.d.S. and M.V.d.S.; investigation, J.A.O.S.S., H.F.E.d.O., J.L.B.d.S., M.V.d.S., M.M. and V.S.d.S.; resources, J.A.O.S.S., H.F.E.d.O. and J.L.B.d.S.; data curation, J.A.O.S.S., H.F.E.d.O. and L.N.L.; writing—original draft preparation, J.A.O.S.S.; writing—review and editing, J.A.O.S.S., M.M., H.F.E.d.O., T.d.N.B.M., V.S.d.S., J.L.M.P.d.L., J.F.d.O.-J., J.L.B.d.S., M.V.d.S., L.N.L. and L.S.R.V.; visualization, J.A.O.S.S., H.F.E.d.O., L.S.R.V., J.L.B.d.S., J.L.M.P.d.L., T.d.N.B.M., J.F.d.O.-J., M.M., M.V.d.S., L.N.L. and V.S.d.S.; supervision, H.F.E.d.O.; project administra- tion, H.F.E.d.O.; funding acquisition, H.F.E.d.O., J.L.M.P.d.L., J.F.d.O.-J. and M.V.d.S. All authors have read and agreed to the published version of the manuscript.

Funding: This research was funded by the National Council for Scientific and Technological De- velopment (CNPq), under processes 407465/2021-9 and 420296/2023-9; the Foundation for Re- search Support of the State of Goiás (FAPEG); Embrapa Rice and Beans; the University of Georgia; ACIV—Associação para o Desenvolvimento da Engenharia Civil—Portugal; and internal funding from the Goiano Federal Institute—Campus Ceres.

Data Availability Statement: The datasets analyzed for this study can be found in the manuscript. Other data presented in this study are available on request from the first author.

Acknowledgments: We would like to thank the Cerrado Irrigation Graduate Program and the Laboratório de Tecnologias de Irrigação (Lab.TI) of the Goiano Federal Institute—Campus Ceres for the technical and technological support in conducting this research. All individuals included in this section have consented to the acknowledgement.

Conflicts of Interest: The authors declare that they have no known competing financial interests or personal relationships that could have appeared to influence the work reported in this paper.


## References

1. Ilniyaz, O.; Du, Q.; Shen, H.; He, W.; Feng, L.; Azadi, H.; Kurban, A.; Chen, X. Leaf area index estimation of pergola-trained vineyards in arid regions using classical and deep learning methods based on UAV-based RGB images. Comput. Electron. Agric. 2023, 207, 107723. [CrossRef] 2. Peng, M.; Han, W.; Li, C.; Yao, X.; Shao, G. Modeling the daytime net primary productivity of maize at the canopy scale based on UAV multispectral imagery and machine learning. J. Clean. Prod. 2022, 367, 133041. [CrossRef] 3. Barbosa, B.D.S.; Ferraz, G.A.E.S.; Costa, L.; Ampatzidis, Y.; Vijayakumar, V.; Santos, L.M.D. UAV-based coffee yield prediction utilizing feature selection and deep learning. Smart Agric. Technol. 2021, 1, 100010. [CrossRef] 4. Alabi, T.R.; Abebe, A.T.; Chigeza, G.; Fowobaje, K.R. Estimation of soybean grain yield from multispectral high-resolution UAV data with machine learning models in West Africa. Remote Sens. Appl. Soc. Environ. 2022, 27, 100782. [CrossRef] 5. Teshome, F.T.; Bayabil, H.K.; Hoogenboom, G.; Schaffer, B.; Singh, A.; Ampatzidis, Y. Unmanned aerial vehicle (UAV) imaging and machine learning applications for plant phenotyping. Comput. Electron. Agric. 2023, 212, 108064. [CrossRef] 6. Ariza-Sentís, M.; Valente, J.; Kooistra, L.; Kramer, H.; Mücher, S. Estimation of spinach (Spinacia oleracea) seed yield with 2D UAV data and deep learning. Smart Agric. Technol. 2022, 3, 100129. [CrossRef] 7. Niu, B.; Feng, Q.; Chen, B.; Ou, C.; Liu, Y.; Yang, J. HSI-TransUNet: A Segmentation Model semantics based in transformer for crop mapping from UAV hyperspectral images. Comput. Electron. Agric. 2022, 201, 107297. [CrossRef] 8. Pandey, A.; Jain, K. An intelligent system for crop identification and classification from UAV images using conjugated dense convolutional neural network. Comput. Electron. Agric. 2021, 192, 106543. [CrossRef]

Remote Sens. 2024, 16, 4394 22 of 23

9. Vong, N.; Conway, L.S.; Feng, A.; Zhou, J.; Kitchen, N.R.; Sudduth, K.A. Estimating and Mapping Corn Emergence Uniformity using UAV imagery and deep learning. Comput. Electron. Agric. 2022, 198, 107008. [CrossRef] 10. Chen, R.; Zhang, C.; Xu, B.; Zhu, Y.; Zhao, F.; Han, S.; Yang, G.; Yang, H. Predicting Individual Apple Yield using sensing data remote from multiple UAV sources and ensemble learning. Comput. Electron. Agric. 2022, 201, 107275. [CrossRef] 11. Sharma, N.; Sharma, R.; Jindal, N. Machine Learning and Deep Learning Applications-A Vision. Glob. Trans. Proceed. 2021, 2, 24–28. [CrossRef] 12. Arab, A.; Chinda, B.; Medvedev, G.; Siu, W.; Guo, H.; Gu, T.; Moreno, S.; Hamarneh, G.; Ester, M.; Song, X. A fast and fully- automated deep-learning approach for accurate hemorrhage segmentation and volume quantification in non-contrast whole-head CT. Sci. Rep. 2020, 10, 19389. [CrossRef] [PubMed] 13. Lopez-Granados, F.; Jurado-Exposito, M.; Peña-Barragan, J.M.; García-Torres, L. Using remote sensing for identification of late-season grass weed patches in wheat. Weed Sci. 2006, 54, 346–353. [CrossRef] 14. Feng, Y.; Chen, W.; Ma, Y.; Zhang, Z.; Gao, P.; Lv, X. Cotton Seedling Detection and Counting Based on UAV Multispectral Images and Deep Learning Methods. Remote Sens. 2023, 15, 2680. [CrossRef] 15. Tunca, E.; Köksal, E.S.; Özturk, E.; Akayc, H.; Taner, S.Ç. Accurate leaf area index estimation in sorghum using high-resolution UAV data and machine learning models. Phys. Chem. Earth Parts A/B/C 2024, 133, 103537. [CrossRef] 16. Genze, N.; Ajekwe, R.; Güreli, Z.; Haselbeck, F.; Grieb, M.; Grimm, D.G. Deep learning-based early weed segmentation using motion blurred UAV images of sorghum fields. Comput. Electron. Agric. 2022, 202, 107388. [CrossRef] 17. Mohidem, N.A.; Che’ya, N.N.; Juraimi, A.S.; Ilahi, W.F.F.; Roslim, M.H.M.; Sulaiman, N.; Saberioon, M.; Noor, N.M. How can unmanned aerial vehicles be used for detecting weeds in agricultural fields? Agriculture 2021, 11, 1004. [CrossRef] 18. Ma, J.; Liu, B.; Ji, L.; Zhu, Z.; Wu, Y.; Jiao, W. Field-scale yield prediction of winter wheat under different irrigation regimes based on the dynamic fusion of multimodal UAV imagery. Int. J. Appl. Earth Obs. Geoinf. 2023, 118, 103292. [CrossRef] 19. Liu, S.; Jin, X.; Bai, Y.; Wu, W.; Cui, N.; Cheng, M.; Liu, Y.; Meng, L.; Jia, X.; Nie, C.; et al. UAV multispectral images for accurate estimation of the maize LAI considering the effect of soil background. Int. J. Appl. Earth Obs. Geoinf. 2023, 121, 103383. [CrossRef] 20. Demir, S.; Dedeo˘glu, M.; Ba¸sayi˘git, L. Yield prediction models of organic oil rose farming with agricultural unmanned aerial vehicles (UAVs) images and machine learning algorithms. Remote Sens. Appl. Soc. Environ. 2023, 33, 101131. [CrossRef] 21. Jamali, M.; Bakhshandeh, E.; Yeganeh, B.; Özdo˘gan, M. Development of machine learning models for estimating wheat biophysical variables using satellite-based vegetation indices. Adv. Space Res. 2024, 73, 498–513. [CrossRef] 22. Qu, H.; Zheng, C.; Ji, H.; Barai, K.; Zhang, Y. A fast and efficient approach to estimate wild blueberry yield using machine learning with drone photography: Flight altitude, sampling method, and model effects. Comput. Electron. Agric. 2024, 216, 108543. [CrossRef] 23. Sivakumar, A.N.V.; Li, J.; Scott, S.; Psota, E.; Jhala, A.J.; Luck, J.D.; Shi, Y. Comparison of object detection and patch-based classification deep learning models on mid-to late-season weed detection in UAV imagery. Remote Sens. 2020, 12, 2136. [CrossRef] 24. Deng, J.; Zhang, X.; Yang, Z.; Zhou, C.; Wang, R.; Zhang, K.; Lv, X.; Yang, L.; Wang, Z.; Li, P.; et al. Pixel-level regression for UAV hyperspectral images: Deep learning-based quantitative inverse of wheat stripe rust disease index. Comput. Electron. Agric. 2023, 215, 108434. [CrossRef] 25. Casas, E.; Arbelo, M.; Moreno-Ruiz, J.A.; Hernández-Leal, P.A.; Reyes-Carlos, J.A. UAV-Based Disease Detection in Palm Groves of Phoenix canariensis Using Machine Learning and Multispectral Imagery. Remote Sens. 2023, 15, 3584. [CrossRef] 26. Somerville, G.J.; Sønderskov, M.; Mathiassen, S.K.; Metcalfe, H. Spatial Modelling of within-field weed populations; a review. Agronomy 2020, 10, 1044. [CrossRef] 27. Rahman, A.; Lu, Y.; Wang, H. Performance Evaluation of Deep Learning Object Detectors for Herbal Detection weeds for cotton. Smart Agric. Technol. 2022, 3, 100126. [CrossRef] 28. Ajayi, O.G.; Ashi, J.; Guda, B. Performance evaluation of YOLO v5 model for automatic crop and weed classification on UAV images. Smart Agric. Technol. 2023, 5, 100231. [CrossRef] 29. Wang, H.; Feng, J.; Yin, H. Improved Method for Apple Fruit Target Detection Based on YOLOv5s. Agriculture 2023, 2167. [CrossRef] 30. Guo, H.; Xiao, Y.; Li, M.; Hao, F.; Zhang, X.; Sun, H.; Beurs, K.; Fu, Y.H.; He, Y. Identifying crop phenology using maize height constructed from multi-sources images. Int. J. Appl. Earth Obs. Geoinf. 2022, 13, 115. [CrossRef] 31. Nasiri, A.; Omid, M.; Taheri-Garavand, A.; Jafari, A. Deep learning-based precision agriculture through weed recognition in sugar beet fields. Sustain. Comput. Inform. Syst. 2022, 35, 100759. [CrossRef] 32. Gallo, I.; Rehman, A.U.; Dehkord, R.H.; Landro, N.; La Grassa, R.; Boschetti, M. Deep Object Detection of Crop Weeds: Performance of YOLOv7 on a Real Case Dataset from UAV Images. Remote Sens. 2023, 15, 539. [CrossRef] 33. Butt, M.; Glas, N.; Monsuur, J.; Stoop, R.; de Keijzer, A. Application of YOLOv8 and Detectron2 for Bullet Hole Detection and Score Calculation from Shooting Cards. AI 2024, 5, 72–90. [CrossRef] 34. Redmon, J.; Divvala, S.; Girshick, R.; Farhadi, A. You Only Look Once: Unified, Real-Time Object Detection. In Proceedings of the 2016 IEEE Conference on Computer Vision and Pattern Recognition (CVPR), Las Vegas, NV, USA, 27–30 June 2016; pp. 779–788. 35. Lin, T.-Y.; Dollar, P.; Girshick, R.; He, K.; Hariharan, B.; Belongie, S. Feature Pyramid Networks for Object Detection. In Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition (CVPR), Honolulu, HI, USA, 21–26 July 2017.

Remote Sens. 2024, 16, 4394 23 of 23

36. Ronneberger, O.; Fischer, P.; Brox, T. U-Net: Convolutional Networks for Biomedical Image Segmentation. 2015. Computer Science Department and BIOSS Centre for Biological Signalling Studies, University of Freiburg, Germany. Available online: http://lmb.informatik.uni-freiburg.de/ (accessed on 2 March 2024). 37. Wang, J.; Lou, Y.; Wang, W.; Liu, S.; Zhang, H.; Hui, X.; Wang, Y.; Yan, H.; Maes, W.H. A robust model for diagnosing water stress of winter wheat by combining UAV multispectral and thermal remote sensing. Agric. Water Manag. 2024, 291, 108616. [CrossRef] 38. Girshick, R. Fast R-CNN. In Proceedings of the IEEE International Conference on Computer Vision (ICCV), Santiago, Chile, 7–13 December 2015; pp. 1440–1448. 39. Pan, Q.; Gao, M.; Wu, P.; Yan, J.; Li, S. A Deep-Learning-Based Approach for Wheat Yellow Rust Disease Recognition from Unmanned Aerial Vehicle Images. Sensors 2021, 21, 6540. [CrossRef] 40. Lin, T.-Y.; Goyal, P.; Girshick, R.; He, K.; Dollar, P. Focal Loss for Dense Object Detection. In Proceedings of the IEEE International Conference on Computer Vision, Venice, Italy, 22–29 October 2017; pp. 2980–2988. 41. Ramesh, N.; Tasdizen, T. Chapter 3—Detection and segmentation in microscopy images. Comput. Vis. Pattern Recognit. 2021, 43–71. [CrossRef] 42. Öztürk, ¸S.; Polat, K. Chapter 13—A novel polyp segmentation approach using U-net with saliency-like feature fusion. Intell. Data-Centric Syst. 2023, 251–269. [CrossRef] 43. Kattenborn, T.; Leitloff, J.; Schiefer, F.; Hinz, S. Review on Convolutional Neural Networks (CNN) in Vegetation Remote Sensing March. J. Photogramm. Remote Sens. 2021, 173, 24–49. [CrossRef] 44. dos Santos, H.G.; Jacomine, P.K.T.; dos Anjos, L.H.C.; de Oliveira, V.Á.; Lumbreras, J.F.; Coelho, M.R.; de Almeida, J.A.; Filho, J.C.d.A.; de Oliveira, J.B.; Cunha, T.J.F. Sistema Brasileiro de Classificação de Solos, 5th ed.; rev. e ampl. Embrapa DF: Embrapa: Brasília, Brazil, 2018. 45. Roboflow. Available online: https://roboflow.com/ (accessed on 1 March 2024). 46. BBCH English. Growth Stages of Mono-and Dicotyledonous Plants. BBCH Monograph. 2001, p. 158. Available online: https://www.reterurale.it/downloads/BBCH_engl_2001.pdf (accessed on 2 November 2024). 47. Overleaf. Overleaf, Online LaTex Editor. 2024. Available online: https://pt.overleaf.com/ (accessed on 4 November 2024). 48. Ju, R.Y.; Cai, W. Fracture Detection in Pediatric Wrist Trauma X-ray Images Using YOLOv8 Algorithm. arXiv 2023. [CrossRef] 49. Jaccard, P. The distribution of the flora in the alpine zone. 1. New Phytol. 1912, 11, 37–50. [CrossRef] 50. Nnadozie, E.C.; Iloanusi, O.N.; Ani, O.A.; Yu, K. Detecting Cassava Plants Under Different Field Conditions Using UAV-Based RGB Images and Deep Learning Models. Remote Sens. 2023, 15, 2322. [CrossRef] 51. Hafeez, A.; Husain, M.A.; Singh, S.P.; Chauhan, A.; Khan, M.T.; Kumar, N.; Chauhan, A.; Soni, S.K. Implementation of drone technology for farm monitoring & pesticide spraying: A review. Inf. Process. Agric. 2022, 10, 192–203. [CrossRef] 52. Robert, N. Colwell Determining the prevalence of certain cereal crop diseases by means of aerial photography. Hilgardia 1956, 26, 223–286. [CrossRef] 53. Cisternas, I.; Velasquez, I.; Caro, A.; Rodriguez, A. Systematic literature review of implementations of precision agriculture. Comput. Electron. Agric. 2020, 176, 105626. [CrossRef] 54. Wang, H.; Fapojuwo, A.O.; Davies, R.J. A wireless sensor network for feedlot animal health monitoring. IEEE Sens. J. 2016, 16, 6433–6446. [CrossRef] 55. Sportelli, M.; Apolo-Apolo, O.E.; Fontanelli, M.; Frasconi, C.; Raffaelli, M.; Peruzzi, A.; Perez-Ruiz, M. Evaluation of YOLO Object Detectors for Weed Detection in Different Turfgrass Scenarios. Appl. Sci. 2023, 13, 8502. [CrossRef] 56. Niu, W.; Lei, X.; Li, H.; Wu, H.; Hu, F.; Wen, X.; Zheng, D.; Song, H. YOLOv8-ECFS: A lightweight model for weed species detection in soybean fields. Crop Prot. 2024, 184, 106847. [CrossRef] 57. Reis, D.; Kupec, J.; Hong, J.; Daoudi, A. Real-Time Flying Object Detection with YOLOv8. arXiv 2023. [CrossRef] 58. Shao, Y.; Guan, X.; Xuan, G.; Gao, F.; Feng, W.; Gao, G.; Wang, Q.; Huang, X.; Li, J. GTCBS-YOLOv5s: A lightweight model for weed species identification in paddy fields. Comput. Eletron. Agric. 2023, 215, 108461. [CrossRef] 59. Sapkota, R.; Ahmed, D.; Karkee, M. Comparing YOLOv8 and Mask R-CNN for instance segmentation in complex orchard environments. Art. Intel. Agric. 2024, 13, 84–99. [CrossRef] 60. Amogi, B.R.; Ranjan, R.; Khot, L.R. Mask R-CNN aided fruit surface temperature monitoring algorithm with edge compute enabled internet of things system for automated apple heat stress management. Inform. Process. Agric. 2023, 10, 1–9. [CrossRef] 61. Habib, M.; Sekha, S.; Tannouche, A.; Ounejjar, Y. New segmentation approach for effective weed management in agriculture. Smart Agric. Technol. 2024, 8, 100505. [CrossRef] 62. Zunair, H.; Ben Hamza, A. Sharp U-Net: Depthwise convolutional network for biomedical image segmentation. Comput. Biol. Med. 2021, 136, 104699. [CrossRef] [PubMed] 63. Karim, M.J.; Nahiduzzaman, M.; Ahsan, M.; Haider, J. Development of an early detection and automatic targeting system for cotton weeds using an improved lightweight YOLOv8 architecture on an edge device. Knowl.-Based Sys. 2024, 300, 112204. [CrossRef]

Disclaimer/Publisher’s Note: The statements, opinions and data contained in all publications are solely those of the individual author(s) and contributor(s) and not of MDPI and/or the editor(s). MDPI and/or the editor(s) disclaim responsibility for any injury to people or property resulting from any ideas, methods, instructions or products referred to in the content.
