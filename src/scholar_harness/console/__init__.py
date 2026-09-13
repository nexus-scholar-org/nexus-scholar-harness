"""Harness Console: thin, local-first observability + human-judgment surface.

The console is a "wraps, renders, triggers" surface (Phase 5, D1-D6). It never
owns state: every read endpoint serves canonical workspace files and every
mutation is an atomic file write or a subprocess call to a kit CLI.
"""

from __future__ import annotations

from typing import Any

__all__ = ["create_app"]


def create_app(*args: Any, **kwargs: Any) -> Any:
    """Lazily import and create the FastAPI console application."""
    from .serve import create_app as _create_app

    return _create_app(*args, **kwargs)

