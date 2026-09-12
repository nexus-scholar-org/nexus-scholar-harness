"""Hermetic tests for the term-frequency distiller (M0.2: T2.1-T2.6)."""

import json

import pytest

from scholar_harness.recon import distill, distill_pool


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


def test_anchored_term_freq_and_dois():
    pool = _pool(
        [
            _doc(
                "10.1000/leafnet-a",
                "A Deep Learning Method for Crop Disease Detection",
                "We present an approach that performs crop disease detection on "
                "UAV images. The model is a visible-light CNN trained for real "
                "time inference in the field.",
            ),
            _doc(
                "10.1000/leafnet-b",
                "Disease Detection in Plant Leaves Using Deep Learning",
                "We propose a CNN baseline for disease detection in plant "
                "leaves and evaluate its robustness under varying illumination.",
            ),
        ]
    )
    result = distill_pool(pool)

    terms = {t["term"]: t for t in result["micro_taxonomy"]}
    assert terms["disease detection"]["freq"] == 2
    assert terms["disease detection"]["anchor_dois"] == [
        "10.1000/leafnet-a",
        "10.1000/leafnet-b",
    ]
    assert terms["deep learning"]["freq"] == 2
    assert terms["deep learning"]["anchor_dois"] == [
        "10.1000/leafnet-a",
        "10.1000/leafnet-b",
    ]
    assert all(
        t["freq"] == len(t["anchor_dois"]) and t["freq"] >= 1
        for t in result["micro_taxonomy"]
    )


def test_unanchored_term_is_absent():
    pool = _pool(
        [
            _doc(
                "10.1000/leafnet-a",
                "Crop Disease Detection",
                "We study crop disease detection using a visible-light CNN.",
            ),
            _doc(
                "10.1000/leafnet-b",
                "Disease Detection in Plant Leaves",
                "We propose a CNN baseline for disease detection in plant leaves.",
            ),
            {
                "id": "openalex|no-doi",
                "provider": "openalex",
                "doi": None,
                "title": "Quantum Entanglement Teleportation",
                "abstract": "We teleport quantum states through entangled "
                "photon pairs across free-space channels.",
                "year": 2022,
                "citations": 3,
                "oa_url": None,
            },
        ]
    )
    result = distill_pool(pool)
    blob = json.dumps(result).lower()
    # Unique vocabulary contributed only by the DOI-less doc must never enter
    # the taxonomy, even when the DOI-less doc sits next to DOI-carrying docs.
    assert "quantum" not in blob
    assert "entanglement" not in blob
    assert "teleport" not in blob
    assert all("quantum" not in t["term"] for t in result["micro_taxonomy"])
    # Vocabulary from DOI-carrying docs must still surface, anchored to those
    # docs only.
    terms = {t["term"]: t for t in result["micro_taxonomy"]}
    assert terms["disease detection"]["freq"] == 2
    assert terms["disease detection"]["anchor_dois"] == [
        "10.1000/leafnet-a",
        "10.1000/leafnet-b",
    ]


def test_metrics_and_datasets_observed_only():
    pool = _pool(
        [
            _doc(
                "10.1000/bench-a",
                "Crop Disease Detection at Scale",
                "We evaluate the detection model with mAP@0.5 and report "
                "inference FPS over the PlantVillage collection.",
            )
        ]
    )
    result = distill_pool(pool)
    assert result["metrics"]["mAP"] >= 1
    assert result["metrics"]["FPS"] >= 1
    assert result["datasets"]["PlantVillage"] >= 1


def test_metrics_and_datasets_absent_when_unobserved():
    pool = _pool(
        [
            _doc(
                "10.1000/clean-a",
                "Greenhouse Tomato Cultivation",
                "We compare seasonal growth patterns under controlled "
                "temperature and humidity.",
            ),
            _doc(
                "10.1000/clean-b",
                "Leaf Sampling Protocol",
                "We detail a sampling procedure for phenotypic assessment of "
                "tomato leaves.",
            ),
        ]
    )
    result = distill_pool(pool)
    assert result["metrics"] == {}
    assert result["datasets"] == {}


def test_pass_metric_variants_match():
    pool = _pool(
        [
            _doc(
                "10.1000/code-a",
                "Code Repair Sampling",
                "We report pass_at_1 and pass_at_k on HumanEval.",
            ),
            _doc(
                "10.1000/code-b",
                "Decoder Sampling",
                "Greedy decoding is compared against pass@1 estimates.",
            ),
            _doc(
                "10.1000/code-c",
                "Unrelated Survey",
                "The pass runs in the corridor without issue.",
            ),
        ]
    )
    result = distill_pool(pool)
    assert result["metrics"]["pass@"] == 2


def test_deterministic_output_and_byte_identical_rerun(tmp_path):
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
    first = distill_pool(pool)
    second = distill_pool(pool)
    assert first == second
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)

    # Emitted list order is part of the contract: the micro-taxonomy is sorted
    # by (-freq, term) and schools by (-n, label).  A lost sort would break the
    # in-process order, not just cross-run byte equality.
    taxonomy = first["micro_taxonomy"]
    assert taxonomy[0]["freq"] == max(t["freq"] for t in taxonomy)
    assert [(t["freq"], t["term"]) for t in taxonomy] == sorted(
        [(t["freq"], t["term"]) for t in taxonomy], key=lambda kv: (-kv[0], kv[1])
    )
    schools = first["schools"]
    assert [(s["label"], s["n"]) for s in schools] == sorted(
        [(s["label"], s["n"]) for s in schools], key=lambda kv: (-kv[1], kv[0])
    )

    pool_path = tmp_path / "pool.json"
    pool_path.write_text(json.dumps(pool), encoding="utf-8")
    out_a = distill(pool_path, tmp_path / "terms-a.json")
    out_b = distill(pool_path, tmp_path / "terms-b.json")
    assert out_a.read_bytes() == out_b.read_bytes()


def test_empty_pool_yields_empty_payload():
    result = distill_pool({"cache_key": "v1/openalex/y2000-2026/q/x", "docs": []})
    assert result["cache_key"] == "v1/openalex/y2000-2026/q/x"
    assert result["micro_taxonomy"] == []
    assert result["metrics"] == {}
    assert result["datasets"] == {}
    assert result["schools"] == []


def test_missing_or_doi_less_docs_do_not_crash():
    result = distill_pool({})
    assert result["cache_key"] == ""
    assert result["micro_taxonomy"] == []
    assert result["metrics"] == {}
    assert result["schools"] == []

    no_anchors = distill_pool(
        {
            "docs": [
                {"doi": None, "title": "disease detection", "abstract": "disease detection"},
                {"doi": "10.1000/x", "title": "", "abstract": ""},
            ]
        }
    )
    assert no_anchors["micro_taxonomy"] == []


def test_schools_heuristic_detects_two_schools():
    pool = _pool(
        [
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
    by_label = {s["label"]: s for s in result["schools"]}
    assert set(by_label) == {"UAV/drone", "language model/LLM"}
    assert by_label["UAV/drone"]["n"] == 1
    assert by_label["UAV/drone"]["anchor_dois"] == ["10.1000/uav"]
    assert by_label["language model/LLM"]["n"] == 1
    assert by_label["language model/LLM"]["anchor_dois"] == ["10.1000/llm"]


def test_distill_file_wrapper_roundtrip(tmp_path):
    pool = _pool(
        [_doc("10.1000/rt", "Crop Disease Detection", "We detect crop disease with deep learning.")]
    )
    pool_path = tmp_path / "pool.json"
    pool_path.write_text(json.dumps(pool), encoding="utf-8")
    out = distill(pool_path, tmp_path / "terms.json")
    assert out == (tmp_path / "terms.json")
    assert out.exists()
    assert json.loads(out.read_text(encoding="utf-8")) == distill_pool(pool)
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["cache_key"] == pool["cache_key"]
    assert all(t["freq"] >= 1 for t in loaded["micro_taxonomy"])


def test_distill_refuses_workspaces_output(tmp_path):
    pool_path = tmp_path / "pool.json"
    pool_path.write_text(json.dumps(_pool([])), encoding="utf-8")
    with pytest.raises(RuntimeError, match="workspaces"):
        distill(pool_path, tmp_path / "workspaces" / "terms.json")
    assert not (tmp_path / "workspaces").exists()