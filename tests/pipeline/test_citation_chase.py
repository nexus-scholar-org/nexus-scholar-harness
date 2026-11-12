"""M3g-citation-chasing: the chase run, offline (fakes; the socket guard is on).

The workspace is the published screening of ``tests/console/test_export_api.py``
(three records, one EXCLUDE, one MAYBE, one INCLUDE), with DOIs on its
``verified.json`` so the includes are chaseable.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
from pathlib import Path

import pytest
from scholar_search.exceptions import ProviderError
from scholar_search.models import Author, Document, ExternalIds

from scholar_harness.pipeline import citation_chase as cc
from scholar_harness.pipeline import discovery as disc

_SPEC = importlib.util.spec_from_file_location(
    "_export_api_helpers", Path(__file__).resolve().parents[1] / "console" / "test_export_api.py"
)
tea = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(tea)

#: Filled by the ``ws`` fixture from the published includes: the INCLUDE seed's
#: OpenAlex work id and DOI, and the DOI of the excluded corpus record.
W_INCLUDE = ""
DOI_INCLUDE = ""
DOI_EXCLUDED = ""
W_EXCLUDED = ""


def _doc(title: str, *, provider: str, pid: str, doi: str | None = None, year: int | None = 2024,
         openalex: str | None = None, s2: str | None = None) -> Document:
    return Document(
        title=title, year=year, provider=provider, provider_id=pid, abstract="an abstract",
        external_ids=ExternalIds(doi=doi, openalex_id=openalex, s2_id=s2),
        authors=[Author(family_name="Author")],
    )


class FakeChaseProvider:
    """Answers ``get_citations`` / ``get_references`` from dicts keyed by the asked id."""

    def __init__(self, name: str, *, citations: dict | None = None, references: dict | None = None,
                 fail: Exception | None = None, resolve: dict[str, str] | None = None,
                 lookup_client: bool = False):
        self.name = name
        self.citations = citations or {}
        self.references = references or {}
        self.fail = fail
        self.asked: list[tuple[str, str]] = []
        self.current_leg = None
        self.closed = False
        if resolve is not None and not lookup_client:
            self._resolve = resolve

            async def resolve_doi(doi: str) -> str | None:
                return resolve.get(doi)
            self.resolve_doi = resolve_doi
        if lookup_client:
            self.base_url = "https://api.openalex.org/works"
            self.client = _LookupClient(resolve or {})

    async def search(self, query):  # pragma: no cover - not asked in a chase
        return
        yield

    async def get_citations(self, document_id: str):
        self.asked.append(("forward", document_id))
        if self.fail is not None:
            raise self.fail
        for doc in self.citations.get(document_id, []):
            yield doc

    async def get_references(self, document_id: str):
        self.asked.append(("backward", document_id))
        if self.fail is not None:
            raise self.fail
        for doc in self.references.get(document_id, []):
            yield doc

    async def close(self):
        self.closed = True


class _Response:
    def __init__(self, body):
        self._body = body

    def json(self):
        return self._body


class _LookupClient:
    def __init__(self, resolve: dict[str, str]):
        self.resolve = resolve
        self.urls: list[str] = []

    async def get(self, url: str, **kw):
        self.urls.append(url)
        doi = url.rsplit("https://doi.org/", 1)[-1]
        if doi in self.resolve:
            return _Response({"id": f"https://openalex.org/{self.resolve[doi]}", "ids": {"openalex": f"https://openalex.org/{self.resolve[doi]}"}})
        raise ProviderError("openalex", "not found", status_code=404)

    async def close(self):
        pass


def build_ws(tmp_path: Path, ids: str = "doi+openalex") -> Path:
    """A published screening whose includes are chaseable (also used by the CLI tests).

    ``ids`` sets the identifiers the records are published with (``doi+openalex``,
    ``doi`` or ``none``), so a test never edits a published output afterwards
    (a changed output makes the generation STALE, which the chase refuses).
    """
    tmp_path.mkdir(parents=True, exist_ok=True)
    workspace = tea.se._build(tmp_path)
    tea.decide(workspace)
    rows = json.loads((workspace / "literature" / "verified.json").read_text(encoding="utf-8"))
    for row in rows:
        i = row["title"].rsplit(" ", 1)[-1]
        eids = {"doi": f"10.1000/ev-{i}", "openalex_id": f"W{i}000"}
        if ids == "doi":
            eids = {"doi": f"10.1000/ev-{i}"}
        elif ids == "none":
            eids = {}
        row.update({"year": 2026, "provider": "crossref", "provider_id": f"ev-{i}",
                    "external_ids": eids, "authors": [{"family_name": "Reviewer"}]})
    (workspace / "literature" / "verified.json").write_text(json.dumps(rows), encoding="utf-8")
    tea.publish(workspace)
    global W_INCLUDE, DOI_INCLUDE, DOI_EXCLUDED, W_EXCLUDED
    included = json.loads((workspace / "literature" / "included.json").read_text(encoding="utf-8"))
    seed = next(r for r in included if r["screening"]["decision"] == "INCLUDE")
    W_INCLUDE, DOI_INCLUDE = seed["external_ids"].get("openalex_id"), seed["external_ids"].get("doi")
    excluded = json.loads((workspace / "literature" / "excluded.json").read_text(encoding="utf-8"))
    DOI_EXCLUDED, W_EXCLUDED = excluded[0]["external_ids"].get("doi"), excluded[0]["external_ids"].get("openalex_id")
    return workspace


@pytest.fixture
def ws(tmp_path: Path) -> Path:
    return build_ws(tmp_path)


def _install(monkeypatch, *providers: FakeChaseProvider) -> None:
    by_name = {p.name: p for p in providers}
    monkeypatch.setattr(disc, "_resolve_providers", lambda names: [by_name[n] for n in names if n in by_name] or None)


def _run(ws: Path, **kw) -> cc.ChaseOutcome:
    return asyncio.run(cc.run_citation_chase(ws, **kw))


def _manifest(ws: Path, name: str) -> dict:
    return json.loads((ws / "literature" / "citation_chase" / name / "chase.json").read_text(encoding="utf-8"))


def _journal(ws: Path, action: str) -> list[dict]:
    rows = [json.loads(line) for line in (ws / "audit" / "journal.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    return [r for r in rows if r.get("action") == action]


# --------------------------------------------------------------------------- seeds


def test_seeds_are_the_published_includes_with_an_identifier(ws):
    seeds = cc.load_seeds(ws)
    assert [s.decision for s in seeds] == ["INCLUDE"]
    assert seeds[0].doi == DOI_INCLUDE and seeds[0].openalex_id == W_INCLUDE and seeds[0].chaseable

    both = cc.load_seeds(ws, seed_source="included+unclear")
    assert sorted(s.decision for s in both) == ["INCLUDE", "MAYBE"]

    rows = json.loads((ws / "literature" / "included.json").read_text(encoding="utf-8"))
    for row in rows:
        row["external_ids"] = {}
    (ws / "literature" / "included.json").write_text(json.dumps(rows), encoding="utf-8")
    bare = cc.load_seeds(ws)
    assert bare and not bare[0].chaseable and "no DOI" in bare[0].reason


def test_without_a_published_screening_the_chase_refuses(ws):
    (ws / "literature" / "included.json").unlink()
    with pytest.raises(cc.ChaseRefused) as exc:
        cc.load_seeds(ws)
    assert exc.value.code == "SCREENING_NOT_PUBLISHED"
    assert not (ws / "literature" / "citation_chase").exists()


# --------------------------------------------------------------------------- the run


def test_a_chase_asks_openalex_then_s2_in_both_directions_and_keeps_only_what_is_new(ws, monkeypatch):
    found_twice_oa = _doc("Found twice", provider="openalex", pid="W10", doi="10.2/twice", openalex="W10")
    found_twice_s2 = _doc("Found twice", provider="semanticscholar", pid="s2-10", doi="10.2/twice", s2="s2-10")
    in_corpus = _doc("Event record 0", provider="openalex", pid=W_EXCLUDED, doi=DOI_EXCLUDED, openalex=W_EXCLUDED, year=2026)
    too_old = _doc("Old reference", provider="openalex", pid="W11", doi="10.2/old", openalex="W11", year=2012)
    new_ref = _doc("A new reference", provider="openalex", pid="W12", doi="10.2/ref", openalex="W12", year=2021)
    s2_only = _doc("Only S2 knows", provider="semanticscholar", pid="s2-13", doi="10.2/s2", s2="s2-13", year=2025)
    undated = _doc("No year", provider="semanticscholar", pid="s2-14", doi="10.2/nodate", s2="s2-14", year=None)
    openalex = FakeChaseProvider(
        "openalex",
        citations={W_INCLUDE: [found_twice_oa, in_corpus]},
        references={W_INCLUDE: [too_old, new_ref]},
    )
    s2 = FakeChaseProvider(
        "semanticscholar",
        citations={f"DOI:{DOI_INCLUDE}": [found_twice_s2, s2_only]},
        references={f"DOI:{DOI_INCLUDE}": [undated]},
    )
    _install(monkeypatch, openalex, s2)

    outcome = _run(ws, note="first chase")

    assert outcome.status == "SUCCESS" and outcome.published and not outcome.cancelled
    # OpenAlex first, both directions, then Semantic Scholar; the seed asked by its own id.
    assert openalex.asked == [("forward", W_INCLUDE), ("backward", W_INCLUDE)]
    assert s2.asked == [("forward", f"DOI:{DOI_INCLUDE}"), ("backward", f"DOI:{DOI_INCLUDE}")]
    assert [(leg.provider, leg.direction, leg.fetched, leg.status) for leg in outcome.legs] == [
        ("openalex", "forward", 2, "ok"), ("openalex", "backward", 2, "ok"),
        ("semanticscholar", "forward", 2, "ok"), ("semanticscholar", "backward", 1, "ok"),
    ]
    counts = outcome.counts
    assert counts.raw == 7
    assert counts.duplicates_within_chase == 1  # "Found twice" from both databases
    assert counts.already_in_corpus == 1  # Event record 0 is in the frozen corpus
    assert counts.outside_year_window == 1  # 2012 is before the protocol's 2020
    assert counts.new == 4  # twice (merged), new_ref, s2_only, undated (a missing year is screened)

    run_dir = ws / "literature" / "citation_chase" / "chase_001"
    new = json.loads((run_dir / "new.json").read_text(encoding="utf-8"))
    assert [r["title"] for r in new] == ["Found twice", "A new reference", "Only S2 knows", "No year"]
    twice = new[0]
    assert twice["sources"] == [
        {"provider": "openalex", "id": "W10", "via": "citation-chase", "seed": outcome.seeds[0].study_id, "direction": "forward"},
        {"provider": "semanticscholar", "id": "s2-10", "via": "citation-chase", "seed": outcome.seeds[0].study_id, "direction": "forward"},
    ]
    assert all(r["workspace_id"] is None for r in new)  # no id is minted here; the accept does
    raw = json.loads((run_dir / "raw.json").read_text(encoding="utf-8"))
    assert len(raw) == 7
    edges = json.loads((run_dir / "edges.json").read_text(encoding="utf-8"))
    assert len(edges) == 7 and {e["direction"] for e in edges} == {"forward", "backward"}
    assert any(e["record"] == f"doi:{DOI_EXCLUDED}" for e in edges)  # provenance kept for a corpus record too

    manifest = _manifest(ws, "chase_001")
    assert manifest["schema"] == "nexus.citation-chase.v1"
    assert manifest["status"] == "SUCCESS" and manifest["published"] is True and manifest["accepted"] is None
    assert manifest["providers"] == ["openalex", "semanticscholar"] and manifest["directions"] == ["forward", "backward"]
    assert manifest["forward_cap"] == 500 and manifest["run_ceiling"] == 5000
    assert (manifest["year_min"], manifest["year_max"]) == (2020, 2026)
    assert manifest["notes"] == ["first chase"]
    assert manifest["generation_id"].startswith("GEN-")
    assert manifest["parent_corpus"]["artifact_id"].startswith("ART-corpus-") and manifest["parent_corpus"]["sha256"]
    assert manifest["already_in_corpus"][0]["study_id"].startswith("STU-")
    assert manifest["counts"] == {
        "raw": 7, "duplicates_within_chase": 1, "already_in_corpus": 1,
        "outside_year_window": 1, "over_ceiling": 0, "new": 4,
    }
    assert len(manifest["seeds"]) == 1 and manifest["seeds"][0]["chaseable"]

    (event,) = _journal(ws, "CITATION_CHASE")
    assert event["status"] == "SUCCESS"
    assert event["parameters"]["method"] == "EXTERNAL_PROVIDER" and event["parameters"]["chase"] == "chase_001"
    assert event["metrics"]["new"] == 4 and event["metrics"]["legs"] == 4


def test_the_raw_list_depends_on_the_inputs_not_on_arrival(ws, monkeypatch):
    a = _doc("Alpha", provider="openalex", pid="W1", doi="10.2/a", openalex="W1")
    b = _doc("Beta", provider="openalex", pid="W2", doi="10.2/b", openalex="W2")
    _install(monkeypatch, FakeChaseProvider("openalex", citations={W_INCLUDE: [a, b]}))
    first = _run(ws, providers=["openalex"], directions=["forward"])
    _install(monkeypatch, FakeChaseProvider("openalex", citations={W_INCLUDE: [b, a]}))
    second = _run(ws, providers=["openalex"], directions=["forward"])
    def read(name: str) -> list[str]:
        path = ws / "literature" / "citation_chase" / name / "new.json"
        return [r["title"] for r in json.loads(path.read_text(encoding="utf-8"))]

    assert first.counts.new == second.counts.new == 2
    assert read("chase_001") == ["Alpha", "Beta"]  # new.json follows the raw order
    assert read("chase_002") == ["Beta", "Alpha"]  # the raw order follows the database's answer


def test_a_forward_cap_stops_the_leg_and_says_the_count_is_a_lower_bound(ws, monkeypatch):
    citing = [_doc(f"Citing {i}", provider="openalex", pid=f"W{i}", doi=f"10.2/c{i}", openalex=f"W{i}") for i in range(7)]
    refs = [_doc(f"Ref {i}", provider="openalex", pid=f"W{100 + i}", doi=f"10.2/r{i}", openalex=f"W{100 + i}") for i in range(7)]
    _install(monkeypatch, FakeChaseProvider("openalex", citations={W_INCLUDE: citing}, references={W_INCLUDE: refs}))

    outcome = _run(ws, providers=["openalex"], forward_cap=5)

    forward, backward = outcome.legs
    assert (forward.fetched, forward.cap, forward.cap_hit) == (5, 5, True)
    assert "lower bound" in forward.notes[0]
    assert (backward.fetched, backward.cap, backward.cap_hit) == (7, None, False)  # references are never capped
    assert outcome.status == "SUCCESS" and outcome.counts.new == 12


def test_one_failing_database_is_partial_and_every_database_failing_publishes_nothing(ws, monkeypatch):
    doc = _doc("Cited", provider="openalex", pid="W1", doi="10.2/a", openalex="W1")
    throttled = ProviderError("semanticscholar", "slow down", status_code=429)
    _install(monkeypatch, FakeChaseProvider("openalex", citations={W_INCLUDE: [doc]}),
             FakeChaseProvider("semanticscholar", fail=throttled))
    partial = _run(ws)
    assert partial.status == "PARTIAL" and partial.published
    failed = [leg for leg in partial.legs if leg.status == "failed"]
    assert len(failed) == 2 and all(leg.error_code == "PROVIDER_RATE_LIMITED" for leg in failed)
    assert all(leg.provider == "semanticscholar" for leg in failed)
    assert (ws / "literature" / "citation_chase" / "chase_001" / "new.json").is_file()
    assert _manifest(ws, "chase_001")["reason"] == "2 of 4 legs failed"

    refused = ProviderError("openalex", "key", status_code=403)
    _install(monkeypatch, FakeChaseProvider("openalex", fail=refused), FakeChaseProvider("semanticscholar", fail=throttled))
    failed_run = _run(ws)
    assert failed_run.status == "FAILED" and not failed_run.published
    run_dir = ws / "literature" / "citation_chase" / "chase_002"
    assert not (run_dir / "new.json").exists()
    assert (run_dir / "chase.json").is_file() and (run_dir / "raw.json").is_file()  # the legs are evidence
    assert [leg.error_code for leg in failed_run.legs if leg.provider == "openalex"] == ["PROVIDER_REFUSED"] * 2
    (_, event) = _journal(ws, "CITATION_CHASE")
    assert event["status"] == "FAILED" and event["parameters"]["published"] is False


def test_a_cancel_keeps_the_fetched_records_but_publishes_nothing(ws, monkeypatch):
    doc = _doc("Cited", provider="openalex", pid="W1", doi="10.2/a", openalex="W1")
    _install(monkeypatch, FakeChaseProvider("openalex", citations={W_INCLUDE: [doc]}),
             FakeChaseProvider("semanticscholar", citations={f"DOI:{DOI_INCLUDE}": [doc]}))
    calls = {"n": 0}

    def should_stop() -> bool:
        calls["n"] += 1
        return calls["n"] > 1  # stop before the second database

    outcome = _run(ws, should_stop=should_stop)
    assert outcome.cancelled and outcome.status == "PARTIAL" and not outcome.published
    assert "cancelled by the researcher" in outcome.notes
    run_dir = ws / "literature" / "citation_chase" / "chase_001"
    assert len(json.loads((run_dir / "raw.json").read_text(encoding="utf-8"))) == 1  # OpenAlex ran, S2 never did
    assert not (run_dir / "new.json").exists()
    assert [(leg.provider, leg.status) for leg in outcome.legs] == [("openalex", "ok"), ("openalex", "ok")]


def test_a_doi_only_seed_is_looked_up_once_on_openalex_and_a_miss_skips_its_legs(tmp_path, monkeypatch):
    ws = build_ws(tmp_path / "doi-only", ids="doi")
    doc = _doc("Cited", provider="openalex", pid="W1", doi="10.2/a", openalex="W1")
    openalex = FakeChaseProvider("openalex", citations={"W777": [doc]}, resolve={DOI_INCLUDE: "W777"}, lookup_client=True)
    _install(monkeypatch, openalex)
    outcome = _run(ws, providers=["openalex"])
    assert openalex.client.urls == [f"https://api.openalex.org/works/https://doi.org/{DOI_INCLUDE}"]  # one lookup, both directions
    assert openalex.asked == [("forward", "W777"), ("backward", "W777")]
    assert outcome.counts.new == 1
    assert _manifest(ws, "chase_001")["seeds"][0]["openalex_id"] == "W777"

    missing = FakeChaseProvider("openalex", resolve={}, lookup_client=True)
    _install(monkeypatch, missing)
    skipped = _run(ws, providers=["openalex"])
    assert skipped.status == "EMPTY_RESULT"
    assert [leg.status for leg in skipped.legs] == ["skipped", "skipped"]
    assert "not found on OpenAlex" in skipped.legs[0].notes[0]
    assert missing.asked == []


def test_nothing_new_is_an_empty_result_and_a_seed_without_an_id_is_reported(ws, tmp_path, monkeypatch):
    in_corpus = _doc("Event record 0", provider="openalex", pid=W_EXCLUDED, doi=DOI_EXCLUDED, openalex=W_EXCLUDED, year=2026)
    _install(monkeypatch, FakeChaseProvider("openalex", citations={W_INCLUDE: [in_corpus]}))
    outcome = _run(ws, providers=["openalex"])
    assert outcome.status == "EMPTY_RESULT" and outcome.published
    assert outcome.counts.already_in_corpus == 1 and outcome.counts.new == 0
    assert json.loads((ws / "literature" / "citation_chase" / "chase_001" / "new.json").read_text(encoding="utf-8")) == []

    bare_ws = build_ws(tmp_path / "bare", ids="none")
    bare = _run(bare_ws, providers=["openalex"])
    assert bare.status == "EMPTY_RESULT" and "no chaseable seed" in bare.reason and bare.legs == []
    assert _manifest(bare_ws, "chase_001")["seeds"][0]["chaseable"] is False


def test_the_run_ceiling_keeps_the_first_records_and_marks_the_run_partial(ws, monkeypatch):
    citing = [_doc(f"Citing {i}", provider="openalex", pid=f"W{i}", doi=f"10.2/c{i}", openalex=f"W{i}") for i in range(6)]
    _install(monkeypatch, FakeChaseProvider("openalex", citations={W_INCLUDE: citing}))
    outcome = _run(ws, providers=["openalex"], directions=["forward"], run_ceiling=4)
    assert outcome.status == "PARTIAL" and outcome.published
    assert outcome.counts.new == 4 and outcome.counts.over_ceiling == 2
    assert outcome.notes == ["run ceiling of 4 new records reached: 2 not kept"]
    new = json.loads((ws / "literature" / "citation_chase" / "chase_001" / "new.json").read_text(encoding="utf-8"))
    assert [r["title"] for r in new] == ["Citing 0", "Citing 1", "Citing 2", "Citing 3"]


def test_invalid_options_refuse_before_anything_is_written(ws, monkeypatch):
    _install(monkeypatch, FakeChaseProvider("openalex"))
    with pytest.raises(cc.ChaseRefused) as exc:
        _run(ws, directions=["sideways"])
    assert exc.value.code == "CHASE_DIRECTION_INVALID"
    with pytest.raises(cc.ChaseRefused) as exc:
        _run(ws, seed_source="everything")
    assert exc.value.code == "CHASE_SEEDS_INVALID"
    with pytest.raises(cc.ChaseRefused) as exc:
        _run(ws, providers=["nowhere"])
    assert exc.value.code == "PROVIDER_UNKNOWN"
    assert not (ws / "literature" / "citation_chase").exists()
    assert _journal(ws, "CITATION_CHASE") == []


def test_chase_summaries_list_the_runs_newest_first(ws, monkeypatch):
    doc = _doc("Cited", provider="openalex", pid="W1", doi="10.2/a", openalex="W1")
    _install(monkeypatch, FakeChaseProvider("openalex", citations={W_INCLUDE: [doc]}))
    _run(ws, providers=["openalex"])
    _run(ws, providers=["openalex"])
    summaries = cc.chase_summaries(ws)
    assert [s["chase"] for s in summaries] == ["chase_002", "chase_001"]
    assert summaries[0]["counts"]["new"] == 1 and summaries[0]["published"] and summaries[0]["accepted"] is None
    assert summaries[0]["chaseable_seeds"] == 1 and summaries[0]["providers"] == ["openalex"]
