"""Pure-Python term-frequency distiller (M0.2, M0.4).

Reads a probe pool (spec 04_memory_and_cache.md section 5) and emits a
deterministic micro-taxonomy plus metric/dataset keyword counts and school
groupings (section 6).  Stdlib + regex only; no scikit-learn / keybert.

The ``freq`` of each micro-taxonomy term counts distinct evidence docs (docs
that carry a DOI), so ``freq == len(anchor_dois)`` always holds.

Since M0.4 (T4.5) the metric/dataset/school pattern tables are pluggable via
:class:`DomainLexicon`.  ``distill_pool(pool, lexicon=DEFAULT_LEXICON)``
keeps today's tables verbatim (byte-identical output with the default); any
research domain can register its own patterns and pass its lexicon in.
Micro-taxonomy frequency extraction is purely empirical and field-agnostic;
it never consults the lexicon.
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

from .lexicon import DEFAULT_LEXICON, DomainLexicon

_WORD_RE = re.compile(r"[a-z0-9]+(?:[-'&][a-z0-9]+)*")

_STOPWORDS = frozenset({
    "a", "about", "above", "after", "again", "against", "al", "all",
    "also", "although", "am", "an", "and", "another", "any", "approach",
    "approaches", "are", "as", "at", "based", "be", "because", "been",
    "before", "being", "below", "between", "both", "but", "by", "can",
    "could", "dataset", "datasets", "did", "do", "does", "doing", "down",
    "due", "during", "each", "et", "few", "for", "from", "further", "had",
    "has", "have", "having", "he", "her", "here", "hers", "herself",
    "him", "himself", "his", "how", "however", "i", "if", "in",
    "including", "into", "is", "it", "its", "itself", "just", "may", "me",
    "method", "methods", "might", "more", "moreover", "most", "much",
    "must", "my", "myself", "new", "no", "nor", "not", "now", "of", "off",
    "on", "once", "one", "only", "or", "other", "our", "ours",
    "ourselves", "out", "over", "overall", "own", "paper", "papers",
    "per", "present", "presented", "presenting", "presents", "propose",
    "proposed", "proposes", "provide", "provided", "provides", "recent",
    "recently", "research", "results", "same", "several", "she",
    "should", "show", "showed", "shows", "significant", "significantly",
    "so", "some", "study", "studies", "such", "than", "that", "the",
    "their", "theirs", "them", "themselves", "then", "there", "these",
    "they", "this", "those", "through", "thus", "to", "too", "under",
    "until", "up", "use", "used", "using", "various", "very", "via",
    "was", "we", "were", "what", "when", "where", "whereas", "which",
    "while", "who", "whom", "why", "will", "with", "within", "without",
    "would", "you", "your", "yours", "yourself", "yourselves",
})

def _table(patterns: dict[str, str]) -> list[tuple[str, re.Pattern[str]]]:
    """Compile a lexicon's ``pattern -> label`` mapping into ``(label, pattern)`` pairs.

    Insertion order is preserved; downstream sorting (labels in keyword
    counts, schools by ``(-n, label)``) keeps output deterministic.
    """
    return [(label, re.compile(pattern)) for pattern, label in patterns.items()]


def _evidence_docs(pool: dict[str, Any]) -> list[tuple[str, str]]:
    """Return ``(doi, lowercased title + abstract)`` for docs that carry a DOI."""
    docs = pool.get("docs", [])
    if not isinstance(docs, list):
        return []
    evidence: list[tuple[str, str]] = []
    for doc in docs:
        if not isinstance(doc, dict):
            continue
        doi = doc.get("doi")
        if not doi:
            continue
        title = doc.get("title")
        abstract = doc.get("abstract")
        text = " ".join(
            part for part in (str(title or ""), str(abstract or "")) if part
        )
        if not text:
            continue
        evidence.append((str(doi), text.lower()))
    return evidence


def _term_candidates(text: str) -> set[str]:
    """1-3 token word n-grams of ``text`` with stopword/length filtering."""
    tokens = _WORD_RE.findall(text)
    terms: set[str] = set()
    for size in range(1, min(3, len(tokens)) + 1):
        for start in range(len(tokens) - size + 1):
            gram = tokens[start : start + size]
            if not any(ch.isalpha() for ch in "".join(gram)):
                continue
            if any(t in _STOPWORDS or len(t) == 1 for t in gram):
                continue
            terms.add(" ".join(gram))
    return terms


def _micro_taxonomy(evidence: list[tuple[str, str]]) -> list[dict[str, Any]]:
    freq: dict[str, int] = defaultdict(int)
    anchors: dict[str, set[str]] = defaultdict(set)
    for doi, text in evidence:
        for term in _term_candidates(text):
            freq[term] += 1
            anchors[term].add(doi)
    entries = [
        {"term": term, "freq": freq[term], "anchor_dois": sorted(anchors[term])}
        for term in freq
    ]
    entries.sort(key=lambda entry: (-entry["freq"], entry["term"]))
    return entries


def _tokenize(text: str) -> set[str]:
    """Lowercased tokens of ``text`` with stopwords dropped and length >= 2."""
    return {
        t
        for t in _WORD_RE.findall(text.casefold())
        if t not in _STOPWORDS and len(t) >= 2
    }


def _echo_index(
    query_text: str, top_terms: list[dict[str, Any]], k: int = 10
) -> float:
    """Query Echo Index (13_evaluation.md section 3.1).

    The fraction of the top-``k`` taxonomy terms (by emitted order, i.e.
    ``-freq, term``) whose tokens overlap the seeded query's tokens.  ``0.0``
    when there are no terms or ``k == 0``; otherwise
    ``round(overlap / min(len(terms), k), 4)``.  A high value means the
    distiller is echoing the user's prompt instead of revealing field
    vocabulary -- evaluation Dimension 2 gates ``<= 0.3``.
    """
    top = [e for e in (top_terms or []) if isinstance(e, dict) and e.get("term")][:k]
    query_tokens = _tokenize(query_text)
    if not top or not query_tokens:
        return 0.0
    echo = sum(
        1
        for entry in top
        if query_tokens & _tokenize(str(entry.get("term") or ""))
    )
    return round(echo / len(top), 4)


def _keyword_counts(
    evidence: list[tuple[str, str]],
    table: list[tuple[str, re.Pattern[str]]],
) -> dict[str, int]:
    """Per-doc counts for each keyword label; observed-in-pool docs only."""
    counts: dict[str, int] = {}
    for _doi, text in evidence:
        for label, pattern in table:
            if pattern.search(text):
                counts[label] = counts.get(label, 0) + 1
    return {label: counts[label] for label in sorted(counts)}


def _schools(
    evidence: list[tuple[str, str]],
    schools_table: list[tuple[str, re.Pattern[str]]] | None = None,
) -> list[dict[str, Any]]:
    """Group evidence docs into keyword-heuristic schools.

    School labels are DOI-anchored keyword heuristics that can false-positive
    (e.g. "drone" matching bee drones, "transformer" matching power-grid
    transformers); this is acceptable for a directional taxonomy.
    """
    groups: list[dict[str, Any]] = []
    for label, pattern in schools_table or _table(DEFAULT_LEXICON.schools):
        matches = [(doi, text) for doi, text in evidence if pattern.search(text)]
        if not matches:
            continue
        groups.append(
            {
                "label": label,
                "n": len(matches),
                "anchor_dois": sorted({doi for doi, _ in matches}),
            }
        )
    groups.sort(key=lambda group: (-group["n"], group["label"]))
    return groups


def _topic_layer(pool: dict[str, Any]) -> list[dict[str, Any]]:
    """Aggregate optional per-doc OpenAlex ``topics`` into an anchored layer (M0.6).

    Anchor discipline matches the rest of the distiller: only docs carrying a
    DOI contribute.  For each doc + label (a topic's ``display_name``) the
    highest entry score wins (missing/``None`` scores are ignored); the
    pool-level ``score`` is the mean of those per-doc max scores rounded to 4
    decimals, or ``None`` when no scored doc contributes.  ``n`` counts
    distinct anchored DOIs.  Entries sort by ``(-n, label)``; a label whose
    ``display_name`` is empty/``None`` is skipped entirely.
    """
    docs = pool.get("docs", [])
    if not isinstance(docs, list):
        return []
    label_dois: dict[str, set[str]] = defaultdict(set)
    label_maxes: dict[str, list[float]] = defaultdict(list)
    for doc in docs:
        if not isinstance(doc, dict):
            continue
        doi = doc.get("doi")
        if not doi:
            continue
        topics = doc.get("topics")
        if not isinstance(topics, list) or not topics:
            continue
        doc_max: dict[str, float] = {}
        labels: set[str] = set()
        for entry in topics:
            if not isinstance(entry, dict):
                continue
            label = entry.get("display_name")
            if not label:
                continue
            label = str(label)
            labels.add(label)
            score = entry.get("score")
            if isinstance(score, (int, float)) and not isinstance(score, bool):
                doc_max[label] = max(doc_max.get(label, 0.0), float(score))
        for label in labels:
            label_dois[label].add(str(doi))
            if label in doc_max:
                label_maxes[label].append(doc_max[label])
    entries = []
    for label, dois in label_dois.items():
        scores = label_maxes.get(label) or []
        entries.append(
            {
                "label": label,
                "n": len(dois),
                "score": round(sum(scores) / len(scores), 4) if scores else None,
                "anchor_dois": sorted(dois),
            }
        )
    entries.sort(key=lambda entry: (-entry["n"], entry["label"]))
    return entries


def distill_pool(
    pool: dict[str, Any],
    lexicon: DomainLexicon | None = None,
    query_text: str | None = None,
) -> dict[str, Any]:
    """Return the terms-file payload for a pool (spec section 6).

    ``lexicon`` is the per-field pattern configuration (see
    :class:`~scholar_harness.recon.lexicon.DomainLexicon`); when omitted (or
    ``None``) the default cross-domain lexicon is used (CV/LLM core plus
    curated climate/health/finance/education/materials patterns, P6).  Any
    research domain registers its own metric/dataset/school patterns and
    passes its lexicon in.  ``micro_taxonomy`` is extracted with
    pure term frequency and is field-agnostic: it never consults the lexicon.

    ``query_text`` (M0.7) seeds the Query Echo Index (``qei`` at
    ``13_evaluation.md`` section 3.1): the fraction of the top-10 taxonomy
    terms echoing the probe query.  When omitted (``None``) the ``qei`` key is
    absent and output stays byte-identical to pre-M0.7.
    """
    if lexicon is None:
        lexicon = DEFAULT_LEXICON
    evidence = _evidence_docs(pool)
    micro_taxonomy = _micro_taxonomy(evidence)
    payload = {
        "cache_key": str(pool.get("cache_key") or ""),
        "micro_taxonomy": micro_taxonomy,
        "metrics": _keyword_counts(evidence, _table(lexicon.metrics)),
        "datasets": _keyword_counts(evidence, _table(lexicon.datasets)),
        "schools": _schools(evidence, _table(lexicon.schools)),
        "topics": _topic_layer(pool),
    }
    if query_text is not None:
        payload["qei"] = _echo_index(query_text, micro_taxonomy)
    return payload


def _assert_safe_output(path: Path) -> None:
    resolved = Path(path).resolve()
    if any(part.lower() == "workspaces" for part in resolved.parts):
        raise RuntimeError(f"refusing to write under workspaces/: {resolved}")


def distill(pool_path: Path | str, out_path: Path | str) -> Path:
    """Distill a pool JSON file into a terms JSON file; return ``out_path``."""
    out_file = Path(out_path).resolve()
    _assert_safe_output(out_file)
    payload = json.loads(Path(pool_path).read_text(encoding="utf-8"))
    distilled = distill_pool(payload)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    tmp = out_file.with_suffix(out_file.suffix + ".tmp")
    tmp.write_text(
        json.dumps(distilled, indent=2, ensure_ascii=False, sort_keys=True),
        encoding="utf-8",
    )
    os.replace(tmp, out_file)
    return out_file