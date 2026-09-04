---
workspace_id: SCI-000451
doi: 10.2139/ssrn.4486700
title: High-Precision Time Synchronization Algorithm for Unmanned Aerial Vehicle Ad
  Hoc Networks
authors:
- family_name: Bai
  given_name: Kaiyuan
  orcid: null
- family_name: Wu
  given_name: Jianfeng
  orcid: null
- family_name: Wu
  given_name: Huabing
  orcid: null
year: 2023
extraction_engine: pymupdf
extracted_at: '2026-09-04T10:46:38.828014+00:00'
---

# High-Precision Time Synchronization Algorithm for Unmanned Aerial Vehicle Ad Hoc Networks

Preprint not peer reviewed

High-precision Time Synchronization Algorithm for  Unmanned Aerial Vehicle Ad Hoc Networks

Kaiyuan Bai a,b, Jianfeng Wu a,b and Huabing Wu a,b,*

a National Time Service Center, Chinese Academy of Sciences, Xi’an 710600, China; baikaiyuan@ntsc.ac.cn(K.B.); wujianf@ntsc.ac.cn (J.W.)

b University of Chinese Academy of Sciences, Beijing 100049, China * Correspondence: whb@ntsc.ac.cn(H.W.)

Abstract: The increasing demand for missions involving unmanned aerial vehicles (UAVs) raises the need for reliable and accurate  time synchronization in ad hoc networks. Time synchronization plays a crucial role in coordinating the actions of multiple UAVs,  particularly when it comes to positioning, coordination, and data fusion. However, achieving high-precision time synchronization is  challenging due to the difficult-to-estimate communication transmission delay, measurement noise, relative motion, and clock source

characteristics in wireless ad hoc networks formed by UAVs. To address this issue, this paper proposes a fully distributed high-

precision network time synchronization algorithm that is suitable for multi-hop dynamic ad hoc networks. The proposed algorithm  is based on bidirectional pseudo-range measurements, graph theory, and random matrix correlation theory. The algorithm is  rigorously derived, requiring no central node, and it is capable of obtaining relative clock skew even when nodes broadcast clock  information asynchronously. In addition, the proposed algorithm enables real-time elimination of transmission delays and has noise- resistant capabilities. Simulation results validate the effectiveness of the algorithm, demonstrating that the time synchronization  accuracy in UAV ad hoc networks can reach the sub-nanosecond level.

Keywords: time synchronization; sub-nanosecond accuracy; wireless ad hoc networks; distributed algorithm; multi-hop dynamic  networks; transmission delay elimination


## 1. Introduction

As a special type of wireless communication network, wireless ad hoc networks comprise nodes that are equal in  status without a central control node [1]. Due to their flexibility and convenience, such networks play a critical role in  everyday life and military applications, e.g., sensor networks, vehicular networks, unmanned aerial vehicle (UAV)  swarms, and emergency response systems. UAV swarms are a specific application of wireless ad hoc networks, and  studying time synchronization techniques for wireless ad hoc networks is of significant importance for data fusion,  distance measurement, collaborative control, network stability, and security in UAV swarms [2–5].

In wireless ad hoc networks, the time of each node is provided by its own clock source; however, due to  manufacturing processes, inherent hardware characteristics, power-on duration, and aging, each clock source exhibits  frequency offset and frequency drift [6]. This implies that even with initial adjustments to achieve clock synchronization,  clock discrepancies gradually occur among nodes as devices operate over time. Thus, appropriate time synchronization  algorithms are required to address this issue.

Dynamic wireless ad hoc network time synchronization algorithms can be divided into three categories based on  the presence or absence of reference nodes, i.e., structured, distributed, and hybrid algorithms.

Structured time synchronization algorithms rely on the network's connectivity topology. Reference broadcast  synchronization, which was the first algorithm for sensor network time synchronization, is a representative example of  structured time synchronization algorithms [7]. Such networks require predefined or elected reference nodes, and time  synchronization among all nodes is realized through a specific tree-based routing network toward the reference nodes.  Similarly, the timing-sync protocol for sensor networks (TPSN) adopts a hierarchical network design, where each node  in the lower layer synchronizes with its corresponding node in the upper layer to achieve synchronization with the  reference nodes [8]. These structured algorithms were initially designed for specific network structures, which means  they tend to suffer from several issues, e.g., routing disruptions, significant pre-calibration information deviations, and  error accumulation, when faced with dynamic networks, thereby potentially affecting their effectiveness [9].

Distributed time synchronization algorithms originate from research into consistency issues in intelligent control  and distributed computing fields [10]. These algorithms do not require specific reference nodes. Here, each node  receives information from neighboring nodes within its communication range and achieves clock synchronization  among all nodes using consensus iteration algorithms [11]. In addition, distributed time synchronization algorithms are

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4486700

Preprint not peer reviewed

independent of the specific network connectivity topologies, with different topologies primarily affecting convergence  speed and synchronization accuracy but not the overall effectiveness of the algorithm. Currently, distributed time  synchronization algorithms are categorized into maximum consensus time synchronization (MTS) and average  consensus time synchronization (ATS) algorithms based on their core mechanisms. MTS algorithms attempt to  synchronize all node clocks to the fastest clock in the network [12], and ATS algorithms adjust the clocks of each node  to the weighted average of the clocks of its neighboring nodes, thereby converging to realize network-wide  synchronization [13].

The main concept of the hybrid time synchronization algorithm is that it integrates structured time synchronization  algorithm and distributed time synchronization algorithm based on the foundation of clustering. These algorithms  involve selecting reference nodes, where the nodes in the network are classified into clusters based on their Euclidean  distances to other nodes. Then a reference node is selected in each cluster, and distributed time synchronization  algorithms are applied among the reference nodes. Nodes within each cluster synchronize with the cluster's reference  node using one-way broadcast, ultimately achieving network-wide time synchronization with the reference nodes.  Representative examples of such algorithms include the flooding time synchronization protocol [14],the Doppler- enhanced time synchronization scheme [15],the vehicular ad-hoc networks time synchronization mechanism [16],the  median Kalman-filtering time synchronization scheme [17].

In consideration of various factors, e.g., communication delays, clock source noise, measurement noise, and routing  variations, the aforementioned ad hoc network time synchronization algorithms suffer from reduced synchronization  accuracy and may fail to operate effectively [18]. Time synchronization problems with noise are more aligned with real- world applications and have become a growing research focus, resulting in numerous achievements. For example, the  weighted maximum time synchronization algorithm, which is based on maximum consensus, synchronizes the clocks  of all nodes in the network to the fastest clock when the transmission delay follows a positive random variable; however,  the pseudo-synchronization issue was implicitly ignored in the corresponding paper [12]. Similarly, in consideration of  bounded noise, the noise-resilient maximum-consensus-based clock synchronization algorithm presents a completely  distributed time synchronization algorithm and exhibits exponential convergence [19]. Another study relied on the  maximum consensus principle to design the robust maximum time synchronization algorithm, which can compensate  for frequency offset and frequency drift independently while considering bounded noise [18]. However, these  algorithms are dependent on estimations of noise and the upper and lower bounds of transmission delays, thereby  limiting their synchronization accuracy severely. The distributed consensus time synchronization algorithm, which is  based on the average consensus concept, addresses time synchronization issues in intermittent connection dynamic  networks and performs well in terms of synchronization accuracy, energy consumption, and convergence speed [20].  Choi et al. proposed the distributed asynchronous clock synchronization (DCS) protocol for the pseudo-synchronization  problem; however, they did not address real-time elimination of transmission delays [21]. Li et al. studied the issue of  accelerated convergence based on the DCS protocol [22]. In addition, Xiong et al. proposed the second-order distributed  consensus time synchronization algorithm and determined its convergence region and optimal convergence speed in  undirected networks, and they conducted a study to investigate scenarios with Gaussian delays [23]. Sommer et al.  studied distributed time synchronization algorithms by abstracting them as gradient optimization problems and  proposed the gradient time synchronization protocol (GTSP) [24], which Solis et al. also investigated and found similar  results [25]. Kim et al. further studied the convergence speed and energy consumption of GTSP and proposed the  adaptive gradient time synchronization protocol , which adjusts communication intervals dynamically [26]. Yildirim et  al. researched how to synchronize ad hoc network time to an external reference clock source (e.g., UTC) based on GTSP  and proposed external gradient time synchronization protocol [27]. Garone et al. proposed the robust average time  synchronization algorithm, which considers a bounded noise model based on ATS [28]. In addition, Carli et al. studied  the clock synchronization problem in the presence of frequency drift under noise considerations by introducing a  second-order consensus algorithm while exploring issues arising from asynchronous implementations [29]. Bolognani  et al. proposed a random clock synchronization protocol based on the second-order consensus algorithm and  mathematically proved its convergence rigorously in terms of mean square [30]. Other studies have investigated ad hoc  network time synchronization algorithms from different perspectives. For example, Masood et al. constructed clock  difference equations with an autoregressive integrated moving average process to ensure steady-state Kalman filter  solutions and then tracked the clock evolution of the oscillator with a dynamic stochastic model to synchronize the  clocks between nodes [31]. In addition, Wang et al. employed the simulated annealing algorithm to study network time  synchronization problems [32], and Qiu et al. studied static single-hop network time synchronization algorithms by  introducing the least-squares method to combine time and frequency synchronization in TPSN [33]. Ansere et al.  proposed the adaptive beacon time synchronization algorithm to achieve time synchronization among nodes in a  vehicle ad hoc network, where the transmission delays follow a Gaussian distribution. They also introduced a node

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4486700

Preprint not peer reviewed

pairing algorithm to reduce energy consumption by improving the transmission of beacon messages [34]. Werner-Allen  et al. referred to the mechanism of firefly bioluminescence and achieved state synchronization of all nodes in a network  by adjusting their pulse frequency and phase [35].

In summary, the current research on time synchronization algorithms in static wireless ad hoc networks is  relatively mature; however, research into time synchronization algorithms in dynamic wireless ad hoc networks faces  four main challenges [19,36].

The first challenge is the consideration of clock source characteristics. Mathematical models describing the clock  sources themselves vary, and the emphasis varies when applied to different practical applications. In addition, the  vibration and temperature characteristics of devices in dynamic scenarios can affect the clock sources. When each clock  source operates independently, it measures time based on its own reference, which leads to the practical issue of pseudo- synchronization [13].

The second challenge is related to communication transmission delay during the time synchronization process.  This delay is caused by the hardware delay of the transmitting node, propagation delay, and hardware delay of the  receiving node. The hardware delay of the transmitting and receiving nodes can be calibrated and eliminated in advance  in a laboratory setting. However, the propagation delay changes continuously due to the dynamic nature of the  network. With high-precision time synchronization requirements, this delay must be eliminated in real time.

The third challenge is the impact of noise errors. Wireless communication signals are affected by propagation noise,  reception noise, and the inherent noise of the clock source during propagation. These noise errors directly affect the  time synchronization accuracy and may affect successful operation of time synchronization algorithms.

The fourth challenge is the relative motion of nodes. The movement of nodes in an ad hoc network serves specific  network functions rather than the time synchronization algorithm itself. Thus, adaptive and robust requirements are  imposed on dynamic ad hoc network time synchronization algorithms. The dynamic nature of nodes causes the  communication topology network structure to change continuously, which may lead to several problems, including  communication routing table failure and data loss, thereby rendering many time synchronization algorithms designed  for static networks inapplicable. In addition, it renders the calibration of propagation delay and fixed routing tables  inapplicable.

Therefore, this paper focuses on the high-precision time synchronization requirements of dynamic wireless ad hoc  networks composed of UAV clusters. Considering the characteristics of clock sources, second-order power-law  spectrum noise models, signal propagation delay, Gaussian white noise in the measurement process, pseudo- synchronization problems, and node motion, we design a high-precision wireless ad hoc network time synchronization  algorithm based on bidirectional pseudo-range measurement and average consistency. The proposed algorithm ensures  that all UAV nodes in the network can obtain the same logical clock skew and logical clock offset. A theoretical analysis  proves that the proposed algorithm realizes high-precision time synchronization in noisy dynamic scenarios, and a  simulation implementation is conducted. The proposed algorithm comprises bidirectional pseudo-range measurement,  relative skew estimation, logic skew compensation, and logic offset compensation.

The remainder of this paper is organized as follows. Section 2 introduces the time synchronization problem in  dynamic ad hoc networks with noise, bidirectional time-frequency transfer models, wireless ad hoc network models,  and clock models. Section 3 describes the flow of the proposed algorithm in detail and its theoretical proof. Section 4  discusses simulations performed to validate the effectiveness of the proposed algorithm. Finally, the paper is concluded  in Section 5.


## 2. Preliminaries and Problem Formulation

2.1. Network Model

A wireless ad hoc network comprising 𝑁 UAVs can be abstracted as an undirected graph 𝐺= (𝑉,𝐸), where 𝑉= {1,2,…,𝑁} represents the set of nodes in the network. Here, (𝑖,𝑗) ∈E denotes any two nodes (i,𝑗) in the network that  can communicate with each other, and this is referred to as an edge in the network, where 𝐸 is the set of edges in the  network. In the undirected graph 𝐺, if there exist nodes 𝑖, 𝑗, and 𝑘 such that (𝑖,𝑗) ∈E and (𝑗,𝑘) ∈E, it is said that there  exists a path between nodes 𝑖 and 𝑘. In addition, if there exists a path between any two nodes 𝑖 and 𝑗, the graph 𝐺 is  called a connected graph. For any node 𝑖 in graph 𝐺, if there exists {(𝑖,𝑗) ∈𝐸│𝑖,𝑗∈𝑉}, node 𝑖 is considered to be a  neighbor of node 𝑗, and due to the undirected nature of graph 𝐺, 𝑗 is also a neighbor of 𝑖. Here, 𝑁𝑖 denotes the set of  neighboring nodes of node 𝑖, and d𝑖 represents the number of neighboring nodes, which is referred to as the degree of  node 𝑖.

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4486700

Preprint not peer reviewed

The Laplace matrix of graph 𝐺 is defined as 𝐿= 𝐷― 𝐴, where matrix D ∈𝑅𝑁×𝑁 is the degree matrix, the main  diagonal element is {d1,d2,…,d𝑁}, the other elements are 0, matrix A ∈𝑅𝑁×𝑁 is the adjacency matrix, and the elements  in A satisfy the following.

𝐴𝑖,𝑗= {1; 𝑖𝑓𝑓  (𝑖,𝑗) ∈E

0;   𝑜𝑡ℎ𝑒𝑟𝑤𝑖𝑠𝑒 (1)

Corresponding lemmas for the Laplace matrix are given below [37]. Lemma 2.1. The Laplace matrix L corresponding to the undirected graph G is a real symmetric matrix, and its row sum and column  sum are 0. Lemma 2.2. If graph 𝐺 is an undirected connected graph, then the Laplace matrix 𝐿 corresponding to graph 𝐺 is a semipositive  definite matrix, and 0 is the singlet eigenvalue of 𝐿, where 1 = {1,1,…,1}𝑇 is an eigenvector corresponding to 0.

2.2. Clock Model

2.2.1. Hardware Clock

The clock information of the UAV nodes is generated based on the oscillators equipped on the nodes. Neglecting  the small amplitude deviations of the oscillators, the output signals can be described by a mathematical model as  follows:

𝑉(𝑡) = 𝑉0𝑠𝑖𝑛 (2𝜋𝑓0𝑡+ 𝜙(𝑡)) (2)

where 𝑡 denotes the real time, 𝑉0 represents the amplitude of the output signal, 𝑓0 is the nominal frequency of the  oscillator, and 𝜙(𝑡) is the phase deviation caused by various noise sources. Here, the physical quantity of interest is the  instantaneous oscillator phase 𝐻(𝑡) = 2𝜋𝑓0𝑡+ 𝜙(𝑡), which can be expressed as follows:

𝐷𝑖


## 2 𝑡2 + 𝜀𝐻𝑖(𝑡)

(3)

𝐻𝑖(𝑡) = 𝛽𝑖+ 𝛼𝑖𝑡+

where 𝑡 is the real time, 𝛽𝑖 is the initial phase, 𝛼𝑖 is the actual frequency, 𝐷𝑖 is the frequency drift rate, and 𝜀𝐻𝑖(𝑡) is  random noise.

Taking the derivative of 𝐻𝑖(𝑡) yields the instantaneous frequency 𝑦𝑖(t):

𝑑𝐻𝑖(𝑡)

𝑑𝑡 = 𝛼𝑖+ 𝐷𝑖𝑡+ 𝜀𝑦𝑖(𝑡) (4)

𝑦𝑖(𝑡) =

where the random component 𝜀𝑦𝑖(𝑡) is the derivative of 𝜀𝐻𝑖(𝑡), which can be described by a power-law spectral noise  model. Typically, 𝜀𝑦𝑖(𝑡) is assumed to be a linear combination of five mutually independent random noises, which can  be modeled mathematically as follows:

2

ℎ𝑘𝑓𝑘 (5)

𝑆𝑦𝑖(𝑓) =

𝑘=―2

where 𝑆𝑦𝑖(𝑓) is the power spectral density function of frequency, and ℎ𝑘 is a constant, where 𝑘= { ―2, ― 1,0,1,2},  corresponding to five different types of noise, i.e., random walk frequency modulation, flicker frequency modulation,  white frequency modulation, flicker phase modulation, and white phase modulation [38,39].

2.2.2. Software Clock

As mentioned previously, the oscillators equipped on different UAV nodes have different initial phases, initial  frequencies, and frequency drifts due to various production processes, operating times, working temperatures.  Considering that the oscillator must provide continuous physical clock signals for the entire device, its model  parameters should not be changed arbitrarily. Thus, a software clock model is introduced to adjust parameters to realize  time synchronization. Specifically, the software clock 𝐿𝑖(𝑡) is a first-order linear function of the hardware clock 𝐻𝑖(𝑡):

𝐷𝑖


## 2 𝑡2 + 𝛼𝑖(𝑡)𝜀𝐻𝑖(𝑡) = 𝛼𝑖(𝑡)𝑡+ 𝛽𝑖(𝑡)

(6)

𝐿𝑖(𝑡) = 𝛼𝑖(𝑡)𝐻𝑖(𝑡) + 𝛽𝑖(𝑡) = 𝛼𝑖(𝑡)𝛼𝑖𝑡+ 𝛼𝑖(𝑡)𝛽𝑖+ 𝛽𝑖(𝑡) + 𝛼𝑖(𝑡)

where 𝑡 represents the real time, 𝛼𝑖(𝑡) is the software clock skew, 𝛽𝑖(𝑡) is the software clock offset, 𝛼𝑖(𝑡) = 𝛼𝑖(𝑡)𝛼𝑖 is

the logical clock skew, and 𝛽𝑖(𝑡) = 𝛼𝑖(𝑡)𝛽𝑖+ 𝛽𝑖(𝑡) + 𝛼𝑖(𝑡)𝐷𝑖

2𝑡2 is the logical clock offset. Here, 𝛼𝑖𝜀𝐻𝑖(𝑡) represents the  noise term.

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4486700

Preprint not peer reviewed

2.3. Two-Way Time and Frequency Transfer Model

Two-way time and frequency transfer is based on bidirectional pseudo-range measurement [40]. To ensure the  existence of direct or indirect communication links between any UAV nodes in the network, each node adopts the  CDMA+FDMA multiple access scheme and full-duplex communication mechanism [41]. Here, the node modulates its  own clock signal through a modulator-demodulator and pseudo-random code modulation, and it sends the  synchronous signal to other nodes within the communication range at fixed intervals and at the pre-assigned frequency  points of each node. The UAV node that receives the signal records the reading of the local clock at the current moment  and captures, tracks, demodulates, achieves bit synchronization and frame synchronization of the received signal. The  information of hours, minutes, and seconds can be obtained directly after demodulation, and time information accuracy  of less than a second can be extracted from the epoch counter. The local pseudo-range measurement value can be  obtained by subtracting the combined time information from the local clock information. At the next transmission  moment, pseudo-range information is exchanged through a bidirectional communication link, which can be utilized to  compute the clock offset and Euclidean distance between the two nodes, thereby completing the bidirectional time and  frequency transfer [42].

𝜌𝑖

Node i

𝜏𝑗𝑖

𝜏𝑖𝑗

Node j

𝜌𝑗

∆𝑡


> **Figure 1. Principle of two-way time and frequency transfer.**

The principle of two-way time and frequency transfer is illustrated in Figure 1 from a geometrical perspective. Two  UAV nodes 𝑖 and 𝑗 send ranging signals simultaneously and begin timing. The time interval can be obtained when  these nodes receive each other's ranging signals, i.e., the ranging information 𝜌𝑖 and 𝜌𝑗, respectively.

{

𝜌𝑖= ∆𝑡+ 𝜏𝑗𝑖+ 𝛿𝑖 𝜌𝑗= ―∆𝑡+ 𝜏𝑖𝑗+ 𝛿𝑗 (7)

Here, ∆𝑡 represents the clock offset between nodes 𝑖 and 𝑗, 𝜏𝑗𝑖 and 𝜏𝑖𝑗 are the propagation delays, and 𝛿𝑖 and  𝛿𝑗 are the mutually independent pseudo-range measurement white noise of nodes 𝑖 and 𝑗, respectively. Throughout  the entire bidirectional pseudo-range measurement process, the communication channel is approximately symmetric,  i.e., 𝜏𝑗𝑖≈𝜏𝑖𝑗, which is represented as 𝜏 in the following. Subtracting the two equations yields the clock offset ∆𝑡.

1 2 [(𝜌𝑖― 𝜌𝑗) ― (𝛿𝑖― 𝛿𝑗)] (8)

∆𝑡=

The obtained measurement accuracy of the clock offset can reach the nanosecond level, thereby laying the  foundation for high-precision time synchronization of the entire network [40,43].

Here, we describe the bidirectional time and frequency transfer from the perspective of clock data sources. Local  node 𝑖 extracts clock information 𝐻𝑗(𝑡) sent by node 𝑗 at time 𝑡 from the epoch counter and subtracts it from the  current local clock information 𝐻𝑖(𝑡+ 𝜏) to obtain the range measurement information 𝜌𝑖.

𝐷𝑖


## 2 (𝑡+ 𝜏)2 + 𝜀𝐻𝑖(𝑡+ 𝜏) ―[𝛽𝑗+ 𝛼𝑗𝑡+

𝐷𝑗


## 2 𝑡2 + 𝜀𝐻𝑗(𝑡)] + 𝛿𝑖

(9)

𝜌𝑖= 𝐻𝑖(𝑡+ 𝜏) ― 𝐻𝑗(𝑡) = 𝛽𝑖+ 𝛼𝑖(𝑡+ 𝜏) +

Similarly, node 𝑗 measures the range measurement information 𝜌𝑗 as follows.

𝐷𝑗


## 2 (𝑡+ 𝜏)2 + 𝜀𝐻𝑗(𝑡+ 𝜏) ―[𝛽𝑖+ 𝛼𝑖𝑡+

𝐷𝑖


## 2 𝑡2 + 𝜀𝐻𝑖(𝑡)] + 𝛿𝑗

(10)

𝜌𝑗= 𝐻𝑗(𝑡+ 𝜏) ― 𝐻𝑖(𝑡) = 𝛽𝑗+ 𝛼𝑗(𝑡+ 𝜏) +

Note that the symbols used in Equations (9) and (10) are consistent with those defined in the previous text. The  clock offset ∆𝑡 can be obtained by subtracting Equation (10) from Equation (9).

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4486700

Preprint not peer reviewed

1 2 [(𝜌𝑖― 𝜌𝑗) ― (𝛼𝑖― 𝛼𝑗)𝜏―( 𝐷𝑖


## 2 ―

𝐷𝑗

2)(2𝜏𝑡+ 𝜏2) ― (𝜀𝐻𝑖(𝑡+ 𝜏) ― 𝜀𝐻𝑗(𝑡) ― 𝜀𝐻𝑗(𝑡+ 𝜏) + 𝜀𝐻𝑖(𝑡)) ― (𝛿𝑖― 𝛿𝑗)] (11)

∆𝑡=

2.4. Problem Formulation

As mentioned previously, a hardware clock model and software clock model are introduced into the UAV ad hoc  network. The hardware clock is an inherent characteristic of the oscillator, and its parameters cannot be adjusted.  Realizing software clock reading equivalence between nodes can only be achieved by adjusting the parameters of the  software clock:

|𝐿𝑖(𝑘) ― 𝐿𝑗(𝑘)| = 0,    ∀𝑖,𝑗∈𝑉 (12)

𝑙𝑖𝑚 k→∞

Here, 𝑘 is the number of iterations. Time synchronization can be implemented in the entire network only when  the logical clock skew and logical clock offset of all nodes are the same.

𝑙𝑖𝑚 𝑘→∞|𝛼𝑖(𝑘) ― 𝛼𝑗(𝑘)| = 0,    ∀𝑖,𝑗∈𝑉 (13)

𝑙𝑖𝑚 𝑘→∞|𝛽𝑖(𝑘) ― 𝛽𝑗(𝑘)| = 0,    ∀𝑖,𝑗∈𝑉 (14)

To measure the time synchronization accuracy in the UAV ad hoc network, the following evaluation metrics are  defined.

𝜀𝛼(𝑘) = 𝑚𝑎𝑥|𝛼𝑖(𝑘) ― 𝛼𝑗(𝑘)| ,    ∀𝑖,𝑗∈𝑉 (15)

𝜀𝐿(𝑘) = 𝑚𝑎𝑥|𝐿𝑖(𝑘) ― 𝐿𝑗(𝑘)| ,    ∀𝑖,𝑗∈𝑉 (16)

where 𝜀𝛼(𝑘) represents the maximum difference of the logical clock skew, and 𝜀𝐿(𝑘) represents the maximum  difference of the software clock readings.

In this study, we specifically targeted a dynamic wireless ad hoc network comprising UAV nodes, where the  maximum speed of each UAV is no greater than 340 m/s, and the direct communication range of each UAV is no greater  than 10 km to ensure that the ranging signals can be captured and tracked. In addition, the UAVs have an endurance  mileage of less than six hours. To achieve high-precision time synchronization in the UAV network, the oscillators  equipped on each UAV node adopt ultra-stable crystal oscillators or atomic clocks with a frequency accuracy of no  greater than 5𝑒―11 and a frequency drift rate of no greater than 1.67𝑒―12/𝑑𝑎𝑦. In addition, the clock information  sending period T is no greater than 1000 s. We propose a distributed-network time synchronization algorithm for the  above scenario, where each node relies on only the clock information received from its neighboring nodes to adjust its

own software clock parameters 𝛼𝑖(k) and 𝛽𝑖(𝑘) in order to reduce 𝜀𝛼(𝑘) and 𝜀𝐿(𝑘), and ultimately achieve high- precision time synchronization for the entire network.


## 3. Proposed Synchronization Algorithm

This section introduces the proposed high-precision wireless ad hoc network time synchronization algorithm.  Similar to most consistency algorithms, the proposed algorithm primarily consists of three parts, i.e., relative clock skew  estimation, logic clock skew compensation, and logic clock offset compensation. Note that the asynchronous problem  of bidirectional time-frequency transmission is considered in the relative skew estimation process.

3.1. Relative Clock Skew Estimation

As can be seen from Equation (13), one of the purposes of time synchronization is to equalize the logic clock skew  between nodes. By substituting Equation (6) into Equation (13), we obtain the following:

𝛼𝑗 𝛼𝑖= 𝛼𝑗(𝑘)𝛼𝑖j    ∀𝑖,𝑗∈𝑉 (17)

𝑙𝑖𝑚 𝑘→∞𝛼𝑖(𝑘) = 𝛼𝑗(𝑘)

where 𝛼𝑖𝑗= 𝛼𝑗/𝛼𝑖 is the relative clock skew, and it is obvious that 𝛼𝑖𝑗= 1/𝛼𝑗𝑖. For any node 𝑖 in the network, after  receiving synchronization information from neighbor node 𝑗, the relative clock skew 𝛼𝑖𝑗 is first estimated to adjust  𝛼𝑖(𝑘).

Due to the inability of nodes to measure their own hardware clock skew directly, in previous literature [11–13,16– 19], 𝛼𝑖𝑗 was obtained based on a first-order clock model through clock sequence differential, as shown in Equation (18):

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4486700

Preprint not peer reviewed

𝛼𝑗𝑇+ 𝐷𝑗


## 2 (2𝑘𝑇2 ― 𝑇2) + 𝜀𝐻𝑗(𝑘𝑇) ― 𝜀𝐻𝑗((𝑘― 1)𝑇)

𝐻𝑗(𝑘𝑇) ― 𝐻𝑗((𝑘― 1)𝑇) 𝐻𝑖(𝑘𝑇) ― 𝐻𝑖((𝑘― 1)𝑇) =


## 2 (2𝑘𝑇2 ― 𝑇2) + 𝜀𝐻𝑖(𝑘𝑇) ― 𝜀𝐻𝑖((𝑘― 1)𝑇)

(18)

𝛼𝑖𝑗(𝑘𝑇) =

𝛼𝑖𝑇+ 𝐷𝑖

where 𝑇 is the synchronization information sending period for all network nodes, and 𝐻𝑗(𝑘𝑇) is the local clock  reading of node 𝑗 at real time 𝑘𝑇. By ignoring the impact of second-order terms and noise terms, Equation (18) can be  simplified to 𝛼𝑖𝑗(𝑘𝑇) = 𝛼𝑗/𝛼𝑖.

However, in practical situations, there are two points that must be clarified. First, after the synchronization  information sending period for all network nodes is predetermined, each node sends synchronization information at  its own clock source as the basis, which means that the values of 𝑇 in the numerator and denominator of the equation  differ. Second, taking the local node 𝑖 as an example, the time interval between two synchronization information  sending times is read from the local clock, and its value is the predetermined synchronization information sending  period 𝑇 for the entire network. Thus, the value of 𝐻𝑖(𝑘𝑇) ― 𝐻𝑖((𝑘― 1)𝑇) in Equation (18) cannot be obtained in  practice. Therefore, it is impossible to obtain the relative clock skew 𝛼𝑖𝑗 using Equation (18) in actual measurements.

In the proposed algorithm, the estimation of the relative clock skew between nodes 𝑖 and 𝑗, which is denoted 𝛼𝑗𝑖 (𝑘+ 1), is obtained by taking the difference of the clock difference from two bidirectional time and frequency transfers  as follows:

{

𝑇 + (

𝜂i𝑗,𝑘+1

2 + 1

𝜂i𝑗,𝑘+1

𝑇)

𝛼𝑗𝑖(𝑘+ 1) =

𝑆𝑖𝑗,𝑘+1 + 𝑘∙𝜂i𝑗,𝑘

(19)

𝜂i𝑗,𝑘+1 =

𝑘+ 1 𝑆𝑖𝑗,𝑘+1 = 1

2(𝜌𝑗𝑖,𝑘+1 ― 𝜌𝑖𝑗,𝑘+1) ― 1 2(𝜌𝑗𝑖,𝑘― 𝜌𝑖𝑗,𝑘)

where k ∈𝑁+ represents the ranging round, 𝑆𝑖𝑗,𝑘+1 represents the difference between the clock differences of nodes 𝑖  and 𝑗 between the 𝑘+ 1th and 𝑘th rounds, and 𝜂i𝑗,𝑘+1 represents the mean of 𝑆𝑖𝑗, and the theoretical analysis is as  follows:

Taking nodes 𝑖 and 𝑗 as an example, assuming 𝑇 is the synchronization information sending period for all  network nodes, node 𝑗 sends synchronization information to its neighboring node at local clock reading 𝑘𝑇. Here,  corresponding real time is denoted 𝑡𝑗,𝑘, i.e., 𝐻𝑗(𝑡𝑗,𝑘) = 𝑘𝑇. After the propagation delay 𝜏j𝑖(𝑡𝑗,𝑘), node 𝑖 receives the  synchronization information from node 𝑗 at the real time 𝑡𝑗,𝑘+ 𝜏j𝑖(𝑡𝑗,𝑘). At this time, the local clock reading of node 𝑖  is 𝐻𝑖(𝑡𝑗,𝑘+ 𝜏j𝑖(𝑡𝑗,𝑘)). Thus, the ranging information 𝜌𝑗𝑖,𝑘 obtained by node 𝑖 in the 𝑘th round with respect to node 𝑗 is  expressed as follows:

𝐷𝑖


## 2 (𝑡𝑗,𝑘+ 𝜏j𝑖(𝑡𝑗,𝑘))2 + 𝜀𝐻𝑖(𝑡𝑗,𝑘+ 𝜏j𝑖(𝑡𝑗,𝑘))

𝜌𝑗𝑖,𝑘= 𝐻𝑖(𝑡𝑗,𝑘+ 𝜏j𝑖(𝑡𝑗,𝑘)) ― 𝐻𝑗(𝑡𝑗,𝑘) = 𝛽𝑖+ 𝛼𝑖(𝑡𝑗,𝑘+ 𝜏j𝑖(𝑡𝑗,𝑘)) +


## 2 𝑡𝑗,𝑘

2 + 𝜀𝐻𝑗(𝑡𝑗,𝑘)] + 𝛿𝑖,𝑘
(20)

𝐷𝑗

―[𝛽𝑗+ 𝛼𝑗(𝑡𝑗,𝑘) +

Similarly, the ranging information 𝜌𝑖𝑗,𝑘 obtained by node 𝑗 in the 𝑘th round with respect to node 𝑖 is expressed  as follows:

𝐷𝑗


## 2 (𝑡𝑖,𝑘+ 𝜏𝑖𝑗(𝑡𝑖,𝑘))2 + 𝜀𝐻𝑗(𝑡𝑖,𝑘+ 𝜏𝑖𝑗(𝑡𝑖,𝑘))

𝜌𝑖𝑗,𝑘= 𝐻𝑗(𝑡𝑖,𝑘+ 𝜏𝑖𝑗(𝑡𝑖,𝑘)) ― 𝐻𝑖(𝑡𝑖,𝑘) = 𝛽𝑗+ 𝛼𝑗(𝑡𝑖,𝑘+ 𝜏𝑖𝑗(𝑡𝑖,𝑘)) +


## 2 𝑡𝑖,𝑘

2 + 𝜀𝐻𝑖(𝑡𝑖,𝑘)] + 𝛿𝑗,𝑘
(21)

𝐷𝑖

―[𝛽𝑖+ 𝛼𝑖(𝑡𝑖,𝑘) +

The symbols used in Equations (20) and (21) are consistent with those defined in the previous text. Then, when two nodes exchange synchronous information for the 𝑘+ 1th time, they swap the ranging information  from the 𝑘th time. Here, each node subtracts its own measurement information from the counterpart's measurement  information and divides the result by 2 to obtain the clock offset ∆𝑡(𝑘) at the time of transmitting the 𝑘th message as  follows:

1 2(𝜌𝑗𝑖,𝑘― 𝜌𝑖𝑗,𝑘) ― 1 2[(𝛼𝑖― 𝛼𝑗)(𝑡𝑗,𝑘― 𝑡𝑖,𝑘)] ― 1 2( 𝐷𝑖


## 2 -

𝐷𝑗

2)(𝑡𝑗,𝑘 2 ― 𝑡𝑖,𝑘 2) - 1 2𝑆𝑂𝑘- 1 2𝑀𝑘- 1 2𝑁𝑘― 1 2 (𝛿𝑖,𝑘― 𝛿𝑗,𝑘) (22)

∆𝑡(𝑘) =

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4486700

Preprint not peer reviewed

Here, ∆t(k) = (𝛼𝑖― 𝛼𝑗)𝑡𝑖,𝑘+ (

2)𝑡𝑖,𝑘 2 + (𝛽𝑖― 𝛽𝑗) represents the clock offset between two nodes at the real time

𝐷𝑖


## 2 -

𝐷𝑗

1 2𝑆𝑂𝑘 term is primarily influenced by the second-order term and is defined as  1 2𝑆𝑂𝑘= 𝐷𝑖 4(𝑡𝑗,𝑘∙𝜏j𝑖(𝑡𝑗,𝑘) + 𝜏j𝑖(𝑡𝑗,𝑘)2)

𝑡𝑖,𝑘. The

4(𝑡𝑖,𝑘∙𝜏𝑖𝑗(𝑡𝑖,𝑘) + 𝜏𝑖𝑗(𝑡𝑖,𝑘)2). In addition, the  1 2𝑀𝑘 term is mainly affected by the propagation delay and is defined as  1 2 𝑀𝑘= 1

𝐷𝑗

-

2[𝛼𝑖𝜏j𝑖(𝑡𝑗,𝑘) ― 𝛼𝑗𝜏𝑖𝑗(𝑡𝑖,𝑘)]. The  1 2𝑁𝑘 term is primarily influenced by the variation in power-law spectral noise and is

1 2𝑁𝑘= 1 2[𝜀𝐻𝑖(𝑡𝑗,𝑘+ 𝜏j𝑖(𝑡𝑗,𝑘)) + 𝜀𝐻𝑖(𝑡𝑖,𝑘) ― 𝜀𝐻𝑗(𝑡𝑖,𝑘+ 𝜏𝑖𝑗(𝑡𝑖,𝑘)) ― 𝜀𝐻𝑗(𝑡𝑗,𝑘)]. Finally,  1 2(𝛿𝑖,𝑘― 𝛿𝑗,𝑘) represents the  measurement white noise in the clock difference.

defined as

Similarly, the measured clock offset for the 𝑘+ 1th round is denoted ∆t(k + 1), which is calculated as follows.

∆𝑡(𝑘+ 1)

1 2(𝜌𝑗𝑖,𝑘+1 ― 𝜌𝑖𝑗,𝑘+1) ― 1 2[(𝛼𝑖― 𝛼𝑗)(𝑡𝑗,𝑘+1 ― 𝑡𝑖,𝑘+1)] - 1 2( 𝐷𝑖


## 2 -

𝐷𝑗

2)(𝑡𝑗,𝑘+1 2 ― 𝑡𝑖,𝑘+1 2) ― 1 2𝑆𝑂𝑘+1 - 1 2𝑀𝑘+1 - 1 2𝑁

(23)

=

𝛿𝑖,𝑘+1 ― 𝛿𝑗,𝑘+1)

Taking the difference between Equations (22) and (23), and then substituting 𝐻𝑖(𝑡𝑖,𝑘) = 𝐻𝑗(𝑡𝑗,𝑘) = 𝑘𝑇 and 𝐻𝑖(𝑡𝑖,𝑘+1) = 𝐻𝑗(𝑡𝑗,𝑘+1) = (𝑘+ 1)𝑇, we obtain the difference between the clock offsets in the 𝑘+ 1th and 𝑘th rounds.

1 2(𝜌𝑗𝑖,𝑘+1 ― 𝜌𝑖𝑗,𝑘+1) ― 1 2(𝜌𝑗𝑖,𝑘― 𝜌𝑖𝑗,𝑘)

2[(𝛼𝑖― 𝛼𝑗)( 𝑇 𝛼𝑗+ 𝑇

𝛼𝑖)] + (𝛼𝑖― 𝛼𝑗) 1

𝐷𝑖

𝐷𝑖

= 1


## 2 (𝑡𝑗,𝑘+1

2 ― 𝑡𝑗,𝑘
2)] + (𝛼𝑖― 𝛼𝑗) 1
𝛼𝑖[


## 2 (𝑡𝑖,𝑘+1

2 ― 𝑡𝑖,𝑘
2)] + (𝛼𝑖― 𝛼𝑗) 1
𝛼𝑗

𝛼𝑗[

(𝜀

(24)

2( 𝐷𝑖


## 2 -

𝐷𝑗

𝑗,𝑘) ― 𝜀𝐻𝑗(𝑡𝑗,𝑘+1)) + (𝛼𝑖― 𝛼𝑗) 1

(𝜀𝐻𝑖(𝑡𝑖,𝑘) ― 𝜀𝐻𝑖(𝑡𝑖,𝑘+1)) + 1

2)(𝑡𝑗,𝑘+1 2 + 𝑡𝑖,𝑘+1 2 ― 𝑡𝑗,𝑘 2 ― 𝑡𝑖,𝑘 2) + 1 2𝑆𝑂𝑘+

𝛼𝑖

― 1

2𝑆𝑂𝑘+ 1 2𝑀𝑘+1 ― 1 2𝑀𝑘+ 1 2𝑁𝑘+1 ― 1 2𝑁𝑘+ 1 2(𝛿𝑖,𝑘+1 ― 𝛿𝑗,𝑘+1) ― 1 2(𝛿𝑖,𝑘― 𝛿𝑗,𝑘)

Equation (24) can be rewritten as follows:

2[(𝛼𝑖― 𝛼𝑗)( 𝑇 𝛼𝑗+ 𝑇

𝛼𝑖)] + 1

𝑆𝑖𝑗,𝑘+1 = 1

2𝛶𝑖𝑗,𝑘+1 + 1 2𝛴𝑖𝑗,𝑘+1 (25)

1 2𝛴𝑖𝑗,𝑘+1 represents the difference between the white noise measurements of the clock offset between the 𝑘+ 1th

where

1 2𝛶𝑖𝑗,𝑘+1 refers to the other terms in Equation (24). According to the definition of relative clock skew,  we obtain the following.

and 𝑘th round, and


## 2 ∙𝑆𝑖𝑗,𝑘+1 = 𝑇(𝛼𝑗𝑖― 1

𝛼𝑗𝑖) + 𝛶𝑖𝑗,𝑘+1 + 𝛴𝑖𝑗,𝑘+1
(26)

In the context of this study, the numerical analysis has demonstrated that the impact of the frequency drift term in  𝛶𝑖𝑗,𝑘+1 is in the order of 𝑒―13, while errors resulting from the variability of the power spectral density noise are primarily  influenced by the synchronization period 𝑇, producing a value in the order of 𝑒―12 after computing the mean. Note  that errors caused by propagation delay are primarily influenced by the relative velocity and synchronization period  𝑇, with an effect on the order of 𝑒―13. In addition,

1 2𝛴𝑖𝑗,𝑘+1 is normally distributed with a mean of 0 and standard

1 2𝛶𝑖𝑗,𝑘+1 is subsumed under that generated by  1 2𝛴𝑖𝑗,𝑘+1, which implies  that 𝑆𝑖𝑗,𝑘+1 is mainly affected by the Gaussian white noise of the ranging measurement. To address this issue, we utilize  a recursive method to filter out the noise and compute the mean as follows.

deviation of 𝜎= 1𝑒―10. The noise introduced by

𝑆𝑖𝑗,𝑘+1 + 𝑘∙𝜂i𝑗,𝑘

𝑘+ 1 ,  𝑘∈𝑁+ (27)

𝜂i𝑗,𝑘+1 =

As each node's pseudo-range measurement noise is mutually independent at different time points, we can  determine that:

2(𝛼𝑗𝑖― 1 𝛼𝑗𝑖),  𝑘∈𝑁+ (28)

𝐸(𝜂i𝑗,𝑘) = 𝑇

𝑙𝑖𝑚 𝑘→∞𝑉𝑎𝑟(𝜂i𝑗,𝑘) = 𝜎2

𝑘= 0 (29)

Thus, as 𝑘 increases, 𝜂i𝑗,𝑘 will converge at a sublinear rate. In addition, as the relative clock skew 𝛼𝑗𝑖 is  nonnegative, we can estimate it as follows:

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4486700

Preprint not peer reviewed

𝑇 + (

𝜂i𝑗,𝑘+1

2 + 1 (30)

𝜂i𝑗,𝑘+1

𝑇)

𝛼𝑗𝑖(𝑘+ 1) =

We then obtain the following:

𝑙𝑖𝑚 𝑘→∞𝛼𝑗𝑖(𝑘) = 𝛼𝑗𝑖 (31)

3.2. Logic Clock Skew Compensation

In this section, we describe equalizing the logic clock skew 𝛼𝑖(𝑘) between nodes, i.e.:

𝑙𝑖𝑚 𝑘→∞|𝛼𝑖(𝑘) ― 𝛼𝑗(𝑘)| = 0,  ∀𝑖,𝑗∈𝑉 (32)

Drawing on the design of other consensus algorithms, we take node 𝑖 as an example. Once the relative clock skew  estimate 𝛼𝑖𝑗(𝑘) has stabilized, a software clock skew adjustment 𝛼𝑖(𝑘) is performed to equalize the logical clock skew  𝛼𝑖(𝑘) between nodes. The iterative formula for the software clock skew adjustment 𝛼𝑖(𝑘) is given in Equation (33).

1 𝑁𝑢𝑚+ 1(𝛼𝑖𝑗(𝑘+ 1)𝛼𝑗(𝑘) ― 𝛼𝑖(𝑘)) (33)

𝛼𝑖(𝑘+ 1) = 𝛼𝑖(𝑘) +

∀𝑗∈𝑁𝑖

Here, 𝑁𝑢𝑚 represents the maximum number of nodes that can communicate simultaneously in the network, where  𝑁𝑢𝑚+ 1 ≤𝑁. The definitions of the other symbols are consistent with those in the previous text.

Multiplying both sides of Equation (33) by 𝛼𝑖 yields:

1 𝑁𝑢𝑚+ 1(𝛼𝑖𝑗(𝑘+ 1)𝛼𝑗(𝑘)𝛼𝑖― 𝛼𝑖(𝑘)𝛼𝑖) (34)

𝛼𝑖(𝑘+ 1)𝛼𝑖= 𝛼𝑖(𝑘)𝛼𝑖+

∀𝑗∈𝑁𝑖

Thus, the iterative Equation (35) for the logical clock skew can be obtained by adjusting the software clock skew  𝛼𝑖(𝑘) according to Equation (34):

1 𝑁𝑢𝑚+ 1(𝛼𝑗(𝑘) ― 𝛼𝑖(𝑘)) (35)

𝛼𝑖(𝑘+ 1) = 𝛼𝑖(𝑘) +

∀𝑗∈𝑁𝑖

By expressing Equation (35) in matrix form, we obtain:

𝑋(k + 1) =(𝐼― 1 𝑁𝑢𝑚+ 1 𝐿(𝑘+ 1))𝑋(k) = 𝑃(𝑘+ 1)𝑋(k) (36)

where 𝑋(k) = (𝑥1(𝑘),𝑥2(𝑘),⋯,𝑥𝑁(𝑘))𝑇 represents the logical clock skew values of all nodes in the kth round of iteration,  𝐼 is an 𝑁-dimensional identity matrix, and 𝑃(𝑘+ 1) ∈𝑅𝑁×𝑁 is a doubly stochastic matrix.

The convergence analysis of the iterative process described above is as follows. Due to the motion of nodes in the network, the topology of the network changes constantly, which results in  different matrices 𝐿(𝑘),  𝑃(𝑘)，𝑘= 1,2,…,∞ at different times. The entire iterative process can be represented as follows:

𝑋(k) = 𝑃(𝑘)𝑋(k - 1) = 𝑃(𝑘)𝑃(𝑘- 1)···𝑃(1)𝑋(0) (37)

Here, 𝑋(0) = (𝑥1(0),𝑥2(0),⋯,𝑥𝑛(0))𝑇 represents the initial values of the logical clock skew of each node, and each 𝑃 (𝑛) is a doubly stochastic matrix. According to the relevant theory of Markov matrices, Lemma 2.1, and Lemma 2.2, it  is known that 1 is the simple eigenvalue of 𝑃(𝑛), 𝟏∈𝑅𝑁×1 is the corresponding eigenvector of 1, and the other  eigenvalues |𝛬𝑛(d)| < 1，𝑑= 2,3,…,𝑁 of 𝑃(𝑛). In addition, 𝑃(𝑛) is a real symmetric matrix that can be diagonalized  as follows:

1 ⋯ 0 ⋮ ⋱ ⋮ 0 ⋯ Λ𝑛(𝑁)][

⋮ 𝑄𝑛(𝑁)𝑇] (38)

𝑄𝑛(1)𝑇

𝑃(𝑛) = 𝑄𝑛Λ𝑛𝑄𝑇𝑛= [𝑄𝑛(1),𝑄𝑛(2),⋯,𝑄𝑛(𝑁)][

𝑄𝑛(2)𝑇

In Equation (38), 𝛬𝑛 is a diagonal matrix with all eigenvalues of 𝑃(𝑛) as its diagonal elements, and 𝑄𝑛(𝑑) is the  normalized eigenvector corresponding to the eigenvalue 𝛬𝑛(𝑑), 𝑑= 1,2,…,𝑁. The eigenvector corresponding to the

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4486700

Preprint not peer reviewed

eigenvalue 1 is 𝑄𝑛(1) = {

𝑇. Here, 𝑄𝑛(1),𝑄𝑛(2),…,𝑄𝑛(𝑁) form a set of orthonormal basis in N-dimensional

𝑁}

1 𝑁, 1

𝑁,⋯, 1

space, and 𝑋(0) can be expressed as a linear combination of [𝑄1(1),𝑄1(2),⋯,𝑄1(𝑁)] as follows:

𝑋(0) = [𝑄1(1),𝑄1(2),⋯,𝑄1(𝑁)][

⋮ 𝑐𝑁] (39)

𝑐1 𝑐2

Here, let 𝑋(0)′ = [𝑐2,𝑐3,⋯,𝑐𝑁]𝑇. From Equation (37), we obtain the following.

𝑋(1) = 𝑃(1)𝑋(0) = [𝑄1(1),𝑄1(2),⋯,𝑄1(𝑁)][

⋮ 𝛬1(𝑁)𝑐𝑁] (40)

𝑐1 𝛬1(2)𝑐2

Here, let 𝑋(1)′ = [𝛬1(2)𝑐2,𝛬1(3)𝑐3,⋯,𝛬1(𝑁)𝑐𝑁]𝑇. From the above equation, we can see that 𝑋(1) maintains its component on 𝑄1(1) from 𝑋(0), while the  components on 𝑄1(2),⋯,𝑄1(𝑁) are multiplied by a coefficient less than 1 in absolute value. In other words, 𝑋(1) is  obtained by compressing all components of 𝑋(0) except the one on 𝑄1(1) by a factor less than 1 in absolute value.  Thus, we obtain the following:

|𝑋(1)′| < |𝑋(0)′| (41)

Similarly, 𝑋(1) can be expressed as a linear combination of the orthonormal basis vectors 𝑄2(1),𝑄2(2),…,𝑄2(𝑁)  that are formed by the eigenvectors of 𝑃(2):

𝑋(2)

1 ⋯ 0 ⋮ ⋱ ⋮ 0 ⋯ 𝛬2(𝑁)]𝑄21[

⋮ 𝛬1(𝑁)𝑐𝑁]

𝑐1 𝛬1(2)𝑐2

= 𝑃(2)𝑋(1) = [𝑄2(1),𝑄2(2),⋯,𝑄2(𝑁)][

= [𝑄2(1),𝑄2(2),⋯,𝑄2(𝑁)]

[

𝑄2(𝑁)𝑇𝑄1(𝑖)𝛬1(𝑖)𝑐𝑖]

𝑐1

𝑁

(42)

𝑄2(2)𝑇𝑄1(𝑖)𝛬1(𝑖)𝑐𝑖

𝛬2(2)

𝑖=2

⋮

𝑁

𝛬2(𝑁)

𝑖=2

where

𝑄21 =[

⋮ 𝑄2(𝑁)𝑇𝑄1(𝑁)] (43)

0 𝑄2(2)𝑇𝑄1(2)

0 𝑄2(2)𝑇𝑄1(𝑁)

1 0 ⋮ 0

⋯ ⋯ ⋯ ⋯

⋮ 𝑄2(𝑁)𝑇𝑄1(2)

Let

𝑁

𝑋(2)′ =[

𝑄2(𝑁)𝑇𝑄1(𝑖)𝛬1(𝑖)𝑐𝑖]

𝑄2(2)𝑇𝑄1(𝑖)𝛬1(𝑖)𝑐𝑖

𝛬2(2)

𝑖=2

𝑁

𝑄2(3)𝑇𝑄1(𝑖)𝛬1(𝑖)𝑐𝑖

𝛬2(3)

(44)

𝑖=2

⋮

𝑁

𝛬2(𝑁)

𝑖=2

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4486700

Preprint not peer reviewed

The column vectors of matrix 𝑄21 form an orthonormal basis because the effect of multiplying an orthogonal  matrix by a vector is to reflect or rotate the vector without changing the length of the vector, and |𝛬2(d)| < 1， 𝑑= 2,3,…,𝑁. Thus, we obtain the following.

|𝑋(2)′| < |𝑋(1)′| < |𝑋(0)′| (45)

By applying the above process recursively, we can infer that:

|𝑋(𝑘)′| < |𝑋(𝑘― 1)′| < … < |𝑋(0)′| (46)

As 𝑘 tends to infinity, we have:

𝑙𝑖𝑚 𝑘→∞|𝑋(𝑘)′| = 0 (47)

Further, we obtain:

1 𝑁 ⋮ 1 𝑁]

𝑐1 𝑋(𝑘)′] = 𝑐1[

𝑙𝑖𝑚 𝑘→∞𝑋(𝑘) = [𝑄𝑘(1),𝑄𝑘(2),⋯,𝑄𝑘(𝑁)][

(48)

Here, 𝑐1 = {

𝑇𝑋(0). Equation (48) indicates that as the iteration proceeds, the elements of 𝑋(𝑘)

𝑁}

1 𝑁, 1

𝑁,⋯, 1

1 𝑁∑𝑁

converge to the same value of

𝑖=1 𝑥𝑖(0). Considering the practical significance of 𝑋(𝑘), the final logical clock skew  values of each node will converge to the average of the initial logical clock skew values of all nodes.

3.3. Logic Clock Offset Compensation

The objective of this section is to achieve equal logical clock offset among all nodes.

𝑙𝑖𝑚 𝑘→∞|𝛽𝑖(𝑘) ― 𝛽𝑗(𝑘)| = 0,    ∀𝑖,𝑗∈𝑉 (49)

By adjusting the software clock offset 𝛽𝑖(𝑡) to make the logical clock offset 𝛽𝑖(𝑡) equal, the iterative formula is  given by Equation (50).

1 𝑁𝑢𝑚+ 1(𝐿𝑗(𝑘) ― 𝐿𝑖(𝑘)) (50)

𝛽𝑖(𝑘+ 1) = 𝛽𝑖(𝑘) +

∀𝑗∈𝑁𝑖

By substituting Equation (6) and adding 𝛼i(𝑘)𝛽𝑖+ 𝛼𝑖(𝑘)𝐷𝑖

2𝑘2 to both sides of Equation (50) yields the following.

𝐷𝑖


## 2 𝑘2 = 𝛽𝑖(𝑘) + 𝛼i(𝑘)𝛽𝑖+ 𝛼𝑖(𝑘)

𝐷𝑖

𝐷𝑗

1 𝑁𝑢𝑚+ 1((𝛼𝑗(𝑘)𝛼𝑗𝑘+ 𝛼𝑗(𝑘)𝛽𝑗+ 𝛽𝑗(𝑘) + 𝛼𝑗(𝑘)


## 2 𝑘2 +

𝛽𝑖(𝑘+ 1) + 𝛼i(𝑘)𝛽𝑖+ 𝛼𝑖(𝑘)


## 2 𝑘

(51)

∀𝑗∈𝑁𝑖

𝐷𝑖


## 2 𝑘2 + 𝛼𝑖(𝑘+ 1)𝜀𝐻𝑖(𝑘)))

+ 𝛼𝑗(𝑘)𝜀𝐻𝑗(𝑘)) ― (𝛼𝑖(𝑘+ 1)𝛼𝑖𝑘+ 𝛼𝑖(𝑘+ 1)𝛽𝑖+ 𝛽𝑖(𝑘) + 𝛼𝑖(𝑘+ 1)

As 𝑘 increases, the software clock skew 𝛼i(𝑘) in Equation (51) tends to stabilize. By neglecting the changes in the

2(𝑘+ 1)2 - 𝛼𝑖(𝑘)𝐷𝑖 2𝑘2 and the effects of power-law spectral noise, Equation (51) can be  written as:

second-order term 𝛼𝑖(𝑘+ 1)𝐷𝑖

1 𝑁𝑢𝑚+ 1 (𝛽𝑗(𝑘) ― 𝛽𝑖(𝑘)) (52)

𝛽𝑖(𝑘+ 1) = 𝛽𝑖(𝑘) +

∀𝑗∈𝑁𝑖

Writing Equation (52) in matrix form yields:

(k + 1) =(𝐼― 1 𝑁𝑢𝑚+ 1 𝐿(𝑘+ 1))𝑌(k) = 𝑃(𝑘+ 1)𝑌(k) (53)

In Equation (53), 𝑌(k) = (𝑦1(𝑘),𝑦2(𝑘),…,𝑦𝑁(𝑘))𝑇 represents the values of the logical clock offset at each node in the  𝑘th iteration, 𝐼 is an 𝑁-dimensional identity matrix, and 𝑃(𝑘+ 1) ∈𝑅𝑁×𝑁 is a doubly stochastic matrix.

The convergence analysis is consistent with Section 3.2, and the final logical clock offset value of each node will  converge to the average of the initial logical clock offset values of all nodes. Thus, time synchronization is realized  among all nodes in the network:

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4486700

Preprint not peer reviewed

|𝐿𝑖(𝑘) ― 𝐿𝑗(𝑘)| = 0,    ∀𝑖,𝑗∈𝑉 (54)

𝑙𝑖𝑚 k→∞


## 4. Performance Evaluation

4.1. Simulation Setup

The proposed algorithm was simulated and verified based on STK and MATLAB. Here, 30 UAVs, each equipped  with an independent clock source, performed flying missions. The maximum communication range for each UAV was  10 km, and the maximum flying speed was no greater than 340 m/s. The initial frequency 𝛼𝑖 of each UAV node clock  source followed a uniform distribution within the range of [1 ― 5𝑒―11,1 + 5𝑒―11], the initial frequency drift rate 𝐷𝑖  followed a uniform distribution within the range of [0, 1.67𝑒―12 𝑑𝑎𝑦], the initial clock offset 𝛽𝑖 was uniformly  distributed within [ ―1s,1𝑠], and the power-law spectral noise of the clock source was generated based on the numerical  simulation presented in the literature [39]. The clock discrepancy measurement noise was Gaussian white noise  following 𝑁(0,( 2𝑒―10)2). The initial values of each node were set to 𝛼𝑖(0) = 1,𝛽𝑖(0) = 0,𝑁𝑢𝑚= 29,∀𝑖∈𝑉, and the  synchronization signal transmission period 𝑇= 1 s.


> **Figure 2. Top view of the UAV trajectory.**

The top view of the flight trajectories of the 30 UAVs is shown in Figure 2, where each UAV took off from a different  location and sequentially passed through four target points. After hovering for five circles above each target point, the  UAVs returned to their starting point. The entire operation lasted approximately three hours, and at any given time the  undirected graph 𝐺 formed by the UAVs was connected. Due to the movement of the UAVs, the communication link  between two nodes may be interrupted. Taking UAV3-3 as an example, Figure 3 shows the communication link  establishment between UAV3-3 and the other 29 UAVs, where the line segments represent the available bidirectional  communication between the two UAVs during that time.

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4486700

Preprint not peer reviewed


> **Figure 3. Changes in UAV3-3 communication link.**

4.2. Simulation Results

To validate the effectiveness and robustness of the proposed algorithm for time synchronization in dynamic  network scenarios, the algorithm was applied to the scenario described in Section 4.1.

1.000000000074

1.0000000000735

1.000000000073

Relative clock skew

1.0000000000725

1.000000000072

1.0000000000715

1.000000000071

Estimation Ideal

1.0000000000705

0 1000 2000 3000 4000 5000 6000 7000 8000 9000 10000 Time (s)


> **Figure 4. Variation of estimated relative clock skew with time.**

10-12

0.5

0

Estimation error of relative clock skew

-0.5

-1

-1.5

-2

-2.5

-3

-3.5

0 1000 2000 3000 4000 5000 6000 7000 8000 9000 10000

Time (s)


> **Figure 5. Estimation error of relative clock skew.**

Taking UAV3-3 and UAV5-1 as examples, Figure 4 shows the change in the relative clock skew estimation  calculated using the proposed algorithm as the operation time increased. The estimated relative clock skew gradually

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4486700

Preprint not peer reviewed

approached the true value, and its estimation error is shown in Figure 5. As can be seen, it reached the 𝑒-13 level and  tended to be stable after approximately 500 s. In Figure 4 and Figure 5, the line segments parallel to the horizontal axis  at the beginning are set to be strictly equal to 0, which indicates that no communication link was established between  the two nodes. The other line segments parallel to the horizontal axis imply that the two UAVs were out of  communication range during this time period, and their estimates maintain the values from the previous moment until  new bidirectional pseudo-range measurement information appears between the two UAVs, corresponding to UAV03- 3-To-UAV05-1-Times in Figure 3.

RMSE

1.50E-10

RMSE of the relative clock skew estimation

1.20E-12

1.00E-10

1.00E-12

8.00E-13

6.00E-13

5.00E-11

0 5000 10000

0.00E+00

0 5000 10000

Time (s)


> **Figure 6. RMSE of the relative clock skew estimation.**


> **Figure 6 shows the root mean square error (RMSE) of the relative clock skew estimation at different moments. After**

> approximately 550 s, the value converged to the 𝑒-13 level, which validates the effectiveness of the proposed algorithm 
(Section 3.1).

UAV1-1 UAV1-2 UAV1-3 UAV2-1 UAV2-2 UAV2-3 UAV3-1 UAV3-2 UAV3-3 UAV4-1 UAV4-2 UAV4-3 UAV5-1 UAV5-2 UAV5-3 UAV6-1 UAV6-2 UAV6-3 UAV7-1 UAV7-2 UAV7-3 UAV8-1 UAV8-2 UAV8-3 UAV9-1 UAV9-2 UAV9-3 UAV10-1 UAV10-2 UAV10-3

1.000000000076E+0

1.000000000056E+0

Logical clock skew

1.000000000036E+0

1.000000000016E+0

9.999999999959E-1

9.999999999759E-1

9.999999999559E-1

0 5000 10000 9.999999999359E-1

Time (s)


> **Figure 7. Change in logical clock skew.**


> **Figure 7 shows the change in logical clock skew over time. As shown, the values converged progressively as the**

> operation time increased; thus, gradual stability was realized.

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4486700

Preprint not peer reviewed

2.60E-12

1.50E-10

2.40E-12

The maximum difference of logical clock skew

2.20E-12

2.00E-12

1.80E-12

1.00E-10

1.60E-12

1.40E-12

5000 10000 1.20E-12

5.00E-11

0.00E+00

0 5000 10000

Time (s)


> **Figure 8. Maximum difference of logical clock skew.**


> **Figure 8 shows the change in the maximum difference of logical clock skew 𝜀𝛼(𝑘) over time. As can be seen, 𝜀𝛼(𝑘)**

> decreased gradually to the 𝑒-12 level and tended to stabilize. This was because, upon reaching the 𝑒-12 level, it was 
affected by the average value of the power-law spectral noise variation in the relative clock skew estimation, which 
could not be filtered out by averaging, which is consistent with the analysis presented in Section 3.1.

2.0

The maximum difference in software clock readings (s)

8.00E-10

7.00E-10

1.5

6.00E-10

5.00E-10

4.00E-10

3.00E-10

1.0

2.00E-10

5000 10000 1.00E-10

0.5

0.0

0 5000 10000

Time (s)


> **Figure 9. Maximum difference in software clock readings.**


> **Figure 9 shows the change in the maximum difference in software clock readings 𝜀𝐿(𝑘) over time. As shown, after**

> 600 s, 𝜀𝐿(𝑘) converged to the 𝑒―10 level and tended to stabilize, with an average value of 0.27 ns and a standard 
deviation of 5.6𝑒―11. These results demonstrate that the overall UAV network time synchronization precision reached 
the sub-nanosecond level.


## 5. Conclusions

Focusing on the demand for high-precision time synchronization in UAV networking, this paper investigated the  practical problem of obtaining the hardware clock relative skew when UAV nodes cannot broadcast clock information  synchronously. Based on an analysis of UAV motion, transmission delay, communication noise, and clock source  characteristics, a distributed-network high-precision time synchronization algorithm was proposed. The proposed

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4486700

Preprint not peer reviewed

algorithm comprises bidirectional one-way pseudo-range measurements, relative clock skew estimation, logic clock  skew compensation, and logic clock offset compensation. The proposed algorithm was evaluated in simulations, and  the results demonstrated that this algorithm can realize real-time elimination of transmission delays, suppression of  ranging noises under more realistic conditions, and robustness to frequent changes in communication network  topology. In addition, the time synchronization precision of the entire UAV network can reach the sub-nanosecond  level.

Author Contributions: Conceptualization, K.B. and H.W.; methodology, K.B., H.W. and J.W; software, K.B. and H.W.; validation,  K.B., H.W. and J.W; formal analysis, K.B.; resources, K.B., H.W. and J.W; data curation, K.B.; writing—original draft preparation,  K.B.; writing—review and editing, H.W. and J.W.; supervision, H.W. and J.W. All authors have read and agreed to the published  version of the manuscript.

Funding: This work was supported by the Youth Innovation Promotion Association CAS (No. 2019399).

Data Availability Statement: The datasets analyzed are available from the corresponding author upon a reasonable request.

Conflicts of Interest: The authors declare no conflict of interest.


## References

[1] B. Sundararaman, U. Buy, A.D. Kshemkalyani, Clock synchronization for wireless sensor networks: a survey, Ad Hoc  Networks. 3 (2005) 281–323. https://doi.org/10.1016/j.adhoc.2005.01.002. [2] C.-C. Tuan, Y.-C. Wu, Temporal Event Ordering with Fault Tolerance for Wireless Sensor and Actuator Networks, Wirel. Pers.  Commun. 68 (2013) 679–695. https://doi.org/10.1007/s11277-011-0476-3. [3] L. Girod, D. Estrin, Robust range estimation using acoustic and multimodal sensing, Proceedings 2001 IEEE/RSJ International  Conference on Intelligent Robots and Systems. Expanding the Societal Role of Robotics in the the Next Millennium (Cat.  No.01CH37180). 3 (2001) 1312–1320 vol.3. [4] H. Wang, P. Gong, F. Yu, M. Li, Clock Offset and Skew Estimation Using Hybrid One-Way Message Dissemination and Two- Way Timestamp Free Synchronization in Wireless Sensor Networks, IEEE Communications Letters. 24 (2020) 2893–2897.  https://doi.org/10.1109/LCOMM.2020.3019521. [5] M.K. Maggs, S.G. O’Keefe, D.V. Thiel, Consensus Clock Synchronization for Wireless Sensor Networks, IEEE Sensors Journal.  12 (2012) 2269–2277. https://doi.org/10.1109/JSEN.2011.2182045. [6] O.N. Sherstyukov, A.I. Sulimov, R.R. Latypov, D.K. Nurgaliev, A.D. Smolyakov, Simulation of Short-Term Instability of UAV’s  Clock, in: 2021 Systems of Signal Synchronization, Generating and Processing in Telecommunications (SYNCHROINFO, 2021: pp.  1–8. https://doi.org/10.1109/SYNCHROINFO51390.2021.9488167. [7] J. Elson, L. Girod, D. Estrin, Fine-Grained Network Time Synchronization Using Reference Broadcasts, SIGOPS Oper. Syst.  Rev. 36 (2003) 147–163. https://doi.org/10.1145/844128.844143. [8] S. Ganeriwal, R. Kumar, M.B. Srivastava, Timing-Sync Protocol for Sensor Networks, in: Proceedings of the 1st International  Conference on Embedded Networked Sensor Systems, Association for Computing Machinery, New York, NY, USA, 2003: pp. 138– 149. https://doi.org/10.1145/958491.958508. [9] H. Dai, R. Han, TSync: A Lightweight Bidirectional Time Synchronization Service for Wireless Sensor Networks, SIGMOBILE  Mob. Comput. Commun. Rev. 8 (2004) 125–139. https://doi.org/10.1145/980159.980173. [10] R. Olfati-Saber, R.M. Murray, Consensus problems in networks of agents with switching topology and time-delays, IEEE  Transactions on Automatic Control. 49 (2004) 1520–1533. https://doi.org/10.1109/TAC.2004.834113. [11] L. Schenato, G. Gamba, A distributed consensus protocol for clock synchronization in wireless sensor network, in: 2007 46th  IEEE Conference on Decision and Control, 2007: pp. 2289–2294. https://doi.org/10.1109/CDC.2007.4434671. [12] J. He, P. Cheng, L. Shi, J. Chen, Y. Sun, Time Synchronization in WSNs: A Maximum-Value-Based Consensus Approach, IEEE  Transactions on Automatic Control. 59 (2014) 660–675. https://doi.org/10.1109/TAC.2013.2286893. [13] L. Schenato, F. Fiorentin, Average TimeSync: a consensus-based protocol for time synchronization in wireless sensor  networks1, IFAC Proceedings Volumes. 42 (2009) 30–35. https://doi.org/10.3182/20090924-3-IT-4005.00006. [14] M. Maróti, B. Kusy, G. Simon, Á. Lédeczi, The Flooding Time Synchronization Protocol, in: Proceedings of the 2nd  International Conference on Embedded Networked Sensor Systems, Association for Computing Machinery, New York, NY, USA,  2004: pp. 39–49. https://doi.org/10.1145/1031495.1031501. [15] F. Zhou, Q. Wang, D. Nie, G. Qiao, DE-Sync: A Doppler-Enhanced Time Synchronization for Mobile Underwater Sensor  Networks, Sensors. 18 (2018) 1710. https://doi.org/10.3390/s18061710. [16] J. Liang, K. Wu, An Extremely Accurate Time Synchronization Mechanism in Fog-Based Vehicular Ad-Hoc Network, IEEE  Access. 8 (2020) 253–268. https://doi.org/10.1109/ACCESS.2019.2958867. [17] Y. Jeon, T. Kim, T. Kim, Fast and Robust Time Synchronization with Median Kalman Filtering for Mobile Ad-Hoc Networks,  Sensors. 21 (2021). https://doi.org/10.3390/s21020590. [18] X. Zhang, H. Chen, K. Lin, Z. Wang, J. Yu, L. Shi, RMTS: A robust clock synchronization scheme for wireless sensor networks,  Journal of Network and Computer Applications. 135 (2019) 1–10. https://doi.org/10.1016/j.jnca.2019.02.028. [19] J. He, X. Duan, P. Cheng, L. Shi, L. Cai, Accurate clock synchronization in wireless sensor networks with bounded noise,  Automatica. 81 (2017) 350–358. https://doi.org/10.1016/j.automatica.2017.03.009.

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4486700

Preprint not peer reviewed

[20] G. Xiong, S. Kishore, Performance of Distributed Consensus Time Synchronization with Gaussian Delay in Wireless Sensor  Networks,  in:  2009  IEEE  Wireless  Communications  and  Networking  Conference,  2009:  pp.  1–5.  https://doi.org/10.1109/WCNC.2009.4917900. [21] B.J. Choi, H. Liang, X. Shen, W. Zhuang, DCS: Distributed Asynchronous Clock Synchronization in Delay Tolerant Networks,  IEEE Transactions on Parallel and Distributed Systems. 23 (2012) 491–504. https://doi.org/10.1109/TPDS.2011.179. [22] L. Li, Y. Liu, H. Yang, H. Wang, Lightweight Precision-Adaptive Time Synchronization in Wireless Sensor Networks, IEICE  Transactions. 93-B (2010) 2299–2308. https://doi.org/10.1587/transcom.E93.B.2299. [23] G. Xiong, S. Kishore, Discrete-Time Second-Order Distributed Consensus Time Synchronization Algorithm for Wireless Sensor  Networks, EURASIP J. Wirel. Commun. Netw. 2009 (2009). https://doi.org/10.1155/2009/623537. [24] P. Sommer, R. Wattenhofer, Gradient clock synchronization in wireless sensor networks, in: 2009 International Conference on  Information Processing in Sensor Networks, 2009: pp. 37–48. [25] R. Solis, V.S. Borkar, P.R. Kumar, A New Distributed Time Synchronization Protocol for Multihop Wireless Networks, in:  Proceedings of the 45th IEEE Conference on Decision and Control, 2006: pp. 2734–2739. https://doi.org/10.1109/CDC.2006.377675. [26] Y. Kim, L.-A. Phan, T. Kim, J. Lee, J.-H. Ham, Adaptive Gradient Time Synchronization Protocol in Wireless Ad-hoc Networks,  Journal of Institute of Control, Robotics and Systems. 25 (2019) 1116–1123. https://doi.org/10.5302/J.ICROS.2019.19.0162. [27] K.S. Yildirim, A. Kantarci, External Gradient Time Synchronization in Wireless Sensor Networks, IEEE Transactions on Parallel  and Distributed Systems. 25 (2014) 633–641. https://doi.org/10.1109/TPDS.2013.58. [28] E. Garone, A. Gasparri, F. Lamonaca, Clock synchronization protocol for wireless sensor networks with bounded  communication delays, Automatica. 59 (2015) 60–72. https://doi.org/10.1016/j.automatica.2015.06.014. [29] R. Carli, S. Zampieri, Network Clock Synchronization Based on the Second-Order Linear Consensus Algorithm, IEEE  Transactions on Automatic Control. 59 (2014) 409–422. https://doi.org/10.1109/TAC.2013.2283742. [30] S. Bolognani, R. Carli, E. Lovisari, S. Zampieri, A Randomized Linear Algorithm for Clock Synchronization in Multi-Agent  Systems, IEEE Transactions on Automatic Control. 61 (2016) 1711–1726. https://doi.org/10.1109/TAC.2015.2479136. [31] W. Masood, J.F. Schmidt, G. Brandner, C. Bettstetter, DISTY: Dynamic Stochastic Time Synchronization for Wireless Sensor  Networks, IEEE Transactions on Industrial Informatics. 13 (2017) 1421–1429. https://doi.org/10.1109/TII.2016.2618348. [32] F. Wang, X. Wu, Y. Pang, C. Yu, Y. Hu, X. Liu, A time synchronization method of Wireless Sensor Networks based on the  simulated annealing algorithm, in: The 26th Chinese Control and Decision Conference (2014 CCDC), 2014: pp. 870–875.  https://doi.org/10.1109/CCDC.2014.6852286. [33] Y. Qiu, Q. Zhang, S. Gao, Precision Time and Frequency Joint Synchronization Protocol for Wireless Ad Hoc Networks, in:  2020  IEEE  3rd  International  Conference  on  Electronics  Technology  (ICET),  2020:  pp.  770–775.  https://doi.org/10.1109/ICET49382.2020.9119692. [34] J.A. Ansere, G. Han, H. Wang, A Novel Reliable Adaptive Beacon Time Synchronization Algorithm for Large-Scale Vehicular  Ad Hoc Networks, IEEE Transactions on Vehicular Technology. 68 (2019) 11565–11576. https://doi.org/10.1109/TVT.2019.2946225. [35] G. Werner-Allen, G. Tewari, A. Patel, M. Welsh, R. Nagpal, Firefly-Inspired Sensor Network Synchronicity with Realistic Radio  Effects, in: Proceedings of the 3rd International Conference on Embedded Networked Sensor Systems, Association for Computing  Machinery, New York, NY, USA, 2005: pp. 142–153. https://doi.org/10.1145/1098918.1098934. [36] C. Liu, H. Pang, N. Cao, Research on Time Synchronization Technology of Wireless Sensor Network, in: 2017 International  Conference  on  Cyber-Enabled  Distributed  Computing  and  Knowledge  Discovery  (CyberC),  2017:  pp.  391–394.  https://doi.org/10.1109/CyberC.2017.67. [37] M. Cao, A.S. Morse, B.D.O. Anderson, Reaching a Consensus in a Dynamically Changing Environment: Convergence Rates,  Measurement Delays, and Asynchronous Events, SIAM Journal on Control and Optimization. 47 (2008) 601–623.  https://doi.org/10.1137/060657029. [38] N.J. Kasdin, T. Walter, Discrete simulation of power law noise (for oscillator stability evaluation), in: Proceedings of the 1992  IEEE Frequency Control Symposium, 1992: pp. 274–283. https://doi.org/10.1109/FREQ.1992.270003. [39] A. Harting, Considering clock errors in numerical simulations, IEEE Transactions on Instrumentation and Measurement. 45  (1996) 715–720. https://doi.org/10.1109/19.494587. [40] Y. Xu, Q. Chang, Z. Yu, On new measurement and communication techniques of GNSS inter-satellite links, Science China  Technological Sciences. 55 (2012) 285–294. [41] Z.-T. Qiao, C. Xu, Research on the Technology of Wireless Time Synchronization System, in: 2020 Cross Strait Radio Science &  Wireless Technology Conference (CSRSWTC), 2020: pp. 1–2. https://doi.org/10.1109/CSRSWTC50769.2020.9372593. [42] X. Gu, Q. Chang, Y. Xu, D. Wang, Time synchronization and ranging under unknown positions and velocities, Science China  Technological Sciences. 60 (2017) 271–281. [43] Y. Guo, S. Gao, Y. Bai, Z. Pan, Y. Liu, X. Lu, S. Zhang, A New Space-to-Ground Microwave-Based Two-Way Time  Synchronization Method for Next-Generation Space Atomic Clocks, Remote Sensing. 14 (2022). https://doi.org/10.3390/rs14030528.

This preprint research paper has not been peer reviewed. Electronic copy available at: https://ssrn.com/abstract=4486700
