"""Interactive Inception CLI: the Socratic methodology interview (Phase 0).

Implements the 4-stage inception architecture from
``docs/phase_0/04_socratic_inception_protocol.md`` as a terminal wizard:

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

import json
import subprocess
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKSPACE_MANAGER_SCRIPTS = REPO_ROOT / ".agents" / "skills" / "workspace-manager" / "scripts"
INIT_PROJECT_SCRIPT = WORKSPACE_MANAGER_SCRIPTS / "init_project.py"
LOG_EVENT_SCRIPT = WORKSPACE_MANAGER_SCRIPTS / "log_event.py"

console = Console()

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
    """Rich + typer terminal implementation of :class:`Responder`."""

    def text(self, message: str, default: str = "") -> str:
        prompt = f"• {message}"
        if default:
            value = typer.prompt(prompt, default=default)
        else:
            value = typer.prompt(prompt)
        return str(value).strip()

    def confirm(self, message: str, default: bool = True) -> bool:
        return typer.confirm(message, default=default)

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
        while True:
            raw = input("  Enter choice number: ").strip()
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
        while True:
            raw = input("  → ").strip().lower()
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
    if not INIT_PROJECT_SCRIPT.exists():
        raise typer.Exit(f"workspace-manager init_project.py not found at {INIT_PROJECT_SCRIPT}")
    cmd = [
        sys.executable, str(INIT_PROJECT_SCRIPT), title,
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


def log_genesis(ws_dir: Path, description: str) -> None:
    """Record the GENESIS audit event via workspace-manager's log_event.py."""
    cmd = [sys.executable, str(LOG_EVENT_SCRIPT), str(ws_dir)]
    cmd += ["--action", "GENESIS", "--agent", "scholar-harness/inception", "--status", "SUCCESS"]
    cmd += ["--inputs"] + [str(f) for f in (ws_dir / "intent.json",)]
    cmd += ["--outputs"] + [str(f) for f in (ws_dir / "protocol.json", ws_dir / "SCREENING_CRITERIA.md")]
    cmd += ["--description", description]
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, encoding="utf-8")
    except subprocess.CalledProcessError as exc:  # pragma: no cover - best effort
        console.print(f"[yellow]⚠ warning: GENESIS event not logged ({exc.stderr or exc})[/yellow]")


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
# The wizard
# ---------------------------------------------------------------------------


def run_wizard(
    responder: Responder,
    root: Path,
    *,
    genesis_timestamp: str | None = None,
    no_scaffold: bool = False,
) -> dict:
    """Run the 4-stage Socratic inception interview and emit the protocol.

    Returns a summary dict: {intent, slug, title, playbook, paradigm,
    protocol_fingerprint, workspace_dir} where ``workspace_dir`` is set only
    when scaffolding ran (or already existed).
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
    concepts_raw = responder.text(
        "Core search concepts (comma-separated)",
        default=", ".join(draft_default_concepts(topic)),
    )
    concepts: list[ConceptDraft] = []
    for c in [s.strip() for s in concepts_raw.split(",") if s.strip()]:
        syn_raw = responder.text(f"Synonyms / alternate terms for '{c}' (comma-separated; blank = none)")
        concepts.append(ConceptDraft(concept=c, synonyms=[s.strip() for s in syn_raw.split(",") if s.strip()]))

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
    title = responder.text("Project title", default=topic.strip().rstrip("?").capitalize())
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

    ws_dir = scaffold_project(root, title, slug, paradigm, [rq.text for rq in rqs])
    compiled = compile_protocol_files(ws_dir, intent)
    log_genesis(
        ws_dir,
        f"Phase-0 Inception: '{title}' [{paradigm}, {playbook}] compiled protocol fingerprint "
        f"{compiled['protocol_fingerprint']}",
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
) -> None:
    """Launch the interactive Phase-0 Socratic inception wizard."""
    run_wizard(ConsoleResponder(), root, no_scaffold=no_scaffold)