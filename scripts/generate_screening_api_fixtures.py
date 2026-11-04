"""Generate the shared screening API fixtures (contract §8, M1a).

One JSON file per route and state under `tests/fixtures/screening_api/`:
`{name, request: {method, path, json?, scope?}, response: {status, body}}`.
They are produced by driving the real console over HTTP against a synthetic
three-study workspace whose every input is pinned (corpus time, producer
commit, batch time, event ids, receive clock), so the bytes are reproducible.

The engine's contract test (`tests/console/test_screening_api_contract.py`)
runs this generator in memory and requires the committed files to match. The
M1b UI loads the same files as its mock data, so a fixture change is a
contract change and is reviewed by both tracks.

    uv run python scripts/generate_screening_api_fixtures.py          # write
    uv run python scripts/generate_screening_api_fixtures.py --check  # verify
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from contextlib import ExitStack
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "tests" / "fixtures" / "screening_api"
PROTOCOL = ROOT / "tests" / "kits" / "protocol" / "fixtures" / "canonical" / "identity_base.json"
WS_ID = "WSP-" + "f" * 32
BASE = "/api/v1/screening"
DESKTOP, PHONE = "fixture-desktop-token", "fixture-phone-token"
FIXED = datetime(2026, 11, 4, 9, 0, tzinfo=UTC)
RECEIVED = "2026-11-04T09:30:00Z"
SCREENER = "researcher:local"


class _FixedDatetime(datetime):
    @classmethod
    def now(cls, tz=None):  # pinned clock: reproducible artifacts
        return FIXED if tz is None else FIXED.astimezone(tz)


def _workspace(root: Path, *, prepare: bool = True) -> Path:
    from scholar_harness.contracts import AcceptanceContext, accept_artifact
    from scholar_harness.screening import batcher
    from scholar_protocol.canonical import canonical_fingerprint
    from scholar_protocol.models import ResearchProtocol
    from scholar_search.identity import build_corpus_snapshot_artifact
    from scholar_search.models import Author, Document, ExternalIds

    ws = root / "ws"
    ws.mkdir()
    (ws / "project.json").write_text(
        json.dumps({"project_id": "fixtures", "registered_workspace_id": WS_ID}), encoding="utf-8"
    )
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    (ws / "protocol.json").write_text(json.dumps(protocol), encoding="utf-8")
    (ws / "audit").mkdir()
    (ws / "audit" / "journal.jsonl").touch()
    if not prepare:
        return ws
    fingerprint = canonical_fingerprint(ResearchProtocol.model_validate(protocol))
    docs = [
        Document(
            title=title,
            year=2025,
            provider="crossref",
            provider_id=f"fixture-{i}",
            external_ids=ExternalIds(doi=f"10.1000/fixture-{i}"),
            abstract=abstract,
            authors=[Author("Reviewer")],
            workspace_id=f"SCI-00000{i}",
        )
        for i, (title, abstract) in enumerate(
            [
                ("UAV multispectral weed mapping in maize", "We map weeds from drone imagery in maize fields."),
                ("Ground robot weed detection", "A wheeled robot detects weeds between crop rows."),
                ("Weed segmentation from aerial orthomosaics", None),
            ]
        )
    ]
    corpus = build_corpus_snapshot_artifact(
        docs, workspace_id=WS_ID, run_id="RUN-fixtures", protocol_fingerprint=fingerprint,
        created_at=FIXED, commit="0" * 40,
    ).artifact
    accepted = accept_artifact(
        ws, corpus,
        expected=AcceptanceContext(
            workspace_id=WS_ID, protocol_fingerprint=fingerprint, corpus_fingerprint=corpus["corpus_fingerprint"]
        ),
    )
    assert accepted.accepted, accepted.issues
    (ws / "literature").mkdir()
    (ws / "literature" / "verified.json").write_text(
        json.dumps([{"workspace_id": d.workspace_id, "title": d.title, "abstract": d.abstract} for d in docs]),
        encoding="utf-8",
    )
    batcher.cmd_prepare(ws, batch_size=20)
    return ws


def _uuid(n: int) -> str:
    return f"0193f4a2-7c1e-7b2a-9e55-{n:012d}"


def generate() -> dict[str, dict[str, Any]]:
    """Every fixture, by file name, built from a fresh pinned workspace."""
    from fastapi.testclient import TestClient

    from scholar_harness.console import create_app
    from scholar_harness.console.api import screening_v1
    from scholar_harness.screening import batcher
    from scholar_harness.screening import proposals as pr

    fixtures: dict[str, dict[str, Any]] = {}
    with ExitStack() as stack, tempfile.TemporaryDirectory() as tmp:
        stack.enter_context(mock.patch.object(batcher, "_harness_commit", lambda: "0" * 40))
        stack.enter_context(mock.patch.object(batcher, "datetime", _FixedDatetime))
        stack.enter_context(mock.patch.object(screening_v1, "_now", lambda: RECEIVED))
        ws = _workspace(Path(tmp))
        client = TestClient(
            create_app(ws, token=DESKTOP, phone_tokens={PHONE}),
            base_url="http://127.0.0.1",
            headers={"Authorization": f"Bearer {DESKTOP}"},
        )

        def call(name: str, method: str, path: str, *, body: Any = None, scope: str = "desktop") -> Any:
            headers = {"Authorization": f"Bearer {PHONE}"} if scope == "phone" else {}
            response = client.request(method, path, json=body, headers=headers)
            request: dict[str, Any] = {"method": method, "path": path, "scope": scope}
            if body is not None:
                request["json"] = body
            fixtures[f"{name}.json"] = {
                "name": name,
                "request": request,
                "response": {"status": response.status_code, "body": response.json()},
            }
            return response.json()

        call("summary_start", "GET", f"{BASE}/summary")
        queue = call("queue_needs_you", "GET", f"{BASE}/queue?view=needs_you")
        call("queue_decided_empty", "GET", f"{BASE}/queue?view=decided")
        studies = [item["study_id"] for item in queue["items"]]
        first, second, third = studies
        record = call("record_detail", "GET", f"{BASE}/records/{first}")
        binding = record["binding"]

        protocol = json.loads((ws / "protocol.json").read_text(encoding="utf-8"))
        text = pr.record_text(record["title"], record["abstract"])
        quote = "drone imagery"
        start = text.index(quote)
        pr.submit_proposal(
            ws, study_id=first, title=record["title"], abstract=record["abstract"],
            output={
                "criteria": [
                    {"id": c["id"], "answer": "yes" if c["kind"] == "inclusion" else "no",
                     "evidence": {"text": quote, "start": start, "end": start + len(quote)}}
                    for c in record["criteria"]
                ],
                "cannot_decide": False,
            },
            protocol=protocol, protocol_fingerprint=binding["protocol_fingerprint"],
            provenance={"task_id": "screening-proposal", "task_version": "screen-v1", "driver": "mcp",
                        "model": "claude-opus-5-5", "prompt_sha256": "sha256:" + "a" * 64},
            created_at="2026-11-04T09:10:00Z",
        )
        call("proposal_hidden", "GET", f"{BASE}/records/{first}/proposal")

        def event(n: int, study: str, outcome: str, **extra: Any) -> dict[str, Any]:
            item = {
                "event_id": _uuid(n), "study_id": study, "screener_id": SCREENER, "method": "HUMAN",
                "outcome": outcome, "reason_code": "EXC-01" if outcome == "EXCLUDE" else None,
                "note": None, "criteria": [], "decided_at": "2026-11-04T09:20:00.000Z",
                "device": "desktop", "supersedes": None, "proposal_shown": None,
                "binding": {**binding} if study == first else client.get(f"{BASE}/records/{study}").json()["binding"],
            }
            item.update(extra)
            return item

        include = event(1, first, "INCLUDE")
        call("events_accepted", "POST", f"{BASE}/decisions/events", body={"events": [include]})
        call("events_duplicate", "POST", f"{BASE}/decisions/events", body={"events": [include]})
        call("events_refused_reason_code", "POST", f"{BASE}/decisions/events",
             body={"events": [event(2, second, "EXCLUDE", reason_code=None)]})
        stale = event(3, second, "EXCLUDE")
        stale["binding"] = {**stale["binding"], "batch_sha256": "sha256:" + "0" * 64}
        call("events_refused_stale_binding", "POST", f"{BASE}/decisions/events", body={"events": [stale]})
        call("proposal_revealed", "GET", f"{BASE}/records/{first}/proposal")
        call("events_conflict", "POST", f"{BASE}/decisions/events",
             body={"events": [event(4, first, "EXCLUDE", device="phone")]}, scope="phone")
        call("conflicts_open", "GET", f"{BASE}/decisions/conflicts")
        call("conflict_resolved", "POST", f"{BASE}/decisions/conflicts/{first}/resolve",
             body={"keep_event_id": include["event_id"]})
        call("events_more_decided", "POST", f"{BASE}/decisions/events",
             body={"events": [event(5, second, "EXCLUDE"), event(6, third, "MAYBE", note="Title only; check the full text.")]})
        call("prisma_preview", "GET", f"{BASE}/prisma/preview")
        call("summary_done", "GET", f"{BASE}/summary")
        call("settings_default", "GET", f"{BASE}/settings")
        call("phone_scope_refused", "POST", f"{BASE}/prepare", body={"batch_size": 20}, scope="phone")

        (Path(tmp) / "bare").mkdir()
        bare = _workspace(Path(tmp) / "bare", prepare=False)
        bare_client = TestClient(create_app(bare), base_url="http://127.0.0.1")
        response = bare_client.post(f"{BASE}/prepare", json={"batch_size": 20})
        fixtures["prepare_snapshot_not_accepted.json"] = {
            "name": "prepare_snapshot_not_accepted",
            "request": {"method": "POST", "path": f"{BASE}/prepare", "scope": "desktop", "json": {"batch_size": 20}},
            "response": {"status": response.status_code, "body": response.json()},
        }
    return fixtures


def _bytes(fixture: dict[str, Any]) -> bytes:
    return (json.dumps(fixture, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="fail if the committed fixtures are stale")
    args = parser.parse_args(argv)
    fixtures = generate()
    if args.check:
        stale = sorted(
            name for name, fixture in fixtures.items()
            if not (OUT / name).is_file()
            or (OUT / name).read_bytes().replace(b"\r\n", b"\n") != _bytes(fixture)
        )
        extra = sorted(p.name for p in OUT.glob("*.json") if p.name not in fixtures) if OUT.is_dir() else []
        if stale or extra:
            print(f"screening API fixtures are stale: changed={stale} unexpected={extra}")
            return 1
        print(f"screening API fixtures are current ({len(fixtures)} files)")
        return 0
    OUT.mkdir(parents=True, exist_ok=True)
    for name, fixture in fixtures.items():
        (OUT / name).write_bytes(_bytes(fixture))
    print(f"wrote {len(fixtures)} fixtures to {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
