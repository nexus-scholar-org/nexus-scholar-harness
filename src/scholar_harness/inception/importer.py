"""Start an inception draft from an existing protocol (M10b, ``09-start-from-protocol``).

The researcher's earlier answers arrive as their own text: a workspace's
``protocol.json`` or a picked ``protocol.json`` / ``intent.json`` is mapped onto
the inception :class:`~scholar_harness.inception.steps.Draft` field by field,
without a language model, and every value that cannot come across, or comes
across changed, is listed (``lost``) instead of dropped or guessed. Nothing in
the source is ever written.

:func:`read_source` reads and validates the source; :func:`map_source` builds the
draft and the report. The HTTP route (``POST /inception/drafts/import``) stores
the draft with an ``origin`` record beside it.
"""

from __future__ import annotations

import base64
import binascii
import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .drafts import DraftRefused
from .intent import PARADIGM_PROFILE, VERIFICATION_TRUST_THRESHOLD, slugify

#: A protocol file is a few kilobytes (the UAV one about 22 KB); this refuses a
#: file that cannot be one before it is parsed.
MAX_SOURCE_BYTES = 1024 * 1024
#: The only ``$schema`` a v1 protocol writes (``scholar_protocol/models.py``).
SUPPORTED_SCHEMA = "schemas/v1/protocol.schema.json"
#: The wizard's prefix for the inclusion it writes from the proof answer (``intent.draft_criteria``).
PROOF_PREFIX = "Reports the gold-standard proof — "
#: The steps that hold imported values, each marked until the researcher opens it.
IMPORTED_STEPS = ("scope", "direction", "shape", "criteria", "review")
_PROTOCOL_KEYS = ("epistemology", "search_strategy", "screening_criteria")
_INTENT_KEYS = ("inclusion_criteria", "research_questions")


@dataclass
class Source:
    """A read and validated source: its shape, its data as the model dumps it, and its identity."""

    kind: str  # "workspace" | "file"
    label: str
    read: str  # "protocol" | "intent"
    data: dict[str, Any]
    slug: str | None = None
    file_name: str | None = None
    protocol_id: str | None = None
    created_at: str | None = None
    fingerprint: str | None = None

    def summary(self, target_slug: str) -> dict[str, Any]:
        out: dict[str, Any] = {
            "kind": self.kind,
            "label": self.label,
            "read": self.read,
            "schema": self.data.get("$schema") if self.read == "protocol" else None,
            "protocol_id": self.protocol_id,
            "protocol_created_at": self.created_at,
            "protocol_fingerprint": self.fingerprint,
            "target_slug": target_slug,
            "collides_with_source": self.kind == "workspace" and target_slug == self.slug,
        }
        if self.slug is not None:
            out["slug"] = self.slug
        if self.file_name is not None:
            out["file_name"] = self.file_name
        return out


def _refuse(code: str, message: str, status: int, details: dict[str, Any] | None = None) -> DraftRefused:
    return DraftRefused(code, message, status=status, details=details)


def _bytes_of(source: dict[str, Any], workspaces_root: Path) -> tuple[bytes, str, str | None, str | None]:
    """``(bytes, label, slug, file_name)`` of the requested source."""
    from scholar_harness.workspace import catalog

    if source.get("kind") == "workspace":
        slug = str(source.get("slug") or "")
        try:
            folder = catalog._target(Path(workspaces_root), slug)
        except catalog.WorkspaceRefused as exc:
            raise _refuse(exc.code, exc.message, exc.status) from exc
        path = folder / "protocol.json"
        if not path.is_file():
            raise _refuse("IMPORT_SOURCE_NOT_FOUND", f"no protocol.json in workspace {slug!r}", 404, {"slug": slug})
        try:
            return path.read_bytes(), slug, slug, None
        except OSError as exc:
            raise _refuse("IMPORT_SOURCE_UNREADABLE", f"the workspace's protocol cannot be read: {exc}", 422, {"reason": "unreadable"}) from exc
    file_name = str(source.get("file_name") or "")
    try:
        raw = base64.b64decode(str(source.get("content_base64") or ""), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise _refuse("IMPORT_SOURCE_UNREADABLE", "the file content is not base64", 422, {"reason": "not_base64"}) from exc
    if len(raw) > MAX_SOURCE_BYTES:
        raise _refuse(
            "IMPORT_SOURCE_TOO_LARGE", "a protocol file is a few kilobytes; this one is over 1 MiB", 413,
            {"max_bytes": MAX_SOURCE_BYTES, "got_bytes": len(raw)},
        )
    return raw, file_name, None, file_name


def _fingerprint(protocol: Any) -> str:
    """The same fingerprint the compiler and the discovery routes give a protocol."""
    from scholar_protocol.canonical import canonical_fingerprint

    return canonical_fingerprint(protocol)


def read_source(source: dict[str, Any], workspaces_root: Path) -> Source:
    """Read, parse and validate one source; refuse with a typed code otherwise."""
    from scholar_protocol.intent import IntentPacket
    from scholar_protocol.models import ResearchProtocol

    raw, label, slug, file_name = _bytes_of(source, workspaces_root)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise _refuse("IMPORT_SOURCE_UNREADABLE", "the file is not UTF-8 text", 422, {"reason": "not_utf8"}) from exc
    try:
        data = json.loads(text)
    except ValueError as exc:
        raise _refuse("IMPORT_SOURCE_UNREADABLE", "the file is not JSON", 422, {"reason": "not_json"}) from exc
    if not isinstance(data, dict):
        raise _refuse("IMPORT_SOURCE_UNREADABLE", "the file is JSON but not a JSON object", 422, {"reason": "not_an_object"})
    kind = "workspace" if slug is not None else "file"
    if all(k in data for k in _PROTOCOL_KEYS):
        schema = data.get("$schema")
        if schema is not None and schema != SUPPORTED_SCHEMA:
            raise _refuse(
                "IMPORT_PROTOCOL_VERSION_UNSUPPORTED", f"this protocol says {schema!r}; this app reads {SUPPORTED_SCHEMA}", 422,
                {"found": schema, "supported": [SUPPORTED_SCHEMA]},
            )
        try:
            model = ResearchProtocol.model_validate(data)
        except ValidationError as exc:
            raise _refuse("PROTOCOL_INVALID", "the protocol does not pass the protocol check", 422, {"shape": "protocol", "errors": _errors(exc)}) from exc
        dumped = model.model_dump(mode="json", by_alias=True)
        return Source(
            kind, label, "protocol", dumped, slug=slug, file_name=file_name,
            protocol_id=dumped.get("protocol_id"), created_at=dumped.get("created_at"), fingerprint=_fingerprint(model),
        )
    if all(k in data for k in _INTENT_KEYS):
        try:
            model = IntentPacket.model_validate(data)
        except ValidationError as exc:
            raise _refuse("PROTOCOL_INVALID", "the intent does not pass the intent check", 422, {"shape": "intent", "errors": _errors(exc)}) from exc
        dumped = model.model_dump(mode="json")
        return Source(
            kind, label, "intent", dumped, slug=slug, file_name=file_name,
            protocol_id=dumped.get("protocol_id"), created_at=dumped.get("genesis_timestamp"), fingerprint=None,
        )
    missing = [k for k in (*_PROTOCOL_KEYS, *_INTENT_KEYS) if k not in data]
    raise _refuse("IMPORT_NOT_A_PROTOCOL", "this JSON is neither a protocol nor an intent", 422, {"missing": missing})


def _errors(exc: ValidationError) -> list[dict[str, Any]]:
    """The validator's errors without echoing the source's values."""
    return [{k: v for k, v in e.items() if k != "input"} for e in json.loads(exc.json(include_url=False))]


def _view(source: Source) -> dict[str, Any]:
    """One reading of either shape, field by field."""
    d = source.data
    if source.read == "protocol":
        meta, epi, ss, sc = d.get("metadata") or {}, d.get("epistemology") or {}, d.get("search_strategy") or {}, d.get("screening_criteria") or {}
        dates = ss.get("date_range") or {}
        return {
            "title": meta.get("title"), "lead_researcher": meta.get("lead_researcher"), "venue": meta.get("target_venue_type"),
            "timeline_weeks": meta.get("timeline_weeks"), "paradigm": epi.get("primary_paradigm"),
            "secondary_paradigm": epi.get("secondary_paradigm"), "playbook": d.get("playbook_type"),
            "unit": epi.get("unit_of_analysis"), "languages": ss.get("languages"),
            "start_year": dates.get("start_year"), "end_year": dates.get("end_year"),
            "rqs": d.get("research_questions") or [], "concepts": ss.get("core_concepts") or [],
            "inclusions": sc.get("inclusion") or [], "exclusions": sc.get("exclusion") or [],
            "seeds": ss.get("golden_seeds") or [], "threshold": (d.get("verification") or {}).get("minimum_trust_score_threshold"),
            "matrix": d.get("matrix_dimensions") or [], "pool": ss.get("target_candidate_pool_size") or None,
            "method": d.get("method"),
        }
    pool = {"min": d.get("pool_min"), "max": d.get("pool_max")} if d.get("pool_max") is not None else None
    return {
        "title": d.get("title"), "lead_researcher": d.get("lead_researcher"), "venue": d.get("target_venue_type"),
        "timeline_weeks": d.get("timeline_weeks"), "paradigm": d.get("primary_paradigm"),
        "secondary_paradigm": d.get("secondary_paradigm"), "playbook": d.get("playbook_type"),
        "unit": d.get("unit_of_analysis"), "languages": d.get("languages"),
        "start_year": d.get("start_year"), "end_year": d.get("end_year"),
        "rqs": d.get("research_questions") or [], "concepts": d.get("core_concepts") or [],
        "inclusions": d.get("inclusion_criteria") or [], "exclusions": d.get("exclusion_criteria") or [],
        "seeds": d.get("golden_seeds") or [], "threshold": d.get("minimum_trust_score_threshold"),
        "matrix": d.get("matrix_dimensions") or [], "pool": pool, "method": None,
    }


def normalise_reason(code: str | None) -> str:
    """A reason code in the form the draft accepts (``05-criteria``): never a refusal."""
    text = re.sub(r"[^A-Z0-9_]", "_", str(code or "").upper())
    text = text.lstrip("_0123456789")[:40]
    return text if len(text) >= 3 else "OUT_OF_SCOPE"


def map_source(source: Source) -> dict[str, Any]:
    """``{draft, carried, lost, needs_you, earlier_pool}`` for one source (the mapping table of ``09``)."""
    from .genesis import _default_matrix_dimensions
    from .steps import REASON_CODE, custom_columns, parse_draft

    v = _view(source)
    carried: list[dict[str, Any]] = []
    lost: list[dict[str, Any]] = []
    needs: list[str] = []

    def carry(field: str, origin: str) -> None:
        carried.append({"field": field, "from": origin, "class": "exact"})

    draft: dict[str, Any] = {"topic": ""}
    for field, key in (("title", "title"), ("lead_researcher", "lead_researcher"), ("venue", "venue")):
        if v.get(key):
            draft[field] = v[key]
            carry(field, key)
    if isinstance(v.get("timeline_weeks"), int):
        draft["timeline_weeks"] = v["timeline_weeks"]
        carry("timeline_weeks", "timeline_weeks")
    if v.get("paradigm") in PARADIGM_PROFILE:
        draft["paradigm"] = v["paradigm"]
        carry("paradigm", "primary_paradigm")
    else:
        needs.append("paradigm")
    if v.get("secondary_paradigm"):
        draft["secondary_paradigm"] = v["secondary_paradigm"]
    if v.get("playbook"):
        draft["playbook"] = v["playbook"]
        carry("playbook", "playbook_type")
    if v.get("unit"):
        draft["unit_of_analysis"] = v["unit"]
        carry("unit_of_analysis", "unit_of_analysis")
    else:
        needs.append("unit")
    if v.get("languages"):
        draft["languages"] = list(v["languages"])
    for year in ("start_year", "end_year"):
        if v.get(year) is not None:
            draft[year] = v[year]

    rqs = [rq.get("text", "") for rq in v["rqs"] if rq.get("text")]
    if rqs:
        draft["rqs"] = rqs
        carry("rqs", "research_questions[].text")
        lost.append({"what": "facets", "count": len(rqs)})

    concepts = []
    for c in v["concepts"]:
        concepts.append({"concept": c.get("concept", ""), "synonyms": list(c.get("synonyms") or [])})
        if str(c.get("boolean_operator") or "OR").upper() != "OR":
            lost.append({"what": "operator", "concept": c.get("concept"), "operator": c.get("boolean_operator")})
    if concepts:
        draft["concepts"] = concepts
        carry("concepts", "core_concepts")

    rq_ids = sorted({rq.get("id") for rq in v["rqs"] if rq.get("id")})
    inclusions = list(v["inclusions"])
    if inclusions and str(inclusions[0].get("criterion", "")).startswith(PROOF_PREFIX):
        # The researcher's own earlier proof answer, written back word for word.
        draft["proof"] = str(inclusions[0]["criterion"])[len(PROOF_PREFIX):]
        carry("proof", "the wizard's proof criterion")
        # H-run-small-fixes (finding 1): with other inclusions the proof writes no
        # criterion, so the protocol's criterion is kept as a typed inclusion
        # (the import keeps every inclusion; the researcher may drop it).
        if len(inclusions) == 1:
            inclusions = inclusions[1:]
    draft["extra_inclusions"] = [c.get("criterion", "") for c in inclusions]
    exclusions = []
    for i, c in enumerate(v["exclusions"]):
        code = c.get("reason_category")
        label = c.get("id") or f"EXC-{i + 1:02d}"
        if not code:
            exclusions.append({"criterion": c.get("criterion", ""), "reason_category": "OUT_OF_SCOPE"})
            lost.append({"what": "category", "id": label})
            continue
        fixed = code if REASON_CODE.match(code) else normalise_reason(code)
        if fixed != code:
            lost.append({"what": "reason_code", "id": label, "original": code, "code": fixed})
        exclusions.append({"criterion": c.get("criterion", ""), "reason_category": fixed})
    draft["extra_exclusions"] = exclusions
    if inclusions or exclusions:
        carry("criteria", "screening_criteria")
    for c in [*v["inclusions"], *v["exclusions"]]:
        maps = sorted(c.get("maps_to_rqs") or [])
        if rq_ids and maps and maps != rq_ids:
            lost.append({"what": "maps", "id": c.get("id"), "rqs": maps})
    if not draft["extra_inclusions"] and not draft.get("proof"):
        needs.append("proof")

    seeds, bad = [], 0
    from .steps import _doi_list

    for doi in v["seeds"]:
        try:
            seeds.extend(d for d in _doi_list([doi]) if d.lower() not in {s.lower() for s in seeds})
        except ValueError:
            bad += 1
    if seeds:
        draft["golden_seeds"] = seeds
        carry("golden_seeds", "golden_seeds")
    if bad:
        lost.append({"what": "seeds", "count": bad})

    threshold = v.get("threshold")
    if threshold is not None:
        draft["verification_checks"] = threshold > 0
        if threshold not in (0, 0.0, VERIFICATION_TRUST_THRESHOLD):
            lost.append({"what": "threshold", "value": threshold})

    defaults = {d["name"].casefold(): d for d in _default_matrix_dimensions(draft.get("playbook") or "", draft.get("unit_of_analysis") or "")}
    ticked, own = [], []
    compared = ("description", "data_type", "required", "fallback_value", "target_section_category")
    for dim in v["matrix"]:
        default = defaults.get(str(dim.get("name") or "").casefold())
        if default is not None:
            # A column named like a suggested one is the suggestion, ticked; the
            # suggestion's own wording compiles. Say so when the source's differed.
            ticked.append(default["name"])
            if any(dim.get(k) != default.get(k) for k in compared):
                lost.append({"what": "matrix_default", "name": default["name"]})
        else:
            own.append({k: dim.get(k) for k in ("id", "name", "description", "data_type", "required", "fallback_value", "target_section_category")})
    if ticked:
        draft["matrix_columns"] = ticked
    if own:
        draft["custom_matrix_columns"] = [{k: val for k, val in col.items() if val is not None} for col in own]
        carry("custom_matrix_columns", "matrix_dimensions")

    if source.read == "protocol":
        lost.append({"what": "rationale"})
    lost.append({"what": "preset"})
    if v.get("method"):
        lost.append({"what": "method"})
    if source.kind == "workspace":
        lost.append({"what": "grounding"})
    needs.insert(0, "topic")

    parsed = parse_draft(draft, saving=True)  # the draft limits and shape apply as to a typed draft
    if own:
        for col, derived in zip(own, custom_columns(parsed)):
            if col.get("id") and derived["id"] != col["id"]:
                lost.append({"what": "matrix_id", "name": col["name"], "id": col["id"], "new": derived["id"]})
    pool = v.get("pool")
    earlier = {"min": pool.get("min"), "max": pool.get("max")} if isinstance(pool, dict) and pool.get("max") is not None else None
    return {"draft": draft, "carried": carried, "lost": lost, "needs_you": needs, "earlier_pool": earlier}


def report(source: Source, mapped: dict[str, Any]) -> dict[str, Any]:
    """The dry-run answer: the source, the draft and what changed."""
    target = slugify(mapped["draft"].get("title") or "")
    return {
        "source": source.summary(target),
        "draft": mapped["draft"],
        "carried": mapped["carried"],
        "lost": mapped["lost"],
        "needs_you": mapped["needs_you"],
        "earlier_pool": mapped["earlier_pool"],
    }


def origin_record(source: Source, mapped: dict[str, Any]) -> dict[str, Any]:
    """The ``origin`` kept beside the created draft."""
    target = slugify(mapped["draft"].get("title") or "")
    return {
        "kind": "import",
        "source": source.summary(target),
        "imported_at": datetime.now(UTC).isoformat(),
        "checked": {step: False for step in IMPORTED_STEPS},
        "report": {"carried": mapped["carried"], "lost": mapped["lost"], "needs_you": mapped["needs_you"]},
        "earlier_pool": mapped["earlier_pool"],
    }


def genesis_sentence(origin: dict[str, Any] | None) -> str:
    """The sentence the GENESIS row adds for a draft started from an earlier protocol."""
    if not origin or origin.get("kind") != "import":
        return ""
    src = origin.get("source") or {}
    fingerprint = src.get("protocol_fingerprint") or "not computed (an intent file)"
    date = str(origin.get("imported_at") or "")[:10]
    return f" Started from {src.get('label')}, protocol {fingerprint}, imported {date}."
