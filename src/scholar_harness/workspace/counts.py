"""Physical corpus counting and declared-vs-actual reconciliation (T-TRUTH-COUNTS-01).

Why this module exists
----------------------
A harness that reports "0 discovered papers" while thousands of records
physically exist in the workspace is lying. The live counterexample is
``workspaces/uav-pilot-demo``: ``project.json`` declares
``discovered_papers: 0`` while ``calibration/`` physically holds 2165
harvested records (``raw_union.json``) and 2060 deduplicated records
(``deduped.json``). The old counting code only ever looked at five
canonical paths under ``literature/``, so every corpus stored anywhere else
was invisible -- and the mismatch was reported as a soft ``WARN``.

The exact rules (no over-claims)
--------------------------------
This module is deliberately explicit about what it does, because the defect
it closes was a *silent* one. Read this list as the contract:

1. **Artifacts are discovered by content, not by name.** Every ``*.json``,
   ``*.jsonl`` and ``*.ndjson`` file under the workspace is inspected (see
   the documented exclusions below). A file whose name the harness has never
   seen is still read; if it physically carries a record list, its records
   are counted.

2. **Every inspected artifact gets exactly one named state:**

   * ``COUNTED`` -- a physical record list was found and counted (a
     top-level array, or an array under a well-known record-list key, at any
     depth reachable *through* those keys);
   * ``SUMMARY_ONLY`` -- the artifact carries **no** record list but does
     carry an explicit count field (``count`` / ``union_count`` /
     ``cluster_count`` / ``total_records`` / ``total``). The number is then a
     *declared summary*, not physical truth, and the artifact is labelled as
     such;
   * ``CONFLICT`` -- the artifact carries **both** a record list and a count
     field that disagree. The physical list is the truth and is used for the
     counter, but the disagreement is surfaced (never silently dropped).
     A conflict artifact still **physically carries records**: it is part of
     the corpus and contributes its physical count (a conflict never turns a
     corpus into "no corpus"). When the record list is *empty* while the
     artifact declares a positive count, the physical count is
     **undetermined** (never a silent ``0``);
   * ``UNREADABLE`` -- the file could not be read or is not valid JSON. This
     is never collapsed into "no candidate" and never into ``0``;
   * ``UNKNOWN_SHAPE`` -- the file parsed, but it carries neither a record
     list nor a count field.

3. **Role assignment is token-assisted and tokenised.** A file *stem* is split
   into words; a role token matches only as a whole word (or a whole
   consecutive word phrase), never as a bare substring. Role-specific tokens
   (``deduped``/``deduplicated``, ``verified``, ``included``, ``excluded``)
   **outrank** the generic ones (``papers``, ``records``, ``corpus``,
   ``results``, ...), so ``deduped_papers.json`` maps to ``deduped_papers``
   and never to ``discovered_papers``. A stem that matches a known provider
   name is mapped to the *discovered* role as provider evidence. A
   record-bearing artifact with neither is **counted** and reported as an
   ``UNCLASSIFIED`` corpus contribution -- it is never dropped and never
   silently counted as ``0``.

4. **Selection is deterministic and content-based (never mtime-based).**
   For each role the counted artifact is chosen by, in order:

   (a) the canonical ``literature/<name>`` artifact, if present;
   (b) the strongest role token (role-specific tokens outrank generic
       ones; a longer token phrase outranks a shorter one);
   (c) physical records beat a summary (a ``COUNTED`` artifact outranks a
       ``SUMMARY_ONLY`` one with the same token strength);
   (d) the artifact with the most records;
   (e) the lexicographically smallest relative path.

   No timestamp/mtime enters the result: a count must be reproducible from
   the *content* of the workspace. Every candidate of a role stays visible in
   :attr:`CorpusCounts.sources` / :attr:`CorpusCounts.selected` so a human
   can judge the alternatives.

5. **Determinism.** The traversal is sorted and no timestamp enters the
   result, so two runs over an unchanged workspace produce identical counts
   and an identical status.

6. **Explicit status.** The physical counting reports ``OK``,
   ``UNCLASSIFIED``, ``UNRESOLVED``, ``UNIDENTIFIED``, ``SUMMARY`` or
   ``NO_CORPUS``; the reconciliation adds ``STALE``, ``CONFLICT`` and
   ``SUMMARY``. ``NO_CORPUS`` means exactly one thing: **this workspace
   contains no corpus artifact at all** -- a verifiable state that reconciles
   against a declared ``0``. A workspace that *does* contain corpus artifacts
   but none could be identified or parsed is ``UNIDENTIFIED`` (never
   reconciled, never a green verdict). A corpus that exists only as a
   *declared summary* (no physical record list) is ``SUMMARY``: it is never
   reported as a verified physical reconciliation. A corpus whose own summary
   disagrees with its own record list is ``CONFLICT``: the physical count is
   used, but the verdict is never a green "reconciled".

7. **Severity follows the impact (D-1).** An artifact that could not be
   read/understood and *does* map to a counted role makes that counter
   undetermined (``UNRESOLVED`` -> FAIL) -- unless the very same role is
   determined by an artifact that physically carries records (then the
   counter is determined and the unreadable artifact is only reported). An
   artifact that could not be read/understood and maps to *no* role is
   reported on its own line (``WARN``); it never turns the counted counters
   into "undetermined" and never poisons them.

Documented exclusions (and why)
-------------------------------
* ``audit/`` -- the append-only event ledger; its rows are events, not
  corpus records.
* ``chroma_db/``, ``rag/`` -- vector stores and heavy binary payloads.
* ``__pycache__/``, ``node_modules/`` and dot-paths (any path part starting
  with ``.``, the file name included) -- build/runtime scratch.
* ``project.json`` -- the manifest *declares* the counters that are being
  reconciled; counting it would be circular.
* Harness-owned **derived** artifacts, which are computed *from* the corpus
  and would otherwise be counted a second time. The list is an explicit set
  of named paths (never a prefix guess about an arbitrary directory name):

  - ``literature/synthesis_matrix.json`` (protocol matrix rows),
  - ``literature/verified_unresolved.json`` (verification quarantine),
  - ``literature/prisma_report.json`` (PRISMA counters),
  - ``literature/graph.json`` and ``literature/knowledge_graph.json``
    (citation graph nodes/edges),
  - ``literature/extraction/**`` (the merged extraction records, e.g.
    ``literature/extraction/merged/records.json``),
  - ``literature/verification/**`` (verification artifacts),
  - ``literature/screening/**`` (screening batches/decisions/manifest --
    they repeat corpus records under a decision context).

  The screening stage also writes its artifacts under its own canonical
  names wherever the screening lane lives (``batch_NNN.json``,
  ``batch_NNN_decisions*.json``, ``pack_NNN*.json``, ``*.view.json``); those
  names are excluded as well, because they are the same derived screening
  artifacts and they repeat the very same studies.

  Every other JSON/JSONL file in the workspace (including files under
  ``pdfs/`` and ``extracted/``) is inspected.

The module is import-side-effect free and reads only from disk; it never
writes to a workspace.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

__all__ = [
    "CANONICAL_CORPUS_FILES",
    "CORPUS_STAT_KEYS",
    "STATE_CONFLICT",
    "STATE_COUNTED",
    "STATE_SUMMARY_ONLY",
    "STATE_UNREADABLE",
    "STATE_UNKNOWN_SHAPE",
    "CorpusArtifact",
    "CorpusCounts",
    "Mismatch",
    "Reconciliation",
    "count_corpus",
    "extra_actual_stats",
    "read_declared_stats",
    "reconcile",
]


# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

#: Logical ``project.json.stats`` keys the harness derives from physical
#: corpus artifacts. The key names are part of the manifest schema and are
#: never renamed here.
CORPUS_STAT_KEYS: tuple[str, ...] = (
    "discovered_papers",
    "deduped_papers",
    "verified_papers",
    "included_papers",
    "excluded_papers",
)

#: Canonical artifact names per logical key, in priority order. These are the
#: ``literature/`` paths the harness has always counted; they keep priority
#: over any non-canonical candidate.
CANONICAL_CORPUS_FILES: dict[str, tuple[str, ...]] = {
    "discovered_papers": ("raw_search.json", "all_raw_search.json"),
    "deduped_papers": ("deduped.json",),
    "verified_papers": ("verified.json",),
    "included_papers": ("included.json",),
    "excluded_papers": ("excluded.json",),
}

#: Artifact states.
STATE_COUNTED = "COUNTED"
STATE_SUMMARY_ONLY = "SUMMARY_ONLY"
STATE_CONFLICT = "CONFLICT"
STATE_UNREADABLE = "UNREADABLE"
STATE_UNKNOWN_SHAPE = "UNKNOWN_SHAPE"


def bears_records(artifact: CorpusArtifact) -> bool:
    """True when the artifact PHYSICALLY carries a record list.

    ``COUNTED`` is a physical record list; ``CONFLICT`` is a physical record
    list whose own summary disagrees with it (the physical list is still the
    truth, so the artifact is part of the corpus). A conflict whose physical
    count is *undetermined* (an empty list next to a positive declared count)
    carries no countable record and is excluded.
    """
    return (
        artifact.state in (STATE_COUNTED, STATE_CONFLICT) and artifact.count is not None
    )


#: Filename tokens that identify a role, in *strength* order (earlier token =
#: stronger evidence). The role-specific tokens come FIRST: they outrank the
#: generic ones, so ``deduped_papers.json`` can never be misrouted to
#: ``discovered_papers``.
_ROLE_TOKEN_RANKS: tuple[tuple[str, str], ...] = (
    # -- role specific (outrank every generic token) ----------------------
    ("deduped", "deduped_papers"),
    ("deduplicated", "deduped_papers"),
    ("verified", "verified_papers"),
    ("included", "included_papers"),
    ("excluded", "excluded_papers"),
    # -- generic ----------------------------------------------------------
    ("all_raw_search", "discovered_papers"),
    ("raw_search", "discovered_papers"),
    ("raw_union", "discovered_papers"),
    ("union", "discovered_papers"),
    ("corpus", "discovered_papers"),
    ("all_records", "discovered_papers"),
    ("records", "discovered_papers"),
    ("record", "discovered_papers"),
    ("papers", "discovered_papers"),
    ("results", "discovered_papers"),
    ("hits", "discovered_papers"),
)

#: Tokens that mark a file as *not* being the corpus of that role.
_NEGATIVE_TOKENS = (
    "not_included",
    "not_excluded",
    "non_included",
    "non_excluded",
    "unincluded",
    "none_included",
    "no_included",
    "unverified",
)

#: Provider names. A file whose stem contains one of them is *provider
#: evidence* for the discovered role. Provider evidence is weaker than a
#: role token: it is only used when no role-token artifact exists.
_PROVIDER_TOKENS: tuple[str, ...] = (
    "openalex",
    "crossref",
    "arxiv",
    "pubmed",
    "semanticscholar",
    "semantic_scholar",
    "biorxiv",
    "europepmc",
    "scopus",
    "springer",
    "elsevier",
    "ieee",
    "unpaywall",
    "doaj",
    "dimensions",
    "wos",
)

#: Directories that never hold a corpus artifact.
_SKIP_DIR_NAMES = frozenset(
    {"audit", "chroma_db", "rag", "__pycache__", "node_modules"}
)

#: Harness-owned derived artifacts (computed *from* the corpus), named one by
#: one so the exclusion stays auditable.
_DERIVED_ARTIFACT_PATHS = frozenset(
    {
        "literature/synthesis_matrix.json",
        "literature/verified_unresolved.json",
        "literature/prisma_report.json",
        "literature/graph.json",
        "literature/knowledge_graph.json",
    }
)

#: Harness-owned derived artifact *trees*, named one by one (never a guess
#: about an arbitrary directory prefix such as ``screening*``).
_DERIVED_ARTIFACT_TREES = (
    "literature/extraction/",
    "literature/verification/",
    "literature/screening/",
)

#: The screening stage's own artifact names (``batch_NNN.json``,
#: ``batch_NNN_decisions*.json``, ``pack_NNN*.json``, ``*.view.json``). They
#: are derived screening artifacts -- corpus records repeated under a
#: decision context -- and are excluded wherever the screening lane lives.
_HARNESS_SCREENING_ARTIFACT_RE = re.compile(
    r"^(?:batch|pack)_\d+(?:[._].*)?\.json$" r"|^.*\.view\d*\.json$"
)

#: The manifest itself: it declares the counters, it is not evidence.
_DECLARATION_PATHS = frozenset({"project.json"})

#: File suffixes that carry a corpus payload.
_JSON_SUFFIXES = (".json",)
#: Line oriented corpus suffixes (one JSON object per line = one record).
_LINE_SUFFIXES = (".jsonl", ".ndjson")

#: Keys inspected inside a JSON payload to find the record list. The search
#: descends *only* through these keys (bounded depth), so a nested corpus
#: such as ``{"data": {"documents": [...]}}`` is found while an unrelated
#: nested list (e.g. ``research_questions``) is not mistaken for a corpus.
_RECORD_LIST_KEYS = (
    "documents",
    "records",
    "items",
    "results",
    "data",
    "papers",
    "hits",
    "entries",
)

#: Maximum nesting depth of the record-list search.
_MAX_NESTING_DEPTH = 3

#: Keys inspected inside a JSON payload when no record list is present.
_COUNT_FIELD_KEYS = ("count", "union_count", "cluster_count", "total_records", "total")

#: Word splitter used for the tokenised (never substring) name matching.
_WORD_RE = re.compile(r"[a-z0-9]+")


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CorpusArtifact:
    """One physical artifact inspected by the counter.

    ``state`` is one of the ``STATE_*`` constants and ``count`` is ``None``
    whenever the artifact could not be counted (``UNREADABLE`` /
    ``UNKNOWN_SHAPE`` / an empty-list-vs-summary conflict) -- it is never
    silently ``0``.
    """

    relpath: str
    state: str
    count: int | None
    role: str | None
    role_basis: str
    canonical: bool = False
    canonical_priority: int | None = None
    token_rank: int | None = None
    provider: str | None = None
    detail: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.relpath,
            "state": self.state,
            "count": self.count,
            "role": self.role,
            "role_basis": self.role_basis,
            "canonical": self.canonical,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class CorpusCounts:
    """The physical corpus counts of one workspace."""

    stats: dict[str, int]
    #: role -> every candidate path for that role (machine readable: one path
    #: per list entry, never a comma-joined string).
    sources: dict[str, list[str]]
    #: role -> the path(s) whose count produced ``stats[role]``.
    selected: dict[str, list[str]]
    candidates: tuple[CorpusArtifact, ...]
    status: str
    #: role -> paths that could not be counted (unreadable / unexpected shape).
    undetermined: dict[str, list[str]] = field(default_factory=dict)
    #: providers whose evidence was summed into a counter (see
    #: :attr:`provider_overlap`).
    provider_evidence: tuple[str, ...] = ()

    # -- derived views ----------------------------------------------------

    @property
    def counted(self) -> tuple[CorpusArtifact, ...]:
        """The artifacts that PHYSICALLY carry a record list.

        A ``CONFLICT`` artifact (its own summary disagrees with its own
        record list) still carries records: the physical list is the truth,
        so the artifact is part of the corpus and contributes its physical
        count. Only a conflict whose physical count is *undetermined* (an
        empty list next to a positive declared count) is excluded -- it
        carries no countable record.
        """
        return tuple(a for a in self.candidates if bears_records(a))

    @property
    def corpus_present(self) -> bool:
        """True when at least one artifact physically carries records."""
        return bool(self.counted)

    @property
    def unclassified(self) -> tuple[CorpusArtifact, ...]:
        """Record-bearing artifacts with no known role (never dropped)."""
        return tuple(a for a in self.candidates if bears_records(a) and a.role is None)

    @property
    def unreadable(self) -> tuple[CorpusArtifact, ...]:
        """Artifacts that could not be read/parsed at all."""
        return tuple(a for a in self.candidates if a.state == STATE_UNREADABLE)

    @property
    def uninterpretable(self) -> tuple[CorpusArtifact, ...]:
        """Artifacts that could not be read *or* understood.

        An ``UNKNOWN_SHAPE`` artifact was parsed successfully -- it simply is
        not a corpus -- so it is only reported when it maps to a role.
        """
        return tuple(
            a
            for a in self.candidates
            if a.state in (STATE_UNREADABLE, STATE_UNKNOWN_SHAPE)
        )

    @property
    def conflicts(self) -> tuple[CorpusArtifact, ...]:
        """Artifacts whose own summary disagrees with their own record list."""
        return tuple(a for a in self.candidates if a.state == STATE_CONFLICT)

    @property
    def unresolved(self) -> tuple[CorpusArtifact, ...]:
        """Artifacts that block the reconciliation.

        An artifact that could not be read/understood and maps to a counted
        role makes that counter undetermined (never a silent ``0``). An
        artifact that maps to *no* role does not block anything: it is
        reported on its own line (see :attr:`unreadable`).
        """
        blocked: set[str] = set()
        for paths in self.undetermined.values():
            blocked.update(paths)
        return tuple(a for a in self.candidates if a.relpath in blocked)

    @property
    def provider_overlap(self) -> bool:
        """True when a counter was summed from more than one provider.

        Provider harvests overlap (the same document can be returned by two
        providers), so a summed provider counter may over-count the physical
        corpus. This is a **stated limitation**, surfaced by the doctor.
        """
        return len(self.provider_evidence) > 1

    @property
    def headline(self) -> int:
        """The number of harvested (discovered) corpus records."""
        return int(self.stats.get("discovered_papers", 0))

    def summary(self) -> str:
        """One deterministic, human-readable summary line."""
        parts: list[str] = []
        for key in CORPUS_STAT_KEYS:
            selected = self.selected.get(key) or []
            if not selected:
                continue
            parts.append(f"{key}={self.stats.get(key, 0)} ({', '.join(selected)})")
        text = ", ".join(parts) if parts else "0 corpus records counted"
        extras: list[str] = []
        unclassified = self.unclassified
        if unclassified:
            records = sum(a.count or 0 for a in unclassified)
            extras.append(
                f"{len(unclassified)} unclassified record-bearing artifact(s) "
                f"({records} records)"
            )
        conflicts = self.conflicts
        if conflicts:
            extras.append(f"{len(conflicts)} summary-vs-list conflict(s)")
        unreadable = self.unreadable
        if unreadable:
            extras.append(f"{len(unreadable)} unreadable artifact(s)")
        odd = sum(1 for a in self.uninterpretable if a.state == STATE_UNKNOWN_SHAPE)
        if odd:
            extras.append(f"{odd} artifact(s) with an unexpected shape")
        if extras:
            text = f"{text}; " + "; ".join(extras)
        if self.undetermined:
            roles = ", ".join(sorted(self.undetermined))
            return f"corpus count UNDETERMINED for {roles} — {text}"
        if not self.counted:
            # No physical record list at all. Say WHICH kind of evidence was
            # seen: a declared summary is not a corpus, and a conflict whose
            # physical count is undetermined is not a corpus either -- but
            # neither is "no corpus artifact at all".
            summaries = [a for a in self.candidates if a.state == STATE_SUMMARY_ONLY]
            if summaries:
                return (
                    "no physical record list (declared summary only: "
                    + ", ".join(a.relpath for a in summaries)
                    + f") — {text}"
                )
            conflict_artifacts = [
                a for a in self.candidates if a.state == STATE_CONFLICT
            ]
            if conflict_artifacts:
                return (
                    "no physical record list (conflicting summary, physical count "
                    "undetermined: "
                    + ", ".join(a.relpath for a in conflict_artifacts)
                    + f") — {text}"
                )
            return f"no corpus artifact identified ({text})"
        return text


@dataclass(frozen=True)
class Mismatch:
    """One declared-vs-actual disagreement."""

    key: str
    declared: int
    actual: int

    def as_dict(self) -> dict[str, Any]:
        return {"key": self.key, "declared": self.declared, "actual": self.actual}


@dataclass(frozen=True)
class Reconciliation:
    """Declared (``project.json``) vs actual (physical) corpus accounting."""

    workspace: Path
    declared: dict[str, int]
    actual: dict[str, int]
    mismatches: tuple[Mismatch, ...]
    status: str
    counts: CorpusCounts

    @property
    def consistent(self) -> bool:
        return not self.mismatches

    @property
    def reconciled(self) -> bool:
        """True only when the declared counters were actually verified.

        ``NO_CORPUS`` counts as reconciled: the workspace provably holds no
        corpus artifact at all, so a declared ``0`` is verified against the
        physical state (D-2). ``CONFLICT`` and ``SUMMARY`` never count as
        reconciled: a self-contradicting corpus and a declared summary are
        not verified physical counts.
        """
        return self.status in ("OK", "NO_CORPUS")

    def as_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "declared": dict(self.declared),
            "actual": dict(self.actual),
            "mismatches": [m.as_dict() for m in self.mismatches],
            "corpus_present": self.counts.corpus_present,
            "sources": {k: list(v) for k, v in self.counts.sources.items()},
            "selected": {k: list(v) for k, v in self.counts.selected.items()},
            "unclassified": [a.as_dict() for a in self.counts.unclassified],
            "unreadable": [a.as_dict() for a in self.counts.unreadable],
            "conflicts": [a.as_dict() for a in self.counts.conflicts],
            "undetermined": {k: list(v) for k, v in self.counts.undetermined.items()},
            "provider_evidence": list(self.counts.provider_evidence),
        }


# ---------------------------------------------------------------------------
# Payload reading
# ---------------------------------------------------------------------------


def _words(text: str) -> list[str]:
    """Split a name into lowercase words (tokenised matching, no substrings)."""
    return _WORD_RE.findall(text.lower())


def _phrase_matches(phrase: list[str], words: list[str]) -> bool:
    """True when ``phrase`` occurs as a consecutive word sequence in ``words``."""
    size = len(phrase)
    if size == 0 or size > len(words):
        return False
    return any(words[i : i + size] == phrase for i in range(len(words) - size + 1))


def _find_record_list(
    payload: Any, depth: int = 0
) -> tuple[dict[str, Any] | None, str, list[Any] | None]:
    """Locate the physical record list of a payload.

    Returns ``(container, key, records)``. The search starts at the payload
    itself and descends **only through the well-known record-list keys**
    (bounded by :data:`_MAX_NESTING_DEPTH`), so a nested corpus such as
    ``{"data": {"documents": [...]}}`` is found while an unrelated nested
    list (e.g. ``research_questions``) is never mistaken for a corpus.
    """
    if isinstance(payload, list):
        return None, "", payload
    if not isinstance(payload, dict) or depth >= _MAX_NESTING_DEPTH:
        return None, "", None
    for key in _RECORD_LIST_KEYS:
        value = payload.get(key)
        if isinstance(value, list):
            return payload, key, value
    for key in _RECORD_LIST_KEYS:
        value = payload.get(key)
        if isinstance(value, dict):
            container, found_key, records = _find_record_list(value, depth + 1)
            if records is not None:
                return container, found_key, records
    return None, "", None


def _find_count_field(
    payload: Any, container: dict[str, Any] | None
) -> tuple[str | None, int | None]:
    """Return ``(key, value)`` of the artifact's own declared count."""
    for source in (container, payload):
        if not isinstance(source, dict):
            continue
        for key in _COUNT_FIELD_KEYS:
            value = source.get(key)
            if isinstance(value, bool):
                continue
            if isinstance(value, int):
                return key, value
    return None, None


def _classify_payload(payload: Any) -> tuple[str, int | None, str]:
    """Return ``(state, count, detail)`` for one parsed JSON payload.

    A record list is a top-level array or an array under a well-known
    record-list key (at any depth reachable through those keys). When the
    artifact also carries its own count field and the two disagree, the
    disagreement is surfaced as ``CONFLICT`` -- and an *empty* record list
    next to a positive declared count leaves the physical count
    **undetermined** (never a silent ``0``).
    """
    container, key, records = _find_record_list(payload)
    count_key, declared = _find_count_field(payload, container)

    if records is not None:
        size = len(records)
        if declared is not None and declared != size:
            if size == 0:
                return (
                    STATE_CONFLICT,
                    None,
                    f"CONFLICT: the record list '{key or '<root>'}' is empty but the "
                    f"artifact declares {count_key}={declared} — the physical count "
                    f"is undetermined (never a silent 0)",
                )
            return (
                STATE_CONFLICT,
                size,
                f"CONFLICT: the artifact declares {count_key}={declared} but carries "
                f"{size} record(s) — the physical count is used",
            )
        if key:
            return (
                STATE_COUNTED,
                size,
                f"record list under '{key}' with {size} record(s)",
            )
        return STATE_COUNTED, size, f"top-level record list with {size} record(s)"

    if declared is not None:
        return (
            STATE_SUMMARY_ONLY,
            declared,
            f"summary field '{count_key}'={declared} (no physical record list)",
        )
    return (
        STATE_UNKNOWN_SHAPE,
        None,
        "no record list and no count field (unexpected shape)",
    )


def _read_line_oriented(path: Path) -> tuple[str, int | None, str]:
    """Read a ``.jsonl``/``.ndjson`` corpus: one JSON object per line."""
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        return STATE_UNREADABLE, None, f"could not be read: {exc}"
    records = 0
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        try:
            json.loads(line)
        except ValueError as exc:
            return (
                STATE_UNREADABLE,
                None,
                f"line {lineno} is not valid JSON: {exc}",
            )
        records += 1
    return (
        STATE_COUNTED,
        records,
        f"{records} NDJSON record(s) (one JSON object per line)",
    )


def _read_artifact(path: Path) -> tuple[str, int | None, str]:
    """Read one artifact and return ``(state, count, detail)``.

    A parse/read error is NEVER collapsed into "no candidate" and never into
    ``0``: it is reported as ``UNREADABLE`` with ``count=None``.
    """
    if path.suffix.lower() in _LINE_SUFFIXES:
        return _read_line_oriented(path)
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        return STATE_UNREADABLE, None, f"could not be read: {exc}"
    try:
        payload = json.loads(text)
    except ValueError as exc:
        return STATE_UNREADABLE, None, f"is not valid JSON: {exc}"
    return _classify_payload(payload)


# ---------------------------------------------------------------------------
# Role assignment
# ---------------------------------------------------------------------------


def _role_for_stem(stem: str) -> tuple[str | None, str, int | None, str | None]:
    """Return ``(role, basis, token_rank, provider)`` for a file stem.

    Matching is **tokenised**: a token matches only as a whole word (or a
    whole consecutive word phrase), never as a bare substring. Role-specific
    tokens (``deduped``, ``verified``, ``included``, ``excluded``) outrank
    the generic ones.

    ``basis`` is one of ``token:<token>``, ``provider:<provider>``,
    ``negative-token`` or ``unclassified``.
    """
    words = _words(stem)
    for token in _NEGATIVE_TOKENS:
        if _phrase_matches(_words(token), words):
            return None, "negative-token", None, None

    best: tuple[tuple[int, int, int], str, str, int] | None = None
    for rank, (token, role) in enumerate(_ROLE_TOKEN_RANKS):
        phrase = _words(token)
        if not _phrase_matches(phrase, words):
            continue
        # Role-specific tokens outrank the generic ones; a longer token
        # phrase outranks a shorter one; the rank order is the final tie.
        specific = 1 if role != "discovered_papers" else 0
        key = (specific, len(phrase), -rank)
        if best is None or key > best[0]:
            best = (key, token, role, rank)
    if best is not None:
        _key, token, role, rank = best
        return role, f"token:{token}", rank, None

    for provider in _PROVIDER_TOKENS:
        if _phrase_matches(_words(provider), words):
            return "discovered_papers", f"provider:{provider}", None, provider
    return None, "unclassified", None, None


def _canonical_match(key: str, relpath: str) -> int | None:
    """Return the canonical priority of a relative path (``None`` if not canonical)."""
    for index, name in enumerate(CANONICAL_CORPUS_FILES.get(key, ())):
        if relpath == f"literature/{name}":
            return index
    return None


def _is_excluded(relpath: str) -> bool:
    """True for the documented exclusions (see the module docstring)."""
    if relpath in _DERIVED_ARTIFACT_PATHS or relpath in _DECLARATION_PATHS:
        return True
    if relpath.startswith(_DERIVED_ARTIFACT_TREES):
        return True
    return bool(_HARNESS_SCREENING_ARTIFACT_RE.match(relpath.rsplit("/", 1)[-1]))


def _iter_artifact_paths(workspace: Path) -> list[tuple[Path, str]]:
    """Return ``(path, relative posix path)`` for every inspected artifact.

    The traversal is sorted, so the result is identical on every run. The
    dot-path exclusion is symmetric: every part of the relative path is
    checked, the file name included.
    """
    found: list[tuple[Path, str]] = []
    if not workspace.is_dir():
        return found
    seen: set[str] = set()
    for pattern in ("*.json", "*.jsonl", "*.ndjson"):
        for path in sorted(workspace.rglob(pattern)):
            if not path.is_file():
                continue
            rel = path.relative_to(workspace)
            parts = rel.parts
            # Symmetric dot exclusion: any part (the file name included).
            if any(part.startswith(".") for part in parts):
                continue
            if any(part in _SKIP_DIR_NAMES for part in parts[:-1]):
                continue
            relpath = rel.as_posix()
            if relpath in seen:
                continue
            if _is_excluded(relpath):
                continue
            seen.add(relpath)
            found.append((path, relpath))
    return found


# ---------------------------------------------------------------------------
# Counting
# ---------------------------------------------------------------------------


def _state_rank(artifact: CorpusArtifact) -> int:
    """Preference of an artifact's state: physical records beat a summary."""
    if artifact.state in (STATE_COUNTED, STATE_CONFLICT):
        return 0
    if artifact.state == STATE_SUMMARY_ONLY:
        return 1
    return 2


def _selection_key(artifact: CorpusArtifact) -> tuple[int, int, int, int, str]:
    """The documented, deterministic selection key (never mtime, never "size wins").

    Order: canonical ``literature/`` artifacts first, then the strongest
    role token, then physical records over a summary, then the most records,
    and finally the lexicographically smallest path so the result never
    depends on directory iteration order.
    """
    canonical_priority = (
        artifact.canonical_priority if artifact.canonical_priority is not None else 99
    )
    token_rank = artifact.token_rank if artifact.token_rank is not None else 99
    return (
        canonical_priority,
        token_rank,
        _state_rank(artifact),
        -(artifact.count or 0),
        artifact.relpath,
    )


def _select_for_role(
    role: str, candidates: list[CorpusArtifact]
) -> list[CorpusArtifact]:
    """Return the artifacts whose counts make up the role's counter.

    * Role-token evidence wins over provider evidence.
    * Within a tier the canonical ``literature/`` artifacts win, then the
      strongest role token, then physical records over a summary, then the
      most records, then the smallest path.
    * Provider evidence is aggregated per provider (the best artifact per
      provider -- alternative snapshots of the same provider output are not
      summed, to avoid double counting) and the per-provider totals are
      summed. Provider harvests may overlap: the summed counter is a
      **stated limitation** (see :attr:`CorpusCounts.provider_overlap`).
    """
    token_candidates = [c for c in candidates if c.role_basis.startswith("token:")]
    if token_candidates:
        return [min(token_candidates, key=_selection_key)]

    provider_candidates = [c for c in candidates if c.provider is not None]
    if not provider_candidates:
        return []

    by_provider: dict[str, list[CorpusArtifact]] = {}
    for candidate in provider_candidates:
        by_provider.setdefault(candidate.provider or "", []).append(candidate)
    chosen: list[CorpusArtifact] = []
    for provider in sorted(by_provider):
        group = by_provider[provider]
        chosen.append(min(group, key=_selection_key))
    return chosen


def count_corpus(workspace: Path | str) -> CorpusCounts:
    """Count the physical corpus artifacts of a workspace.

    Recognition is content-based: an artifact that physically carries a
    record list is counted even when its name is unknown to the harness.
    Role assignment is token-assisted and best-effort; a record-bearing
    artifact with no known role is reported as an unclassified contribution
    instead of being dropped.
    """
    ws = Path(workspace)
    artifacts: list[CorpusArtifact] = []

    for path, relpath in _iter_artifact_paths(ws):
        state, count, detail = _read_artifact(path)
        role, basis, rank, provider = _role_for_stem(path.stem)
        canonical_priority = (
            _canonical_match(role, relpath) if role is not None else None
        )
        artifacts.append(
            CorpusArtifact(
                relpath=relpath,
                state=state,
                count=count,
                role=role,
                role_basis=basis,
                canonical=canonical_priority is not None,
                canonical_priority=canonical_priority,
                token_rank=rank,
                provider=provider,
                detail=detail,
            )
        )

    by_role: dict[str, list[CorpusArtifact]] = {key: [] for key in CORPUS_STAT_KEYS}
    for artifact in artifacts:
        if artifact.role is not None:
            by_role.setdefault(artifact.role, []).append(artifact)

    stats: dict[str, int] = {}
    sources: dict[str, list[str]] = {}
    selected: dict[str, list[str]] = {}
    undetermined: dict[str, list[str]] = {}
    provider_evidence: list[str] = []

    for key in CORPUS_STAT_KEYS:
        candidates = by_role.get(key, [])
        sources[key] = sorted(c.relpath for c in candidates)
        chosen = _select_for_role(key, candidates)
        for artifact in chosen:
            if artifact.provider and artifact.provider not in provider_evidence:
                provider_evidence.append(artifact.provider)
        if not chosen:
            stats[key] = 0
            selected[key] = []
            continue
        counts = [c.count for c in chosen if c.count is not None]
        if len(counts) != len(chosen):
            # The selected artifact(s) could not be counted: the role is
            # UNDETERMINED, never a silent 0.
            undetermined[key] = sorted(c.relpath for c in chosen)
            stats[key] = 0
            selected[key] = sorted(c.relpath for c in chosen)
            continue
        stats[key] = sum(counts)
        selected[key] = sorted(c.relpath for c in chosen)

    # Severity follows the impact (D-1): an artifact that could not be
    # read/understood and DOES map to a counted role makes that counter
    # undetermined -- unless the very same role is determined by an artifact
    # that physically carries records (then the counter is determined and the
    # unreadable artifact is only reported). An artifact that maps to NO role
    # is only reported.
    for key, candidates in by_role.items():
        if any(candidate.count is not None for candidate in candidates):
            # The role's counter is determined by a physical artifact.
            continue
        if not candidates:
            continue
        undetermined[key] = sorted(candidate.relpath for candidate in candidates)

    status = _counts_status(artifacts, undetermined)
    return CorpusCounts(
        stats=stats,
        sources=sources,
        selected=selected,
        candidates=tuple(sorted(artifacts, key=lambda a: a.relpath)),
        status=status,
        undetermined=undetermined,
        provider_evidence=tuple(sorted(provider_evidence)),
    )


def _counts_status(
    artifacts: list[CorpusArtifact], undetermined: dict[str, list[str]]
) -> str:
    """The status of the physical counting itself.

    * ``UNRESOLVED`` -- a counted role could not be determined (an artifact
      that could not be read/understood maps to that role). No reconciliation
      may be claimed.
    * ``UNCLASSIFIED`` -- a record-bearing artifact carries no known role,
      so the declared counters cannot represent the physical corpus.
    * ``OK`` -- records were physically counted.
    * ``SUMMARY`` -- corpus evidence exists, but only as a declared summary
      (no physical record list).
    * ``UNIDENTIFIED`` -- an artifact could not be read/parsed at all and no
      corpus could be identified: **not reconciled**. (An artifact that
      parsed but has an unexpected shape was *understood* -- it simply is not
      a corpus -- so it never triggers this state.)
    * ``NO_CORPUS`` -- the workspace holds no corpus artifact at all. This is
      a verifiable state: it reconciles against a declared ``0``.
    """
    if undetermined:
        return "UNRESOLVED"
    if any(bears_records(a) and a.role is None for a in artifacts):
        return "UNCLASSIFIED"
    if any(a.state == STATE_COUNTED for a in artifacts):
        return "OK"
    if any(a.state == STATE_CONFLICT and a.count is not None for a in artifacts):
        # A summary/list conflict with a physical record list: the records are
        # the truth, the disagreement is surfaced separately.
        return "OK"
    if any(a.state in (STATE_SUMMARY_ONLY, STATE_CONFLICT) for a in artifacts):
        return "SUMMARY"
    if any(a.state == STATE_UNREADABLE for a in artifacts):
        # Something is there, but nothing could be read as a corpus.
        return "UNIDENTIFIED"
    return "NO_CORPUS"


# ---------------------------------------------------------------------------
# Declared state and reconciliation
# ---------------------------------------------------------------------------


def read_declared_stats(workspace: Path | str) -> dict[str, int]:
    """Read the declared ``project.json.stats`` counters of a workspace.

    Unreadable/missing/non-object manifests yield an empty mapping; the
    reconciliation then reports every physically counted key as a mismatch
    instead of crashing.
    """
    ws = Path(workspace)
    manifest_path = ws / "project.json"
    if not manifest_path.is_file():
        return {}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return {}
    if not isinstance(manifest, dict):
        return {}
    stats = manifest.get("stats")
    if not isinstance(stats, dict):
        return {}
    declared: dict[str, int] = {}
    for key, value in stats.items():
        if isinstance(value, bool):
            continue
        if isinstance(value, int):
            declared[key] = value
        elif isinstance(value, float):
            declared[key] = int(value)
    return declared


def extra_actual_stats(workspace: Path | str) -> dict[str, int]:
    """Counters the harness derives outside the corpus: PDFs and extractions.

    Both counters are ALWAYS emitted -- ``0`` when the directory is absent --
    so a declared ``downloaded_pdfs: 5`` in a workspace without a ``pdfs/``
    directory is still compared (silently skipping it would hide a stale
    manifest).

    This is the SINGLE source of these counters: the doctor and
    ``orchestrator.sync_state`` must both call it, otherwise the same
    workspace gets two different reconciliation verdicts (the doctor said
    FAIL, the journal said OK for one and the same workspace).
    """
    ws = Path(workspace)
    pdf_dir = ws / "pdfs"
    ext_dir = ws / "extracted"
    return {
        "downloaded_pdfs": len(list(pdf_dir.glob("*.pdf"))) if pdf_dir.is_dir() else 0,
        "extracted_markdowns": (
            len(list(ext_dir.glob("*.md"))) if ext_dir.is_dir() else 0
        ),
    }


def reconcile(
    workspace: Path | str,
    *,
    corpus: CorpusCounts | None = None,
    additional_actual: Mapping[str, int] | None = None,
) -> Reconciliation:
    """Compare the declared summary against the physical artifacts.

    ``status`` is:

    * ``UNRESOLVED`` -- a counted role is undetermined (an artifact that
      could not be read/understood maps to that role): the counter is
      undetermined, never ``0``;
    * ``UNCLASSIFIED`` -- at least one record-bearing artifact carries no
      known role, so the declared counters cannot represent the physical
      corpus;
    * ``UNIDENTIFIED`` -- corpus artifacts exist but none could be
      identified or parsed: the workspace is **not reconciled**;
    * ``CONFLICT`` -- a corpus artifact's own summary disagrees with its own
      record list. The physical list is the truth and is used for the
      counter, but the corpus is not self-consistent, so the workspace is
      **not reconciled** (never a green verdict);
    * ``SUMMARY`` -- the corpus exists only as a *declared summary* (no
      physical record list): a summary is **not** a verified physical
      reconciliation;
    * ``STALE`` -- at least one counter disagrees with the physical state;
    * ``NO_CORPUS`` -- the workspace holds no corpus artifact at all: the
      declared ``0`` is verified against the physical state;
    * ``OK`` -- the declared counters match the physical state.

    ``corpus`` lets a caller pass an already-computed
    :class:`CorpusCounts` (the doctor and ``sync`` count once, not twice).
    ``additional_actual`` lets a caller contribute counters it derives itself
    (the doctor and ``sync`` both add the PDF/extraction counts through
    :func:`extra_actual_stats`) without duplicating the comparison logic.
    """
    ws = Path(workspace)
    counts = corpus if corpus is not None else count_corpus(ws)
    declared_all = read_declared_stats(ws)

    actual: dict[str, int] = dict(counts.stats)
    if additional_actual:
        actual.update({k: int(v) for k, v in additional_actual.items()})

    keys = set(CORPUS_STAT_KEYS) | set(actual)
    mismatches: list[Mismatch] = []
    for key in sorted(keys):
        if key in counts.undetermined:
            # The physical count of this role is undetermined: comparing it
            # would be a fabricated comparison.
            continue
        declared_value = int(declared_all.get(key, 0) or 0)
        actual_value = int(actual.get(key, 0) or 0)
        if declared_value != actual_value:
            mismatches.append(
                Mismatch(key=key, declared=declared_value, actual=actual_value)
            )

    declared = {
        key: int(declared_all.get(key, 0) or 0)
        for key in sorted(keys)
        if key in declared_all or key in CORPUS_STAT_KEYS
    }

    if counts.status == "UNRESOLVED":
        status = "UNRESOLVED"
    elif counts.status == "UNCLASSIFIED":
        status = "UNCLASSIFIED"
    elif counts.status == "UNIDENTIFIED":
        status = "UNIDENTIFIED"
    elif counts.conflicts:
        # The corpus exists (it physically carries records) but it contradicts
        # itself: the physical count is used, the verdict is never a green
        # "reconciled" -- and it is never "NO_CORPUS" either.
        status = "CONFLICT"
    elif counts.status == "SUMMARY":
        # Corpus evidence exists, but only as a declared summary: a summary
        # is never a verified physical reconciliation.
        status = "SUMMARY"
    elif mismatches:
        status = "STALE"
    elif counts.status == "NO_CORPUS":
        # "This workspace holds no corpus artifact at all" -- and nothing
        # else was seen (no summary, no conflict, no unreadable artifact).
        status = "NO_CORPUS"
    else:
        status = "OK"

    return Reconciliation(
        workspace=ws,
        declared=declared,
        actual=actual,
        mismatches=tuple(mismatches),
        status=status,
        counts=counts,
    )
