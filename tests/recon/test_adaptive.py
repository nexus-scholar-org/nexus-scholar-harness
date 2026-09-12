"""Hermetic tests for M0.4 adaptive probe horizon (T4.1-T4.4).

All merges/plans are pure in-memory; the end-to-end tests drive a
``ReconEngine`` with an injected fake ``search_fn``, so no provider network
is ever touched.
"""

import asyncio
import json
import re

from scholar_search.models import Document, ExternalIds, Query

from scholar_harness.recon import POOL_MAX, ReconEngine, distill_pool
from scholar_harness.recon.adaptive import (
    execute_followups,
    merge_pools,
    plan_followups,
)

THIN_TERM = "edge inference"

_REASON_RE = re.compile(r"^\d+ direct hits, \d+ adjacent$")


def _doc(doi: str, title: str, abstract: str) -> dict:
    return {
        "id": f"openalex|{doi}",
        "provider": "openalex",
        "doi": doi,
        "title": title,
        "abstract": abstract,
        "year": 2023,
        "citations": 2,
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
# T4.1/T4.2: thin sub-school detection + confidence reason strings
# ---------------------------------------------------------------------------


def _thin_pool() -> dict:
    """Two direct edge-inference docs plus one modernization-adjacent doc.

    The third doc carries ``inference`` vocabulary (sharing a micro-taxonomy
    term with the school's anchors) but not the ``edge inference`` phrase, so
    it is adjacent, not a direct hit: total docs in school = 3, direct = 2,
    so the reason is "2 direct hits, 1 adjacent".
    """
    return _pool(
        [
            _doc(
                "10.1000/edge-a",
                "Edge Inference Disease Detection",
                "We run edge inference on embedded hardware.",
            ),
            _doc(
                "10.1000/edge-b",
                "Real-Time Edge Inference in Orchards",
                "Edge inference detects crop disease with a small CNN.",
            ),
            _doc(
                "10.1000/robot-c",
                "Field Survey Robots",
                "An inference pipeline for orchard robots using "
                "visible-light cameras.",
            ),
        ]
    )


def test_thin_school_triggers_followup_with_confidence_reason():
    pool = _thin_pool()
    distilled = distill_pool(pool)
    schools = {s["label"]: s for s in distilled["schools"]}
    assert THIN_TERM in schools
    assert schools[THIN_TERM]["n"] == 2

    followups = plan_followups(distilled, pool)
    assert len(followups) >= 1
    candidate = next(c for c in followups if c["term"] == THIN_TERM)
    assert candidate["triggered"] is True
    assert candidate["school_n"] == 2
    assert candidate["school_n"] <= 2
    # Exact confidence format: direct hits + residual docs, both counts.
    assert candidate["reason"] == "2 direct hits, 1 adjacent"
    assert _REASON_RE.fullmatch(candidate["reason"])


def test_reason_format_matches_documented_regex():
    pool = _thin_pool()
    distilled = distill_pool(pool)
    for candidate in plan_followups(distilled, pool):
        assert _REASON_RE.fullmatch(candidate["reason"])
        assert candidate["reason"]


def test_healthy_school_not_triggered():
    pool = _pool(
        [
            _doc(
                f"10.1000/drone-{i:02d}",
                f"Orchard Survey {i}",
                "We counted trees using fixed-wing drones over large orchards "
                "and compared the census with ground sampling.",
            )
            for i in range(5)
        ]
    )
    distilled = distill_pool(pool)
    assert distilled["schools"][0]["label"] == "UAV/drone"
    assert distilled["schools"][0]["n"] == 5
    assert plan_followups(distilled, pool) == []


def test_plan_followups_ordering_is_documented_rule():
    pool = _pool(
        [
            _doc("10.1000/a1", "Alpha Study", "edge inference runtime."),
            _doc("10.1000/g1", "Gamma Study", "edge inference survey."),
            _doc("10.1000/z1", "Zeta One", "edge inference systems."),
            _doc("10.1000/z2", "Zeta Two", "edge inference models."),
        ]
    )
    distilled = {
        "micro_taxonomy": [],
        "schools": [
            {"label": THIN_TERM, "n": 2, "anchor_dois": ["10.1000/z1", "10.1000/z2"]},
            {"label": "alpha-edge", "n": 1, "anchor_dois": ["10.1000/a1"]},
            {"label": "gamma-edge", "n": 1, "anchor_dois": ["10.1000/g1"]},
        ],
    }
    # Deterministic rule: ascending school_n, then case-folded term.
    assert [c["term"] for c in plan_followups(distilled, pool)] == [
        "alpha-edge",
        "gamma-edge",
        THIN_TERM,
    ]


def test_plan_followups_deterministic():
    pool = _thin_pool()
    distilled = distill_pool(pool)
    first = plan_followups(distilled, pool)
    second = plan_followups(distilled, pool)
    assert first == second
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_empty_and_edge_cases():
    assert plan_followups({}, {}) == []
    assert plan_followups({"schools": []}, _pool([])) == []
    empty_pool = _pool([])
    assert plan_followups(distill_pool(empty_pool), empty_pool) == []


def test_school_anchors_missing_from_pool_not_triggered():
    distilled = {
        "schools": [
            {"label": THIN_TERM, "n": 1, "anchor_dois": ["10.1000/not-in-pool"]}
        ]
    }
    assert plan_followups(distilled, _pool([])) == []


# ---------------------------------------------------------------------------
# M0.6 (T6.4): thin classifier-grounded topics trigger follow-ups
# ---------------------------------------------------------------------------


def _topic_doc(doi: str, label: str, score: float | None = 0.9) -> dict:
    return {
        "id": f"openalex|{doi}",
        "provider": "openalex",
        "doi": doi,
        "title": f"Study {doi}",
        "abstract": "Edge inference for crop disease detection.",
        "year": 2023,
        "citations": 2,
        "oa_url": None,
        "topics": [
            {"source": "openalex_topics", "id": f"T-{doi}", "display_name": label, "score": score}
        ],
    }


def test_thin_topic_triggers_followup_with_non_empty_reason():
    pool = _pool(
        [
            _topic_doc("10.1000/t1", "Thin topic", 0.8),
            _topic_doc("10.1000/t2", "Thin topic", 0.7),
        ]
    )
    distilled = distill_pool(pool)
    assert {t["label"] for t in distilled["topics"]} == {"Thin topic"}
    candidate = next(c for c in plan_followups(distilled, pool) if c["term"] == "Thin topic")
    assert candidate["triggered"] is True
    assert candidate["school_n"] == 2
    assert candidate["reason"]
    assert _REASON_RE.fullmatch(candidate["reason"])


def test_healthy_topic_not_triggered():
    pool = _pool(
        [
            _topic_doc(f"10.1000/h{i:02d}", "Healthy topic", 0.9) for i in range(4)
        ]
    )
    distilled = distill_pool(pool)
    assert all(t["n"] > 2 for t in distilled["topics"])
    assert all(c["term"] != "Healthy topic" for c in plan_followups(distilled, pool))


def test_school_and_topic_same_label_dedup_keeps_first():
    pool = _pool(
        [
            _topic_doc("10.1000/a", THIN_TERM, 0.8),
        ]
    )
    distilled = distill_pool(pool)
    # Force a school with the same label as the topic: the school candidate
    # (emitted first) must win; the topic candidate is dropped.
    distilled["schools"] = [
        {"label": THIN_TERM, "n": 1, "anchor_dois": ["10.1000/a"]}
    ]
    followups = plan_followups(distilled, pool)
    assert [c["term"] for c in followups] == [THIN_TERM]
    assert len(followups) == 1
    assert followups[0]["school_n"] == 1
    assert _REASON_RE.fullmatch(followups[0]["reason"])


def test_topic_candidates_share_the_documented_ordering_rule():
    pool = _pool(
        [
            _topic_doc("10.1000/a", "Zebra topic", 0.5),
            _topic_doc("10.1000/b", "Alpha topic", 0.5),
        ]
    )
    distilled = distill_pool(pool)
    candidates = [
        c for c in plan_followups(distilled, pool) if c["term"].endswith("topic")
    ]
    assert [c["term"] for c in candidates] == ["Alpha topic", "Zebra topic"]


# ---------------------------------------------------------------------------
# T4.3 merge semantics: DOI-union, 25-cap, full entries, cache keys
# ---------------------------------------------------------------------------


def _merge_originals(n: int) -> list[dict]:
    return [
        _doc(f"10.0000/orig-{i:02d}", "Original", "Crop monitoring field trials.")
        for i in range(n)
    ]


def test_merge_respects_pool_cap():
    originals = _merge_originals(20)
    followup = [
        _doc(f"10.0000/fu-{i:02d}", "Followup", "Refined edge inference surveys.")
        for i in range(10)
    ]
    merged = merge_pools([_pool(originals), _pool(followup, "v1/.../k-followup")])
    assert len(merged["docs"]) == POOL_MAX == 25
    assert [d["doi"] for d in merged["docs"][:20]] == [d["doi"] for d in originals]
    assert [d["doi"] for d in merged["docs"][20:]] == [
        d["doi"] for d in followup[:5]
    ]


def test_merge_keeps_full_pool_entries():
    originals = [_doc("10.0000/orig-00", "Original", "Field trials report canopy status.")]
    merged = merge_pools(
        [_pool(originals), _pool([_doc("10.0000/new-00", "New", "Edge inference study.")])]
    )
    for entry in merged["docs"]:
        for key in ("id", "provider", "doi", "title", "abstract", "year", "citations", "oa_url"):
            assert key in entry


def test_merge_dedups_by_doi_case_insensitive():
    originals = [_doc("10.1000/shared-01", "Original Version", "First abstract.")]
    followup = [
        _doc("10.1000/SHARED-01", "Duplicate Version", "Same DOI, different title."),
        _doc("10.1000/brand-new", "Brand New", "Fresh evidence."),
    ]
    merged = merge_pools([_pool(originals), _pool(followup)])
    assert len(merged["docs"]) == 2
    assert [d["doi"] for d in merged["docs"]] == [
        "10.1000/shared-01",
        "10.1000/brand-new",
    ]
    # The original entry survives dedup, not the duplicate.
    assert merged["docs"][0]["title"] == "Original Version"


def test_merge_preserves_followup_cache_keys():
    original = _pool([_doc("10.1000/a", "A", "Abstract a")], "v1/openalex/y2000-2026/q/orig")
    fu_a = _pool([_doc("10.1000/b", "B", "Abstract b")], "v1/openalex/y2000-2026/q/cand-a")
    fu_b = _pool([_doc("10.1000/c", "C", "Abstract c")], "v1/openalex/y2000-2026/q/cand-a")
    fu_c = _pool([_doc("10.1000/d", "D", "Abstract d")], "v1/openalex/y2000-2026/q/cand-b")
    merged = merge_pools([original, fu_a, fu_b, fu_c])
    assert merged["cache_key"] == original["cache_key"]
    assert merged["merged_from_cache_keys"] == [
        "v1/openalex/y2000-2026/q/cand-a",
        "v1/openalex/y2000-2026/q/cand-b",
    ]


def test_merge_empty_and_cap_already_full():
    assert merge_pools([]) == {"docs": [], "merged_from_cache_keys": []}
    full = _pool(_merge_originals(POOL_MAX), "v1/.../full")
    followup = [_doc("10.0000/fu-00", "Followup", "Spillover.")]
    merged = merge_pools([full, _pool(followup, "v1/.../fu")])
    assert len(merged["docs"]) == POOL_MAX
    assert merged["merged_from_cache_keys"] == ["v1/.../fu"]


# ---------------------------------------------------------------------------
# T4.3/T4.4 driver: bounded follow-up probes through the engine
# ---------------------------------------------------------------------------


def _fake_doc(doi: str, title: str, abstract: str) -> Document:
    return Document(
        title=title,
        year=2023,
        provider="openalex",
        provider_id="W" + doi.replace("/", "").replace(":", "")[:20],
        external_ids=ExternalIds(doi=doi),
        abstract=abstract,
        citations_count=4,
        url=f"https://example.org/{doi}",
    )


def _topic_docs() -> list[Document]:
    return [
        _fake_doc(
            "10.1000/edge-a",
            "Edge Inference Disease Detection",
            "We run edge inference on embedded hardware.",
        ),
        _fake_doc(
            "10.1000/edge-b",
            "Real-Time Edge Inference in Orchards",
            "Edge inference detects crop disease with a small CNN.",
        ),
        _fake_doc(
            "10.1000/robot-c",
            "Field Survey Robots",
            "An inference pipeline for orchard robots using visible-light cameras.",
        ),
    ]


def _followup_docs() -> list[Document]:
    return [
        _fake_doc(
            "10.1000/fu-1",
            "Edge Inference Benchmarks",
            "Comparing edge inference frameworks for on-device vision.",
        ),
        _fake_doc(
            "10.1000/fu-2",
            "Edge Inference Acceleration",
            "Hardware acceleration for edge inference workloads.",
        ),
        _fake_doc(
            "10.1000/fu-3",
            "Embedded Inference Systems",
            "A system survey of embedded inference for field robots.",
        ),
    ]


def test_execute_followups_probes_bounded_and_merges(tmp_path):
    calls = []
    topic = "drone crop disease detection"

    def search_fn(query: Query, providers: list[str]):
        calls.append(query.text)
        if query.text == topic:
            return _topic_docs()
        return _followup_docs()

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    pool_path, _n = asyncio.run(engine.probe(topic))
    pool = json.loads(pool_path.read_text(encoding="utf-8"))
    distilled = distill_pool(pool)

    followups = plan_followups(distilled, pool)
    assert followups and followups[0]["term"] == THIN_TERM
    assert followups[0]["triggered"] is True
    assert _REASON_RE.fullmatch(followups[0]["reason"])

    result = asyncio.run(execute_followups(pool, distilled, engine))

    # Bounded: exactly one follow-up probe (one thin school, <= 3 budget),
    # issued in addition to the original topic probe.
    assert calls == [topic, THIN_TERM]
    assert result["followups"] == [followups[0]]
    assert len(result["cache_keys_merged"]) == 1
    assert result["cache_keys_merged"][0].startswith("v1/")
    assert result["cache_keys_merged"][0] != pool["cache_key"]
    assert result["dropped_n"] == 0
    # The follow-up pool file itself rests under the engine cache root.
    assert len(list((tmp_path / "cache" / "pools").glob("*_pool.json"))) == 2

    # Merged pool: 3 original + 3 follow-up docs, all full entries, cap held.
    merged = result["pool"]
    assert len(merged["docs"]) == 6
    assert len(merged["docs"]) <= POOL_MAX
    assert len({d["doi"] for d in merged["docs"]}) == 6
    assert merged["cache_key"] == pool["cache_key"]
    for entry in merged["docs"]:
        for key in ("id", "provider", "doi", "title", "abstract", "year", "citations", "oa_url"):
            assert key in entry
    # Every merged doc that came from a follow-up pool still carries its own
    # metadata fields (full-entry check above); merged metadata keeps lineage.
    assert "merged_from_cache_keys" in merged
    assert merged["merged_from_cache_keys"] == result["cache_keys_merged"]

    # Re-distilled on the merged pool: the school is now denser, no re-clutter.
    re_schools = {s["label"]: s for s in result["distilled"]["schools"]}
    assert re_schools[THIN_TERM]["n"] == 4

    # Idempotent re-run: cache hit -> no new search_fn calls, identical merge.
    calls_before = len(calls)
    second = asyncio.run(execute_followups(pool, distilled, engine))
    assert len(calls) == calls_before
    assert second == result


def test_execute_followups_dedups_duplicate_followup_doi(tmp_path):
    def search_fn(query: Query, providers: list[str]):
        if query.text == THIN_TERM:
            # Re-returns the original doc (same DOI) plus one brand-new doc.
            return [_topic_docs()[0], _fake_doc("10.1000/fu-new", "New Evidence", "edge inference on edge devices.")]
        return [_topic_docs()[0]]

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    pool_path, _n = asyncio.run(engine.probe("edge computing for orchards"))
    pool = json.loads(pool_path.read_text(encoding="utf-8"))
    distilled = distill_pool(pool)

    result = asyncio.run(execute_followups(pool, distilled, engine))
    assert len(result["pool"]["docs"]) == 2
    assert len({d["doi"] for d in result["pool"]["docs"]}) == 2
    assert result["dropped_n"] == 0


def test_execute_followups_records_dropped_n_at_cap(tmp_path):
    topic = "orchard drone census"

    def search_fn(query: Query, providers: list[str]):
        if query.text == THIN_TERM:
            return [_fake_doc(f"10.9110/fu-{i:02d}", "Followup", "edge inference surveys next.") for i in range(5)]
        drones = [
            _fake_doc(
                f"10.9110/drone-{i:02d}",
                f"Orchard Survey {i}",
                "We counted trees using fixed-wing drones over large orchards.",
            )
            for i in range(22)
        ]
        edges = [
            _fake_doc(
                f"10.9110/edge-{i:02d}",
                f"Edge Inference Study {i}",
                "We run edge inference on embedded hardware.",
            )
            for i in range(2)
        ]
        return drones + edges

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    pool_path, _n = asyncio.run(engine.probe(topic))
    pool = json.loads(pool_path.read_text(encoding="utf-8"))
    distilled = distill_pool(pool)

    candidates = plan_followups(distilled, pool)
    assert [c["term"] for c in candidates] == [THIN_TERM]
    assert candidates[0]["school_n"] == 2

    result = asyncio.run(execute_followups(pool, distilled, engine))
    # 24 originals + 25th slot go to follow-up docs; the remaining 4 new
    # follow-up DOIs are discarded and counted.
    assert len(result["pool"]["docs"]) == POOL_MAX == 25
    assert result["dropped_n"] == 4
    assert len(result["cache_keys_merged"]) == 1


def test_execute_followups_no_candidates_returns_original(tmp_path):
    def search_fn(query: Query, providers: list[str]):
        return [
            _fake_doc(
                f"10.1000/d-{i:02d}",
                f"Orchard Survey {i}",
                "We counted trees using fixed-wing drones over large orchards.",
            )
            for i in range(5)
        ]

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    pool_path, _n = asyncio.run(engine.probe("orchard drone census"))
    pool = json.loads(pool_path.read_text(encoding="utf-8"))
    distilled = distill_pool(pool)
    assert plan_followups(distilled, pool) == []

    result = asyncio.run(execute_followups(pool, distilled, engine))
    # Cheap path: original pool/distilled returned unchanged, nothing probed.
    assert result["followups"] == []
    assert result["cache_keys_merged"] == []
    assert result["dropped_n"] == 0
    assert result["pool"] == pool
    assert result["pool"]["docs"] == pool["docs"]
    assert "merged_from_cache_keys" not in result["pool"]
    assert result["distilled"] == distilled
    # No follow-up pools were ever persisted.
    assert len(list((tmp_path / "cache" / "pools").glob("*_pool.json"))) == 1