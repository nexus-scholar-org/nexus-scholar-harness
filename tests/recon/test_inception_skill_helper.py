"""Hermetic tests for the inception-agent skill parity helper.

Runs ``.agents/skills/inception-agent/scripts/grounded_directions.py`` as a
subprocess against synthetic fixtures (no network). Locks the contract that
the chat-driven flow proposes exactly the wizard's grounded directions and
builds the ``recon_context`` document the same way ``_run_grounded_recon``
does.
"""

import json
import subprocess
import sys
from pathlib import Path

SKILL_SCRIPT = (
    Path(".agents/skills/inception-agent/scripts/grounded_directions.py").resolve()
)

TERMS_FIXTURE = {
    "qei": 0.2,
    "micro_taxonomy": [
        {"term": "edge inference", "freq": 3, "anchor_dois": ["10.1/a", "10.1/b"]},
        {"term": "orchard robots", "freq": 2, "anchor_dois": ["10.1/b", "10.1/c"]},
        {"term": "cnn", "freq": 1, "anchor_dois": ["10.1/a"]},
    ],
}

POOL_FIXTURE = {
    "cache_key": "v1/fake/q/abc",
    "docs": [
        {"doi": "10.1/a", "title": "Edge inference"},
        {"doi": "10.1/b", "title": "Orchard robots"},
        {"doi": "10.1/c", "title": "CNN features"},
    ],
}


def _write(tmp_path: Path, name: str, payload: dict) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _run(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SKILL_SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=tmp_path,
        check=False,
    )


def test_helper_returns_wizard_directions(tmp_path):
    terms = _write(tmp_path, "terms.json", TERMS_FIXTURE)
    result = _run(
        tmp_path, "--terms", str(terms), "--topic", "edge inference"
    )
    assert result.returncode == 0, result.stderr
    out = json.loads(result.stdout)
    # Same >= 2-anchor filter and ordering as the --grounded wizard:
    # multi-word first, then freq, then lexicographic.
    assert [d["label"] for d in out["directions"]] == [
        "edge inference",
        "orchard robots",
    ]
    assert all(len(d["anchor_dois"]) >= 2 for d in out["directions"])
    assert out["qei"] == 0.2
    assert out["qei_note"].startswith("PASS")


def test_helper_emits_recon_context_for_validated_direction(tmp_path):
    terms = _write(tmp_path, "terms.json", TERMS_FIXTURE)
    pool = _write(tmp_path, "pool.json", POOL_FIXTURE)
    result = _run(
        tmp_path,
        "--terms",
        str(terms),
        "--topic",
        "edge inference",
        "--pool",
        str(pool),
        "--direction",
        "edge inference",
    )
    assert result.returncode == 0, result.stderr
    recon = json.loads(result.stdout)["recon_context"]
    assert recon["direction"] == "edge inference"
    assert recon["concept"] == "edge inference"
    # Validated concept leads the pool-anchored default concepts.
    assert recon["default_concepts"][0] == "edge inference"
    assert recon["anchor_dois"] == ["10.1/a", "10.1/b"]
    # anchored_terms: session topic + validated concept are seeded, every
    # taxonomy term with >= 1 anchor DOI is evidenced.
    assert "orchard robots" in recon["anchored_terms"]
    assert "cnn" in recon["anchored_terms"]
    # Seeded anchors lead; the taxonomy loop may extend (wizard parity).
    assert recon["anchored_terms"]["edge inference"][:2] == ["10.1/a", "10.1/b"]


def test_helper_caps_default_concepts_for_chat_seeding(tmp_path):
    terms = _write(tmp_path, "terms.json", TERMS_FIXTURE)
    result = _run(
        tmp_path,
        "--terms",
        str(terms),
        "--topic",
        "edge inference",
        "--direction",
        "edge inference",
        "--max-default-concepts",
        "1",
    )
    assert result.returncode == 0, result.stderr
    recon = json.loads(result.stdout)["recon_context"]
    # Chat seeding is bounded; the validated concept leads and stays.
    assert recon["default_concepts"] == ["edge inference"]
    assert recon["anchor_dois"] == ["10.1/a", "10.1/b"]


def test_helper_rejects_unknown_direction(tmp_path):
    terms = _write(tmp_path, "terms.json", TERMS_FIXTURE)
    result = _run(
        tmp_path,
        "--terms",
        str(terms),
        "--topic",
        "edge inference",
        "--direction",
        "not-a-direction",
    )
    assert result.returncode == 2
    assert "error" in json.loads(result.stdout)


def test_helper_reports_missing_terms_file(tmp_path):
    result = _run(tmp_path, "--terms", str(tmp_path / "nope.json"), "--topic", "x")
    assert result.returncode == 2
    assert "cannot read --terms" in json.loads(result.stdout)["error"]