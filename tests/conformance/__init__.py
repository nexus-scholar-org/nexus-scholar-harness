"""Conformance tests: the documented surface must never silently drift from code.

The suite enforces the contract stated in ``actions.py`` (single source of
truth, SPECS.md §5): every console action's rendered command must parse under
the referenced kit CLI, and the MCP surface referenced by the actions table
must be exported by the scholar-agent-kit MCP server.  These checks are
hermetic (no network, no heavy model loads) so they can run in CI.
"""