"""Nexus Scholar Research Harness Orchestrator."""

from importlib.metadata import PackageNotFoundError, version as _dist_version

# One version, in pyproject.toml; the installed metadata carries it (M6-beta).
try:
    __version__ = _dist_version("nexus-scholar")
except PackageNotFoundError:  # a bare source tree with no install
    __version__ = "0+unknown"

__all__ = ["ResearchOrchestrator", "__version__"]


def __getattr__(name: str):
    # H-faster-python-tests: the orchestrator pulls in the PDF and search kits,
    # pypdf and aiohttp. It is imported when first asked
    # for, not by every ``import scholar_harness.<anything>``.
    if name == "ResearchOrchestrator":
        from .orchestrator import ResearchOrchestrator

        return ResearchOrchestrator
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
