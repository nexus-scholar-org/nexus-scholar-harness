import re
from dataclasses import dataclass, field

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

# Phase-4 trust threshold when the verification checks are enabled (else 0.0).
VERIFICATION_TRUST_THRESHOLD = 6.0

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
    #: DOIs the discovery Recall check looks for (M4d): the pool anchors the researcher kept.
    golden_seeds: list[str] = field(default_factory=list)
    #: The number of records the researcher plans to screen (M10b, R3); ``None``
    #: keeps the playbook preset. ``pool_max`` alone means "up to", from 0.
    pool_min: int | None = None
    pool_max: int | None = None
    #: The reason code of each out-of-scope line, keyed by the line's text (M10b).
    out_of_scope_reasons: dict[str, str] = field(default_factory=dict)
    #: The reason code of the paradigm's default exclusion (M10b); ``None`` is ``OUT_OF_SCOPE``.
    default_exclusion_reason: str | None = None
    #: H-run-small-fixes (finding 1): whether the proof answer writes the inclusion
    #: "Reports the gold-standard proof — …". The browser draft sets it only when
    #: no typed inclusion is left (``steps.proof_required``); the CLI wizard keeps it.
    proof_criterion: bool = True


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


def slugify(text: str) -> str:
    import re

    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    return re.sub(r"[-\s]+", "-", text).strip("-")


def draft_rq(paradigm: str, topic: str, unit: str, proof: str) -> str:
    """The paradigm's RQ1 draft (Stage 4a), shared by the wizard and the step API."""
    return PARADIGM_PROFILE[paradigm]["rq_template"].format(topic=topic, unit=unit, proof=proof)


#: The reason code an exclusion carries when the researcher chose none.
DEFAULT_REASON = "OUT_OF_SCOPE"

# INC-22: where a criterion came from. ``generated`` sources were written by the
# wizard, not typed by the researcher; their acceptance prompt defaults to "no".
CRITERION_SOURCES: dict[str, tuple[str, bool]] = {
    "proof": ("written by the wizard from your proof answer", True),
    "paradigm_default": ("the {paradigm} paradigm's default exclusion, written by the wizard", True),
    "out_of_scope": ("your out-of-scope answer", False),
    "manual": ("typed by you", False),
}


@dataclass(frozen=True)
class CriterionDraft:
    """One screening criterion the wizard proposes, before the researcher accepts it."""

    kind: str  # "inclusion" | "exclusion"
    criterion: str
    source: str  # a key of CRITERION_SOURCES
    reason_category: str | None = None

    @property
    def generated(self) -> bool:
        return CRITERION_SOURCES[self.source][1]

    @property
    def id(self) -> str:
        """Content-derived: editing a criterion's text makes it a new, undecided one."""
        import hashlib

        raw = "\x1f".join((self.kind, self.source, self.criterion, self.reason_category or ""))
        return "crit_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:12]

    def source_label(self, paradigm: str) -> str:
        return CRITERION_SOURCES[self.source][0].format(paradigm=paradigm)

    def as_dict(self, paradigm: str) -> dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "criterion": self.criterion,
            "reason_category": self.reason_category,
            "source": self.source,
            "source_label": self.source_label(paradigm),
            "generated": self.generated,
        }


def split_out_of_scope(items: list[str]) -> list[str]:
    """Each out-of-scope item on its own (finding 2): semicolons and line breaks separate items.

    Commas do not: "satellite, aerial or ground imagery" is one item. Blank
    pieces are dropped and a repeat is kept once, in order.
    """
    out: list[str] = []
    for item in items:
        for piece in re.split(r"[;\n]", item or ""):
            piece = piece.strip()
            if piece and piece not in out:
                out.append(piece)
    return out


def draft_criteria(survey: Survey) -> list[CriterionDraft]:
    """Every criterion the wizard proposes, in order, each tagged with its source.

    The rules are the historic ``make_intent`` rules: the proof answer becomes an
    inclusion criterion; out-of-scope items and manual exclusions become
    exclusions; with no exclusion at all, the paradigm's default is proposed.
    H-run-small-fixes (finding 1): the proof answer ("what would a reviewer
    accept as proof") is not a screening rule, so it writes its criterion only
    as the fallback inclusion of a draft without a typed one
    (``survey.proof_criterion``); it still feeds the rationale and the template
    research question. (finding 2): an out-of-scope answer typed as one line
    of items separated by semicolons gives one candidate per item, each
    undecided until accepted.

    M10b: an empty proof answer writes no proof criterion (the proof may be
    empty when the draft holds a typed inclusion, ``04-shape``), and the reason
    of an out-of-scope line or of the paradigm default is the researcher's when
    set. The default reason stays ``OUT_OF_SCOPE``, so the ids of drafts that set
    none are unchanged.
    """
    drafts = []
    if survey.proof.strip() and survey.proof_criterion:
        drafts.append(CriterionDraft("inclusion", f"Reports the gold-standard proof — {survey.proof}", "proof"))
    drafts += [CriterionDraft("inclusion", c, "manual") for c in survey.extra_inclusions]
    reasons = survey.out_of_scope_reasons or {}
    exclusions = [
        CriterionDraft("exclusion", item, "out_of_scope", reasons.get(item) or DEFAULT_REASON)
        for item in split_out_of_scope(survey.out_of_scope)
    ]
    exclusions += [CriterionDraft("exclusion", text, "manual", category) for text, category in survey.extra_exclusions]
    if not exclusions:
        default_exclusion = PARADIGM_PROFILE[survey.paradigm]["negative_exclusions"]
        exclusions.append(
            CriterionDraft("exclusion", default_exclusion, "paradigm_default", survey.default_exclusion_reason or DEFAULT_REASON)
        )
    return drafts + exclusions


def _answer(text: str) -> str:
    """An answer as it reads inside a sentence: trimmed, without one final full stop."""
    text = (text or "").strip()
    if text.endswith(".") and not text.endswith(".."):
        text = text[:-1].rstrip()
    return text


def make_intent(
    survey: Survey,
    slug: str,
    genesis_timestamp: str,
    criteria: list[CriterionDraft] | None = None,
) -> dict:
    """Assemble the ``IntentPacket`` dict (Stage 4) for the deterministic compiler.

    ``criteria`` are the criteria the researcher accepted (INC-22). ``None`` keeps
    every drafted criterion, which only the deterministic placeholder protocol of
    ``--scaffold-only`` relies on.
    """
    all_rqs = [f"RQ{i}" for i, _ in enumerate(survey.rqs, start=1)]
    chosen = draft_criteria(survey) if criteria is None else criteria

    inclusion = [{"criterion": c.criterion, "maps_to_rqs": all_rqs} for c in chosen if c.kind == "inclusion"]
    exclusion = [
        {"criterion": c.criterion, "reason_category": c.reason_category or DEFAULT_REASON, "maps_to_rqs": all_rqs}
        for c in chosen
        if c.kind == "exclusion"
    ]
    # The rationale names only the out-of-scope items the researcher accepted.
    out_of_scope = [c.criterion for c in chosen if c.source == "out_of_scope"]  # each accepted item

    # Strict run 2026-11-13 (finding 9): the answers are pasted as written, so
    # each follows a colon and loses a final full stop of its own ("..." stays).
    # M10b: an empty proof answer leaves its sentence out.
    proof = _answer(survey.proof)
    rationale = (
        f"{survey.paradigm} stance via the {survey.playbook} playbook. "
        f"Unit of analysis: {_answer(survey.unit_of_analysis)}. "
        + (f"Convincing evidence: {proof}. " if proof else "")
        + f"Explicitly out of scope: {'; '.join(_answer(o) for o in out_of_scope) or 'none specified'}."
    )

    languages = survey.languages or ["en"]

    intent = {
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
        # M10b (R3): the researcher's planned number, else the playbook preset
        # (``None``). "Up to N" alone is from 0, so the preset's minimum can
        # never exceed the stated maximum.
        "pool_min": (survey.pool_min or 0) if survey.pool_max is not None else None,
        "pool_max": survey.pool_max,
        "inclusion_criteria": inclusion,
        "exclusion_criteria": exclusion,
        "two_tier_screening": True,
        "matrix_dimensions": survey.matrix_dimensions,
        "retraction_check_required": True,
        "coi_and_funding_audit_required": True,
        "reproducibility_das_cas_check": True,
        "minimum_trust_score_threshold": survey.trust_score_threshold,
    }
    # Only when the researcher kept seeds, so an intent without them is unchanged (M4d).
    if survey.golden_seeds:
        intent["golden_seeds"] = list(survey.golden_seeds)
    return intent


