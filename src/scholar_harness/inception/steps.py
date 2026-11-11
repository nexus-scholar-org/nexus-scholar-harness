"""The stateless inception step API (M4a; plan §2, Phase 0 screens 01–06).

Each step takes the whole draft and returns what the wizard would propose at
that point; nothing is stored and nothing is written. The proposals come from
the same functions the CLI wizard calls (`detect_leanings`, `draft_rq`,
`draft_criteria`, `_default_matrix_dimensions`, `make_intent`,
`compile_intent`); this module only maps a draft onto them.

* :func:`run_step` answers ``scope``, ``shape``, ``criteria`` and ``matrix``.
* :func:`preview` is the compile-preview: the intent, the protocol, its
  fingerprint, the exact ``SCREENING_CRITERIA.md`` text and the files a genesis
  would write. It writes nothing.
* :func:`genesis` is the one write, through :func:`emit_workspace` and its
  overwrite guard.

Grounded evidence (M4c): a draft record may carry a ``grounding`` written by
the recon bind route (``inception/grounding.py``). :func:`preview` and
:func:`genesis` take it as an argument: preview shows the bound pool, the
direction and per-RQ evidence; genesis writes it to ``audit/recon_context.json``.
Without it every step answers as in M4b.
"""

from __future__ import annotations

import json
import re
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from .emit import (
    NEW_WORKSPACE_FILES,
    REPLACEMENT_FILES,
    GenesisRefused,
    check_writable,
    emit_workspace,
    existing_markers,
    corpus_paths,
    screening_state,
)
from .genesis import (
    SUPPORT_FILES,
    _default_matrix_dimensions,
    compile_intent,
    install_workspace_support_files,
)
from .intent import (
    ALL_PLAYBOOKS,
    PARADIGM_PROFILE,
    TRUSTWORTHINESS_FRAMEWORK,
    VERIFICATION_TRUST_THRESHOLD,
    ConceptDraft,
    RQDraft,
    Survey,
    detect_leanings,
    draft_criteria,
    draft_default_concepts,
    draft_rq,
    enforce_lexicon,
    make_intent,
    recommend_playbook,
    refraction_rows,
    slugify,
)

STEPS = ("scope", "shape", "criteria", "matrix")
#: Written by genesis for a draft with grounded evidence (M4c).
RECON_CONTEXT_FILE = "audit/recon_context.json"


class StepRefused(Exception):
    """A step cannot answer for this draft; ``code`` names why."""

    def __init__(self, code: str, message: str, status: int = 422, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.code, self.message, self.status, self.details = code, message, status, details or {}


class ConceptIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    concept: str
    synonyms: list[str] = Field(default_factory=list)


class ExclusionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    criterion: str
    reason_category: str = "OUT_OF_SCOPE"


#: The discovery Recall check takes at most 25 seeds (``scholar_search.recall``).
MAX_GOLDEN_SEEDS = 25
_DOI = re.compile(r"^10\.\d+(\.\d+)*/\S+$")


def _doi_list(values: list[str]) -> list[str]:
    out: list[str] = []
    for value in values:
        doi = str(value).strip()
        for prefix in ("https://doi.org/", "http://doi.org/", "doi:"):
            if doi.lower().startswith(prefix):
                doi = doi[len(prefix):]
        if not _DOI.match(doi):
            raise ValueError(f"{value!r} is not a DOI (10.<registrant>/<suffix>)")
        if doi.lower() not in {d.lower() for d in out}:
            out.append(doi)
    return out


class Draft(BaseModel):
    """Everything the interview collects. Every field is optional until preview."""

    model_config = ConfigDict(extra="forbid")

    topic: str = ""
    paradigm: str | None = None
    playbook: str | None = None
    secondary_paradigm: str | None = None
    unit_of_analysis: str = ""
    proof: str = ""
    out_of_scope: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=lambda: ["en"])
    start_year: int | None = None
    end_year: int | None = None
    rqs: list[str] = Field(default_factory=list)
    concepts: list[ConceptIn] = Field(default_factory=list)
    extra_inclusions: list[str] = Field(default_factory=list)
    extra_exclusions: list[ExclusionIn] = Field(default_factory=list)
    #: criterion id -> accepted (True) / rejected (False). Ids come from the criteria step.
    criteria_decisions: dict[str, bool] = Field(default_factory=dict)
    matrix_columns: list[str] = Field(default_factory=list)
    verification_checks: bool = True
    #: DOIs kept as recall seeds from the pool's anchors (M4d DoD 5); compiled
    #: into ``search_strategy.golden_seeds`` at genesis.
    golden_seeds: list[str] = Field(default_factory=list, max_length=MAX_GOLDEN_SEEDS)
    title: str = ""
    lead_researcher: str = ""
    venue: str = ""
    timeline_weeks: int | None = None

    @field_validator("golden_seeds")
    @classmethod
    def _seeds_are_dois(cls, values: list[str]) -> list[str]:
        return _doi_list(values)


def parse_draft(raw: dict[str, Any] | None) -> Draft:
    try:
        return Draft.model_validate(raw or {})
    except ValidationError as exc:
        raise StepRefused(
            "DRAFT_INVALID", "the draft does not match the draft shape",
            details={"errors": json.loads(exc.json(include_url=False))},
        ) from exc


def _require(draft: Draft, *fields: str) -> None:
    missing = [f for f in fields if not getattr(draft, f)]
    if missing:
        raise StepRefused("DRAFT_INCOMPLETE", f"this step needs: {', '.join(missing)}", details={"missing": missing})
    if "paradigm" in fields and draft.paradigm not in PARADIGM_PROFILE:
        raise StepRefused("DRAFT_INVALID", f"unknown paradigm {draft.paradigm!r}", details={"paradigms": list(PARADIGM_PROFILE)})
    if "playbook" in fields and draft.playbook not in ALL_PLAYBOOKS:
        raise StepRefused("DRAFT_INVALID", f"unknown playbook {draft.playbook!r}", details={"playbooks": list(ALL_PLAYBOOKS)})


def _survey(draft: Draft) -> Survey:
    paradigm = draft.paradigm or ""
    profile = PARADIGM_PROFILE.get(paradigm, {})
    return Survey(
        topic=draft.topic,
        paradigm=paradigm,
        playbook=draft.playbook or "",
        secondary_paradigm=draft.secondary_paradigm,
        unit_of_analysis=draft.unit_of_analysis,
        proof=draft.proof,
        out_of_scope=list(draft.out_of_scope),
        languages=list(draft.languages),
        start_year=draft.start_year,
        end_year=draft.end_year,
        lead_researcher=draft.lead_researcher,
        title=draft.title,
        venue=draft.venue,
        timeline_weeks=draft.timeline_weeks,
        rqs=[RQDraft(text=t, facet=profile.get("facet", ""), evidence=profile.get("evidence", "")) for t in draft.rqs],
        concepts=[ConceptDraft(concept=c.concept, synonyms=list(c.synonyms)) for c in draft.concepts],
        extra_inclusions=list(draft.extra_inclusions),
        extra_exclusions=[(e.criterion, e.reason_category) for e in draft.extra_exclusions],
        trust_score_threshold=VERIFICATION_TRUST_THRESHOLD if draft.verification_checks else 0.0,
        matrix_dimensions=[],
        golden_seeds=list(draft.golden_seeds),
    )


# ---------------------------------------------------------------------------
# Steps
# ---------------------------------------------------------------------------


def _scope(draft: Draft) -> dict[str, Any]:
    _require(draft, "topic")
    ranked = detect_leanings(draft.topic)
    return {
        "leanings": [{"paradigm": p, "score": s} for p, s in ranked],
        "recommended_paradigm": ranked[0][0],
        "paradigms": [{"name": p, "goal": profile["goal"]} for p, profile in PARADIGM_PROFILE.items()],
        "refraction": refraction_rows(draft.topic),
        "default_concepts": draft_default_concepts(draft.topic),
    }


def _shape(draft: Draft) -> dict[str, Any]:
    _require(draft, "topic", "paradigm")
    paradigm = draft.paradigm
    playbook = draft.playbook or recommend_playbook(paradigm)
    return {
        "recommended_playbook": recommend_playbook(paradigm),
        "playbooks": [{"name": p, "framework": TRUSTWORTHINESS_FRAMEWORK[p]} for p in ALL_PLAYBOOKS],
        "trustworthiness_framework": TRUSTWORTHINESS_FRAMEWORK.get(playbook),
        "rq_draft": draft_rq(paradigm, draft.topic, draft.unit_of_analysis, draft.proof),
        "lexicon": PARADIGM_PROFILE[paradigm]["lexicon"],
        "lexicon_warnings": enforce_lexicon(paradigm, draft.topic),
    }


def criteria_with_decisions(draft: Draft) -> list[dict[str, Any]]:
    """Each drafted criterion, verbatim, with its source and the researcher's decision.

    ``status`` is ``accepted``, ``rejected`` or ``undecided``. A criterion the
    researcher typed is accepted unless rejected; one the wizard wrote stays
    ``undecided`` until the researcher accepts or rejects it (INC-22).
    """
    out = []
    for c in draft_criteria(_survey(draft)):
        item = c.as_dict(draft.paradigm or "")
        decision = draft.criteria_decisions.get(c.id)
        if decision is None:
            item["status"] = "undecided" if c.generated else "accepted"
        else:
            item["status"] = "accepted" if decision else "rejected"
        out.append(item)
    return out


def _criteria(draft: Draft) -> dict[str, Any]:
    _require(draft, "paradigm", "proof")
    items = criteria_with_decisions(draft)
    accepted_kinds = {i["kind"] for i in items if i["status"] == "accepted"}
    return {
        "criteria": items,
        "undecided": [i["id"] for i in items if i["status"] == "undecided"],
        "missing_sides": [k for k in ("inclusion", "exclusion") if k not in accepted_kinds],
    }


def _matrix(draft: Draft) -> dict[str, Any]:
    _require(draft, "playbook")
    dims = _default_matrix_dimensions(draft.playbook, draft.unit_of_analysis or "the unit of analysis")
    return {"columns": dims, "selected": [d["name"] for d in dims if d["name"] in draft.matrix_columns]}


_STEP_FUNCS = {"scope": _scope, "shape": _shape, "criteria": _criteria, "matrix": _matrix}


def run_step(step: str, raw_draft: dict[str, Any] | None) -> dict[str, Any]:
    if step not in _STEP_FUNCS:
        raise StepRefused("STEP_UNKNOWN", f"unknown step {step!r}", status=404, details={"steps": list(STEPS)})
    return {"step": step, **_STEP_FUNCS[step](parse_draft(raw_draft))}


# ---------------------------------------------------------------------------
# Compile-preview and genesis
# ---------------------------------------------------------------------------


def build_intent(draft: Draft, genesis_timestamp: str) -> dict[str, Any]:
    """The intent a genesis would compile; refuses an incomplete draft or undecided criteria."""
    _require(draft, "topic", "paradigm", "playbook", "unit_of_analysis", "proof", "rqs", "concepts", "title", "lead_researcher")
    criteria = _criteria(draft)
    if criteria["undecided"]:
        raise StepRefused(
            "CRITERIA_UNDECIDED", "accept or reject every criterion the wizard wrote",
            details={"undecided": criteria["undecided"]},
        )
    if criteria["missing_sides"]:
        raise StepRefused(
            "CRITERIA_MISSING", "a protocol needs at least one inclusion and one exclusion criterion",
            details={"missing_sides": criteria["missing_sides"]},
        )
    slug = slugify(draft.title)
    if not slug:
        raise StepRefused("WORKSPACE_TITLE_INVALID", "the title has no letters or digits to make a folder name from")
    survey = _survey(draft)
    if draft.matrix_columns:
        dims = _default_matrix_dimensions(draft.playbook, draft.unit_of_analysis)
        survey.matrix_dimensions = [d for d in dims if d["name"] in draft.matrix_columns]
    accepted_ids = {i["id"] for i in criteria["criteria"] if i["status"] == "accepted"}
    accepted = [c for c in draft_criteria(survey) if c.id in accepted_ids]
    return make_intent(survey, slug, genesis_timestamp, criteria=accepted)


def preview(
    raw_draft: dict[str, Any] | None,
    *,
    workspaces_root: Path | None = None,
    genesis_timestamp: str | None = None,
    grounding: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compile the draft in memory. Writes nothing.

    With ``workspaces_root`` it also says where the workspace would go and
    whether that folder already holds one (and its screening state), so the
    review screen can show a replacement before the researcher asks for it.
    """
    draft = parse_draft(raw_draft)
    ts = genesis_timestamp or datetime.now(UTC).isoformat()
    intent = build_intent(draft, ts)
    try:
        compiled = compile_intent(intent)
    except ValidationError as exc:
        raise StepRefused("INTENT_INVALID", "the compiler refused this intent", details={"errors": json.loads(exc.json(include_url=False))}) from exc
    out: dict[str, Any] = {
        "intent": intent,
        "protocol": json.loads(compiled["protocol_bytes"].decode("utf-8")),
        "protocol_fingerprint": compiled["protocol_fingerprint"],
        "screening_criteria": compiled["criteria_text"],
        "criteria": [i for i in criteria_with_decisions(draft) if i["status"] == "accepted"],
        "files": planned_files(exists=False),
        "written": [],
    }
    if grounding:
        out["grounding"] = grounding_preview(draft, grounding)
    if workspaces_root is not None:
        target = Path(workspaces_root) / intent["project_slug"]
        exists = target.exists()
        # What genesis decides on: a folder holds a workspace when it has a marker.
        workspace = bool(existing_markers(target))
        out["files"] = planned_files(exists=workspace)
        out["target"] = {
            "slug": intent["project_slug"],
            "path": str(target),
            "exists": exists,
            "workspace": workspace,
            "screening": screening_state(target) if workspace else None,
            # F1 (M4d): what a replacement would archive beside the old protocol.
            "archive": corpus_paths(target) if workspace else [],
        }
    if grounding and RECON_CONTEXT_FILE not in out["files"]:
        out["files"].append(RECON_CONTEXT_FILE)  # genesis writes it for a bound draft
    return out


def grounding_preview(draft: Draft, grounding: dict[str, Any]) -> dict[str, Any]:
    """What a bound draft's genesis records: the pool, the direction and the evidence per RQ."""
    from .grounding import recon_context

    ctx = recon_context(grounding, list(draft.rqs), [c.concept for c in draft.concepts])
    return {
        "session_id": grounding.get("session_id"),
        "pool": grounding.get("pool"),
        "direction": grounding.get("direction"),
        "anchors": grounding.get("anchors"),
        "rq_evidence": ctx["rq_evidence"],
        "concept_evidence": {c.concept: ctx["term_evidence"].get(c.concept) for c in draft.concepts},
        "apr_observed": ctx["apr_observed"],
    }


def planned_files(*, exists: bool) -> list[str]:
    """Every file :func:`genesis` writes: a new workspace, or a replacement of one."""
    return list(REPLACEMENT_FILES) if exists else [*NEW_WORKSPACE_FILES, *SUPPORT_FILES]


def genesis(
    raw_draft: dict[str, Any] | None,
    *,
    workspaces_root: Path,
    agent: str,
    replace: bool = False,
    confirm_discard_screening_binding: str | None = None,
    grounding: dict[str, Any] | None = None,
    busy: Callable[[Path], str | None] | None = None,
) -> dict[str, Any]:
    """Create (or, with ``replace``, re-protocol) ``<workspaces_root>/<slug>`` from a draft.

    ``busy(target)`` names a job still running in the target workspace; a
    replacement is then refused with ``WORKSPACE_JOB_ACTIVE`` before anything
    moves, so a running search or screening cannot write into the new
    protocol's corpus (F1 review, M4d).

    The only write of the web wizard, through :func:`emit_workspace`. A
    screening binding is discarded only when ``confirm_discard_screening_binding``
    equals the slug, typed by the researcher (decision 2026-11-08,
    re-inception). A new workspace that fails half-way is removed.
    """
    from scholar_harness.workspace import catalog

    draft = parse_draft(raw_draft)
    intent = build_intent(draft, datetime.now(UTC).isoformat())
    slug = intent["project_slug"]
    try:
        target = catalog._target(Path(workspaces_root), slug)
    except catalog.WorkspaceRefused as exc:
        raise StepRefused(exc.code, exc.message, status=exc.status) from exc
    discard = confirm_discard_screening_binding is not None and confirm_discard_screening_binding == slug
    if confirm_discard_screening_binding is not None and not discard:
        raise StepRefused(
            "CONFIRMATION_MISMATCH", f"type the workspace name '{slug}' to confirm", details={"expected": slug}
        )
    # As POST /workspaces: any existing folder that is not a workspace is refused,
    # so a failure below can only ever remove a folder this request created.
    if target.exists() and not existing_markers(target):
        raise StepRefused(
            "WORKSPACE_EXISTS", f"{target} already exists and is not a workspace; choose another title",
            status=409, details={"path": str(target)},
        )
    if replace and busy is not None and existing_markers(target):
        running = busy(target)
        if running:
            raise StepRefused(
                "WORKSPACE_JOB_ACTIVE",
                f"{running} is still running in this workspace; wait for it to end or stop it, then replace the protocol",
                status=409, details={"job": running},
            )
    try:
        guard = check_writable(target, replace=replace, discard_screening_binding=discard)
    except GenesisRefused as exc:
        raise StepRefused(exc.code, exc.message, status=409, details=exc.details) from exc
    created = not guard["exists"] and not target.exists()
    try:
        context = None
        if grounding:
            from .grounding import recon_context

            context = recon_context(grounding, list(draft.rqs), [c.concept for c in draft.concepts])
        result = emit_workspace(
            intent, target_dir=target, replace=replace, discard_screening_binding=discard,
            agent=agent, recon_context=context,
        )
        if created:
            install_workspace_support_files(target)
    except GenesisRefused as exc:
        raise StepRefused(exc.code, exc.message, status=409, details=exc.details) from exc
    except (OSError, shutil.Error) as exc:
        if created:
            shutil.rmtree(target, ignore_errors=True)
        raise StepRefused(
            "WORKSPACE_ROOT_UNAVAILABLE",
            f"the workspace could not be written under {workspaces_root}: {type(exc).__name__}: {str(exc)[:300]}",
            status=409,
        ) from exc
    except BaseException:
        if created:
            shutil.rmtree(target, ignore_errors=True)
        raise
    return {"slug": slug, "path": str(target), **result}
