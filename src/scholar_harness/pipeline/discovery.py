"""Discovery stage (HCM-04b neutral extraction).

Stage 1 of the research pipeline: protocol-query compilation, federated
search, and raw-result publication. Extracted verbatim from
``ResearchOrchestrator.run_pipeline_async`` so the orchestrator delegates
without behavior change.

Neutrality: stdlib plus ``scholar-search-kit`` for the search itself, plus
the harness' own neutral workspace audit service for the journal row. No
console transport, no Contract v1 acceptance, no registry/acceptance state:
the stage writes **no** registry state and publishes exactly one canonical
audit event (``DISCOVERY_SEARCH``) through
:mod:`scholar_harness.workspace.audit`, the sole owner of append-only
journal discipline (T-TRUTH-COUNTS-01).

Truthfulness about provider failures (T-TRUTH-COUNTS-01)
---------------------------------------------------------
The kit's ``SearchEngine.fetch_provider`` catches every provider exception
and only logs it, so a provider failure does **not** propagate as an
exception and it does **not** produce an empty success either -- it silently
removes that provider's documents from the result. The harness therefore
compensates: every provider is wrapped in an observation proxy that records
per-provider success/failure, and the stage reports

* ``SUCCESS`` -- documents obtained and no provider failed;
* ``PARTIAL`` -- documents obtained but at least one provider failed (the
  degradation is named in ``reason`` and in the audit event);
* ``EMPTY_RESULT`` -- no documents obtained and no provider reported an
  error (never an unqualified success: an empty harvest is reported as an
  empty harvest);
* ``FAILED`` -- no documents obtained **and at least one provider failed**
  (the harvest is known-degraded and produced nothing; the failing
  providers are named in ``reason``).

``EMPTY_RESULT`` is an explicit extension of the ``SUCCESS``/``FAILED``
vocabulary of the workspace audit writer (``log_event.py`` documents only
``SUCCESS``/``FAILED``). It exists because "the search ran and legitimately
returned nothing" is neither a success nor a failure; the extension is
recorded in ``docs/architecture/workspace_stats_reconciliation.md``. The
provenance ``method`` of the event is ``EXTERNAL_PROVIDER`` (the records come
from an external provider, not from a deterministic rule or an LLM), as
required by ``docs/architecture/DEVELOPER_COMPASS.md`` section 3.

Fail-closed publication
------------------------
A ``FAILED`` harvest publishes **no** raw corpus artifact: an empty or
broken harvest must never leave an authoritative-looking
``literature/raw_search.json`` behind. An ``EMPTY_RESULT`` harvest does
publish the (empty) raw artifact -- it is a truthful, empty corpus.

**Pre-existing artifacts are never deleted.** A failed harvest leaves the
artifacts of an earlier run in place (deleting a researcher's data would
destroy evidence), but those artifacts are **not** this run's corpus: the
outcome names them (``stale_artifacts`` /
``stale_artifacts_present``) and the audit row records them, so a later
``sync_state`` can see that the physical corpus on disk predates this run.

The audit event is appended to the workspace that **owns** the literature
directory, resolved strictly (the literature directory's own parent, which
must carry ``project.json``). The stage never walks up the directory tree
looking for "some" ancestor workspace: a nested workspace without its own
``project.json`` must not have its discovery row appended to an unrelated
project's ledger. When the literature directory has no manifest of its own,
the protocol's own workspace is the owner (it is the authorisation for the
harvest). When no owning workspace can be resolved at all, the stage says
so explicitly on the outcome (``audit_status`` / ``audit_reason``) instead
of silently skipping the event.

The kit's swallow behavior itself is unchanged here: fixing it belongs to
the canonical ``scholar-search-kit`` repository, not to the harness.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from scholar_search.engine import SearchEngine
from scholar_search.protocol_adapter import compile_protocol_search
from scholar_search.providers import (
    ArxivProvider,
    BaseAPIProvider,
    BiorxivProvider,
    CrossrefProvider,
    OpenAlexProvider,
    PubMedProvider,
    SearchProvider,
    SemanticScholarProvider,
)

from scholar_harness.workspace.audit import append_event

logger = logging.getLogger(__name__)


_PROVIDER_MAP: dict[str, type[SearchProvider]] = {
    "openalex": OpenAlexProvider,
    "semanticscholar": SemanticScholarProvider,
    "semantic_scholar": SemanticScholarProvider,
    "crossref": CrossrefProvider,
    "arxiv": ArxivProvider,
    "pubmed": PubMedProvider,
    "biorxiv": BiorxivProvider,
}

#: Canonical audit action for a federated search (workspace-manager audit
#: trace spec, section 3 -- standard action names).
DISCOVERY_ACTION = "DISCOVERY_SEARCH"

#: The raw corpus artifacts the discovery stage publishes. They are also the
#: artifacts a *pre-existing* run may have left behind (see
#: :attr:`DiscoveryOutcome.stale_artifacts`).
CORPUS_ARTIFACT_NAMES: tuple[str, ...] = ("all_raw_search.json", "raw_search.json")


def _resolve_providers(providers: list[Any] | None) -> list[SearchProvider] | None:
    """Resolve provider instances from names (strings) or existing instances."""
    if not providers:
        return None
    instances: list[SearchProvider] = []
    for p in providers:
        if isinstance(p, str):
            key = p.lower().strip().replace("-", "_").replace(" ", "_")
            cls = _PROVIDER_MAP.get(key)
            if cls:
                instances.append(cls())
            else:
                logger.warning("Unknown search provider: %s", p)
        elif isinstance(p, BaseAPIProvider) or hasattr(p, "search"):
            instances.append(p)
        else:
            logger.warning("Unexpected provider item: %r", p)
    return instances if instances else None


# ---------------------------------------------------------------------------
# Provider observation (compensating for the kit's swallowed exceptions)
# ---------------------------------------------------------------------------


class _ProviderProbe:
    """Records the observed outcome of every provider that actually ran."""

    def __init__(self) -> None:
        self.succeeded: dict[str, int] = {}
        self.failed: dict[str, str] = {}

    def record_success(self, name: str, count: int) -> None:
        self.succeeded[name] = count

    def record_failure(self, name: str, exc: BaseException) -> None:
        self.failed[name] = f"{type(exc).__name__}: {exc}"

    @property
    def observed(self) -> int:
        return len(self.succeeded) + len(self.failed)

    @property
    def failed_names(self) -> list[str]:
        return sorted(self.failed)


class _ObservedProvider:
    """Transparent proxy around one provider that reports its outcome.

    The proxy delegates everything it does not observe to the wrapped
    provider (``name``, ``client``, ``close``), so the kit's engine behaves
    exactly as before -- it only learns what happened.
    """

    def __init__(self, provider: Any, probe: _ProviderProbe) -> None:
        self._provider = provider
        self._probe = probe

    @property
    def name(self) -> str:
        return getattr(self._provider, "name", type(self._provider).__name__)

    async def search(self, query: Any):
        count = 0
        try:
            async for doc in self._provider.search(query):
                count += 1
                yield doc
        except Exception as exc:  # noqa: BLE001 - the kit swallows it; we record it
            self._probe.record_failure(self.name, exc)
            raise
        self._probe.record_success(self.name, count)

    def __getattr__(self, item: str) -> Any:
        return getattr(self._provider, item)


def _observe_providers(engine: Any, probe: _ProviderProbe) -> list[str]:
    """Wrap the engine's providers with observation proxies.

    Returns the observed provider names. Engines without a ``providers``
    attribute (test doubles) are left untouched.
    """
    providers = getattr(engine, "providers", None)
    if not providers:
        return []
    observed: list[str] = []
    wrapped = []
    for provider in providers:
        proxy = _ObservedProvider(provider, probe)
        wrapped.append(proxy)
        observed.append(proxy.name)
    engine.providers = wrapped
    return observed


def _classify(count: int, probe: _ProviderProbe) -> tuple[str, str]:
    """Classify the harvest outcome: ``(status, reason)``.

    An empty harvest is never an unqualified success (COMPASS section 3:
    "Empty output is not automatically success. Degraded work is ``PARTIAL``
    and must explain the degradation.").
    """
    failed = probe.failed_names
    if count == 0:
        if failed:
            return (
                "FAILED",
                "no documents obtained; "
                f"{len(failed)} provider(s) failed: {', '.join(failed)}",
            )
        return (
            "EMPTY_RESULT",
            f"no documents obtained from {probe.observed} provider(s)",
        )
    if failed:
        return (
            "PARTIAL",
            f"{count} document(s) obtained but {len(failed)} of "
            f"{probe.observed} provider(s) failed: {', '.join(failed)}",
        )
    if probe.observed == 0:
        return (
            "SUCCESS",
            f"{count} document(s) obtained (no provider outcome was observed)",
        )
    return (
        "SUCCESS",
        f"{count} document(s) obtained from {probe.observed} provider(s)",
    )


# ---------------------------------------------------------------------------
# Workspace resolution for the audit event
# ---------------------------------------------------------------------------


def _resolve_audit_workspace(protocol_path: Path, literature_dir: Path) -> Path | None:
    """Resolve the workspace that owns ``literature_dir`` (``None`` if none).

    The resolution is **strict** (T-TRUTH-COUNTS-01):

    * the owning workspace is the directory that contains the literature
      directory -- exactly one level up, never an arbitrary ancestor;
    * that directory must be a real workspace (``project.json``);
    * the protocol must live inside that owner (the protocol is the
      authorization for the harvest).

    Both sides are **resolved** before they are compared: a relative
    ``literature_dir`` (``"ws/literature"``) resolves to an absolute owner,
    and the protocol is compared against that resolved owner -- otherwise a
    relative literature directory makes a legitimate workspace look like it
    has no owner and the canonical row is silently lost.

    A nested workspace without its own ``project.json`` therefore never has
    its discovery row appended to an unrelated parent project's ledger: the
    stage reports "no owning workspace" instead. The one fallback is the
    protocol's *own* workspace, used when the literature directory has no
    manifest of its own: the protocol is the authorisation for the harvest,
    so its workspace owns the row (never an unrelated ancestor).
    """
    protocol = Path(protocol_path).resolve()
    owner = Path(literature_dir).resolve().parent
    if (owner / "project.json").is_file():
        try:
            protocol.relative_to(owner)
        except ValueError:
            # The protocol lives outside the literature owner: the owner
            # cannot vouch for the harvest, and the row is reported as
            # NOT_WRITTEN (an explicit, visible provenance gap).
            return None
        return owner
    protocol_owner = protocol.parent
    if (protocol_owner / "project.json").is_file():
        return protocol_owner
    return None


@dataclass
class DiscoveryOutcome:
    """Typed outcome of the discovery stage: raw documents plus their count.

    ``status`` is the honest outcome of the harvest (``SUCCESS``,
    ``PARTIAL``, ``EMPTY_RESULT``, ``FAILED``) and ``reason`` explains it.
    ``audit_status`` / ``audit_reason`` / ``audit_workspace`` make the audit
    trail explicit: ``audit_status`` is ``WRITTEN`` when the canonical
    ``DISCOVERY_SEARCH`` event was appended and ``NOT_WRITTEN`` (with a
    reason) when no owning workspace could be resolved -- never a silent
    skip.

    ``stale_artifacts`` names the corpus artifacts a **pre-existing** run
    left in place. A failed harvest never deletes a researcher's artifacts,
    so those files physically contradict the failed journal row; they are
    reported here (and in the audit row) so nobody mistakes them for this
    run's corpus.
    """

    documents: list[Any]
    count: int
    status: str = "SUCCESS"
    reason: str = ""
    providers_succeeded: tuple[str, ...] = ()
    providers_failed: tuple[str, ...] = ()
    provider_errors: dict[str, str] = field(default_factory=dict)
    published: bool = True
    audit_status: str = "WRITTEN"
    audit_reason: str = ""
    audit_workspace: str = ""
    stale_artifacts: tuple[str, ...] = ()

    @property
    def stale_artifacts_present(self) -> bool:
        """True when artifacts of an earlier run are still on disk."""
        return bool(self.stale_artifacts)


async def run_discovery(
    *,
    protocol_path: Path | str,
    literature_dir: Path | str,
    max_search_results: int | None = None,
    agent_or_tool: str = "scholar-harness",
) -> DiscoveryOutcome:
    """Compile the protocol query, run federated search, publish raw results.

    Verbatim move of orchestrator Stage 1: ``compile_protocol_search``,
    ``max_search_results`` override, ``SearchEngine`` construction via
    ``_resolve_providers``, ``search_all(query, dedup=False)``, ``close()``,
    then identical ``asdict``/``json`` serialization into
    ``all_raw_search.json`` and ``raw_search.json``.

    Provider failure does **not** propagate: the kit's ``SearchEngine``
    catches provider exceptions and only logs them, so a failed provider
    simply contributes no documents. The stage compensates by observing
    every provider, so the outcome is never reported as a success it was not
    (see the module docstring).

    Fail-closed publication: a ``FAILED`` harvest publishes **no** raw corpus
    artifact (``published=False``) -- a broken harvest must not leave an
    authoritative-looking ``literature/raw_search.json`` behind. Artifacts of
    an earlier run are **not** deleted; they are reported as
    ``stale_artifacts`` (they are not this run's corpus).

    Exactly one canonical ``DISCOVERY_SEARCH`` audit event is appended
    through :mod:`scholar_harness.workspace.audit` (the sole owner of the
    append-only journal discipline) recording the real actor, the inputs,
    the outputs, the obtained counts, and the honest status. The owning
    workspace is resolved strictly; when none can be resolved the outcome
    says so explicitly (``audit_status="NOT_WRITTEN"``). The stage writes no
    registry/acceptance state.
    """
    p_path = Path(protocol_path).resolve()
    if not p_path.exists():
        raise FileNotFoundError(f"Protocol file not found at {p_path}")

    lit_dir = Path(literature_dir)
    lit_dir.mkdir(parents=True, exist_ok=True)

    query, providers = compile_protocol_search(p_path)
    if max_search_results:
        query.max_results = max_search_results

    engine = SearchEngine(providers=_resolve_providers(providers))
    probe = _ProviderProbe()
    observed_providers = _observe_providers(engine, probe)
    discovered_docs = await engine.search_all(query, dedup=False)
    await engine.close()

    count = len(discovered_docs)
    status, reason = _classify(count, probe)

    # Save both combined raw and first-provider raw for reference. A FAILED
    # harvest publishes nothing: an authoritative corpus artifact must never
    # be the product of a broken harvest (fail-closed publication).
    published = status != "FAILED"
    # Artifacts of a PREVIOUS run that are still on disk. A failed harvest
    # does not delete them (that would destroy the researcher's evidence),
    # but they are not this run's corpus -- they are reported explicitly.
    pre_existing = tuple(
        str(lit_dir / name)
        for name in CORPUS_ARTIFACT_NAMES
        if (lit_dir / name).exists()
    )
    stale_artifacts = () if published else pre_existing
    if published:
        payload = json.dumps(
            [
                asdict(d) if hasattr(d, "__dataclass_fields__") else d
                for d in discovered_docs
            ],
            indent=2,
            default=str,
        )
        (lit_dir / "all_raw_search.json").write_text(payload, encoding="utf-8")
        (lit_dir / "raw_search.json").write_text(payload, encoding="utf-8")

    outcome = DiscoveryOutcome(
        documents=discovered_docs,
        count=count,
        status=status,
        reason=reason,
        providers_succeeded=tuple(sorted(probe.succeeded)),
        providers_failed=tuple(probe.failed_names),
        provider_errors=dict(probe.failed),
        published=published,
        stale_artifacts=stale_artifacts,
    )

    audit_status, audit_reason, audit_workspace = _append_discovery_event(
        lit_dir=lit_dir,
        protocol_path=p_path,
        outcome=outcome,
        agent_or_tool=agent_or_tool,
        observed_providers=observed_providers,
        max_results=getattr(query, "max_results", None),
    )
    outcome.audit_status = audit_status
    outcome.audit_reason = audit_reason
    outcome.audit_workspace = audit_workspace
    return outcome


def _append_discovery_event(
    *,
    lit_dir: Path,
    protocol_path: Path,
    outcome: DiscoveryOutcome,
    agent_or_tool: str,
    observed_providers: list[str],
    max_results: Any,
) -> tuple[str, str, str]:
    """Append the canonical ``DISCOVERY_SEARCH`` event.

    Returns ``(audit_status, audit_reason, audit_workspace)`` so a missing
    event is an explicit, visible outcome instead of a silent skip.
    """
    workspace = _resolve_audit_workspace(protocol_path, lit_dir)
    if workspace is None:
        reason = (
            "no owning workspace could be resolved for "
            f"{lit_dir} (the owner is the literature directory's parent or "
            "the protocol's own workspace and must carry project.json) — no "
            "DISCOVERY_SEARCH audit event was written"
        )
        logger.warning(
            "Discovery produced %d document(s) but %s",
            outcome.count,
            reason,
        )
        return "NOT_WRITTEN", reason, ""

    outputs = [
        str(lit_dir / name) for name in CORPUS_ARTIFACT_NAMES if outcome.published
    ]

    description = (
        f"Federated discovery via scholar-search-kit: {outcome.count} raw "
        f"document(s) obtained ({outcome.status})"
    )
    if outcome.stale_artifacts_present:
        description += (
            "; artifacts of an earlier run were left in place and are NOT this "
            "run's corpus: " + ", ".join(outcome.stale_artifacts)
        )

    append_event(
        workspace,
        DISCOVERY_ACTION,
        description,
        agent=agent_or_tool,
        inputs=[str(protocol_path)],
        outputs=outputs,
        parameters={
            "search_tool": "scholar-search-kit",
            # Provenance method (COMPASS section 3): the records come from an
            # external provider, not from a deterministic rule or an LLM.
            "method": "EXTERNAL_PROVIDER",
            "providers": list(observed_providers),
            "max_results": max_results,
            "status": outcome.status,
            "reason": outcome.reason,
            "corpus_published": outcome.published,
            "stale_artifacts_present": outcome.stale_artifacts_present,
            "stale_artifacts": list(outcome.stale_artifacts),
        },
        metrics={
            "raw_hits": outcome.count,
            "providers_observed": len(observed_providers),
            "providers_succeeded": len(outcome.providers_succeeded),
            "providers_failed": len(outcome.providers_failed),
            "failed_providers": list(outcome.providers_failed),
            "harvest_status": outcome.status,
            "corpus_published": outcome.published,
            "stale_artifacts_present": outcome.stale_artifacts_present,
            "stale_artifacts": list(outcome.stale_artifacts),
        },
        status=outcome.status,
    )
    return "WRITTEN", f"DISCOVERY_SEARCH appended to {workspace}", str(workspace)
