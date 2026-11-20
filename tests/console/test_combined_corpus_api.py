"""M3f-combined-corpus: a harvest and staged database exports make one corpus, deduplicated together.

Offline, as ``test_discovery_api.py`` (whose doubles and helpers this file
loads): the databases are in-memory doubles run by the real engine, and the
abstract and verification clients are replaced. Nothing reaches the network.

Found by the acceptance run of 2026-11-20 (findings 26, 27): a corpus was
either a harvest or imported files, and the Hand-off counted no abstracts for
imported files.
"""

from __future__ import annotations

import base64
import importlib.util
import json
from pathlib import Path

from scholar_harness.pipeline import verification as ver_mod

_SPEC = importlib.util.spec_from_file_location(
    "_discovery_api_helpers_m3f", Path(__file__).resolve().parent / "test_discovery_api.py"
)
h = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(h)

env = h.env
BASE = h.BASE
CORPUS = "/api/v1/screening/corpus"
ACCEPT = "/api/v1/screening/corpus/accept"

# Scopus #1 has the DOI of the harvest's openalex record 0 (a duplicate across the two parts);
# Scopus #2 is new; Scopus #3 is new and has no abstract.
SCOPUS = (
    "TY  - JOUR\nAU  - Rossi, M.\nTI  - UAV weed mapping study openalex 0\nPY  - 2023\nDO  - 10.1/openalex.0\n"
    "AB  - Scopus abstract one.\nER  - \n"
    "TY  - JOUR\nAU  - Chen, L.\nTI  - Drone crop scouting with deep learning\nPY  - 2022\nDO  - 10.1000/m3f-2\n"
    "AB  - Scopus abstract two.\nER  - \n"
    "TY  - JOUR\nAU  - Diaz, A.\nTI  - Hyperspectral weed discrimination\nPY  - 2021\nER  - \n"
)
IEEE = "TY  - JOUR\nAU  - Okafor, N.\nTI  - Site-specific herbicide prescription maps\nPY  - 2023\nDO  - 10.1000/m3f-4\nAB  - IEEE one.\nER  - \n"


def _stage(client, label: str, text: str, name: str, **extra):
    return client.post(f"{CORPUS}/sources", json={
        "label": label, "file_name": name, "content_base64": base64.b64encode(text.encode()).decode("ascii"), **extra,
    })


def _harvest(client, providers=("openalex",)) -> dict:
    job, _ = h._run(client, {"providers": list(providers)})
    assert job["state"] == "succeeded", job
    return job


def _snapshot(ws: Path) -> dict:
    registry = json.loads((ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8"))["artifacts"]
    (entry,) = [e for e in registry.values() if e["artifact_type"] == "corpus_snapshot"]
    return json.loads((ws / entry["path"]).read_text(encoding="utf-8"))


def _verified(ws: Path) -> list[dict]:
    return json.loads((ws / "literature" / "verified.json").read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- order (D1)


def test_an_export_staged_after_a_harvest_is_combined_at_the_accept(env):
    """Finding 26: staging after a harvest was refused (VERIFIED_EXISTS); now both parts make one corpus."""
    client, ws, _ = env
    _harvest(client)  # four openalex records, 10.1/openalex.0 to .3
    harvest_rows = _verified(ws)
    assert len(harvest_rows) == 4

    staged = _stage(client, "Scopus", SCOPUS, "scopus.ris", searched_on="2026-11-20", query="uav AND weed")
    assert staged.status_code == 201, staged.text
    corpus = staged.json()
    assert corpus["staging_refused"] is None
    assert corpus["origin"] == "combined" and corpus["state"] == "STAGED"
    assert corpus["harvest"] == {"run": "run_001", "state": "ready", "included": True}
    # 4 harvested + 3 imported records; Scopus #1 is the harvest's record 0.
    assert corpus["preview"] == {"identified": 7, "duplicates": 1, "unique_studies": 6}
    # Nothing is written over before the accept.
    assert _verified(ws) == harvest_rows

    accepted = client.post(ACCEPT)
    assert accepted.status_code == 200, accepted.text
    after = accepted.json()
    assert after["state"] == "ACCEPTED" and after["accepted"]["studies"] == 6 and after["accepted"]["records"] == 7
    data = _snapshot(ws)["data"]
    assert len(data["studies"]) == 6 and len(data["record_to_study"]) == 7
    merged = [s for s in data["studies"] if len(s["source_record_ids"]) == 2]
    assert len(merged) == 1 and merged[0]["external_ids"]["doi"] == ["10.1/openalex.0"]
    # The combined rows: the harvest's rows unchanged, then the export's records, each saying where it came from.
    rows = _verified(ws)
    assert rows[:4] == harvest_rows
    assert [r.get("source_database") for r in rows[4:]] == ["Scopus"] * 3
    # The harvest's own file is kept in its run folder; the manifest names both parts.
    run_copy = ws / "literature" / "search_runs" / "run_001" / "verified.json"
    assert json.loads(run_copy.read_text(encoding="utf-8")) == harvest_rows
    manifest = json.loads((ws / "literature" / "raw" / "provenance_manifest.json").read_text(encoding="utf-8"))
    assert manifest["schema"] == "nexus.corpus-combined.v1"
    assert manifest["harvest"]["run"] == "run_001" and manifest["harvest"]["identified"] == 4
    assert manifest["total_raw_harvested"] == 7
    assert [d["label"] for d in manifest["databases"]] == ["Scopus"]
    event = next(e for e in h._journal(ws) if e["action"] == "CORPUS_SNAPSHOT_ACCEPTED")
    assert event["parameters"]["run"] == "run_001"


def test_a_harvest_after_staging_is_combined_and_both_can_be_repeated(env):
    """A run while exports are staged was refused (STAGED_IMPORT_PENDING); the order no longer matters."""
    client, ws, _ = env
    assert _stage(client, "Scopus", SCOPUS, "scopus.ris").status_code == 201
    first = client.post(f"{BASE}/runs", json={"providers": ["openalex"]})
    assert first.status_code == 202, first.text
    h._events(client, first.json()["job"]["job_id"])
    _harvest(client)  # a second harvest replaces the first as the harvest part
    assert _stage(client, "IEEE Xplore", IEEE, "ieee.ris").status_code == 201
    corpus = client.get(CORPUS).json()
    assert corpus["harvest"]["run"] == "run_002"
    assert corpus["preview"] == {"identified": 8, "duplicates": 1, "unique_studies": 7}
    assert client.post(ACCEPT).status_code == 200
    assert len(_snapshot(ws)["data"]["studies"]) == 7


def test_records_of_unknown_origin_still_refuse_an_export(env):
    """VERIFIED_EXISTS is kept for a verified.json that no search run and no import of this app made."""
    client, ws, _ = env
    (ws / "literature").mkdir(exist_ok=True)
    (ws / "literature" / "verified.json").write_text(json.dumps([{"title": "x", "provider": "openalex"}]), encoding="utf-8")
    refused = _stage(client, "Scopus", SCOPUS, "scopus.ris")
    assert refused.status_code == 409 and h._code(refused) == "VERIFIED_EXISTS"


# --------------------------------------------------------------------------- an unfinished harvest (D3)


class _VerifierDown(h._PassthroughVerifier):
    async def process_batch(self, docs, verify=True, enrich=True):
        raise RuntimeError("verifier down")


def test_an_unfinished_harvest_beside_exports_is_left_out_and_said_so(env, monkeypatch):
    """M3i item 10 kept: with exports staged, the accept takes the exports alone; the views say so first."""
    client, ws, _ = env
    monkeypatch.setattr(ver_mod, "DocumentVerifier", _VerifierDown)
    job, _ = h._run(client, {"providers": ["openalex"]})
    assert job["state"] == "failed", job
    assert _stage(client, "Scopus", SCOPUS, "scopus.ris").status_code == 201
    corpus = client.get(CORPUS).json()
    assert corpus["origin"] == "imports"
    assert corpus["harvest"] == {"run": "run_001", "state": "failed", "included": False}
    handoff = client.get(f"{BASE}/handoff").json()
    assert handoff["corpus"]["harvest"]["included"] is False
    assert client.post(ACCEPT).status_code == 200
    assert len(_snapshot(ws)["data"]["record_to_study"]) == 3


def test_an_unfinished_harvest_alone_is_still_refused(env, monkeypatch):
    client, ws, _ = env
    monkeypatch.setattr(ver_mod, "DocumentVerifier", _VerifierDown)
    job, _ = h._run(client, {"providers": ["openalex"]})
    assert job["state"] == "failed", job
    refused = client.post(ACCEPT)
    assert refused.status_code == 409 and h._code(refused) == "PREPARATION_UNFINISHED"


def test_a_changed_protocol_refuses_the_combined_accept(env):
    client, ws, _ = env
    _harvest(client)
    assert _stage(client, "Scopus", SCOPUS, "scopus.ris").status_code == 201
    protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
    protocol["search_strategy"]["date_range"]["start_year"] = 2015
    (ws / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    refused = client.post(ACCEPT)
    assert refused.status_code == 409 and h._code(refused) == "PROTOCOL_CHANGED_SINCE_RUN"
    assert not (ws / "audit" / "artifact_registry.json").is_file() or "corpus_snapshot" not in (
        ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8")


# --------------------------------------------------------------------------- the Hand-off (D4, finding 27)


def test_the_handoff_counts_abstracts_of_staged_exports_per_work(env):
    """Finding 27: before the accept, imported files showed 0 with an abstract and 0 title only."""
    client, ws, _ = env
    assert _stage(client, "Scopus", SCOPUS, "scopus.ris").status_code == 201
    assert _stage(client, "IEEE Xplore", IEEE, "ieee.ris").status_code == 201
    handoff = client.get(f"{BASE}/handoff").json()
    assert handoff["abstracts"] == {"with_abstract": 3, "title_only": 1, "share_with_abstract": 0.75}
    mix = {m["provider"]: m for m in handoff["provider_mix"]}
    assert mix["Scopus"] == {"provider": "Scopus", "kind": "import", "records": 3, "share": 0.75}
    assert mix["IEEE Xplore"]["records"] == 1 and "ris" not in mix
    # After the accept the counts are the same.
    assert client.post(ACCEPT).status_code == 200
    assert client.get(f"{BASE}/handoff").json()["abstracts"] == handoff["abstracts"]


def test_the_handoff_shows_the_combined_corpus(env):
    client, ws, _ = env
    _harvest(client)
    assert _stage(client, "Scopus", SCOPUS, "scopus.ris").status_code == 201
    handoff = client.get(f"{BASE}/handoff").json()
    assert handoff["corpus"]["origin"] == "combined" and handoff["run"] == "run_001"
    # Six works; the one found in both parts is counted under both sources.
    mix = {m["provider"]: m for m in handoff["provider_mix"]}
    assert mix["openalex"] == {"provider": "openalex", "kind": "search", "records": 4, "share": round(4 / 6, 4)}
    assert mix["Scopus"] == {"provider": "Scopus", "kind": "import", "records": 3, "share": 0.5}
    # Hyperspectral (Scopus #3) is the only work without an abstract.
    assert handoff["abstracts"] == {"with_abstract": 5, "title_only": 1, "share_with_abstract": round(5 / 6, 4)}
    assert handoff["imports_unchecked"] == 3


# --------------------------------------------------------------------------- the report (D5)


def test_the_report_and_methods_text_name_both_parts(env):
    client, ws, _ = env
    _harvest(client)
    assert _stage(client, "Scopus", SCOPUS, "scopus.ris", searched_on="2026-11-20", query="uav AND weed",
                  limits="English").status_code == 200
    assert _stage(client, "IEEE Xplore", IEEE, "ieee.ris").status_code == 201
    report = client.get(f"{BASE}/report").json()
    kinds = [(row["database"], row["kind"]) for row in report["identification"]]
    assert kinds == [("openalex", "search"), ("Scopus", "import"), ("IEEE Xplore", "import")]
    assert report["dedup"]["unique_works"] == 7 and report["dedup"]["removed"] == 1
    text = report["methods_text"]["text"]
    assert "We searched 1 database (openalex)" in text
    assert "Scopus (3 records; searched on 2026-11-20; search string: `uav AND weed`; limits: English)" in text
    assert "IEEE Xplore (1 record; date searched not stated; search string not stated)" in text
    assert "The 4 imported records were not checked against Crossref or OpenAlex." in text
    assert "Deduplication across the 3 sources removed 1 record, leaving 7 unique works." in text
