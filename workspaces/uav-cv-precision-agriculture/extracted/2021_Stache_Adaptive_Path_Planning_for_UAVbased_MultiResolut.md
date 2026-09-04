---
workspace_id: SCI-000002
title: Adaptive Path Planning for UAV-based Multi-Resolution Semantic Segmentation
authors:
- family_name: Stache
  given_name: Felix
  orcid: null
- family_name: Westheider
  given_name: Jonas
  orcid: null
- family_name: Magistri
  given_name: Federico
  orcid: null
- family_name: "Popovi\u0107"
  given_name: Marija
  orcid: null
- family_name: Stachniss
  given_name: Cyrill
  orcid: null
year: 2021
extraction_engine: pymupdf
extracted_at: '2026-09-04T01:48:53.102670+00:00'
---

# Adaptive Path Planning for UAV-based Multi-Resolution Semantic Segmentation

Adaptive Path Planning for UAV-based Multi-Resolution Semantic Segmentation

Felix Stache∗ Jonas Westheider∗ Federico Magistri Marija Popovi´c Cyrill Stachniss


## Abstract— In this paper, we address the problem of adaptive

path planning for accurate semantic segmentation of terrain
using unmanned aerial vehicles (UAVs). The usage of UAVs
for terrain monitoring and remote sensing is rapidly gaining
momentum due to their high mobility, low cost, and ﬂexible
deployment. However, a key challenge is planning missions to
maximize the value of acquired data in large environments given
ﬂight time limitations. To address this, we propose an online
planning algorithm which adapts the UAV paths to obtain high-
resolution semantic segmentations necessary in areas on the
terrain with ﬁne details as they are detected in incoming images.
This enables us to perform close inspections at low altitudes only
where required, without wasting energy on exhaustive mapping
at maximum resolution. A key feature of our approach is a
new accuracy model for deep learning-based architectures that
captures the relationship between UAV altitude and semantic
segmentation accuracy. We evaluate our approach on the
application of crop/weed segmentation in precision agriculture
using real-world ﬁeld data.

arXiv:2108.01884v1  [cs.RO]  4 Aug 2021

I. INTRODUCTION

Fig. 1: A comparison of our proposed adaptive path planning strategy (top-left) against lawn-mower coverage planning (top-right) for UAV-based ﬁeld segmentation, evaluated on the application of precision agriculture using real ﬁeld data (bottom). By allowing the paths to change online, our approach enables selecting high- resolution (low-altitude) imagery in areas with more semantic detail, enabling higher-accuracy, ﬁne-grained segmentation in these regions.

Unmanned aerial vehicles (UAVs) are experiencing a rapid uptake in a variety of aerial monitoring applications, includ- ing search and rescue [10], wildlife conservation [9], and precision agriculture [14], [15], [25]. They offer a ﬂexible and easy to execute a way to monitor areas from a top- down perspective. Recently, the advent of deep learning has unlocked their potential for image-based remote sensing, enabling ﬂexible, low-cost data collection and processing [3]. However, a key challenge is planning paths to efﬁciently gather the most useful data in large environments, while accounting for the constraints of physical platforms, e.g. on fuel/energy, as well as the on-board sensor properties.

in the target environment; mapping the entire area at a constant image spatial resolution governed by the altitude. Recent work has explored informative planning for terrain mapping, whereby the aim is to maximize an information- theoretic mapping objective subject to platform constraints. However, these studies either consider 2D planning at a ﬁxed altitude or apply simple heuristic predictive sensor models [14], [15], [10], which limits the applicability of future plans. A key challenge is reliably characterizing how the accuracy of segmented images varies with the altitude and relative scales of the objects in registered images.

This paper examines the problem of deep learning-based semantic segmentation using UAVs and the exploitation of this information in path planning. Our goal is to adaptively select the next sensing locations above a 2D terrain to maximize the classiﬁcation accuracy of objects or areas of interest seen in images, e.g. animals on grassland or crops on a ﬁeld. This enables us to perform targeted high-resolution classiﬁcation only where necessary and thus maximize the value of data gathered during a mission.

To address this, we propose a new adaptive planning algorithm that directly tackles the altitude dependency of the deep learning semantic segmentation model using UAV- based imagery. First, our approach leverages prior labeled terrain data to empirically determine how classiﬁcation accu- racy varies with altitude; we train a deep neural network with images obtained at different altitudes that we use to initialize our planning strategy. Based on this analysis, we develop a decision function using Gaussian Process (GP) regression that is ﬁrst initialized on a training ﬁeld and then updated

Most data acquisition campaigns rely on coverage-based planning to generate UAV paths at a ﬁxed ﬂight altitude [2]. Although easily implemented, the main drawback of such methods is that they assume an even distribution of features

∗: authors with equal contribution. All authors are with the University of Bonn, Germany. This work has been funded by the Deutsche Forschungsgemeinschaft (DFG, German Research Foundation) under Germany’s Excellence Strategy, EXC-2070 – 390732324 (PhenoRob).

Current waypoint

online on a separate testing ﬁeld during a mission as new images are received. For replanning, the UAV path is chosen according to the decision function and segmented images to obtain higher classiﬁcation accuracy in more semantically detailed or interesting areas. This allows us to gather more accurate data in targeted areas without relying on a heuristic sensor model for informative planning.

Scouting at higher resolution

Continue predefined path

The contributions of this work are: (i) an online planning algorithm for UAVs that uses the semantic content of new images to adaptively map areas of ﬁner detail with higher accuracy. (ii) A variable-altitude accuracy model for deep learning-based semantic segmentation architectures and its integration in our planning algorithm. (iii) The evaluation of our approach against state-of-the-art methods using real- world data from an agricultural ﬁeld to demonstrate its performance. We note that, while this work targets the ap- plication of precision agriculture, our algorithm can be used in any other UAV-based semantic segmentation scenario, e.g., search and rescue [10], urban scene analysis, wetland assessment, etc.

Update decision function

low res

Next waypoint

high res

Fig. 2: Each time the UAV segments one region of the ﬁeld, we decide if the UAV should follow its predeﬁned path (right side) or if it should scout the same region with a lower altitude, i.e. obtaining images with high resolution (left side). In the second case, we update the decision strategy by comparing the segmentation results of the same regions at different altitudes.

II. RELATED WORK

There is an emerging body of literature addressing mission planning for UAV-based remote sensing. This section brieﬂy reviews the sub-topics most related to our work.

UAV-based Semantic Segmentation: The goal of se- mantic segmentation is to assign a predetermined class label to each pixel of an image. State-of-the-art approaches are predominantly based on convolutional neural networks (CNNs) and have been successfully applied to aerial datasets in various scenarios [20], [3], [12], [8], [21]. In the past few years, technological advancements have enabled efﬁcient segmentation on board small UAVs with limited computing power. Nguyen et al. [12] introduced MAVNet, a light- weight network designed for real-time aerial surveillance and inspection. Sa et al. [20] and Deng et al. [5] proposed CNN methods to segment vegetation for smart farming using similar platforms. Our work shares the motivation of these studies; we adopt ERFNet [19] to perform efﬁcient aerial crop/weed classiﬁcation in agricultural ﬁelds. How- ever, rather than ﬂying predetermined paths for monitoring, as in previous studies, we focus on planning: we aim to exploit modern data processing capabilities to localize areas of interest and ﬁner detail (e.g. high vegetation cover) online and steer the robot for adaptive, high-accuracy mapping in these regions.

model to update the map with new uncertain measurements. In contrast, our approach directly exploits the accuracy in semantic segmentation to drive adaptive planning. Second, they consider a predeﬁned, i.e. non-adaptive, sensor model, whereas ours is adapted online according to the behavior of the semantic segmentation model.

Very few works have considered planning based on seman- tic information. Bartolomei et al. [1] introduced a perception- aware planner for UAV pose tracking. Although like us, they exploit semantics to guide next UAV actions, their goal is to triangulate high-quality landmarks whereas we aim to obtain accurate semantic segmentation in dense images. Dang et al. [4] and Meera et al. [10] study informative planning for target search using object detection networks. Most similar to our approach is that of Popovi´c et al. [16], which adaptively plans the 3D path of a UAV for terrain monitoring based on an empirical performance analysis of a SegNet-based architecture at different altitudes [20]. A key difference is that our decision function, representing the network accuracy, is not static. Instead, we allow it to change online and thus adapt to new unseen environments.

Adaptive Path Planning: Adaptive algorithms for active sensing allow an agent to replan online as measurements are collected during a mission to focus on application-speciﬁc interests. Several works have successfully incorporated adap- tivity requirements within informative path planning prob- lems. Here, the objective is to minimize uncertainty in target areas as quickly as possible, e.g. for exploration [24], under- water surface inspection [7], target search [10], [22], [23], and environmental sensing [23]. These problem setups differ from ours in several ways. First, they consider a probabilistic map to represent the entire environment, using a sensor

Multi-Resolution: An important trade-off in aerial imag- ing arises from the fact that spatial resolution degrades with increasing coverage, e.g. Pe˜na et al. [13] show that there are optimal altitudes for monitoring plants based on their size. Relatively limited research has tackled this challenge in the contexts of semantic segmentation and planning. For mapping, Dang et al. [4] employ an interesting method for weighting distance measurements according to their resolu-

tion. Sadat et al. [22] propose an adaptive coverage-based strategy that assumes sensor accuracy increases with altitude. Other studies [25], [21] only consider ﬁxed-altitude mission planning. We follow previous approaches that empirically assess the effects of multi-resolution observations for trained models [10], [16], [17]. Speciﬁcally, our contribution is a new decision function that supports online updates for more reliable predictive planning.

altitudes to allow it to generalize across possible altitudes without the need for retraining. If the same region is observed by the camera from different altitudes, we preserve the results obtained with the highest resolution, assuming that higher- resolution images yield greater segmentation accuracy.

B. Path Planning: Basic Strategy

The initial ﬂight path is calculated based on the standard lawn-mower strategy [6]. Such a path enables covering the region of interest efﬁciently without any prior knowledge. We aim to adapt this path according to the non-uniform distribution of features in the ﬁeld to improve semantic segmentation performance.

III. OUR APPROACH

The goal of this work is to maximize the accuracy in the semantic segmentation of RGB images taken by a camera on-board a UAV with a limited ﬂight time. We propose a data-driven approach that uses information from incoming images to adapt an initial predeﬁned UAV ﬂight path online. The main idea behind our approach is to guide the UAV to take high-resolution images for ﬁne-grained segmentation at lower altitudes (higher resolutions) only where necessary.

For a desired region of interest, we deﬁne a lawn-mower path based on a series of waypoints. A waypoint is deﬁned as a position wi in the 3D UAV workspace where: (i) the UAV camera footprint does not overlap the footprints of any other waypoint; (ii) the UAV performs the semantic segmentation of its current ﬁeld of view; (iii) the UAV decides to revise its path or to execute the path as previously determined; and (iv) we impose zero velocity and zero acceleration.

As a motivating application, our problem setup considers a UAV monitoring an agricultural ﬁeld to identify crops and weeds for precision treatment. We ﬁrst divide the target ﬁeld into non-overlapping regions and, for each, associate a waypoint in the 3D space above the ﬁeld from which the camera footprint of the UAV camera covers the entire area. From these waypoints, we then deﬁne a lawn-mower coverage path that we use to bootstrap the adaptive strategy. Our strategy consists of two steps. First, at each waypoint along the lawnmower path, we use a deep neural network to assign a semantic label to each pixel in the observed region (soil, crop, and weed in our selected use-case). Second, based on the segmented output, we decide whether the current region requires more detailed re-observation at a higher image resolution, i.e., lower UAV altitude; otherwise, the UAV continues its pre-determined coverage path.

The initial ﬂight path is calculated in form of ﬁxed way- points at the highest altitude W hmax = {w0, w1, . . . , wn}. If necessary, we modify this coarse plan by inserting further waypoints based on the new imagery as it arrives. At each waypoint wi, UAV decides either to follow the pre- determined path, i.e. moving to wi+1, or to inspect the current region more closely at a lower altitude. In the second case, we deﬁne a second series of waypoints, W h′ = {w0, w1, . . . , wn}, at the desired altitude, h′, that will be inserted before wi+1 ∈W hmax so that the resulting path, at the desired altitude, is a lawn-mower strategy covering the camera footprint from wi ∈W hmax.

C. Planning Strategy: Ofﬂine Initialization

A key aspect of our approach is a new data-driven decision function that enables the UAV to select a new altitude for higher-resolution images if they are needed. This decision function is updated adaptively during the mission by com- paring the segmentation results of the current region at the different altitudes. This enables us to precisely capture the relationship between image resolution (altitude) and segmen- tation accuracy when planning new paths. Fig. 2 shows an overview of our planning strategy. In the following sub- sections, we describe the CNN for semantic segmentation and the path planning strategy, which consists of ofﬂine planning and online path adaptation.

We develop a decision function that takes a given waypoint as input and outputs the next waypoint, either wi+1 ∈W hmax

or w0 ∈W h′, given the segmentation result. In the case of an altitude change, our decision function outputs also the value of the desired altitude h′. To do this, we start by deﬁning a vegetation ratio providing the number of pixels classiﬁed as vegetation (crop and weed) as a fraction of the total number of pixels in the image:

P

c∈{crop, weed} pc

, (1)

v =

ptot

where ptot is the total number of pixel and pc is the total number of pixels classiﬁed as c. This vegetation ratio gives us a way to infer how valuable it is to spend time on the current region of the ﬁeld. It captures the intuition that higher values of this ratio indicate more possible misclassiﬁcations between the crop and weed classes. To quantify such a relationship, we let the UAV run on a separate ﬁeld, where we have access to ground truth data, segmenting regions of the ﬁelds with different altitudes. Segmenting the same region of the ﬁeld with different altitudes provides two pieces of information that we use to shape the decision function. On

A. Semantic Segmentation

In this work, we consider the semantic segmentation of RGB images not only as of the ﬁnal goal but also as a tool to deﬁne adaptive paths for re-observing given regions of the ﬁeld. Each time the UAV reaches a waypoint, we perform a pixel-wise semantic segmentation to assign a label (crop, weed or soil in our case) to each pixel in the current view. We use the ERFNet [19] architecture provided by the Bonnetal framework [11] that allows for real-time inference. We train this neural network on RGB images collected at different

Semantic Train Path Train Test

mIoU vs execution time

0.575

0.550

GSD3.0 GSD2.5 GSD2.0 GSD1.5 GSD1.0 Adaptive Non Adaptive

0.525

mIoU [%]

0.500

Fig. 3: We use three different ﬁelds from the WeedMap dataset [21] to train a CNN for semantic segmentation and one ﬁeld to initialize the planning strategy. The remaining ﬁeld is used for evaluation. For an extensive evaluation of our approach, we swap the roles of the ﬁelds so that we test our algorithm on each ﬁeld once.

0.475

0.450

0.425

250 500 750 1000 1250 1500 1750 exection time [s]

one hand, we have the difference between the altitudes from which we segment the ﬁeld, ∆h = hmax −h′. On the other hand, we have the the difference between the vegetation ratio in the predicted segmentation, ∆v = vhmax −vh′. At the same time, we can compare the vegetation ratio to the accuracy of the predicted segmentation by computing the mean inter- section over union (mIoU). Where the mIoU is deﬁned as the average over the classes C = {crop, weed, soil} of the ratio between the intersection of ground truth and predicted segmentation and the union of the same quantities:

Fig. 4: The averaged results for the testing ﬁelds from the WeedMap dataset. The blue square lies to the left of all performances with a linear decision function, indicating some performance improvement.

are learned from the training data by maximizing the log marginal likelihood. Given a set of observations y of f for the inputs X (i.e. our sets O, I), GP regression allows for learning a predictive model of f at the query inputs X∗by assuming a joint Gaussian distribution over the samples. The predictions at X∗are represented by the predictive mean µ∗ and variance σ2

gtc ∩predictionc gtc ∪predictionc

mIoU = 1 |C|

X

. (2)

∗deﬁned as:

c∈C

Again, we deﬁne the difference between mIoUs at different altitudes as, ∆mIoU = mIoUhmax −mIoUh′ .

µ∗= K(X∗, X) K−1

XX y,

−1 K(X, X∗), (5)

σ2

∗= K(X∗, X∗) −K(X∗, X) KXX

Our method thus considers two sets of observations, representing the relationships between the vegetation ratio and UAV altitude (O) and between vegetation ratio and mIoU (I) as follows:

where KXX = K(X, X) + ς2

n I, and K(·, ·) are matrices constructed using the covariance function k(·, ·) evaluated at the training and test inputs, X and X∗. In the following, we will use the ground sampling distance (GSD) to identify the image resolution (thus the UAV altitude) from which the UAV performs the semantic segmentation. The GSD is deﬁned as: GSD = hSw









∆v0 ∆mIoU0 ∆v1 ∆mIoU1

∆v0 ∆h0 ∆v1 ∆h1 ... ∆vn ∆hn

fIw , where h is the UAV altitude, Sw the sensor width of the camera in mm, f the focal length of the camera in mm and Iw the image width in pixels.

.

, I =





O =

... ∆vn ∆mIoUn

D. Planning Strategy: Online Adaptation

While both sets are initialized ofﬂine, we only update O online given that I requires access to ground truth that is clearly not available on testing ﬁelds. We ﬁt both sets of observations using GP regression [18]. A GP for a function f(x) is deﬁned by a mean function m(x) and a covariance function k(xi, xj):

To adapt the UAV behavior online to ﬁt the differences between the testing and training ﬁelds, we update the GP deﬁned by the set O in the following way. In the testing ﬁeld, each time the UAV decides to change altitude to a lower one, we compute a new pair ∆v′, ∆h′ and re-compute the GP output as deﬁned in Eq. (3).

f(x) ∼GP(m(x), k(xi, xj)). (3)

IV. EXPERIMENTAL RESULTS

A common choice is to set the mean function m(x) = 0 and to use the squared exponential covariance function:

We validate our proposed algorithm for online adaptive path planning on the application of UAV-based crop/weed semantic segmentation. The goal of our experiments is to demonstrate the beneﬁts of using our adaptive strategy to maximize segmentation accuracy in missions while keeping a low execution time. Speciﬁcally, we show results to support two key claims: our online adaptive algorithm can (i) map high-interest regions with higher accuracy and (ii) improve

2 |xi −xj|2





−1

k(xi, xj) = ς2

+ ς2

fexp

n, (4)

ℓ2

where θ = {ℓ, ς2

f, ς2

n} are the model hyperparameters and represent respectively the length scale ℓ, the variance of the output ς2

f and of the noise ς2

n. Typically, the hyperparameters

Fig. 5: Visual comparison of trajectories traveled by the UAV over a ﬁeld using different planning strategies. The coverage paths (left) are restricted to ﬁxed heights and cannot map targeted areas of interest. The linear decision function (middle) enables adaptive planning, but it is continuous with respect to altitude and leads to sudden jumps. Our adaptive approach overcomes this issue, leaving the path less often and more purposefully at selected heights for more efﬁcient mapping. The black spheres indicate measurement points.

D. Field Segmentation Accuracy vs Execution Time

segmentation accuracy while keeping a low execution time with respect to the baselines described in Sec. IV-B.

The ﬁrst experiment is designed to show that our proposed strategy obtains higher accuracy while keeping low execution time. We show such results in Fig. 4. For each strategy, we compute the mIoU (over the entire ﬁeld) and the execution time needed by the UAV to complete its path. The adaptive strategy crosses the line deﬁned by the lawnmower strategies at different altitudes, meaning that it can achieve better segmentation accuracy while keeping a lower execution time. The non-adaptive strategy instead lies under the curve, failing to overtake the lawn-mower strategy. We plot exemplary paths results from the different strategies in Fig. 5; on the left, we show the lawn-mower strategy with altitudes corresponding to GSDs of 1.0 cm

A. Dataset

To evaluate our approach, we use the WeedMap dataset [21]. It consists of 8 different ﬁelds collected with two different having different channels, it also provides pixel-wise semantic segmentation labels for each of the 8 ﬁelds. In this study, we focus only on the 5 ﬁelds having RGB information. We split the 5 ﬁelds into training and testing sets (Fig. 3). One of the training ﬁelds is used to initialize the decision function that shapes altitude selection in the adaptive strategy, as described in Sec. III-D. For each experiment in the following sub-sections, we test our approach and the baselines, see Sec. IV-B, on each ﬁeld once, and then report the average among each run.

px and 3.0 cm

px , while the middle and right plots show the paths resulting from non-adaptive and adaptive strategy, respectively.

E. Per-Image Segmentation Accuracy vs Altitude

B. Baselines

The second experiment shows the ability of our approach to achieve targeted semantic segmentation when compared to the non-adaptive strategy. At this stage, we compute mIoU for each image that contributes to the ﬁnal segmentation of the whole ﬁeld. This will give us a way to evaluate the efﬁciency of our adaptation strategy. We then visualize the mean and standard deviation. As can be seen in Fig. 6, our adaptive strategy provides higher per-image accuracies when the UAV is scouting the ﬁeld at low altitudes. This entails that, with our strategy, the UAV invests time resources in a more proﬁcuous manner. We show a qualitative comparison of the per-image semantic masks in Fig. 7.

To evaluate our proposed approach, we compare it against two main baselines. The ﬁrst one is the standard lawn- mower strategy where a UAV covers the entire ﬁeld at the same altitude, for this strategy we use consider ﬁve different altitudes resulting in GSD ∈{1.0, 1.5, 2.0, 2.5, 3.0} cm

px . The lawnmower strategy with a ﬁxed GSD of 3.0 cm

px corresponds to the initial plan for our strategy described in Sec. III-B. The second baseline is deﬁned by only initializing the UAV behavior as described in Sec. III-C and without adapting the strategy online using the decision function as new segmen- tations arrive. We refer to this strategy as “Non Adaptive”. This benchmark allows us to study the beneﬁt of adaptivity obtained by using our proposed approach (“Adaptive”).

V. CONCLUSION

In this paper, we presented a new approach for efﬁcient multi-resolution mapping using UAVs for semantic segmen- tation. We exploit prior knowledge and the new incoming segmentations in a way, that we get a decision function with a shape that produces a ﬂight path, leading to a performance gain in terms of segmentation accuracy while keeping comparatively short execution time. The resulting map is mapped with different resolutions, depending on the information content of a corresponding area. We believe that our approach opens a direction for efﬁcient UAV mapping

C. Metrics

Our evaluation consists of two main criteria: segmentation accuracy and mission execution time. For execution time, we compute the total time taken by the UAV to survey the whole ﬁeld, including the time needed to move between waypoints, segment a new image, and plan the next path. To assess the quality of the semantic segmentation we use the mIoU metric deﬁned in Eq. (2).

[7] G.A. Hollinger, B. Englot, F.S. Hover, U. Mitra, and G.S. Sukhatme.

Per-Image GSD vs mIoU

Active planning for underwater inspection and the beneﬁt of adaptivity. Intl. Journal of Robotics Research (IJRR), 32(1):3–18, 2013. [8] Y. Lyu, G. Vosselman, G.S. Xia, A. Yilmaz, and M.Y. Yang. Uavid:

0.65

Adaptive Non Adaptive

0.60

A semantic segmentation dataset for uav imagery. ISPRS Journal of Photogrammetry and Remote Sensing (JPRS), 165:108 – 119, 2020. [9] S. Manfreda, M.F. McCabe, P.E. Miller, R. Lucas, V. Pajuelo Madri-

0.55

mIoU [%]

gal, G. Mallinis, E. Ben Dor, D. Helman, L. Estes, G. Ciraolo, J. M¨ullerov´a, F. Tauro, M.I. De Lima, J.L.M.P. De Lima, A. Maltese, F. Frances, K. Caylor, M. Kohv, M. Perks, G. Ruiz-P´erez, Z. Su, G. Vico, and B. Toth. On the Use of Unmanned Aerial Systems for Environmental Monitoring. Remote Sensing, 10(4), 2018. [10] A.A. Meera, M. Popovi´c, A. Millane, and R. Siegwart. Obstacle-aware

0.50

0.45

0.40

Adaptive Informative Path Planning for UAV-based Target Search. In Proc. of the IEEE Intl. Conf. on Robotics & Automation (ICRA), pages 718–724, 2019. [11] A. Milioto, L. Mandtler, and C. Stachniss. Fast Instance and Semantic

0.35

1.0 1.5 2.0 2.5 3.0 GSD

Segmentation Exploiting LocalConnectivity, Metric Learning, and One-Shot Detection for Robotics. In Proc. of the IEEE Intl. Conf. on Robotics & Automation (ICRA), Montreal, QC, Canada, 2019. [12] T. Nguyen, S.S. Shivakumar, I.D. Miller, J. Keller, E.S. Lee, A. Zhou,

Fig. 6: Mean and standard deviation of the per-image statistics for semantic segmentation. Our adaptive strategy leads to better performance when scouting the ﬁeld at low altitudes.

T. ¨Ozaslan, G. Loianno, J.H. Harwood, J. Wozencraft, C.J. Taylor, and V. Kumar. MAVNet: An Effective Semantic Segmentation Micro- Network for MAV-Based Tasks. IEEE Robotics and Automation Letters (RA-L), 4(4):3908–3915, 2019. [13] J.M. Pe˜na, J. Torres-S´anchez, A. Serrano-P´erez, A.I. De Castro, and

F. L´opez-Granados. Quantifying Efﬁcacy and Limits of Unmanned Aerial Vehicle (UAV) Technology for Weed Seedling Detection as Affected by Sensor Resolution. Sensors, 15(3), 2015. [14] M. Popovi´c, G. Hitz, J. Nieto, I. Sa, R. Siegwart, and E. Galceran.

Online Informative Path Planning for Active Classiﬁcation Using UAVs. In Proc. of the IEEE Intl. Conf. on Robotics & Automation (ICRA), Singapore, 2017. [15] M. Popovi´c, T. Vidal-Calleja, G. Hitz, I. Sa, R. Siegwart, and J. Nieto.

Multiresolution Mapping and Informative Path Planning for UAV- based Terrain Monitoring. In Proc. of the IEEE/RSJ Intl. Conf. on Intelligent Robots and Systems (IROS), Vancouver, BC, Canada, 2017. [16] M. Popovi´c, T. Vidal-Calleja, G. Hitz, J.J. Chung, I. Sa, R. Siegwart,

and J. Nieto. An informative path planning framework for UAV-based terrain monitoring. Autonomous Robots, 44(6):889–911, 2020. [17] L. Qingqing, J. Taipalmaa, J.P. Queralta, T.N. Gia, M. Gabbouj,

Fig. 7: Qualitative ﬁeld segmentation results using the non-adaptive strategy (left) and the proposed adaptive strategy using our decision function (right) for path planning. The circled details demonstrate that our adaptive planning approach enables targeted high-resolution segmentation to better capture ﬁner plant details.

H. Tenhunen, J. Raitoharju, and T. Westerlund. Towards Active Vision with UAVs in Marine Search and Rescue: Analyzing Human Detection at Variable Altitudes. In IEEE International Symposium on Safety, Security, and Rescue Robotics, pages 65–70, 2020. [18] C.E. Rasmussen and C.K.I. Williams. Gaussian Processes for Machine

Learning. MIT Press, Cambridge, MA, 2006. [19] E. Romera, J.M. Alvarez, L.M. Bergasa, and R. Arroyo. Erfnet: Efﬁ-

cient residual factorized convnet for real-time semantic segmentation. IEEE Transactions on Intelligent Transportation Systems, 19(1):263– 272, 2017. [20] I. Sa, Z. Chen, M. Popovi´c, R. Khanna, F. Liebisch, J. Nieto, and

purposes, especially in precision agriculture. Further investi- gations on less homogeneous ﬁeld structures are to be carried out to reﬁne the approach.

R. Siegwart. weednet: Dense semantic weed classiﬁcation using multispectral images and mav for smart farming. IEEE Robotics and Automation Letters (RA-L), 3(1):588–595, 2018. [21] I. Sa, M. Popovi´c, R. Khanna, Z. Chen, P. Lottes, F. Liebisch, J. Nieto,


## REFERENCES

C. Stachniss, A. Walter, and R. Siegwart. Weedmap: A large-scale semantic weed mapping framework using aerial multispectral imaging and deep neural network for precision farming. Remote Sensing, 10, 2018. [22] S.A. Sadat, J. Wawerla, and R. Vaughan. Fractal trajectories for online

[1] L. Bartolomei, L. Teixeira, and M. Chli. Perception-aware path planning for uavs using semantic segmentation. In Proc. of the IEEE/RSJ Intl. Conf. on Intelligent Robots and Systems (IROS). IEEE, 2020. [2] T. Cabreira, L. Brisolara, and P.R. Ferreira Jr. Survey on coverage

non-uniform aerial coverage. In Proc. of the IEEE Intl. Conf. on Robotics & Automation (ICRA), pages 2971–2976, 2015. [23] A. Singh, A. Krause, and W.J. Kaiser. Nonmyopic Adaptive In- formative Path Planning for Multiple Robots. In International Jont Conference on Artiﬁcal Intelligence, page 1843–1850, 2009. [24] C. Stachniss, G. Grisetti, and W. Burgard. Information Gain-based

path planning with unmanned aerial vehicles. Drones, 3(1), 2019. [3] A. Carrio, C. Sampedro P´erez, A. Rodr´ıguez Ramos, and P. Campoy.

A review of deep learning methods and applications for unmanned aerial vehicles. Journal of Sensors, 2017:1–13, 2017. [4] T. Dang, C. Papachristos, and K. Alexis. Autonomous exploration and

simultaneous object search using aerial robots. In IEEE Aerospace Conference, 2018. [5] J. Deng, Z. Zhong, H. Huang, Y. Lan, Y. Han, and Y. Zhang.

Exploration Using Rao-Blackwellized Particle Filters. In Proc. of Robotics: Science and Systems (RSS), pages 65–72, Cambridge, MA, USA, 2005. [25] K.C. Vivaldini, T.H. Martinelli, V.C. Guizilini, J.R. Souza, M.D.

Lightweight Semantic Segmentation Network for Real-Time Weed Mapping Using Unmanned Aerial Vehicles. Applied Sciences, 10(20), 2020. [6] E. Galceran and M. Carreras. A survey on coverage path planning

Oliveira, F.T. Ramos, and D.F. Wolf. Uav route planning for active disease classiﬁcation. Autonomous Robots, 43(5):1137–1153, 2019.

for robotics. Robotics and Autonomous Systems, 61(12):1258–1276, 2013.
