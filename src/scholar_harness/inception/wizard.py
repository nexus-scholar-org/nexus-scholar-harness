from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Protocol

import typer
from rich.panel import Panel
from rich.table import Table

from ..recon.engine import ReconEngine
from .display import console, show_refraction_grid, _bounded, _INLINE_LIST_CAP
from .intent import (
    ALL_PLAYBOOKS,
    PARADIGM_KEYWORDS,
    PARADIGM_PROFILE,
    ConceptDraft,
    RQDraft,
    Survey,
    detect_leanings,
    draft_default_concepts,
    enforce_lexicon,
    make_intent,
    recommend_playbook,
    refraction_rows,
    slugify,
)
from .grounded import _run_grounded_recon, _enforce_grounded_anchors, _now_iso
from .genesis import (
    _default_matrix_dimensions,
    compile_protocol_files,
    install_workspace_support_files,
    log_genesis,
    require_uninitialized,
    scaffold_project,
    scaffold_raw_project,
    _scaffold_only_intent,
)

class Responder(Protocol):
    def text(self, message: str, default: str = "") -> str: ...
    def confirm(self, message: str, default: bool = True) -> bool: ...
    def choice(self, message: str, choices: Sequence[tuple[str, str]], default: str = "") -> str: ...
    def multi(self, message: str, choices: Sequence[str]) -> list[str]: ...
    def num_if_valid(self, raw: str) -> int | None: ...


class ConsoleResponder:
    """Terminal implementation of :class:`Responder` for TTY and piped stdin.

    Reads prompts via a single uniform line reader (``input()``). This keeps
    piped / scripted runs (CI smoke tests, ``... | scholar-harness inception``)
    aligned with interactive use, unlike ``typer.prompt`` which reads stdin
    through its own buffering and drifts on non-TTY pipes. EOF aborts cleanly.
    """

    def _read_line(self) -> str:
        try:
            return input().strip()
        except EOFError as exc:
            raise typer.Abort() from exc

    def text(self, message: str, default: str = "") -> str:
        if default:
            console.print(f"[bold cyan]• {message}[/bold cyan]  [dim](default: {default})[/dim]")
        else:
            console.print(f"• {message}")
        return self._read_line() or default

    def confirm(self, message: str, default: bool = True) -> bool:
        suffix = "[Y/n]" if default else "[y/N]"
        while True:
            console.print(f"• {message} {suffix}")
            raw = self._read_line().lower()
            if not raw:
                return default
            if raw in ("y", "yes"):
                return True
            if raw in ("n", "no"):
                return False
            console.print("[red]Invalid input: answer 'yes' or 'no'.[/red]")

    def num_if_valid(self, raw: str) -> int | None:
        raw = raw.strip()
        if not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            return None

    def choice(self, message: str, choices: Sequence[tuple[str, str]], default: str = "") -> str:
        console.print(f"[bold cyan]▸ {message}[/bold cyan]")
        for i, (label, desc) in enumerate(choices, start=1):
            console.print(f"  [bold]{i}.[/bold] {label}  [dim]— {desc}[/dim]")
        console.print("  Enter choice number:")
        while True:
            raw = self._read_line()
            if raw:
                try:
                    idx = int(raw) - 1
                    if 0 <= idx < len(choices):
                        return choices[idx][0]
                except ValueError:
                    pass
                console.print("[red]Invalid selection; retry.[/red]")
            elif default:
                return default

    def multi(self, message: str, choices: Sequence[str]) -> list[str]:
        console.print(f"[bold cyan]▸ {message}[/bold cyan]  [dim](enter comma-separated numbers or 'all' for every option)[/dim]")
        for i, label in enumerate(choices, start=1):
            console.print(f"  [bold]{i}.[/bold] {label}")
        console.print("  →")
        while True:
            raw = self._read_line().lower()
            if raw in ("",):
                return []
            if raw == "all":
                return list(choices)
            selected = []
            for chunk in raw.split(","):
                chunk = chunk.strip()
                try:
                    idx = int(chunk) - 1
                    if 0 <= idx < len(choices) and choices[idx] not in selected:
                        selected.append(choices[idx])
                except ValueError:
                    console.print(f"[dim]custom entry: {chunk}[/dim]; kept as literal")
                    selected.append(chunk)
            if selected:
                return selected
            console.print("[red]Nothing selected; retry.[/red]")


# ---------------------------------------------------------------------------
# The wizard
# ---------------------------------------------------------------------------


def run_wizard(
    responder: Responder,
    root: Path,
    *,
    genesis_timestamp: str | None = None,
    no_scaffold: bool = False,
    grounded: bool = False,
    recon_engine: ReconEngine | None = None,
    auto_select: bool = False,
    direction_id: int | None = None,
    target_dir: Path | None = None,
    init_title: str | None = None,
) -> dict:
    """Run the 4-stage Socratic inception interview and emit the protocol.

    Returns a summary dict: {intent, slug, title, playbook, paradigm,
    protocol_fingerprint, workspace_dir} where ``workspace_dir`` is set only
    when scaffolding ran (or already existed).  With ``grounded=True`` the
    summary also carries ``recon_context`` (the Step-2-4 session record).
    ``auto_select`` / ``direction_id`` (M0.7 T7.8) drive the grounded
    direction pick without an interactive prompt.

    P7.3 ``nexus-scholar init`` adaptation: when ``target_dir`` is given the
    scaffold lands in the raw folder (via :func:`scaffold_raw_project`) instead
    of ``root/workspaces/<slug>``, and ``init_title`` pre-seeds the Project
    title prompt default so ``nexus-scholar init "Title"`` carries the CLI
    argument into the interview.
    """
    root = root.resolve()
    ts = genesis_timestamp or _now_iso()

    # ---- Stage 1: raw curiosity -------------------------------------------
    console.print(Panel.fit(
        "Nexus Scholar Phase-0 Inception — the Socratic methodology interview",
        border_style="cyan",
        subtitle="From raw curiosity to a deterministic, machine-readable protocol",
    ))
    topic = responder.text(
        "Describe your raw research curiosity in one or two sentences (what do you want to investigate?)",
    )
    if not topic:
        raise typer.Exit("No research topic provided; aborting.")

    # ---- Grounded recon: probe -> distill -> validated direction -----------
    recon_context: dict | None = None
    if grounded:
        recon_engine = recon_engine if recon_engine is not None else ReconEngine()
        recon_context = _run_grounded_recon(
            responder, topic, recon_engine,
            auto_select=auto_select, direction_id=direction_id,
        )

    # ---- Stage 2: refraction grid + paradigm/playbook ----------------------
    ranked = detect_leanings(topic)
    console.print(
        "\n[bold]Latent intent scan:[/bold] " + ", ".join(f"{p} ({s})" for p, s in ranked)
    )
    show_refraction_grid(topic)

    paradigm_choices = [
        (p, profile["goal"])
        for p, profile in PARADIGM_PROFILE.items()
    ]
    recommended = ranked[0][0]
    paradigm = responder.choice(
        "Select the paradigm that best matches your intended contribution",
        paradigm_choices,
        default=recommended,
    )

    playbook_default = recommend_playbook(paradigm)
    playbook = responder.choice(
        f"Select the review playbook archetype (recommended for {paradigm}: {playbook_default})",
        [(p, "") for p in ALL_PLAYBOOKS],
        default=playbook_default,
    )
    secondary = None
    if responder.confirm("Add a secondary paradigm (mixed lens)?", default=paradigm == "Pragmatist / Mixed Methods"):
        candidates = [k for k in PARADIGM_KEYWORDS if k != paradigm]
        secondary = responder.choice("Secondary paradigm", [(c, "") for c in candidates])

    # ---- Stage 3: Socratic boundary grill ---------------------------------
    unit = responder.text("What is the atomic unit being observed or analyzed? (a model, a team, a commit diff, a crop field, a system…)")
    proof = responder.text("What specific artifact or metric would convince a top-tier peer reviewer that your finding is true?")
    out_of_scope_raw = responder.text(
        "What is strictly out of scope? (comma-separated; e.g. 'closed-source models, pre-2022 studies, non-English')"
    )
    out_of_scope = [s.strip() for s in out_of_scope_raw.split(",") if s.strip()] if out_of_scope_raw else []

    console.print(
        Panel("[bold]Lexicon enforcement[/bold]\n" + PARADIGM_PROFILE[paradigm]["lexicon"], border_style="yellow")
    )
    lexicon_warnings = enforce_lexicon(paradigm, topic)
    if lexicon_warnings:
        console.print("[bold yellow]⚠ " + " | ".join(lexicon_warnings) + "[/bold yellow]")

    languages = ["en"]
    start_year = end_year = None
    if responder.confirm("Set a publication date window and language(s)?", default=False):
        start_year = responder.num_if_valid(responder.text("Start year (blank = none): "))
        end_year = responder.num_if_valid(responder.text("End year (blank = present): "))
        langs = responder.text("ISO language codes, comma-separated (default: en): ", default="en")
        languages = [l.strip().lower() for l in langs.split(",") if l.strip()] or ["en"]

    # ---- Stage 4a: research questions ---------------------------------------
    profile = PARADIGM_PROFILE[paradigm]
    rq1_text = responder.text(
        "Refine research question RQ1 (or accept the draft)",
        default=profile["rq_template"].format(topic=topic, unit=unit, proof=proof),
    )
    rqs = [RQDraft(text=rq1_text, facet=profile["facet"], evidence=profile["evidence"])]
    if responder.confirm("Add a second research question (RQ2)?", default=False):
        rq2_text = responder.text("Draft RQ2:", default=f"How does {topic} vary by context, as evidenced by {proof}?")
        rqs.append(RQDraft(text=rq2_text, facet=profile["facet"], evidence=profile["evidence"]))

    # ---- Stage 4b: concept clusters -----------------------------------------
    if grounded and recon_context:
        # M0.3 DoD 3: grounded defaults come ONLY from pool-anchored taxonomy
        # terms (validated direction first), never from draft_default_concepts.
        default_concepts = list(recon_context.get("default_concepts") or [])
    else:
        default_concepts = draft_default_concepts(topic)
    concepts_raw = responder.text(
        "Core search concepts (comma-separated)",
        default=", ".join(default_concepts),
    )
    concepts: list[ConceptDraft] = []
    for c in [s.strip() for s in concepts_raw.split(",") if s.strip()]:
        syn_raw = responder.text(f"Synonyms / alternate terms for '{c}' (comma-separated; blank = none)")
        concepts.append(ConceptDraft(concept=c, synonyms=[s.strip() for s in syn_raw.split(",") if s.strip()]))

    if grounded and recon_context:
        # Step-5 delta-probe enforcement: every concept/synonym entering
        # core_concepts must be anchored (concepts abort, synonyms drop).
        recon_context = _enforce_grounded_anchors(concepts, recon_context, recon_engine)

    # ---- Stage 4c: screening criteria ---------------------------------------
    extra_inclusions: list[str] = []
    if responder.confirm("Add a manual inclusion criterion (e.g. 'publishes on a named public dataset')?", default=False):
        extra_inclusions.append(responder.text("Inclusion criterion:"))
    extra_exclusions: list[tuple[str, str]] = []
    if responder.confirm("Add a manual exclusion with a rejection category?", default=False):
        text = responder.text("Exclusion criterion:")
        cat = responder.text("Rejection category (e.g. LANGUAGE, INSUFFICIENT_DATA)", default="OUT_OF_SCOPE")
        extra_exclusions.append((text, cat))

    # ---- Stage 4d: extraction matrix + verification --------------------------
    matrix_dimensions: list[dict] = []
    if responder.confirm("Configure a core extraction matrix (columns for the Phase-2 RAG extractor)?", default=playbook == "DESIGN_SCIENCE"):
        default_dims = _default_matrix_dimensions(playbook, unit)
        chosen = responder.multi("Select matrix columns", [d["name"] for d in default_dims])
        matrix_dimensions = [d for d in default_dims if d["name"] in chosen]

    trust_threshold = 6.0
    if responder.confirm("Enable all Phase-4 verification checks (retraction, COI, open-science)?", default=True):
        trust_threshold = 6.0
    else:
        trust_threshold = 0.0

    # ---- Stage 4e: metadata + confirmation -----------------------------------
    title = responder.text(
        "Project title",
        default=init_title or topic.strip().rstrip("?").capitalize(),
    )
    slug = slugify(title)
    lead = responder.text(
        "Lead researcher", default="AI Agent"
    )
    venue = responder.text("Target venue type (optional)", default="")
    timeline_raw = responder.text("Timeline in weeks (blank = playbook default)")
    timeline_weeks = responder.num_if_valid(timeline_raw)

    survey = Survey(
        topic=topic,
        paradigm=paradigm,
        playbook=playbook,
        secondary_paradigm=secondary,
        unit_of_analysis=unit,
        proof=proof,
        out_of_scope=out_of_scope,
        languages=languages,
        start_year=start_year,
        end_year=end_year,
        lead_researcher=lead,
        title=title,
        venue=venue,
        timeline_weeks=timeline_weeks,
        rqs=rqs,
        concepts=concepts,
        extra_inclusions=extra_inclusions,
        extra_exclusions=extra_exclusions,
        trust_score_threshold=trust_threshold,
        matrix_dimensions=matrix_dimensions,
    )
    intent = make_intent(survey, slug, ts)

    # ---- Stage 4f: review + genesis -------------------------------------------
    console.print(Panel.fit(
        f"[bold]{title}[/bold]\n"
        f"• slug: {slug}\n• paradigm: {paradigm} ({playbook})\n• RQs: {len(rqs)}\n"
        f"• concepts: {len(concepts)}\n• inclusion: {len(intent['inclusion_criteria'])} / exclusion: {len(intent['exclusion_criteria'])}\n\n"
        f"Review the summary above; the protocol will be compiled deterministically from this intent.",
        title="Protocol Intent — Ready to Emit",
        border_style="cyan",
    ))
    if not responder.confirm("Emit protocol.json and scaffold the workspace?", default=True):
        raise typer.Exit("Inception aborted by user.")

    if no_scaffold:
        raise typer.Exit(
            "Interview complete (--no-scaffold mode); intent captured, nothing written."
        )

    if target_dir is not None:
        ws_dir = scaffold_raw_project(
            target_dir, title, slug, paradigm, [rq.text for rq in rqs]
        )
    else:
        ws_dir = scaffold_project(root, title, slug, paradigm, [rq.text for rq in rqs])
    compiled = compile_protocol_files(ws_dir, intent)
    log_genesis(
        ws_dir,
        f"Phase-0 Inception: '{title}' [{paradigm}, {playbook}] compiled protocol fingerprint "
        f"{compiled['protocol_fingerprint']}",
        recon_context=recon_context,
    )
    console.print(f"[bold green]✅ Workspace scaffolded: {ws_dir}[/bold green]")
    console.print(f"   intent.json → protocol.json ({compiled['protocol_fingerprint']})")
    console.print("   SCREENING_CRITERIA.md written. Ready for Phase-1 discovery (uv run scholar-search ...).")

    return {
        "intent": intent,
        "slug": slug,
        "title": title,
        "playbook": playbook,
        "paradigm": paradigm,
        "protocol_fingerprint": compiled["protocol_fingerprint"],
        "workspace_dir": str(ws_dir),
        "recon_context": recon_context,
    }


def inception_command(
    root: Path = typer.Option(Path("."), "--root", "-r", help="Repository root containing workspaces/ (default: current dir)"),
    no_scaffold: bool = typer.Option(False, "--no-scaffold", help="Run interview only; do not write anything"),
    grounded: bool = False,
    auto_select: bool = False,
    direction_id: int | None = None,
) -> None:
    """Launch the interactive Phase-0 Socratic inception wizard."""
    run_wizard(
        ConsoleResponder(), root,
        no_scaffold=no_scaffold, grounded=grounded,
        auto_select=auto_select, direction_id=direction_id,
    )


# ---------------------------------------------------------------------------
# P7.3: `nexus-scholar init <title>` — portable raw-folder bootstrap
# ---------------------------------------------------------------------------


def init_command(
    project_title: str,
    target_dir: Path,
    *,
    scaffold_only: bool = False,
) -> dict:
    """P7.3 ``nexus-scholar init <title>``: bootstrap a portable workspace.

    Scaffolds the canonical contract layout into ``target_dir`` (a raw folder,
    NOT the monorepo ``workspaces/<slug>``), vendors the skills as symlinks
    (copy fallback on restricted systems), writes ``.env.example`` and
    ``.mcp.json``, then either runs the full Phase-0 Socratic wizard (default,
    via ``run_wizard`` with ``target_dir=``) or emits a deterministic
    placeholder protocol (``--scaffold-only``).  Both paths end in the canonical
    ``PROJECT_INITIALIZED`` + ``GENESIS`` audit events under
    ``audit/journal.jsonl``.
    """
    target = target_dir.resolve()
    slug = slugify(project_title)
    if not slug:
        console.print("[bold red]❌ Project title must produce a non-empty slug.[/bold red]")
        raise typer.Exit(1)

    require_uninitialized(target)

    if scaffold_only:
        target.mkdir(parents=True, exist_ok=True)
        ts = _now_iso()
        intent = _scaffold_only_intent(project_title, slug, ts)
        ws_dir = scaffold_raw_project(
            target,
            project_title,
            slug,
            intent["primary_paradigm"],
            [rq["text"] for rq in intent["research_questions"]],
        )
        compiled = compile_protocol_files(ws_dir, intent)
        log_genesis(
            ws_dir,
            f"nexus-scholar init (--scaffold-only): '{project_title}' compiled "
            f"placeholder protocol fingerprint {compiled['protocol_fingerprint']}",
            agent="nexus-scholar/init",
        )
        result = {
            "intent": intent,
            "slug": slug,
            "title": project_title,
            "playbook": intent["playbook_type"],
            "paradigm": intent["primary_paradigm"],
            "protocol_fingerprint": compiled["protocol_fingerprint"],
            "workspace_dir": str(ws_dir),
            "recon_context": None,
        }
    else:
        # Full Socratic interview, emitted into the raw target dir (not
        # root/workspaces/<slug>) by reusing run_wizard's existing machinery.
        result = run_wizard(
            ConsoleResponder(),
            target,
            target_dir=target,
            init_title=project_title,
        )

    support = install_workspace_support_files(target)

    console.print(f"[bold green]✅ New Nexus Scholar workspace: {target}[/bold green]")
    if scaffold_only:
        console.print(
            "   --scaffold-only: placeholder protocol compiled; re-run without "
            "the flag to run the Socratic wizard against this folder."
        )
    console.print(
        "   skills → .agents/skills/ · env template → .env.example · "
        f"MCP wiring → {support['mcp_config'].name} ({support['mcp_config']})"
    )
    return result
