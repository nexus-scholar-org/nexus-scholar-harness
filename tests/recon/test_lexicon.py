"""Hermetic tests for the pluggable DomainLexicon (M0.4: T4.5).

All pools are fabricated in-process; no provider network is touched.  The
default lexicon must reproduce today's CV/LLM tables plus the curated
cross-domain core (P6) byte-identically, and a fabricated oncology lexicon
must pick up its own patterns while ignoring the CV-era defaults (and vice
versa).
"""

import json

from scholar_harness.recon import (
    DEFAULT_LEXICON,
    DomainLexicon,
    distill_pool,
    merge_lexicons,
)


def _doc(doi: str, title: str, abstract: str) -> dict:
    return {
        "id": f"openalex|{doi}",
        "provider": "openalex",
        "doi": doi,
        "title": title,
        "abstract": abstract,
        "year": 2022,
        "citations": 3,
        "oa_url": None,
    }


def _pool(docs: list[dict], cache_key: str = "v1/openalex/y2000-2026/q/feedface00") -> dict:
    return {
        "cache_key": cache_key,
        "created_at": "2026-09-12T00:00:00Z",
        "docs": docs,
        "fulltexts": {},
    }


# ---------------------------------------------------------------------------
# Default lexicon keeps today's behavior byte-identical
# ---------------------------------------------------------------------------


def test_default_lexicon_detects_cv_fixtures():
    pool = _pool(
        [
            _doc(
                "10.1000/bench-a",
                "Crop Disease Detection at Scale",
                "We evaluate the detection model with mAP@0.5 and report "
                "inference FPS over the PlantVillage collection.",
            ),
            _doc(
                "10.1000/code-a",
                "Code Repair Sampling",
                "We report pass_at_1 and pass_at_k on HumanEval.",
            ),
            _doc(
                "10.1000/uav",
                "UAV Crop Monitoring with Drones",
                "We survey field stress with drones and a visible-light camera.",
            ),
            _doc(
                "10.1000/llm",
                "Large Language Models for Code Repair",
                "We fine-tune an LLM on HumanEval to repair broken tests.",
            ),
        ]
    )
    result = distill_pool(pool)
    assert result["metrics"] == {"FPS": 1, "mAP": 1, "pass@": 1}
    assert result["datasets"] == {"PlantVillage": 1, "HumanEval": 2}
    by_label = {s["label"]: s for s in result["schools"]}
    assert set(by_label) == {"UAV/drone", "language model/LLM"}
    assert by_label["UAV/drone"]["n"] == 1


def test_default_lexicon_pass_variants_match():
    pool = _pool(
        [
            _doc("10.1000/code-b", "Decoder Sampling", "Greedy decoding is compared against pass@1 estimates."),
            _doc("10.1000/code-c", "Verifier Sampling", "We measure pass_at_k for the repaired programs."),
        ]
    )
    assert distill_pool(pool)["metrics"]["pass@"] == 2


def test_default_lexicon_covers_every_shipped_pattern():
    metrics_docs = [
        ("10.2000/m-01", "mAP report", "we report map@0.5 performance"),
        ("10.2000/m-02", "F1 study", "the f1 measure"),
        ("10.2000/m-03", "FPS study", "at 50 fps"),
        ("10.2000/m-04", "IoU study", "iou of boxes"),
        ("10.2000/m-05", "precision study", "high precision"),
        ("10.2000/m-06", "recall study", "higher recall"),
        ("10.2000/m-07", "BLEU study", "bleu score"),
        ("10.2000/m-08", "pass study", "we report pass@1 and pass_at_k"),
        ("10.2000/m-09", "accuracy study", "accuracy improves"),
        ("10.2000/m-10", "exact match study", "exact match rates"),
        ("10.2000/m-11", "codebleu study", "codebleu metric"),
        ("10.2000/m-12", "RMSE report", "we report rmse"),
        ("10.2000/m-13", "MAE study", "lower mae"),
        ("10.2000/m-14", "AUC study", "auc rises"),
        ("10.2000/m-15", "R2 study", "r2 improves"),
        ("10.2000/m-16", "MCC study", "the mcc value"),
        ("10.2000/m-17", "p-value study", "a small p-value"),
        ("10.2000/m-18", "CI study", "the 95% confidence interval"),
        ("10.2000/m-19", "Odds study", "the odds ratio"),
    ]
    datasets_docs = [
        ("10.2000/d-01", "PlantVillage study", "plant village dataset"),
        ("10.2000/d-02", "RoCoLe study", "rocole benchmark"),
        ("10.2000/d-03", "MBPP study", "mbpp tasks"),
        ("10.2000/d-04", "HumanEval study", "humaneval set"),
        ("10.2000/d-05", "SWE-bench study", "swe-bench suite"),
        ("10.2000/d-06", "CodeTransOcean study", "codetransocean corpus"),
        ("10.2000/d-07", "ImageNet study", "imagenet pretraining"),
        ("10.2000/d-08", "COCO study", "coco annotations"),
        ("10.2000/d-09", "MNIST study", "mnist digits"),
        ("10.2000/d-10", "CIFAR study", "cifar10 images"),
        ("10.2000/d-11", "GSM8K study", "gsm8k reasoning"),
        ("10.2000/d-12", "MMLU study", "mmmlu multiple choice"),
        ("10.2000/d-13", "SQuAD study", "squad reading comprehension"),
        ("10.2000/d-14", "MedMNIST study", "medmnist classification"),
        ("10.2000/d-15", "Cityscapes study", "cityscapes segmentation"),
        ("10.2000/d-16", "Pascal VOC study", "pascal voc dataset"),
        ("10.2000/d-17", "ERA5 study", "era5 reanalysis fields"),
        ("10.2000/d-18", "CMIP study", "cmip6 simulations"),
        ("10.2000/d-19", "TCGA study", "tcga expression data"),
        ("10.2000/d-20", "MIMIC study", "the mimic-iv cohort"),
    ]
    schools_docs = [
        ("10.2000/s-01", "deep learning study", "deep learning models"),
        ("10.2000/s-02", "UAV study", "uav survey with drones"),
        ("10.2000/s-03", "LLM study", "large language models and llms"),
        ("10.2000/s-04", "edge inference study", "edge inference runtime"),
        ("10.2000/s-05", "multispectral study", "multispectral imaging and hyperspectral data"),
        ("10.2000/s-06", "segmentation study", "semantic segmentation task"),
        ("10.2000/s-07", "transformer study", "vision transformers"),
        ("10.2000/s-08", "climate change study", "climate change impacts"),
        ("10.2000/s-09", "global warming study", "global warming trend"),
        ("10.2000/s-10", "precipitation study", "extreme precipitation"),
        ("10.2000/s-11", "drought study", "severe drought"),
        ("10.2000/s-12", "hydrology study", "hydrological modeling"),
        ("10.2000/s-13", "oncology study", "oncology imaging"),
        ("10.2000/s-14", "immunotherapy study", "immunotherapy response"),
        ("10.2000/s-15", "clinical trial study", "randomized controlled trial"),
        ("10.2000/s-16", "MRI study", "magnetic resonance imaging"),
        ("10.2000/s-17", "credit risk study", "credit risk models"),
        ("10.2000/s-18", "causal inference study", "causal inference methods"),
        ("10.2000/s-19", "econometrics study", "econometric analysis"),
        ("10.2000/s-20", "learning analytics study", "learning analytics dashboards"),
        ("10.2000/s-21", "self-regulated learning study", "self-regulated learning"),
        ("10.2000/s-22", "qualitative study", "qualitative content analysis"),
        ("10.2000/s-23", "DFT study", "density functional theory"),
        ("10.2000/s-24", "molecular dynamics study", "molecular dynamics simulations"),
        ("10.2000/s-25", "interatomic potentials study", "machine-learned interatomic potentials"),
    ]
    docs = [
        _doc(doi, title, abstract)
        for doi, title, abstract in metrics_docs + datasets_docs + schools_docs
    ]
    result = distill_pool(_pool(docs))
    assert set(result["metrics"]) == {
        "mAP",
        "F1",
        "FPS",
        "IoU",
        "precision",
        "recall",
        "BLEU",
        "pass@",
        "accuracy",
        "exact match",
        "codebleu",
        "RMSE",
        "MAE",
        "AUC",
        "R2",
        "MCC",
        "p-value",
        "confidence interval",
        "odds ratio",
    }
    assert set(result["datasets"]) == {
        "PlantVillage",
        "RoCoLe",
        "MBPP",
        "HumanEval",
        "SWE-bench",
        "CodeTransOcean",
        "ImageNet",
        "COCO",
        "MNIST",
        "CIFAR",
        "GSM8K",
        "MMLU",
        "SQuAD",
        "MedMNIST",
        "Cityscapes",
        "Pascal VOC",
        "ERA5",
        "CMIP",
        "TCGA",
        "MIMIC",
    }
    assert {s["label"] for s in result["schools"]} == {
        "deep learning",
        "UAV/drone",
        "language model/LLM",
        "edge inference",
        "multispectral/hyperspectral",
        "segmentation",
        "transformer",
        "climate science",
        "global warming",
        "precipitation",
        "drought",
        "hydrology",
        "oncology",
        "immunotherapy",
        "clinical trial",
        "MRI",
        "credit risk",
        "causal inference",
        "econometrics",
        "learning analytics",
        "self-regulated learning",
        "qualitative research",
        "DFT",
        "molecular dynamics",
        "interatomic potentials",
    }


def test_distill_pool_no_lexicon_byte_identical_to_today():
    pool = _pool(
        [
            _doc(
                "10.1000/det-a",
                "Deep Learning Disease Detection",
                "We detect crop disease with deep learning and report mAP@0.5 "
                "on PlantVillage.",
            ),
            _doc(
                "10.1000/det-b",
                "UAV-Based Crop Monitoring",
                "Drones capture field images for disease detection.",
            ),
        ]
    )
    no_lexicon = distill_pool(pool)
    explicit = distill_pool(pool, DEFAULT_LEXICON)
    assert no_lexicon == explicit
    assert json.dumps(no_lexicon, sort_keys=True) == json.dumps(
        explicit, sort_keys=True
    )
    # Metadata shape unchanged since M0.4/5 plus the M0.6 topics layer.
    assert set(no_lexicon) == {
        "cache_key",
        "micro_taxonomy",
        "metrics",
        "datasets",
        "schools",
        "topics",
    }


def test_distill_pool_none_lexicon_means_default():
    pool = _pool(
        [_doc("10.1000/a", "Traffic Study", "We compute precise mAP@0.5 figures.")]
    )
    assert distill_pool(pool, None) == distill_pool(pool)
    assert distill_pool(pool, None)["metrics"] == {"mAP": 1}


# ---------------------------------------------------------------------------
# A fabricated non-CV lexicon detects its own domain and ignores CV defaults
# ---------------------------------------------------------------------------

ONCOLOGY_LEXICON = DomainLexicon(
    metrics={
        r"\bos\b": "OS",
        r"\bdfs\b": "DFS",
        r"\borr\b": "ORR",
        r"\bpfs\b": "PFS",
    },
    datasets={
        r"\btcga\b": "TCGA",
        r"\bgdc\b": "GDC",
    },
    schools={
        r"\bimmunotherapy\b": "immunotherapy",
        r"\bcheckpoint[ -]?inhibitors?\b": "checkpoint inhibitor",
    },
)


def _oncology_pool() -> dict:
    return _pool(
        [
            _doc(
                "10.3000/onc-1",
                "Oncology Outcomes",
                "We analyze overall survival (OS) and disease-free survival "
                "(DFS) in immunotherapy patients receiving checkpoint "
                "inhibitors, using TCGA expression data.",
            ),
            _doc(
                "10.3000/onc-2",
                "Response Prediction",
                "Objective response rate (ORR) and progression-free survival "
                "(PFS) predict survival in immunotherapy cohorts.",
            ),
            _doc(
                "10.3000/onc-3",
                "Benchmark Comparison",
                "We compare detection mAP@0.5 on COCO with our oncology "
                "imaging model.",
            ),
        ]
    )


def test_oncology_lexicon_detects_own_terms_and_not_cv():
    result = distill_pool(_oncology_pool(), ONCOLOGY_LEXICON)
    assert result["metrics"] == {"DFS": 1, "ORR": 1, "OS": 1, "PFS": 1}
    assert result["datasets"] == {"TCGA": 1}
    by_label = {s["label"]: s for s in result["schools"]}
    assert set(by_label) == {"immunotherapy", "checkpoint inhibitor"}
    assert by_label["immunotherapy"]["n"] == 2
    # CV-era terms must not leak even though the pool text mentions them.
    assert "mAP" not in result["metrics"]
    assert "COCO" not in result["datasets"]


def test_default_lexicon_on_oncology_pool_catches_broad_but_not_specialized():
    result = distill_pool(_oncology_pool())
    # The default now carries a curated cross-domain core (P6), so it picks up
    # the broad oncology-immunotherapy signals the pool mentions...
    assert result["metrics"] == {"mAP": 1}
    assert result["datasets"] == {"COCO": 1, "TCGA": 1}
    by_label = {s["label"]: s for s in result["schools"]}
    assert set(by_label) == {"oncology", "immunotherapy"}
    assert by_label["immunotherapy"]["n"] == 2
    # ...but a niche registry (the ONCOLOGY_LEXICON) is still required for the
    # specialized terms and sub-schools.
    assert "OS" not in result["metrics"]
    assert "DFS" not in result["metrics"]
    assert "checkpoint inhibitor" not in by_label


# ---------------------------------------------------------------------------
# P6: default lexicon gives non-CV pools schools/metrics signal on day one
# ---------------------------------------------------------------------------


def test_default_lexicon_surfaces_cross_domain_signal_without_any_lexicon_json():
    pool = _pool(
        [
            _doc(
                "10.4000/cli-1",
                "Attributing heat extremes",
                "Climate change intensifies drought and extreme precipitation; "
                "detection and attribution relies on climate models and "
                "reanalysis like ERA5.",
            ),
            _doc(
                "10.4000/fin-1",
                "Credit scoring with tree ensembles",
                "We train models for credit risk on default outcomes and "
                "benchmark each model's AUC and MCC.",
            ),
            _doc(
                "10.4000/edu-1",
                "Self-regulated learning dashboards",
                "Learning analytics dashboards support self-regulated "
                "learning; we report accuracy and RMSE on log traces.",
            ),
        ]
    )
    result = distill_pool(pool)
    schools = {s["label"]: s for s in result["schools"]}
    for expected in ("climate science", "drought", "precipitation", "credit risk"):
        assert schools[expected]["n"] == 1
    assert "learning analytics" in schools
    assert "self-regulated learning" in schools
    for expected in ("ERA5",):
        assert result["datasets"][expected] == 1
    for expected in ("AUC", "MCC"):
        assert result["metrics"][expected] == 1


# ---------------------------------------------------------------------------
# merge_lexicons: field-wise merge, extra wins, base untouched
# ---------------------------------------------------------------------------


def test_merge_lexicons_precedence_and_base_untouched():
    base = DomainLexicon(
        metrics={r"\bmap\b": "mAP", r"\bf1\b": "F1"},
        datasets={r"\bcoco\b": "COCO"},
        schools={r"\bdeep learning\b": "deep learning"},
    )
    extra = DomainLexicon(
        metrics={r"\bmap\b": "MAP-OVERRIDE", r"\bos\b": "OS"},
        datasets={},
        schools={},
    )
    merged = merge_lexicons(base, extra)
    # Overlapping key resolves to extra's label.
    assert merged.metrics[r"\bmap\b"] == "MAP-OVERRIDE"
    # Base-only key survives.
    assert merged.metrics[r"\bf1\b"] == "F1"
    assert merged.datasets[r"\bcoco\b"] == "COCO"
    assert merged.schools[r"\bdeep learning\b"] == "deep learning"
    # Extra-only key is added.
    assert merged.metrics[r"\bos\b"] == "OS"
    # Result is a new object; neither input is mutated.
    assert merged is not base
    assert merged is not extra
    assert base.metrics[r"\bmap\b"] == "mAP"
    assert extra.metrics[r"\bmap\b"] == "MAP-OVERRIDE"
    assert base.datasets == {r"\bcoco\b": "COCO"}


def test_merge_lexicons_plain_dict_inputs_and_independent_result():
    base = DomainLexicon(metrics={r"\ba\b": "A"}, datasets={}, schools={})
    extra_metrics = {r"\ba\b": "A2", r"\bb\b": "B"}
    extra = DomainLexicon(metrics=extra_metrics, datasets={}, schools={})
    merged = merge_lexicons(base, extra)
    assert merged.metrics == {r"\ba\b": "A2", r"\bb\b": "B"}
    # Mutating the merged field does not touch either input's dict.
    merged.metrics[r"\bb\b"] = "CHANGED"
    assert extra_metrics[r"\bb\b"] == "B"
    assert extra.metrics[r"\bb\b"] == "B"
    assert base.metrics[r"\ba\b"] == "A"
    assert merged.metrics[r"\ba\b"] == "A2"


def test_merge_lexicons_with_empty_extra_preserves_base():
    base = DomainLexicon(
        metrics={r"\bx\b": "X"},
        datasets={r"\by\b": "Y"},
        schools={r"\bz\b": "Z"},
    )
    merged = merge_lexicons(base, DomainLexicon(metrics={}, datasets={}, schools={}))
    assert merged.metrics == base.metrics
    assert merged.datasets == base.datasets
    assert merged.schools == base.schools


def test_merge_lexicons_onto_default_keeps_cv_metrics_when_adding_oncology():
    merged = merge_lexicons(
        DEFAULT_LEXICON,
        DomainLexicon(
            metrics={r"\bos\b": "OS"},
            datasets={r"\btcga\b": "TCGA"},
            schools={},
        ),
    )
    pool = _oncology_pool()
    result = distill_pool(pool, merged)
    # The field overlay inherits the CV defaults...
    assert result["metrics"]["mAP"] == 1
    assert result["datasets"]["COCO"] == 1
    # ...and adds its own patterns.
    assert result["metrics"]["OS"] == 1
    assert result["datasets"]["TCGA"] == 1