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

from .workspace import counts

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

# The corpus counters are NOT limited to the canonical ``literature/`` paths
# any more (T-TRUTH-COUNTS-01): the physical corpus is counted wherever it
# physically lives (``literature/``, ``calibration/``, any other corpus-bearing
# directory) and recognition is content-based.  The counting rules live in
# :mod:`scholar_harness.workspace.counts` -- the doctor never re-implements
# them.

#: The check row that carries the declared-vs-actual reconciliation.
RECONCILIATION_CHECK = ("layout", "project.json-stats")


def _cap(items: list[str], limit: int = 8) -> str:
    """Join artifact names for a check detail, capped so one workspace cannot
    flood the table/JSON output."""
    if len(items) <= limit:
        return ", ".join(items)
    return ", ".join(items[:limit]) + f", ... (+{len(items) - limit} more)"


def _extra_actual_stats(ws: Path) -> dict[str, int]:
    """Counters the doctor derives itself (PDFs, extracted markdown).

    Both counters are ALWAYS emitted -- ``0`` when the directory is absent --
    so a declared ``downloaded_pdfs: 5`` in a workspace without a ``pdfs/``
    directory is still compared (silently skipping it would hide a stale
    manifest).

    The computation lives in :mod:`scholar_harness.workspace.counts` so the
    doctor and ``orchestrator.sync_state`` reconcile the SAME workspace the
    SAME way (F-4): two different extra counters produced two different
    verdicts for one and the same workspace.
    """
    return counts.extra_actual_stats(ws)


def _counted_parts(corpus: "counts.CorpusCounts") -> str:
    """The physically counted counters, rendered for a check detail."""
    parts = []
    for key in counts.CORPUS_STAT_KEYS:
        selected = corpus.selected.get(key) or []
        if not selected:
            continue
        parts.append(f"{key}={corpus.stats.get(key, 0)} ({', '.join(selected)})")
    return "; ".join(parts)


def _layout_row(name: str, status: Status, detail: str) -> CheckResult:
    """One layout check row."""
    return CheckResult("layout", name, status, detail)


def _record_state(state: dict[str, Any] | None, **values: Any) -> None:
    """Write the reconciliation state into the caller's out-parameter."""
    if state is None:
        return
    state.clear()
    state.update(values)
    state.setdefault("performed", False)
    state.setdefault("status", "NOT_APPLICABLE")
    state.setdefault("detail", "")


def check_layout(
    workspace: Path, *, state: dict[str, Any] | None = None
) -> list[CheckResult]:
    """Validate the workspace layout against the canonical contract.

    A directory without Nexus markers reports SKIP (not a failure).  With
    markers: PASS when every canonical contract file exists, FAIL when any
    canonical file is missing, and FAIL when the ``project.json`` summary
    disagrees with the physical artifacts (T-TRUTH-COUNTS-01: a stale
    summary is a correctness defect, not a hint -- it used to be a soft
    ``WARN`` while a workspace holding 2165 records claimed ``0``).

    The physical truth is reported next to the consistency check, so the
    doctor never hides the counts behind a stale registry:

    * ``corpus-counts`` states what was physically counted;
    * ``corpus-unreadable`` puts the artifacts that could not be read or
      understood on their OWN line -- an unreadable artifact that maps to no
      role must not poison the counted counters (D-1);
    * ``provider-evidence-overlap`` states the known limitation of a
      summed provider counter;
    * ``project.json-stats`` is NEVER ``PASS`` when the reconciliation was
      not performed: a corpus-free workspace reconciles against its declared
      ``0`` (D-2), an unreadable/unexpected-shaped corpus artifact reports
      ``UNRESOLVED`` (FAIL), record-bearing artifacts the harness cannot
      classify report ``UNCLASSIFIED`` (FAIL), and a missing manifest
      reports that no reconciliation was performed.

    ``state`` is an optional out-parameter: when a dict is passed, the
    reconciliation state is written into it (machine readable).
    """
    ws = workspace.resolve()
    if not ws.is_dir():
        return [
            CheckResult(
                "layout",
                "workspace",
                Status.FAIL,
                f"Workspace directory does not exist: {ws}",
            )
        ]

    if not any((ws / marker).exists() for marker in MARKERS):
        return [
            CheckResult(
                "layout",
                "workspace",
                Status.SKIP,
                f"No Nexus Scholar markers in {ws} (not an init'd workspace)",
            )
        ]

    results: list[CheckResult] = []
    missing_files = [f for f in CANONICAL_FILES if not (ws / f).is_file()]
    if not (ws / "audit" / "journal.jsonl").is_file():
        missing_files.append("audit/journal.jsonl")
    missing_dirs = [d for d in CANONICAL_DIRS if not (ws / d).is_dir()]

    if missing_files or missing_dirs:
        results.append(
            CheckResult(
                "layout",
                "canonical-files",
                Status.FAIL,
                "Missing canonical contract files: "
                + ", ".join(missing_files + missing_dirs),
            )
        )
    else:
        results.append(
            CheckResult(
                "layout",
                "canonical-files",
                Status.PASS,
                "All canonical contract files present",
            )
        )

    # Count ONCE and hand the result to the reconciliation (the corpus may
    # hold tens of thousands of records; parsing it twice doubled runtime).
    corpus = counts.count_corpus(ws)
    counted = _counted_parts(corpus)
    unresolved = corpus.unresolved

    if corpus.undetermined:
        detail = (
            "NOT RECONCILED — the counter(s) for "
            + ", ".join(sorted(corpus.undetermined))
            + " could not be determined: "
            + _cap([f"{a.relpath} ({a.state})" for a in unresolved])
            + " (never a silent 0)"
            + (f"; the counters that were counted: {counted}" if counted else "")
        )
        results.append(_layout_row("corpus-counts", Status.FAIL, detail))
    elif corpus.status == "UNIDENTIFIED":
        detail = (
            "NOT RECONCILED — no corpus artifact could be identified or parsed: "
            + _cap(
                [
                    f"{a.relpath} ({a.state})"
                    for a in corpus.candidates
                    if a.state == counts.STATE_UNREADABLE
                ]
            )
        )
        results.append(_layout_row("corpus-counts", Status.FAIL, detail))
    elif corpus.unclassified:
        detail = (
            "corpus: "
            + corpus.summary()
            + " — UNCLASSIFIED record-bearing artifact(s): "
            + _cap([f"{a.relpath} ({a.count} records)" for a in corpus.unclassified])
            + " (these records are not represented by any declared counter)"
        )
        results.append(_layout_row("corpus-counts", Status.WARN, detail))
    elif corpus.status == "SUMMARY":
        # Corpus evidence, but only a DECLARED summary: there is no physical
        # record list to count, so this is never a physical count.
        evidence = [
            a
            for a in corpus.candidates
            if a.state in (counts.STATE_SUMMARY_ONLY, counts.STATE_CONFLICT)
        ]
        detail = (
            "corpus: DECLARED SUMMARY only — no physical record list was found: "
            + _cap([f"{a.relpath} ({a.detail})" for a in evidence])
        )
        results.append(_layout_row("corpus-counts", Status.WARN, detail))
    else:
        results.append(
            _layout_row("corpus-counts", Status.PASS, "corpus: " + corpus.summary())
        )

    if corpus.conflicts:
        detail = (
            "artifact(s) whose own summary disagrees with their own record list: "
            + _cap([f"{a.relpath} — {a.detail}" for a in corpus.conflicts])
        )
        results.append(_layout_row("corpus-conflicts", Status.WARN, detail))

    # D-1: an artifact that could not be read/understood gets its OWN line.
    # A role-less artifact never poisons the counted counters; a role-mapped
    # one only does so when its role has no counted evidence at all (that
    # case is already reported by the corpus-counts row above).
    broken = [
        a
        for a in corpus.candidates
        if a.state == counts.STATE_UNREADABLE
        or (a.state == counts.STATE_UNKNOWN_SHAPE and a.role is not None)
    ]
    if broken:
        lines = []
        for artifact in broken:
            if artifact.relpath in corpus.undetermined.get(artifact.role or "", []):
                role_note = f"maps to {artifact.role}, whose counter is undetermined"
            elif artifact.role is None:
                role_note = "maps to no counter"
            else:
                selected = corpus.selected.get(artifact.role) or []
                role_note = (
                    f"maps to {artifact.role} (that counter is determined by "
                    f"{', '.join(selected)})"
                )
            state_note = (
                "could not be read/parsed"
                if artifact.state == counts.STATE_UNREADABLE
                else "could not be understood (unexpected shape)"
            )
            lines.append(f"{artifact.relpath} ({state_note}) — {role_note}")
        detail = "artifact(s) " + _cap(lines)
        if counted:
            detail += f"; the counters that were counted: {counted}"
        results.append(_layout_row("corpus-unreadable", Status.WARN, detail))

    if corpus.provider_overlap:
        detail = (
            "the discovered_papers counter was summed from "
            + str(len(corpus.provider_evidence))
            + " provider artifact(s) ("
            + ", ".join(corpus.provider_evidence)
            + ") — provider harvests overlap, so the counter may count the same "
            "document twice; a union artifact is the authoritative count"
        )
        results.append(_layout_row("provider-evidence-overlap", Status.WARN, detail))

    manifest_path = ws / "project.json"
    if not manifest_path.is_file():
        results.append(
            _layout_row(
                "project.json-stats",
                Status.WARN,
                "project.json is missing — no reconciliation was performed (the "
                "declared counters could not be compared with the physical artifacts)",
            )
        )
        _record_state(
            state,
            performed=False,
            reconciled=False,
            status="MISSING_MANIFEST",
            detail="project.json is missing",
        )
        return results

    try:
        json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        manifest_readable = True
    except (OSError, ValueError):
        manifest_readable = False  # unreadable manifest -> warn, don't crash
    if not manifest_readable:
        results.append(
            _layout_row(
                "project.json-stats",
                Status.WARN,
                "Could not parse project.json — no reconciliation was performed",
            )
        )
        _record_state(
            state,
            performed=False,
            reconciled=False,
            status="UNREADABLE_MANIFEST",
            detail="project.json could not be parsed",
        )
        return results

    reconciliation = counts.reconcile(
        ws, corpus=corpus, additional_actual=_extra_actual_stats(ws)
    )
    details = [
        f"{m.key} declared={m.declared} actual={m.actual}"
        for m in reconciliation.mismatches
    ]
    stale = ("; declared-vs-actual: " + "; ".join(details)) if details else ""
    counted_note = f"; counted: {counted}" if counted else ""
    status = reconciliation.status
    # The physical number of records the workspace really holds (never a
    # declared number): the guard for every "0 corpus records" claim.
    physical_records = sum(a.count or 0 for a in corpus.counted)

    if status == "UNRESOLVED":
        detail = (
            "NOT RECONCILED — project.json stats could NOT be verified against "
            "the physical artifacts: "
            + _cap([f"{a.relpath} ({a.state})" for a in unresolved])
            + " — the affected counter(s) were NOT counted (never a silent 0)"
            + stale
            + counted_note
        )
        results.append(_layout_row("project.json-stats", Status.FAIL, detail))
    elif status == "UNCLASSIFIED":
        detail = (
            "NOT RECONCILED — project.json stats could NOT be verified against "
            "the physical artifacts: "
            + _cap([f"{a.relpath} ({a.count} records)" for a in corpus.unclassified])
            + " — these records are not represented by any declared counter"
            + stale
            + counted_note
        )
        results.append(_layout_row("project.json-stats", Status.FAIL, detail))
    elif status == "UNIDENTIFIED":
        detail = (
            "NOT RECONCILED — corpus artifacts exist but none could be identified "
            "or parsed, so the declared counters could not be verified"
            + stale
            + counted_note
        )
        results.append(_layout_row("project.json-stats", Status.FAIL, detail))
    elif status == "CONFLICT":
        # The corpus physically exists (it carries records) but one of its
        # artifacts contradicts itself. The physical count is used and
        # reported; the workspace is NOT reconciled and never a green verdict.
        detail = (
            "NOT RECONCILED — the corpus artifact(s) whose own summary "
            "disagrees with their own record list: "
            + _cap([f"{a.relpath} — {a.detail}" for a in corpus.conflicts])
            + f"; the physical count ({physical_records} record(s)) is used, "
            "but the corpus is not self-consistent, so the declared counters "
            "were not verified"
            + stale
            + counted_note
        )
        results.append(_layout_row("project.json-stats", Status.FAIL, detail))
    elif status == "SUMMARY":
        # A declared summary is not a physical count: it can never be a
        # verified reconciliation.
        summary_artifacts = [
            a for a in corpus.candidates if a.state == counts.STATE_SUMMARY_ONLY
        ]
        detail = (
            "NOT RECONCILED — the corpus is a DECLARED SUMMARY only (no "
            "physical record list): "
            + _cap([f"{a.relpath} ({a.detail})" for a in summary_artifacts])
            + " — a declared summary is not a verified physical count"
            + stale
            + counted_note
        )
        results.append(_layout_row("project.json-stats", Status.FAIL, detail))
    elif status == "STALE":
        detail = (
            "project.json stats disagree with the physical artifacts ("
            + "; ".join(details)
            + ")"
            + counted_note
            + " — run `nexus-scholar sync` to repair"
        )
        results.append(_layout_row("project.json-stats", Status.FAIL, detail))
    elif status == "NO_CORPUS":
        # D-2: NO_CORPUS means "this workspace holds no corpus artifact at
        # all" -- a verifiable state that reconciles against a declared 0
        # (it is NOT the same as "nothing was counted"). The claim "0 corpus
        # records" is only ever made when the physical count really is zero:
        # a record-bearing artifact (even a conflicting one) must never be
        # reported as "no corpus artifact".
        if physical_records == 0:
            detail = (
                "no corpus artifact in this workspace — the declared counters ("
                + ", ".join(
                    f"{k}={v}" for k, v in sorted(reconciliation.declared.items())
                )
                + ") reconcile against the physical state (0 corpus records)"
            )
            results.append(_layout_row("project.json-stats", Status.PASS, detail))
        else:
            detail = (
                "NOT RECONCILED — the workspace holds "
                + f"{physical_records} physical corpus record(s), so it is not "
                "a corpus-free workspace"
                + stale
                + counted_note
            )
            results.append(_layout_row("project.json-stats", Status.FAIL, detail))
    else:
        detail = (
            "project.json stats match the physical artifacts (" + corpus.summary() + ")"
        )
        results.append(_layout_row("project.json-stats", Status.PASS, detail))

    _record_state(
        state,
        performed=True,
        reconciled=reconciliation.reconciled,
        status=status,
        detail="",
        declared=dict(reconciliation.declared),
        actual=dict(reconciliation.actual),
        mismatches=[m.as_dict() for m in reconciliation.mismatches],
    )
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

    Returns ``{"checks": [{group, name, status, detail}, ...], "overall": str,
    "reconciliation": {...}}``. Overall is the worst status across checks
    (FAIL > WARN > PASS > SKIP) -- with ONE hard rule (D-3): the aggregate can
    never report ``PASS`` while the reconciliation was not performed. An
    ordinary optional ``SKIP`` sub-check stays harmless; only the
    reconciliation row can block a PASS aggregate.
    """
    ws = (workspace or Path(".")).resolve()
    checks: list[CheckResult] = []
    checks.extend(check_kits(importable_map=importable_map))
    checks.extend(check_keys(env_file))
    checks.extend(check_skills(skills_root=skills_root))
    reconciliation: dict[str, Any] = {}
    checks.extend(check_layout(ws, state=reconciliation))
    checks.extend(check_seam())
    if not reconciliation:
        # ``check_layout`` did not fill the state (it returned early, or the
        # caller stubbed it): fall back to the reconciliation row itself.
        row = next(
            (c for c in checks if (c.group, c.name) == RECONCILIATION_CHECK), None
        )
        if row is None:
            reconciliation = {
                "performed": False,
                "reconciled": False,
                "status": "NOT_APPLICABLE",
                "detail": "no reconciliation check was run (not a Nexus Scholar workspace)",
            }
        else:
            reconciliation = {
                "performed": row.status in (Status.PASS, Status.FAIL),
                "reconciled": row.status is Status.PASS,
                "status": row.status.value,
                "detail": row.detail,
            }
    else:
        reconciliation.setdefault("reconciled", False)

    overall = Status.SKIP
    for check in checks:
        if _STATUS_PRIORITY.index(check.status) < _STATUS_PRIORITY.index(overall):
            overall = check.status

    # D-3: a green aggregate must mean the declared counters were actually
    # compared with the physical artifacts.
    if not reconciliation.get("performed") and overall is Status.PASS:
        overall = Status.WARN

    report: dict[str, Any] = {
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
        "reconciliation": {
            "performed": bool(reconciliation.get("performed", False)),
            "reconciled": bool(reconciliation.get("reconciled", False)),
            "status": reconciliation.get("status", "NOT_APPLICABLE"),
            "detail": reconciliation.get("detail", ""),
        },
    }
    for key in ("declared", "actual", "mismatches"):
        if key in reconciliation:
            report["reconciliation"][key] = reconciliation[key]
    return report


def _mask_json(report: dict[str, Any]) -> str:
    """Serialize the report to JSON, guaranteeing no secret values.

    Keys-section details already carry ``***``/``Missing`` by construction
    (:func:`check_keys` never embeds values); this re-emits the check list
    verbatim so the guarantee is structurally enforced here too.
    """
    # NOTE: unlike _render_table (which re-masks), the JSON guarantee rests on
    # check_keys never placing a value in a detail string — keep it that way.
    return json.dumps(
        {
            "checks": report["checks"],
            "overall": report["overall"],
            "reconciliation": report.get("reconciliation", {}),
        },
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