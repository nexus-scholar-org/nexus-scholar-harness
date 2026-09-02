#!/usr/bin/env python3
"""
rescreen_workspace.py — Thin wrapper that delegates to agent_screen.py.

The harness itself is the LLM. No external API key required.

USAGE
-----
Step 1 — Prepare batches:
    python rescreen_workspace.py prepare [workspace_dir]

Step 2 — Ask the harness agent to screen (no script needed):
    Tell the agent: "screen all pending batches in literature/screening/"

Step 3 — Collect decisions:
    python rescreen_workspace.py collect [workspace_dir]

Step 4 — Check progress:
    python rescreen_workspace.py status [workspace_dir]

This script is a convenience alias. You can also call agent_screen.py directly.
"""
import sys
from pathlib import Path

# Forward to agent_screen
sys.argv[0] = "agent_screen.py"
_here = Path(__file__).resolve().parent
sys.path.insert(0, str(_here))

from agent_screen import main  # noqa: E402

if __name__ == "__main__":
    main()
