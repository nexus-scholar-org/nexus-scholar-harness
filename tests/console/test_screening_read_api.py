"""HCM-06 read-only presentation API (UI-07 §§1-6; RELEASE lane, new GET routes).

Hermetic tests over synthetic registered workspaces in tmp_path (never
workspaces/, never a real workspace). Covers acceptance HCM06-01..06 on the
Python side; HCM06-07..10 are covered by apps/research-ui/tests/screening-live.test.tsx.

New routes under test (8 GETs, zero mutations):
  workspace.py:  GET /api/v1/ui/project-summary
                 GET /api/v1/ui/publication-status
                 GET /api/v1/ui/publication/outputs/{name}
  screening.py:  GET /api/v1/screening/ui/batches
                 GET /api/v1/screening/ui/batch/{n}/rows
                 GET /api/v1/screening/ui/batch/{n}/review
                 GET /api/v1/screening/ui/batch/{n}/criterion-refs
                 GET /api/v1/screening/ui/audit-feed

The pre-existing routes (including POST .../decisions) are untouched: their
behavior is pinned by tests/console/test_console_serve.py and
tests/console/test_console_screening.py, and one test below asserts the
legacy included/excluded routes still serve without a currentness gate
(spec §1.1: storage behavior unchanged; the UI-07 gated routes are the
enforcement point).
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from scholar_harness.console import create_app

REPO_ROOT = Path(__file__).resolve().parents[2]
AGENT_SCREEN = REPO_ROOT / "src" / "scholar_harness" / "agent_screen.py"

WS_ID = "WSP-0123456789abcdef0123456789abcdef"
RUN_ID = "RUN-HCM06-1"
DUMMY_FP = "sha256:" + "b" * 64

PROTOCOL = {
    "$schema": "schemas/v1/protocol.schema.json",
    "created_at": "2026-10-13T00:00:00+00:00",
    "epistemology": {
        "epistemological_rationale": "Empirical check that read APIs report honestly.",
        "incompatible_concepts": [],
        "primary_paradigm": "Pragmatist / Mixed Methods",
        "secondary_paradigm": None,
        "trustworthiness_framework": "JBI Scoping Review Framework",
        "unit_of_analysis": "Read-only presentation shapes",
    },
    "matrix_dimensions": [],
    "metadata": {
        "lead_researcher": "HCM-06 Reader",
        "target_venue_type": "ACM Computing Surveys",
        "timeline_weeks": 8,
        "title": "HCM-06 demo protocol",
    },
    "playbook_type": "SCOPING_REVIEW",
    "project_slug": "hcm06-demo",
    "protocol_id": "PRT-0123456789abcdef0123456789abcdef",
    "research_questions": [
        {
            "id": "RQ1",
            "required_evidence_type": "Empirical read output",
            "synthesis_type": "Comparative Matrix",
            "target_facet": "honesty",
            "text": "Do read APIs report honestly?",
        }
    ],
    "screening_criteria": {
        "exclusion": [
            {
                "criterion": "No comparator arm.",
                "id": "EXC-02",
                "maps_to_rqs": [],
                "reason_category": "INVALID_FORMAT",
            }
        ],
        "inclusion": [
            {
                "criterion": "Names the population and outcome.",
                "id": "INC-01",
                "maps_to_rqs": ["RQ1"],
                "reason_category": None,
            }
        ],
        "two_tier_screening": True,
    },
    "search_strategy": {
        "core_concepts": [
            {
                "boolean_operator": "OR",
                "concept": "Read APIs",
                "synonyms": ["presentation shapes"],
            }
        ],
        "date_range": {"end_year": 2026, "start_year": 2020},
        "languages": ["en"],
        "open_access_preferred": True,
        "target_candidate_pool_size": {"max": 500, "min": 100},
        "target_databases": ["openalex", "semanticscholar"],
    },
    "verification": {
        "coi_and_funding_audit_required": True,
        "minimum_trust_score_threshold": 5.0,
        "reproducibility_das_cas_check": True,
        "retraction_check_required": True,
    },
}


def _papers(batch: int) -> list[dict]:
    base = batch * 2
    return [
        {
            "workspace_id": f"SCI-{base + 1:06d}",
            "title": f"Demo study {base + 1} on read-only reporting",
            "citation": f"Author {base + 1}. Demo study {base + 1} on read-only reporting. J Read; 2024.",
            "abstract": f"Abstract of demo study {base + 1}, served exactly as stored.",
            "venue": "J Read",
            "year": 2024,
            "doi": f"10.0000/hcm06.{base + 1}",
            "url": f"https://example.invalid/hcm06/{base + 1}",
        },
        {
            "workspace_id": f"SCI-{base + 2:06d}",
            "title": f"Demo study {base + 2} on read-only reporting",
            "citation": f"Author {base + 2}. Demo study {base + 2} on read-only reporting. J Read; 2024.",
            "abstract": f"Abstract of demo study {base + 2}, served exactly as stored.",
            "venue": "J Read",
            "year": 2024,
            "doi": f"10.0000/hcm06.{base + 2}",
            "url": f"https://example.invalid/hcm06/{base + 2}",
        },
    ]


def _load_agent_screen():
    spec = importlib.util.spec_from_file_location("agent_screen_hcm06", AGENT_SCREEN)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _protocol_fingerprint() -> str:
    from scholar_protocol.canonical import canonical_fingerprint
    from scholar_protocol.models import ResearchProtocol

    return canonical_fingerprint(ResearchProtocol.model_validate(PROTOCOL))


def _make_ws(tmp, *, n_batches=2, with_decisions=False, old_format=True) -> Path:
    """Synthetic registered workspace. Old-format registry/MANIFEST rows carry
    no accepted lineage, so (without any collect) the generation gate reads
    true-legacy — the honest baseline for LEGACY_UNVERIFIED tests."""
    from scholar_harness.contracts.canonical import (
        canonical_fingerprint,
        canonical_json_bytes,
    )

    ws = tmp / "ws"
    (ws / "literature" / "screening").mkdir(parents=True)
    (ws / "synthesis").mkdir(parents=True)
    (ws / "phase4").mkdir(parents=True)
    (ws / "audit").mkdir(parents=True)

    (ws / "project.json").write_text(
        json.dumps(
            {"project_id": "hcm06-demo", "registered_workspace_id": WS_ID, "stats": {}}
        ),
        encoding="utf-8",
    )
    (ws / "INDEX.md").write_text("# hcm06 demo", encoding="utf-8")
    (ws / "protocol.json").write_text(json.dumps(PROTOCOL), encoding="utf-8")

    verified = []
    for b in range(n_batches):
        verified.extend(
            {
                "workspace_id": p["workspace_id"],
                "title": p["title"],
                "abstract": p["abstract"],
                "venue": p["venue"],
                "year": p["year"],
                "external_ids": {"doi": p["doi"]},
                "url": p["url"],
            }
            for p in _papers(b)
        )
    (ws / "literature" / "verified.json").write_text(
        json.dumps(verified), encoding="utf-8"
    )

    protocol_fp = _protocol_fingerprint()
    manifest_batches = []
    registry = {"artifacts": {}}
    for b in range(n_batches):
        papers = _papers(b)
        art_id = f"ART-hcm06-{b:03d}"
        (ws / "literature" / "screening" / f"batch_{b:03d}.json").write_text(
            json.dumps(
                {
                    "batch_index": b,
                    "batch_size": 2,
                    "status": "PENDING",
                    "protocol": {
                        "title": "HCM-06 demo protocol",
                        "screening_criteria": PROTOCOL["screening_criteria"],
                    },
                    "papers": papers,
                    "artifact_id": art_id,
                }
            ),
            encoding="utf-8",
        )
        manifest_batches.append(
            {
                "batch_index": b,
                "file": f"batch_{b:03d}.json",
                "decisions_file": f"batch_{b:03d}_decisions.json",
                "paper_count": 2,
                "status": "DONE" if with_decisions else "PENDING",
            }
        )
        envelope = {
            "schema_version": "1.0.0",
            "artifact_type": "screening_batch",
            "artifact_id": art_id,
            "created_at": "2026-10-13T00:00:00Z",
            "producer": {
                "package": "scholar-harness",
                "version": "1.0.0",
                "commit": "test",
            },
            "workspace_id": WS_ID,
            "run_id": RUN_ID,
            "protocol_fingerprint": protocol_fp,
            "corpus_fingerprint": DUMMY_FP,
            "inputs": [],
            "data": {
                "binding": {
                    "screening_run_id": RUN_ID,
                    "protocol_fingerprint": protocol_fp,
                    "corpus_fingerprint": DUMMY_FP,
                    "criteria_renderer_version": "v1",
                    "dedup_configuration_hash": DUMMY_FP,
                    "preparation_run_id": "RUN-PREP-HCM06",
                },
                "batch_id": f"BAT-{b:03d}",
                "batch_index": b,
                "candidates": [
                    {"study_id": p["workspace_id"], "title": p["title"]} for p in papers
                ],
            },
        }
        sha = canonical_fingerprint(envelope)
        art_path = ws / "artifacts" / "screening_batch" / f"{art_id}.json"
        art_path.parent.mkdir(parents=True, exist_ok=True)
        art_path.write_bytes(canonical_json_bytes(envelope) + b"\n")
        registry["artifacts"][art_id] = {
            "artifact_type": "screening_batch",
            "path": f"artifacts/screening_batch/{art_id}.json",
            "sha256": sha,
            "accepted_at": "2026-10-13T00:00:00Z",
            "run_id": RUN_ID,
            "producer": {
                "package": "scholar-harness",
                "version": "1.0.0",
                "commit": "test",
            },
        }
        if with_decisions:
            (
                ws / "literature" / "screening" / f"batch_{b:03d}_decisions.json"
            ).write_text(
                json.dumps(
                    {
                        "batch": b,
                        "decisions": [
                            {
                                "workspace_id": papers[0]["workspace_id"],
                                "decision": "INCLUDE",
                                "confidence": 0.9,
                                "matched_inclusion_criteria": ["INC-01"],
                                "screening_reasoning": "Matches the population criterion.",
                            },
                            {
                                "workspace_id": papers[1]["workspace_id"],
                                "decision": "EXCLUDE",
                                "confidence": 0.8,
                                "violated_exclusion_criteria": ["EXC-02"],
                                "screening_reasoning": "No comparator arm.",
                            },
                        ],
                        "reviewed_by": "hcm06-draft",
                        "timestamp": "2026-10-13T00:00:00+00:00",
                    }
                ),
                encoding="utf-8",
            )
    assert old_format  # lineage keys are never written by this builder
    (ws / "literature" / "screening" / "MANIFEST.json").write_text(
        json.dumps(
            {
                "screening_run_id": RUN_ID,
                "total_papers": n_batches * 2,
                "batch_size": 2,
                "total_batches": n_batches,
                "batches": manifest_batches,
            }
        ),
        encoding="utf-8",
    )
    (ws / "audit" / "artifact_registry.json").write_text(
        json.dumps(registry), encoding="utf-8"
    )
    (ws / "audit" / "journal.jsonl").write_text("", encoding="utf-8")
    return ws


def _snapshot(ws: Path) -> dict[str, str]:
    """sha256 of every regular file + mtime, keyed by workspace-relative posix path."""
    out = {}
    for p in sorted(ws.rglob("*")):
        if p.is_file() and ".harness-console" not in p.parts:
            rel = p.relative_to(ws).as_posix()
            out[rel] = (
                f"{p.stat().st_mtime_ns}:{hashlib.sha256(p.read_bytes()).hexdigest()}"
            )
    return out


def _collect_current(ws: Path):
    """Drive the real authority path to a CURRENT generation: recommend (worker),
    console-POST decisions (drafts), stage a publication approval, collect."""
    from scholar_harness.authority.generations import (
        build_publication_snapshot,
        content_sha256,
        mint_publication_approval,
        publication_binding,
        publication_file_bytes,
        resolve_publication_scope,
        write_publication_approval,
    )
    from scholar_harness.authority.binding import OperatorIdentity
    from scholar_harness.screening.worker import run_recommend
    import scholar_harness.authority.generations as generations

    agent_screen = _load_agent_screen()
    manifest = json.loads(
        (ws / "literature" / "screening" / "MANIFEST.json").read_text(encoding="utf-8")
    )
    for row in manifest["batches"]:
        run_recommend(
            ws, int(row["batch_index"]), produced_at="2026-10-13T00:00:00+00:00"
        )
    client = TestClient(create_app(ws))
    for row in manifest["batches"]:
        idx = int(row["batch_index"])
        papers = json.loads(
            (ws / "literature" / "screening" / f"batch_{idx:03d}.json").read_text(
                encoding="utf-8"
            )
        )["papers"]
        r = client.post(
            f"/api/v1/screening/batch/{idx}/decisions",
            json={
                "batch": idx,
                "reviewed_by": "hcm06",
                "decisions": [
                    {
                        "workspace_id": papers[0]["workspace_id"],
                        "decision": "INCLUDE",
                        "confidence": 0.9,
                        # Explicit: the route merges by workspace_id and does
                        # not default a field the caller omitted.
                        "screening_reasoning": "include during console verification review",
                    },
                    {
                        "workspace_id": papers[1]["workspace_id"],
                        "decision": "EXCLUDE",
                        "confidence": 0.8,
                        "screening_reasoning": "exclude during console verification review",
                    },
                ],
            },
        )
        assert r.status_code == 200, r.text

    real_publish = generations.publish_generation
    captured: dict = {}

    def _capture(**kwargs):
        captured["content"] = dict(kwargs["content"])
        raise RuntimeError("capture-only")

    generations.publish_generation = _capture  # type: ignore[method-assign]
    try:
        try:
            agent_screen.cmd_collect(ws)
        except RuntimeError as exc:
            assert str(exc) == "capture-only"
    finally:
        generations.publish_generation = real_publish  # type: ignore[method-assign]
    assert captured.get("content"), "capturing collect never reached the gate"

    scope = resolve_publication_scope(ws)
    digests = {
        name: content_sha256(publication_file_bytes(text))
        for name, text in captured["content"].items()
    }
    snapshot = build_publication_snapshot(
        workspace_id=scope.workspace_id,
        run_id=scope.run_id,
        batch_bindings=[dict(b) for b in scope.batch_bindings],
        protocol_fingerprint=scope.protocol_fingerprint,
        corpus_fingerprint=scope.corpus_fingerprint,
        output_digests=digests,
    )
    binding = publication_binding(
        workspace_id=scope.workspace_id,
        run_id=scope.run_id,
        batch_bindings=[dict(b) for b in scope.batch_bindings],
        protocol_fingerprint=scope.protocol_fingerprint,
        corpus_fingerprint=scope.corpus_fingerprint,
    )
    record = mint_publication_approval(
        operator=OperatorIdentity(
            identity="hcm06-operator", source="publisher-operator-context"
        ),
        binding=binding,
        snapshot_bytes=snapshot,
        approved_at="2026-10-13T12:00:00+00:00",
    )
    write_publication_approval(
        ws / "literature" / "screening", record, staged_at="2026-10-13T12:00:00+00:00"
    )
    agent_screen.cmd_collect(ws)


# ---------------------------------------------------------------------------
# HCM06-01/02: backend-resolved references; no arbitrary paths / caller ids
# ---------------------------------------------------------------------------

_READ_ROUTES = [
    "/api/v1/ui/project-summary",
    "/api/v1/ui/publication-status",
    "/api/v1/screening/ui/batches",
    "/api/v1/screening/ui/audit-feed",
]


def test_ui_refs_resolved_backend_side(tmp_path):
    ws = _make_ws(tmp_path)
    client = TestClient(create_app(ws))
    summary = client.get("/api/v1/ui/project-summary").json()
    assert summary["shape"] == "ui07.project-summary-v1"
    assert summary["workspace_id"] == WS_ID  # from project.json, never the browser
    assert summary["run"]["screening_run_id"] == RUN_ID  # from MANIFEST.json
    assert summary["run"]["batches"] == 2
    assert summary["protocol"]["present"] is True
    assert summary["protocol"]["fingerprint"] == _protocol_fingerprint()

    batches = client.get("/api/v1/screening/ui/batches").json()
    assert batches["shape"] == "ui07.screening-batches-v1"
    assert batches["run_id"] == RUN_ID
    assert batches["count"] == 2
    assert [b["batch_file"] for b in batches["batches"]] == [
        "batch_000.json",
        "batch_001.json",
    ]
    assert all(b["batch_index"] in (0, 1) for b in batches["batches"])


def test_ui_caller_minted_ids_refused_everywhere(tmp_path):
    ws = _make_ws(tmp_path)
    client = TestClient(create_app(ws))
    forged = "workspace_id=WSP-ffffffffffffffffffffffffffffffff&run_id=RUN-FORGED&generation_id=GEN-FORGED"
    for route in _READ_ROUTES + [
        "/api/v1/screening/ui/batch/0/rows",
        "/api/v1/screening/ui/batch/0/review",
        "/api/v1/screening/ui/batch/0/criterion-refs",
        "/api/v1/ui/publication/outputs/included.json",
    ]:
        r = client.get(f"{route}?{forged}")
        assert r.status_code == 422, route
        assert r.json()["detail"]["code"] == "CALLER_IDENTITY_REFUSED", route
    # Fingerprint smuggling is refused too.
    r = client.get("/api/v1/ui/project-summary?protocol_fingerprint=sha256:forged")
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "CALLER_IDENTITY_REFUSED"


def test_ui_publication_output_traversal_refused(tmp_path):
    ws = _make_ws(tmp_path)
    client = TestClient(create_app(ws))
    for name in [
        "nope.json",
        "project.json",
        "included.json%00",
        "generation.json",
    ]:
        r = client.get(f"/api/v1/ui/publication/outputs/{name}")
        assert r.status_code == 400, name
        body = r.json()["detail"]
        assert body["code"] == "INVALID_FILE_NAME", name
        assert "served_outputs" in body["details"], name
    # Dot-segments never reach the router: Starlette normalizes "/.." away
    # before matching, so the framework itself refuses with 404 — still no
    # filesystem escape, still no caller-path resolution.
    assert client.get("/api/v1/ui/publication/outputs/..").status_code == 404
    # A slash never reaches the allowlist: it is not a served name either.
    r = client.get("/api/v1/ui/publication/outputs/a%2Fb")
    assert r.status_code in (400, 404)


def test_ui_missing_batch_is_404_not_empty_200(tmp_path):
    ws = _make_ws(tmp_path)
    client = TestClient(create_app(ws))
    for route in [
        "/api/v1/screening/ui/batch/9/rows",
        "/api/v1/screening/ui/batch/9/review",
        "/api/v1/screening/ui/batch/9/criterion-refs",
    ]:
        r = client.get(route)
        assert r.status_code == 404, route
        assert r.json()["detail"]["code"] == "BATCH_MISSING", route
        assert "batch_009.json" in r.json()["detail"]["message"], route


# ---------------------------------------------------------------------------
# HCM06-03: reads never mutate, migrate, or mint
# ---------------------------------------------------------------------------


def test_ui_reads_never_mutate(tmp_path):
    ws = _make_ws(tmp_path, with_decisions=True)
    _collect_current(ws)
    client = TestClient(create_app(ws))
    before = _snapshot(ws)
    battery = [
        "/api/v1/ui/project-summary",
        "/api/v1/ui/publication-status",
        "/api/v1/ui/publication/outputs/included.json",
        "/api/v1/ui/publication/outputs/excluded.json",
        "/api/v1/ui/publication/outputs/conflicts.json",
        "/api/v1/ui/publication/outputs/prisma_screening_report.md",
        "/api/v1/ui/publication/outputs/prisma_report.json",
        "/api/v1/screening/ui/batches",
        "/api/v1/screening/ui/batch/0/rows",
        "/api/v1/screening/ui/batch/1/rows?limit=1&offset=1",
        "/api/v1/screening/ui/batch/0/review",
        "/api/v1/screening/ui/batch/0/criterion-refs",
        "/api/v1/screening/ui/audit-feed",
        "/api/v1/screening/ui/audit-feed?action=SCREEN_DECISIONS",
        # Error paths must not write either.
        "/api/v1/screening/ui/batch/9/rows",
        "/api/v1/ui/publication/outputs/nope.json",
        "/api/v1/ui/project-summary?workspace_id=WSP-00000000000000000000000000000000",
    ]
    for route in battery:
        client.get(route)
    after = _snapshot(ws)
    assert before == after
    # No staging, lock, recovery, or minted-identity residue.
    leftovers = [p for p in ws.rglob("*.tmp*")] + [
        ws / "literature" / "screening" / ".collect.lock"
    ]
    assert [p for p in leftovers if p.exists()] == []
    assert (
        json.loads((ws / "project.json").read_text(encoding="utf-8"))[
            "registered_workspace_id"
        ]
        == WS_ID
    )


def test_ui_legacy_routes_unchanged_without_gate(tmp_path):
    """Spec §1.1: existing storage behavior is unchanged; only the new UI-07
    gated routes enforce currentness."""
    ws = _make_ws(tmp_path, with_decisions=True)
    (ws / "literature" / "included.json").write_text(
        json.dumps([{"workspace_id": "SCI-000001"}]), encoding="utf-8"
    )
    client = TestClient(create_app(ws))
    assert client.get("/api/v1/literature/included").status_code == 200
    status = client.get("/api/v1/ui/publication-status").json()
    assert status["status"] == "LEGACY_UNVERIFIED"  # no generation: honestly legacy
    gated = client.get("/api/v1/ui/publication/outputs/included.json")
    assert gated.status_code == 409
    assert gated.json()["detail"]["code"] == "GENERATION_LEGACY_UNVERIFIED"


# ---------------------------------------------------------------------------
# HCM06-04: draft / unresolved / approved / stale / superseded / legacy / current
# ---------------------------------------------------------------------------


def test_ui_review_draft_vs_unresolved_vs_approved(tmp_path):
    from scholar_harness.authority.review import approve_command

    ws = _make_ws(tmp_path, with_decisions=True)
    client = TestClient(create_app(ws))

    # Draft: decisions recorded, no approval, no deferral.
    draft = client.get("/api/v1/screening/ui/batch/0/review").json()
    assert draft["shape"] == "ui07.review-state-v1"
    assert draft["recommendation"]["present"] is False  # no worker file yet
    assert draft["resolution"] == {"resolved": 2, "total": 2, "unresolved_rows": []}
    assert draft["override"] == {"superseded": False}
    assert draft["review"] == {"present": False}
    assert draft["deferral"] == {"present": False}

    # Unresolved-only: MAYBE rows are named, never coerced. (Written after
    # the approval below would break approve_command's whole-manifest content
    # computation, so the unresolved probe runs on batch 1 last.)
    # Approved: operator approval over content differing from the worker draft
    # becomes a superseding revision (original preserved, fresh binding).
    from scholar_harness.screening.worker import run_recommend

    run_recommend(ws, 0, produced_at="2026-10-13T00:00:00+00:00")
    (ws / "literature" / "screening" / "operator_context.json").write_text(
        json.dumps({"operator_identity": "hcm06-operator"}), encoding="utf-8"
    )
    approve_command(ws, 0, approved_at="2026-10-13T12:00:00+00:00")
    approved = client.get("/api/v1/screening/ui/batch/0/review").json()
    assert approved["recommendation"]["present"] is True
    assert approved["recommendation"]["schema"] == "harness-screening-recommendation-v1"
    assert approved["recommendation"]["method"] == "DETERMINISTIC_CLI"
    assert (
        approved["override"]["superseded"] is True
    )  # researcher content != worker draft
    assert approved["override"]["snapshot_fingerprint"].startswith("sha256:")
    assert approved["override"]["recommendation_sha256"].startswith("sha256:")
    assert approved["override"]["final_decision_sha256"].startswith("sha256:")
    assert approved["review"]["present"] is True
    assert approved["review"]["approval_fingerprint"].startswith("sha256:")

    (ws / "literature" / "screening" / "batch_001_decisions.json").write_text(
        json.dumps(
            [
                {"workspace_id": "SCI-000003", "decision": "MAYBE"},
                {"workspace_id": "SCI-000004", "decision": "CONFLICT"},
            ]
        ),
        encoding="utf-8",
    )
    unresolved = client.get("/api/v1/screening/ui/batch/1/review").json()
    assert unresolved["resolution"] == {
        "resolved": 0,
        "total": 2,
        "unresolved_rows": ["SCI-000003", "SCI-000004"],
    }


def test_ui_batches_stale_binding(tmp_path):
    ws = _make_ws(tmp_path, with_decisions=True)
    client = TestClient(create_app(ws))
    before = client.get("/api/v1/screening/ui/batches").json()
    assert all("binding" not in b for b in before["batches"])  # current: member absent

    # Supersede the registered parent envelope after acceptance.
    art = ws / "artifacts" / "screening_batch" / "ART-hcm06-000.json"
    payload = json.loads(art.read_bytes().decode("utf-8"))
    payload["data"]["candidates"].append(
        {"study_id": "SCI-999999", "title": "late arrival"}
    )
    art.write_bytes(
        json.dumps(payload, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    )
    stale = client.get("/api/v1/screening/ui/batches").json()
    changed = [b for b in stale["batches"] if b["batch_index"] == 0][0]
    assert changed["binding"] == {
        "state": "STALE_BINDING",
        "reason": "Parent batch superseded after acceptance; re-resolve before approval.",
    }
    untouched = [b for b in stale["batches"] if b["batch_index"] == 1][0]
    assert "binding" not in untouched


def test_ui_publication_statuses_current_stale_mismatched_legacy(tmp_path):
    ws = _make_ws(tmp_path, with_decisions=True)
    _collect_current(ws)
    client = TestClient(create_app(ws))

    current = client.get("/api/v1/ui/publication-status").json()
    assert current["status"] == "CURRENT"
    assert current["code"] is None
    assert current["generation_id"].startswith("GEN-")
    assert set(current["outputs"]) == {
        "included.json",
        "excluded.json",
        "conflicts.json",
        "prisma_screening_report.md",
        "prisma_report.json",
    }
    # The summary reuses the identical status object verbatim (never disagrees).
    summary_pub = client.get("/api/v1/ui/project-summary").json()["readiness"][
        "publication"
    ]
    assert summary_pub == current

    # STALE: output digest drift after publication.
    inc = ws / "literature" / "included.json"
    inc.write_text(inc.read_text(encoding="utf-8") + " ", encoding="utf-8")
    stale = client.get("/api/v1/ui/publication-status").json()
    assert stale["status"] == "STALE"
    assert stale["code"] == "GENERATION_STALE"
    assert stale["outputs"]["included.json"].startswith(
        "sha256:"
    )  # manifest facts, not bytes

    # MISMATCHED: generation record deleted beside surviving authorized material.
    (ws / "literature" / "screening" / "generation.json").unlink()
    mismatched = client.get("/api/v1/ui/publication-status").json()
    assert mismatched["status"] == "MISMATCHED"
    assert mismatched["code"] == "GENERATION_MISMATCHED"

    # LEGACY_UNVERIFIED: prepared old-format workspace, no authorized material anywhere.
    legacy_ws = _make_ws(tmp_path / "legacy")
    legacy = (
        TestClient(create_app(legacy_ws)).get("/api/v1/ui/publication-status").json()
    )
    assert legacy["status"] == "LEGACY_UNVERIFIED"
    assert legacy["code"] == "GENERATION_LEGACY_UNVERIFIED"
    assert legacy["generation_id"] is None
    assert legacy["outputs"] == {}


# ---------------------------------------------------------------------------
# HCM06-05: unavailable sources are explicit, never silent or invented
# ---------------------------------------------------------------------------


def test_ui_empty_workspace_is_explicit(tmp_path):
    ws = tmp_path / "ws"
    (ws / "literature" / "screening").mkdir(parents=True)
    (ws / "audit").mkdir(parents=True)
    (ws / "project.json").write_text(
        json.dumps({"project_id": "empty"}), encoding="utf-8"
    )
    (ws / "audit" / "journal.jsonl").write_text("", encoding="utf-8")
    client = TestClient(create_app(ws))

    summary = client.get("/api/v1/ui/project-summary").json()
    assert summary["workspace_id"] is None  # unregistered: explicit, never minted
    assert summary["protocol"] == {"present": False, "fingerprint": None}
    assert summary["run"] is None
    assert summary["readiness"] == {
        "screening_prepared": False,
        "all_batches_resolved": False,
        "publication": summary["readiness"]["publication"],
    }
    reasons = {m["reason"] for m in summary["missing"]}
    assert {"IDENTITY_UNREGISTERED", "NOT_PREPARED"} <= reasons

    # The §4 empty envelope, exactly: null run, zero count, NOT_PREPARED.
    batches = client.get("/api/v1/screening/ui/batches").json()
    assert batches == {
        "shape": "ui07.screening-batches-v1",
        "run_id": None,
        "count": 0,
        "batches": [],
        "missing": [
            {"file": "literature/screening/MANIFEST.json", "reason": "NOT_PREPARED"}
        ],
    }
    feed = client.get("/api/v1/screening/ui/audit-feed").json()
    assert feed == {
        "shape": "ui07.audit-feed-v1",
        "total": 0,
        "offset": 0,
        "limit": 100,
        "items": [],
    }


def test_ui_no_decisions_yet_is_200_with_reason(tmp_path):
    ws = _make_ws(tmp_path)  # prepared, no decisions anywhere
    client = TestClient(create_app(ws))
    batches = client.get("/api/v1/screening/ui/batches").json()
    assert batches["run_id"] == RUN_ID
    first = batches["batches"][0]
    assert first["decisions_file"] is None
    assert first["decisions_count"] is None
    assert first["coverage"] == "INCOMPLETE"
    assert first["collected"] is False
    assert {"batch": "batch_000.json", "reason": "NO_DECISIONS_YET"} in batches[
        "missing"
    ]

    review = client.get("/api/v1/screening/ui/batch/0/review").json()
    assert review["resolution"] == {"resolved": 0, "total": 2, "unresolved_rows": []}
    assert {"batch": "batch_000.json", "reason": "NO_DECISIONS_YET"} in review[
        "missing"
    ]

    rows = client.get("/api/v1/screening/ui/batch/0/rows").json()
    assert rows["total"] == 2
    assert all(
        r["decision"] == "PENDING_REVIEW" for r in rows["rows"]
    )  # never defaulted INCLUDE
    assert {"batch": "batch_000.json", "reason": "NO_DECISIONS_YET"} in rows["missing"]


def test_ui_malformed_files_are_500_not_silent(tmp_path):
    ws = _make_ws(tmp_path, with_decisions=True)
    (ws / "literature" / "screening" / "batch_000.json").write_text(
        "{not json", encoding="utf-8"
    )
    client = TestClient(create_app(ws))
    for route in ["/api/v1/screening/ui/batches", "/api/v1/screening/ui/batch/0/rows"]:
        r = client.get(route)
        assert r.status_code == 500, route
        assert r.json()["detail"]["code"] == "UNPARSEABLE_JSON", route
    (ws / "literature" / "screening" / "batch_000_decisions.json").write_text(
        "[oops", encoding="utf-8"
    )
    r = client.get("/api/v1/screening/ui/batch/0/review")
    assert r.status_code == 500
    assert r.json()["detail"]["code"] == "UNPARSEABLE_JSON"


def test_ui_rows_serve_stored_bytes_with_coverage_and_refs(tmp_path):
    ws = _make_ws(tmp_path, with_decisions=True)
    client = TestClient(create_app(ws))

    batches = client.get("/api/v1/screening/ui/batches").json()
    first = batches["batches"][0]
    assert first["coverage"] == "COMPLETE"
    assert (
        "missing_ids" not in first and "extra_ids" not in first
    )  # COMPLETE carries none
    assert first["decisions_count"] == 2

    rows = client.get("/api/v1/screening/ui/batch/0/rows").json()
    assert rows["shape"] == "ui07.screening-rows-v1"
    by_id = {r["study_id"]: r for r in rows["rows"]}
    assert by_id["SCI-000001"]["decision"] == "INCLUDE"
    assert by_id["SCI-000002"]["decision"] == "EXCLUDE"
    assert by_id["SCI-000001"]["citation"].startswith("Author 1.")
    assert by_id["SCI-000002"]["abstract"].endswith("as stored.")
    assert by_id["SCI-000001"]["criterion_refs"] == {
        "inclusion": ["INC-01"],
        "exclusion": [],
    }
    assert by_id["SCI-000002"]["source_locators"]["doi"] == "10.0000/hcm06.2"

    paged = client.get("/api/v1/screening/ui/batch/0/rows?limit=1&offset=1").json()
    assert (paged["total"], paged["limit"], paged["offset"]) == (2, 1, 1)
    assert [r["study_id"] for r in paged["rows"]] == ["SCI-000002"]

    refs = client.get("/api/v1/screening/ui/batch/0/criterion-refs").json()
    assert refs["shape"] == "ui07.criterion-refs-v1"
    assert refs["protocol_fingerprint"] == _protocol_fingerprint()
    assert refs["inclusion"] == [
        {"id": "INC-01", "text": "Names the population and outcome."}
    ]
    assert refs["exclusion"] == [{"id": "EXC-02", "text": "No comparator arm."}]
    assert refs["sources"][0]["doi"] == "10.0000/hcm06.1"
    assert refs["missing"] == []


def test_ui_incomplete_coverage_names_missing_and_extra(tmp_path):
    ws = _make_ws(tmp_path, with_decisions=True)
    # Drop one decision, invent one extra: both directions are named.
    keep = json.loads(
        (ws / "literature" / "screening" / "batch_000_decisions.json").read_text(
            encoding="utf-8"
        )
    )
    keep["decisions"] = [
        keep["decisions"][0],
        {"workspace_id": "SCI-999999", "decision": "INCLUDE"},
    ]
    (ws / "literature" / "screening" / "batch_000_decisions.json").write_text(
        json.dumps(keep), encoding="utf-8"
    )
    client = TestClient(create_app(ws))
    first = [
        b
        for b in client.get("/api/v1/screening/ui/batches").json()["batches"]
        if b["batch_index"] == 0
    ][0]
    assert first["coverage"] == "INCOMPLETE"
    assert first["missing_ids"] == ["SCI-000002"]
    assert first["extra_ids"] == ["SCI-999999"]


# ---------------------------------------------------------------------------
# HCM06-06: publication outputs serve ONLY when CURRENT
# ---------------------------------------------------------------------------

_PUB_OUTPUTS = [
    "included.json",
    "excluded.json",
    "conflicts.json",
    "prisma_screening_report.md",
    "prisma_report.json",
]


def test_ui_publication_outputs_serve_only_when_current(tmp_path):
    ws = _make_ws(tmp_path, with_decisions=True)
    _collect_current(ws)
    client = TestClient(create_app(ws))
    for name in _PUB_OUTPUTS:
        r = client.get(f"/api/v1/ui/publication/outputs/{name}")
        assert r.status_code == 200, name
        body = r.json()
        assert body["filename"] == name
        assert body["content"] == (ws / "literature" / name).read_text(encoding="utf-8")


def test_ui_publication_outputs_refuse_without_bytes(tmp_path):
    cases = []
    stale_ws = _make_ws(tmp_path / "stale", with_decisions=True)
    _collect_current(stale_ws)
    (stale_ws / "literature" / "included.json").write_text(
        (stale_ws / "literature" / "included.json").read_text(encoding="utf-8") + " ",
        encoding="utf-8",
    )
    cases.append((stale_ws, "GENERATION_STALE"))

    legacy_ws = _make_ws(tmp_path / "legacy", with_decisions=True)
    (legacy_ws / "literature" / "included.json").write_text("[]", encoding="utf-8")
    cases.append((legacy_ws, "GENERATION_LEGACY_UNVERIFIED"))

    mismatch_ws = _make_ws(tmp_path / "mismatch", with_decisions=True)
    _collect_current(mismatch_ws)
    (mismatch_ws / "literature" / "screening" / "generation.json").unlink()
    cases.append((mismatch_ws, "GENERATION_MISMATCHED"))

    for ws, code in cases:
        client = TestClient(create_app(ws))
        r = client.get("/api/v1/ui/publication/outputs/included.json")
        assert r.status_code == 409, code
        body = r.json()["detail"]
        assert body["code"] == code, code
        assert "content" not in body and "filename" not in body  # no bytes, ever
        assert body["message"]


def test_ui_audit_feed_projects_journey_newest_first(tmp_path):
    ws = _make_ws(tmp_path, with_decisions=True)
    _collect_current(ws)
    client = TestClient(create_app(ws))
    feed = client.get("/api/v1/screening/ui/audit-feed").json()
    assert feed["shape"] == "ui07.audit-feed-v1"
    assert feed["total"] >= 2
    actions = [e["action"] for e in feed["items"]]
    # The journey projection serves screening writes only: console drafts,
    # the collect acceptance record, and the published generation.
    assert set(actions) <= {
        "SCREEN_DECISIONS",
        "SCREENING_DECISIONS_RECORDED",
        "SCREENING_GENERATION_PUBLISHED",
    }
    assert "SCREENING_GENERATION_PUBLISHED" in actions
    for item in feed["items"]:
        assert set(item) == {
            "timestamp",
            "event_id",
            "action",
            "agent_or_tool",
            "description",
            "status",
        }
    narrowed = client.get(
        "/api/v1/screening/ui/audit-feed?action=SCREEN_DECISIONS"
    ).json()
    assert narrowed["total"] >= 1
    assert {e["action"] for e in narrowed["items"]} == {"SCREEN_DECISIONS"}


def test_ui_locator_less_paper_reports_no_source_locators(tmp_path):
    """H-01: the renamed NO_SOURCE_LOCATORS reason surfaces (never invented,
    never silent) on both the rows join and the criterion-refs sources.
    Locator coverage is evaluated on decided rows, so the fixture keeps
    decisions and strips only the locator fields."""
    ws = _make_ws(tmp_path, n_batches=1, with_decisions=True)
    batch_file = ws / "literature" / "screening" / "batch_000.json"
    batch = json.loads(batch_file.read_text(encoding="utf-8"))
    for paper in batch["papers"]:
        for key in ("doi", "url", "venue", "year"):
            paper.pop(key, None)
    batch_file.write_text(json.dumps(batch), encoding="utf-8")
    verified = json.loads(
        (ws / "literature" / "verified.json").read_text(encoding="utf-8")
    )
    for entry in verified:
        for key in ("doi", "url", "venue", "year", "external_ids"):
            entry.pop(key, None)
    (ws / "literature" / "verified.json").write_text(
        json.dumps(verified), encoding="utf-8"
    )
    client = TestClient(create_app(ws))
    rows = client.get("/api/v1/screening/ui/batch/0/rows").json()
    assert {"study": "SCI-000001", "reason": "NO_SOURCE_LOCATORS"} in rows["missing"]
    refs = client.get("/api/v1/screening/ui/batch/0/criterion-refs").json()
    assert {"study": "SCI-000001", "reason": "NO_SOURCE_LOCATORS"} in refs["missing"]


def test_ui_loopback_cors_allows_get_only(tmp_path):
    """H-02: loopback origins get ACAO on GET; cross-origin POST stays
    preflight-blocked by design."""
    ws = _make_ws(tmp_path, n_batches=1)
    client = TestClient(create_app(ws))
    r = client.get(
        "/api/v1/screening/ui/batches",
        headers={"Origin": "http://localhost:3000"},
    )
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"
    pre = client.options(
        "/api/v1/screening/ui/batches",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert "POST" not in pre.headers.get("access-control-allow-methods", "")
