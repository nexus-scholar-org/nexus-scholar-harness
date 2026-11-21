"""M8b-triage-highlights: the two read fields behind the Triage marks.

``search_terms`` on ``GET /records/{study_id}`` (the protocol's concepts, their
mentions and where their words occur) and ``quotes`` on ``GET
/records/{study_id}/proposal`` (where each quote of the draft shows, or that it
is not at its offsets). Decisions 2026-11-21, M8b items 12 and 13.
"""

from __future__ import annotations

import json
from pathlib import Path

import test_screening_api_v1 as api
from fastapi.testclient import TestClient
from test_screening_api_v1 import BASE, DESKTOP, PHONE, PROMPT, _event, _post, _studies

from scholar_harness.console import create_app
from scholar_harness.screening import proposals as pr

CONCEPTS = [
    {"concept": "UAV", "synonyms": ["drone"], "boolean_operator": "OR"},
    {"concept": "weed mapping", "synonyms": ["weed map"], "boolean_operator": "OR"},
    {"concept": "rice", "synonyms": [], "boolean_operator": "OR"},
]


def _ws(tmp_path: Path, monkeypatch, *, blinding: str | None = None) -> Path:
    protocol = json.loads(api.PROTOCOL.read_text(encoding="utf-8"))
    protocol["search_strategy"]["core_concepts"] = CONCEPTS
    if blinding:
        protocol["method"] = {
            "dedup": {"doi": True, "title_similarity": 0.97, "first_author": True, "year_tolerance": 1},
            "rules_version": "screening-rules-v1",
            "not_reported": "unclear",
            "blinding": blinding,
        }
    path = tmp_path / "protocol_concepts.json"
    path.write_text(json.dumps(protocol), encoding="utf-8")
    monkeypatch.setattr(api, "PROTOCOL", path)
    root = tmp_path / "root"
    root.mkdir()
    return api._workspace(root)


def _client(ws: Path) -> TestClient:
    return TestClient(
        create_app(ws, token=DESKTOP, phone_tokens={PHONE}),
        base_url="http://127.0.0.1",
        headers={"Authorization": f"Bearer {DESKTOP}"},
    )


def _paper(ws: Path, study: str) -> dict:
    for path in sorted((ws / "literature" / "screening").glob("batch_*.json")):
        for paper in json.loads(path.read_text(encoding="utf-8")).get("papers", []):
            if paper["workspace_id"] == study:
                return paper
    raise AssertionError(study)


def _set_paper(ws: Path, study: str, **fields) -> None:
    for path in sorted((ws / "literature" / "screening").glob("batch_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for paper in data.get("papers", []):
            if paper["workspace_id"] == study:
                paper.update(fields)
                path.write_text(json.dumps(data), encoding="utf-8")
                return
    raise AssertionError(study)


def _study(client: TestClient, ws: Path) -> str:
    """A record with an abstract (the API fixture's record 2 is title only)."""
    return next(s for s in _studies(client) if "about UAV" in str(_paper(ws, s).get("abstract")))


def _propose(client: TestClient, ws: Path, study: str, criteria: list[dict]) -> None:
    paper = _paper(ws, study)
    year = str(paper["year"]) if paper.get("year") else None
    abstract = str(paper.get("abstract") or "").strip() or None
    pr.submit_proposal(
        ws, study_id=study, title=paper.get("title"), abstract=abstract, published=year,
        output={"criteria": criteria, "cannot_decide": False},
        protocol=json.loads((ws / "protocol.json").read_text(encoding="utf-8")),
        protocol_fingerprint=client.get(f"{BASE}/records/{study}").json()["binding"]["protocol_fingerprint"],
        provenance={"task_version": "screen-v1", "model": "claude-opus-5-5", "prompt_sha256": PROMPT},
        created_at="2026-11-21T09:00:00Z",
    )


def _answer(cid: str, answer: str, text: str, quote: str, *, shift: int = 0) -> dict:
    start = text.index(quote) + shift
    return {"id": cid, "answer": answer, "evidence": {"text": quote, "start": start, "end": start + len(quote)}}


# --- search_terms on the record read ------------------------------------------------


def test_the_record_read_carries_the_concepts_their_mentions_and_marks(tmp_path, monkeypatch):
    ws = _ws(tmp_path, monkeypatch)
    client = _client(ws)
    study = _study(client, ws)
    record = client.get(f"{BASE}/records/{study}").json()
    terms = record["search_terms"]
    assert [(c["concept"], c["terms"], c["mentions"]) for c in terms["concepts"]] == [
        ("UAV", ["UAV", "drone"], 1),
        ("weed mapping", ["weed mapping", "weed map"], 1),
        ("rice", ["rice"], 0),  # absent: the legend says so
    ]
    abstract = record["abstract"]
    assert [(m["field"], abstract[m["start"] : m["end"]], m["concept"]) for m in terms["marks"]] == [
        ("abstract", "UAV", 0),
        ("abstract", "weed mapping", 1),
    ]
    # The criterion highlights are a different thing and stay empty.
    assert record["highlights"] == []


def test_title_marks_use_utf16_offsets_and_a_title_only_record_marks_its_title(tmp_path, monkeypatch):
    ws = _ws(tmp_path, monkeypatch)
    client = _client(ws)
    study = _studies(client)[0]
    title = "\U0001f681 Drones over rice"  # a helicopter emoji: two UTF-16 code units
    _set_paper(ws, study, title=title, abstract="No abstract available.")
    record = client.get(f"{BASE}/records/{study}").json()
    assert record["abstract"] is None
    marks = record["search_terms"]["marks"]
    assert [(m["field"], m["start"], m["end"], m["concept"]) for m in marks] == [
        ("title", 3, 9, 0),  # "Drones" starts at code point 2, UTF-16 unit 3
        ("title", 15, 19, 2),
    ]
    assert [c["mentions"] for c in record["search_terms"]["concepts"]] == [1, 0, 1]


def test_a_protocol_without_concepts_gives_an_empty_list(tmp_path, monkeypatch):
    ws = _ws(tmp_path, monkeypatch)
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    client = _client(ws)
    study = _studies(client)[0]
    before = client.get(f"{BASE}/records/{study}").json()["search_terms"]
    assert before["concepts"]
    protocol["search_strategy"]["core_concepts"] = [{"concept": "  ", "synonyms": []}]
    from scholar_harness.screening.highlights import search_terms

    assert search_terms(protocol, "a UAV", "drones") == {"concepts": [], "marks": []}


# --- quotes on the draft read -------------------------------------------------------


def test_quotes_are_hidden_with_the_draft_until_the_decision(tmp_path, monkeypatch):
    ws = _ws(tmp_path, monkeypatch)
    client = _client(ws)
    study = _study(client, ws)
    paper = _paper(ws, study)
    _propose(client, ws, study, [_answer("INC-01", "yes", f"{paper['title']}\n\n{paper['abstract']}", "UAV weed")])
    hidden = client.get(f"{BASE}/records/{study}/proposal")
    assert hidden.status_code == 403
    assert hidden.json()["detail"]["code"] == "PROPOSAL_HIDDEN"
    assert "quotes" not in json.dumps(hidden.json())
    _post(client, [_event(client, study)])
    shown = client.get(f"{BASE}/records/{study}/proposal").json()["proposal"]
    assert shown["quotes"][0]["criterion_id"] == "INC-01"


def test_quotes_found_in_the_title_and_the_abstract_get_their_places(tmp_path, monkeypatch):
    ws = _ws(tmp_path, monkeypatch, blinding="show")
    client = _client(ws)
    study = _studies(client)[0]
    _set_paper(ws, study, abstract="  Abstract about UAV weed mapping in rice.\n")
    paper = _paper(ws, study)
    text = pr.record_text(paper["title"], paper["abstract"].strip(), str(paper["year"]) if paper.get("year") else None)
    _propose(client, ws, study, [
        _answer("INC-01", "yes", text, "record"),
        _answer("EXC-01", "no", text, "UAV weed mapping"),
    ])
    record = client.get(f"{BASE}/records/{study}").json()
    quotes = client.get(f"{BASE}/records/{study}/proposal").json()["proposal"]["quotes"]
    by_id = {q["criterion_id"]: q for q in quotes}
    title_q, abstract_q = by_id["INC-01"], by_id["EXC-01"]
    assert (title_q["found"], title_q["field"], title_q["answer"]) == (True, "title", "yes")
    assert record["title"][title_q["start"] : title_q["end"]] == "record"
    assert (abstract_q["found"], abstract_q["field"]) == (True, "abstract")
    # The served abstract keeps its leading spaces: the place counts them.
    assert record["abstract"][abstract_q["start"] : abstract_q["end"]] == "UAV weed mapping"


def test_a_quote_not_at_its_offsets_is_not_found_and_gets_no_place(tmp_path, monkeypatch):
    ws = _ws(tmp_path, monkeypatch, blinding="show")
    client = _client(ws)
    study = _study(client, ws)
    paper = _paper(ws, study)
    text = pr.record_text(paper["title"], paper["abstract"], str(paper["year"]) if paper.get("year") else None)
    _propose(client, ws, study, [
        _answer("INC-01", "yes", text, "UAV weed", shift=2),
        {"id": "EXC-01", "answer": "not_reported", "evidence": None},
    ])
    proposal = client.get(f"{BASE}/records/{study}/proposal").json()["proposal"]
    assert [v for v in proposal["validators"] if v["name"] == "quote_in_source"][0]["ok"] is False
    # The not-reported answer quotes nothing, so it has no entry.
    assert proposal["quotes"] == [
        {"criterion_id": "INC-01", "answer": "yes", "found": False, "field": None, "start": None, "end": None}
    ]


def test_a_quote_in_the_year_line_or_across_the_fields_is_found_without_a_place(tmp_path, monkeypatch):
    ws = _ws(tmp_path, monkeypatch, blinding="show")
    client = _client(ws)
    study = _study(client, ws)
    _set_paper(ws, study, year=2024)
    paper = _paper(ws, study)
    text = pr.record_text(paper["title"], paper["abstract"], str(paper["year"]))
    across = paper["title"][-3:] + "\n\n" + paper["abstract"][:5]
    _propose(client, ws, study, [
        _answer("INC-01", "yes", text, f"Published: {paper['year']}"),
        _answer("EXC-01", "no", text, across),
    ])
    quotes = client.get(f"{BASE}/records/{study}/proposal").json()["proposal"]["quotes"]
    assert [(q["found"], q["field"], q["start"]) for q in quotes] == [(True, None, None), (True, None, None)]


def test_the_phone_token_reads_the_same_fields(tmp_path, monkeypatch):
    ws = _ws(tmp_path, monkeypatch)
    phone = TestClient(
        create_app(ws, token=DESKTOP, phone_tokens={PHONE}),
        base_url="http://127.0.0.1",
        headers={"Authorization": f"Bearer {PHONE}"},
    )
    study = _studies(_client(ws))[0]
    assert "search_terms" in phone.get(f"{BASE}/records/{study}").json()
