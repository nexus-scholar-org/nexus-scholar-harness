"""Nexus Scholar Research Harness Orchestrator."""

from importlib.metadata import PackageNotFoundError, version as _dist_version

# One version, in pyproject.toml; the installed metadata carries it (M6-beta).
try:
    __version__ = _dist_version("nexus-scholar")
except PackageNotFoundError:  # a bare source tree with no install
    __version__ = "0+unknown"

from .orchestrator import ResearchOrchestrator

__all__ = ["ResearchOrchestrator", "__version__"]
