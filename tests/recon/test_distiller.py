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


# ---------------------------------------------------------------------------
# M0.6: classifier-grounded topics layer (T6.3)
# ---------------------------------------------------------------------------


def _topic_doc(doi: str, topics: list[dict]) -> dict:
    return {
        "id": f"openalex|{doi}",
        "provider": "openalex",
        "doi": doi,
        "title": f"Study {doi}",
        "abstract": "Edge inference for crop disease detection.",
        "year": 2022,
        "citations": 1,
        "oa_url": None,
        "topics": topics,
    }


def test_topics_layer_empty_when_pool_has_no_topics():
    pool = _pool([_doc("10.1000/a", "A Study", "disease detection.")])
    result = distill_pool(pool)
    assert result["topics"] == []
    assert distill_pool({"cache_key": "x", "docs": []})["topics"] == []
    assert distill_pool({})["topics"] == []


def test_topics_layer_aggregation_math_and_per_doc_max():
    doc_a = _topic_doc(
        "10.1000/b",
        [
            {"source": "openalex_topics", "id": "T1", "display_name": "Computer vision", "score": 0.8},
            {"source": "openalex_topics", "id": "T2", "display_name": "Computer vision", "score": 0.6},
            {"source": "openalex_topics", "id": "T3", "display_name": "Edge AI", "score": 0.9},
        ],
    )
    doc_b = _topic_doc(
        "10.1000/a",
        [
            {"source": "openalex_topics", "id": "T1", "display_name": "Computer vision", "score": 0.5},
            {"source": "openalex_topics", "id": "T4", "display_name": "Edge AI", "score": None},
        ],
    )
    result = distill_pool(_pool([doc_a, doc_b]))
    by_label = {t["label"]: t for t in result["topics"]}

    # Computer vision: doc a max 0.8 (two entries -> max wins), doc b 0.5;
    # pool score = mean(0.8, 0.5) = 0.65, n = 2, DOIs sorted.
    cv = by_label["Computer vision"]
    assert cv["n"] == 2
    assert cv["anchor_dois"] == ["10.1000/a", "10.1000/b"]
    assert cv["score"] == 0.65

    # Edge AI: doc a 0.9, doc b has no score -> mean over scored docs only.
    assert by_label["Edge AI"]["n"] == 2
    assert by_label["Edge AI"]["score"] == 0.9


def test_topics_require_doi_anchor():
    no_doi = {
        "id": "openalex|no-doi",
        "provider": "openalex",
        "doi": None,
        "title": "No DOI",
        "abstract": "abstract.",
        "year": 2022,
        "citations": 0,
        "oa_url": None,
        "topics": [
            {"source": "openalex_topics", "id": "T1", "display_name": "Ghost topic", "score": 1.0}
        ],
    }
    doi_doc = _topic_doc(
        "10.1000/a",
        [{"source": "openalex_topics", "id": "T2", "display_name": "Ghost topic", "score": 1.0}],
    )
    result = distill_pool(_pool([no_doi, doi_doc]))
    by_label = {t["label"]: t for t in result["topics"]}
    assert by_label["Ghost topic"]["n"] == 1
    assert by_label["Ghost topic"]["anchor_dois"] == ["10.1000/a"]


def test_topics_score_none_when_never_scored():
    pool = _pool(
        [
            _topic_doc(
                "10.1000/a",
                [{"source": "openalex_topics", "id": "T1", "display_name": "Untitled topic", "score": None}],
            ),
            _topic_doc(
                "10.1000/b",
                [{"source": "openalex_topics", "id": "T1", "display_name": "Untitled topic"}],
            ),
        ]
    )
    result = distill_pool(pool)
    assert result["topics"] == [
        {
            "label": "Untitled topic",
            "n": 2,
            "score": None,
            "anchor_dois": ["10.1000/a", "10.1000/b"],
        }
    ]


def test_topics_skip_empty_display_name():
    doc = _topic_doc(
        "10.1000/a",
        [
            {"source": "openalex_topics", "id": "T1", "display_name": "", "score": 1.0},
            {"source": "openalex_topics", "id": "T2", "display_name": None, "score": 1.0},
            {"source": "openalex_topics", "id": "T3", "display_name": "Real topic", "score": 0.7},
        ],
    )
    result = distill_pool(_pool([doc]))
    assert [t["label"] for t in result["topics"]] == ["Real topic"]


def test_topics_layer_deterministic_and_sorted_rerun():
    pool = _pool(
        [
            _topic_doc(
                "10.1000/a",
                [
                    {"source": "openalex_topics", "id": "T1", "display_name": "Alpha topic", "score": 0.9},
                    {"source": "openalex_topics", "id": "T2", "display_name": "Beta topic", "score": 0.4},
                ],
            ),
            _topic_doc(
                "10.1000/b",
                [{"source": "openalex_topics", "id": "T1", "display_name": "Alpha topic", "score": 0.7}],
            ),
            _topic_doc(
                "10.1000/c",
                [{"source": "openalex_topics", "id": "T3", "display_name": "Gamma topic", "score": 0.6}],
            ),
        ]
    )
    first = distill_pool(pool)
    second = distill_pool(pool)
    assert first["topics"] == second["topics"]
    assert json.dumps(first["topics"], sort_keys=True) == json.dumps(
        second["topics"], sort_keys=True
    )
    topics = first["topics"]
    assert [(t["label"], t["n"]) for t in topics] == sorted(
        [(t["label"], t["n"]) for t in topics], key=lambda kv: (-kv[1], kv[0])
    )
    assert topics[0] == {
        "label": "Alpha topic",
        "n": 2,
        "score": round((0.9 + 0.7) / 2, 4),
        "anchor_dois": ["10.1000/a", "10.1000/b"],
    }