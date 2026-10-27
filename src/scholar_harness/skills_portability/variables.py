"""Environment placeholders for skill bodies (spec 03 §4).

A skill never names its environment; it names *placeholders* and the adapter
binds them. ``REGISTRY`` is the closed vocabulary:

* ``{CLI:<kit>}`` — the kit's command surface. Dev: ``uv run scholar-<kit>``;
  app: the app's alias or in-process call. Never a literal path.
* ``{KIT_ROOT:<kit>}`` — the kit root (``tools/<kit>`` in the loop; the
  installed package root in an app; read-only in app mode).
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
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

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


def rewrite_text(text: str) -> str:
    """One deterministic pass of the spec 03 §4 rewrite rules.

    ``uv run scholar-<x> …`` → ``{CLI:<x>} …``; ``uv run python …`` →
    ``{PY} …``; ``tools/scholar-<kit>/…`` → ``{KIT_ROOT:<kit>}/…``;
    repo ``workspaces/<project-slug>`` / ``workspaces/<ws>`` → ``{WORKSPACE}``.
    Prose references that are **not** invocations or paths (e.g. the package
    name ``scholar-search-kit``) are left alone. No second-guessing: anything
    still banning-consistent after this pass is the author's defect and the
    audit reports it.
    """

    out = text
    for kit, short in KIT_COMMANDS.items():
        out = re.sub(rf"\buv run {kit}\b", "{CLI:" + short + "}", out)
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

    Dev-loop defaults bind ``{CLI:<kit>}`` to ``uv run scholar-<kit>`` and
    ``{KIT_ROOT:<kit>}`` to ``tools/scholar-<kit>``. An application supplies
    its own bindings; an unbound placeholder raises a ``KeyError``-free
    ``ValueError`` naming the variable — callers convert it to a named
    refusal, never half-render.
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
    ) -> None:
        #: Templates use ``{{kit}}`` where the blessed short name is spliced in.
        self.cli = cli
        self.kit_root = kit_root
        self.workspace = workspace
        self.cache = cache
        self.config = config
        self.py = py
        self.skill_dirs = skill_dirs or {}

    @classmethod
    def dev(cls, *, repo_root: Path | None = None) -> "Preamble":
        """Default development-loop bindings, anchored at the repo root."""
        repo = repo_root or Path(__file__).resolve().parents[3]
        skills = repo / ".agents" / "skills"
        skill_dirs = (
            {
                entry.name: str(entry.resolve())
                for entry in skills.iterdir()
                if entry.is_dir()
            }
            if skills.is_dir()
            else {}
        )
        cache: str | None = str(repo / ".cache")
        return cls(
            cli="uv run scholar-{{kit}}",
            kit_root=str(repo / "tools" / "scholar-{{kit}}"),
            workspace=str(repo / "workspaces" / "{ws}"),
            cache=cache,
            config=str(repo / ".agents" / "plugins" / "nexus-scholar" / "plugins.json"),
            py="uv run python",
            skill_dirs=skill_dirs,
        )

    def bind(self, name: str, arg: str | None = None) -> str:
        if name in ("CLI", "KIT_ROOT") and arg is None:
            raise ValueError(f"{{{name}}} requires ':<value>'")
        if name == "CLI":
            if self.cli is None:
                raise ValueError(f"no CLI binding in this preamble (kit: {arg})")
            return self.cli.replace("{{kit}}", str(arg))
        if name == "KIT_ROOT":
            if self.kit_root is None:
                raise ValueError(f"no KIT_ROOT binding in this preamble (kit: {arg})")
            return self.kit_root.replace("{{kit}}", str(arg))
        if name == "SKILL_DIR":
            if arg is None or arg not in self.skill_dirs:
                raise ValueError(f"no SKILL_DIR binding for skill {arg!r}")
            return self.skill_dirs[arg]
        value: str | None = {
            "WORKSPACE": self.workspace,
            "CACHE": self.cache,
            "CONFIG": self.config,
            "PY": self.py,
        }[name]
        if value is None:
            raise ValueError(f"no {name} binding in this preamble")
        return value


def render(text: str, preamble: Preamble) -> str:
    """Bind every placeholder; unbound ones fail loudly by name."""

    def _sub(match: re.Match[str]) -> str:
        return preamble.bind(match.group(1), match.group(2))

    return "".join(
        VARIABLE_PATTERN.sub(_sub, line) if VARIABLE_PATTERN.search(line) else line
        for line in text.splitlines(keepends=True)
    )


__all__ = [
    "Finding",
    "Preamble",
    "REGISTRY",
    "TYPED",
    "VARIABLE_PATTERN",
    "audit_text",
    "render",
    "rewrite_text",
]
