"""Environment placeholders for skill bodies (spec 03 §4).

A skill never names its environment; it names *placeholders* and the adapter
binds them. ``REGISTRY`` is the closed vocabulary:

* ``{CLI:<kit>}`` — the kit's command surface. Dev: ``uv run scholar-<kit>``;
  app: the app's alias or in-process call. Never a literal path.
* ``{KIT_ROOT:<kit>}`` — the kit root (the vendored
  ``tools/scholar-<kit>-kit`` checkout in the loop; the installed package
  directory in an app; read-only in app mode).
* ``{WORKSPACE}`` — the active research workspace root.
* ``{CACHE}`` — CWD-independent cache root (``NEXUS_RECON_ROOT`` aware).
* ``{CONFIG}`` — the pin manifest (bundled in the wheel); the only place a
  kit revision may be read.
* ``{PY}`` — the python invocation (dev: ``uv run python``; app: the app's
  interpreter/runner). This is the spec 03 §4 addendum recorded in Phase D.
* ``{SKILL_DIR:<skill>}`` — the named skill's own directory (how a skill
  addresses its co-shipped scripts without ``.agents/`` repo paths).

``audit_text`` flags the spec 03 §2/§8 violations mechanically; every finding
is deterministic and line-numbered. ``rewrite_text`` applies the §4 rewrite
rules idempotently. ``render`` binds placeholders under a ``Preamble``; an
unbound placeholder is a loud ``ValueError`` naming it — a skill never
renders half-bound.

The binding mapping uses the vocabulary's own spelling as its keys:
``CLI:<short>``, ``KIT_ROOT:<short>``, ``SKILL_DIR:<skill>``, ``WORKSPACE``,
``CACHE``, ``CONFIG``, ``PY``. ``Preamble.from_env`` reads exactly those keys —
it must be given the mapping ``CapabilityAdapter.resolve_env`` produced, not an
ambient process environment (a host ``WORKSPACE``/``CACHE`` variable cannot be
distinguished from a binding) — and ``Preamble.bindings`` emits them again, so
a caller can assert round-trip parity without a second key convention.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

#: The closed placeholder vocabulary. Typed placeholders use ``:value``;
#: plain names (WORKSPACE, CACHE, CONFIG, PY) take no value.
REGISTRY: frozenset[str] = frozenset(
    {"CLI", "KIT_ROOT", "WORKSPACE", "CACHE", "CONFIG", "PY", "SKILL_DIR"}
)

#: Placeholders that require a ``:value`` argument.
TYPED: frozenset[str] = frozenset({"CLI", "KIT_ROOT", "SKILL_DIR"})

VARIABLE_PATTERN = re.compile(
    r"\{(CLI|KIT_ROOT|SKILL_DIR|WORKSPACE|CACHE|CONFIG|PY)(?::([a-zA-Z0-9-]+))?\}"
)

_SHA_FULL_RE = re.compile(r"\b[0-9a-f]{40}\b")
_SHA_PIN_PHRASE_RE = re.compile(r"pin(?:ned)?[^`]*`[0-9a-f]{7,40}`", re.IGNORECASE)
_ABS_WINDOWS_RE = re.compile(r"[A-Za-z]:\\")
_ABS_POSIX_RE = re.compile(r"/(home|Users|root)/")
_WS_PATH_RE = re.compile(r"(?<!\w)workspaces/")
_TOOLS_PATH_RE = re.compile(r"(?<!\w)tools/scholar")
_DEV_LOOP_INVOKE_RE = re.compile(r"\buv run\b")


@dataclass(frozen=True)
class Finding:
    """One mechanical portability violation (spec 03 §8)."""

    line_no: int
    rule: str
    detail: str


def audit_text(
    text: str, *, shipped_docs: frozenset[str] | None = None
) -> list[Finding]:
    """Mechanical spec 03 §8 scan; every rule reports line numbers."""

    findings: list[Finding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        if _DEV_LOOP_INVOKE_RE.search(line):
            findings.append(
                Finding(line_no, "literal-invocation", "'uv run' in a skill body")
            )
        if _ABS_WINDOWS_RE.search(line):
            findings.append(Finding(line_no, "absolute-path", "Windows path"))
        if _ABS_POSIX_RE.search(line):
            findings.append(Finding(line_no, "absolute-path", "POSIX home path"))
        if (
            _TOOLS_PATH_RE.search(line) or _WS_PATH_RE.search(line)
        ) and not line.lstrip().startswith("|"):
            findings.append(
                Finding(
                    line_no,
                    "repo-path",
                    "bare repo path ('tools/scholar…' or 'workspaces/…')",
                )
            )
        if _SHA_FULL_RE.search(line) or _SHA_PIN_PHRASE_RE.search(line):
            findings.append(
                Finding(line_no, "prose-pin", "commit SHA restated in prose")
            )
        for match in VARIABLE_PATTERN.finditer(line):
            name, arg = match.group(1), match.group(2)
            if name in TYPED and arg is None:
                findings.append(
                    Finding(
                        line_no,
                        "unregistered-variable",
                        f"{{{name}}} requires ':<value>'",
                    )
                )
            if name not in TYPED and arg is not None:
                findings.append(
                    Finding(
                        line_no,
                        "unregistered-variable",
                        f"{{{name}}} takes no ':value'",
                    )
                )
        if shipped_docs is not None:
            # A doc pointer is a *documentation* reference (``docs/…`` or a
            # co-shipped ``references/…`` file). Workspace runtime artifacts a
            # skill writes (``{WORKSPACE}/synthesis/…`` etc.) are outputs, not
            # pointers.
            for doc in re.findall(r"`([^`]+\.md)`", line):
                if doc.startswith("http") or not re.match(
                    r"^(\{\w+.*?\}/)?(docs/|references/)", doc
                ):
                    continue
                if doc not in shipped_docs:
                    findings.append(
                        Finding(
                            line_no,
                            "dangling-doc",
                            f"doc {doc!r} not shipped with the skill",
                        )
                    )
    return findings


# ---------------------------------------------------------------------------
# Mechanical rewrite (spec 03 §4 rules, idempotent)
# ---------------------------------------------------------------------------

#: CLI surface name → blessed short name used in the ``{CLI:x}`` placeholder.
KIT_COMMANDS: dict[str, str] = {
    "scholar-protocol": "protocol",
    "scholar-search": "search",
    "scholar-pdf": "pdf",
    "scholar-bib": "bib",
    "scholar-rag": "rag",
    "scholar-graph": "graph",
    "scholar-agent": "agent",
    "scholar-verify": "verify",
}

#: Every ``<short>`` a ``{CLI:<short>}`` placeholder may name: the eight kit
#: commands plus the harness's own CLI (``{CLI:harness}``, which
#: ``rewrite_text`` produces for ``uv run scholar-harness``). An adapter
#: iterates this set, so a CLI a skill may name is always a CLI it can bind.
CLI_SHORTS: tuple[str, ...] = tuple(sorted(KIT_COMMANDS.values())) + ("harness",)

#: Every ``<short>`` a ``{KIT_ROOT:<short>}`` placeholder may name. The harness
#: is not a kit — it has a CLI but no vendored/installed kit root — so it is
#: deliberately absent, and no adapter pretends otherwise.
KIT_SHORTS: tuple[str, ...] = tuple(sorted(KIT_COMMANDS.values()))

#: The **single** definition of the dev loop's kit root, relative to the repo
#: root. ``{{kit}}`` is where the blessed short name is spliced in. Both
#: :meth:`Preamble.dev` and
#: :func:`scholar_harness.capabilities.adapter.dev_kit_root` consume this
#: constant, so the preamble and the dev adapter can never disagree about where
#: a vendored kit lives (the checkout is ``tools/scholar-<short>-kit``, not
#: ``tools/scholar-<short>``).
DEV_KIT_ROOT_TEMPLATE = "tools/scholar-{{kit}}-kit"


def _skill_dirs_under(skills: Path) -> dict[str, str]:
    """``{skill_id: resolved_dir}`` for ``<skills>/<id>/SKILL.md`` entries."""
    if not skills.is_dir():
        return {}
    return {
        entry.name: str(entry.resolve())
        for entry in skills.iterdir()
        if entry.is_dir() and (entry / "SKILL.md").is_file()
    }


def _repo_skill_ids() -> frozenset[str]:
    """Skill ids this checkout registers under ``.agents/skills``.

    :meth:`Preamble.from_env` accepts only these names (plus a value that is
    itself a skill directory, e.g. a workspace-local or wheel-installed copy),
    so its key filtering is consistent with :meth:`Preamble.bindings`.
    """
    return frozenset(
        _skill_dirs_under(Path(__file__).resolve().parents[3] / ".agents" / "skills")
    )


def _is_skill_dir(value: str) -> bool:
    """True when ``value`` is an existing directory containing ``SKILL.md``."""
    try:
        path = Path(value)
        return path.is_dir() and (path / "SKILL.md").is_file()
    except OSError:  # unrepresentable host path: not a binding, not an error
        return False


def rewrite_text(text: str) -> str:
    """One deterministic pass of the spec 03 §4 rewrite rules.

    ``uv run scholar-<x> …`` → ``{CLI:<x>} …``; ``uv run python …`` →
    ``{PY} …``; ``tools/scholar-<kit>-kit/…`` (the real dev checkout) and the
    older ``tools/scholar-<kit>/…`` spelling → ``{KIT_ROOT:<kit>}/…``;
    repo ``workspaces/<project-slug>`` / ``workspaces/<ws>`` → ``{WORKSPACE}``.
    Prose references that are **not** invocations or paths (e.g. the package
    name ``scholar-search-kit``) are left alone. No second-guessing: anything
    still banning-consistent after this pass is the author's defect and the
    audit reports it.
    """

    out = text
    for kit, short in KIT_COMMANDS.items():
        out = re.sub(rf"\buv run {kit}\b", "{CLI:" + short + "}", out)
        # The vendored checkout is ``tools/scholar-<short>-kit``; the bare
        # ``tools/scholar-<short>`` spelling is kept because older bodies and
        # spec 03 §4's own example still use it.
        out = out.replace(f"tools/{kit}-kit/", "{KIT_ROOT:" + short + "}/")
        out = out.replace(f"tools/{kit}/", "{KIT_ROOT:" + short + "}/")
    out = out.replace("uv run python", "{PY}")
    # The harness's own CLI surface and its test runner: mechanical extensions
    # recorded for Phase D (spec 03 §4 addendum).
    out = re.sub(r"\buv run scholar-harness\b", "{CLI:harness}", out)
    out = re.sub(r"\buv run pytest\b", "{PY} -m pytest", out)
    out = out.replace("workspaces/<project-slug>", "{WORKSPACE}")
    out = out.replace("workspaces/<ws>", "{WORKSPACE}")
    return out


# ---------------------------------------------------------------------------
# Placeholder binding (dev loop / application preambles)
# ---------------------------------------------------------------------------


class Preamble:
    """Binds registry placeholders for one environment (spec 03 §4 table).

    Two ways to build one:

    * :meth:`dev` — the development loop, anchored at the repo root
      (``uv run scholar-<kit>``, ``tools/scholar-<kit>-kit``).
    * :meth:`from_env` — the flat mapping
      ``CapabilityAdapter.resolve_env`` produces, keyed in the vocabulary's own
      spelling: ``CLI:<short>``, ``KIT_ROOT:<short>``, ``SKILL_DIR:<skill>``,
      ``WORKSPACE``, ``CACHE``, ``CONFIG``, ``PY``. Only names the vocabulary
      registers are accepted; every other key is ignored, so
      ``bindings()`` and the accepted keys always agree. Pass a resolved
      adapter mapping, **not** an ambient process environment: a host
      ``WORKSPACE``/``CACHE`` variable is indistinguishable from a binding here
      and would be bound instead of raising.

    An application supplies its own bindings; an unbound placeholder raises a
    ``ValueError`` naming it (``{PY}``, ``{KIT_ROOT:rag}``, …) — never a
    ``KeyError`` and never a half-rendered string. Callers convert it to a
    named refusal. :meth:`bindings` emits the same key spelling, so
    ``Preamble.from_env(p.bindings()).bindings() == p.bindings()``.
    """

    def __init__(
        self,
        *,
        cli: str | None = None,
        kit_root: str | None = None,
        workspace: str | None = None,
        cache: str | None = None,
        config: str | None = None,
        py: str | None = None,
        skill_dirs: dict[str, str] | None = None,
        cli_bindings: Mapping[str, str] | None = None,
        kit_root_bindings: Mapping[str, str] | None = None,
    ) -> None:
        #: Templates use ``{{kit}}`` where the blessed short name is spliced in.
        self.cli = cli
        self.kit_root = kit_root
        self.workspace = workspace
        self.cache = cache
        self.config = config
        self.py = py
        self.skill_dirs = dict(skill_dirs or {})
        #: Per-``<short>`` bindings (an adapter env names each one explicitly);
        #: consulted before the ``{{kit}}`` template.
        self.cli_bindings = dict(cli_bindings or {})
        self.kit_root_bindings = dict(kit_root_bindings or {})

    @classmethod
    def dev(cls, *, repo_root: Path | None = None) -> "Preamble":
        """Default development-loop bindings, anchored at the repo root.

        ``{KIT_ROOT:<short>}`` expands through :data:`DEV_KIT_ROOT_TEMPLATE`,
        the same constant :func:`~scholar_harness.capabilities.adapter.dev_kit_root`
        uses, so it names the vendored ``tools/scholar-<short>-kit`` checkout
        and never a path that does not exist.
        """
        repo = repo_root or Path(__file__).resolve().parents[3]
        skill_dirs = _skill_dirs_under(repo / ".agents" / "skills")
        cache: str | None = str(repo / ".cache")
        return cls(
            cli="uv run scholar-{{kit}}",
            kit_root=str(repo / DEV_KIT_ROOT_TEMPLATE),
            workspace=str(repo / "workspaces" / "{ws}"),
            cache=cache,
            config=str(repo / ".agents" / "plugins" / "nexus-scholar" / "plugins.json"),
            py="uv run python",
            skill_dirs=skill_dirs,
        )

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> "Preamble":
        """Build a preamble from an adapter's vocabulary-keyed mapping.

        ``env`` must be the mapping ``CapabilityAdapter.resolve_env`` produced
        (never an ambient process environment: ``WORKSPACE``/``CACHE`` are
        plausible host names, so a stray value would bind silently instead of
        raising). Only registered names are accepted:
        ``CLI:<short>`` for ``<short> in CLI_SHORTS``, ``KIT_ROOT:<short>`` for
        ``<short> in KIT_SHORTS``, ``SKILL_DIR:<skill>`` for an id this
        checkout registers (or a value that is itself a ``SKILL.md``
        directory), plus ``WORKSPACE``, ``CACHE``, ``CONFIG`` and ``PY``.
        Everything else (``PATH``, ``HOME``, ``CLI:bogus``, a bare ``CLI``
        without ``:<short>``, …) is ignored — a missing binding is simply
        absent here and becomes a named ``ValueError`` at :meth:`bind`, never
        an invented value, and never a key :meth:`bindings` would omit.
        """
        registered_skills = _repo_skill_ids()
        cli: dict[str, str] = {}
        kit_root: dict[str, str] = {}
        skill_dirs: dict[str, str] = {}
        plain: dict[str, str] = {}
        for key, value in env.items():
            name, sep, arg = str(key).partition(":")
            if sep:
                if not arg:
                    continue
                if name == "CLI" and arg in CLI_SHORTS:
                    cli[arg] = str(value)
                elif name == "KIT_ROOT" and arg in KIT_SHORTS:
                    kit_root[arg] = str(value)
                elif name == "SKILL_DIR" and (
                    arg in registered_skills or _is_skill_dir(str(value))
                ):
                    skill_dirs[arg] = str(value)
                continue
            if name in ("WORKSPACE", "CACHE", "CONFIG", "PY"):
                plain[name] = str(value)
        return cls(
            workspace=plain.get("WORKSPACE"),
            cache=plain.get("CACHE"),
            config=plain.get("CONFIG"),
            py=plain.get("PY"),
            skill_dirs=skill_dirs,
            cli_bindings=cli,
            kit_root_bindings=kit_root,
        )

    def bind(self, name: str, arg: str | None = None) -> str:
        if name not in REGISTRY:
            raise ValueError(f"unknown placeholder {{{name}}}: not in the registry")
        if name in TYPED and arg is None:
            raise ValueError(f"{{{name}}} requires ':<value>'")
        if name not in TYPED and arg is not None:
            raise ValueError(f"{{{name}}} takes no ':value'")
        if name == "CLI":
            if arg in self.cli_bindings:
                return self.cli_bindings[arg]
            if self.cli is None:
                raise ValueError(f"{{CLI:{arg}}} is not bound in this preamble")
            return self.cli.replace("{{kit}}", str(arg))
        if name == "KIT_ROOT":
            if arg in self.kit_root_bindings:
                return self.kit_root_bindings[arg]
            if self.kit_root is None:
                raise ValueError(f"{{KIT_ROOT:{arg}}} is not bound in this preamble")
            return self.kit_root.replace("{{kit}}", str(arg))
        if name == "SKILL_DIR":
            if arg is None or arg not in self.skill_dirs:
                raise ValueError(f"{{SKILL_DIR:{arg}}} is not bound in this preamble")
            return self.skill_dirs[arg]
        value: str | None = {
            "WORKSPACE": self.workspace,
            "CACHE": self.cache,
            "CONFIG": self.config,
            "PY": self.py,
        }[name]
        if value is None:
            raise ValueError(f"{{{name}}} is not bound in this preamble")
        return value

    def bindings(self) -> dict[str, str]:
        """Every binding this preamble can produce, in vocabulary key spelling.

        The keys are the ones :meth:`from_env` reads, so a round trip is
        identity and a caller (or a test) can compare an adapter env with the
        preamble it produced without a second naming convention.
        """
        out: dict[str, str] = {}
        for short in CLI_SHORTS:
            try:
                out[f"CLI:{short}"] = self.bind("CLI", short)
            except ValueError:
                continue
        for short in KIT_SHORTS:
            try:
                out[f"KIT_ROOT:{short}"] = self.bind("KIT_ROOT", short)
            except ValueError:
                continue
        for skill in sorted(self.skill_dirs):
            out[f"SKILL_DIR:{skill}"] = self.skill_dirs[skill]
        for name in ("WORKSPACE", "CACHE", "CONFIG", "PY"):
            try:
                out[name] = self.bind(name)
            except ValueError:
                continue
        return out

    def env_keys(self) -> frozenset[str]:
        """The vocabulary keys this preamble binds (``bindings()`` keys)."""
        return frozenset(self.bindings())


def render(text: str, preamble: Preamble) -> str:
    """Bind every placeholder; unbound ones fail loudly by name.

    All placeholders are resolved **before** any substitution, so a body that
    needs a missing binding raises instead of returning a half-rendered
    string: a caller can never ship output with a literal ``{...}`` left in it.
    """

    resolved: dict[tuple[str, str | None], str] = {}
    for match in VARIABLE_PATTERN.finditer(text):
        key = (match.group(1), match.group(2))
        if key not in resolved:
            resolved[key] = preamble.bind(match.group(1), match.group(2))
    return VARIABLE_PATTERN.sub(
        lambda match: resolved[(match.group(1), match.group(2))], text
    )


__all__ = [
    "CLI_SHORTS",
    "DEV_KIT_ROOT_TEMPLATE",
    "Finding",
    "KIT_COMMANDS",
    "KIT_SHORTS",
    "Preamble",
    "REGISTRY",
    "TYPED",
    "VARIABLE_PATTERN",
    "audit_text",
    "render",
    "rewrite_text",
]
