"""Interactive Inception CLI: the Socratic methodology interview (Phase 0).

Implements the 4-stage inception architecture from
``docs/architecture/phase_0/04_socratic_inception_protocol.md`` as a terminal wizard:

  Stage 1  Latent intent mining   — keyword-scored paradigm orientation
  Stage 2  4-way refraction grid  — paradigm + playbook selection (rich panel)
  Stage 3  Socratic boundary grill— unit of analysis, gold-standard proof,
           exclusion boundary, lexicon enforcement
  Stage 4  Protocol emission      — intent.json → compiler → protocol.json,
           SCREENING_CRITERIA.md, workspace genesis + GENESIS audit event

The wizard is *responder-driven*: every interaction goes through the
:class:`Responder` protocol so the whole flow can be scripted in tests
(and any future GUI/LLM front-end) without a live terminal.
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .mcp_setup import _serialize, build_mcp_entry
from .recon.engine import ReconEngine

REPO_ROOT = Path(__file__).resolve().parents[2]
console = Console()

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
# Stage 1: paradigm lexicon & latent-intent mining
# ---------------------------------------------------------------------------

POSITIVIST_KEYWORDS = (
    "impact", "measure", "effect size", "correlation", "optimize", "benchmark",
    "statistically compare", "predict", "quantify", "statistically significant",
    "p-value", "efficacy", "performance", "accuracy", "metric",
)
INTERPRETIVIST_KEYWORDS = (
    "perceive", "experience", "understand", "lived experience", "cultural nuance",
    "identity", "sense-making", "meaning", "qualitative", "attitude", "belief",
    "stakeholder", "narrative",
)
DESIGN_SCIENCE_KEYWORDS = (
    "build", "construct", "prototype", "architecture", "pipeline", "harness",
    "benchmark suite", "implement", "engineering", "efficiency", "throughput",
    "frame rate", "latency", "embedded", "artifact", "system",
)
PRAGMATIST_KEYWORDS = (
    "tradeoffs", "organizational friction", "under what conditions",
    "practical deployment", "socio-technical", "mixed methods", "feasibility",
    "adoption", "cost", "real-world",
)

PARADIGM_KEYWORDS: dict[str, tuple[str, ...]] = {
    "Positivist": POSITIVIST_KEYWORDS,
    "Interpretivist": INTERPRETIVIST_KEYWORDS,
    "Design Science": DESIGN_SCIENCE_KEYWORDS,
    "Pragmatist / Mixed Methods": PRAGMATIST_KEYWORDS,
}

# Recommended playbook archetype per paradigm (Stage 2 default, user can override).
PLAYBOOK_RECOMMENDATION: dict[str, str] = {
    "Positivist": "PRISMA_SLR",
    "Interpretivist": "SCOPING_REVIEW",
    "Design Science": "DESIGN_SCIENCE",
    "Pragmatist / Mixed Methods": "SCOPING_REVIEW",
}

ALL_PLAYBOOKS = (
    "PRISMA_SLR",
    "SCOPING_REVIEW",
    "RAPID_EVIDENCE",
    "DESIGN_SCIENCE",
    "STUDENT_DISSERTATION",
)

# Trustworthiness / rigor frameworks wired to the protocol-kit presets.
TRUSTWORTHINESS_FRAMEWORK: dict[str, str] = {
    "PRISMA_SLR": "PRISMA 2020",
    "SCOPING_REVIEW": "JBI Scoping Review Framework",
    "RAPID_EVIDENCE": "REA Guidelines",
    "DESIGN_SCIENCE": "Hevner DSR",
    "STUDENT_DISSERTATION": "APA / JBI Adapted Guidelines",
}

# Per-paradigm sample-RQ template and required evidence (used in the grid + drafting).
PARADIGM_PROFILE: dict[str, dict] = {
    "Positivist": {
        "goal": "Measure objective, generalizable statistical effects.",
        "evidence": "Quantitative telemetry, controlled benchmarks / A/B logs",
        "facet": "quantitative_effects",
        "negative_exclusions": "Subjective emotional state as primary proof; non-replicable anecdotes.",
        "lexicon": (
            "Enforce statistical power, control groups, effect sizes, and preregistration "
            "vocabulary. Flag 'insight/anecdote' claims without a measured comparison."
        ),
        "rq_template": "What is the statistically significant effect/impact of {topic} on {unit}, as quantified by {proof}?",
    },
    "Interpretivist": {
        "goal": "Understand human meaning, perceptions, and identity.",
        "evidence": "Semi-structured interviews; thematic coding; contextual inquiry transcripts",
        "facet": "lived_experience",
        "negative_exclusions": "Statistical p-values, claims of global generalizability, arbitrary numerical scoring.",
        "lexicon": (
            "Use Lincoln & Guba trustworthiness vocabulary: Credibility, Transferability, "
            "Dependability, Confirmability. Flag Positivist terms ('internal validity', "
            "'sample randomization', 'p-value')."
        ),
        "rq_template": "How do {unit} perceive and experience {topic}, and what meaning do they attribute to it?",
    },
    "Design Science": {
        "goal": "Engineer a novel artifact that solves an operational utility problem.",
        "evidence": "Benchmark suites, ablation studies, latency profiling, error-rate delta",
        "facet": "artifact_performance",
        "negative_exclusions": "Mere descriptive opinion without an evaluated computational artifact.",
        "lexicon": (
            "Use DSR rigor vocabulary: artifact, design propositions, evaluation criteria, "
            "utility. Flag purely narrative claims without an implemented, evaluated artifact."
        ),
        "rq_template": "Can a novel {topic} artifact achieve {proof} for {unit}, compared to a defined baseline?",
    },
    "Pragmatist / Mixed Methods": {
        "goal": "Solve a socio-technical problem by triangulating metrics with narratives.",
        "evidence": "Triangulated telemetry data + interview coding",
        "facet": "socio_technical_conditions",
        "negative_exclusions": "Purely theoretical models without empirical grounding in practice.",
        "lexicon": (
            "Justify the mixing logic; state which claims each strand (numeric vs narrative) "
            "answers, and how they triangulate."
        ),
        "rq_template": "Under what practical conditions does {topic} improve {unit} (quantified by {proof}), and what barriers emerge in real-world deployment?",
    },
}

# Positivist vocabulary that would violate Interpretivist lexicon (enforced flagging).
INTERPRETIVIST_FORBIDDEN = (
    "statistically significant", "p-value", "internal validity", "sample randomization",
    "effect size", "generalizability",
)


def detect_leanings(topic: str) -> list[tuple[str, int]]:
    """Keyword-score the raw curiosity prompt across the four paradigms (Stage 1).

    Returns paradigm names sorted by descending score (ties by fixed order).
    """
    text = topic.lower()
    scores: dict[str, int] = {}
    for paradigm, kws in PARADIGM_KEYWORDS.items():
        scores[paradigm] = sum(1 for kw in kws if kw in text)
    order = list(PARADIGM_KEYWORDS)
    return sorted(scores.items(), key=lambda kv: (-kv[1], order.index(kv[0])))


def recommend_playbook(paradigm: str) -> str:
    """Map a paradigm to its default playbook archetype."""
    return PLAYBOOK_RECOMMENDATION.get(paradigm, "PRISMA_SLR")


def enforce_lexicon(paradigm: str, *texts: str) -> list[str]:
    """Return pseudo-violation warnings when Interpretivist text uses Positivist terms."""
    if paradigm != "Interpretivist":
        return []
    haystack = " ".join(texts).lower()
    return [f"Flagged Positivist term: '{term}'" for term in INTERPRETIVIST_FORBIDDEN if term in haystack]


# ---------------------------------------------------------------------------
# Stage 2: refraction grid data
# ---------------------------------------------------------------------------


def refraction_rows(topic: str) -> list[dict[str, str]]:
    """Rows for the 4-way paradigm refraction grid (Stage 2)."""
    rows = []
    for paradigm, profile in PARADIGM_PROFILE.items():
        unit = "the target population / system"
        sample = profile["rq_template"].format(topic=topic, unit=unit, proof=profile["evidence"])
        rows.append(
            {
                "paradigm": paradigm,
                "goal": profile["goal"],
                "sample_rq": sample,
                "evidence": profile["evidence"],
                "negatives": profile["negative_exclusions"],
            }
        )
    return rows


def show_refraction_grid(topic: str) -> None:
    table = Table(title="4-Way Paradigm Refraction", show_header=True, header_style="bold cyan")
    table.add_column("Paradigm", style="bold white", width=24)
    table.add_column("Epistemological Goal", width=34)
    table.add_column("Sample Refined RQ", width=52)
    table.add_column("Required Primary Evidence", width=34)
    table.add_column("Strict Negative Exclusions", width=34)
    for r in refraction_rows(topic):
        table.add_row(
            r["paradigm"], r["goal"], r["sample_rq"], r["evidence"], r["negatives"]
        )
    console.print(table)


# ---------------------------------------------------------------------------
# Responder protocol: abstraction over every interactive prompt
# ---------------------------------------------------------------------------


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
# Stage 3 + 4: survey model, intent packet, workspace genesis
# ---------------------------------------------------------------------------


@dataclass
class ConceptDraft:
    concept: str
    synonyms: list[str] = field(default_factory=list)


@dataclass
class RQDraft:
    text: str
    facet: str
    evidence: str
    synthesis: str = "Comparative Matrix"


@dataclass
class Survey:
    """Everything the interview collected, independent of the responder/CLI."""

    topic: str
    paradigm: str
    playbook: str
    secondary_paradigm: str | None
    unit_of_analysis: str
    proof: str
    out_of_scope: list[str]
    languages: list[str]
    start_year: int | None
    end_year: int | None
    lead_researcher: str
    title: str
    venue: str
    timeline_weeks: int | None
    rqs: list[RQDraft]
    concepts: list[ConceptDraft]
    extra_inclusions: list[str]
    extra_exclusions: list[tuple[str, str]]
    trust_score_threshold: float
    matrix_dimensions: list[dict] = field(default_factory=list)


def slugify(text: str) -> str:
    import re

    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text).strip("-")


def make_intent(survey: Survey, slug: str, genesis_timestamp: str) -> dict:
    """Assemble the ``IntentPacket`` dict (Stage 4) for the deterministic compiler."""
    all_rqs = [f"RQ{i}" for i, _ in enumerate(survey.rqs, start=1)]

    inclusion = [
        {"criterion": f"Reports the gold-standard proof — {survey.proof}", "maps_to_rqs": all_rqs},
    ] + [{"criterion": c, "maps_to_rqs": all_rqs} for c in survey.extra_inclusions]

    exclusion = [
        {
            "criterion": item,
            "reason_category": "OUT_OF_SCOPE",
            "maps_to_rqs": all_rqs,
        }
        for item in survey.out_of_scope
    ]
    for text, category in survey.extra_exclusions:
        exclusion.append({"criterion": text, "reason_category": category, "maps_to_rqs": all_rqs})
    if not exclusion:
        default_exclusion = PARADIGM_PROFILE[survey.paradigm]["negative_exclusions"]
        exclusion.append({"criterion": default_exclusion, "reason_category": "OUT_OF_SCOPE", "maps_to_rqs": all_rqs})

    rationale = (
        f"{survey.paradigm} stance via the {survey.playbook} playbook. "
        f"Unit of analysis: {survey.unit_of_analysis}. "
        f"Convincing evidence is {survey.proof}. "
        f"Explicitly out of scope: {'; '.join(survey.out_of_scope) or 'none specified'}."
    )

    languages = survey.languages or ["en"]

    return {
        "protocol_id": f"proto-{genesis_timestamp[:10].replace('-', '')}-{slug}",
        "genesis_timestamp": genesis_timestamp,
        "project_slug": slug,
        "playbook_type": survey.playbook,
        "title": survey.title,
        "lead_researcher": survey.lead_researcher,
        "target_venue_type": survey.venue,
        "timeline_weeks": survey.timeline_weeks,
        "primary_paradigm": survey.paradigm,
        "secondary_paradigm": survey.secondary_paradigm,
        "unit_of_analysis": survey.unit_of_analysis,
        "trustworthiness_framework": TRUSTWORTHINESS_FRAMEWORK[survey.playbook],
        "epistemological_rationale": rationale,
        "incompatible_concepts": [],
        "research_questions": [
            {
                "text": rq.text,
                "target_facet": rq.facet,
                "synthesis_type": rq.synthesis,
                "required_evidence_type": rq.evidence,
            }
            for rq in survey.rqs
        ],
        "core_concepts": [
            {"concept": c.concept, "synonyms": c.synonyms, "boolean_operator": "OR"}
            for c in survey.concepts
        ],
        "target_databases": None,  # playbook preset default
        "start_year": survey.start_year,
        "end_year": survey.end_year,
        "languages": languages,
        "open_access_preferred": None,
        "pool_min": None,
        "pool_max": None,
        "inclusion_criteria": inclusion,
        "exclusion_criteria": exclusion,
        "two_tier_screening": True,
        "matrix_dimensions": survey.matrix_dimensions,
        "retraction_check_required": True,
        "coi_and_funding_audit_required": True,
        "reproducibility_das_cas_check": True,
        "minimum_trust_score_threshold": survey.trust_score_threshold,
    }


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
        raise typer.Exit(f"init_project.py failed:\n{exc.stderr or exc.stdout}") from exc
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
        rq_section = "\n".join(
            f"- **{rq}**"
            for rq in (rqs or ["RQ1: Primary research questions to be formulated."])
        )
        notes.write_text(
            f"# Literature Review: {title}\n\n"
            f"## Objectives & Research Questions\n{rq_section}\n\n"
            f"## Findings & Synthesis\n*To be generated from extracted papers.*\n",
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


_INLINE_LIST_CAP = 50


def _bounded(items: list, cap: int = _INLINE_LIST_CAP) -> dict:
    """Bound a list for an audit-description payload (subprocess argv safety)."""
    if len(items) <= cap:
        return {"values": list(items), "truncated_count": 0}
    return {"values": list(items[:cap]), "truncated_count": len(items) - cap}


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


def draft_default_concepts(topic: str) -> list[str]:
    """Very light concept suggestion from the topic's prominent words."""
    import re

    words = re.findall(r"[a-zA-Z][a-zA-Z-]{3,}", topic.lower())
    stop = {
        "with", "and", "for", "the", "of", "on", "in", "how", "what", "does",
        "impact", "experience", "build", "under", "conditions", "quantified",
    }
    seen = []
    for w in words:
        if w not in stop and w not in seen:
            seen.append(w)
        if len(seen) == 3:
            break
    return seen or [topic[:40].strip()]


def _now_iso() -> str:
    return datetime.now(UTC).isoformat()


# ---------------------------------------------------------------------------
# Grounded recon loop (--grounded): Step 2 probe -> Step 3 distill -> Step 4
# direction proposal + validation, inserted between Stage 1 and Stage 2.
# ---------------------------------------------------------------------------

_DELTA_PROBE_CHOICE = "__delta_probe__"

# P1 junk filter (16_inception_improvements.md F1/F3): numeric- and venue-
# scrape artifacts and verb-led sentence fragments must never surface as a
# validated direction or a default concept.  Curated from observed distiller
# fragments ("11 kcal mol", "reduces default probability") and venue noise
# ("62nd annual meeting", "computational linguistics volume").
_VENUE_NOISE_TOKENS = frozenset(
    {
        "proceedings",
        "conference",
        "symposium",
        "workshop",
        "meeting",
        "volume",
        "journal",
        "congress",
        "edition",
    }
)
_LEADING_FUNCTIONAL_TOKENS = frozenset(
    {
        "using", "based", "use", "uses", "used",
        "reduces", "reduce", "reduced",
        "improves", "improve", "improved",
        "increases", "increase", "increased",
        "achieves", "achieve", "achieving",
        "provides", "provide", "provided",
        "enables", "enable", "enabled",
        "shows", "show", "demonstrates", "demonstrate",
        "allows", "allow",
        "toward", "towards", "with", "for", "how", "what", "does",
        "under", "during", "between", "from", "on", "in",
        "the", "a", "an", "this", "that",
    }
)


def _is_junk_term_label(label: str | None) -> bool:
    """True for non-direction lexical artifacts (P1 junk filter).

    ``False`` always for terms with leading n-gram numeric prefixes, ordinal
    years/editions, verb-led fragments or venue-scrape tokens, so the
    filters are purely additive: a clean term is never rejected.
    """
    text = (label or "").strip()
    if not text:
        return True
    first = text.split()[0].casefold()
    if re.fullmatch(r"\d+(?:\.\d+)?", first):  # "11 kcal mol"
        return True
    if re.fullmatch(r"\d+(?:st|nd|rd|th)", first):  # "62nd annual meeting"
        return True
    if first in _LEADING_FUNCTIONAL_TOKENS:  # "reduces default probability"
        return True
    return any(tok in text.casefold() for tok in _VENUE_NOISE_TOKENS)


def _family_tokens(term: str) -> set[str]:
    """Plural-normalized token set for family matching (labels stay verbatim).

    ``language model`` vs ``language models`` are the same family, so the
    trailing plural ``-s``/``-es`` is dropped before comparison.  This is the
    only place the surface form is loosened: proposed labels keep their
    exact distiller spelling.
    """
    tokens: set[str] = set()
    for tok in term.casefold().split():
        if len(tok) > 3 and tok.endswith("es"):
            tok = tok[:-2]
        elif len(tok) > 3 and tok.endswith("s"):
            tok = tok[:-1]
        tokens.add(tok)
    return tokens


def _same_direction_family(a: dict, b: dict) -> bool:
    """True when two taxonomy terms are lexical variants of one direction.

    Collision iff they share >= 2 (plural-normalized) tokens -- covers
    ``large language model`` vs ``large language models`` and vs ``vision
    language models`` -- or one term's token set is a subset of the other's
    while sharing >= 1 token (modifier-dropped paraphrases).  A genuinely
    distinct sub-field term such as ``vision-language-action vla models``
    shares only a genus head (``model``) and stays separate, as does
    ``self-regulated learning srl`` (only ``learning`` in common with
    ``learning analytics dashboards``) -- that is the diversity P1 is meant
    to surface.
    """
    ta = _family_tokens(a["term"])
    tb = _family_tokens(b["term"])
    shared = ta & tb
    if len(shared) >= 2:
        return True
    return bool(shared) and (ta <= tb or tb <= ta)


def _select_diverse_directions(candidates: list[dict], limit: int = 3) -> list[dict]:
    """Greedy rank-order selection, at most one direction per term family.

    Deterministic: the relative rank of the input (multi-word desc, freq
    desc, lexicographic) is preserved; a candidate is only *dropped* when it
    duplicates a family already selected.  When no overlaps exist the output
    is exactly the old top-N, so legacy behavior is the default.
    """
    selected: list[dict] = []
    for candidate in candidates:
        if any(_same_direction_family(candidate, s) for s in selected):
            continue
        selected.append(candidate)
        if len(selected) == limit:
            break
    return selected


def _grounded_directions_for_terms(terms: dict) -> list[dict]:
    """Build up to 3 DOI-anchored directions from the distilled micro-taxonomy.

    Every direction carries >= 2 distinct anchor DOIs observed in the pool
    (hard filter: an unanchored term can never be proposed).  P1 applies the
    junk filter first, then diversity capping so lexical variants of one
    family never monopolize the top-3.
    """
    candidates = [
        t
        for t in terms.get("micro_taxonomy", [])
        if len(t["anchor_dois"]) >= 2 and not _is_junk_term_label(t["term"])
    ]
    candidates.sort(key=lambda t: (-len(t["term"].split()), -t["freq"], t["term"]))
    candidates = _select_diverse_directions(candidates)
    directions = [
        {
            "label": t["term"],
            "concept": t["term"],
            "anchor_dois": list(t["anchor_dois"]),
            "detail": f"pool term observed in {len(t['anchor_dois'])} papers",
        }
        for t in candidates[:3]
    ]
    if directions:
        return directions
    dois: list[str] = []
    labels: list[str] = []
    for entry in terms.get("micro_taxonomy", []):
        if _is_junk_term_label(entry["term"]):
            continue
        labels.append(entry["term"])
        for doi in entry["anchor_dois"]:
            if doi not in dois:
                dois.append(doi)
        if len(dois) >= 2:
            break
    if len(dois) >= 2:
        return [
            {
                "label": " ".join(labels)[:80] or "pool vocabulary",
                "concept": labels[0] if labels else "pool vocabulary",
                "anchor_dois": sorted(dois),
                "detail": f"pool vocabulary observed in {len(dois)} papers",
            }
        ]
    return []


def _present_grounded_directions(terms: dict, directions: list[dict]) -> None:
    schools = terms.get("schools", [])
    if schools:
        console.print(
            "[bold]Observed sub-schools in the pool:[/bold] "
            + ", ".join(f"{s['label']} ({s['n']})" for s in schools)
        )
    for i, d in enumerate(directions, start=1):
        body = f"[bold]{d['label']}[/bold]\n{d['detail']}\n\n[bold]Citation anchors:[/bold]"
        for doi in d["anchor_dois"]:
            body += f"\n  \u2022 {doi}"
        console.print(Panel.fit(body, title=f"Grounded Direction {i}", border_style="green"))


def _present_pool_assessment(pool_size: int, terms: dict) -> None:
    """Advisory pool-qa panel shown before directions (P5 + P2; additive).

    Computed from the two recon admission gates
    (``scholar_harness.recon.gates``) and printed only when there is
    something non-obvious to say.  It never aborts: the human remains the
    final gate in the interactive wizard, and in headless mode these notes
    are informational.
    """
    from .recon.gates import (
        TOPIC_COHERENCE_TOP3_SHARE,
        compute_pool_sufficiency,
        compute_topic_purity,
    )

    suff = compute_pool_sufficiency(pool_size)
    purity = compute_topic_purity(terms.get("topics") or [])
    notes: list[str] = []
    if not suff["sufficient"]:
        notes.append(
            f"thin pool ({suff['n_docs']} docs < {suff['threshold']}): proposed "
            "directions may be fragmentary -- raise the probe limit or run a "
            "delta probe before validating."
        )
    if purity["label"] == "indeterminate":
        notes.append(
            "no OpenAlex topics: topical coherence is indeterminate (treat "
            "purity as unknown, not absent)."
        )
    elif purity["label"] == "fragmented":
        notes.append(
            f"topically fragmented (top-3 topic share {purity['purity']:.2f} < "
            f"{purity['threshold']:.2f}): the pool spans several subfields."
        )
    qei = terms.get("qei")
    if (
        qei is not None
        and purity["label"] == "coherent"
        and qei > TOPIC_COHERENCE_TOP3_SHARE
    ):
        notes.append(
            "QEI high on a topically coherent pool: high echo here reflects a "
            "well-scoped seed, not poor inquiry -- do not reject on QEI alone."
        )
    if notes:
        console.print("[bold]Pool assessment:[/bold] " + " ".join(notes))


def _run_grounded_recon(
    responder: Responder,
    topic: str,
    recon_engine: ReconEngine | None = None,
    auto_select: bool = False,
    direction_id: int | None = None,
) -> dict | None:
    """Steps 2-4 of the grounding lifecycle for one session (--grounded).

    Probes the topic, distills the pool, presents <= 3 DOI-anchored directions,
    lets the researcher validate one (optionally after a single delta probe)
    and returns the session ``recon_context``.

    ``recon_context`` additionally carries ``default_concepts`` (the pool-anchored
    Stage-4b prompt default, M0.3 DoD 3) and ``anchored_terms`` (the session's
    anchored-term map: every term with literature evidence, term -> anchor DOIs).

    Hard contract: when the pool yields no >= 2-anchor direction, the wizard
    aborts with ``typer.Exit`` -- there is no warn-and-continue path, because
    emitting unanchored concepts would violate M0.3 DoD 3.

    Headless mode (M0.7 T7.8): ``auto_select=True`` picks the first (most
    anchored) direction; ``direction_id`` picks a specific 1-based direction.
    Either flag bypasses the interactive prompt, so a script/CI/agent run in a
    subshell never blocks on terminal input.  The interactive gate remains the
    default.
    """
    from .recon.distiller import distill_pool

    engine = recon_engine if recon_engine is not None else ReconEngine()
    session_id = uuid.uuid4().hex[:12]
    cache_keys: list[str] = []
    pool_sizes: list[int] = []
    anchor_dois: list[str] = []

    def probe_and_read(query: str) -> dict:
        pool_path, _n = asyncio.run(engine.probe(query))
        pool = json.loads(pool_path.read_text(encoding="utf-8"))
        cache_keys.append(str(pool.get("cache_key") or ""))
        pool_sizes.append(len(pool.get("docs", [])))
        return {"pool": pool, "terms": distill_pool(pool, query_text=query)}

    data = probe_and_read(topic)
    directions = _grounded_directions_for_terms(data["terms"])
    if not directions:
        raise typer.Exit(
            "No literature evidence was found under this topic (no direction with "
            ">= 2 citation anchors could be formed from the probe pool). Refine "
            "the topic or run inception without --grounded."
        )

    topic_dois: list[str] = []
    for doc in data["pool"].get("docs", []):
        doi = doc.get("doi")
        if doi and doi not in topic_dois:
            topic_dois.append(doi)
    topic_dois.sort()

    delta_allowed = True
    while True:
        _present_pool_assessment(
            pool_sizes[-1] if pool_sizes else 0, data["terms"]
        )
        _present_grounded_directions(data["terms"], directions)
        choices = [
            (d["label"], f"{len(d['anchor_dois'])} anchor papers") for d in directions
        ]
        if delta_allowed:
            choices.append((_DELTA_PROBE_CHOICE, "Run one refined delta probe"))
        if auto_select or direction_id is not None:
            idx = (direction_id - 1) if direction_id is not None else 0
            if idx < 0 or idx >= len(directions):
                raise typer.Exit(
                    f"Direction {direction_id} out of range (1-{len(directions)}); "
                    "nothing was emitted."
                )
            pick = directions[idx]["label"]
        else:
            pick = responder.choice(
                "Select the grounded research direction to pursue",
                choices,
                default=directions[0]["label"],
            )
        if pick == _DELTA_PROBE_CHOICE:
            target = responder.choice(
                "Which direction should the delta probe refine?",
                [(d["label"], f"{len(d['anchor_dois'])} anchor papers") for d in directions],
                default=directions[0]["label"],
            )
            delta = probe_and_read(target)
            delta_directions = _grounded_directions_for_terms(delta["terms"])
            if delta_directions:
                directions = delta_directions
                data = delta
            delta_allowed = False
            continue
        selected = next((d for d in directions if d["label"] == pick), None)
        if selected is None:
            continue
        anchor_dois = list(selected["anchor_dois"])
        validated_concept = selected["concept"]
        # Session anchored-term map: topic + validated direction are already
        # anchored (never re-probed later); pool taxonomy terms with >= 1
        # anchor DOI are evidenced in the pool and count as anchored too.
        anchored_terms = {
            topic: topic_dois,
            validated_concept: list(selected["anchor_dois"]),
        }
        for t in data["terms"].get("micro_taxonomy", []):
            if len(t["anchor_dois"]) >= 1:
                anchored_terms.setdefault(t["term"], []).extend(t["anchor_dois"])
        return {
            "session_id": session_id,
            "cache_keys": cache_keys,
            "pool_sizes": pool_sizes,
            "anchor_dois": anchor_dois,
            "direction": selected["label"],
            "concept": validated_concept,
            "default_concepts": _grounded_default_concepts(
                data["terms"], validated_concept
            ),
            "anchored_terms": anchored_terms,
        }


def _grounded_default_concepts(terms: dict, validated_concept: str) -> list[str]:
    """Stage-4b "Core search concepts" default in grounded mode (M0.3 DoD 3).

    Built exclusively from pool-anchored taxonomy terms -- :func:`draft_default_concepts`
    is never called in the grounded branch.  The validated direction's concept
    always leads; every remaining taxonomy term carrying >= 2 anchor DOIs
    follows (P1 junk filter applied), multi-word terms first (then frequency,
    then lexicographic).
    """
    defaults: list[str] = []
    seen: set[str] = set()
    if validated_concept:
        defaults.append(validated_concept)
        seen.add(validated_concept)
    others = [
        t
        for t in terms.get("micro_taxonomy", [])
        if (
            t["term"] not in seen
            and len(t["anchor_dois"]) >= 2
            and not _is_junk_term_label(t["term"])  # P1: venue-scrape/noise
        )
    ]
    others.sort(key=lambda t: (-len(t["term"].split()), -t["freq"], t["term"]))
    defaults.extend(t["term"] for t in others)
    return defaults


_GROUNDED_PROBE_BUDGET = 3


def _pool_anchor_dois(pool: dict) -> list[str]:
    """Distinct DOIs carried by a probe pool (sorted; empty == unanchored)."""
    dois: list[str] = []
    for doc in pool.get("docs", []):
        doi = doc.get("doi")
        if doi and doi not in dois:
            dois.append(doi)
    return sorted(dois)


def _enforce_grounded_anchors(
    concepts: list[ConceptDraft],
    recon_context: dict,
    recon_engine: ReconEngine,
) -> dict:
    """Step-5 delta-probe enforcement (03_lifecycle.md Step 5; M0.3 DoD 3).

    Every concept/synonym that would enter ``core_concepts`` in grounded mode
    must already sit in the session's anchored-term map or earn its anchors
    through a bounded supplementary probe.  A synonym that still yields zero
    anchors is dropped with a yellow warning; a concept that still yields zero
    anchors (or cannot be probed within the budget) aborts the wizard with
    ``typer.Exit`` -- nothing unanchored is ever emitted.
    """
    anchored_terms = dict(recon_context.get("anchored_terms") or {})
    cache_keys: list[str] = recon_context.get("cache_keys", [])
    pool_sizes: list[int] = recon_context.get("pool_sizes", [])
    probes_used = 0

    def probe(term: str) -> list[str]:
        nonlocal probes_used
        probes_used += 1
        pool_path, _n = asyncio.run(recon_engine.probe(term))
        pool = json.loads(pool_path.read_text(encoding="utf-8"))
        cache_keys.append(str(pool.get("cache_key") or ""))
        pool_sizes.append(len(pool.get("docs", [])))
        return _pool_anchor_dois(pool)

    def budget_left() -> bool:
        return probes_used < _GROUNDED_PROBE_BUDGET

    def no_evidence_exit(term: str) -> typer.Exit:
        return typer.Exit(
            f"Concept '{term}' has no literature evidence; refine it or run "
            "inception without --grounded. Nothing was emitted."
        )

    for draft in concepts:
        if draft.concept not in anchored_terms:
            if not budget_left():
                raise no_evidence_exit(draft.concept)
            dois = probe(draft.concept)
            if not dois:
                raise no_evidence_exit(draft.concept)
            anchored_terms[draft.concept] = dois
        kept: list[str] = []
        for synonym in draft.synonyms:
            if synonym in anchored_terms:
                kept.append(synonym)
                continue
            if not budget_left():
                console.print(
                    f"[yellow]\u26a0 probe budget exceeded; '{synonym}' has no confirmed "
                    f"literature evidence, removed as a search synonym.[/yellow]"
                )
                continue
            dois = probe(synonym)
            if dois:
                anchored_terms[synonym] = dois
                kept.append(synonym)
            else:
                console.print(
                    f"[yellow]\u26a0 '{synonym}' has no literature evidence under probe; "
                    f"removed as a search synonym.[/yellow]"
                )
        draft.synonyms = kept

    # Belt-and-suspenders: never ship a concept that is still unanchored.
    for draft in concepts:
        if draft.concept not in anchored_terms:
            raise no_evidence_exit(draft.concept)
    recon_context["anchored_terms"] = anchored_terms
    return recon_context


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
    console.print("\n[bold]Latent intent scan:[/bold] " + ", ".join(f"{p} ({s})" for p, s in ranked))
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

    console.print(Panel("[bold]Lexicon enforcement[/bold]\n" + PARADIGM_PROFILE[paradigm]["lexicon"], border_style="yellow"))
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
        f"• concepts: {len(concepts)}\n• inclusion: {len(intent['inclusion_criteria'])} / exclusion: {len(intent['exclusion_criteria'])}"
        f"\n\nReview the summary above; the protocol will be compiled deterministically from this intent.",
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