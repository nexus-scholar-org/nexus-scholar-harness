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

from scholar_harness.capabilities import InProcessAdapter, OpencodeAdapter
from scholar_harness.skills_portability import (
    CLI_SHORTS,
    KIT_SHORTS,
    Preamble,
    VARIABLE_PATTERN,
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

#: Every skill directory present in this checkout, including the dev-only
#: ``pull-request-gate``, which the wheel excludes
#: (``packaging/nexus-scholar/pyproject.toml``). It is a vocabulary key in the
#: dev loop and in a checkout-backed app, not a claim about wheel contents.
SKILL_DIRS_PRESENT = [
    d.name
    for d in sorted(SKILLS_DIR.iterdir())
    if d.is_dir() and (d / "SKILL.md").is_file()
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
    """Simulated application preamble, generated from the vocabulary.

    Every typed key comes from the registry (``CLI_SHORTS``/``KIT_SHORTS``) or
    from the skill directories present in this checkout, so this fixture cannot
    drift from the placeholders the skills actually use.
    """
    env = {f"CLI:{short}": f"nexus {short}" for short in CLI_SHORTS}
    env |= {
        f"KIT_ROOT:{short}": f"/opt/app/kits/scholar-{short}" for short in KIT_SHORTS
    }
    env |= {
        f"SKILL_DIR:{skill}": f"/opt/app/skills/{skill}" for skill in SKILL_DIRS_PRESENT
    }
    env |= {
        "WORKSPACE": "/data/projects/demo",
        "CACHE": "/data/cache",
        "CONFIG": "/data/config/plugins.json",
        "PY": "/usr/bin/python3",
    }
    return Preamble.from_env(env)


def _adapter_envs(workspace: Path, config: Path) -> dict[str, dict[str, str]]:
    """The two adapter surfaces' binding maps (spec 04 §1 ``resolve_env``)."""
    return {
        "in-process": InProcessAdapter(
            root=ROOT, workspace=workspace, roles_dir=ROLES_DIR
        ).resolve_env(workspace=workspace, config=config),
        "opencode": OpencodeAdapter(
            workspace=workspace, roles_dir=ROLES_DIR
        ).resolve_env(workspace=workspace, config=config),
    }


def _body(skill: str) -> str:
    path = SKILLS_DIR / skill / "SKILL.md"
    _contract, body = parse_frontmatter(path.read_text(encoding="utf-8"), path)
    return body


def _assert_fully_bound(skill: str, preamble: Preamble) -> str:
    resolved = render(_body(skill), preamble)
    assert not VARIABLE_PATTERN.search(resolved), [
        m.group(0) for m in VARIABLE_PATTERN.finditer(resolved)
    ]
    return resolved


@pytest.mark.parametrize("skill", RESEARCH_FACING)
def test_dev_preamble_resolves(skill: str) -> None:
    # Both surfaces must resolve the same body: one vocabulary, two preambles.
    assert _assert_fully_bound(skill, Preamble.dev())
    assert _assert_fully_bound(skill, _app_preamble())
    # The dev ``{KIT_ROOT:<short>}`` must name the vendored checkout, not
    # ``tools/scholar-<short>`` (which does not exist): "no placeholder
    # survives" alone cannot catch a wrong-but-renderable template.
    dev = Preamble.dev()
    for short in KIT_SHORTS:
        rendered = render("{KIT_ROOT:" + short + "}", dev)
        assert Path(rendered).is_dir(), (short, rendered)
        assert Path(rendered).name == f"scholar-{short}-kit", rendered


@pytest.mark.parametrize("skill", RESEARCH_FACING)
def test_app_preamble_resolves(skill: str) -> None:
    assert _assert_fully_bound(skill, _app_preamble())


# ---------------------------------------------------------------------------
# The adapter env is the app/dev preamble source (spec 04 §1 + spec 03 §4)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("surface", ["in-process", "opencode"])
@pytest.mark.parametrize("skill", SKILL_DIRS_PRESENT)
def test_adapter_env_renders_every_shipped_skill(
    skill: str, surface: str, tmp_path: Path
) -> None:
    """Criterion 2: all 14 skills resolve from both adapter envs (28 cases)."""
    workspace = tmp_path / "workspaces" / "demo"
    workspace.mkdir(parents=True)
    env = _adapter_envs(workspace, tmp_path / "plugins.json")[surface]
    preamble = Preamble.from_env(env)

    # The env is the preamble's own key spelling: a round trip is identity.
    assert preamble.env_keys() == frozenset(env)
    resolved = _assert_fully_bound(skill, preamble)

    if surface == "in-process":
        # The application never shells out to ``uv``.
        assert "uv run" not in resolved


def test_adapter_env_cli_and_kit_root_bindings_per_surface(tmp_path: Path) -> None:
    """Criterion 3: dev says ``uv run scholar-search``; app says
    ``scholar-search`` with no ``uv run``; both ``{KIT_ROOT:*}`` exist."""
    workspace = tmp_path / "workspaces" / "demo"
    workspace.mkdir(parents=True)
    envs = _adapter_envs(workspace, tmp_path / "plugins.json")

    dev = Preamble.from_env(envs["opencode"])
    app = Preamble.from_env(envs["in-process"])
    assert render("{CLI:search}", dev) == "uv run scholar-search"
    assert render("{CLI:search}", app) == "scholar-search"
    assert "uv run" not in render("{CLI:search} {CLI:harness}", app)
    assert render("{CLI:harness}", dev) == "uv run scholar-harness"

    for surface, preamble in (("opencode", dev), ("in-process", app)):
        for short in KIT_SHORTS:
            rendered = render("{KIT_ROOT:" + short + "}", preamble)
            assert Path(rendered).is_dir(), (surface, short, rendered)


def test_kit_root_pyproject_resolves_in_dev_but_not_in_app(tmp_path: Path) -> None:
    """Boundary (open contract decision): the app ``KIT_ROOT`` is a package dir.

    A shipped body composes ``{KIT_ROOT:rag}/pyproject.toml``; that idiom is
    checkout-shaped. Under the dev preamble it names a real file, under the
    in-process adapter (installed package directory) it does not. This test
    documents the gap rather than pretending the app column is resolved.
    """
    workspace = tmp_path / "workspaces" / "demo"
    workspace.mkdir(parents=True)
    app_env = _adapter_envs(workspace, tmp_path / "plugins.json")["in-process"]

    dev_file = Path(render("{KIT_ROOT:rag}/pyproject.toml", Preamble.dev()))
    app_file = Path(render("{KIT_ROOT:rag}/pyproject.toml", Preamble.from_env(app_env)))

    assert dev_file.is_file(), dev_file
    assert not app_file.exists(), app_file
    # The package directory itself exists; the checkout idioms below it do not.
    assert Path(render("{KIT_ROOT:rag}", Preamble.from_env(app_env))).is_dir()
    assert not Path(
        render("{KIT_ROOT:rag}/src/scholar_rag", Preamble.from_env(app_env))
    ).exists()


def test_missing_py_binding_is_a_named_value_error(tmp_path: Path) -> None:
    """Criterion 4: a missing ``PY`` is a loud ``ValueError`` naming it."""
    workspace = tmp_path / "workspaces" / "demo"
    workspace.mkdir(parents=True)
    env = dict(_adapter_envs(workspace, tmp_path / "plugins.json")["in-process"])
    env.pop("PY")
    preamble = Preamble.from_env(env)
    assert "PY" not in preamble.env_keys()

    body = "{WORKSPACE}/protocol.json\n{PY} -m pytest\n"
    with pytest.raises(ValueError) as excinfo:
        render(body, preamble)
    assert not isinstance(excinfo.value, KeyError)
    assert "{PY}" in str(excinfo.value)

    # The same body renders completely once the binding exists: the failing
    # call above could never return a half-bound string.
    bound = render(body, Preamble.from_env({**env, "PY": "python"}))
    assert "{PY}" not in bound
    assert bound.endswith("python -m pytest\n")


def test_missing_skill_dir_binding_is_a_named_value_error() -> None:
    """A skill directory that does not exist is absent, not invented."""
    preamble = Preamble.from_env({"WORKSPACE": "/data/projects/demo"})
    with pytest.raises(ValueError) as excinfo:
        render("{SKILL_DIR:no-such-skill}/scripts/run.py", preamble)
    assert "{SKILL_DIR:no-such-skill}" in str(excinfo.value)


def test_preamble_from_env_round_trips_and_ignores_foreign_keys() -> None:
    """Only vocabulary keys are read; everything else is ignored."""
    preamble = _app_preamble()
    env = preamble.bindings()
    assert Preamble.from_env(env).bindings() == env

    noise = {
        **env,
        "PATH": "/usr/bin:/bin",
        "HOME": "/home/someone",
        "CLI": "not-a-typed-key",
        "FOO:bar": "ignored",
        "SKILL_DIR": "not-a-typed-key",
    }
    assert Preamble.from_env(noise).bindings() == env


def test_from_env_ignores_unregistered_typed_names_symmetrically() -> None:
    """Accepting a key is the same decision as ``bindings()`` emitting it.

    ``from_env`` must not bind ``CLI:bogus`` / ``KIT_ROOT:bogus`` /
    ``SKILL_DIR:no-such-skill``: ``bindings()`` iterates the registry (and the
    bound skill dirs), so the old unconditional acceptance rendered a
    placeholder that the same preamble could never re-emit.
    """
    bound = _app_preamble().bindings()
    env = {
        **bound,
        "CLI:bogus": "x",
        "KIT_ROOT:bogus": "/tmp/not-a-kit",
        "SKILL_DIR:no-such-skill": "/tmp/not-a-skill",
        "SKILL_DIR": "/tmp/bare-key",
    }
    preamble = Preamble.from_env(env)

    assert preamble.bindings() == bound
    for placeholder in ("{CLI:bogus}", "{KIT_ROOT:bogus}", "{SKILL_DIR:no-such-skill}"):
        with pytest.raises(ValueError) as excinfo:
            render(placeholder, preamble)
        assert placeholder in str(excinfo.value)
        assert not isinstance(excinfo.value, KeyError)


# ---------------------------------------------------------------------------
# Mechanical rewrite idempotence + negative cases (spec 03 §8 bottom)
# ---------------------------------------------------------------------------


def test_rewrite_is_idempotent() -> None:
    sample = "uv run scholar-search search ...\nuv run python tools/apply.py"
    once = rewrite_text(sample)
    twice = rewrite_text(once)
    assert once == twice


def test_rewrite_maps_both_kit_root_spellings() -> None:
    """The vendored checkout form (``tools/scholar-rag-kit/``) rewrites too.

    ``tools/scholar-rag/`` (still used by spec 03 §4's example) and the real
    ``tools/scholar-rag-kit/`` both map to the same placeholder, and the result
    is a fixed point.
    """
    for form in ("tools/scholar-rag/", "tools/scholar-rag-kit/"):
        rewritten = rewrite_text(form + "src/scholar_rag/indexer.py")
        assert rewritten == "{KIT_ROOT:rag}/src/scholar_rag/indexer.py"
        assert rewrite_text(rewritten) == rewritten


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
