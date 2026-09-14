"""The nexus-scholar metapackage declares the umbrella entrypoints and bundles the kit sources."""

from __future__ import annotations

import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

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
    "../../.agents/skills": "scholar_harness_data/skills",
    "nexus_scholar_pins.json": "nexus_scholar_pins.json",
}


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
    assert set(package_sources.values()) == {"scholar_harness", "scholar_agent", "scholar_bib", "scholar_graph", "scholar_pdf", "scholar_protocol", "scholar_rag", "scholar_search", "scholar_verify", "scholar_harness_data/skills"}
    for source, destination in package_sources.items():
        resolved = (METAPACKAGE_DIR / source).resolve()
        assert resolved.is_dir(), (
            f"force-include source {source!r} for {destination!r} is not a directory: {resolved}"
        )
    pins = METAPACKAGE_DIR / "nexus_scholar_pins.json"
    assert pins.is_file(), "force-included nexus_scholar_pins.json snapshot is missing"


def test_skills_bundle_covers_all_shipped_skills():
    """The P7.3 skills bundle mirrors the full `.agents/skills` tree at wheel build."""
    force_include = _load_pyproject()["tool"]["hatch"]["build"]["targets"]["wheel"][
        "force-include"
    ]
    assert force_include["../../.agents/skills"] == "scholar_harness_data/skills"
    skills_dir = (METAPACKAGE_DIR / "../../.agents/skills").resolve()
    assert skills_dir.is_dir()
    shipped = {
        d.name
        for d in skills_dir.iterdir()
        if d.is_dir() and (d / "SKILL.md").is_file()
    }
    assert len(shipped) == 12, f"expected all 12 skills in wheel, found {len(shipped)}: {sorted(shipped)}"
    assert {"workspace-manager", "scholar-search-kit", "methodology-copilot"} <= shipped