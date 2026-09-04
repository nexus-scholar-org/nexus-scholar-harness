---
workspace_id: SCI-001480
doi: 10.1109/metroagrifor66923.2025.11512335
title: Vision-Based UAV Navigation in Vineyards using a Disturbance-Aware NMPC
authors:
- family_name: Enrico
  given_name: Riccardo
  orcid: null
- family_name: Ricioppo
  given_name: Petre
  orcid: null
- family_name: Primatesta
  given_name: S.
  orcid: null
- family_name: Mancini
  given_name: M.
  orcid: null
- family_name: Capello
  given_name: Elisa
  orcid: null
year: 2025
extraction_engine: pymupdf
extracted_at: '2026-09-04T09:51:42.330700+00:00'
---

# Vision-Based UAV Navigation in Vineyards using a Disturbance-Aware NMPC

Vision-Based UAV Navigation in Vineyards using a Disturbance-Aware NMPC

2025 IEEE International Workshop on Metrology for Agriculture and Forestry (MetroAgriFor) | 979-8-3315-5486-6/25/$31.00 ©2025 IEEE | DOI: 10.1109/MetroAgriFor66923.2025.11512335

Riccardo Enrico Petre Ricioppo Stefano Primatesta Mauro Mancini Elisa Capello Department of Mechanical and Aerospace Engineering, Politecnico di Torino

Corso Duca degli Abruzzi 24, 10129 Torino, Italy riccardo.enrico@polito.it petre.ricioppo@polito.it stefano.primatesta@polito.it mauro.mancini@polito.it elisa.capello@polito.it

providing fast and efficient monitoring of crop health, field boundaries, and soil variability [3], [4]. UGVs, in contrast, are designed for close-range ground operations that require precise and reliable point-to-point (P2P) navigation to physically interact with plants or soil [5], [6]. This direct contact is essential for tasks such as seeding, weeding, or localized treatment.


## Abstract—The increasing need for sustainable and efficient

agricultural practices has accelerated the adoption of autonomous
systems within the framework of Agriculture 4.0. In this context,
Unmanned Aerial Vehicles (UAVs) emerge as powerful tools for
precision viticulture, especially in monitoring and intervention tasks
along structured environments such as vineyard rows. However,
two key challenges persist: unreliable GPS data in rural areas and
vulnerability to environmental disturbances like wind. This paper
presents a vision-enhanced navigation and control strategy for UAV
row-following missions. A computer vision system integrates with
onboard GPS to improve localization accuracy based on real-time
visual feedback. To ensure robust path tracking, a Nonlinear
Model Predictive Control (NMPC) scheme is adopted, augmented
by a High-Order Sliding Mode (HOSM) disturbance observer
to mitigate the effects of external perturbations. The proposed
approach is validated through extensive Software-in-the-Loop
(SITL) and Processor-in-the-Loop (PITL) simulations in a
Gazebo-PX4 environment. Results show significant improvements
in tracking performance and robustness compared to the standard
PX4 PID controller, while confirming real-time feasibility for
embedded deployment in precision agriculture missions.

This paper addresses autonomous navigation of UAVs in viti- culture, with a focus on tasks requiring precise row-following in vineyards. Two main challenges are tackled: (i) accurate estimate of the row position relative to the UAV, and (ii) robust rejection of external disturbances, such as wind, that affect vehicle dynamics.

To overcome the first challenge, a vision-based navigation system is proposed to complement the onboard GPS. In rural environments, GPS signals are often unreliable, and discrepancies may occur between the map used at the ground station and the ac- tual row position [7]. The proposed approach leverages real-time visual data to enhance localization accuracy and ensure reliable guidance even when GPS coverage is poor, the proposed algo- rithm was first developed in [8] and further enhanced in this work.

Index Terms—Precision agriculture, Vineyard row-following, Sliding mode observer, UAV trajectory tracking, Robust control

To address the second challenge, a trajectory tracking controller based on Nonlinear Model Predictive Control (NMPC) [9], enhanced with a High-Order Sliding Mode (HOSM) disturbance observer [10], was developed. In precision agriculture missions, even small deviations from the reference path can significantly degrade task execution. The proposed control scheme improves tracking performance in the presence of wind disturbances.

I. INTRODUCTION

In recent years, agriculture has become increasingly central to global food security, amid growing urbanization, increased population, and shrinking arable land [1]. To address these challenges, the concept of Agriculture 4.0 has emerged, integrating advanced technologies to increase productivity while minimizing environmental impact. A pivotal element in this paradigm is Precision Agriculture, which utilizes the Internet of Things (IoT), artificial intelligence (AI), and robotics to enhance the efficacy of crop management. The IoT and AI facilitate monitoring and data analysis, while robotic systems automate tasks such as seeding, targeted treatment, and harvesting, thereby contributing to more efficient and sustainable food production [2].

In particular, the NMPC framework provides a systematic way to incorporate nonlinear UAV dynamics, actuator constraints, and state limits directly into the control problem [11], [12]. By solving a constrained finite-horizon optimization problem at each time step, NMPC is able to anticipate the future evolution of the system and adjust control inputs accordingly [13]. Efficient implementations leveraging tools such as CasADi and Acados—already demonstrated in UAV applications by [13]—further enable real-time deployment of NMPC on embedded platforms [14]. Moreover, the modular formulation of NMPC allows the integration of disturbance observers, such as HOSM in this case, without altering the optimization structure, thereby combining robustness with predictive accuracy.

In this context, Unmanned Aerial Vehicles (UAVs) and Unmanned Ground Vehicles (UGVs) offer complementary capabilities. UAVs are well suited for large-scale aerial surveys,

This study was carried out within the “National Research Centre for Agricultural Technologies – AGRITECH” and received funding from the European Union Next-GenerationEU (PIANO NAZIONALE DI RIPRESA E RESILIENZA (PNRR) – MISSIONE 4 COMPONENTE 2, INVESTIMENTO 1.4 – Avviso n. 3138 del 16/12/2021, Codice Programma CN00000022). This manuscript reflects only the authors’ views and opinions, neither the European Union nor the European Commission can be considered responsible for them.

This study builds on the work presented in [8], which employed the default PX4 PID controller for UAV trajectory tracking [15]. Although widely adopted, this baseline strategy often shows limited effectiveness in rejecting external perturbations, compromising tracking accuracy in agricultural settings.

This publication is part of the project PNRR-NGEU which has received funding from the MUR – DM 117/2023.

By introducing a more advanced control architecture, the present contribution overcomes these limitations and ensures

Additionally, this research was carried out in the frame of project ”4IPLAY”, funded within Programme PRIN, Project ID: 20228KBR5R.

389

979-8-3315-5486-6/25/$31.00 ©2025 IEEE

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:47:04 UTC from IEEE Xplore.  Restrictions apply.

higher reliability in tasks requiring strict path adherence.

a point cloud of the environment. The terrain plane is first identified and flattened using the RANSAC algorithm. Then, the modified point cloud is processed with OpenCV to detect the vineyard row and compute its centroid. A Kalman filter is applied to smooth the row position estimates before passing them to the NMPC controller. This approach is computationally efficient and suitable for real-time onboard operation.

Finally, the proposed control strategy is validated through extensive simulations conducted in both a custom Python-based dynamical model and a high-fidelity Gazebo environment integrated with the PX4 Autopilot. The evaluation includes Software-in-the-Loop (SITL) and Processor-in-the-Loop (PITL) configurations, which are widely adopted methodologies for test- ing control algorithms in realistic conditions before deployment [16], [17]. Results, in Section III, highlight the superior tracking accuracy and disturbance rejection capabilities of the NMPC- based controller paired with the disturbance observer compared to the baseline PX4’s PID implementation. Furthermore, PITL testing (Section III-D) confirms the computational efficiency and real-time feasibility of the proposed algorithm on embedded UAV hardware, supporting its applicability for onboard deployment in precision-critical missions.

For further implementation details, the reader is referred to our previous work [5].

C. Control Stack

This section presents the control architecture, which encom- passes an NMPC-based trajectory controller operating as the outer loop of the UAV control stack, thereby sending angular rates and collective thrust commands to the inner-loop attitude controller. The inner loop is implemented using the default PID controller from the PX4 Autopilot, which converts these references into low-level motor commands by generating the appropriate PWM signals for each propeller. The control stack is completed by a high-order sliding mode (HOSM) disturbance observer, based on Levant’s differentiator. Its purpose is to estimate external distur- bances (primarily wind) that affect the UAV dynamics. The esti- mated disturbance is then fed to the NMPC controller, enabling compensation and enhancing trajectory tracking performance in the presence of model uncertainties and external perturbations.

II. METHODOLOGY This section presents the methodology used to develop and validate a robust UAV navigation system for tracking vineyard rows. The control architecture, implementation details, simulation configuration and software architecture are also described, with the aim of ensuring accurate and disturbance-resistant trajectory tracking.

A. Mathematical model of the UAV

The UAV dynamical model treats the quadrotor as a rigid body with mass m and inertia tensor J, the values of which are based on the Holybro X500 quadcopter. The 3-dimensional motion of the UAV is described using a body-fixed frame FB (attached to the UAV) and an inertial world frame FI (fixed in space). The rotational motion of FB relative to FI is represented by the attitude quaternion q∈R4 and the angular velocity ω ∈R3. The translational motion is described by the position vector p ∈R3 and the linear velocity v ∈R3, which represent the position and velocity of the origin of FB with respect to the origin of FI. Then, the time evolution of the UAV state variables is governed by the following model:

The following subsections provide a detailed description of the control strategies and the UAV dynamic model employed for the controller design, a graphical visualization of the architecture is presented in Figure 1.

1) NMPC: The control output of the NMPC-based outer-loop is given by u=[Td,ωd]T ∈R4, where Td ∈R, ωd ∈R3 are the desired collective thrust and desired angular rate of the UAV, respectively. To compute u, the NMPC considers a reduced state vector x = [p,v,q]T ∈R10, where p,v, and q are as described above, and solves an optimal control problem by minimizing the following cost function J over the prediction horizon N:

2q⊙ 



N−1 X



 

0 ω

Q+∥uk−uref,k∥2

∥xk−xref,k∥2

min x(·),u(·)J =

˙p=v, ˙q= 1

,

R

(1)

k=0

˙v= 1

mR(q)Ft+g+d, ˙ω=J−1(τ −ω×Jω),

+∥xN −xref,N∥2

P subject to:

where R(q) rotates the thrust vector Ft =[0,0,T]T ∈R3 from body coordinates to world coordinates, and T ∈R is the collective thrust provided by the propellers. The other terms are the gravita- tional acceleration vector g=[0,0,−9.81]∈R3, and the external disturbance forces d∈R3 due to the wind. The dynamical model in Eq. (1) was initially implemented in Python to carry out preliminary tests and tune the control strategy in a simplified environment, free from noise and other non-idealities. This allowed for an initial validation of the controller’s performance in a controlled setting. Subsequently, the final simulations were performed in the Gazebo environment, which enables a more accurate representation of real-world conditions and serves as a more realistic validation step prior to actual flight tests [17].

1) System Dynamics: xk+1 =f(xk,uk) 2) Control Input Constraints: umin ≤uk ≤umax 3) Initial State Constraint: xk =x0 Here, xk and uk represent the predicted state and control input at time step k. The terms xref,k and uref,k are the reference state and control trajectories, respectively. The matrices Q, R, and P are positive semidefinite weighting matrices that penalize deviations from the reference trajectory for the stage, control input, and terminal state, respectively. The constraints on uk ensure that the control inputs remain within the physical limits of the hardware. The function f(xk,uk) represents the nonlinear dynamics model of the quadrotor, and is taken from Eq. (1). In this context, the disturbance term d in Eq. (1) is not modeled as an unknown input, but rather as a known input estimated online by the HOSM observer, and injected into the NMPC model to improve prediction accuracy and trajectory tracking performance.

B. Vineyard Row Detection

The vision-based vineyard-following method, originally developed in [8], is summarized here and reused in this work. The algorithm relies on the onboard depth camera to acquire

390

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:47:04 UTC from IEEE Xplore.  Restrictions apply.

Fig. 1: The complete control architecture diagram.

2) Disturbance observer: To enhance the robustness of the NMPC against external disturbances such as wind, a High-Order Sliding Mode (HOSM) disturbance observer, based on Levant’s robust differentiator [18], is implemented. This observer estimates the wind disturbances affecting the UAV dynamics. Based on Eq. (1), the extended state observer is constructed as follows:

(SQP-RTI) scheme, for its fast, embedded solutions tailored to nonlinear control. A Python script leverages acados’ automatic code generation to produce optimized C code, which is then executed within a Python ROS 2 (rclpy) node using the acados Python API. This process seamlessly integrates the NMPC into the ROS 2 framework.

˙ˆv= ˆd+ 1

mR(q)T +g−3.34(k3L)1/3|ev|2/3sgn(ev) (2a)

E. Hardware integration

˙ˆd= ¨ˆd−5.3(k3L)2/3|ev|1/3sgn(ev) (2b) ¨ˆd=−k3L·sgn(ev) (2c) The dynamics of the observer are driven by the velocity estimation error ev = ˆv−v, which is obtained as the difference between the observer values ˆv and the measured velocity v. Based on this value, the observer estimates the disturbance force d and its rate of change ˙d. Since Eqs. (2) are discontinuous, their solutions are understood in the sense of Filippov [19] The parameters k3 and L are the observer gains that govern the disturbance estimation dynamics. To ensure proper disturbance estimation (i.e., ˆd→d), these gains must satisfy L>∥¨d∥∞and k3 >L. For the observer implementation, we select k3 =1.0 and L=0.5, which satisfy these conditions. Following the analysis in [10], this parameter selection guarantees finite-time stability of the observation errors in the absence of measurement noise. The observer is implemented in discrete time using a 4th-order Runge-Kutta (RK4) integrator. The estimated disturbance ˆd is then fed back into the UAV dynamic model used by the NMPC.

The experimental platform consists of a Mavtech RX2 quadcopter, similar to the X500 used in simulations. The UAV employs a two-tiered computational architecture to ensure safety and performance. A PX4-based Pixhawk 6c flight controller handles low-level control functions, while an onboard Jetson Orin Nano companion computer executes computationally intensive high-level algorithms, including computer vision and NMPC. Processor-in-the-loop (PITL) validation is performed on the companion computer.

III. RESULTS

Each standalone component of the control stack has been evaluated independently to ascertain its performance in comparison to standard modules.

A. Control algorithm

The disturbances are estimated by this external module and fed to the NMPC controller as shown in Figure 1. As previously discussed, these disturbances are taken into account by the dynamical model employed in the controller.

To test our NMPC controller, we compared it against the standard PX4 PID controller [8] in a Gazebo simulation. We had them both follow a figure-8 trajectory, as shown in Figure 2, first in calm conditions and then with a steady 7.5 m/s wind applied to both the x and y axes using the PX4 wind plugin. This allowed us to directly compare their tracking performance, especially when faced with external disturbances. The results of the tracking are presented in Table I.

D. Software implementation

All algorithms are integrated through the Robot Operating System 2 (ROS 2), which facilitates seamless communication between different programming languages (e.g., Python, C++) and has become the standard in academic robotics applications. The control algorithms, executed on the companion computer, are implemented as independent ROS 2 nodes that interface with the PX4 Autopilot (which remains unchanged and provides low-level control) via the uXRCE-DDS bridge. In our cascaded architecture (see Figure 1), a position controller drives an attitude controller, with data exchanged through ROS 2 topics.

TABLE I: Comparison of RMSE Values for PID and NMPC under Different Conditions

Condition Component PX4 Controller RMSE (m) NMPC RMSE (m) No Wind x 0.5605 0.2360 y 0.5306 0.3084 z 0.8396 0.2175 Wind Enabled x 0.8728 0.5602 y 0.8739 0.6314 z 0.7285 0.3341

For the NMPC, we utilize the acados package, employing a Sequential Quadratic Programming Real-Time Iteration

391

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:47:04 UTC from IEEE Xplore.  Restrictions apply.

velocity of the UAV and disturbance acting on it, as detailed in Table II. The simulation employs sinusoidal wind disturbances of 2.0 N at 0.5 rad/s (X-axis), 1.5 N at 0.3 rad/s (Y-axis), and 1.0 N at 0.8 rad/s (Z-axis). For a quadrotor mass of 1.5 kg, these yield maximum accelerations of 1.33 m/s2, 1.0 m/s2, and 0.67 m/s2, respectively. In the clean scenario, the observer exhibits excellent performance, with very low RMSE values across all estimated states. When zero-mean Gaussian noise is added directly to the disturbance signals with standard deviations of 0.2 N, 0.15 N, and 0.1 N for the X, Y, and Z axes respectively (representing 10% of each signal’s amplitude), the RMSE for all estimates increases, as expected. Notably, as indicated by the results in Figure 3 and Table II, the velocity and disturbance estimation performance worsens with noise as expected, though the estimates remain reasonably accurate in the noisy disturbance environment.

TABLE II: HOSM Observer RMSE Performance

Fig. 2: NMPC 3D trajectory tracking performance.

Metric Clean RMSE Noisy RMSE

Velocity Estimation (ms−1) X-axis 0.0095 0.0124 Y-axis 0.0065 0.0072 Z-axis 0.0001 0.0016

B. Disturbance observer

The disturbance observer is validated in a Python simulation featuring the UAV dynamical model presented in Subsection II-A. A fundamental assumption in the design of the observer is that these disturbances acting on the system are unknown.

Wind Disturbance Estimation (ms−2) X-axis 0.0109 0.1347 Y-axis 0.0068 0.1015 Z-axis 0.0063 0.0719

1) Noisy measurements: The disturbance estimator’s performance depends on velocity measurements from PX4’s EKF2, which can be affected by noise. We therefore test the observer under both ideal and realistic conditions. While this subsection presents Python-based simulation results, the next subsection demonstrates the PX4 SITL implementation with Gazebo simulation and in pairing with the NMPC. The real implementation of the HOSM observer will rely on PX4’s EKF2 for velocity measurements.

2) Different wind gust profiles: To assess the effectiveness of the HOSM observer in identifying disturbances, tests are performed under four wind types: constant, sinusoidal, random, and gusty. Each profile is generated using the wind disturbance model with specific parameters: a base amplitude of about 1.2–1.5 m/s, sinusoidal components with frequencies of 0.05–0.15 Hz and phase shifts, random fluctuations scaled by Gaussian noise, and in the gusty case, additional gusts with amplitude up to 2 m/s and turbulence of 0.3 m/s. Table III summarizes the tracking errors and wind characteristics for each case. In this case, the RMSE is computed over all three directions, rather than on a single coordinate as in the previous subsection.


> **Figure 3 shows the observer successfully tracking time-varying**

> wind disturbances. The estimator accurately follows the true
disturbance values along all axes with minimal delay.

TABLE III: HOSM performance in estimating the wind under different wind profiles.

Wind Type HOSM RMSE [m/s2] Avg Wind [m/s2] Max Wind [m/s2] Constant 0.2329 1.6994 1.7037 Sinusoidal 0.2621 1.4859 2.1317 Random 1.2187 1.6010 3.1745 Gusty 0.5290 1.5232 2.6478


> **Table III reports the observer’s performance in tracking**

> different wind profiles, which are depicted in Figure 4. In the
following subsection, the observer is evaluated jointly with the
NMPC, as shown in Figure 1. The RMSE values in Table IV
refer to the complete control architecture, encompassing both
the NMPC and the observer.

C. Control stack - NMPC and Disturbance observer

Fig. 3: Wind disturbance tracking performance of the HOSM Disturbance observer.

1) Model Based Simulation - Python: In this subsection, a comparison table is presented to evaluate the effectiveness of HOSM in conjunction with NMPC under different wind profile types. This evaluation is conducted using a Python-based model

To quantify the observer’s performance, the Root Mean Square Error (RMSE) was calculated for the estimation of

392

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:47:04 UTC from IEEE Xplore.  Restrictions apply.

(a) Trajectory without HOSM observer.

(b) Trajectory with HOSM observer.

Fig. 5: Comparison of the UAV’s trajectory following a lawnmower path. The path without the Higher-Order Sliding Mode (HOSM) observer is shown in (a), while the improved tracking performance with the observer enabled is shown in (b).

closer to its intended path when the observer is enabled. By incorporating disturbance estimation into the NMPC framework, the system becomes notably more robust against wind and other external forces that would otherwise push the drone off course.

Fig. 4: Illustration of the different wind profiles and the corresponding performance of the observer in tracking them across all XYZ directions.

D. Processor in the Loop testing

Following the implementation and validation of the control stack on a workstation PC, the algorithms were further validated on UAV hardware. Given that NMPC is the most computationally intensive module of the control stack, its performance validation was conducted on both the workstation PC and the embedded Jetson Orin Nano mounted on the actual UAV.

simulation, since Gazebo currently supports only a constant wind profile, while the other profiles had to be validated through the Python simulation. Section III-B show how the disturbance observer performs under different wind profiles.

TABLE VI: NMPC Solver Time Statistics

The results highlight that the integration of the disturbance observer significantly improves tracking accuracy for constant, sinusoidal, and gusty wind profiles, reducing the RMSE by more than 48% in all cases. The most notable improvement is under constant wind, where the RMSE decreases by about 55%. However, in the random wind scenario, the observer provides only a marginal improvement, reducing the RMSE by about 5%. This suggests that while the observer is effective for structured wind profiles, its performance is less robust under highly irregular and unpredictable disturbances.

Platform Mean (ms) Upper Bound (ms) Std Dev (ms) Sample Size Workstation PC 0.54 0.63 0.03 1821 Jetson Orin Nano 11.04 13.13 0.68 1968

As shown in Table VI, the workstation PC naturally excels with a computation time of just 0.54 ms, while the embedded Jetson Orin Nano still delivers solid real-time performance at an average of 11.04 ms. Both platforms showed consistent behavior across nearly 2000 data points, with very little variation in execution times. What is particularly encouraging is that even the Jetson’s worst-case time of 13.13 ms stays well under our 20 ms constraint for 50 Hz UAV control frequency, which means this control stack can actually run on the target drone hardware without computational issues.

2) Gazebo Simulation: Figure 1 shows the control architecture combining a HOSM disturbance observer with NMPC. The NMPC uses disturbance estimates from the observer as constant values over each prediction horizon.

We implemented this integrated framework as a ROS 2 node and tested it in Gazebo simulation, following the methodology from Section II-D. The complete control stack ran in Software-in-the-Loop (SITL) simulation with PX4 Autopilot. To evaluate performance under external disturbances, we introduced a constant horizontal wind field using PX4’s wind plugin, with velocity components vx =7.5m/s and vy =7.5m/s.

E. Power draw

The NMPC was tested on both an NVIDIA Jetson Orin Nano and an NVIDIA Jetson Xavier NX, the latter offering the possi- bility to adjust the power budget (from 10 W to 20 W) to improve computational performance. Results indicate that doubling the allocated power reduces the NMPC solver time by approximately 3.9 ms, corresponding to an increase of about 40 Hz in the achiev- able solution rate1. The typical load for a lighter, smaller quadro- tor is ≈200 W [20] and from telemetry data on the Mavtech RX2 onboard electrical load is slightly below 300 W, the additional 10 W required for faster computation has a negligible impact on

The experimental validation of the integrated NMPC-HOSM control stack shows clear improvements in how well the drone follows its planned path when dealing with wind disturbances. The data in Table V suggest that adding the HOSM disturbance observer reduces tracking errors by 63% along the x-axis and 49% along the y-axis during lawnmower pattern flights under constant wind conditions. The visual comparison in Figure 5 makes this improvement obvious - as the drone stays much

1Comparison between 1.2 GHz/4 cores and 1.9 GHz/2 cores, with doubled power draw.

393

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:47:04 UTC from IEEE Xplore.  Restrictions apply.

TABLE IV: Summary of RMSE results under different wind conditions.

Wind Type No Obs RMSE [m] With Obs RMSE [m] Obs RMSE Change (%) Constant 0.7239 0.3246 -55.2 Sinusoidal 0.5342 0.2739 -48.7 Random 0.3351 0.3181 -5.1 Gusty 0.6930 0.3202 -53.8

TABLE V: Root Mean Square Error (RMSE) for the Lawnmower Path.

[5] P. Ricioppo, M. Mancini, and E. Capello, “Learning-based artificial

potential field path planning for agricultural ugvs,” in 2024 IEEE International Workshop on Metrology for Agriculture and Forestry (MetroAgriFor), 2024, pp. 301–306. [6] P. Ricioppo, D. Celestini, and E. Capello, “Generalization of reinforcement

Trajectory HOSM State RMSE (x) [m] RMSE (y) [m]

Disabled 0.189 0.304 Enabled 0.070 0.154

learning through artificial potential fields for agricultural ugvs,” in 2023 IEEE International Workshop on Metrology for Agriculture and Forestry (MetroAgriFor), 2023, pp. 386–391. [7] F. Rovira-M´as, I. Chatterjee, and V. S´aiz-Rubio, “The role of

Lawnmower

Improvement -63% -49%

gnss in the navigation strategies of cost-effective agricultural robots,” Computers and Electronics in Agriculture, vol. 112, pp. 172–183, 2015, precision Agriculture. [Online]. Available: https://www.sciencedirect.com/science/article/pii/S0168169914003275 [8] R. Enrico, P. Ricioppo, M. Mancini, and S. Primatesta, “Computer

flight endurance, while yielding a noticeable improvement in con- trol responsiveness. This trade-off is particularly advantageous in missions demanding rapid trajectory tracking, supporting the suit- ability of embedded NMPC for precision agriculture applications.

vision-based autonomous navigation for uav vineyard row following,” in 2024 IEEE International Workshop on Metrology for Agriculture and Forestry (MetroAgriFor), 2024, pp. 551–556. [9] L. Grne and J. Pannek, Nonlinear Model Predictive Control: Theory and

IV. CONCLUSION

Algorithms. Springer Publishing Company, Incorporated, 2013. [10] J. A. Moreno, “Levant’s arbitrary order differentiator with varying gain,”

This paper presents an enhanced UAV navigation and control framework specifically designed to reject disturbances that may be present in an environment such as a vineyard, primarily wind. Building on our previous vision-based guidance work [8], we integrate a disturbance-aware NMPC with an HOSM observer. This combination effectively handles external wind disturbances that can affect UAVs in maintaining precise following of the vineyard row.

IFAC-PapersOnLine, vol. 50, no. 1, pp. 1705–1710, 2017. [11] M. Kamel, M. Burri, and R. Siegwart, “Linear vs nonlinear mpc

for trajectory tracking applied to rotary wing micro aerial vehicles,” IFAC-PapersOnLine, vol. 50, no. 1, pp. 3463–3469, 2017. [12] D. Hanover, P. Foehn, S. Sun, E. Kaufmann, and D. Scaramuzza,

“Performance, precision, and payloads: Adaptive nonlinear MPC for

quadrotors,” IEEE Robotics and Automation Letters, vol. 7, no. 2, pp. 690–697, Apr. 2022. [13] B. B. Carlos, T. Sartor, A. Zanelli, G. Frison, W. Burgard, M. Diehl, and G. Oriolo, “An efficient real-time NMPC for quadrotor position control under communication time-delay,” in 2020 16th International Conference on Control, Automation, Robotics and Vision (ICARCV). IEEE, Dec. 2020. [Online]. Available: https://www.diag.uniroma1.it/ labrob/pub/papers/ICARCV20.pdf [14] R. Verschueren, G. Frison, D. Kouzoupis, J. Frey, N. van Duijkeren,

We evaluated our proposed control framework through both SITL and PITL approaches and with Python based and Gazebo simulations. The results demonstrate significant improvements in both trajectory tracking accuracy and disturbance rejection compared to the standard PX4’s PID controller and standalone NMPC approaches. Moreover, our tests on real hardware confirm that this advanced control stack operates in real-time on embedded hardware platforms, thus validating its practicality.

A. Zanelli, B. Novoselnik, T. Albin, R. Quirynen, and M. Diehl, “acados—a modular open-source framework for fast embedded optimal control,” Mathematical Programming Computation, vol. 14, pp. 147–183, 2022. [15] L. Meier, D. Honegger, and M. Pollefeys, “Px4: A node-based multithreaded

open source robotics framework for deeply embedded platforms,” in 2015 IEEE International Conference on Robotics and Automation (ICRA). Piscataway, NJ: IEEE, 2015, Conference Paper, pp. 6235 – 6240, 2015 IEEE International Conference on Robotics and Automation (ICRA); Conference Location: Seattle, WA, USA; Conference Date: May 26-30, 2015. [16] S. Macenski, T. Foote, B. Gerkey, C. Lalancette, and W. Woodall, “Robot

This work represents an important step toward achieving more reliable and precise autonomous operations in precision viticulture. Future work will focus on real-world flight validation, comparison with other adaptive control strategies that can dynamically respond to changing environmental conditions, and exploration of GPU-based implementations such as Model Predictive Path Integral (MPPI) control [21] for enhanced computational performance on hardware such as the Jetson.

operating system 2: Design, architecture, and uses in the wild,” Sci. Robot., vol. 7, no. 66, p. eabm6074, May 2022. [Online]. Available: https://www.science.org/doi/10.1126/scirobotics.abm6074 [17] C. A. Dimmig, G. Silano, K. McGuire, C. Gabellieri, W. H¨onig, J. Moore,

and M. Kobilarov, “Survey of simulators for aerial robots: An overview and in-depth systematic comparisons [survey],” IEEE Robot. Autom. Mag., vol. 32, no. 2, pp. 153–166, Jun. 2025. [Online]. Available: http://dx.doi.org/10.1109/MRA.2024.3433171 [18] A. Levant, “Higher-order sliding modes, differentiation and output-feedback


## REFERENCES

control,” International Journal of Control, vol. 76, no. 9-10, pp. 924–941, 2003. [Online]. Available: https://doi.org/10.1080/0020717031000099029 [19] A. F. Filippov, Differential equations with discontinuous righthand sides:

[1] N. Ramankutty, Z. Mehrabi, K. Waha, L. Jarvis, C. Kremen, M. Herrero,

and L. Rieseberg, “Trends in global agricultural land use: Implications for environmental health and food security,” Annual Review of Plant Biology, vol. 69, 04 2018. [2] A. Botta, P. Cavallone, L. Baglieri, G. Colucci, L. Tagliavini, and

control systems. Springer Science & Business Media, 2013, vol. 18. [20] P. Ganchaudhuri and C. Bhawal, “Power consumption of a quadrotor

based on maneuvers,” in 2023 IEEE Guwahati Subsection Conference (GCON), 2023, pp. 01–06. [21] R. Enrico, M. Mancini, and E. Capello, “Comparison of nmpc

G. Quaglia, “A review of robots, perception, and tasks in precision agriculture,” Applied Mechanics, vol. 3, no. 3, pp. 830–854, 2022. [Online]. Available: https://www.mdpi.com/2673-3161/3/3/49 [3] D. C. Tsouros, S. Bibi, and P. G. Sarigiannidis, “A review on uav-based

and gpu-parallelized mppi for real-time uav control on embedded hardware,” Applied Sciences, vol. 15, no. 16, 2025. [Online]. Available: https://www.mdpi.com/2076-3417/15/16/9114

applications for precision agriculture,” Information, vol. 10, no. 11, 2019. [Online]. Available: https://www.mdpi.com/2078-2489/10/11/349 [4] F. Toscano, C. Fiorentino, N. Capece, U. Erra, D. Travascia, A. Scopa,

M. Drosos, and P. D’Antonio, “Unmanned aerial vehicle for precision agriculture: A review,” IEEE Access, vol. 12, pp. 69 188–69 205, 2024.

394

Authorized licensed use limited to: Consortium - Algeria (CERIST). Downloaded on September 04,2026 at 09:47:04 UTC from IEEE Xplore.  Restrictions apply.
