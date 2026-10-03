"""Helper script to initialize a standardized research project workspace."""

import argparse
import json
import re
import secrets
from datetime import datetime, timezone
from pathlib import Path

# Registered workspace identity (Contract v1 ``IdentifierKind.WORKSPACE``). The
# frozen registry admits exactly one registered form, ``WSP-<opaque>``, so a human
# slug is not a workspace identity and every typed surface refuses it. Minted once
# at initialization and recorded as ``registered_workspace_id``; ``project_id``
# stays the human label.
#
# This restates ``mint_registered_workspace_id``,
# ``validate_registered_workspace_id``, and ``recorded_or_minted_workspace_id``
# from ``src/scholar_harness/inception/genesis.py`` rather than importing them,
# because this script runs standalone (``python init_project.py``) and from the
# distribution wheel's bundled skills copy, where the harness package is not
# importable. ``RegisteredWorkspaceIdentityMissingError`` is the same single typed
# refusal the harness raises, restated for the same reason.
#
# ``tests/inception/test_registered_workspace_id.py`` runs BOTH creators over the
# same cases (valid recorded, absent, non-``WSP-``, non-hex ``WSP-``, corrupt JSON,
# missing file), so this copy cannot drift from the harness one.
_REGISTERED_WORKSPACE_ID = re.compile(r"^WSP-[0-9a-f]{32}$")


class RegisteredWorkspaceIdentityMissingError(RuntimeError):
    """A recorded workspace identity is absent, unusable, or not registered.

    Restatement of the harness's single typed refusal for workspace identity; see
    ``scholar_harness.inception.genesis.RegisteredWorkspaceIdentityMissingError``.
    """


def mint_registered_workspace_id() -> str:
    """Return a fresh registered workspace identity: ``WSP-<32 hex>`` from the OS CSPRNG."""
    candidate = f"WSP-{secrets.token_hex(16)}"
    if not _REGISTERED_WORKSPACE_ID.fullmatch(candidate):  # pragma: no cover
        raise RegisteredWorkspaceIdentityMissingError(
            f"minted workspace id is not registered: {candidate!r}"
        )
    return candidate


def validate_registered_workspace_id(value: str) -> str:
    """Return ``value`` if it is ``WSP-<32 lowercase hex>``, else refuse naming it."""
    candidate = value.strip()
    if not _REGISTERED_WORKSPACE_ID.fullmatch(candidate):
        raise RegisteredWorkspaceIdentityMissingError(
            f"{value!r} is not a registered workspace identity: the registered "
            f"form is WSP-<32 lowercase hex>. Fix: replace the recorded value "
            f"with a registered identity, or re-create the workspace."
        )
    return candidate


def recorded_or_minted_workspace_id(project_dir: Path) -> str:
    """Resolve a workspace's identity under one fail-closed policy.

    Minting is permitted only when the workspace has no recorded identity to lose:
    a missing ``project.json``, or a readable manifest without the field. Every
    other case is a typed refusal rather than a fresh identity, because silently
    minting over recorded state is silent re-identification -- artifacts already
    accepted under the old id would no longer share a workspace.

    The policy, identical in both ``project.json`` creators:

    * no manifest / manifest without ``registered_workspace_id`` -> mint;
    * recorded value that is not ``WSP-<32 hex>`` -> refuse, naming the value;
    * unreadable, corrupt, or non-object ``project.json`` -> refuse, naming the
      path and the corruption.
    """
    manifest_path = project_dir / "project.json"
    if not manifest_path.is_file():
        return mint_registered_workspace_id()

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RegisteredWorkspaceIdentityMissingError(
            f"cannot read the recorded workspace identity from {manifest_path}: "
            f"{exc}. Repair or re-create project.json rather than minting over "
            f"recorded state (nexus-scholar init <title>)."
        ) from exc
    if not isinstance(manifest, dict):
        raise RegisteredWorkspaceIdentityMissingError(
            f"cannot read the recorded workspace identity from {manifest_path}: "
            f"it is not a JSON object. Repair or re-create project.json rather "
            f"than minting over recorded state."
        )

    recorded = manifest.get("registered_workspace_id")
    if recorded is None:
        # No identity has ever been recorded for this workspace, so there is no
        # lineage to destroy and minting creates rather than replaces one.
        return mint_registered_workspace_id()
    if not isinstance(recorded, str):
        raise RegisteredWorkspaceIdentityMissingError(
            f"{manifest_path} records 'registered_workspace_id' as "
            f"{type(recorded).__name__} ({recorded!r}) rather than a string. "
            f"Fix: replace it with a registered identity of the form "
            f"WSP-<32 lowercase hex>."
        )
    return validate_registered_workspace_id(recorded)

def slugify(text: str) -> str:
    """Converts a title to a clean URL/filesystem friendly slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text).strip("-")

def init_project(
    workspace_root: Path,
    title: str,
    slug: str | None = None,
    description: str = "",
    research_questions: list[str] | None = None,
    keywords: list[str] | None = None,
    paradigm: str = ""
) -> Path:
    project_slug = slug or slugify(title)
    project_dir = workspace_root / "workspaces" / project_slug

    # Subdirectories
    subdirs = ["audit", "literature", "pdfs", "extracted", "synthesis", "exports"]
    for sub in subdirs:
        (project_dir / sub).mkdir(parents=True, exist_ok=True)

    # Initial project.json manifest
    now = datetime.now(timezone.utc).isoformat()
    manifest = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "project_id": project_slug,
        "registered_workspace_id": recorded_or_minted_workspace_id(project_dir),
        "title": title,
        "description": description or f"Systematic literature review for {title}",
        "created_at": now,
        "updated_at": now,
        "status": "active",
        "paradigm": paradigm,
        "research_questions": research_questions or [],
        "keywords": keywords or [],
        "stats": {
            "discovered_papers": 0,
            "verified_papers": 0,
            "downloaded_pdfs": 0,
            "extracted_markdowns": 0
        }
    }

    manifest_path = project_dir / "project.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    # Create an initial synthesis notes template
    notes_path = project_dir / "synthesis" / "literature_review.md"
    if not notes_path.exists():
        rq_section = "\n".join([f"- **{rq}**" for rq in (research_questions or ["RQ1: Primary research questions to be formulated."])])
        notes_content = f"# Literature Review: {title}\n\n## Objectives & Research Questions\n{rq_section}\n\n## Findings & Synthesis\n*To be generated from extracted papers.*\n"
        notes_path.write_text(notes_content, encoding="utf-8")

    # Import logger if available to log event and build INDEX.md
    try:
        from log_event import log_project_event
        log_project_event(
            project_path_or_slug=project_dir,
            action="PROJECT_INITIALIZED",
            agent_or_tool="workspace-manager",
            description=f"Initialized research project workspace for '{title}'",
            outputs=["project.json", "synthesis/literature_review.md"],
            parameters={"title": title, "slug": project_slug, "rqs": research_questions or []}
        )
    except Exception:
        pass

    print(f"Initialized research project: {project_dir}")
    return project_dir

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize a new research project workspace.")
    parser.add_argument("title", help="Human-readable project title")
    parser.add_argument("--slug", "-s", help="Optional custom project directory slug")
    parser.add_argument("--description", "-d", default="", help="Project description")
    parser.add_argument("--paradigm", "-p", default="", help="Epistemological paradigm (e.g., 'Design Science & Quantitative Benchmark')")
    parser.add_argument("--rq", action="append", help="Research question (can be repeated)")
    parser.add_argument("--keyword", "-k", action="append", help="Project keyword (can be repeated)")
    parser.add_argument("--root", default=".", help="Root repository directory (default: current directory)")

    args = parser.parse_args()
    init_project(
        workspace_root=Path(args.root),
        title=args.title,
        slug=args.slug,
        description=args.description,
        paradigm=args.paradigm,
        research_questions=args.rq,
        keywords=args.keyword
    )
