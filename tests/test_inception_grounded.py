"""Hermetic tests for the M0.3 ``--grounded`` wizard flag (T3.1-T3.7).

Walks ``run_wizard`` end-to-end with a scripted responder and an injected
``ReconEngine`` whose ``search_fn`` is a fake callable, so no provider
network is ever touched.

M0.3 DoD 3 hardening covered here:
- grounded Stage-4b defaults are pool-anchored only (never draft_default_concepts);
- every shipped concept/synonym is anchored in the session anchored-term map;
- a supplementary probe with zero anchors drops a synonym and aborts a concept;
- an empty/sparse pool hard-aborts the wizard.
"""

import asyncio
import json

import pytest
import typer
from scholar_search.models import Document, ExternalIds, Query
from typer.testing import CliRunner

import scholar_harness.recon.engine as recon_engine_module
from scholar_harness.cli import app
from scholar_harness.inception import (
    _grounded_default_concepts,
    draft_default_concepts,
    run_wizard,
)
from scholar_harness.recon import ReconEngine, distill_pool

GENESIS_TS = "2026-09-06T12:00:00+00:00"

TOPIC = (
    "Can an on-device computer-vision weed-detection pipeline achieve real-time "
    "frame rates on embedded hardware without sacrificing classification accuracy?"
)

GROUNDED_CONCEPT = "grape disease detection"
GROUNDED_DOIS = [f"10.1000/ground-{i:03d}" for i in range(3)]
SYNONYM_A_DOI = "10.1000/syn-a-001"

BASE_DESCRIPTION = (
    "Phase-0 Inception: 'On-Device Weed Detection for Embedded Agriculture' "
    "[Design Science, DESIGN_SCIENCE] compiled protocol fingerprint "
)

# Answers shared by every wizard walk, in wizard prompt order.
_TAIL_COMMON = [
    "Design Science",  # paradigm choice
    "DESIGN_SCIENCE",  # playbook choice
    False,             # add secondary paradigm?
    "embedded crop-field RGB cameras running weed-detection models",
    "mIoU and FPS measurements on a public benchmark suite with ablation studies",
    "closed-source models, pre-2022 studies",
    False,             # set date window?
    (
        "Can an on-device weed-detection pipeline achieve real-time frame rates "
        "on embedded hardware without sacrificing classification accuracy?"
    ),
    False,             # add RQ2?
    None,              # core search concepts -> use the prompt default
    # <one synonym answer per default concept goes here>
    False,             # manual inclusion?
    False,             # manual exclusion?
    False,             # configure matrix?
    True,              # verification flags all-on?
    "On-Device Weed Detection for Embedded Agriculture",
    "Dr. Mouadh",      # lead researcher
    "",                # venue
    "",                # timeline
    None,              # num_if_valid(timeline)
    True,              # emit protocol + scaffold?
]


def _wizard_answers(n_concepts: int) -> list:
    synonyms = [""] * n_concepts
    return _TAIL_COMMON[:10] + synonyms + _TAIL_COMMON[10:]


def _grounded_answers(choice_script, n_concepts: int = 4) -> list:
    return [TOPIC, choice_script] + _wizard_answers(n_concepts)


def _plain_answers() -> list:
    # Without --grounded there is no recon choice prompt, and the default
    # concept dump holds three entries (no grounded concept prepended).
    return [TOPIC] + _wizard_answers(3)


def _doc(doi: str, title: str, abstract: str, year: int = 2023) -> Document:
    return Document(
        title=title,
        year=year,
        provider="openalex",
        provider_id="W" + doi.replace("/", "").replace(":", "")[:20],
        external_ids=ExternalIds(doi=doi),
        abstract=abstract,
        citations_count=5,
        url=f"https://example.org/{doi}",
    )


def _fake_docs(n: int) -> list[Document]:
    abstracts = [
        "We benchmark grape disease detection on an embedded orchard vision system with aerial field images.",
        "Automated grape disease detection improves yield monitoring accuracy for precision agriculture practitioners.",
        "A review of grape disease detection techniques for vineyard robots reports open challenges.",
    ]
    return [
        _doc(GROUNDED_DOIS[i % 3], f"Fake Doc {i}", abstracts[i % len(abstracts)])
        for i in range(n)
    ]


def _pool_anchored_defaults(engine: ReconEngine) -> list[str]:
    """Distill the fake topic pool and predict the grounded Stage-4b defaults.

    The wizard's own topic probe later hits the same cache entry, so the
    prediction is byte-deterministic and consumes no extra ``search_fn`` call.
    """
    pool_path, _n = asyncio.run(engine.probe(TOPIC))
    pool = json.loads(pool_path.read_text(encoding="utf-8"))
    return _grounded_default_concepts(distill_pool(pool), GROUNDED_CONCEPT)


class GroundedScriptedResponder:
    """Scripted responder; ``None`` answers fall back to the prompt default."""

    sequenceless = True

    def __init__(self, answers):
        self.answers = list(answers)

    def _take(self):
        if not self.answers:
            raise AssertionError(
                f"GroundedScriptedResponder exhausted; {len(self.answers)} answers left"
            )
        return self.answers.pop(0)

    def text(self, message, default=""):
        value = self._take()
        return default if value is None else value

    def confirm(self, message, default=True):
        value = self._take()
        return default if value is None else value

    def choice(self, message, choices, default=""):
        value = self._take()
        if value is None:
            return default or choices[0][0]
        return value

    def multi(self, message, choices):
        value = self._take()
        return choices if value is None else value

    def num_if_valid(self, raw):
        return self._take()


def _read_genesis(ws_dir):
    journal = (
        (ws_dir / "audit" / "journal.jsonl").read_text(encoding="utf-8").strip().splitlines()
    )
    return next(evt for evt in map(json.loads, journal) if evt["action"] == "GENESIS")


# ---------------------------------------------------------------------------
# T3.1: the --grounded flag is user-visible on the inception command
# ---------------------------------------------------------------------------


def test_inception_help_lists_grounded_flag():
    result = CliRunner().invoke(app, ["inception", "--help"])
    assert result.exit_code == 0
    assert "--grounded" in result.stdout
    assert "--no-scaffold" in result.stdout


# ---------------------------------------------------------------------------
# T3.1/T3.7: without --grounded the behavior stays byte-identical
# ---------------------------------------------------------------------------


def test_without_grounded_never_constructs_engine_or_cache(tmp_path, monkeypatch):
    def _explode(*args, **kwargs):
        raise AssertionError("ReconEngine constructed without --grounded")

    monkeypatch.setattr(recon_engine_module, "ReconEngine", _explode)
    monkeypatch.chdir(tmp_path)

    result = run_wizard(
        GroundedScriptedResponder(_plain_answers()),
        tmp_path,
        genesis_timestamp=GENESIS_TS,
    )

    assert result["recon_context"] is None
    assert not (tmp_path / ".cache").exists()

    ws = tmp_path / "workspaces" / result["slug"]
    genesis = _read_genesis(ws)
    assert genesis["description"] == BASE_DESCRIPTION + result["protocol_fingerprint"]
    assert "recon_context" not in genesis["description"]


def test_without_grounded_byte_identical_summary(tmp_path):
    result = run_wizard(
        GroundedScriptedResponder(_plain_answers()),
        tmp_path,
        genesis_timestamp=GENESIS_TS,
    )
    assert result["slug"] == "on-device-weed-detection-for-embedded-agriculture"
    assert result["playbook"] == "DESIGN_SCIENCE"
    assert result["paradigm"] == "Design Science"
    assert result["title"] == "On-Device Weed Detection for Embedded Agriculture"
    assert result["recon_context"] is None
    assert "concept" not in result


# ---------------------------------------------------------------------------
# T3.2-T3.5/T3.7: --grounded end-to-end with an injected fake-search engine
# ---------------------------------------------------------------------------


def test_grounded_wizard_presents_direction_and_records_recon_context(tmp_path):
    calls = []

    def search_fn(query: Query, providers: list[str]):
        calls.append((query.text, tuple(providers)))
        return _fake_docs(3)

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    n_concepts = len(_pool_anchored_defaults(engine))
    result = run_wizard(
        GroundedScriptedResponder(_grounded_answers(None, n_concepts)),
        tmp_path,
        genesis_timestamp=GENESIS_TS,
        grounded=True,
        recon_engine=engine,
    )

    # One probe on the exact topic text; no delta in this walk.
    assert [c[0] for c in calls] == [TOPIC]

    rc = result["recon_context"]
    assert rc is not None
    assert len(rc["session_id"]) == 12
    assert rc["cache_keys"] and all(k.startswith("v1/") for k in rc["cache_keys"])
    assert rc["pool_sizes"] == [3]
    assert set(rc["anchor_dois"]) == set(GROUNDED_DOIS)
    assert len(rc["anchor_dois"]) >= 2

    # The pool was written under the injected cache root.
    assert len(list((tmp_path / "cache" / "pools").glob("*_pool.json"))) == 1

    # The validated direction flows into the existing IntentPacket -> protocol.
    assert rc["concept"] == GROUNDED_CONCEPT
    ws = tmp_path / "workspaces" / result["slug"]
    intent = json.loads((ws / "intent.json").read_text(encoding="utf-8"))
    assert intent["core_concepts"][0]["concept"] == GROUNDED_CONCEPT
    assert intent["core_concepts"][0]["synonyms"] == []

    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    assert protocol["search_strategy"]["core_concepts"][0]["concept"] == GROUNDED_CONCEPT

    # M0.3 DoD 3: EVERY shipped concept and synonym is anchored in the session.
    for concept in intent["core_concepts"]:
        assert concept["concept"] in rc["anchored_terms"]
        assert rc["anchored_terms"][concept["concept"]]
        for syn in concept["synonyms"]:
            assert syn in rc["anchored_terms"]

    # GENESIS carries the full recon_context embedded in the description.
    genesis = _read_genesis(ws)
    assert genesis["description"].startswith(BASE_DESCRIPTION)
    assert "recon_context=" in genesis["description"]
    rc_json = json.loads(genesis["description"].split("recon_context=", 1)[1])
    for key in ("session_id", "cache_keys", "pool_sizes", "anchor_dois", "anchored_terms"):
        assert key in rc_json
    assert rc_json["pool_sizes"] == [3]
    assert rc_json["cache_keys"] == rc["cache_keys"]
    assert rc_json["anchor_dois"] == rc["anchor_dois"]


# ---------------------------------------------------------------------------
# T3.3: every presented direction cites >= 2 distinct DOIs from the pool
# ---------------------------------------------------------------------------


def test_grounded_directions_require_two_anchors():
    from scholar_harness.inception import _grounded_directions_for_terms

    pool_terms = {
        "micro_taxonomy": [
            {"term": "one-shot term", "freq": 1, "anchor_dois": ["10.1000/x"]},
            {"term": "grape disease detection", "freq": 3, "anchor_dois": GROUNDED_DOIS},
        ]
    }
    directions = _grounded_directions_for_terms(pool_terms)
    assert len(directions) == 1
    assert directions[0]["label"] == "grape disease detection"
    assert len(directions[0]["anchor_dois"]) == 3
    assert all(len(d["anchor_dois"]) >= 2 for d in directions)


def test_grounded_no_direction_when_pool_empty():
    from scholar_harness.inception import _grounded_directions_for_terms

    assert _grounded_directions_for_terms({"micro_taxonomy": []}) == []


def test_grounded_sparse_pool_merges_terms_to_keep_two_anchors():
    from scholar_harness.inception import _grounded_directions_for_terms

    # A sparse pool may only show singleton terms; the proposer merges the
    # top terms until a direction carries >= 2 real anchor DOIs.
    lonely = {
        "micro_taxonomy": [
            {"term": "a", "freq": 1, "anchor_dois": ["10.1000/x"]},
            {"term": "b", "freq": 1, "anchor_dois": ["10.1000/y"]},
        ]
    }
    directions = _grounded_directions_for_terms(lonely)
    assert len(directions) == 1
    assert directions[0]["anchor_dois"] == ["10.1000/x", "10.1000/y"]
    assert len(directions[0]["anchor_dois"]) >= 2


# ---------------------------------------------------------------------------
# M0.3 DoD 2: an empty/sparse pool hard-aborts (no warn-and-continue)
# ---------------------------------------------------------------------------


def test_grounded_empty_pool_hard_aborts_with_guidance(tmp_path):
    def search_fn(query: Query, providers: list[str]):
        return []

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    with pytest.raises(typer.Exit) as exc:
        run_wizard(
            GroundedScriptedResponder([TOPIC]),
            tmp_path,
            genesis_timestamp=GENESIS_TS,
            grounded=True,
            recon_engine=engine,
        )
    assert "literature evidence" in str(exc.value)
    assert "without --grounded" in str(exc.value)
    assert not (tmp_path / "workspaces").exists()


# ---------------------------------------------------------------------------
# M0.3 DoD 3: grounded defaults are pool-anchored ONLY
# ---------------------------------------------------------------------------


def test_grounded_default_concepts_are_pool_anchored_only(tmp_path):
    def search_fn(query: Query, providers: list[str]):
        return _fake_docs(3)

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    expected = _pool_anchored_defaults(engine)

    # Sanity: the terms that WERE the old unanchored default come from
    # draft_default_concepts, and must NOT appear in the grounded default.
    assert "on-device" in draft_default_concepts(TOPIC)
    assert "computer-vision" in draft_default_concepts(TOPIC)
    assert "on-device" not in expected
    assert "computer-vision" not in expected
    assert expected[0] == GROUNDED_CONCEPT
    assert all(expected)

    result = run_wizard(
        GroundedScriptedResponder(_grounded_answers(None, len(expected))),
        tmp_path,
        genesis_timestamp=GENESIS_TS,
        grounded=True,
        recon_engine=engine,
    )
    rc = result["recon_context"]
    assert rc["default_concepts"] == expected

    protocol = json.loads(
        (tmp_path / "workspaces" / result["slug"] / "protocol.json").read_text(encoding="utf-8")
    )
    shipped = protocol["search_strategy"]["core_concepts"]
    assert [c["concept"] for c in shipped] == expected
    for concept in shipped:
        assert concept["concept"] in rc["anchored_terms"]
        assert rc["anchored_terms"][concept["concept"]]
        for syn in concept["synonyms"]:
            assert syn in rc["anchored_terms"]
    shipped_names = [c["concept"] for c in shipped]
    assert "on-device" not in shipped_names
    assert "computer-vision" not in shipped_names


# ---------------------------------------------------------------------------
# M0.3 DoD 3: Step-5 delta-probe enforcement for user-typed terms
# ---------------------------------------------------------------------------


def test_grounded_unanchored_synonym_dropped_with_warning(tmp_path, monkeypatch):
    from scholar_harness import inception as inception_module

    printed = []
    monkeypatch.setattr(
        inception_module.console, "print", lambda *args, **kwargs: printed.append(args)
    )

    mapping = {
        TOPIC.strip().lower(): _fake_docs(3),
        "vineyard blight detection": [
            _doc(
                SYNONYM_A_DOI,
                "Vineyard blight detection at the edge",
                "A study of vineyard blight detection with embedded vision sensors.",
            )
        ],
    }

    def search_fn(query: Query, providers: list[str]):
        return mapping.get(query.text.strip().lower(), [])

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    expected = _pool_anchored_defaults(engine)
    answers = (
        [TOPIC, None]
        + _TAIL_COMMON[:10]
        + ["vineyard blight detection, phantom synonym b"]
        + [""] * (len(expected) - 1)
        + _TAIL_COMMON[10:]
    )
    result = run_wizard(
        GroundedScriptedResponder(answers),
        tmp_path,
        genesis_timestamp=GENESIS_TS,
        grounded=True,
        recon_engine=engine,
    )
    rc = result["recon_context"]

    protocol = json.loads(
        (tmp_path / "workspaces" / result["slug"] / "protocol.json").read_text(encoding="utf-8")
    )
    shipped = protocol["search_strategy"]["core_concepts"]

    # The concept still ships (anchored) with only the evidenced synonym.
    assert shipped[0]["concept"] == GROUNDED_CONCEPT
    assert shipped[0]["synonyms"] == ["vineyard blight detection"]
    # The unanchored synonym is dropped everywhere, including the anchor map.
    for concept in shipped:
        assert "phantom synonym b" not in concept["synonyms"]
    assert "phantom synonym b" not in rc["anchored_terms"]
    # The evidenced synonym entered the session anchor map via its probe.
    assert SYNONYM_A_DOI in rc["anchored_terms"]["vineyard blight detection"]

    # DoD 3: everything that shipped is anchored in the session.
    for concept in shipped:
        assert concept["concept"] in rc["anchored_terms"]
        assert rc["anchored_terms"][concept["concept"]]
        for syn in concept["synonyms"]:
            assert syn in rc["anchored_terms"]

    # The supplementary probes ran within the bound and are recorded.
    assert rc["pool_sizes"] == [3, 1, 0]
    assert len(rc["cache_keys"]) == 3

    # The drop warning was surfaced to the researcher.
    warning_text = " ".join(str(a) for a in printed)
    assert "no literature evidence under probe" in warning_text
    assert "phantom synonym b" in warning_text


def test_grounded_unanchored_concept_exits_without_emitting(tmp_path):
    def search_fn(query: Query, providers: list[str]):
        if query.text.strip().lower() == TOPIC.strip().lower():
            return _fake_docs(3)
        return []

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    expected = _pool_anchored_defaults(engine)
    unanchored_concept = "satellite bioweapon spectral forecast"
    concepts_answer = f"{expected[0]}, {unanchored_concept}"

    with pytest.raises(typer.Exit) as exc:
        run_wizard(
            GroundedScriptedResponder(
                [TOPIC, None]
                + _TAIL_COMMON[:9]
                + [concepts_answer]
                + ["", ""]
                + _TAIL_COMMON[10:]
            ),
            tmp_path,
            genesis_timestamp=GENESIS_TS,
            grounded=True,
            recon_engine=engine,
        )
    assert "literature evidence" in str(exc.value)
    assert "without --grounded" in str(exc.value)
    # Nothing was emitted: no scaffold, no intent, no cache under the root.
    assert not (tmp_path / "workspaces").exists()
    assert not (tmp_path / "intent.json").exists()
    assert not (tmp_path / ".cache").exists()


# ---------------------------------------------------------------------------
# T3.4: exactly ONE delta probe is wired through cache reuse
# ---------------------------------------------------------------------------


def test_grounded_delta_probe_runs_once_and_merges(tmp_path):
    calls = []

    def search_fn(query: Query, providers: list[str]):
        calls.append(query.text)
        return _fake_docs(3)

    engine = ReconEngine(cache_root=tmp_path / "cache", search_fn=search_fn)
    n_concepts = len(_pool_anchored_defaults(engine))
    answers = [TOPIC, "__delta_probe__", GROUNDED_CONCEPT, GROUNDED_CONCEPT] + _wizard_answers(n_concepts)
    result = run_wizard(
        GroundedScriptedResponder(answers),
        tmp_path,
        genesis_timestamp=GENESIS_TS,
        grounded=True,
        recon_engine=engine,
    )

    # Exactly two probes: the topic plus one targeted delta on the direction.
    assert calls == [TOPIC, GROUNDED_CONCEPT]
    rc = result["recon_context"]
    assert len(rc["cache_keys"]) == 2
    assert rc["pool_sizes"] == [3, 3]
    assert len(rc["anchor_dois"]) >= 2
    # The delta reuses the engine cache (pools under the injected root).
    assert len(list((tmp_path / "cache" / "pools").glob("*_pool.json"))) == 2


# ---------------------------------------------------------------------------
# M0.7 (T7.8): headless grounded selection -- no prompt, no block
# ---------------------------------------------------------------------------


def test_inception_help_lists_headless_flags():
    result = CliRunner().invoke(app, ["inception", "--help"])
    assert result.exit_code == 0
    assert "--auto-select" in result.stdout
    assert "--direction-id" in result.stdout


def _grounded_engine(tmp_path) -> ReconEngine:
    return ReconEngine(
        cache_root=tmp_path / "cache", search_fn=lambda q, p: _fake_docs(3)
    )


def _predicted_directions(tmp_path) -> list[dict]:
    from scholar_harness.inception import _grounded_directions_for_terms
    from scholar_harness.recon import distill_pool as distiller_distill

    engine = _grounded_engine(tmp_path)
    pool_path, _n = asyncio.run(engine.probe(TOPIC))
    pool = json.loads(pool_path.read_text(encoding="utf-8"))
    return _grounded_directions_for_terms(distiller_distill(pool))


def test_auto_select_picks_first_direction_without_prompt(tmp_path):
    engine = _grounded_engine(tmp_path)
    n_concepts = len(_pool_anchored_defaults(engine))
    result = run_wizard(
        GroundedScriptedResponder([TOPIC] + _wizard_answers(n_concepts)),
        tmp_path,
        genesis_timestamp=GENESIS_TS,
        grounded=True,
        recon_engine=engine,
        auto_select=True,
    )
    rc = result["recon_context"]
    assert rc["concept"] == GROUNDED_CONCEPT
    assert rc["direction"] == GROUNDED_CONCEPT
    assert len(rc["anchor_dois"]) >= 2


def test_direction_id_selects_nth_direction_without_prompt(tmp_path):
    engine = _grounded_engine(tmp_path)
    directions = _predicted_directions(tmp_path)
    assert len(directions) >= 2
    second = directions[1]["label"]

    n_concepts = len(_pool_anchored_defaults(engine))
    result = run_wizard(
        GroundedScriptedResponder([TOPIC] + _wizard_answers(n_concepts)),
        tmp_path,
        genesis_timestamp=GENESIS_TS,
        grounded=True,
        recon_engine=engine,
        direction_id=2,
    )
    rc = result["recon_context"]
    assert rc["concept"] == second
    assert rc["direction"] == second


def test_direction_id_out_of_range_exits_without_emitting(tmp_path):
    engine = _grounded_engine(tmp_path)
    directions = _predicted_directions(tmp_path)
    with pytest.raises(typer.Exit) as exc:
        run_wizard(
            GroundedScriptedResponder([TOPIC]),
            tmp_path,
            genesis_timestamp=GENESIS_TS,
            grounded=True,
            recon_engine=engine,
            direction_id=len(directions) + 1,
        )
    assert "out of range" in str(exc.value)
    assert "nothing was emitted" in str(exc.value)
    assert not (tmp_path / "workspaces").exists()


def test_direction_id_zero_exits_without_emitting(tmp_path):
    engine = _grounded_engine(tmp_path)
    with pytest.raises(typer.Exit) as exc:
        run_wizard(
            GroundedScriptedResponder([TOPIC]),
            tmp_path,
            genesis_timestamp=GENESIS_TS,
            grounded=True,
            recon_engine=engine,
            direction_id=0,
        )
    assert "out of range" in str(exc.value)
    assert "nothing was emitted" in str(exc.value)
    assert not (tmp_path / "workspaces").exists()