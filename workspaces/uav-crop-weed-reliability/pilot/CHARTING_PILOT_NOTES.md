# Preliminary charting notes — codebook pilot on 2 full texts (NOT accepted charting)

**Status:** PRELIMINARY_ONLY. No `DOC-*` accepted IDs, no
`charting.schema.json` rows, no Contract registry entries. Evidence below cites
convenience files (`pdfs/*.pdf` + `extracted_prelim/*.md` with SHA256 in
`SOURCE_REGISTER.md`) by section/table/figure + verbatim quote. A future
accepted row must re-verify each quote against E1/E2-accepted bytes; schema
validation here would prove structure only, not entailment. **Zero accepted
studies, zero accepted evaluations.** Preliminary notes: 2 studies, 4
evaluation settings. Unresolved: S4 (no bytes).

**Sources inspected:** WeedsGalore arXiv v1 (preprint; IEEE final not diffed);
SemiWeedNet Frontiers Vor (single version). S4 not inspected beyond publisher
index (no charting). Locator convention: `WG §x / Tab.n / Fig.n / p.n` =
WeedsGalore preprint; `SWN §x / Tab.n / Fig.n` = SemiWeedNet publisher PDF.
Quotes are verbatim from the convenience extraction (line-breaks normalised).

**Interpretation safeguards applied throughout:** (a) dataset diversity ≠
external validation; (b) multitemporal imagery ≠ held-out temporal test; (c)
sensor inventory ≠ evaluated channels; (d) semi-supervised ≠ target-domain
adaptation; (e) combined field/year/growth-stage shift cannot isolate a sensor
or temporal effect; (f) structural validity ≠ entailment; (g) missing =
`unavailable`/`not_reported` explicitly, never inferred.

---

## STU-PRELIM-WG — WeedsGalore family (preliminary)

| Cell | State → value | Evidence (locator + quote) | Note |
|---|---|---|---|
| task | reported → `multiple` (semantic_segmentation + instance_segmentation) | WG §4.1.1 “The goal of semantic segmentation is to assign pixel-level class labels. We evaluate two settings: 3-class … and 6-class …” + WG §4.1.2 “We use MaskFormer to provide baseline results for instance segmentation … and report mAP …” | Two tasks on same dataset; future accepted rows chart settings separately. |
| method_family | reported → `deep_learning` | WG §4.1.1 “baselines using two different established architectures: DeepLabv3+ [8], and MaskFormer [10]” + WG §4.2 “probabilistic version of DeepLabv3+, by adding dropout layers …” | All evaluated methods are deep segmentation nets (ResNet50 backbone). No non-learning baseline evaluated. |
| report_type | reported → `mixed` (preprint + conference) | Header “accepted for publication at … WACV 2025. © IEEE” + “arXiv:2502.13103v1 [cs.CV] 18 Feb 2025”; Crossref `proceedings-article WACV 2025-02-26 pp.4767–4777` | Family links v1 preprint (inspected) + IEEE proceedings (not inspected). Most complete current = v1 inspected; do not double-count as two studies. |
| report_family | reported → narrative | Same as above + arXiv API “11 pages, 7 figures, 7 tables” vs preprint 7 tabs/6 figs observed | Discrepant claims retained: IEEE pagination vs preprint; no diff performed (unresolved). |
| dataset_provenance | reported → narrative | WG §3.1 “The field is located in Marquardt, Potsdam, Germany (52°27’50.6”N 12°57’27.5”E) and covers … ~1840m2 … maize (Zea mays L.) planted … May 9, 2023 … irrigation June 6 … Herbicide June 12” + WG §3.2 “divided the whole field into 12 patches … 48 locations … 36 annotated for first three dates … remaining 12 for all four dates … total ~128 m2 (per date)” + Tab.2 “Train 104 / Val 26 / Test 26 images; 2,169 crops / 10,031 weeds” + “4 large orthomosaics … large amount of unlabeled data” | Primary dataset report + method baselines in one family. Distinct primary experiment reusing another dataset (Maize2024 eval, PhenoBench/CropAndWeed comparators) does not merge studies; Maize2024 is an evaluation target, not a second included study. |
| crop_context | reported → narrative | Maize + 4 weeds (amaranth, barnyard grass, quickweed, weed other); “weeds occurred naturally … usual practices without experimental interference”; Fig.2 four dates (May 25 / May 30 / Jun 6 / Jun 15); late-stage Jun 15 “too late for herbicide application” but retained for mechanical/cover analysis | Field, crop, weed classes, natural infestation, dates, herbicide context all reported. Season = 2023 growing season (single season; not a multi-season design). |
| open_science | reported → narrative | Abstract “dataset and code are available at https://github.com/GFZ/weedsgalore” + §3.2 annotation “Encord [20] … SAM [37] point prompt … 156 images annotated by two annotators and mutually reviewed by three experts” | Code/data claimed available; license, retraction, funding/COI not checked in this pilot (unavailable — no Phase-4 streams run). |

### WG-E1 — in-domain semantic + instance benchmarks, clean (preliminary)

| Cell | State → value | Evidence | Note |
|---|---|---|---|
| setting_definition | reported | “Sec. 4.1.1 and 4.1.2 contain results for semantic and instance segmentation for different input data modalities” + “train DeepLabv3+ / MaskFormer on WeedsGalore spatial splits; test on held-out patches” | Clean in-domain setting; groups RGB vs MSI × 3-class/6-class × architecture. Repeated seeds grouped (none reported — see seeds). |
| sensor_bands | reported | “images taken with the DJI Phantom P4 Multispectral, a UAV equipped with five monochromic sensors (Blue: 450±16 nm, Green: 560±16, Red: 650±16, Red-Edge: 730±16, NIR: 840±26 nm) 2.08 MP + RGB sensor” + “test 3-channel (RGB) and 5-channel (MSI) inputs” + “changing the first convolutional layer to 5 input channels” | **Actual evaluated channels** are RGB vs MSI (5-ch). Sensor inventory ≠ proof of use is respected: only the tested 3/5-ch conditions are coded, not the full spec sheet. |
| split_unit | reported → `patch_or_tile` | §3.3 “We spatially split the data as 70:15:15 (i.e. 8/2/2 patches), such that images from the same location do not appear in more than one split, even if the data was recorded at a different date” + Fig.3 “splits are spatially separated by patches” | Spatial patch split; location-disjoint across splits even across dates. Not pixel/image random. |
| shift_axes | reported → `none` | In-domain test patches from same field/dates/sensor as train; no degradation/sensor/field/date shift in this setting | Dataset diversity (4 dates, 12 patches) is NOT external validation — coded none. |
| temporal_design | reported → `multiple_dates_no_heldout` | Fig.2/§3.2 four dates (May25–Jun15) present in train/val/test via spatial split; same locations sampled across dates; no date held out | Multitemporal imagery ≠ held-out temporal test (safeguard b). |
| target_data_use | reported → `none` | No adaptation/fine-tuning on test patches; “final parameters are chosen based on the validation set” (source-domain validation only) | Test patches are held-out for evaluation, not used for training/selection beyond standard val. |
| uncertainty_evaluation | reported → `none` (for this setting) | No UQ in §4.1; UQ lives in separate WG-E2 setting | Explicitly no calibration in benchmark setting; not conflated with WG-E2. |
| stress_origin | reported → `none` | No synthetic/observed stress in §4.1 | Clean vs stressed separated (WG-E3 is the stressed/OOD setting). |
| sensor_awareness | reported → `band_availability` | RGB-vs-MSI comparison (“additional NIR and RE bands consistently improve … most significant for quickweed and weed other … underrepresented classes”) | Band-subset experiment, not sensor-metadata conditioning or learned fusion as calibration. |
| group_counts | reported | Tab.2 train/val/test image + instance counts (104/26/26 images; per-class instances) + Tab.3/4/5 IoU/mAP numbers (e.g. Tab.3 DeepLabv3+ RGB mIoU 79.33 vs MSI 82.90; MaskFormer RGB 79.26 vs MSI 80.27; Tab.4 6-class MSI 55.52 vs RGB 50.81) | Units = images + plant instances; class-specific IoU preserved; no cross-dataset leaderboard implied. |
| metrics_and_controls | reported | “report IoU per class + mIoU” + “mAP [0.5:0.95] + mAP50/75” + “start with pre-trained ResNet50, Adam, batch 8, augmentation rotation/flipping/jitter, LR 0.001 / 0.00003, A100, params chosen on validation” + matched RGB/MSI controls per architecture | Comparators are within-study (architecture × input); PhenoBench/CropAndWeed comparators belong to WG-E3, not here. |
| transfer_result | reported | In-domain: MSI > RGB (Tab.3–5); “MSI boost highest for amaranth for MaskFormer, for barnyard grass/quickweed for DeepLabv3+”; confusion: “8% crops missed, 13% misclassified as weeds; weed errors almost entirely false negatives, especially small early-growth weeds”; “Quickweed classified as amaranth by 28% (broad-leaf similarity)” | Negative/limitation evidence preserved (small-weed false negatives, quickweed/amaranth confusion, weed-other pooling). |
| seeds_and_intervals | not_reported → null | Checked §§4.1–4.2, Tabs.3–6, Fig.4–5: no seeds, no CIs, no repeats reported | Silence is not zero; required note records inspected scope. |
| limitations | reported | Small-weed false negatives; quickweed/amaranth confusion; weed-other heterogeneity; instance mAP “overall lower … >78 plants/image … challenging, especially small weeds” | Author-stated + evidence-derived limits; no invented limits. |

### WG-E2 — in-domain probabilistic calibration (preliminary)

| Cell | State → value | Evidence | Note |
|---|---|---|---|
| setting_definition | reported | §4.2 “Variational Inference with MC dropout … predictive entropy as uncertainty metric” + “probabilistic DeepLabv3+ adding dropout pd=0.5 between each of four ResNet50 blocks; inference pd 0.5, K=5 forward passes” | Same spatial splits as WG-E1; only DeepLabv3+ 3-class tested probabilistically. |
| sensor_bands | reported | Tab.6 RGB + MSI rows (deterministic vs Prob. DLv3+) | Both modalities tested. |
| split_unit / shift_axes / temporal_design / target_data_use / stress_origin | reported → same as WG-E1 (`patch_or_tile` / `none` / `multiple_dates_no_heldout` / `none` / `none`) | Same data assignment; no new shift | Separate row because uncertainty treatment differs (codebook: separate clean vs stressed AND distinct UQ conditions). |
| uncertainty_evaluation | reported → `calibration_evaluated` | “report ECE … acc/conf per bin … deterministic softmax vs MC-dropout mean over K” + Tab.6 “ECE: RGB 0.0058→0.0041; MSI 0.0048→0.0018” + “probabilistic significantly better calibrated + consistently higher IoU” + Fig.5 “uncertainty high in misclassified regions … high correlation between error and high uncertainty” | Calibration measured (ECE), not merely attention/entropy display. Learned weights ≠ calibration is respected: ECE is the calibrating evidence. |
| sensor_awareness | reported → `band_availability` | Same RGB/MSI manipulation; “improvement in calibration most pronounced for MSI (ECE < half)” | No sensor-transfer claim. |
| group_counts / metrics_and_controls | reported | Tab.6 IoUcrop/IoUweed/mIoU + ECE per input × deterministic/probabilistic (e.g. MSI mIoU 82.90→82.94 with ECE halved) | Matched deterministic control per input. |
| transfer_result | reported | Calibration + small IoU gain; qualitative error–uncertainty correlation; “aleatoric at object borders … epistemic + aleatoric in soil/stone shadows” | Positive + mechanistic note; no selective-prediction/abstention experiment (not claimed). |
| seeds_and_intervals | not_reported → null | No K-sensitivity, seed, or ECE-interval analysis found in §4.2/Tab.6 | — |
| limitations | reported | K=5 only; single architecture (DeepLabv3+); 3-class only; no held-out calibration (in-domain ECE only); no abstention/cost analysis | Absent tests listed as data, not as exclusion. |

### WG-E3 — OOD Maize2024 combined-shift application (preliminary)

| Cell | State → value | Evidence | Note |
|---|---|---|---|
| setting_definition | reported | §4.3 “introduce additional test field Maize2024 … different field, year, plant cover, unseen (later) growth stages … domain shifts we expect” + “Marquardt, Potsdam … 12/24 control (no herbicide, full weed cover) + 12/24 test (sprayed, weeds eliminated) … same drone after treatment” + “annotate 6 cropped patches (~90 m2, 1000×1100px) for quantitative scores; Fig.6 full orthomosaic qualitative” | Direct-transfer application; 6-patch quantitative + orthomosaic qualitative. Training sets: WeedsGalore vs PhenoBench (same acquisition, different crop) vs CropAndWeed (maize incl., different acquisition) vs MaizeOrWeed subset (1753 maize-only). |
| sensor_bands | reported | “collected with the same drone” (P4 Multispectral lineage) for Maize2024; training inputs per-dataset (WeedsGalore MSI/RGB; comparators per their own sensors) | OOD sensor is same platform; shift is NOT a sensor shift — coded combined without sensor axis. |
| split_unit | reported → `field` (with `multiple` nuance) | Train on WeedsGalore field(s) → test on distinct Maize2024 field; 6 evaluation patches are measurement units within the held-out field | Split is by field; explanation records patch-level scoring inside the held-out field. Uses `field` + definition note (not bare `multiple`). |
| shift_axes | reported → `combined` | “different field, year, plant cover, and unseen (later) growth stages” + herbicide-induced class-prior shift (control full cover vs sprayed clean) | Combined field + date/year + growth_stage + class_prior (+ cover). **Cannot isolate** sensor or temporal effect (safeguard e). |
| temporal_design | reported → `heldout_date` (within combined) | Train 2023 season → test Maize2024 (2024, later growth stages) | Held-out year/growth-stage holds, but only as one axis of a combined shift — not an isolated temporal proof. Multitemporal-train ≠ temporal generalisation proof. |
| target_data_use | reported → `none` | “train DeepLabv3+ separately on [each dataset]” then predict Maize2024; 6 annotated patches are test-only (“to get quantitative scores … we annotate 6 patches”) — no fine-tuning/selection on Maize2024 reported | Direct transfer without adaptation. Target labels used for *evaluation*, not training (not `labeled_finetuning`). |
| uncertainty_evaluation | not_reported → null | §4.3 reports IoU + qualitative weed-cover; no ECE/entropy on Maize2024 in inspected text | Checked §4.3/Tab.7/Fig.6 scope; in-domain calibration (WG-E2) does not transfer automatically. |
| stress_origin | reported → `observed` | Natural field/year/cover/growth + real herbicide treatment effects (not synthetic corruption) | Observed real-world shift, not synthetic spectral stress. No spectral-degradation experiment in any setting (absent test). |
| sensor_awareness | reported → `band_availability` (train-side) | RGB/MSI training contrast exists only in WG-E1/E2; §4.3 transfer uses 3-class DeepLabv3+ (input modality per training set, not ablated on OOD in inspected text) | No OOD sensor-awareness claim; do not carry over in-domain MSI gain as OOD proof. |
| group_counts | reported (partial) | “6 cropped patches ~90 m2, 1000×1100px” + “WeedsGalore model 52.55% mIoU on OOD, 23.22% higher than runner-up” + qualitative “WeedsGalore captures high weed cover in control; MaizeOrWeed completely fails to segment any vegetation” | Full Tab.7 per-dataset numbers not fully captured in convenience extraction — marked partial; needs IEEE-final verification before accepted row. |
| metrics_and_controls | reported | 3-class semantic IoU/mIoU on 6 OOD patches; matched controls = same DeepLabv3+ trained on PhenoBench / CropAndWeed / MaizeOrWeed | Controls test acquisition-vs-crop hypotheses: “acquisition mode or crop type alone isn’t sufficient … datasets targeting UAV weed-maize monitoring are needed.” |
| transfer_result | reported (mixed/positive with failure) | Positive: WeedsGalore transfers best (52.55%). Negative (preserved): MaizeOrWeed “completely fails”; PhenoBench/CropAndWeed trail by ≥23.22 pp. No uncertainty on OOD. | Failures preserved; no leaderboard beyond this OOD target. |
| seeds_and_intervals | not_reported → null | No repeats/CIs on 6-patch OOD scores in inspected text | Small-n (6 patches) uncertainty unquantified — limitation, not a calculated CI. |
| limitations | reported | 6-patch quantitative (small, single OOD field/year); qualitative remainder; combined shift prevents attribution; no calibration/abstention on OOD; no sensor-shift isolation; IEEE-final Tab.7 unverified | All absent tests listed explicitly. |

---

## STU-PRELIM-SWN — SemiWeedNet family (preliminary)

| Cell | State → value | Evidence | Note |
|---|---|---|---|
| task | reported → `semantic_segmentation` | Title “Semi-supervised Learning for Weed and Crop Segmentation Using UAV Imagery” + “Comparative experiments … segmentation … IoU per class + mIoU” + Fig.4 “Green crop, Red weed, Black background” | Pixel-wise crop/weed/soil segmentation; no detection/instance/mapping claim. |
| method_family | reported → `deep_learning` | “DeepLabV3+ employed as encoder–decoder … ResNet50/101 backbone … MFEM + SKA attention + OHEM + consistency (directional contrastive) loss” | Deep semi-supervised; comparators CAC/ST++/Adv-Semi/cycleGAN also deep (same backbone for fairness). |
| report_type | reported → `journal` | “ORIGINAL RESEARCH … Frontiers in Plant Science … Volume 13 Article 927368” + Crossref `journal-article` | Single Vor; no preprint lineage. |
| report_family | reported → narrative | Single version 2022-07-01 (Received Apr 24 / Accepted Jun 10 / Published Jul 1); authors Nong/Fan/Wang; no version conflict | — |
| dataset_provenance | reported → narrative | “use publicly available WeedMap (Sa et al. 2018) … two sugar fields Switzerland/Germany … two UAV platforms … RedEdge + Sequoia … Orthomosaic + Tile (480×360) … 7 subsets 000–004 RedEdge Germany + 005–007 Sequoia Switzerland … sliding window … some tiles invalid” + “select effective tiles with no invalid pixels, only RGB channel … 289 RGB labelled images from 000–004 … randomly split 8:2 train:test” | Reuse of another study’s dataset as a distinct primary experiment (codebook: distinct study even on shared dataset). Subset (000–004 only) + RGB-only + clean-tile filter must be preserved — not the full WeedMap inventory. |
| crop_context | reported (partial) | WeedMap sugar fields (crop: sugar beet per WeedMap; classes in Fig.4: crop/weed/soil); tile filtering; no field/date/season details in inspected scope | Field identity, dates, seasons, GSD, flight details **not_reported** in inspected SemiWeedNet scope (would need WeedMap 2018 background for context, not as included study). Unavailable vs not_reported: relevant SemiWeedNet sections checked (Dataset ¶) — code `not_reported` with note, not `unavailable`. |
| open_science | reported (partial) | Methods/implementation detailed (PyTorch, RTX3080Ti, hyperparams); “implemented [comparators] within unified framework following official code, same backbone + data lists” | Code/data URLs, license, retraction, funding/COI not checked (unavailable — no Phase-4). |

### SWN-E1 — semi-supervised RGB in-domain, random image split (preliminary)

| Cell | State → value | Evidence | Note |
|---|---|---|---|
| setting_definition | reported | “289 RGB images … randomly split 8:2 train:test” + “labelled proportions 2/8, 3/7, 5/5, full … batch 8 (4 labelled + 4 unlabelled) … λ=0.7 … full setting: unsupervised branch fed from labelled set” + ablations Tab.2 (baseline/SK/OHEM) | One in-domain setting with labelled-proportion variants grouped (repeated conditions, not separate shifts). |
| sensor_bands | reported | “only choose the RGB channel as input” + “input resized 480×480 + random flipping” | **RGB actual input.** Original WeedMap RedEdge/Sequoia multispectral inventory does NOT prove multispectral evaluation (safeguard c). |
| split_unit | reported → `image` | “randomly split into training and testing in ratio 8:2” (images/tiles); no spatial/field/date blocking reported | Weak random-tile/image evaluation — charted, not excluded (protocol). Overlap risk (same orthomosaic, sliding window, adjacent tiles across splits) is unaddressed → limitation. |
| shift_axes | reported → `none` | Same subset (000–004), same sensor-channels (RGB), same preprocessing; no degradation/sensor/field/date shift tested | — |
| temporal_design | not_reported → null | Dataset ¶ + Implementation + Results checked: no acquisition dates, no multi-date design, no held-out date/season | Cannot code `single_date` without date evidence; multitemporal ≠ assumed. Note records inspected scope. |
| target_data_use | reported → `none` (with justification) | Unlabelled images come from same 000–004 pool (“two batches xl/xu … overlapping crops xu1/xu2 … memory bank of last batches”); no distinct target field/sensor/date with separate assignment | **Semi-supervised ≠ target-domain adaptation** (safeguard d). No explicitly distinct evaluation target + assignment evidence → `none`, not `unlabeled_adaptation`. Derivation note preserved here. |
| uncertainty_evaluation | not_reported → null | Full text checked (Method/Results/Ablation/Tabs.1–2/Figs.5–7): consistency/DC loss + OHEM are training objectives, not uncertainty/calibration experiments; no ECE, no predictive entropy, no abstention | Learned attention/consistency ≠ calibrated uncertainty (protocol). Silence is not `none`. |
| stress_origin | reported → `none` | No synthetic/observed stress; “low-level augmentation” only (random flip) | Augmentation is not a stress test. |
| sensor_awareness | reported → `none` | RGB-only; no band-availability/metadata/fusion experiment in inspected scope | Original multispectral inventory is background, not an evaluated condition. |
| group_counts | reported | 289 images (8:2 ≈ 231/58); labelled proportions 2/8 etc.; Tab.1 mIoU per method×backbone×proportion (e.g. Ours R50 0.698/0.695/0.695/0.701; SupOnly R50 0.664/0.675/0.698/0.700; ST++ ~0.60; cycleGAN R101 0.388–0.558) + Tab.2 ablations (e.g. 5/5: baseline 0.683 → full 0.696) | Units = tile images; class IoU + mIoU; “20% labelled + unlabelled ≈ full labelled” (competitive, not superior). |
| metrics_and_controls | reported | “IoU per class + mIoU (Eq.15–16)” + “same base backbone (ResNet) + same data lists for training/testing” + SGD LR 0.02 / wd 0.0001 / momentum 0.9 | Matched controls; failure modes of comparators preserved (Adv-Semi/cycleGAN “unstable adversarial”, ST++/CAC “pseudo-label errors on overlap/occlusion”). |
| transfer_result | reported → in-domain only | “outperforms SOTA by large margin on all proportions” (in-domain); “only method effectively identifying small-size crop/weeds, almost consistent with GT” (Fig.7); no cross-field/date/sensor transfer tested | No external validation to report; absence is data. |
| seeds_and_intervals | not_reported → null | No seeds/CIs in Tabs.1–2/Figs.5–6 in inspected scope | — |
| limitations | reported | Random image split with sliding-window tiles (leakage risk); RGB-only on multispectral source (no spectral-shift test); single subset (000–004, Germany/RedEdge tiles) — no cross-site (005–007 Sequoia/Switzerland) test despite inventory; no temporal/sensor/field generalisation; no calibration; small-n (289) | Author + reviewer-observed limits; overlapping/occlusion + imbalance motivate OHEM but do not prove robustness. |

---

## Prohibited claims (do NOT make from this pilot)

1. Do not claim WeedsGalore preprint extraction = IEEE final (unreconciled delta).
2. Do not claim dataset diversity (4 dates / 12 patches / 5 bands inventory) = external validation (only WG-E3 is external, and it is combined-shift).
3. Do not claim multitemporal data = held-out temporal proof (WG-E1/E2 are `multiple_dates_no_heldout`).
4. Do not claim WeedMap multispectral inventory = SemiWeedNet multispectral evaluation (SWN evaluated RGB only).
5. Do not claim semi-supervised unlabelled use = domain adaptation (SWN `target_data_use none`).
6. Do not claim WG-E3 combined shift isolates a sensor or temporal effect.
7. Do not claim attention/consistency (SKA/DC) = calibrated uncertainty (only WG-E2 ECE counts).
8. Do not claim schema pass = entailment (no accepted rows exist; quotes above still need E1/E2 re-verification).
9. Do not count S4, WeedMap 2018, or S5 in any eligible-study denominator.
10. Do not use sentinel coverage (S1/S3/S4) as held-out agent performance.

## Counts

- Accepted studies / evaluations / datasets: **0 / 0 / 0** (acceptance gate unsatisfied by design).
- Preliminary study notes: **2** (WG, SWN). Preliminary evaluation-setting notes: **4** (WG-E1/E2/E3, SWN-E1).
- Unresolved: **1** (S4, no bytes). Background probes: **2** (WeedMap 2018, S5 review).
- No `DOC-*` IDs minted; no `charting.schema.json` rows fabricated to pass validation.
