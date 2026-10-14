"""UI-05 evidence lineage read route (RELEASE lane, one new GET route).

Hermetic tests over synthetic registered workspaces in tmp_path (never
workspaces/, never a real workspace). The builder below reuses the HCM-06
screening fixtures (protocol, batches, registry) through the frozen file
layout, drives the real authority path to a CURRENT generation, then adds
four Contract v1 lineage artifacts plus their registry entries:

  corpus_snapshot  (studies: canonical ids, recorded aliases, titles, DOIs)
  document_manifest (document records: study link, source hash, status)
  screening_decisions (recorded INCLUDE/EXCLUDE decisions with reasons)
  claims_ledger    (claims with evidence ids + citation tokens, and the
                    evidence itself: quote, locator, document link)

The new route under test (GET only, zero mutations):

  workspace.py:  GET /api/v1/ui/lineage?claim_id=... | ?chunk_id=...

Acceptance on the Python side: UI05-01 (complete trace), UI05-02 (four
typed broken-link refusals), UI05-03 (served bytes equal stored bytes, no
entailment language), UI05-06 (reads never mutate; TestClient only, no
spawned servers), UI05-07 (CURRENT gate, stale refuses without bytes).
UI05-04/05 are covered by apps/research-ui/tests/lineage.test.tsx.
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
HCM06_TEST = REPO_ROOT / "tests" / "console" / "test_screening_read_api.py"


def _load_hcm06():
    spec = importlib.util.spec_from_file_location("hcm06_lineage_base", HCM06_TEST)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


_hcm06 = _load_hcm06()

WS_ID = _hcm06.WS_ID
RUN_ID = _hcm06.RUN_ID

STUDY_1 = "STU-LIN-1"
STUDY_2 = "STU-LIN-2"
STUDY_UNDECIDED = "STU-LIN-9"
STUDY_UNKNOWN = "STU-LIN-999"
LEGACY_ALIAS_1 = "SCI-000001"
LEGACY_ALIAS_2 = "SCI-000002"
DOC_1 = "DOC-LIN-1"
DOC_2 = "DOC-LIN-2"
DOC_UNDECIDED = "DOC-LIN-9"
CLAIM_1 = "CLM-LIN-1"
EVIDENCE_1 = "EV-LIN-1"
CHUNK_1 = "CHK-LIN-1"
HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64
HASH_F = "sha256:" + "f" * 64

CLAIM_TEXT = "Structured extraction improves auditability."
CLAIM_KIND = "finding"
QUOTE_1 = "We recorded every decision with its provenance."
LOCATOR_1 = "Methods, paragraph 4"
TITLE_1 = "Lineage study one: recorded decisions with provenance."
TITLE_2 = "Lineage study two: comparator record."
TITLE_UNDECIDED = "Lineage study nine: awaiting a decision."
DOI_1 = "10.0000/lineage1"
# Stored bytes of the real collect-path decisions (console POST defaults):
# SCI-000001 INCLUDE / SCI-000002 EXCLUDE, reason "<decision> during ...".
DECISION_REASON_1 = "include during console verification review"
TOKEN_1 = f"[rag:v2:{WS_ID}:{STUDY_1}:{CHUNK_1}]"


def _envelope(*, artifact_type, artifact_id, protocol_fp, corpus_fp, data, created_at):
    return {
        "schema_version": "1.0.0",
        "artifact_type": artifact_type,
        "artifact_id": artifact_id,
        "created_at": created_at,
        "producer": {
            "package": "scholar-harness",
            "version": "1.0.0",
            "commit": "test",
        },
        "workspace_id": WS_ID,
        "run_id": RUN_ID,
        "protocol_fingerprint": protocol_fp,
        "corpus_fingerprint": corpus_fp,
        "inputs": [],
        "data": data,
    }


def add_lineage(ws: Path, *, variant: str = "complete") -> dict[str, str]:
    """Add lineage artifacts to a workspace that is already at CURRENT generation.

    Used for the non-collect variants (legacy/stale workspaces): the screening
    scope keeps its own fingerprint and the lineage triple stands alone.
    """
    protocol_fp = _hcm06._protocol_fingerprint()
    plan = plan_lineage(protocol_fp, variant)
    return write_lineage(ws, protocol_fp, plan)


def _study_row(study_id, record_id, *, aliases=(), doi, title, year):
    return {
        "study_id": study_id,
        "source_record_ids": [record_id],
        "alias_ids": list(aliases),
        "external_ids": {"doi": [doi]},
        "title": title,
        "publication_year": year,
    }


def plan_lineage(protocol_fp: str, variant: str):
    """Return (corpus_data, corpus_fp, documents, ledger_data, ledger_corpus_fp).

    The corpus fingerprint is planned BEFORE the screening collect so the
    fixture can align the screening scope with it (the screening envelopes
    carry the corpus fingerprint of the corpus they were built from, exactly
    as a real pipeline would record). Decisions are NOT synthesized here:
    the trace joins the real collect-path screening_decisions artifacts.
    """
    from scholar_harness.contracts.canonical import corpus_snapshot_fingerprint

    if variant == "missing_decision":
        studies = [
            _study_row(
                STUDY_1,
                "REC-LIN-1",
                aliases=[LEGACY_ALIAS_1],
                doi=DOI_1,
                title=TITLE_1,
                year=2024,
            ),
            _study_row(
                STUDY_UNDECIDED,
                "REC-LIN-9",
                doi="10.0000/lineage9",
                title=TITLE_UNDECIDED,
                year=2026,
            ),
        ]
        record_to_study = {"REC-LIN-1": STUDY_1, "REC-LIN-9": STUDY_UNDECIDED}
        documents = [
            {
                "document_id": DOC_1,
                "study_id": STUDY_1,
                "source_hash": HASH_A,
                "content_status": "VALID",
                "extracted_path": "extracted/stu-lin-1.md",
                "extraction_method": "DETERMINISTIC_RULE",
            },
            {
                "document_id": DOC_UNDECIDED,
                "study_id": STUDY_UNDECIDED,
                "source_hash": HASH_B,
                "content_status": "VALID",
                "extracted_path": "extracted/stu-lin-9.md",
                "extraction_method": "DETERMINISTIC_RULE",
            },
        ]
        claim_studies = [STUDY_UNDECIDED]
        ev_study, ev_doc, ev_hash = STUDY_UNDECIDED, DOC_UNDECIDED, HASH_B
        token = f"[rag:v2:{WS_ID}:{STUDY_UNDECIDED}:CHK-LIN-9]"
    else:
        studies = [
            _study_row(
                STUDY_1,
                "REC-LIN-1",
                aliases=[LEGACY_ALIAS_1],
                doi=DOI_1,
                title=TITLE_1,
                year=2024,
            ),
            _study_row(
                STUDY_2,
                "REC-LIN-2",
                aliases=[LEGACY_ALIAS_2],
                doi="10.0000/lineage2",
                title=TITLE_2,
                year=2025,
            ),
        ]
        record_to_study = {"REC-LIN-1": STUDY_1, "REC-LIN-2": STUDY_2}
        doc_study = STUDY_UNKNOWN if variant == "unknown_study" else STUDY_1
        documents = [
            {
                "document_id": DOC_1,
                "study_id": doc_study,
                "source_hash": HASH_A,
                "content_status": "VALID",
                "extracted_path": "extracted/stu-lin-1.md",
                "extraction_method": "DETERMINISTIC_RULE",
            },
            {
                "document_id": DOC_2,
                "study_id": STUDY_2,
                "source_hash": HASH_B,
                "content_status": "VALID",
                "extracted_path": "extracted/stu-lin-2.md",
                "extraction_method": "DETERMINISTIC_RULE",
            },
        ]
        if variant == "unknown_study":
            claim_studies = [STUDY_UNKNOWN]
            ev_study, ev_doc = STUDY_UNKNOWN, DOC_1
            token = f"[rag:v2:{WS_ID}:{STUDY_UNKNOWN}:CHK-LIN-9]"
        else:
            claim_studies = [STUDY_1]
            ev_study = STUDY_1
            ev_doc = "DOC-LIN-999" if variant == "unlinked_document" else DOC_1
            token = TOKEN_1
        ev_hash = HASH_C if variant == "hash_mismatch" else HASH_A
    corpus_data = {
        "corpus_id": "COR-LIN-1",
        "identity_algorithm_version": "corpus-identity-v1",
        "studies": studies,
        "record_to_study": record_to_study,
    }
    corpus_fp = corpus_snapshot_fingerprint(corpus_data)
    ledger_data = {
        "claims": [
            {
                "claim_id": CLAIM_1,
                "claim_text": CLAIM_TEXT,
                "claim_kind": CLAIM_KIND,
                "study_ids": claim_studies,
                "evidence_ids": [EVIDENCE_1],
                "citation_tokens": [token],
                "generation_method": "DETERMINISTIC_RULE",
                "verification": {
                    "retrieval": "SOURCE_AVAILABLE",
                    "lexical_support": "SUPPORTED_VERBATIM",
                    "entailment": "NOT_ASSESSED",
                    "trust": "NOT_CHECKED",
                },
            }
        ],
        "evidence": [
            {
                "evidence_id": EVIDENCE_1,
                "study_id": ev_study,
                "document_id": ev_doc,
                "locator": LOCATOR_1,
                "quote": QUOTE_1,
                "extraction_method": "HUMAN",
                "source_hash": ev_hash,
            }
        ],
    }
    ledger_corpus_fp = HASH_F if variant == "generation_mismatch" else corpus_fp
    return corpus_data, corpus_fp, documents, ledger_data, ledger_corpus_fp


def write_lineage(ws: Path, protocol_fp: str, plan) -> dict[str, str]:
    """Validate the planned payloads through their frozen models and publish them."""
    from scholar_harness.contracts.canonical import (
        canonical_fingerprint,
        canonical_json_bytes,
    )
    from scholar_harness.contracts.models import (
        ClaimEvidenceLedger,
        CorpusSnapshotArtifact,
        DocumentManifestArtifact,
    )

    corpus_data, corpus_fp, documents, ledger_data, ledger_corpus_fp = plan
    payloads = {
        "corpus_snapshot": _envelope(
            artifact_type="corpus_snapshot",
            artifact_id="ART-LIN-CORPUS-1",
            protocol_fp=protocol_fp,
            corpus_fp=corpus_fp,
            data=corpus_data,
            created_at="2026-10-14T00:00:01+00:00",
        ),
        "document_manifest": _envelope(
            artifact_type="document_manifest",
            artifact_id="ART-LIN-DOCS-1",
            protocol_fp=protocol_fp,
            corpus_fp=corpus_fp,
            data={"documents": documents},
            created_at="2026-10-14T00:00:02+00:00",
        ),
        "claims_ledger": _envelope(
            artifact_type="claims_ledger",
            artifact_id="ART-LIN-LEDGER-1",
            protocol_fp=protocol_fp,
            corpus_fp=ledger_corpus_fp,
            data=ledger_data,
            created_at="2026-10-14T00:00:04+00:00",
        ),
    }
    # Frozen-model self-check: a fixture that fails its schema never reaches disk.
    CorpusSnapshotArtifact.model_validate(payloads["corpus_snapshot"])
    DocumentManifestArtifact.model_validate(payloads["document_manifest"])
    ClaimEvidenceLedger.model_validate(payloads["claims_ledger"])

    registry_path = ws / "audit" / "artifact_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    ids: dict[str, str] = {}
    for position, (artifact_type, payload) in enumerate(payloads.items()):
        artifact_id = payload["artifact_id"]
        rel = f"artifacts/{artifact_type}/{artifact_id}.json"
        dest = ws / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(canonical_json_bytes(payload) + b"\n")
        registry["artifacts"][artifact_id] = {
            "artifact_type": artifact_type,
            "path": rel,
            "sha256": canonical_fingerprint(payload),
            "accepted_at": f"2026-10-14T00:00:0{5 + position}+00:00",
            "run_id": RUN_ID,
            "producer": {
                "package": "scholar-harness",
                "version": "1.0.0",
                "commit": "test",
            },
        }
        ids[artifact_type] = artifact_id
    registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n")
    return ids


def align_screening_scope(ws: Path, corpus_fp: str) -> None:
    """Record the planned corpus fingerprint on the screening batch envelopes.

    A real pipeline builds its batches from an accepted corpus, so the batch
    envelopes carry that corpus fingerprint into the collect scope. The HCM-06
    builder carries a dummy instead; rewriting it here (with the registry
    hashes recomputed, never hand-edited) emulates the real coherence before
    the collect runs.
    """
    from scholar_harness.contracts.canonical import canonical_fingerprint

    registry_path = ws / "audit" / "artifact_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    for artifact_id, entry in registry["artifacts"].items():
        if entry.get("artifact_type") != "screening_batch":
            continue
        envelope_path = ws / entry["path"]
        envelope = json.loads(envelope_path.read_text(encoding="utf-8"))
        envelope["corpus_fingerprint"] = corpus_fp
        envelope["data"]["binding"]["corpus_fingerprint"] = corpus_fp
        envelope_path.write_text(
            json.dumps(envelope, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        entry["sha256"] = canonical_fingerprint(envelope)
    registry_path.write_text(json.dumps(registry, indent=2, sort_keys=True) + "\n")


def add_lineage(ws: Path, *, variant: str = "complete") -> dict[str, str]:
    """Add lineage artifacts to a workspace that is already at CURRENT generation.

    Used for the non-collect variants (legacy/stale workspaces): the screening
    scope keeps its own fingerprint and the lineage triple stands alone.
    """
    protocol_fp = _hcm06._protocol_fingerprint()
    plan = plan_lineage(protocol_fp, variant)
    return write_lineage(ws, protocol_fp, plan)


def make_current_ws(tmp, *, variant: str = "complete") -> Path:
    """Screening workspace at CURRENT generation with lineage artifacts.

    The lineage corpus is planned first so the screening scope can be
    aligned with it before the collect runs; one triple then spans the
    screening publication and the lineage artifacts.
    """
    ws = _hcm06._make_ws(tmp, with_decisions=True)
    protocol_fp = _hcm06._protocol_fingerprint()
    plan = plan_lineage(protocol_fp, variant)
    _, corpus_fp, _, _, _ = plan
    align_screening_scope(ws, corpus_fp)
    _hcm06._collect_current(ws)
    write_lineage(ws, protocol_fp, plan)
    return ws


def _snapshot(ws: Path) -> dict[str, str]:
    out = {}
    for p in sorted(ws.rglob("*")):
        if p.is_file() and ".harness-console" not in p.parts:
            rel = p.relative_to(ws).as_posix()
            out[rel] = (
                f"{p.stat().st_mtime_ns}:{hashlib.sha256(p.read_bytes()).hexdigest()}"
            )
    return out


# ---------------------------------------------------------------------------
# UI05-01: complete trace renders end to end
# ---------------------------------------------------------------------------


def test_lineage_complete_trace(tmp_path):
    ws = make_current_ws(tmp_path)
    client = TestClient(create_app(ws))
    r = client.get(f"/api/v1/ui/lineage?claim_id={CLAIM_1}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["shape"] == "ui07.lineage-trace-v1"
    assert body["complete"] is True
    assert body["selector"] == {"claim_id": CLAIM_1}
    assert body["missing"] == []
    assert len(body["claims"]) == 1
    claim = body["claims"][0]
    assert claim["claim_id"] == CLAIM_1
    assert claim["claim_text"] == CLAIM_TEXT
    assert claim["claim_kind"] == CLAIM_KIND
    assert claim["study_ids"] == [STUDY_1]
    assert claim["evidence_ids"] == [EVIDENCE_1]
    assert claim["chunk_ids"] == [CHUNK_1]
    assert claim["citation_tokens"] == [TOKEN_1]
    assert claim["verification"]["retrieval"] == "SOURCE_AVAILABLE"
    assert claim["verification"]["lexical_support"] == "SUPPORTED_VERBATIM"
    assert len(claim["legs"]) == 1
    leg = claim["legs"][0]
    assert leg["refusal"] is None
    assert leg["evidence"]["quote"] == QUOTE_1
    assert leg["evidence"]["locator"] == LOCATOR_1
    assert leg["evidence"]["evidence_id"] == EVIDENCE_1
    assert leg["chunk_ids"] == [CHUNK_1]
    assert leg["document"]["document_id"] == DOC_1
    assert leg["document"]["content_status"] == "VALID"
    assert leg["study"]["study_id"] == STUDY_1
    assert leg["study"]["title"] == TITLE_1
    assert DOI_1 in leg["study"]["external_ids"]["doi"]
    assert leg["decision"]["decision"] == "INCLUDE"
    assert leg["decision"]["reason"] == DECISION_REASON_1
    # The publication status travels verbatim beside the trace (never disagrees).
    publication = client.get("/api/v1/ui/publication-status").json()
    assert publication["status"] == "CURRENT"
    assert body["publication"] == publication


def test_lineage_chunk_selector_resolves(tmp_path):
    ws = make_current_ws(tmp_path)
    client = TestClient(create_app(ws))
    r = client.get(f"/api/v1/ui/lineage?chunk_id={CHUNK_1}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["complete"] is True
    assert body["selector"] == {"chunk_id": CHUNK_1}
    assert [c["claim_id"] for c in body["claims"]] == [CLAIM_1]
    assert body["claims"][0]["legs"][0]["evidence"]["quote"] == QUOTE_1


def test_lineage_alias_decision_resolution(tmp_path):
    """Mixed identity eras: the complete trace itself joins a canonical STU-
    study to a decision recorded under its legacy SCI- alias through the
    corpus-recorded alias, never by guessing."""
    ws = make_current_ws(tmp_path)
    client = TestClient(create_app(ws))
    body = client.get(f"/api/v1/ui/lineage?claim_id={CLAIM_1}").json()
    assert body["complete"] is True
    leg = body["claims"][0]["legs"][0]
    assert leg["study"]["study_id"] == STUDY_1
    assert LEGACY_ALIAS_1 in leg["study"]["alias_ids"]
    assert leg["decision"]["study_id"] == LEGACY_ALIAS_1
    assert leg["decision"]["decision"] == "INCLUDE"
    assert leg["decision"]["reason"] == DECISION_REASON_1


# ---------------------------------------------------------------------------
# UI05-02: each broken-link type renders its typed refusal state
# ---------------------------------------------------------------------------


def test_lineage_unknown_claim_refused(tmp_path):
    ws = make_current_ws(tmp_path)
    client = TestClient(create_app(ws))
    r = client.get("/api/v1/ui/lineage?claim_id=CLM-LIN-999")
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "CLAIM_MISSING"


def test_lineage_unknown_chunk_refused(tmp_path):
    ws = make_current_ws(tmp_path)
    client = TestClient(create_app(ws))
    r = client.get("/api/v1/ui/lineage?chunk_id=CHK-LIN-999")
    assert r.status_code == 404
    body = r.json()["detail"]
    assert body["code"] == "CHUNK_MISSING"
    assert body["message"]


def test_lineage_unlinked_document_refusal(tmp_path):
    ws = make_current_ws(tmp_path, variant="unlinked_document")
    client = TestClient(create_app(ws))
    r = client.get(f"/api/v1/ui/lineage?claim_id={CLAIM_1}")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["complete"] is False
    leg = body["claims"][0]["legs"][0]
    assert leg["document"] is None
    assert leg["study"] is None
    assert leg["decision"] is None
    assert leg["refusal"]["code"] == "UNLINKED_DOCUMENT"
    assert leg["evidence"]["quote"] == QUOTE_1  # served bytes stop at the break


def test_lineage_unknown_study_refusal(tmp_path):
    ws = make_current_ws(tmp_path, variant="unknown_study")
    client = TestClient(create_app(ws))
    body = client.get(f"/api/v1/ui/lineage?claim_id={CLAIM_1}").json()
    assert body["complete"] is False
    leg = body["claims"][0]["legs"][0]
    assert leg["document"]["document_id"] == DOC_1
    assert leg["study"] is None
    assert leg["decision"] is None
    assert leg["refusal"]["code"] == "UNKNOWN_STUDY"


def test_lineage_missing_decision_refusal(tmp_path):
    ws = make_current_ws(tmp_path, variant="missing_decision")
    client = TestClient(create_app(ws))
    body = client.get(f"/api/v1/ui/lineage?claim_id={CLAIM_1}").json()
    assert body["complete"] is False
    leg = body["claims"][0]["legs"][0]
    assert leg["study"]["study_id"] == STUDY_UNDECIDED
    assert leg["decision"] is None
    assert leg["refusal"]["code"] == "MISSING_DECISION"


def test_lineage_source_hash_mismatch_refuses(tmp_path):
    ws = make_current_ws(tmp_path, variant="hash_mismatch")
    client = TestClient(create_app(ws))
    body = client.get(f"/api/v1/ui/lineage?claim_id={CLAIM_1}").json()
    assert body["complete"] is False
    assert body["claims"][0]["legs"][0]["refusal"]["code"] == "UNLINKED_DOCUMENT"


# ---------------------------------------------------------------------------
# Entry, identity, and scope discipline
# ---------------------------------------------------------------------------


def test_lineage_selector_rules(tmp_path):
    ws = make_current_ws(tmp_path)
    client = TestClient(create_app(ws))
    r = client.get("/api/v1/ui/lineage")
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "MISSING_SELECTOR"
    r = client.get(f"/api/v1/ui/lineage?claim_id={CLAIM_1}&chunk_id={CHUNK_1}")
    assert r.status_code == 400
    assert r.json()["detail"]["code"] == "CONFLICTING_SELECTOR"


def test_lineage_caller_identity_refused(tmp_path):
    ws = make_current_ws(tmp_path)
    client = TestClient(create_app(ws))
    r = client.get(f"/api/v1/ui/lineage?claim_id={CLAIM_1}&workspace_id={WS_ID}")
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "CALLER_IDENTITY_REFUSED"
    r = client.get(f"/api/v1/ui/lineage?chunk_id={CHUNK_1}&run_id={RUN_ID}")
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "CALLER_IDENTITY_REFUSED"


def test_lineage_not_prepared_without_ledger(tmp_path):
    ws = _hcm06._make_ws(tmp_path, with_decisions=True)
    _hcm06._collect_current(ws)
    client = TestClient(create_app(ws))
    r = client.get(f"/api/v1/ui/lineage?claim_id={CLAIM_1}")
    assert r.status_code == 404
    assert r.json()["detail"]["code"] == "LINEAGE_NOT_PREPARED"


def test_lineage_generation_mismatch_refused(tmp_path):
    ws = make_current_ws(tmp_path, variant="generation_mismatch")
    client = TestClient(create_app(ws))
    r = client.get(f"/api/v1/ui/lineage?claim_id={CLAIM_1}")
    assert r.status_code == 409
    assert r.json()["detail"]["code"] == "LINEAGE_GENERATION_MISMATCH"


# ---------------------------------------------------------------------------
# UI05-03: mechanical no-invention check on the served bytes
# ---------------------------------------------------------------------------


def test_lineage_serves_stored_bytes_only(tmp_path):
    ws = make_current_ws(tmp_path)
    client = TestClient(create_app(ws))
    body = client.get(f"/api/v1/ui/lineage?claim_id={CLAIM_1}").json()

    stored: set[str] = set()

    def _collect(value):
        if isinstance(value, str):
            stored.add(value)
        elif isinstance(value, list):
            for item in value:
                _collect(item)
        elif isinstance(value, dict):
            for item in value.values():
                _collect(item)

    for artifact_type in (
        "claims_ledger",
        "document_manifest",
        "corpus_snapshot",
        "screening_decisions",
    ):
        for entry in json.loads(
            (ws / "audit" / "artifact_registry.json").read_text(encoding="utf-8")
        )["artifacts"].values():
            if entry["artifact_type"] == artifact_type:
                _collect(json.loads((ws / entry["path"]).read_text(encoding="utf-8")))
    # The publication status object is served verbatim beside the trace.
    _collect(client.get("/api/v1/ui/publication-status").json())

    served: list[str] = []
    claim = body["claims"][0]
    leg = claim["legs"][0]
    served += [
        claim["claim_id"],
        claim["claim_text"],
        claim["claim_kind"],
        claim["citation_tokens"][0],
        leg["evidence"]["evidence_id"],
        leg["evidence"]["quote"],
        leg["evidence"]["locator"],
        leg["evidence"]["study_id"],
        leg["evidence"]["document_id"],
        leg["evidence"]["source_hash"],
        leg["document"]["document_id"],
        leg["document"]["study_id"],
        leg["study"]["study_id"],
        leg["study"]["title"],
        leg["study"]["external_ids"]["doi"][0],
        leg["decision"]["study_id"],
        leg["decision"]["decision"],
        leg["decision"]["reason"],
    ]
    assert served
    for value in served:
        assert value in stored, f"served value absent from stored payloads: {value!r}"
    # Parsed chunk segments are slices of their stored citation tokens,
    # never standalone values: containment, not membership.
    for chunk in claim["chunk_ids"]:
        assert any(chunk in token for token in claim["citation_tokens"]), (
            f"chunk id outside its stored token: {chunk!r}"
        )


def _refusal_texts(payload: dict) -> list[str]:
    texts = []
    for claim in payload.get("claims", []):
        for leg in claim.get("legs", []):
            refusal = leg.get("refusal")
            if refusal:
                texts += [refusal.get("code", ""), refusal.get("message", "")]
    return texts


def test_lineage_never_claims_entailment(tmp_path):
    """A verbatim quote is served as a quote: server-composed refusal and
    error text never claims entailment, support, or proof. Stored bytes
    (quotes, reasons, the lexical axis) are served verbatim and are covered
    by the byte-equality test above instead."""
    ws = make_current_ws(tmp_path)
    client = TestClient(create_app(ws))
    texts: list[str] = []
    for variant in ("unlinked_document", "unknown_study", "missing_decision"):
        variant_ws = make_current_ws(tmp_path / variant, variant=variant)
        variant_client = TestClient(create_app(variant_ws))
        texts += _refusal_texts(
            variant_client.get(f"/api/v1/ui/lineage?claim_id={CLAIM_1}").json()
        )
    for route in (
        "/api/v1/ui/lineage",
        f"/api/v1/ui/lineage?claim_id={CLAIM_1}&chunk_id={CHUNK_1}",
        "/api/v1/ui/lineage?claim_id=CLM-LIN-999",
        "/api/v1/ui/lineage?chunk_id=CHK-LIN-999",
    ):
        detail = client.get(route).json()["detail"]
        texts += [detail.get("code", ""), detail.get("message", "")]
    assert texts
    for text in texts:
        lowered = text.lower()
        for verb in ("entail", "prove", "support"):
            assert verb not in lowered, f"entailment language in refusal: {text!r}"


# ---------------------------------------------------------------------------
# UI05-06: server hygiene — reads never mutate (TestClient only, no servers)
# ---------------------------------------------------------------------------


def test_lineage_reads_never_mutate(tmp_path):
    ws = make_current_ws(tmp_path)
    client = TestClient(create_app(ws))
    before = _snapshot(ws)
    battery = [
        f"/api/v1/ui/lineage?claim_id={CLAIM_1}",
        f"/api/v1/ui/lineage?chunk_id={CHUNK_1}",
        "/api/v1/ui/lineage?claim_id=CLM-LIN-999",
        "/api/v1/ui/lineage?chunk_id=CHK-LIN-999",
        "/api/v1/ui/lineage",
        f"/api/v1/ui/lineage?claim_id={CLAIM_1}&workspace_id={WS_ID}",
    ]
    for route in battery:
        client.get(route)
    assert before == _snapshot(ws)
    leftovers = [p for p in ws.rglob("*.tmp*")] + [
        ws / "literature" / "screening" / ".collect.lock"
    ]
    assert [p for p in leftovers if p.exists()] == []
    # This module spawns no console servers: every read above ran in process.
    # Spawned-server hygiene for the browser-driven live test is asserted in
    # apps/research-ui/tests/lineage.test.tsx (kill + port-free assert).


# ---------------------------------------------------------------------------
# UI05-07: publication-linked traces require CURRENT generation
# ---------------------------------------------------------------------------


def test_lineage_refuses_without_trace_bytes_when_not_current(tmp_path):
    stale_ws = _hcm06._make_ws(tmp_path / "stale", with_decisions=True)
    _hcm06._collect_current(stale_ws)
    add_lineage(stale_ws)
    inc = stale_ws / "literature" / "included.json"
    inc.write_text(inc.read_text(encoding="utf-8") + " ", encoding="utf-8")

    legacy_ws = _hcm06._make_ws(tmp_path / "legacy", with_decisions=True)
    add_lineage(legacy_ws)

    mismatch_ws = _hcm06._make_ws(tmp_path / "mismatch", with_decisions=True)
    _hcm06._collect_current(mismatch_ws)
    add_lineage(mismatch_ws)
    (mismatch_ws / "literature" / "screening" / "generation.json").unlink()

    cases = [
        (stale_ws, "GENERATION_STALE"),
        (legacy_ws, "GENERATION_LEGACY_UNVERIFIED"),
        (mismatch_ws, "GENERATION_MISMATCHED"),
    ]
    for ws, code in cases:
        client = TestClient(create_app(ws))
        r = client.get(f"/api/v1/ui/lineage?claim_id={CLAIM_1}")
        assert r.status_code == 409, code
        detail = r.json()["detail"]
        assert detail["code"] == code, code
        assert detail["message"]
        assert "claims" not in detail and "legs" not in json.dumps(detail), code


def _build_cli(outdir: str, variant: str) -> Path:
    """Build a served workspace on disk for the research-ui live test."""
    from pathlib import Path as _Path

    return make_current_ws(_Path(outdir), variant=variant)


if (
    __name__ == "__main__"
):  # `python tests/console/test_lineage_api.py build <dir> [variant]`
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    if action != "build" or len(sys.argv) < 3:
        raise SystemExit("usage: test_lineage_api.py build <outdir> [variant]")
    out = _build_cli(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "complete")
    print(str(out))
