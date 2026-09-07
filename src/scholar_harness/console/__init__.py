"""Harness Console: thin, local-first observability + human-judgment surface.

The console is a "wraps, renders, triggers" surface (Phase 5, D1-D6). It never
owns state: every read endpoint serves canonical workspace files and every
mutation is an atomic file write or a subprocess call to a kit CLI.
"""

from __future__ import annotations

__all__ = ["create_app"]

from .serve import create_app
