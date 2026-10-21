"""T-TRUTH-COUNTS-01: harness counts must reconcile with physical artifacts.

The harness must never report "0 discovered" while records physically exist,
and must never report SUCCESS for an empty or degraded result.

The live counterexample is ``workspaces/uav-pilot-demo``: ``project.json``
declared ``discovered_papers: 0`` while ``calibration/`` physically held a
union of 2165 records and 2060 deduplicated records. The measured numbers
live in ``docs/architecture/workspace_stats_reconciliation.md`` -- this suite
is **hermetic and self-contained**: every fixture is generated in
``tmp_path`` and every expectation is derived from the fixture itself, so the
suite never depends on the current content of a live workspace.

Hermetic: no network, no kit calls, ``tmp_path`` workspaces only.
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pytest

from scholar_harness.doctor import Status, check_layout
from scholar_harness.orchestrator import ResearchOrchestrator
from scholar_harness.workspace import counts


# ---------------------------------------------------------------------------
# Fixtures (fully synthetic -- expectations are derived from the fixture)
# ---------------------------------------------------------------------------


def _write_manifest(ws: Path, stats: dict[str, int]) -> None:
    (ws / "project.json").write_text(
        json.dumps(
            {
                "project_id": ws.name,
                "title": "Reconciliation Fixture",
                "status": "active",
                "research_questions": [],
                "keywords": [],
                "stats": stats,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def _record_count(payload: object) -> int:
    """Count the records physically present in a corpus payload."""
    if isinstance(payload, list):
        return len(payload)
    if isinstance(payload, dict):
        for key in ("documents", "records", "items", "results", "data", "papers"):
            value = payload.get(key)
            if isinstance(value, list):
                return len(value)
    raise AssertionError(f"unreadable corpus payload: {type(payload).__name__}")


@pytest.fixture
def calibration_workspace(tmp_path: Path) -> tuple[Path, dict[str, int]]:
    """A workspace whose corpus lives OUTSIDE ``literature/``.

    The corpus is generated synthetically (never copied from a live
    workspace) and the expectations are derived from the generated files.
    """
    ws = tmp_path / "ws"
    corpus_dir = ws / "calibration"
    corpus_dir.mkdir(parents=True)
    expected: dict[str, int] = {}

    for name, size in (("raw_union.json", 40), ("deduped.json", 25)):
        payload = {
            "executed_query": "synthetic",
            "documents": [{"title": f"study {i}"} for i in range(size)],
        }
        (corpus_dir / name).write_text(json.dumps(payload), encoding="utf-8")
        expected[name] = _record_count(
            json.loads((corpus_dir / name).read_text(encoding="utf-8-sig"))
        )

    _write_manifest(ws, {"discovered_papers": 0, "verified_papers": 0})
    return ws, expected


def _corpus_workspace(tmp_path: Path, name: str = "ws") -> Path:
    """A minimal workspace with a manifest and a ``literature/`` directory."""
    ws = tmp_path / name
    (ws / "literature").mkdir(parents=True)
    _write_manifest(ws, {})
    return ws


# ---------------------------------------------------------------------------
# AC-1 / N-1: content-based, directory-agnostic counting
# ---------------------------------------------------------------------------


def test_non_canonical_corpus_directory_is_counted(calibration_workspace):
    """N-1 / AC-1: a corpus under ``calibration/`` is counted, never ignored."""
    ws, expected = calibration_workspace
    counted = counts.count_corpus(ws)

    assert counted.stats["discovered_papers"] == expected["raw_union.json"]
    assert counted.stats["deduped_papers"] == expected["deduped.json"]
    assert counted.status == "OK"
    assert counted.selected["discovered_papers"] == ["calibration/raw_union.json"]
    assert counted.headline > 0


def test_canonical_literature_paths_keep_working(tmp_path):
    """AC-9: the canonical ``literature/`` counting is unchanged."""
    ws = tmp_path / "ws"
    lit = ws / "literature"
    lit.mkdir(parents=True)
    (lit / "raw_search.json").write_text(
        json.dumps([{"title": f"p{i}"} for i in range(3)]), encoding="utf-8"
    )
    (lit / "deduped.json").write_text(json.dumps([{"title": "p0"}]), encoding="utf-8")
    _write_manifest(ws, {"discovered_papers": 3, "deduped_papers": 1})

    counted = counts.count_corpus(ws)
    assert counted.stats["discovered_papers"] == 3
    assert counted.stats["deduped_papers"] == 1
    assert counted.selected["discovered_papers"] == ["literature/raw_search.json"]


def test_canonical_artifact_wins_over_non_canonical(tmp_path):
    """AC-1/AC-9: canonical ``literature/`` output keeps priority."""
    ws = tmp_path / "ws"
    lit = ws / "literature"
    lit.mkdir(parents=True)
    (lit / "raw_search.json").write_text(json.dumps([{"t": 1}]), encoding="utf-8")
    cal = ws / "calibration"
    cal.mkdir()
    (cal / "raw_union.json").write_text(
        json.dumps({"documents": [{"t": i} for i in range(9)]}), encoding="utf-8"
    )

    counted = counts.count_corpus(ws)
    assert counted.stats["discovered_papers"] == 1
    assert counted.selected["discovered_papers"] == ["literature/raw_search.json"]


def test_provider_raw_files_are_summed_when_no_union_exists(tmp_path):
    """A per-provider harvest is physical evidence too."""
    ws = tmp_path / "ws"
    cal = ws / "calibration"
    cal.mkdir(parents=True)
    (cal / "raw_openalex.json").write_text(
        json.dumps({"documents": [{"t": i} for i in range(4)]}), encoding="utf-8"
    )
    (cal / "raw_crossref.json").write_text(
        json.dumps({"documents": [{"t": i} for i in range(6)]}), encoding="utf-8"
    )
    _write_manifest(ws, {})

    counted = counts.count_corpus(ws)
    assert counted.stats["discovered_papers"] == 10
    # The sources block is machine readable: one path per entry.
    assert counted.selected["discovered_papers"] == [
        "calibration/raw_crossref.json",
        "calibration/raw_openalex.json",
    ]


# ---------------------------------------------------------------------------
# B1: recognition is content-based -- an unknown name is never invisible
# ---------------------------------------------------------------------------


def test_corpus_token_artifact_is_mapped_to_discovered(tmp_path):
    """B1: a corpus artifact whose stem carries the ``corpus`` token is counted.

    The stem matches a *generic* role token, so the artifact is mapped to the
    discovered role (basis ``token:corpus``) -- the fixture name says what
    the test exercises.
    """
    ws = _corpus_workspace(tmp_path)
    (ws / "literature" / "corpus_snapshot.json").write_text(
        json.dumps({"documents": [{"t": i} for i in range(500)]}), encoding="utf-8"
    )
    _write_manifest(ws, {"discovered_papers": 0})

    counted = counts.count_corpus(ws)
    assert counted.stats["discovered_papers"] == 500
    assert "literature/corpus_snapshot.json" in counted.selected["discovered_papers"]
    artifact = next(
        a for a in counted.candidates if a.relpath.endswith("corpus_snapshot.json")
    )
    assert artifact.role_basis == "token:corpus"


def test_generic_papers_token_is_mapped_to_discovered(tmp_path):
    """B1: ``{"papers": [...]}`` is a record list and is counted.

    ``papers`` is a *generic* role token, so the artifact is mapped to the
    discovered role (basis ``token:papers``) -- it is never dropped and never
    silently counted as ``0``.
    """
    ws = _corpus_workspace(tmp_path)
    (ws / "literature" / "papers_export.json").write_text(
        json.dumps({"papers": [{"title": f"p{i}"} for i in range(7)]}),
        encoding="utf-8",
    )
    _write_manifest(ws, {"discovered_papers": 0})

    counted = counts.count_corpus(ws)
    artifact = counted.candidates[0]
    assert artifact.state == counts.STATE_COUNTED
    assert artifact.count == 7
    assert artifact.role_basis == "token:papers"
    assert counted.stats["discovered_papers"] == 7
    assert "7 records" not in counted.summary()  # it is a *counter*, not a stray
    assert counts.reconcile(ws, corpus=counted).status == "STALE"


def test_results_token_artifact_is_mapped_to_discovered(tmp_path):
    """B1: a ``results`` payload is a record list and is counted.

    The stem matches the generic ``results`` token, so the artifact is mapped
    to the discovered role (basis ``token:results``) -- the fixture name says
    what the test exercises.
    """
    ws = _corpus_workspace(tmp_path)
    (ws / "calibration").mkdir()
    (ws / "calibration" / "results_dump.json").write_text(
        json.dumps({"results": [{"t": i} for i in range(11)]}), encoding="utf-8"
    )
    _write_manifest(ws, {"discovered_papers": 0})

    counted = counts.count_corpus(ws)
    assert counted.stats["discovered_papers"] == 11
    artifact = next(
        a for a in counted.candidates if a.relpath.endswith("results_dump.json")
    )
    assert artifact.role_basis == "token:results"


def test_provider_stem_without_role_token_is_provider_evidence(tmp_path):
    """B1: a provider harvest named differently is still physical evidence."""
    ws = _corpus_workspace(tmp_path)
    (ws / "calibration").mkdir()
    (ws / "calibration" / "openalex_harvest.json").write_text(
        json.dumps({"documents": [{"t": i} for i in range(11)]}), encoding="utf-8"
    )
    _write_manifest(ws, {"discovered_papers": 0})

    counted = counts.count_corpus(ws)
    assert counted.stats["discovered_papers"] == 11
    artifact = next(
        a for a in counted.candidates if a.relpath.endswith("openalex_harvest.json")
    )
    assert artifact.role_basis == "provider:openalex"
    assert artifact.provider == "openalex"


def test_artifact_matching_no_token_and_no_provider_is_unclassified(tmp_path):
    """B1/A-F10: a stem with no role token and no provider is UNCLASSIFIED.

    The records are counted and reported -- never dropped -- but they are not
    represented by any declared counter, so the reconciliation is not a green
    PASS.
    """
    ws = _corpus_workspace(tmp_path)
    (ws / "literature" / "harvest_dump.json").write_text(
        json.dumps({"documents": [{"t": i} for i in range(500)]}), encoding="utf-8"
    )
    _write_manifest(ws, {"discovered_papers": 0})

    counted = counts.count_corpus(ws)
    artifact = counted.candidates[0]
    assert artifact.state == counts.STATE_COUNTED
    assert artifact.count == 500
    assert artifact.role is None
    assert artifact.role_basis == "unclassified"
    assert [a.relpath for a in counted.unclassified] == ["literature/harvest_dump.json"]
    assert counted.status == "UNCLASSIFIED"
    assert counts.reconcile(ws, corpus=counted).status == "UNCLASSIFIED"

    stats_check = next(r for r in check_layout(ws) if r.name == "project.json-stats")
    assert stats_check.status is Status.FAIL
    assert "harvest_dump.json" in stats_check.detail


def test_corpus_json_in_pdf_and_extracted_dirs_is_not_invisible(tmp_path):
    """B1/n2: ``pdfs/`` and ``extracted/`` are scanned, not skipped."""
    ws = tmp_path / "ws"
    for name in ("pdfs", "extracted"):
        (ws / name).mkdir(parents=True)
    (ws / "pdfs" / "corpus.json").write_text(
        json.dumps({"documents": [{"t": 1}, {"t": 2}]}), encoding="utf-8"
    )
    (ws / "extracted" / "corpus.json").write_text(
        json.dumps({"documents": [{"t": 1}]}), encoding="utf-8"
    )
    _write_manifest(ws, {"discovered_papers": 0})

    counted = counts.count_corpus(ws)
    # Both artifacts are inspected and counted (the selected one provides the
    # counter; the other stays visible as a candidate).
    assert counted.sources["discovered_papers"] == [
        "extracted/corpus.json",
        "pdfs/corpus.json",
    ]
    # The expectation is derived from the fixture: the artifact with the most
    # records wins the selection (2 records in ``pdfs/corpus.json``).
    assert counted.stats["discovered_papers"] == 2
    assert counted.selected["discovered_papers"] == ["pdfs/corpus.json"]
    assert counted.headline > 0


def test_truncated_corpus_artifact_is_a_named_state_not_zero(tmp_path):
    """B1: an unreadable artifact is UNREADABLE, never a silent 0."""
    ws = tmp_path / "ws"
    lit = ws / "literature"
    lit.mkdir(parents=True)
    (lit / "raw_search.json").write_text('[{"t": 1}, {"t": 2', encoding="utf-8")
    _write_manifest(ws, {"discovered_papers": 0})

    counted = counts.count_corpus(ws)
    artifact = next(
        a for a in counted.candidates if a.relpath.endswith("raw_search.json")
    )
    assert artifact.state == counts.STATE_UNREADABLE
    assert artifact.count is None
    assert "literature/raw_search.json" in counted.undetermined["discovered_papers"]
    assert counted.status == "UNRESOLVED"

    reconciliation = counts.reconcile(ws, corpus=counted)
    assert reconciliation.status == "UNRESOLVED"


def test_unclassified_record_bearing_artifact_is_reported_not_dropped(tmp_path):
    """B1: a record-bearing artifact with no known role is an UNCLASSIFIED
    contribution -- counted and reported, never silently ignored."""
    ws = tmp_path / "ws"
    lit = ws / "literature"
    lit.mkdir(parents=True)
    (lit / "mystery_dump.json").write_text(
        json.dumps({"documents": [{"t": i} for i in range(3)]}), encoding="utf-8"
    )
    _write_manifest(ws, {"discovered_papers": 0})

    counted = counts.count_corpus(ws)
    unclassified = counted.unclassified
    assert [a.relpath for a in unclassified] == ["literature/mystery_dump.json"]
    assert unclassified[0].count == 3
    assert counted.status == "UNCLASSIFIED"
    assert "unclassified" in counted.summary().lower()

    reconciliation = counts.reconcile(ws, corpus=counted)
    assert reconciliation.status == "UNCLASSIFIED"


def test_every_candidate_of_a_role_is_exposed(tmp_path):
    """B1: all candidates of a role stay visible (no hidden selection)."""
    ws = tmp_path / "ws"
    cal = ws / "calibration"
    cal.mkdir(parents=True)
    for name in ("raw_union.json", "raw_union_hydrated.json", "raw_openalex.json"):
        (cal / name).write_text(json.dumps({"documents": [{"t": 1}]}), encoding="utf-8")
    _write_manifest(ws, {})

    counted = counts.count_corpus(ws)
    assert counted.sources["discovered_papers"] == [
        "calibration/raw_openalex.json",
        "calibration/raw_union.json",
        "calibration/raw_union_hydrated.json",
    ]
    assert len(counted.selected["discovered_papers"]) == 1


def test_selection_prefers_the_most_records_and_ignores_mtime(tmp_path):
    """D-4: the selection rule is content-based -- mtime never decides.

    The fixture makes the *older* artifact the bigger one and the *newer*
    artifact the smaller one: the counter must follow the records (the
    reproducible, content-based evidence), never the filesystem timestamp.
    """
    ws = tmp_path / "ws"
    cal = ws / "calibration"
    cal.mkdir(parents=True)
    big = cal / "raw_union.json"
    small = cal / "raw_union_hydrated.json"
    big.write_text(
        json.dumps({"documents": [{"t": i} for i in range(100)]}), encoding="utf-8"
    )
    small.write_text(json.dumps({"documents": [{"t": 1}]}), encoding="utf-8")
    # The hydrated snapshot is the more recent artifact (currency) even
    # though it holds fewer records -- the timestamp must not decide.
    os.utime(big, (1_000_000, 1_000_000))
    os.utime(small, (2_000_000, 2_000_000))
    _write_manifest(ws, {})

    counted = counts.count_corpus(ws)
    assert counted.selected["discovered_papers"] == ["calibration/raw_union.json"]
    assert counted.stats["discovered_papers"] == 100


def test_summary_field_fallback_is_labelled(tmp_path):
    """B1/M3: the summary-field fallback exists but is named, not hidden."""
    ws = tmp_path / "ws"
    lit = ws / "literature"
    lit.mkdir(parents=True)
    (lit / "raw_search.json").write_text(
        json.dumps({"count": 12, "note": "no records here"}), encoding="utf-8"
    )
    _write_manifest(ws, {"discovered_papers": 12})

    counted = counts.count_corpus(ws)
    artifact = counted.candidates[0]
    assert artifact.state == counts.STATE_SUMMARY_ONLY
    assert artifact.count == 12
    assert "summary field" in artifact.detail


# ---------------------------------------------------------------------------
# A-F1/A-F2/A-F3: the payload shapes that used to be invisible
# ---------------------------------------------------------------------------


def test_nested_record_list_is_counted(tmp_path):
    """A-F2: a record list nested under a well-known key is COUNTED.

    ``{"data": {"documents": [...]}}`` used to be UNKNOWN_SHAPE, which did
    not block the reconciliation: 500 physical records were silently
    uncounted.
    """
    ws = _corpus_workspace(tmp_path)
    (ws / "literature" / "raw_union.json").write_text(
        json.dumps({"data": {"documents": [{"t": i} for i in range(500)]}}),
        encoding="utf-8",
    )

    counted = counts.count_corpus(ws)
    artifact = counted.candidates[0]
    assert artifact.state == counts.STATE_COUNTED
    assert artifact.count == 500
    assert counted.stats["discovered_papers"] == 500
    assert counted.status == "OK"


def test_ndjson_corpus_is_counted_line_wise(tmp_path):
    """A-F1: ``.jsonl``/``.ndjson`` corpora are swept and counted line-wise."""
    ws = _corpus_workspace(tmp_path)
    (ws / "literature" / "corpus.jsonl").write_text(
        "\n".join(json.dumps({"t": i}) for i in range(50)), encoding="utf-8"
    )
    (ws / "literature" / "second_corpus.ndjson").write_text(
        "\n".join(json.dumps({"t": i}) for i in range(3)) + "\n", encoding="utf-8"
    )

    counted = counts.count_corpus(ws)
    assert counted.stats["discovered_papers"] == 50
    assert "literature/corpus.jsonl" in counted.selected["discovered_papers"]
    assert counted.status == "OK"


def test_broken_ndjson_line_is_unreadable_not_a_silent_zero(tmp_path):
    """A-F1: a malformed NDJSON line is UNREADABLE, never a silent 0."""
    ws = _corpus_workspace(tmp_path)
    (ws / "literature" / "corpus.jsonl").write_text(
        json.dumps({"t": 1}) + "\nnot json\n", encoding="utf-8"
    )

    counted = counts.count_corpus(ws)
    artifact = counted.candidates[0]
    assert artifact.state == counts.STATE_UNREADABLE
    assert artifact.count is None
    assert counted.status == "UNRESOLVED"


def test_empty_record_list_with_a_declared_total_is_a_named_conflict(tmp_path):
    """A-F3: ``{"documents": [], "total": 9999}`` is not "0 records".

    The artifact declares 9999 records but carries none: the physical count
    is UNDETERMINED (a named CONFLICT state), never a silent ``0``.
    """
    ws = _corpus_workspace(tmp_path)
    (ws / "literature" / "raw_union.json").write_text(
        json.dumps({"documents": [], "total": 9999}), encoding="utf-8"
    )

    counted = counts.count_corpus(ws)
    artifact = counted.candidates[0]
    assert artifact.state == counts.STATE_CONFLICT
    assert artifact.count is None
    assert "9999" in artifact.detail
    assert counted.undetermined["discovered_papers"] == ["literature/raw_union.json"]
    assert counted.status == "UNRESOLVED"

    stats_check = next(r for r in check_layout(ws) if r.name == "project.json-stats")
    assert stats_check.status is Status.FAIL
    assert "NOT RECONCILED" in stats_check.detail


def test_summary_vs_list_conflict_is_surfaced(tmp_path):
    """A-F3: a summary/list disagreement is surfaced, not silently dropped."""
    ws = _corpus_workspace(tmp_path)
    (ws / "literature" / "raw_union.json").write_text(
        json.dumps({"documents": [{"t": 1}, {"t": 2}, {"t": 3}], "total": 13096}),
        encoding="utf-8",
    )

    counted = counts.count_corpus(ws)
    artifact = counted.candidates[0]
    assert artifact.state == counts.STATE_CONFLICT
    assert artifact.count == 3  # the physical list is the truth
    assert "13096" in artifact.detail
    assert [a.relpath for a in counted.conflicts] == ["literature/raw_union.json"]

    conflicts_check = next(r for r in check_layout(ws) if r.name == "corpus-conflicts")
    assert conflicts_check.status is Status.WARN
    assert "13096" in conflicts_check.detail


# ---------------------------------------------------------------------------
# A-F4 / D-4: role token precedence (never a bare substring match)
# ---------------------------------------------------------------------------


def test_role_specific_tokens_outrank_the_generic_papers_token(tmp_path):
    """A-F4: ``<role>_papers.json`` maps to its role, never to discovered.

    Before the fix all four files mapped to ``discovered_papers`` (four
    silent zeros plus cross-role double counting).
    """
    ws = _corpus_workspace(tmp_path)
    expected = {
        "deduped_papers.json": ("deduped_papers", 2),
        "included_papers.json": ("included_papers", 1),
        "excluded_papers.json": ("excluded_papers", 3),
        "verified_papers.json": ("verified_papers", 4),
    }
    for name, (_role, size) in expected.items():
        (ws / "literature" / name).write_text(
            json.dumps({"documents": [{"t": i} for i in range(size)]}), encoding="utf-8"
        )

    counted = counts.count_corpus(ws)
    for name, (role, size) in expected.items():
        assert counted.stats[role] == size, name
        assert counted.selected[role] == [f"literature/{name}"], name
    # Nothing leaked into the discovered counter.
    assert counted.stats["discovered_papers"] == 0
    assert counted.selected["discovered_papers"] == []
    assert counted.status == "OK"


def test_token_matching_is_not_a_bare_substring(tmp_path):
    """D-4: a token matches whole words, never a substring of a word."""
    ws = _corpus_workspace(tmp_path)
    # "includ" is a substring of "included" but not a word: the stem carries
    # no role token at all.
    (ws / "literature" / "includ_dump.json").write_text(
        json.dumps({"documents": [{"t": 1}]}), encoding="utf-8"
    )

    counted = counts.count_corpus(ws)
    artifact = counted.candidates[0]
    assert artifact.role is None
    assert artifact.role_basis == "unclassified"


# ---------------------------------------------------------------------------
# A-F7: provider evidence overlap is a stated limitation, surfaced by the doctor
# ---------------------------------------------------------------------------


def test_provider_overlap_is_flagged_and_surfaced(tmp_path):
    """A-F7: two providers holding the same 10 documents are counted as 20.

    That over-count is a *stated limitation* of summing provider evidence:
    the counter carries the overlap flag and the doctor surfaces it.
    """
    ws = _corpus_workspace(tmp_path)
    (ws / "calibration").mkdir()
    for provider in ("openalex", "crossref"):
        (ws / "calibration" / f"raw_{provider}.json").write_text(
            json.dumps({"documents": [{"t": i} for i in range(10)]}), encoding="utf-8"
        )

    counted = counts.count_corpus(ws)
    assert counted.stats["discovered_papers"] == 20
    assert counted.provider_evidence == ("crossref", "openalex")
    assert counted.provider_overlap is True

    overlap_check = next(
        r for r in check_layout(ws) if r.name == "provider-evidence-overlap"
    )
    assert overlap_check.status is Status.WARN
    assert "overlap" in overlap_check.detail.lower()


def test_corpus_under_two_paths_is_not_double_counted(tmp_path):
    """A-F11: the same corpus under two paths is counted once."""
    ws = _corpus_workspace(tmp_path)
    (ws / "calibration").mkdir()
    payload = json.dumps({"documents": [{"t": i} for i in range(5)]})
    (ws / "literature" / "raw_search.json").write_text(payload, encoding="utf-8")
    (ws / "calibration" / "raw_union.json").write_text(payload, encoding="utf-8")

    counted = counts.count_corpus(ws)
    assert counted.stats["discovered_papers"] == 5
    assert counted.selected["discovered_papers"] == ["literature/raw_search.json"]


# ---------------------------------------------------------------------------
# A-F6 / A-F13: the exclusions are explicit paths, never prefix guesses
# ---------------------------------------------------------------------------


def test_harness_derived_artifacts_are_excluded_by_named_path(tmp_path):
    """A-F6: the harness' own derived artifacts are excluded by name."""
    ws = _corpus_workspace(tmp_path)
    (ws / "literature" / "extraction" / "merged").mkdir(parents=True)
    (ws / "literature" / "extraction" / "merged" / "records.json").write_text(
        json.dumps({"documents": [{"t": i} for i in range(99)]}), encoding="utf-8"
    )
    (ws / "literature" / "screening").mkdir()
    (ws / "literature" / "screening" / "batch_0001.json").write_text(
        json.dumps({"records": [{"t": i} for i in range(50)]}), encoding="utf-8"
    )
    (ws / "literature" / "graph.json").write_text(
        json.dumps({"nodes": [{"t": i} for i in range(7)]}), encoding="utf-8"
    )
    (ws / "literature" / "raw_union.json").write_text(
        json.dumps({"documents": [{"t": 1}]}), encoding="utf-8"
    )

    counted = counts.count_corpus(ws)
    assert counted.stats["discovered_papers"] == 1
    assert counted.selected["discovered_papers"] == ["literature/raw_union.json"]
    assert [a.relpath for a in counted.candidates] == ["literature/raw_union.json"]


def test_a_real_directory_named_screening_corpus_is_not_skipped(tmp_path):
    """A-F6: the exclusion is a named path, not a ``screening*`` prefix guess."""
    ws = _corpus_workspace(tmp_path)
    (ws / "screening_corpus").mkdir()
    (ws / "screening_corpus" / "corpus.json").write_text(
        json.dumps({"documents": [{"t": i} for i in range(6)]}), encoding="utf-8"
    )

    counted = counts.count_corpus(ws)
    assert counted.stats["discovered_papers"] == 6
    assert counted.selected["discovered_papers"] == ["screening_corpus/corpus.json"]


def test_dot_paths_are_excluded_symmetrically(tmp_path):
    """A-F13: the dot exclusion covers the file name too."""
    ws = _corpus_workspace(tmp_path)
    (ws / "literature" / ".hidden_corpus.json").write_text(
        json.dumps({"documents": [{"t": i} for i in range(9)]}), encoding="utf-8"
    )
    (ws / "literature" / "raw_union.json").write_text(
        json.dumps({"documents": [{"t": 1}]}), encoding="utf-8"
    )

    counted = counts.count_corpus(ws)
    assert counted.stats["discovered_papers"] == 1
    assert [a.relpath for a in counted.candidates] == ["literature/raw_union.json"]


# ---------------------------------------------------------------------------
# D-1: severity follows the impact
# ---------------------------------------------------------------------------


def test_role_less_malformed_artifact_does_not_poison_the_counters(tmp_path):
    """A-F12/D-1: an unreadable artifact that maps to no role is a WARN.

    The counted numbers stay the primary truth: the workspace reports the
    exact counts and names the broken file on its own line.
    """
    ws = _corpus_workspace(tmp_path)
    (ws / "calibration_v03").mkdir()
    (ws / "calibration_v03" / "v03_scr1_provider_uniqueness.json").write_text(
        "}\\n", encoding="utf-8"
    )
    (ws / "calibration").mkdir()
    (ws / "calibration" / "raw_union.json").write_text(
        json.dumps({"documents": [{"t": i} for i in range(40)]}), encoding="utf-8"
    )
    (ws / "calibration" / "deduped.json").write_text(
        json.dumps({"documents": [{"t": i} for i in range(30)]}), encoding="utf-8"
    )

    counted = counts.count_corpus(ws)
    assert counted.status == "OK"
    assert counted.undetermined == {}
    assert counted.stats["discovered_papers"] == 40
    assert counted.stats["deduped_papers"] == 30
    assert "UNDETERMINED" not in counted.summary()

    results = check_layout(ws)
    corpus_check = next(r for r in results if r.name == "corpus-counts")
    assert corpus_check.status is Status.PASS
    assert "discovered_papers=40" in corpus_check.detail
    assert "deduped_papers=30" in corpus_check.detail

    broken_check = next(r for r in results if r.name == "corpus-unreadable")
    assert broken_check.status is Status.WARN
    assert "v03_scr1_provider_uniqueness.json" in broken_check.detail
    assert "maps to no counter" in broken_check.detail


def test_uninterpretable_role_artifact_blocks_the_reconciliation(tmp_path):
    """A-F11: an unexpected shape that maps to a role blocks the verdict.

    Before the fix an UNKNOWN_SHAPE artifact did not block anything, so the
    workspace reported OK while its corpus was uncounted.
    """
    ws = _corpus_workspace(tmp_path)
    (ws / "literature" / "raw_search.json").write_text(
        json.dumps({"unexpected": "shape"}), encoding="utf-8"
    )

    counted = counts.count_corpus(ws)
    assert counted.status == "UNRESOLVED"
    assert counted.undetermined["discovered_papers"] == ["literature/raw_search.json"]

    stats_check = next(r for r in check_layout(ws) if r.name == "project.json-stats")
    assert stats_check.status is Status.FAIL
    assert "NOT RECONCILED" in stats_check.detail
    assert "raw_search.json" in stats_check.detail


# ---------------------------------------------------------------------------
# AC-2 / N-3 / N-4 / N-5: declared vs actual
# ---------------------------------------------------------------------------


def test_workspace_with_corpus_never_reports_zero(calibration_workspace):
    """AC-2: a workspace holding N physical records reports N, never 0."""
    ws, expected = calibration_workspace
    counted = counts.count_corpus(ws)
    assert counted.stats["discovered_papers"] == expected["raw_union.json"]
    assert counted.stats["discovered_papers"] != 0


def test_under_reporting_summary_is_detected_and_repaired(calibration_workspace):
    """N-3: declared 0 vs actual N -> detected, and ``sync`` repairs it."""
    ws, expected = calibration_workspace
    reconciliation = counts.reconcile(ws)
    assert reconciliation.status == "STALE"
    mismatch = {m.key: m for m in reconciliation.mismatches}
    assert mismatch["discovered_papers"].declared == 0
    assert mismatch["discovered_papers"].actual == expected["raw_union.json"]

    result = ResearchOrchestrator(ws).sync_state()
    assert result["stats"]["discovered_papers"] == expected["raw_union.json"]

    manifest = json.loads((ws / "project.json").read_text(encoding="utf-8"))
    assert manifest["stats"]["discovered_papers"] == expected["raw_union.json"]
    assert manifest["stats"]["deduped_papers"] == expected["deduped.json"]
    # The repaired summary is now consistent.
    assert counts.reconcile(ws).status == "OK"


def test_over_reporting_summary_is_detected(tmp_path):
    """N-4: declared 9999 vs actual N is a mismatch too."""
    ws = tmp_path / "ws"
    lit = ws / "literature"
    lit.mkdir(parents=True)
    (lit / "raw_search.json").write_text(
        json.dumps([{"t": 1}, {"t": 2}]), encoding="utf-8"
    )
    _write_manifest(ws, {"discovered_papers": 9999})

    reconciliation = counts.reconcile(ws)
    assert reconciliation.status == "STALE"
    mismatch = {m.key: m for m in reconciliation.mismatches}
    assert mismatch["discovered_papers"].declared == 9999
    assert mismatch["discovered_papers"].actual == 2

    ResearchOrchestrator(ws).sync_state()
    manifest = json.loads((ws / "project.json").read_text(encoding="utf-8"))
    assert manifest["stats"]["discovered_papers"] == 2


def test_empty_workspace_reports_no_corpus_explicitly(tmp_path):
    """D-2: no corpus at all is a VERIFIABLE state that reconciles.

    ``NO_CORPUS`` means "this workspace holds no corpus artifact at all" --
    it reconciles against a declared ``0`` (PASS). It is NOT the same as
    "nothing was counted" (which was the old, conflated state).
    """
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_manifest(ws, {"discovered_papers": 0})

    reconciliation = counts.reconcile(ws)
    assert reconciliation.status == "NO_CORPUS"
    assert reconciliation.actual["discovered_papers"] == 0
    assert reconciliation.consistent is True
    assert "no corpus artifact identified" in reconciliation.counts.summary().lower()

    results = check_layout(ws)
    corpus = next(r for r in results if r.name == "corpus-counts")
    assert corpus.status is Status.PASS
    assert "no corpus artifact" in corpus.detail.lower()

    stats = next(r for r in results if r.name == "project.json-stats")
    assert stats.status is Status.PASS
    assert "reconcile against the physical state" in stats.detail


def test_deleted_corpus_drops_to_zero_without_stale_carry_over(calibration_workspace):
    """N-5: a deleted corpus directory drops the counts to 0."""
    ws, expected = calibration_workspace
    ResearchOrchestrator(ws).sync_state()
    manifest = json.loads((ws / "project.json").read_text(encoding="utf-8"))
    assert manifest["stats"]["discovered_papers"] == expected["raw_union.json"]

    shutil.rmtree(ws / "calibration")

    result = ResearchOrchestrator(ws).sync_state()
    assert result["stats"]["discovered_papers"] == 0
    manifest = json.loads((ws / "project.json").read_text(encoding="utf-8"))
    assert manifest["stats"]["discovered_papers"] == 0
    assert manifest["stats"]["deduped_papers"] == 0
    assert counts.reconcile(ws).status == "NO_CORPUS"


def test_doctor_reports_stale_summary_as_fail(calibration_workspace):
    """AC-3: a stale summary is a FAIL, not a WARN."""
    ws, expected = calibration_workspace
    results = check_layout(ws)
    stats_check = next(r for r in results if r.name == "project.json-stats")
    assert stats_check.status is Status.FAIL
    assert f"actual={expected['raw_union.json']}" in stats_check.detail

    corpus_check = next(r for r in results if r.name == "corpus-counts")
    assert corpus_check.status is Status.PASS
    assert str(expected["raw_union.json"]) in corpus_check.detail


def test_doctor_reports_over_reporting_as_fail(tmp_path):
    """N-4 (doctor side): an over-reported summary is detected too."""
    ws = tmp_path / "ws"
    lit = ws / "literature"
    lit.mkdir(parents=True)
    (lit / "raw_search.json").write_text(json.dumps([{"t": 1}]), encoding="utf-8")
    _write_manifest(ws, {"discovered_papers": 9999})

    stats_check = next(r for r in check_layout(ws) if r.name == "project.json-stats")
    assert stats_check.status is Status.FAIL
    assert "declared=9999" in stats_check.detail


# ---------------------------------------------------------------------------
# B2 / D-2: the doctor may never report PASS for a reconciliation never performed
# ---------------------------------------------------------------------------


def test_corpus_free_workspace_reconciles_against_its_declared_zero(tmp_path):
    """D-2: an empty workspace RECONCILES against the declared 0.

    The old state ("NOT RECONCILED -- NOTHING WAS COUNTED") conflated "the
    workspace holds no corpus" with "the reconciliation never happened"; the
    two are now separate, verifiable states.
    """
    ws = tmp_path / "ws"
    ws.mkdir()
    _write_manifest(ws, {"discovered_papers": 0})

    results = check_layout(ws)
    stats_check = next(r for r in results if r.name == "project.json-stats")
    assert stats_check.status is Status.PASS
    assert "no corpus artifact in this workspace" in stats_check.detail
    assert "reconcile against the physical state" in stats_check.detail


def test_doctor_never_passes_for_an_unrecognised_corpus_name(tmp_path):
    """B2: a corpus artifact the harness cannot classify is not a PASS."""
    ws = tmp_path / "ws"
    lit = ws / "literature"
    lit.mkdir(parents=True)
    (lit / "mystery_dump.json").write_text(
        json.dumps({"documents": [{"t": i} for i in range(4)]}), encoding="utf-8"
    )
    _write_manifest(ws, {"discovered_papers": 0})

    results = check_layout(ws)
    stats_check = next(r for r in results if r.name == "project.json-stats")
    assert stats_check.status is not Status.PASS
    assert stats_check.status is Status.FAIL
    assert "NOT RECONCILED" in stats_check.detail
    assert "mystery_dump.json" in stats_check.detail

    corpus_check = next(r for r in results if r.name == "corpus-counts")
    assert corpus_check.status is not Status.PASS
    assert "mystery_dump.json" in corpus_check.detail


def test_doctor_names_an_unreadable_corpus_artifact(tmp_path):
    """B2: an unreadable corpus artifact produces a named, non-PASS state."""
    ws = tmp_path / "ws"
    lit = ws / "literature"
    lit.mkdir(parents=True)
    (lit / "raw_search.json").write_text('[{"t": 1}, {"t"', encoding="utf-8")
    _write_manifest(ws, {"discovered_papers": 0})

    results = check_layout(ws)
    stats_check = next(r for r in results if r.name == "project.json-stats")
    assert stats_check.status is Status.FAIL
    assert "UNREADABLE" in stats_check.detail
    assert "raw_search.json" in stats_check.detail

    corpus_check = next(r for r in results if r.name == "corpus-counts")
    assert corpus_check.status is Status.FAIL
    assert "raw_search.json" in corpus_check.detail


# ---------------------------------------------------------------------------
# AC-4 / N-8: determinism
# ---------------------------------------------------------------------------


def test_counting_is_deterministic(calibration_workspace):
    """AC-4: two runs over an unchanged workspace agree exactly."""
    ws, _expected = calibration_workspace
    first = counts.count_corpus(ws)
    second = counts.count_corpus(ws)
    assert first.stats == second.stats
    assert first.sources == second.sources
    assert first.selected == second.selected
    assert first.status == second.status
    assert [c.as_dict() for c in first.candidates] == [
        c.as_dict() for c in second.candidates
    ]


def test_two_syncs_produce_identical_stats(calibration_workspace):
    """N-8: ``sync`` is idempotent for the stats block."""
    ws, expected = calibration_workspace
    ResearchOrchestrator(ws).sync_state()
    first = json.loads((ws / "project.json").read_text(encoding="utf-8"))["stats"]
    ResearchOrchestrator(ws).sync_state()
    second = json.loads((ws / "project.json").read_text(encoding="utf-8"))["stats"]
    assert first == second
    assert first["discovered_papers"] == expected["raw_union.json"]


# ---------------------------------------------------------------------------
# AC-8: the reconciliation is recorded in the journal
# ---------------------------------------------------------------------------


def _journal_events(ws: Path) -> list[dict]:
    journal = ws / "audit" / "journal.jsonl"
    if not journal.is_file():
        return []
    return [
        json.loads(line)
        for line in journal.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_sync_records_the_reconciliation_in_the_journal(calibration_workspace):
    """AC-8: declared-vs-actual and the corrected values land in the journal."""
    ws, expected = calibration_workspace
    ResearchOrchestrator(ws).sync_state()

    events = _journal_events(ws)
    sync_events = [e for e in events if e.get("action") == "STATE_SYNC"]
    assert sync_events, "the sync must leave a reconciliation event"

    event = sync_events[-1]
    assert event["agent_or_tool"] == "scholar-harness"
    assert event["inputs"], "the event must name its inputs"
    assert event["outputs"], "the event must name its outputs"

    metrics = event["metrics"]
    assert metrics, "metrics must not be empty"
    reconciliation = metrics["reconciliation"]
    assert reconciliation["status"] == "STALE"
    assert reconciliation["declared"]["discovered_papers"] == 0
    assert reconciliation["actual"]["discovered_papers"] == expected["raw_union.json"]
    assert reconciliation["mismatches"], "the corrected values must be recorded"
    # n1: the sources block is machine readable (one path per entry).
    assert reconciliation["sources"]["discovered_papers"] == [
        "calibration/raw_union.json"
    ]
    assert reconciliation["selected"]["discovered_papers"] == [
        "calibration/raw_union.json"
    ]


def test_sync_event_action_and_actor_are_canonical(calibration_workspace):
    """AC-8: the action name is the harness' existing canonical state-sync name.

    The workspace-manager audit trace spec (section 3) has no
    reconciliation-specific action and states that the writer enforces no
    closed enum, so the pre-existing ``STATE_SYNC`` action is reused rather
    than inventing a new dialect.
    """
    ws, _expected = calibration_workspace
    ResearchOrchestrator(ws).sync_state()
    event = [e for e in _journal_events(ws) if e.get("action") == "STATE_SYNC"][-1]
    assert event["action"] == "STATE_SYNC"
    assert event["status"]
    assert event["event_id"].startswith("EVT-")


# ---------------------------------------------------------------------------
# AC-9: existing behavior is preserved
# ---------------------------------------------------------------------------


def test_project_json_schema_and_authored_fields_are_preserved(calibration_workspace):
    """AC-9: ``sync`` keeps the manifest shape and researcher-authored fields."""
    ws, expected = calibration_workspace
    ResearchOrchestrator(ws).sync_state()
    manifest = json.loads((ws / "project.json").read_text(encoding="utf-8"))
    assert manifest["project_id"] == ws.name
    assert manifest["title"] == "Reconciliation Fixture"
    assert manifest["research_questions"] == []
    assert manifest["keywords"] == []
    assert isinstance(manifest["stats"], dict)
    assert manifest["stats"]["discovered_papers"] == expected["raw_union.json"]
    assert "updated_at" in manifest


# ---------------------------------------------------------------------------
# F-1 / F-2: a corpus that EXISTS is never reported as "no corpus artifact"
# ---------------------------------------------------------------------------


def _conflict_only_workspace(tmp_path: Path) -> Path:
    """The verifier's fixture: a physical record list whose own summary lies.

    ``literature/papers.json`` physically carries 3 records but declares
    ``total: 13096`` -- a summary/list conflict. The manifest declares 3.
    """
    ws = tmp_path / "ws"
    lit = ws / "literature"
    lit.mkdir(parents=True)
    (lit / "papers.json").write_text(
        json.dumps(
            {"documents": [{"t": 1}, {"t": 2}, {"t": 3}], "total": 13096},
        ),
        encoding="utf-8",
    )
    _write_manifest(ws, {"discovered_papers": 3})
    return ws


def test_conflict_only_corpus_is_never_reported_as_no_corpus(tmp_path):
    """F-1: a corpus that physically exists is never "no corpus artifact".

    The artifact's own summary contradicts its own record list, but it
    PHYSICALLY carries 3 records. The old code only counted ``COUNTED``
    artifacts, so the conflict artifact was invisible: the workspace was
    reported as ``NO_CORPUS`` / "no corpus artifact ... (0 corpus records)"
    while 3 records physically existed -- and the doctor printed
    "discovered_papers=3" and "0 corpus records" in one breath.
    """
    ws = _conflict_only_workspace(tmp_path)

    counted = counts.count_corpus(ws)
    assert counted.corpus_present is True, "a conflict artifact carries records"
    assert counted.stats["discovered_papers"] == 3

    reconciliation = counts.reconcile(ws)
    assert reconciliation.status != "NO_CORPUS"
    assert reconciliation.status == "CONFLICT"
    assert reconciliation.reconciled is False

    results = check_layout(ws)
    stats_check = next(r for r in results if r.name == "project.json-stats")
    assert stats_check.status is not Status.PASS
    detail = stats_check.detail.lower()
    assert "no corpus artifact" not in detail
    assert "0 corpus records" not in detail
    # The physical count is reported (3 records), and the conflict is named.
    assert "3" in stats_check.detail
    assert "papers.json" in stats_check.detail

    corpus_check = next(r for r in results if r.name == "corpus-counts")
    assert "3" in corpus_check.detail


def test_summary_only_corpus_is_never_a_verified_physical_reconciliation(tmp_path):
    """F-2: a DECLARED summary is not a verified physical reconciliation.

    The corpus exists only as a summary field (``{"count": 12}``): there is
    no physical record list. The old code had no ``SUMMARY`` branch in
    ``reconcile()``, so the summary-only workspace collapsed into
    ``NO_CORPUS`` -- presented as a *verified* physical reconciliation of
    "0 corpus records" while the manifest declared 12.
    """
    ws = tmp_path / "ws"
    lit = ws / "literature"
    lit.mkdir(parents=True)
    (lit / "papers.json").write_text(json.dumps({"count": 12}), encoding="utf-8")
    _write_manifest(ws, {"discovered_papers": 12})

    counted = counts.count_corpus(ws)
    assert counted.status == "SUMMARY"
    assert counted.corpus_present is False

    reconciliation = counts.reconcile(ws)
    assert reconciliation.status == "SUMMARY"
    assert reconciliation.reconciled is False

    results = check_layout(ws)
    stats_check = next(r for r in results if r.name == "project.json-stats")
    assert stats_check.status is not Status.PASS
    detail = stats_check.detail.lower()
    assert "no corpus artifact in this workspace" not in detail
    assert "0 corpus records" not in detail
    assert "summary" in detail


# ---------------------------------------------------------------------------
# F-4: the doctor and ``sync`` must report the SAME reconciliation
# ---------------------------------------------------------------------------


def test_doctor_and_sync_report_the_same_reconciliation(tmp_path):
    """F-4: one workspace, one reconciliation, one verdict.

    The doctor compared the PDF/extraction counters while ``sync_state`` did
    not, so the same workspace got two verdicts: the doctor said ``FAIL``
    while the ``STATE_SYNC`` row said ``OK``.
    """
    ws = tmp_path / "ws"
    lit = ws / "literature"
    lit.mkdir(parents=True)
    (lit / "raw_search.json").write_text(json.dumps([{"t": 1}]), encoding="utf-8")
    # The corpus is correct; the PDF counter is stale (there is no pdfs/).
    _write_manifest(ws, {"discovered_papers": 1, "downloaded_pdfs": 5})

    state: dict = {}
    check_layout(ws, state=state)
    doctor_status = state["status"]

    result = ResearchOrchestrator(ws).sync_state()
    sync_status = result["reconciliation"]["status"]

    event = [e for e in _journal_events(ws) if e.get("action") == "STATE_SYNC"][-1]

    assert doctor_status == "STALE"
    assert sync_status == doctor_status
    assert event["status"] == doctor_status
    assert event["metrics"]["reconciliation"]["status"] == doctor_status

    # The declared PDF counter is repaired by the sync, so the doctor and the
    # journal agree again afterwards.
    ResearchOrchestrator(ws).sync_state()
    state = {}
    check_layout(ws, state=state)
    event = [e for e in _journal_events(ws) if e.get("action") == "STATE_SYNC"][-1]
    assert state["status"] == event["status"] == "OK"


# ---------------------------------------------------------------------------
# F-5: the documentation states the truth
# ---------------------------------------------------------------------------


def _reconciliation_doc() -> str:
    path = (
        Path(__file__).resolve().parents[2]
        / "docs"
        / "architecture"
        / "workspace_stats_reconciliation.md"
    )
    return path.read_text(encoding="utf-8")


def test_documentation_states_the_reconciliation_vocabulary():
    """F-5: the doc lists every status the harness can report.

    The doctor reports three "the reconciliation never happened" statuses
    (``MISSING_MANIFEST`` / ``UNREADABLE_MANIFEST`` / ``NOT_APPLICABLE``)
    that were missing from the documented vocabulary, and the ``SUMMARY`` /
    ``CONFLICT`` verdicts were not documented at all.
    """
    doc = _reconciliation_doc()
    for status in (
        "OK",
        "STALE",
        "UNCLASSIFIED",
        "UNRESOLVED",
        "UNIDENTIFIED",
        "CONFLICT",
        "SUMMARY",
        "NO_CORPUS",
        "MISSING_MANIFEST",
        "UNREADABLE_MANIFEST",
        "NOT_APPLICABLE",
    ):
        assert f"`{status}`" in doc, f"{status} is not documented"


def test_documentation_names_the_artifact_the_counter_really_selects():
    """F-5: the measured file name is the one the counter selects.

    The doc attributed the 14413 records to ``v03_r3e_...`` while the
    counter selects ``v03_r3d_...`` (same record count, lexicographic
    tie-break, never mtime).
    """
    doc = _reconciliation_doc()
    assert "v03_r3d_20261017_union_hydrated.json" in doc
    assert "v03_r3e_20261017_union_hydrated.json" not in doc
