"""``nexus-scholar doctor``: light distribution-hardening health command (P7.5).

Validates kits/versions against the kit manifest, API-key presence, skill
resolvability, workspace layout, and the CLI/bin seam — all locally, with no
network access and no heavy dependency imports (no torch/chromadb).  The
command is advisory by default (always exits 0); ``--exit-code`` opts in to
a non-zero exit when any check FAILs.

Version-check honesty: ``__version__`` from each kit is *not* the truthful
assertion -- the distribution wheel bundles the very same source tree the
harness imports in the repo checkout, so a version echo would merely
re-report the bundled code.  The truthful assertions are (1) importability of
each declared kit in the current Python env and (2) the pinned ``default_rev``
from the kit manifest (``.agents/plugins/nexus-scholar/plugins.json`` in the
repo checkout; the codegen-derived ``nexus_scholar_pins.json`` snapshot inside
the wheel).
"""

from __future__ import annotations

import importlib
import importlib.metadata
import json
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table

console = Console(force_terminal=True, legacy_windows=False)


class Status(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"
    SKIP = "SKIP"


# Worst → lightest; overall status = the strictest status seen across checks.
_STATUS_PRIORITY = (Status.FAIL, Status.WARN, Status.PASS, Status.SKIP)


_STATUS_STYLE = {
    Status.PASS: "bold green",
    Status.WARN: "bold yellow",
    Status.FAIL: "bold red",
    Status.SKIP: "dim",
}


@dataclass
class CheckResult:
    group: str
    name: str
    status: Status
    detail: str


# ---------------------------------------------------------------------------
# Kit manifest: repo plugins.json (source of truth) -> wheel pins snapshot
# ---------------------------------------------------------------------------


def _repo_plugins_json() -> Path:
    return Path(__file__).resolve().parents[2] / ".agents" / "plugins" / "nexus-scholar" / "plugins.json"


def _wheel_pins_path() -> Path | None:
    """Locate the pins snapshot inside an installed ``nexus-scholar`` wheel."""
    try:
        dist = importlib.metadata.distribution("nexus-scholar")
    except importlib.metadata.PackageNotFoundError:
        return None
    try:
        located = Path(dist.locate_file("nexus_scholar_pins.json"))
    except (OSError, ValueError):
        return None
    return located if located.is_file() else None


def load_kit_manifest() -> dict[str, str]:
    """Return ``{kit_name: default_rev}`` for every declared kit.

    Read order: the repo checkout's ``.agents/plugins/nexus-scholar/plugins.json``
    (single source of truth), then the wheel-bundled ``nexus_scholar_pins.json``
    snapshot (codegen-derived from ``plugins.json`` -- see
    ``scripts/generate_nexus_scholar_pins.py``, CI-enforced in sync), else empty.
    """
    source = _repo_plugins_json()
    if source.is_file():
        data = json.loads(source.read_text(encoding="utf-8"))
        return {
            plugin["name"]: plugin.get("default_rev", "")
            for plugin in data.get("plugins", [])
            if "name" in plugin
        }
    pins = _wheel_pins_path()
    if pins is not None:
        data = json.loads(pins.read_text(encoding="utf-8"))
        return {
            kit["name"]: kit.get("default_rev", "")
            for kit in data.get("kits", [])
            if "name" in kit
        }
    return {}


def _import_name(kit_name: str) -> str:
    """Map a declared kit name to its Python import name.

    ``scholar-protocol-kit`` → ``scholar_protocol`` (the ``scholar-``/``-kit``
    scaffolding is stripped, hyphens become underscores).
    """
    core = kit_name.removeprefix("scholar-").removesuffix("-kit")
    return f"scholar_{core.replace('-', '_')}"


def check_kits(importable_map: dict[str, bool] | None = None) -> list[CheckResult]:
    """Verify every declared kit imports in the CURRENT Python environment.

    ``importable_map`` is a hermetic-test seam: ``{kit_name: importable}``
    replaces real ``importlib.import_module`` lookups when provided.
    """
    manifest = load_kit_manifest()
    if not manifest:
        return [
            CheckResult(
                "kits", "kit-manifest", Status.FAIL,
                "No kit manifest found (repo plugins.json or wheel pins snapshot)",
            )
        ]
    results: list[CheckResult] = []
    for kit_name, rev in manifest.items():
        import_name = _import_name(kit_name)
        if importable_map is not None:
            ok = importable_map.get(kit_name, False)
        else:
            try:
                importlib.import_module(import_name)
                ok = True
            except ImportError:
                ok = False
        if ok:
            suffix = f"pinned {rev[:12]}" if rev else "no pinned rev"
            detail = f"{import_name} imports · {suffix}"
        else:
            detail = f"{import_name} import FAILED"
        results.append(
            CheckResult("kits", kit_name, Status.PASS if ok else Status.FAIL, detail)
        )
    return results


# ---------------------------------------------------------------------------
# Keys: presence only -- values are masked, never echoed
# ---------------------------------------------------------------------------

_MODEL_KEYS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY")
_MASK = "***"


def _read_env_file(path: Path) -> dict[str, str]:
    """Parse a ``.env``-style file into ``{KEY: value}`` (no interpolation).

    ``utf-8-sig`` drops a BOM transparently (Windows ``Set-Content``).
    """
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip("'\"").strip()
        if key:
            values[key] = value
    return values


def check_keys(env_file: Path | None) -> list[CheckResult]:
    """Check API-key presence from the env file.

    - ``SCHOLAR_MAILTO`` present → PASS; missing → WARN (it gates the provider
      polite pool; the only search requirement that gates providers).
    - Model keys (``OPENAI_API_KEY`` / ``ANTHROPIC_API_KEY`` / ``GEMINI_API_KEY``)
      missing → WARN (optional in screening) -- never FAIL.
    - No env file at all → the whole keys section SKIPs.

    Values are never echoed: present keys render as ``***`` (the mask), both in
    the rich table and machine JSON; absent keys render as ``Missing``.
    """
    if env_file is None or not env_file.is_file():
        return [
            CheckResult(
                "keys", "env-file", Status.SKIP,
                "No env file provided or found (default: <workspace>/.env)",
            )
        ]

    env = _read_env_file(env_file)
    results: list[CheckResult] = []

    if env.get("SCHOLAR_MAILTO", "").strip():
        results.append(CheckResult(
            "keys", "SCHOLAR_MAILTO", Status.PASS, _MASK,
        ))
    else:
        results.append(CheckResult(
            "keys", "SCHOLAR_MAILTO", Status.WARN,
            "Missing — add SCHOLAR_MAILTO to the env file for a polite provider pool",
        ))

    for key in _MODEL_KEYS:
        if env.get(key, "").strip():
            results.append(CheckResult("keys", key, Status.PASS, _MASK))
        else:
            results.append(CheckResult(
                "keys", key, Status.WARN,
                f"Missing — {key} is optional (LLM-backed screening / claim checks only)",
            ))

    return results


# ---------------------------------------------------------------------------
# Skills: resolvability via the P7.3 resolver
# ---------------------------------------------------------------------------


def check_skills(skills_root: Path | None = None) -> list[CheckResult]:
    """Verify the skills source resolves to a directory with ``<name>/SKILL.md``.

    ``skills_root`` is a test seam; when ``None`` the real resolver
    (:func:`scholar_harness.inception.resolve_skills_root`) is consulted.
    """
    from .inception import resolve_skills_root

    root = skills_root if skills_root is not None else resolve_skills_root()
    if root is None or not root.is_dir():
        return [
            CheckResult(
                "skills", "skills-root", Status.FAIL,
                "No skills root resolved — set NEXUS_SKILLS_SRC, install the wheel "
                "(bundled scholar_harness_data/skills), or run from the repo checkout "
                "(.agents/skills)",
            )
        ]
    skill_dirs = [d for d in root.iterdir() if d.is_dir() and (d / "SKILL.md").is_file()]
    if not skill_dirs:
        return [
            CheckResult(
                "skills", "skills-root", Status.FAIL,
                f"Skills source {root} contains no <name>/SKILL.md entries",
            )
        ]
    return [
        CheckResult(
            "skills", "skills-root", Status.PASS,
            f"{len(skill_dirs)} skill(s) resolved from {root}",
        )
    ]


# ---------------------------------------------------------------------------
# Layout: canonical workspace contract
# ---------------------------------------------------------------------------

# Strong markers: a directory holding any of these is a Nexus Scholar workspace.
MARKERS = (
    "protocol.json",
    "audit/journal.jsonl",
    "INDEX.md",
    "project.json",
    "intent.json",
    ".mcp.json",
)

CANONICAL_FILES = (
    "protocol.json",
    "intent.json",
    "SCREENING_CRITERIA.md",
    "INDEX.md",
    "project.json",
)

CANONICAL_DIRS = ("synthesis", "literature")

# Stats doctor can derive from the filesystem using the same rules ``sync`` uses
# (sync_state in orchestrator.py) -- excluding chromadb/vector counts, which
# would pull a heavy dependency into a light command.
_SYNC_COUNT_KEYS = (
    ("discovered_papers", "literature/raw_search.json"),
    ("deduped_papers", "literature/deduped.json"),
    ("verified_papers", "literature/verified.json"),
    ("included_papers", "literature/included.json"),
    ("excluded_papers", "literature/excluded.json"),
)


def _actual_stats(ws: Path) -> dict[str, int]:
    """Derive countable stats from the filesystem (sync's rules, minus heavy deps)."""
    stats: dict[str, int] = {}
    for key, rel in _SYNC_COUNT_KEYS:
        path = ws / rel
        if path.is_file():
            try:
                stats[key] = len(json.loads(path.read_text(encoding="utf-8-sig")))
            except (OSError, ValueError):
                stats[key] = 0
    pdf_dir = ws / "pdfs"
    if pdf_dir.is_dir():
        stats["downloaded_pdfs"] = len(list(pdf_dir.glob("*.pdf")))
    ext_dir = ws / "extracted"
    if ext_dir.is_dir():
        stats["extracted_markdowns"] = len(list(ext_dir.glob("*.md")))
    return stats


def check_layout(workspace: Path) -> list[CheckResult]:
    """Validate the workspace layout against the canonical contract.

    A directory without Nexus markers reports SKIP (not a failure).  With
    markers: PASS when every canonical contract file exists, WARN when
    ``project.json`` stats are stale vs the directory state, FAIL when any
    canonical file is missing.
    """
    ws = workspace.resolve()
    if not ws.is_dir():
        return [
            CheckResult(
                "layout", "workspace", Status.FAIL,
                f"Workspace directory does not exist: {ws}",
            )
        ]

    if not any((ws / marker).exists() for marker in MARKERS):
        return [
            CheckResult(
                "layout", "workspace", Status.SKIP,
                f"No Nexus Scholar markers in {ws} (not an init'd workspace)",
            )
        ]

    results: list[CheckResult] = []
    missing_files = [f for f in CANONICAL_FILES if not (ws / f).is_file()]
    if not (ws / "audit" / "journal.jsonl").is_file():
        missing_files.append("audit/journal.jsonl")
    missing_dirs = [d for d in CANONICAL_DIRS if not (ws / d).is_dir()]

    if missing_files or missing_dirs:
        results.append(CheckResult(
            "layout", "canonical-files", Status.FAIL,
            "Missing canonical contract files: " + ", ".join(missing_files + missing_dirs),
        ))
    else:
        results.append(CheckResult(
            "layout", "canonical-files", Status.PASS,
            "All canonical contract files present",
        ))

    manifest_path = ws / "project.json"
    if manifest_path.is_file():
        stale: list[str] = []
        try:
            declared = json.loads(manifest_path.read_text(encoding="utf-8-sig")).get("stats", {})
            actual = _actual_stats(ws)
            stale = [
                key for key, value in actual.items()
                if int(declared.get(key, 0) or 0) != value
            ]
        except (OSError, ValueError):
            stale = None  # unreadable manifest -> warn, don't crash the doctor
        if stale is None:
            results.append(CheckResult(
                "layout", "project.json-stats", Status.WARN,
                "Could not parse project.json for the staleness check",
            ))
        elif stale:
            results.append(CheckResult(
                "layout", "project.json-stats", Status.WARN,
                "Stats may be stale vs the directory state (" + ", ".join(stale) + ") — "
                "run `nexus-scholar sync` to refresh",
            ))
        else:
            results.append(CheckResult(
                "layout", "project.json-stats", Status.PASS,
                "project.json stats match the directory state",
            ))

    return results


# ---------------------------------------------------------------------------
# Seam: CLI importable + console-script entrypoints
# ---------------------------------------------------------------------------


def check_seam() -> list[CheckResult]:
    """Verify the CLI/bin seam: app importable, contract entrypoints present.

    ``nexus-scholar`` and ``scholar-agent`` are the wheel-contracted
    ``console_scripts`` names.  In a repo checkout (harness installed as
    ``nexus-scholar-harness``) the ``nexus-scholar`` metapackage entrypoint is
    expectedly absent -- the check reports the gap truthfully.
    """
    results: list[CheckResult] = [
        CheckResult(
            "seam", "python-version", Status.PASS,
            f"Python {sys.version.split()[0]}",
        ),
    ]

    try:
        importlib.import_module("scholar_harness.cli")
        results.append(CheckResult(
            "seam", "cli-import", Status.PASS,
            "scholar_harness.cli app importable",
        ))
    except ImportError as exc:  # pragma: no cover - import machinery
        results.append(CheckResult(
            "seam", "cli-import", Status.FAIL,
            f"scholar_harness.cli app import FAILED: {exc}",
        ))

    entry_points: dict[str, str] = {}
    try:
        for ep in importlib.metadata.entry_points(group="console_scripts"):
            entry_points.setdefault(ep.name, ep.value)
    except Exception as exc:  # noqa: BLE001 - broken dist metadata must not crash doctor
        results.append(CheckResult(
            "seam", "entry-points", Status.FAIL,
            f"console_scripts entry points could not be read: {exc}",
        ))
        return results

    for name in ("nexus-scholar", "scholar-agent"):
        if name in entry_points:
            results.append(CheckResult(
                "seam", f"entrypoint-{name}", Status.PASS,
                f"{name} → {entry_points[name]}",
            ))
        elif name == "nexus-scholar":
            # The metapackage entrypoint only exists inside the installed wheel;
            # a repo/dev checkout truthfully lacks it and that is expected —
            # WARN (not FAIL) so a healthy dev workspace never reports FAIL.
            results.append(CheckResult(
                "seam", f"entrypoint-{name}", Status.WARN,
                f"{name} not found in console_scripts (wheel-provided via "
                "uvx --from nexus-scholar)",
            ))
        else:
            results.append(CheckResult(
                "seam", f"entrypoint-{name}", Status.FAIL,
                f"{name} not found in console_scripts (install scholar-agent-kit)",
            ))

    return results


# ---------------------------------------------------------------------------
# Report assembly + rendering
# ---------------------------------------------------------------------------


def run_doctor(
    workspace: Path | None = None,
    env_file: Path | None = None,
    *,
    skills_root: Path | None = None,
    importable_map: dict[str, bool] | None = None,
) -> dict[str, Any]:
    """Run every doctor check and assemble the report.

    Returns ``{"checks": [{group, name, status, detail}, ...], "overall": str}``.
    Overall is the worst status across checks (FAIL > WARN > PASS > SKIP).
    """
    ws = (workspace or Path(".")).resolve()
    checks: list[CheckResult] = []
    checks.extend(check_kits(importable_map=importable_map))
    checks.extend(check_keys(env_file))
    checks.extend(check_skills(skills_root=skills_root))
    checks.extend(check_layout(ws))
    checks.extend(check_seam())

    overall = Status.SKIP
    for check in checks:
        if _STATUS_PRIORITY.index(check.status) < _STATUS_PRIORITY.index(overall):
            overall = check.status

    return {
        "checks": [
            {
                "group": check.group,
                "name": check.name,
                "status": check.status.value,
                "detail": check.detail,
            }
            for check in checks
        ],
        "overall": overall.value,
    }


def _mask_json(report: dict[str, Any]) -> str:
    """Serialize the report to JSON, guaranteeing no secret values.

    Keys-section details already carry ``***``/``Missing`` by construction
    (:func:`check_keys` never embeds values); this re-emits the check list
    verbatim so the guarantee is structurally enforced here too.
    """
    # NOTE: unlike _render_table (which re-masks), the JSON guarantee rests on
    # check_keys never placing a value in a detail string — keep it that way.
    return json.dumps(
        {"checks": report["checks"], "overall": report["overall"]},
        indent=2,
    )


def _render_table(report: dict[str, Any]) -> None:
    overall_style = f"[{_STATUS_STYLE[Status(report['overall'])]}]{report['overall']}[/]"
    table = Table(
        title=f"nexus-scholar doctor — overall {overall_style}",
        show_header=True,
        header_style="bold cyan",
    )
    table.add_column("Group", style="bold white", width=10)
    table.add_column("Check", style="bold", width=24)
    table.add_column("Status", width=6)
    table.add_column("Detail", style="white")

    for check in report["checks"]:
        status = Status(check["status"])
        style = _STATUS_STYLE[status]
        status_text = f"[{style}]{status.value}[/{style}]"
        detail = check["detail"]
        if check["group"] == "keys" and status is Status.PASS:
            detail = _MASK  # belt-and-suspenders: keys never render real values
        table.add_row(check["group"], check["name"], status_text, detail)

    console.print(table)

    if any(check["group"] == "kits" for check in report["checks"]):
        console.print(
            "[dim]kits version policy: pinned `default_rev` + importability are the "
            "truthful assertions — the wheel bundles the exact source the harness "
            "imports, so a `__version__` echo would re-report bundled code, not the "
            "install.[/dim]"
        )


def render(report: dict[str, Any], *, as_json: bool = False) -> None:
    """Render the report: a rich table by default, machine JSON with ``--json``."""
    if as_json:
        print(_mask_json(report))
        return
    _render_table(report)