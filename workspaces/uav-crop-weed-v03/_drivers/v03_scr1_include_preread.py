# -*- coding: utf-8 -*-
"""v03 SCR1 include-lean pool: post-hoc pre-read for the human research lead.

NOT a blinded screen. Samples every 12th record of the sorted 626-record
include-lean pool (588 mutual-INCLUDE + 38 T3 majority-INCLUDE) and writes a
preread classification against the frozen criteria reference to JSON.

Run:  uv run python workspaces\\uav-crop-weed-v03\\_drivers\\v03_scr1_include_preread.py
Outputs (ONLY these two files are touched):
  workspaces\\uav-crop-weed-v03\\calibration_v03\\v03_scr1_include_preread.json
"""

import json
import os
from collections import Counter

WS = os.path.join("workspaces", "uav-crop-weed-v03")
CAL = os.path.join(WS, "calibration_v03")
DEDUPED = os.path.join(CAL, "v03_r3e_20261017_deduped.json")
RECON = os.path.join(CAL, "v03_scr1_reconciliation_full.json")
T3 = os.path.join(CAL, "v03_scr1_t3_tricot_reconcile.json")
OUT = os.path.join(CAL, "v03_scr1_include_preread.json")

# sampling rule
STRIDE = 12
START = 0


def main() -> None:
    docs = json.load(open(DEDUPED, encoding="utf-8"))["documents"]
    docs = {d["workspace_id"]: d for d in docs}

    mutual = json.load(open(RECON, encoding="utf-8"))["human_lanes"]["mutual_include"]
    t3 = json.load(open(T3, encoding="utf-8"))["outcomes"]
    t3_include = [r["sid"] for r in t3 if r["class"] == "majority_include"]

    pool = sorted(set(mutual) | set(t3_include))
    assert len(pool) == 626, len(pool)

    sampled = [pool[i] for i in range(START, len(pool), STRIDE)]

    # ---- preread adjudications (human-readable, hand-curated from titles + abstracts) ----
    D = {
        "SCI-000002": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "Onboard-UAV real-time weed mapping for SSWM; INC-01/INC-02 primary method study.",
            "full",
            "",
        ),
        "SCI-000036": (
            "dataset_benchmark",
            "keep",
            "uav_evident",
            "Patch version of WeedsGalore 'using UAV multispectral imagery' with crop/weed masks; INC-02 dataset report.",
            "full",
            "",
        ),
        "SCI-000054": (
            "out_of_window",
            "drop",
            "uav_evident",
            "EXC-04 OUTSIDE_DATE_LANGUAGE: abstract is Spanish ([SPA]); needs language verification before include.",
            "full",
            "abstract begins '[SPA]' - foreign-language record flag",
        ),
        "SCI-000078": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "RPAS coffee-farm weed classify/map (INC-01 managed perennial); 'aerial images were obtained by a remotely piloted aircraft'.",
            "full",
            "",
        ),
        "SCI-000098": (
            "phenotyping_traits",
            "drop",
            "uav_evident",
            "EXC-02 WRONG_TASK: walnut canopy nutritional/parameter inversion, no weed/crop-weed mapping task.",
            "full",
            "",
        ),
        "SCI-000122": (
            "review_or_secondary",
            "uncertain",
            "unclear",
            "PhD-thesis chapter compilation; EXC-03-adjacent but Chapter 5 is 'weed mapping ... using unmanned aerial vehicle imagery'.",
            "full",
            "thesis chapter list, not a single report",
        ),
        "SCI-000137": (
            "dataset_benchmark",
            "keep",
            "uav_evident",
            "Multitemporal multispectral UAV orthomosaics of maize for crop/weed monitoring (INC-02).",
            "full",
            "",
        ),
        "SCI-000157": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "Feature-enriched DL on 'drone imagery, we collected a dataset'; INC-01/INC-02.",
            "full",
            "",
        ),
        "SCI-000172": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "U-Net/DeepLabV3+ weed segmentation on 'aerial images ... captured by UAVs' (Cofly, AgricultureVision).",
            "full",
            "",
        ),
        "SCI-000189": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "Encoder-decoder attention segmentation of weed/crop in drone images; INC-01/INC-02.",
            "full",
            "",
        ),
        "SCI-000206": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "Few-shot weed localization in 'multispectral drone images' with radiometric calibration (reliability-relevant, RQ1).",
            "full",
            "",
        ),
        "SCI-000227": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "Vision Transformers for weeds/crops classification of 'High Resolution UAV Images' (arXiv preprint, INC-02).",
            "full",
            "",
        ),
        "SCI-000260": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "Core is weed detection/segmentation + prescription maps on 'UAV-acquired imagery'; spraying is downstream application, not exclusion.",
            "full",
            "spraying-in-title boundary: method core kept under INC-01/INC-02",
        ),
        "SCI-000277": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "Camouflage weed-patch detection in sugarcane 'using UAV data'; INC-01/INC-02.",
            "full",
            "",
        ),
        "SCI-000296": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "Crop-row + weed-pressure mapping from 'drone imagery captured at altitudes of 20-30 m'; spatial weed mapping (INC-01).",
            "full",
            "",
        ),
        "SCI-000312": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "Title/abstract: 'Weed Classification on UAV Images Using Deep Learning' (conference, INC-02).",
            "full",
            "",
        ),
        "SCI-000332": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "K-means weed ID in 'Multi-Spectral Images Taken by UAV'; INC-01.",
            "full",
            "",
        ),
        "SCI-000351": (
            "dataset_benchmark",
            "uncertain",
            "uav_evident",
            "Drone rangeland leafy-spurge dataset; rangeland vs INC-01 'managed pastures' boundary - human confirm.",
            "full",
            "rangeland/grassland weed mapping is an EXC-02 vs INC-01 boundary case",
        ),
        "SCI-000368": (
            "dataset_benchmark",
            "keep",
            "uav_evident",
            "'High-rEsolution dRone dataset for Site-Specific weed management in Maize'; INC-02 dataset report.",
            "full",
            "",
        ),
        "SCI-000389": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "UAV + ML weed detection/localization in strawberry; INC-01 vegetables.",
            "full",
            "",
        ),
        "SCI-000413": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "Red-edge band contribution to wheat/chickweed/buttercup mapping with 'drone ... Altum multispectral camera' (sensor-difference RQ1).",
            "full",
            "",
        ),
        "SCI-000430": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "'UAV acquired camouflage dataset' weed-patch detection in sugarcane; short conference abstract-length paper (INC-02).",
            "full",
            "",
        ),
        "SCI-000454": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "UAV orthomosaic workflow over weed-infested wheat ('UAV flying at altitudes of 30 to 100 m'); INC-01.",
            "full",
            "",
        ),
        "SCI-000475": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "Automated weed/crop labeling workflow on 'high-resolution UAV imagery (0.88 mm)' Saskatchewan; INC-02.",
            "full",
            "",
        ),
        "SCI-000491": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "Drone-image ML detection of small morning-glory in soybean; INC-01 row crop.",
            "full",
            "",
        ),
        "SCI-000508": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "Faster R-CNN weed classification from 'A ... DJI phantom 4 UAV'; training-epoch ablation (INC-02).",
            "full",
            "",
        ),
        "SCI-000530": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "Corn/weed spectral discrimination with 'EBEE SQ agricultural drone'; INC-01.",
            "full",
            "",
        ),
        "SCI-000564": (
            "dataset_benchmark",
            "keep",
            "uav_evident",
            "Zenodo weed-detection bbox dataset 'captured by a UAV over a field seeded with celeriac'; INC-02.",
            "full",
            "abstract head is project blurb; dataset spec at tail",
        ),
        "SCI-000584": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "Swarm-learning lightweight YOLOv11 'weed detection in UAV images' with heterogeneity/generalization angle (RQ1).",
            "full",
            "",
        ),
        "SCI-000624": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "YOLO-WEED on data 'derived from a five-minute UAV video'; INC-02.",
            "full",
            "",
        ),
        "SCI-000664": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "Radon+YOLO weed detection in 'Images Captured by Unmanned Aerial Vehicle (UAV) in SRI planted fields'; INC-01.",
            "full",
            "",
        ),
        "SCI-000693": (
            "platform_ambiguous",
            "uncertain",
            "mixed_separable",
            "Satellite-first herbicide-efficacy study but 'separation between damaged and healthy weeds in UAV images' is a separable UAV stream; human confirm.",
            "full",
            "satellite title wearing an embedded UAV experiment - review-scope boundary",
        ),
        "SCI-000712": (
            "platform_ambiguous",
            "uncertain",
            "unclear",
            "'synthetic ... UAV multispectral sensor emulations' derived from HySpex AIRBORNE (not UAV-acquired) imagery; human confirm under EXC-01.",
            "full",
            "synthetic UAV-band emulation from airborne HySpex source - platform boundary",
        ),
        "SCI-000737": (
            "primary_method_study",
            "uncertain",
            "uav_evident",
            "BSS-YOLOv8 grassland noxious-plant detection 'using UAV images'; pasture/grassland vs non-agricultural EXC-02 boundary.",
            "full",
            "grassland poisonous-plant mapping - INC-01 pasture boundary case",
        ),
        "SCI-000778": (
            "dataset_benchmark",
            "keep",
            "uav_evident",
            "'Annotated UAV Imagery Dataset' with weed-polygon labels for camelina; INC-02.",
            "full",
            "",
        ),
        "SCI-000800": (
            "phenotyping_traits",
            "drop",
            "uav_evident",
            "EXC-02 WRONG_TASK: multimodal fusion estimating weed-competitiveness trait index, not weed detection/mapping.",
            "full",
            "",
        ),
        "SCI-000834": (
            "other_wrong_task",
            "drop",
            "uav_evident",
            "EXC-02 WRONG_TASK: broccoli disease detection + fungicide resistance; disease is an excluded task.",
            "full",
            "",
        ),
        "SCI-000879": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "Italian ryegrass vs wheat discrimination 'using an unmanned aerial vehicle (UAV) equipped with a 5-band multispectral sensor'; INC-01.",
            "full",
            "",
        ),
        "SCI-000919": (
            "platform_ambiguous",
            "drop",
            "unclear",
            "EXC-01-adjacent: 'helicopter-based aerial imaging' HySpex patches emulated to UAV sensor bands; no UAV-acquired evidence.",
            "full",
            "helicopter imagery wearing UAV-sensor emulation - platform boundary case",
        ),
        "SCI-000956": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "YOLOv8n barnyard-grass detection, 'Field tests using drones ... in real-world complex paddy environments'; INC-01.",
            "full",
            "",
        ),
        "SCI-001011": (
            "platform_ambiguous",
            "uncertain",
            "mixed_separable",
            "Multi-benchmark framework incl 91.5% on 'UAV Crop and Weed' but mixed with PlantVillage disease + satellite land-cover tasks; human confirm.",
            "full",
            "multi-task multi-platform framework; UAV weed result separable but incidental",
        ),
        "SCI-001045": (
            "dataset_benchmark",
            "keep",
            "uav_evident",
            "VITAFields watermelon 'aerial and drone imagery ... for field-scale semantic segmentation, weed and crop'; INC-02.",
            "full",
            "",
        ),
        "SCI-001102": (
            "dataset_benchmark",
            "uncertain",
            "unclear",
            "Pea-crop orthomosaic part 5; weed/crop-classification use stated but no explicit UAV-acquisition fragment in this part's abstract.",
            "full",
            "companion parts are drone imagery; this part's abstract alone is platform-thin",
        ),
        "SCI-001146": (
            "primary_method_study",
            "keep",
            "uav_evident",
            "'Drone images and an automatic image recognition method' for Datura infestation mapping in soybean; INC-01.",
            "full",
            "",
        ),
        "SCI-001192": (
            "dataset_benchmark",
            "drop",
            "mixed_separable",
            "EXC-02-adjacent: dataset is crop-classification ('cassava, sugarcane, maize...'); weeds live in a separate part; drone capture only partial.",
            "full",
            "crop-classification dataset, weed class split into part two",
        ),
        "SCI-001375": (
            "other_wrong_task",
            "drop",
            "mixed_separable",
            "EXC-02 WRONG_TASK: UAV+Sentinel crop FIELD classification, no weed task despite UAV being separable.",
            "full",
            "mixed-platform but crop-type mapping, not weed localization",
        ),
        "SCI-002152": (
            "other_wrong_task",
            "drop",
            "uav_evident",
            "EXC-02 WRONG_TASK: UAS land-use/agriculture mapping for food-security monitoring, no crop/weed localization.",
            "full",
            "",
        ),
        "SCI-003560": (
            "other_wrong_task",
            "drop",
            "uav_evident",
            "EXC-02 WRONG_TASK: UAV coconut-TREE detection/object localization; perennial-crop tree counting, not weed mapping.",
            "full",
            "",
        ),
        "SCI-005645": (
            "other_wrong_task",
            "drop",
            "uav_evident",
            "EXC-02 WRONG_TASK: vine detection + vineyard zoning; no weed/crop-weed mapping component.",
            "full",
            "managed-perennial setting but task is vine zoning, not weed mapping",
        ),
        "SCI-008137": (
            "platform_ambiguous",
            "uncertain",
            "unclear",
            "U-Net crop/weed segmentation in tobacco from 'Aerial Images'; abstract names no UAV/drone/satellite platform; human confirm (INC-01 separability).",
            "full",
            "aerial-title with zero platform keywords in abstract",
        ),
        "SCI-009692": (
            "other_wrong_task",
            "drop",
            "uav_evident",
            "EXC-02 WRONG_TASK: wheat-EAR detection 'critical for wheat yield prediction'; yield/phenology task.",
            "full",
            "",
        ),
        "SCI-011678": (
            "phenotyping_traits",
            "drop",
            "uav_evident",
            "EXC-02 WRONG_TASK: rice plant counting/localization (phenotyping), no weed mapping.",
            "full",
            "",
        ),
        "SCI-013486": (
            "other_wrong_task",
            "drop",
            "uav_evident",
            "EXC-02 WRONG_TASK: economic tree-species + built-up detection in Thailand; non-crop-weed vegetation mapping.",
            "full",
            "",
        ),
    }

    assert len(sampled) == len(D) == 53, (len(sampled), len(D))
    for sid in sampled:
        assert sid in D, sid

    items, drop_risk = [], []
    for sid in sampled:
        d = docs[sid]
        ab = d.get("abstract") or ""
        cls, plaus, plat, reason, aq, note = D[sid]
        eid = d.get("external_ids") or {}
        doi = eid.get("doi") if isinstance(eid, dict) else (eid if eid else None)
        provs = sorted({x["provider"] for x in (d.get("sources") or [])})
        if aq == "thin-or-absent":  # not used, kept for future
            aq = "thin" if len(ab) < 300 else ("absent" if not ab else "full")
        rec = {
            "screening_id": sid,
            "title": d.get("title"),
            "year": d.get("year"),
            "primary_provider": d.get("provider"),
            "source_providers": provs,
            "doi": doi,
            "abstract_len": len(ab),
            "class": cls,
            "plausibility": plaus,
            "platform_signal": plat,
            "abstract_quality": aq,
            "note": note,
            "reason": reason,
            "pool_origin": "t3_majority_include"
            if sid in set(t3_include)
            else "mutual_include",
        }
        items.append(rec)
        if plaus in ("drop", "uncertain"):
            drop_risk.append(rec)

    stats = {
        "pool_size": len(pool),
        "sample_size": len(items),
        "sampling_rule": f"sorted-pool every-12th: sorted(sids)[{START}, {START}+{STRIDE}, ...] -> {len(sampled)} records",
        "class_distribution": dict(sorted(Counter(r["class"] for r in items).items())),
        "plausibility_distribution": dict(Counter(r["plausibility"] for r in items)),
        "platform_signal_distribution": dict(
            sorted(Counter(r["platform_signal"] for r in items).items())
        ),
        "primary_provider_distribution": dict(
            Counter(r["primary_provider"] for r in items)
        ),
        "source_provider_multiset": dict(
            Counter(p for r in items for p in r["source_providers"])
        ),
        "dual_source_count": sum(1 for r in items if len(r["source_providers"]) > 1),
        "abstract_quality_distribution": dict(
            Counter(r["abstract_quality"] for r in items)
        ),
        "year_range": [
            min(r["year"] for r in items if r["year"]),
            max(r["year"] for r in items if r["year"]),
        ],
        "drop_risk_count": len(drop_risk),
    }

    out = {
        "artifact": "v03_scr1_include_preread",
        "generated_by": "v03_scr1_include_preread.py (post-hoc pre-read, NOT a blinded screen)",
        "generated_date": "2026-10-19",
        "frozen_criteria_ref": "workspaces/uav-crop-weed-v03/calibration_v03/v03_scr1_SCREENING_CRITERIA_frozen_ref.md",
        "inputs": {
            "deduped_corpus": os.path.basename(DEDUPED),
            "mutual_include": os.path.basename(RECON)
            + " :: human_lanes.mutual_include (588 ids)",
            "t3_majority_include": os.path.basename(T3)
            + " :: outcomes[] records with class == 'majority_include' (38 ids); facts: wave SCR1-T3-20261018, 814 conflict records, other classes are majority_exclude/majority_pending/tie_three_way",
            "pool_overlap_588x38": 0,
        },
        "stats": stats,
        "records": items,
        "drop_risk_records": [
            {
                k: r[k]
                for k in ("screening_id", "title", "class", "plausibility", "reason")
            }
            for r in drop_risk
        ],
    }
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        f.write(out_text := json.dumps(out, indent=2, ensure_ascii=False))
    return out_text


if __name__ == "__main__":
    txt = main()
    o = json.loads(txt)
    s = o["stats"]
    width = 40
    print("=" * width)
    print("v03 SCR1 INCLUDE-POOL PREREAD SUMMARY")
    print("=" * width)
    print(
        "pool:",
        s["pool_size"],
        "| sampled:",
        s["sample_size"],
        "| rule:",
        s["sampling_rule"],
    )
    print("\nCLASS DISTRIBUTION")
    for k, v in s["class_distribution"].items():
        print(f"  {k:28s} {v:3d}")
    print("\nPLAUSIBILITY", s["plausibility_distribution"])
    print("PLATFORM SIGNALS", s["platform_signal_distribution"])
    print(
        "PRIMARY PROVIDER",
        s["primary_provider_distribution"],
        "| dual-source:",
        s["dual_source_count"],
    )
    print("SOURCE PROVIDER MULTISET", s["source_provider_multiset"])
    print("ABSTRACT QUALITY", s["abstract_quality_distribution"])
    print("YEAR RANGE", s["year_range"])
    print("\nDROP-RISK RECORDS (uncertain/drop):", s["drop_risk_count"])
    for r in o["drop_risk_records"]:
        print(
            f"  {r['screening_id']} [{r['plausibility']:9s}] [{r['class']:22s}] {r['title'][:72]}"
        )
        print(f"     reason: {r['reason']}")
    print(
        "\nboundary highlights: satellite/HySpex/helicopter wearing UAV framing ->",
        [r["screening_id"] for r in o["records"] if r["class"] == "platform_ambiguous"],
    )
