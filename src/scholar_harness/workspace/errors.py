"""Neutral workspace errors (HCM-02).

Single canonical refusal types for workspace identity and resolution.
Harness callers (orchestrator, genesis, audit_log, CLI) import these rather
than defining their own, so a typed refusal is one type everywhere.
"""

from __future__ import annotations


class RegisteredWorkspaceIdentityMissingError(RuntimeError):
    """A recorded workspace identity is absent, unusable, or not registered.

    This is the single typed refusal for workspace identity across the harness. It
    is defined here, beside the mint policy that creates the identity, and is
    imported by orchestrator, genesis, and the CLI, so a caller can catch one
    exception type whether the refusal came from creating a workspace or from
    reading one back. Nothing is ever minted to get past it: a substitute identity
    would let one workspace present two identities and destroy lineage.
    """


class NotWorkspaceError(Exception):
    """A target path cannot be resolved to a Nexus Scholar workspace."""
