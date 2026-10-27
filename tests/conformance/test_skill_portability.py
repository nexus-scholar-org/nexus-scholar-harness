"""Agent-layer Phase D conformance: skill portability (spec 03 §8).

Deterministic, no network. Every assertion is machine-checkable over the
``.agents/skills/*`` tree; the negative cases are the spec's own list (§8
bottom) exercised through synthetic skill text.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

import pytest

from scholar_harness.skills_portability import (
    Preamble,
    audit_text,
    generate_skill_meta,
    parse_frontmatter,
    render,
    rewrite_text,
    validate_frontmatter,
)
from scholar_harness.skills_portability.frontmatter import SkillContractRefusal

ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / ".agents" / "skills"
ROLES_DIR = ROOT / "roles"

RESEARCH_FACING = [
    d.name
    for d in sorted(SKILLS_DIR.iterdir())
    if d.is_dir() and (d / "SKILL.md").is_file() and d.name != "pull-request-gate"
]

#: Docs force-included in the wheel beside the skills (spec 03 §6, packaging
#: ``pyproject.toml`` force-include table). One authoritative copy.
SHIPPED_DOCS = frozenset({"docs/kits_surface_matrix.md"})


def _skill_files():
    return [(name, SKILLS_DIR / name / "SKILL.md") for name in RESEARCH_FACING]


@pytest.mark.parametrize(["skill", "path"], _skill_files())
def test_frontmatter_contract(skill: str, path: Path) -> None:
    contract, body = parse_frontmatter(path.read_text(encoding="utf-8"), path)
    assert contract.name == skill
    # `returns:` is mandatory text — an agent must never guess the shape.
    assert re.search(
        r"^returns: (json|prose|files)$", path.read_text(encoding="utf-8"), re.MULTILINE
    )


@pytest.mark.parametrize("skill", RESEARCH_FACING)
def test_applies_to_roles_and_preflight(skill: str) -> None:
    path = SKILLS_DIR / skill / "SKILL.md"
    contract, _body = parse_frontmatter(path.read_text(encoding="utf-8"), path)
    validate_frontmatter(
        contract,
        roles_dir=ROLES_DIR,
        skill_text=path.read_text(encoding="utf-8"),
        path=path,
    )


def _shipped_for(skill: str) -> frozenset[str]:
    """Spec 03 §6: docs visible where the skill ships — force-included repo
    docs plus co-shipped ``references/*.md`` files (both the bare
    ``references/…`` and the ``{SKILL_DIR:<skill>}/references/…`` forms)."""
    allowed = set(SHIPPED_DOCS)
    for ref in (SKILLS_DIR / skill / "references").glob("*.md"):
        name = f"references/{ref.name}"
        allowed.add(name)
        allowed.add("{SKILL_DIR:" + skill + "}/" + name)
    return frozenset(allowed)


@pytest.mark.parametrize("skill", RESEARCH_FACING)
def test_no_machine_leakage(skill: str) -> None:
    """Spec 03 §8 assertions: no literal invocation, no absolute path, no
    bare tools/workspaces, no prose pin, no dangling doc pointer."""
    path = SKILLS_DIR / skill / "SKILL.md"
    findings = audit_text(
        path.read_text(encoding="utf-8"), shipped_docs=_shipped_for(skill)
    )
    breaches = [
        f
        for f in findings
        if f.rule
        in (
            "literal-invocation",
            "absolute-path",
            "repo-path",
            "prose-pin",
            "dangling-doc",
            "unregistered-variable",
        )
    ]
    assert breaches == [], [(b.rule, b.detail, b.line_no) for b in breaches]


@pytest.mark.parametrize("skill", RESEARCH_FACING)
def test_skeleton_sections(skill: str) -> None:
    """Spec 03 §7: Preflight required whenever `requires` is declared;
    Refusals whenever the skill surfaces commands (domain/procedure layers;
    a `policy` skill encodes prohibitions and may omit Refusals)."""
    path = SKILLS_DIR / skill / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    contract, _body = parse_frontmatter(text, path)
    if contract.requires:
        assert re.search(r"^##\s+Preflight$", text, re.MULTILINE), (
            f"{skill}: declares requires={contract.requires} but has no Preflight"
        )
    if contract.layer != "policy":
        assert re.search(r"^##\s+Refusals$", text, re.MULTILINE), (
            f"{skill}: no Refusals section"
        )
    else:  # policy skills may omit Refusals — spec 03 §7 omission rule
        pass


def _app_preamble() -> Preamble:
    """Simulated application preamble (spec 03 §4, right-hand column)."""
    return Preamble(
        cli="nexus {{kit}}",  # the app's command alias
        kit_root="/opt/app/kits/scholar-{{kit}}",
        workspace="/data/projects/demo",
        cache="/data/cache",
        config="/data/config/plugins.json",
        py="/usr/bin/python3",
        skill_dirs={"scholar-search-kit": "/opt/app/skills/scholar-search-kit"},
    )


@pytest.mark.parametrize("skill", RESEARCH_FACING)
def test_dev_preamble_resolves(skill: str) -> None:
    from scholar_harness.skills_portability import VARIABLE_PATTERN

    path = SKILLS_DIR / skill / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    _contract, body = parse_frontmatter(text, path)
    resolved = render(body, Preamble.dev())
    # Nothing stays half-bound in the dev loop.
    assert not VARIABLE_PATTERN.search(resolved), [
        m.group(0) for m in VARIABLE_PATTERN.finditer(resolved)
    ]


def _app_preamble() -> Preamble:
    """Simulated application preamble (spec 03 §4, right-hand column)."""
    return Preamble(
        cli="nexus {{kit}}",  # the app's command alias
        kit_root="/opt/app/kits/scholar-{{kit}}",
        workspace="/data/projects/demo",
        cache="/data/cache",
        config="/data/config/plugins.json",
        py="/usr/bin/python3",
        skill_dirs={"scholar-search-kit": "/opt/app/skills/scholar-search-kit"},
    )


@pytest.mark.parametrize("skill", ["scholar-search-kit"])
def test_app_preamble_resolves(skill: str) -> None:
    from scholar_harness.skills_portability import VARIABLE_PATTERN

    path = SKILLS_DIR / skill / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    _contract, body = parse_frontmatter(text, path)
    resolved = render(body, _app_preamble())
    assert not VARIABLE_PATTERN.search(resolved), "a placeholder failed to bind"


# ---------------------------------------------------------------------------
# Mechanical rewrite idempotence + negative cases (spec 03 §8 bottom)
# ---------------------------------------------------------------------------


def test_rewrite_is_idempotent() -> None:
    sample = "uv run scholar-search search ...\nuv run python tools/apply.py"
    once = rewrite_text(sample)
    twice = rewrite_text(once)
    assert once == twice


def test_negative_reintroduced_invocation() -> None:
    findings = audit_text("```bash\nuv run scholar-search search 'covid'\n```")
    assert any(f.rule == "literal-invocation" for f in findings)


def test_negative_prose_sha(tmp_path: Path) -> None:
    findings = audit_text("Pinned at `79ffe421dfea2a2b6e4c02fdff651e6d23ce9b92`.")
    assert any(f.rule == "prose-pin" for f in findings)


SEALED_SKILL = """\
---
name: negative-probe
description: Synthetic negative-case skill.
applies_to: [screener]
requires: [scholar-pdf]
variables: [WORKSPACE]
returns: json
layer: domain
---
# negative-probe
Commands only.
"""


def test_negative_requires_without_preflight(tmp_path: Path) -> None:
    roles = tmp_path / "roles"
    roles.mkdir()
    (roles / "screener.json").write_text("{}", encoding="utf-8")
    contract, body = parse_frontmatter(SEALED_SKILL, Path("negative-probe"))
    with pytest.raises(SkillContractRefusal) as excinfo:
        validate_frontmatter(contract, roles_dir=roles, skill_text=body)
    assert "Preflight" in str(excinfo.value.detail)


def test_negative_unknown_role(tmp_path: Path) -> None:
    roles = tmp_path / "roles"
    roles.mkdir()
    (roles / "screener.json").write_text("{}", encoding="utf-8")
    contract, body = parse_frontmatter(SEALED_SKILL, Path("negative-probe"))
    with pytest.raises(SkillContractRefusal) as no_roles:
        validate_frontmatter(
            contract, roles_dir=tmp_path / "missing-roles", skill_text=body
        )
    assert no_roles.value.refusal_code.value == "BLOCKED_INPUT"
    roles2 = tmp_path / "roles2"
    roles2.mkdir()
    (roles2 / "screener.json").write_text("{}", encoding="utf-8")
    # applies_to ok here; the orphan case needs a bogus role in frontmatter
    bogus = SEALED_SKILL.replace(
        "applies_to: [screener]", "applies_to: [nonexistent-role]"
    )
    contract2, body2 = parse_frontmatter(bogus, Path("negative-probe"))
    with pytest.raises(SkillContractRefusal) as orphan:
        validate_frontmatter(contract2, roles_dir=roles2, skill_text=body2)
    assert "nonexistent-role" in orphan.value.detail


def test_negative_dangling_pointer(tmp_path: Path) -> None:
    shipped = tmp_path / "skill" / "SKILL.probe.md"
    shipped.parent.mkdir()
    shipped.write_text(
        "# probe\nSee `docs/kits_surface_matrix_nope.md` for details.\n",
        encoding="utf-8",
    )
    findings = audit_text(
        shipped.read_text(encoding="utf-8"), shipped_docs=SHIPPED_DOCS
    )
    assert any(f.rule == "dangling-doc" for f in findings)


# ---------------------------------------------------------------------------
# SKILL.meta.json at install (spec 03 §5) — manifest is the only pin source
# ---------------------------------------------------------------------------


def test_skill_meta_generated_from_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    src = tmp_path / "skills_src" / "scholar-search-kit"
    src.mkdir(parents=True)
    (src / "SKILL.md").write_text(
        "---\nname: scholar-search-kit\ndescription: probe\n---\nbody\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "plugins.json"
    manifest.write_text(
        '{"plugins": [{"name": "scholar-search-kit", "default_rev": "d20292a410a4aaa278fa9ffef8021b949a3218c3"}]}',
        encoding="utf-8",
    )
    created = generate_skill_meta(
        tmp_path / "skills_src", manifest, verified_at="2026-10-27T00:00:00Z"
    )
    meta = __import__("json").loads(
        (created["scholar-search-kit"]).read_text(encoding="utf-8")
    )
    assert meta["rev"] == "d20292a410a4aaa278fa9ffef8021b949a3218c3"
    assert meta["kit"] == "scholar-search-kit"
    assert meta["source"].endswith("plugins.json")
    assert meta["verified_at"] == "2026-10-27T00:00:00Z"


def test_skill_meta_unknown_kit_is_honest(tmp_path: Path) -> None:
    src = tmp_path / "pull-request-gate"
    src.mkdir()
    (src / "SKILL.md").write_text(
        "---\nname: pull-request-gate\ndescription: dev-only\n---\nbody\n",
        encoding="utf-8",
    )
    manifest = tmp_path / "plugins.json"
    manifest.write_text('{"plugins": []}', encoding="utf-8")
    created = generate_skill_meta(tmp_path, manifest, dry_run=True)
    assert (
        created["pull-request-gate"]
        == tmp_path / "pull-request-gate" / "SKILL.meta.json"
    )
