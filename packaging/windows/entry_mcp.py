"""The console program of the Windows bundle: the MCP server (`scholar-agent`), for Part C's Claude Desktop entry."""

import sys

from scholar_agent.server import main

if __name__ == "__main__":
    sys.exit(main())
