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
from typing import Annotated, Any, Callable

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, ValidationError, field_validator

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
    DEFAULT_REASON,
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


#: The discovery Recall check takes at most 25 seeds (``scholar_search.recall``).
MAX_GOLDEN_SEEDS = 25

# Draft size limits (F6, H-input-limits; decision 2026-11-12). Generous for a
# real review and the same 2 000 characters the discovery note allows; a draft
# over them is refused ``DRAFT_TOO_LARGE`` and never saved.
#: A free-text answer: topic, unit of analysis, proof, title, each research
#: question, each scope exclusion, each extra criterion.
MAX_TEXT_CHARS = 2_000
#: A name or label: researcher, venue, a concept, a synonym, a matrix column, a
#: criterion id, a lens, a playbook, a language tag.
MAX_NAME_CHARS = 200
MAX_RQS = 20
MAX_CONCEPTS = 50
#: Synonyms per concept.
MAX_SYNONYMS = 50
#: ``out_of_scope``, ``extra_inclusions``, ``extra_exclusions``, ``matrix_columns``,
#: ``out_of_scope_reasons`` and ``custom_matrix_columns`` (M10b).
MAX_LIST_ITEMS = 50
MAX_CRITERIA_DECISIONS = 500
MAX_LANGUAGES = 20
#: The limits as the refusal's ``details.limits`` reports them.
DRAFT_LIMITS: dict[str, int] = {
    "text_chars": MAX_TEXT_CHARS,
    "name_chars": MAX_NAME_CHARS,
    "rqs": MAX_RQS,
    "concepts": MAX_CONCEPTS,
    "synonyms_per_concept": MAX_SYNONYMS,
    "list_items": MAX_LIST_ITEMS,
    "criteria_decisions": MAX_CRITERIA_DECISIONS,
    "languages": MAX_LANGUAGES,
    "golden_seeds": MAX_GOLDEN_SEEDS,
}
#: The planned number of records to screen (M10b, R3): whole numbers, the maximum
#: from 1 to this.
MAX_PLANNED_RECORDS = 1_000_000
#: An exclusion's reason code (M10b, decided 2026-11-15): 3 to 40 characters,
#: capitals, digits and ``_``, starting with a letter. Tighter than the protocol
#: model, which takes any string.
REASON_CODE = re.compile(r"^[A-Z][A-Z0-9_]{2,39}$")
#: The values of ``MatrixDimension.data_type`` (``scholar_protocol.models.DimensionDataType``).
MATRIX_DATA_TYPES = ("free_text", "numeric", "categorical", "list")
Text = Annotated[str, StringConstraints(max_length=MAX_TEXT_CHARS)]
Name = Annotated[str, StringConstraints(max_length=MAX_NAME_CHARS)]
#: pydantic's error types for a value over a length limit.
_SIZE_ERRORS = frozenset({"string_too_long", "too_long"})


class ConceptIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    concept: Name
    synonyms: list[Name] = Field(default_factory=list, max_length=MAX_SYNONYMS)


REASON_CODE_RULE = "a reason code has 3 to 40 characters: capital letters, digits and underscores, starting with a letter"


def reason_code_ok(value: str | None) -> bool:
    return bool(REASON_CODE.match(value or ""))


class ExclusionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    criterion: Text
    reason_category: Name = DEFAULT_REASON


class MatrixColumnIn(BaseModel):
    """The researcher's own extraction column (M10b, ``05-criteria``).

    It holds the whole ``MatrixDimensionIntent``, so a column imported from an
    earlier protocol compiles exactly as it was; the screen offers name,
    description, type and required. ``id`` is derived from the name by the
    engine when it is not given (:func:`custom_columns`).
    """

    model_config = ConfigDict(extra="forbid")
    id: Name | None = None
    name: Name
    description: Text = ""
    data_type: Name = "free_text"
    required: bool = False
    fallback_value: Name = "Not Reported"
    target_section_category: Name | None = None

    @field_validator("name")
    @classmethod
    def _named(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("a column needs a name")
        return value.strip()

    @field_validator("data_type")
    @classmethod
    def _type(cls, value: str) -> str:
        if value not in MATRIX_DATA_TYPES:
            raise ValueError(f"data_type is one of {', '.join(MATRIX_DATA_TYPES)}")
        return value


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

    topic: Text = ""
    paradigm: Name | None = None
    playbook: Name | None = None
    secondary_paradigm: Name | None = None
    unit_of_analysis: Text = ""
    proof: Text = ""
    out_of_scope: list[Text] = Field(default_factory=list, max_length=MAX_LIST_ITEMS)
    languages: list[Name] = Field(default_factory=lambda: ["en"], max_length=MAX_LANGUAGES)
    start_year: int | None = None
    end_year: int | None = None
    rqs: list[Text] = Field(default_factory=list, max_length=MAX_RQS)
    concepts: list[ConceptIn] = Field(default_factory=list, max_length=MAX_CONCEPTS)
    extra_inclusions: list[Text] = Field(default_factory=list, max_length=MAX_LIST_ITEMS)
    extra_exclusions: list[ExclusionIn] = Field(default_factory=list, max_length=MAX_LIST_ITEMS)
    #: criterion id -> accepted (True) / rejected (False). Ids come from the criteria step.
    criteria_decisions: dict[Name, bool] = Field(default_factory=dict, max_length=MAX_CRITERIA_DECISIONS)
    matrix_columns: list[Name] = Field(default_factory=list, max_length=MAX_LIST_ITEMS)
    verification_checks: bool = True
    #: DOIs kept as recall seeds from the pool's anchors (M4d DoD 5); compiled
    #: into ``search_strategy.golden_seeds`` at genesis.
    golden_seeds: list[str] = Field(default_factory=list, max_length=MAX_GOLDEN_SEEDS)
    title: Text = ""
    lead_researcher: Name = ""
    venue: Name = ""
    timeline_weeks: int | None = None
    #: The number of records the researcher plans to screen (M10b, R3, ``04-shape``).
    #: Optional; empty keeps the playbook preset in the protocol.
    pool_min: int | None = None
    pool_max: int | None = None
    #: The reason code of each out-of-scope line, keyed by the line's text (M10b).
    #: A key whose line is gone is ignored.
    out_of_scope_reasons: dict[Text, Name] = Field(default_factory=dict, max_length=MAX_LIST_ITEMS)
    #: The reason code of the paradigm's default exclusion (M10b); empty is ``OUT_OF_SCOPE``.
    default_exclusion_reason: Name | None = None
    #: The researcher's own matrix columns (M10b, ``05-criteria``).
    custom_matrix_columns: list[MatrixColumnIn] = Field(default_factory=list, max_length=MAX_LIST_ITEMS)

    @field_validator("golden_seeds")
    @classmethod
    def _seeds_are_dois(cls, values: list[str]) -> list[str]:
        return _doi_list(values)



def _over_limit(error: dict[str, Any]) -> str:
    """``rqs[3] (over 2000 characters)`` or ``rqs (21 items, at most 20)`` for one size error."""
    path = ""
    for part in error.get("loc", ()):
        path += f"[{part}]" if isinstance(part, int) else (f".{part}" if path else str(part))
    ctx = error.get("ctx") or {}
    if error.get("type") == "string_too_long":
        return f"{path} (over {ctx.get('max_length')} characters)"
    return f"{path} ({ctx.get('actual_length')} items, at most {ctx.get('max_length')})"


def _field_errors(draft: Draft) -> list[dict[str, Any]]:
    """Cross-field rules of the M10b fields, each naming its field (``loc``) and never the client's value."""
    errors: list[dict[str, Any]] = []
    lo, hi = draft.pool_min, draft.pool_max
    if hi is None and lo is not None:
        errors.append({"loc": ["pool_max"], "msg": "state the largest number you plan to screen", "type": "value_error"})
    if hi is not None and not 1 <= hi <= MAX_PLANNED_RECORDS:
        errors.append({"loc": ["pool_max"], "msg": f"a whole number from 1 to {MAX_PLANNED_RECORDS:,}", "type": "value_error"})
    if hi is not None and lo is not None and not 0 <= lo <= hi:
        errors.append({"loc": ["pool_min"], "msg": "a whole number from 0 to pool_max", "type": "value_error"})
    seen: set[str] = set()
    for i, column in enumerate(draft.custom_matrix_columns):
        key = column.name.casefold()
        if key in seen:
            errors.append({"loc": ["custom_matrix_columns", i, "name"], "msg": "another own column has this name", "type": "value_error"})
        seen.add(key)
    return errors


def reason_code_errors(draft: Draft) -> list[dict[str, Any]]:
    """Every reason code outside :data:`REASON_CODE`, as ``DRAFT_INVALID`` errors (M10b).

    Checked only when a draft is saved or created (``parse_draft(saving=True)``),
    never when it is read: a draft saved before M10b with another code stays
    readable, its row is flagged (``reason_valid: false``), and the next save
    asks for a valid code (``05-criteria``, decided 2026-11-15).
    """
    errors: list[dict[str, Any]] = []

    def bad(loc: list[Any]) -> None:
        errors.append({"loc": loc, "msg": REASON_CODE_RULE, "type": "value_error"})

    for i, exclusion in enumerate(draft.extra_exclusions):
        if not reason_code_ok(exclusion.reason_category):
            bad(["extra_exclusions", i, "reason_category"])
    for line, code in draft.out_of_scope_reasons.items():
        if not reason_code_ok(code):
            bad(["out_of_scope_reasons", line])
    if draft.default_exclusion_reason is not None and not reason_code_ok(draft.default_exclusion_reason):
        bad(["default_exclusion_reason"])
    return errors


def parse_draft(raw: dict[str, Any] | None, *, saving: bool = False) -> Draft:
    """The draft as the model reads it; ``saving`` adds the checks a save must pass (M10b)."""
    draft = _parse_draft(raw)
    if saving:
        errors = reason_code_errors(draft)
        if errors:
            raise StepRefused("DRAFT_INVALID", REASON_CODE_RULE, details={"errors": errors})
    return draft


def _parse_draft(raw: dict[str, Any] | None) -> Draft:
    draft = _validate_draft(raw)
    errors = _field_errors(draft)
    if errors:
        raise StepRefused("DRAFT_INVALID", "the draft does not match the draft shape", details={"errors": errors})
    return draft


def _validate_draft(raw: dict[str, Any] | None) -> Draft:
    try:
        return Draft.model_validate(raw or {})
    except ValidationError as exc:
        # The client's own values (``input``) are not echoed back: a refused
        # draft may be the oversized one.
        errors = [{k: v for k, v in e.items() if k != "input"} for e in json.loads(exc.json(include_url=False))]
        over = [e for e in errors if e.get("type") in _SIZE_ERRORS]
        if over:
            raise StepRefused(
                "DRAFT_TOO_LARGE",
                "the draft is over its size limits: " + ", ".join(_over_limit(e) for e in over),
                details={"errors": errors, "limits": dict(DRAFT_LIMITS)},
            ) from exc
        raise StepRefused(
            "DRAFT_INVALID", "the draft does not match the draft shape", details={"errors": errors},
        ) from exc


def _require(draft: Draft, *fields: str) -> None:
    # A text of white space only is missing too (review of M10b Part A, finding 4).
    missing = [f for f in fields if not (getattr(draft, f).strip() if isinstance(getattr(draft, f), str) else getattr(draft, f))]
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
        pool_min=draft.pool_min,
        pool_max=draft.pool_max,
        out_of_scope_reasons=dict(draft.out_of_scope_reasons),
        default_exclusion_reason=draft.default_exclusion_reason,
    )


def proof_required(draft: Draft) -> bool:
    """Whether the proof answer is still needed (M10b, R4, ``04-shape``).

    It may be empty when the draft holds an inclusion the researcher typed or
    imported that they have not dropped. Decisions are keyed by criterion id;
    a typed inclusion is accepted unless its id is decided ``False``.
    """
    from .intent import CriterionDraft

    for text in draft.extra_inclusions:
        if text.strip() and draft.criteria_decisions.get(CriterionDraft("inclusion", text, "manual").id) is not False:
            return False
    return True


def _required(draft: Draft, *fields: str) -> tuple[str, ...]:
    """``fields`` without ``proof`` when the draft does not need one."""
    if "proof" in fields and not proof_required(draft):
        return tuple(f for f in fields if f != "proof")
    return fields


def _slug_id(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return slug or "column"


def custom_columns(draft: Draft) -> list[dict[str, Any]]:
    """The researcher's own columns as matrix dimensions, each with a unique id.

    An id the column carries (an imported one) is kept when it is unique among
    the suggested columns and the other own columns; otherwise, and for a typed
    column, it is derived from the name: lower case, runs of other characters
    become ``_``, and ``_2``, ``_3`` ... on a clash.
    """
    suggested = {d["id"] for d in _default_matrix_dimensions(draft.playbook or "", draft.unit_of_analysis or "")}
    taken = set(suggested)
    out: list[dict[str, Any]] = []
    for column in draft.custom_matrix_columns:
        base = column.id if column.id and column.id not in taken else _slug_id(column.name)
        cid, n = base, 2
        while cid in taken:
            cid, n = f"{base}_{n}", n + 1
        taken.add(cid)
        out.append({
            "id": cid,
            "name": column.name,
            "description": column.description,
            "target_section_category": column.target_section_category,
            "data_type": column.data_type,
            "required": column.required,
            "fallback_value": column.fallback_value,
        })
    return out


def _column_clash(draft: Draft) -> None:
    """An own column may not share a name with a suggested one (``05-criteria``)."""
    if not draft.playbook or not draft.custom_matrix_columns:
        return
    names = {d["name"].casefold() for d in _default_matrix_dimensions(draft.playbook, draft.unit_of_analysis or "")}
    for i, column in enumerate(draft.custom_matrix_columns):
        if column.name.casefold() in names:
            raise StepRefused(
                "DRAFT_INVALID",
                f"a suggested column is already named {column.name!r}; tick it instead",
                details={"errors": [{
                    "loc": ["custom_matrix_columns", i, "name"],
                    "msg": f"a column named {column.name!r} already exists",
                    "type": "value_error",
                }]},
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
        # M10b (R4): with no proof answer there is no template question to offer.
        "rq_draft": draft_rq(paradigm, draft.topic, draft.unit_of_analysis, draft.proof) if draft.proof.strip() else None,
        "lexicon": PARADIGM_PROFILE[paradigm]["lexicon"],
        "lexicon_warnings": enforce_lexicon(paradigm, draft.topic),
        "proof_required": proof_required(draft),
        # M10b (R3): the chosen playbook's preset, so the browser holds no preset table.
        "pool_preset": pool_preset(playbook),
    }


def pool_preset(playbook: str | None) -> dict[str, int] | None:
    """The playbook's ``target_candidate_pool_size`` preset, or ``None`` for an unknown one."""
    from scholar_protocol.models import PlaybookType
    from scholar_protocol.presets import PRESETS

    try:
        preset = PRESETS[PlaybookType(playbook)]
    except (ValueError, KeyError):
        return None
    return {"min": preset.pool_min, "max": preset.pool_max}


def criteria_with_decisions(draft: Draft) -> list[dict[str, Any]]:
    """Each drafted criterion, verbatim, with its source and the researcher's decision.

    ``status`` is ``accepted``, ``rejected`` or ``undecided``. A criterion the
    researcher typed is accepted unless rejected; one the wizard wrote stays
    ``undecided`` until the researcher accepts or rejects it (INC-22).
    """
    out = []
    for c in draft_criteria(_survey(draft)):
        item = c.as_dict(draft.paradigm or "")
        if c.kind == "exclusion":
            # M10b: a code saved before the rule existed is shown and flagged, not refused.
            item["reason_valid"] = reason_code_ok(c.reason_category)
        decision = draft.criteria_decisions.get(c.id)
        if decision is None:
            item["status"] = "undecided" if c.generated else "accepted"
        else:
            item["status"] = "accepted" if decision else "rejected"
        out.append(item)
    return out


def reason_suggestions(draft: Draft) -> list[dict[str, Any]]:
    """Reason codes offered on the criteria step (M10b, ``05-criteria``).

    Codes already used in this draft come first. ``phrases`` says whether the
    rule-based screener has a phrase list for the code. Nothing is selected.
    """
    from scholar_search.screening import PHRASE_REASON_CODES as EXCLUSION_REASON_PATTERNS

    used: list[str] = []
    for code in [
        *(e.reason_category for e in draft.extra_exclusions),
        *draft.out_of_scope_reasons.values(),
        *([draft.default_exclusion_reason] if draft.default_exclusion_reason else []),
    ]:
        if code not in used:
            used.append(code)
    out = [{"code": c, "source": "used", "phrases": c in EXCLUSION_REASON_PATTERNS} for c in used]
    for code, source in REASON_SUGGESTIONS:
        if code not in used:
            out.append({"code": code, "source": source, "phrases": code in EXCLUSION_REASON_PATTERNS})
    return out


#: The suggested reason codes and where each comes from (``05-criteria``, "Suggested list").
REASON_SUGGESTIONS: tuple[tuple[str, str], ...] = (
    ("OUT_OF_SCOPE", "default"),
    ("LANGUAGE", "wizard"),
    ("INSUFFICIENT_DATA", "wizard"),
    ("WRONG_POPULATION", "protocol_model"),
    ("WRONG_OUTCOME", "protocol_model"),
    ("NO_EMPIRICAL_EVALUATION", "screener"),
    ("LANGUAGE_OR_FORMAT", "screener"),
    ("WRONG_PLATFORM", "example_protocol"),
    ("WRONG_TASK", "example_protocol"),
    ("WRONG_REPORT_TYPE", "example_protocol"),
    ("OUTSIDE_DATE_LANGUAGE", "example_protocol"),
)


def _criteria(draft: Draft) -> dict[str, Any]:
    _require(draft, *_required(draft, "paradigm", "proof"))
    items = criteria_with_decisions(draft)
    accepted_kinds = {i["kind"] for i in items if i["status"] == "accepted"}
    return {
        "criteria": items,
        "undecided": [i["id"] for i in items if i["status"] == "undecided"],
        "missing_sides": [k for k in ("inclusion", "exclusion") if k not in accepted_kinds],
        "reason_suggestions": reason_suggestions(draft),
    }


def _matrix(draft: Draft) -> dict[str, Any]:
    _require(draft, "playbook")
    _column_clash(draft)
    dims = _default_matrix_dimensions(draft.playbook, draft.unit_of_analysis or "the unit of analysis")
    own = custom_columns(draft)
    return {
        "columns": dims,
        "custom_columns": own,
        "selected": [d["name"] for d in dims if d["name"] in draft.matrix_columns] + [c["name"] for c in own],
    }


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
    _require(draft, *_required(
        draft, "topic", "paradigm", "playbook", "unit_of_analysis", "proof", "rqs", "concepts", "title", "lead_researcher",
    ))
    _column_clash(draft)
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
    # The ticked suggested columns in the playbook's order, then the researcher's
    # own in the order entered (M10b); before M10b a custom name was dropped.
    dims = _default_matrix_dimensions(draft.playbook, draft.unit_of_analysis)
    survey.matrix_dimensions = [d for d in dims if d["name"] in draft.matrix_columns] + custom_columns(draft)
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


def _write_draft_records(target: Path, record: dict[str, Any] | None, agent: str) -> None:
    """The draft's proposals and check dismissals, as the workspace's record (M10b).

    The files are the record; the journal rows index them.
    """
    from . import checks, proposals

    lines = proposals.genesis_lines(record)
    proposals.write_jsonl(target / proposals.PROPOSALS_FILE, lines)
    dismissals = checks.genesis_lines(record)
    proposals.write_jsonl(target / checks.DISMISSALS_FILE, dismissals)
    # A failed journal write fails genesis (a new folder is then removed), as the journal rule asks.
    from scholar_harness.workspace.audit import append_event

    tally = proposals.counts(lines)
    append_event(
        target, "PROPOSALS_RECORDED",
        f"{tally['proposed']} suggestions recorded from the draft; {tally['in_protocol']} applied and in the protocol",
        agent=agent, parameters=tally, outputs=[proposals.PROPOSALS_FILE],
    )
    append_event(
        target, "CHECK_DISMISSALS_RECORDED",
        f"{len(dismissals)} check dismissals and restores carried from the draft",
        agent=agent, parameters=checks.dismissal_counts(dismissals), outputs=[checks.DISMISSALS_FILE],
    )


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
    origin: dict[str, Any] | None = None,
    record: dict[str, Any] | None = None,
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

    ``record`` is the draft record (M10b): its ``proposals`` and
    ``check_dismissals`` become ``audit/proposals.jsonl`` and
    ``audit/check_dismissals.jsonl``, written with the other genesis files
    (always, empty when there is nothing, so the preview's file list is exact).
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
        # M10b (09-start-from-protocol): a draft started from an earlier protocol
        # keeps the default GENESIS summary and adds one sentence naming the source.
        from .importer import genesis_sentence

        added = genesis_sentence(origin)
        result = emit_workspace(
            intent, target_dir=target, replace=replace, discard_screening_binding=discard,
            agent=agent, recon_context=context, source_note=added.strip(),
            protocol_origin="import" if added else "inception",
            before_log=lambda ws: _write_draft_records(ws, record, agent),
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
