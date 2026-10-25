"""UAV research-layer query configuration — DOMAIN CONFIG OUT OF THE KIT.

Researcher decision 2026-10-17: the scholar-search-kit stays domain-neutral.
The compaction behavior that produced the definitive r3/r3b arXiv leg is
recreated EXACTLY here, at the harness/driver layer, by injecting research
configuration into the generic kit knobs (ArxivProvider(compact_stoplist=...,
compact_stem_families=...)). Kit defaults are EMPTY; without research config
the compact query is the pure single-token translation.

Lineage (research-level, journaled): arXiv Lucene does NO stemming, and the
earlier r2 compaction revision was an inert no-op; the r3 fix enumerated the
weed-stem morphology family and recovered the arXiv-native sentinel
2609.05762 ('Weedy Rice') organically through the boolean search (no
id_list augmentation). The bytestoplist drops bare single-token heads that
are too generic as standalone all: terms for this domain. Both value sets
were authorized live and are preserved verbatim below, so any re-harvest
reproduces the r3-emitted string byte-for-byte (verified by the parity
probe in the same run of _drivers/genericity_probe.py).
"""

RESEARCH_COMPACT_STOPLIST = ("aerial", "orthomosaic", "crop")
RESEARCH_COMPACT_STEM_FAMILIES = {"weed": ("weedy", "weediness")}

# Recorded r3/r3b emitted compact string (parity target).
R3_RECORDED_EMITTED_QUERY = (
    "(all:UAV OR all:UAS OR all:drone OR all:drones) AND "
    "(all:weed OR all:weeds OR all:crop-weed OR all:weedy OR all:weediness) AND "
    "(all:mapping OR all:detection OR all:segmentation OR all:classification "
    "OR all:monitoring OR all:localization)"
)


def build_protocol_boolean_query(protocol_path):
    """Build the 3-cluster boolean string from the fused protocol (kernel used by all drivers)."""
    import json
    from pathlib import Path

    proto = json.loads(Path(protocol_path).read_text(encoding="utf-8"))
    cc = proto["search_strategy"]["core_concepts"]
    clusters = []
    for c in cc:
        ops = (c.get("boolean_operator") or "OR").upper()
        terms = [c["concept"]] + list(c["synonyms"])
        clusters.append((" " + ops + " ").join(f'"{t}"' for t in terms))
    return "(" + ") AND (".join(clusters) + ")"


def make_research_arxiv_provider():
    """ArxivProvider carrying the research-level compaction config (kit stays clean)."""
    from scholar_search.providers import ArxivProvider

    return ArxivProvider(
        compact_stoplist=RESEARCH_COMPACT_STOPLIST,
        compact_stem_families=RESEARCH_COMPACT_STEM_FAMILIES,
    )


def emitted_compact_query(provider, query_text):
    """Return the exact compact search_query the provider will send (probe helper)."""
    from scholar_search.models import Query

    q = Query(text=query_text, id="PROBE-PARITY", year_min=2020, year_max=2026)
    translated = provider.translator.translate(q)
    if len(translated) > 300 and " AND " in query_text:
        import re as _re

        compact_clauses = []
        for clause in query_text.split(" AND "):
            phrases = _re.findall(r'"([^"]*)"', clause)
            bare = _re.sub(r'"[^"]*"', " ", clause)
            tokens = []
            for p in phrases:
                p_toks = _re.findall(r"[a-zA-Z0-9_-]{2,}", p)
                if len(p_toks) == 1:
                    tokens.append(p_toks[0])
            tokens.extend(_re.findall(r"[a-zA-Z0-9_-]{3,}", bare))
            seen, deduped = set(), []
            for t in tokens:
                tl = t.lower()
                if tl in seen:
                    continue
                seen.add(tl)
                if t.upper() in ("AND", "OR", "NOT"):
                    continue
                if tl in provider.compact_stoplist:
                    continue
                deduped.append(t)
            for prefix, extras in provider.compact_stem_families:
                if any(t.lower().startswith(prefix) for t in deduped):
                    for extra in extras:
                        if extra not in deduped:
                            deduped.append(extra)
            if deduped:
                compact_clauses.append(
                    "(" + " OR ".join(f"all:{t}" for t in deduped[:6]) + ")"
                )
        return " AND ".join(compact_clauses)
    return translated


# Research-level screening fallback signals (withdrawn from the kit worktree,
# preserved verbatim from the authorized L1-L6-era screening signals). The
# harness triage driver consumes these as config; the kit never embeds them.
RESEARCH_SCREENING_FALLBACK_SIGNALS = {
    "WRONG_PLATFORM": [
        "satellite-only",
        "sentinel-2 only",
        "landsat only",
        "ground robot only",
        "handheld camera",
        "laboratory imaging",
        "greenhouse pot",
        "proximal sensing only",
    ],
    "WRONG_TASK": [
        "forest fire",
        "wildfire",
        "flood monitoring",
        "ice detection",
        "de-icing",
        "indoor localization",
        "wild boar",
        "rice lodging",
        "wheat lodging",
        "disease detection",
        "vine disease",
        "soybean disease",
        "fruit counting",
        "boll detection",
        "water hyacinth",
        "aquatic weed",
        "turf grass",
    ],
    "WRONG_REPORT_TYPE": [
        "systematic literature review",
        "bibliometric review",
        "scoping review",
        "comprehensive overview",
        "survey of deep learning",
        "a review of",
        "this review explores",
        "this review provides",
        "editorial",
    ],
    "OUTSIDE_DATE_LANGUAGE": [
        "non-english",
        "in chinese",
        "in spanish",
        "in portuguese",
    ],
}
