from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer
from rich.console import Console

from ..mcp_setup import _serialize, build_mcp_entry
from .display import console, _bounded
from .intent import ConceptDraft, RQDraft, Survey, draft_default_concepts, make_intent, recommend_playbook, PARADIGM_PROFILE

REPO_ROOT = Path(__file__).resolve().parents[3]

# ---------------------------------------------------------------------------
# Skill / workspace-manager source resolution (P7.3)
#
# The distribution wheel bundles the skills tree under
# ``scholar_harness_data/skills`` (a top-level data dir, never a namespace that
# could collide with a kit package).  ``nexus-scholar init`` resolves the skill
# source with the same precedence everywhere: NEXUS_SKILLS_SRC env override ->
# wheel bundle -> repository ``.agents/skills``.  The workspace-manager
# ``scripts/`` dir (init_project.py, log_event.py) is located through the same
# resolver so ``inception`` and ``init`` keep the audit convention in the wheel
# env, where the repo-relative path does not exist.
# ---------------------------------------------------------------------------

SKILL_SOURCE_ENV = "NEXUS_SKILLS_SRC"
_BUNDLED_SKILLS_PACKAGE = "scholar_harness_data"
_BUNDLED_SKILLS_REL = "skills"

# Strong canonical markers: a folder holding any of these is already a Nexus
# Scholar workspace and ``init`` refuses to touch it (second-run clobber guard).
INIT_MARKERS = (
    "project.json",
    "protocol.json",
    "intent.json",
    "audit/journal.jsonl",
    ".mcp.json",
)

_LOGIMPORT_NAME = "workspace_manager_log_event"
_log_module_ref: Any | None = None
_log_module_tried = False


def _bundled_skills_root() -> Path | None:
    """Locate the skills tree bundled inside the installed distribution wheel."""
    try:
        spec = importlib.util.find_spec(_BUNDLED_SKILLS_PACKAGE)
    except (ImportError, ValueError):
        return None
    for location in getattr(spec, "submodule_search_locations", None) or []:
        candidate = Path(location) / _BUNDLED_SKILLS_REL
        if candidate.is_dir():
            return candidate
    return None


def resolve_skills_root() -> Path | None:
    """Resolve the skills source root (a dir of ``<name>/SKILL.md`` children).

    Precedence (P7.3): ``NEXUS_SKILLS_SRC`` env override, then the skills
    bundled inside the installed wheel, then the repository checkout's
    ``.agents/skills``.
    """
    env = os.environ.get(SKILL_SOURCE_ENV)
    if env:
        candidate = Path(env).expanduser().resolve()
        if candidate.is_dir():
            return candidate
    bundled = _bundled_skills_root()
    if bundled is not None:
        return bundled
    repo = REPO_ROOT / ".agents" / "skills"
    return repo if repo.is_dir() else None


def resolve_workspace_manager_scripts() -> Path | None:
    """Locate the workspace-manager ``scripts/`` dir (wheel-portable)."""
    skills = resolve_skills_root()
    if skills is None:
        return None
    candidate = skills / "workspace-manager" / "scripts"
    return candidate if candidate.is_dir() else None


def _load_log_module():
    """Load ``log_event.py`` (workspace-manager) in-process, cached.

    Mirrors the pattern in ``scholar_harness.console.api.audit`` but resolves
    the script through the wheel-portable skills resolver and registers the
    module under a distinct name so a wheel env and the harness console can
    coexist.
    """
    global _log_module_ref, _log_module_tried
    if _log_module_tried:
        return _log_module_ref
    _log_module_tried = True
    scripts = resolve_workspace_manager_scripts()
    if scripts is None:
        return None
    script = scripts / "log_event.py"
    if not script.is_file():
        return None
    try:
        spec = importlib.util.spec_from_file_location(_LOGIMPORT_NAME, script)
        if spec is None or spec.loader is None:
            return None
        module = importlib.util.module_from_spec(spec)
        sys.modules[_LOGIMPORT_NAME] = module
        spec.loader.exec_module(module)
        if not hasattr(module, "log_project_event"):
            return None
        _log_module_ref = module
    except (ImportError, OSError, TypeError, ValueError, SyntaxError, AttributeError):
        _log_module_ref = None
    return _log_module_ref


def _log_project_event(
    ws_dir: Path,
    *,
    action: str,
    agent: str,
    description: str,
    inputs: list[str] | None = None,
    outputs: list[str] | None = None,
    parameters: dict | None = None,
    status: str = "SUCCESS",
) -> None:
    """Append a canonical audit event through workspace-manager's log_event.py.

    Best effort: when the workspace-manager skill is unreachable (no wheel
    bundle / no repo checkout) the event is skipped with a warning instead of
    failing the command.
    """
    module = _load_log_module()
    if module is None:
        console.print(
            f"[yellow]\u26a0 warning: workspace-manager log_event.py unavailable; "
            f"{action} event not logged[/yellow]"
        )
        return
    try:
        module.log_project_event(
            ws_dir,
            action,
            agent,
            description,
            inputs=inputs,
            outputs=outputs,
            parameters=parameters,
            status=status,
        )
    except (OSError, TypeError, ValueError) as exc:  # pragma: no cover - best effort
        console.print(
            f"[yellow]\u26a0 warning: {action} event not logged ({exc})[/yellow]"
        )






# ---------------------------------------------------------------------------
# Responder protocol: abstraction over every interactive prompt
# ---------------------------------------------------------------------------


def compile_protocol_files(ws_dir: Path, intent: dict) -> dict[str, str]:
    """Compile intent.json → protocol.json + SCREENING_CRITERIA.md via the kit, deterministically.

    Returns {"protocol_fingerprint": ..., "protocol_path": ..., "criteria_path": ...}.
    """
    try:
        from scholar_protocol.canonical import canonical_fingerprint, canonical_json
        from scholar_protocol.compiler import compile_protocol
        from scholar_protocol.intent import IntentPacket
        from scholar_protocol.render import render_screening_criteria
    except ImportError as exc:  # pragma: no cover - kit dependency missing
        raise typer.Exit("scholar-protocol-kit is not installed; run scripts/install_plugins.py first") from exc

    intent_path = ws_dir / "intent.json"
    intent_path.write_text(json.dumps(intent, indent=2, ensure_ascii=False), encoding="utf-8")

    compiled = compile_protocol(IntentPacket.model_validate(intent))
    (ws_dir / "protocol.json").write_bytes(canonical_json(compiled))
    (ws_dir / "SCREENING_CRITERIA.md").write_text(render_screening_criteria(compiled), encoding="utf-8")
    return {
        "protocol_fingerprint": canonical_fingerprint(compiled),
        "protocol_path": str(ws_dir / "protocol.json"),
        "criteria_path": str(ws_dir / "SCREENING_CRITERIA.md"),
    }


def scaffold_project(ws_root: Path, title: str, slug: str, paradigm: str, rqs: list[str]) -> Path:
    """Scaffold ``workspaces/<slug>/`` by delegating to workspace-manager's init_project.py."""
    ws_root = ws_root.resolve()
    scripts = resolve_workspace_manager_scripts()
    if scripts is None or not (scripts / "init_project.py").is_file():
        raise typer.Exit(
            "workspace-manager init_project.py not found "
            "(NEXUS_SKILLS_SRC / wheel bundle / repo .agents/skills unavailable)"
        )
    cmd = [
        sys.executable, str(scripts / "init_project.py"), title,
        "--slug", slug,
        "--paradigm", paradigm,
        "--root", str(ws_root),
    ]
    for rq in rqs:
        cmd += ["--rq", rq]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8")
    except subprocess.CalledProcessError as exc:
        raise typer.Exit(f"init_project.py failed:\\n{exc.stderr or exc.stdout}") from exc
    return ws_root / "workspaces" / slug


def scaffold_raw_project(
    ws_dir: Path,
    title: str,
    slug: str,
    paradigm: str,
    rqs: list[str],
    *,
    agent: str = "workspace-manager",
) -> Path:
    """Scaffold the canonical contract layout directly INTO ``ws_dir`` (raw folder).

    P7.3 ``nexus-scholar init`` targets any empty folder, so unlike
    :func:`scaffold_project` this variant writes into the caller-chosen
    directory instead of the monorepo ``<root>/workspaces/<slug>`` layout.  It
    mirrors the workspace-manager ``init_project.py`` manifest byte-for-byte
    (same field order and defaults), logs the canonical ``PROJECT_INITIALIZED``
    audit event and refreshes ``INDEX.md`` through log_event.py -- the exact
    journal convention the wizard produces in the monorepo layout.
    """
    ws_dir = ws_dir.resolve()
    for sub in ("audit", "literature", "pdfs", "extracted", "synthesis", "exports"):
        (ws_dir / sub).mkdir(parents=True, exist_ok=True)

    now = datetime.now(UTC).isoformat()
    manifest = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "project_id": slug,
        "title": title,
        "description": f"Systematic literature review for {title}",
        "created_at": now,
        "updated_at": now,
        "status": "active",
        "paradigm": paradigm,
        "research_questions": list(rqs),
        "keywords": [],
        "stats": {
            "discovered_papers": 0,
            "verified_papers": 0,
            "downloaded_pdfs": 0,
            "extracted_markdowns": 0,
        },
    }
    (ws_dir / "project.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    notes = ws_dir / "synthesis" / "literature_review.md"
    if not notes.exists():
        rq_section = "\\n".join(
            f"- **{rq}**"
            for rq in (rqs or ["RQ1: Primary research questions to be formulated."])
        )
        notes.write_text(
            f"# Literature Review: {title}\\n\\n"
            f"## Objectives & Research Questions\\n{rq_section}\\n\\n"
            f"## Findings & Synthesis\\n*To be generated from extracted papers.*\\n",
            encoding="utf-8",
        )

    _log_project_event(
        ws_dir,
        action="PROJECT_INITIALIZED",
        agent=agent,
        description=f"Initialized research project workspace for '{title}'",
        inputs=None,
        outputs=["project.json", "synthesis/literature_review.md"],
        parameters={"title": title, "slug": slug, "rqs": list(rqs)},
    )
    return ws_dir





def log_genesis(
    ws_dir: Path,
    description: str,
    *,
    recon_context: dict | None = None,
    agent: str = "scholar-harness/inception",
) -> None:
    """Record the GENESIS audit event via workspace-manager's log_event.py.

    The full ``recon_context`` (which can hold hundreds of anchored terms on a
    rich pool) is persisted verbatim to ``audit/recon_context.json``; the
    description embeds only a bounded inline summary of the provenance fields
    plus a ``provenance_file`` pointer.  Embedding the raw dict inline used to
    overflow the OS command line when driving ``log_event.py`` as a subprocess
    (observed on Windows: ``WinError 206``).
    """
    outputs: list[Path] = [ws_dir / "protocol.json", ws_dir / "SCREENING_CRITERIA.md"]
    if recon_context:
        rc_file = ws_dir / "audit" / "recon_context.json"
        rc_file.parent.mkdir(parents=True, exist_ok=True)
        rc_file.write_text(json.dumps(recon_context, ensure_ascii=False, indent=2), encoding="utf-8")
        anchors = _bounded(recon_context.get("anchor_dois") or [])
        concepts = _bounded(recon_context.get("default_concepts") or [])
        summary = {
            "session_id": recon_context.get("session_id"),
            "cache_keys": recon_context.get("cache_keys") or [],
            "pool_sizes": recon_context.get("pool_sizes") or [],
            "direction": recon_context.get("direction"),
            "concept": recon_context.get("concept"),
            "anchor_dois": anchors["values"],
            "anchor_dois_truncated": anchors["truncated_count"],
            "default_concepts": concepts["values"],
            "default_concepts_truncated": concepts["truncated_count"],
            "anchored_term_count": len(recon_context.get("anchored_terms") or {}),
            "provenance_file": str(rc_file.relative_to(ws_dir)).replace("\\", "/"),
        }
        description = (
            f"{description} recon_context="
            + json.dumps(summary, ensure_ascii=False, separators=(",", ":"))
        )
        outputs.append(rc_file)
    _log_project_event(
        ws_dir,
        action="GENESIS",
        agent=agent,
        description=description,
        inputs=[str(ws_dir / "intent.json")],
        outputs=[str(p) for p in outputs],
    )



def _default_matrix_dimensions(playbook: str, unit: str) -> list[dict]:
    """Suggested extraction matrix columns per playbook archetype."""
    base: dict[str, dict] = {
        "sample_size": {
            "id": "sample_size", "name": "Sample Size",
            "description": f"Number of {unit} sampled / evaluated",
            "target_section_category": "methodology", "data_type": "numeric",
            "required": True, "fallback_value": "Not Reported",
        },
        "key_findings": {
            "id": "key_findings", "name": "Key Findings",
            "description": "Summary of the study's primary reported findings",
            "target_section_category": "results_empirical", "data_type": "free_text",
            "required": False, "fallback_value": "Not Reported",
        },
        "limitations": {
            "id": "limitations", "name": "Limitations",
            "description": "Author-reported limitations and caveats",
            "target_section_category": "discussion_limitations", "data_type": "free_text",
            "required": False, "fallback_value": "Not Reported",
        },
    }
    if playbook == "DESIGN_SCIENCE":
        return [
            base["sample_size"],
            {
                "id": "performance", "name": "Performance Metric",
                "description": "Primary accuracy/quality metric with value (e.g. mIoU, F1, latency ms)",
                "target_section_category": "results_empirical", "data_type": "numeric",
                "required": True, "fallback_value": "Not Reported",
            },
            {
                "id": "artifact", "name": "Artifact & Stack",
                "description": "Implemented artifact, architecture and runtime stack",
                "target_section_category": "methodology", "data_type": "free_text",
                "required": False, "fallback_value": "Not Reported",
            },
        ]
    return [base["sample_size"], base["key_findings"], base["limitations"]]


def require_uninitialized(target: Path) -> None:
    """Refuse to re-initialize a folder that already carries Nexus markers.

    ``nexus-scholar init`` clobbers nothing -- it only *adds* the canonical
    contract layout -- but a previous ``init``/inception run leaves strong
    markers and a second run would silently overwrite a live protocol.  The
    refusal rule: any of :data:`INIT_MARKERS` already present under ``target``
    blocks a new init (exit 1, nothing written).
    """
    target = target.resolve()
    if not target.exists():
        return
    if target.is_file():
        console.print(
            f"[bold red]❌ Refusing to initialize {target}: path exists and is a "
            f"file, not a directory.[/bold red]"
        )
        raise typer.Exit(1)
    present = [marker for marker in INIT_MARKERS if (target / marker).exists()]
    if present:
        console.print(
            f"[bold red]❌ Refusing to initialize {target}: already contains Nexus "
            f"Scholar scaffold marker(s): {', '.join(present)}.[/bold red]"
        )
        console.print(
            "[dim]Run `nexus-scholar status --workspace <dir>` (or a pipeline) against "
            "the existing workspace, or choose a new --dir.[/dim]"
        )
        raise typer.Exit(1)


def install_skills(source: Path | None, dest_root: Path) -> list[dict]:
    """Vendor every ``<name>/SKILL.md`` skill from ``source`` into ``dest_root``.

    Each skill directory is symlinked *whole* (SKILL.md plus its
    ``references/`` and ``scripts/`` companions) so workspaces never drift from
    the shipped skill version and every helper a skill embeds stays reachable.
    One link per skill keeps the workspace lightweight.  On platforms where
    directory symlinks need privileges the caller does not have (Windows
    without admin/Developer Mode), ``os.symlink`` raises and the skill is
    copied instead; the record's ``mode`` reports ``"symlink"`` vs ``"copy"``
    so callers can surface the fallback.
    """
    dest_root.mkdir(parents=True, exist_ok=True)
    records: list[dict] = []
    if source is None or not source.is_dir():
        return records
    for skill_dir in sorted(
        d for d in source.iterdir() if d.is_dir() and (d / "SKILL.md").is_file()
    ):
        dest = dest_root / skill_dir.name
        if dest.exists() or dest.is_symlink():
            records.append(
                {"name": skill_dir.name, "mode": "existing", "source": str(skill_dir.resolve())}
            )
            continue
        mode = "symlink"
        try:
            dest.symlink_to(skill_dir.resolve(), target_is_directory=True)
        except (OSError, NotImplementedError):
            shutil.copytree(skill_dir, dest)
            mode = "copy"
        records.append(
            {"name": skill_dir.name, "mode": mode, "source": str(skill_dir.resolve())}
        )
    return records


def write_env_example(ws_dir: Path) -> Path:
    """Write the ``.env.example`` template (placeholders only, never secrets)."""
    content = (
        "# Nexus Scholar — environment template.\n"
        "# Copy this file to `.env` and fill in real values; the harness reads `.env`\n"
        "# from where you run the kit commands (search settings use the SCHOLAR_ prefix).\n"
        "# Secrets are NEVER written into project.json, protocol.json or audit/ — they\n"
        "# live only in your local, git-ignored `.env`.\n"
        "\n"
        "# --- Academic search providers (scholar-search-kit; SCHOLAR_* prefix) --------\n"
        "SCHOLAR_MAILTO=you@example.com\n"
        "SCHOLAR_OPENALEX_KEY=\n"
        "SCHOLAR_S2_KEY=\n"
        "\n"
        "# --- Model provider keys (OPTIONAL; LLM-backed screening / claim checks) -----\n"
        "OPENAI_API_KEY=\n"
        "ANTHROPIC_API_KEY=\n"
        "GEMINI_API_KEY=\n"
        "\n"
        "# --- Nexus runtime (harness) --------------------------------------------------\n"
        "# Grounded-recon cache root (CWD-independent); override per machine.\n"
        "NEXUS_RECON_ROOT=.cache/inception_recon\n"
        "# Optional skill source root for `nexus-scholar init` (directory of\n"
        "# <skill-name>/SKILL.md). Defaults to the wheel bundle, else the repo checkout.\n"
        "NEXUS_SKILLS_SRC=\n"
    )
    path = ws_dir / ".env.example"
    path.write_text(content, encoding="utf-8")
    return path


def write_mcp_json(ws_dir: Path) -> Path:
    """Write ``.mcp.json`` wiring ``scholar-agent --workspace <dir>`` (Tier 3).

    Shares the P7.4 :func:`~.mcp_setup.build_mcp_entry` builder with
    ``nexus-scholar setup-mcp`` so the emitted entry is byte-identical
    (the absolute, baked-in workspace path is a P7.1 hard requirement:
    ``${workspaceFolder}`` only expands in Cursor/Windsurf/VS Code, not in
    Claude Desktop or a terminal-launched MCP server).
    """
    ws_dir = ws_dir.resolve()
    config = {"mcpServers": {"nexus-scholar": build_mcp_entry(ws_dir)}}
    path = ws_dir / ".mcp.json"
    path.write_bytes(_serialize(config))
    return path


def install_workspace_support_files(target: Path) -> dict:
    """Vendor skills, ``.env.example`` and ``.mcp.json`` into ``target`` (P7.3).

    Returns {"skills_source", "skill_records", "env_example", "mcp_config"} and
    reports per-skill symlink vs copy-fallback on the console.
    """
    target = target.resolve()
    skills_root = resolve_skills_root()
    if skills_root is None:
        console.print(
            "[yellow]\u26a0 warning: no skill source found "
            "(NEXUS_SKILLS_SRC / wheel bundle / repo .agents/skills); "
            ".agents/skills left empty[/yellow]"
        )
    records = install_skills(skills_root, target / ".agents" / "skills") if skills_root else []
    for rec in records:
        if rec["mode"] == "symlink":
            console.print(f"   [dim]skill {rec['name']}: symlinked from {rec['source']}[/dim]")
        elif rec["mode"] == "copy":
            console.print(
                f"   [dim]skill {rec['name']}: COPIED (symlink unavailable on this "
                f"system; enable Developer Mode, delete the workspace, and re-run "
                f"`nexus-scholar init` to symlink instead)[/dim]"
            )
        else:
            console.print(f"   [dim]skill {rec['name']}: kept existing[/dim]")
    env = write_env_example(target)
    mcp = write_mcp_json(target)
    return {
        "skills_source": skills_root,
        "skill_records": records,
        "env_example": env,
        "mcp_config": mcp,
    }


def _scaffold_only_intent(title: str, slug: str, genesis_timestamp: str) -> dict:
    """Deterministic placeholder intent for ``init --scaffold-only``.

    No interview runs in scaffold-only mode, so the intent is derived from the
    title alone through the very same :func:`make_intent` pipeline the wizard
    uses (neutral Positivist / PRISMA-SLR default, matching the wizard's
    deterministic lean when a title carries no paradigm keywords).  The user
    can re-run the full Socratic wizard later.
    """
    paradigm = "Positivist"
    playbook = recommend_playbook(paradigm)
    profile = PARADIGM_PROFILE[paradigm]
    unit = "the target population or system"
    proof = profile["evidence"]
    rq_text = profile["rq_template"].format(topic=title, unit=unit, proof=proof)
    concepts = [ConceptDraft(concept=c) for c in draft_default_concepts(title)]
    survey = Survey(
        topic=title,
        paradigm=paradigm,
        playbook=playbook,
        secondary_paradigm=None,
        unit_of_analysis=unit,
        proof=proof,
        out_of_scope=[],
        languages=["en"],
        start_year=None,
        end_year=None,
        lead_researcher="AI Agent",
        title=title,
        venue="",
        timeline_weeks=None,
        rqs=[RQDraft(text=rq_text, facet=profile["facet"], evidence=profile["evidence"])],
        concepts=concepts,
        extra_inclusions=[],
        extra_exclusions=[],
        trust_score_threshold=6.0,
        matrix_dimensions=[],
    )
    return make_intent(survey, slug, genesis_timestamp)


