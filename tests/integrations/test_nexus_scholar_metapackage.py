"""The nexus-scholar metapackage declares the umbrella entrypoints and bundles the kit sources."""

from __future__ import annotations

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

METAPACKAGE_DIR = REPO_ROOT / "packaging" / "nexus-scholar"
PYPROJECT = METAPACKAGE_DIR / "pyproject.toml"

# force-include mapping: monorepo source path (relative to the packaging dir) -> wheel top-level package.
EXPECTED_FORCE_INCLUDE = {
    "../../src/scholar_harness": "scholar_harness",
    "../../tools/scholar-protocol-kit/src/scholar_protocol": "scholar_protocol",
    "../../tools/scholar-search-kit/src/scholar_search": "scholar_search",
    "../../tools/scholar-pdf-kit/src/scholar_pdf": "scholar_pdf",
    "../../tools/scholar-bib-kit/src/scholar_bib": "scholar_bib",
    "../../tools/scholar-rag-kit/src/scholar_rag": "scholar_rag",
    "../../tools/scholar-graph-kit/src/scholar_graph": "scholar_graph",
    "../../tools/scholar-agent-kit/src/scholar_agent": "scholar_agent",
    "../../tools/scholar-verify-kit/src/scholar_verify": "scholar_verify",
    "nexus_scholar_pins.json": "nexus_scholar_pins.json",
}

# Phase D (spec 03 §9): the skills bundle ships per-skill, excluding the
# dev-only pull-request-gate (repo-policy-only), plus the referenced doc.
RESEARCH_FACING_SKILLS = [
    "critic-contract",
    "doer-contract",
    "inception-agent",
    "methodology-copilot",
    "scholar-agent-kit",
    "scholar-bib-kit",
    "scholar-graph-kit",
    "scholar-pdf-kit",
    "scholar-protocol-kit",
    "scholar-rag-kit",
    "scholar-search-kit",
    "scholar-verify-kit",
    "workspace-manager",
]
for _skill in RESEARCH_FACING_SKILLS:
    EXPECTED_FORCE_INCLUDE[f"../../.agents/skills/{_skill}"] = (
        f"scholar_harness_data/skills/{_skill}"
    )
EXPECTED_FORCE_INCLUDE["../../docs/kits_surface_matrix.md"] = (
    "scholar_harness_data/docs/kits_surface_matrix.md"
)


def _load_pyproject() -> dict:
    with PYPROJECT.open("rb") as fh:
        return tomllib.load(fh)


def test_metapackage_pyproject_exists_and_is_named_nexus_scholar():
    assert PYPROJECT.is_file()
    pyproject = _load_pyproject()
    assert pyproject["project"]["name"] == "nexus-scholar"
    assert pyproject["project"]["requires-python"] == ">=3.11"


def test_console_scripts_point_at_real_entrypoints():
    scripts = _load_pyproject()["project"]["scripts"]
    assert scripts == {
        "nexus-scholar": "scholar_harness.cli:app",
        "scholar-agent": "scholar_agent.server:main",
    }


def test_bundled_packages_cover_harness_and_all_eight_kits():
    force_include = _load_pyproject()["tool"]["hatch"]["build"]["targets"]["wheel"][
        "force-include"
    ]
    assert force_include == EXPECTED_FORCE_INCLUDE


def test_bundled_package_sources_map_to_real_dirs():
    force_include = _load_pyproject()["tool"]["hatch"]["build"]["targets"]["wheel"][
        "force-include"
    ]
    package_sources = {
        source: destination
        for source, destination in force_include.items()
        if destination != "nexus_scholar_pins.json"
    }
    # Phase D (spec 03 §9): the skills tree is bundled per-skill — dev-only
    # pull-request-gate is excluded from the customer-facing wheel — and the
    # skill-referenced doc (kits_surface_matrix) ships beside the skills.
    expected = {
        "scholar_harness",
        "scholar_agent",
        "scholar_bib",
        "scholar_graph",
        "scholar_pdf",
        "scholar_protocol",
        "scholar_rag",
        "scholar_search",
        "scholar_verify",
        "scholar_harness_data/docs/kits_surface_matrix.md",
    } | {"scholar_harness_data/skills/" + name for name in RESEARCH_FACING_SKILLS}
    assert set(package_sources.values()) == expected
    for source, destination in package_sources.items():
        if destination == "scholar_harness_data/docs/kits_surface_matrix.md":
            resolved = METAPACKAGE_DIR / source
            assert resolved.is_file(), f"force-include source {source!r} is not a file"
            continue
        resolved = (METAPACKAGE_DIR / source).resolve()
        assert resolved.is_dir(), (
            f"force-include source {source!r} for {destination!r} is not a directory: {resolved}"
        )
    pins = METAPACKAGE_DIR / "nexus_scholar_pins.json"
    assert pins.is_file(), "force-included nexus_scholar_pins.json snapshot is missing"


def test_skills_bundle_covers_all_shipped_skills():
    """Phase D (spec 03 §9): 13 research-facing skills bundle per-skill;
    the dev-only contribution-workflow skill (pull-request-gate) never ships."""
    force_include = _load_pyproject()["tool"]["hatch"]["build"]["targets"]["wheel"][
        "force-include"
    ]
    skills_dir = (METAPACKAGE_DIR / "../../.agents/skills").resolve()
    assert skills_dir.is_dir()
    on_disk = {
        d.name
        for d in skills_dir.iterdir()
        if d.is_dir() and (d / "SKILL.md").is_file()
    }
    assert len(on_disk) == 14, (
        f"expected 14 skills on disk, found {len(on_disk)}: {sorted(on_disk)}"
    )
    bundled = {
        destination.rsplit("/", 1)[-1]
        for source, destination in force_include.items()
        if destination.startswith("scholar_harness_data/skills/")
    }
    assert bundled <= on_disk
    assert "pull-request-gate" in on_disk
    assert "pull-request-gate" not in bundled, (
        "pull-request-gate is repo-policy-only and must not ship in the wheel"
    )
    assert {"workspace-manager", "scholar-search-kit", "methodology-copilot"} <= bundled
